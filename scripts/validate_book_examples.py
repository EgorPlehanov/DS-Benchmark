# scripts/validate_book_examples.py
#!/usr/bin/env python3
"""
Скрипт для проверки нашей реализации на примерах из книги
Сравнивает результаты с ожидаемыми значениями из учебника
"""

import sys
import os
import json
import math
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.our_adapter import OurImplementationAdapter


class BookExampleValidator:
    """Валидатор примеров из книги"""
    
    def __init__(self):
        self.adapter = OurImplementationAdapter()
        self.results = []
    
    def validate_example(self, example_file: str, tolerance: float = 1e-3) -> dict:
        """
        Проверяет пример из книги
        
        Args:
            example_file: путь к файлу примера
            tolerance: допустимая погрешность
            
        Returns:
            Словарь с результатами валидации
        """
        print(f"\n{'='*60}")
        print(f"Проверка: {Path(example_file).name}")
        print(f"{'='*60}")
        
        # Загружаем пример
        with open(example_file, 'r', encoding='utf-8') as f:
            example_data = json.load(f)
        
        metadata = example_data.get('metadata', {})
        print(f"Описание: {metadata.get('description', 'N/A')}")
        print(f"Страница: {metadata.get('page', 'N/A')}")
        print(f"Тип: {metadata.get('type', 'N/A')}")
        
        # Загружаем данные через адаптер
        data = self.adapter.load_from_dass(example_data)
        expected = example_data.get('expected_results', {})
        
        validation_result = {
            'file': os.path.basename(example_file),
            'description': metadata.get('description', ''),
            'passed_tests': 0,
            'total_tests': 0,
            'details': []
        }
        
        # Проверяем разные типы примеров
        example_type = metadata.get('type', '')
        
        if example_type == 'belief_plausibility_calculation':
            self._validate_belief_plausibility(data, expected, validation_result, tolerance)
        elif example_type == 'dempster_combination':
            self._validate_dempster_combination(data, expected, validation_result, tolerance)
        elif example_type == 'yager_combination':
            self._validate_yager_combination(data, expected, validation_result, tolerance)
        elif example_type == 'discounting_dempster':
            self._validate_discounting(example_data, data, expected, validation_result, tolerance)
        else:
            print(f"⚠ Неизвестный тип примера: {example_type}")
            # Пробуем все типы проверок по очереди
            self._validate_all(data, expected, validation_result, tolerance)
        
        # Выводим итог
        passed = validation_result['passed_tests']
        total = validation_result['total_tests']
        print(f"\nИтог: {passed}/{total} тестов пройдено")
        
        if passed == total:
            print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        else:
            print("❌ Есть ошибки")
        
        self.results.append(validation_result)
        return validation_result
    
    def _validate_all(self, data, expected, result, tolerance):
        """Пробует все типы проверок по очереди"""
        if 'Belief' in expected or 'Plausibility' in expected:
            self._validate_belief_plausibility(data, expected, result, tolerance)
        
        if 'combined_dempster' in expected:
            self._validate_dempster_combination(data, expected, result, tolerance)
        
        if 'combined_yager' in expected:
            self._validate_yager_combination(data, expected, result, tolerance)
        
        if any(key.startswith('discounted_source') for key in expected.keys()):
            # Нужны оригинальные данные для дисконтирования
            pass
    
    def _validate_belief_plausibility(self, data, expected, result, tolerance):
        """Проверяет вычисление Belief и Plausibility"""
        print("\n1. Проверка Belief и Plausibility:")
        
        # Проверяем Belief
        if 'Belief' in expected:
            for event_str, expected_value in expected['Belief'].items():
                result['total_tests'] += 1
                
                try:
                    # Вычисляем Belief
                    computed = self.adapter.belief(data, event_str)
                    
                    # Сравниваем
                    if self._compare_values(computed, expected_value, tolerance):
                        print(f"  ✓ Belief({event_str}) = {computed:.4f} (ожидалось: {expected_value:.4f})")
                        result['passed_tests'] += 1
                    else:
                        print(f"  ✗ Belief({event_str}) = {computed:.4f} (ожидалось: {expected_value:.4f})")
                        result['details'].append({
                            'test': f'Belief({event_str})',
                            'computed': computed,
                            'expected': expected_value,
                            'diff': abs(computed - expected_value)
                        })
                except Exception as e:
                    print(f"  ✗ Ошибка при вычислении Belief({event_str}): {e}")
                    result['details'].append({
                        'test': f'Belief({event_str})',
                        'error': str(e)
                    })
        
        # Проверяем Plausibility
        if 'Plausibility' in expected:
            for event_str, expected_value in expected['Plausibility'].items():
                result['total_tests'] += 1
                
                try:
                    # Вычисляем Plausibility
                    computed = self.adapter.plausibility(data, event_str)
                    
                    # Сравниваем
                    if self._compare_values(computed, expected_value, tolerance):
                        print(f"  ✓ Plausibility({event_str}) = {computed:.4f} (ожидалось: {expected_value:.4f})")
                        result['passed_tests'] += 1
                    else:
                        print(f"  ✗ Plausibility({event_str}) = {computed:.4f} (ожидалось: {expected_value:.4f})")
                        result['details'].append({
                            'test': f'Plausibility({event_str})',
                            'computed': computed,
                            'expected': expected_value,
                            'diff': abs(computed - expected_value)
                        })
                except Exception as e:
                    print(f"  ✗ Ошибка при вычислении Plausibility({event_str}): {e}")
                    result['details'].append({
                        'test': f'Plausibility({event_str})',
                        'error': str(e)
                    })
    
    def _validate_dempster_combination(self, data, expected, result, tolerance):
        """Проверяет комбинирование по Демпстеру"""
        print("\n1. Проверка комбинирования Демпстера:")
        
        if 'combined_dempster' in expected:
            try:
                # Вычисляем комбинирование
                computed_result = self.adapter.dempster_combine_sources(data)
                
                # Сравниваем с ожидаемым
                expected_result = expected['combined_dempster']
                
                # Проверяем каждое ожидаемое значение
                all_keys = set(computed_result.keys()) | set(expected_result.keys())
                
                for key in sorted(all_keys):
                    computed_val = computed_result.get(key, 0.0)
                    expected_val = expected_result.get(key, 0.0)
                    
                    result['total_tests'] += 1
                    
                    if self._compare_values(computed_val, expected_val, tolerance):
                        print(f"  ✓ m({key}) = {computed_val:.4f} (ожидалось: {expected_val:.4f})")
                        result['passed_tests'] += 1
                    else:
                        print(f"  ✗ m({key}) = {computed_val:.4f} (ожидалось: {expected_val:.4f})")
                        result['details'].append({
                            'test': f'm({key})',
                            'computed': computed_val,
                            'expected': expected_val,
                            'diff': abs(computed_val - expected_val)
                        })
            except Exception as e:
                print(f"  ✗ Ошибка при комбинировании Демпстера: {e}")
                result['details'].append({
                    'test': 'dempster_combination',
                    'error': str(e)
                })
        
        # Также проверяем комбинирование Ягера если есть
        if 'combined_yager' in expected:
            self._validate_yager_combination(data, expected, result, tolerance)
    
    def _validate_yager_combination(self, data, expected, result, tolerance):
        """Проверяет комбинирование по Ягеру"""
        print("\n2. Проверка комбинирования Ягера:")
        
        if 'combined_yager' in expected:
            try:
                # Вычисляем комбинирование
                computed_result = self.adapter.yager_combine_sources(data)
                
                # Сравниваем с ожидаемым
                expected_result = expected['combined_yager']
                
                # Проверяем каждое ожидаемое значение
                all_keys = set(computed_result.keys()) | set(expected_result.keys())
                
                for key in sorted(all_keys):
                    computed_val = computed_result.get(key, 0.0)
                    expected_val = expected_result.get(key, 0.0)
                    
                    result['total_tests'] += 1
                    
                    if self._compare_values(computed_val, expected_val, tolerance):
                        print(f"  ✓ m_Yag({key}) = {computed_val:.4f} (ожидалось: {expected_val:.4f})")
                        result['passed_tests'] += 1
                    else:
                        print(f"  ✗ m_Yag({key}) = {computed_val:.4f} (ожидалось: {expected_val:.4f})")
                        result['details'].append({
                            'test': f'm_Yag({key})',
                            'computed': computed_val,
                            'expected': expected_val,
                            'diff': abs(computed_val - expected_val)
                        })
            except Exception as e:
                print(f"  ✗ Ошибка при комбинировании Ягера: {e}")
                result['details'].append({
                    'test': 'yager_combination',
                    'error': str(e)
                })
    
    def _validate_discounting(self, example_data, data, expected, result, tolerance):
        """Проверяет дисконтирование"""
        print("\n1. Проверка дисконтирования:")
        
        # Получаем коэффициенты дисконтирования из источников
        discount_factors = []
        for source in example_data.get('bba_sources', []):
            if 'reliability' in source:
                alpha = 1 - source['reliability']  # reliability = 1 - alpha
                discount_factors.append(alpha)
        
        # Если нет reliability, используем значения из discount_factors
        if not discount_factors and 'discount_factors' in example_data:
            discount_factors = example_data['discount_factors']
        
        # Если все еще нет, используем значения из книги
        if not discount_factors:
            discount_factors = [0.048, 0.952]  # из примера 2.7
        
        # Получаем BPA из данных
        bpas = data.get('bpas', [])
        
        # Проверяем дисконтированные BPA
        for i, alpha in enumerate(discount_factors):
            if i < len(bpas):
                # Конвертируем BPA в строковый формат для дисконтирования
                bpa_string = self.adapter._convert_bpa_to_string_format(bpas[i])
                
                # Применяем дисконтирование
                discounted = self.adapter.discount(bpa_string, alpha)
                
                # Проверяем если есть ожидаемые значения
                expected_key = f'discounted_source{i+1}'
                if expected_key in expected:
                    self._compare_bba(
                        discounted, 
                        expected[expected_key], 
                        f"Дисконтированный источник {i+1}",
                        result, 
                        tolerance
                    )
        
        # Проверяем комбинированный результат после дисконтирования
        if 'combined_dempster' in expected and len(bpas) >= 2:
            print("\n2. Проверка комбинирования после дисконтирования:")
            
            # Дисконтируем BPA
            discounted_bpas = []
            for i, (bpa, alpha) in enumerate(zip(bpas, discount_factors)):
                if i >= len(discount_factors):
                    break
                
                bpa_string = self.adapter._convert_bpa_to_string_format(bpa)
                discounted = self.adapter.discount(bpa_string, alpha)
                discounted_bpas.append(discounted)
            
            if len(discounted_bpas) >= 2:
                # Комбинируем дисконтированные BPA
                combined_result = self.adapter.dempster_combine(*discounted_bpas)
                
                self._compare_bba(
                    combined_result,
                    expected['combined_dempster'],
                    "Комбинированный результат после дисконтирования",
                    result,
                    tolerance
                )
    
    def _compare_bba(self, computed_bba, expected_bba, test_name, result, tolerance):
        """Сравнивает два BPA"""
        print(f"\n{test_name}:")
        
        all_keys = set(computed_bba.keys()) | set(expected_bba.keys())
        
        for key in sorted(all_keys):
            computed_val = computed_bba.get(key, 0.0)
            expected_val = expected_bba.get(key, 0.0)
            
            result['total_tests'] += 1
            
            if self._compare_values(computed_val, expected_val, tolerance):
                print(f"  ✓ {key}: {computed_val:.4f} (ожидалось: {expected_val:.4f})")
                result['passed_tests'] += 1
            else:
                print(f"  ✗ {key}: {computed_val:.4f} (ожидалось: {expected_val:.4f})")
                result['details'].append({
                    'test': f'{test_name}: {key}',
                    'computed': computed_val,
                    'expected': expected_val,
                    'diff': abs(computed_val - expected_val)
                })
    
    def _compare_values(self, computed, expected, tolerance):
        """Сравнивает два значения с заданной точностью"""
        if math.isnan(computed) or math.isnan(expected):
            return math.isnan(computed) and math.isnan(expected)
        
        return abs(computed - expected) <= tolerance
    
    def print_summary(self):
        """Выводит сводку по всем проверкам"""
        print(f"\n{'='*80}")
        print("СВОДКА ПО ВСЕМ ПРИМЕРАМ")
        print(f"{'='*80}")
        
        total_passed = sum(r['passed_tests'] for r in self.results)
        total_tests = sum(r['total_tests'] for r in self.results)
        
        for result in self.results:
            filename = result['file']
            passed = result['passed_tests']
            total = result['total_tests']
            status = "✅" if passed == total else "❌"
            
            print(f"{status} {filename:30} {passed:2}/{total:2} тестов")
            
            # Выводим детали ошибок если есть
            if result['details']:
                for detail in result['details'][:3]:  # Первые 3 ошибки
                    if 'computed' in detail:
                        print(f"     {detail['test']}: {detail['computed']:.4f} != {detail['expected']:.4f} (разница: {detail['diff']:.6f})")
                    else:
                        print(f"     {detail['test']}: ОШИБКА - {detail.get('error', 'Unknown')}")
                if len(result['details']) > 3:
                    print(f"     ... и еще {len(result['details']) - 3} ошибок")
        
        print(f"\nИтого: {total_passed}/{total_tests} тестов пройдено")
        
        if total_tests > 0 and total_passed == total_tests:
            print("\n🎉 ВСЕ ПРИМЕРЫ ИЗ КНИГИ ПРОЙДЕНЫ УСПЕШНО!")
        elif total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"\n⚠ Успешность: {success_rate:.1f}%")
            print("Требуется отладка реализации.")
        else:
            print("\n⚠ Нет тестов для проверки")


