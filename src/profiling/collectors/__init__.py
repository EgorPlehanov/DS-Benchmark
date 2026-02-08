# src/profiling/collectors/__init__.py
"""
Пакет коллекторов для профилирования.
"""

from .system_collector import SystemCollector, create_system_collector, system_collector

__all__ = [
    'SystemCollector',
    'create_system_collector',
    'system_collector',
]