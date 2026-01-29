# src/runners/profiling_runner.py
"""
ProfilingRunner - расширение UniversalBenchmarkRunner с поддержкой профилирования.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

from .universal_runner import UniversalBenchmarkRunner
from ..profiling.composite_profiler import CompositeProfiler, CompositeProfileResult
from ..profiling.core.cpu_profiler import CPUProfiler
from ..profiling.core.memory_profiler import MemoryProfiler


class ProfilingBenchmarkRunner(UniversalBenchmarkRunner):
    """
    UniversalBenchmarkRunner с поддержкой профилирования.
    Запускает тесты со сбором детальной информации о производительности.
    """
    
    def __init__(self, 
                 adapter,
                 results_dir: str = "results/benchmark",
                 profiling_level: str = "medium",
                 save_raw_profiles: bool = True):
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
        self.profiler = self._setup_profiler()
        
        # Создаем поддиректории для профилирования
        self.profiling_dir = os.path.join(self.run_dir, "profiling")
        os.makedirs(self.profiling_dir, exist_ok=True)
        os.makedirs(os.path.join(self.profiling_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.profiling_dir, "reports"), exist_ok=True)
        
        print(f"🔧 ProfilingRunner инициализирован с уровнем: {profiling_level}")
        print(f"📊 Профилировщики: {', '.join(self.profiler.get_enabled_profilers())}")
    
    def _setup_profiler(self) -> CompositeProfiler:
        """Настраивает композитный профилировщик в зависимости от уровня"""
        profilers = []
        
        if self.profiling_level == "off":
            # Без профилирования
            return CompositeProfiler(profilers=[], auto_setup=False)
        
        elif self.profiling_level == "light":
            # Только базовое CPU профилирование
            cpu_profiler = CPUProfiler(
                name="cpu",
                enabled=True,
                sort_by='cumulative',
                limit=15
            )
            profilers.append(cpu_profiler)
        
        elif self.profiling_level == "medium":
            # CPU + Memory профилирование
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
            # Полное профилирование (будет расширено позже)
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
            profilers.extend([cpu_profiler, memory_profiler])
        
        else:
            raise ValueError(f"Неизвестный уровень профилирования: {self.profiling_level}")
        
        return CompositeProfiler(profilers=profilers, auto_setup=False)
    
    def _measure_performance(self, func, *args, step_name: str = "", **kwargs):
        """
        Расширенное измерение производительности с профилированием.
        Переопределяет метод родительского класса.
        """
        # Если профилирование выключено, используем базовый метод
        if self.profiling_level == "off":
            return super()._measure_performance(func, *args, step_name=step_name, **kwargs)
        
        print(f"   📊 Профилирование {step_name}...", end="", flush=True)
        
        try:
            # Запускаем функцию с профилированием
            result, profile_result = self.profiler.profile(func, *args, **kwargs)
            
            # Извлекаем базовые метрики из профилирования
            execution_time = profile_result.metadata.get('function_execution_time', 0) * 1000  # мс
            
            # Базовые метрики (как в родительском классе)
            base_metrics = {
                "time_ms": execution_time,
                "memory_peak_mb": 0.0,
                "cpu_usage_percent": 0.0
            }
            
            # Добавляем данные профилирования
            if profile_result.results:
                # Извлекаем данные памяти
                memory_data = profile_result.results.get('memory')
                if memory_data:
                    peak_bytes = memory_data.data.get('peak_memory_bytes', 0)
                    base_metrics["memory_peak_mb"] = peak_bytes / (1024 * 1024)
                
                # Сохраняем результаты профилирования
                self._save_profiling_data(step_name, profile_result)
                
                # Добавляем анализ в метрики
                base_metrics["profiling"] = {
                    'bottlenecks': profile_result.bottlenecks,
                    'correlations': profile_result.correlations,
                    'profiler_count': len(profile_result.results)
                }
            
            # Проверяем, была ли ошибка в выполнении функции
            if 'error' in profile_result.metadata:
                error_info = profile_result.metadata['error']
                base_metrics["error"] = error_info.get('error', 'Unknown error')
                base_metrics["error_type"] = error_info.get('error_type', 'Exception')
            
            print(" ✓")
            return result, base_metrics
            
        except Exception as e:
            # Если произошла ошибка в самом профилировании
            print(f" ❌ (ошибка профилирования: {str(e)[:50]}...)")
            
            # Возвращаем базовые метрики с ошибкой
            return None, {
                "time_ms": 0.0,
                "memory_peak_mb": 0.0,
                "cpu_usage_percent": 0.0,
                "error": f"Ошибка профилирования: {str(e)}",
                "error_type": type(e).__name__
            }
    
    def _save_profiling_data(self, step_name: str, profile_result: CompositeProfileResult) -> None:
        """Сохраняет данные профилирования"""
        if not self.save_raw_profiles:
            return
        
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{step_name}_{timestamp}"
        
        # 1. Сохраняем структурированные результаты
        report_data = {
            'step': step_name,
            'timestamp': datetime.now().isoformat(),
            'total_duration': profile_result.total_duration,
            'bottlenecks': profile_result.bottlenecks,
            'correlations': profile_result.correlations,
            'metadata': profile_result.metadata
        }
        
        report_file = os.path.join(self.profiling_dir, "reports", f"{filename}_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # 2. Сохраняем детальные данные каждого профилировщика
        for profiler_name, result in profile_result.results.items():
            profiler_data = {
                'profiler': profiler_name,
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
    
    def run_test(self, *args, **kwargs) -> Dict[str, Any]:
        """Запускает тест с профилированием"""
        result = super().run_test(*args, **kwargs)
        
        # Добавляем информацию о профилировании в результаты
        if self.profiling_level != "off":
            result['metadata']['profiling_level'] = self.profiling_level
            result['metadata']['profiling_dir'] = self.profiling_dir
        
        return result
    
    def cleanup(self):
        """Очистка ресурсов раннера и профилировщиков"""
        # Сначала вызываем cleanup родительского класса
        super().cleanup()
        
        # Затем очищаем профилировщик
        if hasattr(self, 'profiler') and self.profiler:
            # Безопасный вызов cleanup
            if hasattr(self.profiler, 'cleanup'):
                try:
                    self.profiler.cleanup()
                except Exception as e:
                    print(f"⚠️  Ошибка при очистке профилировщика: {e}")