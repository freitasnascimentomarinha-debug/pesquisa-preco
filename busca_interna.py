"""Busca dentro do próprio site da loja (sem passar por buscador): tenta os endereços de busca mais comuns das lojas virtuais
e devolve o primeiro que responde com uma lista de produtos com preço. O endereço que funciona é guardado na memória da loja."""
import re
import time
import random
import unicodedata
from urllib.parse import quote_plus, urlparse

# {q} = termo pesquisado. Plataformas comuns: VTEX/Tray/Nuvemshop (/busca, /search), WordPress/WooCommerce (/?s=), Magento (/catalogsearch),
# OpenCart, Loja Integrada (/buscar)
PADROES = [
    "/busca?q={q}",
    "/search?q={q}",
    "/?s={q}&post_type=product",
    "/catalogsearch/result/?q={q}",
    "/buscar?q={q}",
    "/pesquisa?q={q}",
    "/busca/?q={q}",
    "/search/?q={q}",
    "/?s={q}",
    "/index.php?route=product/search&search={q}",
    "/busca?search={q}",
    "/loja/busca.php?palavra_busca={q}",
]
TIMEOUT_S = 8


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def url_de(site: str, padrao: str, item: str) -> str:
    return f"https://{site}{padrao.format(q=quote_plus(item))}"


def parece_busca(resp, item: str) -> bool:
    """A resposta é uma página de resultados de busca com produtos? (200, não caiu na página inicial, cita o item e tem preço em R$)."""
    if resp.status_code != 200 or "html" not in resp.headers.get("Content-Type", "html").lower():
        return False
    final = urlparse(resp.url)
    if final.path in ("", "/") and not final.query:
        return False  # o site ignorou a busca e mandou para a página inicial
    texto = _sem_acento(resp.text)
    palavras = [p for p in re.findall(r"[a-z0-9]+", _sem_acento(item)) if len(p) > 3]
    if palavras and not any(p in texto for p in palavras):
        return False
    return len(re.findall(r"r\$\s*\d", texto)) >= 2


def descobrir(session, site: str, item: str, headers: dict, padrao_conhecido: str = "", max_tentativas: int = 4):
    """(url da busca, padrão que funcionou) ou ("", ""). Com `padrao_conhecido` (guardado na memória) não testa nada: usa direto."""
    if padrao_conhecido:
        return url_de(site, padrao_conhecido, item), padrao_conhecido
    for padrao in PADROES[:max_tentativas]:
        url = url_de(site, padrao, item)
        try:
            resp = session.get(url, headers=headers, timeout=TIMEOUT_S)
        except Exception:
            continue
        if resp.status_code in (403, 429):
            return "", ""  # o site barrou: insistir só piora
        if parece_busca(resp, item):
            return url, padrao
        time.sleep(random.uniform(0.5, 1.2))
    return "", ""
