"""
Main Orchestrator: Batch processing for cryptic clue generation and validation.

This module coordinates the entire adversarial loop:
1. Generate clues (Setter Agent)
2. Validate mechanically (Mechanic)
3. Solve clues (Solver Agent)
4. Judge results (Referee)
5. Output passed clues
"""

import asyncio
import sys
import os
import json
import logging
import re
import random
import hashlib
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix: Force Windows to use the correct event loop policy
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from setter_agent import SetterAgent
from solver_agent import SolverAgent
from mechanic import validate_clue_complete
from referee import referee_with_validation
from auditor import XimeneanAuditor
from word_selector import WordSelector
from word_pool_loader import WordPoolLoader
from explanation_agent import ExplanationAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ==================== Utility Functions for Compatibility Fields ====================

def ensure_enumeration(clue: str, answer: str) -> str:
    """
    Ensure clue has enumeration pattern like (N) or (N,M,P).
    If missing, append it based on answer structure.
    
    Args:
        clue: The clue text (may or may not have enumeration)
        answer: The answer word/phrase
        
    Returns:
        Clue with enumeration guaranteed
    """
    # Check if clue already has enumeration at the end
    if re.search(r'\(\d+[,\-\d]*\)$', clue.strip()):
        return clue
    
    # Calculate enumeration from answer
    words = re.split(r'[\s\-]+', answer)
    lengths = [str(len(word)) for word in words if word]
    
    if len(lengths) == 1:
        enumeration = f"({lengths[0]})"
    else:
        enumeration = f"({','.join(lengths)})"
    
    return f"{clue.strip()} {enumeration}"


def calculate_length(answer: str) -> int:
    """
    Calculate the letter-only length of an answer.
    Strips spaces, hyphens, and other non-letter characters.
    
    Args:
        answer: The answer word/phrase
        
    Returns:
        Count of letters only
    """
    letters_only = re.sub(r'[^A-Za-z]', '', answer)
    return len(letters_only)


def generate_reveal_order(answer: str) -> List[int]:
    """
    Generate a shuffled list of indices for progressive letter reveal.
    
    Args:
        answer: The answer word/phrase
        
    Returns:
        List of shuffled indices [0...N-1] where N is letter count
    """
    letters_only = re.sub(r'[^A-Za-z]', '', answer)
    indices = list(range(len(letters_only)))
    random.shuffle(indices)
    return indices


def generate_clue_id(answer: str, clue_type: str, timestamp: str = None) -> str:
    """
    Generate a unique ID for the clue.
    Format: {clue_type}_{timestamp}_{answer}
    
    Args:
        answer: The answer word
        clue_type: Type of clue (e.g., 'Anagram', 'Hidden Word')
        timestamp: Optional timestamp string
        
    Returns:
        Unique clue ID
    """
    clean_type = re.sub(r'[^a-z0-9]', '', clue_type.lower().replace(' ', '_'))
    
    if timestamp:
        clean_timestamp = re.sub(r'[^0-9]', '', timestamp)
        return f"{clean_type}_{clean_timestamp}_{answer}"
    else:
        # Use hash if no timestamp
        hash_input = f"{clue_type}_{answer}".encode('utf-8')
        hash_hex = hashlib.md5(hash_input).hexdigest()[:12]
        return f"{clean_type}_{hash_hex}_{answer}"


