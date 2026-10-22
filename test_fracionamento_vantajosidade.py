"""Testes offline do detector de fracionamento e da vantajosidade da adesão (sem rede)."""
import fracionamento as F
import modelos_processo as MP
import vantajosidade as V

FAMILIAS = {"PAPEL A4": ("127", "PAPEL A4", "ARTIGOS PARA ESCRITÓRIO"),
            "SALGADOS DIVERSOS": ("11919", "SALGADOS DIVERSOS", "PANIFICAÇÃO"), "PAPEL": ("1", "PAPEL", "X")}


def test_ramo_pelo_pdm_mais_longo_e_servico_aproximado():
    r = F.ramo_do_item("PAPEL A4, GRAMATURA: 75 G/M2", True, FAMILIAS)
    assert r["ramo"] == "PAPEL A4" and r["base"] == "PDM (CATMAT)"
    assert F.ramo_do_item("Salgados Diversos aplicação: coquetel", True, FAMILIAS)["chave"] == "PDM 11919"
    s = F.ramo_do_item("Manutenção de Veículos Pesados", False, FAMILIAS)
    assert s["base"] == "descrição (aproximado)" and s["ramo"] == "MANUTENCAO VEICULOS PESADOS"


def test_inciso():
    assert F.inciso("Lei 14.133/2021, Art. 75, II") == "II"
    assert F.inciso("Lei 14.133/2021, Art. 75, I") == "I"
    assert F.inciso("Lei 14.133/2021, Art. 75, VIII") is None and F.inciso("Lei 13.303/2016, Art. 29, II") is None


def _compra(n, valor, desc="PAPEL A4, GRAMATURA: 75", sit="Homologado"):
    return {"idCompra": str(n), "numeroControlePNCP": f"c{n}", "amparoLegalNome": "Lei 14.133/2021, Art. 75, II",
            "_itens": [{"descricaoResumida": desc, "materialOuServico": "M", "temResultado": True,
                        "valorTotalResultado": valor, "situacaoCompraItemNome": sit}]}


def test_consolidar_soma_por_ramo_e_ignora_cancelados():
    grupos = F.consolidar([_compra(1, 40000), _compra(2, 30000), _compra(3, 99999, sit="Cancelado"),
                           _compra(4, 5000, "Salgados Diversos aplicação: x")], FAMILIAS)
    papel = next(g for g in grupos if g["ramo"] == "PAPEL A4")
    assert papel["total"] == 70000 and len(papel["compras"]) == 2 and papel["situacao"].startswith("🔴")
    assert grupos[0]["ramo"] == "PAPEL A4"                                  # ordenado pelo uso do limite
    sim = F.simular(grupos, "PAPEL A4, COR: BRANCA", 1000, True, familias=FAMILIAS)
    assert sim["ja_contratado"] == 70000 and not sim["cabe"]
    corpo = F.corpo_relatorio("123", "OM", 2026, grupos, [])
    assert "PAPEL A4" in corpo and "fracionamento" in corpo


def test_saneamento_e_analise():
    aceitos, fora = V.sanear([100, 110, 90, 400, 10])
    assert fora == [400, 10] and sorted(aceitos) == [90, 100, 110]
    fontes = [{"fonte": "Ata", "orgao": "X", "referencia": "1", "valor": v, "data": ""} for v in (100, 110, 90)]
    r = V.analisar_item({"Item": "1", "Descrição": "Papel", "preco": 80, "Quantidade": "10"}, fontes)
    # estimativa = preço da ata (80): aceita de 40 a 104 -> 90 e 100 (110 fica fora)
    assert r["mediana"] == 95 and r["economia"] == 150 and r["situacao"].startswith("✅")
    aceitos, fora, _ = V.selecionar([539, 560, 1680, 3100, 550, 200], 600)
    assert aceitos == [539, 550, 560] and sorted(fora) == [200, 1680, 3100]
    assert V.selecionar(list(range(500, 520)), 500)[0] == list(range(500, 510))     # até 10, os menores
    compat = V.analisar_item({"Item": "2", "Descrição": "X", "preco": 105, "Quantidade": 1}, fontes)
    assert compat["classe"] == "compativel" and "compatível com os valores praticados no mercado" in V.justificativa_item(compat)
    caro = V.analisar_item({"Item": "2", "Descrição": "X", "preco": 130, "Quantidade": 1}, fontes)
    assert caro["classe"] == "acima" and caro["situacao"].startswith("🔴")
    manual = V.analisar_item({"Item": "4", "Descrição": "Z", "preco": 9, "Quantidade": 1, "ref_manual": 10}, [])
    assert manual["mediana"] == 10 and manual["manual"] and manual["classe"] == "vantajoso"
    sem = V.analisar_item({"Item": "3", "Descrição": "Y", "preco": 5, "Quantidade": 1}, [])
    assert sem["mediana"] is None and sem["classe"] == "sem_ref" and "__________" in V.justificativa_item(sem)
    assert V.semelhanca("MESA, MATERIAL ESTRUTURA METAL, TAMPO MDF", "MESA, MATERIAL ESTRUTURA METAL, TAMPO MDP") > 0.5


def test_justificativa_e_relatorio():
    fontes = [{"fonte": "Ata", "orgao": "X", "referencia": "1", "valor": v, "data": ""} for v in (100, 110, 90)]
    res = [V.analisar_item({"Item": "1", "Descrição": "Papel", "preco": 80, "Quantidade": 10}, fontes)]
    txt = V.texto_justificativa(res, "12/2026")
    assert "R$ 150,00" in txt and "15,8%" in txt and "foram comparados" in txt
    corpo = V.corpo_relatorio({"ata": "12/2026", "gerenciador": "G", "uasg": "1", "licitacao": "PE"}, res)
    assert "**R$ 800,00**" in corpo and "FONTES CONSULTADAS" in corpo and "JUSTIFICATIVA POR ITEM" in corpo
    assert "entre 50% e 130%" in corpo
    oficio = MP.corpo_oficio_adesao({"justificativa": txt})
    assert "foram comparados" in oficio and "mostraram-se vantajosos" not in oficio


if __name__ == "__main__":
    for nome, f in list(globals().items()):
        if nome.startswith("test_"):
            f()
            print("ok", nome)
