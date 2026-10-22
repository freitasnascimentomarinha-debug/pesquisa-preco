"""Vantajosidade da adesão a Ata de Registro de Preços (Lei nº 14.133/2021, art. 86, §2º, I e II).

Para cada item escolhido na página Adesões, compara o preço registrado na ata com preços de mercado dos últimos 12
meses (IN SEGES/ME nº 65/2021, art. 5º, I e II):
1. outras atas do mesmo código CATMAT/CATSER;
2. se marcado, compras homologadas do mesmo código (consulta lenta e limitada pelo Compras.gov.br);
3. se ainda houver menos de 3 preços, atas da mesma família (PDM) com descrição parecida;
4. preço informado pelo operador (pesquisa complementar), quando nada for encontrado.
Saneia os extremos e classifica: vantajoso (até a mediana), compatível com o mercado (dentro da faixa pesquisada),
acima do mercado, ou sem referência (o operador precisa pesquisar).
"""

from __future__ import annotations

import re
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from statistics import mean, median

import modelos_processo as MP

DADOSABERTOS = "https://dadosabertos.compras.gov.br"
FAIXA_SANEAMENTO = (0.5, 2.0)    # sem preço de estimativa: fora de 50% a 200% da mediana é descartado
FAIXA_ESTIMATIVA = (0.5, 1.3)    # com o preço da ata como estimativa: aceita de 50% a 130% dele
MAXIMO_PRECOS = 10               # usa até 10 preços, priorizando os menores
SEMELHANCA_MINIMA = 0.65         # descrições da mesma família consideradas comparáveis
FAIXA_FAMILIA = FAIXA_ESTIMATIVA  # item "semelhante" com preço fora desta faixa do preço da ata é outro produto
MINIMO_PRECOS = 3
MARGEM_COMPATIVEL = 0.10         # até 10% acima da mediana: compatível (critério da análise, não da lei)
_CACHE: dict[tuple, tuple[float, list]] = {}
_CACHE_TTL = 6 * 3600
_UMA_CONSULTA_LENTA = threading.Semaphore(1)   # a consulta de compras homologadas é lenta e devolve 429 se paralela

SEM_REFERENCIA = "🔴 sem preço de referência — pesquisar"


def _get(url: str, params: dict, timeout: int = 90) -> tuple[dict | None, str | None]:
    """GET com nova tentativa em 429 (muitas requisições) e 5xx, respeitando o Retry-After."""
    import requests
    from servicos_publicos import USER_AGENT
    erro = "sem resposta"
    for espera in (0, 3, 8, 15):
        if espera:
            time.sleep(espera)
        try:
            r = requests.get(url, params=params, timeout=timeout, headers=USER_AGENT)
        except requests.exceptions.Timeout:
            erro = "tempo esgotado"
            continue
        except requests.exceptions.RequestException as exc:
            erro = f"falha de conexão ({type(exc).__name__})"
            continue
        if r.status_code == 200:
            try:
                return r.json(), None
            except ValueError:
                return None, "resposta inválida"
        erro = "limite de consultas do Compras.gov.br (HTTP 429)" if r.status_code == 429 else f"HTTP {r.status_code}"
        if r.status_code == 429 and str(r.headers.get("Retry-After", "")).isdigit():
            time.sleep(min(int(r.headers["Retry-After"]), 30))
        if r.status_code != 429 and r.status_code < 500:
            break
    return None, erro


def _cacheado(chave: tuple, buscar):
    agora = time.time()
    if chave in _CACHE and agora - _CACHE[chave][0] < _CACHE_TTL:
        return _CACHE[chave][1], None
    dados, erro = buscar()
    if not erro:
        _CACHE[chave] = (agora, dados)
    return dados, erro


def _janela(meses: int = 12) -> tuple[str, str]:
    hoje = date.today()
    return (hoje - timedelta(days=30 * meses)).isoformat(), hoje.isoformat()


def _tokens(texto: str) -> set[str]:
    t = unicodedata.normalize("NFD", str(texto or "")).encode("ascii", "ignore").decode().lower()
    return {p for p in re.findall(r"[a-z0-9]+(?:[.,][0-9]+)?", t) if len(p) > 1}


