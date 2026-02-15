"""Внешние адаптеры теории Демпстера-Шейфера."""

from .dempster_shafer_adapter import DempsterShaferPyAdapter
from .pyds_adapter import PyDSAdapter

__all__ = ["PyDSAdapter", "DempsterShaferPyAdapter"]
