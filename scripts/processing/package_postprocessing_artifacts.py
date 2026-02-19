#!/usr/bin/env python3
"""Упаковка артефактов постпроцессинга и связанных исходных прогонов в один архив."""

from __future__ import annotations

import argparse
import json
import shutil
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
POSTPROCESSING_ROOT = REPO_ROOT / "results" / "profiling" / "processed_results" / "postprocessing_analysis"
PACKAGED_ROOT = REPO_ROOT / "results" / "profiling" / "processed_results" / "postprocessing_artifacts"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Сжимает все source_runs из analysis_report.json выбранного postprocessing-отчета "
            "и складывает в отдельную папку в processed_results/postprocessing_artifacts/<timestamp> "
            "вместе с копией файлов отчета."
        )
    )
    parser.add_argument(
        "--analysis-timestamp",
        default=None,
        help="Таймстемп папки анализа (по умолчанию берется последний доступный отчет).",
    )
    parser.add_argument(
        "--output-timestamp",
        default=None,
        help="Таймстемп папки назначения в postprocessing_artifacts/<timestamp> (по умолчанию текущее время YYYYmmdd_HHMMSS).",
    )
    parser.add_argument(
        "--delete-source",
        action="store_true",
        help="После успешного сжатия удалить исходные source_runs (по умолчанию только копирование в архив).",
    )
    parser.add_argument(
        "--archive-name",
        default="source_runs.tar.xz",
        help="Имя архива в папке назначения (по умолчанию source_runs.tar.xz).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать план действий без записи файлов и удаления данных.",
    )
    return parser.parse_args()


def latest_analysis_dir(root: Path) -> Path:
    dirs = sorted([p for p in root.iterdir() if p.is_dir()])
    if not dirs:
        raise FileNotFoundError(f"В {root} не найдено директорий анализа")
    return dirs[-1]


def normalize_path(path_str: str) -> Path:
    normalized = path_str.replace("\\", "/")
    candidate = Path(normalized)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def load_source_runs(analysis_dir: Path) -> dict[str, Path]:
    report_path = analysis_dir / "analysis_report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Не найден файл отчета: {report_path}")

    payload: dict[str, Any] = json.loads(report_path.read_text(encoding="utf-8"))
    meta = payload.get("meta", {}) if isinstance(payload.get("meta"), dict) else {}
    source_runs_raw = meta.get("source_runs")

    if not isinstance(source_runs_raw, dict) or not source_runs_raw:
        raise ValueError(f"В {report_path} не найден непустой объект meta.source_runs")

    source_runs: dict[str, Path] = {}
    for library, raw_path in source_runs_raw.items():
        if not isinstance(raw_path, str):
            raise ValueError(f"meta.source_runs[{library}] должен быть строкой, получено: {type(raw_path)}")
        resolved = normalize_path(raw_path)
        if not resolved.exists():
            raise FileNotFoundError(f"Путь source_runs для {library} не существует: {resolved}")
        source_runs[str(library)] = resolved

    return source_runs


def copy_analysis_files(src_dir: Path, dst_dir: Path, dry_run: bool) -> None:
    for item in src_dir.iterdir():
        target = dst_dir / item.name
        if dry_run:
            print(f"[dry-run] copy: {item} -> {target}")
            continue
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def build_archive(archive_path: Path, source_runs: dict[str, Path], dry_run: bool) -> None:
    if dry_run:
        for library, src in source_runs.items():
            arcname = Path("source_runs") / library / src.name
            print(f"[dry-run] archive add: {src} as {arcname}")
        return

    with tarfile.open(archive_path, "w:xz", preset=9) as tar:
        for library, src in source_runs.items():
            arcname = Path("source_runs") / library / src.name
            tar.add(src, arcname=arcname.as_posix())


def maybe_delete_source(source_runs: dict[str, Path], dry_run: bool) -> None:
    for library, src in source_runs.items():
        if dry_run:
            print(f"[dry-run] delete: {src}")
            continue
        if src.is_dir():
            shutil.rmtree(src)
        else:
            src.unlink()
        print(f"Удален source_run для {library}: {src}")


def main() -> None:
    args = parse_args()
    analysis_dir = (
        POSTPROCESSING_ROOT / args.analysis_timestamp
        if args.analysis_timestamp
        else latest_analysis_dir(POSTPROCESSING_ROOT)
    )
    if not analysis_dir.exists() or not analysis_dir.is_dir():
        raise FileNotFoundError(f"Директория анализа не найдена: {analysis_dir}")

    output_timestamp = args.output_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = PACKAGED_ROOT / output_timestamp
    archive_path = output_dir / args.archive_name

    if output_dir.exists():
        raise FileExistsError(f"Директория назначения уже существует: {output_dir}")

    source_runs = load_source_runs(analysis_dir)

    print(f"Выбран отчет: {analysis_dir}")
    print(f"Папка назначения: {output_dir}")
    print("Режим: копия отчета + архив в отдельной папке processed_results/postprocessing_artifacts")
    print(f"Архив: {archive_path.name}")
    print("source_runs:")
    for library, src in source_runs.items():
        print(f"  - {library}: {src}")

    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=False)

    copy_analysis_files(analysis_dir, output_dir, args.dry_run)
    build_archive(archive_path, source_runs, args.dry_run)

    if args.delete_source:
        maybe_delete_source(source_runs, args.dry_run)

    print("Готово.")


if __name__ == "__main__":
    main()
