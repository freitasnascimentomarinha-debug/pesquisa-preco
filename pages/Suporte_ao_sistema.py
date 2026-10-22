"""Suporte ao sistema: canal de contato (grupo do WhatsApp), divulgação do AtaCotada e contribuidores."""

from __future__ import annotations

import base64
import os
import sys
from urllib.parse import quote

import streamlit as st

st.set_page_config(
    page_title="Suporte ao sistema",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")
sys.path.insert(0, BASE_DIR)
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('contribuidores')  # evita módulo antigo em memória após deploy
from contribuidores import CONTRIBUIDORES, gerar_card_pdf, nome_do_arquivo  # noqa: E402

# Link de convite do grupo do WhatsApp (https://chat.whatsapp.com/...). Pode ficar aqui ou nos Secrets do app (WHATSAPP_GRUPO_URL).
GRUPO_WHATSAPP_URL = "https://chat.whatsapp.com/GYIuL0fuVrV2TEItXHVVf3"
# Endereço público do app; o link compartilhado abre direto na página "Sobre o projeto". Pode ser trocado nos Secrets (APP_URL).
APP_URL = "https://atacotada.streamlit.app"


def _segredo(nome: str, padrao: str = "") -> str:
    try:
        return str(st.secrets.get(nome, "") or "") or os.environ.get(nome, "") or padrao
    except Exception:
        return os.environ.get(nome, "") or padrao


link_grupo = _segredo("WHATSAPP_GRUPO_URL", GRUPO_WHATSAPP_URL).strip()
url_app = _segredo("APP_URL", APP_URL).rstrip("/")
mensagem = ("Conheça o AtaCotada: um sistema autônomo de apoio à pesquisa de preços e à instrução de processos de contratação, "
            "criado para reduzir semanas de trabalho a minutos. Acesse: " + url_app + "/Sobre_o_projeto")
link_compartilhar = "https://wa.me/?text=" + quote(mensagem)

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp { background: #001a4d !important; color: #f8fafc; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #22c55e !important;
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
        .su-header { background: linear-gradient(135deg, #25d366 0%, #128c7e 100%); border-radius: 10px; padding: 1.3rem 1.6rem; margin-bottom: 1rem; box-shadow: 0 10px 28px rgba(0, 0, 0, .3); }
        .su-header h1 { color: #fff; margin: 0; font-size: 1.6rem; font-weight: 900; }
        .su-header p { color: #ecfdf5; margin: .35rem 0 0; font-size: .98rem; font-weight: 500; line-height: 1.55; }
        .su-panel { background: rgba(8, 26, 57, .78); border: 1px solid #1e5b9f; border-left: 5px solid #25d366; border-radius: 9px; padding: .9rem 1.1rem; margin: .6rem 0 .9rem; }
        .su-panel h3 { color: #d4af37; font-size: 1.05rem; margin: 0 0 .4rem; }
        .su-panel p, .su-panel li { color: #dbe7f7; font-size: .92rem; line-height: 1.55; }
        .su-panel ul { margin: .3rem 0 0 1.1rem; padding: 0; }
        .su-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: .6rem; margin-top: .5rem; }
        .su-card { background: rgba(0, 26, 77, .7); border: 1px solid #1e5b9f; border-radius: 8px; padding: .7rem .85rem; }
        .su-card .t { color: #fff; font-weight: 800; font-size: .95rem; }
        .su-card .d { color: #b6cae2; font-size: .82rem; margin-top: .2rem; line-height: 1.45; }
        .su-msg { background: rgba(37, 211, 102, .1); border: 1px dashed rgba(37, 211, 102, .6); border-radius: 8px; padding: .6rem .8rem; color: #d1fae5; font-size: .82rem; line-height: 1.5; margin: .4rem 0 .6rem; }
        [data-testid="stLinkButton"] a, [data-testid="stBaseLinkButton-primary"], a[data-testid="stBaseLinkButton-primary"] {
            border-radius: 10px !important; font-weight: 800 !important; padding: .7rem 1rem !important;
        }
        [data-testid="stLinkButton"] a[kind="primary"], a[data-testid="stBaseLinkButton-primary"] { background: linear-gradient(135deg, #25d366, #128c7e) !important; border: 0 !important; color: #fff !important; }
        [data-testid="stLinkButton"] a[kind="secondary"], a[data-testid="stBaseLinkButton-secondary"] { background: #0a2540 !important; border: 1px solid #25d366 !important; color: #d1fae5 !important; }
        [data-testid="stDownloadButton"] button {
            width: 100%; height: auto !important; min-height: 112px; white-space: normal; text-align: center; line-height: 1.5;
            background: linear-gradient(135deg, #001a4d 0%, #0a2f78 100%) !important; border: 2px solid #d4af37 !important; border-radius: 12px !important;
            color: #fff !important; padding: 1rem .8rem !important; box-shadow: 0 6px 18px rgba(0, 0, 0, .35);
        }
        [data-testid="stDownloadButton"] button:hover { border-color: #fde68a !important; box-shadow: 0 8px 22px rgba(212, 175, 55, .35); }
        [data-testid="stDownloadButton"] button p { color: #fff !important; margin: 0 !important; }
        [data-testid="stDownloadButton"] button strong { color: #d4af37 !important; font-size: 1.1rem; }
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
    st.page_link("pages/Suporte_ao_sistema.py", label="Suporte ao sistema", icon="💬")
    st.markdown("---")
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br><span style="color:#d4af37;">AtaCotada V2.0</span></div>', unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid],[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#facc15,#eab308)!important;border:1px solid #fde047!important;box-shadow:0 0 14px rgba(250,204,21,.55)!important}[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid] *{background:transparent!important;color:#111!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid],[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#ef4444,#b91c1c)!important;border:1px solid #fca5a5!important;box-shadow:0 0 14px rgba(239,68,68,.55)!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid],[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#25d366,#128c7e)!important;border:1px solid #86efac!important;box-shadow:0 0 14px rgba(37,211,102,.5)!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}</style>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="su-header">
        <h1>💬 Suporte ao sistema</h1>
        <p>Este espaço é seu. Aqui você pode <b>sugerir melhorias</b>, <b>avisar</b> quando algo parar de funcionar, <b>pedir atualizações</b> e novas versões,
        fazer <b>críticas construtivas</b> e trocar ideias com quem usa e desenvolve o sistema. Todo mundo é bem-vindo, e toda contribuição ajuda o AtaCotada a evoluir.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="su-panel">
        <h3>O que você pode fazer no grupo</h3>
        <div class="su-grid">
            <div class="su-card"><div class="t">💡 Sugerir melhorias</div><div class="d">Teve uma ideia que facilitaria o seu trabalho? Conte para a gente.</div></div>
            <div class="su-card"><div class="t">🛠️ Avisar um problema</div><div class="d">Uma funcionalidade parou de funcionar? Avise: quanto antes soubermos, mais rápido corrigimos.</div></div>
            <div class="su-card"><div class="t">🆕 Pedir atualização ou nova versão</div><div class="d">Precisa de uma ferramenta nova ou de um ajuste numa que já existe? Solicite.</div></div>
            <div class="su-card"><div class="t">🗣️ Críticas construtivas</div><div class="d">Sua opinião honesta é bem-vinda e ajuda a melhorar o sistema.</div></div>
            <div class="su-card"><div class="t">🎓 Debater e aprender</div><div class="d">Troque experiências sobre <b>obtenção</b>, <b>logística</b> e <b>soluções administrativas</b>, com fluxos de trabalho, sistemas, automação e IA.</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="su-panel"><h3>Entre no grupo do WhatsApp</h3><p>Um toque e você já entra no grupo. Respeito, colaboração e vontade de aprender são o que nos move.</p></div>', unsafe_allow_html=True)
if link_grupo:
    st.link_button("💬 Entrar no grupo do WhatsApp", link_grupo, type="primary", use_container_width=True)
else:
    st.button("💬 Entrar no grupo do WhatsApp", disabled=True, use_container_width=True)
    st.caption("O link do grupo será divulgado em breve.")
st.markdown(
    '<div class="su-panel"><h3>Ao avisar um problema, ajude-nos a resolver mais rápido</h3>'
    "<ul><li>Diga <b>em qual página</b> estava e <b>o que tentou fazer</b>.</li>"
    "<li>Copie a <b>mensagem de erro</b> que apareceu, se houver, ou envie um <b>print</b> da tela.</li>"
    "<li>Informe se acontece <b>sempre</b> ou só <b>às vezes</b> (o sistema pode ficar lento quando há muita gente usando).</li></ul></div>",
    unsafe_allow_html=True,
)

st.markdown('<div class="su-panel"><h3>Divulgue o AtaCotada</h3><p>Compartilhe com colegas pelo WhatsApp. O link já abre na página <b>Sobre o projeto</b>, que apresenta o sistema.</p></div>', unsafe_allow_html=True)
st.markdown(f'<div class="su-msg">{mensagem}</div>', unsafe_allow_html=True)
st.link_button("📲 Compartilhar o AtaCotada no WhatsApp", link_compartilhar, use_container_width=True)

st.markdown('<div class="su-panel"><h3>Contribuidores</h3><p>Conheça quem ajudou a criar e a aperfeiçoar o sistema. Toque em um card para baixar o PDF.</p></div>', unsafe_allow_html=True)
mostrar = st.session_state.get("su_mostrar_contribuidores", False)
if st.button("🙌 Ocultar contribuidores" if mostrar else "🙌 Contribuidores", key="su_btn_contribuidores", use_container_width=True):
    st.session_state["su_mostrar_contribuidores"] = not mostrar
    st.rerun()
if mostrar:
    por_linha = 3
    for inicio in range(0, len(CONTRIBUIDORES), por_linha):
        colunas = st.columns(por_linha)
        for coluna, pessoa in zip(colunas, CONTRIBUIDORES[inicio:inicio + por_linha]):
            with coluna:
                st.download_button(
                    f"**{pessoa['nome']}**  \nNIP {pessoa['nip']}  \n{pessoa.get('papel', '')}",
                    data=gerar_card_pdf(pessoa), file_name=nome_do_arquivo(pessoa), mime="application/pdf",
                    key=f"su_card_{pessoa['nip']}", use_container_width=True,
                )

st.markdown(
    """
    <div style="margin-top:2rem;padding-top:1.4rem;border-top:1px solid #0033cc;text-align:center;">
        <p style="color:#d4af37;font-size:12px;margin:0;letter-spacing:.5px;">Idealizado e Desenvolvido pelo 2°SG-PL Freitas com o apoio do COpAb</p>
    </div>
    """,
    unsafe_allow_html=True,
)
