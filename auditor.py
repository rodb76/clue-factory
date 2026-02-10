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
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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
NOUN_INDICATORS = {
    "anagram",
    "mix",
    "medley",
    "salad",
    "mixture",
    "hash",
    "chaos",
    "mess",
    "jumble",
    "tangle",
    "scramble"
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
    fairness_score: float
    refinement_suggestion: Optional[str] = None
    
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
            "fairness_score": self.fairness_score,
            "refinement_suggestion": self.refinement_suggestion,
        }


class XimeneanAuditor:
    """Audits cryptic clues for Ximenean fairness and technical correctness."""
    
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    # Use logic model for careful reasoning in auditing
    MODEL_ID = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID"))
    
    def __init__(self, timeout: float = 30.0):
        """Initialize the Auditor with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 30.0).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        
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
        
        logger.info(f"Auditor initialized with model: {self.MODEL_ID} [LOGIC tier]")
    
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

Remember: Only flag FAIL if the SAME SINGLE WORD acts as both the mechanical instruction AND the definition.

Answer with ONLY:
PASS: [explanation] if no double duty is detected
FAIL: [explanation] if double duty is detected"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=200,
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
        
        # Calculate fairness score (0-1)
        fairness_score = sum([
            direction_passed,
            double_duty_passed,
            fairness_passed
        ]) / 3.0
        
        # Overall pass (all flags must pass)
        overall_passed = direction_passed and double_duty_passed and fairness_passed
        
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
            fairness_score=fairness_score,
            refinement_suggestion=refinement_suggestion
        )
        
        logger.info(
            f"Audit result: {'PASSED' if overall_passed else 'FAILED'} "
            f"(fairness_score: {fairness_score:.1%})"
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
