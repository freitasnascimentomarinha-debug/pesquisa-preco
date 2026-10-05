"""Print real (screenshot) das páginas dos preços, com data/hora e endereço no rodapé.

Usa o Chromium pelo Playwright, uma página por vez (o servidor gratuito do Streamlit tem pouca memória).
Na nuvem o Chromium vem do arquivo packages.txt; no computador do usuário, do `playwright install chromium`.
Sem dependência do Streamlit.
"""

from __future__ import annotations

import io
import os
import re
import time
from datetime import datetime

LARGURA, ALTURA = 1366, 900
TEMPO_NAVEGACAO_S = 25
ALTURA_RODAPE = 34
CAMINHOS_CHROMIUM = ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable")
ARGUMENTOS_NAVEGADOR = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-extensions", "--mute-audio"]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# Botões de aviso/popup que podem ser clicados (texto inteiro do botão, sem diferenciar maiúsculas/acentos)
TEXTOS_FECHAR = re.compile(
    r"^\s*(aceitar( todos)?( os)?( cookies)?|aceito|aceitar e fechar|concordo|concordar|entendi|ok|fechar|agora n[aã]o|n[aã]o,? obrigad[oa]|"
    r"n[aã]o,? agora|dispensar|depois|mais tarde|recusar|rejeitar|continuar e fechar|prosseguir|pular|skip|close|got it|accept( all)?|no,? thanks|x|×|✕)\s*$",
    re.IGNORECASE,
)
SELETORES_FECHAR = (
    '[class*="cookie"] button', '[id*="cookie"] button', '[class*="lgpd"] button', '[id*="lgpd"] button', '[class*="consent"] button',
    '[aria-label="Fechar"]', '[aria-label="fechar"]', '[aria-label="Close"]', '[aria-label="close"]', 'button[title="Fechar"]', 'button[title="Close"]',
    '[class*="modal"] [class*="close"]', '[class*="popup"] [class*="close"]', '[class*="overlay"] [class*="close"]', '[class*="newsletter"] [class*="close"]',
    'button.close', '.modal .close', '[data-dismiss="modal"]', '[class*="CloseButton"]', '[class*="closeButton"]', '[class*="icon-close"]',
)
# Esconde, pelo JavaScript da própria página, o que ainda cobre o conteúdo: diálogos, avisos fixos e camadas sobrepostas (menos o cabeçalho do site)
JS_LIMPAR_SOBREPOSICOES = """
() => {
  const largura = window.innerWidth, altura = window.innerHeight;
  const ehCabecalho = (e, r) => /^(HEADER|NAV)$/.test(e.tagName) || e.closest('header, nav') || (r.top <= 8 && r.height < 190 && r.width > largura * 0.6);
  const palavras = /(cookie|lgpd|consent|gdpr|modal|popup|pop-up|overlay|newsletter|lightbox|dialog|banner-?promo|region|regiao|geoloc|cep|app-?banner|chat-?widget)/i;
  let removidos = 0;
  document.querySelectorAll('body *').forEach(e => {
    const css = getComputedStyle(e);
    if (!['fixed', 'sticky', 'absolute'].includes(css.position) || css.display === 'none' || css.visibility === 'hidden') return;
    const r = e.getBoundingClientRect();
    if (r.width < 40 || r.height < 24 || r.bottom < 0 || r.top > altura) return;
    if (ehCabecalho(e, r)) return;
    const id = (e.id || '') + ' ' + (typeof e.className === 'string' ? e.className : '');
    const dialogo = e.matches('[role=dialog], [role=alertdialog], [aria-modal=true], dialog');
    const z = parseInt(css.zIndex) || 0;
    const cobre = r.width >= largura * 0.9 && r.height >= altura * 0.5;           // camada sobre a tela inteira
    const barra = css.position === 'fixed' && (r.bottom >= altura - 4 || r.top <= 4) && r.width >= largura * 0.6 && r.height < altura * 0.4 && z >= 10; // faixa fixa
    const flutuante = z >= 100 && palavras.test(id);
    if (dialogo || cobre || barra || flutuante || (css.position !== 'sticky' && z >= 1000 && palavras.test(id))) { e.style.setProperty('display', 'none', 'important'); removidos++; }
  });
  document.documentElement.style.setProperty('overflow', 'auto', 'important');
  document.body.style.setProperty('overflow', 'auto', 'important');
  return removidos;
}
"""


def caminho_chromium() -> str | None:
    """Chromium do sistema (packages.txt), se existir; senão None (o Playwright usa o dele)."""
    for caminho in (os.environ.get("CHROMIUM_PATH", ""),) + CAMINHOS_CHROMIUM:
        if caminho and os.path.exists(caminho):
            return caminho
    return None


