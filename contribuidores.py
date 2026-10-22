"""Contribuidores do AtaCotada e geração do "card" em PDF de cada um (baixado ao clicar no card, na página Suporte ao sistema).

Para incluir alguém, acrescente um item em CONTRIBUIDORES. O visual do card (gerar_card_pdf) é provisório e será ajustado ao modelo oficial.
"""

from __future__ import annotations

from fpdf import FPDF

CONTRIBUIDORES = [
    {"nome": "2°SG-PL Freitas", "papel": "Idealização e desenvolvimento"},
]

AZUL, DOURADO, BRANCO = (0, 26, 77), (212, 175, 55), (255, 255, 255)


def nome_do_arquivo(contribuidor: dict[str, str]) -> str:
    base = "".join(c if c.isalnum() else "_" for c in contribuidor["nome"])
    return f"Card_AtaCotada_{base}.pdf"


def gerar_card_pdf(contribuidor: dict[str, str]) -> bytes:
    """PDF de uma página no formato de cartão (100 x 62 mm, paisagem) com nome e contribuição."""
    pdf = FPDF(orientation="L", unit="mm", format=(62, 100))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_fill_color(*AZUL)
    pdf.rect(0, 0, 100, 62, "F")
    pdf.set_draw_color(*DOURADO)
    pdf.set_line_width(0.8)
    pdf.rect(2.5, 2.5, 95, 57, "D")
    pdf.set_line_width(0.25)
    pdf.rect(4, 4, 92, 54, "D")

    pdf.set_text_color(*DOURADO)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_xy(8, 9)
    pdf.cell(84, 5, "MARINHA DO BRASIL", align="C")
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_xy(8, 15)
    pdf.cell(84, 9, "AtaCotada", align="C")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_xy(8, 24)
    pdf.cell(84, 4, "CONTRIBUIDOR DO PROJETO", align="C")
    pdf.line(30, 30, 70, 30)

    pdf.set_text_color(*BRANCO)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_xy(8, 36)
    pdf.cell(84, 8, contribuidor["nome"], align="C")
    pdf.set_text_color(*DOURADO)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_xy(8, 46)
    pdf.cell(84, 4, contribuidor.get("papel", ""), align="C")
    pdf.set_text_color(160, 174, 192)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_xy(8, 53)
    pdf.cell(84, 3, "Centro de Operações do Abastecimento - AtaCotada V2.0", align="C")
    return bytes(pdf.output())
