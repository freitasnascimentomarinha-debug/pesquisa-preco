"""Entrada de itens com quantidade e unidade (lista digitada ou planilha) e tabela de conferência, para as páginas de pesquisa."""

from __future__ import annotations

import io
import re

import pandas as pd
import streamlit as st

from lista_itens import detectar_coluna_estimativa, detectar_colunas, interpretar_lista, itens_do_dataframe, unir_repetidos

SEM_COLUNA = "(nenhuma)"
EXEMPLO = "Caneta esferográfica azul - 100\n50 resmas de papel A4\nParafuso sextavado 1/2 x 20 zincado; 200 un\nFita isolante 20m - 30"


def _ler_planilha(arquivo) -> pd.DataFrame:
    conteudo = io.BytesIO(arquivo.getvalue())
    return pd.read_csv(conteudo) if arquivo.name.lower().endswith(".csv") else pd.read_excel(conteudo)


def _coletar(prefixo: str, rotulo: str, placeholder: str, altura: int, ajuda: str | None, com_estimativa: bool) -> tuple[list[dict[str, object]], str]:
    """Caixa de texto + envio de planilha. Devolve (itens unidos e sem repetição, assinatura do que foi digitado/enviado)."""
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
    return itens, f"{abs(hash((texto, assinatura_arquivo)))}"


def entrada_itens(prefixo: str, rotulo: str = "Itens a pesquisar (um por linha, com a quantidade ao lado, se quiser)", placeholder: str = EXEMPLO,
                  altura: int = 170, ajuda: str | None = None, com_estimativa: bool = False) -> list[dict[str, object]]:
    """Caixa de texto + envio de planilha + tabela de conferência editável (coluna Usar, descrição, quantidade e unidade).
    Devolve os itens marcados em 'Usar': {descricao, quantidade, unidade, quantidade_informada, estimativa}. A quantidade é opcional.
    Com `com_estimativa`, a tabela ganha a coluna "Estimativa do preço (R$)": quanto o usuário acha que vale a unidade do item (opcional)."""
    itens, assinatura = _coletar(prefixo, rotulo, placeholder, altura, ajuda, com_estimativa)
    if not itens:
        return []
    tabela = pd.DataFrame([{"Usar": True, "Descrição": i["descricao"], "Qtd.": float(i["quantidade"]) if i["quantidade_informada"] else None, "Un.": i["unidade"],
                            **({"Estimativa": i.get("estimativa") or float("nan")} if com_estimativa else {})} for i in itens])
    # a tabela recomeça quando o texto ou a planilha mudam (a assinatura entra na chave do editor)
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


# ---------- lista com CATMAT à vista (Cotação Rápida): "Carregar" abre a tabela, "Cotar" só aparece depois ----------

def _chave_descricao(texto: str) -> str:
    return " ".join(str(texto).lower().split())


def _sugestoes(prefixo: str, catmat, descricao: str) -> list[dict[str, object]]:
    """Os 3 CATMAT mais próximos da descrição (guardados na sessão: só recalcula quando a descrição muda)."""
    import cotacao_direta  # import tardio: o módulo carrega a busca de CATMAT

    cache = st.session_state.setdefault(f"{prefixo}_catmat_cache", {})
    chave = _chave_descricao(descricao)
    if chave not in cache:
        cache[chave] = cotacao_direta.melhores_catmats(descricao, catmat)
    return cache[chave]


URL_ITEM_MATERIAL = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"


