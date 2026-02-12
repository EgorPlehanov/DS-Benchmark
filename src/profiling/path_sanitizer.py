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

    def _is_url_context(match_start: int) -> bool:
        """Проверяет, находится ли совпадение внутри URL-токена."""
        separators = [
            text.rfind(" ", 0, match_start),
            text.rfind("\n", 0, match_start),
            text.rfind("\t", 0, match_start),
            text.rfind('"', 0, match_start),
            text.rfind("'", 0, match_start),
            text.rfind("(", 0, match_start),
        ]
        token_start = max(separators) + 1
        token_prefix = text[token_start:match_start]
        return "://" in token_prefix

    def _looks_like_html_or_mime_fragment(candidate: str, match_start: int) -> bool:
        """Отсекает ложные срабатывания по HTML/MIME фрагментам (`</title>`, `image/x-icon`)."""
        if not candidate.startswith("/"):
            return False

        # CSS/JS комментарии и служебные маркеры не являются файловыми путями.
        if candidate.startswith("/*") or candidate.startswith("//"):
            return True

        prev_char = text[match_start - 1] if match_start > 0 else ""

        # HTML теги: <.../tag...> или </tag>
        if prev_char == "<":
            return True

        # MIME-подобные суффиксы вида image/x-icon
        # (один сегмент после '/', перед ним буквенно-цифровой тип)
        if candidate.count("/") == 1 and prev_char and re.match(r"[A-Za-z0-9_.+-]", prev_char):
            return True

        return False

    def _replace(match: re.Match[str]) -> str:
        candidate = match.group(0)
        start = match.start()

        if _is_url_context(start):
            return candidate

        if _looks_like_html_or_mime_fragment(candidate, start):
            return candidate

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
