#!/usr/bin/env python3
"""
GIFT RUSH - Prize Wheel Engine.
Hero feature: spin for gems & real NFT gift prizes.
Free daily spin + referral bonus spins (viral loop).
"""

import random
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import User, Wallet, Transaction, SpinResult, InventoryItem
from api.deposits import Base, Column, Integer, String, DateTime, Column, Integer, DateTime
import config


class FreeSpinLog(Base):
    __tablename__ = "free_spin_logs"

    id = Column(Integer, primary_key=True)
    user_tg = Column(Integer, nullable=False, index=True)
    source = Column(String(20), nullable=False)  # daily / referral / admin
    created_at = Column(DateTime, default=datetime.utcnow)


def _wheel_total_chance():
    return sum(s["chance"] for s in config.WHEEL_SEGMENTS)


def roll_wheel_segment():
    """Server-side roll. Returns (index, segment)."""
    roll = random.random() * 100
    cumulative = 0.0
    for i, seg in enumerate(config.WHEEL_SEGMENTS):
        cumulative += seg["chance"]
        if roll <= cumulative:
            return i, seg
    return 0, config.WHEEL_SEGMENTS[0]


def get_spin_status(user) -> dict:
    """Compute available spins: free daily + bonus + gem cost."""
    now = datetime.utcnow()
    free_available = False

    if user.last_free_spin is None:
        free_available = True
    elif (now - user.last_free_spin) >= timedelta(hours=23, minutes=50):
        free_available = True

    return {
        "free_available": free_available,
        "bonus_spins": user.bonus_spins or 0,
        "gem_cost": config.WHEEL_SPIN_COST,
        "next_free_in": None if free_available else "24h",
    }


async def spin_wheel(session: AsyncSession, telegram_id: int):
    """
    Execute one wheel spin.
    Priority: free daily spin -> bonus spins -> gems.
    Returns segment index + prize info.
    """
    u = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = u.scalar_one_or_none()
    if not user:
        return {"success": False, "message": "Send /start first"}

    status = get_spin_status(user)
    w = await session.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = w.scalar_one_or_none()
    if not wallet:
        return {"success": False, "message": "Wallet missing"}

    used = None
    if status["free_available"]:
        user.last_free_spin = datetime.utcnow()
        used = "free"
        session.add(FreeSpinLog(
            user_tg=telegram_id, source="daily",
            created_at=datetime.utcnow(),
        ))
    elif (user.bonus_spins or 0) > 0:
        user.bonus_spins -= 1
        used = "bonus"
        session.add(FreeSpinLog(
            user_tg=telegram_id, source="referral",
            created_at=datetime.utcnow(),
        ))
    else:
        if wallet.coins < config.WHEEL_SPIN_COST:
            return {
                "success": False,
                "message": f"Need {config.WHEEL_SPIN_COST} gems — deposit or invite friends for free spins!",
                "balance": wallet.coins,
                "need_gems": True,
            }
        wallet.coins -= config.WHEEL_SPIN_COST
        used = "gems"
        session.add(Transaction(
            user_id=user.telegram_id,
            type="wheel_spin",
            amount=-config.WHEEL_SPIN_COST,
            balance_after=wallet.coins,
            description="Wheel spin",
        ))

    # Roll the wheel server-side
    seg_index, seg = roll_wheel_segment()

    prize = {
        "type": seg["type"],
        "label": seg["label"],
        "emoji": seg["emoji"],
        "value": seg.get("value", 0),
    }

    won_gems = 0
    if seg["type"] == "gems":
        won_gems = seg["value"]
        wallet.coins += won_gems
        prize["credited"] = True
        session.add(Transaction(
            user_id=user.telegram_id,
            type="wheel_win",
            amount=won_gems,
            balance_after=wallet.coins,
            description=f"Wheel prize: {won_gems} gems",
        ))
        user.total_earned += won_gems

    elif seg["type"] == "gift":
        item_meta = seg["item"]
        inv = InventoryItem(
            user_id=user.telegram_id,
            item_name=item_meta["name"],
            item_emoji=item_meta["emoji"],
            rarity=item_meta["rarity"],
            value=item_meta.get("value", seg.get("value", 0)),
            case_id="wheel",
        )
        session.add(inv_item)
        prize["item_name"] = item_meta["name"]
        prize["rarity"] = item_meta["rarity"]
        user.total_earned += seg.get("value", 0)

    # log spin
    session.add(SpinResult(
        user_id=user.telegram_id,
        game_type="wheel",
        bet=config.WHEEL_SPIN_COST if used == "gems" else 0,
        result={"segment": seg_index, "label": seg["label"]},
        multiplier=0,
        won=won_gems,
    ))

    user.wheel_spins = (getattr(user, "wheel_spins", 0) or 0) + 1

    await session.commit()

    return {
        "success": True,
        "segment": seg_index,
        "total_segments": len(config.WHEEL_SEGMENTS),
        "used": used,
        "prize": prize,
        "balance": wallet.coins,
        "status": get_spin_status(user),
    }


async def grant_bonus_spins(session: AsyncSession, telegram_id: int, amount: int):
    """Grant referral/admin bonus spins."""
    u = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = u.scalar_one_or_none()
    if not user:
        return False
    user.bonus_spins = (user.bonus_spins or 0) + amount
    await session.commit()
    return True


async def get_wheel_config():
    """Public wheel view for the mini app."""
    return {
        "segments": [
            {
                "index": i,
                "label": s["label"],
                "emoji": s["emoji"],
                "color": s["color"],
                "type": s["type"],
            }
            for i, s in enumerate(config.WHEEL_SEGMENTS)
        ],
        "spin_cost": config.WHEEL_SPIN_COST,
        "free_per_day": config.FREE_SPIN_PER_DAY,
    }
