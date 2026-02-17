# Generators / Генераторы

## RU
Модуль генерации тестовых данных в формате DASS.

### Назначение
- Создание синтетических наборов (`DassGenerator`) с настраиваемым размером фрейма, количеством источников и плотностью BBA.
- Валидация и нормализация BPA/BBA (`DassValidator`).

### Ключевые файлы
- `dass_generator.py` — генерация данных и быстрый конструктор случайных BPA.
- `validator.py` — проверка формата и нормализация распределений масс.

### Вход / Выход
- Вход: параметры генерации (элементы фрейма, число источников, плотность).
- Выход: JSON-структура DASS с `frame_of_discernment` и `bba_sources`.

---

## EN
Test data generation module for DASS format.

### Purpose
- Generate synthetic datasets (`DassGenerator`) with configurable frame size, source count, and BBA density.
- Validate and normalize BPA/BBA payloads (`DassValidator`).

### Key files
- `dass_generator.py` — data generation and fast random BPA builder.
- `validator.py` — format checks and mass normalization.

### Input / Output
- Input: generation parameters (frame elements, number of sources, density).
- Output: DASS JSON payload with `frame_of_discernment` and `bba_sources`.
