(()=>{
const D=JSON.parse(document.getElementById('fd').textContent);
const W=1080,H=1350,cv=document.getElementById('cv'),c=cv.getContext('2d');
cv.width=W;cv.height=H;
const $=id=>document.getElementById(id);
const BEB='"Bebas","Arial Narrow",Impact,sans-serif',SERIF='Georgia,"Iowan Old Style","Times New Roman",serif',SANS='"Helvetica Neue",Arial,system-ui,sans-serif';
const imgs={};
const load=src=>!src?Promise.resolve(null):(imgs[src]||(imgs[src]=new Promise(r=>{const i=new Image();i.onload=()=>r(i);i.onerror=()=>r(null);i.src=src})));
const dp=s=>{const m=/(\d+)\.(\d+)\.(\d+)/.exec(s);return m?new Date(2000+ +m[3],+m[2]-1,+m[1]):null};
const rnd0=s=>()=>(s=(s*16807)%2147483647)/2147483647;
function rr(x,y,w,h,r){c.beginPath();c.roundRect(x,y,w,h,r)}
function hex(h){const n=parseInt(h.slice(1),16);return[n>>16,n>>8&255,n&255]}
function shade(h,k,a=1){const[r,g,b]=hex(h);return`rgba(${r*k|0},${g*k|0},${b*k|0},${a})`}
function tint(h,k,a=1){const[r,g,b]=hex(h);return`rgba(${r+(255-r)*k|0},${g+(255-g)*k|0},${b+(255-b)*k|0},${a})`}
function txt(t,x,y,size,fill,o={}){c.save();c.font=`${o.w||''} ${size}px ${o.f||BEB}`;c.textAlign=o.a||'left';c.textBaseline='alphabetic';
 if(c.letterSpacing!==undefined)c.letterSpacing=(o.ls||0)+'px';
 if(o.max){const w=c.measureText(t).width;if(w>o.max){size=size*o.max/w;c.font=`${o.w||''} ${size}px ${o.f||BEB}`}}
 if(o.skew)c.transform(1,0,-0.2,1,0.2*y,0);
 if(o.shadow){c.shadowColor=o.shadow;c.shadowBlur=o.sb||18}
 if(o.stroke){c.lineWidth=o.sw||3;c.strokeStyle=o.stroke;c.strokeText(t,x,y)}
 if(fill){c.fillStyle=fill;c.fillText(t,x,y)}
 c.restore()}
function metal(y,h,a,b){const g=c.createLinearGradient(0,y,0,y+h);g.addColorStop(0,a);g.addColorStop(.55,b);g.addColorStop(1,a);return g}
function wrap(t,n){const w=t.split(' ');let l1='',l2='';for(const x of w){if((l1+' '+x).trim().length<=n&&!l2)l1=(l1+' '+x).trim();else l2=(l2+' '+x).trim()}return[l1,l2].filter(Boolean)}
function board(cx,cy,R){
 c.save();c.translate(cx,cy);
 c.fillStyle='#1a1512';c.beginPath();c.arc(0,0,R*1.08,0,7);c.fill();
 const ring=(r0,r1,i)=>{const a0=(i-.5)*Math.PI/10-Math.PI/2,a1=(i+.5)*Math.PI/10-Math.PI/2;c.beginPath();c.arc(0,0,r1,a0,a1);c.arc(0,0,r0,a1,a0,true);c.closePath()};
 for(let i=0;i<20;i++){const e=i%2===0;
  c.fillStyle=e?'#15110f':'#cdbb94';ring(R*.1,R*.95,i);c.fill();
  c.fillStyle=e?'#8a1a1a':'#1d6a3e';ring(R*.58,R*.65,i);c.fill();ring(R*.88,R*.95,i);c.fill();
  c.strokeStyle='#8f8f8f';c.lineWidth=2;ring(R*.1,R*.95,i);c.stroke()}
 c.fillStyle='#1d6a3e';c.beginPath();c.arc(0,0,R*.1,0,7);c.fill();c.fillStyle='#8a1a1a';c.beginPath();c.arc(0,0,R*.04,0,7);c.fill();
 c.restore()}
function icon(kind,x,y,s,col,hole='#0b0707'){c.save();c.translate(x,y);c.strokeStyle=col;c.fillStyle=col;c.lineWidth=s*.08;c.lineJoin='round';c.lineCap='round';
 if(kind==='cal'){rr(-s/2,-s*.42,s,s*.9,s*.12);c.stroke();c.fillRect(-s/2,-s*.42,s,s*.24);
  for(const dx of[-.26,.26]){rr(dx*s-s*.04,-s*.55,s*.08,s*.2,s*.04);c.fill()}
  for(let i=0;i<9;i++)c.fillRect(-s*.34+(i%3)*s*.25,-s*.08+Math.floor(i/3)*s*.2,s*.15,s*.12)}
 if(kind==='clock'){c.beginPath();c.arc(0,0,s*.48,0,7);c.stroke();c.beginPath();c.moveTo(0,-s*.28);c.lineTo(0,0);c.lineTo(s*.2,s*.12);c.stroke()}
 if(kind==='pin'){c.beginPath();c.moveTo(0,s*.55);c.bezierCurveTo(-s*.55,-.05*s,-s*.42,-s*.5,0,-s*.5);c.bezierCurveTo(s*.42,-s*.5,s*.55,-.05*s,0,s*.55);c.fill();
  c.fillStyle=hole;c.beginPath();c.arc(0,-s*.1,s*.16,0,7);c.fill()}
 if(kind==='ppl'){const p=(dx,dy,k)=>{c.beginPath();c.arc(dx,dy-s*.18*k,s*.13*k,0,7);c.fill();c.beginPath();c.ellipse(dx,dy+s*.14*k,s*.25*k,s*.16*k,0,Math.PI,0);c.fill()};
  p(-s*.3,s*.08,.8);p(s*.3,s*.08,.8);p(0,0,1)}
 c.restore()}
async function logo(t,cx,cy,R,tm,o={}){
 const col=o.col||(tm&&tm.color)||'#dd4a47';
 c.save();if(o.glow!==false){c.shadowColor=o.shadowCol||col;c.shadowBlur=o.sb||36}else{c.shadowColor='rgba(0,0,0,.25)';c.shadowBlur=22;c.shadowOffsetY=8}
 c.fillStyle='#111';c.beginPath();c.arc(cx,cy,R,0,7);c.fill();c.restore();
 const im=tm&&tm.logo?await load(tm.logo):null;
 const own=D.own&&t.toLowerCase()===D.own.toLowerCase();
 c.save();
 if(im){
  if(!own&&tm.mode==='round'){c.beginPath();c.arc(cx,cy,R,0,7);c.clip();const s=R*2.02;c.drawImage(im,cx-s/2,cy-s/2,s,s)}
  else if(!own){c.fillStyle='#fff';c.beginPath();c.arc(cx,cy,R,0,7);c.fill();c.beginPath();c.arc(cx,cy,R,0,7);c.clip();const s=R*1.7;c.drawImage(im,cx-s/2,cy-s/2,s,s)}
  else{const s=R*2.04;c.drawImage(im,cx-s/2,cy-s/2,s,s)}
 }else{
  const ini=t.split(/[^A-Za-zÄÖÜäöü0-9]+/).filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase();
  c.fillStyle=col;c.beginPath();c.arc(cx,cy,R,0,7);c.fill();txt(ini,cx,cy+R*.3,R*.95,'#fff',{a:'center'})}
 c.restore();
 if(o.ring!==0){c.save();c.strokeStyle=col;c.lineWidth=o.ring||5;if(o.glow!==false){c.shadowColor=col;c.shadowBlur=22}c.beginPath();c.arc(cx,cy,R+2,0,7);c.stroke();c.restore()}}
function dots(form,cx,y,g=34,r=10,align='c',pc='#4fb27c',nc='#dd4a47'){const n=form.length,x0=align==='c'?cx-(n-1)*g/2:cx;form.forEach((w,i)=>{c.fillStyle=w?pc:nc;c.beginPath();c.arc(x0+i*g,y,r,0,7);c.fill()})}
const platz=m=>`PLATZ ${m.rank}  ·  ${m.pp}:${m.pm} PUNKTE`;
function venue(S){const l=[S.hm.lokal,S.hm.strasse,S.hm.ort].filter(Boolean);if(!l.length&&S.f.place)l.push(S.f.place);return l.slice(0,3)}

/* ---------- Design 0: Klassisch dunkel ---------- */
const T0={
 bg(S){
  c.fillStyle='#090505';c.fillRect(0,0,W,H);
  let g=c.createRadialGradient(150,100,0,150,100,800);g.addColorStop(0,'#3a0c0e');g.addColorStop(1,'#090505');c.fillStyle=g;c.fillRect(0,0,W,H);
  board(1010,820,560);
  g=c.createLinearGradient(0,0,W,0);g.addColorStop(0,'rgba(9,5,5,.97)');g.addColorStop(.55,'rgba(9,5,5,.9)');g.addColorStop(1,'rgba(9,5,5,.45)');c.fillStyle=g;c.fillRect(0,0,W,H);
  g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,'rgba(9,5,5,.1)');g.addColorStop(.75,'rgba(9,5,5,.3)');g.addColorStop(1,'rgba(9,5,5,.85)');c.fillStyle=g;c.fillRect(0,0,W,H);
  const rnd=rnd0(7);for(let i=0;i<2600;i++){const x=Math.pow(rnd(),2.4)*W*.5,y=rnd()*H,a=rnd()*.5;c.fillStyle=`rgba(200,20,25,${a})`;c.fillRect(x,y,rnd()*3+1,rnd()*3+1)}},
 async content(S){
  const{f,hm,gm}=S;
  if(S.vf){const h=210,w=h*S.vf.width/S.vf.height;c.drawImage(S.vf,52,40,w,h)}
  const cx=690;
  txt('LIGABEGEGNUNG',cx,190,128,metal(80,120,'#8c8c8c','#f1f1f1'),{a:'center',skew:1,shadow:'#000',sb:8,max:660});
  txt(D.season,cx,330,170,metal(190,150,'#5a0d10','#d2282c'),{a:'center',skew:1,max:620});
  c.fillStyle='#c01e22';c.fillRect(cx-330,392,96,4);c.fillRect(cx+234,392,96,4);
  txt(D.sport,cx,408,44,'#bdbdbd',{a:'center',ls:12});
  rr(225,450,630,125,22);c.fillStyle='rgba(0,0,0,.55)';c.fill();c.strokeStyle='#8a1a1a';c.lineWidth=3;c.stroke();
  icon('cal',295,512,76,'#b0171b');txt(S.wd,355,500,44,'#c01e22');txt(f.date,355,552,52,'#c9c9c9');
  c.fillStyle='#4a2a2a';c.fillRect(549,470,2,86);
  icon('clock',610,512,76,'#b0171b');txt('START',668,500,44,'#c01e22');txt(S.time+' UHR',668,552,52,'#c9c9c9');
  txt('HEIMTEAM',250,650,52,'#8e1214',{a:'center',ls:2});txt('GASTTEAM',830,650,52,'#8e1214',{a:'center',ls:2});
  await logo(f.home,250,850,168,hm);await logo(f.guest,830,850,168,gm);
  c.save();c.strokeStyle='rgba(220,40,40,.8)';c.lineWidth=3;c.shadowColor='#e02020';c.shadowBlur=18;c.beginPath();c.moveTo(565,700);c.lineTo(515,1010);c.stroke();c.restore();
  txt('VS',540,895,140,metal(790,110,'#777','#e8e8e8'),{a:'center',skew:1,shadow:'#000',sb:12});
  for(const[t,x,m]of[[f.home,250,hm],[f.guest,830,gm]]){
   txt(t.toUpperCase(),x,1068,50,'#dcdcdc',{a:'center',max:470});
   if(S.showT&&m.rank){txt(platz(m),x,1104,32,'#9a8f90',{a:'center',ls:1});if(m.form&&m.form.length)dots(m.form,x,1136)}}
  const y0=1168,h0=164;rr(55,y0,970,h0,20);c.fillStyle='rgba(0,0,0,.6)';c.fill();c.strokeStyle='#8a1a1a';c.lineWidth=3;c.stroke();
  c.fillStyle='#4a2a2a';c.fillRect(540,y0+18,2,h0-36);
  icon('pin',108,y0+40,52,'#b0171b');txt('SPIELORT',138,y0+56,46,'#c01e22');
  venue(S).forEach((l,i)=>txt(l.toUpperCase(),138,y0+92+i*30,29,'#c4c4c4',{max:380}));
  icon('ppl',585,y0+42,58,'#b0171b');txt('SUPPORT',630,y0+56,46,'#c01e22');
  wrap(S.sup,26).forEach((l,i)=>txt(l,585,y0+104+i*38,32,'#c4c4c4',{max:430}))}};

/* ---------- Design 1: Clean (Webseiten-Look) ---------- */
const T1={
 bg(){c.fillStyle='#f5f4f3';c.fillRect(0,0,W,H)},
 async content(S){
  const{f,hm,gm}=S,INK='#1b1416',MUTE='#675d60',RED='#9a1b1c';
  c.fillStyle='#17100f';c.fillRect(0,0,W,236);c.fillStyle=RED;c.fillRect(0,236,W,8);
  if(S.vf){const h=150,w=h*S.vf.width/S.vf.height;c.drawImage(S.vf,56,44,w,h)}
  txt('LIGABEGEGNUNG',1024,112,72,'#f4eeee',{a:'right',f:SERIF,w:'bold',max:700});
  txt(`${D.season}  ·  ${D.sport}`,1024,178,46,'#e0605a',{a:'right',ls:4,max:700});
  const card=(x,y,w,h,r=26)=>{c.save();c.shadowColor='rgba(40,20,20,.14)';c.shadowBlur=26;c.shadowOffsetY=8;rr(x,y,w,h,r);c.fillStyle='#fff';c.fill();c.restore();rr(x,y,w,h,r);c.strokeStyle='#ddd8d9';c.lineWidth=2;c.stroke()};
  card(55,290,970,150);
  icon('cal',130,365,70,RED,'#fff');txt(S.wd,185,350,40,RED,{ls:2});txt(f.date,185,410,64,INK,{f:SERIF,w:'bold'});
  c.fillStyle='#ddd8d9';c.fillRect(560,312,2,106);
  icon('clock',630,365,70,RED);txt('START',685,350,40,RED,{ls:2});txt(S.time+' UHR',685,410,64,INK,{f:SERIF,w:'bold'});
  for(const[t,x,m,lab]of[[f.home,55,hm,'HEIMTEAM'],[f.guest,555,gm,'GASTTEAM']]){
   card(x,480,470,540);
   c.save();rr(x,480,470,540,26);c.clip();c.fillStyle=m.colorL||RED;c.fillRect(x,480,470,12);c.restore();
   txt(lab,x+235,552,42,MUTE,{a:'center',ls:4});
   await logo(t,x+235,720,140,m,{glow:false,ring:6,col:m.colorL||RED});
   txt(t,x+235,925,44,INK,{a:'center',f:SERIF,w:'bold',max:420});
   if(S.showT&&m.rank){txt(platz(m),x+235,968,30,MUTE,{a:'center',f:SANS,ls:.5,max:420});if(m.form&&m.form.length)dots(m.form,x+235,1000,34,9,'c','#1d6a3e',RED)}}
  c.save();c.shadowColor='rgba(0,0,0,.3)';c.shadowBlur=16;c.fillStyle='#17100f';c.beginPath();c.arc(540,720,44,0,7);c.fill();c.restore();
  txt('VS',540,737,50,'#f4eeee',{a:'center',ls:1});
  card(55,1048,970,192);
  icon('pin',112,1100,50,RED,'#fff');txt('SPIELORT',146,1114,48,RED,{ls:2});
  venue(S).forEach((l,i)=>txt(l,100,1160+i*32,28,INK,{f:SERIF,max:390}));
  c.fillStyle='#ddd8d9';c.fillRect(540,1072,2,144);
  icon('ppl',596,1100,56,RED);txt('SUPPORT',640,1114,48,RED,{ls:2});
  wrap(S.sup,28).forEach((l,i)=>txt(l,586,1164+i*34,28,INK,{f:SERIF,max:420}))}};

/* ---------- Design 2: Split in Vereinsfarben ---------- */
const T2={
 bg(S){
  const hc=S.hm.color||'#dd4a47',gc=S.gm.color||'#4fd1c5';
  c.fillStyle='#050505';c.fillRect(0,0,W,H);
  const poly=(pts,a,b)=>{const g=c.createLinearGradient(0,0,0,H);g.addColorStop(0,a);g.addColorStop(1,b);c.fillStyle=g;c.beginPath();pts.forEach(([x,y],i)=>i?c.lineTo(x,y):c.moveTo(x,y));c.closePath();c.fill()};
  poly([[0,0],[640,0],[440,H],[0,H]],shade(hc,.62),shade(hc,.16));
  poly([[640,0],[W,0],[W,H],[440,H]],shade(gc,.62),shade(gc,.16));
  c.save();c.strokeStyle='rgba(255,255,255,.85)';c.lineWidth=5;c.shadowColor='#fff';c.shadowBlur=24;c.beginPath();c.moveTo(640,0);c.lineTo(440,H);c.stroke();c.restore();
  c.save();c.globalAlpha=.07;c.strokeStyle='#fff';c.lineWidth=3;for(let r=120;r<900;r+=110){c.beginPath();c.arc(540,700,r,0,7);c.stroke()}c.restore();
  const g=c.createLinearGradient(0,H*.6,0,H);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'rgba(0,0,0,.75)');c.fillStyle=g;c.fillRect(0,0,W,H)},
 async content(S){
  const{f,hm,gm}=S;
  txt('LIGABEGEGNUNG',540,150,118,'#fff',{a:'center',skew:1,shadow:'#000',sb:20,max:900});
  txt(`${D.season}  ·  ${D.sport}`,540,214,50,'rgba(255,255,255,.85)',{a:'center',ls:6,max:900});
  rr(210,262,660,118,60);c.fillStyle='rgba(0,0,0,.62)';c.fill();c.strokeStyle='rgba(255,255,255,.5)';c.lineWidth=2;c.stroke();
  txt(`${S.wd}  ${f.date}`,540,342,66,'#fff',{a:'center',max:560});
  txt(`START ${S.time} UHR`,540,436,52,'rgba(255,255,255,.9)',{a:'center',ls:3,shadow:'#000',sb:10});
  txt('HEIMTEAM',250,540,48,'rgba(255,255,255,.7)',{a:'center',ls:6});txt('GASTTEAM',830,540,48,'rgba(255,255,255,.7)',{a:'center',ls:6});
  await logo(f.home,250,745,175,hm,{col:'#fff',ring:6});await logo(f.guest,830,745,175,gm,{col:'#fff',ring:6});
  txt('VS',540,800,150,'#fff',{a:'center',skew:1,shadow:'#000',sb:26});
  for(const[t,x,m]of[[f.home,250,hm],[f.guest,830,gm]]){
   txt(t.toUpperCase(),x,1000,64,'#fff',{a:'center',max:470,shadow:'#000',sb:14});
   if(S.showT&&m.rank){txt(platz(m),x,1042,32,'rgba(255,255,255,.8)',{a:'center',ls:1,max:470});if(m.form&&m.form.length)dots(m.form,x,1076,34,10,'c','#7fe0a5','#ff8a85')}}
  const y0=1126,h0=186;rr(55,y0,970,h0,24);c.fillStyle='rgba(0,0,0,.7)';c.fill();
  icon('pin',108,y0+48,54,'#fff','#000');txt('SPIELORT',142,y0+62,50,'#fff',{ls:2});
  venue(S).forEach((l,i)=>txt(l.toUpperCase(),96,y0+108+i*34,30,'rgba(255,255,255,.85)',{max:400}));
  c.fillStyle='rgba(255,255,255,.3)';c.fillRect(540,y0+22,2,h0-44);
  icon('ppl',590,y0+48,58,'#fff');txt('SUPPORT',634,y0+62,50,'#fff',{ls:2});
  wrap(S.sup,26).forEach((l,i)=>txt(l,584,y0+112+i*40,34,'rgba(255,255,255,.85)',{max:430}))}};

