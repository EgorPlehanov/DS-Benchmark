#!/usr/bin/env python3
"""Единоразовая проверка backend-зависимостей всех адаптеров."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.factory import create_adapter, list_adapters


def main() -> int:
    unavailable = []

    for adapter_name in list_adapters():
        adapter = create_adapter(adapter_name)
        try:
            adapter._ensure_backend()
            print(f"✅ {adapter_name}: backend доступен")
        except ImportError as exc:
            unavailable.append((adapter_name, str(exc)))
            print(f"⚠️ {adapter_name}: backend недоступен: {exc}")

    if unavailable:
        print("\n⚠️ Проверка завершена: есть адаптеры с недостающими зависимостями.")
    else:
        print("\n✅ Проверка завершена: зависимости всех адаптеров доступны.")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
