"""
Test suite for Advanced Narrative Masking & Thematic Logic.

Tests that the auditor flags literal letter listings and setter uses proper
cryptic substitutions.
"""

import test_config
from auditor import XimeneanAuditor


def test_fails_literal_listing():
    """Test that clues with literal letter listings fail narrative integrity check."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Earnest request with en, treat, y",
        "definition": "Earnest request",
        "answer": "ENTREATY",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "EN + TREAT + Y",
            "indicator": "with",
            "mechanism": "EN + TREAT + Y"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 1: Literal Letter Listing (should fail)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nNarrative Integrity: {'PASS' if result.narrative_integrity_check else 'FAIL'}")
    print(f"Feedback: {result.narrative_integrity_feedback}")
    
    assert not result.passed, "Clue with literal listing should fail"
    assert not result.narrative_integrity_check, "Should fail narrative integrity"
    assert "literal letter listing" in result.narrative_integrity_feedback.lower()


def test_passes_masked_narrative():
    """Test that clues using proper cryptic substitutions pass."""
    auditor = XimeneanAuditor()
    
    # Good version: uses "nurse" for EN, "unknown" for Y
    clue = {
        "clue": "Earnest request from nurse's treat for unknown",
        "definition": "Earnest request",
        "answer": "ENTREATY",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "nurse treat unknown",
            "indicator": "from",
            "mechanism": "EN (nurse) + TREAT + Y (unknown)"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 2: Proper Cryptic Substitutions (should pass)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nNarrative Integrity: {'PASS' if result.narrative_integrity_check else 'FAIL'}")
    print(f"Feedback: {result.narrative_integrity_feedback}")
    
    assert result.narrative_integrity_check, "Should pass narrative integrity with proper substitutions"


def test_warns_suspicious_tokens():
    """Test that clues with suspicious 2-letter tokens get warnings."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Found in re, la, te position",
        "definition": "Found in",
        "answer": "RELATE",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "re la te",
            "indicator": "in",
            "mechanism": "RE + LA + TE"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 3: Suspicious Unmasked Tokens (should warn or fail)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nNarrative Integrity: {'PASS' if result.narrative_integrity_check else 'FAIL'}")
    print(f"Feedback: {result.narrative_integrity_feedback}")
    
    # Should either fail or warn
    assert not result.passed or "WARN" in result.narrative_integrity_feedback


def test_passes_natural_clue():
    """Test that naturally written clues pass all checks."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Final Greek letter found in home game",
        "definition": "Final Greek letter",
        "answer": "OMEGA",
        "type": "Hidden Word",
        "wordplay_parts": {
            "fodder": "home game",
            "indicator": "found in",
            "mechanism": "hidden in 'h[OMEGA]me'"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 4: Natural English Surface (should pass)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nResult: {'PASS' if result.passed else 'FAIL'}")
    print(f"Fairness Score: {result.fairness_score * 100:.1f}%")
    print(f"\nAll Checks:")
    print(f"  Narrative Integrity: {'PASS' if result.narrative_integrity_check else 'FAIL'}")
    print(f"  Feedback: {result.narrative_integrity_feedback}")
    
    assert result.passed, "Natural clue should pass all checks"
    assert result.narrative_integrity_check, "Should pass narrative integrity"
    assert result.fairness_score == 1.0, "Should achieve 100% score"


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ADVANCED NARRATIVE MASKING TEST SUITE")
    print("Testing NO-GIBBERISH RULE & Cryptic Substitutions")
    print("="*70)
    
    test_fails_literal_listing()
    test_passes_masked_narrative()
    test_warns_suspicious_tokens()
    test_passes_natural_clue()
    
    print("\n" + "="*70)
    print("ALL NARRATIVE MASKING TESTS COMPLETED")
    print("="*70)
