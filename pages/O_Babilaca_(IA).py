"""
O Babilaca (IA) — Assistente Inteligente para Licitações e Contratações Públicas
Sistema integrado com IA, APIs públicas e geração de documentos (Lei 14.133/2021)
"""

import streamlit as st
import requests
import pandas as pd
import json
import os
import re
import io
import hashlib
import base64
from datetime import datetime, timedelta
from fpdf import FPDF

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="O Babilaca (IA)",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CSS CUSTOMIZADO
# ============================================================
st.markdown("""
<style>
    body, .main { background-color: #001a4d; color: #ffffff; }
    .stApp { background-color: #001a4d; }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
        border-right: 2px solid #d4af37;
    }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] div { color: #ffffff !important; }
    [data-testid="stSidebar"] .stMarkdown h1,
    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #d4af37; border-bottom: 2px solid #d4af37;
        padding-bottom: 0.5rem; margin-bottom: 1rem;
    }

    .babilaca-header {
        background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%);
        padding: 1.2rem 2rem; border-radius: 12px;
        margin-bottom: 1.5rem; text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }
    .babilaca-header h1 { color: #d4af37; margin: 0; font-size: 2rem; }
    .babilaca-header p { color: #cbd5e1; margin: 0.3rem 0 0; font-size: 0.95rem; }

    .disclaimer-box {
        background: rgba(212,175,55,0.12); border: 1px solid #d4af37;
        border-radius: 8px; padding: 0.6rem 1rem; margin-bottom: 1rem;
        color: #d4af37; font-size: 0.85rem; text-align: center;
    }
    .doc-card {
        background: linear-gradient(135deg, #0a1628 0%, #132244 100%);
        border: 1px solid #1e3a5f; border-radius: 10px; padding: 1.2rem;
        margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .doc-card h4 { color: #d4af37; margin-top: 0; }
    .doc-card p  { color: #cbd5e1; font-size: 0.9rem; }

    .alert-card {
        border-radius: 10px; padding: 1rem; margin: 0.5rem 0;
        border-left: 4px solid; color: #ffffff;
    }
    .alert-high   { background: rgba(220,38,38,0.15); border-color: #dc2626; }
    .alert-medium { background: rgba(245,158,11,0.15); border-color: #f59e0b; }
    .alert-low    { background: rgba(34,197,94,0.15); border-color: #22c55e; }
    .alert-info   { background: rgba(59,130,246,0.15); border-color: #3b82f6; }

    .stat-card {
        background: linear-gradient(135deg, #0a1628 0%, #132244 100%);
        border: 1px solid #1e3a5f; border-radius: 10px; padding: 1rem;
        text-align: center;
    }
    .stat-card .valor { color: #d4af37; font-size: 1.8rem; font-weight: bold; }
    .stat-card .label { color: #94a3b8; font-size: 0.8rem; }

    div[data-testid="stChatMessage"] { background: rgba(10,22,40,0.6) !important; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTES
# ============================================================
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MEMORIA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "babilaca_memoria.json")

MODELOS_DISPONIVEIS = {
    "Google Gemini 2.5 Flash": "google/gemini-2.5-flash",
    "Google Gemini 2.5 Pro": "google/gemini-2.5-pro",
    "OpenAI GPT-4.1": "openai/gpt-4.1",
    "OpenAI GPT-4.1 Mini": "openai/gpt-4.1-mini",
    "Anthropic Claude Sonnet 4": "anthropic/claude-sonnet-4",
    "DeepSeek V3.2": "deepseek/deepseek-v3.2",
    "DeepSeek R1": "deepseek/deepseek-r1-0528",
    "Meta Llama 4 Maverick": "meta-llama/llama-4-maverick",
    "Qwen3 235B": "qwen/qwen3-235b-a22b",
    "Meta Llama 3.3 70B (gratis)": "meta-llama/llama-3.3-70b-instruct:free",
}

# ============================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================
_defaults = {
    "babilaca_messages": [],
    "babilaca_api_key": os.environ.get(
        "OPENROUTER_API_KEY",
        "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",
    ),
    "babilaca_modelo": "google/gemini-2.5-flash",
    "babilaca_alertas": [],
    "babilaca_docs_gerados": [],
    "babilaca_preferencias": {},
    "babilaca_respostas_salvas": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# BASE JURÍDICA (RAG SIMPLIFICADO)
# ============================================================
BASE_JURIDICA = [
    # --- Lei 14.133/2021 ---
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 6°",
        "titulo": "Definições",
        "conteudo": (
            "Define os conceitos fundamentais: obra, serviço, compra, alienação, "
            "contratação direta, licitação, pregão, concorrência, diálogo competitivo, "
            "sistema de registro de preços, ata de registro de preços, entre outros."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art6",
        "palavras_chave": [
            "definição", "conceito", "obra", "serviço", "compra", "contratação",
            "licitação", "pregão", "concorrência", "registro de preços", "ata",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 11",
        "titulo": "Objetivos do processo licitatório",
        "conteudo": (
            "O processo licitatório tem por objetivos: I – assegurar a seleção da proposta "
            "apta a gerar o resultado de contratação mais vantajoso para a Administração "
            "Pública; II – assegurar tratamento isonômico entre os licitantes e justa "
            "competição; III – evitar contratações com sobrepreço ou com preços "
            "manifestamente inexequíveis e superfaturamento; IV – incentivar a inovação "
            "e o desenvolvimento nacional sustentável."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art11",
        "palavras_chave": [
            "objetivo", "vantajoso", "isonomia", "competição", "sobrepreço",
            "inexequível", "superfaturamento", "inovação", "sustentável",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 28",
        "titulo": "Modalidades de licitação",
        "conteudo": (
            "São modalidades de licitação: I – pregão; II – concorrência; "
            "III – concurso; IV – leilão; V – diálogo competitivo. "
            "O pregão é obrigatório para aquisição de bens e serviços comuns. "
            "A concorrência aplica-se a obras, serviços especiais e bens especiais. "
            "O diálogo competitivo é para contratações em que a Administração "
            "necessita realizar diálogos com licitantes previamente selecionados."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art28",
        "palavras_chave": [
            "modalidade", "pregão", "concorrência", "concurso", "leilão",
            "diálogo competitivo", "bens comuns", "serviços comuns",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 23",
        "titulo": "Pesquisa de preços",
        "conteudo": (
            "O valor previamente estimado da contratação deverá ser compatível com "
            "os valores praticados pelo mercado, considerados os preços constantes de "
            "bancos de dados públicos e as quantidades a serem contratadas. "
            "A pesquisa de preços deve observar parâmetros definidos em regulamento."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art23",
        "palavras_chave": [
            "preço", "estimado", "mercado", "pesquisa", "orçamento",
            "banco de dados", "valor estimado", "cotação",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 17 e Art. 18",
        "titulo": "Fases da licitação e fase preparatória",
        "conteudo": (
            "Art. 17: O processo de licitação observará as seguintes fases, em sequência: "
            "I – preparatória; II – de divulgação do edital de licitação; "
            "III – de apresentação de propostas e lances, quando for o caso; "
            "IV – de julgamento; V – de habilitação; VI – recursal; "
            "VII – de homologação. "
            "Art. 18: A fase preparatória do processo licitatório é caracterizada "
            "pelo planejamento e deve compatibilizar-se com o plano de contratações anual. "
            "Compreende: formalização da demanda, estudo técnico preliminar (ETP), "
            "análise de riscos, termo de referência ou projeto básico, "
            "e orçamento estimado."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art17",
        "palavras_chave": [
            "fase", "preparatória", "edital", "proposta", "lance",
            "julgamento", "habilitação", "recurso", "homologação",
            "estudo técnico", "termo de referência", "planejamento",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 75",
        "titulo": "Contratação direta — Dispensa e inexigibilidade",
        "conteudo": (
            "É dispensável a licitação em diversas hipóteses, incluindo: "
            "contratação de valor até R$ 59.906,02 para obras e serviços de engenharia "
            "(atualizado pelo Decreto 12.343/2024); até R$ 59.906,02 para outros serviços "
            "e compras; em caso de emergência ou calamidade pública; "
            "quando não acudirem interessados à licitação anterior. "
            "É inexigível a licitação quando houver inviabilidade de competição, "
            "como fornecedor exclusivo, profissional de notória especialização ou "
            "artista consagrado."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art75",
        "palavras_chave": [
            "dispensa", "inexigibilidade", "contratação direta", "emergência",
            "valor", "limite", "fornecedor exclusivo", "notória especialização",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 82",
        "titulo": "Sistema de Registro de Preços (SRP)",
        "conteudo": (
            "O Sistema de Registro de Preços pode ser adotado quando: "
            "I – pelas características do bem ou serviço, houver necessidade de "
            "contratações frequentes; II – for mais conveniente aquisição com previsão "
            "de entregas parceladas; III – for conveniente para atendimento a mais de "
            "um órgão ou entidade; IV – pela natureza do objeto, não for possível "
            "definir previamente o quantitativo a ser demandado. "
            "A ata de registro de preços terá prazo de validade de até 1 ano, "
            "prorrogável por igual período."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art82",
        "palavras_chave": [
            "registro de preços", "SRP", "ata", "adesão", "carona",
            "frequente", "parcelada", "prazo", "validade",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 95",
        "titulo": "Formalização dos contratos",
        "conteudo": (
            "O contrato deverá conter cláusulas que definam: o objeto e seus elementos "
            "característicos; a vinculação ao edital; a legislação aplicável; "
            "o regime de execução; o preço e condições de pagamento; "
            "os prazos; os direitos e obrigações das partes; "
            "a matriz de riscos (quando aplicável); as penalidades."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art95",
        "palavras_chave": [
            "contrato", "cláusula", "objeto", "preço", "pagamento",
            "prazo", "obrigação", "penalidade", "risco", "formalização",
        ],
    },
    {
        "fonte": "Lei 14.133/2021",
        "artigo": "Art. 155-163",
        "titulo": "Sanções administrativas",
        "conteudo": (
            "O licitante ou contratado será responsabilizado administrativamente: "
            "advertência; multa (não inferior a 0,5% nem superior a 30% do valor contratado); "
            "impedimento de licitar e contratar (até 3 anos); "
            "declaração de inidoneidade (3 a 6 anos). "
            "As sanções devem ser aplicadas com observância ao contraditório e ampla defesa."
        ),
        "link": "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm#art155",
        "palavras_chave": [
            "sanção", "penalidade", "multa", "impedimento", "inidoneidade",
            "advertência", "infração", "punição",
        ],
    },
    # --- Instruções Normativas ---
    {
        "fonte": "IN SEGES/ME n. 65/2021",
        "artigo": "Arts. 1 a 10",
        "titulo": "Pesquisa de precos para contratacoes",
        "conteudo": (
            "Estabelece procedimentos para pesquisa de precos: "
            "I - Painel de Precos ou banco de precos em saude (parametro preferencial); "
            "II - Aquisicoes e contratacoes similares de outros entes publicos; "
            "III - Dados de pesquisa publicada em midia especializada, sitios eletronicos "
            "especializados ou de dominio amplo; "
            "IV - Pesquisa direta com fornecedores. "
            "Deve-se utilizar no minimo 3 precos. "
            "Devem ser desconsiderados precos inexequiveis ou excessivamente elevados."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-no-65-de-7-de-julho-de-2021",
        "palavras_chave": [
            "pesquisa de precos", "IN 65", "painel de precos", "cotacao",
            "fornecedor", "parametro", "minimo", "preco inexequivel",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 65/2021",
        "artigo": "Art. 2",
        "titulo": "Parametros de pesquisa de precos - ordem de prioridade",
        "conteudo": (
            "A pesquisa de precos para fins de determinacao do preco estimado em "
            "processo licitatorio deve observar os seguintes parametros, nesta ordem: "
            "I - composicao de custos unitarios menores ou iguais a mediana do Painel de Precos; "
            "II - contratacoes similares feitas pela Administracao Publica (ultimos 12 meses); "
            "III - dados de pesquisa publicada em midia especializada, "
            "sitios eletronicos especializados ou de dominio amplo; "
            "IV - pesquisa direta com no minimo 3 fornecedores. "
            "Excepcionalmente, mediante justificativa, sera admitido preco estimado "
            "com base em menos de 3 precos."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-no-65-de-7-de-julho-de-2021",
        "palavras_chave": [
            "parametro", "prioridade", "painel", "mediana", "12 meses",
            "3 fornecedores", "cotacao", "preco estimado", "IN 65",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 65/2021",
        "artigo": "Art. 5",
        "titulo": "Metodologia de calculo do preco estimado",
        "conteudo": (
            "O preco estimado sera obtido pela media, mediana ou menor valor dos precos "
            "obtidos na pesquisa, mediante justificativa da metodologia adotada. "
            "Devem ser desconsiderados valores inexequiveis (inferiores a 75% da mediana) "
            "e excessivos (superiores a 225% da mediana). "
            "A pesquisa deve ser documentada com registro de fontes, datas e metodologia."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-no-65-de-7-de-julho-de-2021",
        "palavras_chave": [
            "media", "mediana", "menor valor", "metodologia", "inexequivel",
            "75%", "225%", "excessivo", "IN 65", "calculo",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 65/2021",
        "artigo": "Art. 6",
        "titulo": "Pesquisa de precos para contratacao direta",
        "conteudo": (
            "Na contratacao direta por dispensa ou inexigibilidade, a estimativa de "
            "preco deve ser realizada quando possivel com os parametros do Art. 2. "
            "Quando inviavel, e aceitavel a justificativa de preco com base em "
            "nota fiscal, proposta do fornecedor ou tabela oficial de precos."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-no-65-de-7-de-julho-de-2021",
        "palavras_chave": [
            "contratacao direta", "dispensa", "inexigibilidade", "nota fiscal",
            "proposta", "justificativa de preco", "IN 65",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 58/2022",
        "artigo": "Arts. 1 a 30",
        "titulo": "Planejamento das contratacoes - PCA e DFD",
        "conteudo": (
            "Disciplina o planejamento das contratacoes, o Plano de Contratacoes Anual "
            "(PCA) e o Documento de Formalizacao de Demanda (DFD). "
            "O DFD deve conter: justificativa da necessidade, quantidade estimada, "
            "previsao de data, grau de prioridade e indicacao do requisitante. "
            "O Estudo Tecnico Preliminar (ETP) deve analisar a viabilidade, "
            "os riscos e as alternativas de contratacao."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-seges-me-no-58-de-8-de-agosto-de-2022",
        "palavras_chave": [
            "planejamento", "PCA", "DFD", "demanda", "ETP",
            "estudo tecnico", "viabilidade", "prioridade", "IN 58",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 58/2022",
        "artigo": "Arts. 7 a 12",
        "titulo": "Estudo Tecnico Preliminar (ETP)",
        "conteudo": (
            "O ETP deve conter: descricao da necessidade, requisitos da contratacao, "
            "levantamento de mercado, estimativa de quantidades, estimativa de custos, "
            "descricao da solucao, justificativas para parcelamento ou nao, "
            "providencias para adequacao do ambiente, analise de riscos, "
            "posicionamento quanto a viabilidade da contratacao. "
            "O ETP e elaborado pelo setor tecnico e deve anteceder o Termo de Referencia."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-seges-me-no-58-de-8-de-agosto-de-2022",
        "palavras_chave": [
            "ETP", "estudo tecnico preliminar", "viabilidade", "solucao",
            "requisitos", "risco", "parcelamento", "IN 58",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 58/2022",
        "artigo": "Arts. 13 a 18",
        "titulo": "Termo de Referencia e Projeto Basico",
        "conteudo": (
            "O Termo de Referencia deve conter: descricao do objeto, fundamentacao, "
            "descricao da solucao, requisitos da contratacao, modelo de execucao, "
            "modelo de gestao, criterios de medicao e pagamento, forma e criterios "
            "de selecao do fornecedor, adequacao orcamentaria. "
            "E obrigatorio para licitacoes de bens e servicos comuns."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas/instrucao-normativa-seges-me-no-58-de-8-de-agosto-de-2022",
        "palavras_chave": [
            "termo de referencia", "projeto basico", "objeto", "execucao",
            "gestao", "medicao", "pagamento", "IN 58",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 73/2022",
        "artigo": "Arts. 1 a 25",
        "titulo": "Procedimentos para aplicacao de sancoes",
        "conteudo": (
            "Regulamenta o procedimento administrativo para aplicacao de sancoes "
            "a licitantes e contratados no ambito da administracao publica federal: "
            "o registro no SICAF, e o cadastro de fornecedores impedidos e inidoneos. "
            "Define prazos de defesa (15 dias uteis), criterios de dosimetria "
            "(gravidade, dano, reincidencia, boa-fe), procedimentos para ampla defesa "
            "e contraditorio. As sancoes devem ser proporcionais a infração."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas",
        "palavras_chave": [
            "sancao", "SICAF", "cadastro", "impedido", "inidoneo",
            "dosimetria", "defesa", "IN 73", "penalidade", "infração",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 67/2021",
        "artigo": "Arts. 1 a 15",
        "titulo": "Sistema de Registro de Precos (SRP) e adesao (carona)",
        "conteudo": (
            "Regulamenta o Sistema de Registro de Precos. A adesao a ata (carona) "
            "e permitida desde que: a ata esteja vigente; haja justificativa de "
            "vantajosidade; haja anuencia do orgao gerenciador e do fornecedor; "
            "nao ultrapasse o limite de 50% dos quantitativos registrados (orgaos federais) "
            "ou o limite individual previsto na ata. "
            "O orgao nao participante deve demonstrar que os precos sao compativeis "
            "com o mercado e que a adesao e mais vantajosa que nova licitacao."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas",
        "palavras_chave": [
            "SRP", "registro de precos", "adesao", "carona", "ata",
            "gerenciador", "50%", "vantajosidade", "IN 67",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 81/2022",
        "artigo": "Arts. 1 a 10",
        "titulo": "Dispensa eletronica de licitacao",
        "conteudo": (
            "Regulamenta a dispensa de licitacao na forma eletronica. "
            "A dispensa eletronica deve ser realizada no sistema Compras.gov.br. "
            "Prazo minimo de 3 dias uteis para envio de propostas. "
            "Aplicavel para contratacoes de valor ate os limites do Art. 75 da Lei 14.133. "
            "Deve haver ampla divulgacao e garantir competitividade. "
            "O fornecedor com menor preco sera convocado para negociacao."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas",
        "palavras_chave": [
            "dispensa eletronica", "compras.gov.br", "3 dias uteis",
            "menor preco", "IN 81", "dispensa", "eletronica", "limite",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 91/2022",
        "artigo": "Arts. 1 a 12",
        "titulo": "Contratacao de servicos terceirizados",
        "conteudo": (
            "Regulamenta a contratacao de servicos continuos com mao de obra dedicada. "
            "Exige conta-deposito vinculada para provisoes trabalhistas, "
            "planilha de custos e formacao de precos detalhada, "
            "repactuacao anual baseada em convencao coletiva de trabalho. "
            "O fiscal deve verificar regularidade fiscal e trabalhista mensal."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas",
        "palavras_chave": [
            "terceirizacao", "mao de obra", "continuos", "planilha de custos",
            "repactuacao", "convencao coletiva", "fiscal", "IN 91",
        ],
    },
    {
        "fonte": "IN SEGES/ME n. 94/2022",
        "artigo": "Arts. 1 a 8",
        "titulo": "Contratacao de solucoes de TIC",
        "conteudo": (
            "Regulamenta a contratacao de solucoes de Tecnologia da Informacao e "
            "Comunicacao (TIC). Exige ETP-Digital elaborado no sistema, "
            "alinhamento com o PDTIC, analise de viabilidade tecnica, "
            "e sustentacao por contrato de manutencao e suporte. "
            "A licitacao deve ser por pregao eletronico para bens e servicos comuns de TIC."
        ),
        "link": "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas",
        "palavras_chave": [
            "TIC", "tecnologia da informacao", "TI", "PDTIC", "ETP digital",
            "software", "hardware", "IN 94", "computador", "sistema",
        ],
    },
    # --- Acordaos TCU (expandido) ---
    {
        "fonte": "TCU - Acordao 1.793/2011-Plenario",
        "artigo": "",
        "titulo": "Pesquisa de precos ampla e diversificada",
        "conteudo": (
            "O TCU firmou entendimento de que a pesquisa de precos deve contemplar "
            "diversas fontes, incluindo contratacoes publicas anteriores, midia "
            "especializada e pesquisa direta com fornecedores, para que o preco "
            "estimado reflita adequadamente os valores de mercado. "
            "A utilizacao de apenas uma fonte e insuficiente e configura falha "
            "no planejamento. Recomenda-se cesta de precos com no minimo 3 fontes."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1793%252F2011/%2520/DTRELEVANCIA%2520desc%252C%2520NUMACORDAOINT%2520desc/0/",
        "palavras_chave": [
            "TCU", "pesquisa de precos", "fontes", "mercado", "acordao",
            "cesta de precos", "1793", "diversificada",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.170/2007-Plenario",
        "artigo": "",
        "titulo": "Sobrepreco e superfaturamento - conceitos e distincoes",
        "conteudo": (
            "O TCU considera sobrepreco quando o preco contratado supera o preco "
            "de referencia (mediana de mercado). Superfaturamento ocorre quando ha "
            "medicao ou pagamento indevido de servicos nao executados, quantidades "
            "superiores ou qualidade inferior. Ambos configuram dano ao erario e "
            "podem ensejar aplicacao de multa, inabilitacao e ressarcimento. "
            "O preco de referencia deve ser a mediana dos precos coletados."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2170%252F2007/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "sobrepreco", "superfaturamento", "dano ao erario", "mediana",
            "TCU", "referencia", "2170", "multa",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.861/2008-Plenario",
        "artigo": "",
        "titulo": "Fracionamento de despesa e fuga de modalidade",
        "conteudo": (
            "O TCU entende que o fracionamento de despesa com vistas a fugir da "
            "modalidade licitatoria adequada configura irregularidade grave. "
            "O planejamento deve considerar todas as necessidades do exercicio. "
            "Contratos de mesmo objeto celebrados no mesmo exercicio que somados "
            "ultrapassam o limite da modalidade utilizada configuram fracionamento. "
            "Cabe ao gestor demonstrar que nao havia como prever as necessidades."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2861%252F2008/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "fracionamento", "despesa", "modalidade", "irregular",
            "planejamento", "TCU", "2861", "limite",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.224/2020-Plenario",
        "artigo": "",
        "titulo": "Contratacao direta - Justificativa de preco obrigatoria",
        "conteudo": (
            "Nas contratacoes diretas (dispensa e inexigibilidade), e indispensavel "
            "a justificativa detalhada do preco, demonstrando que o valor e compativel "
            "com o mercado. A ausencia de justificativa de preco e irregularidade grave. "
            "Deve-se apresentar pelo menos 3 cotacoes ou demonstrar que ha tabela "
            "oficial, nota fiscal recente ou contratacoes similares que embasam o valor."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1224%252F2020/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "contratacao direta", "dispensa", "inexigibilidade",
            "justificativa de preco", "mercado", "TCU", "1224",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.637/2015-Plenario",
        "artigo": "",
        "titulo": "Termo de Referencia deficiente e direcionamento",
        "conteudo": (
            "O TCU determina que o Termo de Referencia deve ser elaborado com "
            "especificacoes claras, suficientes e nao restritivas a competicao. "
            "Indicacao de marca sem justificativa tecnica configura direcionamento. "
            "Especificacoes vagas prejudicam o julgamento e comprometem a contratacao. "
            "E responsabilidade do setor requisitante e do setor tecnico a adequada "
            "descricao do objeto."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2637%252F2015/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "termo de referencia", "especificacao", "marca", "direcionamento",
            "restricao", "competicao", "TCU", "2637",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.214/2013-Plenario",
        "artigo": "",
        "titulo": "Obrigatoriedade de publicacao no PNCP e transparencia",
        "conteudo": (
            "O TCU reafirma que todos os atos do processo licitatorio devem ser "
            "publicados nos meios oficiais, incluindo DOU e PNCP, para garantir "
            "transparencia e controle social. A falta de publicidade pode "
            "configurar cerceamento de competicao e nulidade do certame."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1214%252F2013/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "publicacao", "PNCP", "DOU", "transparencia", "publicidade",
            "competicao", "nulidade", "TCU", "1214",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.390/2004-Plenario",
        "artigo": "",
        "titulo": "Parcelamento do objeto licitatorio",
        "conteudo": (
            "O TCU entende que o parcelamento do objeto e a regra, devendo ser adotado "
            "sempre que tecnica e economicamente viavel, visando ampliar a competitividade. "
            "A nao adocao do parcelamento exige justificativa fundamentada "
            "demonstrando inviabilidade tecnica ou prejuizo economico ao conjunto. "
            "O parcelamento nao se confunde com fracionamento de despesa."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1390%252F2004/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "parcelamento", "objeto", "competitividade", "viavel",
            "justificativa", "lote", "TCU", "1390",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.622/2015-Plenario",
        "artigo": "",
        "titulo": "Registro de precos - Adesao (carona) - Limites e requisitos",
        "conteudo": (
            "O TCU esclarece os requisitos para adesao a ata de registro de precos: "
            "necessidade de justificativa da vantajosidade, compatibilidade do preco "
            "com o mercado, anuencia do orgao gerenciador e do fornecedor, "
            "respeito aos limites quantitativos. "
            "A adesao nao pode ser utilizada para burlar a obrigacao de licitar. "
            "O orgao deve demonstrar que o preco registrado continua vantajoso."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2622%252F2015/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "adesao", "carona", "registro de precos", "ata", "gerenciador",
            "vantajosidade", "limite", "TCU", "2622",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.328/2018-Plenario",
        "artigo": "",
        "titulo": "Gestao e fiscalizacao contratual - obrigatoriedade",
        "conteudo": (
            "O TCU determina que a Administracao deve designar formalmente "
            "fiscal e gestor do contrato, com capacidade tecnica para acompanhar "
            "a execucao. A ausencia de fiscalizacao adequada e a falta de "
            "atesto tecnico das medicoes configuram irregularidade. "
            "O fiscal deve registrar ocorrencias, notificar a contratada "
            "e comunicar ao gestor qualquer inadimplencia."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2328%252F2018/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "fiscal", "gestor", "contrato", "fiscalizacao", "medicao",
            "inadimplencia", "atesto", "TCU", "2328",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.613/2015-Plenario",
        "artigo": "",
        "titulo": "Pregao eletronico obrigatorio para bens e servicos comuns",
        "conteudo": (
            "O TCU reitera que o pregao, preferencialmente eletronico, e obrigatorio "
            "para aquisicao de bens e servicos comuns. A utilizacao de outra modalidade "
            "sem justificativa configura irregularidade. "
            "Servico comum e aquele cujos padroes de desempenho e qualidade "
            "podem ser objetivamente definidos no edital. "
            "A concorrencia so e admitida quando demonstrada a inviabilidade do pregao."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1613%252F2015/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "pregao", "eletronico", "obrigatorio", "bens comuns",
            "servicos comuns", "concorrencia", "modalidade", "TCU", "1613",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.188/2010-Plenario",
        "artigo": "",
        "titulo": "Inexigibilidade - inviabilidade de competicao",
        "conteudo": (
            "O TCU exige que a inexigibilidade seja fundamentada em documentacao "
            "que comprove a inviabilidade de competicao: atestado de exclusividade "
            "emitido por entidade competente, comprovacao de notoria especializacao, "
            "ou demonstracao tecnica de que so aquele fornecedor atende. "
            "Atestado de exclusividade emitido pelo proprio fabricante nao e aceito; "
            "deve ser emitido por sindicatos, federacoes ou associacoes de classe."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1188%252F2010/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "inexigibilidade", "exclusividade", "inviabilidade", "competicao",
            "atestado", "notoria especializacao", "TCU", "1188",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.992/2020-Plenario",
        "artigo": "",
        "titulo": "Contratacao emergencial - requisitos e limites",
        "conteudo": (
            "O TCU reconhece a possibilidade de contratacao emergencial, mas exige: "
            "situacao de emergencia devidamente caracterizada e comprovada; "
            "contratacao restrita ao periodo estritamente necessario (ate 1 ano); "
            "justificativa de que a emergencia nao decorreu de falta de planejamento; "
            "pesquisa de precos compativel com o mercado. "
            "Emergencia fabricada por dessidia configura responsabilidade do gestor."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2992%252F2020/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "emergencia", "urgencia", "contratacao emergencial", "prazo",
            "dessidia", "planejamento", "TCU", "2992",
        ],
    },
    {
        "fonte": "TCU - Acordao 5.301/2015-1a Camara",
        "artigo": "",
        "titulo": "Pesquisa de precos insuficiente - 1 cotacao",
        "conteudo": (
            "O TCU considerou irregular a pesquisa de precos baseada em unica cotacao. "
            "A Administracao deve buscar ampla pesquisa de mercado, "
            "utilizando no minimo 3 fontes diferentes de precos conforme a IN 65/2021. "
            "Quando nao for possivel obter 3 fontes, deve-se justificar formalmente "
            "a impossibilidade e registrar as tentativas frustradas."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/5301%252F2015/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "pesquisa de precos", "cotacao", "unica", "insuficiente",
            "3 fontes", "minimo", "TCU", "5301", "IN 65",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.106/2021-Plenario",
        "artigo": "",
        "titulo": "Estudo Tecnico Preliminar (ETP) obrigatorio",
        "conteudo": (
            "O TCU reiterou a obrigatoriedade do ETP como elemento fundamental "
            "da fase preparatoria. O ETP deve conter alternativas analisadas, "
            "justificativa da solucao escolhida, analise de riscos e demonstracao "
            "de viabilidade. A contratacao sem ETP ou com ETP deficiente "
            "compromete a legalidade do processo. O ETP deve ser anterior "
            "ao Termo de Referencia."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2106%252F2021/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "ETP", "estudo tecnico preliminar", "fase preparatoria",
            "viabilidade", "risco", "alternativas", "TCU", "2106",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.056/2017-Plenario",
        "artigo": "",
        "titulo": "Terceirizacao - limites e irregularidades",
        "conteudo": (
            "O TCU aponta que a terceirizacao e permitida para atividades acessorias "
            "e instrumentais, sendo vedada para atividades-fim (atividades substantivas). "
            "A contratada deve possuir qualificacao tecnica e economica. "
            "A Administracao deve evitar relacao direta de subordinacao com os "
            "trabalhadores terceirizados, sob pena de configurar vinculo irregular."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1056%252F2017/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "terceirizacao", "atividade-fim", "subordinacao", "vinculo",
            "trabalhadores", "acessoria", "TCU", "1056",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.816/2014-Plenario",
        "artigo": "",
        "titulo": "Sustentabilidade nas contratacoes publicas",
        "conteudo": (
            "O TCU recomenda que a Administracao incorpore criterios de "
            "sustentabilidade ambiental nas licitacoes, conforme Art. 11, IV "
            "da Lei 14.133/2021 e Decreto 7.746/2012. "
            "Criterios sustentaveis nao devem restringir a competitividade "
            "injustificadamente. Devem ser proporcionais e vinculados ao objeto."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2816%252F2014/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "sustentabilidade", "ambiental", "verde", "criterios sustentaveis",
            "meio ambiente", "TCU", "2816",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.743/2015-Plenario",
        "artigo": "",
        "titulo": "Aplicacao de sancoes - proporcionalidade e motivacao",
        "conteudo": (
            "O TCU entende que a aplicacao de sancoes deve observar proporcionalidade "
            "e razoabilidade. Deve-se considerar: natureza e gravidade da infração, "
            "dano causado, circunstancias agravantes e atenuantes, "
            "antecedentes do fornecedor. A sancao deve ser formalmente motivada "
            "e precedida de processo com ampla defesa. "
            "Sancao desproporcional pode ser anulada."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2743%252F2015/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "sancao", "penalidade", "proporcionalidade", "motivacao",
            "multa", "ampla defesa", "TCU", "2743",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.297/2015-Plenario",
        "artigo": "",
        "titulo": "Contratacao de TI - planejamento obrigatorio",
        "conteudo": (
            "O TCU determina que contratacoes de TI devem ser precedidas de "
            "planejamento especifico: alinhamento ao PDTIC, ETP com analise de "
            "alternativas (incluindo solucoes de software livre), "
            "justificativa de escolha da solucao, analise de riscos tecnologicos. "
            "Renovacoes de licencas sem analise de alternativas configuram irregularidade."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1297%252F2015/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "TI", "tecnologia da informacao", "PDTIC", "software",
            "licenca", "planejamento", "TCU", "1297",
        ],
    },
    {
        "fonte": "TCU - Acordao 963/2020-Plenario",
        "artigo": "",
        "titulo": "Gerenciamento de riscos obrigatorio no planejamento",
        "conteudo": (
            "O TCU orienta que o gerenciamento de riscos deve ser parte integrante "
            "da fase preparatoria de toda contratacao, conforme Art. 18, X "
            "da Lei 14.133/2021. Deve-se identificar os riscos, avaliar "
            "probabilidade e impacto, definir respostas e responsaveis. "
            "A ausencia de mapa de riscos compromete a legalidade da contratacao."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/963%252F2020/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "risco", "gerenciamento", "mapa de riscos", "planejamento",
            "probabilidade", "impacto", "matriz", "TCU", "963",
        ],
    },
    {
        "fonte": "TCU - Acordao 827/2019-Plenario",
        "artigo": "",
        "titulo": "Aditivos contratuais - limite de 25%",
        "conteudo": (
            "O TCU reitera que os acrescimos contratuais estao limitados a 25% "
            "do valor do contrato (50% para reforma). O percentual incide sobre o "
            "valor original e nao sobre o valor ja aditado. Acrescimos e supressoes "
            "devem ser calculados separadamente. Aditivos que desnaturem o objeto "
            "original sao irregulares. A necessidade de acrescimo acima do limite "
            "exige nova licitacao."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/827%252F2019/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "aditivo", "acrescimo", "25%", "50%", "contrato", "limite",
            "reforma", "supressao", "TCU", "827",
        ],
    },
    {
        "fonte": "TCU - Acordao 3.190/2019-Plenario",
        "artigo": "",
        "titulo": "Habilitacao - exigencias proporcionais ao objeto",
        "conteudo": (
            "O TCU alerta que exigencias de habilitacao devem ser estritamente "
            "proporcionais ao objeto. Exigencias excessivas ou desproporcionais "
            "restringem a competicao e configuram direcionamento. "
            "Atestados de capacidade tecnica devem ter relacao direta com "
            "as parcelas de maior relevancia do objeto licitado."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/3190%252F2019/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "habilitacao", "exigencia", "proporcional", "competicao",
            "atestado", "capacidade tecnica", "TCU", "3190",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.842/2013-Plenario",
        "artigo": "",
        "titulo": "Orcamento sigiloso - possibilidade e limites",
        "conteudo": (
            "O TCU reconhece a possibilidade de orcamento sigiloso em licitacoes "
            "(Art. 24 da Lei 14.133), desde que haja justificativa adequada. "
            "O sigilo visa impedir conluio entre licitantes. "
            "O orcamento deve ser tornado publico imediatamente apos o encerramento "
            "da fase de lances. O sigilo nao exime a Administracao de realizar "
            "pesquisa de precos adequada."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1842%252F2013/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "orcamento sigiloso", "sigilo", "conluio", "lances",
            "publicidade", "preco estimado", "TCU", "1842",
        ],
    },
    {
        "fonte": "TCU - Acordao 2.471/2008-Plenario",
        "artigo": "",
        "titulo": "Economia de escala e consolidacao de demandas",
        "conteudo": (
            "O TCU recomenda que os orgaos publicos busquem economia de escala "
            "por meio da consolidacao de demandas, atas de registro de precos "
            "compartilhadas e planejamento integrado de compras. "
            "A compra pulverizada sem justificativa desperdiça recursos e "
            "perde poder de barganha."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/2471%252F2008/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "economia de escala", "consolidacao", "demanda", "planejamento",
            "compras", "registro de precos", "TCU", "2471",
        ],
    },
    {
        "fonte": "TCU - Acordao 1.545/2016-Plenario",
        "artigo": "",
        "titulo": "Reequilibrio economico-financeiro de contratos",
        "conteudo": (
            "O TCU esclarece que o reequilibrio economico-financeiro exige: "
            "comprovacao de alea extraordinaria e extracontratual, "
            "posterior a proposta e imprevisivel; nexo causal entre fato e desequilibrio; "
            "demonstracao contabil do impacto. Reajuste periodico "
            "nao se confunde com reequilibrio. O mero aumento de custos "
            "previsivel nao justifica reequilibrio."
        ),
        "link": "https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/1545%252F2016/%2520/DTRELEVANCIA%2520desc/0/",
        "palavras_chave": [
            "reequilibrio", "economico-financeiro", "reajuste", "revisao",
            "alea", "contrato", "desequilibrio", "TCU", "1545",
        ],
    },
]


def buscar_base_juridica(pergunta: str, top_n: int = 12) -> list[dict]:
    """Busca os trechos mais relevantes da base jurídica para a pergunta.
    Retorna uma mistura equilibrada de Leis, INs e Acórdãos TCU."""
    tokens = set(re.findall(r"\w+", pergunta.lower()))
    scored = []
    for item in BASE_JURIDICA:
        kws = set(w.lower() for w in item["palavras_chave"])
        all_text = (item["conteudo"] + " " + item["titulo"]).lower()
        score = sum(1 for t in tokens if any(t in kw for kw in kws))
        score += sum(0.3 for t in tokens if t in all_text)
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    # Garantir mix equilibrado: leis + INs + acórdãos
    leis = [s for s in scored if "Lei 14.133" in s[1]["fonte"]]
    ins = [s for s in scored if "IN " in s[1]["fonte"]]
    acordaos = [s for s in scored if "TCU" in s[1]["fonte"] or "Acordao" in s[1]["fonte"]]
    resultado = []
    # Pegar os melhores de cada categoria, proporcionalmente
    max_lei = max(3, top_n // 3)
    max_in = max(3, top_n // 3)
    max_tcu = max(4, top_n // 3 + top_n % 3)
    resultado.extend(leis[:max_lei])
    resultado.extend(ins[:max_in])
    resultado.extend(acordaos[:max_tcu])
    # Completar com restantes se faltou
    ids_usados = {id(s) for s in resultado}
    for s in scored:
        if len(resultado) >= top_n:
            break
        if id(s) not in ids_usados:
            resultado.append(s)
    resultado.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in resultado[:top_n]]


# ============================================================
# FUNÇÕES DE API (TOOLS)
# ============================================================

def buscar_licitacoes(palavra_chave: str, pagina: int = 1) -> dict:
    """Busca licitações no PNCP."""
    try:
        hoje = datetime.now()
        inicio = (hoje - timedelta(days=90)).strftime("%Y%m%d")
        fim = hoje.strftime("%Y%m%d")
        resp = requests.get(
            "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao",
            params={
                "dataInicial": inicio,
                "dataFinal": fim,
                "pagina": pagina,
                "tamanhoPagina": 10,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            # Filtrar por palavra-chave localmente se a API não suportar
            if palavra_chave:
                kw = palavra_chave.lower()
                if isinstance(data, list):
                    data = [
                        i for i in data
                        if kw in json.dumps(i, ensure_ascii=False).lower()
                    ]
                elif isinstance(data, dict) and "data" in data:
                    data["data"] = [
                        i for i in data.get("data", [])
                        if kw in json.dumps(i, ensure_ascii=False).lower()
                    ]
            return {"sucesso": True, "dados": data, "fonte": "PNCP"}
        return {"sucesso": False, "erro": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def buscar_atas(item_codigo: str = "", descricao: str = "", pagina: int = 1) -> dict:
    """Busca atas de registro de preços no ComprasGov."""
    try:
        params = {"tamanhoPagina": 10, "pagina": pagina}
        if item_codigo:
            params["codigoItemCatalogoMaterial"] = item_codigo
        if descricao:
            params["descricaoItem"] = descricao
        resp = requests.get(
            "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem",
            params=params,
            timeout=15,
        )
        if resp.status_code == 200:
            return {"sucesso": True, "dados": resp.json(), "fonte": "ComprasGov – Atas (ARP)"}
        return {"sucesso": False, "erro": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def consultar_fornecedor(cnpj: str) -> dict:
    """Consulta dados do fornecedor via OpenCNPJ + BrasilAPI."""
    cnpj_limpo = re.sub(r"[./-]", "", cnpj.strip())
    resultado: dict = {"cnpj": cnpj_limpo, "sucesso": False}
    # Tentativa 1 — OpenCNPJ
    try:
        resp = requests.get(f"https://api.opencnpj.org/{cnpj_limpo}", timeout=8)
        if resp.status_code == 200:
            resultado.update({"sucesso": True, "dados": resp.json(), "fonte": "OpenCNPJ"})
            return resultado
    except Exception:
        pass
    # Tentativa 2 — BrasilAPI
    try:
        resp = requests.get(
            f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}", timeout=8
        )
        if resp.status_code == 200:
            resultado.update({"sucesso": True, "dados": resp.json(), "fonte": "BrasilAPI"})
            return resultado
    except Exception:
        pass
    resultado["erro"] = "Não foi possível consultar o CNPJ nas APIs disponíveis."
    return resultado


def buscar_fornecedores_cnae(cnae: str, pagina: int = 1) -> dict:
    """Busca fornecedores por CNAE no ComprasGov."""
    try:
        resp = requests.get(
            "https://dadosabertos.compras.gov.br/modulo-fornecedor/1_consultarFornecedor",
            params={"cnae": cnae, "tamanhoPagina": 10, "pagina": pagina},
            timeout=15,
        )
        if resp.status_code == 200:
            return {"sucesso": True, "dados": resp.json(), "fonte": "ComprasGov – Fornecedores"}
        return {"sucesso": False, "erro": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"sucesso": False, "erro": str(e)}


def buscar_precos_mercado(descricao: str) -> dict:
    """Busca preços de mercado via atas de registro de preços."""
    resultado = buscar_atas(descricao=descricao)
    if resultado.get("sucesso"):
        dados = resultado.get("dados", [])
        if isinstance(dados, dict):
            dados = dados.get("resultado", dados.get("data", []))
        precos = []
        for item in (dados if isinstance(dados, list) else []):
            preco = item.get("valorUnitario") or item.get("precoUnitario")
            if preco:
                precos.append(float(preco))
        if precos:
            return {
                "sucesso": True,
                "quantidade": len(precos),
                "menor": min(precos),
                "maior": max(precos),
                "media": sum(precos) / len(precos),
                "mediana": sorted(precos)[len(precos) // 2],
                "precos": precos[:20],
                "fonte": "ComprasGov – Atas (ARP)",
            }
    return {"sucesso": False, "erro": "Nenhum preço encontrado para o item."}


# ============================================================
# UTILIDADES — EXTRAÇÃO DE TEXTO
# ============================================================

def extrair_texto_pdf(arquivo) -> str:
    """Extrai texto de um arquivo PDF enviado pelo usuário."""
    if not PDF_SUPPORT:
        return "[PyPDF2 não instalado — execute: pip install PyPDF2]"
    try:
        reader = PyPDF2.PdfReader(arquivo)
        textos = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                textos.append(t)
        return "\n".join(textos) if textos else "[Não foi possível extrair texto do PDF]"
    except Exception as e:
        return f"[Erro ao ler PDF: {e}]"


def extrair_dados_excel(arquivo) -> tuple[str, pd.DataFrame | None]:
    """Extrai dados de um arquivo Excel."""
    try:
        df = pd.read_excel(arquivo, engine="openpyxl")
        resumo = f"Planilha com {len(df)} linhas e {len(df.columns)} colunas.\n"
        resumo += f"Colunas: {', '.join(df.columns.astype(str))}\n"
        resumo += f"Primeiras linhas:\n{df.head(10).to_string()}"
        return resumo, df
    except Exception as e:
        return f"[Erro ao ler Excel: {e}]", None


# ============================================================
# COMUNICAÇÃO COM IA (OPENROUTER)
# ============================================================

SYSTEM_PROMPT = """Você é **O Babilaca**, um assistente jurídico inteligente especializado em licitações e contratações públicas brasileiras, com foco na Lei 14.133/2021, Instruções Normativas (SEGES/ME) e jurisprudência do TCU.

═══════════════════════════════════════════════════════════
REGRA FUNDAMENTAL — CITAÇÕES SOMENTE DO CONTEXTO FORNECIDO
═══════════════════════════════════════════════════════════
Você receberá abaixo um bloco chamado CONTEXTO JURÍDICO VERIFICADO contendo artigos de lei, instruções normativas e acórdãos do TCU. Estas são as ÚNICAS fontes que você pode citar com números específicos.

• CITE SOMENTE artigos, INs e acórdãos que estejam EXPLICITAMENTE listados no CONTEXTO JURÍDICO VERIFICADO abaixo.
• NUNCA invente, deduza ou complete números de artigos, INs ou acórdãos a partir de sua memória ou treinamento.
• Se o contexto fornecido contém "Art. 17" da Lei 14.133, cite "Art. 17". Se NÃO contém, NÃO cite.
• Se nenhuma fonte do contexto for relevante para a pergunta, diga: "Não disponho de referência verificada sobre esse ponto específico. Consulte o texto integral da Lei 14.133/2021 ou a jurisprudência do TCU."
• É PROIBIDO citar qualquer Acórdão TCU cujo número não apareça literalmente no contexto.
• É PROIBIDO citar qualquer IN cujo número não apareça literalmente no contexto.
• É PROIBIDO citar artigos da Lei 14.133 cujo número não apareça literalmente no contexto.

REGRAS DE QUALIDADE:
1. Estruture a resposta de forma clara, usando as fontes disponíveis no contexto.
2. Se o contexto contiver fontes de diferentes categorias (Lei, IN, TCU), organize em camadas:
   - **Base legal**: artigo da Lei 14.133/2021 (se disponível no contexto)
   - **Regulamentação**: IN aplicável (se disponível no contexto)
   - **Jurisprudência TCU**: Acórdão relevante (se disponível no contexto)
3. Se uma camada não tiver fonte no contexto, omita-a — NÃO a preencha com informações inventadas.
4. Forneça os links que acompanham cada fonte no contexto (campo 🔗).
5. Responda sempre em português brasileiro.
6. Destaque trechos relevantes com **negrito** e use > citação para trechos literais.
7. Quando utilizar dados de APIs, indique a fonte.
8. No final da resposta, inclua uma seção "📚 **Fontes consultadas**" listando APENAS as fontes do contexto que você efetivamente utilizou, com seus links.
9. Para temas genéricos onde você pode responder com conhecimento geral (ex: conceitos, boas práticas), faça-o — mas NÃO atribua números específicos de artigos/acórdãos/INs que não estejam no contexto.

FORMATO DE CITAÇÃO (somente com fontes do contexto):
- Lei: "Conforme o Art. XX da Lei 14.133/2021..."
- IN: "De acordo com o Art. XX da IN SEGES/ME nº XX/XXXX..."
- TCU: "Nesse sentido, o TCU no Acórdão X.XXX/XXXX-Plenário firmou entendimento de que..."

AVISO: Você é uma ferramenta de apoio. Recomende sempre que o usuário confirme nas fontes oficiais.

{contexto_juridico}

{dados_api}"""


def _build_system_prompt(contexto_items: list[dict], dados_api: str = "") -> str:
    if contexto_items:
        partes = [
            "═══════════════════════════════════════════════",
            "CONTEXTO JURÍDICO VERIFICADO",
            "(Cite SOMENTE as fontes listadas abaixo)",
            "═══════════════════════════════════════════════",
        ]
        for i, item in enumerate(contexto_items, 1):
            fonte = item['fonte']
            artigo = item.get('artigo', '')
            titulo = item['titulo']
            ref = f"{fonte} — {artigo}" if artigo else fonte
            partes.append(
                f"[FONTE {i}] {ref}\n"
                f"Título: {titulo}\n"
                f"Conteúdo: {item['conteudo']}\n"
                f"🔗 Link: {item['link']}"
            )
        partes.append("═══════════════════════════════════════════════")
        partes.append(f"Total de fontes disponíveis: {len(contexto_items)}. NÃO cite nenhuma fonte fora desta lista.")
        ctx = "\n\n".join(partes)
    else:
        ctx = "(Nenhuma fonte jurídica disponível no contexto. Responda com conhecimento geral, SEM citar números específicos de artigos, INs ou acórdãos.)"
    api_section = f"DADOS DE APIs:\n{dados_api}" if dados_api else ""
    return SYSTEM_PROMPT.format(contexto_juridico=ctx, dados_api=api_section)


def chamar_ia(
    mensagens: list[dict],
    system_prompt: str,
    modelo: str | None = None,
    temperatura: float = 0.3,
) -> str:
    """Envia mensagens ao OpenRouter e retorna a resposta."""
    api_key = st.session_state.get("babilaca_api_key", "")
    if not api_key:
        return "⚠️ Chave de API não configurada. Acesse a aba **Configurações**."
    model = modelo or st.session_state.get("babilaca_modelo", "google/gemini-2.0-flash-001")
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}] + mensagens,
        "temperature": temperatura,
        "max_tokens": 4096,
    }
    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://atacotada.streamlit.app",
                "X-Title": "AtaCotada - O Babilaca",
            },
            json=payload,
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        return f"⚠️ Erro na API (HTTP {resp.status_code}): {resp.text[:300]}"
    except requests.Timeout:
        return "⚠️ Tempo limite da requisição excedido. Tente novamente."
    except Exception as e:
        return f"⚠️ Erro ao chamar a IA: {e}"


# ============================================================
# ROTEAMENTO DE INTENÇÃO
# ============================================================

def extrair_cnpj(texto: str) -> str | None:
    m = re.search(r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}", texto)
    return re.sub(r"[./-]", "", m.group()) if m else None


def analisar_intencao(msg: str) -> list[str]:
    """Determina quais APIs chamar com base na mensagem."""
    low = msg.lower()
    acoes = []
    if any(k in low for k in ["licitação", "licitacao", "pregão", "pregao", "edital", "contratação pública"]):
        acoes.append("buscar_licitacoes")
    if any(k in low for k in ["ata de registro", "ata ", "adesão", "adesao", "srp", "registro de preço"]):
        acoes.append("buscar_atas")
    if extrair_cnpj(msg):
        acoes.append("consultar_fornecedor")
    if any(k in low for k in ["fornecedor", "empresa", "cnae"]):
        if "consultar_fornecedor" not in acoes:
            acoes.append("buscar_fornecedores")
    if any(k in low for k in ["preço", "preco", "cotação", "cotacao", "valor de mercado", "quanto custa"]):
        acoes.append("buscar_precos")
    return acoes


def executar_apis(msg: str, acoes: list[str]) -> str:
    """Executa as APIs necessárias e retorna texto com resultados."""
    partes = []
    for acao in acoes:
        if acao == "buscar_licitacoes":
            palavras = re.sub(r"[^\w\s]", "", msg).strip()
            resultado = buscar_licitacoes(palavras)
            partes.append(f"[API — Licitações PNCP]\n{json.dumps(resultado, ensure_ascii=False, default=str)[:2000]}")
        elif acao == "buscar_atas":
            palavras = re.sub(r"[^\w\s]", "", msg).strip()
            resultado = buscar_atas(descricao=palavras)
            partes.append(f"[API — Atas ARP]\n{json.dumps(resultado, ensure_ascii=False, default=str)[:2000]}")
        elif acao == "consultar_fornecedor":
            cnpj = extrair_cnpj(msg)
            if cnpj:
                resultado = consultar_fornecedor(cnpj)
                partes.append(f"[API — Fornecedor {cnpj}]\n{json.dumps(resultado, ensure_ascii=False, default=str)[:2000]}")
        elif acao == "buscar_fornecedores":
            pass  # Requer CNAE específico; tratado via chat interativo
        elif acao == "buscar_precos":
            palavras = re.sub(r"[^\w\s]", "", msg).strip()
            resultado = buscar_precos_mercado(palavras)
            partes.append(f"[API — Preços de mercado]\n{json.dumps(resultado, ensure_ascii=False, default=str)[:2000]}")
    return "\n\n".join(partes)


# ============================================================
# GERAÇÃO DE DOCUMENTOS
# ============================================================

def _sanitize_for_pdf(text: str) -> str:
    """Remove/substitui caracteres que não são suportados pela fonte Helvetica (Latin-1)."""
    replacements = {
        "\u2013": "-", "\u2014": "-", "\u2015": "-",  # en-dash, em-dash
        "\u2018": "'", "\u2019": "'",  # aspas simples curvas
        "\u201c": '"', "\u201d": '"',  # aspas duplas curvas
        "\u2022": "-",  # bullet
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",  # non-breaking space
        "\u200b": "",  # zero-width space
        "\u2010": "-", "\u2011": "-",  # hyphens
        "\u2212": "-",  # minus sign
        "\u2264": "<=", "\u2265": ">=",  # comparison
        "\u00b0": "o",  # degree -> o (nº)
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove emojis and other non-Latin-1 characters
    cleaned = []
    for ch in text:
        try:
            ch.encode("latin-1")
            cleaned.append(ch)
        except UnicodeEncodeError:
            cleaned.append(" ")
    return "".join(cleaned)


def gerar_pdf_documento(titulo: str, corpo: str) -> bytes:
    """Gera um PDF simples com título e corpo."""
    titulo = _sanitize_for_pdf(titulo)
    corpo = _sanitize_for_pdf(corpo)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    # Título
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 26, 77)
    pdf.cell(0, 12, titulo, ln=True, align="C")
    pdf.ln(4)
    pdf.set_draw_color(212, 175, 55)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)
    # Data
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="R")
    pdf.ln(4)
    # Corpo
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(30, 30, 30)
    for linha in corpo.split("\n"):
        if linha.startswith("## "):
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 7, linha.replace("## ", ""))
            pdf.set_font("Helvetica", "", 11)
        elif linha.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, linha.replace("### ", ""))
            pdf.set_font("Helvetica", "", 11)
        elif linha.strip().startswith("- "):
            pdf.multi_cell(0, 6, f"  \u2022 {linha.strip()[2:]}")
        elif linha.strip() == "":
            pdf.ln(3)
        else:
            pdf.multi_cell(0, 6, linha)
    return bytes(pdf.output())


TEMPLATE_DFD = """## DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA (DFD)

### 1. Identificação do Requisitante
- Órgão/Entidade: {orgao}
- Setor Requisitante: {setor}
- Responsável: {responsavel}

### 2. Descrição da Necessidade
{necessidade}

### 3. Justificativa da Necessidade
{justificativa}

### 4. Quantidade Estimada
{quantidade}

### 5. Previsão de Data
- Data desejada para contratação: {data_prevista}

### 6. Grau de Prioridade
{prioridade}

### 7. Vinculação ao Plano de Contratações Anual (PCA)
{vinculacao_pca}

### 8. Base Legal
- Lei 14.133/2021, Art. 72, §1°
- IN SEGES/ME nº 58/2022

---
Documento gerado pelo sistema O Babilaca (IA) — Ferramenta de apoio.
Confirmar sempre nas fontes oficiais.
"""

TEMPLATE_TR = """## TERMO DE REFERÊNCIA

### 1. Objeto
{objeto}

### 2. Justificativa da Contratação
{justificativa}

### 3. Descrição Detalhada / Especificações
{especificacoes}

### 4. Quantidades e Unidades
{quantidades}

### 5. Valor Estimado
{valor_estimado}

### 6. Condições de Entrega / Execução
{condicoes_entrega}

### 7. Prazo de Execução / Vigência
{prazo}

### 8. Condições de Pagamento
{pagamento}

### 9. Critério de Julgamento
{criterio_julgamento}

### 10. Penalidades
Conforme previsto na Lei 14.133/2021, Arts. 155 a 163.

### 11. Base Legal
- Lei 14.133/2021
- IN SEGES/ME nº 65/2021

---
Documento gerado pelo sistema O Babilaca (IA) — Ferramenta de apoio.
Confirmar sempre nas fontes oficiais.
"""

TEMPLATE_JUSTIFICATIVA = """## JUSTIFICATIVA DE CONTRATAÇÃO

### 1. Contextualização
{contexto}

### 2. Necessidade da Contratação
{necessidade}

### 3. Análise de Mercado
{analise_mercado}

### 4. Justificativa do Preço
{justificativa_preco}

### 5. Modalidade Sugerida
{modalidade}

### 6. Fundamentação Legal
{fundamentacao}

### 7. Conclusão
{conclusao}

---
Documento gerado pelo sistema O Babilaca (IA) — Ferramenta de apoio.
Confirmar sempre nas fontes oficiais.
"""


def gerar_mapa_comparativo_pdf(itens: list[dict]) -> bytes:
    """Gera PDF de mapa comparativo de preços."""
    pdf = FPDF("L")  # Paisagem
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 26, 77)
    pdf.cell(0, 10, _sanitize_for_pdf("MAPA COMPARATIVO DE PRECOS"), ln=True, align="C")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="R")
    pdf.ln(4)

    # Cabeçalho da tabela
    pdf.set_fill_color(0, 26, 77)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    colunas = ["Item", "Descrição", "Forn. 1", "Forn. 2", "Forn. 3", "Média", "Mediana"]
    larguras = [12, 70, 35, 35, 35, 35, 35]
    for col, larg in zip(colunas, larguras):
        pdf.cell(larg, 8, col, border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "", 9)
    for i, item in enumerate(itens, 1):
        precos = [item.get("preco1", 0), item.get("preco2", 0), item.get("preco3", 0)]
        validos = [p for p in precos if p > 0]
        media = sum(validos) / len(validos) if validos else 0
        mediana = sorted(validos)[len(validos) // 2] if validos else 0
        pdf.cell(12, 7, str(i), border=1, align="C")
        pdf.cell(70, 7, _sanitize_for_pdf(str(item.get("descricao", ""))[:45]), border=1)
        for p in precos:
            pdf.cell(35, 7, f"R$ {p:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if p else "-", border=1, align="R")
        pdf.cell(35, 7, f"R$ {media:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if media else "-", border=1, align="R")
        pdf.cell(35, 7, f"R$ {mediana:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if mediana else "-", border=1, align="R")
        pdf.ln()

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, _sanitize_for_pdf("Documento gerado pelo sistema O Babilaca (IA) - Ferramenta de apoio. Confirmar sempre nas fontes oficiais."), ln=True)
    return bytes(pdf.output())


# ============================================================
# ANÁLISE INTELIGENTE
# ============================================================

def analisar_sobrepreco(precos: list[float], valor_referencia: float) -> dict:
    """Detecta possível sobrepreço comparando com média/mediana."""
    if not precos:
        return {"analise": "Dados insuficientes para análise."}
    media = sum(precos) / len(precos)
    mediana = sorted(precos)[len(precos) // 2]
    desvio_media = ((valor_referencia - media) / media * 100) if media else 0
    desvio_mediana = ((valor_referencia - mediana) / mediana * 100) if mediana else 0
    if desvio_mediana > 30:
        risco = "🔴 ALTO"
        msg = "Valor significativamente acima da mediana de mercado."
    elif desvio_mediana > 15:
        risco = "🟡 MÉDIO"
        msg = "Valor acima da mediana. Recomenda-se justificativa detalhada."
    elif desvio_mediana > 0:
        risco = "🟢 BAIXO"
        msg = "Valor ligeiramente acima da mediana, dentro da faixa aceitável."
    else:
        risco = "🟢 OK"
        msg = "Valor igual ou abaixo da mediana de mercado."
    return {
        "risco": risco,
        "mensagem": msg,
        "media": media,
        "mediana": mediana,
        "desvio_media_pct": round(desvio_media, 2),
        "desvio_mediana_pct": round(desvio_mediana, 2),
        "valor_referencia": valor_referencia,
    }


def classificar_risco_juridico(descricao_cenario: str) -> str:
    """Usa IA para classificar o risco jurídico de um cenário."""
    prompt_risco = (
        "Analise o cenário de contratação pública abaixo e classifique o risco jurídico "
        "em BAIXO, MÉDIO ou ALTO. Justifique com base na Lei 14.133/2021 e jurisprudência do TCU.\n\n"
        f"CENÁRIO: {descricao_cenario}"
    )
    ctx = buscar_base_juridica(descricao_cenario)
    system = _build_system_prompt(ctx)
    return chamar_ia([{"role": "user", "content": prompt_risco}], system)


# ============================================================
# SISTEMA DE ALERTAS
# ============================================================

def verificar_alertas(palavras_chave: list[str] | None = None) -> list[dict]:
    """Verifica alertas proativos consultando APIs."""
    alertas = []
    # 1. Novas licitações
    if palavras_chave:
        for kw in palavras_chave[:3]:
            res = buscar_licitacoes(kw)
            if res.get("sucesso"):
                dados = res["dados"]
                qtd = len(dados) if isinstance(dados, list) else len(dados.get("data", [])) if isinstance(dados, dict) else 0
                if qtd > 0:
                    alertas.append({
                        "tipo": "info",
                        "titulo": f"Novas licitações: '{kw}'",
                        "descricao": f"Encontradas {qtd} licitação(ões) nos últimos 90 dias.",
                        "data": datetime.now().isoformat(),
                    })
    # 2. Alerta padrão de legislação
    alertas.append({
        "tipo": "info",
        "titulo": "Atualização legislativa",
        "descricao": (
            "Verifique regularmente o Portal Nacional de Contratações Públicas (PNCP) "
            "e o DOU para atualizações na regulamentação da Lei 14.133/2021."
        ),
        "data": datetime.now().isoformat(),
    })
    return alertas


# ============================================================
# SISTEMA DE MEMÓRIA
# ============================================================

def carregar_memoria() -> dict:
    if os.path.exists(MEMORIA_PATH):
        try:
            with open(MEMORIA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"preferencias": {}, "respostas_salvas": [], "alertas_palavras": []}


def salvar_memoria(dados: dict):
    try:
        with open(MEMORIA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def salvar_resposta(pergunta: str, resposta: str):
    mem = carregar_memoria()
    mem["respostas_salvas"].append({
        "pergunta": pergunta,
        "resposta": resposta,
        "data": datetime.now().isoformat(),
    })
    salvar_memoria(mem)


# ============================================================
# SIDEBAR — Navegação customizada (padrão do projeto)
# ============================================================
_acanto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Projeto Adesões", "acanto.png")
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

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="babilaca-header">
    <h1>🧠 O Babilaca (IA)</h1>
    <p>Assistente Inteligente para Licitações e Contratações Públicas — Lei 14.133/2021</p>
</div>
<div class="disclaimer-box">
    ⚠️ Ferramenta de apoio. Confirmar sempre nas fontes oficiais.
</div>
""", unsafe_allow_html=True)

