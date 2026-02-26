"""
Auditor: Ximenean Quality and Directional Checking.

This module implements Phase 4 auditing to ensure:
1. Stand-alone horizontal clues (no down-only indicators)
2. No double duty (definition and wordplay are discrete)
3. Fair indicators (contextual fairness checks)
"""

import logging
import os
import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

from portkey_ai import Portkey

# Configure logging
# Note: logging.basicConfig() should only be called in the main entry point (main.py)
# to avoid duplicate handlers when modules are imported
logger = logging.getLogger(__name__)


# ============================================================================
# DIRECTIONAL BLOCKLIST: Down-only indicators that should never appear
# ============================================================================
DIRECTIONAL_BLOCKLIST = {
    "rising",
    "lifted",
    "climbing",
    "up",
    "upwards",
    "skyward",
    "mounting",
    "ascending",
    "on",
    "supports",
    "overhead",
    "over",
    "underneath",
    "atop",
    "climbing up",
    "going up",
    "comes up",
    "rises",
    "lifts",
    "climbs"
}

# Noun indicators (generally unfair for anagrams)
# Note: Removed "mix" and "scramble" as these are acceptable as imperative verbs
# in MINIMALIST LIE style (e.g., "Mix listen" or "Scramble word")
NOUN_INDICATORS = {
    "anagram",
    "medley",
    "salad",
    "mixture",
    "hash",
    "chaos",
    "mess",
    "jumble",
    "tangle"
}


# Standard connectors allowed in Ximenean clues
ALLOWED_CONNECTORS = {
    "is", "for", "gives", "from", "at", "becomes", "to", "in", "of", "with"
}

# Priority cryptic abbreviations (Top 50 - widely recognized)
PRIORITY_ABBREVIATIONS = {
    # Roman numerals
    "I", "V", "X", "L", "C", "D", "M", "XI",
    # Common elements
    "H", "O", "N", "C", "AU", "AG", "FE", "PB", "CU",
    # Directions
    "N", "S", "E", "W", "L", "R",
    # Music
    "P", "F", "PP", "FF",
    # Chess
    "K", "Q", "B", "N", "R",
    # Titles
    "DR", "MO", "MP", "QC", "PM",
    # Academic
    "L", "BA", "MA", "BSC",
    # Units
    "T", "M", "G", "OZ", "LB", "S", "HR", "MIN",
    # Common single letters
    "A", "I", "O", "U", "V", "Y", "Z",
}

# Extended abbreviations (less common - flagged for review)
EXTENDED_ABBREVIATIONS = {
    "EN", "RE", "RA", "GI", "CA", "CH", "LA", "TE", "DIT", "DAH",
    "NT", "ER", "ED", "ST", "ND", "RD", "TH",
}


@dataclass
class AuditResult:
    """Result of auditing a clue."""
    
    passed: bool
    direction_check: bool
    direction_feedback: str
    double_duty_check: bool
    double_duty_feedback: str
    indicator_fairness_check: bool
    indicator_fairness_feedback: str
    identity_check: bool = True
    identity_feedback: str = ""
    fodder_presence_check: bool = True
    fodder_presence_feedback: str = ""
    filler_check: bool = True
    filler_feedback: str = ""
    indicator_grammar_check: bool = True
    indicator_grammar_feedback: str = ""
    narrative_integrity_check: bool = True
    narrative_integrity_feedback: str = ""
    obscurity_check: bool = True
    obscurity_feedback: str = ""
    word_validity_check: bool = True
    word_validity_feedback: str = ""
    fairness_score: float = 1.0
    refinement_suggestion: Optional[str] = None
    ximenean_score: float = 1.0
    difficulty_level: int = 3
    narrative_fidelity: float = 100.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "direction_check": self.direction_check,
            "direction_feedback": self.direction_feedback,
            "double_duty_check": self.double_duty_check,
            "double_duty_feedback": self.double_duty_feedback,
            "indicator_fairness_check": self.indicator_fairness_check,
            "indicator_fairness_feedback": self.indicator_fairness_feedback,
            "identity_check": self.identity_check,
            "identity_feedback": self.identity_feedback,
            "fodder_presence_check": self.fodder_presence_check,
            "fodder_presence_feedback": self.fodder_presence_feedback,
            "filler_check": self.filler_check,
            "filler_feedback": self.filler_feedback,
            "indicator_grammar_check": self.indicator_grammar_check,
            "indicator_grammar_feedback": self.indicator_grammar_feedback,
            "narrative_integrity_check": self.narrative_integrity_check,
            "narrative_integrity_feedback": self.narrative_integrity_feedback,
            "obscurity_check": self.obscurity_check,
            "obscurity_feedback": self.obscurity_feedback,
            "fairness_score": self.fairness_score,
            "refinement_suggestion": self.refinement_suggestion,
            "ximenean_score": self.ximenean_score,
            "difficulty_level": self.difficulty_level,
            "narrative_fidelity": self.narrative_fidelity,
        }


