#!/usr/bin/env python3
"""
Professional FastAPI Server.
Full REST API for the casino mini app.
"""

import os
import hashlib
import hmac
import json
import urllib.parse
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from db.engine import async_session, init_db
from api import (
    get_or_create_user, get_wallet, update_wallet,
    claim_daily, open_case, spin_roulette, spin_slots,
    breed_items, list_item, buy_item,
    get_inventory, get_user_stats, get_achievements,
    get_leaderboard, send_gift
)
import config
from api.deposits import (
    get_deposit_info, check_deposits,
    request_withdrawal, list_withdrawals, complete_withdrawal,
)

app = FastAPI(title="Casino Bot API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_init_data(init_data: str) -> bool:
    """Verify Telegram Mini App init_data."""
    try:
        parsed = urllib.parse.parse_qs(init_data)
        if "hash" not in parsed:
            return False

        received_hash = parsed["hash"][0]
        data_check = sorted([f"{k}={v[0]}" for k, v in parsed.items() if k != "hash"])

        secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, "\n".join(data_check).encode(), hashlib.sha256).hexdigest()

        return computed_hash == received_hash
    except Exception:
        return False


def extract_user(init_data: str) -> dict:
    """Extract user data from init_data."""
    try:
        parsed = urllib.parse.parse_qs(init_data)
        user_json = parsed.get("user", ["{}"])[0]
        return json.loads(user_json)
    except Exception:
        return {}


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/")
async def root():
    with open("miniapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


# ============================================================
# USER ENDPOINTS
# ============================================================

@app.post("/api/user")
async def api_user(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    user_data = data

    if not user_id:
        # fallback: try telegram init_data
        init_data = data.get("init_data", "")
        user_data = extract_user(init_data)
        user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="No user identified")

    async with async_session() as session:
        user, is_new = await get_or_create_user(
            session, user_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            language_code=user_data.get("language_code"),
            referral_code=data.get("referral_code")
        )
        wallet = await get_wallet(session, user.id)

        return {
            "id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "coins": wallet.coins if wallet else 0,
            "level": user.level,
            "xp": user.xp,
            "xp_to_next": config.LEADERBOARD.get("xp_to_next", 1000),
            "referral_code": user.referral_code,
            "daily_streak": user.daily_streak,
            "is_new": is_new
        }


@app.post("/api/stats")
async def api_stats(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    async with async_session() as session:
        stats = await get_user_stats(session, user_id)
        if not stats:
            raise HTTPException(status_code=404, detail="User not found")
        return stats


# ============================================================
# DAILY REWARD
# ============================================================

@app.post("/api/daily")
async def api_daily(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    async with async_session() as session:
        success, coins, streak, next_claim = await claim_daily(session, user_id)

        if success:
            wallet = await get_wallet(session, user_id)
            return {"success": True, "coins": coins, "streak": streak, "balance": wallet.coins}
        else:
            return {"success": False, "next_claim": next_claim}


# ============================================================
# CASE SYSTEM
# ============================================================

@app.get("/api/cases")
async def api_cases():
    """Get all available cases."""
    return {
        "cases": [
            {
                "id": case_id,
                "name": case["name"],
                "price": case["price"],
                "emoji": case["emoji"],
                "color": case["color"],
                "items": len(case["items"])
            }
            for case_id, case in config.CASES.items()
        ]
    }


@app.post("/api/case/open")
async def api_case_open(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    case_id = data.get("case_id")

    if not user_id or not case_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with async_session() as session:
        result = await open_case(session, user_id, case_id)
        return result


@app.post("/api/case/open/bulk")
async def api_case_open_bulk(request: Request):
    """Open multiple cases at once."""
    data = await request.json()
    user_id = data.get("user_id")
    case_id = data.get("case_id")
    count = min(data.get("count", 1), 10)  # Max 10 at once

    if not user_id or not case_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with async_session() as session:
        results = []
        for _ in range(count):
            result = await open_case(session, user_id, case_id)
            results.append(result)
            if not result.get("success"):
                break

        return {"results": results}


# ============================================================
# ROULETTE
# ============================================================

@app.post("/api/roulette/spin")
async def api_roulette_spin(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    bet = data.get("bet", 50)
    color = data.get("color", "red")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    async with async_session() as session:
        result = await spin_roulette(session, user_id, bet, color)
        return result


@app.get("/api/roulette/config")
async def api_roulette_config():
    return config.ROULETTE


# ============================================================
# SLOTS
# ============================================================

@app.post("/api/slots/spin")
async def api_slots_spin(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    bet = data.get("bet", 25)

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    async with async_session() as session:
        result = await spin_slots(session, user_id, bet)
        return result


@app.get("/api/slots/config")
async def api_slots_config():
    return config.SLOTS


# ============================================================
# BREEDING
# ============================================================

@app.post("/api/breed")
async def api_breed(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    item1_id = data.get("item1_id")
    item2_id = data.get("item2_id")

    if not user_id or not item1_id or not item2_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with async_session() as session:
        result = await breed_items(session, user_id, item1_id, item2_id)
        return result


# ============================================================
# INVENTORY
# ============================================================

@app.post("/api/inventory")
async def api_inventory(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    rarity = data.get("rarity")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    async with async_session() as session:
        items = await get_inventory(session, user_id, rarity)
        return {
            "items": [
                {
                    "id": item.id,
                    "name": item.item_name,
                    "emoji": item.item_emoji,
                    "rarity": item.rarity,
                    "value": item.value,
                    "is_tradeable": item.is_tradeable,
                    "is_locked": item.is_locked,
                    "breed_count": item.breed_count,
                    "acquired_at": item.acquired_at.isoformat() if item.acquired_at else None
                }
                for item in items
            ]
        }


# ============================================================
# MARKETPLACE
# ============================================================

@app.get("/api/marketplace")
async def api_marketplace(
    rarity: str = Query(None),
    sort: str = Query("newest"),
    page: int = Query(1)
):
    """Get marketplace listings."""
    from db import MarketplaceListing, InventoryItem
    from sqlalchemy import select, desc

    async with async_session() as session:
        query = (
            select(MarketplaceListing, InventoryItem)
            .join(InventoryItem, MarketplaceListing.item_id == InventoryItem.id)
            .where(MarketplaceListing.is_active == True)
        )

        if rarity:
            query = query.where(InventoryItem.rarity == rarity)

        if sort == "cheapest":
            query = query.order_by(MarketplaceListing.price)
        elif sort == "expensive":
            query = query.order_by(desc(MarketplaceListing.price))
        else:
            query = query.order_by(desc(MarketplaceListing.created_at))

        query = query.limit(20).offset((page - 1) * 20)

        result = await session.execute(query)
        listings = result.all()

        return {
            "listings": [
                {
                    "id": listing.id,
                    "price": listing.price,
                    "item": {
                        "name": item.item_name,
                        "emoji": item.item_emoji,
                        "rarity": item.rarity,
                        "value": item.value
                    },
                    "created_at": listing.created_at.isoformat()
                }
                for listing, item in listings
            ]
        }


@app.post("/api/marketplace/list")
async def api_marketplace_list(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    price = data.get("price")

    if not user_id or not item_id or not price:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with async_session() as session:
        result = await list_item(session, user_id, item_id, price)
        return result


@app.post("/api/marketplace/buy")
async def api_marketplace_buy(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    listing_id = data.get("listing_id")

    if not user_id or not listing_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with async_session() as session:
        result = await buy_item(session, user_id, listing_id)
        return result


# ============================================================
# LEADERBOARD
# ============================================================

@app.get("/api/leaderboard")
async def api_leaderboard(category: str = Query("coins")):
    async with async_session() as session:
        leaderboard = await get_leaderboard(session, category)
        return {"leaderboard": leaderboard, "category": category}


# ============================================================
# ACHIEVEMENTS
# ============================================================

@app.post("/api/achievements")
async def api_achievements(request: Request):
    data = await request.json()
    user_id = data.get("user_id")

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    async with async_session() as session:
        achievements = await get_achievements(session, user_id)
        return {"achievements": achievements}


# ============================================================
# GIFTS
# ============================================================

@app.post("/api/gift")
async def api_gift(request: Request):
    data = await request.json()
    sender_id = data.get("sender_id")
    receiver_id = data.get("receiver_id")
    item_id = data.get("item_id")
    message = data.get("message", "")

    if not sender_id or not receiver_id or not item_id:
        raise HTTPException(status_code=400, detail="Missing parameters")

    async with async_session() as session:
        result = await send_gift(session, sender_id, receiver_id, item_id, message)
        return result


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@app.post("/api/admin/balance")
async def api_admin_balance(request: Request):
    data = await request.json()
    admin_id = data.get("admin_id")
    target_username = data.get("username")

    if admin_id not in config.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from sqlalchemy import select, or_
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                or_(User.username == target_username, User.telegram_id == target_username)
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            return {"error": "User not found"}

        wallet = await get_wallet(session, user.id)
        return {
            "user": user.username or user.first_name,
            "coins": wallet.coins if wallet else 0
        }


@app.post("/api/admin/give")
async def api_admin_give(request: Request):
    data = await request.json()
    admin_id = data.get("admin_id")
    target_username = data.get("username")
    amount = data.get("amount", 0)

    if admin_id not in config.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Unauthorized")

    from sqlalchemy import select, or_
    async with async_session() as session:
        result = await session.execute(
            select(User).where(
                or_(User.username == target_username, User.telegram_id == target_username)
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            return {"error": "User not found"}

        await update_wallet(session, user.id, amount, "admin_grant", f"Admin grant: +{amount}")
        wallet = await get_wallet(session, user.id)

        return {"success": True, "new_balance": wallet.coins}



# ============================================================
# DEPOSITS (TON)
# ============================================================

@app.post("/api/deposit/info")
async def api_deposit_info(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    async with async_session() as session:
        return await get_deposit_info(session, user_id)


@app.post("/api/deposit/check")
async def api_deposit_check(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    async with async_session() as session:
        result = await check_deposits(session, user_id)
        return result


# ============================================================
# WITHDRAWALS
# ============================================================

@app.post("/api/withdraw")
async def api_withdraw(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Missing parameters")
    async with async_session() as session:
        return await request_withdrawal(session, user_id, item_id)


@app.get("/api/withdrawals")
async def api_withdrawals():
    async with async_session() as session:
        return {"requests": await list_withdrawals(session)}


@app.post("/api/withdrawals/complete")
async def api_withdrawals_complete(request: Request):
    data = await request.json()
    admin_id = data.get("admin_id")
    request_id = data.get("request_id")
    if admin_id not in config.ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Unauthorized")
    async with async_session() as session:
        return await complete_withdrawal(session, request_id)

# Mount static files
app.mount("/static", StaticFiles(directory="miniapp/static"), name="static")
