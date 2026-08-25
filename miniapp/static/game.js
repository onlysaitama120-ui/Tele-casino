/* ============================================================
   GIFT RUSH  –  Game Engine  v8
   Premium Telegram Mini App
   ============================================================ */

const tg = window.Telegram?.WebApp;
if (tg){ tg.ready(); tg.expand(); }

let uid = null;
let gems = 0;
let spinsActive = false;
let WHEEL = [];
let invCache = [];
let bPick1 = null, bPick2 = null;

const $ = id => document.getElementById(id);
const RC = {common:"#8b93b5",uncommon:"#44dd77",rare:"#4488ff",epic:"#aa44ff",
  legendary:"#ffaa00",mythic:"#ff4444",divine:"#ffd700"};

/* ======================== UTILS ======================== */
function haptic(t){
  try{ if(!tg?.HapticFeedback) return;
    if(t==="win")tg.HapticFeedback.notificationOccurred("success");
    else if(t==="lose")tg.HapticFeedback.notificationOccurred("error");
    else tg.HapticFeedback.impactOccurred("light");
  }catch(e){}
}
function toast(m){
  const t=$("toast");t.textContent=m;t.classList.add("show");
  setTimeout(()=>t.classList.remove("show"),2800);
}
function setGems(v){
  gems=Number(v)||0;
  const c=$("coins");if(c)c.textContent=gems.toLocaleString();
  const p=$("profile-coins");if(p)p.textContent=gems.toLocaleString();
}
async function api(ep, body={}){
  const ctrl=new AbortController(), tm=setTimeout(()=>ctrl.abort(),15000);
  try{const r=await fetch(ep,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),signal:ctrl.signal});clearTimeout(tm);return await r.json();}
  catch(e){clearTimeout(tm);return{error:"Timed out or network error"};}
}
function confetti(n){
  n=n||50; const cols=["#ffd54a","#7c5cff","#39d353","#ff5252","#38bdf8"];
  for(let i=0;i<n;i++){const d=document.createElement("div");d.className="confetti";
  d.style.left=(35+Math.random()*30)+"%";d.style.background=cols[i%cols.length];
  d.style.animationDelay=(Math.random()*.4)+"s";
  d.style.transform="rotate("+(Math.random()*360)+"deg)";
  document.body.appendChild(d);setTimeout(()=>d.remove(),2800);}
}
function copyText(id){
  navigator.clipboard.writeText($(id).textContent)
    .then(()=>{toast("Copied!");haptic();}).catch(()=>toast("Copy failed"));
}

/* ======================== INIT ======================== */
async function initApp(){
  let ud=null;
  if(tg?.initDataUnsafe?.user){ud=tg.initDataUnsafe.user;uid=ud.id;}
  else{uid=123456789;ud={id:uid,username:"demo",first_name:"Player"};}
  const sp=parseStartParam();
  if(sp.inviteCode)window.__refCode=sp.inviteCode;

  const r=await api("/api/user",{user_id:uid,username:ud.username||"",first_name:ud.first_name||"",referral_code:window.__refCode||""});
  if(r.error||!r.id){$("loading").innerHTML="<p style='color:#ff7a7a;padding:24px;text-align:center'>"+JSON.stringify(r)+"</p>";return;}

  setGems(r.coins);
  $("username").textContent=r.first_name||r.username||"Player";
  $("user-avatar").textContent=(r.first_name||r.username||"P").charAt(0).toUpperCase();
  const el=("user-level");if(el)el.textContent=r.level||1;
  $("profile-username").textContent=r.username||"-";
  $("profile-refcode").textContent=r.referral_code||"-";
  $("ref-link").textContent="https://t.me/"+("MyCasinoBotx_bot")+"?start=ref_"+r.referral_code;
  $("ref-total").textContent=r.total_referrals||0;
  const xf=$("xp-fill");if(xf)xf.style.width=Math.min(((r.xp||0)/((r.level||1)*100))*100,100)+"%";
  $("profile-coins").textContent=gems.toLocaleString();
  $("profile-level").textContent=r.level||1;

  loadBoxes();loadTasks();initWheel();
  $("loading").classList.add("hidden");
  if(sp.command==="openWheelMain"||location.hash==="#wheel")showScreen("wheel");
}
document.addEventListener("DOMContentLoaded",()=>initApp().catch(e=>{console.error(e);const l=$("loading");if(l)l.innerHTML="<p style='color:#ff7a7a'>Error: "+e.message+"</p>";}));

