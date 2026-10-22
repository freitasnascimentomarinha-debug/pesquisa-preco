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
import zipfile
import base64
from datetime import datetime, timedelta
from fpdf import FPDF
from docx import Document as DocxDocument
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou("documento_oficial", "modelos_processo", "conferencia_processo", "natureza_despesa", "fracionamento")  # evita módulo antigo em memória após deploy
import documento_oficial  # noqa: E402
import modelos_processo as MP  # noqa: E402
import conferencia_processo as CP  # noqa: E402
import fracionamento as FR  # noqa: E402
import natureza_despesa as ND  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass  # em produção (Streamlit Cloud), usa variáveis de ambiente direto

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

    /* SIDEBAR MODERNA */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
        border-right: 3px solid #d4af37 !important;
        box-shadow: 4px 0 15px rgba(0, 0, 0, 0.5);
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] { background: transparent !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Título da sidebar */
    [data-testid="stSidebar"] .stMarkdown h2 {
        color: #d4af37 !important;
        font-family: 'Arial Black', sans-serif;
        font-size: 22px;
        text-align: center;
        letter-spacing: 2px;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
        border-bottom: 2px solid #d4af37;
        padding-bottom: 0.75rem;
        margin-bottom: 1.5rem;
    }

    /* Links de navegação na sidebar */
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%) !important;
        color: #ffffff !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
        margin: 0.2rem 0 !important;
        padding: 0.45rem 0.7rem !important;
        font-weight: 600 !important;
        font-size: 12.5px !important;
        line-height: 1.2 !important;
        min-height: 0 !important;
        transition: all 0.3s ease !important;
        text-decoration: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background: linear-gradient(135deg, #252525 0%, #353535 100%) !important;
        border: 1px solid #d4af37 !important;
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.25) !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover span {
        color: #d4af37 !important;
    }
    /* Link ativo / página atual */
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
        color: #0a0a0a !important;
        border: 1px solid #d4af37 !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4) !important;
    }
    [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span {
        color: #0a0a0a !important;
    }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stText, [data-testid="stSidebar"] p { color: #ffffff !important; }
    [data-testid="stSidebar"] hr { border-color: #333333 !important; margin: 1rem 0 !important; }
    .sidebar-footer { color: #666666; font-size: 11px; text-align: center; padding: 1rem 0; border-top: 1px solid #333333; margin-top: 2rem; }

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

    .chat-console {
        background: linear-gradient(135deg, rgba(10, 22, 40, 0.96), rgba(10, 42, 91, 0.84));
        border: 1px solid #1e5b9f;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
    }
    .chat-console-top { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
    .chat-console-title { display: flex; align-items: center; gap: 0.75rem; }
    .chat-console-avatar {
        width: 2.35rem; height: 2.35rem; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        background: #d4af37; color: #001a4d; font-size: 1.2rem; box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.13);
    }
    .chat-console h3 { color: #f8fafc; font-size: 1rem; margin: 0; }
    .chat-console p { color: #a8c6e8; font-size: 0.78rem; margin: 0.1rem 0 0; }
    .online-indicator { color: #86efac; font-size: 0.74rem; font-weight: 700; }
    .online-indicator::before {
        content: ""; display: inline-block; width: 0.45rem; height: 0.45rem; margin-right: 0.38rem;
        background: #22c55e; border-radius: 50%; box-shadow: 0 0 8px rgba(34, 197, 94, 0.8);
    }
    .chat-metrics { display: flex; gap: 0.45rem; flex-wrap: wrap; }
    .chat-metric { background: rgba(0, 12, 34, 0.46); border: 1px solid rgba(96, 165, 250, 0.25); border-radius: 6px; padding: 0.32rem 0.55rem; }
    .chat-metric-label { color: #94a3b8; font-size: 0.65rem; text-transform: uppercase; }
    .chat-metric-value { color: #e2e8f0; font-size: 0.78rem; font-weight: 700; margin-left: 0.28rem; }
    .chat-actions { margin-bottom: 0.8rem; }
    .chat-actions [data-testid="stButton"] button, .chat-actions [data-testid="stFileUploader"] button {
        border-color: #2b6cb0 !important;
    }
    .workspace-console {
        background: linear-gradient(135deg, rgba(10, 22, 40, 0.96), rgba(10, 42, 91, 0.84));
        border: 1px solid #1e5b9f;
        border-radius: 10px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
    }
    .workspace-console-content { display: flex; align-items: center; gap: 0.85rem; }
    .workspace-console-icon {
        width: 2.5rem; height: 2.5rem; display: flex; align-items: center; justify-content: center;
        border-radius: 7px; background: rgba(212, 175, 55, 0.16); border: 1px solid rgba(212, 175, 55, 0.45);
        font-size: 1.2rem;
    }
    .workspace-console h3 { color: #f8fafc; font-size: 1rem; margin: 0; }
    .workspace-console p { color: #a8c6e8; font-size: 0.8rem; margin: 0.15rem 0 0; }
    .workspace-console-badge { color: #d4af37; font-size: 0.72rem; font-weight: 700; margin-left: auto; }
    .document-workspace [data-testid="stSelectbox"] > div > div,
    .checklist-workspace [data-testid="stSelectbox"] > div > div {
        border-color: #2b6cb0 !important;
        background: rgba(10, 22, 40, 0.78) !important;
    }
    .checklist-progress {
        background: rgba(7, 20, 42, 0.7); border: 1px solid #1e5b9f; border-radius: 8px;
        padding: 0.85rem 1rem; margin: 0.8rem 0 1rem;
    }
    .checklist-progress-head { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; }
    .checklist-progress-title { color: #dbeafe; font-size: 0.82rem; font-weight: 700; }
    .checklist-progress-value { color: #d4af37; font-size: 0.95rem; font-weight: 800; }
    .checklist-progress-track { background: #10284a; border-radius: 999px; height: 0.42rem; margin-top: 0.55rem; overflow: hidden; }
    .checklist-progress-fill { background: linear-gradient(90deg, #3b82f6, #d4af37); height: 100%; border-radius: inherit; }
    .checklist-workspace [data-testid="stCheckbox"] {
        background: rgba(10, 22, 40, 0.42); border: 1px solid rgba(59, 130, 246, 0.16);
        border-radius: 6px; padding: 0.38rem 0.55rem; margin-bottom: 0.2rem;
    }
    div[data-testid="stChatMessage"] {
        background: rgba(10,22,40,0.6) !important;
        border: 1px solid rgba(59, 130, 246, 0.18);
        border-radius: 10px;
        padding: 0.35rem 0.55rem;
        margin-bottom: 0.45rem;
    }
    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarUser"] { background: #d4af37; }
    div[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarAssistant"] { background: #1d4ed8; }

    /* Auto-scroll chat to bottom */
    .stChatFloatingInputContainer { position: sticky; bottom: 0; z-index: 100; }
    section[data-testid="stChatMessageContainer"] {
        max-height: 65vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
    }

    /* Traduzir textos do file_uploader para PT-BR */
    [data-testid="stFileUploaderDropzone"] span:has(+ small) {
        visibility: hidden;
        position: relative;
    }
    [data-testid="stFileUploaderDropzone"] span:has(+ small)::after {
        content: "Arraste e solte o arquivo aqui";
        visibility: visible;
        position: absolute;
        left: 0;
        white-space: nowrap;
    }
    [data-testid="stFileUploaderDropzone"] small {
        visibility: hidden;
        position: relative;
    }
    [data-testid="stFileUploaderDropzone"] small::after {
        content: "Limite de 200MB por arquivo";
        visibility: visible;
        position: absolute;
        left: 0;
        white-space: nowrap;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] button[data-testid="baseButton-minimal"] {
        visibility: hidden;
        position: relative;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] button[data-testid="baseButton-minimal"]::after {
        content: "Procurar arquivos";
        visibility: visible;
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
        white-space: nowrap;
        color: #d4af37;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTES
# ============================================================
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MEMORIA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "babilaca_memoria.json")
REQ_COUNTER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "babilaca_req_count.json")

def _ler_req_data() -> dict:
    """Lê dados persistentes de requisições (total + por chave)."""
    try:
        with open(REQ_COUNTER_PATH, "r") as f:
            data = json.load(f)
            # Migrar formato antigo {total: N} para novo
            if "por_chave" not in data:
                data = {"total": data.get("total", 0), "por_chave": {}}
            return data
    except Exception:
        return {"total": 0, "por_chave": {}}

def _ler_req_count() -> int:
    """Lê contador persistente total de requisições."""
    return _ler_req_data().get("total", 0)

def _ler_req_count_chave(api_key: str) -> int:
    """Lê contador de requisições para uma chave de API específica."""
    data = _ler_req_data()
    # Usar hash parcial da chave como identificador (segurança)
    chave_id = api_key[-12:] if len(api_key) > 12 else api_key
    return data.get("por_chave", {}).get(chave_id, 0)

def _incrementar_req_count(api_key: str = "") -> int:
    """Incrementa e salva contador persistente (total + por chave). Retorna novo total."""
    data = _ler_req_data()
    data["total"] = data.get("total", 0) + 1
    if api_key:
        chave_id = api_key[-12:] if len(api_key) > 12 else api_key
        data.setdefault("por_chave", {})
        data["por_chave"][chave_id] = data["por_chave"].get(chave_id, 0) + 1
    try:
        with open(REQ_COUNTER_PATH, "w") as f:
            json.dump(data, f)
    except Exception:
        pass
    return data["total"]

# ============================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================
def _get_api_key():
    """Tenta obter a chave do OpenRouter de múltiplas fontes."""
    # 1. Variável de ambiente / .env
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    # 2. st.secrets (Streamlit Cloud) — top level ou dentro de [openrouter]
    try:
        key = st.secrets.get("OPENROUTER_API_KEY", "")
        if key:
            return key
        key = st.secrets.get("openrouter", {}).get("OPENROUTER_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return ""

_defaults = {
    "babilaca_messages": [],
    "babilaca_api_key": _get_api_key(),
    "babilaca_modelo": "deepseek/deepseek-v4.1-flash",
    "babilaca_alertas": [],
    "babilaca_docs_gerados": [],
    "babilaca_preferencias": {},
    "babilaca_respostas_salvas": [],
    "babilaca_sessao_reqs": 0,
    "babilaca_sessao_custo": 0.0,
    "babilaca_sessao_tokens_in": 0,
    "babilaca_sessao_tokens_out": 0,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# BASE JURÍDICA (RAG SIMPLIFICADO) — arquivo externo
# ============================================================
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "base_juridica",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "base_juridica.py"),
)
_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
BASE_JURIDICA = _mod.BASE_JURIDICA

# --- Base RAG expandida (INs, Decreto 10.024, Acórdãos TCU) ---
_RAG_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rag_knowledge_base.json")
RAG_KNOWLEDGE_BASE = []
if os.path.isfile(_RAG_JSON_PATH):
    with open(_RAG_JSON_PATH, "r", encoding="utf-8") as _f:
        RAG_KNOWLEDGE_BASE = json.load(_f)

# --- Texto integral da Lei 14.133/2021 (parser automático) ---
_spec_lei = _ilu.spec_from_file_location(
    "lei_parser",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lei_parser.py"),
)
_mod_lei = _ilu.module_from_spec(_spec_lei)
_spec_lei.loader.exec_module(_mod_lei)
ARTIGOS_LEI_INTEGRAL = _mod_lei.get_artigos_lei()


def _score_item(item: dict, tokens: set[str]) -> float:
    """Calcula score de relevância de um item da base jurídica."""
    kws = set(w.lower() for w in item["palavras_chave"])
    all_text = (item["conteudo"] + " " + item["titulo"]).lower()
    score = sum(1 for t in tokens if any(t in kw for kw in kws))
    score += sum(0.3 for t in tokens if t in all_text)
    return score


def buscar_base_juridica(pergunta: str, top_n: int = 15) -> list[dict]:
    """Busca os trechos mais relevantes da base jurídica para a pergunta.
    Retorna uma mistura equilibrada de Leis, INs, Decretos, Legislação Complementar e Acórdãos TCU.
    Fontes: base curada + texto integral Lei 14.133 + RAG (INs, Decreto 10.024, Acórdãos TCU)."""
    tokens = set(re.findall(r"\w+", pergunta.lower()))

    # 1) Pontuar itens da base curada (INs, acórdãos, resumos manuais)
    scored = []
    for item in BASE_JURIDICA:
        score = _score_item(item, tokens)
        if score > 0:
            scored.append((score, item))

    # 2) Pontuar artigos do texto integral da lei
    artigos_ids_curados = {
        item["artigo"] for item in BASE_JURIDICA if "Lei 14.133" in item.get("fonte", "")
    }
    for item in ARTIGOS_LEI_INTEGRAL:
        if item["artigo"] in artigos_ids_curados:
            continue
        score = _score_item(item, tokens)
        if score > 0:
            scored.append((score, item))

    # 3) Pontuar itens da base RAG expandida (INs, Decreto 10.024, Acórdãos TCU)
    for item in RAG_KNOWLEDGE_BASE:
        score = _score_item(item, tokens)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)

    # Garantir mix equilibrado: leis + decretos + INs + acórdãos
    leis = [s for s in scored if "Lei 14.133" in s[1]["fonte"]]
    decretos = [s for s in scored if "Decreto" in s[1]["fonte"]]
    ins = [s for s in scored if "IN " in s[1]["fonte"]]
    acordaos = [s for s in scored if "TCU" in s[1]["fonte"] or "Acord" in s[1]["fonte"]]
    outras = [
        s for s in scored
        if s not in leis and s not in decretos and s not in ins and s not in acordaos
    ]
    resultado = []
    max_lei = max(3, top_n // 4)
    max_decreto = max(2, top_n // 5)
    max_in = max(2, top_n // 5)
    max_tcu = max(3, top_n // 4)
    max_outras = top_n - max_lei - max_decreto - max_in - max_tcu
    resultado.extend(leis[:max_lei])
    resultado.extend(decretos[:max_decreto])
    resultado.extend(ins[:max_in])
    resultado.extend(acordaos[:max_tcu])
    resultado.extend(outras[:max(1, max_outras)])
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

SYSTEM_PROMPT = """Você é **O Babilaca**, um assistente jurídico inteligente especializado em licitações e contratações públicas brasileiras, com foco na Lei 14.133/2021, Decreto 10.024/2019 (Pregão Eletrônico), Instruções Normativas (SEGES/ME nº 5/2017, 58/2022, 65/2021, 67/2021) e jurisprudência do TCU.

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
2. Se o contexto contiver fontes de diferentes categorias (Lei, Decreto, IN, TCU), organize em camadas:
   - **Base legal**: artigo da Lei 14.133/2021 (se disponível no contexto)
   - **Regulamentação**: Decreto 10.024/2019 ou IN aplicável (se disponível no contexto)
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

AVISO: Você é uma ferramenta de apoio.

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
    model = modelo or st.session_state.get("babilaca_modelo", "deepseek/deepseek-v4.1-flash")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://atacotada.streamlit.app",
        "X-Title": "AtaCotada - O Babilaca",
    }
    msgs = [{"role": "system", "content": system_prompt}] + mensagens

    # Tenta com 4096 tokens; se créditos insuficientes (402), reduz automaticamente
    for max_tk in (4096, 2048, 1024):
        payload = {
            "model": model,
            "messages": msgs,
            "temperature": temperatura,
            "max_tokens": max_tk,
        }
        try:
            resp = requests.post(
                OPENROUTER_URL, headers=headers, json=payload, timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                # Incrementar contador persistente de requisições
                _incrementar_req_count(api_key)
                # Rastrear uso da sessão (tokens e custo)
                usage = data.get("usage", {})
                st.session_state["babilaca_sessao_reqs"] = st.session_state.get("babilaca_sessao_reqs", 0) + 1
                st.session_state["babilaca_sessao_tokens_in"] = st.session_state.get("babilaca_sessao_tokens_in", 0) + (usage.get("prompt_tokens", 0) or 0)
                st.session_state["babilaca_sessao_tokens_out"] = st.session_state.get("babilaca_sessao_tokens_out", 0) + (usage.get("completion_tokens", 0) or 0)
                custo_req = float(data.get("usage", {}).get("total_cost", 0) or 0)
                if not custo_req:
                    # Estimar custo se a API não retornar
                    custo_req = ((usage.get("prompt_tokens", 0) or 0) * 0.15 + (usage.get("completion_tokens", 0) or 0) * 0.60) / 1_000_000
                st.session_state["babilaca_sessao_custo"] = st.session_state.get("babilaca_sessao_custo", 0.0) + custo_req
                return data["choices"][0]["message"]["content"]

            # --- Tratamento de erros conhecidos ---
            if resp.status_code == 402:
                # Créditos insuficientes — tentar com menos tokens
                try:
                    err = resp.json().get("error", {})
                    meta = err.get("metadata", {})
                except Exception:
                    err, meta = {}, {}
                if max_tk > 1024:
                    continue  # retry com menos tokens
                return (
                    "⚠️ **Créditos insuficientes** na conta OpenRouter.\n\n"
                    "Adicione créditos em https://openrouter.ai/settings/credits "
                    "e tente novamente."
                )

            if resp.status_code == 404:
                return (
                    f"⚠️ **Modelo indisponível**: `{model}`\n\n"
                    "Possíveis causas:\n"
                    "- Restrições de privacidade/política de dados na sua conta OpenRouter\n"
                    "- Modelo temporariamente fora do ar\n\n"
                    "Se persistir, verifique suas configurações em https://openrouter.ai/settings/privacy"
                )

            if resp.status_code == 403:
                return (
                    "⚠️ **Limite diário atingido**.\n\n"
                    "Sua chave de API alcançou o limite de uso do dia. "
                    "Gerencie seus limites em https://openrouter.ai/settings/keys"
                )

            if resp.status_code == 429:
                return (
                    "⚠️ **Limite de requisições atingido**. "
                    "Aguarde alguns segundos e tente novamente."
                )

            return f"⚠️ Erro na API (HTTP {resp.status_code}): {resp.text[:300]}"

        except requests.Timeout:
            return "⚠️ Tempo limite da requisição excedido. Tente novamente."
        except Exception as e:
            return f"⚠️ Erro ao chamar a IA: {e}"

    return "⚠️ Não foi possível obter resposta da IA. Verifique sua conexão e créditos."


# ============================================================
# ROTEAMENTO DE INTENÇÃO
# ============================================================

# ---- Consultar saldo da conta OpenRouter ----
def consultar_saldo_openrouter() -> dict | None:
    """Consulta saldo e uso da conta via API /auth/key."""
    api_key = st.session_state.get("babilaca_api_key", "")
    if not api_key:
        return None
    try:
        resp = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {})
    except Exception:
        pass
    return None


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


def _dados_documento() -> dict:
    """Dados da OM, do processo e do signatário informados na aba Documentos (valem para todos os documentos)."""
    dados = {k: st.session_state.get(f"docom_{k}") for k in ("om", "cidade", "uf", "nup", "data")}
    dados["assinantes"] = [{c: st.session_state.get(f"docom_ass{i}_{c}") for c in ("nome", "posto", "cargo")}
                           for i in range(int(st.session_state.get("docom_n_assinantes") or 1))]
    return dados


def _pendencias_documento() -> list[str]:
    """Campos obrigatórios do cabeçalho e da assinatura que ainda não foram preenchidos."""
    faltam = []
    for chave, rotulo in (("docom_om", "nome da OM"), ("docom_cidade", "cidade"), ("docom_uf", "UF")):
        if not (st.session_state.get(chave) or "").strip():
            faltam.append(rotulo)
    for i in range(int(st.session_state.get("docom_n_assinantes") or 1)):
        for campo, rotulo in (("nome", "nome"), ("posto", "posto/graduação ou cargo efetivo"), ("cargo", "função")):
            if not (st.session_state.get(f"docom_ass{i}_{campo}") or "").strip():
                faltam.append(f"{rotulo} do {i + 1}º signatário")
    return faltam


CAMPOS_PERFIL_OM = ("om", "cidade", "uf", "uasg", "endereco", "contato")


def _perfil_om_json() -> bytes:
    """Dados da OM e dos signatários num arquivo que o usuário guarda (nada fica no servidor)."""
    perfil = {c: st.session_state.get(f"docom_{c}", "") or "" for c in CAMPOS_PERFIL_OM}
    n = int(st.session_state.get("docom_n_assinantes") or 1)
    perfil["assinantes"] = [{c: st.session_state.get(f"docom_ass{i}_{c}", "") or "" for c in ("nome", "posto", "cargo")}
                            for i in range(n)]
    return json.dumps({"versao": 1, "perfil_om": perfil}, ensure_ascii=False, indent=2).encode("utf-8")


def _aplicar_perfil_om(dados: dict):
    perfil = dados.get("perfil_om") or {}
    if not perfil.get("om"):
        raise ValueError("o arquivo não traz o nome da OM")
    for c in CAMPOS_PERFIL_OM:
        st.session_state[f"docom_{c}"] = str(perfil.get(c) or "")
    assinantes = (perfil.get("assinantes") or [])[:4] or [{}]
    st.session_state["docom_n_assinantes"] = len(assinantes)
    for i, a in enumerate(assinantes):
        for c in ("nome", "posto", "cargo"):
            st.session_state[f"docom_ass{i}_{c}"] = str(a.get(c) or "")


def _preencher(chave: str, valor: str):
    """Sugere um valor dos dados da OM num campo ainda vazio (o usuário pode alterar)."""
    if valor and not str(st.session_state.get(chave) or "").strip():
        st.session_state[chave] = valor


def _om(campo: str) -> str:
    return str(st.session_state.get(f"docom_{campo}") or "").strip()


def gerar_pdf_documento(titulo: str, corpo: str, oficio: dict | None = None, nup: str = "") -> bytes:
    """PDF no padrão gráfico da Marinha (SGM-105/MaTDoc): timbre, tabelas, paginação e assinatura."""
    dados = _dados_documento()
    if nup:
        dados["nup"] = nup
    return documento_oficial.gerar_pdf(titulo, corpo, dados, oficio)


def gerar_docx_documento(titulo: str, corpo: str, oficio: dict | None = None, nup: str = "") -> bytes:
    """Word editável no mesmo padrão do PDF."""
    dados = _dados_documento()
    if nup:
        dados["nup"] = nup
    return documento_oficial.gerar_docx(titulo, corpo, dados, oficio)


INSTRUCOES_DOCUMENTO = """

INSTRUÇÕES PARA DOCUMENTO (prevalecem sobre as instruções de conversa):
- Responda SOMENTE com o texto do documento: sem saudação, sem introdução ("Claro", "Segue") e sem comentários finais.
- Não repita o título do documento na primeira linha; o sistema já monta cabeçalho, título, local e data e assinatura.
- Use "### 1. TÍTULO DO ITEM" para cada item numerado; subitens como "1.1.", alíneas como "a)" e subalíneas como "I)".
- Tabelas sempre em Markdown com barras verticais (| Coluna | Coluna |) e linha separadora (|---|---|).
- Linguagem impessoal, culta, clara e concisa (padrão da redação oficial); valores em R$ com o extenso entre parênteses.
- Campos que dependem de dado não informado ficam como lacuna "__________", sem inventar números, nomes ou datas.
"""


def _registrar_doc(chave: str, titulo: str, corpo: str, nome_base: str, oficio: dict | None = None):
    """Guarda o documento gerado: ele continua na tela depois de baixar um dos formatos e pode ser editado.
    oficio: cabeçalho do Of/OfExt (Do, Ao, Assunto...), quando o documento for um ofício."""
    st.session_state[f"doc_gerado_{chave}"] = {"titulo": titulo, "corpo": corpo, "nome": nome_base, "oficio": oficio}
    st.session_state[f"doc_editado_{chave}"] = corpo


def _exibir_doc(chave: str):
    """Pré-visualização editável e downloads em PDF e Word do último documento gerado para este tipo."""
    doc = st.session_state.get(f"doc_gerado_{chave}")
    if not doc:
        return
    st.markdown("---")
    st.markdown(f"##### 📄 {doc['titulo'].title()} — pré-visualização")
    st.caption("Revise e edite o texto abaixo antes de baixar. As alterações valem para o PDF e para o Word. "
               "Use ### para itens, a) para alíneas e tabelas com | Coluna | Coluna |.")
    corpo = st.text_area("Texto do documento", key=f"doc_editado_{chave}", height=420, label_visibility="collapsed")
    with st.expander("👁️ Ver como fica formatado", expanded=False):
        st.markdown(corpo)
    if _pendencias_documento():
        st.warning("Preencha os **dados obrigatórios da OM e do(s) signatário(s)** no topo desta aba para baixar o documento.")
    bloqueado = bool(_pendencias_documento())
    c_pdf, c_docx, c_limpar = st.columns([2, 2, 1])
    with c_pdf:
        st.download_button("⬇️ Baixar em PDF", gerar_pdf_documento(doc["titulo"], corpo, doc.get("oficio")), f"{doc['nome']}.pdf",
                           "application/pdf", key=f"dl_pdf_{chave}", use_container_width=True, disabled=bloqueado)
    with c_docx:
        st.download_button("📝 Baixar em Word", gerar_docx_documento(doc["titulo"], corpo, doc.get("oficio")), f"{doc['nome']}.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key=f"dl_docx_{chave}", use_container_width=True, disabled=bloqueado)
    with c_limpar:
        if st.button("🗑️ Descartar", key=f"descartar_{chave}", use_container_width=True):
            st.session_state.pop(f"doc_gerado_{chave}", None)
            st.session_state.pop(f"doc_editado_{chave}", None)
            st.rerun()


def _texto_anexos(arquivos) -> str:
    """Texto dos anexos enviados (PDF, planilha, CSV ou Word), para servir de contexto à IA."""
    partes = []
    for arq in arquivos or []:
        try:
            nome = arq.name.lower()
            if nome.endswith(".pdf"):
                texto = extrair_texto_pdf(arq)
            elif nome.endswith((".xlsx", ".xls")):
                texto, _ = extrair_dados_excel(arq)
            elif nome.endswith(".csv"):
                texto = pd.read_csv(arq).head(100).to_string(index=False)
            else:
                texto = "\n".join(p.text for p in DocxDocument(arq).paragraphs)
            if texto:
                partes.append(f"[ARQUIVO: {arq.name}]\n{texto[:4000]}")
        except Exception as erro:
            st.warning(f"Não foi possível ler o arquivo {arq.name}: {erro}")
    return "\n\n".join(partes)


def _gerar_com_ia(chave: str, titulo: str, prompt: str, consulta: str, nome_base: str, oficio: dict | None = None):
    with st.spinner("O Babilaca está redigindo o documento..."):
        system = _build_system_prompt(buscar_base_juridica(consulta)) + INSTRUCOES_DOCUMENTO
        resultado = chamar_ia([{"role": "user", "content": prompt}], system)
    if not resultado or resultado.lstrip().startswith(("⚠️", "❌")):
        st.error(resultado or "A IA não retornou texto. Tente de novo.")
        return
    _registrar_doc(chave, titulo, resultado, nome_base, oficio)


def _definir_enquadramento(chave_hip: str, chave_texto: str, tabela: dict):
    """Ao trocar a hipótese, escreve o enquadramento legal correspondente (o usuário pode completar o texto)."""
    texto = MP.texto_hipotese(st.session_state.get(chave_hip), tabela)
    st.session_state[chave_texto] = f"A contratação fundamenta-se no {texto}." if texto else ""


def _form_secoes(tipo: str, bloqueado: bool):
    """ETP, TJDL e TJIL: um campo por seção do modelo, montagem direta ou completada pela IA."""
    modelo = MP.MODELOS[tipo]
    arq = modelo["arquivo"]
    st.markdown(f"#### 📑 {tipo}")
    st.caption(f"Base: {modelo['base']} Seções com * são obrigatórias; deixe em branco o que não souber e use a IA para "
               "completar.")
    secoes = modelo["secoes"]
    idx_enq = next((i for i, s in enumerate(secoes) if s[0] == "ENQUADRAMENTO LEGAL"), None)
    if tipo in (MP.DOC_TJDL, MP.DOC_TJIL):
        tabela = MP.HIPOTESES_DISPENSA if tipo == MP.DOC_TJDL else MP.HIPOTESES_INEXIGIBILIDADE
        chave_hip, chave_enq = f"{arq}_hipotese", f"mdl_{arq}_{idx_enq}"
        st.selectbox("Hipótese legal", list(tabela), key=chave_hip, on_change=_definir_enquadramento,
                     args=(chave_hip, chave_enq, tabela))
        if chave_enq not in st.session_state:
            _definir_enquadramento(chave_hip, chave_enq, tabela)
        if tipo == MP.DOC_TJDL:
            hip = st.session_state.get(chave_hip, "")
            limite = (MP.LIMITES_DISPENSA["inciso_II"] if hip.startswith("Art. 75, II") else
                      MP.LIMITES_DISPENSA["inciso_I"] if hip.startswith("Art. 75, I ") else None)
            if limite:
                _v1, _v2 = st.columns(2)
                with _v1:
                    valor = st.number_input("Valor estimado desta contratação (R$)", min_value=0.0, step=100.0,
                                            format="%.2f", key="tjdl_valor")
                _fr = st.session_state.get("frac_resultado")
                if _fr and _fr["grupos"]:
                    _opcoes_fr = {f"Ramo: {x['ramo']} (art. 75, {x['inciso']}) — {MP.brl(x['total'])}": x["total"]
                                  for x in _fr["grupos"]}
                    _opcoes_fr.update({f"Subelemento: {x['rotulo']} (art. 75, {x['inciso']}) — {MP.brl(x['total'])}": x["total"]
                                       for x in FR.por_subelemento(_fr["grupos"], st.session_state.get("frac_ajustes"))
                                       if x["subelemento"]})
                    st.selectbox("Preencher \"já contratado\" com um ramo ou subelemento verificado na aba ⚖️ Limite de Dispensa",
                                 ["—"] + list(_opcoes_fr), key="tjdl_ramo_fr",
                                 on_change=lambda: st.session_state.__setitem__(
                                     "tjdl_acumulado", float(_opcoes_fr.get(st.session_state["tjdl_ramo_fr"], 0.0))))
                with _v2:
                    acumulado = st.number_input("Já contratado no exercício, mesmo ramo de atividade (R$)", min_value=0.0,
                                                step=100.0, format="%.2f", key="tjdl_acumulado",
                                                help="Art. 75, §1º: o limite considera o somatório da unidade gestora no "
                                                     "exercício para objetos de mesma natureza.")
                total = valor + acumulado
                if total > limite:
                    st.error(f"Somatório de {MP.brl(total)} ultrapassa o limite de {MP.brl(limite)}: a dispensa por valor "
                             "não cabe (risco de fracionamento). Avalie licitar ou outra hipótese.")
                elif total:
                    st.success(f"Somatório de {MP.brl(total)} dentro do limite de {MP.brl(limite)} "
                               f"({total * 100 / limite:.0f}% usado).")
                st.caption(MP.nota_limites())
    textos = []
    for i, (titulo, ajuda, obrigatoria) in enumerate(secoes):
        textos.append(st.text_area(f"{i + 1}. {titulo.capitalize()}{' *' if obrigatoria else ''}", key=f"mdl_{arq}_{i}",
                                   height=90, placeholder=ajuda, help=ajuda))
    with st.expander("🤖 Contexto e anexos para a IA (opcional)"):
        contexto = st.text_area("Informe o que a IA deve saber (objeto, histórico, números já conhecidos)",
                                key=f"mdl_{arq}_contexto", height=100)
        anexos = st.file_uploader("Anexos de apoio", type=["pdf", "xlsx", "xls", "csv", "docx"], accept_multiple_files=True,
                                  key=f"mdl_{arq}_anexos")
    _b1, _b2 = st.columns(2)
    with _b1:
        if st.button("📄 Montar com o que preenchi", key=f"mdl_{arq}_montar", use_container_width=True, disabled=bloqueado):
            _registrar_doc(tipo, modelo["titulo"], MP.corpo_secoes(modelo, textos), arq)
    with _b2:
        if st.button("🤖 Completar e revisar com IA", key=f"mdl_{arq}_ia", use_container_width=True, disabled=bloqueado):
            if any(t.strip() for t in textos) or contexto.strip() or anexos:
                extra = _texto_anexos(anexos)
                prompt = MP.prompt_secoes(modelo, textos, contexto + ("\n\nANEXOS:\n" + extra if extra else ""))
                _gerar_com_ia(tipo, modelo["titulo"], prompt, modelo["consulta"], f"{arq}_ia")
            else:
                st.warning("Preencha ao menos uma seção, o contexto ou um anexo.")


def _form_mapa_riscos(bloqueado: bool):
    st.markdown("#### ⚠️ Mapa de Riscos")
    st.caption("Lei nº 14.133/2021, art. 18, X. A tabela já traz riscos comuns de aquisição: edite, apague ou acrescente "
               "linhas. O nível sai da probabilidade × impacto.")
    objeto = st.text_area("Objeto da contratação *", key="riscos_objeto", height=70)
    riscos = st.data_editor(
        pd.DataFrame(MP.RISCOS_PADRAO, columns=MP.COLUNAS_RISCO), key="riscos_editor", num_rows="dynamic",
        width="stretch", hide_index=True,
        column_config={
            "Fase": st.column_config.SelectboxColumn(options=["Planejamento", "Seleção do fornecedor", "Gestão do contrato"]),
            "Probabilidade": st.column_config.SelectboxColumn(options=["Baixa", "Média", "Alta"]),
            "Impacto": st.column_config.SelectboxColumn(options=["Baixo", "Médio", "Alto"]),
            "Risco": st.column_config.TextColumn(width="large"),
        })
    lista = riscos.fillna("").to_dict("records")
    _b1, _b2 = st.columns(2)
    with _b1:
        if st.button("📄 Montar mapa de riscos", key="riscos_montar", use_container_width=True, disabled=bloqueado):
            _registrar_doc(MP.DOC_RISCOS, "MAPA DE RISCOS", MP.corpo_mapa_riscos(objeto, lista), "mapa_de_riscos")
    with _b2:
        if st.button("🤖 Revisar e completar riscos com IA", key="riscos_ia", use_container_width=True, disabled=bloqueado):
            if objeto.strip():
                prompt = (
                    "Revise e complete o mapa de riscos abaixo para a contratação descrita, acrescentando riscos "
                    "específicos do objeto. Mantenha EXATAMENTE as seções e o formato do texto-base, inclusive a tabela "
                    "com as mesmas colunas; o nível segue a regra da metodologia.\n\nTEXTO-BASE:\n"
                    + MP.corpo_mapa_riscos(objeto, lista))
                _gerar_com_ia(MP.DOC_RISCOS, "MAPA DE RISCOS", prompt, "análise de riscos art 18 matriz de riscos",
                              "mapa_de_riscos_ia")
            else:
                st.warning("Descreva o objeto.")


def _form_aviso(bloqueado: bool):
    st.markdown("#### 📢 Aviso de Contratação Direta (dispensa eletrônica)")
    st.caption("Lei nº 14.133/2021, art. 75, §3º, e IN SEGES/ME nº 67/2021: aviso no sítio oficial por no mínimo 3 dias "
               "úteis, com o objeto e a manifestação de interesse em obter propostas adicionais.")
    _a1, _a2 = st.columns(2)
    with _a1:
        numero = st.text_input("Nº do aviso", key="aviso_numero", placeholder="Ex: 90012/2026")
    with _a2:
        _preencher("aviso_uasg", _om("uasg"))
        uasg = st.text_input("UASG", key="aviso_uasg")
    objeto = st.text_area("Objeto *", key="aviso_objeto", height=70)
    hip = st.selectbox("Fundamento", list(MP.HIPOTESES_DISPENSA)[:-1],
                       key="aviso_hipotese")
    _v1, _v2 = st.columns([2, 1])
    with _v1:
        valor = st.number_input("Valor estimado (R$)", min_value=0.0, step=100.0, format="%.2f", key="aviso_valor")
    with _v2:
        sigiloso = st.checkbox("Orçamento sigiloso (art. 24)", key="aviso_sigiloso")
    limite = (MP.LIMITES_DISPENSA["inciso_II"] if hip.startswith("Art. 75, II") else
              MP.LIMITES_DISPENSA["inciso_I"] if hip.startswith("Art. 75, I ") else None)
    if limite and valor > limite:
        st.error(f"O valor ultrapassa o limite de {MP.brl(limite)} ({MP.LIMITES_DISPENSA['decreto']}).")
    hoje = datetime.now().date()
    _d1, _d2, _d3, _d4 = st.columns(4)
    with _d1:
        d_ini = st.date_input("Abertura das propostas", value=hoje, key="aviso_d_ini", format="DD/MM/YYYY")
    with _d2:
        h_ini = st.time_input("Hora", value=datetime.strptime("08:00", "%H:%M").time(), key="aviso_h_ini")
    with _d3:
        d_fim = st.date_input("Encerramento", value=hoje + timedelta(days=5), key="aviso_d_fim", format="DD/MM/YYYY")
    with _d4:
        h_fim = st.time_input("Hora ", value=datetime.strptime("10:00", "%H:%M").time(), key="aviso_h_fim")
    uteis = MP.dias_uteis(d_ini, d_fim)
    if uteis < 3:
        st.error(f"Prazo de {uteis} dia(s) útil(eis): o mínimo é 3 dias úteis (art. 75, §3º). Contagem do art. 183: "
                 "exclui o dia de início e inclui o do vencimento; feriados nacionais descontados.")
    else:
        st.success(f"Prazo de {uteis} dias úteis (mínimo de 3). Feriados estaduais e municipais não são descontados.")
    _c1, _c2 = st.columns(2)
    with _c1:
        criterio = st.selectbox("Critério de julgamento", ["menor preço", "maior desconto"], key="aviso_criterio")
        prazo_entrega = st.text_input("Prazo de entrega / execução", key="aviso_prazo",
                                      placeholder="Ex: 30 dias corridos da nota de empenho")
        _preencher("aviso_contato", _om("contato"))
        contato = st.text_input("Contato para esclarecimentos", key="aviso_contato", placeholder="e-mail e telefone")
    with _c2:
        exclusiva = st.checkbox("Exclusiva para ME/EPP", key="aviso_me", value=True,
                                help="LC nº 123/2006, art. 48, I: itens de até R$ 80.000,00.")
        local = st.text_input("Local de entrega", key="aviso_local")
        pagamento = st.text_input("Condição de pagamento (opcional)", key="aviso_pagamento")
    habilitacao = st.text_area("Habilitação exigida (opcional; em branco usa o texto padrão)", key="aviso_habilitacao",
                               height=70)
    contexto = st.text_area("🤖 Contexto para a IA (opcional): detalhes do objeto, exigências, condições especiais",
                            key="aviso_contexto", height=70)
    corpo = MP.corpo_aviso({
        "numero": numero, "uasg": uasg, "objeto": objeto, "hipotese_txt": MP.texto_hipotese(hip, MP.HIPOTESES_DISPENSA),
        "valor": valor, "sigiloso": sigiloso, "criterio": criterio, "exclusiva_me": exclusiva,
        "inicio": datetime.combine(d_ini, h_ini), "fim": datetime.combine(d_fim, h_fim),
        "prazo_entrega": prazo_entrega, "local_entrega": local, "pagamento": pagamento,
        "habilitacao": habilitacao, "contato": contato})
    titulo = f"AVISO DE CONTRATAÇÃO DIRETA Nº {numero.strip()}" if numero.strip() else "AVISO DE CONTRATAÇÃO DIRETA"
    _b1, _b2 = st.columns(2)
    with _b1:
        if st.button("📄 Gerar aviso", key="aviso_gerar", use_container_width=True, disabled=bloqueado):
            _registrar_doc(MP.DOC_AVISO, titulo, corpo, "aviso_contratacao_direta")
    with _b2:
        if st.button("🤖 Completar e revisar com IA", key="aviso_ia", use_container_width=True, disabled=bloqueado):
            if objeto.strip():
                _gerar_com_ia(MP.DOC_AVISO, titulo, MP.prompt_revisar(corpo, contexto, "aviso"),
                              "dispensa eletrônica aviso art 75 IN 67/2021", "aviso_contratacao_direta_ia")
            else:
                st.warning("Descreva o objeto.")


def _form_oficio(tipo: str, bloqueado: bool):
    adesao = tipo == MP.DOC_OF_ADESAO
    k = "ofad" if adesao else "ofirp"
    st.markdown(f"#### ✉️ {tipo}")
    st.caption("Forma gráfica do MaTDoc: Ofício (cap. 16) para OM da Marinha — Do/Ao/Assunto, itens numerados sem título "
               "e sem fecho; Ofício Externo (cap. 17) para órgão fora da MB — destinatário, vocativo e fecho.")
    externo = st.radio("Destinatário", ["OM da Marinha (Ofício)", "Órgão fora da Marinha (Ofício Externo)"],
                       horizontal=True, key=f"{k}_tipo") != "OM da Marinha (Ofício)"
    _h1, _h2 = st.columns([1, 3])
    with _h1:
        numero = st.text_input("Nº do ofício", key=f"{k}_numero", placeholder="12/COpAb-MB" if externo else "12")
    with _h2:
        assunto = st.text_input("Assunto", key=f"{k}_assunto",
                                value="Solicitação de adesão a Ata de Registro de Preços" if adesao else
                                "Manifestação de interesse em Intenção de Registro de Preços")
    if externo:
        _preencher(f"{k}_endereco", "\n".join(x for x in (_om("endereco"), _om("contato")) if x))
        endereco = st.text_area("Endereço, telefone e e-mail da OM (abaixo do nome)", key=f"{k}_endereco", height=70)
        destinatario = st.text_area("Destinatário (forma de tratamento, nome, cargo, órgão e endereço)", key=f"{k}_dest",
                                    height=110, value="Ao Senhor\nNome do destinatário\nCargo\nÓrgão\nEndereço")
        _x1, _x2 = st.columns(2)
        with _x1:
            vocativo = st.text_input("Vocativo", key=f"{k}_vocativo", value="Senhor Diretor,")
        with _x2:
            fecho = st.selectbox("Fecho", ["Atenciosamente,", "Respeitosamente,"], key=f"{k}_fecho",
                                 help="Respeitosamente para autoridade de hierarquia superior; Atenciosamente nos demais casos.")
        do = ao = via = ""
        referencias, anexos = [], []
    else:
        _h3, _h4 = st.columns(2)
        with _h3:
            do = st.text_input("Do:", key=f"{k}_do", placeholder="Ex: Diretor do Centro de ...")
        with _h4:
            ao = st.text_input("Ao:", key=f"{k}_ao", placeholder="Ex: Diretor do ... (órgão gerenciador)")
        via = st.text_input("Via: (opcional)", key=f"{k}_via")
        _h5, _h6 = st.columns(2)
        with _h5:
            referencias = st.text_area("Referências (uma por linha)", key=f"{k}_refs", height=80,
                                       value="Lei nº 14.133/2021\nDecreto nº 11.462/2023").splitlines()
        with _h6:
            anexos = st.text_area("Anexos (um por linha)", key=f"{k}_anexos", height=80).splitlines()
        endereco = destinatario = vocativo = fecho = ""
    copias = st.text_input("Cópias (separe por vírgula; opcional)", key=f"{k}_copias")

    st.markdown("**Conteúdo**")
    _c1, _c2 = st.columns(2)
    with _c1:
        gerenciador = st.text_input("Órgão gerenciador", key=f"{k}_gerenciador")
        uasg = st.text_input("UASG gerenciadora", key=f"{k}_uasg")
    with _c2:
        if adesao:
            ata = st.text_input("Nº da Ata de Registro de Preços", key=f"{k}_ata")
            licitacao = st.text_input("Licitação de origem", key=f"{k}_licitacao", placeholder="Ex: Pregão Eletrônico nº 90010/2026")
        else:
            irp = st.text_input("Nº da IRP", key=f"{k}_irp")
            prazo = st.text_input("Prazo final da IRP", key=f"{k}_prazo", placeholder="dd/mm/aaaa")
    objeto = st.text_input("Objeto", key=f"{k}_objeto")
    justificativa = st.text_area("Justificativa (complete a frase: \"... se justifica porque ...\")", key=f"{k}_just",
                                 height=80)
    if adesao and st.session_state.get("_ofad_itens_ini"):
        st.info("Itens trazidos da página **Adesões**. Informe a **quantidade** pretendida de cada um, respeitando o "
                "máximo por órgão indicado na descrição.")
    itens_ini = (st.session_state.get(f"_{k}_itens_ini") or
                 [{"Item": "", "Descrição": "", "Unidade": "", "Quantidade": ""}])
    itens = st.data_editor(pd.DataFrame(itens_ini, columns=["Item", "Descrição", "Unidade", "Quantidade"]),
                           key=f"{k}_itens_{st.session_state.get(f'_{k}_itens_ver', 0)}", num_rows="dynamic",
                           width="stretch", hide_index=True)
    _c3, _c4 = st.columns(2)
    with _c3:
        _preencher(f"{k}_contato", ", ".join(x for x in (_om("ass0_nome"), _om("contato")) if x))
        contato = st.text_input("Ponto de contato da OM", key=f"{k}_contato", placeholder="Nome, telefone e e-mail")
    with _c4:
        if adesao:
            ciente = st.checkbox("Fornecedor já concordou com o fornecimento", key=f"{k}_ciente")
        else:
            local = st.text_input("Local de entrega", key=f"{k}_local")
    if adesao:
        st.page_link("pages/Adesões.py", label="Conferir saldo para adesão e limite por órgão na página Adesões", icon="🧾")
    else:
        st.page_link("pages/Radar_de_Licitacoes.py", label="Procurar IRPs abertas no Radar de Licitações", icon="📡")

    contexto = st.text_area("🤖 Contexto para a IA (opcional): histórico, urgência, situação da OM",
                            key=f"{k}_contexto", height=70)
    lista = itens.fillna("").to_dict("records")
    if adesao:
        corpo = MP.corpo_oficio_adesao({"gerenciador": gerenciador, "ata": ata, "licitacao": licitacao, "uasg": uasg,
                                        "objeto": objeto, "justificativa": justificativa, "fornecedor_ciente": ciente,
                                        "contato": contato, "itens": lista})
    else:
        corpo = MP.corpo_oficio_irp({"gerenciador": gerenciador, "irp": irp, "uasg": uasg, "objeto": objeto,
                                     "prazo": prazo, "justificativa": justificativa, "local_entrega": local,
                                     "contato": contato, "itens": lista})
    oficio = {"externo": externo, "numero": numero, "do": do, "ao": ao, "via": via, "assunto": assunto,
              "referencias": referencias, "anexos": anexos,
              "copias": [c.strip() for c in copias.split(",") if c.strip()],
              "endereco": endereco, "destinatario": destinatario, "vocativo": vocativo, "fecho": fecho}
    nome_base = "oficio_adesao" if adesao else "oficio_irp"
    _b1, _b2 = st.columns(2)
    with _b1:
        if st.button("📄 Gerar ofício", key=f"{k}_gerar", use_container_width=True, disabled=bloqueado):
            _registrar_doc(tipo, "OFÍCIO", corpo, nome_base, oficio)
    with _b2:
        if st.button("🤖 Melhorar a redação com IA", key=f"{k}_ia", use_container_width=True, disabled=bloqueado):
            _gerar_com_ia(tipo, "OFÍCIO", MP.prompt_revisar(corpo, contexto, "oficio_externo" if externo else "oficio"),
                          "adesão ata registro de preços art 86" if adesao else "intenção de registro de preços art 86",
                          f"{nome_base}_ia", oficio)


def _form_modelo_processo(tipo: str, bloqueado: bool):
    if tipo in MP.MODELOS:
        _form_secoes(tipo, bloqueado)
    elif tipo == MP.DOC_RISCOS:
        _form_mapa_riscos(bloqueado)
    elif tipo == MP.DOC_AVISO:
        _form_aviso(bloqueado)
    else:
        _form_oficio(tipo, bloqueado)


def _ck_chave(modalidade: str, texto: str) -> str:
    return hashlib.md5((modalidade + texto).encode()).hexdigest()[:10]


# ordem das peças no kit (a mesma em que costumam ser juntadas ao processo)
ORDEM_KIT = [MP.DOC_DFD, MP.DOC_ETP, MP.DOC_RISCOS, MP.DOC_TR, MP.DOC_MAPA, MP.DOC_VANTAJOSIDADE, MP.DOC_FRACIONAMENTO,
             MP.DOC_MEMORIA, "Cronograma Físico-Financeiro",
             "Justificativa de Contratação", MP.DOC_TJDL, MP.DOC_TJIL, MP.DOC_AVISO, MP.DOC_OF_ADESAO, MP.DOC_OF_IRP,
             "Ata de Registro de Preços", "Minuta de Contrato de Serviço / Material", "Outras justificativas",
             "Outros documentos", "Classificação de Risco Jurídico"]


def _documentos_gerados() -> list[tuple[str, dict]]:
    """[(chave, documento)] dos documentos gerados nesta sessão, na ordem do processo."""
    chaves = [k[len("doc_gerado_"):] for k in st.session_state.keys() if str(k).startswith("doc_gerado_")]
    chaves = [c for c in chaves if st.session_state.get(f"doc_gerado_{c}")]
    chaves.sort(key=lambda c: (ORDEM_KIT.index(c) if c in ORDEM_KIT else len(ORDEM_KIT), c))
    return [(c, st.session_state[f"doc_gerado_{c}"]) for c in chaves]


def _montar_kit(formatos: list[str]) -> tuple[bytes, list[str]]:
    """ZIP com os documentos gerados (texto já editado), o checklist, o relatório de conferência e o índice."""
    buf, nomes, n = io.BytesIO(), [], 0
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        def gravar(nome, dados):
            z.writestr(nome, dados)
            nomes.append(nome)

        for chave, doc in _documentos_gerados():
            n += 1
            corpo = st.session_state.get(f"doc_editado_{chave}") or doc["corpo"]
            base = f"{n:02d}_{doc['nome']}"
            if "PDF" in formatos:
                gravar(f"{base}.pdf", gerar_pdf_documento(doc["titulo"], corpo, doc.get("oficio")))
            if "Word" in formatos:
                gravar(f"{base}.docx", gerar_docx_documento(doc["titulo"], corpo, doc.get("oficio")))
            if chave == MP.DOC_MAPA and st.session_state.get("mapa_xlsx"):
                gravar(f"{base}.xlsx", st.session_state["mapa_xlsx"])
        modalidade = st.session_state.get("checklist_modalidade")
        if modalidade in CHECKLIST_MODALIDADES:
            itens = CHECKLIST_MODALIDADES[modalidade]
            chaves = [_ck_chave(modalidade, t) for t, _f, _a in itens]
            if any(f"ck_st_{c}" in st.session_state for c in chaves):
                situacoes = [st.session_state.get(f"ck_st_{c}") or "Pendente" for c in chaves]
                observacoes = [st.session_state.get(f"ck_obs_{c}", "") for c in chaves]
                ident = {c: st.session_state.get(f"ck_id_{c}", "") for c in ("objeto", "valor", "responsavel", "nup")}
                corpo = MP.corpo_checklist(modalidade, itens, situacoes, observacoes, ident)
                gravar("90_lista_de_verificacao.pdf",
                       gerar_pdf_documento(f"LISTA DE VERIFICAÇÃO — {modalidade}", corpo, nup=ident["nup"]))
        conf = st.session_state.get("conf_resultado")
        if conf:
            gravar("91_relatorio_conferencia.pdf", gerar_pdf_documento(
                "RELATÓRIO DE CONFERÊNCIA DO PROCESSO",
                CP.corpo_relatorio(conf["res"], conf["modalidade"], conf["arquivos"], conf["ext"])))
        indice = ["KIT DO PROCESSO", f"OM: {_om('om')}", f"NUP: {_om('nup') or '-'}",
                  f"Montado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", "", "Arquivos:"] + [f"- {x}" for x in nomes]
        indice += ["", "Documentos gerados com apoio do AtaCotada / Babilaca. Revise e assine cada peça antes de juntar ao "
                   "processo."]
        z.writestr("00_indice.txt", "\n".join(indice))
    return buf.getvalue(), nomes


def _painel_kit(bloqueado: bool):
    docs = _documentos_gerados()
    with st.expander(f"📦 Kit do processo (ZIP) — {len(docs)} documento(s) gerado(s) nesta sessão", expanded=False):
        if not docs and not st.session_state.get("conf_resultado"):
            st.caption("Gere ao menos um documento para montar o kit.")
            return
        st.caption("Reúne num ZIP os documentos gerados nesta sessão (com as edições feitas), numerados na ordem do "
                   "processo, mais a lista de verificação e o relatório de conferência, se houver.")
        st.markdown("\n".join(f"- {d['titulo'].title()}" for _c, d in docs) or "- (nenhum documento)")
        formatos = st.multiselect("Formatos", ["PDF", "Word"], default=["PDF", "Word"], key="kit_formatos")
        if st.button("📦 Montar kit", key="kit_montar", use_container_width=True, disabled=bloqueado or not formatos):
            with st.spinner("Montando o kit..."):
                st.session_state["kit_zip"], _ = _montar_kit(formatos)
        if st.session_state.get("kit_zip"):
            st.download_button("⬇️ Baixar kit do processo (.zip)", st.session_state["kit_zip"],
                               f"kit_processo_{datetime.now().strftime('%Y%m%d')}.zip", "application/zip",
                               key="kit_baixar", use_container_width=True)
        if bloqueado:
            st.caption("Preencha os dados obrigatórios da OM e do(s) signatário(s) para montar o kit.")



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

"""

TEMPLATE_ATA_RP = """## ATA DE REGISTRO DE PREÇOS

### PREÂMBULO
- **Processo Administrativo nº:** {processo}
- **Pregão Eletrônico nº:** {pregao}
- **Órgão Gerenciador:** {orgao}
- **CNPJ do Órgão:** {cnpj_orgao}
- **Vigência da Ata:** {vigencia}
- **Data de Assinatura:** {data_assinatura}

O(A) **{orgao}**, com sede em {endereco_orgao}, inscrito(a) no CNPJ sob nº {cnpj_orgao}, neste ato representado(a) pelo(a) {cargo_representante}, Sr(a). {representante}, nomeado(a) pela Portaria nº ____________, resolve REGISTRAR OS PREÇOS para eventual aquisição/contratação dos itens abaixo especificados, conforme condições estabelecidas no Edital do Pregão Eletrônico nº {pregao} e seus anexos.

---

### 1. DO OBJETO
Registro de preços para {objeto}, conforme especificações e condições estabelecidas no Termo de Referência (Anexo I do Edital).

### 2. DO FORNECEDOR REGISTRADO
- **Razão Social:** {fornecedor}
- **CNPJ:** {cnpj_fornecedor}
- **Endereço:** {endereco_fornecedor}
- **Representante Legal:** {representante_fornecedor}
- **Telefone/E-mail:** {contato_fornecedor}

### 3. DOS ITENS REGISTRADOS

| Item | Descrição | Unidade | Qtd Estimada | Valor Unitário (R$) | Valor Total (R$) |
|------|-----------|---------|-------------|--------------------|--------------------|
{tabela_itens}

**Valor Total Registrado:** {valor_total}

### 4. DA VALIDADE DA ATA
A presente Ata de Registro de Preços terá validade de **{vigencia}**, contados a partir da data de sua publicação no Diário Oficial, podendo ser prorrogada por igual período, nos termos do **Art. 84 da Lei 14.133/2021**.

### 5. DA REVISÃO E CANCELAMENTO DOS PREÇOS
5.1. Os preços registrados poderão ser revisados em decorrência de eventual redução dos preços praticados no mercado ou de fato que eleve o custo dos bens, obras ou serviços registrados, nos termos do **Art. 82, §5° da Lei 14.133/2021**.

5.2. O registro do preço do fornecedor será cancelado quando:
- Descumprir as condições da Ata de Registro de Preços;
- Não aceitar reduzir o preço registrado, na hipótese de este se tornar superior aos praticados no mercado;
- Sofrer sanção prevista nos incisos III ou IV do Art. 156 da Lei 14.133/2021.

### 6. DAS CONDIÇÕES DE ENTREGA / EXECUÇÃO
6.1. **Prazo de entrega:** {prazo_entrega}
6.2. **Local de entrega:** {local_entrega}
6.3. **Responsável pelo recebimento:** Comissão de Recebimento designada pelo Órgão Gerenciador.

### 7. DO PAGAMENTO
7.1. O pagamento será efetuado em até **{prazo_pagamento}** após o recebimento definitivo, mediante apresentação de nota fiscal/fatura.
7.2. A nota fiscal deverá ser acompanhada das certidões de regularidade fiscal e trabalhista vigentes.

### 8. DAS OBRIGAÇÕES DO FORNECEDOR
8.1. Entregar os materiais/prestar os serviços conforme especificações do Termo de Referência;
8.2. Manter, durante toda a vigência da Ata, as condições de habilitação exigidas na licitação;
8.3. Comunicar ao Órgão Gerenciador qualquer alteração de dados cadastrais;
8.4. Responsabilizar-se pelos encargos trabalhistas, previdenciários, fiscais e comerciais;
8.5. Substituir, às suas expensas, os materiais que apresentarem defeitos.

### 9. DAS OBRIGAÇÕES DO ÓRGÃO GERENCIADOR
9.1. Gerenciar a Ata de Registro de Preços;
9.2. Conduzir eventuais renegociações de preços;
9.3. Aplicar, garantida a ampla defesa e o contraditório, as penalidades cabíveis;
9.4. Providenciar a publicação da Ata e seus aditivos no Diário Oficial.

### 10. DA ADESÃO À ATA (CARONA)
10.1. A Ata de Registro de Preços poderá ser utilizada por órgãos e entidades não participantes, mediante prévia consulta ao Órgão Gerenciador e anuência do Fornecedor, nos termos do **Art. 86 da Lei 14.133/2021**.
10.2. O quantitativo para adesão não poderá exceder, por órgão/entidade, a **50% dos quantitativos** registrados na Ata.
10.3. O quantitativo total de adesões não poderá exceder, na totalidade, ao **dobro** do quantitativo registrado.

### 11. DAS PENALIDADES
Aplicam-se as sanções previstas nos **Arts. 155 a 163 da Lei 14.133/2021**, sem prejuízo das responsabilidades civil e criminal.

### 12. DA FUNDAMENTAÇÃO LEGAL
- Lei 14.133/2021, Arts. 82 a 86 (Registro de Preços)
- Decreto nº 11.462/2023 (regulamenta o SRP)
- Edital do Pregão Eletrônico nº {pregao} e seus anexos

### 13. DO FORO
Fica eleito o foro da Justiça Federal — Seção Judiciária de __________ para dirimir quaisquer questões oriundas desta Ata.

### 14. DAS DISPOSIÇÕES GERAIS
{observacoes}

"""

TEMPLATE_MINUTA_CONTRATO = """## MINUTA DE CONTRATO DE {tipo_contrato}

### PREÂMBULO
- **Processo Administrativo nº:** {processo}
- **Licitação nº:** {licitacao}
- **Modalidade:** {modalidade}
- **Contrato nº:** ____/{ano}
- **Vigência:** {vigencia}

O(A) **{orgao}** (CONTRATANTE), com sede em {endereco_orgao}, inscrito(a) no CNPJ sob nº {cnpj_orgao}, neste ato representado(a) pelo(a) {cargo_representante}, Sr(a). {representante}, e a empresa **{empresa}** (CONTRATADA), inscrita no CNPJ sob nº {cnpj_empresa}, com sede em {endereco_empresa}, representada pelo(a) Sr(a). {representante_empresa}, celebram o presente Contrato, nos termos da **Lei 14.133/2021** e demais legislações aplicáveis.

---

### CLÁUSULA PRIMEIRA — DO OBJETO
1.1. {objeto}
1.2. A CONTRATADA deverá fornecer/executar os itens/serviços conforme especificações do Termo de Referência (Anexo I).

### CLÁUSULA SEGUNDA — DOS ITENS / ESPECIFICAÇÕES

| Item | Descrição | Unidade | Quantidade | Valor Unitário (R$) | Valor Total (R$) |
|------|-----------|---------|-----------|--------------------|--------------------|
{tabela_itens}

**Valor Total do Contrato:** {valor_total}

### CLÁUSULA TERCEIRA — DO VALOR E DO PAGAMENTO
3.1. O valor total do presente contrato é de **{valor_total}** ({valor_extenso}).
3.2. O pagamento será efetuado em até **{prazo_pagamento}** após o recebimento definitivo dos materiais/serviços, mediante apresentação de nota fiscal/fatura devidamente atestada.
3.3. A nota fiscal deverá conter: descrição do item, quantidade, valor unitário e total, número do contrato e dados bancários da CONTRATADA.
3.4. Será retido na fonte os tributos previstos na legislação vigente (IR, CSLL, PIS, COFINS, ISS quando aplicável).

### CLÁUSULA QUARTA — DO PRAZO DE VIGÊNCIA E EXECUÇÃO
4.1. O presente contrato terá vigência de **{vigencia}**, contados a partir da data de sua assinatura.
4.2. O prazo de entrega/execução dos serviços será de **{prazo_execucao}**, contados a partir do recebimento da Ordem de Fornecimento/Serviço.
4.3. Os prazos poderão ser prorrogados nos termos do **Art. 107 da Lei 14.133/2021**.

### CLÁUSULA QUINTA — DA GARANTIA CONTRATUAL
5.1. A CONTRATADA deverá prestar garantia de execução do contrato no valor correspondente a **{percentual_garantia_contratual}** do valor total, em uma das seguintes modalidades (Art. 96, §1° da Lei 14.133/2021):
   - I — Caução em dinheiro ou em títulos da dívida pública;
   - II — Seguro-garantia;
   - III — Fiança bancária.
5.2. A garantia deverá ser apresentada no prazo de **10 (dez) dias úteis** após a assinatura do contrato.
5.3. A garantia somente será liberada após o integral cumprimento de todas as obrigações contratuais, inclusive quanto a multas aplicadas.

### CLÁUSULA SEXTA — DA GARANTIA DOS PRODUTOS / SERVIÇOS
6.1. Os materiais fornecidos deverão possuir garantia mínima de **{garantia_produto}**, contados a partir do recebimento definitivo.
6.2. Durante o período de garantia, a CONTRATADA deverá:
   - a) Substituir, sem ônus, os materiais que apresentarem defeitos de fabricação, vícios ou não conformidade com as especificações;
   - b) Realizar o reparo/substituição no prazo máximo de **{prazo_reparo}** após a notificação do defeito;
   - c) Arcar com todos os custos de transporte, frete, mão de obra e peças de reposição;
   - d) Fornecer assistência técnica autorizada pelo fabricante, quando aplicável.
6.3. A garantia não cobre defeitos decorrentes de mau uso, negligência, instalação inadequada ou caso fortuito e força maior devidamente comprovados.
6.4. Para serviços, a garantia cobre:
   - a) Vícios ou defeitos de execução que se manifestem dentro do prazo de garantia;
   - b) Conformidade com normas técnicas aplicáveis (ABNT, INMETRO e demais);
   - c) Reexecução integral do serviço defeituoso, às expensas da CONTRATADA.
6.5. O prazo de garantia será suspenso durante o período em que o material estiver em reparo ou substituição.
6.6. A recusa injustificada da CONTRATADA em atender chamados de garantia ensejará a aplicação das sanções previstas neste contrato.

### CLÁUSULA SÉTIMA — DAS OBRIGAÇÕES DA CONTRATADA
7.1. Executar o objeto conforme especificações do Termo de Referência e proposta apresentada;
7.2. Manter durante toda a execução do contrato as condições de habilitação exigidas na licitação;
7.3. Responsabilizar-se por todos os encargos trabalhistas, previdenciários, fiscais e comerciais;
7.4. Reparar, corrigir, remover ou substituir, às suas expensas, no total ou em parte, os materiais/serviços em que se verificarem vícios, defeitos ou incorreções;
7.5. Designar preposto para representá-la durante a execução contratual (Art. 118 da Lei 14.133/2021);
7.6. Comunicar ao CONTRATANTE qualquer anormalidade que interfira no cumprimento do contrato;
7.7. No caso de serviços continuados, apresentar mensalmente os comprovantes de regularidade fiscal, trabalhista e previdenciária;
7.8. Fornecer EPI e garantir condições de segurança do trabalho a seus empregados.

### CLÁUSULA OITAVA — DAS OBRIGAÇÕES DO CONTRATANTE
8.1. Proporcionar condições para a execução contratual;
8.2. Designar Fiscal e Gestor do Contrato (Art. 117 da Lei 14.133/2021);
8.3. Efetuar o pagamento conforme estipulado;
8.4. Comunicar à CONTRATADA as irregularidades observadas;
8.5. Aplicar as sanções cabíveis, garantidos o contraditório e a ampla defesa.

### CLÁUSULA NONA — DA FISCALIZAÇÃO
9.1. A fiscalização será exercida por servidor designado pelo CONTRATANTE, nos termos do **Art. 117 da Lei 14.133/2021**.
9.2. A fiscalização não exclui nem reduz a responsabilidade da CONTRATADA.

### CLÁUSULA DÉCIMA — DO RECEBIMENTO DO OBJETO
10.1. **Recebimento provisório:** em até **{prazo_recebimento_provisorio}** do término da entrega/execução, pelo fiscal do contrato.
10.2. **Recebimento definitivo:** em até **{prazo_recebimento_definitivo}** do recebimento provisório, pela comissão de recebimento ou gestor do contrato, após verificação da conformidade.
10.3. Nos casos de inconformidade, a CONTRATADA será notificada para correção em prazo razoável.

### CLÁUSULA DÉCIMA PRIMEIRA — DA ALTERAÇÃO CONTRATUAL
11.1. O contrato poderá ser alterado nos termos dos **Arts. 124 a 136 da Lei 14.133/2021**.
11.2. Acréscimos ou supressões de até **25%** do valor inicial atualizado (ou até 50% para reforma de edifícios/equipamentos).

### CLÁUSULA DÉCIMA SEGUNDA — DAS PENALIDADES
12.1. Pelo inadimplemento, aplicam-se as sanções dos **Arts. 155 a 163 da Lei 14.133/2021**:
   - I — Advertência;
   - II — Multa moratória de **{multa_moratoria}** por dia de atraso, limitada a **{limite_multa}** do valor do contrato;
   - III — Multa compensatória de até **{multa_compensatoria}** do valor total, por inexecução parcial ou total;
   - IV — Impedimento de licitar e contratar pelo prazo de até 3 anos;
   - V — Declaração de inidoneidade para licitar ou contratar.
12.2. As multas poderão ser descontadas da garantia, de pagamentos devidos ou cobradas judicialmente.

### CLÁUSULA DÉCIMA TERCEIRA — DA RESCISÃO
13.1. O contrato poderá ser rescindido nas hipóteses previstas nos **Arts. 137 a 139 da Lei 14.133/2021**.

### CLÁUSULA DÉCIMA QUARTA — DA FUNDAMENTAÇÃO LEGAL
- Lei 14.133/2021 (Lei de Licitações e Contratos)
- Decreto nº 11.462/2023 (quando aplicável — SRP)
- IN SEGES/ME nº 5/2017 ou IN SEGES/ME nº 58/2022 (conforme o caso)
- Edital da Licitação nº {licitacao} e seus anexos

### CLÁUSULA DÉCIMA QUINTA — DO FORO
Fica eleito o foro da Justiça Federal — Seção Judiciária de __________ para dirimir quaisquer questões oriundas deste contrato.

### CLÁUSULA DÉCIMA SEXTA — DAS DISPOSIÇÕES GERAIS
{observacoes}

---

**CONTRATANTE:**
{orgao}
Nome: {representante}
Cargo: {cargo_representante}

**CONTRATADA:**
{empresa}
Nome: {representante_empresa}

**TESTEMUNHAS:**
1. Nome: _________________ CPF: _________________
2. Nome: _________________ CPF: _________________

"""


def _fmt_brl(valor: float) -> str:
    """Formata um valor float em reais BR: R$ 1.234,56"""
    if not valor:
        return "-"
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _registrar_mapa(itens: list[dict], observacoes: str = ""):
    """Mapa comparativo no padrão dos documentos oficiais (PDF/Word editáveis) e planilha Excel guardada para download."""
    _registrar_doc(MP.DOC_MAPA, "MAPA COMPARATIVO DE PREÇOS", MP.corpo_mapa_comparativo(itens, observacoes),
                   "mapa_comparativo")
    st.session_state["mapa_xlsx"] = gerar_mapa_comparativo_xlsx(itens, observacoes=observacoes)


def gerar_mapa_comparativo_xlsx(itens: list[dict], observacoes: str = "") -> bytes:
    """Gera planilha Excel editável do mapa comparativo de preços."""
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Mapa Comparativo"

    # Estilos
    header_font = Font(name="Calibri", bold=True, size=10, color="FFFFFF")
    header_fill = PatternFill(start_color="001A4D", end_color="001A4D", fill_type="solid")
    total_fill = PatternFill(start_color="F0F5FF", end_color="F0F5FF", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    center = Alignment(horizontal="center", vertical="center")
    right_align = Alignment(horizontal="right", vertical="center")

    # Título
    ws.merge_cells("A1:I1")
    ws["A1"] = "MAPA COMPARATIVO DE PREÇOS"
    ws["A1"].font = Font(name="Calibri", bold=True, size=14, color="001A4D")
    ws["A1"].alignment = Alignment(horizontal="center")

    ws.merge_cells("A2:I2")
    ws["A2"] = f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    ws["A2"].font = Font(name="Calibri", size=9, color="666666")
    ws["A2"].alignment = Alignment(horizontal="right")

    # Cabeçalho
    headers = ["Item", "Descrição", "Qtd", "Fornecedor 1", "Fornecedor 2", "Fornecedor 3", "Média", "Mediana", "Total Estimado"]
    larguras = [6, 40, 8, 16, 16, 16, 16, 16, 18]
    for col_idx, (header, larg) in enumerate(zip(headers, larguras), 1):
        cell = ws.cell(row=4, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = thin_border
        cell.alignment = center
        ws.column_dimensions[get_column_letter(col_idx)].width = larg

    # Dados
    total_geral = 0.0
    for i, item in enumerate(itens, 1):
        row = i + 4
        precos = [item.get("preco1", 0), item.get("preco2", 0), item.get("preco3", 0)]
        validos = [p for p in precos if p > 0]
        media = sum(validos) / len(validos) if validos else 0
        mediana = MP._mediana(validos)
        qtd = item.get("quantidade", 1) or 1
        total_item = media * qtd
        total_geral += total_item

        valores = [i, item.get("descricao", ""), int(qtd),
                    item.get("preco1", 0), item.get("preco2", 0), item.get("preco3", 0),
                    media, mediana, total_item]
        for col_idx, val in enumerate(valores, 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.border = thin_border
            if col_idx >= 4:
                cell.number_format = '#,##0.00'
                cell.alignment = right_align
            elif col_idx in (1, 3):
                cell.alignment = center

    # Total geral
    total_row = len(itens) + 5
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=8)
    cell_label = ws.cell(row=total_row, column=1, value="TOTAL GERAL")
    cell_label.font = Font(name="Calibri", bold=True, size=10)
    cell_label.fill = total_fill
    cell_label.border = thin_border
    cell_label.alignment = Alignment(horizontal="right")
    cell_total = ws.cell(row=total_row, column=9, value=total_geral)
    cell_total.font = Font(name="Calibri", bold=True, size=10)
    cell_total.fill = total_fill
    cell_total.border = thin_border
    cell_total.number_format = '#,##0.00'
    cell_total.alignment = right_align

    # Observações
    if observacoes and observacoes.strip():
        obs_row = total_row + 2
        ws.cell(row=obs_row, column=1, value="OBSERVAÇÕES:").font = Font(name="Calibri", bold=True, size=10)
        ws.merge_cells(start_row=obs_row + 1, start_column=1, end_row=obs_row + 1, end_column=9)
        ws.cell(row=obs_row + 1, column=1, value=observacoes.strip())

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


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
    """Usa IA para classificar o risco jurídico com mapa de riscos."""
    prompt_risco = (
        "Analise o cenário de contratação pública abaixo e produza:\n\n"
        "1. **CLASSIFICAÇÃO GERAL**: Risco BAIXO, MÉDIO ou ALTO com justificativa.\n\n"
        "2. **MAPA DE RISCOS** — Para CADA categoria abaixo, classifique Probabilidade "
        "(Baixa / Média / Alta) e Impacto (Baixo / Médio / Alto), e descreva brevemente o risco:\n"
        "   - Risco de Nulidade do Processo\n"
        "   - Risco de Responsabilização do Gestor\n"
        "   - Risco de Impugnação / Recurso\n"
        "   - Risco de Prejuízo ao Erário\n"
        "   - Risco Reputacional\n\n"
        "Use formato de tabela Markdown para o mapa de riscos com colunas: "
        "Categoria | Probabilidade | Impacto | Nível | Descrição\n\n"
        "3. **RECOMENDAÇÕES** de mitigação para os riscos identificados.\n\n"
        "Fundamente toda a análise na Lei 14.133/2021 e jurisprudência do TCU.\n\n"
        f"CENÁRIO: {descricao_cenario}"
    )
    ctx = buscar_base_juridica(descricao_cenario)
    system = _build_system_prompt(ctx)
    return chamar_ia([{"role": "user", "content": prompt_risco}], system)


# ============================================================
# CHECKLIST POR MODALIDADE
# ============================================================
# Itens, fundamentos e atalhos: modelos_processo.CHECKLIST (testado sem o Streamlit).
CHECKLIST_MODALIDADES = MP.CHECKLIST

# Informações explicativas de cada modalidade
INFO_MODALIDADES = {
    "Dispensa eletrônica (art. 75, I e II)": {
        "descricao": (
            "A **dispensa eletrônica** é a contratação direta por valor (art. 75, I e II, da Lei 14.133/2021) "
            "precedida de aviso no sítio oficial por no mínimo 3 dias úteis (art. 75, §3º), com disputa no "
            "Compras.gov.br, regulada pela **IN SEGES/ME nº 67/2021**."
        ),
        "quando_aplicar": (
            "- **Outros serviços e compras** com valor inferior a **{LIM_II}** (art. 75, II);\n"
            "- **Obras, serviços de engenharia e manutenção de veículos** com valor inferior a **{LIM_I}** (art. 75, I);\n"
            "- O limite considera o **somatório do exercício** para objetos do mesmo ramo de atividade (art. 75, §1º);\n"
            "- Sempre que a dispensa se enquadrar nos incisos I ou II do Art. 75."
        ),
        "limites": (
            "| Tipo | Limite (atualizado) |\n"
            "|------|---------------------|\n"
            "| Outros serviços e compras (art. 75, II) | {LIM_II} |\n"
            "| Obras, serviços de engenharia e manutenção de veículos (art. 75, I) | {LIM_I} |\n\n"
            "*{NOTA_LIMITES}*"
        ),
        "como_montar": (
            "1. Elaborar DFD e TR com especificação clara do objeto;\n"
            "2. Realizar pesquisa de preços (IN 65/2021 — mín. 3 fontes);\n"
            "3. Publicar Aviso de Dispensa Eletrônica no PNCP (prazo mín. 3 dias úteis);\n"
            "4. Abrir sessão no ComprasGov para recebimento de propostas;\n"
            "5. Avaliar propostas e habilitação do vencedor;\n"
            "6. Adjudicar, obter parecer jurídico e autorizar;\n"
            "7. Emitir nota de empenho e publicar resultado no PNCP."
        ),
    },
    "Pregão Eletrônico": {
        "descricao": (
            "O **Pregão Eletrônico** é a modalidade obrigatória para aquisição de **bens e "
            "serviços comuns** (Art. 6°, XLI e Art. 28, I, Lei 14.133/2021). Caracteriza-se pela "
            "inversão de fases (proposta antes da habilitação) e lances em tempo real."
        ),
        "quando_aplicar": (
            "- Aquisição de **bens comuns** (qualquer valor acima do limite de dispensa);\n"
            "- Contratação de **serviços comuns** (inclusive de engenharia, quando aplicável);\n"
            "- Sempre que o objeto puder ser definido por especificações usuais de mercado."
        ),
        "limites": (
            "**Não possui limite máximo de valor.** O Pregão Eletrônico pode ser utilizado para "
            "qualquer valor, desde que o objeto seja bem ou serviço comum.\n\n"
            "Abaixo de {LIM_II} (compras e serviços) cabe a dispensa por valor (art. 75, II)."
        ),
        "como_montar": (
            "1. Elaborar DFD, ETP e Mapa de Riscos;\n"
            "2. Elaborar Termo de Referência detalhado;\n"
            "3. Realizar pesquisa de preços (IN 65/2021);\n"
            "4. Elaborar minuta do Edital e obter parecer jurídico;\n"
            "5. Designar pregoeiro e equipe de apoio;\n"
            "6. Publicar Edital no PNCP e DOU (prazo mín. 8 dias úteis);\n"
            "7. Realizar sessão pública com lances no ComprasGov;\n"
            "8. Habilitar vencedor, adjudicar e homologar;\n"
            "9. Publicar resultado no PNCP."
        ),
    },
    "Dispensa de Licitação — outras hipóteses do art. 75 (TJDL)": {
        "descricao": (
            "O **Termo de Justificativa de Dispensa de Licitação (TJDL)** é usado quando a "
            "administração precisa contratar **sem licitar**, em hipóteses taxativamente "
            "previstas no **Art. 75 da Lei 14.133/2021**, como valor baixo, emergência, "
            "ou situações específicas."
        ),
        "quando_aplicar": (
            "- Contratações de **baixo valor** (Art. 75, I e II) sem cotação eletrônica;\n"
            "- **Emergência ou calamidade** (Art. 75, VIII) — prazo máx. 1 ano;\n"
            "- **Guerra ou grave perturbação da ordem** (Art. 75, VII);\n"
            "- **Materiais de uso das Forças Armadas** sem similaridade ou de padronização (Art. 75, IV, g);\n"
            "- **Suprimento de efetivos** em estada eventual (Art. 75, IV, i);\n"
            "- Licitação deserta ou fracassada há menos de 1 ano (Art. 75, III) e demais incisos do Art. 75."
        ),
        "limites": (
            "| Hipótese | Limite |\n"
            "|----------|--------|\n"
            "| Obras/serviços de engenharia (Art. 75, I) | {LIM_I} |\n"
            "| Bens/serviços comuns (Art. 75, II) | {LIM_II} |\n"
            "| Emergência (Art. 75, VIII) | Sem limite de valor (prazo máx. 1 ano) |\n\n"
            "*Obs: No TJDL, a contratação é feita diretamente com fornecedor escolhido, sem cotação eletrônica.*"
        ),
        "como_montar": (
            "1. Elaborar DFD com justificativa da necessidade;\n"
            "2. Elaborar TJDL com enquadramento legal (inciso específico do Art. 75);\n"
            "3. Justificar razão da escolha do fornecedor e do preço;\n"
            "4. Realizar pesquisa de preços (IN 65/2021);\n"
            "5. Obter proposta formal e documentação do fornecedor;\n"
            "6. Obter parecer jurídico;\n"
            "7. Autorização da autoridade competente;\n"
            "8. Emitir nota de empenho e publicar no PNCP."
        ),
    },
    "Inexigibilidade de Licitação (TJIL)": {
        "descricao": (
            "O **Termo de Justificativa de Inexigibilidade de Licitação (TJIL)** é utilizado "
            "quando há **inviabilidade de competição**, conforme **Art. 74 da Lei 14.133/2021**. "
            "Não se trata de escolher não licitar — a licitação é impossível."
        ),
        "quando_aplicar": (
            "- **Fornecedor exclusivo** comprovado (Art. 74, I);\n"
            "- **Serviço técnico especializado** com profissional ou empresa de **notória especialização** (Art. 74, III);\n"
            "- Contratação de **artista consagrado** (Art. 74, II);\n"
            "- **Credenciamento** (Art. 74, IV) e **aquisição ou locação de imóvel** (Art. 74, V);\n"
            "- Serviços de **treinamento** com profissional/empresa de notória especialização."
        ),
        "limites": (
            "**Não possui limite de valor.** A inexigibilidade pode ser utilizada para qualquer valor, "
            "desde que comprovada a inviabilidade de competição.\n\n"
            "*Atenção: a justificativa de preço é obrigatória (Art. 72, VII), com notas fiscais a outros contratantes (Art. 23, §4º).*"
        ),
        "como_montar": (
            "1. Elaborar DFD com descrição detalhada da necessidade;\n"
            "2. Elaborar TJIL demonstrando a inviabilidade de competição;\n"
            "3. Comprovar exclusividade (atestado) ou notória especialização;\n"
            "4. Justificar escolha do fornecedor e compatibilidade do preço;\n"
            "5. Obter proposta formal e habilitação do fornecedor;\n"
            "6. Obter parecer jurídico;\n"
            "7. Autorização da autoridade competente;\n"
            "8. Emitir nota de empenho e publicar no PNCP."
        ),
    },
    "Adesão a Ata de Registro de Preços (carona)": {
        "descricao": (
            "A **Adesão a Ata de Registro de Preços (Carona)** permite que um órgão ou entidade "
            "que **não participou** da licitação original adira a uma Ata vigente de outro "
            "órgão, conforme **Art. 86 da Lei 14.133/2021**."
        ),
        "quando_aplicar": (
            "- Quando existe **Ata de Registro de Preços vigente** de outro órgão com o objeto desejado;\n"
            "- Quando a adesão for **mais vantajosa** que realizar novo processo;\n"
            "- Quando o órgão gerenciador e o fornecedor **concordarem** com a adesão;\n"
            "- Respeitado o limite de até **50% dos quantitativos** registrados na Ata por órgão (Art. 86, §4°);\n"
            "- Órgão **federal** só adere a ata **federal** (Art. 86, §8º)."
        ),
        "limites": (
            "| Regra | Limite |\n"
            "|-------|--------|\n"
            "| Quantitativo máximo por adesão | 50% do quantitativo registrado |\n"
            "| Quantitativo total de adesões | Até o dobro do quantitativo original |\n\n"
            "*O preço deve ser compatível com o praticado no mercado (pesquisa obrigatória).*"
        ),
        "como_montar": (
            "1. Elaborar DFD e ETP justificando a adesão;\n"
            "2. Demonstrar vantajosidade em relação a novo processo;\n"
            "3. Realizar pesquisa de preços para comprovar compatibilidade;\n"
            "4. Obter cópia da Ata e do Edital original;\n"
            "5. Solicitar autorização ao órgão gerenciador;\n"
            "6. Obter concordância do fornecedor;\n"
            "7. Verificar habilitação e regularidade fiscal do fornecedor;\n"
            "8. Obter parecer jurídico e autorização da autoridade;\n"
            "9. Publicar no PNCP."
        ),
    },
    "Participação em IRP (Intenção de Registro de Preços)": {
        "descricao": (
            "A **Participação em IRP** ocorre quando seu órgão identifica uma **Intenção de "
            "Registro de Preços** publicada por outro órgão (gerenciador) e decide aderir como "
            "**órgão participante**, informando seus quantitativos para serem incluídos na "
            "licitação, conforme **Art. 86 da Lei 14.133/2021** e **Decreto 11.462/2023**. "
            "Diferente da Adesão (Carona), aqui o órgão participa **antes** da licitação."
        ),
        "quando_aplicar": (
            "- Quando o órgão identifica uma **IRP publicada no ComprasGov** com objeto compatível;\n"
            "- Quando há **demanda real** pelo bem ou serviço registrado;\n"
            "- Quando a participação é mais vantajosa que conduzir licitação própria;\n"
            "- Para **planejar aquisições futuras** com preços já registrados;\n"
            "- O prazo para manifestar interesse é de **mínimo 8 dias úteis** após publicação da IRP."
        ),
        "limites": (
            "**Não possui limite financeiro próprio.** O valor depende do quantitativo informado "
            "e dos preços que forem registrados na Ata.\n\n"
            "| Regra | Detalhe |\n"
            "|-------|--------|\n"
            "| Prazo para manifestar interesse | Mínimo 8 dias úteis (Art. 86, caput) |\n"
            "| Quantitativo | Definido pelo órgão participante conforme sua demanda |\n"
            "| Vigência da Ata | 1 ano, prorrogável por igual período se o preço for vantajoso (Art. 84) |\n"
            "| Obrigação de contratar | Não obrigatória para participante (facultativa) |\n\n"
            "*Vantagem: o órgão participante tem prioridade sobre órgãos não participantes (carona).*"
        ),
        "como_montar": (
            "1. Monitorar as IRPs publicadas no **ComprasGov** que atendam à necessidade;\n"
            "2. Elaborar **DFD** justificando a demanda e a participação na IRP;\n"
            "3. Elaborar **ETP** e **TR** com especificações e quantitativos do órgão;\n"
            "4. Realizar pesquisa de preços para comprovar compatibilidade;\n"
            "5. Registrar manifestação de interesse no ComprasGov **dentro do prazo de 8 dias úteis**;\n"
            "6. Enviar planilha de quantitativos e especificações ao órgão gerenciador;\n"
            "7. Obter autorização da autoridade competente;\n"
            "8. Acompanhar a sessão pública da licitação;\n"
            "9. Após homologação, receber cópia da Ata de Registro de Preços;\n"
            "10. Quando necessitar, emitir nota de empenho para efetivar a contratação."
        ),
    },
    "Prorrogação da vigência de Ata de Registro de Preços": {
        "descricao": (
            "A **Renovação (prorrogação) de Ata de Registro de Preços** permite estender a "
            "vigência da Ata por igual período (**1 ano**), conforme **Art. 84, caput, da Lei 14.133/2021**. "
            "A prorrogação depende de concordância do fornecedor e comprovação de que os preços "
            "continuam vantajosos em relação ao mercado."
        ),
        "quando_aplicar": (
            "- Quando a **Ata de Registro de Preços** está próxima do vencimento (vigência original de 1 ano);\n"
            "- Quando os **preços registrados continuam compatíveis** com o mercado;\n"
            "- Quando há **interesse da Administração** em manter o registro;\n"
            "- Quando o **fornecedor concorda** com a prorrogação nas mesmas condições;\n"
            "- Prorrogação permitida por **igual período** (1 ano), comprovado o preço vantajoso (Art. 84, caput)."
        ),
        "limites": (
            "| Regra | Detalhe |\n"
            "|-------|--------|\n"
            "| Vigência original da Ata | Até 1 ano |\n"
            "| Prorrogação máxima | Mais 1 ano (total máximo: 2 anos) |\n"
            "| Condição obrigatória | Pesquisa demonstrando vantajosidade dos preços |\n"
            "| Concordância do fornecedor | Obrigatória |\n\n"
            "*A prorrogação não é automática — requer análise de vantajosidade e formalização.*"
        ),
        "como_montar": (
            "1. Verificar se a Ata ainda está dentro do prazo de vigência;\n"
            "2. Realizar **pesquisa de preços atualizada** para comprovar vantajosidade;\n"
            "3. Solicitar **concordância formal do fornecedor** para prorrogação;\n"
            "4. Verificar **regularidade fiscal e trabalhista** atualizada do fornecedor;\n"
            "5. Elaborar **justificativa técnica** da necessidade de prorrogação;\n"
            "6. Consultar o **órgão gerenciador** da Ata (se não for o próprio órgão);\n"
            "7. Obter **parecer jurídico** sobre a prorrogação;\n"
            "8. Obter **autorização da autoridade competente**;\n"
            "9. Formalizar o **termo de prorrogação da Ata**;\n"
            "10. **Publicar** a prorrogação no PNCP."
        ),
    },
    "Termo Aditivo": {
        "descricao": (
            "O **Termo Aditivo** é o instrumento formal utilizado para **modificar cláusulas contratuais** "
            "originalmente pactuadas, conforme **Arts. 124 a 136 da Lei 14.133/2021**. Diferente do "
            "apostilamento, o Termo Aditivo exige **acordo bilateral** (assinatura de ambas as partes) "
            "e é obrigatório quando a alteração afeta o equilíbrio econômico-financeiro ou modifica "
            "condições substanciais do contrato."
        ),
        "quando_aplicar": (
            "**Casos em que ocorre o Termo Aditivo (Art. 124, Lei 14.133/2021):**\n\n"
            "- **Acréscimo ou supressão** de quantitativos (até 25% do valor inicial, ou 50% para reforma — Art. 125);\n"
            "- **Prorrogação de prazo** de vigência ou execução do contrato;\n"
            "- **Alteração do objeto** por necessidade superveniente (modificação do projeto, especificações);\n"
            "- **Reequilíbrio econômico-financeiro** por fatos imprevisíveis (Art. 124, II, d);\n"
            "- **Substituição de garantia** contratual;\n"
            "- **Alteração da forma de pagamento** (nunca antecipando sem contraprestação);\n"
            "- **Inclusão ou exclusão de obrigações** das partes;\n"
            "- **Alteração do regime de execução** (quando justificado tecnicamente);\n"
            "- Qualquer modificação que altere **cláusulas essenciais** do contrato."
        ),
        "limites": (
            "| Regra | Limite |\n"
            "|-------|--------|\n"
            "| Acréscimo (bens/serviços/obras) | Até 25% do valor inicial atualizado (Art. 125) |\n"
            "| Acréscimo (reforma de edifício/equipamento) | Até 50% do valor inicial (Art. 125, §1°) |\n"
            "| Supressão | Até 25% do valor inicial atualizado |\n"
            "| Supressão acima de 25% | Apenas por acordo entre as partes (Art. 125, §2°) |\n"
            "| Prorrogação (serviços contínuos) | Até 5 anos, prorrogável por mais 5 (Art. 107) |\n"
            "| Prorrogação (outros contratos) | Conforme prazo máximo do Art. 105/106 |\n\n"
            "*O Termo Aditivo não pode descaracterizar o objeto original do contrato nem do edital que o originou.*"
        ),
        "como_montar": (
            "1. Identificar a **necessidade da alteração** e a hipótese legal (Art. 124 ou 125);\n"
            "2. Elaborar **justificativa técnica e/ou econômica** detalhada;\n"
            "3. Quando envolver valores, realizar **pesquisa de preços** atualizada;\n"
            "4. Verificar se a alteração está **dentro dos limites legais** (25% ou 50%);\n"
            "5. Obter **concordância formal do contratado** (quando necessário);\n"
            "6. Verificar **regularidade fiscal e trabalhista** do contratado;\n"
            "7. Elaborar **demonstrativo do impacto financeiro**;\n"
            "8. Obter **parecer jurídico** (Art. 53, Lei 14.133/2021);\n"
            "9. Obter **autorização da autoridade competente**;\n"
            "10. Elaborar e assinar a **minuta do Termo Aditivo** (ambas as partes);\n"
            "11. Publicar o **extrato do Termo Aditivo no PNCP** (Art. 94);\n"
            "12. Atualizar o registro no **sistema de gestão de contratos**."
        ),
    },
    "Apostilamento": {
        "descricao": (
            "O **Apostilamento** é o registro administrativo **unilateral** de alterações contratuais "
            "que **não modificam cláusulas essenciais** do contrato, conforme **Art. 136 da Lei 14.133/2021**. "
            "É mais simples que o Termo Aditivo — não exige assinatura do contratado nem parecer jurídico "
            "obrigatório. Utilizado principalmente para **reajustes de preços** previstos no contrato e "
            "**compensações/penalizações** financeiras previstas."
        ),
        "quando_aplicar": (
            "**Casos em que ocorre o Apostilamento (Art. 136, Lei 14.133/2021):**\n\n"
            "- **Reajuste de preços** previsto no contrato (por índice — IPCA, INPC, IGP-M ou setorial);\n"
            "- **Repactuação** de contratos de serviços contínuos com dedicação exclusiva de mão de obra;\n"
            "- **Compensações ou penalizações financeiras** por condições de pagamento;\n"
            "- **Empenho de dotações orçamentárias** complementares até o limite do contrato;\n"
            "- Alterações que **não modifiquem** o objeto, as condições de execução nem o equilíbrio contratual;\n\n"
            "**NÃO cabe apostilamento quando:**\n"
            "- Houver alteração de **cláusula essencial** (prazo, objeto, condições de execução);\n"
            "- For necessário **acréscimo ou supressão** de quantitativos;\n"
            "- A alteração exigir **concordância do contratado** → usar Termo Aditivo."
        ),
        "limites": (
            "| Regra | Detalhe |\n"
            "|-------|--------|\n"
            "| Natureza | Ato **unilateral** da Administração |\n"
            "| Assinatura do contratado | **Não necessária** |\n"
            "| Parecer jurídico | Não obrigatório (recomendável em repactuações complexas) |\n"
            "| Prazo mínimo para reajuste | 1 ano da data do orçamento estimado (Art. 92, §3º); repactuação, Art. 135 |\n"
            "| Índice de reajuste | O previsto no contrato/edital |\n"
            "| Forma de registro | Anotação no verso/margem do contrato ou documento apartado |\n\n"
            "*O apostilamento é mais ágil que o Termo Aditivo, mas limitado a alterações não substanciais.*"
        ),
        "como_montar": (
            "1. Identificar o **tipo de apostilamento** (reajuste por índice, repactuação, etc.);\n"
            "2. Verificar se o **reajuste está previsto** no contrato/edital e qual o **índice aplicável**;\n"
            "3. Confirmar que transcorreu o **período mínimo de 1 ano** (Art. 92, §3º; repactuação, Art. 135);\n"
            "4. Elaborar **memória de cálculo** detalhada com o índice acumulado;\n"
            "5. Elaborar **planilha** com os novos valores unitários e globais;\n"
            "6. Obter **parecer jurídico** quando exigido pelo órgão ou em casos complexos;\n"
            "7. Obter **autorização da autoridade competente**;\n"
            "8. Registrar o apostilamento no **verso/margem do contrato** ou em documento apartado;\n"
            "9. **Publicar** o apostilamento no PNCP;\n"
            "10. **Atualizar** os valores no sistema de gestão de contratos e empenho."
        ),
    },
}


# limites de dispensa num só lugar (modelos_processo.LIMITES_DISPENSA)
for _info in INFO_MODALIDADES.values():
    for _campo, _texto in _info.items():
        _info[_campo] = (_texto.replace("{LIM_I}", MP.brl(MP.LIMITES_DISPENSA["inciso_I"]))
                         .replace("{LIM_II}", MP.brl(MP.LIMITES_DISPENSA["inciso_II"]))
                         .replace("{NOTA_LIMITES}", MP.nota_limites())
                         .replace("$", "\\$"))   # "R$ ... R$" na mesma linha viraria fórmula no Markdown

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
_acanto_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Projeto Adesões", "acanto.png")
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

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="babilaca-header">
    <h1>🧠 O Babilaca (IA)</h1>
    <p>Assistente Inteligente para Licitações e Contratações Públicas — Lei 14.133/2021</p>
</div>
<div class="disclaimer-box">
    ⚠️ Ferramenta de apoio.
</div>
""", unsafe_allow_html=True)

# ============================================================
# ABAS PRINCIPAIS
# ============================================================
ABA_DOCUMENTOS = "📄 Gerar Documentos com IA"
# itens escolhidos na página Adesões: abre o ofício de adesão já preenchido
_pre_ofad = st.session_state.pop("_ofad_prefill", None)
if _pre_ofad:
    st.session_state["tipo_doc_sel"] = MP.DOC_OF_ADESAO
    for _campo in ("ata", "gerenciador", "uasg", "objeto", "licitacao"):
        st.session_state[f"ofad_{_campo}"] = str(_pre_ofad.get(_campo) or "")
    st.session_state["_ofad_itens_ini"] = _pre_ofad.get("itens") or []
    if _pre_ofad.get("justificativa"):
        st.session_state["ofad_just"] = _pre_ofad["justificativa"]
    if _pre_ofad.get("relatorio_vantajosidade"):
        _registrar_doc(MP.DOC_VANTAJOSIDADE, "RELATÓRIO DE VANTAJOSIDADE DA ADESÃO", _pre_ofad["relatorio_vantajosidade"],
                       "relatorio_vantajosidade_adesao")
        st.session_state["ofad_anexos"] = "Relatório de vantajosidade da adesão"
    st.session_state["_ofad_itens_ver"] = int(st.session_state.get("_ofad_itens_ver") or 0) + 1
    st.session_state["babilaca_aba"] = ABA_DOCUMENTOS
    st.toast("✉️ Ofício de adesão preenchido com os itens escolhidos em Adesões.")

tab_chat, tab_docs, tab_checklist, tab_conferencia, tab_fracionamento = st.tabs([
    "💬 Chat IA",
    ABA_DOCUMENTOS,
    "📋 Checklist de Processo",
    "🔎 Conferência do Processo",
    "⚖️ Limite de Dispensa",
], key="babilaca_aba", on_change="rerun")  # com key, a página pode abrir direto na aba Documentos

# ============================================================
# TAB 1 — CHAT IA
# ============================================================
with tab_chat:
    # Contador de sessão
    _s_reqs = st.session_state.get("babilaca_sessao_reqs", 0)
    _s_custo = st.session_state.get("babilaca_sessao_custo", 0.0)
    _s_tk_in = st.session_state.get("babilaca_sessao_tokens_in", 0)
    _s_tk_out = st.session_state.get("babilaca_sessao_tokens_out", 0)
    _cor_custo = "#22c55e" if _s_custo < 0.01 else "#f59e0b" if _s_custo < 0.10 else "#ef4444"
    st.markdown(f"""
    <div class="chat-console">
        <div class="chat-console-top">
            <div class="chat-console-title">
                <div class="chat-console-avatar">🧠</div>
                <div>
                    <h3>Babilaca</h3>
                    <p>Assistente para licitações e contratações públicas</p>
                </div>
            </div>
            <span class="online-indicator">Pronto para ajudar</span>
            <div class="chat-metrics">
                <div class="chat-metric"><span class="chat-metric-label">Sessão</span><span class="chat-metric-value">{_s_reqs} req</span></div>
                <div class="chat-metric"><span class="chat-metric-label">Gasto</span><span class="chat-metric-value" style="color:{_cor_custo};">${_s_custo:.6f}</span></div>
                <div class="chat-metric"><span class="chat-metric-label">Tokens</span><span class="chat-metric-value">{_s_tk_in:,} in · {_s_tk_out:,} out</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Barra de ações da conversa
    st.markdown('<div class="chat-actions">', unsafe_allow_html=True)
    tb_col1, tb_col2, tb_col3 = st.columns([4, 1.3, 1.3])

    with tb_col1:
        st.markdown('<p style="color:#93c5fd;font-size:0.8rem;margin:0.45rem 0;">Converse, envie documentos e receba orientações com base na legislação aplicável.</p>', unsafe_allow_html=True)
    with tb_col2:
        if st.button("🗑️ Limpar conversa", use_container_width=True):
            st.session_state["babilaca_messages"] = []
            st.session_state.pop("_arquivo_texto", None)
            st.session_state.pop("_arquivo_nome", None)
            st.rerun()
    with tb_col3:
        arquivo_chat = st.file_uploader(
            "📎 Anexar",
            type=["pdf", "xlsx", "xls", "csv"],
            key="chat_upload",
            label_visibility="collapsed",
        )
    st.markdown('</div>', unsafe_allow_html=True)

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
        # Persistir no session_state para não perder no rerun
        if texto_arquivo:
            st.session_state["_arquivo_texto"] = texto_arquivo
            st.session_state["_arquivo_nome"] = arquivo_chat.name
    else:
        # Recuperar texto previamente extraído (se houver)
        texto_arquivo = st.session_state.get("_arquivo_texto", "")

    # Histórico de mensagens
    for idx, msg in enumerate(st.session_state["babilaca_messages"]):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "user":
                if st.button("🔄 Reenviar", key=f"resend_{idx}"):
                    st.session_state["_reenviar_prompt"] = msg["content"]
                    st.rerun()

    # Auto-scroll para manter sempre no final da conversa
    if st.session_state["babilaca_messages"]:
        st.markdown(
            """<div id="chat-anchor"></div>
            <script>
            (function() {
                const anchor = window.parent.document.getElementById('chat-anchor');
                if (anchor) anchor.scrollIntoView({behavior: 'smooth', block: 'end'});
                const chatContainer = window.parent.document.querySelector('section[data-testid="stChatMessageContainer"]');
                if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
            })();
            </script>""",
            unsafe_allow_html=True,
        )

    # Processar reenvio de mensagem (botão 🔄)
    _reenviar = st.session_state.pop("_reenviar_prompt", None)

    # Input do usuário
    if prompt := (_reenviar or st.chat_input("Digite sua pergunta sobre licitações, legislação ou contratações...")):
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

            # Botão salvar resposta (joinha)
            if st.button("👍", key=f"save_{len(st.session_state['babilaca_messages'])}"):
                salvar_resposta(prompt, resposta)
                st.toast("Resposta salva!")

        st.session_state["babilaca_messages"].append({"role": "assistant", "content": resposta})
        # Auto-scroll para o final da conversa
        st.markdown(
            """<script>
            const chatContainer = window.parent.document.querySelector('section[data-testid="stChatMessageContainer"]');
            if (chatContainer) { chatContainer.scrollTop = chatContainer.scrollHeight; }
            // Fallback: scroll the main container
            const main = window.parent.document.querySelector('.main');
            if (main) { main.scrollTop = main.scrollHeight; }
            </script>""",
            unsafe_allow_html=True,
        )

# ============================================================
# TAB 2 — DOCUMENTOS
# ============================================================
with tab_docs:
    st.markdown("""
    <div class="workspace-console document-workspace">
        <div class="workspace-console-content">
            <div class="workspace-console-icon">📄</div>
            <div><h3>Central de Documentos</h3><p>Estruture peças do processo com dados, anexos e contexto jurídico.</p></div>
            <span class="workspace-console-badge">GERAÇÃO ASSISTIDA</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    _faltam_doc = _pendencias_documento()
    with st.expander("🏛️ Dados obrigatórios: OM e signatário(s) — cabeçalho e assinatura dos documentos", expanded=bool(_faltam_doc)):
        st.caption("Preencha antes de gerar: os dados valem para todos os documentos desta sessão. Padrão gráfico da SGM-105 "
                   "(MaTDoc): Armas Nacionais, MARINHA DO BRASIL, nome da OM, local e data, Carlito/Calibri 12 e paginação.")
        _perfil_arq = st.file_uploader("📂 Carregar perfil da OM salvo (.json)", type=["json"], key="docom_perfil_arq",
                                       help="Arquivo baixado no botão 'Salvar perfil da OM', no fim deste quadro.")
        if _perfil_arq is not None:
            _assin = hashlib.md5(_perfil_arq.getvalue()).hexdigest()
            if st.session_state.get("_docom_perfil_aplicado") != _assin:
                try:
                    _aplicar_perfil_om(json.loads(_perfil_arq.getvalue().decode("utf-8")))
                    st.session_state["_docom_perfil_aplicado"] = _assin
                    st.success("Perfil da OM carregado.")
                except Exception as _erro:
                    st.error(f"Arquivo de perfil inválido: {_erro}")
        st.text_input("Nome da OM por extenso *", key="docom_om", placeholder="Escreva o nome completo da sua Organização Militar")
        _o3, _o4, _o5, _o6 = st.columns([2, 1, 2, 2])
        with _o3:
            st.text_input("Cidade *", key="docom_cidade", placeholder="Cidade da OM")
        with _o4:
            st.text_input("UF *", key="docom_uf", placeholder="UF", max_chars=2)
        with _o5:
            st.text_input("NUP / nº do processo", key="docom_nup", placeholder="Opcional")
        with _o6:
            st.date_input("Data do documento", key="docom_data", format="DD/MM/YYYY")
        st.number_input("Quantidade de signatários", min_value=1, max_value=4, step=1, key="docom_n_assinantes",
                        help="Com mais de um, informe do mais antigo para o mais moderno: as assinaturas saem da esquerda "
                             "para a direita e de cima para baixo (MaTDoc 1.11).")
        for _i in range(int(st.session_state.get("docom_n_assinantes") or 1)):
            _a1, _a2, _a3 = st.columns(3)
            with _a1:
                st.text_input(f"Nome do {_i + 1}º signatário *", key=f"docom_ass{_i}_nome", placeholder="Nome completo")
            with _a2:
                st.text_input("Posto/graduação ou cargo efetivo *", key=f"docom_ass{_i}_posto",
                              placeholder="Ex: Capitão-Tenente (IM) ou Analista")
            with _a3:
                st.text_input("Função *", key=f"docom_ass{_i}_cargo", placeholder="Ex: Encarregado da Divisão de Obtenção")
        st.markdown("**Dados complementares (opcionais)** — preenchem automaticamente os modelos (UASG do aviso, endereço "
                    "do Ofício Externo, contato, contratante da minuta e da ata).")
        _p1, _p2 = st.columns([1, 3])
        with _p1:
            st.text_input("UASG da OM", key="docom_uasg")
        with _p2:
            st.text_input("Endereço da OM", key="docom_endereco", placeholder="Rua, nº, bairro, cidade, UF, CEP")
        st.text_input("Telefone e e-mail para contato", key="docom_contato", placeholder="(21) 0000-0000 – setor@marinha.mil.br")
        st.download_button("💾 Salvar perfil da OM (.json)", _perfil_om_json(), "perfil_om.json", "application/json",
                           key="docom_perfil_dl",
                           help="Guarde o arquivo e carregue-o nas próximas vezes para não digitar tudo de novo. "
                                "O sistema não guarda seus dados no servidor.")
    _faltam_doc = _pendencias_documento()
    if _faltam_doc:
        st.warning("⚠️ Para gerar documentos, preencha os dados obrigatórios (*) acima. Falta: " + ", ".join(_faltam_doc) + ".")

    tipo_doc = st.selectbox(
        "Documento que deseja preparar",
        [MP.DOC_DFD,
         MP.DOC_ETP,
         MP.DOC_RISCOS,
         MP.DOC_TR,
         MP.DOC_TJDL,
         MP.DOC_TJIL,
         MP.DOC_AVISO,
         MP.DOC_OF_ADESAO,
         MP.DOC_OF_IRP,
         "Justificativa de Contratação",
         "Outras justificativas",
         "Outros documentos",
         MP.DOC_MAPA,
         MP.DOC_VANTAJOSIDADE,
         MP.DOC_FRACIONAMENTO,
         "Cronograma Físico-Financeiro",
         MP.DOC_MEMORIA,
         "Ata de Registro de Preços",
         "Minuta de Contrato de Serviço / Material",
         "Classificação de Risco Jurídico"],
        key="tipo_doc_sel",
    )
    if st.session_state.pop("_doc_vindo_checklist", False):
        st.info("📋 Modelo aberto a partir da lista de verificação. Volte à aba **Checklist de Processo** para continuar "
                "a conferência.")

    # ---- RELATÓRIOS QUE VÊM DE OUTRAS TELAS (Adesões e aba Limite de Dispensa) ----
    if tipo_doc in (MP.DOC_VANTAJOSIDADE, MP.DOC_FRACIONAMENTO):
        if not st.session_state.get(f"doc_gerado_{tipo_doc}"):
            if tipo_doc == MP.DOC_VANTAJOSIDADE:
                st.info("Este relatório é montado na página **Adesões**: inclua os itens da ata na adesão, clique em "
                        "**Analisar vantajosidade** e depois em **Gerar ofício no Babilaca**.")
                st.page_link("pages/Adesões.py", label="Abrir a página Adesões", icon="🧾")
            else:
                st.info("Este relatório é montado na aba **⚖️ Limite de Dispensa** deste Babilaca.")

    # ---- MODELOS NOVOS: ETP, TJDL, TJIL, Mapa de Riscos, Aviso e ofícios (antes dos testes por trecho do nome) ----
    elif tipo_doc in (MP.DOC_ETP, MP.DOC_TJDL, MP.DOC_TJIL, MP.DOC_RISCOS, MP.DOC_AVISO, MP.DOC_OF_ADESAO, MP.DOC_OF_IRP):
        _form_modelo_processo(tipo_doc, bool(_faltam_doc))

    # ---- DFD ----
    elif "DFD" in tipo_doc:
        st.markdown("#### 📋 Gerar DFD")
        modo_dfd = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_dfd", index=1)

        if modo_dfd == "Manual":
            with st.form("form_dfd"):
                c1, c2 = st.columns(2)
                with c1:
                    _preencher("dfd_orgao", _om("om"))
                    _preencher("dfd_responsavel", _om("ass0_nome"))
                    orgao = st.text_input("Órgão/Entidade", key="dfd_orgao")
                    setor = st.text_input("Setor Requisitante")
                    responsavel = st.text_input("Responsável", key="dfd_responsavel")
                with c2:
                    data_prevista = st.date_input("Data prevista")
                    prioridade = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
                necessidade = st.text_area("Descrição da necessidade", height=100)
                justificativa = st.text_area("Justificativa", height=100)
                quantidade = st.text_input("Quantidade estimada")
                vinculacao = st.text_input("Vinculação ao PCA (se houver)")
                submit_dfd = st.form_submit_button("📄 Gerar DFD", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_dfd:
                corpo = TEMPLATE_DFD.format(
                    orgao=orgao, setor=setor, responsavel=responsavel,
                    necessidade=necessidade, justificativa=justificativa,
                    quantidade=quantidade, data_prevista=data_prevista.strftime("%d/%m/%Y"),
                    prioridade=prioridade, vinculacao_pca=vinculacao or "Não informado",
                )
                _registrar_doc(tipo_doc, "DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA (DFD)", corpo, "dfd")
        else:
            desc_ia = st.text_area(
                "Descreva brevemente a necessidade de contratação e o Babilaca preencherá o DFD:",
                height=120,
                key="dfd_ia_input",
            )
            if st.button("🤖 Gerar DFD com IA", key="btn_dfd_ia", disabled=bool(_faltam_doc)):
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
                        resultado = chamar_ia([{"role": "user", "content": prompt_dfd}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA (DFD)", resultado, "dfd_ia")
                else:
                    st.warning("Descreva a necessidade antes de gerar.")

    # ---- TERMO DE REFERÊNCIA ----
    elif "Termo de Referência" in tipo_doc:
        st.markdown("#### 📑 Gerar Termo de Referência")
        modo_tr = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_tr", index=1)

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
                submit_tr = st.form_submit_button("📄 Gerar Termo de Referência", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_tr:
                corpo = TEMPLATE_TR.format(
                    objeto=objeto, justificativa=justificativa, especificacoes=especificacoes,
                    quantidades=quantidades, valor_estimado=valor_estimado,
                    condicoes_entrega=condicoes, prazo=prazo, pagamento=pagamento,
                    criterio_julgamento=criterio,
                )
                _registrar_doc(tipo_doc, "TERMO DE REFERÊNCIA", corpo, "termo_referencia")
        else:
            desc_tr = st.text_area(
                "Descreva o que precisa contratar e o Babilaca elaborará o Termo de Referência:",
                height=120,
                key="tr_ia_input",
            )
            arquivo_tr = st.file_uploader("Ou envie um arquivo com especificações (PDF/Excel)", type=["pdf", "xlsx"], key="tr_upload")
            if st.button("🤖 Gerar TR com IA", key="btn_tr_ia", disabled=bool(_faltam_doc)):
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
                        resultado = chamar_ia([{"role": "user", "content": prompt_tr}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "TERMO DE REFERÊNCIA", resultado, "tr_ia")
                else:
                    st.warning("Forneça uma descrição ou envie um arquivo.")

    # ---- JUSTIFICATIVA ----
    elif "Justificativa" in tipo_doc:
        st.markdown("#### 📝 Gerar Justificativa de Contratação")
        modo_just = st.radio("Modo", ["Manual", "Assistido por IA"], horizontal=True, key="modo_just", index=1)

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
                submit_j = st.form_submit_button("📄 Gerar Justificativa", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_j:
                corpo = TEMPLATE_JUSTIFICATIVA.format(
                    contexto=contexto, necessidade=necessidade, analise_mercado=analise,
                    justificativa_preco=just_preco, modalidade=modalidade,
                    fundamentacao=fundamentacao, conclusao=conclusao,
                )
                _registrar_doc(tipo_doc, "JUSTIFICATIVA DE CONTRATAÇÃO", corpo, "justificativa")
        else:
            desc_just = st.text_area(
                "Descreva a contratação que precisa justificar:",
                height=120,
                key="just_ia_input",
            )
            if st.button("🤖 Gerar Justificativa com IA", key="btn_just_ia", disabled=bool(_faltam_doc)):
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
                        resultado = chamar_ia([{"role": "user", "content": prompt_just}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "JUSTIFICATIVA DE CONTRATAÇÃO", resultado, "justificativa_ia")
                else:
                    st.warning("Descreva o cenário.")

    # ---- OUTRAS JUSTIFICATIVAS E DOCUMENTOS LIVRES ----
    elif tipo_doc in ("Outras justificativas", "Outros documentos"):
        is_justificativa = tipo_doc == "Outras justificativas"
        titulo_livre = "Outras Justificativas" if is_justificativa else "Outros Documentos"
        st.markdown(f"#### ✨ {titulo_livre}")
        st.markdown(
            "Explique o que precisa elaborar e anexe os materiais disponíveis. "
            "O Babilaca organizará as informações e gerará um documento editável, com as ressalvas necessárias."
        )
        necessidade_livre = st.text_area(
            "Qual documento você precisa? Descreva a finalidade, o contexto e os pontos que devem constar.",
            height=160,
            key="documento_livre_necessidade",
            placeholder=(
                "Ex: Preciso justificar a prorrogação de um contrato de manutenção. "
                "O documento deve abordar a continuidade do serviço, a vantajosidade e o histórico de execução."
            ),
        )
        arquivos_livres = st.file_uploader(
            "Anexe documentos de apoio (opcional)",
            type=["pdf", "xlsx", "xls", "csv", "docx"],
            accept_multiple_files=True,
            key="documento_livre_upload",
            help="Os anexos são usados somente como contexto para a geração deste documento.",
        )
        if arquivos_livres:
            st.caption(f"{len(arquivos_livres)} arquivo(s) pronto(s) para análise.")

        if st.button(f"✨ Gerar {titulo_livre} com IA", key="btn_documento_livre", use_container_width=True, disabled=bool(_faltam_doc)):
            contexto_arquivos = []
            for arquivo_livre in arquivos_livres or []:
                try:
                    nome_arquivo = arquivo_livre.name
                    nome_minusculo = nome_arquivo.lower()
                    if nome_minusculo.endswith(".pdf"):
                        texto_extraido = extrair_texto_pdf(arquivo_livre)
                    elif nome_minusculo.endswith((".xlsx", ".xls")):
                        texto_extraido, _ = extrair_dados_excel(arquivo_livre)
                    elif nome_minusculo.endswith(".csv"):
                        dataframe_csv = pd.read_csv(arquivo_livre)
                        texto_extraido = dataframe_csv.head(100).to_string(index=False)
                    else:
                        documento_word = DocxDocument(arquivo_livre)
                        texto_extraido = "\n".join(paragrafo.text for paragrafo in documento_word.paragraphs)
                    if texto_extraido:
                        contexto_arquivos.append(f"[ARQUIVO: {nome_arquivo}]\n{texto_extraido[:4000]}")
                except Exception as erro:
                    st.warning(f"Não foi possível ler o arquivo {arquivo_livre.name}: {erro}")

            if necessidade_livre or contexto_arquivos:
                with st.spinner(f"Elaborando {titulo_livre.lower()} com IA..."):
                    orientacao = (
                        "Gere uma justificativa administrativa completa, objetiva e formal, adequada ao contexto descrito. "
                        "Estruture com título, contextualização, fatos e evidências, análise, fundamentação aplicável, "
                        "conclusão e encaminhamento. Não invente fatos, dados, normas ou fontes ausentes."
                        if is_justificativa
                        else "Gere o documento administrativo solicitado, em linguagem formal e com estrutura adequada à finalidade. "
                        "Defina um título coerente e organize o conteúdo em seções. Use exclusivamente as informações fornecidas; "
                        "quando faltar um dado essencial, indique-o como campo a completar, sem inventar informações."
                    )
                    prompt_livre = (
                        f"{orientacao}\n\n"
                        f"SOLICITAÇÃO DO USUÁRIO:\n{necessidade_livre or 'Não informada; utilize os anexos.'}\n\n"
                    )
                    if contexto_arquivos:
                        prompt_livre += "MATERIAIS DE APOIO:\n" + "\n\n".join(contexto_arquivos)
                    consulta = "justificativa contratação processo administrativo" if is_justificativa else "documento processo administrativo contratação pública"
                    system = _build_system_prompt(buscar_base_juridica(consulta))
                    resultado = chamar_ia([{"role": "user", "content": prompt_livre}], system + INSTRUCOES_DOCUMENTO)
                nome_base = "outra_justificativa" if is_justificativa else "outro_documento"
                _registrar_doc(tipo_doc, titulo_livre.upper(), resultado, nome_base)
            else:
                st.warning("Descreva a necessidade ou anexe ao menos um documento de apoio.")

    # ---- MAPA COMPARATIVO ----
    elif "Mapa Comparativo" in tipo_doc:
        st.markdown("#### 📊 Mapa Comparativo de Preços")
        modo_mapa = st.radio("Modo", ["Manual", "Via Arquivo"], horizontal=True, key="modo_mapa")

        if modo_mapa == "Manual":
            n_itens = st.number_input("Número de itens", min_value=1, max_value=50, value=3, key="n_itens_mapa")
            itens_mapa = []
            for i in range(int(n_itens)):
                st.markdown(f"**Item {i + 1}**")
                c1, c2, c3, c4, c5 = st.columns([3, 1, 1.5, 1.5, 1.5])
                with c1:
                    desc = st.text_input("Descrição", key=f"mapa_desc_{i}")
                with c2:
                    qtd = st.number_input("Qtd", min_value=1, value=1, key=f"mapa_qtd_{i}")
                with c3:
                    p1 = st.number_input("Fornecedor 1 (R$)", min_value=0.0, format="%.2f", key=f"mapa_p1_{i}")
                with c4:
                    p2 = st.number_input("Fornecedor 2 (R$)", min_value=0.0, format="%.2f", key=f"mapa_p2_{i}")
                with c5:
                    p3 = st.number_input("Fornecedor 3 (R$)", min_value=0.0, format="%.2f", key=f"mapa_p3_{i}")
                itens_mapa.append({"descricao": desc, "quantidade": qtd, "preco1": p1, "preco2": p2, "preco3": p3})

            obs_mapa = st.text_area(
                "Observações (aparecerá abaixo da tabela no PDF)",
                height=80,
                key="mapa_obs",
                placeholder="Ex: Preços coletados em março/2026. Frete incluso...",
            )

            if st.button("📊 Gerar Mapa Comparativo", key="btn_mapa", disabled=bool(_faltam_doc)):
                _registrar_mapa(itens_mapa, obs_mapa)

                # Mostrar tabela na tela
                rows = []
                total_geral = 0.0
                for i, item in enumerate(itens_mapa, 1):
                    precos = [item["preco1"], item["preco2"], item["preco3"]]
                    validos = [p for p in precos if p > 0]
                    media = sum(validos) / len(validos) if validos else 0
                    q = item.get("quantidade", 1) or 1
                    total_item = media * q
                    total_geral += total_item
                    rows.append({
                        "Item": i,
                        "Descrição": item["descricao"],
                        "Qtd": int(q),
                        "Forn. 1": f"R$ {item['preco1']:,.2f}",
                        "Forn. 2": f"R$ {item['preco2']:,.2f}",
                        "Forn. 3": f"R$ {item['preco3']:,.2f}",
                        "Média": f"R$ {media:,.2f}" if validos else "-",
                        "Total Est.": f"R$ {total_item:,.2f}" if total_item else "-",
                    })
                df_mapa = pd.DataFrame(rows)
                st.dataframe(df_mapa, use_container_width=True, hide_index=True)
                st.markdown(f"**Total Geral Estimado: R$ {total_geral:,.2f}**")
                if obs_mapa and obs_mapa.strip():
                    st.info(f"**Observações:** {obs_mapa}")
        else:
            arq_mapa = st.file_uploader("Envie planilha ou PDF com itens e preços", type=["xlsx", "xls", "csv", "pdf"], key="mapa_upload")
            obs_mapa_arq = st.text_area(
                "Observações (aparecerá abaixo da tabela no PDF)",
                height=80,
                key="mapa_obs_arq",
                placeholder="Ex: Preços coletados em março/2026. Frete incluso...",
            )
            if arq_mapa:
                try:
                    if arq_mapa.name.lower().endswith(".pdf"):
                        texto_pdf = extrair_texto_pdf(arq_mapa)
                        st.text_area("Conteúdo extraído do PDF", texto_pdf[:3000], height=200, disabled=True)
                        st.info("PDF carregado. Use o modo Manual para preencher os dados com base no conteúdo extraído.")
                    elif arq_mapa.name.endswith(".csv"):
                        df_m = pd.read_csv(arq_mapa)
                    else:
                        df_m = pd.read_excel(arq_mapa)

                    if not arq_mapa.name.lower().endswith(".pdf"):
                        st.dataframe(df_m, use_container_width=True)
                        st.info("Revise os dados acima. O sistema tentará identificar colunas de descrição e preços.")
                        if st.button("📊 Gerar Mapa a partir da planilha", key="btn_mapa_arq", disabled=bool(_faltam_doc)):
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
                            # Tentar encontrar coluna de quantidade
                            qtd_col = None
                            for c in df_m.columns:
                                if any(k in c.lower() for k in ["qtd", "quant", "quantidade", "qty"]):
                                    qtd_col = c
                                    break
                            for _, row in df_m.iterrows():
                                item = {"descricao": str(row[desc_col])}
                                if qtd_col:
                                    try:
                                        item["quantidade"] = int(float(row[qtd_col]))
                                    except (ValueError, TypeError):
                                        item["quantidade"] = 1
                                else:
                                    item["quantidade"] = 1
                                for j, pc in enumerate(preco_cols[:3], 1):
                                    try:
                                        item[f"preco{j}"] = float(row[pc])
                                    except (ValueError, TypeError):
                                        item[f"preco{j}"] = 0
                                for j in range(len(preco_cols) + 1, 4):
                                    item[f"preco{j}"] = 0
                                itens_arq.append(item)
                            if itens_arq:
                                _registrar_mapa(itens_arq, obs_mapa_arq)
                except Exception as e:
                    st.error(f"Erro ao processar arquivo: {e}")

        if st.session_state.get("mapa_xlsx") and st.session_state.get(f"doc_gerado_{MP.DOC_MAPA}"):
            st.download_button("📊 Baixar o mapa em Excel", st.session_state["mapa_xlsx"],
                               "mapa_comparativo.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="dl_mapa_xlsx")

    # ---- CRONOGRAMA FÍSICO-FINANCEIRO ----
    elif "Cronograma" in tipo_doc:
        st.markdown("#### 📅 Cronograma Físico-Financeiro")
        st.markdown(
            "Gere um cronograma detalhado de execução e desembolso financeiro para obras, "
            "serviços de engenharia ou contratos de grande porte, conforme **Art. 25, §1° e "
            "Art. 46, Lei 14.133/2021**."
        )
        modo_crono = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_crono", index=1)

        if modo_crono == "Manual":
            with st.form("form_cronograma"):
                st.markdown("**Dados Gerais**")
                c1, c2 = st.columns(2)
                with c1:
                    crono_objeto = st.text_area("Objeto da contratação", height=60, key="crono_obj")
                    crono_contrato = st.text_input("Nº do Contrato / Processo", key="crono_contrato")
                    crono_contratada = st.text_input("Empresa contratada", key="crono_contratada")
                with c2:
                    crono_valor_global = st.number_input("Valor Global do Contrato (R$)", min_value=0.0, format="%.2f", key="crono_valor")
                    crono_inicio = st.date_input("Data de início prevista", key="crono_inicio")
                    crono_prazo_meses = st.number_input("Prazo total (meses)", min_value=1, max_value=120, value=12, key="crono_prazo")

                st.markdown("---")
                st.markdown("**Etapas / Fases de Execução**")
                n_etapas = st.number_input("Número de etapas", min_value=1, max_value=30, value=4, key="crono_n_etapas")
                etapas = []
                for i in range(int(n_etapas)):
                    st.markdown(f"**Etapa {i + 1}**")
                    ec1, ec2, ec3, ec4 = st.columns([3, 1.5, 1.5, 1.5])
                    with ec1:
                        et_desc = st.text_input("Descrição da etapa", key=f"crono_et_desc_{i}")
                    with ec2:
                        et_inicio_mes = st.number_input("Mês início", min_value=1, max_value=120, value=i + 1, key=f"crono_et_ini_{i}")
                    with ec3:
                        et_fim_mes = st.number_input("Mês fim", min_value=1, max_value=120, value=i + 3, key=f"crono_et_fim_{i}")
                    with ec4:
                        et_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key=f"crono_et_val_{i}")
                    etapas.append({"descricao": et_desc, "mes_inicio": et_inicio_mes, "mes_fim": et_fim_mes, "valor": et_valor})

                crono_obs = st.text_area("Observações", height=60, key="crono_obs_manual")
                submit_crono = st.form_submit_button("📅 Gerar Cronograma", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_crono:
                # Montar documento
                corpo_crono = f"""## CRONOGRAMA FÍSICO-FINANCEIRO

### 1. Dados Gerais
- **Objeto:** {crono_objeto}
- **Nº Contrato/Processo:** {crono_contrato}
- **Empresa Contratada:** {crono_contratada}
- **Valor Global:** {_fmt_brl(crono_valor_global)}
- **Data de Início:** {crono_inicio.strftime('%d/%m/%Y')}
- **Prazo de Execução:** {crono_prazo_meses} meses

### 2. Detalhamento das Etapas

| # | Etapa | Mês Início | Mês Fim | Duração | Valor (R$) | % do Total |
|---|-------|-----------|---------|---------|-----------|-----------|
"""
                soma_etapas = sum(e["valor"] for e in etapas)
                for j, e in enumerate(etapas, 1):
                    dur = max(1, e["mes_fim"] - e["mes_inicio"] + 1)
                    pct = (e["valor"] / crono_valor_global * 100) if crono_valor_global > 0 else 0
                    corpo_crono += f"| {j} | {e['descricao']} | {e['mes_inicio']}° | {e['mes_fim']}° | {dur} meses | {_fmt_brl(e['valor'])} | {pct:.1f}% |\n"

                corpo_crono += f"\n**Total das Etapas:** {_fmt_brl(soma_etapas)}"
                if crono_valor_global > 0:
                    corpo_crono += f" ({soma_etapas / crono_valor_global * 100:.1f}% do valor global)"

                # Cronograma de desembolso mensal
                corpo_crono += "\n\n### 3. Cronograma de Desembolso Mensal\n\n"
                corpo_crono += "| Mês | Etapas Ativas | Desembolso Estimado (R$) | Acumulado (R$) |\n"
                corpo_crono += "|-----|--------------|------------------------|----------------|\n"
                acumulado = 0.0
                for mes in range(1, int(crono_prazo_meses) + 1):
                    desembolso_mes = 0.0
                    ativos = []
                    for e in etapas:
                        if e["mes_inicio"] <= mes <= e["mes_fim"]:
                            dur = max(1, e["mes_fim"] - e["mes_inicio"] + 1)
                            desembolso_mes += e["valor"] / dur
                            ativos.append(e["descricao"][:30])
                    acumulado += desembolso_mes
                    nomes = ", ".join(ativos) if ativos else "—"
                    corpo_crono += f"| {mes}° | {nomes} | {_fmt_brl(desembolso_mes)} | {_fmt_brl(acumulado)} |\n"

                corpo_crono += f"""
### 4. Base Legal
- Lei 14.133/2021, Art. 25, §1° e Art. 46
- IN SEGES/ME nº 58/2022

### 5. Observações
{crono_obs or 'Sem observações.'}

"""
                _registrar_doc(tipo_doc, "CRONOGRAMA FÍSICO-FINANCEIRO", corpo_crono, "cronograma_fisico_financeiro")

        else:  # Assistido por IA
            st.markdown(
                "Descreva o projeto/contrato abaixo e a IA gerará um cronograma físico-financeiro "
                "completo com etapas, prazos, valores e curva de desembolso."
            )
            desc_crono = st.text_area(
                "Descreva o objeto, valor estimado, prazo e principais etapas:",
                height=150,
                key="crono_ia_input",
                placeholder=(
                    "Ex: Obra de reforma do prédio administrativo, valor estimado R$ 800.000,00, "
                    "prazo de 12 meses. Inclui demolição, estrutura, instalações elétricas e hidráulicas, "
                    "acabamento e limpeza final."
                ),
            )
            arquivo_crono = st.file_uploader("Ou envie projeto básico/planilha orçamentária (PDF/Excel)", type=["pdf", "xlsx"], key="crono_upload")
            if st.button("🤖 Gerar Cronograma com IA", key="btn_crono_ia", disabled=bool(_faltam_doc)):
                ctx_extra = ""
                if arquivo_crono:
                    if arquivo_crono.name.endswith(".pdf"):
                        ctx_extra = extrair_texto_pdf(arquivo_crono)
                    else:
                        ctx_extra, _ = extrair_dados_excel(arquivo_crono)
                if desc_crono or ctx_extra:
                    with st.spinner("Gerando Cronograma Físico-Financeiro com IA..."):
                        prompt_crono = (
                            "Gere um **Cronograma Físico-Financeiro** completo e detalhado para o seguinte projeto/contrato, "
                            "conforme exigido pela Lei 14.133/2021 (Art. 25, §1° e Art. 46).\n\n"
                            f"**Descrição do projeto:**\n{desc_crono}\n\n"
                        )
                        if ctx_extra:
                            prompt_crono += f"**Dados do arquivo anexado:**\n{ctx_extra[:4000]}\n\n"
                        prompt_crono += (
                            "O documento deve conter OBRIGATORIAMENTE:\n\n"
                            "1. **DADOS GERAIS**: objeto, valor global estimado, prazo total, empresa (quando informada)\n\n"
                            "2. **DETALHAMENTO DAS ETAPAS** em tabela com: Nº, Descrição da Etapa/Fase, "
                            "Mês de Início, Mês de Término, Duração, Valor da Etapa (R$), Percentual do Total (%)\n\n"
                            "3. **CRONOGRAMA DE DESEMBOLSO MENSAL** em tabela com: Mês, Etapas Ativas, "
                            "Desembolso no Mês (R$), Acumulado (R$), Percentual Acumulado (%)\n\n"
                            "4. **CURVA S** descritiva: explique a evolução dos desembolsos ao longo do tempo "
                            "(se há concentração no início, meio ou fim)\n\n"
                            "5. **MARCOS CRÍTICOS**: liste os marcos de medição/pagamento mais importantes\n\n"
                            "6. **CONDIÇÕES DE PAGAMENTO**: vincule os pagamentos à medição das etapas efetivamente executadas\n\n"
                            "7. **BASE LEGAL**: Art. 25 §1° e Art. 46 da Lei 14.133/2021\n\n"
                            "8. **RESSALVAS**: indique que os valores e prazos são estimativos e sujeitos a ajustes\n\n"
                            "Use valores realistas e proporcionais. Formate tabelas em Markdown. "
                            "Todos os valores devem estar em Reais (R$)."
                        )
                        ctx = buscar_base_juridica("cronograma execução pagamento medição prazo contrato obra")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_crono}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "CRONOGRAMA FÍSICO-FINANCEIRO", resultado, "cronograma_ia")
                else:
                    st.warning("Descreva o projeto ou envie um arquivo.")

    # ---- MEMÓRIA DE CÁLCULO ----
    elif "Memória de Cálculo" in tipo_doc:
        st.markdown("#### 🧮 Memória de Cálculo")
        st.markdown(
            "Gere uma memória de cálculo detalhada para fundamentar o **valor estimado** da contratação, "
            "conforme **Art. 23 da Lei 14.133/2021** e **IN SEGES/ME nº 65/2021**. "
            "Documento essencial para demonstrar como se chegou ao preço de referência."
        )
        modo_mc = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_mc", index=1)

        if modo_mc == "Manual":
            with st.form("form_memoria_calculo"):
                st.markdown("**Dados Gerais**")
                mc_c1, mc_c2 = st.columns(2)
                with mc_c1:
                    mc_objeto = st.text_area("Objeto da contratação", height=60, key="mc_obj")
                    mc_processo = st.text_input("Nº do Processo", key="mc_processo")
                with mc_c2:
                    mc_metodologia = st.selectbox("Metodologia de pesquisa (IN 65/2021)", [
                        "Painel de Preços / ComprasGov",
                        "Contratações similares de outros entes (PNCP)",
                        "Pesquisa direta com fornecedores (mín. 3 cotações)",
                        "Pesquisa em sites especializados / catálogos",
                        "Combinação de fontes (recomendado)",
                    ], key="mc_metodo")
                    mc_criterio = st.selectbox("Critério de formação do preço de referência", [
                        "Média aritmética dos preços válidos",
                        "Mediana dos preços válidos",
                        "Menor preço obtido",
                        "Média saneada (excluídos outliers)",
                    ], key="mc_criterio")

                st.markdown("---")
                st.markdown("**Itens e Cotações**")
                mc_n_itens = st.number_input("Número de itens", min_value=1, max_value=50, value=3, key="mc_n_itens")
                itens_mc = []
                for i in range(int(mc_n_itens)):
                    st.markdown(f"**Item {i + 1}**")
                    ic1, ic2, ic3 = st.columns([3, 1, 1])
                    with ic1:
                        mc_desc = st.text_input("Descrição do item", key=f"mc_desc_{i}")
                    with ic2:
                        mc_und = st.text_input("Unidade", value="UN", key=f"mc_und_{i}")
                    with ic3:
                        mc_qtd = st.number_input("Qtd", min_value=1, value=1, key=f"mc_qtd_{i}")

                    st.markdown("Cotações obtidas:")
                    fc1, fc2, fc3, fc4, fc5 = st.columns(5)
                    with fc1:
                        mc_f1 = st.number_input("Fonte 1 (R$)", min_value=0.0, format="%.2f", key=f"mc_f1_{i}")
                        mc_f1_nome = st.text_input("Nome Fonte 1", key=f"mc_f1n_{i}", placeholder="Ex: Ata PE 10/2025")
                    with fc2:
                        mc_f2 = st.number_input("Fonte 2 (R$)", min_value=0.0, format="%.2f", key=f"mc_f2_{i}")
                        mc_f2_nome = st.text_input("Nome Fonte 2", key=f"mc_f2n_{i}", placeholder="Ex: Cotação Empresa X")
                    with fc3:
                        mc_f3 = st.number_input("Fonte 3 (R$)", min_value=0.0, format="%.2f", key=f"mc_f3_{i}")
                        mc_f3_nome = st.text_input("Nome Fonte 3", key=f"mc_f3n_{i}", placeholder="Ex: Painel de Preços")
                    with fc4:
                        mc_f4 = st.number_input("Fonte 4 (R$)", min_value=0.0, format="%.2f", key=f"mc_f4_{i}")
                        mc_f4_nome = st.text_input("Nome Fonte 4", key=f"mc_f4n_{i}", placeholder="(Opcional)")
                    with fc5:
                        mc_f5 = st.number_input("Fonte 5 (R$)", min_value=0.0, format="%.2f", key=f"mc_f5_{i}")
                        mc_f5_nome = st.text_input("Nome Fonte 5", key=f"mc_f5n_{i}", placeholder="(Opcional)")

                    itens_mc.append({
                        "descricao": mc_desc, "unidade": mc_und, "quantidade": mc_qtd,
                        "fontes": [
                            {"nome": mc_f1_nome, "valor": mc_f1},
                            {"nome": mc_f2_nome, "valor": mc_f2},
                            {"nome": mc_f3_nome, "valor": mc_f3},
                            {"nome": mc_f4_nome, "valor": mc_f4},
                            {"nome": mc_f5_nome, "valor": mc_f5},
                        ],
                    })

                mc_obs = st.text_area("Observações e justificativas adicionais", height=80, key="mc_obs")
                submit_mc = st.form_submit_button("🧮 Gerar Memória de Cálculo", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_mc:
                import statistics
                corpo_mc = f"""## MEMÓRIA DE CÁLCULO — ESTIMATIVA DE PREÇOS

### 1. Dados Gerais
- **Objeto:** {mc_objeto}
- **Nº Processo:** {mc_processo}
- **Metodologia:** {mc_metodologia}
- **Critério de formação do preço:** {mc_criterio}

### 2. Fontes de Pesquisa Utilizadas
Conforme Art. 23, §1° da Lei 14.133/2021 e IN SEGES/ME nº 65/2021, a pesquisa de preços
utilizou as seguintes fontes, priorizando a ordem estabelecida no Art. 5° da IN 65/2021:

"""
                # Coletar todas as fontes únicas dos itens
                fontes_unicas = set()
                for item in itens_mc:
                    for f in item["fontes"]:
                        if f["nome"] and f["valor"] > 0:
                            fontes_unicas.add(f["nome"])
                for idx_f, fn in enumerate(sorted(fontes_unicas), 1):
                    corpo_mc += f"- **Fonte {idx_f}:** {fn}\n"

                corpo_mc += "\n### 3. Detalhamento por Item\n\n"

                valor_total_global = 0.0
                for j, item in enumerate(itens_mc, 1):
                    fontes_validas = [f for f in item["fontes"] if f["valor"] > 0]
                    precos = [f["valor"] for f in fontes_validas]

                    corpo_mc += f"---\n#### Item {j}: {item['descricao']}\n"
                    corpo_mc += f"- **Unidade:** {item['unidade']} | **Quantidade:** {item['quantidade']}\n\n"

                    # Tabela de cotações
                    corpo_mc += "| Fonte | Valor Unitário (R$) |\n"
                    corpo_mc += "|-------|--------------------|\n"
                    for f in fontes_validas:
                        corpo_mc += f"| {f['nome']} | {_fmt_brl(f['valor'])} |\n"

                    if precos:
                        media = sum(precos) / len(precos)
                        mediana = statistics.median(precos)
                        menor = min(precos)
                        maior = max(precos)
                        coef_var = (statistics.stdev(precos) / media * 100) if len(precos) > 1 else 0

                        # Determinar preço de referência conforme critério
                        if "Mediana" in mc_criterio:
                            preco_ref = mediana
                        elif "Menor" in mc_criterio:
                            preco_ref = menor
                        elif "saneada" in mc_criterio.lower():
                            # Excluir valores fora de 1 desvio padrão
                            if len(precos) > 2:
                                dp = statistics.stdev(precos)
                                saneados = [p for p in precos if abs(p - media) <= dp]
                                preco_ref = sum(saneados) / len(saneados) if saneados else media
                            else:
                                preco_ref = media
                        else:
                            preco_ref = media

                        total_item = preco_ref * item["quantidade"]
                        valor_total_global += total_item

                        corpo_mc += f"\n**Análise Estatística:**\n"
                        corpo_mc += f"- Menor preço: {_fmt_brl(menor)}\n"
                        corpo_mc += f"- Maior preço: {_fmt_brl(maior)}\n"
                        corpo_mc += f"- Média aritmética: {_fmt_brl(media)}\n"
                        corpo_mc += f"- Mediana: {_fmt_brl(mediana)}\n"
                        if len(precos) > 1:
                            corpo_mc += f"- Coeficiente de variação: {coef_var:.1f}%"
                            if coef_var > 25:
                                corpo_mc += " ⚠️ *Dispersão alta — recomenda-se justificativa*"
                            corpo_mc += "\n"
                        corpo_mc += f"\n**▶ Preço de Referência Unitário ({mc_criterio}):** {_fmt_brl(preco_ref)}\n"
                        corpo_mc += f"**▶ Valor Total do Item ({item['quantidade']} x {_fmt_brl(preco_ref)}):** {_fmt_brl(total_item)}\n\n"
                    else:
                        corpo_mc += "\n⚠️ *Nenhuma cotação informada para este item.*\n\n"

                corpo_mc += f"""---
### 4. Resumo — Valor Total Estimado

| Critério | Valor |
|----------|-------|
| **Valor Total Estimado Global** | **{_fmt_brl(valor_total_global)}** |
| Metodologia aplicada | {mc_metodologia} |
| Critério de formação | {mc_criterio} |
| Nº de fontes utilizadas | {len(fontes_unicas)} |

### 5. Conformidade Legal
- **Art. 23, Lei 14.133/2021** — Valor estimado compatível com mercado
- **IN SEGES/ME nº 65/2021, Arts. 5° a 7°** — Parâmetros e ordem de fontes
- **Acórdão 1.793/2011 — TCU Plenário** — Pesquisa ampla e diversificada

### 6. Observações
{mc_obs or 'Sem observações adicionais.'}

"""
                _registrar_doc(tipo_doc, "MEMÓRIA DE CÁLCULO", corpo_mc, "memoria_calculo")

        else:  # Assistido por IA
            st.markdown(
                "Descreva os itens a contratar, fontes de pesquisa e valores obtidos. "
                "A IA gerará uma memória de cálculo completa com análise estatística, "
                "justificativa e fundamentação legal."
            )
            desc_mc = st.text_area(
                "Descreva os itens, quantidades, valores pesquisados e fontes utilizadas:",
                height=180,
                key="mc_ia_input",
                placeholder=(
                    "Ex: Preciso de memória de cálculo para aquisição de 50 notebooks Dell Latitude 5540.\n"
                    "Fontes pesquisadas:\n"
                    "- Ata PE 15/2025 UASG 160XXX: R$ 5.200,00/un\n"
                    "- Painel de Preços (ComprasGov): R$ 5.450,00/un\n"
                    "- Cotação Fornecedor ABC: R$ 5.100,00/un\n"
                    "- Site Magazine Luiza: R$ 5.800,00/un"
                ),
            )
            arquivo_mc = st.file_uploader("Ou envie planilha de cotações / pesquisa de preços (PDF/Excel)", type=["pdf", "xlsx"], key="mc_upload")
            if st.button("🤖 Gerar Memória de Cálculo com IA", key="btn_mc_ia", disabled=bool(_faltam_doc)):
                ctx_extra = ""
                if arquivo_mc:
                    if arquivo_mc.name.endswith(".pdf"):
                        ctx_extra = extrair_texto_pdf(arquivo_mc)
                    else:
                        ctx_extra, _ = extrair_dados_excel(arquivo_mc)
                if desc_mc or ctx_extra:
                    with st.spinner("Gerando Memória de Cálculo com IA..."):
                        prompt_mc = (
                            "Gere uma **Memória de Cálculo** completa e detalhada para fundamentar o valor estimado "
                            "da contratação abaixo, conforme Art. 23 da Lei 14.133/2021 e IN SEGES/ME nº 65/2021.\n\n"
                            f"**Descrição / Dados fornecidos:**\n{desc_mc}\n\n"
                        )
                        if ctx_extra:
                            prompt_mc += f"**Dados do arquivo anexado:**\n{ctx_extra[:4000]}\n\n"
                        prompt_mc += (
                            "O documento deve conter OBRIGATORIAMENTE:\n\n"
                            "1. **DADOS GERAIS**: objeto, processo (se informado), metodologia de pesquisa\n\n"
                            "2. **FONTES DE PESQUISA**: listar todas as fontes utilizadas, seguindo a ordem "
                            "de prioridade da IN 65/2021 Art. 5°: I-Painel de Preços, II-Contratações similares, "
                            "III-Sites especializados, IV-Pesquisa direta com fornecedores\n\n"
                            "3. **DETALHAMENTO POR ITEM** com tabela de cotações contendo: Fonte, CNPJ/Identificação "
                            "(quando disponível), Valor Unitário, Data da Cotação\n\n"
                            "4. **ANÁLISE ESTATÍSTICA POR ITEM**: média aritmética, mediana, menor preço, maior preço, "
                            "desvio padrão, coeficiente de variação. Se CV > 25%, alertar sobre dispersão alta\n\n"
                            "5. **TRATAMENTO DE OUTLIERS**: se houver preços com dispersão excessiva (>25%), "
                            "aplicar média saneada excluindo valores fora de 1 desvio padrão, justificando a exclusão\n\n"
                            "6. **PREÇO DE REFERÊNCIA**: indicar o critério adotado (média, mediana ou menor), "
                            "calcular o valor unitário e o valor total por item e global\n\n"
                            "7. **QUADRO RESUMO** com tabela: Item, Qtd, Unidade, Preço Ref. Unitário, Valor Total\n\n"
                            "8. **CONFORMIDADE LEGAL**: citar Art. 23 Lei 14.133, IN 65/2021, e jurisprudência "
                            "relevante (Acórdão 1.793/2011-TCU caso esteja no contexto)\n\n"
                            "9. **CONCLUSÃO**: valor total estimado e declaração de compatibilidade com mercado\n\n"
                            "Use tabelas Markdown, valores em Reais (R$) formatados, e cálculos demonstrados passo a passo."
                        )
                        ctx = buscar_base_juridica("pesquisa preços estimativa orçamento cotação memória cálculo IN 65")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_mc}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "MEMÓRIA DE CÁLCULO", resultado, "memoria_calculo_ia")
                else:
                    st.warning("Descreva os itens/valores ou envie um arquivo.")

    # ---- ATA DE REGISTRO DE PREÇOS ----
    elif "Ata de Registro" in tipo_doc:
        st.markdown("#### 📜 Modelo de Ata de Registro de Preços")
        st.markdown(
            "Gere um modelo completo de Ata de Registro de Preços conforme a **Lei 14.133/2021 (Arts. 82 a 86)** "
            "e o **Decreto nº 11.462/2023**. Inclui cláusulas de revisão, cancelamento, adesão (carona), "
            "obrigações e penalidades."
        )
        modo_ata = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_ata", index=1)

        if modo_ata == "Manual":
            with st.form("form_ata_rp"):
                st.markdown("**Dados do Órgão Gerenciador**")
                ca1, ca2 = st.columns(2)
                with ca1:
                    _preencher("ata_orgao", _om("om"))
                    _preencher("ata_end_orgao", _om("endereco"))
                    ata_orgao = st.text_input("Órgão Gerenciador", key="ata_orgao")
                    ata_cnpj_orgao = st.text_input("CNPJ do Órgão", key="ata_cnpj_orgao")
                    ata_endereco_orgao = st.text_input("Endereço do Órgão", key="ata_end_orgao")
                with ca2:
                    ata_representante = st.text_input("Representante Legal", key="ata_repr")
                    ata_cargo = st.text_input("Cargo do Representante", key="ata_cargo")
                    ata_processo = st.text_input("Nº Processo Administrativo", key="ata_processo")

                st.markdown("---")
                st.markdown("**Dados da Licitação**")
                cb1, cb2 = st.columns(2)
                with cb1:
                    ata_pregao = st.text_input("Nº do Pregão Eletrônico", key="ata_pregao")
                    ata_objeto = st.text_area("Objeto", height=60, key="ata_objeto")
                with cb2:
                    ata_vigencia = st.text_input("Vigência da Ata", value="12 (doze) meses", key="ata_vigencia")
                    ata_data_assinatura = st.date_input("Data de Assinatura", key="ata_data_ass")

                st.markdown("---")
                st.markdown("**Dados do Fornecedor**")
                cc1, cc2 = st.columns(2)
                with cc1:
                    ata_fornecedor = st.text_input("Razão Social do Fornecedor", key="ata_forn")
                    ata_cnpj_forn = st.text_input("CNPJ do Fornecedor", key="ata_cnpj_forn")
                    ata_end_forn = st.text_input("Endereço do Fornecedor", key="ata_end_forn")
                with cc2:
                    ata_repr_forn = st.text_input("Representante do Fornecedor", key="ata_repr_forn")
                    ata_contato_forn = st.text_input("Telefone/E-mail do Fornecedor", key="ata_contato_forn")

                st.markdown("---")
                st.markdown("**Itens Registrados**")
                n_itens_ata = st.number_input("Número de itens", min_value=1, max_value=50, value=3, key="n_itens_ata")
                itens_ata = []
                for i in range(int(n_itens_ata)):
                    st.markdown(f"**Item {i + 1}**")
                    ia1, ia2, ia3, ia4 = st.columns([4, 1, 1, 1.5])
                    with ia1:
                        ata_desc = st.text_input("Descrição", key=f"ata_desc_{i}")
                    with ia2:
                        ata_und = st.text_input("Unidade", value="UN", key=f"ata_und_{i}")
                    with ia3:
                        ata_qtd = st.number_input("Qtd", min_value=1, value=1, key=f"ata_qtd_{i}")
                    with ia4:
                        ata_val = st.number_input("Valor Unit. (R$)", min_value=0.0, format="%.2f", key=f"ata_val_{i}")
                    itens_ata.append({"descricao": ata_desc, "unidade": ata_und, "quantidade": ata_qtd, "valor": ata_val})

                st.markdown("---")
                st.markdown("**Condições**")
                cd1, cd2 = st.columns(2)
                with cd1:
                    ata_prazo_entrega = st.text_input("Prazo de entrega", value="30 (trinta) dias", key="ata_prazo_ent")
                    ata_local_entrega = st.text_input("Local de entrega", key="ata_local_ent")
                with cd2:
                    ata_prazo_pgto = st.text_input("Prazo de pagamento", value="30 (trinta) dias", key="ata_prazo_pgto")
                ata_obs = st.text_area("Observações / Disposições Gerais", height=80, key="ata_obs")
                submit_ata = st.form_submit_button("📜 Gerar Ata de Registro de Preços", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_ata:
                tabela_itens_str = ""
                valor_total_ata = 0.0
                for j, it in enumerate(itens_ata, 1):
                    vt = it["valor"] * it["quantidade"]
                    valor_total_ata += vt
                    tabela_itens_str += f"| {j} | {it['descricao']} | {it['unidade']} | {it['quantidade']} | {_fmt_brl(it['valor'])} | {_fmt_brl(vt)} |\n"

                corpo_ata = TEMPLATE_ATA_RP.format(
                    processo=ata_processo, pregao=ata_pregao, orgao=ata_orgao,
                    cnpj_orgao=ata_cnpj_orgao, vigencia=ata_vigencia,
                    data_assinatura=ata_data_assinatura.strftime("%d/%m/%Y"),
                    endereco_orgao=ata_endereco_orgao, cargo_representante=ata_cargo,
                    representante=ata_representante, objeto=ata_objeto,
                    fornecedor=ata_fornecedor, cnpj_fornecedor=ata_cnpj_forn,
                    endereco_fornecedor=ata_end_forn, representante_fornecedor=ata_repr_forn,
                    contato_fornecedor=ata_contato_forn, tabela_itens=tabela_itens_str,
                    valor_total=_fmt_brl(valor_total_ata), prazo_entrega=ata_prazo_entrega,
                    local_entrega=ata_local_entrega, prazo_pagamento=ata_prazo_pgto,
                    observacoes=ata_obs or "Sem observações adicionais.",
                )
                _registrar_doc(tipo_doc, "ATA DE REGISTRO DE PREÇOS", corpo_ata, "ata_registro_precos")
        else:
            desc_ata = st.text_area(
                "Descreva os dados da licitação, órgão, fornecedor, itens e condições. O Babilaca gerará a Ata completa:",
                height=180,
                key="ata_ia_input",
                placeholder=(
                    "Ex: Pregão Eletrônico nº 10/2026, UASG 787000 (Centro de Obtenção da Marinha).\n"
                    "Fornecedor vencedor: Empresa ABC Ltda, CNPJ 12.345.678/0001-90.\n"
                    "Itens: 100 un resma de papel A4 a R$ 25,00/un; 50 un toner HP a R$ 180,00/un.\n"
                    "Vigência: 12 meses. Entrega em 30 dias no almoxarifado central."
                ),
            )
            arquivo_ata = st.file_uploader("Ou envie edital/resultado de licitação (PDF/Excel)", type=["pdf", "xlsx"], key="ata_upload")
            if st.button("🤖 Gerar Ata com IA", key="btn_ata_ia", disabled=bool(_faltam_doc)):
                ctx_extra = ""
                if arquivo_ata:
                    if arquivo_ata.name.endswith(".pdf"):
                        ctx_extra = extrair_texto_pdf(arquivo_ata)
                    else:
                        ctx_extra, _ = extrair_dados_excel(arquivo_ata)
                if desc_ata or ctx_extra:
                    with st.spinner("Gerando Ata de Registro de Preços com IA..."):
                        prompt_ata = (
                            "Gere um **Modelo de Ata de Registro de Preços** completo e detalhado, "
                            "conforme a Lei 14.133/2021 (Arts. 82 a 86) e o Decreto 11.462/2023.\n\n"
                            f"**Dados fornecidos:**\n{desc_ata}\n\n"
                        )
                        if ctx_extra:
                            prompt_ata += f"**Dados do arquivo anexado:**\n{ctx_extra[:4000]}\n\n"
                        prompt_ata += (
                            "O documento deve conter OBRIGATORIAMENTE:\n\n"
                            "1. **PREÂMBULO** com identificação do Órgão Gerenciador, licitação e fornecedor\n"
                            "2. **OBJETO** detalhado\n"
                            "3. **TABELA DE ITENS** com descrição, unidade, quantidade, valor unitário e total\n"
                            "4. **VALIDADE DA ATA** — prazo e condições de prorrogação (Art. 84)\n"
                            "5. **REVISÃO E CANCELAMENTO** de preços (Art. 82, §5°)\n"
                            "6. **CONDIÇÕES DE ENTREGA** — prazo, local, recebimento provisório/definitivo\n"
                            "7. **PAGAMENTO** — prazo, documentação, retenções\n"
                            "8. **OBRIGAÇÕES DO FORNECEDOR** — habilitação, encargos, substituição\n"
                            "9. **OBRIGAÇÕES DO ÓRGÃO** — gerenciamento, renegociação, sanções\n"
                            "10. **ADESÃO (CARONA)** — limites de 50% por órgão e dobro total (Art. 86)\n"
                            "11. **PENALIDADES** — Arts. 155 a 163\n"
                            "12. **FUNDAMENTAÇÃO LEGAL** — Lei 14.133/2021, Decreto 11.462/2023\n\n"
                            "Use tabelas Markdown, valores em Reais (R$) e linguagem jurídica formal."
                        )
                        ctx = buscar_base_juridica("ata registro preços pregão licitação fornecedor")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_ata}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "ATA DE REGISTRO DE PREÇOS", resultado, "ata_rp_ia")
                else:
                    st.warning("Descreva os dados da licitação ou envie um arquivo.")

    # ---- MINUTA DE CONTRATO ----
    elif "Minuta de Contrato" in tipo_doc:
        st.markdown("#### 📑 Minuta de Contrato de Serviço / Material")
        st.markdown(
            "Gere uma minuta de contrato completa com todas as cláusulas essenciais, incluindo "
            "**garantia contratual**, **garantia dos produtos/serviços**, penalidades, fiscalização "
            "e recebimento, conforme a **Lei 14.133/2021**."
        )
        modo_contrato = st.radio("Modo de preenchimento", ["Manual", "Assistido por IA"], horizontal=True, key="modo_contrato", index=1)

        if modo_contrato == "Manual":
            with st.form("form_minuta_contrato"):
                st.markdown("**Dados do Contratante**")
                mc1, mc2 = st.columns(2)
                with mc1:
                    _preencher("ct_orgao", _om("om"))
                    _preencher("ct_end_orgao", _om("endereco"))
                    ct_orgao = st.text_input("Órgão/Entidade", key="ct_orgao")
                    ct_cnpj_orgao = st.text_input("CNPJ do Órgão", key="ct_cnpj_orgao")
                    ct_endereco_orgao = st.text_input("Endereço do Órgão", key="ct_end_orgao")
                with mc2:
                    ct_representante = st.text_input("Representante Legal", key="ct_repr")
                    ct_cargo = st.text_input("Cargo", key="ct_cargo")
                    ct_processo = st.text_input("Nº Processo Administrativo", key="ct_processo")

                st.markdown("---")
                st.markdown("**Dados da Licitação e Contrato**")
                md1, md2 = st.columns(2)
                with md1:
                    ct_licitacao = st.text_input("Nº da Licitação", key="ct_licitacao")
                    ct_modalidade = st.selectbox("Modalidade", [
                        "Pregão Eletrônico", "Concorrência", "Dispensa de Licitação",
                        "Inexigibilidade", "Adesão a Ata de Registro de Preços"
                    ], key="ct_modalidade")
                    ct_tipo = st.selectbox("Tipo de Contrato", [
                        "FORNECIMENTO DE MATERIAL", "PRESTAÇÃO DE SERVIÇO",
                        "FORNECIMENTO DE MATERIAL E PRESTAÇÃO DE SERVIÇO"
                    ], key="ct_tipo")
                with md2:
                    ct_ano = st.text_input("Ano", value=str(datetime.now().year), key="ct_ano")
                    ct_vigencia = st.text_input("Vigência", value="12 (doze) meses", key="ct_vigencia")
                    ct_objeto = st.text_area("Objeto da Contratação", height=60, key="ct_objeto")

                st.markdown("---")
                st.markdown("**Dados da Contratada**")
                me1, me2 = st.columns(2)
                with me1:
                    ct_empresa = st.text_input("Razão Social da Empresa", key="ct_empresa")
                    ct_cnpj_empresa = st.text_input("CNPJ da Empresa", key="ct_cnpj_emp")
                    ct_end_empresa = st.text_input("Endereço da Empresa", key="ct_end_emp")
                with me2:
                    ct_repr_empresa = st.text_input("Representante da Empresa", key="ct_repr_emp")

                st.markdown("---")
                st.markdown("**Itens / Serviços**")
                n_itens_ct = st.number_input("Número de itens", min_value=1, max_value=50, value=3, key="n_itens_ct")
                itens_ct = []
                for i in range(int(n_itens_ct)):
                    st.markdown(f"**Item {i + 1}**")
                    ic1, ic2, ic3, ic4 = st.columns([4, 1, 1, 1.5])
                    with ic1:
                        ct_desc = st.text_input("Descrição", key=f"ct_desc_{i}")
                    with ic2:
                        ct_und = st.text_input("Unidade", value="UN", key=f"ct_und_{i}")
                    with ic3:
                        ct_qtd = st.number_input("Qtd", min_value=1, value=1, key=f"ct_qtd_{i}")
                    with ic4:
                        ct_val = st.number_input("Valor Unit. (R$)", min_value=0.0, format="%.2f", key=f"ct_val_{i}")
                    itens_ct.append({"descricao": ct_desc, "unidade": ct_und, "quantidade": ct_qtd, "valor": ct_val})

                st.markdown("---")
                st.markdown("**Garantia e Condições**")
                gf1, gf2 = st.columns(2)
                with gf1:
                    ct_garantia_contratual = st.selectbox("Garantia contratual (% do valor)", [
                        "5%", "10%", "Até 30% (obras de grande vulto)"
                    ], key="ct_gar_contratual")
                    ct_garantia_produto = st.text_input("Garantia dos produtos/serviços", value="12 (doze) meses", key="ct_gar_prod")
                    ct_prazo_reparo = st.text_input("Prazo para reparo/substituição em garantia", value="10 (dez) dias úteis", key="ct_prazo_reparo")
                with gf2:
                    ct_prazo_execucao = st.text_input("Prazo de execução/entrega", value="30 (trinta) dias", key="ct_prazo_exec")
                    ct_prazo_pgto = st.text_input("Prazo de pagamento", value="30 (trinta) dias", key="ct_prazo_pgto")

                st.markdown("---")
                st.markdown("**Penalidades**")
                gp1, gp2, gp3 = st.columns(3)
                with gp1:
                    ct_multa_mora = st.text_input("Multa moratória (por dia)", value="0,5%", key="ct_multa_mora")
                with gp2:
                    ct_limite_multa = st.text_input("Limite da multa moratória", value="10%", key="ct_limite_multa")
                with gp3:
                    ct_multa_comp = st.text_input("Multa compensatória", value="20%", key="ct_multa_comp")

                st.markdown("---")
                st.markdown("**Recebimento**")
                gr1, gr2 = st.columns(2)
                with gr1:
                    ct_receb_prov = st.text_input("Prazo receb. provisório", value="5 (cinco) dias úteis", key="ct_rec_prov")
                with gr2:
                    ct_receb_def = st.text_input("Prazo receb. definitivo", value="10 (dez) dias úteis", key="ct_rec_def")

                ct_obs = st.text_area("Observações / Disposições Gerais", height=80, key="ct_obs")
                submit_ct = st.form_submit_button("📑 Gerar Minuta de Contrato", use_container_width=True, disabled=bool(_faltam_doc))

            if submit_ct:
                tabela_itens_ct = ""
                valor_total_ct = 0.0
                for j, it in enumerate(itens_ct, 1):
                    vt = it["valor"] * it["quantidade"]
                    valor_total_ct += vt
                    tabela_itens_ct += f"| {j} | {it['descricao']} | {it['unidade']} | {it['quantidade']} | {_fmt_brl(it['valor'])} | {_fmt_brl(vt)} |\n"

                corpo_ct = TEMPLATE_MINUTA_CONTRATO.format(
                    tipo_contrato=ct_tipo, processo=ct_processo, licitacao=ct_licitacao,
                    modalidade=ct_modalidade, ano=ct_ano, vigencia=ct_vigencia,
                    orgao=ct_orgao, endereco_orgao=ct_endereco_orgao, cnpj_orgao=ct_cnpj_orgao,
                    cargo_representante=ct_cargo, representante=ct_representante,
                    empresa=ct_empresa, cnpj_empresa=ct_cnpj_empresa,
                    endereco_empresa=ct_end_empresa, representante_empresa=ct_repr_empresa,
                    objeto=ct_objeto, tabela_itens=tabela_itens_ct,
                    valor_total=_fmt_brl(valor_total_ct),
                    valor_extenso="(valor por extenso)",
                    prazo_pagamento=ct_prazo_pgto, prazo_execucao=ct_prazo_execucao,
                    percentual_garantia_contratual=ct_garantia_contratual,
                    garantia_produto=ct_garantia_produto, prazo_reparo=ct_prazo_reparo,
                    multa_moratoria=ct_multa_mora, limite_multa=ct_limite_multa,
                    multa_compensatoria=ct_multa_comp,
                    prazo_recebimento_provisorio=ct_receb_prov,
                    prazo_recebimento_definitivo=ct_receb_def,
                    observacoes=ct_obs or "Sem observações adicionais.",
                )
                _registrar_doc(tipo_doc, f"MINUTA DE CONTRATO DE {ct_tipo}", corpo_ct, "minuta_contrato")
        else:
            desc_ct = st.text_area(
                "Descreva o objeto, tipo (serviço/material), condições e o Babilaca gerará a Minuta completa:",
                height=180,
                key="ct_ia_input",
                placeholder=(
                    "Ex: Contrato de fornecimento de 200 cadeiras ergonômicas para o prédio administrativo.\n"
                    "Empresa: Móveis XYZ Ltda. Valor: R$ 150.000,00. Prazo de entrega: 45 dias.\n"
                    "Garantia do produto: 5 anos. Garantia contratual: 5% em seguro-garantia.\n"
                    "Incluir cláusula de assistência técnica e substituição em caso de defeito."
                ),
            )
            arquivo_ct = st.file_uploader("Ou envie Termo de Referência / proposta (PDF/Excel)", type=["pdf", "xlsx"], key="ct_upload")
            if st.button("🤖 Gerar Minuta com IA", key="btn_ct_ia", disabled=bool(_faltam_doc)):
                ctx_extra = ""
                if arquivo_ct:
                    if arquivo_ct.name.endswith(".pdf"):
                        ctx_extra = extrair_texto_pdf(arquivo_ct)
                    else:
                        ctx_extra, _ = extrair_dados_excel(arquivo_ct)
                if desc_ct or ctx_extra:
                    with st.spinner("Gerando Minuta de Contrato com IA..."):
                        prompt_ct = (
                            "Gere uma **Minuta de Contrato** completa e detalhada para a contratação abaixo, "
                            "conforme a Lei 14.133/2021.\n\n"
                            f"**Dados fornecidos:**\n{desc_ct}\n\n"
                        )
                        if ctx_extra:
                            prompt_ct += f"**Dados do arquivo anexado:**\n{ctx_extra[:4000]}\n\n"
                        prompt_ct += (
                            "O documento deve conter OBRIGATORIAMENTE todas as cláusulas essenciais:\n\n"
                            "1. **PREÂMBULO** — identificação das partes (CONTRATANTE e CONTRATADA)\n"
                            "2. **OBJETO** — descrição detalhada\n"
                            "3. **ITENS/ESPECIFICAÇÕES** — tabela com descrição, unidade, qtd, valor unitário e total\n"
                            "4. **VALOR E PAGAMENTO** — valor total, prazo de pagamento, condições, retenções fiscais\n"
                            "5. **VIGÊNCIA E EXECUÇÃO** — prazos, possibilidade de prorrogação (Art. 107)\n"
                            "6. **GARANTIA CONTRATUAL** (CLÁUSULA ESSENCIAL!) — percentual (5% a 10%), "
                            "modalidades (caução, seguro-garantia, fiança bancária), prazo de apresentação, "
                            "condições de liberação (Art. 96 da Lei 14.133/2021)\n"
                            "7. **GARANTIA DOS PRODUTOS/SERVIÇOS** (CLÁUSULA ESSENCIAL!) — prazo mínimo de garantia, "
                            "obrigações de substituição/reparo, prazo para atendimento de chamados, "
                            "cobertura (defeitos de fabricação, vícios, não conformidade), "
                            "exclusões (mau uso, caso fortuito), suspensão do prazo durante reparo, "
                            "assistência técnica, reexecução de serviços defeituosos\n"
                            "8. **OBRIGAÇÕES DA CONTRATADA** — habilitação, encargos, preposto, EPI, segurança\n"
                            "9. **OBRIGAÇÕES DO CONTRATANTE** — fiscalização, pagamento, comunicação\n"
                            "10. **FISCALIZAÇÃO** — fiscal e gestor do contrato (Art. 117)\n"
                            "11. **RECEBIMENTO** — provisório e definitivo, prazos, conferência\n"
                            "12. **ALTERAÇÃO CONTRATUAL** — limites de 25%/50% (Arts. 124-136)\n"
                            "13. **PENALIDADES** — multa moratória (% por dia), multa compensatória, "
                            "impedimento de licitar, inidoneidade (Arts. 155-163)\n"
                            "14. **RESCISÃO** — hipóteses (Arts. 137-139)\n"
                            "15. **FUNDAMENTAÇÃO LEGAL**\n"
                            "16. **FORO**\n"
                            "17. **ASSINATURAS** — espaço para CONTRATANTE, CONTRATADA e testemunhas\n\n"
                            "ATENÇÃO ESPECIAL às cláusulas de GARANTIA: sejam extremamente detalhistas sobre "
                            "prazos, coberturas, exclusões, procedimentos de acionamento e penalidades por descumprimento.\n\n"
                            "Use linguagem jurídica formal, tabelas Markdown e valores em Reais (R$)."
                        )
                        ctx = buscar_base_juridica("contrato garantia fiscalização recebimento penalidade pagamento")
                        system = _build_system_prompt(ctx)
                        resultado = chamar_ia([{"role": "user", "content": prompt_ct}], system + INSTRUCOES_DOCUMENTO)
                    _registrar_doc(tipo_doc, "MINUTA DE CONTRATO", resultado, "minuta_contrato_ia")
                else:
                    st.warning("Descreva a contratação ou envie um arquivo.")

    # ---- Classificação de Risco Jurídico ----
    elif "Risco" in tipo_doc:
        st.markdown("#### ⚖️ Classificação de Risco Jurídico")
        st.markdown(
            "Descreva o cenário de contratação e a IA irá gerar uma **classificação de risco** "
            "com **mapa de riscos** (probabilidade × impacto) e **recomendações de mitigação**."
        )
        cenario = st.text_area(
            "Descreva o cenário de contratação para análise de risco:",
            height=150,
            key="cenario_risco",
            placeholder="Ex: Contratação direta de software de gestão por dispensa de licitação, valor estimado R$ 70.000...",
        )
        if st.button("⚖️ Analisar Risco Jurídico", key="btn_risco", use_container_width=True):
            if cenario:
                with st.spinner("Analisando risco jurídico e gerando mapa de riscos..."):
                    resultado = classificar_risco_juridico(cenario)
                st.markdown("---")
                st.markdown(resultado)
                # Legenda visual da matriz de risco
                st.markdown("---")
                st.markdown("##### 🗺️ Legenda — Matriz de Risco")
                legenda_html = """
                <div style="margin-top:0.5rem;">
                <table style="border-collapse:collapse;width:100%;max-width:600px;margin:0 auto;text-align:center;font-size:13px;color:#e0e0e0;">
                <thead>
                <tr style="background:#001a4d;">
                    <th style="border:1px solid #d4af37;padding:8px 10px;color:#d4af37;">Probabilidade \\ Impacto</th>
                    <th style="border:1px solid #d4af37;padding:8px 10px;color:#d4af37;">Baixo</th>
                    <th style="border:1px solid #d4af37;padding:8px 10px;color:#d4af37;">Medio</th>
                    <th style="border:1px solid #d4af37;padding:8px 10px;color:#d4af37;">Alto</th>
                </tr>
                </thead>
                <tbody>
                <tr>
                    <td style="border:1px solid #445;padding:8px;font-weight:bold;background:#0a1628;color:#cbd5e1;">Alta</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(245,158,11,0.25);color:#f59e0b;font-weight:600;">Medio</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(220,38,38,0.25);color:#ef4444;font-weight:600;">Alto</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(220,38,38,0.45);color:#ff6b6b;font-weight:bold;">Critico</td>
                </tr>
                <tr>
                    <td style="border:1px solid #445;padding:8px;font-weight:bold;background:#0a1628;color:#cbd5e1;">Media</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(34,197,94,0.2);color:#22c55e;font-weight:600;">Baixo</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(245,158,11,0.25);color:#f59e0b;font-weight:600;">Medio</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(220,38,38,0.25);color:#ef4444;font-weight:600;">Alto</td>
                </tr>
                <tr>
                    <td style="border:1px solid #445;padding:8px;font-weight:bold;background:#0a1628;color:#cbd5e1;">Baixa</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(34,197,94,0.2);color:#22c55e;font-weight:600;">Baixo</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(34,197,94,0.2);color:#22c55e;font-weight:600;">Baixo</td>
                    <td style="border:1px solid #445;padding:8px;background:rgba(245,158,11,0.25);color:#f59e0b;font-weight:600;">Medio</td>
                </tr>
                </tbody>
                </table>
                </div>
                """
                st.markdown(legenda_html, unsafe_allow_html=True)
                st.caption("A tabela acima e uma referencia visual. O mapa detalhado por categoria esta na analise da IA.")
            else:
                st.warning("Descreva o cenário de contratação.")

    _exibir_doc(tipo_doc)
    _painel_kit(bool(_faltam_doc))

def _ck_abrir_documento(rotulo: str):
    """Atalho da lista de verificação: deixa o modelo escolhido na aba Documentos."""
    st.session_state["tipo_doc_sel"] = rotulo
    st.session_state["_doc_vindo_checklist"] = True
    st.session_state["babilaca_aba"] = "📄 Gerar Documentos com IA"


def _ck_aplicar_json(dados: dict) -> str:
    """Carrega uma conferência salva. Devolve a modalidade carregada."""
    modalidade = dados.get("modalidade")
    if modalidade not in CHECKLIST_MODALIDADES:
        raise ValueError("modalidade desconhecida no arquivo")
    st.session_state["checklist_modalidade"] = modalidade
    for campo in ("objeto", "valor", "responsavel", "nup"):
        st.session_state[f"ck_id_{campo}"] = (dados.get("identificacao") or {}).get(campo, "")
    salvos = {i.get("texto"): i for i in dados.get("itens") or []}
    for texto, _f, _a in CHECKLIST_MODALIDADES[modalidade]:
        item = salvos.get(texto) or {}
        chave = _ck_chave(modalidade, texto)
        situacao = item.get("situacao")
        st.session_state[f"ck_st_{chave}"] = situacao if situacao in MP.SITUACOES else "Pendente"
        st.session_state[f"ck_obs_{chave}"] = item.get("observacao") or ""
    return modalidade


# ============================================================
# TAB 3 — CHECKLIST DE PROCESSO
# ============================================================
with tab_checklist:
    st.markdown("""
    <div class="workspace-console checklist-workspace">
        <div class="workspace-console-content">
            <div class="workspace-console-icon">📋</div>
            <div><h3>Painel de Conferência do Processo</h3><p>Acompanhe a documentação essencial antes de formalizar ou encaminhar a contratação.</p></div>
            <span class="workspace-console-badge">CONTROLE DE ETAPAS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # widgets de abas que somem da tela perdem o valor; regravar mantém a conferência ao trocar de modalidade
    for _k in [k for k in st.session_state.keys() if str(k).startswith(("ck_st_", "ck_obs_", "ck_id_"))]:
        st.session_state[_k] = st.session_state[_k]

    with st.expander("💾 Carregar uma conferência salva"):
        _arq_ck = st.file_uploader("Arquivo .json baixado nesta aba", type=["json"], key="ck_json")
        if _arq_ck is not None:
            _conteudo = _arq_ck.getvalue()
            _assinatura = hashlib.md5(_conteudo).hexdigest()
            if st.session_state.get("_ck_json_aplicado") != _assinatura:
                try:
                    _mod = _ck_aplicar_json(json.loads(_conteudo.decode("utf-8")))
                    st.session_state["_ck_json_aplicado"] = _assinatura
                    st.success(f"Conferência carregada: {_mod}.")
                except Exception as _erro:
                    st.error(f"Arquivo inválido: {_erro}")

    modalidade_sel = st.selectbox(
        "Modalidade ou tipo de processo",
        list(CHECKLIST_MODALIDADES.keys()),
        key="checklist_modalidade",
    )

    # Expander explicativo da modalidade
    info = INFO_MODALIDADES.get(modalidade_sel, {})
    if info:
        with st.expander(f"ℹ️ O que é: {modalidade_sel}", expanded=False):
            st.markdown(f"**📖 Descrição**\n\n{info['descricao']}")
            st.markdown(f"**📌 Quando se aplica**\n\n{info['quando_aplicar']}")
            st.markdown(f"**💰 Limites financeiros**\n\n{info['limites']}")
            st.markdown(f"**📋 Como montar o processo (Lei 14.133/2021)**\n\n{info['como_montar']}")

    with st.expander("⏱️ Calculadora de prazos (dias úteis — Lei nº 14.133/2021)", expanded=False):
        st.caption("Contagem do art. 183: exclui o dia do começo e inclui o do vencimento; só dias úteis. Descontados "
                   "sábados, domingos e feriados nacionais (inclusive Sexta-feira Santa); feriados estaduais, municipais "
                   "e pontos facultativos não entram: confira o calendário local.")
        _pz1, _pz2 = st.columns([3, 1])
        with _pz1:
            _prazo_sel = st.selectbox("Prazo", [p[0] for p in MP.PRAZOS], key="prazo_sel")
        _pz = MP.PRAZOS_POR_ROTULO[_prazo_sel]
        with _pz2:
            _base = st.date_input(_pz[3], value=datetime.now().date(), key="prazo_base", format="DD/MM/YYYY")
        _calc = MP.calcular_prazo(_prazo_sel, _base)
        _dias_semana = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
        st.success(f"**{_calc['significado']}: {_calc['data'].strftime('%d/%m/%Y')} ({_dias_semana[_calc['data'].weekday()]})** "
                   f"— {abs(_calc['dias'])} dia(s) útil(eis) {'depois' if _calc['dias'] > 0 else 'antes'} de "
                   f"{_base.strftime('%d/%m/%Y')}. Fundamento: {_calc['fundamento']}.")
        if not _calc["base_util"] and _calc["dias"] > 0:
            st.caption("A data-base não é dia útil: a contagem começa no primeiro dia útil seguinte, como no cálculo acima.")
        if _prazo_sel.startswith("Edital"):
            _imp = MP.somar_dias_uteis(_calc["data"], -3)
            st.info(f"Com a abertura nessa data, o último dia para impugnação ou esclarecimento seria "
                    f"**{_imp.strftime('%d/%m/%Y')}** (3 dias úteis antes — art. 164).")

    with st.expander("🗂️ Identificação do processo (sai no PDF)", expanded=False):
        _i1, _i2 = st.columns([3, 1])
        with _i1:
            st.text_input("Objeto", key="ck_id_objeto", placeholder="Ex: Aquisição de material de expediente")
        with _i2:
            st.text_input("Valor estimado", key="ck_id_valor", placeholder="R$")
        _i3, _i4 = st.columns(2)
        with _i3:
            st.text_input("NUP do processo", key="ck_id_nup", placeholder="Se vazio, usa o NUP da aba Documentos")
        with _i4:
            _preencher("ck_id_responsavel", _om("ass0_nome"))
            st.text_input("Responsável pela conferência", key="ck_id_responsavel")

    itens_checklist = CHECKLIST_MODALIDADES[modalidade_sel]
    st.caption(f"{len(itens_checklist)} itens nesta modalidade. Marque cada um como **Presente**, **Pendente** ou "
               "**Não se aplica**; o fundamento legal aparece abaixo de cada item.")
    _mostrar_obs = st.toggle("Mostrar campos de observação", key="ck_mostrar_obs")

    situacoes, observacoes = [], []
    for _n, (_texto, _fund, _atalho) in enumerate(itens_checklist, 1):
        _ch = _ck_chave(modalidade_sel, _texto)
        st.session_state.setdefault(f"ck_st_{_ch}", "Pendente")
        _c_txt, _c_st = st.columns([4, 2.6])
        with _c_txt:
            st.markdown(f"**{_n}.** {_texto}")
            st.caption(f"⚖️ {_fund}")
            if _atalho and _atalho[0] == "doc":
                st.button(f"📄 Abrir modelo: {_atalho[1].split(' — ')[0]}", key=f"ck_doc_{_ch}",
                          on_click=_ck_abrir_documento, args=(_atalho[1],))
            elif _atalho:
                st.page_link(_atalho[1], label=_atalho[2], icon="↗️")
        with _c_st:
            _sit = st.segmented_control("Situação", MP.SITUACOES, key=f"ck_st_{_ch}", label_visibility="collapsed")
        situacoes.append(_sit or "Pendente")
        if _mostrar_obs:
            observacoes.append(st.text_input("Observação", key=f"ck_obs_{_ch}", label_visibility="collapsed",
                                             placeholder="Observação (folha do processo, data, pendência...)"))
        else:
            observacoes.append(st.session_state.get(f"ck_obs_{_ch}", ""))

    # Resumo
    _r = MP.resumo_checklist(situacoes)
    marcados, total, percentual = _r["presentes"], _r["aplicaveis"], _r["percentual"]
    st.markdown(f"""
    <div class="checklist-progress">
        <div class="checklist-progress-head">
            <span class="checklist-progress-title">Andamento da documentação</span>
            <span class="checklist-progress-value">{marcados}/{total} · {percentual}%</span>
        </div>
        <div class="checklist-progress-track"><div class="checklist-progress-fill" style="width:{percentual}%;"></div></div>
    </div>
    """, unsafe_allow_html=True)
    if _r["nao_aplica"]:
        st.caption(f"{_r['nao_aplica']} item(ns) marcado(s) como não se aplica saem da conta.")
    if marcados == total:
        st.success(f"✅ Processo completo! {marcados}/{total} itens aplicáveis presentes.")
    elif marcados > 0:
        st.warning(f"⚠️ {marcados}/{total} itens presentes. Faltam {total - marcados}.")
    else:
        st.info(f"📋 {total} itens a conferir. Marque os que já constam do processo.")

    # Exportação: PDF/Word no padrão do documento_oficial e JSON para continuar depois
    _ident = {c: st.session_state.get(f"ck_id_{c}", "") for c in ("objeto", "valor", "responsavel", "nup")}
    _corpo_ck = MP.corpo_checklist(modalidade_sel, itens_checklist, situacoes, observacoes, _ident)
    _titulo_ck = f"LISTA DE VERIFICAÇÃO — {modalidade_sel}"
    _arq_base = f"checklist_{MP.nome_arquivo(modalidade_sel)}"
    _faltam_ck = _pendencias_documento()
    if _faltam_ck:
        st.warning("Para baixar o PDF ou o Word, preencha na aba **📄 Documentos** os dados obrigatórios da OM e do(s) "
                   "signatário(s). Falta: " + ", ".join(_faltam_ck) + ".")
    _e1, _e2, _e3 = st.columns(3)
    with _e1:
        st.download_button("🖨️ Baixar PDF", gerar_pdf_documento(_titulo_ck, _corpo_ck, nup=_ident["nup"]) if not _faltam_ck else b"",
                           f"{_arq_base}.pdf", "application/pdf", key="dl_checklist_pdf", use_container_width=True,
                           disabled=bool(_faltam_ck))
    with _e2:
        st.download_button("📝 Baixar Word", gerar_docx_documento(_titulo_ck, _corpo_ck, nup=_ident["nup"]) if not _faltam_ck else b"",
                           f"{_arq_base}.docx",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key="dl_checklist_docx", use_container_width=True, disabled=bool(_faltam_ck))
    with _e3:
        _json_ck = json.dumps({"versao": 1, "modalidade": modalidade_sel, "identificacao": _ident,
                               "itens": [{"texto": t, "fundamento": f, "situacao": s_, "observacao": o}
                                         for (t, f, _a), s_, o in zip(itens_checklist, situacoes, observacoes)]},
                              ensure_ascii=False, indent=2)
        st.download_button("💾 Salvar conferência (.json)", _json_ck.encode("utf-8"), f"{_arq_base}.json",
                           "application/json", key="dl_checklist_json", use_container_width=True,
                           help="Guarde o arquivo e carregue-o depois em 'Carregar uma conferência salva'.")


def formatar_cnpj_conf(cnpj: str | None) -> str:
    from servicos_publicos import formatar_cnpj
    return formatar_cnpj(cnpj) if cnpj else ""


def _conf_aplicar_checklist(modalidade: str, itens: list[dict]):
    """Leva o resultado da conferência para a aba Checklist (itens encontrados ficam 'Presente')."""
    st.session_state["checklist_modalidade"] = modalidade
    for item in itens:
        chave = _ck_chave(modalidade, item["texto"])
        st.session_state[f"ck_st_{chave}"] = "Presente" if item["situacao"] == "Presente" else "Pendente"
        st.session_state[f"ck_obs_{chave}"] = item["onde"] if item["situacao"] == "Presente" else ""
    st.session_state["babilaca_aba"] = "📋 Checklist de Processo"


def _conf_consultas_externas(cnpj: str) -> tuple[list[dict], list[dict]]:
    """Sanções (CEIS/CNEP/CEPIM) e cadastro no Compras.gov.br do fornecedor identificado."""
    from servicos_publicos import consultar_sancoes, consultar_sicaf, formatar_cnpj, texto_sicaf
    externos, achados = [], []
    sancoes, datas, erro = consultar_sancoes(cnpj)
    if erro:
        externos.append({"base": "CEIS/CNEP/CEPIM", "resultado": f"não consultado ({erro})"})
    for base, registros in (sancoes or {}).items():
        vigentes = [r for r in registros if r.get("vigente")]
        externos.append({"base": f"{base} (base de {datas.get(base, '-')})",
                         "resultado": f"{len(vigentes)} sanção(ões) vigente(s)" if vigentes else
                         ("só sanções encerradas" if registros else "nada consta")})
        if vigentes:
            achados.append({"gravidade": CP.GRAVE, "titulo": f"Fornecedor com sanção vigente no {base}",
                            "detalhe": f"{formatar_cnpj(cnpj)}: {len(vigentes)} registro(s) vigente(s). Verifique se a "
                                       "sanção impede esta contratação (art. 156 da Lei nº 14.133/2021).", "onde": "-"})
    sicaf, erro = consultar_sicaf(cnpj)
    rotulo = texto_sicaf(sicaf) if not erro else f"não consultado ({erro})"
    externos.append({"base": "Cadastro de fornecedores (SICAF)", "resultado": rotulo})
    if not erro and rotulo != "Ativo e habilitado a licitar":
        achados.append({"gravidade": CP.CORRIGIR, "titulo": "Fornecedor não está ativo e habilitado no SICAF",
                        "detalhe": f"{formatar_cnpj(cnpj)}: {rotulo}. Confira o SICAF antes de contratar.", "onde": "-"})
    return externos, achados


# ============================================================
# TAB 4 — CONFERÊNCIA DO PROCESSO
# ============================================================
with tab_conferencia:
    st.markdown("""
    <div class="workspace-console checklist-workspace">
        <div class="workspace-console-content">
            <div class="workspace-console-icon">🔎</div>
            <div><h3>Conferência do Processo</h3><p>Envie o processo em PDF: o sistema identifica as peças, marca a lista de verificação e aponta inconsistências.</p></div>
            <span class="workspace-console-badge">REGRAS OBJETIVAS</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("O que é conferido: presença e ordem das peças; coerência de CNPJ e valores entre proposta, certidões, "
               "crédito e empenho; validade das certidões; limite de dispensa; prazo do aviso; datas (parecer antes da "
               "autorização, autorização antes do empenho); idade da pesquisa de preços; lacunas não preenchidas. "
               "É uma triagem: não substitui a análise do agente de contratação nem o parecer jurídico.")
    _cf1, _cf2 = st.columns([3, 1])
    with _cf1:
        conf_modalidade = st.selectbox("Modalidade ou tipo de processo", list(CHECKLIST_MODALIDADES), key="conf_modalidade")
    with _cf2:
        conf_ref = st.date_input("Data de referência", value=None, key="conf_ref", format="DD/MM/YYYY",
                                 help="Data em que a validade das certidões é conferida. Em branco: data do empenho, "
                                      "da autorização ou hoje.")
    conf_arquivos = st.file_uploader("Arquivos do processo (PDF com texto ou Word), na ordem do processo",
                                     type=["pdf", "docx"], accept_multiple_files=True, key="conf_arquivos")
    conf_externas = st.checkbox("Consultar também sanções (CEIS/CNEP/CEPIM) e SICAF do fornecedor identificado",
                                value=True, key="conf_externas")
    if st.button("🔎 Conferir processo", key="btn_conferir", type="primary", use_container_width=True,
                 disabled=not conf_arquivos):
        with st.spinner("Lendo as páginas e conferindo o processo..."):
            _pags = CP.extrair_paginas([(a.name, a.getvalue()) for a in conf_arquivos])
            _res = CP.conferir(_pags, conf_modalidade, conf_ref)
            _ext = []
            if conf_externas and _res["dados"]["contratado"]:
                _ext, _ach = _conf_consultas_externas(_res["dados"]["contratado"])
                _res["achados"] = sorted(_res["achados"] + _ach, key=lambda a: CP.ORDEM_GRAVIDADE[a["gravidade"]])
        st.session_state["conf_resultado"] = {"res": _res, "ext": _ext, "modalidade": conf_modalidade,
                                              "arquivos": [a.name for a in conf_arquivos]}

    _conf = st.session_state.get("conf_resultado")
    if _conf:
        _res = _conf["res"]
        _cont = {g: sum(1 for a in _res["achados"] if a["gravidade"] == g) for g in (CP.GRAVE, CP.CORRIGIR, CP.SUGESTAO)}
        _presentes = sum(1 for c in _res["checklist"] if c["situacao"] == "Presente")
        _m1, _m2, _m3, _m4 = st.columns(4)
        _m1.metric("🔴 Graves", _cont[CP.GRAVE])
        _m2.metric("🟡 A corrigir", _cont[CP.CORRIGIR])
        _m3.metric("🔵 Sugestões", _cont[CP.SUGESTAO])
        _m4.metric("Itens encontrados", f"{_presentes}/{len(_res['checklist'])}")
        _d = _res["dados"]
        st.caption(f"Fornecedor identificado: **{formatar_cnpj_conf(_d['contratado']) or 'não identificado'}** · valor estimado: "
                   f"**{CP.brl(_d['total']).replace('$', chr(92) + '$')}** · referência: **{CP.fmt(_d['referencia'])}** · "
                   f"{len(_res['paginas'])} página(s) em {len(_conf['arquivos'])} arquivo(s).")
        for _aviso in _res["avisos"]:
            st.warning(_aviso)
        if _conf["modalidade"] != conf_modalidade:
            st.info(f"Resultado da conferência feita como **{_conf['modalidade']}**. Clique em Conferir para refazer.")

        st.markdown("##### Inconsistências")
        if not _res["achados"]:
            st.success("Nenhuma inconsistência encontrada pelas regras automáticas.")
        for _a in _res["achados"]:
            with st.container(border=True):
                st.markdown(f"{_a['gravidade']} **{_a['titulo']}**".replace("$", "\\$"))
                st.caption((f"{_a['detalhe']}" + (f" · 📍 {_a['onde']}" if _a["onde"] != "-" else "")).replace("$", "\\$"))
        if _conf["ext"]:
            st.markdown("##### Consultas do fornecedor")
            st.dataframe(pd.DataFrame(_conf["ext"]).rename(columns={"base": "Base", "resultado": "Resultado"}),
                         hide_index=True, width="stretch")
        with st.expander("📑 Peças identificadas", expanded=False):
            st.dataframe(pd.DataFrame([{"Peça": CP.ROTULO[d["tipo"]], "Onde": CP.onde(_res["paginas"], d["indices"]),
                                        "Data": CP.fmt(d["data"])} for d in _res["docs"]]),
                         hide_index=True, width="stretch")
        with st.expander("📋 Lista de verificação marcada", expanded=False):
            st.dataframe(pd.DataFrame([{"Item": c["texto"], "Situação": c["situacao"], "Onde": c["onde"]}
                                       for c in _res["checklist"]]), hide_index=True, width="stretch")
        st.button("📋 Levar o resultado para a aba Checklist", key="btn_conf_ck", use_container_width=True,
                  on_click=_conf_aplicar_checklist, args=(_conf["modalidade"], _res["checklist"]))

        _corpo_conf = CP.corpo_relatorio(_res, _conf["modalidade"], _conf["arquivos"], _conf["ext"])
        _titulo_conf = "RELATÓRIO DE CONFERÊNCIA DO PROCESSO"
        _faltam_conf = _pendencias_documento()
        if _faltam_conf:
            st.warning("Para baixar o relatório, preencha na aba **📄 Documentos** os dados obrigatórios da OM e do(s) "
                       "signatário(s). Falta: " + ", ".join(_faltam_conf) + ".")
        _r1, _r2 = st.columns(2)
        with _r1:
            st.download_button("🖨️ Relatório em PDF", gerar_pdf_documento(_titulo_conf, _corpo_conf) if not _faltam_conf else b"",
                               "conferencia_processo.pdf", "application/pdf", key="dl_conf_pdf",
                               use_container_width=True, disabled=bool(_faltam_conf))
        with _r2:
            st.download_button("📝 Relatório em Word", gerar_docx_documento(_titulo_conf, _corpo_conf) if not _faltam_conf else b"",
                               "conferencia_processo.docx",
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                               key="dl_conf_docx", use_container_width=True, disabled=bool(_faltam_conf))


# ============================================================
# TAB 5 — LIMITE DE DISPENSA (fracionamento, art. 75, §1º)
# ============================================================
with tab_fracionamento:
    st.markdown("""
    <div class="workspace-console checklist-workspace">
        <div class="workspace-console-content">
            <div class="workspace-console-icon">⚖️</div>
            <div><h3>Limite de Dispensa por Ramo de Atividade</h3><p>Quanto a UASG já contratou por dispensa em razão do valor no exercício, por ramo, e quanto ainda cabe.</p></div>
            <span class="workspace-console-badge">ART. 75, §1º</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("O limite do art. 75, I e II, vale para o somatório do exercício na unidade gestora, por objetos do mesmo "
               "ramo de atividade (art. 75, §1º). Ramo: família do item no CATMAT (PDM) para materiais e serviço do "
               "CATSER para serviços (IN SEGES/ME nº 67/2021). Também soma por natureza de despesa e subelemento "
               "(Portaria STN nº 448/2002), sugeridos pelo sistema e ajustáveis por você. Fonte: dispensas publicadas no "
               "PNCP (dados abertos do Compras.gov.br). " + MP.nota_limites().replace("$", "\\$"))
    _f1, _f2, _f3 = st.columns([2, 1, 2])
    with _f1:
        _preencher("frac_uasg", _om("uasg"))
        frac_uasg = st.text_input("UASG da unidade gestora", key="frac_uasg", placeholder="Ex: 765000")
    with _f2:
        frac_ano = st.number_input("Exercício", min_value=2023, max_value=datetime.now().year,
                                   value=datetime.now().year, step=1, key="frac_ano")
    with _f3:
        st.write("")
        st.write("")
        _verificar = st.button("⚖️ Verificar o exercício", key="frac_verificar", type="primary",
                               use_container_width=True, disabled=not frac_uasg.strip().isdigit())
    if _verificar:
        _barra = st.progress(0.0, text="Buscando as dispensas da UASG no PNCP...")
        _compras, _erro = FR.buscar_dispensas(frac_uasg.strip(), int(frac_ano),
                                              lambda f, t: _barra.progress(min(f, 1.0), text=t))
        _barra.empty()
        if _erro:
            st.error(f"Não foi possível consultar agora: {_erro}")
        else:
            _grupos = FR.consolidar(_compras)
            _nome = next((c.get("unidadeOrgaoNomeUnidade") for c in _compras if c.get("unidadeOrgaoNomeUnidade")), "")
            _anterior = st.session_state.get("frac_resultado") or {}
            if _anterior.get("uasg") != frac_uasg.strip():
                st.session_state["frac_ajustes"] = {}      # subelementos escolhidos valem para a mesma UASG
            st.session_state["frac_resultado"] = {"uasg": frac_uasg.strip(), "ano": int(frac_ano), "nome": _nome,
                                                  "compras": _compras, "grupos": _grupos,
                                                  "versao": int(datetime.now().timestamp())}
            st.session_state.pop(f"doc_gerado_{MP.DOC_FRACIONAMENTO}", None)
            st.session_state.pop(f"doc_editado_{MP.DOC_FRACIONAMENTO}", None)

    _fr = st.session_state.get("frac_resultado")
    if _fr:
        _g = _fr["grupos"]
        _ajustes = st.session_state.setdefault("frac_ajustes", {})
        _materiais = [x for x in _g if x.get("tipo", "Material") == "Material"]
        _servicos = [x for x in _g if x.get("tipo") == "Serviço"]
        st.markdown(f"**UASG {_fr['uasg']}{' – ' + _fr['nome'] if _fr['nome'] else ''} · exercício {_fr['ano']}**")
        _k1, _k2, _k3, _k4, _k5 = st.columns(5)
        _k1.metric("Dispensas por valor", len(_fr["compras"]))
        _k2.metric("📦 Ramos de material", len(_materiais))
        _k3.metric("🛠️ Ramos de serviço", len(_servicos))
        _k4.metric("🔴 Ultrapassados", sum(1 for x in _g if x["uso"] >= 1))
        _k5.metric("🟡 Acima de 80%", sum(1 for x in _g if 0.8 <= x["uso"] < 1))
        if not _fr["compras"]:
            st.info("Nenhuma dispensa por valor (art. 75, I ou II) publicada no PNCP para esta UASG no exercício.")
        else:
            _opcoes_nd = ND.opcoes()
            _t_mat, _t_serv, _t_nd = st.tabs([f"📦 Materiais ({len(_materiais)})", f"🛠️ Serviços ({len(_servicos)})",
                                              "🧾 Por natureza de despesa"])
            _conf_moeda = {"Total": st.column_config.NumberColumn(format="R$ %.2f"),
                           "Saldo": st.column_config.NumberColumn(format="R$ %.2f"),
                           "Uso": st.column_config.ProgressColumn("Uso do limite", format="%.0f%%", min_value=0,
                                                                 max_value=100)}
            for _aba, _lista, _tipo in ((_t_mat, _materiais, "Material"), (_t_serv, _servicos, "Serviço")):
                with _aba:
                    if not _lista:
                        st.info(f"Nenhum {'material' if _tipo == 'Material' else 'serviço'} nas dispensas por valor do exercício.")
                        continue
                    _df = pd.DataFrame([{
                        "Situação": x["situacao"], "Inciso": x["inciso"], "Ramo de atividade": x["ramo"],
                        "Subelemento": ND.rotulo(_ajustes.get(f"{x['inciso']}|{x['chave']}", x.get("subelemento") or "")),
                        "Dispensas": len(x["compras"]), "Total": x["total"], "Saldo": max(x["saldo"], 0),
                        "Uso": x["uso"] * 100, "Base": x["base"], "Classe": x["classe"],
                        "Exemplos de itens": "; ".join(x["exemplos"]),
                        "Valor estimado?": "sim" if x["estimado"] else ""} for x in _lista])
                    _ed = st.data_editor(
                        _df, key=f"frac_ed_{_tipo}_{_fr.get('versao', 0)}", hide_index=True, width="stretch",
                        disabled=[c for c in _df.columns if c != "Subelemento"],
                        column_config={**_conf_moeda, "Subelemento": st.column_config.SelectboxColumn(
                            "Subelemento (editável)", options=_opcoes_nd, width="large",
                            help="Sugerido pela família ou pelo serviço. Corrija se a sua OM classifica de outro modo.")})
                    for _x, _rot in zip(_lista, _ed["Subelemento"]):
                        _chave = f"{_x['inciso']}|{_x['chave']}"
                        _cod = ND.codigo_do_rotulo(_rot)
                        if _cod != (_x.get("subelemento") or ""):
                            _ajustes[_chave] = _cod
                        else:
                            _ajustes.pop(_chave, None)
                    if _tipo == "Serviço":
                        st.caption("Serviços agrupados pelo catálogo CATSER. \"CATSER (semelhança N%)\" = nome do serviço "
                                   "não idêntico ao do catálogo; confira o agrupamento.")
                    else:
                        st.caption("Materiais agrupados pela família do CATMAT (PDM). \"descrição (aproximado)\" = item "
                                   "sem correspondência no catálogo.")
            with _t_nd:
                _subs = FR.por_subelemento(_g, _ajustes)
                st.dataframe(pd.DataFrame([{
                    "Situação": x["situacao"], "Inciso": x["inciso"], "Natureza / subelemento": x["rotulo"],
                    "Ramos": x["ramos"], "Dispensas": x["compras"], "Total": x["total"], "Saldo": max(x["saldo"], 0),
                    "Uso": x["uso"] * 100} for x in _subs]), hide_index=True, width="stretch", column_config=_conf_moeda)
                if any(not x["subelemento"] for x in _subs):
                    st.warning("Há ramos com subelemento **a definir**: escolha o subelemento nas abas Materiais e "
                               "Serviços para a soma ficar completa.")
                st.caption("Soma por subelemento da Portaria STN nº 448/2002 (3.3.90.30, 3.3.90.39 e 4.4.90.52), usando "
                           "os subelementos escolhidos nas abas ao lado. Despesas de TIC têm naturezas próprias "
                           "(3.3.90.40 e 4.4.90.40) e não estão detalhadas.")
            # relatório acompanha os subelementos escolhidos (sem apagar edições feitas à mão no texto)
            _corpo_novo = FR.corpo_relatorio(_fr["uasg"], _fr["nome"], _fr["ano"], _g, _fr["compras"], _ajustes)
            _doc_atual = st.session_state.get(f"doc_gerado_{MP.DOC_FRACIONAMENTO}")
            if not _doc_atual or _doc_atual["corpo"] != _corpo_novo:
                _editado = st.session_state.get(f"doc_editado_{MP.DOC_FRACIONAMENTO}")
                _mexido = _doc_atual and _editado and _editado != _doc_atual["corpo"]
                st.session_state[f"doc_gerado_{MP.DOC_FRACIONAMENTO}"] = {
                    "titulo": "RELATÓRIO DE VERIFICAÇÃO DE FRACIONAMENTO", "corpo": _corpo_novo,
                    "nome": f"fracionamento_{_fr['uasg']}_{_fr['ano']}", "oficio": None}
                if not _mexido:
                    st.session_state[f"doc_editado_{MP.DOC_FRACIONAMENTO}"] = _corpo_novo

        st.markdown("##### 🧮 Simular uma nova dispensa")
        _s1, _s2, _s3, _s4 = st.columns([3, 1.3, 1, 1])
        with _s1:
            _sim_desc = st.text_input("Descrição do item (como no CATMAT)", key="frac_sim_desc",
                                      placeholder="Ex: PAPEL A4, GRAMATURA: 75 G/M2")
        with _s2:
            _sim_valor = st.number_input("Valor (R$)", min_value=0.0, step=100.0, format="%.2f", key="frac_sim_valor")
        with _s3:
            _sim_tipo = st.selectbox("Tipo", ["Material", "Serviço"], key="frac_sim_tipo")
        with _s4:
            _sim_inc = st.selectbox("Inciso", ["II", "I"], key="frac_sim_inc")
        if _sim_desc.strip() and _sim_valor:
            _sim = FR.simular(_g, _sim_desc, _sim_valor, _sim_tipo == "Material", _sim_inc)
            _msg = (f"Ramo **{_sim['ramo']}** ({_sim['base']}): já contratado {MP.brl(_sim['ja_contratado'])} + esta "
                    f"dispensa {MP.brl(_sim['novo'])} = **{MP.brl(_sim['total'])}** de {MP.brl(_sim['limite'])}.").replace("$", "\\$")
            (st.success if _sim["cabe"] else st.error)(
                _msg + (" Cabe no limite." if _sim["cabe"] else " **Ultrapassa o limite**: avalie licitar ou outra hipótese."))
            _cod_sim = next((_ajustes.get(f"{_sim_inc}|{x['chave']}", x.get("subelemento") or "") for x in _g
                             if x["chave"] == _sim["chave"] and x["inciso"] == _sim_inc), "") \
                or ND.sugerir(_sim_tipo == "Material", _sim["ramo"], _sim.get("classe", ""))
            if _cod_sim:
                _ja_sub = sum(x["total"] for x in FR.por_subelemento(_g, _ajustes)
                              if x["subelemento"] == _cod_sim and x["inciso"] == _sim_inc)
                _tot_sub = _ja_sub + _sim_valor
                (st.success if _tot_sub < _sim["limite"] else st.error)(
                    (f"Subelemento **{ND.rotulo(_cod_sim)}**: já contratado {MP.brl(_ja_sub)} + esta dispensa = "
                     f"**{MP.brl(_tot_sub)}** de {MP.brl(_sim['limite'])}."
                     + (" Cabe no limite." if _tot_sub < _sim["limite"] else " **Ultrapassa o limite pelo subelemento.**")
                     ).replace("$", "\\$"))

        _faltam_fr = _pendencias_documento()
        _doc_fr = st.session_state.get(f"doc_gerado_{MP.DOC_FRACIONAMENTO}")
        if _doc_fr:
            _corpo_fr = st.session_state.get(f"doc_editado_{MP.DOC_FRACIONAMENTO}") or _doc_fr["corpo"]
            if _faltam_fr:
                st.warning("Para baixar o relatório, preencha na aba **📄 Documentos** os dados obrigatórios da OM. "
                           "Falta: " + ", ".join(_faltam_fr) + ".")
            _d1, _d2 = st.columns(2)
            with _d1:
                st.download_button("🖨️ Relatório em PDF", gerar_pdf_documento(_doc_fr["titulo"], _corpo_fr) if not _faltam_fr else b"",
                                   f"{_doc_fr['nome']}.pdf", "application/pdf", key="dl_frac_pdf",
                                   use_container_width=True, disabled=bool(_faltam_fr))
            with _d2:
                st.download_button("📝 Relatório em Word", gerar_docx_documento(_doc_fr["titulo"], _corpo_fr) if not _faltam_fr else b"",
                                   f"{_doc_fr['nome']}.docx",
                                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                   key="dl_frac_docx", use_container_width=True, disabled=bool(_faltam_fr))
            st.caption("O relatório também entra no Kit do processo e pode ser editado na aba Documentos "
                       f"(\"{MP.DOC_FRACIONAMENTO}\"). O TJDL passa a oferecer o total do ramo para preencher o campo "
                       "\"já contratado no exercício\".")
