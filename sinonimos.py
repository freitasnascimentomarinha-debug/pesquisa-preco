"""Nome de mercado dos itens e conferência do nome do produto anunciado.

1. SINÔNIMOS: como o item é pedido na repartição x como as lojas o anunciam ("caneta piloto" = marcador para quadro branco; "papel contact"
   = plástico/papel adesivo). Cada entrada diz como BUSCAR, que nomes de produto ACEITAR e que palavras EXCLUEM o anúncio
   (ex.: "esferográfica" nunca é caneta piloto; "toalha" nunca é papel contact).
2. confere_nome(item, nome): o nome do produto (título da página, card da listagem, JSON-LD) é do item pedido? Sem sinônimo, exige a
   1ª palavra do item (o substantivo: "papel", "caneta", "lâmpada") e pelo menos 60% das palavras; "papel toalha" não passa por "papel contact".
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


def entrada(item: str) -> dict | None:
    """A entrada de sinônimo que vale para o item (a do nome mais longo que aparece nele), ou None."""
    texto = normalizar(item)
    melhor, tamanho = None, 0
    for registro in SINONIMOS:
        for nome in registro["nomes"]:
            nome_norm = normalizar(nome).strip()
            if f" {nome_norm} " in texto and len(nome_norm) > tamanho:
                melhor, tamanho = registro, len(nome_norm)
    return melhor


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


def _palavras_chave(item: str) -> list[str]:
    return [p for p in normalizar(item).split() if p not in VAZIAS and (len(p) > 2 or any(c.isdigit() for c in p))]


def confere_nome(item: str, nome: str) -> bool:
    """O nome do produto anunciado corresponde ao item pedido?
    Com sinônimo: precisa casar um dos conjuntos 'aceitar' e nenhuma palavra de 'excluir'.
    Sem sinônimo: a 1ª palavra do item (o substantivo) e pelo menos 60% das palavras do item (no máximo 4)."""
    nome_norm = normalizar(nome)
    if not nome_norm.strip():
        return False
    registro = entrada(item)
    if registro:
        if any(_tem(nome_norm, termo) for termo in registro["excluir"]):
            return False
        return any(all(_tem(nome_norm, palavra) for palavra in conjunto) for conjunto in registro["aceitar"])
    palavras = _palavras_chave(embalagem.base(item))  # medida e embalagem ("500ml", "caixa") são conferidas à parte, em embalagem.py
    if not palavras:
        return True
    if not _tem(nome_norm, palavras[0]):
        return False
    acertos = sum(1 for p in palavras if _tem(nome_norm, p))
    return acertos >= max(1, min(math.ceil(0.6 * len(palavras)), 4))  # 60% das palavras; descrição longa: no máximo 4 exigidas


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
