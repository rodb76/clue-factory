"""
FILE: enrich_ho_data.py

DESCRIPTION:
    Enriches crossword clue CSV files with detailed logic/explanation text by scraping
    solutions from three online sources:
    
    1. FIFTEENSQUARED (fifteensquared.net)
       - Uses source_url from CSV to fetch blog post explanations
       - Parses table-based or paragraph-based explanation formats
       
    2. TIMES FOR THE TIMES (timesforthetimes.co.uk)
       - Uses puzzle_name + puzzle_date to discover the correct blog post
       - Automatically detects between standard and Quick Cryptic formats
       - Queries archive.org pattern: YYYY/MM/DD
       
    3. BIG DAVE'S CROSSWORD BLOG (bigdave44.com)
       - Uses source_url from CSV to fetch blog post clue explanations
       - Parses clue/answer/explanation blocks
    
    Match Strategy:
    - For fifteensquared and bigdave44: answers matched by uppercase comparison
    - For times_xwd_times: answers extracted from page via date-based discovery
    
    Output:
    - Input CSV is extended with new 'logic' column containing explanation text
    - Clues without matches show: "Logic not found"
    - Summary printed: "Enriched X out of Y clues"

USAGE:
    python enrich_ho_data.py
        Processes default input: ho_clues_sample.csv
        Creates output: ho_clues_sample_enriched.csv
    
    python enrich_ho_data.py -i my_clues.csv
        Processes: my_clues.csv
        Creates output: my_clues_enriched.csv
    
    python enrich_ho_data.py -i my_clues.csv --limit 50
        Processes only first 50 rows from my_clues.csv
        Useful for testing before processing full file
        Use --limit 0 for no limit (process all rows)
    
    python enrich_ho_data.py -i data.csv -o results.csv
        Processes: data.csv
        Creates output: results.csv (custom filename)
    
    python enrich_ho_data.py -i clues.csv --limit 100 -o enriched_subset.csv
        Combines options: limit to 100 rows, custom output file
    
    python enrich_ho_data.py --help
        Shows all available command-line arguments
    
REQUIREMENTS:
    - Input CSV must have columns: source, answer
    - Optional columns: source_url (for fifteensquared, bigdave44)
                        puzzle_name, puzzle_date (for times_xwd_times)
                        clue (helpful for debugging/matching)
    
    Supported source values:
        - 'fifteensquared' (requires source_url)
        - 'times_xwd_times' (requires puzzle_name, puzzle_date)
        - 'bigdave44' (requires source_url)
    
PERFORMANCE NOTE:
    Network requests are rate-limited with 1-second delays between URLs to avoid
    overwhelming target servers. Processing 100 clues typically takes 2-3 minutes.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
import argparse
import os
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_text(text):
    """Removes non-breaking spaces and extra whitespace."""
    return text.replace('\xa0', ' ').strip()

def find_post_on_day(date_str, puzzle_id, is_quick):
    """
    date_str: '2019-08-08'
    puzzle_id: '27424'
    is_quick: True/False
    """
    # Convert YYYY-MM-DD to YYYY/MM/DD
    formatted_date = date_str.replace('-', '/')
    archive_url = f"https://timesforthetimes.co.uk/{formatted_date}"
    
    print(f"Checking Archive: {archive_url}")
    try:
        r = requests.get(archive_url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Look for all links in the archive page
        for link in soup.find_all('a', href=True):
            text = link.get_text().replace(',', '') # Handle 27,424
            if puzzle_id in text:
                # Ensure we don't mix up Quick Cryptic and Main Cryptic
                if is_quick == ("Quick" in text):
                    return link['href']
    except Exception as e:
        print(f"  Error accessing archive: {e}")
    return None

def get_logic_map(url):
    """Scrapes the entire post and builds an {ANSWER: LOGIC} dictionary."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check for HTTP errors
        if r.status_code == 404:
            print(f"    [404] Entry not found")
            return {}
        elif r.status_code >= 400:
            print(f"    [HTTP {r.status_code}] Error accessing page")
            return {}
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Try different content containers (timesforthetimes.co.uk vs LiveJournal)
        content = soup.find('div', class_='entry-content')
        if not content:
            content = soup.find('article', class_='aentry-post')
        if not content: return {}
        
        # First, replace inline tags with spaces to keep text together
        # This handles <strike>, <em>, <strong>, etc. that would otherwise break up the text
        for tag in content.find_all(['strike', 'del', 's', 'em', 'i', 'strong', 'b', 'span']):
            # Replace the tag with its text content surrounded by spaces
            tag.replace_with(' ' + tag.get_text() + ' ')
        
        # Now extract text with newline separators
        lines = [l.strip() for l in content.get_text(separator='\n').split('\n') if l.strip()]
        
        # Normalize whitespace in each line (collapse multiple spaces)
        lines = [re.sub(r'\s+', ' ', line) for line in lines]
        
        logic_map = {}
        
        for i, line in enumerate(lines):
            # If line is ALL CAPS and long enough, it's likely an ANSWER
            if line.isupper() and len(line) > 2:
                # Logic is either on the same line (separated by dash) or the next line
                match = re.search(rf"\b{re.escape(line)}\b\s*[-–—:.]\s*(.*)", line)
                if match:
                    logic_map[line] = match.group(1).strip()
                elif i + 1 < len(lines):
                    # Collect logic from next line and any continuation lines
                    logic_parts = [lines[i+1]]
                    j = i + 2
                    # Continue collecting lines until we hit another ALL CAPS line or a line starting with a number (new clue)
                    while j < len(lines):
                        next_line = lines[j]
                        # Stop if we hit another ALL CAPS answer or a new clue number
                        if next_line.isupper() and len(next_line) > 2:
                            break
                        # Stop at clue numbers: "20", "20a", "20 ", "20a "
                        if re.match(r'^\d+[a-d]?(\s|$)', next_line):
                            break
                        # Add this line to the logic
                        logic_parts.append(next_line)
                        j += 1
                    
                    logic_map[line] = ' '.join(logic_parts).strip()
        return logic_map
    except:
        return {}

