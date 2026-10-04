import streamlit as st
import pandas as pd
import time
import random
import re
import os
import base64
import json
import html as html_lib
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse, quote_plus
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # módulos da raiz do projeto
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('cotacao_rapida', 'relatorio_cotacao_rapida', 'relatorio_nf_lote', 'web_precos', 'relatorio_web', 'memoria_lojas', 'captura_pagina')
import web_precos  # noqa: E402  (escolha do preço da página)
import relatorio_web  # noqa: E402  (relatório padrão da Cotação Rápida)
import memoria_lojas  # noqa: E402  (lojas aprendidas com o uso)
import captura_pagina  # noqa: E402  (print real das páginas dos preços)

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
            border-radius: 8px !important;
            margin: 0.2rem 0 !important;
            padding: 0.45rem 0.7rem !important;
            font-weight: 600 !important;
            font-size: 12.5px !important;
            line-height: 1.2 !important;
            min-height: 0 !important;
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
        .log-orcamento { color: #1a1a1a; background: #87CEEB; font-weight: bold; padding: 2px 6px; border-radius: 4px; display: inline-block; margin: 1px 0; }

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

# Frases de compra com o material no começo e sem "brasil" (a região Brasil já é pedida ao buscador; a palavra puxava páginas sobre o país).
# São usadas em ordem: as que mais trazem lojas com preço primeiro.
VARIANTES_BUSCA = [
    "{item} comprar",
    "{item} preço",
    "venda de {item}",
    "{item} valor",
    "{item} atacado",
]
# Reserva: as frases antigas, usadas só se as novas não bastarem para juntar as fontes pedidas.
VARIANTES_RESERVA = [
    "{item} preço brasil",
    "{item} comprar brasil",
    "comprar {item} online brasil",
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
    # Streamlit / app próprio
    "streamlit.app", "streamlit.io", "share.streamlit.io",
    # Blogs, notícias, comparadores, fóruns
    "blog.", "medium.com", "blogspot.com", "wordpress.com",
    "noticias.", "uol.com.br", "globo.com", "g1.globo.com",
    "folha.uol.com.br", "terra.com.br", "ig.com.br",
    "reclameaqui.com.br", "jusbrasil.com.br",
    "slideshare.net", "scribd.com", "pinterest.com",
    "quora.com", "stackoverflow.com", "github.com",
    "comparador.", "versus.com", "techtudo.com.br",
    "tudocelular.com", "canaltech.com.br", "tecmundo.com.br",
    "olx.com.br", "enjoei.com.br",
    # Específicos
    "forneceb2b.com", "forneceb2b.com.br",
    # Domínios de Portugal e Europa
    ".pt", ".es", ".fr", ".de", ".it", ".uk", ".eu",
]

MAX_FONTES_POR_ITEM = 3
MAX_RETRIES = 2
SCREENSHOT_DIR = "/tmp/scraping_screenshots"
OUTLIER_MULTIPLIER = 1.6
MIN_ORCAMENTOS_PARA_ANALISE_OUTLIER = 3



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
    """Verifica se o domínio não está na lista de ignorados e é brasileiro."""
    try:
        dominio = urlparse(url).netloc.lower()
        # Rejeitar domínios na lista de ignorados
        if any(d in dominio for d in DOMINIOS_IGNORADOS):
            return False
        # Aceitar apenas domínios brasileiros (.com.br, .br) ou .com genéricos
        if dominio.endswith('.br') or dominio.endswith('.com') or dominio.endswith('.net') or dominio.endswith('.org'):
            return True
        return False
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


def normalizar_texto_contexto(texto):
    """Limpa e formata o texto extraído para evidências."""
    if not texto:
        return ""

    texto = html_lib.unescape(str(texto)).replace("\xa0", " ")
    linhas = []
    for linha in texto.splitlines():
        linha_limpa = re.sub(r"\s+", " ", linha).strip()
        if linha_limpa:
            linhas.append(linha_limpa)

    if not linhas:
        return ""

    texto_limpo = "\n".join(linhas)
    texto_limpo = re.sub(r"\n{3,}", "\n\n", texto_limpo)
    return texto_limpo.strip()


def extrair_contexto_preco(texto_base, preco_referencia, janela=260):
    """Extrai um trecho legível ao redor do preço encontrado."""
    texto_base = normalizar_texto_contexto(texto_base)
    if not texto_base:
        return ""

    formatos_preco = [
        f"{preco_referencia:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        f"{preco_referencia:.2f}".replace(".", ","),
        f"R$ {preco_referencia:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
    ]

    idx_preco = -1
    preco_encontrado = ""
    for formato in formatos_preco:
        idx_preco = texto_base.find(formato)
        if idx_preco >= 0:
            preco_encontrado = formato
            break

    if idx_preco < 0:
        return texto_base[:600]

    inicio = max(0, idx_preco - janela)
    fim = min(len(texto_base), idx_preco + len(preco_encontrado) + janela)

    while inicio > 0 and texto_base[inicio] not in ".!?\n":
        inicio -= 1
    while fim < len(texto_base) and texto_base[fim - 1] not in ".!?\n":
        fim += 1

    return texto_base[inicio:fim].strip(" \n-:")


def classificar_orcamentos_item(orcamentos, max_fontes):
    """Descarta outliers altos com base na média e mantém a quantidade necessária."""
    if not orcamentos:
        return [], [], []

    selecionados = sorted(orcamentos, key=lambda registro: registro["preco"])
    descartados = []

    while len(selecionados) >= MIN_ORCAMENTOS_PARA_ANALISE_OUTLIER:
        media_atual = sum(registro["preco"] for registro in selecionados) / len(selecionados)
        limite_superior = media_atual * OUTLIER_MULTIPLIER
        candidatos_outlier = [
            registro for registro in selecionados
            if registro["preco"] > limite_superior
        ]

        if not candidatos_outlier:
            break

        maior_preco = max(candidatos_outlier, key=lambda registro: registro["preco"])
        selecionados = [
            registro for registro in selecionados
            if registro["resultado_id"] != maior_preco["resultado_id"]
        ]

        outlier_info = dict(maior_preco)
        outlier_info["media_referencia"] = media_atual
        outlier_info["limite_superior"] = limite_superior
        descartados.append(outlier_info)

    reservas = []
    if len(selecionados) > max_fontes:
        reservas = selecionados[max_fontes:]
        selecionados = selecionados[:max_fontes]

    return selecionados, descartados, reservas


def atualizar_estado_orcamentos(candidatos_item, max_fontes):
    """Recalcula o conjunto válido do item após cada nova cotação."""
    validos, descartados, reservas = classificar_orcamentos_item(candidatos_item, max_fontes)
    return {
        "validos": validos,
        "ids_validos": {registro["resultado_id"] for registro in validos},
        "descartados": descartados,
        "ids_descartados": {registro["resultado_id"] for registro in descartados},
        "reservas": reservas,
    }


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


INTERVALO_MIN_BUSCA_S = 2.0  # pausa mínima entre duas requisições a buscadores (DuckDuckGo, Google, Bing), de qualquer tipo
ULTIMA_REQUISICAO_BUSCA = {"t": 0.0}


def intervalo_entre_buscas():
    """Espera o que faltar para completar INTERVALO_MIN_BUSCA_S (mais um pouco aleatório) desde a última requisição a um buscador.
    Vale entre buscas de frases diferentes e também entre os buscadores da cascata (ex.: ddgs e logo depois o DuckDuckGo HTML)."""
    falta = ULTIMA_REQUISICAO_BUSCA["t"] + INTERVALO_MIN_BUSCA_S + random.uniform(0.0, 0.5) - time.time()
    if falta > 0:
        time.sleep(falta)
    ULTIMA_REQUISICAO_BUSCA["t"] = time.time()


DIAG_BUSCA = {}  # o que cada buscador respondeu na última busca (erro, HTTP ou nº de sites): aparece no log quando o DuckDuckGo falha
DDG_PROXIMA_TENTATIVA = {"ate": 0.0}  # depois de um bloqueio suspeito, o DuckDuckGo descansa um pouco antes de ser consultado de novo
PAUSA_APOS_BLOQUEIO_DDG = 60  # segundos (o descanso dobra a cada bloqueio seguido, até PAUSA_MAXIMA_DDG)
PAUSA_MAXIMA_DDG = 600
DDG_BLOQUEIOS_SEGUIDOS = {"n": 0}


def descansar_ddg():
    """Marca o descanso do DuckDuckGo: 60 s no 1º bloqueio, depois 120, 240... (insistir cedo demais renova o bloqueio). Devolve os segundos."""
    pausa = min(PAUSA_APOS_BLOQUEIO_DDG * (2 ** DDG_BLOQUEIOS_SEGUIDOS["n"]), PAUSA_MAXIMA_DDG)
    DDG_BLOQUEIOS_SEGUIDOS["n"] += 1
    DDG_PROXIMA_TENTATIVA["ate"] = time.time() + pausa
    return pausa


def ddg_voltou():
    DDG_PROXIMA_TENTATIVA["ate"] = 0.0
    DDG_BLOQUEIOS_SEGUIDOS["n"] = 0


def buscar_ddgs_api(query, num_results=8):
    """Busca usando o pacote ddgs (DuckDuckGo Search) — mais confiável em servidores."""
    intervalo_entre_buscas()
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, region="br-pt", max_results=num_results))
        urls = [r["href"] for r in results if r.get("href") and dominio_valido(r["href"])]
        DIAG_BUSCA["DDGS"] = f"{len(urls)} sites"
        return _dedup_urls(urls, num_results)
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="br-pt", max_results=num_results))
            urls = [r["href"] for r in results if r.get("href") and dominio_valido(r["href"])]
            DIAG_BUSCA["DDGS"] = f"{len(urls)} sites"
            return _dedup_urls(urls, num_results)
        except Exception as erro:
            DIAG_BUSCA["DDGS"] = "0 sites" if "No results" in str(erro) else f"erro {type(erro).__name__}"
            return []
    except Exception as erro:
        # o pacote levanta "No results found" quando a frase não tem resultado: não é bloqueio
        DIAG_BUSCA["DDGS"] = "0 sites" if "No results" in str(erro) else f"erro {type(erro).__name__}"
        return []


