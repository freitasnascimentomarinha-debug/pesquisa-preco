"""Pesquisa em lote nas notas fiscais (Portal da Transparência): vários itens, todos os arquivos mensais, uma só leitura.

Cada arquivo CSV é lido uma única vez (em blocos) e, em cada bloco, todos os itens pedidos são procurados ao mesmo tempo.
Os arquivos são baixados/lidos em paralelo. Depois, os preços de cada item passam pela mesma limpeza e seleção da
Cotação Rápida (sem outliers, até 5 preços a até 30% da média).
"""

from __future__ import annotations

import datetime as dt
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import pandas as pd

from catmat_busca import EQUIVALENCIAS, _perfil
from cotacao_rapida import MAX_PRECOS, MIN_PRECOS, TOLERANCIA, _unidade_dominante, estatisticas, remover_outliers, selecionar_precos

COL_DESCRICAO = "DESCRIÇÃO DO PRODUTO/SERVIÇO"
COL_NOME_DEST = "NOME DESTINATÁRIO"
COL_UF_DEST = "UF DESTINATÁRIO"
COL_UF_EMIT = "UF EMITENTE"
COL_CNPJ = "CPF/CNPJ Emitente"
COL_RAZAO = "RAZÃO SOCIAL EMITENTE"
COLUNAS_UTEIS = [
    "DATA EMISSÃO", COL_DESCRICAO, "UNIDADE", "QUANTIDADE", "VALOR UNITÁRIO", "VALOR TOTAL", COL_UF_DEST, COL_NOME_DEST,
    "ÓRGÃO DESTINATÁRIO", COL_RAZAO, COL_CNPJ, COL_UF_EMIT, "MUNICÍPIO EMITENTE", "NCM/SH (TIPO DE PRODUTO)",
    "CHAVE DE ACESSO", "NATUREZA DA OPERAÇÃO", "NÚMERO", "SÉRIE",
]
TAMANHO_BLOCO = 100_000
LIMITE_CACHE_BYTES = 4 * 1024**3  # arquivos baixados além disso são descartados (os menos recentes primeiro)
UNIDADES_EQUIVALENTES = {
    "UN": "UN", "UND": "UN", "UNID": "UN", "UNI": "UN", "UNIDADE": "UN", "PC": "UN", "PÇ": "UN", "PECA": "UN", "PEÇA": "UN",
    "CX": "CX", "CAIXA": "CX", "PCT": "PCT", "PACOTE": "PCT", "PT": "PCT", "RESMA": "RESMA", "RM": "RESMA",
    "KG": "KG", "KILO": "KG", "QUILO": "KG", "L": "L", "LT": "L", "LITRO": "L", "M": "M", "MT": "M", "METRO": "M",
    "M2": "M2", "M²": "M2", "FR": "FR", "FRASCO": "FR", "GL": "GL", "GALAO": "GL", "GALÃO": "GL", "KIT": "KIT", "JG": "JG", "JOGO": "JG",
}

_ACENTOS = {"a": "aáàâãä", "e": "eéèêë", "i": "iíìîï", "o": "oóòôõö", "u": "uúùûü", "c": "cç", "n": "nñ"}


def _letra(caractere: str) -> str:
    return f"[{_ACENTOS[caractere]}]" if caractere in _ACENTOS else re.escape(caractere)


def padrao_token(token: str) -> str:
    """Regex que acha o termo no texto da nota ignorando acentos e maiúsculas; letras casam por prefixo (plural)."""
    corpo = "".join(_letra(c) for c in token)
    if token.isdigit():
        return rf"(?<!\d){corpo}(?!\d)"
    if any(c.isdigit() for c in token):
        return rf"(?<!\w){corpo}(?!\w)"
    return rf"(?<!\w){corpo}"


def padrao_frase(texto: str) -> str:
    """Regex de trecho exato (como o filtro 'contém' da página original), ignorando acentos."""
    return r"\s+".join("".join(_letra(c) for c in palavra.lower()) for palavra in texto.split())


Termo = list[list[str]]  # alternativas; cada alternativa é uma lista de padrões que precisam casar juntos


def _termo(token: str) -> Termo:
    alternativas = [[padrao_token(token)]]
    for grupo in EQUIVALENCIAS.get(token, []):
        alternativas.append([padrao_token(equivalente) for equivalente in sorted(grupo)])  # ex.: a4 = 210 e 297
    return alternativas


