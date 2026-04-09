import requests, json, re

# Testar busca de contrato para ver o formato do numeroControlePncp
r = requests.get('https://dadosabertos.compras.gov.br/modulo-contratos/1_consultarContratos?codigoUnidadeGestora=771300&dataVigenciaInicialMin=2024-01-01&dataVigenciaInicialMax=2024-12-31&pagina=1&tamanhoPagina=3', timeout=20, headers={'User-Agent':'Mozilla/5.0'})
print('Status contratos:', r.status_code)
if r.status_code == 200:
    data = r.json()
    resultado = data.get('resultado', [])
    if resultado:
        c = resultado[0]
        print('idCompra:', c.get('idCompra'))
        ctrl = c.get('numeroControlePncpCompra', '')
        print('numeroControlePncpCompra:', ctrl)
        print('nomeModalidadeCompra:', c.get('nomeModalidadeCompra'))
        
        # Parse the control number
        m = re.match(r"(\d{14})-\d+-(\d+)/(\d{4})", ctrl)
        if m:
            cnpj, seq, ano = m.group(1), m.group(2), m.group(3)
            print(f'\nParsed: cnpj={cnpj}, ano={ano}, seq={seq}')
            
            # Current link format
            seq_int = str(int(seq))
            link_old = f"https://pncp.gov.br/app/compras/{cnpj}/{ano}/{seq_int}"
            print(f'Old link: {link_old}')
            
            # Test API call matching
            api_url = f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj}/compras/{ano}/{seq}"
            print(f'API URL: {api_url}')
            r_api = requests.get(api_url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
            print(f'API Status: {r_api.status_code}')
            if r_api.status_code == 200:
                d = r_api.json()
                print('linkSistemaOrigem:', d.get('linkSistemaOrigem', ''))
                # Check all keys for link/url/pncp
                for k in sorted(d.keys()):
                    v = d[k]
                    if isinstance(v, str) and ('link' in k.lower() or 'url' in k.lower()):
                        print(f'  {k}: {v}')

# Test ARP
print('\n--- ARPs ---')
r2 = requests.get('https://dadosabertos.compras.gov.br/modulo-arp/1_consultarARP?codigoUnidadeGestora=771300&dataVigenciaInicioMin=2024-01-01&dataVigenciaInicioMax=2024-12-31&pagina=1&tamanhoPagina=3', timeout=20, headers={'User-Agent':'Mozilla/5.0'})
print('Status ARPs:', r2.status_code)
if r2.status_code == 200:
    data2 = r2.json()
    resultado2 = data2.get('resultado', [])
    if resultado2:
        a = resultado2[0]
        print('Keys:', list(a.keys()))
        ctrl_compra = a.get('numeroControlePncpCompra', '')
        ctrl_ata = a.get('numeroControlePncpAta', '')
        print('numeroControlePncpCompra:', ctrl_compra)
        print('numeroControlePncpAta:', ctrl_ata)
        
        # Test ata docs
        if ctrl_compra:
            m2 = re.match(r"(\d{14})-\d+-(\d+)/(\d{4})", ctrl_compra)
            if m2:
                cnpj2, seq2, ano2 = m2.group(1), m2.group(2), m2.group(3)
                # Buscar atas
                atas_url = f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj2}/compras/{ano2}/{seq2}/atas"
                print(f'Atas URL: {atas_url}')
                r_atas = requests.get(atas_url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
                print(f'Atas Status: {r_atas.status_code}')
                if r_atas.status_code == 200:
                    atas = r_atas.json()
                    print(f'Atas count: {len(atas)}')
                    if atas:
                        at = atas[0]
                        print('Ata keys:', list(at.keys()))
                        seq_ata = at.get('sequencialAta', '')
                        print(f'sequencialAta: {seq_ata}')
                        # Buscar docs da ata
                        docs_url = f"https://pncp.gov.br/pncp-api/v1/orgaos/{cnpj2}/compras/{ano2}/{seq2}/atas/{seq_ata}/arquivos"
                        print(f'Docs ata URL: {docs_url}')
                        r_docs = requests.get(docs_url, timeout=15, headers={'User-Agent':'Mozilla/5.0'})
                        print(f'Docs ata Status: {r_docs.status_code}')
                        if r_docs.status_code == 200:
                            docs = r_docs.json()
                            print(f'Docs count: {len(docs)}')
                            for d in docs[:3]:
                                print(f'  - {d.get("titulo","")}: {d.get("url","")}')
