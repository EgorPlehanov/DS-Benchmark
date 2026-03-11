"""
Classical discounting methods for Dempster-Shafer theory.

This module implements the classical discounting approach introduced by Shafer.
"""

from ..core.mass_function import MassFunction

def discount(mass, reliability):
    """
    Apply classical discounting to a mass function.
    
    Formula:
        m^α(A) = α * m(A) for A ≠ Θ
        m^α(Θ) = (1-α) + α * m(Θ)
    
    Parameters:
        mass: Mass function to discount
        reliability: Reliability factor α ∈ [0,1]
        
    Returns:
        Discounted mass function
    """
    if not 0 <= reliability <= 1:
        raise ValueError("Reliability factor must be between 0 and 1")
    
    if reliability == 1:
        return mass.copy()  # No discounting needed
    
    if reliability == 0:
        # Complete discounting - return vacuous belief assignment
        if mass.frame is not None:
            theta = frozenset(mass.frame.elements)
        else:
            # Infer frame from mass function
            elements = set()
            for h in mass:
                elements.update(h)
            theta = frozenset(elements)
        
        return MassFunction({theta: 1.0}, frame=mass.frame)
    
    result = MassFunction(frame=mass.frame)
    
    # Get the universal set
    if mass.frame is not None:
        theta = frozenset(mass.frame.elements)
    else:
        # Infer frame from mass function
        elements = set()
        for h in mass:
            elements.update(h)
        theta = frozenset(elements)
    
    # Apply discounting formula
    for h, m in mass.items():
        if h == theta:  # Universal set
            result[h] = reliability * m + (1 - reliability)
        else:
            result[h] = reliability * m
    
    return result

# Alias for backward compatibility
discount_classical = discount
