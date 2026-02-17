# DS-Benchmark

## RU
DS-Benchmark — проект для сравнения реализаций теории Демпстера–Шейфера в единых сценариях: от генерации входных DASS-данных до запуска бенчмарков, профилирования и постобработки результатов.

### Что внутри
- Генерация тестовых DASS-наборов.
- Унифицированные адаптеры для нескольких библиотек.
- Единый runner для воспроизводимых запусков.
- Профилирование CPU/Memory/Line/Scalene.
- Стандартизированное хранение артефактов и результатов.
- Скрипты валидации и обработки отчетов.

### Навигация по модулям
- [`src/generators/README.md`](src/generators/README.md) — генерация и валидация DASS-данных.
- [`src/adapters/README.md`](src/adapters/README.md) — адаптерный слой библиотек.
- [`src/runners/README.md`](src/runners/README.md) — запуск сценариев бенчмарка.
- [`src/profiling/README.md`](src/profiling/README.md) — профилировщики и артефакты.
- [`src/core/README.md`](src/core/README.md) — базовая реализация/ядро.
- [`data/README.md`](data/README.md) — структура входных данных.
- [`results/README.md`](results/README.md) — структура выходных артефактов.
- [`scripts/README.md`](scripts/README.md) — CLI-скрипты проекта.

### Быстрый старт
```bash
pip install -r requirements.txt
python scripts/generate_test_data.py --help
python scripts/profile_benchmark.py --help
```

---

## EN
DS-Benchmark is a benchmarking project for Dempster–Shafer implementations, covering the full workflow: DASS input generation, benchmark execution, profiling, and result post-processing.

### What is included
- DASS test data generation.
- Unified adapters for multiple libraries.
- Reproducible benchmark runner.
- CPU/Memory/Line/Scalene profiling.
- Standardized artifact/result storage.
- Validation and report-processing scripts.

### Module map
- [`src/generators/README.md`](src/generators/README.md) — DASS data generation and validation.
- [`src/adapters/README.md`](src/adapters/README.md) — adapter layer for libraries.
- [`src/runners/README.md`](src/runners/README.md) — benchmark execution flows.
- [`src/profiling/README.md`](src/profiling/README.md) — profilers and artifact management.
- [`src/core/README.md`](src/core/README.md) — core implementation.
- [`data/README.md`](data/README.md) — input data structure.
- [`results/README.md`](results/README.md) — output artifact structure.
- [`scripts/README.md`](scripts/README.md) — project CLI scripts.

### Quick start
```bash
pip install -r requirements.txt
python scripts/generate_test_data.py --help
python scripts/profile_benchmark.py --help
```
