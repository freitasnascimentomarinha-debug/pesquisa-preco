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
recarregar_se_mudou('embalagem', 'banco_sinonimos', 'sinonimos', 'naturezas', 'cotacao_rapida', 'relatorio_cotacao_rapida', 'relatorio_nf_lote', 'web_precos', 'relatorio_web', 'memoria_lojas', 'desempenho', 'captura_pagina', 'busca_interna', 'naturezas')
import embalagem  # noqa: E402  (medida e unidade de fornecimento do item)
import sinonimos  # noqa: E402  (nome de mercado do item e conferência do nome do produto)
import naturezas  # noqa: E402  (natureza/ramo do item)
import busca_interna  # noqa: E402  (busca dentro do site da loja)
import desempenho  # noqa: E402  (tempo e acertividade: a pesquisa aprende o que funciona)
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
    # Universidades, justiça, legislativo, ministério público e militares: não vendem
    ".edu.br", ".edu", ".jus.br", ".leg.br", ".mp.br", ".mil.br", "scielo.", "academia.edu", "researchgate.net",
    # Artigos científicos, o próprio Bing, calculadoras e conversores
    "bing.com", "microsoft.com", "arxiv.org", "ssrn.com", "sciencedirect.com", "springer.com", "oup.com", "doi.org", "nih.gov",
    "researchgate.net", "wiley.com", "jstor.org", "thecalculatorsite", "unitconverters", "seguros",
    # Jornais, portais de notícia e de conteúdo escolar
    "jornal", "folha.", "estadao.", "correio", "diario", "gazeta", "cnn", "bbc.", "r7.com", "infomoney", "exame.com",
    "olhardigital", "tecmundo", "techtudo", "canaltech", "mundoeducacao", "brasilescola", "todamateria", "significados.",
    "infoescola", "dicio.com", "oglobo", "veja.abril", "istoe", "metropoles", "poder360",
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
        "Accept-Encoding": "gzip, deflate",
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
        if re.match(r"^(www\.|[a-z0-9-]+\.)?(usp|unicamp|unesp|unb|uerj|uff|uft|ufrj|ufmg|ufsc|ufpr|ufrgs|ufba|ufpe|ufc|ufes|ufg|ufu|ufscar|ufop|ufpa|ufam|ufrn|ufpb|uespi|uepb|uece|uem|uel|udesc|unifesp|unir|unifei|utfpr|ifsp|ifrj|ifsc|ifpr|ifmg|ifba)\.br$", dominio):
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
    """Recalcula o conjunto válido do item após cada nova cotação, com a MESMA regra do relatório (web_precos.analisar_item_web: sem
    outliers e cada preço a até 30% da média). Assim a pesquisa só dá o item por resolvido quando o relatório vai mostrar max_fontes
    preços; se a regra derrubar algum, ela continua procurando."""
    _, descartados, _ = classificar_orcamentos_item(candidatos_item, max_fontes)  # outliers altos (para o log)
    analise = web_precos.analisar_item_web("", candidatos_item, max_precos=max_fontes)
    por_endereco = {}
    for candidato in candidatos_item:
        por_endereco.setdefault(candidato.get("url") or candidato.get("dominio"), candidato)
    validos = [por_endereco[p["url"] or p["dominio"]] for p in analise["precos"] if (p["url"] or p["dominio"]) in por_endereco]
    ids_validos = {registro["resultado_id"] for registro in validos}
    ids_descartados = {registro["resultado_id"] for registro in descartados}
    reservas = [c for c in candidatos_item if c["resultado_id"] not in ids_validos and c["resultado_id"] not in ids_descartados]
    return {
        "validos": validos,
        "ids_validos": ids_validos,
        "descartados": descartados,
        "ids_descartados": ids_descartados,
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


INTERVALO_MIN_BUSCA_S = 2.0  # pausa mínima entre duas requisições a buscadores (DuckDuckGo, Google), de qualquer tipo
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
DDG_VAZIOS_SEGUIDOS = {"n": 0}  # o ddgs costuma disfarçar bloqueio de "sem resultados": 2 vazios seguidos são tratados como bloqueio


def descansar_ddg():
    """Marca o descanso do DuckDuckGo: 60 s no 1º bloqueio, depois 120, 240... (insistir cedo demais renova o bloqueio). Devolve os segundos."""
    pausa = min(PAUSA_APOS_BLOQUEIO_DDG * (2 ** DDG_BLOQUEIOS_SEGUIDOS["n"]), PAUSA_MAXIMA_DDG)
    DDG_BLOQUEIOS_SEGUIDOS["n"] += 1
    DDG_PROXIMA_TENTATIVA["ate"] = time.time() + pausa
    return pausa


def ddg_voltou():
    DDG_PROXIMA_TENTATIVA["ate"] = 0.0
    DDG_BLOQUEIOS_SEGUIDOS["n"] = 0
    DDG_VAZIOS_SEGUIDOS["n"] = 0


def _raizes_do_item(item):
    """Raízes (5 primeiras letras, sem acento) das palavras do item com mais de 3 letras: 'fita isolante' -> {'fita', 'isola'}."""
    import unicodedata
    texto = unicodedata.normalize("NFD", (embalagem.base(item) + " " + sinonimos.termo_busca(item)).lower() if item else "")  # nome sem medida/embalagem + nome de mercado
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return {p[:5] for p in re.findall(r"[a-z0-9]+", texto) if len(p) > 3}


def _medida_primeiro(item, pares):
    """[(url, texto do resultado)] -> urls, com os que citam a mesma medida do item na frente e os de medida diferente no fim."""
    ordem = {"igual": 0, "sem_medida": 1, "diferente": 2}
    return [u for u, _ in sorted(pares, key=lambda par: ordem[embalagem.confere(item or "", par[1])])]


def _cita_o_item(texto, raizes):
    """O texto (título, trecho ou endereço) cita pelo menos uma palavra do item? Sem raízes (item desconhecido), não filtra."""
    if not raizes:
        return True
    import unicodedata
    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto).lower()) if unicodedata.category(c) != "Mn")
    return any(r in texto for r in raizes)


def _com_cara_de_venda(resultados, item=None):
    """Resultados do ddgs (dicts com title/body/href) cujo título, trecho ou endereço têm sinal de venda (R$, preço, comprar, loja, frete...).
    Frases genéricas ("valor", "atacado") trazem artigos científicos, calculadoras e notícias; esses ficam de fora."""
    raizes = _raizes_do_item(item)
    pares = [(r["href"], f"{r.get('title', '')} {r.get('body', '')} {r['href']}") for r in resultados if r.get("href") and dominio_valido(r["href"])]
    return _medida_primeiro(item, [(u, t) for u, t in pares
                                   if SINAIS_VENDA.search(t.lower()) and _cita_o_item(t, raizes) and not sinonimos.excluido(item or "", t)])


def buscar_ddgs_api(query, num_results=8, item=None):
    """Busca usando o pacote ddgs (DuckDuckGo Search) — mais confiável em servidores."""
    intervalo_entre_buscas()
    try:
        from ddgs import DDGS
        results = list(DDGS().text(query, region="br-pt", max_results=num_results))
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="br-pt", max_results=num_results))
        except Exception as erro:
            DIAG_BUSCA["DDGS"] = "0 sites" if "No results" in str(erro) else f"erro {type(erro).__name__}"
            return []
    except Exception as erro:
        # o pacote levanta "No results found" quando a frase não tem resultado: não é bloqueio
        DIAG_BUSCA["DDGS"] = "0 sites" if "No results" in str(erro) else f"erro {type(erro).__name__}"
        return []
    urls = _com_cara_de_venda(results, item)
    # respondeu, mas nada com cara de venda: não é bloqueio (o contador de respostas vazias só conta "0 sites" puro)
    DIAG_BUSCA["DDGS"] = f"{len(urls)} sites" if urls or not results else f"0 sites ({len(results)} sem cara de venda)"
    return _dedup_urls(urls, num_results)


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


SINAIS_VENDA = re.compile(r"r\$|\bcompr(a|ar|e)\b|\bpre[çc]o|\bloja\b|\boferta|\bcomprar\b|\bfrete\b|\bcarrinho\b|\bem estoque\b|\bparcel")


