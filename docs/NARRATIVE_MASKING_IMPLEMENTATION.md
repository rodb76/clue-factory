# Advanced Narrative Masking & Thematic Logic

**Date:** February 11, 2026  
**Status:** ✅ Complete

## Overview

Implemented the **NO-GIBBERISH RULE** to eliminate literal letter listings (e.g., "with en, treat, y") by enforcing standard cryptic abbreviations and thematic masking. This transforms mechanical component listings into natural, deceptive surface readings.

## The Problem

**Before (Literal Listing):**
```
"Earnest request with en, treat, y" → ENTREATY
```
- Lists components mechanically
- Non-word fragments (en, y) appear standalone
- Reads like assembly instructions, not English prose
- Fairness Score: 85.7% (fails narrative integrity)

**After (Narrative Masking):**
```
"Earnest plea from nurse's treat for unknown" → ENTREATY
```
- Uses cryptic substitutions: EN → "nurse", Y → "unknown"
- Reads as coherent English sentence
- Maintains surface deception
- Fairness Score: Target 100%

## Implementation Summary

### 1. Cryptic Abbreviations Reference (`setter_agent.py`)

Added comprehensive `CRYPTIC_ABBREVIATIONS` dictionary with 60+ standard substitutions:

#### Letter Substitutions
- **A**: "a", "one", "ace", "adult", "article"
- **N**: "new", "north", "knight", "note", "pole"
- **Y**: "unknown", "year", "yesterday"
- **X**: "unknown", "kiss", "ten", "cross", "times"
- **EN**: "in", "nurse", "printer's measure"

#### Roman Numerals
- **I** → "one"
- **V** → "five"
- **X** → "ten"
- **L** → "fifty"
- **C** → "hundred"
- **M** → "thousand"
- **XI** → "team", "eleven"

#### Chemical Elements
- **H** → "gas", "hydrogen"
- **O** → "oxygen", "nothing", "love"
- **AU** → "gold"
- **FE** → "iron"
- **AG** → "silver"
- **CU** → "copper"
- **PB** → "lead"

#### Country/Region Codes
- **CH** → "switzerland", "swiss"
- **CA** → "california", "canada"
- **NY** → "new york"
- **LA** → "los angeles", "louisiana"

#### Academic/Professional
- **L** → "learner", "student", "pound"
- **BA/MA** → "graduate", "degree"
- **DR** → "doctor", "drive"
- **MD** → "doctor"

#### Military/Organizational
- **RE** → "soldier", "engineer", "about"
- **RA** → "soldier", "artist"
- **GI** → "soldier", "grunt"
- **UN** → "peacekeepers", "one"
- **EU** → "europe", "union"

### 2. Updated Setter Prompts (`setter_agent.py`)

Enhanced system prompt with three new sections:

#### A. The NO-GIBBERISH RULE (MANDATORY)
```
- NEVER include standalone letters or non-word fragments in the surface
- Single letters MUST be masked using standard cryptic abbreviations
- Forbidden: "with en, treat, y"
- Required: "from nurse, treat, unknown"
```

#### B. Narrative Masking Guidelines
```
- Choose substitutions that fit your thematic story
- Chess theme: N → "knight", K → "king"
- Geographic theme: N → "north", E → "east"
- The surface MUST read as plausible English, NOT mechanical listing
```

#### C. NO-GIBBERISH Enforcement (User Prompt)
```
- If fodder contains single letters (e.g., EN, Y, N), MUST substitute
- Check: Every token in your clue must be a real English word
```

### 3. Narrative Integrity Check (`auditor.py`)

Added `_check_narrative_integrity()` method with two-tier validation:

#### Tier 1: Literal Listing Detection (HARD FAIL)
Regex patterns catch obvious violations:
```python
# Patterns that trigger FAIL:
r'\b[a-z]\s*,\s*[a-z]\b'           # "x, y" or "n, e"
r'\bwith\s+[a-z]{1,2}\s*,'         # "with en," or "with n,"
r'\bfrom\s+[a-z]{1,2}\s*,'         # "from en," or "from n,"
r'\bhas\s+[a-z]{1,2}\s*,'          # "has en," or "has n,"
```

