"""Investigar como buscar ARPs/adesões vigentes por CNPJ do fornecedor."""
import requests, json, urllib3
urllib3.disable_warnings()

CNPJ = '34954091000116'
H = {'User-Agent': 'Mozilla/5.0'}

# 1) Verificar swagger do dadosabertos para ver params do 1_consultarARP e 2_consultarARPItem
print("=" * 60)
print("1) Verificando Swagger dadosabertos")
print("=" * 60)
for url in [
    'https://dadosabertos.compras.gov.br/v3/api-docs',
    'https://dadosabertos.compras.gov.br/swagger-ui/index.html',
    'https://dadosabertos.compras.gov.br/v2/api-docs',
]:
    try:
        r = requests.get(url, headers=H, timeout=15, verify=False)
        print(f'  [{r.status_code}] {url}')
        if r.status_code == 200 and 'json' in r.headers.get('content-type', ''):
            d = r.json()
            paths = list(d.get('paths', {}).keys())
            arp_paths = [p for p in paths if 'arp' in p.lower() or 'ata' in p.lower()]
            print(f'  Paths ARP/ATA: {arp_paths}')
            for p in arp_paths:
                methods = d['paths'][p]
                for m, info in methods.items():
                    params = info.get('parameters', [])
                    pnames = [(x.get('name'), x.get('required', False)) for x in params]
                    print(f'    {m.upper()} {p}:')
                    for name, req in pnames:
                        print(f'      - {name} (required={req})')
            break
    except Exception as e:
        print(f'  ERRO: {e}')

# 2) Testar 1_consultarARP com cnpjFornecedor + datas (range largo)
print("\n" + "=" * 60)
print("2) Testando 1_consultarARP com cnpjFornecedor + datas")
print("=" * 60)
combos = [
    {'cnpjFornecedor': CNPJ, 'dataVigenciaInicialMin': '2020-01-01', 'dataVigenciaInicialMax': '2026-12-31', 'pagina': 1, 'tamanhoPagina': 5},
    {'cnpjFornecedor': CNPJ, 'pagina': 1, 'tamanhoPagina': 5},
]
for params in combos:
    try:
        r = requests.get('https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP',
                         params=params, headers=H, timeout=20, verify=False)
        print(f'  [{r.status_code}] params={params}')
        if r.status_code == 200:
            data = r.json()
            print(f'    total={data.get("totalRegistros", "?")} resultado_count={len(data.get("resultado", []))}')
            if data.get('resultado'):
                print(f'    primeiro: {json.dumps(data["resultado"][0], indent=2, ensure_ascii=False)[:500]}')
        else:
            print(f'    body: {r.text[:300]}')
    except Exception as e:
        print(f'  ERRO: {e}')

# 3) Testar 2_consultarARPItem com cnpjFornecedor + datas (sem código catálogo)
print("\n" + "=" * 60)
print("3) Testando 2_consultarARPItem com cnpjFornecedor + datas")
print("=" * 60)
combos2 = [
    {'cnpjFornecedor': CNPJ, 'dataVigenciaInicialMin': '2020-01-01', 'dataVigenciaInicialMax': '2026-12-31', 'pagina': 1, 'tamanhoPagina': 5},
    {'cnpjFornecedor': CNPJ, 'pagina': 1, 'tamanhoPagina': 5},
]
for params in combos2:
    try:
        r = requests.get('https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem',
                         params=params, headers=H, timeout=20, verify=False)
        print(f'  [{r.status_code}] params={params}')
        if r.status_code == 200:
            data = r.json()
            print(f'    total={data.get("totalRegistros", "?")} resultado_count={len(data.get("resultado", []))}')
            if data.get('resultado'):
                print(f'    primeiro: {json.dumps(data["resultado"][0], indent=2, ensure_ascii=False)[:800]}')
        else:
            print(f'    body: {r.text[:300]}')
    except Exception as e:
        print(f'  ERRO: {e}')

# 4) Testar PNCP search com razão social da empresa (busca por texto)
print("\n" + "=" * 60)
print("4) Testando PNCP search com razão social / nome da empresa")
print("=" * 60)
# Primeiro pegar razão social do CNPJ
try:
    r = requests.get(f'https://publica.cnpj.ws/cnpj/{CNPJ}', headers=H, timeout=15, verify=False)
    if r.status_code == 200:
        dados = r.json()
        razao = dados.get('razao_social', '')
        print(f'  Razão social: {razao}')
        
        # Buscar atas no PNCP usando razão social
        for termo in [razao, razao.split()[0] if razao else '']:
            if not termo:
                continue
            r2 = requests.get('https://pncp.gov.br/api/search/',
                              params={'q': termo, 'tipos_documento': 'ata', 'pagina': 1},
                              headers=H, timeout=30, verify=False)
            print(f'  [{r2.status_code}] search ata q="{termo}"')
            if r2.status_code == 200:
                d2 = r2.json()
                print(f'    total={d2.get("total", 0)}')
                for item in d2.get('items', [])[:3]:
                    print(f'    - {item.get("title")} | {item.get("orgao_nome")} | {item.get("description", "")[:100]}')
    else:
        print(f'  [{r.status_code}] cnpj.ws')
except Exception as e:
    print(f'  ERRO: {e}')

# 5) Testar PNCP search com "lavanderia" + ata para ver se acha algo
print("\n" + "=" * 60)
print("5) Testando PNCP search com 'lavanderia' + ata (RJ)")
print("=" * 60)
try:
    r = requests.get('https://pncp.gov.br/api/search/',
                     params={'q': 'lavanderia', 'tipos_documento': 'ata', 'uf': 'RJ', 'pagina': 1},
                     headers=H, timeout=30, verify=False)
    print(f'  [{r.status_code}] search ata q="lavanderia" uf=RJ')
    if r.status_code == 200:
        d = r.json()
        print(f'  total={d.get("total", 0)}')
        for item in d.get('items', [])[:5]:
            desc = item.get('description', '')
            print(f'  - {item.get("title")} | {item.get("orgao_nome")} | desc: {desc[:150]}')
            # Check if our CNPJ appears
            if CNPJ in json.dumps(item):
                print(f'    *** CNPJ {CNPJ} ENCONTRADO NESTE ITEM ***')
except Exception as e:
    print(f'  ERRO: {e}')

# 6) Testar endpoint PNCP de atas específico (pncp-api)
print("\n" + "=" * 60)
print("6) Testando PNCP pncp-api endpoint de atas")
print("=" * 60)
for url in [
    f'https://pncp.gov.br/pncp-api/v1/orgaos/{CNPJ}/compras',
    f'https://pncp.gov.br/pncp-api/v1/atas?cnpjFornecedor={CNPJ}&pagina=1&tamanhoPagina=5',
]:
    try:
        r = requests.get(url, headers=H, timeout=15, verify=False)
        print(f'  [{r.status_code}] {url}')
        print(f'    body: {r.text[:300]}')
    except Exception as e:
        print(f'  ERRO: {e}')

print("\nFim.")
