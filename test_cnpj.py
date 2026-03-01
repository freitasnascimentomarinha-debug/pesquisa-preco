import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cnpj = "05999534000197" 

print("=== OPENCNPJ ===")
try:
    req = urllib.request.Request(f"https://api.opencnpj.org/{cnpj}", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
        print(f"Telefones list: {data.get('telefones')}")
        print(f"Keys in data: {list(data.keys())}")
        if 'estabelecimento' in data:
            print(f"Estabelecimento: {data['estabelecimento']}")
except Exception as e:
    print("Error OpenCNPJ:", e)

print("\n=== GOV BR (PNCP) ===")
try:
    url = f"https://pncp.gov.br/api/pncp/v1/fornecedores/{cnpj}/contratos"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Testing: {url}")
    with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
        print("Status Base:", response.status)
        data = json.loads(response.read().decode())
        print("Data len:", len(data))
except Exception as e:
    print("Error PNCP:", getattr(e, 'code', e))

print("\n=== COMPRAS DADOS (Legacy) ===")
try:
    url = f"http://compras.dados.gov.br/contratos/v1/contratos.json?cnpj_contratada={cnpj}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Testing: {url}")
    with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
        print("Status Base:", response.status)
        data = json.loads(response.read().decode())
        res = data.get('_embedded', {}).get('contratos', [])
        print("Total returned:", len(res))
except Exception as e:
    print("Error Legacy:", getattr(e, 'code', e))

print("\n=== PORTAL TRANSPARENCIA (Another endpoint) ===")
try:
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/contratos?cnpjFornecedor={cnpj}&pagina=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'chave-api-dados': '551c38fc467d69e9b3176ab296bdf829'})
    print(f"Testing: {url}")
    with urllib.request.urlopen(req, timeout=10) as response:
        print("Status Base:", response.status)
        data = json.loads(response.read().decode())
        print("Total returned:", len(data))
except Exception as e:
    print("Error PD:", getattr(e, 'code', e))
    if hasattr(e, 'read'):
        try:
            print(e.read().decode())
        except:
            pass
