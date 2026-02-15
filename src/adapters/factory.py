"""Реестр доступных адаптеров для единообразного запуска тестов."""

from typing import Dict, List, Type

from .base_adapter import BaseDempsterShaferAdapter
from .our_adapter import OurImplementationAdapter
from .pydempster_adapter import PyDempsterShaferAdapter
from .pyds_adapter import PyDSAdapter


ADAPTER_REGISTRY: Dict[str, Type[BaseDempsterShaferAdapter]] = {
    "our": OurImplementationAdapter,
    "pyds": PyDSAdapter,
    "py_dempster_shafer": PyDempsterShaferAdapter,
}

ALIASES: Dict[str, str] = {
    "ourimplementation": "our",
    "pyds": "pyds",
    "pydempster": "py_dempster_shafer",
    "pydempstershafer": "py_dempster_shafer",
}


def create_adapter(name: str) -> BaseDempsterShaferAdapter:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in ADAPTER_REGISTRY:
        supported = ", ".join(sorted(ADAPTER_REGISTRY))
        raise ValueError(f"Unsupported adapter: {name}. Supported: {supported}")
    return ADAPTER_REGISTRY[key]()


def list_adapters() -> List[str]:
    return sorted(ADAPTER_REGISTRY.keys())
