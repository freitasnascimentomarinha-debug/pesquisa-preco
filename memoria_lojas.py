"""Memória de lojas da página Web Scraping: aprende, com o uso, quais sites dão preço e para quais itens.

- Lojas que deram preço: site, nº de acertos, data do último e os itens cotados (para achar lojas de itens parecidos).
- Sites que falham sempre (bloqueio, sem preço legível): depois de FALHAS_PARA_PULAR falhas sem nenhum acerto, são pulados.

A memória fica no repositório do GitHub, num branch separado (BRANCH), para não reiniciar o app a cada gravação.
Sem chave do GitHub nos Secrets, vale só enquanto o app estiver no ar (arquivo local).
"""

from __future__ import annotations

import base64
import datetime as dt
import json
import os
import re
import unicodedata

import naturezas

ARQUIVO = "memoria_lojas.json"
BRANCH = "memoria-scraping"
REPOSITORIO_PADRAO = "freitasnascimentomarinha-debug/pesquisa-preco"
ARQUIVO_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".memoria_lojas_local.json")
FALHAS_PARA_PULAR = 3
MAX_ITENS_POR_LOJA = 60
MAX_LOJAS_POR_ITEM = 3
SIMILARIDADE_MINIMA = 0.6  # "fita crepe" x "fita isolante" (0,5) não conta como parecido
DIAS_PARA_ESQUECER_FALHAS = 60
API = "https://api.github.com"


def vazia() -> dict:
    return {"versao": 1, "lojas": {}, "falhas": {}, "frases": {}, "buscas": 0, "sem_busca": {}, "serper": {"mes": "", "n": 0}, "tavily": {"mes": "", "n": 0}}


def dominio(url_ou_site: str) -> str:
    texto = re.sub(r"^[a-z]+://", "", str(url_ou_site or "").strip().lower()).split("/")[0].split(":")[0]
    return texto[4:] if texto.startswith("www.") else texto


def _palavras(texto: str) -> set[str]:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    palavras = set()
    for p in re.findall(r"[a-z0-9]+", texto):
        if len(p) > 2 or any(c.isdigit() for c in p):  # mantém medidas curtas como "a4", "m8"
            palavras.add(p[:-1] if len(p) > 3 and p.endswith("s") else p)
    return palavras


def similaridade(item_a: str, item_b: str) -> float:
    """Proporção das palavras do item menor presentes no outro ('papel a4 75g' x 'papel a4 resma' = 2/3)."""
    a, b = _palavras(item_a), _palavras(item_b)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _hoje() -> str:
    return dt.date.today().isoformat()


# ---------- uso durante a pesquisa ----------

METODOS = ("navegador", "texto")


def _falha_nova() -> dict:
    return {"navegador": 0, "texto": 0, "ultimo": ""}


def _migrar_falha(falha: dict) -> dict:
    """Memória antiga guardava um só contador ('falhas', que vinha da leitura por texto)."""
    if "falhas" in falha and "texto" not in falha:
        return {"navegador": 0, "texto": falha["falhas"], "ultimo": falha.get("ultimo", "")}
    return {"navegador": falha.get("navegador", 0), "texto": falha.get("texto", 0), "ultimo": falha.get("ultimo", "")}


def registrar_acerto(memoria: dict, url: str, item: str, metodo: str = "texto") -> None:
    """Loja que deu preço: guarda o item e por qual método (navegador/texto); limpa as falhas dela."""
    site = dominio(url)
    if not site:
        return
    loja = memoria["lojas"].setdefault(site, {"acertos": 0, "ultimo": "", "itens": []})
    loja["acertos"] += 1
    loja["ultimo"] = _hoje()
    loja.setdefault("metodos", {"navegador": 0, "texto": 0})
    loja["metodos"][metodo] = loja["metodos"].get(metodo, 0) + 1
    item = item.strip().lower()
    if item in loja["itens"]:
        loja["itens"].remove(item)
    loja["itens"].insert(0, item)
    del loja["itens"][MAX_ITENS_POR_LOJA:]
    natureza = naturezas.classificar(item)
    if natureza:  # a loja vai bem nesse ramo: será tentada nos próximos itens da mesma natureza
        contagem = loja.setdefault("naturezas", {})
        contagem[natureza] = contagem.get(natureza, 0) + 1
    # a página que deu o preço: serve de atalho quando os buscadores estão bloqueados
    paginas = loja.setdefault("paginas", {})
    paginas[item] = url
    for antigo in [i for i in paginas if i not in loja["itens"]]:
        del paginas[antigo]
    memoria["falhas"].pop(site, None)  # deu preço: não é mais um site problemático
    memoria["_mudou"] = True


