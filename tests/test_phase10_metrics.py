"""
Test suite for Phase 10: Advanced Metrics (Ximenean, Difficulty, Narrative).

Tests the new quantitative scoring system.
"""

import test_config
from auditor import XimeneanAuditor


def test_ximenean_score_perfect_clue():
    """Test Ximenean score for a perfect clue (no penalties)."""
    auditor = XimeneanAuditor()
    
    # Perfect clue: minimal, good grammar, proper fodder
    clue = {
        "clue": "Home game contains final Greek letter",
        "definition": "final Greek letter",
        "answer": "OMEGA",
        "type": "Hidden",
        "wordplay_parts": {
            "fodder": "HOME GAME",
            "indicator": "contains",
            "mechanism": "hidden in HOME GAME"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 1: Ximenean Score - Perfect Clue")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nXimenean Score: {result.ximenean_score:.2f} / 1.00")
    print(f"Fairness Score: {result.fairness_score:.1%}")
    print(f"Expected: 1.00 (perfect compliance)")
    
    assert result.ximenean_score >= 0.95, "Perfect clue should have ximenean score >= 0.95"


def test_difficulty_level_simple():
    """Test difficulty rating for a simple clue."""
    auditor = XimeneanAuditor()
    
    # Simple hidden word clue
    clue = {
        "clue": "Match found in game at chess",
        "definition": "match",
        "answer": "MATCH",
        "type": "Hidden",
        "wordplay_parts": {
            "fodder": "GAME AT CH",
            "indicator": "found in",
            "mechanism": "hidden in GAME AT CH"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 2: Difficulty Level - Simple Clue")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"Type: {clue['type']}")
    print(f"\nDifficulty Level: {result.difficulty_level} / 5")
    print(f"Expected: 1-2 (Direct/Moderate)")
    
    assert result.difficulty_level <= 2, "Simple hidden word should be difficulty 1-2"


def test_difficulty_level_complex():
    """Test difficulty rating for a complex clue."""
    auditor = XimeneanAuditor()
    
    # Complex charade with multiple abbreviations
    clue = {
        "clue": "One doctor and three knights unite for military force",
        "definition": "military force",
        "answer": "IDRNNN",  # Made up
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "I + DR + N + N + N",
            "indicator": "and",
            "mechanism": "I (one) + DR (doctor) + N (knight) + N (knight) + N (knight)"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 3: Difficulty Level - Complex Clue")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"Type: {clue['type']}")
    print(f"Fodder Parts: {clue['wordplay_parts']['fodder']}")
    print(f"\nDifficulty Level: {result.difficulty_level} / 5")
    print(f"Expected: 3-5 (Intermediate/Advanced/Master)")
    
    assert result.difficulty_level >= 3, "Complex charade should be difficulty 3+"


def test_narrative_fidelity_natural():
    """Test narrative fidelity for a natural-sounding clue."""
    auditor = XimeneanAuditor()
    
    # Clean, natural clue
    clue = {
        "clue": "Final Greek letter found in home game",
        "definition": "final Greek letter",
        "answer": "OMEGA",
        "type": "Hidden",
        "wordplay_parts": {
            "fodder": "HOME GAME",
            "indicator": "found in",
            "mechanism": "hidden in HOME GAME"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 4: Narrative Fidelity - Natural Clue")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nNarrative Fidelity: {result.narrative_fidelity:.1f}%")
    print(f"Expected: 90-105% (natural sentence)")
    
    assert result.narrative_fidelity >= 90.0, "Natural clue should have narrative fidelity >= 90%"


def test_narrative_fidelity_mechanical():
    """Test narrative fidelity for a mechanical-looking clue."""
    auditor = XimeneanAuditor()
    
    # Mechanical clue with literal listing
    clue = {
        "clue": "Earnest request with en, treat, y for unknown",
        "definition": "earnest request",
        "answer": "ENTREATY",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "EN + TREAT + Y",
            "indicator": "with",
            "mechanism": "EN + TREAT + Y"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 5: Narrative Fidelity - Mechanical Clue")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\nNarrative Fidelity: {result.narrative_fidelity:.1f}%")
    print(f"Expected: <80% (visible mechanics)")
    
    assert result.narrative_fidelity < 80.0, "Mechanical clue should have narrative fidelity < 80%"


def test_all_metrics_integration():
    """Test that all three metrics are calculated and logged."""
    auditor = XimeneanAuditor()
    
    clue = {
        "clue": "Rough we hear from course",
        "definition": "rough",
        "answer": "COARSE",
        "type": "Homophone",
        "wordplay_parts": {
            "fodder": "course",
            "indicator": "we hear",
            "mechanism": "sounds like COURSE"
        }
    }
    
    result = auditor.audit_clue(clue)
    
    print("\n" + "="*70)
    print("TEST 6: All Metrics Integration")
    print("="*70)
    print(f"Clue: '{clue['clue']}'")
    print(f"Answer: {clue['answer']}")
    print(f"\n=== METRICS ===")
    print(f"Fairness Score:      {result.fairness_score:.1%}")
    print(f"Ximenean Score:      {result.ximenean_score:.2f} / 1.00")
    print(f"Difficulty Level:    {result.difficulty_level} / 5")
    print(f"Narrative Fidelity:  {result.narrative_fidelity:.1f}%")
    
    # Verify all metrics are present
    assert hasattr(result, 'ximenean_score')
    assert hasattr(result, 'difficulty_level')
    assert hasattr(result, 'narrative_fidelity')
    
    # Verify metrics are in valid ranges
    assert 0.0 <= result.ximenean_score <= 1.0
    assert 1 <= result.difficulty_level <= 5
    assert 0.0 <= result.narrative_fidelity <= 105.0  # Allow bonus
    
    # Verify metrics are in to_dict output
    result_dict = result.to_dict()
    assert 'ximenean_score' in result_dict
    assert 'difficulty_level' in result_dict
    assert 'narrative_fidelity' in result_dict


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 10: ADVANCED METRICS TEST SUITE")
    print("Testing Ximenean Score, Difficulty Level, and Narrative Fidelity")
    print("="*70)
    
    test_ximenean_score_perfect_clue()
    test_difficulty_level_simple()
    test_difficulty_level_complex()
    test_narrative_fidelity_natural()
    test_narrative_fidelity_mechanical()
    test_all_metrics_integration()
    
    print("\n" + "="*70)
    print("ALL PHASE 10 METRICS TESTS COMPLETED")
    print("="*70)
