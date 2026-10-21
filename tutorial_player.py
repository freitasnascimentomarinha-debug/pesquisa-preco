"""Player de vídeo-aula simulado (HTML/JS autocontido) para a página "Aprendendo a usar".

Cada vídeo é uma simulação animada da tela real (cursor, digitação, cliques, rolagem, destaques) com
legenda didática e narração opcional. Para criar um vídeo novo, escreva um módulo ``tutorial_<ferramenta>.py``
com ``TITULO``, ``DESCRICAO``, ``STAGE_HTML`` (a tela simulada, 760x540) e ``STEPS_JS`` (a lista de passos) e
use :func:`montar_player`.
"""

from __future__ import annotations

import json

LARGURA_TELA, ALTURA_TELA = 760, 540
ALTURA_IFRAME = 1010

_CSS = r"""
:root{--navy:#001a4d;--panel:#0a2540;--gold:#d4af37;--yellow:#facc15;--txt:#f8fafc;--mut:#b6cae2;--line:#1e5b9f}
*{box-sizing:border-box}
html,body{margin:0;background:transparent;color:var(--txt);font-family:"Segoe UI",Roboto,Arial,sans-serif}
.player{max-width:920px;margin:0 auto;background:#00123a;border:2px solid var(--yellow);border-radius:14px;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.45)}
.player:fullscreen{max-width:none;border-radius:0;display:flex;flex-direction:column;justify-content:center;background:#00123a}
.player:fullscreen .stagewrap{max-width:calc((100vh - 270px)*1.4074)}
.topbar{display:flex;align-items:center;gap:.6rem;padding:.55rem .9rem;background:var(--yellow);color:#111;font-weight:800;font-size:.92rem}
.topbar small{font-weight:600;opacity:.8;margin-left:auto}
.stagewrap{position:relative;width:100%;aspect-ratio:760/540;overflow:hidden;background:var(--navy);margin:0 auto}
.stage{position:absolute;left:0;top:0;width:760px;height:540px;transform-origin:0 0;overflow:hidden;background:var(--navy);font-size:13px;color:var(--txt)}
.stage.nofx *{transition:none!important;animation:none!important}
#page{position:absolute;left:0;top:0;width:760px;padding:14px 18px 40px;transition:transform calc(var(--mv,.65s)*1.23) cubic-bezier(.3,.7,.3,1)}
.cursor{position:absolute;left:380px;top:270px;width:22px;height:22px;z-index:50;pointer-events:none;transition:left var(--mv,.65s) cubic-bezier(.4,.1,.2,1),top var(--mv,.65s) cubic-bezier(.4,.1,.2,1);filter:drop-shadow(1px 2px 2px rgba(0,0,0,.6))}
.cursor svg{display:block;transition:transform .12s}
.cursor.down svg{transform:scale(.8)}
.cursor .rip{position:absolute;left:-9px;top:-9px;width:40px;height:40px;border-radius:50%;border:3px solid var(--yellow);opacity:0;transform:scale(.3)}
.cursor.down .rip{animation:rip .45s ease-out}
@keyframes rip{0%{opacity:.95;transform:scale(.3)}100%{opacity:0;transform:scale(1.3)}}
.ring{position:absolute;z-index:40;border:3px solid var(--yellow);border-radius:9px;box-shadow:0 0 0 4000px rgba(0,8,30,.0),0 0 18px rgba(250,204,21,.8);pointer-events:none;opacity:0;transition:all calc(var(--mv,.65s)*.7) ease}
.ring.on{opacity:1;animation:pulse 1.4s ease-in-out infinite}
@keyframes pulse{50%{box-shadow:0 0 0 4000px rgba(0,8,30,.0),0 0 30px rgba(250,204,21,1)}}
.ringlabel{position:absolute;z-index:41;background:var(--yellow);color:#111;font-weight:800;font-size:12px;padding:3px 9px;border-radius:6px;pointer-events:none;opacity:0;transition:all calc(var(--mv,.65s)*.7) ease;white-space:nowrap}
.ringlabel.on{opacity:1}
.toast{position:absolute;z-index:60;right:14px;bottom:14px;background:#14532d;border:1px solid #22c55e;color:#dcfce7;padding:9px 14px;border-radius:8px;font-weight:700;font-size:12.5px;opacity:0;transform:translateY(12px);transition:all .35s}
.toast.on{opacity:1;transform:none}
.ribbon{position:absolute;z-index:55;left:0;top:0;background:rgba(250,204,21,.95);color:#111;font-size:10.5px;font-weight:800;padding:2px 10px;border-bottom-right-radius:8px}
.poster{position:absolute;inset:0;z-index:70;background:radial-gradient(circle at 50% 40%,rgba(0,26,77,.78),rgba(0,10,40,.96));display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:.5rem;padding:1rem;cursor:pointer}
.poster.hide{display:none}
.poster h2{margin:.2rem 0 0;color:var(--yellow);font-size:clamp(15px,4.2vw,26px)}
.poster p{margin:0;color:var(--mut);font-size:clamp(11px,2.6vw,14px);max-width:560px}
.playbtn{width:clamp(54px,14vw,86px);height:clamp(54px,14vw,86px);border-radius:50%;background:var(--yellow);display:flex;align-items:center;justify-content:center;box-shadow:0 0 30px rgba(250,204,21,.6);transition:transform .2s}
.poster:hover .playbtn{transform:scale(1.08)}
.playbtn svg{width:42%;height:42%;margin-left:8%}
.bar{height:6px;background:#0b2a63;cursor:pointer;position:relative}
.bar i{display:block;height:100%;width:0;background:var(--yellow);transition:width .25s}
.ctrl{display:flex;flex-wrap:wrap;align-items:center;gap:.4rem;padding:.55rem .7rem;background:#031642;border-top:1px solid var(--line)}
.ctrl button,.ctrl select{background:#0a2a63;color:#fff;border:1px solid #2b6cb0;border-radius:7px;padding:.38rem .7rem;font-size:.82rem;font-weight:700;cursor:pointer}
.ctrl button:hover{border-color:var(--yellow)}
.ctrl button.main{background:var(--yellow);color:#111;border-color:var(--yellow)}
.ctrl .sp{flex:1}
.ctrl label{font-size:.78rem;color:var(--mut);display:flex;align-items:center;gap:.3rem}
.cap{padding:.8rem 1rem 1rem;background:#031642;border-top:1px solid var(--line);min-height:150px}
.cap .n{color:var(--yellow);font-size:.74rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.cap h3{margin:.15rem 0 .35rem;font-size:1.08rem;color:#fff}
.cap .b{color:#dbe7f7;font-size:.92rem;line-height:1.5}
.cap .tip{margin-top:.55rem;background:rgba(250,204,21,.1);border-left:4px solid var(--yellow);padding:.45rem .7rem;border-radius:0 7px 7px 0;color:#fde68a;font-size:.84rem;line-height:1.4}
.cap .tip:empty{display:none}
.chips{display:flex;gap:.35rem;overflow-x:auto;padding:.55rem .7rem;background:#00123a;border-top:1px solid var(--line)}
.chips button{flex:0 0 auto;background:#0a2a63;color:#cfe0f7;border:1px solid #2b6cb0;border-radius:999px;padding:.28rem .7rem;font-size:.74rem;font-weight:700;cursor:pointer;white-space:nowrap}
.chips button.on{background:var(--yellow);color:#111;border-color:var(--yellow)}
.chips button.done{border-color:#22c55e;color:#bbf7d0}
"""

