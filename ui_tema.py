"""Tema visual do AtaCotada: mascote animado, visual moderno e JavaScript.

Somente apresentação. Nenhuma regra de negócio passa por aqui.

Uso (dentro de ``with st.sidebar:``, no lugar da imagem do acanto):

    from ui_tema import sidebar_mascote
    sidebar_mascote()

A chamada injeta, uma vez por execução da página:
  * o CSS moderno (cartões em vidro, botões, campos, abas, tabelas...);
  * o mascote "Ata", o balconista de preços (SVG animado) no topo da sidebar;
  * o JavaScript de interação (olhos que seguem o mouse, balão de falas,
    barra de progresso de rolagem e botão "voltar ao topo").
"""
from __future__ import annotations

import json
import re

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Mascote (SVG inline, animado só com CSS; os olhos são guiados pelo JS)
# ---------------------------------------------------------------------------
_MASCOTE_SVG = (
    '<svg class="mc-svg" viewBox="0 0 200 190" xmlns="http://www.w3.org/2000/svg" '
    'role="img" aria-label="Mascote Ata, o balconista de preços">'
    '<defs>'
    '<linearGradient id="mcGold" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#ffe27a"/><stop offset="1" stop-color="#c99a1b"/></linearGradient>'
    '<linearGradient id="mcNavy" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#1d4ed8"/><stop offset="1" stop-color="#0b2a78"/></linearGradient>'
    '<linearGradient id="mcMetal" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#b7cbee"/></linearGradient>'
    '<linearGradient id="mcScreen" x1="0" y1="0" x2="0" y2="1">'
    '<stop offset="0" stop-color="#14245c"/><stop offset="1" stop-color="#060d2b"/></linearGradient>'
    '</defs>'
    # robô balconista (flutua de leve)
    '<g class="mc-boat">'
    # corpo e avental
    '<path d="M62 150 V128 C62 114 76 108 100 108 C124 108 138 114 138 128 V150 Z" fill="url(#mcNavy)"/>'
    '<path d="M80 112 H120 L125 150 H75 Z" fill="#fff"/>'
    '<path d="M80 112 Q100 127 120 112" stroke="#d4af37" stroke-width="2.6" fill="none" stroke-linecap="round"/>'
    '<rect x="102" y="129" width="16" height="10" rx="2.5" fill="#0b2a78"/>'
    '<text x="110" y="136.6" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="6.2" fill="#ffe27a">AC</text>'
    '<rect x="92" y="100" width="16" height="12" rx="4" fill="#8fa8d6"/>'
    # orelhas e cabeça
    '<rect x="49" y="62" width="11" height="28" rx="5.5" fill="url(#mcGold)"/>'
    '<rect x="140" y="62" width="11" height="28" rx="5.5" fill="url(#mcGold)"/>'
    '<rect x="56" y="38" width="88" height="68" rx="28" fill="url(#mcMetal)" stroke="#8fa8d6" stroke-width="1.5"/>'
    # tela do rosto
    '<rect x="67" y="50" width="66" height="46" rx="19" fill="url(#mcScreen)"/>'
    '<path d="M77 57 Q100 51 123 57" stroke="#fff" stroke-opacity=".14" stroke-width="3" fill="none" stroke-linecap="round"/>'
    '<g transform="translate(86 70)"><g class="mc-eye">'
    '<ellipse class="mc-pupil" rx="6.6" ry="8.6" fill="#ffe27a"/><circle class="mc-glint" cx="-1.8" cy="-2.6" r="2" fill="#fff"/>'
    '</g></g>'
    '<g transform="translate(114 70)"><g class="mc-eye">'
    '<ellipse class="mc-pupil" rx="6.6" ry="8.6" fill="#ffe27a"/><circle class="mc-glint" cx="-1.8" cy="-2.6" r="2" fill="#fff"/>'
    '</g></g>'
    '<ellipse cx="78" cy="83" rx="4.4" ry="2.6" fill="#ff8fa3" opacity=".6"/>'
    '<ellipse cx="122" cy="83" rx="4.4" ry="2.6" fill="#ff8fa3" opacity=".6"/>'
    '<path class="mc-mouth" d="M92 83 Q100 91 108 83" stroke="#ffe27a" stroke-width="2.8" fill="none" stroke-linecap="round"/>'
    # luz que pisca na orelha
    '<circle class="mc-led" cx="145.5" cy="76" r="2.6" fill="#34d399"/>'
    # boné de marinheiro
    '<g transform="rotate(-4 100 34)">'
    '<path d="M64 44 C64 12 136 12 136 44 C136 48 64 48 64 44 Z" fill="#fff" stroke="#d6e0f5" stroke-width="1"/>'
    '<rect x="62" y="38" width="76" height="9" rx="4.5" fill="url(#mcNavy)"/>'
    '<g transform="translate(100 26) scale(.52)">'
    '<circle cy="-9" r="4.2" fill="none" stroke="url(#mcGold)" stroke-width="3"/>'
    '<path d="M0 -5 V17 M-9 4 H9 M-14 9 C-12 18 -4 19 0 17 C4 19 12 18 14 9" '
    'stroke="url(#mcGold)" stroke-width="3.2" fill="none" stroke-linecap="round"/>'
    '</g></g>'
    # braço esquerdo: lupa (pesquisa de preços)
    '<g class="mc-lens">'
    '<path d="M68 122 Q52 122 49 106" stroke="#0b2a78" stroke-width="12" stroke-linecap="round" fill="none"/>'
    '<path d="M46 98 L34 80" stroke="#7a4620" stroke-width="5" stroke-linecap="round"/>'
    '<circle cx="49" cy="100" r="7.5" fill="#fff" stroke="#8fa8d6" stroke-width="1.4"/>'
    '<circle cx="27" cy="68" r="15" fill="#9fdcff" fill-opacity=".30" stroke="url(#mcGold)" stroke-width="4.5"/>'
    '</g>'
    # braço direito: segura a etiqueta de preço
    '<path d="M132 122 Q148 122 151 106" stroke="#0b2a78" stroke-width="12" stroke-linecap="round" fill="none"/>'
    '<circle cx="151" cy="100" r="7.5" fill="#fff" stroke="#8fa8d6" stroke-width="1.4"/>'
    '</g>'
    # etiqueta de preço balançando (preços que se alternam)
    '<g class="mc-tag">'
    '<path d="M151 104 L158 114" stroke="#c99a1b" stroke-width="1.6"/>'
    '<path d="M148 122 L156 113 H186 Q190 113 190 117 V133 Q190 137 186 137 H152 Q148 137 148 133 Z" fill="#fff7d1" stroke="#d4af37" stroke-width="1.6"/>'
    '<circle cx="156" cy="121" r="2" fill="#c99a1b"/>'
    '<g font-family="Arial Black,Arial,sans-serif" font-size="9" fill="#0b2a78" text-anchor="middle">'
    '<text class="pr p1" x="173" y="130" textLength="30" lengthAdjust="spacingAndGlyphs">R$ 12,90</text>'
    '<text class="pr p2" x="173" y="130" textLength="26" lengthAdjust="spacingAndGlyphs">R$ 8,45</text>'
    '<text class="pr p3" x="173" y="130" textLength="30" lengthAdjust="spacingAndGlyphs">R$ 19,00</text>'
    '</g></g>'
    # balcão
    '<rect x="10" y="136" width="180" height="10" rx="5" fill="url(#mcGold)"/>'
    '<path d="M16 146 H184 V180 Q184 185 179 185 H21 Q16 185 16 180 Z" fill="url(#mcNavy)"/>'
    '<rect x="24" y="153" width="152" height="24" rx="7" fill="none" stroke="#d4af37" stroke-opacity=".65" stroke-width="1.3"/>'
    '<text x="100" y="170" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="11" textLength="92" lengthAdjust="spacingAndGlyphs" fill="#ffe27a">ATACOTADA</text>'
    # sineta do balcão
    '<g class="mc-bell"><path d="M26 136 C26 122 46 122 46 136 Z" fill="url(#mcGold)" stroke="#9a7410" stroke-width="1"/>'
    '<rect x="34" y="118" width="4" height="5" rx="2" fill="#9a7410"/></g>'
    # moeda que flutua
    '<g class="mc-coin"><ellipse cx="0" cy="0" rx="11" ry="11" fill="url(#mcGold)" stroke="#9a7410" stroke-width="1.5"/>'
    '<text x="0" y="4" text-anchor="middle" font-family="Arial Black,Arial,sans-serif" font-size="11" fill="#6b4c05">R$</text></g>'
    '</svg>'
)

