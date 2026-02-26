"""
FILE: scrape_and_pair.py
DESCRIPTION: 
    Extracts crossword clues from Fifteensquared.net, pairing the 
    clue/answer row with the wordplay explanation row that follows it.
    
DEPENDENCIES: 
    pip install requests beautifulsoup4

RUNNING THE SCRIPT:
    python scrape_and_pair.py

EXPECTED OUTPUT:
    --- Processing: [URL] ---
    ID: 1/19 | Clue: Criticise terrible roads... | Answer: PANDORAS JAR
    Logic: PAN (ROADS)*AInd: terribleJAR (shock)...
    --------------------------------------------------
"""

import requests
from bs4 import BeautifulSoup
import time
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_text(text):
    """Removes non-breaking spaces and extra whitespace."""
    return text.replace('\xa0', ' ').strip()

def parse_fifteensquared_post(url):
    print(f"\n--- Processing: {url} ---")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    entry = soup.find('div', class_='entry-content')
    
    if not entry: return

    tables = entry.find_all('table')
    all_data = []

    for table in tables:
        rows = table.find_all('tr')
        current_clue = None

        for row in rows:
            cells = [clean_text(cell.get_text()) for cell in row.find_all('td')]
            
            # Skip empty rows
            if not cells or not any(cells): continue

            # CHECK: Is this a 'Clue Row'? 
            # Usually starts with a number (e.g., '1', '10', '1/19')
            if re.match(r'^\d+', cells[0]):
                # If we had a previous clue that didn't get an explanation, save it now
                if current_clue:
                    all_data.append(current_clue)
                
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
                all_data.append(current_clue)
                current_clue = None # Reset for the next pair

    # Print a summary of what we found
    for item in all_data[:5]: # Print first 5 for brevity
        print(f"ID: {item['id']} | Answer: {item['answer']}")
        print(f"Clue: {item['clue']}")
        print(f"Logic: {item['explanation']}")
        print("-" * 50)

# EXECUTION
test_url = "https://www.fifteensquared.net/2026/02/14/independent-12279-by-mev/"
parse_fifteensquared_post(test_url)