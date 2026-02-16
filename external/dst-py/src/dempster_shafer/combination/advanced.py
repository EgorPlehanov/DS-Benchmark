"""
Advanced combination rules for Dempster-Shafer theory.

This module provides advanced combination rules for belief functions:
- Yager's rule
- Dubois & Prade's rule
- Zhang's rule

References:
-----------
1. Yager, R. R. (1987). On the Dempster-Shafer Framework and New Combination Rules. 
   Information Sciences, 41(2), 93-137.
2. Dubois, D., & Prade, H. (1988). Representation and Combination of Uncertainty 
   with Belief Functions and Possibility Measures. Computational Intelligence, 4(3), 244-264.
3. Zhang, L. (1994). Representation, Independence, and Combination of Evidence in the 
   Dempster-Shafer Theory. Advances in the Dempster-Shafer Theory of Evidence, 51-69.
"""

from ..core.mass_function import MassFunction
from .basic import combine_conjunctive

def combine_yager(m1, m2):
    """
    Combine two mass functions using Yager's rule of combination.
    
    Yager's rule assigns conflicting mass to the universal set instead of normalizing.
    
    Formula:
        m₁⊕m₂(A) = ∑_{B∩C=A} m₁(B)m₂(C) for A ≠ ∅, A ≠ Ω
        m₁⊕m₂(Ω) = m₁(Ω)m₂(Ω) + ∑_{B∩C=∅} m₁(B)m₂(C)
    
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
    Yager, R. R. (1987). On the Dempster-Shafer Framework and New Combination Rules. 
    Information Sciences, 41(2), 93-137.
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
    
    # Get the universal set
    if frame is not None:
        universal_set = frozenset(frame.elements)
    else:
        # Infer universal set from the mass functions
        elements = set()
        for h in m1:
            elements.update(h)
        for h in m2:
            elements.update(h)
        universal_set = frozenset(elements)
    
    # Combine using the unnormalized conjunctive rule
    combined = combine_conjunctive(m1, m2, normalization=False)
    
    # Get the mass assigned to the empty set (conflict)
    empty_set = frozenset()
    conflict = combined.get(empty_set, 0.0)
    
    # Remove the empty set
    if empty_set in combined:
        del combined[empty_set]
    
    # Assign the conflict to the universal set
    if universal_set in combined:
        combined[universal_set] += conflict
    else:
        combined[universal_set] = conflict
    
    return combined

def combine_dubois_prade(m1, m2):
    """
    Combine two mass functions using Dubois & Prade's rule of combination.
    
    Dubois & Prade's rule assigns conflicting mass to the union of the focal elements.
    
    Formula:
        m₁⊕m₂(A) = ∑_{B∩C=A} m₁(B)m₂(C) + ∑_{B∩C=∅, B∪C=A} m₁(B)m₂(C)
    
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
            intersection = h1.intersection(h2)
            if intersection:
                # Non-conflicting case
                if intersection in result:
                    result[intersection] += v1 * v2
                else:
                    result[intersection] = v1 * v2
            else:
                # Conflicting case - assign to union
                union = h1.union(h2)
                if union in result:
                    result[union] += v1 * v2
                else:
                    result[union] = v1 * v2
    
    # Create mass function from result
    return MassFunction(result, frame=frame)

def combine_zhang(m1, m2):
    """
    Combine two mass functions using Zhang's rule of combination.
    
    Zhang's rule is a modification of Dempster's rule that handles conflict differently.
    
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
    Zhang, L. (1994). Representation, Independence, and Combination of Evidence in the 
    Dempster-Shafer Theory. Advances in the Dempster-Shafer Theory of Evidence, 51-69.
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
    
    # Get the universal set
    if frame is not None:
        universal_set = frozenset(frame.elements)
    else:
        # Infer universal set from the mass functions
        elements = set()
        for h in m1:
            elements.update(h)
        for h in m2:
            elements.update(h)
        universal_set = frozenset(elements)
    
    # Combine using the unnormalized conjunctive rule
    combined = combine_conjunctive(m1, m2, normalization=False)
    
    # Get the mass assigned to the empty set (conflict)
    empty_set = frozenset()
    conflict = combined.get(empty_set, 0.0)
    
    # Remove the empty set
    if empty_set in combined:
        del combined[empty_set]
    
    # Calculate plausibilities for each focal element
    pl1 = {h: m1.plausibility(h) for h in m1}
    pl2 = {h: m2.plausibility(h) for h in m2}
    
    # Redistribute conflict according to Zhang's rule
    for h in combined:
        if h != universal_set:
            # Calculate weights based on plausibilities
            w1 = pl1.get(h, 0.0)
            w2 = pl2.get(h, 0.0)
            total_weight = w1 + w2
            
            if total_weight > 0:
                # Redistribute conflict proportionally to plausibilities
                combined[h] += conflict * (w1 + w2) / total_weight
    
    return combined
