#!/usr/bin/env python3
"""Testa endpoints de consulta pública do PNCP e dadosabertos para adesões."""
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
                    print(f"  keys[0]: {list(items[0].keys())[:15]}")
                    print(f"  sample: {json.dumps(items[0], ensure_ascii=False)[:500]}")
                else:
                    print(f"  keys: {list(d.keys())}")
            elif isinstance(d, list):
                print(f"  list len: {len(d)}")
                if d:
                    print(f"  keys[0]: {list(d[0].keys())[:10]}")
        else:
            print(f"  body: {r.text[:250]}")
    except requests.exceptions.Timeout:
        print(f"\n[TIMEOUT] {label}")
    except Exception as e:
        print(f"\n[ERROR] {label}: {e}")

print("=== Testando API consulta pública PNCP ===")

# PNCP public consultation endpoints
test("pncp-api consulta compras abertas (todos)",
     "https://pncp.gov.br/pncp-api/v1/compras/proposta/receber",
     {"cnpj": CNPJ, "pagina": 1, "tamanhoPagina": 5})

# Try PNCP consulta endpoints
for path in [
    "/pncp-api/v1/compras",
    "/pncp-api/v1/compras/srp",  # SRP = Sistema de Registro de Preços
]:
    test(f"pncp-api {path}",
         f"https://pncp.gov.br{path}",
         {"cnpjOrgao": CNPJ, "pagina": 1, "tamanhoPagina": 5})

# dadosabertos consulta by CNPJ
test("dadosabertos: ARPs por cnpjFornecedor (CNPJ)",
     "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem",
     {"cnpjFornecedor": CNPJ, "pagina": 1, "tamanhoPagina": 3})

# dadosabertos with different param name
test("dadosabertos: ARPs por cnpj",
     "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem",
     {"cnpj": CNPJ, "pagina": 1, "tamanhoPagina": 3})

print("\n=== Testando PNCP search com campos específicos ===")
# Try filtering via the search API with different terms
test("PNCP search: compra ou ata qualquer tipo",
     "https://pncp.gov.br/api/search/",
     {"q": CNPJ, "tipos_documento": "compra,ata", "pagina": 1})

# Try multiple doc types
for doc_type in ["contrato", "ata", "compra"]:
    test(f"PNCP search: {doc_type} (full detail)",
         "https://pncp.gov.br/api/search/",
         {"q": CNPJ, "tipos_documento": doc_type, "pagina": 1})

print("\n=== Verificando estrutura completa de um contrato da Search API ===")
try:
    r = requests.get("https://pncp.gov.br/api/search/",
                     params={"q": CNPJ, "tipos_documento": "contrato", "pagina": 1},
                     headers=HEADERS, timeout=20, verify=False)
    if r.status_code == 200:
        items = r.json().get('items', [])
        if items:
            print("Todos os campos do primeiro contrato encontrado:")
            print(json.dumps(items[0], indent=2, ensure_ascii=False))
        else:
            print("Nenhum contrato encontrado")
except Exception as e:
    print(f"Erro: {e}")

print("\n=== Testando dadosabertos ARPs por CNPJ gerenciador ===")
# The dadosabertos API uses "codigoUnidadeGestora" (UASG), but let's try other params
test("dadosabertos: ARPs todos campos",
     "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP",
     {"cnpjGerenciador": CNPJ, "pagina": 1, "tamanhoPagina": 3})

test("dadosabertos: ARPs por codigoOrgaoEntidade",
     "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP",
     {"codigoOrgaoEntidade": CNPJ, "pagina": 1, "tamanhoPagina": 3})

print("\nFim.")
