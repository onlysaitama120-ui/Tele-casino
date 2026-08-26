#!/usr/bin/env python3
"""Adds seed_marketplace to api/__init__.py."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "__init__.py"
s = P.read_text(encoding="utf-8")
NL = chr(10)

if "async def seed_marketplace" in s:
    print("[skip] already exists")
else:
    seed_fn = NL.join([
        "",
        "async def seed_marketplace(session):",
        '    """Auto-populate marketplace with 25 demo listings on fresh DB."""',
        "    import random",
        "    from sqlalchemy import func",
        "    try:",
        "        count = await session.execute(select(func.count()).select_from(MarketplaceListing))",
        "        if count.scalar() and count.scalar() > 0:",
        '            return',
        "    except Exception:",
        "        pass  # table might not exist yet",
        "",
        "    pool = []",
        "    for case in config.BOXES.values():",
        "        for item in case.get('items', []):",
        "            pool.append(item)",
        "    if not pool:",
        '        return',
        "",
        "    rarity_mult = {",
        '        "common": 1.2, "uncommon": 2.5, "rare": 5, "epic": 15,',
        '        "legendary": 50, "mythic": 200, "divine": 1000',
        "    }",
        "",
        "    for _ in range(25):",
        "        pick = random.choice(pool)",
        "        val = pick.get('value', 100)",
        "        m = rarity_mult.get(pick.get('rarity', 'common'), 1)",
        "        price = max(int(val * m * random.uniform(0.7, 1.3)), 10)",
        "        inv = InventoryItem(",
        "            user_id=0,",
        "            item_name=pick['name'],",
        "            item_emoji=pick.get('emoji', '🎁'),",
        "            rarity=pick.get('rarity', 'common'),",
        "            value=val,",
        "        )",
        "        session.add(inv)",
        "        await session.flush()",
        "        session.add(MarketplaceListing(",
        "            item_id=inv.id, seller_id=0,",
        "            price=price, is_active=True,",
        "        ))",
        "    await session.commit()",
        '    print("[+] Marketplace seeded with 25 demo listings")',
        "",
    ])

    # Insert before the MARKETPLACE section (which starts the route handlers)
    anchor = "# MARKETPLACE" + NL + "# ===="
    i = s.find(anchor)
    if i > 0:
        s = s[:i] + seed_fn + NL + s[i:]
    else:
        # fallback: append before spin_roulette function
        anchor2 = "# SLOTS MACHINE"
        i2 = s.find(anchor2)
        if i2 > 0:
            s = s[:i2] + seed_fn + NL + s[i2:]
        else:
            s += seed_fn
            print("[warn] appended to end of file")

    P.write_text(s, encoding="utf-8")
    print("[ok] seed_marketplace added to api/__init__.py")
