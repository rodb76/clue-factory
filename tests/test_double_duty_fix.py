import test_config
"""
Test: Auditor Double-Duty Hallucination Fix
Verifies all requested changes are present:
1. Auditor: Rewritten Double Duty prompt with specific examples
2. Auditor: DIRECTIONAL_BLOCKLIST uses re.IGNORECASE and word boundaries
3. Solver: Added preamble warning
4. Main: Enhanced audit failure logging
"""

import unittest
import os

class TestDoubleHallucinationFix(unittest.TestCase):
    
    def setUp(self):
        self.base_path = os.path.dirname(__file__)
        
    def test_auditor_double_duty_rewrite(self):
        """Test 1: Auditor has rewritten Double Duty prompt"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the specific new language
        self.assertIn("You are a strict but fair Ximenean auditor", content)
        self.assertIn("'Double Duty' error is VERY SPECIFIC", content)
        self.assertIn("only occurs if a word is being used as a mechanical instruction (indicator) AND is also the only word providing the definition", content)
        
        # Check for the specific examples
        self.assertIn("Supply food or look after someone's needs", content)
        self.assertIn("CATER", content)
        self.assertIn("Confused enlist soldiers to be quiet", content)
        self.assertIn("SILENT", content)
        self.assertIn("ONLY flag FAIL if a word like 'scrambled' is the definition and the anagram indicator at the same time", content)
        
        # Check for updated examples
        self.assertIn("PASS: \"Serenity in pieces (5)\"", content)
        self.assertIn("PASS: \"Supply food or look after someone's needs (5)\"", content)
        self.assertIn("PASS: \"Confused enlist soldiers to be quiet (6)\"", content)
        
        print("✓ TEST 1 PASSED: Auditor has rewritten Double Duty prompt")
        
    def test_auditor_directional_blocklist_regex(self):
        """Test 2: Auditor DIRECTIONAL_BLOCKLIST uses re.IGNORECASE and word boundaries"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check that the directional check uses word boundaries
        self.assertIn(r"pattern = r'\b' + re.escape(term) + r'\b'", content)
        self.assertIn("re.search(pattern, indicator, re.IGNORECASE)", content)
        
        print("✓ TEST 2 PASSED: Directional blocklist uses word boundaries and re.IGNORECASE")
        
    def test_solver_preamble_warning(self):
        """Test 3: Solver has preamble warning"""
        solver_path = os.path.join(self.base_path, "solver_agent.py")
        with open(solver_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the new preamble warning
        self.assertIn("Return ONLY the JSON", content)
        self.assertIn("Do not include 'I'll solve this' or any Step 0 preamble text", content)
        
        print("✓ TEST 3 PASSED: Solver has preamble warning")
        
    def test_main_enhanced_audit_logging(self):
        """Test 4: Main has enhanced audit failure logging"""
        main_path = os.path.join(self.base_path, "main.py")
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for specific failure logging
        self.assertIn("DIRECTION CHECK FAILED", content)
        self.assertIn("DOUBLE DUTY CHECK FAILED", content)
        self.assertIn("FAIRNESS CHECK FAILED", content)
        
        # Ensure full feedback is logged (not truncated)
        self.assertIn("audit_result.direction_feedback}", content)
        self.assertIn("audit_result.double_duty_feedback}", content)
        self.assertIn("audit_result.indicator_fairness_feedback}", content)
        
        print("✓ TEST 4 PASSED: Main has enhanced audit failure logging")
        
    def test_model_tiering_preserved(self):
        """Test 5: Verify Sonnet/Haiku tiering still intact"""
        # Check auditor.py uses logic model
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("LOGIC_MODEL_ID", content)
        
        # Check solver_agent.py uses logic model
        solver_path = os.path.join(self.base_path, "solver_agent.py")
        with open(solver_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("LOGIC_MODEL_ID", content)
        
        print("✓ TEST 5 PASSED: Model tiering structure preserved")
        
    def test_all_agents_import(self):
        """Test 6: All agents import successfully"""
        try:
            from setter_agent import SetterAgent
            from auditor import XimeneanAuditor
            from solver_agent import SolverAgent
            print("✓ TEST 6 PASSED: All agents import successfully")
        except Exception as e:
            self.fail(f"Agent import failed: {str(e)}")

if __name__ == "__main__":
    # Run tests with verbose output
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDoubleHallucinationFix)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("DOUBLE DUTY HALLUCINATION FIX TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED")
        print("\nChanges verified:")
        print("  1. Auditor: Rewritten Double Duty prompt with CATER/SILENT examples ✓")
        print("  2. Auditor: Word boundaries and re.IGNORECASE in directional check ✓")
        print("  3. Solver: Preamble warning added ✓")
        print("  4. Main: Enhanced audit failure logging ✓")
        print("  5. Model tiering: Preserved ✓")
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

