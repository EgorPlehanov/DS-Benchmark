"""
Visualization module for Dempster-Shafer theory.

This module provides visualization tools for mass functions, belief, and plausibility.

References:
-----------
1. Shafer, G. (1976). A Mathematical Theory of Evidence. Princeton University Press.
2. Smets, P. (1990). The Combination of Evidence in the Transferable Belief Model. 
   IEEE Transactions on Pattern Analysis and Machine Intelligence, 12(5), 447-458.
"""

import matplotlib.pyplot as plt
import numpy as np
from ..core import MassFunction

def plot_mass_function(mass_function, title="Mass Function", figsize=(10, 6)):
    """
    Plot a mass function as a bar chart.
    
    Parameters:
    -----------
    mass_function : MassFunction
        The mass function to plot.
    title : str, optional
        The title of the plot. Default is "Mass Function".
    figsize : tuple, optional
        The size of the figure. Default is (10, 6).
        
    Returns:
    --------
    matplotlib.figure.Figure
        The figure object.
    """
    # Get focal elements and masses
    focal_elements = []
    masses = []
    
    for h, m in sorted(mass_function.items(), key=lambda x: (len(x[0]), str(x[0]))):
        if m > 0:
            focal_elements.append(str(set(h)))
            masses.append(m)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot bars
    bars = ax.bar(focal_elements, masses)
    
    # Add labels and title
    ax.set_xlabel('Focal Elements')
    ax.set_ylabel('Mass')
    ax.set_title(title)
    
    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.4f}',
                ha='center', va='bottom')
    
    # Adjust layout
    plt.tight_layout()
    
    return fig

def plot_belief_plausibility(mass_function, hypotheses=None, title="Belief and Plausibility", figsize=(12, 8)):
    """
    Plot belief and plausibility for selected hypotheses.
    
    Parameters:
    -----------
    mass_function : MassFunction
        The mass function to calculate belief and plausibility from.
    hypotheses : list, optional
        List of hypotheses to plot. If None, all singletons and the frame are used.
    title : str, optional
        The title of the plot. Default is "Belief and Plausibility".
    figsize : tuple, optional
        The size of the figure. Default is (12, 8).
        
    Returns:
    --------
    matplotlib.figure.Figure
        The figure object.
    """
    # If no hypotheses provided, use singletons and frame
    if hypotheses is None:
        if mass_function.frame is not None:
            hypotheses = [frozenset([x]) for x in mass_function.frame.elements]
            hypotheses.append(frozenset(mass_function.frame.elements))
        else:
            # Infer frame from mass function
            elements = set()
            for h in mass_function:
                elements.update(h)
            hypotheses = [frozenset([x]) for x in elements]
            hypotheses.append(frozenset(elements))
    
    # Calculate belief and plausibility for each hypothesis
    hypothesis_labels = []
    beliefs = []
    plausibilities = []
    
    for h in hypotheses:
        if isinstance(h, str):
            h = frozenset([h])
        elif not isinstance(h, frozenset):
            h = frozenset(h)
        
        hypothesis_labels.append(str(set(h)))
        beliefs.append(mass_function.belief(h))
        plausibilities.append(mass_function.plausibility(h))
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set up x-axis
    x = np.arange(len(hypothesis_labels))
    width = 0.35
    
    # Plot bars
    bars1 = ax.bar(x - width/2, beliefs, width, label='Belief')
    bars2 = ax.bar(x + width/2, plausibilities, width, label='Plausibility')
    
    # Add labels and title
    ax.set_xlabel('Hypotheses')
    ax.set_ylabel('Value')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(hypothesis_labels)
    ax.legend()
    
    # Add values on top of bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}',
                    ha='center', va='bottom')
    
    # Adjust layout
    plt.tight_layout()
    
    return fig

def plot_comparison(mass_functions, labels=None, title="Comparison of Mass Functions", figsize=(14, 8)):
    """
    Plot a comparison of multiple mass functions.
    
    Parameters:
    -----------
    mass_functions : list of MassFunction
        The mass functions to compare.
    labels : list of str, optional
        Labels for the mass functions. If None, default labels are used.
    title : str, optional
        The title of the plot. Default is "Comparison of Mass Functions".
    figsize : tuple, optional
        The size of the figure. Default is (14, 8).
        
    Returns:
    --------
    matplotlib.figure.Figure
        The figure object.
    """
    if not mass_functions:
        raise ValueError("No mass functions provided")
    
    # If no labels provided, use default labels
    if labels is None:
        labels = [f"Mass Function {i+1}" for i in range(len(mass_functions))]
    
    # Get all focal elements from all mass functions
    all_focal_elements = set()
    for m in mass_functions:
        all_focal_elements.update(m.keys())
    
    # Sort focal elements by size and then by string representation
    focal_elements = sorted(all_focal_elements, key=lambda x: (len(x), str(x)))
    focal_element_labels = [str(set(h)) for h in focal_elements]
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Set up x-axis
    x = np.arange(len(focal_element_labels))
    width = 0.8 / len(mass_functions)
    
    # Plot bars for each mass function
    for i, (m, label) in enumerate(zip(mass_functions, labels)):
        masses = [m[h] for h in focal_elements]
        offset = (i - len(mass_functions) / 2 + 0.5) * width
        bars = ax.bar(x + offset, masses, width, label=label)
    
    # Add labels and title
    ax.set_xlabel('Focal Elements')
    ax.set_ylabel('Mass')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(focal_element_labels, rotation=45, ha='right')
    ax.legend()
    
    # Adjust layout
    plt.tight_layout()
    
    return fig
