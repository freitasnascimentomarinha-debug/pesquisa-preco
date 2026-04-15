import streamlit as st
import requests
import pandas as pd
import json
import os
import re
import io
import base64
import tempfile
import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuração da página
st.set_page_config(
    page_title="AtaCotada - Consulta",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS customizado
st.markdown("""
    <style>
        /* Anti-flash: forçar fundo escuro desde o início */
        html, body, [data-testid="stAppViewContainer"],
        .main, [data-testid="stApp"], .stApp {
            background-color: #001a4d !important;
            color: #ffffff !important;
        }

        .stApp { animation: fadeIn 0.3s ease-in; }
        @keyframes fadeIn { from { opacity: 0.7; } to { opacity: 1; } }

        /* Header customizado */
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

        /* SIDEBAR MODERNA */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #d4af37 !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.5);
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { background: transparent !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        
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
        
        [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p { color: #ffffff !important; }
        [data-testid="stSidebar"] hr { border-color: #333333 !important; margin: 1rem 0 !important; }
        .sidebar-footer { color: #666666; font-size: 11px; text-align: center; padding: 1rem 0; border-top: 1px solid #333333; margin-top: 2rem; }

        /* CARDS */
        .info-card {
            background: rgba(0, 26, 77, 0.6);
            border: 1px solid #d4af37;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.35);
            margin-bottom: 1rem;
        }
        .info-title { color: #d4af37; font-size: 1.2rem; font-weight: bold; margin-bottom: 1rem; border-bottom: 1px solid rgba(212, 175, 55, 0.3); padding-bottom: 0.5rem; }
        .info-item { margin-bottom: 0.5rem; }
        .info-label { color: #cbd5e1; font-weight: bold; }
        .info-value { color: #ffffff; }

        .contract-card {
            background: rgba(0, 26, 77, 0.45);
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            border: 1px solid rgba(212, 175, 55, 0.3);
            box-shadow: 0 6px 24px rgba(0,0,0,0.28);
        }
        .contract-title { color: #d4af37; font-weight: bold; font-size: 1.1rem; margin-bottom: 0.5rem; }

        /* Botão primário amarelo */
        .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
            background-color: #d4af37 !important; color: #ffffff !important; border: none !important; font-weight: bold !important;
        }
        .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
            background-color: #c5a028 !important; color: #ffffff !important;
        }

        /* Tabs styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
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

        /* Tabelas */
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border-radius: 8px;
            overflow: hidden;
        }
        th { background-color: #ffffff !important; color: #333333 !important; font-weight: bold; border-bottom: 2px solid #d4af37 !important; }
        td { background-color: #ffffff !important; color: #333333 !important; }
        
    </style>
""", unsafe_allow_html=True)


# ===================== FUNÇÕES AUXILIARES =====================

def formatar_moeda_br(valor):
    try:
        val = float(valor)
        return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"

def formatar_cnpj(cnpj):
    cnpj = str(cnpj).zfill(14)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


# ===================== APIs =====================

@st.cache_data(ttl=3600)
def consultar_opencnpj(cnpj_limpo):
    """Consulta dados cadastrais via OpenCNPJ."""
    try:
        url = f"https://api.opencnpj.org/{cnpj_limpo}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600)
def consultar_brasilapi(cnpj_limpo):
    """Fallback: consulta dados cadastrais via BrasilAPI para obter email/telefone."""
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600)
def consultar_pncp_search(cnpj_limpo, tipo_documento="contrato"):
    """Consulta o PNCP via API de busca (Search).
    Busca contratos ou compras associados ao CNPJ fornecido.
    Retorna lista de resultados paginados."""
    todos = []
    pagina = 1
    max_paginas = 20

    while pagina <= max_paginas:
        try:
            url = "https://pncp.gov.br/api/search/"
            params = {
                'q': cnpj_limpo,
                'tipos_documento': tipo_documento,
                'pagina': pagina,
                'ordenacao': '-data',
            }
            resp = requests.get(url, params=params, timeout=60,
                                headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            if resp.status_code != 200:
                break

            data = resp.json()
            items = data.get('items', [])
            if not items:
                break

            # Filtrar somente dicts (a API pode retornar strings em busca geral)
            for item in items:
                if isinstance(item, dict):
                    todos.append(item)

            total = data.get('total', 0)
            if len(todos) >= total:
                break

            pagina += 1
        except Exception:
            break

    return todos


@st.cache_data(ttl=3600)
def consultar_dadosabertos_arps(cnpj_limpo, anos_janela=3, apenas_vigentes=False):
    """Consulta Atas de Registro de Preços no dadosabertos.compras.gov.br
    filtrando por CNPJ do fornecedor registrado na ata."""
    todos = []
    pagina = 1
    max_paginas = 20
    hoje = datetime.date.today()
    data_ini = (hoje - datetime.timedelta(days=365 * anos_janela)).strftime("%Y-%m-%d")
    data_fim = hoje.strftime("%Y-%m-%d")

    while pagina <= max_paginas:
        try:
            params = {
                'cnpjFornecedor': cnpj_limpo,
                'dataVigenciaInicialMin': data_ini,
                'dataVigenciaInicialMax': data_fim,
                'pagina': pagina,
                'tamanhoPagina': 50,
            }
            if apenas_vigentes:
                params['situacaoAta'] = 'VIGENTE'

            resp = requests.get(
                'https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP',
                params=params, timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'}, verify=False
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            itens = data.get('resultado', [])
            if not itens:
                break

            todos.extend(itens)

            total = data.get('totalRegistros', 0)
            if len(todos) >= total:
                break

            pagina += 1
        except Exception:
            break

    return todos


@st.cache_data(ttl=3600)
def consultar_pncp_atas(cnpj_limpo, anos_janela=3):
    """Consulta atas de registro de preços no PNCP via Search API.
    Busca atas associadas ao CNPJ do fornecedor."""
    todos = []
    pagina = 1
    max_paginas = 20

    while pagina <= max_paginas:
        try:
            url = "https://pncp.gov.br/api/search/"
            params = {
                'q': cnpj_limpo,
                'tipos_documento': 'ata',
                'pagina': pagina,
                'ordenacao': '-data',
            }
            resp = requests.get(url, params=params, timeout=60,
                                headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            if resp.status_code != 200:
                break

            data = resp.json()
            items = data.get('items', [])
            if not items:
                break

            for item in items:
                if isinstance(item, dict):
                    todos.append(item)

            total = data.get('total', 0)
            if len(todos) >= total:
                break

            pagina += 1
        except Exception:
            break

    return todos


@st.cache_data(ttl=3600)
def consultar_pncp_compras(cnpj_limpo):
    """Consulta compras/licitações no PNCP via Search API.
    Captura pregões, concorrências e outros processos licitatórios."""
    todos = []
    pagina = 1
    max_paginas = 20

    while pagina <= max_paginas:
        try:
            url = "https://pncp.gov.br/api/search/"
            params = {
                'q': cnpj_limpo,
                'tipos_documento': 'compra',
                'pagina': pagina,
                'ordenacao': '-data',
            }
            resp = requests.get(url, params=params, timeout=60,
                                headers={'User-Agent': 'Mozilla/5.0'}, verify=False)
            if resp.status_code != 200:
                break

            data = resp.json()
            items = data.get('items', [])
            if not items:
                break

            for item in items:
                if isinstance(item, dict):
                    todos.append(item)

            total = data.get('total', 0)
            if len(todos) >= total:
                break

            pagina += 1
        except Exception:
            break

    return todos


# ===================== NOTAS FISCAIS =====================

PASTA_ID = "1369rEJAqpprCP3dZp55eXaTcQRU9D5Ol"
DOWNLOAD_BASE = "https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "atacotada_nf")
os.makedirs(CACHE_DIR, exist_ok=True)

ARQUIVOS_FALLBACK = {
    "1HwHmY16I7OXmhdRqhaBbLY_tuyLe3plx": "202503_NFe_NotaFiscalItem.csv",
    "1vYWRVtDFCklm2o2TQJPbFbVzEGUZBKYt": "202504_NFe_NotaFiscalItem.csv",
    "13JjeGhNsIoUlfZH8ZnNOtB_xa3aCAyVJ": "202505_NFe_NotaFiscalItem.csv",
    "1j1y5PgaxbgRWbPkwymRBYE6kNNDSJeM6": "202506_NFe_NotaFiscalItem.csv",
    "1ibH9e3GRS638eLDoMyWsxcckKW4RYYFR": "202507_NFe_NotaFiscalItem.csv",
    "1wTiEvuD0NgSGXTbPB9LSlrFgqmXnZDUa": "202508_NFe_NotaFiscalItem.csv",
    "1ZJJtcfFpkCtQBfxUB-iOowv0buFq01VX": "202509_NFe_NotaFiscalItem.csv",
    "1sTDH3Zi38dZmsL3NOb1pcbV9WEDxn6yh": "202510_NFe_NotaFiscalItem.csv",
    "1jD1NLznnwvdHhWcr3NSBGeIzrRjMxX3g": "202511_NFe_NotaFiscalItem.csv",
    "1Ye9GhANeEErRuV4GjC3Y-wyn6HKUTSDh": "202512_NFe_NotaFiscalItem.csv",
    "1tSqz-nIiM_uDZW38GdWeRboNC7nwq3jH": "202601_NFe_NotaFiscalItem.csv",
    "1tgekwOo8__NZZSs2OdFMS6xT6pS3LXVn": "202602_NFe_NotaFiscalItem.csv",
}


@st.cache_data(ttl=600, show_spinner=False)
def listar_arquivos_disponiveis(folder_id):
    """Descobre os arquivos CSV disponíveis na pasta do Google Drive."""
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        ids_encontrados = re.findall(r'data-id="([a-zA-Z0-9_-]{20,})"', resp.text)
        ids_encontrados = list(dict.fromkeys(ids_encontrados))

        if not ids_encontrados:
            return None

        arquivos = {}
        for fid in ids_encontrados:
            try:
                view_url = f"https://drive.google.com/file/d/{fid}/view"
                view_resp = requests.get(view_url, timeout=15)
                title_match = re.search(r"<title>([^<]+)</title>", view_resp.text)
                if title_match:
                    nome = title_match.group(1).replace(" - Google Drive", "").strip()
                    if nome and nome != "Google Drive":
                        arquivos[fid] = nome
                    else:
                        arquivos[fid] = f"Arquivo {fid[:10]}"
                else:
                    arquivos[fid] = f"Arquivo {fid[:10]}"
            except Exception:
                arquivos[fid] = f"Arquivo {fid[:10]}"

        return arquivos if arquivos else None
    except Exception:
        return None


def baixar_arquivo_csv(file_id, progress_bar=None):
    """Baixa o arquivo CSV para cache local."""
    cache_path = os.path.join(CACHE_DIR, f"{file_id}.csv")

    if os.path.exists(cache_path):
        if os.path.getsize(cache_path) > 10000:
            return cache_path
        else:
            os.remove(cache_path)

    url = DOWNLOAD_BASE.format(file_id=file_id)
    response = requests.get(url, stream=True, timeout=600)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        response.close()
        raise Exception("O Google Drive retornou uma página de erro (quota de downloads excedida).")

    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    tmp_path = cache_path + ".tmp"

    with open(tmp_path, "wb") as f:
        for data in response.iter_content(chunk_size=131072):
            f.write(data)
            downloaded += len(data)
            if progress_bar and total:
                pct = min(downloaded / total, 1.0)
                mb_down = downloaded / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                progress_bar.progress(pct, text=f"Baixando... {mb_down:.0f} / {mb_total:.0f} MB ({pct*100:.0f}%)")

    with open(tmp_path, "rb") as f:
        head = f.read(200)
    if b"<!DOCTYPE" in head or b"<html" in head.lower():
        os.remove(tmp_path)
        raise Exception("O arquivo baixado não é um CSV válido (quota do Google Drive excedida).")

    os.rename(tmp_path, cache_path)
    return cache_path


@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_notas_por_cnpj(file_path, cnpj_busca, max_resultados=1000):
    """Pesquisa notas fiscais pelo CNPJ do emitente."""
    resultados = []
    total_linhas = 0
    cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj_busca)))

    for chunk in pd.read_csv(
        file_path,
        sep=";",
        encoding="latin-1",
        chunksize=50000,
        dtype=str,
        on_bad_lines="skip",
    ):
        col_cnpj = "CPF/CNPJ Emitente"
        if col_cnpj in chunk.columns:
            cnpj_col_limpo = chunk[col_cnpj].astype(str).str.replace(r'[.\-/]', '', regex=True).str.strip()
            mask = cnpj_col_limpo == cnpj_limpo
            filtered = chunk[mask]
            if len(filtered) > 0:
                resultados.append(filtered)

        total_linhas += len(chunk)
        total_encontrados = sum(len(r) for r in resultados)
        if total_encontrados >= max_resultados:
            break

    if resultados:
        df = pd.concat(resultados, ignore_index=True).head(max_resultados)
        return df, total_linhas
    return pd.DataFrame(), total_linhas


