"""Адаптер для пакета dempster_shafer."""

from __future__ import annotations

from typing import Any, Dict, List, Union

from ..base_adapter import BaseDempsterShaferAdapter
from .common import AdapterFormatMixin, OptionalDependencyAdapterMixin


class DempsterShaferPyAdapter(OptionalDependencyAdapterMixin, AdapterFormatMixin, BaseDempsterShaferAdapter):
    module_name = "dempster_shafer"

    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:
        self.require_module()
        frame_elements = dass_data["frame_of_discernment"]
        bpas = []
        for source in dass_data["bba_sources"]:
            bpas.append({self.parse_subset_str(k): float(v) for k, v in source["bba"].items()})
        return {"frame_elements": frame_elements, "bpas": bpas}

    def get_frame_of_discernment(self, data: Any) -> List[str]:
        return data.get("frame_elements", []) if isinstance(data, dict) else []

    def get_sources_count(self, data: Any) -> int:
        return len(data.get("bpas", [])) if isinstance(data, dict) else 0

    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        module = self.require_module()
        event_set = self.parse_subset_str(event) if isinstance(event, str) else frozenset(event)
        bpa = self._extract_one_bpa(data)
        if not hasattr(module, "belief"):
            raise RuntimeError("В библиотеке dempster_shafer не найдена функция belief")
        return float(module.belief(bpa, event_set))

    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        module = self.require_module()
        event_set = self.parse_subset_str(event) if isinstance(event, str) else frozenset(event)
        bpa = self._extract_one_bpa(data)
        if not hasattr(module, "plausibility"):
            raise RuntimeError("В библиотеке dempster_shafer не найдена функция plausibility")
        return float(module.plausibility(bpa, event_set))

    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        module = self.require_module()
        bpas = self._extract_all_bpas(data)
        if not bpas:
            return {}
        if not hasattr(module, "combine_dempster"):
            raise RuntimeError("В библиотеке dempster_shafer не найдена функция combine_dempster")

        current = bpas[0]
        for bpa in bpas[1:]:
            current = module.combine_dempster(current, bpa)
        return self.format_bpa(current)

    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        module = self.require_module()
        if not hasattr(module, "discount"):
            raise RuntimeError("В библиотеке dempster_shafer не найдена функция discount")
        return [self.format_bpa(module.discount(bpa, alpha)) for bpa in self._extract_all_bpas(data)]

    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        module = self.require_module()
        bpas = self._extract_all_bpas(data)
        if not bpas:
            return {}
        if not hasattr(module, "combine_yager"):
            raise RuntimeError("В библиотеке dempster_shafer не найдена функция combine_yager")

        current = bpas[0]
        for bpa in bpas[1:]:
            current = module.combine_yager(current, bpa)
        return self.format_bpa(current)

    def _extract_one_bpa(self, data: Any):
        if isinstance(data, dict) and data.get("bpas"):
            return data["bpas"][0]
        if isinstance(data, dict) and data and isinstance(next(iter(data.keys())), frozenset):
            return data
        raise TypeError("Не удалось извлечь BPA")

    @staticmethod
    def _extract_all_bpas(data: Any):
        return data.get("bpas", []) if isinstance(data, dict) else []
