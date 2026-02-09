#!/usr/bin/env python3
"""
scripts/profile_benchmark.py
Запуск бенчмарков с различными уровнями профилирования
"""

import os
import sys
import argparse
from pathlib import Path

# Добавляем путь для импорта
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent
sys.path.insert(0, str(project_root))

from src.runners.profiling_runner import ProfilingBenchmarkRunner
from src.adapters.our_adapter import OurImplementationAdapter


def get_test_dir(tests_arg: str) -> str:
    """Получает путь к тестовым данным"""
    if tests_arg == "last":
        # Ищем последнюю генерацию
        last_gen_file = "data/generated/last_generation.txt"
        if os.path.exists(last_gen_file):
            with open(last_gen_file, 'r', encoding='utf-8') as f:
                folder_name = f.read().strip()
            return os.path.join("data/generated", folder_name)
        else:
            # Ищем любую существующую генерацию
            generated_dir = Path("data/generated")
            if generated_dir.exists():
                # Берем последнюю папку
                dirs = sorted([d for d in generated_dir.iterdir() if d.is_dir()])
                if dirs:
                    return str(dirs[-1])
    
    # Если указан конкретный путь
    if os.path.exists(tests_arg):
        return tests_arg
    
    # Пробуем как относительный путь
    possible_path = os.path.join("data/generated", tests_arg)
    if os.path.exists(possible_path):
        return possible_path
    
    raise FileNotFoundError(f"Не удалось найти тесты: {tests_arg}")


def main():
    parser = argparse.ArgumentParser(
        description='Запуск бенчмарков с профилированием Демпстера-Шейфера'
    )
    
    parser.add_argument('--library', 
                       default='our',
                       choices=['our'],  # Позже добавим другие библиотеки
                       help='Библиотека для тестирования')
    
    parser.add_argument('--tests',
                       default='last',
                       help='Путь к тестам или "last" для последней генерации')
    
    parser.add_argument('--profiling',
                       default='medium',
                       choices=['off', 'light', 'medium', 'full'],
                       help='Уровень профилирования')
    
    parser.add_argument('--iterations',
                       type=int,
                       default=3,
                       help='Количество итераций каждого теста')
    
    parser.add_argument('--output-dir',
                       default='results/profiling',
                       help='Директория для результатов')
    
    parser.add_argument('--max-tests',
                       type=int,
                       default=None,
                       help='Максимальное количество тестов для запуска')

    parser.add_argument('--scalene',
                       action='store_true',
                       default=False,
                       help='Включить scalene профилирование (если доступно)')

    parser.add_argument('--scalene-include',
                       nargs='*',
                       default=['src'],
                       help=('Список директорий для фильтрации Scalene (по умолчанию: src). '
                             'Если указать параметр без значений, фильтры отключаются.'))
    
    parser.add_argument('--save-raw',
                       action='store_true',
                       default=True,
                       help='Сохранять сырые данные профилирования')
    
    parser.add_argument('--no-save-raw',
                       dest='save_raw',
                       action='store_false',
                       help='Не сохранять сырые данные профилирования')
    
    args = parser.parse_args()
    
    print("🔬 ЗАПУСК БЕНЧМАРКА С ПРОФИЛИРОВАНИЕМ")
    print("=" * 60)
    print(f"Библиотека: {args.library}")
    print(f"Профилирование: {args.profiling}")
    print(f"Итераций: {args.iterations}")
    print(f"Сырые данные: {'сохраняются' if args.save_raw else 'не сохраняются'}")
    
    try:
        # Получаем путь к тестам
        test_dir = get_test_dir(args.tests)
        print(f"Тесты: {test_dir}")
        
        # Создаем адаптер
        if args.library == 'our':
            adapter = OurImplementationAdapter()
        else:
            raise ValueError(f"Библиотека {args.library} не поддерживается")
        
        # Создаем раннер с профилированием
        runner = ProfilingBenchmarkRunner(
            adapter=adapter,
            results_dir=args.output_dir,
            profiling_level=args.profiling,
            save_raw_profiles=args.save_raw,
            enable_scalene=args.scalene,
            scalene_include_paths=args.scalene_include
        )
        
        # Запускаем тесты
        print(f"\n🚀 Запуск тестов из: {test_dir}")
        summary = runner.run_test_suite(
            test_dir=test_dir,
            iterations=args.iterations,
            max_tests=args.max_tests
        )
        
        # Выводим информацию о профилировании
        if args.profiling != 'off':
            profiling_dir = runner.profiling_dir
            print(f"\n📊 ДАННЫЕ ПРОФИЛИРОВАНИЯ:")
            print(f"   Отчеты: {profiling_dir}/reports/")
            print(f"   Сырые данные: {profiling_dir}/raw/")
            
            # Подсчитываем количество файлов
            report_files = list(Path(profiling_dir).glob("reports/*.json"))
            raw_files = list(Path(profiling_dir).glob("raw/*.json"))
            
            print(f"   Сохранено отчетов: {len(report_files)}")
            print(f"   Сохранено сырых файлов: {len(raw_files)}")
        
        print(f"\n✅ ВЫПОЛНЕНИЕ ЗАВЕРШЕНО")
        print(f"📁 Результаты: {runner.run_dir}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