def get_logic_map_quick_cryptic(url, answers):
    """Scrapes Quick Cryptic format posts where answers aren't in ALL CAPS lines."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check for HTTP errors
        if r.status_code == 404:
            return {}
        elif r.status_code >= 400:
            return {}
        
        soup = BeautifulSoup(r.text, 'html.parser')
        # Try different content containers (timesforthetimes.co.uk vs LiveJournal)
        content = soup.find('div', class_='entry-content')
        if not content:
            content = soup.find('article', class_='aentry-post')
        if not content: return {}
        
        # Get all text as one block
        full_text = content.get_text(separator=' ', strip=True)
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # Split into sentences (periods followed by space and capital)
        sentences = re.split(r'(?<=\.)\s+(?=[A-Z])', full_text)
        
        logic_map = {}
        
        for answer in answers:
            answer_upper = str(answer).upper()
            
            # Look for sentences containing the answer
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Check if answer appears in sentence
                # Pattern 1: "ANSWER – logic text"
                if f'{answer_upper} ' in sentence or f' {answer_upper}' in sentence:
                    # Extract the logic part (after the answer and any dash)
                    match = re.search(rf'{re.escape(answer_upper)}\s*[-–]\s*(.*?)(?:\s+\d+\.?)?$', sentence)
                    if match:
                        logic = match.group(1).strip()
                        if logic and len(logic) > 3:  # Avoid very short matches
                            logic_map[answer_upper] = logic
                            break
                    # If no dash found, just use the sentence if it has wordplay indicators
                    elif any(kw in sentence.lower() for kw in ['anagram', 'hidden', 'reversal', 'inside', 'containing', 'around', '(', ')']):
                        logic_map[answer_upper] = sentence
                        break
        
        return logic_map
    except:
        return {}

def get_logic_map_fifteensquared(url):
    """Scrapes fifteensquared.net posts with table structure and builds {ANSWER: LOGIC} dictionary."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        # Check for HTTP errors
        if r.status_code == 404:
            print(f"    [404] Entry not found")
            return {}
        elif r.status_code >= 400:
            print(f"    [HTTP {r.status_code}] Error accessing page")
            return {}
        
        soup = BeautifulSoup(r.text, 'html.parser')
        entry = soup.find('div', class_='entry-content')
        
        if not entry:
            return {}
        
        tables = entry.find_all('table')
        logic_map = {}
        
        # If tables exist, use table-based parsing
        if tables:
            for table in tables:
                rows = table.find_all('tr')
                current_clue = None
                
                for row in rows:
                    cells = [clean_text(cell.get_text()) for cell in row.find_all('td')]
                    
                    # Skip empty rows
                    if not cells or not any(cells):
                        continue
                    
                    # CHECK: Is this a 'Clue Row'?
                    # Usually starts with a number (e.g., '1', '10', '1/19')
                    if re.match(r'^\d+', cells[0]):
                        # If we had a previous clue that didn't get an explanation, save it now
                        if current_clue:
                            answer_upper = current_clue['answer'].upper()
                            logic_map[answer_upper] = current_clue.get('explanation', '')
                        
                        # Create a new clue dictionary
                        current_clue = {
                            'id': cells[0],
                            'answer': cells[1] if len(cells) > 1 else "",
                            'clue': cells[2] if len(cells) > 2 else "",
                            'explanation': ""
                        }
                    
                    # CHECK: Is this an 'Explanation Row'?
                    # It follows a clue and often starts with a blank or a symbol
                    elif current_clue and (not cells[0] or cells[0] == '|'):
                        # Combine all cell content into the explanation
                        current_clue['explanation'] = " ".join(cells[1:])
                        answer_upper = current_clue['answer'].upper()
                        logic_map[answer_upper] = current_clue['explanation']
                        current_clue = None  # Reset for the next pair
                
                # Handle last clue if it didn't get an explanation
                if current_clue:
                    answer_upper = current_clue['answer'].upper()
                    logic_map[answer_upper] = current_clue.get('explanation', '')
        
        # If no tables found, try paragraph-based format
        else:
            # Some fifteensquared posts use paragraph format: numbered clues followed by ANSWER then logic
            lines = [l.strip() for l in entry.get_text(separator='\n').split('\n') if l.strip()]
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Look for clue numbers (e.g., "1.", "10.", "1d")
                if re.match(r'^\d+[a-d]?\.?$', line):
                    # Next few lines are: clue text, definition, (length), ANSWER, logic
                    answer_line = None
                    logic_start = None
                    
                    # Search forward for ALL CAPS answer (typically within 5-7 lines)
                    for j in range(i + 1, min(i + 8, len(lines))):
                        if lines[j].isupper() and len(lines[j]) > 2 and not re.match(r'^\d+', lines[j]):
                            # Found answer in all caps
                            answer_line = j
                            logic_start = j + 1
                            break
                    
                    if answer_line and logic_start < len(lines):
                        answer = lines[answer_line]
                        # Collect logic (typically 1-2 lines after answer)
                        logic_parts = []
                        for k in range(logic_start, min(logic_start + 3, len(lines))):
                            next_line = lines[k]
                            # Stop if we hit another clue number
                            if re.match(r'^\d+[a-d]?\.?$', next_line):
                                break
                            # Stop if we hit another ALL CAPS answer
                            if next_line.isupper() and len(next_line) > 2:
                                break
                            logic_parts.append(next_line)
                        
                        if logic_parts:
                            logic_map[answer] = ' '.join(logic_parts).strip()
                        
                        i = logic_start + len(logic_parts)
                        continue
                
                i += 1
        
        return logic_map
    except Exception as e:
        print(f"  Error parsing fifteensquared: {e}")
        return {}

