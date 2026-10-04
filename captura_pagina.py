"""Print real (screenshot) das páginas dos preços, com data/hora e endereço no rodapé.

Usa o Chromium pelo Playwright, uma página por vez (o servidor gratuito do Streamlit tem pouca memória).
Na nuvem o Chromium vem do arquivo packages.txt; no computador do usuário, do `playwright install chromium`.
Sem dependência do Streamlit.
"""

from __future__ import annotations

import io
import os
import re
from datetime import datetime

LARGURA, ALTURA = 1366, 900
TEMPO_NAVEGACAO_S = 25
ALTURA_RODAPE = 34
CAMINHOS_CHROMIUM = ("/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable")
ARGUMENTOS_NAVEGADOR = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-extensions", "--mute-audio"]
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

SELETORES_FECHAR = (
    'button:has-text("Aceitar")', 'button:has-text("Aceito")', 'button:has-text("Concordo")', 'button:has-text("Entendi")',
    'button:has-text("Continuar")', 'button:has-text("Accept")', '[class*="cookie"] button', '[id*="cookie"] button',
    '[class*="lgpd"] button', '[class*="consent"] button', '[aria-label="Fechar"]', '[aria-label="Close"]',
    '[class*="modal"] [class*="close"]', '[class*="popup"] [class*="close"]', 'button.close',
)


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


def _preparar_pagina(page, preco: float | None) -> None:
    """Fecha avisos de cookies/popups e leva a tela até o preço, marcando-o com um contorno."""
    for seletor in SELETORES_FECHAR:
        try:
            alvo = page.locator(seletor).first
            if alvo.is_visible(timeout=200):
                alvo.click(timeout=800)
                page.wait_for_timeout(200)
        except Exception:
            pass
    for formato in _formatos_preco(preco):
        try:
            elemento = page.locator(f"text=/{re.escape(formato)}/").first
            if elemento.count() and elemento.is_visible(timeout=500):
                elemento.scroll_into_view_if_needed(timeout=1500)
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
            finally:
                navegador.close()
            if progresso:
                progresso(len(unicas), len(unicas), "")
    except Exception as erro:
        for url in unicas:
            resultados.setdefault(url, {"imagem": None, "capturado_em": "", "erro": f"navegador não iniciou ({type(erro).__name__})"})
    return resultados
