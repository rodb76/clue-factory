import test_config
"""
Unit tests for Phase 4: Ximenean Auditor
"""

import unittest
from auditor import XimeneanAuditor, DIRECTIONAL_BLOCKLIST, NOUN_INDICATORS


class TestAuditorDirectionCheck(unittest.TestCase):
    """Test directional blocklist checks."""
    
    def setUp(self):
        self.auditor = XimeneanAuditor()
    
    def test_good_clue_passes_direction(self):
        """Good clue with no down-only indicators should pass."""
        clue = {
            "clue": "Quietly listen to storyteller (6)",
            "definition": "Quietly",
            "wordplay_parts": {
                "indicator": "listen",
                "mechanism": "hear"
            }
        }
        passed, feedback = self.auditor._check_direction(clue)
        self.assertTrue(passed, f"Expected pass, got: {feedback}")
    
    def test_clue_with_rising_fails_direction(self):
        """Clue with 'rising' indicator should fail."""
        clue = {
            "clue": "Listen rising (6)",
            "definition": "Listen",
            "wordplay_parts": {
                "indicator": "rising",
                "mechanism": ""
            }
        }
        passed, feedback = self.auditor._check_direction(clue)
        self.assertFalse(passed, "Expected to fail direction check")
        self.assertIn("rising", feedback.lower())
    
    def test_blocklist_contains_expected_terms(self):
        """Verify blocklist has all required down-only indicators."""
        required_terms = {
            "rising", "lifted", "climbing", "up", "upwards",
            "skyward", "mounting", "ascending", "on", "supports",
            "overhead", "over", "underneath", "atop"
        }
        for term in required_terms:
            self.assertIn(term, DIRECTIONAL_BLOCKLIST, 
                         f"Missing required term: {term}")


class TestAuditorIndicatorFairness(unittest.TestCase):
    """Test indicator fairness checks."""
    
    def setUp(self):
        self.auditor = XimeneanAuditor()
    
    def test_anagram_with_noun_indicator_fails(self):
        """Anagrams with noun indicators should fail fairness."""
        clue = {
            "type": "Anagram",
            "wordplay_parts": {
                "indicator": "jumble"
            }
        }
        passed, feedback = self.auditor._check_indicator_fairness(clue)
        self.assertFalse(passed, "Expected to fail fairness check")
        self.assertIn("jumble", feedback.lower())
    
    def test_anagram_with_verb_indicator_passes(self):
        """Anagrams with verb indicators should pass."""
        clue = {
            "type": "Anagram",
            "wordplay_parts": {
                "indicator": "mixed"
            }
        }
        passed, feedback = self.auditor._check_indicator_fairness(clue)
        self.assertTrue(passed, f"Expected pass, got: {feedback}")
    
    def test_noun_indicators_defined(self):
        """Verify noun indicators list is populated."""
        self.assertGreater(len(NOUN_INDICATORS), 0)
        self.assertIn("jumble", NOUN_INDICATORS)


class TestAuditResultSerialization(unittest.TestCase):
    """Test AuditResult can be serialized to dict."""
    
    def setUp(self):
        self.auditor = XimeneanAuditor()
    
    def test_audit_result_to_dict(self):
        """AuditResult should serialize to dict."""
        clue = {
            "clue": "Test clue (4)",
            "definition": "Test",
            "type": "Anagram",
            "wordplay_parts": {"indicator": "mixed", "mechanism": "test"}
        }
        audit_result = self.auditor.audit_clue(clue)
        result_dict = audit_result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertIn("passed", result_dict)
        self.assertIn("direction_check", result_dict)
        self.assertIn("double_duty_check", result_dict)
        self.assertIn("indicator_fairness_check", result_dict)
        self.assertIn("fairness_score", result_dict)


class TestAuditorIntegration(unittest.TestCase):
    """Integration tests for complete auditor workflow."""
    
    def setUp(self):
        self.auditor = XimeneanAuditor()
    
    def test_multiple_checks_all_pass(self):
        """All checks should pass for a good clue."""
        clue = {
            "clue": "Hear from tale (6)",
            "definition": "Hear",
            "type": "Hidden Word",
            "answer": "LISTEN",
            "wordplay_parts": {
                "fodder": "tale",
                "indicator": "from",
                "mechanism": "LISTEN hidden in tale"
            },
            "explanation": "From tale"
        }
        result = self.auditor.audit_clue(clue)
        
        self.assertTrue(result.direction_check, "Direction check should pass")
        self.assertTrue(result.fairness_score >= 0.5, "Fairness score should be acceptable")


if __name__ == "__main__":
    unittest.main(verbosity=2)

