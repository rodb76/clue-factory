import test_config
"""
Test: Relaxed Auditor and Hardened Hidden Word Verification
Verifies all requested changes are present:
1. Auditor: "serenity/PEACE" example for Double Duty
2. Setter: "r[ADIO ORTA]rio" bracketed verification
3. Solver: "max 50 words" reasoning limit
4. Main: Pre-solve character match (already implemented)
"""

import unittest
import os

class TestRelaxedHardening(unittest.TestCase):
    
    def setUp(self):
        self.base_path = os.path.dirname(__file__)
        
    def test_auditor_double_duty_serenity_example(self):
        """Test 1: Auditor has serenity/PEACE example"""
        auditor_path = os.path.join(self.base_path, "auditor.py")
        with open(auditor_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the specific language requested
        self.assertIn("A word is NOT doing double duty if it is the intended definition", content)
        self.assertIn("if the answer is 'PEACE' and the clue uses 'serenity'", content)
        self.assertIn("Serenity in pieces (5)", content)
        self.assertIn("serenity\" is definition (synonym of PEACE)", content)
        print("✓ TEST 1 PASSED: Auditor has serenity/PEACE Double Duty example")
        
    def test_setter_hidden_word_brackets(self):
        """Test 2: Setter has r[ADIO ORTA]rio bracketed verification"""
        setter_path = os.path.join(self.base_path, "setter_agent.py")
        with open(setter_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the specific bracketed example
        self.assertIn("MANDATORY: You must verify the spelling by placing brackets", content)
        self.assertIn("Example for 'AORTA': 'found in r[ADIO ORTA]rio'", content)
        self.assertIn("If the letters are not consecutive, it is a FAIL", content)
        print("✓ TEST 2 PASSED: Setter has r[ADIO ORTA]rio bracketed verification")
        
    def test_solver_reasoning_length_limit(self):
        """Test 3: Solver has 'max 50 words' reasoning constraint"""
        solver_path = os.path.join(self.base_path, "solver_agent.py")
        with open(solver_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the reasoning length limit
        self.assertIn("max 50 words", content)
        self.assertIn("Keep your reasoning concise (max 50 words)", content)
        print("✓ TEST 3 PASSED: Solver has 'max 50 words' reasoning limit")
        
    def test_main_pre_solve_character_match(self):
        """Test 4: Main has pre-solve character match for Hidden Words"""
        main_path = os.path.join(self.base_path, "main.py")
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for the pre-surface substring check
        self.assertIn("PRE-SURFACE CHECK", content)
        self.assertIn("fodder_no_spaces", content)
        self.assertIn("if word.upper() not in fodder_no_spaces", content)
        self.assertIn("Pre-surface check failed", content)
        print("✓ TEST 4 PASSED: Main has pre-solve character match")
        
    def test_model_tiering_preserved(self):
        """Test 5: Verify Sonnet/Haiku tiering still intact"""
        # Check setter_agent.py has dual-model tiering
        setter_path = os.path.join(self.base_path, "setter_agent.py")
        with open(setter_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("LOGIC_MODEL_ID", content)
        self.assertIn("SURFACE_MODEL_ID", content)
        self.assertIn("Inverted Model Tiering", content)
        
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
        
        print("✓ TEST 5 PASSED: Sonnet/Haiku model tiering structure preserved")
        
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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRelaxedHardening)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("RELAXED HARDENING TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL RELAXED HARDENING TESTS PASSED")
        print("\nChanges verified:")
        print("  1. Auditor: serenity/PEACE Double Duty example ✓")
        print("  2. Setter: r[ADIO ORTA]rio bracketed verification ✓")
        print("  3. Solver: max 50 words reasoning limit ✓")
        print("  4. Main: Pre-solve character match ✓")
        print("  5. Model tiering: Sonnet/Haiku preserved ✓")
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

