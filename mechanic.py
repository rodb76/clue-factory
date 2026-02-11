"""
Mechanic: Mechanical validators for cryptic clue types.

This module implements string-based validation functions for cryptic clue types
that can be verified programmatically without requiring LLM reasoning.
"""

import logging
import re
from typing import Dict, Tuple, Optional

# Configure logging
# Note: logging.basicConfig() should only be called in the main entry point (main.py)
# to avoid duplicate handlers when modules are imported
logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of a clue validation check."""
    
    def __init__(self, is_valid: bool, message: str = "", details: Optional[Dict] = None):
        self.is_valid = is_valid
        self.message = message
        self.details = details or {}
    
    def __bool__(self):
        return self.is_valid
    
    def __repr__(self):
        return f"ValidationResult(valid={self.is_valid}, message='{self.message}')"


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by removing spaces, punctuation, and converting to lowercase.
    
    Args:
        text: The text to normalize.
    
    Returns:
        Normalized text with only letters, lowercase.
    """
    # Remove everything except letters and convert to lowercase
    return re.sub(r'[^a-zA-Z]', '', text).lower()


def validate_length(answer: str, enumeration: Optional[str] = None) -> ValidationResult:
    """
    Validate that the answer length matches the provided enumeration.
    
    Args:
        answer: The answer word/phrase.
        enumeration: Optional enumeration like "(6)" or "(3,4)" or "(2-5)".
    
    Returns:
        ValidationResult indicating if length matches.
    """
    if not enumeration:
        return ValidationResult(True, "No enumeration provided to check")
    
    # Extract numbers from enumeration
    numbers = re.findall(r'\d+', enumeration)
    if not numbers:
        return ValidationResult(False, f"Invalid enumeration format: {enumeration}")
    
    # Calculate expected length
    expected_length = sum(int(n) for n in numbers)
    actual_length = len(normalize_text(answer))
    
    if actual_length == expected_length:
        return ValidationResult(True, f"Length matches: {actual_length}")
    else:
        return ValidationResult(
            False, 
            f"Length mismatch: expected {expected_length}, got {actual_length}",
            {"expected": expected_length, "actual": actual_length}
        )


def validate_anagram(fodder: str, answer: str) -> ValidationResult:
    """
    Validate that the fodder is a valid anagram of the answer.
    
    Args:
        fodder: The letters to be rearranged.
        answer: The target answer.
    
    Returns:
        ValidationResult indicating if fodder is an anagram of answer.
    """
    normalized_fodder = normalize_text(fodder)
    normalized_answer = normalize_text(answer)
    
    if sorted(normalized_fodder) == sorted(normalized_answer):
        return ValidationResult(
            True, 
            f"Valid anagram: '{fodder}' → '{answer}'",
            {"fodder": normalized_fodder, "answer": normalized_answer}
        )
    else:
        # Provide detailed feedback
        fodder_letters = sorted(normalized_fodder)
        answer_letters = sorted(normalized_answer)
        return ValidationResult(
            False,
            f"Invalid anagram: '{fodder}' does not rearrange to '{answer}'",
            {
                "fodder_letters": fodder_letters,
                "answer_letters": answer_letters,
                "fodder_sorted": ''.join(fodder_letters),
                "answer_sorted": ''.join(answer_letters)
            }
        )


def validate_hidden_word(fodder: str, answer: str) -> ValidationResult:
    """
    Validate that the answer is hidden within the fodder string.
    
    Args:
        fodder: The text containing the hidden word.
        answer: The target answer.
    
    Returns:
        ValidationResult indicating if answer is hidden in fodder.
    """
    normalized_fodder = normalize_text(fodder)
    normalized_answer = normalize_text(answer)
    
    if normalized_answer in normalized_fodder:
        # Find the position for detailed feedback
        start_pos = normalized_fodder.index(normalized_answer)
        end_pos = start_pos + len(normalized_answer)
        
        return ValidationResult(
            True,
            f"Valid hidden word: '{answer}' found in '{fodder}'",
            {
                "position": (start_pos, end_pos),
                "before": normalized_fodder[:start_pos],
                "hidden": normalized_answer,
                "after": normalized_fodder[end_pos:]
            }
        )
    else:
        return ValidationResult(
            False,
            f"Invalid hidden word: '{answer}' not found in '{fodder}'",
            {"fodder": normalized_fodder, "answer": normalized_answer}
        )


