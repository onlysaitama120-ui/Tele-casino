#!/usr/bin/env python3
"""Inserts marketplace promo card into home screen."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "index.html"
s = P.read_text(encoding="utf-8")

if "market-promo" in s:
    print("[skip] already present")
    exit()

promo = """
            <h2 class="sec-title">🛒 Marketplace</h2>
            <div class="market-promo" onclick="showScreen('market')">
                <div class="mp-left">
                    <span class="mp-icon">💎</span>
                    <div><b>Buy &amp; Sell NFT Gifts</b>
                    <small>Browse collectibles from the community</small></div>
                </div>
                <span class="claim-btn">VIEW</span>
            </div>
"""

anchor = 'Rankings</h2>'
i = s.find(anchor)
if i < 0:
    print("[warn] anchor not found")
    exit()

# find the full <h2> tag before anchor
tag_start = s.rfind('<h2', 0, i)
if tag_start < 0:
    print("[warn] h2 tag not found before anchor")
    exit()

s = s[:tag_start] + promo + "    " + s[tag_start:]
P.write_text(s, encoding="utf-8")
print("[ok] marketplace promo inserted before Rankings")
