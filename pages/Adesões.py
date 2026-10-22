import asyncio
import base64
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt, timedelta as td
from typing import Dict, List, Optional, Tuple

import aiohttp
import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

# ── Caminhos dos dados do Projeto Adesões ──────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # catmat_busca.py (raiz do projeto)
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('catmat_busca', 'servicos_publicos', 'modelos_processo', 'vantajosidade')  # evita módulo antigo em memória após deploy
from servicos_publicos import consultar_sicaf, http_get_json, texto_sicaf  # noqa: E402
from catmat_busca import (  # noqa: E402
    CATMAT_PATH,
    CATSERV_PATH,
    atualizado_em,
    buscar_familias,
    buscar_servicos,
    carregar_catalogo,
    carregar_indice_catmat,
)

# ── Constantes da API ──────────────────────────────────────────────────────
API_URL = "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem"
API_URL_UNIDADES = "https://dadosabertos.compras.gov.br/modulo-arp/3_consultarUnidadesItem"
API_URL_ADESOES = "https://dadosabertos.compras.gov.br/modulo-arp/5_consultarAdesoesItem"
MAX_CONCURRENCY = 4
DATE_RANGE_DAYS = 360
PAGE_SIZE = {"Material": 100, "Serviço": 100}
API_CONNECT_TIMEOUT_SECONDS = 15
API_SEARCH_READ_TIMEOUT_SECONDS = 90
API_DETAIL_READ_TIMEOUT_SECONDS = 60
API_SEARCH_RETRIES = 3
API_DETAIL_RETRIES = 2

