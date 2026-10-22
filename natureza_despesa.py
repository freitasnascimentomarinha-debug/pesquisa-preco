"""Natureza de despesa e subelemento (Portaria STN nº 448/2002; códigos do Plano de Contas do SIAFI).

Os nomes vêm dos anexos da Portaria STN nº 448/2002 e os códigos de subelemento do plano de contas extraído do SIAFI
(consolidação da 8ª ICFEx, divulgada pela UFRJ). Desde 2017 as despesas de TIC têm naturezas próprias (339040 e
449040): os subelementos de TIC antigos de 339039 e 449052 não estão aqui.

A sugestão de subelemento é feita por palavras-chave da família (PDM) / classe do material ou do nome do serviço e
deve ser confirmada pelo operador: a API pública não informa a natureza de despesa dos itens.
"""

from __future__ import annotations

import re
import unicodedata

NATUREZAS = {
    "339030": "Material de consumo",
    "339039": "Outros serviços de terceiros – pessoa jurídica",
    "449052": "Equipamentos e material permanente",
}

SUBELEMENTOS = {
    "339030": {
        "01": "Combustíveis e lubrificantes automotivos", "02": "Combustíveis e lubrificantes de aviação",
        "03": "Combustíveis e lubrificantes para outras finalidades", "04": "Gás e outros materiais engarrafados",
        "05": "Explosivos e munições", "06": "Alimentos para animais", "07": "Gêneros de alimentação",
        "08": "Animais para pesquisa e abate", "09": "Material farmacológico", "10": "Material odontológico",
        "11": "Material químico", "12": "Material de coudelaria ou de uso zootécnico", "13": "Material de caça e pesca",
        "14": "Material educativo e esportivo", "15": "Material para festividades e homenagens",
        "16": "Material de expediente", "17": "Material de processamento de dados",
        "18": "Materiais e medicamentos para uso veterinário", "19": "Material de acondicionamento e embalagem",
        "20": "Material de cama, mesa e banho", "21": "Material de copa e cozinha",
        "22": "Material de limpeza e produtos de higienização", "23": "Uniformes, tecidos e aviamentos",
        "24": "Material para manutenção de bens imóveis/instalações", "25": "Material para manutenção de bens móveis",
        "26": "Material elétrico e eletrônico", "27": "Material de manobra e patrulhamento",
        "28": "Material de proteção e segurança", "29": "Material para áudio, vídeo e foto",
        "30": "Material para comunicações", "31": "Sementes, mudas de plantas e insumos", "32": "Suprimento de aviação",
        "33": "Material para produção industrial", "34": "Sobressalentes de máquinas e motores de navios e embarcações",
        "35": "Material laboratorial", "36": "Material hospitalar", "37": "Sobressalentes de armamento",
        "39": "Material para manutenção de veículos", "40": "Material biológico",
        "41": "Material para utilização em gráfica", "42": "Ferramentas", "43": "Material para reabilitação profissional",
        "44": "Material de sinalização visual e outros", "45": "Material técnico para seleção e treinamento",
        "46": "Material bibliográfico", "48": "Bens móveis não ativáveis", "49": "Bilhetes de passagem",
        "50": "Bandeiras, flâmulas e insígnias", "53": "Material meteorológico", "99": "Outros materiais de consumo",
    },
    "339039": {
        "01": "Assinaturas de periódicos e anuidades", "02": "Condomínios", "05": "Serviços técnicos profissionais",
        "09": "Armazenagem", "10": "Locação de imóveis", "12": "Locação de máquinas e equipamentos",
        "14": "Locação de bens móveis de outras naturezas e intangíveis",
        "16": "Manutenção e conservação de bens imóveis", "17": "Manutenção e conservação de máquinas e equipamentos",
        "18": "Serviços de estacionamento de veículos", "19": "Manutenção e conservação de veículos",
        "20": "Manutenção e conservação de bens móveis de outras naturezas", "22": "Exposições, congressos e conferências",
        "23": "Festividades e homenagens", "46": "Serviços domésticos", "47": "Serviços de comunicação em geral",
        "48": "Serviço de seleção e treinamento", "50": "Serviço médico-hospitalar, odontológico e laboratoriais",
        "51": "Serviços de análises e pesquisas científicas", "58": "Serviços de telecomunicações",
        "59": "Serviços de áudio, vídeo e foto", "61": "Serviços de socorro e salvamento",
        "62": "Serviços de produção industrial", "63": "Serviços gráficos e editoriais", "65": "Serviços de apoio ao ensino",
        "69": "Seguros em geral", "70": "Confecção de uniformes, bandeiras e flâmulas",
        "71": "Confecção de material de acondicionamento e embalagem", "73": "Transporte de servidores",
        "74": "Fretes e transportes de encomendas", "75": "Serviço de incineração/destruição de material",
        "77": "Vigilância ostensiva/monitorada", "78": "Limpeza e conservação",
        "79": "Serviço de apoio administrativo, técnico e operacional", "80": "Hospedagens", "81": "Serviços bancários",
        "83": "Serviços de cópias e reprodução de documentos", "85": "Serviços em itens reparáveis de aviação",
        "90": "Serviços de publicidade legal", "99": "Outros serviços de terceiros – pessoa jurídica",
    },
    "449052": {
        "02": "Aeronaves", "04": "Aparelhos de medição e orientação", "06": "Aparelhos e equipamentos de comunicação",
        "08": "Aparelhos, equipamentos e utensílios médicos, odontológicos, laboratoriais e hospitalares",
        "10": "Aparelhos e equipamentos para esportes e diversões", "12": "Aparelhos e utensílios domésticos",
        "14": "Armamentos", "18": "Coleções e materiais bibliográficos", "20": "Embarcações",
        "22": "Equipamentos de manobra e patrulhamento", "24": "Equipamento de proteção, segurança e socorro",
        "26": "Instrumentos musicais e artísticos", "28": "Máquinas e equipamentos de natureza industrial",
        "30": "Máquinas e equipamentos energéticos", "32": "Máquinas e equipamentos gráficos",
        "33": "Equipamentos para áudio, vídeo e foto", "34": "Máquinas, utensílios e equipamentos diversos",
        "35": "Equipamentos de processamento de dados", "36": "Máquinas, instalações e utensílios de escritório",
        "38": "Máquinas, ferramentas e utensílios de oficina", "39": "Equipamentos e utensílios hidráulicos e elétricos",
        "40": "Máquinas e equipamentos agrícolas e rodoviários", "42": "Mobiliário em geral",
        "48": "Veículos diversos", "51": "Peças não incorporáveis a imóveis", "52": "Veículos de tração mecânica",
        "57": "Acessórios para veículos", "58": "Equipamentos de mergulho e salvamento",
        "60": "Equipamentos, peças e acessórios marítimos", "99": "Outros materiais permanentes",
    },
}