def _catmat_digitado(prefixo: str, catmat, descricao: str, codigo: str) -> dict[str, object] | None:
    """O CATMAT que o usuário digitou: procurado no catálogo local e, se não estiver lá (código novo ou inativo), no Compras.gov. Devolve código, descrição do catálogo,
    % de correspondência com a descrição do item e se o item está ativo. None se não existir em lugar nenhum."""
    import requests

    from catmat_busca import calcular_similaridade

    posicao = catmat.por_codigo.get(codigo)
    if posicao is not None:
        _, _, nome_pdm, descricao_catalogo = catmat.itens[posicao]
        ativo = True
    else:
        cache = st.session_state.setdefault(f"{prefixo}_catmat_api", {})
        if codigo not in cache:
            try:
                resposta = requests.get(URL_ITEM_MATERIAL, params={"codigoItem": codigo, "pagina": 1, "tamanhoPagina": 10}, timeout=12)
                registros = resposta.json().get("resultado", []) if resposta.status_code == 200 else []
            except (requests.RequestException, ValueError):
                registros = []
            cache[codigo] = registros[0] if registros else None
        registro = cache[codigo]
        if not registro:
            return None
        nome_pdm, descricao_catalogo, ativo = str(registro.get("nomePdm") or ""), str(registro.get("descricaoItem") or ""), bool(registro.get("statusItem", True))
    return {"codigo": codigo, "descricao": descricao_catalogo, "combinacao": float(calcular_similaridade(descricao, descricao_catalogo, nome_pdm)), "ativo": ativo}


def _linha_com_catmat(prefixo: str, catmat, item: dict[str, object], usar: bool, com_estimativa: bool, fixo: str | None = None) -> tuple[dict[str, object], str | None, str]:
    """(linha da tabela, CATMAT fixado pelo usuário ou None = automático, mensagem para mostrar sob a tabela). Com `fixo`, mostra o código digitado com a descrição do
    catálogo e a % de correspondência; se o código não existir, volta ao automático e avisa. O CATMAT e a % ficam logo depois da descrição, à vista."""
    import cotacao_direta

    limiar = cotacao_direta.LIMIAR_CATMAT
    nome = str(item["descricao"])
    qtd = float(item["quantidade"]) if item.get("quantidade_informada") else None
    estimativa = item.get("estimativa") or float("nan")  # vazio aparece em branco (e não "None")
    aviso = ""
    if fixo:
        escolhido = _catmat_digitado(prefixo, catmat, nome, fixo)
        if escolhido:
            situacao = "👆 informado por você" + ("" if escolhido["ativo"] else " (item INATIVO no catálogo)") + ("" if escolhido["combinacao"] >= limiar else f" (casamento abaixo de {limiar:.0f}%: confira se é o item certo)")
            linha = {"Usar": usar, "Descrição": nome, "CATMAT": fixo, "% casamento": round(escolhido["combinacao"], 1), "Descrição do CATMAT": escolhido["descricao"],
                     "Qtd.": qtd, "Un.": item["unidade"], **({"Estimativa": estimativa} if com_estimativa else {}), "Outras opções": "", "Situação": situacao}
            mensagem = f"{'✅' if escolhido['combinacao'] >= limiar else '⚠️'} **{nome}** — CATMAT {fixo}: {escolhido['descricao'][:140]} ({escolhido['combinacao']:.0f}% de correspondência com a sua descrição).{'' if escolhido['ativo'] else ' Atenção: item INATIVO no catálogo.'}"
            return linha, fixo, mensagem
        aviso = f"❌ CATMAT {fixo} não existe (nem no catálogo local nem no Compras.gov); voltou ao sugerido. "
    sugestoes = _sugestoes(prefixo, catmat, nome)
    melhor = sugestoes[0] if sugestoes else None
    entra = bool(melhor and melhor["combinacao"] >= limiar)
    linha = {"Usar": usar, "Descrição": nome, "CATMAT": melhor["codigo"] if melhor else "—", "% casamento": round(melhor["combinacao"], 1) if melhor else 0.0,
             "Descrição do CATMAT": melhor["descricao"] if melhor else "Nenhuma correspondência no catálogo", "Qtd.": qtd, "Un.": item["unidade"],
             **({"Estimativa": estimativa} if com_estimativa else {}),
             "Outras opções": "\n".join(f"{c['codigo']} ({c['combinacao']:.0f}%)" for c in sugestoes[1:] if c["combinacao"] >= limiar),
             "Situação": aviso + ("✅ bom casamento" if entra else f"⚠️ abaixo de {limiar:.0f}%: melhore a descrição ou digite o CATMAT")}
    if aviso:
        mensagem = f"{aviso}**{nome}** ficou com o sugerido: {linha['CATMAT']} ({linha['% casamento']:.0f}%)."
    elif melhor:
        mensagem = f"{'✅' if entra else '⚠️'} **{nome}** — CATMAT sugerido {melhor['codigo']}: {melhor['descricao'][:140]} ({melhor['combinacao']:.0f}% de correspondência)."
    else:
        mensagem = f"⚠️ **{nome}** — nenhuma correspondência no catálogo."
    return linha, None, mensagem