def buscar_duckduckgo(session, query, headers, num_results=8):
    """Busca no DuckDuckGo HTML usando requests e retorna lista de URLs."""
    intervalo_entre_buscas()
    from bs4 import BeautifulSoup
    from urllib.parse import unquote

    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    try:
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            DIAG_BUSCA["DuckDuckGo HTML"] = f"HTTP {resp.status_code}"
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

        DIAG_BUSCA["DuckDuckGo HTML"] = f"{len(urls)} sites"
        return _dedup_urls(urls, num_results)

    except Exception as erro:
        DIAG_BUSCA["DuckDuckGo HTML"] = f"erro {type(erro).__name__}"
        return []


def buscar_google_requests(session, query, headers, num_results=8):
    """Busca no Google usando requests (fallback)."""
    intervalo_entre_buscas()
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


def desembrulhar_link_bing(href):
    """Os resultados do Bing costumam vir como https://www.bing.com/ck/a?...&u=a1<base64 do endereço real>: devolve o endereço real
    (sem isso todos os resultados parecem do domínio bing.com e a deduplicação por domínio deixa só um)."""
    import base64
    from urllib.parse import parse_qs, urlparse

    try:
        partes = urlparse(href)
        if not partes.netloc.endswith("bing.com"):
            return href
        valor = (parse_qs(partes.query).get("u") or [""])[0]
        if valor.startswith("a1"):
            bruto = valor[2:]
            real = base64.urlsafe_b64decode(bruto + "=" * (-len(bruto) % 4)).decode("utf-8", "ignore")
            if real.startswith("http"):
                return real
    except Exception:
        pass
    return href


def buscar_bing_requests(session, query, headers, num_results=8):
    """Busca no Bing como fallback adicional."""
    intervalo_entre_buscas()
    from bs4 import BeautifulSoup

    url = f"https://www.bing.com/search?q={quote_plus(query)}&setlang=pt-BR&count={num_results}"
    bing_headers = dict(headers)
    bing_headers["Referer"] = "https://www.bing.com/"
    try:
        resp = session.get(url, headers=bing_headers, timeout=15)
        if resp.status_code != 200:
            DIAG_BUSCA["Bing"] = f"HTTP {resp.status_code}"
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        urls = []

        for li in soup.select("li.b_algo"):
            a_tag = li.select_one("h2 a")
            if a_tag:
                href = desembrulhar_link_bing(a_tag.get("href", ""))
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        if not urls:
            for a_tag in soup.select("#b_results a[href^='http']"):
                href = desembrulhar_link_bing(a_tag.get("href", ""))
                if href.startswith("http") and dominio_valido(href):
                    urls.append(href)

        DIAG_BUSCA["Bing"] = f"{len(urls)} sites"
        return _dedup_urls(urls, num_results)

    except Exception as erro:
        DIAG_BUSCA["Bing"] = f"erro {type(erro).__name__}"
        return []


def buscar_na_loja(session, item, site, headers, num_results=8):
    """Procura o item dentro de uma loja da memória ("item site:loja"), com a mesma busca da página (ddgs > DuckDuckGo HTML).
    Devolve só páginas da própria loja (até 3)."""
    from bs4 import BeautifulSoup
    from urllib.parse import unquote

    def da_loja(url):
        return memoria_lojas.dominio(url) == site or memoria_lojas.dominio(url).endswith("." + site)

    query = f"{item} site:{site}"
    urls = []
    if time.time() >= DDG_PROXIMA_TENTATIVA["ate"]:
        DIAG_BUSCA.clear()
        urls = [u for u in buscar_ddgs_api(query, num_results) if da_loja(u)]
        if not urls:
            urls = [u for u in buscar_duckduckgo(session, query, headers, num_results) if da_loja(u)]
        sinais = [v for k, v in DIAG_BUSCA.items() if k in ("DDGS", "DuckDuckGo HTML")]
        if not urls and any(str(v).startswith(("erro", "HTTP 202", "HTTP 403", "HTTP 429", "HTTP 5")) for v in sinais):
            descansar_ddg()
    if not urls:  # DuckDuckGo descansando ou sem resposta: o Bing também aceita "site:"
        urls = [u for u in buscar_bing_requests(session, query, headers, num_results) if da_loja(u)]
    return list(dict.fromkeys(urls))[:3]


def buscar_urls(session, query, headers, num_results=8):
    """Busca combinada: DDGS API > DuckDuckGo HTML > Google > Bing. Se o DuckDuckGo falhar com sinal de bloqueio (erro, HTTP 202/403/429),
    ele descansa PAUSA_APOS_BLOQUEIO_DDG segundos antes de ser consultado de novo (insistir só prolonga o bloqueio); nesse intervalo a busca
    segue pelos outros. O motivo vai junto com o nome do buscador, para aparecer no log."""
    DIAG_BUSCA.clear()
    nota = ""
    if time.time() < DDG_PROXIMA_TENTATIVA["ate"]:
        nota = f"DuckDuckGo descansando por mais {DDG_PROXIMA_TENTATIVA['ate'] - time.time():.0f} s após bloqueio"
    else:
        # 1. Tentar DDGS API (mais confiável em ambientes de servidor)
        urls = buscar_ddgs_api(query, num_results)
        if urls:
            ddg_voltou()
            return urls, "DDGS API"
        # 2. DuckDuckGo HTML scraping
        urls = buscar_duckduckgo(session, query, headers, num_results)
        if urls:
            ddg_voltou()
            return urls, "DuckDuckGo HTML"
        sinais = [v for k, v in DIAG_BUSCA.items() if k in ("DDGS", "DuckDuckGo HTML")]
        if any(str(v).startswith(("erro", "HTTP 202", "HTTP 403", "HTTP 429", "HTTP 5")) for v in sinais):
            pausa = descansar_ddg()
            nota = "DuckDuckGo sem resposta (" + "; ".join(f"{k}: {v}" for k, v in DIAG_BUSCA.items() if k in ("DDGS", "DuckDuckGo HTML")) + f"); descansa {pausa} s"
        else:
            nota = "DuckDuckGo sem resultados para esta frase"
    # 3. Google
    urls = buscar_google_requests(session, query, headers, num_results)
    if urls:
        return urls, f"Google — {nota}" if nota else "Google"
    # 4. Bing
    urls = buscar_bing_requests(session, query, headers, num_results)
    if urls:
        return urls, f"Bing — {nota}" if nota else "Bing"
    outros = "; ".join(f"{k}: {v}" for k, v in DIAG_BUSCA.items() if k in ("Google", "Bing"))
    nota = "; ".join(x for x in (nota, outros) if x)
    return [], f"nenhum ({nota})" if nota else "nenhum"


def extrair_precos_pagina(html_content):
    """Extrai possíveis preços de uma página HTML usando múltiplas estratégias."""
    from bs4 import BeautifulSoup

    precos_estruturados = []  # Alta confiança (JSON-LD, meta, classes de preço)
    precos_regex = []         # Baixa confiança (regex genérico)

    soup = BeautifulSoup(html_content, "html.parser")

    # --- Estratégia 1: JSON-LD (schema.org) — máxima confiança ---
    for script_tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script_tag.string or "")
            _extrair_preco_jsonld(data, precos_estruturados)
        except (json.JSONDecodeError, TypeError):
            continue

    # --- Estratégia 2: Meta tags (og:price, product:price) ---
    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or meta.get("name") or "").lower()
        if any(k in prop for k in ("price", "amount", "preco")):
            content = meta.get("content", "")
            val = _parse_valor_br(content)
            if val:
                precos_estruturados.append(val)

    # --- Estratégia 3: Elementos com classes/atributos de preço ---
    seletores_preco = [
        "[class*='price']", "[class*='preco']", "[class*='Price']",
        "[class*='valor']", "[class*='Valor']",
        "[itemprop='price']", "[data-price]",
        "[class*='sale']", "[class*='offer']",
        "[class*='product-price']", "[class*='finalPrice']",
        "[class*='priceBox']", "[class*='price-box']",
        "[class*='current-price']", "[class*='selling-price']",
        "[class*='special-price']", "[class*='best-price']",
        "[class*='productPrice']", "[class*='item-price']",
        "[class*='amount']", "[class*='cost']",
        "[data-product-price]", "[data-amount]",
        "[data-value]", "[data-sale-price]",
    ]
    for sel in seletores_preco:
        for elem in soup.select(sel):
            # Priorizar atributo content/data-price sobre texto
            for attr in ("content", "data-price", "data-value", "data-product-price",
                         "data-amount", "data-sale-price", "data-original-price", "value"):
                attr_val = elem.get(attr)
                if attr_val:
                    val = _parse_valor_br(attr_val)
                    if val:
                        precos_estruturados.append(val)
            # Texto do elemento
            texto = elem.get_text(strip=True)
            val = _extrair_valor_texto(texto)
            if val:
                precos_estruturados.append(val)

    # --- Estratégia 4: Regex no HTML bruto (fallback) ---
    padroes = [
        r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
        r"R\$\s*(\d+,\d{2})",
        r"BRL\s*(\d{1,3}(?:\.\d{3})*,\d{2})",
    ]
    for padrao in padroes:
        matches = re.findall(padrao, html_content, re.IGNORECASE)
        for match in matches:
            val = _parse_valor_br(match)
            if val:
                precos_regex.append(val)

    # --- Estratégia 5: Preços em JavaScript inline ---
    # Muitos e-commerce colocam preço em variáveis JS
    padroes_js = [
        r'["\']price["\']\s*:\s*["\']?(\d+[.,]\d{2})["\']?',
        r'["\']amount["\']\s*:\s*["\']?(\d+[.,]\d{2})["\']?',
        r'["\']value["\']\s*:\s*["\']?(\d+[.,]\d{2})["\']?',
        r'["\']preco["\']\s*:\s*["\']?(\d+[.,]\d{2})["\']?',
        r'["\']salePrice["\']\s*:\s*["\']?(\d+[.,]\d{2})["\']?',
        r'["\']sellingPrice["\']\s*:\s*["\']?(\d+[.,]\d{2})["\']?',
    ]
    for script_tag in soup.find_all("script"):
        script_text = script_tag.string or ""
        if not script_text:
            continue
        for padrao in padroes_js:
            matches = re.findall(padrao, script_text, re.IGNORECASE)
            for match in matches:
                val = _parse_valor_br(match)
                if val:
                    precos_regex.append(val)

    # Se temos preços estruturados, preferir eles; senão usar regex
    if precos_estruturados:
        return sorted(set(precos_estruturados))
    return sorted(set(precos_regex))


