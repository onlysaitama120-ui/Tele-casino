#!/usr/bin/env python3
"""Adds wheel hero banner + wheel screen to index.html (clean quoting)."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "index.html"
NL = chr(10)
DQ = chr(34)
SQ = chr(39)

def q(s):
    return DQ + s + DQ

# ---------- 1) hero banner ----------
hero = NL.join([
    "",
    "            <!-- WHEEL HERO -->",
    "            <div class=" + q("wheel-hero") + " onclick=" + q("showScreen(" + SQ + "wheel" + SQ + ")") + ">",
    '                <div class="wh-left">',
    '                    <span class="wh-icon">🎡</span>',
    "                    <div><b>GIFT WHEEL</b><small>Win Plush Pepe · Durov Cap</small></div>",
    "                </div>",
    '                <span class="claim-btn wh-btn">SPIN</span>',
    "            </div>",
    "",
])
anchor1 = '            <h2 class="sec-title">📦 Mystery Boxes</h2>'

# ---------- 2) wheel screen ----------
wheel_screen = NL.join([
    "",
    "        <!-- ======== GIFT WHEEL ======== -->",
    '        <div id="wheel-screen" class="screen">',
    '            <div class="top-back" onclick=' + q("showScreen(" + SQ + "menu" + SQ + ")") + ">← Game</div>",
    '            <h1 class="title">🎡 Gift Wheel</h1>',
    "",
    '            <div class="wheel-stage">',
    '                <div class="wheel-pointer">▼</div>',
    '                <div class="big-wheel" id="big-wheel"></div>',
    '                <div class="wheel-hub" id="wheel-spin-btn" onclick=' + q("spinWheel()") + ">SPIN</div>",
    "            </div>",
    "",
    '            <div id="wheel-status" class="wheel-status"></div>',
    '            <div id="wheel-result" class="result-box hidden"></div>',
    "",
    '            <div class="paytable">',
    "                <b>🎁 Prize Pool</b>",
    "                <span>🐸 Plush Pepe — 0.001%</span>",
    "                <span>🧢 Durov Cap — 0.03%</span>",
    "                <span>🌹 Eternal Rose — 0.15%</span>",
    "                <span>💍 Neon Signet — 0.8%</span>",
    "                <span>💎 up to 300 gems on every spin</span>",
    "            </div>",
    "        </div>",
    "",
])
anchor2 = '        <!-- ======== DEPOSIT ======== -->'

s = P.read_text(encoding="utf-8")
changed = []

if "wheel-hero" not in s:
    i = s.find(anchor1)
    if i < 0:
        raise SystemExit("[fail] cases anchor missing")
    s = s[:i] + hero + NL + s[i:]
    changed.append("hero")

if 'id="wheel-screen"' not in s:
    i = s.find(anchor2)
    if i < 0:
        raise SystemExit("[fail] deposit anchor missing")
    s = s[:i] + wheel_screen + NL + s[i:]
    changed.append("wheel-screen")

s = s.replace("style.css?v=6", "style.css?v=7").replace("game.js?v=6", "game.js?v=7")
s = s.replace("style.css?v=5", "style.css?v=7").replace("game.js?v=5", "game.js?v=7")

P.write_text(s, encoding="utf-8")
print(f"[done] index.html updated: {changed or 'cache only'}")