def _item_da_linha(linha) -> dict[str, object] | None:
    descricao = str(linha["Descrição"] or "").strip()
    if not descricao or descricao.lower() == "nan":
        return None
    quantidade = pd.to_numeric(linha["Qtd."], errors="coerce")
    informada = bool(quantidade == quantidade and quantidade > 0)
    estimativa = pd.to_numeric(linha["Estimativa"], errors="coerce") if "Estimativa" in linha.index else float("nan")
    return {"descricao": descricao, "quantidade": float(quantidade) if informada else 1.0, "unidade": str(linha["Un."] or "UN").strip().upper() or "UN",
            "quantidade_informada": informada, "estimativa": float(estimativa) if estimativa == estimativa and estimativa > 0 else None}


def entrada_itens_com_catmat(prefixo: str, catmat, rotulo: str = "Itens a pesquisar (um por linha, com a quantidade ao lado, se quiser)", placeholder: str = EXEMPLO,
                             altura: int = 170, ajuda: str | None = None, com_estimativa: bool = False) -> tuple[list[dict[str, object]], bool]:
    """Lista digitada/enviada + botão "Carregar" (não pesquisa preço: só monta a tabela de itens com o CATMAT mais próximo, a % de correspondência e a
    descrição do CATMAT). Na tabela dá para desmarcar itens, mexer na descrição (o CATMAT é casado de novo sozinho), quantidade, unidade e estimativa.
    Devolve (itens marcados em 'Usar', tabela carregada?). O botão de pesquisar deve aparecer só quando a tabela estiver carregada."""
    itens, assinatura = _coletar(prefixo, rotulo, placeholder, altura, ajuda, com_estimativa)
    chave_tabela, chave_versao, chave_assinatura = f"{prefixo}_catmat_tabela", f"{prefixo}_catmat_versao", f"{prefixo}_catmat_assinatura"
    if st.button("📥 Carregar", key=f"{prefixo}_carregar", help="Só monta a tabela de itens com o CATMAT mais próximo de cada um. Não pesquisa preços."):
        if not itens:
            st.warning("Digite ou importe ao menos um item.")
        else:
            with st.spinner("Procurando o CATMAT mais próximo de cada item…"):
                st.session_state[chave_tabela] = [_linha_com_catmat(prefixo, catmat, item, True, com_estimativa)[0] for item in itens]
            st.session_state[f"{prefixo}_catmat_fixos"] = [None] * len(itens)
            st.session_state[chave_versao] = st.session_state.get(chave_versao, 0) + 1
            st.session_state[chave_assinatura] = assinatura
            st.session_state[f"{prefixo}_catmat_mensagens"] = []
    linhas = st.session_state.get(chave_tabela)
    if not linhas:
        st.caption("Escreva a lista e clique em **Carregar** para ver o CATMAT de cada item e testar as descrições antes de pesquisar os preços.")
        return [], False
    if st.session_state.get(chave_assinatura) != assinatura:
        st.info("A lista (texto ou planilha) mudou depois do último carregamento: clique em **Carregar** de novo para atualizar a tabela.")
    st.caption("Confira o CATMAT de cada item. **Usar**: desmarque para deixar um item de fora. Mexeu na descrição? O CATMAT é casado de novo sozinho, sem pesquisar preço. "
               "Um número solto no fim da linha (“estandarte 1”) é lido como quantidade.")
    base = pd.DataFrame(linhas)
    editada = st.data_editor(
        base, hide_index=True, use_container_width=True, num_rows="fixed", key=f"{prefixo}_catmat_editor_{st.session_state.get(chave_versao, 0)}",
        disabled=["% casamento", "Descrição do CATMAT", "Outras opções", "Situação"],
        column_config={"Usar": st.column_config.CheckboxColumn("Usar", width="small", help="Desmarque para deixar este item de fora."),
                       "Descrição": st.column_config.TextColumn("Descrição do item (edite para melhorar)", width="large"),
                       "Qtd.": st.column_config.NumberColumn("Qtd.", min_value=0, width="small", help="Opcional: com a quantidade, o mapa calcula o valor total do orçamento."),
                       "Un.": st.column_config.TextColumn("Un.", width="small"),
                       "Estimativa": st.column_config.NumberColumn("Estimativa do preço (R$)", min_value=0.0, format="R$ %.2f", width="medium",
                                                                   help="Opcional: quanto você acha que vale 1 unidade do item. Ao cotar, o sistema confere se o CATMAT e os preços são compatíveis com ela."),
                       "CATMAT": st.column_config.TextColumn("CATMAT (pode digitar)", width="small", help="É o mais próximo da descrição. Para usar outro, digite o código do CATMAT aqui: a descrição e a % de casamento se atualizam. "
                                                                                                  "Apague para voltar ao sugerido."),
                       "% casamento": st.column_config.NumberColumn("% casamento", format="%.0f%%", width="small", help="Semelhança entre a sua descrição e a do catálogo."),
                       "Descrição do CATMAT": st.column_config.TextColumn("Descrição do item no CATMAT", width="large"),
                       "Outras opções": st.column_config.TextColumn("Outras opções (≥ 70%)", width="medium"), "Situação": st.column_config.TextColumn("Situação", width="medium")})
    fixos = st.session_state.get(f"{prefixo}_catmat_fixos") or [None] * len(base)
    descricao_mudou = [str(n).strip() != str(a).strip() for n, a in zip(editada["Descrição"], base["Descrição"])]
    catmat_mudou = [str(n).strip() != str(a).strip() for n, a in zip(editada["CATMAT"], base["CATMAT"])]
    if any(descricao_mudou) or any(catmat_mudou):  # descrição ou CATMAT editados: atualiza o CATMAT, a descrição do catálogo e a % (catálogo local, sem pesquisar preço)
        novas, novos_fixos, mensagens = [], [], []
        for posicao, (_, linha) in enumerate(editada.iterrows()):
            item = _item_da_linha(linha)
            if item is None:
                continue
            fixo = fixos[posicao] if posicao < len(fixos) else None
            if catmat_mudou[posicao]:  # digitou um código (só números) ou apagou o campo (volta ao sugerido)
                fixo = re.sub(r"\D", "", str(linha["CATMAT"])) or None
            usar = True if pd.isna(linha["Usar"]) else bool(linha["Usar"])
            nova, fixo_efetivo, mensagem = _linha_com_catmat(prefixo, catmat, item, usar, com_estimativa, fixo)
            novas.append(nova)
            novos_fixos.append(fixo_efetivo)
            if descricao_mudou[posicao] or catmat_mudou[posicao]:
                mensagens.append(mensagem)
        st.session_state[f"{prefixo}_catmat_mensagens"] = mensagens
        st.session_state[chave_tabela], st.session_state[f"{prefixo}_catmat_fixos"] = novas, novos_fixos
        st.session_state[chave_versao] = st.session_state.get(chave_versao, 0) + 1
        st.rerun()
    for mensagem in st.session_state.get(f"{prefixo}_catmat_mensagens", []):  # resultado da última edição, sempre à vista (as colunas da tabela podem exigir rolagem)
        (st.warning if mensagem.startswith(("⚠️", "❌")) else st.success)(mensagem.replace("$", "\\$"))
    saida = []
    for posicao, (_, linha) in enumerate(editada.iterrows()):
        usar = True if pd.isna(linha["Usar"]) else bool(linha["Usar"])
        item = _item_da_linha(linha)
        if item is not None and usar:
            item["catmat_fixo"] = fixos[posicao] if posicao < len(fixos) else None  # código que o usuário digitou (a cotação usa exatamente esse)
            saida.append(item)
    st.caption(f"{len(saida)} item(ns) no pedido" + (f" ({len(editada) - len(saida)} deixado(s) de fora)." if len(editada) > len(saida) else "."))
    return saida, True
