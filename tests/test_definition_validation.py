import test_config
"""
Test Definition Validation Logic.

Simulates a scenario where the LLM doesn't follow instructions
to verify the validation catches and corrects it.
"""

import json
from explanation_agent import ExplanationAgent, ExplanationResult


def test_validation_catches_missing_definition():
    """Test that validation catches and corrects missing exact definition text."""
    
    print("\n" + "="*80)
    print("DEFINITION VALIDATION TEST (Simulated Bad Response)")
    print("="*80 + "\n")
    
    # Test Case: Simulate LLM response that doesn't include exact definition
    definition = "a dead giveaway"
    
    # Simulate a bad hint that uses dictionary definition instead of exact text
    bad_hint = "The answer will be a legal document that distributes assets after death."
    
    print(f"Expected definition text: '{definition}'")
    print(f"Bad hint (missing exact text): '{bad_hint}'")
    print()
    
    # Check validation logic
    if definition.lower() not in bad_hint.lower():
        print("✓ Validation detects missing exact definition text")
        
        # Simulate correction
        corrected_hint = f"Our definition here is '{definition}'. " + bad_hint
        print(f"\nCorrected hint:")
        print(f"  {corrected_hint}")
        
        # Verify correction
        if definition.lower() in corrected_hint.lower():
            print("\n✓ PASS: Correction successfully adds exact definition text")
        else:
            print("\n✗ FAIL: Correction didn't work")
    else:
        print("✗ FAIL: Validation didn't detect missing definition")
    
    print("\n" + "="*80)
    print("Now testing with real ExplanationAgent...")
    print("="*80 + "\n")
    
    # Create a result that's expected to fail initial validation
    # (but should get corrected automatically)
    agent = ExplanationAgent()
    
    # Test with a challenging clue
    result = agent.generate_explanation(
        clue="Sword holder cab crashed with card",
        answer="SCABBARD",
        clue_type="Container",
        definition="Sword holder",
        wordplay_parts={
            "type": "Container",
            "outer": "SCAB",
            "inner": "CARD",
            "indicator": "with",
            "mechanism": "CARD inside SCAB"
        }
    )
    
    definition_hint = result.hints["definition"]
    
    print("Generated definition hint:")
    print(f"  {definition_hint}")
    print()
    
    if "sword holder" in definition_hint.lower():
        print("✓ PASS: Exact definition text 'Sword holder' is present")
    else:
        print("✗ FAIL: Exact definition text 'Sword holder' is missing")
        print("  This should have been caught by validation!")
    
    # Check for common dictionary definitions that shouldn't appear alone
    forbidden = ["sheath", "scabbard", "case"]
    found = [word for word in forbidden if word in definition_hint.lower() and "sword holder" not in definition_hint.lower()]
    
    if found:
        print(f"✗ FAIL: Contains only dictionary definitions: {found}")
    else:
        print("✓ PASS: No isolated dictionary definitions")
    
    print("\n" + "="*80)
    print("VALIDATION TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_validation_catches_missing_definition()

