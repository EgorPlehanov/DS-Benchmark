"""
Frame of discernment module for Dempster-Shafer theory.

This module provides the Frame class for representing frames of discernment
in the Dempster-Shafer theory.
"""

from itertools import chain, combinations

class Frame:
    """
    A frame of discernment for Dempster-Shafer theory.
    
    In Dempster-Shafer theory, a frame of discernment is a set of mutually exclusive
    and exhaustive possibilities.
    
    Parameters:
    -----------
    elements : iterable
        The elements of the frame of discernment.
    
    Attributes:
    -----------
    elements : frozenset
        The elements of the frame of discernment.
    """
    
    def __init__(self, elements):
        """
        Initialize a frame of discernment.
        
        Parameters:
        -----------
        elements : iterable
            The elements of the frame of discernment.
        """
        self.elements = frozenset(elements)
    
    def __len__(self):
        """
        Return the number of elements in the frame.
        
        Returns:
        --------
        int
            The number of elements in the frame.
        """
        return len(self.elements)
    
    def __contains__(self, element):
        """
        Check if an element is in the frame.
        
        Parameters:
        -----------
        element : object
            The element to check.
            
        Returns:
        --------
        bool
            True if the element is in the frame, False otherwise.
        """
        return element in self.elements
    
    def __iter__(self):
        """
        Return an iterator over the elements of the frame.
        
        Returns:
        --------
        iterator
            An iterator over the elements of the frame.
        """
        return iter(self.elements)
    
    def __eq__(self, other):
        """
        Check if two frames are equal.
        
        Parameters:
        -----------
        other : Frame
            The other frame to compare with.
            
        Returns:
        --------
        bool
            True if the frames are equal, False otherwise.
        """
        if not isinstance(other, Frame):
            return False
        return self.elements == other.elements
    
    def __hash__(self):
        """
        Return the hash of the frame.
        
        Returns:
        --------
        int
            The hash of the frame.
        """
        return hash(self.elements)
    
    def __repr__(self):
        """
        Return a string representation of the frame.
        
        Returns:
        --------
        str
            A string representation of the frame.
        """
        return f"Frame({list(self.elements)})"
    
    def powerset(self):
        """
        Return the power set of the frame.
        
        The power set of a set S is the set of all subsets of S, including the
        empty set and S itself.
        
        Returns:
        --------
        iterator
            An iterator over all subsets of the frame.
        """
        return chain.from_iterable(combinations(self.elements, r) for r in range(len(self.elements) + 1))
