(()=>{
const D=JSON.parse(document.getElementById('fd').textContent);
const W=1080,H=1350,cv=document.getElementById('cv'),c=cv.getContext('2d');
cv.width=W;cv.height=H;
const $=id=>document.getElementById(id);
const FONT='"Bebas","Arial Narrow",Impact,sans-serif';
const imgs={};
const load=src=>imgs[src]||(imgs[src]=new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.onerror=()=>r(null);i.src=src}));
const dp=s=>{const m=/(\d+)\.(\d+)\.(\d+)/.exec(s);return m?new Date(2000+ +m[3],+m[2]-1,+m[1]):null};
const rnd=(s=>()=>(s=(s*16807)%2147483647)/2147483647)(7);
function rr(x,y,w,h,r){c.beginPath();c.roundRect(x,y,w,h,r)}
function txt(t,x,y,size,fill,o={}){c.save();c.font=`${size}px ${FONT}`;c.textAlign=o.a||'left';c.textBaseline='alphabetic';
 if(c.letterSpacing!==undefined)c.letterSpacing=(o.ls||0)+'px';
 if(o.skew){c.transform(1,0,-0.2,1,0.2*y,0)}
 if(o.shadow){c.shadowColor=o.shadow;c.shadowBlur=o.sb||18}
 c.fillStyle=fill;
 if(o.max){const w=c.measureText(t).width;if(w>o.max){size=size*o.max/w;c.font=`${size}px ${FONT}`}}
 c.fillText(t,x,y);c.restore()}
function metal(y,h,a,b){const g=c.createLinearGradient(0,y,0,y+h);g.addColorStop(0,a);g.addColorStop(.55,b);g.addColorStop(1,a);return g}
function board(cx,cy,R){
 const nums=[20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5];
 c.save();c.translate(cx,cy);
 c.fillStyle='#1a1512';c.beginPath();c.arc(0,0,R*1.08,0,7);c.fill();
 const ring=(r0,r1,i,odd)=>{const a0=(i-.5)*Math.PI/10-Math.PI/2,a1=(i+.5)*Math.PI/10-Math.PI/2;c.beginPath();c.arc(0,0,r1,a0,a1);c.arc(0,0,r0,a1,a0,true);c.closePath()};
 for(let i=0;i<20;i++){const e=i%2===0;
  c.fillStyle=e?'#15110f':'#cdbb94';ring(R*.1,R*.95,i);c.fill();
  c.fillStyle=e?'#8a1a1a':'#1d6a3e';ring(R*.58,R*.65,i);c.fill();ring(R*.88,R*.95,i);c.fill();
  c.strokeStyle='#8f8f8f';c.lineWidth=2;ring(R*.1,R*.95,i);c.stroke()}
 c.fillStyle='#1d6a3e';c.beginPath();c.arc(0,0,R*.1,0,7);c.fill();
 c.fillStyle='#8a1a1a';c.beginPath();c.arc(0,0,R*.04,0,7);c.fill();
 c.restore()}
function icon(kind,x,y,s,col){c.save();c.translate(x,y);c.strokeStyle=col;c.fillStyle=col;c.lineWidth=s*.08;c.lineJoin='round';c.lineCap='round';
 if(kind==='cal'){rr(-s/2,-s*.42,s,s*.9,s*.12);c.stroke();c.fillRect(-s/2,-s*.42,s,s*.24);
  for(const dx of[-.26,.26]){rr(dx*s-s*.04,-s*.55,s*.08,s*.2,s*.04);c.fill()}
  for(let i=0;i<9;i++)c.fillRect(-s*.34+(i%3)*s*.25,-s*.08+Math.floor(i/3)*s*.2,s*.15,s*.12)}
 if(kind==='clock'){c.beginPath();c.arc(0,0,s*.48,0,7);c.stroke();c.beginPath();c.moveTo(0,-s*.28);c.lineTo(0,0);c.lineTo(s*.2,s*.12);c.stroke()}
 if(kind==='pin'){c.beginPath();c.moveTo(0,s*.55);c.bezierCurveTo(-s*.55,-.05*s,-s*.42,-s*.5,0,-s*.5);c.bezierCurveTo(s*.42,-s*.5,s*.55,-.05*s,0,s*.55);c.fill();
  c.fillStyle='#0b0707';c.beginPath();c.arc(0,-s*.1,s*.16,0,7);c.fill()}
 if(kind==='ppl'){const p=(dx,dy,k)=>{c.beginPath();c.arc(dx,dy-s*.18*k,s*.13*k,0,7);c.fill();c.beginPath();c.ellipse(dx,dy+s*.14*k,s*.25*k,s*.16*k,0,Math.PI,0);c.fill()};
  p(-s*.3,s*.08,.8);p(s*.3,s*.08,.8);p(0,0,1)}
 c.restore()}
