import base64
import os
from datetime import datetime
import re

import pandas as pd
import requests
import streamlit as st
from fpdf import FPDF


st.set_page_config(
	page_title="Cálculo IPCA",
	page_icon="📊",
	layout="wide",
	initial_sidebar_state="expanded",
)

st.markdown(
	"""
<style>
	body, .main { background-color: #001a4d; color: #ffffff; }
	.stApp { background-color: #001a4d; }

	[data-testid="stSidebar"] {
		background: linear-gradient(180deg, #0a0a0a 0%, #111111 50%, #0a0a0a 100%) !important;
		border-right: 3px solid #d4af37 !important;
		box-shadow: 4px 0 15px rgba(0, 0, 0, 0.5);
	}
	[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { background: transparent !important; }
	[data-testid="stSidebarNav"] { display: none !important; }
	[data-testid="stSidebar"] .stMarkdown h2 {
		color: #d4af37 !important;
		font-family: 'Arial Black', sans-serif;
		font-size: 22px;
		text-align: center;
		letter-spacing: 2px;
		text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8);
		border-bottom: 2px solid #d4af37;
		padding-bottom: 0.75rem;
		margin-bottom: 1.5rem;
	}
	[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
		background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%) !important;
		color: #ffffff !important;
		border: 1px solid #333333 !important;
		border-radius: 8px !important;
		margin: 0.2rem 0 !important;
		padding: 0.45rem 0.7rem !important;
		font-weight: 600 !important;
		font-size: 12.5px !important;
		line-height: 1.2 !important;
		min-height: 0 !important;
		transition: all 0.3s ease !important;
		text-decoration: none !important;
		display: flex !important;
		align-items: center !important;
		justify-content: center !important;
	}
	[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] span {
		color: #ffffff !important;
	}
	[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
		background: linear-gradient(135deg, #d4af37 0%, #c5a028 100%) !important;
		color: #0a0a0a !important;
		border: 1px solid #d4af37 !important;
		font-weight: bold !important;
	}
	[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] span {
		color: #0a0a0a !important;
	}
	[data-testid="stSidebar"] hr { border-color: #333333 !important; margin: 1rem 0 !important; }
	.sidebar-footer {
		color: #666666;
		font-size: 11px;
		text-align: center;
		padding: 1rem 0;
		border-top: 1px solid #333333;
		margin-top: 2rem;
	}

	.header-box {
		background: linear-gradient(135deg, #001a4d 0%, #0033cc 100%);
		border-radius: 12px;
		padding: 1.2rem 1.6rem;
		margin-bottom: 1rem;
		box-shadow: 0 6px 20px rgba(0,0,0,0.4);
	}
	.header-box h1 { color: #d4af37; margin: 0 0 0.3rem 0; }
	.header-box p { color: #cbd5e1; margin: 0; }
</style>
""",
	unsafe_allow_html=True,
)

_acanto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Projeto Adesões", "acanto.png")
if os.path.exists(_acanto_path):
	with open(_acanto_path, "rb") as _f:
		_acanto_b64 = base64.b64encode(_f.read()).decode()
else:
	_acanto_b64 = None

