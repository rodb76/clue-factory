import test_config
"""
Unit tests for word_pool_loader.py
"""

import unittest
import json
import tempfile
import os
from word_pool_loader import WordPoolLoader, CATEGORY_TO_TYPE


class TestWordPoolLoader(unittest.TestCase):
    """Test cases for WordPoolLoader class."""
    
    def setUp(self):
        """Create a temporary seed_words.json for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_seed_file = os.path.join(self.temp_dir, "test_seed_words.json")
        
        # Create test seed data
        test_data = {
            "anagram_friendly": ["LISTEN", "SILENT", "ENLIST"],
            "charade_friendly": ["PARTRIDGE", "FARMING"],
            "hidden_word_friendly": ["THECA", "SCONE"],
            "container_friendly": ["PAINT", "VOICE"],
            "reversal_friendly": ["REGAL", "STOPS"],
            "homophone_friendly": ["BEAR", "PARE"],
            "double_def_friendly": ["BLIND", "POLISH"],
            "standard_utility": ["ELAPSED", "DRIVERS"]
        }
        
        with open(self.test_seed_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)
    
    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_seed_file):
            os.remove(self.test_seed_file)
        os.rmdir(self.temp_dir)
    
    def test_initialization(self):
        """Test that WordPoolLoader initializes correctly."""
        loader = WordPoolLoader(self.test_seed_file)
        
        self.assertIsNotNone(loader.word_pool)
        self.assertGreater(len(loader.word_pool), 0)
        self.assertEqual(len(loader.used_words), 0)
    
    def test_load_seed_words(self):
        """Test that seed words are loaded correctly."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Should have loaded all words
        # 3 + 2 + 2 + 2 + 2 + 2 + 2 + 2 = 17 words
        self.assertEqual(len(loader.word_pool), 17)
        
        # Check category map
        self.assertEqual(len(loader.category_map["anagram_friendly"]), 3)
        self.assertEqual(len(loader.category_map["charade_friendly"]), 2)
    
    def test_get_random_seed(self):
        """Test getting random seeds."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Get a seed
        result = loader.get_random_seed()
        self.assertIsNotNone(result)
        
        word, clue_type = result
        self.assertIsInstance(word, str)
        self.assertIsInstance(clue_type, str)
        self.assertEqual(word, word.upper())
        
        # Word should be marked as used
        self.assertIn(word, loader.used_words)
    
    def test_avoid_duplicates(self):
        """Test that avoid_duplicates works correctly."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Get all words
        used_words = set()
        for _ in range(len(loader.word_pool)):
            result = loader.get_random_seed(avoid_duplicates=True)
            if result:
                word, _ = result
                self.assertNotIn(word, used_words)
                used_words.add(word)
        
        # Pool should be exhausted
        result = loader.get_random_seed(avoid_duplicates=True)
        self.assertIsNone(result)
    
    def test_get_specific_type_seed(self):
        """Test getting type-specific seeds."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Get an anagram seed
        result = loader.get_specific_type_seed("Anagram")
        self.assertIsNotNone(result)
        
        word, clue_type = result
        self.assertEqual(clue_type, "Anagram")
        self.assertIn(word, ["LISTEN", "SILENT", "ENLIST"])
    
    def test_reset_used(self):
        """Test resetting used words."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Use some words
        for _ in range(5):
            loader.get_random_seed()
        
        self.assertEqual(len(loader.used_words), 5)
        
        # Reset
        loader.reset_used()
        self.assertEqual(len(loader.used_words), 0)
    
    def test_get_pool_stats(self):
        """Test getting pool statistics."""
        loader = WordPoolLoader(self.test_seed_file)
        
        stats = loader.get_pool_stats()
        
        self.assertIn("total_words", stats)
        self.assertIn("used_words", stats)
        self.assertIn("available_words", stats)
        self.assertIn("type_distribution", stats)
        
        self.assertEqual(stats["total_words"], 17)
        self.assertEqual(stats["used_words"], 0)
        self.assertEqual(stats["available_words"], 17)
    
    def test_file_not_found(self):
        """Test handling of missing seed file."""
        with self.assertRaises(FileNotFoundError):
            WordPoolLoader("nonexistent_file.json")
    
    def test_invalid_json(self):
        """Test handling of invalid JSON."""
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, 'w') as f:
            f.write("not valid json{")
        
        with self.assertRaises(json.JSONDecodeError):
            WordPoolLoader(invalid_file)
        
        os.remove(invalid_file)
    
    def test_category_mapping(self):
        """Test that categories are mapped to correct clue types."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Check that anagram_friendly words are assigned Anagram type
        anagram_words = [word for word, ctype in loader.word_pool if ctype == "Anagram"]
        self.assertGreater(len(anagram_words), 0)
        
        # Check at least one specific word
        anagram_pairs = [(w, t) for w, t in loader.word_pool if w in ["LISTEN", "SILENT", "ENLIST"]]
        for word, clue_type in anagram_pairs:
            self.assertEqual(clue_type, "Anagram")
    
    def test_standard_utility_random_assignment(self):
        """Test that standard_utility words get assigned random types."""
        loader = WordPoolLoader(self.test_seed_file)
        
        # Standard utility words should be in pool with some type
        utility_pairs = [(w, t) for w, t in loader.word_pool if w in ["ELAPSED", "DRIVERS"]]
        self.assertEqual(len(utility_pairs), 2)
        
        # Each should have a type assigned
        for word, clue_type in utility_pairs:
            self.assertIsNotNone(clue_type)
            self.assertIn(clue_type, ["Anagram", "Charade", "Container", "Hidden Word"])


class TestCategoryMapping(unittest.TestCase):
    """Test the CATEGORY_TO_TYPE mapping."""
    
    def test_all_categories_mapped(self):
        """Test that all expected categories are in the mapping."""
        expected_categories = [
            "anagram_friendly",
            "charade_friendly",
            "hidden_word_friendly",
            "container_friendly",
            "reversal_friendly",
            "homophone_friendly",
            "double_def_friendly",
            "standard_utility"
        ]
        
        for category in expected_categories:
            self.assertIn(category, CATEGORY_TO_TYPE)
    
    def test_type_validity(self):
        """Test that all mapped types are valid clue types."""
        valid_types = [
            "Anagram", "Charade", "Hidden Word", "Container",
            "Reversal", "Homophone", "Double Definition", None
        ]
        
        for clue_type in CATEGORY_TO_TYPE.values():
            self.assertIn(clue_type, valid_types)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)

