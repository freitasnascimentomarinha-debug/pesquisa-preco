"""Documentos oficiais em PDF e Word no padrão gráfico da Marinha (SGM-105, que remete a forma gráfica ao MaTDoc).

O texto chega em Markdown simples (o que os modelos e a IA produzem) e sai com:
- timbre: Armas Nacionais (2,0 x 2,0 cm), "MARINHA DO BRASIL" e o nome da OM, em negrito (MaTDoc 1.4.1 e 1.4.2);
- local e data por extenso, à direita (MaTDoc 1.4.5);
- título centralizado em negrito; NUP/processo, quando informado;
- letra Carlito/Calibri 12, A4, margens 3,0 cm (esq.), 1,5 cm (dir.), 2,0 cm (sup. e inf.) (MaTDoc 1.2.2 a 1.2.4);
- itens, subitens, alíneas a) e subalíneas I) com os recuos do MaTDoc; texto justificado;
- tabelas de verdade (bordas, cabeçalho em negrito, repetido em cada página);
- uma ou mais assinaturas (nome, posto/graduação e cargo), três linhas abaixo do texto; várias assinaturas do mais antigo
  para o mais moderno, da esquerda para a direita e de cima para baixo (MaTDoc 1.11);
- paginação "- n de N -" no rodapé, só quando houver mais de uma página (MaTDoc 1.14), e NUP à direita (MaTDoc 1.6).

DFD, TR, ETP, mapa e memória de cálculo não são tipos de documento administrativo da SGM-105 (1.3): seguem o cap. 1
do MaTDoc no que couber, como peças do processo.
"""

from __future__ import annotations

import io
import os
import re
import unicodedata
from datetime import date

PASTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_documentos")
ARMAS = os.path.join(PASTA, "armas_nacionais.png")
FONTES = {estilo: os.path.join(PASTA, "fontes", f"Carlito-{nome}.ttf")
          for estilo, nome in (("", "Regular"), ("B", "Bold"), ("I", "Italic"), ("BI", "BoldItalic"))}
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
RODAPES_DESCARTADOS = re.compile(r"documento gerado (pelo|por)|gerado por atacotada|ferramenta de apoio\.?$", re.I)
# frases de conversa que a IA às vezes põe antes ou depois do documento
CONVERSA = re.compile(r"^(claro|certo|certamente|com certeza|perfeito|ótimo|segue|seguem|aqui está|aqui estão|abaixo segue|"
                      r"espero que|caso precise|se precisar|fico à disposição|posso ajudar|observação: este documento foi gerado)", re.I)
ROMANOS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"]


# ── Dados do documento ────────────────────────────────────────────────────────────────────────────────────────
def local_e_data(cidade: str = "", uf: str = "", dia: date | None = None) -> str:
    """'Rio de Janeiro, RJ, 1º de março de 2026.' (MaTDoc 1.4.5 e 1.9 a: dia sem zero, 1º no primeiro dia)."""
    dia = dia or date.today()
    numero = "1º" if dia.day == 1 else str(dia.day)
    lugar = ", ".join(p for p in ((cidade or "").strip(), (uf or "").strip().upper()) if p) or "__________, __"
    return f"{lugar}, {numero} de {MESES[dia.month - 1]} de {dia.year}."


def _assinantes(d: dict) -> list[dict]:
    """Lista de signatários [{'nome', 'posto', 'cargo'}], na ordem informada (do mais antigo para o mais moderno)."""
    lista = d.get("assinantes")
    if not lista and any(d.get(k) for k in ("assinante_nome", "assinante_posto", "assinante_cargo")):
        lista = [{"nome": d.get("assinante_nome"), "posto": d.get("assinante_posto"), "cargo": d.get("assinante_cargo")}]
    limpos = [{k: (a.get(k) or "").strip() for k in ("nome", "posto", "cargo")} for a in (lista or [])]
    limpos = [a for a in limpos if any(a.values())]
    return limpos or [{"nome": "", "posto": "", "cargo": ""}]


def _linhas_assinatura(a: dict) -> list[str]:
    return [a["nome"].upper() or "NOME DO SIGNATÁRIO", a["posto"] or "Posto / graduação", a["cargo"] or "Cargo / função"]


