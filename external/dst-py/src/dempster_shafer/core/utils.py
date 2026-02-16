"""
Core utilities for the Dempster-Shafer theory package.

This module provides utility functions for set operations and other
common operations used throughout the package.
"""

def powerset(iterable):
    """
    Return the power set of an iterable.
    
    The power set of a set S is the set of all subsets of S, including the
    empty set and S itself.
    
    Parameters:
    -----------
    iterable : iterable
        The input set or iterable.
        
    Returns:
    --------
    list
        A list containing all subsets of the input set.
        
    Examples:
    ---------
    >>> list(powerset([1, 2, 3]))
    [(), (1,), (2,), (3,), (1, 2), (1, 3), (2, 3), (1, 2, 3)]
    """
    from itertools import chain, combinations
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))

def normalize_masses(masses):
    """
    Normalize a dictionary of masses to ensure they sum to 1.
    
    Parameters:
    -----------
    masses : dict
        Dictionary mapping focal sets to mass values.
        
    Returns:
    --------
    dict
        Normalized dictionary of masses.
    """
    total = sum(masses.values())
    if total == 0:
        return masses
    return {k: v / total for k, v in masses.items()}

def calculate_conflict(m1, m2):
    """
    Calculate the conflict between two mass functions.
    
    The conflict is the sum of the products of masses assigned to sets
    with empty intersection.
    
    Parameters:
    -----------
    m1 : dict
        First mass function as a dictionary mapping focal sets to mass values.
    m2 : dict
        Second mass function as a dictionary mapping focal sets to mass values.
        
    Returns:
    --------
    float
        The conflict value between 0 and 1.
    """
    conflict = 0.0
    for A, mass_A in m1.items():
        for B, mass_B in m2.items():
            if not A.intersection(B):
                conflict += mass_A * mass_B
    return conflict
