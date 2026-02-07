# src/profiling/runners/__init__.py
"""
Пакет раннеров для профилирования.
"""

from .simple_profiling_runner import SimpleProfilingRunner, create_profiling_runner

__all__ = [
    'SimpleProfilingRunner',
    'create_profiling_runner'
]