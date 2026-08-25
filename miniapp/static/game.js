/* ============ GIFT RUSH — Game Engine ============ */

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

let userId = null;
let userGems = 0;
let inventoryCache = [];
let breedPick1 = null, breedPick2 = null;

const $ = (id) => document.getElementById(id);
const RARITY_COLOR = { common:"#8b93b5", uncommon:"#44dd77", rare:"#4488ff", epic:"#aa44ff", legendary:"#ffaa00", mythic:"#ff4444", divine:"#ffd700" };

function haptic(type) {
  try {
    if (!tg?.HapticFeedback) return;
    if (type === "win") tg.HapticFeedback.notificationOccurred("success");
    else if (type === "lose") tg.HapticFeedback.notificationOccurred("error");
    else tg.HapticFeedback.impactOccurred("light");
  } catch (e) {}
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}

function setGems(v) {
  userGems = Number(v) || 0;
  const c = $("coins"); if (c) c.textContent = userGems.toLocaleString();
  const p = $("profile-coins"); if (p) p.textContent = userGems.toLocaleString();
}

async function api(endpoint, data = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const r = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: controller.signal
    });
    clearTimeout(timer);
    return await r.json();
  } catch (e) {
    clearTimeout(timer);
    return { error: e.name === "AbortError" ? "Timed out" : "Network error" };
  }
}

/* ============ INIT ============ */
async function initUser() {
  let ud = null;
  if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
    ud = tg.initDataUnsafe.user;
    userId = ud.id;
  } else {
    userId = 123456789;
    ud = { id: userId, username: "demo_player", first_name: "Demo" };
  }

  const result = await api("/api/user", { user_id: userId, username: ud.username || "", first_name: ud.first_name || "", referral_code: window.__refCode || "" });

  if (result.error || !result.id) {
    $("loading").innerHTML = "<p style='color:#ff7a7a;padding:20px;text-align:center'>API: " + JSON.stringify(result) + "</p>";
    return;
  }

  setGems(result.coins);
  $("username").textContent = result.first_name || result.username || "Player";
  $("user-avatar").textContent = (result.first_name || result.username || "P").charAt(0).toUpperCase();
  const lvl = $("user-level"); if (lvl) lvl.textContent = result.level || 1;
  const st = $("streak-days"); if (st) st.textContent = result.daily_streak || 0;
  const rc = $("ref-count"); if (rc) rc.textContent = result.total_referrals || 0;
  const bc = $("box-count"); if (bc) bc.textContent = result.cases_opened || 0;
  $("profile-username").textContent = result.username || "-";
  $("profile-refcode").textContent = result.referral_code || "-";
  const xf = $("xp-fill");
  if (xf) xf.style.width = Math.min(((result.xp || 0) / ((result.level || 1) * 100)) * 100, 100) + "%";

  loadBoxes();
  $("loading").classList.add("hidden");
}
document.addEventListener("DOMContentLoaded", () => initUser().catch(e => {
  console.error(e);
  const l = $("loading");
  if (l) l.innerHTML = "<p style='color:#ff7a7a'>Init failed: " + e.message + "</p>";
}));

/* ============ NAV ============ */
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  const scr = $(id + "-screen");
  if (scr) scr.classList.add("active");
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.nav === id));
  haptic();
  window.scrollTo(0, 0);

  if (id === "inventory") loadInventory();
  if (id === "deposit") loadDepositInfo();
  if (id === "withdraw") loadWithdrawList();
  if (id === "breed") loadBreedList();
  if (id === "market") loadMarket();
  if (id === "leaderboard") loadLeaderboard();
  if (id === "achievements") loadAchievements();
  if (id === "menu") refreshBalance();
}

/* ============ BOXES ============ */
function loadBoxes() {
  const grid = $("cases-grid");
  if (!grid || typeof CASES_DATA === "undefined") return;
  grid.innerHTML = Object.entries(CASES_DATA).map(([id, b]) => `
    <div class="case-card" style="--glow:${b.color}44" onclick="openBox('${id}')">
      <span class="case-emoji">${b.emoji}</span>
      <h3>${b.name.replace(" Box", "")}</h3>
      <div class="case-price">💎 ${Number(b.price).toLocaleString()}</div>
    </div>
  `).join("");
}

