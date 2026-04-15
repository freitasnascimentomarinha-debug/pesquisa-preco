"""Teste correto: 2_consultarARPItem com niFornecedor + janela <= 365 dias."""
import requests, json, urllib3
from datetime import date, timedelta
urllib3.disable_warnings()

CNPJ = '34954091000116'
H = {'User-Agent': 'Mozilla/5.0'}

# Janela de 360 dias (API exige <= 365)
hoje = date.today()
data_fim = hoje.strftime('%Y-%m-%d')
data_ini = (hoje - timedelta(days=360)).strftime('%Y-%m-%d')

print(f"Janela: {data_ini} -> {data_fim}")
print()

# Teste 1: 2_consultarARPItem com niFornecedor
print("=== 2_consultarARPItem com niFornecedor ===")
params = {
    'niFornecedor': CNPJ,
    'dataVigenciaInicialMin': data_ini,
    'dataVigenciaInicialMax': data_fim,
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

# Teste 2: janelas históricas (2 anos atrás, 3 anos atrás)
print("\n\n=== Testando janelas históricas ===")
for anos_atras in range(1, 5):
    d_ini = (hoje - timedelta(days=360 * (anos_atras))).strftime('%Y-%m-%d')
    d_fim = (hoje - timedelta(days=360 * (anos_atras - 1))).strftime('%Y-%m-%d')
    params2 = {
        'niFornecedor': CNPJ,
        'dataVigenciaInicialMin': d_ini,
        'dataVigenciaInicialMax': d_fim,
        'pagina': 1,
        'tamanhoPagina': 50,
    }
    r2 = requests.get('https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem',
                     params=params2, headers=H, timeout=30, verify=False)
    if r2.status_code == 200:
        d2 = r2.json()
        total2 = d2.get('totalRegistros', 0)
        print(f'  Janela {d_ini} -> {d_fim}: {total2} registros')
        if total2 > 0:
            for item in d2.get('resultado', [])[:2]:
                print(f'    - ATA {item.get("numeroAtaRegistroPreco", "?")} | {item.get("nomeUnidadeGerenciadora", "?")} | maximoAdesao={item.get("maximoAdesao", "?")} | situacao={item.get("situacaoAta", "?")}')
    else:
        print(f'  Janela {d_ini} -> {d_fim}: [{r2.status_code}] {r2.text[:200]}')

# Teste 3: modulo-contratacoes/3 com niFornecedor
print("\n\n=== modulo-contratacoes/3_consultarResultadoItensContratacoes ===")
params3 = {
    'niFornecedor': CNPJ,
    'dataResultadoPncpInicial': data_ini,
    'dataResultadoPncpFinal': data_fim,
    'pagina': 1,
    'tamanhoPagina': 50,
}
r3 = requests.get('https://dadosabertos.compras.gov.br/modulo-contratacoes/3_consultarResultadoItensContratacoes_PNCP_14133',
                  params=params3, headers=H, timeout=30, verify=False)
print(f'Status: {r3.status_code}')
if r3.status_code == 200:
    d3 = r3.json()
    print(f'Total: {d3.get("totalRegistros", "?")}')
    for item in d3.get('resultado', [])[:3]:
        print(f'  - {item.get("descricaoObjeto", item.get("descricao", "?"))[:100]}')
else:
    print(f'Body: {r3.text[:300]}')

print("\nFim.")