_FRASES_PADRAO = [
    "Cote agora! Vamos nessa?",
    "Trabalho de semanas em minutos!",
    "Preço bom é preço pesquisado! 🔎",
    "Deixa que eu procuro no Compras.gov.",
    "Ata cotada, missão cumprida! ⚓",
    "Três preços na mão e a cotação sai.",
    "Me clica! Eu falo e toco a sineta. 🔔",
    "Já conferiu o CATMAT do seu item?",
    "Sem pesquisa de preços, sem processo!",
    "Média ou mediana? Eu calculo as duas.",
    "Preço fora da curva? Eu te aviso. 📈",
    "Com pressa? Tem a Cotação Rápida! ⚡",
    "Atas vigentes esperando por você. 🤝",
    "Dúvida de licitação? Pergunte ao Babilaca! 🧠",
    "Tem vídeo-aula em Aprendendo a usar. 🎓",
    "Nota fiscal também é fonte de preço. 📄",
    "Corrija pelo IPCA e fique tranquilo. 📊",
    "Cada centavo economizado é da Marinha. ⚓",
    "Fornecedor bom a gente acha por aqui. 🏢",
    "Cotação bem feita, processo aprovado!",
    "Adesão a ata? Eu monto itens, vantajosidade e ofício. 🤝",
    "CATMAT ou CATSERV? Eu sugiro o código certo. 🔎",
    "DFD, ETP, TR e ofícios já saem no modelo da Marinha! 📄",
]


