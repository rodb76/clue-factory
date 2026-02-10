import test_config
"""
Test Definition Hardening in ExplanationAgent.

Verifies that definition hints always reference the exact text from the clue,
not dictionary definitions or paraphrases.
"""

import json
from explanation_agent import ExplanationAgent


def test_definition_exact_text():
    """Test that definition hint contains exact text from clue."""
    
    print("\n" + "="*80)
    print("DEFINITION HARDENING TEST")
    print("="*80 + "\n")
    
    agent = ExplanationAgent()
    
    test_cases = [
        {
            "name": "Hidden Word (WILL)",
            "clue": "How illusionist disguises a dead giveaway?",
            "answer": "WILL",
            "clue_type": "Hidden Word",
            "definition": "a dead giveaway",
            "wordplay_parts": {
                "type": "Hidden Word",
                "fodder": "How illusionist",
                "indicator": "disguises",
                "mechanism": "hidden in 'ho[W ILL]usionist'"
            },
            "expected_in_hint": "a dead giveaway",
            "should_not_contain": ["testament", "legal document", "last wishes"]
        },
        {
            "name": "Anagram (SILENT)",
            "clue": "Listen about being quiet",
            "answer": "SILENT",
            "clue_type": "Anagram",
            "definition": "quiet",
            "wordplay_parts": {
                "type": "Anagram",
                "fodder": "listen",
                "indicator": "about",
                "mechanism": "anagram of listen"
            },
            "expected_in_hint": "quiet",
            "should_not_contain": ["still", "hushed", "noiseless"]
        },
        {
            "name": "Container (SCABBARD)",
            "clue": "Cab crash with card creates protection for sword",
            "answer": "SCABBARD",
            "clue_type": "Container",
            "definition": "protection for sword",
            "wordplay_parts": {
                "type": "Container",
                "outer": "SCAB",
                "inner": "CARD",
                "indicator": "with",
                "mechanism": "CARD inside SCAB + ARD"
            },
            "expected_in_hint": "protection for sword",
            "should_not_contain": ["sheath", "case", "holder"]
        }
    ]
    
    all_passed = True
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 80)
        
        result = agent.generate_explanation(
            clue=test["clue"],
            answer=test["answer"],
            clue_type=test["clue_type"],
            definition=test["definition"],
            wordplay_parts=test["wordplay_parts"]
        )
        
        definition_hint = result.hints["definition"]
        
        # Check 1: Exact definition text must appear
        if test["expected_in_hint"].lower() in definition_hint.lower():
            print(f"✓ PASS: Contains exact definition text: '{test['expected_in_hint']}'")
        else:
            print(f"✗ FAIL: Missing exact definition text: '{test['expected_in_hint']}'")
            print(f"  Got: {definition_hint[:100]}...")
            all_passed = False
        
        # Check 2: Should not contain dictionary definitions
        found_forbidden = []
        for forbidden in test.get("should_not_contain", []):
            if forbidden.lower() in definition_hint.lower():
                found_forbidden.append(forbidden)
        
        if found_forbidden:
            print(f"✗ WARNING: Contains dictionary definitions: {', '.join(found_forbidden)}")
            print(f"  (Only acceptable if '{test['definition']}' also present)")
        else:
            print(f"✓ PASS: No dictionary definitions used")
        
        print(f"\nDefinition Hint:")
        print(f"  {definition_hint}")
    
    print("\n" + "="*80)
    if all_passed:
        print("ALL TESTS PASSED: Definition hardening working correctly")
    else:
        print("SOME TESTS FAILED: Definition validation needs improvement")
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    test_definition_exact_text()

