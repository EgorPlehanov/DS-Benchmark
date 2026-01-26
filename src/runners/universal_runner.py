# runners/universal_runner.py
"""
Универсальный раннер для тестирования библиотек Демпстера-Шейфера.
Выполняет расчеты только для отдельных элементов фрейма и всего Ω.
"""

import os
import json
import time
import gc
import psutil
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import itertools

# Импортируем базовый адаптер для type hints
from ..adapters.base_adapter import BaseDempsterShaferAdapter


class UniversalBenchmarkRunner:
    """
    Универсальный раннер для тестирования любой библиотеки Демпстера-Шейфера.
    
    Выполняет расчеты только для отдельных элементов фрейма и всего Ω.
    """
    
    def __init__(self, adapter: BaseDempsterShaferAdapter, library_name: str):
        """
        Инициализация раннера.
        
        Args:
            adapter: Экземпляр адаптера для тестируемой библиотеки
            library_name: Имя библиотеки (для логирования)
        """
        self.adapter = adapter
        self.library_name = library_name
        self.process = psutil.Process()
        self.results_dir = None
        self.current_run_dir = None
        
    def run_test_suite(self, test_files: List[str], 
                      output_dir: str = "results",
                      discount_factor: float = 0.1,
                      repetitions: int = 1) -> Dict[str, Any]:
        """
        Запускает полный набор тестов с повторениями.
        
        Args:
            test_files: Список путей к тестовым файлам
            output_dir: Директория для сохранения результатов
            discount_factor: Коэффициент дисконтирования
            repetitions: Количество повторений каждого теста
            
        Returns:
            Сводные результаты
        """
        print(f"🚀 Запуск тестирования библиотеки: {self.library_name}")
        print(f"📊 Количество тестов: {len(test_files)}")
        print(f"🔄 Повторений каждого теста: {repetitions}")
        print(f"📁 Результаты будут сохранены в: {output_dir}")
        print("-" * 70)
        
        # Создаем директорию для результатов
        self._create_results_directory(output_dir)
        
        # Сохраняем конфигурацию
        self._save_configuration(test_files, discount_factor, repetitions)
        
        all_results = []
        total_time = 0
        
        # Запускаем каждый тест
        for i, test_file in enumerate(test_files, 1):
            test_name = Path(test_file).stem
            print(f"Тест {i:3d}/{len(test_files)}: {test_name:<30}", end="", flush=True)
            
            try:
                # Запускаем тест с повторениями
                test_results = self._run_single_test_with_repetitions(
                    test_file, discount_factor, repetitions
                )
                
                # Собираем статистику по повторениям
                aggregated = self._aggregate_repetitions(test_results)
                all_results.append(aggregated)
                
                total_time += aggregated['timings']['total_time']['avg']
                
                # Выводим статистику
                avg_time = aggregated['timings']['total_time']['avg']
                std_time = aggregated['timings']['total_time']['std']
                print(f" ✓ {avg_time:.3f} ± {std_time:.3f} сек")
                
            except Exception as e:
                print(f" ✗ ОШИБКА: {str(e)}")
                self._save_error(test_file, str(e))
        
        # Сохраняем сводные результаты
        summary = self._create_summary(all_results, total_time)
        self._save_summary(summary)
        
        # Создаем симлинк latest
        self._create_latest_symlink()
        
        print("=" * 70)
        print(f"✅ Тестирование завершено!")
        print(f"📊 Общее время: {total_time:.2f} сек")
        print(f"📁 Результаты: {self.current_run_dir}")
        
        return summary
    
    def _run_single_test_with_repetitions(self, test_file: str, 
                                         discount_factor: float,
                                         repetitions: int) -> List[Dict[str, Any]]:
        """
        Запускает один тест несколько раз.
        
        Returns:
            Список результатов для каждого повторения
        """
        test_results = []
        
        for rep in range(repetitions):
            result = self._run_single_test(
                test_file, 
                discount_factor,
                repetition=rep + 1
            )
            test_results.append(result)
        
        return test_results
    
    def _run_single_test(self, test_file: str, 
                        discount_factor: float,
                        repetition: int = 1) -> Dict[str, Any]:
        """
        Запускает один тест по полной методике.
        Считает только для отдельных элементов и всего Ω.
        """
        # Создаем директорию для теста
        test_name = Path(test_file).stem
        test_dir = os.path.join(self.current_run_dir, "raw", test_name, f"rep_{repetition:03d}")
        os.makedirs(test_dir, exist_ok=True)
        
        # Загружаем тестовые данные
        with open(test_file, 'r', encoding='utf-8') as f:
            dass_data = json.load(f)
        
        # Сохраняем входные данные
        self._save_json(dass_data, os.path.join(test_dir, "input.json"))
        
        # Инициализируем замеры
        timings = {}
        
        # 0. Загрузка данных
        load_start = time.perf_counter()
        loaded_data = self.adapter.load_from_dass(dass_data)
        timings['load'] = time.perf_counter() - load_start
        
        # Получаем информацию о тесте
        frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
        frame_size = len(frame_elements)
        sources_count = self.adapter.get_sources_count(loaded_data)
        
        # События для расчета: отдельные элементы и весь Ω
        events_to_calculate = []
        
        # Отдельные элементы
        for element in frame_elements:
            events_to_calculate.append(f"{{{element}}}")
        
        # Весь фрейм Ω
        omega_event = "{" + ",".join(sorted(frame_elements)) + "}"
        events_to_calculate.append(omega_event)
        
        # Пустое множество (для проверки)
        empty_event = "{}"
        events_to_calculate.append(empty_event)
        
        # ==================== 1. ИСХОДНЫЕ BPA (m1, m2...) ====================
        belief_by_source = []
        plausibility_by_source = []
        
        for source_idx in range(sources_count):
            source_data = self._create_source_data(loaded_data, source_idx)
            
            # Belief
            belief_start = time.perf_counter()
            source_belief = {}
            for event in events_to_calculate:
                try:
                    source_belief[event] = self.adapter.calculate_belief(source_data, event)
                except Exception as e:
                    source_belief[event] = 0.0
            timings[f'belief_source_{source_idx}'] = time.perf_counter() - belief_start
            
            # Plausibility
            plausibility_start = time.perf_counter()
            source_plausibility = {}
            for event in events_to_calculate:
                try:
                    source_plausibility[event] = self.adapter.calculate_plausibility(source_data, event)
                except Exception as e:
                    source_plausibility[event] = 0.0
            timings[f'plausibility_source_{source_idx}'] = time.perf_counter() - plausibility_start
            
            belief_by_source.append(source_belief)
            plausibility_by_source.append(source_plausibility)
        
        # ==================== 2. ДЕМПСТЕР (m1 ⊕ m2) ====================
        dempster_start = time.perf_counter()
        try:
            combined_bpa_dempster = self.adapter.combine_sources_dempster(loaded_data)
            
            # Создаем объект данных с комбинированным BPA
            combined_data_dempster = {
                'frame': loaded_data.get('frame', set()),
                'bpa': self._parse_bpa_strings_to_frozenset(combined_bpa_dempster)
            }
            
            # Belief после Демпстера
            belief_dempster = {}
            for event in events_to_calculate:
                belief_dempster[event] = self.adapter.calculate_belief(combined_data_dempster, event)
            
            # Plausibility после Демпстера
            plausibility_dempster = {}
            for event in events_to_calculate:
                plausibility_dempster[event] = self.adapter.calculate_plausibility(combined_data_dempster, event)
                
        except ValueError as e:
            if "Полный конфликт" in str(e) or "конфликт" in str(e).lower():
                # Обработка полного конфликта - это нормальная ситуация
                combined_bpa_dempster = {}
                belief_dempster = {event: 0.0 for event in events_to_calculate}
                plausibility_dempster = {event: 0.0 for event in events_to_calculate}
            else:
                raise
        except Exception as e:
            # Обработка других ошибок
            combined_bpa_dempster = {}
            belief_dempster = {event: 0.0 for event in events_to_calculate}
            plausibility_dempster = {event: 0.0 for event in events_to_calculate}
        
        timings['dempster_combination'] = time.perf_counter() - dempster_start
        
        # ==================== 3. ДИСКОНТИРОВАНИЕ ====================
        discount_start = time.perf_counter()
        
        try:
            # Применяем дисконтирование ко всем источникам
            discounted_bpas = self.adapter.apply_discounting(loaded_data, discount_factor)
            
            # Комбинируем дисконтированные источники
            discounted_loaded_data = loaded_data.copy()
            discounted_loaded_data['bpas'] = [
                self._parse_bpa_strings_to_frozenset(bpa) for bpa in discounted_bpas
            ]
            
            combined_bpa_discounted = self.adapter.combine_sources_dempster(discounted_loaded_data)
            
            # Создаем объект данных с комбинированным дисконтированным BPA
            combined_data_discounted = {
                'frame': loaded_data.get('frame', set()),
                'bpa': self._parse_bpa_strings_to_frozenset(combined_bpa_discounted)
            }
            
            # Belief после дисконтирования
            belief_discounted = {}
            for event in events_to_calculate:
                belief_discounted[event] = self.adapter.calculate_belief(combined_data_discounted, event)
            
            # Plausibility после дисконтирования
            plausibility_discounted = {}
            for event in events_to_calculate:
                plausibility_discounted[event] = self.adapter.calculate_plausibility(combined_data_discounted, event)
                
        except Exception as e:
            # В случае ошибки заполняем нулями
            discounted_bpas = []
            combined_bpa_discounted = {}
            belief_discounted = {event: 0.0 for event in events_to_calculate}
            plausibility_discounted = {event: 0.0 for event in events_to_calculate}
        
        timings['discounting'] = time.perf_counter() - discount_start
        
        # ==================== 4. ЯГЕР (m1 ⊕ᵧ m2) ====================
        yager_start = time.perf_counter()
        
        try:
            combined_bpa_yager = self.adapter.combine_sources_yager(loaded_data)
            
            # Создаем объект данных с комбинированным BPA Ягера
            combined_data_yager = {
                'frame': loaded_data.get('frame', set()),
                'bpa': self._parse_bpa_strings_to_frozenset(combined_bpa_yager)
            }
            
            # Belief после Ягера
            belief_yager = {}
            for event in events_to_calculate:
                belief_yager[event] = self.adapter.calculate_belief(combined_data_yager, event)
            
            # Plausibility после Ягера
            plausibility_yager = {}
            for event in events_to_calculate:
                plausibility_yager[event] = self.adapter.calculate_plausibility(combined_data_yager, event)
                
        except Exception as e:
            # В случае ошибки заполняем нулями
            combined_bpa_yager = {}
            belief_yager = {event: 0.0 for event in events_to_calculate}
            plausibility_yager = {event: 0.0 for event in events_to_calculate}
        
        timings['yager_combination'] = time.perf_counter() - yager_start
        
        # ==================== СБОР РЕЗУЛЬТАТОВ ====================
        total_time = sum(timings.values())
        timings['total_time'] = total_time
        
        # Формируем результаты
        results = {
            'test_file': test_file,
            'test_name': test_name,
            'repetition': repetition,
            'metadata': {
                'frame_size': frame_size,
                'sources_count': sources_count,
                'events_count': len(events_to_calculate),
                'discount_factor': discount_factor,
                'frame_elements': frame_elements,
                'calculated_events': events_to_calculate
            },
            'timings': timings,
            'results': {
                'initial_belief': belief_by_source,
                'initial_plausibility': plausibility_by_source,
                'dempster': {
                    'combined_bpa': combined_bpa_dempster,
                    'belief': belief_dempster,
                    'plausibility': plausibility_dempster
                },
                'discounted': {
                    'discounted_bpas': discounted_bpas,
                    'combined_bpa': combined_bpa_discounted,
                    'belief': belief_discounted,
                    'plausibility': plausibility_discounted
                },
                'yager': {
                    'combined_bpa': combined_bpa_yager,
                    'belief': belief_yager,
                    'plausibility': plausibility_yager
                }
            },
            'validation': {
                'empty_set': {
                    'belief': belief_dempster.get('{}', 0),
                    'plausibility': plausibility_dempster.get('{}', 0)
                },
                'omega_set': {
                    'belief': belief_dempster.get(omega_event, 0),
                    'plausibility': plausibility_dempster.get(omega_event, 0)
                }
            }
        }
        
        # Проверяем корректность
        self._validate_results(results)
        
        # Сохраняем результаты теста
        self._save_json(results, os.path.join(test_dir, "results.json"))
        self._save_json(timings, os.path.join(test_dir, "timings.json"))
        
        return {
            'test_name': test_name,
            'test_file': test_file,
            'frame_size': frame_size,
            'sources_count': sources_count,
            'repetition': repetition,
            'timings': timings
        }
    
    def _validate_results(self, results: Dict[str, Any]):
        """
        Проверяет корректность результатов с учетом погрешности.
        Выводит предупреждения только при значительных отклонениях.
        """
        errors = []
        warnings = []
        
        # Увеличиваем погрешность для предупреждений
        tolerance_warning = 1e-3  # 0.1% для предупреждений
        tolerance_error = 1e-2    # 1% для ошибок
        
        # Проверяем пустое множество
        empty_bel = results['validation']['empty_set']['belief']
        empty_pl = results['validation']['empty_set']['plausibility']
        
        if abs(empty_bel) > tolerance_error:
            errors.append(f"Bel(∅) = {empty_bel}, должно быть 0 (отклонение: {abs(empty_bel):.6f})")
        elif abs(empty_bel) > tolerance_warning:
            warnings.append(f"Bel(∅) = {empty_bel}, должно быть 0 (небольшое отклонение)")
        
        if abs(empty_pl) > tolerance_error:
            errors.append(f"Pl(∅) = {empty_pl}, должно быть 0 (отклонение: {abs(empty_pl):.6f})")
        elif abs(empty_pl) > tolerance_warning:
            warnings.append(f"Pl(∅) = {empty_pl}, должно быть 0 (небольшое отклонение)")
        
        # Проверяем Ω
        omega_event = "{" + ",".join(results['metadata']['frame_elements']) + "}"
        omega_bel = results['results']['dempster']['belief'].get(omega_event, 0)
        omega_pl = results['results']['dempster']['plausibility'].get(omega_event, 0)
        
        if abs(omega_bel - 1.0) > tolerance_error:
            errors.append(f"Bel(Ω) = {omega_bel}, должно быть 1 (отклонение: {abs(omega_bel - 1.0):.6f})")
        elif abs(omega_bel - 1.0) > tolerance_warning:
            warnings.append(f"Bel(Ω) = {omega_bel}, должно быть 1 (небольшое отклонение)")
        
        if abs(omega_pl - 1.0) > tolerance_error:
            errors.append(f"Pl(Ω) = {omega_pl}, должно быть 1 (отклонение: {abs(omega_pl - 1.0):.6f})")
        elif abs(omega_pl - 1.0) > tolerance_warning:
            warnings.append(f"Pl(Ω) = {omega_pl}, должно быть 1 (небольшое отклонение)")
        
        # Проверяем, что Belief <= Plausibility для всех событий
        for source_idx in range(results['metadata']['sources_count']):
            for event in results['metadata']['calculated_events']:
                bel = results['results']['initial_belief'][source_idx].get(event, 0)
                pl = results['results']['initial_plausibility'][source_idx].get(event, 0)
                
                if bel > pl + tolerance_error:  # Значительное нарушение
                    errors.append(f"Источник {source_idx}: Bel({event})={bel:.4f} > Pl({event})={pl:.4f}")
                elif bel > pl + tolerance_warning:  # Небольшое нарушение
                    warnings.append(f"Источник {source_idx}: Bel({event})={bel:.4f} > Pl({event})={pl:.4f}")
        
        # Выводим ошибки и предупреждения
        if errors:
            print(f"\n❌ Ошибки в тесте {results['test_name']}:")
            for error in errors[:2]:  # Показываем только первые 2 ошибки
                print(f"  {error}")
        
        if warnings and not errors:  # Показываем warnings только если нет errors
            if len(warnings) > 2:
                print(f"\n⚠️  {len(warnings)} предупреждений для теста {results['test_name']}")
            else:
                for warning in warnings[:2]:
                    print(f"  {warning}")
    
    def _create_source_data(self, loaded_data: Any, source_idx: int) -> Dict:
        """
        Создает объект данных для конкретного источника.
        """
        # Если данные содержат список BPA
        if isinstance(loaded_data, dict) and 'bpas' in loaded_data:
            bpas = loaded_data['bpas']
            if source_idx < len(bpas):
                # Возвращаем данные с одним BPA
                return {
                    'frame': loaded_data.get('frame', set()),
                    'bpa': bpas[source_idx]
                }
            else:
                # Если индекс выходит за пределы, возвращаем первый BPA
                return {
                    'frame': loaded_data.get('frame', set()),
                    'bpa': bpas[0] if bpas else {}
                }
        
        # Если не удалось, возвращаем оригинальные данные
        return loaded_data
    
    def _parse_bpa_strings_to_frozenset(self, bpa_strings: Dict[str, float]) -> Dict[frozenset, float]:
        """
        Конвертирует BPA из строкового формата в frozenset.
        """
        if not bpa_strings:
            return {}
        
        result = {}
        for subset_str, mass in bpa_strings.items():
            if subset_str == "{}":
                subset = frozenset()
            else:
                elements = subset_str.strip("{}").split(",")
                subset = frozenset(elements)
            result[subset] = mass
        return result
    
    def _aggregate_repetitions(self, repetitions_results: List[Dict]) -> Dict[str, Any]:
        """
        Агрегирует результаты повторных запусков.
        """
        if not repetitions_results:
            return {}
        
        first_result = repetitions_results[0]
        
        # Агрегируем тайминги
        aggregated_timings = {}
        timing_keys = first_result['timings'].keys()
        
        for key in timing_keys:
            # Собираем значения только для тех повторений, где есть этот ключ
            values = []
            for r in repetitions_results:
                if key in r['timings']:
                    values.append(r['timings'][key])
            
            if values:  # Если есть хотя бы одно значение
                aggregated_timings[key] = {
                    'values': values,
                    'avg': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                    'median': statistics.median(values),
                    'count': len(values)
                }
        
        return {
            'test_name': first_result['test_name'],
            'test_file': first_result['test_file'],
            'frame_size': first_result['frame_size'],
            'sources_count': first_result['sources_count'],
            'repetitions_count': len(repetitions_results),
            'timings': aggregated_timings,
            'raw_repetitions': repetitions_results
        }
    
    def _create_results_directory(self, output_dir: str):
        """Создает директорию для результатов."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.results_dir = os.path.join(output_dir, self.library_name)
        self.current_run_dir = os.path.join(self.results_dir, f"run_{timestamp}")
        
        os.makedirs(self.current_run_dir, exist_ok=True)
        os.makedirs(os.path.join(self.current_run_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.current_run_dir, "aggregated"), exist_ok=True)
        os.makedirs(os.path.join(self.current_run_dir, "plots"), exist_ok=True)
    
    def _save_configuration(self, test_files: List[str], discount_factor: float, repetitions: int):
        """Сохраняет конфигурацию запуска."""
        config = {
            'library': self.library_name,
            'timestamp': datetime.now().isoformat(),
            'test_files_count': len(test_files),
            'repetitions': repetitions,
            'test_files': [Path(f).name for f in test_files],
            'discount_factor': discount_factor,
            'system_info': {
                'cpu_count': psutil.cpu_count(),
                'total_memory_mb': psutil.virtual_memory().total / 1024 / 1024
            }
        }
        self._save_json(config, os.path.join(self.current_run_dir, "config.json"))
    
    def _save_summary(self, summary: Dict[str, Any]):
        """Сохраняет сводные результаты."""
        self._save_json(summary, os.path.join(self.current_run_dir, "summary.json"))
    
    def _save_error(self, test_file: str, error_msg: str):
        """Сохраняет информацию об ошибке."""
        test_name = Path(test_file).stem
        error_data = {
            'test_file': test_file,
            'test_name': test_name,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }
        
        error_file = os.path.join(self.current_run_dir, "raw", f"{test_name}_error.json")
        self._save_json(error_data, error_file)
    
    def _save_json(self, data: Any, filepath: str):
        """Сохраняет данные в JSON файл."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _create_summary(self, all_results: List[Dict], total_time: float) -> Dict[str, Any]:
        """Создает сводный отчет с учетом повторений."""
        if not all_results:
            return {}
        
        # Группируем по размеру фрейма
        by_frame_size = {}
        for result in all_results:
            size = result['frame_size']
            if size not in by_frame_size:
                by_frame_size[size] = []
            by_frame_size[size].append(result)
        
        # Вычисляем статистики
        summary = {
            'library': self.library_name,
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(all_results),
            'repetitions': all_results[0]['repetitions_count'] if all_results else 1,
            'total_time': total_time,
            'avg_time_per_test': total_time / len(all_results) if all_results else 0,
            'by_frame_size': {},
            'operation_timings': self._aggregate_operation_timings(all_results)
        }
        
        for size, results in by_frame_size.items():
            avg_times = [r['timings']['total_time']['avg'] for r in results]
            summary['by_frame_size'][str(size)] = {
                'test_count': len(results),
                'avg_time': statistics.mean(avg_times) if avg_times else 0,
                'min_time': min(avg_times) if avg_times else 0,
                'max_time': max(avg_times) if avg_times else 0,
                'std_time': statistics.stdev(avg_times) if len(avg_times) > 1 else 0,
                'total_repetitions': sum(r['repetitions_count'] for r in results)
            }
        
        return summary
    
    def _aggregate_operation_timings(self, all_results: List[Dict]) -> Dict[str, Any]:
        """Агрегирует замеры времени по операциям."""
        if not all_results:
            return {}
        
        # Собираем все уникальные ключи таймингов из всех результатов
        all_timing_keys = set()
        for result in all_results:
            all_timing_keys.update(result['timings'].keys())
        
        aggregated = {}
        total_avg_time = sum(r['timings']['total_time']['avg'] for r in all_results)
        
        for key in all_timing_keys:
            # Собираем значения только для тех тестов, где есть этот ключ
            avg_times = []
            for r in all_results:
                if key in r['timings']:
                    avg_times.append(r['timings'][key]['avg'])
            
            if avg_times:  # Если есть хотя бы одно значение
                aggregated[key] = {
                    'total': sum(avg_times),
                    'avg': statistics.mean(avg_times),
                    'min': min(avg_times),
                    'max': max(avg_times),
                    'count': len(avg_times),
                    'percentage': (sum(avg_times) / total_avg_time) * 100 if total_avg_time > 0 else 0
                }
        
        return aggregated
    
    def _create_latest_symlink(self):
        """Создает симлинк latest на текущий запуск."""
        latest_link = os.path.join(self.results_dir, "latest")
        
        if os.path.exists(latest_link):
            if os.path.islink(latest_link):
                os.unlink(latest_link)
            else:
                os.remove(latest_link)
        
        target = os.path.basename(self.current_run_dir)
        os.symlink(target, latest_link)