def get_logic_map_bigdave44(url):
    """Scrapes bigdave44.com blog posts and builds {ANSWER: LOGIC} dictionary.
    
    Extracts ALL clues/answers/explanations from page, regardless of CSV content.
    The matching to CSV answers happens during enrichment.
    
    BigDave44 pages have structure:
    - Line: "1a    Clue text (length) Click here!: explanation [ANSWER]"
    - OR Line: "1a    Clue text (length)"
    - Next lines: continuation of clue
    - Line: "ANSWER" (standalone)
    - Line: ": explanation text"
    
    Answers may be:
    1. Standalone uppercase lines (original format)
    2. Embedded in brackets [ANSWER] within explanation text (common format)
    
    Returns:
        {ANSWER: LOGIC} dictionary keyed by answer (uppercase)
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        
        if r.status_code == 404:
            print(f"    [404] Entry not found")
            return {}
        elif r.status_code >= 400:
            print(f"    [HTTP {r.status_code}] Error accessing page")
            return {}
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Find the main content area
        content = soup.find('div', class_='entry-content')
        if not content:
            content = soup.find('article')
        if not content:
            return {}
        
        # Get all text lines
        lines = [l.strip() for l in content.get_text(separator='\n').split('\n') if l.strip()]
        
        logic_map = {}
        
        # Parse clues: look for lines starting with number(a/d)
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Match clue number line: "1a" or "1a    Clue text..." (whitespace optional due to line breaks)
            if re.match(r'^\d+[ad](?:\s|$)', line):
                clue_and_explanation = [line]
                
                # Collect continuation lines until we find ANSWER or hit next clue
                j = i + 1
                answer_line = None
                explanation_lines = []
                clue_ended = False
                
                while j < len(lines):
                    next_line = lines[j]
                    
                    # Stop at next clue or section header
                    if re.match(r'^\d+[ad](?:\s|$)', next_line) or next_line in ['Down', 'Across']:
                        clue_ended = True
                        break
                    
                    # Is this an answer? (all uppercase, no colons, not a clue number)
                    # Relaxed filter: allow brackets and parens for answers like "PAK CHOI" or "[ANSWER]"
                    if (next_line and next_line.isupper() and 
                        len(next_line.replace(' ', '')) > 1 and
                        ':' not in next_line and  # Colons indicate explanation start
                        not re.match(r'^\d+[ad]', next_line) and
                        next_line not in ['DOWN', 'ACROSS']):
                        
                        answer_line = next_line
                        
                        # Now get explanation (starts with ':')
                        if j + 1 < len(lines) and lines[j + 1].startswith(':'):
                            explanation_lines = [lines[j + 1][1:].strip()]
                            
                            # Collect more explanation lines
                            k = j + 2
                            while k < len(lines):
                                exp_line = lines[k].strip()
                                # Stop at next clue or section
                                if (re.match(r'^\d+[ad](?:\s|$)', exp_line) or 
                                    exp_line in ['Down', 'Across']):
                                    break
                                # Stop if we hit another uppercase answer
                                if (exp_line.isupper() and len(exp_line) > 3 and 
                                    ':' not in exp_line and
                                    not any(word in exp_line for word in ['CLICK', 'HERE'])):
                                    break
                                if exp_line:
                                    explanation_lines.append(exp_line)
                                k += 1
                        
                        # Store the mapping
                        answer_upper = answer_line.upper().strip()
                        explanation = ' '.join(explanation_lines).strip()
                        logic_map[answer_upper] = explanation
                        
                        i = j
                        break
                    else:
                        # Continuation of clue or explanation text
                        clue_and_explanation.append(next_line)
                        j += 1
                
                # FALLBACK: If no standalone answer found, extract from brackets in collected text
                if not answer_line:
                    full_text = ' '.join(clue_and_explanation)
                    # Look for [ANSWER] pattern - answers are often in brackets after explanation
                    bracket_match = re.search(r'\[([A-Za-z\s]+)\]', full_text)
                    if bracket_match:
                        candidate_answer = bracket_match.group(1).upper().strip()
                        # Validate: mostly letters/spaces, >2 non-space chars
                        if (len(candidate_answer.replace(' ', '')) > 2 and 
                            candidate_answer.replace(' ', '').replace('-', '').isalpha()):
                            # Extract explanation: everything after ":..."
                            colon_pos = full_text.find(':')
                            if colon_pos >= 0:
                                explanation = full_text[colon_pos + 1:].strip()
                                # Remove trailing bracketed answer from explanation
                                explanation = re.sub(r'\[[^\]]+\]\s*$', '', explanation).strip()
                            else:
                                explanation = full_text
                            
                            logic_map[candidate_answer] = explanation
                
                i += 1
            else:
                # Not a clue line
                i += 1
        
        return logic_map
    except Exception as e:
        print(f"  Error parsing bigdave44: {e}")
        return {}

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Enrich crossword clues CSV with logic explanations from online sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enrich_ho_data.py
  python enrich_ho_data.py --input ho_clues_full.csv
    python enrich_ho_data.py --input ho_clues_full.csv --limit 200
  python enrich_ho_data.py -i data.csv -o results.csv
        """
    )
    parser.add_argument('-i', '--input', 
                        default='ho_clues_sample.csv',
                        help='Input CSV file (default: ho_clues_sample.csv)')
    parser.add_argument('-o', '--output',
                        default=None,
                        help='Output CSV file (default: auto-generated from input name)')
    parser.add_argument('-n', '--limit',
                        type=int,
                        default=0,
                        help='Maximum number of rows to process from input (0 = no limit)')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        exit(1)

    # Validate limit value
    if args.limit < 0:
        print("Error: --limit must be 0 or a positive integer")
        exit(1)
    
    # Generate output filename if not specified
    if args.output is None:
        base_name = os.path.splitext(args.input)[0]
        args.output = f'{base_name}_enriched.csv'
    
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}\n")

    if args.limit == 0:
        print("Row limit: no limit (processing all rows)\n")
        df = pd.read_csv(args.input)
    else:
        print(f"Row limit: first {args.limit} rows\n")
        df = pd.read_csv(args.input, nrows=args.limit)
    
    # Add clue column if not present (will be populated from CSV if it exists)
    if 'clue' not in df.columns:
        print("Warning: 'clue' column not found in input CSV (required for bigdave44 matching)\n")

