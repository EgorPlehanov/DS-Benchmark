# src/profiling/core/cpu_profiler.py
"""
CPU профилировщик на основе cProfile.
Собирает время выполнения по функциям.
"""

import cProfile
import pstats
import io
import tempfile
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .base_profiler import BaseProfiler, ProfileResult, ProfilerState


class CPUProfiler(BaseProfiler):
    """Профилировщик CPU на основе cProfile"""
    
    def __init__(self, 
                 name: str = "cpu_profiler",
                 enabled: bool = True,
                 sort_by: str = 'cumulative',
                 limit: int = 20):
        super().__init__(name, enabled)
        self.sort_by = sort_by
        self.limit = limit
        self.profiler: Optional[cProfile.Profile] = None
        self.temp_file: Optional[str] = None
        
    def _on_start(self) -> None:
        """Начинаем профилирование CPU"""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        
        # Создаем временный файл для хранения сырых данных
        temp_dir = tempfile.gettempdir()
        self.temp_file = os.path.join(temp_dir, f"ds_profile_{os.getpid()}_{int(time.time())}.prof")
        
    def _on_stop(self) -> Dict[str, Any]:
        """Останавливаем профилирование и анализируем результаты"""
        if not self.profiler:
            return {}
            
        self.profiler.disable()
        
        # Сохраняем сырые данные во временный файл
        if self.temp_file:
            self.profiler.dump_stats(self.temp_file)
        
        # Анализируем статистику
        stats = pstats.Stats(self.profiler)
        
        # Получаем топ функций
        top_functions = self._get_top_functions(stats)
        
        # Анализ по файлам (получаем stats через внутренние атрибуты)
        stats_dict = self._get_stats_dict(stats)
        file_stats = self._analyze_by_file(stats_dict)
        
        # Общая статистика
        total_stats = self._get_total_stats(stats_dict)
        
        return {
            'top_functions': top_functions,
            'file_stats': file_stats,
            'total_stats': total_stats,
            'raw_data_path': self.temp_file,
        }
    
    def _get_stats_dict(self, stats: pstats.Stats) -> Dict[Tuple[str, int, str], Tuple]:
        """Получает словарь статистик из объекта Stats"""
        # pstats.Stats хранит статистику в атрибуте .stats
        # Используем getattr для обхода проверки типов
        return getattr(stats, 'stats', {})
    
    def _get_total_stats(self, stats_dict: Dict) -> Dict[str, Any]:
        """Вычисляет общую статистику"""
        if not stats_dict:
            return {
                'total_calls': 0,
                'primitive_calls': 0,
                'total_time': 0.0,
            }
        
        total_calls = sum(stat[0] for stat in stats_dict.values())
        
        # Подсчитываем примитивные вызовы (stat[1] - рекурсивные вызовы)
        primitive_calls = sum(
            stat[0] - stat[1] if len(stat) > 1 and stat[1] > 0 else stat[0]
            for stat in stats_dict.values()
        )
        
        # Общее время (stat[3] - cumulative time)
        total_time = sum(
            stat[3] if len(stat) > 3 else 0.0
            for stat in stats_dict.values()
        )
        
        return {
            'total_calls': total_calls,
            'primitive_calls': primitive_calls,
            'total_time': total_time,
        }
    
    def _get_top_functions(self, stats: pstats.Stats) -> List[Dict[str, Any]]:
        """Получаем топ-N самых затратных функций"""
        # Используем StringIO для захвата вывода pstats
        output = io.StringIO()
        stats_stream = pstats.Stats(self.profiler, stream=output)
        stats_stream.sort_stats(self.sort_by)
        stats_stream.print_stats(self.limit)
        
        # Парсим вывод
        lines = output.getvalue().strip().split('\n')
        
        top_functions = []
        # Пропускаем заголовок
        for line in lines[5:]:  # cProfile выводит 5 строк заголовка
            if not line.strip():
                continue
                
            parts = line.strip().split()
            if len(parts) >= 6:
                try:
                    ncalls = parts[0]
                    if '/' in ncalls:
                        total_calls, primitive_calls = ncalls.split('/')
                    else:
                        total_calls = primitive_calls = ncalls
                    
                    total_time = float(parts[3])
                    per_call = float(parts[4]) if parts[4] != '' else 0.0
                    cumulative_time = float(parts[5])
                    
                    # Извлекаем информацию о функции
                    func_info = ' '.join(parts[6:])
                    
                    top_functions.append({
                        'function': func_info,
                        'total_calls': int(total_calls),
                        'primitive_calls': int(primitive_calls),
                        'total_time': total_time,
                        'per_call': per_call,
                        'cumulative_time': cumulative_time,
                    })
                except (ValueError, IndexError):
                    continue
        
        return top_functions
    
    def _analyze_by_file(self, stats_dict: Dict) -> Dict[str, Any]:
        """Анализирует статистику по файлам"""
        file_stats = {}
        
        # stats_dict содержит сырые данные: {(filename, line, funcname): stats}
        for func_key, stat_data in stats_dict.items():
            filename, line_num, func_name = func_key
            
            if filename not in file_stats:
                file_stats[filename] = {
                    'total_time': 0.0,
                    'call_count': 0,
                    'functions': {}
                }
            
            # cumulative time - это stat_data[3]
            cumulative_time = stat_data[3] if len(stat_data) > 3 else 0.0
            call_count = stat_data[0] if len(stat_data) > 0 else 0
            
            file_stats[filename]['total_time'] += cumulative_time
            file_stats[filename]['call_count'] += call_count
            
            # Сохраняем информацию о функции
            func_key_str = f"{func_name}:{line_num}"
            if func_key_str not in file_stats[filename]['functions']:
                file_stats[filename]['functions'][func_key_str] = {
                    'cumulative_time': 0.0,
                    'call_count': 0
                }
            
            file_stats[filename]['functions'][func_key_str]['cumulative_time'] += cumulative_time
            file_stats[filename]['functions'][func_key_str]['call_count'] += call_count
        
        # Сортируем файлы по общему времени
        sorted_files = sorted(
            file_stats.items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )
        
        return {filename: data for filename, data in sorted_files[:10]}  # Топ-10 файлов
    
    def cleanup(self):
        """Очистка временных файлов"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
            except:
                pass