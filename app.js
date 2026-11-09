document.querySelectorAll('table.sortable th').forEach(th=>{const i=th.cellIndex;th.tabIndex=0;const go=()=>{const b=th.closest('table').tBodies[0],d=th.dataset.d=th.dataset.d==='a'?'d':'a';
[...b.rows].sort((x,y)=>{const a=x.cells[i].dataset.v??x.cells[i].textContent,c=y.cells[i].dataset.v??y.cells[i].textContent,
n=parseFloat(a),m=parseFloat(c),r=isNaN(n)||isNaN(m)?a.localeCompare(c):n-m;return d==='a'?r:-r}).forEach(r=>b.append(r))};
th.addEventListener('click',go);th.addEventListener('keydown',e=>{if(e.key==='Enter')go()})});
const TABS=['uebersicht','spieler','liga','analyse','partien'];
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
let lastTab=null,pushed=false;
function parse(){const h=(location.hash||'').slice(1),i=h.indexOf('~'),t=i<0?h:h.slice(0,i);return{tab:TABS.includes(t)?t:'uebersicht',slug:i<0?'':h.slice(i+1)}}
function setHash(tab,slug,push){const u=location.pathname+location.search+'#'+tab+(slug?'~'+slug:'');
if(push){history.pushState(null,'',u);pushed=true}else history.replaceState(null,'',u)}
function showTab(h){$$('.panel').forEach(p=>p.classList.toggle('on',p.id==='p-'+h));
$$('.tabs a').forEach(a=>{const on=a.getAttribute('href')==='#'+h;a.classList.toggle('on',on);if(on)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
if(lastTab!==null&&lastTab!==h)scrollTo(0,0);lastTab=h}
function closeAll(){$$('dialog[open]').forEach(x=>{x._int=true;x.close()})}
function openDlg(d){if(!d||!d.showModal)return;const was=$$('dialog[open][data-s]').length>0;closeAll();d.showModal();
const dlg=d.querySelector('.dlg');if(dlg)dlg.scrollTop=0;d.scrollTop=0;
if(d.dataset.s)setHash(parse().tab,d.dataset.s,!was)}
function sync(){const p=parse();showTab(p.tab);
if(p.slug){const d=$('dialog[data-s="'+p.slug.replace(/"/g,'')+'"]');if(d&&!d.open){closeAll();d.showModal()}}
else{pushed=false;closeAll()}}
addEventListener('hashchange',sync);sync();
document.addEventListener('close',e=>{const d=e.target;if(d.tagName!=='DIALOG')return;if(d._int){d._int=false;return}
if(!d.dataset.s)return;if(pushed){pushed=false;history.back()}else setHash(parse().tab,'',false)},true);
document.addEventListener('keydown',e=>{const d=$('dialog[open]');
if(e.key==='/'&&!d&&!/INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName)){e.preventDefault();openSearch();return}
if(!d||(e.key!=='ArrowLeft'&&e.key!=='ArrowRight'))return;if(/INPUT|SELECT/.test(document.activeElement.tagName))return;
const b=d.querySelector(e.key==='ArrowLeft'?'.nb-prev':'.nb-next');if(b&&!b.disabled)b.click()});
function copyText(c,txt){const o=c.textContent,done=()=>{c.textContent='Kopiert ✓';setTimeout(()=>{c.textContent=o},1800)};
const fb=()=>{const a=document.createElement('textarea');a.value=txt;(c.closest('dialog')||document.body).appendChild(a);a.select();
try{document.execCommand('copy');done()}catch(_){c.textContent='Kopieren nicht möglich'}a.remove()};
if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,fb)}else{fb()}}
/* Ergebnis-Bild (Canvas, 1080x1350) zum Teilen oder Speichern */
function loadImg(src){return new Promise(r=>{if(!src)return r(null);const i=new Image();i.onload=()=>r(i);i.onerror=()=>r(null);i.src=src})}
function fitText(x,t,w,start,font,min){let s=start;do{x.font=font.replace('$',s);if(x.measureText(t).width<=w)break;s-=2}while(s>min);return s}
async function shareImg(btn,d){
const old=btn.textContent;btn.textContent='Bild wird erstellt …';
try{
const m=document.querySelector('meta[name="dts-logos"]'),[l1,l2]=(m?m.content:',').split(',');
const [a,b]=await Promise.all([loadImg(l1),loadImg(l2)]);
if(document.fonts&&document.fonts.ready)await document.fonts.ready;
const W=1080,H=1350,c=document.createElement('canvas');c.width=W;c.height=H;const x=c.getContext('2d');
const cs=getComputedStyle(document.documentElement),red=(cs.getPropertyValue('--green')||'#9a1b1c').trim()||'#9a1b1c';
x.fillStyle='#17100f';x.fillRect(0,0,W,H);
x.fillStyle=red;x.fillRect(0,0,W,14);x.fillRect(0,H-14,W,14);
const g=x.createRadialGradient(W/2,H*.42,40,W/2,H*.42,720);g.addColorStop(0,'#3a1a1b');g.addColorStop(1,'#17100f');x.fillStyle=g;x.fillRect(0,14,W,H-28);
const SERIF='Georgia,"Times New Roman",serif',SANS='system-ui,-apple-system,"Segoe UI",Roboto,sans-serif';
if(a)x.drawImage(a,60,60,170,170*a.height/a.width);
if(b){const h=96,w=h*b.width/b.height;x.drawImage(b,W-60-w,70,w,h)}
x.textAlign='center';x.fillStyle='#c9bcbe';x.font='34px '+SANS;x.fillText('Liga STSO S 2 · '+d.date,W/2,300);
x.fillStyle='#fff';
let y=420;[d.home,d.guest].forEach((t,i)=>{const s=fitText(x,t,900,76,'700 $px '+SERIF,34);x.font='700 '+s+'px '+SERIF;x.fillText(t,W/2,y);y+=i?0:70;if(!i){x.fillStyle='#c9bcbe';x.font='32px '+SANS;x.fillText('gegen',W/2,y+10);x.fillStyle='#fff';y+=90}});
y+=100;x.fillStyle='#c9bcbe';x.font='34px '+SANS;x.fillText('Spiele',W/2,y);
x.fillStyle='#fff';x.font='700 190px '+SERIF;x.fillText(d.games,W/2,y+190);y+=190;
if(d.sets){x.fillStyle='#c9bcbe';x.font='36px '+SANS;x.fillText('Sätze '+d.sets,W/2,y+70);y+=70}
y+=90;
if(d.mvp&&d.mvp.length){x.fillStyle=red;x.fillRect(W/2-300,y,600,4);y+=64;x.fillStyle='#c9bcbe';x.font='30px '+SANS;x.fillText(d.mvp.length>1?'Spieler des Spiels':'Spieler des Spiels',W/2,y);y+=56;
x.fillStyle='#fff';d.mvp.forEach(p=>{x.font='700 44px '+SERIF;x.fillText(p[0]+'  '+p[1],W/2,y);y+=44;x.fillStyle='#c9bcbe';x.font='28px '+SANS;x.fillText(p[2],W/2,y);x.fillStyle='#fff';y+=54})}
const blob=await new Promise(r=>c.toBlob(r,'image/png'));
const name='ergebnis-'+(d.home+'-'+d.guest).toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')+'.png';
const f=new File([blob],name,{type:'image/png'});
const dlg=btn.closest('dialog');let box=dlg.querySelector('.imgprev');if(box){URL.revokeObjectURL(box.dataset.u);box.remove()}
const u=URL.createObjectURL(blob);box=document.createElement('div');box.className='imgprev';box.dataset.u=u;
const can=navigator.canShare&&navigator.canShare({files:[f]});
box.innerHTML='<img alt="Ergebnisbild" src="'+u+'"><p class="acts"><a class="rb" download="'+name+'" href="'+u+'">Bild speichern</a>'+(can?' <button type="button" class="rb" data-sh>Teilen …</button>':'')+' <button type="button" class="rb" data-x>Schliessen</button></p>';
box.addEventListener('click',async e=>{if(e.target.closest('[data-x]')){URL.revokeObjectURL(u);box.remove()}
if(e.target.closest('[data-sh]')){try{await navigator.share({files:[f],title:d.home+' '+d.pts+' '+d.guest})}catch(_){}}});
btn.closest('.acts').after(box);box.scrollIntoView({block:'center',behavior:'smooth'});
btn.textContent=old;return
}catch(e){btn.textContent='Bild nicht möglich'}
setTimeout(()=>{btn.textContent=old},2200)}
document.addEventListener('click',e=>{
const l=e.target.closest('[data-link]');
if(l){const d=l.closest('dialog');copyText(l,location.origin+location.pathname+location.search+'#~'+d.dataset.s);return}
const c=e.target.closest('[data-copy]');
if(c){copyText(c,c.dataset.copy);return}
const im=e.target.closest('[data-img]');
if(im){shareImg(im,JSON.parse(im.dataset.img));return}
const g=e.target.closest('[data-go]');
if(g){if(!g.disabled)openDlg(document.getElementById(g.dataset.go));return}
const t=e.target.closest('[data-open]');
if(t){openDlg(document.getElementById(t.dataset.open));return}
if(e.target.closest('#sbtn')){openSearch();return}
const d=e.target.closest('dialog');if(e.target.tagName==='DIALOG'||e.target.closest('[data-close]'))(d||e.target).close()});
/* Wischen: Fenster folgt dem Finger; links/rechts blättert, nach unten wegziehen schliesst */
let g=null;
const nbtn=(d,s)=>{const b=d.querySelector(s);return b&&!b.disabled?b:null};
function rst(d,ms){const f=()=>{d.style.transition=d.style.transform=d.style.opacity=''};ms?setTimeout(f,ms):f()}
document.addEventListener('touchstart',e=>{const d=e.target.closest('dialog[open]');
if(!d||e.touches.length!==1||e.target.closest('.scroll,input,select,textarea')){g=null;return}
const t=e.touches[0];g={d,x:t.clientX,y:t.clientY,ax:null,t:Date.now(),top:d.scrollTop<=0}},{passive:true});
document.addEventListener('touchmove',e=>{if(!g)return;const t=e.touches[0],dx=t.clientX-g.x,dy=t.clientY-g.y;
if(g.ax===null){if(Math.abs(dx)<10&&Math.abs(dy)<10)return;
if(Math.abs(dx)>Math.abs(dy)*1.4)g.ax='x';else if(Math.abs(dy)>Math.abs(dx)&&g.top&&dy>0)g.ax='y';else{g=null;return}
g.d.style.transition='none'}
if(g.ax==='x'){const k=nbtn(g.d,dx<0?'.nb-next':'.nb-prev')?1:.25;g.d.style.transform='translateX('+dx*k+'px)';g.d.style.opacity=1-Math.min(.4,Math.abs(dx)/450)}
else{g.d.style.transform='translateY('+Math.max(0,dy)+'px)'}},{passive:true});
function endDrag(e){if(!g)return;const s=g;g=null;if(!s.ax)return;const d=s.d,t=(e.changedTouches||[])[0];
const dx=t?t.clientX-s.x:0,dy=t?t.clientY-s.y:0,v=Math.max(Math.abs(dx),Math.abs(dy))/Math.max(1,Date.now()-s.t);
d.style.transition='transform .18s ease-out,opacity .18s ease-out';
if(s.ax==='x'){const b=nbtn(d,dx<0?'.nb-next':'.nb-prev');
if(b&&(Math.abs(dx)>90||(v>.5&&Math.abs(dx)>40))){d.style.transform='translateX('+(dx<0?-50:50)+'px)';d.style.opacity='0';
setTimeout(()=>{rst(d);b.click();const n=$('dialog[open]');if(n){n.classList.add(dx<0?'in-r':'in-l');setTimeout(()=>n.classList.remove('in-r','in-l'),260)}},140)}
else{d.style.transform='none';d.style.opacity='1';rst(d,200)}}
else if(dy>110||(v>.6&&dy>50)){d.style.transform='translateY(110%)';setTimeout(()=>{rst(d);d.close()},170)}
else{d.style.transform='none';rst(d,200)}}
document.addEventListener('touchend',endDrag,{passive:true});
document.addEventListener('touchcancel',e=>{if(g&&g.ax){rst(g.d)}g=null},{passive:true});
/* Suche */
function openSearch(){const d=document.getElementById('search');if(!d)return;closeAll();d.showModal();const i=document.getElementById('s-in');i.value='';render('');i.focus()}
function render(q){const out=document.getElementById('s-res');q=q.trim().toLowerCase();
const items=$$('dialog[data-k]').filter(d=>!q||(d.dataset.n+' '+d.dataset.sub).toLowerCase().includes(q)).slice(0,40);
out.innerHTML=items.length?items.map(d=>'<li><button class="tl" data-open="'+d.id+'">'+d.dataset.n.replace(/</g,'&lt;')+'</button><small>'+d.dataset.k+' · '+d.dataset.sub.replace(/</g,'&lt;')+'</small></li>').join(''):'<li><small>Nichts gefunden</small></li>'}
(()=>{const i=document.getElementById('s-in');if(!i)return;i.addEventListener('input',()=>render(i.value));
i.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();const b=document.querySelector('#s-res button');if(b)b.click()}})})();
/* Hinweis bei veralteten Daten, Countdown */
(()=>{const s=document.getElementById('stand'),b=document.getElementById('stale');
if(s&&b){const t=new Date(s.getAttribute('datetime')),h=(Date.now()-t)/36e5;if(h>36){b.hidden=false;b.textContent='Hinweis: Die Daten sind vom '+t.toLocaleDateString('de-CH',{day:'2-digit',month:'2-digit'})+' – vfc.ch war zuletzt nicht erreichbar, der nächste Lauf versucht es erneut.'}}
$$('.cd[data-d]').forEach(e=>{const d=new Date(e.dataset.d+'T00:00:00'),n=new Date();n.setHours(0,0,0,0);const k=Math.round((d-n)/864e5);
e.textContent=k===0?'heute':k===1?'morgen':k>1?'in '+k+' Tagen':k===-1?'gestern':'vor '+(-k)+' Tagen'})})();

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

