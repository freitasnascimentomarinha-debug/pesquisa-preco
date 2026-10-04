"""Catálogo de lojas (nome, site e ramos) e classificação de itens por ramo, para a pesquisa nas lojas preferidas.

Sem dependência do Streamlit nem de rede: o site de uma loja fora do catálogo é descoberto pela página Web Scraping.
"""

from __future__ import annotations

import re
import unicodedata

RAMOS = {
    "expediente": "Expediente e papelaria",
    "informatica": "Informática",
    "eletronicos": "Eletrônicos e eletrodomésticos",
    "construcao": "Construção",
    "tintas": "Tintas e pintura",
    "eletrica": "Material elétrico",
    "hidraulica": "Hidráulica",
    "ferramentas": "Ferramentas e máquinas",
    "epi": "EPI e segurança",
    "limpeza": "Limpeza e higiene",
    "copa": "Copa, cozinha e descartáveis",
    "alimentos": "Alimentos e bebidas",
    "moveis": "Móveis",
    "saude": "Saúde e farmácia",
    "automotivo": "Automotivo",
    "jardinagem": "Jardinagem",
    "esporte": "Esporte",
}

# Palavras-chave sem acento. Expressões com espaço valem mais (3) que palavras soltas (1); o item fica no(s) ramo(s) de maior pontuação.
PALAVRAS_RAMO = {
    "expediente": [
        "caneta", "lapis", "lapiseira", "borracha", "papel a4", "papel sulfite", "papel oficio", "resma", "sulfite", "grampeador", "grampo",
        "clips", "clipe", "envelope", "pasta", "fichario", "caderno", "bloco de notas", "bloco adesivo", "post it", "etiqueta", "cola",
        "corretivo", "marca texto", "marcador", "apontador", "regua", "tesoura", "perfurador", "carimbo", "almofada para carimbo",
        "tinta para carimbo", "livro ata", "livro de protocolo", "agenda", "prancheta", "arquivo morto", "caixa arquivo", "elastico",
        "percevejo", "papel contact", "contact", "durex", "fita adesiva", "fita crepe", "pincel atomico", "quadro branco", "apagador",
        "papel cartao", "cartolina", "papel kraft", "papel fotografico", "porta canetas", "calculadora", "extrator de grampo",
        "tinta guache", "tinta aquarela", "tinta artistica",
    ],
    "informatica": [
        "mouse", "teclado", "monitor", "notebook", "computador", "pendrive", "pen drive", "hd externo", "ssd", "memoria ram", "cabo hdmi",
        "cabo usb", "cabo de rede", "roteador", "switch", "webcam", "headset", "impressora", "toner", "cartucho", "estabilizador",
        "nobreak", "hub usb", "adaptador usb", "carregador", "mousepad", "cartao de memoria", "processador", "placa de video",
    ],
    "eletronicos": [
        "televisor", "televisao", "smart tv", "ar condicionado", "ventilador", "geladeira", "refrigerador", "micro ondas", "microondas",
        "cafeteira", "bebedouro", "liquidificador", "aspirador", "fogao", "freezer", "purificador", "telefone", "celular", "pilha",
        "bateria", "caixa de som", "chaleira eletrica", "frigobar", "projetor",
    ],
    "construcao": [
        "cimento", "argamassa", "rejunte", "areia", "brita", "tijolo", "bloco de concreto", "telha", "piso", "porcelanato", "ceramica",
        "azulejo", "gesso", "drywall", "madeira", "compensado", "prego", "parafuso", "bucha", "vergalhao", "impermeabilizante",
        "silicone", "espuma expansiva", "manta asfaltica", "arruela", "porca", "rebite", "abracadeira", "chumbador", "barra roscada", "fechadura", "dobradica", "cadeado", "porta", "janela", "vidro", "rodape",
    ],
    "tintas": [
        "tinta", "massa corrida", "massa acrilica", "selador", "verniz", "esmalte", "solvente", "thinner", "aguarras", "rolo de pintura",
        "rolo", "pincel", "trincha", "lixa", "fita crepe", "primer", "fundo preparador", "textura", "tinta spray", "zarcao",
    ],
    "eletrica": [
        "fita isolante", "disjuntor", "tomada", "interruptor", "cabo flexivel", "cabo eletrico", "lampada", "luminaria", "reator",
        "refletor", "plafon", "extensao", "filtro de linha", "eletroduto", "conduite", "fio eletrico", "fio flexivel", "fio de cobre", "fio paralelo", "cabinho", "quadro de distribuicao", "rele", "sensor de presenca",
        "conector", "terminal", "plugue", "benjamim", "fotocelula", "dps",
    ],
    "hidraulica": [
        "torneira", "registro", "cano", "tubo pvc", "conexao", "joelho", "luva", "valvula", "sifao", "caixa d agua", "caixa dagua", "boia",
        "mangueira", "chuveiro", "ducha", "vaso sanitario", "assento sanitario", "pia", "ralo", "engate", "veda rosca", "fita veda rosca",
    ],
    "ferramentas": [
        "furadeira", "parafusadeira", "martelo", "chave de fenda", "chave philips", "alicate", "serra", "serrote", "esmerilhadeira",
        "lixadeira", "trena", "nivel", "broca", "disco de corte", "chave inglesa", "jogo de chaves", "escada", "carrinho de mao",
        "compressor", "soldador", "maquina de solda", "estilete", "macaco hidraulico", "torquimetro",
    ],
    "epi": [
        "luva", "capacete", "oculos de protecao", "protetor auricular", "mascara", "respirador", "botina", "bota", "colete refletivo",
        "cinto de seguranca", "talabarte", "avental", "luva nitrilica", "luva de latex", "luva de vaqueta", "luva de seguranca", "extintor", "cone", "fita zebrada", "protetor facial", "mangote", "perneira",
    ],
    "limpeza": [
        "detergente", "desinfetante", "agua sanitaria", "alvejante", "sabao", "sabonete", "alcool", "alcool gel", "papel higienico",
        "papel toalha", "saco de lixo", "saco para lixo", "vassoura", "rodo", "pano de chao", "esponja", "flanela", "limpa vidro", "multiuso",
        "cera", "lustra moveis", "balde", "pa de lixo", "lixeira", "dispenser", "odorizador", "cloro", "inseticida", "luva de limpeza",
    ],
    "copa": [
        "copo descartavel", "copo", "prato descartavel", "talher descartavel", "guardanapo", "garrafa termica", "filtro de papel", "coador",
        "xicara", "jarra", "bandeja", "mexedor", "papel aluminio", "filme pvc", "cafe", "acucar", "adocante", "cha", "garrafao",
    ],
    "alimentos": [
        "cafe", "acucar", "biscoito", "bolacha", "leite", "arroz", "feijao", "oleo de soja", "agua mineral", "refrigerante", "suco",
        "achocolatado", "margarina", "macarrao", "sal",
    ],
    "moveis": [
        "cadeira", "mesa", "armario", "estante", "gaveteiro", "poltrona", "sofa", "arquivo de aco", "balcao", "rack", "longarina", "escrivaninha",
    ],
    "saude": [
        "termometro", "curativo", "gaze", "esparadrapo", "soro fisiologico", "luva de procedimento", "mascara cirurgica", "seringa",
        "medicamento", "dipirona", "primeiros socorros", "algodao", "oximetro", "aparelho de pressao", "atadura", "agulha",
    ],
    "automotivo": [
        "oleo de motor", "oleo lubrificante", "pneu", "bateria automotiva", "aditivo para radiador", "fluido de freio", "palheta",
        "limpador de para brisa", "filtro de oleo", "lampada automotiva", "arla",
    ],
    "jardinagem": [
        "mangueira de jardim", "adubo", "fertilizante", "terra vegetal", "semente", "regador", "tesoura de poda", "cortador de grama",
        "rocadeira", "vaso de planta", "grama",
    ],
    "esporte": ["bola", "colchonete", "halter", "bicicleta", "apito", "cone de treino", "rede de volei", "rede de futebol"],
}

