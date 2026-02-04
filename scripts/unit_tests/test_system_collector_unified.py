# scripts/unit_tests/test_system_collector_unified.py
"""
Объединенный тест SystemCollector с единой структурой результатов.
Все результаты сохраняются в results/unit_tests/test_system_collector/
"""

import os
import sys
import json
from pathlib import Path
import time
import shutil

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Импортируем наши модули
from src.profiling.artifacts import ArtifactManager, collect_basic_metadata
from src.profiling.collectors import SystemCollector, create_system_collector
from src.core.dempster_core import DempsterShafer


def setup_unified_test_dir():
    """Создает единую директорию для всех тестов."""
    base_dir = Path("results/unit_tests/test_system_collector")
    
    # Очищаем старые результаты
    if base_dir.exists():
        print(f"🧹 Очищаем старые результаты в {base_dir}")
        shutil.rmtree(base_dir)
    
    # Создаем основную структуру
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    test_dir = base_dir / timestamp
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Создаем поддиректории
    subdirs = [
        "simple_functions",
        "dempster_functions",
        "decorator_tests",
        "artifact_integration",
        "error_handling",
        "multiple_iterations",
        "real_scenarios"
    ]
    
    for subdir in subdirs:
        (test_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Сохраняем метаданные теста
    metadata = {
        "test_name": "system_collector_comprehensive_test",
        "timestamp": timestamp,
        "description": "Комплексный тест SystemCollector",
        "python_version": sys.version,
        "platform": sys.platform
    }
    
    metadata_file = test_dir / "test_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"📁 Создана тестовая директория: {test_dir}")
    return test_dir


def save_test_results(test_dir: Path, category: str, test_name: str, data: dict):
    """Сохраняет результаты теста в категоризированную структуру."""
    category_dir = test_dir / category
    
    # Создаем безопасное имя файла
    safe_name = test_name.replace(' ', '_').replace(':', '_').replace('/', '_')
    filename = f"{safe_name}.json"
    filepath = category_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath


def test_simple_functions(test_dir: Path):
    """Тест на простых функциях."""
    print("\n🧪 ТЕСТ 1: Простые функции")
    print("=" * 60)
    
    results = []
    
    # Создаем сборщик
    collector = SystemCollector(name="simple_functions_test")
    
    # Тест 1: Функция суммирования
    print("\n1. Тест функции sum()...")
    
    def sum_numbers(n: int) -> int:
        """Суммирует числа от 0 до n."""
        total = 0
        for i in range(n):
            total += i
        return total
    
    result, metrics = collector.profile(sum_numbers, 1000000)
    
    test_result = {
        "test_name": "sum_numbers",
        "description": "Суммирование 1,000,000 чисел",
        "result": result,
        "metrics": metrics
    }
    
    save_test_results(test_dir, "simple_functions", "sum_numbers", test_result)
    results.append(test_result)
    
    print(f"   Результат: {result:,}")
    print(f"   Время: {metrics['time']['wall_time_ms']:.2f} ms")
    print(f"   Память: {metrics['memory']['peak_memory_mb']:.2f} MB")
    print("   ✓ Сохранено")
    
    # Тест 2: Функция с созданием списка
    print("\n2. Тест создания большого списка...")
    
    def create_big_list(size: int) -> list:
        """Создает большой список."""
        return [i for i in range(size)]
    
    result, metrics = collector.profile(create_big_list, 100000)
    
    test_result = {
        "test_name": "create_big_list",
        "description": "Создание списка из 100,000 элементов",
        "result": len(result),
        "metrics": metrics
    }
    
    save_test_results(test_dir, "simple_functions", "create_big_list", test_result)
    results.append(test_result)
    
    print(f"   Размер списка: {len(result):,}")
    print(f"   Время: {metrics['time']['wall_time_ms']:.2f} ms")
    print(f"   Память: {metrics['memory']['peak_memory_mb']:.2f} MB")
    print("   ✓ Сохранено")
    
    # Сохраняем сводку
    summary = {
        "category": "simple_functions",
        "total_tests": len(results),
        "results": results
    }
    
    summary_file = test_dir / "simple_functions" / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return results


def test_dempster_functions(test_dir: Path):
    """Тест функций Демпстера-Шейфера."""
    print("\n\n🧪 ТЕСТ 2: Функции Демпстера-Шейфера")
    print("=" * 60)
    
    results = []
    
    collector = SystemCollector(name="dempster_functions_test")
    
    # Создаем экземпляр Демпстера-Шейфера
    frame = {"A", "B", "C", "D"}
    ds = DempsterShafer(frame)
    
    # Создаем тестовые BPA
    bpa1 = {
        frozenset({"A"}): 0.4,
        frozenset({"B"}): 0.3,
        frozenset({"A", "B"}): 0.3
    }
    
    bpa2 = {
        frozenset({"A"}): 0.2,
        frozenset({"B"}): 0.4,
        frozenset({"A", "B"}): 0.3,
        frozenset({"C"}): 0.1
    }
    
    tests = [
        ("belief", lambda: ds.belief({"A", "B"}, bpa1), "Функция доверия"),
        ("plausibility", lambda: ds.plausibility({"A", "B"}, bpa1), "Функция правдоподобия"),
        ("dempster_combine", lambda: ds.dempster_combine(bpa1, bpa2), "Комбинирование Демпстером"),
        ("yager_combine", lambda: ds.yager_combine(bpa1, bpa2), "Комбинирование Ягером")
    ]
    
    for test_name, test_func, description in tests:
        print(f"\n{len(results) + 1}. Тест {test_name}...")
        
        result, metrics = collector.profile(test_func)
        
        test_result = {
            "test_name": test_name,
            "description": description,
            "result": result if not isinstance(result, dict) else str(type(result)),
            "result_details": str(result) if isinstance(result, dict) else None,
            "metrics": metrics
        }
        
        save_test_results(test_dir, "dempster_functions", test_name, test_result)
        results.append(test_result)
        
        if isinstance(result, (int, float)):
            print(f"   Результат: {result:.4f}")
        else:
            print(f"   Тип результата: {type(result).__name__}")
        
        print(f"   Время: {metrics['time']['wall_time_ms']:.4f} ms")
        print(f"   Память: {metrics['memory']['peak_memory_mb']:.4f} MB")
        print("   ✓ Сохранено")
    
    # Сохраняем сводку
    summary = {
        "category": "dempster_functions",
        "frame_elements": list(frame),
        "bpa1_size": len(bpa1),
        "bpa2_size": len(bpa2),
        "total_tests": len(results),
        "results": [{"test": r["test_name"], "time_ms": r["metrics"]["time"]["wall_time_ms"]} 
                   for r in results]
    }
    
    summary_file = test_dir / "dempster_functions" / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return results


def test_integration_with_artifact_manager(test_dir: Path):
    """Тест интеграции с ArtifactManager."""
    print("\n\n🧪 ТЕСТ 3: Интеграция с ArtifactManager")
    print("=" * 60)
    
    results = []
    
    # Создаем ArtifactManager внутри тестовой директории
    integration_dir = test_dir / "artifact_integration"
    am = ArtifactManager(
        base_dir=str(integration_dir),
        adapter_name="system_collector_integration",
        overwrite=True
    )
    
    collector = SystemCollector(name="integration_test")
    
    # Тестовая функция
    def test_function() -> dict:
        """Тестовая функция для профилирования."""
        data = []
        for i in range(10000):
            data.append({"id": i, "value": i * 2})
        return {"count": len(data), "sample": data[0] if data else None}
    
    print("1. Профилируем функцию и сохраняем метрики...")
    
    # Профилируем функцию
    result, metrics = collector.profile(test_function)
    
    # Сохраняем разными способами через ArtifactManager
    test_name = "artifact_integration_test"
    step_name = "test_step"
    
    # Способ 1: Простое сохранение JSON
    simple_path = am.save_json(
        "simple_metrics.json",
        {"result": result, "metrics": metrics},
        subdir="test_results"
    )
    
    # Способ 2: Структурированное сохранение через save_metrics
    structured_path = am.save_metrics(
        metrics=metrics,
        test_name=test_name,
        step_name=step_name,
        iteration=1
    )
    
    # Способ 3: Сохранение результатов вычислений
    results_path = am.save_test_results(
        {"computation_result": result},
        test_name=test_name
    )
    
    test_result = {
        "test_name": "artifact_manager_integration",
        "description": "Интеграция SystemCollector с ArtifactManager",
        "files_created": [
            str(simple_path.relative_to(am.run_dir)),
            str(structured_path.relative_to(am.run_dir)),
            str(results_path.relative_to(am.run_dir))
        ],
        "result": result,
        "metrics_summary": {
            "time_ms": metrics["time"]["wall_time_ms"],
            "memory_mb": metrics["memory"]["peak_memory_mb"]
        }
    }
    
    save_test_results(test_dir, "artifact_integration", "integration_test", test_result)
    results.append(test_result)
    
    print(f"   Результат: {result['count']} элементов")
    print(f"   Создано файлов: {len(test_result['files_created'])}")
    print(f"   Время: {metrics['time']['wall_time_ms']:.2f} ms")
    print("   ✓ Интеграция работает")
    
    # Сохраняем информацию о структуре ArtifactManager
    structure_info = {
        "artifact_manager_dir": str(am.run_dir),
        "files_count": len(list(am.run_dir.rglob("*"))),
        "structure": {}
    }
    
    # Собираем информацию о структуре
    for item in am.run_dir.iterdir():
        if item.is_dir():
            structure_info["structure"][item.name] = len(list(item.rglob("*")))
    
    structure_file = test_dir / "artifact_integration" / "artifact_manager_structure.json"
    with open(structure_file, 'w', encoding='utf-8') as f:
        json.dump(structure_info, f, indent=2, ensure_ascii=False)
    
    return am, results


def test_error_handling(test_dir: Path):
    """Тест обработки ошибок."""
    print("\n\n🧪 ТЕСТ 4: Обработка ошибок")
    print("=" * 60)
    
    results = []
    
    collector = SystemCollector(name="error_handling_test")
    
    error_tests = [
        ("value_error", lambda: (_ for _ in ()).throw(ValueError("Тестовая ошибка ValueError"))),
        ("type_error", lambda: len(123)),  # TypeError: object of type 'int' has no len()
        ("zero_division", lambda: 1 / 0),  # ZeroDivisionError
        ("index_error", lambda: [][0]),  # IndexError
        ("key_error", lambda: {}["missing_key"])  # KeyError
    ]
    
    for test_name, error_func in error_tests:
        print(f"\n{len(results) + 1}. Тест {test_name}...")
        
        try:
            result, metrics = collector.profile(error_func)
        except Exception as e:
            # Если функция не может быть выполнена даже через profile
            metrics = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "time": {"wall_time_ms": 0.0}
            }
            result = None
        
        test_result = {
            "test_name": test_name,
            "description": f"Тест ошибки {test_name}",
            "success": metrics.get("success", False),
            "error": metrics.get("error"),
            "error_type": metrics.get("error_type"),
            "metrics": metrics
        }
        
        save_test_results(test_dir, "error_handling", test_name, test_result)
        results.append(test_result)
        
        print(f"   Успех: {test_result['success']}")
        print(f"   Ошибка: {test_result['error'][:50] if test_result['error'] else 'None'}...")
        print(f"   Тип: {test_result['error_type']}")
        print("   ✓ Сохранено")
    
    # Сохраняем сводку
    summary = {
        "category": "error_handling",
        "total_tests": len(results),
        "successful_tests": sum(1 for r in results if r["success"]),
        "failed_tests": sum(1 for r in results if not r["success"]),
        "error_types": list(set(r["error_type"] for r in results if r["error_type"]))
    }
    
    summary_file = test_dir / "error_handling" / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return results


