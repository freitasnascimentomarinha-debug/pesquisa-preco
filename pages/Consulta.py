import streamlit as st
import pandas as pd
import os
import base64
import datetime
from html import escape

from servicos_publicos import (
    baixar_csv_drive, cnpj_valido, consultar_cadastro_cnpj, formatar_cnpj, itens_arp_por_fornecedor, limpar_cnpj,
    listar_arquivos_drive, pesquisar_notas_por_cnpj, pncp_search, resumo_notas, separar_vigentes,
)

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
    except (TypeError, ValueError):
        return "R$ 0,00"


def esc(valor, padrao="N/A"):
    """Texto vindo de API escapado para uso dentro de HTML."""
    return escape(str(valor)) if valor not in (None, "") else padrao


@st.cache_data(show_spinner=False, ttl=600)
def listar_arquivos_disponiveis(folder_id):
    """Descobre os arquivos CSV disponíveis na pasta do Google Drive (None se não conseguir listar)."""
    return listar_arquivos_drive(folder_id)


@st.cache_data(show_spinner=False, ttl=1800)
def pesquisar_notas(caminho, cnpj_busca):
    return pesquisar_notas_por_cnpj(caminho, cnpj_busca)


def card_pncp(emoji, c, rodape_rotulo, rodape_valor, valor):
    """Card HTML de um registro do PNCP (contrato, ata, compra ou dispensa) com os campos escapados."""
    url_pncp = c.get('item_url', '')
    link = (f'<div style="margin-top:0.5rem;"><a href="{escape("https://pncp.gov.br/app" + url_pncp, quote=True)}" '
            f'target="_blank" style="color:#4da6ff;">🔗 Ver no PNCP</a></div>') if url_pncp else ''
    st.markdown(f"""
    <div class="contract-card">
        <div class="contract-title">{emoji} {esc(c.get('title'))} — {esc(c.get('orgao_nome'))}</div>
        <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Unidade:</strong> {esc(c.get('unidade_nome'), '')} ({esc(c.get('municipio_nome'), '')}/{esc(c.get('uf'), '')})</div>
        <div style="margin-bottom:0.3rem; color:#cbd5e1;"><strong>Modalidade:</strong> {esc(c.get('modalidade_licitacao_nome'))} | <strong>Situação:</strong> {esc(c.get('situacao_nome'))}</div>
        <div style="margin-bottom:0.5rem; color:#cbd5e1;"><strong>Objeto:</strong> {esc(str(c.get('description') or 'N/A')[:200])}</div>
        <div style="display:flex; justify-content:space-between; flex-wrap:wrap; color:#cbd5e1; font-size:0.9rem;">
            <div><strong>{rodape_rotulo}:</strong> {esc(rodape_valor)}</div>
            <div style="color:#d4af37; font-weight:bold;">Valor: {formatar_moeda_br(valor)}</div>
        </div>
        {link}
    </div>
    """, unsafe_allow_html=True)


# ===================== NOTAS FISCAIS =====================

PASTA_ID = "1369rEJAqpprCP3dZp55eXaTcQRU9D5Ol"

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
    st.page_link("pages/CATMAT_CATSERV_Automatico.py", label="CATMAT/CATSERV", icon="🔎")
    st.page_link("pages/Cotação_Rápida.py", label="Cotação Rápida", icon="⚡")
    st.page_link("pages/Cotação_Direta.py", label="Cotação Direta", icon="📨")
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
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

    with col3:
        st.write("")
        st.write("")
        btn_consultar = st.button("Consultar", use_container_width=True, type="primary")


# ===================== CONSULTA =====================

