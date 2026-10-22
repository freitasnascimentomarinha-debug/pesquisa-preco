"""Contribuidores do AtaCotada e geração do "card" em PDF de cada um (baixado ao clicar no card, na página Suporte ao sistema).

Para incluir alguém, acrescente um item em CONTRIBUIDORES. O card em PDF (gerar_card_pdf) segue o modelo com foto redonda; para incluir foto, ponha o PNG em contribuidores_fotos/.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

CONTRIBUIDORES = [
    {
        "nome": "2°SG-PL Freitas", "papel": "Idealização, desenvolvimento, manutenção e suporte",
        # dados do card em PDF: título (nome de guerra), posto, e-mail e foto (PNG redondo em contribuidores_fotos/)
        "card": {"titulo": "FREITAS", "posto": "2°SG-PL", "email": "freitas.nascimento@marinha.mil.br", "foto": "freitas.png"},
    },
]

PASTA_FOTOS = Path(__file__).resolve().parent / "contribuidores_fotos"
FUNDO, DOURADO, BRANCO, CINZA = (11, 31, 58), (212, 175, 55), (255, 255, 255), (190, 200, 215)


def nome_do_arquivo(contribuidor: dict) -> str:
    base = "".join(c if c.isalnum() else "_" for c in contribuidor["nome"])
    return f"Card_AtaCotada_{base}.pdf"


def gerar_card_pdf(contribuidor: dict) -> bytes:
    """PDF de uma página no formato de card vertical (72 x 92 mm): foto com anel dourado, nome, posto e e-mail."""
    dados = contribuidor.get("card", {})
    pdf = FPDF(orientation="P", unit="mm", format=(72, 92))
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_fill_color(*FUNDO)
    pdf.rect(0, 0, 72, 92, "F")

    foto = PASTA_FOTOS / dados.get("foto", "")
    if dados.get("foto") and foto.exists():
        pdf.set_fill_color(*DOURADO)
        pdf.ellipse(13, 7, 46, 46, "F")  # anel dourado
        pdf.image(str(foto), x=14.3, y=8.3, w=43.4, h=43.4)
        topo_texto = 59
    else:
        topo_texto = 28

    pdf.set_text_color(*BRANCO)
    pdf.set_font("Helvetica", "B", 27)
    pdf.set_xy(0, topo_texto)
    pdf.cell(72, 12, dados.get("titulo", contribuidor["nome"]).upper(), align="C")
    if dados.get("posto"):
        pdf.set_text_color(*DOURADO)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_char_spacing(0.6)
        pdf.set_xy(0, topo_texto + 14)
        pdf.cell(72, 6, dados["posto"], align="C")
        pdf.set_char_spacing(0)
    if dados.get("email"):
        pdf.set_text_color(*CINZA)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_xy(0, topo_texto + 22)
        pdf.cell(72, 5, dados["email"], align="C")
    pdf.set_draw_color(*DOURADO)
    pdf.set_line_width(0.5)
    pdf.line(16, topo_texto + 31, 56, topo_texto + 31)
    return bytes(pdf.output())