def _extrair_preco_jsonld(data, out):
    """Extrai preços de dados JSON-LD recursivamente."""
    if isinstance(data, list):
        for item in data:
            _extrair_preco_jsonld(item, out)
        return
    if not isinstance(data, dict):
        return
    # offers.price / offers.lowPrice
    for key in ("price", "lowPrice", "highPrice"):
        if key in data:
            val = _parse_valor_br(str(data[key]))
            if val:
                out.append(val)
    # Recursão em sub-objetos relevantes
    for key in ("offers", "priceSpecification", "mainEntity"):
        if key in data:
            _extrair_preco_jsonld(data[key], out)


def _parse_valor_br(texto):
    """Converte texto de preço BR ou internacional para float. Retorna None se inválido."""
    if not texto:
        return None
    texto = texto.strip().replace("R$", "").replace("\xa0", "").replace("\u00a0", "").strip()
    # Remover espaços internos
    texto = texto.replace(" ", "")
    # Formato BR: 1.234,56
    m = re.match(r"^(\d{1,3}(?:\.\d{3})*),(\d{2})$", texto)
    if m:
        val = float(texto.replace(".", "").replace(",", "."))
        return val if 0.50 < val < 500_000 else None
    # Formato BR simples: 123,45 ou 1,50
    m = re.match(r"^(\d+),(\d{2})$", texto)
    if m:
        val = float(texto.replace(",", "."))
        return val if 0.50 < val < 500_000 else None
    # Formato internacional com ponto: 1234.56
    m = re.match(r"^(\d+)\.(\d{2})$", texto)
    if m:
        val = float(texto)
        return val if 0.50 < val < 500_000 else None
    # Formato inteiro (sem centavos): 1234 ou 12
    m = re.match(r"^(\d+)$", texto)
    if m:
        val = float(texto)
        return val if 0.50 < val < 500_000 else None
    return None


def _extrair_valor_texto(texto):
    """Extrai primeiro valor monetário de um texto curto."""
    if not texto:
        return None
    # R$ 1.234,56 ou R$ 123,45 ou R$ 6,44
    m = re.search(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})", texto)
    if m:
        return _parse_valor_br(m.group(1))
    # Sem R$ mas com formato BR: 1.234,56 ou 123,45
    m = re.search(r"(\d{1,3}(?:\.\d{3})*,\d{2})", texto)
    if m:
        return _parse_valor_br(m.group(1))
    # Formato com ponto decimal: 123.45
    m = re.search(r"(\d+\.\d{2})\b", texto)
    if m:
        val = float(m.group(1))
        return val if 0.50 < val < 500_000 else None
    return None


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


def _eh_pagina_produto(html, titulo):
    """Verifica se a página parece ser de um produto/fornecedor e não blog/notícia/comparador."""
    titulo_lower = (titulo or "").lower()
    html_lower = html[:5000].lower()
    # Rejeitar páginas que claramente não são de produto
    termos_rejeitar = [
        "notícia", "artigo", "blog post", "publicado em", "autor:",
        "cookie policy", "política de privacidade", "terms of service",
        "404 not found", "page not found", "página não encontrada",
        "error 404", "403 forbidden", "access denied",
    ]
    for termo in termos_rejeitar:
        if termo in titulo_lower or termo in html_lower:
            return False
    # Indicadores positivos de página de produto
    indicadores_produto = [
        "add to cart", "adicionar ao carrinho", "comprar", "buy now",
        "add-to-cart", "addtocart", "carrinho", "cart",
        'itemprop="price"', 'itemprop="offers"', "schema.org/Product",
        "schema.org/Offer", '"@type":"Product"', '"@type": "Product"',
        "product-price", "preco", "preço", "valor unitário",
    ]
    for ind in indicadores_produto:
        if ind in html_lower or ind in html[:10000]:
            return True
    # Se tem preços detectáveis, considerar válido
    return True


MOTIVO_REJEICAO = {"texto": ""}  # por que a última página foi rejeitada (aparece no log)