if btn_consultar and cnpj_input:
    cnpj_limpo = limpar_cnpj(cnpj_input)
    if len(cnpj_limpo) != 14:
        st.error("CNPJ inválido. Certifique-se de preencher 14 dígitos inteiros.")
    elif not cnpj_valido(cnpj_limpo):
        st.error("CNPJ inválido: os dígitos verificadores não conferem. Confira o número digitado.")
    else:
        hoje = datetime.date.today()
        data_min = hoje - datetime.timedelta(days=365 * anos_janela)
        # cada fonte é consultada de forma independente; a falha de uma não esconde as demais
        status_fontes = []

        with st.spinner(f"Consultando bases de dados para o CNPJ {formatar_cnpj(cnpj_limpo)}..."):
            progresso = st.progress(0, text="Consultando dados cadastrais...")
            cadastro = consultar_cadastro_cnpj(cnpj_limpo)
            for fonte, erro in cadastro["erros"].items():
                status_fontes.append(("OpenCNPJ" if fonte == "opencnpj" else "BrasilAPI", erro))

            progresso.progress(0.15, text="Consultando contratos no PNCP...")
            contratos_pncp, erro = pncp_search(cnpj_limpo, "contrato", data_min)
            if erro:
                status_fontes.append(("PNCP — contratos", erro))

            progresso.progress(0.35, text="Consultando compras/licitações no PNCP...")
            compras_pncp, erro = pncp_search(cnpj_limpo, "compra", data_min)
            if erro:
                status_fontes.append(("PNCP — compras", erro))

            progresso.progress(0.55, text="Consultando atas de registro de preços (PNCP)...")
            atas_pncp, erro = pncp_search(cnpj_limpo, "ata", data_min)
            if erro:
                status_fontes.append(("PNCP — atas", erro))

            progresso.progress(0.75, text="Consultando atas e adesões vigentes (Compras.gov.br)...")
            atas_dadosabertos, erro = itens_arp_por_fornecedor(cnpj_limpo, anos_janela)
            if erro:
                status_fontes.append(("Compras.gov.br — ARP", erro))

            # pregões/concorrências → aba Contratos; dispensas e inexigibilidades → aba Dispensas
            def _direta(c):
                return str(c.get('modalidade_licitacao_nome') or '').lower() in ('dispensa', 'inexigibilidade')

            progresso.progress(1.0, text="Consulta concluída!")
            progresso.empty()

        st.session_state['cnpj_consulta'] = cnpj_limpo
        st.session_state['dados_empresa'] = cadastro["opencnpj"]
        st.session_state['dados_brasil_api'] = cadastro["brasilapi"]
        st.session_state['contratos_pncp'] = contratos_pncp
        st.session_state['compras_pregao'] = [c for c in compras_pncp if not _direta(c)]
        st.session_state['compras_dispensa'] = [c for c in compras_pncp if _direta(c)]
        st.session_state['atas_pncp'] = atas_pncp
        st.session_state['atas_dadosabertos'] = atas_dadosabertos
        st.session_state['status_fontes'] = status_fontes
        st.session_state['anos_janela_consulta'] = anos_janela


# ===================== EXIBIÇÃO POR ABAS =====================

