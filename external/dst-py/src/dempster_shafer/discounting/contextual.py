"""
Basic contextual discounting methods for Dempster-Shafer theory.

This module implements basic contextual discounting methods that extend
classical discounting by considering reliability in specific contexts.
"""

from ..core.mass_function import MassFunction

def discount_contextual(mass, reliability_map):
    """
    Apply contextual discounting to a mass function.
    
    Contextual discounting takes into account the reliability of a source
    in specific contexts or for specific hypotheses.
    
    Parameters:
        mass: Mass function to discount
        reliability_map: Dictionary mapping contexts (subsets of the frame) to reliability factors
        
    Returns:
        Discounted mass function
    """
    # Convert all keys in reliability_map to frozensets
    reliability_map = {
        frozenset(h) if not isinstance(h, frozenset) else h: r 
        for h, r in reliability_map.items()
    }
    
    # Validate reliability factors
    for h, r in reliability_map.items():
        if not 0 <= r <= 1:
            raise ValueError(f"Reliability factor for {h} must be between 0 and 1")
    
    # If no reliability factors provided, return the original mass function
    if not reliability_map:
        return mass.copy()
    
    # Start with the original mass function
    result = mass.copy()
    
    # Get the universal set
    if mass.frame is not None:
        theta = frozenset(mass.frame.elements)
    else:
        # Infer frame from mass function
        elements = set()
        for h in mass:
            elements.update(h)
        theta = frozenset(elements)
    
    # Apply discounting for each context
    for context, reliability in reliability_map.items():
        # Create a specialized discounting for this context
        specialized_mass = MassFunction(frame=mass.frame)
        
        # For each focal element in the original mass function
        for h, m in result.items():
            if h.issubset(context):
                # Elements in the context are discounted
                specialized_mass[h] = reliability * m
                if theta in specialized_mass:
                    specialized_mass[theta] += (1 - reliability) * m
                else:
                    specialized_mass[theta] = (1 - reliability) * m
            else:
                # Elements outside the context are unchanged
                specialized_mass[h] = m
        
        # Update the result
        result = specialized_mass
    
    return result

def discount_contextual_simple(mass, reliability_map):
    """
    Apply a simple form of contextual discounting to a mass function.
    
    This is a simplified version where each hypothesis has its own reliability factor.
    
    Parameters:
        mass: Mass function to discount
        reliability_map: Dictionary mapping hypotheses to reliability factors
        
    Returns:
        Discounted mass function
    """
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
    
    # Convert all keys in reliability_map to frozensets
    reliability_map = {
        frozenset(h) if not isinstance(h, frozenset) else h: r 
        for h, r in reliability_map.items()
    }
    
    # First, copy all masses to the result
    for h, m in mass.items():
        result[h] = m
    
    # Then apply discounting for each hypothesis with a reliability factor
    for h, reliability in reliability_map.items():
        if not 0 <= reliability <= 1:
            raise ValueError(f"Reliability factor for {h} must be between 0 and 1")
        
        if h in mass:
            # Discount this hypothesis
            original_mass = result[h]
            result[h] = reliability * original_mass
            # Add the discounted mass to the universal set
            if theta in result:
                result[theta] += (1 - reliability) * original_mass
            else:
                result[theta] = (1 - reliability) * original_mass
    
    return result
