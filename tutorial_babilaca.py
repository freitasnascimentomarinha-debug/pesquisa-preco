"""Vídeo-aula simulada: como usar O Babilaca (IA) — chat, documentos, checklist, conferência e limite de dispensa."""

from __future__ import annotations

from tutorial_player import montar_player

TITULO = "Como usar O Babilaca (IA)"
DESCRICAO = (
    "Assistente para licitações: chat com fontes, documentos no padrão da Marinha (DFD, ETP, TR, TJDL, ofícios...), "
    "kit do processo, checklist com prazos, conferência automática do processo e limite de dispensa por ramo. "
    "Duração aproximada: 5 min, com narração."
)

_MOCK_CSS = r"""
.pn{display:none}.pn.on{display:block}
.box2{background:rgba(8,26,57,.82);border:1px solid #1e5b9f;border-radius:9px;padding:9px 12px;margin:8px 0;font-size:11.5px}
.gold{border-color:#d4af37}
.msg{border-radius:9px;padding:8px 11px;margin:6px 0;font-size:11.5px;line-height:1.45}
.msg.u{background:#1e3a5f;margin-left:120px}.msg.ia{background:#0b2447;border:1px solid #1e5b9f;margin-right:60px}
.msg.ia small{display:block;color:#93c5fd;margin-top:4px}
table.tb{width:100%;border-collapse:collapse;font-size:10.5px;margin:6px 0}
table.tb th{background:#0f2b52;color:#f8e7a1;text-align:left;padding:4px 5px;border:1px solid #1e3a5f}
table.tb td{padding:4px 5px;border:1px solid #1e3a5f;color:#e2e8f0}
.seg{display:inline-flex;border:1px solid #475569;border-radius:7px;overflow:hidden;font-size:10.5px}
.seg span{padding:3px 8px;color:#cbd5e1}.seg span.on{background:#d4af37;color:#111;font-weight:800}
.ckrow{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e3a5f;padding:6px 0;font-size:11.5px}
.ckrow small{display:block;color:#93c5fd;font-size:10px}
.doc{background:#f8fafc;color:#0f172a;border-radius:8px;padding:10px 14px;font-size:10.5px;line-height:1.45;text-align:center}
.doc .l{text-align:left}.doc b{color:#0f172a}
.met{display:flex;gap:8px}.met div{flex:1;background:#0b2447;border:1px solid #1e5b9f;border-radius:8px;padding:6px;text-align:center}
.met b{display:block;font-size:20px;color:#fde68a}
.ach{border-left:4px solid #ef4444;background:#1f1630;padding:6px 9px;margin:5px 0;border-radius:0 7px 7px 0;font-size:11px}
.ach.y{border-left-color:#f59e0b}
.okm{background:#14532d;border:1px solid #22c55e;color:#dcfce7;border-radius:7px;padding:6px 9px;margin-top:6px;font-size:11.5px}
.erm{background:#450a0a;border:1px solid #ef4444;color:#fee2e2;border-radius:7px;padding:6px 9px;margin-top:6px;font-size:11.5px}
.bar2{height:8px;background:#1e293b;border-radius:4px;overflow:hidden}.bar2 i{display:block;height:100%}
.hid2{display:none}.hid2.on{display:block}
"""

