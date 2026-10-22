"""Gera a narração (MP3) das vídeo-aulas da página "Aprendendo a usar" com o Piper (voz pt-BR "faber", código aberto, offline).

Uso (na raiz do projeto), depois de editar os textos de uma aula:
    pip install piper-tts
    python scripts/gerar_audios_tutoriais.py            # todas as aulas
    python scripts/gerar_audios_tutoriais.py ipca web   # só algumas (nomes em AULAS)

A voz "faber" (rhasspy/piper-voices) é licenciada em CC0 (domínio público).
Requer o ffmpeg e o node no PATH. O modelo de voz (~63 MB) é baixado uma vez para ~/.cache/piper e NÃO vai para o repositório.
Os MP3 ficam em audio_tutoriais/<aula>/NN.mp3 e são embutidos no player por tutorial_player.montar_player.
Só regera o trecho cujo texto mudou (hash em audio_tutoriais/<aula>/manifest.json); use --forcar para regerar tudo.
"""

from __future__ import annotations

import hashlib
import html
import importlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

VOZ = "pt_BR-faber-medium"
URL_VOZ = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/" + VOZ
CACHE = Path.home() / ".cache" / "piper"

AULAS = {  # nome do áudio -> módulo da aula
    "cotacao": "tutorial_cotacao",
    "catmat": "tutorial_catmat",
    "cotacao_direta": "tutorial_cotacao_direta",
    "cotacao_rapida": "tutorial_cotacao_rapida",
    "adesoes": "tutorial_adesoes",
    "notas_fiscais": "tutorial_notas_fiscais",
    "fornecedores": "tutorial_fornecedores",
    "web_scraping": "tutorial_web_scraping",
    "ipca": "tutorial_ipca",
    "detalhes_compra": "tutorial_detalhes_compra",
    "consulta_cnpj": "tutorial_consulta_cnpj",
}

# Pronúncias: siglas viram letras separadas; termos que o sintetizador lê mal ganham grafia fonética.
SUBSTITUICOES = [
    (r"IN SEGES/ME nº 65/2021", "Instrução Normativa Seges ME número 65 de 2021"),
    (r"Lei nº 14\.133/2021", "Lei número 14.133 de 2021"),
    (r"Compras\.gov\.br", "Compras ponto gov ponto bê érre"),
    (r"Compras\.gov", "Compras ponto gov"),
    (r"\s*\(NF-e\)", ""),
    (r"NF-e", "nota fiscal eletrônica"),
    (r"\(“- 50”\)", "(por exemplo, hífen cinquenta)"),
    (r"\(“10 notebook…”\)", "(por exemplo, dez notebooks)"),
    (r"\(“; 30 un”\)", "(por exemplo, ponto e vírgula, trinta unidades)"),
    (r"Item\(ns\)", "Itens"),
    (r"\b([aA])\s+%", r"\1 porcentagem"),
    (r"\bCATMAT/CATSERV\b", "Catmat e Catserv"),
    (r"\bCATMAT\b", "Catmat"),
    (r"\bCATSERV\b", "Catserv"),
    (r"\bCNAE\b", "Cê náe"),
    (r"\bCEIS\b", "Céis"),
    (r"\bCNEP\b", "Cenépe"),
    (r"\bCEPIM\b", "Cepim"),
    (r"\bSICAF\b", "Sicáfi"),
    (r"\bMEI\b", "Mêi"),
    (r"ComprasNet", "Compras Net"),
    (r"ComprasGov", "Compras gov"),
    (r"\bIPCA\b", "Ípeca"),
    (r"\bDANFE\b", "Danfe"),
    (r"\bCEP\b", "cép"),
    (r"\bExcel\b", "Équisel"),
    (r"\bWord\b", "Uórd"),
    (r"\bJSON\b", "Jêison"),
    (r"\bPlaywright\b", "Pleirait"),
    (r"\be-mails?\b", "imeiu"),
    (r"\bA4\b", "A quatro"),
    (r"g/m²", "gramas por metro quadrado"),
    (r"\bPDF/Excel\b", "PDF e Équisel"),
    (r"\bCATMAT\b", "Catmat"),
    (r"\bRJ\b", "Rio de Janeiro"),
    (r"\bSP\b", "São Paulo"),
    (r"\bMG\b", "Minas Gerais"),
    (r"\bDF\b", "Distrito Federal"),
    (r"\bUFs?\b", "U F"),
]
SIGLAS = ["CNPJ", "UASG", "PDM", "IQR", "PDF", "HTML", "XML", "CSV", "API", "OM", "CV", "TCU", "PNCP", "BCB", "IBGE", "IA", "BRL", "ID"]


