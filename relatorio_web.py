"""Relatório padrão (PDF e Excel) da pesquisa de preços na internet, no layout da Cotação Rápida.

Mapa comparativo na primeira página, uma página por item e a relação das páginas consultadas (endereço, data e hora do acesso).
"""

from __future__ import annotations

import io

import pandas as pd
from fpdf import FPDF

import relatorio_cotacao_rapida as base
from cotacao_rapida import MIN_PRECOS, TOLERANCIA
from relatorio_cotacao_rapida import (
    AZUL_CARTAO, DOURADO, JUSTIFICATIVA_COTACAO, LARGURA, STATUS_TEXTO, _cabecalho_tabela, _cartoes, _quebrar, _seguro, _truncar, moeda,
)
from relatorio_nf_lote import _formatar_planilhas
from web_precos import PRECOS_POR_ITEM_PADRAO

STATUS_TEXTO["sem_paginas"] = "Sem paginas com preco"
TITULO_PDF = "Pesquisa de Precos na Internet - Mapa Comparativo de Precos"
COLUNAS_FONTES = [("Item", 9), ("Descricao pesquisada", 40), ("Loja / site", 42), ("Acesso em", 26), ("Preco", 22), ("Origem do preco", 44), ("Endereco da pagina", 98)]


def metodologia(info: dict) -> str:
    return (
        "Metodologia da Pesquisa de Precos na Internet\n\n"
        f"1. Para cada descricao informada foram feitas buscas na internet ({info.get('motores', 'DuckDuckGo')}) e acessadas as paginas de lojas "
        "encontradas. De cada pagina foi extraido o preco do produto anunciado, nesta ordem de confianca: oferta do produto nos dados estruturados "
        "da pagina (schema.org), metadados e, por ultimo, leitura do texto. Parcelas e precos riscados nao sao considerados; ofertas sem estoque sao ignoradas.\n\n"
        "2. Foram descartados precos inexequiveis ou extremos (abaixo de 30% ou acima de 300% da mediana) e os valores atipicos (outliers) "
        "pelo metodo do intervalo interquartil (IQR).\n\n"
        f"3. Foram selecionados ate {info.get('max_precos', PRECOS_POR_ITEM_PADRAO)} precos por item, priorizando lojas distintas, de modo que cada preco listado nao se afaste mais que "
        f"{TOLERANCIA * 100:.0f}% (para mais ou para menos) da media dos precos listados. Itens com menos de {MIN_PRECOS} precos sao sinalizados e devem ser "
        "complementados por outras fontes (IN SEGES/ME nº 65/2021, art. 5º).\n\n"
        "4. O preco de pagina de loja e o preco de venda ao publico na data e hora do acesso, para a unidade ou embalagem anunciada, e pode variar a qualquer momento. "
        "A descricao do anuncio nao foi conferida automaticamente com o objeto pretendido: o requisitante deve abrir o endereco indicado, verificar marca, "
        "quantidade por embalagem, frete e condicoes, e anexar a captura da pagina ao processo."
    )