# ============================================================================
# CACHE MANAGEMENT FUNCTIONS
# ============================================================================
def get_checkpoint_file(input_file):
    """Generate checkpoint filename from input CSV path."""
    base_dir = os.path.dirname(input_file) or '.'
    base_name = os.path.basename(input_file)
    checkpoint = os.path.join(base_dir, f'.logic_cache_{base_name}.json')
    return checkpoint

def load_cache(checkpoint_file):
    """Load cache from JSON file if it exists."""
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            print(f"  [RESUME] Loaded existing cache from {os.path.basename(checkpoint_file)}")
            return cache
        except Exception as e:
            print(f"  [WARNING] Could not load cache: {e}, starting fresh")
            return {}
    return {}

def save_cache(cache, checkpoint_file):
    """Save cache to JSON file."""
    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"  [WARNING] Could not save cache: {e}")

# 1. Extract unique URLs to scrape from the CSV
# Use different keys for different sources
# - fifteensquared: key on source_url (from CSV)
# - times_xwd_times: key on puzzle_name (to avoid stale LiveJournal URLs)
checkpoint_file = get_checkpoint_file(args.input)
logic_cache = load_cache(checkpoint_file)

print("Step 1: Scraping Logic from Source URLs...\n")

# Track URLs processed across all sources for checkpointing
urls_scraped = 0
CHECKPOINT_INTERVAL = 1000

