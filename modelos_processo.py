"""Listas de verificação e modelos de peças do processo de contratação (Lei nº 14.133/2021).

Fica fora da página do Babilaca para poder ser testado sem o Streamlit. Os valores que mudam todo ano (limites de
dispensa) ficam em um só lugar: LIMITES_DISPENSA.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

# ── Limites de dispensa (art. 75, I e II) ─────────────────────────────────────────────────────────────────────
# Atualizados todo ano por decreto (art. 182 da Lei nº 14.133/2021). Ao sair o decreto do ano seguinte, trocar aqui.
LIMITES_DISPENSA = {
    "decreto": "Decreto nº 12.807/2025",
    "vigencia": "1º/01/2026",
    "inciso_I": 130_984.20,   # obras, serviços de engenharia e manutenção de veículos automotores
    "inciso_II": 65_492.11,   # outros serviços e compras
}


def brl(valor: float) -> str:
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def nota_limites() -> str:
    return (f"Limites do art. 75, I ({brl(LIMITES_DISPENSA['inciso_I'])}) e II ({brl(LIMITES_DISPENSA['inciso_II'])}) "
            f"atualizados pelo {LIMITES_DISPENSA['decreto']}, vigentes a partir de {LIMITES_DISPENSA['vigencia']}. "
            "Os valores são corrigidos todo ano: confira o decreto vigente na data da contratação.")


# ── Tipos de documento da aba Documentos (rótulos do seletor) ────────────────────────────────────────────────
DOC_DFD = "DFD — Documento de Formalização de Demanda"
DOC_ETP = "ETP — Estudo Técnico Preliminar"
DOC_RISCOS = "Mapa de Riscos"
DOC_TR = "Termo de Referência"
DOC_TJDL = "TJDL — Termo de Justificativa de Dispensa de Licitação"
DOC_TJIL = "TJIL — Termo de Justificativa de Inexigibilidade de Licitação"
DOC_AVISO = "Aviso de Contratação Direta (dispensa eletrônica)"
DOC_OF_ADESAO = "Ofício — Solicitação de adesão a Ata de Registro de Preços"
DOC_OF_IRP = "Ofício — Manifestação de interesse em IRP"
DOC_MAPA = "Mapa Comparativo de Preços"
DOC_VANTAJOSIDADE = "Relatório de vantajosidade da adesão"
DOC_FRACIONAMENTO = "Relatório de verificação de fracionamento"
DOC_MEMORIA = "Memória de Cálculo"

# atalhos das listas de verificação: ("doc", rótulo do seletor) ou ("pag", arquivo da página, rótulo do link)
PAG_COTACAO = ("pag", "pages/Cotação_Rápida.py", "Cotação Rápida")
PAG_CONSULTA = ("pag", "pages/Consulta.py", "Consulta CNPJ (SICAF e sanções)")
PAG_ADESOES = ("pag", "pages/Adesões.py", "Adesões (saldo da ata)")
PAG_RADAR = ("pag", "pages/Radar_de_Licitacoes.py", "Radar de Licitações")
PAG_IPCA = ("pag", "pages/Calculo_IPCA.py", "Cálculo IPCA")

# ── Itens comuns ─────────────────────────────────────────────────────────────────────────────────────────────
L = "Lei nº 14.133/2021"
_DFD_DIRETA = ("Documento de Formalização de Demanda (DFD)", f"{L}, art. 72, I", ("doc", DOC_DFD))
_ETP_DIRETA = ("Estudo Técnico Preliminar e análise de riscos, se for o caso (facultativo nas hipóteses do art. 75, I, II, "
               "VII e VIII)", f"{L}, art. 72, I; IN SEGES/ME nº 58/2022, art. 14", ("doc", DOC_ETP))
_TR_DIRETA = ("Termo de Referência", f"{L}, art. 6º, XXIII, e art. 72, I", ("doc", DOC_TR))
_ESTIMATIVA = ("Estimativa da despesa: pesquisa de preços com as fontes do art. 23", f"{L}, art. 23 e art. 72, II; "
               "IN SEGES/ME nº 65/2021", PAG_COTACAO)
_MAPA = ("Mapa comparativo e memória de cálculo do preço estimado", "IN SEGES/ME nº 65/2021", ("doc", DOC_MAPA))
_ORCAMENTO_DIRETA = ("Demonstração da compatibilidade da previsão de recursos orçamentários com o compromisso a ser "
                     "assumido (nota de crédito / indicação de dotação)", f"{L}, art. 72, IV, e art. 150", None)
_HABILITACAO = ("Comprovação de que o contratado preenche os requisitos de habilitação e qualificação mínima "
                "(SICAF e certidões)", f"{L}, art. 72, V, e arts. 62 a 70", PAG_CONSULTA)
_SANCOES = ("Consulta ao CEIS e ao CNEP e certidões negativas de inidoneidade, de impedimento e de débitos trabalhistas "
            "juntadas ao processo", f"{L}, art. 91, §4º", PAG_CONSULTA)
_CADIN = ("Consulta prévia ao CADIN", "Lei nº 10.522/2002, art. 6º, III", None)
_ESCOLHA = ("Razão da escolha do contratado", f"{L}, art. 72, VI", None)
_PRECO = ("Justificativa de preço", f"{L}, art. 72, VII", None)
_PARECER_DIRETA = ("Parecer jurídico e pareceres técnicos, se for o caso (a análise jurídica pode ser dispensada nas "
                   "hipóteses fixadas em ato da AGU)", f"{L}, art. 72, III, e art. 53, §§4º e 5º", None)
_AUTORIZACAO_DIRETA = ("Autorização da autoridade competente", f"{L}, art. 72, VIII", None)
_DIVULGACAO_DIRETA = ("Divulgação do ato que autoriza a contratação direta ou do extrato do contrato no sítio oficial / "
                      "PNCP", f"{L}, art. 72, parágrafo único, e art. 94, II", None)
_INSTRUMENTO = ("Contrato ou instrumento substitutivo (nota de empenho, quando cabível)", f"{L}, arts. 92 e 95", None)

CHECKLIST: dict[str, list[tuple[str, str, tuple | None]]] = {
    "Pregão Eletrônico": [
        ("Documento de Formalização de Demanda (DFD) e previsão no Plano de Contratações Anual",
         f"{L}, art. 12, VII, e art. 18, caput; Decreto nº 10.947/2022", ("doc", DOC_DFD)),
        ("Estudo Técnico Preliminar (ETP)", f"{L}, art. 18, I e §§1º e 2º; IN SEGES/ME nº 58/2022", ("doc", DOC_ETP)),
        ("Mapa de Riscos (análise dos riscos da licitação e da execução)", f"{L}, art. 18, X", ("doc", DOC_RISCOS)),
        ("Termo de Referência", f"{L}, art. 6º, XXIII, art. 18, II, e art. 40, §1º", ("doc", DOC_TR)),
        ("Estimativa do valor: pesquisa de preços com as fontes do art. 23", f"{L}, art. 18, IV, e art. 23; "
         "IN SEGES/ME nº 65/2021", PAG_COTACAO),
        _MAPA,
        ("Indicação dos créditos orçamentários (dispensada no registro de preços até a contratação)",
         f"{L}, art. 150; Decreto nº 11.462/2023", None),
        ("Justificativa da modalidade, do critério de julgamento e do modo de disputa", f"{L}, art. 18, VIII, e art. 29",
         None),
        ("Minuta do edital e do contrato (preferencialmente os modelos da AGU)", f"{L}, art. 18, V e VI, art. 19, IV, "
         "e art. 25", None),
        ("Designação do agente de contratação / pregoeiro e da equipe de apoio", f"{L}, art. 8º; Decreto nº 11.246/2022",
         None),
        ("Parecer jurídico sobre a minuta do edital", f"{L}, art. 53, caput e §1º", None),
        ("Autorização da autoridade competente para abertura do certame", f"{L}, art. 18", None),
        ("Divulgação do edital no PNCP e do extrato no DOU, respeitado o prazo mínimo (8 dias úteis para bens, "
         "10 para serviços comuns)", f"{L}, art. 54 e art. 55", None),
        ("Ata da sessão pública, propostas e lances", f"{L}, art. 17", PAG_RADAR),
        ("Habilitação do vencedor (SICAF e certidões)", f"{L}, arts. 62 a 70", PAG_CONSULTA),
        _SANCOES,
        _CADIN,
        ("Adjudicação e homologação", f"{L}, art. 71, IV", None),
        ("Contrato / ata assinados e divulgados no PNCP", f"{L}, art. 94", None),
    ],
    "Dispensa eletrônica (art. 75, I e II)": [
        _DFD_DIRETA, _ETP_DIRETA, _TR_DIRETA, _ESTIMATIVA, _MAPA,
        ("Enquadramento no limite do art. 75, I ou II, considerando o somatório do exercício para objetos do mesmo "
         "ramo de atividade (vedado o fracionamento)", f"{L}, art. 75, I e II e §1º; {LIMITES_DISPENSA['decreto']}",
         ("doc", DOC_TJDL)),
        _ORCAMENTO_DIRETA,
        ("Aviso de contratação direta divulgado no sítio oficial por no mínimo 3 dias úteis",
         f"{L}, art. 75, §3º; IN SEGES/ME nº 67/2021", ("doc", DOC_AVISO)),
        ("Propostas e lances registrados no sistema (Compras.gov.br — dispensa eletrônica)", "IN SEGES/ME nº 67/2021",
         None),
        _HABILITACAO, _SANCOES, _CADIN, _ESCOLHA, _PRECO, _PARECER_DIRETA, _AUTORIZACAO_DIRETA, _DIVULGACAO_DIRETA,
        _INSTRUMENTO,
    ],
    "Dispensa de Licitação — outras hipóteses do art. 75 (TJDL)": [
        _DFD_DIRETA, _ETP_DIRETA, _TR_DIRETA,
        ("Termo de Justificativa de Dispensa de Licitação com o inciso do art. 75 que fundamenta a contratação",
         f"{L}, art. 72 e art. 75", ("doc", DOC_TJDL)),
        ("Emergência (inciso VIII): caracterização da urgência, prazo máximo de 1 ano, vedadas prorrogação e "
         "recontratação; providências para a licitação e apuração de responsabilidade", f"{L}, art. 75, VIII e §6º",
         None),
        _ESTIMATIVA, _MAPA, _ORCAMENTO_DIRETA,
        ("Proposta formal do fornecedor", f"{L}, art. 72", None),
        _HABILITACAO, _SANCOES, _CADIN, _ESCOLHA, _PRECO, _PARECER_DIRETA, _AUTORIZACAO_DIRETA, _DIVULGACAO_DIRETA,
        _INSTRUMENTO,
    ],
    "Inexigibilidade de Licitação (TJIL)": [
        _DFD_DIRETA, _ETP_DIRETA, _TR_DIRETA,
        ("Termo de Justificativa de Inexigibilidade com o inciso do art. 74 que fundamenta a contratação",
         f"{L}, art. 72 e art. 74", ("doc", DOC_TJIL)),
        ("Comprovação da inviabilidade de competição: atestado ou contrato de exclusividade, declaração do fabricante "
         "(vedada preferência por marca) ou prova da notória especialização", f"{L}, art. 74, §§1º e 3º", None),
        ("Justificativa de preço: notas fiscais emitidas a outros contratantes em até 1 ano ou outro meio idôneo",
         f"{L}, art. 23, §4º, e art. 72, VII", None),
        _ORCAMENTO_DIRETA,
        ("Proposta formal do fornecedor", f"{L}, art. 72", None),
        _HABILITACAO, _SANCOES, _CADIN, _ESCOLHA, _PARECER_DIRETA, _AUTORIZACAO_DIRETA, _DIVULGACAO_DIRETA,
        _INSTRUMENTO,
    ],
    "Adesão a Ata de Registro de Preços (carona)": [
        ("Documento de Formalização de Demanda (DFD)", f"{L}, art. 18, caput", ("doc", DOC_DFD)),
        ("Estudo Técnico Preliminar (ETP)", f"{L}, art. 18, I; IN SEGES/ME nº 58/2022", ("doc", DOC_ETP)),
        ("Ata gerenciada por órgão ou entidade federal (vedada a adesão de órgão federal a ata estadual, distrital ou "
         "municipal)", f"{L}, art. 86, §8º", PAG_ADESOES),
        ("Ata vigente e saldo para adesão: até 50% dos quantitativos por órgão aderente e, no total, até o dobro do "
         "registrado", f"{L}, art. 84 e art. 86, §§4º e 5º", PAG_ADESOES),
        ("Justificativa da vantagem da adesão", f"{L}, art. 86, §2º, I", None),
        ("Demonstração de que os preços registrados são compatíveis com os de mercado (pesquisa de preços)",
         f"{L}, art. 86, §2º, II, e art. 23", PAG_COTACAO),
        ("Ofício de consulta ao órgão gerenciador", f"{L}, art. 86, §2º, III", ("doc", DOC_OF_ADESAO)),
        ("Aceitação do órgão gerenciador", f"{L}, art. 86, §2º, III; Decreto nº 11.462/2023", None),
        ("Aceitação do fornecedor beneficiário da ata", f"{L}, art. 86, §2º, III", None),
        ("Cópia da ata, do edital e do termo de referência da licitação de origem", "Decreto nº 11.462/2023", None),
        ("Indicação dos créditos orçamentários", f"{L}, art. 150", None),
        ("Regularidade do fornecedor: SICAF, CEIS, CNEP e certidões", f"{L}, art. 91, §4º", PAG_CONSULTA),
        _CADIN,
        ("Parecer jurídico sobre a adesão", f"{L}, art. 53, §4º", None),
        ("Autorização da autoridade competente", f"{L}, art. 86, §2º", None),
        ("Contratação dentro do prazo fixado após a autorização do gerenciador e da vigência da ata; divulgação no "
         "PNCP", f"{L}, art. 94; Decreto nº 11.462/2023", None),
    ],
    "Participação em IRP (Intenção de Registro de Preços)": [
        ("Documento de Formalização de Demanda (DFD)", f"{L}, art. 18, caput", ("doc", DOC_DFD)),
        ("Especificação e estimativa das quantidades da OM, compatíveis com o objeto da IRP", f"{L}, art. 86, caput; "
         "Decreto nº 11.462/2023", None),
        ("Pesquisa de preços, quando exigida pelo órgão gerenciador", f"{L}, art. 23; IN SEGES/ME nº 65/2021",
         PAG_COTACAO),
        ("Manifestação de interesse dentro do prazo da IRP (mínimo de 8 dias úteis)", f"{L}, art. 86, caput",
         PAG_RADAR),
        ("Ofício de manifestação de interesse ao órgão gerenciador", "Decreto nº 11.462/2023", ("doc", DOC_OF_IRP)),
        ("Registro da participação no Compras.gov.br (módulo IRP)", "Decreto nº 11.462/2023", None),
        ("Autorização da autoridade competente para participar", "Decreto nº 11.462/2023", None),
        ("Confirmação da inclusão da OM pelo órgão gerenciador", "Decreto nº 11.462/2023", None),
        ("Acompanhamento do certame e cópia da ata assinada", f"{L}, art. 82 e art. 84", PAG_RADAR),
        ("Indicação dos créditos orçamentários na contratação", f"{L}, art. 150", None),
        ("Contratação (empenho) dentro da vigência da ata e divulgação no PNCP", f"{L}, art. 84 e art. 94", None),
    ],
    "Prorrogação da vigência de Ata de Registro de Preços": [
        ("Ata vigente (prorrogação formalizada antes do término)", f"{L}, art. 84, caput", None),
        ("Pesquisa de preços que comprove que os preços registrados continuam vantajosos", f"{L}, art. 84, caput, e "
         "art. 23", PAG_COTACAO),
        ("Justificativa da necessidade da prorrogação", f"{L}, art. 84", None),
        ("Concordância do fornecedor beneficiário", "Decreto nº 11.462/2023", None),
        ("Manifestação do órgão gerenciador (se não for a própria OM)", "Decreto nº 11.462/2023", None),
        ("Regularidade do fornecedor: SICAF, CEIS, CNEP e certidões", f"{L}, art. 91, §4º", PAG_CONSULTA),
        ("Parecer jurídico", f"{L}, art. 53, §4º", None),
        ("Autorização da autoridade competente", f"{L}, art. 84", None),
        ("Termo de prorrogação da ata assinado e divulgado no PNCP", f"{L}, art. 84 e art. 94", None),
    ],
    "Termo Aditivo": [
        ("Contrato vigente", f"{L}, arts. 105 a 107", None),
        ("Justificativa técnica e/ou econômica da alteração", f"{L}, art. 124", None),
        ("Identificação da hipótese legal: alteração unilateral (art. 124, I) ou por acordo (art. 124, II)",
         f"{L}, art. 124", None),
        ("Acréscimos e supressões dentro dos limites (25%; 50% em reforma)", f"{L}, art. 125", None),
        ("Prorrogação de serviços e fornecimentos contínuos: vantajosidade atestada e previsão no edital",
         f"{L}, art. 107", PAG_COTACAO),
        ("Concordância do contratado, quando exigida", f"{L}, art. 124, II", None),
        ("Antes de prorrogar: regularidade fiscal, CEIS, CNEP e certidões negativas", f"{L}, art. 91, §4º",
         PAG_CONSULTA),
        _CADIN,
        ("Indicação dos créditos orçamentários", f"{L}, art. 150", None),
        ("Parecer jurídico sobre o termo aditivo", f"{L}, art. 53, §4º", None),
        ("Autorização da autoridade competente", f"{L}, art. 124", None),
        ("Termo aditivo assinado (condição para a execução das novas prestações)", f"{L}, art. 132", None),
        ("Divulgação do aditivo no PNCP", f"{L}, art. 94", None),
    ],
    "Apostilamento": [
        ("Contrato vigente", f"{L}, art. 136", None),
        ("Hipótese de apostila: reajuste ou repactuação, compensações ou penalizações financeiras, empenho de dotações "
         "complementares ou alteração de razão social", f"{L}, art. 136", None),
        ("Índice de reajuste previsto no edital e no contrato", f"{L}, art. 25, §7º, e art. 92, V", None),
        ("Interregno mínimo de 1 ano: da data do orçamento estimado (reajuste) ou da proposta / acordo coletivo "
         "(repactuação)", f"{L}, art. 92, §3º, e art. 135", None),
        ("Memória de cálculo do reajuste ou da repactuação", f"{L}, art. 136", PAG_IPCA),
        ("Planilha com os novos valores unitários e globais", f"{L}, art. 136", None),
        ("Indicação dos créditos orçamentários", f"{L}, art. 150", None),
        ("Autorização da autoridade competente e registro da apostila no processo e no Contratos.gov.br",
         f"{L}, art. 136", None),
    ],
}

SITUACOES = ["Pendente", "Presente", "Não se aplica"]


def resumo_checklist(situacoes: list[str]) -> dict:
    """Totais da conferência. Itens 'Não se aplica' saem da base do percentual."""
    presentes = sum(1 for s in situacoes if s == "Presente")
    nao_aplica = sum(1 for s in situacoes if s == "Não se aplica")
    aplicaveis = len(situacoes) - nao_aplica
    return {"presentes": presentes, "pendentes": aplicaveis - presentes, "nao_aplica": nao_aplica,
            "aplicaveis": aplicaveis, "percentual": round(presentes * 100 / aplicaveis) if aplicaveis else 100}


def _celula(texto: str) -> str:
    return (texto or "").replace("|", "/").replace("\n", " ").strip()


def corpo_checklist(modalidade: str, itens: list[tuple], situacoes: list[str], observacoes: list[str],
                    identificacao: dict) -> str:
    """Texto (Markdown) da lista de verificação para o documento_oficial."""
    r = resumo_checklist(situacoes)
    linhas = ["### 1. IDENTIFICAÇÃO DO PROCESSO", f"**Modalidade / tipo de processo:** {modalidade}."]
    for chave, rotulo in (("objeto", "Objeto"), ("valor", "Valor estimado"), ("responsavel", "Responsável pela conferência")):
        linhas.append(f"**{rotulo}:** {(identificacao.get(chave) or '').strip() or '__________'}.")
    linhas += ["", "### 2. DOCUMENTOS E PROVIDÊNCIAS",
               "| Nº | Documento / providência | Fundamento | Situação | Observação |", "|---|---|---|---|---|"]
    for n, ((texto, fundamento, _), sit, obs) in enumerate(zip(itens, situacoes, observacoes), 1):
        linhas.append(f"| {n} | {_celula(texto)} | {_celula(fundamento)} | {sit} | {_celula(obs)} |")
    linhas += ["", "### 3. RESULTADO DA CONFERÊNCIA",
               f"Presentes {r['presentes']} de {r['aplicaveis']} itens aplicáveis ({r['percentual']}%); "
               f"{r['pendentes']} pendente(s); {r['nao_aplica']} item(ns) não se aplica(m) a este processo."]
    pend = [t for (t, _f, _a), s in zip(itens, situacoes) if s == "Pendente"]
    if pend:
        linhas.append("Pendências a sanear antes do prosseguimento:")
        linhas += [f"- {t}" for t in pend]
    if any("art. 75, I" in f for _t, f, _a in itens):
        linhas += ["", "### 4. OBSERVAÇÃO", nota_limites()]
    return "\n".join(linhas)


# ── Dias úteis (prazos do aviso de dispensa, art. 75, §3º, e da IRP, art. 86) ────────────────────────────────
def _pascoa(ano: int) -> date:
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    mes = (h + l_ - 7 * m + 114) // 31
    dia = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


def feriados_nacionais(ano: int) -> set[date]:
    fixos = [(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)]
    return {date(ano, m, d) for m, d in fixos} | {_pascoa(ano) - timedelta(days=2)}  # Sexta-feira Santa


def dias_uteis(inicio: date, fim: date) -> int:
    """Dias úteis contados como no art. 183: exclui o dia do começo e inclui o do vencimento (feriados nacionais)."""
    total, dia = 0, inicio
    while dia < fim:
        dia += timedelta(days=1)
        if dia.weekday() < 5 and dia not in feriados_nacionais(dia.year):
            total += 1
    return total


# ── Modelos por seções (ETP, TJDL, TJIL) ─────────────────────────────────────────────────────────────────────
# Cada seção: (título, orientação para preencher, obrigatória). Seção obrigatória em branco vira lacuna; a não
# obrigatória do ETP vira a justificativa exigida pelo art. 18, §2º.
MODELOS: dict[str, dict] = {
    DOC_ETP: {
        "titulo": "ESTUDO TÉCNICO PRELIMINAR",
        "arquivo": "etp",
        "base": f"{L}, art. 18, §§1º e 2º; IN SEGES/ME nº 58/2022. Estrutura do modelo de ETP da AGU.",
        "consulta": "estudo técnico preliminar art 18 necessidade solução parcelamento",
        "secoes": [
            ("DESCRIÇÃO DA NECESSIDADE", "Problema a resolver, sob a perspectiva do interesse público (art. 18, §1º, I).", True),
            ("PREVISÃO NO PLANO DE CONTRATAÇÕES ANUAL", "Item do PCA ou justificativa da ausência (art. 18, §1º, II).", False),
            ("REQUISITOS DA CONTRATAÇÃO", "Requisitos técnicos, de sustentabilidade, garantia, prazos (art. 18, §1º, III).", False),
            ("ESTIMATIVA DAS QUANTIDADES", "Quantidades com memória de cálculo e documentos de suporte (art. 18, §1º, IV).", True),
            ("LEVANTAMENTO DE MERCADO", "Alternativas possíveis e justificativa técnica e econômica da escolha (art. 18, §1º, V).", False),
            ("ESTIMATIVA DO VALOR DA CONTRATAÇÃO", "Preços unitários referenciais, memória de cálculo e fontes (art. 18, §1º, VI).", True),
            ("DESCRIÇÃO DA SOLUÇÃO COMO UM TODO", "Inclusive manutenção e assistência técnica, quando for o caso (art. 18, §1º, VII).", False),
            ("JUSTIFICATIVA PARA O PARCELAMENTO OU NÃO DA CONTRATAÇÃO", "Itens, lotes ou grupo único e por quê (art. 18, §1º, VIII).", True),
            ("RESULTADOS PRETENDIDOS", "Economicidade e melhor aproveitamento dos recursos (art. 18, §1º, IX).", False),
            ("PROVIDÊNCIAS PRÉVIAS AO CONTRATO", "Adequações, capacitação de fiscais e gestores (art. 18, §1º, X).", False),
            ("CONTRATAÇÕES CORRELATAS E/OU INTERDEPENDENTES", "(art. 18, §1º, XI).", False),
            ("IMPACTOS AMBIENTAIS E MEDIDAS MITIGADORAS", "Logística reversa, descarte, eficiência energética (art. 18, §1º, XII).", False),
            ("POSICIONAMENTO CONCLUSIVO", "Se a contratação é adequada e viável para atender à necessidade (art. 18, §1º, XIII).", True),
        ],
    },
    DOC_TJDL: {
        "titulo": "TERMO DE JUSTIFICATIVA DE DISPENSA DE LICITAÇÃO",
        "arquivo": "tjdl",
        "base": f"{L}, arts. 72 e 75. Elementos do processo de contratação direta (art. 72).",
        "consulta": "dispensa de licitação art 75 art 72 justificativa preço razão escolha",
        "secoes": [
            ("OBJETO", "O que será contratado, quantidades e prazo.", True),
            ("NECESSIDADE DA CONTRATAÇÃO", "Por que a OM precisa do objeto (remete ao DFD).", True),
            ("ENQUADRAMENTO LEGAL", "Inciso do art. 75 e por que o caso se encaixa nele.", True),
            ("RAZÃO DA ESCOLHA DO CONTRATADO", "Art. 72, VI.", True),
            ("JUSTIFICATIVA DO PREÇO", "Comparação com a pesquisa de preços (art. 72, VII, e art. 23).", True),
            ("HABILITAÇÃO DO CONTRATADO", "SICAF, certidões, CEIS/CNEP (art. 72, V, e art. 91, §4º).", True),
            ("DISPONIBILIDADE ORÇAMENTÁRIA", "Nota de crédito, PI, natureza de despesa (art. 72, IV).", True),
            ("CONCLUSÃO", "Proposta de autorização à autoridade competente (art. 72, VIII).", True),
        ],
    },
    DOC_TJIL: {
        "titulo": "TERMO DE JUSTIFICATIVA DE INEXIGIBILIDADE DE LICITAÇÃO",
        "arquivo": "tjil",
        "base": f"{L}, arts. 72 e 74. Elementos do processo de contratação direta (art. 72).",
        "consulta": "inexigibilidade art 74 exclusividade notória especialização justificativa de preço",
        "secoes": [
            ("OBJETO", "O que será contratado, quantidades e prazo.", True),
            ("NECESSIDADE DA CONTRATAÇÃO", "Por que a OM precisa do objeto (remete ao DFD).", True),
            ("ENQUADRAMENTO LEGAL", "Inciso do art. 74 que fundamenta a contratação.", True),
            ("INVIABILIDADE DE COMPETIÇÃO", "Documento que a comprova: atestado/contrato de exclusividade, declaração do "
             "fabricante (art. 74, §1º) ou prova da notória especialização (art. 74, §3º).", True),
            ("RAZÃO DA ESCOLHA DO CONTRATADO", "Art. 72, VI.", True),
            ("JUSTIFICATIVA DO PREÇO", "Notas fiscais emitidas a outros contratantes em até 1 ano ou outro meio idôneo "
             "(art. 23, §4º, e art. 72, VII).", True),
            ("HABILITAÇÃO DO CONTRATADO", "SICAF, certidões, CEIS/CNEP (art. 72, V, e art. 91, §4º).", True),
            ("DISPONIBILIDADE ORÇAMENTÁRIA", "Nota de crédito, PI, natureza de despesa (art. 72, IV).", True),
            ("CONCLUSÃO", "Proposta de autorização à autoridade competente (art. 72, VIII).", True),
        ],
    },
}

HIPOTESES_DISPENSA = {
    "Art. 75, II — outros serviços e compras (até o limite anual)":
        "art. 75, II, da Lei nº 14.133/2021: contratação que envolva valores inferiores a {II}, no caso de outros "
        "serviços e compras ({decreto})",
    "Art. 75, I — obras, serviços de engenharia e manutenção de veículos (até o limite anual)":
        "art. 75, I, da Lei nº 14.133/2021: contratação que envolva valores inferiores a {I}, no caso de obras e "
        "serviços de engenharia ou de serviços de manutenção de veículos automotores ({decreto})",
    "Art. 75, III — licitação deserta ou fracassada há menos de 1 ano":
        "art. 75, III, da Lei nº 14.133/2021: contratação que mantém todas as condições do edital de licitação "
        "realizada há menos de 1 (um) ano, na qual não surgiram licitantes interessados ou não foram apresentadas "
        "propostas válidas, ou as propostas consignaram preços manifestamente superiores aos de mercado",
    "Art. 75, IV, e — hortifrutigranjeiros, pães e perecíveis":
        "art. 75, IV, e, da Lei nº 14.133/2021: compras de hortifrutigranjeiros, pães e outros gêneros perecíveis, no "
        "período necessário para a realização dos processos licitatórios correspondentes, com base no preço do dia",
    "Art. 75, IV, f — alta complexidade tecnológica e defesa nacional":
        "art. 75, IV, f, da Lei nº 14.133/2021: bens ou serviços produzidos ou prestados no País que envolvam, "
        "cumulativamente, alta complexidade tecnológica e defesa nacional",
    "Art. 75, IV, g — materiais de uso das Forças Armadas (padronização / sem similar)":
        "art. 75, IV, g, da Lei nº 14.133/2021: materiais de uso das Forças Armadas, sem similaridade ou de "
        "padronização para apoio logístico dos meios navais, aéreos e terrestres, mediante autorização por ato do "
        "Comandante da Força",
    "Art. 75, IV, h — contingentes em operações de paz no exterior":
        "art. 75, IV, h, da Lei nº 14.133/2021: bens e serviços para atendimento dos contingentes militares das forças "
        "singulares brasileiras empregadas em operações de paz no exterior",
    "Art. 75, IV, i — suprimento de efetivos em estada eventual (movimentação operacional ou adestramento)":
        "art. 75, IV, i, da Lei nº 14.133/2021: abastecimento ou suprimento de efetivos militares em estada eventual de "
        "curta duração em portos, aeroportos ou localidades diferentes de suas sedes, por motivo de movimentação "
        "operacional ou de adestramento",
    "Art. 75, VI — comprometimento da segurança nacional":
        "art. 75, VI, da Lei nº 14.133/2021: contratação que possa acarretar comprometimento da segurança nacional, nos "
        "casos estabelecidos pelo Ministro de Estado da Defesa",
    "Art. 75, VII — guerra, estado de defesa ou de sítio, grave perturbação da ordem":
        "art. 75, VII, da Lei nº 14.133/2021: casos de guerra, estado de defesa, estado de sítio, intervenção federal ou "
        "de grave perturbação da ordem",
    "Art. 75, VIII — emergência ou calamidade pública":
        "art. 75, VIII, da Lei nº 14.133/2021: emergência ou calamidade pública, quando caracterizada urgência de "
        "atendimento de situação que possa ocasionar prejuízo ou comprometer a continuidade dos serviços públicos ou a "
        "segurança de pessoas, obras, serviços, equipamentos e outros bens, limitada às parcelas que possam ser "
        "concluídas no prazo máximo de 1 (um) ano, vedadas a prorrogação e a recontratação (art. 75, §6º)",
    "Outra hipótese do art. 75 (descrever no campo)": "",
}

HIPOTESES_INEXIGIBILIDADE = {
    "Art. 74, I — fornecedor ou representante exclusivo":
        "art. 74, I, da Lei nº 14.133/2021: aquisição de materiais, equipamentos ou gêneros, ou contratação de "
        "serviços, que só possam ser fornecidos por produtor, empresa ou representante comercial exclusivos, "
        "comprovada a exclusividade na forma do §1º, vedada a preferência por marca específica",
    "Art. 74, III — serviço técnico especializado com notória especialização":
        "art. 74, III, da Lei nº 14.133/2021: serviço técnico especializado de natureza predominantemente intelectual, "
        "com profissional ou empresa de notória especialização (§3º)",
    "Art. 74, III, f — treinamento e aperfeiçoamento de pessoal":
        "art. 74, III, f, da Lei nº 14.133/2021: treinamento e aperfeiçoamento de pessoal, com profissional ou empresa "
        "de notória especialização (§3º)",
    "Art. 74, IV — credenciamento":
        "art. 74, IV, da Lei nº 14.133/2021: objeto que deve ou pode ser contratado por meio de credenciamento",
    "Art. 74, V — aquisição ou locação de imóvel":
        "art. 74, V, da Lei nº 14.133/2021: aquisição ou locação de imóvel cujas características de instalações e de "
        "localização tornem necessária sua escolha, observados os requisitos do §5º",
    "Art. 74, II — profissional do setor artístico":
        "art. 74, II, da Lei nº 14.133/2021: contratação de profissional do setor artístico consagrado pela crítica "
        "especializada ou pela opinião pública",
    "Outra situação de inviabilidade de competição (art. 74, caput)": "",
}


def texto_hipotese(hipotese: str, tabela: dict) -> str:
    modelo = tabela.get(hipotese, "")
    return modelo.format(I=brl(LIMITES_DISPENSA["inciso_I"]), II=brl(LIMITES_DISPENSA["inciso_II"]),
                         decreto=LIMITES_DISPENSA["decreto"]) if modelo else ""


def corpo_secoes(modelo: dict, textos: list[str]) -> str:
    """Monta o texto do documento a partir das seções preenchidas."""
    partes = []
    for n, ((titulo, _ajuda, obrigatoria), texto) in enumerate(zip(modelo["secoes"], textos), 1):
        texto = (texto or "").strip()
        if not texto:
            texto = ("__________." if obrigatoria or modelo["arquivo"] != "etp" else
                     "Elemento não contemplado neste estudo. Justificativa: __________ (art. 18, §2º, da Lei nº 14.133/2021).")
        partes.append(f"### {n}. {titulo}\n{texto}")
    return "\n\n".join(partes)


def prompt_secoes(modelo: dict, textos: list[str], contexto: str) -> str:
    """Pedido à IA para completar o documento mantendo a ordem e os títulos das seções."""
    linhas = [f"Elabore o documento \"{modelo['titulo']}\" com base em: {modelo['base']}",
              "Use EXATAMENTE as seções abaixo, nesta ordem, no formato \"### n. TÍTULO\". Aproveite e melhore o texto já "
              "escrito pelo usuário; complete as seções vazias apenas com o que se pode concluir das informações dadas. "
              "Dado que não foi informado (valores, datas, nomes, números de documentos) fica como lacuna \"__________\".",
              ""]
    for n, ((titulo, ajuda, obrigatoria), texto) in enumerate(zip(modelo["secoes"], textos), 1):
        linhas.append(f"### {n}. {titulo} {'(obrigatória)' if obrigatoria else '(se não se aplicar, justificar)'}")
        linhas.append(f"Orientação: {ajuda}")
        linhas.append(f"Texto do usuário: {(texto or '').strip() or '(vazio)'}")
        linhas.append("")
    if contexto.strip():
        linhas += ["CONTEXTO INFORMADO PELO USUÁRIO:", contexto.strip()]
    return "\n".join(linhas)


# ── Mapa de Riscos ───────────────────────────────────────────────────────────────────────────────────────────
NIVEIS = {"Baixa": 1, "Média": 2, "Alta": 3, "Baixo": 1, "Médio": 2, "Alto": 3}
RISCOS_PADRAO = [
    {"Fase": "Planejamento", "Risco": "Especificação técnica deficiente ou restritiva", "Probabilidade": "Média",
     "Impacto": "Alto", "Ação preventiva": "Revisar o TR com a área técnica; usar o CATMAT ou CATSER adequado",
     "Ação de contingência": "Retificar o edital ou o aviso e reabrir o prazo", "Responsável": "Equipe de planejamento"},
    {"Fase": "Planejamento", "Risco": "Preço estimado inadequado (sobrepreço ou inexequível)", "Probabilidade": "Média",
     "Impacto": "Alto", "Ação preventiva": "Pesquisa com as fontes do art. 23 e da IN SEGES/ME nº 65/2021",
     "Ação de contingência": "Refazer a pesquisa e sanear o preço de referência", "Responsável": "Setor de obtenção"},
    {"Fase": "Seleção do fornecedor", "Risco": "Licitação deserta ou fracassada", "Probabilidade": "Média",
     "Impacto": "Alto", "Ação preventiva": "Ampla divulgação, prazos adequados e consulta prévia ao mercado",
     "Ação de contingência": "Repetir o certame ou contratar com base no art. 75, III",
     "Responsável": "Agente de contratação"},
    {"Fase": "Seleção do fornecedor", "Risco": "Vencedor impedido ou sem habilitação", "Probabilidade": "Baixa",
     "Impacto": "Alto", "Ação preventiva": "Consultar SICAF, CEIS, CNEP e certidões (art. 91, §4º)",
     "Ação de contingência": "Convocar o licitante seguinte na ordem de classificação",
     "Responsável": "Agente de contratação"},
    {"Fase": "Gestão do contrato", "Risco": "Atraso ou inexecução da entrega", "Probabilidade": "Média",
     "Impacto": "Alto", "Ação preventiva": "Prazos claros no TR, acompanhamento e notificação tempestiva",
     "Ação de contingência": "Aplicar as sanções dos arts. 155 e 156 e convocar o remanescente",
     "Responsável": "Fiscal do contrato"},
    {"Fase": "Gestão do contrato", "Risco": "Material entregue fora da especificação", "Probabilidade": "Média",
     "Impacto": "Médio", "Ação preventiva": "Recebimento provisório com conferência técnica (art. 140)",
     "Ação de contingência": "Recusar e exigir a substituição às custas do contratado",
     "Responsável": "Fiscal técnico"},
    {"Fase": "Gestão do contrato", "Risco": "Insuficiência de crédito orçamentário", "Probabilidade": "Baixa",
     "Impacto": "Alto", "Ação preventiva": "Indicar o crédito antes da contratação (art. 150)",
     "Ação de contingência": "Reduzir o quantitativo ou solicitar remanejamento", "Responsável": "Execução financeira"},
]
COLUNAS_RISCO = ["Fase", "Risco", "Probabilidade", "Impacto", "Ação preventiva", "Ação de contingência", "Responsável"]


def nivel_risco(probabilidade: str, impacto: str) -> str:
    v = NIVEIS.get(probabilidade or "", 0) * NIVEIS.get(impacto or "", 0)
    return "Alto" if v >= 6 else "Médio" if v >= 3 else "Baixo" if v else "-"


def corpo_mapa_riscos(objeto: str, riscos: list[dict]) -> str:
    riscos = [r for r in riscos if (r.get("Risco") or "").strip()]
    linhas = ["### 1. OBJETO", (objeto or "").strip() or "__________.",
              "", "### 2. METODOLOGIA",
              "Os riscos foram identificados para as fases de planejamento, seleção do fornecedor e gestão do contrato, "
              "nos termos do art. 18, X, da Lei nº 14.133/2021. O nível de cada risco resulta da combinação da "
              "probabilidade com o impacto (Baixa/Baixo = 1, Média/Médio = 2, Alta/Alto = 3): produto até 2 = baixo; "
              "3 ou 4 = médio; 6 ou 9 = alto.",
              "", "### 3. RISCOS IDENTIFICADOS",
              "| Nº | Fase | Risco | Prob. | Impacto | Nível | Ação preventiva | Ação de contingência | Responsável |",
              "|---|---|---|---|---|---|---|---|---|"]
    for n, r in enumerate(riscos, 1):
        linhas.append("| " + " | ".join([str(n), _celula(r.get("Fase")), _celula(r.get("Risco")),
                                         _celula(r.get("Probabilidade")), _celula(r.get("Impacto")),
                                         nivel_risco(r.get("Probabilidade"), r.get("Impacto")),
                                         _celula(r.get("Ação preventiva")), _celula(r.get("Ação de contingência")),
                                         _celula(r.get("Responsável"))]) + " |")
    altos = [r["Risco"].strip() for r in riscos if nivel_risco(r.get("Probabilidade"), r.get("Impacto")) == "Alto"]
    linhas += ["", "### 4. ACOMPANHAMENTO",
               "O mapa será revisto ao fim de cada fase da contratação e sempre que surgir risco novo, e as ações "
               "registradas no processo."]
    if altos:
        linhas.append("Riscos de nível alto, que exigem acompanhamento prioritário:")
        linhas += [f"- {a}" for a in altos]
    return "\n".join(linhas)


# ── Aviso de contratação direta (dispensa eletrônica) ───────────────────────────────────────────────────────
def corpo_aviso(a: dict) -> str:
    """a: numero, objeto, hipotese_txt, valor, sigiloso, inicio, fim (datetime), criterio, exclusiva_me,
    prazo_entrega, local_entrega, habilitacao, pagamento, contato, uasg."""
    fmt = lambda dt: dt.strftime("%d/%m/%Y, às %Hh%M") if dt else "__________"
    valor = ("Sigiloso, nos termos do art. 24 da Lei nº 14.133/2021." if a.get("sigiloso") else
             (brl(a["valor"]) + "." if a.get("valor") else "__________."))
    me = ("Participação exclusiva de microempresas, empresas de pequeno porte e equiparadas, nos termos do art. 48, I, "
          "da Lei Complementar nº 123/2006." if a.get("exclusiva_me") else
          "Participação ampla, aplicados os benefícios da Lei Complementar nº 123/2006 às microempresas e empresas de "
          "pequeno porte.")
    return "\n".join([
        "### 1. OBJETO",
        f"{(a.get('objeto') or '').strip() or '__________'}, conforme especificações e quantidades do Termo de "
        "Referência anexo a este aviso.",
        "", "### 2. FUNDAMENTO LEGAL",
        f"Contratação direta com fundamento no {a.get('hipotese_txt') or 'art. 75 da Lei nº 14.133/2021'}, processada "
        "na forma de dispensa eletrônica (art. 75, §3º, da Lei nº 14.133/2021 e IN SEGES/ME nº 67/2021).",
        "", "### 3. VALOR ESTIMADO", valor,
        "", "### 4. ENVIO DE PROPOSTAS",
        f"As propostas serão recebidas exclusivamente pelo sistema Compras.gov.br (UASG {a.get('uasg') or '__________'}), "
        f"de {fmt(a.get('inicio'))} até {fmt(a.get('fim'))} (horário de Brasília). O prazo de divulgação não é inferior a "
        "3 (três) dias úteis (art. 75, §3º).",
        "", "### 5. PARTICIPAÇÃO", me,
        "", "### 6. CRITÉRIO DE JULGAMENTO E LANCES",
        f"Critério de julgamento: {a.get('criterio') or 'menor preço'}. Encerrado o prazo de propostas, haverá disputa por "
        "lances no sistema, e será selecionada a proposta mais vantajosa.",
        "", "### 7. HABILITAÇÃO",
        (a.get("habilitacao") or "").strip() or
        "Regularidade no SICAF; certidões de regularidade fiscal, social e trabalhista; ausência de registros "
        "impeditivos no CEIS e no CNEP (art. 91, §4º, da Lei nº 14.133/2021).",
        "", "### 8. ENTREGA E PAGAMENTO",
        f"Prazo de entrega: {(a.get('prazo_entrega') or '').strip() or '__________'}. Local: "
        f"{(a.get('local_entrega') or '').strip() or '__________'}. "
        f"{(a.get('pagamento') or '').strip() or 'Pagamento em até 30 (trinta) dias após o recebimento definitivo e o ateste da nota fiscal.'}",
        "", "### 9. SANÇÕES",
        "O fornecedor que não mantiver a proposta, não assinar o contrato ou não entregar o objeto ficará sujeito às "
        "sanções dos arts. 155 e 156 da Lei nº 14.133/2021.",
        "", "### 10. DISPOSIÇÕES GERAIS",
        f"Esclarecimentos: {(a.get('contato') or '').strip() or '__________'}. Integra este aviso, como anexo, o Termo de "
        "Referência.",
    ])


# ── Ofícios ───────────────────────────────────────────────────────────────────────────────────────────────────
def _tabela_itens(itens: list[dict]) -> list[str]:
    itens = [i for i in itens if (i.get("Descrição") or "").strip()]
    if not itens:
        return ["| Item | Descrição | Unidade | Quantidade |", "|---|---|---|---|", "| __ | __________ | __ | __ |"]
    linhas = ["| Item | Descrição | Unidade | Quantidade |", "|---|---|---|---|"]
    for n, i in enumerate(itens, 1):
        linhas.append(f"| {_celula(str(i.get('Item') or n))} | {_celula(i.get('Descrição'))} | "
                      f"{_celula(i.get('Unidade'))} | {_celula(str(i.get('Quantidade') or ''))} |")
    return linhas


def corpo_oficio_adesao(o: dict) -> str:
    """o: gerenciador, ata, licitacao, uasg, objeto, justificativa, fornecedor_ciente, contato, itens."""
    lacuna = "__________"
    ciente = ("O fornecedor beneficiário já manifestou concordância com o fornecimento, conforme documento anexo."
              if o.get("fornecedor_ciente") else
              "O fornecedor beneficiário será consultado sobre a aceitação do fornecimento após a manifestação desse "
              "órgão gerenciador.")
    return "\n\n".join([
        f"1. Solicito a autorização desse órgão gerenciador ({o.get('gerenciador') or lacuna}) para que esta Organização "
        f"Militar adira, na condição de órgão não participante, à Ata de Registro de Preços nº {o.get('ata') or lacuna}, "
        f"decorrente do {o.get('licitacao') or lacuna} (UASG {o.get('uasg') or lacuna}), cujo objeto é "
        f"{o.get('objeto') or lacuna}, nos termos do art. 86, §2º, da Lei nº 14.133/2021 e do Decreto nº 11.462/2023.",
        f"2. A adesão se justifica porque {(o.get('justificativa') or lacuna).rstrip('.')}."
        + ("" if "foram comparados" in (o.get("justificativa") or "") else
           " Os preços registrados foram comparados com os praticados no mercado, conforme pesquisa realizada nos "
           "termos do art. 23 da Lei nº 14.133/2021, e mostraram-se vantajosos para a Administração."),
        "3. Os itens e as quantidades pretendidos são os seguintes, observado o limite de 50% dos quantitativos "
        "registrados por órgão aderente (art. 86, §4º, da Lei nº 14.133/2021):\n\n" + "\n".join(_tabela_itens(o.get("itens") or [])),
        f"4. {ciente} Autorizada a adesão, a contratação será efetivada no prazo regulamentar, observada a vigência da ata.",
        f"5. Ponto de contato desta OM: {o.get('contato') or lacuna}.",
    ])


def corpo_oficio_irp(o: dict) -> str:
    """o: gerenciador, irp, uasg, objeto, prazo, justificativa, local_entrega, contato, itens."""
    lacuna = "__________"
    return "\n\n".join([
        f"1. Em atenção à Intenção de Registro de Preços nº {o.get('irp') or lacuna}, divulgada por esse órgão "
        f"gerenciador ({o.get('gerenciador') or lacuna}, UASG {o.get('uasg') or lacuna}), cujo objeto é "
        f"{o.get('objeto') or lacuna}, manifesto o interesse desta Organização Militar em participar do registro de "
        "preços, na condição de órgão participante, nos termos do art. 86 da Lei nº 14.133/2021 e do Decreto nº "
        "11.462/2023.",
        "2. A estimativa de consumo desta OM é a seguinte:\n\n" + "\n".join(_tabela_itens(o.get("itens") or [])),
        f"3. A participação se justifica porque {(o.get('justificativa') or lacuna).rstrip('.')}. Esta OM concorda com o "
        "objeto a ser licitado e com as condições do termo de referência elaborado pelo órgão gerenciador.",
        f"4. A manifestação de interesse foi registrada no Compras.gov.br dentro do prazo da IRP, que se encerra em "
        f"{o.get('prazo') or lacuna}. Local de entrega: {o.get('local_entrega') or lacuna}.",
        f"5. Ponto de contato desta OM: {o.get('contato') or lacuna}.",
    ])


def nome_arquivo(texto: str) -> str:
    texto = re.sub(r"[^\w]+", "_", (texto or "").lower(), flags=re.UNICODE).strip("_")
    return texto[:60] or "documento"

# ordem de exibição no seletor
CHECKLIST = {k: CHECKLIST[k] for k in (
    "Dispensa eletrônica (art. 75, I e II)", "Pregão Eletrônico", "Dispensa de Licitação — outras hipóteses do art. 75 (TJDL)",
    "Inexigibilidade de Licitação (TJIL)", "Adesão a Ata de Registro de Preços (carona)",
    "Participação em IRP (Intenção de Registro de Preços)", "Prorrogação da vigência de Ata de Registro de Preços",
    "Termo Aditivo", "Apostilamento")}


# ── Mapa comparativo de preços ───────────────────────────────────────────────────────────────────────────────
def _mediana(valores: list[float]) -> float:
    v = sorted(valores)
    if not v:
        return 0.0
    meio = len(v) // 2
    return v[meio] if len(v) % 2 else (v[meio - 1] + v[meio]) / 2


def linhas_mapa(itens: list[dict]) -> list[dict]:
    """Calcula média, mediana, menor preço e total estimado (pela média) de cada item."""
    linhas = []
    for n, item in enumerate(itens, 1):
        precos = [float(item.get(f"preco{j}") or 0) for j in (1, 2, 3)]
        validos = [p for p in precos if p > 0]
        qtd = float(item.get("quantidade") or 1)
        media = sum(validos) / len(validos) if validos else 0.0
        linhas.append({"n": n, "descricao": str(item.get("descricao") or "").strip(), "quantidade": qtd,
                       "precos": precos, "validos": len(validos), "media": media, "mediana": _mediana(validos),
                       "menor": min(validos) if validos else 0.0, "total": media * qtd})
    return linhas


def _qtd_txt(q: float) -> str:
    return str(int(q)) if float(q).is_integer() else f"{q:.2f}".replace(".", ",")


def corpo_mapa_comparativo(itens: list[dict], observacoes: str = "") -> str:
    linhas_calc = linhas_mapa(itens)
    total = sum(l["total"] for l in linhas_calc)
    v = lambda x: brl(x) if x else "-"
    linhas = ["### 1. PREÇOS PESQUISADOS",
              "| Item | Descrição | Qtd | Fornecedor 1 | Fornecedor 2 | Fornecedor 3 | Média | Mediana | Total estimado |",
              "|---|---|---|---|---|---|---|---|---|"]
    for l in linhas_calc:
        linhas.append("| " + " | ".join([str(l["n"]), _celula(l["descricao"]) or "__________", _qtd_txt(l["quantidade"]),
                                         *[v(p) for p in l["precos"]], v(l["media"]), v(l["mediana"]),
                                         v(l["total"])]) + " |")
    linhas.append(f"| | **TOTAL GERAL ESTIMADO** | | | | | | | **{brl(total)}** |")
    poucos = [str(l["n"]) for l in linhas_calc if 0 < l["validos"] < 3]
    linhas += ["", "### 2. METODOLOGIA",
               "O preço estimado de cada item corresponde à média dos preços válidos obtidos na pesquisa, realizada nos "
               "termos do art. 23 da Lei nº 14.133/2021 e da IN SEGES/ME nº 65/2021. O total estimado é o produto do "
               "preço médio pela quantidade. A mediana é apresentada para conferência da dispersão dos preços.",
               f"Valor total estimado da contratação: **{brl(total)}**."]
    if poucos:
        linhas.append(f"Itens com menos de 3 preços válidos ({', '.join(poucos)}): justificar no processo a "
                      "impossibilidade de obter mais cotações.")
    if (observacoes or "").strip():
        linhas += ["", "### 3. OBSERVAÇÕES", observacoes.strip()]
    return "\n".join(linhas)


# ── Calculadora de prazos (contados em dias úteis, art. 183) ─────────────────────────────────────────────────
def eh_util(dia: date) -> bool:
    return dia.weekday() < 5 and dia not in feriados_nacionais(dia.year)


def somar_dias_uteis(inicio: date, n: int) -> date:
    """Data que fica n dias úteis depois (n > 0) ou antes (n < 0) de 'inicio', sem contar o próprio dia de início."""
    passo = 1 if n >= 0 else -1
    dia, faltam = inicio, abs(n)
    while faltam:
        dia += timedelta(days=passo)
        if eh_util(dia):
            faltam -= 1
    return dia


# (rótulo, dias úteis, sentido, data-base pedida, o que a data calculada significa, fundamento)
# sentido +1: prazo conta para a frente a partir da data-base; -1: termina antes da data-base.
PRAZOS = [
    ("Edital — bens, menor preço ou maior desconto", 8, 1, "Data de divulgação do edital",
     "Primeira data possível para a abertura (apresentação das propostas)", f"{L}, art. 55, I, a"),
    ("Edital — bens, demais critérios", 15, 1, "Data de divulgação do edital",
     "Primeira data possível para a abertura", f"{L}, art. 55, I, b"),
    ("Edital — serviços comuns e obras/serviços comuns de engenharia, menor preço ou maior desconto", 10, 1,
     "Data de divulgação do edital", "Primeira data possível para a abertura", f"{L}, art. 55, II, a"),
    ("Edital — serviços especiais e obras/serviços especiais de engenharia, menor preço ou maior desconto", 25, 1,
     "Data de divulgação do edital", "Primeira data possível para a abertura", f"{L}, art. 55, II, b"),
    ("Edital — maior lance (leilão)", 15, 1, "Data de divulgação do edital",
     "Primeira data possível para a abertura", f"{L}, art. 55, III"),
    ("Edital — técnica e preço ou melhor técnica / conteúdo artístico", 35, 1, "Data de divulgação do edital",
     "Primeira data possível para a abertura", f"{L}, art. 55, IV"),
    ("Aviso de contratação direta (dispensa eletrônica)", 3, 1, "Data de divulgação do aviso",
     "Primeira data possível para encerrar o recebimento de propostas", f"{L}, art. 75, §3º"),
    ("Intenção de Registro de Preços (IRP)", 8, 1, "Data de divulgação da IRP",
     "Primeira data possível para encerrar a manifestação de interesse", f"{L}, art. 86, caput"),
    ("Impugnação ou pedido de esclarecimento ao edital", -3, -1, "Data de abertura do certame",
     "Último dia para impugnar ou pedir esclarecimento", f"{L}, art. 164, caput"),
    ("Resposta à impugnação / esclarecimento", -1, -1, "Data de abertura do certame",
     "Último dia para a Administração responder (prazo de até 3 dias úteis, limitado a este dia)",
     f"{L}, art. 164, parágrafo único"),
    ("Recurso (razões) contra julgamento ou habilitação", 3, 1, "Data da intimação ou da lavratura da ata",
     "Último dia para apresentar as razões do recurso", f"{L}, art. 165, I e §1º"),
    ("Contrarrazões ao recurso", 3, 1, "Data da intimação ou divulgação da interposição do recurso",
     "Último dia para as contrarrazões", f"{L}, art. 165, §4º"),
    ("Reconsideração pelo agente de contratação", 3, 1, "Data do recebimento do recurso",
     "Último dia para reconsiderar ou encaminhar à autoridade superior", f"{L}, art. 165, §2º"),
    ("Decisão do recurso pela autoridade superior", 10, 1, "Data do recebimento dos autos",
     "Último dia para a decisão", f"{L}, art. 165, §2º"),
    ("Divulgação do contrato no PNCP — licitação", 20, 1, "Data da assinatura do contrato",
     "Último dia para divulgar (condição de eficácia)", f"{L}, art. 94, I"),
    ("Divulgação do contrato no PNCP — contratação direta", 10, 1, "Data da assinatura do contrato",
     "Último dia para divulgar (condição de eficácia)", f"{L}, art. 94, II"),
    ("Defesa no processo de sanção (multa, impedimento, inidoneidade)", 15, 1, "Data da intimação do licitante",
     "Último dia para a defesa", f"{L}, arts. 157 e 158"),
    ("Recurso contra sanção de advertência, multa ou impedimento", 15, 1, "Data da intimação da sanção",
     "Último dia para o recurso", f"{L}, art. 166"),
    ("Pedido de reconsideração da declaração de inidoneidade", 15, 1, "Data da intimação da sanção",
     "Último dia para o pedido", f"{L}, art. 167"),
]
PRAZOS_POR_ROTULO = {p[0]: p for p in PRAZOS}


def calcular_prazo(rotulo: str, base: date) -> dict:
    _r, dias, _s, nome_base, significado, fundamento = PRAZOS_POR_ROTULO[rotulo]
    alvo = somar_dias_uteis(base, dias)
    return {"data": alvo, "dias": dias, "base": nome_base, "significado": significado, "fundamento": fundamento,
            "base_util": eh_util(base)}


# ── Revisão pela IA de textos montados pelo sistema (aviso e ofícios) ────────────────────────────────────────
_REGRAS_REVISAO = {
    "aviso": "Mantenha EXATAMENTE as seções \"### n. TÍTULO\" e a ordem. Melhore a descrição do objeto e complete "
             "condições de entrega, habilitação e disposições com o contexto informado.",
    "oficio": "É um Ofício da Marinha (MaTDoc cap. 16): itens numerados \"1.\", \"2.\"... SEM títulos, SEM vocativo, "
              "SEM fecho de cortesia e SEM assinatura (o sistema monta cabeçalho e assinatura). Primeiro item expõe o "
              "fato, os seguintes analisam e o último solicita ou conclui. Mantenha a tabela de itens como está.",
    "oficio_externo": "É um Ofício Externo (MaTDoc cap. 17) para órgão fora da Marinha: parágrafos numerados \"1.\", "
                      "\"2.\"... SEM vocativo e SEM fecho (o sistema já os coloca), SEM assinatura. Tratamento formal "
                      "e por extenso. Mantenha a tabela de itens como está.",
}


def prompt_revisar(corpo: str, contexto: str, tipo: str) -> str:
    """Pedido à IA para revisar e completar um texto que o sistema já montou com os dados do formulário."""
    return "\n".join([
        "Revise e complete o texto abaixo em redação oficial: linguagem impessoal, culta, clara e concisa.",
        _REGRAS_REVISAO[tipo],
        "Preserve todos os números, datas, valores, CNPJ, UASG e nomes que já constam. Não invente dados: o que faltar "
        "fica como \"__________\". Não acrescente citações legais além das que já estão no texto.",
        "", "TEXTO-BASE:", corpo, "",
        "CONTEXTO INFORMADO PELO USUÁRIO:", (contexto or "").strip() or "(nenhum)",
    ])
