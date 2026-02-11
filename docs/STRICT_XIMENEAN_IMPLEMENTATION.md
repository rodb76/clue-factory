# Strict Ximenean Logic Implementation

**Date:** February 10, 2026  
**Status:** ✅ Complete

## Overview

Implemented strict Ximenean cryptic grammar rules to eliminate filler words, prevent indirect anagrams (using synonyms for fodder), and enforce imperative indicators.

## Changes Implemented

### 1. Auditor Hardening (`auditor.py`)

Added three new validation checks:

#### A. Fodder Presence Check (`_check_fodder_presence`)
- **Purpose**: Ensures every character in the fodder is physically present in the clue text
- **Rule**: No synonyms allowed for fodder elements
- **Example FAIL**: Using "merchant" in clue when fodder is "dealer"
- **Example PASS**: Using "listen" in clue when fodder is "listen"

#### B. Filler Words Audit (`_check_filler_words`)
- **Purpose**: Flags extraneous words that aren't part of definition, fodder, or indicator
- **Rule**: Only allows 0-2 standard connectors (is, for, gives, from, at, becomes, to, in, of, with)
- **Example FAIL**: "So when the person becomes confused with listen it gives a quiet result"
- **Example PASS**: "Mix listen to be quiet"

#### C. Indicator Grammar Check (`_check_indicator_grammar`)
- **Purpose**: Ensures indicators are imperative when they come before fodder
- **Rule**: Use imperative forms (Mix, Scramble, Reverse, Hide), not indicative (Mixed, Scrambled, Reversed, Hidden)
- **Example FAIL**: "Listen **mixed** quietly" (indicative)
- **Example PASS**: "**Mix** listen to be quiet" (imperative)

### 2. Updated `AuditResult` Dataclass

Added new fields:
```python
fodder_presence_check: bool = True
fodder_presence_feedback: str = ""
filler_check: bool = True
filler_feedback: str = ""
indicator_grammar_check: bool = True
indicator_grammar_feedback: str = ""
```

Fairness score now incorporates all 6 checks (up from 3):
- Direction check
- Double duty check
- Indicator fairness check
- **Fodder presence check** (new)
- **Filler words check** (new)
- **Indicator grammar check** (new)

### 3. Surface Refinement (`setter_agent.py`)

Updated `generate_surface_from_wordplay` prompt with stricter rules:

**New System Prompt:**
```
CRITICAL RULES:
1. STRICTLY use the exact fodder provided - NO synonyms allowed
2. Every word must justify its presence (definition, fodder, indicator, or connector)
3. Prioritize simplicity and clarity over literary flourishes
```

**New User Prompt Requirements:**
```
- MANDATORY: Use the EXACT fodder words in the clue (no synonyms)
- Eliminate unnecessary filler words
- Allow at most 2 connectors
```

### 4. Example Refinement

Added Reversal example demonstrating simpler Ximenean style:
```python
Reversal Example:
{"wordplay_parts": {"fodder": "lager", "indicator": "returned", "mechanism": "reverse of lager"}, "definition_hint": "majestic"}
```

**Result**: "Reverse lager for majestic" → REGAL  
**Removes**: Previous verbose style with "bearing when" type fillers

## Test Results

Created `tests/test_strict_ximenean.py` with comprehensive validation:

### Fodder Presence Tests
- ✅ PASS: "Disturbed listen to be quiet" (fodder "listen" is present)
- ✅ FAIL: "Confused merchant leads group" (fodder "dealer" not present)

### Filler Words Tests
- ✅ PASS: "Listen quietly" (minimal filler)
- ✅ FAIL: "So when the person becomes confused with listen it gives a quiet result" (3 connectors)

### Indicator Grammar Tests
- ✅ PASS: "Mix listen to be quiet" (imperative)
- ✅ FAIL: "Listen mixed up quietly" (indicative - past participle)
- ✅ FAIL: "Listen scrambled quietly" (indicative - past participle)

### Overall Audit Test
- ✅ **Perfect Score**: "Reverse lager for majestic" → 100% fairness score
  - Direction: ✅ PASS
  - Double Duty: ✅ PASS
  - Indicator Fairness: ✅ PASS
  - Fodder Presence: ✅ PASS
  - Filler Check: ✅ PASS
  - Grammar Check: ✅ PASS

## Impact on Pipeline

### Before (Lenient)
```
Clue: "Majestic bearing when lager is returned"
- Multiple filler words: "bearing when", "is"
- Less clear cryptic structure
- Fairness: 66.7% (3/3 old checks)
```

### After (Strict)
```
Clue: "Reverse lager for majestic"
- No filler words
- Clear cryptic structure
- Fairness: 100% (6/6 new checks)
```

### Success Rate Impact
Expected to **decrease initial pass rate** but **increase quality**:
- More clues will fail audit on first attempt
- Regeneration will produce cleaner, more Ximenean clues
- Final output will have higher fairness scores

## Allowed Connectors

Standard Ximenean connectors (max 2 per clue):
- is, for, gives, from, at, becomes, to, in, of, with

## Usage Example

```python
from auditor import XimeneanAuditor

auditor = XimeneanAuditor()

clue = {
    "clue": "Reverse lager for majestic",
    "definition": "majestic",
    "answer": "REGAL",
    "type": "Reversal",
    "wordplay_parts": {
        "fodder": "lager",
        "indicator": "reverse",
        "mechanism": "reverse of lager"
    }
}

result = auditor.audit_clue(clue)
# result.passed = True
# result.fairness_score = 1.0
# All 6 checks pass
```

## Documentation Updates

- Created: `tests/test_strict_ximenean.py`
- Updated: `auditor.py` (+150 lines)
- Updated: `setter_agent.py` (stricter prompts)
- Created: `docs/STRICT_XIMENEAN_IMPLEMENTATION.md` (this file)

## Backward Compatibility

- ✅ All existing tests still pass
- ✅ Old `AuditResult` consumers work (new fields have defaults)
- ✅ Main pipeline unchanged
- ⚠️ **Expected**: Lower initial success rate (more strict validation)
- ✅ **Benefit**: Higher quality final clues

## Next Steps

1. **Monitor Impact**: Track success rates in factory_run
2. **Tune Setter**: May need to adjust few-shot examples if success rate drops too much
3. **Consider Feedback Loop**: Feed audit failures back to wordplay generation for learning

## Summary

This implementation enforces the core Ximenean principles:
1. **Physical Presence**: Fodder must be in the clue (no synonyms)
2. **Economy**: Every word earns its place (minimal fillers)
3. **Clear Grammar**: Imperative indicators for direct instruction

Result: Cleaner, fairer, more elegant cryptic clues.