_STAGE_HTML = r"""
<div class="qh" id="b-head"><div class="qs">🧠</div><div><b>O Babilaca (IA)</b><small>Assistente Inteligente para Licitações e Contratações Públicas — Lei 14.133/2021</small></div></div>
<div class="tabs" id="b-tabs"><div id="t0">💬 Chat IA</div><div id="t1">📄 Gerar Documentos</div><div id="t2">📋 Checklist</div><div id="t3">🔎 Conferência</div><div id="t4">⚖️ Limite de Dispensa</div></div>

<div class="pn" id="p0">
  <div class="msg u" id="b-perg"></div>
  <div class="msg ia hid2" id="b-resp">Na dispensa em razão do valor, o limite para compras e outros serviços em 2026 é de R$ 65.492,11 (art. 75, II), e ele vale para a <b>soma do exercício</b> por ramo de atividade (art. 75, §1º)...<small>📚 Fontes consultadas: Lei nº 14.133/2021, art. 75 — link para o texto oficial</small></div>
  <div class="fld" id="b-chatin" style="margin-top:10px"><span class="ph">Pergunte sobre licitações, contratos, legislação...</span></div>
</div>

<div class="pn" id="p1">
  <div class="box2 gold" id="b-om"><b>🏛️ Dados obrigatórios: OM e signatário(s)</b>
    <div class="lbl">📂 Carregar perfil da OM salvo (.json)</div><div class="fld" id="b-perfil"><span id="b-perfil-v" style="font-size:11px"></span><span class="ph" id="b-perfil-ph">Upload</span></div>
    <div class="lbl">Nome da OM por extenso *</div><div class="fld"><span id="b-omv"></span></div>
    <div class="lbl">Signatário *</div><div class="fld"><span id="b-assv"></span></div>
    <div class="btn" style="width:210px;margin-top:6px">💾 Salvar perfil da OM (.json)</div>
  </div>
  <div class="lbl">Documento que deseja preparar</div>
  <div class="fld sel" id="b-tipo"><span id="b-tipo-v">DFD — Documento de Formalização de Demanda</span>
    <div class="dd lg" id="b-tdd"><div>DFD — Documento de Formalização de Demanda</div><div id="b-o-etp">ETP — Estudo Técnico Preliminar</div><div>Mapa de Riscos</div><div>Termo de Referência</div><div>TJDL — Termo de Justificativa de Dispensa</div><div>TJIL — Termo de Justificativa de Inexigibilidade</div><div>Aviso de Contratação Direta</div><div>Ofício — Solicitação de adesão</div><div>Ofício — Manifestação de interesse em IRP</div><div>Mapa Comparativo de Preços</div></div></div>
  <div class="hid2" id="b-etp">
    <div class="lbl">1. Descrição da necessidade *</div><div class="fld"><span id="b-nec"></span></div>
    <div class="lbl">4. Estimativa das quantidades *</div><div class="fld"><span></span><span class="ph">Quantidades com memória de cálculo (art. 18, §1º, IV)</span></div>
    <div class="row3" style="display:flex;gap:8px;margin-top:8px"><div class="btn" style="flex:1">📄 Montar com o que preenchi</div><div class="btn pri" id="b-ia" style="flex:1">🤖 Completar e revisar com IA</div></div>
  </div>
  <div class="hid2" id="b-prev">
    <div class="sec2">📄 Estudo Técnico Preliminar — pré-visualização (editável)</div>
    <div class="doc" id="b-doc">🇧🇷<br><b>MARINHA DO BRASIL</b><br><b>CENTRO DE EXEMPLO DA MARINHA</b><div style="text-align:right">Rio de Janeiro, RJ, 22 de outubro de 2026.</div><b>ESTUDO TÉCNICO PRELIMINAR</b><div class="l"><b>1. DESCRIÇÃO DA NECESSIDADE</b><br>Aquisição de papel A4 para atender às atividades administrativas...</div></div>
    <div style="display:flex;gap:8px;margin-top:6px"><div class="btn" id="b-pdf" style="flex:1">⬇️ Baixar em PDF</div><div class="btn" style="flex:1">📝 Baixar em Word</div></div>
    <div class="box2" id="b-kit"><b>📦 Kit do processo (ZIP) — 3 documento(s) gerado(s) nesta sessão</b><br>01_dfd · 02_etp · 03_termo_referencia + lista de verificação + índice<div class="btn pri" style="width:200px;margin-top:6px">📦 Montar kit</div></div>
  </div>
</div>

<div class="pn" id="p2">
  <div class="lbl">Modalidade ou tipo de processo</div><div class="fld"><span>Dispensa eletrônica (art. 75, I e II)</span></div>
  <div class="box2" id="b-prazo"><b>⏱️ Calculadora de prazos</b> · Edital — bens, menor preço · divulgação em 22/10/2026
    <div class="okm">Primeira data possível para a abertura: <b>04/11/2026 (quarta-feira)</b> — 8 dias úteis (art. 55, I, a). Último dia para impugnação: 29/10/2026.</div></div>
  <div id="b-ck">
    <div class="ckrow"><div><b>1.</b> Documento de Formalização de Demanda (DFD)<small>⚖️ Lei nº 14.133/2021, art. 72, I · 📄 Abrir modelo: DFD</small></div><div class="seg"><span id="s1a">Pendente</span><span id="s1b">Presente</span><span>Não se aplica</span></div></div>
    <div class="ckrow"><div><b>2.</b> Estudo Técnico Preliminar (facultativo no art. 75, I e II)<small>⚖️ IN SEGES/ME nº 58/2022, art. 14</small></div><div class="seg"><span id="s2a">Pendente</span><span>Presente</span><span id="s2c">Não se aplica</span></div></div>
    <div class="ckrow"><div><b>3.</b> Consulta ao CEIS e ao CNEP e certidões<small>⚖️ art. 91, §4º · ↗️ Consulta CNPJ</small></div><div class="seg"><span class="on">Pendente</span><span>Presente</span><span>Não se aplica</span></div></div>
  </div>
  <div class="okm" id="b-ckok">⚠️ 1/2 itens aplicáveis presentes · 🖨️ Baixar PDF · 📝 Word · 💾 Salvar conferência (.json)</div>
</div>

<div class="pn" id="p3">
  <div class="lbl">Arquivos do processo (PDF com texto ou Word)</div><div class="fld" id="b-up"><span id="b-up-v"></span><span class="ph" id="b-up-ph">Upload</span></div>
  <div class="btn pri" id="b-conf" style="margin-top:8px">🔎 Conferir processo</div>
  <div class="hid2" id="b-res">
    <div class="met" style="margin-top:8px"><div><b>2</b>🔴 Graves</div><div><b>3</b>🟡 A corrigir</div><div><b>1</b>🔵 Sugestões</div><div><b>11/18</b>Itens encontrados</div></div>
    <div class="ach" id="b-a1">🔴 <b>Certidão de regularidade vencida na data de referência</b><br>Validade 01/04/2026; referência 22/04/2026 · 📍 processo.pdf, p. 5</div>
    <div class="ach">🔴 <b>Autorização anterior ao parecer jurídico</b><br>Autorização em 15/04/2026 e parecer em 20/04/2026 · 📍 p. 7-8</div>
    <div class="ach y">🟡 <b>Valor estimado diferente entre o mapa de preços e o TR</b><br>Mapa: R$ 50.000,00; TR: R$ 52.000,00 · 📍 p. 2-3</div>
    <div class="btn" id="b-levar" style="margin-top:6px">📋 Levar o resultado para a aba Checklist</div>
  </div>
</div>

<div class="pn" id="p4">
  <div style="display:flex;gap:8px"><div style="flex:2"><div class="lbl">UASG da unidade gestora</div><div class="fld"><span id="b-uasg"></span></div></div>
  <div style="flex:1"><div class="lbl">Exercício</div><div class="fld"><span>2026</span></div></div></div>
  <div class="btn pri" id="b-ver" style="margin-top:8px">⚖️ Verificar o exercício</div>
  <div class="hid2" id="b-frac">
    <div class="met" style="margin-top:8px"><div><b>52</b>Dispensas</div><div><b>174</b>Ramos</div><div><b>1</b>🔴 Ultrapassados</div><div><b>1</b>🟡 Acima de 80%</div></div>
    <table class="tb" id="b-ftab"><tr><th>Situação</th><th>Ramo de atividade</th><th>Base</th><th>Total</th><th>Uso do limite</th></tr>
      <tr><td>🟡</td><td>MANTEIGA</td><td>PDM (CATMAT)</td><td>R$ 53.925,00</td><td><div class="bar2"><i style="width:82%;background:#f59e0b"></i></div></td></tr>
      <tr><td>🟢</td><td>QUEIJO</td><td>PDM (CATMAT)</td><td>R$ 38.482,58</td><td><div class="bar2"><i style="width:59%;background:#22c55e"></i></div></td></tr>
      <tr><td>🟢</td><td>PAPEL A4</td><td>PDM (CATMAT)</td><td>R$ 12.000,00</td><td><div class="bar2"><i style="width:18%;background:#22c55e"></i></div></td></tr></table>
    <div class="lbl">🧮 Simular uma nova dispensa</div><div class="fld" id="b-sim"><span id="b-sim-v"></span></div>
    <div class="erm hid2" id="b-simr">Ramo <b>MANTEIGA</b>: já contratado R$ 53.925,00 + esta dispensa R$ 15.000,00 = <b>R$ 68.925,00</b> de R$ 65.492,11. <b>Ultrapassa o limite</b>: avalie licitar ou outra hipótese.</div>
  </div>
</div>
<div class="foot">Idealizado e Desenvolvido por COpAb - Sobressalentes - V1.2026</div>
"""

