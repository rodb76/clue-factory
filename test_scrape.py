import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

url = 'https://timesforthetimes.co.uk/times-27424-id-rather-have-a-21-than-a-10'
r = requests.get(url, headers=HEADERS, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')

content = soup.find('div', class_='entry-content')

if content:
    print("=== Testing UPDATED method (replace inline tags first) ===")
    # Make a copy for testing
    import copy
    test_content = copy.copy(content)
    
    # Replace inline tags with their text
    for tag in test_content.find_all(['strike', 'del', 's', 'em', 'i', 'strong', 'b', 'span']):
        tag.replace_with(' ' + tag.get_text() + ' ')
    
    lines = [l.strip() for l in test_content.get_text(separator='\n').split('\n') if l.strip()]
    lines = [re.sub(r'\s+', ' ', line) for line in lines]
    
    print(f"Total lines: {len(lines)}")
    for i, line in enumerate(lines):
        if 'DYNASTY' in line:
            print(f"\nLine {i}: {repr(line[:200])}")
            if i+1 < len(lines):
                print(f"Line {i+1}: {repr(lines[i+1][:200])}")
    
    # Also check: what are the ALL CAPS lines?
    print("\n=== ALL CAPS lines ===")
    for i, line in enumerate(lines):
        if line.isupper() and len(line) > 2:
            print(f"Line {i}: {repr(line[:100])}")
            # Try to match logic on the same line
            match = re.search(rf"^([A-Z\s]+)\s*[-–—:.]\s*(.*)", line)
            if match:
                print(f"  -> Answer: {match.group(1).strip()}")
                print(f"  -> Logic: {match.group(2).strip()[:100]}")
else:
    print("Content div not found")
