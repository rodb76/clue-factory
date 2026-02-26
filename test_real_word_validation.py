"""
Test script for real-word validation in anagram mechanics.

This script tests the new dictionary validation feature added to mechanic.py.
"""

from mechanic import validate_anagram

def test_real_word_validation():
    """Test that anagram validation catches non-dictionary words."""
    
    print("=" * 80)
    print("TESTING REAL-WORD VALIDATION IN ANAGRAMS")
    print("=" * 80)
    print()
    
    # Test cases: (fodder, answer, should_pass, description)
    test_cases = [
        ("dirty room", "DORMITORY", True, "Valid: both 'dirty' and 'room' are real words"),
        ("sng ro", "ROUSING", False, "Invalid: 'sng' is not a real word"),
        ("tame sng", "MAGNETS", False, "Invalid: 'sng' is gibberish"),
        ("listen", "SILENT", True, "Valid: 'listen' is a real word"),
        ("evil", "VILE", True, "Valid: 'evil' is a real word"),
        ("ab cd", "ABCD", False, "Invalid: 'ab' and 'cd' are not real words (unless very short abbreviations)"),
        ("a rose", "AROSE", True, "Valid: 'a' and 'rose' are real words"),
        ("last king", "STALKING", True, "Valid: 'last' and 'king' are real words"),
    ]
    
    passed = 0
    failed = 0
    
    for fodder, answer, expected_pass, description in test_cases:
        result = validate_anagram(fodder, answer)
        
        # Check if result matches expectation
        if result.is_valid == expected_pass:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        print(f"{status}: {description}")
        print(f"   Fodder: '{fodder}' → Answer: '{answer}'")
        print(f"   Result: {result.message}")
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    print()
    
    if failed > 0:
        print("Note: Some failures may be expected if enchant dictionary is not available.")
        print("If enchant is not installed, real-word validation is skipped.")
    
    return passed, failed


if __name__ == "__main__":
    test_real_word_validation()