SERPER_URL = "https://google.serper.dev/search"
TEMPO_MAX_ITEM_S = 120  # meta: cada item termina (com os preços que achou) em até 2 minutos
TEMPO_MAX_LOJAS_MEMORIA_S = 40  # parte do tempo do item que pode ir para as lojas da memória antes da busca
NAVEGADOR_MAX_POR_ITEM = 3  # páginas abertas no navegador por item (cada uma custa 10-15 s)
MOTIVOS_PARA_NAVEGADOR = {"sem preço identificável (página dinâmica)", "não é página de produto"}  # só nesses o navegador pode achar o que o texto não achou
FRASES_COM_API = 5  # frases de busca por item quando há API de busca ativa (cada consulta gasta 1 crédito; a pesquisa para ao fechar 3 preços)
SERPER_ESTADO = {"ate": 0.0}  # depois de erro de chave/créditos o Serper fica de fora por um tempo (a busca segue pelos buscadores gratuitos)
SERPER_USO = {"n": 0}  # consultas ao Serper nesta execução do app


def chave_serper():
    """Chave do Serper nos Secrets (SERPER_API_KEY, no 1º nível ou dentro de uma seção) ou na variável de ambiente. Vazio se não houver."""
    chave = ""
    try:
        chave, _ = memoria_lojas._procurar(st.secrets, "SERPER_API_KEY")
    except Exception:
        chave = ""
    return str(chave or os.environ.get("SERPER_API_KEY", "")).strip().strip('"').strip()


def buscar_serper(query, chave, num_results=8, item=None):
    """Busca no Serper (resultados do Google, em JSON, mercado brasileiro). Não é scraping: é uma API com chave e cota própria, sem bloqueio por
    endereço. Preenche DIAG_BUSCA['Serper'] com 'ok ...' ou o motivo do erro. Só ficam resultados que citam o item; os com cara de venda vão na frente."""
    import requests as _rq

    try:
        resp = _rq.post(SERPER_URL, headers={"X-API-KEY": chave, "Content-Type": "application/json"},
                        json={"q": query, "gl": "br", "hl": "pt-br", "num": 10}, timeout=15)
    except Exception as erro:
        DIAG_BUSCA["Serper"] = f"erro {type(erro).__name__}"
        return []
    SERPER_USO["n"] += 1
    if resp.status_code != 200:
        texto = (resp.text or "")[:120].replace("\n", " ")
        if resp.status_code in (401, 403):
            DIAG_BUSCA["Serper"] = f"chave recusada (HTTP {resp.status_code})"
            SERPER_ESTADO["ate"] = time.time() + 600
        elif resp.status_code in (400, 402) and ("credit" in texto.lower() or "balance" in texto.lower()):
            DIAG_BUSCA["Serper"] = "sem créditos"
            SERPER_ESTADO["ate"] = time.time() + 3600
        elif resp.status_code == 429:
            DIAG_BUSCA["Serper"] = "limite de consultas por segundo (HTTP 429)"
            SERPER_ESTADO["ate"] = time.time() + 30
        else:
            DIAG_BUSCA["Serper"] = f"HTTP {resp.status_code} {texto}"
        return []
    try:
        organicos = resp.json().get("organic", []) or []
    except Exception:
        DIAG_BUSCA["Serper"] = "resposta ilegível"
        return []
    raizes = _raizes_do_item(item)
    comerciais, outros = [], []
    for r in organicos:
        link = r.get("link", "")
        if not link or not dominio_valido(link):
            continue
        texto = f"{r.get('title', '')} {r.get('snippet', '')} {link}"
        if not _cita_o_item(texto, raizes) or sinonimos.excluido(item or "", texto):
            continue
        (comerciais if SINAIS_VENDA.search(texto.lower()) else outros).append((link, texto))
    urls = _medida_primeiro(item, comerciais) + _medida_primeiro(item, outros)
    DIAG_BUSCA["Serper"] = f"ok, {len(organicos)} resultados, {len(urls)} com o item"
    return _dedup_urls(urls, num_results)


TAVILY_URL = "https://api.tavily.com/search"
TAVILY_ESTADO = {"ate": 0.0}
TAVILY_USO = {"n": 0}


def chave_tavily():
    """Chave do Tavily nos Secrets (TAVILY_API_KEY, no 1º nível ou dentro de uma seção) ou na variável de ambiente. Vazio se não houver."""
    chave = ""
    try:
        chave, _ = memoria_lojas._procurar(st.secrets, "TAVILY_API_KEY")
    except Exception:
        chave = ""
    return str(chave or os.environ.get("TAVILY_API_KEY", "")).strip().strip('"').strip()


def buscar_tavily(query, chave, num_results=8, item=None, dominios=None):
    """Busca no Tavily (API de busca para IA, em JSON). `dominios`: restringe a esses sites (usado nas lojas da memória). Preenche
    DIAG_BUSCA['Tavily'] com 'ok ...' ou o motivo do erro. Só ficam resultados que citam o item; os com cara de venda vão na frente."""
    import requests as _rq

    corpo = {"query": query, "search_depth": "basic", "max_results": 10, "topic": "general"}
    if dominios:
        corpo["include_domains"] = list(dominios)
    try:
        resp = _rq.post(TAVILY_URL, headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}, json=corpo, timeout=20)
    except Exception as erro:
        DIAG_BUSCA["Tavily"] = f"erro {type(erro).__name__}"
        return []
    TAVILY_USO["n"] += 1
    if resp.status_code != 200:
        texto = (resp.text or "")[:120].replace("\n", " ")
        if resp.status_code == 401:
            DIAG_BUSCA["Tavily"] = "chave recusada (HTTP 401)"
            TAVILY_ESTADO["ate"] = time.time() + 600
        elif resp.status_code in (402, 432, 433):
            DIAG_BUSCA["Tavily"] = f"sem créditos/limite do plano (HTTP {resp.status_code})"
            TAVILY_ESTADO["ate"] = time.time() + 3600
        elif resp.status_code == 429:
            DIAG_BUSCA["Tavily"] = "limite de consultas por minuto (HTTP 429)"
            TAVILY_ESTADO["ate"] = time.time() + 30
        else:
            DIAG_BUSCA["Tavily"] = f"HTTP {resp.status_code} {texto}"
        return []
    try:
        resultados = resp.json().get("results", []) or []
    except Exception:
        DIAG_BUSCA["Tavily"] = "resposta ilegível"
        return []
    raizes = _raizes_do_item(item)
    comerciais, outros = [], []
    for r in resultados:
        link = r.get("url", "")
        if not link or not dominio_valido(link):
            continue
        texto = f"{r.get('title', '')} {str(r.get('content', ''))[:500]} {link}"
        if not _cita_o_item(texto, raizes) or sinonimos.excluido(item or "", texto):
            continue
        (comerciais if SINAIS_VENDA.search(texto.lower()) else outros).append((link, texto))
    urls = _medida_primeiro(item, comerciais) + _medida_primeiro(item, outros)
    DIAG_BUSCA["Tavily"] = f"ok, {len(resultados)} resultados, {len(urls)} com o item"
    return _dedup_urls(urls, num_results)


def buscar_na_loja(session, item, site, headers, num_results=8):
    """Procura o item dentro de uma loja da memória ("item site:loja"): Tavily, depois Serper; sem API, uma tentativa pelo ddgs.
    Devolve só páginas da própria loja (até 3)."""
    def da_loja(url):
        return memoria_lojas.dominio(url) == site or memoria_lojas.dominio(url).endswith("." + site)

    # Com API (Serper/Tavily) não passa pelo DuckDuckGo; sem API, é uma tentativa só pelo ddgs (cada busca extra aumenta o risco de bloqueio)
    query = f"{item} site:{site}"
    urls = []
    chave_t, chave_s = chave_tavily(), chave_serper()
    if chave_t and time.time() >= TAVILY_ESTADO["ate"]:
        urls = [u for u in buscar_tavily(query, chave_t, num_results, item, dominios=[site]) if da_loja(u)]
    if not urls and chave_s and time.time() >= SERPER_ESTADO["ate"]:
        urls = [u for u in buscar_serper(query, chave_s, num_results, item) if da_loja(u)]
    if not urls and not chave_t and not chave_s and time.time() >= DDG_PROXIMA_TENTATIVA["ate"]:  # sem API: uma tentativa pelo ddgs
        urls = [u for u in buscar_ddgs_api(query, num_results, item) if da_loja(u)]
    return list(dict.fromkeys(urls))[:3]


