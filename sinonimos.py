"""Nome de mercado dos itens e conferência do nome do produto anunciado.

1. SINÔNIMOS: como o item é pedido na repartição x como as lojas o anunciam ("caneta piloto" = marcador para quadro branco; "papel contact"
   = plástico/papel adesivo). Cada entrada diz como BUSCAR, que nomes de produto ACEITAR e que palavras EXCLUEM o anúncio
   (ex.: "esferográfica" nunca é caneta piloto; "toalha" nunca é papel contact).
2. confere_nome(item, nome): o nome do produto (título da página, card da listagem, JSON-LD) é do item pedido? Sem sinônimo, exige a
   1ª palavra do item (o substantivo: "papel", "caneta", "lâmpada") e pelo menos metade das palavras; "papel toalha" não passa por "papel contact".
Sem IA e sem internet. Para acrescentar um termo, basta uma nova entrada em SINONIMOS."""
import math
import re
import unicodedata

import embalagem

SINONIMOS = [
    {"nomes": ["caneta piloto", "caneta para quadro branco", "caneta quadro branco", "piloto quadro branco", "marcador quadro branco"],
     "busca": "marcador para quadro branco",
     "aceitar": [["marcador", "quadro"], ["pincel", "quadro"], ["caneta", "quadro"], ["marcador", "branco", "apagavel"], ["pincel", "quadro", "branco"]],
     "excluir": ["esferografica", "esferografic", "gel", "rollerball", "roller", "tinteiro", "permanente", "marca texto", "cd"]},
    {"nomes": ["pincel atomico", "caneta pincel atomico"],
     "busca": "pincel atômico marcador permanente",
     "aceitar": [["pincel", "atomico"], ["marcador", "permanente"]],
     "excluir": ["quadro branco", "esferografica"]},
    {"nomes": ["papel contact", "plastico contact", "contact transparente", "contact"],
     "busca": "papel adesivo contact",
     "aceitar": [["contact"], ["papel", "adesivo"], ["plastico", "adesivo"], ["vinil", "adesivo"]],
     "excluir": ["toalha", "higienico", "guardanapo", "filtro", "sulfite", "fotografico", "seda", "manteiga", "aluminio", "lente de contato"]},
    {"nomes": ["fita durex", "durex"],
     "busca": "fita adesiva transparente",
     "aceitar": [["fita", "adesiva"], ["durex"], ["fita", "transparente"]],
     "excluir": ["dupla face", "crepe", "isolante", "silver tape"]},
    {"nomes": ["post it", "postit", "post-it"],
     "busca": "bloco adesivo de recado",
     "aceitar": [["bloco", "adesivo"], ["post"], ["nota", "adesiva"], ["recado", "adesivo"]],
     "excluir": []},
    {"nomes": ["bombril", "palha de aco"],
     "busca": "lã de aço",
     "aceitar": [["la", "aco"], ["palha", "aco"], ["esponja", "aco"]],
     "excluir": ["inox", "dupla face"]},
    {"nomes": ["cotonete"],
     "busca": "haste flexível com pontas de algodão",
     "aceitar": [["haste", "flexivel"], ["cotonete"]],
     "excluir": []},
    {"nomes": ["marca texto", "caneta marca texto"],
     "busca": "marca texto",
     "aceitar": [["marca", "texto"], ["marcador", "texto"]],
     "excluir": ["quadro branco", "permanente", "esferografica"]},
    {"nomes": ["fita crepe"],
     "busca": "fita crepe",
     "aceitar": [["fita", "crepe"]],
     "excluir": ["isolante", "durex"]},
    {"nomes": ["clips", "clipes", "clipe"],
     "busca": "clips para papel",
     "aceitar": [["clip"], ["clipe"]],
     "excluir": ["cabelo", "prendedor de cabelo"]},
    {"nomes": ["corretivo liquido", "corretivo em fita", "corretivo"],
     "busca": "corretivo escolar",
     "aceitar": [["corretivo"]],
     "excluir": ["facial", "maquiagem", "olheira", "pele"]},
    {"nomes": ["envelope pardo"],
     "busca": "envelope pardo kraft",
     "aceitar": [["envelope", "pardo"], ["envelope", "kraft"]],
     "excluir": ["caixa de pizza", "pizza"]},
    {"nomes": ["agua sanitaria", "candida"],
     "busca": "água sanitária",
     "aceitar": [["agua", "sanitaria"], ["alvejante"], ["candida"]],
     "excluir": []},
]

