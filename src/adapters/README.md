# Adapters / Адаптеры

## RU
Адаптерный слой приводит разные библиотеки ДШ к единому интерфейсу бенчмарка.

### Назначение
- Инкапсуляция различий между библиотеками (`our`, `dstz`, `dstpy`, `pyds`).
- Единый контракт для runner'ов: загрузка DASS, Belief/Plausibility, комбинирование, дисконтирование.

### Ключевые файлы
- `base_adapter.py` — базовый интерфейс адаптера.
- `factory.py` — реестр и фабрика адаптеров.
- `*_adapter.py` — конкретные реализации под библиотеки.

### Использование
```python
from src.adapters.factory import create_adapter
adapter = create_adapter("our")
```

---

## EN
The adapter layer maps different DS libraries to a single benchmark interface.

### Purpose
- Encapsulate library-specific behavior (`our`, `dstz`, `dstpy`, `pyds`).
- Provide a uniform contract for runners: DASS loading, Belief/Plausibility, combination, discounting.

### Key files
- `base_adapter.py` — adapter base interface.
- `factory.py` — adapter registry and factory.
- `*_adapter.py` — library-specific implementations.

### Usage
```python
from src.adapters.factory import create_adapter
adapter = create_adapter("our")
```
