"""Baixa o catálogo CATMAT completo (itens ativos) da API do Compras.gov e salva em
'Projeto Adesões/catalogo_catmat.csv.gz', usado pela página CATMAT/CATSERV.

A API não faz busca por texto, então a página pesquisa neste arquivo local.
Uso: python scripts/atualizar_catalogo_catmat.py
"""

import csv
import gzip
import os
import time
from concurrent.futures import ThreadPoolExecutor

import requests

URL = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"
SAIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Projeto Adesões", "catalogo_catmat.csv.gz")
TAMANHO_PAGINA = 500


def baixar_pagina(pagina: int) -> dict:
    for tentativa in range(5):
        try:
            resposta = requests.get(URL, params={"pagina": pagina, "tamanhoPagina": TAMANHO_PAGINA, "statusItem": "true"}, timeout=60)
            if resposta.status_code == 200:
                return resposta.json()
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** tentativa)
    raise RuntimeError(f"Falha ao baixar a página {pagina}")


def main() -> None:
    primeira = baixar_pagina(1)
    paginas = int(primeira["totalPaginas"])
    print(f"{primeira['totalRegistros']} itens em {paginas} páginas")
    with ThreadPoolExecutor(max_workers=6) as executor:
        resultados = [primeira] + list(executor.map(baixar_pagina, range(2, paginas + 1)))
    vistos = set()
    with gzip.open(SAIDA, "wt", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["codigo", "codigo_pdm", "nome_pdm", "descricao", "nome_classe"])
        for pagina in resultados:
            for item in pagina["resultado"]:
                if item["codigoItem"] in vistos or not item.get("descricaoItem"):
                    continue
                vistos.add(item["codigoItem"])
                escritor.writerow([item["codigoItem"], item["codigoPdm"], item["nomePdm"], item["descricaoItem"].strip(), item.get("nomeClasse", "")])
    print(f"{len(vistos)} itens salvos em {SAIDA} ({os.path.getsize(SAIDA) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
