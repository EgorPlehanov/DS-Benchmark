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

    @staticmethod
    def _build_scalene_command(
        script_path: Path,
        profile_json_path: Path,
        profile_only_filters: List[str],
        script_args: Optional[List[str]]
    ) -> List[str]:
        """Собирает команду запуска scalene run с валидными флагами v2.x."""
        args = [
            "scalene",
            "run",
            "-o",
            str(profile_json_path),
            "--memory",
            "--profile-all",
        ]

        if profile_only_filters:
            args.extend(["--profile-only", ",".join(profile_only_filters)])

        args.append(str(script_path))
        if script_args:
            args.extend(script_args)

        return args

    @staticmethod
    def _build_scalene_view_command(profile_json_path: Path) -> List[str]:
        """Собирает команду scalene view для генерации HTML отчета без браузера."""
        return [
            "scalene",
            "view",
            "--html",
            str(profile_json_path),
        ]

    def _capture_scalene_profile_json(self, test_output_dir: Path, profile_json_path: Path) -> Optional[str]:
        """Сохраняет raw profile JSON как артефакт конкретного шага (новое и legacy имя)."""
        if profile_json_path.exists():
            return str(profile_json_path.resolve())

        raw_candidates = [
            test_output_dir / "scalene-profile.json",
            test_output_dir / "profile.json",
        ]

        raw_profile_path = next((path for path in raw_candidates if path.exists()), None)
        if raw_profile_path is None:
            return None

        raw_profile_path.replace(profile_json_path)
        return str(profile_json_path.resolve())

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
            profile_json_filename = f"{test_name}_{step_name}_rep{repeat_count}_{timestamp}.profile.json"
        else:
            profile_json_filename = f"{test_name}_{step_name}_iter{iteration}_{timestamp}.profile.json"
        profile_json_path = (test_output_dir / profile_json_filename).resolve()
        html_path = profile_json_path.with_suffix('.html')
        info["html_path"] = str(html_path)

        profile_only_filters = self._get_profile_only_filters()
        if profile_only_filters:
            info["profile_only"] = profile_only_filters

        args = self._build_scalene_command(
            script_path=script_path,
            profile_json_path=profile_json_path,
            profile_only_filters=profile_only_filters,
            script_args=script_args,
        )

        env = dict(os.environ)
        env.setdefault("PYTHONIOENCODING", "utf-8")

        try:
            completed = subprocess.run(
                args,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
                cwd=str(test_output_dir),
            )
            if completed.stdout:
                (test_output_dir / f"{profile_json_filename}.stdout.txt").write_text(
                    completed.stdout,
                    encoding="utf-8"
                )
            if completed.stderr:
                (test_output_dir / f"{profile_json_filename}.stderr.txt").write_text(
                    completed.stderr,
                    encoding="utf-8"
                )
        except Exception as exc:  # noqa: BLE001 - сохраняем ошибку профилирования
            if isinstance(exc, subprocess.CalledProcessError):
                if exc.stdout:
                    (test_output_dir / f"{profile_json_filename}.stdout.txt").write_text(
                        exc.stdout,
                        encoding="utf-8"
                    )
                if exc.stderr:
                    (test_output_dir / f"{profile_json_filename}.stderr.txt").write_text(
                        exc.stderr,
                        encoding="utf-8"
                    )
            info["error"] = str(exc)
        finally:
            captured_profile_path = self._capture_scalene_profile_json(test_output_dir, profile_json_path)
            if captured_profile_path:
                info["profile_json_path"] = captured_profile_path
                view_args = self._build_scalene_view_command(Path(captured_profile_path))
                try:
                    view_completed = subprocess.run(
                        view_args,
                        check=True,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        env=env,
                        cwd=str(test_output_dir),
                    )
                    if view_completed.stdout:
                        (test_output_dir / f"{profile_json_filename}.view.stdout.txt").write_text(
                            view_completed.stdout,
                            encoding="utf-8"
                        )
                    if view_completed.stderr:
                        (test_output_dir / f"{profile_json_filename}.view.stderr.txt").write_text(
                            view_completed.stderr,
                            encoding="utf-8"
                        )

                    default_html = test_output_dir / "scalene-profile.html"
                    if default_html.exists():
                        default_html.replace(html_path)
                    elif not html_path.exists():
                        info["html_path"] = None
                except Exception as view_exc:  # noqa: BLE001 - не прерываем JSON-профиль
                    info["html_path"] = None
                    info["view_error"] = str(view_exc)
            else:
                info["html_path"] = None

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
            from src.adapters.factory import create_adapter


            def parse_args():
                parser = argparse.ArgumentParser(description="Run a single D-S step for scalene profiling.")
                parser.add_argument("--adapter", default="our", help="Adapter name (default: our)")
                parser.add_argument("--step", required=True, help="Step name")
                parser.add_argument("--input", required=True, help="Path to DASS test JSON")
                parser.add_argument("--alpha", type=float, default=0.1, help="Discounting alpha for step3")
                parser.add_argument("--repeat", type=int, default=1, help="Repeat count to ensure enough profiling samples")
                return parser.parse_args()


            def load_adapter(adapter_name: str):
                return create_adapter(adapter_name)


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
