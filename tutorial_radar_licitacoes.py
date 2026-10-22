"""Vídeo-aula simulado: como usar a página Radar de Licitações (busca de licitações no PNCP e detalhamento)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar o Radar de Licitações"
DESCRICAO = (
    "Encontrar licitações por objeto, UASG, período e situação; calendário de encerramentos; documentos, link de acompanhamento, "
    "itens com deságio, fornecedores, atas e homologação. Duração aproximada: 4 min, com narração."
)

_MOCK_CSS = r"""
.opt{padding:7px 10px;border:1px solid #2b6cb0;border-radius:7px;margin-top:5px;font-size:12px;background:rgba(7,20,42,.8)}
.opt.sel{background:#1d4ed8;border-color:#60a5fa}
.mtr{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px}.mtr .k{font-size:11px;color:#b6cae2}.mtr .v{font-size:21px;font-weight:700}
.sbtn{display:inline-block;background:#1b2a47;border:1px solid #3b4d70;border-radius:8px;padding:6px 12px;font-weight:700;font-size:12px;margin:6px 8px 0 0}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:8px}
.pn{display:none}.pn.on{display:block}
#r-res,#r-det{display:none}#r-res.on,#r-det.on{display:block}
.tabs div{white-space:nowrap}
.lk{color:#60a5fa;text-decoration:underline}
.docb{background:#0b2a63;border:1px solid #2b6cb0;border-radius:7px;padding:6px 10px;margin-top:5px;font-size:11.5px}
.card3{background:rgba(8,26,57,.78);border:1px solid #d4af37;border-radius:10px;padding:10px 12px;font-size:11.5px;line-height:1.55;margin-top:8px}
.card3 .tt{color:var(--gold);font-weight:800;font-size:13px;margin-bottom:4px}
td.n,th.n{text-align:right}
"""

_STAGE_HTML = r"""
<div class="qh" id="r-head"><div class="qs">📡</div><div><b>Radar de Licitações</b><small>Licitações publicadas no PNCP: calendário, documentos, itens, deságio, fornecedores e atas.</small></div></div>

<div class="two" style="grid-template-columns:3fr 2fr;margin-top:12px">
  <div><div class="lbl">Objeto (palavras-chave)</div><div class="fld" id="r-obj"><span id="r-obj-v"></span><span class="ph">Ex: material de limpeza, gênero alimentício</span></div></div>
  <div><div class="lbl">UASG (código ou parte do nome)</div><div class="fld" id="r-uasg"><span id="r-uasg-v"></span><span class="ph">Ex: 789000 ou distrito naval</span></div></div>
</div>
<div id="r-uasg-opts" class="hid">
  <div class="lbl" style="margin-top:8px">UASG encontrada</div>
  <div class="opt" id="r-o1">889000 — COMANDO DO 8.DISTRITO NAVAL (SP)</div>
  <div class="opt" id="r-o2">789000 — COMANDO 8 DISTRITO NAVAL - SP (SP)</div>
</div>
<div class="grid4" id="r-filtros">
  <div><div class="lbl">Situação</div><div class="fld sel" id="r-sit"><span id="r-sit-v">Todas</span></div></div>
  <div><div class="lbl">UF</div><div class="fld sel"><span>Todas</span></div></div>
  <div><div class="lbl">Publicadas a partir de</div><div class="fld"><span id="r-ini-v"></span><span class="ph">dd/mm/aaaa</span></div></div>
  <div><div class="lbl">Publicadas até</div><div class="fld"><span class="ph">dd/mm/aaaa</span></div></div>
</div>
<div class="btn pri" id="r-go" style="margin-top:12px;padding:10px;font-size:13.5px;background:#d4af37;border-color:#d4af37;color:#111">🔎 Buscar licitações</div>
<div class="spin" id="r-spin"><i></i><span>Buscando licitações no PNCP...</span></div>

<div id="r-res">
  <div class="mtr" id="r-met"><div><div class="k">Licitações encontradas</div><div class="v">30</div></div><div><div class="k">Ainda recebendo propostas</div><div class="v">2</div></div><div><div class="k">Com resultado publicado</div><div class="v">24</div></div></div>
  <div class="sec2">📅 Calendário de encerramentos</div>
  <table id="r-cal"><thead><tr><th>Encerramento das propostas</th><th>Licitação</th><th>Objeto</th></tr></thead>
    <tbody><tr><td>04/11/2026 09:00</td><td>Edital nº 90031/2026</td><td>Aquisição de material de expediente</td></tr><tr><td>12/11/2026 10:00</td><td>Edital nº 90033/2026</td><td>Aquisição de material de limpeza</td></tr></tbody></table>
  <div class="sbtn" id="r-ics">📅 Adicionar à minha agenda (.ics)</div>
  <div class="sec2">📋 Licitações encontradas</div>
  <table id="r-lista"><thead><tr><th>Publicação</th><th>Encerramento</th><th>Licitação</th><th>Objeto</th><th>Resultado</th><th>PNCP</th></tr></thead>
    <tbody><tr><td>15/04/2026</td><td>29/04/2026 09:00</td><td>Edital nº 90005/2026</td><td>Materiais permanentes e de consumo</td><td>Sim</td><td class="lk">Abrir</td></tr>
    <tr><td>05/01/2026</td><td>15/01/2026 09:00</td><td>Edital nº 90022/2025</td><td>Material de limpeza e expediente</td><td>Sim</td><td class="lk">Abrir</td></tr></tbody></table>
  <div class="sbtn" id="r-xls">📊 Exportar lista (Excel)</div>
  <div class="sec2">🔍 Detalhar uma licitação</div>
  <div class="two" style="grid-template-columns:5fr 1fr"><div class="fld" id="r-sel" style="font-size:11.5px">Edital nº 90022/2025 — COMANDO 8 DISTRITO NAVAL - SP — Material de limpeza e expediente</div><div class="btn" id="r-ver">Ver detalhes</div></div>
</div>

<div id="r-det">
  <div class="card3" id="r-card"><div class="tt">Edital nº 90022/2025 — Pregão - Eletrônico</div>
    <div><b>Unidade:</b> COMANDO 8 DISTRITO NAVAL - SP (UASG 789000) — COMANDO DA MARINHA — São Paulo/SP</div>
    <div><b>Objeto:</b> Aquisição de material de limpeza e expediente</div>
    <div><b>Processo:</b> 62455.000123/2025-00 · <b>Situação:</b> Divulgada no PNCP · <b>Registro de preços:</b> Sim</div></div>
  <div class="mtr" id="r-datas"><div><div class="k">Publicação no PNCP</div><div class="v" style="font-size:16px">16/12/2025 10:15</div></div><div><div class="k">Abertura das propostas</div><div class="v" style="font-size:16px">05/01/2026 09:00</div></div><div><div class="k">Encerramento das propostas</div><div class="v" style="font-size:16px">15/01/2026 09:00</div></div></div>
  <div class="mtr" id="r-valores"><div><div class="k">Valor estimado</div><div class="v">R$ 643.114,50</div></div><div><div class="k">Valor homologado</div><div class="v">R$ 394.711,42</div></div><div><div class="k">Deságio</div><div class="v">38,6%</div></div></div>
  <div><span class="sbtn" id="r-acomp">👁️ Acompanhar a licitação</span><span class="sbtn">🌐 Ver no PNCP</span></div>
  <div class="tabs" id="r-tabs"><div id="t-doc" class="on">📎 Documentos (1)</div><div id="t-it">📦 Itens e deságio (42)</div><div id="t-fo">🏢 Fornecedores (9)</div><div id="t-at">📜 Atas e participantes (6)</div><div id="t-ho">✅ Homologação (6)</div></div>
  <div class="pn on" id="p-doc">
    <div class="docb" id="r-zip">📥 78900005900222025000.zip — Edital · publicado em 16/12/2025</div>
    <div class="cap2">Dentro do .zip: Estudo Técnico Preliminar, Termo de Referência, Edital e Relação de Itens (com valor estimado, quantidade e local de entrega).</div>
  </div>
  <div class="pn" id="p-it">
    <table id="r-itens"><thead><tr><th>Item</th><th>Descrição</th><th class="n">Unit. estimado</th><th>Vencedor</th><th class="n">Unit. homologado</th><th class="n">Deságio</th><th>Cancelados</th></tr></thead>
      <tbody><tr><td>1</td><td>Água sanitária 1 L</td><td class="n">R$ 2,58</td><td>EMPRESA EXEMPLO B</td><td class="n">R$ 1,50</td><td class="n">41,9%</td><td>EMPRESA EXEMPLO A a 1,20</td></tr>
      <tr><td>2</td><td>Detergente neutro 500 ml</td><td class="n">R$ 2,10</td><td>EMPRESA EXEMPLO C</td><td class="n">R$ 1,39</td><td class="n">33,8%</td><td>—</td></tr></tbody></table>
  </div>
  <div class="pn" id="p-fo">
    <table id="r-forn"><thead><tr><th>Fornecedor</th><th>Porte</th><th class="n">Itens vencidos</th><th class="n">Valor homologado</th><th class="n">Itens cancelados</th></tr></thead>
      <tbody><tr><td>EMPRESA EXEMPLO C</td><td>ME</td><td class="n">14</td><td class="n">R$ 152.300,00</td><td class="n">0</td></tr><tr><td>EMPRESA EXEMPLO B</td><td>EPP</td><td class="n">11</td><td class="n">R$ 98.410,00</td><td class="n">1</td></tr></tbody></table>
    <div class="two" style="grid-template-columns:5fr 1fr;margin-top:6px"><div class="fld" style="font-size:11.5px">EMPRESA EXEMPLO C (00000000000191)</div><div class="btn" id="r-consult">🏢 Consultar</div></div>
  </div>
  <div class="pn" id="p-at">
    <div class="docb" style="background:#0b2447">📜 Ata nº 00006/2026 — vigência 06/03/2026 a 06/03/2027</div>
    <div class="docb">📥 Ata de Registro de Preços nº 00006 (PDF)</div>
    <table id="r-partes" style="margin-top:6px"><thead><tr><th>Papel</th><th>Unidade</th><th>Município/UF</th></tr></thead>
      <tbody><tr><td>Gerenciadora</td><td>COMANDO 8 DISTRITO NAVAL - SP</td><td>São Paulo/SP</td></tr><tr><td>Participante</td><td>UNIDADE EXEMPLO DA MARINHA</td><td>Santos/SP</td></tr></tbody></table>
  </div>
  <div class="pn" id="p-ho">
    <div class="docb">📥 Ata de Registro de Preços nº 00006 — Ata de Registro de Preços</div>
    <div class="docb">📥 Termo de Homologação — Termo/Ato de Homologação</div>
    <div class="cap2">Quando o órgão publica, aparecem também a ata da sessão pública e o termo de adjudicação.</div>
  </div>
  <div class="sbtn" id="r-xlsdet">📊 Exportar esta licitação (Excel)</div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
let S;
function resetS(){S={obj:'',uasg:'',opts:false,sel:0,spin:false,res:false,det:false,tab:'doc'};}
function render(){
  const ph=(vid,val)=>{const e=document.getElementById(vid);e.textContent=val;const p=e.parentElement.querySelector('.ph');if(p)p.style.display=val?'none':'inline';};
  ph('r-obj-v',S.obj);ph('r-uasg-v',S.uasg);
  $('#r-uasg-opts').classList.toggle('on',S.opts);$('#r-o1').classList.toggle('sel',S.sel===1);$('#r-o2').classList.toggle('sel',S.sel===2);
  $('#r-spin').classList.toggle('on',S.spin);$('#r-res').classList.toggle('on',S.res);$('#r-det').classList.toggle('on',S.det);
  ['doc','it','fo','at','ho'].forEach(k=>{$('#p-'+k).classList.toggle('on',S.tab===k);$('#t-'+k).classList.toggle('on',S.tab===k);});
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça o Radar de Licitações',
 b:'O <b>Radar de Licitações</b> procura, no <b>PNCP</b>, as licitações publicadas pelos órgãos. Você vê o <b>calendário</b> das que ainda recebem propostas e, de cada licitação, os <b>documentos</b>, o link para <b>acompanhar</b>, os <b>itens</b> com o <b>deságio</b>, os <b>fornecedores</b> vencedores, as <b>atas de registro de preços</b> e os documentos de <b>homologação</b>.',
 tip:'💡 É ótimo para achar editais e termos de referência de outras unidades com o mesmo objeto e aproveitar como modelo.',
 run:async a=>{a.unring();await a.top();a.ring('#r-head','Radar de Licitações');await a.sleep(2800);a.unring();}},

{short:'Objeto e UASG',t:'Passo 1 — Informe o objeto e a UASG',
 b:'Digite o <b>objeto</b> em palavras-chave e, se quiser, a <b>UASG</b>. A UASG pode ser o <b>código</b> ou <b>parte do nome</b>: o sistema lista as unidades encontradas para você escolher. Atenção: algumas unidades antigas têm nome parecido e não publicam mais. Aqui, a certa é a <b>789000</b>.',
 tip:'💡 É preciso informar ao menos o objeto ou a UASG.',
 run:async a=>{a.unring();await a.top();await a.click('#r-obj');await a.type('#r-obj-v','material',90);a.set(S=>S.obj='material');
  await a.click('#r-uasg');await a.type('#r-uasg-v','distrito naval',90);a.set(S=>{S.uasg='distrito naval';S.opts=true;});await a.sleep(900);
  a.ring('#r-o1','Unidade antiga',4);await a.sleep(1600);a.unring();await a.click('#r-o2',()=>a.set(S=>S.sel=2));a.ring('#r-o2','Escolha a ativa',4);await a.sleep(1800);a.unring();}},

{short:'Filtros',t:'Passo 2 — Situação, UF e período',
 b:'Em <b>Situação</b>, escolha <b>Recebendo propostas</b> para ver só as abertas, <b>Encerradas</b> para as que já terminaram, ou <b>Todas</b>. Também dá para filtrar por <b>UF</b> e pelo <b>período de publicação</b>. Depois clique em <b>Buscar licitações</b>.',
 tip:'💡 Para pesquisar modelos e deságio, use Todas ou Encerradas. Para acompanhar oportunidades, use Recebendo propostas.',
 run:async a=>{a.unring();await a.scroll('#r-filtros',90);a.ring('#r-filtros','Filtros opcionais',4);await a.sleep(2600);a.unring();
  await a.click('#r-go',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.res=true;});await a.sleep(400);}},

{short:'Calendário',t:'Passo 3 — Veja o calendário de encerramentos',
 b:'No topo aparecem os totais: quantas licitações foram encontradas, quantas <b>ainda recebem propostas</b> e quantas já têm <b>resultado</b>. O <b>calendário</b> lista as abertas pela <b>data de encerramento</b>. O botão <b>Adicionar à minha agenda</b> baixa um arquivo que abre no <b>Outlook</b> ou no <b>Google Agenda</b>, com lembrete <b>um dia antes</b>.',
 tip:'💡 Assim você não perde o prazo de nenhuma licitação de interesse.',
 run:async a=>{a.unring();await a.scroll('#r-met',80);a.ring('#r-met','Totais');await a.sleep(2000);a.unring();a.ring('#r-cal','Encerramentos');await a.sleep(2200);a.unring();
  await a.click('#r-ics',()=>a.toast('✔ licitacoes_encerramentos.ics'));a.ring('#r-ics','Agenda');await a.sleep(1800);a.unring();}},

{short:'Lista',t:'Passo 4 — Escolha uma licitação',
 b:'A <b>lista</b> mostra cada licitação com publicação, encerramento, objeto, se já tem resultado e o link para o <b>PNCP</b>. Ela pode ser exportada para o <b>Excel</b>. Para ver tudo de uma licitação, escolha-a em <b>Detalhar uma licitação</b> e clique em <b>Ver detalhes</b>.',
 tip:'💡 Licitações grandes podem levar alguns segundos para abrir, porque o sistema busca itens, resultados e atas.',
 run:async a=>{a.unring();await a.scroll('#r-lista',90);a.ring('#r-lista','Licitações encontradas');await a.sleep(2400);a.unring();
  await a.scroll('#r-sel',150);await a.click('#r-ver',()=>a.set(S=>S.det=true));await a.sleep(500);}},

{short:'Resumo',t:'Passo 5 — Leia o resumo e acompanhe',
 b:'O resumo traz a <b>unidade</b>, o <b>objeto</b>, o processo, se é <b>registro de preços</b> e as datas de <b>abertura</b> e <b>encerramento</b> das propostas. Em seguida, o <b>valor estimado</b>, o <b>homologado</b> e o <b>deságio</b>. O botão <b>Acompanhar a licitação</b> abre a página do sistema de origem, onde aparecem as propostas e os lances.',
 tip:'💡 Os lances e as propostas dos demais participantes só aparecem no acompanhamento do sistema de origem; o PNCP não os publica.',
 run:async a=>{a.unring();await a.scroll('#r-card',70);a.ring('#r-card','Resumo');await a.sleep(2000);a.unring();a.ring('#r-valores','Deságio da licitação');await a.sleep(2400);a.unring();
  a.ring('#r-acomp','Acompanhamento');await a.sleep(2000);a.unring();}},

{short:'Documentos',t:'Passo 6 — Baixe os documentos e veja os itens',
 b:'Na aba <b>Documentos</b> estão os arquivos publicados. A Marinha costuma publicar um <b>arquivo compactado</b> com o <b>estudo técnico preliminar</b>, o <b>termo de referência</b>, o <b>edital</b> e a <b>relação de itens</b>. Na aba <b>Itens e deságio</b>, cada item mostra o valor estimado, o <b>vencedor</b>, o valor homologado, o deságio e os resultados <b>cancelados</b>.',
 tip:'💡 Resultado cancelado mostra quem chegou a vencer e depois foi substituído, por exemplo por desistência ou inabilitação.',
 run:async a=>{a.unring();await a.scroll('#r-tabs',60);a.ring('#r-zip','Edital, TR e ETP');await a.sleep(2400);a.unring();
  await a.click('#t-it',()=>a.set(S=>S.tab='it'));await a.sleep(500);a.ring('#r-itens','Deságio por item');await a.sleep(2800);a.unring();}},

{short:'Fornecedores',t:'Passo 7 — Fornecedores, atas e homologação',
 b:'A aba <b>Fornecedores</b> mostra quem venceu, o porte, os itens e o valor homologado; o botão <b>Consultar</b> abre a <b>Consulta CNPJ</b>. Em <b>Atas e participantes</b> estão as atas de registro de preços, com o PDF e as unidades <b>gerenciadora</b> e <b>participantes</b>. Em <b>Homologação</b>, o termo de homologação e as atas, quando publicados.',
 tip:'💡 As participantes da ata indicam quais unidades já estão incluídas no registro de preços.',
 run:async a=>{a.unring();await a.scroll('#r-tabs',60);await a.click('#t-fo',()=>a.set(S=>S.tab='fo'));await a.sleep(500);a.ring('#r-forn','Vencedores');await a.sleep(2000);a.unring();
  a.ring('#r-consult','Abre a Consulta CNPJ');await a.sleep(1600);a.unring();
  await a.click('#t-at',()=>a.set(S=>S.tab='at'));await a.sleep(500);a.ring('#r-partes','Gerenciadora e participantes');await a.sleep(2200);a.unring();
  await a.click('#t-ho',()=>a.set(S=>S.tab='ho'));await a.sleep(1400);}},

{short:'Exportar',t:'Passo 8 — Exporte a licitação',
 b:'Por fim, <b>Exportar esta licitação</b> gera uma planilha <b>Excel</b> com o resumo, os itens, os fornecedores e os documentos. <b>Resumo:</b> 1) objeto e UASG; 2) filtros e buscar; 3) calendário; 4) escolha a licitação; 5) resumo e acompanhamento; 6) documentos e itens; 7) fornecedores, atas e homologação; 8) exporte.',
 tip:'🎉 Fim da aula! Use o Radar para encontrar modelos, acompanhar prazos e conhecer o deságio das compras.',
 run:async a=>{a.unring();await a.scroll('#r-xlsdet',200);a.ring('#r-xlsdet','Excel');await a.click('#r-xlsdet',()=>a.toast('✔ licitacao_789000_2025_14559.xlsx'));await a.sleep(1800);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="radar_licitacoes")
