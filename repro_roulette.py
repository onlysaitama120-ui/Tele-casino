#!/usr/bin/env python3
"""Local repro of roulette 500 - full traceback."""
import asyncio
import os
import sys

sys.path.insert(0, ".")

async def main():
    # fresh temp DB
    if os.path.exists("db/test_repro.db"):
        os.remove("db/test_repro.db")
    import db.engine as eng
    eng.engine = None  # reset any cached engine

    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    engine = create_async_engine("sqlite+aiosqlite:///db/test_repro.db")
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    from db import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from api import get_or_create_user
    from api import spin_roulette

    db = Session()
    try:
        user, _ = await get_or_create_user(db, 424242, username="tester")
        print("[*] user created id:", user.id)

        result = await spin_roulette(db, 424242, 50, "red")
        print("RESULT:", result)
    except Exception:
        import traceback
        traceback.print_exc()
    finally:
        await db.close()

asyncio.run(main())
