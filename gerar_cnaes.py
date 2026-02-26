#!/usr/bin/env python3
"""
Script auxiliar para gerar o arquivo cnaes_completo.json
contendo TODAS as subclasses CNAE da classificação IBGE/CONCLA.

Uso:
    python3 gerar_cnaes.py

Gera o arquivo 'cnaes_completo.json' na mesma pasta.
"""
import json
import requests

URL = "https://servicodados.ibge.gov.br/api/v2/cnae/subclasses"


def main():
    print("Buscando subclasses CNAE na API do IBGE…")
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    print(f"  → {len(data)} subclasses obtidas.")

    cnae_dict: dict[str, int] = {}
    for item in data:
        code_str = item["id"]  # ex.: "4761003"
        code_int = int(code_str)
        desc = item["descricao"].strip().title()

        # Formatar código CNAE legível: XXXX-X/XX
        if len(code_str) == 7:
            fmt = f"{code_str[:4]}-{code_str[4]}/{code_str[5:]}"
        else:
            fmt = code_str

        label = f"{desc} ({fmt})"
        cnae_dict[label] = code_int

    # Ordenar por label
    cnae_dict = dict(sorted(cnae_dict.items()))

    out = "cnaes_completo.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(cnae_dict, f, ensure_ascii=False, indent=2)

    print(f"Arquivo '{out}' gerado com {len(cnae_dict)} CNAEs.")


if __name__ == "__main__":
    main()