def registrar_falha(memoria: dict, url: str, metodo: str = "texto") -> None:
    """Site em que o método (navegador ou texto) não achou preço. Cada método tem a sua própria contagem."""
    site = dominio(url)
    if not site or site in memoria["lojas"]:
        return  # loja que já deu preço não é marcada como problemática por uma falha
    falha = memoria["falhas"][site] = _migrar_falha(memoria["falhas"].get(site, _falha_nova()))
    falha[metodo] += 1
    falha["ultimo"] = _hoje()
    memoria["_mudou"] = True


def deve_pular(memoria: dict, url: str, metodo: str = "texto") -> bool:
    """Pula o site só se ESSE método falhou FALHAS_PARA_PULAR vezes, sem nenhum acerto, nos últimos DIAS_PARA_ESQUECER_FALHAS dias.
    Falhas da leitura por texto não impedem o navegador (que tem mais chance), e vice-versa."""
    falha = memoria["falhas"].get(dominio(url))
    if not falha:
        return False
    falha = _migrar_falha(falha)
    if falha.get(metodo, 0) < FALHAS_PARA_PULAR:
        return False
    try:
        idade = (dt.date.today() - dt.date.fromisoformat(falha["ultimo"])).days
    except ValueError:
        return True
    return idade <= DIAS_PARA_ESQUECER_FALHAS


def metodo_preferido(memoria: dict, url: str) -> str:
    """Por qual método a loja costuma dar preço: 'texto' se só deu por texto; 'navegador' se deu pelo navegador (ou se é desconhecida,
    porque o navegador tem mais chance). Com os dois, vale o que mais deu certo."""
    loja = memoria["lojas"].get(dominio(url))
    if not loja:
        return "navegador"
    metodos = loja.get("metodos", {})
    n_navegador, n_texto = metodos.get("navegador", 0), metodos.get("texto", 0)
    return "texto" if n_texto > n_navegador else "navegador"


# ---------- aprendizado das frases de busca ----------

PESO_DO_PASSADO = 0.95  # a cada uso da frase, o histórico dela vale um pouco menos (o que aconteceu há pouco pesa mais)
PRIOR_ACERTOS, PRIOR_USOS = 3.0, 3.0  # frase nova começa com nota 1,0 (1 preço por busca) e vai se afastando com os dados
USOS_MINIMOS = 5  # abaixo disso a nota ainda não é confiável: a frase fica na ordem original
EXPLORAR_A_CADA = 5  # a cada N pesquisas, a frase de pior nota passa na frente para ter nova chance


def nota_da_frase(memoria: dict, frase: str) -> float:
    dados = memoria.get("frases", {}).get(frase)
    if not dados:
        return PRIOR_ACERTOS / PRIOR_USOS
    return (dados.get("acertos", 0) + PRIOR_ACERTOS) / (dados.get("usos", 0) + PRIOR_USOS)


def registrar_busca(memoria: dict, frase: str, acertos: int) -> None:
    """Uma busca feita com a frase (modelo, com {item}) e quantos preços válidos ela rendeu."""
    dados = memoria.setdefault("frases", {}).setdefault(frase, {"usos": 0.0, "acertos": 0.0, "ultimo": ""})
    dados["usos"] = round(dados["usos"] * PESO_DO_PASSADO + 1, 4)  # o histórico da própria frase perde um pouco de peso a cada uso
    dados["acertos"] = round(dados["acertos"] * PESO_DO_PASSADO + acertos, 4)
    dados["ultimo"] = _hoje()
    memoria["_mudou"] = True


