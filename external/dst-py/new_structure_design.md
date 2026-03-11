# New Structure Design for Dempster-Shafer Package

Based on Python packaging best practices and the issues identified in the current structure, here's the proposed new structure for the Dempster-Shafer package.

## Current Issues

1. **Discounting Module Duplication**: 
   - There's duplication between `classical.py` and `contextual.py`
   - There's a nested `contextual/contextual.py` with similar functionality
   - Functions like `classical_discount` and `contextual_discount` appear in multiple files

2. **Test Organization**:
   - Test files are in the root directory instead of a dedicated tests folder
   - `test_dempster_shafer.py` and `test_advanced_features.py` need to be moved

3. **Package Structure**:
   - Needs to follow Python packaging best practices with src layout
   - Missing proper documentation with paper references

## Proposed New Structure

```
dempster_shafer_project/
├── LICENSE
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── src/
│   └── dempster_shafer/
│       ├── __init__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── frame.py
│       │   ├── mass_function.py
│       │   └── utils.py
│       ├── combination/
│       │   ├── __init__.py
│       │   ├── basic.py
│       │   ├── advanced.py
│       │   ├── pcr.py
│       │   └── advanced_rules.py
│       ├── discounting/
│       │   ├── __init__.py
│       │   ├── classical.py
│       │   ├── contextual.py
│       │   └── contextual_advanced.py
│       ├── visualization/
│       │   ├── __init__.py
│       │   └── plots.py
│       └── examples/
│           ├── __init__.py
│           ├── basic_usage.py
│           ├── real_world.py
│           ├── visualization.py
│           └── advanced_examples.py
└── tests/
    ├── __init__.py
    ├── test_core.py
    ├── test_combination.py
    ├── test_discounting.py
    ├── test_visualization.py
    └── test_advanced_features.py
```

## Discounting Module Reorganization

The discounting module will be reorganized to eliminate duplication:

```
discounting/
├── __init__.py        # Exports all functions from submodules
├── classical.py       # Contains classical discounting methods only
├── contextual.py      # Contains basic contextual discounting
└── contextual_advanced.py  # Contains advanced contextual discounting (from papers)
```

### Function Organization

1. `classical.py`:
   - `discount()` (primary function)
   - `discount_classical()` (alias for backward compatibility)

2. `contextual.py`:
   - `discount_contextual()` (basic contextual discounting)
   - `discount_contextual_simple()` (simplified version)

3. `contextual_advanced.py`:
   - `contextual_discount()` (from ECSQARU 2005 paper)
   - `theta_contextual_discount()` (from ECSQARU 2005 paper)
   - `compute_generalization_matrix()` (helper function)
   - `compute_theta_generalization_matrix()` (helper function)

### Imports and Exports

The `__init__.py` file will export all functions to maintain backward compatibility:

```python
# discounting/__init__.py
from .classical import discount, discount_classical
from .contextual import discount_contextual, discount_contextual_simple
from .contextual_advanced import (
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
```

## Tests Reorganization

Tests will be moved to a dedicated `tests` directory:

1. `test_dempster_shafer.py` → `tests/test_core.py` and `tests/test_combination.py`
2. `test_advanced_features.py` → `tests/test_advanced_features.py` and `tests/test_discounting.py`

## Documentation Updates

1. Add paper references in docstrings for all functions derived from academic papers
2. Create a comprehensive README.md
3. Create a CHANGELOG.md to document all changes

## Configuration Files

1. `pyproject.toml` will be updated to follow modern Python packaging standards
2. Use `setuptools` as the build backend
3. Include proper metadata and dependencies
