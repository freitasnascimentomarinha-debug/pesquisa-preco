"""Desempenho da pesquisa na internet: medição (tempo, preços, acertividade) e aprendizado com ela (final do arquivo).

Medição de um lote de 15 itens (já treinados da memória x novos), hoje sem tela própria:

Mede, por item, o tempo até ter os preços (meta: média de até 2 minutos para 3 preços) e a acertividade (meta: 90% a 100%):
- automática: o nome do anúncio confere com o item (sinonimos.confere_nome) e a embalagem/medida não é diferente da pedida;
- revisada: o usuário marca na tabela os anúncios que estão errados (ou certos) e as métricas são recalculadas.
Sem rede e sem Streamlit neste módulo: só listas e contas (testável)."""
import embalagem
import memoria_lojas
import sinonimos

META_SEGUNDOS = 120
META_ACERTO = 0.90
PRECOS_POR_ITEM = 3

# candidatos a "itens novos" (nunca pesquisados): variados em natureza, nome popular e medida
ITENS_NOVOS = [
    "Maizena 500g", "Bombril pacote c/ 8", "Pilha palito AAA c/ 4", "Fita dupla face 12mm x 30m", "Pasta suspensa kraft",
    "Tesoura escolar 21cm", "Café em pó 500g", "Água sanitária 2 litros", "Cabo HDMI 2m", "Mouse óptico USB",
    "Disjuntor 20A monopolar", "Fita veda rosca 18mm x 25m", "Cadeira giratória de escritório", "Ventilador de mesa 30cm", "Tinta acrílica branca 18 litros",
    "Cotonete caixa c/ 75", "Papel toalha interfolhado", "Extintor de incêndio ABC 4kg", "Garrafa térmica 1 litro", "Régua de tomada 5 tomadas",
    "Caneta marca texto verde", "Arquivo morto caixa de papelão", "Lixeira com pedal 15 litros", "Álcool etílico 70% 1 litro", "Fio flexível 2,5mm 100m",
    # reserva: cada teste usa os que a memória ainda não viu; depois que um teste roda, esses itens passam a ser "treinados"
    "Saco de lixo 60 litros c/ 100", "Esponja multiuso dupla face", "Vassoura de piaçava", "Rodo de borracha 40cm", "Balde plástico 12 litros",
    "Desinfetante pinho 2 litros", "Sabonete líquido 5 litros", "Álcool em gel 70% 500ml", "Máscara descartável tripla c/ 50", "Luva nitrílica tamanho M c/ 100",
    "Pasta AZ lombo largo", "Envelope saco branco 25x35", "Fita adesiva marrom 48mm x 50m", "Cola branca 1 litro", "Calculadora de mesa 12 dígitos",
    "Pendrive 32GB", "Teclado USB ABNT2", "Cabo de rede cat6 5m", "Nobreak 600VA", "Resma de papel A3",
    "Lâmpada LED tubular 18W", "Extensão elétrica 5m", "Interruptor simples 10A", "Tomada 2P+T 10A", "Alicate universal 8 polegadas",
    "Martelo de unha 27mm", "Trena 5 metros", "Furadeira de impacto 500W", "Chave inglesa 12 polegadas", "Cimento CP II 50kg",
    "Tubo PVC esgoto 100mm 6m", "Torneira de pia cromada", "Registro de gaveta 3/4", "Capacete de segurança branco", "Óculos de proteção incolor",
    "Protetor auricular tipo plug", "Bota de segurança nº 42", "Extintor de pó químico 6kg", "Bebedouro de coluna", "Micro-ondas 30 litros",
    "Cafeteira elétrica 30 xícaras", "Fogão 4 bocas", "Ar condicionado split 12000 BTUs", "Ventilador de coluna 50cm", "Mesa de escritório 1,20m",
    "Armário de aço 2 portas", "Quadro branco 120x90cm", "Açúcar refinado 1kg", "Óleo de soja 900ml", "Macarrão espaguete 500g",
    "Leite integral 1 litro", "Pneu aro 15", "Palheta limpador para-brisa 20 polegadas", "Óleo lubrificante 5W30 1 litro", "Lixa d'água grão 220",
    "Pincel trincha 2 polegadas", "Rolo de lã 23cm", "Tinta spray preto fosco", "Disco de corte 4.1/2", "Broca para concreto 8mm",
    "Cadeado 40mm", "Corrente galvanizada 6mm", "Fita zebrada 70mm x 200m", "Cone de sinalização 75cm", "Colete refletivo",
]
# reserva caso a memória ainda não tenha 15 itens treinados
ITENS_TREINADOS_PADRAO = [
    "caneta esferográfica azul", "caneta piloto azul", "lápis preto", "detergente 500ml", "fita isolante", "grampeador", "papel a4 sulfite",
    "frigobar", "papel contact", "papel crepom", "lâmpada led branca e27", "parafuso sextavado 1/2", "chave de fenda",
    "caneta marca texto amarelo", "luva de limpeza",
]


