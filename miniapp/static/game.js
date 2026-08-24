/* ============ Casino Bot — Pro Game Engine ============ */

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

let userId = null;
let userCoins = 0;
let currentBet = 50;
let slotsBet = 100;
let spinning = false;
let inventoryCache = [];
let breedPick1 = null, breedPick2 = null;

const $ = (id) => document.getElementById(id);
const RARITY_EMOJI = { common:"🪙", uncommon:"💍", rare:"💎", epic:"🔮", legendary:"👑", mythic:"🌋", divine:"✨" };
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

async function api(endpoint, data = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: controller.signal
    });
    clearTimeout(timer);
    return await response.json();
  } catch (error) {
    clearTimeout(timer);
    console.error("API Error:", error);
    return { error: error.name === "AbortError" ? "Request timed out" : "Network error" };
  }
}

function setCoins(v) {
  userCoins = Number(v) || 0;
  const el = $("coins");
  if (el) el.textContent = userCoins.toLocaleString();
  const pc = $("profile-coins");
  if (pc) pc.textContent = userCoins.toLocaleString();
}

/* ============ INIT ============ */
async function initUser() {
  let userData = null;
  if (tg && tg.initDataUnsafe && tg.initDataUnsafe.user) {
    userData = tg.initDataUnsafe.user;
    userId = userData.id;
  } else {
    userId = 123456789;
    userData = { id: userId, username: "demo_player", first_name: "Demo" };
  }

  const result = await api("/api/user", {
    user_id: userId,
    username: userData.username || "",
    first_name: userData.first_name || ""
  });

  if (result.error || !result.id) {
    $("loading").innerHTML = "<p style='color:#ff7a7a;padding:20px;text-align:center'>API said: " + JSON.stringify(result) + "</p>";
    return;
  }

  setCoins(result.coins);
  $("username").textContent = result.first_name || result.username || "Player";
  $("user-avatar").textContent = (result.first_name || result.username || "P").charAt(0).toUpperCase();
  const lvl = $("user-level"); if (lvl) lvl.textContent = result.level || 1;
  const st = $("streak-days"); if (st) st.textContent = result.daily_streak || 0;
  const rc = $("ref-count"); if (rc) rc.textContent = result.total_referrals || 0;
  $("profile-username").textContent = result.username || "-";
  $("profile-refcode").textContent = result.referral_code || "-";
  const xpFill = $("xp-fill"); if (xpFill) xpFill.style.width = Math.min(((result.xp || 0) / ((result.level || 1) * 100)) * 100, 100) + "%";

  loadCases();
  $("loading").classList.add("hidden");
}
document.addEventListener("DOMContentLoaded", () => initUser().catch(e => {
  console.error(e);
  const l = $("loading");
  if (l) l.innerHTML = "<p style='color:#ff7a7a'>Init failed: " + e.message + "</p>";
}));

/* ============ NAVIGATION ============ */
function showScreen(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  const scr = $(id + "-screen");
  if (scr) scr.classList.add("active");
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.nav === id));
  haptic();
  if (id === "inventory") loadInventory();
  if (id === "menu") refreshBalance();
  if (id === "leaderboard") loadLeaderboard();
  if (id === "achievements") loadAchievements();
  if (id === "market") loadMarket();
  if (id === "breed") loadBreedList();
  window.scrollTo(0, 0);
}

/* ============ CASES ============ */
function loadCases() {
  const grid = $("cases-grid");
  if (!grid) return;
  grid.innerHTML = Object.entries(CASES_DATA).map(([id, c]) => `
    <div class="case-card" style="--glow:${c.color}44" onclick="openCase('${id}')">
      <span class="case-emoji">${c.emoji}</span>
      <h3>${c.name.replace(" Case", "")}</h3>
      <div class="case-price">🪙 ${c.price.toLocaleString()}</div>
    </div>
  `).join("");
}