/* ======================== NAVIGATION ======================== */
function showScreen(id){
  document.querySelectorAll(".screen").forEach(s=>s.classList.remove("active"));
  const el=$(id+"-screen");if(el)el.classList.add("active");
  document.querySelectorAll(".nav-btn").forEach(b=>b.classList.toggle("active",b.dataset.nav===id));
  haptic();window.scrollTo(0,0);
  const loaders={inventory:loadInventory,market:loadMarket,breed:loadBreed,
    tasks:loadTasks,leaderboard:()=>loadLeaderboard(),achievements:loadAchievements,
    referrals:loadReferrals,deposit:loadDeposit,withdraw:loadWithdraw,
    home:refreshBalance};
  if(loaders[id])loaders[id]();
}

/* ======================== CASES ======================== */
function loadBoxes(){
  [["cases-grid",true],["cases-grid-full",false]].forEach(([id,home])=>{
    const g=$(id);if(!g||!window.BOXES_DATA)return;
    const items=home?Object.entries(BOXES_DATA).slice(0,4):Object.entries(BOXES_DATA);
    g.innerHTML=items.map(([k,b])=>`<div class="case-card" style="--glow:${b.color}44" onclick="openBox('${k}')"><span class="case-emoji">${b.emoji}</span><h3>${b.name.replace(/ Box/,"")}</h3><div class="case-price">💎 ${Number(b.price).toLocaleString()}</div></div>`).join("");
  });
}
async function openBox(id){
  if(spinsActive)return;spinsActive=true;haptic();
  const r=await api("/api/case/open",{user_id:uid,case_id:id});
  if(!r.success){spinsActive=false;toast(r.message||"Not enough gems");return;}
  const strip=$("roll-strip");strip.style.transition="none";strip.style.transform="translateX(0)";strip.innerHTML="";
  const pool=[];Object.values(BOXES_DATA).forEach(b=>b.items.forEach(i=>pool.push(i)));const WIN=24;
  for(let i=0;i<34;i++){const it=i===WIN?r.item:pool[Math.floor(Math.random()*pool.length)];strip.innerHTML+=`<div class="roll-item" style="--rc:${RC[it.rarity]||"#333"}">${it.emoji||"🎁"}</div>`;}
  $("case-modal").classList.remove("hidden");$("reveal-card").classList.add("hidden");
  requestAnimationFrame(()=>{const tw=108;strip.style.transition="transform 3.5s cubic-bezier(.12,.78,.15,1)";strip.style.transform=`translateX(${-(WIN*tw)+158+Math.random()*36}px)`;});
  setTimeout(()=>{const it=r.item;$("revealed-item").textContent=it.emoji||"🎁";$("item-name").textContent=it.name;$("item-rarity").textContent=it.rarity;$("item-rarity").style.color=RC[it.rarity]||"#fff";$("item-value").textContent="💎 "+(it.value||0).toLocaleString();$("reveal-card").classList.remove("hidden");setGems(r.balance);haptic((it.value||0)>=2000?"win":"");spinsActive=false;},3700);
}
function closeCaseModal(){$("case-modal").classList.add("hidden");}

