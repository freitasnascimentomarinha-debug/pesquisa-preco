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
recarregar_se_mudou('catmat_busca', 'cotacao_rapida', 'lista_itens', 'relatorio_cotacao_rapida', 'lista_itens_ui')  # evita módulo antigo em memória após deploy
from catmat_busca import CATMAT_PATH, CATSERV_PATH, carregar_catalogo, carregar_indice_catmat  # noqa: E402
from cotacao_rapida import TOLERANCIA_ESTIMATIVA, aplicar_estimativa, JANELA_DIAS, LIMIAR_CORRESPONDENCIA, LIMIAR_SERVICO, MAX_CATMAT, MAX_PRECOS, MIN_PRECOS, TOLERANCIA, cotar_item, resultado_vazio  # noqa: E402
from relatorio_cotacao_rapida import STATUS_TEXTO, gerar_excel, gerar_pdf, tabela_mapa  # noqa: E402
from lista_itens import anexar_pedido, tem_quantidades, valor_total_orcamento  # noqa: E402
from lista_itens_ui import entrada_itens_com_catmat  # noqa: E402


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
    st.page_link("pages/Cotação_Direta.py", label="Cotação Direta", icon="📨")
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
""", unsafe_allow_html=True)
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
        1. Para cada item, o sistema localiza **até {MAX_CATMAT} códigos CATMAT (materiais) ou CATSERV (serviços)** com **mais de {LIMIAR_CORRESPONDENCIA:.0f}%** (materiais) ou **{LIMIAR_SERVICO:.0f}%** (serviços) de correspondência que tenham preços praticados.
        2. Busca os preços das compras públicas dos **últimos {JANELA_DIAS} dias**, comparando apenas a **mesma unidade de fornecimento/medida**.
        3. **Remove outliers** (preços inexequíveis ou muito diferentes dos demais).
        4. Traz **até {MAX_PRECOS} preços** por item, todos a **até {TOLERANCIA * 100:.0f}%** (para mais ou para menos) da **média** dos preços listados, priorizando fornecedores diferentes.
        5. Itens com menos de {MIN_PRECOS} preços são sinalizados. O PDF traz, na primeira página, o **mapa comparativo** com a **média unitária** de cada item.

        Descreva o item com as características que importam (ex.: *resma de papel A4 75 g/m²*, *notebook 15 polegadas*). Em serviços, o preço depende do escopo (quantidade, área, jornada): confira se é compatível. Confira sempre o código e a unidade sugeridos.
        """
    )

catmat = carregar_indice_catmat(CATMAT_PATH)
catalogo_servico = carregar_catalogo(CATSERV_PATH)

st.markdown('<div class="input-panel"><h3>Lista de itens</h3><p>Digite ou cole um item por linha, com a quantidade ao lado se quiser (ex.: “caneta azul - 100”, “50 resmas de papel A4”), ou importe uma planilha (CSV ou Excel). Com quantidades, o mapa já traz o valor total de cada item e do orçamento.</p></div>', unsafe_allow_html=True)
itens_pedidos, lista_carregada = entrada_itens_com_catmat(
    "cr", catmat, rotulo="Descrições dos itens", altura=170, com_estimativa=True,
    placeholder="Ex:\nResma de papel A4 75 g/m² - 50\n10 notebook 15 polegadas 16 GB\nDetergente líquido neutro 5 litros; 30 un",
)
tipo_busca, priorizar_estimativa, cotar_clicado = "Automático", True, False
if lista_carregada:  # só depois de "Carregar" (que apenas monta a tabela com o CATMAT) aparecem as opções e o botão de cotar
    tipo_busca = st.selectbox(
        "Tipo de item",
        ["Automático", "Material", "Serviço"],
        help="Automático decide, para cada linha, se é material (CATMAT) ou serviço (CATSERV) pela descrição mais parecida. "
        "É um pouco mais lento; prefira escolher o tipo quando a lista for toda de um só tipo.",
    )

    priorizar_estimativa = st.checkbox(
        "Deixar a estimativa de preço orientar a escolha do CATMAT", value=True,
        help=f"Só vale para os itens com “Estimativa do preço”. Entre os CATMAT bem parecidos (60% ou mais), passam na frente os que praticam preço compatível (até {TOLERANCIA_ESTIMATIVA:.0%} de diferença) com a sua estimativa. "
             "Se nenhum pratica, o sistema mantém o mais parecido e avisa. Desmarque para usar só a semelhança do texto (a estimativa vira apenas um aviso).",
    )

    cotar_clicado = st.button("⚡ Cotar itens", type="primary", use_container_width=True)

