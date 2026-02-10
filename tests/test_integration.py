import test_config
"""
Integration test: Setter Agent + Mechanic Validator

This script demonstrates the complete workflow:
1. Generate a clue using the Setter Agent
2. Validate the clue using the Mechanic
3. Report results
"""

import json
import logging
from setter_agent import SetterAgent
from mechanic import validate_clue_complete, ValidationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_setter_with_validation(answer: str, clue_type: str, enumeration: str = None):
    """
    Generate and validate a clue.
    
    Args:
        answer: The target word.
        clue_type: The type of clue to generate.
        enumeration: Optional enumeration like "(6)".
    """
    print(f"\n{'='*80}")
    print(f"Testing: {answer} ({clue_type})")
    print(f"{'='*80}\n")
    
    try:
        # 1. Generate the clue
        setter = SetterAgent(timeout=45.0)
        clue_json = setter.generate_cryptic_clue(answer, clue_type)
        
        print("Generated Clue:")
        print(f"  Clue: {clue_json['clue']}")
        print(f"  Definition: {clue_json['definition']}")
        print(f"  Type: {clue_json['type']}")
        
        # 2. Validate the clue
        print("\nMechanical Validation:")
        all_valid, results = validate_clue_complete(clue_json, enumeration)
        
        for check_name, result in results.items():
            status = "✓" if result.is_valid else "✗"
            print(f"  {status} {check_name.capitalize()}: {result.message}")
        
        # 3. Summary
        print("\n" + "-"*80)
        if all_valid:
            print("✓ CLUE VALIDATED: All checks passed")
        else:
            print("✗ VALIDATION FAILED: Clue needs revision")
            print("\nWordplay Details:")
            print(json.dumps(clue_json['wordplay_parts'], indent=2))
        print("-"*80)
        
        return all_valid, clue_json
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        print(f"\n✗ Test failed with error: {e}")
        return False, None


def main():
    """Run integration tests."""
    
    print("\n" + "="*80)
    print("INTEGRATION TEST: Setter Agent + Mechanic Validator")
    print("="*80)
    
    # Note: These require API access
    # Uncomment to test with actual API calls
    
    print("\n[INFO] To run live tests with API calls, uncomment test cases in main()")
    print("[INFO] Example tests:")
    print("  - test_setter_with_validation('SILENT', 'Anagram', '(6)')")
    print("  - test_setter_with_validation('STAR', 'Reversal', '(4)')")
    print("  - test_setter_with_validation('STEAL', 'Hidden Word', '(5)')")
    
    # Example: Uncomment to run
    # test_setter_with_validation('SILENT', 'Anagram', '(6)')
    
    print("\n" + "="*80)
    print("For offline testing, see mechanic.py (no API required)")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