A_DEFINIR = "a definir"


def rotulo(codigo: str) -> str:
    """'33903016' -> '3.3.90.30.16 – Material de expediente'."""
    if not codigo or len(codigo) != 8:
        return A_DEFINIR
    nd, sub = codigo[:6], codigo[6:]
    nome = SUBELEMENTOS.get(nd, {}).get(sub, "")
    return f"{nd[0]}.{nd[1]}.{nd[2:4]}.{nd[4:6]}.{sub} – {nome}" if nome else codigo


def opcoes() -> list[str]:
    """Todos os subelementos como rótulos, para o seletor da tela."""
    return [A_DEFINIR] + [rotulo(nd + sub) for nd in SUBELEMENTOS for sub in SUBELEMENTOS[nd]]


def codigo_do_rotulo(texto: str) -> str:
    m = re.match(r"(\d)\.(\d)\.(\d{2})\.(\d{2})\.(\d{2})", texto or "")
    return "".join(m.groups()) if m else ""


def _norm(t: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", unicodedata.normalize("NFD", str(t or "")).encode("ascii", "ignore").decode().upper())


# (padrão, subelemento) — a primeira regra que casar vence. Material permanente antes do de consumo.
REGRAS_MATERIAL = [
    (r"MERGULHO|SALVAMENTO MARITIMO|SALVA VIDAS|BOTE INFLAVEL|BALSA SALVA", "44905258"),
    (r"INSTRUMENTOS DE MEDICAO|TESTES DE PROPRIEDADES|TORQUIMETRO|PAQUIMETRO|MICROMETRO|MULTIMETRO|"
     r"RELOGIO COMPARADOR|NIVEL DE PRECISAO|DINAMOMETRO", "44905204"),
    (r"RETIFICADORA|ESMERILHADEIRA|FURADEIRA|SERRA (CIRCULAR|ELETRICA)|MAQUINA FERRAMENTA|TORNO MECANICO", "44905238"),
    (r"ANTENA|TRANSCEPTOR", "44905206"),
    (r"PURIFICADOR|ENCERADEIRA|ASPIRADOR", "44905212"),
    (r"VENTILADOR|EXAUSTOR|CIRCULADOR DE AR|MAQUINA COSTURA|MAQUINAS PARA INDUSTRIA|GUINCHO|ICADOR|TALHA|"
     r"BOMBA|COMPRESSOR|SECADORA AR|GERADOR|MOTOBOMBA", "44905234"),
    (r"MOBILIARIO|\bMESA\b(?! E BANHO)|CADEIRA|ARMARIO|ESTANTE|ARQUIVO DE ACO|POLTRONA|SOFA", "44905242"),
    (r"MICROCOMPUTADOR|COMPUTADOR|NOTEBOOK|SERVIDOR DE REDE|IMPRESSORA|SCANNER|MONITOR", "44905235"),
    (r"AR CONDICIONADO|REFRIGERADOR|GELADEIRA|FOGAO|FORNO|BEBEDOURO|LAVADORA|FREEZER|ELETRODOMEST", "44905212"),
    (r"TELEVISOR|PROJETOR|CAMERA|FILMADORA|EQUIPAMENTO.*(AUDIO|VIDEO|FOTO)", "44905233"),
    (r"RADIO TRANSCEPTOR|TELEFONE|EQUIPAMENTO.*COMUNICAC", "44905206"),
    (r"FERRAMENTA|ABRASIV|BROCA|ALARGADOR|ESCARIADOR|DISCO CORTE", "33903042"),
    (r"OLEOS E GORDURAS COMESTIV|GORDURA VEGETAL|MARGARINA|CONSERVA|GELEIA|GELATINA", "33903007"),
    (r"GASES COMPRIMIDOS|MISTURA GASOSA", "33903004"),
    (r"LIXEIRA|BALDE|CARRO COLETOR", "33903022"),
    (r"PORCA|ARRUELA|PARAFUSO|BUCHA|ANEIS|ESPACADOR|ROLAMENTO|GAXETA|VEDACAO|VEDANTE|JUNTA|VALVULA|REGISTRO|"
     r"MANGUEIRA|MANGOTE|ADESIVO|\bCOLA\b|SOLDA|ELETRODO|ANODO|ACABAMENTO EM METAL|FILTRO|ELEMENTO FILTRANTE|"
     r"ACESSORIOS DIVERSOS DE MOTORES|OFICINA MECANICA|PASTILHA METALICA|CORDOALHA|CABOS DE FIBRA|CORDA", "33903025"),
    (r"BARRAS|VERGALH|PERFIS ESTRUTURAIS|PERFILADO|CANTONEIRA|SEMI ACABADOS|TARUGO|CHAPA|PRODUTOS DIVERSOS NAO METALICOS|"
     r"ARTIGOS DE PLASTICO|IMPERMEABILIZANTE|MANTA ASFALTICA|PRESERVATIVOS", "33903024"),
    (r"RECIPIENTE|FRASCO|CONTAINER|TANQUE", "33903019"),
    (r"ITENS DIVERSOS|BRINDE", "33903099"),
    (r"PROCESSAMENTO DE DADOS|INFORMATICA|TONER|CARTUCHO|PEN DRIVE|MOUSE|TECLADO", "33903017"),
    (r"ESCRITORIO|EXPEDIENTE|PAPEL|CANETA|LAPIS|GRAMPEADOR|PASTA|ENVELOPE|CLIPS|ETIQUETA", "33903016"),
    (r"LIMPEZA|HIGIEN|DETERGENTE|SABAO|DESINFETANTE|PAPEL HIGIENICO", "33903022"),
    (r"COPA|COZINHA|DESCARTAVEL|COPO|PRATO|TALHER|UTENSILIO DOMESTICO", "33903021"),
    (r"ALIMENT|GENERO|LATICINIO|OVOS|PANIFICACAO|CEREAIS|CARNE|PESCADO|FRUTA|VERDURA|LEGUME|CONDIMENTO|BEBIDA|"
     r"MANTEIGA|QUEIJO|EMBUTIDO|CAFE|ACUCAR|DOCE|SALGADO|FERMENTO|OLEAGINOSA|AGUA MINERAL", "33903007"),
    (r"MEDICAMENTO|FARMAC", "33903009"),
    (r"ODONTO", "33903010"),
    (r"HOSPITALAR|MEDICO|CIRURGIC", "33903036"),
    (r"LABORATORI", "33903035"),
    (r"QUIMIC", "33903011"),
    (r"COMBUSTIVE|LUBRIFICANTE|OLEO DIESEL|GASOLINA", "33903001"),
    (r"\bGAS\b|EXTINTOR", "33903004"),
    (r"VEICUL|AUTOMOTIV|PNEU|FILTRO DE AR|PASTILHA DE FREIO", "33903039"),
    (r"NAVIO|EMBARCAC|NAVAL|SOBRESSALENTE", "33903034"),
    (r"ARMAMENTO", "33903037"),
    (r"ELETRIC|ELETRONIC|LAMPADA|\bCABO\b|\bFIO\b|DISJUNTOR|TOMADA|PILHA|BATERIA", "33903026"),
    (r"CONSTRUC|HIDRAULIC|TINTA|PINTURA|CIMENTO|TELHA|TUBO|CONEXAO|MADEIRA", "33903024"),
    (r"UNIFORME|VESTUARIO|TECIDO|CALCADO|AVIAMENTO|FARDAMENTO", "33903023"),
    (r"\bCAMA\b|BANHO|TOALHA|LENCOL|COLCHAO", "33903020"),
    (r"EMBALAGEM|ACONDICIONAMENTO|SACO|CAIXA DE PAPELAO", "33903019"),
    (r"PROTECAO|SEGURANCA|\bEPI\b|LUVA|CAPACETE|\bBOTA\b", "33903028"),
    (r"SINALIZACAO|PLACA", "33903044"),
    (r"GRAFIC", "33903041"),
    (r"EDUCATIV|ESPORTIV|ESPORTE", "33903014"),
    (r"BANDEIRA|FLAMULA|INSIGNIA", "33903050"),
    (r"LIVRO|BIBLIOGRAF|PERIODICO", "33903046"),
    (r"SEMENTE|MUDA|JARDINAGEM|ADUBO|FERTILIZANTE", "33903031"),
    (r"AUDIO|VIDEO|FOTO", "33903029"),
]

REGRAS_SERVICO = [
    (r"(MANUTENCAO|REVISAO|REPARO|CONSERTO).*(VEICUL|VIATURA|AUTOMOT)|REVISAO VEICULO|LAVAGEM.*VEICUL", "33903919"),
    (r"(MANUTENCAO|INSTALACAO|REPARO).*(PREDI|IMOVE|EDIFIC|ELEVADOR|ESCADA|TELHADO|PINTURA|HIDRAULIC|ALVENARIA|"
     r"REDES? (DE )?AGUA|ESGOTO|PELICULA|CANCELA|PORTAO)", "33903916"),
    (r"(MANUTENCAO|INSTALACAO|REPARO|CONSERTO).*(MAQUINA|EQUIPAMENTO|COMPRESSOR|NOBREAK|GERADOR|TALHA|TORNO|BOMBA|"
     r"AR CONDICIONADO|REFRIGERAC|VENTILAC|EXAUST|MOTOR)|CALIBRAC|AFERIC", "33903917"),
    (r"(MANUTENCAO|REFORMA|ESTOFAMENTO).*(MOVEIS|MOBILIARIO)|ESTOFAMENTO", "33903920"),
    (r"LOCACAO.*IMOVE", "33903910"),
    (r"LOCACAO.*(MAQUINA|EQUIPAMENTO|AR CONDICIONADO|ANDAIME|IMPRESSORA|GERADOR|CONTAINER)", "33903912"),
    (r"LOCACAO", "33903914"),
    (r"SEGURO", "33903969"),
    (r"VIGILANCIA", "33903977"),
    (r"LIMPEZA|CONSERVACAO|DESINSETIZ|DEDETIZ|DESRATIZ|JARDINAGEM|ROCADA", "33903978"),
    (r"TREINAMENTO|CURSO|CAPACITAC|QUALIFICAC|APERFEICOAMENTO", "33903948"),
    (r"ANALISE|ENSAIO|LABORATORI|PESQUISA CIENTIFICA", "33903951"),
    (r"MEDIC|HOSPITALAR|ODONTOL|EXAME", "33903950"),
    (r"GRAFIC|IMPRESSAO|EDITORA|ENCADERNA", "33903963"),
    (r"COPIA|REPROGRAF|DIGITALIZAC", "33903983"),
    (r"TELEFON|TELECOMUNIC|INTERNET|LINK|SATELITE|DADOS MOVEIS", "33903958"),
    (r"FRETE|TRANSPORTE DE (CARGA|ENCOMENDA|MATERIA)|MUDANCA|REBOQUE", "33903974"),
    (r"TRANSPORTE DE (PESSOAL|SERVIDOR|PASSAGEIRO)", "33903973"),
    (r"HOSPEDAGEM", "33903980"),
    (r"PUBLICAC|PUBLICIDADE LEGAL", "33903990"),
    (r"FESTIVIDADE|HOMENAGEM|ORNAMENT|ARRANJO|BUFFET|COQUETEL|CERIMONIA", "33903923"),
    (r"CONFECC.*(UNIFORME|BANDEIRA|FLAMULA)", "33903970"),
    (r"INCINERAC|DESTRUICAO", "33903975"),
    (r"APOIO ADMINISTRATIVO|RECEPC|COPEIRAGEM|LAVANDERIA|MOTORISTA|CARREGADOR", "33903979"),
    (r"TRADUC|INTERPRETAC|ENGENHARIA|PROJETO|CONSULTORIA|ASSESSORIA|PERICIA|AUDITORIA|LAUDO", "33903905"),
    (r"AUDIO|VIDEO|FOTO|FILMAGEM", "33903959"),
    (r"ESTACIONAMENTO", "33903918"),
]


def sugerir(material: bool, ramo: str, classe: str = "") -> str:
    """Código de 8 dígitos sugerido (ex.: '33903016') ou '' quando nenhuma regra se aplica."""
    texto = _norm(f"{ramo} {classe}")
    for padrao, codigo in (REGRAS_MATERIAL if material else REGRAS_SERVICO):
        if re.search(padrao, texto):
            return codigo
    return "33903999" if not material else ""