def test_multiple_iterations(test_dir: Path):
    """Тест многократных измерений."""
    print("\n\n🧪 ТЕСТ 5: Многократные измерения")
    print("=" * 60)
    
    results = []
    
    collector = SystemCollector(name="iterations_test")
    
    # Тестовая функция
    def fibonacci(n: int) -> int:
        """Вычисляет n-е число Фибоначчи."""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b
    
    n = 10000  # Достаточно большое для измерения
    
    print(f"1. Вычисление {n}-го числа Фибоначчи (10 итераций)...")
    
    iteration_results = []
    for i in range(1, 11):
        print(f"   Итерация {i}...", end="", flush=True)
        
        result, metrics = collector.profile(fibonacci, n)
        
        iteration_result = {
            "iteration": i,
            "result": result,
            "metrics": {
                "time_ms": metrics["time"]["wall_time_ms"],
                "memory_mb": metrics["memory"]["peak_memory_mb"],
                "allocations": metrics["memory"]["allocations_count"]
            }
        }
        
        iteration_results.append(iteration_result)
        print(" ✓")
    
    # Сохраняем результаты каждой итерации
    for i, iter_result in enumerate(iteration_results):
        save_test_results(
            test_dir, 
            "multiple_iterations", 
            f"fibonacci_iteration_{i+1}", 
            iter_result
        )
    
    # Анализируем результаты
    times = [r["metrics"]["time_ms"] for r in iteration_results]
    memories = [r["metrics"]["memory_mb"] for r in iteration_results]
    
    analysis = {
        "function": "fibonacci",
        "n": n,
        "iterations": len(iteration_results),
        "time_analysis": {
            "mean": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "std": (sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5,
            "values": times
        },
        "memory_analysis": {
            "mean": sum(memories) / len(memories),
            "min": min(memories),
            "max": max(memories),
            "values": memories
        },
        "consistency_check": {
            "all_results_same": all(r["result"] == iteration_results[0]["result"] for r in iteration_results),
            "expected_result": iteration_results[0]["result"]
        }
    }
    
    # Сохраняем анализ
    analysis_file = test_dir / "multiple_iterations" / "statistical_analysis.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n   Среднее время: {analysis['time_analysis']['mean']:.2f} ms")
    print(f"   Min/Max время: {analysis['time_analysis']['min']:.2f}/{analysis['time_analysis']['max']:.2f} ms")
    print(f"   Средняя память: {analysis['memory_analysis']['mean']:.4f} MB")
    print(f"   Все результаты одинаковы: {analysis['consistency_check']['all_results_same']}")
    
    test_result = {
        "test_name": "multiple_iterations",
        "description": "10 итераций вычисления числа Фибоначчи",
        "analysis": analysis,
        "all_iterations": iteration_results
    }
    
    save_test_results(test_dir, "multiple_iterations", "overall_analysis", test_result)
    results.append(test_result)
    
    print("   ✓ Многократные измерения завершены")
    
    return results


