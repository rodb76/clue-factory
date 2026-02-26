"""
Setter Agent: Generates Ximenean cryptic clues using Portkey AI.

This module implements the "Setter" component of the cryptic clue generation system.
It uses the Portkey AI Gateway to interface with Claude 3.5 Sonnet for creating
clues that adhere to Ximenean standards (definition + fair wordplay + nothing else).
"""

import asyncio
import sys
import os
import json
import logging
from typing import Optional
from dotenv import load_dotenv

# Fix: Force Windows to use the correct event loop policy
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Configure logging
# Note: logging.basicConfig() should only be called in the main entry point (main.py)
# to avoid duplicate handlers when modules are imported
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

from portkey_ai import Portkey


# PRIORITY CRYPTIC ABBREVIATIONS (Top 50 - Standard Crossword Fair)
# These are widely recognized and defensible via Wikipedia/standard dictionaries
PRIORITY_ABBREVIATIONS = {
    # Roman Numerals (Universal)
    "I": ["one"],
    "V": ["five"],
    "X": ["ten"],
    "L": ["fifty"],
    "C": ["hundred"],
    "D": ["five hundred"],
    "M": ["thousand"],
    "XI": ["team", "eleven"],
    
    # Common Chemical Elements (Standard)
    "H": ["hydrogen", "gas"],
    "O": ["oxygen", "love", "duck", "nothing"],
    "N": ["nitrogen", "north", "knight"],
    "C": ["carbon"],
    "AU": ["gold"],
    "AG": ["silver"],
    "FE": ["iron"],
    "PB": ["lead"],
    "CU": ["copper"],
    
    # Direction/Navigation (Universal)
    "N": ["north"],
    "S": ["south"],
    "E": ["east"],
    "W": ["west"],
    "L": ["left"],
    "R": ["right"],
    
    # Music/Sound (Standard)
    "P": ["piano", "soft", "quiet"],
    "F": ["forte", "loud"],
    "PP": ["very soft"],
    "FF": ["very loud"],
    
    # Chess Pieces (Standard)
    "K": ["king"],
    "Q": ["queen"],
    "B": ["bishop"],
    "N": ["knight"],
    "R": ["rook"],
    
    # Titles/Professions (Common)
    "DR": ["doctor"],
    "MO": ["doctor", "medic"],
    "MP": ["politician", "military police"],
    "QC": ["lawyer", "silk"],
    "PM": ["minister", "leader"],
    
    # Academic/Learning (Standard)
    "L": ["learner", "student"],
    "BA": ["graduate", "degree"],
    "MA": ["master", "degree"],
    "BSC": ["graduate"],
    
    # Units/Measures (Common)
    "T": ["time", "ton"],
    "M": ["metre", "mile"],
    "G": ["gram"],
    "OZ": ["ounce"],
    "LB": ["pound"],
    "S": ["second"],
    "HR": ["hour"],
    "MIN": ["minute"],
    
    # Common Single Letters (Universal)
    "A": ["one", "ace", "article"],
    "I": ["one", "eye"],
    "O": ["nothing", "love"],
    "U": ["university", "you"],
    "V": ["very", "five"],
    "Y": ["year", "unknown"],
    "Z": ["sleep"],
}

# EXTENDED CRYPTIC ABBREVIATIONS (Less Common - Use Cautiously)
# These are valid but less standard - prefer PRIORITY_ABBREVIATIONS when possible
EXTENDED_ABBREVIATIONS = {
    "EN": ["in", "nurse"],  # Less common, prefer "N" for "in"
    "RE": ["about", "soldier"],
    "RA": ["artist", "gunner"],
    "GI": ["soldier", "american"],
    "CA": ["about", "california"],
    "CH": ["church", "switzerland"],
    "LA": ["note", "los angeles"],
    "TE": ["note"],
    "DIT": ["signal"],  # Obscure - avoid
    "DAH": ["signal"],  # Obscure - avoid
}

# COMBINED REFERENCE (for lookup)
CRYPTIC_ABBREVIATIONS = {**PRIORITY_ABBREVIATIONS, **EXTENDED_ABBREVIATIONS}
# COMBINED REFERENCE (for lookup)
CRYPTIC_ABBREVIATIONS = {**PRIORITY_ABBREVIATIONS, **EXTENDED_ABBREVIATIONS}


