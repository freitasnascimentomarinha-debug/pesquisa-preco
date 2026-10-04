"""Cotação Rápida: cotação de vários itens de uma vez, com mapa comparativo de preços em PDF."""

from __future__ import annotations

import base64
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Cotação Rápida",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")
sys.path.insert(0, BASE_DIR)  # permite importar catmat_busca.py (raiz do projeto)
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('catmat_busca', 'cotacao_rapida', 'relatorio_cotacao_rapida')  # evita módulo antigo em memória após deploy
from catmat_busca import CATMAT_PATH, CATSERV_PATH, carregar_catalogo, carregar_indice_catmat  # noqa: E402
from cotacao_rapida import JANELA_DIAS, LIMIAR_CORRESPONDENCIA, MAX_CATMAT, MAX_PRECOS, MIN_PRECOS, TOLERANCIA, cotar_item, resultado_vazio  # noqa: E402
from relatorio_cotacao_rapida import STATUS_TEXTO, gerar_excel, gerar_pdf, tabela_mapa  # noqa: E402


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
    st.page_link("pages/CATMAT_CATSERV_Automatico.py", label="CATMAT/CATSERV", icon="🔎")
    st.page_link("pages/Cotação_Rápida.py", label="Cotação Rápida", icon="⚡")
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
    st.page_link("pages/Calculo_IPCA.py", label="Cálculo IPCA", icon="📊")
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



MAX_ITENS = 50


def ler_lista_enviada(arquivo: object) -> tuple[list[str], dict[str, list[str]]]:
    nome = getattr(arquivo, "name", "").lower()
    dados = pd.read_csv(arquivo) if nome.endswith(".csv") else pd.read_excel(arquivo)
    return [str(coluna) for coluna in dados.columns], dados.astype(str).fillna("").to_dict("list")


def moeda(valor: float | None) -> str:
    return "" if valor is None or valor != valor else f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


