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

from catmat_busca import IndiceCatmat, _opcoes_servico, buscar_familias, calcular_similaridade

API_PRECOS = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"
API_PRECOS_SERVICO = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico"
LIMIAR_CORRESPONDENCIA = 75.0  # % mínimo de correspondência entre a descrição e o item CATMAT
LIMIAR_FAMILIA = 60.0  # famílias (PDM) abaixo disso nem têm os preços consultados
MAX_CATMAT = 3
MAX_PRECOS = 5
MIN_PRECOS = 3  # abaixo disso o item é sinalizado (IN SEGES/ME nº 65/2021 recomenda ao menos três preços)
TOLERANCIA = 0.30  # cada preço deve ficar a até 30% (para mais ou para menos) da média dos preços listados
JANELA_DIAS = 365
MAX_FAMILIAS = 12
MAX_CANDIDATOS_SERVICO = 10  # serviços do catálogo cujos preços são conferidos antes de escolher os 3 melhores
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


def _baixar_pagina(parametros: dict[str, object], url: str = API_PRECOS) -> dict | None:
    """Uma página da API, com espera crescente quando ela limita as requisições. None se desistir."""
    for tentativa in range(4):
        try:
            resposta = requests.get(url, params=parametros, timeout=90)
            if resposta.status_code == 200:
                return resposta.json()
            if resposta.status_code == 400:
                return None
        except (requests.RequestException, ValueError):
            pass
        time.sleep(2 ** (tentativa + 1))
    return None


CAMPOS_SERVICO = {**CAMPOS, "siglaUnidadeMedida": "sigla", "nomeUnidadeMedida": "unidade"}
CAMPOS_SERVICO = {k: v for k, v in CAMPOS_SERVICO.items() if k not in ("siglaUnidadeFornecimento", "nomeUnidadeFornecimento", "capacidadeUnidadeFornecimento")}


def _reduzir(registro: dict, campos: dict[str, str] = CAMPOS) -> dict:
    reduzido = {novo: registro.get(original) for original, novo in campos.items()}
    reduzido.setdefault("capacidade", None)  # serviços não têm capacidade de embalagem
    return reduzido


def _registros_paginados(url: str, base: dict[str, object], campos: dict[str, str]) -> tuple[list[dict], bool]:
    """Todas as páginas (até MAX_PAGINAS) de uma consulta de preços. Retorna (registros, houve_falha)."""
    primeira = _baixar_pagina({**base, "pagina": 1}, url)
    if primeira is None:
        return [], True
    registros = [_reduzir(registro, campos) for registro in primeira.get("resultado", [])]
    paginas = min(int(primeira.get("totalPaginas") or 0), MAX_PAGINAS)
    falha = False
    if paginas > 1:
        with ThreadPoolExecutor(max_workers=4) as executor:
            restante = list(executor.map(lambda pagina: _baixar_pagina({**base, "pagina": pagina}, url), range(2, paginas + 1)))
        for resposta in restante:
            if resposta is None:
                falha = True
            else:
                registros += [_reduzir(registro, campos) for registro in resposta.get("resultado", [])]
    return registros, falha


@st.cache_data(ttl=3600, show_spinner=False)
def registros_da_familia(codigo_pdm: str, inicio: str, fim: str) -> tuple[list[dict], bool]:
    """Preços praticados de toda a família de material (PDM) no período."""
    base = {"tamanhoPagina": TAMANHO_PAGINA, "tipo": "codigoPdm", "codigo": codigo_pdm, "dataCompraInicio": inicio, "dataCompraFim": fim}
    return _registros_paginados(API_PRECOS, base, CAMPOS)


@st.cache_data(ttl=3600, show_spinner=False)
def registros_do_servico(codigo_servico: str, inicio: str, fim: str) -> tuple[list[dict], bool]:
    """Preços praticados de um serviço (CATSERV) no período."""
    base = {"tamanhoPagina": TAMANHO_PAGINA, "codigoItemCatalogo": codigo_servico, "dataCompraInicio": inicio, "dataCompraFim": fim}
    return _registros_paginados(API_PRECOS_SERVICO, base, CAMPOS_SERVICO)