_STATE_JS = r"""
let S;
function resetS(){S={tab:0,perg:'',resp:false,perfil:false,tdd:false,tipo:'DFD — Documento de Formalização de Demanda',etp:false,prev:false,s1:'a',s2:'a',up:false,res:false,uasg:'',frac:false,sim:false};}
function render(){
  for(let i=0;i<5;i++){$('#t'+i).classList.toggle('on',S.tab===i);$('#p'+i).classList.toggle('on',S.tab===i);}
  const T=(id,t)=>{const e=document.getElementById(id);if(e)e.textContent=t;};
  T('b-perg',S.perg);$('#b-perg').style.display=S.perg?'block':'none';$('#b-resp').classList.toggle('on',S.resp);
  T('b-perfil-v',S.perfil?'perfil_om.json':'');$('#b-perfil-ph').style.display=S.perfil?'none':'inline';
  T('b-omv',S.perfil?'Centro de Exemplo da Marinha':'');T('b-assv',S.perfil?'FULANO DE TAL · Capitão-Tenente (IM) · Encarregado':'');
  T('b-tipo-v',S.tipo);$('#b-tdd').classList.toggle('on',S.tdd);$('#b-etp').classList.toggle('on',S.etp);$('#b-prev').classList.toggle('on',S.prev);
  $('#s1a').classList.toggle('on',S.s1==='a');$('#s1b').classList.toggle('on',S.s1==='b');
  $('#s2a').classList.toggle('on',S.s2==='a');$('#s2c').classList.toggle('on',S.s2==='c');
  T('b-up-v',S.up?'processo_dispensa.pdf':'');$('#b-up-ph').style.display=S.up?'none':'inline';$('#b-res').classList.toggle('on',S.res);
  T('b-uasg',S.uasg);$('#b-frac').classList.toggle('on',S.frac);$('#b-simr').classList.toggle('on',S.sim);
}
"""

