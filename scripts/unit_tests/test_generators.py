#!/usr/bin/env python3
"""
Тестируем генераторы данных
"""

import sys
import os
import json
from datetime import datetime

# Добавляем корневую директорию проекта в путь Python
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
sys.path.insert(0, project_root)

# Теперь импортируем из src
try:
    from src.generators.dass_generator import DassGenerator
    from src.generators.validator import DassValidator
    print("✅ Модули успешно импортированы")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


def save_results_with_timestamp(test_name: str, results_data: dict):
    """
    Сохраняет результаты тестов в структурированную папку с временной меткой
    
    Args:
        test_name: название теста (например, 'generators_test')
        results_data: результаты теста (без полных тестовых данных)
    """
    # Создаем основную структуру папок
    base_dir = os.path.join(project_root, "results")
    os.makedirs(base_dir, exist_ok=True)
    
    # Создаем папку для конкретного теста
    test_dir = os.path.join(base_dir, "unit_tests", test_name)
    os.makedirs(test_dir, exist_ok=True)
    
    # Создаем папку с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamp_dir = os.path.join(test_dir, timestamp)
    os.makedirs(timestamp_dir, exist_ok=True)
    
    # Сохраняем основные данные теста (без полных тестовых данных)
    test_results = {
        "metadata": {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "description": "Тестирование генераторов DASS данных",
            "project_root": project_root
        },
        **results_data  # Добавляем все результаты
    }
    
    # Сохраняем все в один JSON файл
    main_result_file = os.path.join(timestamp_dir, "test_results.json")
    with open(main_result_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    # Сохраняем только примеры тестовых данных (по одному на группу)
    save_example_test_data(timestamp_dir, results_data)
    
    # Создаем краткий отчет
    create_text_report(timestamp_dir, results_data)
    
    print(f"📁 Результаты сохранены в: {os.path.relpath(timestamp_dir, project_root)}")
    return timestamp_dir


def save_example_test_data(timestamp_dir: str, results: dict):
    """Сохраняет примеры тестовых данных (не все)"""
    example_dir = os.path.join(timestamp_dir, "examples")
    os.makedirs(example_dir, exist_ok=True)
    
    # Сохраняем только базовые примеры из test_suite
    if 'test_suite' in results.get('test_data', {}):
        test_suite = results['test_data']['test_suite']
        for name, data in test_suite.items():
            # Сохраняем только основные данные, без избыточной информации
            simplified_data = {
                "metadata": data.get('metadata', {}),
                "frame_of_discernment": data.get('frame_of_discernment', []),
                "bba_sources": data.get('bba_sources', [])
            }
            
            filename = os.path.join(example_dir, f"example_{name}.json")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(simplified_data, f, indent=2, ensure_ascii=False)
        
        print(f"  📄 Сохранены примеры: {len(test_suite)} файлов")


def create_text_report(timestamp_dir: str, results: dict):
    """Создает текстовый отчет с результатами"""
    report_file = os.path.join(timestamp_dir, "test_report.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("ОТЧЕТ ПО ТЕСТИРОВАНИЮ ГЕНЕРАТОРОВ ДАННЫХ\n")
        f.write("="*70 + "\n\n")
        
        # 1. Валидация
        f.write("1. ВАЛИДАЦИЯ ТЕСТОВЫХ ДАННЫХ:\n")
        f.write("-"*70 + "\n")
        
        validation_results = results.get("validation_results", {})
        for name, v_result in validation_results.items():
            status = "✓ ВАЛИДЕН" if v_result['valid'] else "✗ НЕВАЛИДЕН"
            f.write(f"  {name:10}: {status:15} | Фрейм: {v_result['frame_size']:2} элем. | Источников: {v_result['sources_count']}\n")
        
        # 2. Файловые операции
        f.write("\n2. ФАЙЛОВЫЕ ОПЕРАЦИИ:\n")
        f.write("-"*70 + "\n")
        
        file_ops = results.get("file_operations", [])
        success_count = sum(1 for op in file_ops 
                           if op.get('save_success') and 
                           op.get('load_success') and 
                           op.get('validation_after_load'))
        
        f.write(f"  Всего операций: {len(file_ops)}\n")
        f.write(f"  Успешных: {success_count}\n")
        f.write(f"  Неудачных: {len(file_ops) - success_count}\n")
        
        # Показываем неудачные операции
        failed_ops = [op for op in file_ops 
                     if not (op.get('save_success') and 
                            op.get('load_success') and 
                            op.get('validation_after_load'))]
        
        if failed_ops:
            f.write("\n  Неудачные операции:\n")
            for op in failed_ops[:3]:  # Показываем первые 3
                filename = os.path.basename(op.get('filename', ''))
                errors = op.get('errors_after_load', ['неизвестно'])[0]
                f.write(f"    - {filename}: {errors}\n")
            if len(failed_ops) > 3:
                f.write(f"    ... и еще {len(failed_ops) - 3} ошибок\n")
        
        # 3. Статистика оптимизированной генерации
        if 'optimized_generation' in results:
            f.write("\n3. ОПТИМИЗИРОВАННАЯ ГЕНЕРАЦИЯ:\n")
            f.write("-"*70 + "\n")
            
            optimized_results = results['optimized_generation']
            total_tests = 0
            total_valid = 0
            
            for group_name, stats in optimized_results.items():
                group_total = stats.get('total_tests', 0)
                group_valid = stats.get('valid_tests', 0)
                total_tests += group_total
                total_valid += group_valid
                
                f.write(f"  {group_name:10}: {group_valid:3}/{group_total:3} валидных тестов\n")
            
            if total_tests > 0:
                success_rate = (total_valid / total_tests) * 100
                f.write(f"\n  Итого: {total_valid}/{total_tests} тестов валидны ({success_rate:.1f}%)\n")
        
        # 4. Итоговая сводка
        f.write("\n4. ИТОГИ:\n")
        f.write("-"*70 + "\n")
        
        summary = results.get("summary", {})
        
        f.write(f"  Валидация: {summary.get('validation_success_rate', 0):.1f}%\n")
        f.write(f"  Файловые операции: {summary.get('file_operations_success_rate', 0):.1f}%\n")
        
        if 'optimized_generation' in results:
            f.write(f"  Оптимизированная генерация: {summary.get('optimized_success_rate', 0):.1f}%\n")
        
        # 5. Общий результат
        f.write("\n" + "="*70 + "\n")
        
        all_passed = (
            summary.get('validation_success_rate', 0) == 100 and
            summary.get('file_operations_success_rate', 0) == 100
        )
        
        if all_passed:
            f.write("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!\n")
        else:
            f.write("⚠️  ЕСТЬ ПРОБЛЕМЫ, ТРЕБУЕТСЯ ОТЛАДКА\n")
        
        f.write("="*70 + "\n")
    
    print(f"📄 Текстовый отчет создан: {os.path.basename(report_file)}")


def test_generators():
    """Основная логика тестирования генераторов"""
    print("🧪 Тестируем генераторы DASS данных...")
    
    # Собираем все результаты теста
    all_results = {
        "validation_results": {},
        "file_operations": [],
        "summary": {}
    }
    
    # 1. Генерируем тестовый набор
    print("\n" + "="*60)
    print("1. ГЕНЕРАЦИЯ ТЕСТОВОГО НАБОРА")
    print("="*60)
    
    test_suite = DassGenerator.generate_test_suite()
    
    validation_results = {}
    for name, data in test_suite.items():
        print(f"\n  {name.upper()}:")
        print(f"    Фрейм: {len(data['frame_of_discernment'])} элементов")
        print(f"    Источники: {len(data['bba_sources'])}")
        
        # Валидируем
        is_valid, errors = DassValidator.validate_data(data)
        validation_results[name] = {
            "valid": is_valid,
            "errors": errors if errors else None,
            "frame_size": len(data['frame_of_discernment']),
            "sources_count": len(data['bba_sources'])
        }
        
        if is_valid:
            print("    ✓ Данные валидны")
        else:
            print(f"    ✗ Ошибки: {errors}")
    
    all_results["validation_results"] = validation_results
    all_results["test_data"] = {"test_suite": test_suite}
    
    # 2. Тестируем файловые операции в памяти (без сохранения на диск)
    print("\n" + "="*60)
    print("2. ТЕСТИРОВАНИЕ ФАЙЛОВЫХ ОПЕРАЦИЙ (в памяти)")
    print("="*60)
    
    # Используем временную директорию в памяти или в /tmp
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        file_operations = []
        
        for name, data in test_suite.items():
            filename = os.path.join(temp_dir, f"test_{name}.json")
            
            # Сохраняем
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                save_success = True
            except Exception:
                save_success = False
            
            # Загружаем обратно
            if save_success:
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                    load_success = True
                except Exception:
                    load_success = False
                    loaded = None
            else:
                load_success = False
                loaded = None
            
            # Валидируем загруженные данные
            if loaded:
                is_valid, errors = DassValidator.validate_data(loaded)
                
                file_operation = {
                    "filename": f"temp/test_{name}.json",
                    "save_success": save_success,
                    "load_success": True,
                    "validation_after_load": is_valid,
                    "errors_after_load": errors if errors else None,
                }
                
                if is_valid:
                    print(f"  ✓ Файл {name}: сохранен, загружен и валиден")
                else:
                    print(f"  ✗ Файл {name}: ошибки при загрузке: {errors}")
            else:
                file_operation = {
                    "filename": f"temp/test_{name}.json",
                    "save_success": save_success,
                    "load_success": False,
                    "validation_after_load": False,
                    "errors_after_load": ["Не удалось загрузить файл"]
                }
                print(f"  ✗ Файл {name}: не удалось загрузить")
            
            file_operations.append(file_operation)
    
    all_results["file_operations"] = file_operations
    
    # 3. Генерация расширенного набора тестов (опционально)
    print("\n" + "="*60)
    print("3. ГЕНЕРАЦИЯ РАСШИРЕННОГО НАБОРА ТЕСТОВ")
    print("="*60)
    
    try:
        # Пытаемся импортировать оптимизированный генератор
        scripts_dir = os.path.join(project_root, "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        from generate_test_data import OptimizedTestDataGenerator
        
        generator = OptimizedTestDataGenerator()
        optimized_suite = generator.generate_optimized_test_suite()
        
        # Валидируем оптимизированный набор
        optimized_results = {}
        total_tests = 0
        total_valid = 0
        
        for group_name, tests in optimized_suite.items():
            print(f"\n  {group_name.upper()}: {len(tests)} тестов")
            
            valid_count = 0
            for test in tests:
                is_valid, errors = DassValidator.validate_data(test)
                if is_valid:
                    valid_count += 1
            
            optimized_results[group_name] = {
                "total_tests": len(tests),
                "valid_tests": valid_count,
                "invalid_tests": len(tests) - valid_count
            }
            
            total_tests += len(tests)
            total_valid += valid_count
            
            if valid_count == len(tests):
                print(f"    ✓ Все тесты валидны")
            else:
                print(f"    ⚠️  {valid_count}/{len(tests)} тестов валидны")
        
        all_results["optimized_generation"] = optimized_results
        all_results["optimized_stats"] = {
            "total_tests": total_tests,
            "valid_tests": total_valid,
            "success_rate": (total_valid / total_tests * 100) if total_tests > 0 else 0
        }
        
    except ImportError as e:
        print(f"  ⚠️  Не удалось импортировать OptimizedTestDataGenerator: {e}")
        print(f"    Пропускаем тест оптимизированной генерации")
    except Exception as e:
        print(f"  ⚠️  Ошибка при генерации оптимизированного набора: {e}")
    
    # 4. Подведение итогов
    print("\n" + "="*60)
    print("4. ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    # Анализируем результаты
    total_tests = len(validation_results)
    valid_tests = sum(1 for r in validation_results.values() if r['valid'])
    
    file_operations_success = sum(1 for op in file_operations 
                                 if op.get('save_success') and 
                                 op.get('load_success') and 
                                 op.get('validation_after_load'))
    
    summary = {
        "total_tests_generated": total_tests,
        "valid_tests_generated": valid_tests,
        "validation_success_rate": (valid_tests / total_tests * 100) if total_tests > 0 else 0,
        "file_operations_total": len(file_operations),
        "file_operations_successful": file_operations_success,
        "file_operations_success_rate": (file_operations_success / len(file_operations) * 100) if file_operations else 0
    }
    
    # Добавляем статистику оптимизированной генерации если есть
    if 'optimized_stats' in all_results:
        stats = all_results['optimized_stats']
        summary.update({
            "optimized_total_tests": stats['total_tests'],
            "optimized_valid_tests": stats['valid_tests'],
            "optimized_success_rate": stats['success_rate']
        })
    
    all_results["summary"] = summary
    
    # Выводим сводку
    print(f"\n📊 СТАТИСТИКА:")
    print(f"  Сгенерировано тестов: {summary['total_tests_generated']}")
    print(f"  Валидных тестов: {summary['valid_tests_generated']} ({summary['validation_success_rate']:.1f}%)")
    print(f"  Успешных файловых операций: {summary['file_operations_successful']}/{summary['file_operations_total']} ({summary['file_operations_success_rate']:.1f}%)")
    
    if 'optimized_success_rate' in summary:
        print(f"  Оптимизированная генерация: {summary['optimized_success_rate']:.1f}% успеха")
    
    # Сохраняем результаты
    timestamp_dir = save_results_with_timestamp(
        test_name="generators_test",
        results_data=all_results
    )
    
    print(f"\n✅ Тестирование завершено!")
    print(f"📁 Все результаты сохранены в: {os.path.relpath(timestamp_dir, project_root)}")


def main():
    try:
        test_generators()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()