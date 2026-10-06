"""Preço correto de uma página de produto e análise das ofertas da internet com as regras da Cotação Rápida.

Sem dependência do Streamlit: o módulo é usado pela página Web Scraping e pode ser testado isoladamente.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Callable

from cotacao_rapida import MAX_PRECOS, MIN_PRECOS, TOLERANCIA, estatisticas, remover_outliers, selecionar_precos

PRECO_MIN, PRECO_MAX = 0.5, 500_000
PRECOS_POR_ITEM_PADRAO = 3  # colunas de preço do relatório da pesquisa na internet (a Cotação Rápida usa 5)
SEM_ESTOQUE = ("outofstock", "soldout", "discontinued")
PRECO_DE_REFERENCIA = ("list", "strikethrough", "srp", "minimumadvertised", "installment")


def parse_preco(valor: object) -> float | None:
    """Converte número ou texto (1.299,90 / 1299.90 / R$ 12,5) em float; None se fora da faixa plausível."""
    if isinstance(valor, bool) or valor is None:
        return None
    if isinstance(valor, (int, float)):
        numero = float(valor)
    else:
        texto = re.sub(r"[^\d.,]", "", str(valor))
        if not texto:
            return None
        if "." in texto and "," in texto:
            decimal = "," if texto.rfind(",") > texto.rfind(".") else "."
            milhar = "." if decimal == "," else ","
            texto = texto.replace(milhar, "").replace(decimal, ".")
        elif "," in texto:
            texto = texto.replace(",", ".") if re.search(r",\d{1,2}$", texto) else texto.replace(",", "")
        elif "." in texto and re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
            texto = texto.replace(".", "")
        try:
            numero = float(texto)
        except ValueError:
            return None
    return numero if PRECO_MIN <= numero <= PRECO_MAX else None


def _tipos(no: dict) -> list[str]:
    tipo = no.get("@type", [])
    return [str(t).lower() for t in (tipo if isinstance(tipo, list) else [tipo])]


def _preco_da_especificacao(especificacao: object) -> float | None:
    """Preço à vista de um priceSpecification, ignorando parcelas e preços 'de' (riscados)."""
    for item in especificacao if isinstance(especificacao, list) else [especificacao]:
        if not isinstance(item, dict) or "billingduration" in {str(k).lower() for k in item}:
            continue
        if any(marca in str(item.get("priceType", "")).lower() for marca in PRECO_DE_REFERENCIA):
            continue
        preco = parse_preco(item.get("price"))
        if preco:
            return preco
    return None


def _precos_da_oferta(oferta: object) -> list[float]:
    if isinstance(oferta, list):
        return [p for item in oferta for p in _precos_da_oferta(item)]
    if not isinstance(oferta, dict):
        return []
    if any(marca in str(oferta.get("availability", "")).lower() for marca in SEM_ESTOQUE):
        return []
    if "aggregateoffer" in _tipos(oferta) and oferta.get("offers"):
        internos = _precos_da_oferta(oferta["offers"])
        if internos:
            return internos
    preco = parse_preco(oferta.get("price")) or parse_preco(oferta.get("lowPrice")) or _preco_da_especificacao(oferta.get("priceSpecification"))
    return [preco] if preco else []


def _produtos_jsonld(dado: object):
    if isinstance(dado, list):
        for item in dado:
            yield from _produtos_jsonld(item)
    elif isinstance(dado, dict):
        if "product" in _tipos(dado) or "productgroup" in _tipos(dado):
            yield dado
        # não desce em ItemList/itemListElement: produtos de uma listagem não são o produto da página
        for chave in ("@graph", "mainEntity", "hasVariant"):
            if chave in dado:
                yield from _produtos_jsonld(dado[chave])


ULTIMO_MOTIVO = {"texto": ""}  # por que preco_principal não devolveu preço (aparece no log)
RE_PRECO_ESCONDIDO = re.compile(r"informe\s+(o\s+)?(seu\s+)?cep|digite\s+(o\s+)?(seu\s+)?cep|insira\s+(o\s+)?(seu\s+)?cep|pre[cç]o\s+sob\s+consulta|"
                                r"consulte\s+(o\s+)?pre[cç]o|fa[cç]a\s+(o\s+)?login\s+para\s+ver|entre\s+para\s+ver\s+(o\s+)?pre[cç]o|cadastre-se\s+para\s+ver",
                                re.IGNORECASE)
RE_URL_DE_BUSCA = re.compile(r"[?&](q|s|query|busca|search|termo|palavra_busca|text|ft)=|/(busca|search|pesquisa|buscar|catalogsearch|categoria|categorias|departamento)(/|$|\?)",
                             re.IGNORECASE)


def eh_url_de_busca(url: str) -> bool:
    """Endereço de página de busca ou de categoria da loja (vários produtos), e não de um produto."""
    return bool(RE_URL_DE_BUSCA.search(str(url or "")))


def preco_principal(html: str, alternativa: Callable[[str], list[float]] | None = None, item: str = "", url: str = "") -> dict | None:
    """O preço do produto anunciado na página, do mais ao menos confiável.

    1. Oferta do produto em JSON-LD (schema.org): a mais barata em estoque; parcelas e preços riscados são ignorados.
    2. Metadados (product:price:amount, itemprop="price").
    3. Listagem de produtos: com o nome do `item`, acha na lista o(s) produto(s) que o citam e usa o preço dele(s).
    4. `alternativa` (heurísticas de texto/classes): usa a mediana dos valores e marca a confiança como baixa.
    Com `item`, o produto precisa ter o nome do item (sinonimos.confere_nome). Em página de busca/categoria (3+ produtos ou endereço de busca),
    só vale o produto da lista que cita o item: a mediana dos valores do texto misturaria produtos, filtros de faixa de preço e frete.
    Loja que esconde o preço (pede CEP/login) não tem a mediana do texto aceita."""
    from bs4 import BeautifulSoup

    import sinonimos

    ULTIMO_MOTIVO["texto"] = ""
    soup = BeautifulSoup(html, "html.parser")
    cards = _cards_da_listagem(soup)
    listagem = len(cards) >= MIN_CARDS_LISTAGEM or eh_url_de_busca(url)
    for marcador in soup.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(marcador.string or marcador.get_text() or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for produto in _produtos_jsonld(dados):
            nome_produto = str(produto.get("name") or "")
            if item and nome_produto and not sinonimos.confere_nome(item, nome_produto):
                continue  # produto de outra coisa (vitrine, "compre junto"): não é o item pedido
            precos = _precos_da_oferta(produto.get("offers"))
            if precos:
                return {"preco": min(precos), "origem": "JSON-LD (oferta do produto)", "confianca": "alta", "nome": str(produto.get("name") or "")[:150]}

    for meta in ([] if listagem else soup.find_all("meta")):  # em listagem, o metadado de preço não diz de qual produto é
        propriedade = str(meta.get("property") or meta.get("name") or meta.get("itemprop") or "").lower()
        if propriedade in ("product:price:amount", "og:price:amount", "product:sale_price:amount", "price", "twitter:data1"):
            preco = parse_preco(meta.get("content"))
            if preco and (propriedade != "twitter:data1" or "R$" in str(meta.get("content"))):
                return {"preco": preco, "origem": "metadado da página", "confianca": "alta", "nome": ""}
    for elemento in ([] if listagem else soup.select("[itemprop='price']")):
        preco = parse_preco(elemento.get("content") or elemento.get("data-price") or elemento.get_text(strip=True))
        if preco:
            return {"preco": preco, "origem": "itemprop=price", "confianca": "alta", "nome": ""}

    if item:
        achado = preco_na_listagem(soup, item, url, cards)
        if achado:
            return achado

    if listagem:
        ULTIMO_MOTIVO["texto"] = "página de busca/listagem sem o produto pedido"
        return None
    if alternativa and RE_PRECO_ESCONDIDO.search(soup.get_text(" ", strip=True)[:20000]):
        ULTIMO_MOTIVO["texto"] = "a loja esconde o preço (pede CEP ou login)"
        return None
    if alternativa:
        valores = sorted(set(alternativa(html)))
        if valores:  # qualquer valor do texto serve, inclusive de listagem (confiança baixa, avisada no relatório)
            return {"preco": valores[len(valores) // 2], "origem": "texto da página (mediana dos valores)", "confianca": "baixa", "nome": ""}
    return None


RE_PRECO_TEXTO = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})")
RE_PARCELA = re.compile(r"\b\d{1,2}\s*x\b|parcela|sem juros", re.IGNORECASE)
RE_CLASSE_RISCADO = re.compile(r"old|antigo|riscad|strike|original|from|list-?price|price-?de\b|was\b|de-?por", re.IGNORECASE)
RE_FRASES_DE_PRECO = re.compile(r"a partir de|por apenas|por|de|à vista|a vista|no pix|no boleto|em até|em ate|sem juros|economize|cada|unidade|un\.?|oferta|promoção|promocao|frete grátis|frete gratis", re.IGNORECASE)
MIN_CARDS_LISTAGEM = 3


def _palavras(texto: str) -> set[str]:
    """Palavras sem acento, minúsculas e sem plural simples ('Fitas Isolantes' -> fita, isolante)."""
    import unicodedata

    texto = "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower()) if unicodedata.category(c) != "Mn")
    return {(p[:-1] if len(p) > 3 and p.endswith("s") else p) for p in re.findall(r"[a-z0-9]+", texto) if len(p) > 2 or p.isdigit()}


def _preco_do_card(card) -> float | None:
    """O preço atual do produto: ignora preço riscado ('de') e parcelas; sem sobra, o menor valor."""
    atuais, todos = [], []
    for texto in card.find_all(string=RE_PRECO_TEXTO):
        valor = parse_preco(RE_PRECO_TEXTO.search(texto).group(1))
        if not valor:
            continue
        pai, riscado = texto.parent, False
        for _ in range(3):
            if pai is None:
                break
            classe = " ".join(pai.get("class", [])) if hasattr(pai, "get") else ""
            if pai.name in ("s", "del", "strike") or RE_CLASSE_RISCADO.search(classe):
                riscado = True
            pai = pai.parent
        todos.append(valor)
        if not riscado and not RE_PARCELA.search(str(texto)):
            atuais.append(valor)
    return atuais[0] if atuais else (min(todos) if todos else None)


RE_RUIDO_DO_CARD = re.compile(r"\b\d{1,2}\s*x\s*(de)?\b|sem juros|adicionar( ao carrinho)?|comprar( agora)?|indispon[ií]vel|ver (mais|detalhes)|avali[aã]o?", re.IGNORECASE)


def _nome_do_card(card) -> str:
    """O título do produto: o 1º cabeçalho ou link com texto de nome; senão o texto do bloco sem preços, parcelas e botões."""
    for marca in card.find_all(["h1", "h2", "h3", "h4", "h5", "a"]):
        texto = re.sub(r"\s+", " ", RE_PRECO_TEXTO.sub(" ", marca.get_text(" ", strip=True))).strip()
        if len(re.findall(r"[A-Za-zÀ-ú]", texto)) >= 10:
            return texto
    texto = RE_RUIDO_DO_CARD.sub(" ", RE_PRECO_TEXTO.sub(" ", card.get_text(" ", strip=True)))
    return re.sub(r"\s+", " ", texto).strip()


def _cards_da_listagem(soup) -> list[dict]:
    """Os produtos de uma listagem: para cada preço, o menor bloco acima dele que tenha também um nome (texto com letras)."""
    cards, vistos = [], set()
    for texto in soup.find_all(string=RE_PRECO_TEXTO):
        no = texto.parent
        for _ in range(8):
            if no is None or no.name in ("body", "html"):
                break
            sem_precos = RE_FRASES_DE_PRECO.sub(" ", RE_PRECO_TEXTO.sub(" ", no.get_text(" ", strip=True)))
            letras = len(re.findall(r"[A-Za-zÀ-ú]", sem_precos))
            if letras >= 14:
                if id(no) not in vistos:
                    vistos.add(id(no))
                    preco = _preco_do_card(no)
                    if preco:
                        link = next((a.get("href") for a in no.find_all("a", href=True)
                                     if not str(a.get("href")).startswith(("#", "javascript", "mailto"))), "")
                        cards.append({"nome": (nome := _nome_do_card(no))[:160], "palavras": _palavras(nome), "preco": preco, "link": link})
                break
            no = no.parent
    return cards


def preco_na_listagem(soup, item: str, url: str = "", cards: list[dict] | None = None) -> dict | None:
    """Em página de listagem (3+ produtos), o preço do produto cujo nome é do item (sinonimos.confere_nome: 'papel toalha' não serve
    para 'papel contact'). Com medida no item, a mesma medida tem preferência e medida diferente fica de fora. Vários produtos servem:
    o do meio (mediana). Devolve também o `link` do produto, para o sistema abrir a página dele e confirmar o preço."""
    from urllib.parse import urljoin

    import embalagem
    import sinonimos

    cards = cards if cards is not None else _cards_da_listagem(soup)
    if len(cards) < (1 if eh_url_de_busca(url) else MIN_CARDS_LISTAGEM):  # em endereço de busca/categoria, até 1 produto da lista vale
        return None
    achados = sorted((c for c in cards if sinonimos.confere_nome(item, c["nome"])), key=lambda c: c["preco"])
    if achados and embalagem.medidas(item):  # mesma medida do item primeiro; sem medida depois; medida diferente só se não houver outro
        for grupo in ("igual", "sem_medida", "diferente"):
            do_grupo = [c for c in achados if embalagem.confere(item, c["nome"]) == grupo]
            if do_grupo:
                achados = do_grupo
                break
    if not achados:
        return None
    melhor = max(sinonimos.pontuacao(item, c["nome"]) for c in achados)  # os que mais se parecem com o pedido ("papel adesivo contact" > "papel adesivo leonora")
    achados = [c for c in achados if sinonimos.pontuacao(item, c["nome"]) == melhor]
    escolhido = achados[(len(achados) - 1) // 2]
    extra = f" (mediana de {len(achados)} produtos que citam o item)" if len(achados) > 1 else ""
    link = urljoin(url, escolhido["link"]) if escolhido.get("link") and url else escolhido.get("link", "")
    return {"preco": escolhido["preco"], "origem": f"listagem: {escolhido['nome'][:70]}{extra}", "confianca": "média", "nome": escolhido["nome"],
            "link": link}


def _moedas_jsonld(dado: object, achadas: set[str]) -> None:
    if isinstance(dado, list):
        for item in dado:
            _moedas_jsonld(item, achadas)
    elif isinstance(dado, dict):
        for chave, valor in dado.items():
            if chave == "priceCurrency" and isinstance(valor, str):
                achadas.add(valor.strip().upper())
            elif isinstance(valor, (dict, list)):
                _moedas_jsonld(valor, achadas)


def moedas_da_pagina(html: str) -> set[str]:
    """Moedas declaradas nos dados da página (JSON-LD priceCurrency, metadados). Vazio = a página não declara."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    achadas: set[str] = set()
    for marcador in soup.find_all("script", type="application/ld+json"):
        try:
            _moedas_jsonld(json.loads(marcador.string or marcador.get_text() or ""), achadas)
        except (json.JSONDecodeError, TypeError):
            continue
    for meta in soup.find_all("meta"):
        propriedade = str(meta.get("property") or meta.get("name") or meta.get("itemprop") or "").lower()
        if propriedade.endswith(("price:currency", "pricecurrency")) and meta.get("content"):
            achadas.add(str(meta["content"]).strip().upper())
    for elemento in soup.select("[itemprop='priceCurrency']"):
        valor = elemento.get("content") or elemento.get_text(strip=True)
        if valor:
            achadas.add(str(valor).strip().upper())
    return {m for m in achadas if m}


