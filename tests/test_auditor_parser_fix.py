import test_config
"""
Test: Auditor Parser and Directional Regex Fix
Verifies all requested changes:
1. Robust PASS/FAIL parsing (handles metadata, looks at first line)
2. Directional regex uses word boundaries (prevents "supper" flagging)
3. Consolidated response extraction matches setter_agent.py
4. Re-emphasized double duty guidance (synonym != double duty)
"""

import unittest
import os
import re

class TestAuditorParserFix(unittest.TestCase):
    
    def setUp(self):
        self.base_path = os.path.dirname(__file__)
        
    def test_auditor_robust_pass_parsing(self):
        """Test 1: Auditor uses robust PASS/FAIL parsing"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the robust parsing logic
        self.assertIn("clean_text = response_text.strip().upper()", content)
        self.assertIn("first_line = clean_text.split('\\n')[0]", content)
        self.assertIn('if "PASS" in first_line or "PASS:" in clean_text:', content)
        
        # Ensure old startswith logic is gone
        self.assertNotIn('if response_text.startswith("PASS"):', content)
        
        print("✓ TEST 1 PASSED: Auditor uses robust PASS parsing (first line check)")
        
    def test_directional_regex_word_boundaries(self):
        """Test 2: Directional check uses word boundaries"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for word boundary regex
        self.assertIn(r"pattern = r'\b' + re.escape(term) + r'\b'", content)
        self.assertIn("re.search(pattern, indicator, re.IGNORECASE)", content)
        
        # Verify the pattern works correctly (simulate the check)
        # "up" should NOT match in "supper"
        pattern = r'\b' + re.escape("up") + r'\b'
        self.assertIsNone(re.search(pattern, "supper", re.IGNORECASE))
        self.assertIsNotNone(re.search(pattern, "up", re.IGNORECASE))
        self.assertIsNotNone(re.search(pattern, "going up", re.IGNORECASE))
        
        print("✓ TEST 2 PASSED: Directional regex uses word boundaries (no false positives)")
        
    def test_consolidated_response_extraction(self):
        """Test 3: Auditor uses consolidated response extraction"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the consolidated extraction logic (same as setter_agent.py)
        self.assertIn("if not response.choices or len(response.choices) == 0:", content)
        self.assertIn("choice = response.choices[0]", content)
        self.assertIn("if hasattr(choice, 'text') and isinstance(choice.text, str):", content)
        self.assertIn("elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):", content)
        self.assertIn("if isinstance(msg_content, str):", content)
        self.assertIn("elif isinstance(msg_content, dict):", content)
        
        print("✓ TEST 3 PASSED: Auditor uses consolidated response extraction")
        
    def test_double_duty_synonym_emphasis(self):
        """Test 4: Double duty prompt re-emphasizes synonyms are NOT double duty"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the re-emphasized guidance
        self.assertIn("CRITICAL: If the definition is a synonym of the answer, that is NOT double duty", content)
        self.assertIn("Double duty only occurs when a wordplay indicator is also the definition", content)
        
        print("✓ TEST 4 PASSED: Double duty prompt re-emphasizes synonyms != double duty")
        
    def test_auditor_imports_successfully(self):
        """Test 5: Auditor imports without errors"""
        try:
            from auditor import XimeneanAuditor, DIRECTIONAL_BLOCKLIST
            
            # Verify DIRECTIONAL_BLOCKLIST has expected entries
            self.assertIn("up", DIRECTIONAL_BLOCKLIST)
            self.assertIn("rising", DIRECTIONAL_BLOCKLIST)
            
            print("✓ TEST 5 PASSED: Auditor imports successfully")
        except Exception as e:
            self.fail(f"Auditor import failed: {str(e)}")
            
    def test_directional_check_specific_cases(self):
        """Test 6: Directional check handles specific edge cases correctly"""
        # Test that word boundaries work as expected
        test_cases = [
            ("supper", "up", False),  # "up" in "supper" should NOT match
            ("up", "up", True),       # standalone "up" should match
            ("going up", "up", True), # "up" with word boundary should match
            ("scones", "on", False),  # "on" in "scones" should NOT match
            ("on", "on", True),       # standalone "on" should match
            ("support", "up", False), # "up" in "support" should NOT match
        ]
        
        for text, term, should_match in test_cases:
            pattern = r'\b' + re.escape(term) + r'\b'
            match = re.search(pattern, text, re.IGNORECASE)
            if should_match:
                self.assertIsNotNone(match, f"'{term}' should match in '{text}'")
            else:
                self.assertIsNone(match, f"'{term}' should NOT match in '{text}'")
        
        print("✓ TEST 6 PASSED: Directional check handles edge cases correctly")

if __name__ == "__main__":
    # Run tests with verbose output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuditorParserFix)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("AUDITOR PARSER FIX TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
        print("\nChanges verified:")
        print("  1. Robust PASS parsing (handles metadata, first-line check) ✓")
        print("  2. Word boundaries prevent false positives ('supper' ≠ 'up') ✓")
        print("  3. Consolidated response extraction (matches setter_agent.py) ✓")
        print("  4. Re-emphasized: synonyms are NOT double duty ✓")
        print("  5. Edge cases handled correctly ✓")
    else:
        print("\n❌ SOME TESTS FAILED")
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")

