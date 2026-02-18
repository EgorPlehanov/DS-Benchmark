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
    mean_step_repeat_count: float
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


@dataclass
class ScaleneStageSummary:
    library: str
    stage: str
    sample_count: int
    mean_elapsed_ms: float
    mean_max_footprint_mb: float
    mean_filtered_cpu_percent: float


@dataclass
class ScaleneHotspot:
    library: str
    stage: str
    filename: str
    line: int
    code: str
    cpu_percent: float
    peak_mb: float
    malloc_mb: float


def normalize_stage(raw_stage: str) -> str:
    if not raw_stage:
        return ""
    return raw_stage.split("_", 1)[0]


def flatten_numeric(data: Any, prefix: str = "") -> dict[str, float]:
    """Плоское представление только числовых полей вложенной структуры."""
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


def latest_run_with_results(base_dir: Path, library: str) -> Path | None:
    lib_dir = base_dir / library
    if not lib_dir.exists():
        return None
    timestamps = sorted([p for p in lib_dir.iterdir() if p.is_dir()])
    for run_dir in reversed(timestamps):
        test_dir = run_dir / "test_results"
        if test_dir.exists() and any(test_dir.glob("*_results.json")):
            return run_dir
    return None


def build_supported_map_from_test_results(base_dir: Path, reference: str, libraries: list[str]) -> tuple[dict[str, dict[str, bool]], str | None]:
    support = {lib: {stage: True for stage in STAGES} for lib in libraries}

    ref_run = latest_run_with_results(base_dir, reference)
    if ref_run is None:
        return support, None

    ref_test_dir = ref_run / "test_results"
    ref_files = sorted(ref_test_dir.glob("*_results.json"))
    if not ref_files:
        return support, None

    for lib in libraries:
        if lib != reference:
            for stage in STAGES:
                support[lib][stage] = False

    runs_by_lib = {lib: latest_run_with_results(base_dir, lib) for lib in libraries if lib != reference}

    for ref_file in ref_files:
        test_name = ref_file.name
        ref_payload = load_json(ref_file)
        ref_results = ref_payload.get("results", {}) if isinstance(ref_payload.get("results", {}), dict) else {}

        for lib in libraries:
            if lib == reference:
                continue
            lib_run = runs_by_lib.get(lib)
            if lib_run is None:
                continue
            tgt_file = lib_run / "test_results" / test_name
            if not tgt_file.exists():
                continue
            tgt_payload = load_json(tgt_file)
            tgt_results = tgt_payload.get("results", {}) if isinstance(tgt_payload.get("results", {}), dict) else {}

            for stage in STAGES:
                ref_stage = ref_results.get(stage)
                tgt_stage = tgt_results.get(stage)
                if ref_stage is None or tgt_stage is None:
                    continue
                ref_flat = flatten_numeric(ref_stage)
                tgt_flat = flatten_numeric(tgt_stage)
                if not ref_flat:
                    continue
                if set(ref_flat).intersection(tgt_flat):
                    support[lib][stage] = True

    source = f"derived_from_test_results:{ref_run}"
    return support, source


def discover_libraries(base_dir: Path) -> list[str]:
    return sorted([p.name for p in base_dir.iterdir() if p.is_dir() and p.name != "processed_results"])


def latest_run_dir(base_dir: Path, library: str) -> Path:
    lib_dir = base_dir / library
    timestamps = sorted([p for p in lib_dir.iterdir() if p.is_dir()])
    if not timestamps:
        raise FileNotFoundError(f"Не найдено прогонов для библиотеки: {library}")
    for run_dir in reversed(timestamps):
        cpu_files = collect_profiler_files(run_dir, "cpu")
        if not cpu_files:
            continue
        for file in cpu_files:
            payload = load_json(file)
            stage = normalize_stage(str(payload.get("step", "")))
            if stage in STAGES:
                return run_dir
    return timestamps[-1]


