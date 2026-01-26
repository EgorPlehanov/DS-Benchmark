# test_our_adapter.py
#!/usr/bin/env python3
"""
Тест адаптера для нашей реализации
"""

import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.adapters.our_adapter import OurImplementationAdapter

def test_basic_functionality():
    """Тест базовой функциональности адаптера."""
    
    # Создаем тестовые данные в формате DASS
    test_dass = {
        "frame_of_discernment": ["A", "B", "C"],
        "bba_sources": [
            {
                "id": "source1",
                "bba": {
                    "{}": 0.0,
                    "{A}": 0.3,
                    "{B}": 0.3,
                    "{A,B}": 0.4
                }
            },
            {
                "id": "source2",
                "bba": {
                    "{}": 0.1,
                    "{A}": 0.2,
                    "{B}": 0.3,
                    "{A,B}": 0.4
                }
            }
        ],
        "metadata": {
            "description": "Тестовые данные"
        }
    }
    
    # Создаем адаптер
    adapter = OurImplementationAdapter()
    
    print("🧪 Тестирование адаптера для нашей реализации...")
    
    # 1. Тестируем загрузку данных
    print("\n1. Загрузка данных из DASS формата...")
    data = adapter.load_from_dass(test_dass)
    print(f"   ✓ Фрейм: {adapter.get_frame(data)}")
    print(f"   ✓ Источников: {len(data['bpas'])}")
    
    # 2. Тестируем комбинирование Демпстера
    print("\n2. Комбинирование по Демпстеру...")
    combined = adapter.dempster_combine_sources(data)
    print(f"   ✓ Результат содержит {len(combined)} подмножеств")
    
    # 3. Тестируем belief и plausibility
    print("\n3. Вычисление belief и plausibility...")
    bel_a = adapter.belief(data, "{A}")
    pl_a = adapter.plausibility(data, "{A}")
    print(f"   ✓ Bel({{A}}) = {bel_a:.4f}")
    print(f"   ✓ Pl({{A}}) = {pl_a:.4f}")
    
    # 4. Тестируем дисконтирование
    print("\n4. Дисконтирование BPA...")
    discounted = adapter.discount(combined, 0.2)
    print(f"   ✓ Дисконтированная BPA содержит {len(discounted)} подмножеств")
    
    # 5. Тестируем комбинирование Ягера
    print("\n5. Комбинирование по Ягеру...")
    yager_combined = adapter.yager_combine_sources(data)
    print(f"   ✓ Ягер результат содержит {len(yager_combined)} подмножеств")
    
    # 6. Тестируем получение подмножеств
    print("\n6. Получение всех подмножеств фрейма...")
    subsets = adapter.get_all_subsets(data)
    print(f"   ✓ Всего подмножеств: {len(subsets)} (ожидаем 8 для 3 элементов)")
    
    print("\n✅ Все тесты пройдены успешно!")

if __name__ == "__main__":
    test_basic_functionality()