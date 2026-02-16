"""
Examples module initialization for Dempster-Shafer theory.

This module provides examples of using the Dempster-Shafer package.
"""

from .basic_usage import (
    basic_mass_function_example,
    combination_rules_example,
    discounting_example,
    run_all_examples as run_basic_examples
)
from .real_world import (
    medical_diagnosis_example,
    sensor_fusion_example,
    run_all_examples as run_real_world_examples
)
from .visualization import (
    mass_function_visualization_example,
    belief_plausibility_visualization_example,
    combination_rules_visualization_example,
    run_all_examples as run_visualization_examples
)

__all__ = [
    'basic_mass_function_example',
    'combination_rules_example',
    'discounting_example',
    'run_basic_examples',
    'medical_diagnosis_example',
    'sensor_fusion_example',
    'run_real_world_examples',
    'mass_function_visualization_example',
    'belief_plausibility_visualization_example',
    'combination_rules_visualization_example',
    'run_visualization_examples'
]
