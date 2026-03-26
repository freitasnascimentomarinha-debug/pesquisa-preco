import streamlit as st
import pandas as pd
import time
import random
import re
import os
import base64
import json
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse, quote_plus

# Configuração da página
st.set_page_config(
    page_title="AtaCotada - Web Scraping",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado (mesmo padrão das outras páginas)
st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"],
        .main, [data-testid="stApp"], .stApp {
            background-color: #001a4d !important;
            color: #ffffff !important;
        }

        .stApp { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0.7; } to { opacity: 1; } }

        .header-container {
            background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
        }
        .logo-text { color: #ffffff; font-size: 14px; font-weight: 600; letter-spacing: 2px; margin-bottom: 0.5rem; }
        .sistema-nome {
            color: #d4af37; font-size: 48px; font-weight: bold; letter-spacing: 3px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5); margin: 0.5rem 0; font-family: 'Arial Black', sans-serif;
        }
        .subtitulo { color: #ffffff; font-size: 14px; margin-top: 0.5rem; letter-spacing: 1px; }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #d4af37 !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.5);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { background: transparent !important; }
        [data-testid="stSidebarNav"] { display: none !important; }

        [data-testid="stSidebar"] .stMarkdown h2 {
            color: #d4af37 !important;
            font-family: 'Arial Black', sans-serif;
            font-size: 22px;
            text-align: center;
            letter-spacing: 2px;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
            border-bottom: 2px solid #d4af37;
            padding-bottom: 0.75rem;
            margin-bottom: 1.5rem;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%) !important;
            color: #ffffff !important;
            border: 1px solid #333333 !important;
            border-radius: 10px !important;
            margin: 0.4rem 0 !important;
            padding: 0.85rem 1.2rem !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            transition: all 0.3s ease !important;
            text-decoration: none !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span { color: #ffffff !important; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
            background: linear-gradient(135deg, #252525 0%, #353535 100%) !important;
            border: 1px solid #d4af37 !important;
            transform: translateX(5px);
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25) !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover span { color: #d4af37 !important; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
            color: #0a0a0a !important;
            border: 1px solid #d4af37 !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4) !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span { color: #0a0a0a !important; }
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p { color: #ffffff !important; }
        [data-testid="stSidebar"] hr { border-color: #333333 !important; margin: 1rem 0 !important; }

        .info-card {
            background: rgba(0, 26, 77, 0.6);
            border: 1px solid #d4af37;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            margin-bottom: 1rem;
        }
        .info-title { color: #d4af37; font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; border-bottom: 1px solid rgba(212, 175, 55, 0.3); padding-bottom: 0.5rem; }

        .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
            background-color: #d4af37 !important; color: #ffffff !important; border: none !important; font-weight: bold !important;
        }
        .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
            background-color: #c5a028 !important; color: #ffffff !important;
        }

        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(0, 26, 77, 0.6);
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            color: #ffffff;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] {
            background-color: #d4af37 !important;
            color: #0a0a0a !important;
        }

        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border-radius: 8px;
            overflow: hidden;
        }
        th { background-color: #ffffff !important; color: #333333 !important; font-weight: bold; border-bottom: 2px solid #d4af37 !important; }
        td { background-color: #ffffff !important; color: #333333 !important; }

        .log-container {
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 1rem;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #00ff00;
            max-height: 400px;
            overflow-y: auto;
        }
        .log-info { color: #00ff00; }
        .log-warn { color: #ffaa00; }
        .log-error { color: #ff4444; }
        .log-success { color: #44ff44; font-weight: bold; }

        .screenshot-container {
            border: 2px solid #d4af37;
            border-radius: 8px;
            overflow: hidden;
            margin: 0.5rem 0;
        }

        .sidebar-footer {
            color: #666666;
            font-size: 11px;
            text-align: center;
            padding: 1rem 0;
            border-top: 1px solid #333333;
            margin-top: 2rem;
        }
    </style>
""", unsafe_allow_html=True)


# ===================== CONSTANTES =====================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
]

VARIANTES_BUSCA = [
    "{item} preço",
    "{item} comprar",
    "{item} fornecedor",
    "comprar {item} online",
    "{item} valor unitário",
    "{item} loja online",
]

# Domínios a ignorar nos resultados
DOMINIOS_IGNORADOS = [
    "google.com", "google.com.br", "youtube.com", "facebook.com",
    "instagram.com", "twitter.com", "linkedin.com", "wikipedia.org",
    "gov.br", "reddit.com", "tiktok.com",
    # Marketplaces
    "mercadolivre.com.br", "mercadolivre.com", "lista.mercadolivre.com.br",
    "produto.mercadolivre.com.br", "mlstatic.com",
    "magazineluiza.com.br", "magalu.com.br",
    "shopee.com.br", "shopee.com",
    "amazon.com.br", "amazon.com",
    "aliexpress.com", "aliexpress.com.br",
    "casasbahia.com.br", "pontofrio.com.br",
    "submarino.com.br", "americanas.com.br",
    "kabum.com.br", "zoom.com.br",
    "buscape.com.br", "bondfaro.com.br",
]

MAX_FONTES_POR_ITEM = 3
MAX_RETRIES = 2
SCREENSHOT_DIR = "/tmp/scraping_screenshots"

# SearchAPI.io (Google Shopping) — fallback quando DDGS falha
SEARCHAPI_KEY = "wZb2W9zvLh3gPziTp2639VCr"
SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"


# ===================== FUNÇÕES AUXILIARES =====================

def gerar_delay(min_seg=2.0, max_seg=6.0):
    """Delay aleatório entre requisições para simular comportamento humano."""
    return random.uniform(min_seg, max_seg)


def gerar_delay_leitura(min_seg=1.5, max_seg=4.0):
    """Delay de permanência na página simulando leitura."""
    return random.uniform(min_seg, max_seg)


def escolher_user_agent():
    """Seleciona um User-Agent aleatório."""
    return random.choice(USER_AGENTS)


def gerar_headers(user_agent=None):
    """Gera headers realistas de navegador."""
    ua = user_agent or escolher_user_agent()
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }


def dominio_valido(url):
    """Verifica se o domínio não está na lista de ignorados."""
    try:
        dominio = urlparse(url).netloc.lower()
        return not any(d in dominio for d in DOMINIOS_IGNORADOS)
    except Exception:
        return False


def extrair_dominio(url):
    """Extrai domínio limpo de uma URL."""
    try:
        return urlparse(url).netloc
    except Exception:
        return url


def log_msg(log_container, logs, msg, nivel="info"):
    """Adiciona mensagem de log e atualiza o container."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    classe = f"log-{nivel}"
    logs.append(f'<span class="{classe}">[{timestamp}] {msg}</span>')
    log_container.markdown(
        '<div class="log-container">' + "<br>".join(logs[-50:]) + "</div>",
        unsafe_allow_html=True,
    )


def formatar_moeda_br(valor):
    """Formata valor numérico para moeda brasileira."""
    try:
        val = float(valor)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "N/A"


# ===================== SCRAPING COM REQUESTS + BS4 =====================

def _dedup_urls(urls, num_results=8):
    """Remove duplicatas mantendo ordem e diversidade de domínios."""
    seen = set()
    unique = []
    for u in urls:
        dom = extrair_dominio(u)
        if dom not in seen:
            seen.add(dom)
            unique.append(u)
    return unique[:num_results]


def buscar_ddgs_api(query, num_results=8):
    """Busca usando o pacote ddgs (DuckDuckGo Search) — mais confiável em servidores."""
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, region="br-pt", max_results=num_results))
        urls = [r["href"] for r in results if r.get("href") and dominio_valido(r["href"])]
        return _dedup_urls(urls, num_results)
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="br-pt", max_results=num_results))
            urls = [r["href"] for r in results if r.get("href") and dominio_valido(r["href"])]
            return _dedup_urls(urls, num_results)
        except Exception:
            return []
    except Exception:
        return []


def buscar_duckduckgo(session, query, headers, num_results=8):
    """Busca no DuckDuckGo HTML usando requests e retorna lista de URLs."""
    from bs4 import BeautifulSoup
    from urllib.parse import unquote

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []

        for a_tag in soup.select("a.result__a"):
            href = a_tag.get("href", "")
            if href.startswith("//duckduckgo.com/l/?uddg="):
                real_url = unquote(href.split("uddg=")[1].split("&")[0])
            elif href.startswith("http"):
                real_url = href
            else:
                continue
            if real_url.startswith("http") and dominio_valido(real_url):
                urls.append(real_url)

        # Fallback: links dentro de .result__body ou .result
        if not urls:
            for a_tag in soup.select(".result a[href^='http']"):
                href = a_tag.get("href", "")
                if dominio_valido(href):
                    urls.append(href)

        return _dedup_urls(urls, num_results)

    except Exception:
        return []


def buscar_google_requests(session, query, headers, num_results=8):
    """Busca no Google usando requests (fallback)."""
    from bs4 import BeautifulSoup
    from urllib.parse import unquote

    url = f"https://www.google.com.br/search?q={quote_plus(query)}&hl=pt-BR&num={num_results}"
    google_headers = dict(headers)
    google_headers["Referer"] = "https://www.google.com.br/"
    google_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    try:
        resp = session.get(url, headers=google_headers, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("/url?q="):
                real_url = unquote(href.split("/url?q=")[1].split("&")[0])
                if real_url.startswith("http") and dominio_valido(real_url):
                    urls.append(real_url)

        if not urls:
            for a_tag in soup.select("a[href^='http']"):
                href = a_tag.get("href", "")
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        return _dedup_urls(urls, num_results)

    except Exception:
        return []


def buscar_bing_requests(session, query, headers, num_results=8):
    """Busca no Bing como fallback adicional."""
    from bs4 import BeautifulSoup

    url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=pt-BR&count={num_results}"
    bing_headers = dict(headers)
    bing_headers["Referer"] = "https://www.bing.com/"
    try:
        resp = session.get(url, headers=bing_headers, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []

        for li in soup.select("li.b_algo"):
            a_tag = li.select_one("h2 a")
            if a_tag:
                href = a_tag.get("href", "")
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        if not urls:
            for a_tag in soup.select("#b_results a[href^='http']"):
                href = a_tag.get("href", "")
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        return _dedup_urls(urls, num_results)

    except Exception:
        return []


def buscar_searchapi(query, num_results=8):
    """Busca usando SearchAPI.io (Google Shopping) — fallback pago e confiável.
    Retorna resultados diretos com preços já extraídos."""
    import requests as req

    if not SEARCHAPI_KEY:
        return []

    try:
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": SEARCHAPI_KEY,
            "location": "Brazil",
            "gl": "br",
            "hl": "pt",
            "num": num_results,
        }
        resp = req.get(SEARCHAPI_URL, params=params, timeout=20)
        if resp.status_code != 200:
            return []

        data = resp.json()
        shopping_results = data.get("shopping_results", [])

        resultados = []
        for item in shopping_results:
            preco = item.get("extracted_price")
            titulo = item.get("title", "")
            seller = item.get("seller", "Google Shopping")
            thumbnail = item.get("thumbnail", "")
            product_link = item.get("product_link", "")

            if preco and preco > 0 and titulo:
                resultados.append({
                    "titulo": titulo,
                    "preco": preco,
                    "url": product_link,
                    "dominio": seller,
                    "thumbnail": thumbnail,
                    "fonte": "Google Shopping (SearchAPI)",
                })

        return resultados[:num_results]

    except Exception:
        return []


def buscar_urls(session, query, headers, num_results=8):
    """Busca combinada: DDGS API > DuckDuckGo HTML > Google > Bing."""
    # 1. Tentar DDGS API (mais confiável em ambientes de servidor)
    urls = buscar_ddgs_api(query, num_results)
    if urls:
        return urls, "DDGS API"
    # 2. DuckDuckGo HTML scraping
    urls = buscar_duckduckgo(session, query, headers, num_results)
    if urls:
        return urls, "DuckDuckGo HTML"
    # 3. Google
    urls = buscar_google_requests(session, query, headers, num_results)
    if urls:
        return urls, "Google"
    # 4. Bing
    urls = buscar_bing_requests(session, query, headers, num_results)
    if urls:
        return urls, "Bing"
    return [], "nenhum"


def extrair_precos_pagina(html_content):
    """Extrai possíveis preços de uma página HTML."""
    precos = []

    # Padrões de preço em reais
    padroes = [
        r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"R\$\s*(\d+,\d{2})",
        r"(?:por|preço|valor|price)[\s:]*R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
    ]

    for padrao in padroes:
        matches = re.findall(padrao, html_content, re.IGNORECASE)
        for match in matches:
            try:
                valor_str = match.replace(".", "").replace(",", ".")
                valor = float(valor_str)
                if 0.01 < valor < 1_000_000:  # Filtra valores absurdos
                    precos.append(valor)
            except (ValueError, TypeError):
                continue

    return sorted(set(precos))


def extrair_titulo_pagina(html_content):
    """Extrai o título da página."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        return title_tag.string.strip()[:120]
    h1_tag = soup.find("h1")
    if h1_tag:
        return h1_tag.get_text(strip=True)[:120]
    return "Sem título"


def scraping_requests(session, url, headers):
    """Acessa uma página via requests e extrai informações."""
    from bs4 import BeautifulSoup

    try:
        resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        if resp.status_code != 200:
            return None

        html = resp.text
        titulo = extrair_titulo_pagina(html)
        precos = extrair_precos_pagina(html)

        if not precos:
            return None

        # Pegar o preço mais provável (mediana dos encontrados)
        preco_medio = sorted(precos)[len(precos) // 2]

        # Gerar screenshot HTML como evidência (sem precisar de Playwright)
        screenshot_path = None
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Remover scripts e styles para captura limpa
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            body_text = soup.get_text(separator="\n", strip=True)[:3000]
            # Salvar captura como imagem via HTML renderizado
            screenshot_dir = SCREENSHOT_DIR
            os.makedirs(screenshot_dir, exist_ok=True)
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', titulo[:40])
            snapshot_path = os.path.join(screenshot_dir, f"{safe_name}_{hash(url) % 10000}.html")
            with open(snapshot_path, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{titulo}</title>
<style>body{{font-family:Arial;padding:20px;max-width:900px;margin:auto;background:#f5f5f5}}
.header{{background:#001a4d;color:#d4af37;padding:15px;border-radius:8px;margin-bottom:15px}}
.price{{color:#006600;font-size:24px;font-weight:bold;margin:10px 0}}
.url{{color:#666;font-size:12px;word-break:break-all}}
.content{{background:#fff;padding:15px;border-radius:8px;border:1px solid #ddd;white-space:pre-wrap;font-size:13px;max-height:600px;overflow:auto}}
</style></head><body>
<div class="header"><h2>{titulo}</h2>
<div class="price">Preço encontrado: R$ {preco_medio:,.2f}</div>
<div class="url">Fonte: {url}</div>
<div style="color:#fff;font-size:11px;margin-top:5px">Capturado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div></div>
<div class="content">{body_text[:2000]}</div>
</body></html>""")
            screenshot_path = snapshot_path
        except Exception:
            pass

        return {
            "titulo": titulo,
            "preco": preco_medio,
            "url": url,
            "dominio": extrair_dominio(url),
            "screenshot": screenshot_path,
        }
    except Exception:
        return None


# ===================== SCRAPING COM PLAYWRIGHT =====================

def _ensure_playwright_installed():
    """Verifica se playwright está instalado e instala browsers se necessário."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        return False


def scraping_playwright(url, item_nome, screenshot_path=None):
    """Acessa uma página via Playwright (para sites dinâmicos) e extrai informações."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    resultado = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )

            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=escolher_user_agent(),
                locale="pt-BR",
                timezone_id="America/Sao_Paulo",
            )

            page = context.new_page()

            # Navegar com timeout
            page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # Simular scroll humano
            page.evaluate("window.scrollBy(0, Math.random() * 400 + 200)")
            time.sleep(gerar_delay_leitura(1.0, 2.5))

            # Aguardar possível carregamento dinâmico
            page.wait_for_load_state("networkidle", timeout=10000)

            # Mais um scroll
            page.evaluate("window.scrollBy(0, Math.random() * 300 + 100)")
            time.sleep(random.uniform(0.5, 1.5))

            html = page.content()
            titulo = page.title() or extrair_titulo_pagina(html)
            precos = extrair_precos_pagina(html)

            # Captura de tela
            if screenshot_path and precos:
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                page.screenshot(path=screenshot_path, full_page=False)

            browser.close()

            if precos:
                preco_medio = sorted(precos)[len(precos) // 2]
                resultado = {
                    "titulo": titulo,
                    "preco": preco_medio,
                    "url": url,
                    "dominio": extrair_dominio(url),
                    "screenshot": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                }
    except Exception:
        pass

    return resultado


# ===================== ORQUESTRADOR DE SCRAPING =====================

def executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text):
    """Executa o scraping completo para todos os itens."""
    import requests as req

    logs = []
    resultados = []
    total_itens = len(itens)
    playwright_disponivel = usar_playwright and _ensure_playwright_installed()

    # Criar sessão reutilizável
    session = req.Session()
    ua = escolher_user_agent()
    headers = gerar_headers(ua)
    session.headers.update(headers)

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    for idx, item in enumerate(itens):
        item = item.strip()
        if not item:
            continue

        log_msg(log_container, logs, f"━━━ Iniciando busca: <b>{item}</b> ({idx+1}/{total_itens}) ━━━", "info")
        status_text.text(f"Buscando: {item} ({idx+1}/{total_itens})")
        progress_bar.progress((idx) / total_itens)

        orcamentos_item = []
        dominios_usados = set()

        # Selecionar variantes de busca aleatoriamente
        variantes = random.sample(VARIANTES_BUSCA, min(3, len(VARIANTES_BUSCA)))

        for variante in variantes:
            if len(orcamentos_item) >= MAX_FONTES_POR_ITEM:
                log_msg(log_container, logs, f"✓ {MAX_FONTES_POR_ITEM} orçamentos encontrados para '{item}'. Avançando.", "success")
                break

            query = variante.format(item=item)
            log_msg(log_container, logs, f"🔍 Buscando: \"{query}\"", "info")

            # Delay antes da busca
            delay = gerar_delay(2.0, 5.0)
            log_msg(log_container, logs, f"⏳ Aguardando {delay:.1f}s...", "info")
            time.sleep(delay)

            # Buscar URLs (DDGS API > DuckDuckGo HTML > Google > Bing)
            urls, engine = buscar_urls(session, query, headers)

            if not urls:
                log_msg(log_container, logs, f"⚠ Nenhum resultado encontrado para \"{query}\"", "warn")
                continue

            log_msg(log_container, logs, f"📋 {len(urls)} resultados encontrados via {engine}", "info")

            for url in urls:
                if len(orcamentos_item) >= MAX_FONTES_POR_ITEM:
                    break

                dominio = extrair_dominio(url)
                if dominio in dominios_usados:
                    continue

                log_msg(log_container, logs, f"🌐 Acessando: {dominio}", "info")

                # Delay entre acessos a sites
                delay = gerar_delay(2.5, 6.0)
                log_msg(log_container, logs, f"⏳ Delay de navegação: {delay:.1f}s", "info")
                time.sleep(delay)

                resultado = None
                screenshot_path = os.path.join(
                    SCREENSHOT_DIR,
                    f"{re.sub(r'[^a-zA-Z0-9]', '_', item)}_{len(orcamentos_item)+1}.png",
                )

                # Tentar com requests primeiro
                for tentativa in range(MAX_RETRIES + 1):
                    # Simular tempo de leitura
                    time.sleep(gerar_delay_leitura())

                    resultado = scraping_requests(session, url, headers)
                    if resultado:
                        break

                    if tentativa < MAX_RETRIES:
                        retry_delay = gerar_delay(3.0, 7.0)
                        log_msg(log_container, logs, f"🔄 Retry {tentativa+1}/{MAX_RETRIES} em {retry_delay:.1f}s...", "warn")
                        time.sleep(retry_delay)
                        # Trocar User-Agent no retry
                        headers = gerar_headers()
                        session.headers.update(headers)

                # Se requests falhou e Playwright disponível, tentar com Playwright
                if not resultado and playwright_disponivel:
                    log_msg(log_container, logs, f"🎭 Tentando com navegador automatizado: {dominio}", "info")
                    time.sleep(gerar_delay(1.5, 3.5))
                    resultado = scraping_playwright(url, item, screenshot_path)

                if resultado:
                    resultado["item"] = item
                    resultado["data_coleta"] = datetime.now().strftime("%d/%m/%Y %H:%M")

                    # Capturar screenshot via Playwright se ainda não temos
                    if playwright_disponivel and not resultado.get("screenshot"):
                        try:
                            _resultado_pw = scraping_playwright(url, item, screenshot_path)
                            if _resultado_pw and _resultado_pw.get("screenshot"):
                                resultado["screenshot"] = _resultado_pw["screenshot"]
                        except Exception:
                            pass

                    orcamentos_item.append(resultado)
                    dominios_usados.add(dominio)
                    log_msg(
                        log_container,
                        logs,
                        f"💰 Orçamento encontrado: {formatar_moeda_br(resultado['preco'])} em {dominio}",
                        "success",
                    )
                else:
                    log_msg(log_container, logs, f"✗ Sem preço extraível de {dominio}", "error")

        if not orcamentos_item:
            # Fallback: tentar SearchAPI (Google Shopping) que retorna preços diretos
            log_msg(log_container, logs, f"🛒 Tentando Google Shopping (SearchAPI) para '{item}'...", "info")
            searchapi_results = buscar_searchapi(item, MAX_FONTES_POR_ITEM)
            if searchapi_results:
                for sr in searchapi_results[:MAX_FONTES_POR_ITEM]:
                    sr["item"] = item
                    sr["data_coleta"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    orcamentos_item.append(sr)
                    log_msg(
                        log_container,
                        logs,
                        f"💰 Google Shopping: {formatar_moeda_br(sr['preco'])} — {sr['dominio']} ({sr['titulo'][:50]})",
                        "success",
                    )
            else:
                log_msg(log_container, logs, f"⚠ Nenhum orçamento encontrado para '{item}'", "warn")

        resultados.extend(orcamentos_item)

        # Delay maior entre itens diferentes
        if idx < total_itens - 1:
            delay = gerar_delay(4.0, 8.0)
            log_msg(log_container, logs, f"⏳ Intervalo entre itens: {delay:.1f}s", "info")
            time.sleep(delay)

    progress_bar.progress(1.0)
    log_msg(log_container, logs, f"━━━ Scraping concluído! {len(resultados)} orçamentos coletados ━━━", "success")
    status_text.text("Scraping concluído!")

    return resultados


# ===================== GERAÇÃO DE RELATÓRIO =====================

def gerar_relatorio_excel(resultados):
    """Gera relatório Excel com os resultados do scraping."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório de Cotações"

    # Estilos
    header_font = Font(name="Arial", bold=True, size=12, color="FFFFFF")
    header_fill = PatternFill(start_color="001A4D", end_color="001A4D", fill_type="solid")
    gold_font = Font(name="Arial", bold=True, size=14, color="D4AF37")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # Título
    ws.merge_cells("A1:F1")
    titulo_cell = ws["A1"]
    titulo_cell.value = "RELATÓRIO DE COTAÇÕES - WEB SCRAPING"
    titulo_cell.font = gold_font
    titulo_cell.alignment = Alignment(horizontal="center")
    titulo_cell.fill = PatternFill(start_color="0A0A0A", end_color="0A0A0A", fill_type="solid")

    ws.merge_cells("A2:F2")
    ws["A2"].value = f"Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = Font(name="Arial", size=10, color="666666")
    ws["A2"].alignment = Alignment(horizontal="center")

    # Cabeçalhos
    headers = ["Item", "Fornecedor/Site", "Preço", "Link", "Data da Coleta", "Título da Página"]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
        cell.border = border

    # Dados
    for row_idx, r in enumerate(resultados, 5):
        ws.cell(row=row_idx, column=1, value=r.get("item", "")).border = border
        ws.cell(row=row_idx, column=2, value=r.get("dominio", "")).border = border
        preco_cell = ws.cell(row=row_idx, column=3, value=r.get("preco", 0))
        preco_cell.number_format = 'R$ #,##0.00'
        preco_cell.border = border
        ws.cell(row=row_idx, column=4, value=r.get("url", "")).border = border
        ws.cell(row=row_idx, column=5, value=r.get("data_coleta", "")).border = border
        ws.cell(row=row_idx, column=6, value=r.get("titulo", "")).border = border

    # Resumo por item
    ws_resumo = wb.create_sheet("Resumo por Item")
    ws_resumo.merge_cells("A1:D1")
    ws_resumo["A1"].value = "RESUMO POR ITEM"
    ws_resumo["A1"].font = gold_font
    ws_resumo["A1"].fill = PatternFill(start_color="0A0A0A", end_color="0A0A0A", fill_type="solid")
    ws_resumo["A1"].alignment = Alignment(horizontal="center")

    resumo_headers = ["Item", "Menor Preço", "Maior Preço", "Preço Médio"]
    for col, h in enumerate(resumo_headers, 1):
        cell = ws_resumo.cell(row=3, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    df = pd.DataFrame(resultados)
    if not df.empty and "preco" in df.columns:
        resumo = df.groupby("item")["preco"].agg(["min", "max", "mean"]).reset_index()
        for row_idx, (_, row) in enumerate(resumo.iterrows(), 4):
            ws_resumo.cell(row=row_idx, column=1, value=row["item"]).border = border
            for c, col_name in enumerate(["min", "max", "mean"], 2):
                cell = ws_resumo.cell(row=row_idx, column=c, value=row[col_name])
                cell.number_format = 'R$ #,##0.00'
                cell.border = border

    # Ajustar largura das colunas
    for ws_sheet in [ws, ws_resumo]:
        for col in ws_sheet.columns:
            max_len = 0
            try:
                col_letter = col[0].column_letter
            except AttributeError:
                from openpyxl.utils import get_column_letter
                col_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    if cell.value:
                        max_len = max(max_len, len(str(cell.value)))
                except Exception:
                    pass
            ws_sheet.column_dimensions[col_letter].width = min(max_len + 4, 60)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def gerar_relatorio_csv(resultados):
    """Gera CSV simples dos resultados."""
    df = pd.DataFrame(resultados)
    if df.empty:
        return None
    colunas = ["item", "dominio", "preco", "url", "data_coleta", "titulo"]
    colunas_existentes = [c for c in colunas if c in df.columns]
    df = df[colunas_existentes]
    df.columns = ["Item", "Fornecedor", "Preço (R$)", "Link", "Data Coleta", "Título"][:len(colunas_existentes)]
    output = BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig", sep=";")
    output.seek(0)
    return output


# ===================== SIDEBAR =====================

# Carregar imagem do acanto para a sidebar
_acanto_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões", "acanto.png")
if os.path.exists(_acanto_path):
    with open(_acanto_path, "rb") as _f:
        _acanto_b64 = base64.b64encode(_f.read()).decode()
else:
    _acanto_b64 = None

with st.sidebar:
    if _acanto_b64:
        st.markdown(f'<div style="text-align:center;padding:1rem 0 0.5rem 0;"><img src="data:image/png;base64,{_acanto_b64}" style="max-width:70%;height:auto;"></div>', unsafe_allow_html=True)
    st.markdown("## MENU")
    st.markdown("---")
    st.page_link("streamlit_app.py", label="Cotação", icon="⚓")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.markdown("---")
    st.markdown("## LINKS ÚTEIS")
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <a href="https://freitasnascimentomarinha-debug.github.io/ShootMail/" target="_blank" style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
            📧 Disparador de Emails
        </a>
    </div>
    <div style="margin-bottom: 1rem;">
        <a href="https://detetive-obtencao.vercel.app/" target="_blank" style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
            🚨 Detetive Obtenção
        </a>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)


# ===================== HEADER =====================

st.markdown("""
    <div class="header-container">
        <div class="logo-text">MARINHA DO BRASIL</div>
        <div class="sistema-nome">ATACOTADA</div>
        <div class="subtitulo">🕷️ Web Scraping — Pesquisa de Preços Automatizada</div>
    </div>
""", unsafe_allow_html=True)


# ===================== INTERFACE PRINCIPAL =====================

st.markdown("""
<div class="info-card">
    <div class="info-title">⚙️ Como Funciona o Web Scraping</div>
    <div style="margin-bottom: 0.8rem;">Este módulo automatiza a pesquisa de preços na internet para fins de <b>cotação e estimativa de preços</b>,
    em conformidade com a IN 65/2021. O sistema busca preços diretamente em sites de fornecedores
    (ignorando marketplaces como Mercado Livre, Amazon, Shopee etc.) para obter valores mais próximos
    da realidade praticada no comércio direto.</div>

    <div style="font-weight:bold; color:#d4af37; margin-bottom: 0.5rem;">🔄 Fluxo de Execução:</div>
    <div style="margin-left: 1rem; margin-bottom: 1rem;">
        <div style="margin-bottom:0.3rem;">1. Você informa os itens que deseja pesquisar (um por linha)</div>
        <div style="margin-bottom:0.3rem;">2. O sistema gera variações de busca para cada item (ex: "caneta preço", "comprar caneta online")</div>
        <div style="margin-bottom:0.3rem;">3. Para cada variação, busca URLs relevantes usando até <b>5 mecanismos</b> em cascata:
            <br><b>DDGS API → DuckDuckGo → Google → Bing</b>
            <br>Se nenhum scraping encontrar preço, aciona o <b>Google Shopping (SearchAPI)</b> como último recurso,
            que retorna preços diretamente de lojas cadastradas no Google.</div>
        <div style="margin-bottom:0.3rem;">4. Acessa cada site encontrado e extrai preços em Reais (R$) do HTML</div>
        <div style="margin-bottom:0.3rem;">5. Salva automaticamente uma evidência (snapshot) de cada página onde encontrou preço</div>
        <div style="margin-bottom:0.3rem;">6. Gera relatório exportável em Excel, CSV ou JSON</div>
    </div>

    <div style="font-weight:bold; color:#d4af37; margin-bottom: 0.5rem;">⚙️ Configurações Disponíveis:</div>
    <div style="margin-left: 1rem; margin-bottom: 1rem;">
        <div style="margin-bottom:0.4rem;">• <b>Navegador Automatizado (Playwright):</b> Quando ativado, usa um navegador real (Chromium)
            para acessar sites que carregam preços via JavaScript. É mais lento, mas captura preços
            de sites dinâmicos que o modo padrão não consegue ler. <span style="font-style:italic;">Recomendação: deixe desativado
            na maioria dos casos; ative apenas se estiver recebendo poucos resultados.</span></div>
        <div style="margin-bottom:0.4rem;">• <b>Máx. fontes por item:</b> Quantidade máxima de orçamentos diferentes que o sistema
            buscará para cada material. <span style="font-style:italic;">Recomendação: <b>3</b> fontes é o ideal — já atende
            à IN 65/2021 e mantém a pesquisa rápida.</span></div>
        <div style="margin-bottom:0.4rem;">• <b>Delay mínimo / máximo (seg):</b> Intervalo de espera entre cada requisição,
            simulando comportamento humano. Evita bloqueios dos sites.
            <span style="font-style:italic;">Recomendação: mínimo <b>2s</b> e máximo <b>6s</b> (padrão) —
            aumente para 4s/10s se pesquisar muitos itens de uma vez.</span></div>
    </div>

    <div style="font-weight:bold; color:#d4af37; margin-bottom: 0.5rem;">✅ Configuração Ideal para a Maioria dos Casos:</div>
    <div style="margin-left: 1rem;">
        <div style="margin-bottom:0.3rem;">• Navegador automatizado: <b>Desativado</b></div>
        <div style="margin-bottom:0.3rem;">• Máx. fontes por item: <b>3</b></div>
        <div style="margin-bottom:0.3rem;">• Delay mínimo: <b>2.0s</b> &nbsp;|&nbsp; Delay máximo: <b>6.0s</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Formulário de entrada
st.markdown("### 📝 Itens para Pesquisa")

col1, col2 = st.columns([3, 1])

with col1:
    itens_input = st.text_area(
        "Informe os itens (um por linha):",
        height=150,
        placeholder="Exemplo:\nArruela de pressão 1/4\nParafuso sextavado M10\nFita isolante 20m",
        help="Digite os nomes dos materiais que deseja pesquisar, um por linha.",
    )

with col2:
    st.markdown("#### ⚙️ Configurações")
    usar_playwright = st.checkbox(
        "Usar navegador automatizado",
        value=False,
        help="Ativa o Playwright para sites com carregamento dinâmico. Mais lento, porém mais preciso.",
    )
    max_fontes = st.number_input(
        "Máx. fontes por item",
        min_value=1,
        max_value=5,
        value=3,
        help="Número máximo de orçamentos por item.",
    )
    delay_min = st.number_input("Delay mín. (seg)", min_value=1.0, max_value=15.0, value=2.0, step=0.5)
    delay_max = st.number_input("Delay máx. (seg)", min_value=2.0, max_value=30.0, value=6.0, step=0.5)

# Validação
if delay_min >= delay_max:
    st.warning("O delay mínimo deve ser menor que o máximo.")

# Botão de execução
st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

with col_btn2:
    iniciar = st.button("🚀 Iniciar Scraping", type="primary", use_container_width=True)

if iniciar:
    itens = [i.strip() for i in itens_input.strip().split("\n") if i.strip()]

    if not itens:
        st.error("⚠️ Informe pelo menos um item para pesquisa.")
    else:
        # Atualizar constante global com a config do usuário
        MAX_FONTES_POR_ITEM_LOCAL = max_fontes

        st.markdown("### 📊 Execução do Scraping")

        # Área de logs
        st.markdown("#### 📜 Log de Execução")
        log_container = st.empty()

        # Barra de progresso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Executar scraping
        resultados = executar_scraping(
            itens=itens,
            usar_playwright=usar_playwright,
            progress_bar=progress_bar,
            log_container=log_container,
            status_text=status_text,
        )

        # Armazenar resultados no session_state
        st.session_state["scraping_resultados"] = resultados
        st.session_state["scraping_itens"] = itens

# ===================== EXIBIÇÃO DE RESULTADOS =====================

if "scraping_resultados" in st.session_state and st.session_state["scraping_resultados"]:
    resultados = st.session_state["scraping_resultados"]

    st.markdown("---")
    st.markdown("### 📋 Resultados")

    tab_tabela, tab_resumo, tab_evidencias, tab_export = st.tabs(
        ["📊 Tabela Completa", "📈 Resumo", "📸 Evidências", "📥 Exportar"]
    )

    with tab_tabela:
        df = pd.DataFrame(resultados)
        df_display = df[["item", "dominio", "preco", "url", "data_coleta", "titulo"]].copy()
        df_display.columns = ["Item", "Fornecedor", "Preço (R$)", "Link", "Data Coleta", "Título"]
        df_display["Preço (R$)"] = df_display["Preço (R$)"].apply(formatar_moeda_br)

        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Link": st.column_config.LinkColumn("Link", display_text="Acessar"),
            },
        )

    with tab_resumo:
        df = pd.DataFrame(resultados)

        if not df.empty:
            # Métricas gerais
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Total de Orçamentos", len(resultados))
            with col_m2:
                st.metric("Itens Pesquisados", len(st.session_state.get("scraping_itens", [])))
            with col_m3:
                st.metric("Fontes Distintas", df["dominio"].nunique())
            with col_m4:
                st.metric("Menor Preço", formatar_moeda_br(df["preco"].min()))

            st.markdown("#### Resumo por Item")
            resumo = df.groupby("item")["preco"].agg(["count", "min", "max", "mean"]).reset_index()
            resumo.columns = ["Item", "Qtd. Orçamentos", "Menor Preço", "Maior Preço", "Preço Médio"]
            resumo["Menor Preço"] = resumo["Menor Preço"].apply(formatar_moeda_br)
            resumo["Maior Preço"] = resumo["Maior Preço"].apply(formatar_moeda_br)
            resumo["Preço Médio"] = resumo["Preço Médio"].apply(formatar_moeda_br)

            st.dataframe(resumo, use_container_width=True, hide_index=True)

    with tab_evidencias:
        screenshots = [r for r in resultados if r.get("screenshot") and os.path.exists(r.get("screenshot", ""))]

        if screenshots:
            st.markdown(f"**{len(screenshots)} evidências visuais capturadas**")
            for r in screenshots:
                with st.expander(f"📸 {r['item']} — {r['dominio']} — {formatar_moeda_br(r['preco'])}"):
                    sc_path = r["screenshot"]
                    if sc_path.endswith(".html"):
                        # Renderizar snapshot HTML como evidência
                        try:
                            with open(sc_path, "r", encoding="utf-8") as f:
                                html_content = f.read()
                            import streamlit.components.v1 as components
                            components.html(html_content, height=500, scrolling=True)
                        except Exception:
                            st.markdown(f"📄 Evidência salva em: `{sc_path}`")
                    else:
                        st.image(sc_path, caption=f"{r['dominio']} - {r['data_coleta']}")
                    st.markdown(f"**Link:** [{r['url']}]({r['url']})")
        else:
            st.info(
                "Nenhuma evidência visual capturada nesta execução."
            )

    with tab_export:
        st.markdown("#### 📥 Exportar Relatório")

        col_exp1, col_exp2, col_exp3 = st.columns(3)

        with col_exp1:
            excel_data = gerar_relatorio_excel(resultados)
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_data,
                file_name=f"relatorio_scraping_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True,
            )

        with col_exp2:
            csv_data = gerar_relatorio_csv(resultados)
            if csv_data:
                st.download_button(
                    label="📄 Baixar CSV",
                    data=csv_data,
                    file_name=f"relatorio_scraping_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        with col_exp3:
            json_data = json.dumps(resultados, ensure_ascii=False, indent=2, default=str)
            st.download_button(
                label="🔗 Baixar JSON",
                data=json_data,
                file_name=f"relatorio_scraping_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
            )

elif "scraping_resultados" in st.session_state and not st.session_state["scraping_resultados"]:
    st.warning("⚠️ O scraping foi executado mas nenhum orçamento foi encontrado. Tente com outros termos.")
