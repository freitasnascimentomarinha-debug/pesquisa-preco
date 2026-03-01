import streamlit as st
import requests
import pandas as pd
import json
import os
import base64

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
        
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            margin-bottom: 0.5rem !important;
            padding: 0.7rem 1rem !important;
            transition: all 0.3s ease !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
            background: rgba(212, 175, 55, 0.1) !important;
            border-color: #d4af37 !important;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25) !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover span { color: #d4af37 !important; }
        
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
            color: #0a0a0a !important;
            border: 1px solid #d4af37 !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4) !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span { color: #0a0a0a !important; }
        
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
        
    </style>
""", unsafe_allow_html=True)

def formatar_moeda_br(valor):
    try:
        val = float(valor)
        return f'R$ {val:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return "R$ 0,00"

def formatar_cnpj(cnpj):
    cnpj = str(cnpj).zfill(14)
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

# Funções de API
@st.cache_data(ttl=3600)
def consultar_opencnpj(cnpj_limpo):
    try:
        url = f"https://api.opencnpj.org/{cnpj_limpo}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        return None
    return None

@st.cache_data(ttl=3600)
def consultar_comprasgov(cnpj_limpo, data_inicial, data_final):
    try:
        url = f"http://compras.dados.gov.br/contratos/v1/contratos.json?cnpj_contratada={cnpj_limpo}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            dados = resp.json()
            if isinstance(dados, dict) and 'resultado' in dados:
                return dados['resultado']
            elif isinstance(dados, dict) and '_embedded' in dados:
                # ComprasNet Legacy API format
                return dados['_embedded'].get('contratos', [])
            return dados if isinstance(dados, list) else []
    except Exception as e:
        return []
    return []

# Remover cache_data do Portal da Transparencia pois não pode ser consultado de forma global agnóstica sem Unidade

# Sidebar Navigation
with st.sidebar:
    st.markdown('<div class="logo-text">MARINHA DO BRASIL</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("streamlit_app.py", label="⚓ Cotação", icon="📊")
    st.page_link("pages/Adesões.py", label="🤝 Adesões", icon="📋")
    st.page_link("pages/Notas_Fiscais.py", label="📄 Notas Fiscais", icon="🧾")
    st.page_link("pages/Banco_de_Fornecedores.py", label="🏢 Fornecedores", icon="🔍")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.markdown("---")
    st.markdown('<div class="sidebar-footer">AtaCotada v1.0</div>', unsafe_allow_html=True)

# Main Header
st.markdown("""
<div class="header-container">
    <div class="logo-text">MARINHA DO BRASIL</div>
    <div class="sistema-nome">AtaCotada</div>
    <div class="subtitulo">Consulta detalhada de Fornecedores e Contratos</div>
</div>
""", unsafe_allow_html=True)

st.title("Consulta de Fornecedor por CNPJ")
st.markdown("Busque por informações de contato atualizadas e verifique o histórico de contratos com o Governo Federal.")

with st.container():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        cnpj_input = st.text_input("Digite o CNPJ (somente números ou com pontuação):", placeholder="Ex: 00.000.000/0001-00")
    with col2:
        anos_janela = st.number_input("Janela de Pesquisa (Anos de histórico):", min_value=1, max_value=10, value=3)
        
        # Calcular datas baseadas na janela
        import datetime
        hoje = datetime.date.today()
        data_ini = (hoje - datetime.timedelta(days=365 * anos_janela)).strftime("%Y-%m-%d")
        data_fim = hoje.strftime("%Y-%m-%d")
        
    with col3:
        st.write("")
        st.write("")
        btn_consultar = st.button("Consultar", use_container_width=True, type="primary")

if btn_consultar and cnpj_input:
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj_input))
    if len(cnpj_limpo) != 14:
        st.error("CNPJ inválido. Certifique-se de preencher 14 dígitos inteiros.")
    else:
        with st.spinner(f"Consultando bases de dados para o CNPJ {formatar_cnpj(cnpj_limpo)} (Isso pode levar até 30s)..."):
            dados_empresa = consultar_opencnpj(cnpj_limpo)
            contratos_cg = consultar_comprasgov(cnpj_limpo, data_ini, data_fim)

        st.markdown("---")

        # Dados da Empresa (OpenCNPJ)
        if dados_empresa:
            st.markdown(f"### Informações da Empresa: {dados_empresa.get('nome_fantasia') or dados_empresa.get('razao_social')}")
            
            # Formatar telefones (se houver)
            telefones_lista = dados_empresa.get('telefones', [])
            tel_formatado = "N/A"
            if telefones_lista:
                tel_formatado = f"({telefones_lista[0].get('ddd', '')}) {telefones_lista[0].get('numero', '')}"

            e_col1, e_col2 = st.columns(2)
            with e_col1:
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-title">Identificação</div>
                    <div class="info-item"><span class="info-label">Razão Social:</span> <span class="info-value">{dados_empresa.get('razao_social', 'N/A')}</span></div>
                    <div class="info-item"><span class="info-label">Nome Fantasia:</span> <span class="info-value">{dados_empresa.get('nome_fantasia', 'N/A')}</span></div>
                    <div class="info-item"><span class="info-label">CNPJ:</span> <span class="info-value">{formatar_cnpj(cnpj_limpo)}</span></div>
                    <div class="info-item"><span class="info-label">Situação:</span> <span class="info-value">{dados_empresa.get('situacao', 'N/A')}</span></div>
                </div>
                """, unsafe_allow_html=True)
            with e_col2:
                ender = f"{dados_empresa.get('logradouro', '')}, {dados_empresa.get('numero', '')} - {dados_empresa.get('municipio', '')}/{dados_empresa.get('uf', '')}"
                st.markdown(f"""
                <div class="info-card">
                    <div class="info-title">Contato e Endereço</div>
                    <div class="info-item"><span class="info-label">Email:</span> <span class="info-value">{dados_empresa.get('email', 'N/A')}</span></div>
                    <div class="info-item"><span class="info-label">Telefone:</span> <span class="info-value">{tel_formatado}</span></div>
                    <div class="info-item"><span class="info-label">Endereço:</span> <span class="info-value">{ender}</span></div>
                    <div class="info-item"><span class="info-label">CEP:</span> <span class="info-value">{dados_empresa.get('cep', 'N/A')}</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Não foi possível carregar os dados cadastrais desta empresa (OpenCNPJ).")

        st.markdown("---")
        st.markdown("### Histórico de Contratos Governamentais")
        
        st.write("##### Fonte: Dados Abertos Compras.gov.br")
        if contratos_cg and len(contratos_cg) > 0:
            # Filtrar manual por data se a API retornou sem filtrar (caso da API legada)
            contratos_filtrados = []
            for c in contratos_cg:
                data_ass = c.get('data_assinatura') or c.get('data_inicio_vigencia')
                if data_ass and data_ass >= data_ini and data_ass <= data_fim:
                    contratos_filtrados.append(c)
                elif not data_ass:
                    contratos_filtrados.append(c)
            
            # Se for a API legada, o array pode não ter sido filtrado pela data no servidor.
            # No entanto, se usamos os parametros na URL (como no legacy), a URL ignorou se nao suporta.
            
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