if cotar_clicado:
    st.session_state["cotacao_rapida_geracao"] = st.session_state.get("cotacao_rapida_geracao", 0) + 1
    itens_lista = list(itens_pedidos)
    if not itens_lista:
        st.warning("Informe ao menos uma descrição ou envie uma lista de itens.")
    else:
        if len(itens_lista) > MAX_ITENS:
            st.warning(f"Limite de {MAX_ITENS} itens por cotação; os {len(itens_lista) - MAX_ITENS} últimos foram ignorados.")
            itens_lista = itens_lista[:MAX_ITENS]
        itens = [i["descricao"] for i in itens_lista]
        barra = st.progress(0, text="Iniciando…")
        resultados = []
        inicio = datetime.now()
        for posicao, (item, pedido) in enumerate(zip(itens, itens_lista), start=1):
            barra.progress((posicao - 1) / len(itens), text=f"Cotando {posicao}/{len(itens)}: {item[:60]}")
            try:
                resultados.append(anexar_pedido(cotar_item(item, catmat, catalogo_servico, tipo_busca, estimativa=pedido.get("estimativa"), priorizar=priorizar_estimativa), pedido))
            except Exception as erro:  # um item com problema não derruba a cotação inteira
                vazio = resultado_vazio(item, tipo_busca if tipo_busca != "Automático" else "Material")
                vazio["falha_api"] = True
                resultados.append(anexar_pedido(aplicar_estimativa(vazio, pedido.get("estimativa")), pedido))
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
    configuracao = {coluna: formato_moeda for coluna in mapa.columns if coluna.startswith("Preço") or coluna in ("Média unitária", "Mediana", "Mínimo", "Máximo", "Desvio padrão", "Valor total (média × qtd.)")}
    configuracao["CV (%)"] = st.column_config.NumberColumn(format="%.1f%%")
    configuracao["% casamento"] = st.column_config.NumberColumn(format="%.0f%%")
    configuracao["Estimativa (R$)"] = formato_moeda
    com_estimativa = [r for r in resultados if r.get("estimativa")]
    if com_estimativa:
        divergentes = [r for r in com_estimativa if r["validacao"] == "divergente"]
        outros = [r for r in com_estimativa if r["compativeis"]]
        st.markdown(f"**Conferência com a sua estimativa de preço** — {len(com_estimativa)} item(ns) com estimativa: "
                    f"{sum(1 for r in com_estimativa if r['validacao'] == 'coerente')} coerente(s), {len(divergentes)} divergente(s), {len(outros)} com sugestão de outro CATMAT mais próximo da estimativa.")
        for indice, r in enumerate(resultados):
            if not r.get("estimativa") or not (r["validacao"] != "coerente" or r["compativeis"] or r.get("escolha") in ("estimativa", "manual")):
                continue
            texto_aviso = f"**{r['descricao']}** — {r['texto_validacao']}".replace("$", "\\$")  # "$" solto vira fórmula no markdown
            (st.warning if r["validacao"] != "coerente" else st.info)(texto_aviso)
            if r["compativeis"] and r.get("tipo") != "Serviço":  # opção de trocar o CATMAT por um dos compatíveis em preço
                botoes = st.columns(len(r["compativeis"]))
                for coluna_botao, alternativa in zip(botoes, r["compativeis"]):
                    if coluna_botao.button(f"Usar o CATMAT {alternativa['codigo']} ({alternativa['correspondencia']:.0f}%)", key=f"cr_usar_{st.session_state.get('cotacao_rapida_geracao', 0)}_{indice}_{alternativa['codigo']}",
                                           help=f"Cota de novo só este item, com este código. {alternativa['perto']} de {alternativa['registros']} compras perto da estimativa (mediana {moeda(alternativa['mediana'])}). {alternativa['descricao'][:160]}".replace("$", "\\$")):
                        with st.spinner("Cotando com o CATMAT escolhido…"):
                            novo = cotar_item(r["descricao"], catmat, catalogo_servico, "Material", estimativa=r["estimativa"], forcar=[alternativa["codigo"]], priorizar=False)
                            resultados[indice] = anexar_pedido(novo, {"quantidade": r.get("quantidade_pedida") or 1.0, "quantidade_informada": r.get("quantidade_pedida") is not None,
                                                                      "unidade": r.get("unidade_pedida") or "UN"})
                        st.rerun()
    if tem_quantidades(resultados):
        com_total = sum(1 for r in resultados if r.get("quantidade_pedida") and r["stats"])
        st.metric("Valor total estimado do orçamento", moeda(valor_total_orcamento(resultados)),
                  help=f"Soma de média unitária × quantidade dos {com_total} item(ns) com quantidade e preços. Itens sem quantidade ou sem preço não entram.")
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
            if r.get("estimativa"):
                st.markdown(f"**Conferência com a sua estimativa ({moeda(r['estimativa'])} por unidade):** {r['texto_validacao']}".replace("$", "\\$"))
                if r["compativeis"]:
                    st.dataframe(pd.DataFrame([{"Código": a["codigo"], "Correspondência (%)": round(a["correspondencia"], 1), "Mediana dos preços": a["mediana"], "Compras perto da estimativa": a["perto"], "Registros": a["registros"],
                                                "Unidade": a["unidade"], "Descrição no catálogo": a["descricao"]} for a in r["compativeis"]]),
                                 hide_index=True, use_container_width=True, column_config={"Mediana dos preços": formato_moeda})
            if r["precos"]:
                s = r["stats"]
                st.caption(f"Unidade: {r['unidade']} · universo analisado: {r.get('universo', r['brutos'])} registros · outliers removidos: {r['outliers']} · mínimo {moeda(s['min'])} · máximo {moeda(s['max'])} · CV {s['cv']:.1f}%".replace("$", "\\$"))
                st.dataframe(
                    pd.DataFrame([{"Data": str(p["data"])[:10], "Valor unitário": p["preco"], "Quantidade": p["quantidade"], "Fornecedor": p["fornecedor"], "CNPJ": p["cnpj"], "Órgão": p["nome_uasg"], "UF": p["uf"], "UASG": p["uasg"], "Código": p["catmat"], "ID Compra": p["id_compra"]} for p in r["precos"]]),
                    hide_index=True, use_container_width=True, column_config={"Valor unitário": formato_moeda},
                )
                if r["status"] == "insuficiente":
                    st.warning(f"Menos de {MIN_PRECOS} preços: complemente com outras fontes (IN SEGES/ME nº 65/2021).")
            elif r.get("proximos"):
                st.info(f"Nenhum CATMAT/CATSERV com {r.get('limiar', LIMIAR_CORRESPONDENCIA):.0f}%+ e preços no período. Códigos mais próximos abaixo; descreva o item com mais detalhes.")
                st.dataframe(pd.DataFrame([{"Código": p["codigo"], "Correspondência (%)": round(p["correspondencia"], 1), "Descrição no catálogo": p["descricao"]} for p in r["proximos"]]), hide_index=True, use_container_width=True)
            else:
                st.info("Nenhum CATMAT/CATSERV correspondente com preços no período. Tente descrever o item de outra forma.")