# Process fifteensquared.net clues using CSV source_url
print("  [FIFTEENSQUARED] Processing CSV URLs...")
fifteensquared_urls = df[df['source'] == 'fifteensquared'][['source_url']].drop_duplicates()
fifteensquared_cached = sum(1 for url in fifteensquared_urls['source_url'] 
                            if pd.notna(url) and url in logic_cache)
print(f"    -> {fifteensquared_cached} already cached")

for _, row in fifteensquared_urls.iterrows():
    url = row['source_url']
    
    if pd.isna(url) or url == '':
        print(f"    [SKIP] Empty URL")
        continue
    
    # Skip if already cached
    if url in logic_cache:
        print(f"    [CACHED] {url}")
        continue
    
    print(f"    [SCRAPING] {url}")
    logic_map = get_logic_map_fifteensquared(url)
    print(f"      -> {len(logic_map)} clues found")
    
    logic_cache[url] = logic_map
    urls_scraped += 1
    
    # Checkpoint every 1000 URLs
    if urls_scraped % CHECKPOINT_INTERVAL == 0:
        save_cache(logic_cache, checkpoint_file)
        print(f"    [CHECKPOINT] Saved {urls_scraped} URLs to {os.path.basename(checkpoint_file)}")
    
    time.sleep(1)

# Process bigdave44.com clues using CSV source_url
print("\n  [BIGDAVE44] Processing CSV URLs...")
bigdave44_urls = df[df['source'] == 'bigdave44'][['source_url']].drop_duplicates()
bigdave44_cached = sum(1 for url in bigdave44_urls['source_url'] 
                       if pd.notna(url) and url in logic_cache)
print(f"    -> {bigdave44_cached} already cached")

for _, row in bigdave44_urls.iterrows():
    url = row['source_url']
    
    if pd.isna(url) or url == '':
        print(f"    [SKIP] Empty URL")
        continue
    
    # Skip if already cached
    if url in logic_cache:
        print(f"    [CACHED] {url}")
        continue
    
    print(f"    [SCRAPING] {url}")
    
    logic_map = get_logic_map_bigdave44(url)
    print(f"      -> {len(logic_map)} clues found")
    
    logic_cache[url] = logic_map
    urls_scraped += 1
    
    # Checkpoint every 1000 URLs
    if urls_scraped % CHECKPOINT_INTERVAL == 0:
        save_cache(logic_cache, checkpoint_file)
        print(f"    [CHECKPOINT] Saved {urls_scraped} URLs to {os.path.basename(checkpoint_file)}")
    
    time.sleep(1)

# Process times_xwd_times clues using date-based discovery
print("\n  [TIMES_XWD_TIMES] Using date-based discovery (do not use CSV URLs)...")
times_puzzles = df[df['source'] == 'times_xwd_times'][['puzzle_name', 'puzzle_date']].drop_duplicates()
times_cached = sum(1 for p_name in times_puzzles['puzzle_name'] 
                   if p_name in logic_cache)
