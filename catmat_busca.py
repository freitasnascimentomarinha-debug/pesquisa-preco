"""Motor de busca CATMAT/CATSERV compartilhado pelas páginas do app.

A API do Compras.gov não busca por texto; por isso a busca é feita no catálogo local
(Projeto Adesões/catalogo_catmat.csv.gz), atualizado por scripts/atualizar_catalogo_catmat.py.
"""

from __future__ import annotations

import csv
import gzip
import heapq
import json
import math
import os
import re
import unicodedata
from array import array
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from functools import lru_cache
from typing import NamedTuple

import requests
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")
CATSERV_PATH = os.path.join(CATALOGO_DIR, "catalogo_servicos.json")
CATMAT_PATH = os.path.join(CATALOGO_DIR, "catalogo_catmat.csv.gz")
META_PATH = os.path.join(CATALOGO_DIR, "catalogo_meta.json")

STOP_WORDS = {"a", "as", "com", "da", "das", "de", "do", "dos", "e", "em", "o", "os", "para", "por", "sem", "um", "uma", "tipo"}
# Termos de embalagem/unidade: descrevem como o item é comprado, não o que ele é.
# Entram na comparação com peso baixo e nunca definem o "termo principal" do item.
TERMOS_EMBALAGEM = {
    "caixa", "cx", "fardo", "folha", "pacote", "pct", "resma", "und", "unid", "unidade",
    "kg", "ml", "mm", "cm", "m2", "gr", "lt", "litro", "metro",
    # palavras que acompanham pedidos de serviço mas raramente aparecem no nome do catálogo
    "servico", "prestacao", "contratacao", "empresa", "especializada",
    "preventiva", "preventivo", "corretiva", "corretivo",
}
TERMOS_RESTRITIVOS = {
    "automotivo", "cartucho", "descartavel", "hospitalar", "impressora", "industrial",
    "infantil", "medico", "odontologico", "recarga", "refil", "tinteiro", "toner",
}
# Verbos/ações de serviço: dizem o que se faz, não o objeto ("troca de PISO", "manutenção de AR CONDICIONADO").
TERMOS_ACAO = {"troca", "manutencao", "instalacao", "reparo", "conserto", "substituicao", "remocao", "recuperacao", "reforma"}
# Termo da descrição -> grupos de termos que o catálogo usa para dizer a mesma coisa.
# Um grupo só vale se TODOS os seus termos estiverem na descrição do catálogo.
EQUIVALENCIAS = {
    "a4": [{"210", "297"}],
    "a3": [{"297", "420"}],
    "oficio": [{"216", "330"}],
    "carta": [{"216", "279"}],
    "sulfite": [{"alcalino"}, {"reprografico"}],
    "reprografico": [{"sulfite"}],
    "split": [{"parede"}],
    "troca": [{"substituicao"}, {"instalacao"}, {"manutencao"}],
    "substituicao": [{"troca"}, {"instalacao"}, {"manutencao"}],
    "reparo": [{"manutencao"}],
    "conserto": [{"manutencao"}],
    "reforma": [{"manutencao"}, {"recuperacao"}],
}
# Quando a descrição traz estes termos, o catálogo é ranqueado preferindo o produto usual da compra
# (termo -> bônus). Ex.: "resma de papel A4" sem outros detalhes = papel de escritório branco de 75 g/m².
_PAPEL_ESCRITORIO = {"sulfite": 4, "alcalino": 4, "reprografico": 4, "celulose": 3, "branca": 4, "75": 8}
PREFERENCIAS = [
    ({"papel", "resma"}, _PAPEL_ESCRITORIO),
    ({"papel", "a4"}, _PAPEL_ESCRITORIO),
]
# Consulta genérica de uma palavra só -> o que ela costuma significar numa compra (decisão do projeto).
EXPANSOES_GENERICAS = {"caneta": "caneta esferografica"}
LIMIAR_SIMILARIDADE = 45.0
CANDIDATOS_POR_CONSULTA = 200
CANDIDATOS_PARA_FAMILIAS = 2000


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto)).encode("ASCII", "ignore").decode("ASCII").lower()
    texto = re.sub(r"(\d)([a-z])", r"\1 \2", texto)  # "75g" -> "75 g"
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto)).strip()


