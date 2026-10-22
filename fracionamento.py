"""Detector de fracionamento de despesa (Lei nº 14.133/2021, art. 75, §1º).

Soma, por ramo de atividade, o que a unidade gestora (UASG) já contratou no exercício por dispensa em razão do valor
(art. 75, I e II), a partir dos dados abertos do Compras.gov.br (contratações publicadas no PNCP).

Ramo de atividade: para materiais, a família do item no catálogo (PDM do CATMAT); para serviços, a descrição do
serviço (IN SEGES/ME nº 67/2021). A API pública não traz o PDM dos itens das dispensas, então o PDM é deduzido da
descrição do item (que no CATMAT começa pelo nome da família) e conferido no catálogo local. Quando não há
correspondência, o agrupamento é feito pelas primeiras palavras da descrição e marcado como aproximado.
"""

from __future__ import annotations

import gzip
import csv
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache
from typing import Callable

import modelos_processo as MP
import natureza_despesa as ND

DADOSABERTOS = "https://dadosabertos.compras.gov.br"
CATALOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Projeto Adesões", "catalogo_catmat.csv.gz")
CATALOGO_SERVICOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Projeto Adesões", "catalogo_servicos.json")
MODALIDADE_DISPENSA = 6               # código da modalidade "Dispensa" no módulo de contratações
SITUACOES_SEM_DESPESA = ("cancelad", "desert", "fracassad", "anulad", "revogad")
PALAVRAS_VAZIAS = {"de", "da", "do", "das", "dos", "e", "para", "com", "em", "a", "o", "tipo", "servico", "servicos"}


def _norm(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "")).encode("ascii", "ignore").decode().upper()
    return re.sub(r"[^A-Z0-9]+", " ", texto).strip()


@lru_cache(maxsize=1)
def familias_catmat() -> dict[str, tuple[str, str, str]]:
    """Nome normalizado do PDM -> (código do PDM, nome do PDM, classe)."""
    familias: dict[str, tuple[str, str, str]] = {}
    if not os.path.exists(CATALOGO):
        return familias
    with gzip.open(CATALOGO, "rt", encoding="utf-8", newline="") as arq:
        for linha in csv.DictReader(arq):
            nome = linha["nome_pdm"].strip('" ')
            familias.setdefault(_norm(nome), (linha["codigo_pdm"], nome, linha.get("nome_classe", "")))
    return familias


@lru_cache(maxsize=1)
def servicos_catser() -> dict[str, tuple[str, str]]:
    """Nome normalizado do serviço no catálogo (CATSER) -> (código, nome)."""
    import json
    if not os.path.exists(CATALOGO_SERVICOS):
        return {}
    with open(CATALOGO_SERVICOS, encoding="utf-8") as arq:
        catalogo = json.load(arq)
    servicos: dict[str, tuple[str, str]] = {}
    for nome, codigo in catalogo.items():
        servicos.setdefault(_norm(nome), (str(codigo), nome))
    return servicos