/* ---------- Design 3: Editorial ---------- */
const T3={
 bg(S){
  const ac=S.hm.color||'#dd4a47';
  c.fillStyle='#0a0a0a';c.fillRect(0,0,W,H);
  c.save();c.strokeStyle=shade(ac,1,.13);c.lineWidth=3;for(let r=110;r<760;r+=95){c.beginPath();c.arc(1010,250,r,0,7);c.stroke()}c.restore();
  c.fillStyle=ac;c.fillRect(0,0,16,H)},
 async content(S){
  const{f,hm,gm}=S,ac=hm.color||'#dd4a47',[dd,mm]=f.date.split('.');
  txt('LIGABEGEGNUNG',72,118,56,'#8a8a8a',{ls:10});
  txt(`${D.season}  ·  ${D.sport}`,72,180,56,ac,{ls:6,max:900});
  txt(S.wd,72,300,92,'#fff',{ls:8});
  txt(`${dd}.${mm}.`,60,590,360,'#fff',{max:900});
  txt(`START ${S.time} UHR`,72,668,64,'#8a8a8a',{ls:5});
  c.fillStyle='#2a2a2a';c.fillRect(72,712,936,3);
  const row=async(t,m,y,lab)=>{
   await logo(t,160,y,78,m,{col:m.color,ring:4,sb:20});
   txt(lab,270,y-42,34,ac,{ls:6});
   txt(t.toUpperCase(),270,y+30,84,'#fff',{max:720});
   if(S.showT&&m.rank){txt(platz(m),270,y+68,32,'#8a8a8a',{ls:1});if(m.form&&m.form.length)dots(m.form,1008-(m.form.length-1)*32,y+58,32,9,'l','#4fb27c','#dd4a47')}};
  await row(f.home,hm,810,'HEIMTEAM');
  txt('VS',72,935,56,'#555',{ls:6});c.fillStyle='#2a2a2a';c.fillRect(160,918,848,3);
  await row(f.guest,gm,1050,'GASTTEAM');
  c.fillStyle='#2a2a2a';c.fillRect(72,1160,936,3);
  txt('SPIELORT',72,1218,44,ac,{ls:4});
  venue(S).forEach((l,i)=>txt(l.toUpperCase(),72,1258+i*32,28,'#cfcfcf',{max:430}));
  txt('SUPPORT',570,1218,44,ac,{ls:4});
  wrap(S.sup,30).forEach((l,i)=>txt(l,570,1258+i*34,30,'#cfcfcf',{max:440}))}};
