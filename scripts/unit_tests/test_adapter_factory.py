#!/usr/bin/env python3
"""Проверки реестра адаптеров."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.factory import create_adapter, list_adapters
from src.adapters.our_adapter import OurImplementationAdapter


def main() -> int:
    adapters = list_adapters()
    assert 'our' in adapters
    assert 'py_dempster_shafer' in adapters

    our = create_adapter('our')
    alias = create_adapter('ourimplementation')

    assert isinstance(our, OurImplementationAdapter)
    assert isinstance(alias, OurImplementationAdapter)

    try:
        create_adapter('unknown')
    except ValueError:
        pass
    else:
        raise AssertionError('Expected ValueError for unknown adapter')

    print('✅ adapter factory tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
