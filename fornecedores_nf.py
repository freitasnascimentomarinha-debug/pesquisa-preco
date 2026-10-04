"""Fornecedores encontrados na pesquisa de notas fiscais: dados cadastrais (OpenCNPJ), CNAE principal e resumo do que vendem."""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Callable

import pandas as pd
import requests

API_CNPJ = "https://api.opencnpj.org/{cnpj}"
CAMINHO_CNAES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cnaes_completo.json")
MAX_FORNECEDORES_TODOS = 300
NAO_INFORMADO = "Não informado"
_CACHE: dict[str, dict | None] = {}


@lru_cache(maxsize=1)
def _cnaes() -> dict[int, str]:
    """Código CNAE (7 dígitos) -> descrição, a partir do cnaes_completo.json do projeto."""
    try:
        with open(CAMINHO_CNAES, "r", encoding="utf-8") as arquivo:
            bruto = json.load(arquivo)
    except (OSError, ValueError):
        return {}
    return {int(codigo): re.sub(r"\s*\(\d{4}-\d/\d{2}\)\s*$", "", descricao).strip() for descricao, codigo in bruto.items()}


def formatar_cnpj(cnpj: str) -> str:
    digitos = re.sub(r"\D", "", str(cnpj or ""))
    if len(digitos) != 14:
        return str(cnpj or "")
    return f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}"


def formatar_cnae(valor: object) -> str:
    """'4751201' ou {'codigo':..., 'descricao':...} -> '4751-2/01 - Comércio varejista...'."""
    descricao = ""
    if isinstance(valor, dict):
        descricao = str(valor.get("descricao") or valor.get("description") or valor.get("text") or "")
        valor = valor.get("codigo") or valor.get("code") or valor.get("id") or ""
    digitos = re.sub(r"\D", "", str(valor or ""))
    if len(digitos) != 7:
        return " - ".join(parte for parte in (str(valor or ""), descricao) if parte) or NAO_INFORMADO
    codigo = f"{digitos[:4]}-{digitos[4]}/{digitos[5:]}"
    descricao = descricao or _cnaes().get(int(digitos), "")
    return f"{codigo} - {descricao}" if descricao else codigo


def _telefone(valor: object) -> str:
    if isinstance(valor, dict):
        ddd = re.sub(r"\D", "", str(valor.get("ddd") or ""))
        numero = re.sub(r"\D", "", str(valor.get("numero") or valor.get("number") or ""))
        if not numero:
            return ""
        texto = f"{numero[:-4]}-{numero[-4:]}" if len(numero) >= 8 else numero
        return f"({ddd}) {texto}" if ddd else texto
    return str(valor or "").strip()


def interpretar_dados(dados: dict | None) -> dict[str, str]:
    """Campos cadastrais úteis do retorno da API (aceita variações de nomes de campo)."""
    vazio = {"razao_social": "", "nome_fantasia": "", "situacao": "", "email": NAO_INFORMADO, "telefones": NAO_INFORMADO,
             "uf": "", "municipio": "", "cnae": NAO_INFORMADO}
    if not dados:
        return vazio
    pegar = lambda *chaves: next((str(dados[c]).strip() for c in chaves if dados.get(c)), "")  # noqa: E731
    telefones: list[str] = []
    for chave in ("telefones", "phones", "phone_numbers"):
        for valor in dados.get(chave) or []:
            texto = _telefone(valor)
            if texto and texto not in telefones:
                telefones.append(texto)
    for chave in ("telefone", "phone", "ddd_telefone", "telefone_principal"):
        texto = _telefone(dados.get(chave))
        if texto and texto not in telefones:
            telefones.append(texto)
    return {
        "razao_social": pegar("razao_social", "razaoSocial", "nome_empresarial", "company_name", "legal_name"),
        "nome_fantasia": pegar("nome_fantasia", "nomeFantasia", "trade_name"),
        "situacao": pegar("situacao_cadastral", "situacao", "status"),
        "email": pegar("email", "correio_eletronico", "e_mail", "mail").lower() or NAO_INFORMADO,
        "telefones": ", ".join(telefones) or NAO_INFORMADO,
        "uf": pegar("uf", "estado", "state").upper(),
        "municipio": pegar("municipio", "cidade", "city"),
        "cnae": formatar_cnae(dados.get("cnae_principal") or dados.get("cnaePrincipal") or dados.get("cnae_fiscal") or dados.get("main_activity")),
    }


def consultar_cnpj(cnpj: str, tentativas: int = 3) -> dict | None:
    """Consulta a API OpenCNPJ (com espera quando ela limita as requisições). None se não achar/falhar."""
    digitos = re.sub(r"\D", "", str(cnpj or ""))
    if len(digitos) != 14:
        return None
    if digitos in _CACHE:
        return _CACHE[digitos]
    resultado = None
    for tentativa in range(tentativas):
        try:
            resposta = requests.get(API_CNPJ.format(cnpj=digitos), timeout=12)
            if resposta.status_code == 200:
                resultado = resposta.json()
                break
            if resposta.status_code == 404:
                break
        except (requests.RequestException, ValueError):
            pass
        time.sleep(1.5 * (tentativa + 1))
    _CACHE[digitos] = resultado
    return resultado