def buscar_urls(session, query, headers, num_results=10, item=None, complementar=False):
    """APIs de busca com chave primeiro (Tavily, cuja cota grátis renova todo mês; depois Serper = Google, cujos créditos grátis não renovam); sem chave, sem créditos ou com erro, a busca gratuita (ddgs > Google) assume.
    Se uma API respondeu mas não havia lojas que citem o item, tenta a próxima; se nenhuma achou, devolve vazio sem insistir nos gratuitos."""
    provedores = [("Tavily", chave_tavily(), TAVILY_ESTADO, buscar_tavily, "Tavily"),
                  ("Serper", chave_serper(), SERPER_ESTADO, buscar_serper, "Serper (Google)")]
    falhas, vazios = [], []
    somados, rotulos = [], []  # `complementar`: item ainda sem os preços; junta o que TODAS as APIs devolvem (gasta 1 crédito de cada)
    for nome, chave, estado, funcao, rotulo in provedores:
        if not chave or time.time() < estado["ate"]:
            continue
        DIAG_BUSCA.clear()
        urls = funcao(query, chave, num_results, item)
        situacao = DIAG_BUSCA.get(nome, "")
        if urls:
            if not complementar:
                return urls, rotulo
            somados += urls
            rotulos.append(rotulo)
            continue
        (vazios if situacao.startswith("ok") else falhas).append(f"{nome}: {situacao}")
    if somados:
        return _dedup_urls(somados, num_results + 4), " + ".join(rotulos)
    if vazios:
        return [], "nenhum (" + "; ".join(vazios + falhas) + ")"
    urls, motor = _buscar_urls_gratis(session, query, headers, num_results, item)
    return urls, motor + (" — " + "; ".join(falhas) if falhas else "")


def _buscar_urls_gratis(session, query, headers, num_results=8, item=None):
    """Busca gratuita: DDGS API > Google (o DuckDuckGo HTML saiu: é o mesmo buscador do ddgs; o Bing saiu: não achava lojas). Se o DuckDuckGo falhar com sinal de bloqueio (erro, HTTP 202/403/429),
    ele descansa PAUSA_APOS_BLOQUEIO_DDG segundos antes de ser consultado de novo (insistir só prolonga o bloqueio); nesse intervalo a busca
    segue pelos outros. O motivo vai junto com o nome do buscador, para aparecer no log."""
    DIAG_BUSCA.clear()
    nota = ""
    if time.time() < DDG_PROXIMA_TENTATIVA["ate"]:
        nota = f"DuckDuckGo descansando por mais {DDG_PROXIMA_TENTATIVA['ate'] - time.time():.0f} s após bloqueio"
    else:
        # 1. Tentar DDGS API (mais confiável em ambientes de servidor)
        urls = buscar_ddgs_api(query, num_results, item)
        if urls:
            ddg_voltou()
            return urls, "DDGS API"
        # (o DuckDuckGo HTML não é mais consultado: é o mesmo buscador do ddgs, e duas visitas por frase reforçam a cara de robô)
        sinais = [v for k, v in DIAG_BUSCA.items() if k in ("DDGS", "DuckDuckGo HTML")]
        if str(DIAG_BUSCA.get("DDGS", "")).startswith("0 sites ("):
            DDG_VAZIOS_SEGUIDOS["n"] = 0  # o DuckDuckGo respondeu (só não havia loja entre os resultados): não é bloqueio
            nota = f"DuckDuckGo respondeu, mas sem lojas nesta frase ({DIAG_BUSCA['DDGS']})"
        elif any(str(v).startswith(("erro", "HTTP 202", "HTTP 403", "HTTP 429", "HTTP 5")) for v in sinais):
            pausa = descansar_ddg()
            nota = "DuckDuckGo sem resposta (" + "; ".join(f"{k}: {v}" for k, v in DIAG_BUSCA.items() if k in ("DDGS", "DuckDuckGo HTML")) + f"); descansa {pausa} s"
        else:
            DDG_VAZIOS_SEGUIDOS["n"] += 1
            if DDG_VAZIOS_SEGUIDOS["n"] >= 2:
                DDG_VAZIOS_SEGUIDOS["n"] = 0
                pausa = descansar_ddg()
                nota = f"DuckDuckGo respondeu vazio 2 vezes seguidas (provável bloqueio); descansa {pausa} s"
            else:
                nota = "DuckDuckGo sem resultados para esta frase"
    # 3. Google
    urls = buscar_google_requests(session, query, headers, num_results)
    if urls:
        return urls, f"Google — {nota}" if nota else "Google"
    outros = "; ".join(f"{k}: {v}" for k, v in DIAG_BUSCA.items() if k in ("Google",))
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


MOTIVO_REJEICAO = {"texto": ""}
# a página foi lida e com certeza não serve: abrir no navegador não muda o resultado
MOTIVOS_DEFINITIVOS = {"página não corresponde ao item", "página de busca/listagem sem o produto pedido", "a loja esconde o preço (pede CEP ou login)"}  # por que a última página foi rejeitada (aparece no log)


PREFETCH = {}  # url -> (status, texto, url final): páginas baixadas em paralelo antes da leitura (consumidas por scraping_requests)


def prefetch_paginas(urls, headers, max_workers=6, timeout=12):
    """Baixa várias páginas ao mesmo tempo (sites diferentes, uma requisição cada) e guarda em PREFETCH; a leitura/avaliação segue uma a uma.
    Troca N esperas de rede em fila por uma só (a mais lenta). Falha de rede aqui não é erro: a leitura normal tenta de novo."""
    import requests as _rq
    from concurrent.futures import ThreadPoolExecutor

    def baixar(u):
        try:
            sessao = _rq.Session()
            r = sessao.get(u, headers=headers, timeout=timeout, allow_redirects=True)
            return u, (r.status_code, r.text if r.status_code == 200 else "", str(getattr(r, "url", "") or u))
        except Exception:
            return u, None

    alvo = [u for u in dict.fromkeys(urls) if u not in PREFETCH]
    if len(alvo) < 2:
        return
    with ThreadPoolExecutor(max_workers=min(max_workers, len(alvo))) as pool:
        for u, resultado in pool.map(baixar, alvo):
            if resultado:
                PREFETCH[u] = resultado


