"""
Test suite for Top-Tier Cryptic Abbreviations & Obscurity Check.

Tests that the auditor flags non-standard abbreviations and non-word fodder.
"""

import test_config
from auditor import XimeneanAuditor


def test_passes_priority_abbreviations():
    """Test that clues using TOP 50 priority abbreviations pass."""
    auditor = XimeneanAuditor()
    
    # Uses I (one/Roman numeral), DR (doctor), N (north)
    clue = {
        "clue": "One doctor heads north for discipline",
        "definition": "discipline",
        "answer": "IDRN",  # Made up for testing
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "I + DR + N",
            "indicator": "heads",
            "mechanism": "I (one) + DR (doctor) + N (north)"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 1: Priority Abbreviations (should pass)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Fodder: {clue['wordplay_parts']['fodder']}")
    print(f"\nObscurity Check: {'PASS' if result.obscurity_check else 'FAIL'}")
    print(f"Feedback: {result.obscurity_feedback}")
    
    assert result.obscurity_check, "Should pass with priority abbreviations"
    assert "standard Top 50" in result.obscurity_feedback or "PASS" in result.obscurity_feedback


def test_warns_extended_abbreviations():
    """Test that clues using extended (less common) abbreviations get warnings."""
    auditor = XimeneanAuditor()
    
    # Uses EN (extended - less common), RA (extended)
    clue = {
        "clue": "Nurse and artist create energy",
        "definition": "energy",
        "answer": "ENRA",  # Made up
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "EN + RA",
            "indicator": "and",
            "mechanism": "EN (nurse) + RA (artist)"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 2: Extended Abbreviations (should warn)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Fodder: {clue['wordplay_parts']['fodder']}")
    print(f"\nObscurity Check: {'PASS' if result.obscurity_check else 'FAIL'}")
    print(f"Feedback: {result.obscurity_feedback}")
    
    # Should pass but with warning
    assert result.obscurity_check, "Should pass (with warning)"
    assert "WARN" in result.obscurity_feedback or "extended" in result.obscurity_feedback.lower()


def test_passes_real_word_reversal():
    """Test that reversals with real English words pass."""
    auditor = XimeneanAuditor()
    
    # "tab" reversed = "bat" (both real words)
    clue = {
        "clue": "Tab returned for cricket stick",
        "definition": "cricket stick",
        "answer": "BAT",
        "type": "Reversal",
        "wordplay_parts": {
            "fodder": "tab",
            "indicator": "returned",
            "mechanism": "reverse of tab"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 3: Real Word Reversal (should pass)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Fodder: {clue['wordplay_parts']['fodder']}")
    print(f"Mechanism: {clue['wordplay_parts']['mechanism']}")
    print(f"\nObscurity Check: {'PASS' if result.obscurity_check else 'FAIL'}")
    print(f"Feedback: {result.obscurity_feedback}")
    
    # May skip if enchant not available
    if "enchant" not in result.obscurity_feedback:
        assert result.obscurity_check, "Should pass with real English word"


def test_flags_obscure_abbreviations():
    """Test that truly obscure abbreviations are flagged."""
    auditor = XimeneanAuditor()
    
    # Uses DIT (very obscure Morse code)
    clue = {
        "clue": "Signal with dit and dah",
        "definition": "signal",
        "answer": "DITDAH",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "DIT + DAH",
            "indicator": "with",
            "mechanism": "DIT (morse) + DAH (morse)"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 4: Obscure Abbreviations (should warn)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Fodder: {clue['wordplay_parts']['fodder']}")
    print(f"\nObscurity Check: {'PASS' if result.obscurity_check else 'FAIL'}")
    print(f"Feedback: {result.obscurity_feedback}")
    
    # Should warn about non-priority
    assert "WARN" in result.obscurity_feedback or "Non-priority" in result.obscurity_feedback


def test_passes_common_elements():
    """Test that common chemical elements pass as priority."""
    auditor = XimeneanAuditor()
    
    # AU (gold), FE (iron) - common elements
    clue = {
        "clue": "Gold and iron in mixture",
        "definition": "mixture",
        "answer": "AUFE",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "AU + FE",
            "indicator": "and",
            "mechanism": "AU (gold) + FE (iron)"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 5: Common Chemical Elements (should pass)")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Fodder: {clue['wordplay_parts']['fodder']}")
    print(f"\nObscurity Check: {'PASS' if result.obscurity_check else 'FAIL'}")
    print(f"Feedback: {result.obscurity_feedback}")
    
    assert result.obscurity_check, "Should pass with priority elements"
    assert "PASS" in result.obscurity_feedback or "standard" in result.obscurity_feedback.lower()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("TOP-TIER CRYPTIC ABBREVIATIONS TEST SUITE")
    print("Testing Obscurity Check & Priority Standards")
    print("="*70)
    
    test_passes_priority_abbreviations()
    test_warns_extended_abbreviations()
    test_passes_real_word_reversal()
    test_flags_obscure_abbreviations()
    test_passes_common_elements()
    
    print("\n" + "="*70)
    print("ALL OBSCURITY CHECK TESTS COMPLETED")
    print("="*70)
