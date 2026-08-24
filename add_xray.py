#!/usr/bin/env python3
"""Temporary X-ray: dumps every wallet + user row mapping."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

if "/api/debug/wallets" in s:
    print("[skip] exists")
    raise SystemExit

BLOCK = NL.join([
    "",
    "@app.get(" + DQ + "/api/debug/wallets" + DQ + ")",
    "async def api_debug_wallets():",
    "    from sqlalchemy import select",
    "    from db import User, Wallet",
    "    async with async_session() as session:",
    "        users = (await session.execute(select(User))).scalars().all()",
    "        wallets = (await session.execute(select(Wallet))).scalars().all()",
    "        wmap = {w.user_id: w.coins for w in wallets}",
    "        return [",
    "            {",
    '                "row_id": u.id,',
    '                "telegram_id": u.telegram_id,',
    '                "username": u.username,',
    '                "wallet_row_for_internal": wmap.get(u.id, "MISSING"),',
    '                "wallet_row_for_telegram": wmap.get(u.telegram_id, "MISSING"),',
    "            }",
    "            for u in users",
    "        ]",
    "",
])

marker = "# Mount static files"
i = s.find(marker)
if i < 0:
    raise SystemExit("[fail] marker missing")
s = s[:i] + BLOCK + NL + s[i:]
P.write_text(s, encoding="utf-8")
print("[ok] x-ray endpoint added")
