"""Vídeo-aula simulado: como usar a página Cotação (pesquisa de preços de um item de catálogo)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a página Cotação"
DESCRICAO = (
    "Do código do item ao relatório: catálogo, consulta, filtros, outliers, seleção, estatísticas, "
    "Excel/PDF e fornecedores. Duração aproximada: 4 min, com narração."
)

_MOCK_CSS = r"""
.orient{background:var(--panel);border-left:5px solid var(--gold);border-radius:8px;padding:9px 12px;margin:10px 0}.orient b{color:var(--gold)}
.cat{background:#fff;color:#1f2937;border-radius:8px;overflow:hidden;border:1px solid #cbd5e1}
.cat .cb{background:#1d4ed8;color:#fff;padding:6px 12px;font-weight:700;font-size:12px}
.cat .sb{display:flex;gap:6px;padding:10px 12px}
.cat .inp{flex:1;border:1px solid #94a3b8;border-radius:6px;padding:7px 9px;min-height:30px;font-size:13px;color:#111}
.cat .go{background:#1d4ed8;color:#fff;border-radius:6px;padding:7px 12px;font-weight:700}
.cat .res{padding:0 12px 10px;display:none}.cat .res.on{display:block}
.cat .it{border:1px solid #cbd5e1;border-radius:6px;padding:7px 9px;margin-top:6px;display:flex;justify-content:space-between;gap:8px;font-size:12px}
.cat .it.sel{border-color:#1d4ed8;background:#dbeafe}.cat .it b{color:#1d4ed8}
.frm{display:grid;grid-template-columns:1fr 2fr 1fr;gap:10px;align-items:end}
#results{display:none}#results.on{display:block}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.uf{background:#ef4444;color:#fff;border-radius:6px;padding:3px 8px;font-weight:700;font-size:12px;display:inline-block;margin:0 4px 4px 0}.uf b{margin-left:6px}
.interv{background:var(--panel);border-left:4px solid var(--gold);border-radius:6px;padding:8px 10px;margin-top:8px}.interv b{color:var(--gold)}
.cards{display:grid;grid-template-columns:1fr 1fr .6fr .6fr;gap:10px;align-items:stretch}
.card{background:linear-gradient(135deg,#0a2540,#164863);border-left:5px solid var(--gold);border-radius:8px;padding:12px;text-align:center}
.card .k{color:var(--gold);font-size:11px;font-weight:800;letter-spacing:1px}.card .v{font-size:28px;font-weight:800;margin-top:4px}
.dl{display:flex;align-items:center;justify-content:center;text-align:center;font-size:11.5px}
.band{background:var(--panel);border-left:5px solid var(--gold);border-radius:8px;padding:9px 12px;margin-top:10px;display:none}.band.on{display:block}.band b{color:var(--gold)}
.st{text-align:center}.st th{text-align:center}.st td{font-weight:800;font-size:13px}
.frow{display:flex;gap:10px;margin-top:10px}.frow .btn{flex:0 0 auto;padding:8px 16px}
.newp{margin-top:18px;background:linear-gradient(135deg,#0a2540,#164863);border-left:5px solid var(--gold);border-radius:8px;padding:12px;text-align:center;color:var(--gold);font-weight:800}
.sw{display:flex;gap:8px;flex-wrap:wrap}
"""

_STAGE_HTML = r"""
<div class="hdr" id="m-hdr"><div class="l">⚓ MARINHA DO BRASIL ⚓</div><div class="s">AtaCotada</div><div class="u">PESQUISA DE PREÇOS DE MATERIAIS E SERVIÇOS</div></div>
<div class="orient"><b>📚 Orientação</b><br>Utilize o catálogo de materiais e serviços do Governo Federal para encontrar o código desejado.</div>

<div class="cat" id="m-cat">
  <div class="cb">Catálogo de Materiais e Serviços — Compras.gov.br</div>
  <div class="sb"><div class="inp" id="cat-q"></div><div class="go" id="cat-go">Buscar</div></div>
  <div class="res" id="cat-res">
    <div class="it" id="cat-it1"><span>Papel A4, 75 g/m², branco, resma com 500 folhas</span><b>Código 123456</b></div>
    <div class="it" id="cat-it2"><span>Papel A4 reciclado, 75 g/m², resma</span><b>Código 234567</b></div>
    <div class="it" id="cat-it3"><span>Papel A4 colorido, 75 g/m², pacote</span><b>Código 345678</b></div>
  </div>
</div>

<div class="sec">🔍 Consultar Item</div>
<div id="m-form">
  <div class="frm">
    <div><div class="lbl">Tipo de Item</div><div class="fld sel" id="f-tipo"><span id="f-tipo-v"></span>
      <div class="dd" id="dd-tipo"><div id="opt-mat">Material</div><div id="opt-serv">Serviço</div></div></div></div>
    <div><div class="lbl">Código do Item de Catálogo</div><div class="fld" id="f-cod"><span id="f-cod-v"></span><span class="ph" id="f-cod-ph">Ex: 123456</span></div></div>
    <div><div class="btn" id="b-consultar">🔎 Consultar</div></div>
  </div>
  <div class="spin" id="spin"><i></i><span>Consultando a base de preços praticados…</span></div>
</div>

<div id="results">
  <div class="sec" id="m-filt">⚙️ Filtros de Consulta</div>
  <div class="two">
    <div>
      <div class="lbl">Unidade de Fornecimento</div><div class="fld"><div class="sw" id="unchips"></div></div>
      <div class="lbl" style="margin-top:8px">Nome UASG</div><div class="fld"><span class="ph">Filtrar por nome...</span></div>
    </div>
    <div>
      <div class="lbl">Estado (UF)</div><div class="fld"><div class="sw" id="ufchips"></div></div>
      <div class="ck" id="cb-out" style="margin-top:12px"><span class="box" id="cb-out-b"></span><span>🔍 Remover outliers (IQR)</span></div>
    </div>
  </div>
  <div class="lbl" style="margin-top:10px">Faixa de Preço Unitário (R$)</div>
  <div class="slid" id="slid"><i style="left:0"></i><i style="right:0"></i></div>
  <div class="interv" id="interv"></div>

  <div class="sec" id="m-res">📊 Resultados</div>
  <div class="cards" id="cards">
    <div class="card"><div class="k">REGISTROS ENCONTRADOS</div><div class="v" id="c-reg">0</div></div>
    <div class="card"><div class="k">OUTLIERS REMOVIDOS</div><div class="v" id="c-out">0</div></div>
    <div class="btn dl" id="btn-xls">📊 Excel</div><div class="btn dl" id="btn-pdf">📄 PDF</div>
  </div>
  <div class="band" id="band"></div>
  <h4 style="margin:14px 0 6px;font-size:14px">Itens encontrados</h4>
  <table id="tbl"><thead><tr><th></th><th>UASG</th><th>UF</th><th>Unidade</th><th>Preço Unitário</th><th>Data</th></tr></thead><tbody></tbody></table>
  <table class="st" id="stats" style="margin-top:12px"><thead><tr><th>Preço Mínimo</th><th>Preço Unitário Médio</th><th>Preço Unitário Mediano</th><th>Preço Máximo</th><th>Desvio Padrão</th><th>Coef. de Variação</th></tr></thead><tbody><tr id="stats-row"></tr></tbody></table>
  <div class="frow"><div class="btn" id="btn-forn">📞 Consultar Fornecedores</div></div>
  <div class="spin" id="spinf"><i></i><span>Consultando dados de fornecedores…</span></div>
  <div class="frow" id="forn-dl" style="display:none"><div class="btn">📋 Baixar Fornecedores (HTML)</div><div class="btn">📊 Baixar Fornecedores (Excel)</div></div>
  <div class="newp" id="newp">Deseja realizar uma nova pesquisa?</div>
  <div class="frow" style="justify-content:center"><div class="btn" id="btn-new" style="width:60%">🔄 Nova Pesquisa</div></div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const ROWS=[
 {id:1,uasg:'ÓRGÃO EXEMPLO A',uf:'RJ',un:'RESMA',p:24.90,d:'12/08/2026'},
 {id:2,uasg:'ÓRGÃO EXEMPLO B',uf:'RJ',un:'RESMA',p:26.50,d:'03/09/2026'},
 {id:3,uasg:'ÓRGÃO EXEMPLO C',uf:'SP',un:'RESMA',p:23.80,d:'21/06/2026'},
 {id:4,uasg:'ÓRGÃO EXEMPLO D',uf:'DF',un:'RESMA',p:25.40,d:'15/05/2026'},
 {id:5,uasg:'ÓRGÃO EXEMPLO E',uf:'MG',un:'RESMA',p:27.10,d:'30/07/2026'},
 {id:6,uasg:'ÓRGÃO EXEMPLO F',uf:'SP',un:'RESMA',p:22.90,d:'09/10/2026'},
 {id:7,uasg:'ÓRGÃO EXEMPLO G',uf:'RJ',un:'RESMA',p:25.00,d:'18/04/2026'},
 {id:8,uasg:'ÓRGÃO EXEMPLO H',uf:'DF',un:'CAIXA',p:189.90,d:'27/02/2026'},
 {id:9,uasg:'ÓRGÃO EXEMPLO I',uf:'SP',un:'RESMA',p:61.50,d:'11/03/2026'}
];
let S;
function resetS(){S={q:'',catres:false,catsel:false,tipo:'',dd:false,cod:'',spin:false,results:false,un:{RESMA:true,CAIXA:true},ufs:{RJ:true,SP:true,MG:true,DF:true},out:false,sel:[],spinf:false,forn:false};}
const num=v=>v.toFixed(2).replace('.',',');
function quant(a,q){const s=[...a].sort((x,y)=>x-y),pos=(s.length-1)*q,lo=Math.floor(pos),hi=Math.ceil(pos);return s[lo]+(s[hi]-s[lo])*(pos-lo);}
function visible(){let r=ROWS.filter(x=>S.ufs[x.uf]&&S.un[x.un]);let removed=0,lim=null;
  if(S.out&&r.length>3){const ps=r.map(x=>x.p),q1=quant(ps,.25),q3=quant(ps,.75),i=q3-q1;lim=[q1-1.5*i,q3+1.5*i];const k=r.filter(x=>x.p>=lim[0]&&x.p<=lim[1]);removed=r.length-k.length;r=k;}
  return{rows:r,removed,lim};}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('cat-q',S.q);$('#cat-res').classList.toggle('on',S.catres);$('#cat-it1').classList.toggle('sel',S.catsel);
  T('f-tipo-v',S.tipo);$('#dd-tipo').classList.toggle('on',S.dd);
  T('f-cod-v',S.cod);$('#f-cod-ph').style.display=S.cod?'none':'inline';
  $('#spin').classList.toggle('on',S.spin);$('#spinf').classList.toggle('on',S.spinf);
  $('#results').classList.toggle('on',S.results);$('#forn-dl').style.display=S.forn?'flex':'none';
  $('#unchips').innerHTML=Object.keys(S.un).filter(u=>S.un[u]).map(u=>'<span class="uf">'+u+'<b id="un-'+u+'-x">×</b></span>').join('');
  $('#ufchips').innerHTML=Object.keys(S.ufs).filter(u=>S.ufs[u]).map(u=>'<span class="uf">'+u+'<b id="uf-'+u+'-x">×</b></span>').join('');
  $('#cb-out-b').className='box'+(S.out?' on':'');$('#cb-out-b').textContent=S.out?'✓':'';
  const v=visible(),ps=v.rows.map(x=>x.p);
  S.sel=S.sel.filter(id=>v.rows.some(x=>x.id===id));
  const base=S.sel.length?v.rows.filter(x=>S.sel.includes(x.id)):v.rows,bp=base.map(x=>x.p);
  if(ps.length)$('#interv').innerHTML='<b>Intervalo selecionado:</b> '+brl(Math.min(...ps))+' até '+brl(Math.max(...ps));
  T('c-reg',v.rows.length);T('c-out',v.removed);
  $('#band').classList.toggle('on',!!(S.out&&v.lim));if(S.out&&v.lim)$('#band').innerHTML='<b>📊 Faixa válida (sem outliers):</b><br>'+brl(v.lim[0])+' até '+brl(v.lim[1]);
  $('#tbl tbody').innerHTML=v.rows.map(x=>'<tr class="'+(S.sel.includes(x.id)?'sel':'')+'"><td><span class="box'+(S.sel.includes(x.id)?' on':'')+'" id="r'+x.id+'" style="'+(S.sel.includes(x.id)?'background:#facc15;border-color:#facc15;color:#111':'')+'">'+(S.sel.includes(x.id)?'✓':'')+'</span></td><td>'+x.uasg+'</td><td>'+x.uf+'</td><td>'+x.un+'</td><td>'+brl(x.p)+'</td><td>'+x.d+'</td></tr>').join('');
  const suf=S.sel.length?' (seleção)':'';T('btn-xls','📊 Excel'+suf);T('btn-pdf','📄 PDF'+suf);
  if(bp.length){const m=mean(bp),med=quant(bp,.5),sd=bp.length>1?Math.sqrt(bp.reduce((a,b)=>a+(b-m)**2,0)/(bp.length-1)):0,cv=m?sd/m*100:0;
    $('#stats-row').innerHTML=[brl(Math.min(...bp)),brl(m),brl(med),brl(Math.max(...bp)),brl(sd),num(cv)+'%'].map(t=>'<td>'+t+'</td>').join('');}
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Cotação',
 b:'A página <b>Cotação</b> pesquisa os <b>preços praticados</b> em compras públicas federais (base do Compras.gov.br) para <b>um item de catálogo</b> por vez. Ela mostra os registros, permite <b>filtrar</b>, calcula <b>estatísticas</b> e gera relatório em <b>Excel</b> e <b>PDF</b>.',
 tip:'💡 Para pesquisar <b>vários itens de uma vez</b>, use a <b>Cotação Rápida</b>. Para um item específico, com filtros detalhados, use esta página.',
 run:async a=>{a.unring();await a.top();a.ring('#m-hdr','Página Cotação');await a.sleep(2800);a.unring();}},

{short:'Código',t:'Passo 1 — Descubra o código do item',
 b:'Antes de consultar, é preciso o <b>código do catálogo</b>: <b>CATMAT</b> para materiais ou <b>CATSERV</b> para serviços. Use o catálogo do Governo Federal exibido na própria página: <b>digite a descrição</b>, clique em <b>Buscar</b>, escolha o item mais parecido e <b>anote o código</b>.',
 tip:'💡 Leia a descrição completa antes de escolher: unidade de fornecimento e características mudam o preço.',
 run:async a=>{a.unring();await a.scroll('#m-cat',40);a.ring('#m-cat','Catálogo de materiais e serviços');await a.sleep(1500);
  await a.click('#cat-q');await a.type('#cat-q','papel A4 75g');a.set(S=>S.q='papel A4 75g');
  await a.click('#cat-go',()=>a.set(S=>S.catres=true));a.unring();
  await a.click('#cat-it1',()=>a.set(S=>S.catsel=true));a.ring('#cat-it1','Código do item: 123456');await a.sleep(2500);a.unring();}},

{short:'Tipo e código',t:'Passo 2 — Informe o tipo e o código',
 b:'Role até <b>🔍 Consultar Item</b>. Em <b>Tipo de Item</b> escolha <b>Material</b> ou <b>Serviço</b>. Em <b>Código do Item de Catálogo</b> digite o código — somente <b>números</b>, no máximo 20 dígitos.',
 tip:'💡 Se o código estiver vazio ou tiver letras, o sistema avisa e não consulta.',
 run:async a=>{a.unring();await a.scroll('#m-form',90);a.ring('#m-form','Preencha o formulário');await a.sleep(1200);
  await a.click('#f-tipo',()=>a.set(S=>S.dd=true));await a.click('#opt-mat',()=>a.set(S=>{S.tipo='Material';S.dd=false;}));
  await a.click('#f-cod');await a.type('#f-cod-v','123456',110);a.set(S=>S.cod='123456');await a.sleep(800);a.unring();}},

{short:'Consultar',t:'Passo 3 — Clique em Consultar',
 b:'Clique em <b>🔎 Consultar</b>. O sistema busca as compras públicas do item e considera só a <b>janela dos últimos 12 meses</b>. Ao terminar aparecem os <b>Filtros</b> e os <b>Resultados</b>, com o total de <b>registros encontrados</b>.',
 tip:'💡 Se nada for encontrado, confira o código e o tipo (Material × Serviço).',
 run:async a=>{a.unring();await a.click('#b-consultar',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.results=true;});
  await a.scroll('#m-res',70);a.ring('#c-reg','Registros encontrados');await a.sleep(2600);a.unring();}},

{short:'Unidade',t:'Passo 4 — Compare a mesma unidade',
 b:'Em <b>⚙️ Filtros de Consulta</b>, comece pela <b>Unidade de Fornecimento</b>. Preços de <b>resma</b> e de <b>caixa</b> não se comparam! Retire <b>CAIXA</b> clicando no “×”: o registro de R$ 189,90 (caixa com várias resmas) sai da lista e os números se atualizam.',
 tip:'💡 Dê preferência à unidade que você vai comprar. Outros filtros: nome da unidade, nome da UASG e faixa de preço.',
 run:async a=>{a.unring();await a.scroll('#m-filt',40);a.ring('#unchips','Unidade de fornecimento');await a.sleep(1500);
  await a.click('#un-CAIXA-x',()=>a.set(S=>S.un.CAIXA=false));await a.sleep(1500);a.unring();}},

{short:'Estado',t:'Passo 5 — Filtre por estado e faixa de preço',
 b:'O filtro <b>Estado (UF)</b> restringe os registros às regiões de interesse. Aqui retiramos <b>MG</b>. A <b>Faixa de Preço Unitário</b> também pode ser reduzida arrastando as pontas do controle, e o quadro <b>Intervalo selecionado</b> mostra o menor e o maior preço que restaram.',
 tip:'💡 Priorize estados próximos ou com realidade logística parecida com a sua.',
 run:async a=>{a.unring();await a.scroll('#m-filt',40);a.ring('#ufchips','Filtro de UF');await a.sleep(1300);
  await a.click('#uf-MG-x',()=>a.set(S=>S.ufs.MG=false));await a.sleep(900);a.unring();a.ring('#interv','Intervalo selecionado');await a.sleep(2200);a.unring();}},

{short:'Outliers',t:'Passo 6 — Remova os valores discrepantes',
 b:'Marque <b>🔍 Remover outliers (IQR)</b>. <b>Outlier</b> é um preço muito fora do padrão. Aqui há um registro de <b>R$ 61,50</b> por resma, bem acima dos demais. O método <b>IQR</b> calcula uma <b>faixa válida</b> e descarta o que fica fora dela; veja <b>Outliers removidos</b> e a faixa válida.',
 tip:'💡 Analise o que foi removido: o preço pode estar errado, ser de outra unidade ou de compra atípica.',
 run:async a=>{a.unring();await a.scroll('#m-filt',40);a.ring('#cb-out','Remover outliers');await a.click('#cb-out',()=>a.set(S=>S.out=true));
  await a.scroll('#m-res',70);a.unring();a.ring('#c-out','Outliers removidos');await a.sleep(1800);a.unring();a.ring('#band','Faixa válida');await a.sleep(2200);a.unring();}},

{short:'Seleção',t:'Passo 7 — Escolha os preços da pesquisa',
 b:'Na tabela <b>Itens encontrados</b>, <b>marque as linhas</b> que fazem sentido para a sua pesquisa. Os cálculos e o relatório passam a considerar <b>só a seleção</b>. Se você não marcar nenhuma linha, o sistema usa <b>todas</b> as linhas visíveis.',
 tip:'💡 Descarte registros de órgão muito distante da sua realidade ou com descrição pouco parecida.',
 run:async a=>{a.unring();await a.scroll('#tbl',60);a.ring('#tbl','Itens encontrados');await a.sleep(1300);
  for(const id of [1,2,4,6])await a.click('#r'+id,()=>a.set(S=>S.sel.push(id)));await a.sleep(900);a.unring();}},

{short:'Estatísticas',t:'Passo 8 — Leia as estatísticas',
 b:'Abaixo da tabela estão <b>preço mínimo</b>, <b>médio</b>, <b>mediano</b>, <b>máximo</b>, <b>desvio padrão</b> e <b>coeficiente de variação</b> (CV) da seleção. Quanto <b>menor o CV</b>, mais parecidos são os preços; CV alto indica dispersão e pede nova análise dos registros.',
 tip:'💡 A escolha entre média, mediana ou menor preço como referência deve ser <b>justificada</b> no processo.',
 run:async a=>{a.unring();await a.scroll('#stats',150);a.ring('#stats','Estatísticas da seleção');await a.sleep(4200);a.unring();}},

{short:'Relatório',t:'Passo 9 — Baixe o relatório',
 b:'Clique em <b>📊 Excel</b> ou <b>📄 PDF</b>. Como há linhas marcadas, os botões mostram <b>“(seleção)”</b>: o relatório traz só os registros escolhidos, com as estatísticas e a informação sobre outliers.',
 tip:'💡 Anexe o relatório ao processo como memória da pesquisa de preços.',
 run:async a=>{a.unring();await a.scroll('#m-res',70);a.ring('#btn-xls','Excel');await a.click('#btn-xls',()=>a.toast('✔ relatorio_AtaCotada_20261021_101500.xlsx'));
  a.unring();a.ring('#btn-pdf','PDF');await a.click('#btn-pdf',()=>a.toast('✔ relatorio_AtaCotada_20261021_101502.pdf'));await a.sleep(900);a.unring();}},

{short:'Fornecedores',t:'Passo 10 — Consulte os fornecedores (opcional)',
 b:'Clique em <b>📞 Consultar Fornecedores</b> para reunir os dados das empresas que venderam o item nos registros selecionados. Depois baixe a lista em <b>HTML</b> ou <b>Excel</b> — útil para enviar pedidos de cotação.',
 tip:'💡 A etapa seguinte natural é a página <b>Cotação Direta</b>, que pede orçamento por e-mail.',
 run:async a=>{a.unring();await a.scroll('#btn-forn',200);await a.click('#btn-forn',()=>a.set(S=>S.spinf=true));await a.sleep(1700);a.set(S=>{S.spinf=false;S.forn=true;});
  a.ring('#forn-dl','Downloads de fornecedores');await a.sleep(2600);a.unring();}},

{short:'Nova pesquisa',t:'Passo 11 — Faça uma nova pesquisa',
 b:'Ao final, clique em <b>🔄 Nova Pesquisa</b> para limpar os resultados e consultar outro item. <b>Resumo:</b> 1) ache o código; 2) tipo e código; 3) Consultar; 4) mesma unidade; 5) UF e faixa; 6) outliers; 7) selecione os preços; 8) estatísticas; 9) baixe o relatório.',
 tip:'🎉 Fim da aula! Os dados desta aula são fictícios.',
 run:async a=>{a.unring();await a.scroll('#btn-new',250);a.ring('#btn-new','Nova Pesquisa');await a.click('#btn-new',()=>a.set(S=>{S.results=false;S.cod='';S.tipo='';S.sel=[];S.out=false;S.forn=false;S.un={RESMA:true,CAIXA:true};S.ufs={RJ:true,SP:true,MG:true,DF:true};}));
  a.unring();await a.top();await a.sleep(1200);}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="cotacao")
