#!/usr/bin/env python3
"""Builds visual analytics plots from postprocessing profiling artifacts."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import matplotlib.pyplot as plt
import numpy as np


STAGE_ORDER = ["step1", "step2", "step3", "step4"]


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_csv_rows(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def latest_analysis_dir(base_dir: Path) -> Path:
    dirs = sorted([p for p in base_dir.iterdir() if p.is_dir()])
    if not dirs:
        raise FileNotFoundError(f"No analysis directories found in: {base_dir}")
    return dirs[-1]


def order_libraries(rows: Iterable[dict]) -> List[str]:
    libs = sorted({row["library"] for row in rows})
    if "our" in libs:
        libs.remove("our")
        libs.insert(0, "our")
    return libs


def draw_heatmap(matrix: np.ndarray, row_labels: List[str], col_labels: List[str], title: str, cbar_label: str, out_path: Path, cmap: str = "viridis") -> None:
    fig, ax = plt.subplots(figsize=(10, 5.2))
    im = ax.imshow(matrix, aspect="auto", cmap=cmap)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    ax.set_title(title)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            text = "n/s" if np.isnan(value) else f"{value:.2f}"
            ax.text(j, i, text, ha="center", va="center", color="white" if not np.isnan(value) and value > np.nanmean(matrix) else "black", fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def build_stage_matrices(rows: List[dict], value_key: str) -> Tuple[List[str], List[str], np.ndarray]:
    libs = order_libraries(rows)
    stage_labels = STAGE_ORDER.copy()
    matrix = np.full((len(libs), len(stage_labels)), np.nan)

    index_lib = {lib: i for i, lib in enumerate(libs)}
    index_stage = {stage: i for i, stage in enumerate(stage_labels)}

    for row in rows:
        lib = row["library"]
        stage = row["stage"]
        supported = parse_bool(row.get("supported", "true"))
        if lib not in index_lib or stage not in index_stage or not supported:
            continue
        try:
            matrix[index_lib[lib], index_stage[stage]] = float(row[value_key])
        except (TypeError, ValueError):
            continue
    return libs, stage_labels, matrix


def plot_speedup(rows: List[dict], out_path: Path) -> None:
    filtered = [r for r in rows if parse_bool(r.get("supported", "true")) and r.get("speedup_vs_reference") not in {"", "nan", "None"}]
    libs = order_libraries(filtered)
    stages = STAGE_ORDER.copy()

    values = defaultdict(dict)
    for row in filtered:
        try:
            values[row["stage"]][row["library"]] = float(row["speedup_vs_reference"])
        except (TypeError, ValueError):
            pass

    fig, ax = plt.subplots(figsize=(11, 5.5))
    width = 0.18
    x = np.arange(len(libs))

    for i, stage in enumerate(stages):
        y = [values[stage].get(lib, np.nan) for lib in libs]
        ax.bar(x + (i - 1.5) * width, y, width=width, label=stage)

    ax.axhline(1.0, color="black", linestyle="--", linewidth=1, label="reference=1x")
    ax.set_xticks(x)
    ax.set_xticklabels(libs)
    ax.set_ylabel("speedup vs reference (x)")
    ax.set_title("Relative CPU speedup by stage (supported only)")
    ax.legend(ncols=3, fontsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_profiler_overhead(rows: List[dict], out_path: Path) -> None:
    filtered = [r for r in rows if parse_bool(r.get("supported", "true"))]
    libs = order_libraries(filtered)
    profilers = sorted({r["profiler"] for r in filtered})

    agg: Dict[Tuple[str, str], float] = defaultdict(float)
    for row in filtered:
        try:
            agg[(row["library"], row["profiler"])] += float(row["mean_duration_ms"])
        except (TypeError, ValueError):
            continue

    fig, ax = plt.subplots(figsize=(11, 5.5))
    width = 0.18
    x = np.arange(len(libs))

    for i, profiler in enumerate(profilers):
        y = [agg.get((lib, profiler), np.nan) for lib in libs]
        ax.bar(x + (i - (len(profilers)-1)/2) * width, y, width=width, label=profiler)

    ax.set_xticks(x)
    ax.set_xticklabels(libs)
    ax.set_ylabel("sum mean duration across stages (ms)")
    ax.set_title("Profiling overhead by profiler and library")
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_line_bottlenecks(rows: List[dict], out_path: Path, top_n: int = 12) -> None:
    filtered = []
    for row in rows:
        try:
            value = float(row.get("total_time_s", 0.0))
        except (TypeError, ValueError):
            continue
        filtered.append((value, row))

    filtered.sort(key=lambda x: x[0], reverse=True)
    top = filtered[:top_n]
    if not top:
        return

    labels = [f"{r['library']}:{r['stage']}:{Path(r['filename']).name}:{r['line']}" for _, r in top]
    values = [v for v, _ in top]

    fig, ax = plt.subplots(figsize=(12, 6.5))
    y = np.arange(len(labels))
    ax.barh(y, values, color="tab:red")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("total line time (s)")
    ax.set_title(f"Top-{len(labels)} line-level bottlenecks")
    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def build_plot_summary(plot_dir: Path, analysis_dir: Path) -> Path:
    summary_path = plot_dir / "plot_summary.md"
    lines = [
        "# Profiling plots summary",
        "",
        f"Source analysis directory: `{analysis_dir.as_posix()}`",
        "",
        "Generated plots:",
        "- `stage_timing_heatmap.png` — absolute CPU stage timings (ms).",
        "- `speedup_grouped_bar.png` — speedup vs reference by stage.",
        "- `memory_ratio_heatmap.png` — memory ratio vs reference (x).",
        "- `profiler_overhead_grouped_bar.png` — summed profiler overhead by library.",
        "- `line_bottlenecks_top.png` — largest line-level hotspots by total time.",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot profiling postprocessing artifacts")
    parser.add_argument("--base-dir", default="results/profiling/processed_results/postprocessing_analysis", help="Base directory with timestamped postprocessing outputs")
    parser.add_argument("--analysis-dir", default=None, help="Specific postprocessing analysis directory; if omitted latest is used")
    parser.add_argument("--out-dir", default=None, help="Directory for plots (default: <analysis-dir>/plots)")
    parser.add_argument("--top-lines", type=int, default=12, help="How many line bottlenecks to plot")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else latest_analysis_dir(base_dir)
    out_dir = Path(args.out_dir) if args.out_dir else analysis_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    stage_rows = read_csv_rows(analysis_dir / "stage_timings.csv")
    mem_rows = read_csv_rows(analysis_dir / "memory_stage_summary.csv")
    duration_rows = read_csv_rows(analysis_dir / "profiler_durations.csv")
    line_rows = read_csv_rows(analysis_dir / "line_bottlenecks.csv")

    libs, stages, stage_matrix = build_stage_matrices(stage_rows, "mean_per_repeat_ms")
    draw_heatmap(
        stage_matrix,
        libs,
        stages,
        "CPU stage timing heatmap (mean per repeat, ms)",
        "ms",
        out_dir / "stage_timing_heatmap.png",
        cmap="YlGnBu",
    )

    plot_speedup(stage_rows, out_dir / "speedup_grouped_bar.png")

    mem_libs, mem_stages, mem_matrix = build_stage_matrices(mem_rows, "memory_ratio_vs_reference")
    draw_heatmap(
        mem_matrix,
        mem_libs,
        mem_stages,
        "Memory ratio vs reference by stage (supported only)",
        "ratio (x)",
        out_dir / "memory_ratio_heatmap.png",
        cmap="OrRd",
    )

    plot_profiler_overhead(duration_rows, out_dir / "profiler_overhead_grouped_bar.png")
    plot_line_bottlenecks(line_rows, out_dir / "line_bottlenecks_top.png", top_n=args.top_lines)
    build_plot_summary(out_dir, analysis_dir)

    print(f"Plots saved to: {out_dir}")


if __name__ == "__main__":
    main()