class SetterAgent:
    """
    Setter Agent responsible for generating Ximenean cryptic clues.
    
    Uses Portkey AI Gateway to communicate with Claude 3.5 Sonnet.
    """
    
    # Configuration constants
    BASE_URL = "https://eu.aigw.galileo.roche.com/v1"
    # Inverted Model Tiering: Use stronger model for logic, cheaper for surface
    LOGIC_MODEL_ID = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID"))  # Wordplay generation
    SURFACE_MODEL_ID = os.getenv("SURFACE_MODEL_ID", os.getenv("MODEL_ID"))  # Surface writing
    MODEL_ID = LOGIC_MODEL_ID  # Default to logic model for backward compatibility
    
    def __init__(self, timeout: float = 30.0, temperature: float = 0.5):
        """Initialize the Setter Agent with Portkey client.
        
        Args:
            timeout: Request timeout in seconds (default: 30.0).
            temperature: Temperature for generation (0.0-1.0, default: 0.5).
        """
        self.api_key = os.getenv("PORTKEY_API_KEY")
        self.temperature = temperature
        
        if not self.api_key:
            raise ValueError(
                "PORTKEY_API_KEY environment variable not set. "
                "Please set it before initializing the Setter Agent."
            )
        
        # Initialize Portkey client with explicit base_url and api_key
        self.client = Portkey(
            api_key=self.api_key,
            base_url=self.BASE_URL,
            timeout=timeout
        )
        
        logger.info(f"Setter Agent initialized (temperature: {self.temperature})")
        logger.info(f"  Logic model (wordplay): {self.LOGIC_MODEL_ID}")
        logger.info(f"  Surface model (clue text): {self.SURFACE_MODEL_ID}")
    
    def _extract_response_text(self, response) -> str:
        """
        Extract text content from Portkey API response.
        
        Handles various response formats from the Portkey Gateway.
        
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
    
    def generate_wordplay_only(
        self,
        answer: str,
        clue_type: str,
        retry_feedback: Optional[str] = None
    ) -> dict:
        """
        STEP 1: Generate ONLY the wordplay components (fodder, indicator, mechanism).
        
        This allows mechanical validation BEFORE generating the full surface reading,
        improving success rates dramatically.
        
        Args:
            answer: The target word.
            clue_type: Type of clue to generate.
            retry_feedback: Optional feedback from failed mechanical validation.
        
        Returns:
            Dictionary with wordplay_parts only (fodder, indicator, mechanism, type).
        """
        
        retry_context = ""
        if retry_feedback:
            retry_context = f"\n\nPREVIOUS ATTEMPT FAILED:\n{retry_feedback}\n\nPlease correct this in your new attempt."
        
        system_prompt = """You are a Ximenean cryptic crossword wordplay generator. 
Your job is to generate ONLY the mechanical wordplay components - NOT a full clue yet.

Focus on creating technically sound wordplay that will pass mechanical validation.

FEW-SHOT EXAMPLES - GOLD STANDARD (Classic Ximenean Economy):

Anagram Example:
{"wordplay_parts": {"fodder": "dirty room", "indicator": "confused", "mechanism": "anagram of 'dirty room'"}, "definition_hint": "dormitory"}
Classic Surface: "Confused dirty room (9)" → DORMITORY
Note: Perfect 1:1 ratio - no filler words needed.

Hidden Word Example:
{"wordplay_parts": {"fodder": "illusionist", "indicator": "disguises", "mechanism": "hidden in 'il[LUSI]onist'"}, "definition_hint": "dead giveaway"}
Classic Surface: "How illusionist disguises a dead giveaway? (4)" → LUSI (illustrative)
Note: "disguises" serves as both indicator AND thematic anchor.

Container Example:
{"wordplay_parts": {"outer": "PAT", "inner": "IN", "indicator": "grips", "mechanism": "IN inside PAT"}, "definition_hint": "To apply color", "target_answer": "PAINT"}

