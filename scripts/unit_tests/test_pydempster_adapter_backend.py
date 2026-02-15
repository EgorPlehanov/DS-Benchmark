#!/usr/bin/env python3
"""Проверка сообщения об установке для PyDempsterShaferAdapter."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.pydempster_adapter import PyDempsterShaferAdapter


def main() -> int:
    adapter = PyDempsterShaferAdapter()

    try:
        adapter._ensure_backend()
    except ImportError as exc:
        message = str(exc)
        assert 'py_dempster_shafer' in message
        assert 'pyds' in message
        print('✅ py_dempster_shafer backend hint is correct')
        return 0

    print('✅ py_dempster_shafer backend import succeeded')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
