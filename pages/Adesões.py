import asyncio
import base64
import json
import os
import re
from datetime import datetime as dt, timedelta as td
from typing import Dict, List, Optional, Tuple

import aiohttp
import folium
import streamlit as st
from streamlit_folium import st_folium

# ── Caminhos dos dados do Projeto Adesões ──────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões")

# ── Constantes da API ──────────────────────────────────────────────────────
API_URL = "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem"
API_URL_UNIDADES = "https://dadosabertos.compras.gov.br/modulo-arp/3_consultarUnidadesItem"
MAX_CONCURRENCY = 4
DATE_RANGE_DAYS = 360
PAGE_SIZE = {"Material": 100, "Serviço": 100}

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
    st.page_link("streamlit_app.py", label="⚓ Cotação", icon="📊")
    st.page_link("pages/Adesões.py", label="🤝 Adesões", icon="📋")
    st.page_link("pages/Notas_Fiscais.py", label="📄 Notas Fiscais", icon="🧾")
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-container">
        <div class="logo-text">SISTEMA DE ACOMPANHAMENTO</div>
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


def normalize_item(item: Dict) -> Optional[Tuple[str, str, str, str, str]]:
    if item.get("maximoAdesao", 0) == 0:
        return None
    numero_ata = item.get("numeroAtaRegistroPreco", "Ata não informada")
    unidade = item.get("nomeUnidadeGerenciadora", "Unidade não informada")
    fornecedor = item.get("nomeRazaoSocialFornecedor", "Fornecedor não informado")
    identificador = item.get("numeroControlePncpAta", "")
    url = build_ata_url(identificador)
    return numero_ata, unidade, fornecedor, identificador, url


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
    retries = 10
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
    federal_only: bool,
    uasg_sphere: Dict[str, str],
    max_concurrency: int = MAX_CONCURRENCY,
) -> List[Dict]:
    timeout = aiohttp.ClientTimeout(total=10)
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

        first_page = await fetch_page(session, semaphore, 1, base_params)
        total_pages_count = 1 + parse_remaining_pages(first_page.get("paginasRestantes"))
        render_payload(first_page)
        processed_pages = 1

        for page in range(2, total_pages_count + 1):
            tasks.append(asyncio.create_task(fetch_page(session, semaphore, page, base_params)))

        if total_pages_count == processed_pages:
            status_placeholder.success("Busca concluída.")
            return results

        for idx, task in enumerate(asyncio.as_completed(tasks), start=processed_pages + 1):
            try:
                payload = await task
                render_payload(payload)
                status_placeholder.info(f"Processando páginas ({idx}/{total_pages_count})…")
            except Exception:
                status_placeholder.warning(
                    "Falha ao carregar uma das páginas. Retentativa não disponível."
                )

        status_placeholder.success("Busca concluída.")
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
    retries = 3
    delay = 0.5
    async with semaphore:
        for attempt in range(retries):
            try:
                async with session.get(API_URL_UNIDADES, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()
                    results = data.get("resultado", [])
                    if results:
                        return results[0]
                    return None
            except Exception:
                if attempt == retries - 1:
                    return None
                await asyncio.sleep(delay)
                delay *= 2
    return None


async def enrich_results_async(
    display_results: List[Dict],
    max_concurrency: int = MAX_CONCURRENCY,
) -> Dict[str, Dict]:
    """Para cada ata em display_results, busca detalhes de saldo/adesão.
    Retorna dict mapeando identificador -> detalhes."""
    timeout = aiohttp.ClientTimeout(total=15)
    semaphore = asyncio.Semaphore(max_concurrency)
    connector = aiohttp.TCPConnector(limit=None, ssl=False)
    details: Dict[str, Dict] = {}

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = []
        keys = []
        for raw in display_results:
            numero_ata = raw.get("numeroAtaRegistroPreco", "")
            unidade = raw.get("codigoUnidadeGerenciadora", "") or str(raw.get("codigoUasg", ""))
            numero_item = raw.get("numeroItem", "")
            identificador = raw.get("numeroControlePncpAta", "")
            if not (numero_ata and unidade and numero_item):
                continue
            keys.append(identificador)
            tasks.append(
                asyncio.create_task(
                    fetch_unit_detail(session, semaphore, numero_ata, unidade, numero_item)
                )
            )
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for key, result in zip(keys, results_list):
            if isinstance(result, dict):
                details[key] = result
    return details


def run_enrich(display_results: List[Dict]) -> Dict[str, Dict]:
    """Wrapper síncrono para enriquecer resultados com dados do endpoint 3."""
    try:
        return asyncio.run(enrich_results_async(display_results))
    except Exception:
        return {}


def run_search(
    tipo: str,
    codigo: str,
    federal_only: bool,
    uasg_sphere: Dict[str, str],
) -> List[Dict]:
    status_placeholder = st.empty()
    with st.spinner("Consultando dados, por favor aguarde um momento…"):
        try:
            results = asyncio.run(
                search_async(
                    tipo,
                    codigo,
                    status_placeholder,
                    federal_only=federal_only,
                    uasg_sphere=uasg_sphere,
                )
            )
        except Exception:
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

if tipo == "Material":
    materiais = load_catalog(_data_path("catalogo_pdm.json"))
    selected_label = st.selectbox(
        "Material",
        sorted(materiais.keys()),
        index=None,
        placeholder="Pesquise pelo nome do material",
    )
    if selected_label:
        codigo = materiais[selected_label]

if tipo == "Serviço":
    servicos = load_catalog(_data_path("catalogo_servicos.json"))
    selected_label = st.selectbox(
        "Serviço",
        sorted(servicos.keys()),
        index=None,
        placeholder="Pesquise pelo nome do serviço",
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
            with st.spinner("Buscando detalhes de saldo e adesão…"):
                enriched = run_enrich(display_results)

            for raw in display_results:
                normalized = normalize_item(raw)
                if not normalized:
                    continue
                numero, unidade, fornecedor, identificador, url = normalized

                # Código UASG do órgão
                uasg_code = extract_uasg(raw) or "N/I"

                detail = enriched.get(identificador, {})
                saldo_adesoes = detail.get("saldoAdesoes", "N/I")
                saldo_remanejamento = detail.get("saldoRemanejamentoEmpenho", "N/I")
                qtd_limite_adesao = detail.get("qtdLimiteAdesao", "N/I")
                qtd_limite_compra = detail.get("qtdLimiteInformadoCompra", "N/I")
                aceita_adesao_raw = detail.get("aceitaAdesao")
                if aceita_adesao_raw is True:
                    aceita_adesao = '<span style="color:#22c55e;font-weight:bold;">✅ Sim</span>'
                elif aceita_adesao_raw is False:
                    aceita_adesao = '<span style="color:#ef4444;font-weight:bold;">❌ Não</span>'
                else:
                    aceita_adesao = '<span style="color:#94a3b8;">N/I</span>'

                # Número do item (vem da API 2)
                numero_item = raw.get("numeroItem", "N/I")

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

                st.markdown(
                    f"""
                    <div class="result-card">
                        <div class="status-text">Ata {numero} • {unidade} (UASG {uasg_code})</div>
                        <div><a href="{url}" target="_blank">Visualizar documento – {fornecedor}</a></div>
                        <div style="display:flex;flex-wrap:wrap;gap:0.6rem 1.4rem;margin-top:0.5rem;font-size:0.85rem;color:#cbd5e1;">
                            <span>🔢 <b>Item:</b> {numero_item}</span>
                            <span>📅 <b>Vigência Final:</b> {vigencia_final}</span>
                            <span>📦 <b>Saldo Adesões:</b> {saldo_adesoes}</span>
                            <span>🔄 <b>Saldo Remanej.:</b> {saldo_remanejamento}</span>
                            <span>📊 <b>Lim. Adesão:</b> {qtd_limite_adesao}</span>
                            <span>🛒 <b>Lim. Compra:</b> {qtd_limite_compra}</span>
                            <span>🤝 <b>Aceita Adesão:</b> {aceita_adesao}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
elif start_button and tipo and codigo:
    st.info("Nenhuma ata encontrada para este critério.")