def _radical(token: str) -> str:
    """Remove o plural simples para que 'canetas' e 'caneta' sejam o mesmo termo."""
    if len(token) > 4 and token.endswith(("oes", "aes")):
        return token[:-3] + "ao"
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _calcular_tokens(texto: str) -> tuple[str, ...]:
    vistos: dict[str, None] = {}
    for token in _normalizar(texto).split():
        if len(token) > 1 and token not in STOP_WORDS:
            vistos.setdefault(_radical(token), None)
    return tuple(vistos)


_tokens_ordenados = lru_cache(maxsize=100_000)(_calcular_tokens)


def _tokens(texto: str) -> set[str]:
    return set(_tokens_ordenados(texto))


def _tem_numero(token: str) -> bool:
    return any(caractere.isdigit() for caractere in token)


def _perfil(descricao: str) -> dict[str, object]:
    """Separa a descrição em núcleo (o que o item é), especificações (a4, 75...) e embalagem (resma, caixa...)."""
    ordem = list(_tokens_ordenados(descricao))
    macios = [token for token in ordem if token in TERMOS_EMBALAGEM]
    especificos = [token for token in ordem if token not in macios and _tem_numero(token)]
    nucleo = [token for token in ordem if token not in macios and token not in especificos] or ordem
    objeto = [token for token in nucleo if token not in TERMOS_ACAO] or nucleo
    return {"ordem": ordem, "macios": macios, "especificos": especificos, "nucleo": nucleo, "cabeca": objeto[0] if objeto else ""}


def _termo_principal(texto: str) -> str:
    """Retorna o termo que diz o que o item é, ignorando embalagem ('resma de papel' -> 'papel')."""
    return str(_perfil(texto)["cabeca"])


def _forca_termo(token: str, destino: set[str]) -> float:
    """1.0 = termo presente; menos que isso = equivalente ou variação do mesmo termo; 0 = ausente."""
    if token in destino:
        return 1.0
    if any(grupo <= destino for grupo in EQUIVALENCIAS.get(token, [])):
        return 0.85
    if len(token) >= 5 and not _tem_numero(token):
        for candidato in destino:
            menor = min(len(token), len(candidato))
            if menor >= 5 and not _tem_numero(candidato):
                comum = len(os.path.commonprefix([token, candidato]))
                if comum >= menor - 1:
                    return 0.7
    return 0.0


@st.cache_data(show_spinner=False)
def carregar_catalogo(caminho: str) -> list[dict[str, object]]:
    with open(caminho, "r", encoding="utf-8") as arquivo:
        catalogo = json.load(arquivo)
    return [
        {"codigo": str(codigo), "descricao": descricao, "tokens": sorted(_tokens(descricao))}
        for descricao, codigo in catalogo.items()
    ]


class IndiceCatmat(NamedTuple):
    itens: list[tuple[str, str, str, str]]  # (código do item, código PDM, nome PDM, descrição)
    indice: dict[str, array]  # palavra -> posições em `itens`
    por_codigo: dict[str, int]  # código do item -> posição em `itens`
    pdms: dict[str, dict[str, object]]  # código PDM -> {nome, classe, itens}
    tokens_pdm: dict[str, frozenset[str]]  # código PDM -> palavras do nome da família


