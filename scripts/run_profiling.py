#!/usr/bin/env python3
"""
Главный скрипт для запуска сбора артефактов профилирования.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Добавляем путь для импорта
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from src.adapters.our_adapter import OurImplementationAdapter
    from src.profiling.runners.simple_profiling_runner import SimpleProfilingRunner
    from scripts.generate_test_data import get_last_generation_path
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("   Убедитесь, что вы запускаете скрипт из корневой директории проекта")
    print(f"   Текущая директория: {os.getcwd()}")
    print(f"   Проект должен быть в: {project_root}")
    sys.exit(1)

def main():
    """Основная функция запуска."""
    parser = argparse.ArgumentParser(
        description='Сбор артефактов профилирования для реализации Демпстера-Шейфера',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python scripts/run_profiling.py --tests data/generated/last
  python scripts/run_profiling.py --tests data/generated/tests_20240130 --max-tests 5
  python scripts/run_profiling.py --tests last --iterations 2 --group tiny
        """
    )
    
    parser.add_argument('--tests', type=str, required=True,
                       help='Путь к тестам или "last" для последней генерации')
    
    parser.add_argument('--iterations', type=int, default=3,
                       help='Количество итераций на тест (по умолчанию: 3)')
    
    parser.add_argument('--max-tests', type=int, default=None,
                       help='Максимальное количество тестов (по умолчанию: все)')
    
    parser.add_argument('--min-size', type=int, default=None,
                       help='Минимальный размер фрейма для фильтрации')
    
    parser.add_argument('--max-size', type=int, default=None,
                       help='Максимальный размер фрейма для фильтрации')
    
    parser.add_argument('--group', type=str, default=None,
                       help='Группа тестов (tiny, small, medium, etc.)')
    
    parser.add_argument('--output-dir', type=str, default='artifacts',
                       help='Директория для сохранения артефактов')
    
    parser.add_argument('--session-id', type=str, default=None,
                       help='ID сессии (по умолчанию: генерируется)')
    
    parser.add_argument('--adapter', type=str, default='our',
                       choices=['our'],
                       help='Адаптер для тестирования (пока только our)')
    
    args = parser.parse_args()
    
    print("🔬 СИСТЕМА СБОРА АРТЕФАКТОВ ПРОФИЛИРОВАНИЯ")
    print("=" * 70)
    
    # Определяем директорию с тестами
    if args.tests.lower() == 'last':
        test_dir = get_last_generation_path()
        if not test_dir:
            print("❌ Не найдена последняя генерация тестов")
            print("   Запустите сначала: python scripts/generate_test_data.py")
            sys.exit(1)
    else:
        test_dir = Path(args.tests)
        if not test_dir.exists():
            print(f"❌ Директория с тестами не существует: {test_dir}")
            print(f"   Текущая директория: {os.getcwd()}")
            sys.exit(1)
    
    print(f"📁 Тесты: {test_dir}")
    print(f"📁 Абсолютный путь: {Path(test_dir).absolute()}")
    
    # Создаем адаптер
    if args.adapter == 'our':
        adapter = OurImplementationAdapter()
        print(f"📚 Адаптер: Наша реализация")
    else:
        print(f"❌ Неизвестный адаптер: {args.adapter}")
        sys.exit(1)
    
    # Фильтр по размеру
    filter_by_size = None
    if args.min_size is not None or args.max_size is not None:
        min_size = args.min_size if args.min_size is not None else 2
        max_size = args.max_size if args.max_size is not None else 100
        filter_by_size = (min_size, max_size)
        print(f"📏 Фильтр по размеру: {min_size}-{max_size} элементов")
    
    # Фильтр по группе
    filter_by_group = args.group
    if filter_by_group:
        print(f"📂 Фильтр по группе: {filter_by_group}")
    
    print(f"🔄 Итераций на тест: {args.iterations}")
    if args.max_tests:
        print(f"📊 Максимальное количество тестов: {args.max_tests}")
    
    output_dir = Path(args.output_dir)
    print(f"💾 Артефакты будут сохранены в: {output_dir.absolute()}/")
    print("-" * 70)
    
    # Проверяем права на запись
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        test_file = output_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        print("✅ Права на запись в выходную директорию: OK")
    except Exception as e:
        print(f"❌ Нет прав на запись в выходную директорию: {e}")
        print(f"   Попробуйте указать другую директорию с помощью --output-dir")
        sys.exit(1)
    
    # Создаем раннер
    try:
        runner = SimpleProfilingRunner(
            adapter=adapter,
            tests_dir=test_dir,
            output_dir=args.output_dir,
            session_id=args.session_id
        )
        
        # Запускаем набор тестов
        summary = runner.run_test_suite(
            iterations=args.iterations,
            max_tests=args.max_tests,
            filter_by_size=filter_by_size,
            filter_by_group=filter_by_group
        )
        
        # Очистка
        runner.cleanup()
        
        # Выводим путь к артефактам
        session_path = runner.artifact_manager.session_path
        print(f"\n📁 АРТЕФАКТЫ СОХРАНЕНЫ В:")
        print(f"   {session_path.absolute()}")
        
        # Показываем основные файлы
        print(f"\n📄 ОСНОВНЫЕ ФАЙЛЫ:")
        main_files = ['meta.json', 'config.json', 'suite_summary.json']
        for filename in main_files:
            filepath = session_path / filename
            if filepath.exists():
                size_kb = filepath.stat().st_size / 1024
                print(f"   {filename}: {size_kb:.1f} KB")
        
        print(f"\n✅ СБОР АРТЕФАКТОВ ЗАВЕРШЕН УСПЕШНО")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Выполнение прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()