# Configuração da página
st.set_page_config(
    page_title="AtaCotada - Adesões",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado (sidebar + anti-flash + header + estilos Adesões)
st.markdown("""
    <style>
        /* Anti-flash: forçar fundo escuro desde o início */
        html, body, [data-testid="stAppViewContainer"],
        .main, [data-testid="stApp"], .stApp {
            background-color: #001a4d !important;
            color: #ffffff !important;
        }

        /* Transição suave ao carregar */
        .stApp {
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0.7; }
            to { opacity: 1; }
        }

        /* Header customizado */
        .header-container {
            background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            text-align: center;
        }

        .logo-text {
            color: #ffffff;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 2px;
            margin-bottom: 0.5rem;
        }

        .sistema-nome {
            color: #d4af37;
            font-size: 48px;
            font-weight: bold;
            letter-spacing: 3px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            margin: 0.5rem 0;
            font-family: 'Arial Black', sans-serif;
        }

        .subtitulo {
            color: #ffffff;
            font-size: 14px;
            margin-top: 0.5rem;
            letter-spacing: 1px;
        }

        /* ===== SIDEBAR MODERNA - PRETA COM BORDA DOURADA ===== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #d4af37 !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.5);
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            background: transparent !important;
        }

        /* Esconder navegação padrão do Streamlit */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }

        /* Título da sidebar */
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

        /* Links de navegação na sidebar */
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

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span {
            color: #ffffff !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
            background: linear-gradient(135deg, #252525 0%, #353535 100%) !important;
            border: 1px solid #d4af37 !important;
            transform: translateX(5px);
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25) !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover span {
            color: #d4af37 !important;
        }

        /* Link ativo / página atual */
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
            color: #0a0a0a !important;
            border: 1px solid #d4af37 !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4) !important;
        }

        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span {
            color: #0a0a0a !important;
        }

        /* Texto e labels na sidebar */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stText,
        [data-testid="stSidebar"] p {
            color: #ffffff !important;
        }

        /* Separadores na sidebar */
        [data-testid="stSidebar"] hr {
            border-color: #333333 !important;
            margin: 1rem 0 !important;
        }

        /* Rodapé da sidebar */
        .sidebar-footer {
            color: #666666;
            font-size: 11px;
            text-align: center;
            padding: 1rem 0;
            border-top: 1px solid #333333;
            margin-top: 2rem;
        }

        /* ===== ESTILOS ESPECÍFICOS DA PÁGINA ADESÕES ===== */
        .metric-card {
            background: rgba(0, 26, 77, 0.6);
            border: 1px solid #d4af37;
            border-radius: 12px;
            padding: 1rem 1.25rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
        }

        .result-card {
            background: rgba(0, 26, 77, 0.45);
            border-radius: 10px;
            padding: 0.9rem 1.1rem;
            margin-bottom: 0.55rem;
            border: 1px solid rgba(212, 175, 55, 0.3);
            box-shadow: 0 6px 24px rgba(0,0,0,0.28);
        }

        .result-card a {
            color: #d4af37 !important;
            text-decoration: none !important;
            font-weight: 600;
        }

        .result-card a:hover {
            color: #f0d060 !important;
            text-decoration: underline !important;
        }

        .status-text {
            color: #cbd5e1;
            font-size: 0.95rem;
            margin-bottom: 0.25rem;
        }

        .stFolium,
        .stFolium iframe,
        .folium-map,
        iframe[title="streamlit_folium.st_folium"],
        iframe[title^="streamlit_folium"],
        div[data-testid="stIframe"],
        div[data-testid="stIframe"] iframe {
            height: 650px !important;
            min-height: 650px !important;
            width: 100% !important;
        }

        /* Botão primário amarelo */
        .stButton > button[kind="primary"],
        .stButton > button[data-testid="stBaseButton-primary"] {
            background-color: #d4af37 !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: bold !important;
        }
        .stButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="stBaseButton-primary"]:hover {
            background-color: #c5a028 !important;
            color: #ffffff !important;
        }

        /* ===== ATA CARDS (st.container com border) ===== */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(135deg, rgba(0, 26, 77, 0.55) 0%, rgba(10, 20, 50, 0.7) 100%) !important;
            border: 1px solid rgba(212, 175, 55, 0.25) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.25) !important;
            transition: border-color 0.25s ease, box-shadow 0.25s ease !important;
            margin-bottom: 0.6rem !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: #d4af37 !important;
            box-shadow: 0 6px 28px rgba(212, 175, 55, 0.15) !important;
        }

        /* Link do fornecedor */
        .ata-fornecedor-link {
            color: #d4af37 !important;
            text-decoration: none !important;
            font-weight: 700 !important;
            font-size: 0.88rem;
        }

        .ata-fornecedor-link:hover {
            color: #f0d060 !important;
            text-decoration: underline !important;
        }

        .ata-info-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem 0.6rem;
        }

        .ata-tag {
            background: rgba(212, 175, 55, 0.08);
            border: 1px solid rgba(212, 175, 55, 0.15);
            border-radius: 6px;
            padding: 0.2rem 0.55rem;
            font-size: 0.78rem;
            color: #cbd5e1;
            white-space: nowrap;
        }

        /* Botão "Outros Docs" — parece uma tag, sem espaço extra */
        [data-testid="stVerticalBlockBorderWrapper"] .stElementContainer:has(.stButton) {
            margin-top: 0.45rem !important;
            margin-bottom: 0 !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
            background: rgba(212, 175, 55, 0.08) !important;
            border: 1px solid rgba(212, 175, 55, 0.15) !important;
            color: #d4af37 !important;
            font-size: 0.73rem !important;
            padding: 0.12rem 0.5rem !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
            min-height: 0 !important;
            height: 1.45rem !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            width: auto !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {
            background: rgba(212, 175, 55, 0.18) !important;
            border-color: #d4af37 !important;
            color: #f0d060 !important;
        }

        /* Botão secundário genérico (fallback) */
        .stButton > button[data-testid="stBaseButton-secondary"] {
            border-color: rgba(212, 175, 55, 0.4) !important;
            color: #d4af37 !important;
            font-size: 0.78rem !important;
            padding: 0.25rem 0.7rem !important;
            border-radius: 6px !important;
            background: transparent !important;
        }
        .stButton > button[data-testid="stBaseButton-secondary"]:hover {
            background: rgba(212, 175, 55, 0.12) !important;
            border-color: #d4af37 !important;
            color: #f0d060 !important;
        }

        /* Lista de docs retornados */
        .doc-list-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-bottom: 0.8rem;
        }

        .doc-pill {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: rgba(0, 26, 77, 0.6);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 20px;
            padding: 0.3rem 0.75rem;
            color: #d4af37 !important;
            font-size: 0.78rem;
            font-weight: 600;
            text-decoration: none !important;
            transition: all 0.2s ease;
            white-space: nowrap;
        }

        .doc-pill:hover {
            background: rgba(0, 26, 77, 0.85);
            border-color: #d4af37;
            color: #f0d060 !important;
        }

        .doc-badge {
            background: rgba(212, 175, 55, 0.15);
            border-radius: 4px;
            padding: 0.05rem 0.35rem;
            font-size: 0.68rem;
            color: #d4af37;
            font-weight: 500;
        }
    </style>
""", unsafe_allow_html=True)

# ===== SIDEBAR - Navegação customizada =====
# Carregar imagem do acanto para a sidebar
_acanto_path = os.path.join(DATA_DIR, "acanto.png")
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
    st.page_link("pages/Cotação_Direta.py", label="Cotação Direta", icon="📨")
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
    st.page_link("pages/Radar_de_Licitacoes.py", label="Radar de Licitações", icon="📡")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
    st.page_link("pages/Calculo_IPCA.py", label="Cálculo IPCA", icon="📊")
    st.page_link("pages/Aprendendo_a_usar.py", label="Aprendendo a usar", icon="🎓")
    st.page_link("pages/Sobre_o_projeto.py", label="Sobre o projeto", icon="ℹ️")
    st.page_link("pages/Suporte_ao_sistema.py", label="Suporte ao sistema", icon="💬")
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br><span style="color:#d4af37;">AtaCotada V2.0</span></div>', unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid],[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#facc15,#eab308)!important;border:1px solid #fde047!important;box-shadow:0 0 14px rgba(250,204,21,.55)!important}[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid] *{background:transparent!important;color:#111!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid],[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#ef4444,#b91c1c)!important;border:1px solid #fca5a5!important;box-shadow:0 0 14px rgba(239,68,68,.55)!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid],[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#25d366,#128c7e)!important;border:1px solid #86efac!important;box-shadow:0 0 14px rgba(37,211,102,.5)!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}</style>', unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-container">
        <div class="logo-text">⚓ MARINHA DO BRASIL ⚓</div>
        <div class="sistema-nome">AtaCotada</div>
        <div class="subtitulo">Adesões</div>
    </div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DO BUSCADOR DE ADESÕES (integrado de Projeto Adesões)
# ═══════════════════════════════════════════════════════════════════════════

def _data_path(filename: str) -> str:
    """Retorna o caminho absoluto para um arquivo de dados do Projeto Adesões."""
    return os.path.join(DATA_DIR, filename)


@st.cache_data
def load_catalog(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, show_spinner=False)
def contar_atas(tipo: str, codigo: str) -> Optional[int]:
    """Quantidade de itens de ata vigentes no período da busca para o código (None se a API falhar)."""
    fim = dt.today().date()
    parametros = {
        "pagina": 1,
        "tamanhoPagina": 10,
        "dataVigenciaInicialMin": (fim - td(days=DATE_RANGE_DAYS - 1)).strftime("%Y-%m-%d"),
        "dataVigenciaInicialMax": fim.strftime("%Y-%m-%d"),
        "codigoPdm" if tipo == "Material" else "codigoItem": codigo,
    }
    try:
        resposta = requests.get(API_URL, params=parametros, timeout=20)
        return int(resposta.json()["totalRegistros"]) if resposta.status_code == 200 else None
    except (requests.RequestException, ValueError, KeyError):
        return None


def contar_atas_em_paralelo(tipo: str, codigos: List[str]) -> Dict[str, Optional[int]]:
    with ThreadPoolExecutor(max_workers=8) as executor:
        return dict(zip(codigos, executor.map(lambda codigo: contar_atas(tipo, codigo), codigos)))


def texto_atas(quantidade: Optional[int]) -> str:
    if quantidade is None:
        return "atas: indisponível"
    return "sem atas no período" if quantidade == 0 else f"{quantidade} itens de ata"


def build_ata_url(identifier: str) -> str:
    try:
        orgao = identifier.split("-")[0]
        compra = identifier.split("/")[1].split("-")[0]
        year = identifier.split("-")[2].split("/")[0].lstrip("0") or "0"
        ata = identifier.split("-")[-1].split("/")[0].lstrip("0") or "0"
        arquivo = identifier.split("-")[1]
        return (
            f"https://pncp.gov.br/pncp-api/v1/orgaos/{orgao}"
            f"/compras/{compra}/{year}/atas/{ata}/arquivos/{arquivo}"
        )
    except Exception:
        return ""


def build_ata_documents_url(identifier: str) -> str:
    """Monta a URL da API PNCP para listar todos os documentos de uma Ata."""
    try:
        orgao = identifier.split("-")[0]
        compra = identifier.split("/")[1].split("-")[0]
        year = identifier.split("-")[2].split("/")[0].lstrip("0") or "0"
        ata = identifier.split("-")[-1].split("/")[0].lstrip("0") or "0"
        return (
            f"https://pncp.gov.br/pncp-api/v1/orgaos/{orgao}"
            f"/compras/{compra}/{year}/atas/{ata}/arquivos"
        )
    except Exception:
        return ""


def build_compra_documents_url(identifier: str) -> str:
    """Monta a URL da API PNCP para listar os documentos da Compra/Licitação."""
    try:
        orgao = identifier.split("-")[0]
        compra = identifier.split("/")[1].split("-")[0]
        year = identifier.split("-")[2].split("/")[0].lstrip("0") or "0"
        return (
            f"https://pncp.gov.br/pncp-api/v1/orgaos/{orgao}"
            f"/compras/{compra}/{year}/arquivos"
        )
    except Exception:
        return ""


def _fetch_docs_from_url(url: str, _requests) -> Tuple[List[Dict], str]:
    """Busca documentos de uma URL da API PNCP."""
    try:
        r = _requests.get(url, timeout=15)
        if r.status_code == 401:
            return [], "Acesso negado (401)."
        if r.status_code == 403:
            return [], "Acesso proibido (403)."
        if r.status_code == 404:
            return [], ""  # Sem documentos neste endpoint, não é erro
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            return data, ""
        return data.get("resultado", data.get("arquivos", [])), ""
    except _requests.exceptions.Timeout:
        return [], "Tempo limite excedido."
    except _requests.exceptions.ConnectionError:
        return [], "Erro de conexão."
    except Exception as e:
        return [], f"Erro: {str(e)}"


def fetch_ata_documents(identifier: str) -> Tuple[List[Dict], str]:
    """Busca todos os documentos relacionados a uma Ata de Registro de Preço
    via API PNCP, combinando documentos da ata e da compra/licitação.
    Retorna (lista_de_docs, mensagem_de_erro). Se sucesso, erro é string vazia."""
    import requests as _requests

    url_ata = build_ata_documents_url(identifier)
    url_compra = build_compra_documents_url(identifier)

    if not url_ata and not url_compra:
        return [], "Não foi possível montar a URL da ata."

    all_docs: List[Dict] = []
    erros: List[str] = []

    # Buscar documentos da ata
    if url_ata:
        docs_ata, err_ata = _fetch_docs_from_url(url_ata, _requests)
        for doc in docs_ata:
            doc["_origem"] = "Ata"
        all_docs.extend(docs_ata)
        if err_ata:
            erros.append(f"Ata: {err_ata}")

    # Buscar documentos da compra/licitação
    if url_compra:
        docs_compra, err_compra = _fetch_docs_from_url(url_compra, _requests)
        for doc in docs_compra:
            doc["_origem"] = "Compra"
        all_docs.extend(docs_compra)
        if err_compra:
            erros.append(f"Compra: {err_compra}")

    # Deduplica por URL (caso existam documentos repetidos)
    seen_urls = set()
    unique_docs: List[Dict] = []
    for doc in all_docs:
        doc_url = doc.get("url", doc.get("uri", ""))
        if doc_url and doc_url in seen_urls:
            continue
        if doc_url:
            seen_urls.add(doc_url)
        unique_docs.append(doc)

    erro_msg = " | ".join(erros) if erros and not unique_docs else ""
    return unique_docs, erro_msg


def normalize_item(item: Dict) -> Optional[Tuple[str, str, str, str, str, str, str]]:
    if item.get("maximoAdesao", 0) == 0:
        return None
    numero_ata = item.get("numeroAtaRegistroPreco", "Ata não informada")
    unidade = item.get("nomeUnidadeGerenciadora", "Unidade não informada")
    fornecedor = item.get("nomeRazaoSocialFornecedor", "Fornecedor não informado")
    identificador = item.get("numeroControlePncpAta", "")
    url = build_ata_url(identificador)
    
    # Extrair numeroCompra e idCompra
    numero_compra = item.get("numeroCompra", "N/I")
    # idCompra costuma vir de identificadores do tipo "XXXXX.XXXXXX/YYYY-ZZ" ou campos específicos
    id_compra = item.get("idCompra") or item.get("numeroSequencialCompra") or "N/I"
    
    return numero_ata, unidade, fornecedor, identificador, url, str(numero_compra), str(id_compra)


def filter_results_by_uf(
    results: List[Dict], uasg_index: Dict[str, Dict[str, str]], uf: str
) -> List[Dict]:
    filtered: List[Dict] = []
    for raw in results:
        uasg_code = extract_uasg(raw)
        if not uasg_code:
            continue
        uasg_info = uasg_index.get(str(uasg_code))
        if not uasg_info:
            continue
        if uasg_info.get("siglaUf") == uf:
            filtered.append(raw)
    return filtered


def extract_uf_from_map(map_data: Optional[Dict]) -> Optional[str]:
    if not map_data:
        return None
    candidate = map_data.get("last_object_clicked")
    if isinstance(candidate, dict):
        props = candidate.get("properties", {})
        sigla = props.get("sigla") or candidate.get("sigla")
        if isinstance(sigla, str) and sigla:
            return sigla
    candidate = (
        map_data.get("last_object_clicked_popup")
        or map_data.get("last_object_clicked_tooltip")
    )
    if not candidate:
        return None
    text = str(candidate)
    text = re.sub(r"<[^>]+>", " ", text)
    match = re.search(r"\b[A-Z]{2}\b", text)
    return match.group(0) if match else None


def parse_remaining_pages(raw_value) -> int:
    try:
        return max(int(raw_value or 0), 0)
    except (TypeError, ValueError):
        return 0


def extract_uasg(item: Dict) -> Optional[str]:
    candidates = [
        "uasg",
        "codigoUasg",
        "codigoUnidadeGerenciadora",
        "codigoUnidadeGestora",
        "codigoUG",
    ]
    for key in candidates:
        value = item.get(key)
        if value:
            return str(value)
    return None


@st.cache_data
def load_uasg_index(path: str) -> Dict[str, Dict[str, str]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            data = json.load(f)
    index: Dict[str, Dict[str, str]] = {}
    for entry in data:
        code = str(entry.get("codigoUasg", "")).strip()
        if not code:
            continue
        index[code] = entry
    return index


@st.cache_data
def load_state_geojson(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def polygon_centroid(coords: List[List[float]]) -> Tuple[float, float]:
    if not coords:
        return 0.0, 0.0
    area = 0.0
    cx = 0.0
    cy = 0.0
    for idx in range(len(coords) - 1):
        x0, y0 = coords[idx]
        x1, y1 = coords[idx + 1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if area == 0.0:
        xs = [pt[0] for pt in coords]
        ys = [pt[1] for pt in coords]
        return (sum(ys) / len(ys), sum(xs) / len(xs))
    area *= 0.5
    cx /= 6.0 * area
    cy /= 6.0 * area
    return (cy, cx)


def _compute_multipolygon_centroid(coords):
    weighted_lat = 0.0
    weighted_lon = 0.0
    total_area = 0.0
    for polygon in coords:
        if not polygon:
            continue
        ring = polygon[0]
        if len(ring) < 3:
            continue
        area = 0.0
        for idx in range(len(ring) - 1):
            x0, y0 = ring[idx]
            x1, y1 = ring[idx + 1]
            area += x0 * y1 - x1 * y0
        area = abs(area) / 2.0
        if area == 0.0:
            continue
        lat, lon = polygon_centroid(ring)
        weighted_lat += lat * area
        weighted_lon += lon * area
        total_area += area
    if total_area == 0.0:
        return (0.0, 0.0)
    return (weighted_lat / total_area, weighted_lon / total_area)


def compute_state_centroids(geojson: Dict) -> Dict[str, Tuple[float, float]]:
    centroids: Dict[str, Tuple[float, float]] = {}
    for feature in geojson.get("features", []):
        sigla = feature.get("properties", {}).get("sigla")
        geometry = feature.get("geometry", {})
        if not sigla or not geometry:
            continue
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates", [])
        if geom_type == "Polygon" and coords:
            centroid = polygon_centroid(coords[0])
        elif geom_type == "MultiPolygon" and coords:
            centroid = _compute_multipolygon_centroid(coords)
        else:
            centroid = (0.0, 0.0)
        centroids[sigla] = centroid
    return centroids


@st.cache_data
def load_municipio_geojson(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def compute_municipio_centroids(geojson: Dict) -> Dict[str, Tuple[float, float]]:
    centroids: Dict[str, Tuple[float, float]] = {}
    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        mun_id = props.get("id")
        geometry = feature.get("geometry", {})
        if not mun_id or not geometry:
            continue
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates", [])
        if geom_type == "Polygon" and coords:
            centroid = polygon_centroid(coords[0])
        elif geom_type == "MultiPolygon" and coords:
            centroid = _compute_multipolygon_centroid(coords)
        else:
            centroid = (0.0, 0.0)
        centroids[str(mun_id)] = centroid
    return centroids


# ── Funções assíncronas de busca ───────────────────────────────────────────

async def fetch_page(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    page: int,
    base_params: Dict[str, str],
) -> Dict:
    params = {**base_params, "pagina": page}
    retries = API_SEARCH_RETRIES
    delay = 0.5
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(API_URL, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(delay)
                delay *= 2


async def search_async(
    tipo: str,
    codigo: str,
    status_placeholder: st.delta_generator.DeltaGenerator,
    progress_bar,
    federal_only: bool,
    uasg_sphere: Dict[str, str],
    max_concurrency: int = MAX_CONCURRENCY,
) -> List[Dict]:
    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=API_CONNECT_TIMEOUT_SECONDS,
        sock_connect=API_CONNECT_TIMEOUT_SECONDS,
        sock_read=API_SEARCH_READ_TIMEOUT_SECONDS,
    )
    semaphore = asyncio.Semaphore(max_concurrency)
    connector = aiohttp.TCPConnector(limit=None, ssl=False)

    seen = set()
    results: List[Dict] = []
    tasks: List[asyncio.Task] = []
    total_pages_count = 0
    processed_pages = 0

    def render_payload(payload: Dict) -> None:
        for raw in payload.get("resultado", []):
            uasg_code = extract_uasg(raw)
            if federal_only:
                if not uasg_code:
                    continue
                if uasg_sphere.get(str(uasg_code)) != "F":
                    continue
            normalized = normalize_item(raw)
            if not normalized:
                continue
            key = normalized[3]
            if key in seen:
                continue
            seen.add(key)
            results.append(raw)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        end_date = dt.today().date()
        start_date = end_date - td(days=DATE_RANGE_DAYS - 1)
        base_params: Dict[str, str] = {
            "tamanhoPagina": PAGE_SIZE.get(tipo, 120),
            "dataVigenciaInicialMin": start_date.strftime("%Y-%m-%d"),
            "dataVigenciaInicialMax": end_date.strftime("%Y-%m-%d"),
        }
        if tipo == "Material":
            base_params["codigoPdm"] = codigo
        else:
            base_params["codigoItem"] = codigo

        status_placeholder.info("Conectando ao Compras.gov e carregando a primeira página…")
        progress_bar.progress(5, text="Conectando ao Compras.gov…")

        first_page = await fetch_page(session, semaphore, 1, base_params)
        total_pages_count = 1 + parse_remaining_pages(first_page.get("paginasRestantes"))
        render_payload(first_page)
        processed_pages = 1
        progress_value = min(int(processed_pages / max(total_pages_count, 1) * 100), 100)
        status_placeholder.info(
            f"Página {processed_pages}/{total_pages_count} carregada. {len(results)} atas encontradas até agora."
        )
        progress_bar.progress(
            max(progress_value, 10),
            text=(
                f"Carregando páginas do Compras.gov: {processed_pages}/{total_pages_count} "
                f"| atas encontradas: {len(results)}"
            ),
        )

        for page in range(2, total_pages_count + 1):
            tasks.append(asyncio.create_task(fetch_page(session, semaphore, page, base_params)))

        if total_pages_count == processed_pages:
            progress_bar.progress(
                100,
                text=f"Busca concluída. {len(results)} atas encontradas.",
            )
            status_placeholder.success(f"Busca concluída. {len(results)} atas encontradas.")
            return results

        for idx, task in enumerate(asyncio.as_completed(tasks), start=processed_pages + 1):
            try:
                payload = await task
                render_payload(payload)
                progress_value = min(int(idx / max(total_pages_count, 1) * 100), 100)
                status_placeholder.info(
                    f"Página {idx}/{total_pages_count} carregada. {len(results)} atas encontradas até agora."
                )
                progress_bar.progress(
                    progress_value,
                    text=(
                        f"Carregando páginas do Compras.gov: {idx}/{total_pages_count} "
                        f"| atas encontradas: {len(results)}"
                    ),
                )
            except Exception:
                status_placeholder.warning(
                    f"Falha ao carregar uma das páginas. {len(results)} atas já foram encontradas até agora."
                )

        progress_bar.progress(
            100,
            text=f"Busca concluída. {len(results)} atas encontradas.",
        )
        status_placeholder.success(f"Busca concluída. {len(results)} atas encontradas.")
        return results


async def fetch_unit_detail(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    numero_ata: str,
    unidade_gerenciadora: str,
    numero_item: str,
) -> Optional[Dict]:
    """Busca detalhes de saldo/adesão no endpoint 3_consultarUnidadesItem."""
    params = {
        "numeroAta": numero_ata,
        "unidadeGerenciadora": unidade_gerenciadora,
        "numeroItem": numero_item,
        "tamanhoPagina": 10,
        "pagina": 1,
    }
    retries = API_DETAIL_RETRIES
    delay = 0.5
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(API_URL_UNIDADES, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    results = data.get("resultado", [])
                    # o saldo de adesões do item vem na linha da unidade GERENCIADORA (as demais são participantes)
                    gerenciadora = [r for r in results if str(r.get("tipoUnidade", "")).upper() == "GERENCIADORA"]
                    if gerenciadora or results:
                        return (gerenciadora or results)[0]
                    return None
            except Exception:
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(delay)
                delay *= 2
    return None


async def enrich_results_async(
    display_results: List[Dict],
    status_placeholder: st.delta_generator.DeltaGenerator,
    progress_bar,
    max_concurrency: int = MAX_CONCURRENCY,
) -> Dict[str, Dict]:
    """Para cada ata em display_results, busca detalhes de saldo/adesão.
    Retorna dict mapeando identificador -> detalhes."""
    timeout = aiohttp.ClientTimeout(
        total=None,
        connect=API_CONNECT_TIMEOUT_SECONDS,
        sock_connect=API_CONNECT_TIMEOUT_SECONDS,
        sock_read=API_DETAIL_READ_TIMEOUT_SECONDS,
    )
    semaphore = asyncio.Semaphore(max_concurrency)
    connector = aiohttp.TCPConnector(limit=None, ssl=False)
    details: Dict[str, Dict] = {}

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = []
        for raw in display_results:
            numero_ata = raw.get("numeroAtaRegistroPreco", "")
            unidade = raw.get("codigoUnidadeGerenciadora", "") or str(raw.get("codigoUasg", ""))
            numero_item = raw.get("numeroItem", "")
            identificador = f'{raw.get("numeroControlePncpAta", "")}|{numero_item}'  # saldo é por item, não por ata
            if not (numero_ata and unidade and numero_item):
                continue

            async def fetch_with_key(
                key: str,
                ata_numero: str,
                ata_unidade: str,
                ata_item: str,
            ) -> Tuple[str, Optional[Dict]]:
                result = await fetch_unit_detail(
                    session,
                    semaphore,
                    ata_numero,
                    ata_unidade,
                    ata_item,
                )
                return key, result

            tasks.append(
                asyncio.create_task(
                    fetch_with_key(identificador, numero_ata, unidade, numero_item)
                )
            )
        total_tasks = len(tasks)
        if total_tasks == 0:
            progress_bar.progress(100, text="Nenhum detalhe adicional para carregar.")
            status_placeholder.info("Nenhum detalhe adicional para carregar.")
            return details

        status_placeholder.info(
            f"Carregando detalhes complementares de {total_tasks} atas…"
        )
        progress_bar.progress(5, text=f"Carregando detalhes de 0/{total_tasks} atas…")

        processed_tasks = 0
        for task in asyncio.as_completed(tasks):
            key, result = await task
            processed_tasks += 1
            if isinstance(result, dict):
                details[key] = result
            progress_value = min(int(processed_tasks / total_tasks * 100), 100)
            progress_bar.progress(
                progress_value,
                text=(
                    f"Carregando detalhes de {processed_tasks}/{total_tasks} atas "
                    f"| detalhes prontos: {len(details)}"
                ),
            )
            status_placeholder.info(
                f"Detalhes carregados: {processed_tasks}/{total_tasks}."
            )

        progress_bar.progress(
            100,
            text=f"Detalhes concluídos. {len(details)} atas enriquecidas.",
        )
        status_placeholder.success(
            f"Detalhes concluídos. {len(details)} atas enriquecidas."
        )
    return details


def _qtd(valor) -> str:
    """Quantidade sem casas decimais desnecessárias, no formato brasileiro."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return "N/I"
    texto = f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return texto[:-3] if texto.endswith(",00") else texto


def situacao_sicaf_fornecedores(cnpjs: List[str]) -> Dict[str, str]:
    """Situação no cadastro de fornecedores (SICAF) de cada CNPJ, consultada em paralelo (com cache)."""
    unicos = sorted({c for c in cnpjs if c})
    if not unicos:
        return {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = list(pool.map(consultar_sicaf, unicos))
    return {c: (texto_sicaf(sit) if not erro else "N/I") for c, (sit, erro) in zip(unicos, resultados)}


@st.cache_data(ttl=1800, show_spinner=False)
def adesoes_aprovadas(numero_ata: str, unidade_gerenciadora: str, numero_item: str) -> Tuple[List[Dict], Optional[str]]:
    """Adesões (caronas) já aprovadas para o item da ata: unidade não participante, quantidade e data."""
    dados, erro = http_get_json(API_URL_ADESOES, {"numeroAta": numero_ata, "unidadeGerenciadora": unidade_gerenciadora,
                                                  "numeroItem": numero_item, "pagina": 1, "tamanhoPagina": 100}, timeout=60, tentativas=3)
    return (dados or {}).get("resultado", []) or [], erro


def _brl_un(valor) -> str:
    try:
        return "R$ " + f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "N/I"


def _num(valor) -> Optional[float]:
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _incluir_na_cesta(ata: Dict, item: Dict) -> None:
    """Junta o item à lista de adesão da ata. Cada ata vira um ofício (um gerenciador por ofício)."""
    cesta = st.session_state.setdefault("_cesta_adesao", {})
    if ata["id"] not in cesta:
        # versão única por sessão: uma ata removida e incluída de novo não herda a tabela (e as edições) da anterior
        st.session_state["_cesta_seq"] = int(st.session_state.get("_cesta_seq") or 0) + 1
        cesta[ata["id"]] = {**ata, "itens": [], "versao": st.session_state["_cesta_seq"]}
    grupo = cesta[ata["id"]]
    if all(i["Item"] != item["Item"] for i in grupo["itens"]):
        grupo["itens"].append(item)
        grupo.pop("analise", None)
    st.toast(f"Item {item['Item']} incluído na adesão à Ata {ata['ata']}.")


@st.cache_data(ttl=3600, show_spinner=False)
def itens_da_ata(numero_controle_ata: str) -> Tuple[List[Dict], Optional[str]]:
    """Todos os itens de uma ata (do mesmo fornecedor), para incluir outros itens além do pesquisado."""
    dados, erro = http_get_json("https://dadosabertos.compras.gov.br/modulo-arp/2.1_consultarARPItem_Id",
                                {"numeroControlePncpAta": numero_controle_ata}, timeout=60)
    if erro:
        return [], erro
    return (dados or {}).get("resultado") or [], None


def _incluir_outros_itens(chave_ata: str, chave_sel: str) -> None:
    grupo = (st.session_state.get("_cesta_adesao") or {}).get(chave_ata)
    escolhidos = st.session_state.get(chave_sel) or []
    if not grupo or not escolhidos:
        return
    por_rotulo = {o["rotulo"]: o for o in grupo.get("outros") or []}
    ja = {i["Item"] for i in grupo["itens"]}
    for rotulo in escolhidos:
        o = por_rotulo.get(rotulo)
        if o and o["item"]["Item"] not in ja:
            grupo["itens"].append(dict(o["item"]))
    st.session_state["_cesta_seq"] = int(st.session_state.get("_cesta_seq") or 0) + 1
    grupo["versao"] = st.session_state["_cesta_seq"]
    grupo.pop("analise", None)
    st.session_state[chave_sel] = []


def _marcar_reanalise(chave_ata: str) -> None:
    """Ao marcar/desmarcar 'compras homologadas', a análise já exibida é refeita no novo modo."""
    grupo = (st.session_state.get("_cesta_adesao") or {}).get(chave_ata)
    if grupo and grupo.get("analise") is not None:
        grupo["reanalisar"] = True


def _aplicar_edicao_cesta(chave_ata: str, chave_editor: str) -> None:
    """Grava na cesta as quantidades digitadas e retira os itens desmarcados."""
    grupo = (st.session_state.get("_cesta_adesao") or {}).get(chave_ata)
    if not grupo or not chave_editor.endswith(f"_{grupo['versao']}"):
        return  # edição de uma tabela que já saiu da tela (ata removida ou lista refeita): nada a gravar
    edicoes = (st.session_state.get(chave_editor) or {}).get("edited_rows", {})
    retirar = set()
    for linha, campos in edicoes.items():
        if not 0 <= int(linha) < len(grupo["itens"]):
            continue
        item = grupo["itens"][int(linha)]
        if "Quantidade pretendida" in campos:
            item["Quantidade"] = campos["Quantidade pretendida"]
        if "Preço de referência (manual)" in campos:
            item["ref_manual"] = campos["Preço de referência (manual)"]
        if campos.get("Incluir") is False:
            retirar.add(int(linha))
    if retirar:
        grupo["itens"] = [i for n, i in enumerate(grupo["itens"]) if n not in retirar]
        st.session_state["_cesta_seq"] = int(st.session_state.get("_cesta_seq") or 0) + 1
        grupo["versao"] = st.session_state["_cesta_seq"]
    if grupo.pop("analise", None) is not None:
        grupo["reanalisar"] = True   # a análise já feita é refeita com as quantidades e preços novos
    if not grupo["itens"]:
        st.session_state["_cesta_adesao"].pop(chave_ata, None)


def _enviar_ao_babilaca(chave_ata: str) -> None:
    import vantajosidade as V
    grupo = (st.session_state.get("_cesta_adesao") or {}).get(chave_ata)
    if not grupo or not grupo["itens"]:
        return
    itens = grupo["itens"]
    analise = grupo.get("analise")
    st.session_state["_ofad_prefill"] = {
        "ata": grupo["ata"], "gerenciador": grupo["gerenciador"], "uasg": grupo["uasg"], "licitacao": grupo["licitacao"],
        "objeto": itens[0]["Descrição"] if len(itens) == 1 else f"os {len(itens)} itens relacionados no item 3",
        "itens": [{"Item": i["Item"], "Descrição": i["Descrição"], "Unidade": i.get("Unidade", ""),
                   "Quantidade": "" if i.get("Quantidade") in (None, "") else str(i["Quantidade"])} for i in itens],
        "justificativa": V.texto_justificativa(analise, grupo["ata"]) if analise else "",
        "relatorio_vantajosidade": V.corpo_relatorio(grupo, analise) if analise else "",
    }


def _painel_cesta_adesao() -> None:
    """Itens escolhidos para adesão, agrupados por ata: quantidade, vantajosidade e envio do ofício ao Babilaca."""
    cesta = st.session_state.get("_cesta_adesao") or {}
    if not cesta:
        return
    import vantajosidade as V
    st.markdown("#### 🛒 Itens escolhidos para adesão")
    st.caption("Cada ata vira um ofício ao seu órgão gerenciador. Informe a quantidade pretendida de cada item "
               "(até o máximo por órgão), analise a vantajosidade e gere o ofício no Babilaca.")
    for chave_ata, grupo in list(cesta.items()):
        with st.container(border=True):
            st.markdown(f"**Ata {grupo['ata']}** — {grupo['gerenciador']} (UASG {grupo['uasg']}) · {grupo['licitacao']}")
            linhas = [{"Incluir": True, "Item": i["Item"], "Descrição": i["Descrição"], "Preço registrado": i.get("preco"),
                       "Máx. por órgão": i.get("max"), "Quantidade pretendida": _num(i.get("Quantidade")),
                       "Preço de referência (manual)": _num(i.get("ref_manual"))}
                      for i in grupo["itens"]]
            chave_editor = f"cesta_ed_{chave_ata}_{grupo['versao']}"
            st.data_editor(
                linhas, key=chave_editor, hide_index=True, width="stretch",
                disabled=["Item", "Descrição", "Preço registrado", "Máx. por órgão"],
                column_config={
                    "Incluir": st.column_config.CheckboxColumn(width="small", help="Desmarque para retirar o item"),
                    "Preço registrado": st.column_config.NumberColumn(format="R$ %.2f"),
                    "Máx. por órgão": st.column_config.NumberColumn(format="%.0f"),
                    "Quantidade pretendida": st.column_config.NumberColumn(min_value=0, step=1, required=False),
                    "Preço de referência (manual)": st.column_config.NumberColumn(
                        min_value=0.0, format="R$ %.2f", required=False,
                        help="Use quando o sistema não achar preço de mercado: informe o valor obtido na sua pesquisa "
                             "(ex.: Cotação Rápida) e analise de novo."),
                    "Descrição": st.column_config.TextColumn(width="large"),
                },
                on_change=_aplicar_edicao_cesta, args=(chave_ata, chave_editor))
            with st.expander("➕ Outros itens desta ata", expanded=False):
                st.caption("A busca mostra só os itens da família pesquisada. Aqui aparecem todos os itens desta ata "
                           "(mesmo fornecedor) para você incluir no mesmo ofício.")
                if st.button("Carregar os itens da ata", key=f"cesta_out_{chave_ata}"):
                    with st.spinner("Buscando os itens da ata..."):
                        lista, erro = itens_da_ata(chave_ata)
                    if erro:
                        st.warning(f"Não foi possível carregar os itens agora ({erro}).")
                    grupo["outros"] = [{
                        "rotulo": f"Item {r.get('numeroItem')} — {str(r.get('descricaoItem') or '')[:90]} — "
                                  f"{MP_brl(r.get('valorUnitario'))}",
                        "item": {"Item": str(r.get("numeroItem")), "Descrição": str(r.get("descricaoItem") or ""),
                                 "Unidade": "", "codigo": str(r.get("codigoItem") or ""), "pdm": str(r.get("codigoPdm") or ""),
                                 "preco": _num(r.get("valorUnitario")),
                                 "max": (_num(r.get("quantidadeHomologadaItem")) or 0) * 0.5 or None, "Quantidade": ""},
                    } for r in lista if r.get("maximoAdesao")]
                ja = {i["Item"] for i in grupo["itens"]}
                disponiveis = [o["rotulo"] for o in grupo.get("outros") or [] if o["item"]["Item"] not in ja]
                if grupo.get("outros") is not None:
                    if disponiveis:
                        chave_sel = f"cesta_sel_{chave_ata}"
                        st.multiselect("Itens da ata que aceitam adesão", disponiveis, key=chave_sel)
                        st.button("Incluir os itens marcados", key=f"cesta_inc_{chave_ata}",
                                  on_click=_incluir_outros_itens, args=(chave_ata, chave_sel))
                        st.caption("Máximo por órgão destes itens = 50% da quantidade registrada. O saldo de adesão já "
                                   "consumido por outros órgãos só aparece nos itens vindos da busca: confira no card.")
                    else:
                        st.caption("Todos os itens da ata que aceitam adesão já estão na lista.")
            acima = [i["Item"] for i in grupo["itens"] if _num(i.get("Quantidade")) and i.get("max")
                     and _num(i["Quantidade"]) > i["max"]]
            if acima:
                st.warning(f"Quantidade acima do máximo por órgão (art. 86, §4º) no(s) item(ns): {', '.join(acima)}.")
            sem_qtd = [i["Item"] for i in grupo["itens"] if not _num(i.get("Quantidade"))]
            _c1, _c2, _c3 = st.columns([2, 2, 1])
            with _c1:
                compras = st.checkbox("Incluir compras homologadas (mais preciso, mais lento)", key=f"cesta_cmp_{chave_ata}",
                                      on_change=_marcar_reanalise, args=(chave_ata,))
                analisar = st.button("📊 Analisar vantajosidade", key=f"cesta_an_{chave_ata}", use_container_width=True)
                if analisar or grupo.pop("reanalisar", False):
                    with st.spinner("Buscando preços de mercado dos últimos 12 meses"
                                    + (" (compras homologadas: consulta lenta, uma por vez)..." if compras else "...")):
                        grupo["analise"] = V.analisar(
                            [{**i, "Quantidade": i.get("Quantidade") or 0} for i in grupo["itens"]], chave_ata, compras)
                        grupo["analise_com_compras"] = compras
            with _c2:
                if st.button("✉️ Gerar ofício no Babilaca", key=f"cesta_of_{chave_ata}", type="primary",
                             use_container_width=True):
                    _enviar_ao_babilaca(chave_ata)
                    st.switch_page("pages/O_Babilaca_(IA).py")
                if sem_qtd:
                    st.caption(f"Sem quantidade: item(ns) {', '.join(sem_qtd)} — pode completar no Babilaca.")
            with _c3:
                if st.button("🗑️ Remover", key=f"cesta_rm_{chave_ata}", use_container_width=True):
                    cesta.pop(chave_ata, None)
                    st.rerun()
            analise = grupo.get("analise")
            if analise:
                r = V.resumo(analise)
                st.caption("Análise " + ("com" if grupo.get("analise_com_compras") else "sem")
                           + " compras homologadas. Verde: vantajoso · amarelo: compatível com o mercado · vermelho: "
                             "acima do mercado ou sem preço de referência.")
                tabela = pd.DataFrame([{
                    "Item": a["item"], "Preço da ata": MP_brl(a["preco"]), "Mediana de mercado": MP_brl(a["mediana"]),
                    "Faixa de mercado": f"{MP_brl(a['menor'])} a {MP_brl(a['maior'])}" if a["mediana"] is not None else "a pesquisar",
                    "Preços": f"{a['aceitos']}/{a['fontes']}",
                    "Diferença": f"{a['diferenca'] * 100:+.1f}%".replace(".", ",") if a["diferenca"] is not None else "-",
                    "Economia": MP_brl(a["economia"]), "Situação": a["situacao"], "Obs.": a.get("erro") or "",
                    "_classe": a["classe"]} for a in analise])
                cores = {"vantajoso": "#14532d", "compativel": "#713f12", "acima": "#7f1d1d", "sem_ref": "#7f1d1d"}
                st.dataframe(tabela.style.apply(lambda linha: [f"background-color: {cores.get(linha['_classe'], '')}"] * len(linha),
                                                axis=1), hide_index=True, width="stretch",
                             column_order=[c for c in tabela.columns if c != "_classe"])
                if r["sem_referencia"]:
                    st.error("Sem preço de referência no(s) item(ns) " + ", ".join(str(a["item"]) for a in r["sem_referencia"])
                             + ". Confira se o código do item não está restrito demais (o sistema já tentou itens "
                               "semelhantes da mesma família). Se não estiver, pesquise o preço (ex.: Cotação Rápida) e "
                               "informe-o na coluna **Preço de referência (manual)** acima, ou complete o campo marcado "
                               "com __________ no relatório editável do Babilaca.")
                if r["desvantajosos"]:
                    st.warning("Acima de todos os preços de mercado encontrados: item(ns) "
                               + ", ".join(str(a["item"]) for a in r["desvantajosos"])
                               + ". Retire da adesão ou justifique no relatório.")
                with st.expander("Justificativa por item (vai no relatório)"):
                    for a in analise:
                        st.markdown("- " + V.justificativa_item(a).replace("$", "\\$"))
                if r["itens_com_referencia"] and r["valor_mercado"]:
                    cor = st.success if r["economia"] >= 0 else st.warning
                    cor(f"Adesão: {MP_brl(r['valor_ata'])} × mercado (mediana): {MP_brl(r['valor_mercado'])} → "
                        f"{'economia' if r['economia'] >= 0 else 'acréscimo'} de {MP_brl(abs(r['economia']))}"
                        f" ({abs(r['percentual']) * 100:.1f}%). O relatório e a justificativa vão junto com o ofício.".replace("$", "\\$"))
                elif not any(_num(i.get("Quantidade")) for i in grupo["itens"]):
                    st.info("Informe as quantidades para calcular a economia total.")


def MP_brl(valor) -> str:
    if valor is None:
        return "-"
    return "R$ " + f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def run_enrich(
    display_results: List[Dict],
    status_placeholder: st.delta_generator.DeltaGenerator,
    progress_bar,
) -> Dict[str, Dict]:
    """Wrapper síncrono para enriquecer resultados com dados do endpoint 3."""
    try:
        return asyncio.run(enrich_results_async(display_results, status_placeholder, progress_bar))
    except Exception:
        return {}


def run_search(
    tipo: str,
    codigo: str,
    federal_only: bool,
    uasg_sphere: Dict[str, str],
) -> List[Dict]:
    status_placeholder = st.empty()
    progress_bar = st.progress(0, text="Preparando consulta…")
    with st.spinner("Consultando dados, por favor aguarde um momento…"):
        try:
            results = asyncio.run(
                search_async(
                    tipo,
                    codigo,
                    status_placeholder,
                    progress_bar,
                    federal_only=federal_only,
                    uasg_sphere=uasg_sphere,
                )
            )
        except Exception:
            progress_bar.empty()
            status_placeholder.error(
                "Não foi possível concluir a consulta agora, provavelmente por instabilidades no Compras.gov. Tente novamente em instantes."
            )
            return []
    return results


def build_map(results: List[Dict], uasg_index: Dict[str, Dict[str, str]]) -> folium.Map:
    geojson = load_state_geojson(_data_path("brasil-estados.geojson"))
    counts_by_uf: Dict[str, int] = {}

    for raw in results:
        uasg_code = extract_uasg(raw)
        if not uasg_code:
            continue
        uasg_info = uasg_index.get(str(uasg_code))
        if not uasg_info:
            continue
        uf = uasg_info.get("siglaUf")
        if not uf:
            continue
        counts_by_uf[uf] = counts_by_uf.get(uf, 0) + 1

    mapa = folium.Map(
        location=[-14.235, -51.9253],
        zoom_start=4,
        tiles=None,
        height="650px",
        width="100%",
    )
    max_count = max(counts_by_uf.values(), default=0)

    try:
        import branca.colormap as cm
        colormap = cm.linear.YlGnBu_09.scale(0, max(max_count, 1))
        colormap.caption = "Atas encontradas"
        colormap.add_to(mapa)
        default_fill = "#e2e8f0"
    except Exception:
        colormap = None
        default_fill = "#1f2937"

    geojson_with_counts = json.loads(json.dumps(geojson))
    for feature in geojson_with_counts.get("features", []):
        sigla = feature.get("properties", {}).get("sigla")
        feature["properties"]["count"] = counts_by_uf.get(sigla, 0)

    def style_fn(feature: Dict) -> Dict[str, object]:
        sigla = feature.get("properties", {}).get("sigla")
        count = counts_by_uf.get(sigla, 0)
        fill_color = default_fill
        if colormap and count > 0:
            fill_color = colormap(count)
        return {
            "fillColor": fill_color,
            "color": "#1f2937",
            "weight": 1,
            "fillOpacity": 0.72 if count > 0 else 0.3,
        }

    folium.GeoJson(
        geojson_with_counts,
        style_function=style_fn,
        highlight_function=lambda _: {"weight": 2, "color": "#111827"},
        popup=folium.GeoJsonPopup(fields=["sigla"], labels=False),
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "sigla", "count"],
            aliases=["Estado", "UF", "Atas"],
            localize=True,
        ),
    ).add_to(mapa)

    try:
        bounds = folium.GeoJson(geojson).get_bounds()
        mapa.fit_bounds(bounds, padding=(20, 20))
        mapa.options["maxBounds"] = bounds
        mapa.options["minZoom"] = 4
    except Exception:
        pass

    return mapa


# ═══════════════════════════════════════════════════════════════════════════
# INTERFACE DA PÁGINA
# ═══════════════════════════════════════════════════════════════════════════

st.caption("Consulta inteligente às atas de registro de preços do Compras.gov.br.")
st.write("Selecione o tipo de item, escolha o código desejado e encontre atas para adesão.")

tipo = st.selectbox(
    "Tipo de item",
    ["Material", "Serviço"],
    index=None,
    placeholder="Selecione material ou serviço",
)

selected_label = None
codigo = None
federal_only = False
uasg_sphere: Dict[str, str] = {}

if tipo:
    data_catalogo = atualizado_em()
    st.caption(
        "Pesquise pelo nome, por uma descrição (ex.: resma de papel a4) ou pelo código "
        + ("CATMAT/PDM" if tipo == "Material" else "do serviço")
        + (f" — catálogo oficial atualizado em {data_catalogo}." if data_catalogo else ".")
    )
    consulta = st.text_input(
        "Pesquisar material" if tipo == "Material" else "Pesquisar serviço",
        placeholder="Ex.: notebook, luva de procedimento, resma de papel a4" if tipo == "Material" else "Ex.: manutenção de ar condicionado",
    ).strip()

if tipo == "Material":
    catmat = carregar_indice_catmat(CATMAT_PATH)
    if consulta:
        # Muitas famílias parecidas disputam as primeiras posições (ex.: dezenas de "PAPEL ..."): avalia as atas de
        # até 40 delas para que a família que realmente tem atas não fique de fora, e mostra as 15 melhores.
        familias = buscar_familias(consulta, catmat, limite=40)
        atas = contar_atas_em_paralelo(tipo, [f["codigo"] for f in familias])
        so_com_atas = st.checkbox("Mostrar apenas famílias com atas vigentes", value=True, key="familias_so_com_atas")
        if so_com_atas and any(atas.values()):
            familias = [f for f in familias if atas[f["codigo"]]]
        elif so_com_atas and familias:
            st.info("Nenhuma das famílias encontradas tem atas vigentes no período; mostrando todas.")
        familias = familias[:15]
        rotulos = {
            f"{f['nome']} · PDM {f['codigo']} · {texto_atas(atas[f['codigo']])} · {f['nota']:.0f}%": f for f in familias
        }
        if rotulos:
            selected_label = st.selectbox(
                "Famílias de material encontradas (a busca de atas é feita pela família)", list(rotulos), index=0
            )
            escolhida = rotulos[selected_label]
            st.caption(f"Classe: {escolhida['classe']} — {escolhida['exemplo']}")
            codigo = escolhida["codigo"]
        else:
            st.warning("Nenhuma família de material encontrada. Tente outras palavras ou o código CATMAT do item.")
    else:
        materiais = load_catalog(_data_path("catalogo_pdm.json"))
        selected_label = st.selectbox(
            "Ou escolha na lista completa de famílias",
            sorted(materiais.keys()),
            index=None,
            placeholder="Selecione uma família de material",
        )
        if selected_label:
            codigo = materiais[selected_label]

if tipo == "Serviço":
    catalogo_servico = carregar_catalogo(CATSERV_PATH)
    if consulta:
        servicos_encontrados = buscar_servicos(consulta, catalogo_servico)
        atas = contar_atas_em_paralelo(tipo, [s["codigo"] for s in servicos_encontrados])
        rotulos = {
            f"{s['nome']} · cód. {s['codigo']} · {texto_atas(atas[s['codigo']])} · {s['nota']:.0f}%": s
            for s in servicos_encontrados
        }
        if rotulos:
            selected_label = st.selectbox("Serviços encontrados", list(rotulos), index=0)
            codigo = rotulos[selected_label]["codigo"]
        else:
            st.warning("Nenhum serviço encontrado. Tente outras palavras ou o código do serviço.")
    else:
        servicos = load_catalog(_data_path("catalogo_servicos.json"))
        selected_label = st.selectbox(
            "Ou escolha na lista completa de serviços",
            sorted(servicos.keys()),
            index=None,
            placeholder="Selecione um serviço",
        )
        if selected_label:
            codigo = servicos[selected_label]

if selected_label:
    federal_only = st.checkbox("Buscar somente atas da esfera federal", value=True)
    if federal_only:
        uasg_sphere = load_catalog(_data_path("esfera_uasg.json"))

# ── Estado de visualização ─────────────────────────────────────────────────
st.session_state.setdefault("modo_exibicao", "Mapa")
if "selected_uf" not in st.session_state:
    st.session_state["selected_uf"] = None
next_mode = st.session_state.pop("next_modo_exibicao", None)
if next_mode:
    st.session_state["modo_exibicao"] = next_mode
if st.session_state.pop("reset_view", False):
    st.session_state["modo_exibicao"] = "Mapa"
    st.session_state["selected_uf"] = None

start_button = st.button(
    "Buscar adesões", type="primary", use_container_width=True, disabled=not codigo
)

if start_button and tipo and codigo:
    results = run_search(tipo, codigo, federal_only, uasg_sphere)
    st.session_state["atas"] = results
    st.session_state["reset_view"] = True
elif start_button and not codigo:
    st.warning("Selecione um item antes de iniciar a busca.")

# ── Exibição de resultados ─────────────────────────────────────────────────
results = st.session_state.get("atas", [])
modo_exibicao = st.session_state.get("modo_exibicao", "Mapa")
selected_uf = st.session_state.get("selected_uf")

if results:
    uasg_index = load_uasg_index(_data_path("uasgs.json"))

    # Card com quantidade de atas encontradas
    st.markdown(
        f"""
        <div class="metric-card" style="text-align:center;margin-bottom:1.2rem;">
            <div style="color:#d4af37;font-size:2rem;font-weight:bold;">{len(results)}</div>
            <div style="color:#cbd5e1;font-size:0.95rem;">ata{"s" if len(results) != 1 else ""} encontrada{"s" if len(results) != 1 else ""} no total</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if modo_exibicao == "Mapa":
        st.subheader("Mapa das atas encontradas")
        st.caption("Clique no estado onde deseja encontrar atas para adesão.")
        mapa = build_map(results, uasg_index)
        map_data = st_folium(
            mapa,
            height=650,
            use_container_width=True,
            returned_objects=[
                "last_object_clicked",
                "last_object_clicked_popup",
                "last_object_clicked_tooltip",
            ],
        )
        clicked_uf = extract_uf_from_map(map_data)
        if clicked_uf and clicked_uf != selected_uf:
            st.session_state["selected_uf"] = clicked_uf
            st.session_state["next_modo_exibicao"] = "Lista"
            st.rerun()

    if modo_exibicao == "Lista":
        if selected_uf:
            st.subheader(f"Atas encontradas - {selected_uf}")
            if st.button("Limpar filtro de estado"):
                st.session_state["selected_uf"] = None
                st.session_state["next_modo_exibicao"] = "Mapa"
                st.rerun()
            display_results = filter_results_by_uf(results, uasg_index, selected_uf)
        else:
            st.subheader("Atas encontradas")
            display_results = results

        if not display_results:
            st.info("Nenhuma ata encontrada para este estado.")
        else:
            label_uf = f" em {selected_uf}" if selected_uf else ""
            st.markdown(
                f"""
                <div class="metric-card" style="text-align:center;margin-bottom:1rem;">
                    <div style="color:#d4af37;font-size:1.6rem;font-weight:bold;">{len(display_results)}</div>
                    <div style="color:#cbd5e1;font-size:0.9rem;">ata{"s" if len(display_results) != 1 else ""}{label_uf}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Enriquecer resultados com dados do endpoint 3_consultarUnidadesItem
            enrich_status_placeholder = st.empty()
            enrich_progress_bar = st.progress(0, text="Preparando detalhes das atas…")
            with st.spinner("Buscando detalhes de saldo e adesão…"):
                enriched = run_enrich(
                    display_results,
                    enrich_status_placeholder,
                    enrich_progress_bar,
                )
            with st.spinner("Consultando a situação dos fornecedores no SICAF…"):
                sicaf_por_cnpj = situacao_sicaf_fornecedores([str(r.get("niFornecedor") or "") for r in display_results])

            _painel_cesta_adesao()
            for idx, raw in enumerate(display_results):
                normalized = normalize_item(raw)
                if not normalized:
                    continue
                numero, unidade, fornecedor, identificador, url, num_compra, id_compra = normalized

                # Código UASG do órgão
                uasg_code = extract_uasg(raw) or "N/I"

                detail = enriched.get(f"{identificador}|{raw.get('numeroItem', '')}", {})
                saldo_adesoes = detail.get("saldoAdesoes", "N/I")
                saldo_remanejamento = detail.get("saldoRemanejamentoEmpenho", "N/I")
                qtd_limite_adesao = detail.get("qtdLimiteAdesao", "N/I")
                aceita_adesao_raw = detail.get("aceitaAdesao")
                if aceita_adesao_raw is True:
                    aceita_adesao = '✅ Sim'
                elif aceita_adesao_raw is False:
                    aceita_adesao = '❌ Não'
                else:
                    aceita_adesao = 'N/I'

                # Número do item (vem da API 2)
                numero_item = raw.get("numeroItem", "N/I")

                # Saldo explicado: limite global de adesões (dobro do registrado) e máximo por órgão que aderir
                # (50% da quantidade registrada do item — Lei 14.133/2021, art. 86, §4º)
                qtd_registrada = raw.get("quantidadeHomologadaItem")
                try:
                    max_por_orgao = float(qtd_registrada) * 0.5
                    if isinstance(saldo_adesoes, (int, float)):
                        max_por_orgao = min(max_por_orgao, float(saldo_adesoes))
                    max_por_orgao_txt = _qtd(max_por_orgao)
                except (TypeError, ValueError):
                    max_por_orgao_txt = "N/I"
                if isinstance(saldo_adesoes, (int, float)) and isinstance(qtd_limite_adesao, (int, float)) and qtd_limite_adesao:
                    usado_pct = (1 - float(saldo_adesoes) / float(qtd_limite_adesao)) * 100
                    saldo_txt = f"{_qtd(saldo_adesoes)} de {_qtd(qtd_limite_adesao)} ({usado_pct:.0f}% já usado)"
                else:
                    saldo_txt = _qtd(saldo_adesoes) if saldo_adesoes != "N/I" else "N/I"
                sicaf_txt = sicaf_por_cnpj.get(str(raw.get("niFornecedor") or ""), "N/I")
                sicaf_icone = "✅" if sicaf_txt.startswith("Ativo e habilitado") else ("⚠️" if sicaf_txt != "N/I" else "❔")

                # Vigência final (tentar nomes possíveis do campo na API 2)
                vigencia_final_raw = (
                    raw.get("dataVigenciaFinal")
                    or raw.get("dataFimVigencia")
                    or raw.get("dataVigenciaFinalAta")
                    or raw.get("dataFinalVigencia")
                    or raw.get("vigenciaFim")
                    or ""
                )
                if vigencia_final_raw:
                    try:
                        vigencia_dt = dt.fromisoformat(vigencia_final_raw.replace("Z", "+00:00"))
                        vigencia_final = vigencia_dt.strftime("%d/%m/%Y")
                    except Exception:
                        vigencia_final = str(vigencia_final_raw)[:10]
                else:
                    vigencia_final = "N/I"

                # ── Card visual da ata ──
                doc_session_key = f"docs_{identificador}_{idx}"
                doc_err_key = f"docs_err_{identificador}_{idx}"
                btn_key = f"btn_docs_{idx}_{identificador[:30]}"

                with st.container(border=True):
                    # Título da ata
                    st.markdown(f"**Ata {numero} • {unidade} (UASG {uasg_code})**")

                    # Link do fornecedor
                    if url:
                        st.markdown(
                            f'<a href="{url}" target="_blank" class="ata-fornecedor-link">'
                            f'Visualizar documento – {fornecedor}</a>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<span class="ata-fornecedor-link">Visualizar documento – {fornecedor}</span>',
                            unsafe_allow_html=True,
                        )

                    # Tags com todas as informações
                    st.markdown(
                        f"""<div class="ata-info-grid">
                            <span class="ata-tag">🔢 Item: {numero_item}</span>
                            <span class="ata-tag">🛒 Compra: {num_compra}</span>
                            <span class="ata-tag">🆔 ID Compra: {id_compra}</span>
                            <span class="ata-tag">📅 Vigência Final: {vigencia_final}</span>
                            <span class="ata-tag">📦 Saldo para adesão: {saldo_txt}</span>
                            <span class="ata-tag">🏛️ Máx. por órgão aderente: {max_por_orgao_txt}</span>
                            <span class="ata-tag">📋 Qtd. registrada: {_qtd(qtd_registrada)}</span>
                            <span class="ata-tag">🔄 Saldo Remanej.: {_qtd(saldo_remanejamento) if saldo_remanejamento != "N/I" else "N/I"}</span>
                            <span class="ata-tag">🤝 Aceita Adesão: {aceita_adesao}</span>
                            <span class="ata-tag">{sicaf_icone} SICAF do fornecedor: {sicaf_txt}</span>
                        </div>""",
                        unsafe_allow_html=True,
                    )

                    col_docs, col_ades, col_of = st.columns([1, 1, 1])
                    with col_of:
                        _desc_item = str(raw.get("descricaoItem") or raw.get("descricao") or "").strip()
                        _modalidade = str(raw.get("nomeModalidadeCompra") or "Pregão Eletrônico").strip()
                        _ano = str(raw.get("anoCompra") or "").strip()
                        st.button(
                            "🛒 Incluir na adesão", key=f"btn_of_{idx}_{identificador[:30]}",
                            on_click=_incluir_na_cesta,
                            args=({
                                "id": identificador, "ata": str(numero), "gerenciador": str(unidade), "uasg": str(uasg_code),
                                "licitacao": f"{_modalidade} nº {num_compra}" + (f"/{_ano}" if _ano and "/" not in num_compra else ""),
                            }, {
                                "Item": str(numero_item),
                                "Descrição": _desc_item or f"Item {numero_item}",
                                "Unidade": str(raw.get("unidadeFornecimento") or raw.get("siglaUnidadeFornecimento") or ""),
                                "codigo": str(raw.get("codigoItem") or ""),
                                "pdm": str(raw.get("codigoPdm") or ""),
                                "preco": _num(raw.get("valorUnitario")),
                                "max": _num(max_por_orgao_txt.replace(".", "").replace(",", ".")) if max_por_orgao_txt != "N/I" else None,
                                "Quantidade": "",
                            }),
                            help="Junta este item à lista de adesão (vários itens da mesma ata vão no mesmo ofício).",
                        )
                    with col_docs:
                        clicou_docs = st.button("📂 Outros Docs", key=btn_key)
                    with col_ades:
                        if st.button("📋 Adesões já aprovadas", key=f"btn_ades_{idx}_{identificador[:30]}"):
                            st.session_state[f"ades_{identificador}_{idx}"] = adesoes_aprovadas(
                                str(raw.get("numeroAtaRegistroPreco", "")),
                                str(raw.get("codigoUnidadeGerenciadora", "") or uasg_code),
                                str(numero_item),
                            )
                    _ades = st.session_state.get(f"ades_{identificador}_{idx}")
                    if _ades is not None:
                        _lista_ades, _erro_ades = _ades
                        if _erro_ades:
                            st.warning(f"Não foi possível consultar as adesões agora ({_erro_ades}).")
                        elif not _lista_ades:
                            st.caption("Nenhuma adesão aprovada para este item até agora.")
                        else:
                            st.dataframe(
                                [{"Órgão que aderiu": a.get("unidadeNaoParticipante", ""),
                                  "Quantidade aprovada": a.get("quantidadeAprovadaAdesao", ""),
                                  "Aprovada em": str(a.get("dataAprovacaoAnalise", ""))[:10]} for a in _lista_ades],
                                use_container_width=True, hide_index=True,
                            )
                    if clicou_docs:
                        with st.spinner("Buscando…"):
                            docs, erro = fetch_ata_documents(identificador)
                            st.session_state[doc_session_key] = docs
                            st.session_state[doc_err_key] = erro

                    # Documentos carregados
                    if doc_err_key in st.session_state and st.session_state[doc_err_key]:
                        st.warning(st.session_state[doc_err_key])

                    if doc_session_key in st.session_state:
                        # Filtrar docs do tipo "Ata de Registro de Preço" (já disponível via link do fornecedor)
                        docs = [
                            d for d in st.session_state[doc_session_key]
                            if "ata de registro" not in (d.get("tipoDocumentoNome") or "").lower()
                        ]
                        if docs:
                            doc_links_html = ""
                            for doc_idx, doc in enumerate(docs):
                                titulo = (
                                    doc.get("titulo")
                                    or doc.get("tituloDocumento")
                                    or doc.get("nomeArquivo")
                                    or doc.get("nome")
                                    or f"Documento {doc_idx + 1}"
                                )
                                tipo_doc = doc.get("tipoDocumentoNome", doc.get("tipoDocumento", doc.get("tipo", "")))
                                seq = doc.get("sequencialDocumento", doc.get("sequencial", doc_idx + 1))

                                # Evita links assinados expirados quando possível: usa endpoint canônico por origem.
                                origem = (doc.get("_origem") or "").lower()
                                if origem == "compra":
                                    base_url = build_compra_documents_url(identificador)
                                else:
                                    base_url = build_ata_documents_url(identificador)

                                doc_url = ""
                                if base_url and seq not in (None, ""):
                                    doc_url = f"{base_url}/{seq}"

                                if not doc_url:
                                    doc_url = doc.get("url") or doc.get("uri") or ""

                                if not doc_url:
                                    continue

                                badge = f'<span class="doc-badge">{tipo_doc}</span>' if tipo_doc else ""
                                doc_links_html += (
                                    f'<a href="{doc_url}" target="_blank" class="doc-pill">'
                                    f'📎 {titulo} {badge}</a>'
                                )
                            st.markdown(
                                f'<div class="doc-list-row">{doc_links_html}</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.caption("Nenhum documento adicional encontrado.")
elif start_button and tipo and codigo:
    st.info("Nenhuma ata encontrada para este critério.")
