"""
Advanced combination rules for Dempster-Shafer theory.

This module provides advanced combination rules for belief functions:
- Cautious conjunctive rule
- Bold disjunctive rule
- Canonical conjunctive decomposition
- Weight function calculation

References:
-----------
1. Denœux, T. (2008). Conjunctive and Disjunctive Combination of Belief Functions 
   Induced by Non-Distinct Bodies of Evidence. Artificial Intelligence, 172(2-3), 234-264.
"""

import math
import numpy as np
from ..core.mass_function import MassFunction

def weight_function(mass_function):
    """
    Calculate the weight function of a mass function.
    
    The weight function is used in the cautious conjunctive rule and bold disjunctive rule.
    
    Parameters:
    -----------
    mass_function : MassFunction
        The mass function to calculate weights for.
        
    Returns:
    --------
    dict
        Dictionary mapping focal sets to weight values.
        
    References:
    -----------
    Denœux, T. (2008). Conjunctive and Disjunctive Combination of Belief Functions 
    Induced by Non-Distinct Bodies of Evidence. Artificial Intelligence, 172(2-3), 234-264.
    """
    # Get all elements in the frame
    all_elements = set()
    for h in mass_function:
        all_elements.update(h)
    
    # Calculate commonality for each subset
    q = {}
    for A in powerset(all_elements):
        if not A:  # Skip empty set
            continue
        A_frozenset = frozenset(A)
        q[A_frozenset] = mass_function.commonality(A_frozenset)
    
    # Calculate weights
    weights = {}
    for A in q:
        if len(A) == 1:  # Singleton sets
            continue
            
        # Calculate weight using the commonality function
        w_A = 1.0
        for B in q:
            if B.issubset(A) and B != A:
                if len(B) % 2 == len(A) % 2:
                    w_A *= q[B]
                else:
                    w_A /= q[B]
        
        # Take the appropriate root
        if q[A] > 0:
            weights[A] = w_A ** (1.0 / (len(A) - 1))
        else:
            weights[A] = 0.0
    
    return weights

def canonical_conjunctive_decomposition(mass_function):
    """
    Compute the canonical conjunctive decomposition of a mass function.
    
    The canonical conjunctive decomposition expresses a mass function as a
    conjunctive combination of simple support functions.
    
    Parameters:
    -----------
    mass_function : MassFunction
        The mass function to decompose.
        
    Returns:
    --------
    dict
        Dictionary mapping focal sets to weight values.
        
    References:
    -----------
    Denœux, T. (2008). Conjunctive and Disjunctive Combination of Belief Functions 
    Induced by Non-Distinct Bodies of Evidence. Artificial Intelligence, 172(2-3), 234-264.
    """
    # Check if the mass function is dogmatic (has mass on empty set)
    if frozenset() in mass_function and mass_function[frozenset()] > 0:
        raise ValueError("Cannot decompose a dogmatic mass function")
    
    # Calculate weights
    return weight_function(mass_function)

