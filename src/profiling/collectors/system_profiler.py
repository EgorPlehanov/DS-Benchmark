# src/profiling/collectors/system_profiler.py
"""
Базовый профилировщик системных метрик.
"""

import time
import psutil
import tracemalloc
import gc
import threading
from typing import Dict, Any, Callable, Tuple, Optional
from dataclasses import dataclass
import statistics

@dataclass
class SystemMetrics:
    """Контейнер для системных метрик."""
    execution_time_seconds: float = 0.0
    cpu_time_seconds: float = 0.0
    wall_time_seconds: float = 0.0
    peak_memory_bytes: int = 0
    cpu_usage_percent: float = 0.0
    allocation_size_bytes: int = 0
    allocation_count: int = 0
    gc_collections: int = 0
    gc_time_seconds: float = 0.0
    thread_count: int = 0
    error: Optional[str] = None
    warning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует в словарь."""
        result = {
            'execution_time_seconds': self.execution_time_seconds,
            'cpu_time_seconds': self.cpu_time_seconds,
            'wall_time_seconds': self.wall_time_seconds,
            'peak_memory_bytes': self.peak_memory_bytes,
            'peak_memory_mb': self.peak_memory_bytes / (1024 * 1024) if self.peak_memory_bytes > 0 else 0,
            'cpu_usage_percent': self.cpu_usage_percent,
            'allocation_size_bytes': self.allocation_size_bytes,
            'allocation_count': self.allocation_count,
            'gc_collections': self.gc_collections,
            'gc_time_seconds': self.gc_time_seconds,
            'thread_count': self.thread_count
        }
        
        if self.error:
            result['error'] = self.error
        if self.warning:
            result['warning'] = self.warning
            
        return result

class SystemProfiler:
    """
    Профилировщик системных метрик с низкими накладками.
    """
    
    def __init__(self, track_memory: bool = True, track_gc: bool = True):
        """
        Инициализация профилировщика.
        
        Args:
            track_memory: Включить отслеживание памяти
            track_gc: Включить отслеживание сборщика мусора
        """
        self.track_memory = track_memory
        self.track_gc = track_gc
        self.process = psutil.Process()
        
    def profile_function(self, 
                        func: Callable, 
                        *args, 
                        warmup_iterations: int = 1,
                        **kwargs) -> Tuple[Any, SystemMetrics]:
        """
        Профилирует выполнение функции.
        
        Args:
            func: Функция для профилирования
            *args: Аргументы функции
            warmup_iterations: Количество разогревочных итераций
            **kwargs: Именованные аргументы функции
            
        Returns:
            Кортеж (результат функции, метрики)
        """
        # Разогрев (если нужно)
        if warmup_iterations > 0:
            for _ in range(warmup_iterations):
                try:
                    func(*args, **kwargs)
                except:
                    pass
        
        metrics = SystemMetrics()
        
        # Собираем начальные метрики
        cpu_before = self._get_cpu_usage()
        memory_before = self.process.memory_info().rss
        gc_before = self._get_gc_stats()
        thread_before = threading.active_count()
        
        # Начинаем отслеживание памяти
        if self.track_memory:
            tracemalloc.start()
            snapshot_before = tracemalloc.take_snapshot()
        
        # Замер времени
        start_wall = time.perf_counter()
        start_cpu = time.process_time()
        
        try:
            # Выполняем функцию
            result = func(*args, **kwargs)
            
        except ValueError as e:
            # Особый случай: полный конфликт в Демпстере
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in 
                  ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                result = {"warning": "Полный конфликт между источниками (K=1.0)"}
                metrics.warning = "Полный конфликт между источниками (K=1.0)"
            else:
                result = {"error": str(e)}
                metrics.error = str(e)
                
        except Exception as e:
            result = {"error": str(e)}
            metrics.error = str(e)
            
        finally:
            # Конец замеров времени
            end_wall = time.perf_counter()
            end_cpu = time.process_time()
            
            # Собираем конечные метрики
            cpu_after = self._get_cpu_usage()
            memory_after = self.process.memory_info().rss
            gc_after = self._get_gc_stats()
            thread_after = threading.active_count()
            
            # Вычисляем метрики
            metrics.execution_time_seconds = end_wall - start_wall
            metrics.cpu_time_seconds = end_cpu - start_cpu
            metrics.wall_time_seconds = end_wall - start_wall
            metrics.peak_memory_bytes = max(memory_before, memory_after)
            metrics.cpu_usage_percent = max(0, cpu_after - cpu_before)
            metrics.thread_count = thread_after
            
            # Статистика GC
            if self.track_gc:
                metrics.gc_collections = gc_after['collections'] - gc_before['collections']
                metrics.gc_time_seconds = gc_after['time'] - gc_before['time']
            
            # Статистика аллокаций
            if self.track_memory:
                snapshot_after = tracemalloc.take_snapshot()
                tracemalloc.stop()
                
                diff = snapshot_after.compare_to(snapshot_before, 'lineno')
                metrics.allocation_size_bytes = sum(stat.size for stat in diff)
                metrics.allocation_count = sum(stat.count for stat in diff)
        
        return result, metrics
    
    def _get_cpu_usage(self) -> float:
        """Возвращает текущее использование CPU процессом."""
        return self.process.cpu_percent(interval=None)
    
    def _get_gc_stats(self) -> Dict[str, Any]:
        """Возвращает статистику сборщика мусора."""
        if hasattr(gc, 'get_stats'):
            stats = gc.get_stats()
            total_collections = sum(s['collections'] for s in stats)
            total_time = sum(s['collected'] for s in stats)  # В GC это обычно "collected"
            return {
                'collections': total_collections,
                'time': total_time
            }
        else:
            return {'collections': 0, 'time': 0.0}