def sinais_site_nacional(url: str, html: str) -> dict:
    """Sinais de que a página é de uma loja brasileira vendendo em reais: .br, moeda BRL, idioma pt-BR e 'R$' no texto.
    `estrangeira` = a página declara preço em outra moeda e nenhuma em BRL (nesse caso o preço não vale)."""
    from urllib.parse import urlparse
    from bs4 import BeautifulSoup

    dominio = urlparse(url).netloc.lower().split(":")[0]
    moedas = moedas_da_pagina(html)
    soup = BeautifulSoup(html[:200_000], "html.parser")
    idioma = str((soup.html.get("lang") if soup.html else "") or "").lower().replace("_", "-")
    sinais = []
    if dominio.endswith(".br"):
        sinais.append(".br")
    if "BRL" in moedas:
        sinais.append("moeda BRL")
    if idioma in ("pt-br", "pt"):
        sinais.append("pt-BR")
    if re.search(r"R\$\s*\d", html):
        sinais.append("R$")
    return {"pontos": len(sinais), "sinais": sinais, "moedas": sorted(moedas), "estrangeira": bool(moedas) and "BRL" not in moedas}


PONTOS_MINIMOS_SITE_NACIONAL = 2


def site_nacional(url: str, html: str) -> tuple[bool, str]:
    """(aceita?, motivo). Rejeita preço em moeda estrangeira e páginas com menos de 2 sinais de loja brasileira."""
    info = sinais_site_nacional(url, html)
    if info["estrangeira"]:
        return False, f"preço em outra moeda ({', '.join(info['moedas'])})"
    if info["pontos"] < PONTOS_MINIMOS_SITE_NACIONAL:
        return False, "não parece loja brasileira" + (f" (só: {', '.join(info['sinais'])})" if info["sinais"] else "")
    return True, ", ".join(info["sinais"])


