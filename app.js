document.querySelectorAll('table.sortable th').forEach((th,i)=>{th.tabIndex=0;const go=()=>{const b=th.closest('table').tBodies[0],d=th.dataset.d=th.dataset.d==='a'?'d':'a';
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
