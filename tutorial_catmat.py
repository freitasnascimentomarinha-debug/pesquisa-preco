"""Vídeo-aula simulado: como usar a página CATMAT/CATSERV Automático (códigos sugeridos a partir de descrições)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar o CATMAT/CATSERV Automático"
DESCRICAO = (
    "Achar o código CATMAT/CATSERV de uma lista de descrições: digitar ou importar, classificar, escolher quantas "
    "sugestões, conferir a similaridade e baixar. Duração aproximada: 3 min, com narração."
)

_MOCK_CSS = r"""
#c-res{display:none}#c-res.on{display:block}
#c-spin{margin-top:10px}
.sug{background:#0b2447;border:1px solid var(--line);border-radius:7px;margin-top:6px;font-size:11.5px}
.sug .h{padding:8px 11px;display:flex;gap:8px}.sug .h span{margin-left:auto;color:#9fb6d8}
.sug .b{display:none;padding:8px 11px;border-top:1px solid var(--line)}.sug .b.on{display:block}
.pbar{display:inline-block;width:60px;height:8px;background:#0b2a63;border-radius:5px;overflow:hidden;vertical-align:middle;margin-right:5px}.pbar i{display:block;height:100%;background:#22c55e}.pbar i.m{background:#f59e0b}
#c-final td,#c-final th,.sug td,.sug th{font-size:10px;padding:5px 5px}
.rw.pick td{background:rgba(250,204,21,.16)}
.opt{margin-top:6px}
.sl{position:relative;height:6px;background:#2b6cb0;border-radius:4px;margin:16px 6px 6px}.sl i{position:absolute;top:-6px;width:16px;height:16px;border-radius:50%;background:#ef4444;border:2px solid #fff}
"""

_STAGE_HTML = r"""
<div class="qh" id="c-head"><div class="qs">🔎</div><div><b>CATMAT/CATSERV Automático</b><small>Encontre sugestões de classificação para materiais e serviços a partir das descrições do seu processo.</small></div><span class="qb">CATÁLOGO<br>COMPRAS.GOV</span></div>
<div class="panel" id="c-lista"><h3>Lista de itens</h3><p>Digite ou cole uma descrição por linha. Você também pode importar uma planilha CSV ou Excel.</p></div>
<div class="lbl">Descrições dos itens</div>
<div class="ta" id="c-ta" style="min-height:70px"><span id="c-ta-v"></span><span class="ph" id="c-ta-ph">Ex: Papel sulfite A4 75 g/m², resma com 500 folhas
Manutenção preventiva de aparelhos de ar-condicionado
Cadeira ergonômica para escritório</span></div>
<div class="two" style="margin-top:10px">
  <div><div class="lbl">Classificar como</div><div class="fld sel" id="c-tipo"><span id="c-tipo-v">Automático</span><div class="dd" id="c-dd"><div id="c-o-auto">Automático</div><div id="c-o-mat">Material</div><div id="c-o-serv">Serviço</div></div></div></div>
  <div><div class="lbl">Importar lista (CSV ou Excel)</div><div class="upl" id="c-up" style="padding:7px 10px">Arraste aqui <span>Procurar</span></div></div>
</div>
<div class="lbl" style="margin-top:12px">Quantas sugestões listar por item (da maior para a menor correspondência)</div>
<div class="sl" id="c-slider"><i id="c-knob" style="left:18%"></i></div>
<div class="cap2" id="c-qtd" style="text-align:left">10 sugestões por item</div>
<div class="btn pri" id="c-go" style="margin-top:8px;padding:10px;font-size:13.5px">🔎 Encontrar códigos sugeridos</div>
<div class="spin" id="c-spin"><i></i><span id="c-spin-t">Analisando 3 item(ns) nos catálogos oficiais...</span></div>

<div id="c-res">
  <div class="panel" style="margin-top:16px"><h3>Sugestões por item</h3><p>Cada item lista os códigos mais parecidos, da maior para a menor correspondência. A primeira opção já vem escolhida; abra o item e troque se outra servir melhor.</p></div>
  <div id="c-sug"></div>
  <div class="panel" style="margin-top:16px"><h3>Resultado da correlação</h3><p>Use a similaridade como apoio à decisão e confira as especificações do item no catálogo antes de utilizar o código.</p></div>
  <div class="mets" id="c-mets"></div>
  <table id="c-final" style="margin-top:10px"><thead><tr><th>Descrição informada</th><th>Tipo</th><th>Código</th><th>Descrição sugerida</th><th>Simil.</th><th>Unid.</th></tr></thead><tbody></tbody></table>
  <div class="two" style="margin-top:10px"><div class="btn" id="c-xls">⬇️ Baixar correlação em Excel</div><div class="btn" id="c-pdf">⬇️ Baixar correlação em PDF</div></div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const TXT='Papel sulfite A4 75 g/m², resma com 500 folhas\nManutenção preventiva de aparelhos de ar-condicionado\nCadeira ergonômica para escritório';
const IT=[
 {d:'Papel sulfite A4 75 g/m², resma com 500 folhas',un:'RESMA',op:[{t:'CATMAT',c:'123456',s:96,dc:'Papel A4, 75 g/m², branco, resma com 500 folhas',pdm:'PAPEL SULFITE'},{t:'CATMAT',c:'234567',s:81,dc:'Papel A4 reciclado, 75 g/m², resma',pdm:'PAPEL SULFITE'},{t:'CATMAT',c:'345678',s:74,dc:'Papel A4 colorido, 75 g/m², pacote',pdm:'PAPEL SULFITE'}]},
 {d:'Manutenção preventiva de aparelhos de ar-condicionado',un:'',op:[{t:'CATSERV',c:'12345',s:78,dc:'Manutenção preventiva de aparelhos de ar-condicionado',pdm:''},{t:'CATSERV',c:'12346',s:66,dc:'Manutenção corretiva de aparelhos de ar-condicionado',pdm:''}]},
 {d:'Cadeira ergonômica para escritório',un:'UNIDADE',op:[{t:'CATMAT',c:'234100',s:58,dc:'Cadeira giratória, tipo secretária, assento estofado',pdm:'CADEIRA GIRATÓRIA'},{t:'CATMAT',c:'234890',s:57,dc:'Cadeira ergonômica, tipo operacional, com ajuste de altura e apoio lombar',pdm:'CADEIRA GIRATÓRIA'},{t:'CATMAT',c:'234777',s:49,dc:'Cadeira fixa, tipo interlocutor, empilhável',pdm:'CADEIRA FIXA'}]}
];
let S;
function resetS(){S={txt:'',tipo:'Automático',dd:false,qtd:10,spin:false,res:false,exp:false,pick:0,sel3:false};}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('c-ta-v',S.txt);$('#c-ta-ph').style.display=S.txt?'none':'inline';T('c-tipo-v',S.tipo);$('#c-dd').classList.toggle('on',S.dd);
  T('c-qtd',S.qtd+' sugestões por item');$('#c-knob').style.left=((S.qtd-3)/27*92)+'%';
  $('#c-spin').classList.toggle('on',S.spin);$('#c-res').classList.toggle('on',S.res);
  if(!S.res)return;
  const chosen=IT.map((x,i)=>x.op[i===2?S.pick:0]);
  $('#c-sug').innerHTML=IT.map((x,i)=>{const open=i===2&&S.exp;
    const rows=x.op.map((o,p)=>'<tr class="rw'+((i===2&&p===S.pick)?' pick':'')+'"><td>'+(p+1)+'</td><td>'+o.t+'</td><td>'+o.c+'</td><td><span class="pbar"><i class="'+(o.s>=70?'':'m')+'" style="width:'+o.s+'%"></i></span>'+o.s+'%</td><td>'+o.dc+'</td></tr>').join('');
    return '<div class="sug" id="sg'+(i+1)+'"><div class="h"><b>'+(i+1)+'. '+x.d+'</b><span>'+x.op.length+' sugestão(ões) | melhor: '+x.op[0].t+' '+x.op[0].c+' ('+x.op[0].s+'%) '+(open?'▴':'▾')+'</span></div>'+
     '<div class="b'+(open?' on':'')+'" id="sgb'+(i+1)+'"><table><thead><tr><th>Pos.</th><th>Tipo</th><th>Código</th><th>Correspondência</th><th>Descrição</th></tr></thead><tbody>'+rows+'</tbody></table>'+
     '<div class="lbl opt">Usar esta opção</div><div class="fld sel" id="usar'+(i+1)+'" style="font-size:11px">'+chosen[i].t+' '+chosen[i].c+' — '+chosen[i].s+'% — '+chosen[i].dc.slice(0,60)+'<div class="dd" id="usar-dd'+(i+1)+'" style="font-size:11px">'+x.op.map((o,p)=>'<div id="usar'+(i+1)+'-'+p+'">'+o.t+' '+o.c+' — '+o.s+'% — '+o.dc.slice(0,50)+'</div>').join('')+'</div></div></div></div>';}).join('');
  if(S.sel3)$('#usar-dd3').classList.add('on');
  const alta=chosen.filter(o=>o.s>=70).length,med=chosen.filter(o=>o.s>=45&&o.s<70).length,baixa=chosen.length-alta-med;
  $('#c-mets').innerHTML='<div class="met"><div class="k">Itens analisados</div><div class="v">'+chosen.length+'</div></div><div><span class="chip cg">'+alta+' alta similaridade</span></div><div><span class="chip cr">'+med+' para revisar</span></div><div><span class="chip cl">'+baixa+' baixa similaridade</span></div>';
  $('#c-final tbody').innerHTML=chosen.map((o,i)=>'<tr id="cf'+(i+1)+'"><td>'+IT[i].d+'</td><td>'+o.t+'</td><td><b>'+o.c+'</b></td><td>'+o.dc+'</td><td>'+o.s+',0%</td><td>'+(IT[i].un||'—')+'</td></tr>').join('');
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça o CATMAT/CATSERV Automático',
 b:'Esta página encontra o <b>código do catálogo</b> — <b>CATMAT</b> (materiais) ou <b>CATSERV</b> (serviços) — a partir da <b>descrição que você escreve</b>. Em vez de procurar item por item no catálogo, você cola uma <b>lista inteira</b> e recebe <b>sugestões ordenadas por semelhança</b>.',
 tip:'💡 O código é necessário em pesquisas de preços, termos de referência e no cadastro dos itens do processo.',
 run:async a=>{a.unring();await a.top();a.ring('#c-head','Códigos sugeridos automaticamente');await a.sleep(2800);a.unring();}},

{short:'Lista',t:'Passo 1 — Digite a lista de itens',
 b:'No campo <b>Descrições dos itens</b>, escreva <b>uma descrição por linha</b>, como aparece no seu processo. Pode misturar <b>materiais e serviços</b>. Prefira descrições completas: características como tamanho, material e embalagem melhoram a sugestão.',
 tip:'💡 Se a lista já está numa planilha, use <b>Importar lista (CSV ou Excel)</b> e escolha a <b>coluna com as descrições</b>.',
 run:async a=>{a.unring();await a.top();a.ring('#c-ta','Uma descrição por linha',4);await a.click('#c-ta');await a.type('#c-ta-v',TXT,45);a.set(S=>S.txt=TXT);await a.sleep(900);a.unring();a.ring('#c-up','Ou importe uma planilha',4);await a.sleep(2200);a.unring();}},

{short:'Classificar',t:'Passo 2 — Escolha como classificar',
 b:'Em <b>Classificar como</b>, <b>Automático</b> decide, linha a linha, se o item é <b>material</b> ou <b>serviço</b>. Se a sua lista tem <b>só um tipo</b>, escolha <b>Material</b> ou <b>Serviço</b>: a busca fica mais direta e rápida.',
 tip:'💡 No modo Automático, uma descrição ambígua pode ser classificada no tipo errado: confira a coluna Tipo no resultado.',
 run:async a=>{a.unring();await a.scroll('#c-tipo',130);await a.click('#c-tipo',()=>a.set(S=>S.dd=true));await a.click('#c-o-auto',()=>a.set(S=>{S.tipo='Automático';S.dd=false;}));a.ring('#c-tipo','Automático',4);await a.sleep(2200);a.unring();}},

{short:'Sugestões',t:'Passo 3 — Defina quantas sugestões listar',
 b:'O controle <b>Quantas sugestões listar por item</b> vai de <b>3 a 30</b> (padrão 10). Cada item recebe essa quantidade de códigos, <b>da maior para a menor correspondência</b>. Aumente quando a descrição for genérica; diminua para uma lista mais enxuta.',
 tip:'💡 Para itens muito específicos, 3 a 5 sugestões costumam bastar.',
 run:async a=>{a.unring();await a.scroll('#c-slider',140);a.ring('#c-slider','De 3 a 30 sugestões',6);await a.sleep(2400);a.unring();}},

{short:'Encontrar',t:'Passo 4 — Clique em Encontrar códigos',
 b:'Clique em <b>🔎 Encontrar códigos sugeridos</b>. O sistema compara cada descrição com os <b>catálogos oficiais</b> de materiais e serviços e mostra o andamento. Se a lista estiver vazia, ele avisa para informar ao menos uma descrição.',
 tip:'💡 Listas grandes levam mais tempo, pois cada item é comparado com todo o catálogo.',
 run:async a=>{a.unring();await a.scroll('#c-go',220);await a.click('#c-go',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.res=true;});await a.sleep(400);}},

{short:'Sugestões por item',t:'Passo 5 — Confira as sugestões por item',
 b:'Em <b>Sugestões por item</b>, cada linha mostra o item, o <b>número de sugestões</b> e a <b>melhor opção</b> com a % de correspondência. <b>Verde</b> (70% ou mais) indica alta semelhança; <b>amarelo</b>, semelhança média, para revisar. Abra o item para ver a tabela completa: <b>tipo, código, correspondência, descrição e PDM</b>.',
 tip:'💡 A <b>unidade de fornecimento</b> (resma, unidade, caixa) vem do PDM do material e entra no resultado.',
 run:async a=>{a.unring();await a.scroll('#sg1',90);a.ring('#sg1','Melhor opção do item 1',4);await a.sleep(1800);a.unring();a.ring('#sg3','Item 3: correspondência baixa',4);await a.sleep(2400);a.unring();}},

{short:'Trocar opção',t:'Passo 6 — Troque a opção, se for preciso',
 b:'O item 3 (<b>cadeira ergonômica</b>) teve apenas <b>58%</b> de correspondência na primeira opção. Abra o item, leia as descrições e use <b>Usar esta opção</b> para escolher a que realmente atende. Aqui escolhemos o <b>código 234890</b>, “cadeira ergonômica, tipo operacional, com ajuste de altura e apoio lombar”.',
 tip:'💡 A similaridade é <b>apoio à decisão</b>: o código escolhido deve descrever o que você realmente precisa.',
 run:async a=>{a.unring();await a.scroll('#sg3',90);await a.click('#sg3',()=>a.set(S=>S.exp=true));await a.sleep(300);await a.scroll('#usar3',200);await a.click('#usar3',()=>a.set(S=>S.sel3=true));await a.click('#usar3-1',()=>a.set(S=>{S.pick=1;S.sel3=false;}));a.ring('#sgb3','Opção escolhida',4);await a.sleep(2400);a.unring();}},

{short:'Resultado',t:'Passo 7 — Leia o resultado da correlação',
 b:'Em <b>Resultado da correlação</b> você vê o <b>resumo</b>: itens analisados, quantos têm <b>alta similaridade</b>, quantos <b>para revisar</b> e quantos de <b>baixa</b>. A tabela final traz, por item, o <b>tipo</b>, o <b>código</b> escolhido, a <b>descrição sugerida</b>, a <b>similaridade</b> e a <b>unidade de fornecimento</b>.',
 tip:'💡 Abaixo de 45% o sistema não sugere código com segurança: melhore a descrição ou procure no catálogo oficial.',
 run:async a=>{a.unring();await a.scroll('#c-mets',60);a.ring('#c-mets','Resumo',4);await a.sleep(2000);a.unring();a.ring('#c-final','Tabela final',4);await a.sleep(3000);a.unring();}},

{short:'Baixar',t:'Passo 8 — Baixe a correlação',
 b:'Use <b>⬇️ Baixar correlação em Excel</b> (aba com a correlação e aba com <b>todas as opções</b>) ou <b>em PDF</b>. <b>Resumo:</b> 1) digite ou importe a lista; 2) classifique; 3) defina as sugestões; 4) Encontrar; 5) confira; 6) troque a opção se preciso; 7) leia o resultado; 8) baixe.',
 tip:'🎉 Fim da aula! Os códigos e descrições desta aula são fictícios. Confira sempre no catálogo oficial antes de usar no processo.',
 run:async a=>{a.unring();await a.scroll('#c-xls',250);a.ring('#c-xls','Excel',4);await a.click('#c-xls',()=>a.toast('✔ correlacao_catmat_catserv.xlsx'));a.unring();a.ring('#c-pdf','PDF',4);await a.click('#c-pdf',()=>a.toast('✔ correlacao_catmat_catserv.pdf'));await a.sleep(900);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="catmat")