def ordenar_frases(memoria: dict, frases: list[str]) -> tuple[list[str], str]:
    """Ordem de uso das frases: as de melhor nota primeiro. Só reordena frases com USOS_MINIMOS usos ou mais (as demais mantêm o lugar);
    a cada EXPLORAR_A_CADA pesquisas a de pior nota vai para a frente. Devolve (ordem, explicação para o log)."""
    memoria["buscas"] = memoria.get("buscas", 0) + 1
    memoria["_mudou"] = True
    dados = memoria.get("frases", {})
    conhecidas = [f for f in frases if dados.get(f, {}).get("usos", 0) >= USOS_MINIMOS]
    if len(conhecidas) < 2:
        return list(frases), "poucos dados ainda: ordem original"
    ordenadas = sorted(conhecidas, key=lambda f: -nota_da_frase(memoria, f))
    lugares = iter(ordenadas)
    ordem = [next(lugares) if f in conhecidas else f for f in frases]  # as frases sem dados ficam onde estavam
    explicacao = "melhores: " + ", ".join(f"'{f}' ({nota_da_frase(memoria, f):.2f})" for f in ordenadas[:2])
    if memoria["buscas"] % EXPLORAR_A_CADA == 0:
        pior = ordenadas[-1]
        ordem.remove(pior)
        ordem.insert(0, pior)
        explicacao += f"; teste de rotina da pior: '{pior}'"
    return ordem, explicacao


def lojas_para_item(memoria: dict, item: str, limite: int = MAX_LOJAS_POR_ITEM) -> list[tuple[str, str]]:
    """Lojas que já deram preço para itens parecidos: [(site, item parecido)], das mais parecidas/mais acertos para as menos."""
    candidatas = []
    for site, loja in memoria["lojas"].items():
        melhor, parecido = 0.0, ""
        for anterior in loja["itens"]:
            nota = similaridade(item, anterior)
            if nota > melhor:
                melhor, parecido = nota, anterior
        if melhor >= SIMILARIDADE_MINIMA:
            candidatas.append((melhor, loja["acertos"], loja["ultimo"], site, parecido))
    candidatas.sort(reverse=True)
    return [(site, parecido) for _, _, _, site, parecido in candidatas[:limite]]


MAX_LOJAS_POR_NATUREZA = 3  # lojas da mesma natureza tentadas por item (além das de itens parecidos)


def completar_naturezas(memoria: dict) -> int:
    """Classifica as lojas que ainda não têm natureza a partir dos itens que já cotaram (memória antiga). Devolve quantas foram classificadas."""
    classificadas = 0
    for loja in memoria["lojas"].values():
        if loja.get("naturezas"):
            continue
        contagem: dict[str, int] = {}
        for item in loja.get("itens", []):
            natureza = naturezas.classificar(item)
            if natureza:
                contagem[natureza] = contagem.get(natureza, 0) + 1
        if contagem:
            loja["naturezas"] = contagem
            classificadas += 1
    if classificadas:
        memoria["_mudou"] = True
    return classificadas


def lojas_por_natureza(memoria: dict, natureza: str, excluir=(), limite: int = MAX_LOJAS_POR_NATUREZA) -> list[tuple[str, int]]:
    """Lojas que mais deram preço em itens dessa natureza: [(site, nº de itens da natureza)], das melhores para as piores."""
    if not natureza:
        return []
    excluir = {dominio(s) for s in excluir}
    candidatas = [(loja.get("naturezas", {}).get(natureza, 0), loja["acertos"], loja["ultimo"], site)
                  for site, loja in memoria["lojas"].items() if site not in excluir and loja.get("naturezas", {}).get(natureza, 0) > 0]
    candidatas.sort(reverse=True)
    return [(site, n) for n, _, _, site in candidatas[:limite]]


def resumo_naturezas(memoria: dict, por_natureza: int = 5) -> dict[str, list[tuple[str, int]]]:
    """{natureza: [(loja, nº de itens), ...]} para mostrar na tela."""
    todas = sorted({n for loja in memoria["lojas"].values() for n in loja.get("naturezas", {})})
    return {n: lojas_por_natureza(memoria, n, limite=por_natureza) for n in todas}


def registrar_uso_api(memoria: dict, api: str, consultas: int) -> int:
    """Soma as consultas feitas a uma API de busca ('serper' ou 'tavily') nesta pesquisa ao total do mês corrente. Devolve o total do mês."""
    mes = _hoje()[:7]
    uso = memoria.setdefault(api, {"mes": "", "n": 0})
    if uso.get("mes") != mes:
        uso["mes"], uso["n"] = mes, 0
    if consultas > 0:
        uso["n"] += consultas
        memoria["_mudou"] = True
    return uso["n"]


