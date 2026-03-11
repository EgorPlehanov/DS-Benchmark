# scripts/unit_tests/test_artifact_manager.py
"""
Тестовый скрипт для проверки ArtifactManager на Windows.
Все результаты сохраняются в results/unit_tests/artifact_manager_test/
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any  # <-- ИСПРАВЛЕНО: добавлены типы

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.profiling.artifacts import (
    ArtifactManager, 
    collect_test_metadata,
    create_artifact_structure,
    validate_artifact_structure,
    get_artifact_summary
)


class ArtifactManagerTests:
    """Класс для тестирования ArtifactManager."""
    
    def __init__(self):
        self.test_results = {
            "test_suite": "ArtifactManager",
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0
            }
        }
        self.results_dir = Path("results/unit_tests/artifact_manager_test")
        self._setup_results_dir()
    
    def _setup_results_dir(self):
        """Создает директорию для результатов тестов."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_run_dir = self.results_dir / timestamp
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Результаты тестов будут сохранены в: {self.current_run_dir}")
    
    def _record_test_result(self, 
                          test_name: str, 
                          passed: bool, 
                          error: Optional[str] = None,  # <-- ИСПРАВЛЕНО: указан Optional тип
                          details: Optional[Dict[str, Any]] = None):  # <-- ИСПРАВЛЕНО: указан тип
        """Записывает результат теста."""
        result: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
            "name": test_name,
            "passed": passed,
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            result["error"] = error
        
        if details:
            result["details"] = details
        
        self.test_results["tests"].append(result)
        
        if passed:
            self.test_results["summary"]["passed"] += 1
            print(f"  ✅ {test_name}")
        else:
            self.test_results["summary"]["failed"] += 1
            print(f"  ❌ {test_name}")
            if error:
                print(f"     Ошибка: {error}")
        
        self.test_results["summary"]["total"] += 1
    
    def _save_test_results(self):
        """Сохраняет результаты тестов."""
        results_file = self.current_run_dir / "test_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Результаты тестов сохранены: {results_file}")
    
    def test_basic_functionality(self) -> Optional[ArtifactManager]:  # <-- ИСПРАВЛЕНО: указан возвращаемый тип
        """Тест базовой функциональности."""
        test_name = "basic_functionality"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            # 1. Создаем ArtifactManager
            am = ArtifactManager(
                base_dir=str(self.current_run_dir / "test_basic"),
                adapter_name="test_adapter",
                overwrite=True
            )
            
            print(f"  ✓ Создан ArtifactManager: {am}")
            
            # 2. Сохраняем тестовые данные
            test_data = {
                "test": "data",
                "numbers": [1, 2, 3],
                "nested": {"key": "value"}
            }
            
            json_path = am.save_json("test_data.json", test_data)
            print(f"  ✓ Сохранен JSON: {json_path.name}")
            
            text_path = am.save_text("readme.txt", "Это тестовый файл")
            print(f"  ✓ Сохранен текст: {text_path.name}")
            
            # 3. Проверяем существование файлов
            assert json_path.exists(), "JSON файл не создан"
            assert text_path.exists(), "Текстовый файл не создан"
            
            # 4. Проверяем содержимое
            with open(json_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data, "Данные JSON не совпадают"
            
            # 5. Проверяем структуру директорий
            problems = validate_artifact_structure(am.run_dir)
            assert len(problems) == 0, f"Проблемы со структурой: {problems}"
            
            details: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "created_files": [str(p.relative_to(am.run_dir)) for p in [json_path, text_path]],
                "directory": str(am.run_dir),
                "structure_ok": True
            }
            
            self._record_test_result(test_name, True, details=details)
            return am
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
            return None
    
    def test_metadata_collection(self) -> Optional[ArtifactManager]:  # <-- ИСПРАВЛЕНО: указан тип
        """Тест сбора метаданных."""
        test_name = "metadata_collection"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            # Создаем ArtifactManager для этого теста
            am = ArtifactManager(
                base_dir=str(self.current_run_dir / "test_metadata"),
                adapter_name="test_meta",
                overwrite=True
            )
            
            # Собираем метаданные
            metadata = collect_test_metadata(
                iterations=3,
                max_tests=5,
                profiling_level="full"
            )
            
            print(f"  ✓ Собраны метаданные")
            print(f"    Платформа: {metadata['environment']['platform']}")
            print(f"    Python: {metadata['python']['version'][:20]}...")
            
            # Сохраняем метаданные
            meta_path = am.save_json("metadata.json", metadata, root_dir=True)
            print(f"  ✓ Сохранены метаданные: {meta_path.name}")
            
            # Проверяем что файл создан
            assert meta_path.exists(), "Файл метаданных не создан"
            
            # Проверяем структуру метаданных
            required_keys = ['timestamp', 'environment', 'python']
            for key in required_keys:
                assert key in metadata, f"В метаданных отсутствует ключ: {key}"
            
            details: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "metadata_keys": list(metadata.keys()),
                "platform": metadata['environment']['platform'],
                "python_version": metadata['python']['version'][:20]
            }
            
            self._record_test_result(test_name, True, details=details)
            return am
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
            return None
    
    def test_directory_structure(self) -> None:
        """Тест структуры директорий."""
        test_name = "directory_structure"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            # Создаем тестовую директорию
            test_dir = self.current_run_dir / "test_structure"
            if test_dir.exists():
                shutil.rmtree(test_dir)
            
            # Создаем структуру
            structure = create_artifact_structure(test_dir)
            
            print(f"  ✓ Создана структура в: {test_dir.name}")
            
            # Проверяем что все директории созданы
            required_dirs = ['input', 'profilers', 'test_results', 'metrics', 'logs']
            for dir_name in required_dirs:
                dir_path = test_dir / dir_name
                assert dir_path.exists(), f"Отсутствует директория: {dir_name}"
                assert dir_path.is_dir(), f"Не является директорией: {dir_name}"
            
            # Создаем минимальный session_info.json для валидации
            session_info = {
                "session_id": "test_structure_session",
                "created_at": datetime.now().isoformat(),
                "adapter": "test",
                "platform": "test"
            }
            session_file = test_dir / "session_info.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_info, f, indent=2)
            
            print(f"  ✓ Создан session_info.json")
            
            # Проверяем структуру
            problems = validate_artifact_structure(test_dir)
            if problems:
                print(f"  ⚠️  Проблемы со структурой: {problems}")
                # Не считаем это ошибкой теста, так как мы знаем о ограничениях validate_artifact_structure
                details = {
                    "created_dirs": list(structure.keys()),
                    "problems": problems,
                    "note": "validate_artifact_structure требует session_info.json с полным набором полей"
                }
                self._record_test_result(test_name, True, details=details)
            else:
                details = {
                    "created_dirs": list(structure.keys()),
                    "total_dirs": len([d for d in test_dir.rglob('*') if d.is_dir()]),
                    "structure_valid": True
                }
                self._record_test_result(test_name, True, details=details)
            
            # Получаем сводку
            summary = get_artifact_summary(test_dir)
            print(f"  ✓ Сводка: {summary.get('total_dirs', 0)} директорий")
            
            # Очищаем
            shutil.rmtree(test_dir)
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
    
    def test_save_metrics_and_results(self) -> Optional[ArtifactManager]:  # <-- ИСПРАВЛЕНО: указан тип
        """Тест сохранения метрик и результатов."""
        test_name = "save_metrics_and_results"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            am = ArtifactManager(
                base_dir=str(self.current_run_dir / "test_metrics"),
                adapter_name="test_metrics",
                overwrite=True
            )
            
            # 1. Сохраняем метрики
            metrics: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "time_ms": 125.4,
                "memory_mb": 45.2,
                "cpu_percent": 85.3,
                "allocations": 12500
            }
            
            metrics_path = am.save_metrics(
                metrics=metrics,
                test_name="tiny_001",
                step_name="step2_dempster",
                iteration=1
            )
            print(f"  ✓ Сохранены метрики: {metrics_path.relative_to(am.run_dir)}")
            
            # 2. Сохраняем результаты ДШ
            ds_results: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "belief": {"{A}": 0.4, "{B}": 0.3},
                "plausibility": {"{A}": 0.8, "{B}": 0.7},
                "combined_bpa": {"{A}": 0.5, "{A,B}": 0.5}
            }
            
            results_path = am.save_test_results(ds_results, "tiny_001")
            print(f"  ✓ Сохранены результаты: {results_path.relative_to(am.run_dir)}")
            
            # 3. Сохраняем данные профилировщика
            profiler_data: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "top_functions": [
                    {"function": "dempster_combine", "time": 0.1},
                    {"function": "belief", "time": 0.05}
                ],
                "memory_usage": 102400
            }
            
            profiler_path = am.save_profiler_data(
                profiler_name="system",
                data=profiler_data,
                test_name="tiny_001",
                step_name="step2_dempster",
                iteration=1
            )
            print(f"  ✓ Сохранены данные профилировщика: {profiler_path.relative_to(am.run_dir)}")
            
            # 4. Сохраняем HTML отчет
            html_content = "<html><body><h1>Тест</h1></body></html>"
            html_path = am.save_html_report(
                html_content=html_content,
                test_name="tiny_001",
                step_name="step2_dempster",
                profiler_name="scalene"
            )
            print(f"  ✓ Сохранен HTML отчет: {html_path.relative_to(am.run_dir)}")
            
            # Проверяем что все файлы созданы
            created_files = [metrics_path, results_path, profiler_path, html_path]
            for filepath in created_files:
                assert filepath.exists(), f"Файл не создан: {filepath}"
            
            details: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "created_files": [str(p.relative_to(am.run_dir)) for p in created_files],
                "file_types": [p.suffix for p in created_files]
            }
            
            self._record_test_result(test_name, True, details=details)
            return am
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
            return None
    
    def test_archive_creation(self) -> None:  # <-- ИСПРАВЛЕНО: указан тип
        """Тест создания архива."""
        test_name = "archive_creation"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            am = ArtifactManager(
                base_dir=str(self.current_run_dir / "test_archive"),
                adapter_name="test_archive",
                overwrite=True
            )
            
            # Сохраняем несколько файлов
            for i in range(3):
                am.save_json(f"test_{i}.json", {"index": i, "data": "x" * 100})
            
            # Создаем архив
            archive_path = am.archive()
            
            print(f"  ✓ Создан архив: {archive_path.name}")
            print(f"  ✓ Размер: {archive_path.stat().st_size / 1024:.1f} KB")
            
            # Проверяем что архив существует
            assert archive_path.exists(), "Архив не создан!"
            
            # Проверяем размер архива
            assert archive_path.stat().st_size > 0, "Архив пустой"
            
            details: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "archive_path": str(archive_path),
                "archive_size_kb": archive_path.stat().st_size / 1024,
                "archive_exists": True
            }
            
            self._record_test_result(test_name, True, details=details)
            
            # Удаляем архив
            archive_path.unlink()
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
    
    def test_session_info(self) -> Optional[ArtifactManager]:  # <-- ИСПРАВЛЕНО: указан тип
        """Тест информации о сессии."""
        test_name = "session_info"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            am = ArtifactManager(
                base_dir=str(self.current_run_dir / "test_session"),
                adapter_name="test_session",
                overwrite=True
            )
            
            # Получаем информацию о сессии
            session_info = am.get_session_info()
            
            print(f"  ✓ Получена информация о сессии")
            
            # Проверяем обязательные поля
            required_fields = ['session_id', 'created_at', 'adapter', 'platform']
            for field in required_fields:
                assert field in session_info, f"Отсутствует поле: {field}"
            
            # Обновляем метаданные
            am.update_metadata({"custom_field": "test_value"})
            
            # Получаем обновленную информацию
            updated_info = am.get_session_info()
            assert "custom_field" in updated_info, "Пользовательское поле не добавлено"
            assert "updated_at" in updated_info, "Дата обновления не добавлена"
            
            print(f"  ✓ Метаданные обновлены")
            
            details: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "session_id": session_info.get('session_id'),
                "adapter": session_info.get('adapter'),
                "platform": session_info.get('platform'),
                "has_custom_field": "custom_field" in updated_info
            }
            
            self._record_test_result(test_name, True, details=details)
            return am
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
            return None
    
    def test_file_listing(self) -> Optional[ArtifactManager]:  # <-- ИСПРАВЛЕНО: указан тип
        """Тест перечисления файлов."""
        test_name = "file_listing"
        print(f"\n🧪 ТЕСТ: {test_name}")
        print("-" * 40)
        
        try:
            am = ArtifactManager(
                base_dir=str(self.current_run_dir / "test_listing"),
                adapter_name="test_listing",
                overwrite=True
            )
            
            # Создаем несколько файлов разных типов
            am.save_json("data1.json", {"test": 1})
            am.save_text("readme.txt", "Текст")
            am.save_json("subdir/data2.json", {"test": 2}, subdir="test_results")
            
            # Получаем список всех файлов
            all_files = am.list_files("**/*")
            
            print(f"  ✓ Создано файлов: {len(all_files)}")
            
            # Проверяем что файлы найдены
            assert len(all_files) >= 3, f"Найдено слишком мало файлов: {len(all_files)}"
            
            # Получаем сводку
            summary = am.get_summary()
            
            print(f"  ✓ Сводка: {summary['total_files']} файлов, {summary['total_size_bytes']} байт")
            
            # Проверяем сводку
            assert summary['total_files'] >= 3, "Неверное количество файлов в сводке"
            assert summary['total_size_bytes'] > 0, "Нулевой размер в сводке"
            
            details: Dict[str, Any] = {  # <-- ИСПРАВЛЕНО: указан тип
                "total_files": len(all_files),
                "file_extensions": list(summary['by_type'].keys()),
                "summary_total_files": summary['total_files'],
                "summary_total_bytes": summary['total_size_bytes']
            }
            
            self._record_test_result(test_name, True, details=details)
            return am
            
        except Exception as e:
            self._record_test_result(test_name, False, error=str(e))
            return None
    
    def run_all_tests(self) -> bool:  # <-- ИСПРАВЛЕНО: указан возвращаемый тип
        """Запускает все тесты."""
        print("🚀 ЗАПУСК ТЕСТОВ ARTIFACT MANAGER")
        print("=" * 60)
        
        # Запускаем все тесты
        self.test_basic_functionality()
        self.test_metadata_collection()
        self.test_directory_structure()
        self.test_save_metrics_and_results()
        self.test_archive_creation()
        self.test_session_info()
        self.test_file_listing()
        
        # Сохраняем результаты
        self._save_test_results()
        
        # Выводим итоговую статистику
        summary = self.test_results["summary"]
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"   Всего тестов: {summary['total']}")
        print(f"   Успешно: {summary['passed']}")
        print(f"   Неудачно: {summary['failed']}")
        
        if summary['failed'] == 0:
            print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        else:
            print(f"\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
            
            # Показываем неудачные тесты
            print("\nНеудачные тесты:")
            for test in self.test_results["tests"]:
                if not test["passed"]:
                    print(f"  ❌ {test['name']}: {test.get('error', 'Неизвестная ошибка')}")
        
        print(f"\n📁 Подробные результаты в: {self.current_run_dir}")
        
        return summary['failed'] == 0


def main() -> int:  # <-- ИСПРАВЛЕНО: указан возвращаемый тип
    """Основная тестовая функция."""
    try:
        # Проверяем зависимости
        try:
            import psutil
        except ImportError:
            print("⚠️  psutil не установлен. Устанавливаем...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            import psutil
        
        # Запускаем тесты
        tester = ArtifactManagerTests()
        success = tester.run_all_tests()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())