"""Утилиты для нормализации/редакции путей в артефактах."""

from __future__ import annotations

import os
import re
from pathlib import Path, PureWindowsPath, PurePosixPath
from typing import Any


_ABS_PATH_PATTERN = re.compile(r"[A-Za-z]:[\\/][^\s\"'<>|]+|/(?:[^\s\"'<>|]+)")


def sanitize_path_string(value: str) -> str:
    """Преобразует абсолютный путь в относительный к cwd или в `<external_path>`."""
    if not isinstance(value, str) or not value:
        return value

    normalized = value.replace("\\", "/")
    if ":/" not in normalized and not normalized.startswith("/"):
        return value

    cwd_path = Path.cwd().resolve()

    try:
        if re.match(r"^[A-Za-z]:[\\/]", value):
            win_path = PureWindowsPath(value)
            cwd_win = PureWindowsPath(str(cwd_path))
            try:
                return str(win_path.relative_to(cwd_win)).replace("\\", "/")
            except Exception:
                return "<external_path>"

        if normalized.startswith("/"):
            posix_path = Path(PurePosixPath(normalized)).resolve()
            relative = posix_path.relative_to(cwd_path)
            return str(relative).replace("\\", "/")
    except Exception:
        return "<external_path>"

    return "<external_path>"


def sanitize_payload_paths(payload: Any) -> Any:
    """Рекурсивно нормализует пути в структуре dict/list/tuple/str."""
    if isinstance(payload, dict):
        sanitized = {}
        for key, item in payload.items():
            safe_key = sanitize_path_string(key) if isinstance(key, str) else key
            sanitized[safe_key] = sanitize_payload_paths(item)
        return sanitized

    if isinstance(payload, list):
        return [sanitize_payload_paths(item) for item in payload]

    if isinstance(payload, tuple):
        return tuple(sanitize_payload_paths(item) for item in payload)

    if isinstance(payload, str):
        return sanitize_path_string(payload)

    return payload


def sanitize_text_paths(text: str) -> str:
    """Редактирует абсолютные пути в произвольном тексте.

    Если путь внутри текущего проекта, заменяется на относительный.
    Иначе заменяется на `<external_path>`.
    """
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        candidate = match.group(0)
        # Не трогаем URL-подобные значения.
        if candidate.startswith("//") or "//" in candidate[:10]:
            return candidate
        return sanitize_path_string(candidate)

    sanitized = _ABS_PATH_PATTERN.sub(_replace, text)

    # Дополнительно удаляем прямые вхождения cwd (на случай путей с пробелами в HTML/JSON).
    cwd = str(Path.cwd().resolve())
    cwd_posix = Path.cwd().resolve().as_posix()
    for token in {cwd, cwd_posix, cwd.replace("/", "\\")}:
        if token:
            sanitized = sanitized.replace(token, ".")

    # Нормализуем разделители для относительных путей.
    return sanitized.replace(os.sep, "/")
