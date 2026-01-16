#!/usr/bin/env python3
"""
Генератор тестовых данных для бенчмарков Демпстера-Шейфера
Создает по 10 вариантов для каждого размера
"""

import os
import json
import random
from typing import List, Dict, Any
from datetime import datetime
import sys

# Добавляем путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.generators.dass_generator import DassGenerator
from src.generators.validator import DassValidator


def generate_small_tests() -> List[Dict[str, Any]]:
    """Генерирует 10 маленьких тестов (3-4 элемента, 2-3 источника)"""
    tests = []
    
    # Базовые элементы для маленьких тестов
    base_elements = ["A", "B", "C", "D"]
    
    for i in range(1, 11):  # 10 тестов
        # Вариация размера фрейма: 3 или 4 элемента
        n_elements = random.choice([3, 4])
        elements = base_elements[:n_elements]
        
        # Вариация количества источников: 2 или 3
        n_sources = random.choice([2, 3])
        
        # Генерируем тест
        test_data = DassGenerator.generate_simple(
            elements=elements,
            n_sources=n_sources,
            density=0.2,  # низкая плотность
            include_empty=random.choice([True, False])
        )
        
        # Обновляем метаданные
        test_data["metadata"]["description"] = (
            f"Маленький тест #{i}: {n_elements} элементов, {n_sources} источников"
        )
        test_data["metadata"]["test_group"] = "small"
        test_data["metadata"]["test_id"] = f"small_{i:02d}"
        
        tests.append(test_data)
    
    return tests


def generate_medium_tests() -> List[Dict[str, Any]]:
    """Генерирует 10 средних тестов (5-6 элементов, 3-4 источника)"""
    tests = []
    
    # Базовые элементы для средних тестов
    base_elements = ["A", "B", "C", "D", "E", "F"]
    
    for i in range(1, 11):  # 10 тестов
        # Вариация размера фрейма: 5 или 6 элементов
        n_elements = random.choice([5, 6])
        elements = base_elements[:n_elements]
        
        # Вариация количества источников: 3 или 4
        n_sources = random.choice([3, 4])
        
        # Генерируем тест
        test_data = DassGenerator.generate_simple(
            elements=elements,
            n_sources=n_sources,
            density=0.15,  # средняя плотность
            include_empty=random.choice([True, False])
        )
        
        # Обновляем метаданные
        test_data["metadata"]["description"] = (
            f"Средний тест #{i}: {n_elements} элементов, {n_sources} источников"
        )
        test_data["metadata"]["test_group"] = "medium"
        test_data["metadata"]["test_id"] = f"medium_{i:02d}"
        
        tests.append(test_data)
    
    return tests


def generate_large_tests() -> List[Dict[str, Any]]:
    """Генерирует 10 больших тестов (7-8 элементов, 4-5 источников)"""
    tests = []
    
    # Базовые элементы для больших тестов
    base_elements = ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    for i in range(1, 11):  # 10 тестов
        # Вариация размера фрейма: 7 или 8 элементов
        n_elements = random.choice([7, 8])
        elements = base_elements[:n_elements]
        
        # Вариация количества источников: 4 или 5
        n_sources = random.choice([4, 5])
        
        # Генерируем тест
        test_data = DassGenerator.generate_simple(
            elements=elements,
            n_sources=n_sources,
            density=0.1,  # низкая плотность (иначе слишком много комбинаций)
            include_empty=random.choice([True, False])
        )
        
        # Обновляем метаданные
        test_data["metadata"]["description"] = (
            f"Большой тест #{i}: {n_elements} элементов, {n_sources} источников"
        )
        test_data["metadata"]["test_group"] = "large"
        test_data["metadata"]["test_id"] = f"large_{i:02d}"
        
        tests.append(test_data)
    
    return tests


def validate_and_save_tests(tests: List[Dict[str, Any]], output_dir: str):
    """Валидирует и сохраняет тесты в файлы"""
    os.makedirs(output_dir, exist_ok=True)
    
    saved_count = 0
    for test_data in tests:
        test_id = test_data["metadata"]["test_id"]
        
        # Валидируем
        is_valid, errors = DassValidator.validate_data(test_data)
        if not is_valid:
            print(f"  ⚠️  Тест {test_id} невалиден: {errors[:1]}...")
            continue
        
        # Сохраняем
        filename = os.path.join(output_dir, f"{test_id}.json")
        if DassGenerator.save_to_file(test_data, filename):
            saved_count += 1
            print(f"  ✓ Сохранен: {test_id}.json")
    
    return saved_count


def generate_all_tests():
    """Генерирует все тестовые данные"""
    print("🚀 Генерация тестовых данных для бенчмарков")
    print("=" * 50)
    
    # Путь для сохранения
    output_dir = "data/generated/tests"
    
    # Генерируем все группы тестов
    print("\n📊 1. Генерация маленьких тестов (3-4 элемента, 2-3 источника)...")
    small_tests = generate_small_tests()
    
    print("\n📊 2. Генерация средних тестов (5-6 элементов, 3-4 источника)...")
    medium_tests = generate_medium_tests()
    
    print("\n📊 3. Генерация больших тестов (7-8 элементов, 4-5 источников)...")
    large_tests = generate_large_tests()
    
    # Сохраняем
    print("\n💾 Сохранение файлов...")
    
    total_saved = 0
    total_saved += validate_and_save_tests(small_tests, output_dir)
    total_saved += validate_and_save_tests(medium_tests, output_dir)
    total_saved += validate_and_save_tests(large_tests, output_dir)
    
    # Создаем индексный файл
    create_index_file(output_dir, small_tests + medium_tests + large_tests)
    
    print(f"\n✅ Готово! Создано {total_saved} тестовых файлов в {output_dir}/")
    print("\n📁 Структура файлов:")
    print(f"  {output_dir}/small_01.json ... small_10.json  (10 файлов)")
    print(f"  {output_dir}/medium_01.json ... medium_10.json (10 файлов)")
    print(f"  {output_dir}/large_01.json ... large_10.json  (10 файлов)")
    print(f"  {output_dir}/index.json     (индекс всех тестов)")


def create_index_file(output_dir: str, all_tests: List[Dict[str, Any]]):
    """Создает индексный файл со всеми тестами"""
    index = {
        "metadata": {
            "format": "DASS-INDEX",
            "version": "1.0",
            "description": "Индекс всех тестовых файлов",
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(all_tests)
        },
        "tests": []
    }
    
    for test in all_tests:
        test_info = {
            "test_id": test["metadata"]["test_id"],
            "group": test["metadata"]["test_group"],
            "description": test["metadata"]["description"],
            "n_elements": len(test["frame_of_discernment"]),
            "n_sources": len(test["bba_sources"]),
            "filename": f"{test['metadata']['test_id']}.json"
        }
        index["tests"].append(test_info)
    
    # Сохраняем индекс
    index_file = os.path.join(output_dir, "index.json")
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ Создан индекс: index.json")


if __name__ == "__main__":
    # Проверяем текущую директорию
    print(f"Текущая директория: {os.getcwd()}")
    
    # Генерируем тесты
    generate_all_tests()