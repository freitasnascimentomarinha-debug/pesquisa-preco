"""Cotação Direta: pedido de cotação por e-mail aos fornecedores que venderam recentemente à Administração (envio único, fornecedores em cópia oculta)."""

from __future__ import annotations

import base64
import datetime as dt
import os
import sys
import time

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Cotação Direta",
    page_icon="📨",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO_DIR = os.path.join(BASE_DIR, "Projeto Adesões")
sys.path.insert(0, BASE_DIR)
from atualizar_modulos import recarregar_se_mudou  # noqa: E402
recarregar_se_mudou('catmat_busca', 'cotacao_rapida', 'fornecedores_nf', 'memoria_lojas', 'cotacao_direta')  # evita módulo antigo em memória após deploy
import cotacao_direta as cd  # noqa: E402
import memoria_lojas  # noqa: E402  (só para ler os Secrets)
from catmat_busca import CATMAT_PATH, carregar_indice_catmat  # noqa: E402

ITENS_PEDIDO_GRANDE = 60  # acima disso só avisa que demora; não há limite

st.markdown(
    """
    <style>
        html, body, [data-testid="stAppViewContainer"], .stApp { background: #001a4d !important; color: #f8fafc; }
        [data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important; border-right: 3px solid #d4af37 !important; }
        [data-testid="stSidebarNav"] { display: none !important; }
        [data-testid="stSidebar"] .stMarkdown h2 { color: #d4af37 !important; font-family: 'Arial Black', sans-serif; font-size: 22px; text-align: center; letter-spacing: 2px;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8); border-bottom: 2px solid #d4af37; padding-bottom: 0.75rem; margin-bottom: 1.5rem; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] { background: linear-gradient(135deg, #1a1a1a, #252525) !important; border: 1px solid #333 !important; border-radius: 8px !important;
            color: #fff !important; margin: .2rem 0 !important; padding: .45rem .7rem !important; font-size: 12.5px !important; font-weight: 600 !important; justify-content: center !important; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span { color: #fff !important; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] { background: #d4af37 !important; border-color: #d4af37 !important; }
        [data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span { color: #0a0a0a !important; }
        .catalog-header { background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%); border: 1px solid rgba(96, 165, 250, .45); border-radius: 10px;
            padding: 1.35rem 1.55rem; margin-bottom: 1rem; box-shadow: 0 10px 28px rgba(0, 0, 0, .28); }
        .catalog-header-top { display: flex; align-items: center; gap: .85rem; flex-wrap: wrap; }
        .catalog-symbol { width: 2.8rem; height: 2.8rem; display: flex; justify-content: center; align-items: center; background: #d4af37; border-radius: 7px; font-size: 1.35rem; }
        .catalog-header h1 { color: #fff; margin: 0; font-size: 1.35rem; }
        .catalog-header p { color: #bfdbfe; margin: .18rem 0 0; font-size: .85rem; }
        .catalog-badge { color: #d4af37; font-size: .7rem; font-weight: 800; letter-spacing: .08em; margin-left: auto; }
        .passo { background: rgba(8, 26, 57, .78); border: 1px solid #1e5b9f; border-radius: 9px; padding: .8rem 1.1rem; margin: 1.2rem 0 .6rem; }
        .passo h3 { color: #d4af37; font-size: 1rem; margin: 0; }
        .passo p { color: #b6cae2; font-size: .8rem; margin: .2rem 0 0; }
        [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
            background: rgba(7, 20, 42, .8) !important; border-color: #2b6cb0 !important; color: #f8fafc !important; }
        [data-testid="stDataFrame"] { border: 1px solid #1e5b9f; border-radius: 8px; overflow: hidden; }
        .sidebar-footer { color: #666; font-size: 11px; text-align: center; padding: 1rem 0; border-top: 1px solid #333; margin-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

acanto_path = os.path.join(CATALOGO_DIR, "acanto.png")
acanto_b64 = base64.b64encode(open(acanto_path, "rb").read()).decode() if os.path.exists(acanto_path) else None

with st.sidebar:
    if acanto_b64:
        st.markdown(f'<div style="text-align:center;padding:1rem 0 0.5rem 0;"><img src="data:image/png;base64,{acanto_b64}" style="max-width:70%;height:auto;"></div>', unsafe_allow_html=True)
    st.markdown("## MENU")
    st.markdown("---")
    st.page_link("streamlit_app.py", label="Cotação", icon="⚓")
    st.page_link("pages/CATMAT_CATSERV_Automatico.py", label="CATMAT/CATSERV", icon="🔎")
    st.page_link("pages/Cotação_Rápida.py", label="Cotação Rápida", icon="⚡")
    st.page_link("pages/Cotação_Direta.py", label="Cotação Direta", icon="📨")
    st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
    st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
    st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
    st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
    st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
    st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
    st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
    st.page_link("pages/Calculo_IPCA.py", label="Cálculo IPCA", icon="📊")
    st.markdown("---")
    st.markdown("## LINKS ÚTEIS")
    st.markdown("""<div style="margin-bottom:0.6rem;">
        <a href="https://detetive-obtencao.vercel.app/" target="_blank" style="color:#cbd5e1;text-decoration:none;font-size:0.9rem;display:flex;align-items:center;gap:0.5rem;">🚨 Detetive Obtenção</a>
    </div>
""", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="catalog-header">
        <div class="catalog-header-top">
            <div class="catalog-symbol">📨</div>
            <div><h1>Cotação Direta</h1>
            <p>Peça orçamento por e-mail a quem vendeu recentemente à Administração: o sistema monta a proposta em Word, sugere o CATMAT e envia uma mensagem única, com os fornecedores em cópia oculta.</p></div>
            <div class="catalog-badge">PESQUISA DIRETA COM FORNECEDORES</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def passo(numero: int, titulo: str, descricao: str = "") -> None:
    st.markdown(f'<div class="passo"><h3>{numero}. {titulo}</h3>{f"<p>{descricao}</p>" if descricao else ""}</div>', unsafe_allow_html=True)


def segredo(nome: str) -> str:
    try:
        return memoria_lojas._procurar(st.secrets, nome)[0]
    except Exception:
        return ""


@st.cache_resource(show_spinner="Carregando o catálogo CATMAT…")
def catalogo_catmat():
    return carregar_indice_catmat(CATMAT_PATH)


# ---------- 1. dados da OM ----------
def _buscar_cep() -> None:
    endereco = cd.consultar_cep(st.session_state.get("om_cep", ""))
    st.session_state["om_cep_ok"] = bool(endereco)
    if endereco:
        st.session_state["om_logradouro"] = endereco["logradouro"]
        st.session_state["om_bairro"] = endereco["bairro"]
        st.session_state["om_cidade"] = endereco["cidade"]
        st.session_state["om_uf"] = endereco["uf"]


passo(1, "Dados da sua OM", "O cabeçalho da proposta e o e-mail usam estes dados. Digite o CEP e o endereço é preenchido sozinho.")
c1, c2 = st.columns([3, 1])
nome_om = c1.text_input("Nome da OM (Organização Militar)", key="om_nome", placeholder="Ex.: Centro de Operações do Abastecimento")
c2.text_input("CEP de entrega", key="om_cep", placeholder="00000-000", on_change=_buscar_cep)
if st.session_state.get("om_cep") and st.session_state.get("om_cep_ok") is False:
    st.caption("⚠️ CEP não encontrado: preencha o endereço manualmente.")
c3, c4, c5 = st.columns([3, 1, 2])
c3.text_input("Endereço", key="om_logradouro")
c4.text_input("Número", key="om_numero")
c5.text_input("Complemento", key="om_complemento")
c6, c7, c8 = st.columns([2, 2, 1])
c6.text_input("Bairro", key="om_bairro")
c7.text_input("Cidade", key="om_cidade")
c8.text_input("UF", key="om_uf", max_chars=2)
c9, c10 = st.columns(2)
c9.text_input("Telefone para contato", key="om_telefone", placeholder="(21) 0000-0000")
email_om = c10.text_input("Seu e-mail institucional", key="om_email", placeholder="nome@marinha.mil.br",
                          help="Você recebe uma cópia da mensagem, com o Word anexado, e as respostas dos fornecedores chegam aqui.")
responsavel = st.text_input("Responsável pelo pedido (assinatura do e-mail)", key="om_responsavel", placeholder="Ex.: 1T (IM) Fulano de Tal – Encarregado da Divisão de Obtenção")

om = {"nome": nome_om.strip(), "cep": cd.somente_digitos(st.session_state.get("om_cep", "")), "logradouro": st.session_state.get("om_logradouro", ""),
      "numero": st.session_state.get("om_numero", ""), "complemento": st.session_state.get("om_complemento", ""), "bairro": st.session_state.get("om_bairro", ""),
      "cidade": st.session_state.get("om_cidade", ""), "uf": st.session_state.get("om_uf", ""), "telefone": st.session_state.get("om_telefone", ""),
      "email": email_om.strip(), "responsavel": responsavel.strip()}

# ---------- 2. itens ----------
passo(2, "Itens e quantidades", "Digite como uma lista de compras ou envie uma planilha (sem limite de itens). O sistema já procura o CATMAT mais próximo de cada item: confira, melhore as descrições se quiser e deixe de fora o que não for pedir.")
def _catmats_do_item(descricao: str) -> list[dict[str, object]]:
    """Os 3 CATMAT mais próximos da descrição (guardados na sessão: só recalcula quando a descrição muda)."""
    cache = st.session_state.setdefault("cd_cache_catmat", {})
    chave = " ".join(descricao.lower().split())
    if chave not in cache:
        cache[chave] = cd.melhores_catmats(descricao, catalogo_catmat())
    return cache[chave]


def _linhas_com_catmat(itens_brutos: list[dict[str, object]], usar: list[bool] | None = None) -> list[dict[str, object]]:
    return [cd.linha_da_tabela(item, _catmats_do_item(str(item["descricao"])), True if usar is None else usar[i]) for i, item in enumerate(itens_brutos)]


def _itens_da_tabela(tabela: pd.DataFrame) -> list[dict[str, object]]:
    """Linhas da tabela da tela -> itens {descricao, quantidade, unidade} (só as marcadas em 'Usar', sem linhas vazias)."""
    saida = []
    for _, linha in tabela.iterrows():
        descricao = str(linha["Descrição"] or "").strip()
        if not descricao or descricao.lower() == "nan":
            continue
        quantidade = pd.to_numeric(linha["Qtd."], errors="coerce")
        saida.append({"descricao": descricao, "quantidade": float(quantidade) if quantidade == quantidade and quantidade > 0 else 1.0,
                      "unidade": str(linha["Un."] or "UN").strip().upper() or "UN", "usar": True if pd.isna(linha["Usar"]) else bool(linha["Usar"])})
    return saida


aba_texto, aba_arquivo = st.tabs(["✍️ Digitar a lista", "📎 Enviar Excel/CSV"])
with aba_texto:
    texto_lista = st.text_area("Um item por linha, com a quantidade ao lado", height=170, key="cd_lista",
                               placeholder="Caneta esferográfica azul - 100\n50 resmas de papel A4\nParafuso sextavado 1/2 x 20 zincado; 200 un\nFita isolante 20m x 30")
    if st.button("Identificar itens", key="cd_identificar_texto"):
        with st.spinner("Identificando os itens e procurando o CATMAT de cada um…"):
            st.session_state["cd_itens_base"] = _linhas_com_catmat(cd.interpretar_lista(texto_lista))
        st.session_state["cd_versao"] = st.session_state.get("cd_versao", 0) + 1
        st.session_state.pop("cd_resultado", None)
with aba_arquivo:
    arquivo = st.file_uploader("Planilha com os itens (colunas: item/descrição e quantidade)", type=["xlsx", "xls", "csv"], key="cd_arquivo")
    if arquivo is not None and st.button("Ler a planilha", key="cd_identificar_arquivo"):
        try:
            with st.spinner("Lendo a planilha e procurando o CATMAT de cada item…"):
                dados = pd.read_csv(arquivo) if arquivo.name.lower().endswith(".csv") else pd.read_excel(arquivo)
                st.session_state["cd_itens_base"] = _linhas_com_catmat(cd.itens_do_dataframe(dados))
            st.session_state["cd_versao"] = st.session_state.get("cd_versao", 0) + 1
            st.session_state.pop("cd_resultado", None)
        except Exception as erro:  # arquivo ilegível
            st.error(f"Não consegui ler a planilha ({type(erro).__name__}). Confira se é um .xlsx ou .csv válido.")

itens: list[dict[str, object]] = []
if st.session_state.get("cd_itens_base"):
    base = pd.DataFrame(st.session_state["cd_itens_base"])
    st.caption("**Usar**: desmarque para deixar um item de fora do pedido. Dá para **editar a descrição, a quantidade e a unidade**: depois de mexer nas descrições, "
               "clique em **Atualizar CATMAT** para o sistema casar de novo o código mais próximo. As colunas de CATMAT só mostram o resultado (não se edita).")
    editado = st.data_editor(
        base, hide_index=True, use_container_width=True, num_rows="fixed", key=f"cd_editor_{st.session_state.get('cd_versao', 0)}",
        disabled=["CATMAT", "% casamento", "Descrição do CATMAT", "Outras opções", "Situação"],
        column_config={"Usar": st.column_config.CheckboxColumn("Usar", width="small", help="Desmarque para deixar este item de fora do pedido."),
                       "Descrição": st.column_config.TextColumn("Descrição do item (edite para melhorar)", width="large"),
                       "Qtd.": st.column_config.NumberColumn("Qtd.", min_value=0, width="small"), "Un.": st.column_config.TextColumn("Un.", width="small"),
                       "CATMAT": st.column_config.TextColumn("CATMAT", width="small"),
                       "% casamento": st.column_config.NumberColumn("% casamento", format="%.0f%%", width="small",
                                                                    help=f"Semelhança entre a sua descrição e a do catálogo. Só entra na proposta a partir de {cd.LIMIAR_CATMAT:.0f}%."),
                       "Descrição do CATMAT": st.column_config.TextColumn("Descrição do item no CATMAT", width="large"),
                       "Outras opções": st.column_config.TextColumn("Outras opções (≥ 70%)", width="medium"),
                       "Situação": st.column_config.TextColumn("Situação", width="medium")})
    todos = _itens_da_tabela(editado)
    mudou = [i for i, (novo, antigo) in enumerate(zip(editado["Descrição"], base["Descrição"])) if str(novo).strip() != str(antigo).strip()]
    a1, a2 = st.columns([1, 3])
    if a1.button("🔄 Atualizar CATMAT", key="cd_atualizar", type="primary" if mudou else "secondary"):
        with st.spinner("Casando o CATMAT mais próximo…"):
            st.session_state["cd_itens_base"] = _linhas_com_catmat(todos, [t["usar"] for t in todos])
        st.session_state["cd_versao"] = st.session_state.get("cd_versao", 0) + 1
        st.session_state.pop("cd_resultado", None)
        st.rerun()
    if mudou:
        a2.warning(f"Você alterou {len(mudou)} descrição(ões): clique em **Atualizar CATMAT** para casar de novo.")
    with st.expander("➕ Acrescentar mais itens à lista"):
        mais = st.text_area("Um item por linha, com a quantidade ao lado", key="cd_mais", height=100)
        if st.button("Acrescentar", key="cd_acrescentar") and mais.strip():
            with st.spinner("Procurando o CATMAT dos itens novos…"):
                st.session_state["cd_itens_base"] = _linhas_com_catmat(todos + cd.interpretar_lista(mais), [t["usar"] for t in todos] + [True] * len(cd.interpretar_lista(mais)))
            st.session_state["cd_versao"] = st.session_state.get("cd_versao", 0) + 1
            st.session_state.pop("cd_resultado", None)
            st.rerun()
    itens = [{k: v for k, v in t.items() if k != "usar"} for t in todos if t["usar"]]
    st.caption(f"{len(itens)} item(ns) no pedido" + (f" ({len(todos) - len(itens)} deixado(s) de fora)." if len(todos) > len(itens) else "."))
    if len(itens) > ITENS_PEDIDO_GRANDE:
        st.warning(f"Pedido grande ({len(itens)} itens): a busca de fornecedores pode levar vários minutos e o envio sai em várias mensagens. Mantenha esta página aberta até terminar.")

# ---------- 3. condições ----------
# prazo e condições padrão (sem campos na tela): resposta em 5 dias úteis, proposta válida por 60 dias
prazo_dias, validade_dias = cd.PRAZO_PADRAO_DIAS_UTEIS, cd.VALIDADE_PADRAO_DIAS
if "cd_protocolo" not in st.session_state:
    st.session_state["cd_protocolo"] = cd.gerar_protocolo()
protocolo = st.session_state["cd_protocolo"]
hoje = dt.date.today()
data_limite = cd.adicionar_dias_uteis(hoje, prazo_dias)

# ---------- 3. preparar ----------
faltam = [rotulo for rotulo, valor in (("nome da OM", om["nome"]), ("e-mail institucional", om["email"]), ("itens", itens)) if not valor]
if om["email"] and not cd.EMAIL_VALIDO.match(om["email"]):
    faltam.append("e-mail institucional válido")
passo(3, "Escolher fornecedores e gerar a proposta",
      f"Para cada item, o sistema sugere o CATMAT e busca até {cd.FORNECEDORES_POR_ITEM} fornecedores que venderam item igual ou semelhante no último ano, "
      f"sem repetir fornecedor entre os itens. Os fornecedores terão {prazo_dias} dias úteis para responder (até {data_limite:%d/%m/%Y}). Pode levar alguns minutos.")
if faltam:
    st.info("Falta preencher: " + ", ".join(faltam) + ".")
if st.button("🔎 Preparar cotação", type="primary", disabled=bool(faltam), key="cd_preparar"):
    inicio = time.time()
    aviso, etapa, barra, status = st.empty(), st.empty(), st.progress(0), st.empty()
    aviso.warning("⏳ Processando… não feche nem atualize esta página até terminar.")

    def _tempo() -> str:
        decorrido = int(time.time() - inicio)
        return f"{decorrido // 60}min {decorrido % 60:02d}s"

    catmat = catalogo_catmat()
    catmats = {}
    etapa.markdown("**Etapa 1 de 3 — sugerindo o CATMAT de cada item**")
    for i, item in enumerate(itens):
        status.text(f"Item {i + 1}/{len(itens)}  •  decorrido: {_tempo()}")
        catmats[i] = [c for c in _catmats_do_item(str(item["descricao"])) if c["combinacao"] >= cd.LIMIAR_CATMAT]
        barra.progress((i + 1) / len(itens) * 0.2)

    def _progresso(fase: str, feitos: int, total: int, texto: str, achados: int) -> None:
        if fase == "busca":
            etapa.markdown("**Etapa 2 de 3 — consultando as vendas recentes no Compras.gov**")
            barra.progress(0.2 + 0.3 * feitos / max(total, 1))
        else:
            etapa.markdown("**Etapa 3 de 3 — escolhendo fornecedores e buscando os e-mails**")
            barra.progress(0.5 + 0.5 * feitos / max(total, 1))
        status.text(f"{texto}  •  fornecedores com e-mail até agora: {achados}  •  decorrido: {_tempo()}")

    por_item = cd.escolher_fornecedores(itens, catmat, ao_progredir=_progresso, excluir_emails={om["email"]})
    for marcador in (aviso, etapa, barra, status):
        marcador.empty()
    st.session_state["cd_resultado"] = {"itens": itens, "catmats": catmats, "fornecedores": [f for lista in por_item.values() for f in lista], "om": dict(om)}
    st.session_state.pop("cd_envio", None)
    st.success(f"Pronto em {_tempo()}: {len(st.session_state['cd_resultado']['fornecedores'])} fornecedor(es) com e-mail para {len(itens)} item(ns).")

resultado = st.session_state.get("cd_resultado")
if resultado:
    itens_r, catmats_r = resultado["itens"], resultado["catmats"]
    st.markdown("#### Itens e CATMAT sugerido")
    st.dataframe(pd.DataFrame([{"Item": i + 1, "Descrição": it["descricao"], "Qtd.": cd.formatar_quantidade(it["quantidade"]), "Un.": it["unidade"],
                                "CATMAT sugerido": "\n".join(f"{c['codigo']} ({c['combinacao']:.0f}%)" for c in catmats_r.get(i, [])) or "—",
                                "Fornecedores": sum(1 for f in resultado["fornecedores"] if f["posicao_item"] == i + 1)} for i, it in enumerate(itens_r)]),
                 hide_index=True, use_container_width=True)
    st.caption(f"CATMAT sugerido por semelhança de texto (mínimo {cd.LIMIAR_CATMAT:.0f}%, até {cd.MAX_CATMAT_SUGERIDOS} códigos); sem sugestão = sem combinação suficiente. "
               "Entra na proposta como referência.")
    if len({f["email"] for f in resultado["fornecedores"]}) < cd.MIN_FORNECEDORES:
        st.warning(f"Menos de {cd.MIN_FORNECEDORES} fornecedores com e-mail: a IN SEGES/ME nº 65/2021 recomenda ao menos três. "
                   "Inclua fornecedores manualmente na tabela abaixo (linha nova no fim).")

    st.markdown("#### Fornecedores que receberão o pedido")
    st.caption("Desmarque “Enviar” para tirar alguém, corrija um e-mail ou acrescente uma linha (empresa + e-mail) no fim da tabela. Todos recebem a proposta completa, em cópia oculta.")
    tabela = pd.DataFrame([{"Enviar": True, "Item de origem": f["posicao_item"], "Empresa": f["nome"], "E-mail": f["email"], "CNPJ": f["cnpj"],
                            "Telefone": f.get("telefone", ""), "Por que foi escolhida": f["motivo"]} for f in resultado["fornecedores"]],
                          columns=["Enviar", "Item de origem", "Empresa", "E-mail", "CNPJ", "Telefone", "Por que foi escolhida"])
    revisada = st.data_editor(tabela, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"cd_forn_{len(tabela)}",
                              column_config={"Enviar": st.column_config.CheckboxColumn("Enviar", default=True), "Item de origem": st.column_config.NumberColumn(disabled=True),
                                             "Por que foi escolhida": st.column_config.TextColumn(width="large")})
    fornecedores = []
    for _, linha in revisada.iterrows():
        email = str(linha["E-mail"] or "").strip().lower()
        if not email or email == "nan":
            continue
        fornecedores.append({"enviar": True if pd.isna(linha["Enviar"]) else bool(linha["Enviar"]), "posicao_item": int(linha["Item de origem"]) if pd.notna(linha["Item de origem"]) else 0,
                             "item": itens_r[int(linha["Item de origem"]) - 1]["descricao"] if pd.notna(linha["Item de origem"]) and 0 < int(linha["Item de origem"]) <= len(itens_r) else "(incluído manualmente)",
                             "nome": str(linha["Empresa"] or ""), "email": email, "cnpj": str(linha["CNPJ"] or ""), "telefone": str(linha["Telefone"] or ""),
                             "motivo": str(linha["Por que foi escolhida"] or "") or "Incluído manualmente pelo usuário."})
    ativos = [f for f in fornecedores if f["enviar"]]
    invalidos = [f["email"] for f in ativos if not cd.EMAIL_VALIDO.match(f["email"])]
    lotes = cd.separar_destinatarios(om["email"], [f["email"] for f in ativos if f["email"] not in invalidos])
    total_destinos = sum(len(lote) for lote in lotes)
    m1, m2, m3 = st.columns(3)
    m1.metric("Fornecedores selecionados", total_destinos)
    m2.metric("Itens", len(itens_r))
    m3.metric("Mensagens a enviar", len(lotes))
    if invalidos:
        st.error("E-mail inválido: " + ", ".join(invalidos) + ". Corrija ou desmarque antes de enviar.")

    # ---------- 5. e-mail e arquivos ----------
    passo(4, "Revisar o e-mail e baixar os arquivos")
    assunto = cd.assunto_email(protocolo, om["nome"])
    padrao = cd.texto_email(om, protocolo, data_limite, prazo_dias, validade_dias, len(itens_r))
    st.text_input("Assunto", value=assunto, disabled=True)
    texto_final = st.text_area("Texto do e-mail (pode editar)", value=padrao, height=420, key=f"cd_texto_{protocolo}_{prazo_dias}_{validade_dias}_{len(itens_r)}")
    proposta = cd.gerar_proposta_docx(om, itens_r, catmats_r, protocolo, hoje, data_limite, prazo_dias, validade_dias)
    nome_arquivo = f"Proposta_{protocolo}.docx"
    envio_anterior = st.session_state.get("cd_envio", {}).get(protocolo)
    comprovante = cd.gerar_comprovante_xlsx(om, protocolo, itens_r, catmats_r, fornecedores, envio_anterior["registros"] if envio_anterior else None)
    b1, b2 = st.columns(2)
    b1.download_button("⬇️ Baixar a proposta em Word", proposta, file_name=nome_arquivo, key="cd_baixar_docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    b2.download_button("⬇️ Baixar a lista de fornecedores (comprovante, Excel)", comprovante, file_name=f"Comprovante_{protocolo}.xlsx", key="cd_baixar_xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ---------- 6. envio ----------
    passo(5, "Enviar", "Uma mensagem para você (destinatário visível, com a proposta anexada) e os fornecedores em cópia oculta: um não vê o outro.")
    chave_api, remetente, senha_esperada = segredo("RESEND_API_KEY"), segredo("RESEND_FROM"), segredo("COTACAO_DIRETA_SENHA")
    if not (chave_api and remetente and senha_esperada):
        faltantes = [n for n, v in (("RESEND_API_KEY", chave_api), ("RESEND_FROM", remetente), ("COTACAO_DIRETA_SENHA", senha_esperada)) if not v]
        st.info("O envio ainda não está ligado. Configure nos Secrets do app: " + ", ".join(faltantes) + ". "
                "Enquanto isso, baixe o Word e a lista e envie por conta própria.")
    else:
        com_mais = ""
        if len(lotes) > 1:
            com_mais = f" Como são muitos fornecedores, serão {len(lotes)} mensagens iguais (o limite é de {cd.LOTE_BCC} ocultos por mensagem): você receberá {len(lotes)} cópias."
        st.caption(f"Remetente: {cd.remetente_com_nome(remetente, om['nome'])}  •  Respostas para: {om['email']}.{com_mais}")
        senha = st.text_input("Senha de envio", type="password", key="cd_senha", help="Definida em COTACAO_DIRETA_SENHA nos Secrets: evita que qualquer pessoa dispare e-mails em nome da OM.")
        senha_ok = cd.senha_correta(senha, senha_esperada)
        if senha and not senha_ok:
            st.error("Senha incorreta.")
        anexos = [(nome_arquivo, proposta)]
        origem = cd.remetente_com_nome(remetente, om["nome"])
        html_corpo = cd.html_email(texto_final)

        t1, t2 = st.columns(2)
        if t1.button("🧪 Enviar teste só para mim", disabled=not senha_ok or bool(invalidos) or not ativos, key="cd_teste"):
            retorno = cd.enviar_resend(chave_api, origem, om["email"], [], om["email"], "[TESTE] " + assunto, texto_final, html_corpo, anexos)
            (st.success if retorno["ok"] else st.error)("Teste enviado: confira a sua caixa de entrada (e o spam)." if retorno["ok"] else f"Falhou: {retorno['erro']}")
        registros_antes = st.session_state.get("cd_envio", {}).get(protocolo, {}).get("registros", [])
        ja_enviados = {r["E-mails"] for r in registros_antes if r["Resultado"] == "Enviada"}  # lotes que já saíram (não repete em nova tentativa)
        ja_enviado = bool(lotes) and all("; ".join(lote) in ja_enviados for lote in lotes)
        confirma = st.checkbox(f"Revisei o texto, a proposta e a lista: enviar para {total_destinos} fornecedor(es).", key="cd_confirma", disabled=ja_enviado)
        if ja_enviado:
            st.success(f"O pedido nº {protocolo} já foi enviado nesta sessão.")
            if st.button("🆕 Começar um novo pedido", key="cd_novo"):
                for chave in ("cd_protocolo", "cd_resultado", "cd_itens_base", "cd_confirma", "cd_senha"):
                    st.session_state.pop(chave, None)
                st.rerun()
        if t2.button("📨 Enviar para os fornecedores", type="primary", disabled=not (senha_ok and confirma and total_destinos and not invalidos and not ja_enviado), key="cd_enviar"):
            registros = [r for r in registros_antes if r["Resultado"] == "Enviada"]
            with st.spinner("Enviando…"):
                for numero, lote in enumerate(lotes, start=1):
                    if "; ".join(lote) in ja_enviados:
                        continue
                    retorno = cd.enviar_resend(chave_api, origem, om["email"], lote, om["email"], assunto, texto_final, html_corpo, anexos)
                    registros.append({"Mensagem": numero, "Fornecedores ocultos": len(lote), "Resultado": "Enviada" if retorno["ok"] else "FALHOU",
                                      "Código Resend": retorno["id"], "Erro": retorno["erro"], "Data/hora": dt.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                      "E-mails": "; ".join(lote)})
                    if not retorno["ok"]:
                        break
            st.session_state.setdefault("cd_envio", {})[protocolo] = {"registros": registros}
            st.rerun()
    envio = st.session_state.get("cd_envio", {}).get(protocolo)
    if envio:
        enviadas = sum(1 for r in envio["registros"] if r["Resultado"] == "Enviada")
        if lotes and all("; ".join(lote) in {r["E-mails"] for r in envio["registros"] if r["Resultado"] == "Enviada"} for lote in lotes):
            st.success(f"✅ {enviadas} mensagem(ns) enviada(s) para {total_destinos} fornecedor(es). Você recebeu a cópia no e-mail {om['email']}. Baixe o comprovante acima.")
        else:
            st.error("O envio não terminou: " + "; ".join(f"mensagem {r['Mensagem']}: {r['Erro']}" for r in envio["registros"] if r["Resultado"] != "Enviada")
                     + ". Corrija e clique em enviar de novo: só as mensagens que faltam serão enviadas.")
        st.dataframe(pd.DataFrame(envio["registros"]).drop(columns=["E-mails"]), hide_index=True, use_container_width=True)