# ============================================================
# ABAS PRINCIPAIS
# ============================================================
tab_chat, tab_docs, tab_consultas = st.tabs([
    "💬 Chat IA",
    "📄 Documentos",
    "🔍 Consultas (APIs)",
])

# ============================================================
# TAB 1 — CHAT IA
# ============================================================
with tab_chat:
    st.markdown("### 💬 Converse com o Babilaca")

    # Barra de ferramentas: Modelo | Limpar conversa | Anexar arquivo | Base de conhecimento
    tb_col1, tb_col2, tb_col3, tb_col4 = st.columns([3, 1.3, 1.3, 1.3])
    with tb_col1:
        modelo_nome = st.selectbox(
            "Modelo de IA",
            list(MODELOS_DISPONIVEIS.keys()),
            index=list(MODELOS_DISPONIVEIS.values()).index(st.session_state["babilaca_modelo"])
            if st.session_state["babilaca_modelo"] in MODELOS_DISPONIVEIS.values()
            else 0,
            key="toolbar_modelo",
            label_visibility="collapsed",
        )
        st.session_state["babilaca_modelo"] = MODELOS_DISPONIVEIS[modelo_nome]
    with tb_col2:
        if st.button("🗑️ Limpar conversa", use_container_width=True):
            st.session_state["babilaca_messages"] = []
            st.rerun()
    with tb_col3:
        arquivo_chat = st.file_uploader(
            "📎 Anexar",
            type=["pdf", "xlsx", "xls", "csv"],
            key="chat_upload",
            label_visibility="collapsed",
        )
    with tb_col4:
        with st.popover("📚 Base de Conhecimento", use_container_width=True):
            # Organizar fontes por categoria
            _leis = []
            _ins = []
            _acordaos = []
            for _item in BASE_JURIDICA:
                _f = _item["fonte"]
                _a = _item.get("artigo", "")
                _t = _item["titulo"]
                _lk = _item["link"]
                _label = f"{_f} — {_a}" if _a else _f
                if "Lei 14.133" in _f:
                    _leis.append((_label, _t, _lk))
                elif "IN " in _f:
                    _ins.append((_label, _t, _lk))
                elif "TCU" in _f:
                    _acordaos.append((_label, _t, _lk))
            st.markdown(f"**{len(BASE_JURIDICA)} fontes verificadas**")
            st.markdown("---")
            st.markdown(f"##### ⚖️ Lei 14.133/2021 ({len(_leis)} artigos)")
            for _lb, _tt, _lk in _leis:
                st.markdown(f"- [{_lb}]({_lk}) — {_tt}")
            st.markdown(f"##### 📋 Instruções Normativas ({len(_ins)} dispositivos)")
            for _lb, _tt, _lk in _ins:
                st.markdown(f"- [{_lb}]({_lk}) — {_tt}")
            st.markdown(f"##### 🏛️ Acórdãos TCU ({len(_acordaos)} acórdãos)")
            for _lb, _tt, _lk in _acordaos:
                st.markdown(f"- [{_lb}]({_lk}) — {_tt}")

    texto_arquivo = ""
    if arquivo_chat:
        if arquivo_chat.name.endswith(".pdf"):
            texto_arquivo = extrair_texto_pdf(arquivo_chat)
            st.success(f"PDF processado: {len(texto_arquivo)} caracteres extraídos.")
        elif arquivo_chat.name.endswith((".xlsx", ".xls")):
            texto_arquivo, _ = extrair_dados_excel(arquivo_chat)
            st.success("Planilha processada.")
        elif arquivo_chat.name.endswith(".csv"):
            try:
                df_csv = pd.read_csv(arquivo_chat)
                texto_arquivo = f"CSV com {len(df_csv)} linhas.\nColunas: {', '.join(df_csv.columns)}\n{df_csv.head(10).to_string()}"
                st.success("CSV processado.")
            except Exception as e:
                texto_arquivo = f"[Erro ao ler CSV: {e}]"

    # Histórico de mensagens
    for msg in st.session_state["babilaca_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input do usuário
    if prompt := st.chat_input("Digite sua pergunta sobre licitações, legislação ou contratações..."):
        # Adicionar mensagem do usuário
        st.session_state["babilaca_messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🧠 Pensando..."):
                # 1. Buscar contexto jurídico
                contexto = buscar_base_juridica(prompt)

                # 2. Analisar intenção e chamar APIs
                acoes = analisar_intencao(prompt)
                dados_api = ""
                if acoes:
                    dados_api = executar_apis(prompt, acoes)

                # 3. Contexto de arquivo (se houver)
                if texto_arquivo:
                    dados_api += f"\n\n[ARQUIVO ENVIADO PELO USUÁRIO]\n{texto_arquivo[:3000]}"

                # 4. Montar system prompt
                system = _build_system_prompt(contexto, dados_api)

                # 5. Preparar histórico (últimas 20 mensagens)
                historico = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state["babilaca_messages"][-20:]
                ]

                # 6. Chamar IA
                resposta = chamar_ia(historico, system)

            st.markdown(resposta)

            # Botão salvar resposta
            if st.button("💾 Salvar resposta", key=f"save_{len(st.session_state['babilaca_messages'])}"):
                salvar_resposta(prompt, resposta)
                st.toast("Resposta salva na memória!")

        st.session_state["babilaca_messages"].append({"role": "assistant", "content": resposta})

