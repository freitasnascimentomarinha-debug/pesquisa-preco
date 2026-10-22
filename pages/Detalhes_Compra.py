"""
Detalhes da Compra — AtaCotada
Busca contratos, documentos e dados de compras via APIs públicas
(ComprasGov + PNCP) a partir de dados da Cotação.
"""

import base64
import json
import threading
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from html import escape as _e
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import pandas as pd
import requests
import streamlit as st
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

try:
    from servicos_publicos import dados_uasg, gerar_excel, http_get_json, limpar_cnpj
except ImportError:  # após uma atualização do código o servidor pode manter a versão antiga do módulo em memória
    import importlib
    import servicos_publicos
    importlib.reload(servicos_publicos)
    from servicos_publicos import dados_uasg, gerar_excel, http_get_json, limpar_cnpj

# ── Caminhos ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões")

# ── Constantes API ─────────────────────────────────────────────────────────
COMPRASGOV_BASE = "https://dadosabertos.compras.gov.br"
PNCP_API_BASE = "https://pncp.gov.br/pncp-api/v1"
PNCP_API_BASE_NEW = "https://pncp.gov.br/api/consulta/v1"
PNCP_PORTAL_BASE = "https://pncp.gov.br/app/editais"
COMPRASNET_BASE = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/landing"
COMPRASNET_FASE_EXTERNA_BASE = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-fase-externa/v1"
REQUEST_TIMEOUT = 20
MAX_RETRIES = 1

