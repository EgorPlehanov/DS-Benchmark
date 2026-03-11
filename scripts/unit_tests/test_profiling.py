#!/usr/bin/env python3
"""
scripts/unit_tests/test_profiling.py
Тестирование системы профилирования
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.profiling.composite_profiler import CompositeProfiler
from src.profiling.core.cpu_profiler import CPUProfiler
from src.profiling.core.memory_profiler import MemoryProfiler


# Тестовая функция для профилирования
def test_function():
    """Функция для тестирования профилирования"""
    # Имитируем нагрузку
    data = []
    for i in range(10000):
        data.append(i * i)
    
    # Имитируем работу с множествами (как в ДШ)
    set1 = set(range(1000))
    set2 = set(range(500, 1500))
    
    intersections = []
    for _ in range(100):
        intersection = set1 & set2
        intersections.append(intersection)
    
    return len(data), len(intersections)


def test_individual_profilers():
    """Тестирование отдельных профилировщиков"""
    print("🧪 ТЕСТИРОВАНИЕ ОТДЕЛЬНЫХ ПРОФИЛИРОВЩИКОВ")
    print("=" * 50)
    
    # Тест CPU профилировщика
    print("\n1. CPU Profiler:")
    cpu_profiler = CPUProfiler(name="test_cpu", enabled=True)
    
    with cpu_profiler:
        result = test_function()
    
    cpu_results = cpu_profiler.results
    if cpu_results:
        print(f"   Результат: {result}")
        print(f"   Длительность: {cpu_results.duration_seconds:.3f} сек")
        print(f"   Топ функций: {len(cpu_results.data.get('top_functions', []))}")
    else:
        print("   Нет результатов профилирования")
    
    # Тест Memory профилировщика
    print("\n2. Memory Profiler:")
    memory_profiler = MemoryProfiler(name="test_memory", enabled=True)
    
    with memory_profiler:
        result = test_function()
    
    memory_results = memory_profiler.results
    if memory_results:
        print(f"   Результат: {result}")
        print(f"   Длительность: {memory_results.duration_seconds:.3f} сек")
        peak_bytes = memory_results.data.get('peak_memory_bytes', 0)
        print(f"   Пиковая память: {peak_bytes / 1024:.1f} KB")
    else:
        print("   Нет результатов профилирования")


def test_composite_profiler():
    """Тестирование композитного профилировщика"""
    print("\n\n🧪 ТЕСТИРОВАНИЕ КОМПОЗИТНОГО ПРОФИЛИРОВЩИКА")
    print("=" * 50)
    
    # Создаем композитный профилировщик
    composite = CompositeProfiler()
    
    print(f"Включенные профилировщики: {composite.get_enabled_profilers()}")
    
    # Запускаем профилирование
    print("\nЗапуск профилирования...")
    result, profile_result = composite.profile(test_function)
    
    print(f"Результат функции: {result}")
    print(f"Общая длительность: {profile_result.total_duration:.3f} сек")
    print(f"Количество профилировщиков: {len(profile_result.results)}")
    
    # Показываем узкие места
    if profile_result.bottlenecks:
        print("\n⚠️  Обнаружены узкие места:")
        for bottleneck in profile_result.bottlenecks:
            print(f"   - {bottleneck['type']}: {bottleneck.get('location', 'N/A')}")
    
    # Показываем корреляции
    if profile_result.correlations:
        print("\n🔗 Обнаружены корреляции:")
        for correlation in profile_result.correlations:
            print(f"   - {correlation['type']}: {correlation.get('function', 'N/A')}")
    
    # Сохраняем результаты
    print("\n💾 Сохранение результатов...")
    
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("results/unit_tests/test_profiling")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Сохраняем структурированные данные
    output_data = {
        'timestamp': timestamp,
        'function_result': result,
        'profile_result': {
            'total_duration': profile_result.total_duration,
            'bottlenecks': profile_result.bottlenecks,
            'correlations': profile_result.correlations,
            'metadata': profile_result.metadata
        }
    }
    
    output_file = output_dir / f"profile_test_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Результаты сохранены в: {output_file}")
    
    # Очистка
    composite.cleanup()


def main():
    """Основная функция тестирования"""
    print("🔬 ТЕСТИРОВАНИЕ СИСТЕМЫ ПРОФИЛИРОВАНИЯ")
    print("=" * 60)
    
    try:
        # Тестируем отдельные профилировщики
        test_individual_profilers()
        
        # Тестируем композитный профилировщик
        test_composite_profiler()
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🎯 Система профилирования готова к использованию!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())