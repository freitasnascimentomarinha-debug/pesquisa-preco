import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cnpj = "05999534000197"
# Test API
try:
    url = f"https://dadosabertos.compras.gov.br/modulo-legado/6_consultarCompraItensSemLicitacao?cnpj_contratada={cnpj}&ano_compra=2023"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    print(f"Testing: {url}")
    with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
        print("Status Base:", response.status)
        data = json.loads(response.read().decode())
        print("Keys:", list(data.keys()) if isinstance(data, dict) else len(data))
        if isinstance(data, list) and data:
            print("Item:", data[0])
        elif isinstance(data, dict) and 'resultado' in data:
            res = data['resultado']
            print("Num resultados:", len(res))
            if res:
                print("Item:", res[0])
except Exception as e:
    print("Error Legacy 1:", getattr(e, 'code', e))
