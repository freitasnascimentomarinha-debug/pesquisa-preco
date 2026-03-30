"""
build_rag.py — Constrói a base de conhecimento RAG a partir dos documentos da pasta pages/RAG/
Gera o arquivo rag_knowledge_base.json com itens indexados por palavras-chave.

Fontes processadas:
  - Instruções Normativas (.txt)
  - Decretos (.txt)
  - Acórdãos TCU (.xls)
"""

import json
import os
import re
import unicodedata

RAG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages", "RAG")
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rag_knowledge_base.json")

# ════════════════════════════════════════════════════════════
# UTILIDADES
# ════════════════════════════════════════════════════════════

def _normalizar(texto: str) -> str:
    """Remove acentos e converte para minúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


def _extrair_palavras_chave(texto: str, min_len: int = 3) -> list[str]:
    """Extrai palavras-chave relevantes do texto (sem stopwords comuns)."""
    stopwords = {
        "que", "para", "com", "por", "dos", "das", "nos", "nas", "uma", "uns",
        "umas", "pelo", "pela", "pelos", "pelas", "este", "esta", "esse", "essa",
        "aquele", "aquela", "sobre", "como", "mais", "seu", "sua", "seus", "suas",
        "entre", "quando", "onde", "qual", "quais", "cada", "todo", "toda", "todos",
        "todas", "mesmo", "mesma", "mesmos", "mesmas", "outro", "outra", "outros",
        "outras", "ainda", "tambem", "sera", "serao", "pode", "podem", "deve",
        "devem", "sido", "sendo", "tendo", "ter", "tem", "the", "and", "for",
        "from", "nao", "sim", "art", "inc", "lei", "decreto", "nos", "num",
        "cap", "caput", "inciso", "paragrafo", "alinea", "item", "forma",
        "caso", "prazo", "data", "dia", "dias", "ano", "anos", "mes", "meses",
        "podera", "devera", "sera", "deverao", "poderao", "disposto", "previsto",
        "estabelecido", "termos", "observado", "conforme", "mediante",
    }
    palavras = re.findall(r"\w+", _normalizar(texto))
    relevantes = [p for p in palavras if len(p) >= min_len and p not in stopwords and not p.isdigit()]
    # Deduplica mantendo ordem
    vistos = set()
    resultado = []
    for p in relevantes:
        if p not in vistos:
            vistos.add(p)
            resultado.append(p)
    return resultado[:30]  # Máximo de 30 palavras-chave por item


# ════════════════════════════════════════════════════════════
# PARSER DE INSTRUÇÕES NORMATIVAS E DECRETOS (.txt)
# ════════════════════════════════════════════════════════════

def _identificar_fonte(nome_arquivo: str, conteudo: str) -> dict:
    """Identifica metadados da norma a partir do nome do arquivo e conteúdo."""
    info = {"fonte": "", "sigla": "", "link": ""}

    if "INSTRUÇÃO NORMATIVA" in nome_arquivo.upper() or "INSTRUCAO NORMATIVA" in nome_arquivo.upper():
        # Extrair número e ano
        m = re.search(r"(?:Nº\s*)?(\d+)\s*[,-]\s*(?:DE\s+)?(\d{1,2}\s+DE\s+\w+\s+DE\s+)?(\d{4})", conteudo[:500], re.IGNORECASE)
        if m:
            num = m.group(1)
            ano = m.group(3) if m.group(3) else ""
            # Identificar órgão emissor
            if "SEGES/ME" in conteudo[:500] or "SEGESME" in nome_arquivo.upper():
                orgao = "SEGES/ME"
            elif "SEGES" in conteudo[:500]:
                orgao = "SEGES"
            else:
                orgao = "SEGES/ME"
            info["fonte"] = f"IN {orgao} nº {num}/{ano}"
            info["sigla"] = f"IN {num}/{ano}"
        else:
            info["fonte"] = nome_arquivo.replace(".txt", "")
            info["sigla"] = info["fonte"]
        info["link"] = "https://www.gov.br/compras/pt-br/acesso-a-informacao/legislacao/instrucoes-normativas"

    elif "DECRETO" in nome_arquivo.upper():
        m = re.search(r"DECRETO\s+(?:Nº\s*)?(\d[\d.]*)", conteudo[:500], re.IGNORECASE)
        if m:
            num = m.group(1)
            info["fonte"] = f"Decreto nº {num}"
            info["sigla"] = f"Decreto {num}"
        else:
            info["fonte"] = nome_arquivo.replace(".txt", "")
            info["sigla"] = info["fonte"]
        info["link"] = "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/decreto/D10024.htm"

    else:
        info["fonte"] = nome_arquivo.replace(".txt", "")
        info["sigla"] = info["fonte"]
        info["link"] = ""

    return info


def parsear_norma_txt(caminho: str) -> list[dict]:
    """Extrai artigos de um arquivo .txt de norma jurídica."""
    nome_arquivo = os.path.basename(caminho)
    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()

    info = _identificar_fonte(nome_arquivo, texto)

    # Regex para capturar artigos: "Art. 1º", "Art. 12.", "Art. 3°"
    padrao_art = re.compile(
        r"^(Art\.\s*(\d+(?:-[A-Z])?[º°.]?))\b(.*)",
        re.MULTILINE,
    )
    matches = list(padrao_art.finditer(texto))

    if not matches:
        # Se não encontrou artigos, retorna o documento inteiro como um chunk
        return [{
            "fonte": info["fonte"],
            "artigo": "",
            "titulo": nome_arquivo.replace(".txt", ""),
            "conteudo": texto[:3000],
            "link": info["link"],
            "palavras_chave": _extrair_palavras_chave(texto[:3000]),
        }]

    artigos = []
    for i, m in enumerate(matches):
        inicio = m.start()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        bloco = texto[inicio:fim].strip()

        # Limitar tamanho do bloco
        if len(bloco) > 3000:
            bloco = bloco[:3000] + "..."

        num_str = m.group(2).replace("º", "").replace("°", "").replace(".", "")
        artigo_ref = f"Art. {m.group(2)}"

        # Tentar extrair título/ementa do artigo (primeira linha)
        primeira_linha = bloco.split("\n")[0][:200]

        artigos.append({
            "fonte": info["fonte"],
            "artigo": artigo_ref,
            "titulo": primeira_linha,
            "conteudo": bloco,
            "link": info["link"],
            "palavras_chave": _extrair_palavras_chave(bloco),
        })

    return artigos


# ════════════════════════════════════════════════════════════
# PARSER DE ACÓRDÃOS TCU (.xls)
# ════════════════════════════════════════════════════════════

def parsear_acordaos_xls(caminho: str) -> list[dict]:
    """Extrai acórdãos do TCU da planilha .xls"""
    try:
        import xlrd
    except ImportError:
        print("AVISO: xlrd não instalado. Instale com: pip install xlrd")
        return []

    wb = xlrd.open_workbook(caminho)
    sh = wb.sheet_by_index(0)

    # Ler cabeçalho
    if sh.nrows < 2:
        return []

    headers = [str(sh.cell_value(0, j)).strip().lower() for j in range(sh.ncols)]

    # Mapear colunas
    col_map = {}
    for j, h in enumerate(headers):
        if "enunciado" in h:
            col_map["enunciado"] = j
        elif "area" in h or "área" in h:
            col_map["area"] = j
        elif "tema" == h.strip():
            col_map["tema"] = j
        elif "subtema" in h:
            col_map["subtema"] = j
        elif "data" in h:
            col_map["data"] = j
        elif "acórdão" in h or "acordao" in h or "acord" in h:
            col_map["acordao"] = j
        elif "autor" in h:
            col_map["autor"] = j
        elif "legisla" in h:
            col_map["legislacao"] = j
        elif "indexador" in h:
            col_map["indexadores"] = j
        elif "tipo" in h:
            col_map["tipo"] = j

    acordaos = []
    for i in range(1, sh.nrows):
        def cell(col_name):
            j = col_map.get(col_name)
            if j is None:
                return ""
            val = sh.cell_value(i, j)
            if isinstance(val, float):
                return str(int(val)) if val == int(val) else str(val)
            return str(val).strip()

        enunciado = cell("enunciado")
        if not enunciado:
            continue

        # Limpar tags HTML do enunciado
        enunciado = re.sub(r"<[^>]+>", " ", enunciado)
        enunciado = re.sub(r"\s+", " ", enunciado).strip()

        num_acordao = cell("acordao")
        area = cell("area")
        tema = cell("tema")
        subtema = cell("subtema")
        data = cell("data")
        legislacao = cell("legislacao")
        indexadores = cell("indexadores")
        tipo = cell("tipo")

        # Montar título descritivo
        titulo_parts = []
        if area:
            titulo_parts.append(area)
        if tema:
            titulo_parts.append(tema)
        if subtema:
            titulo_parts.append(subtema)
        titulo = " — ".join(titulo_parts) if titulo_parts else f"Acórdão {num_acordao}"

        # Limitar enunciado
        if len(enunciado) > 2000:
            enunciado = enunciado[:2000] + "..."

        # Montar conteúdo completo
        conteudo = enunciado
        if legislacao:
            conteudo += f"\nLegislação: {legislacao}"

        # Palavras-chave: combinar tema, subtema, indexadores e enunciado
        texto_kw = f"{area} {tema} {subtema} {indexadores} {enunciado[:500]}"
        palavras_chave = _extrair_palavras_chave(texto_kw)

        # Extrair número e ano para o link
        # Formato: AC-338/03-P ou similar
        link = ""
        m = re.match(r"AC-?(\d+)/(\d+)-([A-Z])", num_acordao)
        if m:
            num = m.group(1)
            ano_curto = m.group(2)
            colegiado = m.group(3)
            ano_completo = f"20{ano_curto}" if int(ano_curto) < 50 else f"19{ano_curto}"
            col_nome = {"P": "Plenário", "1": "1ª Câmara", "2": "2ª Câmara"}.get(colegiado, "Plenário")
            link = f"https://pesquisa.apps.tcu.gov.br/#/documento/acordao-completo/{num}%20{ano_completo}"

        acordaos.append({
            "fonte": f"TCU — Acórdão {num_acordao}",
            "artigo": num_acordao,
            "titulo": titulo,
            "conteudo": conteudo,
            "link": link,
            "palavras_chave": palavras_chave,
        })

    return acordaos


# ════════════════════════════════════════════════════════════
# CONSTRUÇÃO DA BASE
# ════════════════════════════════════════════════════════════

def build():
    """Constrói a base de conhecimento RAG completa."""
    base = []

    if not os.path.isdir(RAG_DIR):
        print(f"ERRO: Pasta RAG não encontrada em {RAG_DIR}")
        return

    for arquivo in sorted(os.listdir(RAG_DIR)):
        caminho = os.path.join(RAG_DIR, arquivo)

        if arquivo.endswith(".txt"):
            print(f"Processando: {arquivo}")
            itens = parsear_norma_txt(caminho)
            base.extend(itens)
            print(f"  → {len(itens)} artigos extraídos")

        elif arquivo.endswith(".xls") or arquivo.endswith(".xlsx"):
            print(f"Processando: {arquivo}")
            itens = parsear_acordaos_xls(caminho)
            base.extend(itens)
            print(f"  → {len(itens)} acórdãos extraídos")

    # Salvar
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(base, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Base RAG gerada: {OUTPUT_PATH}")
    print(f"   Total de itens: {len(base)}")

    # Resumo por fonte
    fontes = {}
    for item in base:
        tipo = item["fonte"].split("—")[0].strip() if "—" in item["fonte"] else item["fonte"].split(" nº")[0].strip()
        fontes[tipo] = fontes.get(tipo, 0) + 1
    print("   Resumo:")
    for fonte, qtd in sorted(fontes.items()):
        print(f"     {fonte}: {qtd}")


if __name__ == "__main__":
    build()
