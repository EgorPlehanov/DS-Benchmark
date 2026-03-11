"""
Discounting module initialization for Dempster-Shafer theory.

This module provides various discounting methods for belief functions.
"""

from .classical import discount, discount_classical
from .contextual import (
    discount_contextual,
    discount_contextual_simple,
    contextual_discount,
    theta_contextual_discount,
    compute_generalization_matrix,
    compute_theta_generalization_matrix
)

__all__ = [
    'discount',
    'discount_classical',
    'discount_contextual',
    'discount_contextual_simple',
    'contextual_discount',
    'theta_contextual_discount',
    'compute_generalization_matrix',
    'compute_theta_generalization_matrix'
]
