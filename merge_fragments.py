#!/usr/bin/env python3
"""Merges fragment files into main app (zero escaping issues)."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)

# ---- HTML fragments ----
html_p = ROOT / "miniapp" / "index.html"
s = html_p.read_text(encoding="utf-8")
n = 0

# 1) Shop before BOTTOM NAV
shop = (ROOT / "frag_shop.html").read_text(encoding="utf-8")
if "shop-screen" not in s:
    nav = '        <!-- ======================== BOTTOM NAV'
    i = s.find(nav)
    if i > 0:
        s = s[:i] + shop + NL + s[i:]
        n += 1

# 2) Modals before loading div
modals = (ROOT / "frag_modals.html").read_text(encoding="utf-8")
if "preview-modal" not in s:
    loading = '<div id="loading" class="loading">'
    i = s.find(loading)
    if i > 0:
        s = s[:i] + modals + NL + s[i:]
        n += 1

# 3) Search bar before marketplace filter
search = (ROOT / "frag_search.html").read_text(encoding="utf-8")
if "search-row" not in s:
    mkt_i = s.find('id="market-screen"')
    flt_i = s.find('class="filter-row"', mkt_i) if mkt_i > 0 else -1
    if flt_i > 0:
        s = s[:flt_i] + search + NL + s[flt_i:]
        n += 1

# bump cache
s = s.replace("style.css?v=8", "style.css?v=9").replace("game.js?v=8", "game.js?v=9")
html_p.write_text(s, encoding="utf-8")
print(f"[ok] HTML: {n} fragments merged")

# ---- CSS fragment ----
css_p = ROOT / "miniapp" / "static" / "style.css"
css_s = css_p.read_text(encoding="utf-8")
css_extra = (ROOT / "frag_styles_extra.css").read_text(encoding="utf-8")
if "RARITY GLOW" not in css_s:
    css_p.write_text(css_s + NL + css_extra, encoding="utf-8")
    print("[ok] CSS: rarity glow + shop + confirm styles appended")
else:
    print("[skip] CSS already updated")

# ---- JS fragment ----
js_p = ROOT / "miniapp" / "static" / "game.js"
js_s = js_p.read_text(encoding="utf-8")
js_extra = (ROOT / "frag_game_extra.js").read_text(encoding="utf-8")
if "loadShop" not in js_s:
    js_p.write_text(js_s + NL + js_extra, encoding="utf-8")
    print("[ok] JS: shop + search + confirm + tasks appended")
else:
    print("[skip] JS already updated")