def validate_charade(parts: list, answer: str) -> ValidationResult:
    """
    Validate that concatenating the parts produces the answer.
    
    Args:
        parts: List of word parts to concatenate (e.g., ["PART", "RIDGE"]).
        answer: The target answer.
    
    Returns:
        ValidationResult indicating if parts concatenate to answer.
    """
    if not parts:
        return ValidationResult(False, "No parts provided for charade")
    
    # Normalize all parts and concatenate
    normalized_parts = [normalize_text(part) for part in parts]
    concatenated = ''.join(normalized_parts)
    normalized_answer = normalize_text(answer)
    
    if concatenated == normalized_answer:
        return ValidationResult(
            True,
            f"Valid charade: {' + '.join(parts)} = '{answer}'",
            {"parts": normalized_parts, "concatenated": concatenated}
        )
    else:
        return ValidationResult(
            False,
            f"Invalid charade: {' + '.join(parts)} ≠ '{answer}'",
            {
                "parts": normalized_parts,
                "concatenated": concatenated,
                "expected": normalized_answer
            }
        )


def validate_container(outer: str, inner: str, answer: str, position: Optional[int] = None) -> ValidationResult:
    """
    Validate that placing inner word inside outer word produces the answer.
    
    Args:
        outer: The outer word/container.
        inner: The inner word to be inserted.
        answer: The target answer.
        position: Optional position where inner is inserted (0-indexed).
    
    Returns:
        ValidationResult indicating if the container construction is valid.
    """
    normalized_outer = normalize_text(outer)
    normalized_inner = normalize_text(inner)
    normalized_answer = normalize_text(answer)
    
    # Try all possible positions if not specified
    if position is not None:
        positions_to_try = [position]
    else:
        positions_to_try = range(len(normalized_outer) + 1)
    
    for pos in positions_to_try:
        result = normalized_outer[:pos] + normalized_inner + normalized_outer[pos:]
        if result == normalized_answer:
            return ValidationResult(
                True,
                f"Valid container: '{inner}' in '{outer}' at position {pos} = '{answer}'",
                {
                    "outer": normalized_outer,
                    "inner": normalized_inner,
                    "position": pos,
                    "result": result
                }
            )
    
    return ValidationResult(
        False,
        f"Invalid container: '{inner}' in '{outer}' does not produce '{answer}'",
        {
            "outer": normalized_outer,
            "inner": normalized_inner,
            "expected": normalized_answer
        }
    )


def validate_reversal(word: str, answer: str) -> ValidationResult:
    """
    Validate that reversing the word produces the answer.
    
    Args:
        word: The word to be reversed.
        answer: The target answer.
    
    Returns:
        ValidationResult indicating if the reversal is valid.
    """
    normalized_word = normalize_text(word)
    normalized_answer = normalize_text(answer)
    reversed_word = normalized_word[::-1]
    
    if reversed_word == normalized_answer:
        return ValidationResult(
            True,
            f"Valid reversal: '{word}' reversed = '{answer}'",
            {"word": normalized_word, "reversed": reversed_word}
        )
    else:
        return ValidationResult(
            False,
            f"Invalid reversal: '{word}' reversed ('{reversed_word}') ≠ '{answer}'",
            {
                "word": normalized_word,
                "reversed": reversed_word,
                "expected": normalized_answer
            }
        )