class ClueResult:
    """Container for a complete clue processing result."""
    
    def __init__(
        self,
        word: str,
        clue_type: str,
        clue_json: Dict = None,
        mechanical_valid: bool = False,
        solution_json: Dict = None,
        referee_result = None,
        audit_result = None,
        passed: bool = False,
        error: str = None,
        regeneration_count: int = 0,
        explanation_data: Dict = None,
        # Compatibility fields for app integration
        clue_id: str = None,
        clue_with_enum: str = None,
        length: int = None,
        reveal_order: List[int] = None
    ):
        self.word = word
        self.clue_type = clue_type
        self.clue_json = clue_json
        self.mechanical_valid = mechanical_valid
        self.solution_json = solution_json
        self.referee_result = referee_result
        self.audit_result = audit_result
        self.passed = passed
        self.error = error
        self.regeneration_count = regeneration_count
        self.explanation_data = explanation_data
        # Compatibility fields
        self.clue_id = clue_id
        self.clue_with_enum = clue_with_enum
        self.length = length
        self.reveal_order = reveal_order
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        # Compatibility fields first (for app integration)
        if self.clue_id:
            result["id"] = self.clue_id
        if self.clue_with_enum:
            result["clue"] = self.clue_with_enum
        if self.length is not None:
            result["length"] = self.length
        if self.reveal_order:
            result["reveal_order"] = self.reveal_order
        
        # Standard fields
        result["word"] = self.word
        result["clue_type"] = self.clue_type
        result["passed"] = self.passed
        
        if self.error:
            result["error"] = self.error
            return result
        
        if self.clue_json:
            # Only add original clue if compatibility clue not already added
            if not self.clue_with_enum:
                result["clue"] = self.clue_json.get("clue", "")
            result["definition"] = self.clue_json.get("definition", "")
            result["explanation"] = self.clue_json.get("explanation", "")
            result["wordplay_parts"] = self.clue_json.get("wordplay_parts", {})
        
        result["mechanical_valid"] = self.mechanical_valid
        
        if self.solution_json:
            result["solver_answer"] = self.solution_json.get("answer", "")
            result["solver_reasoning"] = self.solution_json.get("reasoning", "")
            result["solver_confidence"] = self.solution_json.get("confidence", "")
        
        if self.referee_result:
            result["referee_feedback"] = self.referee_result.feedback
            result["similarity"] = self.referee_result.similarity
        
        if self.audit_result:
            result["audit"] = self.audit_result.to_dict()
        
        if self.regeneration_count > 0:
            result["regeneration_attempts"] = self.regeneration_count
        
        if self.explanation_data:
            result["explanation"] = self.explanation_data
        
        return result


