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


def preco_principal(html: str, alternativa: Callable[[str], list[float]] | None = None) -> dict | None:
    """O preço do produto anunciado na página, do mais ao menos confiável.

    1. Oferta do produto em JSON-LD (schema.org): a mais barata em estoque; parcelas e preços riscados são ignorados.
    2. Metadados (product:price:amount, itemprop="price").
    3. `alternativa` (heurísticas de texto/classes): usa a mediana dos valores e marca a confiança como baixa."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    for marcador in soup.find_all("script", type="application/ld+json"):
        try:
            dados = json.loads(marcador.string or marcador.get_text() or "")
        except (json.JSONDecodeError, TypeError):
            continue
        for produto in _produtos_jsonld(dados):
            precos = _precos_da_oferta(produto.get("offers"))
            if precos:
                return {"preco": min(precos), "origem": "JSON-LD (oferta do produto)", "confianca": "alta", "nome": str(produto.get("name") or "")[:150]}

    for meta in soup.find_all("meta"):
        propriedade = str(meta.get("property") or meta.get("name") or meta.get("itemprop") or "").lower()
        if propriedade in ("product:price:amount", "og:price:amount", "product:sale_price:amount", "price", "twitter:data1"):
            preco = parse_preco(meta.get("content"))
            if preco and (propriedade != "twitter:data1" or "R$" in str(meta.get("content"))):
                return {"preco": preco, "origem": "metadado da página", "confianca": "alta", "nome": ""}
    for elemento in soup.select("[itemprop='price']"):
        preco = parse_preco(elemento.get("content") or elemento.get("data-price") or elemento.get_text(strip=True))
        if preco:
            return {"preco": preco, "origem": "itemprop=price", "confianca": "alta", "nome": ""}

    if alternativa:
        valores = sorted(set(alternativa(html)))
        if valores and len(valores) <= 8:  # muitos valores diferentes = listagem/categoria, não um produto
            return {"preco": valores[len(valores) // 2], "origem": "texto da página (mediana dos valores)", "confianca": "baixa", "nome": ""}
    return None


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
    }


def analisar_item_web(descricao: str, ofertas: list[dict], remover: bool = True, max_precos: int = MAX_PRECOS, tolerancia: float = TOLERANCIA) -> dict:
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
        "unidade": "unidade ofertada na página", "unidade_curta": "oferta", "brutos": len(registros), "outliers": 0, "faixa_validos": None,
        "universo": len(registros), "proximos": [], "falha_api": False, "melhor_proximo": None, "registros": registros,
        "paginas": len(registros), "lojas": len({r["cnpj"] for r in registros}),
    }
    if not registros:
        return resultado
    limpos, resultado["faixa_validos"] = remover_outliers(registros) if remover else (list(registros), None)
    resultado["outliers"] = len(registros) - len(limpos)
    resultado["status"] = "sem_precos"
    resultado["precos"] = selecionar_precos(limpos, max_precos, tolerancia)
    if resultado["precos"]:
        resultado["stats"] = estatisticas([r["preco"] for r in resultado["precos"]])
        resultado["status"] = "ok" if len(resultado["precos"]) >= MIN_PRECOS else "insuficiente"
    return resultado


def analisar_todos(itens: list[str], ofertas: list[dict], remover: bool = True) -> list[dict]:
    """Um resultado por item pesquisado, na ordem digitada (itens sem página aparecem como 'sem páginas')."""
    return [analisar_item_web(item, [o for o in ofertas if o.get("item") == item], remover) for item in itens if item.strip()]