Reversal Example:
{"wordplay_parts": {"fodder": "lager", "indicator": "returned", "mechanism": "reverse of lager"}, "definition_hint": "majestic"}
Classic Surface: "Majestic lager returned (5)" → REGAL
Note: Zero filler - surface implies drink being sent back, cryptic reading reverses letters.

Follow these Gold Standard examples: build with ONLY definition + fodder + indicator, then add words ONLY if thematically necessary."""

        user_prompt = f"""Generate the wordplay components for answer "{answer.upper()}" using type "{clue_type}".{retry_context}

Return ONLY JSON (no other text) with this structure:
{{
    "wordplay_parts": {{
        "type": "{clue_type}",
        "fodder": "The exact letters/words to manipulate",
        "indicator": "The word that signals the operation",
        "mechanism": "How the wordplay produces {answer.upper()}"
    }},
    "definition_hint": "What the answer means (for later surface generation)"
}}

CRITICAL RULES BY TYPE:
- Anagram: (1) fodder must contain EXACTLY the same letters as {answer.upper()}. (2) ALL ANAGRAM FODDER MUST CONSIST OF REAL, COMMON ENGLISH WORDS. You are STRICTLY FORBIDDEN from using partial words, non-dictionary abbreviations, or random letter strings to balance an anagram. Examples: 'dirty room' → DORMITORY ✓ (both real words), 'sing ro' → ROUSING ✗ ('ro' is not a word), 'tame sng' → MAGENTS ✗ ('sng' is gibberish). Every word in your fodder will be validated against an English dictionary. (3) IDENTITY CONSTRAINT: The answer '{answer.upper()}' (or any variant like '{answer.upper()}S', '{answer.upper()}ED') MUST NOT appear anywhere in the fodder. The fodder must consist of completely different words.
- Hidden Word: MANDATORY: You must verify the spelling by placing brackets around the hidden answer in your 'mechanism' string. Example for 'AORTA': 'found in r[ADIO ORTA]rio'. If the letters are not consecutive, it is a FAIL. The fodder must be real words/phrases. Verify character-by-character: {answer.upper()[0]}, {answer.upper()[1]}, {answer.upper()[2] if len(answer) > 2 else ''}, etc. IDENTITY CONSTRAINT: The answer must be concealed across at least TWO DIFFERENT WORDS, not hidden within a single word that IS the answer (e.g., 'PAINT' hidden in 'paint' is FORBIDDEN; 'PAINT' hidden in 'dePAINTed' is acceptable).
- Charade: parts must CONCATENATE to exactly {answer.upper()}
- Container: outer word must CONTAIN inner word to make {answer.upper()}. BOTH outer and inner words MUST be real English dictionary words (no gibberish like 'nettab').
- Reversal: The fodder word reversed must equal {answer.upper()}. CRITICAL: The fodder MUST be a real English dictionary word BEFORE reversal (e.g., 'lager' → REGAL is valid, but 'amhtsa' → ASTHMA is FORBIDDEN gibberish). If no real word reverses to form {answer.upper()}, you MUST pivot to a different mechanism (Charade, Hidden Word, etc.). IDENTITY CONSTRAINT: The fodder must not BE the answer itself (e.g., using 'STAR' reversed for the answer 'RATS' is lazy; find a different word like 'tsar' or use a different mechanism).

