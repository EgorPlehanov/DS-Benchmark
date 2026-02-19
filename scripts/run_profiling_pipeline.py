#!/usr/bin/env python3
"""Запускает профилирование по всем библиотекам и постпроцессинг результатов."""

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.factory import ADAPTER_REGISTRY


def run_command(cmd: list[str]) -> None:
    print("\n▶️", " ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "on"}:
        return True
    if normalized in {"false", "0", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("Ожидается булево значение: True/False")


def parse_libraries(value: str) -> list[str]:
    libraries = [item.strip() for item in value.split(",") if item.strip()]
    if not libraries:
        raise argparse.ArgumentTypeError("Список библиотек не может быть пустым")

    supported = set(ADAPTER_REGISTRY.keys())
    unknown = [lib for lib in libraries if lib not in supported]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"Неизвестные библиотеки: {', '.join(unknown)}. Доступно: {', '.join(sorted(supported))}"
        )

    return libraries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Запуск профилирования для набора библиотек + постпроцессинг"
    )
    parser.add_argument(
        "--libraries",
        type=parse_libraries,
        default=sorted(ADAPTER_REGISTRY.keys()),
        help="Список библиотек через запятую. По умолчанию: все базовые библиотеки.",
    )
    parser.add_argument("--tests", default="last", help="Параметр --tests для profile_benchmark.py")
    parser.add_argument(
        "--profiling",
        default="full",
        help="Параметр --profiling для profile_benchmark.py (full|off|cpu,memory,...)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Параметр --iterations для profile_benchmark.py",
    )
    parser.add_argument(
        "--output-dir",
        default="results/profiling",
        help="Параметр --output-dir для profile_benchmark.py",
    )
    parser.add_argument(
        "--max-tests",
        type=int,
        default=None,
        help="Параметр --max-tests для profile_benchmark.py",
    )
    parser.add_argument(
        "--sanitize-paths",
        type=parse_bool,
        default=True,
        help="Параметр --sanitize-paths для profile_benchmark.py",
    )
    parser.add_argument(
        "--pause-seconds",
        type=int,
        default=60,
        help="Пауза между библиотеками в секундах (по умолчанию: 60)",
    )
    parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Пропустить compare_profiling_results.py",
    )
    parser.add_argument(
        "--skip-analyze",
        action="store_true",
        help="Пропустить analyze_profiling_postprocessing.py",
    )
    parser.add_argument(
        "--skip-plot",
        action="store_true",
        help="Пропустить plot_postprocessing_analysis.py",
    )
    parser.add_argument(
        "--reference",
        default="our",
        help="Эталонная библиотека для compare/analyze",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    python = sys.executable
    total = len(args.libraries)

    print("🚀 Запуск профилирования по библиотекам")
    print("📚 Библиотеки:", ", ".join(args.libraries))
    print(f"⏸️ Пауза между библиотеками: {args.pause_seconds} сек")

    for idx, library in enumerate(args.libraries, start=1):
        print(f"\n{'=' * 70}\n[{idx}/{total}] Профилирование библиотеки: {library}\n{'=' * 70}")

        cmd = [
            python,
            "scripts/profile_benchmark.py",
            "--library",
            library,
            "--tests",
            args.tests,
            "--profiling",
            args.profiling,
            "--iterations",
            str(args.iterations),
            "--output-dir",
            args.output_dir,
            "--sanitize-paths",
            "True" if args.sanitize_paths else "False",
        ]

        if args.max_tests is not None:
            cmd.extend(["--max-tests", str(args.max_tests)])

        run_command(cmd)

        if idx < total and args.pause_seconds > 0:
            print(f"\n⏳ Пауза {args.pause_seconds} сек перед следующей библиотекой...")
            time.sleep(args.pause_seconds)

    print(f"\n{'=' * 70}\n🧪 Постпроцессинг\n{'=' * 70}")

    if not args.skip_compare:
        run_command(
            [
                python,
                "scripts/processing/compare_profiling_results.py",
                "--reference",
                args.reference,
                "--libraries",
                ",".join(args.libraries),
                "--tests",
                "all",
            ]
        )

    if not args.skip_analyze:
        run_command(
            [
                python,
                "scripts/processing/analyze_profiling_postprocessing.py",
                "--reference",
                args.reference,
                "--libraries",
                ",".join(args.libraries),
            ]
        )

    if not args.skip_plot:
        run_command([python, "scripts/processing/plot_postprocessing_analysis.py"])

    print("\n✅ Готово: профилирование и постпроцессинг завершены")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