def process_single_clue_sync(
    word: str,
    clue_type: str,
    setter: SetterAgent,
    solver: SolverAgent,
    auditor: XimeneanAuditor,
    enumeration: str = None,
    regeneration_attempts: int = 0,
    max_regenerations: int = 1
) -> ClueResult:
    """
    Process a single clue through the complete pipeline (synchronous version).
    
    Pipeline with "Mechanical First" strategy:
    1a. Generate wordplay components only (Setter Step 1)
    1b. Validate mechanically - RETRY up to 3 times if fails
    1c. Generate surface reading (Setter Step 2)
    2. Solve clue (Solver)
    3. Judge results (Referee)
    4. Audit for Ximenean fairness (Auditor)
    
    If audit fails, regenerate with feedback (up to max_regenerations attempts).
    
    Args:
        word: The target word.
        clue_type: Type of clue to generate.
        setter: SetterAgent instance.
        solver: SolverAgent instance.
        auditor: XimeneanAuditor instance.
        enumeration: Optional enumeration (e.g., "(6)").
        regeneration_attempts: Current regeneration attempt count.
        max_regenerations: Maximum regeneration attempts.
    
    Returns:
        ClueResult with full processing details.
    """
    
    logger.info(f"Processing: {word} ({clue_type})" + 
                (f" [Attempt {regeneration_attempts + 1}]" if regeneration_attempts > 0 else ""))
    
    try:
        # Prepare enumeration
        if not enumeration:
            enumeration = f"({len(word)})"
        
        # ===================================================================
        # STEP 1a: Generate wordplay components only (MECHANICAL FIRST)
        # ===================================================================
        logger.info(f"  Step 1a/5: Generating wordplay components...")
        
        max_wordplay_attempts = 3
        wordplay_data = None
        mechanical_valid = False
        validation_results = None
        last_error = None
        
        for wordplay_attempt in range(max_wordplay_attempts):
            if wordplay_attempt > 0:
                logger.info(f"    Retry {wordplay_attempt}/{max_wordplay_attempts} with feedback...")
            
            # Generate wordplay with feedback from previous attempt
            retry_feedback = last_error if wordplay_attempt > 0 else None
            wordplay_data = setter.generate_wordplay_only(word, clue_type, retry_feedback)
            
            # ===================================================================
            # STEP 1b: Validate mechanically BEFORE generating surface
            # ===================================================================
            logger.info(f"  Step 1b/5: Validating wordplay mechanically...")
            
            # Create temporary clue structure for validation
            temp_clue = {
                "answer": word.upper(),
                "type": clue_type,
                "wordplay_parts": wordplay_data.get("wordplay_parts", {}),
                "clue": f"[Wordplay validation - surface pending]"
            }
            
            mechanical_valid, validation_results = validate_clue_complete(temp_clue, enumeration)
            
            if mechanical_valid:
                logger.info(f"  ✓ Wordplay mechanics PASSED on attempt {wordplay_attempt + 1}")
                break
            else:
                # Build detailed error feedback with specific guidance
                failed_checks = []
                for name, result in validation_results.items():
                    if not result.is_valid:
                        failed_checks.append(f"{name}: {result.message}")
                
                # Create enhanced error message with type-specific guidance
                error_detail = "\n".join(failed_checks)
                guidance = ""
                if "Hidden" in error_detail or "hidden" in error_detail:
                    guidance = "\n\nGUIDANCE: For Hidden Word clues, verify character-by-character that the answer appears as consecutive letters in your fodder. Use the bracketed verification format in your mechanism field (e.g., 'hidden in alp[HABET RAY]')."
                elif "Anagram" in error_detail or "anagram" in error_detail or "Letters" in error_detail:
                    guidance = "\n\nGUIDANCE: For Anagram clues, verify the exact letter counts match. The fodder must contain EXACTLY the same letters as the answer."
                
                last_error = f"Mechanical validation failed:\n{error_detail}{guidance}"
                logger.warning(f"  ✗ Wordplay mechanics FAILED: {'; '.join(failed_checks[:2])}")
        
        # If wordplay never passed, fail fast and move to next word
        if not mechanical_valid:
            logger.warning(f"  ✗ Wordplay failed after {max_wordplay_attempts} attempts - discarding {word}")
            return ClueResult(
                word=word,
                clue_type=clue_type,
                clue_json=None,
                mechanical_valid=False,
                passed=False,
                error=f"Wordplay generation failed after {max_wordplay_attempts} attempts: {last_error[:100]}",
                regeneration_count=regeneration_attempts
            )
        
        # ===================================================================
        # PRE-SURFACE CHECK: For Hidden Words, verify answer is literally in fodder
        # ===================================================================
        if clue_type.lower() == "hidden word" or clue_type.lower() == "hidden":
            fodder = wordplay_data.get("wordplay_parts", {}).get("fodder", "")
            # Remove spaces and check if answer is substring
            fodder_no_spaces = fodder.replace(" ", "").replace("-", "").upper()
            if word.upper() not in fodder_no_spaces:
                logger.warning(f"  ✗ Pre-surface check FAILED: '{word.upper()}' not found in fodder '{fodder}'")
                logger.warning(f"  ✗ This indicates a critical spelling error in the wordplay")
                return ClueResult(
                    word=word,
                    clue_type=clue_type,
                    clue_json=None,
                    mechanical_valid=False,
                    passed=False,
                    error=f"Pre-surface check failed: '{word.upper()}' not found as substring in fodder '{fodder}'. Critical spelling error.",
                    regeneration_count=regeneration_attempts
                )
            else:
                logger.info(f"  ✓ Pre-surface check PASSED: '{word.upper()}' found in '{fodder}'")
        
        # ===================================================================
        # STEP 1c: Generate surface reading from VALIDATED wordplay
        # ===================================================================
        logger.info(f"  Step 1c/5: Generating surface reading...")
        clue_json = setter.generate_surface_from_wordplay(wordplay_data, word)
        logger.info(f"  ✓ Surface generated: \"{clue_json.get('clue', 'N/A')[:60]}...\"")
        
        # ===================================================================
        # STEP 2: Solve clue
        # ===================================================================
        logger.info(f"  Step 2/5: Solving clue...")
        solution_json = solver.solve_clue(clue_json["clue"], enumeration)
        
        # ===================================================================
        # STEP 3: Referee judgment
        # ===================================================================
        logger.info(f"  Step 3/5: Refereeing...")
        referee_result = referee_with_validation(clue_json, solution_json, strict=True)
        
        if not referee_result.passed:
            logger.warning(f"  ✗ Referee failed: {word} - {referee_result.feedback}")
            return ClueResult(
                word=word,
                clue_type=clue_type,
                clue_json=clue_json,
                mechanical_valid=True,
                solution_json=solution_json,
                referee_result=referee_result,
                passed=False,
                error=f"Referee judged: {referee_result.feedback}",
                regeneration_count=regeneration_attempts
            )
        
        logger.info(f"  ✓ Referee passed")
        
        # ===================================================================
        # STEP 4: Ximenean Audit
        # ===================================================================
        logger.info(f"  Step 4/5: Auditing for Ximenean fairness...")
        audit_result = auditor.audit_clue(clue_json)
        
        if not audit_result.passed:
            logger.warning(f"  ✗ Audit failed for {word}")
            
            # Log specific failure reasons for monitoring
            if not audit_result.direction_check:
                logger.warning(f"    ✗ DIRECTION CHECK FAILED: {audit_result.direction_feedback}")
            if not audit_result.double_duty_check:
                logger.warning(f"    ✗ DOUBLE DUTY CHECK FAILED: {audit_result.double_duty_feedback}")
            if not audit_result.indicator_fairness_check:
                logger.warning(f"    ✗ FAIRNESS CHECK FAILED: {audit_result.indicator_fairness_feedback}")
            
            # Attempt regeneration if we haven't exceeded max attempts
            if regeneration_attempts < max_regenerations:
                logger.info(f"  Attempting regeneration ({regeneration_attempts + 1}/{max_regenerations})...")
                
                # Build feedback for next attempt
                feedback_parts = []
                if not audit_result.direction_check:
                    feedback_parts.append(audit_result.direction_feedback)
                if not audit_result.double_duty_check:
                    feedback_parts.append(audit_result.double_duty_feedback)
                if not audit_result.indicator_fairness_check:
                    feedback_parts.append(audit_result.indicator_fairness_feedback)
                
                feedback = " | ".join(feedback_parts)
                logger.info(f"    Feedback: {feedback[:80]}")
                
                # Recursively try again with feedback
                return process_single_clue_sync(
                    word,
                    clue_type,
                    setter,
                    solver,
                    auditor,
                    enumeration,
                    regeneration_attempts + 1,
                    max_regenerations
                )
            else:
                logger.warning(f"  Max regeneration attempts reached for {word}")
                return ClueResult(
                    word=word,
                    clue_type=clue_type,
                    clue_json=clue_json,
                    mechanical_valid=True,
                    solution_json=solution_json,
                    referee_result=referee_result,
                    audit_result=audit_result,
                    passed=False,
                    error=f"Audit failed and max regenerations reached",
                    regeneration_count=regeneration_attempts
                )
        
        logger.info(f"  ✓ Audit passed (fairness_score: {audit_result.fairness_score:.1%})")
        logger.info(f"  ✓ PASSED: {word}")
        
        # Generate compatibility fields for app integration
        clue_text = clue_json.get("clue", "")
        clue_with_enum = ensure_enumeration(clue_text, word)
        length = calculate_length(word)
        reveal_order = generate_reveal_order(word)
        clue_id = generate_clue_id(word, clue_type)
        
        return ClueResult(
            word=word,
            clue_type=clue_type,
            clue_json=clue_json,
            mechanical_valid=True,
            solution_json=solution_json,
            referee_result=referee_result,
            audit_result=audit_result,
            passed=True,
            regeneration_count=regeneration_attempts,
            clue_id=clue_id,
            clue_with_enum=clue_with_enum,
            length=length,
            reveal_order=reveal_order
        )
        
    except Exception as e:
        logger.error(f"  ✗ Error processing {word}: {e}")
        return ClueResult(
            word=word,
            clue_type=clue_type,
            passed=False,
            error=str(e),
            regeneration_count=regeneration_attempts
        )