document.querySelectorAll('select.vf').forEach(s=>{const g=s.dataset.g,k='dts.'+g;
const run=()=>document.querySelectorAll('.lb[data-g="'+g+'"]').forEach(b=>{b.hidden=b.dataset.t!==s.value});
s.addEventListener('change',run);
try{const v=localStorage.getItem(k);if(v&&[...s.options].some(o=>o.value===v)){s.value=v;run()}}catch(_){}
s.addEventListener('change',()=>{try{localStorage.setItem(k,s.value)}catch(_){}})});

/* Zustand merken */
(()=>{const get=k=>{try{return localStorage.getItem(k)}catch(_){return null}},set=(k,v)=>{try{localStorage.setItem(k,v)}catch(_){}};
const ft=document.getElementById('f-team');if(ft){const v=get('dts.team');if(v&&[...ft.options].some(o=>o.value===v)){ft.value=v;ft.dispatchEvent(new Event('change'))}ft.addEventListener('change',()=>set('dts.team',ft.value))}
const ids=['f-mon','f-home','f-win'];let st={};try{st=JSON.parse(get('dts.pf')||'{}')}catch(_){}
ids.forEach(i=>{const e=document.getElementById(i);if(!e)return;if(st[i]&&[...e.options].some(o=>o.value===st[i])){e.value=st[i]}
e.addEventListener('input',()=>{st[i]=e.value;set('dts.pf',JSON.stringify(st))})});
const f=document.getElementById('f-mon');if(f)f.dispatchEvent(new Event('input'))})();
