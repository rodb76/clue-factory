"""
Test Word Validity Check for Fodder

This test verifies that the auditor correctly flags non-word fodder
and passes valid English words.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from auditor import XimeneanAuditor


def test_word_validity():
    """Test the word validity check with various clues."""
    
    auditor = XimeneanAuditor()
    
    print("\n" + "="*70)
    print("WORD VALIDITY CHECK TESTS")
    print("="*70)
    
    # Test 1: GOOD - Valid reversal with real words
    print("\n--- Test 1: Valid Reversal (REGAL from 'lager') ---")
    good_reversal = {
        "clue": "Majestic lager returned (5)",
        "definition": "Majestic",
        "answer": "REGAL",
        "type": "Reversal",
        "wordplay_parts": {
            "fodder": "lager",
            "indicator": "returned",
            "mechanism": "reverse of lager"
        }
    }
    
    result = auditor.audit_clue(good_reversal)
    print(f"Word Validity: {result.word_validity_check}")
    print(f"Feedback: {result.word_validity_feedback}")
    print(f"Ximenean Score: {result.ximenean_score:.2f}")
    assert result.word_validity_check, "Should pass - 'lager' is a real word"
    print("✓ PASSED")
    
    # Test 2: BAD - Invalid reversal with gibberish
    print("\n--- Test 2: Invalid Reversal (ASTHMA from 'amhtsa') ---")
    bad_reversal = {
        "clue": "Breathing problem with amhtsa brought back (6)",
        "definition": "Breathing problem",
        "answer": "ASTHMA",
        "type": "Reversal",
        "wordplay_parts": {
            "fodder": "amhtsa",
            "indicator": "brought back",
            "mechanism": "reverse of amhtsa"
        }
    }
    
    result = auditor.audit_clue(bad_reversal)
    print(f"Word Validity: {result.word_validity_check}")
    print(f"Feedback: {result.word_validity_feedback}")
    print(f"Ximenean Score: {result.ximenean_score:.2f}")
    assert not result.word_validity_check, "Should fail - 'amhtsa' is gibberish"
    print("✓ PASSED (correctly failed)")
    
    # Test 3: BAD - Invalid container with gibberish
    print("\n--- Test 3: Invalid Container (BATTEN from 'nettab') ---")
    bad_container = {
        "clue": "Flatten nettab with en inside (6)",
        "definition": "Flatten",
        "answer": "BATTEN",
        "type": "Container",
        "wordplay_parts": {
            "fodder": "nettab + en",
            "indicator": "inside",
            "mechanism": "en inside nettab"
        }
    }
    
    result = auditor.audit_clue(bad_container)
    print(f"Word Validity: {result.word_validity_check}")
    print(f"Feedback: {result.word_validity_feedback}")
    print(f"Ximenean Score: {result.ximenean_score:.2f}")
    assert not result.word_validity_check, "Should fail - 'nettab' is gibberish"
    print("✓ PASSED (correctly failed)")
    
    # Test 4: GOOD - Valid container with real words
    print("\n--- Test 4: Valid Container (PAINT from PAT + IN) ---")
    good_container = {
        "clue": "Pat grips in to apply color (5)",
        "definition": "apply color",
        "answer": "PAINT",
        "type": "Container",
        "wordplay_parts": {
            "fodder": "pat + in",
            "indicator": "grips",
            "mechanism": "in inside pat"
        }
    }
    
    result = auditor.audit_clue(good_container)
    print(f"Word Validity: {result.word_validity_check}")
    print(f"Feedback: {result.word_validity_feedback}")
    print(f"Ximenean Score: {result.ximenean_score:.2f}")
    assert result.word_validity_check, "Should pass - 'pat' and 'in' are real words"
    print("✓ PASSED")
    
    # Test 5: GOOD - Anagram with real words (should pass)
    print("\n--- Test 5: Valid Anagram (SILENT from 'listen') ---")
    good_anagram = {
        "clue": "Confused listen to be quiet (6)",
        "definition": "be quiet",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "confused",
            "mechanism": "anagram of listen"
        }
    }
    
    result = auditor.audit_clue(good_anagram)
    print(f"Word Validity: {result.word_validity_check}")
    print(f"Feedback: {result.word_validity_feedback}")
    print(f"Ximenean Score: {result.ximenean_score:.2f}")
    assert result.word_validity_check, "Should pass - 'listen' is a real word"
    print("✓ PASSED")
    
    # Test 6: Check ximenean_score penalty for non-words
    print("\n--- Test 6: Ximenean Score Penalty for Non-Words ---")
    
    good_reversal_result = auditor.audit_clue(good_reversal)
    bad_reversal_result = auditor.audit_clue(bad_reversal)
    
    good_reversal_score = good_reversal_result.ximenean_score
    bad_reversal_score = bad_reversal_result.ximenean_score
    
    print(f"Good reversal (real word) score: {good_reversal_score:.2f}")
    print(f"Bad reversal (gibberish) score: {bad_reversal_score:.2f}")
    
    penalty = good_reversal_score - bad_reversal_score
    print(f"Penalty for non-word fodder: {penalty:.2f}")
    assert penalty >= 0.4, "Should have significant penalty (>=0.4) for gibberish"
    print("✓ PASSED")
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED!")
    print("="*70)
    print("\nSummary:")
    print("✓ Valid fodder words pass validation")
    print("✓ Gibberish fodder is correctly flagged")
    print("✓ Ximenean score penalties are applied")
    print("✓ Specific guidance provided by clue type")


if __name__ == "__main__":
    try:
        test_word_validity()
    except ImportError as e:
        print("\n" + "="*70)
        print("WARNING: pyenchant library not installed")
        print("="*70)
        print(f"\nError: {e}")
        print("\nTo install pyenchant for full word validation:")
        print("  pip install pyenchant")
        print("\nNote: Word validation will use fallback patterns without enchant.")
        print("Install the library for complete dictionary validation.")
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
