"""Vídeo-aula simulado: como usar a página Cotação Direta (pedido de orçamento por e-mail a fornecedores)."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar a Cotação Direta"
DESCRICAO = (
    "Pedir orçamento por e-mail a quem vendeu recentemente à Administração: dados da OM, itens e CATMAT, "
    "fornecedores, proposta em Word e envio. Duração aproximada: 4 min."
)

_MOCK_CSS = r"""
.passo{background:rgba(8,26,57,.78);border:1px solid #1e5b9f;border-left:5px solid var(--gold);border-radius:9px;padding:9px 12px;margin:16px 0 8px}
.passo h3{color:var(--gold);font-size:14px;margin:0}.passo p{color:#b6cae2;font-size:10.5px;margin:3px 0 0;line-height:1.35}
.g3b{display:grid;grid-template-columns:3fr 1fr;gap:10px}.g3c{display:grid;grid-template-columns:1.2fr 1fr 1.6fr;gap:10px;margin-top:8px}
.tabs div{cursor:default}
#d-lista-box{display:block}
#d-itens,#d-prep,#d-res{display:none}#d-itens.on,#d-res.on{display:block}#d-prep.on{display:block}
#d-ittab td,#d-ittab th,#d-ftab td,#d-ftab th{font-size:10px;padding:5px 4px}
.dd.long{max-height:140px}
.warnb{background:rgba(245,158,11,.14);border:1px solid rgba(245,158,11,.4);color:#fde68a;border-radius:8px;padding:8px 11px;margin:8px 0;font-size:11px}
.okb{background:rgba(34,197,94,.15);border:1px solid rgba(34,197,94,.4);color:#bbf7d0;border-radius:8px;padding:8px 11px;margin:8px 0;font-size:11.5px}
.infb{background:rgba(59,130,246,.15);border:1px solid rgba(59,130,246,.4);color:#bfdbfe;border-radius:8px;padding:8px 11px;margin:8px 0;font-size:11px}
.mail{background:#fff;color:#1f2937;border-radius:8px;padding:10px 12px;font-size:11px;line-height:1.5;white-space:pre-wrap;min-height:90px;border:1px solid #cbd5e1}
.sub{background:rgba(7,20,42,.8);border:1px solid #2b6cb0;border-radius:7px;padding:7px 10px;font-size:12px;color:#9fb6d8}
.frow2{display:flex;gap:10px;margin-top:10px}.frow2 .btn{flex:1}
.hdrm{font-size:22px}
"""

_STAGE_HTML = r"""
<div class="qh" id="d-head"><div class="qs">📨</div><div><b>Cotação Direta</b><small>Peça orçamento por e-mail a quem vendeu recentemente à Administração: o sistema monta a proposta em Word, sugere o CATMAT e envia uma mensagem única, com os fornecedores em cópia oculta.</small></div><span class="qb">PESQUISA DIRETA<br>COM FORNECEDORES</span></div>

<div class="passo" id="d-p1"><h3>1. Dados da sua OM</h3><p>O cabeçalho da proposta e o e-mail usam estes dados. Comece a digitar o nome: se a OM já foi usada antes, o sistema sugere e preenche o endereço. Para uma OM nova, digite o CEP.</p></div>
<div class="g3b">
  <div><div class="lbl">Nome da OM (Organização Militar)</div><div class="fld" id="d-nome"><span id="d-nome-v"></span><span class="ph" id="d-nome-ph">Comece a digitar o nome da OM</span></div></div>
  <div><div class="lbl">CEP de entrega</div><div class="fld" id="d-cep"><span id="d-cep-v"></span><span class="ph" id="d-cep-ph">00000-000</span></div></div>
</div>
<div class="cap2" id="d-cepok"></div>
<div class="g3b"><div><div class="lbl">Endereço</div><div class="fld"><span id="d-end"></span>&nbsp;</div></div><div><div class="lbl">Cidade / UF</div><div class="fld"><span id="d-cid"></span>&nbsp;</div></div></div>
<div class="g3c">
  <div><div class="lbl">CNPJ da OM</div><div class="fld" id="d-cnpj"><span id="d-cnpj-v"></span><span class="ph" id="d-cnpj-ph">00.000.000/0000-00</span></div></div>
  <div><div class="lbl">Telefone para contato</div><div class="fld" id="d-tel"><span id="d-tel-v"></span><span class="ph" id="d-tel-ph">(21) 0000-0000</span></div></div>
  <div><div class="lbl">E-mail(s) institucional(is)</div><div class="fld" id="d-mail"><span id="d-mail-v"></span><span class="ph" id="d-mail-ph">nome@marinha.mil.br; chefe@marinha.mil.br</span></div></div>
</div>
<div class="lbl" style="margin-top:8px">Responsável pelo pedido (assinatura do e-mail)</div><div class="fld" id="d-resp"><span id="d-resp-v"></span><span class="ph" id="d-resp-ph">Ex.: 1T (IM) Fulano de Tal – Encarregado da Divisão de Obtenção</span></div>

<div class="passo" id="d-p2"><h3>2. Itens e quantidades</h3><p>Digite como uma lista de compras ou envie uma planilha. O sistema já procura o CATMAT mais próximo de cada item: confira, melhore as descrições se quiser e deixe de fora o que não for pedir.</p></div>
<div class="tabs"><div class="on">✍️ Digitar a lista</div><div id="d-tabx">📎 Enviar Excel/CSV</div></div>
<div class="lbl" style="margin-top:8px">Um item por linha, com a quantidade ao lado</div>
<div class="ta" id="d-ta" style="min-height:62px"><span id="d-ta-v"></span><span class="ph" id="d-ta-ph">Caneta esferográfica azul - 100
50 resmas de papel A4
Fita isolante 20m - 30</span></div>
<div class="btn" id="d-ident" style="margin-top:8px;width:170px">Identificar itens</div>
<div class="spin" id="d-spin1"><i></i><span>Identificando os itens e procurando o CATMAT de cada um…</span></div>
<div id="d-itens"><div class="cap2"><b>Usar</b>: desmarque para deixar um item de fora do pedido. Você pode <b>editar a descrição, a quantidade e a unidade</b>. Ao alterar uma descrição, o sistema casa sozinho o CATMAT mais próximo.</div>
  <table id="d-ittab"><thead><tr><th>Usar</th><th>Descrição do item (edite)</th><th>Qtd.</th><th>Un.</th><th>CATMAT</th><th>% casam.</th><th>Descrição do item no CATMAT</th></tr></thead><tbody></tbody></table>
  <div class="cap2">3 item(ns) no pedido.</div></div>

<div class="passo" id="d-p3"><h3>3. Escolher fornecedores e gerar a proposta</h3><p>Para cada item, o sistema sugere o CATMAT e busca fornecedores que venderam item igual ou semelhante no último ano, sem repetir fornecedor entre os itens. Os fornecedores terão 5 dias úteis para responder. Pode levar alguns minutos.</p></div>
<div class="ck" id="d-loc"><span class="box on" style="background:#ef4444;border-color:#ef4444">✓</span><span>Dar preferência a fornecedores da mesma cidade e do mesmo estado da OM</span></div>
<div class="infb" id="d-falta">Falta preencher: nome da OM, e-mail institucional, itens.</div>
<div class="btn pri" id="d-prepara" style="margin-top:6px;padding:10px;font-size:13px;opacity:.5">🔎 Preparar cotação</div>
<div id="d-prep"><div class="warnb">⏳ Processando… não feche nem atualize esta página até terminar.</div><div class="cap2" style="color:#dbe7f7"><b id="d-etapa"></b></div><div class="prog on"><div class="b"><i id="d-pb"></i></div></div><div class="cap2" id="d-st"></div></div>
<div class="okb" id="d-ok" style="display:none">Pronto em 1min 12s: 6 fornecedor(es) com e-mail para 3 item(ns).</div>

<div id="d-res">
  <div class="sec2">Itens e CATMAT sugerido</div>
  <table><thead><tr><th>Item</th><th>Descrição</th><th>Qtd.</th><th>CATMAT sugerido</th><th>Fornecedores</th></tr></thead><tbody>
    <tr><td>1</td><td>Caneta esferográfica azul</td><td>100</td><td>150001 (92%)</td><td>2</td></tr>
    <tr><td>2</td><td>Resma de papel A4</td><td>50</td><td>123456 (94%)</td><td>2</td></tr>
    <tr><td>3</td><td>Fita isolante 20m</td><td>30</td><td>150310 (88%)</td><td>2</td></tr></tbody></table>
  <div class="sec2" id="d-fh">Fornecedores que receberão o pedido</div>
  <div class="cap2">Desmarque “Enviar” para tirar alguém, corrija um e-mail ou acrescente uma linha (empresa + e-mail) no fim da tabela. Todos recebem a proposta completa, em cópia oculta.</div>
  <table id="d-ftab"><thead><tr><th>Enviar</th><th>Item</th><th>Empresa</th><th>E-mail</th><th>Cidade/UF</th><th>Por que foi escolhida</th></tr></thead><tbody></tbody></table>
  <div class="mets" style="grid-template-columns:repeat(3,1fr)" id="d-mets"></div>

  <div class="passo"><h3>4. Revisar o e-mail e baixar os arquivos</h3></div>
  <div class="lbl">Assunto</div><div class="sub">Pedido de orçamento nº CD-20261021-A1B2 — Centro de Operações do Abastecimento</div>
  <div class="lbl" style="margin-top:8px">Texto do e-mail (pode editar)</div>
  <div class="mail" id="d-mailtxt">Prezados,

O Centro de Operações do Abastecimento solicita orçamento dos itens constantes da proposta anexa, para pesquisa de preços (IN SEGES/ME nº 65/2021).

Prazo para resposta: 5 dias úteis (até 28/10/2026). Validade da proposta: 60 dias.

Atenciosamente,
1T (IM) Fulano de Tal</div>
  <div class="frow2"><div class="btn" id="d-docx">⬇️ Baixar a proposta em Word</div><div class="btn" id="d-comp">⬇️ Baixar a lista de fornecedores (comprovante, Excel)</div></div>

  <div class="passo"><h3>5. Enviar</h3><p>Uma mensagem para você (destinatário visível, com a proposta anexada) e os fornecedores em cópia oculta: um não vê o outro.</p></div>
  <div class="cap2">Remetente: Centro de Operações do Abastecimento &lt;cotacao@exemplo.example&gt; • Para e respostas: seu e-mail institucional.</div>
  <div class="frow2"><div class="btn" id="d-teste">🧪 Enviar teste só para mim</div><div class="btn pri" id="d-envia" style="opacity:.5">📨 Enviar para os fornecedores</div></div>
  <div class="okb" id="d-testeok" style="display:none">Teste enviado: confira a sua caixa de entrada (e o spam).</div>
  <div class="ck" id="d-conf" style="margin-top:10px"><span class="box" id="d-conf-b"></span><span>Revisei o texto, a proposta e a lista: enviar para 6 fornecedor(es).</span></div>
  <div class="okb" id="d-enviado" style="display:none">✅ 1 mensagem(ns) enviada(s) para 6 fornecedor(es). A cópia foi para o seu e-mail institucional. Baixe o comprovante acima.</div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
const TXT='Caneta esferográfica azul - 100\n50 resmas de papel A4\nFita isolante 20m - 30';
const FORN=[
 {i:1,n:'PAPELARIA EXEMPLO RIO LTDA',e:'vendas@papelaria-rio.example',c:'Rio de Janeiro/RJ',m:'Vendeu item igual (CATMAT 150001) em 08/2026 — mesma cidade'},
 {i:1,n:'COMERCIAL EXEMPLO NITERÓI ME',e:'contato@comercial-niteroi.example',c:'Niterói/RJ',m:'Vendeu item semelhante em 07/2026 — mesmo estado'},
 {i:2,n:'DISTRIBUIDORA EXEMPLO SP LTDA',e:'orcamentos@dist-sp.example',c:'São Paulo/SP',m:'Vendeu item igual (CATMAT 123456) em 09/2026'},
 {i:2,n:'SUPRIMENTOS EXEMPLO RJ EIRELI',e:'comercial@suprimentos-rj.example',c:'Rio de Janeiro/RJ',m:'Vendeu item igual em 06/2026 — mesma cidade'},
 {i:3,n:'ELÉTRICA EXEMPLO LTDA',e:'vendas@eletrica-exemplo.example',c:'Duque de Caxias/RJ',m:'Vendeu item igual (CATMAT 150310) em 08/2026 — mesmo estado'},
 {i:3,n:'MATERIAIS EXEMPLO DF ME',e:'atendimento@materiais-df.example',c:'Brasília/DF',m:'Vendeu item semelhante em 05/2026'}];
let S;
function resetS(){S={nome:'',cep:'',cepok:false,cnpj:'',tel:'',mail:'',resp:'',txt:'',spin1:false,itens:false,edit:false,prep:0,done:false,desm:false,teste:false,conf:false,enviado:false};}
const IT=()=>[
 {d:'Caneta esferográfica azul',q:100,u:'UN',c:'150001',p:92,dc:'Caneta esferográfica, tinta azul, ponta média'},
 {d:S.edit?'Resma de papel A4 75 g/m²':'50 resmas de papel A4',q:50,u:'UN',c:'123456',p:S.edit?96:94,dc:'Papel A4, 75 g/m², branco, resma com 500 folhas'},
 {d:'Fita isolante 20m',q:30,u:'UN',c:'150310',p:88,dc:'Fita isolante, 20 m, PVC, preta'}];
function render(){
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  [['nome',S.nome],['cep',S.cep],['cnpj',S.cnpj],['tel',S.tel],['mail',S.mail],['resp',S.resp],['ta',S.txt]].forEach(([k,v])=>{T('d-'+k+'-v',v);const p=document.getElementById('d-'+k+'-ph');if(p)p.style.display=v?'none':'inline';});
  T('d-cepok',S.cepok?'✅ Endereço encontrado pelo CEP.':'');T('d-end',S.cepok?'Rua Exemplo, 100 — Centro':'');T('d-cid',S.cepok?'Rio de Janeiro / RJ':'');
  $('#d-spin1').classList.toggle('on',S.spin1);$('#d-itens').classList.toggle('on',S.itens);
  $('#d-ittab tbody').innerHTML=IT().map((x,i)=>'<tr id="ir'+(i+1)+'"><td><span class="box on" style="background:#ef4444;border-color:#ef4444;width:13px;height:13px;font-size:9px">✓</span></td><td class="ed" id="idesc'+(i+1)+'">'+x.d+'</td><td>'+x.q+'</td><td>'+x.u+'</td><td><b>'+x.c+'</b></td><td class="good">'+x.p+'%</td><td>'+x.dc+'</td></tr>').join('');
  const falta=[];if(!S.nome)falta.push('nome da OM');if(!S.mail)falta.push('e-mail institucional');if(!S.itens)falta.push('itens');
  $('#d-falta').style.display=falta.length?'block':'none';T('d-falta','Falta preencher: '+falta.join(', ')+'.');
  $('#d-prepara').style.opacity=falta.length?.5:1;
  const et=['','Etapa 1 de 3 — sugerindo o CATMAT de cada item','Etapa 2 de 3 — consultando as vendas recentes no Compras.gov','Etapa 3 de 3 — escolhendo fornecedores e buscando os e-mails'];
  $('#d-prep').classList.toggle('on',S.prep>0&&!S.done);T('d-etapa',et[S.prep]||'');$('#d-pb').style.width=(S.prep/3*100)+'%';
  T('d-st','Item '+Math.min(S.prep,3)+'/3  •  fornecedores com e-mail até agora: '+S.prep*2+'  •  decorrido: 0min '+(S.prep*20)+'s');
  $('#d-ok').style.display=S.done?'block':'none';$('#d-res').classList.toggle('on',S.done);
  if(!S.done)return;
  const F=FORN.filter((f,i)=>!(S.desm&&i===5));
  $('#d-ftab tbody').innerHTML=FORN.map((f,i)=>{const on=!(S.desm&&i===5);return '<tr id="fr'+i+'"><td><span class="box'+(on?' on':'')+'" id="fenv'+i+'" style="'+(on?'background:#ef4444;border-color:#ef4444;':'')+'width:13px;height:13px;font-size:9px">'+(on?'✓':'')+'</span></td><td>'+f.i+'</td><td>'+f.n+'</td><td>'+f.e+'</td><td>'+f.c+'</td><td>'+f.m+'</td></tr>';}).join('');
  $('#d-mets').innerHTML='<div class="met"><div class="k">Fornecedores selecionados</div><div class="v">'+F.length+'</div></div><div class="met"><div class="k">Itens</div><div class="v">3</div></div><div class="met"><div class="k">Mensagens a enviar</div><div class="v">1</div></div>';
  $('#d-testeok').style.display=S.teste?'block':'none';
  $('#d-conf-b').className='box'+(S.conf?' on':'');$('#d-conf-b').style.cssText=S.conf?'background:#ef4444;border-color:#ef4444':'';$('#d-conf-b').textContent=S.conf?'✓':'';
  $('#d-envia').style.opacity=S.conf?1:.5;$('#d-enviado').style.display=S.enviado?'block':'none';
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça a página Cotação Direta',
 b:'A <b>Cotação Direta</b> faz a <b>pesquisa direta com fornecedores</b>: o sistema encontra empresas que <b>venderam recentemente</b> o mesmo item (ou parecido) à Administração, monta a <b>proposta em Word</b> com o CATMAT sugerido e envia <b>uma mensagem única</b>, com os fornecedores em <b>cópia oculta</b>.',
 tip:'💡 A pesquisa direta com fornecedores é uma das fontes previstas na IN SEGES/ME nº 65/2021. Aqui o prazo padrão para resposta é de 5 dias úteis.',
 run:async a=>{a.unring();await a.top();a.ring('#d-head','Pesquisa direta com fornecedores');await a.sleep(3000);a.unring();}},

{short:'Sua OM',t:'Passo 1 — Preencha os dados da sua OM',
 b:'Digite o <b>nome da OM</b>: se ela já foi usada antes, o sistema sugere e <b>preenche o endereço</b>. Para uma OM nova, digite o <b>CEP</b> e o endereço é buscado. Informe também <b>CNPJ</b>, <b>telefone</b>, o(s) <b>e-mail(s) institucional(is)</b> (vários separados por “;”) e o <b>responsável</b> pela assinatura.',
 tip:'💡 O e-mail institucional recebe a <b>cópia da mensagem com o Word anexado</b> e as respostas dos fornecedores.',
 run:async a=>{a.unring();await a.top();await a.scroll('#d-p1',20);await a.click('#d-nome');await a.type('#d-nome-v','Centro de Operações do Abastecimento',40);a.set(S=>S.nome='Centro de Operações do Abastecimento');
  await a.click('#d-cep');await a.type('#d-cep-v','20000-000',90);a.set(S=>{S.cep='20000-000';S.cepok=true;});
  await a.click('#d-cnpj');await a.type('#d-cnpj-v','00.000.000/0001-00',60);a.set(S=>S.cnpj='00.000.000/0001-00');
  await a.click('#d-tel');await a.type('#d-tel-v','(21) 0000-0000',80);a.set(S=>S.tel='(21) 0000-0000');
  await a.click('#d-mail');await a.type('#d-mail-v','cotacao@om.example',60);a.set(S=>S.mail='cotacao@om.example');
  await a.click('#d-resp');await a.type('#d-resp-v','1T (IM) Fulano de Tal – Encarregado da Divisão de Obtenção',35);a.set(S=>S.resp='1T (IM) Fulano de Tal – Encarregado da Divisão de Obtenção');await a.sleep(700);}},

{short:'Itens',t:'Passo 2 — Digite os itens e quantidades',
 b:'Escreva os itens <b>como numa lista de compras</b>, um por linha, com a <b>quantidade</b> ao lado (“- 100”, “50 resmas…”). Prefere planilha? Use a aba <b>📎 Enviar Excel/CSV</b>, sem limite de itens. Clique em <b>Identificar itens</b>.',
 tip:'💡 A quantidade vai para a proposta enviada aos fornecedores: confira antes de seguir.',
 run:async a=>{a.unring();await a.scroll('#d-p2',20);await a.click('#d-ta');await a.type('#d-ta-v',TXT,50);a.set(S=>S.txt=TXT);a.ring('#d-tabx','Ou envie uma planilha',4);await a.sleep(1500);a.unring();
  await a.click('#d-ident',()=>a.set(S=>S.spin1=true));await a.sleep(1500);a.set(S=>{S.spin1=false;S.itens=true;});await a.sleep(500);}},

{short:'CATMAT',t:'Passo 3 — Confira o CATMAT de cada item',
 b:'A tabela mostra o <b>CATMAT mais próximo</b> de cada item e a <b>% de casamento</b> — só entra na proposta a partir de <b>70%</b>. Você pode <b>desmarcar “Usar”</b> para deixar um item de fora e <b>editar a descrição</b>: ao mudar “50 resmas de papel A4” para “Resma de papel A4 75 g/m²”, o CATMAT é <b>casado de novo</b> e a % sobe.',
 tip:'💡 Na lista digitada o CATMAT se atualiza sozinho; na planilha, clique em <b>Atualizar CATMAT</b> depois de editar.',
 run:async a=>{a.unring();await a.scroll('#d-itens',70);a.ring('#d-ittab','Tabela de itens e CATMAT',4);await a.sleep(2000);a.unring();
  await a.click('#idesc2');await a.type('#idesc2','Resma de papel A4 75 g/m²',60);a.set(S=>S.edit=true);a.ring('#ir2','CATMAT casado de novo: 96%',4);await a.sleep(2600);a.unring();}},

{short:'Fornecedores',t:'Passo 4 — Clique em Preparar cotação',
 b:'Em <b>Escolher fornecedores e gerar a proposta</b>, deixe marcada a <b>preferência por fornecedores da mesma cidade e estado</b> da OM, se quiser. Clique em <b>🔎 Preparar cotação</b>: o botão só libera quando <b>nome da OM, e-mail e itens</b> estão preenchidos. O sistema trabalha em <b>3 etapas</b> (CATMAT, vendas recentes no Compras.gov, escolha dos fornecedores e busca dos e-mails).',
 tip:'💡 Não feche nem atualize a página durante o processamento — pode levar alguns minutos, ainda mais com muitos itens.',
 run:async a=>{a.unring();await a.scroll('#d-loc',90);a.ring('#d-loc','Preferência local',4);await a.sleep(1500);a.unring();await a.click('#d-prepara',()=>a.set(S=>S.prep=1));
  for(const n of [1,2,3]){a.set(S=>S.prep=n);await a.sleep(1400);}a.set(S=>S.done=true);await a.sleep(500);await a.scroll('#d-ok',90);a.ring('#d-ok','Pronto!',4);await a.sleep(1800);a.unring();}},

{short:'Revisar lista',t:'Passo 5 — Revise os fornecedores',
 b:'Veja os <b>itens com o CATMAT sugerido</b> e a <b>lista de fornecedores</b>, cada um com o motivo da escolha (“vendeu item igual em 08/2026 — mesma cidade”). <b>Desmarque “Enviar”</b> para tirar alguém, corrija um e-mail ou <b>acrescente uma linha</b> no fim da tabela. O painel mostra quantos fornecedores, itens e mensagens.',
 tip:'💡 Menos de 3 fornecedores com e-mail gera um alerta: a IN SEGES/ME nº 65/2021 recomenda ao menos três. Inclua outros manualmente.',
 run:async a=>{a.unring();await a.scroll('#d-fh',30);a.ring('#d-ftab','Fornecedores que receberão o pedido',4);await a.sleep(2600);a.unring();await a.click('#fenv5',()=>a.set(S=>S.desm=true));a.ring('#d-mets','Contagem atualizada',4);await a.sleep(2400);a.unring();}},

{short:'E-mail',t:'Passo 6 — Revise o e-mail e baixe os arquivos',
 b:'Confira o <b>assunto</b> (com o <b>protocolo</b> do pedido) e o <b>texto do e-mail</b>, que pode ser editado. Baixe a <b>proposta em Word</b> (a mesma que vai anexada) e o <b>comprovante em Excel</b>, com a lista de fornecedores e o registro do envio.',
 tip:'💡 O protocolo identifica o pedido nas respostas dos fornecedores. Guarde o comprovante no processo.',
 run:async a=>{a.unring();await a.scroll('#d-mailtxt',80);a.ring('#d-mailtxt','Texto editável',4);await a.sleep(2400);a.unring();a.ring('#d-docx','Word',4);await a.click('#d-docx',()=>a.toast('✔ Proposta_CD-20261021-A1B2.docx'));a.unring();a.ring('#d-comp','Excel',4);await a.click('#d-comp',()=>a.toast('✔ Comprovante_CD-20261021-A1B2.xlsx'));await a.sleep(700);a.unring();}},

{short:'Enviar',t:'Passo 7 — Teste e envie',
 b:'<b>🧪 Enviar teste só para mim</b> manda a mensagem apenas para o seu e-mail — confira a caixa de entrada (e o spam). Depois, marque <b>“Revisei o texto, a proposta e a lista”</b> e clique em <b>📨 Enviar para os fornecedores</b>: é <b>uma mensagem</b> para você, com a proposta anexada, e os fornecedores em <b>cópia oculta</b> (um não vê o outro).',
 tip:'💡 Se o envio automático não estiver configurado, a página avisa: baixe o Word e a lista e envie por conta própria.',
 run:async a=>{a.unring();await a.scroll('#d-teste',150);await a.click('#d-teste',()=>a.set(S=>S.teste=true));await a.sleep(1200);await a.click('#d-conf',()=>a.set(S=>S.conf=true));await a.click('#d-envia',()=>a.set(S=>S.enviado=true));a.ring('#d-enviado','Enviado',4);await a.sleep(3000);a.unring();}},

{short:'Resumo',t:'Resumo — o caminho completo',
 b:'<b>1)</b> dados da OM; <b>2)</b> itens e quantidades; <b>3)</b> conferir o CATMAT; <b>4)</b> Preparar cotação; <b>5)</b> revisar os fornecedores; <b>6)</b> revisar o e-mail e baixar Word e comprovante; <b>7)</b> testar e enviar. Depois, acompanhe as respostas no e-mail institucional e <b>junte as propostas</b> à pesquisa de preços do processo.',
 tip:'🎉 Fim da aula! Os dados desta aula são fictícios. Para pesquisar preços sem pedir orçamento, use a Cotação ou a Cotação Rápida.',
 run:async a=>{a.unring();await a.top();a.ring('#d-head','Cotação Direta');await a.sleep(2600);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS)