MARKETPLACE = "marketplace (vende de tudo)"

# Maiores lojas online de cada ramo. ramos vazio = vende de tudo (o sistema pesquisa todos os itens nela).
CATALOGO_LOJAS = [
    {"nome": "Kalunga", "site": "kalunga.com.br", "ramos": ["expediente", "informatica", "eletronicos", "moveis", "copa", "limpeza"], "apelidos": []},
    {"nome": "Gimba", "site": "gimba.com.br", "ramos": ["expediente", "limpeza", "copa", "informatica", "epi"], "apelidos": []},
    {"nome": "KaBuM!", "site": "kabum.com.br", "ramos": ["informatica", "eletronicos"], "apelidos": ["kabum"]},
    {"nome": "Pichau", "site": "pichau.com.br", "ramos": ["informatica"], "apelidos": []},
    {"nome": "Terabyte", "site": "terabyteshop.com.br", "ramos": ["informatica"], "apelidos": ["terabyte shop", "terabyteshop"]},
    {"nome": "Fast Shop", "site": "fastshop.com.br", "ramos": ["eletronicos", "informatica"], "apelidos": ["fastshop"]},
    {"nome": "Leroy Merlin", "site": "leroymerlin.com.br", "ramos": ["construcao", "tintas", "eletrica", "hidraulica", "ferramentas", "jardinagem", "moveis", "epi", "limpeza"], "apelidos": ["leroy"]},
    {"nome": "Telhanorte", "site": "telhanorte.com.br", "ramos": ["construcao", "tintas", "eletrica", "hidraulica", "ferramentas"], "apelidos": []},
    {"nome": "C&C", "site": "cec.com.br", "ramos": ["construcao", "tintas", "eletrica", "hidraulica", "ferramentas", "jardinagem"], "apelidos": ["cec", "c e c", "c&c casa e construcao"]},
    {"nome": "Obramax", "site": "obramax.com.br", "ramos": ["construcao", "tintas", "eletrica", "hidraulica", "ferramentas", "epi"], "apelidos": []},
    {"nome": "Ferreira Costa", "site": "ferreiracosta.com", "ramos": ["construcao", "tintas", "eletrica", "hidraulica", "ferramentas", "eletronicos", "moveis"], "apelidos": []},
    {"nome": "Balaroti", "site": "balaroti.com.br", "ramos": ["construcao", "tintas", "eletrica", "hidraulica", "ferramentas"], "apelidos": []},
    {"nome": "Dutra Máquinas", "site": "dutramaquinas.com.br", "ramos": ["ferramentas", "epi", "eletrica", "jardinagem"], "apelidos": ["dutra"]},
    {"nome": "Loja do Mecânico", "site": "lojadomecanico.com.br", "ramos": ["ferramentas", "epi", "jardinagem", "automotivo", "eletrica"], "apelidos": []},
    {"nome": "Ferramentas Kennedy", "site": "ferramentaskennedy.com.br", "ramos": ["ferramentas", "epi", "eletrica", "hidraulica"], "apelidos": ["kennedy"]},
    {"nome": "Loja Elétrica", "site": "lojaeletrica.com.br", "ramos": ["eletrica"], "apelidos": []},
    {"nome": "Carrefour", "site": "carrefour.com.br", "ramos": ["alimentos", "limpeza", "copa", "eletronicos", "informatica", "moveis", "automotivo"], "apelidos": []},
    {"nome": "Atacadão", "site": "atacadao.com.br", "ramos": ["alimentos", "limpeza", "copa"], "apelidos": []},
    {"nome": "Drogasil", "site": "drogasil.com.br", "ramos": ["saude", "limpeza"], "apelidos": []},
    {"nome": "Droga Raia", "site": "drogaraia.com.br", "ramos": ["saude", "limpeza"], "apelidos": ["raia"]},
    {"nome": "Cirúrgica Fernandes", "site": "cirurgicafernandes.com.br", "ramos": ["saude", "epi"], "apelidos": []},
    {"nome": "Dental Cremer", "site": "dentalcremer.com.br", "ramos": ["saude", "epi"], "apelidos": ["cremer"]},
    {"nome": "Tok&Stok", "site": "tokstok.com.br", "ramos": ["moveis", "copa"], "apelidos": ["tok stok", "tokstok"]},
    {"nome": "Mobly", "site": "mobly.com.br", "ramos": ["moveis"], "apelidos": []},
    {"nome": "MadeiraMadeira", "site": "madeiramadeira.com.br", "ramos": ["moveis", "construcao"], "apelidos": ["madeira madeira"]},
    {"nome": "Camicado", "site": "camicado.com.br", "ramos": ["copa"], "apelidos": []},
    {"nome": "Decathlon", "site": "decathlon.com.br", "ramos": ["esporte"], "apelidos": []},
    {"nome": "Centauro", "site": "centauro.com.br", "ramos": ["esporte"], "apelidos": []},
    {"nome": "Cobasi", "site": "cobasi.com.br", "ramos": ["jardinagem"], "apelidos": []},
    {"nome": "PneuStore", "site": "pneustore.com.br", "ramos": ["automotivo"], "apelidos": ["pneu store"]},
    # Marketplaces: a busca normal os ignora, mas entram se você os listar
    {"nome": "Mercado Livre", "site": "mercadolivre.com.br", "ramos": [], "apelidos": ["ml", "mercadolivre"], "marketplace": True},
    {"nome": "Amazon", "site": "amazon.com.br", "ramos": [], "apelidos": [], "marketplace": True},
    {"nome": "Magazine Luiza", "site": "magazineluiza.com.br", "ramos": [], "apelidos": ["magalu"], "marketplace": True},
    {"nome": "Americanas", "site": "americanas.com.br", "ramos": [], "apelidos": [], "marketplace": True},
    {"nome": "Casas Bahia", "site": "casasbahia.com.br", "ramos": [], "apelidos": [], "marketplace": True},
]


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, só letras/números/espaço (& vira 'e')."""
    texto = unicodedata.normalize("NFD", str(texto or "").lower().replace("&", " e "))
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto)).strip()


def dominio_de(texto: str) -> str:
    """'https://www.Kalunga.com.br/busca?x' -> 'kalunga.com.br'; vazio se o texto não for um endereço."""
    texto = (texto or "").strip().lower()
    texto = re.sub(r"^[a-z]+://", "", texto).split("/")[0].split("?")[0].split(":")[0]
    texto = texto[4:] if texto.startswith("www.") else texto
    return texto if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", texto) else ""


def classificar_item(item: str) -> set[str]:
    """Ramo(s) do item pelas palavras-chave. Vazio = não sei classificar (o item é pesquisado em todas as lojas)."""
    texto = f" {normalizar(item)} "
    palavras = texto.split()
    pontos: dict[str, int] = {}
    for ramo, chaves in PALAVRAS_RAMO.items():
        for chave in chaves:
            if " " in chave:
                if f" {chave} " in texto:
                    pontos[ramo] = pontos.get(ramo, 0) + 3
            elif any(p == chave or (len(chave) >= 4 and p in (chave + "s", chave + "es")) for p in palavras):
                pontos[ramo] = pontos.get(ramo, 0) + 1
    if not pontos:
        return set()
    maior = max(pontos.values())
    return {ramo for ramo, valor in pontos.items() if valor == maior}


def _chaves_da_loja(loja: dict) -> set[str]:
    raiz = loja["site"].split(".")[0]
    return {normalizar(loja["nome"]), normalizar(raiz), *(normalizar(a) for a in loja.get("apelidos", []))}


def resolver_loja(texto: str) -> dict | None:
    """Nome ou site digitado -> loja {nome, site, ramos, origem}. site vazio = loja desconhecida (descobrir o site pela busca)."""
    texto = (texto or "").strip()
    if not texto or texto.startswith("#"):
        return None
    dominio = dominio_de(texto) if "." in texto else ""
    for loja in CATALOGO_LOJAS:
        if (dominio and (dominio == loja["site"] or dominio.endswith("." + loja["site"]))) or normalizar(texto) in _chaves_da_loja(loja):
            return {"nome": loja["nome"], "site": loja["site"], "ramos": list(loja["ramos"]), "origem": "catálogo"}
    if dominio:
        return {"nome": texto, "site": dominio, "ramos": [], "origem": "site informado"}
    return {"nome": texto, "site": "", "ramos": [], "origem": "descobrir"}


def ler_ramos(texto: str) -> list[str]:
    """'Expediente, informática' -> ['expediente', 'informatica'] (aceita a chave ou o nome do ramo; ignora o que não reconhecer)."""
    por_nome = {normalizar(nome): chave for chave, nome in RAMOS.items()}
    ramos = []
    for parte in re.split(r"[,;/]", texto or ""):
        chave = normalizar(parte)
        chave = chave if chave in RAMOS else por_nome.get(chave, "")
        if chave and chave not in ramos:
            ramos.append(chave)
    return ramos


def loja_atende(loja: dict, ramos_item: set[str]) -> bool:
    """A loja vende o tipo do item? Loja sem ramos (vende de tudo) ou item sem ramo conhecido: sim."""
    return not loja.get("ramos") or not ramos_item or bool(set(loja["ramos"]) & ramos_item)