def latest_comparison_report(base_dir: Path) -> Path | None:
    root = base_dir / "processed_results" / "comparison_report"
    if not root.exists():
        return None
    runs = sorted([p for p in root.iterdir() if p.is_dir()])
    if not runs:
        return None
    candidate = runs[-1] / "comparison_report.json"
    return candidate if candidate.exists() else None


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_supported_map(base_dir: Path, reference: str, libraries: list[str]) -> tuple[dict[str, dict[str, bool]], str | None]:
    support = {lib: {stage: True for stage in STAGES} for lib in libraries}
    support_source: str | None = None

    report_path = latest_comparison_report(base_dir)
    if report_path is not None:
        payload = load_json(report_path)
        global_by_stage = payload.get("summary", {}).get("global", {}).get("by_stage", {})

        if global_by_stage:
            for lib in libraries:
                if lib == reference:
                    continue
                lib_stage = global_by_stage.get(lib, {})
                for stage in STAGES:
                    compared_values = int(lib_stage.get(stage, {}).get("compared_values", 0))
                    total_reference = int(lib_stage.get(stage, {}).get("total_reference_values", 0))
                    support[lib][stage] = compared_values > 0 and total_reference > 0

            support_source = str(report_path)
            return support, support_source

    # Fallback: derive support directly from test_results if comparison report is absent.
    derived_support, derived_source = build_supported_map_from_test_results(base_dir, reference, libraries)
    return derived_support, derived_source


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

    scalene_counts: dict[str, int] = defaultdict(int)
    stage_re = re.compile(r"(step\d+)")
    for file in collect_profiler_files(run_dir, "scalene"):
        m = stage_re.search(file.name)
        stage = normalize_stage(m.group(1) if m else "")
        if stage in STAGES:
            scalene_counts[stage] += 1

    out: list[ProfilerDuration] = []
    for profiler in PROFILERS:
        for stage in STAGES:
            if profiler == "scalene":
                out.append(ProfilerDuration(library, profiler, stage, scalene_counts.get(stage, 0), 0.0, 0.0))
            else:
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
            repeats = [max(1, x[1]) for x in vals]
            per_repeat = [x[0] / rep for x, rep in zip(vals, repeats)]
            out.append(
                StageTiming(
                    library,
                    stage,
                    len(vals),
                    mean(totals),
                    pstdev(totals) if len(totals) > 1 else 0.0,
                    mean(per_repeat),
                    mean(repeats),
                    "cpu",
                )
            )
        else:
            out.append(StageTiming(library, stage, 0, 0.0, 0.0, 0.0, 0.0, "cpu"))
    return out


