import test_config
"""
Test refined agent logic for solver accuracy and auditor fairness.
Verifies all four updates requested by the user.
"""

import sys
import inspect

print("\n" + "="*70)
print("TEST: REFINED AGENT LOGIC")
print("="*70 + "\n")

# Test 1: Solver Final Check Step
print("TEST 1: Solver System Prompt - Final Check Step")
print("-" * 40)
try:
    from solver_agent import SolverAgent
    source = inspect.getsource(SolverAgent.solve_clue)
    
    has_final_check = "FINAL CHECK" in source
    has_straight_def = "Straight Definition" in source
    has_synonym_check = "MUST be a synonym of that definition" in source
    has_wrong_warning = "If your proposed answer is just a rearrangement" in source
    
    print(f"  'FINAL CHECK' step: {'✓' if has_final_check else '✗'}")
    print(f"  'Straight Definition' identification: {'✓' if has_straight_def else '✗'}")
    print(f"  Synonym requirement: {'✓' if has_synonym_check else '✗'}")
    print(f"  Wrong answer warning: {'✓' if has_wrong_warning else '✗'}")
    
    if all([has_final_check, has_straight_def, has_synonym_check, has_wrong_warning]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 2: Auditor - Only Check Indicator Field
print("TEST 2: Auditor Directional Check - Only Indicator Field")
print("-" * 40)
try:
    from auditor import XimeneanAuditor
    source = inspect.getsource(XimeneanAuditor._check_direction)
    
    has_ignored_note = "EXPLICITLY IGNORED" in source
    has_fodder_ignore = "fodder" in source and "ignored" in source.lower()
    has_mechanism_ignore = "mechanism" in source and "ignored" in source.lower()
    has_critical_note = "CRITICAL: Only check the indicator field" in source
    
    print(f"  'EXPLICITLY IGNORED' section: {'✓' if has_ignored_note else '✗'}")
    print(f"  Fodder explicitly ignored: {'✓' if has_fodder_ignore else '✗'}")
    print(f"  Mechanism explicitly ignored: {'✓' if has_mechanism_ignore else '✗'}")
    print(f"  Critical note about indicator-only: {'✓' if has_critical_note else '✗'}")
    
    # Functional test: "on" in fodder should PASS
    auditor = XimeneanAuditor()
    test_clue = {
        "wordplay_parts": {
            "fodder": "confused on",
            "indicator": "mixed",
            "mechanism": "anagram of CONFUSED ON"
        }
    }
    passed, feedback = auditor._check_direction(test_clue)
    
    print(f"  Functional test ('on' in fodder): {'✓ PASS' if passed else '✗ FAIL'}")
    
    # Functional test: "on" in indicator should FAIL
    test_clue_2 = {
        "wordplay_parts": {
            "fodder": "listen",
            "indicator": "on",
            "mechanism": "reversal"
        }
    }
    passed_2, feedback_2 = auditor._check_direction(test_clue_2)
    
    print(f"  Functional test ('on' in indicator): {'✓ FAIL' if not passed_2 else '✗ PASS'} (expected FAIL)")
    
    if all([has_ignored_note, has_fodder_ignore, has_mechanism_ignore, has_critical_note, passed, not passed_2]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 3: Setter - Forbid Answer in Clue
print("TEST 3: Setter Surface Generation - Forbid Target Answer")
print("-" * 40)
try:
    from setter_agent import SetterAgent
    source = inspect.getsource(SetterAgent.generate_surface_from_wordplay)
    
    has_critical = "CRITICAL" in source
    has_synonym_must = "synonym for the definition_hint" in source
    has_forbidden = "STRICTLY FORBIDDEN" in source
    has_cannot_use = "CANNOT use the word" in source
    has_answer_variable = "'{answer.upper()}' itself" in source or '"{answer.upper()}" itself' in source
    
    print(f"  CRITICAL constraint: {'✓' if has_critical else '✗'}")
    print(f"  Must use synonym: {'✓' if has_synonym_must else '✗'}")
    print(f"  STRICTLY FORBIDDEN clause: {'✓' if has_forbidden else '✗'}")
    print(f"  Cannot use answer word: {'✓' if has_cannot_use else '✗'}")
    print(f"  References answer variable: {'✓' if has_answer_variable else '✗'}")
    
    if all([has_critical, has_synonym_must, has_forbidden, has_cannot_use, has_answer_variable]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Test 4: Setter - Container Few-Shot Example
print("TEST 4: Setter Wordplay Generation - Container Example")
print("-" * 40)
try:
    from setter_agent import SetterAgent
    source = inspect.getsource(SetterAgent.generate_wordplay_only)
    
    has_container_label = "Container Example" in source
    has_paint_example = "PAINT" in source
    has_pat_outer = '"outer": "PAT"' in source or "'outer': 'PAT'" in source
    has_in_inner = '"inner": "IN"' in source or "'inner': 'IN'" in source
    has_grips_indicator = '"indicator": "grips"' in source or "'indicator': 'grips'" in source
    has_color_definition = '"definition_hint": "To apply color"' in source or "'definition_hint': 'To apply color'" in source
    
    print(f"  'Container Example' label: {'✓' if has_container_label else '✗'}")
    print(f"  PAINT target answer: {'✓' if has_paint_example else '✗'}")
    print(f"  outer: PAT: {'✓' if has_pat_outer else '✗'}")
    print(f"  inner: IN: {'✓' if has_in_inner else '✗'}")
    print(f"  indicator: grips: {'✓' if has_grips_indicator else '✗'}")
    print(f"  definition_hint: To apply color: {'✓' if has_color_definition else '✗'}")
    
    if all([has_container_label, has_paint_example, has_pat_outer, has_in_inner, has_grips_indicator, has_color_definition]):
        print("Status: PASS ✓\n")
    else:
        print("Status: FAIL ✗\n")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error: {e}")
    print("Status: FAIL\n")
    sys.exit(1)

# Final Summary
print("="*70)
print("ALL TESTS PASSED ✓")
print("="*70)
print("\nRefined Logic Summary:")
print("  1. Solver: Added 'Final Check' step for definition-synonym validation")
print("  2. Auditor: Explicitly ignores fodder and mechanism in directional check")
print("  3. Setter: Forbids using target answer word in clue text")
print("  4. Setter: Added Container few-shot example (PAINT)")
print("\nExpected Impact:")
print("  • Solver now explicitly validates answer = synonym of definition")
print("  • Auditor eliminates ALL false positives from fodder/mechanism")
print("  • Setter prevents trivial answers appearing in clue surface")
print("  • Container clues now have concrete training example")
print("\n" + "="*70 + "\n")

