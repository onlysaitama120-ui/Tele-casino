#!/usr/bin/env python3
"""Fixes last user.id wallet bug + adds wheel animations."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)

# ---------- 1) wheel.py wallet lookup ----------
P = ROOT / "api" / "wheel.py"
s = P.read_text(encoding="utf-8")
old = "select(Wallet).where(Wallet.user_id == user.id)"
if old in s:
    s = s.replace(old, "select(Wallet).where(Wallet.user_id == user.telegram_id)")
    P.write_text(s, encoding="utf-8")
    print("[ok] wheel.py wallet lookup fixed")
else:
    print("[skip] wheel.py already fixed")

# ---------- 2) confetti trigger in game.js ----------
J = ROOT / "miniapp" / "static" / "game.js"
j = J.read_text(encoding="utf-8")

if "function confetti" not in j:
    conf_fn = NL.join([
        "",
        "/* ============ CONFETTI ============ */",
        "function confetti(count) {",
        "  count = count || 50;",
        "  const colors = ['#ffd54a', '#7c5cff', '#39d353', '#ff5252', '#38bdf8'];",
        "  for (let i = 0; i < count; i++) {",
        "    const d = document.createElement('div');",
        "    d.className = 'confetti';",
        "    d.style.left = (35 + Math.random() * 30) + '%';",
        "    d.style.background = colors[i % colors.length];",
        "    d.style.animationDelay = (Math.random() * 0.4) + 's';",
        "    d.style.transform = 'rotate(' + (Math.random() * 360) + 'deg)';",
        "    document.body.appendChild(d);",
        "    setTimeout(() => d.remove(), 2800);",
        "  }",
        "}",
    ])
    j = j + NL + conf_fn + NL
    print("[ok] confetti function added")

# trigger confetti on gift/gem wins in wheel
old_win = (
    "      box.className = 'result-box win';" + NL +
    "      box.innerHTML = p.emoji + ' <b>' + p.item_name + '</b> won!<br><small>Added to your vault</small>';"
)
new_win = (
    "      box.className = 'result-box win';" + NL +
    "      box.innerHTML = p.emoji + ' <b>' + p.item_name + '</b> won!<br><small>Added to your vault</small>';" + NL +
    "      confetti(90);"
)
if old_win in j:
    j = j.replace(old_win, new_win, 1)
    print("[ok] confetti on gift win")

# big gem win also confetti
old_gem = (
    "      box.className = 'result-box win';" + NL +
    "      box.textContent = '/u{1F48E} +' + p.value + ' gems!';"
)
new_gem = (
    "      box.className = 'result-box win';" + NL +
    "      box.textContent = '/u{1F48E} +' + p.value + ' gems!';" + NL +
    "      if (p.value >= 300) confetti(60);"
)
if old_gem in j:
    j = j.replace(old_gem, new_gem, 1)
    print("[ok] confetti on big gem win")

J.write_text(j, encoding="utf-8")

# ---------- 3) animation CSS ----------
C = ROOT / "miniapp" / "static" / "style.css"
c = C.read_text(encoding="utf-8")

if "confetti-fall" not in c:
    anim = NL.join([
        "",
        "/* ============ WHEEL ANIMATIONS ============ */",
        ".wheel-hub.spinning {",
        "  animation: hubPulse 1s infinite;",
        "}",
        "@keyframes hubPulse {",
        "  50% { box-shadow: 0 0 0 16px rgba(255,213,74,.12), 0 6px 22px rgba(0,0,0,.55); }",
        "}",
        "",
        ".wheel-pointer.bounce {",
        "  animation: pBounce .55s ease;",
        "}",
        "@keyframes pBounce {",
        "  30% { transform: translateX(-50%) translateY(-12px) scale(1.25); }",
        "  60% { transform: translateX(-50%) translateY(3px); }",
        "}",
        "",
        ".big-wheel.settle {",
        "  animation: settle .5s ease;",
        "}",
        "@keyframes settle {",
        "  0% { filter: brightness(1.4); }",
        "  100% { filter: brightness(1); }",
        "}",
        "",
        ".confetti {",
        "  position: fixed;",
        "  top: -16px;",
        "  width: 9px;",
        "  height: 15px;",
        "  z-index: 900;",
        "  border-radius: 2px;",
        "  pointer-events: none;",
        "  animation: confetti-fall 2.4s ease-in forwards;",
        "}",
        "@keyframes confetti-fall {",
        "  to { transform: translateY(105vh) rotate(720deg); opacity: .75; }",
        "}",
        "",
        "#wheel-result.win { animation: winPop .45s cubic-bezier(.2,1.6,.4,1); }",
        "@keyframes winPop {",
        "  0% { transform: scale(.6); opacity: 0; }",
        "  100% { transform: scale(1); opacity: 1; }",
        "}",
    ])
    C.write_text(c + NL + anim + NL, encoding="utf-8")
    print("[ok] animation styles added")