def _saudacao() -> str:
    """Saudação do mascote (sempre "Bom dia", em qualquer horário)."""
    return "Bom dia, Comandante! ☀️"


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
.mc-boat { animation: mc-bob 3.2s ease-in-out infinite; }
@keyframes mc-bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-3px); } }
.mc-lens { transform-box: view-box; transform-origin: 56px 112px; animation: mc-lens 4.4s ease-in-out infinite; }
@keyframes mc-lens { 0%, 100% { transform: rotate(0); } 25% { transform: rotate(-9deg); } 55% { transform: rotate(7deg); } 80% { transform: rotate(-3deg); } }
.mc-tag { transform-box: view-box; transform-origin: 151px 104px; animation: mc-swing 2.8s ease-in-out infinite; }
@keyframes mc-swing { 0%, 100% { transform: rotate(-5deg); } 50% { transform: rotate(5deg); } }
.mc-tag .pr { opacity: 0; animation: mc-price 7.5s infinite; }
.mc-tag .pr.p1 { animation-delay: 0s; } .mc-tag .pr.p2 { animation-delay: 2.5s; } .mc-tag .pr.p3 { animation-delay: 5s; }
@keyframes mc-price { 0% { opacity: 0; } 4%, 30% { opacity: 1; } 34%, 100% { opacity: 0; } }
.mc-led { animation: mc-led 1.6s ease-in-out infinite; }
@keyframes mc-led { 0%, 100% { opacity: .35; } 50% { opacity: 1; } }
.mc-bell { transform-box: fill-box; transform-origin: 50% 100%; animation: mc-ding 6s ease-in-out infinite; }
@keyframes mc-ding { 0%, 88%, 100% { transform: rotate(0); } 90% { transform: rotate(-9deg); } 93% { transform: rotate(8deg); } 96% { transform: rotate(-4deg); } }
.mc-eye { animation: mc-blink 5s infinite; transform-origin: center; transform-box: fill-box; }
@keyframes mc-blink { 0%, 93%, 100% { transform: scaleY(1); } 96% { transform: scaleY(.08); } }
.mc-pupil, .mc-glint { transition: transform .12s ease-out; }
.mc-coin { transform: translate(170px, 36px); animation: mc-coin 3.6s ease-in-out infinite; transform-box: view-box; }
@keyframes mc-coin { 0%, 100% { transform: translate(170px, 36px) rotateY(0); } 50% { transform: translate(170px, 26px) rotateY(180deg); } }
.mc-stage.mc-jump .mc-bell { animation: mc-ding-fast .7s ease-in-out; }
@keyframes mc-ding-fast { 0%, 100% { transform: rotate(0); } 15% { transform: rotate(-16deg); } 35% { transform: rotate(14deg); } 55% { transform: rotate(-9deg); } 75% { transform: rotate(5deg); } }
.mc-stage.mc-jump .mc-svg { animation: mc-jump .7s cubic-bezier(.3,1.6,.5,1); }
@keyframes mc-jump { 0% { transform: translateY(0) scale(1, 1); } 25% { transform: translateY(0) scale(1.08, .88); } 55% { transform: translateY(-22px) scale(.94, 1.08); } 100% { transform: translateY(0) scale(1, 1); } }
.mc-stage.mc-jump .mc-mouth { d: path("M91 82 Q100 98 109 82"); }

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


