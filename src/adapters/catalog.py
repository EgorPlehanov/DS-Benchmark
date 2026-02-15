"""Каталог и фабрика адаптеров для бенчмарков Демпстера-Шейфера."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec
from typing import Callable, Dict, List, Optional, Type

from .base_adapter import BaseDempsterShaferAdapter
from .external import DempsterShaferPyAdapter, PyDSAdapter
from .our_adapter import OurImplementationAdapter


@dataclass(frozen=True)
class AdapterSpec:
    """Описание подключаемого адаптера."""

    key: str
    title: str
    adapter_cls: Type[BaseDempsterShaferAdapter]
    dependency: Optional[str] = None

    def status(self) -> str:
        if self.dependency is None:
            return "available"
        return "available" if find_spec(self.dependency) is not None else "missing_dependency"

    def is_available(self) -> bool:
        return self.status() == "available"

    def create(self) -> BaseDempsterShaferAdapter:
        return self.adapter_cls()


ADAPTER_SPECS: Dict[str, AdapterSpec] = {
    "our": AdapterSpec(
        key="our",
        title="Наша реализация (dempster_core)",
        adapter_cls=OurImplementationAdapter,
        dependency=None,
    ),
    "pyds": AdapterSpec(
        key="pyds",
        title="PyDS (MassFunction)",
        adapter_cls=PyDSAdapter,
        dependency="pyds",
    ),
    "dempster_shafer": AdapterSpec(
        key="dempster_shafer",
        title="python-package dempster_shafer",
        adapter_cls=DempsterShaferPyAdapter,
        dependency="dempster_shafer",
    ),
}


def adapter_choices() -> List[str]:
    """Список ключей для CLI choices."""
    return sorted(ADAPTER_SPECS.keys())


def get_adapter_spec(key: str) -> AdapterSpec:
    spec = ADAPTER_SPECS.get(key)
    if spec is None:
        available = ", ".join(adapter_choices())
        raise ValueError(f"Неизвестный адаптер '{key}'. Доступные варианты: {available}")
    return spec


def create_adapter(key: str, *, require_available: bool = True) -> BaseDempsterShaferAdapter:
    """Создает адаптер по ключу.

    Args:
        key: Идентификатор адаптера.
        require_available: Если True, выбрасывает RuntimeError,
            когда внешний dependency отсутствует.
    """
    spec = get_adapter_spec(key)
    if require_available and not spec.is_available():
        raise RuntimeError(
            f"Адаптер '{key}' недоступен: отсутствует зависимость '{spec.dependency}'."
        )
    return spec.create()


def list_adapter_options() -> List[Dict[str, str]]:
    """Сводная информация для CLI/логирования."""
    result: List[Dict[str, str]] = []
    for spec in ADAPTER_SPECS.values():
        result.append(
            {
                "key": spec.key,
                "title": spec.title,
                "dependency": spec.dependency or "builtin",
                "status": spec.status(),
            }
        )
    return result