async function openCase(caseId) {
  if (spinning) return;
  spinning = true;
  haptic();

  const result = await api("/api/case/open", { user_id: userId, case_id: caseId });

  if (!result.success) {
    spinning = false;
    toast(result.message || "Not enough coins");
    return;
  }

  // build random strip with the winner at a known position
  const strip = $("roll-strip");
  strip.style.transition = "none";
  strip.style.transform = "translateX(0)";
  strip.innerHTML = "";
  const allEmojis = [];
  Object.values(CASES_DATA).forEach(c => c.items.forEach(i => allEmojis.push(i)));
  const WINNER_INDEX = 24;
  for (let i = 0; i < 34; i++) {
    const it = i === WINNER_INDEX ? result.item : allEmojis[Math.floor(Math.random() * allEmojis.length)];
    strip.innerHTML += `<div class="roll-item" style="--rc:${RARITY_COLOR[it.rarity] || "#333"}">${it.emoji || "🎁"}</div>`;
  }
  $("case-modal").classList.remove("hidden");
  $("reveal-card").classList.add("hidden");

  requestAnimationFrame(() => {
    const itemW = 114; // width+gap
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
    $("item-value").textContent = "Value: " + (item.value || 0).toLocaleString() + " coins";
    $("reveal-card").classList.remove("hidden");
    setCoins(result.balance);
    haptic(item.value >= 2000 ? "win" : "");
    spinning = false;
  }, 3600);
}

function closeCaseModal() {
  $("case-modal").classList.add("hidden");
}

/* ============ DAILY ============ */
async function claimDaily() {
  const result = await api("/api/daily", { user_id: userId });
  if (result.success) {
    setCoins(result.balance);
    const ds = $("daily-status"); if (ds) { ds.textContent = "DONE ✓"; ds.style.opacity = .5; }
    const sd = $("streak-days"); if (sd) sd.textContent = result.streak || 0;
    toast(`🎁 +${result.coins} coins! Streak ${result.streak}🔥`);
    haptic("win");
  } else {
    toast(`⏰ Next in ${result.next_claim || "soon"}`);
  }
}

/* ============ ROULETTE ============ */
function setBet(amount) {
  currentBet = amount;
  const el = $("current-bet"); if (el) el.textContent = amount.toLocaleString();
  document.querySelectorAll(".bet-chips button").forEach(b => b.classList.toggle("active", Number(b.dataset.bet) === amount));
  haptic();
}

async function spinRoulette(color) {
  if (spinning) return;
  spinning = true;
  const wheel = $("wheel");
  const box = $("roulette-result");
  box.className = "result-box hidden";
  wheel.style.transform = `rotate(${360 * 5 + Math.random() * 360}deg)`;
  haptic();

  const result = await api("/api/roulette/spin", { user_id: userId, bet: currentBet, color });

  setTimeout(() => {
    spinning = false;
    if (!result.success) { toast(result.message || "Not enough coins"); return; }
    setCoins(result.balance);
    box.classList.remove("hidden");
    if (result.won > 0) {
      box.className = "result-box win";
      box.textContent = `🎉 +${result.won.toLocaleString()} coins (${result.result})`;
      haptic("win");
    } else {
      box.className = "result-box lose";
      box.textContent = `😔 ${result.result} — try again!`;
      haptic("lose");
    }
  }, 2700);
}

/* ============ SLOTS ============ */
const SLOT_SYMBOLS = ["🍒","🍋","🍊","🍇","💎","7️⃣","🎰"];

async function spinSlots() {
  if (spinning) return;
  spinning = true;
  $("slots-spin-btn").style.opacity = .5;
  $("slots-result").className = "result-box hidden";
  const reels = [$("slot1"), $("slot2"), $("slot3")];
  reels.forEach(r => r.classList.add("spin"));
  haptic();

  const result = await api("/api/slots/spin", { user_id: userId, bet: slotsBet });

  reels.forEach((r, i) => {
    setTimeout(() => {
      r.classList.remove("spin");
      r.textContent = result.symbols ? result.symbols[i] : SLOT_SYMBOLS[0];
      haptic();
    }, 800 + i * 500);
  });

  setTimeout(() => {
    spinning = false;
    $("slots-spin-btn").style.opacity = 1;
    if (!result.success) { toast(result.message || "Not enough coins"); return; }
    setCoins(result.balance);
    const box = $("slots-result");
    box.classList.remove("hidden");
    if (result.won > 0) {
      box.className = "result-box win";
      box.textContent = `🎉 WON ${result.won.toLocaleString()}! (${result.multiplier}x)`;
      haptic("win");
    } else {
      box.className = "result-box lose";
      box.textContent = "No match — spin again!";
      haptic("lose");
    }
  }, 2400);
}

