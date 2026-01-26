# scripts/run_benchmark.py
#!/usr/bin/env python3
"""
Скрипт запуска бенчмарков для разных библиотек.
Поддерживает последнюю генерацию тестов по умолчанию.
"""

import os
import sys
import glob
import argparse
from pathlib import Path
from typing import List, Optional

# Добавляем пути
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Импортируем адаптеры
from src.adapters.our_adapter import OurImplementationAdapter
# from src.adapters.pyds_adapter import PydsAdapter  # будет позже
# from src.adapters.dempster_shafer_adapter import DempsterShaferAdapter  # будет позже

# Импортируем раннер
from src.runners.universal_runner import UniversalBenchmarkRunner


def get_last_generation_path() -> Optional[str]:
    """
    Получает путь к последней генерации тестов.
    
    Returns:
        Путь к директории с тестами или None если нет последней генерации
    """
    last_gen_file = "data/generated/last_generation.txt"
    
    if os.path.exists(last_gen_file):
        try:
            with open(last_gen_file, 'r', encoding='utf-8') as f:
                folder_name = f.read().strip()
            
            if folder_name:
                full_path = os.path.join("data/generated", folder_name)
                if os.path.exists(full_path):
                    return full_path
                else:
                    print(f"⚠️  Директория последней генерации не найдена: {full_path}")
        except Exception as e:
            print(f"⚠️  Ошибка чтения файла last_generation.txt: {e}")
    
    return None


def get_adapter(library_name: str):
    """Возвращает адаптер для указанной библиотеки."""
    if library_name == "our":
        return OurImplementationAdapter()
    elif library_name == "pyds":
        # return PydsAdapter()
        raise NotImplementedError(f"Адаптер для {library_name} еще не реализован")
    elif library_name == "dempster_shafer":
        # return DempsterShaferAdapter()
        raise NotImplementedError(f"Адаптер для {library_name} еще не реализован")
    else:
        raise ValueError(f"Неизвестная библиотека: {library_name}")


def find_all_test_files(base_dir: str) -> List[str]:
    """
    Находит все тестовые файлы в указанной директории и поддиректориях.
    
    Args:
        base_dir: Базовая директория для поиска
        
    Returns:
        Список путей к тестовым файлам
    """
    test_files = []
    
    # Проверяем существование директории
    if not os.path.exists(base_dir):
        print(f"⚠️  Директория не найдена: {base_dir}")
        return []
    
    # Рекурсивно ищем все JSON файлы
    for root, dirs, files in os.walk(base_dir):
        # Пропускаем некоторые служебные директории
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith('.json'):
                # Игнорируем специальные файлы
                if any(exclude in file.lower() for exclude in ['index', 'statistics', 'error', 'config']):
                    continue
                
                filepath = os.path.join(root, file)
                test_files.append(filepath)
    
    return test_files


def get_test_files_by_pattern(pattern: str, limit: int = 0) -> List[str]:
    """
    Возвращает тестовые файлы по шаблону или ключевому слову.
    
    Поддерживает:
    - "last" или "latest" - последняя генерация
    - "all" - все тесты из всех генераций
    - "tiny", "small", "medium", "large", "xlarge", "stress" - группы тестов
    - Конкретный путь или шаблон
    
    Args:
        pattern: Паттерн для поиска тестов
        limit: Ограничить количество тестов (0 = все)
        
    Returns:
        Список путей к тестовым файлам
    """
    # Специальные ключевые слова
    if pattern.lower() in ["last", "latest"]:
        # Последняя генерация
        base_dir = get_last_generation_path()
        if base_dir:
            print(f"📁 Используется последняя генерация: {os.path.basename(base_dir)}")
            files = find_all_test_files(base_dir)
        else:
            print("⚠️  Последняя генерация не найдена. Пытаемся найти любые тесты...")
            # Ищем любые тесты в data/generated
            files = find_all_test_files("data/generated")
    
    elif pattern.lower() == "all":
        # Все тесты из всех генераций
        files = find_all_test_files("data/generated")
    
    elif pattern.lower() in ["tiny", "small", "medium", "large", "xlarge", "stress", "special"]:
        # Группа тестов из последней генерации
        base_dir = get_last_generation_path()
        if base_dir:
            # Ищем тесты в конкретной группе
            group_dir = os.path.join(base_dir, pattern.lower())
            if os.path.exists(group_dir):
                files = glob.glob(os.path.join(group_dir, "*.json"))
                # Исключаем специальные файлы
                files = [f for f in files if "statistics" not in f.lower()]
            else:
                print(f"⚠️  Группа '{pattern}' не найдена в последней генерации")
                # Ищем во всех группах
                files = find_all_test_files(base_dir)
                # Фильтруем по имени файла
                files = [f for f in files if f"_{pattern.lower()}_" in f.lower()]
        else:
            # Ищем во всех директориях
            files = []
            search_pattern = os.path.join("data/generated", "*", f"{pattern.lower()}", "*.json")
            files = glob.glob(search_pattern)
            # Исключаем специальные файлы
            files = [f for f in files if "statistics" not in f.lower()]
    
    elif os.path.isdir(pattern):
        # Конкретная директория
        files = find_all_test_files(pattern)
    
    elif "*" in pattern or "?" in pattern:
        # Используем шаблон glob
        files = glob.glob(pattern)
        # Исключаем специальные файлы
        files = [f for f in files if "statistics" not in f.lower() and "index" not in f.lower()]
    
    else:
        # Пытаемся интерпретировать как путь к директории
        if os.path.exists(pattern):
            files = find_all_test_files(pattern)
        else:
            # Пытаемся найти в последней генерации
            base_dir = get_last_generation_path()
            if base_dir:
                # Ищем файл с таким именем
                search_path = os.path.join(base_dir, "**", f"{pattern}.json")
                files = glob.glob(search_path, recursive=True)
            else:
                files = []
    
    # Сортируем для воспроизводимости
    files.sort()
    
    # Ограничиваем если нужно
    if limit > 0:
        files = files[:limit]
    
    return files


