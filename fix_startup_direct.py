#!/usr/bin/env python3
"""Direct fix: rewrite startup + debug seed properly."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
s = P.read_text(encoding="utf-8")
NL = chr(10)

# --- Fix startup ---
START = 'async def startup()'
i = s.find(START)
if i < 0:
    print("[fail] startup not found")
    raise SystemExit

# find end of startup function (next @ decorator)
j = s.find("@app", i + 10)
if j < 0:
    print("[fail] no route after startup")
    raise SystemExit

NEW = """async def startup():
    import db, api.deposits, api.wheel
    from db.engine import init_db
    await init_db()
    from db.engine import async_session
    from api import seed_marketplace
    async with async_session() as session:
        await seed_marketplace(session)
"""

s = s[:i] + NEW + NL + s[j:]
print("[ok] startup rewritten")

# --- Fix debug seed endpoint (add init_db before seed) ---
DS = "async def api_debug_seed()"
i2 = s.find(DS)
if i2 > 0:
    OLD_DS = NL.join([
        "async def api_debug_seed():",
        "    import db, api.deposits, api.wheel",
        "    from db.engine import async_session",
        "    from api import seed_marketplace",
    ])
    NEW_DS = NL.join([
        "async def api_debug_seed():",
        "    import db, api.deposits, api.wheel",
        "    from db.engine import init_db",
        "    await init_db()",
        "    from db.engine import async_session",
        "    from api import seed_marketplace",
    ])
    if OLD_DS in s:
        s = s.replace(OLD_DS, NEW_DS, 1)
        print("[ok] debug seed: init_db added")
    elif "await init_db()" in s[s.find(DS):s.find(DS)+300]:
        print("[skip] debug seed already fixed")

P.write_text(s, encoding="utf-8")
print("[done]")
