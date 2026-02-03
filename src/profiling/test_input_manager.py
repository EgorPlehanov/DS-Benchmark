# src/profiling/test_input_manager.py
"""
Управление входными тестами для профилирования.
Упрощенная версия.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass

@dataclass
class TestCase:
    """Контейнер для тестового случая."""
    name: str
    filepath: Path
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    @property
    def frame_size(self) -> int:
        """Размер фрейма различения."""
        return len(self.data.get('frame_of_discernment', []))
    
    @property
    def sources_count(self) -> int:
        """Количество источников."""
        return len(self.data.get('bba_sources', []))
    
    def get_summary(self) -> Dict[str, Any]:
        """Возвращает краткую сводку о тесте."""
        return {
            'name': self.name,
            'filepath': str(self.filepath),
            'frame_size': self.frame_size,
            'sources_count': self.sources_count,
            'metadata': self.metadata
        }

class TestInputManager:
    """
    Управляет загрузкой и фильтрацией тестовых данных.
    """
    
    def __init__(self, tests_dir: Path):
        """
        Инициализация менеджера тестов.
        
        Args:
            tests_dir: Директория с тестами
        """
        self.tests_dir = Path(tests_dir)
        
        if not self.tests_dir.exists():
            raise ValueError(f"Директория с тестами не существует: {tests_dir}")
    
    def discover_tests(self, 
                      max_tests: Optional[int] = None,
                      filter_by_size: Optional[tuple] = None,
                      filter_by_group: Optional[str] = None) -> List[TestCase]:
        """
        Обнаруживает все тесты в директории.
        
        Args:
            max_tests: Максимальное количество тестов
            filter_by_size: Фильтр по размеру фрейма (min, max)
            filter_by_group: Фильтр по группе тестов
            
        Returns:
            Список тестовых случаев
        """
        test_files = []
        
        # Рекурсивно ищем JSON файлы
        for root, dirs, files in os.walk(self.tests_dir):
            for file in files:
                if file.endswith('.json') and file != 'statistics.json':
                    filepath = Path(root) / file
                    test_files.append(filepath)
        
        # Сортируем по имени для воспроизводимости
        test_files.sort()
        
        # Применяем лимит
        if max_tests:
            test_files = test_files[:max_tests]
        
        # Загружаем тесты
        test_cases = []
        for filepath in test_files:
            try:
                test_case = self._load_test(filepath)
                
                # Применяем фильтры
                if filter_by_size:
                    min_size, max_size = filter_by_size
                    if not (min_size <= test_case.frame_size <= max_size):
                        continue
                
                if filter_by_group:
                    group = test_case.metadata.get('test_group', '')
                    if group != filter_by_group:
                        continue
                
                test_cases.append(test_case)
                
            except Exception as e:
                print(f"⚠️  Ошибка загрузки теста {filepath}: {e}")
                continue
        
        return test_cases
    
    def _load_test(self, filepath: Path) -> TestCase:
        """Загружает тест из файла."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Извлекаем имя теста
        name = filepath.stem
        
        # Извлекаем метаданные
        metadata = data.get('metadata', {})
        
        # Добавляем информацию о файле
        metadata['file_path'] = str(filepath)
        metadata['file_size_bytes'] = filepath.stat().st_size
        
        # Определяем группу теста из пути
        relative_path = filepath.relative_to(self.tests_dir)
        if len(relative_path.parts) > 1:
            metadata['test_group'] = relative_path.parts[0]
        
        return TestCase(
            name=name,
            filepath=filepath,
            data=data,
            metadata=metadata
        )