def _parecido(a: str, b: str, limite: float = 0.8) -> bool:
    return memoria_lojas.similaridade(a, b) >= limite


def itens_treinados(memoria: dict, quantidade: int = 15) -> list[str]:
    """Os itens que mais lojas já cotaram na memória (sem repetir variações do mesmo item); completa com a lista padrão se faltar."""
    contagem: dict[str, int] = {}
    for loja in memoria.get("lojas", {}).values():
        for item in loja.get("itens", []):
            contagem[item] = contagem.get(item, 0) + 1
    escolhidos: list[str] = []
    for item, _ in sorted(contagem.items(), key=lambda x: (-x[1], x[0])):
        if not any(_parecido(item, outro) for outro in escolhidos):
            escolhidos.append(item)
        if len(escolhidos) == quantidade:
            return escolhidos
    for item in ITENS_TREINADOS_PADRAO:
        if len(escolhidos) < quantidade and not any(_parecido(item, outro) for outro in escolhidos):
            escolhidos.append(item)
    return escolhidos


def itens_novos(memoria: dict, quantidade: int = 15) -> list[str]:
    """Itens que a memória nunca viu (nenhuma loja cotou algo parecido). Se não houver inéditos suficientes (testes anteriores já
    gravaram os itens na memória), completa com os menos vistos, para o teste nunca ficar vazio. Veja `itens_novos_info`."""
    return itens_novos_info(memoria, quantidade)[0]


def itens_novos_info(memoria: dict, quantidade: int = 15) -> tuple[list[str], int]:
    """(itens, quantos deles são inéditos)."""
    contagem: dict[str, int] = {}
    for loja in memoria.get("lojas", {}).values():
        for item in loja.get("itens", []):
            contagem[item] = contagem.get(item, 0) + 1
    conhecidos = list(contagem)

    def vezes_visto(item: str) -> int:
        return sum(n for c, n in contagem.items() if _parecido(item, c, 0.6))

    ineditos = [item for item in ITENS_NOVOS if not any(_parecido(item, c, 0.6) for c in conhecidos)]
    escolhidos = ineditos[:quantidade]
    if len(escolhidos) < quantidade:  # completa com os menos vistos (ordem estável)
        restantes = sorted((i for i in ITENS_NOVOS if i not in escolhidos), key=lambda i: (vezes_visto(i), ITENS_NOVOS.index(i)))
        escolhidos += restantes[:quantidade - len(escolhidos)]
    return escolhidos, len(ineditos[:quantidade])


