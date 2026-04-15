#!/usr/bin/env python3
"""Testa endpoints PNCP — foco em compras/pregão aberto p/ adesão e atas."""
import requests
import json
import urllib3
urllib3.disable_warnings()

CNPJ = "34954091000116"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
TIMEOUT = 20

def test(label, url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT, verify=False)
        print(f"\n[{r.status_code}] {label}")
        print(f"  URL: {r.url[:150]}")
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict):
                total = d.get('totalRegistros', d.get('total', d.get('totalElements', '?')))
                print(f"  total: {total}")
                items = d.get('resultado', d.get('data', d.get('items', d.get('content', []))))
                if items and len(items) > 0:
                    print(f"  keys[0]: {list(items[0].keys())[:12]}")
                    print(f"  sample: {json.dumps(items[0], ensure_ascii=False)[:400]}")
                else:
                    print(f"  keys: {list(d.keys())[:12]}")
            elif isinstance(d, list):
                print(f"  list len: {len(d)}")
                if d:
                    print(f"  keys[0]: {list(d[0].keys())[:12]}")
                    print(f"  sample: {json.dumps(d[0], ensure_ascii=False)[:400]}")
        else:
            print(f"  body: {r.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"\n[TIMEOUT] {label}")
    except Exception as e:
        print(f"\n[ERROR] {label}: {e}")

print("=" * 70)
print(f"CNPJ como ORGAO (contratante): {CNPJ}")
print("=" * 70)

# PNCP pncp-api: compras do orgao (CNPJ como orgao contratante)
test("pncp-api: compras do orgao abertas para adesao",
     f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/compras",
     {"abertoParaAdesao": "true", "pagina": 1, "tamanhoPagina": 5})

test("pncp-api: todas compras do orgao",
     f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/compras",
     {"pagina": 1, "tamanhoPagina": 5})

test("pncp-api: atas do orgao",
     f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/atas",
     {"pagina": 1, "tamanhoPagina": 5})

test("pncp-api: contratos do orgao",
     f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/contratos",
     {"pagina": 1, "tamanhoPagina": 5})

print("\n" + "=" * 70)
print("PNCP Search API — compras com CNPJ como texto")
print("=" * 70)

# PNCP search: aberto para adesão
test("PNCP search: compras abertas adesao",
     "https://pncp.gov.br/api/search/",
     {"q": CNPJ, "tipos_documento": "compra", "aberto_para_adesao": "true", "pagina": 1})

test("PNCP search: compras ampliado (sem filtro doc type)",
     "https://pncp.gov.br/api/search/",
     {"q": CNPJ, "pagina": 1})

# PNCP consulta compras globalmente — por data e filtro de adesão
test("pncp-api: compras globais abertas adesao (todos orgaos)",
     "https://pncp.gov.br/pncp-api/v1/compras",
     {"cnpjOrgao": CNPJ, "abertoParaAdesao": "true", "pagina": 1, "tamanhoPagina": 5})

test("pncp-api: compras globais por cnpjOrgao",
     "https://pncp.gov.br/pncp-api/v1/compras",
     {"cnpjOrgao": CNPJ, "pagina": 1, "tamanhoPagina": 5})

# PNCP consulta de atas globalmente
test("pncp-api: atas globais vigentes por cnpjOrgao",
     "https://pncp.gov.br/pncp-api/v1/atas",
     {"cnpjOrgao": CNPJ, "pagina": 1, "tamanhoPagina": 5})

print("\n" + "=" * 70)
print("dadosabertos — contratos e ARPs como orgao contratante")
print("=" * 70)

test("dadosabertos: contratos por cnpjOrgao",
     "https://dadosabertos.compras.gov.br/modulo-contratos/1_consultarContratos",
     {"cnpjOrgaoEntidade": CNPJ, "pagina": 1, "tamanhoPagina": 3})

test("dadosabertos: ARPs como orgao gerenciador",
     "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP",
     {"cnpjOrgaoGerenciador": CNPJ, "pagina": 1, "tamanhoPagina": 3})

test("dadosabertos: ARPs vigentes como orgao gerenciador",
     "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP",
     {"cnpjOrgaoGerenciador": CNPJ, "situacaoAta": "VIGENTE", "pagina": 1, "tamanhoPagina": 3})

print("\nFim.")
