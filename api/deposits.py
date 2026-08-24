#!/usr/bin/env python3
"""
GIFT RUSH - Deposit & Withdraw engine.
TON deposits verified via toncenter public API.
Withdrawals create admin-fulfilled payout requests.
"""

import os
import aiohttp
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import (
    Base, Column, Integer, String, Float, DateTime,
    User, Wallet, Transaction, InventoryItem,
)

# TON settings
TON_WALLET = os.environ.get("TON_WALLET", "UQYourMerchantTonWalletAddressHere")
TONCENTER = "https://toncenter.com/api/v2"
GEMS_PER_TON = int(os.environ.get("GEMS_PER_TON", "1000"))
DEPOSIT_MIN_TON = float(os.environ.get("DEPOSIT_MIN_TON", "0.1"))

NANO = 1_000_000_000


def user_memo(telegram_id: int) -> str:
    """Unique memo so we know which user sent the TON."""
    return f"GR{telegram_id}"


# ============================================================
# MODELS (registered on shared Base)
# ============================================================

class Deposit(Base):
    __tablename__ = "deposits"

    id = Column(Integer, primary_key=True)
    user_tg = Column(Integer, nullable=False, index=True)
    tx_hash = Column(String, unique=True, nullable=False)
    amount_ton = Column(Float, nullable=False)
    gems = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"

    id = Column(Integer, primary_key=True)
    user_tg = Column(Integer, nullable=False, index=True)
    username = Column(String, nullable=True)
    item_name = Column(String, nullable=False)
    item_value = Column(Integer, default=0)
    item_id = Column(Integer, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


# ============================================================
# DEPOSITS
# ============================================================

async def get_deposit_info(session: AsyncSession, telegram_id: int):
    """Deposit address + personal memo + rates."""
    return {
        "address": TON_WALLET,
        "memo": user_memo(telegram_id),
        "gems_per_ton": GEMS_PER_TON,
        "min_ton": DEPOSIT_MIN_TON,
    }


async def check_deposits(session: AsyncSession, telegram_id: int):
    """
    Scan recent incoming TON transactions to merchant wallet.
    Credits gems where comment == user memo and tx not credited before.
    """
    memo = user_memo(telegram_id)
    url = f"{TONCENTER}/getTransactions?address={TON_WALLET}&limit=25"

    try:
        async with aiohttp.ClientSession() as http:
            async with http.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                data = await resp.json()
    except Exception as e:
        return {"success": False, "message": f"Blockchain API error: {e}"}

    if not data.get("ok"):
        return {"success": False, "message": "toncenter unavailable, try later"}

    txs = data.get("result") or []

    seen_rows = await session.execute(
        select(Deposit.tx_hash).where(Deposit.user_tg == telegram_id)
    )
    seen = {h for (h,) in seen_rows.all()}

    u = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = u.scalar_one_or_none()
    if not user:
        return {"success": False, "message": "Send /start first"}

    w = await session.execute(select(Wallet).where(Wallet.user_id == user.id))
    wallet = w.scalar_one_or_none()
    if not wallet:
        return {"success": False, "message": "Wallet missing"}

    credited_ton = 0.0
    credited_count = 0

    for tx in txs:
        tx_hash = (tx.get("transaction_id") or {}).get("hash", "")
        if not tx_hash or tx_hash in seen:
            continue

        in_msg = tx.get("in_msg") or {}
        comment = (in_msg.get("comment") or "").strip()
        if comment != memo:
            continue

        amount_ton = int(in_msg.get("value", "0")) / NANO
        if amount_ton < DEPOSIT_MIN_TON:
            continue

        gems = int(amount_ton * GEMS_PER_TON)

        session.add(Deposit(
            user_tg=telegram_id,
            tx_hash=tx_hash,
            amount_ton=amount_ton,
            gems=gems,
            created_at=datetime.utcnow(),
        ))

        wallet.coins += gems
        wallet.total_deposited += amount_ton

        session.add(Transaction(
            user_id=user.id,
            type="deposit",
            amount=gems,
            balance_after=wallet.coins,
            description=f"Deposit {amount_ton:.2f} TON",
        ))

        credited_ton += amount_ton
        credited_count += 1

    await session.commit()

    if credited_count:
        return {
            "success": True,
            "credited_ton": round(credited_ton, 3),
            "credited_gems": int(credited_ton * GEMS_PER_TON),
            "balance": wallet.coins,
        }
    return {"success": False, "message": "No new deposits found yet"}


# ============================================================
# WITHDRAWALS
# ============================================================

async def request_withdrawal(session: AsyncSession, telegram_id: int, item_id: int):
    """Queue an item for gift payout. Admin fulfils manually."""
    u = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = u.scalar_one_or_none()
    if not user:
        return {"success": False, "message": "User not found"}

    it = await session.execute(
        select(InventoryItem).where(
            InventoryItem.id == item_id,
            InventoryItem.user_id == user.id,
        )
    )
    item = it.scalar_one_or_none()
    if not item:
        return {"success": False, "message": "Item not found"}
    if item.is_locked:
        return {"success": False, "message": "Item already queued"}

    pend = await session.execute(
        select(WithdrawRequest).where(
            WithdrawRequest.user_tg == telegram_id,
            WithdrawRequest.status == "pending",
        )
    )
    if len(pend.scalars().all()) >= 3:
        return {"success": False, "message": "Max 3 pending withdrawals"}

    item.is_locked = True

    wr = WithdrawRequest(
        user_tg=telegram_id,
        username=user.username or "",
        item_name=item.item_name,
        item_value=item.value,
        item_id=item.id,
        status="pending",
        created_at=datetime.utcnow(),
    )
    session.add(wr)
    await session.commit()

    return {
        "success": True,
        "request_id": wr.id,
        "message": f"Withdrawal #{wr.id} queued! Admin will deliver your reward.",
    }


async def list_withdrawals(session: AsyncSession):
    """Admin: pending withdrawal queue."""
    result = await session.execute(
        select(WithdrawRequest).where(WithdrawRequest.status == "pending")
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "user": r.username or str(r.user_tg),
            "user_tg": r.user_tg,
            "item": r.item_name,
            "value": r.item_value,
        }
        for r in rows
    ]


async def complete_withdrawal(session: AsyncSession, request_id: int):
    """Admin marks fulfilled; consume the locked item."""
    r = await session.execute(
        select(WithdrawRequest).where(WithdrawRequest.id == request_id)
    )
    wr = r.scalar_one_or_none()
    if not wr:
        return {"success": False, "message": "Request not found"}
    if wr.status != "pending":
        return {"success": False, "message": "Already processed"}

    wr.status = "done"
    wr.resolved_at = datetime.utcnow()

    if wr.item_id:
        it = await session.execute(
            select(InventoryItem).where(InventoryItem.id == wr.item_id)
        )
        inv_item = it.scalar_one_or_none()
        if inv_item:
            await session.delete(inv_item)

    await session.commit()
    return {"success": True}