function setSlotsBet(amount) {
  slotsBet = amount;
  const el = $("slots-current-bet"); if (el) el.textContent = amount.toLocaleString();
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
  if (!items.length) {
    list.innerHTML = '<p class="empty">No items here yet — open some cases!</p>';
    return;
  }
  list.innerHTML = items.map(it => `
    <div class="inv-item" style="--rc:${RARITY_COLOR[it.rarity] || "#333"}">
      <span class="rarity-tag">${it.rarity}</span>
      <span class="item-icon">${it.emoji || "🎁"}</span>
      <h4>${it.name}</h4>
      <p class="item-value">🪙 ${(it.value || 0).toLocaleString()}</p>
    </div>
  `).join("");
}

/* ============ BREEDING ============ */
async function loadBreedList() {
  const result = await api("/api/inventory", { user_id: userId });
  const items = (result.items || []).filter(i => ["common","uncommon","rare","epic"].includes(i.rarity));
  const list = $("breed-list");
  list.innerHTML = items.length ? items.map(it => `
    <div class="inv-item" style="--rc:${RARITY_COLOR[it.rarity]}" onclick="pickBreedItem(${it.id},'${it.emoji}')">
      <span class="item-icon">${it.emoji || "🎁"}</span>
      <h4>${it.name}</h4>
      <p class="item-value">🪙 ${(it.value || 0).toLocaleString()}</p>
    </div>
  `).join("") : '<p class="empty">Need common-to-epic items to breed</p>';
}

function pickBreedItem(slotOrId, emoji) {
  // called two ways: from slot click (1/2) or from item click (id, emoji)
  if (slotOrId === 1 || slotOrId === 2) return;
  const id = slotOrId;
  if (breedPick1 && breedPick1.id === id) { toast("Already selected"); return; }
  if (!breedPick1) {
    breedPick1 = { id, emoji };
    const s = $("bslot1"); s.textContent = emoji; s.classList.add("filled");
  } else if (!breedPick2) {
    breedPick2 = { id, emoji };
    const s = $("bslot2"); s.textContent = emoji; s.classList.add("filled");
  } else {
    toast("Reset selection first");
  }
  haptic();
}

async function doBreed() {
  if (!breedPick1 || !breedPick2) { toast("Select two items first"); return; }
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
    toast(result.message || "Breeding failed");
  }
  breedPick1 = breedPick2 = null;
  $("bslot1").textContent = "+"; $("bslot2").textContent = "+";
  $("bslot1").classList.remove("filled"); $("bslot2").classList.remove("filled");
  loadBreedList();
}

/* ============ MARKET ============ */
async function loadMarket() {
  try {
    const r = await fetch("/api/marketplace");
    const data = await r.json();
    const list = $("market-list");
    if (data.listings && data.listings.length) {
      list.innerHTML = data.listings.map(l => `
        <div class="inv-item" style="--rc:${RARITY_COLOR[l.item.rarity]}">
          <span class="rarity-tag">${l.item.rarity}</span>
          <span class="item-icon">${l.item.emoji || "🎁"}</span>
          <h4>${l.item.name}</h4>
          <p class="item-value">🪙 ${(l.price || 0).toLocaleString()}</p>
          <button class="gold-btn" style="margin-top:10px;padding:9px 20px;font-size:12px" onclick="buyListing(${l.id})">BUY</button>
        </div>
      `).join("");
    } else {
      list.innerHTML = '<p class="empty">No listings yet. List your items from inventory!</p>';
    }
  } catch (e) {
    $("market-list").innerHTML = '<p class="empty">Market unavailable</p>';
  }
}

async function buyListing(id) {
  const result = await api("/api/marketplace/buy", { user_id: userId, listing_id: id });
  if (result.success) {
    setCoins(result.balance);
    toast("✅ Purchased!");
    loadMarket();
  } else {
    toast(result.message || "Purchase failed");
  }
}

