"""
Advanced contextual discounting methods for Dempster-Shafer theory.

This module implements advanced contextual discounting methods based on:
- "Contextual Discounting of Belief Functions" (ECSQARU 2005)
- "Conjunctive and Disjunctive Combination of Belief Functions Induced by Non-Distinct Bodies of Evidence"

The module provides functions for:
- Contextual discounting (reliability conditionally on different contexts)
- Θ-contextual discounting (using a partition of the frame of discernment)
- Generalization matrix computation
"""

import numpy as np
from itertools import chain, combinations
from ...core.mass_function import MassFunction

def powerset(iterable):
    """
    Return the power set of an iterable.
    
    powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    """
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))

def contextual_discount(mass_function, alphas):
    """
    Apply contextual discounting to a mass function.
    
    Contextual discounting extends classical discounting by considering reliability
    conditionally on different contexts (elements of the frame).
    
    Parameters:
    -----------
    mass_function : MassFunction
        The mass function to be discounted.
    alphas : dict
        Dictionary mapping elements of the frame to discount rates in [0,1].
        
    Returns:
    --------
    MassFunction
        The contextually discounted mass function.
        
    Notes:
    ------
    The contextual discounting operation is defined as:
    (α)m(A) = ∑(B⊆A) G(A,B)m(B), ∀A ⊆ Ω
    where G(A,B) is the generalization matrix.
    
    Reference:
    ----------
    "Contextual Discounting of Belief Functions" (ECSQARU 2005)
    """
    # Get all elements in the frame
    all_elements = set()
    for h in mass_function:
        all_elements.update(h)
    frame = frozenset(all_elements)
    
    # Validate alphas
    for element, alpha in alphas.items():
        if element not in all_elements:
            raise ValueError(f"Element {element} not in frame of discernment")
        if alpha < 0 or alpha > 1:
            raise ValueError(f"Discount rate for {element} must be in [0,1]")
    
    # If alphas is empty or all alphas are 0, return the original mass function
    if not alphas or all(alpha == 0 for alpha in alphas.values()):
        return mass_function.copy()
    
    # If all alphas are 1, return the vacuous belief function
    if all(alpha == 1 for alpha in alphas.values()):
        return MassFunction({frame: 1.0}, frame)
    
    # Compute the generalization matrix
    G = compute_generalization_matrix(all_elements, alphas)
    
    # Apply the generalization matrix to the mass function
    result = {}
    for A in powerset(all_elements):
        if not A:  # Skip empty set
            continue
        
        A_tuple = tuple(sorted(A))
        A_frozenset = frozenset(A)
        result[A_frozenset] = 0
        
        for B in powerset(all_elements):
            if not B:  # Skip empty set
                continue
            
            B_tuple = tuple(sorted(B))
            B_frozenset = frozenset(B)
            
            if B_frozenset in mass_function and set(B).issubset(set(A)):
                result[A_frozenset] += G.get((A_tuple, B_tuple), 0) * mass_function[B_frozenset]
    
    # Remove zero masses
    result = {k: v for k, v in result.items() if v > 0}
    
    # Normalize to ensure sum of masses is 1.0
    total_mass = sum(result.values())
    if total_mass > 0:
        result = {k: v / total_mass for k, v in result.items()}
    
    return MassFunction(result, frame)

def compute_generalization_matrix(frame, alphas):
    """
    Compute the generalization matrix for contextual discounting.
    
    Parameters:
    -----------
    frame : set or frozenset
        The frame of discernment.
    alphas : dict
        Dictionary mapping elements of the frame to discount rates in [0,1].
        
    Returns:
    --------
    dict
        The generalization matrix as a dictionary mapping (A,B) to G(A,B).
        
    Notes:
    ------
    The generalization matrix is defined as:
    G(A,B) = ∏(ωᵢ∈B) (1-αᵢ) ∏(ωⱼ∈A-B) αⱼ, ∀B ⊆ A ⊆ Ω
    
    Reference:
    ----------
    "Contextual Discounting of Belief Functions" (ECSQARU 2005)
    """
    G = {}
    
    # Ensure all elements in frame have an alpha value
    complete_alphas = {element: alphas.get(element, 0) for element in frame}
    
    # Compute G(A,B) for all A, B ⊆ Ω such that B ⊆ A
    for A in powerset(frame):
        if not A:  # Skip empty set
            continue
        
        A_tuple = tuple(sorted(A))
        
        for B in powerset(A):  # Only consider B ⊆ A
            if not B:  # Skip empty set
                continue
            
            B_tuple = tuple(sorted(B))
            
            # For G(A,B) where B is a proper subset of A
            # G(A,B) = product of (1-alpha) for elements in B
            # and product of alphas for elements in A-B
            g_value = 1.0
            
            # For elements in B, use (1-alpha)
            for element in B:
                g_value *= (1 - complete_alphas.get(element, 0))
            
            # For elements in A-B, use alpha
            for element in set(A) - set(B):
                g_value *= complete_alphas.get(element, 0)
            
            G[(A_tuple, B_tuple)] = g_value
    
    return G