_MOCK_CSS = r"""
.hdr{background:linear-gradient(135deg,#001a4d,#0033cc);border:1px solid rgba(96,165,250,.45);border-radius:10px;text-align:center;padding:12px}
.hdr .l{color:var(--gold);font-weight:800;letter-spacing:2px;font-size:12px}.hdr .s{font-size:26px;font-weight:900;color:#fff;margin:2px 0}.hdr .u{color:#bfdbfe;font-size:10.5px;letter-spacing:1.5px}
.orient{background:var(--panel);border-left:5px solid var(--gold);border-radius:8px;padding:9px 12px;margin:10px 0}.orient b{color:var(--gold)}
.sec{color:var(--gold);font-size:17px;font-weight:800;margin:16px 0 8px}
.cat{background:#fff;color:#1f2937;border-radius:8px;overflow:hidden;border:1px solid #cbd5e1}
.cat .cb{background:#1d4ed8;color:#fff;padding:6px 12px;font-weight:700;font-size:12px}
.cat .sb{display:flex;gap:6px;padding:10px 12px}
.cat .inp{flex:1;border:1px solid #94a3b8;border-radius:6px;padding:7px 9px;min-height:30px;font-size:13px;color:#111}
.cat .go{background:#1d4ed8;color:#fff;border-radius:6px;padding:7px 12px;font-weight:700}
.cat .res{padding:0 12px 10px;display:none}.cat .res.on{display:block}
.cat .it{border:1px solid #cbd5e1;border-radius:6px;padding:7px 9px;margin-top:6px;display:flex;justify-content:space-between;gap:8px;font-size:12px}
.cat .it.sel{border-color:#1d4ed8;background:#dbeafe}.cat .it b{color:#1d4ed8}
.frm{display:grid;grid-template-columns:1fr 2fr 1fr;gap:10px;align-items:end}
.lbl{font-size:11.5px;color:#dbe7f7;margin-bottom:4px}
.fld{background:rgba(7,20,42,.8);border:1px solid #2b6cb0;border-radius:7px;padding:8px 10px;min-height:34px;position:relative;font-size:13px}
.fld .ph{color:#7e93b3}.fld.sel:after{content:"▾";position:absolute;right:9px;top:8px;color:#9fb6d8}
.dd{position:absolute;left:-1px;right:-1px;top:36px;background:#0b2447;border:1px solid #2b6cb0;border-radius:7px;z-index:5;display:none;overflow:hidden}
.dd.on{display:block}.dd div{padding:8px 10px}.dd div.h{background:#1d4ed8}
.btn{background:#1b2a47;border:1px solid #3b4d70;border-radius:8px;text-align:center;padding:8px 10px;font-weight:700;color:#fff;font-size:12.5px}
.btn.dis{opacity:.5}
.spin{display:none;align-items:center;gap:8px;margin-top:10px;color:var(--mut)}.spin.on{display:flex}
.spin i{width:16px;height:16px;border:3px solid #2b6cb0;border-top-color:var(--yellow);border-radius:50%;animation:sp .8s linear infinite}
@keyframes sp{to{transform:rotate(360deg)}}
#results{display:none}#results.on{display:block}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.chipbox{display:flex;flex-wrap:wrap;gap:5px}
.uf{background:#ef4444;color:#fff;border-radius:6px;padding:3px 8px;font-weight:700;font-size:12px}.uf b{margin-left:6px;cursor:pointer}
.ck{display:flex;align-items:center;gap:8px;margin-top:6px}
.box{width:17px;height:17px;border:2px solid #7e93b3;border-radius:4px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;color:#fff;flex:0 0 auto}
.box.on{background:#ef4444;border-color:#ef4444}
.interv{background:var(--panel);border-left:4px solid var(--gold);border-radius:6px;padding:8px 10px;margin-top:8px}.interv b{color:var(--gold)}
.slider{height:6px;background:#ef4444;border-radius:4px;margin:12px 4px 6px;position:relative}
.cards{display:grid;grid-template-columns:1fr 1fr .6fr .6fr;gap:10px;align-items:stretch}
.card{background:linear-gradient(135deg,#0a2540,#164863);border-left:5px solid var(--gold);border-radius:8px;padding:12px;text-align:center}
.card .k{color:var(--gold);font-size:11px;font-weight:800;letter-spacing:1px}.card .v{font-size:28px;font-weight:800;margin-top:4px}
.dl{display:flex;align-items:center;justify-content:center;text-align:center;font-size:11.5px}
.band{background:var(--panel);border-left:5px solid var(--gold);border-radius:8px;padding:9px 12px;margin-top:10px;display:none}.band.on{display:block}.band b{color:var(--gold)}
table{width:100%;border-collapse:collapse;background:#0b2447;border:1px solid var(--line);font-size:11.5px}
th{background:#12356b;color:#dbe7f7;text-align:left;padding:6px 7px;font-weight:700;border-bottom:1px solid var(--line)}
td{padding:6px 7px;border-bottom:1px solid #123768}tr.sel td{background:rgba(250,204,21,.16)}
.st{text-align:center}.st th{text-align:center}.st td{font-weight:800;font-size:13px}
.frow{display:flex;gap:10px;margin-top:10px}.frow .btn{flex:0 0 auto;padding:8px 16px}
.newp{margin-top:18px;background:linear-gradient(135deg,#0a2540,#164863);border-left:5px solid var(--gold);border-radius:8px;padding:12px;text-align:center;color:var(--gold);font-weight:800}
.foot{margin-top:22px;border-top:1px solid #0033cc;padding-top:12px;text-align:center;color:var(--gold);font-size:11px}
"""

