#!/usr/bin/env python3
"""Descobre endpoints PNCP via Swagger e testa consultas."""
import requests
import json
import urllib3
urllib3.disable_warnings()

CNPJ = "34954091000116"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
TIMEOUT = 20

def get(url, params=None):
    r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT, verify=False)
    return r.status_code, r

print("=== Buscando Swagger PNCP ===")
for doc_url in [
    "https://pncp.gov.br/pncp-api/v3/api-docs",
    "https://pncp.gov.br/pncp-api/v2/api-docs",
]:
    try:
        status, r = get(doc_url)
        print(f"[{status}] {doc_url}")
        if status == 200:
            data = r.json()
            paths = sorted(data.get('paths', {}).keys())
            print(f"  Total de endpoints: {len(paths)}")
            # Filtrar endpoints relevantes (consulta/compras/atas/contratos)
            for p in paths:
                if any(k in p.lower() for k in ['consulta', 'adesao', 'ata', 'contrato', 'compra', 'fornecedor']):
                    methods = list(data['paths'][p].keys())
                    print(f"  {'|'.join(methods).upper():8s} {p}")
            break
    except Exception as e:
        print(f"  Error: {e}")

print("\n=== Testando endpoints de consulta PNCP ===")

def test(label, url, params=None, method='GET'):
    try:
        if method == 'POST':
            r = requests.post(url, json=params or {}, headers=HEADERS, timeout=TIMEOUT, verify=False)
        else:
            r = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT, verify=False)
        print(f"\n[{r.status_code}] {label}")
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict):
                total = d.get('totalRegistros', d.get('total', d.get('totalElements', '?')))
                print(f"  total: {total}")
                items = d.get('resultado', d.get('data', d.get('items', d.get('content', []))))
                if items and len(items) > 0:
                    print(f"  keys[0]: {list(items[0].keys())[:12]}")
                    print(f"  sample: {json.dumps(items[0], ensure_ascii=False)[:400]}")
            elif isinstance(d, list):
                print(f"  list len: {len(d)}")
                if d:
                    print(f"  keys[0]: {list(d[0].keys())[:10]}")
        else:
            print(f"  body: {r.text[:300]}")
    except requests.exceptions.Timeout:
        print(f"\n[TIMEOUT] {label}")
    except Exception as e:
        print(f"\n[ERROR] {label}: {e}")

# Consulta compras por data + cnpj (substitui /compras por /compras/consulta)
test("pncp consulta/compras por orgao CNPJ",
     "https://pncp.gov.br/pncp-api/v1/consulta/compras",
     {"cnpjOrgao": CNPJ, "pagina": 1, "tamanhoPagina": 5})

test("pncp consulta/atas por orgao CNPJ",
     "https://pncp.gov.br/pncp-api/v1/consulta/atas",
     {"cnpjOrgao": CNPJ, "pagina": 1, "tamanhoPagina": 5})

# Compras abertas para adesão
test("pncp compras abertas adesao (global)",
     "https://pncp.gov.br/pncp-api/v1/compras/publicacao",
     {"cnpjOrgao": CNPJ, "pagina": 1, "tamanhoPagina": 5})

# Com ano
for ano in [2024, 2025, 2026]:
    test(f"pncp orgao/compras/{ano}",
         f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/compras/{ano}",
         {"pagina": 1, "tamanhoPagina": 5})

# Atas orgao por ano
for ano in [2024, 2025, 2026]:
    test(f"pncp orgao/atas/{ano}",
         f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/atas/{ano}",
         {"pagina": 1, "tamanhoPagina": 5})

# Contratos orgao por ano
for ano in [2024, 2025, 2026]:
    test(f"pncp orgao/contratos/{ano}",
         f"https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/contratos/{ano}",
         {"pagina": 1, "tamanhoPagina": 5})

print("\nFim.")
