# src/profiling/collectors/system_collector.py
"""
SystemCollector - сбор базовых системных метрик.
Измеряет время, память, CPU и аллокации для функций Демпстера-Шейфера.
"""

import time
import tracemalloc
import sys
from typing import Dict, Any, Callable, Optional, Tuple, List, Union
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("⚠️  psutil не установлен. CPU метрики будут ограничены.")

try:
    import gc
    HAS_GC = True
except ImportError:
    HAS_GC = False


class SystemCollector:
    """
    Сборщик системных метрик для функций Демпстера-Шейфера.
    
    Собирает:
    - Время выполнения (wall time, CPU time)
    - Использование памяти (пик, текущее, аллокации)
    - Загрузку CPU (%)
    - Статистику сборщика мусора
    - Информацию об аллокациях
    """
    
    def __init__(self, name: str = "system", enabled: bool = True):
        """
        Инициализация сборщика метрик.
        
        Args:
            name: Имя сборщика (используется для именования файлов)
            enabled: Включен ли сборщик
        """
        self.name = name
        self.enabled = enabled
        
        # Для отслеживания аллокаций памяти
        self.allocated_blocks_start: Optional[int] = None
        self.allocated_blocks_end: Optional[int] = None
        
        print(f"🔧 SystemCollector '{name}' инициализирован")
    
    def profile(self, func: Callable, *args, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        """
        Профилирует выполнение функции и возвращает метрики.
        
        Args:
            func: Функция для профилирования
            *args: Аргументы функции
            **kwargs: Ключевые аргументы функции
            
        Returns:
            tuple: (результат_функции, метрики)
        """
        if not self.enabled:
            return func(*args, **kwargs), {}
        
        print(f"📊 SystemCollector: профилирование {func.__name__}...", end="", flush=True)
        
        # Инициализация метрик
        metrics = {
            "function_name": func.__name__,
            "timestamp": datetime.now().isoformat(),
            "profiler": self.name,
            "success": True
        }
        
        # === ПОДГОТОВКА ИЗМЕРЕНИЙ ===
        
        # 1. Сборщик мусора (если доступен)
        gc_stats_before = None
        if HAS_GC:
            gc.collect()  # Принудительная сборка перед началом
            gc.disable()  # Отключаем GC для точных измерений
            gc_stats_before = gc.get_stats()
        
        # 2. Аллокации памяти (Python objects)
        if hasattr(sys, 'getallocatedblocks'):
            self.allocated_blocks_start = sys.getallocatedblocks()
        
        # 3. Отслеживание памяти (tracemalloc)
        tracemalloc.start()
        snapshot_before = tracemalloc.take_snapshot()
        
        # 4. CPU время (если доступен psutil)
        cpu_time_before = None
        cpu_percent_before = None
        if HAS_PSUTIL:
            try:
                process = psutil.Process()
                cpu_time_before = process.cpu_times()
                cpu_percent_before = process.cpu_percent(interval=None)
            except Exception as e:
                print(f"⚠️  Ошибка получения CPU метрик: {e}")
                cpu_time_before = None
                cpu_percent_before = None
        
        # === ВЫПОЛНЕНИЕ ФУНКЦИИ ===
        
        wall_time_start = time.perf_counter()
        cpu_time_start = time.process_time()
        
        result = None
        error = None
        
        try:
            result = func(*args, **kwargs)
            metrics["success"] = True
            metrics["error"] = None
        except Exception as e:
            error = str(e)
            metrics["success"] = False
            metrics["error"] = error
            metrics["error_type"] = type(e).__name__
        
        wall_time_end = time.perf_counter()
        cpu_time_end = time.process_time()
        
        # === СБОР МЕТРИК ПОСЛЕ ВЫПОЛНЕНИЯ ===
        
        # 1. Время выполнения
        metrics["time"] = {
            "wall_time_ms": (wall_time_end - wall_time_start) * 1000,
            "cpu_time_ms": (cpu_time_end - cpu_time_start) * 1000,
            "start_timestamp": wall_time_start,
            "end_timestamp": wall_time_end
        }
        
        # 2. CPU метрики (если доступны)
        cpu_metrics: Dict[str, Any] = {"note": "psutil not available"}
        if HAS_PSUTIL and cpu_time_before is not None:
            try:
                process = psutil.Process()
                cpu_time_after = process.cpu_times()
                cpu_percent_after = process.cpu_percent(interval=None)
                
                # Проверяем что значения не None
                user_time_diff = 0.0
                system_time_diff = 0.0
                cpu_percent_value = 0.0
                
                if hasattr(cpu_time_after, 'user') and hasattr(cpu_time_before, 'user'):
                    user_time_diff = (cpu_time_after.user - cpu_time_before.user) * 1000
                
                if hasattr(cpu_time_after, 'system') and hasattr(cpu_time_before, 'system'):
                    system_time_diff = (cpu_time_after.system - cpu_time_before.system) * 1000
                
                if cpu_percent_after is not None and cpu_percent_before is not None:
                    cpu_percent_value = max(0, cpu_percent_after - cpu_percent_before)
                
                cpu_metrics = {
                    "user_time_ms": user_time_diff,
                    "system_time_ms": system_time_diff,
                    "cpu_percent": cpu_percent_value,
                    "cpu_count": psutil.cpu_count(),
                    "cpu_freq_current": None
                }
                
                # Пытаемся получить частоту CPU
                try:
                    cpu_freq = psutil.cpu_freq()
                    if cpu_freq and hasattr(cpu_freq, 'current'):
                        cpu_metrics["cpu_freq_current"] = cpu_freq.current
                except:
                    pass
                    
            except Exception as e:
                cpu_metrics = {"error": str(e)}
        
        metrics["cpu"] = cpu_metrics
        
        # 3. Память (tracemalloc)
        snapshot_after = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        stats = snapshot_after.compare_to(snapshot_before, 'lineno')
        
        # Анализ аллокаций памяти
        total_memory = sum(stat.size for stat in stats)
        total_allocations = sum(stat.count for stat in stats)
        
        memory_metrics: Dict[str, Any] = {
            "peak_memory_bytes": total_memory,
            "peak_memory_mb": total_memory / (1024 * 1024),
            "allocations_count": total_allocations,
            "memory_diff_stats": self._analyze_memory_stats(stats),
            "current_memory_mb": None
        }
        
        # Пытаемся получить текущее использование памяти
        if HAS_PSUTIL:
            try:
                memory_metrics["current_memory_mb"] = psutil.Process().memory_info().rss / (1024 * 1024)
            except:
                pass
        
        metrics["memory"] = memory_metrics
        
        # 4. Аллокации Python объектов
        if hasattr(sys, 'getallocatedblocks'):
            self.allocated_blocks_end = sys.getallocatedblocks()
            python_objects_metrics: Dict[str, Any] = {
                "allocated_blocks_start": self.allocated_blocks_start,
                "allocated_blocks_end": self.allocated_blocks_end,
            }
            
            # Вычисляем разницу только если оба значения не None
            if self.allocated_blocks_start is not None and self.allocated_blocks_end is not None:
                python_objects_metrics["allocated_blocks_diff"] = (
                    self.allocated_blocks_end - self.allocated_blocks_start
                )
            else:
                python_objects_metrics["allocated_blocks_diff"] = None
                
            metrics["python_objects"] = python_objects_metrics
        else:
            metrics["python_objects"] = {"note": "getallocatedblocks not available"}
        
        # 5. Сборщик мусора (если доступен)
        if HAS_GC:
            gc.enable()  # Включаем GC обратно
            gc.collect()  # Еще одна сборка
            gc_stats_after = gc.get_stats()
            
            gc_metrics: Dict[str, Any] = {
                "collections_before": gc_stats_before,
                "collections_after": gc_stats_after,
                "gc_enabled": gc.isenabled()
            }
            
            if gc_stats_before and gc_stats_after:
                gc_metrics["collections_diff"] = self._calculate_gc_diff(gc_stats_before, gc_stats_after)
            else:
                gc_metrics["collections_diff"] = None
                
            metrics["gc"] = gc_metrics
        else:
            metrics["gc"] = {"note": "gc module not available"}
        
        # 6. Системные метрики (если доступны)
        system_metrics: Dict[str, Any] = {"note": "psutil not available"}
        if HAS_PSUTIL:
            try:
                system_metrics = {
                    "memory_percent": psutil.virtual_memory().percent,
                    "available_memory_gb": psutil.virtual_memory().available / (1024**3),
                    "disk_io": None
                }
                
                # Disk IO может быть недоступен
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    system_metrics["disk_io"] = disk_io._asdict()
                    
            except Exception as e:
                system_metrics = {"error": str(e)}
        
        metrics["system"] = system_metrics
        
        # Дополнительная информация
        metrics["metadata"] = {
            "has_psutil": HAS_PSUTIL,
            "has_gc": HAS_GC,
            "has_tracemalloc": True,
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        print(" ✓")
        return result, metrics
    
    def _analyze_memory_stats(self, stats: List) -> Dict[str, Any]:
        """Анализирует статистику аллокаций памяти."""
        if not stats:
            return {"total_size": 0, "total_count": 0, "top_allocations": []}
        
        total_size = sum(stat.size for stat in stats)
        total_count = sum(stat.count for stat in stats)
        
        # Топ-5 аллокаций по размеру
        top_by_size = sorted(stats, key=lambda s: s.size, reverse=True)[:5]
        top_allocations = []
        
        for stat in top_by_size:
            traceback_str = ""
            if stat.traceback:
                frames = []
                for frame in stat.traceback[:3]:  # Берем 3 верхних фрейма
                    frames.append(f"{frame.filename}:{frame.lineno}")
                traceback_str = " -> ".join(frames)
            
            allocation_info: Dict[str, Any] = {
                "size_bytes": stat.size,
                "count": stat.count,
                "traceback": traceback_str
            }
            
            # Добавляем diff если они есть
            if hasattr(stat, 'size_diff'):
                allocation_info["size_diff"] = stat.size_diff
            if hasattr(stat, 'count_diff'):
                allocation_info["count_diff"] = stat.count_diff
                
            top_allocations.append(allocation_info)
        
        return {
            "total_size_bytes": total_size,
            "total_count": total_count,
            "top_allocations": top_allocations,
            "avg_allocation_size": total_size / total_count if total_count > 0 else 0
        }
    
    def _calculate_gc_diff(self, before: List, after: List) -> Dict[str, Any]:
        """Вычисляет разницу в статистике GC."""
        if not before or not after:
            return {}
        
        diff = {}
        for i in range(min(len(before), len(after))):
            diff[f"generation_{i}"] = {
                "collections": after[i]["collections"] - before[i]["collections"],
                "collected": after[i]["collected"] - before[i]["collected"],
                "uncollectable": after[i]["uncollectable"] - before[i]["uncollectable"]
            }
        
        return diff
    
    def profile_function(self, func: Callable, *args, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        """Алиас для profile() для совместимости."""
        return self.profile(func, *args, **kwargs)
    
    def __call__(self, func: Callable) -> Callable:
        """
        Декоратор для профилирования функций.
        
        Использование:
        @system_collector
        def my_function():
            pass
        """
        def wrapper(*args, **kwargs):
            result, metrics = self.profile(func, *args, **kwargs)
            wrapper.metrics = metrics  # Сохраняем метрики в атрибуте функции
            return result
        
        return wrapper


# Фабричная функция для удобства
def create_system_collector(name: str = "system", enabled: bool = True) -> SystemCollector:
    """
    Создает экземпляр SystemCollector.
    
    Args:
        name: Имя сборщика
        enabled: Включен ли сборщик
        
    Returns:
        SystemCollector: Созданный сборщик
    """
    return SystemCollector(name=name, enabled=enabled)


# Глобальный экземпляр для простого использования
system_collector = SystemCollector()