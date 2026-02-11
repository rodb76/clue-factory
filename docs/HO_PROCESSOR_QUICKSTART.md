# Quick Start: George Ho Processor

## Test with Sample Data

A sample dataset (`ho_sample_data.json`) is included for testing.

### 1. Basic Test (Process with Default Limit)

```bash
python ho_processor.py ho_sample_data.json
```

This will:
- Process up to 10 clues from the dataset (default limit)
- Reverse-engineer each clue
- Generate explanations
- Calculate Ximenean metrics
- Save to `ho_enriched_TIMESTAMP.json`

### 2. Quick Test (1 Clue Only)

```bash
python ho_processor.py ho_sample_data.json --limit 1
```

### 3. Random Sample Test

```bash
python ho_processor.py ho_sample_data.json --limit 2 --random
```

### 4. Filter by Source

```bash
python ho_processor.py ho_sample_data.json --source guardian
```

This filters to only Guardian clues.

### 5. Filter by Review Status (Optional)

```bash
python ho_processor.py ho_sample_data.json --reviewed-only
```

**Note**: The `--reviewed-only` flag filters to clues where `is_reviewed == 1`. Many datasets may not have this field or may have few/no reviewed clues. Use with caution.

## Expected Output

You should see console output like:

```
2026-02-11 14:30:22 - ho_processor - INFO - Loading dataset from: ho_sample_data.json
2026-02-11 14:30:22 - ho_processor - INFO - Loaded 5 clues from dataset
2026-02-11 14:30:22 - ho_processor - INFO - Filtered to 4 reviewed clues

============================================================
Processing clue 1/4
============================================================
2026-02-11 14:30:22 - ho_processor - INFO - Processing: Confused enlist soldiers to be quiet (6) -> SILENT
2026-02-11 14:30:25 - ho_processor - INFO - Deconstructing: 'Confused enlist soldiers to be quiet (6)' -> SILENT
2026-02-11 14:30:28 - ho_processor - INFO - Successfully deconstructed 'SILENT' as Anagram
2026-02-11 14:30:28 - ho_processor - INFO - Generating explanation for 'SILENT'
2026-02-11 14:30:30 - auditor - INFO - Auditing clue for 'SILENT'
2026-02-11 14:30:30 - ho_processor - INFO - ✓ Successfully processed: SILENT (Ximenean: 0.85)

...

============================================================
Batch processing complete: 4/4 successful
============================================================

✓ Saved 4 enriched clues to: ho_enriched_20260211_143032.json

SUMMARY STATISTICS:
  Average Ximenean Score: 0.82
  Average Difficulty: 3.2/5
  Average Narrative Fidelity: 88.5%

CLUE TYPE DISTRIBUTION:
  Anagram: 2
  Hidden: 1
  Double Definition: 1
```

## Inspect the Output

Open the generated `ho_enriched_TIMESTAMP.json` file to see the full enriched data:

```json
{
  "metadata": {
    "source_dataset": "George Ho Cryptics (https://cryptics.georgeho.org/)",
    "processing_timestamp": "2026-02-11T14:30:32",
    "total_clues": 4,
    "logic_model": "claude-3-sonnet",
    "surface_model": "claude-3-haiku"
  },
  "clues": [
    {
      "original_clue": "Confused enlist soldiers to be quiet (6)",
      "answer": "SILENT",
      "clue_type": "Anagram",
      "definition": "be quiet",
      "fodder": "enlist",
      "indicator": "confused",
      "mechanism": "ENLIST (confused) = SILENT",
      "explanation": "The word 'enlist' is confused...",
      "hint": "Think about rearranging letters...",
      "ximenean_score": 0.85,
      "difficulty_level": 3,
      "narrative_fidelity": 90.0,
      "source": "guardian",
      "source_url": "https://...",
      "puzzle_date": "2024-01-15"
    }
  ]
}
```

## Troubleshooting

### "PORTKEY_API_KEY not found"

Make sure your `.env` file contains:

```
PORTKEY_API_KEY=your_key_here
LOGIC_MODEL_ID=your_logic_model
SURFACE_MODEL_ID=your_surface_model
```

### Processing takes too long

The script processes clues sequentially. For the sample dataset:
- Expected time: ~30-40 seconds for 4 clues
- Each clue: ~6-10 seconds (API calls + processing)

### All clues fail

Check:
1. API key is valid
2. Models are accessible
3. Network connection is stable
4. Review console output for specific errors

## Using Your Own Dataset

### From George Ho Database

1. Download the database from https://cryptics.georgeho.org/
2. Export to CSV or JSON format
3. Ensure columns match expected format (see HO_PROCESSOR_README.md)
4. Run with appropriate filters:

```bash
python ho_processor.py your_data.csv --limit 100 --random --reviewed-only
```

### Custom Format

If your data has different column names, edit `ho_processor.py` to map:

```python
clue_dict = {
    "clue": row["your_clue_column"],
    "answer": row["your_answer_column"],
    # ... etc
}
```

## Next Steps

Once you've tested with sample data:

1. **Batch Processing**: Process larger samples with `--limit 100 --random`
2. **Filter by Source**: Target specific publications for style consistency
3. **Integration**: Use enriched data for few-shot prompting in setter_agent.py
4. **Analysis**: Review Ximenean scores to identify high-quality examples

## Performance Tips

For large datasets:
- Use `--limit` to process in batches
- Filter with `--reviewed-only` to ensure quality
- Use `--random` to get diverse samples across time periods
- Monitor API rate limits and adjust timeouts if needed