class XimeneanAuditor:
    """Audits cryptic clues for Ximenean fairness and technical correctness."""
    
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    # Use logic model for careful reasoning in auditing
    MODEL_ID = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID"))
    
    def __init__(self, timeout: float = 30.0, temperature: float = 0.5):
        """Initialize the Auditor with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 30.0).
            temperature: Temperature for generation (0.0-1.0, default: 0.5).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        self.temperature = temperature
        
        if not self.api_key:
            raise ValueError(
                "PORTKEY_API_KEY environment variable not set. "
                "Please set it before initializing the Auditor."
            )
        
        self.client = Portkey(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            timeout=timeout
        )
        
        # Initialize dictionary with robust error handling
        self.enchant_dict = None
        self._init_dictionary()
        
        logger.info(f"Auditor initialized with model: {self.MODEL_ID} [LOGIC tier] (temperature: {self.temperature})")
    
    def _init_dictionary(self):
        """Initialize enchant dictionary with fallback handling."""
        try:
            import enchant
            
            # Try British English first
            try:
                self.enchant_dict = enchant.request_dict("en_GB")
                logger.info("Enchant dictionary initialized: en_GB")
            except (AttributeError, Exception) as e:
                logger.warning(f"Failed to load en_GB dictionary: {e}")
                try:
                    # Fallback to US English
                    self.enchant_dict = enchant.request_dict("en_US")
                    logger.info("Enchant dictionary initialized: en_US (fallback)")
                except (AttributeError, Exception) as e2:
                    logger.warning(f"Failed to load en_US dictionary: {e2}")
                    self.enchant_dict = None
        except ImportError:
            logger.warning("Enchant library not available - word validation will use fallback")
            self.enchant_dict = None
    
    def is_word(self, word: str) -> bool:
        """Safe word validation with fallback.
        
        Args:
            word: Word to check
            
        Returns:
            True if word is valid or validation unavailable, False if definitely invalid
        """
        if not word or len(word) < 2:
            return False
        
        # If dictionary is available, use it
        if self.enchant_dict:
            try:
                return self.enchant_dict.check(word)
            except Exception as e:
                logger.debug(f"Dictionary check failed for '{word}': {e}")
                # Fall through to basic validation
        
        # Fallback: Basic pattern validation
        # Reject obvious gibberish patterns
        gibberish_patterns = [
            r'^[bcdfghjklmnpqrstvwxyz]{5,}$',  # 5+ consonants only
            r'^[aeiou]{4,}$',  # 4+ vowels only
            r'[^a-z]',  # Non-alphabetic characters
        ]
        
        word_lower = word.lower()
        for pattern in gibberish_patterns:
            if re.search(pattern, word_lower):
                return False
        
        # If not obviously gibberish, accept it (permissive fallback)
        return True
    
    def _check_direction(self, clue_json: Dict) -> Tuple[bool, str]:
        """
        Flag 1: Check for directional blocklist violations.
        Only flags directional words when they appear in the INDICATOR field.
        
        EXPLICITLY IGNORED:
        - Words in 'fodder' field (just raw material being manipulated)
        - Words in 'mechanism' field (just explanation of how wordplay works)
        
        Uses word boundaries to avoid false positives (e.g., "on" in "confused").
        
        Returns:
            (passed, feedback)
        """
        indicator = clue_json.get("wordplay_parts", {}).get("indicator", "").lower()
        
        blocklisted_terms = []
        
        # CRITICAL: Only check the indicator field
        # DO NOT check fodder or mechanism - those are just descriptive, not directional
        # Use word boundaries to match whole words only (prevents "on" matching in "scones")
        
        for term in DIRECTIONAL_BLOCKLIST:
            # Use word boundary regex to avoid false positives (e.g., "on" inside "scones")
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, indicator, re.IGNORECASE):
                blocklisted_terms.append(term)
        
        if blocklisted_terms:
            feedback = (
                f"[FAIL] Found down-only indicator(s) in indicator field: {', '.join(set(blocklisted_terms))}. "
                "This clue cannot be used in a stand-alone (horizontal) format."
            )
            return False, feedback
        
        feedback = "[PASS] No down-only indicators detected in indicator field."
        return True, feedback
    
    def _check_double_duty_with_llm(self, clue_json: Dict) -> Tuple[bool, str]:
        """
        Flag 2: Use LLM to verify definition and wordplay are discrete.
        
        Returns:
            (passed, feedback)
        """
        clue_text = clue_json.get("clue", "")
        definition = clue_json.get("definition", "")
        wordplay_parts = clue_json.get("wordplay_parts", {})
        
        prompt = f"""You are a strict but fair Ximenean auditor. Analyze this cryptic clue for "Double Duty" violations.

CLUE: "{clue_text}"

DEFINITION: "{definition}"

WORDPLAY FODDER: "{wordplay_parts.get('fodder', '')}"
INDICATOR: "{wordplay_parts.get('indicator', '')}"
MECHANISM: "{wordplay_parts.get('mechanism', '')}"

A 'Double Duty' error is VERY SPECIFIC: it only occurs if a word is being used as a mechanical instruction (indicator) AND is also the only word providing the definition.

CRITICAL FODDER VALIDATION:
- Cross-reference the FODDER field against the CLUE text.
- If the fodder contains a single letter (like 'a') or a word that is NOT present in the original clue, you MUST fail the clue immediately.
- Do not allow 'near-miss' anagrams where the solver must infer fodder words.
- Example FAIL: If fodder is "listen" but the clue says "Confused hearing sounds" (no "listen" word), FAIL.
- Example FAIL: If fodder is just "a" (single letter), FAIL immediately.

CRITICAL: If the definition is a synonym of the answer, that is NOT double duty. Double duty only occurs when a wordplay indicator is also the definition.

Critical Rules:
- If the clue is 'Supply food or look after someone's needs' (CATER), and 'Supply food' is the definition, and NO WORDS are being used as indicators, it is PASS.
- If the clue is 'Confused enlist soldiers to be quiet' (SILENT), and 'Confused' is the indicator and 'be quiet' is the definition, it is PASS.
- ONLY flag FAIL if a word like 'scrambled' is the definition and the anagram indicator at the same time.

Examples:
- PASS: "Serenity in pieces (5)" - "serenity" is definition, "in pieces" is indicator (separate words)
- PASS: "Ocean current hidden in tide pool (4)" - "current" is definition, "hidden in" is indicator (separate words)
- PASS: "Supply food or look after someone's needs (5)" - multi-word definition, no indicator (double definition clue)
- PASS: "Confused enlist soldiers to be quiet (6)" - "Confused" is indicator, "be quiet" is definition
- FAIL: "Shredded lettuce" - "shredded" is BOTH the anagram indicator AND the definition meaning "torn"
- FAIL: "Auditor with listen mixed" (answer AUTHOR) - "listen" is not in the clue, fodder invalid
- FAIL: "A is confused" - Fodder "a" is just one letter, not valid

Remember: 
1. Only flag FAIL for double duty if the SAME SINGLE WORD acts as both mechanical instruction AND definition.
2. ALSO flag FAIL if any fodder word is missing from the clue or if fodder is just a single letter.