async function logo(t,cx,cy,R,tm,t0){
 c.save();
 const col=(tm&&tm.color)||'#dd4a47';
 c.shadowColor=col;c.shadowBlur=40;c.fillStyle='#000';c.beginPath();c.arc(cx,cy,R,0,7);c.fill();c.restore();
 const im=tm&&tm.logo?await load(tm.logo):null;
 c.save();
 if(im){
    const own=D.own&&t0.toLowerCase()===D.own.toLowerCase();
  if(!own&&tm.mode==='round'){c.beginPath();c.arc(cx,cy,R,0,7);c.clip();const s=R*2.02;c.drawImage(im,cx-s/2,cy-s/2,s,s)}
  else if(!own){c.fillStyle='#fff';c.beginPath();c.arc(cx,cy,R,0,7);c.fill();c.beginPath();c.arc(cx,cy,R,0,7);c.clip();const s=R*1.7;c.drawImage(im,cx-s/2,cy-s/2,s,s)}
  else{const s=R*2.04;c.drawImage(im,cx-s/2,cy-s/2,s,s)}
 }else{
  const ini=t.split(/[^A-Za-zÄÖÜäöü0-9]+/).filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase();
  c.fillStyle=col;c.beginPath();c.arc(cx,cy,R,0,7);c.fill();txt(ini,cx,cy+R*.3,R*.95,'#fff',{a:'center'})}
 c.restore();
 c.save();c.strokeStyle=col;c.lineWidth=5;c.shadowColor=col;c.shadowBlur=22;c.beginPath();c.arc(cx,cy,R+2,0,7);c.stroke();c.restore()}
