"""Адаптер для библиотеки dst-py (пакет `dempster_shafer`)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Union

from .base_adapter import BaseDempsterShaferAdapter


class DstPyAdapter(BaseDempsterShaferAdapter):
    """Адаптер внешней реализации dst-py."""

    def __init__(self):
        self._MassFunction = None
        self._combine_yager = None
        self._discount = None
        self._ensure_backend()

    def _ensure_backend(self) -> None:
        if self._MassFunction is not None:
            return

        project_root = Path(__file__).resolve().parents[2]
        vendored_src = project_root / "external" / "dst-py" / "src"
        if str(vendored_src) not in sys.path:
            sys.path.insert(0, str(vendored_src))

        try:
            from dempster_shafer import MassFunction, combine_yager, discount  # type: ignore
        except Exception as exc:
            raise ImportError(
                "Не удалось импортировать dst-py (`dempster_shafer`). "
                "Убедитесь, что установлены зависимости библиотеки (в т.ч. numpy)."
            ) from exc

        self._MassFunction = MassFunction
        self._combine_yager = combine_yager
        self._discount = discount

    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:

        frame_elements = dass_data["frame_of_discernment"]
        bpas = [self._to_mass_function(source["bba"]) for source in dass_data["bba_sources"]]

        return {
            "frame_elements": frame_elements,
            "bpas": bpas,
        }

    def get_frame_of_discernment(self, data: Any) -> List[str]:
        return data.get("frame_elements", []) if isinstance(data, dict) else []

    def get_sources_count(self, data: Any) -> int:
        return len(data.get("bpas", [])) if isinstance(data, dict) else 0

    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        bpa = self._extract_bpa(data)
        return float(bpa.belief(self._event_to_key(event)))

    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        bpa = self._extract_bpa(data)
        return float(bpa.plausibility(self._event_to_key(event)))

    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        frame_elements = data.get("frame_elements", []) if isinstance(data, dict) else []
        bpas = [self._to_mass_function(bpa, frame_elements) for bpa in data.get("bpas", [])]
        if not bpas:
            return {}

        result = bpas[0]
        for bpa in bpas[1:]:
            result = result.combine_conjunctive(bpa, normalization=True)

        return self._format_bpa(result)

    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        frame_elements = data.get("frame_elements", []) if isinstance(data, dict) else []
        discounted = []
        for bpa in data.get("bpas", []):
            discounted_bpa = self._discount(self._to_mass_function(bpa, frame_elements), 1.0 - alpha)
            discounted.append(self._format_bpa(discounted_bpa))
        return discounted

    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        frame_elements = data.get("frame_elements", []) if isinstance(data, dict) else []
        bpas = [self._to_mass_function(bpa, frame_elements) for bpa in data.get("bpas", [])]
        if not bpas:
            return {}

        result = bpas[0]
        for bpa in bpas[1:]:
            result = self._combine_yager(result, bpa)

        return self._format_bpa(result)

    def _extract_bpa(self, data: Any):
        frame_elements = data.get("frame_elements", []) if isinstance(data, dict) else []
        if isinstance(data, dict) and "bpa" in data:
            return self._to_mass_function(data["bpa"], frame_elements)
        if isinstance(data, dict) and data.get("bpas"):
            return self._to_mass_function(data["bpas"][0], frame_elements)
        return self._MassFunction({})

    def _event_to_key(self, event: Union[str, List[str]]) -> frozenset:
        if isinstance(event, str):
            return self._parse_subset_str(event)
        return frozenset(event)

    def _parse_subset_str(self, subset_str: str) -> frozenset:
        raw = subset_str.strip("{}")
        if not raw:
            return frozenset()
        return frozenset(item.strip() for item in raw.split(",") if item.strip())

    def _format_subset(self, subset: Set[str]) -> str:
        if not subset:
            return "{}"
        return "{" + ",".join(sorted(subset)) + "}"

    def _to_plain_dict(self, bpa: Any) -> Dict[frozenset, float]:
        if isinstance(bpa, dict):
            if not bpa:
                return {}
            first_key = next(iter(bpa.keys()))
            if isinstance(first_key, str):
                return {self._parse_subset_str(k): float(v) for k, v in bpa.items()}
            return {frozenset(k): float(v) for k, v in bpa.items()}

        return {frozenset(k): float(v) for k, v in dict(bpa).items()}

    def _to_mass_function(self, bpa: Any, frame_elements: List[str] | None = None):

        frame = frame_elements if frame_elements else None
        if isinstance(bpa, self._MassFunction):
            if frame is None or bpa.frame is not None and bpa.frame.elements == set(frame):
                return bpa
            return self._MassFunction(self._to_plain_dict(bpa), frame=frame)
        return self._MassFunction(self._to_plain_dict(bpa), frame=frame)

    def _format_bpa(self, bpa: Any) -> Dict[str, float]:
        return {self._format_subset(set(k)): round(float(v), 10) for k, v in dict(bpa).items()}
