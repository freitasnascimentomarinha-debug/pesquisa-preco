"""Vídeo-aula simulado: como usar a página Cotação Rápida (vários itens de uma vez, com mapa comparativo)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a Cotação Rápida"
DESCRICAO = (
    "Da lista de itens ao mapa comparativo em PDF/Excel: carregar, conferir o CATMAT, estimativa de preço, "
    "cotar, ler os resultados e baixar. Duração aproximada: 3 min."
)

_MOCK_CSS = r"""
.qh{display:flex;align-items:center;gap:10px;background:linear-gradient(135deg,#001a4d,#0033cc);border:1px solid rgba(96,165,250,.45);border-radius:10px;padding:12px 14px}
.qs{width:34px;height:34px;background:var(--gold);border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:18px;flex:0 0 auto}
.qh b{font-size:17px}.qh small{color:#bfdbfe;font-size:10.5px;line-height:1.3;display:block}
.qb{margin-left:auto;color:var(--gold);font-size:9px;font-weight:800;letter-spacing:.08em;text-align:right;flex:0 0 auto}
.panel{background:rgba(8,26,57,.78);border:1px solid #1e5b9f;border-radius:9px;padding:10px 12px;margin:10px 0 8px}
.panel h3{color:var(--gold);font-size:14px;margin:0 0 3px}.panel p{color:#b6cae2;font-size:11px;margin:0}
.ta{background:rgba(7,20,42,.8);border:1px solid #2b6cb0;border-radius:7px;padding:8px 10px;min-height:76px;white-space:pre-wrap;font-size:12.5px;line-height:1.45}
.ta .ph{color:#7e93b3}
.upl{border:1px dashed #2b6cb0;border-radius:7px;padding:9px 12px;color:#9fb6d8;font-size:12px;background:rgba(7,20,42,.5);display:flex;justify-content:space-between}
.upl span{border:1px solid #3b4d70;border-radius:6px;padding:2px 9px;color:#fff;font-weight:700}
.cap2{color:#9fb6d8;font-size:11px;margin:8px 0;line-height:1.4}
.pri{background:#ef4444;border-color:#ef4444;color:#fff}
#q-loaded,#q-hint-off{display:none}#q-loaded.on{display:block}
#q-tab td,#q-tab th{font-size:10.5px;padding:5px 5px;vertical-align:middle}
#q-tab td.c{color:#fde68a;font-weight:700}
.ed{border-bottom:1px dashed #5b7fb3}
.low{color:#fcd34d}.good{color:#86efac}
.prog{display:none;margin-top:10px}.prog.on{display:block}
.prog .t{font-size:11.5px;color:#dbe7f7;margin-bottom:4px}.prog .b{height:8px;background:#0b2a63;border-radius:6px;overflow:hidden}.prog .b i{display:block;height:100%;background:#ef4444;width:0;transition:width .5s}
#q-res{display:none}#q-res.on{display:block}
.mets{display:grid;grid-template-columns:.8fr 1fr 1fr 1fr;gap:8px;align-items:center;margin-top:6px}
.met .k{font-size:10.5px;color:#b6cae2}.met .v{font-size:24px;font-weight:700}
.chip{display:inline-block;border-radius:999px;padding:3px 9px;font-size:10.5px;font-weight:700}
.cg{background:rgba(34,197,94,.18);color:#86efac;border:1px solid rgba(34,197,94,.4)}.cr{background:rgba(245,158,11,.15);color:#fcd34d;border:1px solid rgba(245,158,11,.4)}.cl{background:rgba(239,68,68,.14);color:#fca5a5;border:1px solid rgba(239,68,68,.4)}
.alert{border-radius:8px;padding:9px 11px;margin:7px 0;font-size:11.5px;line-height:1.4}
.alert.w{background:rgba(245,158,11,.14);border:1px solid rgba(245,158,11,.4);color:#fde68a}.alert.i{background:rgba(59,130,246,.15);border:1px solid rgba(59,130,246,.4);color:#bfdbfe}
.alert .btn{display:inline-block;margin-top:7px;padding:5px 11px;font-size:11px}
#q-map td,#q-map th{font-size:10px;padding:5px 4px;text-align:left}
#q-map td.n{text-align:right;white-space:nowrap}#q-map th{white-space:nowrap}
.tot{margin:8px 0}.tot .k{font-size:11px;color:#b6cae2}.tot .v{font-size:24px;font-weight:700}
.exph{background:#0b2447;border:1px solid var(--line);border-radius:7px;padding:8px 11px;margin-top:6px;font-size:11.5px;display:flex;gap:8px}.exph span{margin-left:auto;color:#9fb6d8}
.expb{display:none;background:#08203f;border:1px solid var(--line);border-top:0;border-radius:0 0 7px 7px;padding:9px 11px}.expb.on{display:block}
.expb td,.expb th{font-size:10px;padding:4px}
.expb .cp{color:#b6cae2;font-size:10.5px;margin:6px 0}
"""

_STAGE_HTML = r"""
<div class="qh" id="q-head"><div class="qs">⚡</div><div><b>Cotação Rápida</b><small>Cote vários itens de uma vez (materiais e serviços): o sistema acha o CATMAT/CATSERV, busca os preços praticados e monta o mapa comparativo em PDF.</small></div><span class="qb">PREÇOS PRATICADOS<br>· COMPRAS.GOV</span></div>

<div class="panel" id="q-lista"><h3>Lista de itens</h3><p>Digite ou cole um item por linha, com a quantidade ao lado se quiser (ex.: “caneta azul - 100”, “50 resmas de papel A4”), ou importe uma planilha (CSV ou Excel). Com quantidades, o mapa já traz o valor total de cada item e do orçamento.</p></div>
<div class="lbl">Descrições dos itens</div>
<div class="ta" id="q-ta"><span id="q-ta-v"></span><span class="ph" id="q-ta-ph">Ex:
Resma de papel A4 75 g/m² - 50
10 notebook 15 polegadas 16 GB
Detergente líquido neutro 5 litros; 30 un</span></div>
<div class="lbl" style="margin-top:8px">Ou importe uma lista (CSV ou Excel)</div>
<div class="upl" id="q-up">Arraste a planilha aqui · .csv, .xlsx, .xls <span>Procurar</span></div>
<div class="btn" id="b-carregar" style="width:150px;margin-top:10px">📥 Carregar</div>
<div class="spin" id="spinL"><i></i><span>Procurando o CATMAT mais próximo de cada item…</span></div>
<div class="cap2" id="q-hint">Escreva a lista e clique em <b>Carregar</b> para ver o CATMAT de cada item e testar as descrições antes de pesquisar os preços.</div>

<div id="q-loaded">
  <div class="cap2">Confira o CATMAT de cada item. <b>Usar</b>: desmarque para deixar um item de fora. Mexeu na descrição? O CATMAT é casado de novo sozinho, sem pesquisar preço.</div>
  <table id="q-tab"><thead><tr><th>Usar</th><th>Descrição do item (edite)</th><th>CATMAT</th><th>% casam.</th><th>Descrição do item no CATMAT</th><th>Qtd.</th><th>Un.</th><th>Estimativa (R$)</th><th>Situação</th></tr></thead><tbody></tbody></table>
  <div class="cap2" id="q-count"></div>
  <div id="q-opts">
    <div class="lbl">Tipo de item</div>
    <div class="fld sel" id="q-tipo" style="max-width:300px"><span id="q-tipo-v">Automático</span>
      <div class="dd" id="q-dd"><div id="o-auto">Automático</div><div id="o-mat">Material</div><div id="o-serv">Serviço</div></div></div>
    <div class="ck" id="cb-prio" style="margin-top:10px"><span class="box on" id="cb-prio-b" style="background:#ef4444;border-color:#ef4444">✓</span><span>Deixar a estimativa de preço orientar a escolha do CATMAT</span></div>
    <div class="btn pri" id="b-cotar" style="margin-top:12px;font-size:13.5px;padding:10px">⚡ Cotar itens</div>
  </div>
  <div class="prog" id="prog"><div class="t" id="prog-t"></div><div class="b"><i id="prog-b"></i></div></div>
</div>

<div id="q-res">
  <div class="panel" style="margin-top:16px"><h3>Mapa comparativo de preços</h3><p>Preços unitários praticados (últimos 12 meses), sem outliers, a até 30% da média de cada item.</p></div>
  <div class="mets" id="q-mets"></div>
  <div id="q-conf"></div>
  <div class="tot" id="q-tot"></div>
  <table id="q-map"><thead><tr><th>#</th><th>Descrição do item</th><th>CATMAT</th><th>Preço 1</th><th>Preço 2</th><th>Preço 3</th><th>Preço 4</th><th>Preço 5</th><th>Média unit.</th><th>Valor total</th><th>Situação</th></tr></thead><tbody></tbody></table>
  <div class="frow"><div class="btn" id="q-pdf" style="flex:1">📄 Baixar relatório em PDF</div><div class="btn" id="q-xls" style="flex:1">📊 Baixar planilha em Excel</div></div>
  <h4 style="margin:16px 0 4px;font-size:14px">Detalhes por item</h4>
  <div id="q-det"></div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const TXT='Resma de papel A4 75 g/m² - 50\n10 notebook 15 polegadas 16 GB\nDetergente líquido neutro 5 litros; 30 un';
const FORN=[['12/09/2026','FORNECEDOR EXEMPLO 1 LTDA','00.000.000/0001-01','ÓRGÃO EXEMPLO A','RJ'],['03/08/2026','FORNECEDOR EXEMPLO 2 LTDA','00.000.000/0001-02','ÓRGÃO EXEMPLO B','SP'],['21/07/2026','FORNECEDOR EXEMPLO 3 LTDA','00.000.000/0001-03','ÓRGÃO EXEMPLO C','DF'],['15/06/2026','FORNECEDOR EXEMPLO 4 LTDA','00.000.000/0001-04','ÓRGÃO EXEMPLO D','MG'],['09/05/2026','FORNECEDOR EXEMPLO 5 LTDA','00.000.000/0001-05','ÓRGÃO EXEMPLO E','RJ']];
let S;
function resetS(){S={txt:'',spinL:false,loaded:false,fix:false,est3:null,tipo:'Automático',dd:false,prog:0,done:false,swapped:false,exp1:false};}
const brl=v=>'R$ '+v.toFixed(2).replace('.',',').replace(/\B(?=(\d{3})+(?!\d))/g,'.');
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
function rows(){return [
 {d:'Resma de papel A4 75 g/m²',q:50,u:'UN',cat:'123456',pct:94,dc:'Papel A4, 75 g/m², branco, resma com 500 folhas',est:null,sit:'✅ bom casamento'},
 S.fix?{d:'notebook 15 polegadas 16 GB RAM SSD 512 GB',q:10,u:'UN',cat:'234890',pct:88,dc:'Computador portátil (notebook), tela 15,6 pol., 16 GB RAM, SSD 512 GB',est:null,sit:'✅ bom casamento'}
      :{d:'notebook 15 polegadas 16 GB',q:10,u:'UN',cat:'234567',pct:62,dc:'Computador portátil (notebook), tela 14 pol.',est:null,sit:'⚠️ abaixo de 70%: melhore a descrição ou digite o CATMAT'},
 {d:'Detergente líquido neutro 5 litros',q:30,u:'UN',cat:S.swapped?'345700':'345678',pct:S.swapped?78:91,dc:S.swapped?'Detergente líquido neutro, galão 5 L (outro PDM)':'Detergente líquido neutro, galão de 5 litros',est:S.est3,sit:S.swapped?'👆 escolhido por você':'✅ bom casamento'}];}
function results(){const R=rows();return [
 {r:R[0],p:[24.90,26.50,25.40,27.10,22.90],un:'RESMA',univ:14,out:1},
 {r:R[1],p:[3980,4250,4100,3870,4390],un:'UNIDADE',univ:23,out:2},
 S.swapped?{r:R[2],p:[11.40,12.10,11.90,12.60],un:'GALÃO',univ:9,out:0}:{r:R[2],p:[18.90,21.40],un:'GALÃO',univ:7,out:1}];}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('q-ta-v',S.txt);$('#q-ta-ph').style.display=S.txt?'none':'inline';
  $('#spinL').classList.toggle('on',S.spinL);$('#q-hint').style.display=S.loaded?'none':'block';$('#q-loaded').classList.toggle('on',S.loaded);
  T('q-tipo-v',S.tipo);$('#q-dd').classList.toggle('on',S.dd);
  const R=rows();
  $('#q-tab tbody').innerHTML=R.map((x,i)=>'<tr id="r'+(i+1)+'"><td><span class="box on" style="background:#ef4444;border-color:#ef4444;width:14px;height:14px;font-size:10px">✓</span></td><td class="ed" id="d'+(i+1)+'">'+x.d+'</td><td class="c">'+x.cat+'</td><td class="'+(x.pct<70?'low':'good')+'">'+x.pct+'%</td><td>'+x.dc+'</td><td>'+x.q+'</td><td>'+x.u+'</td><td class="ed" id="e'+(i+1)+'">'+(x.est?brl(x.est):'')+'</td><td class="'+(x.pct<70?'low':'good')+'">'+x.sit+'</td></tr>').join('');
  T('q-count',R.length+' item(ns) no pedido.');
  const pc=Math.min(S.prog,3);$('#prog').classList.toggle('on',S.prog>0);
  T('prog-t',S.done?'Concluído em 9 s':'Cotando '+pc+'/3: '+['','Resma de papel A4 75 g/m²','notebook 15 polegadas 16 GB RAM SSD 512 GB','Detergente líquido neutro 5 litros'][pc]);
  $('#prog-b').style.width=(S.done?100:Math.max(0,(pc-1)/3*100))+'%';
  $('#q-res').classList.toggle('on',S.done);if(!S.done)return;
  const X=results();const ok=X.filter(x=>x.p.length>=3).length,ins=X.filter(x=>x.p.length>0&&x.p.length<3).length,sem=X.filter(x=>x.p.length===0).length;
  $('#q-mets').innerHTML='<div class="met"><div class="k">Itens pesquisados</div><div class="v">'+X.length+'</div></div><div><span class="chip cg">'+ok+' com 3+ preços</span></div><div><span class="chip cr">'+ins+' com menos de 3</span></div><div><span class="chip cl">'+sem+' sem preço</span></div>';
  const tot=X.reduce((a,x)=>a+mean(x.p)*x.r.q,0);
  $('#q-tot').innerHTML='<div class="k">Valor total estimado do orçamento</div><div class="v">'+brl(tot)+'</div>';
  let conf='';const x3=X[2];
  if(x3.r.est&&!S.swapped)conf='<div class="alert i"><b>Conferência com a sua estimativa de preço</b> — 1 item(ns) com estimativa: 0 coerente(s), 1 divergente(s), 1 com sugestão de outro CATMAT mais próximo da estimativa.</div><div class="alert w"><b>Detergente líquido neutro 5 litros</b> — a média praticada ('+brl(mean(x3.p))+') está longe da sua estimativa ('+brl(x3.r.est)+'). Há outro CATMAT parecido (78%) com 4 de 6 compras perto da estimativa (mediana R$ 11,95).<br><div class="btn" id="b-usar">Usar o CATMAT 345700 (78%)</div></div>';
  else if(x3.r.est&&S.swapped)conf='<div class="alert i"><b>Detergente líquido neutro 5 litros</b> — cotado de novo com o CATMAT 345700: preços coerentes com a sua estimativa ('+brl(x3.r.est)+').</div>';
  $('#q-conf').innerHTML=conf;
  $('#q-map tbody').innerHTML=X.map((x,i)=>'<tr id="m'+(i+1)+'"><td>'+(i+1)+'</td><td>'+x.r.d+'</td><td>'+x.r.cat+'</td>'+[0,1,2,3,4].map(k=>'<td class="n">'+(x.p[k]!=null?brl(x.p[k]):'')+'</td>').join('')+'<td class="n"><b>'+brl(mean(x.p))+'</b></td><td class="n">'+brl(mean(x.p)*x.r.q)+'</td><td style="color:'+(x.p.length>=3?'#86efac':'#fcd34d')+'">'+(x.p.length>=3?'Preços suficientes':'Menos de 3 preços')+'</td></tr>').join('');
  $('#q-det').innerHTML=X.map((x,i)=>{const m=mean(x.p),sd=x.p.length>1?Math.sqrt(x.p.reduce((a,b)=>a+(b-m)**2,0)/(x.p.length-1)):0;
    const open=(i===0&&S.exp1);
    const body=i===0?'<div class="cp">Unidade: '+x.un+' · universo analisado: '+x.univ+' registros · outliers removidos: '+x.out+' · mínimo '+brl(Math.min(...x.p))+' · máximo '+brl(Math.max(...x.p))+' · CV '+(sd/m*100).toFixed(1).replace('.',',')+'%</div><table id="q-dt"><thead><tr><th>Data</th><th>Valor unitário</th><th>Fornecedor</th><th>CNPJ</th><th>Órgão</th><th>UF</th></tr></thead><tbody>'+x.p.map((v,k)=>'<tr><td>'+FORN[k][0]+'</td><td>'+brl(v)+'</td><td>'+FORN[k][1]+'</td><td>'+FORN[k][2]+'</td><td>'+FORN[k][3]+'</td><td>'+FORN[k][4]+'</td></tr>').join('')+'</tbody></table>':'';
    return '<div class="exph" id="ex'+(i+1)+'"><b>'+(i+1)+'. '+x.r.d+'</b> — '+(x.p.length>=3?'Preços suficientes':'Menos de 3 preços')+' · média '+brl(m)+'<span>'+(open?'▴':'▾')+'</span></div><div class="expb'+(open?' on':'')+'" id="exb'+(i+1)+'">'+body+'</div>';}).join('');
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Cotação Rápida',
 b:'A <b>Cotação Rápida</b> pesquisa preços de <b>vários itens de uma vez</b>, sejam materiais ou serviços. Para cada item o sistema <b>acha o código CATMAT/CATSERV</b>, busca os <b>preços praticados</b> em compras públicas e monta um <b>mapa comparativo</b> em PDF e Excel.',
 tip:'💡 Para pesquisar <b>um único item</b> com filtros detalhados, use a página <b>Cotação</b>. Aqui o foco é rapidez e volume (até 50 itens por cotação).',
 run:async a=>{a.unring();await a.top();a.ring('#q-head','Página Cotação Rápida');await a.sleep(2800);a.unring();}},

{short:'Lista',t:'Passo 1 — Digite a lista de itens',
 b:'No campo <b>Descrições dos itens</b>, escreva <b>um item por linha</b>. A <b>quantidade é opcional</b>: pode vir depois de um hífen (“- 50”), antes do nome (“10 notebook…”) ou depois de ponto e vírgula (“; 30 un”). Se preferir, <b>importe uma planilha</b> CSV ou Excel no campo logo abaixo.',
 tip:'💡 Descreva com as características que importam (ex.: <i>resma de papel A4 75 g/m²</i>, <i>notebook 15 polegadas 16 GB</i>). Quanto melhor a descrição, melhor o CATMAT encontrado.',
 run:async a=>{a.unring();await a.top();a.ring('#q-ta','Um item por linha');await a.click('#q-ta');await a.type('#q-ta-v',TXT,45);a.set(S=>S.txt=TXT);await a.sleep(900);a.unring();a.ring('#q-up','Ou importe uma planilha');await a.sleep(2200);a.unring();}},

{short:'Carregar',t:'Passo 2 — Clique em Carregar',
 b:'Clique em <b>📥 Carregar</b>. Este botão <b>ainda não pesquisa preços</b>: ele só monta a <b>tabela de conferência</b>, mostrando para cada item o <b>CATMAT mais próximo</b>, a <b>% de casamento</b> com a sua descrição e a quantidade e unidade que o sistema entendeu.',
 tip:'💡 Isso é rápido e gratuito: dá para testar e ajustar as descrições quantas vezes quiser antes de cotar.',
 run:async a=>{a.unring();await a.click('#b-carregar',()=>a.set(S=>S.spinL=true));await a.sleep(1500);a.set(S=>{S.spinL=false;S.loaded=true;});
  await a.scroll('#q-tab',70);a.ring('#q-tab','Tabela de conferência');await a.sleep(2600);a.unring();}},

{short:'Conferir CATMAT',t:'Passo 3 — Confira e corrija o CATMAT',
 b:'Olhe as colunas <b>CATMAT</b>, <b>% casamento</b>, <b>Descrição do item no CATMAT</b> e <b>Situação</b>. Casamento <b>abaixo de 70%</b> é sinal de alerta: o item 2 casou apenas <b>62%</b> com um notebook de tela de 14". <b>Edite a descrição</b> acrescentando detalhes — o CATMAT é <b>casado de novo sozinho</b>, e o casamento sobe para <b>88%</b>.',
 tip:'💡 Se já souber o código, <b>digite o CATMAT</b> direto na coluna CATMAT. Para deixar um item de fora, desmarque <b>Usar</b>.',
 run:async a=>{a.unring();await a.scroll('#q-tab',70);a.ring('#r2','Casamento baixo: 62%');await a.sleep(2300);a.unring();
  await a.click('#d2');await a.type('#d2',' RAM SSD 512 GB',80,true);a.set(S=>S.fix=true);a.ring('#r2','Casou de novo: 88%');await a.sleep(2600);a.unring();}},

{short:'Estimativa',t:'Passo 4 — Informe uma estimativa de preço (opcional)',
 b:'Na coluna <b>Estimativa (R$)</b> você pode dizer quanto acha que vale <b>1 unidade</b> do item. Depois da cotação, o sistema <b>confere</b> se os preços praticados e o CATMAT são <b>compatíveis</b> com a sua expectativa e avisa se outro CATMAT parecido pratica preço mais próximo. Aqui informamos <b>R$ 12,00</b> para o detergente.',
 tip:'💡 Deixe em branco se não tiver ideia do preço: o item é cotado normalmente.',
 run:async a=>{a.unring();await a.scroll('#q-tab',70);await a.click('#e3');await a.type('#e3','12,00',120);a.set(S=>S.est3=12);a.ring('#e3','Estimativa: R$ 12,00');await a.sleep(2400);a.unring();}},

{short:'Opções',t:'Passo 5 — Escolha as opções da cotação',
 b:'<b>Tipo de item</b>: <b>Automático</b> decide, linha a linha, se é material (CATMAT) ou serviço (CATSERV), mas é um pouco mais lento. Quando a lista for toda de um tipo, <b>escolha Material ou Serviço</b>. A caixa <b>“Deixar a estimativa de preço orientar a escolha do CATMAT”</b> usa a sua estimativa para desempatar entre CATMAT bem parecidos.',
 tip:'💡 Desmarque a caixa se quiser que o CATMAT seja escolhido <b>só pela semelhança do texto</b>.',
 run:async a=>{a.unring();await a.scroll('#q-opts',120);a.ring('#q-opts','Opções');await a.sleep(1200);
  await a.click('#q-tipo',()=>a.set(S=>S.dd=true));await a.click('#o-mat',()=>a.set(S=>{S.tipo='Material';S.dd=false;}));
  a.unring();a.ring('#cb-prio','Estimativa orienta o CATMAT');await a.sleep(2400);a.unring();}},

{short:'Cotar',t:'Passo 6 — Clique em Cotar itens',
 b:'Clique em <b>⚡ Cotar itens</b>. Para cada item o sistema localiza <b>até 3 CATMAT/CATSERV com bom casamento</b> que tenham preços e busca as compras dos <b>últimos 12 meses</b>, comparando só a <b>mesma unidade de fornecimento</b>. Depois <b>remove outliers</b> e traz <b>até 5 preços</b>, todos a <b>até 30% da média</b>, priorizando fornecedores diferentes.',
 tip:'💡 Uma barra de progresso mostra qual item está sendo cotado. Um item com problema não derruba a cotação inteira.',
 run:async a=>{a.unring();await a.scroll('#b-cotar',220);await a.click('#b-cotar',()=>a.set(S=>S.prog=1));await a.sleep(500);
  for(const n of [1,2,3]){a.set(S=>S.prog=n);await a.sleep(1500);}a.set(S=>S.done=true);await a.sleep(500);}},

{short:'Mapa',t:'Passo 7 — Leia o mapa comparativo',
 b:'O <b>Mapa comparativo de preços</b> resume tudo: quantos itens foram pesquisados e quantos tiveram <b>3 ou mais preços</b> (verde), <b>menos de 3</b> (amarelo) ou <b>nenhum</b> (vermelho). Como informamos quantidades, o mapa traz o <b>valor total de cada item</b> (média × quantidade) e o <b>valor total estimado do orçamento</b>.',
 tip:'💡 A <b>média unitária</b> é calculada só com os preços listados no mapa, já sem outliers.',
 run:async a=>{a.unring();await a.scroll('#q-res',10);a.ring('#q-mets','Resumo da cotação');await a.sleep(2300);a.unring();a.ring('#q-tot','Total do orçamento');await a.sleep(2300);a.unring();
  await a.scroll('#q-map',60);a.ring('#q-map','Mapa comparativo');await a.sleep(3200);a.unring();}},

{short:'Alertas',t:'Passo 8 — Atenção às sinalizações',
 b:'Itens com <b>menos de 3 preços</b> aparecem em amarelo: o detergente teve só <b>2 preços</b>. Nesses casos é preciso <b>complementar com outras fontes</b> (IN SEGES/ME nº 65/2021 recomenda ao menos três preços). Além disso, a <b>Conferência com a sua estimativa</b> avisa que a média praticada está <b>longe de R$ 12,00</b> e sugere <b>outro CATMAT</b> parecido com preços compatíveis.',
 tip:'💡 Nem todo aviso é erro: confira se a unidade (galão de 5 L × frasco) e a descrição do CATMAT realmente servem para o que você precisa.',
 run:async a=>{a.unring();await a.scroll('#q-mets',20);a.ring('#q-conf','Conferência com a estimativa');await a.sleep(2800);a.unring();await a.scroll('#m3',140);a.ring('#m3','Menos de 3 preços');await a.sleep(2600);a.unring();}},

{short:'Trocar CATMAT',t:'Passo 9 — Use o CATMAT sugerido',
 b:'Clique em <b>“Usar o CATMAT 345700 (78%)”</b>. O sistema <b>cota de novo só aquele item</b> com o código escolhido. Agora o detergente tem <b>4 preços coerentes</b> com a estimativa, a situação passa para <b>Preços suficientes</b> e o <b>total do orçamento</b> é recalculado.',
 tip:'💡 A troca vale para esta cotação. Se preferir, volte à lista, digite o CATMAT desejado na tabela e cote novamente.',
 run:async a=>{a.unring();await a.scroll('#q-conf',70);await a.click('#b-usar',()=>a.set(S=>S.swapped=true));await a.sleep(800);
  a.ring('#q-conf','CATMAT trocado');await a.sleep(1800);a.unring();a.ring('#q-tot','Novo total do orçamento');await a.sleep(2200);a.unring();}},

{short:'Baixar',t:'Passo 10 — Baixe o PDF e a planilha',
 b:'Use <b>📄 Baixar relatório em PDF</b> para o documento com o <b>mapa comparativo na primeira página</b> e <b>📊 Baixar planilha em Excel</b> para trabalhar os números (as fórmulas de média e total ficam na planilha).',
 tip:'💡 Anexe o PDF ao processo como memória da pesquisa de preços.',
 run:async a=>{a.unring();await a.scroll('#q-pdf',200);a.ring('#q-pdf','PDF');await a.click('#q-pdf',()=>a.toast('✔ cotacao_rapida_20261021_101500.pdf'));
  a.unring();a.ring('#q-xls','Excel');await a.click('#q-xls',()=>a.toast('✔ cotacao_rapida_20261021_101502.xlsx'));await a.sleep(900);a.unring();}},

{short:'Detalhes',t:'Passo 11 — Veja os detalhes de cada item',
 b:'Em <b>Detalhes por item</b>, clique no item para abrir: você vê o <b>universo analisado</b>, os <b>outliers removidos</b>, o <b>CV</b> e a lista dos preços com <b>data, fornecedor, CNPJ, órgão e UF</b>. <b>Resumo:</b> 1) digite a lista; 2) Carregar; 3) confira/corrija o CATMAT; 4) estimativa (opcional); 5) Cotar; 6) leia o mapa e os alertas; 7) baixe PDF/Excel.',
 tip:'🎉 Fim da aula! Quer treinar? Use os mesmos passos com a sua própria lista.',
 run:async a=>{a.unring();await a.scroll('#q-det',150);await a.click('#ex1',()=>a.set(S=>S.exp1=true));await a.sleep(300);a.ring('#exb1','Preços e fornecedores');await a.sleep(3200);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS)
