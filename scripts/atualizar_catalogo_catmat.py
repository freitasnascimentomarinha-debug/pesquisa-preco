"""Atualiza os catálogos locais a partir da API do Compras.gov.

Gera, em 'Projeto Adesões/':
  - catalogo_catmat.csv.gz   itens CATMAT ativos (a API não faz busca por texto; as páginas pesquisam aqui)
  - catalogo_pdm.json        famílias (PDM) de material: nome -> código
  - catalogo_servicos.json   serviços (CATSERV): nome -> código
  - catalogo_meta.json       data da última atualização

Uso:
  python scripts/atualizar_catalogo_catmat.py                  # tudo (~8 min)
  python scripts/atualizar_catalogo_catmat.py --sem-materiais  # reaproveita o CSV de itens e refaz o resto
"""

import csv
import gzip
import json
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

API = "https://dadosabertos.compras.gov.br"
URL_MATERIAL = f"{API}/modulo-material/4_consultarItemMaterial"
URL_SERVICO = f"{API}/modulo-servico/6_consultarItemServico"
PASTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Projeto Adesões")
CSV_MATERIAL = os.path.join(PASTA, "catalogo_catmat.csv.gz")
TAMANHO_PAGINA = 500


def baixar_pagina(url: str, pagina: int, parametros: dict) -> dict:
    for tentativa in range(5):
        try:
            resposta = requests.get(url, params={**parametros, "pagina": pagina, "tamanhoPagina": TAMANHO_PAGINA}, timeout=60)
            if resposta.status_code == 200:
                return resposta.json()
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** tentativa)
    raise RuntimeError(f"Falha ao baixar a página {pagina} de {url}")


def baixar_tudo(url: str, parametros: dict) -> list[dict]:
    primeira = baixar_pagina(url, 1, parametros)
    paginas = int(primeira["totalPaginas"])
    print(f"{url.rsplit('/', 1)[-1]}: {primeira['totalRegistros']} registros em {paginas} páginas")
    with ThreadPoolExecutor(max_workers=6) as executor:
        resto = list(executor.map(lambda pagina: baixar_pagina(url, pagina, parametros), range(2, paginas + 1)))
    return [item for pagina in [primeira, *resto] for item in pagina["resultado"]]


def _salvar_json(nome: str, dados: dict) -> None:
    with open(os.path.join(PASTA, nome), "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=1)


def _rotulos_unicos(pares: list[tuple[str, object]], prefixo: str) -> dict[str, object]:
    """Nome -> código; quando o mesmo nome existe com códigos diferentes, acrescenta o código ao rótulo."""
    por_nome: dict[str, list[object]] = defaultdict(list)
    for nome, codigo in pares:
        if codigo not in por_nome[nome]:
            por_nome[nome].append(codigo)
    rotulos: dict[str, object] = {}
    for nome, codigos in sorted(por_nome.items()):
        for codigo in codigos:
            rotulos[nome if len(codigos) == 1 else f"{nome} ({prefixo} {codigo})"] = codigo
    return rotulos


def atualizar_materiais() -> None:
    itens = baixar_tudo(URL_MATERIAL, {"statusItem": "true"})
    vistos: set[int] = set()
    with gzip.open(CSV_MATERIAL, "wt", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["codigo", "codigo_pdm", "nome_pdm", "descricao", "nome_classe"])
        for item in itens:
            if item["codigoItem"] in vistos or not item.get("descricaoItem"):
                continue
            vistos.add(item["codigoItem"])
            escritor.writerow([item["codigoItem"], item["codigoPdm"], item["nomePdm"], item["descricaoItem"].strip(), item.get("nomeClasse", "")])
    print(f"{len(vistos)} itens salvos ({os.path.getsize(CSV_MATERIAL) / 1e6:.1f} MB)")


def atualizar_lista_pdm() -> None:
    with gzip.open(CSV_MATERIAL, "rt", encoding="utf-8", newline="") as arquivo:
        pares = [(linha["nome_pdm"].strip('" '), int(linha["codigo_pdm"])) for linha in csv.DictReader(arquivo)]
    lista = _rotulos_unicos(pares, "PDM")
    _salvar_json("catalogo_pdm.json", lista)
    print(f"{len(lista)} famílias de material (PDM)")


def atualizar_servicos() -> None:
    itens = baixar_tudo(URL_SERVICO, {"statusServico": "true"})
    lista = _rotulos_unicos([(item["nomeServico"].strip(), item["codigoServico"]) for item in itens], "serviço")
    _salvar_json("catalogo_servicos.json", lista)
    print(f"{len(lista)} serviços")


def main() -> None:
    if "--sem-materiais" not in sys.argv:
        atualizar_materiais()
    atualizar_lista_pdm()
    atualizar_servicos()
    _salvar_json("catalogo_meta.json", {"atualizado_em": datetime.now().isoformat(timespec="seconds")})


if __name__ == "__main__":
    main()