def scraping_requests(session, url, headers, item_nome=None, html=None):
    """Acessa uma página via requests e extrai informações."""
    from bs4 import BeautifulSoup

    MOTIVO_REJEICAO["texto"] = ""
    try:
        if html is None:  # `html` já vem pronto quando a página foi lida pelo navegador
            resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                MOTIVO_REJEICAO["texto"] = f"HTTP {resp.status_code}"
                return None
            html = resp.text
        titulo = extrair_titulo_pagina(html)

        # Verificar se é uma página de produto antes de gastar tempo extraindo preços
        if not _eh_pagina_produto(html, titulo):
            MOTIVO_REJEICAO["texto"] = "não é página de produto"
            return None

        # Verificar se o conteúdo é relevante para o item buscado
        if item_nome and not _conteudo_relevante(html, titulo, item_nome):
            MOTIVO_REJEICAO["texto"] = "página não corresponde ao item"
            return None

        # Só loja brasileira vendendo em reais: precisa de 2 sinais (.br, moeda BRL, pt-BR, "R$"); preço em outra moeda é rejeitado
        nacional, motivo_nacional = web_precos.site_nacional(url, html)
        if not nacional:
            MOTIVO_REJEICAO["texto"] = motivo_nacional
            return None

        precos = extrair_precos_pagina(html)

        # Preço do produto anunciado: oferta em JSON-LD (sem parcelas/preço riscado) > metadados > mediana dos valores do texto
        principal = web_precos.preco_principal(html, extrair_precos_pagina, item_nome or "")
        if not principal:
            MOTIVO_REJEICAO["texto"] = "sem preço identificável (página dinâmica)"
            return None
        preco_medio = principal["preco"]
        if preco_medio not in precos:
            precos = sorted(set(precos) | {preco_medio})

        # Gerar screenshot HTML como evidência (sem precisar de Playwright)
        screenshot_path = None
        contexto_extraido = ""
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Remover scripts e styles para captura limpa
            for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
                tag.decompose()

            # Extrair trecho de texto ao redor do preço para contexto
            body_text_full = " ".join(soup.stripped_strings)
            contexto_extraido = extrair_contexto_preco(body_text_full, preco_medio)

            # Listar todos os preços encontrados
            todos_precos_str = " | ".join([f"R$ {p:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") for p in precos[:8]])
            titulo_html = html_lib.escape(titulo)
            url_html = html_lib.escape(url, quote=True)
            contexto_html = html_lib.escape(contexto_extraido or "Contexto não identificado.")
            precos_html = html_lib.escape(todos_precos_str)

            screenshot_dir = SCREENSHOT_DIR
            os.makedirs(screenshot_dir, exist_ok=True)
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', titulo[:40])
            snapshot_path = os.path.join(screenshot_dir, f"{safe_name}_{hash(url) % 10000}.html")
            with open(snapshot_path, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Evidência — {titulo_html}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; color: #333; }}
.evidence-card {{ max-width: 900px; margin: auto; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); overflow: hidden; }}
.evidence-header {{ background: linear-gradient(135deg, #001a4d 0%, #003399 100%); color: #fff; padding: 20px 24px; }}
.evidence-header h2 {{ margin: 0 0 8px 0; font-size: 18px; color: #d4af37; }}
.evidence-price {{ font-size: 28px; font-weight: bold; color: #4CAF50; margin: 12px 0; }}
.evidence-meta {{ display: flex; gap: 24px; flex-wrap: wrap; font-size: 12px; color: #ccc; margin-top: 8px; }}
.evidence-meta span {{ display: flex; align-items: center; gap: 4px; }}
.evidence-body {{ padding: 20px 24px; }}
.evidence-section {{ margin-bottom: 16px; }}
.evidence-section-title {{ font-weight: 600; color: #001a4d; font-size: 14px; margin-bottom: 6px; border-bottom: 2px solid #d4af37; padding-bottom: 4px; display: inline-block; }}
.evidence-url {{ color: #1a73e8; word-break: break-all; font-size: 13px; }}
.evidence-context {{ background: #f5f5f5; border-left: 4px solid #d4af37; padding: 12px 16px; border-radius: 0 8px 8px 0; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto; }}
.all-prices {{ background: #e8f5e9; padding: 8px 12px; border-radius: 6px; font-size: 13px; color: #2e7d32; }}
.evidence-footer {{ background: #f0f0f0; text-align: center; padding: 10px; font-size: 11px; color: #999; }}
</style></head><body>
<div class="evidence-card">
  <div class="evidence-header">
        <h2>{titulo_html}</h2>
    <div class="evidence-price">R$ {preco_medio:,.2f}</div>
    <div class="evidence-meta">
      <span>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
      <span>🌐 {extrair_dominio(url)}</span>
      <span>📊 {len(precos)} preço(s) detectado(s)</span>
    </div>
  </div>
  <div class="evidence-body">
    <div class="evidence-section">
      <div class="evidence-section-title">🔗 Fonte</div>
            <div class="evidence-url"><a href="{url_html}" target="_blank">{url_html}</a></div>
    </div>
    <div class="evidence-section">
      <div class="evidence-section-title">💰 Todos os Preços Detectados</div>
            <div class="all-prices">{precos_html}</div>
    </div>
    <div class="evidence-section">
      <div class="evidence-section-title">📄 Contexto Extraído</div>
            <div class="evidence-context">{contexto_html}</div>
    </div>
  </div>
  <div class="evidence-footer">Evidência gerada automaticamente pelo AtaCotada — Marinha do Brasil</div>
</div>
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
            "precos_detectados": precos,
            "contexto_extraido": contexto_extraido,
            "origem_preco": principal["origem"],
            "confianca": principal["confianca"],
        }
    except Exception:
        return None


# ===================== SCRAPING COM PLAYWRIGHT =====================

def _is_streamlit_cloud():
    """Detecta se está rodando no Streamlit Community Cloud."""
    # No Community Cloud, o HOME é /home/appuser e existe a variável STREAMLIT_SHARING_MODE
    return (
        os.environ.get("STREAMLIT_SHARING_MODE") is not None
        or os.environ.get("HOME", "") == "/home/appuser"
        or os.path.exists("/mount/src")
    )


def _ensure_playwright_installed():
    """Verifica se playwright está instalado (pacote + browser baixado)."""
    # Playwright não funciona no Streamlit Community Cloud (sem sudo, sem binários de browser)
    if _is_streamlit_cloud():
        return False
    try:
        from playwright.sync_api import sync_playwright
        import glob

        # Verificar em múltiplos caminhos possíveis (Codespaces podem variar o HOME)
        candidate_paths = []

        # PLAYWRIGHT_BROWSERS_PATH tem prioridade
        env_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        if env_path:
            candidate_paths.append(env_path)

        # Caminho padrão baseado no HOME atual
        home = os.path.expanduser("~")
        candidate_paths.append(os.path.join(home, ".cache", "ms-playwright"))

        # Caminhos comuns em Codespaces / dev containers
        for user_dir in ["/home/codespace", "/home/vscode", "/root"]:
            p = os.path.join(user_dir, ".cache", "ms-playwright")
            if p not in candidate_paths:
                candidate_paths.append(p)

        for browsers_path in candidate_paths:
            if os.path.isdir(browsers_path) and glob.glob(os.path.join(browsers_path, "chromium*")):
                return True

        return False
    except ImportError:
        return False


def _fechar_popups(page):
    """Tenta fechar popups, modais, banners de cookies e propagandas."""
    # Seletores de botões de fechar (ordem: mais específicos primeiro)
    seletores_fechar = [
        # Banners de cookies / LGPD
        'button:has-text("Aceitar")', 'button:has-text("Aceito")',
        'button:has-text("Concordo")', 'button:has-text("Entendi")',
        'button:has-text("Prosseguir")', 'button:has-text("Accept")',
        'button:has-text("Got it")', 'button:has-text("I agree")',
        'button:has-text("continuar e fechar")', 'button:has-text("Continuar")',
        'a:has-text("continuar e fechar")', 'a:has-text("Continuar e fechar")',
        '[class*="cookie"] button', '[id*="cookie"] button',
        '[class*="lgpd"] button', '[id*="lgpd"] button',
        '[class*="consent"] button', '[id*="consent"] button',
        # Botões X de fechar (popups promocionais / modais)
        '[class*="modal"] [class*="close"]', '[class*="modal"] button[class*="close"]',
        '[class*="popup"] [class*="close"]', '[class*="popup"] button[class*="close"]',
        '[class*="promo"] [class*="close"]', '[class*="banner"] [class*="close"]',
        '.modal .close', '.popup-close', '.btn-close',
        'button.close', '[data-dismiss="modal"]',
        '[aria-label="Close"]', '[aria-label="Fechar"]',
        '[aria-label="close"]', '[aria-label="fechar"]',
        'button[title="Close"]', 'button[title="Fechar"]',
        '[class*="close-btn"]', '[class*="closebtn"]', '[class*="close_btn"]',
        '[class*="CloseButton"]', '[class*="closeButton"]',
        '[class*="icon-close"]', '[class*="icon_close"]',
        # Overlays
        '[class*="overlay"] [class*="close"]',
        '[class*="lightbox"] [class*="close"]',
    ]
    for seletor in seletores_fechar:
        try:
            el = page.locator(seletor).first
            if el.is_visible(timeout=300):
                el.click(timeout=1000)
                time.sleep(0.3)
        except Exception:
            continue

    # Ocultar (não remover) apenas overlays escuros de fundo de modal via CSS
    try:
        page.evaluate("""() => {
            document.querySelectorAll('[class*="overlay"], [class*="backdrop"], [class*="modal-bg"]').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' && parseFloat(style.opacity) < 1) {
                    el.style.display = 'none';
                }
            });
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        }""")
    except Exception:
        pass


def _scrollar_ate_preco(page):
    """Tenta scrollar até o elemento que contém o preço na página."""
    # Primeiro tentar encontrar o container do produto (título + preço juntos)
    seletores_produto = [
        '[class*="product-info"]', '[class*="product-detail"]',
        '[class*="productInfo"]', '[class*="produto"]',
        '[class*="product-main"]', '[class*="product-summary"]',
        '[itemtype*="schema.org/Product"]',
        '#product', '#produto',
    ]
    seletores_preco = [
        '[class*="price"]', '[class*="preco"]', '[class*="valor"]',
        '[class*="Price"]', '[class*="product-price"]',
        '[data-testid*="price"]', '[itemprop="price"]',
        '.price', '#price', '.product-price',
    ]
    # Tentar container do produto primeiro
    for seletor in seletores_produto:
        try:
            el = page.locator(seletor).first
            if el.is_visible(timeout=500):
                el.scroll_into_view_if_needed(timeout=2000)
                return
        except Exception:
            continue
    # Fallback: scrollar até o preço
    for seletor in seletores_preco:
        try:
            el = page.locator(seletor).first
            if el.is_visible(timeout=500):
                el.scroll_into_view_if_needed(timeout=2000)
                # Subir um pouco para pegar contexto acima do preço
                page.evaluate("window.scrollBy(0, -150)")
                return
        except Exception:
            continue
    # Se nada encontrado, posicionar logo abaixo do cabeçalho
    try:
        page.evaluate("window.scrollTo(0, 150)")
    except Exception:
        pass


def _conteudo_relevante(html, titulo, item_nome):
    """Verifica se a página tem relação com o item buscado (não é busca/categoria genérica)."""
    if not item_nome:
        return True
    item_lower = item_nome.lower().strip()
    titulo_lower = (titulo or "").lower()
    html_lower = html[:15000].lower()
    # Palavras-chave do item (ex: "fita isolante" -> ["fita", "isolante"])
    palavras = [p for p in item_lower.split() if len(p) > 2]
    if not palavras:
        return True
    # Verificar se o título contém pelo menos uma palavra do item
    titulo_match = any(p in titulo_lower for p in palavras)
    # Verificar se o HTML contém as palavras do item próximas de preço
    html_match = all(p in html_lower for p in palavras)
    # Detectar páginas de busca/categoria (muitos produtos listados)
    indicadores_listagem = [
        "resultados para", "resultados de busca", "resultado da pesquisa",
        "mostrando", "itens encontrados", "produtos encontrados",
        "ordenar por", "filtrar por", "filtrar resultados",
    ]
    eh_listagem = any(ind in html_lower for ind in indicadores_listagem)
    # Se é uma listagem genérica e o título não menciona o item, rejeitar
    if eh_listagem and not titulo_match:
        return False
    # Se nem título nem HTML mencionam o item, rejeitar
    if not titulo_match and not html_match:
        return False
    return True


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

            # Aguardar possível carregamento dinâmico
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass  # Timeout de networkidle não é crítico

            # Fechar popups, modais e banners de cookies (1ª tentativa)
            _fechar_popups(page)

            # Simular scroll humano
            page.evaluate("window.scrollBy(0, Math.random() * 400 + 200)")
            time.sleep(gerar_delay_leitura(1.0, 2.5))

            # Fechar popups que apareceram com delay (2ª tentativa)
            _fechar_popups(page)

            # Mais um scroll
            page.evaluate("window.scrollBy(0, Math.random() * 300 + 100)")
            time.sleep(random.uniform(0.5, 1.5))

            html = page.content()
            titulo = page.title() or extrair_titulo_pagina(html)

            # Verificar se é uma página de produto (não busca/categoria)
            if not _eh_pagina_produto(html, titulo):
                browser.close()
                return None

            # Verificar se o conteúdo é relevante para o item buscado
            if not _conteudo_relevante(html, titulo, item_nome):
                browser.close()
                return None

            precos = extrair_precos_pagina(html)

            # Captura de tela real como PNG
            if screenshot_path and precos:
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                # Fechar popups tardios antes do screenshot (3ª tentativa)
                _fechar_popups(page)
                time.sleep(0.3)
                # Tentar scrollar até o elemento com preço para capturar evidência clara
                _scrollar_ate_preco(page)
                time.sleep(0.5)
                # Screenshot da viewport inteira (sem clip para evitar zoom)
                page.screenshot(path=screenshot_path, full_page=False)

            browser.close()

            if precos:
                preco_medio = sorted(precos)[len(precos) // 2]
                try:
                    body_text_full = page.locator("body").inner_text(timeout=5000)
                except Exception:
                    body_text_full = re.sub(r"<[^>]+>", " ", html)
                contexto_extraido = extrair_contexto_preco(body_text_full, preco_medio)
                resultado = {
                    "titulo": titulo,
                    "preco": preco_medio,
                    "url": url,
                    "dominio": extrair_dominio(url),
                    "screenshot": screenshot_path if screenshot_path and os.path.exists(screenshot_path) else None,
                    "precos_detectados": precos,
                    "contexto_extraido": contexto_extraido,
                }
    except Exception as e:
        # Logar o erro em vez de engolir silenciosamente
        import traceback
        traceback.print_exc()

    return resultado


# ===================== ORQUESTRADOR DE SCRAPING =====================

def _tem_secrets():
    try:
        return len(st.secrets) >= 0
    except Exception:
        return False


def executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text, max_fontes, usar_navegador=False, tempo_max_pagina_min=2):
    """Executa o scraping. `usar_navegador`: as páginas são abertas num navegador (por padrão primeiro, ou depois da leitura por texto nas lojas
    que a memória diz funcionarem por texto). Cada página tem `tempo_max_pagina_min` minutos: se travar, é abandonada, o navegador é
    reiniciado e a leitura por texto assume."""
    leitor = captura_pagina.LeitorNavegador(tempo_max_pagina_s=tempo_max_pagina_min * 60) if usar_navegador else None
    try:
        return _executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text, max_fontes, leitor)
    finally:
        if leitor is not None:
            leitor.fechar()


def _executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text, max_fontes, leitor):
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

    # Memória de lojas: lojas que já deram preço para itens parecidos são tentadas primeiro; sites que sempre falham são pulados
    memoria, onde_memoria = memoria_lojas.carregar(st.secrets if _tem_secrets() else {})
    log_msg(log_container, logs, f"🧠 Memória de lojas: {len(memoria['lojas'])} loja(s) aprendida(s), {len(memoria['falhas'])} site(s) com falha — {onde_memoria}", "info")
    if not onde_memoria.startswith("GitHub"):
        log_msg(log_container, logs, "🧠 " + memoria_lojas.diagnostico_secrets(st.secrets if _tem_secrets() else {}), "warn")

    st.session_state["prints_web"] = {}  # prints desta pesquisa (o navegador guarda o print assim que acha o preço)

    def ler_com_navegador(url, item_nome):
        """Navegador primeiro. Devolve (resultado, leu, tentou): `tentou` = o navegador foi usado nesta página; `leu` = ele a abriu (mesmo sem preço).
        Se achar o preço, já guarda o print da página (com data/hora), para não precisar abrir de novo depois. Sem resultado, quem chama usa a leitura por texto."""
        if leitor is None or not leitor.disponivel:
            return None, False, False
        log_msg(log_container, logs, f"🌐 Abrindo no navegador: {extrair_dominio(url)} ({leitor.usadas + 1}/{leitor.limite})", "info")
        lido = leitor.ler(url)
        if not lido["html"]:
            log_msg(log_container, logs, f"⚠ O navegador não abriu {extrair_dominio(url)} ({lido['erro']}); usando a leitura por texto", "warn")
            return None, False, True
        resultado_navegador = None
        try:
            resultado_navegador = scraping_requests(session, url, headers, item_nome=item_nome, html=lido["html"])
            if resultado_navegador:
                resultado_navegador["origem_preco"] = f"{resultado_navegador.get('origem_preco', '')} (lido com navegador)".strip()
                captura = leitor.capturar(url, resultado_navegador["preco"])
                if captura["imagem"]:
                    st.session_state["prints_web"][url] = captura
                    log_msg(log_container, logs, f"📸 Print guardado de {extrair_dominio(url)}", "info")
            else:
                log_msg(log_container, logs, f"⚠ O navegador abriu {extrair_dominio(url)} mas não achou preço ({MOTIVO_REJEICAO['texto'] or 'sem motivo'}); tentando a leitura por texto", "warn")
        finally:
            leitor.liberar()
        return resultado_navegador, True, True

    def ler_por_texto(url, item_nome, leve):
        """Leitura por texto. `leve`: uma tentativa só e sem pausas (usada quando o navegador já tentou ou vai tentar); senão, as tentativas de antes."""
        nonlocal headers
        tentativas = 1 if leve else MAX_RETRIES + 1
        resultado_texto = None
        for tentativa in range(tentativas):
            if not leve:
                time.sleep(gerar_delay_leitura())  # simula tempo de leitura (só na leitura por texto pura)
            resultado_texto = scraping_requests(session, url, headers, item_nome=item_nome)
            if resultado_texto:
                break
            if tentativa < tentativas - 1:
                retry_delay = gerar_delay(3.0, 7.0)
                log_msg(log_container, logs, f"🔄 Retry {tentativa + 1}/{MAX_RETRIES} em {retry_delay:.1f}s...", "warn")
                time.sleep(retry_delay)
                headers = gerar_headers()  # troca o User-Agent na nova tentativa
                session.headers.update(headers)
        return resultado_texto

    def ler_pagina(url, item_nome):
        """Lê uma página pelo método que a memória indica para a loja (navegador por padrão; texto se a loja só deu preço por texto)
        e, se não achar, tenta o outro método uma vez (leve). Devolve (resultado, método que deu o preço, métodos tentados)."""
        navegador_ativo = leitor is not None and leitor.disponivel
        tentou = {"navegador": False, "texto": False}
        texto_primeiro = navegador_ativo and memoria_lojas.metodo_preferido(memoria, url) == "texto"
        if texto_primeiro:
            tentou["texto"] = True
            resultado_pagina = ler_por_texto(url, item_nome, leve=True)
            if resultado_pagina:
                return resultado_pagina, "texto", tentou
        if navegador_ativo:
            resultado_pagina, _, tentou["navegador"] = ler_com_navegador(url, item_nome)
            if resultado_pagina:
                return resultado_pagina, "navegador", tentou
        if not texto_primeiro:
            tentou["texto"] = True
            resultado_pagina = ler_por_texto(url, item_nome, leve=tentou["navegador"])  # navegador já tentou: texto leve; senão, completo
            if resultado_pagina:
                return resultado_pagina, "texto", tentou
        return None, "texto", tentou

    try:
        for idx, item in enumerate(itens):
            item = item.strip()
            if not item:
                continue
            log_msg(log_container, logs, f"━━━ Iniciando busca: <b>{item}</b> ({idx+1}/{total_itens}) ━━━", "info")
            status_text.text(f"Buscando: {item} ({idx+1}/{total_itens})")
            progress_bar.progress((idx) / total_itens)

            candidatos_item = []
            dominios_usados = set()
            outliers_logados = set()
            reservas_logadas = set()
            contador_item = 0
            item_slug = re.sub(r'[^a-zA-Z0-9]', '_', item)[:40] or "item"

            # Selecionar variantes de busca aleatoriamente (usar mais variantes para maximizar cobertura)
            # Frases na ordem aprendida pela memória (as que mais rendem preços primeiro; de vez em quando a pior é testada); o laço para ao atingir as fontes
            variantes, explicacao_frases = memoria_lojas.ordenar_frases(memoria, VARIANTES_BUSCA + VARIANTES_RESERVA)
            log_msg(log_container, logs, f"🧠 Frases de busca: {explicacao_frases}", "info")
            dominios_falhos = set()  # site que falhou neste item não é tentado de novo nas outras buscas do mesmo item

            # 1º: lojas da memória que já deram preço para itens parecidos (cada uma uma vez só)
            for site_memoria, item_parecido in memoria_lojas.lojas_para_item(memoria, item):
                if len(atualizar_estado_orcamentos(candidatos_item, max_fontes)["validos"]) >= max_fontes:
                    break
                log_msg(log_container, logs, f"🧠 Loja da memória: {site_memoria} (já deu preço para '{item_parecido}')", "info")
                navegador_ligado = leitor is not None and leitor.disponivel
                time.sleep(gerar_delay(0.3, 0.8) if navegador_ligado else gerar_delay(1.5, 3.0))
                urls_loja = buscar_na_loja(session, item, site_memoria, headers)
                guardada = memoria_lojas.pagina_guardada(memoria, site_memoria, item_parecido)
                if guardada and guardada not in urls_loja:
                    urls_loja.append(guardada)  # atalho: a página que já deu preço (vale se os buscadores falharem)
                for url in urls_loja:
                    time.sleep(gerar_delay(0.3, 0.8) if navegador_ligado else gerar_delay(1.5, 3.5))
                    resultado, metodo_ok, _ = ler_pagina(url, item)
                    if resultado:
                        contador_item += 1
                        resultado["resultado_id"] = f"{item_slug}_{contador_item}_{abs(hash(url)) % 10000}"
                        resultado["item"] = item
                        resultado["data_coleta"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        candidatos_item.append(resultado)
                        dominios_usados.add(extrair_dominio(url))
                        memoria_lojas.registrar_acerto(memoria, url, item, metodo_ok)
                        log_msg(log_container, logs, f"💰 Orçamento da memória — {formatar_moeda_br(resultado['preco'])} em {extrair_dominio(url)}", "orcamento")
                        break
                else:
                    log_msg(log_container, logs, f"✗ {site_memoria} não teve preço para '{item}' desta vez", "warn")
                dominios_falhos.update({site_memoria, "www." + site_memoria})

            for variante in variantes:
                estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)
                if len(estado_item["validos"]) >= max_fontes:
                    log_msg(log_container, logs, f"✓ {max_fontes} orçamentos válidos encontrados para '{item}'. Avançando.", "success")
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
                    log_msg(log_container, logs, f"⚠ Nenhum resultado encontrado para \"{query}\" — {engine}", "warn")
                    # buscador bloqueado/com erro não diz nada sobre a frase: só conta quando houve resposta
                    if "erro" not in engine and "HTTP" not in engine:
                        memoria_lojas.registrar_busca(memoria, variante, 0)
                    continue

                log_msg(log_container, logs, f"📋 {len(urls)} resultados encontrados via {engine}", "info")
                acertos_variante = 0  # preços válidos que esta frase rendeu

                for url in urls:
                    estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)
                    if len(estado_item["validos"]) >= max_fontes:
                        break

                    dominio = extrair_dominio(url)
                    if dominio in dominios_usados or dominio in dominios_falhos:
                        continue
                    # Só se pula o site pelo MESMO método que vai ser usado: o navegador tem mais chance e não é barrado por falhas da leitura por texto
                    metodo_atual = "navegador" if (leitor is not None and leitor.disponivel) else "texto"
                    if memoria_lojas.deve_pular(memoria, url, metodo_atual):
                        log_msg(log_container, logs, f"⏭ {dominio} pulado (a leitura por {metodo_atual} falhou {memoria_lojas.FALHAS_PARA_PULAR}+ vezes em pesquisas anteriores)", "info")
                        dominios_falhos.add(dominio)
                        continue

                    log_msg(log_container, logs, f"🌐 Acessando: {dominio}", "info")

                    # Delay entre acessos a sites
                    # (com o navegador ativo a própria abertura da página já espaça os acessos: pausa curta)
                    delay = gerar_delay(0.3, 0.8) if (leitor is not None and leitor.disponivel) else gerar_delay(2.5, 6.0)
                    log_msg(log_container, logs, f"⏳ Delay de navegação: {delay:.1f}s", "info")
                    time.sleep(delay)

                    resultado = None
                    metodo_ok, tentou_navegador, tentou_texto = "texto", False, False
                    screenshot_path = os.path.join(
                        SCREENSHOT_DIR,
                        f"{item_slug}_{contador_item + 1}.png",
                    )

                    # Se Playwright selecionado e disponível, usar primeiro
                    if playwright_disponivel:
                        log_msg(log_container, logs, f"🎭 Tentando com navegador automatizado: {dominio}", "info")
                        time.sleep(gerar_delay(1.5, 3.5))
                        resultado = scraping_playwright(url, item, screenshot_path)

                    # Método pela memória da loja (navegador por padrão) e fallback leve pelo outro
                    if not resultado:
                        resultado, metodo_ok, tentou_metodos = ler_pagina(url, item)
                        tentou_navegador, tentou_texto = tentou_metodos["navegador"], tentou_metodos["texto"]

                    if resultado:
                        contador_item += 1
                        resultado["resultado_id"] = f"{item_slug}_{contador_item}_{abs(hash(url)) % 10000}"
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

                        candidatos_item.append(resultado)
                        dominios_usados.add(dominio)
                        memoria_lojas.registrar_acerto(memoria, url, item, metodo_ok)
                        acertos_variante += 1
                        estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)

                        for descartado in estado_item["descartados"]:
                            if descartado["resultado_id"] in outliers_logados:
                                continue
                            log_msg(
                                log_container,
                                logs,
                                f"🚫 Outlier descartado em {descartado['dominio']}: {formatar_moeda_br(descartado['preco'])} acima do limite de {formatar_moeda_br(descartado['limite_superior'])} para '{item}'. Buscando reposição.",
                                "warn",
                            )
                            outliers_logados.add(descartado["resultado_id"])

                        if resultado["resultado_id"] in estado_item["ids_validos"]:
                            log_msg(
                                log_container,
                                logs,
                                f"💰 Orçamento [{len(estado_item['validos'])}/{max_fontes}] — {formatar_moeda_br(resultado['preco'])} em {dominio}",
                                "orcamento",
                            )
                        elif resultado["resultado_id"] not in estado_item["ids_descartados"] and resultado["resultado_id"] not in reservas_logadas:
                            log_msg(
                                log_container,
                                logs,
                                f"📌 Cotação extra mantida em reserva: {formatar_moeda_br(resultado['preco'])} em {dominio}",
                                "info",
                            )
                            reservas_logadas.add(resultado["resultado_id"])
                    else:
                        log_msg(log_container, logs, f"✗ Sem preço extraível de {dominio}" + (f" — {MOTIVO_REJEICAO['texto']}" if MOTIVO_REJEICAO["texto"] else ""), "error")
                        dominios_falhos.add(dominio)
                        if MOTIVO_REJEICAO["texto"] != "página não corresponde ao item":  # a loja pode servir para outro item
                            if tentou_navegador:
                                memoria_lojas.registrar_falha(memoria, url, "navegador")
                            if tentou_texto:
                                memoria_lojas.registrar_falha(memoria, url, "texto")

                memoria_lojas.registrar_busca(memoria, variante, acertos_variante)

            estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)
            if len(estado_item["validos"]) < max_fontes:
                log_msg(log_container, logs, f"⚠ Apenas {len(estado_item['validos'])} orçamento(s) válido(s) encontrado(s) para '{item}'", "warn")

            orcamentos_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)["validos"]
            resultados.extend(orcamentos_item)

            # Delay maior entre itens diferentes
            if idx < total_itens - 1:
                delay = gerar_delay(4.0, 8.0)
                log_msg(log_container, logs, f"⏳ Intervalo entre itens: {delay:.1f}s", "info")
                time.sleep(delay)
    finally:  # grava o que a pesquisa aprendeu mesmo que ela seja interrompida por um erro
        try:
            log_msg(log_container, logs, "🧠 Memória de lojas: " + memoria_lojas.salvar(memoria, st.secrets if _tem_secrets() else {}), "info")
        except Exception:
            pass

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


def gerar_pdf_evidencias(resultados):
    """Gera um PDF único com todas as evidências de preço coletadas."""
    from fpdf import FPDF

    class EvidenciaPDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(0, 26, 77)
            self.cell(0, 8, "AtaCotada - Evidencias de Pesquisa de Precos", align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(212, 175, 55)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Marinha do Brasil - Pagina {self.page_no()}/{{nb}}", align="C")

    pdf = EvidenciaPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    screenshots = [r for r in resultados if r.get("screenshot") and os.path.exists(r.get("screenshot", ""))]

    if not screenshots:
        pdf.add_page()
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(0, 40, "Nenhuma evidencia capturada.", align="C")
        buf = BytesIO()
        pdf.output(buf)
        buf.seek(0)
        return buf

    # Capa
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 26, 77)
    pdf.cell(0, 15, "Relatorio de Evidencias", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Pesquisa de Precos - Web Scraping", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_draw_color(212, 175, 55)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Total de evidencias: {len(screenshots)}", align="C", new_x="LMARGIN", new_y="NEXT")
    itens_unicos = list(set(r.get("item", "") for r in screenshots))
    pdf.cell(0, 8, f"Itens pesquisados: {len(itens_unicos)}", align="C", new_x="LMARGIN", new_y="NEXT")

    # Páginas de evidência
    for i, r in enumerate(screenshots, 1):
        pdf.add_page()

        # Cabeçalho da evidência
        pdf.set_fill_color(0, 26, 77)
        pdf.rect(10, pdf.get_y(), 190, 28, "F")
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(212, 175, 55)
        y_start = pdf.get_y() + 3
        pdf.set_xy(14, y_start)
        pdf.cell(180, 6, f"Evidencia {i}/{len(screenshots)}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(14)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(255, 255, 255)
        titulo_clean = (r.get("titulo", "Sem titulo") or "Sem titulo").encode("latin-1", "replace").decode("latin-1")
        pdf.cell(180, 5, titulo_clean[:90], new_x="LMARGIN", new_y="NEXT")

        # Preço em destaque
        pdf.set_x(14)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(76, 175, 80)
        preco_str = f"R$ {r['preco']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        pdf.cell(180, 10, preco_str, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(6)

        # Info do item
        pdf.set_text_color(60, 60, 60)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Item:")
        pdf.set_font("Helvetica", "", 10)
        item_clean = (r.get("item", "-") or "-").encode("latin-1", "replace").decode("latin-1")
        pdf.cell(0, 7, item_clean, new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Fornecedor:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, r.get("dominio", "-"), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Data Coleta:")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, r.get("data_coleta", datetime.now().strftime("%d/%m/%Y %H:%M")), new_x="LMARGIN", new_y="NEXT")

        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "URL:")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(26, 115, 232)
        url_str = (r.get("url", "-") or "-")[:120]
        pdf.cell(0, 7, url_str, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(60, 60, 60)

        # Separador
        pdf.ln(4)
        pdf.set_draw_color(212, 175, 55)
        pdf.set_line_width(0.3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        # Conteúdo da evidência (trecho do HTML)
        sc_path = r["screenshot"]
        if sc_path.endswith(".html"):
            try:
                from bs4 import BeautifulSoup as BS4
                with open(sc_path, "r", encoding="utf-8") as f:
                    ev_html = f.read()
                ev_soup = BS4(ev_html, "html.parser")
                # Pegar o trecho de contexto
                contexto_div = ev_soup.select_one(".evidence-context")
                contexto_texto = r.get("contexto_extraido", "")
                if not contexto_texto and contexto_div:
                    contexto_texto = contexto_div.get_text("\n", strip=True)
                if not contexto_texto:
                    contexto_texto = ev_soup.get_text(separator="\n", strip=True)
                contexto_texto = normalizar_texto_contexto(contexto_texto)[:1500]
                contexto_texto = contexto_texto.encode("latin-1", "replace").decode("latin-1")

                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(0, 26, 77)
                pdf.cell(0, 7, "Contexto Extraido da Pagina:", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(80, 80, 80)
                pdf.multi_cell(190, 5, contexto_texto)
            except Exception:
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 7, f"Evidencia salva em: {sc_path}", new_x="LMARGIN", new_y="NEXT")

    buf = BytesIO()
    pdf.output(buf)
    buf.seek(0)
    return buf


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
    st.page_link("pages/CATMAT_CATSERV_Automatico.py", label="CATMAT/CATSERV", icon="🔎")
    st.page_link("pages/Cotação_Rápida.py", label="Cotação Rápida", icon="⚡")
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
    st.page_link("pages/Calculo_IPCA.py", label="Cálculo IPCA", icon="📊")
    st.markdown("---")
    st.markdown("## LINKS ÚTEIS")
    st.markdown("""<div style="margin-bottom: 0.6rem;">
        <a href="https://detetive-obtencao.vercel.app/" target="_blank" style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
            🚨 Detetive Obtenção
        </a>
    </div>
    <div style="margin-bottom: 1rem;">
        <a href="https://depurador.streamlit.app/" target="_blank" style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
            🧾 Depurador de Orçamentos
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

import streamlit.components.v1 as _components

_como_funciona_html = """
<div style="background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%); border: 1px solid #333; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.6;">
    <div style="font-size: 1.2rem; font-weight: bold; color: #d4af37; margin-bottom: 1rem;">⚙️ Como Funciona o Web Scraping</div>
    <div style="margin-bottom: 0.8rem;">Este módulo automatiza a pesquisa de preços na internet para fins de <b>cotação e estimativa de preços</b>,
    em conformidade com a IN 65/2021. O sistema busca preços diretamente em sites de fornecedores
    (ignorando marketplaces como Mercado Livre, Amazon, Shopee etc.) para obter valores mais próximos
    da realidade praticada no comércio direto.</div>

    <div style="font-weight:bold; color:#d4af37; margin-bottom: 0.5rem;">🔄 Fluxo de Execução:</div>
    <div style="margin-left: 1rem; margin-bottom: 1rem;">
        <div style="margin-bottom:0.3rem;">1. Você informa os itens que deseja pesquisar (um por linha)</div>
        <div style="margin-bottom:0.3rem;">2. O sistema gera até <b>5 variações de busca</b> para cada item (ex: "caneta preço", "comprar caneta online", "caneta fornecedor")</div>
        <div style="margin-bottom:0.3rem;">3. Para cada variação, busca URLs relevantes usando <b>4 mecanismos em cascata</b>:
            <br><b>DDGS API → DuckDuckGo HTML → Google → Bing</b></div>
        <div style="margin-bottom:0.3rem;">4. Acessa cada site encontrado e extrai preços usando <b>4 estratégias de detecção</b>:
            <br>dados estruturados (JSON-LD) → meta tags → classes de preço no HTML → regex em R$</div>
        <div style="margin-bottom:0.3rem;">5. Salva uma evidência formatada (snapshot) de cada página com preço encontrado</div>
        <div style="margin-bottom:0.3rem;">6. Gera o <b>relatório padrão da Cotação Rápida</b> (PDF e Excel, com mapa comparativo) e exporta também CSV, JSON e PDF de evidências</div>
    </div>

    <div style="font-weight:bold; color:#d4af37; margin-bottom: 0.5rem;">⚙️ Configurações Disponíveis:</div>
    <div style="margin-left: 1rem; margin-bottom: 1rem;">
        <div style="margin-bottom:0.4rem;">• <b>Navegador Automatizado (Playwright):</b> Quando ativado, usa um navegador real (Chromium)
            para acessar sites que carregam preços via JavaScript. É mais lento, mas captura preços
            de sites dinâmicos que o modo padrão não consegue ler. <i>Recomendação: deixe desativado
            na maioria dos casos; ative apenas se estiver recebendo poucos resultados.</i></div>
        <div style="margin-bottom:0.4rem;">• <b>Máx. fontes por item:</b> Quantidade máxima de orçamentos diferentes que o sistema
            buscará para cada material. <i>Recomendação: <b>3</b> fontes é o ideal — já atende
            à IN 65/2021 e mantém a pesquisa rápida.</i></div>
        <div style="margin-bottom:0.4rem;">• <b>Delay mínimo / máximo (seg):</b> Intervalo de espera entre cada requisição,
            simulando comportamento humano. Evita bloqueios dos sites.
            <i>Recomendação: mínimo <b>2s</b> e máximo <b>6s</b> (padrão) —
            aumente para 4s/10s se pesquisar muitos itens de uma vez.</i></div>
    </div>
</div>
"""
with st.expander("🧠 Memória de lojas (aprende com o uso)", expanded=False):
    st.caption("A cada pesquisa o sistema guarda as lojas que deram preço e os itens que cada uma cotou; nas próximas, tenta primeiro "
               f"essas lojas para itens parecidos. Sites que falharam {memoria_lojas.FALHAS_PARA_PULAR} vezes sem nunca dar preço são pulados.")
    if st.button("Ver o que o sistema já aprendeu", key="ver_memoria_lojas"):
        memoria_vista, onde_vista = memoria_lojas.carregar(st.secrets if _tem_secrets() else {})
        st.caption(f"Onde está guardada: {onde_vista}")
        if not onde_vista.startswith("GitHub"):
            st.warning(memoria_lojas.diagnostico_secrets(st.secrets if _tem_secrets() else {}))
        if memoria_vista["lojas"]:
            st.dataframe(pd.DataFrame([{"Loja": site, "Preços encontrados": l["acertos"], "Pelo navegador": l.get("metodos", {}).get("navegador", 0),
                                        "Por texto": l.get("metodos", {}).get("texto", 0), "Último": l["ultimo"], "Itens cotados": ", ".join(l["itens"][:15])}
                                       for site, l in sorted(memoria_vista["lojas"].items(), key=lambda x: -x[1]["acertos"])]),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma loja aprendida ainda: a memória se forma com as próximas pesquisas.")
        if memoria_vista.get("frases"):
            st.markdown("**Frases de busca** (as de maior nota são usadas primeiro; a nota é preços válidos por busca)")
            st.dataframe(pd.DataFrame([{"Frase": f, "Buscas (peso recente)": round(d.get("usos", 0), 1), "Preços válidos": round(d.get("acertos", 0), 1),
                                        "Nota": round(memoria_lojas.nota_da_frase(memoria_vista, f), 2), "Último uso": d.get("ultimo", "")}
                                       for f, d in sorted(memoria_vista["frases"].items(), key=lambda x: -memoria_lojas.nota_da_frase(memoria_vista, x[0]))]),
                         hide_index=True, use_container_width=True)
        puladas = [{"Site": site, "Falhas no navegador": f.get("navegador", 0), "Falhas por texto": f.get("texto", 0), "Última": f["ultimo"]}
                   for site, f in memoria_vista["falhas"].items()
                   if max(f.get("navegador", 0), f.get("texto", 0)) >= memoria_lojas.FALHAS_PARA_PULAR]
        if puladas:
            st.markdown(f"**Sites pulados** (cada método é pulado só depois de {memoria_lojas.FALHAS_PARA_PULAR} falhas dele mesmo; o navegador não é barrado por falhas da leitura por texto)")
            st.dataframe(pd.DataFrame(puladas), hide_index=True, use_container_width=True)

with st.expander("⚙️ Como Funciona o Web Scraping", expanded=False):
    _components.html(_como_funciona_html, height=700, scrolling=True)

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
    if _is_streamlit_cloud():
        usar_playwright = False  # na nuvem o navegador é o "Navegador primeiro" abaixo
    else:
        usar_playwright = st.checkbox(
            "Usar navegador automatizado",
            value=False,
            help="Ativa o Playwright para sites com carregamento dinâmico. Mais lento, porém mais preciso.",
        )
        if usar_playwright:
            if _ensure_playwright_installed():
                st.success("✅ Playwright ativo", icon="🎭")
            else:
                st.error("❌ Playwright não disponível. Instale com: pip install playwright && playwright install chromium")
                usar_playwright = False
    navegador_ok, navegador_motivo = captura_pagina.disponivel()
    usar_navegador = st.checkbox(
        "Navegador primeiro (Playwright)",
        value=navegador_ok,
        disabled=not navegador_ok,
        help="As páginas são abertas num navegador do servidor, que carrega o JavaScript e fecha popups. Se ele não achar o preço, a leitura por texto "
             "tenta uma vez. Lojas que a memória diz funcionarem só por texto começam pelo texto. Mais lento (5 a 15 s por página).",
    )
    tempo_max_pagina = 2
    if navegador_ok:
        if usar_navegador:
            tempo_max_pagina = st.number_input("Tempo máx. por página no navegador (min)", min_value=1, max_value=10, value=2,
                                               help="Se uma página travar, o navegador a abandona depois desse tempo, é reiniciado e a leitura por texto tenta no lugar.")
    else:
        st.caption(f"Navegador indisponível (leitura simples por texto): {navegador_motivo}")
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
            max_fontes=max_fontes,
            usar_navegador=usar_navegador,
            tempo_max_pagina_min=int(tempo_max_pagina),
        )

        # Armazenar resultados no session_state
        st.session_state["scraping_resultados"] = resultados
        st.session_state["scraping_itens"] = itens
        st.session_state["scraping_excluir_ids"] = []

# ===================== EXIBIÇÃO DE RESULTADOS =====================

if "scraping_resultados" in st.session_state and st.session_state["scraping_resultados"]:
    resultados_brutos = st.session_state["scraping_resultados"]
    opcoes_exclusao = []
    labels_exclusao = {}
    for indice, resultado in enumerate(resultados_brutos, start=1):
        resultado_id = resultado.get("resultado_id") or f"resultado_{indice}"
        resultado["resultado_id"] = resultado_id
        opcoes_exclusao.append(resultado_id)
        labels_exclusao[resultado_id] = (
            f"{resultado.get('item', 'Item')} | {resultado.get('dominio', 'Fornecedor')} | "
            f"{formatar_moeda_br(resultado.get('preco'))}"
        )

    st.session_state["scraping_excluir_ids"] = [
        resultado_id
        for resultado_id in st.session_state.get("scraping_excluir_ids", [])
        if resultado_id in opcoes_exclusao
    ]

    st.markdown("#### Ajuste Manual da Composição")
    st.multiselect(
        "Selecione os orçamentos que devem sair da composição:",
        options=opcoes_exclusao,
        key="scraping_excluir_ids",
        format_func=lambda resultado_id: labels_exclusao.get(resultado_id, resultado_id),
        help="Os orçamentos selecionados aqui saem do resumo, das evidências e das exportações desta execução.",
    )

    resultados = [
        resultado for resultado in resultados_brutos
        if resultado.get("resultado_id") not in st.session_state.get("scraping_excluir_ids", [])
    ]

    st.markdown("---")
    st.markdown("### 📋 Resultados")

    st.caption(
        f"{len(resultados)} de {len(resultados_brutos)} orçamento(s) permanecem na composição após os descartes automáticos e manuais."
    )

    if not resultados:
        st.warning("⚠️ Todos os orçamentos desta execução foram retirados da composição.")
    else:

        tab_relatorio, tab_tabela, tab_resumo, tab_evidencias, tab_export = st.tabs(
            ["📑 Relatório Padrão", "📊 Tabela Completa", "📈 Resumo", "📸 Evidências", "📥 Exportar"]
        )

        with tab_relatorio:
            itens_pesquisados = st.session_state.get("scraping_itens", [])
            precos_por_item = st.selectbox("Preços por item no relatório", [3, 4, 5], index=0, key="precos_por_item_relatorio",
                                           help="Quantas colunas de preço o mapa comparativo (tabela, PDF e Excel) mostra. O padrão é 3.")
            analise = web_precos.analisar_todos(itens_pesquisados, resultados, max_precos=precos_por_item)
            prints = st.session_state.get("prints_web", {})
            info_relatorio = {"max_precos": precos_por_item, "prints": {u: v for u, v in prints.items() if v.get("imagem")}, "motores": "DuckDuckGo e Bing",
                              "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")}
            st.caption("Mesmas regras da Cotação Rápida: sem outliers, preços a ±30% da média, mapa comparativo na 1ª página, "
                       "endereço e data/hora do acesso de cada preço.")
            st.dataframe(relatorio_web.tabela_mapa_web(analise, precos_por_item), use_container_width=True, hide_index=True)
            baixas = [r for r in resultados if r.get("confianca") == "baixa"]
            if baixas:
                st.warning(f"{len(baixas)} preço(s) vieram da leitura do texto da página (confiança baixa): confira o anúncio antes de usar.")
            with st.expander("📸 Prints reais das páginas dos preços do mapa", expanded=bool(prints)):
                paginas_mapa = [{"url": p["url"], "preco": p["preco"]} for r in analise for p in r["precos"]]
                paginas_sem_print = [p for p in paginas_mapa if not prints.get(p["url"], {}).get("imagem")]
                ja_com_print = len({p["url"] for p in paginas_mapa}) - len({p["url"] for p in paginas_sem_print})
                pode_print, motivo_print = captura_pagina.disponivel()
                st.caption("Quando o navegador acha o preço durante a pesquisa, o print já fica guardado (com data, hora e endereço no rodapé). Aqui você tira só os "
                           "que faltam (páginas lidas por texto): o navegador as abre, rola até o preço e destaca o valor. Os prints entram como anexo no PDF.")
                if paginas_mapa:
                    st.caption(f"{ja_com_print} página(s) do mapa já têm print; {len({p['url'] for p in paginas_sem_print})} faltam.")
                if not pode_print:
                    st.info(f"Prints indisponíveis neste servidor: {motivo_print}.")
                elif not paginas_mapa:
                    st.info("Nenhum preço no mapa para tirar print.")
                elif not paginas_sem_print:
                    st.success("Todas as páginas do mapa já têm print.")
                else:
                    if st.button(f"📸 Tirar os prints das {len({p['url'] for p in paginas_sem_print})} página(s) que faltam", key="botao_prints_web"):
                        barra = st.progress(0)
                        texto_barra = st.empty()

                        def andamento(feitas, total, url):
                            barra.progress(feitas / max(total, 1))
                            texto_barra.text(f"Capturando {feitas + 1}/{total}: {extrair_dominio(url)}" if url else "Concluído")

                        novos = captura_pagina.capturar_prints(paginas_sem_print, andamento)
                        st.session_state["prints_web"] = {**st.session_state.get("prints_web", {}), **novos}
                        st.rerun()
                if prints:
                    feitos = [(u, v) for u, v in prints.items() if v.get("imagem")]
                    falhos = [(u, v) for u, v in prints.items() if not v.get("imagem")]
                    if feitos:
                        st.success(f"{len(feitos)} print(s) prontos; entram no PDF abaixo.")
                    for u, v in falhos:
                        st.warning(f"Sem print de {extrair_dominio(u)}: {v.get('erro', 'erro')}")
                    if feitos:
                        import zipfile
                        pacote = BytesIO()
                        with zipfile.ZipFile(pacote, "w", zipfile.ZIP_DEFLATED) as arquivo_zip:
                            for n, (u, v) in enumerate(feitos, start=1):
                                arquivo_zip.writestr(f"print_{n:02d}_{re.sub(r'[^a-zA-Z0-9]+', '_', extrair_dominio(u))}.jpg", v["imagem"])
                        st.download_button("⬇️ Baixar os prints (ZIP)", pacote.getvalue(), file_name="prints_pesquisa_web.zip", mime="application/zip")
                        for u, v in feitos[:3]:
                            st.image(v["imagem"], caption=f"{extrair_dominio(u)} — {v['capturado_em']}")

            col_r1, col_r2 = st.columns(2)
            col_r1.download_button(
                "📄 Baixar relatório PDF (padrão Cotação Rápida)", data=relatorio_web.gerar_pdf_mapa(analise, info_relatorio),
                file_name=f"pesquisa_web_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf", mime="application/pdf", type="primary", use_container_width=True,
            )
            col_r2.download_button(
                "📊 Baixar relatório Excel", data=relatorio_web.gerar_excel_mapa(analise, info_relatorio),
                file_name=f"pesquisa_web_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True,
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
                col_ev_info, col_ev_pdf = st.columns([3, 1])
                with col_ev_info:
                    st.markdown(f"**{len(screenshots)} evidências visuais capturadas**")
                with col_ev_pdf:
                    pdf_ev_data = gerar_pdf_evidencias(resultados)
                    st.download_button(
                        label="📑 Exportar Evidências em PDF",
                        data=pdf_ev_data,
                        file_name=f"evidencias_scraping_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                    )
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
                                # Botão de download do HTML
                                st.download_button(
                                    label="⬇️ Baixar evidência",
                                    data=html_content,
                                    file_name=f"evidencia_{r['item']}_{r['dominio']}.html",
                                    mime="text/html",
                                    key=f"dl_html_{r['item']}_{r['dominio']}_{id(r)}",
                                )
                            except Exception:
                                st.markdown(f"📄 Evidência salva em: {sc_path}")
                        else:
                            st.image(sc_path, caption=f"{r['dominio']} - {r['data_coleta']}")
                            # Botão de download da imagem PNG
                            try:
                                with open(sc_path, "rb") as img_file:
                                    img_bytes = img_file.read()
                                st.download_button(
                                    label="⬇️ Baixar screenshot",
                                    data=img_bytes,
                                    file_name=f"screenshot_{r['item']}_{r['dominio']}.png",
                                    mime="image/png",
                                    key=f"dl_img_{r['item']}_{r['dominio']}_{id(r)}",
                                )
                            except Exception:
                                pass
                        st.markdown(f"**Link:** [{r['url']}]({r['url']})")
                        if r.get("contexto_extraido"):
                            st.text_area(
                                "Contexto extraído",
                                value=r["contexto_extraido"],
                                height=130,
                                disabled=True,
                                key=f"contexto_{r['resultado_id']}",
                            )
            else:
                st.info(
                    "Nenhuma evidência visual capturada nesta execução."
                )

        with tab_export:
            st.markdown("#### 📥 Exportar Relatório")

            col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)

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

            with col_exp4:
                pdf_data = gerar_pdf_evidencias(resultados)
                st.download_button(
                    label="📑 Baixar Evidências PDF",
                    data=pdf_data,
                    file_name=f"evidencias_scraping_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

elif "scraping_resultados" in st.session_state and not st.session_state["scraping_resultados"]:
    st.warning("⚠️ O scraping foi executado mas nenhum orçamento foi encontrado. Tente com outros termos.")