async function openBox(boxId) {
  if (spinning) return;
  spinning = true;
  haptic();

  const result = await api("/api/case/open", { user_id: userId, case_id: boxId });

  if (!result.success) {
    spinning = false;
    toast(result.message || "Not enough gems");
    return;
  }

  const strip = $("roll-strip");
  strip.style.transition = "none";
  strip.style.transform = "translateX(0)";
  strip.innerHTML = "";

  const pool = [];
  Object.values(CASES_DATA).forEach(b => b.items.forEach(i => pool.push(i)));
  const WINNER_INDEX = 24;

  for (let i = 0; i < 34; i++) {
    const it = i === WINNER_INDEX ? result.item : pool[Math.floor(Math.random() * pool.length)];
    strip.innerHTML += `<div class="roll-item" style="--rc:${RARITY_COLOR[it.rarity] || "#333"}">${it.emoji || "🎁"}</div>`;
  }

  $("case-modal").classList.remove("hidden");
  $("reveal-card").classList.add("hidden");

  requestAnimationFrame(() => {
    const itemW = 114;
    const target = -(WINNER_INDEX * itemW) + 158 + Math.random() * 40;
    strip.style.transition = "transform 3.4s cubic-bezier(.12,.75,.18,1)";
    strip.style.transform = `translateX(${target}px)`;
  });

  setTimeout(() => {
    const item = result.item;
    $("revealed-item").textContent = item.emoji || "🎁";
    $("item-name").textContent = item.name;
    $("item-rarity").textContent = item.rarity;
    $("item-rarity").style.color = RARITY_COLOR[item.rarity] || "#fff";
    $("item-value").textContent = "💎 " + (item.value || 0).toLocaleString() + " value";
    $("reveal-card").classList.remove("hidden");
    setGems(result.balance);
    const bc = $("box-count"); if (bc) bc.textContent = (parseInt(bc.textContent || "0") + 1);
    haptic((item.value || 0) >= 5000 ? "win" : "");
    spinning = false;
  }, 3600);
}

function closeCaseModal() { $("case-modal").classList.add("hidden"); }

/* ============ DAILY ============ */
async function claimDaily() {
  const result = await api("/api/daily", { user_id: userId });
  if (result.success) {
    setGems(result.balance);
    const ds = $("daily-status"); if (ds) { ds.textContent = "DONE ✓"; ds.style.opacity = .5; }
    toast(`🎁 +${result.coins} gems! Streak ${result.streak}🔥`);
    haptic("win");
  } else {
    toast(`⏰ Next drop in ${result.next_claim || "soon"}`);
  }
}

