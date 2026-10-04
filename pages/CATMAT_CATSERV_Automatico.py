"""Sugestão automática de códigos CATMAT e CATSERV a partir de descrições."""

from __future__ import annotations

import io
import json
import os
import re
import unicodedata
import base64
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from functools import lru_cache

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


st.set_page_config(
    page_title="CATMAT/CATSERV Automático",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")
PDM_PATH = os.path.join(CATALOGO_DIR, "catalogo_pdm.json")
CATSERV_PATH = os.path.join(CATALOGO_DIR, "catalogo_servicos.json")
CATMAT_API_URL = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"
STOP_WORDS = {"a", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "o", "os", "para", "por", "sem", "um", "uma", "tipo"}
# Termos de embalagem/unidade: descrevem como o item é comprado, não o que ele é.
# Entram na comparação com peso baixo e nunca definem o "termo principal" do item.
TERMOS_EMBALAGEM = {
    "caixa", "cx", "fardo", "folha", "pacote", "pct", "resma", "und", "unid", "unidade",
    "kg", "ml", "mm", "cm", "m2", "gr", "lt", "litro", "metro",
}
TERMOS_RESTRITIVOS = {
    "automotivo", "cartucho", "descartavel", "hospitalar", "impressora", "industrial",
    "infantil", "medico", "odontologico", "recarga", "refil", "tinteiro", "toner",
}
# Termo da descrição -> grupos de termos que o catálogo usa para dizer a mesma coisa.
# Um grupo só vale se TODOS os seus termos estiverem na descrição do catálogo.
EQUIVALENCIAS = {
    "a4": [{"210", "297"}],
    "a3": [{"297", "420"}],
    "oficio": [{"216", "330"}],
    "carta": [{"216", "279"}],
    "sulfite": [{"alcalino"}, {"reprografico"}],
    "reprografico": [{"sulfite"}],
}
# Termos que, presentes na descrição do catálogo, indicam o produto usual daquela compra.
PREFERENCIAS = [
    ({"papel", "resma"}, {"sulfite", "alcalino", "reprografico"}),
    ({"papel", "a4"}, {"sulfite", "alcalino", "reprografico"}),
]
# Termos da descrição -> consultas adicionais enviadas ao catálogo (a API busca por trecho).
EXPANSOES_DE_BUSCA = [
    ({"caneta"}, ["caneta esferografica"]),
    ({"fita", "crepe"}, ["fita crepe adesiva"]),
    ({"papel", "a4"}, ["papel sulfite", "papel alcalino", "papel impressao"]),
    ({"papel", "resma"}, ["papel sulfite", "papel alcalino", "papel impressao"]),
    ({"papel", "sulfite"}, ["papel alcalino", "papel impressao"]),
]
FALLBACKS_GENERICOS = {
    "caneta": {"codigo_pdm": "99", "termos_preferidos": {"esferografica"}},
    "fita crepe": {"codigo_pdm": "18071", "termos_preferidos": {"papel", "crepado"}},
}
LIMIAR_SIMILARIDADE = 45.0
PAGINAS_POR_CONSULTA = 3
TAMANHO_PAGINA = 100


st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background: #001a4d !important;
            color: #f8fafc;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
            border-right: 3px solid #d4af37 !important;
        }
        [data-testid="stSidebarNav"] { display: none !important; }
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
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
            background: linear-gradient(135deg, #1a1a1a, #252525) !important;
            border: 1px solid #333 !important; border-radius: 8px !important;
            color: #fff !important; margin: .2rem 0 !important; padding: .45rem .7rem !important;
            font-size: 12.5px !important; font-weight: 600 !important; justify-content: center !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span { color: #fff !important; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
            background: #d4af37 !important; border-color: #d4af37 !important;
        }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span { color: #0a0a0a !important; }
        .catalog-header {
            background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%);
            border: 1px solid rgba(96, 165, 250, .45); border-radius: 10px;
            padding: 1.35rem 1.55rem; margin-bottom: 1rem;
            box-shadow: 0 10px 28px rgba(0, 0, 0, .28);
        }
        .catalog-header-top { display: flex; align-items: center; gap: .85rem; flex-wrap: wrap; }
        .catalog-symbol { width: 2.8rem; height: 2.8rem; display: flex; justify-content: center; align-items: center; background: #d4af37; border-radius: 7px; font-size: 1.35rem; }
        .catalog-header h1 { color: #fff; margin: 0; font-size: 1.35rem; }
        .catalog-header p { color: #bfdbfe; margin: .18rem 0 0; font-size: .85rem; }
        .catalog-badge { color: #d4af37; font-size: .7rem; font-weight: 800; letter-spacing: .08em; margin-left: auto; }
        .input-panel, .result-panel {
            background: rgba(8, 26, 57, .78); border: 1px solid #1e5b9f; border-radius: 9px;
            padding: 1rem 1.1rem; margin: .5rem 0 1rem;
        }
        .input-panel h3, .result-panel h3 { color: #d4af37; font-size: .95rem; margin: 0 0 .25rem; }
        .input-panel p, .result-panel p { color: #b6cae2; font-size: .78rem; margin: 0; }
        .status-chip { display: inline-block; border-radius: 999px; padding: .2rem .55rem; font-size: .7rem; font-weight: 700; }
        .status-good { background: rgba(34, 197, 94, .18); color: #86efac; border: 1px solid rgba(34, 197, 94, .4); }
        .status-review { background: rgba(245, 158, 11, .15); color: #fcd34d; border: 1px solid rgba(245, 158, 11, .4); }
        .status-low { background: rgba(239, 68, 68, .14); color: #fca5a5; border: 1px solid rgba(239, 68, 68, .4); }
        [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
            background: rgba(7, 20, 42, .8) !important; border-color: #2b6cb0 !important; color: #f8fafc !important;
        }
        [data-testid="stDataFrame"] { border: 1px solid #1e5b9f; border-radius: 8px; overflow: hidden; }
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
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
    st.page_link("pages/Calculo_IPCA.py", label="Cálculo IPCA", icon="📊")
    st.page_link("pages/CATMAT_CATSERV_Automatico.py", label="CATMAT/CATSERV", icon="🔎")
    st.markdown("---")
    st.markdown("## LINKS ÚTEIS")
    st.markdown("""<div style="margin-bottom:0.6rem;">
        <a href="https://detetive-obtencao.vercel.app/" target="_blank" style="color:#cbd5e1;text-decoration:none;font-size:0.9rem;display:flex;align-items:center;gap:0.5rem;">🚨 Detetive Obtenção</a>
    </div>
    <div style="margin-bottom:1rem;">
        <a href="https://depurador.streamlit.app/" target="_blank" style="color:#cbd5e1;text-decoration:none;font-size:0.9rem;display:flex;align-items:center;gap:0.5rem;">🧾 Depurador de Orçamentos</a>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("ASCII").lower()
    texto = re.sub(r"(\d)([a-z])", r"\1 \2", texto)  # "75g" -> "75 g"
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto)).strip()


def _radical(token: str) -> str:
    """Remove o plural simples para que 'canetas' e 'caneta' sejam o mesmo termo."""
    if len(token) > 4 and token.endswith(("oes", "aes")):
        return token[:-3] + "ao"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


@lru_cache(maxsize=100_000)
def _tokens_ordenados(texto: str) -> tuple[str, ...]:
    vistos: dict[str, None] = {}
    for token in _normalizar(texto).split():
        if len(token) > 1 and token not in STOP_WORDS:
            vistos.setdefault(_radical(token), None)
    return tuple(vistos)


def _tokens(texto: str) -> set[str]:
    return set(_tokens_ordenados(texto))


def _tem_numero(token: str) -> bool:
    return any(caractere.isdigit() for caractere in token)


def _perfil(descricao: str) -> dict[str, object]:
    """Separa a descrição em núcleo (o que o item é), especificações (a4, 75...) e embalagem (resma, caixa...)."""
    ordem = list(_tokens_ordenados(descricao))
    macios = [token for token in ordem if token in TERMOS_EMBALAGEM]
    especificos = [token for token in ordem if token not in macios and _tem_numero(token)]
    nucleo = [token for token in ordem if token not in macios and token not in especificos] or ordem
    return {"ordem": ordem, "macios": macios, "especificos": especificos, "nucleo": nucleo, "cabeca": nucleo[0] if nucleo else ""}


def _termo_principal(texto: str) -> str:
    """Retorna o termo que diz o que o item é, ignorando embalagem ('resma de papel' -> 'papel')."""
    return str(_perfil(texto)["cabeca"])


def _forca_termo(token: str, destino: set[str]) -> float:
    """1.0 = termo presente; menos que isso = equivalente ou variação do mesmo termo; 0 = ausente."""
    if token in destino:
        return 1.0
    if any(grupo <= destino for grupo in EQUIVALENCIAS.get(token, [])):
        return 0.85
    if len(token) >= 5 and not _tem_numero(token):
        for candidato in destino:
            menor = min(len(token), len(candidato))
            if menor >= 5 and not _tem_numero(candidato):
                comum = len(os.path.commonprefix([token, candidato]))
                if comum >= menor - 1:
                    return 0.7
    return 0.0


def _texto_pdf(texto: object) -> str:
    """Converte texto do catálogo para caracteres aceitos pela fonte padrão do PDF."""
    return unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode("ascii")


def _texto_pdf_quebravel(texto: object, tamanho_maximo: int = 45) -> str:
    """Insere espaços em tokens longos para que o FPDF consiga quebrar as linhas."""
    linhas = []
    for linha in _texto_pdf(texto).splitlines() or [""]:
        palavras = []
        for palavra in linha.split(" "):
            partes = [palavra[indice:indice + tamanho_maximo] for indice in range(0, len(palavra), tamanho_maximo)]
            palavras.append(" ".join(partes))
        linhas.append(" ".join(palavras))
    return "\n".join(linhas)


@st.cache_data(show_spinner=False)
def carregar_catalogo(caminho: str) -> list[dict[str, object]]:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        catalogo = json.load(arquivo)
    return [
        {"codigo": str(codigo), "descricao": descricao, "tokens": sorted(_tokens(descricao))}
        for descricao, codigo in catalogo.items()
    ]


def _itens_da_resposta(resultado: list[dict]) -> list[dict[str, str]]:
    return [
        {
            "codigo": str(item.get("codigoItem", "")),
            "descricao": item.get("descricaoItem", ""),
            "codigo_pdm": str(item.get("codigoPdm", "")),
            "descricao_pdm": item.get("nomePdm", ""),
        }
        for item in resultado
        if item.get("codigoItem") and item.get("descricaoItem")
    ]


def _consultar_catmat(parametros: dict[str, object]) -> tuple[list[dict[str, str]], bool]:
    """Consulta o catálogo paginando (até PAGINAS_POR_CONSULTA). Retorna (itens, houve_falha)."""
    itens: list[dict[str, str]] = []
    for pagina in range(1, PAGINAS_POR_CONSULTA + 1):
        try:
            resposta = requests.get(
                CATMAT_API_URL,
                params={**parametros, "pagina": pagina, "tamanhoPagina": TAMANHO_PAGINA, "statusItem": "true"},
                timeout=15,
            )
            if resposta.status_code != 200:
                return itens, True
            resultado = resposta.json().get("resultado", [])
        except (requests.RequestException, ValueError):
            return itens, True
        itens.extend(_itens_da_resposta(resultado))
        if len(resultado) < TAMANHO_PAGINA:
            break
    return itens, False


def _consultar_em_paralelo(lista_parametros: list[dict[str, object]]) -> tuple[list[dict[str, str]], int]:
    if not lista_parametros:
        return [], 0
    with ThreadPoolExecutor(max_workers=min(8, len(lista_parametros))) as executor:
        respostas = list(executor.map(_consultar_catmat, lista_parametros))
    itens = [item for lote, _ in respostas for item in lote]
    return itens, sum(1 for _, falhou in respostas if falhou)


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_catmat_api(consultas: tuple[str, ...]) -> tuple[list[dict[str, str]], int]:
    """Busca candidatos do catálogo público do Compras.gov por trecho de descrição."""
    itens, falhas = _consultar_em_paralelo([{"descricaoItem": consulta[:180]} for consulta in consultas])
    return list({item["codigo"]: item for item in itens}.values()), falhas


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_itens_catmat_por_pdm(codigos_pdm: tuple[str, ...]) -> tuple[list[dict[str, str]], int]:
    """Retorna itens CATMAT oficiais associados aos PDMs informados."""
    itens, falhas = _consultar_em_paralelo([{"codigoPdm": codigo} for codigo in codigos_pdm])
    return list({item["codigo"]: item for item in itens}.values()), falhas


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_unidade_fornecimento(codigo_pdm: str) -> str:
    """Retorna a primeira unidade de fornecimento ativa associada ao PDM informado."""
    try:
        resposta = requests.get(
            "https://dadosabertos.compras.gov.br/modulo-material/6_consultarMaterialUnidadeFornecimento",
            params={"pagina": 1, "tamanhoPagina": 100, "codigoPdm": codigo_pdm, "statusUnidadeFornecimentoPdm": "true"},
            timeout=15,
        )
        if resposta.status_code != 200:
            return ""
        unidades = resposta.json().get("resultado", [])
        if not unidades:
            return ""
        unidade = unidades[0]
        sigla = unidade.get("siglaUnidadeFornecimento", "")
        nome = unidade.get("nomeUnidadeFornecimento", "")
        return f"{sigla} - {nome}".strip(" -")
    except (requests.RequestException, ValueError):
        return ""


def calcular_similaridade(descricao: str, candidato: str, nome_pdm: str = "", preferidos: frozenset[str] = frozenset()) -> float:
    """Pontua de 0 a 100 o quanto o item do catálogo corresponde à descrição informada.

    O que pesa: o termo principal ("papel"), os demais termos do núcleo, as especificações
    (a4 casa com 210 x 297 mm) e o item do catálogo começar pelo termo principal. Embalagem
    ("resma") pesa pouco. Descrições longas de catálogo não são punidas por terem mais atributos.
    """
    perfil = _perfil(descricao)
    ordem_destino = list(_tokens_ordenados(f"{nome_pdm} {candidato}"))
    if not perfil["ordem"] or not ordem_destino:
        return 0.0
    destino = set(ordem_destino)
    cabeca = str(perfil["cabeca"])
    nucleo = list(perfil["nucleo"])

    pesos = [(token, 2.0 if token == cabeca else 1.0) for token in nucleo]
    pesos += [(token, 0.6) for token in perfil["especificos"]] + [(token, 0.1) for token in perfil["macios"]]
    forcas = {token: _forca_termo(token, destino) for token, _ in pesos}
    cobertura = sum(peso * forcas[token] for token, peso in pesos) / sum(peso for _, peso in pesos)

    forca_cabeca = forcas.get(cabeca, 0.0)
    comeco = ordem_destino[:3]
    bonus_inicio = 12 if any(_forca_termo(cabeca, {token}) >= 0.7 for token in comeco) else 0
    nucleo_completo = 8 if all(forcas[token] >= 0.7 for token in nucleo) else 0

    nome = _tokens_ordenados(re.split(r"[,;:(]", nome_pdm or candidato, maxsplit=1)[0])
    sequencia = SequenceMatcher(None, " ".join(nucleo), " ".join(nome[:6])).ratio()
    extras_no_nome = [token for token in nome if _forca_termo(token, set(perfil["ordem"])) == 0 and all(_forca_termo(t, {token}) == 0 for t in nucleo)]

    termos_preferidos = set(preferidos)
    for chave, preferencia in PREFERENCIAS:
        if chave <= set(perfil["ordem"]):
            termos_preferidos |= preferencia
    bonus_preferencia = min(20, 10 * len(termos_preferidos & destino))
    restritivos_ausentes = (destino - set(perfil["ordem"])) & TERMOS_RESTRITIVOS
    penalidade = min(36, len(restritivos_ausentes) * 18) + min(16, len(extras_no_nome) * 4)

    pontuacao = cobertura * 72 + bonus_inicio + nucleo_completo + sequencia * 8 + bonus_preferencia - penalidade
    if perfil["especificos"]:
        atendidas = sum(forcas[token] for token in perfil["especificos"]) / len(perfil["especificos"])
        pontuacao *= 0.8 + 0.2 * atendidas
    if not nucleo_completo:
        pontuacao *= 0.85
    if forca_cabeca == 0:
        pontuacao *= 0.35
    return round(max(0, min(100, pontuacao)), 1)


def melhores_do_catalogo(descricao: str, catalogo: list[dict[str, object]], limite: int = 40) -> list[dict[str, object]]:
    """Pré-seleciona entradas do catálogo local que compartilham termos do núcleo com a descrição."""
    perfil = _perfil(descricao)
    cabeca = str(perfil["cabeca"])
    candidatos = []
    for item in catalogo:
        destino = set(item["tokens"])
        pontos = sum((2.0 if token == cabeca else 1.0) * _forca_termo(token, destino) for token in perfil["nucleo"])
        if pontos:
            candidatos.append((pontos, item))
    candidatos.sort(key=lambda candidato: candidato[0], reverse=True)
    return [item for _, item in candidatos[:limite]]


def _gerar_consultas(descricao: str) -> list[str]:
    """Várias formas de perguntar ao catálogo: a API busca trecho exato, então uma frase longa quase nunca acha."""
    perfil = _perfil(descricao)
    nucleo, cabeca = list(perfil["nucleo"]), str(perfil["cabeca"])
    tokens_descricao = set(perfil["ordem"])
    consultas = [cabeca] if cabeca else []
    consultas += [f"{cabeca} {token}" for token in nucleo[1:5]]
    consultas += [token for token in nucleo if len(token) >= 4]
    for chave, adicionais in EXPANSOES_DE_BUSCA:
        if chave <= tokens_descricao:
            consultas.extend(adicionais)
    consultas.append(" ".join(nucleo))
    return list(dict.fromkeys(consulta for consulta in consultas if consulta))


def _pdms_candidatos(descricao: str, catalogo_pdm: list[dict[str, object]], limite: int = 5) -> list[dict[str, object]]:
    """Escolhe os PDMs (famílias do catálogo) mais próximos da descrição para buscar seus itens."""
    descricao_normalizada = _normalizar(descricao)
    tokens_descricao = set(descricao_normalizada.split())
    escolhidos = [
        {"codigo": fallback["codigo_pdm"], "preferidos": frozenset(fallback["termos_preferidos"]), "pontuacao": 100.0}
        for chave, fallback in FALLBACKS_GENERICOS.items()
        if set(chave.split()) <= tokens_descricao
    ]
    pontuados = [
        (calcular_similaridade(descricao, str(pdm["descricao"])), pdm)
        for pdm in melhores_do_catalogo(descricao, catalogo_pdm, limite=150)
    ]
    pontuados.sort(key=lambda par: par[0], reverse=True)
    escolhidos += [
        {"codigo": str(pdm["codigo"]), "preferidos": frozenset(), "pontuacao": pontuacao}
        for pontuacao, pdm in pontuados[:limite]
        if pontuacao >= 30
    ]
    return list({pdm["codigo"]: pdm for pdm in reversed(escolhidos)}.values())


def _opcoes_material(descricao: str, catalogo_pdm: list[dict[str, object]]) -> tuple[list[dict[str, object]], int]:
    candidatos, falhas = buscar_catmat_api(tuple(_gerar_consultas(descricao)))
    pdms = _pdms_candidatos(descricao, catalogo_pdm)
    preferidos_por_pdm = {pdm["codigo"]: pdm["preferidos"] for pdm in pdms}
    itens_pdm, falhas_pdm = buscar_itens_catmat_por_pdm(tuple(pdm["codigo"] for pdm in pdms))
    opcoes: dict[str, dict[str, object]] = {}
    for origem, lote in (("CATMAT específico", candidatos), ("CATMAT via PDM", itens_pdm)):
        for item in lote:
            codigo = str(item["codigo"])
            if codigo in opcoes:
                continue
            opcoes[codigo] = {
                "tipo": "Material",
                "codigo": codigo,
                "descricao_catalogo": str(item["descricao"]),
                "similaridade": calcular_similaridade(
                    descricao, str(item["descricao"]), str(item.get("descricao_pdm", "")),
                    preferidos_por_pdm.get(str(item.get("codigo_pdm", "")), frozenset()),
                ),
                "origem": origem,
                "codigo_pdm": str(item.get("codigo_pdm", "")),
                "descricao_pdm": str(item.get("descricao_pdm", "")),
            }
    return list(opcoes.values()), falhas + falhas_pdm


def _opcoes_servico(descricao: str, catalogo_servico: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "tipo": "Serviço",
            "codigo": str(item["codigo"]),
            "descricao_catalogo": str(item["descricao"]),
            "similaridade": calcular_similaridade(descricao, str(item["descricao"])),
            "origem": "CATSERV",
            "codigo_pdm": "",
            "descricao_pdm": "",
        }
        for item in melhores_do_catalogo(descricao, catalogo_servico)
    ]


def _resumo_alternativa(opcao: dict[str, object]) -> str:
    descricao = str(opcao["descricao_catalogo"])
    return f"{opcao['codigo']} ({opcao['similaridade']:.0f}%) {descricao[:90]}{'…' if len(descricao) > 90 else ''}"


def sugerir_codigo(descricao: str, catalogo_pdm: list[dict[str, object]], catalogo_servico: list[dict[str, object]], tipo: str) -> dict[str, object]:
    opcoes: list[dict[str, object]] = []
    falhas = 0
    if tipo in ("Automático", "Material"):
        material, falhas = _opcoes_material(descricao, catalogo_pdm)
        opcoes += material
    if tipo in ("Automático", "Serviço"):
        opcoes += _opcoes_servico(descricao, catalogo_servico)

    vazio = {"tipo": "-", "codigo": "-", "similaridade": 0.0, "origem": "-", "unidade_fornecimento": "", "codigo_pdm": "", "descricao_pdm": "", "alternativas": "", "falhas_api": falhas}
    if not opcoes:
        aviso = "Catálogo do Compras.gov indisponível no momento; tente novamente" if falhas else "Nenhuma correspondência encontrada"
        return {**vazio, "descricao_catalogo": aviso}
    opcoes.sort(key=lambda opcao: opcao["similaridade"], reverse=True)
    melhor = opcoes[0]
    if melhor["similaridade"] < LIMIAR_SIMILARIDADE:
        return {**vazio, "descricao_catalogo": "Descrição insuficiente para sugerir um código com segurança", "similaridade": melhor["similaridade"]}
    alternativas = [opcao for opcao in opcoes[1:4] if opcao["similaridade"] >= LIMIAR_SIMILARIDADE - 10]
    return {
        **melhor,
        "unidade_fornecimento": buscar_unidade_fornecimento(str(melhor["codigo_pdm"])) if melhor["codigo_pdm"] else "",
        "alternativas": "\n".join(_resumo_alternativa(opcao) for opcao in alternativas),
        "falhas_api": falhas,
    }


def gerar_excel(resultados: pd.DataFrame) -> bytes:
    saida = io.BytesIO()
    with pd.ExcelWriter(saida, engine="openpyxl") as escritor:
        resultados.to_excel(escritor, index=False, sheet_name="Correlação")
        planilha = escritor.book["Correlação"]
        cabecalho = PatternFill("solid", fgColor="001A4D")
        for celula in planilha[1]:
            celula.font = Font(color="FFFFFF", bold=True)
            celula.fill = cabecalho
            celula.alignment = Alignment(horizontal="center", vertical="center")
        for coluna in planilha.columns:
            indice = coluna[0].column
            maior = max(len(str(celula.value or "")) for celula in coluna)
            planilha.column_dimensions[get_column_letter(indice)].width = min(max(maior + 2, 14), 62)
        planilha.freeze_panes = "A2"
        planilha.auto_filter.ref = planilha.dimensions
    return saida.getvalue()


class RelatorioPDF(FPDF):
    def header(self) -> None:
        self.set_fill_color(0, 26, 77)
        self.rect(0, 0, 210, 22, "F")
        self.set_text_color(212, 175, 55)
        self.set_font("Helvetica", "B", 14)
        self.set_xy(12, 8)
        self.cell(0, 7, "CATMAT/CATSERV - Correlacao Automatica")
        self.ln(20)


def gerar_pdf(resultados: pd.DataFrame) -> bytes:
    pdf = RelatorioPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5, "Sugestoes calculadas a partir do catalogo publico do Compras.gov. Revise a descricao e o codigo antes de utilizar no processo.")
    pdf.ln(3)
    for indice, linha in resultados.iterrows():
        pdf.set_fill_color(235, 242, 252)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 7, _texto_pdf_quebravel(f"{indice + 1}. {linha['Descrição informada']}"), fill=True)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _texto_pdf_quebravel(f"{linha['Tipo']} {linha['Código']}  |  Similaridade: {linha['Similaridade (%)']}%"))
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5, _texto_pdf_quebravel(f"Sugestao: {linha['Descrição sugerida']}"))
        if linha.get("Código PDM", ""):
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, _texto_pdf_quebravel(f"PDM: {linha['Código PDM']} - {linha['Descrição PDM']}"))
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, _texto_pdf_quebravel(f"Unidade de fornecimento: {linha['Unidade de fornecimento']}"))
        if linha.get("Outras opções", ""):
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5, _texto_pdf_quebravel(f"Outras opcoes:\n{linha['Outras opções']}"))
        pdf.ln(3)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} - AtaCotada", ln=True)
    return bytes(pdf.output())


def ler_lista_enviada(arquivo: object) -> tuple[list[str], list[str]]:
    nome = getattr(arquivo, "name", "").lower()
    if nome.endswith(".csv"):
        dados = pd.read_csv(arquivo)
    else:
        dados = pd.read_excel(arquivo)
    colunas = [str(coluna) for coluna in dados.columns]
    return colunas, dados.astype(str).fillna("").to_dict("list")


st.markdown(
    """
    <div class="catalog-header">
        <div class="catalog-header-top">
            <div class="catalog-symbol">🔎</div>
            <div><h1>CATMAT/CATSERV Automático</h1><p>Encontre sugestões de classificação para materiais e serviços a partir das descrições do seu processo.</p></div>
            <span class="catalog-badge">CATÁLOGO COMPRAS.GOV</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

catalogo_pdm = carregar_catalogo(PDM_PATH)
catalogo_servico = carregar_catalogo(CATSERV_PATH)

st.markdown('<div class="input-panel"><h3>Lista de itens</h3><p>Digite ou cole uma descrição por linha. Você também pode importar uma planilha CSV ou Excel.</p></div>', unsafe_allow_html=True)
entrada_manual = st.text_area(
    "Descrições dos itens",
    placeholder="Ex: Papel sulfite A4 75 g/m², resma com 500 folhas\nManutenção preventiva de aparelhos de ar-condicionado\nCadeira ergonômica para escritório",
    height=190,
)

col_tipo, col_arquivo = st.columns([1, 2])
with col_tipo:
    tipo_busca = st.selectbox("Classificar como", ["Automático", "Material", "Serviço"])
with col_arquivo:
    arquivo_lista = st.file_uploader("Importar lista (CSV ou Excel)", type=["csv", "xlsx", "xls"])

itens_arquivo: list[str] = []
if arquivo_lista:
    try:
        colunas_arquivo, dados_arquivo = ler_lista_enviada(arquivo_lista)
        coluna_descricao = st.selectbox("Coluna com as descrições", colunas_arquivo)
        itens_arquivo = [valor.strip() for valor in dados_arquivo[coluna_descricao] if valor and valor.strip().lower() != "nan"]
        st.caption(f"{len(itens_arquivo)} item(ns) identificado(s) no arquivo.")
    except Exception as erro:
        st.error(f"Não foi possível ler o arquivo: {erro}")

if st.button("🔎 Encontrar códigos sugeridos", type="primary", use_container_width=True):
    itens_manuais = [linha.strip(" -•\t") for linha in entrada_manual.splitlines() if linha.strip()]
    itens = list(dict.fromkeys(itens_manuais + itens_arquivo))
    if not itens:
        st.warning("Informe ao menos uma descrição ou envie uma lista de itens.")
    else:
        with st.spinner(f"Analisando {len(itens)} item(ns) nos catálogos oficiais..."):
            resultados_brutos = []
            falhas_api = 0
            for item in itens:
                sugestao = sugerir_codigo(item, catalogo_pdm, catalogo_servico, tipo_busca)
                resultados_brutos.append(
                    {
                        "Descrição informada": item,
                        "Tipo": "CATMAT" if sugestao["tipo"] == "Material" else "CATSERV" if sugestao["tipo"] == "Serviço" else "-",
                        "Código": sugestao["codigo"],
                        "Descrição sugerida": sugestao["descricao_catalogo"],
                        "Similaridade (%)": sugestao["similaridade"],
                        "Unidade de fornecimento": sugestao["unidade_fornecimento"],
                        "Código PDM": sugestao["codigo_pdm"],
                        "Descrição PDM": sugestao["descricao_pdm"],
                        "Outras opções": sugestao["alternativas"],
                    }
                )
                falhas_api += int(sugestao["falhas_api"])
        st.session_state["catmat_catserv_resultados"] = resultados_brutos
        st.session_state["catmat_catserv_falhas_api"] = falhas_api

resultados_salvos = st.session_state.get("catmat_catserv_resultados")
if resultados_salvos:
    if st.session_state.get("catmat_catserv_falhas_api"):
        st.warning("Parte das consultas ao catálogo do Compras.gov falhou (instabilidade ou limite de acesso). Os resultados podem estar incompletos; execute novamente para conferir.")
    resultados = pd.DataFrame(resultados_salvos)
    alta = int((resultados["Similaridade (%)"] >= 70).sum())
    media = int(((resultados["Similaridade (%)"] >= 45) & (resultados["Similaridade (%)"] < 70)).sum())
    baixa = len(resultados) - alta - media
    st.markdown('<div class="result-panel"><h3>Resultado da correlação</h3><p>Use a similaridade como apoio à decisão e confira as especificações do item no catálogo antes de utilizar o código.</p></div>', unsafe_allow_html=True)
    metricas = st.columns(4)
    metricas[0].metric("Itens analisados", len(resultados))
    metricas[1].markdown(f'<span class="status-chip status-good">{alta} alta similaridade</span>', unsafe_allow_html=True)
    metricas[2].markdown(f'<span class="status-chip status-review">{media} para revisar</span>', unsafe_allow_html=True)
    metricas[3].markdown(f'<span class="status-chip status-low">{baixa} baixa similaridade</span>', unsafe_allow_html=True)
    st.dataframe(resultados, use_container_width=True, hide_index=True, column_config={"Similaridade (%)": st.column_config.NumberColumn(format="%.1f%%")})
    excel, pdf = st.columns(2)
    with excel:
        st.download_button("⬇️ Baixar correlação em Excel", gerar_excel(resultados), "correlacao_catmat_catserv.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    with pdf:
        st.download_button("⬇️ Baixar correlação em PDF", gerar_pdf(resultados), "correlacao_catmat_catserv.pdf", "application/pdf", use_container_width=True)