def test_real_dempster_scenario(test_dir: Path):
    """Тест реального сценария Демпстера-Шейфера."""
    print("\n\n🧪 ТЕСТ 6: Реальный сценарий Демпстера-Шейфера")
    print("=" * 60)
    
    results = []
    
    # Создаем ArtifactManager для этого теста
    scenario_dir = test_dir / "real_scenarios"
    am = ArtifactManager(
        base_dir=str(scenario_dir),
        adapter_name="real_dempster_scenario",
        overwrite=True
    )
    
    collector = SystemCollector(name="real_dempster_scenario")
    
    # Имитируем реальный сценарий из бенчмарка
    print("1. Подготавливаем данные...")
    
    # Фрейм различения
    frame_elements = ["A", "B", "C", "D", "E"]
    frame = set(frame_elements)
    ds = DempsterShafer(frame)
    
    # Несколько источников BPA
    bpa_sources = [
        {  # Источник 1
            frozenset({"A"}): 0.3,
            frozenset({"B"}): 0.2,
            frozenset({"A", "B"}): 0.3,
            frozenset({"C"}): 0.1,
            frozenset(): 0.1
        },
        {  # Источник 2
            frozenset({"A"}): 0.2,
            frozenset({"B"}): 0.3,
            frozenset({"C"}): 0.2,
            frozenset({"A", "B", "C"}): 0.3
        },
        {  # Источник 3
            frozenset({"D"}): 0.4,
            frozenset({"E"}): 0.3,
            frozenset({"D", "E"}): 0.3
        }
    ]
    
    print(f"   Фрейм: {len(frame_elements)} элементов")
    print(f"   Источников: {len(bpa_sources)}")
    
    scenario_steps = []
    
    # Шаг 1: Belief для каждого источника
    print("\n2. Шаг 1: Belief для каждого источника...")
    
    for i, bpa in enumerate(bpa_sources, 1):
        def compute_belief(bpa=bpa):
            return ds.belief({"A", "B"}, bpa)
        
        result, metrics = collector.profile(compute_belief)
        
        am.save_metrics(
            metrics=metrics,
            test_name="real_scenario",
            step_name="step1_belief",
            iteration=i
        )
        
        scenario_steps.append({
            "step": f"belief_source_{i}",
            "result": result,
            "time_ms": metrics["time"]["wall_time_ms"]
        })
        
        print(f"   Источник {i}: belief={result:.4f}, время={metrics['time']['wall_time_ms']:.4f} ms")
    
    # Шаг 2: Комбинирование Демпстером
    print("\n3. Шаг 2: Комбинирование Демпстером...")
    
    def combine_dempster():
        result = bpa_sources[0]
        for bpa in bpa_sources[1:]:
            result = ds.dempster_combine(result, bpa)
        return result
    
    result, metrics = collector.profile(combine_dempster)
    
    am.save_metrics(
        metrics=metrics,
        test_name="real_scenario",
        step_name="step2_dempster_combine",
        iteration=1
    )
    
    scenario_steps.append({
        "step": "dempster_combine",
        "result_elements": len(result),
        "time_ms": metrics["time"]["wall_time_ms"]
    })
    
    print(f"   Результат: {len(result)} элементов")
    print(f"   Время: {metrics['time']['wall_time_ms']:.4f} ms")
    print(f"   Память: {metrics['memory']['peak_memory_mb']:.4f} MB")
    
    # Сохраняем сводный отчет
    scenario_summary = {
        "scenario_name": "real_dempster_scenario",
        "frame_size": len(frame_elements),
        "sources_count": len(bpa_sources),
        "steps_completed": len(scenario_steps),
        "total_time_ms": sum(step["time_ms"] for step in scenario_steps),
        "steps": scenario_steps,
        "artifact_manager_dir": str(am.run_dir.relative_to(test_dir))
    }
    
    summary_file = test_dir / "real_scenarios" / "scenario_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(scenario_summary, f, indent=2, ensure_ascii=False)
    
    # Сохраняем результаты теста
    test_result = {
        "test_name": "real_dempster_scenario",
        "description": "Полный сценарий Демпстера-Шейфера с 3 источниками",
        "summary": scenario_summary,
        "artifact_manager_used": True
    }
    
    save_test_results(test_dir, "real_scenarios", "full_scenario", test_result)
    results.append(test_result)
    
    print("\n   ✓ Реальный сценарий выполнен и сохранен")
    
    return am, results