def scraping_requests(session, url, headers, item_nome=None, html=None, _profundidade=0):
    """Acessa uma página via requests e extrai informações. Em página de busca/listagem, o preço do produto que é do item é confirmado
    abrindo a página desse produto (uma vez, _profundidade=1): o endereço e o print passam a ser os do anúncio, e não os da lista."""
    from bs4 import BeautifulSoup

    MOTIVO_REJEICAO["texto"] = ""
    try:
        if html is None:  # `html` já vem pronto quando a página foi lida pelo navegador
            pre = PREFETCH.pop(url, None)  # baixada em paralelo antes
            if pre is not None:
                status_pre, texto_pre, final_pre = pre
                if status_pre != 200:
                    MOTIVO_REJEICAO["texto"] = f"HTTP {status_pre}"
                    return None
                html = texto_pre
                url = final_pre or url
            else:
                resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
                if resp.status_code != 200:
                    MOTIVO_REJEICAO["texto"] = f"HTTP {resp.status_code}"
                    return None
                html = resp.text
                url = str(getattr(resp, "url", "") or url) or url  # endereço final (a busca pode redirecionar direto para o produto)
        titulo = extrair_titulo_pagina(html)

        # Verificar se é uma página de produto antes de gastar tempo extraindo preços
        if not _eh_pagina_produto(html, titulo):
            MOTIVO_REJEICAO["texto"] = "não é página de produto"
            return None

        # Verificar se o conteúdo é relevante para o item buscado
        if item_nome and not _conteudo_relevante(html, titulo, item_nome, url):
            MOTIVO_REJEICAO["texto"] = "página não corresponde ao item"
            MOTIVO_REJEICAO["titulo"] = titulo  # guardado para o sistema aprender o nome que as lojas usam
            return None

        # Medida/embalagem: título com outra medida da mesma grandeza (1 kg quando o item é 5 kg) é outro produto
        # Medida/embalagem: outra medida (1 kg quando o item é 5 kg) não descarta a página; o preço vale e o relatório avisa
        medida_confere = "sem_medida" if web_precos.eh_url_de_busca(url) else embalagem.confere(item_nome or "", titulo or "")
        nome_ofertado = titulo

        # Só loja brasileira vendendo em reais: precisa de 2 sinais (.br, moeda BRL, pt-BR, "R$"); preço em outra moeda é rejeitado
        nacional, motivo_nacional = web_precos.site_nacional(url, html)
        if not nacional:
            MOTIVO_REJEICAO["texto"] = motivo_nacional
            return None

        precos = extrair_precos_pagina(html)

        # Preço do produto anunciado: oferta em JSON-LD (sem parcelas/preço riscado) > metadados > mediana dos valores do texto
        principal = web_precos.preco_principal(html, extrair_precos_pagina, item_nome or "", url)
        if not principal:
            MOTIVO_REJEICAO["texto"] = web_precos.ULTIMO_MOTIVO["texto"] or "sem preço identificável (página dinâmica)"
            return None
        if principal.get("link") and _profundidade == 0 and principal["origem"].startswith("listagem"):
            produto = scraping_requests(session, principal["link"], headers, item_nome=item_nome, _profundidade=1)
            if produto:  # confirmado na página do próprio produto: endereço, preço e print do anúncio
                produto["origem_preco"] = f"{produto.get('origem_preco', '')} (produto aberto a partir da lista da loja)".strip()
                return produto
            if principal.get("nome"):
                medida_confere = embalagem.confere(item_nome or "", principal["nome"])
                nome_ofertado = principal["nome"]
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
            "medida_confere": medida_confere,
            "medida_ofertada": embalagem.descrever(nome_ofertado or "").replace("medida ", "").replace("embalagem ", "") if medida_confere == "diferente" else "",
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


def _conteudo_relevante(html, titulo, item_nome, url=""):
    """A página é do item pedido? Confere o NOME do produto (título, h1, og:title, nome no JSON-LD) com sinonimos.confere_nome:
    precisa do substantivo do item e da maioria das palavras ("papel toalha" não serve para "papel contact"; "caneta esferográfica"
    não serve para "caneta piloto"). Página de busca/listagem passa aqui e é decidida produto a produto em web_precos.preco_principal
    (o título dela só repete o que foi pesquisado)."""
    from bs4 import BeautifulSoup

    if not item_nome:
        return True
    if web_precos.eh_url_de_busca(url):
        return True
    soup = BeautifulSoup(html, "html.parser")
    nomes = [titulo] + [h.get_text(" ", strip=True) for h in soup.find_all("h1")[:3]]
    for meta in soup.find_all("meta"):
        if str(meta.get("property") or meta.get("name") or "").lower() in ("og:title", "twitter:title") and meta.get("content"):
            nomes.append(meta["content"])
    for marcador in soup.find_all("script", type="application/ld+json"):
        nomes += re.findall(r'"name"\s*:\s*"([^"]{3,200})"', marcador.string or marcador.get_text() or "")[:5]
    if any(sinonimos.confere_nome(item_nome, n) for n in nomes if n):
        return True
    return len(web_precos._cards_da_listagem(soup)) >= web_precos.MIN_CARDS_LISTAGEM  # listagem: decidida produto a produto


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


def executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text, max_fontes, usar_navegador=False, tempo_max_pagina_min=2, navegador_primeiro=False):
    """Executa o scraping. `usar_navegador`: liga o navegador. `navegador_primeiro`: as páginas são abertas nele antes da leitura por texto
    (senão, ele só é o reserva das páginas em que a leitura por texto não achou preço; o print dessas fica guardado; as demais ganham print pelo botão depois). Cada página tem `tempo_max_pagina_min` minutos: se travar, é abandonada, o navegador é
    reiniciado e a leitura por texto assume."""
    leitor = captura_pagina.LeitorNavegador(tempo_max_pagina_s=tempo_max_pagina_min * 60) if usar_navegador else None
    try:
        return _executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text, max_fontes, leitor, navegador_primeiro)
    finally:
        if leitor is not None:
            leitor.fechar()


