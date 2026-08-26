#!/usr/bin/env python3
"""Adds /api/debug/seed endpoint for manual triggering."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
s = P.read_text(encoding="utf-8")

if "/api/debug/seed" in s:
    print("[skip] seed endpoint exists")
else:
    # find x-ray endpoint as anchor
    anchor = "async def api_debug_wallets"
    i = s.find(anchor)
    if i < 0:
        # find # Mount static files
        anchor = "# Mount static files"
        i = s.find(anchor)

    endpoint = (
        "async def api_debug_seed():" + chr(10) +
        "    import db, api.deposits, api.wheel" + chr(10) +
        '    from db.engine import async_session' + chr(10) +
        "    from api import seed_marketplace" + chr(10) +
        "    async with async_session() as session:" + chr(10) +
        "        await seed_marketplace(session)" + chr(10) +
        '    return {"status": "seeded"}' + chr(10)
    )

    if i > 0:
        s = s[:i] + "@app.get('/api/debug/seed')" + chr(10) + endpoint + chr(10) + chr(10) + s[i:]
        P.write_text(s, encoding="utf-8")
        print("[ok] debug seed endpoint added")
    else:
        print("[warn] no anchor found")