REAL-WORD DICTIONARY CONSTRAINT:
- For Reversals and Containers, every piece of fodder must be a valid English word found in a standard dictionary
- If reversing the answer produces a non-word (e.g., ASTHMA → 'amhtsa'), you MUST choose a different clue type
- Examples:
  * GOOD: 'lager' reversed = REGAL (both are real words)
  * GOOD: 'desserts' reversed = STRESSED (both are real words)
  * BAD: 'amhtsa' reversed = ASTHMA (amhtsa is gibberish - MUST use different mechanism)
  * BAD: 'nettab' reversed = BATTEN (nettab is gibberish - MUST use different mechanism)"""

        try:
            logger.info(f"Generating wordplay for '{answer}' (type: {clue_type}) [Model: LOGIC]")
            
            response = self.client.chat.completions.create(
                model=self.LOGIC_MODEL_ID,  # Use stronger model for mechanical wordplay
                max_tokens=300,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract response text
            response_text = self._extract_response_text(response)
            logger.info(f"Wordplay response received ({len(response_text)} chars)")
            
            # Parse JSON
            wordplay_data = self._parse_json_response(response_text)
            
            # Add answer and type
            wordplay_data["answer"] = answer.upper()
            wordplay_data["type"] = clue_type
            
            return wordplay_data
            
        except Exception as e:
            logger.error(f"Wordplay generation failed: {e}")
            raise
    
    def generate_surface_from_wordplay(
        self,
        wordplay_data: dict,
        answer: str
    ) -> dict:
        """
        STEP 2: Generate the full clue surface reading from validated wordplay.
        
        This runs AFTER mechanical validation has passed.
        
        Args:
            wordplay_data: The validated wordplay components.
            answer: The target word.
        
        Returns:
            Complete clue dictionary with surface reading.
        """
        
        wordplay_parts = wordplay_data.get("wordplay_parts", {})
        definition_hint = wordplay_data.get("definition_hint", "")
        
        system_prompt = """You are a Ximenean cryptic crossword surface writer following the 'Minimalist Lie' principle.
You receive validated wordplay components and create a deceptive, economical clue.

THE MINIMALIST LIE APPROACH:
1. Start with ONLY: Definition + Fodder + Indicator
2. Add words ONLY if required for a plausible, deceptive narrative (Thematic Necessity Test)
3. Every word must be justifiable in the cryptic reading

