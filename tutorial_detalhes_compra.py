"""Vídeo-aula simulado: como usar a página Detalhes Compra (contratos, ARPs, itens, documentos e deságio de uma UASG)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a página Detalhes Compra"
DESCRICAO = (
    "Consultar as compras de uma UASG: buscar a unidade pelo nome, filtrar, ler contratos e atas, ver itens, documentos e deságio, "
    "exportar em Excel e abrir o fornecedor na Consulta CNPJ. Duração aproximada: 4 min, com narração."
)

_MOCK_CSS = r"""
.exp{background:#0b2447;border:1px solid var(--line);border-radius:7px;margin-top:8px}
.exp .h{padding:8px 11px;font-size:12px;display:flex;gap:8px;align-items:center}.exp .h span{margin-left:auto;color:#9fb6d8}
.exp .b{display:none;padding:9px 11px;border-top:1px solid var(--line);font-size:11.5px;line-height:1.5}.exp .b.on{display:block}
.opt{padding:7px 10px;border:1px solid #2b6cb0;border-radius:7px;margin-top:5px;font-size:12px;background:rgba(7,20,42,.8)}
.opt.sel{background:#1d4ed8;border-color:#60a5fa}
.tg{display:inline-block;background:#ef4444;color:#fff;border-radius:6px;padding:3px 8px;font-weight:700;font-size:11.5px;margin:2px 4px 2px 0}
.mtr{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:6px}.mtr .k{font-size:11px;color:#b6cae2}.mtr .v{font-size:23px;font-weight:700}
.lk{color:#60a5fa;text-decoration:underline}
.docb{background:#0b2a63;border:1px solid #2b6cb0;border-radius:7px;padding:6px 10px;margin-top:5px;font-size:11.5px}
.vend{margin:3px 0 8px 12px;font-size:11.5px;color:#bbf7d0}
#d-res{display:none}#d-res.on{display:block}
.it{border-bottom:1px solid #123768;padding:6px 0}
.sbtn{display:inline-block;background:#1b2a47;border:1px solid #3b4d70;border-radius:8px;padding:6px 12px;font-weight:700;font-size:12px;margin:6px 8px 0 0}
"""

_STAGE_HTML = r"""
<div class="qh" id="d-head"><div class="qs">🔍</div><div><b>Detalhes da Compra</b><small>Contratos, atas de registro de preços, itens, documentos e links de uma UASG.</small></div></div>
<div class="tabs"><div class="on">🔍 Busca por UASG</div><div>🌐 Portal Contratos.gov</div></div>
<div class="panel"><h3>🔍 Consultar Detalhes de Compras</h3><p>Busca contratos, ARPs, documentos (TR, edital) e links no PNCP e no ComprasNet a partir do código UASG.</p></div>

<div class="exp" id="d-nm-box"><div class="h" id="d-nm-h">🔎 Não sei o código — buscar UASG pelo nome do órgão <span id="d-nm-s">▸</span></div>
  <div class="b" id="d-nm-b">
    <div class="lbl">Nome (ou parte do nome) do órgão/unidade</div>
    <div class="fld" id="d-nm"><span id="d-nm-v"></span><span class="ph">Ex: hospital naval, comando 1 distrito</span></div>
    <div id="d-nm-res" class="hid"><div class="opt" id="d-o1">999001 — HOSPITAL NAVAL EXEMPLO (RJ)</div><div class="opt">999002 — POLICLINICA NAVAL EXEMPLO (RJ)</div></div>
    <div class="sbtn" id="d-usar" style="display:none">Usar</div>
  </div>
</div>

<div class="frm" style="margin-top:10px">
  <div><div class="lbl">Código UASG</div><div class="fld" id="d-uasg"><span id="d-uasg-v"></span><span class="ph">Ex: 153050, 771300</span></div></div>
  <div><div class="lbl">Ano</div><div class="fld" id="d-ano"><span id="d-ano-v">2026</span></div></div>
  <div><div class="lbl">ID da Compra (opcional)</div><div class="fld" id="d-id"><span id="d-id-v"></span><span class="ph">Ex: 15305006000142026</span></div></div>
</div>

<div class="exp" id="d-fa-box"><div class="h" id="d-fa-h">🔧 Filtros Avançados <span id="d-fa-s">▸</span></div>
  <div class="b" id="d-fa-b">
    <div class="two">
      <div><div class="lbl">Modalidade / Tipo</div><div class="fld" id="d-mod"><span id="d-mod-v"></span><span class="ph">Deixe vazio para exibir todos</span></div></div>
      <div><div class="lbl">Objeto (palavra-chave)</div><div class="fld" id="d-obj"><span id="d-obj-v"></span><span class="ph">Ex: material de limpeza, notebook</span></div></div>
    </div>
    <div class="two" style="margin-top:8px">
      <div><div class="lbl">Fornecedor (nome ou CNPJ)</div><div class="fld"><span class="ph">Ex: Empresa XYZ ou 12345678000199</span></div></div>
      <div><div class="lbl">Número do Processo</div><div class="fld"><span class="ph">Ex: 63379.001234/2025</span></div></div>
    </div>
    <div class="two" style="margin-top:8px">
      <div><div class="lbl">Período — Data Inicial</div><div class="fld"><span class="ph">DD/MM/AAAA</span></div></div>
      <div><div class="lbl">Período — Data Final</div><div class="fld"><span class="ph">DD/MM/AAAA</span></div></div>
    </div>
  </div>
</div>

<div class="btn pri" id="d-go" style="margin-top:12px;padding:10px;font-size:13.5px">🔍 Consultar</div>
<div class="spin" id="d-spin"><i></i><span>Buscando contratos e atas de registro de preços no ComprasGov...</span></div>

<div id="d-res">
  <div class="mtr" id="d-met"><div><div class="k">Contratos</div><div class="v">4</div></div><div><div class="k">ARPs (SRP)</div><div class="v">6</div></div><div><div class="k">Total Registros</div><div class="v">10</div></div></div>
  <div class="sbtn" id="d-xls" style="margin:12px 8px 4px 0">📊 Exportar resultados (Excel)</div>
  <div class="tabs"><div class="on" id="d-t1">📋 Compras (4)</div><div id="d-t2">📜 ARPs (6)</div></div>
  <div id="d-compras">
    <div class="cap2">📋 Total: 4 compra(s) encontrada(s)</div>
    <div class="exp" id="d-cp"><div class="h" id="d-cp-h">📋 12/2025 — Pregão nº 90003/2025 — Aquisição de material de expediente — R$ 184.300,00 <span id="d-cp-s">▸</span></div>
      <div class="b" id="d-cp-b">
        <b>Contrato: 12/2025</b><br>
        <b>Licitação:</b> Pregão nº 90003/2025<br>
        <b>Fornecedor:</b> FORNECEDOR EXEMPLO LTDA (00394460000141)<br>
        <b>Objeto:</b> Aquisição de material de expediente<br>
        <b>Vigência:</b> 01/02/2025 a 01/02/2026 · <b>Valor Global:</b> R$ 184.300,00
        <div><div class="sbtn" id="d-forn">🏢 Consultar fornecedor</div></div>
        <div class="panel" style="margin:8px 0 4px" id="d-links"><h3 style="font-size:12.5px">🌐 Links Externos</h3><p><span class="lk">🔗 Abrir no ComprasNet</span> · <span class="lk">🔗 Abrir no PNCP</span></p></div>
        <div class="docb">📎 Edital do Pregão 90003/2025 <span class="tag">Edital</span></div>
        <div class="docb">📎 Termo de Referência <span class="tag">Termo de Referência</span></div>
        <div class="exp" id="d-it"><div class="h" id="d-it-h">📦 Itens da compra (2 itens) <span id="d-it-s">▸</span></div>
          <div class="b" id="d-it-b">
            <div class="mtr" id="d-des"><div><div class="k">Valor estimado</div><div class="v" style="font-size:17px">R$ 210.000,00</div></div><div><div class="k">Valor homologado</div><div class="v" style="font-size:17px">R$ 184.300,00</div></div><div><div class="k">Deságio</div><div class="v" style="font-size:17px">12,2%</div></div></div>
            <div class="it"><b>Item 1</b> — Papel sulfite A4, caixa com 10 resmas<div class="cap2" style="margin:2px 0">Qtd: 600 CX · Valor unit. est.: R$ 250,00</div>
              <div class="vend">↳ Vencedor: FORNECEDOR EXEMPLO LTDA (00394460000141) — Valor homologado: R$ 129.000,00 — deságio 14,0%</div></div>
            <div class="it"><b>Item 2</b> — Caneta esferográfica azul, caixa com 50<div class="cap2" style="margin:2px 0">Qtd: 900 CX · Valor unit. est.: R$ 66,67</div>
              <div class="vend">↳ Vencedor: FORNECEDOR EXEMPLO LTDA (00394460000141) — Valor homologado: R$ 55.300,00 — deságio 7,8%</div></div>
          </div></div>
      </div>
    </div>
    <div class="sbtn" id="d-mais">⬇️ Carregar mais compras</div>
  </div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
let S;
function resetS(){S={nm:false,q:'',res:false,sel:false,uasg:'',ano:'2026',id:'',fa:false,mod:'',obj:'',spin:false,out:false,cp:false,it:false};}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  const ph=(vid,val)=>{T(vid,val);const e=document.getElementById(vid);const p=e&&e.parentElement&&e.parentElement.querySelector('.ph');if(p)p.style.display=val?'none':'inline';};
  const tog=(id,on)=>$(id).classList.toggle('on',on);
  tog('#d-nm-b',S.nm);T('d-nm-s',S.nm?'▾':'▸');ph('d-nm-v',S.q);
  $('#d-nm-res').classList.toggle('on',S.res);$('#d-o1').classList.toggle('sel',S.sel);$('#d-usar').style.display=S.sel?'inline-block':'none';
  ph('d-uasg-v',S.uasg);T('d-ano-v',S.ano);ph('d-id-v',S.id);
  tog('#d-fa-b',S.fa);T('d-fa-s',S.fa?'▾':'▸');
  ph('d-mod-v',S.mod);ph('d-obj-v',S.obj);
  $('#d-spin').classList.toggle('on',S.spin);tog('#d-res',S.out);
  tog('#d-cp-b',S.cp);T('d-cp-s',S.cp?'▾':'▸');tog('#d-it-b',S.it);T('d-it-s',S.it?'▾':'▸');
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Detalhes Compra',
 b:'A página <b>Detalhes Compra</b> mostra tudo o que uma <b>UASG</b> comprou: <b>contratos</b>, <b>atas de registro de preços</b>, <b>itens</b>, <b>documentos</b> como edital e termo de referência, e os <b>links</b> para o ComprasNet e o PNCP. É a página certa para ver como uma compra foi feita e quem venceu.',
 tip:'💡 UASG é o código da unidade que comprou, com seis dígitos. Se você não sabe o código, o sistema procura pelo nome.',
 run:async a=>{a.unring();await a.top();a.ring('#d-head','Detalhes da Compra');await a.sleep(2800);a.unring();}},

{short:'UASG',t:'Passo 1 — Ache a UASG pelo nome',
 b:'Não sabe o código? Abra <b>Não sei o código</b> e digite <b>parte do nome</b> do órgão, sem se preocupar com acentos. O sistema lista as unidades encontradas. Escolha uma e clique em <b>Usar</b>: o código é preenchido para você.',
 tip:'💡 Digite poucas palavras, como hospital naval, para não excluir a unidade por engano.',
 run:async a=>{a.unring();await a.scroll('#d-nm-h',80);await a.click('#d-nm-h',()=>a.set(S=>S.nm=true));await a.click('#d-nm');await a.type('#d-nm-v','hospital naval',90);
  a.set(S=>{S.q='hospital naval';S.res=true;});await a.sleep(1200);await a.click('#d-o1',()=>a.set(S=>S.sel=true));await a.click('#d-usar',()=>a.set(S=>{S.uasg='999001';S.nm=false;S.res=false;S.sel=false;}));
  a.ring('#d-uasg','UASG preenchida',4);await a.sleep(2200);a.unring();}},

{short:'Ano e ID',t:'Passo 2 — Confira o ano e, se tiver, o ID da compra',
 b:'Se já conhece o código, digite no campo <b>Código UASG</b>. O <b>Ano</b> define o período da busca. O <b>ID da compra</b> é opcional: ao informá-lo, o sistema separa sozinho a <b>UASG</b> e o <b>ano</b> e mostra direto a publicação daquela compra no PNCP, com os links.',
 tip:'💡 Com o ID preenchido, a busca vai direto àquela compra. Sem ele, o sistema lista todos os contratos e atas da UASG no ano.',
 run:async a=>{a.unring();await a.scroll('#d-uasg',100);a.ring('#d-ano','Ano da busca',4);await a.sleep(1600);a.unring();await a.click('#d-id');await a.type('#d-id-v','15305006000142026',80);
  a.ring('#d-id','ID da compra (opcional)',4);await a.sleep(2200);a.unring();a.set(S=>S.id='');await a.sleep(300);}},

{short:'Filtros',t:'Passo 3 — Use os filtros avançados',
 b:'Em <b>Filtros Avançados</b> você afina o resultado por <b>modalidade</b>, <b>palavra-chave do objeto</b>, <b>fornecedor</b> por nome ou CNPJ, <b>número do processo</b> e <b>período</b>. Aqui filtramos pelo objeto <b>material de expediente</b>. Os filtros valem tanto para contratos quanto para atas.',
 tip:'💡 Deixe tudo vazio para ver todos os registros da UASG.',
 run:async a=>{a.unring();await a.scroll('#d-fa-h',80);await a.click('#d-fa-h',()=>a.set(S=>S.fa=true));await a.click('#d-obj');await a.type('#d-obj-v','material de expediente',70);
  a.set(S=>S.obj='material de expediente');a.ring('#d-fa-box','Filtros opcionais',4);await a.sleep(2200);a.unring();}},

{short:'Consultar',t:'Passo 4 — Clique em Consultar',
 b:'Clique em <b>🔍 Consultar</b>. O sistema busca <b>contratos</b> e <b>atas de registro de preços</b> ao mesmo tempo no ComprasGov. No topo aparecem os totais: quantos <b>contratos</b>, quantas <b>atas</b> e o <b>total de registros</b>.',
 tip:'💡 Se as bases do governo estiverem instáveis, o sistema avisa. Tente de novo depois de alguns minutos.',
 run:async a=>{a.unring();await a.scroll('#d-go',250);await a.click('#d-go',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.out=true;});await a.sleep(400);
  await a.scroll('#d-met',90);a.ring('#d-met','Totais encontrados');await a.sleep(2600);a.unring();}},

{short:'Contrato',t:'Passo 5 — Abra uma compra',
 b:'A aba <b>Compras</b> lista os contratos. Clique no título para abrir: você vê o <b>fornecedor</b>, o <b>objeto</b>, a <b>vigência</b> e o <b>valor global</b>. Abaixo ficam os <b>links externos</b> para o ComprasNet e o PNCP e os <b>documentos</b> da compra, como o edital e o termo de referência.',
 tip:'💡 Quando há muitos registros, use o botão Carregar mais compras para ver os seguintes.',
 run:async a=>{a.unring();await a.scroll('#d-cp-h',90);await a.click('#d-cp-h',()=>a.set(S=>S.cp=true));await a.sleep(600);await a.scroll('#d-links',120);a.ring('#d-links','Links externos');await a.sleep(2200);a.unring();
  a.ring('#d-cp-b .docb','Documentos');await a.sleep(2200);a.unring();}},

{short:'Itens',t:'Passo 6 — Veja os itens, o vencedor e o deságio',
 b:'Abra <b>Itens da compra</b>. O sistema soma o <b>valor estimado</b> e o <b>valor homologado</b> e calcula o <b>deságio</b>, que é quanto a licitação ficou abaixo do estimado. Em cada item aparece o <b>vencedor</b>, com nome e CNPJ, o valor homologado e o deságio daquele item.',
 tip:'💡 O deságio considera apenas os itens que têm resultado e valor estimado informado. Itens com valor sigiloso ficam de fora.',
 run:async a=>{a.unring();await a.scroll('#d-it-h',90);await a.click('#d-it-h',()=>a.set(S=>S.it=true));await a.sleep(500);await a.scroll('#d-des',100);a.ring('#d-des','Deságio da compra');await a.sleep(2800);a.unring();
  a.ring('#d-it-b .vend','Vencedor do item');await a.sleep(2400);a.unring();}},

{short:'Exportar',t:'Passo 7 — Exporte e siga para o fornecedor',
 b:'Clique em <b>📊 Exportar resultados</b> para baixar uma planilha <b>Excel</b> com os contratos e as atas, já respeitando os filtros. E, em cada contrato, o botão <b>🏢 Consultar fornecedor</b> abre a página <b>Consulta CNPJ</b> com o fornecedor preenchido e a consulta já feita. <b>Resumo:</b> 1) ache a UASG; 2) ano e ID; 3) filtros; 4) consultar; 5) abra a compra; 6) confira itens e deságio; 7) exporte.',
 tip:'🎉 Fim da aula! Para conhecer o fornecedor a fundo, veja a vídeo-aula da Consulta CNPJ.',
 run:async a=>{a.unring();await a.scroll('#d-xls',80);a.ring('#d-xls','Excel');await a.click('#d-xls',()=>a.toast('✔ detalhes_compra_UASG999001_2026.xlsx'));await a.sleep(1800);a.unring();
  await a.scroll('#d-forn',200);a.ring('#d-forn','Abre a Consulta CNPJ');await a.sleep(2600);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="detalhes_compra")