def padrao_busca(memoria: dict, site: str) -> str:
    """Endereço de busca interna da loja que já funcionou (ex.: '/busca?q={q}'), ou vazio."""
    return memoria["lojas"].get(dominio(site), {}).get("busca", "")


def registrar_busca_interna(memoria: dict, site: str, padrao: str) -> None:
    if padrao:
        loja = memoria["lojas"].setdefault(dominio(site), {"acertos": 0, "ultimo": "", "itens": []})
        if loja.get("busca") != padrao:
            loja["busca"] = padrao
            memoria["_mudou"] = True
    memoria.get("sem_busca", {}).pop(dominio(site), None)


def registrar_sem_busca(memoria: dict, site: str) -> None:
    """Nenhum endereço de busca interna funcionou nesta loja: não testa de novo por DIAS_SEM_BUSCA dias."""
    memoria.setdefault("sem_busca", {})[dominio(site)] = _hoje()
    memoria["_mudou"] = True


DIAS_SEM_BUSCA = 30


def busca_interna_descartada(memoria: dict, site: str) -> bool:
    data = memoria.get("sem_busca", {}).get(dominio(site))
    if not data:
        return False
    try:
        return (dt.date.today() - dt.date.fromisoformat(data)).days < DIAS_SEM_BUSCA
    except ValueError:
        return False


def pagina_guardada(memoria: dict, site: str, item_parecido: str) -> str:
    """Página da loja que já deu preço para esse item (vazio se não houver)."""
    return memoria["lojas"].get(site, {}).get("paginas", {}).get(item_parecido.strip().lower(), "")


# ---------- gravação (GitHub ou arquivo local) ----------

def _procurar(segredos, nome: str, caminho: str = ""):
    """Procura a chave no 1º nível dos Secrets e dentro das seções ([secao]), sem diferenciar maiúsculas.
    Devolve (valor, onde) ou ("", "")."""
    try:
        itens = list(segredos.items())
    except Exception:
        return "", ""
    for chave, valor in itens:
        if str(chave).strip().lower() == nome.lower() and isinstance(valor, str):
            return valor, (caminho + "." if caminho else "") + str(chave)
    for chave, valor in itens:
        if hasattr(valor, "items"):
            achado = _procurar(valor, nome, (caminho + "." if caminho else "") + str(chave))
            if achado[0]:
                return achado
    return "", ""


def _config(segredos) -> tuple[str, str]:
    token, _ = _procurar(segredos, "GITHUB_TOKEN")
    repositorio, _ = _procurar(segredos, "GITHUB_REPO")
    return str(token or "").strip().strip('"').strip(), str(repositorio or "").strip() or REPOSITORIO_PADRAO


def diagnostico_secrets(segredos) -> str:
    """Texto para a tela: onde a chave foi achada e quais nomes existem nos Secrets (nunca mostra valores)."""
    _, onde = _procurar(segredos, "GITHUB_TOKEN")
    nomes = []

    def listar(dados, caminho=""):
        try:
            for chave, valor in dados.items():
                nome = (caminho + "." if caminho else "") + str(chave)
                if hasattr(valor, "items"):
                    listar(valor, nome)
                else:
                    nomes.append(nome)
        except Exception:
            pass

    listar(segredos)
    if onde:
        return f"GITHUB_TOKEN encontrado em: {onde}."
    if not nomes:
        return "Nenhum Secret encontrado (os Secrets estão vazios ou não foram carregados; confira se o texto foi salvo e se o app reiniciou)."
    return ("GITHUB_TOKEN não encontrado. Nomes que existem nos Secrets: " + ", ".join(nomes[:30])
            + ". Coloque a linha GITHUB_TOKEN = \"...\" no início do texto dos Secrets, antes de qualquer [seção].")