def montar_item(descricao: str) -> dict:
    """Transforma a descrição digitada em exigências: todas as palavras do núcleo e as especificações (a4, 75...)."""
    perfil = _perfil(descricao)
    cabeca = str(perfil["cabeca"])
    exigidos = ([cabeca] if cabeca else []) + [t for t in perfil["nucleo"] if t != cabeca] + list(perfil["especificos"])
    termos = [_termo(token) for token in exigidos]
    cabeca_simples = [alt[0] for alt in termos[0] if len(alt) == 1] if termos and cabeca else []
    return {"descricao": descricao, "termos": termos, "prefiltro": "|".join(f"(?:{p})" for p in cabeca_simples) or None}


def _casa(serie: pd.Series, termo: Termo) -> pd.Series:
    resultado = pd.Series(False, index=serie.index)
    for alternativa in termo:
        atual = pd.Series(True, index=serie.index)
        for padrao in alternativa:
            atual &= serie.str.contains(padrao, case=False, regex=True, na=False)
        resultado |= atual
    return resultado


def _aplicar_filtros(bloco: pd.DataFrame, filtros: dict) -> pd.DataFrame:
    if filtros.get("nome_dest") and COL_NOME_DEST in bloco.columns:
        bloco = bloco[bloco[COL_NOME_DEST].str.contains(padrao_frase(filtros["nome_dest"]), case=False, regex=True, na=False)]
    if filtros.get("uf_dest") and COL_UF_DEST in bloco.columns:
        bloco = bloco[bloco[COL_UF_DEST].astype(str).str.upper().eq(filtros["uf_dest"].strip().upper())]
    if filtros.get("uf_emit") and COL_UF_EMIT in bloco.columns:
        bloco = bloco[bloco[COL_UF_EMIT].astype(str).str.upper().eq(filtros["uf_emit"].strip().upper())]
    if filtros.get("emitente") and COL_RAZAO in bloco.columns:
        bloco = bloco[bloco[COL_RAZAO].str.contains(padrao_frase(filtros["emitente"]), case=False, regex=True, na=False)]
    return bloco


def varrer_arquivo(caminho: str, itens: list[dict], filtros: dict, max_por_item: int) -> tuple[dict[int, pd.DataFrame], int]:
    """Lê o CSV uma vez e devolve, por item, as linhas que casam. Retorna ({posição do item: linhas}, linhas analisadas)."""
    achados: dict[int, list[pd.DataFrame]] = {i: [] for i in range(len(itens))}
    contagem = {i: 0 for i in range(len(itens))}
    total_linhas = 0
    uniao = "|".join(item["prefiltro"] for item in itens if item["prefiltro"])
    todos_prefiltrados = all(item["prefiltro"] for item in itens)
    for bloco in pd.read_csv(
        caminho, sep=";", encoding="latin-1", chunksize=TAMANHO_BLOCO, dtype=str, on_bad_lines="skip",
        usecols=lambda coluna: coluna in COLUNAS_UTEIS,
    ):
        total_linhas += len(bloco)
        if COL_DESCRICAO not in bloco.columns:
            continue
        bloco = _aplicar_filtros(bloco, filtros)
        if todos_prefiltrados and uniao and not bloco.empty:
            bloco = bloco[bloco[COL_DESCRICAO].str.contains(uniao, case=False, regex=True, na=False)]
        if bloco.empty:
            continue
        for posicao, item in enumerate(itens):
            if contagem[posicao] >= max_por_item:
                continue
            mascara = pd.Series(True, index=bloco.index)
            for termo in item["termos"]:
                mascara &= _casa(bloco[COL_DESCRICAO], termo)
                if not mascara.any():
                    break
            if mascara.any():
                linhas = bloco[mascara].head(max_por_item - contagem[posicao])
                achados[posicao].append(linhas)
                contagem[posicao] += len(linhas)
        if all(contagem[i] >= max_por_item for i in contagem):
            break
    return {i: (pd.concat(lista, ignore_index=True) if lista else pd.DataFrame()) for i, lista in achados.items()}, total_linhas