# ===================== SIDEBAR =====================

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
    <div class="sistema-nome">AtaCotada</div>
    <div class="subtitulo">Consulta detalhada de Fornecedores e Contratos</div>
</div>
""", unsafe_allow_html=True)

st.title("Consulta de Fornecedor por CNPJ")
st.markdown("Busque por informações de contato atualizadas e verifique o histórico de contratos com o Governo Federal.")

# ===================== INPUTS =====================

with st.container():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        cnpj_input = st.text_input("Digite o CNPJ (somente números ou com pontuação):", placeholder="Ex: 00.000.000/0001-00")
    with col2:
        anos_janela = st.number_input("Janela de Pesquisa (Anos de histórico):", min_value=1, max_value=10, value=3)

        hoje = datetime.date.today()
        data_ini = (hoje - datetime.timedelta(days=365 * anos_janela)).strftime("%Y-%m-%d")
        data_fim = hoje.strftime("%Y-%m-%d")

    with col3:
        st.write("")
        st.write("")
        btn_consultar = st.button("Consultar", use_container_width=True, type="primary")


# ===================== CONSULTA =====================

if btn_consultar and cnpj_input:
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj_input))
    if len(cnpj_limpo) != 14:
        st.error("CNPJ inválido. Certifique-se de preencher 14 dígitos inteiros.")
    else:
        st.session_state['cnpj_consulta'] = cnpj_limpo
        st.session_state['anos_janela'] = anos_janela

        ano_atual = hoje.year
        anos_busca = list(range(ano_atual, ano_atual - anos_janela, -1))

        with st.spinner(f"Consultando bases de dados para o CNPJ {formatar_cnpj(cnpj_limpo)}..."):
            # 1) Dados cadastrais (OpenCNPJ + BrasilAPI como fallback)
            dados_empresa = consultar_opencnpj(cnpj_limpo)
            dados_brasil_api = consultar_brasilapi(cnpj_limpo)

            # 2) Contratos via PNCP Search API (todos os contratos onde este CNPJ é o contratado)
            progress_contratos = st.progress(0, text="Consultando contratos no PNCP...")
            todos_contratos = consultar_pncp_search(cnpj_limpo, "contrato")
            progress_contratos.progress(0.20, text="Consultando compras/licitações no PNCP...")

            # 3) Compras/licitações (pregões, concorrências etc.)
            compras_pncp = consultar_pncp_compras(cnpj_limpo)
            progress_contratos.progress(0.40, text="Consultando atas de registro de preços (PNCP)...")

            # 4) Atas de Registro de Preços via PNCP Search API
            atas_pncp = consultar_pncp_atas(cnpj_limpo, anos_janela)
            progress_contratos.progress(0.60, text="Consultando atas e adesões vigentes (dadosabertos)...")

            # 5) Atas e adesões vigentes via dadosabertos (por cnpjFornecedor)
            atas_dadosabertos = consultar_dadosabertos_arps(cnpj_limpo, anos_janela, apenas_vigentes=False)
            adesoes_vigentes = [a for a in atas_dadosabertos
                                if str(a.get('situacaoAta', '')).upper() == 'VIGENTE'
                                or str(a.get('situacaoAta', '')).upper() == 'ATIVA']
            progress_contratos.progress(0.80, text="Classificando resultados...")

            # 6) Todos os contratos vão para a aba Contratos Governamentais (independente da modalidade)
            #    A aba Dispensas recebe apenas as compras (processos de compra) com modalidade dispensa
            contratos_pncp = todos_contratos  # TODOS os contratos onde este CNPJ é fornecedor
            dispensas_pncp = []              # Contratos por dispensa ficam na aba contratos também

            # 7) Separar compras por modalidade — pregões → Contratos, dispensas → Dispensas
            compras_pregao = [c for c in compras_pncp
                              if c.get('modalidade_licitacao_nome', '').lower() not in ('dispensa', 'inexigibilidade')]
            compras_dispensa = [c for c in compras_pncp
                                if c.get('modalidade_licitacao_nome', '').lower() in ('dispensa', 'inexigibilidade')]

            progress_contratos.progress(1.0, text="Consulta concluída!")
            progress_contratos.empty()

        st.session_state['dados_empresa'] = dados_empresa
        st.session_state['dados_brasil_api'] = dados_brasil_api
        st.session_state['contratos_pncp'] = contratos_pncp
        st.session_state['dispensas_pncp'] = dispensas_pncp
        st.session_state['compras_pregao'] = compras_pregao
        st.session_state['compras_dispensa'] = compras_dispensa
        st.session_state['atas_pncp'] = atas_pncp
        st.session_state['atas_dadosabertos'] = atas_dadosabertos
        st.session_state['adesoes_vigentes'] = adesoes_vigentes
        st.session_state['anos_busca'] = anos_busca
        st.session_state['data_ini'] = data_ini
        st.session_state['data_fim'] = data_fim


# ===================== EXIBIÇÃO POR ABAS =====================

if 'cnpj_consulta' in st.session_state:
    cnpj_limpo = st.session_state['cnpj_consulta']
    dados_empresa = st.session_state.get('dados_empresa')
    dados_brasil_api = st.session_state.get('dados_brasil_api')
    contratos_pncp = st.session_state.get('contratos_pncp', [])
    dispensas_pncp = st.session_state.get('dispensas_pncp', [])
    compras_pregao = st.session_state.get('compras_pregao', [])
    compras_dispensa = st.session_state.get('compras_dispensa', [])
    atas_pncp = st.session_state.get('atas_pncp', [])
    atas_dadosabertos = st.session_state.get('atas_dadosabertos', [])
    adesoes_vigentes = st.session_state.get('adesoes_vigentes', [])
    anos_busca = st.session_state.get('anos_busca', [])
    data_ini = st.session_state.get('data_ini', '')
    data_fim = st.session_state.get('data_fim', '')

    st.markdown("---")

    tab_empresa, tab_contratos, tab_atas, tab_adesoes, tab_compras, tab_nf = st.tabs([
        "🏢 Dados da Empresa",
        "📋 Contratos Governamentais",
        "📑 Atas de Registro de Preços",
        "🤝 Adesões Vigentes",
        "🛒 Dispensas / Contratação Direta",
        "📄 Notas Fiscais"
    ])

    # ==================== ABA 1: DADOS DA EMPRESA ====================
    with tab_empresa:
        if dados_empresa:
            nome_display = dados_empresa.get('nome_fantasia') or dados_empresa.get('razao_social', '')
            st.markdown(f"### Informações da Empresa: {nome_display}")

            # ---- Extrair email/telefone com fallback BrasilAPI ----
            email_raw = dados_empresa.get('email') or ''
            email_final = str(email_raw).strip()

            telefones_lista = dados_empresa.get('telefones') or []
            tel_formatado = ""
            if telefones_lista:
                tels = []
                for t in telefones_lista:
                    if not isinstance(t, dict):
                        continue
                    ddd = str(t.get('ddd') or '').strip()
                    numero = str(t.get('numero') or '').strip()
                    if ddd and numero:
                        tels.append(f"({ddd}) {numero}")
                    elif numero:
                        tels.append(numero)
                tel_formatado = " | ".join(tels)

            # Fallback: BrasilAPI
            if (not email_final or not tel_formatado) and dados_brasil_api:
                if not email_final:
                    email_fb = str(dados_brasil_api.get('email') or '').strip()
                    if email_fb:
                        email_final = email_fb

                if not tel_formatado:
                    ddd1 = str(dados_brasil_api.get('ddd_telefone_1') or '').strip()
                    ddd2 = str(dados_brasil_api.get('ddd_telefone_2') or '').strip()
                    # BrasilAPI retorna DDD+número concatenados (ex: '2121660000')
                    tels_fb = []
                    for raw_tel in [ddd1, ddd2]:
                        if raw_tel and len(raw_tel) >= 10:
                            tels_fb.append(f"({raw_tel[:2]}) {raw_tel[2:]}")
                        elif raw_tel:
                            tels_fb.append(raw_tel)
                    if tels_fb:
                        tel_formatado = " | ".join(tels_fb)

            email_display = email_final if email_final else "Não informado na Receita Federal"
            tel_display = tel_formatado if tel_formatado else "Não informado na Receita Federal"
            situacao = dados_empresa.get('situacao_cadastral') or dados_empresa.get('situacao', 'N/A')

            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-title">Identificação</div>
                    <div class="info-item"><span class="info-label">Razão Social:</span> <span class="info-value">{dados_empresa.get('razao_social', 'N/A')}</span></div>
                    <div class="info-item"><span class="info-label">Nome Fantasia:</span> <span class="info-value">{dados_empresa.get('nome_fantasia', 'N/A')}</span></div>
                    <div class="info-item"><span class="info-label">CNPJ:</span> <span class="info-value">{formatar_cnpj(cnpj_limpo)}</span></div>
                    <div class="info-item"><span class="info-label">Situação:</span> <span class="info-value">{situacao}</span></div>
                    <div class="info-item"><span class="info-label">Capital Social:</span> <span class="info-value">R$ {dados_empresa.get('capital_social', 'N/A')}</span></div>
                    <div class="info-item"><span class="info-label">Porte:</span> <span class="info-value">{dados_empresa.get('porte_empresa', 'N/A')}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with e_col2:
                ender = f"{dados_empresa.get('logradouro', '')}, {dados_empresa.get('numero', '')} - {dados_empresa.get('bairro', '')}"
                cidade_uf = f"{dados_empresa.get('municipio', '')}/{dados_empresa.get('uf', '')}"
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-title">Contato e Endereço</div>
                    <div class="info-item"><span class="info-label">📧 Email:</span> <span class="info-value">{email_display}</span></div>
                    <div class="info-item"><span class="info-label">📞 Telefone:</span> <span class="info-value">{tel_display}</span></div>
                    <div class="info-item"><span class="info-label">📍 Endereço:</span> <span class="info-value">{ender}</span></div>
                    <div class="info-item"><span class="info-label">🏙️ Cidade/UF:</span> <span class="info-value">{cidade_uf}</span></div>
                    <div class="info-item"><span class="info-label">📮 CEP:</span> <span class="info-value">{dados_empresa.get('cep', 'N/A')}</span></div>
                </div>
                """, unsafe_allow_html=True)

            if not email_final and not tel_formatado:
                st.info(
                    "ℹ️ Email e telefone não estão disponíveis nos dados públicos da Receita Federal para este CNPJ. "
                    "Foram consultadas as APIs OpenCNPJ e BrasilAPI. "
                    "Esses campos são opcionais no cadastro da RFB e muitas empresas não os informam."
                )

            # Quadro societário
            qsa = dados_empresa.get('QSA', [])
            if qsa:
                st.markdown("#### Quadro Societário (QSA)")
                qsa_data = []
                for socio in qsa:
                    qsa_data.append({
                        'Nome': socio.get('nome_socio', ''),
                        'Qualificação': socio.get('qualificacao_socio', ''),
                        'Entrada': socio.get('data_entrada_sociedade', ''),
                        'Tipo': socio.get('identificador_socio', ''),
                    })
                st.dataframe(pd.DataFrame(qsa_data), use_container_width=True, hide_index=True)
        else:
            st.warning("Não foi possível carregar os dados cadastrais desta empresa (OpenCNPJ).")

    # ==================== ABA 2: CONTRATOS ====================
    with tab_contratos:
        st.markdown("### Histórico de Contratos e Licitações")
        st.write("##### Fonte: PNCP — Portal Nacional de Contratações Públicas")

        todos_contratos_aba = contratos_pncp + compras_pregao

        if todos_contratos_aba and len(todos_contratos_aba) > 0:
            st.success(f"Encontrados **{len(todos_contratos_aba)}** registros associados a este CNPJ "
                       f"({len(contratos_pncp)} contratos, {len(compras_pregao)} compras/licitações).")

            for c in todos_contratos_aba:
                orgao_nome = c.get('orgao_nome', 'N/A')
                unidade_nome = c.get('unidade_nome', '')
                valor = c.get('valor_global', 0)
                titulo = c.get('title', 'N/A')
                descricao = c.get('description', 'N/A')
                vigencia_inicio = c.get('data_inicio_vigencia', 'N/A')
                vigencia_fim = c.get('data_fim_vigencia', 'N/A')
                modalidade = c.get('modalidade_licitacao_nome', 'N/A')
                situacao = c.get('situacao_nome', 'N/A')
                uf = c.get('uf', '')
                municipio = c.get('municipio_nome', '')
                url_pncp = c.get('item_url', '')
                link_pncp = f"https://pncp.gov.br/app{url_pncp}" if url_pncp else ''

                st.markdown(f"""
                <div class="contract-card">
                    <div class="contract-title">📄 {titulo} — {orgao_nome}</div>
                    <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Unidade:</strong> {unidade_nome} ({municipio}/{uf})</div>
                    <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Modalidade:</strong> {modalidade} | <strong>Situação:</strong> {situacao}</div>
                    <div style="margin-bottom:0.5rem; color:#cbd5e1;"><strong>Objeto:</strong> {str(descricao)[:200]}</div>
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; color:#cbd5e1; font-size:0.9rem;">
                        <div><strong>Vigência:</strong> {vigencia_inicio} a {vigencia_fim}</div>
                        <div style="color:#d4af37; font-weight:bold;">Valor: {formatar_moeda_br(valor)}</div>
                    </div>
                    {'<div style="margin-top:0.5rem;"><a href="' + link_pncp + '" target="_blank" style="color:#4da6ff;">🔗 Ver no PNCP</a></div>' if link_pncp else ''}
                </div>
                """, unsafe_allow_html=True)

            # Tabela resumo
            with st.expander("📊 Ver tabela resumo dos contratos/licitações"):
                df_contratos = pd.DataFrame([{
                    'Título': c.get('title', ''),
                    'Órgão': c.get('orgao_nome', 'N/A'),
                    'Unidade': c.get('unidade_nome', ''),
                    'Modalidade': c.get('modalidade_licitacao_nome', ''),
                    'Início Vigência': c.get('data_inicio_vigencia', ''),
                    'Fim Vigência': c.get('data_fim_vigencia', ''),
                    'Valor': formatar_moeda_br(c.get('valor_global', 0)),
                } for c in todos_contratos_aba])
                st.dataframe(df_contratos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum contrato ou licitação (Pregão, Concorrência etc.) encontrado no PNCP para este CNPJ. "
                    "Verifique a aba **Dispensas / Contratação Direta** e **Atas de Registro de Preços**.")

    # ==================== ABA 3: ATAS DE REGISTRO DE PREÇOS ====================
    with tab_atas:
        st.markdown("### Atas de Registro de Preços")
        st.write("##### Fonte: PNCP — Portal Nacional de Contratações Públicas (Search API)")

        if atas_pncp and len(atas_pncp) > 0:
            st.success(f"Encontradas **{len(atas_pncp)}** atas de registro de preços associadas a este CNPJ.")

            for ata in atas_pncp:
                orgao_nome = ata.get('orgao_nome', 'N/A')
                unidade_nome = ata.get('unidade_nome', '')
                titulo = ata.get('title', 'N/A')
                descricao = ata.get('description', 'N/A')
                data_pub = str(ata.get('data_publicacao_pncp', ''))[:10]
                situacao = ata.get('situacao_nome', 'N/A')
                modalidade = ata.get('modalidade_licitacao_nome', 'N/A')
                valor = ata.get('valor_global') or ata.get('valor_total_estimado', 0)
                uf = ata.get('uf', '')
                municipio = ata.get('municipio_nome', '')
                url_pncp = ata.get('item_url', '')
                link_pncp = f"https://pncp.gov.br/app{url_pncp}" if url_pncp else ''

                st.markdown(f"""
                <div class="contract-card">
                    <div class="contract-title">📑 {titulo} — {orgao_nome}</div>
                    <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Unidade:</strong> {unidade_nome} ({municipio}/{uf})</div>
                    <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Modalidade:</strong> {modalidade} | <strong>Situação:</strong> {situacao}</div>
                    <div style="margin-bottom:0.5rem; color:#cbd5e1;"><strong>Objeto:</strong> {str(descricao)[:200]}</div>
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; color:#cbd5e1; font-size:0.9rem;">
                        <div><strong>Publicação:</strong> {data_pub}</div>
                        <div style="color:#d4af37; font-weight:bold;">Valor: {formatar_moeda_br(valor)}</div>
                    </div>
                    {'<div style="margin-top:0.5rem;"><a href="' + link_pncp + '" target="_blank" style="color:#4da6ff;">🔗 Ver no PNCP</a></div>' if link_pncp else ''}
                </div>
                """, unsafe_allow_html=True)

            with st.expander("📊 Ver tabela resumo das atas"):
                df_atas = pd.DataFrame([{
                    'Título': a.get('title', ''),
                    'Órgão': a.get('orgao_nome', 'N/A'),
                    'Modalidade': a.get('modalidade_licitacao_nome', 'N/A'),
                    'Situação': a.get('situacao_nome', 'N/A'),
                    'Publicação': str(a.get('data_publicacao_pncp', ''))[:10],
                    'Valor': formatar_moeda_br(a.get('valor_global') or a.get('valor_total_estimado', 0)),
                } for a in atas_pncp])
                st.dataframe(df_atas, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma ata de registro de preços encontrada no PNCP para este CNPJ. "
                    "Verifique a aba **🤝 Adesões Vigentes** para atas no ComprasGov.")

    # ==================== ABA 4: ADESÕES VIGENTES ====================
    with tab_adesoes:
        st.markdown("### Adesões Vigentes")
        st.write("##### Fonte: ComprasGov — Atas de Registro de Preços onde este CNPJ é fornecedor registrado")

        # Combina todas as ARPs (dadosabertos): filtra as vigentes/ativas para exibição destacada
        todos_arps_dadosabertos = atas_dadosabertos if atas_dadosabertos else []
        vigentes = [a for a in todos_arps_dadosabertos
                    if str(a.get('situacaoAta', '')).upper() in ('VIGENTE', 'ATIVA')]
        encerradas = [a for a in todos_arps_dadosabertos
                      if str(a.get('situacaoAta', '')).upper() not in ('VIGENTE', 'ATIVA')]

        if todos_arps_dadosabertos:
            st.success(f"Encontradas **{len(todos_arps_dadosabertos)}** atas associadas a este CNPJ "
                       f"({len(vigentes)} vigentes, {len(encerradas)} encerradas).")

            # Subtabs: Vigentes e Todas
            sub_vigentes, sub_todas = st.tabs(["🟢 Vigentes", "📋 Todas"])

            def _render_arps(arps_lista):
                for arp in arps_lista:
                    numero_ata = arp.get('numeroAta') or arp.get('numeroAtaRegistroPreco', 'N/A')
                    orgao = arp.get('nomeOrgao') or arp.get('orgao', 'N/A')
                    unidade = arp.get('nomeUnidadeGestora') or arp.get('unidadeGestora', '')
                    situacao = arp.get('situacaoAta', 'N/A')
                    data_ini_arp = str(arp.get('dataVigenciaInicial') or arp.get('dataInicioVigencia', ''))[:10]
                    data_fim_arp = str(arp.get('dataVigenciaFinal') or arp.get('dataFimVigencia', ''))[:10]
                    objeto = arp.get('objetoAtaRegistroPreco') or arp.get('descricaoObjeto') or arp.get('objeto', 'N/A')
                    valor = arp.get('valorTotalAta') or arp.get('valorTotal') or 0
                    numero_pncp = arp.get('numeroPncp') or arp.get('numeroControlePNCP', '')

                    cor = "🟢" if str(situacao).upper() in ('VIGENTE', 'ATIVA') else "🔴"
                    header = f"{cor} ARP nº {numero_ata} — {orgao}"
                    if unidade and unidade != orgao:
                        header += f" / {unidade}"

                    with st.expander(header):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Situação", situacao)
                        col2.metric("Vigência", f"{data_ini_arp} → {data_fim_arp}")
                        col3.metric("Valor Total", formatar_moeda_br(valor))
                        st.write(f"**Objeto:** {objeto}")
                        if numero_pncp:
                            link_pncp = f"https://pncp.gov.br/app/atas/{numero_pncp.replace('/', '-')}"
                            st.markdown(f"[🔗 Ver no PNCP]({link_pncp})")

            with sub_vigentes:
                if vigentes:
                    _render_arps(vigentes)
                else:
                    st.info("Nenhuma ata vigente encontrada para este CNPJ no período consultado.")

            with sub_todas:
                if todos_arps_dadosabertos:
                    _render_arps(todos_arps_dadosabertos)
                    # Tabela resumida
                    df_arps = pd.DataFrame([{
                        'Nº ATA': a.get('numeroAta') or a.get('numeroAtaRegistroPreco', ''),
                        'Órgão': a.get('nomeOrgao') or a.get('orgao', ''),
                        'Situação': a.get('situacaoAta', ''),
                        'Início Vigência': str(a.get('dataVigenciaInicial') or a.get('dataInicioVigencia', ''))[:10],
                        'Fim Vigência': str(a.get('dataVigenciaFinal') or a.get('dataFimVigencia', ''))[:10],
                        'Valor Total': formatar_moeda_br(a.get('valorTotalAta') or a.get('valorTotal') or 0),
                    } for a in todos_arps_dadosabertos])
                    st.dataframe(df_arps, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma ata de registro de preços encontrada no ComprasGov para este CNPJ no período consultado.")

    # ==================== ABA 5: DISPENSAS / CONTRATAÇÃO DIRETA ====================
    with tab_compras:
        st.markdown("### Dispensas / Contratação Direta")
        st.write("##### Fonte: PNCP — Portal Nacional de Contratações Públicas")

        todas_dispensas_aba = dispensas_pncp + compras_dispensa

        if todas_dispensas_aba and len(todas_dispensas_aba) > 0:
            st.success(f"Encontradas **{len(todas_dispensas_aba)}** compras/contratações diretas associadas a este CNPJ.")

            for c in todas_dispensas_aba:
                orgao_nome = c.get('orgao_nome', 'N/A')
                unidade_nome = c.get('unidade_nome', '')
                valor = c.get('valor_global') or c.get('valor_total_estimado', 0)
                titulo = c.get('title', 'N/A')
                descricao = c.get('description', 'N/A')
                modalidade = c.get('modalidade_licitacao_nome', 'N/A')
                situacao = c.get('situacao_nome', 'N/A')
                data_pub = c.get('data_publicacao_pncp', 'N/A')
                uf = c.get('uf', '')
                municipio = c.get('municipio_nome', '')
                url_pncp = c.get('item_url', '')
                link_pncp = f"https://pncp.gov.br/app{url_pncp}" if url_pncp else ''

                st.markdown(f"""
                <div class="contract-card">
                    <div class="contract-title">🛒 {titulo} — {orgao_nome}</div>
                    <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Unidade:</strong> {unidade_nome} ({municipio}/{uf})</div>
                    <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Modalidade:</strong> {modalidade} | <strong>Situação:</strong> {situacao}</div>
                    <div style="margin-bottom:0.5rem; color:#cbd5e1;"><strong>Objeto:</strong> {str(descricao)[:200]}</div>
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; color:#cbd5e1; font-size:0.9rem;">
                        <div><strong>Publicação:</strong> {str(data_pub)[:10]}</div>
                        <div style="color:#d4af37; font-weight:bold;">Valor: {formatar_moeda_br(valor)}</div>
                    </div>
                    {'<div style="margin-top:0.5rem;"><a href="' + link_pncp + '" target="_blank" style="color:#4da6ff;">🔗 Ver no PNCP</a></div>' if link_pncp else ''}
                </div>
                """, unsafe_allow_html=True)

            with st.expander("📊 Ver tabela resumo"):
                df_dispensas = pd.DataFrame([{
                    'Título': c.get('title', ''),
                    'Órgão': c.get('orgao_nome', 'N/A'),
                    'Modalidade': c.get('modalidade_licitacao_nome', 'N/A'),
                    'Situação': c.get('situacao_nome', 'N/A'),
                    'Publicação': str(c.get('data_publicacao_pncp', ''))[:10],
                    'Valor': formatar_moeda_br(c.get('valor_global') or c.get('valor_total_estimado', 0)),
                } for c in todas_dispensas_aba])
                st.dataframe(df_dispensas, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma compra/contratação direta encontrada no PNCP para este CNPJ.")

    # ==================== ABA 6: NOTAS FISCAIS ====================
    with tab_nf:
        st.markdown("### Pesquisa em Notas Fiscais")
        st.markdown(f"Buscando o CNPJ **{formatar_cnpj(cnpj_limpo)}** nos arquivos de Notas Fiscais do Portal da Transparência.")

        # Tentar listagem dinâmica da pasta do Drive, com fallback para dict estático
        arquivos_drive = listar_arquivos_disponiveis(PASTA_ID)
        if arquivos_drive:
            arquivos_dict = arquivos_drive
        else:
            arquivos_dict = ARQUIVOS_FALLBACK

        nomes_arqs = list(arquivos_dict.values())
        ids_arqs = list(arquivos_dict.keys())

        # Ordenar por nome (YYYYMM)
        idx_sorted = sorted(range(len(nomes_arqs)), key=lambda i: nomes_arqs[i], reverse=True)
        nomes_sorted = [nomes_arqs[i] for i in idx_sorted]
        ids_sorted = [ids_arqs[i] for i in idx_sorted]

        arquivos_selecionados = st.multiselect(
            "Selecione os meses para pesquisar:",
            options=range(len(nomes_sorted)),
            format_func=lambda i: nomes_sorted[i],
            default=[0, 1, 2] if len(nomes_sorted) >= 3 else list(range(len(nomes_sorted))),
            key="nf_cnpj_multiselect"
        )

        btn_nf = st.button("🔍 Pesquisar nas Notas Fiscais", type="primary", key="btn_nf_cnpj")

        if btn_nf and arquivos_selecionados:
            resultados_nf_total = []

            for idx in arquivos_selecionados:
                file_id = ids_sorted[idx]
                nome_arquivo = nomes_sorted[idx]

                st.markdown(f"**Processando:** {nome_arquivo}")
                progress_nf = st.progress(0, text=f"Baixando {nome_arquivo}...")

                try:
                    caminho = baixar_arquivo_csv(file_id, progress_bar=progress_nf)
                    progress_nf.progress(0.5, text=f"Pesquisando CNPJ em {nome_arquivo}...")

                    df_resultado, total_linhas = pesquisar_notas_por_cnpj(caminho, cnpj_limpo)
                    progress_nf.progress(1.0, text=f"Concluído: {nome_arquivo}")
                    progress_nf.empty()

                    if not df_resultado.empty:
                        df_resultado = df_resultado.copy()
                        df_resultado['_arquivo_origem'] = nome_arquivo
                        resultados_nf_total.append(df_resultado)
                        st.success(f"✅ {nome_arquivo}: **{len(df_resultado)}** notas encontradas (de {total_linhas:,} registros)")
                    else:
                        st.info(f"📭 {nome_arquivo}: Nenhuma nota encontrada para este CNPJ.")

                except Exception as e:
                    progress_nf.empty()
                    st.error(f"❌ Erro ao processar {nome_arquivo}: {str(e)}")

            if resultados_nf_total:
                df_todas_nf = pd.concat(resultados_nf_total, ignore_index=True)
                st.markdown("---")
                st.markdown(f"### Resultados Consolidados: {len(df_todas_nf)} notas fiscais encontradas")

                colunas_prio = [
                    '_arquivo_origem',
                    'CPF/CNPJ Emitente',
                    'RAZÃO SOCIAL EMITENTE',
                    'UF EMITENTE',
                    'MUNICÍPIO EMITENTE',
                    'NOME DESTINATÁRIO',
                    'UF DESTINATÁRIO',
                    'DESCRIÇÃO DO PRODUTO/SERVIÇO',
                    'QUANTIDADE COMERCIAL',
                    'VALOR UNITÁRIO DO PRODUTO',
                    'VALOR TOTAL DA NOTA',
                ]
                colunas_existentes = [c for c in colunas_prio if c in df_todas_nf.columns]
                outras_colunas = [c for c in df_todas_nf.columns if c not in colunas_existentes]

                df_exibir = df_todas_nf[colunas_existentes + outras_colunas]
                df_exibir = df_exibir.rename(columns={'_arquivo_origem': 'Período'})

                st.dataframe(df_exibir, use_container_width=True, hide_index=True)

                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1:
                    st.metric("Total de Notas", len(df_todas_nf))
                with col_s2:
                    if 'VALOR TOTAL DA NOTA' in df_todas_nf.columns:
                        try:
                            val_total = pd.to_numeric(
                                df_todas_nf['VALOR TOTAL DA NOTA'].str.replace(',', '.'),
                                errors='coerce'
                            ).sum()
                            st.metric("Valor Total", formatar_moeda_br(val_total))
                        except:
                            st.metric("Valor Total", "N/A")
                with col_s3:
                    periodos = df_todas_nf['_arquivo_origem'].nunique() if '_arquivo_origem' in df_todas_nf.columns else 0
                    st.metric("Períodos com notas", periodos)

                csv_export = df_exibir.to_csv(index=False, sep=";", encoding="utf-8-sig")
                st.download_button(
                    "📥 Baixar resultados em CSV",
                    data=csv_export,
                    file_name=f"notas_fiscais_{cnpj_limpo}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Nenhuma nota fiscal encontrada para este CNPJ nos meses selecionados.")
        elif btn_nf and not arquivos_selecionados:
            st.warning("Selecione ao menos um mês para pesquisar.")
