"""Interface da aba "Pesquisa em Lote" da página Notas Fiscais."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

import pandas as pd
import streamlit as st

from cotacao_rapida import MAX_PRECOS, MIN_PRECOS, TOLERANCIA
from fornecedores_nf import MAX_FORNECEDORES_POR_ITEM, montar_tabelas
from lista_itens import anexar_pedido, tem_quantidades, valor_total_orcamento
from lista_itens_ui import entrada_itens
from nf_lote import analisar_item, limitar_cache, pesquisar_em_lote, registros_das_linhas
from relatorio_nf_lote import (
    STATUS_TEXTO, URL_PORTAL_NFE, gerar_excel_fornecedores, gerar_excel_mapa, gerar_pdf_fornecedores, gerar_pdf_mapa, tabela_mapa_nf, tabela_notas,
)

MAX_ITENS = 40


def _moeda(valor: float | None) -> str:
    return "" if valor is None or valor != valor else f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _ler_lista(arquivo: object) -> tuple[list[str], dict[str, list[str]]]:
    nome = getattr(arquivo, "name", "").lower()
    dados = pd.read_csv(arquivo) if nome.endswith(".csv") else pd.read_excel(arquivo)
    return [str(c) for c in dados.columns], dados.astype(str).fillna("").to_dict("list")


def _texto_filtros(filtros: dict, n_arquivos: int, n_total: int) -> str:
    partes = []
    if filtros.get("nome_dest"):
        partes.append(f"destinatario contem '{filtros['nome_dest']}'")
    if filtros.get("uf_dest"):
        partes.append(f"UF destinatario = {filtros['uf_dest'].upper()}")
    if filtros.get("uf_emit"):
        partes.append(f"UF emitente = {filtros['uf_emit'].upper()}")
    if filtros.get("emitente"):
        partes.append(f"emitente contem '{filtros['emitente']}'")
    partes.append(f"{n_arquivos} de {n_total} arquivos mensais")
    return "; ".join(partes)


def renderizar_lote(obter_arquivos: Callable[[], dict[str, str]], baixar_csv: Callable[..., str], pasta_cache: str) -> None:
    """Desenha a aba. `obter_arquivos()` -> {id: nome}; `baixar_csv(id)` -> caminho do CSV local (com cache)."""
    st.markdown("### 🔍 Pesquisa de Notas Fiscais")
    st.caption(
        "Pesquise um ou vários itens de uma vez em todos os arquivos mensais de notas fiscais. Cada arquivo é lido uma só vez para todos os itens. "
        "O resultado é um mapa comparativo de preços (PDF e Excel) e um relatório dos fornecedores encontrados."
    )
    arquivos = obter_arquivos()
    nomes = dict(sorted(arquivos.items(), key=lambda par: par[1], reverse=True))  # mais recentes primeiro

    itens_pedidos = entrada_itens(
        "nf", rotulo="Item(ns) a pesquisar (um por linha, com a quantidade ao lado, se quiser)",
        placeholder="Ex:\nResma de papel A4 75 g - 50\n10 notebook 15 polegadas\nLuva de procedimento látex; 200 cx",
        ajuda="Descreva o item com as palavras e especificações que importam: todas serão exigidas na descrição da nota (A4 = 210 x 297 mm). "
              "A quantidade é opcional: com ela, o mapa traz o valor total de cada item e do orçamento.",
    )

    st.markdown("#### Filtros da pesquisa")
    selecionados = st.multiselect(
        "📂 Períodos (arquivos mensais)", options=list(nomes), default=list(nomes), format_func=lambda i: nomes[i], key="nf_lote_periodos",
        help="Por padrão, todos os arquivos disponíveis. Cada arquivo baixado fica em cache; a primeira pesquisa é a mais demorada.",
    )
    c1, c2 = st.columns(2)
    nome_dest = c1.text_input("Nome do destinatário", placeholder="Ex: ARSENAL, HOSPITAL NAVAL...", key="nf_lote_dest", help="Pesquisa parcial no nome do destinatário")
    emitente = c2.text_input("Razão social do emitente (fornecedor)", placeholder="Ex: PAPELARIA...", key="nf_lote_emit", help="Pesquisa parcial na razão social do emitente")
    c3, c4, c5 = st.columns(3)
    uf_dest = c3.text_input("UF do destinatário", max_chars=2, placeholder="Ex: RJ", key="nf_lote_uf_dest", help="Sigla do estado do destinatário (filtro exato)")
    uf_emit = c4.text_input("UF do emitente", max_chars=2, placeholder="Ex: SP", key="nf_lote_uf_emit", help="Sigla do estado do fornecedor (filtro exato)")
    max_por_item = c5.number_input("Máximo de notas por item", 100, 10000, 1500, 100, key="nf_lote_max", help="Limita os registros guardados por item (os mais recentes primeiro)")

    if st.button("🔎 Pesquisar notas fiscais", type="primary", use_container_width=True, key="nf_lote_buscar"):
        pedidos = list(itens_pedidos)
        itens = [i["descricao"] for i in pedidos]
        if not itens:
            st.warning("Informe ao menos um item.")
        elif not selecionados:
            st.warning("Selecione ao menos um período (arquivo).")
        else:
            if len(itens) > MAX_ITENS:
                st.warning(f"Limite de {MAX_ITENS} itens por pesquisa; os {len(itens) - MAX_ITENS} últimos foram ignorados.")
                itens, pedidos = itens[:MAX_ITENS], pedidos[:MAX_ITENS]
            filtros = {"nome_dest": nome_dest.strip(), "uf_dest": uf_dest.strip(), "uf_emit": uf_emit.strip(), "emitente": emitente.strip()}
            limitar_cache(pasta_cache, manter={f"{i}.csv" for i in selecionados})
            barra = st.progress(0.0, text="Baixando e lendo os arquivos (a primeira vez demora)…")
            inicio = datetime.now()

            def progresso(feitos: int, total: int, nome: str) -> None:
                barra.progress(feitos / total, text=f"{feitos}/{total} arquivos processados — último: {nome}")

            resposta = pesquisar_em_lote(itens, [(i, nomes[i]) for i in selecionados], baixar_csv, filtros, int(max_por_item), progresso, pasta_cache=pasta_cache)
            barra.progress(1.0, text=f"Concluído em {(datetime.now() - inicio).seconds} s")
            st.session_state["nf_lote"] = {
                "id": st.session_state.get("nf_lote", {}).get("id", 0) + 1, "descricoes": itens, "pedidos": pedidos, "linhas": resposta["linhas"],
                "arquivos": resposta["arquivos_ok"], "erros": resposta["erros"],
                "registros": [registros_das_linhas(df) if len(df) else [] for df in resposta["itens"]],
                "frames": resposta["itens"], "filtros": _texto_filtros(filtros, len(resposta["arquivos_ok"]), len(nomes)),
            }
            st.session_state.pop("nf_lote_fornecedores", None)

    dados = st.session_state.get("nf_lote")
    if dados:
        _mostrar_resultados(dados)


def _mostrar_resultados(dados: dict) -> None:
    for nome, erro in dados["erros"].items():
        st.warning(f"Não foi possível ler **{nome}**: {erro}. Tente novamente em alguns minutos (cota de downloads do Google Drive).")

    st.markdown("---")
    st.markdown("#### Resultado")
    col_a, col_b = st.columns([1, 2])
    remover = col_a.checkbox("🎯 Remover outliers e preços inexequíveis", value=True, key="nf_lote_outliers",
                             help="Remove preços muito diferentes dos demais (fora de 0,3x–3x a mediana e pelo método IQR).")
    col_b.caption(f"{dados['linhas']:,} linhas de notas analisadas em {len(dados['arquivos'])} arquivo(s). Filtros: {dados['filtros']}.".replace(",", "."))

    resultados = []
    for i, (descricao, registros) in enumerate(zip(dados["descricoes"], dados["registros"])):
        base = analisar_item(descricao, registros, remover)
        faixa = st.session_state.get(f"nf_faixa_{dados['id']}_{i}_{int(remover)}")
        resultado = analisar_item(descricao, registros, remover, tuple(faixa)) if faixa and base["limites"] and tuple(faixa) != base["limites"] else base
        resultados.append(anexar_pedido(resultado, dados["pedidos"][i]) if dados.get("pedidos") else resultado)

    ok = sum(1 for r in resultados if r["status"] == "ok")
    insuficientes = sum(1 for r in resultados if r["status"] == "insuficiente")
    m = st.columns(4)
    m[0].metric("Itens pesquisados", len(resultados))
    m[1].markdown(f'<span class="status-chip" style="color:#86efac">{ok} com {MIN_PRECOS}+ preços</span>', unsafe_allow_html=True)
    m[2].markdown(f'<span class="status-chip" style="color:#fcd34d">{insuficientes} com menos de {MIN_PRECOS}</span>', unsafe_allow_html=True)
    m[3].markdown(f'<span class="status-chip" style="color:#fca5a5">{len(resultados) - ok - insuficientes} sem preço</span>', unsafe_allow_html=True)

    mapa = tabela_mapa_nf(resultados)
    moeda = st.column_config.NumberColumn(format="R$ %.2f")
    configuracao = {c: moeda for c in mapa.columns if c.startswith("Preço") or c in ("Média unitária", "Mediana", "Mínimo", "Máximo", "Desvio padrão", "Valor total (média × qtd.)")}
    if tem_quantidades(resultados):
        st.metric("Valor total estimado do orçamento", f"R$ {valor_total_orcamento(resultados):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                  help="Soma de média unitária × quantidade dos itens com quantidade e preços. Itens sem quantidade ou sem preço não entram.")
    configuracao["CV (%)"] = st.column_config.NumberColumn(format="%.1f%%")
    st.dataframe(mapa, use_container_width=True, hide_index=True, column_config=configuracao)

    info = {"arquivos": dados["arquivos"], "linhas": dados["linhas"], "filtros": dados["filtros"]}
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    b1, b2 = st.columns(2)
    b1.download_button("📄 Baixar mapa comparativo (PDF)", gerar_pdf_mapa(resultados, info), f"NF_lote_{carimbo}.pdf", "application/pdf", use_container_width=True)
    b2.download_button("📊 Baixar mapa comparativo (Excel)", gerar_excel_mapa(resultados, info), f"NF_lote_{carimbo}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    _secao_notas(resultados)
    _secao_fornecedores(resultados, dados, info, carimbo)
    _detalhes(resultados, dados, remover)


def _secao_notas(resultados: list[dict]) -> None:
    """Relação das NF-e dos preços do mapa, para conferir/autenticar cada nota no Portal da NF-e."""
    notas = tabela_notas(resultados)
    with st.expander(f"🧾 Notas fiscais dos preços do mapa ({len(notas)}) — para autenticar no Portal da NF-e"):
        st.caption("Copie a chave de acesso (44 dígitos) no Portal da NF-e, resolva o captcha e confira emitente, data e valor. "
                   "Esta relação também está no PDF (última seção antes da justificativa) e na aba “NF-e para autenticação” do Excel.")
        st.link_button("🌐 Abrir o Portal da NF-e (Receita Federal)", URL_PORTAL_NFE)
        st.dataframe(notas, hide_index=True, use_container_width=True, column_config={"Valor unitário": st.column_config.NumberColumn(format="R$ %.2f")})


def _assinatura(resultados: list[dict]) -> int:
    return hash(tuple((r["descricao"], tuple((p["id_compra"], p["id_item"]) for p in r["precos"]), len(r["registros"])) for r in resultados))


def _secao_fornecedores(resultados: list[dict], dados: dict, info: dict, carimbo: str) -> None:
    st.markdown("---")
    st.markdown("#### 🏢 Fornecedores encontrados")
    c_escopo, c_max = st.columns([3, 1])
    escopo = c_escopo.radio(
        "Quais fornecedores considerar", ["todos", "mapa"], horizontal=True, key="nf_lote_escopo",
        format_func=lambda v: "Todos que venderam o item (escolhe os melhores)" if v == "todos" else "Só os dos preços do mapa (mais rápido)",
        help="Havendo mais fornecedores que o limite, vêm primeiro os que têm e-mail e telefone; depois situação ativa e mais notas.",
    )
    max_por_item = int(c_max.number_input("Fornecedores por item (máx.)", 1, 50, MAX_FORNECEDORES_POR_ITEM, 1, key="nf_lote_max_forn"))
    if st.button("📞 Gerar relatório de fornecedores", use_container_width=True, key="nf_lote_forn"):
        barra = st.progress(0.0, text="Consultando o cadastro dos fornecedores (OpenCNPJ)…")
        tabelas = montar_tabelas(resultados, escopo, max_por_item, lambda feitos, total: barra.progress(0.5, text=f"{feitos} fornecedores consultados…"))
        barra.empty()
        st.session_state["nf_lote_fornecedores"] = {"tabelas": tabelas, "assinatura": _assinatura(resultados), "escopo": escopo}
    forn = st.session_state.get("nf_lote_fornecedores")
    if not forn:
        return
    tabelas = forn["tabelas"]
    if tabelas["unica"].empty:
        st.info("Nenhum fornecedor para listar.")
        return
    if forn["assinatura"] != _assinatura(resultados):
        st.warning("Os filtros ou a seleção de preços mudaram depois de gerar este relatório. Gere novamente para atualizá-lo.")
    if tabelas["sem_consulta"]:
        st.caption(f"⚠️ {tabelas['sem_consulta']} fornecedor(es) sem dados cadastrais na API (aparecem com os dados da nota: razão social, UF e município).")
    st.caption(f"{len(tabelas['unica'])} fornecedor(es) distintos, até {tabelas['max_por_item']} por item, agrupados pelo que vendem "
               "(um fornecedor aparece em cada item que vende). Havendo mais candidatos, priorizados os que têm e-mail e telefone.")
    for descricao, grupo in tabelas["por_item"].groupby("Item que vende", sort=False):
        total = tabelas["totais"].get(descricao, len(grupo))
        with st.expander(f"Vendem: {descricao} — {len(grupo)}" + (f" de {total}" if total > len(grupo) else "") + " fornecedor(es)", expanded=len(tabelas["por_item"]) <= 15):
            st.dataframe(grupo.drop(columns=["Item que vende"]), hide_index=True, use_container_width=True,
                         column_config={c: st.column_config.NumberColumn(format="R$ %.2f") for c in ("Preço mínimo", "Preço médio", "Preço máximo")})
    f1, f2 = st.columns(2)
    f1.download_button("📄 Baixar fornecedores (PDF)", gerar_pdf_fornecedores(tabelas, info), f"fornecedores_NF_{carimbo}.pdf", "application/pdf", use_container_width=True, key="nf_lote_forn_pdf")
    f2.download_button("📊 Baixar fornecedores (Excel)", gerar_excel_fornecedores(tabelas), f"fornecedores_NF_{carimbo}.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="nf_lote_forn_xlsx")


def _detalhes(resultados: list[dict], dados: dict, remover: bool) -> None:
    st.markdown("---")
    st.markdown("#### Detalhes por item")
    st.caption("Ajuste a faixa de preço de cada item para refinar o mapa e os relatórios acima.")
    for i, r in enumerate(resultados):
        media = r["stats"]["media"] if r["stats"] else None
        titulo = f"{i + 1}. {r['descricao'][:80]} — {STATUS_TEXTO.get(r['status'], '')}" + (f" · média {_moeda(media)}" if media else "") + f" · {r['notas']} notas"
        with st.expander(titulo):
            if not r["registros"]:
                st.info("Nenhuma nota fiscal encontrada. Revise a descrição (todas as palavras são exigidas) ou os filtros.")
                continue
            if r["limites"] and r["limites"][0] < r["limites"][1]:
                st.slider("Faixa de preço unitário (R$)", float(r["limites"][0]), float(r["limites"][1]), (float(r["limites"][0]), float(r["limites"][1])),
                          step=0.01, format="R$ %.2f", key=f"nf_faixa_{dados['id']}_{i}_{int(remover)}")
            if r["stats"]:
                s = r["stats"]
                st.caption(f"Unidade: {r['unidade']} · universo: {r['universo']} itens de nota · outliers removidos: {r['outliers']} · mínimo {_moeda(s['min'])} · máximo {_moeda(s['max'])} · CV {s['cv']:.1f}% "
                           f"(até {MAX_PRECOS} preços a ±{TOLERANCIA * 100:.0f}% da média)")
                st.dataframe(pd.DataFrame([{"Data": str(p["data"])[:10], "Valor unitário": p["preco"], "Unid.": p["sigla"], "Quantidade": p["quantidade"], "Fornecedor": p["fornecedor"],
                                            "CNPJ": p["cnpj"], "UF": p["uf"], "Município": p["municipio"], "Destinatário": p["nome_uasg"], "UF dest.": p["uf_dest"],
                                            "Produto na nota": p["descricao"], "Chave de acesso": p["id_compra"]} for p in r["precos"]]),
                             hide_index=True, use_container_width=True, column_config={"Valor unitário": st.column_config.NumberColumn(format="R$ %.2f")})
            elif r["status"] == "sem_precos":
                st.info("Os preços encontrados não formaram um conjunto coerente (a até 30% da média). Tente ampliar a faixa de preço.")
            with st.popover("Ver todas as notas encontradas"):
                st.dataframe(dados["frames"][i].head(1000), hide_index=True, use_container_width=True)