def numero_por_extenso_simples(m: re.Match) -> str:
    reais, centavos = m.group(1).replace(".", ""), m.group(2)
    return f"{reais} reais" if centavos == "00" else f"{reais} reais e {int(centavos)} centavos"


def normalizar_fala(texto: str) -> str:
    """HTML do passo -> texto limpo para o sintetizador."""
    t = re.sub(r"<[^>]+>", " ", texto)
    t = html.unescape(t)
    t = re.sub(r"R\$\s*([\d.]+),(\d{2})", numero_por_extenso_simples, t)
    for padrao, troca in SUBSTITUICOES:
        t = re.sub(padrao, troca, t)
    for sigla in SIGLAS:
        t = re.sub(rf"\b{sigla}\b", " ".join(sigla), t)
    t = re.sub(r"(\d+(?:,\d+)?)\s*%", r"\1 por cento", t)
    t = t.replace("nº", "número").replace("×", " ou ").replace("→", " para ")
    t = re.sub(r"ex\.:", "por exemplo,", t, flags=re.I)
    t = re.sub(r"(\d)\)", r"\1,", t)
    t = re.sub(r"\bn/(\d+)", r"n de \1", t)
    t = re.sub(r"[“”‘’\"'«»]", "", t)
    t = re.sub(r"[—–]", ", ", t)
    t = re.sub(r"[^\w\s,.;:!?()%/°ºªáàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ-]", " ", t)  # emojis e símbolos
    t = t.replace("/", " ou ")
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def falas_da_aula(modulo: str) -> list[str]:
    """Texto falado de cada passo (título + corpo), lido do JS da aula com o node."""
    mod = importlib.import_module(modulo)
    js = "const window={};\n" + mod._STEPS_JS + "\nconsole.log(JSON.stringify(window.__STEPS__.map(s=>({t:s.t,b:s.b}))));"
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as arq:
        arq.write(js)
    try:
        saida = subprocess.run(["node", arq.name], capture_output=True, text=True, check=True).stdout
    finally:
        Path(arq.name).unlink(missing_ok=True)
    return [normalizar_fala(f"{p['t']}. {p['b']}") for p in json.loads(saida)]


def baixar_voz() -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    for ext in (".onnx", ".onnx.json"):
        destino = CACHE / (VOZ + ext)
        if destino.exists():
            continue
        for tentativa in range(1, 5):  # a conexão às vezes cai no meio do arquivo de 63 MB
            print(f"baixando {destino.name} (tentativa {tentativa}) ...")
            parcial = destino.with_suffix(destino.suffix + ".part")
            try:
                with urllib.request.urlopen(URL_VOZ + ext, timeout=120) as resposta, open(parcial, "wb") as saida:
                    esperado = int(resposta.headers.get("Content-Length") or 0)
                    shutil.copyfileobj(resposta, saida)
                if esperado and parcial.stat().st_size != esperado:
                    raise OSError("download incompleto")
                parcial.rename(destino)
                break
            except OSError as erro:
                print("  falhou:", erro)
                parcial.unlink(missing_ok=True)
        else:
            sys.exit(f"não consegui baixar {destino.name}")
    return CACHE / (VOZ + ".onnx")


def main(argv: list[str]) -> None:
    forcar = "--forcar" in argv
    nomes = [a for a in argv if not a.startswith("--")] or list(AULAS)
    if not shutil.which("ffmpeg") or not shutil.which("node"):
        sys.exit("ffmpeg e node precisam estar no PATH.")
    from piper import PiperVoice

    voz = PiperVoice.load(str(baixar_voz()))
    for nome in nomes:
        falas = falas_da_aula(AULAS[nome])
        pasta = RAIZ / "audio_tutoriais" / nome
        pasta.mkdir(parents=True, exist_ok=True)
        manifesto_arq = pasta / "manifest.json"
        manifesto = json.loads(manifesto_arq.read_text(encoding="utf-8")) if manifesto_arq.exists() else {}
        novo = {}
        for i, fala in enumerate(falas, start=1):
            mp3 = pasta / f"{i:02d}.mp3"
            selo = hashlib.sha1((VOZ + fala).encode("utf-8")).hexdigest()
            novo[f"{i:02d}"] = selo
            if not forcar and mp3.exists() and manifesto.get(f"{i:02d}") == selo:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                wav = Path(tmp) / "fala.wav"
                with wave.open(str(wav), "wb") as w:
                    voz.synthesize_wav(fala, w)
                subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "22050", "-b:a", "32k", str(mp3)], check=True)
            print(f"{nome} {i:02d}: {len(fala)} caracteres, {mp3.stat().st_size // 1024} KB")
        for antigo in pasta.glob("*.mp3"):  # aula ficou com menos passos
            if antigo.stem not in novo:
                antigo.unlink()
        manifesto_arq.write_text(json.dumps(novo, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
