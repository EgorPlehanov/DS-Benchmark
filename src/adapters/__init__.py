# src/adapters/__init__.py
"""
Пакет адаптеров для библиотек Демпстера-Шейфера.
"""

from .base_adapter import BaseDempsterShaferAdapter
from .our_adapter import OurImplementationAdapter

__all__ = ['BaseDempsterShaferAdapter', 'OurImplementationAdapter']