async def process_single_clue_async(
    word: str,
    clue_type: str,
    setter: SetterAgent,
    solver: SolverAgent,
    auditor: XimeneanAuditor,
    enumeration: str = None,
    executor: ThreadPoolExecutor = None
) -> ClueResult:
    """
    Process a single clue through the complete pipeline (async version).
    
    Args:
        word: The target word.
        clue_type: Type of clue to generate.
        setter: SetterAgent instance.
        solver: SolverAgent instance.
        auditor: XimeneanAuditor instance.
        enumeration: Optional enumeration (e.g., "(6)").
        executor: ThreadPoolExecutor for running sync code in threads.
    
    Returns:
        ClueResult with full processing details.
    """
    loop = asyncio.get_event_loop()
    
    # Run the synchronous processing in a thread pool
    result = await loop.run_in_executor(
        executor,
        process_single_clue_sync,
        word,
        clue_type,
        setter,
        solver,
        auditor,
        enumeration,
        0,  # regeneration_attempts
        1   # max_regenerations
    )
    
    return result


async def process_batch_async(
    word_type_pairs: List[Tuple[str, str]],
    max_concurrent: int = 5
) -> List[ClueResult]:
    """
    Process a batch of words in parallel with concurrency control.
    
    Args:
        word_type_pairs: List of (word, clue_type) tuples.
        max_concurrent: Maximum number of concurrent API calls.
    
    Returns:
        List of ClueResult objects.
    """
    
    logger.info(f"Starting batch processing: {len(word_type_pairs)} clues")
    logger.info(f"Max concurrent requests: {max_concurrent}")
    
    # Initialize agents (reuse for all requests)
    setter = SetterAgent(timeout=60.0)
    solver = SolverAgent(timeout=60.0)
    auditor = XimeneanAuditor(timeout=60.0)
    
    # Create thread pool for parallel execution
    executor = ThreadPoolExecutor(max_workers=max_concurrent)
    
    # Create tasks for all clues
    tasks = []
    for word, clue_type in word_type_pairs:
        task = process_single_clue_async(
            word,
            clue_type,
            setter,
            solver,
            auditor,
            enumeration=None,
            executor=executor
        )
        tasks.append(task)
    
    # Process all tasks with progress tracking
    results = []
    completed = 0
    total = len(tasks)
    
    for coro in asyncio.as_completed(tasks):
        result = await coro
        results.append(result)
        completed += 1
        logger.info(f"Progress: {completed}/{total} clues processed")
    
    # Shutdown executor
    executor.shutdown(wait=True)
    
    return results