def _executar_scraping(itens, usar_playwright, progress_bar, log_container, status_text, max_fontes, leitor, navegador_primeiro=False):
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
    sinonimos.carregar_aprendidos(memoria.setdefault("nomes", {}))  # nomes aprendidos com o uso (ensinados, sugeridos ou por exclusão)
    st.session_state["sugestoes_nomes"] = {}
    classificadas = memoria_lojas.completar_naturezas(memoria)  # lojas aprendidas antes da classificação por natureza
    if classificadas:
        log_msg(log_container, logs, f"🧭 {classificadas} loja(s) da memória classificadas por natureza a partir dos itens que já cotaram", "info")
    if not onde_memoria.startswith("GitHub"):
        log_msg(log_container, logs, "🧠 " + memoria_lojas.diagnostico_secrets(st.secrets if _tem_secrets() else {}), "warn")

    consultas_serper_antes = SERPER_USO["n"]
    consultas_tavily_antes = TAVILY_USO["n"]
    _apis_log = [n for n, c in (("Tavily", chave_tavily()), ("Serper (Google)", chave_serper())) if c]
    if _apis_log:
        log_msg(log_container, logs, "🔑 Busca por API ativa: " + " → ".join(_apis_log) + "; DuckDuckGo (ddgs) fica de reserva", "info")
    else:
        log_msg(log_container, logs, "🔑 Sem SERPER_API_KEY/TAVILY_API_KEY nos Secrets: a busca usa só o DuckDuckGo (gratuito, sujeito a bloqueio)", "warn")

    st.session_state["tempos_itens"] = {}
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
                log_msg(log_container, logs, f"⚠ O navegador abriu {extrair_dominio(url)} mas não achou preço ({MOTIVO_REJEICAO['texto'] or 'sem motivo'})", "warn")
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
            motivo = MOTIVO_REJEICAO["texto"]
            if motivo and not motivo.startswith(("HTTP 429", "HTTP 5", "HTTP 403")):
                break  # a página foi lida e não serve: repetir não muda nada (só erros passageiros de acesso merecem nova tentativa)
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
        texto_primeiro = navegador_ativo and (not navegador_primeiro or memoria_lojas.metodo_preferido(memoria, url) == "texto")
        if texto_primeiro:
            tentou["texto"] = True
            resultado_pagina = ler_por_texto(url, item_nome, leve=True)
            if resultado_pagina:
                return resultado_pagina, "texto", tentou
            if not vale_abrir_navegador():
                return None, "texto", tentou  # a página foi lida e não é do item (ou o item gastou o tempo/cota do navegador): economiza 10-15 s
        if navegador_ativo:
            ITEM["navegador"] += 1
            resultado_pagina, _, tentou["navegador"] = ler_com_navegador(url, item_nome)
            if resultado_pagina:
                return resultado_pagina, "navegador", tentou
        if not texto_primeiro:
            tentou["texto"] = True
            resultado_pagina = ler_por_texto(url, item_nome, leve=tentou["navegador"])  # navegador já tentou: texto leve; senão, completo
            if resultado_pagina:
                return resultado_pagina, "texto", tentou
        return None, "texto", tentou


    internas_tentadas = set()  # lojas cuja busca interna já foi tentada (por item)
    INTERNA = {"sem_o_item": False}  # a última busca interna leu a lista da loja e o item não estava lá
    ITEM = {"inicio": time.time(), "navegador": 0}  # relógio e navegador gasto no item atual

    def tempo_restante_item():
        return TEMPO_MAX_ITEM_S - (time.time() - ITEM["inicio"])

    def vale_abrir_navegador():
        """O navegador (10-15 s por página) só entra quando o texto falhou por motivo que ele resolve, sobra tempo e não passou da cota do item."""
        motivo = str(MOTIVO_REJEICAO["texto"])
        return ((motivo in MOTIVOS_PARA_NAVEGADOR or motivo.startswith(("HTTP 4", "HTTP 5")))
                and ITEM["navegador"] < NAVEGADOR_MAX_POR_ITEM and tempo_restante_item() > 25)

    def tentar_busca_interna(url_ou_site, item_nome):
        """Procura o item na busca do próprio site da loja (sem buscador) e lê a página de resultados (texto; navegador se o texto falhar).
        Devolve (resultado, url, método) ou None."""
        INTERNA["sem_o_item"] = False
        site = memoria_lojas.dominio(url_ou_site)
        if not site or (site, item_nome) in internas_tentadas or memoria_lojas.busca_interna_descartada(memoria, site):
            return None
        internas_tentadas.add((site, item_nome))
        conhecido = memoria_lojas.padrao_busca(memoria, site)
        url_busca, padrao = busca_interna.descobrir(session, site, embalagem.termo_busca(sinonimos.termo_busca(item_nome)), headers, conhecido)
        if not url_busca:
            memoria_lojas.registrar_sem_busca(memoria, site)
            log_msg(log_container, logs, f"🔎 {site}: não achei a busca interna do site", "info")
            return None
        log_msg(log_container, logs, f"🔎 Buscando '{item_nome}' dentro do site {site}", "info")
        time.sleep(gerar_delay(0.3, 0.8) if (leitor is not None and leitor.disponivel and navegador_primeiro) else gerar_delay(1.5, 3.0))
        resultado_interno, metodo_interno, _ = ler_pagina(url_busca, item_nome)
        INTERNA["sem_o_item"] = not resultado_interno and MOTIVO_REJEICAO["texto"] in MOTIVOS_DEFINITIVOS
        if resultado_interno:
            memoria_lojas.registrar_busca_interna(memoria, site, padrao)  # o acerto em si é registrado por quem chama
            return resultado_interno, url_busca, metodo_interno
        log_msg(log_container, logs, f"✗ A busca interna de {site} não deu preço", "warn")
        return None

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
            ITEM["inicio"], ITEM["navegador"] = time.time(), 0
            consultas_item_antes = SERPER_USO["n"] + TAVILY_USO["n"]
            aviso_tempo = {"dado": False}

            # Selecionar variantes de busca aleatoriamente (usar mais variantes para maximizar cobertura)
            # Frases na ordem aprendida pela memória (as que mais rendem preços primeiro; de vez em quando a pior é testada); o laço para ao atingir as fontes
            variantes, explicacao_frases = memoria_lojas.ordenar_frases(memoria, VARIANTES_BUSCA + VARIANTES_RESERVA)
            serper_ativo = (bool(chave_serper()) and time.time() >= SERPER_ESTADO["ate"]) or (bool(chave_tavily()) and time.time() >= TAVILY_ESTADO["ate"])  # há API de busca em uso
            if serper_ativo:
                variantes = variantes[:FRASES_COM_API]  # a pesquisa para ao fechar os preços: só os itens difíceis gastam as 5 frases
            log_msg(log_container, logs, f"🧠 Frases de busca: {explicacao_frases}", "info")
            dominios_falhos = set()  # site que falhou neste item não é tentado de novo nas outras buscas do mesmo item

            # 1º: lojas da memória que já deram preço para itens parecidos (cada uma uma vez só)
            # 1º: lojas que deram preço para itens parecidos; depois, as melhores da mesma natureza (ramo) do item
            termo_item = embalagem.termo_busca(sinonimos.termo_busca(item))  # nome de mercado + medida junta, sem "UN"
            if sinonimos.entrada(item):
                log_msg(log_container, logs, f"🔤 Nome de mercado: '{item}' é buscado como '{termo_item}'; anúncios de outro produto parecido são recusados", "info")
            descricao_medida = embalagem.descrever(item)
            if descricao_medida:
                log_msg(log_container, logs, f"📦 Unidade de fornecimento: {descricao_medida} — a mesma medida tem preferência; outra medida só entra se faltar preço, e o relatório avisa; busca: '{termo_item}'", "info")
            natureza_item = naturezas.classificar(embalagem.base(item))
            log_msg(log_container, logs, f"🧭 Natureza do item: {natureza_item}" if natureza_item
                    else "🧭 Natureza do item: não reconhecida (usa só as lojas de itens parecidos e a busca)", "info")
            origens_item = {o: {"tentativas": 0, "precos": 0, "segundos": 0.0} for o in desempenho.ORIGENS}  # o que cada origem rendeu neste item
            frase_ok = ""  # 1ª frase de busca que rendeu preço
            # quantas lojas de cada origem tentar: o histórico de desempenho da natureza do item aumenta as que rendem e reduz as que só gastam tempo
            limite_parecidas, aviso_parecidas = desempenho.limite_lojas(memoria, natureza_item, "parecida", memoria_lojas.MAX_LOJAS_POR_ITEM)
            limite_natureza, aviso_natureza = desempenho.limite_lojas(memoria, natureza_item, "natureza", memoria_lojas.MAX_LOJAS_POR_NATUREZA)
            for aviso in (aviso_parecidas, aviso_natureza):
                if aviso:
                    log_msg(log_container, logs, f"📈 Desempenho em '{natureza_item or desempenho.SEM_NATUREZA}': {aviso}", "info")
            lojas_parecidas = memoria_lojas.lojas_para_item(memoria, item, limite_parecidas)
            fila_memoria = [(site, parecido, "") for site, parecido in lojas_parecidas]
            fila_memoria += [(site, "", natureza_item) for site, _ in
                             memoria_lojas.lojas_por_natureza(memoria, natureza_item, excluir=[site for site, _ in lojas_parecidas], limite=limite_natureza)]
            inicio_memoria = time.time()
            for site_memoria, item_parecido, natureza_loja in fila_memoria:
                if len(atualizar_estado_orcamentos(candidatos_item, max_fontes)["validos"]) >= max_fontes:
                    break
                if time.time() - inicio_memoria > TEMPO_MAX_LOJAS_MEMORIA_S or tempo_restante_item() < 60:
                    log_msg(log_container, logs, f"⏱ Lojas da memória: limite de {TEMPO_MAX_LOJAS_MEMORIA_S} s para este item; seguindo para a busca", "info")
                    break
                if item_parecido:
                    log_msg(log_container, logs, f"🧠 Loja da memória: {site_memoria} (já deu preço para '{item_parecido}')", "info")
                else:
                    log_msg(log_container, logs, f"🧭 Loja boa em {natureza_loja}: {site_memoria} (tentando a busca do próprio site, sem gastar consulta de API)", "info")
                navegador_ligado = (leitor is not None and leitor.disponivel and navegador_primeiro) or serper_ativo
                inicio_loja = time.time()
                time.sleep(gerar_delay(0.2, 0.5) if navegador_ligado else gerar_delay(1.5, 3.0))
                achado = None  # (resultado, url, método)
                # 1) busca do próprio site da loja (sem buscador); 2) a página que já deu preço antes; 3) busca "site:" pela API de busca
                # (lojas vindas só da natureza não passam pelo passo 3: para não gastar crédito de API com loja que talvez nem venda o item)
                interna = tentar_busca_interna(site_memoria, item)
                if interna:
                    achado = interna
                loja_sem_o_item = INTERNA["sem_o_item"]  # a lista da própria loja não tem o item: não insiste nela
                # a página guardada só serve se for do MESMO item (a de 'caneta piloto azul' não é a de 'caneta piloto preta')
                mesmo_item = sinonimos.normalizar(item_parecido).strip() == sinonimos.normalizar(item).strip()
                guardada = memoria_lojas.pagina_guardada(memoria, site_memoria, item_parecido) if mesmo_item else ""
                if not achado and guardada and not loja_sem_o_item:
                    time.sleep(gerar_delay(0.2, 0.5) if navegador_ligado else gerar_delay(1.5, 3.5))
                    r_guardada, m_guardada, _ = ler_pagina(guardada, item)
                    if r_guardada:
                        achado = (r_guardada, guardada, m_guardada)
                if not achado and not natureza_loja and not loja_sem_o_item:
                    for url in buscar_na_loja(session, item, site_memoria, headers):
                        if url == guardada:
                            continue
                        time.sleep(gerar_delay(0.2, 0.5) if navegador_ligado else gerar_delay(1.5, 3.5))
                        r_url, m_url, _ = ler_pagina(url, item)
                        if r_url:
                            achado = (r_url, url, m_url)
                            break
                if achado:
                    resultado, url, metodo_ok = achado
                    contador_item += 1
                    resultado["resultado_id"] = f"{item_slug}_{contador_item}_{abs(hash(url)) % 10000}"
                    resultado["item"] = item
                    resultado["data_coleta"] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    candidatos_item.append(resultado)
                    dominios_usados.add(extrair_dominio(url))
                    memoria_lojas.registrar_acerto(memoria, url, item, metodo_ok)
                    log_msg(log_container, logs, f"💰 Orçamento da memória — {formatar_moeda_br(resultado['preco'])} em {extrair_dominio(url)}", "orcamento")
                else:
                    log_msg(log_container, logs, f"✗ {site_memoria} não teve preço para '{item}' desta vez", "warn")
                origem_loja = origens_item["parecida" if item_parecido else "natureza"]
                origem_loja["tentativas"] += 1
                origem_loja["precos"] += 1 if achado else 0
                origem_loja["segundos"] += time.time() - inicio_loja
                if achado or loja_sem_o_item:  # só fecha a loja se ela foi consultada e confirmou que não tem o item; senão a busca ainda pode achar a página dela
                    dominios_falhos.update({site_memoria, "www." + site_memoria})

            inicio_busca = time.time()
            for numero_frase, variante in enumerate(variantes):
                estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)
                if len(estado_item["validos"]) >= max_fontes:
                    log_msg(log_container, logs, f"✓ {max_fontes} orçamentos válidos encontrados para '{item}'. Avançando.", "success")
                    break
                if tempo_restante_item() <= 0:
                    log_msg(log_container, logs, f"⏱ '{item}': passou de {TEMPO_MAX_ITEM_S} s; seguindo para o próximo item com o que foi achado", "warn")
                    break

                query = variante.format(item=termo_item)
                log_msg(log_container, logs, f"🔍 Buscando: \"{query}\"", "info")

                # Delay antes da busca
                delay = gerar_delay(0.3, 0.8) if serper_ativo else gerar_delay(2.0, 5.0)  # API com chave não precisa de pausa "humana"
                if not serper_ativo:
                    log_msg(log_container, logs, f"⏳ Aguardando {delay:.1f}s...", "info")
                time.sleep(delay)

                # Buscar URLs (Serper > Tavily > ddgs > Google)
                # a partir da 2ª frase, item ainda sem os preços: pede às duas APIs (Tavily e Serper) e junta os sites
                urls, engine = buscar_urls(session, query, headers, item=item, complementar=numero_frase >= 1)

                if not urls:
                    log_msg(log_container, logs, f"⚠ Nenhum resultado encontrado para \"{query}\" — {engine}", "warn")
                    # buscador bloqueado/com erro não diz nada sobre a frase: só conta quando houve resposta
                    if "erro" not in engine and "HTTP" not in engine:
                        memoria_lojas.registrar_busca(memoria, variante, 0)
                    continue

                log_msg(log_container, logs, f"📋 {len(urls)} resultados encontrados via {engine}", "info")
                acertos_variante = 0  # preços válidos que esta frase rendeu

                # lê várias páginas ao mesmo tempo: a leitura/avaliação segue uma a uma, mas a espera de rede é uma só
                lote_pre = [u for u in urls if extrair_dominio(u) not in dominios_usados and extrair_dominio(u) not in dominios_falhos][:6]
                if len(lote_pre) >= 2 and tempo_restante_item() > 10:
                    prefetch_paginas(lote_pre, headers)

                for url in urls:
                    estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)
                    if len(estado_item["validos"]) >= max_fontes:
                        break
                    if tempo_restante_item() <= 0:
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
                    origens_item["busca"]["tentativas"] += 1

                    # Delay entre acessos a sites
                    # (com o navegador ativo a própria abertura da página já espaça os acessos: pausa curta)
                    if url in PREFETCH or serper_ativo or (leitor is not None and leitor.disponivel and navegador_primeiro):
                        delay = gerar_delay(0.1, 0.3)  # página já baixada (ou API de busca): cada site é visitado uma vez, sem espera "humana"
                    else:
                        delay = gerar_delay(2.5, 6.0)
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
                        # página sem preço de loja que a memória conhece: tenta a busca do próprio site (só nessas, para não deixar a pesquisa lenta)
                        if not resultado and not str(MOTIVO_REJEICAO["texto"]).startswith("HTTP ") and memoria_lojas.dominio(url) in memoria["lojas"]:
                            interna_site = tentar_busca_interna(url, item)
                            if interna_site:
                                resultado, url, metodo_ok = interna_site

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
                        origens_item["busca"]["precos"] += 1
                        frase_ok = frase_ok or variante
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
                                f"💰 Orçamento [{len(estado_item['validos'])}/{max_fontes}] — {formatar_moeda_br(resultado['preco'])} em {dominio}"
                                + (" (medida confere)" if resultado.get("medida_confere") == "igual" else "")
                                + (f" (embalagem diferente: {resultado.get('medida_ofertada') or 'outra medida'})" if resultado.get("medida_confere") == "diferente" else ""),
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
                        if MOTIVO_REJEICAO["texto"] == "página não corresponde ao item" and MOTIVO_REJEICAO.get("titulo"):
                            sinonimos.registrar_recusado(memoria["nomes"], item, MOTIVO_REJEICAO["titulo"])  # base para sugerir o nome das lojas
                            memoria["_mudou"] = True
                        dominios_falhos.add(dominio)
                        if MOTIVO_REJEICAO["texto"] not in ("página não corresponde ao item", "página de busca/listagem sem o produto pedido") \
                                and not MOTIVO_REJEICAO["texto"].startswith("embalagem"):  # a loja pode servir para outro item
                            if tentou_navegador:
                                memoria_lojas.registrar_falha(memoria, url, "navegador")
                            if tentou_texto:
                                memoria_lojas.registrar_falha(memoria, url, "texto")

                memoria_lojas.registrar_busca(memoria, variante, acertos_variante)

            origens_item["busca"]["segundos"] = time.time() - inicio_busca
            estado_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)
            if len(estado_item["validos"]) < max_fontes:
                log_msg(log_container, logs, f"⚠ Apenas {len(estado_item['validos'])} orçamento(s) válido(s) encontrado(s) para '{item}'", "warn")
                sugestao = sinonimos.sugerir(memoria["nomes"], item)
                if sugestao:
                    st.session_state["sugestoes_nomes"][item] = sugestao
                    log_msg(log_container, logs, f"💡 As lojas parecem chamar '{item}' de '{sugestao['busca']}'. Confirme em \"Ensinar nomes ao sistema\", abaixo dos resultados", "info")

            orcamentos_item = atualizar_estado_orcamentos(candidatos_item, max_fontes)["validos"]
            resultados.extend(orcamentos_item)

            # tempo do item: fica na tela e alimenta o aprendizado de desempenho
            st.session_state.setdefault("tempos_itens", {})[item] = {
                "segundos": round(time.time() - ITEM["inicio"], 1), "precos": len(orcamentos_item), "navegador": ITEM["navegador"],
                "consultas_api": (SERPER_USO["n"] + TAVILY_USO["n"]) - consultas_item_antes}
            desempenho.registrar_item(memoria, item, natureza_item, time.time() - ITEM["inicio"], orcamentos_item, max_fontes, origens_item,
                                      consultas_api=(SERPER_USO["n"] + TAVILY_USO["n"]) - consultas_item_antes, navegador=ITEM["navegador"], frase=frase_ok)
            PREFETCH.clear()

            # Delay entre itens diferentes (com API de busca não há o que "esfriar": o próximo item usa outros sites)
            if idx < total_itens - 1:
                delay = gerar_delay(0.5, 1.5) if serper_ativo else gerar_delay(4.0, 8.0)
                if not serper_ativo:
                    log_msg(log_container, logs, f"⏳ Intervalo entre itens: {delay:.1f}s", "info")
                time.sleep(delay)
    finally:  # grava o que a pesquisa aprendeu mesmo que ela seja interrompida por um erro
        try:
            for _nome_api, _uso, _antes in (("serper", SERPER_USO["n"], consultas_serper_antes), ("tavily", TAVILY_USO["n"], consultas_tavily_antes)):
                if _uso - _antes:
                    _total_mes = memoria_lojas.registrar_uso_api(memoria, _nome_api, _uso - _antes)
                    log_msg(log_container, logs, f"🔑 {_nome_api.capitalize()}: {_uso - _antes} consulta(s) nesta pesquisa; {_total_mes} neste mês (confira o saldo no painel do serviço)", "info")
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

