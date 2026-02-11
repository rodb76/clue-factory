import test_config
"""
Unit tests for Phase 3 components (Solver, Referee, Orchestrator).

Tests the adversarial loop components without requiring full API access.
"""

import unittest
from referee import referee, referee_with_validation, normalize_answer, calculate_similarity


class TestReferee(unittest.TestCase):
    """Unit tests for Referee logic."""
    
    def test_normalize_answer(self):
        """Test answer normalization."""
        self.assertEqual(normalize_answer("LISTEN"), "LISTEN")
        self.assertEqual(normalize_answer("listen"), "LISTEN")
        self.assertEqual(normalize_answer("L I S T E N"), "LISTEN")
        self.assertEqual(normalize_answer("L-I-S-T-E-N"), "LISTEN")
        self.assertEqual(normalize_answer("man trap"), "MANTRAP")
    
    def test_calculate_similarity(self):
        """Test similarity calculation."""
        self.assertEqual(calculate_similarity("LISTEN", "LISTEN"), 1.0)
        self.assertGreater(calculate_similarity("LISTEN", "SILENT"), 0.4)
        self.assertLess(calculate_similarity("LISTEN", "HEARING"), 0.5)
        self.assertAlmostEqual(calculate_similarity("PAINT", "PANT"), 0.888, places=2)
    
    def test_referee_exact_match(self):
        """Test referee with exact match."""
        result = referee("SILENT", "SILENT", "Test reasoning")
        self.assertTrue(result.passed)
        self.assertEqual(result.similarity, 1.0)
        self.assertIn("Exact match", result.feedback)
    
    def test_referee_case_insensitive(self):
        """Test referee is case insensitive."""
        result = referee("LISTEN", "listen", "Test reasoning")
        self.assertTrue(result.passed)
        self.assertEqual(result.similarity, 1.0)
    
    def test_referee_with_spaces(self):
        """Test referee handles spaces."""
        result = referee("MANTRAP", "MAN TRAP", "Test reasoning")
        self.assertTrue(result.passed)
        self.assertEqual(result.similarity, 1.0)
    
    def test_referee_mismatch(self):
        """Test referee with wrong answer."""
        result = referee("SILENT", "LISTEN", "Test reasoning")
        self.assertFalse(result.passed)
        self.assertLess(result.similarity, 1.0)
        self.assertIn("Mismatch", result.feedback)
    
    def test_referee_length_mismatch(self):
        """Test referee detects length mismatch."""
        result = referee("PAINT", "PANT", "Test reasoning")
        self.assertFalse(result.passed)
        self.assertIn("Length mismatch", result.feedback)
    
    def test_referee_high_similarity_strict(self):
        """Test referee with high similarity in strict mode."""
        result = referee("PAINT", "PANT", "Test reasoning", strict=True)
        self.assertFalse(result.passed)  # Strict mode requires exact match
    
    def test_referee_high_similarity_lenient(self):
        """Test referee with high similarity in lenient mode."""
        # Note: PAINT vs PANT is 88.9% similar
        result = referee("PAINT", "PANT", "Test reasoning", strict=False)
        self.assertTrue(result.passed)  # Lenient mode accepts >80% similarity
    
    def test_referee_with_validation_success(self):
        """Test referee_with_validation with matching answers."""
        clue_json = {
            "answer": "SILENT",
            "clue": "Confused listen",
            "type": "Anagram"
        }
        solution_json = {
            "answer": "SILENT",
            "reasoning": "Anagram of LISTEN",
            "confidence": "High"
        }
        
        result = referee_with_validation(clue_json, solution_json)
        self.assertTrue(result.passed)
    
    def test_referee_with_validation_failure(self):
        """Test referee_with_validation with mismatched answers."""
        clue_json = {
            "answer": "SILENT",
            "clue": "Confused listen",
            "type": "Anagram"
        }
        solution_json = {
            "answer": "LISTEN",
            "reasoning": "Incorrect reasoning",
            "confidence": "Low"
        }
        
        result = referee_with_validation(clue_json, solution_json)
        self.assertFalse(result.passed)
    
    def test_referee_missing_original_answer(self):
        """Test referee with missing original answer."""
        clue_json = {}
        solution_json = {"answer": "SILENT"}
        
        result = referee_with_validation(clue_json, solution_json)
        self.assertFalse(result.passed)
        self.assertIn("No original answer", result.feedback)
    
    def test_referee_missing_solver_answer(self):
        """Test referee with missing solver answer."""
        clue_json = {"answer": "SILENT"}
        solution_json = {}
        
        result = referee_with_validation(clue_json, solution_json)
        self.assertFalse(result.passed)
        self.assertIn("failed to provide an answer", result.feedback)
    
    def test_referee_result_to_dict(self):
        """Test RefereeResult serialization."""
        result = referee("SILENT", "SILENT", "Test reasoning")
        result_dict = result.to_dict()
        
        self.assertIn("passed", result_dict)
        self.assertIn("original_answer", result_dict)
        self.assertIn("solver_answer", result_dict)
        self.assertIn("similarity", result_dict)
        self.assertIn("feedback", result_dict)
        self.assertTrue(result_dict["passed"])


