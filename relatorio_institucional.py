"""Relatório institucional do AtaCotada: história, finalidade, fontes, metodologia e limites do sistema.

Documento para ser juntado ao processo de contratação e dar à autoridade o respaldo sobre a origem e o funcionamento
dos relatórios que o sistema gera. Sai no padrão gráfico da Marinha (documento_oficial) em PDF e Word.
Sem dependência do Streamlit.
"""

from __future__ import annotations

import hashlib
from datetime import datetime

import documento_oficial

URL_APLICACAO = "https://pesquisa-preco.streamlit.app/"
URL_CODIGO = "https://github.com/freitasnascimentomarinha-debug/pesquisa-preco"
VERSAO = "AtaCotada V2.0"
TITULO = "RELATÓRIO INSTITUCIONAL DO SISTEMA ATACOTADA"
OM_PADRAO = "Centro de Operações do Abastecimento"

FONTES = (
    ("Compras.gov.br – Dados Abertos", "https://dadosabertos.compras.gov.br", "preços praticados, atas de registro de preços, catálogo CATMAT/CATSERV e fornecedores"),
    ("PNCP – Portal Nacional de Contratações Públicas", "https://pncp.gov.br", "contratações, dispensas e atas"),
    ("Portal da Transparência", "https://portaldatransparencia.gov.br", "arquivos mensais de notas fiscais eletrônicas"),
    ("Portal da NF-e (Receita Federal)", "https://www.nfe.fazenda.gov.br", "autenticação das notas fiscais"),
    ("Banco Central do Brasil / IBGE", "https://www.bcb.gov.br", "IPCA (série 433)"),
    ("OpenCNPJ, BrasilAPI e ReceitaWS", "", "dados cadastrais e contatos de empresas a partir do CNPJ"),
    ("Internet aberta", "", "lojas e sítios eletrônicos pesquisados pelo Web Scraping, com endereço e data/hora de cada acesso"),
    ("Legislação e jurisprudência", "", "Lei nº 14.133/2021, instruções normativas e acórdãos do TCU usados pelo Babilaca"),
)


def _metodologia() -> str:
    """Metodologia da Cotação Rápida, com os parâmetros reais do sistema (os mesmos impressos nos relatórios de preços)."""
    try:
        import relatorio_cotacao_rapida as rcr
        texto = rcr.metodologia()
    except Exception:
        return ""
    linhas = [linha.strip() for linha in texto.split("\n") if linha.strip()][1:]  # sem o título "Metodologia da Cotação Rápida"
    numeradas = []
    for linha in linhas:  # "1. ..." vira "5.2. ..." (subitens do item 5)
        numero, _, resto = linha.partition(". ")
        numeradas.append(f"5.{int(numero) + 1}. {resto}" if numero.isdigit() else linha)
    return "\n\n".join(numeradas)


