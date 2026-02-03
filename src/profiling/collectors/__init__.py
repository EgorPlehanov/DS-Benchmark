# src/profiling/collectors/__init__.py
"""
Модуль коллекторов для профилирования.
"""

from .system_profiler import SystemProfiler, SystemMetrics

__all__ = ['SystemProfiler', 'SystemMetrics']