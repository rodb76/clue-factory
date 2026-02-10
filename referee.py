"""
Referee: Compares Setter's intended answer with Solver's solution.

This module implements the "Referee" component that judges whether a clue
passes or fails the adversarial test by comparing the original answer with
the solver's proposed solution.
"""

import logging
from typing import Dict, Tuple
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RefereeResult:
    """Result of a referee judgment."""
    
    def __init__(
        self, 
        passed: bool, 
        original_answer: str,
        solver_answer: str,
        similarity: float,
        feedback: str = "",
        solver_reasoning: str = ""
    ):
        self.passed = passed
        self.original_answer = original_answer
        self.solver_answer = solver_answer
        self.similarity = similarity
        self.feedback = feedback
        self.solver_reasoning = solver_reasoning
    
    def __bool__(self):
        return self.passed
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary."""
        return {
            "passed": self.passed,
            "original_answer": self.original_answer,
            "solver_answer": self.solver_answer,
            "similarity": self.similarity,
            "feedback": self.feedback,
            "solver_reasoning": self.solver_reasoning
        }
    
    def __repr__(self):
        status = "PASSED" if self.passed else "FAILED"
        return f"RefereeResult({status}: {self.original_answer} vs {self.solver_answer})"


def normalize_answer(answer: str) -> str:
    """
    Normalize an answer for comparison.
    
    Args:
        answer: The answer to normalize.
    
    Returns:
        Normalized answer (uppercase, no spaces/punctuation).
    """
    import re
    return re.sub(r'[^A-Z]', '', answer.upper())


def calculate_similarity(str1: str, str2: str) -> float:
    """
    Calculate similarity ratio between two strings.
    
    Args:
        str1: First string.
        str2: Second string.
    
    Returns:
        Similarity ratio (0.0 to 1.0).
    """
    return SequenceMatcher(None, str1, str2).ratio()


def referee(
    original_answer: str,
    solver_answer: str,
    solver_reasoning: str = "",
    strict: bool = True
) -> RefereeResult:
    """
    Compare the original answer with the solver's solution.
    
    Args:
        original_answer: The answer the Setter intended.
        solver_answer: The answer the Solver proposed.
        solver_reasoning: The Solver's reasoning process.
        strict: If True, requires exact match. If False, allows high similarity.
    
    Returns:
        RefereeResult indicating pass/fail with detailed feedback.
    """
    
    # Normalize both answers
    norm_original = normalize_answer(original_answer)
    norm_solver = normalize_answer(solver_answer)
    
    # Calculate similarity
    similarity = calculate_similarity(norm_original, norm_solver)
    
    logger.info(f"Refereeing: '{original_answer}' vs '{solver_answer}' (similarity: {similarity:.2%})")
    
    # Exact match
    if norm_original == norm_solver:
        logger.info(f"✓ PASSED: Exact match")
        return RefereeResult(
            passed=True,
            original_answer=original_answer,
            solver_answer=solver_answer,
            similarity=1.0,
            feedback="Exact match: Solver correctly identified the answer.",
            solver_reasoning=solver_reasoning
        )
    
    # Close match (only if not strict)
    if not strict and similarity >= 0.8:
        logger.warning(f"⚠ PASSED (with warning): High similarity ({similarity:.2%})")
        return RefereeResult(
            passed=True,
            original_answer=original_answer,
            solver_answer=solver_answer,
            similarity=similarity,
            feedback=f"Close match: Solver proposed '{solver_answer}' vs expected '{original_answer}' (similarity: {similarity:.2%})",
            solver_reasoning=solver_reasoning
        )
    
    # No match
    logger.error(f"✗ FAILED: Solver found '{solver_answer}' instead of '{original_answer}'")
    
    # Provide diagnostic feedback
    feedback_parts = [
        f"Mismatch: Expected '{original_answer}' but solver found '{solver_answer}'."
    ]
    
    # Length comparison
    if len(norm_original) != len(norm_solver):
        feedback_parts.append(
            f"Length mismatch: Expected {len(norm_original)} letters, got {len(norm_solver)} letters."
        )
    
    # Similarity feedback
    if similarity > 0.5:
        feedback_parts.append(
            f"Answers are {similarity:.1%} similar - may indicate ambiguous clue or alternative valid answer."
        )
    elif similarity > 0.3:
        feedback_parts.append(
            f"Some similarity ({similarity:.1%}) - solver may have partially understood the clue."
        )
    else:
        feedback_parts.append(
            f"Low similarity ({similarity:.1%}) - solver likely misidentified the definition or wordplay."
        )
    
    feedback = " ".join(feedback_parts)
    
    return RefereeResult(
        passed=False,
        original_answer=original_answer,
        solver_answer=solver_answer,
        similarity=similarity,
        feedback=feedback,
        solver_reasoning=solver_reasoning
    )


def referee_with_validation(
    clue_json: Dict,
    solution_json: Dict,
    strict: bool = True
) -> RefereeResult:
    """
    Referee a clue with full context from both Setter and Solver.
    
    Args:
        clue_json: The clue JSON from Setter Agent (includes answer).
        solution_json: The solution JSON from Solver Agent (includes proposed answer).
        strict: If True, requires exact match.
    
    Returns:
        RefereeResult with comprehensive feedback.
    """
    original_answer = clue_json.get("answer", "")
    solver_answer = solution_json.get("answer", "")
    solver_reasoning = solution_json.get("reasoning", "")
    
    if not original_answer:
        logger.error("No original answer provided in clue_json")
        return RefereeResult(
            passed=False,
            original_answer="UNKNOWN",
            solver_answer=solver_answer,
            similarity=0.0,
            feedback="Error: No original answer provided for comparison",
            solver_reasoning=solver_reasoning
        )
    
    if not solver_answer:
        logger.error("Solver failed to provide an answer")
        return RefereeResult(
            passed=False,
            original_answer=original_answer,
            solver_answer="NO_ANSWER",
            similarity=0.0,
            feedback="Error: Solver failed to provide an answer",
            solver_reasoning=solver_reasoning
        )
    
    return referee(original_answer, solver_answer, solver_reasoning, strict)


def main():
    """Example usage of the Referee."""
    
    print("\n" + "="*80)
    print("REFEREE: Adversarial Clue Judgment System")
    print("="*80 + "\n")
    
    # Test cases
    test_cases = [
        ("SILENT", "SILENT", "Exact match"),
        ("LISTEN", "LISTEN", "Exact match"),
        ("PARTRIDGE", "PARTRIDGE", "Exact match"),
        ("SILENT", "LISTEN", "Anagram confusion"),
        ("STAR", "RATS", "Reversal error"),
        ("PAINT", "PANT", "Close but wrong"),
        ("LISTEN", "HEARING", "Wrong answer, right meaning"),
    ]
    
    for original, solver, description in test_cases:
        print(f"Test: {description}")
        print(f"  Original: {original}")
        print(f"  Solver:   {solver}")
        
        result = referee(original, solver, "Example reasoning...", strict=True)
        
        status = "✓ PASSED" if result.passed else "✗ FAILED"
        print(f"  Result: {status} (similarity: {result.similarity:.1%})")
        print(f"  Feedback: {result.feedback}")
        print()
    
    print("="*80)


if __name__ == "__main__":
    main()
