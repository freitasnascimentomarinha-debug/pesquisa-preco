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
def consultar_comprasgov(cnpj_limpo):
    """Consulta contratos no ComprasGov (API antiga)."""
    try:
        url = f"http://compras.dados.gov.br/contratos/v1/contratos.json?cnpj_contratada={cnpj_limpo}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            dados = resp.json()
            if isinstance(dados, dict) and 'resultado' in dados:
                return dados['resultado']
            elif isinstance(dados, dict) and '_embedded' in dados:
                return dados['_embedded'].get('contratos', [])
            return dados if isinstance(dados, list) else []
    except Exception:
        return []
    return []


@st.cache_data(ttl=3600)
def consultar_compras_sem_licitacao(ano):
    """Consulta compras sem licitação (Endpoint 5) por ano."""
    try:
        url = "https://dadosabertos.compras.gov.br/modulo-legado/5_consultarComprasSemLicitacao"
        params = {
            'dt_ano_aviso': ano,
            'pagina': 1,
            'tamanhoPagina': 500
        }
        resp = requests.get(url, params=params, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and 'resultado' in data:
                return data['resultado']
        return []
    except Exception:
        return []


@st.cache_data(ttl=3600)
def consultar_itens_compras_sem_licitacao(cnpj_limpo, ano):
    """Consulta itens de compras sem licitação (Endpoint 6) por ano.
    Busca página a página e filtra pelo CNPJ do fornecedor vencedor."""
    todos_itens = []
    pagina = 1
    max_paginas = 20

    while pagina <= max_paginas:
        try:
            url = "https://dadosabertos.compras.gov.br/modulo-legado/6_consultarCompraItensSemLicitacao"
            params = {
                'dt_ano_aviso_licitacao': ano,
                'pagina': pagina,
                'tamanhoPagina': 500
            }
            resp = requests.get(url, params=params, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code != 200:
                break

            data = resp.json()
            if isinstance(data, dict) and 'resultado' in data:
                resultados = data['resultado']
                if not resultados:
                    break

                for item in resultados:
                    cnpj_vencedor = str(item.get('nuCnpjVencedor', '')).replace('.', '').replace('/', '').replace('-', '').strip()
                    if cnpj_vencedor == cnpj_limpo:
                        todos_itens.append(item)

                if len(resultados) < 500:
                    break
                pagina += 1
            else:
                break
        except Exception:
            break

    return todos_itens


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

            # 2) Contratos ComprasGov
            contratos_cg = consultar_comprasgov(cnpj_limpo)

            # 3) Compras sem licitação – Endpoints 5 e 6 (por ano)
            compras_ep5_total = []
            compras_ep6_total = []

            progress_compras = st.progress(0, text="Consultando compras sem licitação...")
            for i, ano in enumerate(anos_busca):
                progress_compras.progress(
                    (i + 1) / len(anos_busca),
                    text=f"Consultando compras sem licitação — Ano {ano}... ({i+1}/{len(anos_busca)})"
                )

                # Endpoint 6: Itens (filtra por CNPJ do vencedor)
                itens_ano = consultar_itens_compras_sem_licitacao(cnpj_limpo, ano)
                if itens_ano:
                    compras_ep6_total.extend(itens_ano)

                # Endpoint 5: Compras gerais (sem filtro CNPJ na API)
                compras_ano = consultar_compras_sem_licitacao(ano)
                if compras_ano:
                    compras_ep5_total.extend(compras_ano)

            progress_compras.empty()

        st.session_state['dados_empresa'] = dados_empresa
        st.session_state['dados_brasil_api'] = dados_brasil_api
        st.session_state['contratos_cg'] = contratos_cg
        st.session_state['compras_ep5'] = compras_ep5_total
        st.session_state['compras_ep6'] = compras_ep6_total
        st.session_state['anos_busca'] = anos_busca
        st.session_state['data_ini'] = data_ini
        st.session_state['data_fim'] = data_fim


# ===================== EXIBIÇÃO POR ABAS =====================

if 'cnpj_consulta' in st.session_state:
    cnpj_limpo = st.session_state['cnpj_consulta']
    dados_empresa = st.session_state.get('dados_empresa')
    dados_brasil_api = st.session_state.get('dados_brasil_api')
    contratos_cg = st.session_state.get('contratos_cg', [])
    compras_ep5 = st.session_state.get('compras_ep5', [])
    compras_ep6 = st.session_state.get('compras_ep6', [])
    anos_busca = st.session_state.get('anos_busca', [])
    data_ini = st.session_state.get('data_ini', '')
    data_fim = st.session_state.get('data_fim', '')

    st.markdown("---")

    tab_empresa, tab_contratos, tab_compras, tab_nf = st.tabs([
        "🏢 Dados da Empresa",
        "📋 Contratos Governamentais",
        "🛒 Compras sem Licitação",
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
        st.markdown("### Histórico de Contratos Governamentais")
        st.write("##### Fonte: Dados Abertos Compras.gov.br")

        if contratos_cg and len(contratos_cg) > 0:
            contratos_filtrados = []
            for c in contratos_cg:
                data_ass = c.get('data_assinatura') or c.get('data_inicio_vigencia')
                if data_ass and data_ini and data_fim and data_ass >= data_ini and data_ass <= data_fim:
                    contratos_filtrados.append(c)
                elif not data_ass:
                    contratos_filtrados.append(c)

            st.success(f"Encontrados {len(contratos_filtrados)} contratos no período analisado.")
            for c in contratos_filtrados:
                uasg_nome = c.get('nome_orgao') or c.get('ug_nome', 'N/A')
                uasg_cod = c.get('codigo_orgao') or c.get('ug', '')
                valor = c.get('valor_inicial') or c.get('valor_total', 0)
                objeto = c.get('objeto', 'N/A')
                vigencia_inicio = c.get('data_inicio_vigencia') or c.get('data_assinatura', 'N/A')
                vigencia_fim = c.get('data_fim_vigencia', 'N/A')

                st.markdown(f"""
                <div class="contract-card">
                    <div class="contract-title">📄 Órgão/UASG: {uasg_cod} - {uasg_nome}</div>
                    <div style="margin-bottom:0.5rem; color:#cbd5e1;"><strong>Objeto:</strong> {objeto}</div>
                    <div style="display:flex; justify-content:space-between; flex-wrap:wrap; color:#cbd5e1; font-size:0.9rem;">
                        <div><strong>Vigência:</strong> {vigencia_inicio} a {vigencia_fim}</div>
                        <div style="color:#d4af37; font-weight:bold;">Valor: {formatar_moeda_br(valor)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum contrato encontrado associado a este CNPJ no Compras.gov.br dentro deste período.")

    # ==================== ABA 3: COMPRAS SEM LICITAÇÃO ====================
    with tab_compras:
        st.markdown("### Compras sem Licitação")
        st.markdown(f"Pesquisa nos anos: **{', '.join(str(a) for a in sorted(anos_busca, reverse=True))}** (últimos {len(anos_busca)} anos)")

        sub_tab_itens, sub_tab_compras = st.tabs([
            "📦 Itens de Compras (Endpoint 6)",
            "📋 Compras Gerais (Endpoint 5)"
        ])

        # ---- Sub-aba: Endpoint 6 ----
        with sub_tab_itens:
            st.markdown("##### Fonte: `modulo-legado/6_consultarCompraItensSemLicitacao`")
            st.caption("Itens de compras sem licitação onde este CNPJ foi o fornecedor vencedor.")

            if compras_ep6 and len(compras_ep6) > 0:
                st.success(f"Encontrados **{len(compras_ep6)}** itens de compras para este CNPJ.")

                df_ep6 = pd.DataFrame(compras_ep6)
                mapa_6 = {
                    'dtAnoAvisoLicitacao': 'Ano',
                    'coUasg': 'UASG',
                    'noModalidadeLicitacao': 'Modalidade',
                    'dsObjetoLicitacao': 'Objeto',
                    'noConjuntoMateriais': 'Material',
                    'noServico': 'Serviço',
                    'dsDetalhada': 'Descrição Detalhada',
                    'vrEstimadoItem': 'Valor Estimado',
                    'noFornecedorVencedor': 'Fornecedor',
                    'noUnidadeMedida': 'Unidade',
                    'qtMaterialAlt': 'Quantidade',
                }
                cols_6 = [c for c in mapa_6 if c in df_ep6.columns]
                if cols_6:
                    df_show6 = df_ep6[cols_6].rename(columns=mapa_6)
                    if 'Valor Estimado' in df_show6.columns:
                        df_show6['Valor Estimado'] = df_show6['Valor Estimado'].apply(formatar_moeda_br)
                    st.dataframe(df_show6, use_container_width=True, hide_index=True)

                    try:
                        total_v = sum(float(it.get('vrEstimadoItem', 0) or 0) for it in compras_ep6)
                        st.markdown(f"**Valor total estimado:** {formatar_moeda_br(total_v)}")
                    except:
                        pass

                with st.expander("📋 Ver detalhes completos dos itens"):
                    for i, item in enumerate(compras_ep6):
                        st.markdown(f"""
                        <div class="contract-card">
                            <div class="contract-title">📦 Item {i+1} — UASG {item.get('coUasg', 'N/A')} | Ano {item.get('dtAnoAvisoLicitacao', '')}</div>
                            <div style="color:#cbd5e1;margin-bottom:0.3rem;"><strong>Modalidade:</strong> {item.get('noModalidadeLicitacao', 'N/A')}</div>
                            <div style="color:#cbd5e1;margin-bottom:0.3rem;"><strong>Objeto:</strong> {str(item.get('dsObjetoLicitacao', 'N/A'))[:200]}</div>
                            <div style="color:#cbd5e1;margin-bottom:0.3rem;"><strong>Material/Serviço:</strong> {item.get('noConjuntoMateriais', '') or item.get('noServico', 'N/A')}</div>
                            <div style="color:#cbd5e1;margin-bottom:0.3rem;"><strong>Descrição:</strong> {str(item.get('dsDetalhada', 'N/A'))[:200]}</div>
                            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;color:#cbd5e1;font-size:0.9rem;margin-top:0.5rem;">
                                <div><strong>Fornecedor:</strong> {item.get('noFornecedorVencedor', 'N/A')}</div>
                                <div style="color:#d4af37;font-weight:bold;">Valor: {formatar_moeda_br(item.get('vrEstimadoItem', 0))}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Nenhum item de compra sem licitação encontrado para este CNPJ como fornecedor vencedor nos anos pesquisados.")

        # ---- Sub-aba: Endpoint 5 ----
        with sub_tab_compras:
            st.markdown("##### Fonte: `modulo-legado/5_consultarComprasSemLicitacao`")
            st.caption("Lista geral de compras sem licitação por ano (a API não suporta filtro por CNPJ).")

            if compras_ep5 and len(compras_ep5) > 0:
                st.success(f"Encontradas **{len(compras_ep5)}** compras sem licitação no período.")

                df_ep5 = pd.DataFrame(compras_ep5)
                mapa_5 = {
                    'dt_ano_aviso': 'Ano',
                    'co_uasg': 'UASG',
                    'no_ausg': 'Nome UASG',
                    'co_modalidade_licitacao': 'Mod. Licitação',
                    'ds_objeto_licitacao': 'Objeto',
                    'vr_estimado': 'Valor Estimado',
                    'ds_fundamento_legal': 'Fundamento Legal',
                    'nu_processo': 'Processo',
                }
                cols_5 = [c for c in mapa_5 if c in df_ep5.columns]
                if cols_5:
                    df_show5 = df_ep5[cols_5].rename(columns=mapa_5)
                    if 'Valor Estimado' in df_show5.columns:
                        df_show5['Valor Estimado'] = df_show5['Valor Estimado'].apply(formatar_moeda_br)
                    st.dataframe(df_show5, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma compra sem licitação encontrada nos anos pesquisados.")

    # ==================== ABA 4: NOTAS FISCAIS ====================
    with tab_nf:
        st.markdown("### Pesquisa em Notas Fiscais")
        st.markdown(f"Buscando o CNPJ **{formatar_cnpj(cnpj_limpo)}** nos arquivos de Notas Fiscais do Portal da Transparência.")

        nomes_arqs = list(ARQUIVOS_FALLBACK.values())
        ids_arqs = list(ARQUIVOS_FALLBACK.keys())

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
