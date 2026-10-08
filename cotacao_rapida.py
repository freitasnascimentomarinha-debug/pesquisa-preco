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

from catmat_busca import TERMOS_ACAO, TERMOS_GENERICOS, IndiceCatmat, _opcoes_servico, _perfil, _calcular_tokens, buscar_familias, calcular_similaridade

API_PRECOS = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"
API_PRECOS_SERVICO = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/3_consultarServico"
LIMIAR_CORRESPONDENCIA = 75.0  # % mínimo de correspondência entre a descrição e o item CATMAT (material)
LIMIAR_SERVICO = 65.0  # idem para CATSERV: os nomes de serviço são enxutos e raramente repetem os qualificadores do pedido
LIMIAR_FAMILIA = 60.0  # famílias (PDM) abaixo disso nem têm os preços consultados
MAX_CATMAT = 3
MAX_PRECOS = 5
MIN_PRECOS = 3  # abaixo disso o item é sinalizado (IN SEGES/ME nº 65/2021 recomenda ao menos três preços)
TOLERANCIA = 0.30  # cada preço deve ficar a até 30% (para mais ou para menos) da média dos preços listados
JANELA_DIAS = 365
MAX_FAMILIAS = 12
TOLERANCIA_ESTIMATIVA = 0.40  # preço médio dentro de ±40% da estimativa do usuário = coerente
LIMIAR_FAMILIA_COM_ESTIMATIVA = 45.0  # com estimativa, famílias menos parecidas também são consultadas (para achar outro CATMAT possível)
LIMIAR_ALTERNATIVA = 45.0  # % mínimo de correspondência para um CATMAT não escolhido ser sugerido como alternativa pelo preço
MIN_REGISTROS_ALTERNATIVA = 2
LIMIAR_PRIORIZAR_ESTIMATIVA = 60.0  # com estimativa, só CATMAT com ao menos esta correspondência podem passar na frente...
MARGEM_PRIORIZAR_ESTIMATIVA = 15.0  # ...e só se estiverem a até esta margem (em pontos) do mais parecido: um item de outro tipo nunca ganha só pelo preço
MIN_PERTO_ESTIMATIVA = 3  # compras do CATMAT perto da estimativa (±40%) para considerá-lo compatível em preço
LIMIAR_ALTERNATIVA_FORTE = 70.0  # com o preço já coerente, só vale sugerir outro CATMAT que também case bem
MAX_ALTERNATIVAS = 3
MAX_CANDIDATOS_SERVICO = 40  # serviços do catálogo cujos preços são conferidos antes de escolher os 3 melhores
DECLARACOES_DE_SERVICO = {"servico", "prestacao", "contratacao", "terceirizacao"}
MARCADORES_SERVICO = {"servico", "prestacao", "contratacao", "locacao", "terceirizacao"} | TERMOS_ACAO
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


def resultado_vazio(descricao: str, tipo: str = "Material") -> dict:
    return {
        "descricao": descricao, "tipo": tipo, "status": "sem_catmat", "catmats": [], "precos": [], "stats": None,
        "unidade": "", "unidade_curta": "", "brutos": 0, "outliers": 0, "faixa_validos": None,
        "falha_api": False, "melhor_proximo": None, "proximos": [], "alternativas_preco": [], "limiar": LIMIAR_SERVICO if tipo == "Serviço" else LIMIAR_CORRESPONDENCIA,
    }


def _concluir(resultado: dict, escolhidos: list[tuple[float, int, object, str]], por_item: dict[object, list[dict]],
              estimativa: float | None = None, priorizar: bool = True) -> dict:
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
    amostra = limpos
    resultado["faixa_estimativa"] = None
    if estimativa and priorizar:  # com estimativa, os preços listados saem das compras próximas dela (±40%), se houver ao menos MIN_PRECOS
        faixa = (estimativa * (1 - TOLERANCIA_ESTIMATIVA), estimativa * (1 + TOLERANCIA_ESTIMATIVA))
        na_faixa = [r for r in mesma_unidade if faixa[0] <= r["preco"] <= faixa[1]]
        if len(na_faixa) >= MIN_PRECOS:
            amostra, resultado["faixa_estimativa"] = na_faixa, faixa
    resultado["precos"] = selecionar_precos(amostra)
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


def _preco_do_codigo(registros: list[dict]) -> tuple[float | None, str, int]:
    """(mediana dos preços na unidade dominante, unidade, nº de registros) de um CATMAT."""
    mesma_unidade, _, unidade_curta = _unidade_dominante(registros)
    precos = [r["preco"] for r in mesma_unidade]
    return (float(statistics.median(precos)) if precos else None), unidade_curta, len(precos)


