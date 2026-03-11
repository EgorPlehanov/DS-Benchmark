"""
Mass function module for Dempster-Shafer theory.

This module provides the MassFunction class for representing basic belief assignments
in the Dempster-Shafer theory.

References:
-----------
1. Shafer, G. (1976). A Mathematical Theory of Evidence. Princeton University Press.
2. Smets, P. (1990). The Combination of Evidence in the Transferable Belief Model. 
   IEEE Transactions on Pattern Analysis and Machine Intelligence, 12(5), 447-458.
"""

from itertools import chain, combinations
import math
from .frame import Frame
from .utils import powerset, normalize_masses, calculate_conflict

def _convert_to_frozenset(item):
    """Convert an item to a frozenset if it's not already one."""
    if isinstance(item, frozenset):
        return item
    elif isinstance(item, (list, tuple, set)):
        return frozenset(item)
    else:
        return frozenset([item])

class MassFunction(dict):
    """
    A mass function (basic belief assignment) in Dempster-Shafer theory.
    
    A mass function assigns belief mass to subsets of the frame of discernment.
    
    Parameters:
    -----------
    masses : dict, optional
        Dictionary mapping focal sets to mass values.
    frame : Frame, optional
        The frame of discernment.
    
    Attributes:
    -----------
    frame : Frame
        The frame of discernment.
    """
    
    def __init__(self, masses=None, frame=None):
        """
        Initialize a mass function.
        
        Parameters:
        -----------
        masses : dict, optional
            Dictionary mapping focal sets to mass values.
        frame : Frame, optional
            The frame of discernment.
        """
        # Initialize as empty dictionary
        super().__init__()
        
        # Set frame of discernment
        if frame is not None:
            if isinstance(frame, Frame):
                self.frame = frame
            else:
                self.frame = Frame(frame)
        else:
            self.frame = None
        
        # Add masses
        if masses:
            # Convert all keys to frozensets
            for h, v in masses.items():
                if v > 0:  # Only add positive masses
                    self[_convert_to_frozenset(h)] = float(v)
            
            # Infer frame if not provided
            if self.frame is None:
                elements = set()
                for h in self:
                    elements.update(h)
                self.frame = Frame(elements)
            
            # Normalize if necessary
            if not self.is_normalized():
                self.normalize()
    
    def __missing__(self, key):
        """
        Return 0 for missing keys.
        
        Parameters:
        -----------
        key : frozenset
            The key to look up.
            
        Returns:
        --------
        float
            0.0 if the key is not in the dictionary.
        """
        return 0.0
    
    def focal_elements(self):
        """
        Return the focal elements of the mass function.
        
        Focal elements are subsets of the frame with non-zero mass.
        
        Returns:
        --------
        list
            List of focal elements.
        """
        return list(self.keys())
    
    def is_normalized(self):
        """
        Check if the mass function is normalized.
        
        A mass function is normalized if the sum of all masses is 1.
        
        Returns:
        --------
        bool
            True if the mass function is normalized, False otherwise.
        """
        return abs(sum(self.values()) - 1.0) < 1e-10
    
    def normalize(self):
        """
        Normalize the mass function.
        
        Returns:
        --------
        MassFunction
            The normalized mass function.
        """
        # Remove empty set if present
        empty_set = frozenset()
        if empty_set in self:
            del self[empty_set]
        
        # Normalize remaining masses
        total = sum(self.values())
        if total == 0:
            return self
        
        for h in list(self.keys()):
            self[h] /= total
        
        return self
    
    def belief(self, hypothesis):
        """
        Calculate the belief in a hypothesis.
        
        The belief in a hypothesis is the sum of the masses of all subsets of the hypothesis.
        
        Parameters:
        -----------
        hypothesis : set or frozenset
            The hypothesis to calculate belief for.
            
        Returns:
        --------
        float
            The belief in the hypothesis.
        """
        hypothesis = _convert_to_frozenset(hypothesis)
        return sum(m for h, m in self.items() if h.issubset(hypothesis))
    
    def plausibility(self, hypothesis):
        """
        Calculate the plausibility of a hypothesis.
        
        The plausibility of a hypothesis is the sum of the masses of all sets
        that have non-empty intersection with the hypothesis.
        
        Parameters:
        -----------
        hypothesis : set or frozenset
            The hypothesis to calculate plausibility for.
            
        Returns:
        --------
        float
            The plausibility of the hypothesis.
        """
        hypothesis = _convert_to_frozenset(hypothesis)
        return sum(m for h, m in self.items() if h.intersection(hypothesis))
    
    def commonality(self, hypothesis):
        """
        Calculate the commonality of a hypothesis.
        
        The commonality of a hypothesis is the sum of the masses of all supersets
        of the hypothesis.
        
        Parameters:
        -----------
        hypothesis : set or frozenset
            The hypothesis to calculate commonality for.
            
        Returns:
        --------
        float
            The commonality of the hypothesis.
        """
        hypothesis = _convert_to_frozenset(hypothesis)
        return sum(m for h, m in self.items() if hypothesis.issubset(h))
    
    def combine_conjunctive(self, other, normalization=True):
        """
        Combine with another mass function using Dempster's rule of combination.
        
        Dempster's rule of combination is a normalized conjunctive combination rule.
        
        Parameters:
        -----------
        other : MassFunction
            The other mass function to combine with.
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
        from ..combination import combine_conjunctive
        return combine_conjunctive(self, other, normalization=normalization)
    
    def combine_disjunctive(self, other):
        """
        Combine with another mass function using the disjunctive rule of combination.
        
        The disjunctive rule of combination is useful when one of the sources is reliable
        but we don't know which one.
        
        Parameters:
        -----------
        other : MassFunction
            The other mass function to combine with.
            
        Returns:
        --------
        MassFunction
            The combined mass function.
            
        References:
        -----------
        Dubois, D., & Prade, H. (1988). Representation and Combination of Uncertainty 
        with Belief Functions and Possibility Measures. Computational Intelligence, 4(3), 244-264.
        """
        from ..combination import combine_disjunctive
        return combine_disjunctive(self, other)
    
    def combine_yager(self, other):
        """
        Combine with another mass function using Yager's rule of combination.
        
        Yager's rule assigns conflicting mass to the universal set instead of normalizing.
        
        Parameters:
        -----------
        other : MassFunction
            The other mass function to combine with.
            
        Returns:
        --------
        MassFunction
            The combined mass function.
            
        References:
        -----------
        Yager, R. R. (1987). On the Dempster-Shafer Framework and New Combination Rules. 
        Information Sciences, 41(2), 93-137.
        """
        from ..combination import combine_yager
        return combine_yager(self, other)
    
    def combine_dubois_prade(self, other):
        """
        Combine with another mass function using Dubois & Prade's rule of combination.
        
        Dubois & Prade's rule assigns conflicting mass to the union of the focal elements.
        
        Parameters:
        -----------
        other : MassFunction
            The other mass function to combine with.
            
        Returns:
        --------
        MassFunction
            The combined mass function.
            
        References:
        -----------
        Dubois, D., & Prade, H. (1988). Representation and Combination of Uncertainty 
        with Belief Functions and Possibility Measures. Computational Intelligence, 4(3), 244-264.
        """
        from ..combination import combine_dubois_prade
        return combine_dubois_prade(self, other)
    
    def combine_pcr5(self, other):
        """
        Combine with another mass function using PCR5 rule of combination.
        
        PCR5 redistributes the conflicting mass proportionally to the masses of the elements
        involved in the conflict.
        
        Parameters:
        -----------
        other : MassFunction
            The other mass function to combine with.
            
        Returns:
        --------
        MassFunction
            The combined mass function.
            
        References:
        -----------
        Smarandache, F., & Dezert, J. (2005). Information Fusion Based on New Proportional 
        Conflict Redistribution Rules. Information Fusion, 8(3), 387-393.
        """
        from ..combination import combine_pcr5
        return combine_pcr5(self, other)
    
    def combine_cautious(self, other):
        """
        Combine with another mass function using the cautious conjunctive rule.
        
        The cautious rule is designed for combining belief functions induced by
        non-distinct bodies of evidence.
        
        Parameters:
        -----------
        other : MassFunction
            The other mass function to combine with.
            
        Returns:
        --------
        MassFunction
            The combined mass function.
            
        References:
        -----------
        Denœux, T. (2008). Conjunctive and Disjunctive Combination of Belief Functions 
        Induced by Non-Distinct Bodies of Evidence. Artificial Intelligence, 172(2-3), 234-264.
        """
        from ..combination.advanced_rules import cautious_conjunctive_rule
        return cautious_conjunctive_rule(self, other)
    
    def discount(self, reliability):
        """
        Apply classical discounting to the mass function.
        
        Classical discounting reduces the influence of a source based on its reliability.
        
        Parameters:
        -----------
        reliability : float
            The reliability factor in [0,1].
            
        Returns:
        --------
        MassFunction
            The discounted mass function.
            
        References:
        -----------
        Shafer, G. (1976). A Mathematical Theory of Evidence. Princeton University Press.
        """
        from ..discounting import discount
        return discount(self, reliability)
    
    def contextual_discount(self, reliability_map):
        """
        Apply contextual discounting to the mass function.
        
        Contextual discounting takes into account the reliability of a source
        in specific contexts or for specific hypotheses.
        
        Parameters:
        -----------
        reliability_map : dict
            Dictionary mapping contexts (subsets of the frame) to reliability factors.
            
        Returns:
        --------
        MassFunction
            The contextually discounted mass function.
            
        References:
        -----------
        Mercier, D., Quost, B., & Denœux, T. (2005). Contextual Discounting of Belief Functions. 
        ECSQARU 2005, LNAI 3571, pp. 552-562.
        """
        from ..discounting import discount_contextual
        return discount_contextual(self, reliability_map)
    
    def copy(self):
        """
        Create a copy of the mass function.
        
        Returns:
        --------
        MassFunction
            A copy of the mass function.
        """
        return MassFunction(self, frame=self.frame)
    
    def __str__(self):
        """
        Return a string representation of the mass function.
        
        Returns:
        --------
        str
            A string representation of the mass function.
        """
        return "{" + ", ".join(f"{set(h)}: {m:.4f}" for h, m in sorted(self.items(), key=lambda x: (len(x[0]), x[0]))) + "}"
    
    def __repr__(self):
        """
        Return a string representation of the mass function.
        
        Returns:
        --------
        str
            A string representation of the mass function.
        """
        return f"MassFunction({str(self)})"
