#!/usr/bin/env python3
"""Wraps debug seed endpoint with traceback reporting."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
s = P.read_text(encoding="utf-8")
NL = chr(10)

OLD = NL.join([
    "async def api_debug_seed():",
    "    import db, api.deposits, api.wheel",
    "    from db.engine import init_db",
    "    await init_db()",
    "    from db.engine import async_session",
    "    from api import seed_marketplace",
    "    async with async_session() as session:",
    "        await seed_marketplace(session)",
    '    return {"status": "seeded"}',
])

NEW = NL.join([
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

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] debug endpoint wrapped with error reporting")
elif "traceback.format_exc" in s:
    print("[skip] already wrapped")
else:
    print("[warn] pattern not found")