/* =================== páginas informativas: Sobre / Suporte / Aprendendo =================== */
.sp-header, .su-header, .tut-header {
  position: relative; overflow: hidden; isolation: isolate;
  border-radius: 24px !important; padding: 2rem 2.2rem !important; margin-bottom: 1.6rem !important;
  border: 1px solid rgba(255,255,255,.22) !important;
  box-shadow: 0 24px 60px rgba(0,0,0,.45), inset 0 1px 0 rgba(255,255,255,.3) !important;
}
.sp-header::before, .su-header::before, .tut-header::before {
  content: ""; position: absolute; z-index: -1; right: -70px; top: -90px; width: 320px; height: 320px; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,255,255,.30), rgba(255,255,255,0) 68%);
  animation: at-float 9s ease-in-out infinite;
}
.sp-header::after, .su-header::after, .tut-header::after {
  content: ""; position: absolute; z-index: -1; left: -60px; bottom: -120px; width: 380px; height: 260px; border-radius: 50%;
  background: radial-gradient(circle, rgba(0,0,0,.28), rgba(0,0,0,0) 70%);
}
@keyframes at-float { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(-24px, 18px); } }
.sp-header h1, .su-header h1, .tut-header h1 {
  font-size: 2.1rem !important; font-weight: 900 !important; letter-spacing: -.02em; text-shadow: 0 3px 14px rgba(0,0,0,.28);
}
.sp-header p, .su-header p, .tut-header p { max-width: 62rem; }
.sp-header p.sp-lead { font-size: 1.05rem !important; border-top: 1px solid rgba(255,255,255,.4) !important; }
.sp-chips { display: flex; flex-wrap: wrap; gap: .55rem; margin-top: 1.1rem; }
.sp-chips span {
  background: rgba(255,255,255,.18); border: 1px solid rgba(255,255,255,.38); border-radius: 999px;
  padding: .3rem .85rem; font-size: .8rem; font-weight: 700; color: #fff; backdrop-filter: blur(6px);
}

