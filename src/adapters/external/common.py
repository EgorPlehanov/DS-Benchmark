"""Общие утилиты для внешних адаптеров Демпстера-Шейфера."""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from typing import Dict, Union


class OptionalDependencyAdapterMixin:
    """Переиспользуемая проверка и загрузка опциональной зависимости адаптера."""

    module_name: str = ""

    @classmethod
    def is_available(cls) -> bool:
        return bool(cls.module_name) and find_spec(cls.module_name) is not None

    def require_module(self):
        if not self.module_name:
            raise RuntimeError("Не задано имя python-модуля для адаптера")
        if not self.is_available():
            raise RuntimeError(
                f"Адаптер '{self.__class__.__name__}' недоступен: отсутствует зависимость '{self.module_name}'."
            )
        return import_module(self.module_name)


class AdapterFormatMixin:
    """Унифицированные конвертеры форматов подмножеств/BPA."""

    @staticmethod
    def parse_subset_str(subset_str: str) -> frozenset:
        if subset_str == "{}":
            return frozenset()
        parts = [p for p in subset_str.strip("{}").split(",") if p]
        return frozenset(parts)

    @staticmethod
    def format_subset(subset: Union[set, frozenset]) -> str:
        if not subset:
            return "{}"
        return "{" + ",".join(sorted(subset)) + "}"

    @classmethod
    def format_bpa(cls, bpa: Dict[Union[set, frozenset], float]) -> Dict[str, float]:
        return {cls.format_subset(set(subset)): round(mass, 10) for subset, mass in bpa.items()}
