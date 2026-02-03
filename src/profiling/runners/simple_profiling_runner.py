# src/profiling/runners/simple_profiling_runner.py
"""
Основной раннер для сбора артефактов профилирования.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import sys

# Локальные импорты
try:
    from ..artifacts.artifact_manager import ArtifactManager
    from ..artifacts.metadata_collector import MetadataCollector
    from ..collectors.system_profiler import SystemProfiler
    from ..test_input_manager import TestInputManager, TestCase
except ImportError:
    # Для случаев, когда запускаем из другой директории
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.profiling.artifacts.artifact_manager import ArtifactManager
    from src.profiling.artifacts.metadata_collector import MetadataCollector
    from src.profiling.collectors.system_profiler import SystemProfiler
    from src.profiling.test_input_manager import TestInputManager, TestCase

# Импорт адаптера
try:
    from src.adapters.our_adapter import OurImplementationAdapter
except ImportError:
    # Для случаев, когда запускаем из другой директории
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.adapters.our_adapter import OurImplementationAdapter

class SimpleProfilingRunner:
    """
    Главный раннер для сбора артефактов профилирования.
    """
    
    def __init__(self, 
                 adapter,
                 tests_dir: Union[str, Path],
                 output_dir: str = "artifacts",
                 session_id: Optional[str] = None):
        """
        Инициализация раннера.
        
        Args:
            adapter: Адаптер Демпстера-Шейфера
            tests_dir: Директория с тестами (строка или Path)
            output_dir: Базовая директория для артефактов
            session_id: ID сессии (если None, генерируется)
        """
        self.adapter = adapter
        self.adapter_name = adapter.__class__.__name__.replace('Adapter', '').lower()
        
        # Конвертируем tests_dir в Path
        self.tests_dir = Path(tests_dir)
        
        # Инициализируем менеджер артефактов
        self.artifact_manager = ArtifactManager(
            base_dir=output_dir,
            session_id=session_id
        )
        
        # Инициализируем менеджер тестов
        self.test_manager = TestInputManager(self.tests_dir)
        
        # Инициализируем профилировщики
        self.system_profiler = SystemProfiler(track_memory=True, track_gc=True)
        
        # Конфигурация по умолчанию
        self.config = {
            'adapter': self.adapter_name,
            'tests_dir': str(tests_dir),
            'output_dir': output_dir,
            'session_id': self.artifact_manager.session_id,
            'created_at': datetime.now().isoformat(),
            'system_profiler': {
                'track_memory': True,
                'track_gc': True
            }
        }
        
        # Собираем метаданные
        self._collect_metadata()
        
        # Сохраняем конфигурацию
        self.artifact_manager.save_config(self.config)
        
        print(f"🚀 SimpleProfilingRunner инициализирован")
        print(f"📁 Сессия: {self.artifact_manager.session_id}")
        
        # Проверяем тесты
        test_count = len(self.test_manager.discover_tests(max_tests=1))
        print(f"📊 Тестов: {test_count}+ обнаружено")
    
    def _collect_metadata(self):
        """Собирает и сохраняет метаданные."""
        metadata_collector = MetadataCollector()
        metadata = metadata_collector.collect_all()
        
        # Добавляем информацию о раннере
        metadata['profiling_runner'] = {
            'name': self.__class__.__name__,
            'adapter': self.adapter_name,
            'version': '1.0.0'
        }
        
        # Сохраняем
        self.artifact_manager.save_metadata(metadata)
    
    
    def run_test(self, 
                test_case: TestCase,
                iterations: int = 3,
                alphas: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Запускает один тест и собирает артефакты.
        
        Args:
            test_case: Тестовый случай
            iterations: Количество итераций
            alphas: Коэффициенты дисконтирования (опционально)
            
        Returns:
            Результаты теста
        """
        print(f"\n🧪 Запуск теста: {test_case.name}")
        print(f"   Фрейм: {test_case.frame_size} элементов")
        print(f"   Источников: {test_case.sources_count}")
        print(f"   Итераций: {iterations}")
        
        # Сохраняем входные данные теста
        self.artifact_manager.save_test_input(test_case.name, test_case.data)
        
        # Загружаем данные через адаптер
        try:
            loaded_data = self.adapter.load_from_dass(test_case.data)
        except Exception as e:
            error_msg = f"Ошибка загрузки данных: {str(e)}"
            print(f"   ❌ {error_msg}")
            
            # Сохраняем информацию об ошибке
            error_result = {
                'test_name': test_case.name,
                'error': error_msg,
                'timestamp': datetime.now().isoformat()
            }
            
            self.artifact_manager.save_test_results(test_case.name, error_result)
            return error_result
        
        # Определяем коэффициенты дисконтирования
        if alphas is None:
            try:
                sources_count = self.adapter.get_sources_count(loaded_data)
                alphas = [0.1] * sources_count
            except:
                alphas = [0.1]  # fallback
        
        # ✅ Гарантируем, что alphas это List[float]
        if not isinstance(alphas, list):
            alphas = [0.1]
        
        # ✅ Преобразуем все элементы к float
        alphas = [float(alpha) for alpha in alphas]
        
        # Результаты теста
        test_results = {
            'test_name': test_case.name,
            'metadata': test_case.get_summary(),
            'config': {
                'iterations': iterations,
                'alphas': alphas,  # Теперь гарантированно List[float]
                'timestamp': datetime.now().isoformat()
            },
            'iterations': [],
            'summary': {}
        }
        
        # Запускаем итерации
        for i in range(iterations):
            print(f"   Итерация {i+1}/{iterations}...", end="", flush=True)
            
            iteration_results = self._run_iteration(
                loaded_data=loaded_data,
                test_name=test_case.name,
                iteration_num=i+1,
                alphas=alphas  # Теперь всегда List[float]
            )
            
            test_results['iterations'].append(iteration_results)
            print(" ✓")
        
        # Собираем сводку
        test_results['summary'] = self._summarize_iterations(test_results['iterations'])
        
        # Сохраняем результаты теста
        self.artifact_manager.save_test_results(test_case.name, test_results)
        
        # Логируем завершение
        self.artifact_manager.log_message(
            f"Тест {test_case.name} завершен. "
            f"Время: {test_results['summary'].get('total_time_seconds', 0):.2f}с"
        )
        
        return test_results

    def _run_iteration(self, 
                      loaded_data: Any,
                      test_name: str,
                      iteration_num: int,
                      alphas: List[float]) -> Dict[str, Any]:  # Убрали Optional, теперь всегда List[float]
        """
        Запускает одну итерацию теста.
        
        Args:
            loaded_data: Загруженные данные адаптера
            test_name: Имя теста
            iteration_num: Номер итерации
            alphas: Коэффициенты дисконтирования (гарантированно List[float])
            
        Returns:
            Результаты итерации
        """
        iteration_results = {
            'iteration': iteration_num,
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'performance': {}
        }
        
        # Определяем шаги тестирования
        steps = [
            ('step1_original', self._execute_step1, [loaded_data]),
            ('step2_dempster', self._execute_step2, [loaded_data]),
            ('step3_discount_dempster', self._execute_step3, [loaded_data, alphas]),  # alphas всегда List[float]
            ('step4_yager', self._execute_step4, [loaded_data])
        ]
        
        # Запускаем каждый шаг
        for step_name, step_func, step_args in steps:
            step_result = self._execute_and_profile_step(
                step_func=step_func,
                step_args=step_args,
                test_name=test_name,
                step_name=step_name,
                iteration_num=iteration_num
            )
            
            iteration_results['steps'][step_name] = step_result['computation']
            iteration_results['performance'][step_name] = step_result['metrics']
        
        # Вычисляем общие метрики итерации
        iteration_results['performance']['total'] = self._calculate_iteration_total(
            iteration_results['performance']
        )
        
        return iteration_results
    
    def _execute_and_profile_step(self,
                                step_func,
                                step_args,
                                test_name: str,
                                step_name: str,
                                iteration_num: int) -> Dict[str, Any]:
        """
        Выполняет шаг и профилирует его.
        
        Returns:
            Словарь с результатами вычисления и метриками
        """
        # Профилируем функцию
        result, metrics = self.system_profiler.profile_function(
            step_func, *step_args
        )
        
        # Сохраняем данные профилирования
        metrics_dict = metrics.to_dict()
        
        self.artifact_manager.save_profiler_data(
            profiler_name='system',
            test_name=test_name,
            step_name=step_name,
            data=metrics_dict,
            iteration=iteration_num
        )
        
        return {
            'computation': result,
            'metrics': metrics_dict
        }
    
    def _execute_step1(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 1: Исходные Belief/Plausibility."""
        try:
            frame_elements = self.adapter.get_frame_of_discernment(loaded_data)
            sources_count = self.adapter.get_sources_count(loaded_data)
            
            results = {
                'frame_elements': frame_elements,
                'sources': []
            }
            
            # Для каждого источника
            for i in range(sources_count):
                source_data = self._get_source_data(loaded_data, i)
                
                source_results = {
                    'source_id': f'source_{i+1}',
                    'beliefs': {},
                    'plausibilities': {}
                }
                
                # Для каждого элемента
                for element in frame_elements:
                    belief = self.adapter.calculate_belief(source_data, element)
                    plausibility = self.adapter.calculate_plausibility(source_data, element)
                    
                    source_results['beliefs'][f'{{{element}}}'] = belief
                    source_results['plausibilities'][f'{{{element}}}'] = plausibility
                
                results['sources'].append(source_results)
            
            return results
        except Exception as e:
            return {'error': f'Step1 error: {str(e)}'}
    
    def _execute_step2(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 2: Комбинирование Демпстером."""
        try:
            combined_bpa = self.adapter.combine_sources_dempster(loaded_data)
            return {'combined_bpa': combined_bpa, 'success': True}
        except ValueError as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in 
                  ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                return {
                    'warning': 'Полный конфликт между источниками (K=1.0)',
                    'full_conflict': True
                }
            else:
                return {'error': f'Step2 error: {str(e)}'}
        except Exception as e:
            return {'error': f'Step2 error: {str(e)}'}
    
    def _execute_step3(self, loaded_data: Any, alphas: List[float]) -> Dict[str, Any]:
        """Шаг 3: Дисконтирование + Демпстер."""
        try:
            sources_count = self.adapter.get_sources_count(loaded_data)
            
            # Применяем дисконтирование
            discounted_bpas = []
            for i in range(sources_count):
                source_data = self._get_source_data(loaded_data, i)
                alpha = alphas[i] if i < len(alphas) else 0.1
                
                discounted = self.adapter.apply_discounting(source_data, alpha)
                if discounted and len(discounted) > 0:
                    discounted_bpas.append(discounted[0])
            
            # Комбинируем
            discounted_data = self._create_discounted_data(loaded_data, discounted_bpas)
            combined_bpa = self.adapter.combine_sources_dempster(discounted_data)
            
            return {
                'discounted_bpas': discounted_bpas,
                'combined_bpa': combined_bpa,
                'success': True
            }
            
        except ValueError as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in 
                  ["полный конфликт", "full conflict", "k=1.0", "конфликт между источниками"]):
                return {
                    'warning': 'Полный конфликт между источниками (K=1.0)',
                    'full_conflict': True
                }
            else:
                return {'error': f'Step3 error: {str(e)}'}
        except Exception as e:
            return {'error': f'Step3 error: {str(e)}'}
    
    def _execute_step4(self, loaded_data: Any) -> Dict[str, Any]:
        """Шаг 4: Комбинирование Ягером."""
        try:
            combined_bpa = self.adapter.combine_sources_yager(loaded_data)
            return {'combined_bpa': combined_bpa, 'success': True}
        except Exception as e:
            return {'error': f'Step4 error: {str(e)}'}
    
    def _get_source_data(self, loaded_data: Any, source_index: int) -> Any:
        """Получает данные для конкретного источника."""
        if isinstance(loaded_data, dict) and 'bpas' in loaded_data:
            single_source_data = loaded_data.copy()
            if source_index < len(loaded_data['bpas']):
                single_source_data['bpas'] = [loaded_data['bpas'][source_index]]
            else:
                single_source_data['bpas'] = [{}]
            return single_source_data
        
        return loaded_data
    
    def _create_discounted_data(self, original_data: Any, discounted_bpas: List) -> Any:
        """Создает данные с дисконтированными BPA."""
        if isinstance(original_data, dict):
            discounted_data = original_data.copy()
            discounted_data['bpas'] = discounted_bpas
            return discounted_data
        
        return original_data
    
    def _calculate_iteration_total(self, performance: Dict[str, Any]) -> Dict[str, Any]:
        """Вычисляет общие метрики итерации."""
        total_time = sum(
            step.get('execution_time_seconds', 0) 
            for step in performance.values() 
            if isinstance(step, dict)
        )
        
        peak_memory = max(
            step.get('peak_memory_bytes', 0) 
            for step in performance.values() 
            if isinstance(step, dict)
        )
        
        return {
            'total_time_seconds': total_time,
            'peak_memory_bytes': peak_memory,
            'peak_memory_mb': peak_memory / (1024 * 1024)
        }
    
    def _summarize_iterations(self, iterations: List[Dict]) -> Dict[str, Any]:
        """Создает сводку по всем итерациям."""
        if not iterations:
            return {}
        
        # Собираем метрики
        step_times = {}
        
        for step in ['step1_original', 'step2_dempster', 
                    'step3_discount_dempster', 'step4_yager']:
            times = []
            
            for iteration in iterations:
                if step in iteration.get('performance', {}):
                    perf = iteration['performance'][step]
                    times.append(perf.get('execution_time_seconds', 0))
            
            if times:
                step_times[step] = {
                    'min': min(times),
                    'max': max(times),
                    'mean': sum(times) / len(times)
                }
        
        # Общие метрики
        total_times = [it['performance']['total']['total_time_seconds'] 
                      for it in iterations if 'performance' in it]
        
        summary = {
            'iterations_count': len(iterations),
            'step_times': step_times,
            'total_time': {
                'min': min(total_times) if total_times else 0,
                'max': max(total_times) if total_times else 0,
                'mean': sum(total_times) / len(total_times) if total_times else 0,
                'total_time_seconds': sum(total_times) if total_times else 0
            },
            'errors': sum(1 for it in iterations 
                         if any('error' in it['steps'].get(step, {}) 
                               for step in it['steps'])),
            'warnings': sum(1 for it in iterations 
                           if any('warning' in it['steps'].get(step, {}) 
                                 for step in it['steps']))
        }
        
        return summary
    
    def run_test_suite(self, 
                      iterations: int = 3,
                      max_tests: Optional[int] = None,
                      filter_by_size: Optional[tuple] = None,
                      filter_by_group: Optional[str] = None) -> Dict[str, Any]:
        """
        Запускает набор тестов.
        
        Args:
            iterations: Итераций на тест
            max_tests: Максимальное количество тестов
            filter_by_size: Фильтр по размеру фрейма
            filter_by_group: Фильтр по группе тестов
            
        Returns:
            Сводка по выполнению
        """
        print(f"\n🚀 ЗАПУСК НАБОРА ТЕСТОВ")
        print(f"📁 Директория: {self.test_manager.tests_dir}")
        print(f"🔄 Итераций на тест: {iterations}")
        
        # Обновляем конфигурацию
        self.config.update({
            'iterations_per_test': iterations,
            'max_tests': max_tests,
            'filter_by_size': filter_by_size,
            'filter_by_group': filter_by_group,
            'suite_started_at': datetime.now().isoformat()
        })
        
        self.artifact_manager.save_config(self.config)
        
        # Получаем тесты
        test_cases = self.test_manager.discover_tests(
            max_tests=max_tests,
            filter_by_size=filter_by_size,
            filter_by_group=filter_by_group
        )
        
        print(f"📄 Тестов для запуска: {len(test_cases)}")
        
        # Сводка выполнения
        suite_summary = {
            'session_id': self.artifact_manager.session_id,
            'start_time': datetime.now().isoformat(),
            'total_tests': len(test_cases),
            'iterations_per_test': iterations,
            'completed_tests': 0,
            'failed_tests': 0,
            'tests_with_warnings': 0,
            'total_execution_time_seconds': 0,
            'test_results': []
        }
        
        start_time = time.time()
        
        # Запускаем каждый тест
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] ", end="")
            
            try:
                test_result = self.run_test(
                    test_case=test_case,
                    iterations=iterations
                )
                
                # Анализируем результат
                has_error = False
                has_warning = False
                
                if test_result.get('iterations'):
                    first_iteration = test_result['iterations'][0]
                    for step_name, step_data in first_iteration.get('steps', {}).items():
                        if isinstance(step_data, dict):
                            if 'error' in step_data:
                                has_error = True
                            if 'warning' in step_data:
                                has_warning = True
                
                if has_error:
                    suite_summary['failed_tests'] += 1
                    print(f"❌ {test_case.name} - с ошибками")
                elif has_warning:
                    suite_summary['tests_with_warnings'] += 1
                    print(f"⚠️  {test_case.name} - с предупреждениями")
                else:
                    suite_summary['completed_tests'] += 1
                    print(f"✅ {test_case.name} - успешно")
                
                # Сохраняем сводку по тесту
                test_summary = {
                    'name': test_case.name,
                    'frame_size': test_case.frame_size,
                    'sources_count': test_case.sources_count,
                    'has_error': has_error,
                    'has_warning': has_warning,
                    'total_time_seconds': test_result.get('summary', {}).get('total_time', {}).get('total_time_seconds', 0)
                }
                
                suite_summary['test_results'].append(test_summary)
                
            except Exception as e:
                print(f"❌ {test_case.name} - критическая ошибка: {str(e)[:50]}...")
                suite_summary['failed_tests'] += 1
                
                # Логируем ошибку
                self.artifact_manager.log_message(
                    f"Критическая ошибка в тесте {test_case.name}: {str(e)}",
                    level="ERROR"
                )
        
        # Завершаем выполнение
        end_time = time.time()
        suite_summary['total_execution_time_seconds'] = end_time - start_time
        suite_summary['end_time'] = datetime.now().isoformat()
        
        # Сохраняем сводку
        summary_file = self.artifact_manager.session_path / 'suite_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(suite_summary, f, indent=2, ensure_ascii=False)
        
        # Выводим итоги
        print(f"\n{'='*60}")
        print(f"🏁 ВЫПОЛНЕНИЕ ЗАВЕРШЕНО")
        print(f"{'='*60}")
        print(f"Всего тестов: {suite_summary['total_tests']}")
        print(f"✅ Успешно: {suite_summary['completed_tests']}")
        print(f"⚠️  С предупреждениями: {suite_summary['tests_with_warnings']}")
        print(f"❌ С ошибками: {suite_summary['failed_tests']}")
        print(f"⏱️  Общее время: {suite_summary['total_execution_time_seconds']:.1f} секунд")
        print(f"\n📊 Артефакты сохранены в: {self.artifact_manager.session_path}")
        
        # Логируем завершение
        self.artifact_manager.log_message(
            f"Набор тестов завершен. "
            f"Успешно: {suite_summary['completed_tests']}/"
            f"{suite_summary['total_tests']}. "
            f"Время: {suite_summary['total_execution_time_seconds']:.1f}с"
        )
        
        return suite_summary
    
    def cleanup(self):
        """Очистка временных файлов."""
        self.artifact_manager.cleanup_temp_files()
        print(f"🧹 Временные файлы очищены")