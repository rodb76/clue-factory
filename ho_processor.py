"""
George Ho Dataset Processor: Reverse-Engineering Professional Cryptics

This script enriches the George Ho cryptic dataset (https://cryptics.georgeho.org/)
by adding wordplay explanations and Ximenean metrics through reverse-engineering.

Features:
1. Smart batch sampling with filters (source, is_reviewed, limit, random)
2. Reverse-engineering logic using Logic Tier (Sonnet)
3. Enrichment with Surface Tier (Haiku) explanations
4. Ximenean auditing for quality metrics
5. Metadata preservation (source, source_url, puzzle_date)
"""

import os
import sys
import json
import logging
import argparse
import re
import random
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

from portkey_ai import Portkey
from auditor import XimeneanAuditor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_enumeration(clue: str, answer: str) -> str:
    """Ensure clue has enumeration pattern. Add it if missing.
    
    Args:
        clue: The clue text
        answer: The answer word
    
    Returns:
        Clue with enumeration appended if it was missing
    """
    # Check if clue already has enumeration like (5) or (3,4) or (2-3,4)
    if re.search(r'\(\d+[,\-\d]*\)$', clue.strip()):
        return clue
    
    # Calculate enumeration from answer
    # Split by spaces and hyphens to get word lengths
    words = re.split(r'[\s\-]+', answer)
    lengths = [str(len(word)) for word in words if word]
    
    if len(lengths) == 1:
        enumeration = f"({lengths[0]})"
    else:
        enumeration = f"({','.join(lengths)})"
    
    return f"{clue.strip()} {enumeration}"


def calculate_length(answer: str) -> int:
    """Calculate total letter count in answer (ignoring spaces/hyphens).
    
    Args:
        answer: The answer word/phrase
    
    Returns:
        Integer count of letters only
    """
    # Remove all non-letter characters
    letters_only = re.sub(r'[^A-Za-z]', '', answer)
    return len(letters_only)


def generate_reveal_order(answer: str) -> List[int]:
    """Generate shuffled list of indices for progressive reveal.
    
    Args:
        answer: The answer word/phrase
    
    Returns:
        Shuffled list of integers representing character indices
    """
    # Get only letter positions (skip spaces/hyphens)
    letters_only = re.sub(r'[^A-Za-z]', '', answer)
    indices = list(range(len(letters_only)))
    random.shuffle(indices)
    return indices


def generate_clue_id(answer: str, puzzle_date: Optional[str], source: str) -> str:
    """Generate unique ID for a clue.
    
    Args:
        answer: The answer word
        puzzle_date: Optional puzzle date
        source: Source publication
    
    Returns:
        Unique identifier string
    """
    # Use puzzle_date if available, otherwise generate hash
    if puzzle_date:
        # Format: source_date_answer (e.g., "times_20190808_COVETOUS")
        clean_date = re.sub(r'[^0-9]', '', puzzle_date)
        clean_source = re.sub(r'[^a-z0-9]', '', source.lower())
        return f"{clean_source}_{clean_date}_{answer}"
    else:
        # Generate hash-based ID
        hash_input = f"{source}_{answer}".encode('utf-8')
        hash_hex = hashlib.md5(hash_input).hexdigest()[:12]
        return f"{source.lower().replace(' ', '_')}_{hash_hex}_{answer}"


# ============================================================================
# PRIORITY ABBREVIATIONS (Top 50 - for reference in reverse-engineering)
# ============================================================================
PRIORITY_ABBREVIATIONS = {
    # Roman numerals
    "I": "1", "V": "5", "X": "10", "L": "50", "C": "100", "D": "500", "M": "1000",
    # Common elements
    "H": "hydrogen", "O": "oxygen", "N": "nitrogen", "C": "carbon",
    "AU": "gold", "AG": "silver", "FE": "iron", "PB": "lead", "CU": "copper",
    # Directions
    "N": "north", "S": "south", "E": "east", "W": "west", "L": "left", "R": "right/take",
    # Music
    "P": "piano/soft", "F": "forte/loud", "PP": "very soft", "FF": "very loud",
    # Chess
    "K": "king", "Q": "queen", "B": "bishop", "N": "knight", "R": "rook",
    # Titles
    "DR": "doctor", "MO": "doctor", "MP": "member of parliament", "QC": "barrister", "PM": "prime minister",
    # Academic
    "BA": "degree", "MA": "degree", "BSC": "degree",
    # Units
    "T": "ton", "M": "meter/mile", "G": "gram", "OZ": "ounce", "LB": "pound",
    "S": "second", "HR": "hour", "MIN": "minute",
}