with st.sidebar:
	if _acanto_b64:
		st.markdown(
			f'<div style="text-align:center;padding:1rem 0 0.5rem 0;"><img src="data:image/png;base64,{_acanto_b64}" style="max-width:70%;height:auto;"></div>',
			unsafe_allow_html=True,
		)
	st.markdown("## MENU")
	st.markdown("---")
	st.page_link("streamlit_app.py", label="Cotação", icon="⚓")
	st.page_link("pages/Detalhes_Compra.py", label="Detalhes Compra", icon="🔍")
	st.page_link("pages/Adesões.py", label="Adesões", icon="🤝")
	st.page_link("pages/Notas_Fiscais.py", label="Notas Fiscais", icon="📄")
	st.page_link("pages/Banco_de_Fornecedores.py", label="Fornecedores", icon="🏢")
	st.page_link("pages/Consulta.py", label="Consulta CNPJ", icon="💻")
	st.page_link("pages/Web_Scraping.py", label="Web Scraping", icon="🕷️")
	st.page_link("pages/O_Babilaca_(IA).py", label="O Babilaca (IA)", icon="🧠")
	st.page_link("pages/Calculo_IPCA.py", label="Cálculo IPCA", icon="📊")
	st.page_link("pages/CATMAT_CATSERV_Automatico.py", label="CATMAT/CATSERV", icon="🔎")
	st.markdown("---")
	st.markdown("## LINKS ÚTEIS")
	st.markdown(
		"""<div style="margin-bottom: 0.6rem;">
		<a href="https://detetive-obtencao.vercel.app/" target="_blank" style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
			🚨 Detetive Obtenção
		</a>
	</div>
	<div style="margin-bottom: 1rem;">
		<a href="https://depurador.streamlit.app/" target="_blank" style="color: #cbd5e1; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
			🧾 Depurador de Orçamentos
		</a>
	</div>
	""",
		unsafe_allow_html=True,
	)
	st.markdown('<div style="text-align:center;color:#d4af37;font-size:10px;font-weight:600;padding:0.3rem 0;white-space:nowrap;">Centro de Operações do Abastecimento</div>', unsafe_allow_html=True)
	st.markdown('<div class="sidebar-footer">Marinha do Brasil<br>AtaCotada v1.0</div>', unsafe_allow_html=True)


def _sanitize_for_pdf(text: str) -> str:
	replacements = {
		"\u2013": "-", "\u2014": "-", "\u2015": "-",
		"\u2018": "'", "\u2019": "'",
		"\u201c": '"', "\u201d": '"',
		"\u2022": "-",
		"\u2026": "...",
		"\u00a0": " ",
		"\u200b": "",
		"\u2010": "-", "\u2011": "-",
		"\u2212": "-",
		"\u2264": "<=", "\u2265": ">=",
		"\u00b0": "o",
	}
	for old, new in replacements.items():
		text = text.replace(old, new)
	cleaned = []
	for ch in text:
		try:
			ch.encode("latin-1")
			cleaned.append(ch)
		except UnicodeEncodeError:
			cleaned.append(" ")
	return "".join(cleaned)


@st.cache_data(ttl=86400, show_spinner=False)
def _buscar_ipca_bcb():
	url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
	resp = requests.get(url, timeout=30)
	resp.raise_for_status()
	dados = resp.json()
	registros = []
	for r in dados:
		partes = r["data"].split("/")
		dt = datetime(int(partes[2]), int(partes[1]), int(partes[0]))
		registros.append({"data": dt, "valor": float(r["valor"])})
	return registros


def _calcular_ipca_acumulado(ipca_dados, data_inicio, data_fim):
	inicio_mes = datetime(data_inicio.year, data_inicio.month, 1)
	fim_mes = datetime(data_fim.year, data_fim.month, 1)
	fator = 1.0
	meses_usados = []
	for r in ipca_dados:
		if inicio_mes <= r["data"] <= fim_mes:
			fator *= (1 + r["valor"] / 100)
			meses_usados.append(r)
	percentual = (fator - 1) * 100
	return fator, percentual, meses_usados


def _normalizar_coluna(col: str) -> str:
	col = col.strip().lower()
	return re.sub(r"[^a-z0-9]", "", col)


def _parse_valor(valor):
	if pd.isna(valor):
		return None
	if isinstance(valor, (int, float)):
		return float(valor)
	texto = str(valor).strip()
	if not texto:
		return None
	texto = texto.replace("R$", "").replace(" ", "")
	if "," in texto and "." in texto:
		texto = texto.replace(".", "").replace(",", ".")
	elif "," in texto:
		texto = texto.replace(",", ".")
	try:
		return float(texto)
	except ValueError:
		return None


