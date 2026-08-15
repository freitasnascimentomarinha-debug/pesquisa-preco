"""Sugestão automática de códigos CATMAT e CATSERV a partir de descrições."""

from __future__ import annotations

import io
import json
import os
import re
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher

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
CATMAT_PATH = os.path.join(CATALOGO_DIR, "catalogo_pdm.json")
CATSERV_PATH = os.path.join(CATALOGO_DIR, "catalogo_servicos.json")
CATMAT_API_URL = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"
STOP_WORDS = {"a", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "para", "por", "sem", "um", "uma"}


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
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
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


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto.lower())).strip()


def _tokens(texto: str) -> set[str]:
    return {token for token in _normalizar(texto).split() if len(token) > 1 and token not in STOP_WORDS}


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


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_catmat_api(consulta: str) -> list[dict[str, str]]:
    """Busca candidatos do catálogo público do Compras.gov por descrição."""
    try:
        resposta = requests.get(
            CATMAT_API_URL,
            params={"pagina": 50, "tipo": "descricaoItem", "codigo": consulta[:180]},
            timeout=15,
        )
        if resposta.status_code != 200:
            return []
        return [
            {"codigo": str(item.get("codigoItem", "")), "descricao": item.get("descricaoItem", "")}
            for item in resposta.json().get("resultado", [])
            if item.get("codigoItem") and item.get("descricaoItem")
        ]
    except requests.RequestException:
        return []


def calcular_similaridade(descricao: str, candidato: str) -> float:
    origem = _tokens(descricao)
    destino = _tokens(candidato)
    if not origem or not destino:
        return 0.0
    em_comum = origem & destino
    cobertura = len(em_comum) / len(origem)
    precisao = len(em_comum) / len(destino)
    sequencia = SequenceMatcher(None, _normalizar(descricao), _normalizar(candidato)).ratio()
    return round(min(100, (cobertura * 62 + precisao * 18 + sequencia * 20) * 100), 1)


def melhores_do_catalogo(descricao: str, catalogo: list[dict[str, object]], limite: int = 40) -> list[dict[str, object]]:
    tokens_origem = _tokens(descricao)
    candidatos = []
    for item in catalogo:
        tokens_destino = set(item["tokens"])
        em_comum = len(tokens_origem & tokens_destino)
        if em_comum:
            candidatos.append((em_comum / len(tokens_origem), item))
    candidatos.sort(key=lambda candidato: candidato[0], reverse=True)
    return [item for _, item in candidatos[:limite]]


def sugerir_codigo(descricao: str, catalogo_material: list[dict[str, object]], catalogo_servico: list[dict[str, object]], tipo: str) -> dict[str, object]:
    opcoes: list[dict[str, object]] = []
    tipos_consulta = [tipo] if tipo != "Automático" else ["Material", "Serviço"]
    for tipo_atual in tipos_consulta:
        catalogo = catalogo_material if tipo_atual == "Material" else catalogo_servico
        candidatos = melhores_do_catalogo(descricao, catalogo)
        if tipo_atual == "Material":
            for item_api in buscar_catmat_api(descricao):
                candidatos.append({**item_api, "tokens": sorted(_tokens(item_api["descricao"]))})
        vistos = set()
        for candidato in candidatos:
            codigo = str(candidato["codigo"])
            if codigo in vistos:
                continue
            vistos.add(codigo)
            opcoes.append(
                {
                    "tipo": tipo_atual,
                    "codigo": codigo,
                    "descricao_catalogo": str(candidato["descricao"]),
                    "similaridade": calcular_similaridade(descricao, str(candidato["descricao"])),
                }
            )
    if not opcoes:
        return {"tipo": "-", "codigo": "-", "descricao_catalogo": "Nenhuma correspondência encontrada", "similaridade": 0.0}
    return max(opcoes, key=lambda opcao: opcao["similaridade"])


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

catalogo_material = carregar_catalogo(CATMAT_PATH)
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
            for item in itens:
                sugestao = sugerir_codigo(item, catalogo_material, catalogo_servico, tipo_busca)
                resultados_brutos.append(
                    {
                        "Descrição informada": item,
                        "Tipo": "CATMAT" if sugestao["tipo"] == "Material" else "CATSERV" if sugestao["tipo"] == "Serviço" else "-",
                        "Código": sugestao["codigo"],
                        "Descrição sugerida": sugestao["descricao_catalogo"],
                        "Similaridade (%)": sugestao["similaridade"],
                    }
                )
        st.session_state["catmat_catserv_resultados"] = resultados_brutos

resultados_salvos = st.session_state.get("catmat_catserv_resultados")
if resultados_salvos:
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