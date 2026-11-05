"""Tema visual do AtaCotada: mascote animado, visual moderno e JavaScript.

Somente apresentação. Nenhuma regra de negócio passa por aqui.

Uso (dentro de ``with st.sidebar:``, no lugar da imagem do acanto):

    from ui_tema import sidebar_mascote
    sidebar_mascote()

A chamada injeta, uma vez por execução da página:
  * o CSS moderno (cartões em vidro, botões, campos, abas, tabelas...);
  * o mascote "Marujo Cotado" (SVG animado) no topo da sidebar;
  * o JavaScript de interação (olhos que seguem o mouse, balão de falas,
    barra de progresso de rolagem e botão "voltar ao topo").
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Mascote (SVG inline, animado só com CSS; os olhos são guiados pelo JS)
# ---------------------------------------------------------------------------
_MASCOTE_SVG = (
    '<svg class="mc-svg" viewBox="0 0 200 190" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="Mascote Marujo Cotado">'
    '<defs>'
    '<clipPath id="mcClip"><rect x="8" y="150" width="184" height="38" rx="19"/></clipPath>'
    '<linearGradient id="mcGold" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#ffe27a"/><stop offset="1" stop-color="#c99a1b"/></linearGradient>'
    '<linearGradient id="mcNavy" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#1d4ed8"/><stop offset="1" stop-color="#0b2a78"/></linearGradient>'
    '<linearGradient id="mcWood" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#b9743a"/><stop offset="1" stop-color="#6e3b17"/></linearGradient>'
    '<linearGradient id="mcSea" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#3b82f6" stop-opacity=".9"/><stop offset="1" stop-color="#0b2a78" stop-opacity=".95"/></linearGradient>'
    '<radialGradient id="mcSkin" cx=".4" cy=".35" r=".8">'
    '<stop offset="0" stop-color="#ffd9b0"/><stop offset="1" stop-color="#eaa371"/></radialGradient>'
    '</defs>'
    # fumaça do cachimbo
    '<g class="mc-smoke">'
    '<circle class="mc-puff p1" cx="44" cy="66" r="4" fill="#e8eefc"/>'
    '<circle class="mc-puff p2" cx="44" cy="66" r="3.4" fill="#e8eefc"/>'
    '<circle class="mc-puff p3" cx="44" cy="66" r="3" fill="#e8eefc"/>'
    '</g>'
    # barco + marinheiro (balançam juntos)
    '<g class="mc-boat">'
    # braço esquerdo apoiado na borda (antebraço grosso com âncora)
    '<path d="M64 112 C52 116 44 126 46 134" stroke="#0b2a78" stroke-width="13" stroke-linecap="round" fill="none"/>'
    '<ellipse cx="50" cy="136" rx="11" ry="13" fill="url(#mcSkin)" transform="rotate(14 50 136)"/>'
    '<rect x="40" y="126" width="20" height="5" rx="2.5" fill="#fff" transform="rotate(14 50 128)"/>'
    '<path d="M50 135 v8 M46 138 h8 M45 142 q5 4 10 0" stroke="#1d3a8a" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    # corpo
    '<path d="M62 118 C62 104 138 104 138 118 L144 150 H56 Z" fill="url(#mcNavy)"/>'
    '<path d="M84 108 Q100 120 116 108 L112 114 Q100 124 88 114 Z" fill="#fff"/>'
    '<path d="M100 118 l-7 12 l7 6 l7 -6 Z" fill="#e11d48"/>'
    # braço direito: acena (antebraço grosso)
    '<g class="mc-wave">'
    '<path d="M134 116 C148 118 156 106 156 94" stroke="#0b2a78" stroke-width="13" stroke-linecap="round" fill="none"/>'
    '<rect x="148" y="90" width="17" height="6" rx="3" fill="#fff"/>'
    '<ellipse cx="157" cy="76" rx="11" ry="16" fill="url(#mcSkin)"/>'
    '<path d="M157 70 v9 M153 73 h8 M152 78 q5 4 10 0" stroke="#1d3a8a" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
    '<circle cx="157" cy="58" r="9.5" fill="url(#mcSkin)"/>'
    '<path d="M151 55 q3 2 6 0 M157 55 q3 2 6 0" stroke="#b97a4a" stroke-width="1.2" fill="none"/>'
    '</g>'
    # cabeça: rosto com queixão
    '<ellipse cx="100" cy="76" rx="32" ry="29" fill="url(#mcSkin)"/>'
    '<ellipse cx="108" cy="100" rx="19" ry="13" fill="url(#mcSkin)"/>'
    '<circle cx="68" cy="80" r="6" fill="#eaa371"/><circle cx="132" cy="80" r="6" fill="#eaa371"/>'
    '<ellipse cx="80" cy="90" rx="6" ry="3.6" fill="#ff8f8f" opacity=".5"/>'
    # nariz
    '<ellipse cx="102" cy="88" rx="7" ry="6" fill="#eaa371"/><ellipse cx="100" cy="86" rx="2.6" ry="2" fill="#f7c9a1"/>'
    # olho aberto (segue o mouse) e olho apertado (marca registrada)
    '<g transform="translate(86 74)"><g class="mc-eye">'
    '<ellipse rx="8.5" ry="9.5" fill="#fff"/>'
    '<circle class="mc-pupil" r="4.8" fill="#10224f"/><circle class="mc-glint" cx="-1.4" cy="-2.2" r="1.6" fill="#fff"/>'
    '</g></g>'
    '<path d="M110 76 Q118 71 126 76" stroke="#5a2f12" stroke-width="3.2" fill="none" stroke-linecap="round"/>'
    '<path d="M76 62 Q86 55 95 62" stroke="#6b3a14" stroke-width="4" fill="none" stroke-linecap="round"/>'
    '<path d="M108 63 Q118 57 128 64" stroke="#6b3a14" stroke-width="4" fill="none" stroke-linecap="round"/>'
    # boca e cachimbo
    '<path class="mc-mouth" d="M96 100 Q106 106 118 98" stroke="#7a3b1d" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<path d="M88 98 Q70 100 60 94" stroke="#5a3418" stroke-width="3.4" fill="none" stroke-linecap="round"/>'
    '<path d="M50 84 h12 l-1 14 q-5 4 -10 0 Z" fill="#7a4620" stroke="#4a2810" stroke-width="1.2"/>'
    '<ellipse cx="56" cy="84" rx="6" ry="2.2" fill="#2b1608"/>'
    # boné
    '<g transform="rotate(-6 100 50)">'
    '<path d="M64 52 C64 22 136 22 136 52 C136 56 64 56 64 52 Z" fill="#fff"/>'
    '<rect x="62" y="46" width="76" height="10" rx="5" fill="url(#mcNavy)"/>'
    '<g transform="translate(100 34) scale(.58)">'
    '<circle cy="-9" r="4.2" fill="none" stroke="url(#mcGold)" stroke-width="3"/>'
    '<path d="M0 -5 V17 M-9 4 H9 M-14 9 C-12 18 -4 19 0 17 C4 19 12 18 14 9" '
    'stroke="url(#mcGold)" stroke-width="3.2" fill="none" stroke-linecap="round"/>'
    '</g></g>'
    # barquinho
    '<path d="M22 140 H178 C172 164 152 176 128 176 H72 C48 176 28 164 22 140 Z" fill="url(#mcWood)"/>'
    '<path d="M22 140 H178 L176 147 H24 Z" fill="#f4f1e8"/>'
    '<path d="M25 154 H175 L172 160 H28 Z" fill="#c8102e"/>'
    '<path d="M22 140 H178" stroke="url(#mcGold)" stroke-width="3" stroke-linecap="round"/>'
    # mastro com bandeirinha
    '<path d="M172 140 V112" stroke="#6e3b17" stroke-width="3" stroke-linecap="round"/>'
    '<path class="mc-flag" d="M172 112 L192 118 L172 125 Z" fill="url(#mcGold)"/>'
    '</g>'
    # moeda que flutua
    '<g class="mc-coin"><ellipse cx="0" cy="0" rx="11" ry="11" fill="url(#mcGold)" stroke="#9a7410" stroke-width="1.5"/>'
    '<text x="0" y="4" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="11" fill="#6b4c05">R$</text></g>'
    # ondas (na frente do casco)
    '<g clip-path="url(#mcClip)">'
    '<g class="mc-waves">'
    '<path class="mc-wave-a" d="M-40 166 Q-20 156 0 166 T40 166 T80 166 T120 166 T160 166 T200 166 T240 166 V200 H-40 Z" fill="url(#mcSea)"/>'
    '</g>'
    '<g class="mc-waves">'
    '<path class="mc-wave-b" d="M-40 175 Q-20 167 0 175 T40 175 T80 175 T120 175 T160 175 T200 175 T240 175 V200 H-40 Z" fill="#1e40af" opacity=".95"/>'
    '</g>'
    '</g>'
    '</svg>'
)

_FRASES_PADRAO = [
    "Ata cotada, missão cumprida! ⚓",
    "Bora pesquisar preço?",
    "Preço bom é preço pesquisado!",
    "Tudo certo a bordo!",
    "Cotação em dia, processo em paz.",
    "Me clica! Eu pulo. 😄",
]


def _saudacao() -> str:
    """Saudação conforme a hora de Brasília (o servidor costuma estar em UTC)."""
    agora = datetime.now(timezone.utc) + timedelta(hours=-3)
    h = agora.hour
    if h < 5:
        return "Boa madrugada, Comandante!"
    if h < 12:
        return "Bom dia, Comandante! ☀️"
    if h < 18:
        return "Boa tarde, Comandante! ⚓"
    return "Boa noite, Comandante! 🌙"


# ---------------------------------------------------------------------------
# CSS moderno (cai por cima do CSS que cada página já tem)
# ---------------------------------------------------------------------------
_CSS_BASE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --at-gold: #d4af37;
  --at-gold-2: #ffd75e;
  --at-navy: #001a4d;
  --at-navy-2: #0a2540;
  --at-glass: rgba(255,255,255,.055);
  --at-glass-b: rgba(255,255,255,.12);
  --at-radius: 14px;
  --at-ease: cubic-bezier(.22,.8,.3,1);
}

html, body, .stApp, button, input, textarea, select {
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
}

/* ---------- fundo com brilho suave ---------- */
.stApp, [data-testid="stAppViewContainer"] {
  background-image:
    radial-gradient(900px 520px at 88% -8%, rgba(212,175,55,.16), transparent 60%),
    radial-gradient(800px 560px at -6% 8%, rgba(37,99,235,.30), transparent 60%),
    radial-gradient(700px 500px at 50% 112%, rgba(30,64,175,.35), transparent 60%) !important;
  background-attachment: fixed !important;
}

[data-testid="stHeader"] { background: transparent !important; backdrop-filter: none !important; }

/* ---------- entrada suave dos blocos ---------- */
@keyframes at-rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"],
[data-testid="stMainBlockContainer"] > div > [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
  animation: at-rise .55s var(--at-ease) backwards;
}

/* ---------- cabeçalho (hero) ---------- */
.header-container {
  position: relative; overflow: hidden;
  border: 1px solid rgba(212,175,55,.35) !important;
  border-radius: 20px !important;
  box-shadow: 0 18px 50px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.12) !important;
  background:
    radial-gradient(520px 200px at 85% 0%, rgba(212,175,55,.22), transparent 70%),
    linear-gradient(135deg, #00123a 0%, #0b3bd0 100%) !important;
}
.header-container::after {
  content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,.14) 50%, transparent 65%);
  transform: translateX(-120%); animation: at-shine 7s ease-in-out infinite;
}
@keyframes at-shine { 0%, 55% { transform: translateX(-120%); } 85%, 100% { transform: translateX(120%); } }
.sistema-nome {
  background: linear-gradient(180deg, #fff1b0 0%, #d4af37 60%, #b8901f 100%);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent !important;
  text-shadow: none !important;
}

/* ---------- títulos ---------- */
h1, h2, h3 { letter-spacing: -.01em; }
h1 { font-weight: 800 !important; }

/* ---------- cartões ---------- */
.stats-card, .filtros-container,
[data-testid="stMetric"], [data-testid="stForm"] {
  background: var(--at-glass) !important;
  border: 1px solid var(--at-glass-b) !important;
  border-radius: var(--at-radius) !important;
  backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 10px 30px rgba(0,0,0,.28);
  transition: transform .25s var(--at-ease), box-shadow .25s var(--at-ease), border-color .25s;
}
.stats-card, .filtros-container { border-left: 4px solid var(--at-gold) !important; }
.stats-card:hover, [data-testid="stMetric"]:hover {
  transform: translateY(-3px);
  border-color: rgba(212,175,55,.55) !important;
  box-shadow: 0 16px 38px rgba(0,0,0,.38), 0 0 0 1px rgba(212,175,55,.25);
}
[data-testid="stMetric"] { padding: .9rem 1.1rem; }
[data-testid="stMetricValue"] { font-weight: 800; }

/* ---------- botões ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button,
[data-testid^="stBaseButton"] {
  border-radius: 12px !important;
  font-weight: 700 !important;
  letter-spacing: .01em;
  transition: transform .18s var(--at-ease), box-shadow .18s var(--at-ease), filter .18s !important;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(212,175,55,.32) !important;
  filter: brightness(1.05);
}
.stButton > button:active, .stDownloadButton > button:active, .stFormSubmitButton > button:active {
  transform: translateY(0) scale(.97);
  box-shadow: 0 2px 8px rgba(212,175,55,.3) !important;
}
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"] {
  background: linear-gradient(135deg, #ffe27a 0%, #d4af37 55%, #b8901f 100%) !important;
  color: #001a4d !important; border: none !important;
}

/* ---------- campos ---------- */
[data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"],
.stTextInput input, .stNumberInput input, .stTextArea textarea {
  border-radius: 12px !important;
  transition: box-shadow .2s, border-color .2s;
}
[data-baseweb="input"]:focus-within, [data-baseweb="select"] > div:focus-within,
[data-baseweb="textarea"]:focus-within {
  border-color: var(--at-gold) !important;
  box-shadow: 0 0 0 3px rgba(212,175,55,.25) !important;
}

/* ---------- abas ---------- */
[data-baseweb="tab-list"] { gap: .35rem; border-bottom: 1px solid rgba(255,255,255,.1); }
[data-baseweb="tab"] {
  border-radius: 10px 10px 0 0 !important;
  transition: background .2s, color .2s;
}
[data-baseweb="tab"]:hover { background: rgba(212,175,55,.12) !important; }
[data-baseweb="tab-highlight"] { background: linear-gradient(90deg, #ffe27a, #d4af37) !important; height: 3px !important; border-radius: 3px; }

/* ---------- expanders e alertas ---------- */
[data-testid="stExpander"] {
  border-radius: var(--at-radius) !important;
  border: 1px solid var(--at-glass-b) !important;
  background: var(--at-glass);
  overflow: hidden;
}
[data-testid="stExpander"] summary { transition: background .2s; }
[data-testid="stExpander"] summary:hover { background: rgba(212,175,55,.10); }
[data-testid="stAlert"] { border-radius: var(--at-radius) !important; }

/* ---------- tabelas ---------- */
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border-radius: var(--at-radius); overflow: hidden;
  border: 1px solid var(--at-glass-b);
  box-shadow: 0 10px 30px rgba(0,0,0,.28);
}

/* ---------- campos de formulário (visual unificado) ---------- */
[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div,
[data-testid="stDateInput"] [data-baseweb="input"] {
  background: rgba(255,255,255,.07) !important;
  border: 1px solid rgba(255,255,255,.18) !important;
  border-radius: 12px !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.05);
}
[data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover, [data-baseweb="select"] > div:hover {
  border-color: rgba(212,175,55,.6) !important;
}
[data-baseweb="base-input"], [data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
.stTextInput input, .stNumberInput input, .stTextArea textarea, .stDateInput input {
  background: transparent !important; border: none !important; box-shadow: none !important;
  color: #fff !important;
}
[data-baseweb="input"] input::placeholder, [data-baseweb="textarea"] textarea::placeholder { color: rgba(255,255,255,.42) !important; }
[data-testid="stNumberInput"] button { background: rgba(255,255,255,.06) !important; border: none !important; border-radius: 8px !important; }
[data-testid="stNumberInput"] button:hover { background: rgba(212,175,55,.25) !important; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label { font-weight: 600 !important; letter-spacing: .01em; }

/* listas suspensas e tags */
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul {
  background: #0c1a40 !important; border: 1px solid rgba(212,175,55,.35) !important;
  border-radius: 12px !important; box-shadow: 0 18px 40px rgba(0,0,0,.55) !important; overflow: hidden;
}
[data-baseweb="popover"] li { transition: background .15s; }
[data-baseweb="popover"] li:hover, [data-baseweb="popover"] li[aria-selected="true"] { background: rgba(212,175,55,.18) !important; }
[data-baseweb="tag"] {
  background: linear-gradient(135deg, #ffe27a, #d4af37) !important; color: #001a4d !important;
  border-radius: 8px !important; font-weight: 700 !important;
}
[data-baseweb="tag"] span, [data-baseweb="tag"] svg { color: #001a4d !important; fill: #001a4d !important; }

/* envio de arquivos */
[data-testid="stFileUploaderDropzone"] {
  background: rgba(255,255,255,.045) !important;
  border: 1.5px dashed rgba(212,175,55,.55) !important; border-radius: 16px !important;
  transition: background .2s, border-color .2s, box-shadow .2s;
}
[data-testid="stFileUploaderDropzone"]:hover {
  background: rgba(212,175,55,.09) !important; border-color: #ffe27a !important;
  box-shadow: 0 0 0 4px rgba(212,175,55,.12);
}

/* grupos com borda (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div[data-testid="stVerticalBlock"]) {
  border-radius: 16px !important;
}
[data-testid="stVerticalBlockBorderWrapper"][class*="st-"] > [data-testid="stVerticalBlock"] { gap: .9rem; }

/* ---------- abas em pílula ---------- */
[data-baseweb="tab"] { padding: .55rem 1rem !important; font-weight: 600 !important; }
[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(212,175,55,.16) !important; color: #ffe27a !important;
}

/* ---------- métricas ---------- */
[data-testid="stMetricLabel"] p { text-transform: uppercase; font-size: .72rem !important; letter-spacing: .08em; opacity: .85; }
[data-testid="stMetricValue"] { color: #ffe27a !important; }

/* ---------- expanders ---------- */
[data-testid="stExpander"] summary { padding: .7rem 1rem !important; font-weight: 700; }
[data-testid="stExpander"] summary svg { color: var(--at-gold) !important; }
[data-testid="stExpander"][open], [data-testid="stExpander"]:has(details[open]) { border-color: rgba(212,175,55,.45) !important; }

/* ---------- alertas ---------- */
[data-testid="stAlert"], .stAlert {
  background: rgba(255,255,255,.06) !important;
  border: 1px solid var(--at-glass-b) !important; border-left: 4px solid var(--at-gold) !important;
  border-radius: 14px !important; box-shadow: 0 8px 24px rgba(0,0,0,.25);
}

/* ---------- tabelas HTML (markdown, st.table, relatórios) ---------- */
table { border-collapse: separate !important; border-spacing: 0 !important; width: 100%;
  border: 1px solid var(--at-glass-b) !important; border-radius: 14px !important; overflow: hidden;
  background: rgba(255,255,255,.03) !important; box-shadow: 0 10px 30px rgba(0,0,0,.28); }
th {
  background: #0c32a0 !important; color: #ffe27a !important;
  text-transform: uppercase; font-size: .74rem !important; letter-spacing: .07em; font-weight: 800 !important;
  padding: .75rem .9rem !important; border: none !important; border-bottom: 2px solid rgba(212,175,55,.55) !important;
}
td { background: transparent !important; padding: .65rem .9rem !important; border: none !important;
  border-bottom: 1px solid rgba(255,255,255,.07) !important; }
tbody tr:nth-child(even) td { background: rgba(255,255,255,.035) !important; }
tbody tr { transition: background .15s; }
tbody tr:hover td { background: rgba(212,175,55,.12) !important; }
tbody tr:last-child td { border-bottom: none !important; }

/* ---------- tabelas interativas (st.dataframe / data_editor) ---------- */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
  border: 1px solid rgba(212,175,55,.28) !important; border-radius: 14px !important;
}
[data-testid="stElementToolbar"] { border-radius: 10px !important; }

/* ---------- progresso, código, links, divisores ---------- */
[data-testid="stProgress"] [role="progressbar"] > div > div, [data-baseweb="progress-bar"] > div > div {
  background: linear-gradient(90deg, #ffe27a, #d4af37) !important;
}
[data-testid="stCode"] pre, [data-testid="stCode"] { border-radius: 12px !important; }
[data-testid="stMarkdownContainer"] a { color: #ffe27a; text-underline-offset: 3px; transition: color .15s; }
[data-testid="stMarkdownContainer"] a:hover { color: #fff; }
[data-testid="stMain"] hr { border: none !important; height: 1px !important;
  background: linear-gradient(90deg, transparent, rgba(212,175,55,.55), transparent) !important; margin: 1.4rem 0 !important; }

/* ---------- barra de rolagem ---------- */
* { scrollbar-width: thin; scrollbar-color: rgba(212,175,55,.55) transparent; }
::-webkit-scrollbar { width: 9px; height: 9px; }
::-webkit-scrollbar-thumb { background: rgba(212,175,55,.5); border-radius: 9px; }
::-webkit-scrollbar-thumb:hover { background: rgba(212,175,55,.8); }

/* ============================ SIDEBAR ============================ */
[data-testid="stSidebar"] {
  background:
    radial-gradient(420px 260px at 50% -4%, rgba(37,99,235,.28), transparent 70%),
    linear-gradient(180deg, #060b1c 0%, #0a1330 55%, #050810 100%) !important;
  border-right: 1px solid rgba(212,175,55,.55) !important;
  box-shadow: 8px 0 40px rgba(0,0,0,.55) !important;
}
[data-testid="stSidebar"] .stMarkdown h2 {
  font-family: 'Inter', sans-serif !important; font-weight: 800 !important;
  font-size: 13px !important; letter-spacing: .32em !important;
  background: none !important; border: none !important;
  margin: .2rem 0 .2rem !important; padding: 0 !important;
  color: rgba(212,175,55,.9) !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
  position: relative;
  justify-content: flex-start !important;
  border-radius: 12px !important;
  padding: .5rem .8rem !important;
  transition: transform .22s var(--at-ease), background .22s, box-shadow .22s, border-color .22s !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]::before {
  content: ""; position: absolute; left: 0; top: 22%; bottom: 22%; width: 3px; border-radius: 3px;
  background: var(--at-gold); transform: scaleY(0); transition: transform .22s var(--at-ease);
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:not([href*="Aprendendo_a_usar"]):not([href*="Sobre_o_projeto"]):not([href*="Suporte_ao_sistema"]) {
  border: 1px solid rgba(255,255,255,.07) !important;
  background: rgba(255,255,255,.045) !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
  transform: translateX(6px) !important;
  border-color: #d4af37 !important;
  box-shadow: 0 6px 20px rgba(212,175,55,.22) !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:not([href*="Aprendendo_a_usar"]):not([href*="Sobre_o_projeto"]):not([href*="Suporte_ao_sistema"]):hover {
  background: rgba(212,175,55,.10) !important;
  border-color: #d4af37 !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover::before { transform: scaleY(1); }
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"]:not([href*="Aprendendo_a_usar"]):not([href*="Sobre_o_projeto"]):not([href*="Suporte_ao_sistema"]) {
  background: linear-gradient(135deg, #ffe27a 0%, #d4af37 60%, #b8901f 100%) !important;
  border-color: #ffe27a !important;
  box-shadow: 0 8px 22px rgba(212,175,55,.42) !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p { font-weight: 700; }

/* Aprendendo a usar / Sobre / Suporte: mantêm a cor; no hover só ganham o realce dourado */
[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][data-testid="stPageLink-NavLink"]:hover,
[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][data-testid="stPageLink-NavLink"]:hover,
[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][data-testid="stPageLink-NavLink"]:hover {
  border-color: #d4af37 !important;
  box-shadow: 0 0 0 1px #d4af37, 0 6px 20px rgba(212,175,55,.28) !important;
}
[data-testid="stSidebar"] a[href*="Aprendendo_a_usar"][data-testid="stPageLink-NavLink"]:hover *,
[data-testid="stSidebar"] a[href*="Sobre_o_projeto"][data-testid="stPageLink-NavLink"]:hover *,
[data-testid="stSidebar"] a[href*="Suporte_ao_sistema"][data-testid="stPageLink-NavLink"]:hover * {
  text-shadow: none !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.08) !important; margin: .7rem 0 !important; }
.sidebar-footer { border-top: 1px solid rgba(255,255,255,.08) !important; color: #7b86a6 !important; }

/* ---------- mascote ---------- */
.mc-root { position: relative; text-align: center; padding: .6rem 0 .2rem; user-select: none; }
.mc-stage {
  position: relative; width: 168px; margin: 0 auto; cursor: pointer;
  filter: drop-shadow(0 10px 18px rgba(0,0,0,.45));
  -webkit-tap-highlight-color: transparent;
}
.mc-svg { width: 100%; height: auto; display: block; overflow: visible; }
.mc-stage::before {
  content: ""; position: absolute; inset: 6% -6% 0; border-radius: 50%; z-index: 0;
  background: radial-gradient(closest-side, rgba(212,175,55,.28), transparent 72%);
  animation: mc-halo 4.2s ease-in-out infinite;
}
.mc-svg { position: relative; z-index: 1; }
@keyframes mc-halo { 0%, 100% { opacity: .55; transform: scale(.94); } 50% { opacity: 1; transform: scale(1.06); } }
.mc-boat { animation: mc-rock 3.6s ease-in-out infinite; transform-origin: 100px 168px; }
@keyframes mc-rock { 0%, 100% { transform: translateY(0) rotate(-3deg); } 50% { transform: translateY(-4px) rotate(3deg); } }
.mc-flag { transform-box: fill-box; transform-origin: left center; animation: mc-flag 1.1s ease-in-out infinite; }
@keyframes mc-flag { 0%, 100% { transform: skewY(0) scaleX(1); } 50% { transform: skewY(-8deg) scaleX(.86); } }
.mc-puff { opacity: 0; animation: mc-smoke 3.2s ease-out infinite; }
.mc-puff.p2 { animation-delay: 1.05s; } .mc-puff.p3 { animation-delay: 2.1s; }
@keyframes mc-smoke { 0% { opacity: 0; transform: translate(0, 0) scale(.5); } 15% { opacity: .85; } 100% { opacity: 0; transform: translate(-6px, -34px) scale(2.1); } }
.mc-wave { transform-box: view-box; transform-origin: 134px 116px; animation: mc-wave 2.6s ease-in-out infinite; }
@keyframes mc-wave { 0%, 55%, 100% { transform: rotate(0); } 62% { transform: rotate(-16deg); } 70% { transform: rotate(10deg); } 78% { transform: rotate(-14deg); } 86% { transform: rotate(8deg); } 93% { transform: rotate(-4deg); } }
.mc-eye { animation: mc-blink 5s infinite; transform-origin: center; transform-box: fill-box; }
@keyframes mc-blink { 0%, 93%, 100% { transform: scaleY(1); } 96% { transform: scaleY(.08); } }
.mc-pupil, .mc-glint { transition: transform .12s ease-out; }
.mc-coin { transform: translate(30px, 40px); animation: mc-coin 3.6s ease-in-out infinite; transform-box: view-box; }
@keyframes mc-coin { 0%, 100% { transform: translate(30px, 40px) rotateY(0); } 50% { transform: translate(30px, 30px) rotateY(180deg); } }
.mc-waves { overflow: hidden; }
.mc-wave-a { animation: mc-sea 5s linear infinite; }
.mc-wave-b { animation: mc-sea 3.4s linear infinite reverse; }
@keyframes mc-sea { from { transform: translateX(0); } to { transform: translateX(-80px); } }
.mc-stage.mc-jump .mc-svg { animation: mc-jump .7s cubic-bezier(.3,1.6,.5,1); }
@keyframes mc-jump { 0% { transform: translateY(0) scale(1, 1); } 25% { transform: translateY(0) scale(1.08, .88); } 55% { transform: translateY(-22px) scale(.94, 1.08); } 100% { transform: translateY(0) scale(1, 1); } }
.mc-stage.mc-jump .mc-mouth { d: path("M96 98 Q106 114 118 96"); }

.mc-bubble {
  position: relative; display: inline-block; max-width: 92%;
  margin: .7rem auto 0; padding: .45rem .75rem;
  font: 600 11.5px/1.3 'Inter', sans-serif; color: #10224f;
  background: linear-gradient(135deg, #fff7d1, #ffe27a);
  border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,.35);
  transition: opacity .35s, transform .35s var(--at-ease);
}
.mc-bubble::before {
  content: ""; position: absolute; top: -6px; left: 50%; margin-left: -6px;
  border: 6px solid transparent; border-top: 0; border-bottom-color: #fff7d1;
}
.mc-bubble.mc-out { opacity: 0; transform: translateY(4px) scale(.96); }

@media (prefers-reduced-motion: reduce) {
  .mc-root *, .header-container::after { animation: none !important; transition: none !important; }
  [data-testid="stMainBlockContainer"] * { animation: none !important; }
}

/* ---------- elementos injetados pelo JS ---------- */
#at-progress {
  position: fixed; top: 0; left: 0; height: 3px; width: 0; z-index: 999999; pointer-events: none;
  background: linear-gradient(90deg, #ffe27a, #d4af37, #2563eb);
  box-shadow: 0 0 10px rgba(212,175,55,.8); transition: width .08s linear;
}
#at-top {
  position: fixed; right: 22px; bottom: 22px; z-index: 999998;
  width: 44px; height: 44px; border-radius: 50%; border: 1px solid rgba(212,175,55,.7);
  background: linear-gradient(135deg, #ffe27a, #d4af37); color: #001a4d;
  font: 800 20px/1 'Inter', sans-serif; cursor: pointer;
  box-shadow: 0 10px 26px rgba(0,0,0,.45);
  opacity: 0; transform: translateY(16px) scale(.8); pointer-events: none;
  transition: opacity .25s, transform .25s var(--at-ease);
}
#at-top.show { opacity: 1; transform: none; pointer-events: auto; }
#at-top:hover { transform: translateY(-3px) scale(1.06); }

/* iframe do JavaScript: sem ocupar espaço */
[data-testid="stElementContainer"]:has(> iframe[height="0"]),
[data-testid="stElementContainer"]:has(iframe[height="0"]) {
  position: absolute !important; width: 0 !important; height: 0 !important;
  margin: 0 !important; padding: 0 !important; overflow: hidden !important;
}
</style>
"""

