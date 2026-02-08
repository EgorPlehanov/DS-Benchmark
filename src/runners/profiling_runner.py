# src/runners/profiling_runner.py
"""
ProfilingRunner - расширение UniversalBenchmarkRunner с поддержкой профилирования.
"""

import os
import json
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
                 results_dir: str = "results/benchmark",
                 profiling_level: str = "medium",
                 save_raw_profiles: bool = True,
                 enable_scalene: bool = False):
        """
        Args:
            adapter: Адаптер для тестируемой библиотеки
            results_dir: Директория для сохранения результатов
            profiling_level: Уровень профилирования (off, light, medium, full)
            save_raw_profiles: Сохранять ли сырые данные профилирования
        """
        super().__init__(adapter, results_dir)
        
        self.profiling_level = profiling_level
        self.save_raw_profiles = save_raw_profiles
        self.enable_scalene = enable_scalene
        self.profiler = self._setup_profiler()
        
        # Создаем поддиректории для профилирования
        self.profiling_dir = os.path.join(self.run_dir, "profiling")
        os.makedirs(self.profiling_dir, exist_ok=True)
        os.makedirs(os.path.join(self.profiling_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.profiling_dir, "reports"), exist_ok=True)

        self.scalene_collector = ScaleneCollector(
            output_dir=os.path.join(self.profiling_dir, "scalene"),
            enabled=enable_scalene,
            include_paths=[Path(os.getcwd()) / "src"]
        )
        
        print(f"🔧 ProfilingRunner инициализирован с уровнем: {profiling_level}")
        print(f"📊 Профилировщики: {', '.join(self.profiler.get_enabled_profilers())}")
        print(f"📈 Scalene: {self.scalene_collector.get_status()}")
    
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
                       test_name: str = "", iteration: int = 0, **kwargs):
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
                    iteration=iteration
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
                        iteration=iteration,
                        test_name=test_name
                    )
                    base_metrics["scalene"] = scalene_info
            
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
                           test_name: str = "", iteration: int = 0) -> None:
        """Сохраняет данные профилирования с привязкой к тесту"""
        if not self.save_raw_profiles:
            return
        
        timestamp = datetime.now().strftime("%H%M%S")
        
        # ✅ СОЗДАЕМ ИМЯ ФАЙЛА С ИНФОРМАЦИЕЙ О ТЕСТЕ
        if test_name and iteration > 0:
            filename = f"{test_name}_iter{iteration}_{step_name}_{timestamp}"
        elif test_name:
            filename = f"{test_name}_{step_name}_{timestamp}"
        else:
            filename = f"{step_name}_{timestamp}"
        
        # 1. Структурированный отчет
        report_data = {
            'step': step_name,
            'test_name': test_name,
            'iteration': iteration,
            'timestamp': datetime.now().isoformat(),
            'total_duration': profile_result.total_duration,
            'bottlenecks': profile_result.bottlenecks,
            'correlations': profile_result.correlations,
            'metadata': profile_result.metadata
        }
        
        report_file = os.path.join(self.profiling_dir, "reports", f"{filename}_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # 2. Детальные данные профилировщиков
        for profiler_name, result in profile_result.results.items():
            profiler_data = {
                'profiler': profiler_name,
                'test_name': test_name,
                'iteration': iteration,
                'step': step_name,
                'data': result.data,
                'metadata': result.metadata
            }
            
            data_file = os.path.join(
                self.profiling_dir, 
                "raw", 
                f"{filename}_{profiler_name}.json"
            )
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(profiler_data, f, indent=2, ensure_ascii=False)
        
        # 3. Краткая информация для быстрого поиска
        info_file = os.path.join(self.profiling_dir, "raw", f"{filename}_info.txt")
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write(f"Test: {test_name}\n")
            f.write(f"Step: {step_name}\n")
            f.write(f"Iteration: {iteration}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Profiles: {', '.join(profile_result.results.keys())}\n")
    
    def _run_single_iteration(self, loaded_data: Any, test_data: Dict[str, Any],
                            iteration_num: int, alphas: List[float], 
                            test_name: str = "") -> Dict[str, Any]:
        """Выполняет одну итерацию теста с профилированием"""
        iteration_results = {
            "iteration": iteration_num,
            "performance": {}
        }
        
        # Шаг 1
        step1_results, step1_metrics = self._measure_performance(
            self._execute_step1,
            loaded_data,
            step_name="step1_original",
            test_name=test_name,
            iteration=iteration_num
        )
        iteration_results["step1"] = step1_results
        iteration_results["performance"]["step1"] = step1_metrics
        
        # Шаг 2
        step2_results, step2_metrics = self._measure_performance(
            self._execute_step2,
            loaded_data,
            step_name="step2_dempster",
            test_name=test_name,
            iteration=iteration_num
        )
        iteration_results["step2"] = step2_results
        iteration_results["performance"]["step2"] = step2_metrics
        
        # Шаг 3
        step3_results, step3_metrics = self._measure_performance(
            self._execute_step3,
            loaded_data,
            alphas,
            step_name="step3_discount_dempster",
            test_name=test_name,
            iteration=iteration_num
        )
        iteration_results["step3"] = step3_results
        iteration_results["performance"]["step3"] = step3_metrics
        
        # Шаг 4
        step4_results, step4_metrics = self._measure_performance(
            self._execute_step4,
            loaded_data,
            step_name="step4_yager",
            test_name=test_name,
            iteration=iteration_num
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
        """Запускает тест с профилированием"""
        print(f"\n🧪 Запуск теста: {test_name}")
        print(f"   Итераций: {iterations}")
        
        test_results = {
            "metadata": {
                "test_name": test_name,
                "adapter": self.adapter_name,
                "iterations": iterations,
                "timestamp": datetime.now().isoformat(),
                "frame_size": len(test_data.get("frame_of_discernment", [])),
                "sources_count": len(test_data.get("bba_sources", []))
            },
            "iterations": [],
            "aggregated": {}
        }
        
        loaded_data = self.adapter.load_from_dass(test_data)

        self._save_scalene_input(test_name, test_data)
        
        if alphas is None:
            sources_count = self.adapter.get_sources_count(loaded_data)
            alphas = [0.1] * sources_count
        
        for i in range(iterations):
            print(f"   Итерация {i+1}/{iterations}...", end="", flush=True)
            
            iteration_results = self._run_single_iteration(
                loaded_data=loaded_data,
                test_data=test_data,
                iteration_num=i+1,
                alphas=alphas,
                test_name=test_name  # ✅ Передаем имя теста
            )
            
            test_results["iterations"].append(iteration_results)
            print(" ✓")
        
        test_results["aggregated"] = self._aggregate_iteration_results(
            test_results["iterations"]
        )
        
        self._save_test_results(test_results, test_name)
        self.results.append(test_results)
        
        return test_results

    def _save_scalene_input(self, test_name: str, test_data: Dict[str, Any]) -> None:
        """Сохраняет входные данные теста для scalene."""
        if not self.enable_scalene:
            return
        input_dir = os.path.join(self.profiling_dir, "scalene", "inputs")
        os.makedirs(input_dir, exist_ok=True)
        input_path = os.path.join(input_dir, f"{test_name}.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)

    def _get_scalene_input_path(self, test_name: str) -> Optional[str]:
        if not self.enable_scalene:
            return None
        input_path = os.path.join(self.profiling_dir, "scalene", "inputs", f"{test_name}.json")
        return input_path if os.path.exists(input_path) else None
    
    def cleanup(self):
        """Очистка ресурсов"""
        super().cleanup()
        if hasattr(self, 'profiler') and self.profiler:
            if hasattr(self.profiler, 'cleanup'):
                try:
                    self.profiler.cleanup()
                except Exception as e:
                    print(f"⚠️  Ошибка при очистке профилировщика: {e}")