# palavras que não ajudam a reconhecer o produto
VAZIAS = {"de", "da", "do", "das", "dos", "para", "com", "sem", "em", "e", "a", "o", "as", "os", "tipo", "cor", "c", "p", "x", "n", "no", "na"}


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " " + " ".join(re.findall(r"[a-z0-9]+", texto)) + " "


def _raiz(palavra: str) -> str:
    """Raiz simples: sem plural e com no máximo 6 letras ('envelopes' -> 'envelo', 'transparente' -> 'transp')."""
    if len(palavra) > 3 and palavra.endswith("s"):
        palavra = palavra[:-1]
    return palavra[:6]


def _tem(texto_norm: str, termo: str) -> bool:
    """O termo (uma ou mais palavras) aparece no texto, palavra a palavra pelo começo ('quadro' casa 'quadros')."""
    palavras_texto = texto_norm.split()
    for palavra in termo.split():
        raiz = _raiz(palavra)
        if not any(p.startswith(raiz) for p in palavras_texto):
            return False
    return True


APRENDIDOS: dict[str, dict] = {}  # nomes aprendidos com o uso (memória no GitHub, chave "nomes"); carregados no início de cada pesquisa


def carregar_aprendidos(nomes: dict | None) -> None:
    APRENDIDOS.clear()
    APRENDIDOS.update(nomes or {})


def _melhor_fixo(texto: str) -> tuple[dict | None, int]:
    melhor, tamanho = None, 0
    for registro in SINONIMOS:
        for nome in registro["nomes"]:
            nome_norm = normalizar(nome).strip()
            if f" {nome_norm} " in texto and len(nome_norm) > tamanho:
                melhor, tamanho = registro, len(nome_norm)
    return melhor, tamanho


def entrada(item: str) -> dict | None:
    """A entrada de sinônimo que vale para o item: a da tabela fixa (nome mais longo que aparece nele) somada à aprendida com o uso
    (busca ensinada, nomes aceitos e palavras que recusam o anúncio). None se não houver nenhuma."""
    texto = normalizar(item)
    fixo, _ = _melhor_fixo(texto)
    aprendido_chave = max((c for c in APRENDIDOS if f" {c} " in texto), key=len, default="")
    if not fixo and not aprendido_chave:
        return None
    registro = {"nomes": list(fixo["nomes"]) if fixo else [], "busca": fixo["busca"] if fixo else "",
                "aceitar": [list(c) for c in fixo["aceitar"]] if fixo else [], "excluir": list(fixo["excluir"]) if fixo else []}
    if aprendido_chave:
        aprendido = APRENDIDOS[aprendido_chave]
        registro["nomes"].append(aprendido_chave)
        if aprendido.get("busca"):
            registro["busca"] = aprendido["busca"]
        registro["aceitar"] += [list(c) for c in aprendido.get("aceitar", []) if c]
        registro["excluir"] += [t for t, n in aprendido.get("excluir", {}).items() if n >= 1 and t not in registro["excluir"]]
    if not registro["busca"]:
        registro["busca"] = (aprendido_chave or str(item)).strip()
    return registro


def termo_busca(item: str) -> str:
    """Troca o nome do item pelo nome de mercado na busca, mantendo o resto ('caneta piloto azul' -> 'marcador para quadro branco azul')."""
    registro = entrada(item)
    if not registro:
        return str(item or "").strip()
    texto = normalizar(item)
    for nome in sorted(registro["nomes"], key=len, reverse=True):  # tira todos os nomes do item que aparecem, do mais longo ao mais curto
        nome_norm = normalizar(nome).strip()
        while f" {nome_norm} " in texto:
            texto = texto.replace(f" {nome_norm} ", " ", 1)
    ja_na_busca = set(normalizar(registro["busca"]).split())
    resto = [p for p in texto.split() if p not in ja_na_busca]
    return (registro["busca"] + (" " + " ".join(resto) if resto else "")).strip()


def _resto_do_item(item: str, registro: dict) -> list[str]:
    """Palavras do item (sem medida/embalagem) que não fazem parte dos nomes da entrada de sinônimo."""
    texto = normalizar(embalagem.base(item))
    for nome in sorted(registro["nomes"], key=len, reverse=True):
        nome_norm = normalizar(nome).strip()
        while nome_norm and f" {nome_norm} " in texto:
            texto = texto.replace(f" {nome_norm} ", " ", 1)
    return [p for p in texto.split() if p not in VAZIAS and (len(p) > 2 or any(c.isdigit() for c in p))]