def _cabecalhos(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def _normalizar(dados: dict) -> dict:
    memoria = vazia()
    if isinstance(dados, dict):
        memoria["lojas"] = dict(dados.get("lojas") or {})
        memoria["falhas"] = {k: _migrar_falha(v) for k, v in dict(dados.get("falhas") or {}).items()}
        memoria["frases"] = dict(dados.get("frases") or {})
        memoria["buscas"] = int(dados.get("buscas") or 0)
        memoria["sem_busca"] = dict(dados.get("sem_busca") or {})
        for api in ("serper", "tavily"):
            uso = dados.get(api) or {}
            memoria[api] = {"mes": str(uso.get("mes", "")), "n": int(uso.get("n", 0) or 0)}
    return memoria


def carregar(segredos=None, requisicoes=None) -> tuple[dict, str]:
    """(memória, onde ela está). Nunca falha: em erro devolve a memória vazia e explica no texto."""
    token, repositorio = _config(segredos or {})
    if token:
        import requests
        requisicoes = requisicoes or requests
        try:
            resp = requisicoes.get(f"{API}/repos/{repositorio}/contents/{ARQUIVO}", params={"ref": BRANCH}, headers=_cabecalhos(token), timeout=15)
            if resp.status_code == 404:
                memoria = vazia()
                memoria["_sha"] = None
                return memoria, f"GitHub ({repositorio}, branch {BRANCH}) — ainda vazia"
            if resp.status_code != 200:
                return vazia(), f"erro ao ler do GitHub (HTTP {resp.status_code}); usando memória vazia nesta pesquisa"
            corpo = resp.json()
            memoria = _normalizar(json.loads(base64.b64decode(corpo.get("content", "")).decode("utf-8") or "{}"))
            memoria["_sha"] = corpo.get("sha")
            return memoria, f"GitHub ({repositorio}, branch {BRANCH})"
        except Exception as erro:
            return vazia(), f"erro ao ler do GitHub ({type(erro).__name__}); usando memória vazia nesta pesquisa"
    try:
        with open(ARQUIVO_LOCAL, encoding="utf-8") as arquivo:
            return _normalizar(json.load(arquivo)), "local (sem GITHUB_TOKEN nos Secrets: some quando o app reinicia)"
    except (OSError, ValueError):
        return vazia(), "local (sem GITHUB_TOKEN nos Secrets: some quando o app reinicia)"


def _para_gravar(memoria: dict) -> dict:
    return {"versao": 1, "atualizado": dt.datetime.now().isoformat(timespec="seconds"),
            "lojas": memoria["lojas"], "falhas": memoria["falhas"], "frases": memoria.get("frases", {}), "buscas": memoria.get("buscas", 0), "sem_busca": memoria.get("sem_busca", {}), "serper": memoria.get("serper", {"mes": "", "n": 0}), "tavily": memoria.get("tavily", {"mes": "", "n": 0})}


def _juntar(local: dict, remota: dict) -> dict:
    """Outra pesquisa gravou antes: soma o que esta aprendeu à versão mais nova."""
    junta = _normalizar(remota)
    for site, loja in local["lojas"].items():
        atual = junta["lojas"].setdefault(site, {"acertos": 0, "ultimo": "", "itens": []})
        atual["acertos"] = max(atual["acertos"], loja["acertos"])
        atual["ultimo"] = max(atual["ultimo"], loja["ultimo"])
        atual["itens"] = list(dict.fromkeys(loja["itens"] + atual["itens"]))[:MAX_ITENS_POR_LOJA]
        metodos = atual.setdefault("metodos", {"navegador": 0, "texto": 0})
        for metodo, n in loja.get("metodos", {}).items():
            metodos[metodo] = max(metodos.get(metodo, 0), n)
        junta["falhas"].pop(site, None)
        atual.setdefault("paginas", {}).update({**atual.get("paginas", {}), **loja.get("paginas", {})})
        nat_atual = atual.setdefault("naturezas", {})
        for natureza, n in loja.get("naturezas", {}).items():
            nat_atual[natureza] = max(nat_atual.get(natureza, 0), n)
        if loja.get("busca"):
            atual["busca"] = loja["busca"]
    for site, data in local.get("sem_busca", {}).items():
        junta["sem_busca"][site] = max(junta["sem_busca"].get(site, ""), data)
    for site, falha in local["falhas"].items():
        if site not in junta["lojas"]:
            nova, atual = _migrar_falha(falha), _migrar_falha(junta["falhas"].get(site, _falha_nova()))
            junta["falhas"][site] = {"navegador": max(atual["navegador"], nova["navegador"]), "texto": max(atual["texto"], nova["texto"]),
                                     "ultimo": max(atual["ultimo"], nova["ultimo"])}
    for frase, dados in local.get("frases", {}).items():
        atual = junta["frases"].setdefault(frase, {"usos": 0.0, "acertos": 0.0, "ultimo": ""})
        atual["usos"] = max(atual.get("usos", 0), dados.get("usos", 0))
        atual["acertos"] = max(atual.get("acertos", 0), dados.get("acertos", 0))
        atual["ultimo"] = max(atual.get("ultimo", ""), dados.get("ultimo", ""))
    junta["buscas"] = max(junta.get("buscas", 0), local.get("buscas", 0))
    for api in ("serper", "tavily"):
        ls, js = local.get(api, {}), junta.get(api, {})
        if ls.get("mes") == js.get("mes"):
            junta[api] = {"mes": ls.get("mes", ""), "n": max(ls.get("n", 0), js.get("n", 0))}
        elif ls.get("mes", "") > js.get("mes", ""):
            junta[api] = dict(ls)
    return junta


def _criar_branch(requisicoes, repositorio: str, token: str) -> bool:
    cab = _cabecalhos(token)
    principal = requisicoes.get(f"{API}/repos/{repositorio}", headers=cab, timeout=15).json().get("default_branch", "main")
    ref = requisicoes.get(f"{API}/repos/{repositorio}/git/ref/heads/{principal}", headers=cab, timeout=15)
    if ref.status_code != 200:
        return False
    criado = requisicoes.post(f"{API}/repos/{repositorio}/git/refs", headers=cab, timeout=15,
                              json={"ref": f"refs/heads/{BRANCH}", "sha": ref.json()["object"]["sha"]})
    return criado.status_code in (201, 422)  # 422: já existe


def salvar(memoria: dict, segredos=None, requisicoes=None) -> str:
    """Grava se algo mudou. Devolve um texto curto para o log."""
    if not memoria.get("_mudou"):
        return "nada novo para guardar"
    token, repositorio = _config(segredos or {})
    if not token:
        try:
            with open(ARQUIVO_LOCAL, "w", encoding="utf-8") as arquivo:
                json.dump(_para_gravar(memoria), arquivo, ensure_ascii=False, indent=1)
            memoria["_mudou"] = False
            return "guardada localmente (configure GITHUB_TOKEN para não perder ao reiniciar)"
        except OSError as erro:
            return f"não foi possível guardar ({type(erro).__name__})"
    import requests
    requisicoes = requisicoes or requests
    url = f"{API}/repos/{repositorio}/contents/{ARQUIVO}"
    for tentativa in range(3):
        corpo = {
            "message": f"Memória de lojas do Web Scraping ({len(memoria['lojas'])} lojas, {len(memoria['falhas'])} sites com falha)",
            "content": base64.b64encode(json.dumps(_para_gravar(memoria), ensure_ascii=False, indent=1).encode("utf-8")).decode("ascii"),
            "branch": BRANCH,
        }
        if memoria.get("_sha"):
            corpo["sha"] = memoria["_sha"]
        try:
            resp = requisicoes.put(url, headers=_cabecalhos(token), json=corpo, timeout=20)
        except Exception as erro:
            return f"erro ao gravar no GitHub ({type(erro).__name__})"
        if resp.status_code in (200, 201):
            memoria["_sha"] = resp.json().get("content", {}).get("sha")
            memoria["_mudou"] = False
            return f"guardada no GitHub ({len(memoria['lojas'])} lojas, {len(memoria['falhas'])} sites com falha)"
        sem_branch = resp.status_code == 404 or (resp.status_code == 422 and "branch" in str(resp.text).lower())
        if sem_branch and tentativa == 0 and _criar_branch(requisicoes, repositorio, token):
            continue  # branch da memória ainda não existia
        if resp.status_code in (409, 422) and tentativa < 2:
            remota, _ = carregar(segredos, requisicoes)  # alguém gravou antes: junta e tenta de novo
            junta = _juntar(memoria, remota)
            memoria["lojas"], memoria["falhas"], memoria["_sha"] = junta["lojas"], junta["falhas"], remota.get("_sha")
            continue
        return f"erro ao gravar no GitHub (HTTP {resp.status_code}: {str(resp.text)[:80]})"
    return "erro ao gravar no GitHub (conflito repetido)"
