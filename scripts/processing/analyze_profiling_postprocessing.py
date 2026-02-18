#!/usr/bin/env python3
"""Постпроцессинг профилирования: агрегирование метрик по raw-артефактам профайлеров."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

STAGES = ["step1", "step2", "step3", "step4"]
PROFILERS = ["cpu", "memory", "line", "scalene"]


@dataclass
class StageTiming:
    library: str
    stage: str
    sample_count: int
    mean_total_ms: float
    std_total_ms: float
    mean_per_repeat_ms: float
    source_profiler: str


@dataclass
class ProfilerDuration:
    library: str
    profiler: str
    stage: str
    sample_count: int
    mean_duration_ms: float
    std_duration_ms: float


@dataclass
class MemorySummary:
    library: str
    stage: str
    sample_count: int
    mean_peak_mb: float
    max_peak_mb: float


@dataclass
class Bottleneck:
    library: str
    stage: str
    profiler: str
    filename: str
    line: int
    code: str
    total_time_s: float
    hits: int


def normalize_stage(raw_stage: str) -> str:
    if not raw_stage:
        return ""
    return raw_stage.split("_", 1)[0]


def discover_libraries(base_dir: Path) -> list[str]:
    return sorted([p.name for p in base_dir.iterdir() if p.is_dir() and p.name != "processed_results"])


def latest_run_dir(base_dir: Path, library: str) -> Path:
    lib_dir = base_dir / library
    timestamps = sorted([p for p in lib_dir.iterdir() if p.is_dir()])
    if not timestamps:
        raise FileNotFoundError(f"Не найдено прогонов для библиотеки: {library}")
    return timestamps[-1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def to_repo_relative(path_str: str) -> str:
    path = path_str.replace("\\", "/")
    marker = "DS-Benchmark/"
    idx = path.find(marker)
    if idx >= 0:
        return path[idx + len(marker) :]
    return path


def is_allowed_library_path(rel_path: str, library: str, mode: str) -> bool:
    if mode == "all":
        return True

    p = rel_path.lower()
    if library == "our":
        return p.startswith("src/core/")
    return p.startswith("external/")


def collect_profiler_files(run_dir: Path, profiler: str) -> list[Path]:
    root = run_dir / "profilers" / profiler
    if not root.exists():
        return []

    if profiler == "scalene":
        return sorted(root.glob("*/*.profile.json"))
    return sorted(root.glob("*/*.json"))


def collect_profiler_durations(run_dir: Path, library: str) -> list[ProfilerDuration]:
    durations: dict[tuple[str, str], list[float]] = defaultdict(list)

    for profiler in ["cpu", "memory", "line"]:
        for file in collect_profiler_files(run_dir, profiler):
            payload = load_json(file)
            stage = normalize_stage(str(payload.get("step", "")))
            if stage not in STAGES:
                continue
            dur = float(payload.get("metadata", {}).get("duration_seconds", 0.0)) * 1000.0
            durations[(profiler, stage)].append(dur)

    # scalene: duration из stdout не всегда стабильно доступна; фиксируем только покрытие файлов
    scalene_counts: dict[str, int] = defaultdict(int)
    stage_re = re.compile(r"(step\d+)")
    for file in collect_profiler_files(run_dir, "scalene"):
        match = stage_re.search(file.name)
        stage = normalize_stage(match.group(1) if match else "")
        if stage in STAGES:
            scalene_counts[stage] += 1

    out: list[ProfilerDuration] = []
    for profiler in PROFILERS:
        for stage in STAGES:
            if profiler == "scalene":
                count = scalene_counts.get(stage, 0)
                out.append(
                    ProfilerDuration(
                        library=library,
                        profiler=profiler,
                        stage=stage,
                        sample_count=count,
                        mean_duration_ms=0.0,
                        std_duration_ms=0.0,
                    )
                )
                continue

            vals = durations.get((profiler, stage), [])
            out.append(
                ProfilerDuration(
                    library=library,
                    profiler=profiler,
                    stage=stage,
                    sample_count=len(vals),
                    mean_duration_ms=mean(vals) if vals else 0.0,
                    std_duration_ms=pstdev(vals) if len(vals) > 1 else 0.0,
                )
            )
    return out


def build_stage_timings_from_cpu(run_dir: Path, library: str) -> list[StageTiming]:
    stage_values: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for file in collect_profiler_files(run_dir, "cpu"):
        payload = load_json(file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES:
            continue
        duration_ms = float(payload.get("metadata", {}).get("duration_seconds", 0.0)) * 1000.0
        repeat = int(payload.get("metadata", {}).get("step_repeat_count", payload.get("_metadata", {}).get("repeat_count", 1)) or 1)
        stage_values[stage].append((duration_ms, repeat))

    out: list[StageTiming] = []
    for stage in STAGES:
        vals = stage_values.get(stage, [])
        if vals:
            totals = [x[0] for x in vals]
            per_repeat = [x[0] / max(1, x[1]) for x in vals]
            out.append(
                StageTiming(
                    library=library,
                    stage=stage,
                    sample_count=len(vals),
                    mean_total_ms=mean(totals),
                    std_total_ms=pstdev(totals) if len(totals) > 1 else 0.0,
                    mean_per_repeat_ms=mean(per_repeat),
                    source_profiler="cpu",
                )
            )
        else:
            out.append(StageTiming(library, stage, 0, 0.0, 0.0, 0.0, "cpu"))
    return out


def collect_memory_stats(run_dir: Path, library: str) -> list[MemorySummary]:
    peaks: dict[str, list[float]] = defaultdict(list)
    for file in collect_profiler_files(run_dir, "memory"):
        payload = load_json(file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES:
            continue
        peak_bytes = float(payload.get("data", {}).get("peak_memory_bytes", 0))
        peaks[stage].append(peak_bytes / (1024 * 1024))

    out: list[MemorySummary] = []
    for stage in STAGES:
        vals = peaks.get(stage, [])
        out.append(
            MemorySummary(
                library=library,
                stage=stage,
                sample_count=len(vals),
                mean_peak_mb=mean(vals) if vals else 0.0,
                max_peak_mb=max(vals) if vals else 0.0,
            )
        )
    return out


def collect_line_bottlenecks(run_dir: Path, library: str, top_n: int, path_mode: str) -> list[Bottleneck]:
    grouped: dict[tuple[str, str, int], dict[str, Any]] = {}

    for file in collect_profiler_files(run_dir, "line"):
        payload = load_json(file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES:
            continue

        for line_info in payload.get("data", {}).get("top_lines", []):
            rel_path = to_repo_relative(str(line_info.get("filename", "")))
            if not is_allowed_library_path(rel_path, library, path_mode):
                continue

            line = int(line_info.get("line", 0))
            key = (stage, rel_path, line)
            bucket = grouped.setdefault(
                key,
                {"total_time_s": 0.0, "hits": 0, "code": str(line_info.get("code", "")).strip()},
            )
            bucket["total_time_s"] += float(line_info.get("total_time", 0.0))
            bucket["hits"] += int(line_info.get("hits", 0))

    by_stage: dict[str, list[Bottleneck]] = defaultdict(list)
    for (stage, filename, line), stats in grouped.items():
        by_stage[stage].append(
            Bottleneck(
                library=library,
                stage=stage,
                profiler="line",
                filename=filename,
                line=line,
                code=stats["code"],
                total_time_s=stats["total_time_s"],
                hits=stats["hits"],
            )
        )

    out: list[Bottleneck] = []
    for stage in STAGES:
        out.extend(sorted(by_stage.get(stage, []), key=lambda x: x.total_time_s, reverse=True)[:top_n])
    return out


def speedup_vs_reference(stage_timings: list[StageTiming], reference: str) -> dict[str, dict[str, float | None]]:
    idx = {(x.library, x.stage): x for x in stage_timings}
    out: dict[str, dict[str, float | None]] = defaultdict(dict)
    libs = sorted({x.library for x in stage_timings})
    for lib in libs:
        for stage in STAGES:
            cur = idx.get((lib, stage))
            ref = idx.get((reference, stage))
            if not cur or not ref or cur.sample_count == 0 or ref.sample_count == 0 or cur.mean_per_repeat_ms == 0:
                out[lib][stage] = None
            else:
                out[lib][stage] = ref.mean_per_repeat_ms / cur.mean_per_repeat_ms
    return out


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(
    reference: str,
    path_mode: str,
    stage_timings: list[StageTiming],
    profiler_durations: list[ProfilerDuration],
    memory_stats: list[MemorySummary],
    bottlenecks: list[Bottleneck],
    speedups: dict[str, dict[str, float | None]],
) -> str:
    lines: list[str] = ["# Postprocessing analysis of profiling runs", "", f"Reference library: `{reference}`", f"Path filter mode: `{path_mode}`", ""]

    libs = sorted({x.library for x in stage_timings})

    lines += ["## 1) Stage timings from CPU profiler metadata (mean per repeat, ms)", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = []
        for stage in STAGES:
            rec = next((x for x in stage_timings if x.library == lib and x.stage == stage), None)
            vals.append("n/a" if rec is None or rec.sample_count == 0 else f"{rec.mean_per_repeat_ms:.2f}")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines += ["", "## 2) Relative speedup vs reference (reference_time / lib_time)", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = ["n/a" if speedups.get(lib, {}).get(stage) is None else f"{speedups[lib][stage]:.2f}x" for stage in STAGES]
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines += ["", "## 3) Profiler duration coverage", "", "| Library | Profiler | Stage | Samples | Mean duration (ms) | Std (ms) |", "|---|---|---|---:|---:|---:|"]
    for rec in sorted(profiler_durations, key=lambda x: (x.library, x.profiler, x.stage)):
        lines.append(f"| {rec.library} | {rec.profiler} | {rec.stage} | {rec.sample_count} | {rec.mean_duration_ms:.2f} | {rec.std_duration_ms:.2f} |")

    lines += ["", "## 4) Peak memory by stage (MB)", "", "| Library | Stage | Mean peak | Max peak | Samples |", "|---|---|---:|---:|---:|"]
    for rec in sorted(memory_stats, key=lambda x: (x.library, x.stage)):
        if rec.sample_count == 0:
            lines.append(f"| {rec.library} | {rec.stage} | n/a | n/a | 0 |")
        else:
            lines.append(f"| {rec.library} | {rec.stage} | {rec.mean_peak_mb:.2f} | {rec.max_peak_mb:.2f} | {rec.sample_count} |")

    lines += ["", "## 5) Bottlenecks from line profiler (filtered)", "", "| Library | Stage | File:Line | Total time (s) | Hits | Code |", "|---|---|---|---:|---:|---|"]
    for b in sorted(bottlenecks, key=lambda x: (x.library, x.stage, -x.total_time_s)):
        code = b.code.replace("|", "\\|")
        lines.append(f"| {b.library} | {b.stage} | `{b.filename}:{b.line}` | {b.total_time_s:.4f} | {b.hits} | `{code}` |")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Анализ профилирования по raw-артефактам профайлеров")
    parser.add_argument("--base-dir", default="results/profiling")
    parser.add_argument("--libraries", default="all")
    parser.add_argument("--reference", default="our")
    parser.add_argument("--top-lines", type=int, default=5)
    parser.add_argument(
        "--path-filter",
        choices=["library_only", "all"],
        default="library_only",
        help="library_only: our->src/core/*, others->external/*; all: без фильтра путей",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    libraries = discover_libraries(base_dir) if args.libraries.lower() == "all" else [x.strip() for x in args.libraries.split(",") if x.strip()]
    if not libraries:
        raise ValueError("Не найдено библиотек для анализа")
    if args.reference not in libraries:
        libraries.insert(0, args.reference)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = base_dir / "processed_results" / "postprocessing_analysis" / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stage_timings: list[StageTiming] = []
    all_profiler_durations: list[ProfilerDuration] = []
    all_memory: list[MemorySummary] = []
    all_bottlenecks: list[Bottleneck] = []
    run_paths: dict[str, str] = {}

    for lib in libraries:
        run_dir = latest_run_dir(base_dir, lib)
        run_paths[lib] = str(run_dir)
        all_stage_timings.extend(build_stage_timings_from_cpu(run_dir, lib))
        all_profiler_durations.extend(collect_profiler_durations(run_dir, lib))
        all_memory.extend(collect_memory_stats(run_dir, lib))
        all_bottlenecks.extend(collect_line_bottlenecks(run_dir, lib, top_n=args.top_lines, path_mode=args.path_filter))

    speedups = speedup_vs_reference(all_stage_timings, args.reference)

    timings_rows = [
        {
            "library": x.library,
            "stage": x.stage,
            "sample_count": x.sample_count,
            "mean_total_ms": round(x.mean_total_ms, 6),
            "std_total_ms": round(x.std_total_ms, 6),
            "mean_per_repeat_ms": round(x.mean_per_repeat_ms, 6),
            "source_profiler": x.source_profiler,
            "speedup_vs_reference": None if speedups[x.library][x.stage] is None else round(float(speedups[x.library][x.stage]), 6),
        }
        for x in sorted(all_stage_timings, key=lambda i: (i.library, i.stage))
    ]
    duration_rows = [
        {
            "library": x.library,
            "profiler": x.profiler,
            "stage": x.stage,
            "sample_count": x.sample_count,
            "mean_duration_ms": round(x.mean_duration_ms, 6),
            "std_duration_ms": round(x.std_duration_ms, 6),
        }
        for x in sorted(all_profiler_durations, key=lambda i: (i.library, i.profiler, i.stage))
    ]
    memory_rows = [
        {
            "library": x.library,
            "stage": x.stage,
            "sample_count": x.sample_count,
            "mean_peak_mb": round(x.mean_peak_mb, 6),
            "max_peak_mb": round(x.max_peak_mb, 6),
        }
        for x in sorted(all_memory, key=lambda i: (i.library, i.stage))
    ]
    bottleneck_rows = [
        {
            "library": x.library,
            "stage": x.stage,
            "profiler": x.profiler,
            "filename": x.filename,
            "line": x.line,
            "total_time_s": round(x.total_time_s, 6),
            "hits": x.hits,
            "code": x.code,
        }
        for x in sorted(all_bottlenecks, key=lambda i: (i.library, i.stage, -i.total_time_s))
    ]

    write_csv(
        out_dir / "stage_timings.csv",
        timings_rows,
        ["library", "stage", "sample_count", "mean_total_ms", "std_total_ms", "mean_per_repeat_ms", "source_profiler", "speedup_vs_reference"],
    )
    write_csv(
        out_dir / "profiler_durations.csv",
        duration_rows,
        ["library", "profiler", "stage", "sample_count", "mean_duration_ms", "std_duration_ms"],
    )
    write_csv(out_dir / "memory_stage_summary.csv", memory_rows, ["library", "stage", "sample_count", "mean_peak_mb", "max_peak_mb"])
    write_csv(out_dir / "line_bottlenecks.csv", bottleneck_rows, ["library", "stage", "profiler", "filename", "line", "total_time_s", "hits", "code"])

    report_md = build_markdown_report(
        reference=args.reference,
        path_mode=args.path_filter,
        stage_timings=all_stage_timings,
        profiler_durations=all_profiler_durations,
        memory_stats=all_memory,
        bottlenecks=all_bottlenecks,
        speedups=speedups,
    )
    (out_dir / "analysis_report.md").write_text(report_md, encoding="utf-8")

    report_json = {
        "meta": {
            "generated_at": timestamp,
            "base_dir": str(base_dir),
            "libraries": libraries,
            "reference": args.reference,
            "top_lines_per_stage": args.top_lines,
            "path_filter": args.path_filter,
            "source_runs": run_paths,
        },
        "stage_timings": timings_rows,
        "profiler_durations": duration_rows,
        "memory_summary": memory_rows,
        "line_bottlenecks": bottleneck_rows,
    }
    (out_dir / "analysis_report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Analysis artifacts saved to: {out_dir}")
    print(f" - {out_dir / 'analysis_report.md'}")
    print(f" - {out_dir / 'analysis_report.json'}")
    print(f" - {out_dir / 'stage_timings.csv'}")
    print(f" - {out_dir / 'profiler_durations.csv'}")
    print(f" - {out_dir / 'memory_stage_summary.csv'}")
    print(f" - {out_dir / 'line_bottlenecks.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
