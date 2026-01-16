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

# Добавляем корень проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.our_adapter import OurImplementationAdapter
from src.core.dempster_core import DempsterShafer


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
        print(f"Проверка: {example_file}")
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
            self._validate_discounting(data, expected, validation_result, tolerance)
        else:
            print(f"⚠ Неизвестный тип примера: {example_type}")
        
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
    
    def _validate_belief_plausibility(self, data, expected, result, tolerance):
        """Проверяет вычисление Belief и Plausibility"""
        print("\n1. Проверка Belief и Plausibility:")
        
        # Проверяем Belief
        if 'Belief' in expected:
            for event_str, expected_value in expected['Belief'].items():
                result['total_tests'] += 1
                
                # Вычисляем Belief
                computed = self.adapter.compute_belief(data, event_str)
                
                # Сравниваем
                if self._compare_values(computed, expected_value, tolerance):
                    print(f"  ✓ Belief({event_str}) = {computed:.4f} (ожидалось: {expected_value})")
                    result['passed_tests'] += 1
                else:
                    print(f"  ✗ Belief({event_str}) = {computed:.4f} (ожидалось: {expected_value})")
                    result['details'].append({
                        'test': f'Belief({event_str})',
                        'computed': computed,
                        'expected': expected_value,
                        'diff': abs(computed - expected_value)
                    })
        
        # Проверяем Plausibility
        if 'Plausibility' in expected:
            for event_str, expected_value in expected['Plausibility'].items():
                result['total_tests'] += 1
                
                # Вычисляем Plausibility
                computed = self.adapter.compute_plausibility(data, event_str)
                
                # Сравниваем
                if self._compare_values(computed, expected_value, tolerance):
                    print(f"  ✓ Plausibility({event_str}) = {computed:.4f} (ожидалось: {expected_value})")
                    result['passed_tests'] += 1
                else:
                    print(f"  ✗ Plausibility({event_str}) = {computed:.4f} (ожидалось: {expected_value})")
                    result['details'].append({
                        'test': f'Plausibility({event_str})',
                        'computed': computed,
                        'expected': expected_value,
                        'diff': abs(computed - expected_value)
                    })
    
    def _validate_dempster_combination(self, data, expected, result, tolerance):
        """Проверяет комбинирование по Демпстеру"""
        print("\n1. Проверка комбинирования Демпстера:")
        
        if 'combined_dempster' in expected:
            # Вычисляем комбинирование
            computed_result = self.adapter.combine_all_dempster(data)
            formatted_computed = self.adapter.format_result(computed_result)
            
            # Сравниваем с ожидаемым
            expected_result = expected['combined_dempster']
            
            # Проверяем каждое ожидаемое значение
            all_keys = set(formatted_computed.keys()) | set(expected_result.keys())
            
            for key in sorted(all_keys):
                computed_val = formatted_computed.get(key, 0.0)
                expected_val = expected_result.get(key, 0.0)
                
                result['total_tests'] += 1
                
                if self._compare_values(computed_val, expected_val, tolerance):
                    print(f"  ✓ m({key}) = {computed_val:.4f} (ожидалось: {expected_val})")
                    result['passed_tests'] += 1
                else:
                    print(f"  ✗ m({key}) = {computed_val:.4f} (ожидалось: {expected_val})")
                    result['details'].append({
                        'test': f'm({key})',
                        'computed': computed_val,
                        'expected': expected_val,
                        'diff': abs(computed_val - expected_val)
                    })
        
        # Также проверяем комбинирование Ягера если есть
        if 'combined_yager' in expected:
            self._validate_yager_combination(data, expected, result, tolerance)
    
    def _validate_yager_combination(self, data, expected, result, tolerance):
        """Проверяет комбинирование по Ягеру"""
        print("\n2. Проверка комбинирования Ягера:")
        
        if 'combined_yager' in expected:
            # Вычисляем комбинирование
            computed_result = self.adapter.combine_all_yager(data)
            formatted_computed = self.adapter.format_result(computed_result)
            
            # Сравниваем с ожидаемым
            expected_result = expected['combined_yager']
            
            # Проверяем каждое ожидаемое значение
            all_keys = set(formatted_computed.keys()) | set(expected_result.keys())
            
            for key in sorted(all_keys):
                computed_val = formatted_computed.get(key, 0.0)
                expected_val = expected_result.get(key, 0.0)
                
                result['total_tests'] += 1
                
                if self._compare_values(computed_val, expected_val, tolerance):
                    print(f"  ✓ m_Yag({key}) = {computed_val:.4f} (ожидалось: {expected_val})")
                    result['passed_tests'] += 1
                else:
                    print(f"  ✗ m_Yag({key}) = {computed_val:.4f} (ожидалось: {expected_val})")
                    result['details'].append({
                        'test': f'm_Yag({key})',
                        'computed': computed_val,
                        'expected': expected_val,
                        'diff': abs(computed_val - expected_val)
                    })
    
    def _validate_discounting(self, data, expected, result, tolerance):
        """Проверяет дисконтирование"""
        print("\n1. Проверка дисконтирования:")
        
        # Получаем коэффициенты дисконтирования
        discount_factors = []
        if 'bba_sources' in data.get('original_data', {}):
            for source in data['original_data']['bba_sources']:
                if 'reliability' in source:
                    alpha = 1 - source['reliability']  # reliability = 1 - alpha
                    discount_factors.append(alpha)
        
        # Если нет reliability, используем значения из книги
        if not discount_factors:
            discount_factors = [0.048, 0.952]  # из примера 2.7
        
        # Проверяем дисконтированные BPA
        discounted_bpas = []
        
        for i, alpha in enumerate(discount_factors):
            if i < len(data["bpas"]):
                discounted = self.adapter.discount_bpa(data, i, alpha)
                discounted_bpas.append(discounted)
                
                # Проверяем если есть ожидаемые значения
                if f'discounted_source{i+1}' in expected:
                    formatted_discounted = self.adapter.format_result(discounted)
                    expected_key = f'discounted_source{i+1}'
                    
                    self._compare_bba(
                        formatted_discounted, 
                        expected[expected_key], 
                        f"Дисконтированный источник {i+1}",
                        result, 
                        tolerance
                    )
        
        # Проверяем комбинированный результат после дисконтирования
        if 'combined_dempster' in expected and discounted_bpas:
            print("\n2. Проверка комбинирования после дисконтирования:")
            
            # Создаем новый объект DS с дисконтированными данными
            frame = data["frame"]
            ds_temp = DempsterShafer(frame)
            
            # Комбинируем дисконтированные BPA
            if len(discounted_bpas) == 1:
                combined_result = discounted_bpas[0]
            else:
                combined_result = discounted_bpas[0]
                for bpa in discounted_bpas[1:]:
                    combined_result = ds_temp.dempster_combine(combined_result, bpa)
            
            # Форматируем и сравниваем
            formatted_combined = self.adapter.format_result(combined_result)
            
            self._compare_bba(
                formatted_combined,
                expected['combined_dempster'],
                "Комбинированный результат",
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
                print(f"  ✓ {key}: {computed_val:.4f} (ожидалось: {expected_val})")
                result['passed_tests'] += 1
            else:
                print(f"  ✗ {key}: {computed_val:.4f} (ожидалось: {expected_val})")
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
                    print(f"     {detail['test']}: {detail['computed']:.4f} != {detail['expected']:.4f} (разница: {detail['diff']:.6f})")
                if len(result['details']) > 3:
                    print(f"     ... и еще {len(result['details']) - 3} ошибок")
        
        print(f"\nИтого: {total_passed}/{total_tests} тестов пройдено")
        
        if total_passed == total_tests:
            print("\n🎉 ВСЕ ПРИМЕРЫ ИЗ КНИГИ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            success_rate = (total_passed / total_tests) * 100
            print(f"\n⚠ Успешность: {success_rate:.1f}%")
            print("Требуется отладка реализации.")


def main():
    """Главная функция"""
    print("ПРОВЕРКА РЕАЛИЗАЦИИ НА ПРИМЕРАХ ИЗ КНИГИ")
    print("Сравниваем с результатами из главы 2")
    print("-" * 80)
    
    # Создаем директорию для примеров если ее нет
    examples_dir = "data/book_examples"
    os.makedirs(examples_dir, exist_ok=True)
    
    validator = BookExampleValidator()
    
    # Находим все примеры
    example_files = []
    for filename in os.listdir(examples_dir):
        if filename.endswith('.json'):
            example_files.append(os.path.join(examples_dir, filename))
    
    if not example_files:
        print(f"❌ В директории {examples_dir} нет файлов примеров")
        print("Сначала создайте файлы примеров из книги")
        return
    
    # Сортируем для удобства
    example_files.sort()
    
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


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)