def process_batch_sync(
    word_type_pairs: List[Tuple[str, str]]
) -> List[ClueResult]:
    """
    Process a batch of words sequentially (synchronous version).
    
    Args:
        word_type_pairs: List of (word, clue_type) tuples.
    
    Returns:
        List of ClueResult objects.
    """
    
    logger.info(f"Starting sequential processing: {len(word_type_pairs)} clues")
    
    # Initialize agents
    setter = SetterAgent(timeout=60.0)
    solver = SolverAgent(timeout=60.0)
    auditor = XimeneanAuditor(timeout=60.0)
    
    results = []
    for i, (word, clue_type) in enumerate(word_type_pairs, 1):
        logger.info(f"Processing {i}/{len(word_type_pairs)}: {word}")
        result = process_single_clue_sync(word, clue_type, setter, solver, auditor)
        results.append(result)
    
    return results


def generate_report(results: List[ClueResult]) -> Dict:
    """
    Generate a summary report from batch results.
    
    Args:
        results: List of ClueResult objects.
    
    Returns:
        Dictionary with summary statistics and passed clues.
    """
    
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    mechanical_failures = sum(1 for r in results if not r.mechanical_valid and not r.error)
    solver_failures = sum(1 for r in results if r.mechanical_valid and not r.passed)
    errors = sum(1 for r in results if r.error)
    
    report = {
        "summary": {
            "total_clues": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            "mechanical_failures": mechanical_failures,
            "solver_failures": solver_failures,
            "errors": errors
        },
        "passed_clues": [r.to_dict() for r in results if r.passed],
        "failed_clues": [r.to_dict() for r in results if not r.passed]
    }
    
    return report