def semelhanca(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta and tb else 0.0


def _fonte_ata(r: dict, rotulo: str = "Ata de RP") -> dict:
    return {"fonte": rotulo, "orgao": r.get("nomeUnidadeGerenciadora") or "",
            "referencia": f"Ata {r.get('numeroAtaRegistroPreco')}", "valor": float(r["valorUnitario"]),
            "data": str(r.get("dataVigenciaInicial") or "")[:10], "codigo": str(r.get("codigoItem") or "")}


def precos_atas(codigo_item: str, ata_propria: str = "") -> tuple[list[dict], str | None]:
    """Preços do mesmo código em atas com vigência iniciada nos últimos 12 meses (exceto a própria ata)."""
    ini, fim = _janela()
    dados, erro = _cacheado(("atas", codigo_item), lambda: _get(
        f"{DADOSABERTOS}/modulo-arp/2_consultarARPItem",
        {"pagina": 1, "tamanhoPagina": 500, "codigoItem": codigo_item, "dataVigenciaInicialMin": ini,
         "dataVigenciaInicialMax": fim}))
    if erro:
        return [], f"atas: {erro}"
    return [_fonte_ata(r) for r in (dados or {}).get("resultado") or []
            if r.get("numeroControlePncpAta") != ata_propria and r.get("valorUnitario")], None


def precos_familia(codigo_pdm: str, descricao: str, codigo_item: str, ata_propria: str = "",
                   preco_ata: float = 0.0) -> tuple[list[dict], str | None]:
    """Atas da mesma família (PDM) com descrição parecida — usado quando o código exato tem poucos preços.
    Descarta itens com preço muito distante do da ata: na mesma família há produtos bem diferentes
    (ex.: quadro de vidro de 3 m e quadro de avisos simples)."""
    ini, fim = _janela()
    dados, erro = _cacheado(("pdm", codigo_pdm), lambda: _get(
        f"{DADOSABERTOS}/modulo-arp/2_consultarARPItem",
        {"pagina": 1, "tamanhoPagina": 500, "codigoPdm": codigo_pdm, "dataVigenciaInicialMin": ini,
         "dataVigenciaInicialMax": fim}))
    if erro:
        return [], f"família: {erro}"
    candidatos = []
    for r in (dados or {}).get("resultado") or []:
        if (str(r.get("codigoItem")) == str(codigo_item) or r.get("numeroControlePncpAta") == ata_propria
                or not r.get("valorUnitario")):
            continue
        s = semelhanca(descricao, r.get("descricaoItem"))
        proporcao = float(r["valorUnitario"]) / preco_ata if preco_ata else 1.0
        if s >= SEMELHANCA_MINIMA and FAIXA_FAMILIA[0] <= proporcao <= FAIXA_FAMILIA[1]:
            candidatos.append((s, _fonte_ata(r, f"Ata de RP — item semelhante ({s:.0%})")))
    return [f for _s, f in sorted(candidatos, key=lambda x: -x[0])[:15]], None


def precos_compras(codigo_item: str) -> tuple[list[dict], str | None]:
    """Preços homologados do mesmo código em contratações do PNCP (uma consulta por vez, com nova tentativa)."""
    ini, fim = _janela()

    def buscar():
        with _UMA_CONSULTA_LENTA:
            return _get(f"{DADOSABERTOS}/modulo-contratacoes/2_consultarItensContratacoes_PNCP_14133",
                        {"pagina": 1, "tamanhoPagina": 200, "codItemCatalogo": codigo_item, "temResultado": "true",
                         "dataInclusaoPncpInicial": ini, "dataInclusaoPncpFinal": fim}, timeout=150)
    dados, erro = _cacheado(("compras", codigo_item), buscar)
    if erro:
        return [], f"compras homologadas: {erro}"
    return [{"fonte": "Compra homologada", "orgao": f"UASG {r.get('unidadeOrgaoCodigoUnidade') or ''}",
             "referencia": str(r.get("numeroControlePNCPCompra") or r.get("idCompra") or ""),
             "valor": float(r["valorUnitarioResultado"]), "data": str(r.get("dataResultado") or "")[:10]}
            for r in (dados or {}).get("resultado") or [] if r.get("valorUnitarioResultado")], None


def sanear(valores: list[float]) -> tuple[list[float], list[float]]:
    """(aceitos, descartados) pela faixa em torno da mediana."""
    if len(valores) < 3:
        return list(valores), []
    med = median(valores)
    lo, hi = FAIXA_SANEAMENTO[0] * med, FAIXA_SANEAMENTO[1] * med
    return [v for v in valores if lo <= v <= hi], [v for v in valores if not lo <= v <= hi]


def selecionar(valores: list[float], estimativa: float) -> tuple[list[float], list[float], str]:
    """Filtra os preços usando o preço da ata como estimativa: aceita os que estão entre 50% e 130% dele e, entre
    esses, usa os menores (até 10). Se todos estiverem acima da faixa, usa os 3 menores e avisa.
    Devolve (aceitos, descartados, observação)."""
    if not estimativa:
        aceitos, fora = sanear(valores)
        return aceitos, fora, ""
    lo, hi = FAIXA_ESTIMATIVA[0] * estimativa, FAIXA_ESTIMATIVA[1] * estimativa
    dentro = sorted(v for v in valores if lo <= v <= hi)
    if dentro:
        aceitos = dentro[:MAXIMO_PRECOS]
        obs = f"{len(dentro) - len(aceitos)} preço(s) da faixa não usados (priorizados os menores)" if len(dentro) > len(aceitos) else ""
    else:
        acima = sorted(v for v in valores if v > hi)
        aceitos = acima[:MINIMO_PRECOS]
        obs = (f"todos os preços encontrados estão acima de {FAIXA_ESTIMATIVA[1]:.0%} do preço da ata" if acima else
               f"preços encontrados abaixo de {FAIXA_ESTIMATIVA[0]:.0%} do preço da ata: confira se é o mesmo item"
               if valores else "")
    restantes = list(valores)
    for v in aceitos:
        restantes.remove(v)
    return aceitos, restantes, obs


def _qtd(valor) -> float:
    try:
        return float(str(valor if valor is not None else "0").replace(",", "."))
    except ValueError:
        return 0.0


def analisar_item(item: dict, fontes: list[dict]) -> dict:
    """item: {'Item', 'Descrição', 'preco', 'Quantidade', 'ref_manual'?}. Devolve a comparação com o mercado."""
    preco = float(item.get("preco") or 0)
    qtd = _qtd(item.get("Quantidade"))
    fontes = list(fontes)
    manual = _qtd(item.get("ref_manual"))
    if manual > 0:
        fontes.append({"fonte": "Pesquisa complementar do operador", "orgao": "-", "referencia": "informado na tela",
                       "valor": manual, "data": date.today().isoformat()})
    aceitos, descartados, obs = selecionar([f["valor"] for f in fontes], preco)
    usados = list(aceitos)
    for f in sorted(fontes, key=lambda x: x["valor"]):
        f["usado"] = f["valor"] in usados
        if f["usado"]:
            usados.remove(f["valor"])
    if manual > 0 and manual not in aceitos:   # o preço pesquisado pelo operador sempre entra
        aceitos.append(manual)
        fontes[-1]["usado"] = True
    r = {"item": item.get("Item"), "descricao": item.get("Descrição"), "preco": preco, "quantidade": qtd,
         "fontes": len(fontes), "aceitos": len(aceitos), "descartados": descartados, "detalhe_fontes": fontes,
         "familia": any("semelhante" in f["fonte"] for f in fontes), "manual": manual > 0, "obs_filtro": obs}
    if not aceitos or not preco:
        return {**r, "mediana": None, "media": None, "menor": None, "maior": None, "diferenca": None,
                "economia": None, "situacao": SEM_REFERENCIA, "classe": "sem_ref"}
    med = median(aceitos)
    dif = (preco - med) / med
    if preco <= med:
        situacao, classe = "✅ vantajoso", "vantajoso"
    elif preco <= max(aceitos) or dif <= MARGEM_COMPATIVEL:
        situacao, classe = "🟡 compatível com o mercado", "compativel"
    else:
        situacao, classe = "🔴 acima do mercado", "acima"
    if len(aceitos) < MINIMO_PRECOS:
        situacao += " (menos de 3 preços)"
    return {**r, "mediana": med, "media": mean(aceitos), "menor": min(aceitos), "maior": max(aceitos),
            "diferenca": dif, "economia": (med - preco) * qtd, "situacao": situacao, "classe": classe}


def coletar(item: dict, ata_propria: str, incluir_compras: bool) -> tuple[list[dict], list[str]]:
    codigo = str(item.get("codigo") or "").strip()
    fontes, avisos = [], []
    if not codigo:
        return [], ["item sem código CATMAT/CATSER"]
    f, e = precos_atas(codigo, ata_propria)
    fontes += f
    avisos += [e] if e else []
    if incluir_compras:
        f, e = precos_compras(codigo)
        fontes += f
        avisos += [e] if e else []
    if len(selecionar([x["valor"] for x in fontes], float(item.get("preco") or 0))[0]) < MINIMO_PRECOS and item.get("pdm"):
        f, e = precos_familia(str(item["pdm"]), item.get("Descrição") or "", codigo, ata_propria,
                              float(item.get("preco") or 0))
        fontes += f
        avisos += [e] if e else []
        if f:
            avisos.append(f"{len(f)} preço(s) de itens semelhantes da mesma família")
    return fontes, avisos


def analisar(itens: list[dict], ata_propria: str = "", incluir_compras: bool = False) -> list[dict]:
    """Analisa vários itens (atas em paralelo; compras homologadas uma por vez, para não esbarrar no limite)."""
    def um(item):
        fontes, avisos = coletar(item, ata_propria, incluir_compras)
        r = analisar_item(item, fontes)
        return r | {"erro": "; ".join(x for x in avisos + [r["obs_filtro"]] if x)}

    with ThreadPoolExecutor(max_workers=2 if incluir_compras else 4) as ex:
        return list(ex.map(um, itens))


def resumo(resultados: list[dict]) -> dict:
    validos = [r for r in resultados if r["mediana"] is not None and r["quantidade"]]
    valor_ata = sum(r["preco"] * r["quantidade"] for r in validos)
    valor_mercado = sum(r["mediana"] * r["quantidade"] for r in validos)
    return {"valor_ata": valor_ata, "valor_mercado": valor_mercado, "economia": valor_mercado - valor_ata,
            "percentual": (valor_mercado - valor_ata) / valor_mercado if valor_mercado else None,
            "itens_com_referencia": len([r for r in resultados if r["mediana"] is not None]), "itens": len(resultados),
            "compativeis": [r for r in resultados if r["classe"] == "compativel"],
            "desvantajosos": [r for r in resultados if r["classe"] == "acima"],
            "sem_referencia": [r for r in resultados if r["classe"] == "sem_ref"]}


def _pct(fracao: float) -> str:
    return f"{fracao * 100:.1f}%".replace(".", ",")


def justificativa_item(r: dict) -> str:
    """Frase que justifica (ou aponta a pendência de) cada item."""
    brl = MP.brl
    if r["classe"] == "vantajoso":
        return (f"Item {r['item']}: preço registrado de {brl(r['preco'])}, igual ou inferior à mediana de mercado "
                f"({brl(r['mediana'])}), o que demonstra a vantagem da adesão.")
    if r["classe"] == "compativel":
        motivo = (f"porém dentro da faixa de preços praticados no mercado para o mesmo item ({brl(r['menor'])} a "
                  f"{brl(r['maior'])})" if r["preco"] <= r["maior"] else
                  f"diferença dentro da margem de {MARGEM_COMPATIVEL:.0%} adotada nesta análise para a compatibilidade "
                  "com o mercado")
        return (f"Item {r['item']}: preço registrado de {brl(r['preco'])}, {_pct(r['diferenca'])} acima da mediana "
                f"({brl(r['mediana'])}), {motivo}, sendo compatível com os valores praticados no mercado (art. 86, §2º, "
                "II, da Lei nº 14.133/2021). A adesão permanece vantajosa pela economia processual e pela celeridade "
                "em relação a nova licitação.")
    if r["classe"] == "acima":
        return (f"Item {r['item']}: preço registrado de {brl(r['preco'])}, {_pct(r['diferenca'])} acima da mediana "
                f"de mercado ({brl(r['mediana'])}) e acima de todos os preços encontrados (até {brl(r['maior'])}). "
                "Retirar o item da adesão ou justificar: __________.")
    return (f"Item {r['item']}: não foi encontrado preço de referência nas bases consultadas. Preço de mercado obtido "
            "em pesquisa complementar (IN SEGES/ME nº 65/2021): __________ (fonte: __________).")


def texto_justificativa(resultados: list[dict], ata: str) -> str:
    """Frase para o ofício: 'a adesão se justifica porque ...'."""
    s = resumo(resultados)
    if not s["itens_com_referencia"]:
        return ""
    texto = (f"os preços registrados na Ata nº {ata} foram comparados com {sum(r['aceitos'] for r in resultados)} preços "
             "de mercado dos últimos 12 meses (IN SEGES/ME nº 65/2021, art. 5º)")
    if s["valor_mercado"]:
        if s["economia"] >= 0:
            texto += (f", e o valor da adesão ({MP.brl(s['valor_ata'])}) é inferior em {MP.brl(s['economia'])} "
                      f"({_pct(s['percentual'])}) ao valor pela mediana de mercado ({MP.brl(s['valor_mercado'])})")
        else:
            texto += (f"; o valor da adesão ({MP.brl(s['valor_ata'])}) está dentro da faixa de preços praticados no "
                      f"mercado (mediana de {MP.brl(s['valor_mercado'])}), sendo compatível com os valores de mercado, "
                      "e a adesão é vantajosa pela economia processual e pela celeridade em relação a nova licitação")
    if s["sem_referencia"]:
        texto += ("; para o(s) item(ns) " + ", ".join(str(r["item"]) for r in s["sem_referencia"]) +
                  ", o preço de mercado foi obtido em pesquisa complementar: __________")
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
              "Para cada item, o preço registrado foi comparado com preços de mercado dos últimos 12 meses (IN SEGES/ME "
              "nº 65/2021, art. 5º, I e II): outras atas de registro de preços do mesmo código do catálogo, compras "
              "homologadas do mesmo código (quando consultadas) e, se houvesse menos de três preços, atas de itens "
              "semelhantes da mesma família do catálogo. O preço registrado na ata foi usado como estimativa para filtrar "
              f"os preços: foram considerados os situados entre {FAIXA_ESTIMATIVA[0]:.0%} e {FAIXA_ESTIMATIVA[1]:.0%} "
              f"dele, priorizando os menores (até {MAXIMO_PRECOS} por item); preços fora dessa faixa foram tidos como "
              "inexequíveis, excessivamente elevados ou de produto diferente. Quando todos os preços encontrados "
              "superavam a faixa, usaram-se os três menores. O preço é vantajoso quando igual ou inferior à mediana e compatível com o mercado "
              "quando, acima dela, permanece dentro da faixa de preços pesquisados ou até "
              f"{MARGEM_COMPATIVEL:.0%} acima da mediana (margem adotada como critério desta análise).",
              "", "### 3. COMPARAÇÃO POR ITEM",
              "| Item | Descrição | Qtd | Preço da ata | Mediana de mercado | Faixa de mercado | Preços | Economia | Situação |",
              "|---|---|---|---|---|---|---|---|---|"]
    for r in resultados:
        med = brl(r["mediana"]) if r["mediana"] is not None else "**__________**"
        faixa = f"{brl(r['menor'])} a {brl(r['maior'])}" if r["mediana"] is not None else "**a pesquisar**"
        linhas.append(f"| {cel(r['item'])} | {cel(r['descricao'])[:90]} | {MP._qtd_txt(r['quantidade'])} | {brl(r['preco'])} | "
                      f"{med} | {faixa} | {r['aceitos']}/{r['fontes']} | {brl(r['economia'])} | {cel(r['situacao'][2:])} |")
    linhas.append(f"| | **TOTAL (itens com referência)** | | **{brl(s['valor_ata'])}** | **{brl(s['valor_mercado'])}** | | | "
                  f"**{brl(s['economia'])}** | |")
    linhas += ["", "### 4. JUSTIFICATIVA POR ITEM"] + [justificativa_item(r) for r in resultados]
    linhas += ["", "### 5. CONCLUSÃO"]
    if s["valor_mercado"]:
        pct = f" ({_pct(s['percentual'])})" if s["percentual"] is not None else ""
        linhas.append(f"O valor da adesão dos itens com referência é de {brl(s['valor_ata'])}, contra {brl(s['valor_mercado'])} "
                      f"pela mediana de mercado, diferença de {brl(s['economia'])}{pct} "
                      f"{'a favor da Administração' if s['economia'] >= 0 else 'dentro da faixa de mercado'}.")
    if s["desvantajosos"]:
        linhas.append("Itens acima de todos os preços de mercado encontrados, que devem sair da adesão ou ter a vantagem "
                      "justificada: " + ", ".join(str(r["item"]) for r in s["desvantajosos"]) + ".")
    if s["sem_referencia"]:
        linhas.append("Itens sem preço de referência nas bases consultadas, cuja compatibilidade com o mercado deve ser "
                      "demonstrada por pesquisa complementar antes do envio: "
                      + ", ".join(str(r["item"]) for r in s["sem_referencia"]) + ".")
    linhas += ["", "### 6. FONTES CONSULTADAS", "| Item | Fonte | Órgão / referência | Data | Valor unitário | Usado |",
               "|---|---|---|---|---|---|"]
    for r in resultados:
        fontes = sorted(r["detalhe_fontes"], key=lambda f: (not f.get("usado"), f["valor"]))
        for f in fontes[:15]:
            linhas.append(f"| {cel(r['item'])} | {cel(f['fonte'])} | {cel(f['orgao'])} – {cel(f['referencia'])} | "
                          f"{f['data'] or '-'} | {brl(f['valor'])} | {'sim' if f.get('usado') else 'não'} |")
    return "\n".join(linhas)
