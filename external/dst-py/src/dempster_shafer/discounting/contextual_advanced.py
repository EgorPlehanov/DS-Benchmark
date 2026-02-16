"""
Compatibility module for contextual advanced discounting methods.

This module provides backward compatibility for imports from the original structure.
It re-exports the functions from the contextual.contextual module.
"""

from .contextual.contextual import (
    contextual_discount,
    theta_contextual_discount,
    compute_generalization_matrix
)

__all__ = [
    'contextual_discount',
    'theta_contextual_discount',
    'compute_generalization_matrix'
]
