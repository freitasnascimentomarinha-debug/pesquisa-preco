"""
Detalhes da Compra — AtaCotada
Busca contratos, documentos e dados de compras via APIs públicas
(ComprasGov + PNCP) a partir de dados da Cotação.
"""

import base64
import json
import os
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests
import streamlit as st

# ── Caminhos ───────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões")

# ── Constantes API ─────────────────────────────────────────────────────────
COMPRASGOV_BASE = "https://dadosabertos.compras.gov.br"
PNCP_API_BASE = "https://pncp.gov.br/pncp-api/v1"
PNCP_API_BASE_NEW = "https://pncp.gov.br/api/consulta/v1"
PNCP_PORTAL_BASE = "https://pncp.gov.br/app/editais"
COMPRASNET_BASE = "https://cnetmobile.estaleiro.serpro.gov.br/comprasnet-web/public/landing"
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
        border-radius: 10px !important; margin: .4rem 0 !important;
        padding: .85rem 1.2rem !important; font-weight: 600 !important;
        font-size: 15px !important; transition: all .3s ease !important;
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
        background: rgba(0, 26, 77, 0.6); border: 1px solid rgba(212,175,55,0.3);
        border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: .8rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.25);
    }
    .info-card h4 { color: #d4af37; margin: 0 0 .5rem 0; font-size: 1rem; }
    .info-card p { color: #cbd5e1; margin: .15rem 0; font-size: .9rem; }
    .info-card a { color: #d4af37 !important; text-decoration: none; font-weight: 600; }
    .info-card a:hover { color: #f0d060 !important; text-decoration: underline; }

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
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
    st.markdown("---")
    st.markdown("## LINKS ÚTEIS")
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <a href="https://freitasnascimentomarinha-debug.github.io/ShootMail/" target="_blank"
           style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem;">
            📧 Disparador de Emails
        </a>
    </div>
    <div style="margin-bottom: 1rem;">
        <a href="https://detetive-obtencao.vercel.app/" target="_blank"
           style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem;">
            🚨 Detetive Obtenção
        </a>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;'
        'padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)

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
    """GET com retry e tratamento de erros. Lida com migração de API PNCP."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}, verify=True)
            if r.status_code == 404:
                return None
            if r.status_code == 301:
                # API PNCP migrou — tentar nova URL uma única vez (timeout curto)
                if PNCP_API_BASE in url:
                    alt_url = url.replace(PNCP_API_BASE, PNCP_API_BASE_NEW)
                    try:
                        r2 = requests.get(alt_url, timeout=12, headers={"User-Agent": "Mozilla/5.0"}, verify=True)
                        if r2.status_code == 200:
                            return r2.json()
                    except Exception:
                        pass
                return None
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                time.sleep(0.5)
                continue
            return None
        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES:
                time.sleep(0.5)
                continue
            return None
    return None


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


# ── API ComprasGov: Contratos ──────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def buscar_contratos_uasg(codigo_uasg: str, ano: int) -> List[Dict]:
    """Busca contratos de uma UASG via modulo-contratos do ComprasGov."""
    params = {
        "codigoUnidadeGestora": codigo_uasg,
        "dataVigenciaInicialMin": f"{ano}-01-01",
        "dataVigenciaInicialMax": f"{ano}-12-31",
        "pagina": 1,
        "tamanhoPagina": 500,
    }
    url = f"{COMPRASGOV_BASE}/modulo-contratos/1_consultarContratos?{urlencode(params)}"
    data = _api_get(url)
    if data and isinstance(data, dict):
        return data.get("resultado", [])
    return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_contratos_item_uasg(codigo_uasg: str, ano: int) -> List[Dict]:
    """Busca itens de contratos de uma UASG."""
    params = {
        "codigoUnidadeGestora": codigo_uasg,
        "dataVigenciaInicialMin": f"{ano}-01-01",
        "dataVigenciaInicialMax": f"{ano}-12-31",
        "pagina": 1,
        "tamanhoPagina": 500,
    }
    url = f"{COMPRASGOV_BASE}/modulo-contratos/2_consultarContratosItem?{urlencode(params)}"
    data = _api_get(url)
    if data and isinstance(data, dict):
        return data.get("resultado", [])
    return []


# ── API ComprasGov: ARP (SRP) ─────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def buscar_arp_uasg(codigo_uasg: str, ano: int) -> List[Dict]:
    """Busca Atas de Registro de Preço de uma UASG."""
    params = {
        "codigoUnidadeGestora": codigo_uasg,
        "dataVigenciaInicioMin": f"{ano}-01-01",
        "dataVigenciaInicioMax": f"{ano}-12-31",
        "pagina": 1,
        "tamanhoPagina": 500,
    }
    url = f"{COMPRASGOV_BASE}/modulo-arp/1_consultarARP?{urlencode(params)}"
    data = _api_get(url)
    if data and isinstance(data, dict):
        return data.get("resultado", [])
    return []


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
        badge = f' <span class="doc-badge">{tipo}</span>' if tipo else ""
        st.markdown(
            f'<div class="doc-card">'
            f'<a href="{url_doc}" target="_blank">📥 {titulo_doc}</a>{badge}'
            f"</div>",
            unsafe_allow_html=True,
        )


def render_links_externos(id_compra: str, cnpj: str = "", ano: str = "", seq: str = ""):
    """Renderiza links para ComprasNet e PNCP Portal."""
    links_html = ""
    if id_compra:
        cnet = build_comprasnet_link(id_compra)
        links_html += f'<p>🔗 <a href="{cnet}" target="_blank">Abrir no ComprasNet</a> <small style="color:#999">(nem toda compra está disponível no ComprasNet legado)</small></p>'
    if cnpj and ano and seq:
        portal = build_pncp_portal_link(cnpj, ano, seq)
        links_html += f'<p>🔗 <a href="{portal}" target="_blank">Abrir no PNCP</a></p>'
    if links_html:
        st.markdown(f'<div class="info-card"><h4>🌐 Links Externos</h4>{links_html}</div>', unsafe_allow_html=True)


def render_contrato(contrato: Dict):
    """Renderiza card de um contrato."""
    numero = contrato.get("numeroContrato", "N/I")
    fornecedor = contrato.get("nomeRazaoSocialFornecedor", "N/I")
    cnpj_forn = contrato.get("niFornecedor", "")
    modalidade = contrato.get("nomeModalidadeCompra", "N/I")
    objeto = contrato.get("objeto", "N/I")
    valor = contrato.get("valorGlobal", "")
    processo = contrato.get("processo", "")
    id_compra = contrato.get("idCompra", "")
    ctrl_pncp = contrato.get("numeroControlePncpCompra", "")
    data_vig_ini = contrato.get("dataVigenciaInicial", "")[:10] if contrato.get("dataVigenciaInicial") else ""
    data_vig_fim = contrato.get("dataVigenciaFinal", "")[:10] if contrato.get("dataVigenciaFinal") else ""

    valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor else "N/I"
    vigencia = f"{data_vig_ini} a {data_vig_fim}" if data_vig_ini else "N/I"

    html = f"""<div class="info-card">
        <h4>📋 Contrato: {numero}</h4>
        <p><strong>Modalidade:</strong> {modalidade}</p>
        <p><strong>Fornecedor:</strong> {fornecedor} ({cnpj_forn})</p>
        <p><strong>Objeto:</strong> {objeto}</p>
        <p><strong>Valor Global:</strong> {valor_fmt}</p>
        <p><strong>Vigência:</strong> {vigencia}</p>
        <p><strong>Processo:</strong> {processo}</p>
        <p><strong>ID Compra:</strong> {id_compra}</p>
        <p><strong>PNCP Compra:</strong> {ctrl_pncp or 'N/I'}</p>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)

    return ctrl_pncp, id_compra


def render_arp(ata: Dict):
    """Renderiza card de uma ARP."""
    numero_ata = ata.get("numeroAtaRegistroPreco", "N/I")
    fornecedor = ata.get("nomeRazaoSocialFornecedor", "N/I")
    cnpj_forn = ata.get("niFornecedor", "")
    id_compra = ata.get("idCompra", "")
    ctrl_ata = ata.get("numeroControlePncpAta", "")
    ctrl_compra = ata.get("numeroControlePncpCompra", "")
    data_vig_ini = ata.get("dataVigenciaInicio", "")[:10] if ata.get("dataVigenciaInicio") else ""
    data_vig_fim = ata.get("dataVigenciaFim", "")[:10] if ata.get("dataVigenciaFim") else ""
    situacao = ata.get("situacao", "")

    vigencia = f"{data_vig_ini} a {data_vig_fim}" if data_vig_ini else "N/I"

    html = f"""<div class="info-card">
        <h4>📜 ARP (SRP): {numero_ata}</h4>
        <p><strong>Fornecedor:</strong> {fornecedor} ({cnpj_forn})</p>
        <p><strong>Vigência:</strong> {vigencia}</p>
        <p><strong>Situação:</strong> {situacao}</p>
        <p><strong>ID Compra:</strong> {id_compra}</p>
        <p><strong>PNCP Ata:</strong> {ctrl_ata or 'N/I'}</p>
        <p><strong>PNCP Compra:</strong> {ctrl_compra or 'N/I'}</p>
    </div>"""
    st.markdown(html, unsafe_allow_html=True)

    return ctrl_compra, ctrl_ata, id_compra


def render_item_pncp(item: Dict, idx: int):
    """Renderiza um item PNCP de forma compacta."""
    desc = item.get("descricao", "Sem descrição")
    valor = item.get("valorUnitarioEstimado", "")
    qtd = item.get("quantidade", "")
    unidade = item.get("unidadeMedida", "")
    situacao = item.get("situacaoCompraItemNome", "")
    tipo = item.get("materialOuServicoNome", "")

    valor_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if valor else "N/I"

    st.markdown(
        f"**Item {idx}** — {desc}  \n"
        f"Tipo: {tipo} | Qtd: {qtd} {unidade} | Valor est.: {valor_fmt} | Situação: {situacao}"
    )


# ═══════════════════════════════════════════════════════════════════════════
# PÁGINA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="color: #d4af37; font-size: 20px; font-weight: bold; margin-bottom: .5rem;">
    🔍 Consultar Detalhes de Compras
</div>
<p style="color: #cbd5e1; font-size: .9rem; margin-bottom: 1.5rem;">
    Busca contratos, ARPs (SRP), documentos (TR, edital) e links no PNCP/ComprasNet
    a partir do código UASG. Você pode filtrar por ID da Compra para encontrar um registro específico.
</p>
""", unsafe_allow_html=True)

# ── Formulário de busca ───────────────────────────────────────────────────
col_uasg, col_ano, col_id = st.columns([2, 1, 3])

with col_uasg:
    input_uasg = st.text_input(
        "Código UASG *",
        value=st.session_state.get("detalhe_uasg", ""),
        placeholder="Ex: 153050, 771300",
        help="Código da Unidade Gestora (6 dígitos). Campo obrigatório.",
    )

with col_ano:
    input_ano = st.number_input(
        "Ano",
        min_value=2020,
        max_value=2030,
        value=datetime.now().year,
        help="Ano de vigência/referência.",
    )

with col_id:
    input_id_compra = st.text_input(
        "ID da Compra (opcional)",
        value=st.session_state.get("detalhe_id_compra", ""),
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

# ── Execução da busca ─────────────────────────────────────────────────────
if consultar:
    if not input_uasg or not input_uasg.strip().isdigit():
        st.error("❌ Informe um código UASG válido (apenas números).")
    else:
        uasg = input_uasg.strip()
        ano = int(input_ano)
        id_filtro = input_id_compra.strip() if input_id_compra else ""

        # Info da UASG
        uasg_index = load_uasg_index()
        uasg_info = uasg_index.get(uasg, {})
        nome_uasg = uasg_info.get("nomeUasg", "Não encontrada no cadastro local")
        uf = uasg_info.get("siglaUf", "")

        st.markdown(
            f'<div class="info-card"><h4>🏛️ UASG {uasg}</h4>'
            f'<p><strong>{nome_uasg}</strong>{" — " + uf if uf else ""}</p></div>',
            unsafe_allow_html=True,
        )

        # ── 1. Buscar Contratos ───────────────────────────────────────────
        with st.spinner("Buscando contratos no ComprasGov..."):
            contratos = buscar_contratos_uasg(uasg, ano)

        # Filtrar por idCompra se informado
        if id_filtro and contratos:
            contratos = [c for c in contratos if c.get("idCompra", "") == id_filtro]

        # ── 2. Buscar ARPs (SRP) ──────────────────────────────────────────
        with st.spinner("Buscando Atas de Registro de Preço (SRP)..."):
            arps = buscar_arp_uasg(uasg, ano)

        if id_filtro and arps:
            arps = [a for a in arps if a.get("idCompra", "") == id_filtro]

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
                and _match_texto(c, "objeto", filtro_objeto)
                and _match_fornecedor(c, filtro_fornecedor)
                and _match_texto(c, "processo", filtro_processo)
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
                and _match_fornecedor(a, filtro_fornecedor)
                and _match_vigencia(a, filtro_vigencia_inicio, filtro_vigencia_fim)
            ]

        # ── Métricas ──────────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        c1.metric("Contratos", len(contratos))
        c2.metric("ARPs (SRP)", len(arps))
        c3.metric("Total Registros", len(contratos) + len(arps))

        if not contratos and not arps:
            st.warning(
                "Nenhum registro encontrado. "
                "As APIs do ComprasGov podem estar instáveis — tente novamente em alguns minutos."
            )
            # Gerar links diretos mesmo sem dados da API
            if id_filtro:
                st.markdown("---")
                st.markdown("**Mesmo sem resultados da API, você pode tentar os links diretos:**")
                render_links_externos(id_filtro)

        # ── Coletar PNCP controls para buscar docs ───────────────────────
        pncp_compras_processadas = set()

        # ── 3. Exibir Contratos ───────────────────────────────────────────
        if contratos:
            st.markdown("---")
            st.markdown(
                '<div style="color: #d4af37; font-size: 18px; font-weight: bold; margin: 1rem 0;">'
                "📋 Contratos</div>",
                unsafe_allow_html=True,
            )

            for contrato in contratos:
                ctrl_pncp, id_compra_c = render_contrato(contrato)

                # Links externos
                parsed = parse_pncp_control(ctrl_pncp)
                cnpj_c = parsed[0] if parsed else ""
                ano_c = parsed[1] if parsed else ""
                seq_c = parsed[2] if parsed else ""
                render_links_externos(id_compra_c, cnpj_c, ano_c, seq_c)

                # Buscar docs no PNCP se temos o control number
                if parsed and ctrl_pncp not in pncp_compras_processadas:
                    pncp_compras_processadas.add(ctrl_pncp)
                    with st.spinner(f"Buscando documentos PNCP..."):
                        docs = buscar_documentos_pncp(cnpj_c, ano_c, seq_c)
                        itens = buscar_itens_pncp(cnpj_c, ano_c, seq_c)

                    if not docs and not itens:
                        st.caption("⚠️ API PNCP não retornou documentos (pode estar instável).")

                    if docs:
                        render_documentos(docs, "Documentos da Compra")

                    if itens:
                        with st.expander(f"📦 Itens da compra ({len(itens)} itens)", expanded=False):
                            for it in itens:
                                num = it.get("numeroItem", 0)
                                render_item_pncp(it, num)
                                # Resultado do item (fornecedor vencedor)
                                if it.get("temResultado"):
                                    resultados = buscar_resultado_item_pncp(cnpj_c, ano_c, seq_c, num)
                                    for res in resultados:
                                        forn_ni = res.get("niFornecedor", "")
                                        val_hom = res.get("valorTotalHomologado", "")
                                        val_fmt = (
                                            f"R$ {val_hom:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                                            if val_hom else "N/I"
                                        )
                                        st.markdown(f"  ↳ Vencedor: {forn_ni} — Valor homologado: {val_fmt}")
                                st.markdown("---")

        # ── 4. Exibir ARPs (SRP) ──────────────────────────────────────────
        if arps:
            st.markdown("---")
            st.markdown(
                '<div style="color: #d4af37; font-size: 18px; font-weight: bold; margin: 1rem 0;">'
                "📜 Atas de Registro de Preço (SRP)</div>",
                unsafe_allow_html=True,
            )

            for ata in arps:
                ctrl_compra, ctrl_ata, id_compra_a = render_arp(ata)

                # Links externos
                parsed_compra = parse_pncp_control(ctrl_compra)
                cnpj_a = parsed_compra[0] if parsed_compra else ""
                ano_a = parsed_compra[1] if parsed_compra else ""
                seq_a = parsed_compra[2] if parsed_compra else ""
                render_links_externos(id_compra_a, cnpj_a, ano_a, seq_a)

                # Docs da compra (se não já processada)
                if parsed_compra and ctrl_compra not in pncp_compras_processadas:
                    pncp_compras_processadas.add(ctrl_compra)
                    with st.spinner("Buscando documentos PNCP..."):
                        docs_compra = buscar_documentos_pncp(cnpj_a, ano_a, seq_a)
                    if docs_compra:
                        render_documentos(docs_compra, "Documentos da Compra/Licitação")

                # Buscar atas via PNCP e seus documentos
                if parsed_compra:
                    with st.spinner("Buscando atas no PNCP..."):
                        atas_pncp = buscar_atas_pncp(cnpj_a, ano_a, seq_a)

                    if atas_pncp:
                        with st.expander(f"📜 Atas de Registro de Preço no PNCP ({len(atas_pncp)})", expanded=True):
                            for at in atas_pncp:
                                seq_at_pncp = at.get("sequencialAta", "")
                                vigencia_ini = (at.get("dataVigenciaInicio", "") or "")[:10]
                                vigencia_fim = (at.get("dataVigenciaFim", "") or "")[:10]
                                situacao_ata = at.get("situacao", "")
                                forn_ata = at.get("nomeRazaoSocialFornecedor", "")
                                ni_forn_ata = at.get("niFornecedor", "")
                                st.markdown(
                                    f"**Ata seq {seq_at_pncp}** — "
                                    f"Vigência: {vigencia_ini} a {vigencia_fim}"
                                    + (f" | Situação: {situacao_ata}" if situacao_ata else "")
                                    + (f"  \nFornecedor: {forn_ata} ({ni_forn_ata})" if forn_ata else "")
                                )
                                # Docs desta ata PNCP
                                docs_at = buscar_documentos_ata_pncp(cnpj_a, ano_a, seq_a, str(seq_at_pncp))
                                if docs_at:
                                    render_documentos(docs_at, f"Documentos da Ata {seq_at_pncp}")
                                else:
                                    st.caption("Nenhum documento disponível para esta ata.")
                                st.markdown("---")
                    elif ctrl_ata:
                        # Fallback: tentar buscar docs da ata pelo ctrl_ata diretamente
                        m_ata = re.match(r"(\d{14})-(\d+)-(\d+)/(\d{4})", ctrl_ata)
                        if m_ata and parsed_compra:
                            seq_ata = m_ata.group(3)
                            with st.spinner("Buscando documentos da Ata..."):
                                docs_ata = buscar_documentos_ata_pncp(cnpj_a, ano_a, seq_a, str(int(seq_ata)))
                            if docs_ata:
                                render_documentos(docs_ata, "Documentos da Ata")

        # ── 5. Busca direta PNCP se nada foi encontrado via ComprasGov ───
        if not contratos and not arps and id_filtro:
            st.markdown("---")
            st.markdown(
                '<div style="color: #d4af37; font-size: 16px; font-weight: bold; margin: 1rem 0;">'
                "🔎 Busca direta no PNCP (fallback)</div>",
                unsafe_allow_html=True,
            )
            st.info("Tentando localizar a compra diretamente no PNCP via contratações...")

            # Extrair CNPJ do órgão a partir da UASG - tentar via pesquisa-preco
            # Buscar qualquer item desta UASG para descobrir o CNPJ do órgão
            with st.spinner("Buscando CNPJ do órgão..."):
                params_pp = {
                    "codigoUasg": uasg,
                    "dataCompraInicio": f"{ano}-01-01",
                    "dataCompraFim": f"{ano}-12-31",
                    "pagina": 1,
                    "tamanhoPagina": 10,
                }
                url_pp = f"{COMPRASGOV_BASE}/modulo-pesquisa-preco/1_consultarMaterial?{urlencode(params_pp)}"
                data_pp = _api_get(url_pp)
                cnpj_orgao = ""
                if data_pp and isinstance(data_pp, dict):
                    for item in data_pp.get("resultado", []):
                        ni = item.get("niOrgao", "")
                        if ni and len(ni) == 14:
                            cnpj_orgao = ni
                            break

            if not cnpj_orgao:
                st.warning(
                    "Não foi possível encontrar o CNPJ do órgão automaticamente. "
                    "As APIs podem estar instáveis."
                )
            else:
                st.markdown(f"CNPJ do órgão: **{cnpj_orgao}**")
                # Tentar buscar a compra no PNCP escaneando sequenciais recentes
                encontrou = False
                with st.spinner("Escaneando compras recentes no PNCP..."):
                    for seq_try in range(1, 51):
                        seq_str = f"{seq_try:06d}"
                        compra = buscar_compra_pncp(cnpj_orgao, str(ano), seq_str)
                        if not compra:
                            continue
                        link_origem = compra.get("linkSistemaOrigem", "") or ""
                        uorg = compra.get("unidadeOrgao", {}) or {}
                        cod_unidade = uorg.get("codigoUnidade", "")

                        # Match por idCompra no link ou pela UASG
                        if id_filtro and id_filtro in link_origem:
                            encontrou = True
                            st.success(f"Compra encontrada no PNCP! Sequencial: {seq_str}")
                            obj = compra.get("objetoCompra", "")
                            modal = compra.get("modalidadeNome", "")
                            st.markdown(
                                f'<div class="info-card">'
                                f"<h4>🏷️ {modal}</h4>"
                                f"<p><strong>Objeto:</strong> {obj}</p>"
                                f"<p><strong>UASG:</strong> {cod_unidade}</p>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                            render_links_externos(id_filtro, cnpj_orgao, str(ano), seq_str)

                            docs = buscar_documentos_pncp(cnpj_orgao, str(ano), seq_str)
                            if docs:
                                render_documentos(docs)

                            itens = buscar_itens_pncp(cnpj_orgao, str(ano), seq_str)
                            if itens:
                                with st.expander(f"📦 Itens ({len(itens)})", expanded=False):
                                    for it in itens:
                                        render_item_pncp(it, it.get("numeroItem", 0))
                            break

                if not encontrou:
                    st.warning(
                        "Compra não encontrada no PNCP nos primeiros 50 sequenciais. "
                        "A compra pode ser muito recente ou ainda não publicada no PNCP."
                    )
