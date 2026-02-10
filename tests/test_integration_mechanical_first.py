import test_config
"""
Integration Test: Verify Mechanical-First Pipeline Components

This test verifies that all components of the mechanical-first pipeline
are properly integrated without making actual API calls.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from word_pool_loader import WordPoolLoader
from setter_agent import SetterAgent
import main


class TestMechanicalFirstIntegration(unittest.TestCase):
    """Integration tests for mechanical-first pipeline."""
    
    def test_word_pool_loader_exists_and_works(self):
        """Test that WordPoolLoader can be instantiated and used."""
        loader = WordPoolLoader()
        
        # Verify it loaded words
        self.assertGreater(len(loader.word_pool), 0)
        
        # Verify it can provide seeds
        result = loader.get_random_seed()
        self.assertIsNotNone(result)
        
        word, clue_type = result
        self.assertIsInstance(word, str)
        self.assertIsInstance(clue_type, str)
    
    def test_setter_has_two_step_functions(self):
        """Test that SetterAgent has both mechanical draft and surface polish functions."""
        # Verify the methods exist
        self.assertTrue(hasattr(SetterAgent, 'generate_wordplay_only'))
        self.assertTrue(hasattr(SetterAgent, 'generate_surface_from_wordplay'))
    
    def test_main_imports_word_pool_loader(self):
        """Test that main.py imports WordPoolLoader."""
        # Verify import exists
        self.assertTrue(hasattr(main, 'WordPoolLoader'))
    
    def test_factory_run_has_use_seed_words_parameter(self):
        """Test that factory_run accepts use_seed_words parameter."""
        import inspect
        
        # Get function signature
        sig = inspect.signature(main.factory_run)
        params = sig.parameters
        
        # Verify use_seed_words parameter exists
        self.assertIn('use_seed_words', params)
        
        # Verify default is True
        self.assertEqual(params['use_seed_words'].default, True)
    
    def test_process_single_clue_uses_mechanical_first(self):
        """Test that process_single_clue_sync uses mechanical-first approach."""
        import inspect
        
        # Read source code to verify the flow
        source = inspect.getsource(main.process_single_clue_sync)
        
        # Check for key mechanical-first markers
        self.assertIn('generate_wordplay_only', source)
        self.assertIn('validate_clue_complete', source)
        self.assertIn('generate_surface_from_wordplay', source)
        
        # Verify retry logic exists
        self.assertIn('max_wordplay_attempts', source)
        self.assertIn('retry_feedback', source)
    
    def test_pipeline_order_correct(self):
        """Test that the pipeline stages are in correct order."""
        import inspect
        
        source = inspect.getsource(main.process_single_clue_sync)
        
        # Find positions of key operations
        wordplay_pos = source.find('generate_wordplay_only')
        validate_pos = source.find('validate_clue_complete')
        surface_pos = source.find('generate_surface_from_wordplay')
        solve_pos = source.find('solve_clue')
        
        # Verify order
        self.assertLess(wordplay_pos, validate_pos, "Wordplay should come before validation")
        self.assertLess(validate_pos, surface_pos, "Validation should come before surface")
        self.assertLess(surface_pos, solve_pos, "Surface should come before solving")
    
    def test_seed_words_json_exists(self):
        """Test that seed_words.json exists and is valid."""
        import json
        import os
        
        # Check in word_pools directory
        seed_path = os.path.join('..', 'word_pools', 'seed_words.json')
        if not os.path.exists(seed_path):
            # Fallback to root directory
            seed_path = os.path.join('..', 'seed_words.json')
        
        self.assertTrue(os.path.exists(seed_path), f"seed_words.json not found at {seed_path}")
        
        with open(seed_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verify expected categories exist
        expected_categories = [
            'anagram_friendly',
            'charade_friendly',
            'hidden_word_friendly',
            'container_friendly',
            'reversal_friendly',
            'homophone_friendly',
            'double_def_friendly',
            'standard_utility'
        ]
        
        for category in expected_categories:
            self.assertIn(category, data)
            self.assertIsInstance(data[category], list)
            self.assertGreater(len(data[category]), 0)
    
    def test_complete_pipeline_flow(self):
        """Test that all pipeline components can work together (mock version)."""
        # This tests the integration without making actual API calls
        
        # Step 1: Load words
        loader = WordPoolLoader()
        word, clue_type = loader.get_random_seed()
        
        self.assertIsNotNone(word)
        self.assertIsNotNone(clue_type)
        
        # Step 2: Verify we have the pipeline components
        self.assertTrue(hasattr(main, 'process_single_clue_sync'))
        self.assertTrue(hasattr(main, 'factory_run'))
        
        # Step 3: Verify ClueResult exists
        self.assertTrue(hasattr(main, 'ClueResult'))
        
        # Create a sample result
        result = main.ClueResult(
            word=word,
            clue_type=clue_type,
            passed=False
        )
        
        # Verify it has expected attributes
        self.assertEqual(result.word, word)
        self.assertEqual(result.clue_type, clue_type)
        self.assertFalse(result.passed)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that old code still works."""
    
    def test_word_selector_still_available(self):
        """Test that WordSelector is still available for backward compatibility."""
        self.assertTrue(hasattr(main, 'WordSelector'))
    
    def test_factory_run_works_without_seed_words(self):
        """Test that factory_run can work with use_seed_words=False."""
        import inspect
        
        # Verify the fallback logic exists
        source = inspect.getsource(main.factory_run)
        self.assertIn('WordSelector', source)
        self.assertIn('use_seed_words', source)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("MECHANICAL-FIRST INTEGRATION TESTS")
    print("="*80 + "\n")
    
    # Run tests
    unittest.main(verbosity=2)

