import test_config
"""
Test ExplanationAgent integration with main pipeline.
"""

import json
from main import ClueResult
from explanation_agent import ExplanationAgent


def test_explanation_integration():
    """Test that ExplanationAgent integrates with ClueResult."""
    
    print("\n" + "="*80)
    print("EXPLANATION AGENT INTEGRATION TEST")
    print("="*80 + "\n")
    
    # Create a mock ClueResult (as if it passed all stages)
    clue_json = {
        "clue": "How illusionist disguises a dead giveaway?",
        "definition": "a dead giveaway",
        "wordplay_parts": {
            "type": "Hidden Word",
            "fodder": "How illusionist",
            "indicator": "disguises",
            "mechanism": "hidden in 'ho[W ILL]usionist'"
        }
    }
    
    result = ClueResult(
        word="WILL",
        clue_type="Hidden Word",
        clue_json=clue_json,
        mechanical_valid=True,
        passed=True
    )
    
    # Generate explanation
    explainer = ExplanationAgent()
    
    explanation = explainer.generate_explanation(
        clue=clue_json["clue"],
        answer="WILL",
        clue_type="Hidden Word",
        definition=clue_json["definition"],
        wordplay_parts=clue_json["wordplay_parts"]
    )
    
    # Add to result
    result.explanation_data = explanation.to_dict()
    
    # Verify it serializes correctly
    output = result.to_dict()
    
    print("ClueResult JSON Output:")
    print("-" * 80)
    print(json.dumps(output, indent=2))
    print()
    
    # Verify structure
    assert "explanation" in output, "Missing explanation field"
    assert "hints" in output["explanation"], "Missing hints"
    assert "full_breakdown" in output["explanation"], "Missing full_breakdown"
    assert "indicators" in output["explanation"]["hints"], "Missing indicators hint"
    assert "fodder" in output["explanation"]["hints"], "Missing fodder hint"
    assert "definition" in output["explanation"]["hints"], "Missing definition hint"
    
    print("✓ All fields present")
    print("✓ Structure validated")
    print("\n" + "="*80)
    print("INTEGRATION TEST PASSED")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_explanation_integration()

