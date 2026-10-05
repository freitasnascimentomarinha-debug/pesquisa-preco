"""Unidade de fornecimento e medida do item ("arroz branco 5kg", "detergente 500ml", "sabão em pó caixa 1 kg", "papel A4 resma").

- `base(item)`: o nome sem medida e sem palavra de embalagem (para conferir se a página fala do mesmo produto);
- `termo_busca(item)`: o texto usado nas buscas: medidas juntas ("1 kg" -> "1kg") e sem ruído ("UN", "unidade", "peça");
- `medidas(texto)`: medidas encontradas num texto, convertidas para a mesma base (g, ml, mm, W, V, unidades por embalagem);
- `confere(item, texto)`: 'igual' (a página tem a mesma medida), 'diferente' (só tem outra medida da mesma grandeza) ou 'sem_medida'.
Sem IA e sem internet."""
import re
import unicodedata

# unidade -> (grandeza, fator para a unidade base)
UNIDADES = {
    "kg": ("massa", 1000.0), "kgs": ("massa", 1000.0), "quilo": ("massa", 1000.0), "quilos": ("massa", 1000.0),
    "g": ("massa", 1.0), "gr": ("massa", 1.0), "grs": ("massa", 1.0), "grama": ("massa", 1.0), "gramas": ("massa", 1.0), "mg": ("massa", 0.001),
    "l": ("volume", 1000.0), "lt": ("volume", 1000.0), "lts": ("volume", 1000.0), "litro": ("volume", 1000.0), "litros": ("volume", 1000.0),
    "ml": ("volume", 1.0),
    "m": ("comprimento", 1000.0), "mt": ("comprimento", 1000.0), "mts": ("comprimento", 1000.0), "metro": ("comprimento", 1000.0),
    "metros": ("comprimento", 1000.0), "cm": ("comprimento", 10.0), "mm": ("comprimento", 1.0),
    "w": ("potência", 1.0), "watt": ("potência", 1.0), "watts": ("potência", 1.0),
    "v": ("tensão", 1.0), "volt": ("tensão", 1.0), "volts": ("tensão", 1.0),
}
# palavras de embalagem / unidade de fornecimento (sem acento)
EMBALAGENS = {
    "caixa", "cx", "pacote", "pct", "pc", "rolo", "rl", "resma", "balde", "galao", "gl", "fardo", "frasco", "fr", "saco", "sc", "kit", "par",
    "duzia", "lata", "lt", "garrafa", "pote", "refil", "bisnaga", "tubo", "bobina", "cartela", "display", "embalagem", "emb", "bloco", "maco",
    "unidade", "unidades", "un", "und", "unid", "peca", "pecas", "pca",
}
# não ajudam na busca (todo produto é vendido "por unidade")
RUIDO_BUSCA = {"un", "und", "unid", "unidade", "unidades", "peca", "pecas", "pca", "emb", "embalagem"}

_RE_MEDIDA = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kgs?|quilos?|grs?|gramas?|mg|g|lts?|litros?|ml|l|mts?|metros?|cm|mm|m|watts?|w|volts?|v)(?![a-z])")
_RE_QTD = re.compile(r"(?:c/|com|cx|caixa|pct|pacote|fardo|kit|display)\s*(?:c/|com)?\s*(\d+)\s*(?:un|und|unid|unidades?|pecas?|pcs?|folhas?|fls?|rolos?)?(?![a-z0-9])"
                     r"|(\d+)\s*(?:un|und|unid|unidades|pecas|pcs|folhas|fls|rolos)(?![a-z])")


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def medidas(texto: str) -> list[tuple[str, float]]:
    """[(grandeza, valor na unidade base)]: '5kg' -> ('massa', 5000); '500 ml' -> ('volume', 500); 'c/ 12' -> ('quantidade', 12)."""
    texto = _sem_acento(texto)
    achadas = []
    for numero, unidade in _RE_MEDIDA.findall(texto):
        grandeza, fator = UNIDADES[unidade]
        achadas.append((grandeza, round(float(numero.replace(",", ".")) * fator, 4)))
    for qtd1, qtd2 in _RE_QTD.findall(texto):
        qtd = qtd1 or qtd2
        if qtd and int(qtd) > 1:
            achadas.append(("quantidade", float(qtd)))
    return achadas


