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

    # profile_benchmark.py
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

    # Общие параметры эталона/пропусков
    parser.add_argument("--reference", default="our", help="Эталонная библиотека для compare/analyze")
    parser.add_argument("--skip-compare", action="store_true", help="Пропустить compare_profiling_results.py")
    parser.add_argument("--skip-analyze", action="store_true", help="Пропустить analyze_profiling_postprocessing.py")
    parser.add_argument("--skip-plot", action="store_true", help="Пропустить plot_postprocessing_analysis.py")

    # compare_profiling_results.py
    parser.add_argument(
        "--compare-base-dir",
        default=None,
        help="Параметр --base-dir для compare_profiling_results.py (по умолчанию берется --output-dir)",
    )
    parser.add_argument(
        "--compare-libraries",
        default=None,
        help="Параметр --libraries для compare_profiling_results.py (по умолчанию: --libraries пайплайна)",
    )
    parser.add_argument(
        "--compare-tests",
        default="all",
        help="Параметр --tests для compare_profiling_results.py",
    )
    parser.add_argument(
        "--compare-show-top-diffs",
        type=int,
        default=0,
        help="Параметр --show-top-diffs для compare_profiling_results.py",
    )
    parser.add_argument(
        "--compare-identical-threshold",
        type=float,
        default=1e-12,
        help="Параметр --identical-threshold для compare_profiling_results.py",
    )

    # analyze_profiling_postprocessing.py
    parser.add_argument(
        "--analyze-base-dir",
        default=None,
        help="Параметр --base-dir для analyze_profiling_postprocessing.py (по умолчанию берется --output-dir)",
    )
    parser.add_argument(
        "--analyze-libraries",
        default=None,
        help="Параметр --libraries для analyze_profiling_postprocessing.py (по умолчанию: --libraries пайплайна)",
    )
    parser.add_argument("--analyze-top-lines", type=int, default=5, help="Параметр --top-lines для analyze")
    parser.add_argument(
        "--analyze-path-filter",
        choices=["library_only", "all"],
        default="library_only",
        help="Параметр --path-filter для analyze_profiling_postprocessing.py",
    )
    parser.add_argument(
        "--analyze-include-scalene",
        type=parse_bool,
        default=False,
        help="Параметр --include-scalene для analyze_profiling_postprocessing.py (True/False)",
    )

    # plot_postprocessing_analysis.py
    parser.add_argument(
        "--plot-base-dir",
        default=None,
        help="Параметр --base-dir для plot_postprocessing_analysis.py (по умолчанию: <analyze-base-dir>/processed_results/postprocessing_analysis)",
    )
    parser.add_argument("--plot-analysis-dir", default=None, help="Параметр --analysis-dir для plot")
    parser.add_argument("--plot-out-dir", default=None, help="Параметр --out-dir для plot")
    parser.add_argument("--plot-top-lines", type=int, default=20, help="Параметр --top-lines для plot")
    parser.add_argument("--plot-line-library", default="our", help="Параметр --line-library для plot")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    python = sys.executable
    total = len(args.libraries)
    selected_libraries = ",".join(args.libraries)
    compare_base_dir = args.compare_base_dir or args.output_dir
    analyze_base_dir = args.analyze_base_dir or args.output_dir
    analyze_libraries = args.analyze_libraries or selected_libraries
    compare_libraries = args.compare_libraries or selected_libraries
    plot_base_dir = args.plot_base_dir or f"{analyze_base_dir}/processed_results/postprocessing_analysis"

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
                "--base-dir",
                compare_base_dir,
                "--reference",
                args.reference,
                "--libraries",
                compare_libraries,
                "--tests",
                args.compare_tests,
                "--show-top-diffs",
                str(args.compare_show_top_diffs),
                "--identical-threshold",
                str(args.compare_identical_threshold),
            ]
        )

    if not args.skip_analyze:
        analyze_cmd = [
            python,
            "scripts/processing/analyze_profiling_postprocessing.py",
            "--base-dir",
            analyze_base_dir,
            "--reference",
            args.reference,
            "--libraries",
            analyze_libraries,
            "--top-lines",
            str(args.analyze_top_lines),
            "--path-filter",
            args.analyze_path_filter,
        ]
        analyze_cmd.append("--include-scalene" if args.analyze_include_scalene else "--no-include-scalene")
        run_command(analyze_cmd)

    if not args.skip_plot:
        plot_cmd = [
            python,
            "scripts/processing/plot_postprocessing_analysis.py",
            "--base-dir",
            plot_base_dir,
            "--top-lines",
            str(args.plot_top_lines),
            "--line-library",
            args.plot_line_library,
        ]
        if args.plot_analysis_dir is not None:
            plot_cmd.extend(["--analysis-dir", args.plot_analysis_dir])
        if args.plot_out_dir is not None:
            plot_cmd.extend(["--out-dir", args.plot_out_dir])
        run_command(plot_cmd)

    print("\n✅ Готово: профилирование и постпроцессинг завершены")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
