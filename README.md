# DS-Benchmark — прототип исследовательского бенчмарка теории Демпстера–Шейфера

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## RU

### Статус

**Прототип / активная исследовательская разработка**.

### О проекте

DS-Benchmark — исследовательский проект для сравнения реализаций теории Демпстера–Шейфера в единых сценариях: от генерации входных DASS-данных до запуска бенчмарков, профилирования и постобработки результатов.

### Авторы и роли

- **Основной разработчик:** Егор Сергеевич Плеханов, студент магистратуры.
- **Вторичный разработчик и научный руководитель:** Владимир Андреевич Пархоменко, старший преподаватель.
- **Аффилиация:** Федеральное государственное автономное образовательное учреждение высшего образования «Санкт-Петербургский политехнический университет Петра Великого», Институт компьютерных наук и кибербезопасности, Санкт-Петербург, Россия.

### Отказ от ответственности

Репозиторий содержит исследовательский прототип.
Программное обеспечение предоставляется «как есть» ("as is") без каких-либо явных или подразумеваемых гарантий,
включая, но не ограничиваясь, гарантиями коммерческой пригодности, пригодности для конкретной цели
и отсутствия нарушений прав. Авторы не несут ответственности за любые претензии, ущерб
или иные последствия, возникшие при использовании программного обеспечения.

### Что внутри

- Генерация тестовых DASS-наборов.
- Унифицированные адаптеры для нескольких библиотек.
- Единый runner для воспроизводимых запусков.
- Профилирование CPU/Memory/Line/Scalene.
- Стандартизированное хранение артефактов и результатов.
- Скрипты валидации и обработки отчетов.

### Основной результат исследования

- [Интерпретация результатов профилирования (RU)](results/profiling/processed_results/postprocessing_analysis/20260219_074831/analysis_interpretation_ru.md) — ключевой итог проведенного исследования.

### Структура проекта

- [`docs_pipeline_overview.md`](docs_pipeline_overview.md) — подробное описание реализации пайплайна и архитектуры.
- [`src/generators/`](src/generators/) — генерация и валидация DASS-данных.
- [`src/adapters/`](src/adapters/) — адаптерный слой библиотек.
- [`src/runners/`](src/runners/) — запуск сценариев бенчмарка.
- [`src/profiling/`](src/profiling/) — профилировщики и управление артефактами.
- [`src/core/`](src/core/) — базовая реализация/ядро.
- [`data/`](data/) — входные данные и наборы сценариев.
- [`results/`](results/) — результаты бенчмарков, профилирования и постобработки.
- [`scripts/`](scripts/) — CLI-скрипты проекта.
- [`external/`](external/) — внешние библиотеки/зеркала для сравнения (вспомогательные компоненты).

### Быстрый старт

```bash
pip install -r requirements.txt
python scripts/generate_test_data.py --help
python scripts/profile_benchmark.py --help
```

### Лицензия

Проект распространяется под лицензией **MIT**. Полный текст лицензии находится в файле [LICENSE](LICENSE).

---

## EN

### Status

**Prototype / In active research**.

### About

DS-Benchmark is a research benchmarking project for Dempster–Shafer implementations, covering the full workflow: DASS input generation, benchmark execution, profiling, and result post-processing.

### Authors and roles

- **Main developer:** Egor Sergeevich Plekhanov, master’s student.
- **Secondary developer and supervisor:** Vladimir Andreevich Parkhomenko, senior lecturer.
- **Affiliation:** Peter the Great St. Petersburg Polytechnic University, Institute of Computer Science and Cybersecurity, Saint Petersburg, Russia.

### Disclaimer

Disclaimer: This repository contains a research prototype.
The software is provided "as is", without warranty of any kind, express or implied,
including but not limited to the warranties of merchantability, fitness for a particular
purpose, and noninfringement. The authors are not liable for any claim, damages,
or other liability arising from the use of the software.

### What is included

- DASS test data generation.
- Unified adapters for multiple libraries.
- Reproducible benchmark runner.
- CPU/Memory/Line/Scalene profiling.
- Standardized artifact/result storage.
- Validation and report-processing scripts.

### Primary research outcome

- [Profiling results interpretation (RU)](results/profiling/processed_results/postprocessing_analysis/20260219_074831/analysis_interpretation_ru.md) — the main deliverable of this study.

### Project structure

- [`docs_pipeline_overview.md`](docs_pipeline_overview.md) — detailed implementation guide for pipeline and architecture.
- [`src/generators/`](src/generators/) — DASS data generation and validation.
- [`src/adapters/`](src/adapters/) — adapter layer for libraries.
- [`src/runners/`](src/runners/) — benchmark execution flows.
- [`src/profiling/`](src/profiling/) — profilers and artifact management.
- [`src/core/`](src/core/) — core implementation.
- [`data/`](data/) — input datasets and scenarios.
- [`results/`](results/) — benchmark/profiling/post-processing outputs.
- [`scripts/`](scripts/) — project CLI scripts.
- [`external/`](external/) — external libraries/mirrors used for comparison (supporting components).

### Quick start

```bash
pip install -r requirements.txt
python scripts/generate_test_data.py --help
python scripts/profile_benchmark.py --help
```

### License

This project is distributed under the **MIT** License. See [LICENSE](LICENSE) for the full text.
