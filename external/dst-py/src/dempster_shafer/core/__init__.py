"""
Core module initialization for Dempster-Shafer theory.

This module provides the core functionality for Dempster-Shafer theory,
including Frame and MassFunction classes.
"""

from .frame import Frame
from .mass_function import MassFunction
from .utils import powerset, normalize_masses, calculate_conflict

__all__ = [
    'Frame',
    'MassFunction',
    'powerset',
    'normalize_masses',
    'calculate_conflict'
]
