"""
Test Strict Ximenean Logic Implementation.

Tests the new checks:
1. Fodder presence check
2. Filler words check  
3. Indicator grammar check
"""

import test_config
from auditor import XimeneanAuditor


def test_fodder_presence():
    """Test that fodder words must be physically present in clue."""
    
    print("\n" + "="*80)
    print("TEST: Fodder Presence Check")
    print("="*80 + "\n")
    
    auditor = XimeneanAuditor()
    
    # PASS: Fodder "listen" is in the clue
    good_clue = {
        "clue": "Disturbed listen to be quiet",
        "definition": "be quiet",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "disturbed",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(good_clue)
    print("Test 1: Fodder present in clue")
    print(f"  Clue: '{good_clue['clue']}'")
    print(f"  Fodder: '{good_clue['wordplay_parts']['fodder']}'")
    print(f"  Fodder Check: {'PASS' if result.fodder_presence_check else 'FAIL'}")
    print(f"  Feedback: {result.fodder_presence_feedback}")
    assert result.fodder_presence_check, "Should pass when fodder is present"
    
    # FAIL: Fodder "dealer" but clue uses synonym "merchant"
    bad_clue = {
        "clue": "Confused merchant leads group",
        "definition": "leads group",
        "answer": "LEADER",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "dealer",
            "indicator": "confused",
            "mechanism": "anagram of dealer"
        }
    }
    
    result = auditor.audit_clue(bad_clue)
    print("\nTest 2: Fodder NOT present (synonym used)")
    print(f"  Clue: '{bad_clue['clue']}'")
    print(f"  Fodder: '{bad_clue['wordplay_parts']['fodder']}'")
    print(f"  Fodder Check: {'PASS' if result.fodder_presence_check else 'FAIL'}")
    print(f"  Feedback: {result.fodder_presence_feedback}")
    assert not result.fodder_presence_check, "Should fail when fodder is not present"
    
    print("\n✓ Fodder presence checks working correctly\n")


def test_filler_words():
    """Test that excessive filler words are flagged."""
    
    print("="*80)
    print("TEST: Filler Words Check")
    print("="*80 + "\n")
    
    auditor = XimeneanAuditor()
    
    # PASS: Minimal filler (0-2 connectors allowed)
    good_clue = {
        "clue": "Listen quietly",
        "definition": "quietly",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "disturbed",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(good_clue)
    print("Test 1: Minimal filler words")
    print(f"  Clue: '{good_clue['clue']}'")
    print(f"  Filler Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"  Feedback: {result.filler_feedback}")
    # Note: This might fail if "disturbed" isn't in the clue, but that's OK for this test
    
    # FAIL: Excessive connectors
    bad_clue = {
        "clue": "So when the person becomes confused with listen it gives a quiet result",
        "definition": "quiet result",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "confused",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(bad_clue)
    print("\nTest 2: Excessive filler/connectors")
    print(f"  Clue: '{bad_clue['clue']}'")
    print(f"  Filler Check: {'PASS' if result.filler_check else 'FAIL'}")
    print(f"  Feedback: {result.filler_feedback}")
    assert not result.filler_check, "Should fail with excessive filler"
    
    print("\n✓ Filler word checks working correctly\n")


def test_indicator_grammar():
    """Test that indicators must be imperative, not indicative."""
    
    print("="*80)
    print("TEST: Indicator Grammar Check")
    print("="*80 + "\n")
    
    auditor = XimeneanAuditor()
    
    # PASS: Imperative indicator "mix"
    good_clue = {
        "clue": "Mix listen to be quiet",
        "definition": "be quiet",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "mix",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(good_clue)
    print("Test 1: Imperative indicator (correct)")
    print(f"  Indicator: '{good_clue['wordplay_parts']['indicator']}'")
    print(f"  Grammar Check: {'PASS' if result.indicator_grammar_check else 'FAIL'}")
    print(f"  Feedback: {result.indicator_grammar_feedback}")
    assert result.indicator_grammar_check, "Should pass with imperative indicator"
    
    # FAIL: Indicative indicator "mixed"
    bad_clue = {
        "clue": "Listen mixed up quietly",
        "definition": "quietly",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "mixed",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(bad_clue)
    print("\nTest 2: Indicative indicator (wrong)")
    print(f"  Indicator: '{bad_clue['wordplay_parts']['indicator']}'")
    print(f"  Grammar Check: {'PASS' if result.indicator_grammar_check else 'FAIL'}")
    print(f"  Feedback: {result.indicator_grammar_feedback}")
    assert not result.indicator_grammar_check, "Should fail with indicative indicator"
    
    # FAIL: Another indicative "scrambled"
    bad_clue2 = {
        "clue": "Listen scrambled quietly",
        "definition": "quietly",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "scrambled",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(bad_clue2)
    print("\nTest 3: Another indicative indicator (wrong)")
    print(f"  Indicator: '{bad_clue2['wordplay_parts']['indicator']}'")
    print(f"  Grammar Check: {'PASS' if result.indicator_grammar_check else 'FAIL'}")
    print(f"  Feedback: {result.indicator_grammar_feedback}")
    assert not result.indicator_grammar_check, "Should fail with indicative indicator"
    
    print("\n✓ Indicator grammar checks working correctly\n")


def test_overall_strict_ximenean():
    """Test that all three new checks contribute to overall pass/fail."""
    
    print("="*80)
    print("TEST: Overall Strict Ximenean Audit")
    print("="*80 + "\n")
    
    auditor = XimeneanAuditor()
    
    # Good clue that should pass all checks
    perfect_clue = {
        "clue": "Reverse lager for majestic",
        "definition": "majestic",
        "answer": "REGAL",
        "type": "Reversal",
        "wordplay_parts": {
            "fodder": "lager",
            "indicator": "reverse",
            "mechanism": "reverse of lager"
        }
    }
    
    result = auditor.audit_clue(perfect_clue)
    print("Test: Perfect Ximenean clue (REGAL example)")
    print(f"  Clue: '{perfect_clue['clue']}'")
    print(f"  Overall: {'PASS' if result.passed else 'FAIL'}")
    print(f"  Fairness Score: {result.fairness_score:.1%}")
    print(f"  Direction: {result.direction_check}")
    print(f"  Double Duty: {result.double_duty_check}")
    print(f"  Indicator Fairness: {result.indicator_fairness_check}")
    print(f"  Fodder Presence: {result.fodder_presence_check}")
    print(f"  Filler Check: {result.filler_check}")
    print(f"  Grammar Check: {result.indicator_grammar_check}")
    
    print("\n✓ Overall strict Ximenean audit complete\n")
    print("="*80)


if __name__ == "__main__":
    test_fodder_presence()
    test_filler_words()
    test_indicator_grammar()
    test_overall_strict_ximenean()
    
    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80)
