"""Teste: 2_consultarARPItem com niFornecedor (param correto do swagger)."""
import requests, json, urllib3
urllib3.disable_warnings()

CNPJ = '34954091000116'
H = {'User-Agent': 'Mozilla/5.0'}

print("=== 2_consultarARPItem com niFornecedor ===")
params = {
    'niFornecedor': CNPJ,
    'dataVigenciaInicialMin': '2020-01-01',
    'dataVigenciaInicialMax': '2026-12-31',
    'pagina': 1,
    'tamanhoPagina': 50,
}
r = requests.get('https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem',
                 params=params, headers=H, timeout=30, verify=False)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    total = data.get('totalRegistros', '?')
    resultado = data.get('resultado', [])
    print(f'Total registros: {total}')
    print(f'Itens nesta página: {len(resultado)}')
    for i, item in enumerate(resultado[:5]):
        print(f'\n--- Item {i+1} ---')
        print(json.dumps(item, indent=2, ensure_ascii=False)[:1000])
else:
    print(f'Body: {r.text[:500]}')

# Também testar modulo-contratacoes/3_consultarResultadoItensContratacoes_PNCP_14133
# que tem niFornecedor
print("\n\n=== 3_consultarResultadoItensContratacoes com niFornecedor ===")
params2 = {
    'niFornecedor': CNPJ,
    'dataResultadoPncpInicial': '2020-01-01',
    'dataResultadoPncpFinal': '2026-12-31',
    'pagina': 1,
    'tamanhoPagina': 50,
}
r2 = requests.get('https://dadosabertos.compras.gov.br/modulo-contratacoes/3_consultarResultadoItensContratacoes_PNCP_14133',
                  params=params2, headers=H, timeout=30, verify=False)
print(f'Status: {r2.status_code}')
if r2.status_code == 200:
    data2 = r2.json()
    total2 = data2.get('totalRegistros', '?')
    resultado2 = data2.get('resultado', [])
    print(f'Total registros: {total2}')
    print(f'Itens nesta página: {len(resultado2)}')
    for i, item in enumerate(resultado2[:3]):
        print(f'\n--- Item {i+1} ---')
        print(json.dumps(item, indent=2, ensure_ascii=False)[:800])
else:
    print(f'Body: {r2.text[:500]}')

print("\nFim.")