/* ======================== WHEEL ======================== */
async function initWheel(){
  try{const r=await fetch("/api/wheel/config");const d=await r.json();WHEEL=d.segments||[];buildWheel();updWheelStatus();}catch(e){console.error(e);}
}
function buildWheel(){
  const w=$("big-wheel");if(!w||!WHEEL.length)return;
  const n=WHEEL.length,step=360/n;
  const stops=WHEEL.map((s,i)=>s.color+" "+(i*step)+"deg "+((i+1)*step)+"deg");
  w.style.background="conic-gradient("+stops.join(", ")+")";
  WHEEL.forEach((s,i)=>{const el=document.createElement("div");el.className="seg-label";
  el.style.transform=`rotate(${i*step+step/2-90}deg) translate(74px) rotate(90deg)`;
  el.textContent=s.emoji+" "+s.label;if(s.type==="gift")el.style.color="#ffd54a";w.appendChild(el);});
}
async function updWheelStatus(){
  const r=await api("/api/wheel/status",{user_id:uid});const s=$("wheel-status");
  if(!s||r.error)return;
  if(r.free_available)s.textContent="FREE SPIN AVAILABLE!";
  else if((r.bonus_spins||0)>0)s.textContent=r.bonus_spins+" bonus spins";
  else s.textContent="Cost: 💎"+r.gem_cost;
}
async function spinWheel(){
  if(spinsActive||!WHEEL.length)return;spinsActive=true;
  const btn=$("wheel-spin-btn");btn.classList.add("spinning");btn.textContent="…";
  $("wheel-result").className="result-box hidden";
  $("wheel-pointer").classList.remove("bounce");haptic();
  const r=await api("/api/wheel/spin",{user_id:uid});
  if(!r.success){spinsActive=false;btn.classList.remove("spinning");btn.textContent="SPIN";
    toast(r.message||"Error");return;}
  const n=r.total_segments,step=360/n,mid=r.segment*step+step/2;
  $("big-wheel").style.transform=`rotate(${360*6-mid}deg)`;
  setTimeout(()=>{
    $("wheel-pointer").classList.add("bounce");
    $("big-wheel").classList.add("settle");setTimeout(()=>$("big-wheel").classList.remove("settle"),500);
    setTimeout(()=>{$("wheel-pointer").classList.remove("bounce");},600);
  },4700);
  setTimeout(()=>{
    spinsActive=false;btn.classList.remove("spinning");btn.textContent="SPIN";
    setGems(r.balance);updWheelStatus();
    const box=$("wheel-result");box.classList.remove("hidden");const p=r.prize;
    if(p.type==="gift"){box.className="result-box win";box.innerHTML=p.emoji+" <b>"+p.item_name+"</b> NFT won!";
    confetti(100);haptic("win");}
    else if(p.type==="gems"){box.className="result-box win";box.textContent="💎 +"+p.value+" gems!";
    if(p.value>=300)confetti(60);haptic("win");}
    else{box.className="result-box lose";box.textContent="So close! Try again";haptic("lose");}
  },5000);
}

/* ======================== DAILY ======================== */
async function claimDaily(){
  const r=await api("/api/daily",{user_id:uid});
  if(r.success){setGems(r.balance);$("daily-status").textContent="DONE";$("daily-status").style.opacity=".45";
    $("streak-days").textContent=r.streak||0;toast("🎁 +"+r.coins+" gems");haptic("win");}
  else toast("Next drop: "+(r.next_claim||"24h"));
}

/* ======================== DEPOSIT ======================== */
async function loadDeposit(){
  try{const r=await fetch("/api/deposit/info",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({user_id:uid})});const d=await r.json();
  $("dep-address").textContent=d.address||"-";$("dep-memo").textContent=d.memo||"-";
  $("dep-rate").textContent=d.gems_per_ton||1000;$("dep-min").textContent=d.min_ton||0.1;
  }catch(e){toast("Deposit info unavailable");}
}
async function checkDeposit(){
  $("deposit-result").classList.remove("hidden");$("deposit-result").className="result-box";
  $("deposit-result").textContent="Scanning...";
  const r=await api("/api/deposit/check",{user_id:uid});
  if(r.success){setGems(r.balance);$("deposit-result").className="result-box win";$("deposit-result").textContent="🎉 +"+r.credited_gems+" gems!";haptic("win");}
  else{$("deposit-result").className="result-box lose";$("deposit-result").textContent=r.message||"Not found yet";haptic("lose");}
}

