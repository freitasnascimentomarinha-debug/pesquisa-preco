"""Vantajosidade da adesão a Ata de Registro de Preços (Lei nº 14.133/2021, art. 86, §2º, I e II).

Para cada item escolhido na página Adesões, compara o preço registrado na ata com preços do mesmo item (mesmo código
CATMAT/CATSER) em outras atas e compras homologadas dos últimos 12 meses (IN SEGES/ME nº 65/2021, art. 5º, I e II),
saneia os extremos e calcula a diferença e a economia na quantidade pretendida.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from statistics import mean, median

import modelos_processo as MP

DADOSABERTOS = "https://dadosabertos.compras.gov.br"
FAIXA_SANEAMENTO = (0.5, 2.0)   # fora de 50% a 200% da mediana: inexequível ou excessivamente elevado


def _json(url, params, timeout=90):
    from servicos_publicos import http_get_json
    return http_get_json(url, params, timeout=timeout, tentativas=1)


def precos_atas(codigo_item: str, ata_propria: str = "", meses: int = 12) -> tuple[list[dict], str | None]:
    """Preços do mesmo item em atas com vigência iniciada nos últimos meses (exceto a própria ata)."""
    hoje = date.today()
    dados, erro = _json(f"{DADOSABERTOS}/modulo-arp/2_consultarARPItem",
                        {"pagina": 1, "tamanhoPagina": 500, "codigoItem": codigo_item,
                         "dataVigenciaInicialMin": (hoje - timedelta(days=30 * meses)).isoformat(),
                         "dataVigenciaInicialMax": hoje.isoformat()})
    if erro:
        return [], f"atas: {erro}"
    fontes = []
    for r in (dados or {}).get("resultado") or []:
        if r.get("numeroControlePncpAta") == ata_propria or not r.get("valorUnitario"):
            continue
        fontes.append({"fonte": "Ata de RP", "orgao": r.get("nomeUnidadeGerenciadora") or "",
                       "referencia": f"Ata {r.get('numeroAtaRegistroPreco')}", "valor": float(r["valorUnitario"]),
                       "data": str(r.get("dataVigenciaInicial") or "")[:10]})
    return fontes, None


def precos_compras(codigo_item: str, meses: int = 12) -> tuple[list[dict], str | None]:
    """Preços homologados do mesmo item em contratações publicadas no PNCP (consulta mais lenta)."""
    hoje = date.today()
    dados, erro = _json(f"{DADOSABERTOS}/modulo-contratacoes/2_consultarItensContratacoes_PNCP_14133",
                        {"pagina": 1, "tamanhoPagina": 200, "codItemCatalogo": codigo_item, "temResultado": "true",
                         "dataInclusaoPncpInicial": (hoje - timedelta(days=30 * meses)).isoformat(),
                         "dataInclusaoPncpFinal": hoje.isoformat()}, timeout=150)
    if erro:
        return [], f"compras homologadas: {erro}"
    fontes = []
    for r in (dados or {}).get("resultado") or []:
        if not r.get("valorUnitarioResultado"):
            continue
        fontes.append({"fonte": "Compra homologada", "orgao": str(r.get("unidadeOrgaoCodigoUnidade") or ""),
                       "referencia": str(r.get("numeroControlePNCPCompra") or r.get("idCompra") or ""),
                       "valor": float(r["valorUnitarioResultado"]), "data": str(r.get("dataResultado") or "")[:10],
                       "unidade": str(r.get("unidadeMedida") or "").strip()})
    return fontes, None


def sanear(valores: list[float]) -> tuple[list[float], list[float]]:
    """(aceitos, descartados) pela faixa em torno da mediana."""
    if len(valores) < 3:
        return list(valores), []
    med = median(valores)
    lo, hi = FAIXA_SANEAMENTO[0] * med, FAIXA_SANEAMENTO[1] * med
    aceitos = [v for v in valores if lo <= v <= hi]
    return aceitos, [v for v in valores if not lo <= v <= hi]


def analisar_item(item: dict, fontes: list[dict]) -> dict:
    """item: {'Item', 'Descrição', 'codigo', 'preco', 'Quantidade'}. Devolve a comparação com o mercado."""
    preco = float(item.get("preco") or 0)
    try:
        qtd = float(str(item.get("Quantidade") or "0").replace(",", "."))
    except ValueError:
        qtd = 0.0
    aceitos, descartados = sanear([f["valor"] for f in fontes])
    r = {"item": item.get("Item"), "descricao": item.get("Descrição"), "preco": preco, "quantidade": qtd,
         "fontes": len(fontes), "aceitos": len(aceitos), "descartados": descartados, "detalhe_fontes": fontes}
    if not aceitos or not preco:
        return {**r, "mediana": None, "media": None, "menor": None, "diferenca": None, "economia": None,
                "situacao": "⚪ sem preços de referência"}
    med = median(aceitos)
    dif = (preco - med) / med
    situacao = ("✅ vantajoso" if dif <= 0 else "🟡 até 10% acima do mercado" if dif <= 0.10 else "🔴 acima do mercado")
    if len(aceitos) < 3:
        situacao += " (menos de 3 preços)"
    return {**r, "mediana": med, "media": mean(aceitos), "menor": min(aceitos), "diferenca": dif,
            "economia": (med - preco) * qtd, "situacao": situacao}


def analisar(itens: list[dict], ata_propria: str = "", incluir_compras: bool = False) -> list[dict]:
    """Analisa vários itens em paralelo."""
    def um(item):
        codigo = str(item.get("codigo") or "").strip()
        if not codigo:
            return analisar_item(item, []) | {"erro": "item sem código CATMAT/CATSER"}
        fontes, erros = [], []
        f, e = precos_atas(codigo, ata_propria)
        fontes += f
        erros += [e] if e else []
        if incluir_compras:
            f, e = precos_compras(codigo)
            fontes += f
            erros += [e] if e else []
        return analisar_item(item, fontes) | {"erro": "; ".join(erros)}

    with ThreadPoolExecutor(max_workers=6) as ex:
        return list(ex.map(um, itens))


def resumo(resultados: list[dict]) -> dict:
    validos = [r for r in resultados if r["mediana"] is not None and r["quantidade"]]
    valor_ata = sum(r["preco"] * r["quantidade"] for r in validos)
    valor_mercado = sum(r["mediana"] * r["quantidade"] for r in validos)
    return {"valor_ata": valor_ata, "valor_mercado": valor_mercado, "economia": valor_mercado - valor_ata,
            "percentual": (valor_mercado - valor_ata) / valor_mercado if valor_mercado else None,
            "itens_com_referencia": len(validos), "itens": len(resultados),
            "desvantajosos": [r for r in resultados if r["situacao"].startswith("🔴")]}


def texto_justificativa(resultados: list[dict], ata: str) -> str:
    """Frase para o ofício/ETP: 'a adesão se justifica porque ...'."""
    s = resumo(resultados)
    if not s["itens_com_referencia"]:
        return ""
    texto = (f"os preços registrados na Ata nº {ata} foram comparados com {sum(r['aceitos'] for r in resultados)} preços "
             f"do mesmo item em outras atas e contratações dos últimos 12 meses (IN SEGES/ME nº 65/2021, art. 5º), e o "
             f"valor da adesão ({MP.brl(s['valor_ata'])}) é ")
    if s["economia"] >= 0:
        texto += (f"inferior em {MP.brl(s['economia'])} ({s['percentual'] * 100:.1f}%) ao valor pela mediana de mercado "
                  f"({MP.brl(s['valor_mercado'])}), o que demonstra a vantagem da adesão")
    else:
        texto += (f"superior em {MP.brl(-s['economia'])} ao valor pela mediana de mercado ({MP.brl(s['valor_mercado'])}); "
                  "a vantagem decorre de __________")
    return texto


def corpo_relatorio(ata: dict, resultados: list[dict]) -> str:
    brl = lambda v: MP.brl(v) if v is not None else "-"
    cel = lambda t: str(t or "").replace("|", "/").replace("\n", " ").strip()
    s = resumo(resultados)
    linhas = ["### 1. OBJETO",
              f"Análise da vantajosidade da adesão à Ata de Registro de Preços nº {ata.get('ata')}, gerenciada por "
              f"{ata.get('gerenciador')} (UASG {ata.get('uasg')}), decorrente do {ata.get('licitacao')}, nos termos do "
              "art. 86, §2º, I e II, da Lei nº 14.133/2021.",
              "", "### 2. METODOLOGIA",
              "Para cada item, o preço registrado foi comparado com os preços do mesmo item (mesmo código do catálogo) em "
              "outras atas de registro de preços e, quando consultadas, em contratações homologadas nos últimos 12 meses "
              f"(IN SEGES/ME nº 65/2021, art. 5º, I e II). Foram desconsiderados os preços abaixo de "
              f"{FAIXA_SANEAMENTO[0]:.0%} ou acima de {FAIXA_SANEAMENTO[1]:.0%} da mediana, por inexequíveis ou "
              "excessivamente elevados. A referência de mercado é a mediana dos preços aceitos.",
              "", "### 3. COMPARAÇÃO POR ITEM",
              "| Item | Descrição | Qtd | Preço da ata | Mediana de mercado | Preços (aceitos/total) | Diferença | Economia | Situação |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in resultados:
        dif = f"{r['diferenca'] * 100:+.1f}%" if r["diferenca"] is not None else "-"
        linhas.append(f"| {cel(r['item'])} | {cel(r['descricao'])[:90]} | {MP._qtd_txt(r['quantidade'])} | {brl(r['preco'])} | "
                      f"{brl(r['mediana'])} | {r['aceitos']}/{r['fontes']} | {dif} | {brl(r['economia'])} | "
                      f"{cel(r['situacao'][2:])} |")
    linhas.append(f"| | **TOTAL** | | **{brl(s['valor_ata'])}** | **{brl(s['valor_mercado'])}** | | | "
                  f"**{brl(s['economia'])}** | |")
    linhas += ["", "### 4. CONCLUSÃO"]
    if s["itens_com_referencia"]:
        pct = f" ({s['percentual'] * 100:.1f}%)" if s["percentual"] is not None else ""
        linhas.append(f"O valor total da adesão é de {brl(s['valor_ata'])}, contra {brl(s['valor_mercado'])} pela mediana "
                      f"de mercado, diferença de {brl(s['economia'])}{pct} "
                      f"{'a favor da Administração' if s['economia'] >= 0 else 'em desfavor da Administração'}.")
    sem = [r for r in resultados if r["mediana"] is None]
    if s["desvantajosos"]:
        linhas.append("Itens com preço registrado acima do mercado, que devem ser retirados ou ter a vantagem "
                      "justificada por outro motivo (urgência, risco de desabastecimento, condições de entrega):")
        linhas += [f"- Item {r['item']}: {r['descricao']}" for r in s["desvantajosos"]]
    if sem:
        linhas.append("Itens sem preço de referência suficiente, para os quais a compatibilidade com o mercado deve ser "
                      "demonstrada por pesquisa complementar:")
        linhas += [f"- Item {r['item']}: {r['descricao']}" for r in sem]
    linhas += ["", "### 5. FONTES CONSULTADAS", "| Item | Fonte | Órgão / referência | Data | Valor unitário |",
               "|---|---|---|---|---|"]
    for r in resultados:
        for f in r["detalhe_fontes"][:15]:
            linhas.append(f"| {cel(r['item'])} | {f['fonte']} | {cel(f['orgao'])} – {cel(f['referencia'])} | "
                          f"{f['data'] or '-'} | {brl(f['valor'])} |")
    return "\n".join(linhas)
