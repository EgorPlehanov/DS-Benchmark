# src/profiling/collectors/memray_collector.py
"""
MemrayCollector - сбор сырых данных профилирования памяти через memray.
Сохраняет .bin и (опционально) flamegraph HTML.
"""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Iterator, Optional

try:
    import memray
    HAS_MEMRAY = True
except ImportError:
    HAS_MEMRAY = False


class MemrayCollector:
    """
    Сборщик raw-профилей памяти с помощью memray.

    Использование:
        collector = MemrayCollector(output_dir=Path(...))
        with collector.track(test_name, step_name, iteration) as info:
            result = func(...)
        # info содержит пути к .bin и flamegraph (если доступны)
    """

    def __init__(self,
                 output_dir: Path,
                 enabled: bool = True,
                 generate_flamegraph: bool = True):
        self.output_dir = Path(output_dir)
        self.enabled = enabled
        self.generate_flamegraph = generate_flamegraph
        self.available = HAS_MEMRAY

        self.output_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def track(self,
              test_name: str,
              step_name: str,
              iteration: int = 1) -> Iterator[Dict[str, Any]]:
        """
        Контекстный менеджер для трекинга аллокаций memray.
        """
        info: Dict[str, Any] = {
            "enabled": self.enabled,
            "available": self.available,
            "bin_path": None,
            "flamegraph_path": None,
            "error": None
        }

        if not self.enabled or not self.available:
            yield info
            return

        timestamp = datetime.now().strftime("%H%M%S")
        bin_filename = f"{test_name}_{step_name}_iter{iteration}_{timestamp}.bin"
        bin_path = self.output_dir / bin_filename
        info["bin_path"] = str(bin_path)

        try:
            with memray.Tracker(str(bin_path)):
                yield info
        except Exception as exc:  # noqa: BLE001 - сохраняем ошибку профилирования
            info["error"] = str(exc)
            yield info
            return

        if self.generate_flamegraph:
            flamegraph_path = self._generate_flamegraph(bin_path)
            if flamegraph_path:
                info["flamegraph_path"] = str(flamegraph_path)

    def _generate_flamegraph(self, bin_path: Path) -> Optional[Path]:
        """Генерирует flamegraph HTML через memray CLI."""
        try:
            output_path = bin_path.with_suffix(".html")
            command = [
                "memray",
                "flamegraph",
                str(bin_path),
                "-o",
                str(output_path)
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            return output_path
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус доступности memray."""
        return {
            "enabled": self.enabled,
            "available": self.available,
            "output_dir": str(self.output_dir)
        }
