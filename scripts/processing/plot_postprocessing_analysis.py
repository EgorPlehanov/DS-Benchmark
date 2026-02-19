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
STAGE_COLORS = {
    "step1": "#1f77b4",
    "step2": "#ff7f0e",
    "step3": "#2ca02c",
    "step4": "#d62728",
}


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s in {"", "nan", "none", "null"}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def draw_heatmap(
    matrix: np.ndarray,
    row_labels: List[str],
    col_labels: List[str],
    title: str,
    cbar_label: str,
    out_path: Path,
    cmap: str = "viridis",
    value_fmt: str = ".2f",
) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.4))
    im = ax.imshow(matrix, aspect="auto", cmap=cmap)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels)
    ax.set_yticklabels(row_labels)
    ax.set_title(title)

    matrix_mean = np.nanmean(matrix) if not np.all(np.isnan(matrix)) else 0.0

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            text = "n/s" if np.isnan(value) else format(value, value_fmt)
            color = "white" if not np.isnan(value) and value > matrix_mean else "black"
            ax.text(j, i, text, ha="center", va="center", color=color, fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def build_stage_matrices(rows: List[dict], value_key: str) -> Tuple[List[str], List[str], np.ndarray]:
    libs = order_libraries(rows)
    stages = STAGE_ORDER.copy()
    matrix = np.full((len(libs), len(stages)), np.nan)

    idx_lib = {lib: i for i, lib in enumerate(libs)}
    idx_stage = {stage: i for i, stage in enumerate(stages)}

    for row in rows:
        lib = row.get("library")
        stage = row.get("stage")
        supported = parse_bool(row.get("supported", "true"))
        if not lib or not stage or not supported or lib not in idx_lib or stage not in idx_stage:
            continue
        value = safe_float(row.get(value_key))
        if value is None:
            continue
        matrix[idx_lib[lib], idx_stage[stage]] = value

    return libs, stages, matrix


def plot_grouped_by_stage(
    rows: List[dict],
    metric_key: str,
    ylabel: str,
    title: str,
    out_path: Path,
    reference_line: float | None = None,
    inverse: bool = False,
) -> None:
    filtered = [r for r in rows if parse_bool(r.get("supported", "true"))]
    libs = order_libraries(filtered)
    stages = STAGE_ORDER.copy()

    values = defaultdict(dict)
    for row in filtered:
        value = safe_float(row.get(metric_key))
        if value is None:
            continue
        if inverse and value != 0:
            value = 1.0 / value
        values[row["stage"]][row["library"]] = value

    fig, ax = plt.subplots(figsize=(11, 5.6))
    width = 0.18
    x = np.arange(len(libs))

    for i, stage in enumerate(stages):
        y = [values[stage].get(lib, np.nan) for lib in libs]
        ax.bar(x + (i - 1.5) * width, y, width=width, label=stage)

    if reference_line is not None:
        ax.axhline(reference_line, color="black", linestyle="--", linewidth=1, label="reference=1x")

    ax.set_xticks(x)
    ax.set_xticklabels(libs)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(ncols=3, fontsize=8)
    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def select_primary_file_for_library(rows: List[dict], library: str) -> str | None:
    totals = defaultdict(float)
    for row in rows:
        if row.get("library") != library:
            continue
        filename = row.get("filename")
        if not filename:
            continue
        value = safe_float(row.get("total_time_s"))
        if value is None:
            continue
        totals[filename] += value
    if not totals:
        return None
    return max(totals, key=totals.get)


def plot_line_bottlenecks_library_sorted_by_line(rows: List[dict], library: str, out_path: Path, top_n: int = 25) -> None:
    primary_file = select_primary_file_for_library(rows, library)

    data = []
    for row in rows:
        if row.get("library") != library:
            continue
        if primary_file and row.get("filename") != primary_file:
            continue
        line_no = int(row.get("line", 0) or 0)
        total_s = safe_float(row.get("total_time_s"))
        if line_no <= 0 or total_s is None:
            continue
        stage = row.get("stage", "unknown")
        code = row.get("code", "")
        data.append((line_no, total_s, stage, code))

    if not data:
        return

    # Sort by line number (requested), keep only top_n first entries by line order.
    data.sort(key=lambda x: x[0])
    data = data[:top_n]

    labels = [f"L{line}: {code}" for line, _, _, code in data]
    values = [t for _, t, _, _ in data]
    colors = [STAGE_COLORS.get(stage, "gray") for _, _, stage, _ in data]

    fig, ax = plt.subplots(figsize=(13, 8))
    y = np.arange(len(labels))
    ax.barh(y, values, color=colors)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("total line time (s)")

    file_label = Path(primary_file).as_posix() if primary_file else "all files"
    ax.set_title(f"{library}: line bottlenecks sorted by line number ({file_label})")

    legend_handles = [
        plt.Line2D([0], [0], color=STAGE_COLORS[s], lw=6, label=s)
        for s in STAGE_ORDER
    ]
    ax.legend(handles=legend_handles, title="stage", fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def plot_line_timing_by_library_subplots(rows: List[dict], out_path: Path, top_lines: int = 15) -> None:
    libs = order_libraries(rows)
    if not libs:
        return

    per_lib_data: Dict[str, List[Tuple[int, float, str]]] = {}
    for lib in libs:
        primary = select_primary_file_for_library(rows, lib)
        if not primary:
            continue
        entries = []
        for row in rows:
            if row.get("library") != lib or row.get("filename") != primary:
                continue
            line_no = int(row.get("line", 0) or 0)
            total_s = safe_float(row.get("total_time_s"))
            if line_no <= 0 or total_s is None:
                continue
            entries.append((line_no, total_s, row.get("stage", "unknown")))

        if entries:
            entries.sort(key=lambda x: x[0])
            per_lib_data[lib] = entries[:top_lines]

    if not per_lib_data:
        return

    lib_list = list(per_lib_data.keys())
    fig, axes = plt.subplots(len(lib_list), 1, figsize=(13, 3.1 * len(lib_list)), squeeze=False)

    for i, lib in enumerate(lib_list):
        ax = axes[i][0]
        entries = per_lib_data[lib]
        y = np.arange(len(entries))
        labels = [f"L{ln}" for ln, _, _ in entries]
        values = [t for _, t, _ in entries]
        colors = [STAGE_COLORS.get(stage, "gray") for _, _, stage in entries]

        ax.barh(y, values, color=colors)
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.invert_yaxis()
        ax.set_xlabel("total line time (s)")
        ax.set_title(f"{lib}: lines sorted by line number (library-specific file)")

    legend_handles = [plt.Line2D([0], [0], color=STAGE_COLORS[s], lw=6, label=s) for s in STAGE_ORDER]
    axes[0][0].legend(handles=legend_handles, title="stage", fontsize=8)

    plt.tight_layout()
    fig.savefig(out_path, dpi=180)
    plt.close(fig)


def build_plot_summary(plot_dir: Path, analysis_dir: Path, line_library: str) -> Path:
    summary_path = plot_dir / "plot_summary.md"
    lines = [
        "# Profiling plots summary / Сводка графиков профилирования",
        "",
        f"Source analysis directory / Исходная директория анализа: `{analysis_dir.as_posix()}`",
        "",
        "## English",
        "Generated plots:",
        "- `cpu_absolute_heatmap.png` — absolute CPU stage timings (ms).",
        "- `cpu_relative_heatmap.png` — relative CPU speedup vs reference (x).",
        "- `speedup_grouped_bar.png` — grouped speedup bars by stage (CPU).",
        "- `memory_absolute_heatmap.png` — absolute memory peak by stage (MB).",
        "- `memory_relative_heatmap.png` — relative memory ratio vs reference (x).",
        "- `memory_efficiency_grouped_bar.png` — grouped memory efficiency bars (`ref/lib`).",
        "- `line_bottlenecks_library_sorted_by_line.png` — line bottlenecks for selected library with stage colors, full code line labels, sorted by line number.",
        "- `line_timing_by_library_subplots.png` — one subplot per library, lines sorted by line number inside each library-specific file.",
        f"- Line-library focus: `{line_library}`.",
        "",
        "## Русский",
        "Сформированные графики:",
        "- `cpu_absolute_heatmap.png` — абсолютные CPU-тайминги по этапам (мс).",
        "- `cpu_relative_heatmap.png` — относительное ускорение CPU относительно эталона (x).",
        "- `speedup_grouped_bar.png` — группированный график ускорения по этапам (CPU).",
        "- `memory_absolute_heatmap.png` — абсолютные пиковые значения памяти по этапам (МБ).",
        "- `memory_relative_heatmap.png` — относительное потребление памяти к эталону (x).",
        "- `memory_efficiency_grouped_bar.png` — группированный график эффективности памяти (`ref/lib`).",
        "- `line_bottlenecks_library_sorted_by_line.png` — узкие места по строкам для выбранной библиотеки: цвет зависит от этапа, подпись содержит полный код строки, сортировка по номеру строки.",
        "- `line_timing_by_library_subplots.png` — отдельные подграфики по библиотекам, строки отсортированы по номеру внутри файла конкретной библиотеки.",
        f"- Фокус по библиотеке для строк: `{line_library}`.",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot profiling postprocessing artifacts")
    parser.add_argument("--base-dir", default="results/profiling/processed_results/postprocessing_analysis", help="Base directory with timestamped postprocessing outputs")
    parser.add_argument("--analysis-dir", default=None, help="Specific postprocessing analysis directory; if omitted latest is used")
    parser.add_argument("--out-dir", default=None, help="Directory for plots (default: <analysis-dir>/plots)")
    parser.add_argument("--top-lines", type=int, default=20, help="How many line bottlenecks to include")
    parser.add_argument("--line-library", default="our", help="Library to focus in line-level sorted-by-line chart")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else latest_analysis_dir(base_dir)
    out_dir = Path(args.out_dir) if args.out_dir else analysis_dir / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    stage_rows = read_csv_rows(analysis_dir / "stage_timings.csv")
    mem_rows = read_csv_rows(analysis_dir / "memory_stage_summary.csv")
    line_rows = read_csv_rows(analysis_dir / "line_bottlenecks.csv")

    libs, stages, cpu_abs = build_stage_matrices(stage_rows, "mean_per_repeat_ms")
    draw_heatmap(
        cpu_abs,
        libs,
        stages,
        "CPU stage timings (absolute, mean per repeat, ms)",
        "ms",
        out_dir / "cpu_absolute_heatmap.png",
        cmap="YlGnBu",
    )

    libs, stages, cpu_rel = build_stage_matrices(stage_rows, "speedup_vs_reference")
    draw_heatmap(
        cpu_rel,
        libs,
        stages,
        "CPU stage timings (relative, speedup vs reference)",
        "ratio (x)",
        out_dir / "cpu_relative_heatmap.png",
        cmap="Blues",
    )

    plot_grouped_by_stage(
        stage_rows,
        metric_key="speedup_vs_reference",
        ylabel="speedup vs reference (x)",
        title="Relative CPU speedup by stage (supported only)",
        out_path=out_dir / "speedup_grouped_bar.png",
        reference_line=1.0,
    )

    mem_libs, mem_stages, mem_abs = build_stage_matrices(mem_rows, "mean_peak_mb")
    draw_heatmap(
        mem_abs,
        mem_libs,
        mem_stages,
        "Memory stage peaks (absolute, MB)",
        "MB",
        out_dir / "memory_absolute_heatmap.png",
        cmap="YlOrBr",
    )

    mem_libs, mem_stages, mem_rel = build_stage_matrices(mem_rows, "memory_ratio_vs_reference")
    draw_heatmap(
        mem_rel,
        mem_libs,
        mem_stages,
        "Memory stage usage (relative, lib/reference)",
        "ratio (x)",
        out_dir / "memory_relative_heatmap.png",
        cmap="OrRd",
    )

    plot_grouped_by_stage(
        mem_rows,
        metric_key="memory_ratio_vs_reference",
        ylabel="memory efficiency vs reference (ref/lib, x)",
        title="Relative memory efficiency by stage (supported only)",
        out_path=out_dir / "memory_efficiency_grouped_bar.png",
        reference_line=1.0,
        inverse=True,
    )

    plot_line_bottlenecks_library_sorted_by_line(
        line_rows,
        library=args.line_library,
        out_path=out_dir / "line_bottlenecks_library_sorted_by_line.png",
        top_n=args.top_lines,
    )

    plot_line_timing_by_library_subplots(
        line_rows,
        out_path=out_dir / "line_timing_by_library_subplots.png",
        top_lines=args.top_lines,
    )

    build_plot_summary(out_dir, analysis_dir, args.line_library)
    print(f"Plots saved to: {out_dir}")


if __name__ == "__main__":
    main()