def _moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def agregar_fornecedores(resultados: list[dict], escopo: str = "mapa") -> list[dict]:
    """Um registro por fornecedor (CNPJ) com o que ele vendeu nas notas encontradas.

    escopo="mapa": só os fornecedores dos preços listados no mapa; "todos": todos os que venderam os itens (até
    MAX_FORNECEDORES_TODOS, os de mais notas primeiro)."""
    por_cnpj: dict[str, dict] = {}
    for resultado in resultados:
        origem = resultado["precos"] if escopo == "mapa" else resultado.get("registros", [])
        for registro in origem:
            chave = registro["cnpj"] or registro["fornecedor"]
            if not chave:
                continue
            forn = por_cnpj.setdefault(chave, {"cnpj": registro["cnpj"], "razao_nf": registro["fornecedor"], "uf_nf": registro["uf"],
                                               "municipio_nf": registro["municipio"], "itens": defaultdict(list), "ncm": Counter(),
                                               "natureza": Counter(), "notas": set()})
            forn["itens"][resultado["descricao"]].append(registro["preco"])
            forn["notas"].add(registro["id_compra"] or registro["id_item"])
            if registro["ncm"]:
                forn["ncm"][registro["ncm"]] += 1
            if registro["natureza"]:
                forn["natureza"][registro["natureza"]] += 1
    fornecedores = sorted(por_cnpj.values(), key=lambda f: (-len(f["notas"]), f["razao_nf"]))
    return fornecedores[:MAX_FORNECEDORES_TODOS] if escopo != "mapa" else fornecedores


def resumo_da_natureza(fornecedor: dict) -> str:
    """Resumo do que o fornecedor vende, a partir das notas: itens pesquisados, tipo de produto (NCM) e operação."""
    itens = "; ".join(
        f"{descricao[:45]} ({len(precos)} {'item' if len(precos) == 1 else 'itens'} de NF, {_moeda(sum(precos) / len(precos))} em média)"
        for descricao, precos in sorted(fornecedor["itens"].items(), key=lambda par: -len(par[1]))
    )
    partes = [f"Vende: {itens}"]
    if fornecedor["ncm"]:
        partes.append("Tipo de produto (NCM): " + ", ".join(texto[:60] for texto, _ in fornecedor["ncm"].most_common(2)))
    if fornecedor["natureza"]:
        partes.append("Operação: " + ", ".join(texto[:30] for texto, _ in fornecedor["natureza"].most_common(2)))
    return ". ".join(partes)


COLUNAS_FORNECEDORES = ["CNPJ", "Razão social", "Nome fantasia", "Situação cadastral", "UF", "Município", "Telefones", "E-mail",
                        "CNAE principal", "Natureza dos itens que vende", "Notas encontradas"]


def montar_tabela(resultados: list[dict], escopo: str = "mapa", progresso: Callable[[int, int], None] | None = None) -> tuple[pd.DataFrame, int]:
    """Tabela de fornecedores com os dados cadastrais. Retorna (tabela, quantos CNPJs não puderam ser consultados)."""
    fornecedores = agregar_fornecedores(resultados, escopo)
    cadastros: dict[int, dict] = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futuros = {i: executor.submit(consultar_cnpj, f["cnpj"]) for i, f in enumerate(fornecedores)}
        for feitos, (i, futuro) in enumerate(futuros.items(), start=1):
            cadastros[i] = interpretar_dados(futuro.result())
            if progresso:
                progresso(feitos, len(fornecedores))
    linhas, sem_consulta = [], 0
    for i, forn in enumerate(fornecedores):
        cad = cadastros[i]
        sem_consulta += not cad["razao_social"]
        linhas.append({
            "CNPJ": formatar_cnpj(forn["cnpj"]) or NAO_INFORMADO,
            "Razão social": cad["razao_social"] or forn["razao_nf"] or NAO_INFORMADO,
            "Nome fantasia": cad["nome_fantasia"] or "",
            "Situação cadastral": cad["situacao"] or NAO_INFORMADO,
            "UF": cad["uf"] or forn["uf_nf"] or NAO_INFORMADO,
            "Município": cad["municipio"] or forn["municipio_nf"] or "",
            "Telefones": cad["telefones"],
            "E-mail": cad["email"],
            "CNAE principal": cad["cnae"],
            "Natureza dos itens que vende": resumo_da_natureza(forn),
            "Notas encontradas": len(forn["notas"]),
        })
    return pd.DataFrame(linhas, columns=COLUNAS_FORNECEDORES), sem_consulta
