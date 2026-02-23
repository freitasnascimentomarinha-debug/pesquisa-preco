import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

# Configuração da página
st.set_page_config(
    page_title="AtaCotada - Marinha do Brasil",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para tema azul escuro com dourado
st.markdown("""
    <style>
        :root {
            --azul-escuro: #001a4d;
            --azul-claro: #0033cc;
            --dourado: #d4af37;
            --branco: #ffffff;
            --cinza-claro: #f0f0f0;
        }
        
        * {
            margin: 0;
            padding: 0;
        }
        
        body, .main {
            background-color: #001a4d;
            color: #ffffff;
        }
        
        .stApp {
            background-color: #001a4d;
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
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
            color: #001a4d;
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
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(212, 175, 55, 0.3);
        }
        
        /* Inputs e Selects */
        .stTextInput > div > div > input,
        .stMultiSelect > div > div > div,
        .stSelectbox > div > div > select,
        .stSlider > div > div > div {
            background-color: #0a2540 !important;
            color: #ffffff !important;
            border: 2px solid #0033cc !important;
            border-radius: 6px !important;
        }
        
        /* Labels e textos de input - BRANCO */
        label, .stText, .stLabel, .stMultiSelect label, .stSelectbox label, .stTextInput label {
            color: #ffffff !important;
        }
        
        /* Checkbox labels e texto - MAIS ESPECÍFICO */
        .stCheckbox {
            background-color: transparent;
        }
        
        .stCheckbox > label {
            color: #ffffff !important;
            background-color: transparent;
        }
        
        .stCheckbox > div > label {
            color: #ffffff !important;
        }
        
        .stCheckbox label {
            color: #ffffff !important;
        }
        
        .stCheckbox label span {
            color: #ffffff !important;
        }
        
        .stCheckbox label div {
            color: #ffffff !important;
        }
        
        .stCheckbox input[type="checkbox"] + label {
            color: #ffffff !important;
        }
        
        /* Pegar todo texto dentro de checkbox */
        .stCheckbox * {
            color: #ffffff !important;
        }
        
        /* Labels dos widgets */
        div[role="radiogroup"] label,
        .stMultiSelect > div > div[class*="stMultiSelect"] label {
            color: #ffffff !important;
        }
        
        /* Todos os span e div dentro dos filtros */
        .stMultiSelect > div > div > span,
        .stSelectbox > div > div > span {
            color: #ffffff !important;
        }
        
        /* Títulos */
        h1, h2, h3 {
            color: #d4af37;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #0a2540;
            color: #d4af37;
            border: 2px solid #0033cc;
            border-radius: 6px;
        }
        
        /* Info boxes */
        .stAlert {
            background-color: #0a2540;
            border: 2px solid #d4af37;
            border-radius: 6px;
        }
        
        /* Tabelas */
        .streamlit-dataframe {
            background-color: #0a2540;
            color: #ffffff;
        }
        
        table {
            color: #ffffff;
            background-color: #0a2540;
        }
        
        th {
            background-color: #0033cc !important;
            color: #d4af37 !important;
            font-weight: bold;
        }
        
        td {
            background-color: #0f4c75 !important;
            color: #ffffff;
        }
        
        tr:hover {
            background-color: #164863 !important;
        }
        
        /* Markdown */
        .markdown-text-container {
            color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True)

# Função para formatar preço em reais
def formatar_preco_reais(valor):
    if valor is None:
        return 'Preço não disponível'
    else:
        return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

# Função para formatar número em formato brasileiro
def formatar_numero_br(valor):
    """Formata número para padrão brasileiro (vírgula como separador decimal)"""
    return f'{valor:.2f}'.replace('.', ',')

# Função para encontrar coluna com variações de nome
def encontrar_coluna(df, nomes_possiveis):
    """Procura por uma coluna entre várias variações de nome (case-insensitive)"""
    colunas_lower = {col.lower(): col for col in df.columns}
    # Preferência por correspondência exata (case-insensitive)
    for nome in nomes_possiveis:
        chave = nome.lower()
        if chave in colunas_lower:
            return colunas_lower[chave]

    # Se não houver correspondência exata, procurar por substring nos nomes das colunas
    for col_lower, col_original in colunas_lower.items():
        for nome in nomes_possiveis:
            if nome.lower() in col_lower:
                return col_original

    return None

# Função para remover outliers usando o método IQR (Interquartile Range)
def remover_outliers_iqr(dataframe, coluna):
    """
    Remove outliers usando o método IQR.
    Outliers são valores fora da faixa [Q1 - 1.5*IQR, Q3 + 1.5*IQR]
    Retorna: (df_sem_outliers, quantidade_removida, limite_inferior, limite_superior)
    """
    # Garantir que a coluna exista
    if coluna not in dataframe.columns:
        return dataframe.copy(), 0, None, None

    # Calcular quartis e IQR ignorando valores nulos
    serie = dataframe[coluna].dropna()
    if serie.empty:
        return dataframe.copy(), 0, None, None

    Q1 = serie.quantile(0.25)
    Q3 = serie.quantile(0.75)
    IQR = Q3 - Q1
    limite_inferior = Q1 - 1.5 * IQR
    limite_superior = Q3 + 1.5 * IQR

    df_sem_outliers = dataframe[(dataframe[coluna] >= limite_inferior) & (dataframe[coluna] <= limite_superior)]
    outliers_removidos = len(dataframe) - len(df_sem_outliers)

    return df_sem_outliers, outliers_removidos, limite_inferior, limite_superior

# URLs atualizadas
consultarItemMaterial_base_url = 'https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial'
consultarItemServico_base_url = 'https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico'

def obter_itens(tipo_item, codigo_item_catalogo, pagina, tamanho_pagina):
    url = consultarItemMaterial_base_url if tipo_item == 'Material' else consultarItemServico_base_url
    params = {
        'pagina': pagina,   
        'tamanhoPagina':tamanho_pagina,  # Ajuste para 500 itens por página
        'codigoItemCatalogo': codigo_item_catalogo
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            json_response = response.json()
            itens = json_response.get('resultado', [])
            paginas_restantes = json_response.get('paginasRestantes', 0)
            total_paginas = json_response.get('totalPaginas', 0)
            return itens, paginas_restantes, total_paginas
        else:
            st.error(f"Erro na consulta: {response.status_code}")
            return [], 0
    except Exception as e:
        st.error(f"Erro ao realizar a requisição: {str(e)}")
        return [], 0

# Streamlit UI
# Header customizado
col_header1, col_header2, col_header3 = st.columns([1, 2, 1])
with col_header2:
    st.markdown("""
        <div class="header-container">
            <div class="logo-text">⚓ MARINHA DO BRASIL ⚓</div>
            <div class="sistema-nome">AtaCotada</div>
            <div class="subtitulo">PESQUISA DE PREÇOS DE MATERIAIS E SERVIÇOS</div>
        </div>
    """, unsafe_allow_html=True)

# Disclaimer com estilo
st.markdown("""
    <div style="background-color: #0a2540; padding: 1rem; border-radius: 8px; border-left: 5px solid #d4af37; margin-bottom: 1.5rem;">
        <p style="color: #d4af37; font-weight: bold; margin-bottom: 0.5rem;">📚 Orientação</p>
        <p style="color: #ffffff;">Utilize o catálogo de materiais e serviços do Governo Federal para encontrar o código desejado.</p>
    </div>
""", unsafe_allow_html=True)

components.iframe("https://catalogo.compras.gov.br/cnbs-web/busca", height=450, width=1080, scrolling=True)

# Seção de consulta
st.markdown("""
    <div style="color: #d4af37; font-size: 20px; font-weight: bold; margin-top: 2rem; margin-bottom: 1rem;">
        🔍 Consultar Item
    </div>
""", unsafe_allow_html=True)

col_tipo, col_codigo, col_botao = st.columns([1, 2, 1])

with col_tipo:
    tipo_item = st.selectbox("Tipo de Item", ['Material', 'Serviço'], key='tipo_item')

with col_codigo:
    codigo_item_catalogo = st.text_input("Código do Item de Catálogo", value="", key='codigo_item_catalogo', placeholder="Ex: 123456")

with col_botao:
    st.write("")
    st.write("")
    consultar = st.button('🔎 Consultar', use_container_width=True)

pagina = 1
tamanho_pagina = 500

if consultar:
    if codigo_item_catalogo:  # Verifica se o código do item de catálogo não está vazio
        itens, paginas_restantes, total_paginas = obter_itens(tipo_item, codigo_item_catalogo, pagina, tamanho_pagina)
        if itens:  # Ensure 'itens' is not empty before proceeding
            st.session_state['itens'] = itens      
        else:
            st.error("Nenhum item encontrado. Por favor, tente com um código diferente ou verifique a conexão com a API.")
    else:
        st.warning("Por favor, informe o código do item de catálogo para realizar a consulta.")

# Mostrar filtros e resultados se houver dados em session_state
if st.session_state.get('itens'):
    try:
        # Ensure 'itens' is in the expected format before normalization
        if isinstance(st.session_state['itens'], list) and all(isinstance(item, dict) for item in st.session_state['itens']):
            df_completo = pd.json_normalize(st.session_state['itens'])
            
            # Encontrar colunas com nomes variáveis
            col_unidade = encontrar_coluna(df_completo, ['unidadeFornecimento', 'unidade_fornecimento', 'unidade', 'unitFornecimento'])
            col_nome_unidade = encontrar_coluna(df_completo, ['nomeUnidadeFornecimento', 'nome_unidade_fornecimento', 'nomeUnidade', 'nome_unidade'])
            col_estado = encontrar_coluna(df_completo, ['uf', 'estado', 'estadoUf', 'estado_uf'])
            col_precounitario = encontrar_coluna(df_completo, ['precoUnitario', 'preco_unitario', 'preço_unitário'])
            col_uasg = encontrar_coluna(df_completo, ['nomeUasg', 'nome_uasg', 'uasg', 'nomeUAsg'])
            
            # Seção de Filtros
            st.markdown("""
                <div style="color: #d4af37; font-size: 20px; font-weight: bold; margin-top: 2rem; margin-bottom: 1rem;">
                    ⚙️ Filtros de Consulta
                </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            # Inicializar variáveis de filtro
            unidade_selecionada = []
            nome_unidade_input = ""
            estado_selecionado = []
            uasg_input = ""
            remover_outliers = False
            
            with col1:
                # Filtro de unidade de fornecimento (se a coluna existir)
                if col_unidade:
                    unidades_disponiveis = df_completo[col_unidade].dropna().unique().tolist()
                    if unidades_disponiveis:
                        unidade_selecionada = st.multiselect(
                            "Unidade de Fornecimento",
                            options=sorted(unidades_disponiveis),
                            default=unidades_disponiveis,
                            key='filtro_unidade'
                        )
                
                # Filtro de nome unidade fornecimento (se a coluna existir)
                if col_nome_unidade:
                    nome_unidade_input = st.text_input(
                        "Nome Unidade Fornecimento",
                        value="",
                        key='filtro_nome_unidade',
                        placeholder="Filtrar por nome..."
                    )
                
                # Filtro de nome UASG (se a coluna existir) - ABAIXO DO FILTRO DA UNIDADE
                if col_uasg:
                    uasg_input = st.text_input(
                        "Nome UASG",
                        value="",
                        key='filtro_uasg',
                        placeholder="Filtrar por nome..."
                    )
            
            with col2:
                # Filtro de estado (se a coluna existir)
                if col_estado:
                    estados_disponiveis = df_completo[col_estado].dropna().unique().tolist()
                    if estados_disponiveis:
                        estado_selecionado = st.multiselect(
                            "Estado (UF)",
                            options=sorted(estados_disponiveis),
                            default=estados_disponiveis,
                            key='filtro_estado'
                        )
                
                # Checkbox para remover outliers
                if col_precounitario:
                    remover_outliers = st.checkbox(
                        "🔍 Remover outliers (IQR)",
                        value=False,
                        key='filtro_outliers'
                    )
                    st.write("")
            
            # Aplicar filtros iniciais (sem preço ainda)
            dataframe = df_completo.copy()
            
            # Filtro de unidade de fornecimento
            if col_unidade and unidade_selecionada:
                dataframe = dataframe[dataframe[col_unidade].isin(unidade_selecionada)]
            
            # Filtro de nome unidade fornecimento
            if col_nome_unidade and nome_unidade_input:
                dataframe = dataframe[dataframe[col_nome_unidade].str.contains(nome_unidade_input, case=False, na=False)]
            
            # Filtro de estado
            if col_estado and estado_selecionado:
                dataframe = dataframe[dataframe[col_estado].isin(estado_selecionado)]
            
            # Filtro de nome UASG
            if col_uasg and uasg_input:
                dataframe = dataframe[dataframe[col_uasg].str.contains(uasg_input, case=False, na=False)]
            
            # Remover outliers se selecionado (ANTES do slider de preço)
            outliers_info = None
            if remover_outliers and col_precounitario and col_precounitario in dataframe.columns:
                dataframe_temp, outliers_removidos, limite_inf, limite_sup = remover_outliers_iqr(dataframe, col_precounitario)
                outliers_info = {
                    'removidos': outliers_removidos,
                    'limite_inf': limite_inf,
                    'limite_sup': limite_sup
                }
                dataframe = dataframe_temp
            
            # Agora mostrar o slider de preço com os limites corretos (após remover outliers se necessário)
            faixa_preco = (0, 0)
            if col_precounitario and col_precounitario in dataframe.columns and len(dataframe) > 0:
                preco_min_filtrado = dataframe[col_precounitario].min()
                preco_max_filtrado = dataframe[col_precounitario].max()
                
                faixa_preco = st.slider(
                    "Faixa de Preço Unitário (R$)",
                    min_value=float(preco_min_filtrado),
                    max_value=float(preco_max_filtrado),
                    value=(float(preco_min_filtrado), float(preco_max_filtrado)),
                    step=0.01,
                    key='filtro_preco'
                )
                
                # Mostrar valores selecionados em formato brasileiro
                st.markdown(f"""
                    <div style="background-color: #0a2540; padding: 0.8rem; border-radius: 6px; border-left: 4px solid #d4af37; margin-top: 0.5rem;">
                        <span style="color: #d4af37; font-weight: bold;">Intervalo selecionado:</span>
                        <span style="color: #ffffff;"> {formatar_preco_reais(faixa_preco[0])} até {formatar_preco_reais(faixa_preco[1])}</span>
                    </div>
                """, unsafe_allow_html=True)
            
            # Aplicar filtro de preço
            if col_precounitario and col_precounitario in dataframe.columns:
                dataframe = dataframe[
                    (dataframe[col_precounitario] >= faixa_preco[0]) &
                    (dataframe[col_precounitario] <= faixa_preco[1])
                ]
            
            # Mostrar estatísticas apenas dos dados filtrados
            if len(dataframe) > 0:
                # Seção de resultados
                st.markdown("""
                    <div style="color: #d4af37; font-size: 20px; font-weight: bold; margin-top: 2rem; margin-bottom: 1rem;">
                        📊 Resultados
                    </div>
                """, unsafe_allow_html=True)
                
                # Mostrar contagem com destaque
                col_info_a, col_info_b = st.columns([1, 1])
                with col_info_a:
                    st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #0a2540 0%, #164863 100%); padding: 1.5rem; border-radius: 8px; border-left: 5px solid #d4af37; text-align: center;">
                            <div style="color: #d4af37; font-size: 14px; font-weight: bold; letter-spacing: 1px;">REGISTROS ENCONTRADOS</div>
                            <div style="color: #ffffff; font-size: 32px; font-weight: bold; margin-top: 0.5rem;">{len(dataframe)}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Mostrar informações sobre outliers removidos
                if outliers_info:
                    with col_info_b:
                        st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #0a2540 0%, #164863 100%); padding: 1.5rem; border-radius: 8px; border-left: 5px solid #d4af37; text-align: center;">
                                <div style="color: #d4af37; font-size: 14px; font-weight: bold; letter-spacing: 1px;">OUTLIERS REMOVIDOS</div>
                                <div style="color: #ffffff; font-size: 32px; font-weight: bold; margin-top: 0.5rem;">{outliers_info['removidos']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                # Mostrar faixa de outliers
                if outliers_info:
                    st.markdown(f"""
                        <div style="background-color: #0a2540; padding: 1rem; border-radius: 8px; border-left: 5px solid #d4af37; margin-bottom: 1.5rem;">
                            <span style="color: #d4af37; font-weight: bold;">📊 Faixa válida (sem outliers):</span><br>
                            <span style="color: #ffffff;">{formatar_preco_reais(outliers_info['limite_inf'])} até {formatar_preco_reais(outliers_info['limite_sup'])}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Mostrar estatísticas se a coluna precoUnitario existir
                if col_precounitario and col_precounitario in dataframe.columns:
                    mean = dataframe[col_precounitario].mean()
                    median = dataframe[col_precounitario].median()
                    preco_min = dataframe[col_precounitario].min()
                    preco_max = dataframe[col_precounitario].max()
                    std = dataframe[col_precounitario].std()
                    cv = ((std / mean) * 100) if mean != 0 else 0
                    
                    st.markdown(
                        f"""
                            |Preço Mínimo|Preço Unitário Médio|Preço Unitário Mediano|Preço Máximo|Desvio Padrão|Coeficiente de Variação|
                            |:----------:|:------------------:|:--------------------:|:----------:|:-----------:|:---------------------:|
                            |**{formatar_preco_reais(preco_min)}**|**{formatar_preco_reais(mean)}**|**{formatar_preco_reais(median)}**|**{formatar_preco_reais(preco_max)}**|**{formatar_numero_br(std)}**|**{formatar_numero_br(cv)}%**|
                        """
                    )
                    
                    # Formatar preço para exibição
                    df_exibicao = dataframe.copy()
                    df_exibicao[col_precounitario] = df_exibicao[col_precounitario].apply(formatar_preco_reais)
                    st.write(df_exibicao)
                else:
                    st.write(dataframe)
            else:
                st.warning("Nenhum resultado encontrado com os filtros aplicados. Tente ajustar os critérios.")
                     
        else:
            st.error("Formato dos itens inválido para normalização.")
    except Exception as e:
        st.error(f"Erro ao processar os itens: {str(e)}")
        # Mostrar colunas disponíveis quando há erro
        if st.session_state.get('itens'):
            try:
                df_debug = pd.json_normalize(st.session_state['itens'])
                with st.expander("ℹ️ Colunas disponíveis (Debug)"):
                    st.write("Colunas encontradas no dataframe:")
                    st.write(list(df_debug.columns))
                    st.write("\nPrimeiras linhas dos dados:")
                    st.write(df_debug.head())
            except:
                pass
