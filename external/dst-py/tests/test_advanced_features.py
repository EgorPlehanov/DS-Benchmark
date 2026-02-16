"""
Tests for advanced features of the Dempster-Shafer package.

This module tests the implementation of:
- Advanced contextual discounting methods from "Contextual Discounting of Belief Functions" (ECSQARU 2005)
- Cautious conjunctive rule and bold disjunctive rule from "Conjunctive and Disjunctive Combination 
  of Belief Functions Induced by Non-Distinct Bodies of Evidence"
"""

import unittest
import numpy as np
from dempster_shafer.core.mass_function import MassFunction
from dempster_shafer.discounting.contextual_advanced import (
    contextual_discount,
    theta_contextual_discount,
    compute_generalization_matrix
)
from dempster_shafer.combination.advanced_rules import (
    cautious_conjunctive_rule,
    bold_disjunctive_rule,
    canonical_conjunctive_decomposition,
    weight_function
)

class TestContextualDiscounting(unittest.TestCase):
    """Test cases for contextual discounting methods."""
    
    def setUp(self):
        """Set up test cases."""
        # Create a simple frame of discernment
        self.frame = frozenset(['a', 'b', 'c'])
        
        # Create a simple mass function
        self.m = MassFunction({
            ('a',): 0.2,
            ('b',): 0.3,
            ('a', 'b'): 0.1,
            ('a', 'b', 'c'): 0.4
        }, self.frame)
            
    def test_contextual_discount(self):
        """Test contextual discounting."""
        # Define discount rates for each element
        alphas = {'a': 0.2, 'b': 0.3, 'c': 0.4}
        
        # Apply contextual discounting
        m_ctx = contextual_discount(self.m, alphas)
        
        # Verify the result is a valid mass function
        self.assertIsInstance(m_ctx, MassFunction)
        self.assertAlmostEqual(sum(m_ctx.values()), 1.0)
        
        # Test with empty alphas (no discounting)
        m_ctx_empty = contextual_discount(self.m, {})
        self.assertEqual(m_ctx_empty, self.m)
        
        # Test with all alphas = 0 (no discounting)
        m_ctx_zeros = contextual_discount(self.m, {'a': 0, 'b': 0, 'c': 0})
        self.assertEqual(m_ctx_zeros, self.m)
        
        # Test with all alphas = 1 (complete discounting)
        m_ctx_ones = contextual_discount(self.m, {'a': 1, 'b': 1, 'c': 1})
        self.assertEqual(m_ctx_ones, MassFunction({('a', 'b', 'c'): 1.0}, self.frame))
        
        # Test with invalid alphas
        with self.assertRaises(ValueError):
            contextual_discount(self.m, {'a': -0.1})
        with self.assertRaises(ValueError):
            contextual_discount(self.m, {'a': 1.1})
        with self.assertRaises(ValueError):
            contextual_discount(self.m, {'d': 0.5})  # 'd' not in frame
            
    def test_theta_contextual_discount(self):
        """Test Θ-contextual discounting."""
        # Define a partition of the frame
        theta_partition = [('a',), ('b', 'c')]
        
        # Define discount rates for each subset in the partition
        alphas = {('a',): 0.2, ('b', 'c'): 0.3}
        
        # Apply Θ-contextual discounting
        m_theta = theta_contextual_discount(self.m, theta_partition, alphas)
        
        # Verify the result is a valid mass function
        self.assertIsInstance(m_theta, MassFunction)
        self.assertAlmostEqual(sum(m_theta.values()), 1.0)
        
        # Test with empty alphas (no discounting)
        m_theta_empty = theta_contextual_discount(self.m, theta_partition, {})
        self.assertEqual(m_theta_empty, self.m)
        
        # Test with all alphas = 0 (no discounting)
        m_theta_zeros = theta_contextual_discount(self.m, theta_partition, {('a',): 0, ('b', 'c'): 0})
        self.assertEqual(m_theta_zeros, self.m)
        
        # Test with all alphas = 1 (complete discounting)
        m_theta_ones = theta_contextual_discount(self.m, theta_partition, {('a',): 1, ('b', 'c'): 1})
        self.assertEqual(m_theta_ones, MassFunction({('a', 'b', 'c'): 1.0}, self.frame))
        
        # Test with invalid partition
        with self.assertRaises(ValueError):
            theta_contextual_discount(self.m, [('a',), ('b',)], {('a',): 0.2, ('b',): 0.3})  # Missing 'c'
        with self.assertRaises(ValueError):
            theta_contextual_discount(self.m, [('a',), ('a', 'b')], {('a',): 0.2, ('a', 'b'): 0.3})  # Overlapping
            
        # Test with invalid alphas
        with self.assertRaises(ValueError):
            theta_contextual_discount(self.m, theta_partition, {('a',): -0.1})
        with self.assertRaises(ValueError):
            theta_contextual_discount(self.m, theta_partition, {('a',): 1.1})
        with self.assertRaises(ValueError):
            theta_contextual_discount(self.m, theta_partition, {('d',): 0.5})  # ('d',) not in partition
            
    def test_compute_generalization_matrix(self):
        """Test computation of generalization matrix."""
        # Define discount rates for each element
        alphas = {'a': 0.2, 'b': 0.3, 'c': 0.4}
        
        # Compute generalization matrix
        G = compute_generalization_matrix(self.frame, alphas)
        
        # Verify some properties of the generalization matrix
        self.assertIsInstance(G, dict)
        
        # Check a few specific values
        A = ('a', 'b', 'c')
        B = ('a', 'b')
        
        # G(A,B) should be the product of alphas for elements in A-B and (1-alphas) for elements in B
        self.assertAlmostEqual(G.get((A, B), 0), 0.4 * 0.7 * 0.4)  # 0.4 for 'c', 0.7 and 0.8 for 'a' and 'b'


