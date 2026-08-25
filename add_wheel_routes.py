#!/usr/bin/env python3
"""Injects wheel routes into server.py + wheel_spins column migration."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)
DQ = chr(34)

# ---------- 1. server.py routes ----------
P = ROOT / "api" / "server.py"
s = P.read_text(encoding="utf-8")

if "/api/wheel/spin" in s:
    print("[skip] wheel routes exist")
else:
    imp_old = "from api.deposits import ("
    imp_new = NL.join([
        "from api.wheel import (",
        "    spin_wheel, get_wheel_config, get_spin_status, grant_bonus_spins,",
        ")",
        "from api.deposits import (",
    ])
    s = s.replace(imp_old, imp_new, 1)

    ROUTES = NL.join([
        "",
        "# ============================================================",
        "# GIFT WHEEL",
        "# ============================================================",
        "",
        "@app.get(" + DQ + "/api/wheel/config" + DQ + ")",
        "async def api_wheel_config():",
        "    return await get_wheel_config()",
        "",
        "",
        "@app.post(" + DQ + "/api/wheel/status" + DQ + ")",
        "async def api_wheel_status(request: Request):",
        "    data = await request.json()",
        "    uid = data.get(" + DQ + "user_id" + DQ + ")",
        "    from sqlalchemy import select",
        "    from db import User",
        "    async with async_session() as session:",
        "        u = await session.execute(select(User).where(User.telegram_id == uid))",
        "        user = u.scalar_one_or_none()",
        "        if not user:",
        '            return {"error": "no user"}',
        "        return get_spin_status(user)",
        "",
        "",
        "@app.post(" + DQ + "/api/wheel/spin" + DQ + ")",
        "async def api_wheel_spin(request: Request):",
        "    data = await request.json()",
        "    uid = data.get(" + DQ + "user_id" + DQ + ")",
        "    if not uid:",
        '        raise HTTPException(status_code=400, detail="Missing user_id")',
        "    _rl(uid, " + DQ + "wheel" + DQ + ", 3.0)",
        "    async with async_session() as session:",
        "        return await spin_wheel(session, uid)",
        "",
    ])

    marker = "# Mount static files"
    i = s.find(marker)
    if i < 0:
        raise SystemExit("[fail] mount marker missing")
    s = s[:i] + ROUTES + NL + s[i:]
    P.write_text(s, encoding="utf-8")
    print("[ok] wheel routes injected")

# ---------- 2. engine migrations for new columns ----------
E = ROOT / "db" / "engine.py"
e = E.read_text(encoding="utf-8")

if "ALTER TABLE users ADD COLUMN last_free_spin" in e:
    print("[skip] migrations exist")
else:
    old = "    async with engine.begin() as conn:" + NL + "        await conn.run_sync(Base.metadata.create_all)"
    BS = chr(92)
    new = (
        "    async with engine.begin() as conn:" + NL +
        "        await conn.run_sync(Base.metadata.create_all)" + NL +
        "        from sqlalchemy import text" + NL +
        "        migrations = [" + NL +
        "            " + DQ + "ALTER TABLE users ADD COLUMN last_free_spin DATETIME" + DQ + "," + NL +
        "            " + DQ + "ALTER TABLE users ADD COLUMN bonus_spins INTEGER DEFAULT 0" + DQ + "," + NL +
        "            " + DQ + "ALTER TABLE users ADD COLUMN wheel_spins INTEGER DEFAULT 0" + DQ + "," + NL +
        "            " + DQ + "ALTER TABLE withdraw_requests ADD COLUMN item_id INTEGER" + DQ + "," + NL +
        "        ]" + NL +
        "        for stmt in migrations:" + NL +
        "            try:" + NL +
        "                await conn.execute(text(stmt))" + NL +
        "            except Exception:" + NL +
        "                pass  # column already exists"
    )
    if old in e:
        e = e.replace(old, new, 1)
        E.write_text(e, encoding="utf-8")
        print("[ok] safe migrations added to init_db")
    else:
        print("[warn] engine anchor drifted - add manually")