const TPL=[T0,T1,T2,T3];

/* ---------- Sponsorenleiste ---------- */
async function sponsorBar(list,light){
 const y=1270,h=66;rr(55,y,970,h,20);c.fillStyle='rgba(255,255,255,.96)';c.fill();if(light){c.strokeStyle='#ddd8d9';c.lineWidth=2;c.stroke()}
 const n=list.length,cell=970/n;
 for(let i=0;i<n;i++){const s=list[i],cx=55+cell*(i+.5),im=await load(s.img);
  if(im){let bh=46,bw=bh*im.width/im.height;const mw=cell-34;if(bw>mw){bw=mw;bh=bw*im.height/im.width}
   if(s.icon){const k=46;c.save();rr(cx-k-4,y+10,k,k,10);c.clip();c.drawImage(im,cx-k-4,y+10,k,k);c.restore();txt('LEAVE26',cx+2,y+46,40,'#17100f',{ls:1})}
   else c.drawImage(im,cx-bw/2,y+(h-bh)/2,bw,bh)}
  else txt(s.name.toUpperCase(),cx,y+46,40,'#17100f',{a:'center',ls:1,max:cell-24})}}

async function draw(){
 const f=D.fixtures[+$('sel').value];if(!f)return;
 const hm=D.teams[f.home.toLowerCase()]||{},gm=D.teams[f.guest.toLowerCase()]||{};
 await document.fonts.load('100px Bebas');
 const d=dp(f.date);
 const S={f,hm,gm,time:($('time').value||'20:00').trim(),sup:($('sup').value||'').toUpperCase(),showT:$('tab').checked,
  wd:d?d.toLocaleDateString('de-CH',{weekday:'long'}).toUpperCase():'',vf:await load(D.vfc)};
 const sp=D.sponsors.filter(s=>$('sp-'+s.key)&&$('sp-'+s.key).checked);
 const t=TPL[+$('tpl').value]||T0;
 c.clearRect(0,0,W,H);
 t.bg(S);
 c.save();if(sp.length){const k=.935;c.translate((1-k)*W/2,0);c.scale(k,k)}
 await t.content(S);
 c.restore();
 if(sp.length)await sponsorBar(sp,+$('tpl').value===1)}

