#!/usr/bin/env python3
"""
Vercel Serverless Function - handles webhooks + mini app API.
Single entry point for everything.
"""

import os
import json
import hashlib
import hmac
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler

# Import our app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import models and game logic
from db import Base, User, Wallet, InventoryItem, Transaction
from api import (
    get_or_create_user, get_wallet, claim_daily,
    open_case, spin_roulette, spin_slots,
    get_inventory, get_user_stats, get_achievements,
    get_leaderboard, breed_items, list_item, buy_item
)
import config

# Create FastAPI app
app = FastAPI(title="Casino Bot")

# Database
DATABASE_URL = "sqlite+aiosqlite:///tmp/casino.db"
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@app.on_event("startup")
async def startup():
    """Create tables on first request."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ============================================================
# MINI APP (served as HTML)
# ============================================================

@app.get("/")
async def root():
    """Serve the mini app."""
    with open("miniapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/static/{path:path}")
async def static_files(path: str):
    """Serve static files."""
    from fastapi.responses import FileResponse
    file_path = f"miniapp/static/{path}"
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return HTMLResponse(status_code=404)


# ============================================================
# TELEGRAM WEBHOOK
# ============================================================

def verify_telegram_webhook(update: dict) -> bool:
    """Verify update is from Telegram."""
    # In production, verify with secret_token
    return True


def extract_user_id(data: dict) -> int:
    """Extract user ID from various formats."""
    if "message" in data:
        return data["message"].get("from", {}).get("id", 0)
    elif "callback_query" in data:
        return data["callback_query"].get("from", {}).get("id", 0)
    return 0


async def send_telegram_message(chat_id: int, text: str, reply_markup: dict = None):
    """Send message via Telegram Bot API."""
    import aiohttp

    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.json()


def get_main_keyboard():
    """Main menu keyboard."""
    return {
        "inline_keyboard": [
            [{"text": "🎰 Play Casino", "web_app": {"url": config.WEBAPP_URL}}],
            [{"text": "🎁 Daily", "callback_data": "daily"}, {"text": "📦 Inventory", "callback_data": "inventory"}],
            [{"text": "🎡 Roulette", "callback_data": "roulette"}, {"text": "🎰 Slots", "callback_data": "slots"}],
            [{"text": "👥 Referral", "callback_data": "referral"}, {"text": "🏆 Leaderboard", "callback_data": "leaderboard"}],
            [{"text": "📊 Stats", "callback_data": "stats"}, {"text": "🏅 Achievements", "callback_data": "achievements"}],
        ]
    }


@app.post("/webhook")
async def webhook(request: Request):
    """Handle Telegram updates."""
    data = await request.json()

    if not verify_telegram_webhook(data):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # Extract message/callback
    message = data.get("message") or data.get("callback_query", {}).get("message", {})
    callback_data = data.get("callback_query", {}).get("data")
    from_user = message.get("from", {})
    chat_id = message.get("chat", {}).get("id", from_user.get("id", 0))
    user_id = from_user.get("id", 0)
    text = message.get("text", "")

    if not user_id:
        return JSONResponse({"ok": True})

    # Handle /start
    if text.startswith("/start"):
        args = text.split()
        referral_code = args[1][4:] if len(args) > 1 and args[1].startswith("ref_") else None

        async with async_session() as session:
            user, is_new = await get_or_create_user(
                session, user_id,
                username=from_user.get("username"),
                first_name=from_user.get("first_name"),
                referral_code=referral_code
            )
            wallet = await get_wallet(session, user.id)

        if is_new:
            text = (
                f"🎰 *Welcome to Casino Bot!* 🎰/n/n"
                f"Hey {from_user.get('first_name', 'Player')}! 👋/n/n"
                f"🎁 You received *{config.INITIAL_COINS} coins* to start!/n/n"
                f"*🎮 Games Available:*/n"
                f"📦 Case Opening/n"
                f"🎡 Roulette/n"
                f"🎰 Slots/n"
                f"🧬 Breeding/n"
                f"🛒 Marketplace/n/n"
                f"Tap *Play Casino* to begin! 🚀"
            )
        else:
            text = (
                f"👋 Welcome back, *{from_user.get('first_name', 'Player')}*!/n/n"
                f"💰 Balance: *{wallet.coins if wallet else 0} coins*/n/n"
                f"Tap *Play Casino* to continue!"
            )

        await send_telegram_message(chat_id, text, get_main_keyboard())

    # Handle /daily
    elif text.startswith("/daily") or callback_data == "daily":
        async with async_session() as session:
            success, coins, streak, next_claim = await claim_daily(session, user_id)

            if success:
                wallet = await get_wallet(session, user_id)
                await send_telegram_message(chat_id,
                    f"🎁 *Daily Claimed!*/n/n"
                    f"You received *{coins} coins*!/n"
                    f"🔥 Streak: *{streak} days*/n"
                    f"💰 Balance: *{wallet.coins} coins*"
                )
            else:
                await send_telegram_message(chat_id,
                    f"⏰ *Already Claimed!*/n/nNext daily in: *{next_claim}*"
                )

    # Handle /stats
    elif text.startswith("/stats") or callback_data == "stats":
        async with async_session() as session:
            stats = await get_user_stats(session, user_id)
            if stats:
                await send_telegram_message(chat_id,
                    f"📊 *Your Stats*/n/n"
                    f"💰 Coins: *{stats['coins']}*/n"
                    f"📊 Level: *{stats['level']}*/n"
                    f"📦 Items: *{stats['total_items']}*/n"
                    f"📦 Cases: *{stats['cases_opened']}*/n"
                    f"🎡 Roulette: *{stats['roulette_spins']}*/n"
                    f"🎰 Slots: *{stats['slots_spins']}*"
                )

    # Handle /inventory
    elif text.startswith("/inventory") or callback_data == "inventory":
        await send_telegram_message(chat_id,
            "📦 *Open your inventory in the mini app!*",
            {"inline_keyboard": [[{"text": "📦 Open Inventory", "web_app": {"url": config.WEBAPP_URL}}]]}
        )

    # Handle /referral
    elif text.startswith("/referral") or callback_data == "referral":
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()

            if user:
                ref_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"
                await send_telegram_message(chat_id,
                    f"👥 *Your Referral Link:*/n/n`{ref_link}`/n/n"
                    f"Share it and earn *{config.REFERRAL_BONUS} coins* per friend!"
                )

    # Handle /leaderboard
    elif text.startswith("/leaderboard") or callback_data == "leaderboard":
        async with async_session() as session:
            board = await get_leaderboard(session, "coins")
            text = "🏆 *Top Players*/n/n"
            medals = ["🥇", "🥈", "🥉"]
            for i, entry in enumerate(board[:10]):
                medal = medals[i] if i < 3 else f"{i+1}."
                text += f"{medal} *{entry['username']}* - {entry['value']} coins/n"
            await send_telegram_message(chat_id, text)

    # Handle /help
    elif text.startswith("/help"):
        await send_telegram_message(chat_id,
            "❓ *Help*/n/n"
            "/start - Start bot/n"
            "/daily - Claim reward/n"
            "/inventory - View items/n"
            "/stats - Your stats/n"
            "/referral - Get referral link/n"
            "/leaderboard - Top players/n"
            "/help - This message"
        )

    # Answer callback query
    if callback_query_id := data.get("callback_query", {}).get("id"):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            await session.post(
                f"https://api.telegram.org/bot{config.BOT_TOKEN}/answerCallbackQuery",
                json={"callback_query_id": callback_query_id}
            )

    return JSONResponse({"ok": True})


# ============================================================
# GAME API (for mini app)
# ============================================================

@app.post("/api/user")
async def api_user(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        return JSONResponse({"error": "Missing user_id"}, status_code=400)

    async with async_session() as session:
        user, is_new = await get_or_create_user(session, user_id)
        wallet = await get_wallet(session, user.id)
        return {
            "id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "coins": wallet.coins if wallet else 0,
            "level": user.level,
            "referral_code": user.referral_code,
            "daily_streak": user.daily_streak,
        }


@app.post("/api/daily")
async def api_daily(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    async with async_session() as session:
        success, coins, streak, next_claim = await claim_daily(session, user_id)
        if success:
            wallet = await get_wallet(session, user_id)
            return {"success": True, "coins": coins, "streak": streak, "balance": wallet.coins}
        return {"success": False, "next_claim": next_claim}


@app.post("/api/case/open")
async def api_case_open(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    case_id = data.get("case_id")
    async with async_session() as session:
        result = await open_case(session, user_id, case_id)
        return result


@app.post("/api/roulette/spin")
async def api_roulette_spin(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    bet = data.get("bet", 50)
    color = data.get("color", "red")
    async with async_session() as session:
        result = await spin_roulette(session, user_id, bet, color)
        return result


@app.post("/api/slots/spin")
async def api_slots_spin(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    bet = data.get("bet", 25)
    async with async_session() as session:
        result = await spin_slots(session, user_id, bet)
        return result


@app.post("/api/inventory")
async def api_inventory(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    async with async_session() as session:
        items = await get_inventory(session, user_id)
        return {"items": [{"id": i.id, "name": i.item_name, "emoji": i.item_emoji, "rarity": i.rarity, "value": i.value} for i in items]}


@app.post("/api/stats")
async def api_stats(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    async with async_session() as session:
        stats = await get_user_stats(session, user_id)
        return stats or {}


@app.post("/api/breed")
async def api_breed(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    item1_id = data.get("item1_id")
    item2_id = data.get("item2_id")
    async with async_session() as session:
        result = await breed_items(session, user_id, item1_id, item2_id)
        return result


@app.get("/api/leaderboard")
async def api_leaderboard(category: str = "coins"):
    async with async_session() as session:
        board = await get_leaderboard(session, category)
        return {"leaderboard": board}


@app.get("/api/cases")
async def api_cases():
    return {"cases": [{"id": k, "name": v["name"], "price": v["price"], "emoji": v["emoji"]} for k, v in config.CASES.items()]}


# For Vercel
from mangum import Mangum
handler = Mangum(app)
