"""Sobre o projeto: o que é o AtaCotada, para que serve, ferramentas, fontes de dados e avisos de uso."""

from __future__ import annotations

import base64
import os

import streamlit as st

st.set_page_config(
    page_title="Sobre o projeto",
    page_icon="ℹ️",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp { background: #001a4d !important; color: #f8fafc; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #ef4444 !important;
        }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebar"] .stMarkdown h2 {
            color: #d4af37 !important; font-family: 'Arial Black', sans-serif; font-size: 22px; text-align: center;
            letter-spacing: 2px; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
            border-bottom: 2px solid #d4af37; padding-bottom: 0.75rem; margin-bottom: 1.5rem;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            background: linear-gradient(135deg, #1a1a1a, #252525) !important;
            border: 1px solid #333 !important; border-radius: 8px !important;
            color: #fff !important; margin: .2rem 0 !important; padding: .45rem .7rem !important;
            font-size: 12.5px !important; font-weight: 600 !important; justify-content: center !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span { color: #fff !important; }
        [data-testid="stSidebar"] hr { border-color: #333 !important; margin: 1rem 0 !important; }
        .sp-header {
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); border-radius: 10px;
            padding: 1.3rem 1.6rem; margin-bottom: 1rem; box-shadow: 0 10px 28px rgba(0, 0, 0, .3);
        }
        .sp-header h1 { color: #fff; margin: 0; font-size: 1.6rem; font-weight: 900; }
        .sp-header p { color: #fee2e2; margin: .3rem 0 0; font-size: .92rem; font-weight: 600; }
        .sp-header p.sp-lead { color: #fff; font-size: 1rem; font-weight: 500; line-height: 1.6; margin-top: .8rem; padding-top: .8rem; border-top: 1px solid rgba(255, 255, 255, .35); }
        .sp-header p.sp-lead b { font-weight: 800; }
        .sp-panel {
            background: rgba(8, 26, 57, .78); border: 1px solid #1e5b9f; border-left: 5px solid #ef4444;
            border-radius: 9px; padding: .9rem 1.1rem; margin: .6rem 0 .9rem;
        }
        .sp-panel h3 { color: #d4af37; font-size: 1.05rem; margin: 0 0 .4rem; }
        .sp-panel p, .sp-panel li { color: #dbe7f7; font-size: .9rem; line-height: 1.55; }
        .sp-panel ul { margin: .3rem 0 0 1.1rem; padding: 0; }
        .sp-prop { background: linear-gradient(135deg, rgba(212, 175, 55, .16), rgba(8, 26, 57, .85)); border: 1px solid #d4af37; border-left: 6px solid #d4af37;
            border-radius: 10px; padding: 1.1rem 1.3rem; margin: .8rem 0 1rem; }
        .sp-prop h3 { color: #d4af37; font-size: 1.15rem; margin: 0 0 .6rem; }
        .sp-prop p { color: #f1f5f9; font-size: .95rem; line-height: 1.65; margin: 0 0 .7rem; }
        .sp-prop .destaque { color: #fff; font-size: 1.05rem; font-weight: 700; border-left: 3px solid #ef4444; padding-left: .8rem; margin: .9rem 0 .2rem; }
        .sp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: .6rem; margin-top: .4rem; }
        .sp-card { background: rgba(0, 26, 77, .7); border: 1px solid #1e5b9f; border-radius: 8px; padding: .65rem .8rem; }
        .sp-card .t { color: #fff; font-weight: 800; font-size: .92rem; }
        .sp-card .d { color: #b6cae2; font-size: .8rem; margin-top: .15rem; line-height: 1.4; }
        .sp-aviso { background: rgba(239, 68, 68, .12); border: 1px solid rgba(239, 68, 68, .45); border-radius: 9px; padding: .8rem 1.1rem; margin: .8rem 0; color: #fecaca; font-size: .88rem; line-height: 1.5; }
        .sp-aviso b { color: #fff; }
        .sidebar-footer { color: #666; font-size: 11px; text-align: center; padding: 1rem 0; border-top: 1px solid #333; margin-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

acanto_path = os.path.join(CATALOGO_DIR, "acanto.png")
if os.path.exists(acanto_path):
    with open(acanto_path, "rb") as arquivo_acanto:
        acanto_b64 = base64.b64encode(arquivo_acanto.read()).decode()
else:
    acanto_b64 = None

with st.sidebar:
    if acanto_b64:
        st.markdown(f'<div style="text-align:center;padding:1rem 0 0.5rem 0;"><img src="data:image/png;base64,{acanto_b64}" style="max-width:70%;height:auto;"></div>', unsafe_allow_html=True)
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
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid],[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#facc15,#eab308)!important;border:1px solid #fde047!important;box-shadow:0 0 14px rgba(250,204,21,.55)!important}[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid] *{background:transparent!important;color:#111!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid],[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#ef4444,#b91c1c)!important;border:1px solid #fca5a5!important;box-shadow:0 0 14px rgba(239,68,68,.55)!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}</style>', unsafe_allow_html=True)

FERRAMENTAS = [
    ("⚓", "Cotação", "Pesquisa de preços praticados de um item de catálogo, com filtros, retirada de valores discrepantes, estatísticas e relatório."),
    ("🔎", "CATMAT/CATSERV", "Sugere o código do catálogo (material ou serviço) a partir das descrições dos itens."),
    ("⚡", "Cotação Rápida", "Cota vários itens de uma vez e monta o mapa comparativo de preços em PDF e Excel."),
    ("📨", "Cotação Direta", "Pede orçamento por e-mail a fornecedores que venderam recentemente, com proposta em Word."),
    ("🔍", "Detalhes Compra", "Consulta os detalhes de uma compra pública."),
    ("🤝", "Adesões", "Localiza atas de registro de preços vigentes para adesão, por estado, com saldos e limites."),
    ("📄", "Notas Fiscais", "Pesquisa preços em notas fiscais eletrônicas dos dados abertos e relaciona as NF-e para autenticação."),
    ("🏢", "Fornecedores", "Lista fornecedores por atividade econômica (CNAE), com contatos."),
    ("💻", "Consulta CNPJ", "Consulta dados cadastrais de empresas pelo CNPJ."),
    ("🕷️", "Web Scraping", "Pesquisa de preços automatizada na internet, com endereço, data/hora e prints de evidência."),
    ("🧠", "O Babilaca (IA)", "Assistente de IA para licitações e legislação, com respostas apoiadas em fontes verificadas."),
    ("📊", "Cálculo IPCA", "Correção monetária de valores pelo IPCA acumulado (série 433 do Banco Central)."),
]

st.markdown(
    """
    <div class="sp-header">
        <h1>ℹ️ Sobre o projeto</h1>
        <p>AtaCotada — um sistema autônomo de apoio à pesquisa de preços e à instrução de processos de contratação.</p>
        <p class="sp-lead">Ele faz a <b>pesquisa de preços por você</b>, monta o <b>mapa comparativo</b>, a <b>memória de cálculo</b> e a <b>justificativa da metodologia</b>,
        encontra e entrega o <b>arquivo de atas para adesão</b> com o material de que você precisa, identifica o <b>CATMAT ideal</b> para cada item e oferece outras funcionalidades.
        Um sistema que <b>aumenta a produtividade</b>, reduzindo <b>semanas de trabalho a minutos</b>.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="sp-panel">
        <h3>O que é</h3>
        <p>O <b>AtaCotada</b> é um sistema web que reúne, num só lugar, ferramentas para <b>pesquisar preços</b>, <b>encontrar códigos de catálogo</b>,
        <b>identificar fornecedores</b>, <b>localizar atas para adesão</b> e <b>gerar relatórios</b> que ajudam a instruir processos de contratação.
        Nasceu no Centro de Operações do Abastecimento da Marinha do Brasil.</p>
        <p>O projeto foi <b>idealizado e desenvolvido pelo 2°SG-PL Freitas</b>, sob a <b>liderança e coordenação do CMG (IM) ROMA</b> e com <b>apoios fundamentais</b>
        do <b>CAlt (IM) Yamaguchi</b>, atual DGOM, e do <b>CAlt (IM) Ricardo Nogueira</b>, atual COpAb. Em <b>2026</b>, foi <b>apresentado, aprovado e elogiado</b>
        pelo <b>DAbM Vice-Alt Viveiros</b>.</p>
    </div>
    <div class="sp-prop">
        <h3>🎯 O propósito do projeto</h3>
        <p>O principal objetivo do <b>2°SG-PL Freitas</b> com o AtaCotada é <b>demonstrar a capacidade das novas tecnologias de aprimorar os processos de trabalho</b>,
        para que outras pessoas se inspirem, aprendam e desenvolvam sistemas e soluções criativas que facilitem a vida de quem trabalha.</p>
        <p>O AtaCotada <b>não tem a pretensão de se tornar um sistema oficial</b>. Enquanto facilita o trabalho dos colegas, ele também mostra aplicações relevantes
        que podem servir de ponto de partida para um sistema oficial, caso a Instituição venha a desenvolver um.</p>
        <p>Contribuir com a missão da Marinha é mais importante do que qualquer reconhecimento ou prêmio. Por isso o projeto é de <b>código aberto</b>,
        <b>público</b> e <b>gratuito</b>: quanto mais gente puder ver, usar e aproveitar a ideia, melhor.</p>
        <p class="destaque">O AtaCotada existe para mostrar que a falta de pessoal pode ser suprida com inteligência, automação e IA.</p>
    </div>
    <div class="sp-panel">
        <h3>Para que serve</h3>
        <ul>
            <li>Reduzir o tempo gasto em <b>consultas manuais</b> e na <b>consolidação de dados</b> em planilhas.</li>
            <li>Transformar informações dispersas (APIs, catálogos, notas fiscais, páginas da internet) em <b>dados estruturados e comparáveis</b>.</li>
            <li>Padronizar a <b>memória da pesquisa de preços</b>: origem, data, estatísticas e evidências de cada valor.</li>
            <li>Apoiar a consulta à <b>legislação</b> aplicável, como a Lei nº 14.133/2021 e a IN SEGES/ME nº 65/2021.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="sp-panel"><h3>Ferramentas do sistema</h3><div class="sp-grid">' + "".join(
    f'<div class="sp-card"><div class="t">{icone} {nome}</div><div class="d">{descricao}</div></div>' for icone, nome, descricao in FERRAMENTAS
) + "</div></div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="sp-panel">
        <h3>De onde vêm os dados</h3>
        <ul>
            <li><b>Compras.gov.br – Dados Abertos</b>: preços praticados, atas de registro de preços, catálogo CATMAT/CATSERV e fornecedores.</li>
            <li><b>PNCP</b> (Portal Nacional de Contratações Públicas): contratações e atas.</li>
            <li><b>Portal da Transparência</b>: arquivos mensais de notas fiscais eletrônicas; a autenticação das notas é feita no <b>Portal da NF-e</b> (Receita Federal).</li>
            <li><b>Banco Central do Brasil / IBGE</b>: IPCA (série 433).</li>
            <li><b>Consultas de CNPJ</b>: OpenCNPJ, BrasilAPI e ReceitaWS, para dados cadastrais e contatos de empresas.</li>
            <li><b>Internet aberta</b>: lojas e sítios eletrônicos pesquisados pelo Web Scraping.</li>
            <li><b>Legislação e jurisprudência</b>: textos da Lei nº 14.133/2021, instruções normativas e acórdãos do TCU usados pelo Babilaca.</li>
        </ul>
    </div>
    <div class="sp-panel">
        <h3>Como o sistema é feito</h3>
        <p>Aplicação em <b>Python</b>, com <b>Streamlit</b> para as telas, <b>pandas</b> para tabelas e estatísticas e geração de relatórios em PDF, Excel e Word,
        publicada na nuvem do Streamlit. O código evolui continuamente: novas ferramentas e ajustes entram com base no uso do dia a dia.</p>
        <p>O <b>Streamlit</b> foi escolhido por ser uma biblioteca <b>muito leve</b>, de <b>fácil implantação</b> e de <b>fácil manutenção</b>: permite evoluir o sistema
        com poucos recursos e, a cada ajuste publicado, todos os usuários passam a usar a nova versão, sem instalar nada.</p>
        <p>Além disso, os dados usados pelo sistema são <b>públicos</b> e são <b>captados e estruturados de forma autônoma</b>: o sistema consulta as fontes, organiza as informações
        em tabelas, calcula e gera os relatórios. Esse fluxo de trabalho, <b>dados, tabela, análise e documento</b>, é justamente o que o Streamlit faz melhor, o que o torna
        a opção <b>mais compatível</b> com o projeto.</p>
    </div>
    <div class="sp-aviso">
        <b>⚠️ Avisos importantes</b>
        <ul style="margin:.3rem 0 0 1.1rem;padding:0">
            <li>O AtaCotada é uma <b>ferramenta de apoio</b>. Ele <b>não substitui</b> a análise e a decisão do agente responsável pela contratação.</li>
            <li>O sistema depende de <b>fontes externas</b> (portais públicos e serviços da internet). Com <b>muitos usuários ao mesmo tempo</b>, ele pode ficar <b>mais lento</b> e, quando alguma dessas fontes estiver fora do ar ou em manutenção, pode ficar <b>temporariamente indisponível</b>. Se isso acontecer, tente novamente em alguns instantes.</li>
            <li>Para aprender a usar cada ferramenta, veja as vídeo-aulas em <b>Aprendendo a usar</b>.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="margin-top:2rem;padding-top:1.4rem;border-top:1px solid #0033cc;text-align:center;">
        <p style="color:#d4af37;font-size:12px;margin:0;letter-spacing:.5px;">Idealizado e Desenvolvido pelo 2°SG-PL Freitas com o apoio do COpAb</p>
        <p style="color:#94a3b8;font-size:11px;margin:.3rem 0 0;">Marinha do Brasil · Centro de Operações do Abastecimento · AtaCotada v1.0</p>
    </div>
    """,
    unsafe_allow_html=True,
)
