#!/usr/bin/env python3
"""Проверка диагностики backend для PyDSAdapter."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.pyds_adapter import PyDSAdapter


def main() -> int:
    adapter = PyDSAdapter()
    mass_function = adapter._resolve_mass_function()

    if mass_function is not None:
        print('✅ PyDS backend найден')
        return 0

    try:
        adapter._ensure_backend()
    except ImportError as exc:
        message = str(exc)
        assert 'MassFunction' in message
        assert 'py_dempster_shafer' in message
        print('✅ PyDS backend diagnostics ok')
        return 0

    raise AssertionError('Expected ImportError when backend is missing')


if __name__ == '__main__':
    raise SystemExit(main())