const sel=$('sel');
const mine=D.fixtures.map((f,i)=>[f,i]).filter(([f])=>D.own&&(f.home===D.own||f.guest===D.own));
const opt=([f,i])=>`<option value="${i}">${f.date} · ${f.home} – ${f.guest}</option>`;
const ids=new Set(mine.map(m=>m[1]));
sel.innerHTML=(mine.length?`<optgroup label="Unser Verein">${mine.map(opt).join('')}</optgroup>`:'')+`<optgroup label="Ganze Liga">${D.fixtures.map((f,i)=>[f,i]).filter(([f,i])=>!ids.has(i)).map(opt).join('')}</optgroup>`;
if(mine.length)sel.value=mine[0][1];
$('spons').innerHTML=D.sponsors.map(s=>`<label><input type="checkbox" id="sp-${s.key}"${s.img?' checked':''}> ${s.name}</label>`).join('');
for(const id of['sel','time','sup','tab','tpl',...D.sponsors.map(s=>'sp-'+s.key)])$(id).addEventListener('input',draw);
function blob(){return new Promise(r=>cv.toBlob(r,'image/png'))}
function nm(){const f=D.fixtures[+sel.value];return 'flyer-'+f.date.split('.').reverse().join('-')+'-'+f.home.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'.png'}
$('dl').onclick=async()=>{const b=await blob();let d=null;try{d=window.claude&&await window.claude.use('downloads')}catch(_){}
 if(d){try{await d.save({filename:nm(),data:b})}catch(_){}return}
 const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=nm();a.click();setTimeout(()=>URL.revokeObjectURL(a.href),4000)};
$('sh').onclick=async()=>{const b=await blob(),file=new File([b],nm(),{type:'image/png'});try{await navigator.share({files:[file]})}catch(_){}};
try{if(navigator.canShare&&navigator.canShare({files:[new File([''],'a.png',{type:'image/png'})]}))$('sh').hidden=false}catch(_){}
draw();
})();
