# src/profiling/artifacts/artifact_manager.py
"""
ArtifactManager - управление всеми файлами профилирования.
Главная задача: организовать структурированное сохранение ВСЕХ данных.
"""

import json
import os
import platform
import re
import shutil
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

from ..path_sanitizer import sanitize_payload_paths, sanitize_text_paths

logger = logging.getLogger("ArtifactManager")


class ArtifactManager:
    """
    Центральный менеджер для сохранения всех артефактов профилирования.

    Создает структуру:
    results/profiling/{adapter}/{timestamp}/
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

    def __init__(
        self,
        base_dir: str = "results/profiling",
        adapter_name: str = "our",
        run_id: Optional[str] = None,
        overwrite: bool = False,
    ):
        """
        Args:
            base_dir: Базовая директория (results/profiling)
            adapter_name: Имя адаптера/библиотеки (our, py_dempster_shafer, ds)
            run_id: ID запуска (обычно timestamp)
            overwrite: Перезаписывать ли существующую директорию
        """
        self.base_dir = Path(base_dir)
        self.adapter_name = self._sanitize_name(adapter_name)

        if run_id is None:
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.run_id = self._sanitize_name(run_id)

        self.run_dir = self.base_dir / self.adapter_name / self.run_id

        self._setup_directory(overwrite)
        self._create_subdirectories()
        self._init_session()

        logger.info("🎯 ArtifactManager инициализирован: %s", self.run_dir)

    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Безопасно нормализует значение для имени директории/файла."""
        normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name).strip())
        return normalized.strip("._") or "unknown"

    def _setup_directory(self, overwrite: bool) -> None:
        """Создает или очищает директорию результатов."""
        if self.run_dir.exists():
            if overwrite:
                logger.warning("⚠️  Удаляем существующую директорию: %s", self.run_dir)
                shutil.rmtree(self.run_dir)
            else:
                raise FileExistsError(
                    f"Директория уже существует: {self.run_dir}\n"
                    f"Используйте --overwrite или укажите другой run_id"
                )

        self.run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("📁 Создана директория: %s", self.run_dir)

    def _create_subdirectories(self) -> None:
        """Создает все необходимые поддиректории."""
        subdirs = [
            "input",
            "profilers",
            "test_results",
            "metrics",
            "visualizations",
            "logs",
            "tmp",
        ]

        for subdir in subdirs:
            full_path = self.run_dir / subdir
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug("📂 Создана поддиректория: %s", full_path)

    def _init_session(self) -> None:
        """Инициализирует сессию - создает базовые метаданные."""
        system_info = self._collect_system_info()
        session_info = {
            "session_id": self.run_id,
            "created_at": datetime.now().isoformat(),
            "run_dir": str(self.run_dir.absolute()),
            "artifact_manager_version": "1.4.1",
            "system_info": system_info,
        }

        self.save_json("session_info.json", session_info, root_dir=True)
        logger.info("📝 Инициализирована сессия: %s", self.run_id)

    def _collect_system_info(self) -> Dict[str, Any]:
        """Собирает расширенную информацию о системе для session_info.json."""
        info: Dict[str, Any] = {
            "os": {
                "name": os.name,
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "platform": platform.platform(),
            },
            "python": {
                "version": platform.python_version(),
                "implementation": platform.python_implementation(),
                "compiler": platform.python_compiler(),
                "executable": sys.executable,
            },
            "host": {
                "hostname": socket.gethostname(),
                "cpu_count": os.cpu_count(),
            },
        }

        try:
            import getpass

            info["host"]["username"] = getpass.getuser()
        except Exception:
            info["host"]["username"] = "unknown"

        try:
            import psutil

            virtual_memory = psutil.virtual_memory()
            info["host"]["memory"] = {
                "total_bytes": virtual_memory.total,
                "available_bytes": virtual_memory.available,
            }

            cpu_freq = psutil.cpu_freq()
            if cpu_freq is not None:
                info["host"]["cpu_frequency_mhz"] = {
                    "current": cpu_freq.current,
                    "min": cpu_freq.min,
                    "max": cpu_freq.max,
                }
        except Exception:
            info["host"]["psutil"] = "not_available"

        return info

    def get_path(self, filename: str, subdir: Optional[str] = None, root_dir: bool = False) -> Path:
        """Возвращает полный путь к файлу."""
        safe_filename = self._sanitize_name(filename)

        if root_dir:
            return self.run_dir / safe_filename

        if subdir:
            return self.run_dir / subdir / safe_filename

        return self.run_dir / safe_filename

    def save_json(
        self,
        filename: str,
        data: Dict[str, Any],
        subdir: Optional[str] = None,
        root_dir: bool = False,
        indent: int = 2,
    ) -> Path:
        """Сохраняет данные в JSON файл."""
        filepath = self.get_path(filename, subdir, root_dir)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)

        logger.debug("💾 Сохранен JSON: %s", filepath)
        return filepath

    def save_text(self, filename: str, content: str, subdir: Optional[str] = None) -> Path:
        """Сохраняет текстовый файл."""
        filepath = self.get_path(filename, subdir)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug("📝 Сохранен текстовый файл: %s", filepath)
        return filepath

    def save_binary(self, filename: str, data: bytes, subdir: Optional[str] = None) -> Path:
        """Сохраняет бинарный файл."""
        filepath = self.get_path(filename, subdir)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "wb") as f:
            f.write(data)

        logger.debug("🔧 Сохранен бинарный файл: %s", filepath)
        return filepath

    def save_file(
        self,
        source_path: Union[str, Path],
        dest_filename: Optional[str] = None,
        subdir: Optional[str] = None,
    ) -> Path:
        """Копирует существующий файл в директорию артефактов."""
        source = Path(source_path)

        if dest_filename is None:
            dest_filename = source.name

        dest_path = self.get_path(dest_filename, subdir)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source, dest_path)
        logger.debug("📋 Скопирован файл: %s -> %s", source, dest_path)
        return dest_path

    def save_metrics(self, metrics: Dict[str, Any], test_name: str, step_name: str, iteration: int = 1, repeat_count: Optional[int] = None) -> Path:
        """Сохраняет метрики профилирования."""
        safe_test_name = self._sanitize_name(test_name)
        safe_step_name = self._sanitize_name(step_name)
        if repeat_count is not None:
            filename = f"{safe_test_name}_{safe_step_name}_rep{repeat_count}_metrics.json"
        else:
            filename = f"{safe_test_name}_{safe_step_name}_iter{iteration}_metrics.json"
        subdir = f"metrics/{safe_test_name}"

        metadata = {
            "test_name": safe_test_name,
            "step_name": safe_step_name,
            "repeat_count": repeat_count,
            "saved_at": datetime.now().isoformat(),
        }
        if repeat_count is None:
            metadata["iteration"] = iteration

        enhanced_metrics = {
            **metrics,
            "_metadata": metadata,
        }

        return self.save_json(filename, enhanced_metrics, subdir)

    def save_test_input(self, test_data: Dict[str, Any], test_name: str) -> Path:
        """Сохраняет входные данные теста."""
        safe_test_name = self._sanitize_name(test_name)
        filename = f"{safe_test_name}_input.json"
        return self.save_json(filename, test_data, subdir="input")

    def save_test_results(self, results: Dict[str, Any], test_name: str) -> Path:
        """Сохраняет результаты вычислений Демпстера-Шейфера."""
        safe_test_name = self._sanitize_name(test_name)
        filename = f"{safe_test_name}_results.json"
        return self.save_json(filename, results, subdir="test_results")

    def save_profiler_data(
        self,
        profiler_name: str,
        data: Dict[str, Any],
        test_name: str,
        step_name: str,
        iteration: int = 1,
        repeat_count: Optional[int] = None,
    ) -> Path:
        """Сохраняет данные профилировщика."""
        safe_profiler_name = self._sanitize_name(profiler_name)
        safe_test_name = self._sanitize_name(test_name)
        safe_step_name = self._sanitize_name(step_name)

        if repeat_count is not None:
            filename = f"{safe_test_name}_{safe_step_name}_rep{repeat_count}_{safe_profiler_name}.json"
        else:
            filename = f"{safe_test_name}_{safe_step_name}_iter{iteration}_{safe_profiler_name}.json"
        subdir = f"profilers/{safe_profiler_name}/{safe_test_name}"

        metadata = {
            "profiler": safe_profiler_name,
            "test_name": safe_test_name,
            "step_name": safe_step_name,
            "repeat_count": repeat_count,
            "saved_at": datetime.now().isoformat(),
        }
        if repeat_count is None:
            metadata["iteration"] = iteration

        enhanced_data = {
            **data,
            "_metadata": metadata,
        }

        return self.save_json(filename, enhanced_data, subdir)

    def save_html_report(self, html_content: str, test_name: str, step_name: str, profiler_name: str) -> Path:
        """Сохраняет HTML отчет профилировщика."""
        safe_profiler_name = self._sanitize_name(profiler_name)
        safe_test_name = self._sanitize_name(test_name)
        safe_step_name = self._sanitize_name(step_name)

        filename = f"{safe_test_name}_{safe_step_name}_{safe_profiler_name}.html"
        subdir = f"profilers/{safe_profiler_name}/{safe_test_name}/reports"
        return self.save_text(filename, html_content, subdir)

    def save_run_parameters(self, parameters: Dict[str, Any]) -> Path:
        """Сохраняет параметры запуска отдельным файлом в корне запуска."""
        payload = {
            "saved_at": datetime.now().isoformat(),
            "session_id": self.run_id,
            "adapter": self.adapter_name,
            "parameters": parameters,
        }
        return self.save_json("run_parameters.json", payload, root_dir=True)

    def get_session_info(self) -> Dict[str, Any]:
        """Возвращает информацию о текущей сессии."""
        session_file = self.run_dir / "session_info.json"
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def update_metadata(self, metadata: Dict[str, Any]) -> Path:
        """Обновляет метаданные сессии."""
        current_info = self.get_session_info()
        current_info.update(metadata)
        current_info["updated_at"] = datetime.now().isoformat()
        return self.save_json("session_info.json", current_info, root_dir=True)

    def list_files(self, pattern: str = "**/*") -> List[Path]:
        """Возвращает список всех файлов в директории артефактов."""
        return list(self.run_dir.glob(pattern))

    def get_summary(self) -> Dict[str, Any]:
        """Возвращает сводку о сохраненных артефактах."""
        files = self.list_files("**/*")
        only_files = [p for p in files if p.is_file()]

        summary = {
            "session_id": self.run_id,
            "total_files": len(only_files),
            "by_type": {},
            "by_directory": {},
            "total_size_bytes": 0,
        }

        for filepath in only_files:
            ext = filepath.suffix.lower()
            if ext not in summary["by_type"]:
                summary["by_type"][ext] = 0
            summary["by_type"][ext] += 1

            rel_path = filepath.relative_to(self.run_dir)
            parent_dir = str(rel_path.parent)
            if parent_dir not in summary["by_directory"]:
                summary["by_directory"][parent_dir] = 0
            summary["by_directory"][parent_dir] += 1

            summary["total_size_bytes"] += filepath.stat().st_size

        return summary

    def cleanup_temp_files(self) -> None:
        """Очищает временные файлы."""
        tmp_dir = self.run_dir / "tmp"
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)
            tmp_dir.mkdir(exist_ok=True)
            logger.info("🧹 Очищены временные файлы")

    def sanitize_saved_artifacts(self) -> Dict[str, int]:
        """Пост-обработка: санитизирует пути во всех сохраненных текстовых артефактах.

        Выполняется отдельным этапом после окончания бенчмарка,
        чтобы не увеличивать накладные расходы на каждом шаге профилирования.
        """
        stats = {
            "json_files_checked": 0,
            "json_files_updated": 0,
            "text_files_checked": 0,
            "text_files_updated": 0,
            "errors": 0,
        }

        text_exts = {".txt", ".log", ".html", ".htm", ".stderr", ".stdout"}

        for file_path in self.run_dir.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            try:
                if suffix == ".json":
                    stats["json_files_checked"] += 1
                    original_text = file_path.read_text(encoding="utf-8")
                    data = json.loads(original_text)
                    sanitized = sanitize_payload_paths(data)
                    if sanitized != data:
                        file_path.write_text(
                            json.dumps(sanitized, indent=2, ensure_ascii=False),
                            encoding="utf-8",
                        )
                        stats["json_files_updated"] += 1
                    continue

                name_lower = file_path.name.lower()
                is_text_sidecar = name_lower.endswith(".stdout.txt") or name_lower.endswith(".stderr.txt")
                if suffix in text_exts or is_text_sidecar:
                    stats["text_files_checked"] += 1
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    sanitized = sanitize_text_paths(content)
                    if sanitized != content:
                        file_path.write_text(sanitized, encoding="utf-8")
                        stats["text_files_updated"] += 1
            except Exception:
                stats["errors"] += 1

        logger.info("🛡️ Пост-санитизация артефактов завершена: %s", stats)
        return stats

    def archive(self, output_path: Optional[str] = None) -> Path:
        """Создает архив со всеми артефактами."""
        if output_path is None:
            output_path = f"{self.adapter_name}_{self.run_id}.zip"

        archive_path = shutil.make_archive(
            str(Path(str(output_path)).with_suffix("")),
            "zip",
            str(self.run_dir),
        )

        logger.info("📦 Создан архив: %s", archive_path)
        return Path(archive_path)

    def __repr__(self) -> str:
        summary = self.get_summary()
        return (
            f"ArtifactManager(adapter='{self.adapter_name}', run_id='{self.run_id}', "
            f"files={summary['total_files']}, "
            f"size={summary['total_size_bytes'] / 1024:.1f} KB)"
        )


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С АРТЕФАКТАМИ
# ============================================================================


def create_artifact_manager(
    adapter_name: str = "our",
    run_id: Optional[str] = None,
    base_dir: str = "results/profiling",
    overwrite: bool = False,
) -> ArtifactManager:
    """Фабричная функция для создания ArtifactManager."""
    return ArtifactManager(
        base_dir=base_dir,
        adapter_name=adapter_name,
        run_id=run_id,
        overwrite=overwrite,
    )


def get_latest_artifact_dir(base_dir: str = "results/profiling") -> Optional[Path]:
    """Находит последнюю директорию с артефактами."""
    base_path = Path(base_dir)
    if not base_path.exists():
        return None

    dirs = []
    for library_dir in base_path.iterdir():
        if not library_dir.is_dir() or library_dir.name == "__pycache__":
            continue

        for run_dir in library_dir.iterdir():
            if not run_dir.is_dir() or run_dir.name == "__pycache__":
                continue
            try:
                dt = datetime.strptime(run_dir.name, "%Y%m%d_%H%M%S")
            except ValueError:
                dt = datetime.fromtimestamp(run_dir.stat().st_mtime)
            dirs.append((dt, run_dir))

    if not dirs:
        return None

    dirs.sort(key=lambda x: x[0], reverse=True)
    return dirs[0][1]