def _data_iso(data_coleta: str) -> str:
    try:
        return datetime.strptime(data_coleta[:10], "%d/%m/%Y").date().isoformat()
    except ValueError:
        return ""


def registro_da_oferta(oferta: dict) -> dict | None:
    """Oferta da página (resultado do scraping) no formato dos registros de preço da Cotação Rápida."""
    preco = parse_preco(oferta.get("preco"))
    if not preco:
        return None
    dominio = str(oferta.get("dominio") or "")
    return {
        "preco": preco, "cnpj": dominio, "fornecedor": dominio or str(oferta.get("loja") or ""), "data": _data_iso(str(oferta.get("data_coleta") or "")),
        "dominio": dominio, "url": str(oferta.get("url") or ""), "titulo": str(oferta.get("titulo") or ""), "data_coleta": str(oferta.get("data_coleta") or ""),
        "origem_preco": str(oferta.get("origem_preco") or "não informada"), "confianca": str(oferta.get("confianca") or ""),
        "precos_na_pagina": len(oferta.get("precos_detectados") or []),
        "medida_confere": str(oferta.get("medida_confere") or ""), "medida_ofertada": str(oferta.get("medida_ofertada") or ""),
    }


def analisar_item_web(descricao: str, ofertas: list[dict], remover: bool = True, max_precos: int = PRECOS_POR_ITEM_PADRAO, tolerancia: float = TOLERANCIA) -> dict:
    """Limpa e seleciona os preços de um item pesquisado na internet (mesma regra da Cotação Rápida)."""
    vistos: set[str] = set()
    registros = []
    for oferta in ofertas:
        registro = registro_da_oferta(oferta)
        if registro and (registro["url"] or registro["dominio"]) not in vistos:
            vistos.add(registro["url"] or registro["dominio"])
            registros.append(registro)
    resultado = {
        "descricao": descricao, "tipo": "Web", "status": "sem_paginas", "catmats": [], "precos": [], "stats": None,
        "unidade": "unidade ofertada na página", "unidade_curta": __import__("embalagem").unidade_curta(descricao), "brutos": len(registros), "outliers": 0, "faixa_validos": None,
        "universo": len(registros), "proximos": [], "falha_api": False, "melhor_proximo": None, "registros": registros,
        "paginas": len(registros), "lojas": len({r["cnpj"] for r in registros}),
    }
    if not registros:
        return resultado
    limpos, resultado["faixa_validos"] = remover_outliers(registros) if remover else (list(registros), None)
    resultado["outliers"] = len(registros) - len(limpos)
    resultado["status"] = "sem_precos"
    # embalagem diferente da pedida só entra se faltar preço de embalagem igual (ou sem medida informada)
    mesma_embalagem = [r for r in limpos if r.get("medida_confere") != "diferente"]
    resultado["precos"] = selecionar_precos(mesma_embalagem, max_precos, tolerancia)
    outras = [r for r in limpos if r.get("medida_confere") == "diferente"]
    if len(resultado["precos"]) < max_precos and outras:
        if resultado["precos"]:  # completa com as de outra embalagem mais próximas da média, sem tirar as de embalagem igual
            media = sum(r["preco"] for r in resultado["precos"]) / len(resultado["precos"])
            proximas = sorted((r for r in outras if abs(r["preco"] - media) <= tolerancia * media), key=lambda r: abs(r["preco"] - media))
            resultado["precos"] = sorted(resultado["precos"] + proximas[:max_precos - len(resultado["precos"])], key=lambda r: r["preco"])
        else:
            resultado["precos"] = selecionar_precos(outras, max_precos, tolerancia)
    diferentes = [p for p in resultado["precos"] if p.get("medida_confere") == "diferente"]
    if diferentes and descricao:  # a descrição do relatório passa a dizer a embalagem realmente cotada
        cotadas = ", ".join(f"{p.get('medida_ofertada') or 'outra medida'} ({p['dominio']})" for p in diferentes)
        resultado["descricao"] = f"{descricao} — ATENÇÃO: {len(diferentes)} preço(s) de embalagem diferente da pedida: {cotadas}"
        resultado["unidade_curta"] = "embalagens variadas"
    if resultado["precos"]:
        resultado["stats"] = estatisticas([r["preco"] for r in resultado["precos"]])
        resultado["status"] = "ok" if len(resultado["precos"]) >= MIN_PRECOS else "insuficiente"
    return resultado


def analisar_todos(itens: list[str], ofertas: list[dict], remover: bool = True, max_precos: int = PRECOS_POR_ITEM_PADRAO) -> list[dict]:
    """Um resultado por item pesquisado, na ordem digitada (itens sem página aparecem como 'sem páginas')."""
    return [analisar_item_web(item, [o for o in ofertas if o.get("item") == item], remover, max_precos) for item in itens if item.strip()]

