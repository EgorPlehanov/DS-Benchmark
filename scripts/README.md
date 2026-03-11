# Scripts / Скрипты

## RU
CLI-утилиты для генерации данных, запуска бенчмарков, валидации и постобработки.

### Основные скрипты
- `generate_test_data.py` — генерация DASS-тестов.
- `profile_benchmark.py` — запуск бенчмарка с профилированием.
- `validate_book_examples.py` — проверка корректности на эталонных примерах.
- `run_profiling_pipeline.py` — пакетный запуск профилирования по всем библиотекам с паузой и последующим постпроцессингом.
- `processing/compare_profiling_results.py` — сравнение результатов профилирования.

### Примеры
```bash
python scripts/generate_test_data.py --help
python scripts/profile_benchmark.py --library our --tests last --profiling full
python scripts/validate_book_examples.py
python scripts/run_profiling_pipeline.py --tests last --profiling full --pause-seconds 60
```

---

## EN
CLI utilities for data generation, benchmark execution, validation, and post-processing.

### Main scripts
- `generate_test_data.py` — generate DASS test datasets.
- `profile_benchmark.py` — run benchmark with profiling.
- `validate_book_examples.py` — validate against reference/book examples.
- `run_profiling_pipeline.py` — batch profiling for all libraries with pause between runs and automatic post-processing.
- `processing/compare_profiling_results.py` — compare profiling outputs.

### Examples
```bash
python scripts/generate_test_data.py --help
python scripts/profile_benchmark.py --library our --tests last --profiling full
python scripts/validate_book_examples.py
python scripts/run_profiling_pipeline.py --tests last --profiling full --pause-seconds 60
```