def factory_run(
    target_count: int = 20,
    batch_size: int = 10,
    max_concurrent: int = 5,
    output_file: str = "final_clues_output.json",
    use_seed_words: bool = True,
    required_types: Optional[List[str]] = None
) -> List[ClueResult]:
    """
    The "Clue Factory" - continuous loop that generates valid clues until target is met.
    
    This function:
    1. Automatically selects words from a pool (seed_words.json or general)
    2. Processes batches in parallel with Mechanical-First strategy
    3. Continues until target_count PASSED clues are generated
    4. Saves only PASSED clues to output file
    5. Optionally filters by required clue types
    
    Args:
        target_count: Number of PASSED clues needed (default: 20).
        batch_size: Number of words to process per batch (default: 10).
        max_concurrent: Max concurrent API calls (default: 5).
        output_file: Output JSON file for passed clues (default: "final_clues_output.json").
        use_seed_words: If True, use seed_words.json; else use WordSelector (default: True).
        required_types: List of required clue types (e.g., ["Charade", "Container"]).
                       If None or empty, all types are allowed (default: None).
    
    Returns:
        List of all PASSED ClueResult objects.
    """
    
    print("\n" + "="*80)
    print(f"CLUE FACTORY: Generating {target_count} Valid Cryptic Clues")
    print("="*80 + "\n")
    
    # Display model configuration
    logic_model = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID", "unknown"))
    surface_model = os.getenv("SURFACE_MODEL_ID", os.getenv("MODEL_ID", "unknown"))
    print("Model Configuration (Inverted Tiering):")
    print(f"  Logic tasks (wordplay/audit/solve): {logic_model.split('/')[-1] if '/' in logic_model else logic_model}")
    print(f"  Surface tasks (clue writing): {surface_model.split('/')[-1] if '/' in surface_model else surface_model}")
    print()
    
    # Initialize word source
    word_loader = None
    word_selector = None
    
    if use_seed_words:
        try:
            word_loader = WordPoolLoader()
            stats = word_loader.get_pool_stats()
            print(f"Word pool loaded from seed_words.json: {stats['total_words']} words")
            print(f"Type distribution:")
            for clue_type, count in sorted(stats['type_distribution'].items()):
                print(f"  {clue_type:20}: {count:3} words")
            
            # Log mechanism filter if active
            if required_types:
                logger.info(f"Batch Filter Active: Only processing {required_types}")
                print(f"\n*** MECHANISM FILTER ACTIVE ***")
                print(f"Only generating: {', '.join(required_types)}")
                print()
        except (FileNotFoundError, Exception) as e:
            print(f"Failed to load seed_words.json: {e}")
            print("Falling back to WordSelector...")
            use_seed_words = False
    
    if not use_seed_words:
        word_selector = WordSelector(min_length=4, max_length=10)
        print(f"Word pool loaded (WordSelector): {len(word_selector.word_pool)} words")
    
    print(f"Batch size: {batch_size} words")
    print(f"Target: {target_count} PASSED clues")
    print(f"Pipeline: Mechanical Draft → Validate → Surface Polish → Solve → Judge → Audit")
    print()
    
    # Initialize agents (reuse across batches)
    setter = SetterAgent(timeout=60.0)
    solver = SolverAgent(timeout=60.0)
    auditor = XimeneanAuditor(timeout=60.0)
    explainer = ExplanationAgent(timeout=60.0)
    
    # Track results
    passed_clues = []
    all_attempts = []
    batch_num = 0
    
    start_time = time.time()
    
    while len(passed_clues) < target_count:
        batch_num += 1
        remaining = target_count - len(passed_clues)
        current_batch_size = min(batch_size, remaining * 2)  # Generate 2x to account for failures
        
        logger.info(f"\n{'='*60}")
        logger.info(f"BATCH {batch_num}: Need {remaining} more clues, generating {current_batch_size} candidates")
        logger.info(f"{'='*60}")
        
        # Select words for this batch
        word_type_pairs = []
        
        if word_loader:
            # Use seed words with recommended types
            if required_types:
                # MECHANISM FILTER: Only select words matching required types
                # Distribute evenly across required types
                types_cycle = required_types * (current_batch_size // len(required_types) + 1)
                
                for clue_type in types_cycle[:current_batch_size]:
                    seed_result = word_loader.get_specific_type_seed(clue_type, avoid_duplicates=True)
                    if seed_result:
                        word_type_pairs.append(seed_result)
                    else:
                        # No words available for this type, try resetting
                        logger.warning(f"No unused words for type {clue_type}, resetting pool...")
                        word_loader.reset_used()
                        seed_result = word_loader.get_specific_type_seed(clue_type, avoid_duplicates=True)
                        if seed_result:
                            word_type_pairs.append(seed_result)
            else:
                # No filter: Use any type
                for _ in range(current_batch_size):
                    seed_result = word_loader.get_random_seed(avoid_duplicates=True)
                    if seed_result:
                        word_type_pairs.append(seed_result)
                    else:
                        # Pool exhausted, reset and continue
                        logger.warning("Word pool exhausted, resetting...")
                        word_loader.reset_used()
                        seed_result = word_loader.get_random_seed(avoid_duplicates=True)
                        if seed_result:
                            word_type_pairs.append(seed_result)
        else:
            # Use WordSelector (doesn't support type filtering yet)
            if required_types:
                logger.warning("WordSelector doesn't support type filtering. Use seed_words.json for mechanism filtering.")
            word_type_pairs = word_selector.select_words(current_batch_size, avoid_recent=True)
        
        if not word_type_pairs:
            logger.error("No words available for processing!")
            break
        
        print(f"\nBatch {batch_num}: Processing {len(word_type_pairs)} candidates...")
        print(f"Progress: {len(passed_clues)}/{target_count} clues validated")
        
        # Process batch in parallel
        batch_start = time.time()
        
        # Create thread pool
        executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        # Process all clues in batch
        batch_results = []
        for word, clue_type in word_type_pairs:
            result = process_single_clue_sync(
                word,
                clue_type,
                setter,
                solver,
                auditor,
                enumeration=None,
                regeneration_attempts=0,
                max_regenerations=1
            )
            batch_results.append(result)
            all_attempts.append(result)
            
            # Add to passed clues if successful
            if result.passed:
                passed_clues.append(result)
                logger.info(f"✓ SUCCESS: {word} ({len(passed_clues)}/{target_count})")
                
                # Check if we've reached target
                if len(passed_clues) >= target_count:
                    break
        
        executor.shutdown(wait=True)
        
        batch_elapsed = time.time() - batch_start
        batch_pass_rate = sum(1 for r in batch_results if r.passed) / len(batch_results) * 100
        
        print(f"\nBatch {batch_num} complete:")
        print(f"  Time: {batch_elapsed:.1f}s")
        print(f"  Passed: {sum(1 for r in batch_results if r.passed)}/{len(batch_results)} ({batch_pass_rate:.1f}%)")
        print(f"  Total progress: {len(passed_clues)}/{target_count}")
        
        # Early exit if target reached
        if len(passed_clues) >= target_count:
            break
    
    total_elapsed = time.time() - start_time
    
    # Trim to exact target count
    passed_clues = passed_clues[:target_count]
    
    # Generate explanations for all passed clues
    print("\n" + "="*80)
    print("GENERATING EXPLANATIONS")
    print("="*80)
    print(f"Creating hints and breakdowns for {len(passed_clues)} clues...")
    
    for i, result in enumerate(passed_clues, 1):
        try:
            explanation = explainer.generate_explanation(
                clue=result.clue_json.get("clue", ""),
                answer=result.word,
                clue_type=result.clue_type,
                definition=result.clue_json.get("definition", ""),
                wordplay_parts=result.clue_json.get("wordplay_parts", {})
            )
            result.explanation_data = explanation.to_dict()
            print(f"  [{i}/{len(passed_clues)}] ✓ {result.word}")
        except Exception as e:
            logger.warning(f"Failed to generate explanation for {result.word}: {e}")
            result.explanation_data = None
            print(f"  [{i}/{len(passed_clues)}] ✗ {result.word} (failed)")
    
    print("Explanations complete!\n")
    
    # Generate final report
    print("\n" + "="*80)
    print("CLUE FACTORY COMPLETE")
    print("="*80)
    print(f"Total time: {total_elapsed:.1f} seconds ({total_elapsed/60:.1f} minutes)")
    print(f"Total attempts: {len(all_attempts)}")
    print(f"Successful clues: {len(passed_clues)}")
    print(f"Success rate: {len(passed_clues)/len(all_attempts)*100:.1f}%")
    print(f"Average time per clue: {total_elapsed/len(passed_clues):.1f} seconds")
    print()
    
    # Display sample of passed clues
    print(f"Sample of Generated Clues (showing first 10):")
    for i, result in enumerate(passed_clues[:10], 1):
        clue_data = result.to_dict()
        fairness = ""
        if "audit" in clue_data and clue_data["audit"]:
            fairness = f" [{clue_data['audit'].get('fairness_score', 0):.0%}]"
        print(f"  {i:2}. {clue_data['word']:10} ({clue_data['clue_type']:15}): \"{clue_data.get('clue', 'N/A')}\"{fairness}")
    
    if len(passed_clues) > 10:
        print(f"  ... and {len(passed_clues) - 10} more")
    print()
    
    # Save to file (only passed clues)
    output_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "target_count": target_count,
            "total_attempts": len(all_attempts),
            "success_rate": f"{len(passed_clues)/len(all_attempts)*100:.1f}%",
            "total_time_seconds": total_elapsed,
            "batches_processed": batch_num
        },
        "clues": [result.to_dict() for result in passed_clues]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ {len(passed_clues)} validated clues saved to: {output_file}")
    print("="*80 + "\n")
    
    return passed_clues