def _sem_repeticao(palavras: list[str]) -> list[str]:
    """A API repete o nome do serviço na descrição ('SEGURO AUTOMOTIVO SEGURO AUTOMOTIVO'): fica só uma vez."""
    for n in range(len(palavras) // 2, 0, -1):
        if palavras[:n] == palavras[n:2 * n]:
            return palavras[:n] + palavras[2 * n:]
    return palavras


def _servico(descricao: str, servicos: dict) -> dict | None:
    palavras = _sem_repeticao(_norm(descricao).split())
    for n in range(min(20, len(palavras)), 0, -1):            # 1º: o nome do catálogo no começo da descrição
        achado = servicos.get(" ".join(palavras[:n]))
        if achado and n >= 2:
            return {"chave": f"CATSER {achado[0]}", "ramo": achado[1], "classe": "", "base": "CATSER"}
    alvo = set(palavras[:12]) - {p.upper() for p in PALAVRAS_VAZIAS}
    melhor, nota = None, 0.0                                   # 2º: o serviço do catálogo mais parecido
    for nome, achado in servicos.items():
        tokens = set(nome.split()) - {p.upper() for p in PALAVRAS_VAZIAS}
        if alvo and tokens:
            s = len(alvo & tokens) / len(alvo | tokens)
            if s > nota:
                melhor, nota = achado, s
    if melhor and nota >= 0.6:
        return {"chave": f"CATSER {melhor[0]}", "ramo": melhor[1], "classe": "", "base": f"CATSER (semelhança {nota:.0%})"}
    return None


def ramo_do_item(descricao: str, material: bool, familias: dict | None = None, servicos: dict | None = None) -> dict:
    """{'chave', 'ramo', 'classe', 'base', 'tipo'} do item.
    base: 'PDM (CATMAT)', 'CATSER', 'CATSER (semelhança N%)' ou 'descrição (aproximado)'."""
    familias = familias_catmat() if familias is None else familias
    if material:
        cabeca = re.split(r"\s+\S+:", " " + str(descricao or ""), maxsplit=1)[0]   # corta no 1º atributo "NOME:"
        palavras = _norm(cabeca).split()
        for n in range(min(6, len(palavras)), 0, -1):
            achado = familias.get(" ".join(palavras[:n]))
            if achado:
                return {"chave": f"PDM {achado[0]}", "ramo": achado[1], "classe": achado[2], "base": "PDM (CATMAT)",
                        "tipo": "Material"}
    else:
        achado = _servico(descricao, servicos_catser() if servicos is None else servicos)
        if achado:
            return {**achado, "tipo": "Serviço"}
    uteis = [p for p in _sem_repeticao(_norm(descricao).split()) if p.lower() not in PALAVRAS_VAZIAS][:6]
    rotulo = " ".join(uteis) or "SEM DESCRIÇÃO"
    return {"chave": f"DESC {rotulo}", "ramo": rotulo, "classe": "", "base": "descrição (aproximado)",
            "tipo": "Material" if material else "Serviço"}


def inciso(amparo: str) -> str | None:
    """'Lei 14.133/2021, Art. 75, II' -> 'II'; outros incisos não entram no somatório do §1º."""
    m = re.search(r"art\.?\s*75,\s*(I{1,2})\b(?!I)", str(amparo or ""), re.I)
    return m.group(1).upper() if m else None


def _json(url, params, timeout=90):
    from servicos_publicos import http_get_json
    return http_get_json(url, params, timeout=timeout, tentativas=2)


def buscar_dispensas(uasg: str, ano: int, progresso: Callable[[float, str], None] | None = None) -> tuple[list[dict], str | None]:
    """Dispensas por valor (art. 75, I e II) da UASG no ano, com os itens. Devolve (compras, erro)."""
    compras, pagina = [], 1
    fim = min(date(ano, 12, 31), date.today())
    while True:
        dados, erro = _json(f"{DADOSABERTOS}/modulo-contratacoes/1_consultarContratacoes_PNCP_14133",
                            {"pagina": pagina, "tamanhoPagina": 500, "unidadeOrgaoCodigoUnidade": str(uasg).strip(),
                             "codigoModalidade": MODALIDADE_DISPENSA, "dataPublicacaoPncpInicial": f"{ano}-01-01",
                             "dataPublicacaoPncpFinal": fim.isoformat()})
        if erro:
            return [], f"Compras.gov.br (contratações): {erro}"
        compras += (dados or {}).get("resultado") or []
        if pagina >= int((dados or {}).get("totalPaginas") or 1):
            break
        pagina += 1
    por_valor = [c for c in compras if inciso(c.get("amparoLegalNome")) and not c.get("contratacaoExcluida")]

    def itens(compra):
        dados, erro = _json(f"{DADOSABERTOS}/modulo-contratacoes/2.1_consultarItensContratacoes_PNCP_14133_Id",
                            {"tipo": "idCompra", "codigo": compra["idCompra"]}, timeout=60)
        return (dados or {}).get("resultado") or [], erro

    feitos = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for compra, (lista, erro) in zip(por_valor, ex.map(itens, por_valor)):
            compra["_itens"], compra["_erro_itens"] = lista, erro
            feitos += 1
            if progresso:
                progresso(feitos / max(len(por_valor), 1), f"Lendo itens das dispensas ({feitos}/{len(por_valor)})")
    return por_valor, None


def _valor_item(item: dict) -> tuple[float, bool]:
    """(valor, é_estimado): valor homologado quando há resultado; senão o estimado."""
    if item.get("temResultado") and item.get("valorTotalResultado") is not None:
        return float(item["valorTotalResultado"] or 0), False
    return float(item.get("valorTotal") or 0), True


def consolidar(compras: list[dict], familias: dict | None = None, servicos: dict | None = None) -> list[dict]:
    """Grupos por (inciso, ramo): tipo, subelemento sugerido, total, compras, itens, se há valor estimado e situação."""
    grupos: dict[tuple, dict] = {}
    for compra in compras:
        inc = inciso(compra.get("amparoLegalNome"))
        lista = compra.get("_itens") or []
        if not lista:  # sem itens legíveis: entra pelo valor da compra, agrupado pelo objeto
            lista = [{"descricaoResumida": compra.get("objetoCompra"), "materialOuServico": "",
                      "temResultado": compra.get("valorTotalHomologado") is not None,
                      "valorTotalResultado": compra.get("valorTotalHomologado"), "valorTotal": compra.get("valorTotalEstimado")}]
        for item in lista:
            if any(s in str(item.get("situacaoCompraItemNome") or "").lower() for s in SITUACOES_SEM_DESPESA):
                continue
            r = ramo_do_item(item.get("descricaoResumida") or item.get("descricaodetalhada"),
                             item.get("materialOuServico") != "S", familias, servicos)
            valor, estimado = _valor_item(item)
            g = grupos.setdefault((inc, r["chave"]), {"inciso": inc, **r, "total": 0.0, "compras": set(), "itens": 0,
                                                     "estimado": False, "exemplos": []})
            g["total"] += valor
            g["compras"].add(compra.get("numeroControlePNCP") or compra.get("idCompra"))
            g["itens"] += 1
            g["estimado"] |= estimado
            if len(g["exemplos"]) < 3:
                g["exemplos"].append(str(item.get("descricaoResumida") or "")[:80])
    saida = []
    for g in grupos.values():
        limite = MP.LIMITES_DISPENSA["inciso_I" if g["inciso"] == "I" else "inciso_II"]
        g["limite"] = limite
        g["saldo"] = limite - g["total"]
        g["uso"] = g["total"] / limite
        g["situacao"] = "🔴 ultrapassado" if g["uso"] >= 1 else "🟡 acima de 80%" if g["uso"] >= 0.8 else "🟢 dentro do limite"
        g["compras"] = sorted(g["compras"])
        g["subelemento"] = ND.sugerir(g["tipo"] == "Material", g["ramo"], g["classe"])
        saida.append(g)
    return sorted(saida, key=lambda g: -g["uso"])


def por_subelemento(grupos: list[dict], ajustes: dict[str, str] | None = None) -> list[dict]:
    """Soma por (inciso, subelemento). ajustes: chave do grupo -> código escolhido pelo operador."""
    ajustes = ajustes or {}
    somas: dict[tuple, dict] = {}
    for g in grupos:
        codigo = ajustes.get(f"{g['inciso']}|{g['chave']}", g.get("subelemento") or "")
        s = somas.setdefault((g["inciso"], codigo), {"inciso": g["inciso"], "subelemento": codigo,
                                                     "rotulo": ND.rotulo(codigo), "total": 0.0, "ramos": 0,
                                                     "compras": set()})
        s["total"] += g["total"]
        s["ramos"] += 1
        s["compras"].update(g["compras"])
    saida = []
    for s in somas.values():
        limite = MP.LIMITES_DISPENSA["inciso_I" if s["inciso"] == "I" else "inciso_II"]
        s.update(limite=limite, saldo=limite - s["total"], uso=s["total"] / limite, compras=len(s["compras"]))
        s["situacao"] = "🔴 ultrapassado" if s["uso"] >= 1 else "🟡 acima de 80%" if s["uso"] >= 0.8 else "🟢 dentro do limite"
        saida.append(s)
    return sorted(saida, key=lambda s: -s["uso"])


def simular(grupos: list[dict], descricao: str, valor: float, material: bool, inc: str = "II",
            familias: dict | None = None) -> dict:
    """Quanto já foi gasto no ramo da nova contratação e se ela cabe no limite."""
    r = ramo_do_item(descricao, material, familias)
    ja = sum(g["total"] for g in grupos if g["chave"] == r["chave"] and g["inciso"] == inc)
    limite = MP.LIMITES_DISPENSA["inciso_I" if inc == "I" else "inciso_II"]
    total = ja + valor
    return {**r, "ja_contratado": ja, "novo": valor, "total": total, "limite": limite, "cabe": total < limite,
            "saldo": limite - ja}


def corpo_relatorio(uasg: str, nome_uasg: str, ano: int, grupos: list[dict], compras: list[dict],
                    ajustes: dict[str, str] | None = None) -> str:
    brl = MP.brl
    cel = lambda t: str(t or "").replace("|", "/").replace("\n", " ").strip()
    ajustes = ajustes or {}
    sub = lambda g: ND.rotulo(ajustes.get(f"{g['inciso']}|{g['chave']}", g.get("subelemento") or ""))
    linhas = ["### 1. OBJETIVO",
              f"Verificar, para a UASG {uasg}{' – ' + nome_uasg if nome_uasg else ''}, o somatório das contratações "
              f"diretas em razão do valor realizadas no exercício de {ano}, por ramo de atividade e por natureza de "
              "despesa, nos termos do art. 75, §1º, da Lei nº 14.133/2021.",
              "", "### 2. METODOLOGIA",
              f"Foram consideradas as {len(compras)} dispensas fundamentadas no art. 75, I ou II, publicadas no PNCP e "
              "disponíveis nos dados abertos do Compras.gov.br. O ramo de atividade foi definido pela família do item no "
              "CATMAT (PDM), para materiais, e pelo serviço do CATSER, para serviços, ambos identificados pela descrição "
              "do item; sem correspondência no catálogo, o agrupamento é aproximado. A natureza de despesa e o "
              "subelemento (Portaria STN nº 448/2002) foram sugeridos pela família ou pelo serviço e conferidos pelo "
              "operador. Usou-se o valor homologado do item e, na falta dele, o valor estimado. " + MP.nota_limites()]
    n = 3
    for tipo in ("Material", "Serviço"):
        do_tipo = [g for g in grupos if g.get("tipo", "Material") == tipo]
        if not do_tipo:
            continue
        linhas += ["", f"### {n}. {'MATERIAIS' if tipo == 'Material' else 'SERVIÇOS'} — SOMATÓRIO POR RAMO DE ATIVIDADE",
                   "| Inciso | Ramo de atividade | Subelemento | Dispensas | Total no exercício | Saldo | Situação |",
                   "|---|---|---|---|---|---|---|"]
        for g in do_tipo:
            linhas.append(f"| {g['inciso']} | {cel(g['ramo'])} | {cel(sub(g))} | {len(g['compras'])} | "
                          f"{brl(g['total'])}{' (*)' if g['estimado'] else ''} | {brl(max(g['saldo'], 0))} | "
                          f"{g['situacao'][2:]} |")
        n += 1
    linhas += ["", f"### {n}. SOMATÓRIO POR NATUREZA DE DESPESA E SUBELEMENTO",
               "| Inciso | Natureza / subelemento | Ramos | Dispensas | Total no exercício | Saldo | Situação |",
               "|---|---|---|---|---|---|---|"]
    for s_ in por_subelemento(grupos, ajustes):
        linhas.append(f"| {s_['inciso']} | {cel(s_['rotulo'])} | {s_['ramos']} | {s_['compras']} | {brl(s_['total'])} | "
                      f"{brl(max(s_['saldo'], 0))} | {s_['situacao'][2:]} |")
    if any(g["estimado"] for g in grupos):
        linhas.append("(*) inclui valor estimado de item ainda sem resultado registrado.")
    n += 1
    acima = [g for g in grupos if g["uso"] >= 1]
    acima_sub = [s_ for s_ in por_subelemento(grupos, ajustes) if s_["uso"] >= 1 and s_["subelemento"]]
    linhas += ["", f"### {n}. CONCLUSÃO"]
    if acima or acima_sub:
        linhas.append("Ultrapassaram o limite no exercício e devem ser avaliados quanto a possível fracionamento de despesa:")
        linhas += [f"- Ramo {g['ramo']} (art. 75, {g['inciso']}): {brl(g['total'])}" for g in acima]
        linhas += [f"- Subelemento {s_['rotulo']} (art. 75, {s_['inciso']}): {brl(s_['total'])}" for s_ in acima_sub]
    else:
        linhas.append("Nenhum ramo de atividade nem subelemento ultrapassou o limite no exercício, com base nos dados "
                      "publicados.")
    linhas += ["", f"### {n + 1}. LIMITES DA VERIFICAÇÃO",
               "A verificação usa apenas contratações já publicadas no PNCP; compras recentes ainda não divulgadas não "
               "aparecem. A API pública não informa a natureza de despesa dos itens: o subelemento é sugerido e deve ser "
               "confirmado pelo operador. Despesas de TIC têm naturezas próprias (3.3.90.40 e 4.4.90.40), não "
               "detalhadas aqui. O enquadramento em \"mesmo ramo de atividade\" deve ser confirmado pelo agente de "
               "contratação."]
    return "\n".join(linhas)