@st.cache_resource(show_spinner="Carregando o catálogo CATMAT (apenas na primeira vez, ~15 s)...")
def carregar_indice_catmat(caminho: str) -> IndiceCatmat:
    """Lê o catálogo CATMAT local e monta um índice palavra -> itens (a API do Compras.gov não busca por texto)."""
    itens: list[tuple[str, str, str, str]] = []
    indice: dict[str, array] = defaultdict(lambda: array("I"))
    por_codigo: dict[str, int] = {}
    pdms: dict[str, dict[str, object]] = {}
    with gzip.open(caminho, "rt", encoding="utf-8", newline="") as arquivo:
        for posicao, linha in enumerate(csv.DictReader(arquivo)):
            nome_pdm = linha["nome_pdm"].strip('" ')
            itens.append((linha["codigo"], linha["codigo_pdm"], nome_pdm, linha["descricao"]))
            por_codigo[linha["codigo"]] = posicao
            familia = pdms.setdefault(linha["codigo_pdm"], {"nome": nome_pdm, "classe": linha.get("nome_classe", ""), "itens": 0})
            familia["itens"] += 1
            for token in set(_calcular_tokens(f"{nome_pdm} {linha['descricao']}")):
                indice[token].append(posicao)
    tokens_pdm = {codigo: frozenset(_calcular_tokens(str(familia["nome"]))) for codigo, familia in pdms.items()}
    return IndiceCatmat(itens, dict(indice), por_codigo, pdms, tokens_pdm)


def _buscar_no_catmat(descricao: str, catmat: IndiceCatmat, limite: int = CANDIDATOS_POR_CONSULTA) -> list[int]:
    """Primeira etapa: ranqueia por palavras em comum (mais raras valem mais) e devolve as posições dos melhores itens."""
    itens, indice = catmat.itens, catmat.indice
    perfil = _perfil(descricao)
    cabeca = str(perfil["cabeca"])
    termos: dict[str, float] = {}
    pesos = [(token, 2.0 if token == cabeca else 1.0) for token in perfil["nucleo"]]
    pesos += [(token, 0.8) for token in perfil["especificos"]] + [(token, 0.2) for token in perfil["macios"]]
    for token, peso in pesos:
        termos[token] = max(termos.get(token, 0), peso)
        for grupo in EQUIVALENCIAS.get(token, []):
            for equivalente in grupo:
                termos[equivalente] = max(termos.get(equivalente, 0), peso * 0.5 / len(grupo))
    pontos: dict[int, float] = defaultdict(float)
    for token, peso in termos.items():
        posicoes = indice.get(token)
        if not posicoes or (len(posicoes) > 60_000 and token != cabeca):
            continue
        idf = math.log(1 + len(itens) / len(posicoes))
        for posicao in posicoes:
            pontos[posicao] += peso * idf
    # Desempate da 1ª etapa: itens cuja família tem só os termos pedidos (família NOTEBOOK p/ "notebook") vêm antes
    # dos de famílias que apenas citam a palavra (TAMPA NOTEBOOK); sem isso, o corte de `limite` itens é arbitrário.
    consulta = set(perfil["ordem"]) | {equivalente for token in perfil["ordem"] for grupo in EQUIVALENCIAS.get(token, []) for equivalente in grupo}
    bonus_familia: dict[str, float] = {}
    for posicao in pontos:
        codigo_pdm = itens[posicao][1]
        if codigo_pdm not in bonus_familia:
            nome = catmat.tokens_pdm.get(codigo_pdm, frozenset())
            bonus_familia[codigo_pdm] = 6.0 if nome and nome <= consulta else (1.5 if cabeca in nome else 0.0)
        pontos[posicao] += bonus_familia[codigo_pdm]
    return heapq.nlargest(limite, pontos, key=pontos.__getitem__)


def _opcoes_material(descricao: str, catmat: IndiceCatmat, candidatos: int = CANDIDATOS_POR_CONSULTA) -> list[dict[str, object]]:
    itens = catmat.itens
    descricao = EXPANSOES_GENERICAS.get(" ".join(_tokens_ordenados(descricao)), descricao)  # "canetas" = "caneta"
    opcoes = []
    for posicao in _buscar_no_catmat(descricao, catmat, candidatos):
        codigo, codigo_pdm, nome_pdm, descricao_item = itens[posicao]
        bruta = _pontuar(descricao, descricao_item, nome_pdm)
        opcoes.append(
            {
                "tipo": "Material",
                "codigo": codigo,
                "descricao_catalogo": descricao_item,
                "bruta": bruta,
                "similaridade": round(max(0, min(100, bruta)), 1),
                "origem": "CATMAT",
                "codigo_pdm": codigo_pdm,
                "descricao_pdm": nome_pdm,
                "popularidade": int(catmat.pdms[codigo_pdm]["itens"]),  # desempate: a família maior costuma ser a mais comum
            }
        )
    return opcoes


