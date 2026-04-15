#!/usr/bin/env python3
"""Testa endpoints do PNCP e dadosabertos para um CNPJ fornecedor."""
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
        print(f"  URL: {r.url}")
        if r.status_code == 200:
            d = r.json()
            if isinstance(d, dict):
                total = d.get('totalRegistros', d.get('total', d.get('totalElements', '?')))
                print(f"  total: {total}")
                items = d.get('resultado', d.get('data', d.get('items', d.get('content', []))))
                if items and len(items) > 0:
                    print(f"  keys[0]: {list(items[0].keys())[:10]}")
                    print(f"  sample: {json.dumps(items[0], ensure_ascii=False)[:300]}")
            elif isinstance(d, list):
                print(f"  list len: {len(d)}")
                if d:
                    print(f"  keys[0]: {list(d[0].keys())[:10]}")
        elif r.status_code != 404:
            print(f"  body: {r.text[:200]}")
    except requests.exceptions.Timeout:
        print(f"\n[TIMEOUT] {label}")
    except Exception as e:
        print(f"\n[ERROR] {label}: {e}")

print("=" * 70)
print(f"Testando CNPJ: {CNPJ}")
print("=" * 70)

# 1. dadosabertos - contratos por cnpjContratado
test("dadosabertos: contratos por cnpjContratado",
     "https://dadosabertos.compras.gov.br/modulo-contratos/1_consultarContratos",
     {"cnpjContratado": CNPJ, "pagina": 1, "tamanhoPagina": 3})

# 2. dadosabertos - ARPs por cnpjFornecedor
test("dadosabertos: ARPs por cnpjFornecedor",
     "https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP",
     {"cnpjFornecedor": CNPJ, "pagina": 1, "tamanhoPagina": 3})

# 3. dadosabertos - ARP itens por cnpjFornecedor
test("dadosabertos: ARP itens por cnpjFornecedor",
     "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem",
     {"cnpjFornecedor": CNPJ, "pagina": 1, "tamanhoPagina": 3})

# 4. dadosabertos - Unidades adesões por cnpjFornecedor
test("dadosabertos: adesões vigentes por cnpjFornecedor",
     "https://dadosabertos.compras.gov.br/modulo-arp/3_consultarUnidadesItem",
     {"cnpjFornecedor": CNPJ, "pagina": 1, "tamanhoPagina": 3})

# 5. PNCP search - contratos
test("PNCP search: contratos",
     "https://pncp.gov.br/api/search/",
     {"q": CNPJ, "tipos_documento": "contrato", "pagina": 1})

# 6. PNCP search - atas
test("PNCP search: atas",
     "https://pncp.gov.br/api/search/",
     {"q": CNPJ, "tipos_documento": "ata", "pagina": 1})

# 7. PNCP search - compras
test("PNCP search: compras",
     "https://pncp.gov.br/api/search/",
     {"q": CNPJ, "tipos_documento": "compra", "pagina": 1})

print("\n" + "=" * 70)
print("Teste de adesoes vigentes com cnpjFornecedor=")
print("=" * 70)

# 8. PNCP pncp-api contratos
test("pncp-api: contratos por cnpjFornecedor",
     "https://pncp.gov.br/pncp-api/v1/contratos",
     {"cnpjFornecedor": CNPJ, "pagina": 1, "tamanhoPagina": 3})

# 9. PNCP pncp-api atas
test("pncp-api: atas por cnpjFornecedor",
     "https://pncp.gov.br/pncp-api/v1/atas",
     {"cnpjFornecedor": CNPJ, "pagina": 1, "tamanhoPagina": 3})

print("\nFim dos testes.")
