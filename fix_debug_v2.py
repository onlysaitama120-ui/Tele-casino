#!/usr/bin/env python3
"""Ultra-simple debug: just tests init_db + manual insert."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
s = P.read_text(encoding="utf-8")
NL = chr(10)

OLD_DEBUG = NL.join([
    "async def api_debug_seed():",
    "    import traceback, db, api.deposits, api.wheel",
    "    try:",
    "        from db.engine import init_db",
    "        await init_db()",
    "        from db.engine import async_session",
    "        from api import seed_marketplace",
    "        async with async_session() as session:",
    "            await seed_marketplace(session)",
    '        return {"status": "seeded"}',
    "    except Exception as e:",
    '        return {"error": traceback.format_exc()[-600:]}',
])

NEW_DEBUG = NL.join([
    "async def api_debug_seed():",
    "    import traceback, random",
    "    try:",
    "        import db, api.deposits, config",
    "        from db.engine import init_db, async_session",
    "        await init_db()",
    "        from api.deposits import InventoryItem, MarketplaceListing",
    "        async with async_session() as session:",
    "            count = 0",
    "            import sqlalchemy as sa",
    "            result = await session.execute(sa.select(sa.func.count()).select_from(MarketplaceListing))",
    "            count = result.scalar() or 0",
    "            if count > 0:",
    '                return {"status": f"already seeded ({count} listings)"}',
    "            all_items = []",
    "            for case_name, case in config.CASES.items():",
    "                for item in case.get('items', []):",
    "                    all_items.append(item)",
    "            rarity_mult = {'common':1.2,'uncommon':2.5,'rare':5,'epic':15,'legendary':50,'mythic':200,'divine':1000}",
    "            for _ in range(25):",
    "                item = random.choice(all_items)",
    "                base = item.get('value', 100)",
    "                mult = rarity_mult.get(item.get('rarity','common'), 1)",
    "                price = max(int(base * mult * random.uniform(0.7, 1.3)), 10)",
    "                inv = InventoryItem(user_id=0, item_name=item['name'],",
    "                    item_emoji=item.get('emoji','🎁'), rarity=item.get('rarity','common'),",
    "                    value=item.get('value', 0))",
    "                session.add(inv)",
    "                await session.flush()",
    "                session.add(MarketplaceListing(item_id=inv.id, seller_id=0, price=price, is_active=True))",
    "            await session.commit()",
    '            return {"status": "seeded 25 items"}',
    "    except Exception as e:",
    '        return {"error": traceback.format_exc()[-600:]}',
])

if OLD_DEBUG in s:
    s = s.replace(OLD_DEBUG, NEW_DEBUG, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] debug seed replaced with standalone version")
elif "ultra-simple" not in s:
    # fallback: find and replace the entire debug seed function
    print("[warn] old pattern not found, writing directly")