@st.cache_data(ttl=3600, show_spinner=False)
def buscar_unidade_fornecimento(codigo_pdm: str) -> str:
    """Retorna a primeira unidade de fornecimento ativa associada ao PDM informado."""
    try:
        resposta = requests.get(
            "https://dadosabertos.compras.gov.br/modulo-material/6_consultarMaterialUnidadeFornecimento",
            params={"pagina": 1, "tamanhoPagina": 100, "codigoPdm": codigo_pdm, "statusUnidadeFornecimentoPdm": "true"},
            timeout=15,
        )
        if resposta.status_code != 200:
            return ""
        unidades = resposta.json().get("resultado", [])
        if not unidades:
            return ""
        unidade = unidades[0]
        sigla = unidade.get("siglaUnidadeFornecimento", "")
        nome = unidade.get("nomeUnidadeFornecimento", "")
        return f"{sigla} - {nome}".strip(" -")
    except (requests.RequestException, ValueError):
        return ""


def calcular_similaridade(descricao: str, candidato: str, nome_pdm: str = "", servico: bool = False) -> float:
    """Nota de 0 a 100 exibida ao usuário (ver _pontuar)."""
    return round(max(0, min(100, _pontuar(descricao, candidato, nome_pdm, servico))), 1)
def _pontuar(descricao: str, candidato: str, nome_pdm: str = "", servico: bool = False) -> float:
    """Pontua o quanto o item do catálogo corresponde à descrição (sem teto, para desempatar; 100 = excelente) o quanto o item do catálogo corresponde à descrição informada.

    O que pesa: o termo principal ("papel"), os demais termos do núcleo, as especificações
    (a4 casa com 210 x 297 mm) e o item do catálogo começar pelo termo principal. Embalagem
    ("resma") pesa pouco. Descrições longas de catálogo não são punidas por terem mais atributos.
    """
    perfil = _perfil(descricao)
    ordem_destino = list(_tokens_ordenados(f"{nome_pdm} {candidato}"))
    if not perfil["ordem"] or not ordem_destino:
        return 0.0
    destino = set(ordem_destino)
    cabeca = str(perfil["cabeca"])
    nucleo = list(perfil["nucleo"])

    # Nomes do CATSERV são enxutos ("PISO EM GERAL"): qualificadores do pedido (vinílico, split...) pesam menos.
    peso_demais = 0.8 if servico else 1.0
    pesos = [(token, 2.0 if token == cabeca else peso_demais) for token in nucleo]
    pesos += [(token, 0.6) for token in perfil["especificos"]] + [(token, 0.1) for token in perfil["macios"]]
    forcas = {token: _forca_termo(token, destino) for token, _ in pesos}
    cobertura = sum(peso * forcas[token] for token, peso in pesos) / sum(peso for _, peso in pesos)

    forca_cabeca = forcas.get(cabeca, 0.0)
    comeco = ordem_destino[:5 if servico else 3]
    bonus_inicio = 12 if any(_forca_termo(cabeca, {token}) >= 0.7 for token in comeco) else 0
    if ordem_destino and _forca_termo(cabeca, {ordem_destino[0]}) >= 0.7:
        bonus_inicio += 6  # o item começa pelo termo principal (CANETA ... e não PORTA-CANETA)
    obrigatorios = [cabeca] if servico else nucleo
    nucleo_completo = 8 if all(_forca_termo(token, destino) >= 0.7 for token in obrigatorios) else 0

    nome = _tokens_ordenados(re.split(r"[,;:(]", nome_pdm or candidato, maxsplit=1)[0])
    nome_completo = 15 if all(_forca_termo(token, set(nome)) >= 0.7 for token in nucleo) else 0
    sequencia = SequenceMatcher(None, " ".join(nucleo), " ".join(nome[:6])).ratio()
    extras_no_nome = [token for token in nome if _forca_termo(token, set(perfil["ordem"])) == 0 and all(_forca_termo(t, {token}) == 0 for t in nucleo)]

    bonus_preferencia = 0
    gramatura_informada = any(token.isdigit() for token in perfil["especificos"])
    for chave, preferencia in PREFERENCIAS:
        if chave <= set(perfil["ordem"]):
            bonus_preferencia += sum(
                bonus for termo, bonus in preferencia.items()
                if termo in destino and not (termo == "75" and gramatura_informada)
            )
    restritivos_ausentes = (destino - set(perfil["ordem"])) & TERMOS_RESTRITIVOS
    penalidade = min(20, len(restritivos_ausentes) * 10) + (min(16, len(extras_no_nome) * 4) if servico else min(24, len(extras_no_nome) * 6))

    pontuacao = cobertura * 72 + bonus_inicio + nucleo_completo + nome_completo + sequencia * 8 + bonus_preferencia - penalidade
    if perfil["especificos"]:
        atendidas = sum(forcas[token] for token in perfil["especificos"]) / len(perfil["especificos"])
        pontuacao *= 0.65 + 0.35 * atendidas  # especificação pedida e ausente (ex.: A4) pesa
    if not nucleo_completo:
        pontuacao *= 0.85
    if forca_cabeca == 0:
        pontuacao *= 0.35
    return pontuacao


