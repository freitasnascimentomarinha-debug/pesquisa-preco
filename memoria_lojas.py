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
    return {"versao": 1, "lojas": {}, "falhas": {}}


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
            "lojas": memoria["lojas"], "falhas": memoria["falhas"]}


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
    for site, falha in local["falhas"].items():
        if site not in junta["lojas"]:
            nova, atual = _migrar_falha(falha), _migrar_falha(junta["falhas"].get(site, _falha_nova()))
            junta["falhas"][site] = {"navegador": max(atual["navegador"], nova["navegador"]), "texto": max(atual["texto"], nova["texto"]),
                                     "ultimo": max(atual["ultimo"], nova["ultimo"])}
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
