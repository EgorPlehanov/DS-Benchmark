# Data Processing Scripts / Скрипты обработки данных

## English

This directory contains scripts for processing benchmark/profiling artifacts into aggregated and human-readable reports.

### Available scripts

#### `compare_profiling_results.py`

Compares numerical results across profiling outputs from multiple libraries (for example: `our`, `pyds`, `dstpy`, `dstz`) and produces both machine-readable and text reports.

**What it does:**
- Discovers libraries and tests (or uses user-provided lists).
- Loads the latest `test_results/<test_name>_results.json` per library.
- Compares stages (`step1`..`step4`) against a reference library.
- Computes:
  - compared values (`compared/total`),
  - compared percentage (`compared_%`),
  - identical percentage (with configurable threshold) (`identical_%`),
  - max/mean absolute difference (`max_abs_diff` / `mean_abs_diff`),
  - missing/extra paths (`missing` / `extra`).
- Builds summaries:
  - per test (all stages),
  - global by stage,
  - global by library.
- Saves reports into:
  - `results/profiling/processed_results/comparison_report/<timestamp>/comparison_report.json`
  - `results/profiling/processed_results/comparison_report/<timestamp>/comparison_report.txt`

**Typical usage:**

```bash
python scripts/processing/compare_profiling_results.py
```

```bash
python scripts/processing/compare_profiling_results.py \
  --reference our \
  --libraries our,pyds,dstpy,dstz \
  --tests all \
  --identical-threshold 1e-12 \
  --show-top-diffs 3
```

---

## Русский

В этой директории находятся скрипты для обработки артефактов бенчмарков/профилирования и формирования агрегированных, удобных для анализа отчетов.

### Доступные скрипты

#### `compare_profiling_results.py`

Сравнивает численные результаты между профилировочными прогонами разных библиотек (например: `our`, `pyds`, `dstpy`, `dstz`) и формирует отчеты в JSON и текстовом виде.

**Что делает скрипт:**
- Определяет список библиотек и тестов автоматически (или использует переданные параметры).
- Загружает последний `test_results/<test_name>_results.json` для каждой библиотеки.
- Сравнивает этапы (`step1`..`step4`) относительно эталонной библиотеки.
- Считает метрики:
  - количество сопоставленных значений (`compared/total`),
  - процент сопоставления (`compared_%`),
  - процент идентичности (с настраиваемым порогом) (`identical_%`),
  - максимальную/среднюю абсолютную разницу (`max_abs_diff` / `mean_abs_diff`),
  - отсутствующие/лишние пути (`missing` / `extra`).
- Строит сводки:
  - по каждому тесту (все этапы),
  - общий итог по этапам,
  - общий итог по библиотекам.
- Сохраняет отчеты в:
  - `results/profiling/processed_results/comparison_report/<timestamp>/comparison_report.json`
  - `results/profiling/processed_results/comparison_report/<timestamp>/comparison_report.txt`

**Пример запуска:**

```bash
python scripts/processing/compare_profiling_results.py
```

```bash
python scripts/processing/compare_profiling_results.py \
  --reference our \
  --libraries our,pyds,dstpy,dstz \
  --tests all \
  --identical-threshold 1e-12 \
  --show-top-diffs 3
```


#### `analyze_profiling_postprocessing.py`

Aggregates profiling metrics from the latest run of each library and prepares artifacts for research postprocessing.

**What it does:**
- Reads latest profiler artifacts for each selected library.
- Collects per-stage timing metrics from CPU profiler metadata (`mean_per_repeat_ms`, `std`).
- Marks stages as `supported`/`not_supported` using latest `comparison_report` and masks misleading speedups.
- Builds profiler coverage/duration table by profiler and stage.
- Adds dedicated Scalene analytics block (stage summary + top hotspots for filtered library files).
- Collects per-stage memory peaks from `profilers/memory/*/*.json` and builds comparison tables (`lib_peak`, `lib_peak/ref_peak`).
- Extracts top bottleneck lines from line profiler outputs.
- Computes relative speedup vs reference library.
- Produces CSV/JSON/Markdown artifacts for analysis and plotting.
- Uses raw profiler artifacts (`cpu`, `memory`, `line`, and scalene coverage) instead of run-level quick summary.

**Outputs:**
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/analysis_report.md`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/analysis_report.json`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/stage_timings.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/profiler_durations.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/memory_stage_summary.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/line_bottlenecks.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/scalene_stage_summary.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/scalene_hotspots.csv`

**Typical usage:**

```bash
python scripts/processing/analyze_profiling_postprocessing.py \
  --reference our \
  --libraries all \
  --top-lines 5 \
  --path-filter library_only
