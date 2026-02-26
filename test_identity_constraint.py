"""
Test script for identity constraint validation.

This script tests the new identity constraint that prevents the answer
from appearing in the wordplay fodder.
"""

from mechanic import validate_anagram, validate_hidden_word, check_identity_constraint

def test_identity_constraint():
    """Test that identity constraint catches lazy clues."""
    
    print("=" * 80)
    print("TESTING IDENTITY CONSTRAINT IN CLUES")
    print("=" * 80)
    print()
    
    # Test cases: (fodder, answer, should_pass, description)
    test_cases = [
        # Anagram tests
        ("listen", "SILENT", True, "Anagram - Valid: 'listen' does not contain 'SILENT'"),
        ("silent", "SILENT", False, "Anagram - Invalid: fodder IS the answer"),
        ("dirty room", "DORMITORY", True, "Anagram - Valid: different words"),
        ("dormitory", "DORMITORY", False, "Anagram - Invalid: fodder IS the answer"),
        ("paints", "PAINT", False, "Anagram - Invalid: fodder contains answer variant 'paint'"),
        
        # Hidden Word tests (note: check_identity_constraint is for anagrams, not hidden words)
        ("the art", "HEAR", False, "Helper function - Would reject: 'HEAR' substring found in fodder"),
        ("listen carefully", "LISTEN", False, "Helper function - Would reject: 'LISTEN' found in fodder"),
        ("tales entered", "SENT", False, "Helper function - Would reject: 'SENT' substring found in fodder"),
        
        # Edge cases
        ("star light", "STAR", False, "Invalid: answer appears as complete word in fodder"),
        ("restart engine", "START", False, "Invalid: answer variant 'start' in fodder"),
    ]
    
    passed = 0
    failed = 0
    
    print("Testing identity constraint helper function:")
    print("-" * 80)
    
    for fodder, answer, expected_pass, description in test_cases:
        result = check_identity_constraint(fodder, answer)
        
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
    
    # Now test specific validation functions
    print("\nTesting anagram validation with identity constraint:")
    print("-" * 80)
    
    anagram_tests = [
        ("listen", "SILENT", True, "Valid anagram"),
        ("silent", "SILENT", False, "Invalid - fodder is answer"),
        ("dirty room", "DORMITORY", True, "Valid anagram"),
    ]
    
    for fodder, answer, expected_pass, description in anagram_tests:
        result = validate_anagram(fodder, answer)
        
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
    
    # Test hidden word validation
    print("\nTesting hidden word validation with identity constraint:")
    print("-" * 80)
    
    hidden_tests = [
        ("the art", "HEAR", True, "Valid - spans two words: tHEARt"),
        ("listen", "LISTEN", False, "Invalid - single word IS answer"),
        ("tales entered", "SENT", True, "Valid - hidden across words: taleSENTered"),
    ]
    
    for fodder, answer, expected_pass, description in hidden_tests:
        result = validate_hidden_word(fodder, answer)
        
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
    print(f"RESULTS: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 80)
    print()
    
    return passed, failed


if __name__ == "__main__":
    test_identity_constraint()
