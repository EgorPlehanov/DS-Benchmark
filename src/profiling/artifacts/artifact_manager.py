# src/profiling/artifacts/artifact_manager.py
"""
ArtifactManager - управление всеми файлами профилирования для Windows.
Главная задача: организовать структурированное сохранение ВСЕХ данных.
"""

import os
import json
import shutil
import platform  # <-- ИСПРАВЛЕНО: добавлен импорт
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List  # <-- ИСПРАВЛЕНО: добавлен List
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ArtifactManager")


class ArtifactManager:
    """
    Центральный менеджер для сохранения всех артефактов профилирования.
    
    Создает структуру:
    results/profiling/{adapter}_{timestamp}/
    ├── meta.json
    ├── input/
    ├── profilers/
    │   ├── system/
    │   ├── scalene/
    │   └── ...
    ├── test_results/
    ├── metrics/
    ├── visualizations/
    └── session_info.json
    """
    
    def __init__(self, 
                 base_dir: str = "results/profiling",
                 adapter_name: str = "our",
                 run_id: Optional[str] = None,
                 overwrite: bool = False):
        """
        Инициализация менеджера артефактов.
        
        Args:
            base_dir: Базовая директория (results/profiling)
            adapter_name: Имя адаптера (our, pyds, ds)
            run_id: ID запуска (если None, генерируется автоматически)
            overwrite: Перезаписывать ли существующую директорию
        """
        self.base_dir = Path(base_dir)
        self.adapter_name = adapter_name
        
        # Генерируем уникальный ID запуска
        if run_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.run_id = f"{adapter_name}_{timestamp}"
        else:
            self.run_id = run_id
        
        # Полный путь к директории результатов
        self.run_dir = self.base_dir / self.run_id
        
        # Проверяем и создаем директорию
        self._setup_directory(overwrite)
        
        # Создаем поддиректории
        self._create_subdirectories()
        
        # Инициализируем сессию
        self._init_session()
        
        logger.info(f"🎯 ArtifactManager инициализирован: {self.run_dir}")
    
    def _setup_directory(self, overwrite: bool) -> None:
        """Создает или очищает директорию результатов."""
        if self.run_dir.exists():
            if overwrite:
                logger.warning(f"⚠️  Удаляем существующую директорию: {self.run_dir}")
                shutil.rmtree(self.run_dir)
            else:
                raise FileExistsError(
                    f"Директория уже существует: {self.run_dir}\n"
                    f"Используйте --overwrite или укажите другой run_id"
                )
        
        self.run_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Создана директория: {self.run_dir}")
    
    def _create_subdirectories(self) -> None:
        """Создает все необходимые поддиректории."""
        subdirs = [
            "input",                    # Входные данные тестов
            "profilers/system",        # Системные метрики
            "profilers/scalene",       # Scalene профилирование
            "profilers/memray",        # Memray профилирование
            "test_results",            # Результаты вычислений ДШ
            "metrics",                 # Числовые метрики
            "visualizations",          # Графики и диаграммы
            "logs",                    # Логи выполнения
            "tmp"                      # Временные файлы
        ]
        
        for subdir in subdirs:
            full_path = self.run_dir / subdir
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"📂 Создана поддиректория: {full_path}")
    
    def _init_session(self) -> None:
        """Инициализирует сессию - создает базовые метаданные."""
        session_info = {
            "session_id": self.run_id,
            "created_at": datetime.now().isoformat(),
            "adapter": self.adapter_name,
            "base_dir": str(self.base_dir.absolute()),
            "platform": os.name,
            "system": platform.system(),  # <-- ИСПРАВЛЕНО: используем platform.system()
            "artifact_manager_version": "1.0.0"
        }
        
        self.save_json("session_info.json", session_info, root_dir=True)
        logger.info(f"📝 Инициализирована сессия: {self.run_id}")
    
    def get_path(self, 
                filename: str, 
                subdir: Optional[str] = None,
                root_dir: bool = False) -> Path:
        """
        Возвращает полный путь к файлу.
        
        Args:
            filename: Имя файла
            subdir: Поддиректория (например, 'profilers/system')
            root_dir: Если True, возвращает путь в корневой директории
            
        Returns:
            Path: Полный путь к файлу
        """
        if root_dir:
            return self.run_dir / filename
        
        if subdir:
            return self.run_dir / subdir / filename
        
        return self.run_dir / filename
    
    def save_json(self, 
                 filename: str, 
                 data: Dict[str, Any],
                 subdir: Optional[str] = None,
                 root_dir: bool = False,
                 indent: int = 2) -> Path:
        """
        Сохраняет данные в JSON файл.
        
        Args:
            filename: Имя файла (например, 'metrics.json')
            data: Данные для сохранения
            subdir: Поддиректория
            root_dir: Если True, сохраняет в корневую директорию
            indent: Отступ для форматирования JSON
            
        Returns:
            Path: Путь к сохраненному файлу
        """
        filepath = self.get_path(filename, subdir, root_dir)
        
        # Создаем директорию если её нет
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        logger.debug(f"💾 Сохранен JSON: {filepath}")
        return filepath
    
    def save_text(self,
                 filename: str,
                 content: str,
                 subdir: Optional[str] = None) -> Path:
        """
        Сохраняет текстовый файл.
        """
        filepath = self.get_path(filename, subdir)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"📝 Сохранен текстовый файл: {filepath}")
        return filepath
    
    def save_binary(self,
                   filename: str,
                   data: bytes,
                   subdir: Optional[str] = None) -> Path:
        """
        Сохраняет бинарный файл.
        """
        filepath = self.get_path(filename, subdir)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(data)
        
        logger.debug(f"🔧 Сохранен бинарный файл: {filepath}")
        return filepath
    
    def save_file(self,
                 source_path: Union[str, Path],
                 dest_filename: Optional[str] = None,
                 subdir: Optional[str] = None) -> Path:
        """
        Копирует существующий файл в директорию артефактов.
        """
        source_path = Path(source_path)
        
        if dest_filename is None:
            dest_filename = source_path.name
        
        dest_path = self.get_path(dest_filename, subdir)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(source_path, dest_path)
        logger.debug(f"📋 Скопирован файл: {source_path} -> {dest_path}")
        
        return dest_path
    
    def save_metrics(self,
                    metrics: Dict[str, Any],
                    test_name: str,
                    step_name: str,
                    iteration: int = 1) -> Path:
        """
        Сохраняет метрики профилирования.
        
        Args:
            metrics: Словарь с метриками
            test_name: Имя теста
            step_name: Имя шага (step1, step2, ...)
            iteration: Номер итерации
            
        Returns:
            Path: Путь к сохраненному файлу
        """
        filename = f"{test_name}_{step_name}_iter{iteration}_metrics.json"
        subdir = f"metrics/{test_name}"
        
        # Добавляем метаданные
        enhanced_metrics = {
            **metrics,
            "_metadata": {
                "test_name": test_name,
                "step_name": step_name,
                "iteration": iteration,
                "saved_at": datetime.now().isoformat()
            }
        }
        
        return self.save_json(filename, enhanced_metrics, subdir)
    
    def save_test_input(self,
                       test_data: Dict[str, Any],
                       test_name: str) -> Path:
        """
        Сохраняет входные данные теста.
        """
        filename = f"{test_name}_input.json"
        subdir = f"input/{test_name}"
        
        return self.save_json(filename, test_data, subdir)
    
    def save_test_results(self,
                         results: Dict[str, Any],
                         test_name: str) -> Path:
        """
        Сохраняет результаты вычислений Демпстера-Шейфера.
        """
        filename = f"{test_name}_results.json"
        subdir = f"test_results/{test_name}"
        
        return self.save_json(filename, results, subdir)
    
    def save_profiler_data(self,
                          profiler_name: str,
                          data: Dict[str, Any],
                          test_name: str,
                          step_name: str,
                          iteration: int = 1) -> Path:
        """
        Сохраняет данные профилировщика.
        """
        # JSON данные
        filename = f"{test_name}_{step_name}_iter{iteration}_{profiler_name}.json"
        subdir = f"profilers/{profiler_name}/{test_name}"
        
        # Добавляем метаданные
        enhanced_data = {
            **data,
            "_metadata": {
                "profiler": profiler_name,
                "test_name": test_name,
                "step_name": step_name,
                "iteration": iteration,
                "saved_at": datetime.now().isoformat()
            }
        }
        
        return self.save_json(filename, enhanced_data, subdir)
    
    def save_html_report(self,
                        html_content: str,
                        test_name: str,
                        step_name: str,
                        profiler_name: str) -> Path:
        """
        Сохраняет HTML отчет профилировщика.
        """
        filename = f"{test_name}_{step_name}_{profiler_name}.html"
        subdir = f"profilers/{profiler_name}/{test_name}/reports"
        
        return self.save_text(filename, html_content, subdir)
    
    def get_session_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущей сессии."""
        session_file = self.run_dir / "session_info.json"
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def update_metadata(self, metadata: Dict[str, Any]) -> Path:
        """
        Обновляет метаданные сессии.
        """
        current_info = self.get_session_info()
        current_info.update(metadata)
        current_info["updated_at"] = datetime.now().isoformat()
        
        return self.save_json("session_info.json", current_info, root_dir=True)
    
    def list_files(self, pattern: str = "**/*") -> List[Path]:  # <-- ИСПРАВЛЕНО: указан возвращаемый тип
        """
        Возвращает список всех файлов в директории артефактов.
        """
        return list(self.run_dir.glob(pattern))
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Возвращает сводку о сохраненных артефактах.
        """
        files = self.list_files("**/*")
        
        # Группируем по типам
        summary = {
            "session_id": self.run_id,
            "total_files": len(files),
            "by_type": {},
            "by_directory": {},
            "total_size_bytes": 0
        }
        
        for filepath in files:
            if filepath.is_file():
                # По расширению
                ext = filepath.suffix.lower()
                if ext not in summary["by_type"]:
                    summary["by_type"][ext] = 0
                summary["by_type"][ext] += 1
                
                # По директории
                rel_path = filepath.relative_to(self.run_dir)
                parent_dir = str(rel_path.parent)
                if parent_dir not in summary["by_directory"]:
                    summary["by_directory"][parent_dir] = 0
                summary["by_directory"][parent_dir] += 1
                
                # Размер
                summary["total_size_bytes"] += filepath.stat().st_size
        
        return summary
    
    def cleanup_temp_files(self) -> None:
        """Очищает временные файлы."""
        tmp_dir = self.run_dir / "tmp"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
            tmp_dir.mkdir(exist_ok=True)
            logger.info("🧹 Очищены временные файлы")
    
    def archive(self, output_path: Optional[str] = None) -> Path:
        """
        Создает архив со всеми артефактами.
        
        Args:
            output_path: Путь для архива (если None, создается рядом)
            
        Returns:
            Path: Путь к созданному архиву
        """
        if output_path is None:
            output_path = f"{self.run_id}.zip"
        
        output_path_str = str(output_path)  # <-- ИСПРАВЛЕНО: конвертируем в строку
        
        # Создаем архив
        archive_path = shutil.make_archive(
            str(Path(output_path_str).with_suffix('')),  # <-- ИСПРАВЛЕНО: создаем Path
            'zip',
            str(self.run_dir)  # <-- ИСПРАВЛЕНО: конвертируем в строку
        )
        
        logger.info(f"📦 Создан архив: {archive_path}")
        return Path(archive_path)
    
    def __repr__(self) -> str:
        """Строковое представление."""
        summary = self.get_summary()
        return (
            f"ArtifactManager(run_id='{self.run_id}', "
            f"files={summary['total_files']}, "
            f"size={summary['total_size_bytes'] / 1024:.1f} KB)"
        )


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С АРТЕФАКТАМИ
# ============================================================================

