"""Radar de Licitações: busca de licitações no PNCP e detalhamento (calendário, documentos, itens, deságio,
fornecedores, atas de registro de preços e partes envolvidas). Sem dependência do Streamlit.

Fontes (públicas, sem chave):
- busca: https://pncp.gov.br/api/search/ (tipos_documento=edital; filtros q, status, ufs);
- detalhe da compra: https://pncp.gov.br/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{sequencial};
- arquivos, itens, resultados, atas e partes envolvidas: https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras/...
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Any

from servicos_publicos import http_get_json

PNCP_SEARCH = "https://pncp.gov.br/api/search/"
PNCP_CONSULTA = "https://pncp.gov.br/api/consulta/v1"
PNCP_API = "https://pncp.gov.br/api/pncp/v1"
PNCP_PORTAL = "https://pncp.gov.br/app"

SITUACOES = {"Recebendo propostas": "recebendo_proposta", "Encerradas": "encerradas", "Todas": "todos"}
UFS = ["AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
       "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"]
CAMINHO_UASGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Projeto Adesões", "uasgs.json")


# ── UASG pelo nome (cadastro local) ───────────────────────────────────────────────────────────────────────────
def _sem_acento(texto: object) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(texto or "").lower()) if unicodedata.category(c) != "Mn")


@lru_cache(maxsize=1)
def _uasgs() -> tuple[tuple[str, str, str], ...]:
    try:
        with open(CAMINHO_UASGS, "r", encoding="utf-8") as arq:
            dados = json.load(arq)
    except UnicodeDecodeError:
        with open(CAMINHO_UASGS, "r", encoding="latin-1") as arq:
            dados = json.load(arq)
    except (OSError, ValueError):
        return ()
    return tuple((str(e.get("codigoUasg", "")).strip(), str(e.get("nomeUasg", "")).strip(), str(e.get("siglaUf", "")).strip())
                 for e in dados if e.get("codigoUasg"))


def buscar_uasg_por_nome(consulta: str, limite: int = 40) -> list[dict]:
    """UASGs cujo nome (ou código) contém todas as palavras digitadas, sem considerar acentos."""
    termos = _sem_acento(consulta).split()
    if not termos:
        return []
    achadas = []
    for codigo, nome, uf in _uasgs():
        alvo = _sem_acento(f"{codigo} {nome} {uf}")
        if all(t in alvo for t in termos):
            achadas.append({"codigo": codigo, "nome": nome, "uf": uf})
            if len(achadas) >= limite:
                break
    return achadas


def nome_uasg(codigo: str) -> str:
    return next((nome for cod, nome, _uf in _uasgs() if cod == str(codigo).strip()), "")


# ── Busca ─────────────────────────────────────────────────────────────────────────────────────────────────────
def _data(texto: object) -> _dt.date | None:
    try:
        return _dt.date.fromisoformat(str(texto or "")[:10])
    except ValueError:
        return None


def _mesma_uasg(a: object, b: object) -> bool:
    return str(a or "").strip().lstrip("0") == str(b or "").strip().lstrip("0")


def _resumo_busca(item: dict) -> dict:
    partes = str(item.get("item_url") or "").strip("/").split("/")  # compras/{cnpj}/{ano}/{sequencial}
    cnpj, ano, seq = (partes[1], partes[2], partes[3]) if len(partes) >= 4 else ("", "", "")
    return {
        "cnpj": cnpj, "ano": ano, "sequencial": seq,
        "titulo": item.get("title") or "",
        "objeto": item.get("description") or "",
        "orgao": item.get("orgao_nome") or "",
        "uasg": str(item.get("unidade_codigo") or ""),
        "unidade": (item.get("unidade_nome") or "").strip(),
        "municipio": item.get("municipio_nome") or "",
        "uf": item.get("uf") or "",
        "modalidade": item.get("modalidade_licitacao_nome") or "",
        "publicacao": str(item.get("data_publicacao_pncp") or "")[:10],
        "abertura": str(item.get("data_inicio_vigencia") or "")[:16].replace("T", " "),
        "encerramento": str(item.get("data_fim_vigencia") or "")[:16].replace("T", " "),
        "tem_resultado": bool(item.get("tem_resultado")),
        "cancelada": bool(item.get("cancelado")),
        "controle_pncp": item.get("numero_controle_pncp") or "",
        "link_pncp": f"{PNCP_PORTAL}/editais/{cnpj}/{ano}/{seq}" if seq else "",
    }


def buscar_licitacoes(objeto: str = "", codigo_uasg: str = "", situacao: str = "todos", uf: str = "",
                      data_ini: _dt.date | None = None, data_fim: _dt.date | None = None,
                      max_paginas: int = 5) -> tuple[list[dict], str | None, int]:
    """Licitações (editais e avisos) publicadas no PNCP, das mais recentes para as mais antigas.

    `objeto` e/ou `codigo_uasg` são obrigatórios (ao menos um). A UASG entra no texto da busca e depois é conferida
    no resultado; o período (data de publicação no PNCP) é filtrado aqui. Retorna (licitações, erro, total no PNCP)."""
    termo = " ".join(t for t in (str(codigo_uasg or "").strip(), str(objeto or "").strip()) if t)
    if not termo:
        return [], "Informe o objeto ou a UASG.", 0
    achadas: list[dict] = []
    total = 0
    for pagina in range(1, max_paginas + 1):
        params = {"q": termo, "tipos_documento": "edital", "status": situacao or "todos", "pagina": pagina,
                  "tam_pagina": 100, "ordenacao": "-data"}
        if uf:
            params["ufs"] = uf
        dados, erro = http_get_json(PNCP_SEARCH, params, timeout=40, tentativas=4)
        if erro:
            return achadas, f"PNCP: {erro}" + (f" (mostrando {len(achadas)} já obtidas)" if achadas else ""), total
        itens = [i for i in (dados or {}).get("items", []) if isinstance(i, dict)]
        total = (dados or {}).get("total", 0) or 0
        if not itens:
            break
        mais_antiga = None
        for item in itens:
            if codigo_uasg and not _mesma_uasg(item.get("unidade_codigo"), codigo_uasg):
                continue
            publicada = _data(item.get("data_publicacao_pncp"))
            mais_antiga = publicada if publicada and (mais_antiga is None or publicada < mais_antiga) else mais_antiga
            if data_ini and publicada and publicada < data_ini:
                continue
            if data_fim and publicada and publicada > data_fim:
                continue
            achadas.append(_resumo_busca(item))
        if data_ini and mais_antiga and mais_antiga < data_ini:
            break  # resultados vêm do mais recente para o mais antigo: o resto está fora do período
        if pagina * 100 >= total:
            break
    return achadas, None, total


# ── Detalhe ───────────────────────────────────────────────────────────────────────────────────────────────────
def _lista(dados: Any) -> list:
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict):
        return dados.get("data") or dados.get("resultado") or []
    return []


def _itens_da_compra(cnpj: str, ano: str, seq: str, limite: int = 500) -> tuple[list[dict], str | None]:
    itens: list[dict] = []
    for pagina in range(1, limite // 50 + 2):
        dados, erro = http_get_json(f"{PNCP_API}/orgaos/{cnpj}/compras/{ano}/{seq}/itens", {"pagina": pagina, "tamanhoPagina": 50},
                                    timeout=40, tentativas=3, ok_404=True)
        if erro:
            return itens, erro
        lote = _lista(dados)
        itens.extend(lote)
        if len(lote) < 50 or len(itens) >= limite:
            break
    return itens[:limite], None


def detalhar_licitacao(cnpj: str, ano: str, seq: str, max_itens_resultado: int = 300) -> dict:
    """Tudo o que o PNCP publica sobre a licitação. Cada parte é independente: `erros` lista o que falhou."""
    base_api = f"{PNCP_API}/orgaos/{cnpj}/compras/{ano}/{seq}"
    erros: list[str] = []

    with ThreadPoolExecutor(max_workers=4) as pool:
        f_compra = pool.submit(http_get_json, f"{PNCP_CONSULTA}/orgaos/{cnpj}/compras/{ano}/{seq}", None, 40, 3, True)
        f_arquivos = pool.submit(http_get_json, f"{base_api}/arquivos", None, 40, 3, True)
        f_atas = pool.submit(http_get_json, f"{base_api}/atas", None, 40, 3, True)
        f_itens = pool.submit(_itens_da_compra, cnpj, ano, seq)
        compra, erro = f_compra.result()
        if erro:
            erros.append(f"dados da compra: {erro}")
        arquivos, erro = f_arquivos.result()
        if erro:
            erros.append(f"documentos: {erro}")
        atas, erro = f_atas.result()
        if erro:
            erros.append(f"atas: {erro}")
        itens, erro = f_itens.result()
        if erro:
            erros.append(f"itens: {erro}")

    itens = itens or []
    com_resultado = [i for i in itens if i.get("temResultado")][:max_itens_resultado]

    def _resultados(item: dict) -> tuple[Any, list]:
        dados, _erro = http_get_json(f"{base_api}/itens/{item.get('numeroItem')}/resultados", timeout=40, tentativas=3, ok_404=True)
        return item.get("numeroItem"), _lista(dados)

    atas = _lista(atas)

    def _ata(ata: dict) -> dict:
        s = ata.get("sequencialAta")
        docs, _e1 = http_get_json(f"{base_api}/atas/{s}/arquivos", timeout=40, tentativas=3, ok_404=True)
        partes, _e2 = http_get_json(f"{base_api}/atas/{s}/partesenvolvidas", timeout=40, tentativas=3, ok_404=True)
        return {**ata, "_arquivos": _lista(docs), "_partes": _lista(partes)}

    with ThreadPoolExecutor(max_workers=8) as pool:
        resultados = dict(pool.map(_resultados, com_resultado))
        atas = list(pool.map(_ata, atas))
    if len([i for i in itens if i.get("temResultado")]) > max_itens_resultado:
        erros.append(f"resultados: consultados só os {max_itens_resultado} primeiros itens")

    return {"compra": compra or {}, "arquivos": _lista(arquivos), "itens": itens, "resultados": resultados,
            "atas": atas, "erros": erros}


# ── Análises ──────────────────────────────────────────────────────────────────────────────────────────────────
def _valido(resultado: dict) -> bool:
    return "cancel" not in str(resultado.get("situacaoCompraItemResultadoNome") or "").lower()


def tabela_itens(detalhe: dict) -> list[dict]:
    """Uma linha por item: estimado, vencedor(es) válidos, homologado, deságio e resultados cancelados."""
    linhas = []
    for it in detalhe.get("itens", []):
        res = detalhe.get("resultados", {}).get(it.get("numeroItem"), [])
        validos = [r for r in res if _valido(r)]
        cancelados = [r for r in res if not _valido(r)]
        est_unit = it.get("valorUnitarioEstimado") or 0
        est_total = it.get("valorTotal") or 0
        hom_total = sum((r.get("valorTotalHomologado") or 0) for r in validos)
        hom_unit = validos[0].get("valorUnitarioHomologado") if len(validos) == 1 else None
        linhas.append({
            "Item": it.get("numeroItem"),
            "Descrição": it.get("descricao") or "",
            "Qtd": it.get("quantidade"),
            "Unidade": it.get("unidadeMedida") or "",
            "Valor unit. estimado": est_unit,
            "Valor total estimado": est_total,
            "Vencedor": "; ".join(f"{r.get('nomeRazaoSocialFornecedor', '')} ({r.get('niFornecedor', '')})" for r in validos),
            "Valor unit. homologado": hom_unit,
            "Valor total homologado": hom_total or None,
            "Deságio (%)": round((est_total - hom_total) / est_total * 100, 2) if est_total and hom_total else None,
            "Resultados cancelados": "; ".join(f"{r.get('nomeRazaoSocialFornecedor', '')} a {r.get('valorUnitarioHomologado')}" for r in cancelados),
            "Situação do item": it.get("situacaoCompraItemNome") or "",
        })
    return linhas


def resumo_desagio(detalhe: dict) -> dict:
    """Deságio da licitação: pelo total da compra quando houver; senão, pela soma dos itens com resultado."""
    compra = detalhe.get("compra", {})
    est, hom = compra.get("valorTotalEstimado") or 0, compra.get("valorTotalHomologado") or 0
    base = "compra"
    if not (est and hom):
        linhas = [l for l in tabela_itens(detalhe) if l["Valor total estimado"] and l["Valor total homologado"]]
        est = sum(l["Valor total estimado"] for l in linhas)
        hom = sum(l["Valor total homologado"] for l in linhas)
        base = "itens"
    return {"estimado": est, "homologado": hom, "desagio": ((est - hom) / est * 100) if est and hom else None, "base": base}


def fornecedores(detalhe: dict) -> list[dict]:
    """Fornecedores que aparecem nos resultados: itens vencidos, valor homologado e itens com resultado cancelado."""
    por_cnpj: dict[str, dict] = {}
    for numero, res in detalhe.get("resultados", {}).items():
        for r in res:
            chave = str(r.get("niFornecedor") or "")
            f = por_cnpj.setdefault(chave, {"Fornecedor": r.get("nomeRazaoSocialFornecedor") or "", "CNPJ/CPF": chave,
                                            "Porte": r.get("porteFornecedorNome") or "", "Itens vencidos": 0,
                                            "Valor homologado": 0.0, "Itens cancelados": 0})
            if _valido(r):
                f["Itens vencidos"] += 1
                f["Valor homologado"] += r.get("valorTotalHomologado") or 0
            else:
                f["Itens cancelados"] += 1
    return sorted(por_cnpj.values(), key=lambda f: -f["Valor homologado"])


def documentos_de_homologacao(detalhe: dict) -> list[dict]:
    """Arquivos da compra e das atas que registram o resultado (homologação, adjudicação, sessão pública, ata de RP)."""
    chave = re.compile(r"homolog|adjudic|sess[aã]o|resultado|registro de pre", re.I)
    docs = [d for d in detalhe.get("arquivos", []) if chave.search(f"{d.get('tipoDocumentoNome', '')} {d.get('titulo', '')}")]
    for ata in detalhe.get("atas", []):
        docs.extend(ata.get("_arquivos", []))
    return docs


# ── Calendário (.ics) ─────────────────────────────────────────────────────────────────────────────────────────
def _ics_data(texto: str) -> str | None:
    texto = str(texto or "").strip()
    for formato in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return _dt.datetime.strptime(texto[:16] if " " in texto else texto[:10], formato).strftime("%Y%m%dT%H%M00")
        except ValueError:
            continue
    return None


def _ics_texto(texto: str) -> str:
    return str(texto or "").replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", " ")[:300]


def gerar_calendario_ics(licitacoes: list[dict]) -> bytes:
    """Arquivo .ics (Outlook/Google Agenda) com o encerramento do recebimento de propostas de cada licitação,
    e lembrete 1 dia antes. Licitações sem data de encerramento ficam de fora."""
    agora = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    linhas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AtaCotada//Radar de Licitacoes//PT-BR", "CALSCALE:GREGORIAN"]
    for lic in licitacoes:
        inicio = _ics_data(lic.get("encerramento"))
        if not inicio:
            continue
        titulo = f"Encerramento: {lic.get('titulo', '')} — {lic.get('unidade') or lic.get('orgao', '')}"
        descricao = f"{lic.get('objeto', '')} | Abertura das propostas: {lic.get('abertura', '')} | PNCP: {lic.get('link_pncp', '')}"
        linhas += ["BEGIN:VEVENT", f"UID:{lic.get('controle_pncp') or lic.get('link_pncp')}@atacotada", f"DTSTAMP:{agora}",
                   f"DTSTART:{inicio}", f"SUMMARY:{_ics_texto(titulo)}", f"DESCRIPTION:{_ics_texto(descricao)}",
                   f"URL:{lic.get('link_pncp', '')}",
                   "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", "DESCRIPTION:Licitação encerra amanhã", "END:VALARM",
                   "END:VEVENT"]
    linhas.append("END:VCALENDAR")
    return ("\r\n".join(linhas) + "\r\n").encode("utf-8")
