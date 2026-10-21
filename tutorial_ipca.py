"""Vídeo-aula simulado: como usar a página Cálculo IPCA (correção monetária de valores)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar o Cálculo IPCA"
DESCRICAO = (
    "Corrigir valores pelo IPCA acumulado: data de referência, itens, importação de planilha, "
    "resultado e relatório em PDF. Duração aproximada: 2 min."
)

_MOCK_CSS = r"""
.row3{display:grid;grid-template-columns:4fr 2fr 1.2fr .5fr;gap:10px;align-items:end;margin-bottom:8px}
.fld .ph{color:#7e93b3}
.trash{background:#1b2a47;border:1px solid #3b4d70;border-radius:7px;text-align:center;padding:8px 0}
#i-res{display:none}#i-res.on{display:block}
.ok{background:rgba(34,197,94,.15);border:1px solid rgba(34,197,94,.4);color:#bbf7d0;border-radius:8px;padding:8px 11px;margin-top:8px;font-size:12px;display:none}.ok.on{display:block}
#i-tab td,#i-tab th{font-size:11px}
.m3{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:10px}.m3 .k{font-size:11px;color:#b6cae2}.m3 .v{font-size:21px;font-weight:700}.m3 .d{font-size:11px;color:#86efac}
#i-prev{display:none}#i-prev.on{display:block}
"""

_STAGE_HTML = r"""
<div class="qh" id="i-head"><div class="qs">📊</div><div><b>Cálculo IPCA</b><small>Correção monetária de valores por IPCA com base na série 433 do Banco Central.</small></div></div>
<div class="cap2" style="color:#dbe7f7">Informe os itens com seus valores originais e datas de referência. O sistema buscará o IPCA acumulado no Banco Central e calculará o valor corrigido até o mês mais recente disponível.</div>

<div class="sec2">📅 Data de Referência (única para todos os itens)</div>
<div class="two">
  <div><div class="lbl">Mês</div><div class="fld sel" id="i-mes"><span id="i-mes-v">01</span><div class="dd" id="i-dd"><div>01</div><div>02</div><div id="i-m03">03</div><div>04</div></div></div></div>
  <div><div class="lbl">Ano</div><div class="fld" id="i-ano"><span id="i-ano-v">2026</span></div></div>
</div>

<div class="sec2">📥 Importar Itens por Excel</div>
<div class="lbl">Envie uma planilha .xlsx/.xls com colunas de descrição e valor</div>
<div class="upl" id="i-up">Arraste a planilha aqui · .xlsx, .xls <span>Procurar</span></div>
<div id="i-prev"><div class="cap2">Pré-visualização: 2 linhas lidas da planilha</div>
  <table><thead><tr><th>Descrição</th><th>Valor</th></tr></thead><tbody><tr><td>Material de expediente</td><td>12500</td></tr><tr><td>Serviço de manutenção predial</td><td>8300</td></tr></tbody></table>
  <div class="btn" id="i-usar" style="margin-top:8px">📥 Usar Itens da Planilha</div></div>
<div class="ok" id="i-okimp">2 itens importados com sucesso.</div>

<div class="sec2">📝 Itens para Correção</div>
<div id="i-itens"></div>
<div class="two" style="margin-top:6px"><div class="btn" id="i-add">➕ Adicionar Item</div><div class="btn" id="i-clear">🧹 Limpar Tudo</div></div>
<hr style="border-color:#1e5b9f;margin:14px 0">
<div class="btn pri" id="i-calc" style="padding:10px;font-size:13.5px">🔢 Calcular Correção IPCA</div>
<div class="spin" id="i-spin"><i></i><span>Buscando dados do IPCA no Banco Central...</span></div>

<div id="i-res">
  <hr style="border-color:#1e5b9f;margin:14px 0">
  <div class="sec2">📈 Resultado da Correção</div>
  <div class="cap2" id="i-cap"></div>
  <table id="i-tab"><thead><tr><th>Descrição</th><th>Valor Original</th><th>Data Ref.</th><th>IPCA Acum. (%)</th><th>Fator</th><th>Valor Corrigido</th></tr></thead><tbody></tbody></table>
  <div class="m3" id="i-m3"></div>
  <div class="btn" id="i-pdf" style="margin-top:12px">📥 Baixar Relatório Detalhado (PDF)</div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const FATOR=1.084321;  // exemplo fictício: IPCA acumulado de 03/2024 a 09/2026
let S;
function resetS(){S={mes:'01',ano:'2026',dd:false,prev:false,imp:false,itens:[{d:'',v:null}],spin:false,res:false};}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('i-mes-v',S.mes);T('i-ano-v',S.ano);$('#i-dd').classList.toggle('on',S.dd);
  $('#i-prev').classList.toggle('on',S.prev);$('#i-okimp').classList.toggle('on',S.imp);
  $('#i-itens').innerHTML=S.itens.map((x,i)=>'<div class="row3"><div><div class="lbl">Descrição</div><div class="fld" id="id'+i+'">'+(x.d||'<span class="ph">Ex: Material de expediente</span>')+'</div></div><div><div class="lbl">Valor Original (R$)</div><div class="fld" id="iv'+i+'">'+(x.v!=null?x.v.toFixed(2).replace('.',','):'0,00')+'</div></div><div class="cap2">Mês/Ano:<br>'+S.mes+'/'+S.ano+'</div><div>'+(S.itens.length>1?'<div class="trash">🗑️</div>':'')+'</div></div>').join('');
  $('#i-spin').classList.toggle('on',S.spin);$('#i-res').classList.toggle('on',S.res);
  if(!S.res)return;
  const v=S.itens.filter(x=>x.d&&x.v>0);
  $('#i-cap').textContent='IPCA acumulado até 09/2026 · Calculado em 21/10/2026 às 10:15:00 · Fonte: BCB/IBGE (Série 433)';
  $('#i-tab tbody').innerHTML=v.map(x=>'<tr><td>'+x.d+'</td><td>'+brl(x.v)+'</td><td>'+S.mes+'/'+S.ano+'</td><td>'+pct((FATOR-1)*100,4)+'</td><td>'+FATOR.toFixed(6).replace('.',',')+'</td><td><b>'+brl(x.v*FATOR)+'</b></td></tr>').join('');
  const o=v.reduce((a,x)=>a+x.v,0),c=o*FATOR;
  $('#i-m3').innerHTML='<div><div class="k">Total Original</div><div class="v">'+brl(o)+'</div></div><div><div class="k">Total Corrigido</div><div class="v">'+brl(c)+'</div></div><div><div class="k">Diferença</div><div class="v">'+brl(c-o)+'</div><div class="d">▲ '+pct((c-o)/o*100)+'</div></div>';
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Cálculo IPCA',
 b:'A página <b>Cálculo IPCA</b> faz a <b>correção monetária</b> de valores pelo <b>IPCA acumulado</b>, usando a <b>série 433 do Banco Central</b>. Você informa o valor original e o mês/ano de referência, e o sistema atualiza o valor até o <b>último IPCA disponível</b>.',
 tip:'💡 Útil para atualizar preços de pesquisas antigas, atas e contratos, trazendo-os a valor presente.',
 run:async a=>{a.unring();await a.top();a.ring('#i-head','Correção pelo IPCA');await a.sleep(2800);a.unring();}},

{short:'Data',t:'Passo 1 — Defina a data de referência',
 b:'Em <b>Data de Referência</b>, escolha o <b>mês</b> e o <b>ano</b> em que o valor original foi praticado. Essa data vale <b>para todos os itens</b> da lista. Aqui usamos <b>03/2024</b>.',
 tip:'💡 A data de referência não pode ser posterior ao último IPCA divulgado: o sistema avisa se isso acontecer.',
 run:async a=>{a.unring();await a.scroll('#i-mes',90);await a.click('#i-mes',()=>a.set(S=>S.dd=true));await a.click('#i-m03',()=>a.set(S=>{S.mes='03';S.dd=false;}));
  await a.click('#i-ano');await a.type('#i-ano-v','2024',140);a.set(S=>S.ano='2024');a.ring('#i-mes','Referência: 03/2024',4);await a.sleep(2200);a.unring();}},

{short:'Itens',t:'Passo 2 — Digite os itens e valores',
 b:'Em <b>Itens para Correção</b>, preencha a <b>descrição</b> e o <b>valor original (R$)</b> de cada item. Para incluir mais linhas, clique em <b>➕ Adicionar Item</b>. A lixeira 🗑️ remove um item e <b>🧹 Limpar Tudo</b> recomeça a lista.',
 tip:'💡 Itens sem descrição ou com valor zero são ignorados no cálculo.',
 run:async a=>{a.unring();await a.scroll('#i-itens',120);await a.click('#id0');await a.type('#id0','Material de expediente',70);await a.click('#iv0');await a.type('#iv0','12500,00',110);
  a.set(S=>{S.itens[0]={d:'Material de expediente',v:12500};});
  await a.click('#i-add',()=>a.set(S=>S.itens.push({d:'',v:null})));await a.click('#id1');await a.type('#id1','Serviço de manutenção predial',60);await a.click('#iv1');await a.type('#iv1','8300,00',110);
  a.set(S=>{S.itens[1]={d:'Serviço de manutenção predial',v:8300};});await a.sleep(900);}},

{short:'Planilha',t:'Alternativa — Importe uma planilha Excel',
 b:'Com muitos itens, <b>importe uma planilha</b> .xlsx/.xls com colunas de <b>descrição</b> e <b>valor</b>. O sistema mostra a <b>pré-visualização</b>; clique em <b>📥 Usar Itens da Planilha</b> para substituir a lista atual pelos itens do arquivo.',
 tip:'💡 Confira a pré-visualização antes de usar: a importação substitui os itens digitados.',
 run:async a=>{a.unring();await a.scroll('#i-up',100);a.ring('#i-up','Importar planilha');await a.sleep(1500);a.set(S=>S.prev=true);await a.sleep(800);
  a.ring('#i-prev','Pré-visualização');await a.sleep(1800);a.unring();await a.click('#i-usar',()=>a.set(S=>{S.imp=true;S.prev=false;}));await a.sleep(1500);}},

{short:'Calcular',t:'Passo 3 — Clique em Calcular Correção IPCA',
 b:'Clique em <b>🔢 Calcular Correção IPCA</b>. O sistema consulta o <b>Banco Central</b>, acumula o IPCA <b>mês a mês</b> desde a data de referência até o último mês divulgado e aplica o <b>fator de correção</b> a cada item.',
 tip:'💡 Se a consulta ao Banco Central falhar, o sistema avisa e você pode tentar novamente.',
 run:async a=>{a.unring();await a.scroll('#i-calc',250);await a.click('#i-calc',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.res=true;});await a.sleep(500);}},

{short:'Resultado',t:'Passo 4 — Leia o resultado da correção',
 b:'A tabela mostra, para cada item: <b>valor original</b>, <b>data de referência</b>, <b>IPCA acumulado (%)</b>, o <b>fator</b> e o <b>valor corrigido</b>. Abaixo, os <b>totais</b> (original, corrigido e a diferença em R$ e %). A legenda informa até qual mês o IPCA foi acumulado e a fonte (BCB/IBGE, série 433).',
 tip:'💡 Os percentuais desta aula são fictícios; na ferramenta real vêm da série oficial do Banco Central.',
 run:async a=>{a.unring();await a.scroll('#i-cap',70);a.ring('#i-tab','Valor corrigido');await a.sleep(2800);a.unring();a.ring('#i-m3','Totais');await a.sleep(2800);a.unring();}},

{short:'PDF',t:'Passo 5 — Baixe o relatório em PDF',
 b:'Clique em <b>📥 Baixar Relatório Detalhado (PDF)</b>. O documento traz os itens, o <b>fator</b> e a <b>memória de cálculo mês a mês</b>, para anexar ao processo. <b>Resumo:</b> 1) data de referência; 2) itens e valores (ou planilha); 3) calcular; 4) conferir o resultado; 5) baixar o PDF.',
 tip:'🎉 Fim da aula! O relatório é indicativo: confirme os índices nas fontes oficiais antes de usar em decisões.',
 run:async a=>{a.unring();await a.scroll('#i-pdf',250);a.ring('#i-pdf','Relatório em PDF');await a.click('#i-pdf',()=>a.toast('✔ relatorio_ipca_20261021_101500.pdf'));await a.sleep(1500);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS)
