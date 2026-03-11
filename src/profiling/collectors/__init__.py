# src/profiling/collectors/__init__.py
"""
Пакет коллекторов для профилирования.
"""

from .system_collector import SystemCollector, create_system_collector, system_collector
from .scalene_collector import ScaleneCollector

__all__ = [
    'SystemCollector',
    'create_system_collector',
    'system_collector',
    'ScaleneCollector',
]
