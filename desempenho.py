"""Teste de desempenho da pesquisa na internet: 15 itens já treinados (da memória) x 15 itens novos.

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
    """Itens que a memória nunca viu (nenhuma loja cotou algo parecido)."""
    conhecidos = {i for loja in memoria.get("lojas", {}).values() for i in loja.get("itens", [])}
    novos = [item for item in ITENS_NOVOS if not any(_parecido(item, c, 0.6) for c in conhecidos)]
    return novos[:quantidade]


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