def _importar_itens_excel(df: pd.DataFrame):
	if df is None or df.empty:
		return [], "A planilha está vazia."

	map_cols = {_normalizar_coluna(c): c for c in df.columns}
	col_desc = None
	col_valor = None

	for cand in ["descricao", "descricao", "item", "nome", "produto", "servico"]:
		if cand in map_cols:
			col_desc = map_cols[cand]
			break
	for cand in ["valor", "valororiginal", "preco", "precooriginal", "precoorig", "valorunitario"]:
		if cand in map_cols:
			col_valor = map_cols[cand]
			break

	if not col_desc or not col_valor:
		return [], (
			"Não encontrei as colunas obrigatórias. Use nomes como 'Descrição' e 'Valor'."
		)

	itens = []
	for _, row in df.iterrows():
		desc = str(row[col_desc]).strip() if not pd.isna(row[col_desc]) else ""
		valor = _parse_valor(row[col_valor])
		if desc and valor is not None and valor > 0:
			itens.append({"descricao": desc, "valor": float(valor)})

	if not itens:
		return [], "Nenhuma linha válida encontrada (descrição preenchida e valor > 0)."

	return itens, None


def _gerar_pdf_ipca(itens_resultado, meses_detalhes, data_calc):
	pdf = FPDF()
	pdf.add_page()
	pdf.set_auto_page_break(auto=True, margin=25)

	pdf.set_fill_color(0, 26, 77)
	pdf.rect(0, 0, 210, 50, "F")
	pdf.set_draw_color(212, 175, 55)
	pdf.set_line_width(1.2)
	pdf.line(0, 50, 210, 50)

	pdf.set_y(8)
	pdf.set_font("Helvetica", "B", 10)
	pdf.set_text_color(212, 175, 55)
	pdf.cell(0, 5, "MARINHA DO BRASIL", ln=True, align="C")
	pdf.set_font("Helvetica", "", 8)
	pdf.set_text_color(200, 200, 220)
	pdf.cell(0, 4, "Centro de Operacoes do Abastecimento", ln=True, align="C")
	pdf.ln(3)

	pdf.set_font("Helvetica", "B", 16)
	pdf.set_text_color(255, 255, 255)
	pdf.cell(0, 9, _sanitize_for_pdf("RELATORIO DE CORRECAO PELO IPCA"), ln=True, align="C")
	pdf.ln(1)

	pdf.set_fill_color(212, 175, 55)
	pdf.rect(0, 52, 210, 14, "F")
	pdf.set_y(54)
	pdf.set_font("Helvetica", "B", 13)
	pdf.set_text_color(0, 26, 77)
	pdf.cell(0, 9, _sanitize_for_pdf("Indice Nacional de Precos ao Consumidor Amplo"), ln=True, align="C")
	pdf.ln(6)

	pdf.set_font("Helvetica", "", 9)
	pdf.set_text_color(80, 80, 80)
	pdf.cell(0, 5, f"Data/Hora do Calculo: {data_calc.strftime('%d/%m/%Y %H:%M:%S')}", ln=True)
	pdf.cell(0, 5, "API: Banco Central do Brasil - SGS Serie 433 (IPCA mensal)", ln=True)
	pdf.cell(0, 5, "URL: https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json", ln=True)
	pdf.cell(0, 5, "Fonte: IBGE - Instituto Brasileiro de Geografia e Estatistica", ln=True)
	pdf.ln(4)

	pdf.set_draw_color(212, 175, 55)
	pdf.set_line_width(0.5)
	pdf.line(20, pdf.get_y(), 190, pdf.get_y())
	pdf.ln(6)

	pdf.set_font("Helvetica", "B", 12)
	pdf.set_text_color(0, 26, 77)
	pdf.cell(0, 8, "ITENS CORRIGIDOS", ln=True, align="C")
	pdf.ln(3)

	col_w = [12, 48, 28, 28, 28, 25, 25]
	headers = ["#", "Descricao", "Valor Orig.", "Data Orig.", "IPCA Acum.", "Fator", "Valor Corr."]
	pdf.set_font("Helvetica", "B", 8)
	pdf.set_fill_color(0, 26, 77)
	pdf.set_text_color(255, 255, 255)
	for i, h in enumerate(headers):
		pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
	pdf.ln()

	pdf.set_font("Helvetica", "", 8)
	pdf.set_text_color(30, 30, 30)
	total_original = 0.0
	total_corrigido = 0.0
	for idx, item in enumerate(itens_resultado, 1):
		total_original += item["valor_original"]
		total_corrigido += item["valor_corrigido"]
		fill = idx % 2 == 0
		if fill:
			pdf.set_fill_color(240, 245, 255)
		row = [
			str(idx),
			_sanitize_for_pdf(item["descricao"][:30]),
			f"R$ {item['valor_original']:,.2f}",
			item["data_original"].strftime("%m/%Y"),
			f"{item['percentual']:.4f}%",
			f"{item['fator']:.6f}",
			f"R$ {item['valor_corrigido']:,.2f}",
		]
		for i, val in enumerate(row):
			pdf.cell(col_w[i], 6, val, border=1, fill=fill, align="C" if i != 1 else "L")
		pdf.ln()

	pdf.set_font("Helvetica", "B", 9)
	pdf.set_fill_color(212, 175, 55)
	pdf.set_text_color(0, 26, 77)
	pdf.cell(sum(col_w[:2]), 7, "TOTAL", border=1, fill=True, align="C")
	pdf.cell(col_w[2], 7, f"R$ {total_original:,.2f}", border=1, fill=True, align="C")
	pdf.cell(sum(col_w[3:6]), 7, "", border=1, fill=True)
	pdf.cell(col_w[6], 7, f"R$ {total_corrigido:,.2f}", border=1, fill=True, align="C")
	pdf.ln()

	diferenca = total_corrigido - total_original
	pdf.ln(3)
	pdf.set_font("Helvetica", "B", 10)
	pdf.set_text_color(0, 26, 77)
	pdf.cell(0, 6, f"Diferenca total: R$ {diferenca:,.2f}", ln=True, align="R")
	pdf.ln(6)

	if meses_detalhes:
		pdf.set_draw_color(212, 175, 55)
		pdf.set_line_width(0.5)
		pdf.line(20, pdf.get_y(), 190, pdf.get_y())
		pdf.ln(4)

		pdf.set_font("Helvetica", "B", 11)
		pdf.set_text_color(0, 26, 77)
		pdf.cell(0, 7, "DETALHAMENTO MENSAL DO IPCA", ln=True, align="C")
		pdf.ln(3)

		pdf.set_font("Helvetica", "B", 8)
		pdf.set_fill_color(0, 26, 77)
		pdf.set_text_color(255, 255, 255)
		pdf.cell(40, 6, "Mes/Ano", border=1, fill=True, align="C")
		pdf.cell(40, 6, "IPCA Mensal (%)", border=1, fill=True, align="C")
		pdf.cell(50, 6, "Fator Acumulado", border=1, fill=True, align="C")
		pdf.ln()

		pdf.set_font("Helvetica", "", 8)
		pdf.set_text_color(30, 30, 30)
		fator_acum = 1.0
		for i, m in enumerate(meses_detalhes):
			fator_acum *= (1 + m["valor"] / 100)
			fill = i % 2 == 0
			if fill:
				pdf.set_fill_color(240, 245, 255)
			pdf.cell(40, 5, m["data"].strftime("%m/%Y"), border=1, fill=fill, align="C")
			pdf.cell(40, 5, f"{m['valor']:.2f}%", border=1, fill=fill, align="C")
			pdf.cell(50, 5, f"{fator_acum:.6f}", border=1, fill=fill, align="C")
			pdf.ln()

	pdf.ln(8)
	pdf.set_draw_color(212, 175, 55)
	pdf.set_line_width(0.3)
	pdf.line(20, pdf.get_y(), 190, pdf.get_y())
	pdf.ln(3)
	pdf.set_font("Helvetica", "I", 7)
	pdf.set_text_color(120, 120, 120)
	pdf.cell(0, 4, "Documento gerado automaticamente pelo sistema O Babilaca (IA)", ln=True, align="C")
	pdf.cell(0, 4, "Os valores sao meramente indicativos. Confirme sempre nas fontes oficiais.", ln=True, align="C")

	return bytes(pdf.output())


