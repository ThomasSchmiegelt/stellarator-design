#!/usr/bin/env python3
"""Erzeugt wissensnetz.html (eigenständig, offline) aus wissensnetz.json. KI-generiert (Claude Sonnet im Auftrag von Opus). Nur Standardbibliothek.

Ansicht: Zeitleiste mit Phasen H.. (blau, rekonstruiert) und Vorgängen der Zukunft (orange offen, grün fertig; Pfeile = Vorgänger).
Farben je Art: Phase blau, Vorgang orange/grün, Anforderung violett, Befund braun, Entscheidung türkis, Datei grau.
"""
import json, os, datetime

HIER = os.path.dirname(os.path.abspath(__file__))
QUELLE = os.path.join(HIER, "wissensnetz.json"); ZIEL = os.path.join(HIER, "wissensnetz.html")
d = json.load(open(QUELLE, encoding="utf-8"))
stand = datetime.datetime.fromtimestamp(os.path.getmtime(QUELLE)).strftime("%Y-%m-%d %H:%M")
daten = json.dumps(d, ensure_ascii=False).replace("</", "<\\/")

HTML = r"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Wissensnetz Stellarator</title>
<style>
:root{--fg:#1d232a;--bg:#f6f7f9;--card:#fff;--line:#c9d0d8;--ph:#1f6fb5;--vo:#e08a1e;--vf:#43a047;--rq:#7b1fa2;--bf:#8d6e63;--en:#00897b;--da:#78909c}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,Segoe UI,Arial,sans-serif;color:var(--fg);background:var(--bg)}
header{background:var(--card);border-bottom:1px solid var(--line);padding:10px 16px}
.titel{display:inline-block;border:2px solid var(--fg);padding:6px 12px;font-weight:700;font-size:18px}
.meta span{margin-right:16px;white-space:nowrap}
.warn{margin:8px 0 0;padding:8px 12px;border:2px solid #c62828;background:#fdecea;color:#7f1d1d}
.filter{display:flex;flex-wrap:wrap;gap:12px;align-items:center;padding:8px 16px;background:var(--card);border-bottom:1px solid var(--line)}
select,input[type=search]{font:inherit;padding:3px 6px;max-width:280px}button{font:inherit;padding:3px 10px;cursor:pointer}
main{display:flex;align-items:flex-start}#netz{flex:1 1 auto;min-width:0;overflow:auto;padding:8px;max-height:calc(100vh - 200px);min-height:300px}
#seite{flex:0 0 400px;max-height:calc(100vh - 200px);overflow:auto;background:var(--card);border-left:1px solid var(--line);padding:12px 16px}
#seite h2{margin:0 0 4px;font-size:17px}#seite h3{margin:14px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:#4a5560;border-bottom:1px solid var(--line)}
#seite ul{margin:0;padding-left:18px}#seite td{padding:1px 10px 1px 0;vertical-align:top}
.leg{display:flex;flex-wrap:wrap;gap:14px;padding:6px 16px;font-size:13px;background:var(--card);border-top:1px solid var(--line)}
.leg i{display:inline-block;width:22px;height:13px;vertical-align:-2px;margin-right:4px;border:1.5px solid #555}
footer{padding:10px 16px;color:#4a5560;font-size:13px;border-top:1px solid var(--line);background:var(--card)}
.k{cursor:pointer}.k.dim{opacity:.18}.k.sel rect{stroke:#000!important;stroke-width:3.5}.k.treffer rect{stroke:#6a1b9a!important;stroke-width:3}
.kante{fill:none;stroke:#7b8591;stroke-width:1.2}.kante.dim{opacity:.12}.ok{color:#2e7d32;font-weight:700}.nein{color:#c62828;font-weight:700}
.tag{display:inline-block;padding:0 6px;margin:1px 2px;border-radius:3px;color:#fff;font-size:12px}
@media(max-width:900px){main{flex-direction:column}#seite{flex:none;width:100%;border-left:0;border-top:1px solid var(--line);max-height:none}#netz{max-height:none;width:100%}}
</style></head><body>
<header><div class="titel">Wissensnetz Stellarator – KI-generiert</div><p class="meta" id="meta"></p><div id="warn"></div></header>
<div class="filter">
<label>Anforderung <select id="fReq"></select></label>
<label>Befund <input type="search" id="fB" placeholder="z. B. B-031" size="9"></label>
<label>Suche <input type="search" id="fQ" placeholder="Name oder ID"></label>
<button id="fReset">Zurücksetzen</button><span id="fInfo"></span></div>
<div class="leg" id="leg"></div>
<main><div id="netz"></div><aside id="seite"><p>Balken anklicken, um Anforderungen, Befunde, Dateien und Entscheidungen zu sehen.</p></aside></main>
<footer>KI-generiert (Claude Sonnet im Auftrag von Claude Opus). Phasen H.. sind rekonstruiert (aus BEFUNDE.md, ERINNERUNGEN.md, Git), Dauern der Zukunft sind Annahmen. Erzeugt aus pm/plan/wissensnetz.json.</footer>
<script id="daten" type="application/json">__DATEN__</script>
<script>
const D=JSON.parse(document.getElementById('daten').textContent), STAND="__STAND__";
const K=[...D.phasen,...D.vorgaenge], byId={}; K.forEach(k=>byId[k.id]=k);
const NS='http://www.w3.org/2000/svg';
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const link=p=>'<a href="../../'+esc(p)+'" target="_blank">'+esc(p)+'</a>';
const P=D.pruefung;
document.getElementById('meta').innerHTML='<span>Stand: '+STAND+'</span><span>Phasen (rekonstruiert): '+D.phasen.length+'</span><span>Vorgänge (Zukunft): '+D.vorgaenge.length+
 ' (fertig '+D.vorgaenge.filter(v=>v.status==='fertig').length+')</span><span>Befunde zugeordnet: '+P.befunde_zugeordnet+'/'+P.befunde_gesamt+'</span><span>Anforderungen: '+P.req_gesamt+'</span><span><b>Dauern der Zukunft sind Annahmen.</b></span>';
let w='';
if(P.befunde_fehlend.length) w+='<div class="warn"><b>Befunde ohne Phase:</b> '+esc(P.befunde_fehlend.join(', '))+'</div>';
if(P.req_ohne_knoten.length) w+='<div class="warn"><b>Anforderungen ohne Phase/Vorgang:</b> '+esc(P.req_ohne_knoten.join(', '))+'</div>';
if(P.fehler.length) w+='<div class="warn"><b>Prüffehler:</b><ul>'+P.fehler.map(e=>'<li>'+esc(e)+'</li>').join('')+'</ul></div>';
document.getElementById('warn').innerHTML=w;
const FA={phase:'#1f6fb5',offen:'#e08a1e',fertig:'#43a047'};
document.getElementById('leg').innerHTML=[['Phase (rekonstruiert)','#1f6fb5'],['Vorgang offen (geplant, Annahme)','#e08a1e'],['Vorgang fertig (Ausgabedatei vorhanden)','#43a047'],['Anforderung','#7b1fa2'],['Befund','#8d6e63'],['Entscheidung','#00897b'],['Datei','#78909c']]
 .map(a=>'<span><i style="background:'+a[1]+'"></i>'+a[0]+'</span>').join('')+'<span>Pfeile = Vorgänger (Zukunft); Phasen überlappen zeitlich, keine Vorgängerbeziehung belegt</span>';
// Zeitachse
const T0=Date.parse('2026-10-20'), PXD=22, X0=70, Y0=40, BH=26, GAP=6;
const day=s=>(Date.parse(s)-T0)/864e5;
const rows=K.map((k,i)=>({k,y:Y0+i*(BH+GAP),x:X0+day(k.von)*PXD,w:Math.max((day(k.bis)+1-day(k.von))*PXD,14)}));
const maxX=Math.max(...rows.map(r=>r.x+r.w))+320, H=Y0+rows.length*(BH+GAP)+10;
const svg=document.createElementNS(NS,'svg');svg.setAttribute('width',maxX);svg.setAttribute('height',H);
function el(t,a,p){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);(p||svg).appendChild(e);return e;}
const defs=el('defs',{});const m=el('marker',{id:'pf',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:7,markerHeight:7,orient:'auto'},defs);el('path',{d:'M0,0L10,5L0,10z',fill:'#7b8591'},m);
const maxD=Math.ceil(day(K[K.length-1].bis))+8;
for(let t=0;t<=maxD;t++){const dt=new Date(T0+t*864e5);if(dt.getUTCDay()===1){const x=X0+t*PXD;el('line',{x1:x,x2:x,y1:26,y2:H,stroke:'#dfe3e8'});
 const tx=el('text',{x:x,y:20,'font-size':11,'text-anchor':'middle',fill:'#4a5560'});tx.textContent=dt.toISOString().slice(5,10);}}
const xz=X0+day(D.start_zukunft)*PXD;el('line',{x1:xz,x2:xz,y1:26,y2:H,stroke:'#c62828','stroke-width':1.5});
const tz=el('text',{x:xz+4,y:12,'font-size':11,fill:'#c62828'});tz.textContent='Start Zukunft '+D.start_zukunft;
const pos={};rows.forEach(r=>pos[r.k.id]=r);
const kanten=[];
D.vorgaenge.forEach(v=>v.vorgaenger.forEach(u=>{const a=pos[u],b=pos[v.id];if(!a||!b)return;
 const x1=a.x+a.w,y1=a.y+BH/2,x2=b.x,y2=b.y+BH/2;
 const p=el('path',{d:'M'+x1+','+y1+' C'+(x1+12)+','+y1+' '+(x2-12)+','+y2+' '+x2+','+y2,class:'kante','marker-end':'url(#pf)'});kanten.push({p,a:u,b:v.id});}));
const gm={};
rows.forEach(r=>{const k=r.k,g=el('g',{class:'k',transform:'translate('+r.x+','+r.y+')'});
 const fill=k.art==='Phase'?FA.phase:(k.status==='fertig'?FA.fertig:FA.offen);
 const t=el('title',{},g);t.textContent=k.id+': '+k.name+' ('+k.von+' bis '+k.bis+', '+k.status+')';
 el('rect',{width:r.w,height:BH,rx:3,fill:fill,stroke:'#333','stroke-width':1,'fill-opacity':k.art==='Phase'?0.9:0.7},g);
 const t1=el('text',{x:4,y:17,'font-size':12,'font-weight':700,fill:'#fff'},g);t1.textContent=r.w>30?k.id:'';
 const t2=el('text',{x:r.w+6,y:17,'font-size':11.5,fill:'#1d232a'},g);t2.textContent=(r.w<=30?k.id+' ':'')+(k.name.length>70?k.name.slice(0,69)+'…':k.name);
 g.addEventListener('click',()=>waehle(k.id));gm[k.id]=g;});
document.getElementById('netz').appendChild(svg);
// Filter
const fR=document.getElementById('fReq'),fB=document.getElementById('fB'),fQ=document.getElementById('fQ');
fR.innerHTML='<option value="">– alle –</option>'+D.anforderungen.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.id)+' '+esc(a.text.slice(0,50))+'</option>').join('');
let sel=null;
function filter(){const r=fR.value,b=fB.value.trim().toUpperCase(),q=fQ.value.trim().toLowerCase(),akt=!!(r||b||q),hit=new Set();
 K.forEach(k=>{let ok=true;if(r&&!k.req.includes(r))ok=false;if(b&&!((k.befunde||[]).includes(b)))ok=false;if(q&&!(k.id+' '+k.name).toLowerCase().includes(q))ok=false;if(ok)hit.add(k.id);});
 K.forEach(k=>{gm[k.id].classList.toggle('dim',akt&&!hit.has(k.id));gm[k.id].classList.toggle('treffer',akt&&hit.has(k.id));});
 kanten.forEach(e=>e.p.classList.toggle('dim',akt&&!(hit.has(e.a)&&hit.has(e.b))));
 document.getElementById('fInfo').textContent=akt?hit.size+' von '+K.length+' Knoten':'';}
[fR].forEach(e=>e.addEventListener('change',filter));fB.addEventListener('input',filter);fQ.addEventListener('input',filter);
document.getElementById('fReset').onclick=()=>{fR.value='';fB.value='';fQ.value='';filter();};
const tag=(t,c)=>'<span class="tag" style="background:'+c+'">'+esc(t)+'</span>';
function waehle(id){const k=byId[id];if(!k)return;if(sel&&gm[sel])gm[sel].classList.remove('sel');sel=id;gm[id].classList.add('sel');
 const li=(a,f)=>a&&a.length?'<ul>'+a.map(f).join('')+'</ul>':'<p>–</p>';
 const rq={};D.anforderungen.forEach(a=>rq[a.id]=a.text);const bt={};D.befunde.forEach(b=>bt[b.id]=b.titel);
 let h='<h2>'+esc(k.id)+': '+esc(k.name)+'</h2><table><tr><td>Art</td><td>'+esc(k.art)+'</td></tr><tr><td>Zeitraum</td><td>'+esc(k.von)+' bis '+esc(k.bis)+'</td></tr><tr><td>Status</td><td>'+esc(k.status)+(k.kritisch?' (kritischer Pfad)':'')+'</td></tr>'+
  '<tr><td>Wer</td><td>'+esc((k.wer||[]).join(', ')||'–')+'</td></tr>'+(k.art==='Vorgang'?'<tr><td>Dauer</td><td>'+k.dauer+' AT (Annahme)</td></tr><tr><td>Puffer</td><td>'+k.puffer+' AT</td></tr><tr><td>Vorgänger</td><td>'+esc(k.vorgaenger.join(', ')||'–')+'</td></tr><tr><td>Notiz</td><td>'+esc(k.notiz)+'</td></tr>':'')+'</table>';
 if(k.ergebnis)h+='<h3>Ergebnis (rekonstruiert)</h3><p>'+esc(k.ergebnis)+'</p><h3>Beleg</h3><p>'+esc(k.beleg)+'</p>';
 h+='<h3>Anforderungen</h3>'+li(k.req,r=>'<li>'+tag(r,'#7b1fa2')+' '+esc(rq[r]||'')+'</li>');
 h+='<h3>Befunde</h3>'+li(k.befunde,b=>'<li>'+tag(b,'#8d6e63')+' '+esc((bt[b]||'').slice(0,110))+'</li>');
 const en=D.entscheidungen.filter(e=>e.phase===k.id);h+='<h3>Entscheidungen</h3>'+li(en,e=>'<li>'+tag(e.id,'#00897b')+' '+esc(e.datum)+': '+esc(e.text)+'<br><small>'+esc(e.beleg)+'</small></li>');
 if(k.commits)h+='<h3>Commits</h3><p>'+esc(k.commits.join(', '))+'</p>';
 const da=k.dateien||k.aus||[];h+='<h3>Dateien</h3>'+li(da,x=>'<li><span class="'+(x.vorhanden?'ok':'nein')+'">'+(x.vorhanden?'✓':'✗')+'</span> '+link(x.pfad)+'</li>');
 document.getElementById('seite').innerHTML=h;}
const pm=new URLSearchParams(location.search).get('knoten');if(pm&&byId[pm])waehle(pm);
</script></body></html>
"""
open(ZIEL, "w", encoding="utf-8").write(HTML.replace("__DATEN__", daten).replace("__STAND__", stand))
print("geschrieben: pm/plan/wissensnetz.html")