@dataclass
class HoClueResult:
    """Result of processing a George Ho dataset clue."""
    
    # Compatibility fields (for app integration)
    id: str
    clue: str  # Clue with enumeration ensured
    length: int  # Total letter count
    reveal_order: List[int]  # Shuffled indices for progressive reveal
    
    # Original data
    original_clue: str
    answer: str
    original_definition: Optional[str]
    source: str
    source_url: Optional[str]
    puzzle_date: Optional[str]
    is_reviewed: bool
    
    # Reverse-engineered components
    clue_type: str
    fodder: str
    indicator: str
    mechanism: str
    wordplay_parts: Dict[str, str]  # {"type", "fodder", "indicator", "mechanism"}
    
    # Enrichment
    explanation: Dict[str, object]  # Nested dict: {"hints": {"indicators", "fodder", "definition"}, "full_breakdown": str}
    
    # Audit metrics
    ximenean_score: float
    difficulty_level: int
    narrative_fidelity: float
    
    # Processing metadata
    processing_timestamp: str
    logic_model: str
    surface_model: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization, mapping to main.py schema."""
        d = asdict(self)
        # Map answer → word
        d['word'] = d.pop('answer')
        # Add passed field (ximenean_score > 0.7)
        d['passed'] = d['ximenean_score'] > 0.7
        # Remove fields not in main.py output if needed
        # (optionally, keep all for compatibility)
        return d


class ReverseEngineerAgent:
    """Deconstructs professional cryptic clues using Logic Tier reasoning."""
    
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    
    def __init__(self, timeout: float = 60.0):
        """Initialize the Reverse-Engineer Agent with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 60.0 for complex reasoning).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        self.model_id = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID"))
        
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment variables")
        
        self.client = Portkey(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            timeout=timeout
        )
        
        logger.info(f"ReverseEngineerAgent initialized with model: {self.model_id} [LOGIC tier]")
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract JSON object from response text using first/last brace method.
        
        Args:
            response_text: The raw response text from the LLM.
        
        Returns:
            Parsed JSON dictionary or None if extraction fails.
        """
        try:
            # Method 1: Try direct JSON parse
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Method 2: Extract text between first { and last }
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = response_text[first_brace:last_brace + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Method 3: Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        logger.error(f"Failed to extract JSON from response: {response_text[:200]}")
        return None
    
    def deconstruct_clue(self, clue: str, answer: str, original_definition: Optional[str] = None) -> Optional[Dict]:
        """Reverse-engineer a cryptic clue to identify its components.
        
        Args:
            clue: The cryptic clue text.
            answer: The answer word.
            original_definition: The original definition from the dataset (if available).
        
        Returns:
            Dictionary with clue_type, definition, fodder, indicator, mechanism.
        """
        logger.info(f"Deconstructing: '{clue}' -> {answer}")
        
        # Build the prompt with Top 50 Abbreviations reference
        abbrev_reference = "\n".join([f"- {k}: {v}" for k, v in sorted(PRIORITY_ABBREVIATIONS.items())])
        
        system_prompt = """
You are a master cryptic crossword solver and deconstructor. Your task is to reverse-engineer professional cryptic clues by identifying their mechanical components and outputting a JSON object with these fields:

1. **clue_type**: The primary cryptic mechanism (Anagram, Hidden, Charade, Container, Reversal, Double Definition, Homophone, Acrostic, Exterior Letters, etc.)
2. **definition**: The part of the clue that defines the answer (must match original_definition if provided)
3. **fodder**: A comma-separated list of words or phrases from the clue that provide the raw material for wordplay - MUST be verbatim substrings from the original clue text (NO abbreviations, NO parenthetical notations, NO mechanical instructions)
4. **indicator**: The instruction word(s) that signal the cryptic operation (must be verbatim from the clue)
5. **mechanism**: A clear explanation of how the wordplay produces the answer - ALL logical transformations, abbreviations, and arithmetic operations go here
6. **wordplay_parts**: An object with the following fields:
     - type: The clue_type
     - fodder: The verbatim fodder (see above)
     - indicator: The verbatim indicator (see above)
     - mechanism: A concise mathematical or logical description (e.g., "sounds like 'rays'" or "Reverse(yard [YD] containing weak [POOR])")