st.markdown(
	"""
<div class="header-box">
	<h1>📊 Cálculo IPCA</h1>
	<p>Correção monetária de valores por IPCA com base na série 433 do Banco Central.</p>
</div>
""",
	unsafe_allow_html=True,
)

st.markdown(
	"Informe os itens com seus valores originais e datas de referência. "
	"O sistema buscará o IPCA acumulado no Banco Central e calculará o valor corrigido até o mês mais recente disponível."
)

if "ipca_itens" not in st.session_state:
	st.session_state["ipca_itens"] = [{"descricao": "", "valor": 0.0}]

if "ipca_mes_global" not in st.session_state:
	st.session_state["ipca_mes_global"] = 1
if "ipca_ano_global" not in st.session_state:
	st.session_state["ipca_ano_global"] = datetime.now().year

st.markdown("#### 📅 Data de Referência (única para todos os itens)")
col_data_1, col_data_2 = st.columns([1, 1])
with col_data_1:
	mes_global = st.selectbox(
		"Mês",
		list(range(1, 13)),
		index=st.session_state["ipca_mes_global"] - 1,
		format_func=lambda x: f"{x:02d}",
		key="ipca_mes_global_widget",
	)
with col_data_2:
	ano_global = st.number_input(
		"Ano",
		min_value=1995,
		max_value=datetime.now().year,
		value=st.session_state["ipca_ano_global"],
		step=1,
		key="ipca_ano_global_widget",
	)

