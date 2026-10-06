"""Banco de nomes populares x nomes comerciais de materiais de consumo e permanentes.

Cada linha: (nomes populares, nome comercial usado na BUSCA, palavras que RECUSAM o anúncio, aceitar o nome popular no anúncio?)
- A busca e o scraping usam o nome comercial ("maizena" -> "amido de milho", "durex" -> "fita adesiva transparente").
- O anúncio é aceito se tiver o nome comercial (as 2 primeiras palavras) ou, quando o 4º campo é True, o nome popular
  (muitas lojas também escrevem "Fita Durex", "Cotonete"). Use False quando o nome popular confunde (ex.: "caneta piloto"
  casaria com "caneta esferográfica Pilot").
- As palavras de recusa evitam produtos parecidos de outro tipo (peças, acessórios, refis de outra coisa).
Para acrescentar um material, basta uma nova linha. Nomes que já são comerciais (ex.: "grampeador") não precisam estar aqui.
"""

BANCO = [
    # ---------------- Escritório e papelaria ----------------
    (["caneta piloto", "pincel para quadro branco", "pincel quadro branco", "caneta de quadro branco", "marcador de quadro"],
     "marcador para quadro branco", ["esferografica", "gel", "rollerball", "permanente", "marca texto", "tinteiro"], False),
    (["pincel atomico", "caneta pincel atomico"], "marcador permanente", ["quadro branco", "esferografica"], True),
    (["papel contact", "plastico contact", "contact"], "papel adesivo contact",
     ["toalha", "higienico", "guardanapo", "filtro", "sulfite", "fotografico", "seda", "manteiga", "aluminio", "lente de contato"], True),
    (["durex", "fita durex"], "fita adesiva transparente", ["dupla face", "crepe", "isolante", "silver tape"], True),
    (["post it", "postit", "post-it", "papel de recado"], "bloco de notas adesivas", [], True),
    (["liquid paper", "branquinho", "corretivo branquinho"], "corretivo líquido", ["facial", "maquiagem", "olheira"], True),
    (["caneta bic", "bic cristal"], "caneta esferográfica", ["isqueiro", "barbeador", "gilete"], False),
    (["grafite de lapiseira", "grafite 0,7", "grafite 0,5", "mina de lapiseira"], "grafite para lapiseira", ["lapis de cor"], True),
    (["pasta az", "pasta a-z", "registrador az", "pasta arquivo az"], "pasta registradora AZ", ["sanfonada"], True),
    (["pasta sanfona", "pasta sanfonada"], "pasta sanfonada", [], True),
    (["pasta suspensa"], "pasta suspensa kraft", [], True),
    (["pasta catalogo", "pasta com plasticos"], "pasta catálogo", [], True),
    (["grampo de grampeador", "grampo para grampeador", "grampo 26/6", "grampos 26/6"], "grampo para grampeador 26/6",
     ["cabelo", "roupa", "varal", "u galvanizado"], True),
    (["etiqueta pimaco", "pimaco"], "etiqueta adesiva", [], True),
    (["fita silver tape", "silver tape", "fita prata"], "fita adesiva silver tape", [], True),
    (["fita gomada"], "fita gomada kraft", [], True),
    (["papel pardo", "papel de embrulho"], "papel kraft", ["envelope", "saco"], True),
    (["isopor", "placa de isopor"], "placa de isopor EPS", ["caixa termica", "copo", "bandeja"], True),
    (["eva", "folha de eva", "emborrachado"], "placa de EVA", ["chinelo", "tapete"], True),
    (["tnt", "tecido tnt"], "tecido TNT", [], True),
    (["bobina termica", "bobina de maquininha", "bobina para cartao"], "bobina para impressora térmica", [], True),
    (["livro ponto", "livro de ponto"], "livro de ponto", [], True),
    (["bloco de rascunho", "bloquinho"], "bloco de anotações", ["adesivo"], True),
    (["papel oficio"], "papel sulfite ofício", ["envelope"], True),
    (["papel a4", "folha a4", "papel chamex", "chamex"], "papel sulfite A4", ["envelope", "fotografico", "adesivo", "etiqueta"], True),
    (["liga de dinheiro", "elastico de dinheiro", "liguinha"], "elástico de látex para dinheiro", ["cabelo", "costura", "roupa"], True),
    (["tinta de carimbo"], "tinta para carimbo", [], True),
    (["clips", "clipes", "clipe"], "clips para papel", ["cabelo", "prendedor de cabelo"], True),

    # ---------------- Limpeza e higiene ----------------
    (["bombril", "palha de aco", "esponja de aco"], "lã de aço", ["inox", "dupla face"], True),
    (["cotonete"], "haste flexível com pontas de algodão", [], True),
    (["candida", "qboa", "q-boa", "agua sanitaria"], "água sanitária", [], True),
    (["sabao em pedra", "sabao de pedra"], "sabão em barra", ["po", "liquido"], True),
    (["omo", "sabao em po omo"], "sabão em pó", ["liquido", "barra"], False),
    (["bom ar", "bom-ar", "aromatizador bom ar"], "aromatizador de ambiente spray", [], True),
    (["pinho sol", "pinho-sol"], "desinfetante pinho", [], True),
    (["sapolio", "cif", "saponaceo"], "saponáceo cremoso", [], True),
    (["vidrex", "limpa vidro"], "limpa vidros", [], True),
    (["poliflor", "lustra movel"], "lustra móveis", [], True),
    (["pano de chao saco", "saco alvejado", "saco de chao"], "pano de chão saco alvejado", [], True),
    (["luva de borracha", "luva de limpeza", "luva de cozinha"], "luva látex multiuso", ["procedimento", "nitrilica", "cirurgica"], True),
    (["gilete", "aparelho de barbear"], "aparelho de barbear descartável", ["lamina de estilete"], True),
    (["band-aid", "band aid", "bandaid"], "curativo adesivo", [], True),
    (["pasta de dente", "colgate"], "creme dental", ["escova"], True),
    (["bombinha de pia", "desentupidor"], "desentupidor de pia", ["liquido", "soda"], True),
    (["baygon", "sbp", "veneno de inseto", "mata mosquito"], "inseticida aerossol", [], True),
    (["papel higienico folha dupla", "papel higienico"], "papel higiênico", ["toalha", "umedecido"], True),
    (["papel toalha de mao", "papel interfolha", "papel toalha interfolha"], "papel toalha interfolhado", ["higienico", "rolo de cozinha"], True),
    (["saco de lixo preto", "saco preto"], "saco para lixo", ["aspirador"], True),

    # ---------------- Copa, cozinha e alimentos ----------------
    (["maizena", "amido de milho maizena"], "amido de milho", [], True),
    (["nescau", "toddy", "chocolate em po"], "achocolatado em pó", [], True),
    (["sucrilhos", "sucrilho", "flocos de milho acucarado"], "cereal matinal de milho", [], True),
    (["catupiry"], "requeijão cremoso", [], True),
    (["leite moca", "leite moça"], "leite condensado", [], True),
    (["miojo"], "macarrão instantâneo", [], True),
    (["nescafe", "cafe soluvel nescafe"], "café solúvel", [], True),
    (["agua de galao", "galao de agua", "agua de garrafao", "garrafao de agua"], "água mineral galão", ["suporte", "bebedouro", "bomba"], True),
    (["coador de papel", "filtro de cafe", "filtro de papel 103", "filtro 103"], "filtro de papel para café", ["permanente", "pano"], True),
    (["papel filme", "rolopac", "filme plastico"], "filme PVC", [], True),
    (["copinho descartavel", "copo plastico", "copinho de cafe"], "copo descartável", [], True),
    (["marmitex", "quentinha"], "marmita de alumínio", [], True),
    (["tupperware", "vasilha plastica", "vasilha com tampa"], "pote plástico com tampa", [], True),
    (["termica de cafe", "garrafa de cafe"], "garrafa térmica", [], True),
    (["cacetinho", "pao de sal", "pao frances"], "pão francês", ["forma"], True),
    (["aipim", "macaxeira"], "mandioca", [], True),
    (["jerimum"], "abóbora", [], True),
    (["mexerica", "bergamota", "ponkan"], "tangerina", [], True),
    (["oleo de cozinha"], "óleo de soja", [], True),
    (["massa de tomate"], "extrato de tomate", [], True),
    (["acucar refinado uniao"], "açúcar refinado", [], True),
    (["mortadela", "presunto"], "frios fatiados", [], True),

    # ---------------- Informática ----------------
    (["regua de tomada", "filtro de linha"], "filtro de linha", ["agua"], True),
    (["mouse sem fio"], "mouse wireless", [], True),
    (["cabo de impressora"], "cabo USB para impressora", [], True),
    (["cabo de rede", "cabo lan", "cabo ethernet"], "cabo de rede", [], True),
    (["pendrive"], "pen drive", [], True),

    # ---------------- Elétrico ----------------
    (["benjamim", "benjamin", "t de tomada", "tezinho de tomada"], "adaptador de tomada", [], True),
    (["fio eletrico", "fio flexivel", "fio de luz"], "cabo flexível", ["dental", "nylon", "pesca"], True),
    (["pilha palito"], "pilha AAA", [], True),
    (["pilha pequena", "pilha comum"], "pilha AA", [], True),
    (["pilha media"], "pilha C", [], True),
    (["pilha grande"], "pilha D", [], True),
    (["bateria quadrada", "bateria de 9v"], "bateria 9V", [], True),
    (["bocal de lampada", "bocal"], "soquete para lâmpada", [], True),
    (["holofote"], "refletor LED", [], True),
    (["enforca gato", "enforca-gato", "presilha de nylon", "abracadeira plastica"], "abraçadeira de nylon", ["metalica", "rosca sem fim"], True),
    (["conduite", "conduite corrugado", "mangueira corrugada"], "eletroduto corrugado", [], True),
    (["lampada tubular", "lampada de tubo"], "lâmpada tubular LED", [], True),

    # ---------------- Ferramentas e adesivos ----------------
    (["chave philips", "chave phillips"], "chave phillips", ["fenda"], True),
    (["chave de boca"], "chave fixa", [], True),
    (["chave inglesa"], "chave ajustável", [], True),
    (["chave de cano", "chave grifo"], "chave grifo", [], True),
    (["turques", "torques"], "torquês", [], True),
    (["maquita", "lixadeira angular", "makita"], "esmerilhadeira angular", ["disco"], True),
    (["serra de ferro"], "arco de serra", [], True),
    (["broca de videa", "broca para parede"], "broca para concreto", [], True),
    (["wd40", "wd-40", "wd 40"], "desengripante", [], True),
    (["durepoxi", "durepox"], "massa epóxi", [], True),
    (["super bonder", "superbonder", "cola tudo"], "cola instantânea", [], True),
    (["araldite"], "adesivo epóxi", [], True),
    (["cola de sapateiro", "cola contato", "cascola"], "adesivo de contato", [], True),
    (["teflon", "fita teflon"], "fita veda rosca", [], True),
    (["bastao de cola quente", "cola quente em bastao"], "refil de cola quente", ["pistola"], True),

    # ---------------- Construção e hidráulica ----------------
    (["cano", "cano pvc", "cano de agua"], "tubo PVC", [], True),
    (["boia de caixa", "boia de caixa d agua"], "torneira boia", [], True),
    (["rabicho", "flexivel de pia"], "engate flexível", [], True),
    (["cimento cola"], "argamassa colante", [], True),
    (["zarcao"], "fundo anticorrosivo", [], True),
    (["tijolo baiano", "tijolo de 8 furos"], "tijolo cerâmico 8 furos", [], True),
    (["telha eternit", "telha brasilit", "eternit"], "telha de fibrocimento", [], True),
    (["gesso acartonado"], "chapa de drywall", [], True),
    (["manta liquida"], "impermeabilizante manta líquida", [], True),
    (["ferro de construcao", "ferro 3/8", "ferro 5/16"], "vergalhão CA-50", [], True),
    (["bucha de parede", "bucha de fixacao"], "bucha de nylon", ["vegetal", "banho", "lavar louca"], True),
    (["pincel de pintura", "trincha de pintura"], "trincha", ["maquiagem"], True),

    # ---------------- EPI e sinalização ----------------
    (["luva de procedimento", "luva descartavel"], "luva de látex para procedimento", ["limpeza", "multiuso"], True),
    (["mascara descartavel", "mascara cirurgica"], "máscara cirúrgica descartável", ["pff2", "n95"], True),
    (["abafador de ruido"], "protetor auricular tipo concha", [], True),
    (["protetor de ouvido", "plug de ouvido", "tampao de ouvido"], "protetor auricular de espuma", ["concha"], True),
    (["galocha", "bota de borracha"], "bota de PVC", [], True),
    (["cinto paraquedista"], "cinturão de segurança paraquedista", [], True),
    (["cone de transito"], "cone de sinalização", [], True),
    (["fita zebrada", "fita de isolamento"], "fita de sinalização zebrada", [], True),

    # ---------------- Eletrodomésticos e equipamentos ----------------
    (["geladeira", "refrigerador"], "geladeira",
     ["prateleira", "gaveta", "borracha", "gaxeta", "puxador", "filtro", "adesivo", "envelopamento", "capa", "porta latas", "organizador",
      "termostato", "compressor", "dobradica", "lampada", "pe nivelador", "peca", "brinquedo", "miniatura", "frigobar"], True),
    (["ar condicionado", "ar-condicionado", "split"], "ar condicionado split", ["controle remoto", "suporte", "capa", "tubulacao", "dreno"], True),
    (["televisao", "tv"], "smart TV", ["suporte", "controle", "antena", "capa"], True),
    (["bebedouro de garrafao"], "bebedouro de coluna", ["galao", "garrafao de agua"], True),

    # ---------------- Automotivo ----------------
    (["oleo de motor", "oleo do carro"], "óleo lubrificante para motor", ["filtro"], True),
    (["palheta", "limpador de parabrisa", "limpador de para-brisa"], "palheta limpador para-brisa", [], True),
    (["arla"], "arla 32", [], True),

    # ---------------- Diversos ----------------
    (["lousa", "quadro de escola"], "quadro branco", ["marcador", "apagador", "pincel"], True),
    (["quadro de aviso", "mural de cortica"], "quadro de cortiça", [], True),
    (["apagador"], "apagador para quadro branco", [], True),
    (["saquinho plastico", "saco transparente"], "saco plástico transparente", ["lixo"], True),
    (["sacolinha", "sacola de mercado"], "sacola plástica", [], True),
    (["papelao", "caixa de papelao"], "caixa de papelão", [], True),
]