class TestAdvancedCombinationRules(unittest.TestCase):
    """Test cases for advanced combination rules."""
    
    def setUp(self):
        """Set up test cases."""
        # Create a simple frame of discernment
        self.frame = frozenset(['a', 'b', 'c'])
        
        # Create two simple mass functions
        self.m1 = MassFunction({
            ('a',): 0.2,
            ('b',): 0.3,
            ('a', 'b'): 0.1,
            ('a', 'b', 'c'): 0.4
        }, self.frame)
        
        self.m2 = MassFunction({
            ('a',): 0.1,
            ('c',): 0.2,
            ('a', 'c'): 0.3,
            ('a', 'b', 'c'): 0.4
        }, self.frame)
        
    def test_canonical_conjunctive_decomposition(self):
        """Test canonical conjunctive decomposition."""
        # Compute canonical decomposition
        weights = canonical_conjunctive_decomposition(self.m1)
        
        # Verify the result is a dictionary
        self.assertIsInstance(weights, dict)
        
        # Verify weights are in [0,1]
        for w in weights.values():
            self.assertGreaterEqual(w, 0)
            self.assertLessEqual(w, 1)
            
    def test_cautious_conjunctive_rule(self):
        """Test cautious conjunctive rule."""
        # Apply cautious conjunctive rule
        m_cautious = cautious_conjunctive_rule(self.m1, self.m2)
        
        # Verify the result is a valid mass function
        self.assertIsInstance(m_cautious, MassFunction)
        self.assertAlmostEqual(sum(m_cautious.values()), 1.0)
        
        # Test idempotence property: m ∧ m = m
        m_idempotent = cautious_conjunctive_rule(self.m1, self.m1)
        
        # The result should be approximately equal to m1
        for focal_set in self.m1:
            self.assertAlmostEqual(m_idempotent[focal_set], self.m1[focal_set], places=5)
            
        # Test with incompatible frames
        m3 = MassFunction({('d',): 1.0}, frozenset(['d']))
        with self.assertRaises(ValueError):
            cautious_conjunctive_rule(self.m1, m3)
            
    def test_bold_disjunctive_rule(self):
        """Test bold disjunctive rule."""
        # Apply bold disjunctive rule
        m_bold = bold_disjunctive_rule(self.m1, self.m2)
        
        # Verify the result is a valid mass function
        self.assertIsInstance(m_bold, MassFunction)
        self.assertAlmostEqual(sum(m_bold.values()), 1.0)
        
        # Test idempotence property: m ∨ m = m
        m_idempotent = bold_disjunctive_rule(self.m1, self.m1)
        
        # The result should be approximately equal to m1
        for focal_set in self.m1:
            self.assertAlmostEqual(m_idempotent[focal_set], self.m1[focal_set], places=5)
            
        # Test with incompatible frames
        m3 = MassFunction({('d',): 1.0}, frozenset(['d']))
        with self.assertRaises(ValueError):
            bold_disjunctive_rule(self.m1, m3)
            
    def test_weight_function(self):
        """Test weight function calculation."""
        # Compute weight function
        weights = weight_function(self.m1)
        
        # Verify the result is a dictionary
        self.assertIsInstance(weights, dict)
        
        # Verify weights are in [0,1]
        for w in weights.values():
            self.assertGreaterEqual(w, 0)
            self.assertLessEqual(w, 1)


if __name__ == '__main__':
    unittest.main()
