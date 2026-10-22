"""Aprendendo a usar: vídeo-aulas simuladas que mostram, passo a passo, como usar cada ferramenta do AtaCotada."""

from __future__ import annotations

import base64
import os
import sys

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Aprendendo a usar",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")
sys.path.insert(0, BASE_DIR)
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('tutorial_player', 'tutorial_cotacao', 'tutorial_catmat', 'tutorial_cotacao_direta', 'tutorial_cotacao_rapida', 'tutorial_adesoes', 'tutorial_notas_fiscais', 'tutorial_fornecedores', 'tutorial_web_scraping', 'tutorial_ipca', 'tutorial_detalhes_compra', 'tutorial_consulta_cnpj', 'tutorial_radar_licitacoes')  # evita módulo antigo em memória após deploy
import tutorial_adesoes  # noqa: E402
import tutorial_catmat  # noqa: E402
import tutorial_cotacao  # noqa: E402
import tutorial_cotacao_direta  # noqa: E402
import tutorial_consulta_cnpj  # noqa: E402
import tutorial_cotacao_rapida  # noqa: E402
import tutorial_detalhes_compra  # noqa: E402
import tutorial_fornecedores  # noqa: E402
import tutorial_ipca  # noqa: E402
import tutorial_notas_fiscais  # noqa: E402
import tutorial_radar_licitacoes  # noqa: E402
import tutorial_web_scraping  # noqa: E402
from tutorial_player import ALTURA_IFRAME  # noqa: E402

# Vídeo-aulas disponíveis (módulo com html()) e as previstas. Para publicar uma nova, crie tutorial_<ferramenta>.py
# e troque "modulo" de None para o módulo importado.
VIDEOS = [
    {"id": "cotacao", "titulo": "Cotação", "icone": "⚓", "resumo": "Pesquisa de preços de um item: catálogo, consulta, filtros, outliers, estatísticas e relatório.", "modulo": tutorial_cotacao},
    {"id": "catmat", "titulo": "CATMAT/CATSERV", "icone": "🔎", "resumo": "Como achar o código de material ou serviço.", "modulo": tutorial_catmat},
    {"id": "rapida", "titulo": "Cotação Rápida", "icone": "⚡", "resumo": "Cotar vários itens de uma vez e gerar o mapa comparativo.", "modulo": tutorial_cotacao_rapida},
    {"id": "direta", "titulo": "Cotação Direta", "icone": "📨", "resumo": "Pedidos de cotação direta a fornecedores.", "modulo": tutorial_cotacao_direta},
    {"id": "detalhes", "titulo": "Detalhes Compra", "icone": "🔍", "resumo": "Contratos, atas, itens, documentos e deságio de uma UASG.", "modulo": tutorial_detalhes_compra},
    {"id": "radar", "titulo": "Radar de Licitações", "icone": "📡", "resumo": "Licitações do PNCP: calendário, documentos, deságio, fornecedores e atas.", "modulo": tutorial_radar_licitacoes},
    {"id": "adesoes", "titulo": "Adesões", "icone": "🤝", "resumo": "Atas de registro de preços e adesões.", "modulo": tutorial_adesoes},
    {"id": "nf", "titulo": "Notas Fiscais", "icone": "📄", "resumo": "Consulta de notas fiscais em lote.", "modulo": tutorial_notas_fiscais},
    {"id": "forn", "titulo": "Fornecedores", "icone": "🏢", "resumo": "Banco de fornecedores.", "modulo": tutorial_fornecedores},
    {"id": "cnpj", "titulo": "Consulta CNPJ", "icone": "💻", "resumo": "Cadastro, sanções, contratos, adesões e notas fiscais de um fornecedor.", "modulo": tutorial_consulta_cnpj},
    {"id": "web", "titulo": "Web Scraping", "icone": "🕷️", "resumo": "Pesquisa de preços na web.", "modulo": tutorial_web_scraping},
    {"id": "babilaca", "titulo": "O Babilaca (IA)", "icone": "🧠", "resumo": "Assistente de IA para licitações e legislação.", "modulo": None},
    {"id": "ipca", "titulo": "Cálculo IPCA", "icone": "📊", "resumo": "Atualização monetária de valores pelo IPCA.", "modulo": tutorial_ipca},
]

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp { background: #001a4d !important; color: #f8fafc; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #facc15 !important;
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
        .tut-header {
            background: linear-gradient(135deg, #facc15 0%, #eab308 100%); border-radius: 10px;
            padding: 1.2rem 1.5rem; margin-bottom: 1rem; box-shadow: 0 10px 28px rgba(0, 0, 0, .3);
        }
        .tut-header h1 { color: #111; margin: 0; font-size: 1.5rem; font-weight: 900; }
        .tut-header p { color: #3b2f00; margin: .25rem 0 0; font-size: .9rem; font-weight: 600; }
        .tut-card {
            background: rgba(8, 26, 57, .78); border: 1px solid #1e5b9f; border-radius: 9px;
            padding: .8rem 1rem; margin: .35rem 0; display: flex; gap: .8rem; align-items: center;
        }
        .tut-card.on { border-color: #facc15; box-shadow: 0 0 12px rgba(250, 204, 21, .35); }
        .tut-card .ic { font-size: 1.5rem; }
        .tut-card .tt { color: #fff; font-weight: 800; font-size: .95rem; }
        .tut-card .rs { color: #b6cae2; font-size: .78rem; }
        .tut-tag { margin-left: auto; font-size: .68rem; font-weight: 800; border-radius: 999px; padding: .15rem .6rem; white-space: nowrap; }
        .tut-tag.ok { background: #facc15; color: #111; }
        .tut-tag.soon { background: rgba(148, 163, 184, .2); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, .4); }
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
    st.page_link("pages/Radar_de_Licitacoes.py", label="Radar de Licitações", icon="📡")
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

st.markdown(
    """
    <div class="tut-header">
        <h1>🎓 Aprendendo a usar</h1>
        <p>Vídeo-aulas simuladas, passo a passo, mostrando como usar cada ferramenta do AtaCotada. Os dados das aulas são fictícios.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

disponiveis = [v for v in VIDEOS if v["modulo"] is not None]
escolhido = disponiveis[0]
if len(disponiveis) > 1:
    rotulos = {v["id"]: f'{v["icone"]} {v["titulo"]}' for v in disponiveis}
    escolhido_id = st.radio("Escolha a vídeo-aula", list(rotulos), format_func=rotulos.get, horizontal=True)
    escolhido = next(v for v in disponiveis if v["id"] == escolhido_id)

html_video = escolhido["modulo"].html()
if hasattr(st, "iframe"):  # st.components.v1.html está sendo descontinuado nas versões novas do Streamlit
    st.iframe(html_video, height=ALTURA_IFRAME)
else:
    components.html(html_video, height=ALTURA_IFRAME, scrolling=False)

st.markdown("### Vídeo-aulas")
for v in VIDEOS:
    pronto = v["modulo"] is not None
    st.markdown(
        f'<div class="tut-card{" on" if pronto else ""}"><div class="ic">{v["icone"]}</div>'
        f'<div><div class="tt">{v["titulo"]}</div><div class="rs">{v["resumo"]}</div></div>'
        f'<span class="tut-tag {"ok" if pronto else "soon"}">{"DISPONÍVEL" if pronto else "EM BREVE"}</span></div>',
        unsafe_allow_html=True,
    )
