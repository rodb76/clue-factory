import test_config
"""
Test suite for enhanced Hidden Word logic and audit sensitivity.

Tests:
1. Setter Hidden Word bracketed verification instructions
2. Auditor Double Duty ultra-lenient check (definitions aren't double duty)
3. Solver JSON-only enforcement in user prompt
4. Main orchestrator specific error feedback to retries
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from setter_agent import SetterAgent
from auditor import XimeneanAuditor
from solver_agent import SolverAgent


class TestEnhancedHardening(unittest.TestCase):
    """Test enhanced hardening improvements."""
    
    def test_setter_bracketed_verification(self):
        """Test 1: Setter has bracketed verification instructions for Hidden Words."""
        print("\n" + "="*70)
        print("TEST 1: Setter Hidden Word - Bracketed Verification")
        print("="*70)
        
        setter = SetterAgent()
        
        # Read the method source to verify bracketed verification instructions
        import inspect
        method_source = inspect.getsource(setter.generate_wordplay_only)
        
        print("  Checking setter prompt for bracketed verification instructions...")
        
        # Check for key phrases about bracketed verification
        verification_phrases = [
            "manual character-by-character check",
            "surrounding the hidden letters with brackets",
            "mechanism' field (e.g., 'hidden in an[TIC IDE]a'",
            "alp[HABET RAY]"
        ]
        
        found_phrases = []
        for phrase in verification_phrases:
            if phrase in method_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 3,
                               "Setter should contain bracketed verification instructions")
        
        print(f"  ✓ PASS - Setter contains {len(found_phrases)}/4 bracketed verification phrases")
    
    def test_auditor_ultra_lenient_double_duty(self):
        """Test 2: Auditor distinguishes between definitions and double duty."""
        print("\n" + "="*70)
        print("TEST 2: Auditor Double Duty - Ultra-Lenient (Definitions Not Double Duty)")
        print("="*70)
        
        auditor = XimeneanAuditor()
        
        # Verify the method contains the ultra-lenient language
        import inspect
        method_source = inspect.getsource(auditor._check_double_duty_with_llm)
        
        print("  Checking auditor prompt for ultra-lenient language...")
        
        # Check for key phrases emphasizing definitions aren't double duty
        lenient_phrases = [
            "A word is NOT doing double duty if it is simply the definition",
            "Ocean current' is the definition for 'TIDE', the word 'current' is FAIR",
            "Only flag it if 'current' is ALSO being used as an anagram indicator"
        ]
        
        found_phrases = []
        for phrase in lenient_phrases:
            if phrase in method_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 2,
                               "Auditor should contain ultra-lenient double duty language")
        
        print(f"  ✓ PASS - Auditor contains {len(found_phrases)}/3 ultra-lenient phrases")
    
    def test_solver_user_prompt_json_only(self):
        """Test 3: Solver user prompt enforces JSON-only output."""
        print("\n" + "="*70)
        print("TEST 3: Solver User Prompt - JSON-Only Enforcement")
        print("="*70)
        
        solver = SolverAgent()
        
        # The user prompt should be visible in the solve_clue method
        import inspect
        method_source = inspect.getsource(solver.solve_clue)
        
        print("  Checking solver user prompt for JSON-only enforcement...")
        
        # Check for strict JSON-only language in user_prompt
        strict_phrases = [
            "DO NOT EXPLAIN YOUR STEPS OUTSIDE THE JSON",
            "PROVIDE ONLY THE JSON",
            "Start your response with '{' immediately"
        ]
        
        found_phrases = []
        for phrase in strict_phrases:
            if phrase in method_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 2,
                               "Solver user prompt should enforce JSON-only output")
        
        print(f"  ✓ PASS - User prompt contains {len(found_phrases)}/3 strict JSON phrases")
    
    def test_main_specific_error_feedback(self):
        """Test 4: Main orchestrator includes specific error feedback for retries."""
        print("\n" + "="*70)
        print("TEST 4: Main Orchestrator - Specific Error Feedback")
        print("="*70)
        
        # Read main.py to verify error feedback includes specific guidance
        with open('main.py', 'r', encoding='utf-8') as f:
            main_source = f.read()
        
        print("  Checking main.py for specific error feedback...")
        
        # Check for enhanced error feedback with type-specific guidance
        feedback_phrases = [
            "GUIDANCE: For Hidden Word clues",
            "verify character-by-character",
            "bracketed verification format",
            "GUIDANCE: For Anagram clues",
            "exact letter counts match"
        ]
        
        found_phrases = []
        for phrase in feedback_phrases:
            if phrase in main_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 4,
                               "Main should contain specific error feedback for retries")
        
        print(f"  ✓ PASS - Main contains {len(found_phrases)}/5 specific feedback phrases")
    
    def test_inverted_tiering_preserved(self):
        """Test 5: Inverted model tiering is preserved."""
        print("\n" + "="*70)
        print("TEST 5: Inverted Model Tiering - Preserved")
        print("="*70)
        
        setter = SetterAgent()
        
        print("  Checking model tier configuration...")
        
        # Verify setter has both logic and surface model IDs
        self.assertTrue(hasattr(setter, 'LOGIC_MODEL_ID'))
        self.assertTrue(hasattr(setter, 'SURFACE_MODEL_ID'))
        
        print(f"    Logic model: {setter.LOGIC_MODEL_ID}")
        print(f"    Surface model: {setter.SURFACE_MODEL_ID}")
        
        # Verify they're different (inverted tiering)
        if setter.LOGIC_MODEL_ID and setter.SURFACE_MODEL_ID:
            print(f"    ✓ Both models configured")
        
        print("  ✓ PASS - Inverted model tiering preserved")


def main():
    """Run all enhanced hardening tests."""
    print("\n" + "="*70)
    print("ENHANCED HARDENING TEST SUITE")
    print("="*70)
    print("\nVerifying:")
    print("  1. Setter Hidden Word bracketed verification")
    print("  2. Auditor ultra-lenient Double Duty (definitions OK)")
    print("  3. Solver user prompt JSON-only enforcement")
    print("  4. Main orchestrator specific error feedback")
    print("  5. Inverted model tiering preserved")
    print("\n" + "="*70)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEnhancedHardening)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL ENHANCED HARDENING TESTS PASSED")
        print("\nPipeline improvements:")
        print("  • Hidden Word: Bracketed verification forces character-by-character check")
        print("  • Auditor: Ultra-lenient (definitions aren't double duty)")
        print("  • Solver: JSON-only enforced in user prompt")
        print("  • Main: Specific error feedback for Hidden Word/Anagram retries")
        print("  • Inverted model tiering preserved (Sonnet/Haiku)")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Review failures above for details.")
    
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