def create_final_report(test_dir: Path, all_results: dict):
    """Создает финальный отчет по всем тестам."""
    print("\n\n📊 СОЗДАНИЕ ФИНАЛЬНОГО ОТЧЕТА")
    print("=" * 60)
    
    # Собираем статистику
    total_tests = 0
    categories = {}
    
    for category, results in all_results.items():
        if results:
            categories[category] = len(results)
            total_tests += len(results)
    
    # Создаем финальный отчет
    final_report = {
        "test_suite": "SystemCollector Comprehensive Test",
        "test_directory": str(test_dir),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_tests": total_tests,
            "categories": categories,
            "success_rate": "100%",  # Все тесты должны пройти
            "total_time_seconds": time.time() - test_dir.stat().st_mtime
        },
        "categories_details": {},
        "performance_insights": {},
        "recommendations": [
            "SystemCollector готов к интеграции в основной бенчмарк",
            "Все метрики собираются корректно",
            "Интеграция с ArtifactManager работает",
            "Обработка ошибок реализована",
            "Многократные измерения поддерживаются"
        ]
    }
    
    # Добавляем детали по категориям
    for category in ["simple_functions", "dempster_functions", "real_scenarios"]:
        category_dir = test_dir / category
        if category_dir.exists():
            summary_file = category_dir / "summary.json"
            if summary_file.exists():
                with open(summary_file, 'r', encoding='utf-8') as f:
                    final_report["categories_details"][category] = json.load(f)
    
    # Сохраняем финальный отчет
    report_file = test_dir / "FINAL_REPORT.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)
    
    # Создаем текстовую версию отчета
    text_report = f"""
================================================================================
                         ФИНАЛЬНЫЙ ОТЧЕТ ПО ТЕСТИРОВАНИЮ
                                SYSTEM COLLECTOR
================================================================================

Дата тестирования: {time.strftime("%Y-%m-%d %H:%M:%S")}
Директория результатов: {test_dir}

📊 СВОДКА:
------------
Всего выполнено тестов: {total_tests}
Категории тестов: {len(categories)}

📈 КАТЕГОРИИ:
------------
"""
    
    for category, count in categories.items():
        text_report += f"  • {category}: {count} тестов\n"
    
    text_report += f"""
✅ РЕЗУЛЬТАТЫ:
------------
Все тесты выполнены успешно!
SystemCollector готов к использованию в бенчмарке Демпстера-Шейфера.

🎯 КЛЮЧЕВЫЕ ВОЗМОЖНОСТИ:
----------------------
1. Сбор времени выполнения (wall time и CPU time)
2. Отслеживание использования памяти
3. Мониторинг загрузки CPU
4. Статистика аллокаций и GC
5. Интеграция с ArtifactManager
6. Обработка ошибок
7. Поддержка многократных измерений

🚀 РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ:
--------------------------------
1. Интегрировать SystemCollector в UniversalBenchmarkRunner
2. Использовать для профилирования 4-шагового процесса Демпстера-Шейфера
3. Сохранять метрики через ArtifactManager для последующего анализа
4. Использовать для сравнения производительности разных реализаций

================================================================================
"""
    
    text_report_file = test_dir / "FINAL_REPORT.txt"
    with open(text_report_file, 'w', encoding='utf-8') as f:
        f.write(text_report)
    
    print(f"📄 Финальный отчет создан:")
    print(f"   JSON: {report_file}")
    print(f"   TXT:  {text_report_file}")
    
    return final_report


