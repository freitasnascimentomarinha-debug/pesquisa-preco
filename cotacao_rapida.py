"""Motor da página Cotação Rápida: para cada descrição, acha até 3 itens CATMAT parecidos (>= 75%)
que tenham preços praticados nos últimos 12 meses e seleciona até 5 preços coerentes entre si.

Fonte dos preços: Compras.gov (módulo Pesquisa de Preço, preços praticados em compras públicas).
"""

from __future__ import annotations

import datetime as dt
import statistics
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

import requests
import streamlit as st

from catmat_busca import IndiceCatmat, buscar_familias, calcular_similaridade

API_PRECOS = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"
LIMIAR_CORRESPONDENCIA = 75.0  # % mínimo de correspondência entre a descrição e o item CATMAT
LIMIAR_FAMILIA = 60.0  # famílias (PDM) abaixo disso nem têm os preços consultados
MAX_CATMAT = 3
MAX_PRECOS = 5
MIN_PRECOS = 3  # abaixo disso o item é sinalizado (IN SEGES/ME nº 65/2021 recomenda ao menos três preços)
TOLERANCIA = 0.30  # cada preço deve ficar a até 30% (para mais ou para menos) da média dos preços listados
JANELA_DIAS = 365
MAX_FAMILIAS = 12
MAX_PAGINAS = 8
TAMANHO_PAGINA = 500

CAMPOS = {
    "idCompra": "id_compra",
    "idItemCompra": "id_item",
    "dataCompra": "data",
    "niFornecedor": "cnpj",
    "nomeFornecedor": "fornecedor",
    "codigoItemCatalogo": "catmat",
    "descricaoItem": "descricao",
    "quantidade": "quantidade",
    "precoUnitario": "preco",
    "siglaUnidadeFornecimento": "sigla",
    "nomeUnidadeFornecimento": "unidade",
    "capacidadeUnidadeFornecimento": "capacidade",
    "codigoUasg": "uasg",
    "nomeUasg": "nome_uasg",
    "estado": "uf",
}


def _baixar_pagina(parametros: dict[str, object]) -> dict | None:
    """Uma página da API, com espera crescente quando ela limita as requisições. None se desistir."""
    for tentativa in range(4):
        try:
            resposta = requests.get(API_PRECOS, params=parametros, timeout=90)
            if resposta.status_code == 200:
                return resposta.json()
            if resposta.status_code == 400:
                return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** (tentativa + 1))
    return None


def _reduzir(registro: dict) -> dict:
    return {novo: registro.get(original) for original, novo in CAMPOS.items()}


@st.cache_data(ttl=3600, show_spinner=False)
def registros_da_familia(codigo_pdm: str, inicio: str, fim: str) -> tuple[list[dict], bool]:
    """Preços praticados de toda a família (PDM) no período. Retorna (registros, houve_falha)."""
    base = {"tamanhoPagina": TAMANHO_PAGINA, "tipo": "codigoPdm", "codigo": codigo_pdm, "dataCompraInicio": inicio, "dataCompraFim": fim}
    primeira = _baixar_pagina({**base, "pagina": 1})
    if primeira is None:
        return [], True
    registros = [_reduzir(registro) for registro in primeira.get("resultado", [])]
    paginas = min(int(primeira.get("totalPaginas") or 0), MAX_PAGINAS)
    falha = False
    if paginas > 1:
        with ThreadPoolExecutor(max_workers=4) as executor:
            restante = list(executor.map(lambda pagina: _baixar_pagina({**base, "pagina": pagina}), range(2, paginas + 1)))
        for resposta in restante:
            if resposta is None:
                falha = True
            else:
                registros += [_reduzir(registro) for registro in resposta.get("resultado", [])]
    return registros, falha


def _numero(valor: object) -> float | None:
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return numero if numero == numero else None


def _unidade_dominante(registros: list[dict]) -> tuple[list[dict], str, str]:
    """Compara só preços da mesma unidade de fornecimento (e mesma capacidade da embalagem, quando informada)."""
    por_sigla = Counter(registro["sigla"] for registro in registros)
    sigla = por_sigla.most_common(1)[0][0]
    da_sigla = [registro for registro in registros if registro["sigla"] == sigla]
    capacidades = Counter(_numero(r["capacidade"]) for r in da_sigla if (_numero(r["capacidade"]) or 0) > 0)
    capacidade = capacidades.most_common(1)[0][0] if capacidades else 0
    mantidos = [r for r in da_sigla if capacidade == 0 or (_numero(r["capacidade"]) or 0) in (0, capacidade)]
    nome = next((r["unidade"] for r in mantidos if r["unidade"]), "") or str(sigla or "")
    rotulo = f"{nome} ({sigla})" if sigla and nome and nome != sigla else str(nome or sigla or "N/I")
    curto = str(sigla or nome or "N/I")
    if capacidade:
        rotulo += f" c/ {capacidade:g}"
        curto += f" c/ {capacidade:g}"
    return mantidos, rotulo, curto


def remover_outliers(registros: list[dict]) -> tuple[list[dict], tuple[float, float] | None]:
    """Tira preços inexequíveis/extremos (fora de 0,3x a 3x a mediana) e, com 4+ preços, os outliers pelo IQR."""
    if not registros:
        return [], None
    mediana = statistics.median(r["preco"] for r in registros)
    sobra = [r for r in registros if 0.3 * mediana <= r["preco"] <= 3 * mediana]
    if len(sobra) >= 4:
        q1, _, q3 = statistics.quantiles((r["preco"] for r in sobra), n=4, method="inclusive")
        inferior, superior = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        sobra = [r for r in sobra if inferior <= r["preco"] <= superior]
    precos = [r["preco"] for r in sobra]
    return sobra, ((min(precos), max(precos)) if precos else None)