def theta_contextual_discount(mass_function, theta_partition, alphas):
    """
    Apply Θ-contextual discounting to a mass function.
    
    Θ-contextual discounting generalizes contextual discounting by using a partition
    of the frame of discernment to define more general contexts.
    
    Parameters:
    -----------
    mass_function : MassFunction
        The mass function to be discounted.
    theta_partition : list of tuple
        A partition of the frame of discernment into disjoint subsets.
    alphas : dict
        Dictionary mapping elements of theta_partition to discount rates in [0,1].
        
    Returns:
    --------
    MassFunction
        The Θ-contextually discounted mass function.
        
    Notes:
    ------
    The Θ-contextual discounting operation is defined similarly to contextual discounting
    but with contexts defined by the partition Θ.
    
    Reference:
    ----------
    "Contextual Discounting of Belief Functions" (ECSQARU 2005)
    """
    # Get all elements in the frame
    all_elements = set()
    for h in mass_function:
        all_elements.update(h)
    frame = frozenset(all_elements)
    
    # Validate theta_partition
    flat_partition = [item for subset in theta_partition for item in subset]
    if set(flat_partition) != all_elements:
        raise ValueError("Theta partition must cover the entire frame of discernment")
    
    # Check for overlapping elements in the partition
    for i, subset1 in enumerate(theta_partition):
        for j, subset2 in enumerate(theta_partition):
            if i != j and set(subset1) & set(subset2):
                raise ValueError("Theta partition must consist of disjoint subsets")
    
    # Validate alphas
    for subset, alpha in alphas.items():
        if subset not in theta_partition:
            raise ValueError(f"Subset {subset} not in theta partition")
        if alpha < 0 or alpha > 1:
            raise ValueError(f"Discount rate for {subset} must be in [0,1]")
    
    # If alphas is empty or all alphas are 0, return the original mass function
    if not alphas or all(alpha == 0 for alpha in alphas.values()):
        return mass_function.copy()
    
    # If all alphas are 1, return the vacuous belief function
    if all(alpha == 1 for alpha in alphas.values()):
        return MassFunction({frame: 1.0}, frame)
    
    # Compute the generalization matrix for Θ-contextual discounting
    G = compute_theta_generalization_matrix(all_elements, theta_partition, alphas)
    
    # Apply the generalization matrix to the mass function
    result = {}
    for A in powerset(all_elements):
        if not A:  # Skip empty set
            continue
        
        A_tuple = tuple(sorted(A))
        A_frozenset = frozenset(A)
        result[A_frozenset] = 0
        
        for B in powerset(all_elements):
            if not B:  # Skip empty set
                continue
            
            B_tuple = tuple(sorted(B))
            B_frozenset = frozenset(B)
            
            if B_frozenset in mass_function and set(B).issubset(set(A)):
                result[A_frozenset] += G.get((A_tuple, B_tuple), 0) * mass_function[B_frozenset]
    
    # Remove zero masses
    result = {k: v for k, v in result.items() if v > 0}
    
    # Normalize to ensure sum of masses is 1.0
    total_mass = sum(result.values())
    if total_mass > 0:
        result = {k: v / total_mass for k, v in result.items()}
    
    return MassFunction(result, frame)

def compute_theta_generalization_matrix(frame, theta_partition, alphas):
    """
    Compute the generalization matrix for Θ-contextual discounting.
    
    Parameters:
    -----------
    frame : set or frozenset
        The frame of discernment.
    theta_partition : list of tuple
        A partition of the frame of discernment into disjoint subsets.
    alphas : dict
        Dictionary mapping elements of theta_partition to discount rates in [0,1].
        
    Returns:
    --------
    dict
        The generalization matrix as a dictionary mapping (A,B) to G(A,B).
        
    Notes:
    ------
    The generalization matrix for Θ-contextual discounting is defined similarly to
    the one for contextual discounting but with contexts defined by the partition Θ.
    
    Reference:
    ----------
    "Contextual Discounting of Belief Functions" (ECSQARU 2005)
    """
    G = {}
    
    # Ensure all subsets in theta_partition have an alpha value
    complete_alphas = {subset: alphas.get(subset, 0) for subset in theta_partition}
    
    # Compute beta values (complement of alpha)
    betas = {subset: 1 - alpha for subset, alpha in complete_alphas.items()}
    
    # Compute G(A,B) for all A, B ⊆ Ω such that B ⊆ A
    for A in powerset(frame):
        if not A:  # Skip empty set
            continue
        
        A_tuple = tuple(sorted(A))
        
        for B in powerset(A):  # Only consider B ⊆ A
            if not B:  # Skip empty set
                continue
            
            B_tuple = tuple(sorted(B))
            
            # Compute G(A,B) according to the formula for Θ-contextual discounting
            g_value = 1.0
            
            for theta in theta_partition:
                theta_set = set(theta)
                
                # If theta intersects with B, use beta (1-alpha)
                if theta_set & set(B):
                    g_value *= betas.get(theta, 1)
                # If theta does not intersect with B but intersects with A, use alpha
                elif theta_set & set(A):
                    g_value *= complete_alphas.get(theta, 0)
            
            G[(A_tuple, B_tuple)] = g_value
    
    return G