/* ============ LEADERBOARD ============ */
async function loadLeaderboard() {
  try {
    const r = await fetch("/api/leaderboard?category=coins");
    const data = await r.json();
    const medals = ["🥇","🥈","🥉"];
    $("lb-list").innerHTML = (data.leaderboard || []).map((e, i) => `
      <div class="lb-row">
        <span class="lb-rank">${medals[i] || (i+1)}</span>
        <span class="lb-name">${e.username || e.first_name || "Player"}</span>
        <span class="lb-val">🪙 ${(e.value || 0).toLocaleString()}</span>
      </div>
    `).join("") || '<p class="empty">No players yet</p>';
  } catch (e) {
    $("lb-list").innerHTML = '<p class="empty">Unavailable</p>';
  }
}

/* ============ ACHIEVEMENTS ============ */
async function loadAchievements() {
  const result = await api("/api/achievements", { user_id: userId });
  const list = $("ach-list");
  const achs = result.achievements || [];
  list.innerHTML = achs.length ? achs.map(a => `
    <div class="lb-row">
      <span class="lb-rank">${a.emoji || "🏅"}</span>
      <span class="lb-name">${a.name}<br><small style="color:var(--dim);font-weight:400">${a.description || ""}</small></span>
    </div>
  `).join("") : '<p class="empty">No achievements yet — keep playing!</p>';
}

/* ============ MISC ============ */
async function refreshBalance() {
  const result = await api("/api/stats", { user_id: userId });
  if (result && result.coins !== undefined) setCoins(result.coins);
  const pi = $("profile-items"); if (pi && result) pi.textContent = result.total_items || 0;
  const pc = $("profile-cases"); if (pc && result) pc.textContent = result.cases_opened || 0;
}

function shareReferral() {
  const code = $("profile-refcode").textContent;
  const link = `https://t.me/MyCasinoBotx_bot?start=ref_${code}`;
  if (navigator.share) navigator.share({ title: "Join Casino Bot!", url: link }).catch(() => {});
  else navigator.clipboard.writeText(link).then(() => toast("Link copied!")).catch(() => toast(link));
}

/* case data injected by server-side config; fallback mirror */
const CASES_DATA = window.CASES_DATA || {
  bronze:  { name:"Bronze Case",  price:100,   emoji:"📦", color:"#CD7F32", items:[
    {name:"Bronze Coin",rarity:"common",value:15,emoji:"🪙"},{name:"Copper Ring",rarity:"common",value:30,emoji:"💍"},
    {name:"Iron Dagger",rarity:"uncommon",value:75,emoji:"🗡️"},{name:"Silver Pendant",rarity:"rare",value:200,emoji:"📿"},
    {name:"Golden Token",rarity:"epic",value:500,emoji:"🏅"}]},
  silver:  { name:"Silver Case",  price:500,   emoji:"🎁", color:"#C0C0C0", items:[
    {name:"Silver Bar",rarity:"common",value:60,emoji:"🪙"},{name:"Crystal Shard",rarity:"uncommon",value:150,emoji:"💠"},
    {name:"Ruby Gem",rarity:"rare",value:500,emoji:"💎"},{name:"Emerald Crown",rarity:"epic",value:1500,emoji:"👑"},
    {name:"Dragon Scale",rarity:"legendary",value:5000,emoji:"🐉"}]},
  gold:    { name:"Gold Case",    price:2000,  emoji:"🏆", color:"#FFD700", items:[
    {name:"Gold Ingot",rarity:"uncommon",value:250,emoji:"🪙"},{name:"Sapphire Ring",rarity:"rare",value:800,emoji:"💍"},
    {name:"Phoenix Feather",rarity:"epic",value:3000,emoji:"🔥"},{name:"Unicorn Horn",rarity:"legendary",value:10000,emoji:"🦄"},
    {name:"Cosmic Artifact",rarity:"mythic",value:50000,emoji:"🌌"}]},
  diamond: { name:"Diamond Case", price:10000, emoji:"💎", color:"#B9F2FF", items:[
    {name:"Diamond Shard",rarity:"rare",value:1000,emoji:"💎"},{name:"Obsidian Blade",rarity:"epic",value:4000,emoji:"⚔️"},
    {name:"Leviathan Eye",rarity:"legendary",value:15000,emoji:"👁️"},{name:"Void Walker",rarity:"mythic",value:75000,emoji:"🌀"},
    {name:"Eternal Core",rarity:"divine",value:200000,emoji:"✨"}]}
};
