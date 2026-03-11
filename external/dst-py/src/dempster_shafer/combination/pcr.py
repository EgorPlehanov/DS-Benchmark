"""
PCR (Proportional Conflict Redistribution) combination rules for Dempster-Shafer theory.

This module provides PCR5 and PCR6 combination rules for belief functions.

References:
-----------
1. Smarandache, F., & Dezert, J. (2005). Information Fusion Based on New Proportional 
   Conflict Redistribution Rules. Information Fusion, 8(3), 387-393.
2. Martin, A., & Osswald, C. (2006). A new generalization of the proportional conflict 
   redistribution rule stable in terms of decision. Advances and Applications of DSmT 
   for Information Fusion, 2, 69-88.
"""

from ..core.mass_function import MassFunction
from .basic import combine_conjunctive

def combine_pcr5(m1, m2):
    """
    Combine two mass functions using PCR5 rule of combination.
    
    PCR5 redistributes the conflicting mass proportionally to the masses of the elements
    involved in the conflict.
    
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
    Smarandache, F., & Dezert, J. (2005). Information Fusion Based on New Proportional 
    Conflict Redistribution Rules. Information Fusion, 8(3), 387-393.
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
    
    # Combine using the unnormalized conjunctive rule
    combined = combine_conjunctive(m1, m2, normalization=False)
    
    # Get the mass assigned to the empty set (conflict)
    empty_set = frozenset()
    conflict = combined.get(empty_set, 0.0)
    
    # Remove the empty set
    if empty_set in combined:
        del combined[empty_set]
    
    # If no conflict, return the combined mass function
    if conflict == 0:
        return combined
    
    # Initialize result with the combined mass function
    result = {h: m for h, m in combined.items()}
    
    # Redistribute conflict according to PCR5 rule
    for h1, v1 in m1.items():
        for h2, v2 in m2.items():
            if not h1.intersection(h2):
                # Conflicting focal elements
                # Calculate the proportion of conflict to redistribute
                total = v1 + v2
                if total > 0:
                    # Redistribute to h1
                    if h1 in result:
                        result[h1] += v1 * v2 * v1 / total
                    else:
                        result[h1] = v1 * v2 * v1 / total
                    
                    # Redistribute to h2
                    if h2 in result:
                        result[h2] += v1 * v2 * v2 / total
                    else:
                        result[h2] = v1 * v2 * v2 / total
    
    # Create mass function from result
    return MassFunction(result, frame=frame)

def combine_pcr6(mass_functions):
    """
    Combine multiple mass functions using PCR6 rule of combination.
    
    PCR6 is a generalization of PCR5 for combining more than two mass functions.
    
    Parameters:
    -----------
    mass_functions : list of MassFunction
        List of mass functions to combine.
        
    Returns:
    --------
    MassFunction
        The combined mass function.
        
    References:
    -----------
    Martin, A., & Osswald, C. (2006). A new generalization of the proportional conflict 
    redistribution rule stable in terms of decision. Advances and Applications of DSmT 
    for Information Fusion, 2, 69-88.
    """
    if not mass_functions:
        raise ValueError("No mass functions provided")
    
    if len(mass_functions) == 1:
        return mass_functions[0].copy()
    
    if len(mass_functions) == 2:
        # PCR6 coincides with PCR5 for two sources
        return combine_pcr5(mass_functions[0], mass_functions[1])
    
    # Determine the frame of the result
    frame = None
    for m in mass_functions:
        if m.frame is not None:
            frame = m.frame
            break
    
    # Check if frames are compatible
    if frame is not None:
        for m in mass_functions:
            if m.frame is not None and m.frame.elements != frame.elements:
                raise ValueError("Frames of discernment must be compatible")
    
    # Get all focal elements from all mass functions
    focal_elements = set()
    for m in mass_functions:
        focal_elements.update(m.keys())
    
    # Initialize result
    result = {}
    
    # Calculate conjunctive combination for non-empty intersections
    for focal_element in focal_elements:
        result[focal_element] = 0.0
    
    # Calculate the conjunctive combination
    def calculate_conjunctive_combination(focal_elements, mass_functions, index=0, current_intersection=None, current_product=1.0):
        if current_intersection is None:
            current_intersection = frozenset().union(*focal_elements[0])
        
        if index == len(mass_functions):
            # We've selected one focal element from each mass function
            if current_intersection:
                # Non-empty intersection
                if current_intersection in result:
                    result[current_intersection] += current_product
                else:
                    result[current_intersection] = current_product
            return
        
        # Select each focal element from the current mass function
        for focal_element, mass in mass_functions[index].items():
            new_intersection = current_intersection.intersection(focal_element)
            calculate_conjunctive_combination(
                focal_elements, 
                mass_functions, 
                index + 1, 
                new_intersection, 
                current_product * mass
            )
    
    # Calculate the conjunctive combination
    calculate_conjunctive_combination([list(m.keys()) for m in mass_functions], mass_functions)
    
    # Remove empty set if present
    empty_set = frozenset()
    if empty_set in result:
        del result[empty_set]
    
    # Create mass function from result
    return MassFunction(result, frame=frame)
