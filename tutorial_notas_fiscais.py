"""Vídeo-aula simulado: como usar a página Notas Fiscais (preços praticados em NF-e do Portal da Transparência)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a página Notas Fiscais"
DESCRICAO = (
    "Pesquisar preços em notas fiscais eletrônicas: itens, filtros, mapa comparativo, notas para autenticar, "
    "fornecedores e relatórios. Duração aproximada: 3 min."
)

_MOCK_CSS = r"""
#n-conf,#n-res{display:none}#n-conf.on,#n-res.on{display:block}
#n-tab td,#n-tab th{font-size:10.5px;padding:5px}
#n-map td,#n-map th{font-size:10px;padding:5px 4px;white-space:nowrap}#n-map td.n{text-align:right}
.ms{display:flex;flex-wrap:wrap;gap:4px;background:rgba(7,20,42,.8);border:1px solid #2b6cb0;border-radius:7px;padding:6px 8px}
.ms span{background:#ef4444;color:#fff;border-radius:5px;padding:2px 7px;font-size:10.5px;font-weight:700}.ms span.g{background:#334155;color:#cbd5e1}
.g3{display:grid;grid-template-columns:1fr 1fr;gap:10px}.g5{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:8px}
.nf-mono{font-family:Consolas,monospace;font-size:9.5px}
.expt{background:#0b2447;border:1px solid var(--line);border-radius:7px;margin-top:8px;font-size:11.5px}.expt .h{padding:8px 11px;display:flex;justify-content:space-between}.expt .b{display:none;padding:8px 11px;border-top:1px solid var(--line)}.expt .b.on{display:block}
#n-prog .b i{background:#ef4444}
.tot{margin:8px 0}.tot .k{font-size:11px;color:#b6cae2}.tot .v{font-size:24px;font-weight:700}
"""

_STAGE_HTML = r"""
<div class="hdr" id="n-head"><div class="l">⚓ MARINHA DO BRASIL ⚓</div><div class="s">AtaCotada</div><div class="u">NOTAS FISCAIS</div></div>
<h2 style="margin:12px 0 4px;font-size:21px">📄 Notas Fiscais</h2>
<div class="cap2" style="color:#dbe7f7">Pesquise <b>um ou vários itens</b> de uma vez em todos os arquivos mensais de notas fiscais eletrônicas dos dados abertos do <b>Portal da Transparência</b>.</div>
<div class="sec2" style="margin-top:6px">🔍 Pesquisa de Notas Fiscais</div>
<div class="cap2">Pesquise um ou vários itens de uma vez em todos os arquivos mensais de notas fiscais. O resultado é um mapa comparativo de preços (PDF e Excel) e um relatório dos fornecedores encontrados.</div>
<div class="lbl">Item(ns) a pesquisar (um por linha, com a quantidade ao lado, se quiser)</div>
<div class="ta" id="n-ta" style="min-height:50px"><span id="n-ta-v"></span><span class="ph" id="n-ta-ph">Ex:
Resma de papel A4 75 g - 50
Luva de procedimento látex; 200 cx</span></div>
<div id="n-conf"><div class="cap2">Confira o que o sistema entendeu. <b>Usar</b>: desmarque para deixar um item de fora.</div>
  <table id="n-tab"><thead><tr><th>Usar</th><th>Descrição</th><th>Qtd.</th><th>Un.</th></tr></thead><tbody>
  <tr><td><span class="box on" style="background:#ef4444;border-color:#ef4444;width:14px;height:14px;font-size:10px">✓</span></td><td>Resma de papel A4 75 g</td><td>50</td><td>UN</td></tr>
  <tr><td><span class="box on" style="background:#ef4444;border-color:#ef4444;width:14px;height:14px;font-size:10px">✓</span></td><td>Luva de procedimento látex</td><td>200</td><td>CX</td></tr></tbody></table>
  <div class="cap2">2 item(ns) no pedido.</div></div>

<div class="sec2">Filtros da pesquisa</div>
<div class="lbl">📂 Períodos (arquivos mensais)</div>
<div class="ms" id="n-per"><span>202603_NFe_NotaFiscalItem.csv ×</span><span>202602_NFe_NotaFiscalItem.csv ×</span><span>202601_NFe_NotaFiscalItem.csv ×</span><span class="g">… +9 arquivos</span></div>
<div class="g3" style="margin-top:8px">
  <div><div class="lbl">Nome do destinatário</div><div class="fld" id="n-dest"><span id="n-dest-v"></span><span class="ph" id="n-dest-ph">Ex: ARSENAL, HOSPITAL NAVAL...</span></div></div>
  <div><div class="lbl">Razão social do emitente (fornecedor)</div><div class="fld"><span class="ph">Ex: PAPELARIA...</span></div></div>
</div>
<div class="g5">
  <div><div class="lbl">UF do destinatário</div><div class="fld" id="n-uf"><span id="n-uf-v"></span><span class="ph" id="n-uf-ph">Ex: RJ</span></div></div>
  <div><div class="lbl">UF do emitente</div><div class="fld"><span class="ph">Ex: SP</span></div></div>
  <div><div class="lbl">Máximo de notas por item</div><div class="fld">1500</div></div>
</div>
<div class="btn pri" id="n-buscar" style="margin-top:12px;font-size:13.5px;padding:10px">🔎 Pesquisar notas fiscais</div>
<div class="prog" id="n-prog"><div class="t" id="n-prog-t"></div><div class="b"><i id="n-prog-b"></i></div></div>

<div id="n-res">
  <hr style="border-color:#1e5b9f;margin:14px 0">
  <div class="sec2" style="margin-top:0">Resultado</div>
  <div class="ck" id="n-out"><span class="box on" id="n-out-b" style="background:#ef4444;border-color:#ef4444">✓</span><span>🎯 Remover outliers e preços inexequíveis</span></div>
  <div class="cap2" id="n-cap"></div>
  <div class="mets" id="n-mets"></div>
  <div class="tot" id="n-tot"></div>
  <table id="n-map"><thead><tr><th>#</th><th>Descrição</th><th>Preço 1</th><th>Preço 2</th><th>Preço 3</th><th>Preço 4</th><th>Preço 5</th><th>Média unit.</th><th>Valor total</th><th>Situação</th></tr></thead><tbody></tbody></table>
  <div class="two" style="margin-top:10px"><div class="btn" id="n-pdf">📄 Baixar mapa comparativo (PDF)</div><div class="btn" id="n-xls">📊 Baixar mapa comparativo (Excel)</div></div>

  <div class="expt" id="n-notas"><div class="h"><b>🧾 Notas fiscais dos preços do mapa (10) — para autenticar no Portal da NF-e</b><span id="n-notas-s">▾</span></div>
    <div class="b" id="n-notas-b"><div class="cap2">Copie a chave de acesso (44 dígitos) no Portal da NF-e, resolva o captcha e confira emitente, data e valor.</div>
      <div class="btn" style="width:230px;padding:5px">🌐 Abrir o Portal da NF-e (Receita Federal)</div>
      <table style="margin-top:8px"><thead><tr><th>Item</th><th>Emitente</th><th>Valor unit.</th><th>Chave de acesso</th></tr></thead><tbody id="n-notas-t"></tbody></table></div></div>

  <hr style="border-color:#1e5b9f;margin:14px 0">
  <div class="sec2" style="margin-top:0">🏢 Fornecedores encontrados</div>
  <div class="ck"><span class="box on" style="background:#ef4444;border-color:#ef4444;border-radius:50%">●</span><span>Todos que venderam o item (escolhe os melhores)</span><span style="margin-left:14px;opacity:.7">○ Só os dos preços do mapa (mais rápido)</span></div>
  <div class="btn" id="n-forn" style="margin-top:8px">📞 Gerar relatório de fornecedores</div>
  <div class="spin" id="n-spinf"><i></i><span>Consultando o cadastro dos fornecedores (OpenCNPJ)…</span></div>
  <div id="n-fornr" class="hid"><div class="cap2">6 fornecedor(es) distintos, até 10 por item. Havendo mais candidatos, priorizados os que têm e-mail e telefone.</div>
    <div class="exph"><b>Vendem: Resma de papel A4 75 g — 3 fornecedor(es)</b></div>
    <table style="margin-top:4px"><thead><tr><th>Fornecedor</th><th>UF</th><th>E-mail</th><th>Telefone</th><th>Preço médio</th></tr></thead><tbody>
    <tr><td>PAPELARIA EXEMPLO 1 LTDA</td><td>SP</td><td>vendas@exemplo1.example</td><td>(11) 0000-0001</td><td>R$ 25,10</td></tr>
    <tr><td>DISTRIBUIDORA EXEMPLO 2 ME</td><td>RJ</td><td>contato@exemplo2.example</td><td>(21) 0000-0002</td><td>R$ 25,90</td></tr></tbody></table>
    <div class="two" style="margin-top:8px"><div class="btn" id="n-fpdf">📄 Baixar fornecedores (PDF)</div><div class="btn" id="n-fxls">📊 Baixar fornecedores (Excel)</div></div></div>

  <hr style="border-color:#1e5b9f;margin:14px 0">
  <div class="sec2" style="margin-top:0">Detalhes por item</div>
  <div class="cap2">Ajuste a faixa de preço de cada item para refinar o mapa e os relatórios acima.</div>
  <div class="exph" id="n-d1"><b>1. Resma de papel A4 75 g — Preços suficientes</b><span>▾</span></div>
  <div class="expb" id="n-d1b"><div class="lbl">Faixa de preço unitário (R$)</div><div class="slid" id="n-slid"><i id="n-slid-a" style="left:0"></i><i id="n-slid-b" style="right:0"></i></div>
    <div class="cap2" id="n-faixa"></div></div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const TXT='Resma de papel A4 75 g - 50\nLuva de procedimento látex; 200 cx';
const ITS=[{d:'Resma de papel A4 75 g',q:50,p:[24.90,26.50,25.40,27.10,23.80],i:'PAPELARIA EXEMPLO 1 LTDA',k:'35260800000000000100550010000000111000000115'},
           {d:'Luva de procedimento látex',q:200,p:[32.90,35.50,31.80,34.20,33.40],i:'DISTRIBUIDORA EXEMPLO 2 ME',k:'33260800000000000200550010000000211000000282'}];
let S;
function resetS(){S={txt:'',dest:'',uf:'',prog:-1,done:false,out:true,notas:false,spinf:false,forn:false,det:false,hi:0};}
function precos(i){let p=ITS[i].p;if(i===0&&S.hi)p=p.filter(v=>v<=S.hi);return p;}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('n-ta-v',S.txt);$('#n-ta-ph').style.display=S.txt?'none':'inline';$('#n-conf').classList.toggle('on',!!S.txt);
  T('n-dest-v',S.dest);$('#n-dest-ph').style.display=S.dest?'none':'inline';T('n-uf-v',S.uf);$('#n-uf-ph').style.display=S.uf?'none':'inline';
  const run=S.prog>=0;$('#n-prog').classList.toggle('on',run);
  T('n-prog-t',S.done?'Concluído em 38 s':(S.prog)+'/12 arquivos processados — último: 2026'+String(13-S.prog).padStart(2,'0')+'_NFe_NotaFiscalItem.csv');$('#n-prog-b').style.width=(S.done?100:S.prog/12*100)+'%';
  $('#n-res').classList.toggle('on',S.done);
  $('#n-spinf').classList.toggle('on',S.spinf);$('#n-fornr').classList.toggle('on',S.forn);
  $('#n-notas-b').classList.toggle('on',S.notas);T('n-notas-s',S.notas?'▴':'▾');
  $('#n-d1b').classList.toggle('on',S.det);
  if(!S.done)return;
  $('#n-out-b').className='box'+(S.out?' on':'');$('#n-out-b').style.cssText=S.out?'background:#ef4444;border-color:#ef4444':'';$('#n-out-b').textContent=S.out?'✓':'';
  T('n-cap','48.213 linhas de notas analisadas em 12 arquivo(s). Filtros: destinatario contem \'ARSENAL\'; UF destinatario = RJ; 12 de 12 arquivos mensais.');
  $('#n-mets').innerHTML='<div class="met"><div class="k">Itens pesquisados</div><div class="v">2</div></div><div><span class="chip cg">2 com 3+ preços</span></div><div><span class="chip cr">0 com menos de 3</span></div><div><span class="chip cl">0 sem preço</span></div>';
  const tot=ITS.reduce((a,x,i)=>a+mean(precos(i))*x.q,0);
  $('#n-tot').innerHTML='<div class="k">Valor total estimado do orçamento</div><div class="v">'+brl(tot)+'</div>';
  $('#n-map tbody').innerHTML=ITS.map((x,i)=>{const p=precos(i);return '<tr id="nm'+(i+1)+'"><td>'+(i+1)+'</td><td>'+x.d+'</td>'+[0,1,2,3,4].map(k=>'<td class="n">'+(p[k]!=null?brl(p[k]):'')+'</td>').join('')+'<td class="n"><b>'+brl(mean(p))+'</b></td><td class="n">'+brl(mean(p)*x.q)+'</td><td style="color:#86efac">Preços suficientes</td></tr>';}).join('');
  $('#n-notas-t').innerHTML=[0,1].map(i=>'<tr><td>'+ITS[i].d+'</td><td>'+ITS[i].i+'</td><td>'+brl(ITS[i].p[0])+'</td><td class="nf-mono" id="chave'+(i+1)+'">'+ITS[i].k+'</td></tr>').join('');
  T('n-faixa',S.hi?'Faixa: R$ 23,80 até '+brl(S.hi)+' — o mapa foi recalculado com '+precos(0).length+' preços.':'Faixa: R$ 23,80 até R$ 27,10 (todos os preços).');
  $('#n-slid-b').style.right=S.hi?'35%':'0';
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Notas Fiscais',
 b:'A página <b>Notas Fiscais</b> pesquisa <b>preços realmente praticados</b> em <b>notas fiscais eletrônicas (NF-e)</b> publicadas como dados abertos no <b>Portal da Transparência</b>. Você pesquisa <b>um ou vários itens de uma vez</b> em todos os arquivos mensais e recebe um <b>mapa comparativo de preços</b> e um relatório de <b>fornecedores</b>.',
 tip:'💡 As notas ajudam a achar bens e serviços de <b>mesma natureza</b> adquiridos por outros órgãos e fundamentar a pesquisa de preços.',
 run:async a=>{a.unring();await a.top();a.ring('#n-head','Notas Fiscais');await a.sleep(3000);a.unring();}},

{short:'Itens',t:'Passo 1 — Digite os itens a pesquisar',
 b:'Em <b>Item(ns) a pesquisar</b>, escreva <b>um item por linha</b>, com a <b>quantidade</b> se quiser (opcional). Descreva com as palavras e especificações que importam: <b>todas serão exigidas</b> na descrição da nota. O sistema mostra uma <b>tabela de conferência</b> com o que entendeu — dá para desmarcar itens (<b>Usar</b>) e corrigir quantidade e unidade.',
 tip:'💡 Quanto mais específico o item, mais coerentes os preços. Com quantidades, o mapa traz o <b>valor total do orçamento</b>.',
 run:async a=>{a.unring();await a.scroll('#n-ta',90);await a.click('#n-ta');await a.type('#n-ta-v',TXT,55);a.set(S=>S.txt=TXT);await a.sleep(500);await a.scroll('#n-conf',100);a.ring('#n-conf','Tabela de conferência',4);await a.sleep(2600);a.unring();}},

{short:'Filtros',t:'Passo 2 — Defina os filtros da pesquisa',
 b:'Em <b>Filtros da pesquisa</b>, <b>Períodos</b> já vem com todos os arquivos mensais; retire os que não interessam. Filtre por <b>nome do destinatário</b> (ex.: ARSENAL), <b>razão social do emitente</b>, <b>UF do destinatário</b> e <b>UF do emitente</b>. <b>Máximo de notas por item</b> limita o que é guardado (as mais recentes primeiro).',
 tip:'💡 Filtrar pelo seu estado ou por órgãos parecidos com o seu deixa a pesquisa mais próxima da sua realidade. Sem filtros, a busca é mais ampla e mais lenta.',
 run:async a=>{a.unring();await a.scroll('#n-per',100);a.ring('#n-per','Períodos',4);await a.sleep(1800);a.unring();await a.click('#n-dest');await a.type('#n-dest-v','ARSENAL',100);a.set(S=>S.dest='ARSENAL');await a.click('#n-uf');await a.type('#n-uf-v','RJ',160);a.set(S=>S.uf='RJ');await a.sleep(900);}},

{short:'Pesquisar',t:'Passo 3 — Clique em Pesquisar notas fiscais',
 b:'Clique em <b>🔎 Pesquisar notas fiscais</b>. O sistema <b>baixa e lê cada arquivo mensal uma única vez</b> para todos os itens e mostra o andamento (<b>n/12 arquivos processados</b>). A <b>primeira pesquisa é a mais demorada</b>: os arquivos ficam em cache para as próximas.',
 tip:'💡 Se algum arquivo falhar (limite de downloads do Google Drive), o sistema avisa; tente de novo em alguns minutos.',
 run:async a=>{a.unring();await a.scroll('#n-buscar',200);await a.click('#n-buscar',()=>a.set(S=>S.prog=0));for(const n of [3,6,9,12]){a.set(S=>S.prog=n);await a.sleep(900);}a.set(S=>S.done=true);await a.sleep(500);}},

{short:'Resultado',t:'Passo 4 — Leia o resultado e o mapa',
 b:'<b>Remover outliers e preços inexequíveis</b> vem marcado: descarta preços muito fora do padrão. A legenda informa quantas <b>linhas de notas</b> foram analisadas e os <b>filtros</b> usados. O resumo mostra os itens com <b>3+ preços</b>, o <b>valor total estimado</b> e o <b>mapa comparativo</b> com até 5 preços, <b>média unitária</b> e <b>valor total</b> por item.',
 tip:'💡 Itens com menos de 3 preços ou sem preço são sinalizados: revise a descrição (todas as palavras são exigidas) ou os filtros.',
 run:async a=>{a.unring();await a.scroll('#n-out',70);a.ring('#n-out','Outliers',4);await a.sleep(1800);a.unring();a.ring('#n-cap',null,4);await a.sleep(1800);a.unring();await a.scroll('#n-mets',50);a.ring('#n-map','Mapa comparativo',4);await a.sleep(3400);a.unring();}},

{short:'Notas',t:'Passo 5 — Autentique as notas no Portal da NF-e',
 b:'Abra <b>🧾 Notas fiscais dos preços do mapa</b>: a relação traz, para cada preço usado, o <b>emitente</b>, o <b>valor</b> e a <b>chave de acesso</b> (44 dígitos). Copie a chave, abra o <b>Portal da NF-e</b> da Receita Federal, resolva o captcha e <b>confira emitente, data e valor</b>; lá você baixa o <b>DANFE (PDF)</b> ou o <b>XML</b> da nota como prova.',
 tip:'💡 Essa relação também está no PDF e na aba “NF-e para autenticação” do Excel.',
 run:async a=>{a.unring();await a.scroll('#n-notas',80);await a.click('#n-notas',()=>a.set(S=>S.notas=true));await a.sleep(300);a.ring('#chave1','Chave de acesso (44 dígitos)',4);await a.sleep(3400);a.unring();}},

{short:'Fornecedores',t:'Passo 6 — Gere o relatório de fornecedores',
 b:'Em <b>🏢 Fornecedores encontrados</b>, escolha <b>quais fornecedores considerar</b>: <b>todos que venderam o item</b> (escolhe os melhores) ou <b>só os dos preços do mapa</b> (mais rápido). Clique em <b>📞 Gerar relatório de fornecedores</b>: o sistema consulta o cadastro de cada CNPJ e lista, por item, <b>e-mail e telefone</b> e os preços praticados.',
 tip:'💡 Havendo mais fornecedores que o limite, vêm primeiro os que têm e-mail e telefone, depois os ativos e com mais notas.',
 run:async a=>{a.unring();await a.scroll('#n-forn',200);await a.click('#n-forn',()=>a.set(S=>S.spinf=true));await a.sleep(1700);a.set(S=>{S.spinf=false;S.forn=true;});await a.scroll('#n-fornr',90);a.ring('#n-fornr','Fornecedores por item',4);await a.sleep(3000);a.unring();}},

{short:'Refinar',t:'Passo 7 — Refine a faixa de preço por item',
 b:'Em <b>Detalhes por item</b>, abra o item para ver a <b>faixa de preço unitário</b>. Ao <b>reduzir a faixa</b> (arrastando a ponta do controle), preços fora dela saem do mapa; os <b>totais e as estatísticas são recalculados</b> e os relatórios também. Aqui limitamos o máximo a <b>R$ 26,50</b>.',
 tip:'💡 O ajuste vale para o mapa e para os relatórios acima. Gere os fornecedores de novo se mudar a seleção de preços.',
 run:async a=>{a.unring();await a.scroll('#n-d1',160);await a.click('#n-d1',()=>a.set(S=>S.det=true));await a.sleep(300);await a.move('#n-slid-b');cursor.classList.add('down');await a.sleep(300);a.set(S=>S.hi=26.5);cursor.classList.remove('down');a.ring('#n-faixa','Mapa recalculado',4);await a.sleep(3000);a.unring();}},

{short:'Baixar',t:'Passo 8 — Baixe os relatórios',
 b:'Use <b>📄 Baixar mapa comparativo (PDF)</b> e <b>📊 (Excel)</b> para o mapa de preços e <b>Baixar fornecedores (PDF/Excel)</b> para a lista de empresas. <b>Resumo:</b> 1) digite os itens; 2) defina os filtros; 3) pesquise; 4) leia o mapa; 5) autentique as notas; 6) gere os fornecedores; 7) refine a faixa; 8) baixe os relatórios.',
 tip:'🎉 Fim da aula! Os dados desta aula são fictícios. Anexe o mapa e a relação de NF-e ao processo.',
 run:async a=>{a.unring();await a.scroll('#n-pdf',230);a.ring('#n-pdf','PDF');await a.click('#n-pdf',()=>a.toast('✔ NF_lote_20261021_101500.pdf'));a.unring();a.ring('#n-xls','Excel');await a.click('#n-xls',()=>a.toast('✔ NF_lote_20261021_101502.xlsx'));await a.sleep(900);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS)