def main():
    """Главная функция"""
    print("ПРОВЕРКА РЕАЛИЗАЦИИ НА ПРИМЕРАХ ИЗ КНИГИ")
    print("Сравниваем с результатами из главы 2")
    print("-" * 80)
    
    # Создаем директорию для примеров если ее нет
    examples_dir = "data/book_examples"
    os.makedirs(examples_dir, exist_ok=True)
    
    # Создаем примерные файлы если их нет
    example_files_created = create_example_files_if_needed(examples_dir)
    if example_files_created:
        print(f"📄 Созданы {example_files_created} файлов примеров из книги")
    
    validator = BookExampleValidator()
    
    # Находим все примеры
    example_files = []
    for filename in os.listdir(examples_dir):
        if filename.endswith('.json'):
            example_files.append(os.path.join(examples_dir, filename))
    
    if not example_files:
        print(f"❌ В директории {examples_dir} нет файлов примеров")
        print("Создайте файлы в формате DASS с примерами из книги")
        return
    
    # Сортируем для удобства
    example_files.sort()
    
    print(f"Найдено {len(example_files)} файлов примеров:")
    for f in example_files:
        print(f"  - {Path(f).name}")
    
    # Проверяем каждый пример
    for example_file in example_files:
        validator.validate_example(example_file, tolerance=1e-3)
    
    # Выводим сводку
    validator.print_summary()
    
    # Сохраняем результаты в файл
    output_file = "results/book_validation_results.json"
    os.makedirs("results", exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'total_examples': len(example_files),
            'results': validator.results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Подробные результаты сохранены в {output_file}")


def create_example_files_if_needed(examples_dir):
    """Создает файлы примеров из книги если их нет"""
    examples = [
        {
            "filename": "example_2.1.json",
            "content": {
                "metadata": {
                    "description": "Пример 2.1 из книги: 4 кандидата, 10 экспертов",
                    "page": "40",
                    "type": "belief_plausibility_calculation"
                },
                "frame_of_discernment": ["1", "2", "3", "4"],
                "bba_sources": [
                    {
                        "id": "experts",
                        "bba": {
                            "{}": 0.0,
                            "{1}": 0.5,
                            "{1,2}": 0.2,
                            "{3}": 0.3
                        }
                    }
                ],
                "expected_results": {
                    "Belief": {
                        "{1}": 0.5,
                        "{2}": 0.0,
                        "{3}": 0.3,
                        "{4}": 0.0
                    },
                    "Plausibility": {
                        "{1}": 0.7,
                        "{2}": 0.2,
                        "{3}": 0.3,
                        "{4}": 0.0
                    }
                }
            }
        },
        {
            "filename": "example_2.6.json",
            "content": {
                "metadata": {
                    "description": "Пример 2.6 из книги: комбинирование Демпстера",
                    "page": "53-54",
                    "type": "dempster_combination"
                },
                "frame_of_discernment": ["1", "2", "3", "4"],
                "bba_sources": [
                    {
                        "id": "source1",
                        "bba": {
                            "{}": 0.0,
                            "{1}": 0.625,
                            "{2,3}": 0.375
                        }
                    },
                    {
                        "id": "source2",
                        "bba": {
                            "{}": 0.0,
                            "{1,2}": 0.5,
                            "{3}": 0.4375,
                            "{4}": 0.0625
                        }
                    }
                ],
                "expected_results": {
                    "combined_dempster": {
                        "{}": 0.0,
                        "{1}": 0.4706,
                        "{2}": 0.2824,
                        "{3}": 0.2470
                    },
                    "combined_yager": {
                        "{}": 0.0,
                        "{1}": 0.3125,
                        "{2}": 0.1875,
                        "{3}": 0.1641,
                        "{1,2,3,4}": 0.336
                    }
                }
            }
        },
        {
            "filename": "example_2.7.json",
            "content": {
                "metadata": {
                    "description": "Пример 2.7 из книги: дисконтирование",
                    "page": "56-57",
                    "type": "discounting_dempster"
                },
                "frame_of_discernment": ["1", "2", "3", "4"],
                "bba_sources": [
                    {
                        "id": "source1",
                        "reliability": 0.952,
                        "bba": {
                            "{}": 0.0,
                            "{2}": 0.625,
                            "{2,3}": 0.375
                        }
                    },
                    {
                        "id": "source2", 
                        "reliability": 0.048,
                        "bba": {
                            "{}": 0.0,
                            "{1}": 1.0
                        }
                    }
                ],
                "discount_factors": [0.048, 0.952],
                "expected_results": {
                    "discounted_source1": {
                        "{2}": 0.595,
                        "{2,3}": 0.357,
                        "{1,2,3,4}": 0.048
                    },
                    "discounted_source2": {
                        "{1}": 0.048,
                        "{1,2,3,4}": 0.952
                    },
                    "combined_dempster": {
                        "{1}": 0.002,
                        "{2}": 0.594,
                        "{2,3}": 0.356,
                        "{1,2,3,4}": 0.048
                    }
                }
            }
        },
        {
            "filename": "example_2.8.json",
            "content": {
                "metadata": {
                    "description": "Пример 2.8 из книги: комбинирование Ягера",
                    "page": "59-60",
                    "type": "yager_combination"
                },
                "frame_of_discernment": ["1", "2", "3", "4"],
                "bba_sources": [
                    {
                        "id": "source1",
                        "bba": {
                            "{}": 0.0,
                            "{1}": 0.625,
                            "{2,3}": 0.375
                        }
                    },
                    {
                        "id": "source2",
                        "bba": {
                            "{}": 0.0,
                            "{1,2}": 0.5,
                            "{3}": 0.4375,
                            "{4}": 0.0625
                        }
                    }
                ],
                "expected_results": {
                    "combined_yager": {
                        "{}": 0.0,
                        "{1}": 0.3125,
                        "{2}": 0.1875,
                        "{3}": 0.1641,
                        "{1,2,3,4}": 0.336
                    }
                }
            }
        }
    ]
    
    created_count = 0
    for example in examples:
        filepath = os.path.join(examples_dir, example["filename"])
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(example["content"], f, indent=2, ensure_ascii=False)
            created_count += 1
    
    return created_count


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)