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
    import copy
    test_content = copy.copy(content)
    
    # Replace inline tags with their text  
    for tag in test_content.find_all(['strike', 'del', 's', 'em', 'i', 'strong', 'b', 'span']):
        tag.replace_with(' ' + tag.get_text() + ' ')
    
    lines = [l.strip() for l in test_content.get_text(separator='\n').split('\n') if l.strip()]
    lines = [re.sub(r'\s+', ' ', line) for line in lines]
    
    # Show lines 115-122
    for i in range(115, min(122, len(lines))):
        print(f"Line {i}: {repr(lines[i])}")
