import requests, json
from datetime import datetime, timedelta

url = "https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem"
end = datetime.today().date()
start = end - timedelta(days=360)
params = {
    "tamanhoPagina": 2,
    "pagina": 1,
    "codigoPdm": "4520",
    "dataVigenciaInicialMin": start.strftime("%Y-%m-%d"),
    "dataVigenciaInicialMax": end.strftime("%Y-%m-%d"),
}
try:
    r = requests.get(url, params=params, timeout=15)
    data = r.json()
    results = data.get("resultado", [])
    if results:
        print("=== TODAS AS CHAVES DO PRIMEIRO RESULTADO ===")
        for k, v in results[0].items():
            print(f"  {k}: {v}")
    else:
        print("Nenhum resultado")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
except Exception as e:
    print(f"Erro: {e}")
