#!/usr/bin/env python3
"""
Тестируем генераторы данных
"""

import sys
import os

# Добавляем src в путь Python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Теперь импортируем из src
from src.generators.dass_generator import DassGenerator
from src.generators.validator import DassValidator

def main():
    print("Тестируем генераторы DASS данных...")
    print(f"Текущая директория: {os.getcwd()}")
    
    # 1. Генерируем тестовый набор
    print("\n1. Генерируем тестовый набор...")
    test_suite = DassGenerator.generate_test_suite()
    
    for name, data in test_suite.items():
        print(f"\n  {name.upper()}:")
        print(f"    Фрейм: {len(data['frame_of_discernment'])} элементов")
        print(f"    Источники: {len(data['bba_sources'])}")
        
        # Валидируем
        is_valid, errors = DassValidator.validate_data(data)
        if is_valid:
            print("    ✓ Данные валидны")
        else:
            print(f"    ✗ Ошибки: {errors}")
    
    # 2. Сохраняем в файлы
    print("\n2. Сохраняем в файлы...")
    
    # Определяем правильный путь к data/generated
    project_root = os.path.dirname(os.path.dirname(__file__))
    data_dir = os.path.join(project_root, "data", 'test_generators')
    
    print(f"    Путь для сохранения: {data_dir}")
    os.makedirs(data_dir, exist_ok=True)
    
    for name, data in test_suite.items():
        filename = os.path.join(data_dir, f"test_{name}.json")
        if DassGenerator.save_to_file(data, filename):
            print(f"  ✓ Сохранен {filename}")
        else:
            print(f"  ✗ Ошибка сохранения {filename}")
    
    # 3. Загружаем и проверяем обратно
    print("\n3. Проверяем загрузку...")
    for name in test_suite.keys():
        filename = os.path.join(data_dir, f"test_{name}.json")
        loaded = DassGenerator.load_from_file(filename)
        
        if loaded:
            is_valid, errors = DassValidator.validate_data(loaded)
            if is_valid:
                print(f"  ✓ Файл {filename} загружен и валиден")
            else:
                print(f"  ✗ Файл {filename} содержит ошибки: {errors}")
        else:
            print(f"  ✗ Не удалось загрузить {filename}")
    
    print("\n✅ Готово!")

if __name__ == "__main__":
    main()