def create_artifact_manager(adapter_name: str = "our",
                          run_id: Optional[str] = None,
                          base_dir: str = "results/profiling",
                          overwrite: bool = False) -> ArtifactManager:
    """
    Фабричная функция для создания ArtifactManager.
    
    Args:
        adapter_name: Имя адаптера
        run_id: ID запуска
        base_dir: Базовая директория
        overwrite: Перезаписывать ли существующую директорию
        
    Returns:
        ArtifactManager: Созданный менеджер артефактов
    """
    return ArtifactManager(
        base_dir=base_dir,
        adapter_name=adapter_name,
        run_id=run_id,
        overwrite=overwrite
    )


def get_latest_artifact_dir(base_dir: str = "results/profiling") -> Optional[Path]:
    """
    Находит последнюю директорию с артефактами.
    
    Args:
        base_dir: Базовая директория
        
    Returns:
        Optional[Path]: Путь к последней директории или None
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        return None
    
    # Ищем все директории, сортируем по времени создания
    dirs = []
    for item in base_path.iterdir():
        if item.is_dir() and item.name != "__pycache__":
            try:
                # Пробуем извлечь timestamp из имени
                parts = item.name.split('_')
                if len(parts) >= 2:
                    # Формат: adapter_YYYYMMDD_HHMMSS
                    timestamp_str = f"{parts[-2]}_{parts[-1]}"
                    dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    dirs.append((dt, item))
            except (ValueError, IndexError):
                # Если не удалось распарсить, используем время модификации
                mtime = item.stat().st_mtime
                dirs.append((datetime.fromtimestamp(mtime), item))
    
    if not dirs:
        return None
    
    # Сортируем по времени (последний первый)
    dirs.sort(key=lambda x: x[0], reverse=True)
    return dirs[0][1]