import urllib.request
import json

cnpj = "33683111000107"

try:
    url = f"https://api.portaldatransparencia.gov.br/api-de-dados/despesas/favorecidos?cnpjFavorecido={cnpj}&pagina=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'chave-api-dados': '551c38fc467d69e9b3176ab296bdf829'})
    with urllib.request.urlopen(req, timeout=10) as response:
        print("Status Base:", response.status)
        data = json.loads(response.read().decode())
        print("Len list:", len(data))
        if data:
            print("First item keys:", list(data[0].keys()))
            print("Res:", data[0])
except Exception as e:
    print("Error 1:", getattr(e, 'code', e))
    if hasattr(e, 'read'):
        print(e.read().decode())
