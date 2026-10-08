"""Lista de itens "de supermercado": descrição + quantidade + unidade, digitadas ou vindas de planilha.

Usado pelas páginas de pesquisa (Cotação Direta, Cotação Rápida, Notas Fiscais, Web Scraping). Aceita, por exemplo:
'caneta azul - 50', 'caneta azul; 100 cx', '50 canetas azuis', '50 un caneta azul', 'caneta azul x 50', 'caneta azul 50'.
Sem Streamlit neste módulo (a tela fica em lista_itens_ui.py): só contas, para poder ser testado.
"""

from __future__ import annotations

import re
import unicodedata

UNIDADES = ("un", "und", "unid", "unidade", "unidades", "pç", "pc", "peça", "peças", "cx", "caixa", "caixas", "pct", "pacote", "pacotes",
            "kg", "g", "l", "lt", "litro", "litros", "m", "mt", "metro", "metros", "par", "pares", "rolo", "rolos", "resma", "resmas",
            "galão", "galões", "kit", "kits", "jogo", "jogos", "saco", "sacos", "lata", "latas", "frasco", "frascos", "tubo", "tubos")
ROTULO_UNIDADE = {"un": "UN", "und": "UN", "unid": "UN", "unidade": "UN", "unidades": "UN", "pç": "PÇ", "pc": "PÇ", "peça": "PÇ", "peças": "PÇ",
                  "cx": "CX", "caixa": "CX", "caixas": "CX", "pct": "PCT", "pacote": "PCT", "pacotes": "PCT", "lt": "L", "litro": "L", "litros": "L",
                  "mt": "M", "metro": "M", "metros": "M", "par": "PAR", "pares": "PAR", "rolos": "ROLO", "resmas": "RESMA", "galões": "GALÃO",
                  "kits": "KIT", "jogos": "JOGO", "sacos": "SACO", "latas": "LATA", "frascos": "FRASCO", "tubos": "TUBO"}


def unidade_normalizada(texto: str) -> str:
    chave = texto.strip().lower().rstrip(".")
    return ROTULO_UNIDADE.get(chave, chave.upper())


def numero_quantidade(texto: str) -> float | None:
    """'1.500' -> 1500; '12,5' -> 12,5; '50' -> 50. None se não for número positivo."""
    texto = texto.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?|\d+,\d+", texto):
        texto = texto.replace(".", "").replace(",", ".")
    try:
        valor = float(texto)
    except ValueError:
        return None
    return valor if valor > 0 else None


def _item(descricao: str, quantidade: float | None, unidade: str) -> dict[str, object]:
    """`quantidade` é sempre um número (1 se não foi informada); `quantidade_informada` diz se o usuário a digitou."""
    descricao = descricao.strip(" -–—,;:")
    return {"descricao": descricao[:1].upper() + descricao[1:], "quantidade": quantidade if quantidade is not None else 1.0,
            "unidade": unidade or "UN", "quantidade_informada": quantidade is not None}


UNIDADES_MEDIDA = ("kg", "g", "l", "lt", "litro", "litros", "m", "mt", "metro", "metros")  # também aparecem como especificação do item ("papel 75 g", "fita 20 m")
UNIDADES_CONTAGEM = tuple(u for u in UNIDADES if u not in UNIDADES_MEDIDA)


def _alternativas(unidades: tuple[str, ...]) -> str:
    return "|".join(sorted((re.escape(u) for u in unidades), key=len, reverse=True))


def interpretar_linha(linha: str) -> dict[str, object] | None:
    """Uma linha da lista -> {descricao, quantidade, unidade, quantidade_informada}.

    Só reconhece a quantidade quando não há dúvida, para não estragar especificações do item ("24x34 caixa c/ 250", "papel 75 g", "fita 20 m x 30"):
    - depois de um separador: 'caneta azul - 50', 'caneta azul; 100 cx', 'caneta azul : 50', 'caneta azul qtd 50', 'caneta azul x 50' (o 'x' só
      conta se a palavra antes dele não tiver número). Com unidade de medida (g, kg, l, m) depois do número, não é quantidade;
    - no começo: '50 canetas azuis', '50 un caneta azul', '5 litros de tinta' (o número vem solto, sem letra colada: '500g café' é medida);
    - no fim, com unidade de contagem: 'caneta azul 50 un', 'papel a4 10 resmas'.
    Nos demais casos a linha inteira é a descrição, e a quantidade pode ser digitada na tabela de conferência."""
    texto = re.sub(r"\s+", " ", linha.replace("\t", " ; ")).strip(" -•*;")
    if not texto:
        return None
    todas, contagem = _alternativas(UNIDADES), _alternativas(UNIDADES_CONTAGEM)
    quantidade, unidade = None, "UN"
    casamento = re.search(rf"(?:\s[-–—]\s|\s*[;|:]\s*|\s+(?:qtd|qtde|quant|quantidade)\.?\s*:?\s*)(\d[\d.,]*)\s*({contagem})?\.?\s*$", texto, re.I)
    com_x = re.search(rf"(?<![\d/])\s+[xX]\s+(\d[\d.,]*)\s*({contagem})?\.?\s*$", texto) if not casamento else None
    if com_x and any(c.isdigit() for c in texto[:com_x.start()].split()[-1:] and texto[:com_x.start()].split()[-1]):
        com_x = None  # "1/2 x 20", "20m x 30": é medida, não quantidade
    achado = casamento or com_x
    if achado and numero_quantidade(achado.group(1)):
        quantidade = numero_quantidade(achado.group(1))
        unidade = unidade_normalizada(achado.group(2)) if achado.group(2) else "UN"
        texto = texto[:achado.start()]
    else:
        inicio = re.match(rf"^(\d[\d.,]*)\s+(?:({todas})\.?\s+)?(?:de\s+)?(.+)$", texto, re.I)
        if inicio and numero_quantidade(inicio.group(1)) and not re.match(r"^\d+\s*[xX/]\s*\d", texto) and not re.match(r"^\d+\s+(?:x|/)\s", texto, re.I):
            quantidade = numero_quantidade(inicio.group(1))
            unidade = unidade_normalizada(inicio.group(2)) if inicio.group(2) else "UN"
            texto = inicio.group(3)
        else:
            fim = re.search(rf"\s(\d[\d.,]*)\s*({contagem})\.?\s*$", texto, re.I)
            if fim and numero_quantidade(fim.group(1)) and texto[:fim.start()].strip():
                quantidade = numero_quantidade(fim.group(1))
                unidade = unidade_normalizada(fim.group(2))
                texto = texto[:fim.start()]
    if not texto.strip(" -–—,;:"):
        return None
    return _item(texto, quantidade, unidade)