/* ======================== INVENTORY ======================== */
let invFilter="all";
async function loadInventory(){
  const r=await api("/api/inventory",{user_id:uid});invCache=r.items||[];renderInv();
}
function filterInv(f,btn){invFilter=f;document.querySelectorAll(".f-btn").forEach(b=>b.classList.remove("active"));if(btn)btn.classList.add("active");renderInv();}
function renderInv(){
  const g=$("inventory-list");if(!g)return;
  const ord=["common","uncommon","rare","epic","legendary","mythic","divine"];
  let items=invCache;if(invFilter!=="all"){const mi=ord.indexOf(invFilter);items=items.filter(i=>ord.indexOf(i.rarity)>=mi);}
  g.innerHTML=items.length?items.map(i=>`<div class="inv-item" style="--rc:${RC[i.rarity]||"#333"}" onclick="showItem(${JSON.stringify(i).replace(/"/g,"&quot;")})"><span class="rarity-tag">${i.rarity}</span><span class="item-icon">${i.emoji||"🎁"}</span><h4>${i.name}</h4><p class="item-value">💎 ${(i.value||0).toLocaleString()}</p></div>`).join(""):'<p class="empty">No items yet</p>';
}
function showItem(it){
  $("detail-emoji").textContent=it.emoji||"🎁";$("detail-name").textContent=it.name;
  $("detail-rarity").textContent=it.rarity;$("detail-rarity").style.color=RC[it.rarity]||"#fff";
  $("detail-value").textContent="💎 "+(it.value||0).toLocaleString();
  $("item-modal").classList.remove("hidden");
}
function closeItemModal(){$("item-modal").classList.add("hidden");}

/* ======================== FUSION ======================== */
async function loadBreed(){
  const r=await api("/api/inventory",{user_id:uid});
  const items=(r.items||[]).filter(i=>["common","uncommon","rare","epic"].includes(i.rarity)&&!i.is_locked);
  const g=$("breed-list");
  g.innerHTML=items.length?items.map(i=>`<div class="inv-item" style="--rc:${RC[i.rarity]}" onclick="pickBreed(${i.id},'${(i.emoji||"🎁").replace(/'/g,"")}')"><span class="item-icon">${i.emoji||"🎁"}</span><h4>${i.name}</h4><p class="item-value">💎 ${(i.value||0).toLocaleString()}</p></div>`).join(""):'<p class="empty">Need common-epic items to fuse</p>';
}
function pickBreed(id,emoji){
  if(bPick1&&bPick1.id===id){toast("Already selected");return;}
  if(!bPick1){bPick1={id,emoji};const s=$("bslot1");s.textContent=emoji;s.classList.add("filled");}
  else if(!bPick2){bPick2={id,emoji};const s=$("bslot2");s.textContent=emoji;s.classList.add("filled");}
  else{toast("Slots full");return;}haptic();
}
function clearBreed(n){if(n===1){bPick1=null;const s=$("bslot1");s.textContent="+";s.classList.remove("filled");}
  if(n===2){bPick2=null;const s=$("bslot2");s.textContent="+";s.classList.remove("filled");}}
async function doBreed(){
  if(!bPick1||!bPick2){toast("Select two items");return;}
  const r=await api("/api/breed",{user_id:uid,item1_id:bPick1.id,item2_id:bPick2.id});
  const box=$("breed-result");box.classList.remove("hidden");
  if(r.success&&r.bred){box.className="result-box win";box.textContent="🧬 "+r.item.name+"!";confetti(50);haptic("win");}
  else if(r.success){box.className="result-box lose";box.textContent="Fusion failed...items survived";haptic("lose");}
  else toast(r.message||"Failed");
  clearBreed(1);clearBreed(2);loadBreed();
}

/* ======================== MARKET ======================== */
let marketF="all";
async function loadMarket(){
  try{const r=await fetch("/api/marketplace"+(marketF!=="all"?"?rarity="+marketF:""));const d=await r.json();
  const g=$("market-list");const l=d.listings||[];
  g.innerHTML=l.length?l.map(i=>`<div class="inv-item" style="--rc:${RC[i.item.rarity]||"#333"}" onclick="showItem(${JSON.stringify({emoji:i.item.emoji,name:i.item.name,rarity:i.item.rarity,value:i.price}).replace(/"/g,"&quot;")})"><span class="rarity-tag">${i.item.rarity}</span><span class="item-icon">${i.item.emoji||"🎁"}</span><h4>${i.item.name}</h4><p class="item-value">💎 ${(i.price||0).toLocaleString()}</p></div>`).join(""):'<p class="empty">No listings yet</p>';}catch(e){$("market-list").innerHTML='<p class="empty">Unavailable</p>';}
}
function filterMarket(f,btn){marketF=f;document.querySelectorAll("#market-filters .f-btn").forEach(b=>b.classList.remove("active"));if(btn)btn.classList.add("active");loadMarket();}