def avaliar(itens: list[str], analise: list[dict], tempos: dict, max_precos: int = PRECOS_POR_ITEM):
    """(linhas por preço, linhas por item, métricas). `analise` = web_precos.analisar_todos; `tempos` = {item: {"segundos", "precos", ...}}."""
    por_preco, por_item = [], []
    for item, resultado in zip(itens, analise):
        tempo = tempos.get(item, {})
        precos = resultado.get("precos", [])
        certos = 0
        for p in precos:
            nome_ok = sinonimos.confere_nome(item, p.get("titulo", ""))
            medida_ok = p.get("medida_confere") != "diferente"
            auto = bool(nome_ok and medida_ok)
            certos += auto
            por_preco.append({"Item": item, "Loja": p.get("dominio", ""), "Preço": p.get("preco"), "Título do anúncio": p.get("titulo", ""),
                              "Nome confere": nome_ok, "Medida": {"igual": "igual", "diferente": "DIFERENTE", "sem_medida": "-"}.get(p.get("medida_confere", ""), "-"),
                              "Correto?": auto, "Endereço": p.get("url", "")})
        segundos = tempo.get("segundos")
        por_item.append({"Item": item, "Tempo (s)": segundos, "Preços": len(precos), "Completo (3)": len(precos) >= max_precos,
                         "Dentro de 2 min": (segundos is not None and segundos <= META_SEGUNDOS), "Consultas à API": tempo.get("consultas_api", 0),
                         "Páginas no navegador": tempo.get("navegador", 0), "Acertos automáticos": f"{certos}/{len(precos)}"})
    return por_preco, por_item, metricas(por_item, por_preco)


def metricas(por_item: list[dict], por_preco: list[dict]) -> dict:
    """Médias do teste. `por_preco` com a coluna 'Correto?' (automática ou revisada pelo usuário)."""
    tempos = [i["Tempo (s)"] for i in por_item if i["Tempo (s)"] is not None]
    total_precos = len(por_preco)
    certos = sum(1 for p in por_preco if p["Correto?"])
    itens_com_preco = {p["Item"] for p in por_preco}
    itens_certos = sum(1 for item in itens_com_preco if all(p["Correto?"] for p in por_preco if p["Item"] == item))
    n = len(por_item) or 1
    return {
        "itens": len(por_item), "tempo_medio_s": round(sum(tempos) / len(tempos), 1) if tempos else None,
        "tempo_maximo_s": round(max(tempos), 1) if tempos else None,
        "pct_dentro_2min": round(100 * sum(1 for i in por_item if i["Dentro de 2 min"]) / n, 1),
        "pct_itens_completos": round(100 * sum(1 for i in por_item if i["Completo (3)"]) / n, 1),
        "precos": total_precos, "pct_precos_certos": round(100 * certos / total_precos, 1) if total_precos else 0.0,
        "pct_itens_todos_certos": round(100 * itens_certos / len(itens_com_preco), 1) if itens_com_preco else 0.0,
        "meta_tempo_ok": bool(tempos) and sum(tempos) / len(tempos) <= META_SEGUNDOS,
        "meta_acerto_ok": bool(total_precos) and certos / total_precos >= META_ACERTO,
    }


# ---------- aprendizado com o próprio desempenho ----------
# A cada item pesquisado o sistema anota quanto tempo levou, quantos preços valeram, quantos pareciam certos e QUAL ORIGEM deu os preços:
#   "parecida" = lojas que já cotaram item parecido; "natureza" = melhores lojas do ramo do item; "busca" = buscadores (frases).
# Por natureza ele guarda, com decaimento (o recente pesa mais), quantas tentativas cada origem fez e quantas renderam preço.
# Nas próximas pesquisas, `limite_lojas` usa essa estatística para tentar mais as origens que rendem e menos as que só gastam tempo.

DECAIMENTO = 0.95
MIN_ITENS_NATUREZA = 5  # abaixo disso a estatística da natureza não é confiável: vale o limite padrão
MIN_TENTATIVAS = 6  # tentativas da origem (com peso recente) para confiar na taxa dela
TAXA_BOA = 0.5  # origem que dá preço em metade das tentativas ou mais: ganha mais uma tentativa por item
TAXA_RUIM = 0.15  # origem que quase nunca dá preço: perde uma tentativa por item
EXPLORAR_A_CADA = 5  # a cada N pesquisas o limite padrão é usado, para a origem ruim ter nova chance
MAX_EXECUCOES = 300
SEM_NATUREZA = "(sem natureza)"
ORIGENS = {"parecida": "lojas de itens parecidos", "natureza": "melhores lojas do ramo", "busca": "buscadores"}


