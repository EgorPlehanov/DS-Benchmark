"""
Visualization module initialization for Dempster-Shafer theory.

This module provides visualization tools for mass functions, belief, and plausibility.
"""

from .plots import (
    plot_mass_function,
    plot_belief_plausibility,
    plot_comparison
)

__all__ = [
    'plot_mass_function',
    'plot_belief_plausibility',
    'plot_comparison'
]
