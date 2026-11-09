document.querySelectorAll('table.sortable th').forEach(th=>{const i=th.cellIndex;th.tabIndex=0;const go=()=>{const b=th.closest('table').tBodies[0],d=th.dataset.d=th.dataset.d==='a'?'d':'a';
[...b.rows].sort((x,y)=>{const a=x.cells[i].dataset.v??x.cells[i].textContent,c=y.cells[i].dataset.v??y.cells[i].textContent,
n=parseFloat(a),m=parseFloat(c),r=isNaN(n)||isNaN(m)?a.localeCompare(c):n-m;return d==='a'?r:-r}).forEach(r=>b.append(r))};
th.addEventListener('click',go);th.addEventListener('keydown',e=>{if(e.key==='Enter')go()})});
const TABS=['uebersicht','spieler','liga','partien'];
function showTab(){let h=(location.hash||'').slice(1);if(!TABS.includes(h))h='uebersicht';
document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on',p.id==='p-'+h));
document.querySelectorAll('.tabs a').forEach(a=>{const on=a.getAttribute('href')==='#'+h;a.classList.toggle('on',on);if(on)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
window.scrollTo(0,0)}
addEventListener('hashchange',showTab);showTab();
document.addEventListener('keydown',e=>{const d=document.querySelector('dialog[open]');
if(!d||(e.key!=='ArrowLeft'&&e.key!=='ArrowRight'))return;const b=d.querySelector(e.key==='ArrowLeft'?'.nb-prev':'.nb-next');if(b&&!b.disabled)b.click()});
document.addEventListener('click',e=>{const c=e.target.closest('[data-copy]');
if(c){const txt=c.dataset.copy,o=c.textContent,done=()=>{c.textContent='Kopiert ✓';setTimeout(()=>{c.textContent=o},1800)};
const fb=()=>{const a=document.createElement('textarea');a.value=txt;(c.closest('dialog')||document.body).appendChild(a);a.select();
try{document.execCommand('copy');done()}catch(_){c.textContent='Kopieren nicht möglich'}a.remove()};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,fb)}else{fb()}return}
const g=e.target.closest('[data-go]');
if(g){if(!g.disabled){const n=document.getElementById(g.dataset.go);if(n){g.closest('dialog').close();n.showModal()}}return}
const t=e.target.closest('[data-open]');
if(t){const d=document.getElementById(t.dataset.open);if(d&&d.showModal){document.querySelectorAll('dialog[open]').forEach(x=>x.close());d.showModal()}return}
const d=e.target.closest('dialog');if(e.target.tagName==='DIALOG'||e.target.closest('[data-close]'))(d||e.target).close()})

if('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(()=>{});

(()=>{const t=document.getElementById('mtable');if(!t)return;const ids=['f-q','f-mon','f-home','f-win'],el=ids.map(i=>document.getElementById(i)),cnt=document.getElementById('f-count');
function run(){const [q,mon,home,win]=el.map(e=>e.value.trim().toLowerCase());let n=0;const rows=[...t.tBodies[0].rows];
rows.forEach(r=>{const ok=(!q||r.dataset.q.includes(q))&&(!mon||r.dataset.mon===mon)&&(home===''||r.dataset.home===home)&&(win===''||r.dataset.win===win);r.hidden=!ok;if(ok)n++});
const f=q||mon||home!==''||win!=='';cnt.textContent=f?(n?n+' von '+rows.length+' Partien':'Keine Partie gefunden'):''}
el.forEach(e=>e.addEventListener('input',run))})();

(()=>{let tip=null,cur=null;
function hide(){if(tip)tip.hidden=true;cur=null}
function show(b){const d=b.closest('dialog')||document.body;if(!tip||tip.parentNode!==d){tip&&tip.remove();tip=document.createElement('div');tip.id='tip';tip.setAttribute('role','tooltip');d.appendChild(tip)}
tip.textContent=b.dataset.tip;tip.hidden=false;cur=b;const r=b.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;
let x=Math.min(Math.max(8,r.left+r.width/2-w/2),innerWidth-w-8),y=r.top-h-8;if(y<8)y=r.bottom+8;tip.style.left=x+'px';tip.style.top=y+'px'}
document.addEventListener('mouseover',e=>{const b=e.target.closest('.badge');if(b)show(b);else if(cur)hide()});
document.addEventListener('focusin',e=>{const b=e.target.closest('.badge');if(b)show(b);else hide()});
document.addEventListener('click',e=>{const b=e.target.closest('.badge');if(b){cur===b&&tip&&!tip.hidden&&e.detail===0?hide():show(b)}else hide()});
document.addEventListener('focusout',hide);document.addEventListener('scroll',hide,true)})();

(()=>{const sel=document.getElementById('f-team'),q=document.getElementById('f-pq');if(!sel)return;
function run(){const t=sel.value,s=q.value.trim().toLowerCase();
document.querySelectorAll('.tp').forEach(b=>{b.hidden=b.dataset.t!==t;
if(!b.hidden)b.querySelectorAll('table.sortable tbody tr').forEach(r=>{r.hidden=!!s&&!r.dataset.q.includes(s)})})}
sel.addEventListener('change',run);q.addEventListener('input',run)})();
