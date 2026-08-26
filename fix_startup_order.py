#!/usr/bin/env python3
"""Fixes startup: import models BEFORE create_all so all tables exist."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
NL = chr(10)

s = P.read_text(encoding="utf-8")

OLD = (
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

NEW = (
    '@app.on_event("startup")' + NL +
    'async def startup():' + NL +
    '    """Initialize database + seed marketplace."""' + NL +
    '    # register all models with Base.metadata BEFORE create_all' + NL +
    '    import db                           # User, Wallet, InventoryItem, ...' + NL +
    '    import api.deposits                 # Deposit, WithdrawRequest' + NL +
    '    import api.wheel                    # FreeSpinLog' + NL +
    '    from db.engine import init_db' + NL +
    '    await init_db()                     # now ALL tables are created' + NL +
    '    from db.engine import async_session' + NL +
    '    from api import seed_marketplace' + NL +
    '    async with async_session() as session:' + NL +
    '        await seed_marketplace(session)'
)

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] startup imports fixed (models before create_all)")
elif "import db" in s and "seed_marketplace" in s:
    print("[skip] already fixed")
else:
    print("[warn] anchor not found")
    # find what we have
    i = s.find("startup")
    if i > 0:
        print(s[i:i+400])