def corpo(ferramentas: list[tuple[str, str, str]], emitido_em: datetime | None = None) -> str:
    """Texto do relatório em Markdown (o formato que documento_oficial entende), terminado pelo código de integridade."""
    agora = emitido_em or datetime.now()
    carimbo = agora.strftime("%d/%m/%Y às %H:%M")
    partes = [
        "### 1. IDENTIFICAÇÃO E ACESSO",
        f"1.1. **Sistema:** AtaCotada — sistema autônomo de apoio à pesquisa de preços e à instrução de processos de contratação ({VERSAO}).",
        f"1.2. **Endereço de acesso (aplicação):** {URL_APLICACAO}",
        f"1.3. **Código-fonte (código aberto, com o histórico de todas as alterações):** {URL_CODIGO}",
        "1.4. **Condições de uso:** sistema web, gratuito e sem instalação; o código é aberto e pode ser auditado por qualquer interessado.",
        f"1.5. **Emissão deste relatório:** {carimbo}, a partir da página “Sobre o projeto” do próprio sistema.",
        "",
        "### 2. ORIGEM E HISTÓRICO",
        "2.1. O AtaCotada nasceu no Centro de Operações do Abastecimento da Marinha do Brasil, para reduzir o tempo gasto em consultas manuais "
        "e na consolidação de dados em planilhas na pesquisa de preços.",
        "2.2. O projeto foi idealizado e desenvolvido pelo 2°SG-PL Freitas, sob a liderança e coordenação do CMG (IM) ROMA e com apoios fundamentais "
        "do CAlt (IM) Yamaguchi, atual DGOM, e do CAlt (IM) Ricardo Nogueira, atual COpAb.",
        "2.3. Em 2026, o sistema foi apresentado, aprovado e elogiado pelo DAbM Vice-Alt Viveiros.",
        "2.4. O propósito do projeto é demonstrar a capacidade das novas tecnologias de aprimorar os processos de trabalho, para que outras pessoas se inspirem, "
        "aprendam e desenvolvam sistemas e soluções criativas que facilitem a vida de quem trabalha.",
        "2.5. Por entender que contribuir com a missão da Marinha é mais importante do que qualquer reconhecimento ou valor monetário, o sistema é de código aberto e gratuito.",
        "2.6. O AtaCotada existe para mostrar que a falta de pessoal pode ser suprida com inteligência, automação e IA.",
        "",
        "### 3. FINALIDADE",
        "3.1. O sistema transforma informações dispersas (APIs, catálogos, notas fiscais e páginas da internet) em dados estruturados e comparáveis, e padroniza a "
        "memória da pesquisa de preços: origem, data, estatísticas e evidências de cada valor.",
        "3.2. Apoia a consulta à legislação aplicável, como a Lei nº 14.133/2021 (art. 23, valor estimado da contratação) e a IN SEGES/ME nº 65/2021 (pesquisa de preços).",
        "3.3. Ferramentas disponíveis:",
        "",
        "| Ferramenta | Função |",
        "|---|---|",
    ]
    partes += [f"| {nome} | {descricao} |" for _, nome, descricao in ferramentas]
    partes += [
        "",
        "### 4. FONTES DOS DADOS",
        "4.1. Os dados usados pelo sistema são públicos e são captados e estruturados de forma autônoma: o sistema consulta as fontes, organiza as informações em tabelas, "
        "calcula e gera os relatórios.",
        "",
        "| Fonte | Endereço | Dados utilizados |",
        "|---|---|---|",
    ]
    partes += [f"| {nome} | {url or '—'} | {uso} |" for nome, url, uso in FONTES]
    metodologia = _metodologia()
    partes += [
        "",
        "### 5. METODOLOGIA DA PESQUISA DE PREÇOS",
        "5.1. Os parâmetros abaixo são os aplicados pelo sistema na Cotação Rápida e constam também, em cada relatório de preços, na justificativa da metodologia.",
        "",
        metodologia or "5.2. A metodologia detalhada acompanha cada relatório de preços gerado pelo sistema.",
        "",
        "### 6. RASTREABILIDADE E EVIDÊNCIAS",
        "6.1. Cada preço listado nos relatórios identifica a origem da informação (compra, órgão, fornecedor, CNPJ, data e código do item). Na pesquisa pela internet, "
        "o relatório registra o endereço eletrônico, a data e a hora de cada acesso e, quando disponível, o print da página.",
        "6.2. Os relatórios trazem o mapa comparativo, as estatísticas (média, mediana, mínimo, máximo, desvio padrão e coeficiente de variação) e a memória de cálculo, "
        "permitindo à autoridade conferir como cada valor foi obtido.",
        "6.3. Os dados de origem são públicos e podem ser consultados diretamente nas fontes indicadas no item 4.",
        "",
        "### 7. LIMITES DE USO E RESPONSABILIDADE",
        "7.1. O AtaCotada é uma ferramenta de apoio. Ele não substitui a análise e a decisão do agente responsável pela contratação, a quem cabe conferir os itens, os códigos "
        "de catálogo, as unidades e a adequação dos preços ao objeto.",
        "7.2. A correspondência entre a descrição do item e o código CATMAT/CATSERV é uma sugestão automática e deve ser conferida pelo requisitante antes do uso no processo.",
        "7.3. Itens com menos de três preços são sinalizados nos relatórios e devem ser complementados por outras fontes (IN SEGES/ME nº 65/2021, art. 5º).",
        "7.4. O sistema depende de fontes externas (portais públicos e serviços da internet). Eventuais indisponibilidades ou instabilidades dessas fontes podem afetar o resultado "
        "de uma pesquisa, e o relatório correspondente registra a data e a hora em que ela foi feita.",
        "",
        "### 8. FINALIDADE DESTE DOCUMENTO",
        "8.1. Este relatório descreve o sistema, a sua origem, as suas fontes e a sua metodologia, para ser juntado ao processo de contratação e permitir à autoridade competente "
        "conhecer o funcionamento e a procedência dos relatórios de pesquisa de preços gerados pelo AtaCotada.",
    ]
    texto = "\n".join(partes)
    integridade = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    return texto + (
        "\n\n### 9. CÓDIGO DE INTEGRIDADE\n"
        f"9.1. Código SHA-256 do texto deste relatório (itens 1 a 8), gerado em {carimbo}: {integridade[:32]}\n"
        f"9.2. {integridade[32:]}"
    )


def gerar_pdf(ferramentas: list[tuple[str, str, str]], dados: dict | None = None, emitido_em: datetime | None = None) -> bytes:
    return documento_oficial.gerar_pdf(TITULO, corpo(ferramentas, emitido_em), _dados(dados))


def gerar_docx(ferramentas: list[tuple[str, str, str]], dados: dict | None = None, emitido_em: datetime | None = None) -> bytes:
    return documento_oficial.gerar_docx(TITULO, corpo(ferramentas, emitido_em), _dados(dados))


def _dados(dados: dict | None) -> dict:
    dados = dict(dados or {})
    dados["sem_assinatura"] = True  # relatório institucional do sistema: sem NUP e sem signatário
    dados["nup"] = ""
    dados.setdefault("om", OM_PADRAO)
    if not (dados.get("om") or "").strip():
        dados["om"] = OM_PADRAO
    return dados