@st.cache_data(ttl=3600, show_spinner=False)
def total_de_precos_do_servico(codigo_servico: str, inicio: str, fim: str) -> int:
    """Quantidade de registros de preço do serviço no período (consulta leve, só a contagem)."""
    resposta = _baixar_pagina({"tamanhoPagina": 10, "codigoItemCatalogo": codigo_servico, "dataCompraInicio": inicio, "dataCompraFim": fim, "pagina": 1}, API_PRECOS_SERVICO)
    return int((resposta or {}).get("totalRegistros") or 0)


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


def resultado_vazio(descricao: str, tipo: str = "Material", limiar: float = LIMIAR_CORRESPONDENCIA) -> dict:
    return {
        "descricao": descricao, "tipo": tipo, "status": "sem_catmat", "catmats": [], "precos": [], "stats": None,
        "unidade": "", "unidade_curta": "", "brutos": 0, "outliers": 0, "faixa_validos": None,
        "falha_api": False, "melhor_proximo": None, "proximos": [], "limiar": limiar,
    }


def _concluir(resultado: dict, escolhidos: list[tuple[float, int, object, str]], por_item: dict[object, list[dict]]) -> dict:
    """Parte comum a material e serviço: junta os registros dos códigos escolhidos, limpa e seleciona os preços."""
    resultado["catmats"] = [
        {"codigo": codigo, "correspondencia": nota, "registros": quantidade, "descricao": descricao}
        for nota, quantidade, codigo, descricao in escolhidos
    ]
    nota_do_codigo = {codigo: nota for nota, _, codigo, _ in escolhidos}
    vistos: set[object] = set()
    universo = []
    for _, _, codigo, _ in escolhidos:
        for registro in por_item[codigo]:
            chave = (registro["id_compra"], registro["id_item"])
            if chave not in vistos:
                vistos.add(chave)
                universo.append({**registro, "correspondencia": nota_do_codigo[codigo]})
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


def _preco_valido(registro: dict) -> bool:
    if (_numero(registro["preco"]) or 0) <= 0:
        return False
    registro["preco"] = float(registro["preco"])
    return True


def _cotar_material(descricao: str, catmat: IndiceCatmat, inicio: str, fim: str, limiar: float) -> dict:
    resultado = resultado_vazio(descricao, "Material", limiar)
    familias = [f for f in buscar_familias(descricao, catmat, limite=MAX_FAMILIAS) if f["nota"] >= min(LIMIAR_FAMILIA, limiar - 10)]
    if not familias:
        return resultado
    with ThreadPoolExecutor(max_workers=4) as executor:
        respostas = list(executor.map(lambda f: registros_da_familia(str(f["codigo"]), inicio, fim), familias))
    resultado["falha_api"] = any(falha for _, falha in respostas)

    por_item: dict[object, list[dict]] = defaultdict(list)
    familia_do_item: dict[object, str] = {}
    for familia, (registros, _) in zip(familias, respostas):
        for registro in registros:
            if _preco_valido(registro):
                por_item[registro["catmat"]].append(registro)
                familia_do_item[registro["catmat"]] = str(familia["nome"])
    classificados = sorted(
        (
            (calcular_similaridade(descricao, str(regs[0]["descricao"] or ""), familia_do_item[codigo]), len(regs), codigo, str(regs[0]["descricao"] or ""))
            for codigo, regs in por_item.items()
        ),
        reverse=True,
    )
    resultado["proximos"] = [{"codigo": c[2], "correspondencia": c[0], "descricao": c[3]} for c in classificados[:MAX_CATMAT]]
    resultado["melhor_proximo"] = resultado["proximos"][0] if classificados else None
    escolhidos = [c for c in classificados if c[0] >= limiar][:MAX_CATMAT]
    return _concluir(resultado, escolhidos, por_item) if escolhidos else resultado


