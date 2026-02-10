"""
Archive Ingestor: Process external cryptic crossword databases.

This script ingests cryptic clue databases (CSV or JSON format) and converts them
into the word pool format used by the Clue Factory system.

Supports formats like:
- George Ho's cryptic crossword archive
- Guardian crossword databases
- Custom CSV exports with answer + clue_type columns

Usage:
    python ingest_archive.py input.csv --output word_pools/external_archive.json
    python ingest_archive.py input.json --format json
"""

import json
import csv
import argparse
import logging
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Clue type mappings (handle various naming conventions)
CLUE_TYPE_ALIASES = {
    "anagram": "Anagram",
    "ana": "Anagram",
    "anag": "Anagram",
    "hidden": "Hidden Word",
    "hidden word": "Hidden Word",
    "hid": "Hidden Word",
    "charade": "Charade",
    "char": "Charade",
    "container": "Container",
    "cont": "Container",
    "insertion": "Container",
    "reversal": "Reversal",
    "rev": "Reversal",
    "homophone": "Homophone",
    "homo": "Homophone",
    "double": "Double Definition",
    "double def": "Double Definition",
    "double definition": "Double Definition",
    "dd": "Double Definition",
    "&lit": "&lit",
    "all-in-one": "&lit",
}

# Category mapping for output format
TYPE_TO_CATEGORY = {
    "Anagram": "anagram_friendly",
    "Charade": "charade_friendly",
    "Hidden Word": "hidden_word_friendly",
    "Container": "container_friendly",
    "Reversal": "reversal_friendly",
    "Homophone": "homophone_friendly",
    "Double Definition": "double_def_friendly",
    "&lit": "standard_utility"
}


def clean_word(word: str) -> str:
    """
    Clean and normalize a word.
    
    Args:
        word: The word to clean.
    
    Returns:
        Cleaned word in UPPERCASE without punctuation.
    """
    # Remove punctuation, hyphens, spaces
    cleaned = re.sub(r'[^A-Za-z]', '', word)
    return cleaned.upper()


def normalize_clue_type(clue_type: str) -> str:
    """
    Normalize a clue type to standard format.
    
    Args:
        clue_type: The clue type string (may be in various formats).
    
    Returns:
        Normalized clue type or "Unknown" if not recognized.
    """
    if not clue_type:
        return "Unknown"
    
    clue_type_lower = clue_type.lower().strip()
    
    # Direct match
    if clue_type_lower in CLUE_TYPE_ALIASES:
        return CLUE_TYPE_ALIASES[clue_type_lower]
    
    # Fuzzy match - check if any alias is in the string
    for alias, standard in CLUE_TYPE_ALIASES.items():
        if alias in clue_type_lower:
            return standard
    
    return "Unknown"


def ingest_csv(
    input_file: str,
    answer_column: str = "answer",
    type_column: str = "type"
) -> Dict[str, List[str]]:
    """
    Ingest a CSV file with cryptic clue data.
    
    Args:
        input_file: Path to CSV file.
        answer_column: Name of the column containing answers.
        type_column: Name of the column containing clue types.
    
    Returns:
        Dictionary mapping categories to word lists.
    """
    logger.info(f"Ingesting CSV file: {input_file}")
    
    word_pool = defaultdict(list)
    seen_words: Set[str] = set()
    skipped = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Verify required columns exist
            if answer_column not in reader.fieldnames:
                raise ValueError(f"Column '{answer_column}' not found in CSV. Available: {reader.fieldnames}")
            if type_column not in reader.fieldnames:
                logger.warning(f"Column '{type_column}' not found. Will assign 'standard_utility'")
                type_column = None
            
            for row_num, row in enumerate(reader, start=2):
                # Extract answer
                answer = row.get(answer_column, "").strip()
                if not answer:
                    skipped += 1
                    continue
                
                # Clean the answer
                clean_answer = clean_word(answer)
                if not clean_answer:
                    skipped += 1
                    continue
                
                # Filter by length (4-10 letters)
                if len(clean_answer) < 4 or len(clean_answer) > 10:
                    skipped += 1
                    continue
                
                # Skip duplicates
                if clean_answer in seen_words:
                    continue
                seen_words.add(clean_answer)
                
                # Extract clue type
                if type_column:
                    raw_type = row.get(type_column, "").strip()
                    normalized_type = normalize_clue_type(raw_type)
                else:
                    normalized_type = "Unknown"
                
                # Map to category
                if normalized_type == "Unknown":
                    category = "standard_utility"
                else:
                    category = TYPE_TO_CATEGORY.get(normalized_type, "standard_utility")
                
                # Add to pool
                word_pool[category].append(clean_answer)
        
        logger.info(f"Processed {reader.line_num - 1} rows")
        logger.info(f"  Extracted: {len(seen_words)} unique words")
        logger.info(f"  Skipped: {skipped} entries (empty, too short/long, or invalid)")
        
        return dict(word_pool)
    
    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
        raise
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        raise


