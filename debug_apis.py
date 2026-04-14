import requests, json, datetime, urllib3
urllib3.disable_warnings()
cnpj = '34954091000116'

print('=== TESTE 1: ATAS (cnpjFornecedor) ===')
params = {
    'dataInicial': '20230101',
    'dataFinal': '20260414',
    'cnpjFornecedor': cnpj,
    'pagina': 1,
    'tamanhoPagina': 5,
}
try:
    resp = requests.get('https://pncp.gov.br/api/consulta/v1/atas', params=params, timeout=30, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict):
            items = data.get('data', [])
            print(f'Total items: {len(items)}')
            if items and isinstance(items[0], dict):
                print(json.dumps(items[0], ensure_ascii=False, indent=2)[:1000])
        elif isinstance(data, list):
            print(f'List: {len(data)}')
    else:
        print(f'Resp: {resp.text[:300]}')
except Exception as e:
    print(f'Error: {e}')

print('\n=== TESTE 2: ATAS (cnpjOrgao - para ver se confunde) ===')
params2 = {
    'dataInicial': '20230101',
    'dataFinal': '20260414',
    'cnpjOrgao': cnpj,
    'pagina': 1,
    'tamanhoPagina': 5,
}
try:
    resp2 = requests.get('https://pncp.gov.br/api/consulta/v1/atas', params=params2, timeout=30, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Status: {resp2.status_code}')
    if resp2.status_code == 200:
        data2 = resp2.json()
        if isinstance(data2, dict):
            items2 = data2.get('data', [])
            print(f'Total items: {len(items2)}')
except Exception as e:
    print(f'Error: {e}')

print('\n=== TESTE 3: PNCP SEARCH (contrato) ===')
try:
    resp3 = requests.get('https://pncp.gov.br/api/search/', params={'q': cnpj, 'tipos_documento': 'contrato', 'pagina': 1}, timeout=30, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Status: {resp3.status_code}')
    if resp3.status_code == 200:
        data3 = resp3.json()
        items3 = data3.get('items', [])
        total3 = data3.get('total', 0)
        print(f'Total: {total3}, Items on page: {len(items3)}')
        if items3 and isinstance(items3[0], dict):
            print(f'First item keys: {list(items3[0].keys())}')
            print(f'First title: {items3[0].get("title", "N/A")}')
            print(f'First modalidade: {items3[0].get("modalidade_licitacao_nome", "N/A")}')
except Exception as e:
    print(f'Error: {e}')

print('\n=== TESTE 4: PNCP SEARCH (ata) ===')
try:
    resp4 = requests.get('https://pncp.gov.br/api/search/', params={'q': cnpj, 'tipos_documento': 'ata', 'pagina': 1}, timeout=30, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Status: {resp4.status_code}')
    if resp4.status_code == 200:
        data4 = resp4.json()
        items4 = data4.get('items', [])
        total4 = data4.get('total', 0)
        print(f'Total: {total4}, Items on page: {len(items4)}')
        if items4 and isinstance(items4[0], dict):
            print(json.dumps(items4[0], ensure_ascii=False, indent=2)[:600])
except Exception as e:
    print(f'Error: {e}')

print('\n=== TESTE 5: PNCP SEARCH (compra) ===')
try:
    resp5 = requests.get('https://pncp.gov.br/api/search/', params={'q': cnpj, 'tipos_documento': 'compra', 'pagina': 1}, timeout=30, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Status: {resp5.status_code}')
    if resp5.status_code == 200:
        data5 = resp5.json()
        items5 = data5.get('items', [])
        total5 = data5.get('total', 0)
        print(f'Total: {total5}, Items on page: {len(items5)}')
        if items5 and isinstance(items5[0], dict):
            print(f'First title: {items5[0].get("title", "N/A")}')
            print(f'First modalidade: {items5[0].get("modalidade_licitacao_nome", "N/A")}')
            print(f'First item_url: {items5[0].get("item_url", "N/A")}')
except Exception as e:
    print(f'Error: {e}')

print('\n=== TESTE 6: PNCP Fornecedor contratos ===')
try:
    resp6 = requests.get(f'https://pncp.gov.br/api/pncp/v1/orgaos/{cnpj}/compras', params={'pagina': 1, 'tamanhoPagina': 5}, timeout=30, verify=False, headers={'User-Agent': 'Mozilla/5.0'})
    print(f'Status: {resp6.status_code}')
    if resp6.status_code == 200:
        data6 = resp6.json()
        print(f'Type: {type(data6)}, len: {len(data6) if isinstance(data6, list) else "dict"}')
        if isinstance(data6, list) and data6:
            print(json.dumps(data6[0], ensure_ascii=False, indent=2)[:600])
        elif isinstance(data6, dict):
            print(f'Keys: {list(data6.keys())}')
    else:
        print(f'Resp: {resp6.text[:300]}')
except Exception as e:
    print(f'Error: {e}')
