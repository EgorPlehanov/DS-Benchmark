#!/usr/bin/env python3
"""Проверка, что все этапы пайплайна поддерживаются PyDempsterShaferAdapter."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.adapters.pydempster_adapter import PyDempsterShaferAdapter


class DummyMassFunction(dict):
    """Минимальная совместимая заглушка API pyds.MassFunction."""

    def __init__(self, source=None):
        super().__init__()
        if source:
            if isinstance(source, dict):
                iterable = source.items()
            else:
                iterable = source
            for hypothesis, mass in iterable:
                key = frozenset(hypothesis)
                self[key] = self.get(key, 0.0) + float(mass)

    def bel(self, event):
        event_set = frozenset(event)
        return sum(v for h, v in self.items() if h and h.issubset(event_set))

    def pl(self, event):
        event_set = frozenset(event)
        return sum(v for h, v in self.items() if h and (h & event_set))

    def combine_conjunctive(self, other, normalization=True):
        result = DummyMassFunction()
        conflict = 0.0
        for h1, m1 in self.items():
            for h2, m2 in other.items():
                inter = h1 & h2
                value = m1 * m2
                if inter:
                    result[inter] = result.get(inter, 0.0) + value
                else:
                    conflict += value

        if normalization and conflict < 1.0:
            norm = 1.0 - conflict
            for k in list(result.keys()):
                result[k] = result[k] / norm
        elif not normalization and conflict > 0:
            result[frozenset()] = result.get(frozenset(), 0.0) + conflict
        return result


def main() -> int:
    adapter = PyDempsterShaferAdapter()
    adapter._MassFunction = DummyMassFunction

    dass = {
        "frame_of_discernment": ["A", "B"],
        "bba_sources": [
            {"bba": {"{A}": 0.7, "{A,B}": 0.3}},
            {"bba": {"{A}": 0.2, "{B}": 0.3, "{A,B}": 0.5}},
        ],
    }

    loaded = adapter.load_from_dass(dass)

    # step1
    bel = adapter.calculate_belief({"frame": loaded["frame"], "bpa": loaded["bpas"][0]}, "{A}")
    pl = adapter.calculate_plausibility({"frame": loaded["frame"], "bpa": loaded["bpas"][0]}, "{A}")
    assert 0.0 <= bel <= 1.0
    assert 0.0 <= pl <= 1.0

    # step2
    combined = adapter.combine_sources_dempster(loaded)
    assert isinstance(combined, dict) and combined

    # step3 (expected unsupported in backend)
    try:
        adapter.apply_discounting(loaded, 0.1)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("step3 must raise NotImplementedError for py_dempster_shafer")

    # step4 (expected unsupported in backend)
    try:
        adapter.combine_sources_yager(loaded)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("step4 must raise NotImplementedError for py_dempster_shafer")

    print("✅ pydempster adapter: step1/step2 supported, step3/step4 correctly unsupported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
