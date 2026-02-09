# src/profiling/collectors/scalene_collector.py
"""
ScaleneCollector - запуск scalene для сбора сырых профилей CPU/Memory по строкам.
Работает через CLI scalene, сохраняет HTML отчет.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class ScaleneCollector:
    """
    Сборщик сырых профилей через scalene CLI.
    Подходит для Windows, если scalene установлен и доступен в PATH.
    """

    def __init__(self,
                 output_dir: Path,
                 enabled: bool = True,
                 include_paths: Optional[List[Path]] = None):
        self.output_dir = Path(output_dir)
        self.enabled = enabled
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.include_paths = [Path(path).resolve() for path in include_paths or []]

    def is_available(self) -> bool:
        """Проверяет доступность scalene в PATH."""
        return shutil.which("scalene") is not None

    def profile_script(self,
                       script_path: Path,
                       script_args: Optional[List[str]] = None,
                       test_name: str = "test",
                       step_name: str = "step",
                       iteration: int = 1) -> Dict[str, Any]:
        """
        Запускает scalene для отдельного python-скрипта.
        Возвращает информацию о сохраненном HTML-отчете.
        """
        info: Dict[str, Any] = {
            "enabled": self.enabled,
            "available": self.is_available(),
            "html_path": None,
            "error": None
        }

        if not self.enabled:
            return info

        if not info["available"]:
            info["error"] = "scalene not available in PATH"
            return info

        timestamp = datetime.now().strftime("%H%M%S")
        html_filename = f"{test_name}_{step_name}_iter{iteration}_{timestamp}.html"
        html_path = (self.output_dir / html_filename).resolve()
        info["html_path"] = str(html_path)

        args = [
            "scalene",
            "--cpu",
            "--memory",
            "--profile-all",
            "--html",
            "--no-browser",
            "--outfile",
            str(html_path),
        ]
        profile_just = self._build_profile_just_regex()
        if profile_just:
            args.extend(["--profile-just", profile_just])
        if script_args:
            args.extend(script_args)
        args.append(str(script_path))

        try:
            subprocess.run(args, check=True, capture_output=True, text=True)
        except Exception as exc:  # noqa: BLE001 - сохраняем ошибку профилирования
            info["error"] = str(exc)

        return info

    def profile_step(self,
                     input_path: Path,
                     adapter_name: str,
                     step_name: str,
                     iteration: int,
                     test_name: str,
                     alpha: float = 0.1) -> Dict[str, Any]:
        """
        Запускает scalene для одного шага ДШ через временный скрипт.
        """
        tmp_dir = self.output_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        script_path = tmp_dir / f"scalene_{test_name}_{step_name}_iter{iteration}_{timestamp}.py"

        script_path.write_text(
            self._build_step_script(),
            encoding="utf-8"
        )

        try:
            return self.profile_script(
                script_path=script_path,
                script_args=[
                    "--adapter", adapter_name,
                    "--step", step_name,
                    "--input", str(input_path),
                    "--alpha", str(alpha),
                ],
                test_name=test_name,
                step_name=step_name,
                iteration=iteration
            )
        finally:
            if script_path.exists():
                script_path.unlink()

    def _build_step_script(self) -> str:
        """Генерирует скрипт для выполнения одного шага ДШ."""
        return textwrap.dedent(
            """
            import argparse
            import json
            import shutil
            import sys
            import tempfile
            from pathlib import Path

            project_root = Path.cwd()
            sys.path.insert(0, str(project_root))

            from src.runners.universal_runner import UniversalBenchmarkRunner


            def parse_args():
                parser = argparse.ArgumentParser(description="Run a single D-S step for scalene profiling.")
                parser.add_argument("--adapter", default="our", help="Adapter name (default: our)")
                parser.add_argument("--step", required=True, help="Step name")
                parser.add_argument("--input", required=True, help="Path to DASS test JSON")
                parser.add_argument("--alpha", type=float, default=0.1, help="Discounting alpha for step3")
                return parser.parse_args()


            def load_adapter(adapter_name: str):
                if adapter_name == "our":
                    from src.adapters.our_adapter import OurImplementationAdapter
                    return OurImplementationAdapter()
                raise ValueError(f"Unsupported adapter: {adapter_name}")


            def run_step(runner, adapter, step_name: str, data, alpha: float) -> None:
                if step_name == "step1_original":
                    runner._execute_step1(data)
                    return
                if step_name == "step2_dempster":
                    runner._execute_step2(data)
                    return
                if step_name == "step3_discount_dempster":
                    sources_count = adapter.get_sources_count(data)
                    alphas = [alpha] * sources_count
                    runner._execute_step3(data, alphas)
                    return
                if step_name == "step4_yager":
                    runner._execute_step4(data)
                    return
                raise ValueError(f"Unknown step: {step_name}")


            def main():
                args = parse_args()
                input_path = Path(args.input)
                test_data = json.loads(input_path.read_text(encoding="utf-8"))

                adapter = load_adapter(args.adapter)
                loaded_data = adapter.load_from_dass(test_data)

                temp_dir = tempfile.mkdtemp(prefix="scalene_runner_")
                try:
                    runner = UniversalBenchmarkRunner(adapter, results_dir=temp_dir)
                    run_step(runner, adapter, args.step, loaded_data, args.alpha)
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)


            if __name__ == "__main__":
                main()
            """
        )

    def _build_profile_just_regex(self) -> Optional[str]:
        if not self.include_paths:
            return None
        cwd = Path.cwd().resolve()
        patterns: List[str] = []
        for path in self.include_paths:
            raw_path = str(path)
            posix_path = path.as_posix()
            patterns.append(re.escape(raw_path))
            if posix_path != raw_path:
                patterns.append(re.escape(posix_path))

            parts = [re.escape(part) for part in path.parts if part]
            if parts:
                patterns.append(r"[\\/]+".join(parts))

            try:
                relative_path = path.resolve().relative_to(cwd)
            except ValueError:
                relative_path = None

            if relative_path:
                relative_raw = str(relative_path)
                relative_posix = relative_path.as_posix()
                patterns.append(re.escape(relative_raw))
                if relative_posix != relative_raw:
                    patterns.append(re.escape(relative_posix))
                relative_parts = [re.escape(part) for part in relative_path.parts if part]
                if relative_parts:
                    patterns.append(r"[\\/]+".join(relative_parts))

            patterns.append(re.escape(path.name))
        return "(" + "|".join(patterns) + ")"

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус доступности scalene."""
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "output_dir": str(self.output_dir),
            "include_paths": [str(path) for path in self.include_paths]
        }
