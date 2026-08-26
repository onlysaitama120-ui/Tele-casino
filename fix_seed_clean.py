#!/usr/bin/env python3
"""Minimal test endpoint - no imports, no logic."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
s = P.read_text(encoding="utf-8")

# Add a test endpoint right before "Mount static files"
marker = "# Mount static files"
endpoint = """
# ============================================================
# MARKETPLACE SEED (manual trigger)
# ============================================================
@app.get("/api/debug/seed")
async def api_debug_seed():
    import traceback, random, config
    try:
        import db, api.deposits
        from db.engine import init_db, async_session
        await init_db()
        from api.deposits import InventoryItem, MarketplaceListing
        import sqlalchemy as sa
        async with async_session() as session:
            count_result = await session.execute(
                sa.select(sa.func.count()).select_from(MarketplaceListing)
            )
            existing = count_result.scalar() or 0
            if existing > 0:
                return {"ok": True, "listings": existing}

            pool = []
            for case in config.BOXES.values():
                for item in case.get("items", []):
                    pool.append(item)

            rarity_mult = {"common": 1.2, "uncommon": 2.5, "rare": 5,
                          "epic": 15, "legendary": 50, "mythic": 200, "divine": 1000}

            for _ in range(25):
                pick = random.choice(pool)
                val = pick.get("value", 100)
                m = rarity_mult.get(pick.get("rarity", "common"), 1)
                price = max(int(val * m * random.uniform(0.7, 1.3)), 10)
                inv = InventoryItem(
                    user_id=0,
                    item_name=pick["name"],
                    item_emoji=pick.get("emoji", "🎁"),
                    rarity=pick.get("rarity", "common"),
                    value=val,
                )
                session.add(inv)
                await session.flush()
                listing = MarketplaceListing(
                    item_id=inv.id, seller_id=0,
                    price=price, is_active=True,
                )
                session.add(listing)
            await session.commit()
            return {"ok": True, "seeded": 25}

    except Exception:
        return {"error": traceback.format_exc()[-500:]}

"""

if "api/debug/seed" in s:
    # remove old version
    i = s.find("@app.get(/"/api/debug/seed/")")
    if i > 0:
        j = s.find("@app", i + 10)
        if j > 0:
            s = s[:i] + s[j:]
            print("[removed old debug endpoint]")

# insert before marker
i = s.find(marker)
s = s[:i] + endpoint + NL + s[i:]
P.write_text(s, encoding="utf-8")
print("[ok] debug seed endpoint rebuilt clean")