function dots(form,cx,y){const n=form.length,g=34,x0=cx-(n-1)*g/2;form.forEach((w,i)=>{c.fillStyle=w?'#4fb27c':'#dd4a47';c.beginPath();c.arc(x0+i*g,y,10,0,7);c.fill()})}
async function draw(){
 const f=D.fixtures[+$('sel').value];if(!f)return;
 const hm=D.teams[f.home.toLowerCase()]||{},gm=D.teams[f.guest.toLowerCase()]||{};
 const time=($('time').value||'20:00').trim(),sup=($('sup').value||'').toUpperCase(),showT=$('tab').checked;
 await document.fonts.load('100px Bebas');
 // Hintergrund
 c.fillStyle='#090505';c.fillRect(0,0,W,H);
 let g=c.createRadialGradient(150,100,0,150,100,800);g.addColorStop(0,'#3a0c0e');g.addColorStop(1,'#090505');c.fillStyle=g;c.fillRect(0,0,W,H);
 board(1010,820,560);
 g=c.createLinearGradient(0,0,W,0);g.addColorStop(0,'rgba(9,5,5,.97)');g.addColorStop(.55,'rgba(9,5,5,.9)');g.addColorStop(1,'rgba(9,5,5,.45)');c.fillStyle=g;c.fillRect(0,0,W,H);
 g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,'rgba(9,5,5,.1)');g.addColorStop(.75,'rgba(9,5,5,.3)');g.addColorStop(1,'rgba(9,5,5,.85)');c.fillStyle=g;c.fillRect(0,0,W,H);
 for(let i=0;i<2600;i++){const x=Math.pow(rnd(),2.4)*W*.5,y=rnd()*H,a=rnd()*.5;c.fillStyle=`rgba(200,20,25,${a})`;c.fillRect(x,y,rnd()*3+1,rnd()*3+1)}
 // Kopf
 const vf=await load(D.vfc);if(vf){const h=210,w=h*vf.width/vf.height;c.drawImage(vf,52,40,w,h)}
 const cx=690;
 txt('LIGABEGEGNUNG',cx,190,128,metal(80,120,'#8c8c8c','#f1f1f1'),{a:'center',skew:1,shadow:'#000',sb:8,max:660});
 txt(D.season,cx,330,170,metal(190,150,'#5a0d10','#d2282c'),{a:'center',skew:1,max:620});
 c.fillStyle='#c01e22';c.fillRect(cx-330,392,96,4);c.fillRect(cx+234,392,96,4);
 txt(D.sport,cx,408,44,'#bdbdbd',{a:'center',ls:12});
 // Datum
 const d=dp(f.date),wd=d?d.toLocaleDateString('de-CH',{weekday:'long'}).toUpperCase():'';
 rr(225,450,630,125,22);c.fillStyle='rgba(0,0,0,.55)';c.fill();c.strokeStyle='#8a1a1a';c.lineWidth=3;c.stroke();
 icon('cal',295,512,76,'#b0171b');txt(wd,355,500,44,'#c01e22');txt(f.date.replace(/\.(\d\d)$/,'.$1'),355,552,52,'#c9c9c9');
 c.fillStyle='#4a2a2a';c.fillRect(549,470,2,86);
 icon('clock',610,512,76,'#b0171b');txt('START',668,500,44,'#c01e22');txt(time+' UHR',668,552,52,'#c9c9c9');
 // Teams
 txt('HEIMTEAM',270,650,52,'#8e1214',{a:'center',ls:2});txt('GASTTEAM',810,650,52,'#8e1214',{a:'center',ls:2});
 await logo(f.home,270,865,185,hm,f.home);await logo(f.guest,810,865,185,gm,f.guest);
 c.save();c.strokeStyle='rgba(220,40,40,.8)';c.lineWidth=3;c.shadowColor='#e02020';c.shadowBlur=18;c.beginPath();c.moveTo(585,700);c.lineTo(495,1040);c.stroke();c.restore();
 txt('VS',540,905,190,metal(790,150,'#777','#e8e8e8'),{a:'center',skew:1,shadow:'#000',sb:12});
 for(const [t,x,m] of [[f.home,270,hm],[f.guest,810,gm]]){
  txt(t.toUpperCase(),x,1100,50,'#dcdcdc',{a:'center',max:480});
  if(showT&&m.rank){txt(`PLATZ ${m.rank}  ·  ${m.pp}:${m.pm} PUNKTE`,x,1136,32,'#9a8f90',{a:'center',ls:1});if(m.form&&m.form.length)dots(m.form,x,1166)}}
 // Fuss
 const y0=1190,h0=146;rr(55,y0,970,h0,20);c.fillStyle='rgba(0,0,0,.6)';c.fill();c.strokeStyle='#8a1a1a';c.lineWidth=3;c.stroke();
 c.fillStyle='#4a2a2a';c.fillRect(540,y0+18,2,h0-36);
 const ho=hm.lokal||f.place||'';
 icon('pin',108,y0+40,52,'#b0171b');txt('SPIELORT',138,y0+55,46,'#c01e22');
 const lines=[hm.lokal,hm.strasse,hm.ort].filter(Boolean);if(!lines.length&&f.place)lines.push(f.place);
 lines.slice(0,3).forEach((l,i)=>txt(l.toUpperCase(),138,y0+86+i*25,24,'#c4c4c4',{max:380}));
 icon('ppl',585,y0+42,58,'#b0171b');txt('SUPPORT',630,y0+56,46,'#c01e22');
 const w=sup.split(' ');let l1='',l2='';for(const x of w){if((l1+' '+x).trim().length<=26&&!l2)l1=(l1+' '+x).trim();else l2=(l2+' '+x).trim()}
 txt(l1,585,y0+96,28,'#c4c4c4',{max:420});if(l2)txt(l2,585,y0+126,28,'#c4c4c4',{max:420});
}
// Auswahl
const sel=$('sel');
const mine=D.fixtures.map((f,i)=>[f,i]).filter(([f])=>D.own&&(f.home===D.own||f.guest===D.own));
const opt=([f,i])=>`<option value="${i}">${f.date} · ${f.home} – ${f.guest}</option>`;
const ids=new Set(mine.map(m=>m[1]));
sel.innerHTML=(mine.length?`<optgroup label="Unser Verein">${mine.map(opt).join('')}</optgroup>`:'')+`<optgroup label="Ganze Liga">${D.fixtures.map((f,i)=>[f,i]).filter(([f,i])=>!ids.has(i)).map(opt).join('')}</optgroup>`;
if(mine.length)sel.value=mine[0][1];
for(const id of['sel','time','sup','tab'])$(id).addEventListener('input',draw);
function blob(){return new Promise(r=>cv.toBlob(r,'image/png'))}
function nm(){const f=D.fixtures[+sel.value];return 'flyer-'+f.date.split('.').reverse().join('-')+'-'+f.home.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'.png'}
$('dl').onclick=async()=>{const b=await blob(),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=nm();a.click();setTimeout(()=>URL.revokeObjectURL(a.href),4000)};
$('sh').onclick=async()=>{const b=await blob(),file=new File([b],nm(),{type:'image/png'});try{await navigator.share({files:[file]})}catch(_){}};
try{if(navigator.canShare&&navigator.canShare({files:[new File([''],'a.png',{type:'image/png'})]}))$('sh').hidden=false}catch(_){}
draw();
})();