def _dados_natureza(memoria: dict, natureza: str) -> dict:
    return memoria.setdefault("desempenho", {"execucoes": [], "naturezas": {}}).setdefault("naturezas", {}).setdefault(
        natureza or SEM_NATUREZA, {"itens": 0.0, "segundos": 0.0, "precos": 0.0, "certos": 0.0, "completos": 0.0, "origens": {}})


def acertos_automaticos(item: str, orcamentos: list[dict]) -> int:
    """Quantos dos orçamentos parecem certos: nome do anúncio confere com o item e a medida não é diferente."""
    return sum(1 for p in orcamentos if sinonimos.confere_nome(item, p.get("titulo", "")) and p.get("medida_confere") != "diferente")


def registrar_item(memoria: dict, item: str, natureza: str, segundos: float, orcamentos: list[dict], max_fontes: int,
                   origens: dict, consultas_api: int = 0, navegador: int = 0, frase: str = "") -> None:
    """Um item pesquisado. `origens` = {origem: {"tentativas", "precos", "segundos"}}; `orcamentos` = preços válidos do item."""
    certos = acertos_automaticos(item, orcamentos)
    desempenho = memoria.setdefault("desempenho", {"execucoes": [], "naturezas": {}})
    desempenho.setdefault("execucoes", []).append({
        "data": memoria_lojas.dt.datetime.now().isoformat(timespec="seconds"), "item": item, "natureza": natureza or SEM_NATUREZA,
        "segundos": round(segundos, 1), "precos": len(orcamentos), "certos": certos, "completo": len(orcamentos) >= max_fontes,
        "api": consultas_api, "navegador": navegador, "frase": frase,
        "origens": {o: {k: round(v, 1) for k, v in d.items()} for o, d in origens.items() if d.get("tentativas") or d.get("precos")}})
    del desempenho["execucoes"][:-MAX_EXECUCOES]
    nat = _dados_natureza(memoria, natureza)
    for campo, valor in (("itens", 1), ("segundos", segundos), ("precos", len(orcamentos)), ("certos", certos),
                         ("completos", 1 if len(orcamentos) >= max_fontes else 0)):
        nat[campo] = round(nat.get(campo, 0.0) * DECAIMENTO + valor, 3)
    for origem, dados in origens.items():
        if not dados.get("tentativas") and not dados.get("precos"):
            continue
        antigo = nat["origens"].setdefault(origem, {"tentativas": 0.0, "precos": 0.0, "segundos": 0.0})
        for campo in ("tentativas", "precos", "segundos"):
            antigo[campo] = round(antigo.get(campo, 0.0) * DECAIMENTO + dados.get(campo, 0), 3)
    memoria["_mudou"] = True


def registrar_revisao(memoria: dict, item: str, errados: int) -> None:
    """O usuário apontou anúncios errados do item na última pesquisa: corrige a acertividade (a revisão humana vale mais que a automática)."""
    execucoes = memoria.get("desempenho", {}).get("execucoes", [])
    for execucao in reversed(execucoes):
        if execucao.get("item") == item and execucao.get("errados") is None:
            execucao["errados"] = errados
            nat = _dados_natureza(memoria, execucao.get("natureza", ""))
            nat["certos"] = round(max(0.0, nat["certos"] - max(0, errados - (execucao["precos"] - execucao["certos"]))), 3)
            execucao["certos"] = max(0, execucao["precos"] - errados)
            memoria["_mudou"] = True
            return


def taxa_da_origem(memoria: dict, natureza: str, origem: str) -> tuple[float, float, float]:
    """(tentativas com peso recente, preços por tentativa, segundos por tentativa) da origem nessa natureza."""
    nat = memoria.get("desempenho", {}).get("naturezas", {}).get(natureza or SEM_NATUREZA)
    dados = (nat or {}).get("origens", {}).get(origem)
    if not nat or not dados or nat.get("itens", 0) < MIN_ITENS_NATUREZA or dados.get("tentativas", 0) <= 0:
        return 0.0, 0.0, 0.0
    tentativas = dados["tentativas"]
    return tentativas, dados.get("precos", 0.0) / tentativas, dados.get("segundos", 0.0) / tentativas