# ============================================================
# TAB 2 — DOCUMENTOS
# ============================================================
with tab_docs:
    st.markdown("### 📄 Geração de Documentos Administrativos")

    col_doc1, col_doc2 = st.columns(2)
    with col_doc1:
        st.markdown("""
        <div class="doc-card">
            <h4>📋 DFD</h4>
            <p>Documento de Formalização de Demanda — IN 58/2022</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="doc-card">
            <h4>📑 Termo de Referência</h4>
            <p>Documento com especificações para contratação — Lei 14.133, Art. 6°</p>
        </div>
        """, unsafe_allow_html=True)
    with col_doc2:
        st.markdown("""
        <div class="doc-card">
            <h4>📝 Justificativa</h4>
            <p>Justificativa de contratação com base legal</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="doc-card">
            <h4>📊 Mapa Comparativo</h4>
            <p>Comparativo de preços entre fornecedores</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    tipo_doc = st.selectbox(
        "Selecione o tipo de documento",
        ["DFD — Documento de Formalização de Demanda",
         "Termo de Referência",
         "Justificativa de Contratação",
         "Mapa Comparativo de Preços"],
    )

    # ---- DFD ----
    if "DFD" in tipo_doc:
        st.markdown("#### 📋 Gerar DFD")
        modo_dfd = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_dfd")

        if modo_dfd == "Manual":
            with st.form("form_dfd"):
                c1, c2 = st.columns(2)
                with c1:
                    orgao = st.text_input("Órgão/Entidade")
                    setor = st.text_input("Setor Requisitante")
                    responsavel = st.text_input("Responsável")
                with c2:
                    data_prevista = st.date_input("Data prevista")
                    prioridade = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
                necessidade = st.text_area("Descrição da necessidade", height=100)
                justificativa = st.text_area("Justificativa", height=100)
                quantidade = st.text_input("Quantidade estimada")
                vinculacao = st.text_input("Vinculação ao PCA (se houver)")
                submit_dfd = st.form_submit_button("📄 Gerar DFD", use_container_width=True)

            if submit_dfd:
                corpo = TEMPLATE_DFD.format(
                    orgao=orgao, setor=setor, responsavel=responsavel,
                    necessidade=necessidade, justificativa=justificativa,
                    quantidade=quantidade, data_prevista=data_prevista.strftime("%d/%m/%Y"),
                    prioridade=prioridade, vinculacao_pca=vinculacao or "Não informado",
                )
                st.markdown(corpo)
                pdf_bytes = gerar_pdf_documento("DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA (DFD)", corpo)
                st.download_button("⬇️ Baixar DFD em PDF", pdf_bytes, "dfd.pdf", "application/pdf")
        else:
            desc_ia = st.text_area(
                "Descreva brevemente a necessidade de contratação e o Babilaca preencherá o DFD:",
                height=120,
                key="dfd_ia_input",
            )
            if st.button("🤖 Gerar DFD com IA", key="btn_dfd_ia"):
                if desc_ia:
                    with st.spinner("Gerando DFD com IA..."):
                        prompt_dfd = (
                            f"Gere um Documento de Formalização de Demanda (DFD) completo, "
                            f"seguindo a IN SEGES/ME nº 58/2022, para a seguinte necessidade:\n\n"
                            f"{desc_ia}\n\n"
                            f"Use o formato com seções: Identificação, Necessidade, Justificativa, "
                            f"Quantidade, Previsão de Data, Prioridade, Vinculação ao PCA."
                        )
                        ctx = buscar_base_juridica("DFD formalização demanda planejamento")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_dfd}], system)
                    st.markdown(resultado)
                    pdf_bytes = gerar_pdf_documento("DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA (DFD)", resultado)
                    st.download_button("⬇️ Baixar DFD em PDF", pdf_bytes, "dfd_ia.pdf", "application/pdf")
                else:
                    st.warning("Descreva a necessidade antes de gerar.")

    # ---- TERMO DE REFERÊNCIA ----
    elif "Termo de Referência" in tipo_doc:
        st.markdown("#### 📑 Gerar Termo de Referência")
        modo_tr = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_tr")

        if modo_tr == "Manual":
            with st.form("form_tr"):
                objeto = st.text_area("Objeto da contratação", height=80)
                justificativa = st.text_area("Justificativa", height=80)
                especificacoes = st.text_area("Especificações técnicas", height=100)
                quantidades = st.text_input("Quantidades e unidades")
                valor_estimado = st.text_input("Valor estimado (R$)")
                condicoes = st.text_area("Condições de entrega/execução", height=60)
                prazo = st.text_input("Prazo de execução/vigência")
                pagamento = st.text_input("Condições de pagamento")
                criterio = st.selectbox("Critério de julgamento",
                    ["Menor preço", "Melhor técnica", "Técnica e preço", "Maior desconto", "Maior retorno econômico"])
                submit_tr = st.form_submit_button("📄 Gerar Termo de Referência", use_container_width=True)

            if submit_tr:
                corpo = TEMPLATE_TR.format(
                    objeto=objeto, justificativa=justificativa, especificacoes=especificacoes,
                    quantidades=quantidades, valor_estimado=valor_estimado,
                    condicoes_entrega=condicoes, prazo=prazo, pagamento=pagamento,
                    criterio_julgamento=criterio,
                )
                st.markdown(corpo)
                pdf_bytes = gerar_pdf_documento("TERMO DE REFERÊNCIA", corpo)
                st.download_button("⬇️ Baixar TR em PDF", pdf_bytes, "termo_referencia.pdf", "application/pdf")
        else:
            desc_tr = st.text_area(
                "Descreva o que precisa contratar e o Babilaca elaborará o Termo de Referência:",
                height=120,
                key="tr_ia_input",
            )
            arquivo_tr = st.file_uploader("Ou envie um arquivo com especificações (PDF/Excel)", type=["pdf", "xlsx"], key="tr_upload")
            if st.button("🤖 Gerar TR com IA", key="btn_tr_ia"):
                ctx_extra = ""
                if arquivo_tr:
                    if arquivo_tr.name.endswith(".pdf"):
                        ctx_extra = extrair_texto_pdf(arquivo_tr)
                    else:
                        ctx_extra, _ = extrair_dados_excel(arquivo_tr)
                if desc_tr or ctx_extra:
                    with st.spinner("Gerando Termo de Referência..."):
                        prompt_tr = (
                            f"Gere um Termo de Referência completo conforme a Lei 14.133/2021 "
                            f"para a seguinte contratação:\n\n{desc_tr}\n\n"
                        )
                        if ctx_extra:
                            prompt_tr += f"Dados adicionais do arquivo:\n{ctx_extra[:3000]}\n\n"
                        prompt_tr += (
                            "Inclua: Objeto, Justificativa, Especificações, Quantidades, "
                            "Valor Estimado, Condições de Entrega, Prazo, Pagamento, "
                            "Critério de Julgamento, Penalidades, Base Legal."
                        )
                        ctx = buscar_base_juridica("termo de referência contratação especificação")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_tr}], system)
                    st.markdown(resultado)
                    pdf_bytes = gerar_pdf_documento("TERMO DE REFERÊNCIA", resultado)
                    st.download_button("⬇️ Baixar TR em PDF", pdf_bytes, "tr_ia.pdf", "application/pdf")
                else:
                    st.warning("Forneça uma descrição ou envie um arquivo.")

    # ---- JUSTIFICATIVA ----
    elif "Justificativa" in tipo_doc:
        st.markdown("#### 📝 Gerar Justificativa de Contratação")
        modo_just = st.radio("Modo", ["Manual", "Assistido por IA"], horizontal=True, key="modo_just")

        if modo_just == "Manual":
            with st.form("form_just"):
                contexto = st.text_area("Contextualização", height=80)
                necessidade = st.text_area("Necessidade da contratação", height=80)
                analise = st.text_area("Análise de mercado", height=80)
                just_preco = st.text_area("Justificativa do preço", height=60)
                modalidade = st.selectbox("Modalidade sugerida",
                    ["Pregão Eletrônico", "Concorrência", "Dispensa de Licitação",
                     "Inexigibilidade", "Adesão a Ata de Registro de Preços"])
                fundamentacao = st.text_area("Fundamentação legal", height=60)
                conclusao = st.text_area("Conclusão", height=60)
                submit_j = st.form_submit_button("📄 Gerar Justificativa", use_container_width=True)

            if submit_j:
                corpo = TEMPLATE_JUSTIFICATIVA.format(
                    contexto=contexto, necessidade=necessidade, analise_mercado=analise,
                    justificativa_preco=just_preco, modalidade=modalidade,
                    fundamentacao=fundamentacao, conclusao=conclusao,
                )
                st.markdown(corpo)
                pdf_bytes = gerar_pdf_documento("JUSTIFICATIVA DE CONTRATAÇÃO", corpo)
                st.download_button("⬇️ Baixar Justificativa em PDF", pdf_bytes, "justificativa.pdf", "application/pdf")
        else:
            desc_just = st.text_area(
                "Descreva a contratação que precisa justificar:",
                height=120,
                key="just_ia_input",
            )
            if st.button("🤖 Gerar Justificativa com IA", key="btn_just_ia"):
                if desc_just:
                    with st.spinner("Gerando justificativa..."):
                        prompt_just = (
                            f"Gere uma Justificativa de Contratação completa baseada na Lei 14.133/2021 "
                            f"para o seguinte cenário:\n\n{desc_just}\n\n"
                            f"Inclua: Contextualização, Necessidade, Análise de Mercado, "
                            f"Justificativa de Preço, Modalidade Sugerida, Fundamentação Legal, Conclusão."
                        )
                        ctx = buscar_base_juridica("justificativa contratação dispensa modalidade")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_just}], system)
                    st.markdown(resultado)
                    pdf_bytes = gerar_pdf_documento("JUSTIFICATIVA DE CONTRATAÇÃO", resultado)
                    st.download_button("⬇️ Baixar em PDF", pdf_bytes, "justificativa_ia.pdf", "application/pdf")
                else:
                    st.warning("Descreva o cenário.")

    # ---- MAPA COMPARATIVO ----
    elif "Mapa Comparativo" in tipo_doc:
        st.markdown("#### 📊 Mapa Comparativo de Preços")
        modo_mapa = st.radio("Modo", ["Manual", "Via Arquivo"], horizontal=True, key="modo_mapa")

        if modo_mapa == "Manual":
            n_itens = st.number_input("Número de itens", min_value=1, max_value=50, value=3, key="n_itens_mapa")
            itens_mapa = []
            for i in range(int(n_itens)):
                st.markdown(f"**Item {i + 1}**")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    desc = st.text_input(f"Descrição", key=f"mapa_desc_{i}")
                with c2:
                    p1 = st.number_input(f"Fornecedor 1 (R$)", min_value=0.0, format="%.2f", key=f"mapa_p1_{i}")
                with c3:
                    p2 = st.number_input(f"Fornecedor 2 (R$)", min_value=0.0, format="%.2f", key=f"mapa_p2_{i}")
                with c4:
                    p3 = st.number_input(f"Fornecedor 3 (R$)", min_value=0.0, format="%.2f", key=f"mapa_p3_{i}")
                itens_mapa.append({"descricao": desc, "preco1": p1, "preco2": p2, "preco3": p3})

            if st.button("📊 Gerar Mapa Comparativo", key="btn_mapa"):
                pdf_bytes = gerar_mapa_comparativo_pdf(itens_mapa)
                st.download_button("⬇️ Baixar Mapa em PDF", pdf_bytes, "mapa_comparativo.pdf", "application/pdf")

                # Mostrar tabela na tela
                rows = []
                for i, item in enumerate(itens_mapa, 1):
                    precos = [item["preco1"], item["preco2"], item["preco3"]]
                    validos = [p for p in precos if p > 0]
                    rows.append({
                        "Item": i,
                        "Descrição": item["descricao"],
                        "Forn. 1": f"R$ {item['preco1']:,.2f}",
                        "Forn. 2": f"R$ {item['preco2']:,.2f}",
                        "Forn. 3": f"R$ {item['preco3']:,.2f}",
                        "Média": f"R$ {sum(validos)/len(validos):,.2f}" if validos else "-",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            arq_mapa = st.file_uploader("Envie planilha com itens e preços", type=["xlsx", "xls", "csv"], key="mapa_upload")
            if arq_mapa:
                try:
                    if arq_mapa.name.endswith(".csv"):
                        df_m = pd.read_csv(arq_mapa)
                    else:
                        df_m = pd.read_excel(arq_mapa)
                    st.dataframe(df_m, use_container_width=True)
                    st.info("Revise os dados acima. O sistema tentará identificar colunas de descrição e preços.")
                    if st.button("📊 Gerar Mapa a partir da planilha", key="btn_mapa_arq"):
                        itens_arq = []
                        desc_col = None
                        for c in df_m.columns:
                            if any(k in c.lower() for k in ["desc", "item", "produto", "material", "objeto"]):
                                desc_col = c
                                break
                        if not desc_col:
                            desc_col = df_m.columns[0]
                        preco_cols = [c for c in df_m.columns if any(k in c.lower() for k in ["preco", "preço", "valor", "forn", "cota"])]
                        if not preco_cols:
                            preco_cols = [c for c in df_m.columns if df_m[c].dtype in ["float64", "int64"]]
                        for _, row in df_m.iterrows():
                            item = {"descricao": str(row[desc_col])}
                            for j, pc in enumerate(preco_cols[:3], 1):
                                try:
                                    item[f"preco{j}"] = float(row[pc])
                                except (ValueError, TypeError):
                                    item[f"preco{j}"] = 0
                            for j in range(len(preco_cols) + 1, 4):
                                item[f"preco{j}"] = 0
                            itens_arq.append(item)
                        if itens_arq:
                            pdf_bytes = gerar_mapa_comparativo_pdf(itens_arq)
                            st.download_button("⬇️ Baixar Mapa em PDF", pdf_bytes, "mapa_comparativo.pdf", "application/pdf")
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")

# ============================================================
# TAB 3 — CONSULTAS (APIs)
# ============================================================
with tab_consultas:
    st.markdown("### 🔍 Consultas em APIs Públicas")

    tipo_consulta = st.selectbox(
        "Tipo de consulta",
        ["Buscar Licitações (PNCP)", "Buscar Atas de Registro de Preços",
         "Consultar Fornecedor (CNPJ)", "Buscar Preços de Mercado",
         "Análise de Sobrepreço", "Classificação de Risco Jurídico"],
    )

    # ---- Licitações ----
    if "Licitações" in tipo_consulta:
        st.markdown("#### 🏛️ Buscar Licitações no PNCP")
        kw_lic = st.text_input("Palavra-chave", key="kw_lic")
        if st.button("🔍 Buscar", key="btn_lic"):
            if kw_lic:
                with st.spinner("Consultando PNCP..."):
                    res = buscar_licitacoes(kw_lic)
                if res.get("sucesso"):
                    st.success(f"Fonte: {res['fonte']}")
                    dados = res["dados"]
                    if isinstance(dados, dict):
                        dados_lista = dados.get("data", dados.get("resultado", []))
                    elif isinstance(dados, list):
                        dados_lista = dados
                    else:
                        dados_lista = []
                    if dados_lista:
                        st.json(dados_lista[:5])
                    else:
                        st.info("Nenhum resultado encontrado para o período.")
                else:
                    st.error(f"Erro: {res.get('erro')}")
            else:
                st.warning("Digite uma palavra-chave.")

    # ---- Atas ----
    elif "Atas" in tipo_consulta:
        st.markdown("#### 📋 Buscar Atas de Registro de Preços")
        desc_ata = st.text_input("Descrição do item", key="desc_ata")
        cod_ata = st.text_input("Código do item no catálogo (opcional)", key="cod_ata")
        if st.button("🔍 Buscar Atas", key="btn_ata"):
            with st.spinner("Consultando ComprasGov..."):
                res = buscar_atas(item_codigo=cod_ata, descricao=desc_ata)
            if res.get("sucesso"):
                st.success(f"Fonte: {res['fonte']}")
                dados = res["dados"]
                if isinstance(dados, dict):
                    dados_lista = dados.get("resultado", dados.get("data", []))
                elif isinstance(dados, list):
                    dados_lista = dados
                else:
                    dados_lista = []
                if dados_lista:
                    try:
                        df_atas = pd.json_normalize(dados_lista[:20])
                        st.dataframe(df_atas, use_container_width=True)
                    except Exception:
                        st.json(dados_lista[:5])
                else:
                    st.info("Nenhuma ata encontrada.")
            else:
                st.error(f"Erro: {res.get('erro')}")

    # ---- Fornecedor ----
    elif "Fornecedor" in tipo_consulta:
        st.markdown("#### 🏢 Consultar Fornecedor por CNPJ")
        cnpj_input = st.text_input("CNPJ", placeholder="00.000.000/0000-00", key="cnpj_cons")
        if st.button("🔍 Consultar", key="btn_cnpj"):
            if cnpj_input:
                with st.spinner("Consultando..."):
                    res = consultar_fornecedor(cnpj_input)
                if res.get("sucesso"):
                    st.success(f"Fonte: {res['fonte']}")
                    dados = res["dados"]
                    # Exibir informações principais
                    nome = dados.get("razao_social") or dados.get("razaoSocial") or dados.get("nome") or "N/I"
                    fantasia = dados.get("nome_fantasia") or dados.get("nomeFantasia") or ""
                    situacao = dados.get("situacao_cadastral") or dados.get("descricaoSituacaoCadastral") or ""
                    st.markdown(f"**{nome}**")
                    if fantasia:
                        st.markdown(f"Nome fantasia: {fantasia}")
                    st.markdown(f"Situação: {situacao}")
                    with st.expander("Ver dados completos"):
                        st.json(dados)
                else:
                    st.error(res.get("erro", "Erro na consulta."))
            else:
                st.warning("Digite um CNPJ.")

    # ---- Preços de Mercado ----
    elif "Preços" in tipo_consulta:
        st.markdown("#### 💰 Buscar Preços de Mercado")
        desc_preco = st.text_input("Descrição do item", key="desc_preco")
        if st.button("🔍 Buscar Preços", key="btn_preco"):
            if desc_preco:
                with st.spinner("Buscando preços..."):
                    res = buscar_precos_mercado(desc_preco)
                if res.get("sucesso"):
                    st.success(f"Fonte: {res['fonte']} — {res['quantidade']} preço(s) encontrado(s)")
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        st.markdown(f"""<div class="stat-card"><div class="valor">R$ {res['menor']:,.2f}</div><div class="label">Menor</div></div>""", unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""<div class="stat-card"><div class="valor">R$ {res['media']:,.2f}</div><div class="label">Média</div></div>""", unsafe_allow_html=True)
                    with c3:
                        st.markdown(f"""<div class="stat-card"><div class="valor">R$ {res['mediana']:,.2f}</div><div class="label">Mediana</div></div>""", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"""<div class="stat-card"><div class="valor">R$ {res['maior']:,.2f}</div><div class="label">Maior</div></div>""", unsafe_allow_html=True)
                    if res.get("precos"):
                        st.bar_chart(pd.DataFrame({"Preços (R$)": res["precos"]}))
                else:
                    st.warning(res.get("erro", "Nenhum preço encontrado."))
            else:
                st.warning("Digite a descrição do item.")

    # ---- Análise de Sobrepreço ----
    elif "Sobrepreço" in tipo_consulta:
        st.markdown("#### 🔎 Análise de Sobrepreço")
        st.caption("Compare o valor proposto com preços de mercado para identificar possível sobrepreço.")
        c1, c2 = st.columns(2)
        with c1:
            valor_ref = st.number_input("Valor proposto (R$)", min_value=0.0, format="%.2f", key="val_ref")
        with c2:
            desc_item_sp = st.text_input("Descrição do item para comparação", key="desc_sp")
        if st.button("🔎 Analisar Sobrepreço", key="btn_sp"):
            if valor_ref > 0 and desc_item_sp:
                with st.spinner("Buscando preços de mercado..."):
                    res = buscar_precos_mercado(desc_item_sp)
                if res.get("sucesso") and res.get("precos"):
                    analise = analisar_sobrepreco(res["precos"], valor_ref)
                    st.markdown(f"### Resultado: {analise['risco']}")
                    st.markdown(f"**{analise['mensagem']}**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.metric("Média de mercado", f"R$ {analise['media']:,.2f}")
                    with c2:
                        st.metric("Mediana de mercado", f"R$ {analise['mediana']:,.2f}")
                    with c3:
                        st.metric("Desvio da mediana", f"{analise['desvio_mediana_pct']}%")
                else:
                    st.warning("Não foi possível encontrar preços de mercado para comparação.")
            else:
                st.warning("Preencha o valor e a descrição do item.")

    # ---- Risco Jurídico ----
    elif "Risco" in tipo_consulta:
        st.markdown("#### ⚖️ Classificação de Risco Jurídico")
        cenario = st.text_area(
            "Descreva o cenário de contratação para análise de risco:",
            height=120,
            key="cenario_risco",
        )
        if st.button("⚖️ Analisar Risco", key="btn_risco"):
            if cenario:
                with st.spinner("Analisando risco jurídico..."):
                    resultado = classificar_risco_juridico(cenario)
                st.markdown(resultado)
            else:
                st.warning("Descreva o cenário.")

    # ---- Checklist de Conformidade ----
    st.markdown("---")
    st.markdown("#### 📋 Checklist de Conformidade")
    st.caption("Verifique se seu processo possui todos os documentos obrigatórios.")
    checklist = [
        "Documento de Formalização de Demanda (DFD)",
        "Estudo Técnico Preliminar (ETP)",
        "Termo de Referência (TR)",
        "Pesquisa de Preços (mínimo 3 fontes)",
        "Justificativa da modalidade de contratação",
        "Análise de riscos",
        "Parecer jurídico",
        "Publicação no PNCP",
    ]
    for item in checklist:
        st.checkbox(item, key=f"check_{hashlib.md5(item.encode()).hexdigest()[:8]}")
