"""Адаптер для библиотеки pyds."""

from __future__ import annotations

from typing import Any, Dict, List, Union

from ..base_adapter import BaseDempsterShaferAdapter
from .common import AdapterFormatMixin, OptionalDependencyAdapterMixin


class PyDSAdapter(OptionalDependencyAdapterMixin, AdapterFormatMixin, BaseDempsterShaferAdapter):
    module_name = "pyds"

    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:
        pyds = self.require_module()
        frame_elements = dass_data["frame_of_discernment"]
        bpas = []
        for source in dass_data["bba_sources"]:
            masses = {self.parse_subset_str(k): float(v) for k, v in source["bba"].items()}
            bpas.append(pyds.MassFunction(masses))
        return {"frame_elements": frame_elements, "bpas": bpas}

    def get_frame_of_discernment(self, data: Any) -> List[str]:
        return data.get("frame_elements", []) if isinstance(data, dict) else []

    def get_sources_count(self, data: Any) -> int:
        return len(data.get("bpas", [])) if isinstance(data, dict) else 0

    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        mass_function = self._extract_one_bpa(data)
        event_set = self._parse_event(event)
        return float(mass_function.bel(event_set))

    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        mass_function = self._extract_one_bpa(data)
        event_set = self._parse_event(event)
        return float(mass_function.pl(event_set))

    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        bpas = self._extract_all_bpas(data)
        if not bpas:
            return {}

        current = bpas[0]
        for mass_function in bpas[1:]:
            current = current.combine_conjunctive(mass_function, normalization=True)
        return self.format_bpa(dict(current.items()))

    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        return [self.format_bpa(dict(mf.discount(alpha).items())) for mf in self._extract_all_bpas(data)]

    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        bpas = self._extract_all_bpas(data)
        if not bpas:
            return {}

        current = dict(bpas[0].items())
        omega = frozenset(self.get_frame_of_discernment(data))
        for mass_function in bpas[1:]:
            current = self._yager_pairwise(current, dict(mass_function.items()), omega)
        return self.format_bpa(current)

    def _extract_one_bpa(self, data: Any):
        if hasattr(data, "bel") and hasattr(data, "pl"):
            return data
        if isinstance(data, dict) and data.get("bpas"):
            return data["bpas"][0]
        raise TypeError("Не удалось извлечь MassFunction из входных данных")

    @staticmethod
    def _extract_all_bpas(data: Any):
        return data.get("bpas", []) if isinstance(data, dict) else []

    def _parse_event(self, event: Union[str, List[str]]) -> set:
        if isinstance(event, str):
            return set(self.parse_subset_str(event))
        if isinstance(event, list):
            return set(event)
        raise TypeError(f"Не поддерживается тип события: {type(event)}")

    @staticmethod
    def _yager_pairwise(m1: Dict[frozenset, float], m2: Dict[frozenset, float], omega: frozenset) -> Dict[frozenset, float]:
        result: Dict[frozenset, float] = {}
        conflict = 0.0
        for subset_a, mass_a in m1.items():
            for subset_b, mass_b in m2.items():
                intersection = subset_a & subset_b
                pair_mass = mass_a * mass_b
                if not intersection:
                    conflict += pair_mass
                else:
                    result[intersection] = result.get(intersection, 0.0) + pair_mass
        result[omega] = result.get(omega, 0.0) + conflict
        return result
