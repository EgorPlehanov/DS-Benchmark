# Profiling / Профилирование

## RU
Подсистема профилирования объединяет несколько источников метрик и управляет структурой артефактов.

### Компоненты
- `core/` — CPU, Memory, Line профилировщики.
- `collectors/` — дополнительные сборщики (например, Scalene, system collector).
- `composite_profiler.py` — оркестрация запуска/остановки нескольких профилировщиков.
- `artifacts/` — менеджер структуры и сохранения результатов.

### Структура артефактов
Базовый паттерн хранения:
`results/profiling/<adapter>/<run_id>/`

Внутри используются каталоги `input`, `profilers`, `test_results`, `metrics`, `visualizations`, `logs`, `tmp`.

---

## EN
The profiling subsystem combines multiple metric sources and manages artifact storage layout.

### Components
- `core/` — CPU, Memory, and Line profilers.
- `collectors/` — extra collectors (e.g., Scalene, system collector).
- `composite_profiler.py` — start/stop orchestration for multiple profilers.
- `artifacts/` — artifact layout and persistence manager.

### Artifact layout
Base path pattern:
`results/profiling/<adapter>/<run_id>/`

Typical subdirectories: `input`, `profilers`, `test_results`, `metrics`, `visualizations`, `logs`, `tmp`.