if 'cnpj_consulta' in st.session_state:
    cnpj_limpo = st.session_state['cnpj_consulta']
    dados_empresa = st.session_state.get('dados_empresa')
    dados_brasil_api = st.session_state.get('dados_brasil_api')
    contratos_pncp = st.session_state.get('contratos_pncp', [])
    compras_pregao = st.session_state.get('compras_pregao', [])
    compras_dispensa = st.session_state.get('compras_dispensa', [])
    atas_pncp = st.session_state.get('atas_pncp', [])
    atas_dadosabertos = st.session_state.get('atas_dadosabertos', [])
    status_fontes = st.session_state.get('status_fontes', [])
    anos_consulta = st.session_state.get('anos_janela_consulta', 3)

    st.markdown("---")

    if status_fontes:
        st.warning("⚠️ Algumas fontes não responderam e os resultados podem estar incompletos. Tente novamente em alguns minutos.")
        for fonte, erro in status_fontes:
            st.caption(f"• **{fonte}**: {erro}")
    st.caption(f"Período consultado: últimos {anos_consulta} ano(s) (contratos, compras, atas e ARPs).")

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
                    <div class="info-item"><span class="info-label">Razão Social:</span> <span class="info-value">{esc(dados_empresa.get('razao_social'))}</span></div>
                    <div class="info-item"><span class="info-label">Nome Fantasia:</span> <span class="info-value">{esc(dados_empresa.get('nome_fantasia'))}</span></div>
                    <div class="info-item"><span class="info-label">CNPJ:</span> <span class="info-value">{formatar_cnpj(cnpj_limpo)}</span></div>
                    <div class="info-item"><span class="info-label">Situação:</span> <span class="info-value">{esc(situacao)}</span></div>
                    <div class="info-item"><span class="info-label">Capital Social:</span> <span class="info-value">R$ {esc(dados_empresa.get('capital_social'))}</span></div>
                    <div class="info-item"><span class="info-label">Porte:</span> <span class="info-value">{esc(dados_empresa.get('porte_empresa'))}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with e_col2:
                ender = f"{dados_empresa.get('logradouro', '')}, {dados_empresa.get('numero', '')} - {dados_empresa.get('bairro', '')}"
                cidade_uf = f"{dados_empresa.get('municipio', '')}/{dados_empresa.get('uf', '')}"
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-title">Contato e Endereço</div>
                    <div class="info-item"><span class="info-label">📧 Email:</span> <span class="info-value">{esc(email_display)}</span></div>
                    <div class="info-item"><span class="info-label">📞 Telefone:</span> <span class="info-value">{esc(tel_display)}</span></div>
                    <div class="info-item"><span class="info-label">📍 Endereço:</span> <span class="info-value">{esc(ender)}</span></div>
                    <div class="info-item"><span class="info-label">🏙️ Cidade/UF:</span> <span class="info-value">{esc(cidade_uf)}</span></div>
                    <div class="info-item"><span class="info-label">📮 CEP:</span> <span class="info-value">{esc(dados_empresa.get('cep'))}</span></div>
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
            st.warning("Não foi possível carregar os dados cadastrais desta empresa (OpenCNPJ). Veja o aviso de fontes acima, se houver.")

    # ==================== ABA 2: CONTRATOS ====================
    with tab_contratos:
        st.markdown("### Histórico de Contratos e Licitações")
        st.write("##### Fonte: PNCP — Portal Nacional de Contratações Públicas")

        todos_contratos_aba = contratos_pncp + compras_pregao

        if todos_contratos_aba and len(todos_contratos_aba) > 0:
            st.success(f"Encontrados **{len(todos_contratos_aba)}** registros associados a este CNPJ "
                       f"({len(contratos_pncp)} contratos, {len(compras_pregao)} compras/licitações).")

            for c in todos_contratos_aba:
                card_pncp("📄", c, "Vigência", f"{c.get('data_inicio_vigencia') or 'N/A'} a {c.get('data_fim_vigencia') or 'N/A'}", c.get('valor_global', 0))

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
                card_pncp("📑", ata, "Publicação", str(ata.get('data_publicacao_pncp', ''))[:10], ata.get('valor_global') or ata.get('valor_total_estimado', 0))

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
        st.write("##### Fonte: ComprasGov — Itens de ARP onde este CNPJ é fornecedor registrado")

        # Dados vindos de 2_consultarARPItem (niFornecedor)
        todos_itens_arp = atas_dadosabertos or []
        hoje_str = datetime.date.today().strftime("%Y-%m-%d")
        vigentes, encerradas = separar_vigentes(todos_itens_arp)

        if todos_itens_arp:
            st.success(f"Encontrados **{len(todos_itens_arp)}** itens de ARP associados a este CNPJ "
                       f"(**{len(vigentes)}** abertos para adesão, {len(encerradas)} outros).")

            # Agrupar itens por ATA (numeroAtaRegistroPreco + codigoUnidadeGerenciadora)
            def _agrupar_por_ata(itens):
                atas = {}
                for item in itens:
                    chave = f"{item.get('numeroAtaRegistroPreco', '')}|{item.get('codigoUnidadeGerenciadora', '')}"
                    if chave not in atas:
                        atas[chave] = {
                            'numero_ata': item.get('numeroAtaRegistroPreco', 'N/A'),
                            'unidade': item.get('nomeUnidadeGerenciadora', 'N/A'),
                            'modalidade': item.get('nomeModalidadeCompra', 'N/A'),
                            'data_ini': str(item.get('dataVigenciaInicial', ''))[:10],
                            'data_fim': str(item.get('dataVigenciaFinal', ''))[:10],
                            'numero_pncp': item.get('numeroControlePncpAta', ''),
                            'itens': [],
                        }
                    atas[chave]['itens'].append(item)
                return atas

            sub_vigentes, sub_todas = st.tabs(["🟢 Abertos para Adesão", "📋 Todos os Itens"])

            def _render_atas_agrupadas(atas_dict):
                for _chave, ata_info in atas_dict.items():
                    vigencia_fim = ata_info['data_fim']
                    aberta = vigencia_fim >= hoje_str
                    cor = "🟢" if aberta else "🔴"
                    total_itens = len(ata_info['itens'])
                    valor_total = sum(i.get('valorTotal', 0) or 0 for i in ata_info['itens'])
                    header = f"{cor} ARP nº {ata_info['numero_ata']} — {ata_info['unidade']} ({total_itens} itens)"

                    with st.expander(header):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Modalidade", ata_info['modalidade'])
                        col2.metric("Vigência", f"{ata_info['data_ini']} → {ata_info['data_fim']}")
                        col3.metric("Valor Total Itens", formatar_moeda_br(valor_total))

                        if ata_info['numero_pncp']:
                            link_pncp = f"https://pncp.gov.br/app/atas/{ata_info['numero_pncp']}"
                            st.markdown(f"[🔗 Ver ATA no PNCP]({link_pncp})")

                        # Tabela de itens desta ATA
                        df_itens = pd.DataFrame([{
                            'Item': i.get('numeroItem', ''),
                            'Descrição': i.get('descricaoItem', ''),
                            'Tipo': i.get('tipoItem', ''),
                            'Qtd Homologada': i.get('quantidadeHomologadaItem', ''),
                            'Valor Unitário': formatar_moeda_br(i.get('valorUnitario', 0) or 0),
                            'Valor Total': formatar_moeda_br(i.get('valorTotal', 0) or 0),
                            'Máximo Adesão': i.get('maximoAdesao', 0),
                            'Qtd Empenhada': i.get('quantidadeEmpenhada', 0),
                        } for i in ata_info['itens']])
                        st.dataframe(df_itens, use_container_width=True, hide_index=True)

            with sub_vigentes:
                if vigentes:
                    atas_vigentes = _agrupar_por_ata(vigentes)
                    _render_atas_agrupadas(atas_vigentes)
                else:
                    st.info("Nenhum item vigente com adesão aberta encontrado para este CNPJ.")

            with sub_todas:
                atas_todas = _agrupar_por_ata(todos_itens_arp)
                _render_atas_agrupadas(atas_todas)
                # Tabela resumo geral
                with st.expander("📊 Tabela resumo de todos os itens"):
                    df_todos = pd.DataFrame([{
                        'Nº ATA': a.get('numeroAtaRegistroPreco', ''),
                        'Unidade Gerenciadora': a.get('nomeUnidadeGerenciadora', ''),
                        'Item': a.get('numeroItem', ''),
                        'Descrição': str(a.get('descricaoItem', ''))[:80],
                        'Vigência Início': str(a.get('dataVigenciaInicial', ''))[:10],
                        'Vigência Fim': str(a.get('dataVigenciaFinal', ''))[:10],
                        'Valor Total': formatar_moeda_br(a.get('valorTotal', 0) or 0),
                        'Máx. Adesão': a.get('maximoAdesao', 0),
                    } for a in todos_itens_arp])
                    st.dataframe(df_todos, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum item de ARP encontrado no ComprasGov para este CNPJ no período consultado.")

    # ==================== ABA 5: DISPENSAS / CONTRATAÇÃO DIRETA ====================
    with tab_compras:
        st.markdown("### Dispensas / Contratação Direta")
        st.write("##### Fonte: PNCP — Portal Nacional de Contratações Públicas")

        todas_dispensas_aba = compras_dispensa

        if todas_dispensas_aba and len(todas_dispensas_aba) > 0:
            st.success(f"Encontradas **{len(todas_dispensas_aba)}** compras/contratações diretas associadas a este CNPJ.")

            for c in todas_dispensas_aba:
                card_pncp("🛒", c, "Publicação", str(c.get('data_publicacao_pncp', ''))[:10], c.get('valor_global') or c.get('valor_total_estimado', 0))

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
                    caminho = baixar_csv_drive(file_id, progresso=lambda fracao, texto: progress_nf.progress(fracao, text=texto))
                    progress_nf.progress(0.5, text=f"Pesquisando CNPJ em {nome_arquivo}...")

                    df_resultado, total_linhas = pesquisar_notas(caminho, cnpj_limpo)
                    progress_nf.progress(1.0, text=f"Concluído: {nome_arquivo}")
                    progress_nf.empty()

                    if not df_resultado.empty:
                        df_resultado = df_resultado.copy()
                        df_resultado['_arquivo_origem'] = nome_arquivo
                        resultados_nf_total.append(df_resultado)
                        resumo_mes = resumo_notas(df_resultado)
                        st.success(f"✅ {nome_arquivo}: **{resumo_mes['notas']}** nota(s) em {resumo_mes['itens']} linha(s) de item (de {total_linhas:,} registros)")
                    else:
                        st.info(f"📭 {nome_arquivo}: Nenhuma nota encontrada para este CNPJ.")

                except (RuntimeError, OSError, ValueError) as e:
                    progress_nf.empty()
                    st.error(f"❌ Erro ao processar {nome_arquivo}: {e}")
                except Exception as e:  # falha de rede/Drive: mostra o tipo para facilitar o diagnóstico
                    progress_nf.empty()
                    st.error(f"❌ Erro ao baixar/processar {nome_arquivo} ({type(e).__name__}): {e}")

            if resultados_nf_total:
                df_todas_nf = pd.concat(resultados_nf_total, ignore_index=True)
                st.markdown("---")
                resumo = resumo_notas(df_todas_nf)
                st.markdown("---")
                st.markdown(f"### Resultados Consolidados: {resumo['notas']} nota(s) fiscal(is) em {resumo['itens']} linhas de item")

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
                    st.metric("Notas fiscais (distintas)", resumo['notas'], help=f"{resumo['itens']} linhas de item no total.")
                with col_s2:
                    if resumo['valor'] is None:
                        st.metric("Valor total", "N/A")
                    else:
                        st.metric("Valor total", formatar_moeda_br(resumo['valor']),
                                  help="Soma dos itens das notas encontradas." if resumo['base'] == 'itens'
                                  else "Valor da nota contado uma única vez por nota fiscal.")
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