def interpretar_lista(texto: str) -> list[dict[str, object]]:
    return [item for item in (interpretar_linha(linha) for linha in str(texto or "").splitlines()) if item]


def detectar_colunas(colunas: list[str]) -> tuple[str, str | None, str | None]:
    """(descrição, quantidade, unidade) pelo nome do cabeçalho; sem cabeçalho reconhecível, a 1ª coluna é a descrição e a 2ª a quantidade."""
    minusculas = {c: str(c).strip().lower() for c in colunas}

    def achar(*palavras: str) -> str | None:
        return next((c for c, m in minusculas.items() if any(p in m for p in palavras)), None)

    descricao = achar("descri", "material", "item", "produto", "objeto") or colunas[0]
    quantidade = achar("quant", "qtd", "qtde") or (colunas[1] if len(colunas) > 1 and descricao == colunas[0] else None)
    unidade = achar("unid", "und", "medida")
    return descricao, quantidade, unidade


def itens_do_dataframe(dados, col_descricao: str | None = None, col_quantidade: str | None = None, col_unidade: str | None = None,
                       detectar: bool = True) -> list[dict[str, object]]:
    """Planilha (pandas.DataFrame) -> itens. Sem colunas informadas, procura pelo nome do cabeçalho."""
    if dados is None or dados.empty:
        return []
    colunas = [str(c) for c in dados.columns]
    if detectar and col_descricao is None:
        col_descricao, col_quantidade, col_unidade = detectar_colunas(colunas)
    if col_descricao is None:
        return []
    itens = []
    for _, linha in dados.iterrows():
        descricao = str(linha[col_descricao]).strip()
        if not descricao or descricao.lower() in ("nan", "none"):
            continue
        quantidade = numero_quantidade(str(linha[col_quantidade])) if col_quantidade else None
        unidade = str(linha[col_unidade]).strip() if col_unidade and str(linha[col_unidade]).strip().lower() not in ("", "nan", "none") else "UN"
        itens.append(_item(descricao, quantidade, unidade_normalizada(unidade)))
    return itens


def _chave(descricao: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", descricao) if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.lower().split())


def unir_repetidos(itens: list[dict[str, object]]) -> list[dict[str, object]]:
    """Mesma descrição (sem diferenciar maiúsculas/acentos) e mesma unidade: um item só, com as quantidades somadas. Mantém a ordem."""
    saida: dict[tuple[str, str], dict[str, object]] = {}
    for item in itens:
        chave = (_chave(str(item["descricao"])), str(item["unidade"]))
        if chave not in saida:
            saida[chave] = dict(item)
        else:
            atual = saida[chave]
            atual["quantidade"] = float(atual["quantidade"]) + float(item["quantidade"]) if item.get("quantidade_informada") and atual.get("quantidade_informada") \
                else float(item["quantidade"]) if item.get("quantidade_informada") else float(atual["quantidade"])
            atual["quantidade_informada"] = bool(atual.get("quantidade_informada") or item.get("quantidade_informada"))
    return list(saida.values())


def formatar_quantidade(valor: object) -> str:
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(valor or "")
    return f"{int(numero)}" if numero == int(numero) else f"{numero:g}".replace(".", ",")


# ---------- totais (Cotação Rápida / Notas Fiscais) ----------

def anexar_pedido(resultado: dict, item: dict[str, object]) -> dict:
    """Guarda no resultado da pesquisa o que foi pedido: quantidade (só se o usuário informou) e unidade."""
    resultado["quantidade_pedida"] = float(item["quantidade"]) if item.get("quantidade_informada") else None
    resultado["unidade_pedida"] = str(item.get("unidade") or "UN")
    return resultado


def tem_quantidades(resultados: list[dict]) -> bool:
    return any(r.get("quantidade_pedida") for r in resultados)


def valor_total_item(resultado: dict) -> float | None:
    """Média unitária x quantidade pedida; None sem quantidade ou sem preços."""
    quantidade = resultado.get("quantidade_pedida")
    estatisticas = resultado.get("stats")
    if not quantidade or not estatisticas:
        return None
    return round(float(estatisticas["media"]) * float(quantidade), 2)


def valor_total_orcamento(resultados: list[dict]) -> float:
    return round(sum(valor_total_item(r) or 0.0 for r in resultados), 2)
