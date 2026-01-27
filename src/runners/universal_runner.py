# src/runners/universal_runner.py
"""
Универсальный раннер для бенчмаркинга реализаций теории Демпстера-Шейфера.
Поддерживает любой адаптер, реализующий BaseDempsterShaferAdapter.
"""

import json
import time
import statistics
import tracemalloc
import psutil
import gc
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from datetime import datetime

# Для профилирования (опционально)
try:
    import cProfile
    import pstats
    PROFILE_AVAILABLE = True
except ImportError:
    PROFILE_AVAILABLE = False

from ..adapters.base_adapter import BaseDempsterShaferAdapter
from ..generators.validator import DassValidator


class PerformanceMetrics:
    """Контейнер для метрик производительности"""
    
    def __init__(self):
        self.execution_times = []
        self.memory_usage = []
        self.cpu_percentages = []
        self.gc_stats_before = {}
        self.gc_stats_after = {}
    
    def add_execution_time(self, time_ms: float):
        self.execution_times.append(time_ms)
    
    def add_memory_usage(self, memory_bytes: int):
        self.memory_usage.append(memory_bytes)
    
    def add_cpu_percentage(self, cpu_percent: float):
        self.cpu_percentages.append(cpu_percent)
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводную статистику по метрикам"""
        summary = {}
        
        if self.execution_times:
            summary['time_ms'] = {
                'min': min(self.execution_times),
                'max': max(self.execution_times),
                'mean': statistics.mean(self.execution_times),
                'median': statistics.median(self.execution_times),
                'stdev': statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0
            }
        
        if self.memory_usage:
            summary['memory_bytes'] = {
                'peak': max(self.memory_usage) if self.memory_usage else 0,
                'avg': statistics.mean(self.memory_usage) if self.memory_usage else 0
            }
            summary['memory_mb'] = {
                'peak': max(self.memory_usage) / 1024 / 1024 if self.memory_usage else 0,
                'avg': statistics.mean(self.memory_usage) / 1024 / 1024 if self.memory_usage else 0
            }
        
        if self.cpu_percentages:
            summary['cpu_percent'] = {
                'min': min(self.cpu_percentages),
                'max': max(self.cpu_percentages),
                'mean': statistics.mean(self.cpu_percentages),
                'median': statistics.median(self.cpu_percentages)
            }
        
        return summary


class TestResult:
    """Результаты выполнения одного теста"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.timestamp = datetime.now().isoformat()
        
        # Результаты шагов
        self.step1_original = {}  # Исходные Belief/Plausibility
        self.step2_dempster = {}  # Комбинирование Демпстером
        self.step3_discount = {}  # Дисконтирование + Демпстер
        self.step4_yager = {}     # Комбинирование Ягером
        
        # Метрики производительности
        self.performance = {
            'step1': PerformanceMetrics(),
            'step2': PerformanceMetrics(),
            'step3': PerformanceMetrics(),
            'step4': PerformanceMetrics(),
            'total': PerformanceMetrics()
        }
        
        # Дополнительная информация
        self.metadata = {}
        self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертирует результат в словарь"""
        return {
            'metadata': {
                'test_name': self.test_name,
                'timestamp': self.timestamp,
                'errors': self.errors
            },
            'step1_original': self.step1_original,
            'step2_dempster': self.step2_dempster,
            'step3_discount': self.step3_discount,
            'step4_yager': self.step4_yager,
            'performance': {
                'step1': self.performance['step1'].get_summary(),
                'step2': self.performance['step2'].get_summary(),
                'step3': self.performance['step3'].get_summary(),
                'step4': self.performance['step4'].get_summary(),
                'total': self.performance['total'].get_summary()
            }
        }
    
    def add_error(self, error_msg: str):
        """Добавляет ошибку в результаты"""
        self.errors.append({
            'message': error_msg,
            'timestamp': datetime.now().isoformat()
        })


class UniversalBenchmarkRunner:
    """
    Универсальный раннер для тестирования адаптеров теории Демпстера-Шейфера.
    
    Выполняет 4 шага процесса для каждого теста:
    1. Исходные Belief/Plausibility для каждого источника
    2. Комбинирование всех источников по правилу Демпстера
    3. Дисконтирование + комбинирование по Демпстеру
    4. Комбинирование всех источников по правилу Ягера
    """
    
    def __init__(self, adapter: BaseDempsterShaferAdapter, verbose: bool = False):
        """
        Инициализирует раннер с указанным адаптером.
        
        Args:
            adapter: Адаптер библиотеки для тестирования
            verbose: Выводить ли подробную информацию в процессе
        """
        self.adapter = adapter
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.current_iteration = 0
        self.total_iterations = 0
        
        # Состояние профилирования
        self.profiler = None
        self.profile_results = {}
    
    def _log(self, message: str, level: str = "INFO"):
        """Логирование сообщений"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")
    
    def _measure_performance(self, func: Callable, *args, **kwargs) -> Tuple[Any, Dict[str, Any]]:
        """
        Выполняет функцию с измерением производительности.
        
        Returns:
            tuple: (результат_функции, метрики_производительности)
        """
        metrics = {}
        
        # Измеряем память до выполнения
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        # Измеряем CPU до выполнения
        process = psutil.Process()
        cpu_before = process.cpu_percent(interval=None)
        
        # Собираем статистику GC
        gc.collect()
        gc_stats_before = gc.get_stats()
        
        # Измеряем время выполнения
        start_time = time.perf_counter()
        
        # Выполняем функцию
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            end_time = time.perf_counter()
            snapshot2 = tracemalloc.take_snapshot()
            tracemalloc.stop()
            
            metrics['error'] = str(e)
            metrics['execution_time_ms'] = (end_time - start_time) * 1000
            metrics['memory_delta_bytes'] = 0
            
            raise e
        
        end_time = time.perf_counter()
        
        # Измеряем память после выполнения
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Измеряем CPU после выполнения
        cpu_after = process.cpu_percent(interval=None)
        
        # Собираем статистику GC после
        gc_stats_after = gc.get_stats()
        
        # Вычисляем метрики
        metrics['execution_time_ms'] = (end_time - start_time) * 1000
        
        # Вычисляем использование памяти
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_memory = sum(stat.size for stat in top_stats)
        metrics['memory_delta_bytes'] = total_memory
        metrics['memory_peak_bytes'] = tracemalloc.get_traced_memory()[1]
        
        # Вычисляем использование CPU
        metrics['cpu_percent'] = max(cpu_before, cpu_after)  # Берем максимум
        
        # Собираем статистику GC
        metrics['gc'] = {
            'collections_before': gc_stats_before,
            'collections_after': gc_stats_after
        }
        
        return result, metrics
    
    def _execute_step1(self, loaded_data: Any, result: TestResult) -> Dict[str, Any]:
        """
        Шаг 1: Исходные Belief/Plausibility для каждого источника.
        
        Для каждого источника вычисляем Belief и Plausibility для:
        - Каждого отдельного элемента фрейма
        - Всего фрейма Ω (всегда Bel=1, Pl=1)
        """
        self._log(f"Выполнение шага 1 для теста {result.test_name}")
        
        try:
            # Получаем фрейм различения
            frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
            n_sources = self.adapter.get_sources_count(loaded_data)
            
            step_result = {
                'frame_elements': frame_elements,
                'sources': []
            }
            
            # Для каждого источника
            for source_idx in range(n_sources):
                source_result = {
                    'source_id': f'source_{source_idx + 1}',
                    'beliefs': {},
                    'plausibilities': {}
                }
                
                # Вычисляем Belief и Plausibility для каждого элемента
                for element in frame_elements:
                    # Belief для одиночного элемента
                    event = f"{{{element}}}"
                    bel = self.adapter.calculate_belief(loaded_data, event)
                    pl = self.adapter.calculate_plausibility(loaded_data, event)
                    
                    source_result['beliefs'][event] = bel
                    source_result['plausibilities'][event] = pl
                
                # Добавляем Belief и Plausibility для всего фрейма Ω
                # По определению: Bel(Ω) = 1.0, Pl(Ω) = 1.0
                omega_str = "{" + ",".join(sorted(frame_elements)) + "}"
                source_result['beliefs'][omega_str] = 1.0
                source_result['plausibilities'][omega_str] = 1.0
                
                step_result['sources'].append(source_result)
            
            return step_result
            
        except Exception as e:
            error_msg = f"Ошибка в шаге 1: {str(e)}"
            self._log(error_msg, "ERROR")
            result.add_error(error_msg)
            raise
    
    def _execute_step2(self, loaded_data: Any, result: TestResult) -> Dict[str, Any]:
        """
        Шаг 2: Комбинирование всех источников по правилу Демпстера.
        """
        self._log(f"Выполнение шага 2 для теста {result.test_name}")
        
        try:
            # Получаем фрейм различения
            frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
            
            # Комбинируем все источники по Демпстеру
            combined_bpa = self.adapter.combine_sources_dempster(loaded_data)
            
            # Создаем временные данные с комбинированным BPA
            # (нужно для вычисления Belief/Plausibility)
            combined_data = {
                'bpa': combined_bpa,
                'frame': set(frame_elements),
                'frame_elements': frame_elements
            }
            
            step_result = {
                'combined_bpa': combined_bpa,
                'beliefs': {},
                'plausibilities': {}
            }
            
            # Вычисляем Belief и Plausibility для каждого элемента
            for element in frame_elements:
                event = f"{{{element}}}"
                bel = self.adapter.calculate_belief(combined_data, event)
                pl = self.adapter.calculate_plausibility(combined_data, event)
                
                step_result['beliefs'][event] = bel
                step_result['plausibilities'][event] = pl
            
            # Добавляем для всего фрейма Ω
            omega_str = "{" + ",".join(sorted(frame_elements)) + "}"
            step_result['beliefs'][omega_str] = 1.0
            step_result['plausibilities'][omega_str] = 1.0
            
            # Вычисляем конфликт (если возможно)
            # Для этого нужно проанализировать combined_bpa
            if combined_bpa:
                conflict = combined_bpa.get("{}", 0.0)
                step_result['conflict_K'] = conflict
            
            return step_result
            
        except Exception as e:
            error_msg = f"Ошибка в шаге 2: {str(e)}"
            self._log(error_msg, "ERROR")
            result.add_error(error_msg)
            raise
    
    def _execute_step3(self, loaded_data: Any, alphas: List[float], 
                      result: TestResult) -> Dict[str, Any]:
        """
        Шаг 3: Дисконтирование + комбинирование по Демпстеру.
        
        Для каждого источника применяется дисконтирование с коэффициентом alpha,
        затем все дисконтированные источники комбинируются по Демпстеру.
        """
        self._log(f"Выполнение шага 3 для теста {result.test_name}")
        
        try:
            # Получаем фрейм и количество источников
            frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
            n_sources = self.adapter.get_sources_count(loaded_data)
            
            # Если alphas не предоставлены, используем одинаковые значения
            if alphas is None or len(alphas) != n_sources:
                default_alpha = 0.1
                alphas = [default_alpha] * n_sources
                self._log(f"Используются коэффициенты дисконтирования по умолчанию: {alphas}", "WARNING")
            
            # Применяем дисконтирование к каждому источнику
            discounted_bpas = self.adapter.apply_discounting(loaded_data, alphas)
            
            step_result = {
                'alphas': alphas,
                'discounted_bpas': discounted_bpas,
                'combined_bpa': {},
                'beliefs': {},
                'plausibilities': {}
            }
            
            # Создаем временные данные с дисконтированными BPA
            # Для этого нужно создать структуру, похожую на исходные данные,
            # но с дисконтированными BPA
            discounted_data = {
                'frame': set(frame_elements),
                'frame_elements': frame_elements,
                'bpas': []
            }
            
            # Конвертируем строковые BPA во внутренний формат адаптера
            # (зависит от реализации адаптера)
            for bpa_str in discounted_bpas:
                # Создаем временный BPA в формате адаптера
                temp_bpa = {}
                for subset_str, mass in bpa_str.items():
                    # Преобразуем строку во frozenset
                    if subset_str == "{}":
                        subset = frozenset()
                    else:
                        elements = subset_str.strip("{}").split(",")
                        subset = frozenset(elements)
                    temp_bpa[subset] = mass
                
                discounted_data['bpas'].append(temp_bpa)
            
            # Комбинируем дисконтированные источники по Демпстеру
            combined_bpa = self.adapter.combine_sources_dempster(discounted_data)
            step_result['combined_bpa'] = combined_bpa
            
            # Создаем данные для вычисления Belief/Plausibility
            combined_data = {
                'bpa': combined_bpa,
                'frame': set(frame_elements),
                'frame_elements': frame_elements
            }
            
            # Вычисляем Belief и Plausibility для каждого элемента
            for element in frame_elements:
                event = f"{{{element}}}"
                bel = self.adapter.calculate_belief(combined_data, event)
                pl = self.adapter.calculate_plausibility(combined_data, event)
                
                step_result['beliefs'][event] = bel
                step_result['plausibilities'][event] = pl
            
            # Добавляем для всего фрейма Ω
            omega_str = "{" + ",".join(sorted(frame_elements)) + "}"
            step_result['beliefs'][omega_str] = 1.0
            step_result['plausibilities'][omega_str] = 1.0
            
            # Конфликт
            if combined_bpa:
                conflict = combined_bpa.get("{}", 0.0)
                step_result['conflict_K'] = conflict
            
            return step_result
            
        except Exception as e:
            error_msg = f"Ошибка в шаге 3: {str(e)}"
            self._log(error_msg, "ERROR")
            result.add_error(error_msg)
            raise
    
    def _execute_step4(self, loaded_data: Any, result: TestResult) -> Dict[str, Any]:
        """
        Шаг 4: Комбинирование всех источников по правилу Ягера.
        """
        self._log(f"Выполнение шага 4 для теста {result.test_name}")
        
        try:
            # Получаем фрейм различения
            frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
            
            # Комбинируем все источники по Ягеру
            combined_bpa = self.adapter.combine_sources_yager(loaded_data)
            
            # Создаем временные данные с комбинированным BPA
            combined_data = {
                'bpa': combined_bpa,
                'frame': set(frame_elements),
                'frame_elements': frame_elements
            }
            
            step_result = {
                'combined_bpa': combined_bpa,
                'beliefs': {},
                'plausibilities': {}
            }
            
            # Вычисляем Belief и Plausibility для каждого элемента
            for element in frame_elements:
                event = f"{{{element}}}"
                bel = self.adapter.calculate_belief(combined_data, event)
                pl = self.adapter.calculate_plausibility(combined_data, event)
                
                step_result['beliefs'][event] = bel
                step_result['plausibilities'][event] = pl
            
            # Добавляем для всего фрейма Ω
            omega_str = "{" + ",".join(sorted(frame_elements)) + "}"
            step_result['beliefs'][omega_str] = 1.0
            step_result['plausibilities'][omega_str] = 1.0
            
            # В правиле Ягера конфликт переносится в универсальное множество
            if combined_bpa:
                omega_set = frozenset(frame_elements)
                conflict_mass = combined_bpa.get(omega_set, {}).get("mass", 0.0)
                step_result['conflict_in_omega'] = conflict_mass
            
            return step_result
            
        except Exception as e:
            error_msg = f"Ошибка в шаге 4: {str(e)}"
            self._log(error_msg, "ERROR")
            result.add_error(error_msg)
            raise
    
    def run_single_test(self, test_data: Dict[str, Any], 
                       iterations: int = 3,
                       alphas: Optional[List[float]] = None,
                       enable_profiling: bool = False) -> TestResult:
        """
        Запускает один тест указанное количество раз.
        
        Args:
            test_data: Тестовые данные в формате DASS
            iterations: Количество повторений теста
            alphas: Коэффициенты дисконтирования для каждого источника
            enable_profiling: Включить детальное профилирование
            
        Returns:
            TestResult: Результаты выполнения теста
        """
        test_name = test_data.get('metadata', {}).get('test_id', 'unknown_test')
        
        self._log(f"Запуск теста: {test_name} ({iterations} итераций)")
        self.current_iteration = 0
        self.total_iterations = iterations
        
        # Создаем объект результата
        result = TestResult(test_name)
        
        # Начинаем профилирование, если включено
        if enable_profiling and PROFILE_AVAILABLE:
            self.profiler = cProfile.Profile()
            self.profiler.enable()
        
        try:
            # Загружаем данные через адаптер
            loaded_data = self.adapter.load_from_dass(test_data)
            
            # Запускаем итерации
            for iteration in range(iterations):
                self.current_iteration = iteration + 1
                self._log(f"Итерация {self.current_iteration}/{iterations}")
                
                # Шаг 1: Исходные Belief/Plausibility
                start_total = time.perf_counter()
                
                step1_result, step1_metrics = self._measure_performance(
                    self._execute_step1, loaded_data, result
                )
                result.performance['step1'].add_execution_time(step1_metrics['execution_time_ms'])
                result.performance['step1'].add_memory_usage(step1_metrics['memory_delta_bytes'])
                result.performance['step1'].add_cpu_percentage(step1_metrics['cpu_percent'])
                
                # Шаг 2: Комбинирование Демпстером
                step2_result, step2_metrics = self._measure_performance(
                    self._execute_step2, loaded_data, result
                )
                result.performance['step2'].add_execution_time(step2_metrics['execution_time_ms'])
                result.performance['step2'].add_memory_usage(step2_metrics['memory_delta_bytes'])
                result.performance['step2'].add_cpu_percentage(step2_metrics['cpu_percent'])
                
                # Шаг 3: Дисконтирование + Демпстер
                step3_result, step3_metrics = self._measure_performance(
                    self._execute_step3, loaded_data, alphas, result
                )
                result.performance['step3'].add_execution_time(step3_metrics['execution_time_ms'])
                result.performance['step3'].add_memory_usage(step3_metrics['memory_delta_bytes'])
                result.performance['step3'].add_cpu_percentage(step3_metrics['cpu_percent'])
                
                # Шаг 4: Комбинирование Ягером
                step4_result, step4_metrics = self._measure_performance(
                    self._execute_step4, loaded_data, result
                )
                result.performance['step4'].add_execution_time(step4_metrics['execution_time_ms'])
                result.performance['step4'].add_memory_usage(step4_metrics['memory_delta_bytes'])
                result.performance['step4'].add_cpu_percentage(step4_metrics['cpu_percent'])
                
                # Общее время
                end_total = time.perf_counter()
                total_time_ms = (end_total - start_total) * 1000
                result.performance['total'].add_execution_time(total_time_ms)
                
                # Сохраняем результаты первой итерации
                if iteration == 0:
                    result.step1_original = step1_result
                    result.step2_dempster = step2_result
                    result.step3_discount = step3_result
                    result.step4_yager = step4_result
            
            self._log(f"Тест {test_name} завершен успешно")
            
        except Exception as e:
            error_msg = f"Критическая ошибка в тесте {test_name}: {str(e)}"
            self._log(error_msg, "ERROR")
            result.add_error(error_msg)
        
        finally:
            # Останавливаем профилирование
            if enable_profiling and PROFILE_AVAILABLE and self.profiler:
                self.profiler.disable()
                self.profile_results[test_name] = self.profiler
        
        # Добавляем результат в список
        self.results.append(result)
        
        return result
    
    def run_test_suite(self, test_suite: Dict[str, List[Dict]], 
                      iterations: int = 3,
                      alphas: Optional[List[float]] = None) -> List[TestResult]:
        """
        Запускает набор тестов.
        
        Args:
            test_suite: Словарь {группа: [список_тестов]}
            iterations: Количество повторений каждого теста
            alphas: Коэффициенты дисконтирования
            
        Returns:
            List[TestResult]: Результаты всех тестов
        """
        all_results = []
        
        for group_name, tests in test_suite.items():
            self._log(f"Запуск группы тестов: {group_name} ({len(tests)} тестов)")
            
            for test_idx, test_data in enumerate(tests, 1):
                self._log(f"Тест {test_idx}/{len(tests)} в группе {group_name}")
                
                try:
                    result = self.run_single_test(test_data, iterations, alphas)
                    all_results.append(result)
                except Exception as e:
                    self._log(f"Пропуск теста из-за ошибки: {str(e)}", "ERROR")
        
        return all_results
    
    def save_results(self, output_dir: str, format: str = "json"):
        """
        Сохраняет результаты в указанную директорию.
        
        Args:
            output_dir: Директория для сохранения результатов
            format: Формат сохранения ("json" или "all")
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Сохраняем каждый результат отдельно
        for result in self.results:
            # Создаем директорию для теста
            test_dir = output_path / result.test_name
            test_dir.mkdir(exist_ok=True)
            
            # Сохраняем в JSON
            json_file = test_dir / f"result_{timestamp}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Сохраняем агрегированный отчет
        self._save_aggregated_report(output_path, timestamp)
        
        # Сохраняем профили, если есть
        if self.profile_results:
            self._save_profiles(output_path, timestamp)
    
    def _save_aggregated_report(self, output_path: Path, timestamp: str):
        """Сохраняет агрегированный отчет по всем тестам"""
        aggregated = {
            'metadata': {
                'timestamp': timestamp,
                'total_tests': len(self.results),
                'library': self.adapter.__class__.__name__
            },
            'summary': self._generate_summary(),
            'tests': [result.to_dict() for result in self.results]
        }
        
        report_file = output_path / f"aggregated_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2, ensure_ascii=False)
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Генерирует сводную статистику по всем тестам"""
        if not self.results:
            return {}
        
        summary = {
            'performance_by_step': {},
            'overall_metrics': {
                'total_tests': len(self.results),
                'failed_tests': sum(1 for r in self.results if r.errors),
                'total_iterations': self.total_iterations
            }
        }
        
        # Собираем метрики по шагам
        steps = ['step1', 'step2', 'step3', 'step4', 'total']
        
        for step in steps:
            step_times = []
            step_memory = []
            
            for result in self.results:
                perf_summary = result.performance[step].get_summary()
                if 'time_ms' in perf_summary:
                    step_times.append(perf_summary['time_ms']['mean'])
                if 'memory_bytes' in perf_summary:
                    step_memory.append(perf_summary['memory_bytes']['peak'])
            
            if step_times:
                summary['performance_by_step'][step] = {
                    'avg_time_ms': statistics.mean(step_times) if step_times else 0,
                    'min_time_ms': min(step_times) if step_times else 0,
                    'max_time_ms': max(step_times) if step_times else 0,
                    'avg_memory_mb': (statistics.mean(step_memory) / 1024 / 1024) if step_memory else 0
                }
        
        return summary
    
    def _save_profiles(self, output_path: Path, timestamp: str):
        """Сохраняет результаты профилирования"""
        profiles_dir = output_path / "profiles"
        profiles_dir.mkdir(exist_ok=True)
        
        for test_name, profiler in self.profile_results.items():
            # Сохраняем сырые статистики
            stats_file = profiles_dir / f"profile_{test_name}_{timestamp}.prof"
            
            # Создаем читаемый отчет
            report_file = profiles_dir / f"profile_{test_name}_{timestamp}.txt"
            with open(report_file, 'w') as f:
                stats = pstats.Stats(profiler, stream=f)
                stats.sort_stats('cumulative')
                stats.print_stats(50)  # Топ 50 функций
        
        self._log(f"Профили сохранены в {profiles_dir}")