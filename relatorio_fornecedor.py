"""Ficha do fornecedor em PDF (resumo da página Consulta CNPJ)."""

from __future__ import annotations

import datetime as _dt

from fpdf import FPDF

AZUL, DOURADO, CINZA = (0, 26, 77), (212, 175, 55), (90, 90, 90)


def _t(valor: object, limite: int = 0) -> str:
    """Texto compatível com a fonte padrão do PDF (Latin-1)."""
    texto = str(valor if valor not in (None, "") else "—").replace("—", "-").replace("–", "-").replace("•", "-").replace("→", "->")
    texto = " ".join(texto.split())
    if limite and len(texto) > limite:
        texto = texto[: limite - 1] + "…"
    return texto.encode("latin-1", "replace").decode("latin-1")


def gerar_ficha_pdf(cnpj_formatado: str, campos: list[tuple[str, str]], resumo: list[tuple[str, str]],
                    contratos: list[tuple[str, str, str, str]], adesoes: list[tuple[str, str, str, str]]) -> bytes:
    """PDF A4: identificação, resumo de registros, últimos contratos/compras e atas abertas para adesão.
    `contratos`: (título, órgão, vigência/data, valor). `adesoes`: (ata, unidade, vigência, itens)."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(True, margin=15)
    pdf.add_page()
    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_xy(12, 7)
    pdf.cell(0, 8, "AtaCotada - Ficha do fornecedor")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(12, 16)
    pdf.cell(0, 6, _t(f"CNPJ {cnpj_formatado}  |  gerada em {_dt.datetime.now():%d/%m/%Y %H:%M}"))
    pdf.set_y(34)

    def titulo(texto: str) -> None:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*AZUL)
        pdf.cell(0, 7, _t(texto), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(*DOURADO)
        pdf.line(pdf.l_margin, pdf.get_y(), 198, pdf.get_y())
        pdf.ln(1.5)
        pdf.set_text_color(30, 30, 30)

    titulo("Identificação")
    for rotulo, valor in campos:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 5.2, _t(rotulo + ":"))
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(0, 5.2, _t(valor, 220), new_x="LMARGIN", new_y="NEXT")

    titulo("Resumo dos registros encontrados")
    for rotulo, valor in resumo:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(70, 5.2, _t(rotulo + ":"))
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5.2, _t(valor), new_x="LMARGIN", new_y="NEXT")

    def tabela(cabecalho: tuple[str, ...], linhas: list[tuple[str, ...]], larguras: tuple[int, ...]) -> None:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*AZUL)
        pdf.set_text_color(255, 255, 255)
        for h, w in zip(cabecalho, larguras):
            pdf.cell(w, 6, _t(h), border=0, fill=True)
        pdf.ln()
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        for i, linha in enumerate(linhas):
            pdf.set_fill_color(240, 243, 250) if i % 2 else pdf.set_fill_color(255, 255, 255)
            for valor, w in zip(linha, larguras):
                pdf.cell(w, 5.5, _t(valor, int(w * 0.62)), fill=True)
            pdf.ln()

    if contratos:
        titulo(f"Contratos e compras mais recentes (até {len(contratos)})")
        tabela(("Registro", "Órgão", "Vigência / data", "Valor"), contratos, (50, 66, 42, 34))
    if adesoes:
        titulo(f"Atas abertas para adesão (até {len(adesoes)})")
        tabela(("ARP", "Unidade gerenciadora", "Vigência", "Itens"), adesoes, (30, 88, 54, 20))

    pdf.set_y(-14)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(*CINZA)
    pdf.cell(0, 5, "Dados de fontes publicas (OpenCNPJ, BrasilAPI, PNCP, Compras.gov.br). Gerado pelo AtaCotada.", align="C")
    return bytes(pdf.output())
