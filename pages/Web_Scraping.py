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
]

MAX_FONTES_POR_ITEM = 3
MAX_RETRIES = 2
SCREENSHOT_DIR = "/tmp/scraping_screenshots"


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

def buscar_duckduckgo(session, query, headers, num_results=8):
    """Busca no DuckDuckGo HTML usando requests e retorna lista de URLs."""
    from bs4 import BeautifulSoup

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []

        # DuckDuckGo HTML: resultados ficam em <a class="result__a">
        for a_tag in soup.select("a.result__a"):
            href = a_tag.get("href", "")
            if href.startswith("//duckduckgo.com/l/?uddg="):
                # Extrair URL real do redirect
                from urllib.parse import unquote
                real_url = unquote(href.split("uddg=")[1].split("&")[0])
            elif href.startswith("http"):
                real_url = href
            else:
                continue

            if real_url.startswith("http") and dominio_valido(real_url):
                urls.append(real_url)

        # Remover duplicatas mantendo ordem e diversidade de domínios
        seen = set()
        unique = []
        for u in urls:
            dom = extrair_dominio(u)
            if dom not in seen:
                seen.add(dom)
                unique.append(u)

        return unique[:num_results]

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

        # Método 1: links /url?q=
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.startswith("/url?q="):
                real_url = unquote(href.split("/url?q=")[1].split("&")[0])
                if real_url.startswith("http") and dominio_valido(real_url):
                    urls.append(real_url)

        # Método 2: links diretos dentro de divs de resultado
        if not urls:
            for a_tag in soup.select("a[href^='http']"):
                href = a_tag.get("href", "")
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        seen = set()
        unique = []
        for u in urls:
            dom = extrair_dominio(u)
            if dom not in seen:
                seen.add(dom)
                unique.append(u)

        return unique[:num_results]

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

        # Resultados orgânicos do Bing ficam em <li class="b_algo"> > <h2> > <a>
        for li in soup.select("li.b_algo"):
            a_tag = li.select_one("h2 a")
            if a_tag:
                href = a_tag.get("href", "")
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        # Fallback: qualquer link principal nos resultados
        if not urls:
            for a_tag in soup.select("#b_results a[href^='http']"):
                href = a_tag.get("href", "")
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        seen = set()
        unique = []
        for u in urls:
            dom = extrair_dominio(u)
            if dom not in seen:
                seen.add(dom)
                unique.append(u)

        return unique[:num_results]

    except Exception:
        return []


def buscar_urls(session, query, headers, num_results=8):
    """Busca combinada: DuckDuckGo primeiro, Google, depois Bing como fallback."""
    urls = buscar_duckduckgo(session, query, headers, num_results)
    if not urls:
        urls = buscar_google_requests(session, query, headers, num_results)
    if not urls:
        urls = buscar_bing_requests(session, query, headers, num_results)
    return urls


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

        return {
            "titulo": titulo,
            "preco": preco_medio,
            "url": url,
            "dominio": extrair_dominio(url),
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

            # Buscar URLs (DuckDuckGo + fallback Google)
            urls = buscar_urls(session, query, headers)

            if not urls:
                log_msg(log_container, logs, f"⚠ Nenhum resultado encontrado para \"{query}\"", "warn")
                continue

            log_msg(log_container, logs, f"📋 {len(urls)} resultados encontrados", "info")

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
            col_letter = col[0].column_letter
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

with st.sidebar:
    st.markdown("## MENU")
    st.markdown("---")
    st.page_link("streamlit_app.py", label="⚓ Cotação", icon="📊")
    st.page_link("pages/Adesões.py", label="🤝 Adesões", icon="📋")
    st.page_link("pages/Notas_Fiscais.py", label="📄 Notas Fiscais", icon="🧾")
    st.page_link("pages/Banco_de_Fornecedores.py", label="🏢 Fornecedores", icon="🔍")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="🕷️ Web Scraping", icon="🌐")
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
    <div class="info-title">ℹ️ Como funciona</div>
    <p>Este módulo realiza pesquisa de preços automatizada na web, coletando orçamentos de diferentes
    fornecedores para os materiais informados. O sistema opera de forma controlada e discreta,
    simulando comportamento humano para garantir estabilidade.</p>
    <ul>
        <li>Busca inteligente no Google com variações naturais</li>
        <li>Máximo de 3 fontes distintas por item</li>
        <li>Delays aleatórios entre requisições</li>
        <li>Captura de evidências visuais (screenshots)</li>
        <li>Relatório exportável em Excel e CSV</li>
    </ul>
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
                    st.image(r["screenshot"], caption=f"{r['dominio']} - {r['data_coleta']}")
                    st.markdown(f"**Link:** [{r['url']}]({r['url']})")
        else:
            st.info(
                "Nenhuma evidência visual capturada. "
                "Para capturar screenshots, ative o 'Navegador automatizado' nas configurações."
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