def selecionar_precos(registros: list[dict], limite: int = MAX_PRECOS, tolerancia: float = TOLERANCIA) -> list[dict]:
    """Até `limite` preços, dos mais próximos da mediana para fora, de modo que todos fiquem a até `tolerancia`
    da média do conjunto escolhido. Prefere fornecedores diferentes e, no empate, compras mais recentes."""
    if not registros:
        return []
    mediana = statistics.median(r["preco"] for r in registros)
    ordenados = sorted(registros, key=lambda r: (round(abs(r["preco"] - mediana), 6), _inverso_data(r["data"])))
    escolhidos: list[dict] = []
    fornecedores: set[str] = set()

    def cabe(candidato: dict) -> bool:
        precos = [r["preco"] for r in escolhidos] + [candidato["preco"]]
        media = sum(precos) / len(precos)
        return all(abs(preco - media) <= tolerancia * media for preco in precos)

    for exigir_novo_fornecedor in (True, False):
        for candidato in ordenados:
            if len(escolhidos) >= limite:
                break
            if any(candidato is escolhido for escolhido in escolhidos):
                continue
            if exigir_novo_fornecedor and (candidato["cnpj"] or candidato["fornecedor"]) in fornecedores:
                continue
            if cabe(candidato):
                escolhidos.append(candidato)
                fornecedores.add(candidato["cnpj"] or candidato["fornecedor"])
    return sorted(escolhidos, key=lambda r: r["preco"])


def _inverso_data(data: object) -> int:
    """Chave de ordenação: datas mais recentes primeiro."""
    try:
        return -dt.date.fromisoformat(str(data)[:10]).toordinal()
    except ValueError:
        return 0


def estatisticas(precos: list[float]) -> dict[str, float]:
    media = sum(precos) / len(precos)
    desvio = statistics.stdev(precos) if len(precos) > 1 else 0.0
    return {
        "min": min(precos),
        "media": media,
        "mediana": statistics.median(precos),
        "max": max(precos),
        "desvio": desvio,
        "cv": desvio / media * 100 if media else 0.0,
    }


def resultado_vazio(descricao: str) -> dict:
    return {
        "descricao": descricao, "status": "sem_catmat", "catmats": [], "precos": [], "stats": None,
        "unidade": "", "unidade_curta": "", "brutos": 0, "outliers": 0, "faixa_validos": None,
        "falha_api": False, "melhor_proximo": None,
    }


def cotar_item(descricao: str, catmat: IndiceCatmat, hoje: dt.date | None = None) -> dict:
    """Resultado completo da cotação de uma descrição. Chaves principais: status, catmats, precos, stats."""
    hoje = hoje or dt.date.today()
    inicio, fim = (hoje - dt.timedelta(days=JANELA_DIAS)).isoformat(), hoje.isoformat()
    resultado = resultado_vazio(descricao)
    familias = [f for f in buscar_familias(descricao, catmat, limite=MAX_FAMILIAS) if f["nota"] >= LIMIAR_FAMILIA]
    if not familias:
        return resultado
    with ThreadPoolExecutor(max_workers=4) as executor:
        respostas = list(executor.map(lambda f: registros_da_familia(str(f["codigo"]), inicio, fim), familias))
    resultado["falha_api"] = any(falha for _, falha in respostas)

    por_item: dict[object, list[dict]] = defaultdict(list)
    familia_do_item: dict[object, str] = {}
    for familia, (registros, _) in zip(familias, respostas):
        for registro in registros:
            if (_numero(registro["preco"]) or 0) > 0:
                registro["preco"] = float(registro["preco"])
                por_item[registro["catmat"]].append(registro)
                familia_do_item[registro["catmat"]] = str(familia["nome"])
    classificados = sorted(
        (
            (calcular_similaridade(descricao, str(regs[0]["descricao"] or ""), familia_do_item[codigo]), len(regs), codigo)
            for codigo, regs in por_item.items()
        ),
        reverse=True,
    )
    if classificados:
        resultado["melhor_proximo"] = {"codigo": classificados[0][2], "correspondencia": classificados[0][0], "descricao": str(por_item[classificados[0][2]][0]["descricao"])}
    escolhidos_catmat = [c for c in classificados if c[0] >= LIMIAR_CORRESPONDENCIA][:MAX_CATMAT]
    if not escolhidos_catmat:
        return resultado

    resultado["catmats"] = [
        {"codigo": codigo, "correspondencia": nota, "registros": quantidade, "descricao": str(por_item[codigo][0]["descricao"] or "")}
        for nota, quantidade, codigo in escolhidos_catmat
    ]
    vistos: set[object] = set()
    universo = []
    for _, _, codigo in escolhidos_catmat:
        for registro in por_item[codigo]:
            chave = (registro["id_compra"], registro["id_item"])
            if chave not in vistos:
                vistos.add(chave)
                universo.append({**registro, "correspondencia": next(n for n, _, c in escolhidos_catmat if c == codigo)})
    resultado["brutos"] = len(universo)
    mesma_unidade, resultado["unidade"], resultado["unidade_curta"] = _unidade_dominante(universo)
    limpos, resultado["faixa_validos"] = remover_outliers(mesma_unidade)
    resultado["outliers"] = len(mesma_unidade) - len(limpos)
    resultado["universo"] = len(mesma_unidade)
    resultado["precos"] = selecionar_precos(limpos)
    resultado["status"] = "sem_precos"
    if resultado["precos"]:
        resultado["stats"] = estatisticas([r["preco"] for r in resultado["precos"]])
        resultado["status"] = "ok" if len(resultado["precos"]) >= MIN_PRECOS else "insuficiente"
    return resultado
