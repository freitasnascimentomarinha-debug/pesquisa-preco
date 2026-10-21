"""Vídeo-aula simulado: como usar a página Web Scraping (pesquisa de preços automatizada na internet)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar o Web Scraping"
DESCRICAO = (
    "Pesquisa de preços automatizada na internet: itens, configurações, execução, ajuste manual, mapa comparativo, "
    "prints de evidência e relatórios. Duração aproximada: 3 min."
)

_MOCK_CSS = r"""
#w-exec,#w-res{display:none}#w-exec.on,#w-res.on{display:block}
.cols{display:grid;grid-template-columns:2.6fr 1.4fr;gap:12px}
.cfg{background:rgba(8,26,57,.78);border:1px solid #1e5b9f;border-radius:9px;padding:9px 10px;font-size:11px}
.cfg h4{margin:0 0 6px;color:var(--gold);font-size:13px}
.cfg .f{background:rgba(7,20,42,.8);border:1px solid #2b6cb0;border-radius:6px;padding:4px 8px;margin:2px 0 7px;font-size:12px}
.cfg .cb{display:flex;gap:6px;align-items:flex-start;margin-bottom:7px}
.cfg .cb .box{width:14px;height:14px;font-size:10px;margin-top:1px}
.logbox{max-height:96px;overflow:hidden}
#w-map td,#w-map th{font-size:10px;padding:5px 4px;white-space:nowrap}#w-map td.n{text-align:right}
#w-adtab td,#w-adtab th{font-size:10.5px;padding:5px}
.warnb{background:rgba(245,158,11,.14);border:1px solid rgba(245,158,11,.4);color:#fde68a;border-radius:8px;padding:8px 11px;margin:8px 0;font-size:11px;line-height:1.4}
.tabs div{cursor:default}
.tp{display:none}.tp.on{display:block}
.tot{margin:8px 0}.tot .k{font-size:11px;color:#b6cae2}.tot .v{font-size:24px;font-weight:700}
.msx{display:flex;flex-wrap:wrap;gap:4px;background:rgba(7,20,42,.8);border:1px solid #2b6cb0;border-radius:7px;padding:6px 8px;min-height:30px;font-size:10.5px}
.msx span{background:#ef4444;color:#fff;border-radius:5px;padding:2px 7px;font-weight:700}
.dd.up{top:auto;bottom:36px}
.alsty{background:#0b2447;border:1px solid var(--line);border-radius:7px;padding:8px 11px;margin-top:8px;font-size:11.5px}
.alsty .b{display:none;margin-top:8px}.alsty .b.on{display:block}
"""

_STAGE_HTML = r"""
<div class="hdr" id="w-head"><div class="l">MARINHA DO BRASIL</div><div class="s">ATACOTADA</div><div class="u">🕷️ WEB SCRAPING — PESQUISA DE PREÇOS AUTOMATIZADA</div></div>
<div class="sec2" style="font-size:17px">📝 Itens para Pesquisa</div>
<div class="cols">
  <div>
    <div class="lbl">Informe os itens (um por linha, com a quantidade ao lado, se quiser):</div>
    <div class="ta" id="w-ta" style="min-height:80px"><span id="w-ta-v"></span><span class="ph" id="w-ta-ph">Exemplo:
Lâmpada led bulbo 9W E27 branca - 30
Caneta piloto azul; 100 un
Detergente 500ml</span></div>
    <div class="cap2">Dica: quanto mais específico, mais certo o preço. Inclua tipo, potência/medida e embalagem, sem marca. Nomes do dia a dia como “caneta piloto” e “durex” são traduzidos para o nome usado pelas lojas.</div>
  </div>
  <div class="cfg" id="w-cfg"><h4>⚙️ Configurações</h4>
    <div class="cb"><span class="box on" style="background:#ef4444;border-color:#ef4444">✓</span><span>Usar o navegador como reserva (Playwright)</span></div>
    <div>Tempo máx. por página no navegador (min)</div><div class="f">2</div>
    <div>Máx. fontes por item</div><div class="f" id="w-maxf">3</div>
    <div>Delay mín. (seg)</div><div class="f">2,0</div>
    <div>Delay máx. (seg)</div><div class="f">6,0</div>
  </div>
</div>
<hr style="border-color:#1e5b9f;margin:12px 0">
<div class="btn pri" id="w-go" style="width:60%;margin:0 auto;padding:10px;font-size:13.5px">🚀 Iniciar Scraping</div>

<div id="w-exec">
  <div class="sec2">📊 Execução do Scraping</div>
  <div class="lbl">📜 Log de Execução</div>
  <div class="mono logbox" id="w-log"></div>
  <div class="prog on" style="margin-top:8px"><div class="t" id="w-prog-t"></div><div class="b"><i id="w-prog-b"></i></div></div>
</div>

<div id="w-res">
  <div class="sec2">Ajuste Manual da Composição</div>
  <div class="lbl">Selecione os orçamentos que devem sair da composição:</div>
  <div class="fld sel" id="w-excl"><div class="msx" id="w-excl-v"></div>
    <div class="dd up" id="w-excl-dd"><div id="w-o-pen3">Caneta piloto azul | loja-exemplo-3.com.br | R$ 1,45 (gel)</div><div>Lâmpada led bulbo 9W E27 | loja-exemplo-1.com.br | R$ 8,90</div></div></div>
  <hr style="border-color:#1e5b9f;margin:12px 0">
  <div class="sec2" style="margin-top:0">📋 Resultados</div>
  <div class="cap2" id="w-cap"></div>
  <div class="tabs" id="w-tabs"><div class="on" id="tb-rel">📑 Relatório Padrão</div><div id="tb-tab">📊 Tabela Completa</div><div id="tb-res">📈 Resumo</div><div id="tb-evi">📸 Evidências</div><div id="tb-exp">📥 Exportar</div></div>

  <div class="tp on" id="tp-rel">
    <div class="lbl" style="margin-top:8px">Preços por item no relatório</div><div class="fld sel" style="max-width:120px">3</div>
    <div class="cap2">Mesmas regras da Cotação Rápida: sem outliers, preços a ±30% da média, mapa comparativo na 1ª página, endereço e data/hora do acesso de cada preço.</div>
    <table id="w-map"><thead><tr><th>#</th><th>Descrição</th><th>Preço 1</th><th>Preço 2</th><th>Preço 3</th><th>Média unit.</th><th>Valor total</th></tr></thead><tbody></tbody></table>
    <div class="tot" id="w-tot"></div>
    <div class="warnb" id="w-warn">1 preço(s) do mapa vieram da leitura do texto da página (confiança baixa): confira o anúncio antes de usar.<br>• <b>Lâmpada led bulbo 9W E27</b> — loja-exemplo-3.com.br — R$ 7,90</div>
    <div class="alsty" id="w-prints"><b>📸 Prints reais das páginas dos preços do mapa</b>
      <div class="b on"><div class="cap2">Quando o navegador acha o preço durante a pesquisa, o print já fica guardado (com data, hora e endereço no rodapé). Aqui você tira só os que faltam. Os prints entram como anexo no PDF.</div>
      <div class="cap2" id="w-pcap">3 página(s) do mapa já têm print; 3 faltam.</div>
      <div class="btn" id="w-pbtn" style="padding:6px">📸 Tirar os prints das 3 página(s) que faltam</div>
      <div class="prog" id="w-pprog"><div class="t" id="w-pprog-t"></div><div class="b"><i id="w-pprog-b"></i></div></div>
      <div class="ok2" id="w-pok" style="color:#86efac;font-size:11.5px;margin-top:6px"></div></div></div>
    <div class="two" style="margin-top:10px"><div class="btn pri" id="w-pdf">📄 Baixar relatório PDF (padrão Cotação Rápida)</div><div class="btn" id="w-xls">📊 Baixar relatório Excel</div></div>
  </div>
  <div class="tp" id="tp-tab"><table id="w-adtab" style="margin-top:8px"><thead><tr><th>Item</th><th>Fornecedor</th><th>Preço (R$)</th><th>Link</th><th>Data Coleta</th></tr></thead><tbody></tbody></table></div>
  <div class="tp" id="tp-res"><div class="mets" style="margin-top:10px;grid-template-columns:repeat(4,1fr)" id="w-mets"></div></div>
  <div class="tp" id="tp-evi"><div class="cap2" style="margin-top:10px"><b>6 evidências visuais capturadas</b> — expanda cada uma para ver o print e baixar.</div><div class="btn" style="width:230px;padding:6px">📑 Exportar Evidências em PDF</div></div>
  <div class="tp" id="tp-exp"><div class="sec2">📥 Exportar Relatório</div><div class="g5" style="grid-template-columns:repeat(4,1fr);display:grid;gap:8px"><div class="btn pri">📊 Baixar Excel</div><div class="btn">📄 Baixar CSV</div><div class="btn">🔗 Baixar JSON</div><div class="btn">📑 Baixar Evidências PDF</div></div></div>

  <div class="alsty" id="w-ens"><b>🔤 Ensinar nomes ao sistema (aprende com o uso)</b>
    <div class="b on"><div class="cap2">O que se ensina aqui vale nas próximas pesquisas. Marque os anúncios que <b>NÃO são o item pedido</b> e o sistema aprende a recusar anúncios assim.</div>
    <div class="btn" id="w-ensbtn" style="width:300px;padding:6px">🧠 Ensinar: esses anúncios não são o item</div>
    <div class="ok2" id="w-ensok" style="color:#86efac;font-size:11.5px;margin-top:6px"></div></div></div>
  <div class="alsty" id="w-mem"><b>🧠 Memória de lojas (aprende com o uso)</b><div class="cap2" style="margin:4px 0 0">A cada pesquisa o sistema guarda as lojas que deram preço e os itens que cada uma cotou; nas próximas, tenta primeiro essas lojas para itens parecidos.</div></div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const TXT='Lâmpada led bulbo 9W E27 branca - 30\nCaneta piloto azul; 100 un';
const ADS=[
 {i:0,id:'l1',f:'loja-exemplo-1.com.br',p:8.90},{i:0,id:'l2',f:'loja-exemplo-2.com.br',p:9.49},{i:0,id:'l3',f:'loja-exemplo-3.com.br',p:7.90},
 {i:1,id:'p1',f:'loja-exemplo-4.com.br',p:1.20},{i:1,id:'p2',f:'loja-exemplo-5.com.br',p:1.35},{i:1,id:'p3',f:'loja-exemplo-3.com.br',p:1.45},{i:1,id:'p4',f:'loja-exemplo-6.com.br',p:1.10}];
const NOMES=['Lâmpada led bulbo 9W E27 branca','Caneta piloto azul'],QTD=[30,100];
const LOG=['🔎 Pesquisando: Lâmpada led bulbo 9W E27 branca','   ✅ loja-exemplo-1.com.br — R$ 8,90','   ✅ loja-exemplo-2.com.br — R$ 9,49','   ✅ loja-exemplo-3.com.br — R$ 7,90 (texto da página)','🔎 Pesquisando: Caneta piloto azul → buscado como “caneta marcador permanente azul”','   ✅ loja-exemplo-4.com.br — R$ 1,20','   ✅ loja-exemplo-5.com.br — R$ 1,35','   ✅ loja-exemplo-3.com.br — R$ 1,45','   ✅ loja-exemplo-6.com.br — R$ 1,10'];
let S;
function resetS(){S={txt:'',run:false,n:0,done:false,dd:false,excl:false,tab:'rel',pp:0,ens:false};}
function comp(i){return ADS.filter(a=>a.i===i&&!(S.excl&&a.id==='p3'));}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('w-ta-v',S.txt);$('#w-ta-ph').style.display=S.txt?'none':'inline';
  $('#w-exec').classList.toggle('on',S.run);$('#w-res').classList.toggle('on',S.done);
  $('#w-log').innerHTML=LOG.slice(0,S.n).map(x=>x.replace(/ /g,'&nbsp;')).join('<br>');
  T('w-prog-t',S.done?'Execução concluída ✅':S.n+'/'+LOG.length+' consultas…');$('#w-prog-b').style.width=(S.done?100:S.n/LOG.length*100)+'%';
  if(!S.done)return;
  $('#w-excl-dd').classList.toggle('on',S.dd);$('#w-excl-v').innerHTML=S.excl?'<span>Caneta piloto azul | loja-exemplo-3.com.br | R$ 1,45 ×</span>':'<span style="background:transparent;color:#7e93b3;font-weight:400">Escolha os orçamentos</span>';
  T('w-cap',(S.excl?6:7)+' de 7 orçamento(s) permanecem na composição após os descartes automáticos e manuais.');
  ['rel','tab','res','evi','exp'].forEach(k=>{$('#tp-'+k).classList.toggle('on',S.tab===k);$('#tb-'+k).classList.toggle('on',S.tab===k);});
  const P=[0,1].map(i=>comp(i).slice(0,3).map(a=>a.p));
  $('#w-map tbody').innerHTML=P.map((p,i)=>'<tr><td>'+(i+1)+'</td><td>'+NOMES[i]+'</td>'+[0,1,2].map(k=>'<td class="n">'+(p[k]!=null?brl(p[k]):'')+'</td>').join('')+'<td class="n"><b>'+brl(mean(p))+'</b></td><td class="n">'+brl(mean(p)*QTD[i])+'</td></tr>').join('');
  $('#w-tot').innerHTML='<div class="k">Valor total estimado do orçamento</div><div class="v">'+brl(P.reduce((a,p,i)=>a+mean(p)*QTD[i],0))+'</div>';
  $('#w-adtab tbody').innerHTML=ADS.filter(a=>!(S.excl&&a.id==='p3')).map(a=>'<tr><td>'+NOMES[a.i]+'</td><td>'+a.f+'</td><td>'+brl(a.p)+'</td><td style="color:#60a5fa">Acessar</td><td>21/10/2026 10:1'+(a.i)+'</td></tr>').join('');
  const all=ADS.filter(a=>!(S.excl&&a.id==='p3'));
  $('#w-mets').innerHTML='<div class="met"><div class="k">Total de Orçamentos</div><div class="v">'+all.length+'</div></div><div class="met"><div class="k">Itens Pesquisados</div><div class="v">2</div></div><div class="met"><div class="k">Fontes Distintas</div><div class="v">'+new Set(all.map(a=>a.f)).size+'</div></div><div class="met"><div class="k">Menor Preço</div><div class="v">'+brl(Math.min(...all.map(a=>a.p)))+'</div></div>';
  $('#w-pprog').classList.toggle('on',S.pp===1);T('w-pprog-t',S.pp===1?'Capturando '+S.pq+' de 3…':'');$('#w-pprog-b').style.width=(S.pp===1?(S.pq||0)/3*100:0)+'%';
  T('w-pok',S.pp===2?'6 print(s) prontos; entram no PDF abaixo.':'');T('w-pcap',S.pp===2?'6 página(s) do mapa já têm print; 0 faltam.':'3 página(s) do mapa já têm print; 3 faltam.');
  $('#w-pbtn').style.display=S.pp===2?'none':'block';
  T('w-ensok',S.ens?'✅ Aprendido: anúncios parecidos com “caneta gel” serão recusados nas próximas pesquisas.':'');
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Web Scraping',
 b:'A página <b>Web Scraping</b> faz <b>pesquisa de preços automatizada na internet</b>: para cada item ela <b>busca lojas</b>, abre as páginas, <b>lê o preço</b> e guarda o <b>endereço, a data/hora do acesso e um print</b> como evidência. No final monta o <b>mapa comparativo</b> no mesmo padrão da Cotação Rápida.',
 tip:'💡 A pesquisa em sítios eletrônicos é uma das fontes de preço aceitas na IN SEGES/ME nº 65/2021, desde que registre a <b>data e a hora de acesso</b> — o sistema já faz isso.',
 run:async a=>{a.unring();await a.top();a.ring('#w-head','Pesquisa automatizada na internet');await a.sleep(3000);a.unring();}},

{short:'Itens',t:'Passo 1 — Digite os itens',
 b:'Em <b>Itens para Pesquisa</b>, escreva <b>um item por linha</b>, com a <b>quantidade</b> se quiser. Seja <b>específico</b>: inclua tipo, potência ou medida e embalagem (ex.: “lâmpada led bulbo 9W E27 branca”), <b>sem marca</b>. Nomes do dia a dia, como “caneta piloto”, são <b>traduzidos</b> para o nome que as lojas usam.',
 tip:'💡 Item vago traz preço de produto diferente. Se a quantidade for medida do item, escreva com a unidade colada (“20m”, “9w”).',
 run:async a=>{a.unring();await a.top();await a.click('#w-ta');await a.type('#w-ta-v',TXT,55);a.set(S=>S.txt=TXT);a.ring('#w-ta','Um item por linha',4);await a.sleep(2200);a.unring();}},

{short:'Configurações',t:'Passo 2 — Ajuste as configurações',
 b:'Na coluna <b>⚙️ Configurações</b>: <b>Navegador como reserva</b> abre a página como um navegador de verdade quando a leitura simples não acha o preço — e guarda o <b>print</b>. <b>Máx. fontes por item</b> define quantos orçamentos buscar por item (1 a 5). Os <b>delays</b> (mínimo e máximo, em segundos) são pausas entre acessos, para <b>não sobrecarregar os sites</b>.',
 tip:'💡 O padrão (3 fontes, delay de 2 a 6 s) atende bem à maioria dos casos. O delay mínimo deve ser menor que o máximo.',
 run:async a=>{a.unring();await a.scroll('#w-cfg',80);a.ring('#w-cfg','Configurações',4);await a.sleep(3600);a.unring();}},

{short:'Executar',t:'Passo 3 — Clique em Iniciar Scraping',
 b:'Clique em <b>🚀 Iniciar Scraping</b>. A tela mostra o <b>log de execução</b> — cada item pesquisado, as lojas que deram preço e o valor — e uma <b>barra de progresso</b>. A pesquisa pode levar alguns minutos: <b>não feche nem recarregue a aba</b> até terminar.',
 tip:'💡 Sem chave de API de busca, o sistema usa só o DuckDuckGo (gratuito, sujeito a bloqueio). O administrador pode configurar Serper ou Tavily para busca mais estável.',
 run:async a=>{a.unring();await a.scroll('#w-go',150);await a.click('#w-go',()=>a.set(S=>S.run=true));await a.scroll('#w-exec',60);for(let n=1;n<=9;n++){a.set(S=>S.n=n);await a.sleep(550);}a.set(S=>S.done=true);await a.sleep(800);}},

{short:'Ajuste manual',t:'Passo 4 — Retire anúncios que não servem',
 b:'Em <b>Ajuste Manual da Composição</b>, selecione os orçamentos que devem <b>sair</b> da composição. Aqui retiramos o anúncio da caneta a R$ 1,45, que era de <b>caneta gel</b>, e não do item pedido. A legenda passa a mostrar <b>“6 de 7 orçamentos permanecem”</b> e o mapa, o resumo e as exportações são <b>recalculados</b>.',
 tip:'💡 Confira o anúncio (clique no link) antes de aceitar um preço. A decisão final sobre o que entra na pesquisa é sua.',
 run:async a=>{a.unring();await a.scroll('#w-excl',100);await a.click('#w-excl',()=>a.set(S=>S.dd=true));await a.click('#w-o-pen3',()=>a.set(S=>{S.excl=true;S.dd=false;}));a.ring('#w-cap','Composição atualizada',4);await a.sleep(2600);a.unring();}},

{short:'Mapa',t:'Passo 5 — Leia o Relatório Padrão',
 b:'Na aba <b>📑 Relatório Padrão</b> está o <b>mapa comparativo</b>: até 3 preços por item (você pode escolher 3, 4 ou 5), <b>média unitária</b> e <b>valor total</b> (com as quantidades), mais o <b>valor total estimado do orçamento</b>. Valem as mesmas regras da Cotação Rápida: sem outliers e preços a até 30% da média.',
 tip:'💡 O aviso amarelo lista preços de <b>confiança baixa</b> (lidos do texto da página): abra o anúncio e confira antes de usar.',
 run:async a=>{a.unring();await a.scroll('#w-tabs',60);a.ring('#w-map','Mapa comparativo',4);await a.sleep(2600);a.unring();a.ring('#w-tot','Total do orçamento',4);await a.sleep(1800);a.unring();await a.scroll('#w-warn',120);a.ring('#w-warn','Confira este preço',4);await a.sleep(2800);a.unring();}},

{short:'Prints',t:'Passo 6 — Tire os prints de evidência',
 b:'Em <b>📸 Prints reais das páginas dos preços do mapa</b>, o sistema informa quantas páginas <b>já têm print</b> (tirado durante a pesquisa) e quantas faltam. Clique em <b>📸 Tirar os prints das páginas que faltam</b>: um navegador abre cada página, rola até o preço e <b>destaca o valor</b>, com data, hora e endereço no rodapé. Os prints entram como <b>anexo do PDF</b>.',
 tip:'💡 Cada página leva de 5 a 30 segundos. Não feche nem recarregue a aba até terminar.',
 run:async a=>{a.unring();await a.scroll('#w-prints',80);await a.click('#w-pbtn',()=>a.set(S=>{S.pp=1;S.pq=0;}));for(const n of [1,2,3]){a.set(S=>S.pq=n);await a.sleep(1000);}a.set(S=>S.pp=2);a.ring('#w-prints','Prints prontos',4);await a.sleep(2600);a.unring();}},

{short:'Outras abas',t:'Passo 7 — Explore as outras abas',
 b:'<b>📊 Tabela Completa</b> lista todos os orçamentos com fornecedor, preço, link e data da coleta. <b>📈 Resumo</b> traz os totais e o menor preço. <b>📸 Evidências</b> reúne os prints. <b>📥 Exportar</b> oferece Excel, CSV, JSON e PDF de evidências.',
 tip:'💡 Use a Tabela Completa para conferir cada anúncio e abrir o link da loja.',
 run:async a=>{a.unring();await a.scroll('#w-tabs',60);for(const k of ['tab','res','evi','exp']){await a.click('#tb-'+k,()=>a.set(S=>S.tab=k));await a.sleep(1700);}await a.click('#tb-rel',()=>a.set(S=>S.tab='rel'));await a.sleep(500);}},

{short:'Baixar',t:'Passo 8 — Baixe o relatório',
 b:'De volta ao <b>Relatório Padrão</b>, use <b>📄 Baixar relatório PDF</b> — mapa comparativo na primeira página, endereço e data/hora do acesso de cada preço e os <b>prints em anexo</b> — e <b>📊 Baixar relatório Excel</b>. Anexe o PDF ao processo como memória da pesquisa de preços.',
 tip:'💡 O sistema guarda o que aprende (lojas boas, nomes populares). Veja em “Memória de lojas”.',
 run:async a=>{a.unring();await a.scroll('#w-pdf',230);a.ring('#w-pdf','PDF',4);await a.click('#w-pdf',()=>a.toast('✔ pesquisa_web_20261021_1015.pdf'));a.unring();a.ring('#w-xls','Excel',4);await a.click('#w-xls',()=>a.toast('✔ pesquisa_web_20261021_1015.xlsx'));await a.sleep(900);a.unring();}},

{short:'Ensinar',t:'Passo 9 — Ensine o sistema (opcional)',
 b:'Em <b>🔤 Ensinar nomes ao sistema</b>, marque os anúncios que <b>não são o item pedido</b> e clique em <b>🧠 Ensinar</b>: nas próximas pesquisas o sistema <b>recusa anúncios parecidos</b>. A <b>🧠 Memória de lojas</b> guarda as lojas que deram preço e quais itens cada uma cotou, para tentá-las primeiro em itens semelhantes. <b>Resumo:</b> 1) itens; 2) configurações; 3) iniciar; 4) ajuste manual; 5) mapa; 6) prints; 7) outras abas; 8) baixar.',
 tip:'🎉 Fim da aula! Os preços e lojas desta aula são fictícios.',
 run:async a=>{a.unring();await a.scroll('#w-ens',120);await a.click('#w-ensbtn',()=>a.set(S=>S.ens=true));a.ring('#w-ens','O sistema aprende',4);await a.sleep(2600);a.unring();a.ring('#w-mem','Memória de lojas',4);await a.sleep(2600);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS)
