#!/usr/bin/env python3
"""Adds Shop, Preview, Confirm, Search to index.html (clean quoting)."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "index.html"
NL = chr(10)

s = P.read_text(encoding="utf-8")
changed = []

# ---- SHOP SCREEN (insert before BOTTOM NAV) ----
if "shop-screen" not in s:
    shop = NL.join([
        "",
        "        <!-- ======== SHOP ======== -->",
        '        <div id="shop-screen" class="screen">',
        '            <div class="top-back" onclick="showScreen(/'home/')">Home</div>',
        '            <h1 class="title">Shop</h1>',
        '            <h2 class="sec-title">Featured</h2>',
        '            <div class="shop-featured" id="shop-featured"></div>',
        '            <h2 class="sec-title">Cases</h2>',
        '            <div class="cases-grid" id="shop-cases"></div>',
        '            <h2 class="sec-title">Boosters</h2>',
        '            <div class="shop-grid">',
        '                <div class="shop-item" onclick="toast(/'Coming soon/')">',
        '                    <span class="shop-emoji">🎯</span><b>Lucky Charm</b>',
        '                    <small>+10% rare chance</small><div class="shop-price">💎 500</div>',
        '                </div>',
        '                <div class="shop-item" onclick="toast(/'Coming soon/')">',
        '                    <span class="shop-emoji">🔮</span><b>Fortune Boost</b>',
        '                    <small>+5% epic chance</small><div class="shop-price">💎 2000</div>',
        '                </div>',
        '                <div class="shop-item" onclick="toast(/'Coming soon/')">',
        '                    <span class="shop-emoji">🎟️</span><b>Spin Pack</b>',
        '                    <small>3 bonus wheel spins</small><div class="shop-price">💎 800</div>',
        '                </div>',
        '            </div>',
        '        </div>',
        "",
    ])
    nav = '        <!-- ======================== BOTTOM NAV'
    i = s.find(nav)
    if i > 0:
        s = s[:i] + shop + NL + s[i:]
        changed.append("shop")

# ---- MODALS (insert before loading div) ----
loading = '<div id="loading" class="loading">'
modals = ""
if "preview-modal" not in s:
    modals += NL.join([
        "", "        <!-- CASE PREVIEW -->",
        '        <div id="preview-modal" class="modal hidden">',
        '            <div class="modal-card preview-card" onclick="event.stopPropagation()">',
        '                <div class="preview-header">',
        '                    <span class="preview-emoji" id="preview-emoji">📦</span>',
        '                    <h2 id="preview-name">-</h2>',
        '                    <p class="preview-price">💎 <span id="preview-price">0</span></p>',
        '                </div>',
        '                <h3 class="sec-title">Possible Rewards</h3>',
        '                <div class="preview-rewards" id="preview-rewards"></div>',
        '                <div class="confirm-actions">',
        '                    <button class="gold-btn" id="preview-open-btn">OPEN CASE</button>',
        '                    <button class="cancel-btn" onclick="closePreview()">Cancel</button>',
        '                </div>',
        '            </div>', "        </div>", "",
    ])
if "confirm-modal" not in s:
    modals += NL.join([
        "", "        <!-- CONFIRM MODAL -->",
        '        <div id="confirm-modal" class="modal hidden">',
        '            <div class="modal-card confirm-card" onclick="event.stopPropagation()">',
        '                <div class="confirm-emoji" id="confirm-emoji">📦</div>',
        '                <h2 id="confirm-text">Open Case?</h2>',
        '                <p class="hint" id="confirm-sub">-</p>',
        '                <div class="confirm-actions">',
        '                    <button class="gold-btn" onclick="executeConfirm()">YES</button>',
        '                    <button class="cancel-btn" onclick="closeConfirm()">CANCEL</button>',
        '                </div>',
        '            </div>', "        </div>", "",
    ])
if modals:
    i = s.find(loading)
    if i > 0:
        s = s[:i] + modals + NL + s[i:]
        changed.append("modals")

# ---- SEARCH BAR (before marketplace filter row) ----
if "search-row" not in s:
    search = NL.join(["",
        '            <div class="search-row">',
        '                <input class="search-input" id="market-search" placeholder="Search items..." oninput="searchMarket(this.value)">',
        '                <select class="sort-select" id="market-sort" onchange="sortMarket(this.value)">',
        '                    <option value="newest">Newest</option>',
        '                    <option value="cheapest">Lowest Price</option>',
        '                    <option value="expensive">Highest Price</option>',
        '                </select>', "            </div>",
    ])
    mkt_i = s.find('id="market-screen"')
    flt_i = s.find('class="filter-row"', mkt_i) if mkt_i > 0 else -1
    if flt_i > 0:
        s = s[:flt_i] + search + NL + s[flt_i:]
        changed.append("search")

P.write_text(s, encoding="utf-8")
print(f"[done] HTML: {changed}")
