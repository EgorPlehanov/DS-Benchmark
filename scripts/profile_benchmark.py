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
from src.adapters.factory import create_adapter, list_adapters


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
    available_profilers = {"cpu", "memory", "line", "scalene"}

    def parse_bool(value: str) -> bool:
        """Парсер булевого значения для CLI-параметров вида True/False."""
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
        raise argparse.ArgumentTypeError("Ожидается булево значение: True/False")

    def parse_profiling(value: str):
        """Парсер режима профилирования: full | off | list(cpu,memory,...)"""
        normalized = value.strip().lower()

        if normalized == "full":
            return ["cpu", "memory", "line", "scalene"]

        if normalized == "off":
            return []

        tokens = [token.strip().lower() for token in value.replace(";", ",").split(",") if token.strip()]
        invalid = sorted(set(tokens) - available_profilers)

        if not tokens:
            raise argparse.ArgumentTypeError(
                "--profiling должен быть 'full', 'off' или списком профайлеров: cpu,memory,line,scalene"
            )

        if invalid:
            raise argparse.ArgumentTypeError(
                f"Неизвестные профайлеры: {', '.join(invalid)}. Доступно: {', '.join(sorted(available_profilers))}"
            )

        return list(dict.fromkeys(tokens))

    parser = argparse.ArgumentParser(
        description='Запуск бенчмарков с профилированием Демпстера-Шейфера'
    )
    
    parser.add_argument('--library', 
                       default='our',
                       choices=list_adapters(),
                       help='Библиотека для тестирования')
    
    parser.add_argument('--tests',
                       default='last',
                       help='Путь к тестам или "last" для последней генерации')
    
    parser.add_argument('--profiling',
                       default='full',
                       type=parse_profiling,
                       help='Режим профилирования: full | off | список (cpu,memory,line,scalene)')
    
    parser.add_argument('--iterations',
                       type=int,
                       default=3,
                       help='Количество повторов каждого шага внутри одного прогона теста')
    
    parser.add_argument('--output-dir',
                       default='results/profiling',
                       help='Директория для результатов')
    
    parser.add_argument('--max-tests',
                       type=int,
                       default=None,
                       help='Максимальное количество тестов для запуска')

    parser.add_argument('--sanitize-paths',
                       type=parse_bool,
                       default=True,
                       help='Нормализовать пути в raw-профилях (по умолчанию: True). '
                            'Для отключения передайте: --sanitize-paths False')
    
    args = parser.parse_args()
    
    print("🔬 ЗАПУСК БЕНЧМАРКА С ПРОФИЛИРОВАНИЕМ")
    print("=" * 60)
    print(f"Библиотека: {args.library}")
    selected_profilers = args.profiling
    profiling_mode = "off" if not selected_profilers else "full" if set(selected_profilers) == available_profilers else "custom"
    print(f"Профилирование: {profiling_mode}")
    if selected_profilers:
        print(f"Профайлеры: {', '.join(selected_profilers)}")
    else:
        print("Профайлеры: отключены")
    print(f"Повторов каждого шага: {args.iterations}")
    print(f"Нормализация путей: {'включена' if args.sanitize_paths else 'выключена'}")
    
    runner = None

    try:
        # Получаем путь к тестам
        test_dir = get_test_dir(args.tests)
        print(f"Тесты: {test_dir}")
        
        # Создаем адаптер
        adapter = create_adapter(args.library)

        # Проверяем backend-зависимости адаптера один раз перед запуском тестов
        adapter._ensure_backend()
        
        # Создаем раннер с профилированием
        runner = ProfilingBenchmarkRunner(
            adapter=adapter,
            results_dir=args.output_dir,
            profiling_mode=profiling_mode,
            selected_profilers=selected_profilers,
            sanitize_paths=args.sanitize_paths,
        )

        effective_iterations = 1 if not selected_profilers else args.iterations

        # Сохраняем параметры запуска для воспроизводимости
        runner.set_run_parameters(
            library=args.library,
            tests=args.tests,
            resolved_test_dir=test_dir,
            profiling=args.profiling,
            profiling_mode=profiling_mode,
            profilers=selected_profilers,
            iterations=args.iterations,
            effective_iterations=effective_iterations,
            output_dir=args.output_dir,
            max_tests=args.max_tests,
            sanitize_paths=args.sanitize_paths,
        )
        
        # Запускаем тесты
        print(f"\n🚀 Запуск тестов из: {test_dir}")
        summary = runner.run_test_suite(
            test_dir=test_dir,
            iterations=effective_iterations,
            max_tests=args.max_tests
        )
        
        # Выводим информацию о профилировании
        if selected_profilers:
            profiling_dir = Path(runner.profiling_dir)
            reports_dir = profiling_dir / "reports"
            print(f"\n📊 ДАННЫЕ ПРОФИЛИРОВАНИЯ:")
            print(f"   Отчеты: {reports_dir}")
            print(f"   Сырые данные профайлеров: {profiling_dir}")
            
            # Подсчитываем количество файлов
            report_files = list(reports_dir.rglob("*.json"))
            raw_files = [
                p for p in profiling_dir.rglob("*.json")
                if "reports" not in p.parts and "inputs" not in p.parts
            ]
            
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
    finally:
        if runner is not None:
            try:
                runner.cleanup()
            except Exception as cleanup_error:
                print(f"⚠️  Ошибка при cleanup: {cleanup_error}")


if __name__ == "__main__":
    sys.exit(main())
