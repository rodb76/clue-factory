import test_config
"""
Unit tests for the Mechanic validators.

Tests validation logic for all cryptic clue types without requiring API access.
"""

import unittest
from mechanic import (
    validate_anagram,
    validate_hidden_word,
    validate_charade,
    validate_container,
    validate_reversal,
    validate_length,
    validate_clue,
    normalize_text
)


class TestMechanic(unittest.TestCase):
    """Unit tests for mechanic validators."""
    
    def test_normalize_text(self):
        """Test text normalization."""
        self.assertEqual(normalize_text("Hello World"), "helloworld")
        self.assertEqual(normalize_text("TEST-123"), "test")
        self.assertEqual(normalize_text("  spaces  "), "spaces")
    
    def test_validate_length(self):
        """Test length validation."""
        # Valid lengths
        self.assertTrue(validate_length("LISTEN", "(6)"))
        self.assertTrue(validate_length("MAN TRAP", "(3,4)"))
        self.assertTrue(validate_length("T-BONE", "(1-4)"))
        
        # Invalid lengths
        self.assertFalse(validate_length("LISTEN", "(5)"))
        self.assertFalse(validate_length("WORD", "(3,4)"))
    
    def test_validate_anagram_valid(self):
        """Test valid anagram."""
        result = validate_anagram("LISTEN", "SILENT")
        self.assertTrue(result)
        self.assertIn("Valid anagram", result.message)
    
    def test_validate_anagram_invalid(self):
        """Test invalid anagram."""
        result = validate_anagram("HELLO", "WORLD")
        self.assertFalse(result)
        self.assertIn("Invalid anagram", result.message)
    
    def test_validate_anagram_spaces(self):
        """Test anagram with spaces."""
        result = validate_anagram("A GENTLEMAN", "ELEGANT MAN")
        self.assertTrue(result)
    
    def test_validate_hidden_word_valid(self):
        """Test valid hidden word."""
        result = validate_hidden_word("The cat hid", "THECA")
        self.assertTrue(result)
        
        result = validate_hidden_word("Silent listener", "LISTEN")
        self.assertTrue(result)
    
    def test_validate_hidden_word_invalid(self):
        """Test invalid hidden word."""
        result = validate_hidden_word("Tales Tennessee", "LISTEN")
        self.assertFalse(result)  # LISTEN is not actually in this phrase
    
    def test_validate_hidden_word_case_insensitive(self):
        """Test hidden word is case insensitive."""
        result = validate_hidden_word("THE CATHEDRAL", "Theca")
        self.assertTrue(result)
    
    def test_validate_charade_valid(self):
        """Test valid charade."""
        result = validate_charade(["PART", "RIDGE"], "PARTRIDGE")
        self.assertTrue(result)
        
        result = validate_charade(["B", "ACK"], "BACK")
        self.assertTrue(result)
    
    def test_validate_charade_invalid(self):
        """Test invalid charade."""
        result = validate_charade(["PART", "TREE"], "PARTRIDGE")
        self.assertFalse(result)
    
    def test_validate_charade_multiple_parts(self):
        """Test charade with multiple parts."""
        result = validate_charade(["S", "CARE", "CROW"], "SCARECROW")
        self.assertTrue(result)
    
    def test_validate_container_valid(self):
        """Test valid container."""
        result = validate_container("PAT", "IN", "PAINT")
        self.assertTrue(result)
        
        result = validate_container("PLAN", "I", "PLAIN")
        self.assertTrue(result)
    
    def test_validate_container_invalid(self):
        """Test invalid container."""
        result = validate_container("CAT", "DOG", "HOUSE")
        self.assertFalse(result)
    
    def test_validate_container_position(self):
        """Test container with specific position."""
        result = validate_container("PAT", "IN", "PAINT", position=2)
        self.assertTrue(result)
        
        result = validate_container("PAT", "IN", "PAINT", position=0)
        self.assertFalse(result)
    
    def test_validate_reversal_valid(self):
        """Test valid reversal."""
        result = validate_reversal("STAR", "RATS")
        self.assertTrue(result)
        
        result = validate_reversal("DRAW", "WARD")
        self.assertTrue(result)
    
    def test_validate_reversal_invalid(self):
        """Test invalid reversal."""
        result = validate_reversal("HELLO", "WORLD")
        self.assertFalse(result)
    
    def test_validate_clue_anagram(self):
        """Test clue validation for anagram."""
        clue = {
            "answer": "SILENT",
            "type": "Anagram",
            "wordplay_parts": {"fodder": "listen"}
        }
        result = validate_clue(clue)
        self.assertTrue(result)
    
    def test_validate_clue_hidden_word(self):
        """Test clue validation for hidden word."""
        clue = {
            "answer": "LISTEN",
            "type": "Hidden Word",
            "wordplay_parts": {"fodder": "Silent listener"}
        }
        result = validate_clue(clue)
        self.assertTrue(result)
    
    def test_validate_clue_charade(self):
        """Test clue validation for charade."""
        clue = {
            "answer": "PARTRIDGE",
            "type": "Charade",
            "wordplay_parts": {"parts": ["PART", "RIDGE"]}
        }
        result = validate_clue(clue)
        self.assertTrue(result)
    
    def test_validate_clue_container(self):
        """Test clue validation for container."""
        clue = {
            "answer": "PAINT",
            "type": "Container",
            "wordplay_parts": {"outer": "PAT", "inner": "IN"}
        }
        result = validate_clue(clue)
        self.assertTrue(result)
    
    def test_validate_clue_reversal(self):
        """Test clue validation for reversal."""
        clue = {
            "answer": "STAR",
            "type": "Reversal",
            "wordplay_parts": {"word": "RATS"}
        }
        result = validate_clue(clue)
        self.assertTrue(result)
    
    def test_validate_clue_double_definition(self):
        """Test clue validation for double definition (should pass with warning)."""
        clue = {
            "answer": "TENDER",
            "type": "Double Definition",
            "wordplay_parts": {}
        }
        result = validate_clue(clue)
        self.assertTrue(result)  # Passes but requires LLM
        self.assertTrue(result.details.get("requires_llm"))
    
    def test_validate_clue_homophone(self):
        """Test clue validation for homophone (should pass with warning)."""
        clue = {
            "answer": "WAIT",
            "type": "Homophone",
            "wordplay_parts": {"sounds_like": "WEIGHT"}
        }
        result = validate_clue(clue)
        self.assertTrue(result)  # Passes but requires LLM
        self.assertTrue(result.details.get("requires_llm"))
    
    def test_validate_clue_missing_answer(self):
        """Test clue validation with missing answer."""
        clue = {"type": "Anagram", "wordplay_parts": {}}
        result = validate_clue(clue)
        self.assertFalse(result)
        self.assertIn("No answer", result.message)
    
    def test_validate_clue_unknown_type(self):
        """Test clue validation with unknown type."""
        clue = {
            "answer": "TEST",
            "type": "UnknownType",
            "wordplay_parts": {}
        }
        result = validate_clue(clue)
        self.assertFalse(result)
        self.assertIn("Unknown clue type", result.message)


def run_tests():
    """Run the test suite."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()