# ── Config Streamlit ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="AtaCotada - Detalhes da Compra",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (mesmo padrão visual do app) ──────────────────────────────────────
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
        padding: 2rem; border-radius: 10px; margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center;
    }
    .logo-text { color: #fff; font-size: 14px; font-weight: 600; letter-spacing: 2px; margin-bottom: .5rem; }
    .sistema-nome { color: #d4af37; font-size: 48px; font-weight: bold; letter-spacing: 3px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin: .5rem 0; font-family: 'Arial Black', sans-serif; }
    .subtitulo { color: #fff; font-size: 14px; margin-top: .5rem; letter-spacing: 1px; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #111 50%, #0a0a0a 100%) !important;
        border-right: 3px solid #d4af37 !important;
    }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #d4af37 !important; font-family: 'Arial Black', sans-serif;
        font-size: 22px; text-align: center; letter-spacing: 2px;
        border-bottom: 2px solid #d4af37; padding-bottom: .75rem; margin-bottom: 1.5rem;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%) !important;
        color: #fff !important; border: 1px solid #333 !important;
        border-radius: 8px !important; margin: .2rem 0 !important;
        padding: .45rem .7rem !important; font-weight: 600 !important;
        font-size: 12.5px !important; line-height: 1.2 !important;
        min-height: 0 !important; transition: all .3s ease !important;
        text-decoration: none !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span { color: #fff !important; }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background: linear-gradient(135deg, #252525 0%, #353535 100%) !important;
        border: 1px solid #d4af37 !important; transform: translateX(5px);
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover span { color: #d4af37 !important; }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
        color: #0a0a0a !important; border: 1px solid #d4af37 !important; font-weight: bold !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span { color: #0a0a0a !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fff !important; }
    .sidebar-footer { color: #666; font-size: 11px; text-align: center; padding: 1rem 0;
        border-top: 1px solid #333; margin-top: 2rem; }

    /* Cards */
    .info-card {
        background: linear-gradient(135deg, rgba(7, 37, 92, 0.92) 0%, rgba(0, 82, 204, 0.78) 100%);
        border: 1px solid rgba(212,175,55,0.42);
        border-radius: 14px; padding: 1.05rem 1.35rem; margin-bottom: .9rem;
        box-shadow: 0 10px 28px rgba(0,0,0,0.28);
        backdrop-filter: blur(4px);
    }
    .info-card h4 { color: #d4af37; margin: 0 0 .5rem 0; font-size: 1rem; }
    .info-card p { color: #cbd5e1; margin: .15rem 0; font-size: .9rem; }
    .info-card a { color: #d4af37 !important; text-decoration: none; font-weight: 600; }
    .info-card a:hover { color: #f0d060 !important; text-decoration: underline; }

    .lookup-panel {
        border-radius: 16px; padding: 1.2rem 1.35rem; margin: 1rem 0 1.1rem 0;
        border: 1px solid rgba(212,175,55,0.35);
        box-shadow: 0 14px 30px rgba(0,0,0,0.24);
    }
    .lookup-panel.success {
        background: linear-gradient(135deg, rgba(10, 58, 38, 0.96) 0%, rgba(13, 110, 75, 0.86) 100%);
    }
    .lookup-panel.warning {
        background: linear-gradient(135deg, rgba(92, 45, 7, 0.96) 0%, rgba(156, 87, 17, 0.84) 100%);
    }
    .lookup-title {
        color: #ffffff; font-size: 1.08rem; font-weight: 700; margin-bottom: .45rem;
    }
    .lookup-text {
        color: #f8fafc; font-size: .95rem; line-height: 1.55; margin: .15rem 0;
    }
    .lookup-meta {
        color: #fde68a; font-size: .82rem; letter-spacing: .04em; text-transform: uppercase;
        margin-top: .55rem;
    }

    .doc-card {
        background: rgba(0, 26, 77, 0.45); border: 1px solid rgba(212,175,55,0.2);
        border-radius: 10px; padding: .8rem 1rem; margin-bottom: .5rem;
    }
    .doc-card a { color: #d4af37 !important; font-weight: 600; text-decoration: none; }
    .doc-card a:hover { color: #f0d060 !important; text-decoration: underline; }
    .doc-badge {
        background: rgba(212,175,55,0.15); border-radius: 4px;
        padding: .1rem .4rem; font-size: .75rem; color: #d4af37; font-weight: 500;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #d4af37 !important; color: #fff !important;
        border: none !important; font-weight: bold !important;
    }
    .stButton > button[kind="primary"]:hover { background-color: #c5a028 !important; }

    /* Botão amarelo para carregar mais ARPs */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background-color: #d4af37 !important; color: #000 !important;
        border: 2px solid #d4af37 !important; font-weight: bold !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background-color: #f0d060 !important; border-color: #f0d060 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
_acanto_path = os.path.join(DATA_DIR, "acanto.png")
_acanto_b64 = None
if os.path.exists(_acanto_path):
    with open(_acanto_path, "rb") as _f:
        _acanto_b64 = base64.b64encode(_f.read()).decode()

with st.sidebar:
    if _acanto_b64:
        st.markdown(
            f'<div style="text-align:center;padding:1rem 0 0.5rem 0;">'
            f'<img src="data:image/png;base64,{_acanto_b64}" style="max-width:70%;height:auto;"></div>',
            unsafe_allow_html=True,
        )
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
    st.markdown(
        '<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;'
        'padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br><span style="color:#d4af37;">AtaCotada V2.0</span></div>', unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid],[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#facc15,#eab308)!important;border:1px solid #fde047!important;box-shadow:0 0 14px rgba(250,204,21,.55)!important}[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid] *{background:transparent!important;color:#111!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid],[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#ef4444,#b91c1c)!important;border:1px solid #fca5a5!important;box-shadow:0 0 14px rgba(239,68,68,.55)!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid],[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#25d366,#128c7e)!important;border:1px solid #86efac!important;box-shadow:0 0 14px rgba(37,211,102,.5)!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}</style>', unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <div class="logo-text">⚓ MARINHA DO BRASIL ⚓</div>
    <div class="sistema-nome">AtaCotada</div>
    <div class="subtitulo">Detalhes da Compra</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def _api_get(url: str, timeout: int = REQUEST_TIMEOUT) -> Optional[Any]:
    """GET em JSON (cliente compartilhado, com retry). Se a API antiga do PNCP falhar, tenta a nova URL uma única vez."""
    dados, erro = http_get_json(url, timeout=timeout, tentativas=MAX_RETRIES + 1, ok_404=True)
    if dados is None and erro and PNCP_API_BASE in url:
        dados, _ = http_get_json(url.replace(PNCP_API_BASE, PNCP_API_BASE_NEW), timeout=12, tentativas=1, ok_404=True)
    return dados


def parse_pncp_control(ctrl: str) -> Optional[Tuple[str, str, str]]:
    """Extrai (cnpj, ano, sequencial) de um numeroControlePncp.
    Ex: '32479123000143-1-000006/2026' → ('32479123000143', '2026', '000006')
    """
    if not ctrl:
        return None
    m = re.match(r"(\d{14})-\d+-(\d+)/(\d{4})", ctrl)
    if m:
        return m.group(1), m.group(3), m.group(2)
    return None


def build_comprasnet_link(id_compra: str) -> str:
    """Gera link direto para o ComprasNet a partir do idCompra."""
    return f"{COMPRASNET_BASE}?destino=acompanhamento-compra&compra={id_compra}"


def build_pncp_portal_link(cnpj: str, ano: str, seq: str) -> str:
    """Gera link para o portal PNCP."""
    seq_int = str(int(seq))
    return f"{PNCP_PORTAL_BASE}/{cnpj}/{ano}/{seq_int}"


@st.cache_data(ttl=300, show_spinner=False)
def resolver_publicacao_pncp_por_id(id_compra: str, codigo_uasg: str = "") -> Dict[str, Any]:
    """Valida se um ID de compra possui links externos úteis em ComprasNet e/ou PNCP."""
    parsed = parse_id_compra(id_compra)
    if not parsed:
        return {"status": "invalid", "message": "ID da compra inválido."}

    uasg = normalize_id_compra(codigo_uasg) or parsed["uasg"]
    ano = parsed["ano"]
    seq = parsed["sequencial"]
    comprasnet_status = buscar_link_compra_fase_externa(id_compra)
    comprasnet_link = comprasnet_status.get("link", "") if comprasnet_status.get("status") == "found" else ""
    cnpj_lookup = buscar_cnpj_orgao_por_uasg(uasg, int(ano))
    cnpj = normalize_id_compra(cnpj_lookup.get("cnpj", ""))
    if len(cnpj) != 14:
        if comprasnet_link:
            return {
                "status": "found-comprasnet",
                "message": "Compra localizada em link externo do ComprasNet.",
                "uasg": uasg,
                "ano": ano,
                "seq": seq,
                "comprasnet_url": comprasnet_link,
            }
        return {
            "status": "orgao-not-found",
            "message": "Não foi possível identificar um CNPJ de órgão confiável para esta UASG e não há publicação externa válida para o ID.",
            "uasg": uasg,
            "ano": ano,
            "seq": seq,
            "attempts": cnpj_lookup.get("attempts", []),
        }

    compra = buscar_compra_pncp(cnpj, ano, seq)
    if not compra:
        if comprasnet_link:
            return {
                "status": "found-comprasnet",
                "message": "Compra localizada em link externo do ComprasNet, mas sem publicação de detalhe no PNCP.",
                "uasg": uasg,
                "ano": ano,
                "seq": seq,
                "cnpj": cnpj,
                "comprasnet_url": comprasnet_link,
            }
        return {
            "status": "not-found",
            "message": "O PNCP não retornou publicação para o sequencial extraído do ID e nenhum link externo válido foi confirmado.",
            "uasg": uasg,
            "ano": ano,
            "seq": seq,
            "cnpj": cnpj,
        }

    return {
        "status": "found-both" if comprasnet_link else "found-pncp",
        "message": "Publicação localizada no PNCP.",
        "uasg": uasg,
        "ano": ano,
        "seq": seq,
        "cnpj": cnpj,
        "compra": compra,
        "portal_url": build_pncp_portal_link(cnpj, ano, seq),
        "comprasnet_url": comprasnet_link,
    }


def normalize_id_compra(raw_value: Any) -> str:
    """Normaliza o ID da compra mantendo apenas dígitos para comparação."""
    if raw_value is None:
        return ""
    return re.sub(r"\D", "", str(raw_value))


def parse_id_compra(id_compra: str) -> Optional[Dict[str, str]]:
    """Extrai componentes conhecidos do ID da compra.

    Formato esperado: UASG(6) + modalidade(2) + sequencial(5) + ano(4).
    """
    normalized = normalize_id_compra(id_compra)
    if len(normalized) != 17:
        return None
    return {
        "uasg": normalized[:6],
        "modalidade": normalized[6:8],
        "sequencial": normalized[8:13],
        "ano": normalized[13:17],
    }


def dedupe_by_keys(items: List[Dict], keys: List[str]) -> List[Dict]:
    """Remove duplicados de listas de dicionários usando chaves candidatas."""
    seen = set()
    deduped: List[Dict] = []
    for item in items:
        item_key = ""
        for key in keys:
            value = item.get(key)
            if value:
                item_key = str(value)
                break
        if not item_key:
            item_key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if item_key in seen:
            continue
        seen.add(item_key)
        deduped.append(item)
    return deduped


@st.cache_data(ttl=300, show_spinner=False)
def buscar_link_compra_fase_externa(id_compra: str) -> Dict[str, str]:
    """Consulta a API pública de fase externa do ComprasNet para uma compra."""
    normalized = normalize_id_compra(id_compra)
    if not normalized:
        return {"status": "invalid", "message": "ID da compra inválido."}

    url = f"{COMPRASNET_FASE_EXTERNA_BASE}/compras/{normalized}/link"
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"},
            verify=True,
        )
        if response.status_code == 200:
            return {
                "status": "found",
                "link": response.text.strip(),
                "message": "Compra localizada na fase externa pública do ComprasNet.",
            }
        if response.status_code == 404:
            try:
                payload = response.json()
                message = payload.get("message", "Compra não encontrada.")
            except Exception:
                message = "Compra não encontrada."
            return {"status": "not-found", "message": message}
        return {
            "status": "error",
            "message": f"A API pública do ComprasNet respondeu com status {response.status_code}.",
        }
    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "message": "A consulta pública do ComprasNet demorou além do limite.",
        }
    except requests.exceptions.RequestException:
        return {
            "status": "error",
            "message": "Não foi possível consultar a API pública do ComprasNet no momento.",
        }


@st.cache_data(ttl=300, show_spinner=False)
def buscar_cnpj_orgao_por_uasg(codigo_uasg: str, ano: int) -> Dict[str, Any]:
    """Tenta obter o CNPJ do órgão a partir da UASG usando endpoints públicos conhecidos."""
    headers = {"User-Agent": "Mozilla/5.0"}
    attempts = []
    codigo_uasg_limpo = normalize_id_compra(codigo_uasg)
    endpoints = [
        (
            "material",
            f"{COMPRASGOV_BASE}/modulo-pesquisa-preco/1_consultarMaterial",
        ),
        (
            "servico",
            f"{COMPRASGOV_BASE}/modulo-pesquisa-preco/3_consultarServico",
        ),
    ]

    for label, base_url in endpoints:
        params = {
            "codigoUasg": codigo_uasg_limpo,
            "dataCompraInicio": f"{ano}-01-01",
            "dataCompraFim": f"{ano}-12-31",
            "pagina": 1,
            "tamanhoPagina": 10,
        }
        try:
            response = requests.get(
                base_url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers=headers,
                verify=True,
            )
            attempt: Dict[str, Any] = {
                "fonte": label,
                "status": response.status_code,
                "url": response.url,
            }
            if "json" in response.headers.get("content-type", ""):
                data = response.json()
                if isinstance(data, dict):
                    attempt["message"] = data.get("message")
                    for item in data.get("resultado", []):
                        ni = item.get("niOrgao", "")
                        if ni and len(str(ni)) == 14:
                            attempt["cnpj"] = str(ni)
                            attempts.append(attempt)
                            return {
                                "cnpj": str(ni),
                                "attempts": attempts,
                                "status": "found",
                            }
            else:
                attempt["message"] = response.text[:200]
            attempts.append(attempt)
        except requests.exceptions.Timeout:
            attempts.append({"fonte": label, "status": "timeout"})
        except requests.exceptions.RequestException as exc:
            attempts.append({"fonte": label, "status": "error", "message": str(exc)})

    uasg_info = load_uasg_index().get(codigo_uasg_limpo, {})
    nome_uasg = str(uasg_info.get("nomeUasg", "") or "").strip()
    queries: List[str] = []
    if nome_uasg:
        queries.append(nome_uasg)
        nome_sem_prefixo = re.sub(r"^[A-Z]{2,6}-", "", nome_uasg).strip()
        if nome_sem_prefixo and nome_sem_prefixo not in queries:
            queries.append(nome_sem_prefixo)
        tokens = re.findall(r"[A-Z0-9À-ÿ]{3,}", nome_uasg.upper())
        resumo = " ".join(tokens[:6]).strip()
        if resumo and resumo not in queries:
            queries.append(resumo)

    if codigo_uasg_limpo and codigo_uasg_limpo not in queries:
        queries.append(codigo_uasg_limpo)

    for query in queries:
        for tipo_documento in ("contrato", "ata", "compra"):
            for pagina in range(1, 4):
                params = {
                    "q": query,
                    "tipos_documento": tipo_documento,
                    "pagina": pagina,
                    "ordenacao": "-data",
                }
                try:
                    response = requests.get(
                        "https://pncp.gov.br/api/search/",
                        params=params,
                        timeout=REQUEST_TIMEOUT,
                        headers=headers,
                        verify=True,
                    )
                    attempt = {
                        "fonte": f"pncp-search:{tipo_documento}",
                        "status": response.status_code,
                        "query": query,
                        "pagina": pagina,
                    }
                    if response.status_code != 200:
                        attempt["message"] = response.text[:200]
                        attempts.append(attempt)
                        break

                    data = response.json()
                    items = data.get("items", []) if isinstance(data, dict) else []
                    attempt["total"] = data.get("total", len(items)) if isinstance(data, dict) else len(items)
                    if not items:
                        attempts.append(attempt)
                        break

                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        unidade_codigo = normalize_id_compra(item.get("unidade_codigo", ""))
                        item_ano = str(item.get("ano", "") or "")
                        cnpj = normalize_id_compra(item.get("orgao_cnpj", ""))
                        if unidade_codigo != codigo_uasg_limpo:
                            continue
                        if item_ano and str(ano) and item_ano != str(ano):
                            continue
                        if len(cnpj) != 14:
                            continue

                        attempt["cnpj"] = cnpj
                        attempt["title"] = item.get("title", "")
                        attempts.append(attempt)
                        return {
                            "cnpj": cnpj,
                            "attempts": attempts,
                            "status": "found-search",
                            "evidence": {
                                "query": query,
                                "tipo_documento": tipo_documento,
                                "title": item.get("title", ""),
                                "orgao_nome": item.get("orgao_nome", ""),
                                "unidade_codigo": item.get("unidade_codigo", ""),
                                "unidade_nome": item.get("unidade_nome", ""),
                                "item_url": item.get("item_url", ""),
                            },
                        }

                    attempts.append(attempt)
                except requests.exceptions.Timeout:
                    attempts.append({
                        "fonte": f"pncp-search:{tipo_documento}",
                        "status": "timeout",
                        "query": query,
                        "pagina": pagina,
                    })
                except requests.exceptions.RequestException as exc:
                    attempts.append({
                        "fonte": f"pncp-search:{tipo_documento}",
                        "status": "error",
                        "query": query,
                        "pagina": pagina,
                        "message": str(exc),
                    })

    return {"cnpj": "", "attempts": attempts, "status": "not-found"}


# ── API ComprasGov: Contratos ──────────────────────────────────────────────

def _paginar_comprasgov(caminho: str, params: Dict[str, Any], max_paginas: int = 10) -> List[Dict]:
    """Percorre as páginas (500 registros cada) de um endpoint do Dados Abertos do Compras.gov.br."""
    registros: List[Dict] = []
    for pagina in range(1, max_paginas + 1):
        data = _api_get(f"{COMPRASGOV_BASE}/{caminho}?{urlencode({**params, 'pagina': pagina, 'tamanhoPagina': 500})}")
        if not (data and isinstance(data, dict)):
            break
        registros.extend(data.get("resultado", []) or [])
        if pagina >= (data.get("totalPaginas") or 1):
            break
    return registros


@st.cache_data(ttl=300, show_spinner=False)
def buscar_contratos_uasg(codigo_uasg: str, ano: int, versao: int = 2) -> List[Dict]:
    """Contratos de uma UASG (modulo-contratos). A API exige o código do órgão, obtido do cadastro da UASG."""
    uasg, _erro = dados_uasg(codigo_uasg)
    if not uasg or not uasg.get("codigoOrgao"):
        return []
    return _paginar_comprasgov("modulo-contratos/1_consultarContratos", {
        "codigoOrgao": uasg["codigoOrgao"],
        "codigoUnidadeGestora": codigo_uasg,
        "dataVigenciaInicialMin": f"{ano}-01-01",
        "dataVigenciaInicialMax": f"{ano}-12-31",
    })


# ── API ComprasGov: ARP (SRP) ─────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def buscar_arp_uasg(codigo_uasg: str, ano: int, versao: int = 2) -> List[Dict]:
    """Atas de Registro de Preço de uma UASG (todas as páginas)."""
    return _paginar_comprasgov("modulo-arp/1_consultarARP", {
        "codigoUnidadeGerenciadora": codigo_uasg,
        "dataVigenciaInicialMin": f"{ano}-01-01",
        "dataVigenciaInicialMax": f"{ano}-12-31",
    })


# ── API PNCP ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def buscar_compra_pncp(cnpj: str, ano: str, seq: str) -> Optional[Dict]:
    """Busca detalhes de uma compra no PNCP."""
    url = f"{PNCP_API_BASE}/orgaos/{cnpj}/compras/{ano}/{seq}"
    return _api_get(url)


@st.cache_data(ttl=300, show_spinner=False)
def buscar_documentos_pncp(cnpj: str, ano: str, seq: str) -> List[Dict]:
    """Busca documentos/arquivos de uma compra no PNCP."""
    url = f"{PNCP_API_BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos"
    data = _api_get(url)
    if isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_itens_pncp(cnpj: str, ano: str, seq: str) -> List[Dict]:
    """Busca itens de uma compra no PNCP."""
    url = f"{PNCP_API_BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/itens"
    data = _api_get(url)
    if isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_resultado_item_pncp(cnpj: str, ano: str, seq: str, num_item: int) -> List[Dict]:
    """Busca resultado (fornecedor vencedor) de um item no PNCP."""
    url = f"{PNCP_API_BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/itens/{num_item}/resultados"
    data = _api_get(url)
    if isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_atas_pncp(cnpj: str, ano: str, seq: str) -> List[Dict]:
    """Busca atas de registro de preço de uma compra no PNCP."""
    url = f"{PNCP_API_BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/atas"
    data = _api_get(url)
    if isinstance(data, list):
        return data
    return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_documentos_ata_pncp(cnpj: str, ano_compra: str, seq_compra: str, seq_ata: str) -> List[Dict]:
    """Busca documentos de uma ata específica no PNCP."""
    url = f"{PNCP_API_BASE}/orgaos/{cnpj}/compras/{ano_compra}/{seq_compra}/atas/{seq_ata}/arquivos"
    data = _api_get(url)
    if isinstance(data, list):
        return data
    return []


# ── API PNCP: Contratos por Contratação ───────────────────────────────────


# ── UASG Index ─────────────────────────────────────────────────────────────

@st.cache_data
def load_uasg_index() -> Dict[str, Dict]:
    path = os.path.join(DATA_DIR, "uasgs.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            data = json.load(f)
    return {str(e.get("codigoUasg", "")).strip(): e for e in data if e.get("codigoUasg")}


def executar_em_paralelo(funcoes: List[Any], max_workers: int = 8) -> List[Any]:
    """Executa funções sem argumentos ao mesmo tempo e devolve os resultados na mesma ordem
    (o contexto do Streamlit é repassado às threads para o cache continuar funcionando)."""
    if not funcoes:
        return []
    ctx = get_script_run_ctx()

    def _rodar(funcao):
        add_script_run_ctx(threading.current_thread(), ctx)
        return funcao()

    with ThreadPoolExecutor(max_workers=min(max_workers, len(funcoes))) as pool:
        return list(pool.map(_rodar, funcoes))


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower()) if unicodedata.category(c) != "Mn")


def buscar_uasg_por_nome(consulta: str, limite: int = 40) -> List[Dict]:
    """UASGs do cadastro local cujo nome (ou código) contém todas as palavras digitadas, sem considerar acentos."""
    termos = _sem_acento(consulta).split()
    if not termos:
        return []
    achados = []
    for codigo, info in load_uasg_index().items():
        alvo = _sem_acento(f"{codigo} {info.get('nomeUasg', '')} {info.get('siglaUf', '')}")
        if all(t in alvo for t in termos):
            achados.append({"codigo": codigo, "nome": str(info.get("nomeUasg", "")), "uf": str(info.get("siglaUf", ""))})
            if len(achados) >= limite:
                break
    return achados


def _usar_uasg(codigo: str):
    st.session_state["dc_uasg"] = codigo


def resumo_desagio(itens: List[Dict], resultados_por_item: Dict[Any, List[Dict]]) -> Dict[str, Any]:
    """Estimado x homologado dos itens que têm resultado (ignora itens sem valor estimado, como os sigilosos)."""
    estimado = homologado = 0.0
    contados = 0
    for it in itens:
        resultados = resultados_por_item.get(it.get("numeroItem"), [])
        valor_est = it.get("valorTotal") or 0
        valor_hom = sum((r.get("valorTotalHomologado") or 0) for r in resultados)
        if valor_est and valor_hom:
            estimado += valor_est
            homologado += valor_hom
            contados += 1
    return {"itens": contados, "estimado": estimado, "homologado": homologado,
            "desagio": ((estimado - homologado) / estimado * 100) if estimado else None}


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE RENDERIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def render_documentos(docs: List[Dict], titulo: str = "Documentos"):
    """Renderiza lista de documentos com links de download."""
    if not docs:
        return
    st.markdown(f"**📎 {titulo}** ({len(docs)} arquivo{'s' if len(docs) > 1 else ''})")
    for doc in docs:
        titulo_doc = doc.get("titulo", "Documento sem título")
        tipo = doc.get("tipoDocumentoNome", doc.get("tipoDocumentoDescricao", ""))
        url_doc = doc.get("url", doc.get("uri", ""))
        badge = f' <span class="doc-badge">{_e(str(tipo))}</span>' if tipo else ""
        st.markdown(
            f'<div class="doc-card">'
            f'<a href="{_e(str(url_doc), quote=True)}" target="_blank">📥 {_e(str(titulo_doc))}</a>{badge}'
            f"</div>",
            unsafe_allow_html=True,
        )


def render_links_externos(id_compra: str, cnpj: str = "", ano: str = "", seq: str = ""):
    """Renderiza links para ComprasNet e PNCP Portal."""
    links_html = ""
    if id_compra:
        cnet = build_comprasnet_link(id_compra)
        links_html += f'<p>🔗 <a href="{cnet}" target="_blank">Abrir no ComprasNet</a></p>'
    if cnpj and ano and seq:
        portal = build_pncp_portal_link(cnpj, ano, seq)
        links_html += f'<p>🔗 <a href="{portal}" target="_blank">Abrir no PNCP</a></p>'
    if links_html:
        st.markdown(f'<div class="info-card"><h4>🌐 Links Externos</h4>{links_html}</div>', unsafe_allow_html=True)


def render_resultado_id_pncp(resultado: Dict[str, Any], id_compra: str, nome_uasg: str, uf: str = ""):
    """Exibe o resultado da validação de um ID de compra em links externos."""
    parsed = parse_id_compra(id_compra) or {}
    nome_uasg = _e(str(nome_uasg))
    uf = _e(str(uf))
    cnpj_info = _e(str(resultado.get("cnpj") or "N/I"))
    base_info = (
        f"<div class='lookup-meta'>UASG {parsed.get('uasg', 'N/I')}"
        f" • Sequencial {parsed.get('sequencial', 'N/I')} • Ano {parsed.get('ano', 'N/I')}</div>"
    )

    if resultado.get("status") in {"found-pncp", "found-both"}:
        compra = resultado.get("compra", {}) or {}
        objeto = _e(str(compra.get("objetoCompra", "") or "Objeto não informado"))
        modalidade = _e(str(compra.get("modalidadeNome", "Publicação encontrada") or "Publicação encontrada"))
        orgao = compra.get("orgaoEntidade", {}) or {}
        orgao_nome = _e(str(orgao.get("razaoSocial", "") or nome_uasg))
        st.markdown(
            f"""
            <div class="lookup-panel success">
                <div class="lookup-title">PNCP localizado para o ID {normalize_id_compra(id_compra)}</div>
                <div class="lookup-text"><strong>{modalidade}</strong></div>
                <div class="lookup-text">{objeto}</div>
                <div class="lookup-text"><strong>Órgão:</strong> {orgao_nome}</div>
                <div class="lookup-text"><strong>UASG:</strong> {nome_uasg}{' — ' + uf if uf else ''}</div>
                <div class="lookup-text"><strong>CNPJ:</strong> {cnpj_info}</div>
                {base_info}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if resultado.get("portal_url"):
            st.link_button("🔗 Abrir publicação no PNCP", resultado.get("portal_url", ""), use_container_width=True)
        if resultado.get("comprasnet_url"):
            st.link_button("🔗 Abrir acompanhamento no ComprasNet", resultado.get("comprasnet_url", ""), use_container_width=True)
        return

    if resultado.get("status") == "found-comprasnet":
        st.markdown(
            f"""
            <div class="lookup-panel success">
                <div class="lookup-title">Link externo localizado para o ID {normalize_id_compra(id_compra)}</div>
                <div class="lookup-text">O ComprasNet possui uma página pública para este ID, mas o PNCP não retornou publicação de detalhe.</div>
                <div class="lookup-text"><strong>UASG:</strong> {nome_uasg}{' — ' + uf if uf else ''}</div>
                <div class="lookup-text"><strong>CNPJ:</strong> {cnpj_info}</div>
                {base_info}
            </div>
            """,
            unsafe_allow_html=True,
        )
        if resultado.get("comprasnet_url"):
            st.link_button("🔗 Abrir acompanhamento no ComprasNet", resultado.get("comprasnet_url", ""), use_container_width=True)
        return

    motivo = _e(str(resultado.get("message", "Nenhuma publicação do PNCP foi encontrada para este ID.")))
    st.markdown(
        f"""
        <div class="lookup-panel warning">
            <div class="lookup-title">Nenhum link externo válido encontrado para o ID {normalize_id_compra(id_compra)}</div>
            <div class="lookup-text">{motivo}</div>
            <div class="lookup-text"><strong>UASG:</strong> {nome_uasg}{' — ' + uf if uf else ''}</div>
            {base_info}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _fmt_valor(valor) -> str:
    """Formata valor monetário."""
    if valor is None or valor == "":
        return "N/I"
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(valor)


def _fmt_data(data_str: str) -> str:
    """Formata data ISO para dd/mm/yyyy."""
    if not data_str:
        return ""
    try:
        return datetime.strptime(data_str[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return data_str[:10] if data_str else ""


def botao_consultar_fornecedor(cnpj: str, chave: str):
    """Abre a página Consulta CNPJ já com o fornecedor preenchido e a consulta executada."""
    digitos = limpar_cnpj(cnpj)
    if len(digitos) == 14 and st.button("🏢 Consultar fornecedor", key=f"forn_{chave}", help="Abre a página Consulta CNPJ com este fornecedor"):
        st.session_state["_cons_prefill"] = digitos
        st.switch_page("pages/Consulta.py")


def render_contrato(contrato: Dict, chave: str = ""):
    """Renderiza card de um contrato do ComprasGov."""
    numero = contrato.get("numeroContrato", "N/I")
    fornecedor = contrato.get("nomeRazaoSocialFornecedor", "N/I")
    cnpj_forn = contrato.get("niFornecedor", "")
    modalidade = contrato.get("nomeModalidadeCompra", "N/I")
    numero_compra = contrato.get("numeroCompra", "")
    tipo = contrato.get("nomeTipo", "")
    objeto = contrato.get("objeto", "N/I")
    valor = contrato.get("valorGlobal", "")
    processo = contrato.get("processo", "")
    id_compra = contrato.get("idCompra", "")
    ctrl_pncp = contrato.get("numeroControlePncpCompra", "")
    data_vig_ini = _fmt_data(contrato.get("dataVigenciaInicial", ""))
    data_vig_fim = _fmt_data(contrato.get("dataVigenciaFinal", ""))

    vigencia = f"{data_vig_ini} a {data_vig_fim}" if data_vig_ini else "N/I"
    licitacao = modalidade
    if numero_compra:
        licitacao += f" nº {numero_compra}"
    tipo_label = f" ({tipo})" if tipo else ""

    col_info, col_valores = st.columns([3, 1])
    with col_info:
        st.markdown(f"##### 📋 Contrato: {numero}{tipo_label}")
        st.markdown(f"**Licitação:** {licitacao}")
        st.markdown(f"**Fornecedor:** {fornecedor} ({cnpj_forn})")
        st.markdown(f"**Objeto:** {objeto}")
        st.markdown(f"**Processo:** {processo}")
    with col_valores:
        st.metric("Valor Global", _fmt_valor(valor))
        st.caption(f"Vigência: {vigencia}")
        if id_compra:
            st.caption(f"ID: {id_compra}")
    botao_consultar_fornecedor(cnpj_forn, f"c_{chave}")

    return ctrl_pncp, id_compra


def render_arp(ata: Dict, chave: str = ""):
    """Renderiza card de uma ARP com informações completas."""
    numero_ata = ata.get("numeroAtaRegistroPreco", "N/I")
    fornecedor = ata.get("nomeRazaoSocialFornecedor", "N/I")
    cnpj_forn = ata.get("niFornecedor", "")
    id_compra = ata.get("idCompra", "")
    ctrl_ata = ata.get("numeroControlePncpAta", "")
    ctrl_compra = ata.get("numeroControlePncpCompra", "")
    modalidade = ata.get("nomeModalidadeCompra", "")
    numero_compra = ata.get("numeroCompra", "")
    data_vig_ini = _fmt_data(ata.get("dataVigenciaInicial", ata.get("dataVigenciaInicio", "")))
    data_vig_fim = _fmt_data(ata.get("dataVigenciaFinal", ata.get("dataVigenciaFim", "")))
    data_assinatura = _fmt_data(ata.get("dataAssinatura", ""))
    situacao = ata.get("situacao", ata.get("statusAta", ""))
    objeto = ata.get("objeto", "")
    valor_total = ata.get("valorTotal", "")
    qtd_itens = ata.get("quantidadeItens", "")
    nome_orgao = ata.get("nomeOrgao", ata.get("nomeUnidadeGerenciadora", ""))
    link_ata_pncp = ata.get("linkAtaPNCP", "")

    vigencia = f"{data_vig_ini} a {data_vig_fim}" if data_vig_ini else "N/I"
    licitacao = modalidade
    if numero_compra:
        licitacao += f" nº {numero_compra}"

    col_info, col_valores = st.columns([3, 1])
    with col_info:
        st.markdown(f"##### 📜 ARP: {numero_ata}")
        if objeto:
            st.markdown(f"**Objeto:** {objeto}")
        st.markdown(f"**Licitação:** {licitacao or 'N/I'}")
        if fornecedor and fornecedor != "N/I":
            st.markdown(f"**Fornecedor:** {fornecedor}" + (f" ({cnpj_forn})" if cnpj_forn else ""))
        if nome_orgao:
            st.caption(f"Órgão: {nome_orgao}")
    with col_valores:
        if situacao:
            st.info(f"📊 {situacao}")
        if valor_total:
            st.metric("Valor Total", _fmt_valor(valor_total))
        st.caption(f"Vigência: {vigencia}")
        if data_assinatura:
            st.caption(f"Assinatura: {data_assinatura}")
        if qtd_itens:
            st.caption(f"Itens: {qtd_itens}")

    # Links diretos
    col_l1, _, _ = st.columns([1, 1, 2])
    with col_l1:
        if link_ata_pncp:
            st.link_button("📄 Ata no PNCP", link_ata_pncp, use_container_width=True)
    botao_consultar_fornecedor(cnpj_forn, f"a_{chave}")

    return ctrl_compra, ctrl_ata, id_compra


def render_item_pncp(item: Dict, idx: int):
    """Renderiza um item PNCP de forma compacta."""
    desc = item.get("descricao", "Sem descrição")
    valor = item.get("valorUnitarioEstimado", "")
    qtd = item.get("quantidade", "")
    unidade = item.get("unidadeMedida", "")
    situacao = item.get("situacaoCompraItemNome", "")
    tipo = item.get("materialOuServicoNome", "")

    col_item, col_val = st.columns([4, 1])
    with col_item:
        st.markdown(f"**Item {idx}** — {desc}")
        st.caption(f"Tipo: {tipo} | Qtd: {qtd} {unidade} | Situação: {situacao}")
    with col_val:
        st.metric("Valor Unit. Est.", _fmt_valor(valor))


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

tab_busca, tab_portal = st.tabs(["🔍 Busca por UASG", "🌐 Portal Contratos.gov"])

# ── Aba Portal Contratos.gov ──────────────────────────────────────────────
with tab_portal:
    st.markdown(
        """
        <div class="info-card" style="text-align: center; padding: 2rem;">
            <h3 style="color: #d4af37;">🌐 Gerenciador de Contratos — Compras.gov.br</h3>
            <p style="color: #cbd5e1; margin: 1rem 0; font-size: 1rem; line-height: 1.6;">
                ⚠️ Algumas compras ou Notas de Empenho muito recentes podem não aparecer na pesquisa comum.<br>
                Acesse o <strong>Gerenciador de Contratos em tempo real</strong> do Compras.gov.br
                para verificar informações atualizadas de compras.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_l, col_btn, col_r = st.columns([1, 2, 1])
    with col_btn:
        st.link_button(
            "🔗 Acessar Gerenciador de Contratos",
            "https://contratos.sistema.gov.br/compras",
            use_container_width=True,
        )

# ── Aba Busca por UASG ───────────────────────────────────────────────────
with tab_busca:

    st.markdown("""
<div style="color: #d4af37; font-size: 20px; font-weight: bold; margin-bottom: .5rem;">
    🔍 Consultar Detalhes de Compras
</div>
<p style="color: #cbd5e1; font-size: .9rem; margin-bottom: 1.5rem;">
    Busca contratos, ARPs (SRP), documentos (TR, edital) e links no PNCP/ComprasNet
    a partir do código UASG. Você pode filtrar por ID da Compra para encontrar um registro específico.
</p>
""", unsafe_allow_html=True)

    # vindo da página Consulta CNPJ ("Ver detalhes"): preenche UASG/ano e já executa a busca
    _prefill = st.session_state.pop("_dc_prefill", None)
    if _prefill:
        st.session_state["dc_uasg"] = _prefill["uasg"]
        st.session_state["dc_ano"] = min(max(int(_prefill["ano"]), 2020), 2030)
        st.session_state["dc_id"] = ""
        st.session_state["_dc_active"] = True
        st.session_state["_dc_arps_shown"] = 3
        st.session_state["_dc_compras_shown"] = 5

    inferred_from_state = parse_id_compra(st.session_state.get("detalhe_id_compra", ""))
    default_uasg = st.session_state.get("detalhe_uasg", "") or (
        inferred_from_state["uasg"] if inferred_from_state else ""
    )
    default_year = datetime.now().year
    if inferred_from_state:
        try:
            default_year = int(inferred_from_state["ano"])
        except (TypeError, ValueError):
            pass

    st.session_state.setdefault("dc_uasg", default_uasg)
    st.session_state.setdefault("dc_ano", min(max(default_year, 2020), 2030))
    st.session_state.setdefault("dc_id", st.session_state.get("detalhe_id_compra", ""))

    with st.expander("🔎 Não sei o código — buscar UASG pelo nome do órgão", expanded=False):
        _nome_busca = st.text_input("Nome (ou parte do nome) do órgão/unidade", key="dc_busca_nome", placeholder="Ex: hospital naval, comando 1 distrito")
        if _nome_busca.strip():
            _achadas = buscar_uasg_por_nome(_nome_busca)
            if not _achadas:
                st.caption("Nenhuma UASG encontrada no cadastro local para esse nome.")
            else:
                _c_sel, _c_btn = st.columns([5, 1])
                with _c_sel:
                    _k = st.selectbox("UASG encontrada", range(len(_achadas)), key="dc_busca_sel", label_visibility="collapsed",
                                      format_func=lambda i: f"{_achadas[i]['codigo']} — {_achadas[i]['nome']}" + (f" ({_achadas[i]['uf']})" if _achadas[i]['uf'] else ""))
                with _c_btn:
                    st.button("Usar", key="dc_busca_usar", use_container_width=True, on_click=_usar_uasg, args=(_achadas[_k]["codigo"],))
                if len(_achadas) == 40:
                    st.caption("Mostrando as 40 primeiras — refine o nome para reduzir.")

    # ── Formulário de busca ───────────────────────────────────────────────────
    col_uasg, col_ano, col_id = st.columns([2, 1, 4])

    with col_uasg:
        input_uasg = st.text_input(
            "Código UASG",
            key="dc_uasg",
            placeholder="Ex: 153050, 771300",
            help="Código da Unidade Gestora (6 dígitos). Se você informar o ID da compra, a UASG pode ser preenchida automaticamente.",
        )

    with col_ano:
        input_ano = st.number_input(
            "Ano",
            min_value=2020,
            max_value=2030,
            key="dc_ano",
            help="Ano de vigência/referência. Quando o ID da compra é informado, o ano pode ser inferido automaticamente.",
        )

    with col_id:
        input_id_compra = st.text_input(
            "ID da Compra (opcional)",
            key="dc_id",
            placeholder="Ex: 15305006000142026",
            help="Se informado, filtra os resultados por esse ID específico.",
        )

    # ── Filtros avançados ─────────────────────────────────────────────────────
    with st.expander("🔧 Filtros Avançados", expanded=False):
        col_modal, col_obj = st.columns([1, 2])

        with col_modal:
            filtro_modalidade = st.multiselect(
                "Modalidade / Tipo",
                options=[
                    "ARP (Ata de Registro de Preços)",
                    "Pregão",
                    "Dispensa",
                    "Inexigibilidade",
                    "Concorrência",
                    "Tomada de Preços",
                    "Convite",
                    "Leilão",
                    "Diálogo Competitivo",
                ],
                default=[],
                help="Filtre por modalidade/tipo de compra. Deixe vazio para exibir todos.",
            )

        with col_obj:
            filtro_objeto = st.text_input(
                "Objeto (palavra-chave)",
                value="",
                placeholder="Ex: material de limpeza, notebook",
                help="Filtre contratos/ARPs cujo objeto contenha esta palavra-chave.",
            )

        col_forn, col_proc = st.columns(2)

        with col_forn:
            filtro_fornecedor = st.text_input(
                "Fornecedor (nome ou CNPJ)",
                value="",
                placeholder="Ex: Empresa XYZ ou 12345678000199",
                help="Filtre por nome ou CNPJ do fornecedor.",
            )

        with col_proc:
            filtro_processo = st.text_input(
                "Número do Processo",
                value="",
                placeholder="Ex: 63379.001234/2025",
                help="Filtre pelo número do processo administrativo.",
            )

        col_vig_ini, col_vig_fim = st.columns(2)
        with col_vig_ini:
            filtro_vigencia_inicio = st.date_input(
                "Período — Data Inicial",
                value=None,
                help="Início da janela de busca. Retorna compras executadas ou pregões vigentes que tenham intersecção com este período.",
            )
        with col_vig_fim:
            filtro_vigencia_fim = st.date_input(
                "Período — Data Final",
                value=None,
                help="Fim da janela de busca. Retorna compras executadas ou pregões vigentes que tenham intersecção com este período.",
            )

    consultar = st.button("🔍 Consultar", type="primary", use_container_width=True)

    # ── Preencher da Cotação (se veio por session_state) ──────────────────────
    if st.session_state.get("detalhe_uasg") and not input_uasg:
        input_uasg = st.session_state["detalhe_uasg"]
    if st.session_state.get("detalhe_id_compra") and not input_id_compra:
        input_id_compra = st.session_state["detalhe_id_compra"]

    parsed_id_compra = parse_id_compra(input_id_compra)
    if parsed_id_compra and not input_uasg:
        input_uasg = parsed_id_compra["uasg"]

    # ── Execução da busca ─────────────────────────────────────────────────────
    if consultar:
        valid_uasg = input_uasg and input_uasg.strip().isdigit()
        valid_id_only = bool(parsed_id_compra)
        if not valid_uasg and not valid_id_only:
            st.error("❌ Informe uma UASG válida ou um ID da compra válido para preencher a UASG automaticamente.")
            st.session_state.pop("_dc_active", None)
        else:
            st.session_state["_dc_active"] = True
            st.session_state["_dc_arps_shown"] = 3
            st.session_state["_dc_compras_shown"] = 5
            # Limpar flags de docs sob demanda da busca anterior
            for _k in list(st.session_state.keys()):
                if _k.startswith("_dc_arp_docs_"):
                    del st.session_state[_k]

    # Renderizar resultados (persiste entre reruns via cache + session_state)
    _dc_should_render = (
        st.session_state.get("_dc_active")
        and ((input_uasg and input_uasg.strip().isdigit()) or bool(parsed_id_compra))
    )
    if _dc_should_render:
        _dc_go = True  # nível extra para preservar recuo do bloco original
        if _dc_go:
            uasg = input_uasg.strip() if input_uasg and input_uasg.strip() else ""
            if not uasg and parsed_id_compra:
                uasg = parsed_id_compra["uasg"]
            ano = int(input_ano)
            id_filtro = input_id_compra.strip() if input_id_compra else ""
            anos_busca = [ano]

            # Info da UASG
            uasg_index = load_uasg_index()
            uasg_info = uasg_index.get(uasg, {})
            nome_uasg = uasg_info.get("nomeUasg", "")
            uf = uasg_info.get("siglaUf", "")
            if not nome_uasg:  # fora do cadastro local: consulta o cadastro oficial de UASGs
                _oficial, _ = dados_uasg(uasg)
                nome_uasg = (_oficial or {}).get("nomeUasg") or "UASG não encontrada no cadastro"
                uf = uf or (_oficial or {}).get("siglaUf", "")

            st.markdown(
                f'<div class="info-card"><h4>🏛️ UASG {_e(uasg)}</h4>'
                f'<p><strong>{_e(str(nome_uasg))}</strong>{" — " + _e(str(uf)) if uf else ""}</p></div>',
                unsafe_allow_html=True,
            )
            if parsed_id_compra:
                st.caption(
                    f"ID {normalize_id_compra(id_filtro)} detectado: UASG {parsed_id_compra['uasg']} | "
                    f"sequencial {parsed_id_compra['sequencial']} | ano {parsed_id_compra['ano']}"
                )
            if id_filtro:
                with st.spinner("Validando publicação externa no PNCP..."):
                    resultado_id = resolver_publicacao_pncp_por_id(id_filtro, uasg)
                render_resultado_id_pncp(resultado_id, id_filtro, nome_uasg, uf)
                st.stop()  # com ID da compra o resultado é o detalhamento direto; a listagem por UASG/ano abaixo não se aplica
            # ── 1. Buscar Contratos ───────────────────────────────────────────
            with st.spinner("Buscando contratos e Atas de Registro de Preço (SRP) no ComprasGov..."):
                _res_busca = executar_em_paralelo(
                    [lambda a=a: buscar_contratos_uasg(uasg, a) for a in anos_busca]
                    + [lambda a=a: buscar_arp_uasg(uasg, a) for a in anos_busca]
                )
            contratos = dedupe_by_keys([c for lote in _res_busca[:len(anos_busca)] for c in lote],
                                       ["numeroContrato", "idCompra", "numeroControlePncpCompra"])

            # ── 2. Buscar ARPs (SRP) ──────────────────────────────────────────
            arps = dedupe_by_keys([a for lote in _res_busca[len(anos_busca):] for a in lote],
                                  ["numeroAtaRegistroPreco", "idCompra", "numeroControlePncpAta"])

            # ── Filtros avançados aplicados nos resultados ────────────────────
            _modalidade_map = {
                "ARP (Ata de Registro de Preços)": ["arp", "srp", "registro de preço", "registro de precos"],
                "Pregão": ["pregão", "pregao"],
                "Dispensa": ["dispensa"],
                "Inexigibilidade": ["inexigibilidade"],
                "Concorrência": ["concorrência", "concorrencia"],
                "Tomada de Preços": ["tomada de preço", "tomada de preco"],
                "Convite": ["convite"],
                "Leilão": ["leilão", "leilao"],
                "Diálogo Competitivo": ["diálogo competitivo", "dialogo competitivo"],
            }

            def _match_modalidade(registro, filtros_selecionados):
                """Verifica se o registro corresponde a alguma das modalidades selecionadas."""
                if not filtros_selecionados:
                    return True
                modalidade = (registro.get("nomeModalidadeCompra", "") or "").lower()
                objeto = (registro.get("objeto", "") or "").lower()
                texto = modalidade + " " + objeto
                for filtro in filtros_selecionados:
                    termos = _modalidade_map.get(filtro, [])
                    for termo in termos:
                        if termo in texto:
                            return True
                return False

            def _match_texto(registro, campo, filtro_valor):
                """Verifica se o campo do registro contém o texto de filtro."""
                if not filtro_valor:
                    return True
                valor = (registro.get(campo, "") or "").lower()
                return filtro_valor.lower() in valor

            def _match_texto_campos(registro, campos, filtro_valor):
                """Verifica se qualquer campo informado contém o texto de filtro."""
                if not filtro_valor:
                    return True
                texto = " ".join((registro.get(campo, "") or "") for campo in campos).lower()
                return filtro_valor.lower() in texto

            def _match_fornecedor(registro, filtro_valor):
                """Verifica nome ou CNPJ do fornecedor."""
                if not filtro_valor:
                    return True
                fv = filtro_valor.lower()
                nome = (registro.get("nomeRazaoSocialFornecedor", "") or "").lower()
                cnpj = (registro.get("niFornecedor", "") or "").lower()
                return fv in nome or fv in cnpj

            def _match_vigencia(registro, vig_ini, vig_fim):
                """Verifica se a vigência do registro tem intersecção com a janela [vig_ini, vig_fim].

                Retorna True se qualquer parte da vigência do registro cair dentro do período.
                - Compras executadas dentro do período: vigência começou dentro da janela.
                - Pregões vigentes no período: vigência se sobrepõe à janela.
                """
                if not vig_ini and not vig_fim:
                    return True
                # Contratos usam dataVigenciaInicial/dataVigenciaFinal
                # ARPs usam dataVigenciaInicio/dataVigenciaFim
                data_ini_str = (
                    registro.get("dataVigenciaInicial")
                    or registro.get("dataVigenciaInicio")
                    or registro.get("dataResultadoCompra")
                    or ""
                )
                data_fim_str = (
                    registro.get("dataVigenciaFinal")
                    or registro.get("dataVigenciaFim")
                    or ""
                )
                try:
                    data_ini = datetime.strptime(data_ini_str[:10], "%Y-%m-%d").date() if data_ini_str else None
                except (ValueError, TypeError):
                    data_ini = None
                try:
                    data_fim = datetime.strptime(data_fim_str[:10], "%Y-%m-%d").date() if data_fim_str else None
                except (ValueError, TypeError):
                    data_fim = None

                # Sem nenhuma data no registro → não filtra (inclui)
                if not data_ini and not data_fim:
                    return True
                # Intersecção de intervalos: exclui se não houver sobreposição
                if vig_ini and data_fim and data_fim < vig_ini:
                    return False
                if vig_fim and data_ini and data_ini > vig_fim:
                    return False
                return True

            # Aplicar filtros nos contratos
            if contratos and (filtro_modalidade or filtro_objeto or filtro_fornecedor or filtro_processo or filtro_vigencia_inicio or filtro_vigencia_fim):
                contratos = [
                    c for c in contratos
                    if _match_modalidade(c, filtro_modalidade)
                    and _match_texto_campos(c, ["objeto"], filtro_objeto)
                    and _match_fornecedor(c, filtro_fornecedor)
                    and _match_texto_campos(c, ["processo", "numeroProcesso"], filtro_processo)
                    and _match_vigencia(c, filtro_vigencia_inicio, filtro_vigencia_fim)
                ]

            # Aplicar filtros nas ARPs
            if arps and (filtro_modalidade or filtro_objeto or filtro_fornecedor or filtro_processo or filtro_vigencia_inicio or filtro_vigencia_fim):
                # Para ARPs, se "ARP" está nos filtros de modalidade, sempre incluir
                _arp_selecionada = any("ARP" in f for f in filtro_modalidade) if filtro_modalidade else False
                # Se só ARP está selecionada, manter todas ARPs (filtrar os outros campos)
                arps = [
                    a for a in arps
                    if (_arp_selecionada or _match_modalidade(a, filtro_modalidade) or not filtro_modalidade)
                    and _match_texto_campos(a, ["objeto", "descricaoItem"], filtro_objeto)
                    and _match_fornecedor(a, filtro_fornecedor)
                    and _match_texto_campos(a, ["processo", "numeroProcesso", "numeroProcessoCompra"], filtro_processo)
                    and _match_vigencia(a, filtro_vigencia_inicio, filtro_vigencia_fim)
                ]

            # ── Métricas ──────────────────────────────────────────────────────
            c1, c2, c3 = st.columns(3)
            c1.metric("Contratos", len(contratos))
            c2.metric("ARPs (SRP)", len(arps))
            c3.metric("Total Registros", len(contratos) + len(arps))

            if contratos or arps:
                _df_contratos = pd.DataFrame([{
                    "Nº contrato": c.get("numeroContrato", ""), "Tipo": c.get("nomeTipo", ""),
                    "Modalidade": c.get("nomeModalidadeCompra", ""), "Nº compra": c.get("numeroCompra", ""),
                    "Fornecedor": c.get("nomeRazaoSocialFornecedor", ""), "CNPJ fornecedor": c.get("niFornecedor", ""),
                    "Objeto": c.get("objeto", ""), "Processo": c.get("processo", ""),
                    "Vigência início": _fmt_data(c.get("dataVigenciaInicial", "")), "Vigência fim": _fmt_data(c.get("dataVigenciaFinal", "")),
                    "Valor global": c.get("valorGlobal", ""), "ID da compra": c.get("idCompra", ""),
                    "Controle PNCP": c.get("numeroControlePncpCompra", ""),
                } for c in contratos])
                _df_arps = pd.DataFrame([{
                    "Nº ARP": a.get("numeroAtaRegistroPreco", ""), "Modalidade": a.get("nomeModalidadeCompra", ""),
                    "Nº compra": a.get("numeroCompra", ""), "Ano compra": a.get("anoCompra", ""),
                    "Fornecedor": a.get("nomeRazaoSocialFornecedor", ""), "CNPJ fornecedor": a.get("niFornecedor", ""),
                    "Objeto": a.get("objeto", ""), "Órgão": a.get("nomeOrgao", a.get("nomeUnidadeGerenciadora", "")),
                    "Vigência início": _fmt_data(a.get("dataVigenciaInicial", a.get("dataVigenciaInicio", ""))),
                    "Vigência fim": _fmt_data(a.get("dataVigenciaFinal", a.get("dataVigenciaFim", ""))),
                    "Valor total": a.get("valorTotal", ""), "Itens": a.get("quantidadeItens", ""),
                    "ID da compra": a.get("idCompra", ""), "Link ata PNCP": a.get("linkAtaPNCP", ""),
                } for a in arps])
                st.download_button(
                    "📊 Exportar resultados (Excel)", key="dc_exp_xlsx",
                    data=gerar_excel({"Contratos": _df_contratos, "ARPs": _df_arps}),
                    file_name=f"detalhes_compra_UASG{uasg}_{ano}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            if not contratos and not arps:
                st.warning(
                    "Nenhum registro encontrado. "
                    "As APIs do ComprasGov podem estar instáveis — tente novamente em alguns minutos."
                )

            # ═══ RESULTADOS ORGANIZADOS EM ABAS ═══════════════════════════════
            if contratos or arps:
                tab_contratos, tab_arps = st.tabs([
                    f"📋 Compras ({len(contratos)})",
                    f"📜 ARPs ({len(arps)})",
                ])


                # ── ABA COMPRAS ────────────────────────────────────────────────
                with tab_contratos:
                    if not contratos:
                        st.info("Nenhuma compra encontrada para os filtros selecionados.")
                    else:
                        _COMPRA_PAGE_SIZE = 5
                        _compras_shown = min(
                            st.session_state.get("_dc_compras_shown", _COMPRA_PAGE_SIZE),
                            len(contratos),
                        )
                        st.caption(f"📋 Total: {len(contratos)} compra(s) encontrada(s)")
                        if _compras_shown < len(contratos):
                            st.info(
                                f"📌 **Exibindo {_compras_shown} de {len(contratos)} compras.** "
                                f"Ainda há {len(contratos) - _compras_shown} — use o botão **Carregar mais compras** abaixo."
                            )

                        for i, contrato in enumerate(contratos[:_compras_shown]):
                            _obj_compra = contrato.get('objeto', '') or ''
                            _obj_compra_trunc = (_obj_compra[:80] + '…') if len(_obj_compra) > 80 else _obj_compra
                            _modalidade_compra = contrato.get('nomeModalidadeCompra', '')
                            _numero_compra = contrato.get('numeroCompra', '')
                            _licitacao_label = _modalidade_compra
                            if _numero_compra:
                                _licitacao_label += f" nº {_numero_compra}"
                            _licitacao_parte = f" — {_licitacao_label}" if _licitacao_label else ""
                            with st.expander(
                                f"📋 {contrato.get('numeroContrato', 'N/I')}{_licitacao_parte} — "
                                f"{_obj_compra_trunc or contrato.get('nomeRazaoSocialFornecedor', 'N/I')} — "
                                f"{_fmt_valor(contrato.get('valorGlobal', ''))}",
                                expanded=(i == 0),
                            ):
                                ctrl_pncp, id_compra_c = render_contrato(contrato, f"{i}_{contrato.get('idCompra', '')}_{contrato.get('numeroContrato', '')}")
                                parsed = parse_pncp_control(ctrl_pncp)
                                cnpj_c = parsed[0] if parsed else ""
                                ano_c = parsed[1] if parsed else ""
                                seq_c = parsed[2] if parsed else ""
                                render_links_externos(id_compra_c, cnpj_c, ano_c, seq_c)

                                # Itens e documentos PNCP
                                if parsed:
                                    with st.spinner("Buscando itens e documentos..."):
                                        docs = buscar_documentos_pncp(cnpj_c, ano_c, seq_c)
                                        itens = buscar_itens_pncp(cnpj_c, ano_c, seq_c)

                                    if docs:
                                        render_documentos(docs, "Documentos da Compra")

                                    if itens:
                                        with st.expander(f"📦 Itens da compra ({len(itens)} itens)", expanded=False):
                                            _com_resultado = [it for it in itens if it.get("temResultado")]
                                            _lotes = executar_em_paralelo(
                                                [lambda n=it.get("numeroItem", 0): buscar_resultado_item_pncp(cnpj_c, ano_c, seq_c, n) for it in _com_resultado])
                                            resultados_item = {it.get("numeroItem"): lote for it, lote in zip(_com_resultado, _lotes)}
                                            _desagio = resumo_desagio(itens, resultados_item)
                                            if _desagio["itens"]:
                                                _m1, _m2, _m3 = st.columns(3)
                                                _m1.metric("Valor estimado", _fmt_valor(_desagio["estimado"]), help=f"Soma dos {_desagio['itens']} itens com resultado.")
                                                _m2.metric("Valor homologado", _fmt_valor(_desagio["homologado"]))
                                                _m3.metric("Deságio", f"{_desagio['desagio']:.1f}%".replace(".", ","),
                                                           help="(estimado − homologado) ÷ estimado, nos itens com resultado e valor estimado informado.")
                                            for it in itens:
                                                num = it.get("numeroItem", 0)
                                                render_item_pncp(it, num)
                                                for res in resultados_item.get(num, []):
                                                    forn_ni = res.get("niFornecedor", "")
                                                    forn_nome = res.get("nomeRazaoSocialFornecedor", "")
                                                    val_hom = res.get("valorTotalHomologado", "")
                                                    est = it.get("valorTotal") or 0
                                                    desagio_item = f" — deságio {(est - val_hom) / est * 100:.1f}%".replace(".", ",") if est and val_hom else ""
                                                    st.markdown(f"  ↳ **Vencedor:** {forn_nome or forn_ni} ({forn_ni}) — Valor homologado: {_fmt_valor(val_hom)}{desagio_item}")
                                                st.markdown("---")

                        if _compras_shown < len(contratos):
                            _load_label_compras = "⬇️ Carregar mais compras"
                            if st.button(_load_label_compras, key="btn_load_more_compras_auto"):
                                st.session_state["_dc_compras_shown"] = min(
                                    _compras_shown + _COMPRA_PAGE_SIZE,
                                    len(contratos),
                                )
                                st.rerun()
                        elif len(contratos) > _COMPRA_PAGE_SIZE:
                            st.caption(f"✅ Todas as {len(contratos)} compras foram carregadas.")

                        st.markdown("---")
                        st.caption("💾 Documentos são carregados sob demanda ao expandir cada item.")

                # ── ABA ARPs (carregamento progressivo) ────────────────────
                with tab_arps:
                    if not arps:
                        st.info("Nenhuma ARP (SRP) encontrada para os filtros selecionados.")
                    else:
                        _ARP_PAGE_SIZE = 3
                        _arps_shown = min(
                            st.session_state.get("_dc_arps_shown", _ARP_PAGE_SIZE),
                            len(arps),
                        )
                        if _arps_shown < len(arps):
                            st.info(
                                f"📌 **Exibindo {_arps_shown} de {len(arps)} ARPs.** "
                                f"Ainda há {len(arps) - _arps_shown} — use o botão **Carregar mais ARPs** abaixo."
                            )

                        for i, ata in enumerate(arps[:_arps_shown]):
                            _num_compra = ata.get('numeroCompra', '')
                            _ano_compra = ata.get('anoCompra', '')
                            _ref_compra = f"{_num_compra}/{_ano_compra}" if _ano_compra else _num_compra
                            _obj_arp = ata.get('objeto', '') or ''
                            _obj_arp_trunc = (_obj_arp[:80] + '…') if len(_obj_arp) > 80 else _obj_arp
                            _titulo_arp = (
                                f"📜 ARP {ata.get('numeroAtaRegistroPreco', 'N/I')} — "
                                f"{ata.get('nomeModalidadeCompra', '')} nº {_ref_compra} — "
                                f"{_obj_arp_trunc or _fmt_valor(ata.get('valorTotal', ''))}"
                            )
                            with st.expander(_titulo_arp, expanded=(i == 0)):
                                ctrl_compra, ctrl_ata, id_compra_a = render_arp(ata, f"{i}_{ata.get('idCompra', '')}_{ata.get('numeroAtaRegistroPreco', '')}")
                                parsed_compra = parse_pncp_control(ctrl_compra)
                                cnpj_a = parsed_compra[0] if parsed_compra else ""
                                ano_a = parsed_compra[1] if parsed_compra else ""
                                seq_a = parsed_compra[2] if parsed_compra else ""

                                # Links diretos (sem buscar documentos automaticamente)
                                render_links_externos(id_compra_a, cnpj_a, ano_a, seq_a)

                                # Documentos sob demanda — só busca quando o usuário clica
                                if parsed_compra:
                                    _doc_key = f"_dc_arp_docs_{i}"
                                    if st.button("📎 Buscar documentos no PNCP", key=f"btn_arp_docs_{i}"):
                                        st.session_state[_doc_key] = True

                                    if st.session_state.get(_doc_key):
                                        with st.spinner("Buscando documentos..."):
                                            docs_compra = buscar_documentos_pncp(cnpj_a, ano_a, seq_a)
                                            atas_pncp = buscar_atas_pncp(cnpj_a, ano_a, seq_a)

                                        if docs_compra:
                                            render_documentos(docs_compra, "Documentos da Licitação")

                                        if atas_pncp:
                                            for at in atas_pncp:
                                                seq_at_pncp = at.get("sequencialAta", "")
                                                docs_at = buscar_documentos_ata_pncp(cnpj_a, ano_a, seq_a, str(seq_at_pncp))
                                                if docs_at:
                                                    render_documentos(docs_at, f"Documentos da Ata {seq_at_pncp}")
                                        elif ctrl_ata:
                                            m_ata = re.match(r"(\d{14})-(\d+)-(\d+)/(\d{4})", ctrl_ata)
                                            if m_ata:
                                                seq_ata = m_ata.group(3)
                                                docs_ata = buscar_documentos_ata_pncp(cnpj_a, ano_a, seq_a, str(int(seq_ata)))
                                                if docs_ata:
                                                    render_documentos(docs_ata, "Documentos da Ata")

                                        if not docs_compra and not atas_pncp:
                                            st.caption("Nenhum documento encontrado no PNCP para esta ARP.")

                        # ── Carregamento progressivo ──────────────────────────────────
                        if _arps_shown < len(arps):
                            _load_label_arps = "⬇️ Carregar mais ARPs"
                            if st.button(_load_label_arps, key="btn_load_more_arps_auto"):
                                st.session_state["_dc_arps_shown"] = min(
                                    _arps_shown + _ARP_PAGE_SIZE,
                                    len(arps),
                                )
                                st.rerun()
                        else:
                            if len(arps) > _ARP_PAGE_SIZE:
                                st.caption(f"✅ Todas as {len(arps)} ARPs foram carregadas.")
