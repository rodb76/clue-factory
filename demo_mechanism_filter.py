"""
Quick demonstration of mechanism filtering in action.

Run this to see how the filter works with actual clue generation.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from word_pool_loader import WordPoolLoader
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def demo_filter_selection():
    """
    Demonstrate how mechanism filtering selects words.
    
    This simulates what factory_run() does when required_types is specified.
    """
    
    print("\n" + "="*80)
    print("MECHANISM FILTER DEMONSTRATION")
    print("Simulating factory_run() with required_types=['Charade', 'Container']")
    print("="*80)
    
    # Initialize word pool
    word_loader = WordPoolLoader()
    stats = word_loader.get_pool_stats()
    
    print(f"\nWord Pool Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Unique words: {stats['unique_words']}")
    print(f"  Type distribution:")
    for clue_type, count in sorted(stats['type_distribution'].items()):
        print(f"    {clue_type:20}: {count:3} words")
    
    # Simulate filter activation
    required_types = ["Charade", "Container"]
    batch_size = 10
    
    print("\n" + "-"*80)
    print(f"FILTER ACTIVATED: required_types={required_types}")
    print("-"*80)
    
    # This is what factory_run() does internally
    logger.info(f"Batch Filter Active: Only processing {required_types}")
    
    print(f"\n*** MECHANISM FILTER ACTIVE ***")
    print(f"Only generating: {', '.join(required_types)}")
    print()
    
    # Simulate batch word selection with cycling
    print(f"Selecting {batch_size} words using type cycling...")
    print()
    
    # Create cycling pattern
    types_cycle = required_types * (batch_size // len(required_types) + 1)
    word_type_pairs = []
    
    print(f"Cycle pattern: {types_cycle[:batch_size]}")
    print()
    
    for i, clue_type in enumerate(types_cycle[:batch_size], 1):
        seed_result = word_loader.get_specific_type_seed(clue_type, avoid_duplicates=True)
        if seed_result:
            word, actual_type = seed_result
            word_type_pairs.append(seed_result)
            print(f"  [{i:2}] {word:15} → {actual_type:15} (requested: {clue_type})")
    
    print()
    print(f"✓ Selected {len(word_type_pairs)} words")
    
    # Verify distribution
    charades = sum(1 for _, t in word_type_pairs if t == "Charade")
    containers = sum(1 for _, t in word_type_pairs if t == "Container")
    
    print(f"\nDistribution:")
    print(f"  Charades:   {charades}/{len(word_type_pairs)} ({charades/len(word_type_pairs)*100:.0f}%)")
    print(f"  Containers: {containers}/{len(word_type_pairs)} ({containers/len(word_type_pairs)*100:.0f}%)")
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Run 'python main.py' and select Factory mode (2)")
    print("  2. When prompted for mechanism filter, enter: Charade,Container")
    print("  3. Watch the system generate clues using only these two mechanisms")
    print()
    print("Or programmatically:")
    print("  from main import factory_run")
    print("  results = factory_run(target_count=5, required_types=['Charade', 'Container'])")
    print()


if __name__ == "__main__":
    demo_filter_selection()
