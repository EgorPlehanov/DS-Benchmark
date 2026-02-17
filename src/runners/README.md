# Runners / Раннеры

## RU
Раннеры управляют выполнением тестов и сбором метрик.

### Назначение
- `UniversalBenchmarkRunner` — базовый 4-шаговый сценарий тестирования.
- `ProfilingBenchmarkRunner` — расширение с профилировщиками и сохранением артефактов.

### Ключевые сценарии
- Загрузка теста через адаптер.
- Пошаговый прогон и измерение производительности.
- Агрегация результатов по итерациям.
- Сохранение JSON-артефактов в `results/profiling/...`.

---

## EN
Runners orchestrate test execution and metric collection.

### Purpose
- `UniversalBenchmarkRunner` — base 4-step benchmark flow.
- `ProfilingBenchmarkRunner` — profiling-enabled extension with artifact persistence.

### Main flow
- Load test payload via adapter.
- Execute benchmark steps and measure performance.
- Aggregate iteration-level outputs.
- Persist JSON artifacts under `results/profiling/...`.
