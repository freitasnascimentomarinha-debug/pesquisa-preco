import streamlit as st
import requests
import pandas as pd
import os
import re
import io
import tempfile
from datetime import datetime

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
    </style>
""", unsafe_allow_html=True)

# ===== SIDEBAR - Navegação customizada =====
with st.sidebar:
    st.markdown("## MENU")
    st.markdown("---")
    st.page_link("streamlit_app.py", label="⚓ Cotação", icon="📊")
    st.page_link("pages/Adesões.py", label="🤝 Adesões", icon="📋")
    st.page_link("pages/Notas_Fiscais.py", label="📄 Notas Fiscais", icon="🧾")
    st.markdown("---")
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header-container">
        <div class="logo-text">SISTEMA DE ACOMPANHAMENTO</div>
        <div class="sistema-nome">AtaCotada</div>
        <div class="subtitulo">Notas Fiscais</div>
    </div>
""", unsafe_allow_html=True)

# ===== CONTEÚDO - NOTAS FISCAIS =====
st.title("📄 Notas Fiscais")
st.markdown("Consulta de notas fiscais eletrônicas a partir dos dados abertos do **Portal da Transparência**.")

# --- Configuração da fonte de dados ---
PASTA_ID = "1369rEJAqpprCP3dZp55eXaTcQRU9D5Ol"
DOWNLOAD_BASE = "https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
CACHE_DIR = os.path.join(tempfile.gettempdir(), "atacotada_nf")
os.makedirs(CACHE_DIR, exist_ok=True)

