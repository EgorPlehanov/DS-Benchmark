# src/profiling/core/line_profiler.py
"""
Профилировщик по строкам на основе sys.settrace.
Собирает время выполнения по строкам кода.
Работает без внешних зависимостей и совместим с Win32.
"""

import os
import sys
import time
from typing import Dict, Any, Optional, List, Tuple

from .base_profiler import BaseProfiler


class LineProfiler(BaseProfiler):
    """Профилировщик времени выполнения по строкам."""

    def __init__(
        self,
        name: str = "line_profiler",
        enabled: bool = True,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        limit: int = 50,
        line_limit_per_file: int = 50,
    ):
        super().__init__(name, enabled)
        self.include_paths = self._normalize_paths(include_paths)
        self.exclude_paths = self._normalize_paths(exclude_paths)
        self.limit = limit
        self.line_limit_per_file = line_limit_per_file
        self._line_stats: Dict[str, Dict[str, Any]] = {}
        self._frame_state: Dict[int, Dict[str, Any]] = {}
        self._previous_trace = None

    def _normalize_paths(self, paths: Optional[List[str]]) -> Optional[List[str]]:
        if not paths:
            return None
        normalized = []
        for path in paths:
            normalized.append(os.path.abspath(path))
        return normalized

    def _should_trace(self, filename: str) -> bool:
        if not filename:
            return False
        abs_path = os.path.abspath(filename)
        if self.include_paths and not any(abs_path.startswith(p) for p in self.include_paths):
            return False
        if self.exclude_paths and any(abs_path.startswith(p) for p in self.exclude_paths):
            return False
        return True

    def _record_line(self, filename: str, line_no: int, duration: float) -> None:
        if line_no <= 0:
            return
        file_data = self._line_stats.setdefault(
            filename,
            {"total_time": 0.0, "lines": {}},
        )
        line_stats = file_data["lines"].setdefault(
            line_no,
            {"hits": 0, "total_time": 0.0},
        )
        line_stats["hits"] += 1
        line_stats["total_time"] += duration
        file_data["total_time"] += duration

    def _trace(self, frame, event, arg):
        filename = frame.f_code.co_filename
        if not self._should_trace(filename):
            return self._trace

        now = time.perf_counter()
        frame_id = id(frame)
        state = self._frame_state.get(frame_id)

        if event == "call":
            self._frame_state[frame_id] = {
                "last_time": now,
                "last_line": frame.f_lineno,
                "filename": filename,
            }
            return self._trace

        if state is None:
            self._frame_state[frame_id] = {
                "last_time": now,
                "last_line": frame.f_lineno,
                "filename": filename,
            }
            return self._trace

        if event in ("line", "return", "exception"):
            self._record_line(
                state["filename"],
                state["last_line"],
                now - state["last_time"],
            )
            state["last_time"] = now
            state["last_line"] = frame.f_lineno

            if event == "return":
                self._frame_state.pop(frame_id, None)

        return self._trace

    def _on_start(self) -> None:
        self._line_stats = {}
        self._frame_state = {}
        self._previous_trace = sys.gettrace()
        sys.settrace(self._trace)

    def _on_stop(self) -> Dict[str, Any]:
        sys.settrace(self._previous_trace)
        self._previous_trace = None
        return self._build_report()

    def _build_report(self) -> Dict[str, Any]:
        file_reports = {}
        top_lines: List[Dict[str, Any]] = []

        for filename, data in self._line_stats.items():
            lines_data = data["lines"]
            line_texts = self._load_line_texts(filename, lines_data.keys())
            sorted_lines = sorted(
                lines_data.items(),
                key=lambda item: item[1]["total_time"],
                reverse=True,
            )

            file_lines_report = []
            for line_no, line_stat in sorted_lines[: self.line_limit_per_file]:
                avg_time = (
                    line_stat["total_time"] / line_stat["hits"]
                    if line_stat["hits"]
                    else 0.0
                )
                line_entry = {
                    "line": line_no,
                    "hits": line_stat["hits"],
                    "total_time": line_stat["total_time"],
                    "avg_time": avg_time,
                    "code": line_texts.get(line_no, "").rstrip(),
                }
                file_lines_report.append(line_entry)

                top_lines.append(
                    {
                        "filename": filename,
                        "line": line_no,
                        "hits": line_stat["hits"],
                        "total_time": line_stat["total_time"],
                        "avg_time": avg_time,
                        "code": line_texts.get(line_no, "").rstrip(),
                    }
                )

            file_reports[filename] = {
                "total_time": data["total_time"],
                "lines": file_lines_report,
            }

        top_lines_sorted = sorted(
            top_lines,
            key=lambda item: item["total_time"],
            reverse=True,
        )

        return {
            "file_stats": file_reports,
            "top_lines": top_lines_sorted[: self.limit],
        }

    def _load_line_texts(self, filename: str, line_numbers) -> Dict[int, str]:
        if not filename or not os.path.exists(filename):
            return {}

        try:
            with open(filename, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except OSError:
            return {}

        line_texts = {}
        for line_no in line_numbers:
            index = line_no - 1
            if 0 <= index < len(lines):
                line_texts[line_no] = lines[index]
        return line_texts
