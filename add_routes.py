#!/usr/bin/env python3
"""Adds deposit/withdraw routes into api/server.py before static mount."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

if "/api/deposit/info" in s:
    print("[skip] routes already added")
    raise SystemExit

# import block
imp_old = "import config"
imp_new = NL.join([
    "import config",
    "from api.deposits import (",
    "    get_deposit_info, check_deposits,",
    "    request_withdrawal, list_withdrawals, complete_withdrawal,",
    ")",
])
s = s.replace(imp_old, imp_new, 1)

ROUTES = NL.join([
    "",
    "# ============================================================",
    "# DEPOSITS (TON)",
    "# ============================================================",
    "",
    "@app.post(" + DQ + "/api/deposit/info" + DQ + ")",
    "async def api_deposit_info(request: Request):",
    "    data = await request.json()",
    "    user_id = data.get(" + DQ + "user_id" + DQ + ")",
    "    if not user_id:",
    '        raise HTTPException(status_code=400, detail="Missing user_id")',
    "    async with async_session() as session:",
    "        return await get_deposit_info(session, user_id)",
    "",
    "",
    "@app.post(" + DQ + "/api/deposit/check" + DQ + ")",
    "async def api_deposit_check(request: Request):",
    "    data = await request.json()",
    "    user_id = data.get(" + DQ + "user_id" + DQ + ")",
    "    if not user_id:",
    '        raise HTTPException(status_code=400, detail="Missing user_id")',
    "    async with async_session() as session:",
    "        result = await check_deposits(session, user_id)",
    "        return result",
    "",
    "",
    "# ============================================================",
    "# WITHDRAWALS",
    "# ============================================================",
    "",
    "@app.post(" + DQ + "/api/withdraw" + DQ + ")",
    "async def api_withdraw(request: Request):",
    "    data = await request.json()",
    "    user_id = data.get(" + DQ + "user_id" + DQ + ")",
    "    item_id = data.get(" + DQ + "item_id" + DQ + ")",
    "    if not user_id or not item_id:",
    '        raise HTTPException(status_code=400, detail="Missing parameters")',
    "    async with async_session() as session:",
    "        return await request_withdrawal(session, user_id, item_id)",
    "",
    "",
    "@app.get(" + DQ + "/api/withdrawals" + DQ + ")",
    "async def api_withdrawals():",
    "    async with async_session() as session:",
    "        return {" + DQ + "requests" + DQ + ": await list_withdrawals(session)}",
    "",
    "",
    "@app.post(" + DQ + "/api/withdrawals/complete" + DQ + ")",
    "async def api_withdrawals_complete(request: Request):",
    "    data = await request.json()",
    "    admin_id = data.get(" + DQ + "admin_id" + DQ + ")",
    "    request_id = data.get(" + DQ + "request_id" + DQ + ")",
    "    if admin_id not in config.ADMIN_IDS:",
    '        raise HTTPException(status_code=403, detail="Unauthorized")',
    "    async with async_session() as session:",
    "        return await complete_withdrawal(session, request_id)",
    "",
])

marker = "# Mount static files"
i = s.find(marker)
if i < 0:
    raise SystemExit("[fail] mount marker missing")
s = s[:i] + ROUTES + NL + s[i:]

# compatibility alias so case engine keeps working after rebrand
if "CASES = BOXES" not in s and "config.CASES" in s:
    pass  # handled in config.py

P.write_text(s, encoding="utf-8")
print("[ok] deposit/withdraw routes injected")

# config alias
cfg = ROOT = pathlib.Path(__file__).parent / "config.py"
c = cfg.read_text(encoding="utf-8")
if "CASES = BOXES" not in c:
    c += NL + "# compat alias for case engine" + NL + "CASES = BOXES" + NL
    cfg.write_text(c, encoding="utf-8")
    print("[ok] config.CASES alias added")
