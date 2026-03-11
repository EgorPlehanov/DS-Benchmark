# src/profiling/composite_profiler.py
"""
Композитный профилировщик - запускает ВСЕ профилировщики ОДНОВРЕМЕННО.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from .core.base_profiler import BaseProfiler, ProfileResult
from .core.cpu_profiler import CPUProfiler
from .core.memory_profiler import MemoryProfiler


@dataclass
class CompositeProfileResult:
    """Результат композитного профилирования"""
    results: Dict[str, ProfileResult] = field(default_factory=dict)
    correlations: List[Dict[str, Any]] = field(default_factory=list)
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    total_duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompositeProfiler:
    """Запускает несколько профилировщиков одновременно"""
    
    def __init__(self, 
                 profilers: Optional[List[BaseProfiler]] = None,
                 auto_setup: bool = True):
        """
        Args:
            profilers: Список профилировщиков для запуска
            auto_setup: Автоматически настраивать профилировщики по умолчанию
        """
        self.profilers: Dict[str, BaseProfiler] = {}
        
        if auto_setup and (profilers is None or len(profilers) == 0):
            self._setup_default_profilers()
        elif profilers:
            for profiler in profilers:
                self.add_profiler(profiler)
    
    def _setup_default_profilers(self):
        """Настраивает профилировщики по умолчанию"""
        # CPU профилировщик
        cpu_profiler = CPUProfiler(
            name="cpu",
            enabled=True,
            sort_by='cumulative',
            limit=25
        )
        self.add_profiler(cpu_profiler)
        
        # Memory профилировщик
        memory_profiler = MemoryProfiler(
            name="memory",
            enabled=True,
            trace_frames=20,
            limit=15
        )
        self.add_profiler(memory_profiler)
    
    def add_profiler(self, profiler: BaseProfiler) -> None:
        """Добавляет профилировщик"""
        self.profilers[profiler.name] = profiler
    
    def remove_profiler(self, name: str) -> None:
        """Удаляет профилировщик"""
        if name in self.profilers:
            del self.profilers[name]
    
    def start_all(self) -> None:
        """Запускает ВСЕ профилировщики"""
        for name, profiler in self.profilers.items():
            if profiler.enabled:
                profiler.start()
    
    def stop_all(self) -> CompositeProfileResult:
        """Останавливает ВСЕ профилировщики и возвращает результаты"""
        all_results = {}
        
        for name, profiler in self.profilers.items():
            if profiler.enabled:
                result = profiler.stop()
                all_results[name] = result
        
        # Анализируем корреляции между результатами
        correlations = self._analyze_correlations(all_results)
        
        # Выявляем узкие места
        bottlenecks = self._identify_bottlenecks(all_results)
        
        # Вычисляем общее время
        total_duration = max(
            (r.duration_seconds for r in all_results.values()),
            default=0.0
        )
        
        return CompositeProfileResult(
            results=all_results,
            correlations=correlations,
            bottlenecks=bottlenecks,
            total_duration=total_duration,
            metadata={
                'profiler_count': len(all_results),
                'profiler_names': list(all_results.keys()),
                'timestamp': time.time()
            }
        )
    
    def profile(self, func, *args, **kwargs):
        """
        Запускает функцию со ВСЕМИ профилировщиками одновременно
        
        Returns:
            tuple: (результат функции, CompositeProfileResult)
            или: (None, CompositeProfileResult) если произошла ошибка
        """
        # Запускаем все профилировщики
        self.start_all()
        
        execution_time = 0.0
        result = None
        
        try:
            # Выполняем функцию
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            execution_time = end_time - start_time
            
        except Exception as e:
            # Если произошла ошибка, всё равно останавливаем профилировщики
            # и записываем информацию об ошибке
            end_time = time.perf_counter()
            execution_time = end_time - start_time if 'start_time' in locals() else 0.0
            
            # Сохраняем информацию об ошибке
            error_info = {
                'error': str(e),
                'error_type': type(e).__name__,
                'execution_time': execution_time
            }
            
        finally:
            # Останавливаем все профилировщики (всегда!)
            profile_result = self.stop_all()
            
            # Добавляем время выполнения функции
            profile_result.metadata['function_execution_time'] = execution_time
            
            # Если была ошибка, добавляем информацию об ошибке
            if 'error_info' in locals():
                profile_result.metadata['error'] = error_info
        
        return result, profile_result
    
    def _analyze_correlations(self, all_results: Dict[str, ProfileResult]) -> List[Dict[str, Any]]:
        """Анализирует корреляции между разными типами метрик"""
        correlations = []
        
        # Проверяем наличие данных CPU и памяти
        cpu_data = all_results.get('cpu')
        memory_data = all_results.get('memory')
        
        if cpu_data and memory_data:
            # Ищем функции, которые потребляют много CPU и памяти
            cpu_functions = cpu_data.data.get('top_functions', [])
            memory_stats = memory_data.data.get('memory_stats', {})
            
            for func in cpu_functions[:5]:  # Топ-5 функций по CPU
                func_name = func.get('function', '')
                cpu_time = func.get('cumulative_time', 0)
                
                # Проверяем, есть ли эта функция в аллокациях памяти
                # (упрощенная проверка по имени файла)
                if 'dempster_core.py' in func_name.lower():
                    correlation = {
                        'type': 'cpu_memory_correlation',
                        'function': func_name,
                        'cpu_time': cpu_time,
                        'note': 'Функция из dempster_core.py может создавать аллокации',
                        'recommendation': 'Проверить создание временных объектов в цикле'
                    }
                    correlations.append(correlation)
        
        return correlations
    
    def _identify_bottlenecks(self, all_results: Dict[str, ProfileResult]) -> List[Dict[str, Any]]:
        """Выявляет узкие места на основе всех данных профилирования"""
        bottlenecks = []
        
        cpu_data = all_results.get('cpu')
        if cpu_data:
            # Ищем функции, занимающие больше 20% времени
            top_functions = cpu_data.data.get('top_functions', [])
            for func in top_functions:
                cumulative_time = func.get('cumulative_time', 0)
                
                # Если функция занимает значительное время
                if cumulative_time > 0.1:  # Более 100ms
                    bottleneck = {
                        'type': 'cpu_bottleneck',
                        'location': func.get('function', 'unknown'),
                        'time_seconds': cumulative_time,
                        'severity': 'high' if cumulative_time > 0.5 else 'medium',
                        'recommendation': 'Оптимизировать алгоритм или уменьшить количество вызовов'
                    }
                    bottlenecks.append(bottleneck)
        
        memory_data = all_results.get('memory')
        if memory_data:
            # Проверяем использование памяти
            peak_memory = memory_data.data.get('peak_memory_bytes', 0)
            if peak_memory > 100 * 1024 * 1024:  # Более 100MB
                bottleneck = {
                    'type': 'memory_bottleneck',
                    'peak_memory_mb': peak_memory / (1024 * 1024),
                    'severity': 'high',
                    'recommendation': 'Оптимизировать использование памяти, уменьшить аллокации'
                }
                bottlenecks.append(bottleneck)
        
        return bottlenecks
    
    def get_enabled_profilers(self) -> List[str]:
        """Возвращает список включенных профилировщиков"""
        return [name for name, profiler in self.profilers.items() if profiler.enabled]
    
    def enable_profiler(self, name: str) -> None:
        """Включает профилировщик"""
        if name in self.profilers:
            self.profilers[name].enabled = True
    
    def disable_profiler(self, name: str) -> None:
        """Выключает профилировщик"""
        if name in self.profilers:
            self.profilers[name].enabled = False
    
    def cleanup(self):
        """Очистка ресурсов всех профилировщиков"""
        for profiler in self.profilers.values():
            # Проверяем, есть ли метод cleanup у профилировщика
            cleanup_method = getattr(profiler, 'cleanup', None)
            if cleanup_method and callable(cleanup_method):
                cleanup_method()