with st.expander("🧠 Memória de lojas (aprende com o uso)", expanded=False):
    st.caption("A cada pesquisa o sistema guarda as lojas que deram preço e os itens que cada uma cotou; nas próximas, tenta primeiro "
               f"essas lojas para itens parecidos. Sites que falharam {memoria_lojas.FALHAS_PARA_PULAR} vezes sem nunca dar preço são pulados.")
    if st.button("Ver o que o sistema já aprendeu", key="ver_memoria_lojas"):
        memoria_vista, onde_vista = memoria_lojas.carregar(st.secrets if _tem_secrets() else {})
        memoria_lojas.completar_naturezas(memoria_vista)  # só para mostrar; é gravado na próxima pesquisa
        st.caption(f"Onde está guardada: {onde_vista}")
        if not onde_vista.startswith("GitHub"):
            st.warning(memoria_lojas.diagnostico_secrets(st.secrets if _tem_secrets() else {}))
        if memoria_vista["lojas"]:
            st.dataframe(pd.DataFrame([{"Loja": site, "Preços encontrados": l["acertos"],
                                        "Naturezas": ", ".join(f"{n} ({c})" for n, c in sorted(l.get("naturezas", {}).items(), key=lambda x: -x[1])), "Pelo navegador": l.get("metodos", {}).get("navegador", 0),
                                        "Por texto": l.get("metodos", {}).get("texto", 0), "Último": l["ultimo"], "Itens cotados": ", ".join(l["itens"][:15])}
                                       for site, l in sorted(memoria_vista["lojas"].items(), key=lambda x: -x[1]["acertos"])]),
                         hide_index=True, use_container_width=True)
        else:
            st.info("Nenhuma loja aprendida ainda: a memória se forma com as próximas pesquisas.")
        nomes_vistos = {c: n for c, n in memoria_vista.get("nomes", {}).items() if n.get("busca") or n.get("excluir") or n.get("aceitar")}
        if nomes_vistos:
            st.markdown("**Nomes aprendidos** (como o item é buscado e que palavras recusam o anúncio)")
            st.dataframe(pd.DataFrame([{"Item (como é pedido)": c, "Buscado como": n.get("busca", ""),
                                        "Recusa anúncios com": ", ".join(sorted(n.get("excluir", {}), key=lambda t: -n["excluir"][t])[:10]),
                                        "Origem": n.get("origem", "") or "exclusões"} for c, n in sorted(nomes_vistos.items())]),
                         hide_index=True, use_container_width=True)
        resumo_nat = memoria_lojas.resumo_naturezas(memoria_vista)
        if resumo_nat:
            st.markdown("**Lojas por natureza do item** (para um item novo, as melhores lojas da natureza dele são tentadas pela busca do próprio site)")
            st.dataframe(pd.DataFrame([{"Natureza": nat, "Lojas (itens cotados dessa natureza)": ", ".join(f"{site} ({n})" for site, n in lojas)}
                                       for nat, lojas in resumo_nat.items()]), hide_index=True, use_container_width=True)
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
        resumo_des = desempenho.resumo_geral(memoria_vista)
        if resumo_des["total_registrado"]:
            st.markdown(f"**📈 O que está funcionando** (últimas {resumo_des['geral']['itens']} pesquisas de item; o sistema usa isso para decidir quantas lojas tentar de cada origem)")
            g = resumo_des["geral"]
            c1, c2, c3 = st.columns(3)
            ant, dep = resumo_des["antes"], resumo_des["depois"]

            def _delta(chave):
                if not ant or not dep or ant.get(chave) is None or dep.get(chave) is None:
                    return None
                return f"{dep[chave] - ant[chave]:+.1f} vs. metade anterior"
            c1.metric("Tempo médio por item", f"{g['tempo_medio_s']} s", _delta("tempo_medio_s"), delta_color="inverse")
            c2.metric("Itens com todos os preços", f"{g['pct_completos']}%", _delta("pct_completos"))
            c3.metric("Anúncios certos", f"{g['pct_certos']}%" if g["pct_certos"] is not None else "-", _delta("pct_certos"))
            st.caption("Anúncios certos = nome confere com o item e a medida não é diferente; os que você aponta como errados em \"Ensinar nomes\" corrigem esse número.")
            st.dataframe(pd.DataFrame(desempenho.tabela_naturezas(memoria_vista)), hide_index=True, use_container_width=True)
        else:
            st.info("O quadro de desempenho se forma com as próximas pesquisas (tempo, preços e acertividade de cada item).")

