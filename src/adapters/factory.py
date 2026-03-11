"""Реестр доступных адаптеров для единообразного запуска тестов."""

from typing import Dict, List, Type

from .base_adapter import BaseDempsterShaferAdapter
from .dstpy_adapter import DstPyAdapter
from .dstz_adapter import DstzAdapter
from .our_adapter import OurImplementationAdapter
from .pyds_adapter import PyDempsterShaferAdapter


ADAPTER_REGISTRY: Dict[str, Type[BaseDempsterShaferAdapter]] = {
    "our": OurImplementationAdapter,
    "dst_py": DstPyAdapter,
    "dstz": DstzAdapter,
    "pyds": PyDempsterShaferAdapter,
}

ALIASES: Dict[str, str] = {
    "ourimplementation": "our",
    "pydempstershafer": "pyds",
    "py_dempster_shafer": "pyds",
    "dstpy": "dst_py",
}


def create_adapter(name: str) -> BaseDempsterShaferAdapter:
    key = name.strip().lower()
    key = ALIASES.get(key, key)
    if key not in ADAPTER_REGISTRY:
        supported = ", ".join(sorted(ADAPTER_REGISTRY))
        raise ValueError(f"Unsupported adapter: {name}. Supported: {supported}")
    return ADAPTER_REGISTRY[key]()


def list_adapters() -> List[str]:
    return sorted(set(ADAPTER_REGISTRY.keys()) | set(ALIASES.keys()))