def _palavras_chave(item: str) -> list[str]:
    return [p for p in normalizar(item).split() if p not in VAZIAS and (len(p) > 2 or any(c.isdigit() for c in p))]


def confere_nome(item: str, nome: str) -> bool:
    """O nome do produto anunciado corresponde ao item pedido?
    Com sinônimo: precisa casar um dos conjuntos 'aceitar' e nenhuma palavra de 'excluir'.
    Sem sinônimo: a 1ª palavra do item (o substantivo) e pelo menos metade das palavras do item (no máximo 3)."""
    nome_norm = normalizar(nome)
    if not nome_norm.strip():
        return False
    registro = entrada(item)
    if registro:
        if any(_tem(nome_norm, termo) for termo in registro["excluir"]):
            return False
        if registro["aceitar"]:
            if not any(all(_tem(nome_norm, palavra) for palavra in conjunto) for conjunto in registro["aceitar"]):
                return False
            # o que sobra do item além do apelido (cor, tipo: 'azul' em 'caneta piloto azul') também precisa aparecer, na maioria
            resto = _resto_do_item(item, registro)
            return not resto or sum(1 for p in resto if _tem(nome_norm, p)) >= math.ceil(0.5 * len(resto))
    palavras = _palavras_chave(embalagem.base(item))  # medida e embalagem ("500ml", "caixa") são conferidas à parte, em embalagem.py
    palavras = [p for p in palavras if not p.isdigit()] or palavras  # números soltos ('26/6') não contam: cada loja escreve de um jeito
    if not palavras:
        return True
    if not _tem(nome_norm, palavras[0]):
        return False
    acertos = sum(1 for p in palavras if _tem(nome_norm, p))
    return acertos >= max(1, min(math.ceil(0.5 * len(palavras)), 3))  # metade das palavras; descrição longa: no máximo 3 exigidas


def excluido(item: str, texto: str) -> bool:
    """O resultado do buscador (título/trecho) traz palavra que exclui o item e nenhum nome aceito ('esferográfica' para caneta piloto)."""
    registro = entrada(item)
    if not registro or not registro["excluir"]:
        return False
    texto_norm = normalizar(texto)
    if any(all(_tem(texto_norm, palavra) for palavra in conjunto) for conjunto in registro["aceitar"]):
        return False
    return any(_tem(texto_norm, termo) for termo in registro["excluir"])


def pontuacao(item: str, nome: str) -> int:
    """Quantas palavras do item (sem medida/embalagem) aparecem no nome do produto: desempata produtos aceitos de uma mesma lista."""
    nome_norm = normalizar(nome)
    return sum(1 for p in _palavras_chave(embalagem.base(item)) if _tem(nome_norm, p))



# ---------- aprendizado de nomes (guardado na memória, chave "nomes") ----------

PALAVRAS_DE_LOJA = {"loja", "lojas", "compre", "comprar", "compra", "preco", "precos", "oferta", "ofertas", "frete", "gratis", "atacado", "varejo",
                    "papelaria", "online", "promocao", "melhor", "menor", "entrega", "brasil", "produto", "produtos", "venda", "vendas",
                    "unidade", "unidades", "pacote", "caixa", "kit", "cores", "sortido", "sortidas", "original", "novo", "nova", "site", "oficial"}
MAX_RECUSADOS = 30


def chave_aprendizado(item: str) -> str:
    """Onde o que se aprende sobre o item fica guardado: as 2 primeiras palavras do nome sem medida/embalagem
    ('caneta piloto azul' -> 'caneta piloto'); vale para as variações do mesmo item (outras cores, medidas)."""
    return " ".join(_palavras_chave(embalagem.base(item))[:2])


def _palavras_distintas(nome: str, item: str) -> list[str]:
    """Palavras do nome do anúncio que não são do item, nem medida, nem 'palavra de loja' (só letras, 5+)."""
    do_item = _palavras_chave(item)
    saida = []
    for p in normalizar(nome).split():
        if len(p) < 5 or not p.isalpha() or p in PALAVRAS_DE_LOJA or p in VAZIAS:
            continue
        if any(_raiz(p).startswith(_raiz(i)[:5]) or _raiz(i).startswith(_raiz(p)[:5]) for i in do_item):
            continue
        if p not in saida:
            saida.append(p)
    return saida


def _registro_aprendido(nomes: dict, chave: str) -> dict:
    return nomes.setdefault(chave, {"busca": "", "aceitar": [], "excluir": {}, "recusados": [], "origem": ""})


