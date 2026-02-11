"""
Test Workshop Agent with various quality levels.

This test creates mock clues with different quality scores to verify
that the workshop agent correctly:
1. Keeps excellent clues as-is
2. Suggests alternative mechanisms for low-quality clues
3. Suggests word swaps for good surfaces with suboptimal words
"""
import sys
import os
import json
import tempfile

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workshop import WorkshopAgent


def create_test_clues():
    """Create test clues with various quality levels."""
    return {
        "metadata": {
            "generated_at": "2026-02-11T00:00:00",
            "target_count": 4,
            "total_attempts": 4,
            "success_rate": "100%",
            "total_time_seconds": 100.0,
            "batches_processed": 1
        },
        "clues": [
            # Test 1: Excellent quality - should keep as is
            {
                "word": "REGAL",
                "clue_type": "Reversal",
                "clue": "Majestic lager returned",
                "definition": "Majestic",
                "wordplay_parts": {
                    "fodder": "lager",
                    "indicator": "returned",
                    "mechanism": "reverse of lager"
                },
                "audit": {
                    "passed": True,
                    "narrative_fidelity": 100.0,
                    "ximenean_score": 1.0,
                    "narrative_integrity_check": True,
                    "filler_check": True,
                    "indicator_grammar_check": True
                }
            },
            # Test 2: Low narrative fidelity - should suggest alternative mechanism
            {
                "word": "LISTEN",
                "clue_type": "Charade",
                "clue": "Hear with L, I, S, T, E, N",
                "definition": "Hear",
                "wordplay_parts": {
                    "fodder": "L + I + S + T + E + N",
                    "indicator": "with",
                    "mechanism": "L + I + S + T + E + N"
                },
                "audit": {
                    "passed": False,
                    "narrative_fidelity": 40.0,
                    "ximenean_score": 0.5,
                    "narrative_integrity_check": False,
                    "narrative_integrity_feedback": "[FAIL] Literal letter listing detected",
                    "filler_check": True,
                    "indicator_grammar_check": True
                }
            },
            # Test 3: Low ximenean score - should suggest alternative mechanism
            {
                "word": "SILENT",
                "clue_type": "Anagram",
                "clue": "Quiet for listening mixed up badly wrongly",
                "definition": "Quiet",
                "wordplay_parts": {
                    "fodder": "listen",
                    "indicator": "mixed up",
                    "mechanism": "anagram of listen"
                },
                "audit": {
                    "passed": False,
                    "narrative_fidelity": 85.0,
                    "ximenean_score": 0.6,
                    "narrative_integrity_check": True,
                    "filler_check": False,
                    "filler_feedback": "[FAIL] Too many filler words",
                    "indicator_grammar_check": True
                }
            },
            # Test 4: Good narrative but marginal scores - might suggest word swap
            {
                "word": "ASTHMA",
                "clue_type": "Anagram",
                "clue": "Breathing condition from maths mixed",
                "definition": "Breathing condition",
                "wordplay_parts": {
                    "fodder": "maths",
                    "indicator": "mixed",
                    "mechanism": "anagram of maths + a"
                },
                "audit": {
                    "passed": True,
                    "narrative_fidelity": 85.0,
                    "ximenean_score": 0.85,
                    "narrative_integrity_check": True,
                    "filler_check": True,
                    "indicator_grammar_check": True
                }
            }
        ]
    }


def test_workshop_agent():
    """Test the workshop agent with various quality clues."""
    
    print("\n" + "="*70)
    print("TESTING WORKSHOP AGENT")
    print("="*70 + "\n")
    
    # Create temporary test files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as input_file:
        test_data = create_test_clues()
        json.dump(test_data, input_file, indent=2)
        input_path = input_file.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as output_file:
        output_path = output_file.name
    
    try:
        # Initialize workshop agent
        workshop = WorkshopAgent(timeout=60.0)
        
        # Process test clues
        results = workshop.workshop_batch(
            input_file=input_path,
            output_file=output_path
        )
        
        # Verify results
        print("\n" + "="*70)
        print("VERIFICATION")
        print("="*70 + "\n")
        
        suggestions = results.get("suggestions", [])
        
        # Test 1: Excellent clue should be kept
        test1 = suggestions[0]
        assert test1["suggestion_type"] == "keep_as_is", \
            f"Test 1 failed: Expected 'keep_as_is', got '{test1['suggestion_type']}'"
        print("✓ Test 1 PASSED: Excellent clue kept as-is")
        
        # Test 2: Low narrative fidelity should suggest alternative
        test2 = suggestions[1]
        assert test2["suggestion_type"] == "alternative_mechanism", \
            f"Test 2 failed: Expected 'alternative_mechanism', got '{test2['suggestion_type']}'"
        print("✓ Test 2 PASSED: Low narrative score → alternative mechanism suggested")
        if test2.get("alternative_mechanism"):
            print(f"  Suggested: {test2['alternative_mechanism'].get('type', 'N/A')}")
        
        # Test 3: Low ximenean score should suggest alternative
        test3 = suggestions[2]
        assert test3["suggestion_type"] == "alternative_mechanism", \
            f"Test 3 failed: Expected 'alternative_mechanism', got '{test3['suggestion_type']}'"
        print("✓ Test 3 PASSED: Low ximenean score → alternative mechanism suggested")
        if test3.get("alternative_mechanism"):
            print(f"  Suggested: {test3['alternative_mechanism'].get('type', 'N/A')}")
        
        # Test 4: Good quality might suggest word swap or keep as is
        test4 = suggestions[3]
        assert test4["suggestion_type"] in ["word_swap", "keep_as_is"], \
            f"Test 4 failed: Expected 'word_swap' or 'keep_as_is', got '{test4['suggestion_type']}'"
        print(f"✓ Test 4 PASSED: Marginal quality → {test4['suggestion_type']}")
        if test4.get("word_swap"):
            print(f"  Suggested word: {test4['word_swap'].get('new_word', 'N/A')}")
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED!")
        print("="*70 + "\n")
        
        # Display statistics
        stats = results["metadata"]["statistics"]
        print("Workshop Statistics:")
        print(f"  Total clues: {stats['total_clues']}")
        print(f"  Kept as-is: {stats['kept_as_is']}")
        print(f"  Alternative mechanism: {stats['alternative_mechanism_suggested']}")
        print(f"  Word swap: {stats['word_swap_suggested']}")
        print(f"  Improvement rate: {stats['improvement_rate']}")
        
    finally:
        # Cleanup temp files
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except:
            pass


if __name__ == "__main__":
    try:
        test_workshop_agent()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