def ingest_json(input_file: str) -> Dict[str, List[str]]:
    """
    Ingest a JSON file with cryptic clue data.
    
    Expected format:
    [
        {"answer": "LISTEN", "type": "Anagram"},
        {"answer": "AORTA", "type": "Hidden Word"},
        ...
    ]
    
    Or:
    {
        "clues": [
            {"answer": "LISTEN", "type": "Anagram"},
            ...
        ]
    }
    
    Args:
        input_file: Path to JSON file.
    
    Returns:
        Dictionary mapping categories to word lists.
    """
    logger.info(f"Ingesting JSON file: {input_file}")
    
    word_pool = defaultdict(list)
    seen_words: Set[str] = set()
    skipped = 0
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if isinstance(data, list):
            entries = data
        elif isinstance(data, dict) and "clues" in data:
            entries = data["clues"]
        elif isinstance(data, dict):
            # Assume it's already in category format
            logger.info("Detected pre-formatted category structure")
            return data
        else:
            raise ValueError("Unrecognized JSON format")
        
        # Process entries
        for entry in entries:
            if not isinstance(entry, dict):
                skipped += 1
                continue
            
            # Extract answer
            answer = entry.get("answer", "") or entry.get("word", "")
            if not answer:
                skipped += 1
                continue
            
            # Clean the answer
            clean_answer = clean_word(answer)
            if not clean_answer:
                skipped += 1
                continue
            
            # Filter by length
            if len(clean_answer) < 4 or len(clean_answer) > 10:
                skipped += 1
                continue
            
            # Skip duplicates
            if clean_answer in seen_words:
                continue
            seen_words.add(clean_answer)
            
            # Extract clue type
            raw_type = entry.get("type", "") or entry.get("clue_type", "")
            normalized_type = normalize_clue_type(raw_type)
            
            # Map to category
            if normalized_type == "Unknown":
                category = "standard_utility"
            else:
                category = TYPE_TO_CATEGORY.get(normalized_type, "standard_utility")
            
            # Add to pool
            word_pool[category].append(clean_answer)
        
        logger.info(f"Processed {len(entries)} entries")
        logger.info(f"  Extracted: {len(seen_words)} unique words")
        logger.info(f"  Skipped: {skipped} entries")
        
        return dict(word_pool)
    
    except FileNotFoundError:
        logger.error(f"File not found: {input_file}")
        raise
    except Exception as e:
        logger.error(f"Error processing JSON: {e}")
        raise


def save_word_pool(word_pool: Dict[str, List[str]], output_file: str):
    """
    Save the word pool to JSON file.
    
    Args:
        word_pool: Dictionary mapping categories to word lists.
        output_file: Path to output JSON file.
    """
    logger.info(f"Saving word pool to: {output_file}")
    
    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sort words in each category
    sorted_pool = {
        category: sorted(words)
        for category, words in word_pool.items()
    }
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_pool, f, indent=2)
    
    # Log statistics
    total_words = sum(len(words) for words in word_pool.values())
    logger.info(f"Saved {total_words} words across {len(word_pool)} categories")
    for category, words in sorted(word_pool.items()):
        logger.info(f"  {category:20}: {len(words):4} words")


def main():
    """Main entry point for the archive ingestor."""
    parser = argparse.ArgumentParser(
        description="Ingest external cryptic crossword databases into word pool format"
    )
    parser.add_argument(
        "input",
        help="Input file (CSV or JSON)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="word_pools/external_archive.json",
        help="Output file path (default: word_pools/external_archive.json)"
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["csv", "json", "auto"],
        default="auto",
        help="Input format (default: auto-detect from extension)"
    )
    parser.add_argument(
        "--answer-column",
        default="answer",
        help="CSV column name for answers (default: answer)"
    )
    parser.add_argument(
        "--type-column",
        default="type",
        help="CSV column name for clue types (default: type)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("CRYPTIC CROSSWORD ARCHIVE INGESTOR")
    print("="*80 + "\n")
    
    # Auto-detect format
    if args.format == "auto":
        if args.input.endswith(".csv"):
            file_format = "csv"
        elif args.input.endswith(".json"):
            file_format = "json"
        else:
            logger.error("Could not auto-detect format. Please specify with --format")
            return 1
    else:
        file_format = args.format
    
    logger.info(f"Input format: {file_format}")
    
    # Ingest the file
    try:
        if file_format == "csv":
            word_pool = ingest_csv(
                args.input,
                answer_column=args.answer_column,
                type_column=args.type_column
            )
        else:
            word_pool = ingest_json(args.input)
        
        # Save the output
        save_word_pool(word_pool, args.output)
        
        print("\n" + "="*80)
        print("✓ INGESTION COMPLETE")
        print("="*80)
        print(f"\nOutput saved to: {args.output}")
        print(f"Total words: {sum(len(words) for words in word_pool.values())}")
        print("\nTo use this word pool, place it in the word_pools/ directory.")
        print("The WordPoolLoader will automatically load all *.json files from that directory.")
        
        return 0
    
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
