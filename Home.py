import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="AtaCotada - Home",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
        body, .main {
            background-color: #001a4d;
            color: #ffffff;
        }
        
        .stApp {
            background-color: #001a4d;
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
        
        /* SIDEBAR - NAVEGAÇÃO DE PÁGINAS MODERNO */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
            border-right: 2px solid #d4af37;
        }
        
        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            background: transparent;
        }
        
        /* Botões de navegação das páginas */
        [data-testid="stSidebar"] button {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            color: #ffffff !important;
            border: 2px solid #333333 !important;
            border-radius: 8px;
            margin: 0.5rem 0;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            padding: 0.75rem 1rem !important;
        }
        
        [data-testid="stSidebar"] button:hover {
            background: linear-gradient(135deg, #2d2d2d 0%, #3d3d3d 100%);
            border: 2px solid #d4af37 !important;
            color: #d4af37 !important;
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
        }
        
        /* Botão ativo */
        [data-testid="stSidebar"] button[kind="primary"] {
            background: linear-gradient(135deg, #d4af37 0%, #ffd700 100%);
            color: #001a4d !important;
            border: 2px solid #d4af37 !important;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
        }
        
        /* Links na sidebar */
        [data-testid="stSidebar"] a {
            color: #ffffff !important;
            text-decoration: none;
            transition: all 0.3s ease;
        }
        
        [data-testid="stSidebarNav"] span {
            color: #ffffff !important;
        }
        
        [data-testid="stSidebar"] a:hover,
        [data-testid="stSidebarNav"] a:hover span {
            color: #d4af37 !important;
            text-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
        }
        
        /* Texto e labels na sidebar */
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stText,
        [data-testid="stSidebar"] div {
            color: #ffffff !important;
        }
        
        /* Separadores na sidebar */
        [data-testid="stSidebar"] hr {
            border-color: #333333;
            margin: 1rem 0;
        }
        
        /* Cabeçalho da sidebar */
        [data-testid="stSidebar"] .stMarkdown h1,
        [data-testid="stSidebar"] .stMarkdown h2,
        [data-testid="stSidebar"] .stMarkdown h3 {
            color: #d4af37;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
            border-bottom: 2px solid #d4af37;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
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
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-container">
    <div class="logo-text">SISTEMA DE PESQUISA DE PREÇOS</div>
    <div class="sistema-nome">AtaCotada</div>
    <div class="subtitulo">Marinha do Brasil</div>
</div>
""", unsafe_allow_html=True)

# Conteúdo Principal
st.markdown("""
## Bem-vindo ao AtaCotada

O **AtaCotada** é uma solução completa para gestão e acompanhamento de processos de licitação, cotações e adesões.

### Funcionalidades:
- **⚓ Cotação:** Realize pesquisas de preços e cotações de forma automatizada.
- **📄 Notas Fiscais:** Acompanhe e gerencie notas fiscais emitidas.
- **🤝 Adesões:** Gerencie processos de adesão a atas de registro de preços.

---
Selecione uma opção no menu lateral para começar.
""")
