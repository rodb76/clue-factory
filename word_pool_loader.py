"""
Word Pool Loader: Loads validated seed words with recommended clue types.

This module provides a structured word source for the "Mechanical-First" generation
pipeline, ensuring that words are paired with appropriate clue types that have a
high likelihood of producing valid mechanical wordplay.

Supports modular loading from multiple JSON files in ./word_pools/ directory.
"""

import json
import random
import logging
import os
import glob
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Map seed_words.json categories to clue types
CATEGORY_TO_TYPE = {
    "anagram_friendly": "Anagram",
    "charade_friendly": "Charade",
    "hidden_word_friendly": "Hidden Word",
    "container_friendly": "Container",
    "reversal_friendly": "Reversal",
    "homophone_friendly": "Homophone",
    "double_def_friendly": "Double Definition",
    "standard_utility": None  # Will randomly assign a type
}


class WordPoolLoader:
    """Loads words from all JSON files in ./word_pools/ directory."""
    
    def __init__(self, word_pools_dir: str = "word_pools"):
        """
        Initialize the word pool loader.
        
        Args:
            word_pools_dir: Directory containing word pool JSON files (default: "word_pools").
        """
        self.word_pools_dir = word_pools_dir
        self.word_pool: List[Dict] = []  # List of {word, type, source, usage_count}
        self.used_words: set = set()
        self.category_map: Dict[str, List[str]] = {}
        self.word_metadata: Dict[str, Dict] = {}  # word -> {source, type, usage_count}
        self.usage_counts: Dict[str, int] = defaultdict(int)  # Track usage per word
        
        self._load_all_word_pools()
        
        logger.info(f"WordPoolLoader initialized with {len(self.word_pool)} words from {self.word_pools_dir}/")
    
    def _load_all_word_pools(self):
        """Load and merge all JSON files from word_pools/ directory."""
        # Find all JSON files in word_pools directory
        pool_files = glob.glob(os.path.join(self.word_pools_dir, "*.json"))
        
        if not pool_files:
            logger.warning(f"No JSON files found in {self.word_pools_dir}/ directory")
            # Fall back to legacy seed_words.json in root if it exists
            if os.path.exists("seed_words.json"):
                logger.info("Falling back to legacy seed_words.json in root directory")
                pool_files = ["seed_words.json"]
            else:
                raise FileNotFoundError(f"No word pool files found in {self.word_pools_dir}/ or root directory")
        
        logger.info(f"Found {len(pool_files)} word pool file(s):")
        for file_path in pool_files:
            logger.info(f"  - {os.path.basename(file_path)}")
        
        # Load each file
        for file_path in pool_files:
            self._load_single_pool(file_path)
        
        logger.info(f"Total loaded: {len(self.word_pool)} word-type pairs")
    
    def _load_single_pool(self, file_path: str):
        """Load a single word pool JSON file."""
        source_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            words_from_file = 0
            
            # Parse each category
            for category, words in data.items():
                if category not in CATEGORY_TO_TYPE:
                    logger.warning(f"Unknown category in {source_name}: {category}")
                    continue
                
                clue_type = CATEGORY_TO_TYPE[category]
                self.category_map.setdefault(category, []).extend(words)
                
                for word in words:
                    word_upper = word.upper()
                    
                    if clue_type:
                        # Specific type assigned
                        assigned_type = clue_type
                    else:
                        # Standard utility - randomly pick a type
                        standard_types = ["Anagram", "Charade", "Container", "Hidden Word"]
                        assigned_type = random.choice(standard_types)
                    
                    # Add word with metadata
                    self.word_pool.append({
                        "word": word_upper,
                        "type": assigned_type,
                        "source": source_name,
                        "usage_count": 0
                    })
                    
                    # Store metadata
                    if word_upper not in self.word_metadata:
                        self.word_metadata[word_upper] = {
                            "sources": [source_name],
                            "types": [assigned_type],
                            "usage_count": 0
                        }
                    else:
                        # Word appears in multiple files - track all sources
                        self.word_metadata[word_upper]["sources"].append(source_name)
                        if assigned_type not in self.word_metadata[word_upper]["types"]:
                            self.word_metadata[word_upper]["types"].append(assigned_type)
                    
                    words_from_file += 1
            
            logger.info(f"  {source_name}: {words_from_file} words")
        
        except FileNotFoundError:
            logger.error(f"Pool file not found: {file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            raise
    
    def get_random_seed(self, avoid_duplicates: bool = True) -> Optional[Tuple[str, str]]:
        """
        Get a random word with its recommended clue type.
        Prioritizes words that have been used fewer times.
        
        Args:
            avoid_duplicates: If True, won't return previously used words in this session.
        
        Returns:
            Tuple of (word, recommended_type) or None if pool exhausted.
        """
        available_words = [
            entry for entry in self.word_pool
            if not avoid_duplicates or entry["word"] not in self.used_words
        ]
        
        if not available_words:
            logger.warning("Word pool exhausted (all words used)")
            return None
        
        # Prioritize words with lower usage counts
        # Sort by usage_count (ascending), then shuffle within each usage tier for variety
        available_words.sort(key=lambda x: x["usage_count"])
        
        # Group by usage count and pick from the least-used tier
        min_usage = available_words[0]["usage_count"]
        least_used = [w for w in available_words if w["usage_count"] == min_usage]
        
        # Randomly pick from least-used words
        selected = random.choice(least_used)
        
        word = selected["word"]
        clue_type = selected["type"]
        source = selected["source"]
        
        # Mark as used
        self.used_words.add(word)
        selected["usage_count"] += 1
        self.usage_counts[word] += 1
        
        logger.info(f"Selected: {word} (type: {clue_type}, source: {source}, usage: {selected['usage_count']})")
        return (word, clue_type)
    
    def get_specific_type_seed(
        self,
        clue_type: str,
        avoid_duplicates: bool = True
    ) -> Optional[Tuple[str, str]]:
        """
        Get a random word suitable for a specific clue type.
        Prioritizes words that have been used fewer times.
        
        Args:
            clue_type: The desired clue type.
            avoid_duplicates: If True, won't return previously used words in this session.
        
        Returns:
            Tuple of (word, clue_type) or None if no suitable words available.
        """
        available_words = [
            entry for entry in self.word_pool
            if entry["type"] == clue_type and (not avoid_duplicates or entry["word"] not in self.used_words)
        ]
        
        if not available_words:
            logger.warning(f"No available words for type: {clue_type}")
            return None
        
        # Prioritize words with lower usage counts
        available_words.sort(key=lambda x: x["usage_count"])
        min_usage = available_words[0]["usage_count"]
        least_used = [w for w in available_words if w["usage_count"] == min_usage]
        
        selected = random.choice(least_used)
        word = selected["word"]
        source = selected["source"]
        
        # Mark as used
        self.used_words.add(word)
        selected["usage_count"] += 1
        self.usage_counts[word] += 1
        
        logger.info(f"Selected: {word} (requested type: {clue_type}, source: {source}, usage: {selected['usage_count']})")
        return (word, clue_type)
    
    def reset_used(self):
        """Reset the used words set to allow reusing words."""
        logger.info(f"Resetting used words ({len(self.used_words)} words)")
        self.used_words.clear()
    
    def get_pool_stats(self) -> Dict:
        """
        Get statistics about the word pool.
        
        Returns:
            Dictionary with pool statistics.
        """
        type_counts = {}
        source_counts = {}
        
        for entry in self.word_pool:
            clue_type = entry["type"]
            source = entry["source"]
            
            type_counts[clue_type] = type_counts.get(clue_type, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1
        
        # Calculate unique words (since same word may appear multiple times with different types)
        unique_words = len(set(entry["word"] for entry in self.word_pool))
        
        return {
            "total_entries": len(self.word_pool),
            "unique_words": unique_words,
            "used_words": len(self.used_words),
            "available_words": unique_words - len(self.used_words),
            "type_distribution": type_counts,
            "source_distribution": source_counts,
            "usage_stats": dict(self.usage_counts)
        }


def main():
    """Test the word pool loader."""
    print("\n" + "="*80)
    print("WORD POOL LOADER TEST")
    print("="*80 + "\n")
    
    # Initialize loader
    loader = WordPoolLoader()
    
    # Show statistics
    stats = loader.get_pool_stats()
    print("Pool Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Unique words: {stats['unique_words']}")
    print(f"  Available: {stats['available_words']}")
    print()
    print("Type Distribution:")
    for clue_type, count in sorted(stats['type_distribution'].items()):
        print(f"  {clue_type:20}: {count:3} entries")
    print()
    print("Source Distribution:")
    for source, count in sorted(stats['source_distribution'].items()):
        print(f"  {source:30}: {count:3} entries")
    print()
    
    # Get some random seeds
    print("Random Seeds (10 samples):")
    for i in range(10):
        result = loader.get_random_seed()
        if result:
            word, clue_type = result
            print(f"  {i+1:2}. {word:15} → {clue_type}")
    print()
    
    # Get specific type seeds
    print("Anagram-Specific Seeds (5 samples):")
    loader.reset_used()  # Reset to allow reuse
    for i in range(5):
        result = loader.get_specific_type_seed("Anagram")
        if result:
            word, clue_type = result
            print(f"  {i+1}. {word:15} → {clue_type}")
    print()
    
    # Final statistics
    final_stats = loader.get_pool_stats()
    print(f"After sampling: {final_stats['used_words']} words used, "
          f"{final_stats['available_words']} remaining")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
