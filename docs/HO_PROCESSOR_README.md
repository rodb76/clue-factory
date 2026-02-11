# George Ho Dataset Processor

Reverse-engineers and enriches the [George Ho Cryptic Crossword Database](https://cryptics.georgeho.org/) with wordplay explanations and Ximenean quality metrics.

## Overview

This script takes professional cryptic clues from the George Ho dataset and:

1. **Reverse-engineers** the wordplay using Logic Tier (Sonnet) to identify:
   - Clue type (Anagram, Hidden, Charade, etc.)
   - Definition component
   - Fodder (raw material)
   - Indicator (instruction word)
   - Mechanical breakdown

2. **Enriches** with educational content using Surface Tier (Haiku):
   - Oblique hints
   - Full step-by-step explanations

3. **Audits** using the Ximenean Auditor to calculate:
   - Ximenean Score (technical compliance)
   - Difficulty Level (1-5)
   - Narrative Fidelity (surface naturalness)

4. **Preserves** all original metadata (source, URL, puzzle date)

## Installation

Ensure dependencies are installed:

```bash
pip install -r requirements.txt
```

Required environment variables in `.env`:
```
PORTKEY_API_KEY=your_api_key
LOGIC_MODEL_ID=your_logic_model
SURFACE_MODEL_ID=your_surface_model
MODEL_ID=fallback_model
```

## Usage

### Basic Usage

Process 10 clues from a dataset (default limit):

```bash
python ho_processor.py dataset.csv
```

Process with specific filters:

```bash
# Only reviewed clues (may filter out many/all clues if dataset lacks is_reviewed field)
python ho_processor.py dataset.csv --reviewed-only

# Process more clues
python ho_processor.py dataset.csv --limit 50
```

### Command-Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `dataset` | Path to CSV or JSON file | `ho_data.csv` |
| `--limit N` | Process only N clues (default: 10) | `--limit 50` |
| `--random` | Shuffle before sampling | `--random` |
| `--source` | Filter by source name | `--source guardian` |
| `--reviewed-only` | Only process reviewed clues | `--reviewed-only` |
| `--output` | Custom output filename | `--output my_results.json` |

### Examples

**Process 10 random clues from The Guardian:**

```bash
python ho_processor.py ho_data.csv --limit 10 --random --source guardian
```

**Process all Times clues (no limit):**

```bash
python ho_processor.py ho_data.csv --source times_xwd_times
```

**Process a diverse sample of 100 clues:**

```bash
python ho_processor.py ho_data.csv --limit 100 --random
```

## Input Format

The script accepts CSV or JSON files with the following fields:

### Required Fields
- `clue`: The cryptic clue text
- `answer`: The answer word

### Optional Fields
- `definition`: Original definition (if available)
- `source`: Source identifier (e.g., "guardian", "times_xwd_times")
- `source_url`: URL to original puzzle
- `puzzle_date`: Date of puzzle (any format)
- `is_reviewed`: Quality flag (1 = reviewed, 0 = unreviewed)

### CSV Example

```csv
clue,answer,definition,source,source_url,puzzle_date,is_reviewed
"Confused enlist soldiers to be quiet (6)",SILENT,be quiet,guardian,https://...,2024-01-15,1
"Ocean current hidden in tide pool (4)",DEEP,Ocean current,times,https://...,2024-01-16,1
```

### JSON Example

```json
[
  {
    "clue": "Confused enlist soldiers to be quiet (6)",
    "answer": "SILENT",
    "definition": "be quiet",
    "source": "guardian",
    "source_url": "https://...",
    "puzzle_date": "2024-01-15",
    "is_reviewed": "1"
  }
]
```

## Output Format

The script generates a timestamped JSON file (e.g., `ho_enriched_20260211_143022.json`) with:

```json
{
  "metadata": {
    "source_dataset": "George Ho Cryptics (https://cryptics.georgeho.org/)",
    "processing_timestamp": "2026-02-11T14:30:22",
    "total_clues": 50,
    "logic_model": "claude-3-sonnet",
    "surface_model": "claude-3-haiku"
  },
  "clues": [
    {
      "original_clue": "Confused enlist soldiers to be quiet (6)",
      "answer": "SILENT",
      "original_definition": "be quiet",
      "source": "guardian",
      "source_url": "https://...",
      "puzzle_date": "2024-01-15",
      "is_reviewed": true,
      
      "clue_type": "Anagram",
      "definition": "be quiet",
      "fodder": "enlist",
      "indicator": "confused",
      "mechanism": "ENLIST (confused) = SILENT",
      
      "explanation": "The word 'enlist' is confused (anagrammed) to produce SILENT, which means 'be quiet'.",
      "hint": "Think about rearranging the letters in a word about joining up.",
      
      "ximenean_score": 0.85,
      "difficulty_level": 3,
      "narrative_fidelity": 90.0,
      
      "processing_timestamp": "2026-02-11T14:30:25",
      "logic_model": "claude-3-sonnet",
      "surface_model": "claude-3-haiku"
    }
  ]
}
```

## Automatic Cleaning

The script automatically handles common dataset issues:

1. **Missing Enumerations**: Adds `(N)` to clues without enumeration patterns
2. **Machine Errors**: Logs and skips problematic entries
3. **Failed Processing**: Continues with next clue instead of failing entire batch

## Error Handling

The processor is fault-tolerant:

- **API Failures**: Logs error and continues with next clue
- **Parsing Errors**: Attempts multiple extraction methods
- **Missing Fields**: Uses sensible defaults where possible

Failed clues are logged but don't stop batch processing.

## Summary Statistics

After processing, the script displays:

```
SUMMARY STATISTICS:
  Average Ximenean Score: 0.82
  Average Difficulty: 3.4/5
  Average Narrative Fidelity: 87.3%

CLUE TYPE DISTRIBUTION:
  Anagram: 15
  Hidden: 8
  Charade: 7
  Container: 6
  Double Definition: 5
  Reversal: 4
  Homophone: 3
```

## Performance

Processing times (approximate):
- **ReverseEngineerAgent** (Logic Tier): ~3-5 seconds per clue
- **ExplanationAgent** (Surface Tier): ~2-3 seconds per clue
- **Auditor**: <1 second per clue

For batch processing: ~6-10 seconds per clue total

## Integration with Main Pipeline

The enriched dataset can be used as:

1. **Training Data**: High-quality examples for few-shot prompting
2. **Calibration Set**: Benchmark for quality assessment
3. **Style Guide**: Reference for setting consistent tone

## Top 50 Abbreviations Reference

The ReverseEngineerAgent uses this reference for accurate deconstruction:

- **Roman Numerals**: I, V, X, L, C, D, M
- **Directions**: N, S, E, W, L (left), R (right/take)
- **Elements**: H, O, N, C, AU (gold), AG (silver), FE (iron)
- **Music**: P (soft), F (loud), PP, FF
- **Chess**: K, Q, B, N (knight), R (rook)
- **Titles**: DR, MP, PM, QC
- **Units**: T, M, G, OZ, LB, S, HR, MIN

## Troubleshooting

### "PORTKEY_API_KEY not found"
Add your API key to `.env` file

### "Dataset file not found"
Check the file path and ensure CSV/JSON extension

### "No clues to process after filtering"
- Remove `--reviewed-only` flag (many datasets don't have this field)
- Try relaxing filters or using `--random` for diverse sampling
- Check that your dataset has the expected columns

### High failure rate
- Check that clues have enumerations
- Verify `is_reviewed` flag for quality
- Ensure dataset format matches expected schema

## Testing

Run unit tests:

```bash
pytest tests/test_ho_processor.py -v
```

Run integration tests (requires API access):

```bash
pytest tests/test_ho_processor.py -v -m slow
```

## Future Enhancements

- [ ] Parallel processing for faster batch execution
- [ ] Confidence scores for reverse-engineering
- [ ] Interactive mode for manual review
- [ ] Export to different formats (CSV, SQLite)
- [ ] Integration with Workshop Agent for alternative suggestions

## References

- **George Ho Database**: https://cryptics.georgeho.org/
- **Dataset Datasheet**: See original documentation for column definitions
- **Ximenean Auditor**: See [docs/PHASE10_METRICS_IMPLEMENTATION.md](PHASE10_METRICS_IMPLEMENTATION.md)
