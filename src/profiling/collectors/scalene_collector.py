# src/profiling/collectors/scalene_collector.py
"""
ScaleneCollector - запуск scalene для сбора сырых профилей CPU/Memory по строкам.
Работает через CLI scalene, сохраняет HTML отчет.
"""

from __future__ import annotations

import os
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
                 profile_only_dir: str = "None"):
        self.output_dir = Path(output_dir)
        self.enabled = enabled
        self.profile_only_dir = Path(profile_only_dir)
        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_name(value: str) -> str:
        """Нормализует имя для использования в пути."""
        normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value).strip())
        return normalized.strip("._") or "unknown"

    def _get_test_output_dir(self, test_name: str) -> Path:
        """Возвращает директорию для конкретного теста."""
        test_dir = self.output_dir / self._sanitize_name(test_name)
        test_dir.mkdir(parents=True, exist_ok=True)
        return test_dir

    def is_available(self) -> bool:
        """Проверяет доступность scalene в PATH."""
        return shutil.which("scalene") is not None

    def _get_profile_only_filters(self) -> List[str]:
        """Возвращает фильтры для --profile-only из python-файлов папки и подпапок."""
        if not self.profile_only_dir.exists():
            return []

        python_files = sorted(self.profile_only_dir.rglob("*.py"))
        if not python_files:
            return []

        # Используем полные пути без дубликатов, чтобы избежать лишнего шума в profile_only.
        return [str(py_file.resolve().as_posix()) for py_file in python_files]

    def profile_script(self,
                       script_path: Path,
                       script_args: Optional[List[str]] = None,
                       test_name: str = "test",
                       step_name: str = "step",
                       iteration: int = 1,
                       repeat_count: Optional[int] = None) -> Dict[str, Any]:
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
        test_output_dir = self._get_test_output_dir(test_name)
        if repeat_count is not None:
            html_filename = f"{test_name}_{step_name}_rep{repeat_count}_{timestamp}.html"
        else:
            html_filename = f"{test_name}_{step_name}_iter{iteration}_{timestamp}.html"
        html_path = (test_output_dir / html_filename).resolve()
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

        profile_only_filters = self._get_profile_only_filters()
        if profile_only_filters:
            args.extend(["--profile-only", ",".join(profile_only_filters)])
            info["profile_only"] = profile_only_filters

        args.append(str(script_path))
        if script_args:
            args.extend(script_args)

        try:
            env = dict(os.environ)
            env.setdefault("PYTHONIOENCODING", "utf-8")
            completed = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env
            )
            if completed.stdout:
                (test_output_dir / f"{html_filename}.stdout.txt").write_text(
                    completed.stdout,
                    encoding="utf-8"
                )
            if completed.stderr:
                (test_output_dir / f"{html_filename}.stderr.txt").write_text(
                    completed.stderr,
                    encoding="utf-8"
                )
        except Exception as exc:  # noqa: BLE001 - сохраняем ошибку профилирования
            if isinstance(exc, subprocess.CalledProcessError):
                if exc.stdout:
                    (test_output_dir / f"{html_filename}.stdout.txt").write_text(
                        exc.stdout,
                        encoding="utf-8"
                    )
                if exc.stderr:
                    (test_output_dir / f"{html_filename}.stderr.txt").write_text(
                        exc.stderr,
                        encoding="utf-8"
                    )
            info["error"] = str(exc)

        return info


    def profile_step(self,
                     input_path: Path,
                     adapter_name: str,
                     step_name: str,
                     iteration: int,
                     test_name: str,
                     alpha: float = 0.1,
                     repeat: int = 1) -> Dict[str, Any]:
        """
        Запускает scalene для одного шага ДШ через временный скрипт.
        """
        tmp_dir = self.output_dir / "tmp"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        script_path = tmp_dir / f"scalene_{test_name}_{step_name}_rep{repeat}_{timestamp}.py"

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
                    "--repeat", str(repeat),
                ],
                test_name=test_name,
                step_name=step_name,
                iteration=iteration,
                repeat_count=repeat
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
                parser.add_argument("--repeat", type=int, default=1, help="Repeat count to ensure enough profiling samples")
                return parser.parse_args()


            def load_adapter(adapter_name: str):
                if adapter_name in {"our", "ourimplementation"}:
                    from src.adapters.our_adapter import OurImplementationAdapter
                    return OurImplementationAdapter()
                raise ValueError(f"Unsupported adapter: {adapter_name}")


            def run_step1(runner, data) -> None:
                runner._execute_step1(data)


            def run_step2(runner, data) -> None:
                runner._execute_step2(data)


            def run_step3(runner, adapter, data, alpha: float) -> None:
                sources_count = adapter.get_sources_count(data)
                alphas = [alpha] * sources_count
                runner._execute_step3(data, alphas)


            def run_step4(runner, data) -> None:
                runner._execute_step4(data)


            def run_step(runner, adapter, step_name: str, data, alpha: float) -> None:
                if step_name == "step1_original":
                    run_step1(runner, data)
                    return
                if step_name == "step2_dempster":
                    run_step2(runner, data)
                    return
                if step_name == "step3_discount_dempster":
                    run_step3(runner, adapter, data, alpha)
                    return
                if step_name == "step4_yager":
                    run_step4(runner, data)
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
                    for _ in range(max(1, args.repeat)):
                        run_step(runner, adapter, args.step, loaded_data, args.alpha)
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)


            if __name__ == "__main__":
                main()
            """
        )

    def get_status(self) -> Dict[str, Any]:
        """Возвращает статус доступности scalene."""
        return {
            "enabled": self.enabled,
            "available": self.is_available(),
            "output_dir": str(self.output_dir)
        }
