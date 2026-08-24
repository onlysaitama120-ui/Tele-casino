#!/usr/bin/env python3
"""Database engine and session management."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from db import Base

DATABASE_URL = "sqlite+aiosqlite:///db/casino.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    os.makedirs("db", exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """Get a database session."""
    async with async_session() as session:
        yield session
