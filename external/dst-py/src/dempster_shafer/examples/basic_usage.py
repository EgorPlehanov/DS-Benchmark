"""
Basic usage examples for the Dempster-Shafer package.

This module provides examples of basic operations with mass functions.
"""

from ..core import MassFunction, Frame

def basic_mass_function_example():
    """
    Example of creating and manipulating mass functions.
    
    Returns:
    --------
    dict
        Dictionary containing example mass functions and results.
    """
    # Create a frame of discernment
    frame = Frame(['a', 'b', 'c'])
    
    # Create a mass function
    m1 = MassFunction({
        ('a',): 0.2,
        ('b',): 0.3,
        ('a', 'b'): 0.1,
        ('a', 'b', 'c'): 0.4
    }, frame)
    
    # Calculate belief and plausibility
    belief_a = m1.belief(('a',))
    plausibility_a = m1.plausibility(('a',))
    
    # Create another mass function
    m2 = MassFunction({
        ('a',): 0.1,
        ('c',): 0.2,
        ('a', 'c'): 0.3,
        ('a', 'b', 'c'): 0.4
    }, frame)
    
    # Combine using Dempster's rule
    m_combined = m1.combine_conjunctive(m2, normalization=True)
    
    # Return results
    return {
        'm1': m1,
        'm2': m2,
        'belief_a': belief_a,
        'plausibility_a': plausibility_a,
        'm_combined': m_combined
    }

def combination_rules_example():
    """
    Example of using different combination rules.
    
    Returns:
    --------
    dict
        Dictionary containing example mass functions and combination results.
    """
    from ..combination import (
        combine_conjunctive, combine_disjunctive,
        combine_yager, combine_dubois_prade,
        combine_pcr5
    )
    
    # Create a frame of discernment
    frame = Frame(['a', 'b', 'c'])
    
    # Create two mass functions with conflict
    m1 = MassFunction({
        ('a',): 0.8,
        ('b',): 0.2
    }, frame)
    
    m2 = MassFunction({
        ('a',): 0.1,
        ('b',): 0.9
    }, frame)
    
    # Combine using different rules
    m_dempster = combine_conjunctive(m1, m2, normalization=True)
    m_conjunctive = combine_conjunctive(m1, m2, normalization=False)
    m_disjunctive = combine_disjunctive(m1, m2)
    m_yager = combine_yager(m1, m2)
    m_dubois_prade = combine_dubois_prade(m1, m2)
    m_pcr5 = combine_pcr5(m1, m2)
    
    # Return results
    return {
        'm1': m1,
        'm2': m2,
        'm_dempster': m_dempster,
        'm_conjunctive': m_conjunctive,
        'm_disjunctive': m_disjunctive,
        'm_yager': m_yager,
        'm_dubois_prade': m_dubois_prade,
        'm_pcr5': m_pcr5
    }

def discounting_example():
    """
    Example of using different discounting methods.
    
    Returns:
    --------
    dict
        Dictionary containing example mass functions and discounting results.
    """
    from ..discounting import (
        discount_classical,
        discount_contextual_simple
    )
    
    # Create a frame of discernment
    frame = Frame(['a', 'b', 'c'])
    
    # Create a mass function
    m = MassFunction({
        ('a',): 0.2,
        ('b',): 0.3,
        ('a', 'b'): 0.1,
        ('a', 'b', 'c'): 0.4
    }, frame)
    
    # Apply classical discounting
    m_classical = discount_classical(m, 0.8)
    
    # Apply contextual discounting
    reliability_map = {
        frozenset(['a']): 0.9,
        frozenset(['b']): 0.7,
        frozenset(['c']): 0.8
    }
    m_contextual = discount_contextual_simple(m, reliability_map)
    
    # Return results
    return {
        'm': m,
        'm_classical': m_classical,
        'm_contextual': m_contextual
    }

def run_all_examples():
    """
    Run all examples and print results.
    """
    # Run basic mass function example
    print("Basic Mass Function Example:")
    results = basic_mass_function_example()
    for key, value in results.items():
        print(f"{key}: {value}")
    print()
    
    # Run combination rules example
    print("Combination Rules Example:")
    results = combination_rules_example()
    for key, value in results.items():
        print(f"{key}: {value}")
    print()
    
    # Run discounting example
    print("Discounting Example:")
    results = discounting_example()
    for key, value in results.items():
        print(f"{key}: {value}")
    print()

if __name__ == "__main__":
    run_all_examples()