def _pagina_item_web(pdf: FPDF, numero: int, r: dict) -> None:
    pdf.add_page()
    pdf.set_y(35)
    pdf.set_fill_color(*AZUL_CARTAO)
    pdf.set_text_color(*DOURADO)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(LARGURA, 6, f"  ITEM {numero} (INTERNET) - {STATUS_TEXTO.get(r['status'], '').upper()}", 0, 1, "L", True)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    for linha in _quebrar(pdf, r["descricao"], LARGURA - 4, 3):
        pdf.cell(LARGURA, 5, "  " + linha, 0, 1, "L", True)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(70, 70, 70)
    pdf.cell(0, 5, _seguro(f"{r['paginas']} paginas com preco, {r['lojas']} lojas."), ln=True)
    pdf.ln(1)
    if not r["precos"]:
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(150, 30, 30)
        texto = ("Nenhuma pagina com preco foi encontrada na internet para este item." if r["status"] == "sem_paginas"
                 else "Os precos encontrados nao formaram um conjunto coerente (a ate 30% da media) apos a remocao de outliers.")
        pdf.multi_cell(LARGURA, 5, _seguro(texto), new_x="LMARGIN", new_y="NEXT")
        return
    s = r["stats"]
    _cartoes(pdf, [("MINIMO", f"R$ {moeda(s['min'])}"), ("MEDIA UNITARIA", f"R$ {moeda(s['media'])}"), ("MEDIANA", f"R$ {moeda(s['mediana'])}"),
                   ("MAXIMO", f"R$ {moeda(s['max'])}"), ("DESVIO PADRAO", f"R$ {moeda(s['desvio'])}"), ("CV", f"{s['cv']:.2f}%".replace(".", ","))], pdf.get_y())
    colunas = [("Loja / site", 42), ("Acesso em", 26), ("Preco", 22), ("Origem do preco", 50), ("Titulo da pagina", 141)]
    _cabecalho_tabela(pdf, colunas)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(51, 51, 51)
    for indice, p in enumerate(r["precos"]):
        valores = [p["dominio"], p["data_coleta"], f"R$ {moeda(p['preco'])}", p["origem_preco"], p["titulo"]]
        pdf.set_fill_color(245, 248, 255)
        for (_, largura), valor in zip(colunas, valores):
            pdf.cell(largura, 6, _truncar(pdf, valor, largura - 2), 1, 0, "C", indice % 2 == 1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(70, 70, 70)
    validos = r["faixa_validos"]
    notas = [
        f"Paginas com preco analisadas: {r['universo']}; outliers/precos inexequiveis removidos: {r['outliers']}"
        + (f" (faixa valida: R$ {moeda(validos[0])} a R$ {moeda(validos[1])})." if validos else "."),
        f"Os {len(r['precos'])} precos listados ficam a ate {TOLERANCIA * 100:.0f}% da media (faixa de R$ {moeda(s['media'] * (1 - TOLERANCIA))} a R$ {moeda(s['media'] * (1 + TOLERANCIA))}).",
        "Precos de pagina de loja: confira o anuncio (marca, embalagem, frete) pelo endereco indicado na relacao de paginas consultadas.",
    ]
    if r["status"] == "insuficiente":
        notas.append(f"ATENCAO: menos de {MIN_PRECOS} precos - complementar com outras fontes (IN 65/2021).")
    for nota in notas:
        pdf.multi_cell(LARGURA, 4, _seguro(nota), new_x="LMARGIN", new_y="NEXT")


def tabela_fontes(resultados: list[dict]) -> pd.DataFrame:
    """Páginas dos preços listados no mapa, com endereço e data/hora do acesso."""
    linhas = []
    for numero, r in enumerate(resultados, start=1):
        for p in r["precos"]:
            linhas.append({"Item": numero, "Descrição pesquisada": r["descricao"], "Loja / site": p["dominio"], "Acesso em": p["data_coleta"], "Preço": p["preco"],
                           "Origem do preço": p["origem_preco"], "Título da página": p["titulo"], "Endereço da página": p["url"]})
    return pd.DataFrame(linhas, columns=["Item", "Descrição pesquisada", "Loja / site", "Acesso em", "Preço", "Origem do preço", "Título da página", "Endereço da página"])


def _anexo_fontes(resultados: list[dict]):
    def cabecalho_pagina(pdf: FPDF) -> None:
        pdf.set_y(35)
        pdf.set_fill_color(*AZUL_CARTAO)
        pdf.set_text_color(*DOURADO)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(LARGURA, 6, "  PAGINAS CONSULTADAS - endereco e data/hora do acesso de cada preco do mapa", 0, 1, "L", True)
        pdf.ln(1)
        _cabecalho_tabela(pdf, COLUNAS_FONTES)

    def anexo(pdf: FPDF) -> None:
        fontes = tabela_fontes(resultados)
        pdf.add_page()
        cabecalho_pagina(pdf)
        for numero, (_, linha) in enumerate(fontes.iterrows()):
            if pdf.get_y() + 6 > pdf.h - 14:
                pdf.add_page()
                cabecalho_pagina(pdf)
            pdf.set_font("Helvetica", "", 6.3)
            pdf.set_text_color(51, 51, 51)
            valores = [str(linha["Item"]), linha["Descrição pesquisada"], linha["Loja / site"], linha["Acesso em"], f"R$ {moeda(linha['Preço'])}", linha["Origem do preço"]]
            pdf.set_fill_color(245, 248, 255)
            for (_, largura), valor in zip(COLUNAS_FONTES[:-1], valores):
                pdf.cell(largura, 6, _truncar(pdf, valor, largura - 2), 1, 0, "C", numero % 2 == 1)
            largura = COLUNAS_FONTES[-1][1]
            pdf.set_text_color(20, 70, 190)
            pdf.cell(largura, 6, _truncar(pdf, linha["Endereço da página"], largura - 2), 1, 1, "L", numero % 2 == 1, link=linha["Endereço da página"])
        if fontes.empty:
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(150, 30, 30)
            pdf.cell(0, 6, "Nenhuma pagina listada: nenhum item atingiu precos validos.", ln=True)

    return anexo


def _anexo_prints(resultados: list[dict], prints: dict):
    """Uma página por print: item, loja, preço, endereço e data/hora; a imagem leva o rodapé com a data/hora da captura."""
    import io as _io

    def anexo(pdf: FPDF) -> None:
        numero = 0
        for indice, r in enumerate(resultados, start=1):
            for p in r["precos"]:
                captura = prints.get(p["url"])
                if not captura or not captura.get("imagem"):
                    continue
                numero += 1
                pdf.add_page()
                pdf.set_y(35)
                pdf.set_fill_color(*AZUL_CARTAO)
                pdf.set_text_color(*DOURADO)
                pdf.set_font("Helvetica", "B", 8)
                pdf.cell(LARGURA, 6, f"  PRINT {numero} - ITEM {indice} - {_truncar(pdf, p['dominio'], 80)} - R$ {moeda(p['preco'])}", 0, 1, "L", True)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 9)
                for linha in _quebrar(pdf, r["descricao"], LARGURA - 4, 2):
                    pdf.cell(LARGURA, 5, "  " + linha, 0, 1, "L", True)
                pdf.set_font("Helvetica", "", 6.5)
                pdf.set_text_color(20, 70, 190)
                pdf.cell(LARGURA, 5, _seguro(p["url"])[:170], 0, 1, "L", link=p["url"])
                pdf.set_text_color(70, 70, 70)
                pdf.cell(0, 4, _seguro(f"Captura da pagina em {captura['capturado_em']} (data e hora do acesso)."), ln=True)
                pdf.ln(1)
                altura_max = pdf.h - pdf.get_y() - 14
                from PIL import Image
                largura_img, altura_img = Image.open(_io.BytesIO(captura["imagem"])).size
                altura = min(altura_max, LARGURA * altura_img / largura_img)
                largura = altura * largura_img / altura_img
                pdf.image(_io.BytesIO(captura["imagem"]), x=(pdf.w - largura) / 2, y=pdf.get_y(), w=largura, h=altura)
        if numero == 0:
            return

    return anexo


