"""
Tests for core functionality of the Dempster-Shafer package.

This module tests the implementation of:
- Frame class
- MassFunction class
- Basic belief operations (belief, plausibility, commonality)
"""

import unittest
import math
from dempster_shafer.core import Frame, MassFunction

class TestCore(unittest.TestCase):
    def test_frame(self):
        # Test Frame creation
        frame = Frame(['a', 'b', 'c'])
        self.assertEqual(len(frame), 3)
        self.assertTrue('a' in frame)
        self.assertTrue('b' in frame)
        self.assertTrue('c' in frame)
        self.assertFalse('d' in frame)
        
        # Test powerset generation
        powerset = list(frame.powerset())
        self.assertEqual(len(powerset), 2**3)  # 2^n elements in powerset
        self.assertTrue(frozenset() in powerset)  # Empty set
        self.assertTrue(frozenset(['a', 'b', 'c']) in powerset)  # Full set
    
    def test_mass_function_creation(self):
        # Test MassFunction creation
        m = MassFunction({'a': 0.2, 'b': 0.3, ('a', 'b'): 0.5})
        self.assertEqual(m[frozenset(['a'])], 0.2)
        self.assertEqual(m[frozenset(['b'])], 0.3)
        self.assertEqual(m[frozenset(['a', 'b'])], 0.5)
        self.assertEqual(m[frozenset(['c'])], 0.0)  # Non-existent hypothesis
        
        # Test with Frame
        frame = Frame(['a', 'b', 'c'])
        m = MassFunction({'a': 0.2, 'b': 0.3, ('a', 'b'): 0.5}, frame=frame)
        self.assertEqual(m.frame.elements, frozenset(['a', 'b', 'c']))
    
    def test_mass_function_operations(self):
        # Test basic operations
        m = MassFunction({'a': 0.2, 'b': 0.3, ('a', 'b'): 0.5})
        
        # Test focal elements
        focal = m.focal_elements()
        self.assertEqual(len(focal), 3)
        self.assertTrue(frozenset(['a']) in focal)
        self.assertTrue(frozenset(['b']) in focal)
        self.assertTrue(frozenset(['a', 'b']) in focal)
        
        # Test normalization
        m_unnorm = MassFunction({(): 0.1, 'a': 0.2, 'b': 0.3, ('a', 'b'): 0.4})
        self.assertFalse(m_unnorm.is_normalized())
        m_norm = m_unnorm.normalize()
        self.assertTrue(m_norm.is_normalized())
        self.assertAlmostEqual(m_norm[frozenset(['a'])], 0.2 / 0.9)
        self.assertAlmostEqual(m_norm[frozenset(['b'])], 0.3 / 0.9)
        self.assertAlmostEqual(m_norm[frozenset(['a', 'b'])], 0.4 / 0.9)
    
    def test_belief_plausibility(self):
        # Test belief and plausibility calculations
        m = MassFunction({'a': 0.2, 'b': 0.3, ('a', 'b'): 0.5})
        
        # Test belief
        self.assertAlmostEqual(m.belief(frozenset(['a'])), 0.2)
        self.assertAlmostEqual(m.belief(frozenset(['b'])), 0.3)
        self.assertAlmostEqual(m.belief(frozenset(['a', 'b'])), 1.0)
        
        # Test plausibility
        self.assertAlmostEqual(m.plausibility(frozenset(['a'])), 0.7)  # 0.2 + 0.5
        self.assertAlmostEqual(m.plausibility(frozenset(['b'])), 0.8)  # 0.3 + 0.5
        self.assertAlmostEqual(m.plausibility(frozenset(['a', 'b'])), 1.0)
        
        # Test commonality
        self.assertAlmostEqual(m.commonality(frozenset(['a'])), 0.7)  # 0.2 + 0.5
        self.assertAlmostEqual(m.commonality(frozenset(['b'])), 0.8)  # 0.3 + 0.5
        self.assertAlmostEqual(m.commonality(frozenset(['a', 'b'])), 0.5)

if __name__ == '__main__':
    unittest.main()