def melhores_do_catalogo(descricao: str, catalogo: list[dict[str, object]], limite: int = 40) -> list[dict[str, object]]:
    """Pré-seleciona entradas do catálogo local que compartilham termos do núcleo com a descrição."""
    perfil = _perfil(descricao)
    cabeca = str(perfil["cabeca"])
    candidatos = []
    for item in catalogo:
        destino = set(item["tokens"])
        pontos = sum((2.0 if token == cabeca else 1.0) * _forca_termo(token, destino) for token in perfil["nucleo"])
        if pontos:
            candidatos.append((pontos, item))
    candidatos.sort(key=lambda candidato: candidato[0], reverse=True)
    return [item for _, item in candidatos[:limite]]


def _opcoes_servico(descricao: str, catalogo_servico: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "tipo": "Serviço",
            "codigo": str(item["codigo"]),
            "descricao_catalogo": str(item["descricao"]),
            "bruta": (bruta := _pontuar(descricao, str(item["descricao"]), "", True)),
            "similaridade": round(max(0, min(100, bruta)), 1),
            "origem": "CATSERV",
            "codigo_pdm": "",
            "descricao_pdm": "",
        }
        for item in melhores_do_catalogo(descricao, catalogo_servico)
    ]


def _resumo_alternativa(opcao: dict[str, object]) -> str:
    descricao = str(opcao["descricao_catalogo"])
    return f"{opcao['codigo']} ({opcao['similaridade']:.0f}%) {descricao[:90]}{'…' if len(descricao) > 90 else ''}"


def sugerir_codigo(descricao: str, catmat: IndiceCatmat, catalogo_servico: list[dict[str, object]], tipo: str) -> dict[str, object]:
    opcoes: list[dict[str, object]] = []
    if tipo in ("Automático", "Material"):
        opcoes += _opcoes_material(descricao, catmat)
    if tipo in ("Automático", "Serviço"):
        opcoes += _opcoes_servico(descricao, catalogo_servico)

    vazio = {"tipo": "-", "codigo": "-", "similaridade": 0.0, "origem": "-", "unidade_fornecimento": "", "codigo_pdm": "", "descricao_pdm": "", "alternativas": ""}
    if not opcoes:
        return {**vazio, "descricao_catalogo": "Nenhuma correspondência encontrada"}
    opcoes.sort(key=lambda opcao: (round(opcao["bruta"], 1), opcao.get("popularidade", 0)), reverse=True)
    melhor = opcoes[0]
    if melhor["similaridade"] < LIMIAR_SIMILARIDADE:
        return {**vazio, "descricao_catalogo": "Descrição insuficiente para sugerir um código com segurança", "similaridade": melhor["similaridade"]}
    alternativas = [opcao for opcao in opcoes[1:4] if opcao["similaridade"] >= LIMIAR_SIMILARIDADE - 10]
    return {
        **melhor,
        "unidade_fornecimento": buscar_unidade_fornecimento(str(melhor["codigo_pdm"])) if melhor["codigo_pdm"] else "",
        "alternativas": "\n".join(_resumo_alternativa(opcao) for opcao in alternativas),
    }