# Formulário de entrada
st.markdown("### 📝 Itens para Pesquisa")

col1, col2 = st.columns([3, 1])

with col1:
    itens_input = st.text_area(
        "Informe os itens (um por linha):",
        height=150,
        placeholder="Exemplo:\nLâmpada led bulbo 9W E27 branca\nCaneta piloto azul\nEnvelope pardo 24x34 caixa c/ 250\nDetergente 500ml",
        help="Digite os nomes dos materiais que deseja pesquisar, um por linha.",
    )
    st.caption("Dica: quanto mais específico, mais certo o preço. Inclua tipo, potência/medida e embalagem (ex.: \"lâmpada led bulbo 9W E27\", "
               "\"envelope pardo 24x34 caixa c/ 250\"), sem marca. Nomes do dia a dia como \"caneta piloto\", \"papel contact\", \"durex\" e "
               "\"post-it\" são traduzidos para o nome usado pelas lojas.")

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
        "Usar o navegador como reserva (Playwright)",
        value=navegador_ok,
        disabled=not navegador_ok,
        help="Navegador do servidor, que carrega o JavaScript e fecha popups. Serve de reserva quando a leitura por texto não acha o preço "
             "(e guarda o print dessas páginas). Sem ele, só há leitura por texto.",
    )
    navegador_primeiro = False  # modo fixo: leitura por texto primeiro; o navegador só entra nas páginas em que o texto não achou preço
    tempo_max_pagina = 2
    if navegador_ok:
        if usar_navegador:
            tempo_max_pagina = st.number_input("Tempo máx. por página no navegador (min)", min_value=1, max_value=10, value=2,
                                               help="Se uma página travar, o navegador a abandona depois desse tempo, é reiniciado e a leitura por texto tenta no lugar.")
    else:
        st.caption(f"Navegador indisponível (leitura simples por texto): {navegador_motivo}")
    _apis = [n for n, c in (("Tavily", chave_tavily()), ("Serper (Google)", chave_serper())) if c]
    if _apis:
        st.caption("🔑 Busca por API ativa: " + " → ".join(_apis) + ". DuckDuckGo (ddgs) fica de reserva.")
    else:
        st.caption("🔑 Sem chave de API de busca: usa só o DuckDuckGo (gratuito, sujeito a bloqueio). Ponha SERPER_API_KEY e/ou TAVILY_API_KEY nos Secrets do app.")
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
            navegador_primeiro=navegador_primeiro,
        )

        # Armazenar resultados no session_state
        st.session_state["scraping_resultados"] = resultados
        st.session_state["scraping_itens"] = itens
        st.session_state["scraping_excluir_ids"] = []


# ===================== EXIBIÇÃO DE RESULTADOS =====================

def _aplicar_nos_nomes(acao, depois=None):
    """Carrega a memória, aplica a ação nos nomes aprendidos, grava (GitHub) e já passa a valer nesta sessão.
    `depois`, se dado, recebe a memória inteira (para registrar outras coisas na mesma gravação)."""
    segredos = st.secrets if _tem_secrets() else {}
    memoria_nomes, _ = memoria_lojas.carregar(segredos)
    retorno = acao(memoria_nomes.setdefault("nomes", {}))
    if depois:
        depois(memoria_nomes)
    memoria_nomes["_mudou"] = True
    mensagem = memoria_lojas.salvar(memoria_nomes, segredos)
    sinonimos.carregar_aprendidos(memoria_nomes["nomes"])
    return retorno, mensagem


