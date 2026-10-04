"""Garante que os módulos do projeto em memória correspondem aos arquivos em disco.

No Streamlit Cloud, depois de um deploy a página nova pode ser executada com a versão ANTIGA de um módulo que já
estava na memória (erro típico: TypeError por função com assinatura diferente). `recarregar_se_mudou` recarrega
o módulo quando o arquivo mudou desde que ele foi carregado. Deve ser chamado antes dos `from modulo import ...`.
"""

from __future__ import annotations

import importlib
import os


def recarregar_se_mudou(*nomes: str) -> None:
    """Recarrega, na ordem dada (dependências primeiro), os módulos cujo arquivo mudou ou cuja versão em memória é desconhecida."""
    for nome in nomes:
        modulo = importlib.import_module(nome)
        arquivo = getattr(modulo, "__file__", None)
        if not arquivo:
            continue
        modificado_em = os.path.getmtime(arquivo)
        if getattr(modulo, "_modificado_em_ao_carregar", None) != modificado_em:
            modulo = importlib.reload(modulo)
            modulo._modificado_em_ao_carregar = modificado_em  # type: ignore[attr-defined]
