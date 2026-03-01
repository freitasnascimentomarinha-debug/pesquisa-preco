import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = [
    "https://dadosabertos.compras.gov.br/v3/api-docs",
    "https://pncp.gov.br/api/pncp/v1/api-docs"
]

for u in urls:
    print(f"\nTrying {u}")
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
            data = json.loads(response.read().decode())
            paths = data.get('paths', {})
            for path in paths.keys():
                if 'fornecedor' in path.lower() or 'cnpj' in path.lower() or 'contratada' in path.lower():
                    print("Found path:", path)
            print("Done paths.")
    except Exception as e:
        print("Error:", e)