def _cotar_servico(descricao: str, catalogo_servico: list[dict], inicio: str, fim: str, limiar: float) -> dict:
    resultado = resultado_vazio(descricao, "Serviço", limiar)
    opcoes = sorted(_opcoes_servico(descricao, catalogo_servico), key=lambda o: o["bruta"], reverse=True)
    resultado["proximos"] = [{"codigo": o["codigo"], "correspondencia": o["similaridade"], "descricao": o["descricao_catalogo"]} for o in opcoes[:MAX_CATMAT]]
    resultado["melhor_proximo"] = resultado["proximos"][0] if opcoes else None
    candidatos = [o for o in opcoes if o["similaridade"] >= limiar][:MAX_CANDIDATOS_SERVICO]
    if not candidatos:
        return resultado
    with ThreadPoolExecutor(max_workers=4) as executor:  # primeiro só a contagem: poucos serviços têm preços no período
        totais = list(executor.map(lambda o: total_de_precos_do_servico(str(o["codigo"]), inicio, fim), candidatos))
    com_precos = sorted(((o, n) for o, n in zip(candidatos, totais) if n > 0), key=lambda par: (round(par[0]["bruta"], 1), par[1]), reverse=True)[:MAX_CATMAT]
    if not com_precos:
        return resultado
    with ThreadPoolExecutor(max_workers=3) as executor:
        respostas = list(executor.map(lambda par: registros_do_servico(str(par[0]["codigo"]), inicio, fim), com_precos))
    resultado["falha_api"] = any(falha for _, falha in respostas)
    por_item: dict[object, list[dict]] = {}
    escolhidos = []
    for (opcao, _), (registros, _) in zip(com_precos, respostas):
        validos = [r for r in registros if _preco_valido(r)]
        if validos:
            por_item[opcao["codigo"]] = validos
            escolhidos.append((opcao["similaridade"], len(validos), opcao["codigo"], opcao["descricao_catalogo"]))
    return _concluir(resultado, escolhidos, por_item) if escolhidos else resultado


_ORDEM_STATUS = {"ok": 3, "insuficiente": 2, "sem_precos": 1, "sem_catmat": 0}


def cotar_item(descricao: str, catmat: IndiceCatmat, catalogo_servico: list[dict] | None = None, tipo: str = "Material", limiar: float = LIMIAR_CORRESPONDENCIA, hoje: dt.date | None = None) -> dict:
    """Cotação de uma descrição. `tipo`: "Material", "Serviço" ou "Automático" (escolhe pelo que combina melhor).
    Chaves principais do resultado: tipo, status, catmats (códigos CATMAT/CATSERV), precos, stats."""
    hoje = hoje or dt.date.today()
    inicio, fim = (hoje - dt.timedelta(days=JANELA_DIAS)).isoformat(), hoje.isoformat()
    catalogo_servico = catalogo_servico or []
    if tipo == "Material":
        return _cotar_material(descricao, catmat, inicio, fim, limiar)
    if tipo == "Serviço":
        return _cotar_servico(descricao, catalogo_servico, inicio, fim, limiar)

    # Automático: só gasta consultas de preço com o tipo que tem correspondência local ≥ limiar (ou com o mais forte).
    nota_material = max((f["nota"] for f in buscar_familias(descricao, catmat, limite=1)), default=0.0)
    servicos = _opcoes_servico(descricao, catalogo_servico)
    nota_servico = max((o["similaridade"] for o in servicos), default=0.0)
    tipos = [t for t, nota in (("Material", nota_material), ("Serviço", nota_servico)) if nota >= limiar]
    tipos = tipos or [("Material", "Serviço")[nota_servico > nota_material]]
    resultados = [(_cotar_material if t == "Material" else _cotar_servico)(descricao, catmat if t == "Material" else catalogo_servico, inicio, fim, limiar) for t in tipos]
    return max(resultados, key=lambda r: (_ORDEM_STATUS[r["status"]], len(r["precos"]), (r["melhor_proximo"] or {}).get("correspondencia", 0)))
