# src/runners/profiling_runner.py
"""
ProfilingRunner - расширение UniversalBenchmarkRunner с поддержкой профилирования.
"""

import os
import json
import copy
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .universal_runner import UniversalBenchmarkRunner
from ..profiling.composite_profiler import CompositeProfiler, CompositeProfileResult
from ..profiling.core.cpu_profiler import CPUProfiler
from ..profiling.core.memory_profiler import MemoryProfiler
from ..profiling.core.line_profiler import LineProfiler
from ..profiling.collectors import ScaleneCollector


class ProfilingBenchmarkRunner(UniversalBenchmarkRunner):
    """
    UniversalBenchmarkRunner с поддержкой профилирования.
    Запускает тесты со сбором детальной информации о производительности.
    """
    
    def __init__(self, 
                 adapter,
                 results_dir: str = "results/profiling",
                 profiling_level: str = "medium",
                 sanitize_paths: bool = True,
                 enable_scalene: bool = False):
        """
        Args:
            adapter: Адаптер для тестируемой библиотеки
            results_dir: Директория для сохранения результатов
            profiling_level: Уровень профилирования (off, light, medium, full)
            sanitize_paths: Нормализовать пути в raw-данных (по умолчанию: True)
        """
        super().__init__(adapter, results_dir)
        
        self.profiling_level = profiling_level
        self.sanitize_paths = sanitize_paths
        self.enable_scalene = enable_scalene
        self.profiler = self._setup_profiler()
        
        # Базовый путь профилирования в структуре артефактов
        self.profiling_dir = str(self.artifact_manager.run_dir / "profilers")

        self.scalene_collector = ScaleneCollector(
            output_dir=str(self.artifact_manager.run_dir / "profilers" / "scalene"),
            enabled=enable_scalene
        )
        
        print(f"🔧 ProfilingRunner инициализирован с уровнем: {profiling_level}")
        print(f"📊 Профилировщики: {', '.join(self.profiler.get_enabled_profilers())}")
        print(f"🛡️  Нормализация путей: {'включена' if self.sanitize_paths else 'выключена'}")
        print(f"📈 Scalene: {self.scalene_collector.get_status()}")

    def _make_path_relative(self, value: Any) -> Any:
        """Преобразует абсолютные пути в относительные к cwd, если возможно."""
        if not isinstance(value, str):
            return value

        if not value:
            return value

        normalized = value.replace("\\", "/")

        if ":/" not in normalized and not normalized.startswith("/"):
            return value

        try:
            abs_path = Path(value).resolve()
            cwd_path = Path.cwd().resolve()
            relative = abs_path.relative_to(cwd_path)
            return str(relative).replace("\\", "/")
        except Exception:
            # Если путь вне проекта или недоступен, не раскрываем локальные детали.
            return "<external_path>"

    def _sanitize_paths_in_value(self, value: Any) -> Any:
        """Рекурсивно нормализует пути во всех строковых значениях структуры данных."""
        if isinstance(value, dict):
            sanitized_dict = {}
            for key, item in value.items():
                sanitized_key = self._make_path_relative(key) if isinstance(key, str) else key
                sanitized_dict[sanitized_key] = self._sanitize_paths_in_value(item)
            return sanitized_dict

        if isinstance(value, list):
            return [self._sanitize_paths_in_value(item) for item in value]

        if isinstance(value, tuple):
            return tuple(self._sanitize_paths_in_value(item) for item in value)

        if isinstance(value, str):
            return self._make_path_relative(value)

        return value

    def _prepare_profiler_payload(self, profiler_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Возвращает полные raw-данные профилировщика с опциональной нормализацией путей."""
        payload = copy.deepcopy(data)

        if not self.sanitize_paths:
            return payload

        return self._sanitize_paths_in_value(payload)
    
    def _setup_profiler(self) -> CompositeProfiler:
        """Настраивает композитный профилировщик в зависимости от уровня"""
        profilers = []
        
        if self.profiling_level == "off":
            return CompositeProfiler(profilers=[], auto_setup=False)
        
        elif self.profiling_level == "light":
            cpu_profiler = CPUProfiler(
                name="cpu",
                enabled=True,
                sort_by='cumulative',
                limit=15
            )
            profilers.append(cpu_profiler)
        
        elif self.profiling_level == "medium":
            cpu_profiler = CPUProfiler(
                name="cpu",
                enabled=True,
                sort_by='cumulative',
                limit=25
            )
            memory_profiler = MemoryProfiler(
                name="memory",
                enabled=True,
                trace_frames=15,
                limit=10
            )
            profilers.extend([cpu_profiler, memory_profiler])
        
        elif self.profiling_level == "full":
            cpu_profiler = CPUProfiler(
                name="cpu",
                enabled=True,
                sort_by='cumulative',
                limit=40
            )
            memory_profiler = MemoryProfiler(
                name="memory",
                enabled=True,
                trace_frames=25,
                limit=20
            )
            line_profiler = LineProfiler(
                name="line",
                enabled=True,
                include_paths=[os.getcwd()],
                limit=50,
                line_limit_per_file=30
            )
            profilers.extend([cpu_profiler, memory_profiler, line_profiler])
        
        else:
            raise ValueError(f"Неизвестный уровень профилирования: {self.profiling_level}")
        
        return CompositeProfiler(profilers=profilers, auto_setup=False)
    
    def _measure_performance(self, func, *args, step_name: str = "", 
                       test_name: str = "", repeat_count: int = 1, **kwargs):
        """
        Расширенное измерение производительности с профилированием.
        """
        if self.profiling_level == "off":
            return super()._measure_performance(func, *args, step_name=step_name, **kwargs)
        
        print(f"   📊 Профилирование {step_name}...", end="", flush=True)
        
        try:
            result, profile_result = self.profiler.profile(func, *args, **kwargs)
            
            execution_time = profile_result.metadata.get('function_execution_time', 0) * 1000
            
            base_metrics = {
                "time_ms": execution_time,
                "memory_peak_mb": 0.0,
                "cpu_usage_percent": 0.0
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
                    base_metrics["scalene"] = scalene_info

            base_metrics["step_repeat_count"] = repeat_count
            
            # ✅ ПРАВИЛЬНАЯ ОБРАБОТКА ОШИБОК
            if 'error' in profile_result.metadata:
                error_info = profile_result.metadata['error']
                error_msg = str(error_info.get('error', 'Unknown error')).lower()
                
                # Проверяем, это полный конфликт или другая ошибка
                if any(keyword in error_msg for keyword in 
                    ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                    # Это полный конфликт - НЕ ошибка, а warning
                    base_metrics["warning"] = error_info.get('error', 'Полный конфликт между источниками')
                else:
                    # Другие ошибки
                    base_metrics["error"] = error_info.get('error', 'Unknown error')
                    base_metrics["error_type"] = error_info.get('error_type', 'Exception')
            
            print(" ✓")
            return result, base_metrics
            
        except Exception as e:
            print(f" ❌ (ошибка профилирования: {str(e)[:50]}...)")
            
            return None, {
                "time_ms": 0.0,
                "memory_peak_mb": 0.0,
                "cpu_usage_percent": 0.0,
                "error": f"Ошибка профилирования: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _save_profiling_data(self, step_name: str, profile_result: CompositeProfileResult,
                           test_name: str = "", repeat_count: int = 1) -> None:
        """Сохраняет данные профилирования с привязкой к тесту"""
        timestamp = datetime.now().strftime("%H%M%S")
        
        # ✅ СОЗДАЕМ ИМЯ ФАЙЛА С ИНФОРМАЦИЕЙ О ТЕСТЕ
        if test_name:
            filename = f"{test_name}_rep{repeat_count}_{step_name}_{timestamp}"
        else:
            filename = f"{step_name}_rep{repeat_count}_{timestamp}"
        
        # 1. Структурированный отчет
        report_data = {
            'step': step_name,
            'test_name': test_name,
            'timestamp': datetime.now().isoformat(),
            'total_duration': profile_result.total_duration,
            'bottlenecks': profile_result.bottlenecks,
            'correlations': profile_result.correlations,
            'metadata': {
                **profile_result.metadata,
                'step_repeat_count': repeat_count
            }
        }
        
        self.artifact_manager.save_json(
            f"{filename}_report.json",
            report_data,
            subdir=f"profilers/reports/{test_name or 'unknown'}"
        )
        
        # 2. Детальные данные профилировщиков
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

        
        # 3. Краткая информация для быстрого поиска
        info_content = (
            f"Test: {test_name}\n"
            f"Step: {step_name}\n"
            f"Repeat count: {repeat_count}\n"
            f"Timestamp: {datetime.now().isoformat()}\n"
            f"Profiles: {', '.join(profile_result.results.keys())}\n"
        )
        self.artifact_manager.save_text(
            f"{filename}_info.txt",
            info_content,
            subdir=f"profilers/info/{test_name or 'unknown'}"
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
        self.artifact_manager.save_metrics(step1_metrics, test_name or "unknown", "step1_original", iteration_num, repeat_count=step_repeat_count)
        
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
        self.artifact_manager.save_metrics(step2_metrics, test_name or "unknown", "step2_dempster", iteration_num, repeat_count=step_repeat_count)
        
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
        self.artifact_manager.save_metrics(step3_metrics, test_name or "unknown", "step3_discount_dempster", iteration_num, repeat_count=step_repeat_count)
        
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
        self.artifact_manager.save_metrics(step4_metrics, test_name or "unknown", "step4_yager", iteration_num, repeat_count=step_repeat_count)
        
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
                "run_count": 1,
                "iterations": 1,
                "step_repeat_count": step_repeat_count,
                "timestamp": datetime.now().isoformat(),
                "frame_size": len(test_data.get("frame_of_discernment", [])),
                "sources_count": len(test_data.get("bba_sources", []))
            },
            "runs": [],
            "iterations": [],
            "aggregated": {}
        }
        
        loaded_data = self.adapter.load_from_dass(test_data)

        # Сохраняем входные данные теста
        self.artifact_manager.save_test_input(test_data, test_name)
        self._save_scalene_input(test_name, test_data)
        
        if alphas is None:
            sources_count = self.adapter.get_sources_count(loaded_data)
            alphas = [0.1] * sources_count
        
        print("   Итерация 1/1...", end="", flush=True)
        iteration_results = self._run_single_iteration(
            loaded_data=loaded_data,
            test_data=test_data,
            iteration_num=1,
            alphas=alphas,
            test_name=test_name,
            step_repeat_count=step_repeat_count
        )
        test_results["runs"].append(iteration_results)
        test_results["iterations"].append(iteration_results)
        print(" ✓")
        
        test_results["aggregated"] = self._aggregate_iteration_results(
            test_results["runs"]
        )
        
        self._save_test_results(test_results, test_name)
        self.results.append(test_results)
        
        return test_results


    def _save_test_results(self, test_results: Dict[str, Any], test_name: str):
        """Сохраняет результаты теста: во внутреннем API оставляем iterations, в файле сохраняем runs."""
        persisted_results = {
            **test_results,
            "metadata": {
                **test_results.get("metadata", {}),
            },
            "runs": list(test_results.get("runs") or test_results.get("iterations", [])),
        }
        persisted_results["metadata"].pop("iterations", None)
        persisted_results.pop("iterations", None)

        self.artifact_manager.save_test_results(persisted_results, test_name)
        self._create_short_report(test_results, test_name)

    def _save_scalene_input(self, test_name: str, test_data: Dict[str, Any]) -> None:
        """Сохраняет входные данные теста для scalene."""
        if not self.enable_scalene:
            return
        self.artifact_manager.save_json(
            f"{test_name}.json",
            test_data,
            subdir="profilers/scalene/inputs"
        )

    def _get_scalene_input_path(self, test_name: str) -> Optional[str]:
        if not self.enable_scalene:
            return None
        input_path = self.artifact_manager.run_dir / "profilers" / "scalene" / "inputs" / f"{test_name}.json"
        return str(input_path) if input_path.exists() else None
    
    def cleanup(self):
        """Очистка ресурсов"""
        super().cleanup()
        if hasattr(self, 'profiler') and self.profiler:
            if hasattr(self.profiler, 'cleanup'):
                try:
                    self.profiler.cleanup()
                except Exception as e:
                    print(f"⚠️  Ошибка при очистке профилировщика: {e}")
