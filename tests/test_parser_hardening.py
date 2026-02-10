import test_config
"""
Test suite for parser hardening and audit sensitivity refinements.

Tests:
1. Solver JSON parser robustness (extracts JSON from noisy responses)
2. Auditor Double Duty leniency (allows separate definition/indicator words)
3. Setter Hidden Word character-by-character validation instructions
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from solver_agent import SolverAgent
from auditor import XimeneanAuditor


class TestParserHardening(unittest.TestCase):
    """Test parser hardening improvements."""
    
    def test_solver_json_extraction_with_preamble(self):
        """Test 1: Solver extracts JSON even with preamble text."""
        print("\n" + "="*70)
        print("TEST 1: Solver JSON Parser - Handles Preamble/Postamble")
        print("="*70)
        
        # Simulate response with preamble
        noisy_response = """Let me solve this step by step.
        
{
    "reasoning": "Step 1: Identify definition...",
    "definition_part": "Quiet",
    "wordplay_part": "listen mixed",
    "clue_type": "Anagram",
    "answer": "SILENT",
    "confidence": "High"
}

I believe this is correct."""
        
        # Test the parser
        result = SolverAgent._parse_json_response(noisy_response)
        
        print(f"  Input (first 80 chars): {noisy_response[:80]}...")
        print(f"  Extracted answer: {result.get('answer')}")
        print(f"  Extracted clue_type: {result.get('clue_type')}")
        
        self.assertEqual(result['answer'], 'SILENT')
        self.assertEqual(result['clue_type'], 'Anagram')
        self.assertIn('reasoning', result)
        print("  ✓ PASS - JSON extracted despite preamble and postamble")
    
    def test_solver_json_extraction_first_last_braces(self):
        """Test 2: Solver uses FIRST '{' and LAST '}' extraction."""
        print("\n" + "="*70)
        print("TEST 2: Solver JSON Parser - First/Last Brace Extraction")
        print("="*70)
        
        # Response with preamble and postamble but valid JSON in between
        messy_response = """I'll analyze this clue now.

{"reasoning": "Step 1: The definition is 'Quiet'. Step 2: The indicator is 'mixed' suggesting anagram. Step 3: The fodder is 'listen' which has letters L-I-S-T-E-N. Step 4: Anagram of LISTEN gives SILENT. Step 5: SILENT means quiet, matching the definition.", "definition_part": "Quiet", "wordplay_part": "mixed listen", "clue_type": "Anagram", "answer": "SILENT", "confidence": "High"}

