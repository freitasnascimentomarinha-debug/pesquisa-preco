#!/usr/bin/env python3
import requests
from urllib.parse import quote_plus, unquote
from bs4 import BeautifulSoup

s = requests.Session()
h = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.5,en;q=0.3',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

query = 'caneta preço comprar'

print('=== DuckDuckGo HTML ===')
try:
    r = s.get(f'https://html.duckduckgo.com/html/?q={quote_plus(query)}', headers=h, timeout=15)
    print(f'Status: {r.status_code}, Len: {len(r.text)}')
    soup = BeautifulSoup(r.text, 'html.parser')
    res = soup.select('a.result__a')
    print(f'result__a count: {len(res)}')
    for x in res[:5]:
        print(f'  href: {x.get("href","")[:100]}')
    if not res:
        # Check what's in the page
        all_a = soup.find_all('a', href=True)
        print(f'Total <a>: {len(all_a)}')
        for a in all_a[:10]:
            print(f'  <a class="{a.get("class","")}" href="{a["href"][:80]}">')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

print()
print('=== Bing ===')
try:
    r = s.get(f'https://www.bing.com/search?q={quote_plus(query)}&setlang=pt-BR', headers=h, timeout=15)
    print(f'Status: {r.status_code}, Len: {len(r.text)}')
    soup = BeautifulSoup(r.text, 'html.parser')
    algos = soup.select('li.b_algo')
    print(f'b_algo count: {len(algos)}')
    for a in algos[:5]:
        link = a.select_one('h2 a')
        if link:
            print(f'  {link.get("href","")[:100]}')
    if not algos:
        all_h2 = soup.find_all('h2')
        print(f'Total h2: {len(all_h2)}')
        for hh in all_h2[:5]:
            aa = hh.find('a', href=True)
            if aa:
                print(f'  h2>a: {aa["href"][:100]}')
        br = soup.find(id='b_results')
        print(f'b_results found: {br is not None}')
        if 'captcha' in r.text.lower() or 'robot' in r.text.lower():
            print('CAPTCHA/robot detected!')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

print()
print('=== Google ===')
try:
    gh = dict(h)
    gh['Referer'] = 'https://www.google.com.br/'
    r = s.get(f'https://www.google.com.br/search?q={quote_plus(query)}&hl=pt-BR&num=5', headers=gh, timeout=15)
    print(f'Status: {r.status_code}, Len: {len(r.text)}')
    if 'unusual traffic' in r.text.lower() or 'captcha' in r.text.lower():
        print('CAPTCHA detected!')
    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/url?q='):
            real = unquote(href.split('/url?q=')[1].split('&')[0])
            if real.startswith('http'):
                links.append(real)
    print(f'/url?q= links: {len(links)}')
    for l in links[:5]:
        print(f'  {l[:100]}')
    # Try direct links
    if not links:
        direct = [a['href'] for a in soup.select('a[href^="http"]') if 'google' not in a['href']]
        print(f'Direct links (non-google): {len(direct)}')
        for l in direct[:5]:
            print(f'  {l[:100]}')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

print()
print('=== duckduckgo_search package ===')
try:
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text(query, region='br-pt', max_results=5))
    print(f'Results: {len(results)}')
    for r in results[:5]:
        print(f'  {r.get("title","")[:50]} -> {r.get("href","")[:80]}')
except ImportError:
    print('duckduckgo_search not installed')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')

print()
print('=== ddgs package ===')
try:
    from ddgs import DDGS
    results = list(DDGS().text(query, region='br-pt', max_results=5))
    print(f'Results: {len(results)}')
    for r in results[:5]:
        print(f'  {r.get("title","")[:50]} -> {r.get("href","")[:80]}')
except ImportError:
    print('ddgs not installed')
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