_JS = r"""
const STAGE_W=760,STAGE_H=540;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const stage=$('#stage'),wrap=$('#wrap'),page=$('#page'),cursor=$('#cursor'),ring=$('#ring'),ringl=$('#ringl'),toastEl=$('#toast');
let scale=1,token=0,paused=true,speed=1,FAST=false,cur=-1,narr=false,started=false,running=false,speechP=null;
const STEPS=window.__STEPS__;
class Cancel{}
function fit(){scale=wrap.clientWidth/STAGE_W;stage.style.transform='scale('+scale+')';}
new ResizeObserver(fit).observe(wrap);fit();
const raw=ms=>new Promise(r=>setTimeout(r,ms));
function chk(tk){if(tk!==token)throw new Cancel();}
async function sleep(ms,tk){if(FAST)return;let rem=ms;while(rem>0){chk(tk);if(paused){await raw(80);continue;}await raw(40);rem-=40*speed;}chk(tk);}
function rel(el){const a=el.getBoundingClientRect(),b=stage.getBoundingClientRect();return{x:(a.left-b.left)/scale,y:(a.top-b.top)/scale,w:a.width/scale,h:a.height/scale};}
function makeApi(tk){
  const A={
    sleep:ms=>sleep(ms,tk),
    set(fn){fn(S);render();},
    async scroll(sel,off=60){const el=$(sel);const pr=page.getBoundingClientRect();const er=el.getBoundingClientRect();
      const y=(er.top-pr.top)/scale-off;const max=Math.max(0,page.offsetHeight-STAGE_H);page.style.transform='translateY(-'+Math.max(0,Math.min(y,max))+'px)';await A.sleep(850);},
    async top(){page.style.transform='translateY(0)';await A.sleep(850);},
    async move(sel,dx=0,dy=0){const el=$(sel);const r=rel(el);cursor.style.left=(r.x+Math.min(r.w/2,60)+dx)+'px';cursor.style.top=(r.y+r.h/2+dy)+'px';await A.sleep(700);},
    async click(sel,fx){await A.move(sel);cursor.classList.add('down');await A.sleep(220);if(fx)fx();cursor.classList.remove('down');await A.sleep(300);},
    async type(sel,txt,per=70){const el=$(sel);el.textContent='';for(const ch of txt){el.textContent+=ch;await A.sleep(per);}await A.sleep(250);},
    ring(sel,label,pad=5){const el=$(sel);const r=rel(el);Object.assign(ring.style,{left:(r.x-pad)+'px',top:(r.y-pad)+'px',width:(r.w+pad*2)+'px',height:(r.h+pad*2)+'px'});ring.classList.add('on');
      if(label){ringl.textContent=label;ringl.classList.add('on');const lw=ringl.offsetWidth;ringl.style.left=Math.max(4,Math.min(STAGE_W-lw-4,r.x+r.w+pad-lw))+'px';ringl.style.top=Math.max(4,r.y-pad-24)+'px';}else ringl.classList.remove('on');},
    unring(){ring.classList.remove('on');ringl.classList.remove('on');},
    toast(t){toastEl.textContent=t;toastEl.classList.add('on');if(!FAST)setTimeout(()=>toastEl.classList.remove('on'),2600);else toastEl.classList.remove('on');},
  };return A;}
function setFast(v){FAST=v;stage.classList.toggle('nofx',v);if(v)stage.style.setProperty('--mv','0s');else stage.style.setProperty('--mv',(.65/speed)+'s');}
function plainText(h){const d=document.createElement('div');d.innerHTML=h;return d.textContent;}
function speak(h){if(!narr||!window.speechSynthesis)return Promise.resolve();speechSynthesis.cancel();
  return new Promise(res=>{const u=new SpeechSynthesisUtterance(plainText(h));u.lang='pt-BR';u.rate=Math.min(1.6,speed);u.onend=res;u.onerror=res;speechSynthesis.speak(u);setTimeout(res,45000);});}
function showCaption(i){const s=STEPS[i];$('#cn').textContent=(i+1)+' de '+STEPS.length;$('#ct').textContent=s.t;$('#cb').innerHTML=s.b;$('#ctip').innerHTML=s.tip||'';
  $('#pb').style.width=((i)/(STEPS.length)*100)+'%';
  $$('#chips button').forEach((b,j)=>{b.classList.toggle('on',j===i);b.classList.toggle('done',j<i);});
  const on=$('#chips button.on');if(on)on.scrollIntoView({block:'nearest',inline:'center'});}
async function runStep(i,tk){
  showCaption(i);const sp=speak(STEPS[i].b);
  await STEPS[i].run(makeApi(tk));
  chk(tk);await Promise.all([sp,sleep(900,tk)]);
}
async function goto(i,autoplay=true){
  token++;const tk=token;window.speechSynthesis&&window.speechSynthesis.cancel();
  $('#poster').classList.add('hide');started=true;
  try{
    setFast(true);resetState();
    for(let j=0;j<i;j++){await STEPS[j].run(makeApi(tk));chk(tk);}
    page.style.transition='none';page.offsetHeight;page.style.transition='';
    setFast(false);cur=i;paused=!autoplay;syncBtn();
    for(let k=i;k<STEPS.length;k++){cur=k;await runStep(k,tk);}
    finish();
  }catch(e){if(!(e instanceof Cancel))throw e;}
}
function resetState(){resetS();render();page.style.transform='translateY(0)';cursor.style.left='380px';cursor.style.top='270px';ring.classList.remove('on');ringl.classList.remove('on');toastEl.classList.remove('on');$$('.dd').forEach(d=>d.classList.remove('on'));}
function finish(){paused=true;syncBtn();$('#pb').style.width='100%';$$('#chips button').forEach(b=>{b.classList.remove('on');b.classList.add('done');});
  const p=$('#poster');p.querySelector('h2').textContent='Fim da aula';p.querySelector('p').textContent='Clique para assistir novamente ou escolha um passo na lista abaixo.';p.classList.remove('hide');cur=-1;started=false;}
function syncBtn(){$('#bplay').textContent=paused?'▶ Continuar':'⏸ Pausar';$('#bplay').classList.toggle('main',paused);}
$('#poster').onclick=()=>goto(0,true);
$('#bplay').onclick=()=>{if(!started){goto(0,true);return;}paused=!paused;syncBtn();if(window.speechSynthesis){paused?speechSynthesis.pause():speechSynthesis.resume();}};
$('#bprev').onclick=()=>goto(Math.max(0,(cur<0?0:cur)-1),true);
$('#bnext').onclick=()=>goto(Math.min(STEPS.length-1,(cur<0?0:cur)+1),true);
$('#brest').onclick=()=>goto(0,true);
$('#spd').onchange=e=>{speed=parseFloat(e.target.value);stage.style.setProperty('--mv',(.65/speed)+'s');};
$('#nar').onchange=e=>{narr=e.target.checked;if(!narr&&window.speechSynthesis)speechSynthesis.cancel();else if(narr&&started&&cur>=0)speak(STEPS[cur].b);};
$('#bar').onclick=e=>{const r=e.currentTarget.getBoundingClientRect();goto(Math.min(STEPS.length-1,Math.floor((e.clientX-r.left)/r.width*STEPS.length)),true);};
const bfs=$('#bfs');
if(!document.fullscreenEnabled){bfs.style.display='none';}
bfs.onclick=()=>{const p=$('#player');document.fullscreenElement?document.exitFullscreen():p.requestFullscreen();};
STEPS.forEach((s,i)=>{const b=document.createElement('button');b.textContent=(i+1)+'. '+s.short;b.onclick=()=>goto(i,true);$('#chips').appendChild(b);});
showCaption(0);$('#pb').style.width='0';$$('#chips button').forEach(b=>b.classList.remove('on'));
resetS();render();
"""

