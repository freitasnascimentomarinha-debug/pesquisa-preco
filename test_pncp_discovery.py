#!/usr/bin/env python3
"""Investigar endpoints PNCP para notas fiscais, contratos, atas, etc."""
import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
BASE = "https://pncp.gov.br/pncp-api/v1"

def fetch(url, label=""):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            data = json.loads(resp.read().decode())
            return resp.status, data
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return 0, str(e)

# Step 1: Try to get swagger docs
print("=" * 60)
print("STEP 1: SWAGGER DOCS")
print("=" * 60)
for doc_url in [
    "https://pncp.gov.br/api/pncp/v3/api-docs",
    "https://pncp.gov.br/pncp-api/v3/api-docs",
    "https://pncp.gov.br/api/pncp/swagger-resources",
]:
    status, data = fetch(doc_url)
    print(f"\n[{status}] {doc_url}")
    if status == 200 and isinstance(data, dict):
        if 'paths' in data:
            paths = sorted(data['paths'].keys())
            print(f"  {len(paths)} endpoints found:")
            for p in paths:
                methods = list(data['paths'][p].keys())
                info = data['paths'][p][methods[0]]
                tags = info.get('tags', [])
                summary = info.get('summary', '')[:60]
                print(f"    {methods[0].upper():6s} {p}  [{','.join(tags)}] {summary}")
            
            # Save full doc
            with open('/tmp/pncp_openapi.json', 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("  -> Saved to /tmp/pncp_openapi.json")
        elif 'urls' in data:
            for entry in data['urls']:
                print(f"  URL group: {entry.get('url')} - {entry.get('name')}")
        else:
            print(f"  Keys: {list(data.keys())[:10]}")
    elif status == 200 and isinstance(data, list):
        for item in data:
            print(f"  {item}")

# Step 2: Test known + speculative endpoints with a real CNPJ
print("\n" + "=" * 60)
print("STEP 2: TEST ENDPOINTS")
print("=" * 60)

# First, find a working compra
test_cnpjs = ["00394502000144", "32479123000143", "00394502000107"]
working_cnpj = None
working_ano = None
working_seq = None

for cnpj in test_cnpjs:
    for ano in ["2024", "2025"]:
        for seq in ["000001", "000002", "000003"]:
            url = f"{BASE}/orgaos/{cnpj}/compras/{ano}/{seq}"
            status, data = fetch(url)
            if status == 200:
                working_cnpj = cnpj
                working_ano = ano
                working_seq = seq
                print(f"\nFound working compra: {cnpj}/{ano}/{seq}")
                print(f"  objetoCompra: {data.get('objetoCompra','')[:80]}")
                print(f"  modalidadeNome: {data.get('modalidadeNome','')}")
                print(f"  srp: {data.get('srp','')}")
                print(f"  ALL KEYS: {sorted(data.keys())}")
                break
        if working_cnpj:
            break
    if working_cnpj:
        break

if not working_cnpj:
    print("No working compra found, using defaults")
    working_cnpj = "00394502000144"
    working_ano = "2024"
    working_seq = "000001"

cnpj = working_cnpj
ano = working_ano
seq = working_seq

# Test ALL possible endpoints for this compra
endpoints = [
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/arquivos", "Documentos compra"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/itens", "Itens compra"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/atas", "Atas"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos", "Contratos da compra"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/termoContrato", "Termo contrato"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/empenhos", "Empenhos"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/notasFiscais", "Notas Fiscais"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/notas-fiscais", "NFs alt"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/instrumentosCobranca", "Instr Cobranca"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/instrumentos-cobranca", "Instr Cobranca alt"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/pagamentos", "Pagamentos"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/penalidades", "Penalidades"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/impugnacoes", "Impugnacoes"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/esclarecimentos", "Esclarecimentos"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/avisos", "Avisos"),
    (f"/orgaos/{cnpj}/compras/{ano}/{seq}/resultados", "Resultados"),
]

print(f"\nTesting endpoints for compra {cnpj}/{ano}/{seq}:")
for endpoint, label in endpoints:
    url = f"{BASE}{endpoint}"
    status, data = fetch(url)
    marker = "OK" if status == 200 else f"{status}"
    print(f"  [{marker:4s}] {label:25s} {endpoint}")
    if status == 200:
        if isinstance(data, list):
            print(f"         -> {len(data)} items")
            if data and isinstance(data[0], dict):
                print(f"         -> Keys: {sorted(data[0].keys())}")
        elif isinstance(data, dict):
            print(f"         -> Keys: {sorted(data.keys())[:10]}")

# Step 3: Try contratos endpoints specifically
print("\n" + "=" * 60)
print("STEP 3: CONTRATOS DETAIL ENDPOINTS")
print("=" * 60)

# Check if contratos returned data
url = f"{BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/contratos"
status, contratos = fetch(url)
if status == 200 and isinstance(contratos, list) and contratos:
    print(f"Found {len(contratos)} contratos!")
    ct = contratos[0]
    print(f"  Contrato keys: {sorted(ct.keys())}")
    seq_ct = ct.get('sequencialContrato', '1')
    
    # Test sub-endpoints of contrato
    ct_endpoints = [
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}", "Contrato detail"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/arquivos", "Docs contrato"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/termos", "Termos aditivos"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/notasFiscais", "NFs contrato"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/empenhos", "Empenhos contrato"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/pagamentos", "Pagamentos contrato"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/instrumentosCobranca", "Instr cobranca ct"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/cronograma", "Cronograma"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/subcontratacao", "Subcontratacao"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/historico", "Historico"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/contratos/{seq_ct}/itens", "Itens contrato"),
    ]
    for endpoint, label in ct_endpoints:
        url = f"{BASE}{endpoint}"
        status, data = fetch(url)
        marker = "OK" if status == 200 else f"{status}"
        print(f"  [{marker:4s}] {label:25s}")
        if status == 200:
            if isinstance(data, list):
                print(f"         -> {len(data)} items")
                if data:
                    print(f"         -> Keys: {sorted(data[0].keys()) if isinstance(data[0], dict) else data[0]}")
            elif isinstance(data, dict):
                print(f"         -> Keys: {sorted(data.keys())[:15]}")
