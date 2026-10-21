"""Vídeo-aula simulado: como usar a página Adesões (atas de registro de preços para adesão/“carona”)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a página Adesões"
DESCRICAO = (
    "Achar atas de registro de preços para adesão: tipo de item, família do catálogo, esfera federal, mapa por estado, "
    "dados de cada ata e documentos. Duração aproximada: 3 min, com narração."
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
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const UFS={RR:[2,0],AP:[4,0],AM:[1,1],PA:[3,1],MA:[4,1],CE:[5,1],RN:[6,1],AC:[0,2],RO:[1,2],MT:[2,2],TO:[3,2],PI:[4,2],PE:[5,2],PB:[6,2],MS:[2,3],GO:[3,3],DF:[4,3],BA:[5,3],AL:[6,3],SE:[7,3],PR:[2,4],SP:[3,4],MG:[4,4],ES:[5,4],SC:[2,5],RJ:[4,5],RS:[2,6]};
const CNT={RJ:4,SP:3,DF:2,MG:2,PR:1,RS:1,BA:1};
const ATAS=[
 {n:'00012/2026',u:'UNIDADE EXEMPLO RJ-A',uasg:'000001',f:'FORNECEDOR EXEMPLO 1 LTDA',c:'00005/2026',v:'15/03/2027',sa:'120',sr:'0',la:'600',lc:'1200',ac:true},
 {n:'00008/2026',u:'UNIDADE EXEMPLO RJ-B',uasg:'000002',f:'FORNECEDOR EXEMPLO 2 LTDA',c:'00003/2026',v:'30/11/2026',sa:'0',sr:'40',la:'300',lc:'600',ac:true},
 {n:'00021/2025',u:'UNIDADE EXEMPLO RJ-C',uasg:'000003',f:'FORNECEDOR EXEMPLO 3 LTDA',c:'00019/2025',v:'10/12/2026',sa:'N/I',sr:'N/I',la:'N/I',lc:'N/I',ac:false},
 {n:'00003/2026',u:'UNIDADE EXEMPLO RJ-D',uasg:'000004',f:'FORNECEDOR EXEMPLO 4 LTDA',c:'00001/2026',v:'05/05/2027',sa:'800',sr:'0',la:'1500',lc:'3000',ac:true}
];
let S;
function resetS(){S={tipo:'',dd:false,q:'',fb:false,fdd:false,fam:'',fed:true,spin:false,res:false,uf:null,docs:false};}
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
  $('#a-cards').innerHTML=ATAS.map((x,i)=>'<div class="ata"><b class="t">Ata '+x.n+' • '+x.u+' (UASG '+x.uasg+')</b><span class="lk">Visualizar documento – '+x.f+'</span><div><span class="tag">🔢 Item: 1</span><span class="tag">🛒 Compra: '+x.c+'</span><span class="tag">📅 Vigência Final: '+x.v+'</span><span class="tag">📦 Saldo Adesões: '+x.sa+'</span><span class="tag">🔄 Saldo Remanej.: '+x.sr+'</span><span class="tag">📊 Lim. Adesão: '+x.la+'</span><span class="tag">🛒 Lim. Compra: '+x.lc+'</span><span class="tag" id="ac'+(i+1)+'">🤝 Aceita Adesão: '+(x.ac?'✅ Sim':'❌ Não')+'</span></div><div class="btn" id="a-docs'+(i+1)+'" style="width:130px;margin-top:6px;padding:5px">📂 Outros Docs</div><div class="docs'+(i===0&&S.docs?' on':'')+'" id="a-pills'+(i+1)+'"><span class="pill">📎 Edital do pregão <small>Edital</small></span><span class="pill">📎 Termo de homologação <small>Homologação</small></span></div></div>').join('');
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Adesões',
 b:'A página <b>Adesões</b> procura <b>atas de registro de preços</b> vigentes no Compras.gov.br em que um órgão que <b>não participou</b> da licitação pode pedir <b>adesão</b> (a chamada “carona”). Você escolhe o item, o sistema encontra as atas e mostra <b>onde estão</b>, <b>quanto resta de saldo</b> e <b>se aceitam adesão</b>.',
 tip:'💡 A adesão a ata de registro de preços tem regras e limites na Lei nº 14.133/2021 (art. 86) e no regulamento aplicável: confira-os antes de aderir.',
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
 b:'Cada cartão mostra <b>número da ata</b>, <b>órgão gerenciador</b> (e UASG), o <b>fornecedor</b> (clique para ver o documento da ata) e as etiquetas: <b>vigência final</b>, <b>saldo de adesões</b>, <b>saldo de remanejamento</b>, <b>limite de adesão</b>, <b>limite de compra</b> e <b>Aceita Adesão</b>. Prefira atas <b>vigentes</b>, com <b>saldo</b> e que <b>aceitem adesão</b>.',
 tip:'💡 “Aceita Adesão: ❌ Não” significa que a ata não admite carona — descarte-a. Saldo 0 ou vigência perto do fim também pedem cuidado.',
 run:async a=>{a.unring();await a.scroll('#a-cards',110);a.ring('#a-cards','Dados de cada ata',4);await a.sleep(2400);a.unring();await a.scroll('#ac3',230);a.ring('#ac3','Não aceita adesão',4);await a.sleep(2800);a.unring();}},

{short:'Documentos',t:'Passo 8 — Veja os outros documentos',
 b:'Clique em <b>📂 Outros Docs</b> para listar os <b>documentos da ata e da compra</b> (edital, termo de homologação etc.) como links. Use-os para conferir <b>objeto, condições e especificações</b> antes de pedir a adesão.',
 tip:'🎉 Fim da aula! <b>Resumo:</b> 1) tipo; 2) pesquise; 3) escolha a família; 4) esfera; 5) Buscar adesões; 6) estado; 7) leia a ata; 8) confira os documentos e <b>contate o órgão gerenciador</b> para formalizar a adesão.',
 run:async a=>{a.unring();await a.scroll('#a-docs1',120);await a.click('#a-docs1',()=>a.set(S=>S.docs=true));a.ring('#a-pills1','Documentos da ata',4);await a.sleep(3200);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="adesoes")