**Example Failures:**
- "Earnest request with en, treat, y" → FAIL
- "Found in n, e, w system" → FAIL
- "Built from x, y, z coordinates" → FAIL

#### Tier 2: Suspicious Token Warning (SOFT WARN)
Flags potential unmasked abbreviations in listing contexts:
```python
# Suspicious 2-letter tokens not in common_two_letter list
# Example: "re", "la", "te" in "Found in re, la, te position"
# Result: [WARN] with guidance to use substitutions
```

### 4. Updated AuditResult Dataclass

Added two new fields:
```python
narrative_integrity_check: bool = True
narrative_integrity_feedback: str = ""
```

Now tracks **7 checks** total (was 6):
1. Direction check
2. Double duty check
3. Indicator fairness check
4. Fodder presence check
5. Filler check
6. Grammar check
7. **Narrative integrity check** (NEW)

Fairness score calculation updated: `sum(7 checks) / 7`

## Test Results

Created comprehensive test suite ([tests/test_narrative_masking.py](../tests/test_narrative_masking.py)):

### Test 1: Literal Listing (FAIL) ✅
```python
Clue: "Earnest request with en, treat, y"
Result: FAIL (85.7% fairness)
Narrative Integrity: FAIL
Feedback: "[FAIL] Surface contains literal letter listing: 'with en,'"
```

### Test 2: Proper Cryptic Substitutions (PASS) ✅
```python
Clue: "Earnest request from nurse's treat for unknown"
Result: Narrative Integrity PASS
Feedback: "[PASS] Surface reading appears natural"
```

### Test 3: Suspicious Tokens (WARN) ✅
```python
Clue: "Found in re, la, te position"
Result: [WARN] Possible unmasked abbreviations: re, la, te
```

### Test 4: Natural English Surface (PASS) ✅
```python
Clue: "Final Greek letter found in home game"
Result: PASS (100% fairness)
All checks pass including narrative integrity
```

### Backward Compatibility ✅
All existing tests pass:
- test_auditor.py: 8/8 tests passing
- test_strict_ximenean.py: All tests passing
- test_minimalist_lie.py: All tests passing

## Usage Examples

### For Setter Agent

**Charade with Single Letters:**
```
Fodder: "EN + TREAT + Y"

❌ BAD: "Earnest request with en, treat, y"
✅ GOOD: "Earnest plea from nurse's treat for unknown"
         (EN → nurse, Y → unknown)

✅ ALSO GOOD: "Earnest appeal: printer's measure, treat, year"
              (EN → printer's measure, Y → year)
```

**Anagram with Compass Points:**
```
Fodder: "N E W S"

❌ BAD: "Confused with n, e, w, s"
✅ GOOD: "Confused knight, east, women, son"
         (N → knight, E → east, W → women, S → son)

✅ THEMATIC: "Confused north, east, west, south directions"
              (Geographic theme fits "directions")
```

**Hidden Word with Elements:**
```
Fodder: "AU in RAG"

❌ BAD: "Find au in rag"
✅ GOOD: "Find gold in rag"
         (AU → gold)
```

### For Auditor

The auditor now automatically:
1. Detects literal listings: `"with x, y"` → FAIL
2. Warns about suspicious tokens: `"re, la, te"` → WARN
3. Passes natural surfaces: `"home game"` → PASS

## Substitution Selection Guidelines

### Thematic Coherence
Choose substitutions that enhance surface narrative:

**Chess/Games Theme:**
- N → "knight"
- K → "king"
- Q → "queen"
- B → "bishop"

**Geographic Theme:**
- N → "north"
- S → "south"
- E → "east"
- W → "west"

**Academic Theme:**
- L → "learner"
- BA → "graduate"
- MA → "master"
- DR → "doctor"

**Time/Measurement:**
- T → "time"
- M → "minute"
- H → "hour"
- S → "second"

### Broad Substitution Authority

Setters have explicit authorization to use:
- Any substitution in the CRYPTIC_ABBREVIATIONS reference
- Additional standard cryptic conventions not in the list
- Context-appropriate meanings (e.g., "L" as "fifty" in Roman context vs "learner" in academic context)

## Impact on Pipeline