def print_test_summary(files: List[str]):
    """Печатает сводную информацию о тестах."""
    if not files:
        print("❌ Не найдены тестовые файлы")
        return
    
    print(f"📁 Найдено {len(files)} тестовых файлов")
    
    # Анализируем распределение по группам
    groups = {}
    sizes = {}
    
    for file in files:
        filename = Path(file).stem
        # Пытаемся определить группу из имени файла
        for group in ["tiny", "small", "medium", "large", "xlarge", "stress", "special"]:
            if f"_{group}_" in filename or filename.startswith(f"{group}_"):
                groups[group] = groups.get(group, 0) + 1
                break
        
        # Пытаемся определить размер фрейма из пути
        parent_dir = Path(file).parent.name
        if parent_dir in ["tiny", "small", "medium", "large", "xlarge", "stress"]:
            sizes[parent_dir] = sizes.get(parent_dir, 0) + 1
    
    if groups:
        print("📊 Распределение по группам (из имен файлов):")
        for group, count in sorted(groups.items()):
            print(f"  {group:10}: {count:3} тестов")
    
    if sizes:
        print("📊 Распределение по директориям:")
        for size, count in sorted(sizes.items()):
            print(f"  {size:10}: {count:3} тестов")
    
    # Показываем первые 10 файлов
    if len(files) <= 10:
        print("📋 Все тестовые файлы:")
        for f in files:
            print(f"  • {Path(f).name}")
    else:
        print("📋 Первые 10 тестовых файлов:")
        for f in files[:10]:
            print(f"  • {Path(f).name}")
        print(f"  ... и еще {len(files) - 10} файлов")