st.markdown(
    """
    <div class="catalog-header">
        <div class="catalog-header-top">
            <div class="catalog-symbol">⚡</div>
            <div><h1>Cotação Rápida</h1><p>Cote vários itens de uma vez (materiais e serviços): o sistema acha o CATMAT/CATSERV, busca os preços praticados e monta o mapa comparativo em PDF.</p></div>
            <span class="catalog-badge">PREÇOS PRATICADOS · COMPRAS.GOV</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Como funciona", expanded=False):
    st.markdown(
        f"""
        1. Para cada item, o sistema localiza **até {MAX_CATMAT} códigos CATMAT (materiais) ou CATSERV (serviços)** com **mais de {LIMIAR_CORRESPONDENCIA:.0f}%** de correspondência que tenham preços praticados.
        2. Busca os preços das compras públicas dos **últimos {JANELA_DIAS} dias**, comparando apenas a **mesma unidade de fornecimento/medida**.
        3. **Remove outliers** (preços inexequíveis ou muito diferentes dos demais).
        4. Traz **até {MAX_PRECOS} preços** por item, todos a **até {TOLERANCIA * 100:.0f}%** (para mais ou para menos) da **média** dos preços listados, priorizando fornecedores diferentes.
        5. Itens com menos de {MIN_PRECOS} preços são sinalizados. O PDF traz, na primeira página, o **mapa comparativo** com a **média unitária** de cada item.

        Descreva o item com as características que importam (ex.: *resma de papel A4 75 g/m²*, *notebook 15 polegadas*). Em serviços, o preço depende do escopo (quantidade, área, jornada): confira se é compatível. Confira sempre o código e a unidade sugeridos.
        """
    )

catmat = carregar_indice_catmat(CATMAT_PATH)
catalogo_servico = carregar_catalogo(CATSERV_PATH)

st.markdown('<div class="input-panel"><h3>Lista de itens</h3><p>Digite ou cole uma descrição por linha, ou importe uma planilha (CSV ou Excel).</p></div>', unsafe_allow_html=True)
entrada_manual = st.text_area(
    "Descrições dos itens",
    placeholder="Ex:\nResma de papel A4 75 g/m²\nNotebook 15 polegadas 16 GB\nDetergente líquido neutro 5 litros",
    height=170,
)
tipo_busca = st.selectbox(
    "Tipo de item",
    ["Material", "Serviço", "Automático"],
    help="Automático decide, para cada linha, se é material (CATMAT) ou serviço (CATSERV) pela descrição mais parecida. "
    "É um pouco mais lento; prefira escolher o tipo quando a lista for toda de um só tipo.",
)
limiar = st.slider(
    "Correspondência mínima com o catálogo (%)",
    50, 100, int(LIMIAR_CORRESPONDENCIA), 5,
    help=f"Padrão {LIMIAR_CORRESPONDENCIA:.0f}%. Nomes de serviços no CATSERV são enxutos (ex.: “PISO EM GERAL”); se um serviço não for encontrado, "
    "reduza um pouco e confira com atenção os códigos sugeridos no relatório.",
)
arquivo_lista = st.file_uploader("Importar lista (CSV ou Excel)", type=["csv", "xlsx", "xls"])
itens_arquivo: list[str] = []
if arquivo_lista:
    try:
        colunas_arquivo, dados_arquivo = ler_lista_enviada(arquivo_lista)
        coluna_descricao = st.selectbox("Coluna com as descrições", colunas_arquivo)
        itens_arquivo = [valor.strip() for valor in dados_arquivo[coluna_descricao] if valor and valor.strip().lower() != "nan"]
        st.caption(f"{len(itens_arquivo)} item(ns) identificado(s) no arquivo.")
    except Exception as erro:  # leitura de planilha: qualquer problema vira aviso ao usuário
        st.error(f"Não foi possível ler o arquivo: {erro}")

if st.button("⚡ Cotar itens", type="primary", use_container_width=True):
    itens_manuais = [linha.strip(" -•\t") for linha in entrada_manual.splitlines() if linha.strip()]
    itens = list(dict.fromkeys(itens_manuais + itens_arquivo))
    if not itens:
        st.warning("Informe ao menos uma descrição ou envie uma lista de itens.")
    else:
        if len(itens) > MAX_ITENS:
            st.warning(f"Limite de {MAX_ITENS} itens por cotação; os {len(itens) - MAX_ITENS} últimos foram ignorados.")
            itens = itens[:MAX_ITENS]
        barra = st.progress(0, text="Iniciando…")
        resultados = []
        inicio = datetime.now()
        for posicao, item in enumerate(itens, start=1):
            barra.progress((posicao - 1) / len(itens), text=f"Cotando {posicao}/{len(itens)}: {item[:60]}")
            try:
                resultados.append(cotar_item(item, catmat, catalogo_servico, tipo_busca, float(limiar)))
            except Exception as erro:  # um item com problema não derruba a cotação inteira
                vazio = resultado_vazio(item, tipo_busca if tipo_busca != "Automático" else "Material", float(limiar))
                vazio["falha_api"] = True
                resultados.append(vazio)
                st.warning(f"Não foi possível cotar “{item[:60]}”: {erro}")
        barra.progress(1.0, text=f"Concluído em {(datetime.now() - inicio).seconds} s")
        st.session_state["cotacao_rapida"] = resultados

resultados = st.session_state.get("cotacao_rapida")
if resultados:
    ok = sum(1 for r in resultados if r["status"] == "ok")
    insuficientes = sum(1 for r in resultados if r["status"] == "insuficiente")
    sem = len(resultados) - ok - insuficientes
    st.markdown('<div class="result-panel"><h3>Mapa comparativo de preços</h3><p>Preços unitários praticados (últimos 12 meses), sem outliers, a até 30% da média de cada item.</p></div>', unsafe_allow_html=True)
    metricas = st.columns(4)
    metricas[0].metric("Itens pesquisados", len(resultados))
    metricas[1].markdown(f'<span class="status-chip status-good">{ok} com {MIN_PRECOS}+ preços</span>', unsafe_allow_html=True)
    metricas[2].markdown(f'<span class="status-chip status-review">{insuficientes} com menos de {MIN_PRECOS}</span>', unsafe_allow_html=True)
    metricas[3].markdown(f'<span class="status-chip status-low">{sem} sem preço</span>', unsafe_allow_html=True)
    if any(r["falha_api"] for r in resultados):
        st.warning("Parte das consultas ao Compras.gov falhou (instabilidade ou limite de acesso). Alguns itens podem estar incompletos; cote novamente para conferir.")

    mapa = tabela_mapa(resultados)
    formato_moeda = st.column_config.NumberColumn(format="R$ %.2f")
    configuracao = {coluna: formato_moeda for coluna in mapa.columns if coluna.startswith("Preço") or coluna in ("Média unitária", "Mediana", "Mínimo", "Máximo", "Desvio padrão")}
    configuracao["CV (%)"] = st.column_config.NumberColumn(format="%.1f%%")
    st.dataframe(mapa, use_container_width=True, hide_index=True, column_config=configuracao)

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    col_pdf, col_excel = st.columns(2)
    with col_pdf:
        st.download_button("📄 Baixar relatório em PDF", gerar_pdf(resultados), f"cotacao_rapida_{carimbo}.pdf", "application/pdf", use_container_width=True)
    with col_excel:
        st.download_button("📊 Baixar planilha em Excel", gerar_excel(resultados), f"cotacao_rapida_{carimbo}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    st.markdown("### Detalhes por item")
    for numero, r in enumerate(resultados, start=1):
        media = r["stats"]["media"] if r["stats"] else None
        titulo = f"{numero}. {r['descricao'][:80]} — {STATUS_TEXTO.get(r['status'], '')}" + (f" · média {moeda(media)}" if media else "")
        with st.expander(titulo):
            if r["catmats"]:
                st.markdown(f"**{'CATSERV' if r.get('tipo') == 'Serviço' else 'CATMAT'} correspondentes**")
                st.dataframe(pd.DataFrame([{"Código": k["codigo"], "Correspondência (%)": round(k["correspondencia"], 1), "Registros": k["registros"], "Descrição no catálogo": k["descricao"]} for k in r["catmats"]]), hide_index=True, use_container_width=True)
            if r["precos"]:
                s = r["stats"]
                st.caption(f"Unidade: {r['unidade']} · universo analisado: {r.get('universo', r['brutos'])} registros · outliers removidos: {r['outliers']} · mínimo {moeda(s['min'])} · máximo {moeda(s['max'])} · CV {s['cv']:.1f}%")
                st.dataframe(
                    pd.DataFrame([{"Data": str(p["data"])[:10], "Valor unitário": p["preco"], "Quantidade": p["quantidade"], "Fornecedor": p["fornecedor"], "CNPJ": p["cnpj"], "Órgão": p["nome_uasg"], "UF": p["uf"], "UASG": p["uasg"], "Código": p["catmat"], "ID Compra": p["id_compra"]} for p in r["precos"]]),
                    hide_index=True, use_container_width=True, column_config={"Valor unitário": formato_moeda},
                )
                if r["status"] == "insuficiente":
                    st.warning(f"Menos de {MIN_PRECOS} preços: complemente com outras fontes (IN SEGES/ME nº 65/2021).")
            elif r.get("proximos"):
                st.info(f"Nenhum CATMAT/CATSERV com {r.get('limiar', LIMIAR_CORRESPONDENCIA):.0f}%+ e preços no período. Códigos mais próximos abaixo; descreva o item com mais detalhes ou reduza a correspondência mínima.")
                st.dataframe(pd.DataFrame([{"Código": p["codigo"], "Correspondência (%)": round(p["correspondencia"], 1), "Descrição no catálogo": p["descricao"]} for p in r["proximos"]]), hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum CATMAT/CATSERV correspondente com preços no período. Tente descrever o item de outra forma.")
