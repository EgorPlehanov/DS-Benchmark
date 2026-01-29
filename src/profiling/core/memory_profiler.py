# src/profiling/core/memory_profiler.py
"""
Memory профилировщик на основе tracemalloc.
Собирает информацию об аллокациях памяти.
"""

import tracemalloc
import sys
from typing import Dict, Any, List, Optional
from .base_profiler import BaseProfiler, ProfileResult


class MemoryProfiler(BaseProfiler):
    """Профилировщик памяти на основе tracemalloc"""
    
    def __init__(self, 
                 name: str = "memory_profiler",
                 enabled: bool = True,
                 trace_frames: int = 25,
                 limit: int = 20):
        super().__init__(name, enabled)
        self.trace_frames = trace_frames
        self.limit = limit
        self.snapshot_start: Optional[tracemalloc.Snapshot] = None
        self.allocated_blocks_start: Optional[int] = None
        
    def _on_start(self) -> None:
        """Начинаем отслеживание памяти"""
        tracemalloc.start(self.trace_frames)
        self.snapshot_start = tracemalloc.take_snapshot()
        
        # Также отслеживаем количество аллоцированных блоков
        if hasattr(sys, 'getallocatedblocks'):
            self.allocated_blocks_start = sys.getallocatedblocks()
        
    def _on_stop(self) -> Dict[str, Any]:
        """Останавливаем отслеживание и анализируем память"""
        if not self.snapshot_start:
            return {}
            
        snapshot_end = tracemalloc.take_snapshot()
        
        # Сравниваем снапшоты
        stats = snapshot_end.compare_to(self.snapshot_start, 'lineno')
        
        # Анализируем статистику
        memory_stats = self._analyze_memory_stats(stats)
        
        # Пиковое использование памяти
        current, peak = tracemalloc.get_traced_memory()
        
        # Количество аллоцированных блоков
        allocated_blocks_end = None
        if hasattr(sys, 'getallocatedblocks'):
            allocated_blocks_end = sys.getallocatedblocks()
        
        tracemalloc.stop()
        
        return {
            'memory_stats': memory_stats,
            'peak_memory_bytes': peak,
            'current_memory_bytes': current,
            'allocated_blocks': {
                'start': self.allocated_blocks_start,
                'end': allocated_blocks_end,
                'difference': (
                    allocated_blocks_end - self.allocated_blocks_start 
                    if allocated_blocks_end and self.allocated_blocks_start 
                    else None
                )
            },
            'traceback_limit': self.trace_frames,
        }
    
    def _analyze_memory_stats(self, stats) -> Dict[str, Any]:
        """Анализирует статистику памяти"""
        total_size = sum(stat.size for stat in stats)
        total_count = sum(stat.count for stat in stats)
        
        # Группируем по файлам
        file_stats = {}
        for stat in stats[:self.limit]:  # Ограничиваем количество
            traceback = stat.traceback
            if traceback:
                frame = traceback[0]
                filename = frame.filename
                lineno = frame.lineno
                
                if filename not in file_stats:
                    file_stats[filename] = {
                        'total_size': 0,
                        'total_count': 0,
                        'locations': []
                    }
                
                file_stats[filename]['total_size'] += stat.size
                file_stats[filename]['total_count'] += stat.count
                
                # Сохраняем информацию о конкретном месте
                location_info = {
                    'line': lineno,
                    'size': stat.size,
                    'count': stat.count,
                }
                
                # Добавляем diff атрибуты если они есть
                if hasattr(stat, 'size_diff'):
                    location_info['size_diff'] = stat.size_diff
                if hasattr(stat, 'count_diff'):
                    location_info['count_diff'] = stat.count_diff
                    
                file_stats[filename]['locations'].append(location_info)
        
        # Топ аллокаций
        top_allocations = []
        for stat in stats[:10]:  # Топ-10 аллокаций
            traceback_str = self._format_traceback(stat.traceback)
            top_allocations.append({
                'size': stat.size,
                'count': stat.count,
                'traceback': traceback_str[:200]  # Ограничиваем длину
            })
        
        return {
            'total_size': total_size,
            'total_count': total_count,
            'file_stats': file_stats,
            'top_allocations': top_allocations,
            'stats_count': len(stats),
        }
    
    def _format_traceback(self, traceback) -> str:
        """Форматирует traceback для вывода"""
        if not traceback:
            return "No traceback"
        
        frames = []
        for frame in traceback[:5]:  # Ограничиваем глубину
            frames.append(f"{frame.filename}:{frame.lineno}")
        
        return " -> ".join(frames)