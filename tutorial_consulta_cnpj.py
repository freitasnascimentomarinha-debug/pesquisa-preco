"""Vídeo-aula simulado: como usar a página Consulta CNPJ (cadastro, sanções, contratos, atas, adesões e notas fiscais de um fornecedor)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a Consulta CNPJ"
DESCRICAO = (
    "Conhecer um fornecedor pelo CNPJ: dados da empresa, sanções, contratos, atas, adesões vigentes e notas fiscais, "
    "com exportação em Excel e ficha em PDF. Duração aproximada: 4 min, com narração."
)

_MOCK_CSS = r"""
.pn{display:none}.pn.on{display:block}
#c-res{display:none}#c-res.on{display:block}
.srcl{color:#9fb6d8;font-size:10.5px;line-height:1.5;margin:8px 0}
.al{border-radius:8px;padding:9px 11px;margin:7px 0;font-size:12px;line-height:1.4;display:none}.al.on{display:block}
.al.r{background:rgba(239,68,68,.16);border:1px solid rgba(239,68,68,.5);color:#fecaca}
.card2{background:rgba(8,26,57,.78);border:1px solid #d4af37;border-radius:10px;padding:10px 12px;font-size:11.5px;line-height:1.55}
.card2 .tt{color:var(--gold);font-weight:800;font-size:13px;border-bottom:1px solid #1e5b9f;padding-bottom:4px;margin-bottom:5px}
.card2 .lb{color:#9fb6d8}
.cc{background:rgba(8,26,57,.78);border-left:5px solid #ef4444;border-radius:8px;padding:9px 12px;margin:8px 0;font-size:11.5px;line-height:1.55;color:#cbd5e1}
.cc.gr{border-left-color:#3b82f6}.cc .ct{color:#fff;font-weight:800;font-size:12.5px;margin-bottom:3px}
.sel2{display:grid;grid-template-columns:5fr 1fr;gap:8px;align-items:center;margin-top:6px}
.sbtn{display:inline-block;background:#1b2a47;border:1px solid #3b4d70;border-radius:8px;padding:6px 12px;font-weight:700;font-size:12px;margin:6px 8px 0 0}
.mtr{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:8px}.mtr .k{font-size:11px;color:#b6cae2}.mtr .v{font-size:21px;font-weight:700}
.ms{display:flex;flex-wrap:wrap;gap:5px;margin-top:4px}
.tg{display:inline-block;background:#ef4444;color:#fff;border-radius:6px;padding:3px 8px;font-weight:700;font-size:11px}
.tabs div{white-space:nowrap}
#c-nfres{display:none}#c-nfres.on{display:block}
"""

_STAGE_HTML = r"""
<div class="qh" id="c-head"><div class="qs">💻</div><div><b>Consulta de Fornecedor por CNPJ</b><small>Informações atualizadas e histórico de contratos com o Governo Federal.</small></div></div>
<div class="frm" style="grid-template-columns:2fr 1fr 1fr;margin-top:12px">
  <div><div class="lbl">Digite o CNPJ (somente números ou com pontuação):</div><div class="fld" id="c-cnpj"><span id="c-cnpj-v"></span><span class="ph">Ex: 00.000.000/0001-00</span></div></div>
  <div><div class="lbl">Janela de Pesquisa (Anos de histórico):</div><div class="fld" id="c-anos"><span id="c-anos-v">3</span></div></div>
  <div><div class="btn pri" id="c-go" style="background:#d4af37;border-color:#d4af37;color:#111;padding:9px">Consultar</div></div>
</div>
<div class="spin" id="c-spin"><i></i><span id="c-spin-t">Consultando 6 fontes em paralelo...</span></div>

<div id="c-res">
  <div class="srcl" id="c-src">Fontes consultadas: ✅ OpenCNPJ · ✅ BrasilAPI · ✅ PNCP — contratos · ✅ PNCP — compras · ✅ PNCP — atas · ✅ Compras.gov.br — ARP · ✅ Sanções (CEIS/CNEP/CEPIM)<br>Período consultado: últimos 3 ano(s) (contratos, compras, atas e ARPs).</div>
  <div class="al r on" id="c-alert">🚫 <b>Atenção: sanção vigente encontrada</b> (1) — veja a aba <b>🚫 Sanções</b>. Verifique o impedimento antes de qualquer contratação.</div>
  <div><span class="sbtn" id="c-xls">📊 Exportar tudo (Excel)</span><span class="sbtn" id="c-pdf">📄 Ficha do fornecedor (PDF)</span></div>
  <div class="tabs" id="c-tabs"><div id="c-tab-emp" class="on">🏢 Dados da Empresa</div><div id="c-tab-sanc">🚫 Sanções (1)</div><div id="c-tab-ct">📋 Contratos</div><div id="c-tab-ad">🤝 Adesões Vigentes</div><div id="c-tab-nf">📄 Notas Fiscais</div></div>

  <div class="pn on" id="p-emp">
    <div class="sec2">Informações da Empresa: EMPRESA EXEMPLO</div>
    <div class="two">
      <div class="card2" id="c-ident"><div class="tt">Identificação</div>
        <div><span class="lb">Razão Social:</span> EMPRESA EXEMPLO COMERCIO LTDA</div><div><span class="lb">CNPJ:</span> 00.394.460/0001-41</div>
        <div><span class="lb">Situação:</span> Ativa</div><div><span class="lb">Porte:</span> Demais</div>
        <div><span class="lb">Natureza jurídica:</span> Sociedade Empresária Limitada</div><div><span class="lb">Início da atividade:</span> 2009-05-12</div>
        <div><span class="lb">Optante pelo Simples:</span> Não</div><div><span class="lb">CNAE principal:</span> 4647-8/01 - Comércio atacadista de artigos de escritório</div></div>
      <div class="card2"><div class="tt">Contato e Endereço</div>
        <div><span class="lb">📧 Email:</span> contato@exemplo.com.br</div><div><span class="lb">📞 Telefone:</span> (21) 3000-0000</div>
        <div><span class="lb">📍 Endereço:</span> RUA EXEMPLO, 100 - CENTRO</div><div><span class="lb">🏙️ Cidade/UF:</span> RIO DE JANEIRO/RJ</div></div>
    </div>
    <div class="sec2" style="font-size:13px">Quadro Societário</div>
    <table id="c-qsa"><thead><tr><th>Nome</th><th>Qualificação</th><th>Entrada</th></tr></thead><tbody><tr><td>SÓCIO EXEMPLO UM</td><td>Sócio-Administrador</td><td>2009-05-12</td></tr><tr><td>SÓCIO EXEMPLO DOIS</td><td>Sócio</td><td>2015-03-01</td></tr></tbody></table>
  </div>

  <div class="pn" id="p-sanc">
    <div class="sec2">Sanções e impedimentos</div>
    <div class="cap2">Fonte: Portal da Transparência (CGU) — CEIS, CNEP e CEPIM. Bases de 21/10/2026, 21/10/2026 e 19/10/2026.</div>
    <div class="cap2" style="color:#dbe7f7"><b>CEIS — Empresas Inidôneas e Suspensas: 1 registro(s)</b></div>
    <div class="cc" id="c-sc"><div class="ct">🔴 Vigente — Impedimento/proibição de contratar com prazo determinado</div>
      <div><b>Período:</b> 10/03/2026 a 10/03/2028</div><div><b>Órgão sancionador:</b> ÓRGÃO EXEMPLO</div><div><b>Processo:</b> 00000.000000/2026-00</div><div><b>Abrangência:</b> Sem informação</div></div>
    <div class="cap2"><b>CNEP:</b> nenhum registro · <b>CEPIM:</b> nenhum registro</div>
  </div>

  <div class="pn" id="p-ct">
    <div class="sec2">Histórico de Contratos e Licitações</div>
    <div class="cap2">Fonte: PNCP — Portal Nacional de Contratações Públicas</div>
    <div class="cc gr"><div class="ct">📄 Contrato nº 00012/2026 — MINISTERIO EXEMPLO</div>
      <div><b>Unidade:</b> UNIDADE EXEMPLO (Brasília/DF)</div><div><b>Modalidade:</b> Pregão | <b>Situação:</b> Ativo</div><div><b>Objeto:</b> Aquisição de material de expediente</div>
      <div><b>Vigência:</b> 2026-02-01 a 2027-02-01 · <span style="color:#d4af37"><b>Valor: R$ 184.300,00</b></span></div></div>
    <div class="lbl" style="margin-top:8px"><b>🔍 Ver detalhes na página Detalhes Compra</b></div>
    <div class="sel2"><div class="fld" id="c-selreg" style="font-size:11px">Contrato nº 00012/2026 — MINISTERIO EXEMPLO (UASG 999001, 2026)</div><div class="btn" id="c-abrir">Abrir</div></div>
  </div>

  <div class="pn" id="p-ad">
    <div class="sec2">Adesões Vigentes</div>
    <div class="cap2">Fonte: ComprasGov — itens de ARP onde este CNPJ é fornecedor registrado</div>
    <div class="al on" style="background:rgba(34,197,94,.15);border:1px solid rgba(34,197,94,.4);color:#bbf7d0;display:block">Encontrados <b>12</b> itens de ARP associados a este CNPJ (<b>5</b> abertos para adesão, 7 outros).</div>
    <div class="tabs"><div class="on">🟢 Abertos para Adesão</div><div>📋 Todos os Itens</div></div>
    <div class="exp" style="background:#0b2447;border:1px solid var(--line);border-radius:7px;margin-top:8px"><div class="h" style="padding:8px 11px;font-size:12px">🟢 ARP nº 00005/2026 — UNIDADE GERENCIADORA EXEMPLO (5 itens)</div>
      <div style="padding:9px 11px;border-top:1px solid var(--line)"><div class="mtr" style="margin-top:0"><div><div class="k">Modalidade</div><div class="v" style="font-size:14px">Pregão</div></div><div><div class="k">Vigência</div><div class="v" style="font-size:12px">2026-03-15 → 2027-03-15</div></div><div><div class="k">Valor Total Itens</div><div class="v" style="font-size:15px">R$ 96.420,00</div></div></div>
        <div class="sbtn" style="margin-top:8px">🔍 Ver detalhes na página Detalhes Compra</div></div></div>
  </div>

  <div class="pn" id="p-nf">
    <div class="sec2">Pesquisa em Notas Fiscais</div>
    <div class="cap2">Buscando o CNPJ <b>00.394.460/0001-41</b> nos arquivos de Notas Fiscais do Portal da Transparência.</div>
    <div class="lbl">Selecione os meses para pesquisar:</div>
    <div class="fld" id="c-meses"><div class="ms"><span class="tg">202602_NFe_NotaFiscalItem.csv</span><span class="tg">202601_NFe_NotaFiscalItem.csv</span><span class="tg">202512_NFe_NotaFiscalItem.csv</span></div></div>
    <div class="btn pri" id="c-nfgo" style="margin-top:10px">🔍 Pesquisar nas Notas Fiscais</div>
    <div class="spin" id="c-nfspin"><i></i><span>Baixando e pesquisando os arquivos...</span></div>
    <div id="c-nfres"><div class="cap2" style="color:#bbf7d0">✅ 202602: <b>3</b> nota(s) em 9 linha(s) de item</div>
      <div class="sec2" style="font-size:13px">Resultados Consolidados: 8 nota(s) fiscal(is) em 24 linhas de item</div>
      <div class="mtr" id="c-nfm"><div><div class="k">Notas fiscais (distintas)</div><div class="v">8</div></div><div><div class="k">Valor total</div><div class="v">R$ 96.420,00</div></div><div><div class="k">Períodos com notas</div><div class="v">3</div></div></div>
      <div><span class="sbtn">📥 Baixar notas fiscais em Excel</span><span class="sbtn">📥 Baixar resultados em CSV</span></div></div>
  </div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
let S;
function resetS(){S={cnpj:'',anos:'3',spin:false,res:false,tab:'emp',nfspin:false,nfres:false};}
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  const p=document.getElementById('c-cnpj-v'),ph=p.parentElement.querySelector('.ph');p.textContent=S.cnpj;ph.style.display=S.cnpj?'none':'inline';
  T('c-anos-v',S.anos);
  $('#c-spin').classList.toggle('on',S.spin);$('#c-res').classList.toggle('on',S.res);
  ['emp','sanc','ct','ad','nf'].forEach(k=>{$('#p-'+k).classList.toggle('on',S.tab===k);$('#c-tab-'+k).classList.toggle('on',S.tab===k);});
  $('#c-nfspin').classList.toggle('on',S.nfspin);$('#c-nfres').classList.toggle('on',S.nfres);
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a Consulta CNPJ',
 b:'A página <b>Consulta CNPJ</b> reúne, em uma única consulta, tudo o que o Governo Federal publica sobre um <b>fornecedor</b>: <b>dados da empresa</b>, <b>sanções</b>, <b>contratos</b>, <b>atas de registro de preços</b>, <b>adesões vigentes</b> e <b>notas fiscais</b>. É ideal para conhecer uma empresa antes de pedir cotação ou contratar.',
 tip:'💡 Os dados vêm de fontes públicas: Receita Federal, PNCP, Compras.gov.br e Portal da Transparência.',
 run:async a=>{a.unring();await a.top();a.ring('#c-head','Consulta por CNPJ');await a.sleep(2800);a.unring();}},

{short:'CNPJ',t:'Passo 1 — Digite o CNPJ e consulte',
 b:'Digite o <b>CNPJ</b>, com ou sem pontuação, e defina a <b>janela de pesquisa</b>, que é quantos anos de histórico você quer ver. Aqui, <b>3 anos</b>. Depois clique em <b>Consultar</b>. O sistema confere os <b>dígitos verificadores</b> e avisa se o CNPJ estiver errado.',
 tip:'💡 Quanto maior a janela, mais registros, mas a consulta pode levar um pouco mais.',
 run:async a=>{a.unring();await a.top();await a.click('#c-cnpj');await a.type('#c-cnpj-v','00.394.460/0001-41',90);a.set(S=>S.cnpj='00.394.460/0001-41');a.ring('#c-anos','Anos de histórico',4);await a.sleep(1600);a.unring();
  await a.click('#c-go',()=>a.set(S=>S.spin=true));await a.sleep(1800);a.set(S=>{S.spin=false;S.res=true;});await a.sleep(500);}},

{short:'Fontes',t:'Passo 2 — Acompanhe as fontes consultadas',
 b:'O sistema consulta <b>seis fontes ao mesmo tempo</b>, por isso a resposta é rápida. Logo abaixo, uma linha mostra o estado de <b>cada fonte</b>: uma marca <b>verde ✅</b> quando a fonte respondeu e uma marca <b>vermelha ❌</b> quando falhou, com o motivo. Se alguma falhar, os resultados das outras continuam valendo, e você pode tentar de novo mais tarde.',
 tip:'💡 Uma fonte fora do ar não significa que a empresa não tem registros nela. Repita a consulta antes de concluir.',
 run:async a=>{a.unring();await a.scroll('#c-src',70);a.ring('#c-src','Estado de cada fonte');await a.sleep(3200);a.unring();}},

{short:'Alerta',t:'Passo 3 — Atenção ao alerta de sanções',
 b:'Se a empresa tiver <b>sanção vigente</b>, aparece um <b>alerta vermelho</b> no topo. Ele checa o <b>CEIS</b>, o <b>CNEP</b> e o <b>CEPIM</b>, os cadastros do Governo sobre empresas punidas ou impedidas. Sem sanção, o aviso é verde e informa a data das bases consultadas.',
 tip:'💡 Nesta aula, a empresa é fictícia e tem uma sanção de exemplo, para você ver como o alerta aparece.',
 run:async a=>{a.unring();await a.scroll('#c-alert',70);a.ring('#c-alert','Sanção vigente');await a.sleep(3200);a.unring();}},

{short:'Empresa',t:'Passo 4 — Leia os dados da empresa',
 b:'A aba <b>Dados da Empresa</b> mostra a <b>razão social</b>, a <b>situação cadastral</b>, o <b>porte</b>, a <b>natureza jurídica</b>, o início da atividade, se é optante pelo <b>Simples</b> ou <b>MEI</b> e o <b>CNAE principal</b>, a atividade econômica. Ao lado, e-mail, telefone e endereço, e abaixo o <b>quadro societário</b>.',
 tip:'💡 Compare o CNAE da empresa com o objeto que você quer comprar. E-mail e telefone podem não constar na Receita.',
 run:async a=>{a.unring();await a.scroll('#c-ident',80);a.ring('#c-ident','Identificação');await a.sleep(3000);a.unring();await a.scroll('#c-qsa',90);a.ring('#c-qsa','Sócios');await a.sleep(2200);a.unring();}},

{short:'Sanções',t:'Passo 5 — Confira a aba Sanções',
 b:'Na aba <b>Sanções</b>, cada registro mostra se está <b>vigente</b> ou <b>encerrado</b>, o <b>período</b>, o <b>órgão sancionador</b>, o processo e a abrangência. Uma sanção vigente de impedimento de contratar é motivo para <b>não prosseguir</b> com a contratação. A certidão oficial continua sendo a do Portal da Transparência ou do SICAF.',
 tip:'💡 As bases são atualizadas pelo Portal em dias úteis. A tela informa a data de cada base.',
 run:async a=>{a.unring();await a.scroll('#c-tabs',60);await a.click('#c-tab-sanc',()=>a.set(S=>S.tab='sanc'));await a.sleep(500);a.ring('#c-sc','Sanção vigente');await a.sleep(3200);a.unring();}},

{short:'Contratos',t:'Passo 6 — Veja contratos, compras e atas',
 b:'As abas <b>Contratos</b>, <b>Atas de Registro de Preços</b> e <b>Dispensas</b> mostram o que o fornecedor já vendeu ao governo: órgão, unidade, modalidade, <b>objeto</b>, vigência e <b>valor</b>. Embaixo, o seletor <b>Ver detalhes na página Detalhes Compra</b>: escolha um registro e clique em <b>Abrir</b> para ver a compra completa, com itens e documentos.',
 tip:'💡 Os registros respeitam a janela de anos que você escolheu no início.',
 run:async a=>{a.unring();await a.scroll('#c-tabs',60);await a.click('#c-tab-ct',()=>a.set(S=>S.tab='ct'));await a.sleep(500);a.ring('.cc.gr','Contrato');await a.sleep(2400);a.unring();
  await a.scroll('#c-selreg',140);a.ring('#c-abrir','Abre a Detalhes Compra');await a.sleep(2600);a.unring();}},

{short:'Adesões',t:'Passo 7 — Encontre adesões vigentes',
 b:'Na aba <b>Adesões Vigentes</b>, o sistema mostra as <b>atas de registro de preços</b> em que a empresa é <b>fornecedora registrada</b> e que ainda estão <b>abertas para adesão</b>, ou seja, vigentes e com quantidade máxima de adesão. Cada ata traz modalidade, vigência, valor e a lista de itens.',
 tip:'💡 É uma forma rápida de achar atas para aproveitar, a chamada carona, a partir de um fornecedor conhecido.',
 run:async a=>{a.unring();await a.scroll('#c-tabs',60);await a.click('#c-tab-ad',()=>a.set(S=>S.tab='ad'));await a.sleep(500);a.ring('#p-ad .exp','ARP aberta para adesão');await a.sleep(3200);a.unring();}},

{short:'Notas',t:'Passo 8 — Pesquise as notas fiscais',
 b:'Na aba <b>Notas Fiscais</b>, escolha os <b>meses</b> e clique em <b>Pesquisar nas Notas Fiscais</b>. O sistema procura as notas emitidas pelo CNPJ nos arquivos do Portal da Transparência. O resumo mostra o número de <b>notas fiscais distintas</b>, o <b>valor total</b> e os períodos com notas. Cada nota é contada uma só vez, mesmo com vários itens.',
 tip:'💡 Os arquivos são grandes; na primeira pesquisa do mês o download pode demorar um pouco.',
 run:async a=>{a.unring();await a.scroll('#c-tabs',60);await a.click('#c-tab-nf',()=>a.set(S=>S.tab='nf'));await a.sleep(500);a.ring('#c-meses','Meses a pesquisar');await a.sleep(1800);a.unring();
  await a.click('#c-nfgo',()=>a.set(S=>S.nfspin=true));await a.sleep(1800);a.set(S=>{S.nfspin=false;S.nfres=true;});await a.sleep(500);await a.scroll('#c-nfm',110);a.ring('#c-nfm','Resumo das notas');await a.sleep(2800);a.unring();}},

{short:'Exportar',t:'Passo 9 — Exporte os resultados',
 b:'No topo, <b>Exportar tudo</b> gera uma planilha <b>Excel</b> com empresa, sócios, contratos, atas, itens de ata, dispensas e sanções. <b>Ficha do fornecedor</b> gera um <b>PDF</b> de uma página com o resumo, para anexar ao processo. <b>Resumo:</b> 1) digite o CNPJ; 2) veja as fontes; 3) atenção às sanções; 4) dados da empresa; 5) contratos e atas; 6) adesões; 7) notas fiscais; 8) exporte.',
 tip:'🎉 Fim da aula! Para ver uma compra por dentro, veja a vídeo-aula de Detalhes Compra.',
 run:async a=>{a.unring();await a.scroll('#c-xls',70);a.ring('#c-xls','Excel');await a.click('#c-xls',()=>a.toast('✔ fornecedor_00394460000141.xlsx'));await a.sleep(1500);a.unring();
  a.ring('#c-pdf','Ficha em PDF');await a.click('#c-pdf',()=>a.toast('✔ ficha_fornecedor_00394460000141.pdf'));await a.sleep(1500);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="consulta_cnpj")