def registrar_recusado(nomes: dict, item: str, titulo: str) -> None:
    """Anúncio recusado na pesquisa porque o nome não bateu com o item: base para o sistema sugerir o nome usado pelas lojas."""
    chave = chave_aprendizado(item)
    titulo = re.sub(r"\s+", " ", str(titulo or "")).strip()[:150]
    if not chave or not titulo:
        return
    registro = _registro_aprendido(nomes, chave)
    if titulo not in registro["recusados"]:
        registro["recusados"] = (registro["recusados"] + [titulo])[-MAX_RECUSADOS:]


def sugerir(nomes: dict, item: str, minimo: int = 3) -> dict | None:
    """Se os anúncios recusados para o item repetem o mesmo nome ('marcador', 'quadro', 'branco' em metade ou mais deles),
    sugere que é assim que as lojas chamam o item. {'palavras': [...], 'busca': '...', 'exemplos': [...]} ou None."""
    registro = nomes.get(chave_aprendizado(item))
    if not registro or len(registro.get("recusados", [])) < minimo or registro.get("aceitar"):
        return None
    titulos = registro["recusados"]
    contagem: dict[str, int] = {}
    for titulo in titulos:
        for palavra in _palavras_distintas(titulo, item):
            contagem[palavra] = contagem.get(palavra, 0) + 1
    excluidas = set(registro.get("excluir", {}))
    comuns = [p for p, n in sorted(contagem.items(), key=lambda x: -x[1]) if n >= max(minimo, math.ceil(len(titulos) / 2)) and p not in excluidas][:3]
    if not comuns:
        return None
    exemplos = [t for t in titulos if all(_tem(normalizar(t), p) for p in comuns)][:3]
    # a busca sugerida segue um anúncio real: as palavras comuns + as que lembram o nome do item ('marcador' de 'caneta marcadora'),
    # sem cor/medida do item (vale para as outras variações)
    referencia = normalizar(exemplos[0] if exemplos else titulos[-1]).split()
    da_chave = _palavras_chave(chave_aprendizado(item))
    ordem = []
    for palavra in referencia:
        parecida = any(_raiz(palavra)[:5] == _raiz(c)[:5] for c in da_chave) and palavra.isalpha() and len(palavra) >= 4
        if (palavra in comuns or parecida) and palavra not in ordem:
            ordem.append(palavra)
    ordem = ordem[:5] or comuns
    return {"palavras": comuns, "busca": " ".join(ordem), "exemplos": exemplos}


def ensinar(nomes: dict, nome_reparticao: str, nome_lojas: str = "", recusar: list[str] | None = None, origem: str = "ensinado") -> str:
    """Grava: quando o item tiver `nome_reparticao`, buscar `nome_lojas` e aceitar anúncios com as palavras dele; recusar os termos dados."""
    chave = " ".join(_palavras_chave(embalagem.base(nome_reparticao))) or normalizar(nome_reparticao).strip()
    if not chave:
        return ""
    registro = _registro_aprendido(nomes, chave)
    if nome_lojas.strip():
        registro["busca"] = nome_lojas.strip()
        conjunto = _palavras_chave(nome_lojas)[:3]
        if conjunto and conjunto not in registro["aceitar"]:
            registro["aceitar"].append(conjunto)
    for termo in recusar or []:
        termo = normalizar(termo).strip()
        if termo:
            registro["excluir"][termo] = registro["excluir"].get(termo, 0) + 1
    registro["origem"] = origem
    return chave


def aprender_exclusoes(nomes: dict, item: str, nomes_excluidos: list[str], nomes_mantidos: list[str]) -> list[str]:
    """O usuário disse que esses anúncios não são o item: as palavras deles que não aparecem nos anúncios mantidos passam a recusar
    anúncios desse item nas próximas pesquisas. Devolve as palavras aprendidas."""
    chave = chave_aprendizado(item)
    if not chave:
        return []
    mantidas = {p for nome in nomes_mantidos for p in normalizar(nome).split()}
    registro = _registro_aprendido(nomes, chave)
    aprendidas = []
    for nome in nomes_excluidos:
        for palavra in _palavras_distintas(nome, item):
            if palavra in mantidas:
                continue
            registro["excluir"][palavra] = registro["excluir"].get(palavra, 0) + 1
            if palavra not in aprendidas:
                aprendidas.append(palavra)
    return aprendidas


def esquecer(nomes: dict, chave: str) -> None:
    nomes.pop(chave, None)
