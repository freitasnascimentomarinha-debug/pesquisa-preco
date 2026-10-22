"""
Radar de Licitações — AtaCotada
Licitações publicadas no PNCP: busca por objeto, UASG, período e situação; calendário de encerramentos;
documentos (edital, TR, ETP), link de acompanhamento, itens com deságio, fornecedores, atas e participantes.
"""

import base64
import os
from datetime import datetime
from html import escape as _e

import pandas as pd
import streamlit as st

from atualizar_modulos import recarregar_se_mudou

recarregar_se_mudou("servicos_publicos", "licitacoes_pncp")  # evita módulo antigo em memória após deploy
from licitacoes_pncp import (  # noqa: E402
    SITUACOES, UFS, buscar_licitacoes, buscar_uasg_por_nome, detalhar_licitacao, documentos_de_homologacao,
    fornecedores, gerar_calendario_ics, nome_uasg, resumo_desagio, tabela_itens,
)
from servicos_publicos import gerar_excel  # noqa: E402

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões")

st.set_page_config(
    page_title="AtaCotada - Radar de Licitações",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (mesmo padrão visual do app) ──────────────────────────────────────
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"],
    .main, [data-testid="stApp"], .stApp {
        background-color: #001a4d !important;
        color: #ffffff !important;
    }
    .stApp { animation: fadeIn 0.3s ease-in; }
    @keyframes fadeIn { from { opacity: 0.7; } to { opacity: 1; } }

    .header-container {
        background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%);
        padding: 2rem; border-radius: 10px; margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); text-align: center;
    }
    .logo-text { color: #fff; font-size: 14px; font-weight: 600; letter-spacing: 2px; margin-bottom: .5rem; }
    .sistema-nome { color: #d4af37; font-size: 48px; font-weight: bold; letter-spacing: 3px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5); margin: .5rem 0; font-family: 'Arial Black', sans-serif; }
    .subtitulo { color: #fff; font-size: 14px; margin-top: .5rem; letter-spacing: 1px; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #111 50%, #0a0a0a 100%) !important;
        border-right: 3px solid #d4af37 !important;
    }
    [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #d4af37 !important; font-family: 'Arial Black', sans-serif;
        font-size: 22px; text-align: center; letter-spacing: 2px;
        border-bottom: 2px solid #d4af37; padding-bottom: .75rem; margin-bottom: 1.5rem;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%) !important;
        color: #fff !important; border: 1px solid #333 !important;
        border-radius: 8px !important; margin: .2rem 0 !important;
        padding: .45rem .7rem !important; font-weight: 600 !important;
        font-size: 12.5px !important; line-height: 1.2 !important;
        min-height: 0 !important; transition: all .3s ease !important;
        text-decoration: none !important; display: flex !important;
        align-items: center !important; justify-content: center !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span { color: #fff !important; }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background: linear-gradient(135deg, #252525 0%, #353535 100%) !important;
        border: 1px solid #d4af37 !important; transform: translateX(5px);
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover span { color: #d4af37 !important; }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
        color: #0a0a0a !important; border: 1px solid #d4af37 !important; font-weight: bold !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span { color: #0a0a0a !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] p { color: #fff !important; }
    .sidebar-footer { color: #666; font-size: 11px; text-align: center; padding: 1rem 0;
        border-top: 1px solid #333; margin-top: 2rem; }

    /* Cards */
    .info-card {
        background: linear-gradient(135deg, rgba(7, 37, 92, 0.92) 0%, rgba(0, 82, 204, 0.78) 100%);
        border: 1px solid rgba(212,175,55,0.42);
        border-radius: 14px; padding: 1.05rem 1.35rem; margin-bottom: .9rem;
        box-shadow: 0 10px 28px rgba(0,0,0,0.28);
        backdrop-filter: blur(4px);
    }
    .info-card h4 { color: #d4af37; margin: 0 0 .5rem 0; font-size: 1rem; }
    .info-card p { color: #cbd5e1; margin: .15rem 0; font-size: .9rem; }
    .info-card a { color: #d4af37 !important; text-decoration: none; font-weight: 600; }
    .info-card a:hover { color: #f0d060 !important; text-decoration: underline; }

    .lookup-panel {
        border-radius: 16px; padding: 1.2rem 1.35rem; margin: 1rem 0 1.1rem 0;
        border: 1px solid rgba(212,175,55,0.35);
        box-shadow: 0 14px 30px rgba(0,0,0,0.24);
    }
    .lookup-panel.success {
        background: linear-gradient(135deg, rgba(10, 58, 38, 0.96) 0%, rgba(13, 110, 75, 0.86) 100%);
    }
    .lookup-panel.warning {
        background: linear-gradient(135deg, rgba(92, 45, 7, 0.96) 0%, rgba(156, 87, 17, 0.84) 100%);
    }
    .lookup-title {
        color: #ffffff; font-size: 1.08rem; font-weight: 700; margin-bottom: .45rem;
    }
    .lookup-text {
        color: #f8fafc; font-size: .95rem; line-height: 1.55; margin: .15rem 0;
    }
    .lookup-meta {
        color: #fde68a; font-size: .82rem; letter-spacing: .04em; text-transform: uppercase;
        margin-top: .55rem;
    }

    .doc-card {
        background: rgba(0, 26, 77, 0.45); border: 1px solid rgba(212,175,55,0.2);
        border-radius: 10px; padding: .8rem 1rem; margin-bottom: .5rem;
    }
    .doc-card a { color: #d4af37 !important; font-weight: 600; text-decoration: none; }
    .doc-card a:hover { color: #f0d060 !important; text-decoration: underline; }
    .doc-badge {
        background: rgba(212,175,55,0.15); border-radius: 4px;
        padding: .1rem .4rem; font-size: .75rem; color: #d4af37; font-weight: 500;
    }

    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #d4af37 !important; color: #fff !important;
        border: none !important; font-weight: bold !important;
    }
    .stButton > button[kind="primary"]:hover { background-color: #c5a028 !important; }

    /* Botão amarelo para carregar mais ARPs */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"] {
        background-color: #d4af37 !important; color: #000 !important;
        border: 2px solid #d4af37 !important; font-weight: bold !important;
        border-radius: 8px !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover {
        background-color: #f0d060 !important; border-color: #f0d060 !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
_acanto_path = os.path.join(DATA_DIR, "acanto.png")
_acanto_b64 = None
if os.path.exists(_acanto_path):
    with open(_acanto_path, "rb") as _f:
        _acanto_b64 = base64.b64encode(_f.read()).decode()

with st.sidebar:
    if _acanto_b64:
        st.markdown(
            f'<div style="text-align:center;padding:1rem 0 0.5rem 0;">'
            f'<img src="data:image/png;base64,{_acanto_b64}" style="max-width:70%;height:auto;"></div>',
            unsafe_allow_html=True,
        )
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
    st.markdown(
        '<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;'
        'padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br><span style="color:#d4af37;">AtaCotada V2.0</span></div>', unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid],[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#facc15,#eab308)!important;border:1px solid #fde047!important;box-shadow:0 0 14px rgba(250,204,21,.55)!important}[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][href][data-testid] *{background:transparent!important;color:#111!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid],[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#ef4444,#b91c1c)!important;border:1px solid #fca5a5!important;box-shadow:0 0 14px rgba(239,68,68,.55)!important}[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid],[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid][aria-current="page"]{background:linear-gradient(135deg,#25d366,#128c7e)!important;border:1px solid #86efac!important;box-shadow:0 0 14px rgba(37,211,102,.5)!important}[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][href][data-testid] *{background:transparent!important;color:#fff!important;font-weight:800!important}</style>', unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-container">
    <div class="logo-text">⚓ MARINHA DO BRASIL ⚓</div>
    <div class="sistema-nome">AtaCotada</div>
    <div class="subtitulo">Radar de Licitações</div>
</div>
""", unsafe_allow_html=True)




# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

def _moeda(valor) -> str:
    if valor in (None, ""):
        return "—"
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return str(valor)


def _data_br(texto) -> str:
    texto = str(texto or "").replace("T", " ")
    for formato, tam in (("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(texto[:tam], formato).strftime("%d/%m/%Y %H:%M" if tam == 16 else "%d/%m/%Y")
        except ValueError:
            continue
    return texto or "—"


def _texto(valor) -> str:
    """Corrige texto com acentuação quebrada vinda da fonte (ex.: 'PreÃ§os' -> 'Preços')."""
    texto = str(valor or "")
    if "Ã" in texto or "Â" in texto:
        try:
            return texto.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return texto


def _url(doc: dict) -> str:
    return doc.get("url") or doc.get("uri") or doc.get("urlDownload") or ""


def _encerra_no_futuro(lic: dict) -> bool:
    try:
        return datetime.strptime(lic["encerramento"][:16], "%Y-%m-%d %H:%M") >= datetime.now()
    except (KeyError, ValueError):
        return False


@st.cache_data(ttl=900, show_spinner=False)
def _detalhe(cnpj: str, ano: str, seq: str) -> dict:
    return detalhar_licitacao(cnpj, ano, seq)


def _df_lista(licitacoes):
    return pd.DataFrame([{
        "Publicação": _data_br(l["publicacao"]), "Abertura das propostas": _data_br(l["abertura"]),
        "Encerramento das propostas": _data_br(l["encerramento"]), "UASG": l["uasg"], "Unidade": _texto(l["unidade"]),
        "Órgão": _texto(l["orgao"]), "UF": l["uf"], "Modalidade": l["modalidade"], "Licitação": _texto(l["titulo"]),
        "Objeto": _texto(l["objeto"]), "Resultado": "Sim" if l["tem_resultado"] else "Não", "PNCP": l["link_pncp"],
    } for l in licitacoes])


# ═══════════════════════════════════════════════════════════════════════════
# BUSCA
# ═══════════════════════════════════════════════════════════════════════════

st.markdown(
    '<div class="info-card"><h4>📡 Radar de Licitações</h4>'
    '<p>Encontre licitações publicadas no PNCP pelo <b>objeto</b>, pela <b>UASG</b> (código ou nome), pelo <b>período</b> e pela '
    '<b>situação</b>. Para cada uma: calendário, documentos (edital, termo de referência, estudo técnico), link de acompanhamento, '
    'itens com deságio, fornecedores, atas de registro de preços e participantes.</p></div>',
    unsafe_allow_html=True,
)

col_obj, col_uasg = st.columns([3, 2])
with col_obj:
    objeto = st.text_input("Objeto (palavras-chave)", key="lic_obj",
                           placeholder="Ex: material de limpeza, gênero alimentício, manutenção de ar-condicionado")
with col_uasg:
    uasg_txt = st.text_input("UASG (código ou parte do nome)", key="lic_uasg", placeholder="Ex: 789000 ou distrito naval")

codigo_uasg = ""
if uasg_txt.strip():
    if uasg_txt.strip().isdigit():
        codigo_uasg = uasg_txt.strip()
        if nome_uasg(codigo_uasg):
            st.caption(f"UASG {codigo_uasg}: {nome_uasg(codigo_uasg)}")
    else:
        _achadas = buscar_uasg_por_nome(uasg_txt)
        if _achadas:
            _i = st.selectbox("UASG encontrada", range(len(_achadas)), key="lic_uasg_sel",
                              format_func=lambda i: f"{_achadas[i]['codigo']} — {_achadas[i]['nome']}" + (f" ({_achadas[i]['uf']})" if _achadas[i]['uf'] else ""))
            codigo_uasg = _achadas[_i]["codigo"]
        else:
            st.warning("Nenhuma UASG com esse nome no cadastro local. Digite o código, se souber.")

col_sit, col_uf, col_ini, col_fim = st.columns(4)
with col_sit:
    situacao_rotulo = st.selectbox("Situação", list(SITUACOES), index=2, key="lic_sit",
                                   help="Recebendo propostas: ainda abertas. Encerradas: prazo de propostas já terminou.")
with col_uf:
    uf = st.selectbox("UF", ["Todas"] + UFS, key="lic_uf")
with col_ini:
    data_ini = st.date_input("Publicadas a partir de", value=None, format="DD/MM/YYYY", key="lic_ini")
with col_fim:
    data_fim = st.date_input("Publicadas até", value=None, format="DD/MM/YYYY", key="lic_fim")

if st.button("🔎 Buscar licitações", type="primary", use_container_width=True):
    if not objeto.strip() and not codigo_uasg:
        st.error("Informe o objeto ou a UASG.")
    elif data_ini and data_fim and data_ini > data_fim:
        st.error("A data inicial é posterior à data final.")
    else:
        with st.spinner("Buscando licitações no PNCP..."):
            lista, erro, total = buscar_licitacoes(objeto, codigo_uasg, SITUACOES[situacao_rotulo],
                                                   "" if uf == "Todas" else uf, data_ini, data_fim)
        st.session_state["lic_res"] = {"lista": lista, "erro": erro, "total": total, "uasg": codigo_uasg}
        st.session_state.pop("lic_detalhe", None)

res = st.session_state.get("lic_res")
if res:
    lista = res["lista"]
    if res["erro"]:
        st.warning(f"⚠️ {res['erro']}. Tente novamente em alguns minutos.")
    if not lista and not res["erro"]:
        st.info("Nenhuma licitação encontrada com esses filtros. Tente palavras-chave mais gerais ou outro período."
                + (" Se escolheu a UASG pelo nome, verifique se não há outra unidade com nome parecido na lista: "
                   "algumas UASGs antigas não publicam mais licitações." if res.get("uasg") else ""))

    if lista:
        abertas = sorted([l for l in lista if _encerra_no_futuro(l)], key=lambda l: l["encerramento"])
        m1, m2, m3 = st.columns(3)
        m1.metric("Licitações encontradas", len(lista))
        m2.metric("Ainda recebendo propostas", len(abertas))
        m3.metric("Com resultado publicado", sum(1 for l in lista if l["tem_resultado"]))
        if len(lista) >= 500:
            st.caption("Mostrando as 500 mais recentes. Use o período ou palavras mais específicas para refinar.")

        # ── Calendário ──
        st.markdown("#### 📅 Calendário de encerramentos")
        if abertas:
            st.dataframe(pd.DataFrame([{
                "Encerramento das propostas": _data_br(l["encerramento"]), "Abertura": _data_br(l["abertura"]),
                "Licitação": _texto(l["titulo"]), "Unidade": _texto(l["unidade"]), "UASG": l["uasg"], "Objeto": _texto(l["objeto"])[:160],
            } for l in abertas]), use_container_width=True, hide_index=True)
            st.download_button("📅 Adicionar à minha agenda (.ics)", key="lic_ics", data=gerar_calendario_ics(abertas),
                               file_name="licitacoes_encerramentos.ics", mime="text/calendar",
                               help="Abre no Outlook ou no Google Agenda, com lembrete um dia antes de cada encerramento.")
        else:
            st.caption("Nenhuma das licitações encontradas está recebendo propostas.")

        # ── Lista ──
        st.markdown("#### 📋 Licitações encontradas")
        df = _df_lista(lista)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={"PNCP": st.column_config.LinkColumn("PNCP", display_text="Abrir")})
        st.download_button("📊 Exportar lista (Excel)", key="lic_xls_lista", data=gerar_excel({"Licitações": df}),
                           file_name="licitacoes.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # ── Escolha para detalhar ──
        st.markdown("#### 🔍 Detalhar uma licitação")
        col_sel, col_btn = st.columns([5, 1])
        with col_sel:
            k = st.selectbox("Licitação", range(len(lista)), key="lic_sel", label_visibility="collapsed",
                             format_func=lambda i: f"{_texto(lista[i]['titulo'])} — {_texto(lista[i]['unidade'])} — {_texto(lista[i]['objeto'])[:90]}")
        with col_btn:
            if st.button("Ver detalhes", key="lic_ver", use_container_width=True):
                st.session_state["lic_detalhe"] = lista[k]


# ═══════════════════════════════════════════════════════════════════════════
# DETALHE
# ═══════════════════════════════════════════════════════════════════════════

lic = st.session_state.get("lic_detalhe")
if lic:
    with st.spinner("Buscando documentos, itens, resultados e atas no PNCP... (licitações grandes podem levar alguns segundos)"):
        det = _detalhe(lic["cnpj"], lic["ano"], lic["sequencial"])
    compra = det["compra"]
    st.markdown("---")
    st.markdown(
        f'<div class="info-card"><h4>{_e(_texto(lic["titulo"]))} — {_e(_texto(compra.get("modalidadeNome") or lic["modalidade"]))}</h4>'
        f'<p><b>Unidade:</b> {_e(_texto(lic["unidade"]))} (UASG {_e(lic["uasg"])}) — {_e(_texto(lic["orgao"]))} — {_e(lic["municipio"])}/{_e(lic["uf"])}</p>'
        f'<p><b>Objeto:</b> {_e(_texto(compra.get("objetoCompra") or lic["objeto"]))}</p>'
        f'<p><b>Processo:</b> {_e(str(compra.get("processo") or "—"))} · <b>Situação:</b> {_e(str(compra.get("situacaoCompraNome") or "—"))} · '
        f'<b>Registro de preços:</b> {"Sim" if compra.get("srp") else "Não"}</p></div>',
        unsafe_allow_html=True,
    )
    if det["erros"]:
        st.warning("Algumas partes não puderam ser consultadas: " + "; ".join(det["erros"]))

    c1, c2, c3 = st.columns(3)
    c1.metric("Publicação no PNCP", _data_br(compra.get("dataPublicacaoPncp") or lic["publicacao"]))
    c2.metric("Abertura das propostas", _data_br(compra.get("dataAberturaProposta") or lic["abertura"]))
    c3.metric("Encerramento das propostas", _data_br(compra.get("dataEncerramentoProposta") or lic["encerramento"]))

    des = resumo_desagio(det)
    v1, v2, v3 = st.columns(3)
    v1.metric("Valor estimado", _moeda(des["estimado"] or None))
    v2.metric("Valor homologado", _moeda(des["homologado"] or None))
    v3.metric("Deságio", f"{des['desagio']:.1f}%".replace(".", ",") if des["desagio"] is not None else "—",
              help="(estimado − homologado) ÷ estimado" + (" — calculado pela soma dos itens com resultado." if des["base"] == "itens" else "."))

    l1, l2, _ = st.columns([1, 1, 2])
    with l1:
        if compra.get("linkSistemaOrigem"):
            st.link_button("👁️ Acompanhar a licitação", compra["linkSistemaOrigem"], use_container_width=True,
                           help="Abre a página de acompanhamento no sistema de origem (ex.: Compras.gov.br), com propostas e lances.")
    with l2:
        st.link_button("🌐 Ver no PNCP", lic["link_pncp"], use_container_width=True)

    linhas_itens = tabela_itens(det)
    lista_forn = fornecedores(det)
    homolog = documentos_de_homologacao(det)
    t_doc, t_itens, t_forn, t_atas, t_hom = st.tabs([
        f"📎 Documentos ({len(det['arquivos'])})", f"📦 Itens e deságio ({len(linhas_itens)})",
        f"🏢 Fornecedores ({len(lista_forn)})", f"📜 Atas e participantes ({len(det['atas'])})", f"✅ Homologação ({len(homolog)})",
    ])

    with t_doc:
        if not det["arquivos"]:
            st.info("O órgão não publicou documentos desta licitação no PNCP.")
        for d in det["arquivos"]:
            st.markdown(f"📥 [{_texto(d.get('titulo') or 'Documento')}]({_url(d)}) — {d.get('tipoDocumentoNome', '')} · "
                        f"publicado em {_data_br(d.get('dataPublicacaoPncp'))}")
        st.caption("A Marinha costuma publicar um único arquivo .zip com o edital, o termo de referência, o estudo técnico preliminar "
                   "e a relação de itens.")

    with t_itens:
        if linhas_itens:
            df_itens = pd.DataFrame(linhas_itens)
            for _col in ("Valor unit. estimado", "Valor total estimado", "Valor unit. homologado", "Valor total homologado"):
                df_itens[_col] = df_itens[_col].map(lambda v: _moeda(v) if v not in (None, "") and v == v else "—")
            df_itens["Deságio (%)"] = df_itens["Deságio (%)"].map(lambda v: f"{v:.1f}%".replace(".", ",") if v not in (None, "") and v == v else "—")
            st.dataframe(df_itens, use_container_width=True, hide_index=True)
            st.caption("Resultados cancelados mostram quem chegou a vencer o item e depois foi substituído (desistência, inabilitação etc.).")
        else:
            st.info("Itens não disponíveis no PNCP.")

    with t_forn:
        if lista_forn:
            _df_forn = pd.DataFrame(lista_forn)
            _df_forn["Valor homologado"] = _df_forn["Valor homologado"].map(_moeda)
            st.dataframe(_df_forn, use_container_width=True, hide_index=True)
            st.caption("Fornecedores que tiveram resultado registrado. As propostas e lances dos demais participantes só aparecem "
                       "no acompanhamento do sistema de origem.")
            cf1, cf2 = st.columns([5, 1])
            with cf1:
                j = st.selectbox("Fornecedor", range(len(lista_forn)), key="lic_forn", label_visibility="collapsed",
                                 format_func=lambda i: f"{lista_forn[i]['Fornecedor']} ({lista_forn[i]['CNPJ/CPF']})")
            with cf2:
                if st.button("🏢 Consultar", key="lic_forn_btn", use_container_width=True, help="Abre a Consulta CNPJ com este fornecedor"):
                    st.session_state["_cons_prefill"] = lista_forn[j]["CNPJ/CPF"]
                    st.switch_page("pages/Consulta.py")
        else:
            st.info("Ainda não há resultado (vencedores) publicado para esta licitação.")

    with t_atas:
        if not det["atas"]:
            st.info("Nenhuma ata de registro de preços publicada para esta licitação.")
        for ata in det["atas"]:
            cancelada = " — ❌ cancelada" if ata.get("cancelado") else ""
            with st.expander(f"📜 Ata nº {ata.get('numeroAtaRegistroPreco', '')}/{ata.get('anoAta', '')} — vigência "
                             f"{_data_br(ata.get('dataVigenciaInicio'))} a {_data_br(ata.get('dataVigenciaFim'))}{cancelada}"):
                for d in ata.get("_arquivos", []):
                    st.markdown(f"📥 [{_texto(d.get('titulo') or 'Ata')}]({_url(d)})")
                partes = ata.get("_partes", [])
                if partes:
                    st.dataframe(pd.DataFrame([{
                        "Papel": (p.get("tipoParteEnvolvida") or {}).get("nome", ""),
                        "Unidade": (p.get("unidade") or {}).get("nomeUnidade", ""), "Código": (p.get("unidade") or {}).get("codigo", ""),
                        "Órgão": (p.get("orgao") or {}).get("nome", ""),
                        "Município/UF": f"{((p.get('unidade') or {}).get('localidade') or {}).get('nomeMunicipio', '')}/"
                                        f"{((p.get('unidade') or {}).get('localidade') or {}).get('uf', '')}",
                    } for p in partes]), use_container_width=True, hide_index=True)

    with t_hom:
        if homolog:
            for d in homolog:
                st.markdown(f"📥 [{_texto(d.get('titulo') or 'Documento')}]({_url(d)}) — {d.get('tipoDocumentoNome', '')}")
        else:
            st.info("O órgão não publicou termo de homologação, ata da sessão ou ata de registro de preços desta licitação no PNCP.")

    st.download_button(
        "📊 Exportar esta licitação (Excel)", key="lic_xls_det",
        data=gerar_excel({
            "Resumo": pd.DataFrame([
                ("Licitação", _texto(lic["titulo"])), ("Unidade", f"{_texto(lic['unidade'])} (UASG {lic['uasg']})"),
                ("Objeto", _texto(compra.get("objetoCompra") or lic["objeto"])), ("Abertura das propostas", _data_br(compra.get("dataAberturaProposta"))),
                ("Encerramento das propostas", _data_br(compra.get("dataEncerramentoProposta"))), ("Valor estimado", des["estimado"]),
                ("Valor homologado", des["homologado"]), ("Deságio (%)", round(des["desagio"], 2) if des["desagio"] is not None else ""),
                ("Acompanhamento", compra.get("linkSistemaOrigem", "")), ("PNCP", lic["link_pncp"]),
            ], columns=["Campo", "Valor"]),
            "Itens": pd.DataFrame(linhas_itens), "Fornecedores": pd.DataFrame(lista_forn),
            "Documentos": pd.DataFrame([{"Título": _texto(d.get("titulo")), "Tipo": d.get("tipoDocumentoNome", ""), "Link": _url(d)}
                                        for d in det["arquivos"] + homolog]),
        }),
        file_name=f"licitacao_{lic['uasg']}_{lic['ano']}_{lic['sequencial']}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