.sp-panel, .su-panel, .sp-prop {
  position: relative; border-radius: 20px !important; padding: 1.35rem 1.6rem !important; margin: 1rem 0 1.3rem !important;
  background: linear-gradient(160deg, rgba(255,255,255,.075), rgba(255,255,255,.025)) !important;
  border: 1px solid var(--at-glass-b) !important; border-left: 1px solid var(--at-glass-b) !important;
  box-shadow: 0 14px 40px rgba(0,0,0,.32);
  transition: transform .25s var(--at-ease), box-shadow .25s var(--at-ease), border-color .25s;
}
.sp-panel:hover, .su-panel:hover { transform: translateY(-2px); border-color: rgba(212,175,55,.4) !important; box-shadow: 0 20px 48px rgba(0,0,0,.4); }
.sp-panel::before, .su-panel::before {
  content: ""; position: absolute; left: 1.6rem; top: 0; width: 56px; height: 4px; border-radius: 0 0 6px 6px;
  background: linear-gradient(90deg, #ffe27a, #d4af37);
}
.sp-prop { border-color: rgba(212,175,55,.55) !important;
  background: radial-gradient(500px 200px at 100% 0%, rgba(212,175,55,.22), transparent 70%), linear-gradient(160deg, rgba(255,255,255,.07), rgba(255,255,255,.02)) !important; }
.sp-panel h3, .su-panel h3, .sp-prop h3 { font-size: 1.2rem !important; font-weight: 800 !important; letter-spacing: -.01em; margin: .5rem 0 .7rem !important; text-shadow: none !important; }
.sp-panel p, .su-panel p, .sp-panel li, .su-panel li { font-size: .95rem !important; line-height: 1.7 !important; color: #e3ecfb !important; }
.sp-panel ul, .su-panel ul { list-style: none !important; margin: .5rem 0 0 !important; padding: 0 !important; }
.sp-panel li, .su-panel li { position: relative; padding-left: 1.6rem; margin: .45rem 0; }
.sp-panel li::before, .su-panel li::before {
  content: "⚓"; position: absolute; left: 0; top: .05rem; font-size: .8rem; color: var(--at-gold);
}
.sp-prop .destaque { border-left: 4px solid var(--at-gold) !important; background: rgba(212,175,55,.1); border-radius: 0 12px 12px 0; padding: .7rem 1rem !important; }

/* cartões de ferramentas / ações */
.sp-grid, .su-grid { gap: .9rem !important; margin-top: .9rem !important; }
.sp-card, .su-card {
  display: flex; gap: .9rem; align-items: flex-start;
  background: linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.025)) !important;
  border: 1px solid var(--at-glass-b) !important; border-radius: 16px !important; padding: 1rem 1.05rem !important;
  transition: transform .22s var(--at-ease), border-color .22s, box-shadow .22s, background .22s;
}
.sp-card:hover, .su-card:hover {
  transform: translateY(-4px); border-color: rgba(212,175,55,.65) !important;
  box-shadow: 0 16px 34px rgba(0,0,0,.4), 0 0 0 1px rgba(212,175,55,.25);
  background: linear-gradient(160deg, rgba(212,175,55,.14), rgba(255,255,255,.03)) !important;
}
.sp-card .ic, .su-card .ic {
  flex: none; width: 46px; height: 46px; border-radius: 14px; display: grid; place-items: center; font-size: 1.45rem;
  background: linear-gradient(135deg, rgba(255,226,122,.28), rgba(212,175,55,.10)); border: 1px solid rgba(212,175,55,.45);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.25); transition: transform .3s var(--at-ease);
}
.sp-card:hover .ic, .su-card:hover .ic { transform: rotate(-8deg) scale(1.1); }
.sp-card .t, .su-card .t { font-size: 1rem !important; letter-spacing: -.01em; }
.sp-card .d, .su-card .d { font-size: .84rem !important; line-height: 1.5 !important; color: #b9cbe6 !important; }
.sp-aviso { border-radius: 18px !important; padding: 1.1rem 1.4rem !important; border-left: 5px solid #ef4444 !important;
  background: linear-gradient(160deg, rgba(239,68,68,.16), rgba(239,68,68,.05)) !important; }
.su-msg { border-radius: 14px !important; }

/* botões de link (WhatsApp / compartilhar) */
[data-testid="stLinkButton"] a, a[data-testid="stBaseLinkButton-primary"], a[data-testid="stBaseLinkButton-secondary"] {
  border-radius: 16px !important; padding: .95rem 1.2rem !important; font-size: 1.05rem !important; font-weight: 800 !important;
  transition: transform .2s var(--at-ease), box-shadow .2s !important;
}
[data-testid="stLinkButton"] a:hover { transform: translateY(-3px); box-shadow: 0 14px 30px rgba(37,211,102,.35) !important; }
a[data-testid="stBaseLinkButton-primary"] { animation: at-pulse 2.8s ease-in-out infinite; }
@keyframes at-pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(37,211,102,.45); } 60% { box-shadow: 0 0 0 14px rgba(37,211,102,0); } }

