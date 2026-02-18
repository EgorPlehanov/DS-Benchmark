#!/usr/bin/env python3
"""Постпроцессинг профилирования: агрегирование метрик, поиск узких мест, рекомендации."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


STAGES = ["step1", "step2", "step3", "step4"]


def normalize_stage(raw_stage: str) -> str:
    """Приводит stage вроде step1_original к базовому виду step1."""
    if not raw_stage:
        return ""
    return raw_stage.split("_", 1)[0]


@dataclass
class StageTiming:
    library: str
    stage: str
    sample_count: int
    mean_total_ms: float
    std_total_ms: float
    mean_per_repeat_ms: float
    success_rate: float
    applicable: int
    not_supported: int


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
    filename: str
    line: int
    code: str
    total_time_s: float
    hits: int


def discover_libraries(base_dir: Path) -> list[str]:
    libs = [p.name for p in base_dir.iterdir() if p.is_dir() and p.name != "processed_results"]
    return sorted(libs)


def latest_run_dir(base_dir: Path, library: str) -> Path:
    lib_dir = base_dir / library
    timestamps = sorted([p for p in lib_dir.iterdir() if p.is_dir()])
    if not timestamps:
        raise FileNotFoundError(f"Не найдено прогонов для библиотеки: {library}")
    return timestamps[-1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_stage_timings(run_summary: dict[str, Any], library: str) -> list[StageTiming]:
    out: list[StageTiming] = []
    steps = run_summary.get("statistics", {}).get("steps", {})
    for stage in STAGES:
        stage_stats = steps.get(stage, {})
        counts = stage_stats.get("counts", {})
        time_total = stage_stats.get("time_total_ms", {})
        time_repeat = stage_stats.get("time_per_repeat_ms", {})
        out.append(
            StageTiming(
                library=library,
                stage=stage,
                sample_count=int(time_total.get("sample_count", 0)),
                mean_total_ms=float(time_total.get("mean", 0.0)),
                std_total_ms=float(time_total.get("std", 0.0)),
                mean_per_repeat_ms=float(time_repeat.get("mean", 0.0)),
                success_rate=float(stage_stats.get("success_rate", 0.0)),
                applicable=int(counts.get("applicable", 0)),
                not_supported=int(counts.get("not_supported", 0)),
            )
        )
    return out


def collect_memory_stats(run_dir: Path, library: str) -> list[MemorySummary]:
    peaks: dict[str, list[float]] = defaultdict(list)
    mem_root = run_dir / "profilers" / "memory"
    for json_file in mem_root.glob("*/*.json"):
        payload = load_json(json_file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES:
            continue
        peak_bytes = payload.get("data", {}).get("peak_memory_bytes", 0)
        peaks[stage].append(float(peak_bytes) / (1024 * 1024))

    summaries: list[MemorySummary] = []
    for stage in STAGES:
        values = peaks.get(stage, [])
        if values:
            summaries.append(
                MemorySummary(
                    library=library,
                    stage=stage,
                    sample_count=len(values),
                    mean_peak_mb=sum(values) / len(values),
                    max_peak_mb=max(values),
                )
            )
        else:
            summaries.append(MemorySummary(library=library, stage=stage, sample_count=0, mean_peak_mb=0.0, max_peak_mb=0.0))
    return summaries


def collect_line_bottlenecks(run_dir: Path, library: str, top_n: int) -> list[Bottleneck]:
    grouped: dict[tuple[str, str, int], dict[str, Any]] = {}
    line_root = run_dir / "profilers" / "line"

    for json_file in line_root.glob("*/*.json"):
        payload = load_json(json_file)
        stage = normalize_stage(str(payload.get("step", "")))
        if stage not in STAGES:
            continue
        for line_info in payload.get("data", {}).get("top_lines", []):
            filename = str(line_info.get("filename", ""))
            line = int(line_info.get("line", 0))
            key = (stage, filename, line)
            bucket = grouped.setdefault(
                key,
                {
                    "total_time_s": 0.0,
                    "hits": 0,
                    "code": str(line_info.get("code", "")).strip(),
                },
            )
            bucket["total_time_s"] += float(line_info.get("total_time", 0.0))
            bucket["hits"] += int(line_info.get("hits", 0))

    by_stage: dict[str, list[Bottleneck]] = defaultdict(list)
    for (stage, filename, line), stats in grouped.items():
        by_stage[stage].append(
            Bottleneck(
                library=library,
                stage=stage,
                filename=filename,
                line=line,
                code=stats["code"],
                total_time_s=stats["total_time_s"],
                hits=stats["hits"],
            )
        )

    top: list[Bottleneck] = []
    for stage in STAGES:
        top.extend(sorted(by_stage.get(stage, []), key=lambda x: x.total_time_s, reverse=True)[:top_n])
    return top


def speedup_vs_reference(stage_timings: list[StageTiming], reference: str) -> dict[str, dict[str, float | None]]:
    ref_map = {(x.library, x.stage): x for x in stage_timings}
    result: dict[str, dict[str, float | None]] = defaultdict(dict)
    libs = sorted({x.library for x in stage_timings})
    for lib in libs:
        for stage in STAGES:
            cur = ref_map.get((lib, stage))
            ref = ref_map.get((reference, stage))
            if not cur or not ref or cur.sample_count == 0 or ref.sample_count == 0:
                result[lib][stage] = None
            else:
                if cur.mean_per_repeat_ms == 0:
                    result[lib][stage] = None
                else:
                    result[lib][stage] = ref.mean_per_repeat_ms / cur.mean_per_repeat_ms
    return result


def write_csv(path: Path, rows: list[dict[str, Any]], headers: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def build_markdown_report(
    reference: str,
    stage_timings: list[StageTiming],
    memory_stats: list[MemorySummary],
    bottlenecks: list[Bottleneck],
    speedups: dict[str, dict[str, float | None]],
) -> str:
    lines: list[str] = []
    lines.append("# Postprocessing analysis of profiling runs")
    lines.append("")
    lines.append(f"Reference library: `{reference}`")
    lines.append("")

    lines.append("## 1) Stage timings (mean per repeat, ms)")
    lines.append("")
    lines.append("| Library | Step1 | Step2 | Step3 | Step4 |")
    lines.append("|---|---:|---:|---:|---:|")
    libs = sorted({x.library for x in stage_timings})
    for lib in libs:
        vals = []
        for stage in STAGES:
            rec = next((x for x in stage_timings if x.library == lib and x.stage == stage), None)
            if rec is None or rec.sample_count == 0:
                vals.append("n/a")
            else:
                vals.append(f"{rec.mean_per_repeat_ms:.2f}")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines.append("")
    lines.append("## 2) Relative speedup vs reference (reference_time / lib_time)")
    lines.append("")
    lines.append("| Library | Step1 | Step2 | Step3 | Step4 |")
    lines.append("|---|---:|---:|---:|---:|")
    for lib in libs:
        vals: list[str] = []
        for stage in STAGES:
            sp = speedups.get(lib, {}).get(stage)
            vals.append("n/a" if sp is None else f"{sp:.2f}x")
        lines.append(f"| {lib} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} |")

    lines.append("")
    lines.append("## 3) Peak memory by stage (MB)")
    lines.append("")
    lines.append("| Library | Stage | Mean peak | Max peak | Samples |")
    lines.append("|---|---|---:|---:|---:|")
    for rec in sorted(memory_stats, key=lambda x: (x.library, x.stage)):
        if rec.sample_count == 0:
            lines.append(f"| {rec.library} | {rec.stage} | n/a | n/a | 0 |")
        else:
            lines.append(f"| {rec.library} | {rec.stage} | {rec.mean_peak_mb:.2f} | {rec.max_peak_mb:.2f} | {rec.sample_count} |")

    lines.append("")
    lines.append("## 4) Bottlenecks from line profiler")
    lines.append("")
    lines.append("| Library | Stage | File:Line | Total time (s) | Hits | Code |")
    lines.append("|---|---|---|---:|---:|---|")
    for row in sorted(bottlenecks, key=lambda x: (x.library, x.stage, -x.total_time_s)):
        short = Path(row.filename).as_posix().split("DS-Benchmark/")[-1]
        code = row.code.replace("|", "\\|")
        lines.append(
            f"| {row.library} | {row.stage} | `{short}:{row.line}` | {row.total_time_s:.4f} | {row.hits} | `{code}` |"
        )

    lines.append("")
    lines.append("## 5) Practical postprocessing recommendations")
    lines.append("")
    lines.append("1. **Разделяйте сравнение на два среза**: (a) только поддерживаемые этапы, (b) полный пайплайн с учетом `not_supported`. Это важно для честного сравнения библиотек с разной функциональностью.")
    lines.append("2. **Для статьи фиксируйте две оси качества**: correctness (из `comparison_report`) и performance (данный отчет). Нельзя интерпретировать ускорение без учета расхождения результатов.")
    lines.append("3. **Узкие места валидируйте micro-benchmark'ами**: для топ-строк из таблицы bottlenecks сделайте изолированные тесты и проверьте влияние оптимизаций отдельно от I/O и сериализации.")
    lines.append("4. **Добавьте визуализации в ноутбук/статью** на основе `stage_timings.csv`, `memory_stage_summary.csv` и `line_bottlenecks.csv`: bar chart по этапам, heatmap speedup, scatter memory-vs-time.")
    lines.append("5. **Для step3/step4 делайте раздельный раздел анализа**, потому что часть библиотек эти этапы не поддерживает; иначе средние показатели будут искажены.")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Анализ профилирования и подготовка артефактов постпроцессинга")
    parser.add_argument("--base-dir", default="results/profiling", help="Базовая директория профилирования")
    parser.add_argument("--libraries", default="all", help="Список библиотек через запятую или all")
    parser.add_argument("--reference", default="our", help="Эталонная библиотека для speedup")
    parser.add_argument("--top-lines", type=int, default=5, help="Сколько bottleneck-строк хранить на этап")
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
    all_memory: list[MemorySummary] = []
    all_bottlenecks: list[Bottleneck] = []
    run_paths: dict[str, str] = {}

    for lib in libraries:
        run_dir = latest_run_dir(base_dir, lib)
        run_paths[lib] = str(run_dir)
        summary_path = run_dir / "run_summary.json"
        summary = load_json(summary_path)

        all_stage_timings.extend(read_stage_timings(summary, lib))
        all_memory.extend(collect_memory_stats(run_dir, lib))
        all_bottlenecks.extend(collect_line_bottlenecks(run_dir, lib, top_n=args.top_lines))

    speedups = speedup_vs_reference(all_stage_timings, args.reference)

    timings_rows = [
        {
            "library": x.library,
            "stage": x.stage,
            "sample_count": x.sample_count,
            "mean_total_ms": round(x.mean_total_ms, 6),
            "std_total_ms": round(x.std_total_ms, 6),
            "mean_per_repeat_ms": round(x.mean_per_repeat_ms, 6),
            "success_rate": round(x.success_rate, 6),
            "applicable": x.applicable,
            "not_supported": x.not_supported,
            "speedup_vs_reference": None if speedups[x.library][x.stage] is None else round(float(speedups[x.library][x.stage]), 6),
        }
        for x in sorted(all_stage_timings, key=lambda i: (i.library, i.stage))
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
        ["library", "stage", "sample_count", "mean_total_ms", "std_total_ms", "mean_per_repeat_ms", "success_rate", "applicable", "not_supported", "speedup_vs_reference"],
    )
    write_csv(out_dir / "memory_stage_summary.csv", memory_rows, ["library", "stage", "sample_count", "mean_peak_mb", "max_peak_mb"])
    write_csv(out_dir / "line_bottlenecks.csv", bottleneck_rows, ["library", "stage", "filename", "line", "total_time_s", "hits", "code"])

    report_md = build_markdown_report(args.reference, all_stage_timings, all_memory, all_bottlenecks, speedups)
    (out_dir / "analysis_report.md").write_text(report_md, encoding="utf-8")

    report_json = {
        "meta": {
            "generated_at": timestamp,
            "base_dir": str(base_dir),
            "libraries": libraries,
            "reference": args.reference,
            "top_lines_per_stage": args.top_lines,
            "source_runs": run_paths,
        },
        "stage_timings": timings_rows,
        "memory_summary": memory_rows,
        "line_bottlenecks": bottleneck_rows,
    }
    (out_dir / "analysis_report.json").write_text(json.dumps(report_json, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ Analysis artifacts saved to: {out_dir}")
    print(f" - {out_dir / 'analysis_report.md'}")
    print(f" - {out_dir / 'analysis_report.json'}")
    print(f" - {out_dir / 'stage_timings.csv'}")
    print(f" - {out_dir / 'memory_stage_summary.csv'}")
    print(f" - {out_dir / 'line_bottlenecks.csv'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
