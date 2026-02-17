# src/runners/profiling_runner.py
"""
ProfilingRunner - расширение UniversalBenchmarkRunner с поддержкой профилирования.
"""

import os
import json
import copy
import shutil
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .universal_runner import UniversalBenchmarkRunner
from ..profiling.composite_profiler import CompositeProfiler, CompositeProfileResult
from ..profiling.core.cpu_profiler import CPUProfiler
from ..profiling.core.memory_profiler import MemoryProfiler
from ..profiling.core.line_profiler import LineProfiler
from ..profiling.collectors import ScaleneCollector
from ..profiling.path_sanitizer import sanitize_payload_paths


class ProfilingBenchmarkRunner(UniversalBenchmarkRunner):
    """
    UniversalBenchmarkRunner с поддержкой профилирования.
    Запускает тесты со сбором детальной информации о производительности.
    """
    
    def __init__(self, 
                 adapter,
                 results_dir: str = "results/profiling",
                 profiling_mode: str = "full",
                 selected_profilers: Optional[List[str]] = None,
                 sanitize_paths: bool = True,
                 enable_scalene: Optional[bool] = None):
        """
        Args:
            adapter: Адаптер для тестируемой библиотеки
            results_dir: Директория для сохранения результатов
            profiling_mode: Режим профилирования (off, custom, full)
            selected_profilers: Список активных профилировщиков (cpu, memory, line, scalene)
            sanitize_paths: Нормализовать пути в raw-данных (по умолчанию: True)
        """
        if selected_profilers is None:
            resolved_selected_profilers = ["cpu", "memory", "line", "scalene"]
        else:
            resolved_selected_profilers = list(dict.fromkeys(selected_profilers))

        super().__init__(adapter, results_dir)

        self.profiling_mode = profiling_mode
        self.selected_profilers = resolved_selected_profilers
        self.core_profilers = [name for name in self.selected_profilers if name != "scalene"]
        self.profiling_level = "off" if not self.selected_profilers else profiling_mode
        self.sanitize_paths = sanitize_paths
        self.enable_scalene = ("scalene" in self.selected_profilers) if enable_scalene is None else enable_scalene
        self.profiler = self._setup_profiler()
        
        # Базовый путь профилирования в структуре артефактов
        self.profiling_dir = str(self.artifact_manager.run_dir / "profilers")

        if not self.selected_profilers:
            profilers_dir = Path(self.profiling_dir)
            if profilers_dir.exists():
                shutil.rmtree(profilers_dir, ignore_errors=True)

        self.scalene_collector = ScaleneCollector(
            output_dir=str(self.artifact_manager.run_dir / "profilers" / "scalene"),
            enabled=self.enable_scalene,
        )
        
        print(f"🔧 ProfilingRunner инициализирован с режимом: {self.profiling_mode}")
        print(f"📊 Профилировщики: {', '.join(self.selected_profilers) if self.selected_profilers else 'отключены'}")
        print(f"🛡️  Нормализация путей: {'включена' if self.sanitize_paths else 'выключена'}")
        print(f"📈 Scalene: {self.scalene_collector.get_status()}")

    def _prepare_profiler_payload(self, profiler_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Возвращает полные raw-данные профилировщика с опциональной нормализацией путей."""
        payload = copy.deepcopy(data)

        if not self.sanitize_paths:
            return payload

        return sanitize_payload_paths(payload)
    
    def _setup_profiler(self) -> CompositeProfiler:
        """Настраивает композитный профилировщик в зависимости от уровня"""
        profilers = []

        if not self.core_profilers:
            return CompositeProfiler(profilers=[], auto_setup=False)

        if "cpu" in self.core_profilers:
            cpu_profiler = CPUProfiler(
                name="cpu",
                enabled=True,
                sort_by='cumulative',
                limit=40
            )
            profilers.append(cpu_profiler)

        if "memory" in self.core_profilers:
            memory_profiler = MemoryProfiler(
                name="memory",
                enabled=True,
                trace_frames=25,
                limit=20
            )
            profilers.append(memory_profiler)

        if "line" in self.core_profilers:
            line_profiler = LineProfiler(
                name="line",
                enabled=True,
                include_paths=[os.getcwd()],
                limit=50,
                line_limit_per_file=30
            )
            profilers.append(line_profiler)
        
        return CompositeProfiler(profilers=profilers, auto_setup=False)
    
    def _measure_performance(self, func, *args, step_name: str = "", 
                       test_name: str = "", repeat_count: int = 1, **kwargs):
        """
        Расширенное измерение производительности с профилированием.
        """
        if not self.selected_profilers:
            return super()._measure_performance(func, *args, step_name=step_name, **kwargs)

        if not self.core_profilers:
            result, base_metrics = super()._measure_performance(func, *args, step_name=step_name, **kwargs)
            if self.enable_scalene and test_name:
                input_path = self._get_scalene_input_path(test_name)
                if input_path:
                    scalene_info = self.scalene_collector.profile_step(
                        input_path=input_path,
                        adapter_name=self.adapter_name,
                        step_name=step_name,
                        iteration=1,
                        test_name=test_name,
                        repeat=repeat_count
                    )
                    base_metrics["scalene"] = self._prepare_profiler_payload("scalene", scalene_info)
            return result, base_metrics
        
        print(f"   📊 Профилирование {step_name}...", end="", flush=True)
        
        try:
            result, profile_result = self.profiler.profile(func, *args, **kwargs)
            
            execution_time = profile_result.metadata.get('function_execution_time', 0) * 1000
            
            base_metrics = {
                "time_ms": execution_time,
                "memory_peak_mb": 0.0,
                "cpu_usage_percent": 0.0,
                "status": "success",
                "supported": True,
            }
            
            if profile_result.results:
                memory_data = profile_result.results.get('memory')
                if memory_data:
                    peak_bytes = memory_data.data.get('peak_memory_bytes', 0)
                    base_metrics["memory_peak_mb"] = peak_bytes / (1024 * 1024)
                
                self._save_profiling_data(
                    step_name=step_name,
                    profile_result=profile_result,
                    test_name=test_name,
                    repeat_count=repeat_count
                )
                
                base_metrics["profiling"] = {
                    'bottlenecks': profile_result.bottlenecks,
                    'correlations': profile_result.correlations,
                    'profiler_count': len(profile_result.results)
                }

            if self.enable_scalene and test_name:
                input_path = self._get_scalene_input_path(test_name)
                if input_path:
                    scalene_info = self.scalene_collector.profile_step(
                        input_path=input_path,
                        adapter_name=self.adapter_name,
                        step_name=step_name,
                        iteration=1,
                        test_name=test_name,
                        repeat=repeat_count
                    )
                    base_metrics["scalene"] = self._prepare_profiler_payload("scalene", scalene_info)

            base_metrics["step_repeat_count"] = repeat_count
            base_metrics["time_per_repeat_ms"] = execution_time / max(1, repeat_count)
            
            # ✅ ПРАВИЛЬНАЯ ОБРАБОТКА ОШИБОК
            if 'error' in profile_result.metadata:
                error_info = profile_result.metadata['error']
                error_msg = str(error_info.get('error', 'Unknown error')).lower()
                
                # Проверяем, это полный конфликт или другая ошибка
                if any(keyword in error_msg for keyword in 
                    ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                    base_metrics["status"] = "full_conflict"
                    base_metrics["warning"] = error_info.get('error', 'Полный конфликт между источниками')
                elif error_info.get('error_type') == 'NotImplementedError':
                    base_metrics["status"] = "not_supported"
                    base_metrics["supported"] = False
                    base_metrics["error"] = error_info.get('error', 'Not supported')
                    base_metrics["error_type"] = 'NotImplementedError'
                else:
                    base_metrics["status"] = "failed"
                    base_metrics["error"] = error_info.get('error', 'Unknown error')
                    base_metrics["error_type"] = error_info.get('error_type', 'Exception')
            
            print(" ✓")
            return result, base_metrics
            
        except Exception as e:
            print(f" ❌ (ошибка профилирования: {str(e)[:50]}...)")
            
            return None, {
                "time_ms": 0.0,
                "time_per_repeat_ms": 0.0,
                "memory_peak_mb": 0.0,
                "cpu_usage_percent": 0.0,
                "status": "failed",
                "supported": True,
                "error": f"Ошибка профилирования: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _save_profiling_data(self, step_name: str, profile_result: CompositeProfileResult,
                           test_name: str = "", repeat_count: int = 1) -> None:
        """Сохраняет данные профилирования с привязкой к тесту"""
        # Сохраняем только детальные данные профилировщиков (raw)
        for profiler_name, result in profile_result.results.items():
            profiler_data = {
                'profiler': profiler_name,
                'test_name': test_name,
                'step': step_name,
                'data': self._prepare_profiler_payload(profiler_name, result.data),
                'metadata': {
                    **result.metadata,
                    'raw_profile_mode': 'full',
                    'sanitize_paths': self.sanitize_paths,
                    'step_repeat_count': repeat_count
                }
            }
            
            self.artifact_manager.save_profiler_data(
                profiler_name=profiler_name,
                data=profiler_data,
                test_name=test_name or "unknown",
                step_name=step_name,
                repeat_count=repeat_count,
            )


    def _repeat_step(self, func, repeat_count: int, *args, **kwargs):
        """Выполняет шаг несколько раз и возвращает результат последнего запуска."""
        result = None
        for _ in range(max(1, repeat_count)):
            result = func(*args, **kwargs)
        return result

    def _run_single_iteration(self, loaded_data: Any, test_data: Dict[str, Any],
                            iteration_num: int, alphas: List[float],
                            test_name: str = "", step_repeat_count: int = 1) -> Dict[str, Any]:
        """Выполняет одну итерацию теста с профилированием"""
        iteration_results = {
            "run": iteration_num,
            "performance": {}
        }
        
        # Шаг 1
        step1_results, step1_metrics = self._measure_performance(
            self._repeat_step,
            self._execute_step1,
            step_repeat_count,
            loaded_data,
            step_name="step1_original",
            test_name=test_name,
            repeat_count=step_repeat_count
        )
        iteration_results["step1"] = step1_results
        iteration_results["performance"]["step1"] = step1_metrics
                
        # Шаг 2
        step2_results, step2_metrics = self._measure_performance(
            self._repeat_step,
            self._execute_step2,
            step_repeat_count,
            loaded_data,
            step_name="step2_dempster",
            test_name=test_name,
            repeat_count=step_repeat_count
        )
        iteration_results["step2"] = step2_results
        iteration_results["performance"]["step2"] = step2_metrics
                
        # Шаг 3
        step3_results, step3_metrics = self._measure_performance(
            self._repeat_step,
            self._execute_step3,
            step_repeat_count,
            loaded_data,
            alphas,
            step_name="step3_discount_dempster",
            test_name=test_name,
            repeat_count=step_repeat_count
        )
        iteration_results["step3"] = step3_results
        iteration_results["performance"]["step3"] = step3_metrics
                
        # Шаг 4
        step4_results, step4_metrics = self._measure_performance(
            self._repeat_step,
            self._execute_step4,
            step_repeat_count,
            loaded_data,
            step_name="step4_yager",
            test_name=test_name,
            repeat_count=step_repeat_count
        )
        iteration_results["step4"] = step4_results
        iteration_results["performance"]["step4"] = step4_metrics
                
        # Общая статистика
        iteration_results["performance"]["total"] = {
            "time_total_ms": sum(
                step["time_ms"] for step in iteration_results["performance"].values() 
                if isinstance(step, dict) and "time_ms" in step
            ),
            "memory_peak_mb": max(
                step.get("memory_peak_mb", 0) for step in iteration_results["performance"].values()
                if isinstance(step, dict)
            )
        }
        
        return iteration_results
    
    def run_test(self, test_data: Dict[str, Any], test_name: str,
                iterations: int = 3, alphas: Optional[List[float]] = None) -> Dict[str, Any]:
        """Запускает тест с профилированием.

        iterations интерпретируется как количество повторов каждого шага
        внутри одного прогона теста.
        """
        print(f"\n🧪 Запуск теста: {test_name}")
        print(f"   Повторов на шаг: {iterations}")
        step_repeat_count = max(1, iterations)
        
        test_results = {
            "metadata": {
                "test_name": test_name,
                "adapter": self.adapter_name,
                "step_repeat_count": step_repeat_count,
                "timestamp": datetime.now().isoformat(),
                "frame_size": len(test_data.get("frame_of_discernment", [])),
                "sources_count": len(test_data.get("bba_sources", []))
            },
            "iterations": []
        }
        
        loaded_data = self.adapter.load_from_dass(test_data)

        # Сохраняем входные данные теста
        self.artifact_manager.save_test_input(test_data, test_name)
        
        if alphas is None:
            sources_count = self.adapter.get_sources_count(loaded_data)
            alphas = [0.1] * sources_count
        
        iteration_results = self._run_single_iteration(
            loaded_data=loaded_data,
            test_data=test_data,
            iteration_num=1,
            alphas=alphas,
            test_name=test_name,
            step_repeat_count=step_repeat_count
        )
        test_results["iterations"].append(iteration_results)
        print(" ✓")

        self._save_test_results(test_results, test_name)
        self.results.append(test_results)
        
        return test_results


    def _save_test_results(self, test_results: Dict[str, Any], test_name: str):
        """Сохраняет только метаданные и вычислительные результаты шагов."""
        def _extract_computation_results(run_data: Dict[str, Any]) -> Dict[str, Any]:
            """Оставляет только step1..step4 без служебных/профилировочных полей."""
            if not isinstance(run_data, dict):
                return {}

            return {
                step_name: run_data.get(step_name)
                for step_name in ("step1", "step2", "step3", "step4")
                if step_name in run_data
            }

        source_run = (test_results.get("iterations") or [{}])[-1]

        persisted_results = {
            "metadata": {
                **test_results.get("metadata", {}),
            },
            "results": _extract_computation_results(source_run),
        }

        self.artifact_manager.save_test_results(persisted_results, test_name)

    def _get_scalene_input_path(self, test_name: str) -> Optional[str]:
        if not self.enable_scalene:
            return None
        input_path = self.artifact_manager.get_path(
            f"{test_name}_input.json",
            subdir="input"
        )
        return str(input_path) if input_path.exists() else None
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.sanitize_paths:
            try:
                self.artifact_manager.sanitize_saved_artifacts()
            except Exception as e:
                print(f"⚠️  Ошибка при пост-санитизации артефактов: {e}")

        super().cleanup()
        if hasattr(self, 'profiler') and self.profiler:
            if hasattr(self.profiler, 'cleanup'):
                try:
                    self.profiler.cleanup()
                except Exception as e:
                    print(f"⚠️  Ошибка при очистке профилировщика: {e}")