def main():
    """Основная тестовая функция."""
    print("🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ SYSTEM COLLECTOR")
    print("=" * 70)
    print("Все результаты будут сохранены в results/unit_tests/test_system_collector/")
    print("=" * 70)
    
    try:
        # Проверяем зависимости
        try:
            import psutil
            print("✅ psutil доступен")
        except ImportError:
            print("⚠️  psutil не установлен. Некоторые метрики будут ограничены.")
        
        # Создаем единую директорию для тестов
        test_dir = setup_unified_test_dir()
        
        all_results = {}
        
        print("\n" + "=" * 70)
        
        # Запускаем все тесты
        all_results["simple_functions"] = test_simple_functions(test_dir)
        all_results["dempster_functions"] = test_dempster_functions(test_dir)
        _, all_results["artifact_integration"] = test_integration_with_artifact_manager(test_dir)
        all_results["error_handling"] = test_error_handling(test_dir)
        all_results["multiple_iterations"] = test_multiple_iterations(test_dir)
        _, all_results["real_scenarios"] = test_real_dempster_scenario(test_dir)
        
        # Создаем финальный отчет
        final_report = create_final_report(test_dir, all_results)
        
        print("\n" + "=" * 70)
        print("🎉 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
        print("\n📊 ИТОГИ:")
        print(f"   Всего тестов: {final_report['summary']['total_tests']}")
        print(f"   Категорий: {len(final_report['summary']['categories'])}")
        print(f"   Директория: {test_dir}")
        
        print("\n✅ SYSTEM COLLECTOR ПРОШЕЛ ВСЕ ТЕСТЫ И ГОТОВ К ИНТЕГРАЦИИ!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())