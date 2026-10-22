"""Testes offline de servicos_publicos (rodar com: python -m pytest test_servicos_publicos.py)."""
import pandas as pd

import servicos_publicos as sp


def test_cnpj():
    assert sp.cnpj_valido("00.394.460/0058-87")
    assert not sp.cnpj_valido("11111111111111")
    assert not sp.cnpj_valido("00394460005888")
    assert sp.formatar_cnpj("00394460005887") == "00.394.460/0058-87"
    assert sp.formatar_cnpj("123") == "123"


def test_resumo_notas_nao_repete_valor_da_nota():
    df = pd.DataFrame({"CHAVE DE ACESSO": ["a", "a", "a", "b"], "VALOR TOTAL DA NOTA": ["1.000,00"] * 3 + ["500,50"]})
    r = sp.resumo_notas(df)
    assert (r["itens"], r["notas"], r["valor"], r["base"]) == (4, 2, 1500.5, "notas")


def test_resumo_notas_prefere_valor_do_item():
    df = pd.DataFrame({"CHAVE DE ACESSO": ["a", "a", "b"], "VALOR TOTAL": ["100,00", "200,00", "50,25"]})
    r = sp.resumo_notas(df)
    assert (r["notas"], r["valor"], r["base"]) == (2, 350.25, "itens")


def test_separar_vigentes():
    itens = [{"dataVigenciaFinal": "2999-01-01", "maximoAdesao": 10}, {"dataVigenciaFinal": "2999-01-01", "maximoAdesao": 0},
             {"dataVigenciaFinal": "2000-01-01", "maximoAdesao": 10}]
    vigentes, outros = sp.separar_vigentes(itens)
    assert len(vigentes) == 1 and len(outros) == 2


def test_cache_nao_guarda_falha(monkeypatch):
    chamadas = []

    def falha_depois_ok(*a, **k):
        chamadas.append(1)
        return ([], None) if len(chamadas) > 1 else (None, "HTTP 500")
    monkeypatch.setattr(sp, "http_get_json", falha_depois_ok)
    sp._cache.clear()
    assert sp.pncp_search("00394460005887", "ata")[1] is not None
    assert sp.pncp_search("00394460005887", "ata")[1] is None  # a falha não ficou em cache