_STEPS_JS = r"""
window.__STEPS__=[
{short:'A tela',t:'Conheça O Babilaca',
 b:'O <b>Babilaca</b> é o assistente do sistema para licitações e contratos. Ele tem cinco abas: <b>Chat IA</b>, para tirar dúvidas; <b>Gerar Documentos</b>, para montar as peças do processo; <b>Checklist</b>, para conferir o que falta; <b>Conferência</b>, que lê o processo e aponta erros; e <b>Limite de Dispensa</b>, que verifica o fracionamento.',
 tip:'💡 O Babilaca é ferramenta de apoio: revise sempre os documentos antes de assinar.',
 run:async a=>{a.unring();await a.top();a.ring('#b-tabs','Cinco abas',4);await a.sleep(3200);a.unring();}},

{short:'Chat',t:'Passo 1 — Pergunte no Chat IA',
 b:'Na aba <b>Chat IA</b>, escreva sua dúvida sobre licitações, contratos ou legislação. A resposta cita <b>somente fontes verificadas</b> da base jurídica do sistema, como a Lei nº 14.133/2021, instruções normativas e acórdãos do TCU, com o link de cada uma.',
 tip:'💡 Se a base não tiver a referência, o Babilaca diz que não tem, em vez de inventar um artigo.',
 run:async a=>{a.unring();await a.click('#t0',()=>a.set(S=>S.tab=0));await a.click('#b-chatin');a.set(S=>S.perg='Qual o limite da dispensa por valor em 2026?');await a.sleep(900);a.set(S=>S.resp=true);a.ring('#b-resp','Resposta com fontes',4);await a.sleep(3200);a.unring();}},

{short:'Dados da OM',t:'Passo 2 — Dados da OM e perfil salvo',
 b:'Na aba <b>Gerar Documentos</b>, preencha primeiro os <b>dados obrigatórios</b>: nome da OM, cidade, UF e os <b>signatários</b>. Eles saem no cabeçalho e na assinatura de todos os documentos. Clique em <b>Salvar perfil da OM</b> para baixar um arquivo; nas próximas vezes, é só <b>carregar o perfil</b> e tudo é preenchido de uma vez.',
 tip:'💡 O sistema não guarda seus dados no servidor: o perfil fica com você.',
 run:async a=>{a.unring();await a.click('#t1',()=>a.set(S=>S.tab=1));await a.top();await a.click('#b-perfil',()=>a.set(S=>S.perfil=true));a.toast('Perfil da OM carregado.');a.ring('#b-om','OM e signatários',4);await a.sleep(3000);a.unring();}},

{short:'Modelos',t:'Passo 3 — Escolha o documento',
 b:'Em <b>Documento que deseja preparar</b>, escolha o modelo: <b>DFD</b>, <b>ETP</b>, <b>Mapa de Riscos</b>, <b>Termo de Referência</b>, <b>TJDL</b>, <b>TJIL</b>, <b>Aviso de Contratação Direta</b>, <b>ofícios</b> de adesão e de IRP, <b>Mapa Comparativo</b> e outros. Cada modelo segue a estrutura da lei e mostra o fundamento de cada seção.',
 tip:'💡 O ETP traz os 13 elementos do art. 18, §1º, e marca os obrigatórios do §2º.',
 run:async a=>{a.unring();await a.scroll('#b-tipo',120);await a.click('#b-tipo',()=>a.set(S=>S.tdd=true));await a.sleep(1200);await a.click('#b-o-etp',()=>a.set(S=>{S.tdd=false;S.tipo='ETP — Estudo Técnico Preliminar';S.etp=true;}));await a.sleep(800);}},

{short:'Preencher',t:'Passo 4 — Preencha e use a IA',
 b:'Preencha as seções que você já sabe. Depois escolha: <b>Montar com o que preenchi</b>, que usa só o seu texto, ou <b>Completar e revisar com IA</b>, que melhora a redação e completa o que faltar com base no contexto e nos anexos que você enviar. O que a IA não souber fica como lacuna, sem inventar dados.',
 tip:'💡 Os campos da OM, da UASG e do contato já vêm preenchidos a partir do perfil.',
 run:async a=>{a.unring();await a.scroll('#b-etp',100);await a.type('#b-nec','Aquisição de papel A4 para as atividades administrativas',45);await a.click('#b-ia',()=>a.set(S=>S.prev=true));a.toast('O Babilaca está redigindo o documento…');await a.sleep(1200);}},

{short:'Baixar',t:'Passo 5 — Revise e baixe no padrão da Marinha',
 b:'O documento aparece numa <b>pré-visualização editável</b>. Ajuste o texto e baixe em <b>PDF</b> ou <b>Word</b>, já no padrão gráfico da Marinha: Armas Nacionais, MARINHA DO BRASIL, nome da OM, local e data, tabelas, paginação e assinatura.',
 tip:'💡 Os ofícios saem no formato do MaTDoc: Ofício para OM da Marinha e Ofício Externo para órgão de fora.',
 run:async a=>{a.unring();await a.scroll('#b-prev',60);a.ring('#b-doc','Padrão MaTDoc',4);await a.sleep(3000);a.unring();a.ring('#b-pdf','PDF ou Word',4);await a.sleep(1600);a.unring();}},

{short:'Kit',t:'Passo 6 — Kit do processo',
 b:'Depois de gerar as peças, use o <b>Kit do processo</b>: ele junta num arquivo ZIP todos os documentos da sessão, já numerados na ordem do processo, em PDF e Word, com a lista de verificação, o relatório de conferência e um índice.',
 tip:'💡 O kit usa o texto já editado de cada documento.',
 run:async a=>{a.unring();await a.scroll('#b-kit',100);a.ring('#b-kit','Tudo num ZIP',4);await a.sleep(3200);a.unring();}},

{short:'Checklist',t:'Passo 7 — Confira o processo no Checklist',
 b:'Na aba <b>Checklist</b>, escolha a modalidade. Cada item mostra o <b>fundamento legal</b> e atalhos para o modelo ou a página certa. Marque cada um como <b>Presente</b>, <b>Pendente</b> ou <b>Não se aplica</b>. A lista sai em PDF e pode ser salva para continuar depois.',
 tip:'💡 Os limites de dispensa de 2026 já estão atualizados pelo Decreto nº 12.807/2025.',
 run:async a=>{a.unring();await a.click('#t2',()=>a.set(S=>S.tab=2));await a.top();await a.scroll('#b-ck',80);await a.click('#s1b',()=>a.set(S=>S.s1='b'));await a.click('#s2c',()=>a.set(S=>S.s2='c'));a.ring('#b-ckok','Andamento e PDF',4);await a.sleep(2200);a.unring();}},

{short:'Prazos',t:'Passo 8 — Calculadora de prazos',
 b:'Ainda no Checklist, a <b>Calculadora de prazos</b> conta os <b>dias úteis</b> da lei: prazo do edital, aviso de dispensa, IRP, impugnação, recursos, divulgação no PNCP e sanções. Ela desconta fins de semana e feriados nacionais e mostra o artigo de cada prazo.',
 tip:'💡 Feriados estaduais e municipais não entram na conta: confira o calendário local.',
 run:async a=>{a.unring();await a.scroll('#b-prazo',80);a.ring('#b-prazo','Dias úteis',4);await a.sleep(3400);a.unring();}},

{short:'Conferência',t:'Passo 9 — Conferência automática do processo',
 b:'Na aba <b>Conferência</b>, envie o processo em PDF e clique em <b>Conferir processo</b>. O sistema identifica as peças e aponta inconsistências por gravidade: certidão vencida, CNPJ diferente entre proposta e certidões, valores que não batem, autorização antes do parecer, lacunas não preenchidas e itens que faltam, com a <b>página</b> de cada achado.',
 tip:'💡 É uma triagem: não substitui a análise do agente de contratação nem o parecer jurídico. PDF escaneado sem texto não é lido.',
 run:async a=>{a.unring();await a.click('#t3',()=>a.set(S=>S.tab=3));await a.top();await a.click('#b-up',()=>a.set(S=>S.up=true));await a.click('#b-conf',()=>a.set(S=>S.res=true));await a.sleep(600);a.ring('#b-a1','Achado com a página',4);await a.sleep(3000);a.unring();a.ring('#b-levar','Leva ao Checklist',4);await a.sleep(1600);a.unring();}},

{short:'Limite',t:'Passo 10 — Limite de dispensa por ramo',
 b:'Na aba <b>Limite de Dispensa</b>, informe a <b>UASG</b> e o ano. O sistema soma as dispensas por valor publicadas no PNCP, <b>por ramo de atividade</b>, e mostra quanto já foi usado do limite e quanto ainda cabe. Isso ajuda a evitar o <b>fracionamento</b> de despesa (art. 75, §1º).',
 tip:'💡 O total do ramo pode preencher automaticamente o campo “já contratado no exercício” do TJDL.',
 run:async a=>{a.unring();await a.click('#t4',()=>a.set(S=>S.tab=4));await a.top();await a.type('#b-uasg','795380',110);a.set(S=>S.uasg='795380');await a.click('#b-ver',()=>a.set(S=>S.frac=true));await a.sleep(600);a.ring('#b-ftab','Uso do limite por ramo',4);await a.sleep(3000);a.unring();}},

{short:'Simular',t:'Passo 11 — Simule uma nova dispensa',
 b:'Em <b>Simular uma nova dispensa</b>, digite a descrição do item e o valor. O sistema encontra o ramo, soma com o que já foi contratado e diz se <b>cabe no limite</b> ou se <b>ultrapassa</b>.',
 tip:'🎉 Fim da aula! <b>Resumo:</b> 1) pergunte no chat; 2) carregue o perfil da OM; 3) escolha o modelo; 4) preencha ou use a IA; 5) revise e baixe; 6) monte o kit; 7) confira no checklist; 8) calcule os prazos; 9) confira o processo; 10 e 11) verifique o limite de dispensa.',
 run:async a=>{a.unring();await a.scroll('#b-sim',120);await a.type('#b-sim-v','MANTEIGA, TIPO: SEM SAL — R$ 15.000,00',45);a.set(S=>S.sim=true);a.ring('#b-simr','Ultrapassa o limite',4);await a.sleep(3400);a.unring();}}
];
"""


def html() -> str:
    return montar_player(TITULO, DESCRICAO, _STAGE_HTML, _MOCK_CSS, _STATE_JS, _STEPS_JS, audio_id="babilaca")
