# Test 1: ddgs package
print('=== Test ddgs ===')
try:
    from ddgs import DDGS
    results = list(DDGS().text('caneta esferográfica preço', region='br-pt', max_results=5))
    print(f'Results: {len(results)}')
    for i, r in enumerate(results):
        print(f'{i+1}. {r.get("title","")[:50]} -> {r.get("href","")[:80]}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

print()

# Test 2: Debug Bing HTML structure
print('=== Debug Bing HTML ===')
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.5,en;q=0.3',
}

query = 'caneta esferográfica preço'
url = f'https://www.bing.com/search?q={quote_plus(query)}&setlang=pt-BR'
resp = session.get(url, headers=headers, timeout=15)
soup = BeautifulSoup(resp.text, 'html.parser')

# Print all classes used in <li> tags
li_classes = set()
for li in soup.find_all('li', class_=True):
    for c in li.get('class', []):
        li_classes.add(c)
print(f'LI classes: {sorted(li_classes)[:20]}')

# Print all <h2> tags (common for search results)
h2_tags = soup.find_all('h2')
print(f'H2 count: {len(h2_tags)}')
for h in h2_tags[:5]:
    a = h.find('a', href=True)
    if a:
        print(f'  H2+A: {a.get_text(strip=True)[:50]} -> {a["href"][:80]}')

# Look for divs with id='b_results' or similar
b_results = soup.find(id='b_results')
if b_results:
    print(f'b_results found, children: {len(list(b_results.children))}')
    for child in list(b_results.children)[:3]:
        if hasattr(child, 'get'):
            print(f'  child class: {child.get("class")}, tag: {child.name}')
else:
    print('b_results NOT found')

# Print title to verify page loaded
print(f'Page title: {soup.title.string if soup.title else "None"}')

# Check for CAPTCHA indicators
captcha_indicators = ['captcha', 'challenge', 'verify', 'blocked', 'robot']
text_lower = resp.text.lower()
for ind in captcha_indicators:
    if ind in text_lower:
        print(f'Found indicator: {ind}')
