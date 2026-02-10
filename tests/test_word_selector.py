import test_config
"""
Unit tests for Phase 5: Word Selector and Factory
"""

import unittest
from word_selector import WordSelector, CLUE_TYPES


class TestWordSelector(unittest.TestCase):
    """Test WordSelector functionality."""
    
    def setUp(self):
        """Initialize WordSelector for tests."""
        self.selector = WordSelector(min_length=4, max_length=8)
    
    def test_word_pool_loaded(self):
        """WordSelector should load a word pool."""
        self.assertGreater(len(self.selector.word_pool), 0, 
                          "Word pool should not be empty")
    
    def test_word_pool_filtered_by_length(self):
        """All words should be within specified length range."""
        for word in self.selector.word_pool:
            self.assertGreaterEqual(len(word), self.selector.min_length,
                                   f"Word too short: {word}")
            self.assertLessEqual(len(word), self.selector.max_length,
                                f"Word too long: {word}")
    
    def test_words_are_alphabetic(self):
        """All words should contain only alphabetic characters."""
        for word in self.selector.word_pool:
            self.assertTrue(word.isalpha(), 
                           f"Word contains non-alphabetic characters: {word}")
    
    def test_words_are_uppercase(self):
        """All words should be uppercase."""
        for word in self.selector.word_pool:
            self.assertEqual(word, word.upper(),
                           f"Word not uppercase: {word}")
    
    def test_select_words_returns_correct_count(self):
        """select_words should return requested number of words."""
        count = 5
        word_pairs = self.selector.select_words(count)
        self.assertEqual(len(word_pairs), count,
                        f"Expected {count} words, got {len(word_pairs)}")
    
    def test_select_words_returns_tuples(self):
        """select_words should return (word, clue_type) tuples."""
        word_pairs = self.selector.select_words(3)
        for item in word_pairs:
            self.assertIsInstance(item, tuple, "Should return tuples")
            self.assertEqual(len(item), 2, "Tuple should have 2 elements")
            word, clue_type = item
            self.assertIsInstance(word, str, "Word should be string")
            self.assertIsInstance(clue_type, str, "Clue type should be string")
    
    def test_clue_types_are_valid(self):
        """Assigned clue types should be from supported list."""
        word_pairs = self.selector.select_words(10)
        for word, clue_type in word_pairs:
            self.assertIn(clue_type, CLUE_TYPES,
                         f"Invalid clue type: {clue_type}")
    
    def test_avoids_recently_used_words(self):
        """With avoid_recent=True, should not repeat words."""
        # Select first batch
        first_batch = self.selector.select_words(5, avoid_recent=True)
        first_words = {word for word, _ in first_batch}
        
        # Select second batch
        second_batch = self.selector.select_words(5, avoid_recent=True)
        second_words = {word for word, _ in second_batch}
        
        # Should have no overlap
        overlap = first_words & second_words
        self.assertEqual(len(overlap), 0,
                        f"Found repeated words: {overlap}")
    
    def test_reset_used_words(self):
        """reset_used_words should clear tracking."""
        self.selector.select_words(5)
        self.assertGreater(len(self.selector.used_words), 0,
                          "Used words should be tracked")
        
        self.selector.reset_used_words()
        self.assertEqual(len(self.selector.used_words), 0,
                        "Used words should be cleared")
    
    def test_suggest_clue_type_returns_valid_type(self):
        """_suggest_clue_type should return a valid clue type."""
        for word in ["STAR", "LISTEN", "PARTRIDGE"]:
            clue_type = self.selector._suggest_clue_type(word)
            self.assertIn(clue_type, CLUE_TYPES,
                         f"Invalid suggested type: {clue_type}")
    
    def test_builtin_word_list_has_variety(self):
        """Built-in word list should have multiple lengths."""
        lengths = {len(word) for word in self.selector.word_pool}
        self.assertGreater(len(lengths), 3,
                          "Should have words of various lengths")


class TestCLUE_TYPES(unittest.TestCase):
    """Test CLUE_TYPES constant."""
    
    def test_clue_types_defined(self):
        """CLUE_TYPES should be defined and non-empty."""
        self.assertIsInstance(CLUE_TYPES, list)
        self.assertGreater(len(CLUE_TYPES), 0)
    
    def test_expected_clue_types_present(self):
        """CLUE_TYPES should contain expected types."""
        expected = [
            "Anagram",
            "Hidden Word",
            "Charade",
            "Container",
            "Reversal",
            "Homophone",
            "Double Definition",
            "&lit"
        ]
        for clue_type in expected:
            self.assertIn(clue_type, CLUE_TYPES,
                         f"Missing expected clue type: {clue_type}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

