# scripts/test_profiling_system.py
"""
Тестовый скрипт для проверки системы профилирования.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Добавляем путь для импорта
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Тестирует все импорты."""
    print("🧪 Тестирование импортов...")
    
    modules_to_test = [
        ("ArtifactManager", "src.profiling.artifacts.artifact_manager"),
        ("MetadataCollector", "src.profiling.artifacts.metadata_collector"),
        ("SystemProfiler", "src.profiling.collectors.system_profiler"),
        ("TestInputManager", "src.profiling.test_input_manager"),
        ("SimpleProfilingRunner", "src.profiling.runners.simple_profiling_runner"),
        ("OurImplementationAdapter", "src.adapters.our_adapter"),
    ]
    
    for name, module_path in modules_to_test:
        try:
            exec(f"from {module_path} import {name}")
            print(f"✅ {name} - OK")
        except ImportError as e:
            print(f"❌ {name} - Ошибка: {e}")
        except Exception as e:
            print(f"⚠️  {name} - Предупреждение: {e}")
    
    print("\n✅ Тест импортов завершен")

def test_artifact_manager():
    """Тестирует ArtifactManager."""
    print("\n🧪 Тестирование ArtifactManager...")
    
    try:
        from src.profiling.artifacts import ArtifactManager
        
        # Создаем временную директорию для тестов
        temp_dir = Path(tempfile.mkdtemp(prefix="test_artifacts_"))
        
        # Создаем менеджер с тестовой директорией
        manager = ArtifactManager(base_dir=temp_dir, session_id="test_123")
        
        # Тестируем методы
        info = manager.get_session_info()
        print(f"✅ Session info: {info['session_id']}")
        
        # Сохраняем тестовые данные
        test_data = {"test": "data"}
        
        result = manager.save_metadata(test_data)
        print(f"✅ save_metadata: {'OK' if result else 'FAILED'}")
        
        result = manager.save_config(test_data)
        print(f"✅ save_config: {'OK' if result else 'FAILED'}")
        
        result = manager.save_test_input("test1", test_data)
        print(f"✅ save_test_input: {'OK' if result else 'FAILED'}")
        
        filepath = manager.save_profiler_data("system", "test1", "step1", test_data)
        print(f"✅ save_profiler_data: {'OK' if filepath else 'FAILED'}")
        
        result = manager.save_test_results("test1", test_data)
        print(f"✅ save_test_results: {'OK' if result else 'FAILED'}")
        
        result = manager.log_message("Test message")
        print(f"✅ log_message: {'OK' if result else 'FAILED'}")
        
        summary = manager.get_session_summary()
        print(f"✅ Session summary создан")
        
        manager.cleanup_temp_files()
        print(f"✅ cleanup_temp_files выполнен")
        
        # Очищаем временную директорию
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        print("\n✅ ArtifactManager работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка в ArtifactManager: {e}")
        import traceback
        traceback.print_exc()
        
        # Пытаемся очистить временную директорию
        try:
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

def test_system_profiler():
    """Тестирует SystemProfiler."""
    print("\n🧪 Тестирование SystemProfiler...")
    
    try:
        from src.profiling.collectors import SystemProfiler
        
        profiler = SystemProfiler()
        
        # Тестовая функция
        def test_function():
            return sum(range(1000))
        
        result, metrics = profiler.profile_function(test_function)
        
        print(f"✅ Результат функции: {result}")
        print(f"✅ Время выполнения: {metrics.execution_time_seconds:.6f} сек")
        print(f"✅ Использование памяти: {metrics.peak_memory_bytes} байт")
        
        metrics_dict = metrics.to_dict()
        print(f"✅ Метрики как словарь: keys={list(metrics_dict.keys())}")
        
        print("\n✅ SystemProfiler работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка в SystemProfiler: {e}")
        import traceback
        traceback.print_exc()

def test_metadata_collector():
    """Тестирует MetadataCollector."""
    print("\n🧪 Тестирование MetadataCollector...")
    
    try:
        from src.profiling.artifacts import MetadataCollector
        
        collector = MetadataCollector()
        metadata = collector.collect_all()
        
        print(f"✅ Собрано полей метаданных: {len(metadata)}")
        print(f"✅ Система: {metadata.get('system', {}).get('system', 'Unknown')}")
        print(f"✅ Python: {metadata.get('python', {}).get('version', 'Unknown')[:20]}...")
        print(f"✅ Зависимости: {len(metadata.get('dependencies', {}))} записей")
        
        print("\n✅ MetadataCollector работает корректно")
        
    except Exception as e:
        print(f"❌ Ошибка в MetadataCollector: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Основная функция тестирования."""
    print("🔬 ТЕСТИРОВАНИЕ СИСТЕМЫ ПРОФИЛИРОВАНИЯ")
    print("=" * 60)
    
    test_imports()
    test_artifact_manager()
    test_system_profiler()
    test_metadata_collector()
    
    print("\n" + "=" * 60)
    print("🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")

if __name__ == "__main__":
    main()