CRITICAL HARDENING RULES (STRICT EVIDENCE-BASED LITERALISM):

- The fodder and indicator fields in both the root and wordplay_parts must ONLY contain exact words or phrases found in the original clue (no abbreviations, no transformations, no mechanical instructions, no synonyms, no parentheticals).
- The mechanism field in wordplay_parts must be a concise, explicit mathematical or logical description of the wordplay (e.g., "Reverse(yard [YD] containing weak [POOR])").
- The root mechanism field must show the full step-by-step logic, including all abbreviations and transformations.
- All other hardening and logic rules from previous instructions still apply.

OUTPUT FORMAT: Respond with ONLY a JSON object (no markdown, no explanations):
{
    "clue_type": "...",
    "definition": "...",
    "fodder": "...",
    "indicator": "...",
    "mechanism": "...",
    "wordplay_parts": {
        "type": "...",
        "fodder": "...",
        "indicator": "...",
        "mechanism": "..."
    }
}
"""

        # Build user prompt with optional original_definition
        definition_context = ""
        if original_definition:
            definition_context = f"\nORIGINAL_DEFINITION (IMMUTABLE ANCHOR): \"{original_definition}\"\n** You MUST use this exact definition in your JSON output. Do not redefine or reinterpret it. **\n"
        
        user_prompt = f"""Deconstruct this professional cryptic clue:

CLUE: "{clue}"
ANSWER: {answer} ({len(answer)}){definition_context}

TOP 50 CRYPTIC ABBREVIATIONS (for reference):
{abbrev_reference}