/* ============ DEPOSIT ============ */
async function loadDepositInfo() {
  try {
    const r = await fetch("/api/deposit/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    const info = await r.json();
    $("dep-address").textContent = info.address || "Not configured";
    $("dep-memo").textContent = info.memo || "-";
    $("dep-rate").textContent = info.gems_per_ton || 1000;
    $("dep-min").textContent = info.min_ton || 0.1;
  } catch (e) {
    toast("Could not load deposit info");
  }
}

function copyText(elId) {
  const text = $(elId).textContent;
  navigator.clipboard.writeText(text)
    .then(() => { toast("📋 Copied!"); haptic(); })
    .catch(() => toast("Copy failed — long-press to copy"));
}

async function checkDeposit() {
  const btn = $("dep-check-btn");
  btn.style.opacity = .5;
  btn.textContent = "Scanning blockchain...";

  const result = await api("/api/deposit/check", { user_id: userId });

  btn.style.opacity = 1;
  btn.textContent = "🔄 I SENT IT — CHECK";

  const box = $("deposit-result");
  box.classList.remove("hidden");

  if (result.success) {
    setGems(result.balance);
    box.className = "result-box win";
    box.textContent = `🎉 +${result.credited_gems.toLocaleString()} gems (${result.credited_ton} TON)`;
    haptic("win");
  } else {
    box.className = "result-box lose";
    box.textContent = result.message || "Nothing found yet";
    haptic("lose");
  }
}

/* ============ WITHDRAW ============ */
async function loadWithdrawList() {
  await loadInventoryForWithdraw();
}

async function loadInventoryForWithdraw() {
  const result = await api("/api/inventory", { user_id: userId });
  const items = result.items || [];
  const list = $("withdraw-list");

  const eligible = items.filter(i => !i.is_locked && (i.value || 0) >= 500);

  list.innerHTML = eligible.length ? eligible.map(it => `
    <div class="inv-item" style="--rc:${RARITY_COLOR[it.rarity] || "#333"}">
      <span class="rarity-tag">${it.rarity}</span>
      <span class="item-icon">${it.emoji || "🎁"}</span>
      <h4>${it.name}</h4>
      <p class="item-value">💎 ${(it.value || 0).toLocaleString()}</p>
      <button class="gold-btn" style="margin-top:10px;padding:9px 18px;font-size:12px" onclick="requestWd(${it.id})">CASH OUT</button>
    </div>
  `).join("") : '<p class="empty">Items worth 💎500+ can be cashed out</p>';
}

async function requestWd(itemId) {
  const result = await api("/api/withdraw", { user_id: userId, item_id: itemId });
  if (result.success) {
    toast(`✅ ${result.message}`);
    haptic("win");
    loadWithdrawList();
  } else {
    toast(result.message || "Failed");
  }
}

/* ============ INVENTORY ============ */
let invFilter = "all";

async function loadInventory() {
  const result = await api("/api/inventory", { user_id: userId });
  inventoryCache = result.items || [];
  renderInventory();
}

function filterInv(f, btn) {
  invFilter = f;
  document.querySelectorAll(".f-btn").forEach(b => b.classList.remove("active"));
  if (btn) btn.classList.add("active");
  renderInventory();
}

function renderInventory() {
  const list = $("inventory-list");
  if (!list) return;
  const order = ["common","uncommon","rare","epic","legendary","mythic","divine"];
  let items = inventoryCache;
  if (invFilter !== "all") {
    const min = order.indexOf(invFilter);
    items = items.filter(it => order.indexOf(it.rarity) >= min);
  }
  list.innerHTML = items.length ? items.map(it => `
    <div class="inv-item" style="--rc:${RARITY_COLOR[it.rarity] || "#333"}">
      <span class="rarity-tag">${it.rarity}</span>
      <span class="item-icon">${it.emoji || "🎁"}</span>
      <h4>${it.name}</h4>
      <p class="item-value">💎 ${(it.value || 0).toLocaleString()}</p>
    </div>
  `).join("") : '<p class="empty">Vault empty — open some boxes!</p>';
}

/* ============ BREEDING ============ */
async function loadBreedList() {
  const result = await api("/api/inventory", { user_id: userId });
  const items = (result.items || []).filter(i =>
    ["common","uncommon","rare","epic"].includes(i.rarity) && !i.is_locked
  );
  const list = $("breed-list");
  list.innerHTML = items.length ? items.map(it => `
    <div class="inv-item" style="--rc:${RARITY_COLOR[it.rarity]}" onclick="pickBreed(${it.id},'${(it.emoji || "🎁").replace(/'/g, "")}')">
      <span class="item-icon">${it.emoji || "🎁"}</span>
      <h4>${it.name}</h4>
      <p class="item-value">💎 ${(it.value || 0).toLocaleString()}</p>
    </div>
  `).join("") : '<p class="empty">Need common→epic items to fuse</p>';
}

function pickBreed(id, emoji) {
  if (breedPick1 && breedPick1.id === id) { toast("Already selected"); return; }
  if (!breedPick1) {
    breedPick1 = { id, emoji };
    const s = $("bslot1"); s.textContent = emoji; s.classList.add("filled");
  } else if (!breedPick2) {
    breedPick2 = { id, emoji };
    const s = $("bslot2"); s.textContent = emoji; s.classList.add("filled");
  } else {
    toast("Slots full — remove one first");
    return;
  }
  haptic();
}

function clearBreed(slot) {
  if (slot === 1) { breedPick1 = null; const s = $("bslot1"); s.textContent = "+"; s.classList.remove("filled"); }
  if (slot === 2) { breedPick2 = null; const s = $("bslot2"); s.textContent = "+"; s.classList.remove("filled"); }
}

async function doBreed() {
  if (!breedPick1 || !breedPick2) { toast("Select two items"); return; }
  const result = await api("/api/breed", { user_id: userId, item1_id: breedPick1.id, item2_id: breedPick2.id });
  const box = $("breed-result");
  box.classList.remove("hidden");
  if (result.success && result.bred) {
    box.className = "result-box win";
    box.textContent = `🧬 Created ${result.item.name}!`;
    haptic("win");
  } else if (result.success) {
    box.className = "result-box lose";
    box.textContent = "Fusion failed... items survived.";
    haptic("lose");
  } else {
    toast(result.message || "Fusion failed");
  }
  clearBreed(1); clearBreed(2);
  loadBreedList();
}

/* ============ MARKET ============ */
async function loadMarket() {
  try {
    const r = await fetch("/api/marketplace");
    const data = await r.json();
    const list = $("market-list");
    const listings = data.listings || [];
    list.innerHTML = listings.length ? listings.map(l => `
      <div class="inv-item" style="--rc:${RARITY_COLOR[l.item.rarity] || "#333"}">
        <span class="rarity-tag">${l.item.rarity}</span>
        <span class="item-icon">${l.item.emoji || "🎁"}</span>
        <h4>${l.item.name}</h4>
        <p class="item-value">💎 ${(l.price || 0).toLocaleString()}</p>
        <button class="gold-btn" style="margin-top:10px;padding:9px 18px;font-size:12px" onclick="buyListing(${l.id})">BUY</button>
      </div>
    `).join("") : '<p class="empty">No listings yet</p>';
  } catch (e) {
    $("market-list").innerHTML = '<p class="empty">Market unavailable</p>';
  }
}

async function buyListing(id) {
  const result = await api("/api/marketplace/buy", { user_id: userId, listing_id: id });
  if (result.success) { setGems(result.balance); toast("✅ Purchased!"); loadMarket(); }
  else toast(result.message || "Purchase failed");
}

/* ============ LEADERBOARD / ACHIEVEMENTS / MISC ============ */
async function loadLeaderboard() {
  try {
    const r = await fetch("/api/leaderboard?category=coins");
    const data = await r.json();
    const medals = ["🥇","🥈","🥉"];
    $("lb-list").innerHTML = (data.leaderboard || []).map((e, i) => `
      <div class="lb-row">
        <span class="lb-rank">${medals[i] || (i+1)}</span>
        <span class="lb-name">${e.username || e.first_name || "Player"}</span>
        <span class="lb-val">💎 ${(e.value || 0).toLocaleString()}</span>
      </div>
    `).join("") || '<p class="empty">No collectors yet</p>';
  } catch (e) {
    $("lb-list").innerHTML = '<p class="empty">Unavailable</p>';
  }
}

async function loadAchievements() {
  const result = await api("/api/achievements", { user_id: userId });
  const achs = result.achievements || [];
  $("ach-list").innerHTML = achs.length ? achs.map(a => `
    <div class="lb-row">
      <span class="lb-rank">${a.emoji || "🏅"}</span>
      <span class="lb-name">${a.name}<br><small style="color:var(--dim);font-weight:400">${a.description || ""}</small></span>
    </div>
  `).join("") : '<p class="empty">None unlocked yet — keep collecting!</p>';
}

async function refreshBalance() {
  const result = await api("/api/stats", { user_id: userId });
  if (result && result.coins !== undefined) setGems(result.coins);
  const pi = $("profile-items"); if (pi && result) pi.textContent = result.total_items || 0;
  const pc = $("profile-cases"); if (pc && result) pc.textContent = result.cases_opened || 0;
}

function shareReferral() {
  const code = $("profile-refcode").textContent;
  const link = `https://t.me/MyCasinoBotx_bot?start=ref_${code}`;
  if (navigator.share) navigator.share({ title: "Join GIFT RUSH!", url: link }).catch(() => {});
  else navigator.clipboard.writeText(link).then(() => toast("Link copied!")).catch(() => toast(link));
}

/* mirror of server box config for the roll animation */
const CASES_DATA = {
  bronze:  { name:"Starter Box", price:250,   emoji:"🎁", color:"#7c5cff", items:[
    {name:"Sticker Pack",rarity:"common",value:80,emoji:"🩷"},{name:"Mini Plush",rarity:"common",value:160,emoji:"🧸"},
    {name:"Neon Signet",rarity:"rare",value:450,emoji:"💍"},{name:"Astral Shard",rarity:"epic",value:1400,emoji:"🔮"},
    {name:"Golden Heart",rarity:"legendary",value:6000,emoji:"💛"}]},
  silver:  { name:"Pro Box", price:1200,  emoji:"🎀", color:"#38bdf8", items:[
    {name:"Candy Cane",rarity:"common",value:350,emoji:"🍬"},{name:"Snow Globe",rarity:"uncommon",value:700,emoji:"🌐"},
    {name:"Signet Ring",rarity:"rare",value:2000,emoji:"💎"},{name:"Eternal Rose",rarity:"epic",value:6500,emoji:"🌹"},
    {name:"Durov Cap",rarity:"legendary",value:30000,emoji:"🧢"}]},
  gold:    { name:"Elite Box", price:6000,  emoji:"🗃️", color:"#f472b6", items:[
    {name:"Crystal Ball",rarity:"uncommon",value:1800,emoji:"🔮"},{name:"Eternal Rose",rarity:"rare",value:4000,emoji:"🌹"},
    {name:"Plush Pepe Mini",rarity:"epic",value:12000,emoji:"🐸"},{name:"Swiss Watch",rarity:"legendary",value:45000,emoji:"⌚"},
    {name:"Plush Pepe (NFT)",rarity:"mythic",value:250000,emoji:"🐸👑"}]},
  diamond: { name:"Legend Box", price:25000, emoji:"🏆", color:"#ffd54a", items:[
    {name:"Swiss Watch",rarity:"epic",value:20000,emoji:"⌚"},{name:"Plush Pepe (NFT)",rarity:"legendary",value:90000,emoji:"🐸"},
    {name:"Durov Cap (NFT)",rarity:"mythic",value:350000,emoji:"🧢"},{name:"Precious Peach",rarity:"divine",value:1000000,emoji:"🍑"}]}
};

/* ============ GIFT WHEEL ============ */
let wheelSpinning = false;
let WHEEL_SEGS = [];

async function initWheel() {
  try {
    const r = await fetch("/api/wheel/config");
    const data = await r.json();
    WHEEL_SEGS = data.segments || [];
    renderWheel();
    updateWheelStatus();
  } catch (e) { console.error(e); }
}

function renderWheel() {
  const wheel = $("big-wheel");
  if (!wheel || !WHEEL_SEGS.length) return;
  const n = WHEEL_SEGS.length;
  const step = 360 / n;
  const stops = [];
  WHEEL_SEGS.forEach((sg, i) => {
    stops.push(sg.color + ' ' + (i * step) + 'deg ' + ((i + 1) * step) + 'deg');
  });
  wheel.style.background = 'conic-gradient(' + stops.join(', ') + ')';
  WHEEL_SEGS.forEach((sg, i) => {
    const mid = i * step + step / 2;
    const el = document.createElement('div');
    el.className = 'seg-label';
    el.style.transform = 'rotate(' + (mid - 90) + 'deg) translate(72px) rotate(90deg)';
    el.textContent = sg.emoji + ' ' + sg.label;
    if (sg.type === 'gift') el.style.color = '#ffd54a';
    wheel.appendChild(el);
  });
}

async function updateWheelStatus() {
  const result = await api("/api/wheel/status", { user_id: userId });
  const st = $("wheel-status");
  if (!st) return;
  if (result.error) { st.textContent = ''; return; }
  let msg = '';
  if (result.free_available) msg = '/u{1F195} FREE SPIN AVAILABLE!';
  else if ((result.bonus_spins || 0) > 0) msg = '/u{1F39F} ' + result.bonus_spins + ' bonus spins left';
  else msg = 'Cost: /u{1F48E}' + result.gem_cost + ' per spin';
  st.textContent = msg;
}

async function spinWheel() {
  if (wheelSpinning || !WHEEL_SEGS.length) return;
  wheelSpinning = true;
  const btn = $("wheel-spin-btn");
  btn.classList.add('spinning');
  btn.textContent = "/u2026";
  $("wheel-result").className = "result-box hidden";
  haptic();
  const result = await api("/api/wheel/spin", { user_id: userId });
  if (!result.success) {
    wheelSpinning = false;
    btn.classList.remove('spinning');
    btn.textContent = "SPIN";
    let m = result.message || 'Spin failed';
    if (result.debug) m += ' | ' + String(result.debug).slice(-140);
    toast(m);
    return;
  }
  const n = result.total_segments;
  const step = 360 / n;
  const segMid = result.segment * step + step / 2;
  const wheel = $("big-wheel");
  wheel.style.transform = 'rotate(' + (360 * 6 - segMid) + 'deg)';
  setTimeout(() => {
    wheelSpinning = false;
    btn.classList.remove('spinning');
    btn.textContent = "SPIN";
    setGems(result.balance);
    updateWheelStatus();
    const box = $("wheel-result");
    box.classList.remove("hidden");
    const p = result.prize;
    if (p.type === 'gift') {
      box.className = 'result-box win';
      box.innerHTML = p.emoji + ' <b>' + p.item_name + '</b> won!<br><small>Added to your vault</small>';
      confetti(90);
      haptic('win');
    } else if (p.type === 'gems') {
      box.className = 'result-box win';
      box.textContent = '/u{1F48E} +' + p.value + ' gems!';
      if (p.value >= 300) confetti(60);
      haptic('win');
    } else {
      box.className = 'result-box lose';
      box.textContent = '/u{1F4A8} So close! Spin again';
      haptic('lose');
    }
  }, 4500);
}

/* ============ DEEP-LINK PARSER ============ */
function parseStartParam() {
  const sp = (tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param)
    ? tg.initDataUnsafe.start_param
    : (new URLSearchParams(location.search).get("startapp") || "");
  if (!sp) return {};
  const parts = sp.split('_');
  const out = { command: parts[0] || '' };
  parts.forEach(p => {
    if (p.indexOf('inviteCode') === 0) out.inviteCode = p.slice(10);
    if (p.indexOf('adSegmentCode') === 0) out.adSegment = p.slice(13);
  });
  return out;
}

const __origInit = initUser;
initUser = async function () {
  const sp = parseStartParam();
  if (sp.inviteCode) window.__refCode = sp.inviteCode;
  await __origInit();
  initWheel();
  if (sp.command === 'openWheelMain' || location.hash === '#wheel') showScreen('wheel');
};



/* ============ CONFETTI ============ */
function confetti(count) {
  count = count || 50;
  const colors = ['#ffd54a', '#7c5cff', '#39d353', '#ff5252', '#38bdf8'];
  for (let i = 0; i < count; i++) {
    const d = document.createElement('div');
    d.className = 'confetti';
    d.style.left = (35 + Math.random() * 30) + '%';
    d.style.background = colors[i % colors.length];
    d.style.animationDelay = (Math.random() * 0.4) + 's';
    d.style.transform = 'rotate(' + (Math.random() * 360) + 'deg)';
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 2800);
  }
}
