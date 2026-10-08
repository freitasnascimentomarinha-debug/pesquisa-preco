import base64
import streamlit as st
import requests
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # módulos da raiz do projeto
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('catmat_busca', 'cotacao_rapida', 'relatorio_cotacao_rapida', 'fornecedores_nf', 'nf_lote', 'relatorio_nf_lote', 'nf_lote_ui')
from nf_lote_ui import renderizar_lote  # noqa: E402

# Configuração da página
st.set_page_config(
    page_title="AtaCotada - Notas Fiscais",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
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

        /* Filtros container */
        .filtros-container {
            background: linear-gradient(135deg, #0a2540 0%, #164863 100%);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            border-left: 5px solid #d4af37;
        }

        /* Cards de estatísticas */
        .stats-card {
            background: linear-gradient(135deg, #0a2540 0%, #0f4c75 100%);
            padding: 1.5rem;
            border-radius: 8px;
            border-left: 5px solid #d4af37;
            margin-bottom: 1rem;
        }

        /* Botões */
        .stButton > button {
            background-color: #d4af37;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 0.75rem 1.5rem;
            font-weight: bold;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            background-color: #ffd700;
            color: #ffffff;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(212, 175, 55, 0.3);
        }

        /* Botões de download */
        .stDownloadButton > button {
            background-color: #d4af37 !important;
            color: #ffffff !important;
            border: none !important;
        }

        .stDownloadButton > button:hover {
            background-color: #ffd700 !important;
            color: #ffffff !important;
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background-color: #0a2540 !important;
            color: #ffffff !important;
            border: 2px solid #0033cc !important;
            border-radius: 6px !important;
        }

        label {
            color: #ffffff !important;
        }

        /* Títulos */
        h1, h2, h3 {
            color: #d4af37;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }

        /* Tabelas */
        [data-testid="stDataFrame"] {
            background-color: #ffffff !important;
            border-radius: 8px;
            overflow: hidden;
        }

        th {
            background-color: #ffffff !important;
            color: #333333 !important;
            font-weight: bold;
            border-bottom: 2px solid #d4af37 !important;
        }

        td {
            background-color: #ffffff !important;
            color: #333333 !important;
        }

        tr:hover {
            background-color: #f5f5f5 !important;
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
    </style>
""", unsafe_allow_html=True)

# ===== SIDEBAR - Navegação customizada =====
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

# Header
st.markdown("""
    <div class="header-container">
        <div class="logo-text">⚓ MARINHA DO BRASIL ⚓</div>
        <div class="sistema-nome">AtaCotada</div>
        <div class="subtitulo">Notas Fiscais</div>
    </div>
""", unsafe_allow_html=True)

# ===== CONTEÚDO - NOTAS FISCAIS =====
st.title("📄 Notas Fiscais")
st.markdown("Pesquise **um ou vários itens** de uma vez em todos os arquivos mensais de notas fiscais eletrônicas dos dados abertos do **Portal da Transparência**.")

NFE_URL = "https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?tipoConsulta=resumo&tipoConteudo=7PhJ+gAVw2g="

# --- Configuração da fonte de dados ---
PASTA_ID = "1369rEJAqpprCP3dZp55eXaTcQRU9D5Ol"
DOWNLOAD_BASE = "https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "atacotada_nf")
os.makedirs(CACHE_DIR, exist_ok=True)

# Fallback caso a listagem falhe
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


# --- Funções auxiliares ---
@st.cache_data(ttl=600, show_spinner=False)
def listar_arquivos_disponiveis(folder_id):
    """Descobre os arquivos CSV disponíveis no Portal da Transparência."""
    url = f"https://drive.google.com/drive/folders/{folder_id}"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        # Extrair data-id dos elementos do HTML
        ids_encontrados = re.findall(r'data-id="([a-zA-Z0-9_-]{20,})"', resp.text)
        ids_encontrados = list(dict.fromkeys(ids_encontrados))  # Remove duplicatas

        if not ids_encontrados:
            return None

        # Obter nomes dos arquivos via título da página do Google Drive
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

    # Verificar cache existente — descartar se for muito pequeno (provável HTML de erro)
    if os.path.exists(cache_path):
        if os.path.getsize(cache_path) > 10000:
            return cache_path
        else:
            os.remove(cache_path)

    url = DOWNLOAD_BASE.format(file_id=file_id)
    response = requests.get(url, stream=True, timeout=600)
    response.raise_for_status()

    # Detectar resposta HTML (quota excedida, página de confirmação, etc.)
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        response.close()
        raise Exception(
            "O Google Drive retornou uma página de erro (quota de downloads excedida). "
            "Tente novamente em alguns minutos."
        )

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

    # Validar que o arquivo baixado é CSV (não HTML de erro)
    with open(tmp_path, "rb") as f:
        head = f.read(200)
    if b"<!DOCTYPE" in head or b"<html" in head.lower():
        os.remove(tmp_path)
        raise Exception(
            "O arquivo baixado não é um CSV válido (quota de downloads do Google Drive excedida). "
            "Tente novamente em alguns minutos."
        )

    os.rename(tmp_path, cache_path)
    return cache_path



# ===== PESQUISA (um ou vários itens, todos os arquivos) =====
def _arquivos_do_portal():
    """{id: nome} dos arquivos mensais (lista do Drive, com o fallback conhecido se a listagem falhar)."""
    return listar_arquivos_disponiveis(PASTA_ID) or ARQUIVOS_FALLBACK.copy()


renderizar_lote(_arquivos_do_portal, baixar_arquivo_csv, CACHE_DIR)

# ===== Como conferir a nota no Portal da NF-e =====
with st.expander("📋 Como conferir uma nota e baixar o DANFE/XML no Portal da NF-e (Receita Federal)"):
    st.link_button("🌐 Acessar o Portal da NF-e (Receita Federal)", NFE_URL, use_container_width=True)
    st.markdown("""
    <div style="background: #0a2540; border: 1px solid #333; border-radius: 8px; padding: 1.2rem; margin-top: 0.5rem;">
        <p style="color: #d4af37; font-weight: bold; font-size: 15px; margin-bottom: 0.8rem;">📌 Como usar:</p>
        <ol style="color: #cccccc; font-size: 13px; line-height: 2.2;">
            <li>Na pesquisa acima, localize a <b>chave de acesso</b> (44 dígitos) da nota (também está na relação de NF-e do relatório).</li>
            <li>Abra o <b>Portal da NF-e</b> da Receita Federal pelo botão acima.</li>
            <li>Cole a <b>chave de acesso</b>, resolva o captcha e clique em <b>"Continuar"</b>.</li>
            <li>Na tela de resultado, confira emitente, data e valor e baixe o <b>DANFE (PDF)</b> ou o <b>XML</b> completo da nota.</li>
        </ol>
        <hr style="border-color: #333; margin: 1rem 0;">
        <p style="color: #d4af37; font-weight: bold; font-size: 14px; margin-bottom: 0.5rem;">💡 Dica — Use as notas como referência de preço:</p>
        <p style="color: #cccccc; font-size: 13px; line-height: 1.8; margin: 0;">
            As notas permitem encontrar <b>materiais e serviços de mesma natureza</b> adquiridos por outros órgãos. Os valores podem servir como
            <b>referência de preço</b> para fundamentar sua pesquisa de preços, conforme previsto na legislação de licitações.
            Baixe o DANFE ou XML para ter o documento comprobatório completo.
        </p>
    </div>
    """, unsafe_allow_html=True)