class TestCompatibilityUtilityFunctions(unittest.TestCase):
    """Test utility functions for compatibility fields."""
    
    def test_ensure_enumeration_missing(self):
        """Test adding enumeration when missing."""
        from main import ensure_enumeration
        
        clue = "Confused listen"
        answer = "SILENT"
        result = ensure_enumeration(clue, answer)
        
        self.assertEqual(result, "Confused listen (6)")
    
    def test_ensure_enumeration_present(self):
        """Test preserving existing enumeration."""
        from main import ensure_enumeration
        
        clue = "Confused listen (6)"
        answer = "SILENT"
        result = ensure_enumeration(clue, answer)
        
        self.assertEqual(result, "Confused listen (6)")
    
    def test_ensure_enumeration_multi_word(self):
        """Test enumeration for multi-word answers."""
        from main import ensure_enumeration
        
        clue = "Stop rugby foul"
        answer = "KNOCK ON THE HEAD"
        result = ensure_enumeration(clue, answer)
        
        self.assertIn("(5,2,3,4)", result)
    
    def test_calculate_length_simple(self):
        """Test length calculation for simple word."""
        from main import calculate_length
        
        self.assertEqual(calculate_length("SILENT"), 6)
    
    def test_calculate_length_with_spaces(self):
        """Test length calculation ignoring spaces."""
        from main import calculate_length
        
        self.assertEqual(calculate_length("KNOCK ON THE HEAD"), 14)
    
    def test_calculate_length_with_hyphens(self):
        """Test length calculation ignoring hyphens."""
        from main import calculate_length
        
        self.assertEqual(calculate_length("MAN-TRAP"), 7)
    
    def test_generate_reveal_order_length(self):
        """Test reveal order has correct length."""
        from main import generate_reveal_order
        
        order = generate_reveal_order("SILENT")
        self.assertEqual(len(order), 6)
    
    def test_generate_reveal_order_unique(self):
        """Test reveal order contains unique indices."""
        from main import generate_reveal_order
        
        order = generate_reveal_order("TESTS")
        self.assertEqual(len(order), len(set(order)))  # All unique
    
    def test_generate_clue_id(self):
        """Test clue ID generation."""
        from main import generate_clue_id
        
        clue_id = generate_clue_id("SILENT", "Anagram", "20260211")
        self.assertIn("anagram", clue_id.lower())
        self.assertIn("SILENT", clue_id)


class TestClueResultIntegration(unittest.TestCase):
    """Test ClueResult data structure from main.py."""
    
    def test_clue_result_import(self):
        """Test that ClueResult can be imported."""
        try:
            from main import ClueResult
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import ClueResult: {e}")
    
    def test_clue_result_creation(self):
        """Test ClueResult creation."""
        from main import ClueResult
        
        result = ClueResult(
            word="SILENT",
            clue_type="Anagram",
            passed=True
        )
        
        self.assertEqual(result.word, "SILENT")
        self.assertEqual(result.clue_type, "Anagram")
        self.assertTrue(result.passed)
    
    def test_clue_result_to_dict(self):
        """Test ClueResult serialization with compatibility fields."""
        from main import ClueResult
        
        result = ClueResult(
            word="SILENT",
            clue_type="Anagram",
            passed=True,
            clue_json={
                "clue": "Confused listen",
                "definition": "Confused",
                "explanation": "Anagram of LISTEN"
            },
            # Compatibility fields
            clue_id="anagram_12345_SILENT",
            clue_with_enum="Confused listen (6)",
            length=6,
            reveal_order=[2, 4, 0, 5, 1, 3]
        )
        
        result_dict = result.to_dict()
        
        # Standard fields
        self.assertEqual(result_dict["word"], "SILENT")
        self.assertEqual(result_dict["clue_type"], "Anagram")
        self.assertTrue(result_dict["passed"])
        
        # Compatibility fields
        self.assertIn("id", result_dict)
        self.assertEqual(result_dict["id"], "anagram_12345_SILENT")
        self.assertIn("clue", result_dict)
        self.assertEqual(result_dict["clue"], "Confused listen (6)")
        self.assertIn("length", result_dict)
        self.assertEqual(result_dict["length"], 6)
        self.assertIn("reveal_order", result_dict)
        self.assertEqual(result_dict["reveal_order"], [2, 4, 0, 5, 1, 3])


def run_tests():
    """Run the test suite."""
    print("\n" + "="*80)
    print("PHASE 3 UNIT TESTS: Solver, Referee, Orchestrator")
    print("="*80 + "\n")
    
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()

