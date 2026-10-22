"""Vídeo-aula simulada: como usar O Babilaca (IA) — um assunto por passo, com cada elemento destacado na tela."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar O Babilaca (IA)"
DESCRICAO = (
    "Passo a passo do assistente: chat com fontes, dados da OM, modelos de documentos, IA, padrão da Marinha, kit do "
    "processo, checklist, calculadora de prazos, conferência automática e limite de dispensa por ramo e por subelemento. "
    "Duração aproximada: 9 min, com narração, em 25 passos."
)

_MOCK_CSS = r"""
.pn{display:none}.pn.on{display:block}
.box2{background:rgba(8,26,57,.82);border:1px solid #1e5b9f;border-radius:9px;padding:9px 12px;margin:8px 0;font-size:11.5px}
.gold{border-color:#d4af37}
.msg{border-radius:9px;padding:8px 11px;margin:6px 0;font-size:11.5px;line-height:1.45}
.msg.u{background:#1e3a5f;margin-left:140px}.msg.ia{background:#0b2447;border:1px solid #1e5b9f;margin-right:40px}
.fontes{display:block;color:#93c5fd;margin-top:6px;border-top:1px dashed #1e5b9f;padding-top:4px}
table.tb{width:100%;border-collapse:collapse;font-size:10.5px;margin:6px 0}
table.tb th{background:#0f2b52;color:#f8e7a1;text-align:left;padding:4px 5px;border:1px solid #1e3a5f}
table.tb td{padding:4px 5px;border:1px solid #1e3a5f;color:#e2e8f0}
.seg{display:inline-flex;border:1px solid #475569;border-radius:7px;overflow:hidden;font-size:10.5px}
.seg span{padding:3px 8px;color:#cbd5e1}.seg span.on{background:#d4af37;color:#111;font-weight:800}
.ckrow{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e3a5f;padding:6px 0;font-size:11.5px;gap:8px}
.ckrow small{display:block;color:#93c5fd;font-size:10px}
.mini{display:inline-block;border:1px solid #475569;border-radius:6px;padding:2px 7px;font-size:10.5px;margin-top:3px}
.doc{background:#f8fafc;color:#0f172a;border-radius:8px;padding:10px 14px;font-size:10.5px;line-height:1.45;text-align:center}
.doc .l{text-align:left}.doc b{color:#0f172a}.doc .sg{margin-top:14px}
.met{display:flex;gap:8px}.met div{flex:1;background:#0b2447;border:1px solid #1e5b9f;border-radius:8px;padding:6px;text-align:center;font-size:11px}
.met b{display:block;font-size:20px;color:#fde68a}
.ach{border-left:4px solid #ef4444;background:#1f1630;padding:6px 9px;margin:5px 0;border-radius:0 7px 7px 0;font-size:11px}
.ach.y{border-left-color:#f59e0b}
.okm{background:#14532d;border:1px solid #22c55e;color:#dcfce7;border-radius:7px;padding:6px 9px;margin-top:6px;font-size:11.5px}
.erm{background:#450a0a;border:1px solid #ef4444;color:#fee2e2;border-radius:7px;padding:6px 9px;margin-top:6px;font-size:11.5px}
.bar2{height:8px;background:#1e293b;border-radius:4px;overflow:hidden}.bar2 i{display:block;height:100%}
.hid2{display:none}.hid2.on{display:block}
.row2{display:flex;gap:8px}.row2>div{flex:1}
.subtabs{display:flex;gap:14px;font-size:11px;border-bottom:1px solid #1e3a5f;margin:8px 0 4px}
.subtabs span{padding:4px 2px;color:#9fb6d8}.subtabs span.on{color:#fde68a;border-bottom:2px solid #d4af37;font-weight:700}
.edc{background:#1e293b;border:1px dashed #d4af37}
.zip{font-family:monospace;font-size:10.5px;color:#cbd5e1;line-height:1.6}
"""

_STAGE_HTML = r"""
<div class="qh" id="b-head"><div class="qs">🧠</div><div><b>O Babilaca (IA)</b><small>Assistente Inteligente para Licitações e Contratações Públicas — Lei 14.133/2021</small></div></div>
<div class="tabs" id="b-tabs"><div id="t0">💬 Chat IA</div><div id="t1">📄 Gerar Documentos</div><div id="t2">📋 Checklist</div><div id="t3">🔎 Conferência</div><div id="t4">⚖️ Limite de Dispensa</div></div>

<!-- CHAT -->
<div class="pn" id="p0">
  <div class="msg u hid2" id="b-perg">Qual o limite da dispensa por valor em 2026?</div>
  <div class="msg ia hid2" id="b-resp"><span id="b-resp1">Na dispensa em razão do valor, o limite para compras e outros serviços em 2026 é de <b>R$ 65.492,11</b> (art. 75, II) e, para obras, serviços de engenharia e manutenção de veículos, <b>R$ 130.984,20</b> (art. 75, I).</span> <span id="b-resp2">O limite vale para a <b>soma do exercício</b> por ramo de atividade (art. 75, §1º).</span>
    <span class="fontes" id="b-fontes">📚 Fontes consultadas: Lei nº 14.133/2021, art. 75 — link para o texto oficial</span></div>
  <div class="fld" id="b-chatin" style="margin-top:10px"><span id="b-chatin-v"></span><span class="ph" id="b-chatin-ph">Pergunte sobre licitações, contratos, legislação...</span></div>
</div>

<!-- DOCUMENTOS -->
<div class="pn" id="p1">
  <div class="box2 gold" id="b-om"><b>🏛️ Dados obrigatórios: OM e signatário(s)</b>
    <div class="lbl">📂 Carregar perfil da OM salvo (.json)</div><div class="fld" id="b-perfil"><span id="b-perfil-v" style="font-size:11px"></span><span class="ph" id="b-perfil-ph">Upload</span></div>
    <div class="lbl">Nome da OM por extenso *</div><div class="fld" id="b-omf"><span id="b-omv"></span></div>
    <div class="row2"><div><div class="lbl">Cidade *</div><div class="fld"><span id="b-cid"></span></div></div><div style="flex:.4"><div class="lbl">UF *</div><div class="fld"><span id="b-uf"></span></div></div></div>
    <div class="lbl">Signatário: nome · posto · função *</div><div class="fld" id="b-assf"><span id="b-assv"></span></div>
    <div id="b-compl"><div class="lbl">Dados complementares: UASG · endereço · contato</div><div class="fld"><span id="b-complv"></span></div></div>
    <div class="btn" id="b-salvar" style="width:210px;margin-top:6px">💾 Salvar perfil da OM (.json)</div>
  </div>
  <div class="lbl">Documento que deseja preparar</div>
  <div class="fld sel" id="b-tipo"><span id="b-tipo-v">DFD — Documento de Formalização de Demanda</span>
    <div class="dd lg" id="b-tdd"><div>DFD — Documento de Formalização de Demanda</div><div id="b-o-etp">ETP — Estudo Técnico Preliminar</div><div>Mapa de Riscos</div><div>Termo de Referência</div><div>TJDL — Termo de Justificativa de Dispensa</div><div>TJIL — Termo de Justificativa de Inexigibilidade</div><div>Aviso de Contratação Direta</div><div>Ofício — Solicitação de adesão</div><div>Ofício — Manifestação de interesse em IRP</div><div>Mapa Comparativo de Preços</div><div>Relatório de vantajosidade da adesão</div></div></div>
  <div class="hid2" id="b-etp">
    <div class="cap2">Base: Lei nº 14.133/2021, art. 18, §§1º e 2º; IN SEGES/ME nº 58/2022. Seções com * são obrigatórias.</div>
    <div class="lbl" id="b-s1l">1. Descrição da necessidade *</div><div class="fld" id="b-s1"><span id="b-nec"></span></div>
    <div class="lbl">2. Previsão no plano de contratações anual</div><div class="fld"><span class="ph">Item do PCA ou justificativa da ausência</span></div>
    <div class="lbl" id="b-s4l">4. Estimativa das quantidades *</div><div class="fld"><span class="ph">Quantidades com memória de cálculo (art. 18, §1º, IV)</span></div>
    <div class="box2" id="b-ctx"><b>🤖 Contexto e anexos para a IA (opcional)</b><div class="fld" style="margin-top:4px"><span id="b-ctxv"></span></div><div class="mini">📎 Anexar PDF, planilha ou Word</div></div>
    <div class="row2" style="margin-top:8px"><div class="btn" id="b-mont">📄 Montar com o que preenchi</div><div class="btn pri" id="b-ia">🤖 Completar e revisar com IA</div></div>
  </div>
  <div class="hid2" id="b-prev">
    <div class="sec2">📄 Estudo Técnico Preliminar — pré-visualização (editável)</div>
    <div class="fld edc" id="b-edit" style="height:auto;min-height:34px;white-space:normal;font-size:10.5px">### 1. DESCRIÇÃO DA NECESSIDADE<br><span id="b-editv">Aquisição de papel A4 para atender às atividades administrativas da OM...</span></div>
    <div class="doc" id="b-doc"><span id="b-timbre">🇧🇷<br><b>MARINHA DO BRASIL</b><br><b>CENTRO DE EXEMPLO DA MARINHA</b></span><div style="text-align:right" id="b-data">Rio de Janeiro, RJ, 22 de outubro de 2026.</div><b id="b-titdoc">ESTUDO TÉCNICO PRELIMINAR</b><div class="l"><b>1. DESCRIÇÃO DA NECESSIDADE</b><br><span id="b-docv">Aquisição de papel A4 para atender às atividades administrativas da OM...</span></div><div class="sg" id="b-assin">FULANO DE TAL<br>Capitão-Tenente (IM)<br>Encarregado da Divisão de Obtenção</div></div>
    <div class="row2" style="margin-top:6px"><div class="btn" id="b-pdf">⬇️ Baixar em PDF</div><div class="btn" id="b-word">📝 Baixar em Word</div></div>
    <div class="box2" id="b-kit"><b>📦 Kit do processo (ZIP) — 3 documento(s) gerado(s) nesta sessão</b>
      <div class="zip">01_dfd.pdf · 01_dfd.docx<br>02_etp.pdf · 02_etp.docx<br>03_termo_referencia.pdf · 03_termo_referencia.docx<br>90_lista_de_verificacao.pdf · 00_indice.txt</div>
      <div class="btn pri" id="b-montkit" style="width:200px;margin-top:6px">📦 Montar kit</div><div class="btn hid2" id="b-baixkit" style="width:260px;margin-top:6px">⬇️ Baixar kit do processo (.zip)</div></div>
  </div>
</div>

<!-- CHECKLIST -->
<div class="pn" id="p2">
  <div class="lbl">Modalidade ou tipo de processo</div><div class="fld" id="b-mod"><span>Dispensa eletrônica (art. 75, I e II)</span></div>
  <div class="box2" id="b-prazo"><b>⏱️ Calculadora de prazos (dias úteis — Lei nº 14.133/2021)</b>
    <div class="row2"><div><div class="lbl">Prazo</div><div class="fld" id="b-pz"><span id="b-pzv">Edital — bens, menor preço ou maior desconto</span></div></div><div style="flex:.6"><div class="lbl">Data de divulgação do edital</div><div class="fld"><span>22/10/2026</span></div></div></div>
    <div class="okm hid2" id="b-pzr">Primeira data possível para a abertura: <b>04/11/2026 (quarta-feira)</b> — 8 dias úteis depois de 22/10/2026. Fundamento: art. 55, I, a.</div>
    <div class="cap2 hid2" id="b-pzi" style="color:#bfdbfe">Com a abertura nessa data, o último dia para impugnação seria <b>29/10/2026</b> (3 dias úteis antes — art. 164).</div></div>
  <div id="b-ck">
    <div class="ckrow" id="b-ck1"><div><b>1.</b> Documento de Formalização de Demanda (DFD)<small id="b-fund1">⚖️ Lei nº 14.133/2021, art. 72, I</small><span class="mini" id="b-atalho">📄 Abrir modelo: DFD</span></div><div class="seg" id="b-seg1"><span id="s1a">Pendente</span><span id="s1b">Presente</span><span>Não se aplica</span></div></div>
    <div class="ckrow"><div><b>2.</b> Estudo Técnico Preliminar (facultativo no art. 75, I e II)<small>⚖️ IN SEGES/ME nº 58/2022, art. 14</small></div><div class="seg"><span id="s2a">Pendente</span><span>Presente</span><span id="s2c">Não se aplica</span></div></div>
    <div class="ckrow"><div><b>3.</b> Consulta ao CEIS e ao CNEP e certidões<small>⚖️ art. 91, §4º</small><span class="mini">↗️ Consulta CNPJ</span></div><div class="seg"><span class="on">Pendente</span><span>Presente</span><span>Não se aplica</span></div></div>
  </div>
  <div class="okm" id="b-ckok">⚠️ 1/2 itens aplicáveis presentes</div>
  <div class="row2" style="margin-top:6px" id="b-ckdl"><div class="btn">🖨️ Baixar PDF</div><div class="btn">📝 Baixar Word</div><div class="btn">💾 Salvar conferência (.json)</div></div>
</div>

<!-- CONFERÊNCIA -->
<div class="pn" id="p3">
  <div class="lbl">Arquivos do processo (PDF com texto ou Word)</div><div class="fld" id="b-up"><span id="b-up-v"></span><span class="ph" id="b-up-ph">Upload</span></div>
  <div class="cap2" id="b-cons">☑ Consultar também sanções (CEIS/CNEP/CEPIM) e SICAF do fornecedor identificado</div>
  <div class="btn pri" id="b-conf" style="margin-top:6px">🔎 Conferir processo</div>
  <div class="hid2" id="b-res">
    <div class="met" style="margin-top:8px" id="b-met"><div><b>2</b>🔴 Graves</div><div><b>3</b>🟡 A corrigir</div><div><b>1</b>🔵 Sugestões</div><div><b>11/18</b>Itens encontrados</div></div>
    <div class="ach" id="b-a1">🔴 <b>Certidão de regularidade vencida na data de referência</b><br>Validade 01/04/2026; referência 22/04/2026 · 📍 processo.pdf, p. 5</div>
    <div class="ach" id="b-a2">🔴 <b>Autorização anterior ao parecer jurídico</b><br>Autorização em 15/04/2026 e parecer em 20/04/2026 · 📍 p. 7-8</div>
    <div class="ach y" id="b-a3">🟡 <b>Valor estimado diferente entre o mapa de preços e o TR</b><br>Mapa: R$ 50.000,00; TR: R$ 52.000,00 · 📍 p. 2-3</div>
    <div class="row2" style="margin-top:6px"><div class="btn" id="b-levar">📋 Levar o resultado para a aba Checklist</div><div class="btn" id="b-rel">🖨️ Relatório em PDF</div></div>
  </div>
</div>

<!-- LIMITE DE DISPENSA -->
<div class="pn" id="p4">
  <div class="row2"><div style="flex:2"><div class="lbl">UASG da unidade gestora</div><div class="fld" id="b-uasgf"><span id="b-uasg"></span></div></div>
  <div><div class="lbl">Exercício</div><div class="fld"><span>2026</span></div></div></div>
  <div class="btn pri" id="b-ver" style="margin-top:8px">⚖️ Verificar o exercício</div>
  <div class="hid2" id="b-frac">
    <div class="met" style="margin-top:8px" id="b-fmet"><div><b>77</b>Dispensas</div><div><b>157</b>📦 Ramos de material</div><div><b>16</b>🛠️ Ramos de serviço</div><div><b>1</b>🔴 Ultrapassados</div><div><b>2</b>🟡 Acima de 80%</div></div>
    <div class="subtabs" id="b-ftabs"><span id="f0">📦 Materiais (157)</span><span id="f1">🛠️ Serviços (16)</span><span id="f2">🧾 Por natureza de despesa</span></div>
    <div class="hid2" id="b-fm"><table class="tb"><tr><th>Situação</th><th>Ramo de atividade</th><th>Subelemento (editável)</th><th>Total</th><th>Uso</th></tr>
      <tr><td>🟡</td><td>MANTEIGA</td><td>3.3.90.30.07 – Gêneros de alimentação</td><td>R$ 53.925,00</td><td><div class="bar2"><i style="width:82%;background:#f59e0b"></i></div></td></tr>
      <tr><td>🟢</td><td>PAPEL A4</td><td>3.3.90.30.16 – Material de expediente</td><td>R$ 12.000,00</td><td><div class="bar2"><i style="width:18%;background:#22c55e"></i></div></td></tr></table></div>
    <div class="hid2" id="b-fs"><table class="tb" id="b-fstab"><tr><th>Situação</th><th>Serviço (CATSER)</th><th>Subelemento (editável)</th><th>Total</th><th>Uso</th></tr>
      <tr><td>🟡</td><td>TRADUÇÃO / INTERPRETAÇÃO SIMULTÂNEA</td><td>3.3.90.39.05 – Serviços técnicos profissionais</td><td>R$ 61.250,00</td><td><div class="bar2"><i style="width:94%;background:#f59e0b"></i></div></td></tr>
      <tr><td>🟢</td><td>REVISÃO VEÍCULO - QUILOMETRAGEM</td><td>3.3.90.39.19 – Manutenção e conservação de veículos</td><td>R$ 4.783,35</td><td><div class="bar2"><i style="width:7%;background:#22c55e"></i></div></td></tr>
      <tr><td>🟢</td><td>PRESTAÇÃO DE SERVIÇOS DE LAVANDERIA</td><td class="edc" id="b-subed"><span id="b-subv">3.3.90.39.79 – Serviço de apoio administrativo</span></td><td>R$ 7.176,00</td><td><div class="bar2"><i style="width:11%;background:#22c55e"></i></div></td></tr></table></div>
    <div class="hid2" id="b-fn"><table class="tb" id="b-fntab"><tr><th>Situação</th><th>Natureza / subelemento</th><th>Ramos</th><th>Total</th><th>Uso</th></tr>
      <tr><td>🔴</td><td>4.4.90.52.58 – Equipamentos de mergulho e salvamento</td><td>2</td><td>R$ 124.743,69</td><td><div class="bar2"><i style="width:100%;background:#ef4444"></i></div></td></tr>
      <tr><td>🟡</td><td>3.3.90.39.05 – Serviços técnicos profissionais</td><td>1</td><td>R$ 61.250,00</td><td><div class="bar2"><i style="width:94%;background:#f59e0b"></i></div></td></tr>
      <tr><td>🟡</td><td>3.3.90.30.07 – Gêneros de alimentação</td><td>12</td><td>R$ 58.410,00</td><td><div class="bar2"><i style="width:89%;background:#f59e0b"></i></div></td></tr></table></div>
    <div class="lbl">🧮 Simular uma nova dispensa</div><div class="fld" id="b-sim"><span id="b-sim-v"></span></div>
    <div class="erm hid2" id="b-simr">Ramo <b>MANTEIGA</b>: já contratado R$ 53.925,00 + esta dispensa R$ 15.000,00 = <b>R$ 68.925,00</b> de R$ 65.492,11. <b>Ultrapassa o limite</b>.</div>
    <div class="erm hid2" id="b-simr2">Subelemento <b>3.3.90.30.07 – Gêneros de alimentação</b>: já contratado R$ 58.410,00 + esta dispensa = <b>R$ 73.410,00</b>. <b>Ultrapassa o limite pelo subelemento.</b></div>
  </div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
let S;
function resetS(){S={tab:0,perg:false,resp:false,chatin:'',perfil:false,om:'',cid:'',uf:'',ass:'',compl:'',tdd:false,tipo:'DFD — Documento de Formalização de Demanda',etp:false,prev:false,kit:false,s1:'a',s2:'a',pz:false,up:false,res:false,uasg:'',frac:false,ftab:0,sub:'',sim:false};}
function render(){
  for(let i=0;i<5;i++){$('#t'+i).classList.toggle('on',S.tab===i);$('#p'+i).classList.toggle('on',S.tab===i);}
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  $('#b-perg').classList.toggle('on',S.perg);$('#b-resp').classList.toggle('on',S.resp);
  T('b-chatin-v',S.chatin);$('#b-chatin-ph').style.display=S.chatin?'none':'inline';
  T('b-perfil-v',S.perfil?'perfil_om.json':'');$('#b-perfil-ph').style.display=S.perfil?'none':'inline';
  T('b-omv',S.om);T('b-cid',S.cid);T('b-uf',S.uf);T('b-assv',S.ass);T('b-complv',S.compl);
  T('b-tipo-v',S.tipo);$('#b-tdd').classList.toggle('on',S.tdd);$('#b-etp').classList.toggle('on',S.etp);$('#b-prev').classList.toggle('on',S.prev);
  $('#b-montkit').style.display=S.kit?'none':'block';$('#b-baixkit').classList.toggle('on',S.kit);
  $('#s1a').classList.toggle('on',S.s1==='a');$('#s1b').classList.toggle('on',S.s1==='b');
  $('#s2a').classList.toggle('on',S.s2==='a');$('#s2c').classList.toggle('on',S.s2==='c');
  $('#b-pzr').classList.toggle('on',S.pz);$('#b-pzi').classList.toggle('on',S.pz);
  T('b-up-v',S.up?'processo_dispensa.pdf':'');$('#b-up-ph').style.display=S.up?'none':'inline';$('#b-res').classList.toggle('on',S.res);
  T('b-uasg',S.uasg);$('#b-frac').classList.toggle('on',S.frac);
  for(let i=0;i<3;i++){$('#f'+i).classList.toggle('on',S.ftab===i);}
  $('#b-fm').classList.toggle('on',S.ftab===0);$('#b-fs').classList.toggle('on',S.ftab===1);$('#b-fn').classList.toggle('on',S.ftab===2);
  if(S.sub)T('b-subv',S.sub);
  $('#b-simr').classList.toggle('on',S.sim);$('#b-simr2').classList.toggle('on',S.sim);
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça O Babilaca',
 b:'O <b>Babilaca</b> é o assistente do sistema para licitações e contratos. Ele tem cinco abas. Vamos ver uma de cada vez: o <b>Chat IA</b>, os <b>Documentos</b>, o <b>Checklist</b>, a <b>Conferência</b> do processo e o <b>Limite de Dispensa</b>.',
 tip:'💡 O Babilaca é ferramenta de apoio: revise sempre os documentos antes de assinar.',
 run:async a=>{a.unring();await a.top();a.ring('#b-head','O assistente',4);await a.sleep(2500);for(const [i,l] of [[0,'Chat'],[1,'Documentos'],[2,'Checklist'],[3,'Conferência'],[4,'Limite de Dispensa']]){a.ring('#t'+i,l,4);await a.sleep(1500);}a.unring();}},

{short:'Perguntar',t:'Chat — Faça a sua pergunta',
 b:'Na aba <b>Chat IA</b>, escreva a dúvida no campo de baixo, do jeito que você perguntaria a um colega. Por exemplo: qual o limite da dispensa por valor em 2026? Depois é só enviar.',
 tip:'💡 Você também pode anexar um PDF ou planilha no chat para a IA considerar.',
 run:async a=>{a.unring();await a.click('#t0',()=>a.set(S=>S.tab=0));await a.top();await a.click('#b-chatin');await a.type('#b-chatin-v','Qual o limite da dispensa por valor em 2026?',55);a.set(S=>{S.chatin='Qual o limite da dispensa por valor em 2026?';});await a.sleep(800);a.set(S=>{S.chatin='';S.perg=true;});a.ring('#b-perg','Pergunta enviada',4);await a.sleep(2500);a.unring();}},

{short:'Resposta',t:'Chat — Leia a resposta e as fontes',
 b:'A resposta vem organizada e cita <b>somente fontes verificadas</b> da base jurídica do sistema: a Lei nº 14.133/2021, instruções normativas e acórdãos do TCU. No fim aparecem as <b>fontes consultadas</b>, com o link de cada uma. Se a base não tiver a referência, o Babilaca avisa, em vez de inventar um artigo.',
 tip:'💡 Confira o artigo citado clicando no link da fonte.',
 run:async a=>{a.unring();a.set(S=>S.resp=true);a.ring('#b-resp1','Resposta',4);await a.sleep(3500);a.unring();a.ring('#b-resp2','Detalhe importante',4);await a.sleep(3000);a.unring();a.ring('#b-fontes','Fontes verificadas',4);await a.sleep(3500);a.unring();}},

{short:'Dados da OM',t:'Documentos — Preencha os dados da OM',
 b:'Na aba <b>Gerar Documentos</b>, comece pelos <b>dados obrigatórios</b>: o nome da OM por extenso, a cidade, a UF e o signatário, com nome, posto e função. Eles vão no <b>cabeçalho</b> e na <b>assinatura</b> de todos os documentos. Enquanto faltar algum, os botões de gerar ficam bloqueados.',
 tip:'💡 Com mais de um signatário, informe do mais antigo para o mais moderno (MaTDoc 1.11).',
 run:async a=>{a.unring();await a.click('#t1',()=>a.set(S=>S.tab=1));await a.top();await a.click('#b-omf');await a.type('#b-omv','Centro de Exemplo da Marinha',45);a.set(S=>S.om='Centro de Exemplo da Marinha');await a.type('#b-cid','Rio de Janeiro',45);a.set(S=>S.cid='Rio de Janeiro');await a.type('#b-uf','RJ',90);a.set(S=>S.uf='RJ');await a.click('#b-assf');await a.type('#b-assv','FULANO DE TAL · Capitão-Tenente (IM) · Encarregado',35);a.set(S=>S.ass='FULANO DE TAL · Capitão-Tenente (IM) · Encarregado');a.ring('#b-om','Dados obrigatórios',4);await a.sleep(2200);a.unring();}},

{short:'Perfil',t:'Documentos — Salve e carregue o perfil da OM',
 b:'Para não digitar tudo de novo, clique em <b>Salvar perfil da OM</b>: o sistema baixa um arquivo com os dados da OM e dos signatários. Nas próximas vezes, use <b>Carregar perfil da OM salvo</b> e tudo é preenchido de uma vez. O sistema não guarda seus dados no servidor: o perfil fica com você.',
 tip:'💡 Guarde o arquivo do perfil numa pasta da Divisão para toda a equipe usar.',
 run:async a=>{a.unring();await a.scroll('#b-salvar',140);a.ring('#b-salvar','Baixa o perfil',4);await a.sleep(3000);a.unring();await a.scroll('#b-perfil',120);await a.click('#b-perfil',()=>a.set(S=>S.perfil=true));a.toast('Perfil da OM carregado.');a.ring('#b-perfil','Carrega tudo de uma vez',4);await a.sleep(3000);a.unring();}},

{short:'Complementares',t:'Documentos — Dados complementares',
 b:'Os <b>dados complementares</b> são opcionais: UASG, endereço e telefone ou e-mail da OM. Com eles, o sistema <b>preenche sozinho</b> vários campos dos modelos: a UASG do aviso, o endereço do Ofício Externo, o ponto de contato dos ofícios e o órgão da minuta de contrato.',
 tip:'💡 Os campos preenchidos automaticamente continuam editáveis.',
 run:async a=>{a.unring();await a.scroll('#b-compl',140);await a.type('#b-complv','765000 · Rua Exemplo, 100 · (21) 0000-0000',40);a.set(S=>S.compl='765000 · Rua Exemplo, 100 · (21) 0000-0000');a.ring('#b-compl','Preenchem os modelos',4);await a.sleep(3200);a.unring();}},

{short:'Modelo',t:'Documentos — Escolha o modelo',
 b:'Em <b>Documento que deseja preparar</b>, abra a lista. Há modelos para todo o processo: <b>DFD</b>, <b>ETP</b>, <b>Mapa de Riscos</b>, <b>Termo de Referência</b>, <b>TJDL</b> e <b>TJIL</b>, <b>Aviso de Contratação Direta</b>, os <b>ofícios</b> de adesão e de IRP, o <b>Mapa Comparativo</b> e outros. Aqui vamos escolher o <b>ETP</b>.',
 tip:'💡 Cada modelo segue a estrutura da lei e mostra o fundamento de cada seção.',
 run:async a=>{a.unring();await a.scroll('#b-tipo',120);await a.click('#b-tipo',()=>a.set(S=>S.tdd=true));a.ring('#b-tdd','Modelos disponíveis',4);await a.sleep(4500);a.unring();await a.click('#b-o-etp',()=>a.set(S=>{S.tdd=false;S.tipo='ETP — Estudo Técnico Preliminar';S.etp=true;}));await a.sleep(1200);}},

{short:'Seções',t:'Documentos — Preencha as seções',
 b:'O ETP aparece dividido nas seções do art. 18, §1º, da Lei nº 14.133/2021. As marcadas com <b>asterisco</b> são obrigatórias. Escreva o que você já sabe em cada seção. Não precisa preencher tudo: o que ficar em branco vira lacuna, ou é completado pela IA.',
 tip:'💡 Seção opcional do ETP deixada em branco vira a justificativa exigida pelo §2º.',
 run:async a=>{a.unring();await a.scroll('#b-etp',90);a.ring('#b-s1l','Obrigatória (*)',4);await a.sleep(2200);a.unring();await a.click('#b-s1');await a.type('#b-nec','Aquisição de papel A4 para as atividades administrativas',45);a.ring('#b-s4l','Outra obrigatória',4);await a.sleep(2200);a.unring();}},

{short:'Contexto IA',t:'Documentos — Dê contexto à IA',
 b:'No quadro <b>Contexto e anexos para a IA</b>, conte o que a IA deve saber: o histórico, os números que você já tem, a urgência. Também dá para <b>anexar</b> um PDF, uma planilha ou um Word, por exemplo a pesquisa de preços. A IA usa esse material para redigir.',
 tip:'💡 Quanto melhor o contexto, menos lacunas sobram no documento.',
 run:async a=>{a.unring();await a.scroll('#b-ctx',110);await a.type('#b-ctxv','Consumo médio de 50 resmas por mês; estoque acaba em dezembro.',40);a.ring('#b-ctx','Contexto e anexos',4);await a.sleep(2600);a.unring();}},

{short:'Gerar',t:'Documentos — Montar ou completar com IA',
 b:'Agora escolha um dos dois botões. <b>Montar com o que preenchi</b> usa só o seu texto. <b>Completar e revisar com IA</b> melhora a redação e completa o que faltar com base no contexto. O que a IA não souber fica como lacuna, sem inventar valores, nomes ou datas.',
 tip:'💡 Use "Montar" quando o texto já está pronto e você só quer o documento formatado.',
 run:async a=>{a.unring();await a.scroll('#b-mont',150);a.ring('#b-mont','Só o seu texto',4);await a.sleep(2600);a.unring();a.ring('#b-ia','Com a IA',4);await a.sleep(2200);a.unring();await a.click('#b-ia',()=>a.set(S=>S.prev=true));a.toast('O Babilaca está redigindo o documento…');await a.sleep(1500);}},

{short:'Editar',t:'Documentos — Revise e edite o texto',
 b:'O documento aparece numa <b>caixa de texto editável</b>. Leia com calma, corrija o que precisar e complete as lacunas. Tudo o que você mudar aqui vale para o PDF e para o Word.',
 tip:'💡 Use ### para títulos de item, a) para alíneas e | Coluna | Coluna | para tabelas.',
 run:async a=>{a.unring();await a.scroll('#b-edit',90);a.ring('#b-edit','Texto editável',4);await a.sleep(3500);a.unring();}},

{short:'Padrão MB',t:'Documentos — O padrão gráfico da Marinha',
 b:'O documento sai no padrão gráfico da Marinha, conforme o MaTDoc: as <b>Armas Nacionais</b>, MARINHA DO BRASIL e o <b>nome da OM</b> no topo; o <b>local e data</b> à direita; o <b>título</b>; o texto com itens, tabelas e paginação; e a <b>assinatura</b> no final.',
 tip:'💡 Os ofícios saem no formato do MaTDoc: Ofício para OM da Marinha e Ofício Externo para órgão de fora.',
 run:async a=>{a.unring();await a.scroll('#b-doc',70);a.ring('#b-timbre','Timbre',4);await a.sleep(2400);a.unring();a.ring('#b-data','Local e data',4);await a.sleep(1800);a.unring();a.ring('#b-titdoc','Título',4);await a.sleep(1500);a.unring();a.ring('#b-assin','Assinatura',4);await a.sleep(2000);a.unring();}},

{short:'Baixar',t:'Documentos — Baixe em PDF ou Word',
 b:'Clique em <b>Baixar em PDF</b> para o documento final, ou em <b>Baixar em Word</b> se quiser continuar editando no seu computador. Os dois saem com a mesma formatação.',
 tip:'💡 O Word abre também no LibreOffice, sem perder a formatação.',
 run:async a=>{a.unring();await a.scroll('#b-pdf',150);a.ring('#b-pdf','PDF',4);await a.sleep(2000);a.unring();a.ring('#b-word','Word',4);await a.sleep(2000);a.unring();}},

{short:'Kit',t:'Documentos — Kit do processo',
 b:'Depois de gerar as peças, use o <b>Kit do processo</b>. Ele junta num arquivo ZIP todos os documentos da sessão, <b>numerados na ordem do processo</b>, em PDF e Word, com a lista de verificação, o relatório de conferência e um índice. Clique em <b>Montar kit</b> e depois em <b>Baixar</b>.',
 tip:'💡 O kit usa o texto já editado de cada documento.',
 run:async a=>{a.unring();await a.scroll('#b-kit',90);a.ring('#b-kit','Tudo num ZIP',4);await a.sleep(3000);a.unring();await a.click('#b-montkit',()=>a.set(S=>S.kit=true));a.ring('#b-baixkit','Pronto para baixar',4);await a.sleep(2200);a.unring();}},

{short:'Checklist',t:'Checklist — Escolha a modalidade',
 b:'Na aba <b>Checklist</b>, escolha a modalidade do processo, por exemplo, dispensa eletrônica. A lista mostra os documentos e providências exigidos, e cada item traz o seu <b>fundamento legal</b> logo abaixo.',
 tip:'💡 Os limites de dispensa de 2026 já estão atualizados pelo Decreto nº 12.807/2025.',
 run:async a=>{a.unring();await a.click('#t2',()=>a.set(S=>S.tab=2));await a.top();a.ring('#b-mod','Modalidade',4);await a.sleep(2200);a.unring();await a.scroll('#b-ck',90);a.ring('#b-fund1','Fundamento legal',4);await a.sleep(3000);a.unring();}},

{short:'Marcar itens',t:'Checklist — Marque cada item',
 b:'Para cada item, marque <b>Presente</b>, <b>Pendente</b> ou <b>Não se aplica</b>. Os itens que não se aplicam saem da conta do percentual. O botão <b>Abrir modelo</b> leva direto ao documento certo na aba Documentos, e os atalhos com seta abrem a página do sistema que resolve o item.',
 tip:'💡 Salve a conferência em .json para continuar outro dia.',
 run:async a=>{a.unring();await a.scroll('#b-ck',90);await a.click('#s1b',()=>a.set(S=>S.s1='b'));await a.sleep(800);await a.click('#s2c',()=>a.set(S=>S.s2='c'));await a.sleep(800);a.ring('#b-atalho','Atalho para o modelo',4);await a.sleep(2400);a.unring();a.ring('#b-ckdl','PDF, Word e .json',4);await a.sleep(2200);a.unring();}},

{short:'Prazos',t:'Checklist — Calculadora de prazos',
 b:'A <b>Calculadora de prazos</b> conta os <b>dias úteis</b> da lei: edital, aviso de dispensa, IRP, impugnação, recursos, divulgação no PNCP e sanções. Escolha o prazo e a data-base. Ela mostra a data final com o dia da semana e o artigo e, no caso do edital, também o último dia para impugnação.',
 tip:'💡 Feriados estaduais e municipais não entram na conta: confira o calendário local.',
 run:async a=>{a.unring();await a.scroll('#b-prazo',80);a.ring('#b-pz','Escolha o prazo',4);await a.sleep(2200);a.unring();a.set(S=>S.pz=true);a.ring('#b-pzr','Data final',4);await a.sleep(3000);a.unring();a.ring('#b-pzi','Impugnação',4);await a.sleep(2200);a.unring();}},

{short:'Conferir',t:'Conferência — Envie o processo',
 b:'Na aba <b>Conferência</b>, envie o processo em PDF, que pode ser um arquivo só ou vários, na ordem. Deixe marcada a consulta de <b>sanções e SICAF</b> do fornecedor e clique em <b>Conferir processo</b>.',
 tip:'💡 PDF escaneado, sem texto selecionável, não é lido.',
 run:async a=>{a.unring();await a.click('#t3',()=>a.set(S=>S.tab=3));await a.top();await a.click('#b-up',()=>a.set(S=>S.up=true));await a.sleep(800);a.ring('#b-cons','Sanções e SICAF',4);await a.sleep(2200);a.unring();await a.click('#b-conf',()=>a.set(S=>S.res=true));await a.sleep(900);}},

{short:'Achados',t:'Conferência — Leia as inconsistências',
 b:'O resultado mostra quantos achados são <b>graves</b>, <b>a corrigir</b> e <b>sugestões</b>. Cada achado diz o problema e a <b>página</b> onde está: certidão vencida, autorização antes do parecer, valores que não batem entre o mapa e o TR, CNPJ diferente e lacunas não preenchidas.',
 tip:'💡 É uma triagem: não substitui a análise do agente de contratação nem o parecer jurídico.',
 run:async a=>{a.unring();await a.scroll('#b-met',70);a.ring('#b-met','Resumo',4);await a.sleep(2500);a.unring();a.ring('#b-a1','Grave, com a página',4);await a.sleep(2600);a.unring();a.ring('#b-a2','Datas fora de ordem',4);await a.sleep(2200);a.unring();a.ring('#b-a3','Valores diferentes',4);await a.sleep(2200);a.unring();}},

{short:'Resultado',t:'Conferência — Leve ao checklist e baixe o relatório',
 b:'Com <b>Levar o resultado para a aba Checklist</b>, os itens encontrados já ficam marcados como presentes, com a página. E o <b>relatório da conferência</b> sai em PDF ou Word, no padrão da Marinha.',
 tip:'💡 O relatório também entra no Kit do processo.',
 run:async a=>{a.unring();await a.scroll('#b-levar',140);a.ring('#b-levar','Marca o checklist',4);await a.sleep(2600);a.unring();a.ring('#b-rel','Relatório',4);await a.sleep(2000);a.unring();}},

{short:'Limite',t:'Limite de Dispensa — Verifique a UASG',
 b:'Na aba <b>Limite de Dispensa</b>, informe a <b>UASG</b> e o ano e clique em <b>Verificar o exercício</b>. O sistema busca todas as dispensas por valor publicadas no PNCP e mostra quantas são, quantos ramos de <b>material</b> e de <b>serviço</b> existem e quantos já passaram do limite.',
 tip:'💡 A UASG vem preenchida a partir do perfil da OM.',
 run:async a=>{a.unring();await a.click('#t4',()=>a.set(S=>S.tab=4));await a.top();await a.click('#b-uasgf');await a.type('#b-uasg','740002',110);a.set(S=>S.uasg='740002');await a.click('#b-ver',()=>a.set(S=>S.frac=true));await a.sleep(700);a.ring('#b-fmet','Resumo do exercício',4);await a.sleep(3000);a.unring();}},

{short:'Materiais',t:'Limite de Dispensa — Materiais',
 b:'A aba <b>Materiais</b> soma o que foi contratado por <b>família do catálogo</b> (PDM), que é o ramo de atividade. A barra mostra quanto do limite já foi usado: <b>verde</b>, dentro; <b>amarelo</b>, acima de 80%; <b>vermelho</b>, ultrapassado. Ao lado aparece o <b>subelemento</b> de despesa sugerido.',
 tip:'💡 O limite do art. 75 vale para a soma do exercício por ramo (art. 75, §1º).',
 run:async a=>{a.unring();await a.scroll('#b-ftabs',90);a.ring('#f0','Materiais',4);await a.sleep(2000);a.unring();a.ring('#b-fm','Soma por família',4);await a.sleep(3500);a.unring();}},

{short:'Serviços',t:'Limite de Dispensa — Serviços e subelemento',
 b:'Na aba <b>Serviços</b>, os serviços são agrupados pelo <b>catálogo CATSER</b>. A coluna <b>Subelemento</b> é editável: o sistema sugere a natureza e o subelemento, e você pode <b>corrigir</b> conforme a classificação da sua OM. Por exemplo: trocar apoio administrativo por outros serviços de terceiros, pessoa jurídica.',
 tip:'💡 A API pública não informa a natureza de despesa dos itens: por isso a sugestão deve ser conferida.',
 run:async a=>{a.unring();await a.click('#f1',()=>a.set(S=>S.ftab=1));await a.scroll('#b-fstab',90);a.ring('#b-fstab','Serviços pelo CATSER',4);await a.sleep(2800);a.unring();await a.click('#b-subed');a.set(S=>S.sub='3.3.90.39.99 – Outros serviços de terceiros – PJ');a.ring('#b-subed','Subelemento editável',4);await a.sleep(2800);a.unring();}},

{short:'Natureza',t:'Limite de Dispensa — Soma por natureza de despesa',
 b:'A aba <b>Por natureza de despesa</b> soma tudo por <b>subelemento</b>: 3.3.90.30, material de consumo; 3.3.90.39, serviços de pessoa jurídica; e 4.4.90.52, equipamentos e material permanente. É o controle que muitas OM usam, pela classificação do SIAFI. A soma acompanha os subelementos que você escolheu.',
 tip:'💡 Despesas de TIC têm naturezas próprias (3.3.90.40 e 4.4.90.40).',
 run:async a=>{a.unring();await a.click('#f2',()=>a.set(S=>S.ftab=2));await a.scroll('#b-fntab',90);a.ring('#b-fntab','Soma por subelemento',4);await a.sleep(4500);a.unring();}},

{short:'Simular',t:'Limite de Dispensa — Simule uma nova dispensa',
 b:'Antes de abrir uma nova dispensa, use <b>Simular</b>: digite a descrição do item e o valor. O sistema soma com o que já foi contratado e responde duas coisas: se cabe no limite pelo <b>ramo de atividade</b> e se cabe pelo <b>subelemento</b>. O total do ramo ou do subelemento também pode preencher o TJDL.',
 tip:'🎉 Fim da aula! Resumo: chat com fontes; dados e perfil da OM; modelos, IA, edição e download no padrão da Marinha; kit; checklist e prazos; conferência; e limite de dispensa por ramo e por subelemento.',
 run:async a=>{a.unring();await a.scroll('#b-sim',130);await a.type('#b-sim-v','MANTEIGA, TIPO: SEM SAL — R$ 15.000,00',45);a.set(S=>S.sim=true);a.ring('#b-simr','Pelo ramo',4);await a.sleep(3000);a.unring();a.ring('#b-simr2','Pelo subelemento',4);await a.sleep(3000);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="babilaca")