else:
    print(f"No contratos for this compra (status={status})")
    # Try a different compra known to have contratos
    print("Trying to find a compra with contratos...")
    for try_cnpj in test_cnpjs:
        for try_ano in ["2024", "2025"]:
            for try_seq in range(1, 20):
                seq_str = f"{try_seq:06d}"
                url = f"{BASE}/orgaos/{try_cnpj}/compras/{try_ano}/{seq_str}/contratos"
                status, data = fetch(url)
                if status == 200 and isinstance(data, list) and len(data) > 0:
                    print(f"\nFound contratos at {try_cnpj}/{try_ano}/{seq_str}: {len(data)} items")
                    ct = data[0]
                    print(f"  Keys: {sorted(ct.keys())}")
                    seq_ct = ct.get('sequencialContrato', '1')
                    
                    # Test NF and other sub-endpoints
                    for sub_ep, sub_label in [
                        (f"/{seq_ct}/arquivos", "Docs"),
                        (f"/{seq_ct}/termos", "Termos"),
                        (f"/{seq_ct}/notasFiscais", "NFs"),
                        (f"/{seq_ct}/empenhos", "Empenhos"),
                        (f"/{seq_ct}/historico", "Historico"),
                    ]:
                        sub_url = f"{BASE}/orgaos/{try_cnpj}/compras/{try_ano}/{seq_str}/contratos{sub_ep}"
                        s2, d2 = fetch(sub_url)
                        print(f"    [{s2}] {sub_label}: {len(d2) if isinstance(d2, list) else type(d2).__name__}")
                        if s2 == 200 and isinstance(d2, list) and d2 and isinstance(d2[0], dict):
                            print(f"         Keys: {sorted(d2[0].keys())}")
                    break
            else:
                continue
            break
        else:
            continue
        break

# Step 4: Try Atas endpoints
print("\n" + "=" * 60)
print("STEP 4: ATAS DETAIL ENDPOINTS")
print("=" * 60)

url = f"{BASE}/orgaos/{cnpj}/compras/{ano}/{seq}/atas"
status, atas = fetch(url)
if status == 200 and isinstance(atas, list) and atas:
    print(f"Found {len(atas)} atas!")
    at = atas[0]
    print(f"  Ata keys: {sorted(at.keys())}")
    seq_at = at.get('sequencialAta', '1')
    
    ata_endpoints = [
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/atas/{seq_at}", "Ata detail"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/atas/{seq_at}/arquivos", "Docs ata"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/atas/{seq_at}/itens", "Itens ata"),
        (f"/orgaos/{cnpj}/compras/{ano}/{seq}/atas/{seq_at}/termos", "Termos ata"),
    ]
    for endpoint, label in ata_endpoints:
        url = f"{BASE}{endpoint}"
        status, data = fetch(url)
        marker = "OK" if status == 200 else f"{status}"
        print(f"  [{marker:4s}] {label:25s}")
        if status == 200:
            if isinstance(data, list):
                print(f"         -> {len(data)} items")
                if data and isinstance(data[0], dict):
                    print(f"         -> Keys: {sorted(data[0].keys())}")
            elif isinstance(data, dict):
                print(f"         -> Keys: {sorted(data.keys())[:15]}")
else:
    print(f"No atas for compra {cnpj}/{ano}/{seq}")

# Step 5: Try consulta API
print("\n" + "=" * 60)
print("STEP 5: CONSULTA API")
print("=" * 60)
consulta_urls = [
    "https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao?dataInicial=20240101&dataFinal=20240131&codigoModalidadeContratacao=6&pagina=1",
    "https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20240101&dataFinal=20240131&pagina=1",
    f"https://pncp.gov.br/api/consulta/v1/orgaos/{cnpj}/compras/{ano}/{seq}",
]
for url in consulta_urls:
    status, data = fetch(url)
    print(f"\n[{status}] {url[:80]}")
    if status == 200:
        if isinstance(data, dict):
            print(f"  Keys: {sorted(data.keys())[:10]}")
            # Show nested structure
            for k, v in data.items():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    print(f"  {k}[0] keys: {sorted(v[0].keys())[:8]}")
        elif isinstance(data, list):
            print(f"  {len(data)} items")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
