#!/usr/bin/env python3
"""Smoke-тесты для новых адаптеров dst_py и dstz."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.dstpy_adapter import DstPyAdapter
from src.adapters.dstz_adapter import DstzAdapter


DASS_SAMPLE = {
    "frame_of_discernment": ["A", "B"],
    "bba_sources": [
        {"bba": {"{A}": 0.7, "{A,B}": 0.3}},
        {"bba": {"{A}": 0.2, "{B}": 0.3, "{A,B}": 0.5}},
    ],
}


def validate_adapter(adapter) -> None:
    loaded = adapter.load_from_dass(DASS_SAMPLE)

    assert adapter.get_frame_of_discernment(loaded) == ["A", "B"]
    assert adapter.get_sources_count(loaded) == 2

    source_data = {
        "frame_elements": loaded["frame_elements"],
        "bpas": [loaded["bpas"][0]],
    }
    bel = adapter.calculate_belief(source_data, "{A}")
    pl = adapter.calculate_plausibility(source_data, "{A}")
    assert 0.0 <= bel <= 1.0
    assert 0.0 <= pl <= 1.0

    dempster = adapter.combine_sources_dempster(loaded)
    assert isinstance(dempster, dict) and dempster

    discounted = adapter.apply_discounting(source_data, 0.1)
    assert isinstance(discounted, list) and discounted

    yager = adapter.combine_sources_yager(loaded)
    assert isinstance(yager, dict) and yager



def main() -> int:
    try:
        validate_adapter(DstPyAdapter())
    except ImportError as exc:
        print(f'⚠️ dst_py adapter skipped: {exc}')

    validate_adapter(DstzAdapter())

    print('✅ new adapters stages tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