def _compras_perto(registros: list[dict], estimativa: float) -> tuple[int, int]:
    """(compras do CATMAT a até ±TOLERANCIA_ESTIMATIVA da estimativa, total de compras na unidade dominante). A mediana de todas não serve:
    um mesmo CATMAT pode ter preços de R$ 80 a R$ 1.600 e ainda assim ser o produto certo."""
    mesma_unidade, _, _ = _unidade_dominante(registros)
    perto = sum(1 for r in mesma_unidade if abs(r["preco"] / estimativa - 1) <= TOLERANCIA_ESTIMATIVA)
    return perto, len(mesma_unidade)


def _cotar_material(descricao: str, catmat: IndiceCatmat, inicio: str, fim: str, estimativa: float | None = None,
                    forcar: list[str] | None = None, priorizar: bool = True) -> dict:
    resultado = resultado_vazio(descricao, "Material")
    limiar = resultado["limiar"]
    corte_familia = min(LIMIAR_FAMILIA, limiar - 10) if not estimativa else LIMIAR_FAMILIA_COM_ESTIMATIVA
    familias = [f for f in buscar_familias(descricao, catmat, limite=MAX_FAMILIAS) if f["nota"] >= corte_familia]
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
    resultado["escolha"] = "parecido"
    if forcar:  # o usuário escolheu o(s) código(s): vale mesmo abaixo do limiar de correspondência
        pedidos = {str(codigo) for codigo in forcar}
        manuais = [c for c in classificados if str(c[2]) in pedidos]
        if manuais:
            escolhidos, resultado["escolha"] = manuais[:MAX_CATMAT], "manual"
    elif estimativa and priorizar:  # a estimativa orienta: entre os CATMAT bem parecidos, os que praticam preço compatível passam na frente
        melhor_nota = classificados[0][0] if classificados else 0.0
        corte = max(LIMIAR_PRIORIZAR_ESTIMATIVA, melhor_nota - MARGEM_PRIORIZAR_ESTIMATIVA)  # só os "empatados" com o mais parecido disputam pelo preço
        compativeis = []
        for candidato in classificados:
            if candidato[0] < corte:
                break  # classificados está em ordem decrescente de correspondência
            perto, _ = _compras_perto(por_item[candidato[2]], estimativa)
            if perto >= MIN_PERTO_ESTIMATIVA:
                compativeis.append(candidato)
        if compativeis and {c[2] for c in compativeis[:MAX_CATMAT]} != {c[2] for c in escolhidos}:
            escolhidos, resultado["escolha"] = compativeis[:MAX_CATMAT], "estimativa"
    if estimativa:  # CATMAT que não entraram na cotação, com o preço que praticam: serve para conferir a estimativa do usuário
        escolhidos_codigos = {c[2] for c in escolhidos}
        for nota, _, codigo, descricao_catalogo in classificados:
            if codigo in escolhidos_codigos or nota < LIMIAR_ALTERNATIVA:
                continue
            mediana, unidade_curta, registros = _preco_do_codigo(por_item[codigo])
            if mediana is not None and registros >= MIN_REGISTROS_ALTERNATIVA:
                perto, _ = _compras_perto(por_item[codigo], estimativa)
                resultado["alternativas_preco"].append({"codigo": codigo, "correspondencia": nota, "descricao": descricao_catalogo, "mediana": mediana,
                                                        "registros": registros, "perto": perto, "unidade": unidade_curta})
    return _concluir(resultado, escolhidos, por_item, estimativa, priorizar) if escolhidos else resultado


