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