def main():
    """Main orchestrator function."""
    
    print("\n" + "="*80)
    print("CRYPTIC CLUE GENERATOR: Full Pipeline with Ximenean Audit (Phase 3-4)")
    print("="*80 + "\n")
    
    # Display model configuration
    logic_model = os.getenv("LOGIC_MODEL_ID", os.getenv("MODEL_ID", "unknown"))
    surface_model = os.getenv("SURFACE_MODEL_ID", os.getenv("MODEL_ID", "unknown"))
    print("Model Configuration (Inverted Tiering):")
    print(f"  Logic tasks (wordplay/audit/solve): {logic_model.split('/')[-1] if '/' in logic_model else logic_model}")
    print(f"  Surface tasks (clue writing): {surface_model.split('/')[-1] if '/' in surface_model else surface_model}")
    print()
    
    # Example batch: 10 words with different clue types
    word_type_pairs = [
        ("LISTEN", "Anagram"),
        ("SILENT", "Anagram"),
        ("STAR", "Reversal"),
        ("RATS", "Reversal"),
        ("STEAL", "Hidden Word"),
        ("PAINT", "Container"),
        ("BACK", "Charade"),
        ("PART", "Charade"),
        ("TENDER", "Double Definition"),
        ("HOUSE", "Anagram"),
    ]
    
    print(f"Batch size: {len(word_type_pairs)} clues")
    print(f"Words: {', '.join(word for word, _ in word_type_pairs)}")
    print(f"Pipeline: Generate → Validate → Solve → Judge → Audit")
    print()
    
    # Ask user for processing mode
    print("Choose processing mode:")
    print("  1. Parallel (faster, uses asyncio)")
    print("  2. Sequential (slower, easier to debug)")
    
    choice = input("\nEnter choice (1 or 2, default=1): ").strip() or "1"
    
    start_time = time.time()
    
    if choice == "1":
        # Parallel processing
        print("\nStarting parallel processing...\n")
        results = asyncio.run(process_batch_async(word_type_pairs, max_concurrent=5))
    else:
        # Sequential processing
        print("\nStarting sequential processing...\n")
        results = process_batch_sync(word_type_pairs)
    
    elapsed = time.time() - start_time
    
    # Generate report
    report = generate_report(results)
    
    # Display summary
    print("\n" + "="*80)
    print("BATCH PROCESSING COMPLETE")
    print("="*80)
    print(f"Total time: {elapsed:.1f} seconds")
    print(f"Average per clue: {elapsed/len(results):.1f} seconds")
    print()
    print("Summary:")
    for key, value in report["summary"].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    print()
    
    # Display passed clues
    if report["passed_clues"]:
        print(f"✓ Passed Clues ({len(report['passed_clues'])}):")
        for clue in report["passed_clues"]:
            audit_info = ""
            if "audit" in clue and clue["audit"]:
                audit_info = f" [fairness: {clue['audit'].get('fairness_score', 0):.0%}]"
            regen_info = ""
            if clue.get("regeneration_attempts", 0) > 0:
                regen_info = f" [{clue['regeneration_attempts']} regen]"
            print(f"  • {clue['word']}: \"{clue.get('clue', 'N/A')}\"{audit_info}{regen_info}")
        print()
    
    # Display failed clues
    if report["failed_clues"]:
        print(f"✗ Failed Clues ({len(report['failed_clues'])}):")
        for clue in report["failed_clues"]:
            reason = clue.get('error') or clue.get('referee_feedback', 'Unknown reason')
            audit_reason = ""
            if "audit" in clue and clue["audit"] and not clue["audit"].get("passed"):
                audit_reason = " [Audit failed]"
            print(f"  • {clue['word']}: {reason[:60]}...{audit_reason}")
        print()
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"batch_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Full results saved to: {output_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("CRYPTIC CLUE GENERATOR")
    print("="*80 + "\n")
    
    print("Select mode:")
    print("  1. Fixed Batch Mode (10 predefined words)")
    print("  2. Clue Factory Mode (automated word selection until target reached)")
    
    mode = input("\nEnter choice (1 or 2, default=2): ").strip() or "2"
    
    if mode == "1":
        main()
    else:
        # Factory mode
        target = input("\nHow many valid clues to generate? (default=20): ").strip()
        target_count = int(target) if target.isdigit() else 20
        
        # Ask about mechanism filtering
        print("\nMechanism Filter (optional):")
        print("Available types: Anagram, Charade, Hidden Word, Container, Reversal, Homophone, Double Definition")
        print("Examples: 'Charade,Container' or 'Anagram' or leave blank for all types")
        filter_input = input("\nFilter by clue types (comma-separated, or Enter for all): ").strip()
        
        required_types = None
        if filter_input:
            # Parse comma-separated types
            required_types = [t.strip() for t in filter_input.split(',') if t.strip()]
            print(f"Filter activated: {', '.join(required_types)}")
        else:
            print("No filter: All clue types allowed")
        
        factory_run(
            target_count=target_count,
            batch_size=10,
            max_concurrent=5,
            required_types=required_types
        )
