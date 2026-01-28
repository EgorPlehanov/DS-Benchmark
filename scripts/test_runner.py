#!/usr/bin/env python3
"""
Тестирование универсального раннера на простых примерах.
"""

import os
import sys
import json
from pathlib import Path

# Добавляем путь для импорта
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from src.adapters.our_adapter import OurImplementationAdapter
from src.runners.universal_runner import UniversalBenchmarkRunner


def create_simple_test():
    """Создает простой тест для проверки раннера."""
    return {
        "metadata": {
            "format": "DASS",
            "version": "1.0",
            "description": "Простой тест для проверки раннера",
            "test_group": "runner_test",
            "test_id": "runner_test_simple"
        },
        "frame_of_discernment": ["A", "B", "C"],
        "bba_sources": [
            {
                "id": "source_1",
                "bba": {
                    "{A}": 0.3,
                    "{B}": 0.2,
                    "{A,B}": 0.5
                }
            },
            {
                "id": "source_2",
                "bba": {
                    "{A}": 0.4,
                    "{C}": 0.3,
                    "{A,C}": 0.3
                }
            }
        ]
    }


def test_single_test():
    """Тестирует один тест."""
    print("🧪 ТЕСТИРОВАНИЕ ОДНОГО ТЕСТА")
    print("=" * 50)
    
    # Создаем адаптер
    adapter = OurImplementationAdapter()
    
    # Создаем раннер
    runner = UniversalBenchmarkRunner(
        adapter, 
        results_dir="results/runner_test"
    )
    
    # Создаем тестовые данные
    test_data = create_simple_test()
    
    # Запускаем тест
    results = runner.run_test(
        test_data=test_data,
        test_name="simple_test",
        iterations=2,
        alphas=[0.1, 0.2]
    )
    
    print(f"\n✅ Тест завершен")
    print(f"📊 Результаты сохранены в: {runner.run_dir}")
    
    # Проверяем результаты
    metadata = results["metadata"]
    aggregated = results.get("aggregated", {})
    
    print(f"\n📈 Результаты:")
    print(f"  Адаптер: {metadata['adapter']}")
    print(f"  Фрейм: {metadata['frame_size']} элементов")
    print(f"  Источников: {metadata['sources_count']}")
    
    if "performance" in aggregated:
        perf = aggregated["performance"]
        print(f"\n  Производительность (среднее время, мс):")
        for step in ["step1", "step2", "step3", "step4"]:
            if step in perf:
                time_data = perf[step].get("time_ms", {})
                mean_time = time_data.get("mean", 0)
                print(f"    {step}: {mean_time:.2f} мс")
    
    return results


def test_test_suite():
    """Тестирует набор тестов."""
    print("\n🧪 ТЕСТИРОВАНИЕ НАБОРА ТЕСТОВ")
    print("=" * 50)
    
    # Создаем адаптер
    adapter = OurImplementationAdapter()
    
    # Создаем раннер
    runner = UniversalBenchmarkRunner(
        adapter,
        results_dir="results/runner_test"
    )
    
    # Создаем временную директорию с тестами
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Создаем несколько тестов
        test_cases = [
            ("tiny_test", ["A", "B"], 2),
            ("small_test", ["A", "B", "C"], 2),
            ("medium_test", ["A", "B", "C", "D"], 3),
        ]
        
        for test_name, elements, n_sources in test_cases:
            test_data = {
                "metadata": {
                    "format": "DASS",
                    "version": "1.0",
                    "description": f"Тест {test_name}",
                    "test_group": "runner_suite",
                    "test_id": test_name
                },
                "frame_of_discernment": elements,
                "bba_sources": []
            }
            
            # Создаем источники
            for i in range(n_sources):
                bba = {}
                # Простая BPA: все масса на первом элементе
                bba[f"{{{elements[0]}}}"] = 1.0
                test_data["bba_sources"].append({
                    "id": f"source_{i+1}",
                    "bba": bba
                })
            
            # Сохраняем тест
            test_file = os.path.join(temp_dir, f"{test_name}.json")
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2)
        
        print(f"📁 Создано тестов: {len(test_cases)}")
        
        # Запускаем набор тестов
        summary = runner.run_test_suite(
            test_dir=temp_dir,
            iterations=2,
            max_tests=2  # Ограничиваем для скорости
        )
        
        print(f"\n✅ Набор тестов завершен")
        print(f"📊 Результаты сохранены в: {runner.run_dir}")
        
        # Выводим краткую статистику
        if summary and "statistics" in summary:
            stats = summary["statistics"]
            print(f"\n📈 Статистика по всем тестам:")
            print(f"  Всего тестов: {summary['metadata']['total_tests']}")
            print(f"  Средний размер фрейма: {stats['frame_size']['mean']:.1f}")
            print(f"  Среднее число источников: {stats['sources_count']['mean']:.1f}")
    
    return runner


def main():
    """Основная функция тестирования."""
    print("🔬 ТЕСТИРОВАНИЕ UNIVERSAL_BENCHMARK_RUNNER")
    print("=" * 60)
    
    try:
        # Тест одного теста
        test_single_test()
        
        # Тест набора тестов
        test_test_suite()
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🎯 Раннер готов к использованию для бенчмаркинга!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()