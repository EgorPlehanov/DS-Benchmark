# src/profiling/artifacts/structure.py
"""
Утилиты для работы со структурой директорий артефактов.
"""

from pathlib import Path
from typing import Dict, Any, List
import json


def create_artifact_structure(base_path: Path) -> Dict[str, Path]:
    """
    Создает стандартную структуру директорий для артефактов.
    
    Args:
        base_path: Базовый путь
        
    Returns:
        Dict[str, Path]: Словарь с путями к директориям
    """
    structure = {
        "root": base_path,
        "input": base_path / "input",
        "profilers": base_path / "profilers",
        "test_results": base_path / "test_results",
        "metrics": base_path / "metrics",
        "visualizations": base_path / "visualizations",
        "logs": base_path / "logs",
        "tmp": base_path / "tmp"
    }
    
    # Создаем все директории
    for dir_path in structure.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return structure


def validate_artifact_structure(base_path: Path) -> List[str]:
    """
    Проверяет структуру директорий артефактов.
    
    Args:
        base_path: Базовый путь
        
    Returns:
        List[str]: Список проблем или пустой список если все OK
    """
    problems = []
    
    required_dirs = [
        "input",
        "profilers",
        "test_results",
        "metrics",
        "visualizations",
        "logs",
        "tmp"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            problems.append(f"Отсутствует директория: {dir_path}")
        elif not dir_path.is_dir():
            problems.append(f"Не является директорией: {dir_path}")
    
    # Проверяем session_info.json
    session_file = base_path / "session_info.json"
    if not session_file.exists():
        problems.append(f"Отсутствует session_info.json")
    else:
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            required_session_keys = ["session_id", "created_at", "adapter", "run_dir"]
            for key in required_session_keys:
                if key not in data:
                    problems.append(f"session_info.json не содержит {key}")
        except json.JSONDecodeError:
            problems.append("session_info.json содержит некорректный JSON")
    
    return problems


def get_artifact_summary(base_path: Path) -> Dict[str, Any]:
    """
    Возвращает сводку о содержимом директории артефактов.
    
    Args:
        base_path: Путь к директории артефактов
        
    Returns:
        Dict[str, Any]: Сводка
    """
    if not base_path.exists():
        return {"error": "Директория не существует"}
    
    summary = {
        "path": str(base_path),
        "total_files": 0,
        "total_dirs": 0,
        "file_types": {},
        "largest_files": [],
        "recent_files": []
    }
    
    # Собираем информацию о файлах
    files_info = []
    for file_path in base_path.rglob("*"):
        if file_path.is_file():
            stat = file_path.stat()
            files_info.append({
                "path": str(file_path.relative_to(base_path)),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "extension": file_path.suffix.lower()
            })
    
    summary["total_files"] = len(files_info)
    
    # Группируем по типам файлов
    for file_info in files_info:
        ext = file_info["extension"] or "no_extension"
        if ext not in summary["file_types"]:
            summary["file_types"][ext] = 0
        summary["file_types"][ext] += 1
    
    # Топ-5 самых больших файлов
    files_info.sort(key=lambda x: x["size"], reverse=True)
    summary["largest_files"] = files_info[:5]
    
    # Топ-5 последних измененных файлов
    files_info.sort(key=lambda x: x["modified"], reverse=True)
    summary["recent_files"] = files_info[:5]
    
    # Считаем директории
    dir_count = sum(1 for _ in base_path.rglob("*") if _.is_dir())
    summary["total_dirs"] = dir_count
    
    return summary