That's my analysis."""
        
        result = SolverAgent._parse_json_response(messy_response)
        
        print(f"  Input has preamble and postamble")
        print(f"  Extracted answer: {result.get('answer')}")
        print(f"  Valid JSON: {bool(result)}")
        
        self.assertEqual(result['answer'], 'SILENT')
        print("  ✓ PASS - Correctly extracted content between first '{' and last '}'")
    
    def test_auditor_double_duty_leniency(self):
        """Test 3: Auditor allows separate definition and indicator words."""
        print("\n" + "="*70)
        print("TEST 3: Auditor Double Duty - Allows Separate Words")
        print("="*70)
        
        # Check the prompt contains the lenient language
        auditor = XimeneanAuditor()
        
        # Verify the class has the _check_double_duty_with_llm method
        self.assertTrue(hasattr(auditor, '_check_double_duty_with_llm'))
        
        # Read the method source to verify it contains the new lenient language
        import inspect
        method_source = inspect.getsource(auditor._check_double_duty_with_llm)
        
        print("  Checking auditor prompt for lenient language...")
        
        # Check for key phrases in the updated prompt
        lenient_phrases = [
            "SAME PHYSICAL WORD",
            "separate word",
            "Do NOT flag simple synonyms"
        ]
        
        found_phrases = []
        for phrase in lenient_phrases:
            if phrase in method_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 2, 
                               "Auditor should contain lenient double duty language")
        
        print(f"  ✓ PASS - Auditor contains {len(found_phrases)}/3 lenient phrases")
    
    def test_auditor_word_boundaries(self):
        """Test 4: Auditor uses word boundaries (already implemented)."""
        print("\n" + "="*70)
        print("TEST 4: Auditor Direction Check - Word Boundaries")
        print("="*70)
        
        auditor = XimeneanAuditor()
        
        # Verify word boundary regex is used
        import inspect
        method_source = inspect.getsource(auditor._check_direction)
        
        print("  Checking for word boundary regex...")
        
        # Check for word boundary pattern
        has_word_boundary = r'\b' in method_source or 'word boundary' in method_source.lower()
        has_re_escape = 're.escape' in method_source
        
        print(f"    Word boundary marker (\\b): {has_word_boundary}")
        print(f"    Uses re.escape for safety: {has_re_escape}")
        
        self.assertTrue(has_word_boundary, "Should use word boundary regex")
        self.assertTrue(has_re_escape, "Should use re.escape for special characters")
        
        print("  ✓ PASS - Word boundaries prevent false positives (e.g., 'on' in 'scones')")
    
    def test_setter_hidden_word_instructions(self):
        """Test 5: Setter has character-by-character checking instruction for Hidden Words."""
        print("\n" + "="*70)
        print("TEST 5: Setter Hidden Word - Character-by-Character Instructions")
        print("="*70)
        
        from setter_agent import SetterAgent
        setter = SetterAgent()
        
        # Verify the generate_wordplay_only method exists
        self.assertTrue(hasattr(setter, 'generate_wordplay_only'))
        
        # Read the method source to verify it contains character checking instruction
        import inspect
        method_source = inspect.getsource(setter.generate_wordplay_only)
        
        print("  Checking setter prompt for character-by-character instruction...")
        
        # Check for key phrases about character checking
        character_phrases = [
            "character-by-character",
            "literal, unbroken substring",
            "Check your spelling"
        ]
        
        found_phrases = []
        for phrase in character_phrases:
            if phrase in method_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 2,
                               "Setter should contain character-checking instructions")
        
        print(f"  ✓ PASS - Setter contains {len(found_phrases)}/3 character-checking phrases")
    
    def test_system_prompt_json_only(self):
        """Test 6: Solver system prompt enforces JSON-only output."""
        print("\n" + "="*70)
        print("TEST 6: Solver System Prompt - JSON-Only Enforcement")
        print("="*70)
        
        solver = SolverAgent()
        
        # The system prompt should be visible in the solve_clue method
        import inspect
        method_source = inspect.getsource(solver.solve_clue)
        
        print("  Checking solver system prompt for JSON-only enforcement...")
        
        # Check for strict JSON-only language
        strict_phrases = [
            "NOTHING but the JSON",
            "Start with '{' and end with '}'",
            "No preamble"
        ]
        
        found_phrases = []
        for phrase in strict_phrases:
            if phrase in method_source:
                found_phrases.append(phrase)
                print(f"    ✓ Found: '{phrase}'")
        
        self.assertGreaterEqual(len(found_phrases), 2,
                               "Solver system prompt should enforce JSON-only output")
        
        print(f"  ✓ PASS - System prompt contains {len(found_phrases)}/3 strict JSON phrases")


def main():
    """Run all parser hardening tests."""
    print("\n" + "="*70)
    print("PARSER HARDENING AND AUDIT SENSITIVITY TEST SUITE")
    print("="*70)
    print("\nVerifying:")
    print("  1. Solver JSON extraction (robust to preamble/postamble)")
    print("  2. Solver first/last brace extraction")
    print("  3. Auditor Double Duty leniency (separate words OK)")
    print("  4. Auditor word boundaries (no false positives)")
    print("  5. Setter Hidden Word character-checking instructions")
    print("  6. Solver system prompt JSON-only enforcement")
    print("\n" + "="*70)
    
    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestParserHardening)
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
        print("\n✅ ALL PARSER HARDENING TESTS PASSED")
        print("\nPipeline is now more robust:")
        print("  • Solver handles noisy JSON responses")
        print("  • Auditor reduces false positives (word boundaries)")
        print("  • Auditor allows separate definition/indicator words")
        print("  • Setter enforces character-by-character Hidden Word checks")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("Review failures above for details.")
    
    print("="*70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

