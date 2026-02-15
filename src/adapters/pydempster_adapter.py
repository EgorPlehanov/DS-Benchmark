"""Адаптер для библиотеки py_dempster_shafer (если установлена)."""

from typing import Any, Dict, List, Union

from .base_adapter import BaseDempsterShaferAdapter


class PyDempsterShaferAdapter(BaseDempsterShaferAdapter):
    """Адаптер внешней реализации py_dempster_shafer с fallback-ошибкой при отсутствии пакета."""

    def __init__(self):
        self._backend = None

    def _ensure_backend(self):
        if self._backend is not None:
            return
        try:
            import py_dempster_shafer as backend  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "Для использования PyDempsterShaferAdapter установите пакет `py_dempster_shafer`."
            ) from exc
        self._backend = backend

    def load_from_dass(self, dass_data: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure_backend()
        frame_elements = dass_data["frame_of_discernment"]
        bpas: List[Dict[str, float]] = []
        for source in dass_data["bba_sources"]:
            bpas.append(dict(source["bba"]))
        return {
            "frame": set(frame_elements),
            "frame_elements": frame_elements,
            "bpas": bpas,
        }

    def get_frame_of_discernment(self, data: Any) -> List[str]:
        return data.get("frame_elements", []) if isinstance(data, dict) else []

    def get_sources_count(self, data: Any) -> int:
        return len(data.get("bpas", [])) if isinstance(data, dict) else 0

    def calculate_belief(self, data: Any, event: Union[str, List[str]]) -> float:
        self._ensure_backend()
        bpa = self._extract_bpa(data)
        event_key = self._normalize_event(event)
        return float(self._backend.belief(bpa, event_key))

    def calculate_plausibility(self, data: Any, event: Union[str, List[str]]) -> float:
        self._ensure_backend()
        bpa = self._extract_bpa(data)
        event_key = self._normalize_event(event)
        return float(self._backend.plausibility(bpa, event_key))

    def combine_sources_dempster(self, data: Any) -> Dict[str, float]:
        self._ensure_backend()
        bpas = data.get("bpas", [])
        if not bpas:
            return {}
        result = dict(bpas[0])
        for bpa in bpas[1:]:
            result = self._backend.combine_dempster(result, bpa)
        return {k: round(float(v), 10) for k, v in result.items()}

    def apply_discounting(self, data: Any, alpha: float) -> List[Dict[str, float]]:
        self._ensure_backend()
        return [
            {k: round(float(v), 10) for k, v in self._backend.discount(bpa, alpha).items()}
            for bpa in data.get("bpas", [])
        ]

    def combine_sources_yager(self, data: Any) -> Dict[str, float]:
        self._ensure_backend()
        bpas = data.get("bpas", [])
        if not bpas:
            return {}
        result = dict(bpas[0])
        for bpa in bpas[1:]:
            result = self._backend.combine_yager(result, bpa)
        return {k: round(float(v), 10) for k, v in result.items()}

    def _extract_bpa(self, data: Any) -> Dict[str, float]:
        if isinstance(data, dict) and "bpa" in data:
            return data["bpa"]
        if isinstance(data, dict) and data.get("bpas"):
            return data["bpas"][0]
        return {}

    def _normalize_event(self, event: Union[str, List[str]]) -> str:
        if isinstance(event, str):
            return event
        return "{" + ",".join(sorted(event)) + "}"