def limitar_cache(pasta: str, manter: set[str], limite: int = LIMITE_CACHE_BYTES, idade_minima: float = 180) -> None:
    """Descarta arquivos baixados antigos quando o cache passa do limite (nunca os de `manter` nem os baixados há pouco)."""
    try:
        arquivos = [os.path.join(pasta, nome) for nome in os.listdir(pasta) if nome.endswith(".csv")]
        tamanho = sum(os.path.getsize(a) for a in arquivos)
        for caminho in sorted(arquivos, key=os.path.getmtime):
            if tamanho <= limite:
                break
            if os.path.basename(caminho) not in manter and time.time() - os.path.getmtime(caminho) > idade_minima:
                tamanho -= os.path.getsize(caminho)
                os.remove(caminho)
    except OSError:
        pass


def pesquisar_em_lote(
    descricoes: list[str],
    arquivos: list[tuple[str, str]],
    baixar: Callable[[str], str],
    filtros: dict,
    max_por_item: int = 1500,
    progresso: Callable[[int, int, str], None] | None = None,
    trabalhadores: int = 3,
    pasta_cache: str | None = None,
) -> dict:
    """Procura todos os itens em todos os arquivos. `arquivos` = [(id, nome)], `baixar(id)` devolve o caminho do CSV.

    Retorna {"itens": [DataFrame por item], "linhas": total analisado, "arquivos_ok": [...], "erros": {nome: mensagem}}."""
    itens = [montar_item(d) for d in descricoes]
    por_arquivo: dict[str, dict[int, pd.DataFrame]] = {}
    erros: dict[str, str] = {}
    linhas = 0

    def tarefa(identificador: str) -> tuple[dict[int, pd.DataFrame], int]:
        caminho = baixar(identificador)
        resultado = varrer_arquivo(caminho, itens, filtros, max_por_item)
        if pasta_cache:  # libera disco enquanto pesquisa: arquivos grandes de vários meses não cabem todos no cache
            limitar_cache(pasta_cache, manter={os.path.basename(caminho)})
        return resultado

    with ThreadPoolExecutor(max_workers=trabalhadores) as executor:
        futuros = {executor.submit(tarefa, identificador): nome for identificador, nome in arquivos}
        for feitos, futuro in enumerate(as_completed(futuros), start=1):
            nome = futuros[futuro]
            try:
                resultado, n = futuro.result()
                por_arquivo[nome] = resultado
                linhas += n
            except Exception as erro:  # um arquivo com problema (cota do Drive, CSV corrompido) não derruba os demais
                erros[nome] = str(erro)[:200]
            if progresso:
                progresso(feitos, len(arquivos), nome)

    nomes_recentes = sorted(por_arquivo, reverse=True)  # arquivos com data no nome (AAAAMM_...): mais recentes primeiro
    resultado_itens = []
    for posicao in range(len(itens)):
        partes = [por_arquivo[nome][posicao] for nome in nomes_recentes if not por_arquivo[nome][posicao].empty]
        resultado_itens.append(pd.concat(partes, ignore_index=True).head(max_por_item) if partes else pd.DataFrame())
    return {"itens": resultado_itens, "linhas": linhas, "arquivos_ok": nomes_recentes, "erros": erros}


# ---------------------------------------------------------------- conversão das linhas em preços

def _numero_br(valor: object) -> float | None:
    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _data_iso(valor: object) -> str:
    texto = str(valor).strip()[:10]
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(texto, formato).date().isoformat()
        except ValueError:
            continue
    return texto


def _unidade(valor: object) -> str:
    texto = str(valor).strip().upper()
    return UNIDADES_EQUIVALENTES.get(texto, texto) if texto and texto != "NAN" else "N/I"


def numero_e_serie(chave: str, numero_coluna: object = "", serie_coluna: object = "") -> tuple[str, str]:
    """Número e série da NF-e. Saem da chave de acesso (44 dígitos: UF, AAMM, CNPJ, modelo, série, número...); se a chave
    não estiver íntegra, usa as colunas NÚMERO/SÉRIE do arquivo."""
    digitos = re.sub(r"\D", "", str(chave or ""))
    if len(digitos) == 44:
        return str(int(digitos[25:34])), str(int(digitos[22:25]))
    limpo = lambda v: "" if str(v).strip().lower() in ("", "nan", "none") else str(v).strip()  # noqa: E731
    return limpo(numero_coluna), limpo(serie_coluna)


