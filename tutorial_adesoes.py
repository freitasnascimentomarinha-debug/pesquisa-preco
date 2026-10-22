"""Vídeo-aula simulado: como usar a página Adesões (atas de registro de preços para adesão/“carona”)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a página Adesões"
DESCRICAO = (
    "Achar atas de registro de preços para adesão (tipo de item, família, esfera, mapa por estado, dados e documentos de "
    "cada ata) e montar a adesão: itens, quantidades, vantajosidade e ofício no Babilaca. Duração aproximada: 5 min, "
    "com narração."
)

_MOCK_CSS = r"""
#a-s1,#a-res{display:none}#a-s1.on,#a-res.on{display:block}
.cntb{background:linear-gradient(135deg,#0a2540,#164863);border-left:5px solid var(--gold);border-radius:8px;text-align:center;padding:10px;margin:10px 0}
.cntb .v{color:var(--gold);font-size:28px;font-weight:800}.cntb .k{color:#cbd5e1;font-size:12px}
.dd.lg div{font-size:11.5px}
#a-map{position:relative;width:560px;height:330px;margin:8px auto}
.tile{position:absolute;width:56px;height:42px;border-radius:7px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#0b1b3a;border:1px solid rgba(255,255,255,.25)}
.tile small{font-size:10px;font-weight:700}
.t0{background:#334155;color:#94a3b8}.t1{background:#fde68a}.t2{background:#fbbf24}.t3{background:#f59e0b}.t4{background:#ea580c;color:#fff}
.ata{background:rgba(8,26,57,.78);border:1px solid #1e5b9f;border-radius:9px;padding:9px 12px;margin:8px 0;font-size:11.5px}
.ata b.t{font-size:12.5px}.ata .lk{color:#60a5fa;text-decoration:underline;margin:3px 0 5px;display:block}
.docs{display:none;margin-top:6px}.docs.on{display:block}
#a-list{display:none}#a-list.on{display:block}#a-mapbox.off{display:none}
.ata .bts{display:flex;gap:6px;margin-top:6px}.ata .bts .btn{padding:5px 8px;font-size:11px;width:auto}
.aprov{display:none;margin-top:6px}.aprov.on{display:block}
#a-cesta,#a-van,#a-bab{display:none}#a-cesta.on,#a-van.on,#a-bab.on{display:block}
.cbox{background:rgba(8,26,57,.85);border:1px solid #d4af37;border-radius:9px;padding:9px 12px;margin:8px 0;font-size:11.5px}
table.tb{width:100%;border-collapse:collapse;font-size:11px;margin:6px 0}
table.tb th{background:#0f2b52;color:#f8e7a1;text-align:left;padding:4px 5px;border:1px solid #1e3a5f}
table.tb td{padding:4px 5px;border:1px solid #1e3a5f;color:#e2e8f0}
td.q{background:#0b2a4a;min-width:44px;font-weight:800;color:#fde68a}
.okm{background:#14532d;border:1px solid #22c55e;color:#dcfce7;border-radius:7px;padding:6px 9px;margin-top:6px;font-size:11.5px}
.row3{display:flex;gap:8px;margin-top:6px}.row3 .btn{flex:1;padding:6px;font-size:11.5px}
.bab{background:#f8fafc;color:#0f172a;border-radius:8px;padding:10px 14px;font-size:11px;line-height:1.45}
.bab b{color:#0f172a}
"""

_STAGE_HTML = r"""
<div class="qh" id="a-head"><div class="qs">🤝</div><div><b>Adesões</b><small>Consulta inteligente às atas de registro de preços do Compras.gov.br.</small></div></div>
<div class="cap2" style="color:#dbe7f7">Selecione o tipo de item, escolha o código desejado e encontre atas para adesão.</div>
<div class="lbl">Tipo de item</div>
<div class="fld sel" id="a-tipo"><span id="a-tipo-v"></span><span class="ph" id="a-tipo-ph">Selecione material ou serviço</span><div class="dd" id="a-dd"><div id="a-o-mat">Material</div><div>Serviço</div></div></div>

<div id="a-s1">
  <div class="cap2">Pesquise pelo nome, por uma descrição (ex.: resma de papel a4) ou pelo código CATMAT/PDM — catálogo oficial atualizado em 2026.</div>
  <div class="lbl">Pesquisar material</div>
  <div class="fld" id="a-q"><span id="a-q-v"></span><span class="ph" id="a-q-ph">Ex.: notebook, luva de procedimento, resma de papel a4</span></div>
  <div id="a-fb" class="hid">
    <div class="ck" id="a-cb1" style="margin-top:8px"><span class="box on" style="background:#ef4444;border-color:#ef4444">✓</span><span>Mostrar apenas famílias com atas vigentes</span></div>
    <div class="lbl" style="margin-top:8px">Famílias de material encontradas (a busca de atas é feita pela família)</div>
    <div class="fld sel" id="a-fam"><span id="a-fam-v" style="font-size:11.5px"></span>
      <div class="dd lg" id="a-fdd"><div id="a-f1">PAPEL SULFITE · PDM 8710 · 14 atas vigentes · 92%</div><div>PAPEL REPROGRÁFICO · PDM 8722 · 3 atas vigentes · 71%</div><div>PAPEL COUCHÊ · PDM 8733 · 1 ata vigente · 60%</div></div></div>
    <div class="cap2" id="a-fclass"></div>
    <div class="ck" id="a-cb2" style="margin-top:6px"><span class="box on" style="background:#ef4444;border-color:#ef4444">✓</span><span>Buscar somente atas da esfera federal</span></div>
    <div class="btn pri" id="a-buscar" style="margin-top:10px">Buscar adesões</div>
  </div>
</div>
<div class="spin" id="a-spin"><i></i><span>Buscando atas…</span></div>

<div id="a-res">
  <div class="cntb" id="a-total"><div class="v">14</div><div class="k">atas encontradas no total</div></div>
  <div id="a-mapbox">
    <div class="sec2" style="margin-top:6px">Mapa das atas encontradas</div>
    <div class="cap2">Clique no estado onde deseja encontrar atas para adesão.</div>
    <div id="a-map"></div>
  </div>
  <div id="a-list">
    <div class="sec2">Atas encontradas - RJ</div>
    <div class="btn" id="a-limpar" style="width:200px">Limpar filtro de estado</div>
    <div class="cntb" style="padding:6px"><div class="v" style="font-size:22px">4</div><div class="k">atas em RJ</div></div>
    <div id="a-cards"></div>
  </div>
  <div id="a-cesta">
    <div class="sec2">🛒 Itens escolhidos para adesão</div>
    <div class="cap2">Cada ata vira um ofício ao seu órgão gerenciador. Informe a quantidade pretendida de cada item (até o máximo por órgão), analise a vantajosidade e gere o ofício no Babilaca.</div>
    <div class="cbox" id="a-cbox"><b>Ata 00012/2026</b> — UNIDADE EXEMPLO RJ-A (UASG 000001) · Pregão Eletrônico nº 90005/2026
      <table class="tb" id="a-ctab"><tr><th>Incluir</th><th>Item</th><th>Descrição</th><th>Preço registrado</th><th>Máx. por órgão</th><th>Quantidade pretendida</th></tr>
        <tr id="a-r1"><td>☑</td><td>1</td><td>PAPEL A4, GRAMATURA 75 G/M2, RESMA 500 FL</td><td>R$ 22,50</td><td id="a-m1">300</td><td class="q" id="a-q1"></td></tr>
        <tr id="a-r2"><td>☑</td><td>3</td><td>PAPEL A3, GRAMATURA 75 G/M2, RESMA 500 FL</td><td>R$ 48,00</td><td>100</td><td class="q" id="a-q2"></td></tr></table>
      <div class="row3"><div class="btn" id="a-anl">📊 Analisar vantajosidade</div><div class="btn pri" id="a-gof">✉️ Gerar ofício no Babilaca</div><div class="btn" style="flex:.5">🗑️ Remover</div></div>
      <div id="a-van">
        <table class="tb"><tr><th>Item</th><th>Preço da ata</th><th>Mediana de mercado</th><th>Preços</th><th>Diferença</th><th>Economia</th><th>Situação</th></tr>
          <tr><td>1</td><td>R$ 22,50</td><td>R$ 26,80</td><td>7/8</td><td>-16,0%</td><td>R$ 430,00</td><td>✅ vantajoso</td></tr>
          <tr><td>3</td><td>R$ 48,00</td><td>R$ 45,00</td><td>4/4</td><td>+6,7%</td><td>-R$ 150,00</td><td>🟡 até 10% acima do mercado</td></tr></table>
        <div class="okm" id="a-okm">Adesão: R$ 4.650,00 × mercado (mediana): R$ 4.930,00 → economia de R$ 280,00 (5,7%). O relatório e a justificativa vão junto com o ofício.</div>
      </div>
    </div>
  </div>
  <div id="a-bab">
    <div class="sec2">🧠 O Babilaca abre o ofício já preenchido</div>
    <div class="bab" id="a-babdoc"><b>Nº ___ — Assunto:</b> Solicitação de adesão a Ata de Registro de Preços<br><b>Anexo:</b> A) Relatório de vantajosidade da adesão.<br><br>
      1. Solicito a autorização desse órgão gerenciador (UNIDADE EXEMPLO RJ-A) para que esta Organização Militar adira, na condição de órgão não participante, à Ata de Registro de Preços nº 00012/2026...<br>
      2. A adesão se justifica porque os preços registrados foram comparados com 11 preços do mesmo item em outras atas e contratações dos últimos 12 meses, e o valor da adesão (R$ 4.650,00) é inferior em R$ 280,00 (5,7%) ao valor pela mediana de mercado...<br>
      3. Itens e quantidades: item 1 — 100 resmas; item 3 — 50 resmas.</div>
  </div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const UFS={RR:[2,0],AP:[4,0],AM:[1,1],PA:[3,1],MA:[4,1],CE:[5,1],RN:[6,1],AC:[0,2],RO:[1,2],MT:[2,2],TO:[3,2],PI:[4,2],PE:[5,2],PB:[6,2],MS:[2,3],GO:[3,3],DF:[4,3],BA:[5,3],AL:[6,3],SE:[7,3],PR:[2,4],SP:[3,4],MG:[4,4],ES:[5,4],SC:[2,5],RJ:[4,5],RS:[2,6]};
const CNT={RJ:4,SP:3,DF:2,MG:2,PR:1,RS:1,BA:1};
const ATAS=[
 {n:'00012/2026',it:'1',u:'UNIDADE EXEMPLO RJ-A',uasg:'000001',f:'FORNECEDOR EXEMPLO 1 LTDA',c:'90005/2026',v:'15/03/2027',sa:'480 de 600 (20% já usado)',mx:'300',qr:'600',ac:true,sc:'✅ SICAF: Ativo e habilitado a licitar'},
 {n:'00012/2026',it:'3',u:'UNIDADE EXEMPLO RJ-A',uasg:'000001',f:'FORNECEDOR EXEMPLO 1 LTDA',c:'90005/2026',v:'15/03/2027',sa:'200 de 400 (50% já usado)',mx:'100',qr:'200',ac:true,sc:'✅ SICAF: Ativo e habilitado a licitar'},
 {n:'00021/2025',it:'2',u:'UNIDADE EXEMPLO RJ-C',uasg:'000003',f:'FORNECEDOR EXEMPLO 3 LTDA',c:'90019/2025',v:'10/12/2026',sa:'N/I',mx:'N/I',qr:'150',ac:false,sc:'⚠️ SICAF: Ativo, não habilitado a licitar'},
 {n:'00003/2026',it:'1',u:'UNIDADE EXEMPLO RJ-D',uasg:'000004',f:'FORNECEDOR EXEMPLO 4 LTDA',c:'90001/2026',v:'05/05/2027',sa:'800 de 1.500 (47% já usado)',mx:'375',qr:'750',ac:true,sc:'✅ SICAF: Ativo e habilitado a licitar'}
];
let S;
function resetS(){S={tipo:'',dd:false,q:'',fb:false,fdd:false,fam:'',fed:true,spin:false,res:false,uf:null,docs:false,aprov:false,cesta:0,q1:'',q2:'',van:false,bab:false};}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('a-tipo-v',S.tipo);$('#a-tipo-ph').style.display=S.tipo?'none':'inline';$('#a-dd').classList.toggle('on',S.dd);
  $('#a-s1').classList.toggle('on',!!S.tipo);T('a-q-v',S.q);$('#a-q-ph').style.display=S.q?'none':'inline';
  $('#a-fb').classList.toggle('on',S.fb);T('a-fam-v',S.fam);$('#a-fdd').classList.toggle('on',S.fdd);
  T('a-fclass',S.fam?'Classe: PAPÉIS PARA ESCRITÓRIO — papel sulfite A4 75 g/m²':'');
  $('#a-spin').classList.toggle('on',S.spin);$('#a-res').classList.toggle('on',S.res);
  $('#a-buscar').style.opacity=S.fam?1:.5;
  if(!S.res)return;
  $('#a-mapbox').classList.toggle('off',!!S.uf);$('#a-list').classList.toggle('on',!!S.uf);
  $('#a-map').innerHTML=Object.keys(UFS).map(u=>{const c=CNT[u]||0,k=c>=4?4:c>=3?3:c>=2?2:c>=1?1:0;return '<div class="tile t'+k+'" id="u-'+u+'" style="left:'+(UFS[u][0]*62)+'px;top:'+(UFS[u][1]*44)+'px">'+u+'<small>'+(c||'')+'</small></div>';}).join('');
  $('#a-cards').innerHTML=ATAS.map((x,i)=>'<div class="ata" id="a-card'+(i+1)+'"><b class="t">Ata '+x.n+' • '+x.u+' (UASG '+x.uasg+')</b><span class="lk">Visualizar documento – '+x.f+'</span><div><span class="tag">🔢 Item: '+x.it+'</span><span class="tag">🛒 Compra: '+x.c+'</span><span class="tag">📅 Vigência Final: '+x.v+'</span><span class="tag" id="sa'+(i+1)+'">📦 Saldo para adesão: '+x.sa+'</span><span class="tag" id="mx'+(i+1)+'">🏛️ Máx. por órgão aderente: '+x.mx+'</span><span class="tag">📋 Qtd. registrada: '+x.qr+'</span><span class="tag" id="ac'+(i+1)+'">🤝 Aceita Adesão: '+(x.ac?'✅ Sim':'❌ Não')+'</span><span class="tag" id="sc'+(i+1)+'">'+x.sc+'</span></div><div class="bts"><div class="btn" id="a-docs'+(i+1)+'">📂 Outros Docs</div><div class="btn" id="a-apr'+(i+1)+'">📋 Adesões já aprovadas</div><div class="btn" id="a-inc'+(i+1)+'">🛒 Incluir na adesão</div></div><div class="docs'+(i===0&&S.docs?' on':'')+'" id="a-pills'+(i+1)+'"><span class="pill">📎 Edital do pregão <small>Edital</small></span><span class="pill">📎 Termo de homologação <small>Homologação</small></span></div><div class="aprov'+(i===0&&S.aprov?' on':'')+'" id="a-aprov'+(i+1)+'"><table class="tb"><tr><th>Órgão que aderiu</th><th>Quantidade aprovada</th><th>Aprovada em</th></tr><tr><td>UNIDADE EXEMPLO SP</td><td>120</td><td>12/06/2026</td></tr></table></div></div>').join('');
  $('#a-cesta').classList.toggle('on',S.cesta>0);$('#a-r2').style.display=S.cesta>1?'':'none';
  T('a-q1',S.q1);T('a-q2',S.q2);$('#a-van').classList.toggle('on',S.van);$('#a-bab').classList.toggle('on',S.bab);
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Adesões',
 b:'A página <b>Adesões</b> procura <b>atas de registro de preços</b> vigentes no Compras.gov.br em que um órgão que <b>não participou</b> da licitação pode pedir <b>adesão</b> (a chamada “carona”). Você escolhe o item, o sistema encontra as atas e mostra <b>onde estão</b>, <b>quanto resta de saldo</b> e <b>se aceitam adesão</b>. Depois você <b>monta a adesão</b>: escolhe os itens, informa as quantidades, confere a <b>vantajosidade</b> e gera o <b>ofício</b> no Babilaca.',
 tip:'💡 A adesão a ata de registro de preços tem regras e limites na Lei nº 14.133/2021 (art. 86): esta página ajuda a cumpri-los.',
 run:async a=>{a.unring();await a.top();a.ring('#a-head','Atas para adesão');await a.sleep(3000);a.unring();}},

{short:'Tipo',t:'Passo 1 — Escolha o tipo de item',
 b:'Em <b>Tipo de item</b>, escolha <b>Material</b> ou <b>Serviço</b>. Ao escolher, aparece o campo de pesquisa do catálogo oficial correspondente (CATMAT para materiais; CATSERV para serviços).',
 tip:'💡 Se estiver em dúvida entre os dois, pense no que é entregue: bem (material) ou atividade (serviço).',
 run:async a=>{a.unring();await a.top();await a.click('#a-tipo',()=>a.set(S=>S.dd=true));await a.click('#a-o-mat',()=>a.set(S=>{S.tipo='Material';S.dd=false;}));a.ring('#a-tipo','Material',4);await a.sleep(1500);a.unring();}},

{short:'Pesquisar',t:'Passo 2 — Pesquise o item',
 b:'Em <b>Pesquisar material</b>, digite o <b>nome</b>, uma <b>descrição</b> (ex.: “resma de papel a4”) ou o <b>código</b> CATMAT/PDM. O sistema procura as <b>famílias de material</b> (PDM) mais parecidas, já informando <b>quantas atas vigentes</b> cada uma tem e a <b>% de semelhança</b>.',
 tip:'💡 A busca de atas é feita pela <b>família</b> do item (PDM), não por um único código.',
 run:async a=>{a.unring();await a.scroll('#a-q',110);await a.click('#a-q');await a.type('#a-q-v','resma de papel a4',90);a.set(S=>{S.q='resma de papel a4';S.fb=true;});await a.sleep(800);a.ring('#a-fb','Famílias encontradas',4);await a.sleep(2200);a.unring();}},

{short:'Família',t:'Passo 3 — Escolha a família',
 b:'Abra a lista <b>Famílias de material encontradas</b> e escolha a que mais se parece com o que você quer. Cada opção mostra o <b>nome</b>, o <b>código PDM</b>, o <b>número de atas vigentes</b> e a <b>semelhança</b>. A caixa <b>“Mostrar apenas famílias com atas vigentes”</b> esconde as famílias sem atas.',
 tip:'💡 Escolha a família com boa semelhança <b>e</b> com atas vigentes. A linha “Classe” abaixo confirma o tipo de item.',
 run:async a=>{a.unring();await a.scroll('#a-fam',150);a.ring('#a-cb1','Só famílias com atas',4);await a.sleep(1600);a.unring();await a.click('#a-fam',()=>a.set(S=>S.fdd=true));await a.click('#a-f1',()=>a.set(S=>{S.fam='PAPEL SULFITE · PDM 8710 · 14 atas vigentes · 92%';S.fdd=false;}));await a.sleep(1000);}},

{short:'Esfera',t:'Passo 4 — Esfera federal',
 b:'Com a família escolhida, aparece <b>Buscar somente atas da esfera federal</b>, já marcada. Mantenha marcada para ver só atas de órgãos <b>federais</b>; desmarque para incluir também atas de <b>estados e municípios</b>.',
 tip:'💡 Cada esfera tem suas próprias regras de adesão: confirme se o seu órgão pode aderir a ata de outra esfera.',
 run:async a=>{a.unring();await a.scroll('#a-cb2',170);a.ring('#a-cb2','Esfera federal',4);await a.sleep(3000);a.unring();}},

{short:'Buscar',t:'Passo 5 — Clique em Buscar adesões',
 b:'Clique em <b>Buscar adesões</b>. O botão só funciona depois que uma família é escolhida. O sistema consulta o Compras.gov.br e mostra o <b>total de atas encontradas</b> e o <b>mapa do Brasil</b>, em que cada estado é colorido pela <b>quantidade de atas</b> (mais escuro = mais atas) e traz o número.',
 tip:'💡 Passe o mouse sobre um estado para ver nome, sigla e quantidade de atas.',
 run:async a=>{a.unring();await a.scroll('#a-buscar',220);await a.click('#a-buscar',()=>a.set(S=>S.spin=true));await a.sleep(1700);a.set(S=>{S.spin=false;S.res=true;});
  await a.scroll('#a-total',60);a.ring('#a-total','Total de atas');await a.sleep(1800);a.unring();a.ring('#a-map','Mapa por estado');await a.sleep(2800);a.unring();}},

{short:'Estado',t:'Passo 6 — Clique no estado',
 b:'Clique no <b>estado</b> onde você quer achar atas. Aqui escolhemos o <b>RJ</b>. A tela passa para a <b>lista de atas do estado</b>, com a contagem. Para voltar ao mapa, use <b>Limpar filtro de estado</b>.',
 tip:'💡 Priorize atas de órgãos mais próximos do seu: facilita a logística de entrega.',
 run:async a=>{a.unring();await a.scroll('#a-map',60);await a.click('#u-RJ',()=>a.set(S=>S.uf='RJ'));await a.sleep(500);await a.scroll('#a-cards',150);a.ring('#a-limpar','Voltar ao mapa');await a.sleep(1800);a.unring();}},

{short:'Ler a ata',t:'Passo 7 — Leia os dados de cada ata',
 b:'Cada cartão mostra o <b>número da ata</b>, o <b>órgão gerenciador</b> (e a UASG), o <b>fornecedor</b> (clique para ver o documento da ata) e as etiquetas: <b>vigência final</b>; <b>saldo para adesão</b>, com quanto já foi usado; <b>máximo por órgão aderente</b>, que é a metade da quantidade registrada; <b>Aceita Adesão</b>; e a situação do fornecedor no <b>SICAF</b>.',
 tip:'💡 “Aceita Adesão: ❌ Não” significa que a ata não admite carona — descarte-a. Confira também se o fornecedor está ativo e habilitado no SICAF.',
 run:async a=>{a.unring();await a.scroll('#a-cards',110);a.ring('#sa1','Saldo para adesão',4);await a.sleep(2200);a.unring();a.ring('#mx1','Máximo por órgão',4);await a.sleep(2200);a.unring();await a.scroll('#ac3',230);a.ring('#ac3','Não aceita adesão',4);await a.sleep(2400);a.unring();}},

{short:'Documentos',t:'Passo 8 — Documentos e adesões já aprovadas',
 b:'Clique em <b>📂 Outros Docs</b> para listar os <b>documentos da ata e da compra</b> (edital, termo de homologação) e conferir objeto e especificações. Em <b>📋 Adesões já aprovadas</b> você vê <b>quais órgãos já aderiram</b> ao item e em que quantidade.',
 tip:'💡 Muitas adesões já aprovadas consomem o saldo: confira antes de pedir.',
 run:async a=>{a.unring();await a.scroll('#a-docs1',120);await a.click('#a-docs1',()=>a.set(S=>S.docs=true));a.ring('#a-pills1','Documentos da ata',4);await a.sleep(2400);a.unring();await a.click('#a-apr1',()=>a.set(S=>S.aprov=true));a.ring('#a-aprov1','Adesões aprovadas',4);await a.sleep(2600);a.unring();}},

{short:'Incluir',t:'Passo 9 — Inclua os itens na adesão',
 b:'Em cada item que você quer, clique em <b>🛒 Incluir na adesão</b>. Pode ser <b>um item</b> ou <b>vários</b>. Os itens aparecem no quadro <b>Itens escolhidos para adesão</b>, <b>agrupados por ata</b>: itens da mesma ata vão no <b>mesmo ofício</b>; itens de atas diferentes geram <b>ofícios separados</b>, um para cada órgão gerenciador.',
 tip:'💡 Aqui incluímos os itens 1 e 3 da mesma ata: os dois irão juntos num só ofício.',
 run:async a=>{a.unring();await a.scroll('#a-inc1',140);await a.click('#a-inc1',()=>a.set(S=>S.cesta=1));a.toast('Item 1 incluído na adesão à Ata 00012/2026.');await a.sleep(1200);await a.scroll('#a-inc2',140);await a.click('#a-inc2',()=>a.set(S=>S.cesta=2));a.toast('Item 3 incluído na adesão à Ata 00012/2026.');await a.sleep(1200);await a.scroll('#a-cbox',80);a.ring('#a-cbox','Um bloco por ata',4);await a.sleep(2400);a.unring();}},

{short:'Quantidade',t:'Passo 10 — Informe a quantidade de cada item',
 b:'Na tabela da ata, preencha a coluna <b>Quantidade pretendida</b> de cada item. Ao lado está o <b>máximo por órgão</b>: se você passar dele, o sistema avisa (art. 86, §4º). Para tirar um item, desmarque <b>Incluir</b>.',
 tip:'💡 Se ainda não souber a quantidade, você pode completá-la depois, no ofício do Babilaca.',
 run:async a=>{a.unring();await a.scroll('#a-cbox',80);await a.click('#a-q1');await a.type('#a-q1','100',140);a.set(S=>S.q1='100');await a.click('#a-q2');await a.type('#a-q2','50',140);a.set(S=>S.q2='50');a.ring('#a-m1','Limite por órgão',4);await a.sleep(2200);a.unring();}},

{short:'Vantajosidade',t:'Passo 11 — Analise a vantajosidade',
 b:'Clique em <b>📊 Analisar vantajosidade</b>. Para cada item, o sistema busca o <b>mesmo código do catálogo</b> em <b>outras atas dos últimos 12 meses</b> (e, se você marcar a opção, em compras homologadas), descarta preços muito fora da curva e compara o <b>preço da ata</b> com a <b>mediana de mercado</b>. Mostra a <b>diferença</b>, a <b>economia</b> na quantidade pedida e o <b>total</b> da adesão.',
 tip:'💡 Item 🔴 acima do mercado deve sair da adesão ou ter a vantagem justificada por outro motivo, como urgência ou risco de desabastecimento.',
 run:async a=>{a.unring();await a.scroll('#a-anl',150);await a.click('#a-anl',()=>a.set(S=>S.spin=true));await a.sleep(1500);a.set(S=>{S.spin=false;S.van=true;});await a.scroll('#a-van',60);a.ring('#a-van','Ata × mercado',4);await a.sleep(2400);a.unring();a.ring('#a-okm','Economia total',4);await a.sleep(2400);a.unring();}},

{short:'Ofício',t:'Passo 12 — Gere o ofício no Babilaca',
 b:'Clique em <b>✉️ Gerar ofício no Babilaca</b>. O Babilaca abre na aba <b>Documentos</b> com o <b>ofício de adesão</b> já preenchido: ata, órgão gerenciador, UASG, itens e quantidades, e a <b>justificativa com os números</b> da vantajosidade. O <b>relatório de vantajosidade</b> vai pronto, como anexo, e também entra no <b>Kit do processo</b>.',
 tip:'🎉 Fim da aula! <b>Resumo:</b> 1) tipo; 2) pesquise; 3) família; 4) esfera; 5) Buscar adesões; 6) estado; 7) leia a ata; 8) documentos e adesões aprovadas; 9) inclua os itens; 10) quantidades; 11) vantajosidade; 12) gere o ofício, revise, assine e envie ao órgão gerenciador.',
 run:async a=>{a.unring();await a.scroll('#a-gof',150);await a.click('#a-gof',()=>a.set(S=>S.bab=true));a.toast('Abrindo o Babilaca com o ofício preenchido…');await a.sleep(900);await a.scroll('#a-babdoc',60);a.ring('#a-babdoc','Ofício pronto para revisar',4);await a.sleep(3200);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="adesoes")
