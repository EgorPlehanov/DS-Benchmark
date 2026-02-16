"""Адаптер для библиотеки dstz."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Union

from .base_adapter import BaseDempsterShaferAdapter


class DstzAdapter(BaseDempsterShaferAdapter):
    """Адаптер для профилирования библиотеки dstz."""

    def __init__(self):
        self._Element = None
        self._Evidence = None
        self._bel = None
        self._pl = None
        self._ds_rule = None
        self._shafer_discounting = None

    def _ensure_backend(self) -> None:
        if self._Evidence is not None:
            return

        try:
            from dstz.core.atom import Element  # type: ignore
            from dstz.core.distribution import Evidence  # type: ignore
            from dstz.math.func import bel, pl  # type: ignore
            from dstz.evpiece.dual import ds_rule  # type: ignore
            from dstz.evpiece.single import shafer_discounting  # type: ignore
        except ImportError:
            project_root = Path(__file__).resolve().parents[2]
            vendored_src = project_root / "external" / "dstz"
            if str(vendored_src) not in sys.path:
                sys.path.insert(0, str(vendored_src))
            from dstz.core.atom import Element  # type: ignore
            from dstz.core.distribution import Evidence  # type: ignore
            from dstz.math.func import bel, pl  # type: ignore
            from dstz.evpiece.dual import ds_rule  # type: ignore
            from dstz.evpiece.single import shafer_discounting  # type: ignore

        self._Element = Element
        self._Evidence = Evidence
        self._bel = bel
        self._pl = pl
        self._ds_rule = ds_rule
        self._shafer_discounting = shafer_discounting

    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:

        frame_elements = dass_data["frame_of_discernment"]
        bpas = [self._to_evidence(source["bba"]) for source in dass_data["bba_sources"]]

        return {"frame_elements": frame_elements, "bpas": bpas}

    def get_frame_of_discernment(self, data: Any) -> List[str]:
        return data.get("frame_elements", []) if isinstance(data, dict) else []

    def get_sources_count(self, data: Any) -> int:
        return len(data.get("bpas", [])) if isinstance(data, dict) else 0

    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        bpa = self._extract_bpa(data)
        event_element = self._Element(self._event_to_set(event))
        return float(self._bel(event_element, bpa))

    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        bpa = self._extract_bpa(data)
        event_element = self._Element(self._event_to_set(event))
        return float(self._pl(event_element, bpa))

    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        bpas = [self._to_evidence(bpa) for bpa in data.get("bpas", [])]
        if not bpas:
            return {}

        result = bpas[0]
        for bpa in bpas[1:]:
            result = self._ds_rule(result, bpa)
        return self._format_bpa(result)

    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        bpas = [self._to_evidence(bpa) for bpa in data.get("bpas", [])]
        reliability = 1.0 - alpha
        return [self._format_bpa(self._shafer_discounting(bpa, reliability)) for bpa in bpas]

    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        bpas = [self._to_evidence(bpa) for bpa in data.get("bpas", [])]
        if not bpas:
            return {}

        result = bpas[0]
        for bpa in bpas[1:]:
            result = self._yager_combine(result, bpa)

        return self._format_bpa(result)

    def _extract_bpa(self, data: Any):

        if isinstance(data, dict) and "bpa" in data:
            return self._to_evidence(data["bpa"])
        if isinstance(data, dict) and data.get("bpas"):
            return self._to_evidence(data["bpas"][0])
        return self._Evidence()

    def _to_evidence(self, bpa: Any):

        if isinstance(bpa, self._Evidence):
            return bpa

        evidence = self._Evidence()
        plain = self._to_plain_dict(bpa)
        for subset, mass in plain.items():
            evidence[self._Element(set(subset))] = float(mass)
        return evidence

    def _to_plain_dict(self, bpa: Any) -> Dict[frozenset, float]:
        if isinstance(bpa, dict):
            if not bpa:
                return {}
            first_key = next(iter(bpa.keys()))
            if isinstance(first_key, str):
                return {self._parse_subset_str(k): float(v) for k, v in bpa.items()}
            if isinstance(first_key, frozenset):
                return {frozenset(k): float(v) for k, v in bpa.items()}

        if hasattr(bpa, "items"):
            result = {}
            for key, value in bpa.items():
                subset = frozenset(getattr(key, "value", set()))
                result[subset] = float(value)
            return result

        return {}

    def _event_to_set(self, event: Union[str, List[str]]) -> Set[str]:
        if isinstance(event, str):
            return set(self._parse_subset_str(event))
        return set(event)

    def _parse_subset_str(self, subset_str: str) -> frozenset:
        raw = subset_str.strip("{}")
        if not raw:
            return frozenset()
        return frozenset(item.strip() for item in raw.split(",") if item.strip())

    def _format_subset(self, subset: Set[str]) -> str:
        if not subset:
            return "{}"
        return "{" + ",".join(sorted(subset)) + "}"

    def _format_bpa(self, bpa: Any) -> Dict[str, float]:
        plain = self._to_plain_dict(bpa)
        return {self._format_subset(set(k)): round(float(v), 10) for k, v in plain.items()}

    def _yager_combine(self, ev1, ev2):
        result = {}
        conflict = 0.0

        theta = self._infer_theta(ev1, ev2)

        for key1, m1 in ev1.items():
            set1 = set(key1.value)
            for key2, m2 in ev2.items():
                set2 = set(key2.value)
                inter = frozenset(set1.intersection(set2))
                value = float(m1) * float(m2)
                if inter:
                    result[inter] = result.get(inter, 0.0) + value
                else:
                    conflict += value

        result[theta] = result.get(theta, 0.0) + conflict

        out = self._Evidence()
        for subset, mass in result.items():
            out[self._Element(set(subset))] = float(mass)
        return out

    def _infer_theta(self, ev1, ev2) -> frozenset:
        items = set()
        for evidence in (ev1, ev2):
            for key in evidence.keys():
                items.update(set(key.value))
        return frozenset(items)