def registros_das_linhas(linhas: pd.DataFrame) -> list[dict]:
    """Linhas do CSV -> registros no formato usado pelo motor de preços da Cotação Rápida."""
    registros = []
    for indice, linha in linhas.iterrows():
        preco = _numero_br(linha.get("VALOR UNITÁRIO"))
        if preco is None or preco <= 0:
            continue
        unidade = _unidade(linha.get("UNIDADE"))
        numero_nf, serie = numero_e_serie(linha.get("CHAVE DE ACESSO", ""), linha.get("NÚMERO", ""), linha.get("SÉRIE", ""))
        registros.append({
            "id_compra": str(linha.get("CHAVE DE ACESSO", "") or ""), "id_item": indice,
            "data": _data_iso(linha.get("DATA EMISSÃO", "")), "cnpj": re.sub(r"\D", "", str(linha.get(COL_CNPJ, "") or "")),
            "fornecedor": str(linha.get(COL_RAZAO, "") or ""), "catmat": "", "descricao": str(linha.get(COL_DESCRICAO, "") or ""),
            "quantidade": _numero_br(linha.get("QUANTIDADE")), "preco": preco, "sigla": unidade, "unidade": unidade, "capacidade": None,
            "uasg": str(linha.get(COL_UF_DEST, "") or ""), "nome_uasg": str(linha.get(COL_NOME_DEST, "") or linha.get("ÓRGÃO DESTINATÁRIO", "") or ""),
            "uf": str(linha.get(COL_UF_EMIT, "") or ""), "municipio": str(linha.get("MUNICÍPIO EMITENTE", "") or ""),
            "ncm": str(linha.get("NCM/SH (TIPO DE PRODUTO)", "") or ""), "natureza": str(linha.get("NATUREZA DA OPERAÇÃO", "") or ""),
            "uf_dest": str(linha.get(COL_UF_DEST, "") or ""), "valor_total": _numero_br(linha.get("VALOR TOTAL")),
            "numero_nf": numero_nf, "serie": serie,
        })
    return registros


def analisar_item(
    descricao: str,
    registros: list[dict],
    remover: bool = True,
    faixa: tuple[float, float] | None = None,
    max_precos: int = MAX_PRECOS,
    tolerancia: float = TOLERANCIA,
) -> dict:
    """Limpa e seleciona os preços de um item (mesma regra da Cotação Rápida).

    `remover`: tira preços inexequíveis/extremos e outliers (IQR). `faixa`: limita o preço unitário (R$ mín, R$ máx),
    aplicada depois da remoção de outliers. O resultado traz `limites` (mín/máx disponíveis) para montar o controle de faixa."""
    resultado = {
        "descricao": descricao, "tipo": "Nota Fiscal", "status": "sem_notas", "catmats": [], "precos": [], "stats": None,
        "unidade": "", "unidade_curta": "", "brutos": len(registros), "outliers": 0, "faixa_validos": None, "limites": None,
        "universo": 0, "proximos": [], "falha_api": False, "melhor_proximo": None, "registros": registros,
        "notas": len({r["id_compra"] or r["id_item"] for r in registros}),
        "fornecedores": len({r["cnpj"] or r["fornecedor"] for r in registros}),
    }
    if not registros:
        return resultado
    mesma_unidade, resultado["unidade"], resultado["unidade_curta"] = _unidade_dominante(registros)
    limpos, resultado["faixa_validos"] = remover_outliers(mesma_unidade) if remover else (list(mesma_unidade), None)
    resultado["outliers"] = len(mesma_unidade) - len(limpos)
    resultado["universo"] = len(mesma_unidade)
    if limpos:
        precos = [r["preco"] for r in limpos]
        resultado["limites"] = (min(precos), max(precos))
    if faixa and limpos:
        limpos = [r for r in limpos if faixa[0] - 1e-9 <= r["preco"] <= faixa[1] + 1e-9]
    resultado["status"] = "sem_precos"
    resultado["precos"] = selecionar_precos(limpos, max_precos, tolerancia)
    if resultado["precos"]:
        resultado["stats"] = estatisticas([r["preco"] for r in resultado["precos"]])
        resultado["status"] = "ok" if len(resultado["precos"]) >= MIN_PRECOS else "insuficiente"
    return resultado
