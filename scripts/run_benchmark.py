#!/usr/bin/env python3
"""
Точка входа для запуска бенчмарков теории Демпстера-Шейфера.
Поддерживает тестирование разных библиотек и адаптеров.
"""

import os
import sys
import argparse
import json
from typing import List, Optional
from pathlib import Path

# Добавляем путь для импорта
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from src.adapters.our_adapter import OurImplementationAdapter
from src.runners.universal_runner import UniversalBenchmarkRunner


def get_last_generation_path() -> Optional[str]:
    """Получает путь к последней генерации тестов."""
    last_gen_file = project_root / "data" / "generated" / "last_generation.txt"
    
    if last_gen_file.exists():
        with open(last_gen_file, 'r', encoding='utf-8') as f:
            folder_name = f.read().strip()
        
        return str(project_root / "data" / "generated" / folder_name)
    
    return None


def load_adapter(adapter_name: str):
    """Загружает адаптер по имени."""
    adapters = {
        "our": OurImplementationAdapter,
        # "pyds": PydsAdapter,  # Будет добавлен позже
        # "ds": DsAdapter,      # Будет добавлен позже
    }
    
    if adapter_name not in adapters:
        available = ", ".join(adapters.keys())
        raise ValueError(f"Адаптер '{adapter_name}' не найден. Доступные: {available}")
    
    return adapters[adapter_name]()


def run_benchmark(adapter_name: str, 
                 test_path: str,
                 iterations: int = 3,
                 max_tests: Optional[int] = None,
                 output_dir: str = "results/benchmark"):
    """
    Запускает бенчмарк для указанного адаптера.
    
    Args:
        adapter_name: Имя адаптера ('our', 'pyds', и т.д.)
        test_path: Путь к тестам ('last' или путь к папке)
        iterations: Количество итераций каждого теста
        max_tests: Максимальное количество тестов
        output_dir: Директория для результатов
    """
    print("🔬 ЗАПУСК БЕНЧМАРКА ТЕОРИИ ДЕМПСТЕРА-ШЕЙФЕРА")
    print("=" * 60)
    
    # Загружаем адаптер
    print(f"📚 Загрузка адаптера: {adapter_name}")
    adapter = load_adapter(adapter_name)
    
    # Определяем путь к тестам
    if test_path == "last":
        test_dir = get_last_generation_path()
        if not test_dir:
            print("❌ Не найдена последняя генерация тестов")
            print("   Сначала запустите: python scripts/generate_test_data.py")
            return
        print(f"📁 Используем последнюю генерацию тестов")
    else:
        test_dir = test_path
        if not os.path.exists(test_dir):
            print(f"❌ Директория тестов не найдена: {test_dir}")
            return
    
    print(f"📁 Тесты: {test_dir}")
    print(f"🔄 Итераций: {iterations}")
    if max_tests:
        print(f"📊 Максимально тестов: {max_tests}")
    
    # Создаем раннер
    runner = UniversalBenchmarkRunner(adapter, results_dir=output_dir)
    
    # Запускаем тесты
    print("\n🚀 Запуск тестов...")
    runner.run_test_suite(
        test_dir=test_dir,
        iterations=iterations,
        max_tests=max_tests
    )
    
    print(f"\n✅ БЕНЧМАРК ЗАВЕРШЕН")
    print(f"📊 Результаты сохранены в: {runner.run_dir}")


def main():
    """Основная функция."""
    parser = argparse.ArgumentParser(
        description="Бенчмарк реализаций теории Демпстера-Шейфера",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Тестировать нашу реализацию на последних тестах
  python scripts/run_benchmark.py --library our --tests last
  
  # Тестировать с 5 итерациями
  python scripts/run_benchmark.py --library our --tests last --iterations 5
  
  # Тестировать только 10 тестов
  python scripts/run_benchmark.py --library our --tests last --max-tests 10
  
  # Тестировать конкретную директорию
  python scripts/run_benchmark.py --library our --tests data/generated/tests_20240115_123456
        """
    )
    
    parser.add_argument(
        "--library", "-l",
        type=str,
        default="our",
        choices=["our"],  # Позже добавим другие
        help="Библиотека для тестирования (our, pyds, ds)"
    )
    
    parser.add_argument(
        "--tests", "-t",
        type=str,
        default="last",
        help="Путь к тестам или 'last' для последней генерации"
    )
    
    parser.add_argument(
        "--iterations", "-i",
        type=int,
        default=3,
        help="Количество итераций каждого теста"
    )
    
    parser.add_argument(
        "--max-tests", "-m",
        type=int,
        default=None,
        help="Максимальное количество тестов для запуска"
    )
    
    parser.add_argument(
        "--output-dir", "-o",
        type=str,
        default="results/benchmark",
        help="Директория для сохранения результатов"
    )
    
    args = parser.parse_args()
    
    try:
        run_benchmark(
            adapter_name=args.library,
            test_path=args.tests,
            iterations=args.iterations,
            max_tests=args.max_tests,
            output_dir=args.output_dir
        )
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()