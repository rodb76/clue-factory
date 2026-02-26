"""
FILE: crossword_to_csv.py
DESCRIPTION: 
    Parses Timesforthetimes and saves ID, Answer, Clue, and Logic 
    into a structured CSV file.
    
RUNNING THE SCRIPT:
    python crossword_to_csv.py

EXPECTED OUTPUT:
    A file named 'crossword_data.csv' will appear in your directory.
    The console will confirm how many clues were saved.
"""

import requests
from bs4 import BeautifulSoup
import re
import csv

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def save_to_csv(data, filename="crossword_data.csv"):
    """Writes a list of dictionaries to a CSV file."""
    keys = ["ID", "Answer", "Clue", "Logic"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"\n[Success] {len(data)} clues saved to {filename}")

def scrape_times_to_list(url):
    print(f"--- Processing: {url} ---")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    content = soup.find('div', class_='entry-content')
    
    if not content:
        return []

    lines = [l.strip() for l in content.get_text(separator='\n').split('\n') if l.strip()]
    
    scraped_data = []
    current_id = None
    clue_buffer = []

    for i in range(len(lines)):
        line = lines[i]

        # 1. ID Detection
        if re.match(r'^\d{1,2}$', line):
            current_id = line
            clue_buffer = []
            continue
        
        # 2. Answer Detection (Upper case check)
        if current_id and line.isupper() and len(line) > 1:
            answer = line
            clue_text = " ".join(clue_buffer)
            
            # 3. Logic Detection (Next line)
            explanation = lines[i+1] if i + 1 < len(lines) else ""

            # Store in list of dictionaries
            scraped_data.append({
                "ID": current_id,
                "Answer": answer,
                "Clue": clue_text,
                "Logic": explanation
            })
            
            current_id = None
            clue_buffer = []
        
        elif current_id:
            clue_buffer.append(line)
            
    return scraped_data

# EXECUTION
target_url = "https://timesforthetimes.co.uk/times-28840"
results = scrape_times_to_list(target_url)

if results:
    save_to_csv(results)