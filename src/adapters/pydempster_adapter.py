"""Адаптер для библиотеки py_dempster_shafer (API MassFunction через модуль pyds)."""

from typing import Any, Dict, List, Set, Union

from .base_adapter import BaseDempsterShaferAdapter


class PyDempsterShaferAdapter(BaseDempsterShaferAdapter):
    """Адаптер внешней реализации py_dempster_shafer."""

    def __init__(self):
        self._MassFunction = None

    def _ensure_backend(self):
        if self._MassFunction is not None:
            return

        try:
            from pyds import MassFunction  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Для использования PyDempsterShaferAdapter установите пакет `py_dempster_shafer` "
                "(в нем доступен модуль `pyds`)."
            ) from exc

        self._MassFunction = MassFunction

    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_backend()

        frame_elements = dass_data["frame_of_discernment"]
        frame = set(frame_elements)

        bpas = []
        for source in dass_data["bba_sources"]:
            bpas.append(self._to_mass_function(source["bba"]))

        return {"frame": frame, "frame_elements": frame_elements, "bpas": bpas}

    def get_frame_of_discernment(self, data: Any) -> List[str]:
        return data.get("frame_elements", []) if isinstance(data, dict) else []

    def get_sources_count(self, data: Any) -> int:
        return len(data.get("bpas", [])) if isinstance(data, dict) else 0

    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        bpa = self._extract_bpa(data)
        return float(bpa.bel(self._event_to_key(event)))

    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        bpa = self._extract_bpa(data)
        return float(bpa.pl(self._event_to_key(event)))

    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        self._ensure_backend()

        bpas = [self._to_mass_function(bpa) for bpa in data.get("bpas", [])]
        if not bpas:
            return {}

        result = bpas[0]
        for bpa in bpas[1:]:
            result = result.combine_conjunctive(bpa, normalization=True)

        return self._format_bpa(result)

    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        discounted = []
        for bpa_raw in data.get("bpas", []):
            bpa_dict = self._to_plain_dict(self._to_mass_function(bpa_raw))
            discounted_bpa = self._discount_plain(bpa_dict, alpha, data.get("frame", set()))
            discounted.append(self._format_plain_bpa(discounted_bpa))
        return discounted

    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        bpas = [self._to_plain_dict(self._to_mass_function(bpa)) for bpa in data.get("bpas", [])]
        if not bpas:
            return {}

        result = bpas[0]
        for bpa in bpas[1:]:
            result = self._yager_two(result, bpa, data["frame"])

        return self._format_plain_bpa(result)

    def _extract_bpa(self, data: Any):
        self._ensure_backend()

        if isinstance(data, dict) and "bpa" in data:
            return self._to_mass_function(data["bpa"])
        if isinstance(data, dict) and data.get("bpas"):
            return self._to_mass_function(data["bpas"][0])
        return self._MassFunction({})

    def _event_to_key(self, event: Union[str, List[str]]) -> frozenset:
        if isinstance(event, str):
            subset = self._parse_subset_str(event)
        else:
            subset = frozenset(event)
        return frozenset(subset)

    def _parse_subset_str(self, subset_str: str) -> frozenset:
        if subset_str == "{}":
            return frozenset()
        raw = subset_str.strip("{}")
        if not raw:
            return frozenset()
        return frozenset(raw.split(","))

    def _format_subset(self, subset: Set[str]) -> str:
        if not subset:
            return "{}"
        return "{" + ",".join(sorted(subset)) + "}"

    def _format_bpa(self, bpa) -> Dict[str, float]:
        return self._format_plain_bpa(self._to_plain_dict(bpa))

    def _to_plain_dict(self, bpa) -> Dict[frozenset, float]:
        self._ensure_backend()

        if isinstance(bpa, dict):
            if not bpa:
                return {}
            first_key = next(iter(bpa.keys()))
            if isinstance(first_key, str):
                return {
                    self._parse_subset_str(subset_str): float(value)
                    for subset_str, value in bpa.items()
                }
            return {frozenset(k): float(v) for k, v in bpa.items()}

        return {frozenset(k): float(v) for k, v in dict(bpa).items()}

    def _to_mass_function(self, bpa):
        self._ensure_backend()
        if isinstance(bpa, self._MassFunction):
            return bpa
        return self._MassFunction(self._to_plain_dict(bpa))

    def _format_plain_bpa(self, bpa: Dict[frozenset, float]) -> Dict[str, float]:
        return {self._format_subset(set(k)): round(float(v), 10) for k, v in bpa.items()}

    def _discount_plain(
        self,
        bpa: Dict[frozenset, float],
        alpha: float,
        frame: Set[str],
    ) -> Dict[frozenset, float]:
        omega = frozenset(frame)
        discounted: Dict[frozenset, float] = {}

        for subset, mass in bpa.items():
            if subset == omega:
                continue
            discounted[subset] = (1.0 - alpha) * mass

        omega_mass = bpa.get(omega, 0.0)
        discounted[omega] = (1.0 - alpha) * omega_mass + alpha
        return discounted

    def _yager_two(
        self,
        bpa1: Dict[frozenset, float],
        bpa2: Dict[frozenset, float],
        frame: Set[str],
    ) -> Dict[frozenset, float]:
        omega = frozenset(frame)
        result: Dict[frozenset, float] = {}
        conflict = 0.0

        for subset_a, mass_a in bpa1.items():
            for subset_b, mass_b in bpa2.items():
                intersection = subset_a & subset_b
                value = mass_a * mass_b
                if intersection:
                    result[intersection] = result.get(intersection, 0.0) + value
                else:
                    conflict += value

        result[omega] = result.get(omega, 0.0) + conflict
        return result