st.session_state["ipca_mes_global"] = int(mes_global)
st.session_state["ipca_ano_global"] = int(ano_global)

st.markdown("#### 📥 Importar Itens por Excel")
arquivo_excel = st.file_uploader(
	"Envie uma planilha .xlsx/.xls com colunas de descrição e valor",
	type=["xlsx", "xls"],
	key="ipca_excel_upload",
)
if arquivo_excel is not None:
	try:
		df_excel = pd.read_excel(arquivo_excel)
		st.caption(f"Pré-visualização: {len(df_excel)} linhas lidas da planilha")
		st.dataframe(df_excel.head(10), use_container_width=True, hide_index=True)
		if st.button("📥 Usar Itens da Planilha", key="ipca_import_excel_btn", use_container_width=True):
			itens_importados, erro_import = _importar_itens_excel(df_excel)
			if erro_import:
				st.error(erro_import)
			else:
				st.session_state["ipca_itens"] = itens_importados
				st.session_state.pop("ipca_resultado", None)
				st.success(f"{len(itens_importados)} itens importados com sucesso.")
				st.rerun()
	except Exception as e:
		st.error(f"Falha ao ler planilha: {e}")

st.markdown("#### 📝 Itens para Correção")

itens_ipca = st.session_state["ipca_itens"]
for i, item in enumerate(itens_ipca):
	cols = st.columns([4, 2, 1, 1, 0.5])
	with cols[0]:
		itens_ipca[i]["descricao"] = st.text_input(
			"Descrição",
			value=item["descricao"],
			key=f"ipca_desc_{i}",
			placeholder="Ex: Material de expediente",
		)
	with cols[1]:
		itens_ipca[i]["valor"] = st.number_input(
			"Valor Original (R$)",
			value=item["valor"],
			min_value=0.0,
			format="%.2f",
			key=f"ipca_val_{i}",
			step=0.01,
		)
	with cols[2]:
		st.caption(f"Mês/Ano: {st.session_state['ipca_mes_global']:02d}/{st.session_state['ipca_ano_global']}")
	with cols[3]:
		st.write("")
	with cols[4]:
		st.markdown("<br>", unsafe_allow_html=True)
		if len(itens_ipca) > 1 and st.button("🗑️", key=f"ipca_rm_{i}", help="Remover item"):
			itens_ipca.pop(i)
			st.rerun()

col_add, col_clear = st.columns([1, 1])
with col_add:
	if st.button("➕ Adicionar Item", key="ipca_add_item", use_container_width=True):
		itens_ipca.append({"descricao": "", "valor": 0.0})
		st.rerun()
with col_clear:
	if st.button("🧹 Limpar Tudo", key="ipca_clear_all", use_container_width=True):
		st.session_state["ipca_itens"] = [{"descricao": "", "valor": 0.0}]
		st.session_state.pop("ipca_resultado", None)
		st.rerun()

