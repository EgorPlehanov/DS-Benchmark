"""
Basic combination rules for Dempster-Shafer theory.

This module provides the basic combination rules for belief functions:
- Dempster's rule (normalized conjunctive)
- Unnormalized conjunctive rule
- Disjunctive rule

References:
-----------
1. Shafer, G. (1976). A Mathematical Theory of Evidence. Princeton University Press.
2. Smets, P. (1990). The Combination of Evidence in the Transferable Belief Model. 
   IEEE Transactions on Pattern Analysis and Machine Intelligence, 12(5), 447-458.
"""

from ..core.mass_function import MassFunction

def combine_conjunctive(m1, m2, normalization=True):
    """
    Combine two mass functions using Dempster's rule of combination.
    
    Dempster's rule of combination is a normalized conjunctive combination rule.
    
    Formula:
        m₁⊕m₂(A) = (1/K) ∑_{B∩C=A} m₁(B)m₂(C)
    
    where K = 1 - ∑_{B∩C=∅} m₁(B)m₂(C) is the normalization factor.
    
    Parameters:
    -----------
    m1 : MassFunction
        First mass function.
    m2 : MassFunction
        Second mass function.
    normalization : bool, optional
        Whether to normalize the result. Default is True.
        
    Returns:
    --------
    MassFunction
        The combined mass function.
        
    References:
    -----------
    Shafer, G. (1976). A Mathematical Theory of Evidence. Princeton University Press.
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
    
    # Initialize result
    result = {}
    
    # Calculate combined masses
    for h1, v1 in m1.items():
        for h2, v2 in m2.items():
            h = h1.intersection(h2)
            if h in result:
                result[h] += v1 * v2
            else:
                result[h] = v1 * v2
    
    # Create mass function from result
    combined = MassFunction(result, frame=frame)
    
    # Normalize if requested
    if normalization:
        combined.normalize()
    
    return combined

def combine_disjunctive(m1, m2):
    """
    Combine two mass functions using the disjunctive rule of combination.
    
    The disjunctive rule of combination is useful when one of the sources is reliable
    but we don't know which one.
    
    Formula:
        m₁⊕m₂(A) = ∑_{B∪C=A} m₁(B)m₂(C)
    
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
    Dubois, D., & Prade, H. (1988). Representation and Combination of Uncertainty 
    with Belief Functions and Possibility Measures. Computational Intelligence, 4(3), 244-264.
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
    
    # Initialize result
    result = {}
    
    # Calculate combined masses
    for h1, v1 in m1.items():
        for h2, v2 in m2.items():
            h = h1.union(h2)
            if h in result:
                result[h] += v1 * v2
            else:
                result[h] = v1 * v2
    
    # Create mass function from result
    return MassFunction(result, frame=frame)

def combine_multiple(mass_functions, combination_rule=combine_conjunctive, **kwargs):
    """
    Combine multiple mass functions using a specified combination rule.
    
    Parameters:
    -----------
    mass_functions : list of MassFunction
        List of mass functions to combine.
    combination_rule : function, optional
        Combination rule to use. Default is combine_conjunctive.
    **kwargs : dict
        Additional arguments to pass to the combination rule.
        
    Returns:
    --------
    MassFunction
        The combined mass function.
    """
    if not mass_functions:
        raise ValueError("No mass functions provided")
    
    if len(mass_functions) == 1:
        return mass_functions[0].copy()
    
    # Start with the first mass function
    result = mass_functions[0].copy()
    
    # Combine with the rest
    for m in mass_functions[1:]:
        result = combination_rule(result, m, **kwargs)
    
    return result