Analyze the clue following the MANDATORY LOGIC PRIORITY ORDER and provide the JSON breakdown."""

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Low temperature for precise analysis
                max_tokens=1000
            )
            
            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from Logic Tier")
                return None
            
            choice = response.choices[0]
            response_text = None
            
            # Extract response text
            if hasattr(choice, 'text') and isinstance(choice.text, str):
                response_text = choice.text
            elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                if isinstance(choice.message.content, str):
                    response_text = choice.message.content
                elif isinstance(choice.message.content, list):
                    for content_part in choice.message.content:
                        if hasattr(content_part, 'text'):
                            response_text = content_part.text
                            break
            
            if not response_text:
                logger.error("Could not extract response text")
                return None
            
            # Parse JSON from response
            result = self._extract_json_from_response(response_text)
            
            if not result:
                logger.error(f"Failed to parse JSON from response for '{answer}'")
                return None
            
            # Validate required fields
            required_fields = ["clue_type", "definition", "fodder", "indicator", "mechanism"]
            missing_fields = [f for f in required_fields if f not in result]
            
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return None
            
            logger.info(f"Successfully deconstructed '{answer}' as {result['clue_type']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in deconstruct_clue for '{answer}': {e}")
            return None


class ExplanationAgent:
    """Generates user-friendly explanations using Surface Tier."""
    
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    
    def __init__(self, timeout: float = 30.0):
        """Initialize the Explanation Agent with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 30.0).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        self.model_id = os.getenv("SURFACE_MODEL_ID", os.getenv("MODEL_ID"))
        
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment variables")
        
        self.client = Portkey(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            timeout=timeout
        )
        
        logger.info(f"ExplanationAgent initialized with model: {self.model_id} [SURFACE tier]")
    

    def generate_explanation(self, clue: str, answer: str, breakdown: Dict) -> Dict[str, object]:
        """Generate a nested explanation dict for a deconstructed clue.
        Args:
            clue: The cryptic clue text.
            answer: The answer word.
            breakdown: Dictionary with clue_type, definition, fodder, indicator, mechanism.
        Returns:
            Dict with keys: 'hints' (dict) and 'full_breakdown' (str).
        """
        logger.info(f"Generating explanation for '{answer}' (nested schema)")

        system_prompt = '''You are a cryptic crossword explainer. Generate a JSON object with this structure:
{
  "hints": {
    "indicators": "Explain the indicator word(s) (e.g., 'back', 'upset'), or explain why there is no indicator (e.g., in Double Definitions).",
    "fodder": "Describe the raw material being manipulated, using only verbatim words/phrases from the clue (no abbreviations or mechanical instructions).",
    "definition": "Give a gentle, guided hint toward the definition, without giving away the answer."
  },
  "full_breakdown": "A warm, encouraging prose explanation that walks through the magic of how the clue works, weaving in the mechanism/formula."
}

Rules:
- 'fodder' must use only exact words/phrases from the clue (verbatim, no abbreviations).
- 'indicators' must explain the indicator word(s) or why none is present.
- 'definition' must nudge the solver toward the definition, not give it away.
- 'full_breakdown' should be a friendly, detailed walkthrough, referencing the mechanism and showing how the answer is constructed.

EXAMPLES:
For a reversal clue:
{
  "hints": {
    "indicators": "The word 'Back' is our engine here; it tells us to reverse the entire sequence that follows.",
    "fodder": "Our raw materials are 'yard' and 'weak'.",
    "definition": "The definition is 'sagging'. Think of something that loses its shape and hangs down low."
  },
  "full_breakdown": "This is a clever reversal! We take 'yard' (abbreviated as YD) and wrap it around 'weak' (POOR). When we take that combined unit (YD+POOR) and follow the instruction to go 'Back', it flips into DROOPY!"
}

For a double definition:
{
  "hints": {
    "indicators": "Notice how there's no traditional indicator word here like 'anagram' or 'hidden in' – that's the key! In a double definition clue, both parts of the clue point directly at the answer from different angles. No wordplay machinery needed; just two separate meanings that converge on one perfect word.",
    "fodder": "Watch out – there's no 'fodder' to manipulate in the traditional sense! Double definition clues work differently from anagrams or hidden words. The entire clue IS the definition material. We're not rearranging letters or extracting hidden sequences; we're finding a single word that satisfies two completely different meanings.",
    "definition": "Our definition here is 'Two definitions: 'gentle/loving' and 'offer/bid''. The beauty of this clue is that one word bridges both meanings perfectly. Think about a word that can mean something soft and caring in one context, and a proposal or presentation of terms in another."
  },
  "full_breakdown": "This is such an elegant clue! Let's see how it works. You have TWO definitions stacked together: 'Gentle' (suggesting something soft, caring, loving) and 'offer' (suggesting a bid, a proposal, something presented). The magic of a double definition clue is finding one word that genuinely lives in both worlds. TENDER does exactly this! 'Tender' means gentle or affectionate ('tender loving care'), but it also means to offer or submit something formally ('tender a bid' or 'tender a resignation'). There's no anagram, no hidden letters, no indicators – just the elegant wordplay of one word carrying two legitimate, unrelated meanings. Cryptic setters love these because they reward solvers who think about words from multiple angles at once. Your job is simply to find the word where both definitions click into place."
}

Always return only the JSON object above, with all fields populated.
'''

        user_prompt = f'''Generate a cryptic clue explanation in the above JSON format.

CLUE: "{clue}"
ANSWER: {answer}

BREAKDOWN:
- Type: {breakdown['clue_type']}
- Definition: {breakdown['definition']}
- Fodder: {breakdown['fodder']}
- Indicator: {breakdown['indicator']}
- Mechanism: {breakdown['mechanism']}
'''

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )

            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from Surface Tier")
                return {"hints": {"indicators": "Unavailable", "fodder": "Unavailable", "definition": "Unavailable"}, "full_breakdown": "Explanation unavailable"}

            choice = response.choices[0]
            response_text = None

            # Extract response text
            if hasattr(choice, 'text') and isinstance(choice.text, str):
                response_text = choice.text
            elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                if isinstance(choice.message.content, str):
                    response_text = choice.message.content
                elif isinstance(choice.message.content, list):
                    for content_part in choice.message.content:
                        if hasattr(content_part, 'text'):
                            response_text = content_part.text
                            break

            if not response_text:
                logger.error("Could not extract response text")
                return {"hints": {"indicators": "Unavailable", "fodder": "Unavailable", "definition": "Unavailable"}, "full_breakdown": "Explanation unavailable"}

            # Parse JSON from response
            result_json = self._extract_json_from_response(response_text)

            if result_json and "hints" in result_json and "full_breakdown" in result_json:
                return result_json
            else:
                logger.error("Failed to parse explanation JSON")
                return {"hints": {"indicators": "Unavailable", "fodder": "Unavailable", "definition": "Unavailable"}, "full_breakdown": "Explanation unavailable"}

        except Exception as e:
            logger.error(f"Error in generate_explanation for '{answer}': {e}")
            return {"hints": {"indicators": "Unavailable", "fodder": "Unavailable", "definition": "Unavailable"}, "full_breakdown": "Explanation unavailable"}

        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            if not response.choices or len(response.choices) == 0:
                logger.error("Empty response from Surface Tier")
                return ("Hint unavailable", "Explanation unavailable")
            
            choice = response.choices[0]
            response_text = None
            
            # Extract response text
            if hasattr(choice, 'text') and isinstance(choice.text, str):
                response_text = choice.text
            elif hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                if isinstance(choice.message.content, str):
                    response_text = choice.message.content
                elif isinstance(choice.message.content, list):
                    for content_part in choice.message.content:
                        if hasattr(content_part, 'text'):
                            response_text = content_part.text
                            break
            
            if not response_text:
                logger.error("Could not extract response text")
                return ("Hint unavailable", "Explanation unavailable")
            
            # Parse JSON from response
            result_json = self._extract_json_from_response(response_text)
            
            if result_json and "hint" in result_json and "explanation" in result_json:
                return (result_json["hint"], result_json["explanation"])
            else:
                logger.error("Failed to parse explanation JSON")
                return ("Hint unavailable", "Explanation unavailable")
            
        except Exception as e:
            logger.error(f"Error in generate_explanation for '{answer}': {e}")
            return ("Hint unavailable", "Explanation unavailable")
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict]:
        """Extract JSON object from response text."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Extract text between first { and last }
        first_brace = response_text.find('{')
        last_brace = response_text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = response_text[first_brace:last_brace + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        return None


class HoProcessor:
    """Main processor for George Ho dataset enrichment."""
    
    def __init__(self):
        """Initialize the processor with all agents."""
        self.reverse_engineer = ReverseEngineerAgent()
        self.explainer = ExplanationAgent()
        self.auditor = XimeneanAuditor()
    
    def load_dataset(self, filepath: str, source_filter: Optional[str] = None,
                     reviewed_only: bool = False, limit: Optional[int] = None,
                     random_sample: bool = False) -> List[Dict]:
        """Load and filter the George Ho dataset.
        
        Args:
            filepath: Path to the CSV or JSON file.
            source_filter: Filter by source name (e.g., "times_xwd_times").
            reviewed_only: Only include clues where is_reviewed == 1.
            limit: Maximum number of clues to process.
            random_sample: Shuffle dataset before sampling.
        
        Returns:
            List of clue dictionaries.
        """
        import csv
        
        logger.info(f"Loading dataset from: {filepath}")
        
        clues = []
        
        try:
            # Try CSV format first
            if filepath.endswith('.csv'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        clues.append(row)
            # Try JSON format
            elif filepath.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        clues = data
                    elif isinstance(data, dict) and 'clues' in data:
                        clues = data['clues']
            else:
                raise ValueError("Unsupported file format. Use .csv or .json")
            
            logger.info(f"Loaded {len(clues)} clues from dataset")
            
            # Apply filters
            if source_filter:
                clues = [c for c in clues if c.get('source', '').lower() == source_filter.lower()]
                logger.info(f"Filtered to {len(clues)} clues from source: {source_filter}")
            
            if reviewed_only:
                # Only filter if is_reviewed field exists and is explicitly set to 1
                clues = [c for c in clues if str(c.get('is_reviewed', '0')) == '1']
                logger.info(f"Filtered to {len(clues)} reviewed clues")
                if len(clues) == 0:
                    logger.warning("No reviewed clues found. Dataset may not have 'is_reviewed' field or all are unreviewed.")
                    logger.warning("Try running without --reviewed-only flag.")
            
            # Clean clues (handle missing enumerations)
            clues = [self._clean_clue(c) for c in clues]
            
            # Random sampling
            if random_sample:
                import random
                random.shuffle(clues)
                logger.info("Dataset shuffled for random sampling")
            
            # Apply limit
            if limit and limit < len(clues):
                clues = clues[:limit]
                logger.info(f"Limited to {limit} clues")
            
            return clues
            
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            return []
    
    def _clean_clue(self, clue_dict: Dict) -> Dict:
        """Clean a clue entry by handling machine errors.
        
        Args:
            clue_dict: Raw clue dictionary from dataset.
        
        Returns:
            Cleaned clue dictionary.
        """
        # Handle missing enumeration in clue text
        clue_text = clue_dict.get('clue', '')
        answer = clue_dict.get('answer', '')
        
        # If clue doesn't end with enumeration pattern like (5) or (3,4)
        if answer and not re.search(r'\(\d+(?:,\d+)*\)$', clue_text.strip()):
            # Calculate enumeration from answer
            enum = str(len(answer))
            clue_dict['clue'] = f"{clue_text.strip()} ({enum})"
            logger.debug(f"Added missing enumeration to: {clue_text[:50]}")
        
        return clue_dict
    
    def process_clue(self, clue_dict: Dict) -> Optional[HoClueResult]:
        """Process a single clue through the full pipeline.
        
        Args:
            clue_dict: Dictionary with clue, answer, and metadata.
        
        Returns:
            HoClueResult or None if processing failed.
        """
        clue = clue_dict.get('clue', '')
        answer = clue_dict.get('answer', '')
        
        if not clue or not answer:
            logger.warning("Skipping clue with missing clue or answer")
            return None
        
        logger.info(f"Processing: {clue} -> {answer}")
        
        try:
            # Step 1: Reverse-engineer the clue with original definition anchor
            breakdown = self.reverse_engineer.deconstruct_clue(
                clue=clue,
                answer=answer,
                original_definition=clue_dict.get('definition')
            )
            
            if not breakdown:
                logger.warning(f"Failed to deconstruct clue: {clue}")
                return None
            
            # Step 2: Generate explanations (nested dict)
            explanation = self.explainer.generate_explanation(clue, answer, breakdown)
            
            # Step 3: Audit for metrics
            # Build clue_json in format expected by auditor
            clue_json = {
                "clue": clue,
                "answer": answer,
                "definition": clue_dict.get('definition', ''),
                "type": breakdown['clue_type'],
                "wordplay_parts": {
                    "fodder": breakdown['fodder'],
                    "indicator": breakdown['indicator'],
                    "mechanism": breakdown['mechanism']
                }
            }
            
            audit_result = self.auditor.audit_clue(clue_json)
            
            # Step 4: Generate compatibility fields
            clue_with_enum = ensure_enumeration(clue, answer)
            clue_length = calculate_length(answer)
            clue_reveal_order = generate_reveal_order(answer)
            clue_id = generate_clue_id(
                answer=answer,
                puzzle_date=clue_dict.get('puzzle_date'),
                source=clue_dict.get('source', 'unknown')
            )
            
            # Step 5: Build result object
            # Map wordplay_parts from breakdown (Logic Tier)
            wordplay_parts = breakdown.get('wordplay_parts', {
                'type': breakdown.get('clue_type', ''),
                'fodder': breakdown.get('fodder', ''),
                'indicator': breakdown.get('indicator', ''),
                'mechanism': breakdown.get('mechanism', '')
            })

            # Map ximenean_score to passed (main.py: >0.7 is pass)
            passed = audit_result.ximenean_score > 0.7

            result = HoClueResult(
                # Compatibility fields
                id=clue_id,
                clue=clue_with_enum,
                length=clue_length,
                reveal_order=clue_reveal_order,
                # Original data
                original_clue=clue,
                answer=answer,
                original_definition=clue_dict.get('definition'),
                source=clue_dict.get('source', 'unknown'),
                source_url=clue_dict.get('source_url'),
                puzzle_date=clue_dict.get('puzzle_date'),
                is_reviewed=str(clue_dict.get('is_reviewed', '0')) == '1',
                # Reverse-engineered components
                clue_type=breakdown['clue_type'],
                fodder=breakdown['fodder'],
                indicator=breakdown['indicator'],
                mechanism=breakdown['mechanism'],
                wordplay_parts=wordplay_parts,
                # Enrichment
                explanation=explanation,
                # Audit metrics
                ximenean_score=audit_result.ximenean_score,
                difficulty_level=audit_result.difficulty_level,
                narrative_fidelity=audit_result.narrative_fidelity,
                # Processing metadata
                processing_timestamp=datetime.now().isoformat(),
                logic_model=self.reverse_engineer.model_id,
                surface_model=self.explainer.model_id
            )
            
            logger.info(f"✓ Successfully processed: {answer} (Ximenean: {audit_result.ximenean_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error processing clue '{answer}': {e}")
            return None
    
    def process_batch(self, clues: List[Dict]) -> List[HoClueResult]:
        """Process a batch of clues.
        
        Args:
            clues: List of clue dictionaries.
        
        Returns:
            List of successfully processed HoClueResults.
        """
        results = []
        
        for i, clue_dict in enumerate(clues, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing clue {i}/{len(clues)}")
            logger.info(f"{'='*60}")
            
            result = self.process_clue(clue_dict)
            
            if result:
                results.append(result)
            else:
                logger.warning(f"Skipped clue {i} due to processing error")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Batch processing complete: {len(results)}/{len(clues)} successful")
        logger.info(f"{'='*60}")
        
        return results
    
    def save_results(self, results: List[HoClueResult], output_path: Optional[str] = None):
        """Save processed results to JSON file.
        
        Args:
            results: List of HoClueResults.
            output_path: Optional custom output path. If None, generates timestamped filename.
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"ho_enriched_{timestamp}.json"
        
        # Convert results to dictionaries
        output_data = {
            "metadata": {
                "source_dataset": "George Ho Cryptics (https://cryptics.georgeho.org/)",
                "processing_timestamp": datetime.now().isoformat(),
                "total_clues": len(results),
                "logic_model": results[0].logic_model if results else "unknown",
                "surface_model": results[0].surface_model if results else "unknown"
            },
            "clues": [r.to_dict() for r in results]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✓ Saved {len(results)} enriched clues to: {output_path}")
        
        # Print summary statistics
        if results:
            avg_ximenean = sum(r.ximenean_score for r in results) / len(results)
            avg_difficulty = sum(r.difficulty_level for r in results) / len(results)
            avg_narrative = sum(r.narrative_fidelity for r in results) / len(results)
            
            logger.info(f"\nSUMMARY STATISTICS:")
            logger.info(f"  Average Ximenean Score: {avg_ximenean:.2f}")
            logger.info(f"  Average Difficulty: {avg_difficulty:.1f}/5")
            logger.info(f"  Average Narrative Fidelity: {avg_narrative:.1f}%")
            
            # Clue type distribution
            type_counts = {}
            for r in results:
                type_counts[r.clue_type] = type_counts.get(r.clue_type, 0) + 1
            
            logger.info(f"\nCLUE TYPE DISTRIBUTION:")
            for clue_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"  {clue_type}: {count}")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Enrich George Ho cryptic dataset with wordplay explanations and metrics"
    )
    
    parser.add_argument(
        'dataset',
        help="Path to George Ho dataset CSV or JSON file"
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help="Maximum number of clues to process (default: 10)"
    )
    
    parser.add_argument(
        '--random',
        action='store_true',
        help="Shuffle dataset before sampling (for diverse samples)"
    )
    
    parser.add_argument(
        '--source',
        help="Filter by source name (e.g., 'times_xwd_times', 'guardian')"
    )
    
    parser.add_argument(
        '--reviewed-only',
        action='store_true',
        help="Only process clues where is_reviewed == 1"
    )
    
    parser.add_argument(
        '--output',
        help="Custom output filename (default: ho_enriched_TIMESTAMP.json)"
    )
    
    args = parser.parse_args()
    
    # Check if dataset file exists
    if not os.path.exists(args.dataset):
        logger.error(f"Dataset file not found: {args.dataset}")
        sys.exit(1)
    
    # Initialize processor
    processor = HoProcessor()
    
    # Load dataset with filters
    clues = processor.load_dataset(
        filepath=args.dataset,
        source_filter=args.source,
        reviewed_only=args.reviewed_only,
        limit=args.limit,
        random_sample=args.random
    )
    
    if not clues:
        logger.error("No clues to process after filtering")
        sys.exit(1)
    
    logger.info(f"\nProcessing {len(clues)} clues from George Ho dataset")
    
    # Process batch
    results = processor.process_batch(clues)
    
    if not results:
        logger.error("No clues were successfully processed")
        sys.exit(1)
    
    # Save results
    processor.save_results(results, args.output)
    
    logger.info("\n✓ Processing complete!")


if __name__ == "__main__":
    main()