### Expected Changes
- **Initial Pass Rate:** May decrease 5-10% (stricter validation)
- **Clue Quality:** Significantly improved readability
- **User Experience:** Clues read as natural English sentences
- **Fairness Perception:** Higher perceived fairness from solvers

### Generation Strategy
Setter agent will now:
1. Identify single-letter components in fodder
2. Select thematically appropriate substitutions
3. Build narrative surface using masked components
4. Avoid mechanical listing patterns

### Audit Enforcement
Auditor will:
1. Flag literal listings as HARD FAIL (0% on that check)
2. Warn about suspicious unmasked tokens
3. Pass natural English surfaces
4. Provide actionable feedback with substitution examples

## Technical Details

### Files Modified

1. **setter_agent.py**
   - Added 60+ entry CRYPTIC_ABBREVIATIONS dictionary
   - Enhanced system prompt with NO-GIBBERISH RULE
   - Updated user prompt with enforcement guidelines
   - Added narrative masking examples

2. **auditor.py**
   - Added `_check_narrative_integrity()` method (70 lines)
   - Updated `AuditResult` dataclass (2 new fields)
   - Modified `audit_clue()` to include 7th check
   - Updated fairness score calculation to 7 checks

3. **tests/test_narrative_masking.py** (NEW)
   - 4 comprehensive test functions
   - Tests literal listings, proper substitutions, warnings, natural surfaces
   - Total runtime: ~40 seconds (8 API calls)

### Backward Compatibility
- ✅ All existing tests pass
- ✅ Old clues continue to work (new check is additive)
- ✅ AuditResult structure extensible (dataclass defaults)
- ✅ Fairness score still 0-1 scale (just recalculated over 7 checks)

## Examples in Production

### Real Output Comparison

**Generated Clue (Before NO-GIBBERISH):**
```json
{
  "clue": "Earnest request with en, treat, y",
  "fairness_score": 0.857,
  "narrative_integrity_check": false
}
```

**Expected Output (After NO-GIBBERISH):**
```json
{
  "clue": "Earnest plea from nurse's treat for unknown",
  "fairness_score": 1.0,
  "narrative_integrity_check": true
}
```

## Reference Quick Guide

### Common Letter Substitutions

| Letter | Common Uses | Example Context |
|--------|-------------|-----------------|
| A | one, ace, article | "Get a point" (A = ace/one) |
| B | born, bishop | "Chess piece born" (B = bishop) |
| E | east, drug, english | "Head east" (E = east) |
| I | one, current | "Single one" (I = one) |
| L | learner, left, fifty | "Student learner" (L = learner) |
| M | male, thousand | "Male parent" (M = male) |
| N | knight, north, new | "Chess knight" (N = knight) |
| O | nothing, love | "Score nothing" (O = love/duck) |
| R | right, river | "Turn right" (R = right) |
| S | south, son, small | "Head south" (S = south) |
| T | time, ton | "Measure time" (T = time) |
| X | unknown, ten | "Solve unknown" (X = unknown) |
| Y | unknown, year | "Variable unknown" (Y = unknown) |

### Multi-Letter Codes

| Code | Substitution | Category |
|------|-------------|----------|
| EN | nurse, in | Medical/Spatial |
| AU | gold | Chemistry |
| FE | iron | Chemistry |
| CH | switzerland | Geography |
| LA | los angeles | Geography |
| BA | graduate | Academic |
| MA | master | Academic |
| XI | team, eleven | Sports/Roman |

## Next Steps

1. **Monitor Generation:** Track narrative integrity pass rates
2. **Expand Reference:** Add more thematic clusters as patterns emerge
3. **Feedback Loop:** Use audit failures to improve setter prompts
4. **User Testing:** Validate that masked clues maintain solvability

## Philosophy Statement

> "A cryptic clue is a story, not a parts list. Every word should belong to the narrative, not announce the machinery. The solver deserves deception through language, not transparency through labeling."

## Summary

Advanced Narrative Masking enforces the NO-GIBBERISH RULE by:
1. Providing 60+ standard cryptic abbreviations
2. Requiring thematic masking of single-letter components
3. Detecting literal listings via regex patterns
4. Warning about suspicious unmasked tokens
5. Ensuring every clue reads as natural English

Result: Clues transform from mechanical listings to deceptive narratives while maintaining Ximenean fairness.