def secao_ensinar_nomes(resultados_brutos=None, opcoes_exclusao=None, labels_exclusao=None):
    """Área "Ensinar nomes ao sistema": sugestões automáticas, anúncios que não são o item (com resultados) e ensino direto."""
    sugestoes_nomes = st.session_state.get("sugestoes_nomes", {})
    with st.expander("🔤 Ensinar nomes ao sistema (aprende com o uso)", expanded=bool(sugestoes_nomes)):
        st.caption("O que se ensina aqui vale nas próximas pesquisas e fica na memória do GitHub. O sistema também aprende sozinho: quando muitos "
                   "anúncios são recusados por terem outro nome, ele sugere o nome que as lojas usam.")
        if st.checkbox(f"Ver o banco de nomes populares que o sistema já conhece ({sum(len(r['nomes']) for r in sinonimos.SINONIMOS)} nomes)",
                       key="ver_banco_nomes"):
            st.dataframe(pd.DataFrame([{"Como é pedido": ", ".join(r["nomes"]), "Buscado nas lojas como": r["busca"],
                                        "Recusa anúncios com": ", ".join(r["excluir"][:8])} for r in sinonimos.SINONIMOS]),
                         hide_index=True, use_container_width=True, height=320)
        for item_sugerido, sugestao in list(sugestoes_nomes.items()):
            exemplos = "; ".join(sugestao.get("exemplos", [])[:2])
            st.markdown(f"💡 **{item_sugerido}**: as lojas parecem chamar esse item de **\"{sugestao['busca']}\"** (ex.: {exemplos}). É o mesmo produto?")
            sim, nao = st.columns(2)
            if sim.button("Sim, é o mesmo: ensinar", key=f"sugestao_sim_{item_sugerido}"):
                chave, mensagem = _aplicar_nos_nomes(lambda nomes: sinonimos.ensinar(nomes, sinonimos.chave_aprendizado(item_sugerido),
                                                                                      sugestao["busca"], origem="sugestão aceita"))
                sugestoes_nomes.pop(item_sugerido, None)
                st.success(f"Aprendido: '{chave}' será buscado como '{sugestao['busca']}'. {mensagem}")
            if nao.button("Não é o mesmo produto", key=f"sugestao_nao_{item_sugerido}"):
                sugestoes_nomes.pop(item_sugerido, None)
                st.rerun()

        if resultados_brutos:
            errados = st.multiselect("Anúncios que NÃO são o item pedido (o sistema aprende a recusar anúncios assim):", options=opcoes_exclusao,
                                     format_func=lambda resultado_id: labels_exclusao.get(resultado_id, resultado_id), key="anuncios_errados")
            if st.button("🧠 Ensinar: esses anúncios não são o item", disabled=not errados):
                por_id = {r["resultado_id"]: r for r in resultados_brutos}
                por_item = {}
                for resultado_id in errados:
                    por_item.setdefault(por_id[resultado_id].get("item", ""), []).append(por_id[resultado_id].get("titulo", ""))
                mantidos = {it: [r.get("titulo", "") for r in resultados_brutos if r.get("item") == it and r["resultado_id"] not in errados] for it in por_item}
                aprendidas, mensagem = _aplicar_nos_nomes(lambda nomes: {it: sinonimos.aprender_exclusoes(nomes, it, nomes_exc, mantidos[it])
                                                                         for it, nomes_exc in por_item.items()},
                                                    depois=lambda memoria_inteira: [desempenho.registrar_revisao(memoria_inteira, it, len(nomes_exc))
                                                                                    for it, nomes_exc in por_item.items()])
                st.session_state["scraping_excluir_ids"] = list(dict.fromkeys(st.session_state.get("scraping_excluir_ids", []) + errados))
                texto = "; ".join(f"{it}: recusar anúncios com {', '.join(p) or '(nada novo)'}" for it, p in aprendidas.items())
                st.success(f"Aprendido — {texto}. Esses anúncios também saíram da composição. {mensagem}")

        with st.form("ensinar_nome_manual", clear_on_submit=True):
            st.markdown("**Ensinar um nome** (ex.: na repartição \"caneta piloto\" → nas lojas \"marcador para quadro branco\")")
            col_rep, col_loja = st.columns(2)
            nome_reparticao = col_rep.text_input("Como é pedido aqui")
            nome_lojas = col_loja.text_input("Como as lojas anunciam")
            recusar = st.text_input("Recusar anúncios que tenham (separe por vírgula)", placeholder="esferográfica, gel")
            if st.form_submit_button("Ensinar") and nome_reparticao.strip():
                chave, mensagem = _aplicar_nos_nomes(lambda nomes: sinonimos.ensinar(nomes, nome_reparticao, nome_lojas,
                                                                                      [t for t in recusar.split(",") if t.strip()]))
                st.success(f"Aprendido para '{chave}'. {mensagem}")
        with st.form("esquecer_nome", clear_on_submit=True):
            esquecer = st.text_input("Esquecer o que foi aprendido para (ex.: caneta piloto)")
            if st.form_submit_button("Esquecer") and esquecer.strip():
                chave_esq = sinonimos.chave_aprendizado(esquecer)
                _, mensagem = _aplicar_nos_nomes(lambda nomes: [sinonimos.esquecer(nomes, c) for c in list(nomes)
                                                                if c == sinonimos.normalizar(esquecer).strip() or c == chave_esq])
                st.success(f"Esquecido. {mensagem}")


if st.session_state.get("scraping_itens") and not st.session_state.get("scraping_resultados"):
    secao_ensinar_nomes()  # pesquisa sem nenhum preço: é justamente quando as sugestões de nome mais ajudam

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

    secao_ensinar_nomes(resultados_brutos, opcoes_exclusao, labels_exclusao)

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
            info_relatorio = {"max_precos": precos_por_item, "prints": {u: v for u, v in prints.items() if v.get("imagem")}, "motores": " e ".join([n for n, c in (("Tavily", chave_tavily()), ("Serper (Google)", chave_serper())) if c] + ["DuckDuckGo"]),
                              "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M")}
            st.caption("Mesmas regras da Cotação Rápida: sem outliers, preços a ±30% da média, mapa comparativo na 1ª página, "
                       "endereço e data/hora do acesso de cada preço.")
            st.dataframe(relatorio_web.tabela_mapa_web(analise, precos_por_item), use_container_width=True, hide_index=True)
            baixas = [(r["descricao"], p) for r in analise for p in r["precos"] if p.get("confianca") == "baixa"]
            if baixas:
                lista_baixas = "\n".join(f"- **{desc}** — [{p.get('dominio') or p.get('url')}]({p.get('url')}) — {formatar_moeda_br(p['preco'])}" for desc, p in baixas)
                st.warning(f"{len(baixas)} preço(s) do mapa vieram da leitura do texto da página (confiança baixa): confira o anúncio antes de usar.\n\n{lista_baixas}")
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
                        inicio_prints = time.time()
                        estado_prints = {"ok": 0, "falha": 0, "linhas": []}
                        st.caption("Cada página leva de 5 a 30 segundos. Não feche nem recarregue a aba até terminar.")
                        barra = st.progress(0, text="Abrindo o navegador do servidor… (pode levar alguns segundos)")
                        detalhe_prints = st.empty()

                        def andamento(feitas, total, url, resultado=None):
                            """Atualiza a barra: antes de cada página (url) e depois dela (resultado com o print ou o erro)."""
                            if resultado is not None:
                                nome = extrair_dominio(url)
                                if resultado.get("imagem"):
                                    estado_prints["ok"] += 1
                                    estado_prints["linhas"].append(f"✅ {nome}")
                                else:
                                    estado_prints["falha"] += 1
                                    estado_prints["linhas"].append(f"⚠️ {nome} — {resultado.get('erro', 'erro')}")
                                situacao = f"Página {feitas} de {total} pronta"
                            elif url:
                                situacao = f"Capturando {feitas + 1} de {total}: {extrair_dominio(url)}"
                            else:
                                situacao = f"Concluído: {feitas} de {total}"
                            percentual = int(100 * feitas / max(total, 1))
                            barra.progress(min(feitas / max(total, 1), 1.0), text=f"{situacao} · {percentual}% · {int(time.time() - inicio_prints)} s")
                            detalhe_prints.markdown(f"**{estado_prints['ok']}** com print · **{estado_prints['falha']}** com erro\n\n" + "\n\n".join(estado_prints["linhas"][-6:]))

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
