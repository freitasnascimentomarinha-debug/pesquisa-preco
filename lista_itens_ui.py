"""Entrada de itens com quantidade e unidade (lista digitada ou planilha) e tabela de conferência, para as páginas de pesquisa."""

from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from lista_itens import detectar_coluna_estimativa, detectar_colunas, interpretar_lista, itens_do_dataframe, unir_repetidos

SEM_COLUNA = "(nenhuma)"
EXEMPLO = "Caneta esferográfica azul - 100\n50 resmas de papel A4\nParafuso sextavado 1/2 x 20 zincado; 200 un\nFita isolante 20m - 30"


def _ler_planilha(arquivo) -> pd.DataFrame:
    conteudo = io.BytesIO(arquivo.getvalue())
    return pd.read_csv(conteudo) if arquivo.name.lower().endswith(".csv") else pd.read_excel(conteudo)


def entrada_itens(prefixo: str, rotulo: str = "Itens a pesquisar (um por linha, com a quantidade ao lado, se quiser)", placeholder: str = EXEMPLO,
                  altura: int = 170, ajuda: str | None = None, com_estimativa: bool = False) -> list[dict[str, object]]:
    """Caixa de texto + envio de planilha + tabela de conferência editável (coluna Usar, descrição, quantidade e unidade).
    Devolve os itens marcados em 'Usar': {descricao, quantidade, unidade, quantidade_informada, estimativa}. A quantidade é opcional.
    Com `com_estimativa`, a tabela ganha a coluna "Estimativa do preço (R$)": quanto o usuário acha que vale a unidade do item (opcional)."""
    texto = st.text_area(rotulo, key=f"{prefixo}_lista_texto", height=altura, placeholder=placeholder,
                         help=ajuda or "Aceita, por exemplo: “caneta azul - 50”, “50 resmas de papel A4”, “parafuso 1/2; 200 un”. A quantidade é opcional.")
    arquivo = st.file_uploader("Ou importe uma lista (CSV ou Excel)", type=["csv", "xlsx", "xls"], key=f"{prefixo}_lista_arquivo")
    itens_planilha: list[dict[str, object]] = []
    assinatura_arquivo = ""
    if arquivo is not None:
        try:
            dados = _ler_planilha(arquivo)
            colunas = [str(c) for c in dados.columns]
            dados.columns = colunas
            padrao_desc, padrao_qtd, padrao_un = detectar_colunas(colunas)
            with st.expander("Colunas da planilha (ajuste se o sistema errou)", expanded=False):
                c1, c2, c3, c4 = st.columns(4 if com_estimativa else 3)
                col_desc = c1.selectbox("Descrição", colunas, index=colunas.index(padrao_desc), key=f"{prefixo}_col_desc")
                opcoes = [SEM_COLUNA] + colunas
                col_qtd = c2.selectbox("Quantidade", opcoes, index=opcoes.index(padrao_qtd) if padrao_qtd in opcoes else 0, key=f"{prefixo}_col_qtd")
                col_un = c3.selectbox("Unidade", opcoes, index=opcoes.index(padrao_un) if padrao_un in opcoes else 0, key=f"{prefixo}_col_un")
                col_est = SEM_COLUNA
                if com_estimativa:
                    padrao_est = detectar_coluna_estimativa([c for c in colunas if c not in (col_desc, col_qtd, col_un)])
                    col_est = c4.selectbox("Estimativa do preço", opcoes, index=opcoes.index(padrao_est) if padrao_est in opcoes else 0, key=f"{prefixo}_col_est")
            itens_planilha = itens_do_dataframe(dados, col_desc, None if col_qtd == SEM_COLUNA else col_qtd, None if col_un == SEM_COLUNA else col_un, detectar=False,
                                                col_estimativa=None if col_est == SEM_COLUNA else col_est)
            assinatura_arquivo = f"{arquivo.name}|{arquivo.size}|{col_desc}|{col_qtd}|{col_un}|{col_est}"
        except Exception as erro:  # planilha ilegível: avisa e segue só com o texto
            st.error(f"Não consegui ler a planilha ({type(erro).__name__}): confira se é um .xlsx ou .csv válido.")

    itens = unir_repetidos(interpretar_lista(texto) + itens_planilha)
    if not itens:
        return []
    tabela = pd.DataFrame([{"Usar": True, "Descrição": i["descricao"], "Qtd.": float(i["quantidade"]) if i["quantidade_informada"] else None, "Un.": i["unidade"],
                            **({"Estimativa": i.get("estimativa")} if com_estimativa else {})} for i in itens])
    assinatura = abs(hash((texto, assinatura_arquivo)))  # a tabela recomeça quando o texto ou a planilha mudam
    st.caption("Confira o que o sistema entendeu. **Usar**: desmarque para deixar um item de fora. Dá para corrigir descrição, quantidade e unidade. "
               "Um número solto no fim da linha (“estandarte 1”) é lido como quantidade; se for medida do item, escreva com a unidade colada (“20m”, “9w”) ou corrija aqui.")
    editada = st.data_editor(
        tabela, hide_index=True, use_container_width=True, num_rows="fixed", key=f"{prefixo}_lista_tabela_{assinatura}",
        column_config={"Usar": st.column_config.CheckboxColumn("Usar", width="small", help="Desmarque para deixar este item de fora."),
                       "Descrição": st.column_config.TextColumn("Descrição do item (edite para melhorar)", width="large"),
                       "Qtd.": st.column_config.NumberColumn("Qtd.", min_value=0, width="small", help="Opcional: com a quantidade, o mapa calcula o valor total do orçamento."),
                       "Un.": st.column_config.TextColumn("Un.", width="small"),
                       "Estimativa": st.column_config.NumberColumn("Estimativa do preço (R$)", min_value=0.0, format="R$ %.2f", width="medium",
                                                                   help="Opcional: quanto você acha que vale 1 unidade do item. O sistema confere se o CATMAT e os preços praticados são compatíveis com ela "
                                                                        "e avisa se outro CATMAT parecido pratica preço mais próximo.")})
    saida = []
    for _, linha in editada.iterrows():
        descricao = str(linha["Descrição"] or "").strip()
        usar = True if pd.isna(linha["Usar"]) else bool(linha["Usar"])
        if not descricao or descricao.lower() == "nan" or not usar:
            continue
        quantidade = pd.to_numeric(linha["Qtd."], errors="coerce")
        informada = bool(quantidade == quantidade and quantidade > 0)
        estimativa = pd.to_numeric(linha["Estimativa"], errors="coerce") if com_estimativa else float("nan")
        saida.append({"descricao": descricao, "quantidade": float(quantidade) if informada else 1.0,
                      "unidade": str(linha["Un."] or "UN").strip().upper() or "UN", "quantidade_informada": informada,
                      "estimativa": float(estimativa) if estimativa == estimativa and estimativa > 0 else None})
    st.caption(f"{len(saida)} item(ns) no pedido" + (f" ({len(itens) - len(saida)} deixado(s) de fora)." if len(itens) > len(saida) else "."))
    return saida
