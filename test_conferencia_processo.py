"""Testes offline da conferência automática do processo (processo sintético com erros plantados)."""
import io
from datetime import date

import conferencia_processo as C
import documento_oficial as D

BASE = {"om": "Centro de Teste", "cidade": "Rio de Janeiro", "uf": "RJ",
        "assinantes": [{"nome": "Fulano", "posto": "CT", "cargo": "Encarregado"}]}
FORNECEDOR, OUTRO = "12.345.678/0001-95", "98.765.432/0001-98"
PECAS = [
    ("DOCUMENTO DE FORMALIZAÇÃO DE DEMANDA (DFD)", "### 1. NECESSIDADE\nPapel. Documento assinado digitalmente.", date(2026, 3, 2)),
    ("TERMO DE REFERÊNCIA", "### 1. VALOR\nValor estimado total: R$ 52.000,00.\nPrazo: ________.", date(2026, 3, 5)),
    ("MAPA COMPARATIVO DE PREÇOS", "Total geral estimado: R$ 50.000,00.", date(2026, 3, 4)),
    ("PROPOSTA", f"Empresa Papel Ltda, CNPJ {FORNECEDOR}. Valor total R$ 49.000,00.", date(2026, 3, 10)),
    ("CERTIDÃO NEGATIVA DE DÉBITOS", f"Contribuinte CNPJ {OUTRO}. Válida até 01/04/2026.", date(2026, 3, 11)),
    ("NOTA DE CRÉDITO", "Disponibilidade orçamentária: R$ 40.000,00.", date(2026, 3, 12)),
    ("PARECER Nº 10/2026", "Razão da escolha do fornecedor adequada.", date(2026, 4, 20)),
    ("DESPACHO DE AUTORIZAÇÃO", "Autorizo a contratação direta.", date(2026, 4, 15)),
    ("NOTA DE EMPENHO", f"Credor {FORNECEDOR} valor R$ 49.000,00.", date(2026, 4, 22)),
]


def _processo() -> list[dict]:
    arquivos = [(f"{n}.pdf", D.gerar_pdf(t, c, dict(BASE, data=d))) for n, (t, c, d) in enumerate(PECAS)]
    return C.extrair_paginas(arquivos)


def test_identifica_pecas_e_dados():
    r = C.conferir(_processo(), "Dispensa eletrônica (art. 75, I e II)")
    tipos = [d["tipo"] for d in r["docs"]]
    assert tipos == ["dfd", "tr", "mapa", "proposta", "certidao", "orcamento", "parecer", "autorizacao", "empenho"]
    assert r["dados"]["contratado"] == "12345678000195" and r["dados"]["total"] == 50000.0
    assert r["dados"]["referencia"] == date(2026, 4, 22)


def test_aponta_erros_plantados():
    r = C.conferir(_processo(), "Dispensa eletrônica (art. 75, I e II)")
    titulos = {a["titulo"]: a["gravidade"] for a in r["achados"]}
    assert titulos["Crédito orçamentário menor que o valor estimado"] == C.GRAVE
    assert titulos["Certidões de CNPJ diferente do fornecedor escolhido"] == C.GRAVE
    assert titulos["Certidão de regularidade vencida na data de referência"] == C.GRAVE
    assert titulos["Autorização anterior ao parecer jurídico"] == C.GRAVE
    assert titulos["Valor estimado diferente entre o mapa de preços e o TR/ETP"] == C.CORRIGIR
    assert titulos["Campos não preenchidos (lacunas ou marcadores)"] == C.CORRIGIR
    assert r["achados"][0]["gravidade"] == C.GRAVE                      # ordenado por gravidade


def test_checklist_e_relatorio():
    r = C.conferir(_processo(), "Dispensa eletrônica (art. 75, I e II)")
    sit = {c["texto"][:30]: c["situacao"] for c in r["checklist"]}
    assert sit["Documento de Formalização de D"] == "Presente"
    assert sit["Consulta prévia ao CADIN"] == "Não encontrado"
    assert sit["Estudo Técnico Preliminar e an"] == "Verificar"           # facultativo na dispensa por valor
    corpo = C.corpo_relatorio(r, "Dispensa eletrônica (art. 75, I e II)", ["processo.pdf"])
    assert "12.345.678/0001-95" in corpo and "LIMITES DA CONFERÊNCIA" in corpo
    assert D.gerar_pdf("RELATÓRIO", corpo, BASE)[:4] == b"%PDF"


def test_validades_e_valores():
    assert C.validades("Válida até 10/05/2026") == [date(2026, 5, 10)]
    assert C.validades("Validade: 01/05/2026 a 30/05/2026") == [date(2026, 5, 30)]
    assert C.valor_total("Itens R$ 10,00 e R$ 20,00. Valor total: R$ 30,00") == 30.0
    assert C.data_do_documento("Rio de Janeiro, RJ, 1º de março de 2026.") == date(2026, 3, 1)


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
