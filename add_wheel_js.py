#!/usr/bin/env python3
"""Appends wheel logic + deep-links to game.js (clean v2)."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "static" / "game.js"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")
changed = []

# ---------- 1) initUser passes referral code ----------
OLD_CALL = (
    '    const result = await api("/api/user", {' + NL +
    "      user_id: userId," + NL +
    '      username: ud.username || "",' + NL +
    '      first_name: ud.first_name || ""' + NL +
    "    });"
)
NEW_CALL = (
    '    const result = await api("/api/user", {' + NL +
    "      user_id: userId," + NL +
    '      username: ud.username || "",' + NL +
    '      first_name: ud.first_name || "",' + NL +
    "      referral_code: window.__refCode || ''" + NL +
    "    });"
)
if NEW_CALL in s:
    print("[skip] referral hook present")
elif OLD_CALL in s:
    s = s.replace(OLD_CALL, NEW_CALL, 1)
    changed.append("referral hook")
else:
    print("[warn] initUser api-call anchor drifted")

# ---------- 2) wheel logic ----------
if "GIFT WHEEL ====" in s:
    print("[skip] wheel js exists")
else:
    WHEEL = NL.join([
        "",
        "/* ============ GIFT WHEEL ============ */",
        "let wheelSpinning = false;",
        "let WHEEL_SEGS = [];",
        "",
        "async function initWheel() {",
        "  try {",
        '    const r = await fetch("/api/wheel/config");',
        "    const data = await r.json();",
        "    WHEEL_SEGS = data.segments || [];",
        "    renderWheel();",
        "    updateWheelStatus();",
        "  } catch (e) { console.error(e); }",
        "}",
        "",
        "function renderWheel() {",
        '  const wheel = $("big-wheel");',
        "  if (!wheel || !WHEEL_SEGS.length) return;",
        "  const n = WHEEL_SEGS.length;",
        "  const step = 360 / n;",
        "  const stops = [];",
        "  WHEEL_SEGS.forEach((sg, i) => {",
        "    stops.push(sg.color + ' ' + (i * step) + 'deg ' + ((i + 1) * step) + 'deg');",
        "  });",
        "  wheel.style.background = 'conic-gradient(' + stops.join(', ') + ')';",
        "  WHEEL_SEGS.forEach((sg, i) => {",
        "    const mid = i * step + step / 2;",
        "    const el = document.createElement('div');",
        "    el.className = 'seg-label';",
        "    el.style.transform = 'rotate(' + (mid - 90) + 'deg) translate(72px) rotate(90deg)';",
        "    el.textContent = sg.emoji + ' ' + sg.label;",
        "    if (sg.type === 'gift') el.style.color = '#ffd54a';",
        "    wheel.appendChild(el);",
        "  });",
        "}",
        "",
        "async function updateWheelStatus() {",
        '  const result = await api("/api/wheel/status", { user_id: userId });',
        '  const st = $("wheel-status");',
        "  if (!st) return;",
        "  if (result.error) { st.textContent = ''; return; }",
        "  let msg = '';",
        "  if (result.free_available) msg = '/u{1F195} FREE SPIN AVAILABLE!';",
        "  else if ((result.bonus_spins || 0) > 0) msg = '/u{1F39F} ' + result.bonus_spins + ' bonus spins left';",
        "  else msg = 'Cost: /u{1F48E}' + result.gem_cost + ' per spin';",
        "  st.textContent = msg;",
        "}",
        "",
        "async function spinWheel() {",
        "  if (wheelSpinning || !WHEEL_SEGS.length) return;",
        "  wheelSpinning = true;",
        '  const btn = $("wheel-spin-btn");',
        "  btn.classList.add('spinning');",
        '  btn.textContent = "/u2026";',
        '  $("wheel-result").className = "result-box hidden";',
        "  haptic();",
        '  const result = await api("/api/wheel/spin", { user_id: userId });',
        "  if (!result.success) {",
        "    wheelSpinning = false;",
        "    btn.classList.remove('spinning');",
        '    btn.textContent = "SPIN";',
        "    let m = result.message || 'Spin failed';",
        "    if (result.debug) m += ' | ' + String(result.debug).slice(-140);",
        "    toast(m);",
        "    return;",
        "  }",
        "  const n = result.total_segments;",
        "  const step = 360 / n;",
        "  const segMid = result.segment * step + step / 2;",
        '  const wheel = $("big-wheel");',
        "  wheel.style.transform = 'rotate(' + (360 * 6 - segMid) + 'deg)';",
        "  setTimeout(() => {",
        "    wheelSpinning = false;",
        "    btn.classList.remove('spinning');",
        '    btn.textContent = "SPIN";',
        "    setGems(result.balance);",
        "    updateWheelStatus();",
        '    const box = $("wheel-result");',
        '    box.classList.remove("hidden");',
        "    const p = result.prize;",
        "    if (p.type === 'gift') {",
        "      box.className = 'result-box win';",
        "      box.innerHTML = p.emoji + ' <b>' + p.item_name + '</b> won!<br><small>Added to your vault</small>';",
        "      haptic('win');",
        "    } else if (p.type === 'gems') {",
        "      box.className = 'result-box win';",
        "      box.textContent = '/u{1F48E} +' + p.value + ' gems!';",
        "      haptic('win');",
        "    } else {",
        "      box.className = 'result-box lose';",
        "      box.textContent = '/u{1F4A8} So close! Spin again';",
        "      haptic('lose');",
        "    }",
        "  }, 4500);",
        "}",
        "",
        "/* ============ DEEP-LINK PARSER ============ */",
        "function parseStartParam() {",
        "  const sp = (tg && tg.initDataUnsafe && tg.initDataUnsafe.start_param)",
        "    ? tg.initDataUnsafe.start_param",
        '    : (new URLSearchParams(location.search).get("startapp") || "");',
        "  if (!sp) return {};",
        "  const parts = sp.split('_');",
        "  const out = { command: parts[0] || '' };",
        "  parts.forEach(p => {",
        "    if (p.indexOf('inviteCode') === 0) out.inviteCode = p.slice(10);",
        "    if (p.indexOf('adSegmentCode') === 0) out.adSegment = p.slice(13);",
        "  });",
        "  return out;",
        "}",
        "",
        "const __origInit = initUser;",
        "initUser = async function () {",
        "  const sp = parseStartParam();",
        "  if (sp.inviteCode) window.__refCode = sp.inviteCode;",
        "  await __origInit();",
        "  initWheel();",
        "  if (sp.command === 'openWheelMain' || location.hash === '#wheel') showScreen('wheel');",
        "};",
        "",
    ])
    s = s + WHEEL + NL
    changed.append("wheel engine")

P.write_text(s, encoding="utf-8")
print(f"[done] game.js: {changed or 'no changes'}")
