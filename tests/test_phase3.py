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
        """Test ClueResult serialization."""
        from main import ClueResult
        
        result = ClueResult(
            word="SILENT",
            clue_type="Anagram",
            passed=True,
            clue_json={
                "clue": "Confused listen",
                "definition": "Confused",
                "explanation": "Anagram of LISTEN"
            }
        )
        
        result_dict = result.to_dict()
        
        self.assertEqual(result_dict["word"], "SILENT")
        self.assertEqual(result_dict["clue_type"], "Anagram")
        self.assertTrue(result_dict["passed"])
        self.assertEqual(result_dict["clue"], "Confused listen")


def run_tests():
    """Run the test suite."""
    print("\n" + "="*80)
    print("PHASE 3 UNIT TESTS: Solver, Referee, Orchestrator")
    print("="*80 + "\n")
    
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()

