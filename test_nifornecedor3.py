"""Teste focado: 2_consultarARPItem com niFornecedor (janela 360 dias)."""
import requests, json, urllib3
from datetime import date, timedelta
urllib3.disable_warnings()

CNPJ = '34954091000116'
H = {'User-Agent': 'Mozilla/5.0'}
hoje = date.today()

# Testar várias janelas de 360 dias
for i in range(5):
    d_fim = (hoje - timedelta(days=360 * i)).strftime('%Y-%m-%d')
    d_ini = (hoje - timedelta(days=360 * (i + 1))).strftime('%Y-%m-%d')
    params = {
        'niFornecedor': CNPJ,
        'dataVigenciaInicialMin': d_ini,
        'dataVigenciaInicialMax': d_fim,
        'pagina': 1,
        'tamanhoPagina': 50,
    }
    try:
        r = requests.get('https://dadosabertos.compras.gov.br/modulo-arp/2_consultarARPItem',
                         params=params, headers=H, timeout=60, verify=False)
        if r.status_code == 200:
            data = r.json()
            total = data.get('totalRegistros', 0)
            resultado = data.get('resultado', [])
            print(f'Janela {d_ini} -> {d_fim}: {total} registros, {len(resultado)} itens')
            for item in resultado[:3]:
                print(f'  - ATA {item.get("numeroAtaRegistroPreco", "?")} | {item.get("nomeUnidadeGerenciadora", "?")} | situacao={item.get("situacaoAta", "?")} | maximoAdesao={item.get("maximoAdesao", "?")} | fornecedor={item.get("nomeRazaoSocialFornecedor", "?")}')
            if total > 0 and resultado:
                print(f'  Campos disponíveis: {list(resultado[0].keys())}')
        else:
            print(f'Janela {d_ini} -> {d_fim}: [{r.status_code}] {r.text[:200]}')
    except Exception as e:
        print(f'Janela {d_ini} -> {d_fim}: ERRO {e}')

print("\nFim.")