Answer with ONLY:
PASS: [explanation] if no double duty is detected
FAIL: [explanation] if double duty is detected"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=200,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": "You are an expert Ximenean crossword auditor."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract response text
            response_text = self._extract_response_text(response)
            
            # Clean response and look for keywords anywhere in the first line
            clean_text = response_text.strip().upper()
            first_line = clean_text.split('\n')[0]
            
            if "PASS" in first_line or "PASS:" in clean_text:
                # It passed
                feedback = f"[PASS] No double duty detected.\n{response_text.strip()}"
                return True, feedback
            else:
                # It failed
                feedback = f"[FAIL] Double duty violation detected.\n{response_text.strip()}"
                return False, feedback
                
        except Exception as e:
            logger.error(f"Error checking double duty: {e}")
            feedback = f"[WARN] Could not verify double duty (LLM error): {str(e)}"
            return True, feedback  # Pass with warning if LLM fails
    
    def _check_indicator_fairness(self, clue_json: Dict) -> Tuple[bool, str]:
        """
        Flag 3: Check if the indicator is fair (e.g., noun indicators for anagrams).
        
        Returns:
            (passed, feedback)
        """
        clue_type = clue_json.get("type", "").lower()
        indicator = clue_json.get("wordplay_parts", {}).get("indicator", "").lower()
        
        # For anagrams, noun indicators are generally unfair
        if clue_type == "anagram":
            # Split indicator into words and check each word
            indicator_words = set(re.findall(r'\b\w+\b', indicator))
            
            for noun_ind in NOUN_INDICATORS:
                if noun_ind in indicator_words:
                    feedback = (
                        f"[WARN] Anagram uses noun indicator '{noun_ind}'. "
                        "Ximeneans prefer verb indicators (e.g., 'mixed', 'scrambled')."
                    )
                    return False, feedback
        
        feedback = "[PASS] Indicator appears fair."
        return True, feedback
    
    def _check_fodder_presence(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check that every character in the fodder is physically present in the clue text.
        
        This prevents using synonyms for fodder elements (e.g., using 'merchant' in 
        surface when fodder is 'DEALER').
        
        Returns:
            (passed, feedback)
        """
        clue_text = clue_json.get("clue", "").lower()
        wordplay_parts = clue_json.get("wordplay_parts", {})
        fodder = wordplay_parts.get("fodder", "").lower()
        
        if not fodder:
            return True, "[PASS] No fodder to check."
        
        # For certain clue types, fodder might be split or abbreviated
        clue_type = clue_json.get("type", "").lower()
        
        # Extract all words from fodder (split on non-alphanumeric)
        fodder_words = re.findall(r'\b[a-z]+\b', fodder)
        
        # Check if each fodder word appears in the clue
        missing_words = []
        for word in fodder_words:
            if len(word) > 2:  # Only check substantial words (not 'a', 'is', etc.)
                # Use word boundaries to match whole words
                pattern = r'\b' + re.escape(word) + r'\b'
                if not re.search(pattern, clue_text):
                    missing_words.append(word)
        
        if missing_words:
            feedback = (
                f"[FAIL] Fodder words not found in clue text: {', '.join(missing_words)}. "
                "This suggests synonyms were used instead of the exact fodder. "
                "Ximenean rules require the fodder to be physically present in the clue."
            )
            return False, feedback
        
        feedback = "[PASS] All fodder words are physically present in the clue."
        return True, feedback
    
    def _check_filler_words(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check for excessive filler words that aren't part of definition, fodder, or indicator.
        
        Only allows 0-2 standard connectors.
        
        Returns:
            (passed, feedback)
        """
        clue_text = clue_json.get("clue", "").lower()
        definition = clue_json.get("definition", "").lower()
        wordplay_parts = clue_json.get("wordplay_parts", {})
        fodder = wordplay_parts.get("fodder", "").lower()
        indicator = wordplay_parts.get("indicator", "").lower()
        
        # Extract all words from clue
        clue_words = set(re.findall(r'\b[a-z]+\b', clue_text))
        definition_words = set(re.findall(r'\b[a-z]+\b', definition))
        fodder_words = set(re.findall(r'\b[a-z]+\b', fodder))
        indicator_words = set(re.findall(r'\b[a-z]+\b', indicator))
        
        # Words that have a purpose
        functional_words = definition_words | fodder_words | indicator_words
        
        # Find potential filler words
        potential_fillers = clue_words - functional_words
        
        # Count how many are connectors vs true fillers
        connectors_used = potential_fillers & ALLOWED_CONNECTORS
        true_fillers = potential_fillers - ALLOWED_CONNECTORS
        
        # MINIMALIST LIE STANDARD: Flag excessive words
        total_extra_words = len(connectors_used) + len(true_fillers)
        
        # MINIMALIST LIE STANDARD: Strict economy
        if len(connectors_used) > 2:
            feedback = (
                f"[FAIL] Too many connectors ({len(connectors_used)}): {', '.join(sorted(connectors_used))}. "
                "MINIMALIST LIE: Use at most 2 connectors. Build with Definition + Fodder + Indicator first."
            )
            return False, feedback
        
        if true_fillers:
            feedback = (
                f"[FAIL] Filler words detected: {', '.join(sorted(true_fillers))}. "
                "These words fail the THEMATIC NECESSITY TEST. "
                "Every word must be definition, fodder, indicator, or an essential thematic connector."
            )
            return False, feedback
        
        feedback = "[PASS] Minimalist economy achieved - all words serve a cryptic purpose."
        return True, feedback
    
    def _check_indicator_grammar(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check indicator grammar based on position relative to fodder.
        
        CLASSIC XIMENEAN RULE (Primarily for Anagrams):
        - Past participles BEFORE fodder are acceptable (attributive: "Confused dirty room")
        - Past participles AFTER fodder are wrong for anagrams (predicative: "Dirty room confused")
        - For other clue types (Reversal, etc.), past participles are often acceptable
        
        Returns:
            (passed, feedback)
        """
        clue_text = clue_json.get("clue", "").lower()
        clue_type = clue_json.get("type", "").lower()
        wordplay_parts = clue_json.get("wordplay_parts", {})
        indicator = wordplay_parts.get("indicator", "").lower().strip()
        fodder = wordplay_parts.get("fodder", "").lower().strip()
        
        if not indicator or not fodder:
            return True, "[PASS] No indicator or fodder to check."
        
        # Find positions in clue
        indicator_pos = clue_text.find(indicator)
        fodder_pos = clue_text.find(fodder)
        
        if indicator_pos == -1 or fodder_pos == -1:
            # Can't determine position, pass
            return True, "[PASS] Cannot determine indicator/fodder positions."
        
        # Check if indicator is a past participle
        indicator_words = indicator.split()
        past_participles = []
        
        for word in indicator_words:
            # Skip very short words and common words that end in 'ed'
            if len(word) <= 3 or word in ['red', 'bed', 'fed', 'led', 'wed', 'bred', 'shed']:
                continue
            
            if word.endswith('ed'):
                past_participles.append(word)
        
        if not past_participles:
            # No past participles, grammar is fine
            return True, "[PASS] Indicator grammar is correct (imperative form)."
        
        # If past participles exist, check position
        if indicator_pos < fodder_pos:
            # Past participle BEFORE fodder - ACCEPTABLE (attributive use)
            feedback = (
                f"[PASS] Indicator '{indicator}' uses past participle in attributive position "
                f"(before fodder). This is acceptable classic Ximenean style."
            )
            return True, feedback
        else:
            # Past participle AFTER fodder - check if it's an anagram
            if clue_type == "anagram":
                # For anagrams, past participles after fodder are WRONG
                feedback = (
                    f"[FAIL] Indicator '{indicator}' appears AFTER fodder in anagram clue. "
                    f"Past participles after fodder suggest a state rather than an instruction. "
                    f"Prefer imperative forms (e.g., 'mix' not 'mixed') or place indicator before fodder."
                )
                return False, feedback
            else:
                # For other types (reversal, etc.), past participles after fodder are OK
                feedback = (
                    f"[PASS] Indicator '{indicator}' uses past participle after fodder. "
                    f"This is acceptable for {clue_type} clues (e.g., 'returned' for reversals)."
                )
                return True, feedback
    
    def _check_identity_constraint(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check that the answer does not appear in the wordplay fodder.
        
        IDENTITY CONSTRAINT:
        - The answer (or common variants) must not appear in the fodder
        - For Hidden Words: answer must span at least two different words
        - Prevents lazy clues where the answer hides within itself
        
        Returns:
            (passed, feedback)
        """
        answer = clue_json.get("answer", "").upper()
        wordplay_parts = clue_json.get("wordplay_parts", {})
        clue_type = clue_json.get("type", "").lower()
        
        # Extract fodder based on clue type
        fodder = ""
        if "fodder" in wordplay_parts:
            fodder = wordplay_parts.get("fodder", "")
        elif "parts" in wordplay_parts and isinstance(wordplay_parts["parts"], list):
            fodder = " ".join(wordplay_parts["parts"])
        elif "outer" in wordplay_parts and "inner" in wordplay_parts:
            fodder = f"{wordplay_parts.get('outer', '')} {wordplay_parts.get('inner', '')}"
        
        if not fodder:
            return True, "[PASS] No fodder to check"
        
        # Normalize for comparison
        normalized_fodder = re.sub(r'[^a-zA-Z]', '', fodder).lower()
        normalized_answer = re.sub(r'[^a-zA-Z]', '', answer).lower()
        
        # Check if answer appears in fodder
        if normalized_answer in normalized_fodder:
            return False, (
                f"[FAIL] Identity constraint violated: answer '{answer}' appears in fodder '{fodder}'. "
                "The answer must not appear in the wordplay material."
            )
        
        # Check common variants
        if len(normalized_answer) > 3:
            variants = [
                normalized_answer + 's',
                normalized_answer + 'ed',
                normalized_answer + 'ing'
            ]
            if normalized_answer.endswith('e'):
                variants.append(normalized_answer[:-1] + 'ed')
                variants.append(normalized_answer[:-1] + 'ing')
            
            for variant in variants:
                if variant in normalized_fodder:
                    return False, (
                        f"[FAIL] Identity constraint violated: answer variant '{variant}' appears in fodder '{fodder}'. "
                        "Common word forms of the answer must not appear in the wordplay."
                    )
        
        # Special check for Hidden Word clues
        if "hidden" in clue_type:
            fodder_words = fodder.split()
            if len(fodder_words) == 1 and normalized_fodder == normalized_answer:
                return False, (
                    f"[FAIL] Identity constraint violated: Hidden Word fodder '{fodder}' IS the answer itself. "
                    "The answer must be concealed across at least two different words."
                )
        
        return True, f"[PASS] Identity constraint satisfied: '{answer}' not found in fodder"
    
    def _check_narrative_integrity(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check that the surface reading is natural English, not a literal listing.
        
        THE NO-GIBBERISH RULE:
        - Clues must not contain standalone single letters or fragments (e.g., "with n, e, w")
        - All components must use standard cryptic abbreviations or real words
        - For anagrams specifically: fodder must consist of real English words, not fragments
        
        Returns:
            (passed, feedback)
        """
        clue_type = clue_json.get("type", "").lower()
        
        # Special check for anagram fodder quality
        if "anagram" in clue_type and self.enchant_dict:
            wordplay_parts = clue_json.get("wordplay_parts", {})
            fodder = wordplay_parts.get("fodder", "")
            
            if fodder:
                words = fodder.lower().split()
                valid_abbreviations = {'n', 's', 'e', 'w', 'l', 'r', 'u', 'o', 'er', 'ed', 're'}
                
                invalid_words = []
                for word in words:
                    # Skip very short abbreviations
                    if len(word) <= 2 and word in valid_abbreviations:
                        continue
                    # Check dictionary
                    if not self.enchant_dict.check(word):
                        invalid_words.append(word)
                
                if invalid_words:
                    feedback = (
                        f"[FAIL] Anagram fodder contains non-dictionary gibberish: {', '.join(invalid_words)}. "
                        f"Ximenean standard requires all anagram fodder to be real English words. "
                        f"Even if the letters match mathematically, gibberish fodder awards a score of 0.0."
                    )
                    return False, feedback
        clue_text = clue_json.get("clue", "").lower()
        
        # Pattern 1: Check for comma-separated single letters (literal listing)
        # Matches patterns like: "with a, b, c" or "from x, y, z" or "has n, e, w"
        import re
        
        literal_listing_patterns = [
            r'\b[a-z]\s*,\s*[a-z]\b',  # "x, y" or "n, e"
            r'\b[a-z]\s*,\s*[a-z]\s*,\s*[a-z]\b',  # "x, y, z"
            r'\bwith\s+[a-z]{1,2}\s*,',  # "with en," or "with n,"
            r'\bfrom\s+[a-z]{1,2}\s*,',  # "from en," or "from n,"
            r'\bhas\s+[a-z]{1,2}\s*,',   # "has en," or "has n,"
        ]
        
        for pattern in literal_listing_patterns:
            if re.search(pattern, clue_text):
                match = re.search(pattern, clue_text)
                snippet = match.group(0) if match else "listing"
                feedback = (
                    f"[FAIL] Surface contains literal letter listing: '{snippet}'. "
                    "NO-GIBBERISH RULE: Single letters must be masked using standard cryptic abbreviations. "
                    "Example: 'N' → 'north/knight/new', 'Y' → 'unknown/year', 'EN' → 'in/nurse'."
                )
                return False, feedback
        
        # Pattern 2: Check for standalone short fragments that look non-English
        # Split by common delimiters and check for suspicious tokens
        tokens = re.findall(r'\b[a-z]+\b', clue_text)
        
        # Common cryptic abbreviations that are acceptable as standalone
        acceptable_short = {
            'a', 'i', 'is', 'in', 'it', 'at', 'to', 'of', 'or', 'an', 'as', 'be', 'by', 
            'do', 'go', 'he', 'if', 'me', 'my', 'no', 'on', 'so', 'up', 'us', 'we',
            # Cryptic standards
            'ace', 'one', 'ten', 'two', 'gas', 'old', 'new', 'son', 'tea'
        }
        
        # Look for 2-letter tokens that might be unmasked abbreviations
        suspicious_tokens = []
        for token in tokens:
            if len(token) == 2 and token not in acceptable_short:
                # Check if it's a common word or likely an unmasked code
                common_two_letter = {'am', 'an', 'as', 'at', 'be', 'by', 'do', 'go', 'he', 
                                    'hi', 'if', 'in', 'is', 'it', 'me', 'my', 'no', 'of', 
                                    'oh', 'ok', 'on', 'or', 'ox', 'so', 'to', 'up', 'us', 
                                    'we', 'ye'}
                if token not in common_two_letter:
                    suspicious_tokens.append(token)
        
        # If we find suspicious unmasked tokens in a listinging context, warn
        if suspicious_tokens and ',' in clue_text:
            feedback = (
                f"[WARN] Possible unmasked abbreviations: {', '.join(suspicious_tokens)}. "
                "Verify these are natural English words, not letter codes. "
                "If codes, use cryptic substitutions (e.g., 'en' → 'nurse', 're' → 'soldier')."
            )
            return True, feedback  # Warning, not hard fail
        
        feedback = "[PASS] Surface reading appears natural - no literal letter listings detected."
        return True, feedback
    
    def _check_obscurity(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check that wordplay uses standard Top 50 cryptic abbreviations, not obscure fragments.
        
        TOP 50 PRIORITY ABBREVIATIONS:
        - Roman numerals, common elements, directions, music, chess, titles, units
        - Widely recognized in standard cryptic crosswords
        
        FLAGS:
        - Non-standard abbreviations (e.g., DIT, DAH, EN) for manual review
        - Non-word fodder (e.g., NETTAB, KCITS) for rejection
        
        Returns:
            (passed, feedback)
        """
        wordplay_parts = clue_json.get("wordplay_parts", {})
        clue_type = clue_json.get("type", "").lower()
        fodder = wordplay_parts.get("fodder", "").upper()
        mechanism = wordplay_parts.get("mechanism", "").lower()
        
        # Extract fragments from fodder (for Charades, Containers)
        # Look for patterns like "EN + TREAT + Y" or "EN (nurse) + TREAT"
        import re
        fragments = re.findall(r'\b([A-Z]{1,4})\b', fodder)
        
        # Check 1: Flag non-priority abbreviations
        non_priority_fragments = []
        for frag in fragments:
            # Skip if it's a full word (not an abbreviation)
            if len(frag) > 3:
                continue
            
            if frag not in PRIORITY_ABBREVIATIONS and frag not in EXTENDED_ABBREVIATIONS:
                # Unknown fragment
                non_priority_fragments.append(frag)
            elif frag in EXTENDED_ABBREVIATIONS:
                # Extended = less common, warn
                non_priority_fragments.append(f"{frag} (extended)")
        
        if non_priority_fragments:
            feedback = (
                f"[WARN] Non-priority abbreviations detected: {', '.join(non_priority_fragments)}. "
                "TOP 50 PRIORITY: Use Roman numerals (I,V,X,L,C,D,M), common elements (H,O,N,AU,FE), "
                "directions (N,S,E,W), music (P,F), chess (K,Q,B,N), titles (DR,MP,MO), units (T,M,S,HR). "
                "Extended abbreviations should be justified via Wikipedia Crossword Abbreviations."
            )
            return True, feedback  # Warning, not hard fail
        
        # Check 2: Verify fodder words are real English (critical for reversals)
        if clue_type in ["reversal", "reverse"]:
            # Extract the actual fodder word (not the mechanism)
            # Pattern: fodder is usually a single word for reversals
            fodder_words = re.findall(r'\b[a-z]+\b', fodder.lower())
            
            # Use safe word validation
            non_words = []
            
            for word in fodder_words:
                if len(word) > 2 and not self.is_word(word):
                    # Not a valid English word
                    non_words.append(word)
            
            if non_words:
                feedback = (
                    f"[FAIL] Non-word fodder detected: {', '.join(non_words)}. "
                    "NO NON-WORDS AS FODDER: Every piece of fodder must be a real English word. "
                    "For reversals, both original and reversed must be valid words. "
                    "If reversal creates non-word (e.g., 'nettab', 'kcits'), choose DIFFERENT mechanism."
                )
                return False, feedback
        
        # Check 3: Look for non-word patterns in mechanism description
        # Patterns like "reverse of nettab" or "anagram of kcits"
        non_word_patterns = [
            r'reverse of ([a-z]+)',
            r'anagram of ([a-z]+)',
            r'hidden in ([a-z]+)',
        ]
        
        for pattern in non_word_patterns:
            matches = re.findall(pattern, mechanism)
            for match in matches:
                if len(match) > 3:  # Only check substantial words
                    if not self.is_word(match):
                        feedback = (
                            f"[FAIL] Non-word in mechanism: '{match}'. "
                            "Surface legitimacy check: Wordplay cannot force non-words into the clue. "
                            "Choose a different mechanism that uses real English words only."
                        )
                        return False, feedback
        
        feedback = "[PASS] All abbreviations are standard Top 50 priority types."
        return True, feedback
    
    def _check_word_validity(self, clue_json: Dict) -> Tuple[bool, str]:
        """Check that all fodder words are valid English dictionary words.
        
        REAL-WORD DICTIONARY CONSTRAINT:
        - All mechanical fodder must be legitimate English words
        - Particularly critical for Reversals and Containers
        - Prevents gibberish like 'AMHTSA', 'nettab', 'kcits'
        
        Returns:
            (passed, feedback)
        """
        wordplay_parts = clue_json.get("wordplay_parts", {})
        clue_type = clue_json.get("type", "").lower()
        fodder = wordplay_parts.get("fodder", "").lower()
        mechanism = wordplay_parts.get("mechanism", "").lower()
        
        if not fodder:
            return True, "[PASS] No fodder to validate."
        
        # Extract all words from fodder (ignoring operators like +, parentheses, etc.)
        fodder_words = re.findall(r'\b[a-z]{2,}\b', fodder)
        
        # Filter out obvious abbreviations (2-3 letter fragments that are known abbreviations)
        words_to_check = []
        for word in fodder_words:
            # Skip if it's a known abbreviation
            word_upper = word.upper()
            if word_upper in PRIORITY_ABBREVIATIONS or word_upper in EXTENDED_ABBREVIATIONS:
                continue
            # Check words of substantial length (3+ characters)
            if len(word) >= 3:
                words_to_check.append(word)
        
        if not words_to_check:
            return True, "[PASS] No substantial words in fodder to validate."
        
        # Validate words using safe dictionary wrapper
        non_words = []
        
        for word in words_to_check:
            if not self.is_word(word):
                non_words.append(word)
        
        if non_words:
            feedback = (
                f"[FAIL] Non-dictionary words detected in fodder: {', '.join(non_words)}. "
                "REAL-WORD DICTIONARY CONSTRAINT: All mechanical fodder must be legitimate English words. "
            )
            
            # Specific guidance by clue type
            if clue_type in ["reversal", "reverse"]:
                feedback += (
                    "For Reversals, both the fodder word AND its reverse must be valid. "
                    "Example: 'lager' (valid) → REGAL (valid) ✓. "
                    "Counter-example: 'amhtsa' (gibberish) → ASTHMA ✗. "
                    "MECHANISM PIVOT REQUIRED: Choose Charade, Hidden Word, or Anagram instead."
                )
            elif clue_type in ["container", "insertion"]:
                feedback += (
                    "For Containers, both outer and inner words must be dictionary-valid. "
                    "Example: IN inside PAT = PAINT ✓. "
                    "Counter-example: 'nettab' containing EN ✗."
                )
            else:
                feedback += (
                    "Every piece of fodder must be defensible via standard English dictionaries "
                    "(Oxford, Merriam-Webster, etc.)."
                )
            
            # Add note if using fallback validation
            if not self.enchant_dict:
                feedback += " (Note: Using basic validation - install pyenchant for full dictionary checking)"
            
            return False, feedback
        
        feedback = "[PASS] All fodder words are valid dictionary entries."
        return True, feedback
    
    def _calculate_ximenean_score(self, clue_json: Dict, checks: Dict[str, bool]) -> float:
        """Calculate Ximenean Score (0.0-1.0) measuring technical compliance.
        
        Penalizes for:
        - Filler words (excessive connectors or true fillers)
        - Incorrect indicator grammar (non-imperative)
        - Lack of fodder integrity (synonyms instead of exact fodder)
        
        Args:
            clue_json: The clue JSON object
            checks: Dictionary of check results
        
        Returns:
            Float between 0.0 and 1.0 (1.0 = perfect compliance)
        """
        score = 1.0
        
        # Penalty for filler words (max -0.3)
        if not checks['filler']:
            clue_text = clue_json.get("clue", "").lower()
            clue_words = len(re.findall(r'\b[a-z]+\b', clue_text))
            # Harsher penalty for longer clues with fillers
            if clue_words > 10:
                score -= 0.3
            elif clue_words > 8:
                score -= 0.2
            else:
                score -= 0.15
        
        # Penalty for indicator grammar issues (max -0.3)
        if not checks['grammar']:
            score -= 0.3
        
        # Penalty for fodder integrity issues (max -0.4)
        if not checks['fodder']:
            score -= 0.4
        
        # CRITICAL: Penalty for non-word fodder (max -0.5)
        # This is the most severe penalty as gibberish violates core Ximenean principles
        if not checks['word_validity']:
            score -= 0.5
        
        # Penalty for obscurity issues (max -0.2)
        if not checks['obscurity']:
            score -= 0.2
        
        # Penalty for narrative integrity (max -0.25)
        if not checks['narrative']:
            score -= 0.25
        
        # Ensure score doesn't go below 0
        return max(0.0, score)
    
    def _calculate_difficulty_level(self, clue_json: Dict) -> int:
        """Calculate Difficulty Level (1-5) based on complexity.
        
        Levels:
        1. Direct: Obvious definitions, simple mechanisms
        2. Moderate: Standard indicators, common abbreviations
        3. Intermediate: Some deceptive masking
        4. Advanced: Oblique definitions, complex charades
        5. Master: Gold standard deceptions, lateral leaps
        
        Args:
            clue_json: The clue JSON object
        
        Returns:
            Integer between 1 and 5
        """
        difficulty = 3  # Start at intermediate
        
        clue_type = clue_json.get("type", "").lower()
        definition = clue_json.get("definition", "").lower()
        clue_text = clue_json.get("clue", "").lower()
        wordplay_parts = clue_json.get("wordplay_parts", {})
        fodder = wordplay_parts.get("fodder", "").upper()
        
        # Factor 1: Clue type complexity
        if clue_type in ["hidden", "homophone"]:
            difficulty -= 1  # Simpler mechanisms
        elif clue_type in ["container", "double definition"]:
            difficulty += 0  # Standard complexity
        elif clue_type in ["reversal", "charade"]:
            difficulty += 1  # More complex
        
        # Factor 2: Definition obliqueness
        # Check if definition appears verbatim in clue (less oblique)
        if definition in clue_text:
            difficulty -= 1
        else:
            # Definition is transformed/oblique
            difficulty += 1
        
        # Factor 3: Abbreviation usage (cryptic masking)
        priority_abbrev_count = sum(1 for abbr in PRIORITY_ABBREVIATIONS if abbr in fodder)
        if priority_abbrev_count >= 3:
            difficulty += 1  # Heavy cryptic substitution
        
        # Factor 4: Clue length (longer = potentially more complex)
        word_count = len(clue_text.split())
        if word_count <= 5:
            difficulty -= 1  # Minimalist, cleaner
        elif word_count >= 10:
            difficulty += 0  # Verbose doesn't mean harder
        
        # Factor 5: Fodder complexity
        fodder_parts = fodder.split("+")
        if len(fodder_parts) >= 4:
            difficulty += 1  # Complex charade
        
        # Clamp to 1-5 range
        return max(1, min(5, difficulty))
    
    def _calculate_narrative_fidelity(self, clue_json: Dict, checks: Dict[str, bool]) -> float:
        """Calculate Narrative Fidelity (0-100%) measuring surface naturalness.
        
        100% means the clue sounds exactly like a natural sentence.
        Lower scores indicate visible cryptic mechanics seams.
        
        Args:
            clue_json: The clue JSON object
            checks: Dictionary of check results
        
        Returns:
            Float between 0.0 and 100.0
        """
        fidelity = 100.0
        
        clue_text = clue_json.get("clue", "")
        
        # Major penalties
        # Narrative integrity failure (literal listings) - severe
        if not checks['narrative']:
            fidelity -= 40.0
        
        # Filler words (verbose, unnatural)
        if not checks['filler']:
            fidelity -= 20.0
        
        # Minor penalties
        # Indicator grammar issues (awkward phrasing)
        if not checks['grammar']:
            fidelity -= 15.0
        
        # Double duty issues (mechanical predictability)
        if not checks['double_duty']:
            fidelity -= 10.0
        
        # Obscurity issues (non-standard abbreviations feel forced)
        if not checks['obscurity']:
            fidelity -= 10.0
        
        # Bonus for brevity (minimalist clues sound cleaner)
        word_count = len(clue_text.split())
        if word_count <= 6:
            fidelity += 5.0  # Elegant economy
        elif word_count >= 12:
            fidelity -= 10.0  # Verbose, clunky
        
        # Ensure fidelity stays in valid range
        return max(0.0, min(100.0, fidelity))
    
    def _extract_response_text(self, response) -> str:
        """
        Extract text content from Portkey API response.
        
        Handles various response formats from the Portkey Gateway.
        Consolidated to match setter_agent.py implementation.
        
        Args:
            response: The response object from Portkey API.
        
        Returns:
            Extracted text string.
        
        Raises:
            ValueError: If response text cannot be extracted.
        """
        if not response.choices or len(response.choices) == 0:
            raise ValueError("Empty response from API")
        
        choice = response.choices[0]
        response_text = None
        
        # Method 1: Try response.choices[0].text
        if hasattr(choice, 'text') and isinstance(choice.text, str):
            response_text = choice.text
        # Method 2: Try response.choices[0].message.content (most common)
        elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
            msg_content = choice.message.content
            # The content might be a dict, string, list, or iterator
            if isinstance(msg_content, str):
                response_text = msg_content
            elif isinstance(msg_content, dict):
                response_text = msg_content.get('text', '')
            elif isinstance(msg_content, (list, tuple)) and len(msg_content) > 0:
                first_item = msg_content[0]
                if isinstance(first_item, dict):
                    response_text = first_item.get('text', str(first_item))
                else:
                    response_text = str(first_item)
            else:
                # Try to convert iterator/complex type to list
                try:
                    msg_list = list(msg_content)
                    if msg_list and isinstance(msg_list[0], dict):
                        response_text = msg_list[0].get('text', '')
                    elif msg_list:
                        response_text = str(msg_list[0])
                except:
                    response_text = str(msg_content)
        
        if not response_text:
            raise ValueError("Could not extract response text from API response")
        
        return response_text
    
    def audit_clue(self, clue_json: Dict) -> AuditResult:
        """
        Audit a clue for Ximenean fairness and technical correctness.
        
        Args:
            clue_json: The clue dictionary from Setter Agent.
        
        Returns:
            AuditResult with pass/fail and detailed feedback.
        """
        logger.info(f"Auditing clue for '{clue_json.get('answer', 'UNKNOWN')}'")
        
        # Flag 1: Direction check
        direction_passed, direction_feedback = self._check_direction(clue_json)
        
        # Flag 2: Double duty check (LLM-based)
        double_duty_passed, double_duty_feedback = self._check_double_duty_with_llm(clue_json)
        
        # Flag 3: Indicator fairness check
        fairness_passed, fairness_feedback = self._check_indicator_fairness(clue_json)
        
        # Flag 4: Identity constraint check (NEW - Anti-Lazy Clue Detection)
        identity_passed, identity_feedback = self._check_identity_constraint(clue_json)
        
        # Flag 5: Fodder presence check (NEW - Strict Ximenean)
        fodder_passed, fodder_feedback = self._check_fodder_presence(clue_json)
        
        # Flag 6: Filler words check (NEW - Strict Ximenean)
        filler_passed, filler_feedback = self._check_filler_words(clue_json)
        
        # Flag 7: Indicator grammar check (NEW - Strict Ximenean)
        grammar_passed, grammar_feedback = self._check_indicator_grammar(clue_json)
        
        # Flag 8: Narrative integrity check (NEW - Advanced Narrative Masking)
        narrative_passed, narrative_feedback = self._check_narrative_integrity(clue_json)
        
        # Flag 9: Obscurity check (NEW - Top-Tier Cryptic Standards)
        obscurity_passed, obscurity_feedback = self._check_obscurity(clue_json)
        
        # Flag 10: Word validity check (NEW - Real-Word Dictionary Constraint)
        word_validity_passed, word_validity_feedback = self._check_word_validity(clue_json)
        
        # Calculate fairness score (0-1)
        checks = [
            direction_passed,
            double_duty_passed,
            fairness_passed,
            identity_passed,
            fodder_passed,
            filler_passed,
            grammar_passed,
            narrative_passed,
            obscurity_passed,
            word_validity_passed
        ]
        fairness_score = sum(checks) / len(checks)
        
        # Calculate advanced metrics (Phase 10)
        check_dict = {
            'direction': direction_passed,
            'double_duty': double_duty_passed,
            'fairness': fairness_passed,
            'identity': identity_passed,
            'fodder': fodder_passed,
            'filler': filler_passed,
            'grammar': grammar_passed,
            'narrative': narrative_passed,
            'obscurity': obscurity_passed,
            'word_validity': word_validity_passed
        }
        
        ximenean_score = self._calculate_ximenean_score(clue_json, check_dict)
        difficulty_level = self._calculate_difficulty_level(clue_json)
        narrative_fidelity = self._calculate_narrative_fidelity(clue_json, check_dict)
        
        # Overall pass (all flags must pass)
        overall_passed = all(checks)
        
        # Generate refinement suggestion if fairness_score < 1.0 but > 0.5
        refinement_suggestion = None
        if not overall_passed and fairness_score > 0.5:
            refinement_suggestion = self._suggest_refinement(clue_json)
        
        audit_result = AuditResult(
            passed=overall_passed,
            direction_check=direction_passed,
            direction_feedback=direction_feedback,
            double_duty_check=double_duty_passed,
            double_duty_feedback=double_duty_feedback,
            indicator_fairness_check=fairness_passed,
            indicator_fairness_feedback=fairness_feedback,
            identity_check=identity_passed,
            identity_feedback=identity_feedback,
            fodder_presence_check=fodder_passed,
            fodder_presence_feedback=fodder_feedback,
            filler_check=filler_passed,
            filler_feedback=filler_feedback,
            indicator_grammar_check=grammar_passed,
            indicator_grammar_feedback=grammar_feedback,
            narrative_integrity_check=narrative_passed,
            narrative_integrity_feedback=narrative_feedback,
            obscurity_check=obscurity_passed,
            obscurity_feedback=obscurity_feedback,
            word_validity_check=word_validity_passed,
            word_validity_feedback=word_validity_feedback,
            fairness_score=fairness_score,
            refinement_suggestion=refinement_suggestion,
            ximenean_score=ximenean_score,
            difficulty_level=difficulty_level,
            narrative_fidelity=narrative_fidelity
        )
        
        logger.info(
            f"Audit result: {'PASSED' if overall_passed else 'FAILED'} "
            f"(fairness_score: {fairness_score:.1%}, ximenean: {ximenean_score:.2f}, "
            f"difficulty: {difficulty_level}/5, narrative: {narrative_fidelity:.0f}%)"
        )
        
        return audit_result
    
    def _suggest_refinement(self, clue_json: Dict) -> str:
        """
        Suggest improvements to the surface reading while keeping wordplay identical.
        
        Args:
            clue_json: The clue dictionary.
        
        Returns:
            A refinement suggestion string.
        """
        clue_text = clue_json.get("clue", "")
        definition = clue_json.get("definition", "")
        wordplay_parts = clue_json.get("wordplay_parts", {})
        
        prompt = f"""Suggest a refined surface reading for this clue that:
1. Keeps the exact same wordplay mechanism
2. Improves the definition part
3. Makes it more natural English

CURRENT CLUE: "{clue_text}"

DEFINITION: "{definition}"

WORDPLAY: {wordplay_parts.get('mechanism', '')}

Suggest ONE alternative surface reading that:
- Uses the same wordplay technique
- Sounds more natural
- Better disguises the wordplay

Return only the refined clue, nothing else."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=150,
                messages=[
                    {"role": "system", "content": "You are an expert cryptic clue writer."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return self._extract_response_text(response).strip()
        except Exception as e:
            logger.error(f"Error suggesting refinement: {e}")
            return None


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    auditor = XimeneanAuditor()
    
    # Test Case 1: Good clue (should pass)
    good_clue = {
        "clue": "Quietly listen to storyteller (6)",
        "definition": "Quietly",
        "answer": "SILENT",
        "type": "Charade",
        "wordplay_parts": {
            "fodder": "S + I + L",
            "indicator": "listen",
            "mechanism": "S (silent sounds) + I (listen to I) + L (storyteller)"
        },
        "explanation": "Silent + I + ent"
    }
    
    print("\n=== TEST 1: Good Clue ===")
    result = auditor.audit_clue(good_clue)
    print(f"Passed: {result.passed}")
    print(f"Direction: {result.direction_check} - {result.direction_feedback}")
    print(f"Double Duty: {result.double_duty_check} - {result.double_duty_feedback}")
    print(f"Fairness: {result.indicator_fairness_check} - {result.indicator_fairness_feedback}")
    
    # Test Case 2: Clue with down-only indicator (should fail direction check)
    bad_clue_direction = {
        "clue": "Listen rising in the morning (6)",
        "definition": "Listen",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "LISTEN",
            "indicator": "rising",
            "mechanism": "LISTEN anagram = SILENT"
        },
        "explanation": "LISTEN (fodder) rising (indicator) = SILENT"
    }
    
    print("\n=== TEST 2: Clue with Down-Only Indicator ===")
    result = auditor.audit_clue(bad_clue_direction)
    print(f"Passed: {result.passed}")
    print(f"Direction: {result.direction_check} - {result.direction_feedback}")
    
    # Test Case 3: Clue with unfair anagram indicator
    noun_indicator_clue = {
        "clue": "Listen - a jumble (6)",
        "definition": "Listen",
        "answer": "SILENT",
        "type": "Anagram",
        "wordplay_parts": {
            "fodder": "LISTEN",
            "indicator": "jumble",
            "mechanism": "LISTEN anagram = SILENT"
        },
        "explanation": "LISTEN (fodder) jumble (indicator) = SILENT"
    }
    
    print("\n=== TEST 3: Clue with Noun Indicator ===")
    result = auditor.audit_clue(noun_indicator_clue)
    print(f"Passed: {result.passed}")
    print(f"Direction: {result.direction_check}")
    print(f"Fairness: {result.indicator_fairness_check} - {result.indicator_fairness_feedback}")