def collect_memory_stats(run_dir: Path, library: str) -> list[MemorySummary]:
    peaks: dict[str, list[float]] = defaultdict(list)
    for file in collect_profiler_files(run_dir, "memory"):
        payload = load_json(file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES:
            continue
        peaks[stage].append(float(payload.get("data", {}).get("peak_memory_bytes", 0)) / (1024 * 1024))

    out: list[MemorySummary] = []
    for stage in STAGES:
        vals = peaks.get(stage, [])
        out.append(MemorySummary(library, stage, len(vals), mean(vals) if vals else 0.0, max(vals) if vals else 0.0))
    return out


def collect_line_bottlenecks(run_dir: Path, library: str, top_n: int, path_mode: str, support_map: dict[str, dict[str, bool]]) -> list[Bottleneck]:
    grouped: dict[tuple[str, str, int], dict[str, Any]] = {}
    for file in collect_profiler_files(run_dir, "line"):
        payload = load_json(file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES or not support_map.get(library, {}).get(stage, True):
            continue
        for line_info in payload.get("data", {}).get("top_lines", []):
            rel_path = to_repo_relative(str(line_info.get("filename", "")))
            if not is_allowed_library_path(rel_path, library, path_mode):
                continue
            line = int(line_info.get("line", 0))
            key = (stage, rel_path, line)
            bucket = grouped.setdefault(key, {"total_time_s": 0.0, "hits": 0, "code": str(line_info.get("code", "")).strip()})
            bucket["total_time_s"] += float(line_info.get("total_time", 0.0))
            bucket["hits"] += int(line_info.get("hits", 0))

    by_stage: dict[str, list[Bottleneck]] = defaultdict(list)
    for (stage, filename, line), stats in grouped.items():
        by_stage[stage].append(Bottleneck(library, stage, "line", filename, line, stats["code"], stats["total_time_s"], stats["hits"]))

    out: list[Bottleneck] = []
    for stage in STAGES:
        out.extend(sorted(by_stage.get(stage, []), key=lambda x: x.total_time_s, reverse=True)[:top_n])
    return out


def collect_scalene_stats(
    run_dir: Path,
    library: str,
    top_n: int,
    path_mode: str,
    support_map: dict[str, dict[str, bool]],
) -> tuple[list[ScaleneStageSummary], list[ScaleneHotspot]]:
    stage_re = re.compile(r"(step\d+)")
    stage_elapsed: dict[str, list[float]] = defaultdict(list)
    stage_footprint: dict[str, list[float]] = defaultdict(list)
    stage_filtered_cpu: dict[str, list[float]] = defaultdict(list)
    grouped_hotspots: dict[tuple[str, str, int], dict[str, Any]] = {}

    for file in collect_profiler_files(run_dir, "scalene"):
        m = stage_re.search(file.name)
        stage = normalize_stage(m.group(1) if m else "")
        if stage not in STAGES or not support_map.get(library, {}).get(stage, True):
            continue

        payload = load_json(file)
        stage_elapsed[stage].append(float(payload.get("elapsed_time_sec", 0.0)) * 1000.0)
        stage_footprint[stage].append(float(payload.get("max_footprint_mb", 0.0)))

        files_map = payload.get("files", {}) if isinstance(payload.get("files", {}), dict) else {}
        filtered_cpu_percent = 0.0

        for fname, fdata in files_map.items():
            rel = to_repo_relative(str(fname))
            if not is_allowed_library_path(rel, library, path_mode):
                continue

            filtered_cpu_percent += float(fdata.get("percent_cpu_time", 0.0) or 0.0)
            for ln in fdata.get("lines", []) or []:
                lineno = int(ln.get("lineno", 0) or 0)
                if lineno <= 0:
                    continue
                cpu_percent = float(ln.get("n_cpu_percent_python", 0.0) or 0.0) + float(ln.get("n_cpu_percent_c", 0.0) or 0.0) + float(ln.get("n_sys_percent", 0.0) or 0.0)
                if cpu_percent <= 0:
                    continue
                key = (stage, rel, lineno)
                bucket = grouped_hotspots.setdefault(
                    key,
                    {
                        "cpu_percent": 0.0,
                        "peak_mb": 0.0,
                        "malloc_mb": 0.0,
                        "code": str(ln.get("line", "")).strip(),
                    },
                )
                bucket["cpu_percent"] += cpu_percent
                bucket["peak_mb"] = max(bucket["peak_mb"], float(ln.get("n_peak_mb", 0.0) or 0.0))
                bucket["malloc_mb"] += float(ln.get("n_malloc_mb", 0.0) or 0.0)

        stage_filtered_cpu[stage].append(filtered_cpu_percent)

    summaries: list[ScaleneStageSummary] = []
    for stage in STAGES:
        elapsed = stage_elapsed.get(stage, [])
        footprint = stage_footprint.get(stage, [])
        filtered_cpu = stage_filtered_cpu.get(stage, [])
        summaries.append(
            ScaleneStageSummary(
                library=library,
                stage=stage,
                sample_count=len(elapsed),
                mean_elapsed_ms=mean(elapsed) if elapsed else 0.0,
                mean_max_footprint_mb=mean(footprint) if footprint else 0.0,
                mean_filtered_cpu_percent=mean(filtered_cpu) if filtered_cpu else 0.0,
            )
        )

    by_stage: dict[str, list[ScaleneHotspot]] = defaultdict(list)
    for (stage, filename, line), vals in grouped_hotspots.items():
        by_stage[stage].append(
            ScaleneHotspot(
                library=library,
                stage=stage,
                filename=filename,
                line=line,
                code=vals["code"],
                cpu_percent=vals["cpu_percent"],
                peak_mb=vals["peak_mb"],
                malloc_mb=vals["malloc_mb"],
            )
        )

    hotspots: list[ScaleneHotspot] = []
    for stage in STAGES:
        hotspots.extend(sorted(by_stage.get(stage, []), key=lambda x: x.cpu_percent, reverse=True)[:top_n])

    return summaries, hotspots


def speedup_vs_reference(stage_timings: list[StageTiming], reference: str, support_map: dict[str, dict[str, bool]]) -> dict[str, dict[str, float | None]]:
    idx = {(x.library, x.stage): x for x in stage_timings}
    out: dict[str, dict[str, float | None]] = defaultdict(dict)
    libs = sorted({x.library for x in stage_timings})
    for lib in libs:
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                out[lib][stage] = None
                continue
            cur = idx.get((lib, stage))
            ref = idx.get((reference, stage))
            if not cur or not ref or cur.sample_count == 0 or ref.sample_count == 0 or cur.mean_per_repeat_ms == 0:
                out[lib][stage] = None
            else:
                out[lib][stage] = ref.mean_per_repeat_ms / cur.mean_per_repeat_ms
    return out


def memory_ratio_vs_reference(memory_stats: list[MemorySummary], reference: str, support_map: dict[str, dict[str, bool]]) -> dict[str, dict[str, float | None]]:
    idx = {(x.library, x.stage): x for x in memory_stats}
    out: dict[str, dict[str, float | None]] = defaultdict(dict)
    libs = sorted({x.library for x in memory_stats})
    for lib in libs:
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                out[lib][stage] = None
                continue
            cur = idx.get((lib, stage))
            ref = idx.get((reference, stage))
            if not cur or not ref or cur.sample_count == 0 or ref.sample_count == 0 or ref.mean_peak_mb == 0:
                out[lib][stage] = None
            else:
                out[lib][stage] = cur.mean_peak_mb / ref.mean_peak_mb
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
    memory_stats: list[MemorySummary],
    line_bottlenecks: list[Bottleneck],
    scalene_summaries: list[ScaleneStageSummary],
    scalene_hotspots: list[ScaleneHotspot],
    profiler_durations: list[ProfilerDuration],
    speedups: dict[str, dict[str, float | None]],
    memory_ratios: dict[str, dict[str, float | None]],
    support_map: dict[str, dict[str, bool]],
    support_source: str | None,
    include_scalene: bool,
) -> str:
    lines: list[str] = [
        "# Postprocessing analysis of profiling runs",
        "_Постобработка результатов профилирования_",
        "",
        f"Reference library: `{reference}`",
        f"Path filter mode: `{path_mode}`",
        f"Support source: `{support_source}`" if support_source else "Support source: `not_found` (all stages treated as supported)",
        "",
    ]
    libs = sorted({x.library for x in stage_timings})

    # CPU
    lines += ["## CPU", "_Процессорное время (CPU)_", "", "### Stage timings from CPU profiler metadata (mean per repeat, ms)", "_Тайминги этапов из метаданных CPU-профайлера (среднее на повтор, мс)_", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = []
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                vals.append("n/s")
                continue
            rec = next((x for x in stage_timings if x.library == lib and x.stage == stage), None)
            vals.append("n/a" if rec is None or rec.sample_count == 0 else f"{rec.mean_per_repeat_ms:.2f}")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines += ["", "### Mean step repeat count captured from CPU metadata", "_Среднее число повторов этапа из метаданных CPU_", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = []
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                vals.append("n/s")
                continue
            rec = next((x for x in stage_timings if x.library == lib and x.stage == stage), None)
            vals.append("n/a" if rec is None or rec.sample_count == 0 else f"{rec.mean_step_repeat_count:.2f}")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines += ["", "### Relative speedup vs reference (reference_time / lib_time)", "_Относительное ускорение относительно эталона (time_ref / time_lib)_", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = []
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                vals.append("n/s")
            else:
                sp = speedups.get(lib, {}).get(stage)
                vals.append("n/a" if sp is None else f"{sp:.2f}x")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    # Memory
    lines += ["", "## Memory", "_Память_", "", "### Peak memory by stage (MB)", "_Пиковое потребление памяти по этапам (МБ)_", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = []
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                vals.append("n/s")
                continue
            rec = next((x for x in memory_stats if x.library == lib and x.stage == stage), None)
            vals.append("n/a" if rec is None or rec.sample_count == 0 else f"{rec.mean_peak_mb:.2f}")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines += ["", "### Relative memory vs reference (lib_peak / ref_peak)", "_Относительная память относительно эталона (peak_lib / peak_ref)_", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---:|---:|---:|---:|"]
    for lib in libs:
        vals = []
        for stage in STAGES:
            if not support_map.get(lib, {}).get(stage, True):
                vals.append("n/s")
            else:
                ratio = memory_ratios.get(lib, {}).get(stage)
                vals.append("n/a" if ratio is None else f"{ratio:.2f}x")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    # Line
    lines += ["", "## Line", "_Построчный профиль (line profiler)_", "", "### Bottlenecks from line profiler (filtered, supported stages only)", "_Узкие места из line profiler (после фильтрации, только поддерживаемые этапы)_", "", "| Library | Stage | File:Line | Total time (s) | Hits | Code |", "|---|---|---|---:|---:|---|"]
    for b in sorted(line_bottlenecks, key=lambda x: (x.library, x.stage, -x.total_time_s)):
        code = b.code.replace('|', '\\|')
        lines.append(f"| {b.library} | {b.stage} | `{b.filename}:{b.line}` | {b.total_time_s:.4f} | {b.hits} | `{code}` |")

    # Scalene
    if include_scalene:
        lines += ["", "## Scalene", "_Scalene-профайлер_", "", "### Stage summary (filtered library files)", "_Сводка по этапам (фильтр по файлам библиотеки)_", "", "| Library | Stage | Samples | Mean elapsed (ms) | Mean max footprint (MB) | Mean filtered CPU % |", "|---|---|---:|---:|---:|---:|"]
        for rec in sorted(scalene_summaries, key=lambda x: (x.library, x.stage)):
            sup = support_map.get(rec.library, {}).get(rec.stage, True)
            if not sup:
                lines.append(f"| {rec.library} | {rec.stage} | n/s | n/s | n/s | n/s |")
            else:
                lines.append(f"| {rec.library} | {rec.stage} | {rec.sample_count} | {rec.mean_elapsed_ms:.2f} | {rec.mean_max_footprint_mb:.2f} | {rec.mean_filtered_cpu_percent:.2f} |")

        lines += ["", "### Top hotspots by CPU % (filtered library files)", "_Топ горячих строк по CPU % (с фильтром по файлам библиотеки)_", "", "| Library | Stage | File:Line | CPU % | Peak MB | Malloc MB | Code |", "|---|---|---|---:|---:|---:|---|"]
        for h in sorted(scalene_hotspots, key=lambda x: (x.library, x.stage, -x.cpu_percent)):
            code = h.code.replace('|', '\\|')
            lines.append(f"| {h.library} | {h.stage} | `{h.filename}:{h.line}` | {h.cpu_percent:.2f} | {h.peak_mb:.2f} | {h.malloc_mb:.2f} | `{code}` |")

    # Coverage / harness overhead
    lines += ["", "## Coverage", "_Покрытие и валидность сравнений_", "", "### Stage support matrix", "_Матрица поддержки этапов_", "", "| Library | Step1 | Step2 | Step3 | Step4 |", "|---|---|---|---|---|"]
    for lib in libs:
        vals = ["supported" if support_map.get(lib, {}).get(stage, True) else "not_supported" for stage in STAGES]
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines += ["", "### Profiler duration coverage (profiling overhead)", "_Покрытие длительностей профайлеров (накладные расходы профилирования)_", "", "| Library | Profiler | Stage | Support | Samples | Mean duration (ms) | Std (ms) |", "|---|---|---|---|---:|---:|---:|"]
    for rec in sorted(profiler_durations, key=lambda x: (x.library, x.profiler, x.stage)):
        supported = support_map.get(rec.library, {}).get(rec.stage, True)
        sup = "supported" if supported else "not_supported (instrumentation only / excluded from comparison)"
        lines.append(f"| {rec.library} | {rec.profiler} | {rec.stage} | {sup} | {rec.sample_count} | {rec.mean_duration_ms:.2f} | {rec.std_duration_ms:.2f} |")

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
    parser.add_argument(
        "--include-scalene",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Включать секцию Scalene в markdown-отчет (по умолчанию: включена)",
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    libraries = discover_libraries(base_dir) if args.libraries.lower() == "all" else [x.strip() for x in args.libraries.split(",") if x.strip()]
    if not libraries:
        raise ValueError("Не найдено библиотек для анализа")
    if args.reference not in libraries:
        libraries.insert(0, args.reference)

    support_map, support_source = build_supported_map(base_dir, args.reference, libraries)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = base_dir / "processed_results" / "postprocessing_analysis" / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    all_stage_timings: list[StageTiming] = []
    all_profiler_durations: list[ProfilerDuration] = []
    all_memory: list[MemorySummary] = []
    all_line_bottlenecks: list[Bottleneck] = []
    all_scalene_summaries: list[ScaleneStageSummary] = []
    all_scalene_hotspots: list[ScaleneHotspot] = []
    run_paths: dict[str, str] = {}

    for lib in libraries:
        run_dir = latest_run_dir(base_dir, lib)
        run_paths[lib] = str(run_dir)
        all_stage_timings.extend(build_stage_timings_from_cpu(run_dir, lib))
        all_profiler_durations.extend(collect_profiler_durations(run_dir, lib))
        all_memory.extend(collect_memory_stats(run_dir, lib))
        all_line_bottlenecks.extend(collect_line_bottlenecks(run_dir, lib, top_n=args.top_lines, path_mode=args.path_filter, support_map=support_map))
        s_summary, s_hotspots = collect_scalene_stats(run_dir, lib, top_n=args.top_lines, path_mode=args.path_filter, support_map=support_map)
        all_scalene_summaries.extend(s_summary)
        all_scalene_hotspots.extend(s_hotspots)

    speedups = speedup_vs_reference(all_stage_timings, args.reference, support_map)
    memory_ratios = memory_ratio_vs_reference(all_memory, args.reference, support_map)

    timings_rows = []
    for x in sorted(all_stage_timings, key=lambda i: (i.library, i.stage)):
        supported = support_map.get(x.library, {}).get(x.stage, True)
        timings_rows.append(
            {
                "library": x.library,
                "stage": x.stage,
                "supported": supported,
                "sample_count": x.sample_count,
                "mean_total_ms": round(x.mean_total_ms, 6),
                "std_total_ms": round(x.std_total_ms, 6),
                "mean_per_repeat_ms": round(x.mean_per_repeat_ms, 6),
                "mean_step_repeat_count": round(x.mean_step_repeat_count, 6),
                "source_profiler": x.source_profiler,
                "speedup_vs_reference": None if (not supported or speedups[x.library][x.stage] is None) else round(float(speedups[x.library][x.stage]), 6),
            }
        )

    duration_rows = [
        {
            "library": x.library,
            "profiler": x.profiler,
            "stage": x.stage,
            "supported": support_map.get(x.library, {}).get(x.stage, True),
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
            "supported": support_map.get(x.library, {}).get(x.stage, True),
            "sample_count": x.sample_count,
            "mean_peak_mb": round(x.mean_peak_mb, 6),
            "max_peak_mb": round(x.max_peak_mb, 6),
            "memory_ratio_vs_reference": None if (not support_map.get(x.library, {}).get(x.stage, True) or memory_ratios[x.library][x.stage] is None) else round(float(memory_ratios[x.library][x.stage]), 6),
        }
        for x in sorted(all_memory, key=lambda i: (i.library, i.stage))
    ]
    line_rows = [
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
        for x in sorted(all_line_bottlenecks, key=lambda i: (i.library, i.stage, -i.total_time_s))
    ]
    scalene_summary_rows = [
        {
            "library": x.library,
            "stage": x.stage,
            "supported": support_map.get(x.library, {}).get(x.stage, True),
            "sample_count": x.sample_count,
            "mean_elapsed_ms": round(x.mean_elapsed_ms, 6),
            "mean_max_footprint_mb": round(x.mean_max_footprint_mb, 6),
            "mean_filtered_cpu_percent": round(x.mean_filtered_cpu_percent, 6),
        }
        for x in sorted(all_scalene_summaries, key=lambda i: (i.library, i.stage))
    ]
    scalene_hotspot_rows = [
        {
            "library": x.library,
            "stage": x.stage,
            "filename": x.filename,
            "line": x.line,
            "cpu_percent": round(x.cpu_percent, 6),
            "peak_mb": round(x.peak_mb, 6),
            "malloc_mb": round(x.malloc_mb, 6),
            "code": x.code,
        }
        for x in sorted(all_scalene_hotspots, key=lambda i: (i.library, i.stage, -i.cpu_percent))
    ]

    write_csv(
        out_dir / "stage_timings.csv",
        timings_rows,
        [
            "library",
            "stage",
            "supported",
            "sample_count",
            "mean_total_ms",
            "std_total_ms",
            "mean_per_repeat_ms",
            "mean_step_repeat_count",
            "source_profiler",
            "speedup_vs_reference",
        ],
    )
    write_csv(out_dir / "profiler_durations.csv", duration_rows, ["library", "profiler", "stage", "supported", "sample_count", "mean_duration_ms", "std_duration_ms"])
    write_csv(out_dir / "memory_stage_summary.csv", memory_rows, ["library", "stage", "supported", "sample_count", "mean_peak_mb", "max_peak_mb", "memory_ratio_vs_reference"])
    write_csv(out_dir / "line_bottlenecks.csv", line_rows, ["library", "stage", "profiler", "filename", "line", "total_time_s", "hits", "code"])
    write_csv(out_dir / "scalene_stage_summary.csv", scalene_summary_rows, ["library", "stage", "supported", "sample_count", "mean_elapsed_ms", "mean_max_footprint_mb", "mean_filtered_cpu_percent"])
    write_csv(out_dir / "scalene_hotspots.csv", scalene_hotspot_rows, ["library", "stage", "filename", "line", "cpu_percent", "peak_mb", "malloc_mb", "code"])

    report_md = build_markdown_report(
        reference=args.reference,
        path_mode=args.path_filter,
        stage_timings=all_stage_timings,
        memory_stats=all_memory,
        line_bottlenecks=all_line_bottlenecks,
        scalene_summaries=all_scalene_summaries,
        scalene_hotspots=all_scalene_hotspots,
        profiler_durations=all_profiler_durations,
        speedups=speedups,
        memory_ratios=memory_ratios,
        support_map=support_map,
        support_source=support_source,
        include_scalene=args.include_scalene,
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
            "support_source": support_source,
        },
        "stage_support": support_map,
        "stage_timings": timings_rows,
        "memory_ratio_vs_reference": memory_ratios,
        "profiler_durations": duration_rows,
        "memory_summary": memory_rows,
        "line_bottlenecks": line_rows,
        "scalene_stage_summary": scalene_summary_rows,
        "scalene_hotspots": scalene_hotspot_rows,
    }
    (out_dir / "analysis_report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Analysis artifacts saved to: {out_dir}")
    print(f" - {out_dir / 'analysis_report.md'}")
    print(f" - {out_dir / 'analysis_report.json'}")
    print(f" - {out_dir / 'stage_timings.csv'}")
    print(f" - {out_dir / 'profiler_durations.csv'}")
    print(f" - {out_dir / 'memory_stage_summary.csv'}")
    print(f" - {out_dir / 'line_bottlenecks.csv'}")
    print(f" - {out_dir / 'scalene_stage_summary.csv'}")
    print(f" - {out_dir / 'scalene_hotspots.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