```


#### `plot_postprocessing_analysis.py`

Builds visual plots from already prepared postprocessing artifacts (`stage_timings.csv`, `memory_stage_summary.csv`, `line_bottlenecks.csv`) so that profiling results can be interpreted quickly and unambiguously.

**What it does:**
- Auto-selects latest analysis folder (or accepts explicit `--analysis-dir`).
- Generates a CPU stage timing heatmap.
- Generates grouped speedup bars vs reference library.
- Generates memory-ratio heatmap vs reference.
- Generates line bottlenecks chart for selected library (stage colors + full code line labels).
- Generates per-library subplots for line timings sorted by line number inside each library.
- Writes a small `plot_summary.md` index.

**Outputs (default):**
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/cpu_absolute_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/cpu_relative_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/speedup_grouped_bar.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/memory_absolute_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/memory_relative_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/memory_efficiency_grouped_bar.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/line_bottlenecks_library_sorted_by_line.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/line_timing_by_library_subplots.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/plot_summary.md`

**Typical usage:**

```bash
python scripts/processing/plot_postprocessing_analysis.py
```

```bash
python scripts/processing/plot_postprocessing_analysis.py \
  --analysis-dir results/profiling/processed_results/postprocessing_analysis/20260219_020406 \
  --top-lines 15 \
  --line-library our
```


---

#### `analyze_profiling_postprocessing.py`

Агрегирует профилировочные метрики из последних прогонов библиотек и подготавливает артефакты для исследовательского постпроцессинга.

**Что делает скрипт:**
- Читает последние raw-артефакты профилировщиков по каждой выбранной библиотеке.
- Собирает метрики времени по этапам из metadata CPU профайлера (`mean_per_repeat_ms`, `std`).
- Формирует таблицу покрытия/длительностей по каждому профайлеру и этапу.
- Добавляет отдельный блок аналитики Scalene (сводка по этапам + топ hot spots по отфильтрованным файлам библиотек).
- Проставляет `supported`/`not_supported` по этапам (по последнему `comparison_report`) и убирает вводящие в заблуждение speedup для неподдерживаемых этапов.
- Собирает пики памяти по этапам из `profilers/memory/*/*.json` и строит сравнительные таблицы (`lib_peak`, `lib_peak/ref_peak`).
- Извлекает узкие места (top lines) из line profiler.
- Считает относительное ускорение относительно эталонной библиотеки.
- Формирует CSV/JSON/Markdown артефакты для графиков и аналитики.
- Использует raw-артефакты профилировщиков (`cpu`, `memory`, `line`, а также покрытие scalene), а не только агрегированный быстрый run-summary.

**Артефакты на выходе:**
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/analysis_report.md`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/analysis_report.json`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/stage_timings.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/profiler_durations.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/memory_stage_summary.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/line_bottlenecks.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/scalene_stage_summary.csv`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/scalene_hotspots.csv`

**Пример запуска:**

```bash
python scripts/processing/analyze_profiling_postprocessing.py \
  --reference our \
  --libraries all \
  --top-lines 5 \
  --path-filter library_only
```


#### `plot_postprocessing_analysis.py`

Строит наглядные графики по уже подготовленным артефактам постобработки (`stage_timings.csv`, `memory_stage_summary.csv`, `line_bottlenecks.csv`), чтобы визуально и однозначно анализировать результаты профилирования.

**Что делает скрипт:**
- Автоматически берет последний каталог анализа (или использует переданный `--analysis-dir`).
- Строит heatmap по CPU-таймингам этапов.
- Строит grouped bar по speedup относительно reference.
- Строит heatmap по отношению памяти к reference.
- Строит график узких мест по строкам для выбранной библиотеки (цвета этапов + полный текст строки кода).
- Строит подграфики по библиотекам для line-таймингов с сортировкой строк по номеру внутри каждой библиотеки.
- Добавляет индекс `plot_summary.md`.

**Артефакты на выходе (по умолчанию):**
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/cpu_absolute_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/cpu_relative_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/speedup_grouped_bar.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/memory_absolute_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/memory_relative_heatmap.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/memory_efficiency_grouped_bar.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/line_bottlenecks_library_sorted_by_line.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/line_timing_by_library_subplots.png`
- `results/profiling/processed_results/postprocessing_analysis/<timestamp>/plots/plot_summary.md`

**Пример запуска:**

```bash
python scripts/processing/plot_postprocessing_analysis.py
```

```bash
python scripts/processing/plot_postprocessing_analysis.py \
  --analysis-dir results/profiling/processed_results/postprocessing_analysis/20260219_020406 \
  --top-lines 15 \
  --line-library our
```