st.markdown("---")

if st.button("🔢 Calcular Correção IPCA", type="primary", use_container_width=True, key="ipca_calc_btn"):
	itens_validos = [it for it in itens_ipca if it["descricao"].strip() and it["valor"] > 0]
	if not itens_validos:
		st.error("Preencha pelo menos um item com descrição e valor maior que zero.")
	else:
		with st.spinner("Buscando dados do IPCA no Banco Central..."):
			try:
				ipca_dados = _buscar_ipca_bcb()
				if not ipca_dados:
					st.error("Não foi possível obter dados do IPCA. Tente novamente.")
				else:
					ultimo_mes = ipca_dados[-1]["data"]
					data_calc = datetime.now()
					dt_inicio_global = datetime(st.session_state["ipca_ano_global"], st.session_state["ipca_mes_global"], 1)
					resultados = []
					todos_meses = []
					if dt_inicio_global > ultimo_mes:
						st.error(
							f"A data de referência {dt_inicio_global.strftime('%m/%Y')} é posterior ao último IPCA disponível ({ultimo_mes.strftime('%m/%Y')})."
						)
						resultados = []
					for it in itens_validos:
						if dt_inicio_global > ultimo_mes:
							break
						fator, percentual, meses = _calcular_ipca_acumulado(ipca_dados, dt_inicio_global, ultimo_mes)
						valor_corrigido = it["valor"] * fator
						resultados.append(
							{
								"descricao": it["descricao"],
								"valor_original": it["valor"],
								"data_original": dt_inicio_global,
								"fator": fator,
								"percentual": percentual,
								"valor_corrigido": valor_corrigido,
							}
						)
						if not todos_meses:
							todos_meses = meses

					if resultados:
						st.session_state["ipca_resultado"] = {
							"itens": resultados,
							"meses": todos_meses,
							"data_calc": data_calc,
							"ultimo_ipca": ultimo_mes,
						}
			except Exception as e:
				st.error(f"Erro ao consultar API do BCB: {e}")

if "ipca_resultado" in st.session_state:
	res = st.session_state["ipca_resultado"]
	itens_res = res["itens"]
	data_calc = res["data_calc"]
	ultimo_ipca = res["ultimo_ipca"]

	st.markdown("---")
	st.markdown("#### 📈 Resultado da Correção")
	st.caption(
		f"IPCA acumulado até {ultimo_ipca.strftime('%m/%Y')} · "
		f"Calculado em {data_calc.strftime('%d/%m/%Y às %H:%M:%S')} · "
		"Fonte: BCB/IBGE (Série 433)"
	)

	df_res = pd.DataFrame(
		[
			{
				"Descrição": it["descricao"],
				"Valor Original": f"R$ {it['valor_original']:,.2f}",
				"Data Ref.": it["data_original"].strftime("%m/%Y"),
				"IPCA Acum. (%)": f"{it['percentual']:.4f}%",
				"Fator": f"{it['fator']:.6f}",
				"Valor Corrigido": f"R$ {it['valor_corrigido']:,.2f}",
			}
			for it in itens_res
		]
	)
	st.dataframe(df_res, use_container_width=True, hide_index=True)

	total_orig = sum(it["valor_original"] for it in itens_res)
	total_corr = sum(it["valor_corrigido"] for it in itens_res)
	diff = total_corr - total_orig

	c1, c2, c3 = st.columns(3)
	c1.metric("Total Original", f"R$ {total_orig:,.2f}")
	c2.metric("Total Corrigido", f"R$ {total_corr:,.2f}")
	c3.metric("Diferença", f"R$ {diff:,.2f}", delta=f"{(diff / total_orig * 100) if total_orig else 0:.2f}%")

	st.markdown("---")
	pdf_ipca = _gerar_pdf_ipca(itens_res, res["meses"], data_calc)
	st.download_button(
		"📥 Baixar Relatório Detalhado (PDF)",
		pdf_ipca,
		f"relatorio_ipca_{data_calc.strftime('%Y%m%d_%H%M%S')}.pdf",
		"application/pdf",
		use_container_width=True,
		key="dl_ipca_pdf",
	)
