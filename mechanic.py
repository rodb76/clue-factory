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

# Initialize enchant dictionary for real-word validation
_enchant_dict = None
try:
    import enchant
    try:
        _enchant_dict = enchant.request_dict("en_GB")
        logger.info("Enchant dictionary initialized: en_GB")
    except Exception as e:
        logger.warning(f"Failed to load en_GB dictionary: {e}")
        try:
            _enchant_dict = enchant.request_dict("en_US")
            logger.info("Enchant dictionary initialized: en_US (fallback)")
        except Exception as e2:
            logger.warning(f"Failed to load en_US dictionary: {e2}")
            _enchant_dict = None
except ImportError:
    logger.warning("Enchant library not available - real-word validation will be skipped")
    _enchant_dict = None


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


def check_identity_constraint(fodder: str, answer: str) -> ValidationResult:
    """
    Check that the answer (or common variants) does not appear in the fodder.
    This prevents lazy clues where the answer hides within itself.
    
    Args:
        fodder: The fodder text to check.
        answer: The answer word.
    
    Returns:
        ValidationResult indicating if identity constraint is satisfied.
    """
    normalized_fodder = normalize_text(fodder)
    normalized_answer = normalize_text(answer)
    
    # Check if answer appears in fodder
    if normalized_answer in normalized_fodder:
        return ValidationResult(
            False,
            f"Identity constraint violated: answer '{answer}' appears in fodder '{fodder}'",
            {"fodder": fodder, "answer": answer}
        )
    
    # Check common variants (plural, past tense)
    variants = []
    if len(answer) > 3:
        variants.append(normalized_answer + 's')  # plural
        variants.append(normalized_answer + 'ed')  # past tense
        variants.append(normalized_answer + 'ing')  # present participle
        if normalized_answer.endswith('e'):
            variants.append(normalized_answer[:-1] + 'ed')  # e.g., bake -> baked
            variants.append(normalized_answer[:-1] + 'ing')  # e.g., bake -> baking
    
    for variant in variants:
        if variant in normalized_fodder:
            return ValidationResult(
                False,
                f"Identity constraint violated: answer variant '{variant}' appears in fodder '{fodder}'",
                {"fodder": fodder, "answer": answer, "variant": variant}
            )
    
    return ValidationResult(
        True,
        f"Identity constraint satisfied: answer not in fodder",
        {"fodder": fodder, "answer": answer}
    )


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
    Also checks that all words in the fodder are real English words.
    
    Args:
        fodder: The letters to be rearranged.
        answer: The target answer.
    
    Returns:
        ValidationResult indicating if fodder is an anagram of answer.
    """
    # First check: Identity constraint (answer must not appear in fodder)
    identity_check = check_identity_constraint(fodder, answer)
    if not identity_check.is_valid:
        return identity_check
    
    # Second check: Real-word validation for fodder
    if _enchant_dict:
        # Split fodder into words and validate each
        words = fodder.lower().split()
        # Common cryptic abbreviations that might not be in dictionary
        valid_abbreviations = {'n', 's', 'e', 'w', 'l', 'r', 'u', 'o', 'er', 'ed', 're'}
        
        invalid_words = []
        for word in words:
            # Skip very short words and known abbreviations
            if len(word) <= 2 and word in valid_abbreviations:
                continue
            # Check if word is in dictionary
            if not _enchant_dict.check(word):
                invalid_words.append(word)
        
        if invalid_words:
            return ValidationResult(
                False,
                f"Fodder contains non-dictionary words: {', '.join(invalid_words)}. "
                f"All anagram fodder must use real English words.",
                {"invalid_words": invalid_words, "fodder": fodder}
            )
    
    # Third check: Letter count validation
    normalized_fodder = normalize_text(fodder)
    normalized_answer = normalize_text(answer)
    
    # Strip spaces and check exact letter match
    f_letters = sorted(normalized_fodder)
    a_letters = sorted(normalized_answer)
    
    if f_letters == a_letters:
        return ValidationResult(
            True, 
            f"Valid anagram: '{fodder}' → '{answer}'",
            {"fodder": normalized_fodder, "answer": normalized_answer}
        )
    else:
        # Calculate missing and extra letters for detailed feedback
        from collections import Counter
        fodder_counter = Counter(normalized_fodder)
        answer_counter = Counter(normalized_answer)
        
        missing = []
        extra = []
        
        # Find missing letters (in answer but not in fodder)
        for letter, count in answer_counter.items():
            fodder_count = fodder_counter.get(letter, 0)
            if fodder_count < count:
                missing.extend([letter] * (count - fodder_count))
        
        # Find extra letters (in fodder but not in answer)
        for letter, count in fodder_counter.items():
            answer_count = answer_counter.get(letter, 0)
            if count > answer_count:
                extra.extend([letter] * (count - answer_count))
        
        # Build detailed error message
        error_parts = [f"Invalid anagram: fodder letters do not exactly match answer letters."]
        if missing:
            error_parts.append(f"Missing letters: {', '.join(sorted(missing))}")
        if extra:
            error_parts.append(f"Extra letters: {', '.join(sorted(extra))}")
        
        return ValidationResult(
            False,
            " | ".join(error_parts),
            {
                "fodder_sorted": ''.join(f_letters),
                "answer_sorted": ''.join(a_letters),
                "missing_letters": missing,
                "extra_letters": extra
            }
        )


def validate_hidden_word(fodder: str, answer: str) -> ValidationResult:
    """
    Validate that the answer is hidden within the fodder string.
    Also checks that the answer is concealed across at least two words.
    
    Args:
        fodder: The text containing the hidden word.
        answer: The target answer.
    
    Returns:
        ValidationResult indicating if answer is hidden in fodder.
    """
    # First check: Identity constraint - answer must span multiple words
    fodder_words = fodder.split()
    if len(fodder_words) == 1:
        # Single word fodder - check if it IS the answer
        if normalize_text(fodder) == normalize_text(answer):
            return ValidationResult(
                False,
                f"Identity constraint violated: Hidden word fodder '{fodder}' is the answer itself. "
                f"The answer must be concealed across at least two words.",
                {"fodder": fodder, "answer": answer}
            )
    
    # Second check: Answer appears as a complete standalone word in multi-word fodder
    answer_lower = answer.lower()
    fodder_words_lower = [w.lower() for w in fodder_words]
    if answer_lower in fodder_words_lower:
        return ValidationResult(
            False,
            f"Identity constraint violated: Answer '{answer}' appears as a standalone word in fodder '{fodder}'. "
            f"The answer must be concealed across word boundaries, not present as a complete word.",
            {"fodder": fodder, "answer": answer}
        )
    
    # Third check: Hidden word validation
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