print(f"    -> {times_cached} already cached")

for _, row in times_puzzles.iterrows():
    p_name = row['puzzle_name']
    p_date = row['puzzle_date']
    
    # Skip if puzzle_date is missing (NaN)
    if pd.isna(p_date):
        print(f"    [SKIP] Missing puzzle_date for '{p_name}'")
        continue
    
    # Skip if already cached
    if p_name in logic_cache:
        print(f"    [CACHED] {p_name}")
        continue
    
    # Extract puzzle ID from puzzle_name (e.g., "Times 27424" -> "27424")
    # Also detect if Quick Cryptic (contains "Quick")
    is_quick = 'Quick' in p_name
    puzzle_id = re.search(r'(\d+)$', p_name)
    
    if not puzzle_id:
        print(f"    [SKIP] Cannot extract puzzle ID from '{p_name}'")
        continue
    
    puzzle_id = puzzle_id.group(1)
    
    print(f"    [DISCOVERING] {p_name} (date: {p_date}, ID: {puzzle_id}, Quick: {is_quick})")
    url = find_post_on_day(p_date, puzzle_id, is_quick)
    
    if not url:
        print(f"      -> Could not find post on timesforthetimes.co.uk for {p_date}")
        logic_cache[p_name] = {}
        urls_scraped += 1
        
        # Checkpoint every 1000 URLs
        if urls_scraped % CHECKPOINT_INTERVAL == 0:
            save_cache(logic_cache, checkpoint_file)
            print(f"    [CHECKPOINT] Saved {urls_scraped} URLs to {os.path.basename(checkpoint_file)}")
        
        continue
    
    print(f"      -> Found: {url}")
    
    # Try standard Times format first
    logic_map = get_logic_map(url)
    
    # If we got very few results, it might be Quick Cryptic format
    if len(logic_map) < 5:
        puzzle_answers = df[df['puzzle_name'] == p_name]['answer'].tolist()
        logic_map_qc = get_logic_map_quick_cryptic(url, puzzle_answers)
        if len(logic_map_qc) > len(logic_map):
            logic_map = logic_map_qc
            print(f"      -> Quick Cryptic format: {len(logic_map)} clues found")
        else:
            print(f"      -> Times format: {len(logic_map)} clues found")
    else:
        print(f"      -> Times format: {len(logic_map)} clues found")
    
    logic_cache[p_name] = logic_map
    urls_scraped += 1
    
    # Checkpoint every 1000 URLs
    if urls_scraped % CHECKPOINT_INTERVAL == 0:
        save_cache(logic_cache, checkpoint_file)
        print(f"    [CHECKPOINT] Saved {urls_scraped} URLs to {os.path.basename(checkpoint_file)}")
    time.sleep(1)

# Final save of cache after all scraping is complete
save_cache(logic_cache, checkpoint_file)
print(f"\n[FINAL SAVE] Completed {urls_scraped} total URLs, cache saved to {os.path.basename(checkpoint_file)}")

print("\nStep 2: Enriching Clues...")
def apply_logic(row):
    source = row.get('source', '')
    ans = str(row['answer']).upper()
    
    if source == 'fifteensquared':
        # Fifteensquared: lookup by source_url
        cache_key = row.get('source_url')
        if pd.isna(cache_key) or cache_key == '':
            return "URL not found"
        return logic_cache.get(cache_key, {}).get(ans, "Logic not found")
    
    elif source == 'times_xwd_times':
        # Times: lookup by puzzle_name (discovered via date-based URL discovery)
        cache_key = row.get('puzzle_name')
        if pd.isna(cache_key) or cache_key == '':
            return "Puzzle name not found"
        return logic_cache.get(cache_key, {}).get(ans, "Logic not found")
    
    elif source == 'bigdave44':
        # BigDave44: lookup by source_url
        cache_key = row.get('source_url')
        if pd.isna(cache_key) or cache_key == '':
            return "URL not found"
        return logic_cache.get(cache_key, {}).get(ans, "Logic not found")
    
    else:
        return None  # Return None for unknown sources (to be filtered out)

df['logic'] = df.apply(apply_logic, axis=1)

# Filter to only rows with recognized sources (remove Unknown source rows)
df = df[df['logic'].notna()]

# 3. Save
import shutil
df.to_csv(args.output, index=False)

remaining_clues = len(df[df['logic'] != 'Logic not found'])
print(f"\nDone! Enriched {remaining_clues} out of {len(df)} clues (non-recognized sources skipped).")
print(f"Output saved to: {args.output}")