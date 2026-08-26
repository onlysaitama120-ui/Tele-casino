#!/usr/bin/env python3
"""Adds marketplace auto-seeding + demo item purchase fix + home promo card."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)
DQ = chr(34)

# ========== 1. api/__init__.py — add seed_marketplace function ==========
P = ROOT / "api" / "__init__.py"
s = P.read_text(encoding="utf-8")

SEED_FN = NL.join([
    "",
    "async def seed_marketplace(session):",
    '    """Create 25 demo listings if DB is empty."""',
    "    from sqlalchemy import func",
    "    count = await session.execute(select(func.count()).select_from(MarketplaceListing))",
    "    if count.scalar() and count.scalar() > 0:",
    '        return  # already seeded',
    "",
    "    all_items = []",
    "    for case in config.BOXES.values():",
    "        for item in case['items']:",
    "            all_items.append(item)",
    "",
    "    rarity_mult = {",
    '        "common": 1.2, "uncommon": 2.5, "rare": 5, "epic": 15,',
    '        "legendary": 50, "mythic": 200, "divine": 1000',
    "    }",
    "",
    "    import random",
    "    for _ in range(25):",
    "        item = random.choice(all_items)",
    "        base = item.get('value', 100)",
    "        mult = rarity_mult.get(item.get('rarity', 'common'), 1)",
    "        price = int(base * mult * random.uniform(0.7, 1.3))",
    "        price = max(price, 10)",
    "",
    "        inv = InventoryItem(",
    "            user_id=0,  # system/demo seller",
    "            item_name=item['name'],",
    "            item_emoji=item.get('emoji', '🎁'),",
    "            rarity=item.get('rarity', 'common'),",
    "            value=item.get('value', 0),",
    "        )",
    "        session.add(inv)",
    "        await session.flush()",
    "",
    "        listing = MarketplaceListing(",
    "            item_id=inv.id,",
    "            seller_id=0,",
    "            price=price,",
    "            is_active=True,",
    "        )",
    "        session.add(listing)",
    "",
    "    await session.commit()",
    '    print("[+] Marketplace seeded with 25 starter listings")',
    "",
])

if "async def seed_marketplace" not in s:
    # Insert before # MARKETPLACE section
    anchor = "# MARKETPLACE"
    i = s.find(anchor)
    if i > 0:
        s = s[:i] + SEED_FN + NL + s[i:]
    else:
        s += NL + SEED_FN
    P.write_text(s, encoding="utf-8")
    print("[ok] seed_marketplace added")
else:
    print("[skip] seed_marketplace exists")

# ========== 2. Fix buy_item: allow purchasing demo listings (seller_id=0) ==========
s2 = ROOT / "api" / "__init__.py"
c = s2.read_text(encoding="utf-8")

old_buy = '    if listing.seller_id == user_id:'
new_buy = '    if listing.seller_id != 0 and listing.seller_id == user_id:'

if new_buy not in c and old_buy in c:
    c = c.replace(old_buy, new_buy, 1)
    s2.write_text(c, encoding="utf-8")
    print("[ok] demo items now purchasable")
elif new_buy in c:
    print("[skip] buy fix applied")
else:
    print("[warn] buy anchor not found")

# ========== 3. Call seed from server.py startup ==========
SV = ROOT / "api" / "server.py"
sv = SV.read_text(encoding="utf-8")

OLD_STARTUP = (
    '@app.on_event("startup")' + NL +
    'async def startup():' + NL +
    '    """Initialize database on first request."""' + NL +
    '    from db.engine import init_db' + NL +
    '    await init_db()'
)

NEW_STARTUP = (
    '@app.on_event("startup")' + NL +
    'async def startup():' + NL +
    '    """Initialize database + seed marketplace."""' + NL +
    '    from db.engine import init_db' + NL +
    '    await init_db()' + NL +
    '    from db.engine import async_session' + NL +
    '    from api import seed_marketplace' + NL +
    '    async with async_session() as session:' + NL +
    '        await seed_marketplace(session)'
)

if OLD_STARTUP in sv:
    sv = sv.replace(OLD_STARTUP, NEW_STARTUP, 1)
    SV.write_text(sv, encoding="utf-8")
    print("[ok] startup seeds marketplace")
elif "seed_marketplace" in sv:
    print("[skip] startup already seeds")
else:
    print("[warn] startup anchor not found")

# ========== 4. Home promo card for marketplace ==========
HTML = ROOT / "miniapp" / "index.html"
h = HTML.read_text(encoding="utf-8")

if "market-promo" not in h:
    promo = NL.join([
        "",
        '            <h2 class="sec-title">🛒 Marketplace</h2>',
        '            <div class="market-promo" onclick="showScreen(/'market/')">',
        '                <div class="mp-left">',
        '                    <span class="mp-icon">💎</span>',
        '                    <div><b>Buy & Sell NFT Gifts</b>',
        '                    <small id="mp-count">Browse collectibles...</small></div>',
        '                </div>',
        '                <span class="claim-btn">VIEW</span>',
        '            </div>',
        "",
    ])
    # insert before the Rankings section
    rank_anchor = '        <h2 class="sec-title">'
    i = h.find(rank_anchor, h.find('id="home-screen"'))
    if i > 0:
        h = h[:i] + promo + NL + h[i:]
        HTML.write_text(h, encoding="utf-8")
        print("[ok] marketplace promo added to home")
    else:
        print("[warn] rank anchor not found in home")

print("[done] marketplace fixes applied")