def main():
    parser = argparse.ArgumentParser(
        description='Запуск бенчмарков Демпстера-Шейфера',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Запуск последней генерации тестов (по умолчанию)
  python scripts/run_benchmark.py --library our
  
  # Запуск последней генерации с 3 повторениями
  python scripts/run_benchmark.py --library our --repetitions 3
  
  # Запуск только tiny тестов из последней генерации
  python scripts/run_benchmark.py --library our --tests tiny
  
  # Запуск всех тестов (из всех генераций)
  python scripts/run_benchmark.py --library our --tests all
  
  # Запуск по конкретному пути
  python scripts/run_benchmark.py --library our --tests "data/generated/tests_20240115_123456"
  
  # Запуск по шаблону
  python scripts/run_benchmark.py --library our --tests "data/generated/*/small/*.json"
  
  # Ограничение количества тестов
  python scripts/run_benchmark.py --library our --tests last --limit 10
  
  # Другая библиотека (когда адаптеры будут готовы)
  python scripts/run_benchmark.py --library pyds --tests small
        """
    )
    
    parser.add_argument('--library', required=True,
                       choices=['our', 'pyds', 'dempster_shafer'],
                       help='Библиотека для тестирования')
    
    parser.add_argument('--tests', default='last',
                       help='Тесты для запуска: "last", "all", "tiny", "small", "medium", "large", "xlarge", "stress", "special", или путь/шаблон')
    
    parser.add_argument('--limit', type=int, default=0,
                       help='Ограничить количество тестов (0 = все)')
    
    parser.add_argument('--output', default='results',
                       help='Директория для сохранения результатов')
    
    parser.add_argument('--discount', type=float, default=0.1,
                       help='Коэффициент дисконтирования (по умолчанию: 0.1)')
    
    parser.add_argument('--repetitions', type=int, default=1,
                       help='Количество повторений каждого теста (по умолчанию: 1)')
    
    parser.add_argument('--quick', action='store_true',
                       help='Быстрый режим: запуск только первых 5 тестов с 1 повторением')
    
    args = parser.parse_args()
    
    print(f"🔬 ЗАПУСК БЕНЧМАРКА ДЛЯ БИБЛИОТЕКИ: {args.library}")
    print("=" * 70)
    
    # Проверяем quick режим
    if args.quick:
        print("⚡️  БЫСТРЫЙ РЕЖИМ АКТИВИРОВАН")
        if args.tests == 'last':
            args.tests = 'tiny'  # В quick режиме используем tiny тесты
        if args.limit == 0:
            args.limit = 5  # Ограничиваем 5 тестами
        args.repetitions = 1  # Только 1 повторение
        args.output = 'results/quick_run'
    
    # Получаем тестовые файлы
    test_files = get_test_files_by_pattern(args.tests, args.limit)
    
    if not test_files:
        print(f"❌ Не найдены тестовые файлы по шаблону: {args.tests}")
        print("\nДоступные опции для --tests:")
        print("  last/latest  - последняя генерация (по умолчанию)")
        print("  all          - все тесты из всех генераций")
        print("  tiny         - только tiny тесты")
        print("  small        - только small тесты")
        print("  medium       - только medium тесты")
        print("  large        - только large тесты")
        print("  xlarge       - только xlarge тесты")
        print("  stress       - только stress тесты")
        print("  special      - только специальные тесты")
        print("  <путь>       - конкретный путь к директории или файлу")
        print("  <шаблон>     - шаблон glob (например: 'data/generated/*/small/*.json')")
        
        # Проверяем существование последней генерации
        last_gen = get_last_generation_path()
        if last_gen:
            print(f"\n📁 Последняя генерация найдена: {last_gen}")
            print(f"   Используйте: python scripts/run_benchmark.py --library {args.library} --tests last")
        else:
            print("\n⚠️  Последняя генерация не найдена.")
            print("   Сначала сгенерируйте тесты: python scripts/generate_test_data.py")
        
        sys.exit(1)
    
    # Выводим информацию о тестах
    print_test_summary(test_files)
    
    if args.limit > 0 and len(test_files) > args.limit:
        print(f"\n⚠️  Ограничение: будет запущено только {args.limit} тестов из {len(test_files)} найденных")
    
    print(f"\n🔄 Повторений каждого теста: {args.repetitions}")
    print(f"📁 Результаты будут сохранены в: {args.output}")
    
    # Создаем адаптер
    try:
        adapter = get_adapter(args.library)
    except NotImplementedError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Запускаем тестирование
    runner = UniversalBenchmarkRunner(adapter, args.library)
    
    try:
        summary = runner.run_test_suite(
            test_files=test_files,
            output_dir=args.output,
            discount_factor=args.discount,
            repetitions=args.repetitions
        )
        
        # Выводим сводку
        print("\n" + "=" * 70)
        print("📊 СВОДКА РЕЗУЛЬТАТОВ:")
        print("=" * 70)
        
        print(f"Библиотека: {summary['library']}")
        print(f"Всего тестов: {summary['total_tests']}")
        print(f"Повторений каждого теста: {summary['repetitions']}")
        print(f"Всего запусков: {summary['total_tests'] * summary['repetitions']}")
        print(f"Общее время: {summary['total_time']:.2f} сек")
        print(f"Среднее время на тест: {summary['avg_time_per_test']:.3f} сек")
        
        if 'by_frame_size' in summary and summary['by_frame_size']:
            print("\n🔢 Производительность по размеру фрейма:")
            print("-" * 50)
            print("Эл. | Тестов | Повтор. | Среднее время | Min | Max")
            print("-" * 50)
            
            for size, stats in sorted(summary['by_frame_size'].items(), key=lambda x: int(x[0])):
                print(f"{size:3} | {stats['test_count']:6} | {stats['total_repetitions']:7} | "
                      f"{stats['avg_time']:12.3f} сек | {stats['min_time']:5.3f} | {stats['max_time']:5.3f}")
        
        if 'operation_timings' in summary:
            # Находим самые затратные операции
            print("\n📈 Самые затратные операции:")
            print("-" * 50)
            operations = []
            for op, stats in summary['operation_timings'].items():
                if stats['percentage'] > 1 and op != 'total_time' and op != 'load':
                    operations.append((op, stats))
            
            # Сортируем по проценту времени
            operations.sort(key=lambda x: x[1]['percentage'], reverse=True)
            
            for op, stats in operations[:5]:  # Только топ-5
                print(f"{op:30} | {stats['avg']:7.3f} сек | {stats['percentage']:5.1f}%")
        
        print("\n✅ Тестирование завершено успешно!")
        print(f"📁 Результаты сохранены в: {runner.current_run_dir}")
        
        # Создаем быстрый отчет
        if args.quick:
            quick_report = os.path.join(runner.current_run_dir, "quick_report.txt")
            with open(quick_report, 'w') as f:
                f.write(f"Библиотека: {summary['library']}\n")
                f.write(f"Тестов: {summary['total_tests']}\n")
                f.write(f"Повторений: {summary['repetitions']}\n")
                f.write(f"Общее время: {summary['total_time']:.2f} сек\n")
                f.write(f"Среднее время на тест: {summary['avg_time_per_test']:.3f} сек\n")
            print(f"📝 Быстрый отчет сохранен в: {quick_report}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при выполнении тестирования: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()