def _anexos(resultados: list[dict], info: dict):
    fontes = _anexo_fontes(resultados)
    prints = info.get("prints") or {}

    def ambos(pdf: FPDF) -> None:
        fontes(pdf)
        if prints:
            _anexo_prints(resultados, prints)(pdf)

    return ambos


def gerar_pdf_mapa(resultados: list[dict], info: dict) -> bytes:
    return base.gerar_pdf(
        resultados,
        titulo=TITULO_PDF,
        pagina_item=_pagina_item_web,
        textos=(JUSTIFICATIVA_COTACAO, metodologia(info)),
        anexos=_anexos(resultados, info),
        argumentos_mapa={
            "max_precos": info.get("max_precos", PRECOS_POR_ITEM_PADRAO),
            "rotulo_col3": "Paginas / lojas",
            "linhas_col3": lambda r: [f"{r['paginas']} paginas", f"{r['lojas']} lojas"] if r["paginas"] else ["-"],
            "fonte": "Fonte: paginas de lojas na internet (preco de venda no momento do acesso), outliers e precos inexequiveis removidos. "
                     "Detalhamento de cada item e enderecos das paginas nas paginas seguintes.",
        },
    )


def tabela_mapa_web(resultados: list[dict], max_precos: int = PRECOS_POR_ITEM_PADRAO) -> pd.DataFrame:
    linhas = []
    for numero, r in enumerate(resultados, start=1):
        precos = [p["preco"] for p in r["precos"]]
        s = r["stats"]
        linha = {"Item": numero, "Descrição pesquisada": r["descricao"], "Páginas com preço": r["paginas"], "Lojas": r["lojas"]}
        for n in range(max_precos):
            linha[f"Preço {n + 1}"] = precos[n] if n < len(precos) else None
        linha.update({
            "Média unitária": s["media"] if s else None, "Mediana": s["mediana"] if s else None, "Mínimo": s["min"] if s else None,
            "Máximo": s["max"] if s else None, "Desvio padrão": s["desvio"] if s else None, "CV (%)": s["cv"] if s else None,
            "Nº de preços": len(precos), "Situação": STATUS_TEXTO.get(r["status"], ""),
        })
        linhas.append(linha)
    return pd.DataFrame(linhas)


def gerar_excel_mapa(resultados: list[dict], info: dict) -> bytes:
    todas = []
    for numero, r in enumerate(resultados, start=1):
        usados = {p["url"] or p["dominio"] for p in r["precos"]}
        for p in r["registros"]:
            todas.append({"Item": numero, "Descrição pesquisada": r["descricao"], "Usado no mapa": "Sim" if (p["url"] or p["dominio"]) in usados else "Não",
                          "Loja / site": p["dominio"], "Acesso em": p["data_coleta"], "Preço": p["preco"], "Origem do preço": p["origem_preco"],
                          "Confiança": p["confianca"], "Título da página": p["titulo"], "Endereço da página": p["url"]})
    parametros = pd.DataFrame([
        ("Mecanismos de busca", info.get("motores", "DuckDuckGo")), ("Itens pesquisados", len(resultados)),
        ("Máx. de preços por item", info.get("max_precos", PRECOS_POR_ITEM_PADRAO)), ("Tolerância sobre a média", f"{TOLERANCIA * 100:.0f}%"),
        ("Remoção de outliers", "Sim (0,3x a 3x a mediana e IQR)"), ("Gerado em", info.get("gerado_em", "")),
    ], columns=["Parâmetro", "Valor"])
    saida = io.BytesIO()
    with pd.ExcelWriter(saida, engine="openpyxl") as escritor:
        tabela_mapa_web(resultados, info.get("max_precos", PRECOS_POR_ITEM_PADRAO)).to_excel(escritor, sheet_name="Mapa", index=False)
        tabela_fontes(resultados).to_excel(escritor, sheet_name="Páginas consultadas", index=False)
        pd.DataFrame(todas).to_excel(escritor, sheet_name="Todas as ofertas", index=False)
        parametros.to_excel(escritor, sheet_name="Parâmetros", index=False)
        _formatar_planilhas(escritor, ("Média unitária", "Mediana", "Mínimo", "Máximo", "Desvio padrão"))
    return saida.getvalue()
