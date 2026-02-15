#!/usr/bin/env python3
"""Тесты каталога адаптеров."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.catalog import (
    ADAPTER_SPECS,
    adapter_choices,
    create_adapter,
    get_adapter_spec,
    list_adapter_options,
)
from src.adapters.our_adapter import OurImplementationAdapter


def main():
    choices = adapter_choices()
    assert choices == sorted(choices), "Список choices должен быть отсортирован"
    assert "our" in choices, "В choices должен быть адаптер 'our'"

    spec = get_adapter_spec("our")
    assert spec.key == "our", "Должен возвращаться корректный spec"
    assert spec.is_available(), "Встроенный адаптер должен быть доступен"

    adapter = create_adapter("our")
    assert isinstance(adapter, OurImplementationAdapter), "create_adapter('our') должен вернуть OurImplementationAdapter"

    options = list_adapter_options()
    keys = {item["key"] for item in options}
    assert keys == set(ADAPTER_SPECS.keys()), "Опции должны соответствовать ADAPTER_SPECS"

    try:
        get_adapter_spec("unknown")
        raise AssertionError("Ожидалась ошибка для неизвестного адаптера")
    except ValueError:
        pass

    for key, spec in ADAPTER_SPECS.items():
        if not spec.is_available() and spec.dependency:
            try:
                create_adapter(key, require_available=True)
                raise AssertionError("Ожидалась ошибка require_available для отсутствующей зависимости")
            except RuntimeError:
                pass

    print("✅ test_adapter_catalog passed")


if __name__ == "__main__":
    main()