/* cartões de contribuidores (botões de download com PDF) */
[data-testid="stDownloadButton"] button {
  border-radius: 18px !important; min-height: 120px;
  background: linear-gradient(160deg, rgba(255,255,255,.09), rgba(255,255,255,.03)) !important;
  border: 1px solid rgba(212,175,55,.5) !important;
}
[data-testid="stDownloadButton"] button:hover { transform: translateY(-4px); border-color: #ffe27a !important; }

/* Aprendendo a usar */
.tut-card {
  border-radius: 18px !important; padding: 1rem 1.2rem !important; margin: .6rem 0 !important; gap: 1rem !important;
  background: linear-gradient(160deg, rgba(255,255,255,.08), rgba(255,255,255,.025)) !important;
  border: 1px solid var(--at-glass-b) !important;
  transition: transform .22s var(--at-ease), border-color .22s, box-shadow .22s;
}
.tut-card:hover { transform: translateX(6px); border-color: rgba(250,204,21,.7) !important; box-shadow: 0 12px 30px rgba(0,0,0,.38); }
.tut-card.on { border-color: rgba(250,204,21,.6) !important; box-shadow: 0 0 0 1px rgba(250,204,21,.25), 0 10px 28px rgba(0,0,0,.3) !important; }
.tut-card .ic { width: 50px; height: 50px; border-radius: 15px; display: grid; place-items: center; font-size: 1.6rem;
  background: linear-gradient(135deg, rgba(250,204,21,.3), rgba(250,204,21,.08)); border: 1px solid rgba(250,204,21,.5); }
.tut-tag { padding: .25rem .75rem !important; letter-spacing: .06em; }
.tut-tag.ok { background: linear-gradient(135deg, #fde047, #eab308) !important; box-shadow: 0 4px 12px rgba(250,204,21,.35); }
[data-testid="stIFrame"], iframe[title="st.iframe"] { border-radius: 18px; }

/* iframe do JavaScript (só o nosso, marcado no conteúdo): sem ocupar espaço */
[data-testid="stElementContainer"]:has(> iframe[srcdoc*="__ata_ui__"]),
[data-testid="stElementContainer"]:has(iframe[srcdoc*="__ata_ui__"]) {
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

      /* som da sineta (Web Audio) e voz "Vamos cotar!" (síntese de fala do navegador) */
      function ding() {
        try {
          const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
          const c = window.__ataAC = window.__ataAC || new AC();
          if (c.state === 'suspended') c.resume();
          const t = c.currentTime;
          [[1318.5, .30], [1976, .16], [2637, .07]].forEach((n) => {
            const o = c.createOscillator(), g = c.createGain();
            o.type = 'sine'; o.frequency.value = n[0];
            g.gain.setValueAtTime(.0001, t);
            g.gain.exponentialRampToValueAtTime(n[1], t + .01);
            g.gain.exponentialRampToValueAtTime(.0001, t + 1.1);
            o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + 1.15);
          });
        } catch (_) {}
      }
      function dizer(texto) {
        try {
          const ss = window.speechSynthesis; if (!ss) return;
          ss.cancel();
          const u = new SpeechSynthesisUtterance(texto);
          u.lang = 'pt-BR'; u.rate = 1.05; u.pitch = 1.3;
          const vozes = ss.getVoices();
          const v = vozes.find((x) => /pt[-_]BR/i.test(x.lang)) || vozes.find((x) => /^pt/i.test(x.lang));
          if (v) u.voice = v;
          setTimeout(() => ss.speak(u), 380);
        } catch (_) {}
      }

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
        falar('Vamos cotar! 🔔'); ding(); dizer('Vamos cotar!');
      });
    }.toString() + ')();';
    D.head.appendChild(s);
  }
})();
"""


def aplicar_tema() -> None:
    """Injeta só o CSS moderno + o JavaScript (para páginas sem mascote)."""
    st.markdown(_CSS, unsafe_allow_html=True)
    components.html(f"<!--__ata_ui__--><script>{_JS}</script>", height=0)


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