def atualizado_em() -> str:
    """Data (dd/mm/aaaa) da última atualização dos catálogos locais, ou '' se desconhecida."""
    try:
        with open(META_PATH, "r", encoding="utf-8") as arquivo:
            return datetime.fromisoformat(json.load(arquivo)["atualizado_em"]).strftime("%d/%m/%Y")
    except (OSError, ValueError, KeyError):
        return ""


def _ficha_familia(catmat: IndiceCatmat, codigo_pdm: str, nota: float, motivo: str) -> dict[str, object]:
    familia = catmat.pdms[codigo_pdm]
    return {
        "codigo": codigo_pdm,
        "nome": str(familia["nome"]),
        "classe": str(familia["classe"]),
        "itens": int(familia["itens"]),
        "nota": round(max(0, min(100, nota)), 1),
        "exemplo": motivo,
    }


def buscar_familias(consulta: str, catmat: IndiceCatmat, limite: int = 15) -> list[dict[str, object]]:
    """Famílias de material (PDM) mais prováveis para um texto livre, código de item CATMAT ou código de PDM."""
    consulta = consulta.strip()
    if not consulta:
        return []
    if consulta.isdigit():
        posicao = catmat.por_codigo.get(consulta)
        if posicao is not None:
            _, codigo_pdm, _, descricao = catmat.itens[posicao]
            return [_ficha_familia(catmat, codigo_pdm, 100, f"Item CATMAT {consulta}: {descricao[:110]}")]
        if consulta in catmat.pdms:
            return [_ficha_familia(catmat, consulta, 100, "Código de PDM informado")]
        return []
    melhores: dict[str, dict[str, object]] = {}
    for opcao in _opcoes_material(consulta, catmat, CANDIDATOS_PARA_FAMILIAS):  # pool maior: a família certa pode ter itens pouco parecidos
        atual = melhores.setdefault(opcao["codigo_pdm"], {"bruta": opcao["bruta"], "exemplo": opcao["descricao_catalogo"], "casam": 0})
        atual["casam"] += 1
        if opcao["bruta"] > atual["bruta"]:
            atual["bruta"], atual["exemplo"] = opcao["bruta"], opcao["descricao_catalogo"]
    ordenadas = sorted(melhores.items(), key=lambda par: (round(par[1]["bruta"], 1), catmat.pdms[par[0]]["itens"]), reverse=True)
    return [
        _ficha_familia(catmat, codigo_pdm, dados["bruta"], f"Ex.: {str(dados['exemplo'])[:110]}")
        for codigo_pdm, dados in ordenadas[:limite]
        if dados["bruta"] >= 30
    ]


def buscar_servicos(consulta: str, catalogo_servico: list[dict[str, object]], limite: int = 8) -> list[dict[str, object]]:
    """Serviços (CATSERV) mais prováveis para um texto livre ou código de serviço."""
    consulta = consulta.strip()
    if not consulta:
        return []
    if consulta.isdigit():
        return [
            {"codigo": str(item["codigo"]), "nome": str(item["descricao"]), "nota": 100.0}
            for item in catalogo_servico if str(item["codigo"]) == consulta
        ]
    opcoes = sorted(_opcoes_servico(consulta, catalogo_servico), key=lambda opcao: opcao["bruta"], reverse=True)
    return [
        {"codigo": str(opcao["codigo"]), "nome": str(opcao["descricao_catalogo"]), "nota": opcao["similaridade"]}
        for opcao in opcoes[:limite]
        if opcao["bruta"] >= 30
    ]
