"""
Combination module initialization for Dempster-Shafer theory.

This module provides various combination rules for belief functions.
"""

from .basic import (
    combine_conjunctive,
    combine_disjunctive,
    combine_multiple
)
from .advanced import (
    combine_yager,
    combine_dubois_prade,
    combine_zhang
)
from .pcr import (
    combine_pcr5,
    combine_pcr6
)
from .advanced_rules import (
    cautious_conjunctive_rule,
    bold_disjunctive_rule,
    canonical_conjunctive_decomposition,
    weight_function
)

__all__ = [
    'combine_conjunctive',
    'combine_disjunctive',
    'combine_multiple',
    'combine_yager',
    'combine_dubois_prade',
    'combine_zhang',
    'combine_pcr5',
    'combine_pcr6',
    'cautious_conjunctive_rule',
    'bold_disjunctive_rule',
    'canonical_conjunctive_decomposition',
    'weight_function'
]
