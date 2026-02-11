"""
Test suite for Minimalist Lie Logic (Classic Ximenean Economy).

Tests that the auditor enforces strict economy and the setter produces
deceptive but economical surfaces.
"""

import test_config
from auditor import XimeneanAuditor


def test_gold_standard_dormitory():
    """Test the gold standard anagram: 'Confused dirty room'."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Confused dirty room",
        "definition": "dormitory",
        "answer": "DORMITORY",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "dirty room",
            "indicator": "confused",
            "mechanism": "anagram of 'dirty room'"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 1: Gold Standard - Dormitory (Perfect 1:1 ratio)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nFiller Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"Filler Feedback: {result.filler_feedback}")
    print(f"\nFodder Presence: {'PASS' if result.fodder_presence_check else 'FAIL'}")
    print(f"Fodder Feedback: {result.fodder_presence_feedback}")
    
    assert result.passed, "Gold standard DORMITORY clue should pass all checks"
    assert result.fairness_score == 1.0, "Should achieve 100% score"
    assert result.filler_check, "Should pass filler check (zero extra words)"
    assert result.fodder_presence_check, "Fodder 'dirty room' present"


def test_gold_standard_regal():
    """Test the gold standard reversal: 'Majestic lager returned'."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Majestic lager returned",
        "definition": "majestic",
        "answer": "REGAL",
        "type": "Reversal",
        "wordplay_parts": {
            "fodder": "lager",
            "indicator": "returned",
            "mechanism": "reverse of lager"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 2: Gold Standard - REGAL (Zero filler)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nAll Checks:")
    print(f"  Direction: {'PASS' if result.direction_check else 'FAIL'} - {result.direction_feedback}")
    print(f"  Double Duty: {'PASS' if result.double_duty_check else 'FAIL'}")
    print(f"  Indicator Fair: {'PASS' if result.indicator_fairness_check else 'FAIL'}")
    print(f"  Fodder Present: {'PASS' if result.fodder_presence_check else 'FAIL'}")
    print(f"  Filler Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"  Grammar: {'PASS' if result.indicator_grammar_check else 'FAIL'} - {result.indicator_grammar_feedback}")
    
    assert result.passed, "Gold standard REGAL clue should pass all checks"
    assert result.fairness_score == 1.0, "Should achieve 100% score"
    assert result.filler_check, "Should pass filler check (zero extra words)"


def test_fails_literal_connectors():
    """Test that literal connectors like 'gives' and 'plus' cause warnings/failures."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Listen mixed gives quiet result with becomes silence",
        "definition": "quiet",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "mixed",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 3: Excessive Literal Connectors (should fail)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nFiller Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"Filler Feedback: {result.filler_feedback}")
    
    # This should FAIL because:
    # 1. Too many connectors (gives, with, becomes = 3)
    # 2. Indicative indicator "mixed"
    assert not result.passed, "Clue with 3 connectors should fail"
    assert not result.filler_check, "Should fail filler check (3 connectors)"


def test_fails_non_essential_words():
    """Test that non-essential words fail the Thematic Necessity Test."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Perhaps listen carefully disturbed for quiet result",
        "definition": "quiet",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "disturbed",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 4: Non-Essential Words (should fail Thematic Necessity Test)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nFiller Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"Filler Feedback: {result.filler_feedback}")
    
    # Should FAIL because "perhaps", "carefully", "result" are non-essential filler words
    assert not result.passed, "Clue with non-essential words should fail"
    assert not result.filler_check, "Should fail filler check"
    assert "perhaps" in result.filler_feedback.lower() or "carefully" in result.filler_feedback.lower(), \
        "Should identify filler words"


def test_minimalist_with_one_connector():
    """Test that clues with 0-1 connectors pass (MINIMALIST LIE ideal)."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Mix listen for quiet",
        "definition": "quiet",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "mix",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 5: Minimalist with 1 Connector (should pass)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nAll Checks:")
    print(f"  Direction: {'PASS' if result.direction_check else 'FAIL'}")
    print(f"  Double Duty: {'PASS' if result.double_duty_check else 'FAIL'}")
    print(f"  Indicator Fair: {'PASS' if result.indicator_fairness_check else 'FAIL'} - {result.indicator_fairness_feedback}")
    print(f"  Fodder Present: {'PASS' if result.fodder_presence_check else 'FAIL'}")
    print(f"  Filler Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"  Grammar: {'PASS' if result.indicator_grammar_check else 'FAIL'}")
    
    assert result.passed, "Clue with 1 connector should pass"
    assert result.filler_check, "Should pass filler check (1 connector ok)"
    assert result.fairness_score == 1.0, "Should achieve 100% score"


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MINIMALIST LIE LOGIC TEST SUITE")
    print("Testing Classic Ximenean Economy Standards")
    print("="*70)
    
    test_gold_standard_dormitory()
    test_gold_standard_regal()
    test_fails_literal_connectors()
    test_fails_non_essential_words()
    test_minimalist_with_one_connector()
    
    print("\n" + "="*70)
    print("ALL MINIMALIST LIE TESTS COMPLETED")
    print("="*70)
