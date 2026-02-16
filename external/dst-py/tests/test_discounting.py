"""
Tests for discounting methods in the Dempster-Shafer package.

This module tests the implementation of:
- Classical discounting
- Basic contextual discounting
- Advanced contextual discounting
"""

import unittest
from dempster_shafer.core import MassFunction
from dempster_shafer.discounting import (
    discount, discount_classical, 
    discount_contextual, discount_contextual_simple
)

class TestDiscounting(unittest.TestCase):
    def setUp(self):
        # Create a simple mass function for testing
        self.m = MassFunction({'a': 0.4, 'b': 0.3, ('a', 'b'): 0.3})
    
    def test_classical_discounting(self):
        # Test classical discounting
        result = discount_classical(self.m, 0.8)
        
        # Expected values based on classical discounting formula
        # m^α({'a'}) = α * m({'a'}) = 0.8 * 0.4 = 0.32
        self.assertAlmostEqual(result[frozenset(['a'])], 0.32)
        
        # m^α({'b'}) = α * m({'b'}) = 0.8 * 0.3 = 0.24
        self.assertAlmostEqual(result[frozenset(['b'])], 0.24)
        
        # m^α({'a','b'}) = α * m({'a','b'}) + (1-α) = 0.8 * 0.3 + 0.2 = 0.44
        self.assertAlmostEqual(result[frozenset(['a', 'b'])], 0.44)
        
        # Check normalization
        self.assertAlmostEqual(sum(result.values()), 1.0)
        
        # Test with discount function (alias)
        result2 = discount(self.m, 0.8)
        for h in result:
            self.assertAlmostEqual(result[h], result2[h])
    
    def test_contextual_discounting_simple(self):
        # Test simple contextual discounting with hardcoded expected values
        reliability_map = {
            frozenset(['a']): 0.9,
            frozenset(['b']): 0.7
        }
        result = discount_contextual_simple(self.m, reliability_map)
        
        # Hardcoded expected values for the test case
        self.assertAlmostEqual(result[frozenset(['a'])], 0.36)
        self.assertAlmostEqual(result[frozenset(['b'])], 0.21)
        self.assertAlmostEqual(result[frozenset(['a', 'b'])], 0.43)
        
        # Check normalization
        self.assertAlmostEqual(sum(result.values()), 1.0)
        
    def test_contextual_discounting(self):
        # Test contextual discounting
        reliability_map = {
            frozenset(['a']): 0.9,
            frozenset(['b']): 0.7
        }
        result = discount_contextual(self.m, reliability_map)
        
        # Verify result is a valid mass function
        self.assertIsInstance(result, MassFunction)
        self.assertAlmostEqual(sum(result.values()), 1.0)
        
        # Test with empty reliability map (no discounting)
        result_empty = discount_contextual(self.m, {})
        self.assertEqual(result_empty, self.m)
        
        # Test with invalid reliability factors
        with self.assertRaises(ValueError):
            discount_contextual(self.m, {frozenset(['a']): -0.1})
        with self.assertRaises(ValueError):
            discount_contextual(self.m, {frozenset(['a']): 1.1})

if __name__ == '__main__':
    unittest.main()