def embalagens(item: str) -> list[str]:
    return [p for p in re.findall(r"[a-z0-9/]+", _sem_acento(item)) if p in EMBALAGENS]


def base(item: str) -> str:
    """Nome do produto sem medidas, quantidades e palavras de embalagem: 'Sabão em pó caixa 1 kg' -> 'sabão em pó'."""
    texto = _RE_MEDIDA.sub(" ", _sem_acento(item))
    texto = _RE_QTD.sub(" ", texto)
    palavras = [p for p in re.findall(r"[a-z0-9]+", texto) if p not in EMBALAGENS and p not in ("c", "com")]
    # devolve com a grafia original (acentos) quando possível
    originais = re.findall(r"\w+", str(item or ""))
    mapa = {_sem_acento(o): o for o in originais}
    return " ".join(mapa.get(p, p) for p in palavras).strip() or str(item or "").strip()


def termo_busca(item: str) -> str:
    """Texto para as buscas: medida junta ao número ('1 kg' -> '1kg') e sem palavras que só atrapalham ('UN', 'unidade', 'peça')."""
    texto = re.sub(r"(\d+(?:[.,]\d+)?)\s+(kg|g|gr|mg|l|lt|ml|m|cm|mm|w|v)\b", r"\1\2", str(item or ""), flags=re.IGNORECASE)
    palavras = [p for p in texto.split() if _sem_acento(p).strip(".,;:") not in RUIDO_BUSCA]
    return " ".join(palavras).strip() or str(item or "").strip()


def descrever(item: str) -> str:
    """Resumo para o log: 'medida 5 kg; embalagem caixa'. Vazio se o item não tem medida nem embalagem."""
    partes = []
    vistos = set()
    for grandeza, valor in medidas(item):
        if (grandeza, valor) in vistos:
            continue
        vistos.add((grandeza, valor))
        if grandeza == "massa":
            partes.append(f"{valor / 1000:g} kg" if valor >= 1000 else f"{valor:g} g")
        elif grandeza == "volume":
            partes.append(f"{valor / 1000:g} L" if valor >= 1000 else f"{valor:g} ml")
        elif grandeza == "comprimento":
            partes.append(f"{valor / 1000:g} m" if valor >= 1000 else f"{valor:g} mm")
        elif grandeza == "potência":
            partes.append(f"{valor:g} W")
        elif grandeza == "tensão":
            partes.append(f"{valor:g} V")
        else:
            partes.append(f"{valor:g} unidades por embalagem")
    texto = ("medida " + ", ".join(partes)) if partes else ""
    emb = [e for e in embalagens(item) if e not in RUIDO_BUSCA]
    if emb:
        texto += ("; " if texto else "") + "embalagem " + ", ".join(dict.fromkeys(emb))
    return texto


def confere(item: str, texto: str) -> str:
    """Compara as medidas do item com as do texto (título da página, nome do produto, trecho do buscador).
    'igual': o texto tem todas as medidas do item; 'diferente': o texto tem medida da mesma grandeza, mas outra; 'sem_medida': nada a comparar."""
    do_item = medidas(item)
    if not do_item:
        return "sem_medida"
    do_texto = medidas(texto)
    grandezas_texto = {g for g, _ in do_texto}
    comparaveis = [(g, v) for g, v in do_item if g in grandezas_texto]
    if not comparaveis:
        return "sem_medida"
    for grandeza, valor in comparaveis:
        if not any(g == grandeza and abs(v - valor) <= max(0.01 * valor, 0.001) for g, v in do_texto):
            return "diferente"
    return "igual"


def unidade_curta(item: str) -> str:
    """Para a coluna 'Unid.' do relatório: a medida/embalagem lida do item ('500 ml', '5 kg; caixa'), ou 'oferta' se não houver."""
    texto = descrever(item).replace("medida ", "").replace("embalagem ", "")
    return texto[:28] if texto else "oferta"
