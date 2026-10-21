"""Vídeo-aula simulado: como usar a página Fornecedores (Banco de Fornecedores por CNAE)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar o Banco de Fornecedores"
DESCRICAO = (
    "Encontrar fornecedores do Compras.gov.br por atividade econômica (CNAE), filtrar, buscar e-mail e telefone "
    "e exportar. Duração aproximada: 2 min."
)

_MOCK_CSS = r"""
.rc{background:rgba(8,26,57,.78);border:1px solid #1e5b9f;border-radius:9px;padding:9px 12px;margin:7px 0;font-size:11px}
.rc .n{font-weight:700;font-size:12.5px;color:#fff;display:flex;justify-content:space-between;gap:8px}
.rc .i{display:flex;flex-wrap:wrap;gap:3px 14px;margin-top:5px;color:#cbd5e1}
.ta2{background:#14532d;color:#bbf7d0;border-radius:5px;padding:1px 7px;font-size:10px;font-weight:700}
.th{background:#1e3a8a;color:#bfdbfe;border-radius:5px;padding:1px 7px;font-size:10px;font-weight:700}
.cntb{background:linear-gradient(135deg,#0a2540,#164863);border-left:5px solid var(--gold);border-radius:8px;text-align:center;padding:10px;margin:10px 0}
.cntb .v{color:var(--gold);font-size:30px;font-weight:800}.cntb .k{color:#cbd5e1;font-size:12px}.cntb .s{color:#94a3b8;font-size:10.5px;margin-top:2px}
#f-res{display:none}#f-res.on{display:block}
.fld .t{color:#fff}
.dd.long{max-height:120px;overflow:hidden}
.ok2{color:#86efac;font-size:12px;margin:6px 0}
"""

_STAGE_HTML = r"""
<div class="hdr" id="f-head"><div class="l">⚓ MARINHA DO BRASIL ⚓</div><div class="s">AtaCotada</div><div class="u">BANCO DE FORNECEDORES</div></div>
<div class="cap2" style="margin-top:10px">Consulta fornecedores registrados no Compras.gov.br por atividade econômica (CNAE). Digite o nome da atividade econômica (CNAE) para encontrar fornecedores habilitados.</div>
<div class="lbl">Atividade Econômica (CNAE)</div>
<div class="fld sel" id="f-cnae"><span id="f-cnae-v"></span><span class="ph" id="f-cnae-ph">Digite para filtrar pelo nome do CNAE…</span>
  <div class="dd" id="f-dd"><div class="h" id="f-o1">Comércio Varejista De Artigos De Papelaria (4761-0/03)</div><div>Comércio Atacadista De Artigos De Papelaria (4647-8/01)</div></div></div>
<div class="ck" id="f-cb" style="display:none"><span class="box on" style="background:#ef4444;border-color:#ef4444">✓</span><span>Buscar somente fornecedores ativos</span></div>
<div class="btn pri" id="f-busca" style="margin-top:10px;opacity:.5">Buscar fornecedores</div>
<div class="spin" id="f-spin"><i></i><span>Consultando fornecedores, aguarde…</span></div>

<div id="f-res">
  <div class="cntb" id="f-cnt"><div class="v" id="f-n">0</div><div class="k">fornecedores encontrados</div><div class="s">Comércio Varejista De Artigos De Papelaria (4761-0/03)</div></div>
  <div class="lbl">🔍 Filtrar resultados por nome do fornecedor, município ou UF</div>
  <div class="fld" id="f-filt"><span id="f-filt-v"></span><span class="ph" id="f-filt-ph">Ex: São Paulo, ME, equipamentos…</span></div>
  <div class="cntb" id="f-cnt2" style="display:none;padding:6px"><div class="v" style="font-size:22px" id="f-n2">0</div><div class="k">fornecedores após filtro</div></div>
  <div class="btn pri" id="f-contatos" style="margin-top:10px">☎️ Buscar e-mail e telefone dos fornecedores</div>
  <div class="prog" id="f-prog"><div class="t" id="f-prog-t"></div><div class="b"><i id="f-prog-b"></i></div></div>
  <div class="ok2" id="f-okc"></div>
  <div id="f-cards"></div>
  <div class="two" style="margin-top:10px"><div class="btn" id="f-xls">📥 Exportar planilha Excel</div><div class="btn" id="f-pdf">📄 Exportar relatório PDF</div></div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const FOR=[
 {n:'PAPELARIA EXEMPLO RIO LTDA',c:'00.000.000/0001-01',m:'Rio de Janeiro',uf:'RJ',p:'Microempresa',nj:'Sociedade Empresária Limitada',h:true,e:'contato@papelaria-exemplo-rio.example',t:'(21) 0000-0001'},
 {n:'COMERCIAL EXEMPLO SÃO PAULO ME',c:'00.000.000/0001-02',m:'São Paulo',uf:'SP',p:'Microempresa',nj:'Empresário Individual',h:true,e:'vendas@comercial-exemplo.example',t:'(11) 0000-0002'},
 {n:'DISTRIBUIDORA EXEMPLO NITERÓI EIRELI',c:'00.000.000/0001-03',m:'Niterói',uf:'RJ',p:'Empresa de Pequeno Porte',nj:'Sociedade Empresária Limitada',h:true,e:'',t:''},
 {n:'SUPRIMENTOS EXEMPLO BRASÍLIA LTDA',c:'00.000.000/0001-04',m:'Brasília',uf:'DF',p:'Demais',nj:'Sociedade Empresária Limitada',h:false,e:'',t:''}
];
let S;
function resetS(){S={cnae:false,dd:false,sel:false,spin:false,res:false,filt:'',cont:0,prog:0};}
function lista(){const f=S.filt.toLowerCase();return FOR.filter(x=>!f||(x.n+x.m+x.uf).toLowerCase().includes(f));}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('f-cnae-v',S.sel?'Comércio Varejista De Artigos De Papelaria (4761-0/03)':'');$('#f-cnae-ph').style.display=S.sel||S.cnae?'none':'inline';
  T('f-cnae-v',S.sel?'Comércio Varejista De Artigos De Papelaria (4761-0/03)':S.cnae?'papelaria':'');
  $('#f-dd').classList.toggle('on',S.dd);$('#f-cb').style.display=S.sel?'flex':'none';$('#f-busca').style.opacity=S.sel?1:.5;
  $('#f-spin').classList.toggle('on',S.spin);$('#f-res').classList.toggle('on',S.res);
  T('f-filt-v',S.filt);$('#f-filt-ph').style.display=S.filt?'none':'inline';
  if(!S.res)return;
  T('f-n',String(FOR.length));const L=lista();$('#f-cnt2').style.display=S.filt?'block':'none';T('f-n2',S.filt?String(L.length):'');
  $('#f-prog').classList.toggle('on',S.cont===1);T('f-prog-t','Buscando contatos… '+S.prog+'/'+L.length);$('#f-prog-b').style.width=(L.length?S.prog/L.length*100:0)+'%';
  T('f-okc',S.cont===2?'✅ Contatos carregados para '+L.length+' fornecedor(es).':'');
  $('#f-contatos').style.display=S.cont===2?'none':'block';
  $('#f-cards').innerHTML=L.map(x=>'<div class="rc"><div class="n"><span>'+x.n+'</span><span><span class="ta2">Ativo</span> <span class="'+(x.h?'th':'ta2')+'">'+(x.h?'Habilitado a licitar':'Não habilitado')+'</span></span></div><div class="i"><span>📄 <b>CNPJ:</b> '+x.c+'</span><span>📍 <b>Município:</b> '+x.m+' – '+x.uf+'</span><span>🏢 <b>Porte:</b> '+x.p+'</span><span>⚖️ <b>Natureza Jurídica:</b> '+x.nj+'</span>'+(S.cont===2&&x.e?'<span>📧 <b>E-mail:</b> '+x.e+'</span>':'')+(S.cont===2&&x.t?'<span>📞 <b>Telefone:</b> '+x.t+'</span>':'')+'</div></div>').join('');
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Fornecedores',
 b:'A página <b>Fornecedores</b> consulta o cadastro de fornecedores do <b>Compras.gov.br</b> por <b>atividade econômica (CNAE)</b>. Serve para descobrir <b>quem pode fornecer</b> determinado tipo de material ou serviço, com CNPJ, município, porte e situação — e, se quiser, <b>e-mail e telefone</b>.',
 tip:'💡 Ótima para montar a lista de empresas a convidar em uma <b>cotação direta</b>.',
 run:async a=>{a.unring();await a.top();a.ring('#f-head','Banco de Fornecedores');await a.sleep(2800);a.unring();}},

{short:'CNAE',t:'Passo 1 — Escolha a atividade econômica (CNAE)',
 b:'No campo <b>Atividade Econômica (CNAE)</b>, <b>digite parte do nome</b> da atividade (ex.: “papelaria”). A lista é filtrada na hora, entre as <b>1.332 subclasses</b> do CNAE (IBGE/CONCLA). Clique na atividade desejada.',
 tip:'💡 Se não souber o CNAE do que procura, pense na atividade da empresa que vende o item (ex.: papelaria, material de limpeza, informática).',
 run:async a=>{a.unring();await a.scroll('#f-cnae',100);await a.click('#f-cnae',()=>a.set(S=>{S.cnae=true;S.dd=true;}));await a.type('#f-cnae-v','papelaria',110);a.set(S=>S.dd=true);await a.sleep(500);
  await a.click('#f-o1',()=>a.set(S=>{S.sel=true;S.dd=false;}));a.ring('#f-cnae','CNAE escolhido');await a.sleep(1800);a.unring();}},

{short:'Buscar',t:'Passo 2 — Busque os fornecedores',
 b:'Deixe marcada a opção <b>Buscar somente fornecedores ativos</b> e clique em <b>Buscar fornecedores</b>. O botão só fica ativo depois de escolher um CNAE. Ao terminar, aparece o <b>total de fornecedores encontrados</b>.',
 tip:'💡 Atividades muito comuns podem ter centenas de fornecedores: use o filtro do próximo passo.',
 run:async a=>{a.unring();a.ring('#f-cb','Somente ativos');await a.sleep(1500);a.unring();await a.click('#f-busca',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.res=true;});
  await a.scroll('#f-cnt',70);a.ring('#f-cnt','Total encontrado');await a.sleep(2200);a.unring();}},

{short:'Filtrar',t:'Passo 3 — Filtre os resultados',
 b:'Use o campo <b>Filtrar resultados</b> para refinar por <b>nome do fornecedor, município, UF, CNPJ, porte ou natureza jurídica</b>. Aqui digitamos <b>RJ</b>: a lista cai para os fornecedores do Rio de Janeiro e o contador mostra quantos restaram.',
 tip:'💡 Para pedir cotação a empresas próximas, filtre pela sua UF ou município.',
 run:async a=>{a.unring();await a.scroll('#f-filt',120);await a.click('#f-filt');await a.type('#f-filt-v','RJ',200);a.set(S=>S.filt='RJ');a.ring('#f-cnt2','Fornecedores após o filtro');await a.sleep(2600);a.unring();}},

{short:'Contatos',t:'Passo 4 — Busque e-mail e telefone',
 b:'Clique em <b>☎️ Buscar e-mail e telefone dos fornecedores</b>. O sistema consulta o <b>cadastro de cada CNPJ</b> em fontes públicas e mostra uma barra de progresso. Ao terminar, os cartões ganham <b>📧 e-mail</b> e <b>📞 telefone</b> — quando a empresa os tem cadastrados.',
 tip:'💡 Nem toda empresa tem contato cadastrado. Confirme os dados antes de enviar o pedido de cotação.',
 run:async a=>{a.unring();await a.scroll('#f-contatos',120);await a.click('#f-contatos',()=>a.set(S=>{S.cont=1;S.prog=0;}));
  for(const n of [1,2]){a.set(S=>S.prog=n);await a.sleep(900);}a.set(S=>S.cont=2);await a.sleep(700);await a.scroll('#f-okc',80);a.ring('#f-cards','Contatos carregados');await a.sleep(2800);a.unring();}},

{short:'Ler cartões',t:'Passo 5 — Leia os cartões dos fornecedores',
 b:'Cada cartão mostra a <b>razão social</b>, as etiquetas <b>Ativo</b> e <b>Habilitado a licitar</b>, o <b>CNPJ</b>, o <b>município/UF</b>, o <b>porte</b> (ME, EPP…) e a <b>natureza jurídica</b>, além do contato. Prefira fornecedores <b>ativos</b> e <b>habilitados a licitar</b>.',
 tip:'💡 Porte e natureza jurídica ajudam a verificar tratamento diferenciado para ME/EPP quando for o caso.',
 run:async a=>{a.unring();await a.scroll('#f-cards',60);a.ring('#f-cards','Cartões dos fornecedores');await a.sleep(3600);a.unring();}},

{short:'Exportar',t:'Passo 6 — Exporte a lista',
 b:'Para levar a lista com você, use <b>📥 Exportar planilha Excel</b> (colunas: razão social, CNPJ, município, UF, porte, natureza jurídica, e-mail, telefone, ativo e habilitado) ou <b>📄 Exportar relatório PDF</b>. <b>Resumo:</b> 1) escolha o CNAE; 2) busque; 3) filtre; 4) busque contatos; 5) exporte.',
 tip:'🎉 Fim da aula! Os dados desta aula são fictícios. Na ferramenta real, vêm do Compras.gov.br.',
 run:async a=>{a.unring();await a.scroll('#f-xls',250);a.ring('#f-xls','Excel');await a.click('#f-xls',()=>a.toast('✔ fornecedores_Comercio_Varejista.xlsx'));a.unring();a.ring('#f-pdf','PDF');await a.click('#f-pdf',()=>a.toast('✔ fornecedores_Comercio_Varejista.pdf'));await a.sleep(900);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS)