def _dados(d: dict | None) -> dict:
    d = dict(d or {})
    return {
        "om": (d.get("om") or "").strip(),
        "cidade": (d.get("cidade") or "").strip(),
        "uf": (d.get("uf") or "").strip(),
        "nup": (d.get("nup") or "").strip(),
        "assinantes": _assinantes(d),
        "data": d.get("data") if isinstance(d.get("data"), date) else None,
    }


# ── Leitura do Markdown ───────────────────────────────────────────────────────────────────────────────────────
def _normal(texto: str) -> str:
    texto = unicodedata.normalize("NFD", re.sub(r"[*_#`]", "", texto or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()


def segmentos(texto: str) -> list[tuple[str, bool, bool]]:
    """'a **b** *c*' -> [('a ', F, F), ('b', T, F), (' ', F, F), ('c', F, T)]."""
    partes = []
    # lacunas "_____" (3 ou mais) são texto, não marcação de itálico/negrito
    lacunas = re.findall(r"_{3,}", texto)
    texto = re.sub(r"_{3,}", "\x00", texto)
    for m in re.finditer(r"\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|__(.+?)__|\*(?!\s)(.+?)(?<!\s)\*|([^*_]+|[*_])", texto):
        if m.group(1) is not None:
            partes.append((m.group(1), True, True))
        elif m.group(2) is not None or m.group(3) is not None:
            partes.append((m.group(2) or m.group(3), True, False))
        elif m.group(4) is not None:
            partes.append((m.group(4), False, True))
        else:
            partes.append((m.group(5), False, False))
    junto: list[tuple[str, bool, bool]] = []
    for t, b, i in partes:
        if junto and junto[-1][1:] == (b, i):
            junto[-1] = (junto[-1][0] + t, b, i)
        else:
            junto.append((t, b, i))
    if lacunas:
        resto = iter(lacunas)
        junto = [(re.sub("\x00", lambda _m: next(resto), t), b, i) for t, b, i in junto]
    return [p for p in junto if p[0]]


_MEDIDORES: dict = {}


def _medidor(fonte_pt: float):
    """FPDF só para medir texto na Carlito (negrito, o caso mais largo)."""
    if fonte_pt not in _MEDIDORES:
        from fpdf import FPDF
        m = FPDF()
        m.add_font("Carlito", "B", FONTES["B"])
        m.set_font("Carlito", "B", fonte_pt)
        _MEDIDORES[fonte_pt] = m
    return _MEDIDORES[fonte_pt]


def _larguras_colunas(linhas: list[list[str]], total_mm: float, fonte_pt: float) -> list[float]:
    """Largura de cada coluna em mm: primeiro garante que a palavra mais longa da coluna (cabeçalho ou conteúdo) caiba
    sem partir; a sobra é repartida conforme o tamanho do conteúdo, com teto menor quando há muitas colunas."""
    medidor = _medidor(fonte_pt)
    teto = 42 if len(linhas[0]) <= 5 else 26
    minimos, extras = [], []
    for c in range(len(linhas[0])):
        textos = [re.sub(r"[*_]", "", r[c]) for r in linhas]
        palavras = [p for t in textos for p in t.split()] or ["___"]
        palavra = max(len(p) for p in palavras)
        conteudo = max((len(t) for t in textos[1:]), default=0)
        larga = max(medidor.get_string_width(p) for p in palavras)
        minimos.append(larga * 1.08 + 4)  # negrito do cabeçalho e margens internas da célula
        extras.append(max(min(teto, conteudo) - palavra, 0) + 1)
    sobra = total_mm - sum(minimos)
    if sobra <= 0:
        return [total_mm * m / sum(minimos) for m in minimos]
    return [m + sobra * e / sum(extras) for m, e in zip(minimos, extras)]


def _celulas(linha: str) -> list[str]:
    linha = linha.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", linha)]


def interpretar(corpo: str, titulo: str = "") -> list[dict]:
    """Markdown -> blocos {'tipo': 'item'|'texto'|'subitem'|'alinea'|'subalinea'|'tabela'|'vazio', ...}."""
    linhas = (corpo or "").replace("\r\n", "\n").split("\n")
    blocos: list[dict] = []
    titulo_n = _normal(titulo)
    i = 0
    letra = 0
    romano = 0
    while i < len(linhas):
        bruta = linhas[i].rstrip()
        linha = bruta.strip()
        if CONVERSA.match(re.sub(r"^[*_#>\s]+", "", linha)) and not any(b["tipo"] in ("tabela",) for b in blocos[-1:]) and (
                not any(b["tipo"] != "vazio" for b in blocos) or i >= len(linhas) - 3):
            i += 1  # conversa no início ou no fim da resposta
            continue
        if not linha or RODAPES_DESCARTADOS.search(linha) or re.fullmatch(r"[-*=]{3,}", linha):
            if not linha and blocos and blocos[-1]["tipo"] != "vazio":
                blocos.append({"tipo": "vazio"})
            letra = 0
            i += 1
            continue
        if linha.startswith("|"):                                   # tabela
            tab = []
            while i < len(linhas) and linhas[i].strip().startswith("|"):
                if not re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?", linhas[i].strip()):
                    tab.append(_celulas(linhas[i]))
                i += 1
            n = max(len(r) for r in tab)
            blocos.append({"tipo": "tabela", "linhas": [r + [""] * (n - len(r)) for r in tab]})
            letra = 0
            continue
        cab = re.match(r"^(#{1,6})\s+(.*)$", linha)
        if cab:
            texto = cab.group(2).strip().strip("*").strip()
            if not (len(cab.group(1)) <= 2 and (not blocos or all(b["tipo"] == "vazio" for b in blocos))
                    and (titulo_n and (_normal(texto) in titulo_n or titulo_n in _normal(texto)))):
                blocos.append({"tipo": "item", "texto": texto.upper() if len(texto) <= 90 else texto})
            letra = 0
            i += 1
            continue
        recuo = len(bruta) - len(bruta.lstrip())
        marcador = re.match(r"^[-*•]\s+(.*)$", linha)
        if marcador:                                                  # lista -> alínea a) / subalínea I)
            if recuo >= 2:
                romano += 1
                blocos.append({"tipo": "subalinea", "texto": f"{ROMANOS[(romano - 1) % len(ROMANOS)]}) {marcador.group(1)}"})
            else:
                romano = 0
                letra += 1
                rot = chr(ord("a") + (letra - 1) % 26)
                blocos.append({"tipo": "alinea", "texto": f"{rot}) {marcador.group(1)}"})
            i += 1
            continue
        if re.match(r"^\d+\.\d+(\.\d+)*\.?\s", linha):
            blocos.append({"tipo": "subitem", "texto": linha})
        elif re.match(r"^[a-z]\)\s", linha):
            blocos.append({"tipo": "alinea", "texto": linha})
        elif re.match(r"^[IVX]+\)\s", linha):
            blocos.append({"tipo": "subalinea", "texto": linha})
        else:
            blocos.append({"tipo": "texto", "texto": linha})
            letra = 0
        i += 1
    while blocos and blocos[-1]["tipo"] == "vazio":
        blocos.pop()
    return blocos


# ── PDF (fpdf2, fonte Carlito embutida) ───────────────────────────────────────────────────────────────────────
MM = {"esq": 30, "dir": 15, "sup": 20, "inf": 20}
# recuo da 1ª linha: texto e subitem a 0,5 cm, alínea a 1,0 cm, subalínea a 1,5 cm (MaTDoc 1.5.3)
RECUO_MM = {"texto": 5, "item": 0, "subitem": 5, "alinea": 10, "subalinea": 15}
# correspondência: itens sem título a 2,5 cm; subitem 3,0, alínea 3,5 e subalínea 4,0 cm (MaTDoc 1.5.1 e cap. 16)
RECUO_OFICIO_MM = {"texto": 25, "item": 25, "subitem": 30, "alinea": 35, "subalinea": 40}


def _fpdf_md(texto: str) -> str:
    """Markdown do texto -> marcação do fpdf2 (**negrito**, __itálico__)."""
    out = []
    for t, b, i in segmentos(texto):
        t = t.replace("--", "-\u2011").replace("_", "_\u200b")  # evita que "__" e "--" virem marcação do fpdf2
        out.append(f"**__{t}__**" if b and i else f"**{t}**" if b else f"__{t}__" if i else t)
    return "".join(out)


def _paragrafo(pdf, texto: str, recuo_1a: float = 0, recuo: float = 0, alinhamento: str = "J", depois: float = 1.5,
               negrito: bool = False):
    """Parágrafo com recuo da primeira linha (o multi_cell não tem), negrito e itálico do Markdown."""
    with pdf.text_columns(text_align=alinhamento, line_height=1.18, l_margin=MM["esq"] + recuo, r_margin=MM["dir"]) as tc:
        with tc.paragraph(first_line_indent=recuo_1a, bottom_margin=depois) as par:
            for t, b, i in segmentos(texto):
                pdf.set_font("Carlito", ("B" if b or negrito else "") + ("I" if i else ""), 12)
                par.write(t)
    pdf.set_font("Carlito", "", 12)


def _rotulado(pdf, rotulo: str, texto: str, negrito_texto: bool = False):
    """'Assunto:' na margem e o texto alinhado a 2,5 cm, com as linhas seguintes também a 2,5 cm (MaTDoc cap. 16)."""
    y = pdf.get_y()
    pdf.set_font("Carlito", "", 12)
    pdf.set_xy(MM["esq"], y)
    pdf.cell(25, 6, rotulo)
    pdf.set_xy(MM["esq"] + 25, y)
    pdf.set_font("Carlito", "B" if negrito_texto else "", 12)
    pdf.multi_cell(pdf.w - MM["esq"] - MM["dir"] - 25, 6, texto, align="J", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Carlito", "", 12)


def _lista_rotulada(pdf, rotulo: str, itens: list[str]):
    """'Referências:' / 'Anexos:' com 'A) ...;' e '... .' (MaTDoc 1.4.10 e 1.4.11)."""
    itens = [i.strip().rstrip(";.") for i in itens if i and i.strip()]
    if not itens:
        return
    linhas = [f"{chr(65 + k)}) {t}{'.' if k == len(itens) - 1 else ('; e' if k == len(itens) - 2 else ';')}"
              for k, t in enumerate(itens)]
    _rotulado(pdf, rotulo, linhas[0])
    for linha in linhas[1:]:
        pdf.set_x(MM["esq"] + 25)
        pdf.multi_cell(pdf.w - MM["esq"] - MM["dir"] - 25, 6, linha, align="J", new_x="LMARGIN", new_y="NEXT")


def _oficio(of: dict | None) -> dict | None:
    if not of:
        return None
    of = dict(of)
    for k in ("numero", "do", "ao", "via", "assunto", "endereco", "destinatario", "vocativo", "fecho"):
        of[k] = (of.get(k) or "").strip()
    for k in ("referencias", "anexos", "copias"):
        v = of.get(k) or []
        of[k] = [x.strip() for x in (v.splitlines() if isinstance(v, str) else v) if x and x.strip()]
    of["externo"] = bool(of.get("externo"))
    if of["externo"] and not of["fecho"]:
        of["fecho"] = "Atenciosamente,"
    return of


def _pdf(titulo: str, blocos: list[dict], d: dict, numerar: bool, of: dict | None = None):
    from fpdf import FPDF
    from fpdf.fonts import FontFace

    class Doc(FPDF):
        def footer(self):
            self.set_y(-14)
            self.set_font("Carlito", "", 12)
            if d["nup"]:
                self.set_y(-19)
                self.cell(0, 5, d["nup"], align="R", new_x="LMARGIN", new_y="NEXT")
            if numerar:
                self.cell(0, 5, f"- {self.page_no()} de {{nb}} -", align="C")

    pdf = Doc(format="A4")
    pdf.set_margins(MM["esq"], MM["sup"], MM["dir"])
    pdf.set_auto_page_break(True, margin=MM["inf"] + (10 if d["nup"] else 6))
    for estilo, arq in FONTES.items():
        pdf.add_font("Carlito", estilo, arq)
    pdf.alias_nb_pages()
    pdf.add_page()
    largura = pdf.w - MM["esq"] - MM["dir"]

    # timbre (MaTDoc 1.4.1): Armas Nacionais 2,0 x 2,0 cm, MARINHA DO BRASIL e nome da OM
    if os.path.exists(ARMAS):
        pdf.image(ARMAS, x=MM["esq"] + (largura - 20) / 2, y=pdf.get_y(), w=20, h=20)
        pdf.ln(21)
    pdf.set_font("Carlito", "B", 12)
    pdf.cell(0, 6, "MARINHA DO BRASIL", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.multi_cell(0, 6, (d["om"] or "NOME DA ORGANIZAÇÃO MILITAR").upper(), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Carlito", "", 12)
    if of and of["externo"] and of["endereco"]:
        for linha in of["endereco"].splitlines():
            pdf.multi_cell(0, 5, linha.strip(), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    data_txt = local_e_data(d["cidade"], d["uf"], d["data"])
    if of:
        # Of (MaTDoc cap. 16): "Nº" e local e data; Do/Ao/Via; Assunto; Referências; Anexos. OfExt (cap. 17): número,
        # local e data, destinatário, Assunto em negrito e vocativo. Nenhum dos dois tem título.
        y = pdf.get_y()
        numero = of["numero"] or "___"
        pdf.cell(0, 6, f"Ofício nº {numero}" if of["externo"] else f"Nº {numero}", align="L")
        pdf.set_xy(MM["esq"], y)
        pdf.cell(0, 6, data_txt, align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(12)
        if of["externo"]:
            for linha in (of["destinatario"] or "Ao Senhor\n__________").splitlines():
                pdf.multi_cell(0, 6, linha.strip(), align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(6)
            _rotulado(pdf, "Assunto:", of["assunto"] or "__________", negrito_texto=True)
            pdf.ln(6)
            if of["vocativo"]:
                _paragrafo(pdf, of["vocativo"], recuo_1a=25, alinhamento="L", depois=4)
        else:
            _rotulado(pdf, "Do:", of["do"] or "__________")
            _rotulado(pdf, "Ao:", of["ao"] or "__________")
            if of["via"]:
                _rotulado(pdf, "Via:", of["via"])
            pdf.ln(6)
            _rotulado(pdf, "Assunto:", of["assunto"] or "__________")
            if of["referencias"]:
                pdf.ln(6)
                _lista_rotulada(pdf, "Referências:" if len(of["referencias"]) > 1 else "Referência:", of["referencias"])
            if of["anexos"]:
                pdf.ln(6)
                _lista_rotulada(pdf, "Anexos:" if len(of["anexos"]) > 1 else "Anexo:", of["anexos"])
            pdf.ln(12)
    else:
        pdf.cell(0, 6, data_txt, align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(12)
        pdf.set_font("Carlito", "B", 12)
        pdf.multi_cell(0, 6, titulo.upper(), align="C", new_x="LMARGIN", new_y="NEXT")
        if d["nup"]:
            pdf.set_font("Carlito", "", 12)
            pdf.cell(0, 6, f"NUP: {d['nup']}", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)

    for b in blocos:
        tipo = b["tipo"]
        if tipo == "vazio":
            pdf.ln(3)
            continue
        if tipo == "tabela":
            linhas = b["linhas"]
            n = len(linhas[0])
            corpo = 9 if n >= 8 else 10 if n >= 5 else 11
            larguras = _larguras_colunas(linhas, largura, corpo)
            pdf.set_font("Carlito", "", corpo)
            pdf.ln(1)
            with pdf.table(col_widths=larguras, width=largura, line_height=5, markdown=True, text_align="LEFT",
                           headings_style=FontFace(emphasis="BOLD", fill_color=(242, 242, 242)),
                           repeat_headings=1, padding=1.2) as tabela:
                for r in linhas:
                    linha = tabela.row()
                    for c in r:
                        linha.cell(_fpdf_md(c))
            pdf.ln(3)
            pdf.set_font("Carlito", "", 12)
            continue
        if tipo == "item":
            pdf.ln(3)
            pdf.set_font("Carlito", "B", 12)
            pdf.multi_cell(0, 6, re.sub(r"[*_]{2,}", "", b["texto"]), align="L", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Carlito", "", 12)
            pdf.ln(1)
            continue
        recuos = RECUO_OFICIO_MM if of else RECUO_MM
        _paragrafo(pdf, b["texto"], recuo_1a=recuos.get(tipo, 0), depois=3 if of else 1.5)

    if of and of["externo"] and of["fecho"]:
        pdf.ln(2)
        _paragrafo(pdf, of["fecho"], recuo_1a=25, alinhamento="L")

    # assinaturas (MaTDoc 1.11): três linhas em branco; uma centralizada ou duas por linha, da esquerda para a direita
    pdf.set_font("Carlito", "", 12)
    assinantes = d["assinantes"]
    for k in range(0, len(assinantes), 2):
        dupla = assinantes[k:k + 2]
        if len(dupla) == 1 and k + 1 == len(assinantes) and len(assinantes) > 1:
            pdf.ln(6)
        if pdf.get_y() + 18 + 18 > pdf.h - pdf.b_margin:  # bloco não parte entre páginas
            pdf.add_page()
        pdf.ln(18)
        y0 = pdf.get_y()
        coluna = largura / len(dupla)
        for j, a in enumerate(dupla):
            pdf.set_xy(MM["esq"] + j * coluna, y0)
            for linha in _linhas_assinatura(a):
                pdf.set_x(MM["esq"] + j * coluna)
                pdf.multi_cell(coluna, 6, linha, align="C", new_x="LEFT", new_y="NEXT")
            fim = pdf.get_y()
        pdf.set_y(max(fim, y0 + 18))
    if of and of["copias"]:
        if pdf.get_y() + 8 + 6 * (len(of["copias"]) + 1) > pdf.h - pdf.b_margin:
            pdf.add_page()
        else:
            pdf.ln(8)
        pdf.cell(0, 6, "Cópias:" if len(of["copias"]) > 1 else "Cópia:", new_x="LMARGIN", new_y="NEXT")
        for c in of["copias"]:
            pdf.cell(0, 6, c, new_x="LMARGIN", new_y="NEXT")
    return pdf


def gerar_pdf(titulo: str, corpo: str, dados: dict | None = None, oficio: dict | None = None) -> bytes:
    """oficio: None (peça do processo com título) ou {'externo', 'numero', 'do', 'ao', 'via', 'assunto', 'referencias',
    'anexos', 'copias'} para o Of (MaTDoc cap. 16), mais 'endereco', 'destinatario', 'vocativo' e 'fecho' no OfExt (cap. 17)."""
    d = _dados(dados)
    of = _oficio(oficio)
    blocos = interpretar(corpo, titulo)
    rascunho = _pdf(titulo, blocos, d, numerar=False, of=of)
    paginas = rascunho.page_no()
    pdf = _pdf(titulo, blocos, d, numerar=paginas > 1, of=of) if paginas > 1 else rascunho  # 1 página: sem numeração (MaTDoc 1.14)
    return bytes(pdf.output())


# ── Word (python-docx) ────────────────────────────────────────────────────────────────────────────────────────
def gerar_docx(titulo: str, corpo: str, dados: dict | None = None, oficio: dict | None = None) -> bytes:
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt

    d = _dados(dados)
    of = _oficio(oficio)
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin, sec.right_margin, sec.top_margin, sec.bottom_margin = Cm(3), Cm(1.5), Cm(2), Cm(2)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"                                   # MaTDoc 1.2.2: Carlito ou Calibri
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.font.size = Pt(12)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.line_spacing = 1.0

    def par(texto="", alinhamento=None, negrito=False, recuo_1a=None, recuo=None, antes=0, depois=0, manter=False, tamanho=None):
        p = doc.add_paragraph()
        if alinhamento is not None:
            p.alignment = alinhamento
        f = p.paragraph_format
        f.space_before, f.space_after = Pt(antes), Pt(depois)
        if recuo_1a is not None:
            f.first_line_indent = Cm(recuo_1a)
        if recuo is not None:
            f.left_indent = Cm(recuo)
        f.keep_with_next = manter
        for t, b, i in (segmentos(texto) if texto else []):
            r = p.add_run(t)
            r.bold = negrito or b
            r.italic = i
            if tamanho:
                r.font.size = Pt(tamanho)
        return p

    # timbre
    if os.path.exists(ARMAS):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(ARMAS, width=Cm(2), height=Cm(2))
    par("MARINHA DO BRASIL", WD_ALIGN_PARAGRAPH.CENTER, negrito=True)
    par()
    par((d["om"] or "NOME DA ORGANIZAÇÃO MILITAR").upper(), WD_ALIGN_PARAGRAPH.CENTER, negrito=True)
    if of and of["externo"] and of["endereco"]:
        for linha in of["endereco"].splitlines():
            par(linha.strip(), WD_ALIGN_PARAGRAPH.CENTER, tamanho=11)
    par()
    data_txt = local_e_data(d["cidade"], d["uf"], d["data"])

    def rotulado(rotulo, texto, negrito_texto=False):
        """Rótulo na margem e texto a 2,5 cm, com as linhas seguintes também a 2,5 cm."""
        p = par(f"{rotulo}\t", WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=2.5, recuo_1a=-2.5)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(2.5))
        for t, b, i in segmentos(texto):
            r = p.add_run(t)
            r.bold = negrito_texto or b
            r.italic = i
        return p

    def lista_rotulada(rotulo, itens):
        itens = [i.strip().rstrip(";.") for i in itens if i and i.strip()]
        for k, t in enumerate(itens):
            fim = "." if k == len(itens) - 1 else ("; e" if k == len(itens) - 2 else ";")
            if k == 0:
                rotulado(rotulo, f"{chr(65 + k)}) {t}{fim}")
            else:
                par(f"{chr(65 + k)}) {t}{fim}", WD_ALIGN_PARAGRAPH.JUSTIFY, recuo=2.5)

    if of:
        p = par(f"Ofício nº {of['numero'] or '___'}" if of["externo"] else f"Nº {of['numero'] or '___'}")
        p.paragraph_format.tab_stops.add_tab_stop(Cm(16.5), WD_TAB_ALIGNMENT.RIGHT)
        p.add_run("\t" + data_txt)
        par()
        par()
        if of["externo"]:
            for linha in (of["destinatario"] or "Ao Senhor\n__________").splitlines():
                par(linha.strip())
            par()
            rotulado("Assunto:", of["assunto"] or "__________", negrito_texto=True)
            par()
            if of["vocativo"]:
                par(of["vocativo"], recuo_1a=2.5, depois=6)
        else:
            rotulado("Do:", of["do"] or "__________")
            rotulado("Ao:", of["ao"] or "__________")
            if of["via"]:
                rotulado("Via:", of["via"])
            par()
            rotulado("Assunto:", of["assunto"] or "__________")
            if of["referencias"]:
                par()
                lista_rotulada("Referências:" if len(of["referencias"]) > 1 else "Referência:", of["referencias"])
            if of["anexos"]:
                par()
                lista_rotulada("Anexos:" if len(of["anexos"]) > 1 else "Anexo:", of["anexos"])
            par()
            par()
    else:
        par(data_txt, WD_ALIGN_PARAGRAPH.RIGHT)
        par()
        par()
        par(titulo.upper(), WD_ALIGN_PARAGRAPH.CENTER, negrito=True)
        if d["nup"]:
            par(f"NUP: {d['nup']}", WD_ALIGN_PARAGRAPH.CENTER)
        par()

    justif = WD_ALIGN_PARAGRAPH.JUSTIFY
    for b in interpretar(corpo, titulo):
        tipo = b["tipo"]
        if tipo == "vazio":
            continue
        if tipo == "item":
            par(b["texto"].replace("**", ""), WD_ALIGN_PARAGRAPH.LEFT, negrito=True, antes=12, depois=4, manter=True)
        elif tipo in ("texto", "subitem", "alinea", "subalinea"):
            recuo_cm = (RECUO_OFICIO_MM if of else RECUO_MM)[tipo] / 10
            par(b["texto"], justif, recuo_1a=recuo_cm, depois=6 if tipo in ("texto", "subitem") else 3)
        elif tipo == "tabela":
            linhas = b["linhas"]
            n = len(linhas[0])
            tam = 9 if n >= 8 else 10 if n >= 5 else 11
            tab = doc.add_table(rows=len(linhas), cols=n)
            tab.style = "Table Grid"
            tab.alignment = WD_TABLE_ALIGNMENT.CENTER
            tab.autofit = False
            larguras = [Cm(w / 10) for w in _larguras_colunas(linhas, 165, tam)]
            for c, w in enumerate(larguras):
                tab.columns[c].width = w                                # grade da tabela (lida pelo LibreOffice)
                for cel in tab.columns[c].cells:
                    cel.width = w                                       # largura de cada célula (lida pelo Word)
            for r, linha in enumerate(linhas):
                row = tab.rows[r]
                if r == 0:  # cabeçalho repetido em cada página
                    trPr = row._tr.get_or_add_trPr()
                    h = OxmlElement("w:tblHeader")
                    h.set(qn("w:val"), "true")
                    trPr.append(h)
                for c, valor in enumerate(linha):
                    cel = row.cells[c]
                    cel.text = ""
                    p = cel.paragraphs[0]
                    for t, bb, ii in segmentos(valor):
                        run = p.add_run(t)
                        run.bold = bb or r == 0
                        run.italic = ii
                        run.font.size = Pt(tam)
                    if r == 0:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        sombra = OxmlElement("w:shd")
                        sombra.set(qn("w:val"), "clear")
                        sombra.set(qn("w:color"), "auto")
                        sombra.set(qn("w:fill"), "F2F2F2")
                        cel._tc.get_or_add_tcPr().append(sombra)
            par(depois=6)

    if of and of["externo"] and of["fecho"]:
        par(of["fecho"], recuo_1a=2.5, antes=6)

    # assinaturas (MaTDoc 1.11): três linhas em branco; uma centralizada ou duas por linha (tabela sem bordas)
    assinantes = d["assinantes"]
    for _ in range(3):
        par(manter=True)
    if len(assinantes) == 1:
        linhas = _linhas_assinatura(assinantes[0])
        for k, linha in enumerate(linhas):
            par(linha, WD_ALIGN_PARAGRAPH.CENTER, manter=k < len(linhas) - 1)
    else:
        for k in range(0, len(assinantes), 2):
            dupla = assinantes[k:k + 2]
            if k:
                for _ in range(3):
                    par(manter=True)
            tab = doc.add_table(rows=1, cols=len(dupla))
            tab.alignment = WD_TABLE_ALIGNMENT.CENTER
            for j, a in enumerate(dupla):
                cel = tab.rows[0].cells[j]
                cel.text = ""
                for n, linha in enumerate(_linhas_assinatura(a)):
                    p = cel.paragraphs[0] if n == 0 else cel.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    p.add_run(linha)
            trPr = tab.rows[0]._tr.get_or_add_trPr()
            nao_parte = OxmlElement("w:cantSplit")
            trPr.append(nao_parte)

    if of and of["copias"]:
        par()
        par("Cópias:" if len(of["copias"]) > 1 else "Cópia:")
        for c in of["copias"]:
            par(c)

    # rodapé: NUP à direita e "- n de N -" centralizado, só com mais de uma página (campo IF do Word)
    rod = sec.footer
    rod.is_linked_to_previous = False
    p0 = rod.paragraphs[0]
    if d["nup"]:
        p0.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p0.add_run(d["nup"])
        p0 = rod.add_paragraph()
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def campo(paragrafo, partes):
        """partes: lista de ('begin'|'instr'|'separate'|'end'|'text', valor)."""
        for tipo, valor in partes:
            run = paragrafo.add_run()
            if tipo == "text":
                run.text = valor
            elif tipo == "instr":
                el = OxmlElement("w:instrText")
                el.set(qn("xml:space"), "preserve")
                el.text = valor
                run._r.append(el)
            else:
                el = OxmlElement("w:fldChar")
                el.set(qn("w:fldCharType"), tipo)
                run._r.append(el)

    campo(p0, [("text", "- "), ("begin", None), ("instr", " PAGE "), ("separate", None), ("text", "1"), ("end", None),
               ("text", " de "), ("begin", None), ("instr", " NUMPAGES "), ("separate", None), ("text", "1"), ("end", None),
               ("text", " -")])

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