_HTML = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>__CSS__</style></head><body>
<div class="player" id="player">
  <div class="topbar">🎓 __TITULO__ <small>Vídeo-aula simulada · dados fictícios</small></div>
  <div class="stagewrap" id="wrap">
    <div class="stage" id="stage" style="--mv:.65s">
      <div id="page">__STAGE__</div>
      <div class="ring" id="ring"></div><div class="ringlabel" id="ringl"></div>
      <div class="cursor" id="cursor"><div class="rip"></div><svg width="22" height="22" viewBox="0 0 24 24"><path d="M3 2l17 8-7.5 2L9 20z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg></div>
      <div class="toast" id="toast"></div>
      <div class="ribbon">SIMULAÇÃO · DADOS FICTÍCIOS</div>
    </div>
    <div class="poster" id="poster"><div class="playbtn"><svg viewBox="0 0 24 24"><path d="M5 3l16 9-16 9z" fill="#111"/></svg></div><h2>__TITULO__</h2><p>__DESCRICAO__</p></div>
  </div>
  <div class="bar" id="bar"><i id="pb"></i></div>
  <div class="ctrl">
    <button id="bprev" title="Passo anterior">⏮</button><button id="bplay" class="main">▶ Assistir</button><button id="bnext" title="Próximo passo">⏭</button><button id="brest" title="Reiniciar">↺</button>
    <span class="sp"></span>
    <label>Velocidade <select id="spd"><option value="0.75">0,75×</option><option value="1" selected>1×</option><option value="1.5">1,5×</option><option value="2">2×</option></select></label>
    <label><input type="checkbox" id="nar"> 🔊 Narração</label>
    <button id="bfs" title="Tela cheia">⛶</button>
  </div>
  <div class="cap"><div class="n">Passo <span id="cn"></span></div><h3 id="ct"></h3><div class="b" id="cb"></div><div class="tip" id="ctip"></div></div>
  <div class="chips" id="chips"></div>
</div>
<script>window.__STEPS__=[];</script>
<script>__STEPS_JS__</script>
<script>__JS__</script>
</body></html>"""


def montar_player(titulo: str, descricao: str, stage_html: str, mock_css: str, state_js: str, steps_js: str) -> str:
    """Monta o HTML completo do player.

    ``state_js`` define ``S``, ``resetS()`` e ``render()`` (estado e redesenho da tela simulada);
    ``steps_js`` preenche ``window.__STEPS__`` com objetos ``{short, t, b, tip, run: async (api) => {...}}``.
    """
    return (
        _HTML.replace("__CSS__", _CSS + _MOCK_CSS + mock_css)
        .replace("__TITULO__", titulo)
        .replace("__DESCRICAO__", descricao)
        .replace("__STAGE__", stage_html)
        .replace("__STEPS_JS__", state_js + "\n" + steps_js)
        .replace("__JS__", _JS)
    )


def para_js(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False)
