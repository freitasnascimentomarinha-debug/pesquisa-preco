"""
Parser da Lei 14.133/2021 — extrai artigos do arquivo .txt e os indexa
para busca por palavras-chave (RAG simplificado com texto integral).
"""

import os
import re

_LEI_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Lei 14.133.txt")

_LINK_BASE = (
    "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14133.htm"
)


def _normalizar_numero_artigo(num_str: str) -> str:
    """Converte '1º', '12', '194-A' para link-friendly: 'art1', 'art12', 'art194a'."""
    limpo = num_str.replace("º", "").replace("°", "").replace(" ", "").lower()
    limpo = re.sub(r"[^a-z0-9]", "", limpo)
    return f"art{limpo}"


def carregar_artigos_lei(caminho: str | None = None) -> list[dict]:
    """Lê o arquivo da lei e retorna lista de dicts no formato da base jurídica.

    Cada dict tem: fonte, artigo, titulo, conteudo, link, palavras_chave
    """
    caminho = caminho or _LEI_PATH
    if not os.path.isfile(caminho):
        return []

    with open(caminho, "r", encoding="utf-8") as f:
        texto = f.read()

    # Regex para capturar início de artigo: "Art. 1º ...", "Art. 12. ...", "Art. 194-A."
    padrao_art = re.compile(
        r"^(Art\.\s*(\d+(?:-[A-Z])?[º°]?))\b(.*)",
        re.MULTILINE,
    )

    matches = list(padrao_art.finditer(texto))
    if not matches:
        return []

    artigos = []
    for i, m in enumerate(matches):
        inicio = m.start()
        fim = matches[i + 1].start() if i + 1 < len(matches) else len(texto)
        bloco = texto[inicio:fim].strip()

        art_label = m.group(1).strip()           # "Art. 23"
        art_num = m.group(2).strip()              # "23"

        # Primeira frase serve de título resumido (até o primeiro ponto ou 120 chars)
        primeira_linha = bloco.split("\n")[0]
        # Remove o "Art. Xº " do início para extrair o título
        titulo_raw = re.sub(r"^Art\.\s*\d+(?:-[A-Z])?[º°]?\s*", "", primeira_linha)
        titulo = titulo_raw[:120].rstrip(".") if titulo_raw else art_label

        # Link direto para o artigo na página do Planalto
        anchor = _normalizar_numero_artigo(art_num)
        link = f"{_LINK_BASE}#{anchor}"

        # Gerar palavras-chave: tokens significativos (>3 chars) do bloco
        tokens = re.findall(r"[a-záàâãéèêíïóôõúüç]{4,}", bloco.lower())
        # Frequência para pegar as mais relevantes
        freq: dict[str, int] = {}
        stopwords = {
            "para", "pelo", "pela", "pelos", "pelas", "esta", "este", "essa",
            "esse", "como", "será", "serão", "pode", "podem", "deve", "devem",
            "sido", "sido", "quando", "caso", "forma", "prazo", "inciso",
            "caput", "artigo", "previsto", "prevista", "referido", "também",
            "desde", "qual", "quais", "sobre", "entre", "mais", "menos",
            "outro", "outra", "outros", "outras", "após", "antes", "ainda",
            "todas", "todos", "cada", "suas", "seus", "dele", "dela",
            "nesta", "neste", "nessa", "nesse", "deste", "desta", "desse",
            "dessa", "aquele", "aquela", "sendo", "terá", "tenha",
        }
        for t in tokens:
            if t not in stopwords:
                freq[t] = freq.get(t, 0) + 1
        palavras_chave = sorted(freq, key=freq.get, reverse=True)[:15]

        artigos.append({
            "fonte": "Lei 14.133/2021",
            "artigo": art_label,
            "titulo": titulo,
            "conteudo": bloco,
            "link": link,
            "palavras_chave": palavras_chave,
        })

    return artigos


# Cache em nível de módulo para não reler o arquivo a cada chamada
_cache: list[dict] | None = None


def get_artigos_lei() -> list[dict]:
    """Retorna os artigos parseados (com cache)."""
    global _cache
    if _cache is None:
        _cache = carregar_artigos_lei()
    return _cache
