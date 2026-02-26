import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_latest_post_links(category_url, limit=3):
    """Finds the URLs for the most recent blog posts."""
    response = requests.get(category_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to load index: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    # Find all h2 headers which usually contain post links in WordPress
    links = []
    for h2 in soup.find_all('h2', class_='entry-title'):
        a_tag = h2.find('a')
        if a_tag and 'href' in a_tag.attrs:
            links.append(a_tag['href'])
    
    return links[:limit]

def parse_post(url):
    """Extracts clue data from a specific post."""
    print(f"\n--- Scraping: {url} ---")
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    entry = soup.find('div', class_='entry-content')
    
    if not entry:
        return

    # Look for tables first
    tables = entry.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            cells = [cell.get_text(strip=True) for cell in row.find_all('td')]
            if cells:
                print(f"Found Clue: {' | '.join(cells)}")

# EXECUTION
index_url = "https://www.fifteensquared.net/category/independent/"
latest_links = get_latest_post_links(index_url)

for link in latest_links:
    parse_post(link)
    time.sleep(2)  # Be polite to the server!