_KEYFRAME = re.compile(r"^(from|to|\d+(\.\d+)?%(\s*,\s*\d+(\.\d+)?%)*)$")


def _prefixar(css: str) -> str:
    """Prefixa os seletores com ``:root:root`` para vencer o CSS próprio de cada
    página, que vem depois no DOM (a sidebar é renderizada antes do conteúdo)."""
    saida, i = [], 0
    for m in re.finditer(r"([^{};]+)\{", css):
        sel = m.group(1)
        corpo = sel.strip()
        # remove comentários /* ... */ do cabeçalho para analisar
        limpo = re.sub(r"/\*.*?\*/", "", corpo, flags=re.S).strip()
        saida.append(css[i:m.start()])
        i = m.end()
        if limpo.startswith("@") or _KEYFRAME.match(limpo) or not limpo:
            saida.append(m.group(0))
            continue
        partes = []
        for parte in limpo.split(","):
            t = parte.strip()
            if t.startswith(("html", ":root", "*", "::", "body")):
                partes.append(t)
            else:
                partes.append(":root:root " + t)
        saida.append(",\n".join(partes) + " {")
    saida.append(css[i:])
    return "".join(saida)


_CSS = _prefixar(_CSS_BASE)

# ---------------------------------------------------------------------------
# JavaScript: injetado no documento principal (e não no iframe), de forma
# idempotente, para sobreviver às reexecuções que o Streamlit faz.
# ---------------------------------------------------------------------------
_JS = r"""
(function () {
  const W = window.parent, D = W.document;
  if (!D.getElementById('at-ui-js')) {
    const s = D.createElement('script');
    s.id = 'at-ui-js';
    s.textContent = '(' + function () {
      if (window.__ataUI) return; window.__ataUI = true;
      const $ = (q) => document.querySelector(q);

      /* barra de progresso + voltar ao topo */
      const bar = document.createElement('div'); bar.id = 'at-progress';
      const top = document.createElement('button'); top.id = 'at-top'; top.type = 'button';
      top.title = 'Voltar ao topo'; top.setAttribute('aria-label', 'Voltar ao topo'); top.textContent = '↑';
      document.body.append(bar, top);
      const scroller = () => $('[data-testid="stMain"]') || $('section.main') || document.scrollingElement;
      top.addEventListener('click', () => scroller().scrollTo({ top: 0, behavior: 'smooth' }));
      document.addEventListener('scroll', (e) => {
        const el = (e.target && e.target.scrollHeight) ? e.target : document.scrollingElement;
        if (!el || el.closest && el.closest('[data-testid="stSidebar"]')) return;
        const max = el.scrollHeight - el.clientHeight;
        bar.style.width = max > 0 ? Math.min(100, (el.scrollTop / max) * 100) + '%' : '0';
        top.classList.toggle('show', el.scrollTop > 400);
      }, true);

      /* olhos do mascote seguem o mouse */
      document.addEventListener('mousemove', (e) => {
        const st = $('.mc-stage'); if (!st) return;
        const r = st.getBoundingClientRect();
        const dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height * .4);
        const d = Math.hypot(dx, dy) || 1, k = Math.min(1, d / 220);
        const x = (dx / d) * 3.6 * k, y = (dy / d) * 3.6 * k;
        st.querySelectorAll('.mc-pupil').forEach((p) => p.style.transform = 'translate(' + x + 'px,' + y + 'px)');
        st.querySelectorAll('.mc-glint').forEach((p) => p.style.transform = 'translate(' + x * .6 + 'px,' + y * .6 + 'px)');
      }, { passive: true });

      /* balão de falas */
      let idx = 0;
      const frases = () => { try { return JSON.parse($('.mc-root').dataset.frases); } catch (_) { return []; } };
      function falar(texto) {
        const b = $('.mc-bubble'); if (!b) return;
        b.classList.add('mc-out');
        setTimeout(() => { b.textContent = texto; b.classList.remove('mc-out'); }, 280);
      }
      setInterval(() => {
        const f = frases(); if (!f.length || document.hidden) return;
        idx = (idx + 1) % f.length; falar(f[idx]);
      }, 7000);

      /* clique: pula e fala */
      document.addEventListener('click', (e) => {
        const st = e.target.closest && e.target.closest('.mc-stage'); if (!st) return;
        st.classList.remove('mc-jump'); void st.offsetWidth; st.classList.add('mc-jump');
        setTimeout(() => st.classList.remove('mc-jump'), 800);
        const f = frases(); if (f.length) { idx = (idx + 1) % f.length; falar(f[idx]); }
      });
    }.toString() + ')();';
    D.head.appendChild(s);
  }
})();
"""


def aplicar_tema() -> None:
    """Injeta só o CSS moderno + o JavaScript (para páginas sem mascote)."""
    st.markdown(_CSS, unsafe_allow_html=True)
    components.html(f"<script>{_JS}</script>", height=0)


def sidebar_mascote() -> None:
    """Mascote animado no topo da sidebar (substitui a imagem estática do acanto).

    Deve ser chamado dentro de ``with st.sidebar:``.
    """
    aplicar_tema()
    frases = [_saudacao()] + _FRASES_PADRAO
    st.markdown(
        '<div class="mc-root" data-frases=\'' + json.dumps(frases, ensure_ascii=False).replace("'", "&#39;") + "'>"
        '<div class="mc-stage" title="Clique em mim!">' + _MASCOTE_SVG + "</div>"
        '<div class="mc-bubble">' + frases[0] + "</div>"
        "</div>",
        unsafe_allow_html=True,
    )
