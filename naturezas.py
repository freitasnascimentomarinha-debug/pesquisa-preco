"""Natureza (ramo) de um item de compra, por palavras-chave. Sem IA e sem internet: rápido e gratuito.

Serve para a memória de lojas: a loja que deu preço de um item de uma natureza é tentada primeiro nos próximos itens da mesma natureza
(ex.: quem cotou "fita isolante" é boa candidata para "disjuntor 20A"). Item que não casa com nada fica sem natureza e segue o fluxo normal.
Cada palavra-chave pontua pelo número de palavras dela: "luva pvc" (2) vence "luva" (1), então o item cai na natureza mais específica."""
import re
import unicodedata

NATUREZAS: dict[str, list[str]] = {
    "elétrico": [
        "fita isolante", "isolante eletric", "disjuntor", "tomada", "interruptor", "lampada", "reator", "soquete", "plugue", "plug",
        "fio eletric", "fio flexivel", "fio rigido", "cabo flexivel", "cabo pp", "cabo eletric", "extensao", "filtro de linha", "benjamim",
        "luminaria", "refletor", "conector", "terminal eletric", "rele", "contator", "fusivel", "pilha", "bateria", "eletroduto", "quadro de distribuicao",
        "canaleta", "sensor de presenca", "fotocelula", "led", "eletric",
    ],
    "papelaria e escritório": [
        "papel a4", "papel sulfite", "resma", "caneta", "lapis", "borracha", "grampeador", "grampo", "clips", "envelope", "pasta", "caderno",
        "cola branca", "cola bastao", "tesoura", "marca texto", "marcador", "post it", "bloco adesivo", "etiqueta", "papel contact", "contact",
        "fita crepe", "fita adesiva", "durex", "corretivo", "regua", "perfurador", "prancheta", "agenda", "livro ata", "pincel atomico",
        "apontador", "elastico", "carimbo", "almofada carimbo", "arquivo morto", "papel cartao", "cartolina", "papel", "cola",
    ],
    "informática": [
        "mouse", "teclado", "monitor", "pendrive", "pen drive", "hd externo", "ssd", "memoria ram", "cabo hdmi", "cabo usb", "cabo de rede",
        "roteador", "switch", "notebook", "computador", "impressora", "toner", "cartucho", "webcam", "headset", "fone de ouvido", "nobreak",
        "estabilizador", "adaptador usb", "hub usb", "cartao de memoria", "mousepad", "patch cord", "conector rj45",
    ],
    "limpeza e higiene": [
        "detergente", "sabao", "sabonete", "desinfetante", "agua sanitaria", "alvejante", "vassoura", "rodo", "pano de chao", "flanela", "esponja",
        "saco de lixo", "saco para lixo", "lixeira", "papel higienico", "papel toalha", "alcool", "limpador", "multiuso", "cera", "lustra movel",
        "desengordurante", "pa de lixo", "balde", "luva de limpeza", "aromatizador", "dispenser", "toalha de papel", "esfregao", "mop",
    ],
    "ferramentas": [
        "chave de fenda", "chave philips", "chave combinada", "chave allen", "jogo de chaves", "alicate", "martelo", "furadeira", "parafusadeira",
        "serra", "serrote", "trena", "broca", "esmerilhadeira", "nivel", "estilete", "lima", "torques", "marreta", "talhadeira", "ferro de solda",
        "pistola de cola", "grampeador industrial", "arco de serra", "disco de corte", "chave inglesa", "soprador", "lixadeira",
    ],
    "fixadores": [
        "parafuso", "porca", "arruela", "prego", "rebite", "bucha", "abracadeira", "chumbador", "barra roscada", "pino", "contrapino", "grampo u",
    ],
    "hidráulica": [
        "cano", "tubo pvc", "joelho", "registro", "torneira", "valvula", "sifao", "mangueira", "conexao", "luva pvc", "veda rosca", "fita veda",
        "caixa d agua", "boia", "engate flexivel", "adaptador soldavel", "te pvc", "ralo", "chuveiro", "ducha", "reparo valvula",
    ],
    "tintas e pintura": [
        "tinta", "verniz", "rolo de pintura", "rolo de la", "pincel", "trincha", "massa corrida", "massa acrilica", "selador", "thinner",
        "aguarras", "lixa", "solvente", "spray", "esmalte sintetico", "fundo preparador", "bandeja de pintura", "fita para pintura",
    ],
    "EPI e segurança": [
        "luva", "capacete", "oculos de protecao", "oculos de seguranca", "protetor auricular", "abafador", "mascara", "respirador", "bota",
        "botina", "colete", "cinto de seguranca", "talabarte", "avental", "protetor facial", "creme protetor", "extintor", "cone de sinalizacao",
        "fita zebrada", "placa de sinalizacao",
    ],
    "construção": [
        "cimento", "areia", "argamassa", "tijolo", "bloco de concreto", "telha", "cal", "rejunte", "piso", "azulejo", "porcelanato", "gesso",
        "brita", "vergalhao", "impermeabilizante", "manta asfaltica", "drywall", "silicone", "espuma expansiva",
    ],
    "copa e cozinha": [
        "copo descartavel", "cafe", "acucar", "adocante", "guardanapo", "prato descartavel", "talher descartavel", "garrafa termica",
        "filtro de cafe", "cha", "leite", "agua mineral", "galao", "bandeja", "pote", "papel aluminio", "filme pvc", "mexedor",
    ],
    "eletrodomésticos": [
        "frigobar", "geladeira", "refrigerador", "freezer", "micro ondas", "microondas", "bebedouro", "purificador de agua", "ventilador",
        "ar condicionado", "climatizador", "cafeteira", "chaleira eletrica", "liquidificador", "batedeira", "fogao", "forno eletrico",
        "televisor", "smart tv", "aspirador de po", "ferro de passar", "secador de cabelo", "sanduicheira", "torradeira", "fritadeira",
    ],
    "gêneros alimentícios": [
        "arroz", "feijao", "macarrao", "farinha de trigo", "farinha de mandioca", "fuba", "oleo de soja", "azeite", "sal refinado", "sal grosso",
        "acucar cristal", "acucar refinado", "leite em po", "leite integral", "cafe em po", "cafe torrado", "achocolatado", "biscoito", "bolacha",
        "molho de tomate", "extrato de tomate", "sardinha", "atum", "milho verde", "ervilha", "vinagre", "tempero", "margarina", "manteiga",
        "carne", "frango", "ovo", "queijo", "presunto", "pao", "farinha", "lentilha", "aveia", "flocos de milho", "creme de leite", "leite condensado",
    ],
    "automotivo e lubrificantes": [
        "oleo lubrificante", "oleo de motor", "oleo", "graxa", "lubrificante", "aditivo", "filtro de oleo", "filtro de ar", "desengripante",
        "fluido de freio", "arla", "palheta", "pneu", "bateria automotiva", "wd 40", "wd40",
    ],
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " " + " ".join(re.findall(r"[a-z0-9]+", texto)) + " "


def _casa(texto_normalizado: str, chave: str) -> bool:
    """A palavra-chave aparece no começo de palavra(s) do item ('isolant' casa 'isolante'; 'led' não casa 'soldagem')."""
    return (" " + chave) in texto_normalizado


def pontuar(item: str) -> dict[str, int]:
    texto = _normalizar(item)
    pontos: dict[str, int] = {}
    for natureza, chaves in NATUREZAS.items():
        total = sum(len(chave.split()) for chave in chaves if _casa(texto, chave))
        if total:
            pontos[natureza] = total
    return pontos


def classificar(item: str) -> str:
    """Natureza mais provável do item, ou '' se nenhuma palavra-chave casar. Empate: a natureza listada primeiro."""
    pontos = pontuar(item)
    if not pontos:
        return ""
    melhor = max(pontos.values())
    return next(n for n in NATUREZAS if pontos.get(n) == melhor)