/* ======================== TASKS ======================== */
const TASKS=[
  {cat:"daily",name:"Claim Daily Reward",reward:50,type:"daily",action:()=>claimDaily()},
  {cat:"daily",name:"Open 1 Mystery Box",reward:100,type:"box",target:1},
  {cat:"social",name:"Join our channel",reward:200,type:"channel",channel:"@FrogCaseHelp",link:"https://t.me/FrogCaseHelp"},
  {cat:"social",name:"Follow support",reward:100,type:"follow",channel:"@MyCasinoBotx_bot",link:"https://t.me/MyCasinoBotx_bot"},
  {cat:"referral",name:"Invite 1 friend",reward:150,type:"ref",target:1},
  {cat:"referral",name:"Invite 5 friends",reward:750,type:"ref",target:5},
];
function loadTasks(){
  const cats={daily:$("daily-tasks"),social:$("social-tasks"),referral:$("ref-tasks")};
  Object.values(cats).forEach(c=>{if(c)c.innerHTML="";});
  TASKS.forEach(t=>{
    const c=cats[t.cat];if(!c)return;
    c.innerHTML+=`<div class="task-row"><div class="task-info"><b>${t.name}</b><small>💎 ${t.reward} gems</small></div>
      <button class="claim-btn task-btn" onclick="completeTask(${JSON.stringify(t).replace(/"/g,"&quot;")})">GO</button></div>`;
  });
  if($("social-tasks")&&!$("social-tasks").children.length)$("social-tasks").innerHTML='<p class="empty">Tasks coming soon</p>';
  if($("ref-tasks")&&!$("ref-tasks").children.length)$("ref-tasks").innerHTML='<p class="empty">Invite friends to unlock</p>';
}
async function completeTask(t){
  if(t.type==="daily"){claimDaily();return;}
  if(t.link){window.open(t.link,"_blank");toast("Task completed! Return to claim");return;}
  toast("Task registered");
}

/* ======================== REFERRALS ======================== */
async function loadReferrals(){
  const r=await api("/api/stats",{user_id:uid});
  $("ref-total").textContent=r.total_referrals||0;
  const milestones=[1,3,5,10,25,50,100];
  const list=$("milestones");
  list.innerHTML=milestones.map(m=>{
    const earned=(r.total_referrals||0)>=m;
    return `<div class="lb-row"><span class="lb-rank">${earned?"✅":"⬜"}</span>
      <span class="lb-name">${m} referrals</span>
      <span class="lb-val">${earned?"Done!":`💎 ${m*150}`}</span></div>`;
  }).join("");
}
function shareReferral(){
  const link=$("ref-link").textContent;
  if(navigator.share)navigator.share({title:"Join GIFT RUSH!",url:link}).catch(()=>{});
  else navigator.clipboard.writeText(link).then(()=>toast("Link copied!")).catch(()=>toast(link));
}
function copyRefLink(){copyText("ref-link");}

/* ======================== LEADERBOARD ======================== */
async function loadLeaderboard(){
  try{const r=await fetch("/api/leaderboard?category=coins");const d=await r.json();
  const medals=["🥇","🥈","🥉"];
  $("lb-list").innerHTML=(d.leaderboard||[]).map((e,i)=>`<div class="lb-row"><span class="lb-rank">${medals[i]||(i+1)}</span><span class="lb-name">${e.username||"Player"}</span><span class="lb-val">💎 ${(e.value||0).toLocaleString()}</span></div>`).join("")||'<p class="empty">No players yet</p>';}catch(e){$("lb-list").innerHTML='<p class="empty">Unavailable</p>';}
}

/* ======================== WITHDRAW ======================== */
async function loadWithdraw(){
  const r=await api("/api/inventory",{user_id:uid});
  const items=(r.items||[]).filter(i=>!i.is_locked&&(i.value||0)>=500);
  $("withdraw-list").innerHTML=items.length?items.map(i=>`<div class="inv-item" style="--rc:${RC[i.rarity]||"#333"}"><span class="rarity-tag">${i.rarity}</span><span class="item-icon">${i.emoji||"🎁"}</span><h4>${i.name}</h4><p class="item-value">💎 ${(i.value||0).toLocaleString()}</p><button class="gold-btn" style="margin-top:8px;padding:8px 18px;font-size:12px" onclick="requestWd(${i.id})">CASH OUT</button></div>`).join(""):'<p class="empty">No cashable items (💎500+)</p>';
}
async function requestWd(id){
  const r=await api("/api/withdraw",{user_id:uid,item_id:id});
  if(r.success){toast(r.message);loadWithdraw();}else toast(r.message||"Failed");
}