def cautious_conjunctive_rule(m1, m2):
    """
    Combine two mass functions using the cautious conjunctive rule.
    
    The cautious rule is designed for combining belief functions induced by
    non-distinct bodies of evidence.
    
    Parameters:
    -----------
    m1 : MassFunction
        First mass function.
    m2 : MassFunction
        Second mass function.
        
    Returns:
    --------
    MassFunction
        The combined mass function.
        
    References:
    -----------
    Denœux, T. (2008). Conjunctive and Disjunctive Combination of Belief Functions 
    Induced by Non-Distinct Bodies of Evidence. Artificial Intelligence, 172(2-3), 234-264.
    """
    # Check if frames are compatible
    if m1.frame is not None and m2.frame is not None:
        if m1.frame.elements != m2.frame.elements:
            raise ValueError("Frames of discernment must be compatible")
    
    # Determine the frame of the result
    if m1.frame is not None:
        frame = m1.frame
    elif m2.frame is not None:
        frame = m2.frame
    else:
        frame = None
    
    # Get all elements in the frame
    all_elements = set()
    for h in m1:
        all_elements.update(h)
    for h in m2:
        all_elements.update(h)
    
    # Calculate weights for both mass functions
    w1 = canonical_conjunctive_decomposition(m1)
    w2 = canonical_conjunctive_decomposition(m2)
    
    # Combine weights by taking the minimum
    combined_weights = {}
    for A in set(w1.keys()).union(w2.keys()):
        combined_weights[A] = min(w1.get(A, 1.0), w2.get(A, 1.0))
    
    # Reconstruct the mass function from the combined weights
    # This is a complex process that involves calculating the commonality function
    # and then converting it back to a mass function
    
    # Initialize commonality with 1 for all subsets
    q = {frozenset(A): 1.0 for A in powerset(all_elements) if A}
    
    # Calculate commonality from weights
    for A, w in combined_weights.items():
        for B in powerset(all_elements):
            if B and A.issubset(B):
                if len(A) % 2 == 0:
                    q[frozenset(B)] /= w
                else:
                    q[frozenset(B)] *= w
    
    # Convert commonality to mass function
    result = {}
    for A in q:
        result[A] = 0.0
        for B in q:
            if A.issubset(B):
                if len(B) - len(A) % 2 == 0:
                    result[A] += q[B]
                else:
                    result[A] -= q[B]
    
    # Create mass function from result
    return MassFunction(result, frame=frame)

def bold_disjunctive_rule(m1, m2):
    """
    Combine two mass functions using the bold disjunctive rule.
    
    The bold disjunctive rule is the dual of the cautious conjunctive rule.
    
    Parameters:
    -----------
    m1 : MassFunction
        First mass function.
    m2 : MassFunction
        Second mass function.
        
    Returns:
    --------
    MassFunction
        The combined mass function.
        
    References:
    -----------
    Denœux, T. (2008). Conjunctive and Disjunctive Combination of Belief Functions 
    Induced by Non-Distinct Bodies of Evidence. Artificial Intelligence, 172(2-3), 234-264.
    """
    # Check if frames are compatible
    if m1.frame is not None and m2.frame is not None:
        if m1.frame.elements != m2.frame.elements:
            raise ValueError("Frames of discernment must be compatible")
    
    # Determine the frame of the result
    if m1.frame is not None:
        frame = m1.frame
    elif m2.frame is not None:
        frame = m2.frame
    else:
        frame = None
    
    # Get all elements in the frame
    all_elements = set()
    for h in m1:
        all_elements.update(h)
    for h in m2:
        all_elements.update(h)
    
    # Calculate weights for both mass functions
    v1 = canonical_conjunctive_decomposition(m1)
    v2 = canonical_conjunctive_decomposition(m2)
    
    # Combine weights by taking the maximum
    combined_weights = {}
    for A in set(v1.keys()).union(v2.keys()):
        combined_weights[A] = max(v1.get(A, 0.0), v2.get(A, 0.0))
    
    # Reconstruct the mass function from the combined weights
    # This is a complex process that involves calculating the commonality function
    # and then converting it back to a mass function
    
    # Initialize commonality with 1 for all subsets
    q = {frozenset(A): 1.0 for A in powerset(all_elements) if A}
    
    # Calculate commonality from weights
    for A, w in combined_weights.items():
        for B in powerset(all_elements):
            if B and A.issubset(B):
                if len(A) % 2 == 0:
                    q[frozenset(B)] /= w
                else:
                    q[frozenset(B)] *= w
    
    # Convert commonality to mass function
    result = {}
    for A in q:
        result[A] = 0.0
        for B in q:
            if A.issubset(B):
                if len(B) - len(A) % 2 == 0:
                    result[A] += q[B]
                else:
                    result[A] -= q[B]
    
    # Create mass function from result
    return MassFunction(result, frame=frame)

def powerset(iterable):
    """
    Return the power set of an iterable.
    
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    from itertools import chain, combinations
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))
