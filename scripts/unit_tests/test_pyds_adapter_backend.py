#!/usr/bin/env python3
"""Проверка сообщения об установке для PyDSAdapter."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.pyds_adapter import PyDSAdapter


def main() -> int:
    adapter = PyDSAdapter()

    try:
        adapter._ensure_backend()
    except ImportError as exc:
        message = str(exc)
        assert 'github.com/reineking/pyds' in message
        assert 'pip install git+https://github.com/reineking/pyds.git' in message
        print('✅ pyds backend hint is correct')
        return 0

    print('✅ pyds backend import succeeded')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