/* ======================== ACHIEVEMENTS ======================== */
async function loadAchievements(){
  const r=await api("/api/achievements",{user_id:uid});
  const a=r.achievements||[];
  $("ach-list").innerHTML=a.length?a.map(i=>`<div class="lb-row"><span class="lb-rank">${i.emoji||"🏅"}</span><span class="lb-name">${i.name}<br><small style="color:var(--dim);font-weight:400">${i.description||""}</small></span></div>`).join(""):'<p class="empty">Keep playing to unlock!</p>';
}

/* ======================== MISC ======================== */
async function refreshBalance(){
  const r=await api("/api/stats",{user_id:uid});
  if(r&&r.coins!==undefined)setGems(r.coins);
  const pi=$("profile-items");if(pi&&r)pi.textContent=r.total_items||0;
  const pc=$("profile-cases");if(pc&&r)pc.textContent=r.cases_opened||0;
  const ps=$("profile-spins");if(ps&&r)ps.textContent=r.wheel_spins||0;
}

/* ======================== DEEP-LINKS ======================== */
function parseStartParam(){
  const sp=(tg?.initDataUnsafe?.start_param)||(new URLSearchParams(location.search).get("startapp")||"");
  if(!sp)return{};const parts=sp.split("_"),out={command:parts[0]||""};
  parts.forEach(p=>{if(p.indexOf("inviteCode")===0)out.inviteCode=p.slice(10);if(p.indexOf("adSegmentCode")===0)out.adSegment=p.slice(13);});
  return out;
}

/* ======================== DATA ======================== */
const BOXES_DATA={
  starter:{name:"Starter Box",price:250,emoji:"🎁",color:"#7c5cff",
    items:[{name:"Sticker Pack",rarity:"common",value:80,emoji:"🩷"},{name:"Mini Plush",rarity:"common",value:160,emoji:"🧸"},{name:"Neon Signet",rarity:"rare",value:450,emoji:"💍"},{name:"Astral Shard",rarity:"epic",value:1400,emoji:"🔮"},{name:"Golden Heart",rarity:"legendary",value:6000,emoji:"💛"}]},
  pro:{name:"Pro Box",price:1200,emoji:"🎀",color:"#38bdf8",
    items:[{name:"Candy Cane",rarity:"common",value:350,emoji:"🍬"},{name:"Snow Globe",rarity:"uncommon",value:700,emoji:"🌐"},{name:"Signet Ring",rarity:"rare",value:2000,emoji:"💎"},{name:"Eternal Rose",rarity:"epic",value:6500,emoji:"🌹"},{name:"Durov Cap",rarity:"legendary",value:30000,emoji:"🧢"}]},
  elite:{name:"Elite Box",price:6000,emoji:"🗃️",color:"#f472b6",
    items:[{name:"Crystal Ball",rarity:"uncommon",value:1800,emoji:"🔮"},{name:"Eternal Rose",rarity:"rare",value:4000,emoji:"🌹"},{name:"Plush Pepe Mini",rarity:"epic",value:12000,emoji:"🐸"},{name:"Swiss Watch",rarity:"legendary",value:45000,emoji:"⌚"},{name:"Plush Pepe (NFT)",rarity:"mythic",value:250000,emoji:"🐸👑"}]},
  legend:{name:"Legend Box",price:25000,emoji:"🏆",color:"#ffd54a",
    items:[{name:"Swiss Watch",rarity:"epic",value:20000,emoji:"⌚"},{name:"Plush Pepe (NFT)",rarity:"legendary",value:90000,emoji:"🐸"},{name:"Durov Cap (NFT)",rarity:"mythic",value:350000,emoji:"🧢"},{name:"Precious Peach",rarity:"divine",value:1000000,emoji:"🍑"}]}
};
