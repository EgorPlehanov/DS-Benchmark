"""
Visualization examples for the Dempster-Shafer package.

This module provides examples of visualizing mass functions, belief, and plausibility.
"""

from ..core import MassFunction, Frame
from ..visualization import plot_mass_function, plot_belief_plausibility, plot_comparison
from ..combination import combine_conjunctive, combine_dubois_prade, combine_pcr5

def mass_function_visualization_example():
    """
    Example of visualizing a mass function.
    
    Returns:
    --------
    dict
        Dictionary containing example mass function and plot.
    """
    # Create a frame of discernment
    frame = Frame(['a', 'b', 'c'])
    
    # Create a mass function
    m = MassFunction({
        ('a',): 0.2,
        ('b',): 0.3,
        ('a', 'b'): 0.1,
        ('a', 'c'): 0.1,
        ('a', 'b', 'c'): 0.3
    }, frame)
    
    # Plot the mass function
    fig = plot_mass_function(m, title="Example Mass Function")
    
    # Return results
    return {
        'mass_function': m,
        'figure': fig
    }

def belief_plausibility_visualization_example():
    """
    Example of visualizing belief and plausibility.
    
    Returns:
    --------
    dict
        Dictionary containing example mass function and plot.
    """
    # Create a frame of discernment
    frame = Frame(['a', 'b', 'c'])
    
    # Create a mass function
    m = MassFunction({
        ('a',): 0.2,
        ('b',): 0.3,
        ('a', 'b'): 0.1,
        ('a', 'c'): 0.1,
        ('a', 'b', 'c'): 0.3
    }, frame)
    
    # Define hypotheses to visualize
    hypotheses = [
        frozenset(['a']),
        frozenset(['b']),
        frozenset(['c']),
        frozenset(['a', 'b']),
        frozenset(['a', 'c']),
        frozenset(['b', 'c']),
        frozenset(['a', 'b', 'c'])
    ]
    
    # Plot belief and plausibility
    fig = plot_belief_plausibility(m, hypotheses, title="Belief and Plausibility")
    
    # Return results
    return {
        'mass_function': m,
        'figure': fig
    }

def combination_rules_visualization_example():
    """
    Example of visualizing different combination rules.
    
    Returns:
    --------
    dict
        Dictionary containing example mass functions and plot.
    """
    # Create a frame of discernment
    frame = Frame(['a', 'b'])
    
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
    m_dubois_prade = combine_dubois_prade(m1, m2)
    m_pcr5 = combine_pcr5(m1, m2)
    
    # Plot comparison
    fig = plot_comparison(
        [m1, m2, m_dempster, m_dubois_prade, m_pcr5],
        labels=["m1", "m2", "Dempster", "Dubois & Prade", "PCR5"],
        title="Comparison of Combination Rules"
    )
    
    # Return results
    return {
        'm1': m1,
        'm2': m2,
        'm_dempster': m_dempster,
        'm_dubois_prade': m_dubois_prade,
        'm_pcr5': m_pcr5,
        'figure': fig
    }

def run_all_examples():
    """
    Run all examples and display plots.
    """
    import matplotlib.pyplot as plt
    
    # Run mass function visualization example
    print("Mass Function Visualization Example:")
    results = mass_function_visualization_example()
    plt.figure(results['figure'].number)
    plt.show()
    
    # Run belief plausibility visualization example
    print("\nBelief and Plausibility Visualization Example:")
    results = belief_plausibility_visualization_example()
    plt.figure(results['figure'].number)
    plt.show()
    
    # Run combination rules visualization example
    print("\nCombination Rules Visualization Example:")
    results = combination_rules_visualization_example()
    plt.figure(results['figure'].number)
    plt.show()

if __name__ == "__main__":
    run_all_examples()