def validate_clue(clue_json: Dict) -> ValidationResult:
    """
    Main validation function that routes to the appropriate validator.
    
    Args:
        clue_json: The clue JSON object from the Setter Agent.
    
    Returns:
        ValidationResult with validation status and details.
    """
    clue_type = clue_json.get('type', '').lower()
    answer = clue_json.get('answer', '')
    wordplay_parts = clue_json.get('wordplay_parts', {})
    
    if not answer:
        return ValidationResult(False, "No answer provided in clue JSON")
    
    logger.info(f"Validating {clue_type} clue for answer: {answer}")
    
    # Route to appropriate validator
    if clue_type == 'anagram':
        fodder = wordplay_parts.get('fodder', '')
        if not fodder:
            return ValidationResult(False, "No fodder provided for anagram")
        result = validate_anagram(fodder, answer)
        
    elif clue_type == 'hidden word':
        fodder = wordplay_parts.get('fodder', '')
        if not fodder:
            return ValidationResult(False, "No fodder provided for hidden word")
        result = validate_hidden_word(fodder, answer)
        
    elif clue_type == 'charades' or clue_type == 'charade':
        # Try to extract parts from wordplay_parts
        parts = wordplay_parts.get('parts', [])
        if not parts and 'fodder' in wordplay_parts:
            # Fallback: split fodder by common separators
            parts = re.split(r'[+\s]+', wordplay_parts['fodder'])
        if not parts:
            return ValidationResult(False, "No parts provided for charade")
        result = validate_charade(parts, answer)
        
    elif clue_type in ['container', 'containers', 'inclusion', 'inclusions']:
        outer = wordplay_parts.get('outer', '')
        inner = wordplay_parts.get('inner', '')
        if not outer or not inner:
            return ValidationResult(False, "Missing 'outer' or 'inner' for container")
        result = validate_container(outer, inner, answer)
        
    elif clue_type == 'reversal' or clue_type == 'reversals':
        word = wordplay_parts.get('word', '') or wordplay_parts.get('fodder', '')
        if not word:
            return ValidationResult(False, "No word provided for reversal")
        result = validate_reversal(word, answer)
        
    elif clue_type in ['homophone', 'homophones']:
        logger.warning(f"Homophone validation requires LLM reasoning (sound-alike check)")
        return ValidationResult(
            True, 
            "Homophone: Mechanical validation skipped (requires audio/phonetic reasoning)",
            {"requires_llm": True}
        )
        
    elif clue_type in ['double definition', 'double definitions']:
        logger.warning(f"Double definition validation requires LLM reasoning")
        return ValidationResult(
            True,
            "Double Definition: Mechanical validation skipped (requires semantic reasoning)",
            {"requires_llm": True}
        )
        
    elif clue_type == '&lit' or clue_type == 'all-in-one':
        logger.warning(f"&lit validation requires LLM reasoning")
        return ValidationResult(
            True,
            "&lit: Mechanical validation skipped (requires holistic reasoning)",
            {"requires_llm": True}
        )
        
    else:
        return ValidationResult(
            False,
            f"Unknown clue type: '{clue_type}'",
            {"supported_types": [
                "anagram", "hidden word", "charade", "container", 
                "reversal", "homophone", "double definition", "&lit"
            ]}
        )
    
    # Log result
    if result.is_valid:
        logger.info(f"✓ Validation passed: {result.message}")
    else:
        logger.error(f"✗ Validation failed: {result.message}")
    
    return result


def validate_clue_complete(clue_json: Dict, enumeration: Optional[str] = None) -> Tuple[bool, Dict]:
    """
    Complete validation including length check and wordplay validation.
    
    Args:
        clue_json: The clue JSON object from the Setter Agent.
        enumeration: Optional enumeration to validate length.
    
    Returns:
        Tuple of (all_valid, results_dict) where results_dict contains all validation results.
    """
    answer = clue_json.get('answer', '')
    results = {}
    
    # 1. Length validation
    if enumeration:
        length_result = validate_length(answer, enumeration)
        results['length'] = length_result
    
    # 2. Wordplay validation
    wordplay_result = validate_clue(clue_json)
    results['wordplay'] = wordplay_result
    
    # Overall validity
    all_valid = all(r.is_valid for r in results.values())
    
    return all_valid, results


def main():
    """Example usage of the mechanic validators."""
    
    # Test cases
    test_cases = [
        {
            "name": "Anagram Test",
            "clue": {
                "answer": "SILENT",
                "type": "Anagram",
                "wordplay_parts": {"fodder": "listen"}
            },
            "enumeration": "(6)"
        },
        {
            "name": "Hidden Word Test",
            "clue": {
                "answer": "LISTEN",
                "type": "Hidden Word",
                "wordplay_parts": {"fodder": "tales Tennessee"}
            },
            "enumeration": "(6)"
        },
        {
            "name": "Charade Test",
            "clue": {
                "answer": "PARTRIDGE",
                "type": "Charade",
                "wordplay_parts": {"parts": ["PART", "RIDGE"]}
            },
            "enumeration": "(9)"
        },
        {
            "name": "Container Test",
            "clue": {
                "answer": "PAINT",
                "type": "Container",
                "wordplay_parts": {"outer": "PAT", "inner": "IN"}
            },
            "enumeration": "(5)"
        },
        {
            "name": "Reversal Test",
            "clue": {
                "answer": "STAR",
                "type": "Reversal",
                "wordplay_parts": {"word": "RATS"}
            },
            "enumeration": "(4)"
        }
    ]
    
    print("\n" + "="*80)
    print("MECHANIC: Cryptic Clue Validator Test Suite")
    print("="*80 + "\n")
    
    for test in test_cases:
        print(f"Testing: {test['name']}")
        print(f"  Answer: {test['clue']['answer']}")
        print(f"  Type: {test['clue']['type']}")
        
        all_valid, results = validate_clue_complete(test['clue'], test['enumeration'])
        
        for check_name, result in results.items():
            status = "✓" if result.is_valid else "✗"
            print(f"  {status} {check_name.capitalize()}: {result.message}")
        
        print()
    
    print("="*80)


if __name__ == "__main__":
    main()