def limite_lojas(memoria: dict, natureza: str, origem: str, padrao: int) -> tuple[int, str]:
    """Quantas lojas dessa origem tentar neste item, pelo que ela rendeu em itens da mesma natureza. Devolve (limite, explicação para o log).
    Origem que rende: +1 loja; origem que quase não rende (ou rende pouco e demora): -1; nunca menos de 1, e a cada EXPLORAR_A_CADA
    pesquisas vale o padrão (para a origem ruim ter nova chance)."""
    tentativas, taxa, segundos = taxa_da_origem(memoria, natureza, origem)
    if tentativas < MIN_TENTATIVAS:
        return padrao, ""
    if memoria.get("buscas", 0) % EXPLORAR_A_CADA == 0:
        return padrao, f"{ORIGENS[origem]}: teste de rotina com o limite padrão ({padrao})"
    resumo = f"{ORIGENS[origem]}: {taxa:.2f} preço por tentativa, {segundos:.0f} s cada"
    if taxa >= TAXA_BOA:
        return padrao + 1, f"{resumo} → vai tentar {padrao + 1} loja(s)"
    if taxa < TAXA_RUIM or (taxa < 0.3 and segundos > 30):
        return max(1, padrao - 1), f"{resumo} → vai tentar só {max(1, padrao - 1)} loja(s)"
    return padrao, ""


def resumo_geral(memoria: dict, ultimas: int = 40) -> dict:
    """Indicadores das últimas pesquisas e a tendência (metade mais antiga x metade mais recente) para o painel."""
    execucoes = memoria.get("desempenho", {}).get("execucoes", [])[-ultimas:]

    def indicadores(grupo: list[dict]) -> dict:
        if not grupo:
            return {"itens": 0, "tempo_medio_s": None, "pct_completos": None, "pct_certos": None}
        precos = sum(e["precos"] for e in grupo)
        return {"itens": len(grupo), "tempo_medio_s": round(sum(e["segundos"] for e in grupo) / len(grupo), 1),
                "pct_completos": round(100 * sum(1 for e in grupo if e["completo"]) / len(grupo), 1),
                "pct_certos": round(100 * sum(e["certos"] for e in grupo) / precos, 1) if precos else None}

    meio = len(execucoes) // 2
    return {"geral": indicadores(execucoes), "antes": indicadores(execucoes[:meio]) if meio else None,
            "depois": indicadores(execucoes[meio:]) if meio else None, "total_registrado": len(memoria.get("desempenho", {}).get("execucoes", []))}


def tabela_naturezas(memoria: dict) -> list[dict]:
    """Uma linha por natureza: itens, tempo médio, preços certos e a origem que mais rende."""
    linhas = []
    for natureza, d in sorted(memoria.get("desempenho", {}).get("naturezas", {}).items(), key=lambda x: -x[1].get("itens", 0)):
        itens = d.get("itens", 0) or 1
        origens = {o: (v["precos"] / v["tentativas"] if v.get("tentativas") else 0.0, v["tentativas"]) for o, v in d.get("origens", {}).items()}
        melhor = max(origens.items(), key=lambda x: x[1][0], default=(None, (0, 0)))
        linhas.append({"Natureza": natureza, "Itens (peso recente)": round(d.get("itens", 0), 1), "Tempo médio (s)": round(d.get("segundos", 0) / itens, 1),
                       "Com 3 preços (%)": round(100 * d.get("completos", 0) / itens, 1),
                       "Anúncios certos (%)": round(100 * d.get("certos", 0) / d["precos"], 1) if d.get("precos") else None,
                       "Origem que mais rende": f"{ORIGENS.get(melhor[0], '-')} ({melhor[1][0]:.2f} preço/tentativa)" if melhor[0] else "-",
                       "Por origem": "; ".join(f"{ORIGENS[o]} {t[0]:.2f}" for o, t in origens.items() if o in ORIGENS)})
    return linhas