CRITICAL RULES:
1. STRICTLY use the exact fodder provided - NO synonyms allowed
2. Avoid literal connectors like 'gives', 'plus', 'becomes' - prefer grammatical links ('s, -ing)
3. Grammatical Integrity: The surface must read as coherent English
4. Prioritize economy over elaboration - fewer words = better clue

THE NO-GIBBERISH RULE (MANDATORY):
- NEVER include standalone letters or non-word fragments in the surface (e.g., "with en, treat, y" is FORBIDDEN)
- Single letters MUST be masked using PRIORITY cryptic abbreviations from TOP 50 list:
  * Roman numerals: I=one, V=five, X=ten, L=fifty, C=hundred, M=thousand
  * Elements: H=hydrogen/gas, O=oxygen/love, N=nitrogen/north, AU=gold, FE=iron
  * Directions: N=north, S=south, E=east, W=west, L=left, R=right
  * Music: P=piano/soft, F=forte/loud
  * Chess: K=king, Q=queen, B=bishop, N=knight
  * Titles: DR=doctor, MP=politician, MO=medic
  * Units: T=time/ton, M=metre, S=second, HR=hour

NO NON-WORDS AS FODDER (CRITICAL - DICTIONARY VALIDATION):
- Every piece of fodder MUST be a real English word found in standard dictionaries
- For reversals: Check BOTH directions - fodder word must be real BEFORE reversal
  * VALID: "lager" (real word) reversed = REGAL (real word) ✓
  * INVALID: "amhtsa" (gibberish) reversed = ASTHMA ✗
- For containers: BOTH outer and inner words must be dictionary-valid
  * VALID: IN inside PAT = PAINT (all real words) ✓
  * INVALID: "nettab" containing EN = BATTEN ✗
- MANDATORY: If reversal of answer produces gibberish, pivot to Charade/Hidden Word/Anagram
- Mechanical Fair Play: Every fodder word must be defensible via standard English dictionaries (Oxford, Merriam-Webster, etc.)

NARRATIVE MASKING:
- Choose substitutions that fit your thematic story
- Example: If solving chess clue, use "knight" for N, "king" for K
- Example: If geographic theme, use "north" for N, "east" for E
- The surface MUST read as a plausible English sentence, NOT a mechanical listing"""

        user_prompt = f"""Create a complete cryptic clue using these VALIDATED wordplay components:

Answer: {answer.upper()}
Type: {wordplay_parts.get('type')}
Fodder: {wordplay_parts.get('fodder')}
Indicator: {wordplay_parts.get('indicator')}
Mechanism: {wordplay_parts.get('mechanism')}
Definition hint: {definition_hint}

Return ONLY JSON with:
{{
    "clue": "Complete natural-reading clue",
    "definition": "The definition part",
    "explanation": "Full breakdown"
}}

MINIMALIST LIE Construction Process:
1. Start with: "{definition_hint}" + "{wordplay_parts.get('fodder')}" + "{wordplay_parts.get('indicator')}"
2. Test: Does this already form a plausible sentence?
3. If yes: STOP. You are done.
4. If no: Add ONLY the minimum words needed for deceptive narrative

STRICT Requirements:
- MANDATORY: Use the EXACT fodder words '{wordplay_parts.get('fodder')}' in the clue (no synonyms)
- Include the definition and ALL wordplay components naturally
- Make it read like a coherent English sentence
- Use ONLY horizontal indicators (no "rising", "up", "over", etc.)
- Don't explain the wordplay in the clue itself
- AVOID literal connectors ('gives', 'plus', 'becomes') - prefer grammatical links like possessives ('s)
- Aim for zero additional words; maximum 1-2 if thematically essential
- CRITICAL: You MUST use a synonym for the definition_hint '{definition_hint}' in the surface reading
- STRICTLY FORBIDDEN: You CANNOT use the word '{answer.upper()}' itself anywhere in the clue text

NO-GIBBERISH ENFORCEMENT:
- If fodder contains single letters (e.g., EN, Y, N), you MUST substitute with PRIORITY abbreviations from TOP 50
- FORBIDDEN: "with en, treat, y" or "found in n, e, w"
- REQUIRED: "from nurse, treat, year" or "within north, east, west"
- Check: Every token in your clue must be a real English word or standard phrase
- CRITICAL: No non-word fodder allowed - if "NETTAB" is needed, reject and use different mechanism"""

        try:
            logger.info(f"Generating surface for '{answer}' [Model: SURFACE]")
            
            response = self.client.chat.completions.create(
                model=self.SURFACE_MODEL_ID,  # Use cheaper model for creative surface writing
                max_tokens=300,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract response text
            response_text = self._extract_response_text(response)
            logger.info(f"Surface response received ({len(response_text)} chars)")
            
            # Parse JSON
            surface_data = self._parse_json_response(response_text)
            
            # Combine with wordplay data
            complete_clue = {
                "clue": surface_data.get("clue", ""),
                "definition": surface_data.get("definition", ""),
                "wordplay_parts": wordplay_parts,
                "explanation": surface_data.get("explanation", ""),
                "type": wordplay_parts.get("type"),
                "answer": answer.upper()
            }
            
            return complete_clue
            
        except Exception as e:
            logger.error(f"Surface generation failed: {e}")
            raise
    
    def generate_cryptic_clue(
        self, 
        answer: str, 
        clue_type: str,
        theme: Optional[str] = None
    ) -> dict:
        """
        Generate a Ximenean cryptic clue for the given answer and clue type.
        
        Args:
            answer: The target word for which to generate a clue.
            clue_type: Type of clue (e.g., "Anagram", "Hidden Word", "Charades", 
                      "Container", "Reversal", "Homophone", "Double Definition", "&lit").
            theme: Optional theme or context constraint for the clue.
        
        Returns:
            A dictionary containing:
            - clue: The final surface reading
            - definition: The "straight" part of the clue
            - wordplay_parts: Breakdown of components (fodder, indicators, etc.)
            - explanation: Mechanical breakdown following "Definition + Wordplay = Answer"
            - type: The clue type used
            - answer: The target answer
        
        Raises:
            ValueError: If the API response is invalid or JSON parsing fails.
            Exception: If the API call fails.
        """
        
        # Construct the prompt for the Setter
        theme_context = f" Theme: {theme}." if theme else ""
        
        system_prompt = """You are a Ximenean cryptic crossword setter. You generate clues that follow the Ximenean standard:
- A precise definition (the "straight" meaning)
- A fair subsidiary indication (wordplay)
- Nothing else

Always return your response as a JSON object with NO additional text before or after."""

        user_prompt = f"""Generate a Ximenean cryptic clue for the answer "{answer.upper()}" using clue type "{clue_type}".{theme_context}

Your response MUST be valid JSON (and ONLY JSON) with exactly this structure:
{{
    "clue": "The complete clue surface reading",
    "definition": "The definition part of the clue",
    "wordplay_parts": {{
        "type": "{clue_type}",
        "fodder": "The letters/words being manipulated (if applicable)",
        "indicator": "The word indicating the wordplay (if applicable)",
        "mechanism": "Brief description of how the wordplay works"
    }},
    "explanation": "Step-by-step breakdown: [Definition part identifies X], [Indicator 'Y' suggests Z operation], [Operating on W gives {answer.upper()}]",
    "is_fair": true
}}"""

        try:
            logger.info(f"Generating clue for '{answer}' with type '{clue_type}'")
            
            # Make API request using the Portkey client
            response = self.client.chat.completions.create(
                model=self.MODEL_ID,
                max_tokens=500,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            
            
            # Extract response text using helper method
            response_text = self._extract_response_text(response)
            logger.info(f"Clue response received ({len(response_text)} chars)")
            
            # Parse JSON response
            clue_json = self._parse_json_response(response_text)
            
            # Add metadata
            clue_json["type"] = clue_type
            clue_json["answer"] = answer.upper()
            
            logger.info(f"Successfully generated clue: {clue_json['clue']}")
            return clue_json
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON in API response: {e}") from e
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "connecttimeout" in error_msg:
                logger.error(
                    f"API request timed out. The Portkey endpoint may be unreachable. "
                    f"Check your network connectivity and API key configuration."
                )
            logger.error(f"API call failed: {e}")
            raise
    
    @staticmethod
    def _parse_json_response(response_text: str) -> dict:
        """
        Parse JSON from the model response, handling potential formatting issues.
        Looks for the LAST valid JSON block to handle "let me reconsider" chatter.
        
        Args:
            response_text: The raw text response from the API.
        
        Returns:
            Parsed JSON as a dictionary.
        
        Raises:
            ValueError: If JSON parsing fails.
        """
        response_text = response_text.strip()
        
        # Try direct parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON if wrapped in markdown code blocks
        # Find ALL code blocks and try the LAST valid one (handles "wait, let me reconsider")
        if "```" in response_text:
            code_blocks = []
            parts = response_text.split("```")
            
            # Collect all potential JSON blocks (odd indices are inside code blocks)
            for i in range(1, len(parts), 2):
                block = parts[i].strip()
                # Remove language specifier if present
                if block.startswith("json"):
                    block = block[4:].strip()
                code_blocks.append(block)
            
            # Try parsing from last to first (most recent correction)
            for block in reversed(code_blocks):
                try:
                    return json.loads(block)
                except json.JSONDecodeError:
                    continue
        
        # Try to find JSON objects in the text (look for last {...})
        import re
        # Find all potential JSON objects
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = list(re.finditer(json_pattern, response_text, re.DOTALL))
        
        # Try from last to first
        for match in reversed(matches):
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
        
        # If all else fails, raise error
        raise ValueError(f"Could not parse JSON from response: {response_text[:200]}...")


def main():
    """Example usage of the Setter Agent.
    
    NOTE: This will attempt to connect to the Portkey endpoint at:
    https://eu.aigw.galileo.roche.com/v1
    
    If you receive a timeout error, verify:
    1. PORTKEY_API_KEY environment variable is set correctly
    2. Network connectivity to the Portkey gateway is available
    3. The API key has appropriate permissions
    """
    try:
        # Initialize the Setter Agent with extended timeout for demo
        setter = SetterAgent(timeout=45.0)
        
        # Example: Generate a clue
        example_answer = "LISTEN"
        example_type = "Hidden Word"
        
        print(f"\n{'='*60}")
        print(f"Generating cryptic clue for: {example_answer}")
        print(f"Clue type: {example_type}")
        print(f"{'='*60}\n")
        
        clue = setter.generate_cryptic_clue(
            answer=example_answer,
            clue_type=example_type
        )
        
        print("Generated Clue:")
        print(json.dumps(clue, indent=2))
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
