import test_config
"""
Test the updated directional check in Auditor.
Tests that directional words in fodder are ignored, only indicator is checked.
"""

from auditor import XimeneanAuditor

print("\n" + "="*70)
print("AUDITOR DIRECTIONAL CHECK TEST")
print("="*70 + "\n")

# Test Case 1: Directional word in FODDER (should PASS)
clue_with_up_in_fodder = {
    "clue": "Scrambled cups and plates (6)",
    "definition": "plates",
    "answer": "SCUPPA",
    "type": "Anagram",
    "wordplay_parts": {
        "fodder": "cups up",  # "up" is in the fodder - should be OK
        "indicator": "scrambled",  # indicator is fine
        "mechanism": "anagram of 'cups up'"
    }
}

print("TEST 1: Directional word 'up' in FODDER")
print(f"  Fodder: '{clue_with_up_in_fodder['wordplay_parts']['fodder']}'")
print(f"  Indicator: '{clue_with_up_in_fodder['wordplay_parts']['indicator']}'")

auditor = XimeneanAuditor()
passed, feedback = auditor._check_direction(clue_with_up_in_fodder)

print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
print(f"  Feedback: {feedback}")
print()

# Test Case 2: Directional word in INDICATOR (should FAIL)
clue_with_up_in_indicator = {
    "clue": "Listen going up (6)",
    "definition": "Listen",
    "answer": "SILENT",
    "type": "Reversal",
    "wordplay_parts": {
        "fodder": "listen",
        "indicator": "going up",  # "up" is in the indicator - should FAIL
        "mechanism": "reversal of 'listen'"
    }
}

print("TEST 2: Directional word 'up' in INDICATOR")
print(f"  Fodder: '{clue_with_up_in_indicator['wordplay_parts']['fodder']}'")
print(f"  Indicator: '{clue_with_up_in_indicator['wordplay_parts']['indicator']}'")

passed, feedback = auditor._check_direction(clue_with_up_in_indicator)

print(f"  Result: {'✓ PASS' if passed else '✗ FAIL (expected)'}")
print(f"  Feedback: {feedback}")
print()

# Test Case 3: Directional word "on" in FODDER (should PASS)
clue_with_on_in_fodder = {
    "clue": "Rearranged person with no end (6)",
    "definition": "someone",
    "answer": "PERSON",
    "type": "Anagram",
    "wordplay_parts": {
        "fodder": "person",  # contains "on" - should be OK
        "indicator": "rearranged",
        "mechanism": "anagram of 'person'"
    }
}

print("TEST 3: Word containing 'on' in FODDER")
print(f"  Fodder: '{clue_with_on_in_fodder['wordplay_parts']['fodder']}'")
print(f"  Indicator: '{clue_with_on_in_fodder['wordplay_parts']['indicator']}'")

passed, feedback = auditor._check_direction(clue_with_on_in_fodder)

print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
print(f"  Feedback: {feedback}")
print()

# Test Case 4: Clean clue with no directional words (should PASS)
clean_clue = {
    "clue": "Confused listen (6)",
    "definition": "Confused",
    "answer": "SILENT",
    "type": "Anagram",
    "wordplay_parts": {
        "fodder": "listen",
        "indicator": "confused",
        "mechanism": "anagram of 'listen'"
    }
}

print("TEST 4: Clean clue with no directional words")
print(f"  Fodder: '{clean_clue['wordplay_parts']['fodder']}'")
print(f"  Indicator: '{clean_clue['wordplay_parts']['indicator']}'")

passed, feedback = auditor._check_direction(clean_clue)

print(f"  Result: {'✓ PASS' if passed else '✗ FAIL'}")
print(f"  Feedback: {feedback}")
print()

print("="*70)
print("SUMMARY:")
print("  ✓ Test 1 should PASS (directional in fodder = OK)")
print("  ✗ Test 2 should FAIL (directional in indicator = BAD)")
print("  ✓ Test 3 should PASS (substring in fodder = OK)")
print("  ✓ Test 4 should PASS (no directional words)")
print("="*70 + "\n")

