"""
Package initialization for Dempster-Shafer theory.

This package provides a comprehensive implementation of Dempster-Shafer theory,
including various combination rules and discounting methods.
"""

from .core import Frame, MassFunction
from .combination import (
    combine_conjunctive,
    combine_disjunctive,
    combine_multiple,
    combine_yager,
    combine_dubois_prade,
    combine_pcr5,
    combine_pcr6,
    cautious_conjunctive_rule,
    bold_disjunctive_rule
)
from .discounting import (
    discount,
    discount_classical,
    discount_contextual,
    discount_contextual_simple,
    contextual_discount,
    theta_contextual_discount
)

__all__ = [
    'Frame',
    'MassFunction',
    'combine_conjunctive',
    'combine_disjunctive',
    'combine_multiple',
    'combine_yager',
    'combine_dubois_prade',
    'combine_pcr5',
    'combine_pcr6',
    'cautious_conjunctive_rule',
    'bold_disjunctive_rule',
    'discount',
    'discount_classical',
    'discount_contextual',
    'discount_contextual_simple',
    'contextual_discount',
    'theta_contextual_discount'
]