def _cotar_servico(descricao: str, catalogo_servico: list[dict], inicio: str, fim: str) -> dict:
    resultado = resultado_vazio(descricao, "Serviço")
    limiar = resultado["limiar"]
    opcoes = sorted(_opcoes_servico(descricao, catalogo_servico), key=lambda o: o["bruta"], reverse=True)
    resultado["proximos"] = [{"codigo": o["codigo"], "correspondencia": o["similaridade"], "descricao": o["descricao_catalogo"]} for o in opcoes[:MAX_CATMAT]]
    resultado["melhor_proximo"] = resultado["proximos"][0] if opcoes else None
    candidatos = [o for o in opcoes if o["similaridade"] >= limiar][:MAX_CANDIDATOS_SERVICO]
    objeto = str(_perfil(descricao)["cabeca"])
    disse_servico = "servico" in _calcular_tokens(descricao)  # "serviço de limpeza" -> prefere "PRESTACAO DE SERVICO DE LIMPEZA..."
    if not candidatos:
        return resultado
    with ThreadPoolExecutor(max_workers=4) as executor:  # primeiro só a contagem: poucos serviços têm preços no período
        totais = list(executor.map(lambda o: total_de_precos_do_servico(str(o["codigo"]), inicio, fim), candidatos))
    # Correspondências próximas (faixas de 15 pontos) empatam e vence o serviço com mais preços praticados: num pedido
    # genérico ("serviço de limpeza") o mais representativo é o mais contratado, não o primeiro da lista.
    com_precos = sorted(((o, n) for o, n in zip(candidatos, totais) if n > 0), key=lambda par: (int(par[0]["similaridade"] // 15), _comeca_pelo_objeto(par[0]["descricao_catalogo"], objeto), disse_servico and "servico" in _calcular_tokens(par[0]["descricao_catalogo"]), par[1]), reverse=True)[:MAX_CATMAT]
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


_INICIO_SERVICOS: dict[int, dict[str, int]] = {}


def _inicio_servicos(catalogo_servico: list[dict]) -> dict[str, int]:
    """Quantos nomes de serviço começam por cada palavra (ignorando ação/genéricas: "MANUTENCAO DE PISO" conta como piso)."""
    chave = id(catalogo_servico)
    if chave not in _INICIO_SERVICOS:
        contagem: dict[str, int] = defaultdict(int)
        for item in catalogo_servico:
            primeira = next((t for t in _calcular_tokens(str(item["descricao"])) if t not in TERMOS_ACAO and t not in TERMOS_GENERICOS), None)
            if primeira:
                contagem[primeira] += 1
        _INICIO_SERVICOS[chave] = dict(contagem)
    return _INICIO_SERVICOS[chave]


def _comeca_pelo_objeto(nome: str, objeto: str) -> bool:
    """O nome do serviço começa (ignorando ação/palavras genéricas) pelo objeto pedido? ("LIMPEZA URBANA" p/ limpeza; não "AR CONDICIONADO - ... LIMPEZA")."""
    primeira = next((t for t in _calcular_tokens(nome) if t not in TERMOS_ACAO and t not in TERMOS_GENERICOS), "")
    return primeira == objeto


_ORDEM_STATUS = {"ok": 3, "insuficiente": 2, "sem_precos": 1, "sem_catmat": 0}


def _brl(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def aplicar_estimativa(resultado: dict, estimativa: float | None) -> dict:
    """Confere a cotação com o preço que o usuário estima para o item: o preço médio dos CATMAT escolhidos bate com a estimativa? E algum CATMAT que ficou
    de fora (parecido, mas abaixo do mínimo) pratica preço mais próximo dela? Só avisa: nunca troca o CATMAT sozinho.
    Preenche `estimativa`, `validacao` ('coerente', 'divergente', 'sem_precos' ou None sem estimativa), `compativeis` e `texto_validacao`."""
    resultado.update({"estimativa": None, "validacao": None, "compativeis": [], "texto_validacao": ""})
    if not estimativa or estimativa <= 0:
        return resultado
    resultado["estimativa"] = float(estimativa)
    compativeis = [a for a in resultado.get("alternativas_preco", []) if a.get("perto", 0) >= MIN_REGISTROS_ALTERNATIVA]
    compativeis.sort(key=lambda a: (-a["correspondencia"], -a["perto"]))
    partes = []
    escolha = resultado.get("escolha", "parecido")
    if escolha == "estimativa":
        partes.append("🎯 CATMAT escolhido pela estimativa: entre os igualmente parecidos, são os que têm compras perto dela.")
    elif escolha == "manual":
        partes.append("👆 CATMAT escolhido por você.")
    if resultado.get("faixa_estimativa"):
        baixo, alto = resultado["faixa_estimativa"]
        partes.append(f"Preços listados escolhidos entre as compras de {_brl(baixo)} a {_brl(alto)} (±{TOLERANCIA_ESTIMATIVA:.0%} da estimativa).")
    if resultado["stats"]:
        media = resultado["stats"]["media"]
        desvio = media / estimativa - 1
        resultado["validacao"] = "coerente" if abs(desvio) <= TOLERANCIA_ESTIMATIVA else "divergente"
        if resultado["validacao"] == "coerente":  # preço e CATMAT já batem: só sugere outro se for bem parecido e ainda mais próximo da estimativa
            compativeis = [a for a in compativeis if a["correspondencia"] >= LIMIAR_ALTERNATIVA_FORTE and a["perto"] >= max(MIN_PERTO_ESTIMATIVA, a["registros"] // 2)]
    resultado["compativeis"] = compativeis[:MAX_ALTERNATIVAS]
    if resultado["stats"]:
        if resultado["validacao"] == "coerente":
            partes.append(f"✅ Preço médio {_brl(media)} coerente com a estimativa de {_brl(estimativa)} ({desvio:+.0%}).")
        else:
            partes.append(f"⚠️ Preço médio {_brl(media)} está {abs(desvio):.0%} {'acima' if desvio > 0 else 'abaixo'} da estimativa de {_brl(estimativa)}: confira o CATMAT, a unidade ou a estimativa."
                          + ("" if resultado.get("compativeis") or escolha != "parecido" else f" Nenhum CATMAT com {LIMIAR_PRIORIZAR_ESTIMATIVA:.0f}% ou mais de correspondência pratica preço perto dela: foi mantido o mais parecido."))
    else:
        resultado["validacao"] = "sem_precos"
        partes.append("Sem preços para comparar com a estimativa.")
    if resultado["compativeis"]:
        partes.append("💡 Outro(s) CATMAT parecido(s) pratica(m) preço compatível com a estimativa: " + "; ".join(
            f"{a['codigo']} ({a['correspondencia']:.0f}%, {a['perto']} de {a['registros']} compras perto da estimativa)" for a in resultado["compativeis"]) + ". Veja se o item pedido não é um deles.")
    resultado["texto_validacao"] = " ".join(partes)
    return resultado


def cotar_item(descricao: str, catmat: IndiceCatmat, catalogo_servico: list[dict] | None = None, tipo: str = "Material", hoje: dt.date | None = None,
               estimativa: float | None = None, forcar: list[str] | None = None, priorizar: bool = True) -> dict:
    """Cotação de uma descrição (ver _cotar_item_base). Com `estimativa` (R$ por unidade, opcional), valida preço e CATMAT contra ela (aplicar_estimativa) e,
    se `priorizar`, deixa os CATMAT bem parecidos de preço compatível passarem na frente. `forcar`: códigos CATMAT escolhidos pelo usuário (material)."""
    return aplicar_estimativa(_cotar_item_base(descricao, catmat, catalogo_servico, tipo, hoje, estimativa, forcar, priorizar), estimativa)


def _cotar_item_base(descricao: str, catmat: IndiceCatmat, catalogo_servico: list[dict] | None = None, tipo: str = "Material", hoje: dt.date | None = None,
                     estimativa: float | None = None, forcar: list[str] | None = None, priorizar: bool = True) -> dict:
    """Cotação de uma descrição. `tipo`: "Material" (mín. 75%), "Serviço" (mín. 65%) ou "Automático" (escolhe pelo que combina melhor).
    Chaves principais do resultado: tipo, status, catmats (códigos CATMAT/CATSERV), precos, stats."""
    hoje = hoje or dt.date.today()
    inicio, fim = (hoje - dt.timedelta(days=JANELA_DIAS)).isoformat(), hoje.isoformat()
    catalogo_servico = catalogo_servico or []
    if tipo == "Material":
        return _cotar_material(descricao, catmat, inicio, fim, estimativa, forcar, priorizar)
    if tipo == "Serviço":
        return _cotar_servico(descricao, catalogo_servico, inicio, fim)

    # Automático: decide o tipo antes de gastar consultas de preço.
    nota_material = max((f["nota"] for f in buscar_familias(descricao, catmat, limite=1)), default=0.0)
    nota_servico = max((o["similaridade"] for o in _opcoes_servico(descricao, catalogo_servico)), default=0.0)
    material_ok, servico_ok = nota_material >= LIMIAR_CORRESPONDENCIA, nota_servico >= LIMIAR_SERVICO
    perfil = _perfil(descricao)
    palavras = set(perfil["ordem"])
    inicio_material = catmat.inicio_pdm.get(str(perfil["cabeca"]), 0)
    inicio_servico = _inicio_servicos(catalogo_servico).get(str(perfil["cabeca"]), 0)
    if palavras & DECLARACOES_DE_SERVICO:
        tipos = ["Serviço"]  # o pedido diz "serviço"/"prestação"/"contratação": é serviço, mesmo que o catálogo não tenha nome parecido
    elif servico_ok and (palavras & MARCADORES_SERVICO):
        tipos = ["Serviço"]  # "serviço de limpeza", "troca de piso", "manutenção de ...": o pedido diz que é serviço
    elif servico_ok and inicio_servico and inicio_servico >= 2 * inicio_material:
        tipos = ["Serviço"]  # "pintura predial", "limpeza": nomes de serviço começam assim bem mais que famílias de material
    elif material_ok and inicio_material and inicio_material >= 2 * inicio_servico:
        tipos = ["Material"]
    else:
        tipos = [t for t, ok in (("Material", material_ok), ("Serviço", servico_ok)) if ok]
        tipos = tipos or [("Material", "Serviço")[nota_servico - LIMIAR_SERVICO > nota_material - LIMIAR_CORRESPONDENCIA]]
    resultados = [_cotar_material(descricao, catmat, inicio, fim, estimativa, forcar, priorizar) if t == "Material" else _cotar_servico(descricao, catalogo_servico, inicio, fim) for t in tipos]
    return max(resultados, key=lambda r: (_ORDEM_STATUS[r["status"]], len(r["precos"]), max((k["correspondencia"] for k in r["catmats"]), default=0), (r["melhor_proximo"] or {}).get("correspondencia", 0)))
