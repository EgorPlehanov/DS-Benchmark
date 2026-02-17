#!/usr/bin/env python3
"""Сравнение вычислительных результатов профилирования между библиотеками."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class DiffStat:
    compared_values: int = 0
    max_abs_diff: float = 0.0
    mean_abs_diff: float = 0.0
    missing_paths: int = 0
    extra_paths: int = 0
    top_diffs: list[tuple[str, float, float, float]] | None = None


def flatten_numeric(data: Any, prefix: str = "") -> dict[str, float]:
    """Преобразует вложенный JSON в плоский словарь только с числовыми значениями."""
    flat: dict[str, float] = {}

    if isinstance(data, dict):
        for key, value in data.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            flat.update(flatten_numeric(value, path))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            flat.update(flatten_numeric(value, path))
    elif isinstance(data, (int, float)) and not isinstance(data, bool):
        flat[prefix] = float(data)

    return flat


def discover_libraries(base_dir: Path) -> list[str]:
    """Возвращает все библиотеки, у которых есть хотя бы один прогон профилирования."""
    if not base_dir.exists():
        raise FileNotFoundError(f"Базовая директория не найдена: {base_dir}")

    return sorted([p.name for p in base_dir.iterdir() if p.is_dir() and p.name != "processed_results"])


def discover_tests(base_dir: Path, libraries: list[str]) -> list[str]:
    """Возвращает пересечение доступных тестов по выбранным библиотекам."""
    tests_by_library: list[set[str]] = []

    for library in libraries:
        lib_root = base_dir / library
        timestamp_dirs = sorted([p for p in lib_root.iterdir() if p.is_dir()])
        if not timestamp_dirs:
            continue

        latest = timestamp_dirs[-1]
        test_results_dir = latest / "test_results"
        if not test_results_dir.exists():
            continue

        test_names = {
            file.name.removesuffix("_results.json")
            for file in test_results_dir.glob("*_results.json")
        }
        if test_names:
            tests_by_library.append(test_names)

    if not tests_by_library:
        return []

    common_tests = set.intersection(*tests_by_library)
    return sorted(common_tests)


def load_latest_result(base_dir: Path, library: str, test_name: str) -> tuple[Path, dict[str, Any]]:
    lib_root = base_dir / library
    timestamps = sorted([p for p in lib_root.iterdir() if p.is_dir()])
    if not timestamps:
        raise FileNotFoundError(f"Не найдены прогоны для библиотеки '{library}' в {lib_root}")

    latest = timestamps[-1]
    result_path = latest / "test_results" / f"{test_name}_results.json"
    if not result_path.exists():
        raise FileNotFoundError(f"Файл результатов не найден: {result_path}")

    with result_path.open("r", encoding="utf-8") as f:
        return result_path, json.load(f)


def compare_stage(reference_stage: Any, target_stage: Any, top_n: int = 0) -> DiffStat:
    if reference_stage is None and target_stage is None:
        return DiffStat()
    if reference_stage is None and target_stage is not None:
        extra = len(flatten_numeric(target_stage))
        return DiffStat(extra_paths=extra)
    if reference_stage is not None and target_stage is None:
        missing = len(flatten_numeric(reference_stage))
        return DiffStat(missing_paths=missing)

    ref_flat = flatten_numeric(reference_stage)
    tgt_flat = flatten_numeric(target_stage)

    common = sorted(set(ref_flat) & set(tgt_flat))
    missing = len(set(ref_flat) - set(tgt_flat))
    extra = len(set(tgt_flat) - set(ref_flat))

    if not common:
        return DiffStat(missing_paths=missing, extra_paths=extra)

    raw_diffs = [
        (path, ref_flat[path], tgt_flat[path], abs(ref_flat[path] - tgt_flat[path]))
        for path in common
    ]
    abs_diffs = [item[3] for item in raw_diffs]
    top_diffs = sorted(raw_diffs, key=lambda item: item[3], reverse=True)[:top_n] if top_n else None

    return DiffStat(
        compared_values=len(common),
        max_abs_diff=max(abs_diffs),
        mean_abs_diff=sum(abs_diffs) / len(abs_diffs),
        missing_paths=missing,
        extra_paths=extra,
        top_diffs=top_diffs,
    )


def write_reports(base_dir: Path, timestamp: str, report_json: dict[str, Any], report_txt: str) -> tuple[Path, Path]:
    """Сохраняет отчеты в processed_results/comparison_report/<timestamp>/..."""
    report_dir = base_dir / "processed_results" / "comparison_report" / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "comparison_report.json"
    txt_path = report_dir / "comparison_report.txt"

    json_path.write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")
    txt_path.write_text(report_txt, encoding="utf-8")

    return json_path, txt_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Сравнение test_results между библиотеками профилирования")
    parser.add_argument("--base-dir", default="results/profiling", help="Базовая директория профилирования")
    parser.add_argument("--reference", default="our", help="Эталонная библиотека")
    parser.add_argument("--libraries", default="all", help="Список библиотек через запятую или 'all'")
    parser.add_argument("--tests", default="all", help="Список тестов через запятую или 'all'")
    parser.add_argument("--show-top-diffs", type=int, default=0, help="Показывать N наибольших расхождений по каждому шагу")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)

    if args.libraries.strip().lower() == "all":
        libraries = discover_libraries(base_dir)
    else:
        libraries = [lib.strip() for lib in args.libraries.split(",") if lib.strip()]

    if not libraries:
        raise ValueError("Не удалось определить список библиотек для сравнения")

    if args.reference not in libraries:
        libraries.insert(0, args.reference)

    if args.tests.strip().lower() == "all":
        tests = discover_tests(base_dir, libraries)
    else:
        tests = [name.strip() for name in args.tests.split(",") if name.strip()]

    if not tests:
        raise ValueError("Не удалось определить список тестов для сравнения")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report: dict[str, Any] = {
        "meta": {
            "generated_at": timestamp,
            "base_dir": str(base_dir),
            "reference": args.reference,
            "libraries": libraries,
            "tests": tests,
            "show_top_diffs": args.show_top_diffs,
        },
        "tests": {},
    }

    text_lines: list[str] = []

    for test_name in tests:
        header_line = f"\n=== Тест: {test_name} ==="
        print(header_line)
        text_lines.append(header_line)

        loaded: dict[str, dict[str, Any]] = {}
        used_paths: dict[str, Path] = {}
        for lib in libraries:
            path, payload = load_latest_result(base_dir, lib, test_name)
            loaded[lib] = payload
            used_paths[lib] = path

        print("Использованные файлы:")
        text_lines.append("Использованные файлы:")
        for lib in libraries:
            src_line = f"  - {lib}: {used_paths[lib]}"
            print(src_line)
            text_lines.append(src_line)

        ref_results = loaded[args.reference]["aggregated"]["results"]
        stages = ["step1", "step2", "step3", "step4"]

        print("\nСравнение с эталоном:")
        text_lines.append("\nСравнение с эталоном:")
        table_header = "library | stage | compared | max_abs_diff | mean_abs_diff | missing | extra"
        print(table_header)
        print("-" * len(table_header))
        text_lines.append(table_header)
        text_lines.append("-" * len(table_header))

        report["tests"][test_name] = {
            "sources": {lib: str(path) for lib, path in used_paths.items()},
            "comparisons": {},
        }

        for lib in libraries:
            if lib == args.reference:
                continue

            target_results = loaded[lib]["aggregated"]["results"]
            report["tests"][test_name]["comparisons"][lib] = {}

            for stage in stages:
                stat = compare_stage(ref_results.get(stage), target_results.get(stage), top_n=args.show_top_diffs)
                row = (
                    f"{lib:7} | {stage:5} | {stat.compared_values:8d} | "
                    f"{stat.max_abs_diff:12.3e} | {stat.mean_abs_diff:13.3e} | "
                    f"{stat.missing_paths:7d} | {stat.extra_paths:5d}"
                )
                print(row)
                text_lines.append(row)

                stat_dict = asdict(stat)
                if stat_dict.get("top_diffs") is not None:
                    stat_dict["top_diffs"] = [
                        {
                            "path": path,
                            "reference": ref_val,
                            "target": tgt_val,
                            "abs_diff": abs_diff,
                        }
                        for path, ref_val, tgt_val, abs_diff in stat.top_diffs or []
                    ]

                report["tests"][test_name]["comparisons"][lib][stage] = stat_dict

                if stat.top_diffs:
                    for path, ref_val, tgt_val, abs_diff in stat.top_diffs:
                        if abs_diff == 0:
                            break
                        diff_line = (
                            f"         └─ {path}: ref={ref_val:.6g}, "
                            f"target={tgt_val:.6g}, abs_diff={abs_diff:.6g}"
                        )
                        print(diff_line)
                        text_lines.append(diff_line)

    report_txt = "\n".join(text_lines).strip() + "\n"
    json_path, txt_path = write_reports(base_dir, timestamp, report, report_txt)

    print("\n✅ Отчеты сохранены:")
    print(f"  JSON: {json_path}")
    print(f"  TABLE: {txt_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