# Fallback caso a listagem falhe
ARQUIVOS_FALLBACK = {
    "1HwHmY16I7OXmhdRqhaBbLY_tuyLe3plx": "Notas Fiscais - Arquivo 1",
    "1j1y5PgaxbgRWbPkwymRBYE6kNNDSJeM6": "Notas Fiscais - Arquivo 2",
    "1tSqz-nIiM_uDZW38GdWeRboNC7nwq3jH": "Notas Fiscais - Arquivo 3",
    "1tgekwOo8__NZZSs2OdFMS6xT6pS3LXVn": "Notas Fiscais - Arquivo 4",
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

        # Tentar obter nomes dos arquivos via Content-Disposition
        arquivos = {}
        for fid in ids_encontrados:
            try:
                dl_url = DOWNLOAD_BASE.format(file_id=fid)
                head_resp = requests.head(dl_url, allow_redirects=True, timeout=15)
                cd = head_resp.headers.get("Content-Disposition", "")
                match = re.search(r"filename\*?=[\"']?(?:UTF-8'')?([^\"';\r\n]+)", cd)
                if match:
                    nome = requests.utils.unquote(match.group(1)).strip()
                else:
                    nome = f"Arquivo {fid[:10]}"
                arquivos[fid] = nome
            except Exception:
                arquivos[fid] = f"Arquivo {fid[:10]}"

        return arquivos if arquivos else None
    except Exception:
        return None


def baixar_arquivo_csv(file_id, progress_bar=None):
    """Baixa o arquivo CSV para cache local."""
    cache_path = os.path.join(CACHE_DIR, f"{file_id}.csv")

    if os.path.exists(cache_path):
        return cache_path

    url = DOWNLOAD_BASE.format(file_id=file_id)
    response = requests.get(url, stream=True, timeout=600)
    response.raise_for_status()

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

    os.rename(tmp_path, cache_path)
    return cache_path


@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_notas(file_path, filtro_produto="", filtro_nome_dest="", filtro_uf_dest="", filtro_uf_emit="", max_resultados=1000):
    """Pesquisa nos dados CSV filtrando por produto, nome destinatário, UF destinatário e UF emitente."""
    resultados = []
    total_linhas = 0

    for chunk in pd.read_csv(
        file_path,
        sep=";",
        encoding="latin-1",
        chunksize=50000,
        dtype=str,
        on_bad_lines="skip",
    ):
        mask = pd.Series(True, index=chunk.index)

        if filtro_produto and filtro_produto.strip():
            col_prod = "DESCRIÇÃO DO PRODUTO/SERVIÇO"
            if col_prod in chunk.columns:
                mask &= chunk[col_prod].astype(str).str.contains(
                    filtro_produto.strip(), case=False, na=False
                )

        if filtro_nome_dest and filtro_nome_dest.strip():
            col_nome = "NOME DESTINATÁRIO"
            if col_nome in chunk.columns:
                mask &= chunk[col_nome].astype(str).str.contains(
                    filtro_nome_dest.strip(), case=False, na=False
                )

        if filtro_uf_dest and filtro_uf_dest.strip():
            col_uf_dest = "UF DESTINATÁRIO"
            if col_uf_dest in chunk.columns:
                mask &= chunk[col_uf_dest].astype(str).str.upper().eq(
                    filtro_uf_dest.strip().upper()
                )

        if filtro_uf_emit and filtro_uf_emit.strip():
            col_uf_emit = "UF EMITENTE"
            if col_uf_emit in chunk.columns:
                mask &= chunk[col_uf_emit].astype(str).str.upper().eq(
                    filtro_uf_emit.strip().upper()
                )

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


# --- Funções de consulta de fornecedores via API OpenCNPJ ---
def buscar_dados_fornecedor(cnpj):
    """Busca dados do fornecedor na API OpenCNPJ"""
    if not cnpj or pd.isna(cnpj):
        return None
    try:
        cnpj_limpo = str(cnpj).replace('.', '').replace('/', '').replace('-', '').strip()
        if len(cnpj_limpo) != 14:
            return None
        api_url = f'https://api.opencnpj.org/{cnpj_limpo}'
        response = requests.get(api_url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def formatar_telefone(telefone):
    """Formata telefone para um padrão legível"""
    if isinstance(telefone, dict):
        ddd = telefone.get('ddd', '').strip() if telefone.get('ddd') else ''
        numero = telefone.get('numero', '').strip() if telefone.get('numero') else ''
        if ddd and numero:
            numero_fmt = f"{numero[:4]}-{numero[4:]}" if len(numero) >= 8 else numero
            return f"({ddd}) {numero_fmt}"
        return numero or ddd or str(telefone)
    return str(telefone).strip()


def extrair_contatos_fornecedor(dados):
    """Extrai email, telefones, estado e cidade do retorno da API"""
    if not dados:
        return None
    try:
        email = ''
        for c in ['email', 'correio_eletronico', 'mail', 'e_mail', 'emailComercial']:
            email = dados.get(c, '')
            if email:
                break

        estado = ''
        for c in ['state', 'estado', 'uf', 'UF', 'state_code', 'sigla_estado']:
            v = dados.get(c, '')
            if v:
                estado = str(v).upper().strip()
                break

        cidade = ''
        for c in ['city', 'cidade', 'municipio', 'municipality', 'city_name']:
            v = dados.get(c, '')
            if v:
                cidade = str(v).strip()
                break

        telefones = []
        for c in ['phone', 'telefone', 'phonePrimary', 'phoneSecondary',
                   'telefone_comercial', 'telefone_principal', 'ddd_telefone',
                   'ddd_fax', 'fone', 'telephone']:
            v = dados.get(c, '')
            if v:
                t = formatar_telefone(v)
                if t and t not in telefones:
                    telefones.append(t)
        for c in ['phones', 'telefones', 'phone_numbers']:
            vals = dados.get(c, [])
            if isinstance(vals, list):
                for v in vals:
                    if v:
                        t = formatar_telefone(v)
                        if t and t not in telefones:
                            telefones.append(t)

        loc = f"{cidade}, {estado}" if cidade and estado else cidade or estado or ''

        return {
            'email': email or 'Não informado',
            'telefones': ', '.join(telefones) if telefones else 'Não informado',
            'localizacao': loc or 'Não informado',
        }
    except Exception:
        return None


def gerar_html_fornecedores_nf(df_resultado):
    """Gera relatório HTML com dados dos fornecedores (CNPJs) encontrados nas notas fiscais."""
    col_cnpj = "CPF/CNPJ Emitente"
    col_razao = "RAZÃO SOCIAL EMITENTE"
    col_uf = "UF EMITENTE"
    col_mun = "MUNICÍPIO EMITENTE"

    # Obter CNPJs únicos
    if col_cnpj not in df_resultado.columns:
        return "<h3 style='color:red;'>Coluna CNPJ Emitente não encontrada.</h3>"

    fornecedores_unicos = df_resultado.drop_duplicates(subset=[col_cnpj])

    css = """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%); font-family: Arial, sans-serif; padding: 2rem; min-height: 100vh; }
    .container { max-width: 1200px; margin: 0 auto; background: #fff; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); overflow: hidden; }
    .header { background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%); color: #fff; padding: 2rem; text-align: center; }
    .header h1 { color: #d4af37; font-size: 36px; margin-bottom: 0.5rem; letter-spacing: 2px; }
    .header p { font-size: 14px; color: #fff; }
    .content { padding: 2rem; }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .stat-box { background: linear-gradient(135deg, #0a2540 0%, #164863 100%); padding: 1.5rem; border-radius: 8px; border-left: 5px solid #d4af37; text-align: center; }
    .stat-box label { color: #d4af37; font-weight: bold; font-size: 12px; letter-spacing: 1px; }
    .stat-box .value { color: #fff; font-size: 28px; font-weight: bold; margin-top: 0.5rem; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    thead { background: #001a4d; color: #fff; }
    th { padding: 1rem; text-align: left; font-weight: bold; border-bottom: 2px solid #d4af37; color: #fff; }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid #e0e0e0; color: #333; }
    tbody tr:hover { background: #f5f5f5; }
    tbody tr:nth-child(even) { background: #f9f9f9; }
    .email { color: #0033cc; text-decoration: none; }
    .email:hover { text-decoration: underline; }
    .phone { color: #006600; }
    .footer { background: #f0f0f0; padding: 1rem 2rem; text-align: center; color: #666; font-size: 12px; border-top: 1px solid #ddd; }
    """

    linhas = []
    com_email = 0
    com_telefone = 0

    for _, row in fornecedores_unicos.iterrows():
        cnpj = row.get(col_cnpj, '')
        razao = row.get(col_razao, '') if col_razao in fornecedores_unicos.columns else ''
        uf_csv = row.get(col_uf, '') if col_uf in fornecedores_unicos.columns else ''
        mun_csv = row.get(col_mun, '') if col_mun in fornecedores_unicos.columns else ''

        dados_api = buscar_dados_fornecedor(cnpj)
        contatos = extrair_contatos_fornecedor(dados_api)

        if contatos:
            email = contatos['email']
            telefones = contatos['telefones']
            localizacao = contatos['localizacao']
            if email != 'Não informado':
                com_email += 1
            if telefones != 'Não informado':
                com_telefone += 1
        else:
            email = 'Não informado'
            telefones = 'Não informado'
            loc_parts = [p for p in [mun_csv, uf_csv] if p]
            localizacao = ', '.join(loc_parts) if loc_parts else 'Não informado'

        email_html = f'<a href="mailto:{email}" class="email">{email}</a>' if email != 'Não informado' else 'Não informado'

        linhas.append(
            f"<tr><td>{cnpj}</td><td>{razao}</td><td>{localizacao}</td>"
            f"<td>{email_html}</td><td><span class='phone'>{telefones}</span></td></tr>"
        )

    data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contatos de Fornecedores - Notas Fiscais - AtaCotada</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AtaCotada</h1>
            <p>Contatos de Fornecedores — Notas Fiscais</p>
        </div>
        <div class="content">
            <div class="stats">
                <div class="stat-box">
                    <label>TOTAL DE FORNECEDORES</label>
                    <div class="value">{len(fornecedores_unicos)}</div>
                </div>
                <div class="stat-box">
                    <label>COM EMAIL</label>
                    <div class="value">{com_email}</div>
                </div>
                <div class="stat-box">
                    <label>COM TELEFONE</label>
                    <div class="value">{com_telefone}</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>CNPJ</th>
                        <th>Razão Social</th>
                        <th>Localização</th>
                        <th>Email</th>
                        <th>Telefones</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(linhas)}
                </tbody>
            </table>
        </div>
        <div class="footer">
            <p>Relatório gerado por AtaCotada em {data_hora}</p>
        </div>
    </div>
</body>
</html>"""


# --- Carregar lista de arquivos ---
with st.spinner("Carregando lista de arquivos do Portal da Transparência..."):
    arquivos_portal = listar_arquivos_disponiveis(PASTA_ID)

if not arquivos_portal:
    arquivos_portal = ARQUIVOS_FALLBACK.copy()
    st.warning("⚠️ Não foi possível listar os arquivos. Usando dados conhecidos como fallback.")

col_info, col_refresh = st.columns([4, 1])
with col_info:
    st.markdown(f"**{len(arquivos_portal)}** arquivo(s) disponível(is) no Portal da Transparência.")
with col_refresh:
    if st.button("🔄 Atualizar lista", use_container_width=True):
        listar_arquivos_disponiveis.clear()
        st.rerun()

# --- Formulário de busca ---
st.markdown('<div class="filtros-container">', unsafe_allow_html=True)
st.subheader("🔍 Filtros de Pesquisa")

nomes_arquivos = list(arquivos_portal.values())
ids_arquivos = list(arquivos_portal.keys())

arquivo_idx = st.selectbox(
    "📂 Arquivo / Período",
    options=range(len(nomes_arquivos)),
    format_func=lambda i: nomes_arquivos[i],
    help="Selecione o arquivo CSV a ser consultado",
)

col1, col2 = st.columns(2)

with col1:
    filtro_produto = st.text_input(
        "Descrição do Produto / Serviço",
        placeholder="Ex: TINTA, PARAFUSO, DIESEL...",
        help="Pesquisa parcial na descrição do produto/serviço",
    )

with col2:
    filtro_nome_dest = st.text_input(
        "Nome Destinatário",
        placeholder="Ex: ARSENAL, HOSPITAL NAVAL...",
        help="Pesquisa parcial no nome do destinatário",
    )

col3, col4, col5 = st.columns(3)

with col3:
    filtro_uf_dest = st.text_input(
        "UF Destinatário",
        placeholder="Ex: RJ, SP, DF...",
        help="Sigla do estado do destinatário (filtro exato)",
        max_chars=2,
    )

with col4:
    filtro_uf_emit = st.text_input(
        "UF Emitente",
        placeholder="Ex: RJ, SP, MG...",
        help="Sigla do estado do emitente/fornecedor (filtro exato)",
        max_chars=2,
    )

with col5:
    max_resultados = st.number_input(
        "Máximo de resultados",
        min_value=100,
        max_value=10000,
        value=500,
        step=100,
        help="Limita a quantidade de registros retornados para otimizar a performance",
    )

buscar = st.button("🔎 Pesquisar Notas Fiscais", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Processar busca ---
if buscar:
    if not filtro_produto and not filtro_nome_dest and not filtro_uf_dest and not filtro_uf_emit:
        st.warning("⚠️ Informe pelo menos um filtro para realizar a pesquisa.")
    else:
        file_id = ids_arquivos[arquivo_idx]
        file_name = nomes_arquivos[arquivo_idx]

        # Etapa 1: Download do arquivo
        progress_bar = st.progress(0, text="Verificando arquivo...")
        cache_path = os.path.join(CACHE_DIR, f"{file_id}.csv")

        if os.path.exists(cache_path):
            progress_bar.progress(1.0, text="✅ Arquivo já em cache local")
        else:
            try:
                cache_path = baixar_arquivo_csv(file_id, progress_bar)
            except Exception as e:
                progress_bar.empty()
                st.error(f"❌ Erro ao baixar o arquivo: {str(e)}")
                st.stop()

        # Etapa 2: Pesquisa nos dados
        progress_bar.progress(1.0, text="🔍 Pesquisando nos dados...")

        try:
            df_resultado, total_linhas = pesquisar_notas(
                cache_path, filtro_produto, filtro_nome_dest, filtro_uf_dest, filtro_uf_emit, max_resultados
            )
        except Exception as e:
            progress_bar.empty()
            st.error(f"❌ Erro ao processar o arquivo: {str(e)}")
            st.stop()

        progress_bar.empty()

        if df_resultado.empty:
            st.info("📭 Nenhuma nota fiscal encontrada para os filtros informados.")
        else:
            # Salvar resultados no session_state para persistir entre interações
            st.session_state["nf_resultado"] = df_resultado
            st.session_state["nf_total_linhas"] = total_linhas
            st.session_state["nf_file_name"] = file_name
            st.session_state["nf_max_resultados"] = max_resultados

# --- Exibir resultados (persistidos no session_state) ---
if "nf_resultado" in st.session_state and not st.session_state["nf_resultado"].empty:
    df_resultado = st.session_state["nf_resultado"]
    total_linhas = st.session_state["nf_total_linhas"]
    file_name = st.session_state["nf_file_name"]
    max_resultados = st.session_state["nf_max_resultados"]

    # Colunas e ordem definidas pelo usuário
    colunas_exibicao = {
        "DATA EMISSÃO": "Data",
        "DESCRIÇÃO DO PRODUTO/SERVIÇO": "Produto",
        "UNIDADE": "Unidade",
        "QUANTIDADE": "Quantidade",
        "VALOR UNITÁRIO": "Valor Unitário",
        "VALOR TOTAL": "Valor Total",
        "UF DESTINATÁRIO": "UF Destinatário",
        "NOME DESTINATÁRIO": "Nome Destinatário",
        "RAZÃO SOCIAL EMITENTE": "Razão Social Emitente",
        "CPF/CNPJ Emitente": "CNPJ Emitente",
        "UF EMITENTE": "UF Emitente",
        "MUNICÍPIO EMITENTE": "Município",
        "NCM/SH (TIPO DE PRODUTO)": "NCM/SH (Tipo de Produto)",
        "CHAVE DE ACESSO": "Chave de Acesso",
        "NATUREZA DA OPERAÇÃO": "Natureza da Operação",
    }
    colunas_disponiveis = [c for c in colunas_exibicao if c in df_resultado.columns]
    df_exib = df_resultado[colunas_disponiveis].rename(columns=colunas_exibicao).copy()

    # --- Cards de estatísticas ---
    st.markdown("---")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        st.markdown(f"""
        <div class="stats-card">
            <div style="color: #d4af37; font-size: 14px; font-weight: 600;">REGISTROS ENCONTRADOS</div>
            <div style="color: #ffffff; font-size: 32px; font-weight: bold;">{len(df_resultado):,}</div>
            <div style="color: #aaaaaa; font-size: 12px;">{total_linhas:,} linhas analisadas</div>
        </div>
        """, unsafe_allow_html=True)

    with col_s2:
        fornecedores = (
            df_resultado["RAZÃO SOCIAL EMITENTE"].nunique()
            if "RAZÃO SOCIAL EMITENTE" in df_resultado.columns
            else 0
        )
        st.markdown(f"""
        <div class="stats-card">
            <div style="color: #d4af37; font-size: 14px; font-weight: 600;">FORNECEDORES</div>
            <div style="color: #ffffff; font-size: 32px; font-weight: bold;">{fornecedores}</div>
            <div style="color: #aaaaaa; font-size: 12px;">Distintos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_s3:
        orgaos = (
            df_resultado["ÓRGÃO DESTINATÁRIO"].nunique()
            if "ÓRGÃO DESTINATÁRIO" in df_resultado.columns
            else 0
        )
        st.markdown(f"""
        <div class="stats-card">
            <div style="color: #d4af37; font-size: 14px; font-weight: 600;">ÓRGÃOS DESTINO</div>
            <div style="color: #ffffff; font-size: 32px; font-weight: bold;">{orgaos}</div>
            <div style="color: #aaaaaa; font-size: 12px;">Distintos</div>
        </div>
        """, unsafe_allow_html=True)

    with col_s4:
        try:
            total_valor = pd.to_numeric(
                df_resultado["VALOR TOTAL"]
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False),
                errors="coerce",
            ).sum()
            valor_fmt = (
                f"R$ {total_valor:,.2f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except Exception:
            valor_fmt = "—"
        st.markdown(f"""
        <div class="stats-card">
            <div style="color: #d4af37; font-size: 14px; font-weight: 600;">VALOR TOTAL</div>
            <div style="color: #ffffff; font-size: 20px; font-weight: bold;">{valor_fmt}</div>
            <div style="color: #aaaaaa; font-size: 12px;">Soma dos registros</div>
        </div>
        """, unsafe_allow_html=True)

    # --- Tabela de resultados ---
    st.markdown("---")
    st.subheader("📋 Resultados")
    st.markdown(f"**Arquivo:** {file_name}")
    st.dataframe(
        df_exib,
        use_container_width=True,
        hide_index=True,
        height=min(len(df_exib) * 38 + 40, 700),
    )

    # --- Botões de download ---
    st.markdown("---")
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        csv_data = df_exib.to_csv(index=False, sep=";", encoding="utf-8-sig")
        st.download_button(
            "📥 Baixar resultados (CSV)",
            data=csv_data,
            file_name="notas_fiscais_resultado.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d2:
        try:
            excel_buffer = io.BytesIO()
            df_exib.to_excel(excel_buffer, index=False, engine="openpyxl")
            st.download_button(
                "📥 Baixar resultados (Excel)",
                data=excel_buffer.getvalue(),
                file_name="notas_fiscais_resultado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception:
            pass

    # --- Botão Consultar Fornecedores ---
    st.markdown("<br>", unsafe_allow_html=True)
    col_forn_btn, _ = st.columns([1, 2])
    with col_forn_btn:
        if st.button("📞 Consultar Fornecedores", use_container_width=True, key="btn_fornecedores_nf"):
            cnpjs_unicos = df_resultado["CPF/CNPJ Emitente"].dropna().unique() if "CPF/CNPJ Emitente" in df_resultado.columns else []
            if len(cnpjs_unicos) == 0:
                st.warning("⚠️ Nenhum CNPJ encontrado nos resultados filtrados.")
            else:
                with st.spinner(f"Consultando dados de {len(cnpjs_unicos)} fornecedor(es) na API..."):
                    html_fornecedores = gerar_html_fornecedores_nf(df_resultado)
                    st.session_state["nf_html_fornecedores"] = html_fornecedores

    # Mostrar botão de download do relatório se já foi gerado
    if "nf_html_fornecedores" in st.session_state:
        col_dl_forn, _ = st.columns([1, 2])
        with col_dl_forn:
            data_hora_arq = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📋 Baixar Relatório de Fornecedores (HTML)",
                data=st.session_state["nf_html_fornecedores"].encode('utf-8'),
                file_name=f"fornecedores_NF_{data_hora_arq}.html",
                mime="text/html",
                use_container_width=True,
                key="btn_download_fornecedores_nf",
            )

    # --- Informações ---
    st.markdown("---")
    st.markdown(f"""
    <div style="background: #0a2540; border: 1px solid #333; border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
        <p style="color: #d4af37; font-weight: bold; margin-bottom: 0.5rem;">ℹ️ Informações:</p>
        <ul style="color: #cccccc; font-size: 13px; line-height: 1.8;">
            <li>Dados extraídos do <b>Portal da Transparência</b> — Notas Fiscais Eletrônicas.</li>
            <li>Na primeira consulta, os dados são carregados e armazenados em <b>cache local</b> (pode levar alguns minutos para arquivos grandes).</li>
            <li>Consultas subsequentes no mesmo arquivo são <b>muito mais rápidas</b>.</li>
            <li>Limite de <b>{max_resultados}</b> resultados para otimizar a performance.</li>
            <li>Os resultados podem ser exportados em <b>CSV</b> ou <b>Excel</b>.</li>
        </ul>
        <p style="color: #d4af37; text-align: center; margin-top: 1rem; font-size: 14px; font-weight: 600;">
            Notas Fiscais podem ser usadas na pesquisa de preço, acesse para baixar com a chave de acesso:
            <a href="https://www.nfe.fazenda.gov.br/portal/principal.aspx" target="_blank" style="color: #ffd700; text-decoration: underline;">https://www.nfe.fazenda.gov.br/portal/principal.aspx</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
