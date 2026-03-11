"""
Contextual discounting module initialization.

This module provides advanced contextual discounting methods for belief functions.
"""

from .contextual import (
    contextual_discount,
    theta_contextual_discount,
    compute_generalization_matrix,
    compute_theta_generalization_matrix
)

# Alias the functions to maintain backward compatibility
discount_contextual = contextual_discount
discount_contextual_simple = theta_contextual_discount

__all__ = [
    'contextual_discount',
    'theta_contextual_discount',
    'compute_generalization_matrix',
    'compute_theta_generalization_matrix',
    'discount_contextual',
    'discount_contextual_simple'
]
