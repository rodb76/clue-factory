"""
Word Selector: Automated word source for the Clue Factory.

This module provides intelligent word selection for cryptic clue generation:
- Filters by length (4-10 letters)
- Avoids overly obscure words
- Randomly assigns appropriate clue types
"""

import random
import logging
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Supported cryptic clue types
CLUE_TYPES = [
    "Anagram",
    "Hidden Word",
    "Charade",
    "Container",
    "Reversal",
    "Homophone",
    "Double Definition",
    "&lit"
]


class WordSelector:
    """Selects words for cryptic clue generation."""
    
    def __init__(
        self,
        min_length: int = 4,
        max_length: int = 10,
        word_source: Optional[str] = None
    ):
        """
        Initialize the Word Selector.
        
        Args:
            min_length: Minimum word length (default: 4).
            max_length: Maximum word length (default: 10).
            word_source: Path to word list file (optional).
        """
        self.min_length = min_length
        self.max_length = max_length
        self.word_pool = self._load_word_pool(word_source)
        self.used_words = set()
        
        logger.info(f"WordSelector initialized with {len(self.word_pool)} words")
    
    def _load_word_pool(self, word_source: Optional[str] = None) -> List[str]:
        """
        Load word pool from file or built-in list.
        
        Args:
            word_source: Optional path to word list file.
        
        Returns:
            List of filtered words.
        """
        words = []
        
        # Try loading from file first
        if word_source:
            try:
                with open(word_source, 'r', encoding='utf-8') as f:
                    words = [line.strip().upper() for line in f if line.strip()]
                logger.info(f"Loaded {len(words)} words from {word_source}")
            except FileNotFoundError:
                logger.warning(f"Word source file not found: {word_source}")
        
        # Try NLTK corpus if available
        if not words:
            try:
                import nltk
                from nltk.corpus import words as nltk_words
                
                try:
                    words = [w.upper() for w in nltk_words.words()]
                    logger.info(f"Loaded {len(words)} words from NLTK corpus")
                except LookupError:
                    logger.info("Downloading NLTK words corpus...")
                    nltk.download('words', quiet=True)
                    words = [w.upper() for w in nltk_words.words()]
            except ImportError:
                logger.info("NLTK not available, using built-in word list")
        
        # Fall back to built-in curated word list
        if not words:
            words = self._get_builtin_words()
            logger.info(f"Using built-in word list: {len(words)} words")
        
        # Filter by length and quality
        filtered = self._filter_words(words)
        logger.info(f"Filtered to {len(filtered)} words ({self.min_length}-{self.max_length} letters)")
        
        return filtered
    
    def _get_builtin_words(self) -> List[str]:
        """Get a curated built-in word list suitable for cryptic clues."""
        return [
            # 4-letter words
            "STAR", "RATS", "ARTS", "TARS", "PART", "TRAP", "BACK", "CART",
            "DEAR", "READ", "DARE", "RATE", "TEAR", "HATE", "LATE", "GATE",
            "PAIN", "RAIN", "MAIN", "GAIN", "COIN", "JOIN", "WEST", "BEST",
            "REST", "TEST", "NEST", "PEST", "TALE", "SALE", "PALE", "MALE",
            
            # 5-letter words
            "STEAL", "STALE", "TALES", "LEAST", "EARTH", "HEART", "HATER",
            "WATER", "LATER", "ALTER", "ALERT", "BREAD", "BEARD", "BRAND",
            "GRAND", "STAND", "STEAD", "TREAD", "DREAD", "BREAK", "STEAK",
            "PAINT", "FAINT", "SAINT", "TRAIN", "BRAIN", "GRAIN", "DRAIN",
            "PLAIN", "CLAIM", "STEAM", "CREAM", "DREAM", "SCREAM", "PETAL",
            
            # 6-letter words
            "LISTEN", "SILENT", "ENLIST", "TINSEL", "PRIEST", "STRIPE",
            "RIPEST", "SPREAD", "SPARED", "PARSED", "RAISED", "PRAISED",
            "MASTER", "STREAM", "TAMERS", "ARMETS", "DANGER", "GARDEN",
            "RANGED", "GANDER", "SACRED", "SCARED", "CEDARS", "THREAD",
            "HATRED", "DEARTH", "BREATH", "BATHER", "FATHER", "RATHER",
            "MOTHER", "BOTHER", "SMOTHER", "PARTRIDGE",
            
            # 7-letter words
            "ANAGRAM", "CHARADE", "PALETTE", "PETALED", "PLEATED", "RELATED",
            "ALTERED", "ALERTED", "DEALING", "LEADING", "ALIGNED", "READING",
            "TRADING", "PARTING", "DARTING", "RECITAL", "ARTICLE", "TEACHER",
            "CHEATER", "REACHES", "RANCHES", "MARCHES", "CHAPTER", "PATCHER",
            "CRAFTER", "GRAFTER", "DRAFTER", "RAFTERS", "MASTERS", "STREAMS",
            
            # 8-letter words
            "TRIANGLE", "INTEGRAL", "RELATING", "ALTERING", "ALERTING",
            "STEALING", "DEALING", "DETAILED", "RETAILED", "STREAMED",
            "MASTERED", "REMASTER", "THEATERS", "CHAPTERS", "PAINTERS",
            "PERTAINS", "PANTRIES", "PINASTER", "PRISTANE",
            
            # 9-letter words
            "STREAMING", "MASTERING", "TRIANGLES", "INTEGRALS", "SEARCHING",
            "RESHAPED", "ORGANIZED",
            
            # 10-letter words
            "CELEBRATED", "DECIMATED", "REPLICATED"
        ]
    
    def _filter_words(self, words: List[str]) -> List[str]:
        """
        Filter words by length and quality.
        
        Args:
            words: Raw word list.
        
        Returns:
            Filtered word list.
        """
        filtered = []
        
        for word in words:
            word = word.upper().strip()
            
            # Length filter
            if not (self.min_length <= len(word) <= self.max_length):
                continue
            
            # Only alphabetic characters
            if not word.isalpha():
                continue
            
            # Avoid too many repeated letters (often obscure words)
            letter_counts = {}
            for char in word:
                letter_counts[char] = letter_counts.get(char, 0) + 1
            
            if any(count > len(word) // 2 for count in letter_counts.values()):
                # Skip words like "AAAA" or "MAMMA"
                continue
            
            # Avoid very short words with unusual letter patterns
            if len(word) <= 4 and any(char in word for char in "QXZJ"):
                continue
            
            filtered.append(word)
        
        return filtered
    
    def select_words(
        self,
        count: int,
        avoid_recent: bool = True
    ) -> List[Tuple[str, str]]:
        """
        Select random words with assigned clue types.
        
        Args:
            count: Number of words to select.
            avoid_recent: If True, avoid recently used words.
        
        Returns:
            List of (word, clue_type) tuples.
        """
        available_words = [
            w for w in self.word_pool
            if not avoid_recent or w not in self.used_words
        ]
        
        if len(available_words) < count:
            logger.warning(
                f"Only {len(available_words)} unused words available "
                f"(requested {count}). Resetting used words."
            )
            self.used_words.clear()
            available_words = self.word_pool
        
        # Select random words
        selected = random.sample(available_words, min(count, len(available_words)))
        
        # Assign clue types intelligently
        word_type_pairs = []
        for word in selected:
            clue_type = self._suggest_clue_type(word)
            word_type_pairs.append((word, clue_type))
            self.used_words.add(word)
        
        logger.info(f"Selected {len(word_type_pairs)} words with assigned types")
        return word_type_pairs
    
    def _suggest_clue_type(self, word: str) -> str:
        """
        Suggest an appropriate clue type for a word using affinity logic.
        
        Affinity rules:
        - Short words (< 5 letters): Prefer Hidden Word, Reversal
        - High vowel words (> 3 vowels): Prefer Anagram
        - Medium words (5-8 letters): Prefer Container, Charade
        - Long words (> 8 letters): Prefer Hidden Word, Charade
        
        Args:
            word: The target word.
        
        Returns:
            Suggested clue type.
        """
        # Analyze word characteristics
        vowel_count = sum(1 for char in word if char in "AEIOU")
        length = len(word)
        
        # Weight suggestions based on affinity logic
        suggestions = []
        
        # AFFINITY RULE 1: Short words (< 5 letters)
        if length < 5:
            suggestions.extend(["Hidden Word"] * 4)  # Strong preference
            suggestions.extend(["Reversal"] * 4)
            suggestions.extend(["Charade"] * 2)
            suggestions.append("Anagram")
        
        # AFFINITY RULE 2: High vowel words (> 3 vowels)
        elif vowel_count > 3:
            suggestions.extend(["Anagram"] * 5)  # Strong preference
            suggestions.extend(["Hidden Word"] * 2)
            suggestions.append("Charade")
        
        # Medium-length words (5-8 letters)
        elif 5 <= length <= 8:
            suggestions.extend(["Anagram"] * 3)
            suggestions.extend(["Container"] * 3)
            suggestions.extend(["Charade"] * 2)
            suggestions.extend(["Hidden Word"] * 2)
            suggestions.append("Reversal")
        
        # Long words (> 8 letters)
        else:
            suggestions.extend(["Hidden Word"] * 4)
            suggestions.extend(["Charade"] * 3)
            suggestions.extend(["Anagram"] * 2)
            suggestions.append("Container")
        
        # Always include these possibilities (lower weight)
        suggestions.append("Double Definition")
        suggestions.append("Homophone")
        suggestions.append("&lit")
        
        return random.choice(suggestions)
    
    def reset_used_words(self):
        """Clear the set of used words."""
        self.used_words.clear()
        logger.info("Reset used words tracking")


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    selector = WordSelector(min_length=4, max_length=8)
    
    print(f"\n=== Word Selector Test ===")
    print(f"Word pool size: {len(selector.word_pool)}")
    print()
    
    # Test word selection
    word_pairs = selector.select_words(10)
    
    print("Sample word-type pairs:")
    for word, clue_type in word_pairs:
        print(f"  {word:12} → {clue_type}")
    
    print()
    print("Used words count:", len(selector.used_words))