def disponivel() -> tuple[bool, str]:
    """(pode tirar print?, motivo). Confere o pacote Playwright e se há um Chromium para ele usar."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "pacote playwright não instalado"
    if caminho_chromium():
        return True, f"Chromium do sistema ({caminho_chromium()})"
    try:
        with sync_playwright() as p:
            if os.path.exists(p.chromium.executable_path):
                return True, "Chromium do Playwright"
    except Exception as erro:
        return False, f"Playwright não iniciou ({type(erro).__name__})"
    return False, "Chromium não está instalado neste servidor (na nuvem, vem do arquivo packages.txt)"


def _formatos_preco(preco: float | None) -> list[str]:
    """'29,90' e '1.299,90': como o preço costuma aparecer escrito na página."""
    if not preco:
        return []
    inteiro, centavos = f"{preco:,.2f}".split(".")
    return [f"{inteiro.replace(',', '.')},{centavos}"]


def _rodape(png: bytes, url: str, capturado_em: str, preco: float | None) -> bytes:
    """Cola uma faixa no rodapé com data/hora, endereço e preço, e devolve JPEG (menor no PDF)."""
    from PIL import Image, ImageDraw, ImageFont

    imagem = Image.open(io.BytesIO(png)).convert("RGB")
    tela = Image.new("RGB", (imagem.width, imagem.height + ALTURA_RODAPE), (0, 26, 77))
    tela.paste(imagem, (0, 0))
    desenho = ImageDraw.Draw(tela)
    try:
        fonte = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        fonte = ImageFont.load_default()
    texto = f"Captura em {capturado_em}  |  {url}"
    if preco:
        texto += f"  |  preço usado: R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    while desenho.textlength(texto, font=fonte) > imagem.width - 20 and len(texto) > 20:
        texto = texto[:-4] + "..."
    desenho.text((10, imagem.height + 8), texto, fill=(255, 255, 255), font=fonte)
    saida = io.BytesIO()
    tela.save(saida, "JPEG", quality=82, optimize=True)
    return saida.getvalue()


def _fechar_avisos(page) -> None:
    """Fecha avisos de cookies, escolha de região, newsletter e popups: clica nos botões de dispensar, tecla Esc e, por fim, esconde o que ainda cobre a tela."""
    for _ in range(2):  # alguns sites abrem um segundo aviso depois de fechar o primeiro
        for alvo in (page.get_by_role("button", name=TEXTOS_FECHAR), page.get_by_role("link", name=TEXTOS_FECHAR)):
            try:
                for i in range(min(alvo.count(), 3)):
                    botao = alvo.nth(i)
                    if botao.is_visible(timeout=200):
                        botao.click(timeout=800)
                        page.wait_for_timeout(250)
            except Exception:
                pass
        for seletor in SELETORES_FECHAR:
            try:
                alvo = page.locator(seletor).first
                if alvo.is_visible(timeout=150):
                    alvo.click(timeout=700)
                    page.wait_for_timeout(200)
            except Exception:
                pass
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        page.wait_for_timeout(300)
    try:
        page.evaluate(JS_LIMPAR_SOBREPOSICOES)
    except Exception:
        pass


def _preparar_pagina(page, preco: float | None) -> None:
    """Fecha os avisos e leva a tela até o preço, marcando-o com um contorno."""
    _fechar_avisos(page)
    for formato in _formatos_preco(preco):
        try:
            elemento = page.locator(f"text=/{re.escape(formato)}/").first
            if elemento.count() and elemento.is_visible(timeout=500):
                elemento.scroll_into_view_if_needed(timeout=1500)
                page.evaluate("window.scrollBy(0, -120)")  # deixa o preço um pouco abaixo do topo, longe do cabeçalho fixo
                elemento.evaluate("e => { e.style.outline = '3px solid #d4af37'; e.style.outlineOffset = '3px'; }")
                page.wait_for_timeout(300)
                return
        except Exception:
            continue


def capturar_prints(paginas: list[dict], progresso=None) -> dict[str, dict]:
    """Tira o print de cada página, uma por vez. `paginas`: [{"url": ..., "preco": ...}].
    Devolve {url: {"imagem": JPEG ou None, "capturado_em": "dd/mm/aaaa hh:mm:ss", "erro": texto}}. Nunca levanta erro."""
    resultados: dict[str, dict] = {}
    unicas = list(dict.fromkeys(p["url"] for p in paginas if str(p.get("url", "")).startswith(("http://", "https://"))))
    preco_de = {p["url"]: p.get("preco") for p in paginas}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {url: {"imagem": None, "capturado_em": "", "erro": "pacote playwright não instalado"} for url in unicas}

    try:
        with sync_playwright() as p:
            opcoes = {"headless": True, "args": ARGUMENTOS_NAVEGADOR}
            if caminho_chromium():
                opcoes["executable_path"] = caminho_chromium()
            navegador = p.chromium.launch(**opcoes)
            try:
                for numero, url in enumerate(unicas, start=1):
                    if progresso:
                        progresso(numero - 1, len(unicas), url)
                    contexto = navegador.new_context(viewport={"width": LARGURA, "height": ALTURA}, locale="pt-BR",
                                                     timezone_id="America/Sao_Paulo", user_agent=USER_AGENT)
                    try:
                        page = contexto.new_page()
                        page.set_default_timeout(TEMPO_NAVEGACAO_S * 1000)
                        resposta = page.goto(url, wait_until="domcontentloaded", timeout=TEMPO_NAVEGACAO_S * 1000)
                        try:
                            page.wait_for_load_state("networkidle", timeout=6000)
                        except Exception:
                            pass  # sites com rastreadores nunca "assentam"; segue com o que carregou
                        if resposta is not None and resposta.status >= 400:
                            motivo = "o site bloqueou o acesso" if resposta.status in (401, 403, 429) else "página indisponível"
                            resultados[url] = {"imagem": None, "capturado_em": "", "erro": f"{motivo} (HTTP {resposta.status})"}
                            continue
                        _preparar_pagina(page, preco_de.get(url))
                        agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        png = page.screenshot(type="png", full_page=False)
                        resultados[url] = {"imagem": _rodape(png, url, agora, preco_de.get(url)), "capturado_em": agora, "erro": ""}
                    except Exception as erro:
                        resultados[url] = {"imagem": None, "capturado_em": "", "erro": f"{type(erro).__name__}: {str(erro).splitlines()[0][:100]}"}
                    finally:
                        contexto.close()  # libera a memória antes da próxima página
                        if progresso:
                            progresso(numero, len(unicas), url, resultados.get(url))
            finally:
                navegador.close()
            if progresso:
                progresso(len(unicas), len(unicas), "")
    except Exception as erro:
        for url in unicas:
            resultados.setdefault(url, {"imagem": None, "capturado_em": "", "erro": f"navegador não iniciou ({type(erro).__name__})"})
    return resultados


class LeitorNavegador:
    """Lê páginas que a leitura simples não consegue (preço montado por JavaScript, bloqueio de robô simples).

    Um navegador por pesquisa, uma página de cada vez. Limites: `tempo_max_pagina_s` por página (se ela travar, é abandonada e o navegador
    é reiniciado para a próxima), `tempo_max_s` desde a criação (trava de segurança da pesquisa inteira) e `limite` de páginas.
    Uso: `with LeitorNavegador(tempo_max_pagina_s=120) as leitor: leitor.ler(url)`; o navegador é sempre fechado ao sair."""

    def __init__(self, limite: int = 500, tempo_max_s: float = 3600, tempo_max_pagina_s: float = 120) -> None:
        self.limite = limite
        self.tempo_max_s = tempo_max_s
        self.tempo_max_pagina_s = tempo_max_pagina_s
        self._prazo = 0.0
        self._inicio = time.monotonic()
        self.usadas = 0
        self._playwright = None
        self._navegador = None
        self._contexto = None
        self._page = None
        self.falha_ao_iniciar = ""

    def __enter__(self) -> "LeitorNavegador":
        return self

    def __exit__(self, *args) -> None:
        self.fechar()

    @property
    def disponivel(self) -> bool:
        return self.usadas < self.limite and not self.falha_ao_iniciar and time.monotonic() - self._inicio < self.tempo_max_s

    @property
    def motivo_indisponivel(self) -> str:
        if self.falha_ao_iniciar:
            return self.falha_ao_iniciar
        if time.monotonic() - self._inicio >= self.tempo_max_s:
            return f"tempo máximo do navegador atingido ({self.tempo_max_s / 60:.0f} min)"
        return "limite de páginas lidas pelo navegador atingido"

    def _iniciar(self) -> bool:
        if self._navegador:
            return True
        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            opcoes = {"headless": True, "args": ARGUMENTOS_NAVEGADOR}
            if caminho_chromium():
                opcoes["executable_path"] = caminho_chromium()
            self._navegador = self._playwright.chromium.launch(**opcoes)
            return True
        except Exception as erro:
            self.falha_ao_iniciar = f"navegador não iniciou ({type(erro).__name__})"
            self.fechar()
            return False

    def _restante(self) -> float:
        """Segundos que ainda sobram para a página atual; levanta TimeoutError se acabaram."""
        sobra = self._prazo - time.monotonic()
        if sobra <= 0:
            raise TimeoutError(f"a página passou de {self.tempo_max_pagina_s / 60:g} min no navegador")
        return sobra

    def _reiniciar(self) -> None:
        """Fecha o navegador inteiro (página travada): a próxima leitura abre um novo."""
        self.fechar()
        self.falha_ao_iniciar = ""

    def ler(self, url: str) -> dict:
        """{"html": texto ou "", "status": HTTP ou 0, "erro": texto}. Nunca levanta erro.
        Em caso de sucesso a página fica aberta para `capturar` (print) e é fechada por `liberar` (ou pela próxima leitura).
        Cada página tem `tempo_max_pagina_s`: se estourar, a página é abandonada e o navegador reiniciado."""
        self.liberar()
        if not self.disponivel or not str(url).startswith(("http://", "https://")):
            return {"html": "", "status": 0, "erro": self.motivo_indisponivel}
        if not self._iniciar():
            return {"html": "", "status": 0, "erro": self.falha_ao_iniciar}
        self.usadas += 1
        self._prazo = time.monotonic() + self.tempo_max_pagina_s
        try:
            self._contexto = self._navegador.new_context(viewport={"width": LARGURA, "height": ALTURA}, locale="pt-BR",
                                                         timezone_id="America/Sao_Paulo", user_agent=USER_AGENT)
            self._page = self._contexto.new_page()
            espera = min(TEMPO_NAVEGACAO_S, self._restante())  # nenhuma operação passa do que resta para a página
            self._page.set_default_timeout(espera * 1000)
            resposta = self._page.goto(url, wait_until="domcontentloaded", timeout=espera * 1000)
            try:
                self._page.wait_for_load_state("networkidle", timeout=min(6, self._restante()) * 1000)
            except TimeoutError:
                raise
            except Exception:
                pass
            status = resposta.status if resposta is not None else 0
            if status >= 400:
                self.liberar()
                return {"html": "", "status": status, "erro": f"HTTP {status}"}
            self._restante()
            _fechar_avisos(self._page)
            for _ in range(3):  # rola a página para carregar o que aparece aos poucos (produtos, preços)
                self._restante()
                self._page.mouse.wheel(0, ALTURA)
                self._page.wait_for_timeout(500)
            self._restante()
            self._page.evaluate("window.scrollTo(0, 0)")
            return {"html": self._page.content(), "status": status, "erro": ""}
        except Exception as erro:
            estourou = type(erro).__name__ == "TimeoutError" or "Target" in type(erro).__name__ or "closed" in str(erro).lower()
            self.liberar()
            if estourou and time.monotonic() >= self._prazo:
                self._reiniciar()  # página travada: não reaproveita este navegador
            return {"html": "", "status": 0, "erro": f"{type(erro).__name__}: {str(erro).splitlines()[0][:100]}"}

    def capturar(self, url: str, preco: float | None) -> dict:
        """Print da página que acabou de ser lida (ainda aberta): leva a tela até o preço, destaca o valor e põe data/hora no rodapé.
        {"imagem": JPEG ou None, "capturado_em": ..., "erro": ...}. Nunca levanta erro."""
        if self._page is None:
            return {"imagem": None, "capturado_em": "", "erro": "página já fechada"}
        try:
            self._restante()  # o print faz parte do tempo da página
            self._page.set_default_timeout(min(TEMPO_NAVEGACAO_S, self._restante()) * 1000)
            _preparar_pagina(self._page, preco)
            self._restante()
            agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            png = self._page.screenshot(type="png", full_page=False)
            return {"imagem": _rodape(png, url, agora, preco), "capturado_em": agora, "erro": ""}
        except Exception as erro:
            return {"imagem": None, "capturado_em": "", "erro": f"{type(erro).__name__}: {str(erro).splitlines()[0][:100]}"}

    def liberar(self) -> None:
        """Fecha a página aberta (libera a memória antes da próxima)."""
        for objeto in (self._contexto,):
            try:
                if objeto is not None:
                    objeto.close()
            except Exception:
                pass
        self._contexto = None
        self._page = None

    def fechar(self) -> None:
        self.liberar()
        for objeto, metodo in ((self._navegador, "close"), (self._playwright, "stop")):
            try:
                if objeto is not None:
                    getattr(objeto, metodo)()
            except Exception:
                pass
        self._navegador = None
        self._playwright = None
