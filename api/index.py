#!/usr/bin/env python3
"""
Vercel Serverless - Casino Bot
Single file deployment, no import issues.
"""

import os
import json
import hashlib
import hmac
import urllib.parse
import random
import aiohttp
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, select, func, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8944289947:AAEDO9RcrZWr-KdOFy5ypC7E3H43CUtuRMY")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "MyCasinoBotx_bot")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://tele-casino.vercel.app")
ADMIN_IDS = [123456789]

INITIAL_COINS = 1000
DAILY_REWARD = 100
REFERRAL_BONUS = 200

CASES = {
    "bronze": {
        "name": "Bronze Case", "price": 100, "emoji": "📦",
        "items": [
            {"name": "Bronze Coin", "rarity": "common", "chance": 50, "value": 15, "emoji": "🪙"},
            {"name": "Copper Ring", "rarity": "common", "chance": 25, "value": 30, "emoji": "💍"},
            {"name": "Silver Pendant", "rarity": "rare", "chance": 15, "value": 200, "emoji": "📿"},
            {"name": "Golden Token", "rarity": "epic", "chance": 10, "value": 500, "emoji": "🏅"},
        ]
    },
    "silver": {
        "name": "Silver Case", "price": 500, "emoji": "🎁",
        "items": [
            {"name": "Silver Bar", "rarity": "common", "chance": 30, "value": 60, "emoji": "🪙"},
            {"name": "Ruby Gem", "rarity": "rare", "chance": 30, "value": 500, "emoji": "💎"},
            {"name": "Dragon Scale", "rarity": "epic", "chance": 25, "value": 2000, "emoji": "🐉"},
            {"name": "Unicorn Horn", "rarity": "legendary", "chance": 15, "value": 10000, "emoji": "🦄"},
        ]
    },
    "gold": {
        "name": "Gold Case", "price": 2000, "emoji": "🏆",
        "items": [
            {"name": "Gold Ingot", "rarity": "uncommon", "chance": 30, "value": 250, "emoji": "🪙"},
            {"name": "Phoenix Feather", "rarity": "epic", "chance": 30, "value": 3000, "emoji": "🔥"},
            {"name": "Void Walker", "rarity": "legendary", "chance": 25, "value": 15000, "emoji": "🌀"},
            {"name": "Eternal Core", "rarity": "mythic", "chance": 15, "value": 50000, "emoji": "✨"},
        ]
    },
}

# ============================================================
# DATABASE
# ============================================================

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    referral_code = Column(String, unique=True, nullable=False)
    referred_by = Column(Integer, nullable=True)
    total_referrals = Column(Integer, default=0)
    cases_opened = Column(Integer, default=0)
    roulette_spins = Column(Integer, default=0)
    last_daily = Column(DateTime, nullable=True)
    daily_streak = Column(Integer, default=0)
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Wallet(Base):
    __tablename__ = "wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    coins = Column(Integer, default=0)

class InventoryItem(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    item_name = Column(String, nullable=False)
    item_emoji = Column(String, nullable=True)
    rarity = Column(String, nullable=False)
    value = Column(Integer, default=0)
    case_id = Column(String, nullable=True)
    acquired_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    type = Column(String, nullable=False)
    amount = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
DB_URL = "sqlite:///tmp/casino.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================
# GAME LOGIC
# ============================================================

def generate_referral_code():
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:8].upper()

def get_or_create_user(db, telegram_id, username=None, first_name=None, referral_code=None):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        return user, False

    new_code = generate_referral_code()
    referred_by = None
    if referral_code:
        ref_user = db.query(User).filter(User.referral_code == referral_code).first()
        if ref_user:
            referred_by = ref_user.telegram_id
            ref_user.total_referrals += 1

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        referral_code=new_code,
        referred_by=referred_by
    )
    db.add(user)
    db.flush()

    wallet = Wallet(user_id=user.id, coins=INITIAL_COINS)
    db.add(wallet)

    if referred_by:
        ref_wallet = db.query(Wallet).filter(Wallet.user_id == ref_user.id).first()
        if ref_wallet:
            ref_wallet.coins += REFERRAL_BONUS

    db.commit()
    return user, True

def get_wallet(db, user_id):
    return db.query(Wallet).filter(Wallet.user_id == user_id).first()

def claim_daily(db, user_id):
    user = db.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        return False, 0, 0, None

    now = datetime.utcnow()
    if user.last_daily and (now - user.last_daily) < timedelta(hours=23, minutes=50):
        remaining = timedelta(hours=24) - (now - user.last_daily)
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        return False, 0, 0, f"{hours}h {minutes}m"

    if user.last_daily and (now - user.last_daily) < timedelta(hours=48):
        user.daily_streak = min(user.daily_streak + 1, 10)
    else:
        user.daily_streak = 1

    streak_bonus = min(user.daily_streak * 50, 500)
    total_reward = DAILY_REWARD + streak_bonus

    user.last_daily = now
    wallet = get_wallet(db, user.id)
    if wallet:
        wallet.coins += total_reward
        tx = Transaction(user_id=user.id, type="daily", amount=total_reward, description=f"Daily reward (streak: {user.daily_streak})")
        db.add(tx)
    db.commit()
    return True, total_reward, user.daily_streak, None

def open_case(db, user_id, case_id):
    case = CASES.get(case_id)
    if not case:
        return {"success": False, "message": "Invalid case"}

    wallet = get_wallet(db, user_id)
    if not wallet or wallet.coins < case["price"]:
        return {"success": False, "message": "Not enough coins"}

    wallet.coins -= case["price"]

    roll = random.randint(1, 100)
    cumulative = 0
    item = case["items"][0]
    for i in case["items"]:
        cumulative += i["chance"]
        if roll <= cumulative:
            item = i
            break

    inv_item = InventoryItem(
        user_id=user_id,
        item_name=item["name"],
        item_emoji=item["emoji"],
        rarity=item["rarity"],
        value=item["value"],
        case_id=case_id
    )
    db.add(inv_item)

    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.cases_opened += 1

    tx = Transaction(user_id=user_id, type="case_open", amount=-case["price"], description=f"Opened {case['name']}")
    db.add(tx)
    db.commit()

    return {
        "success": True,
        "item": {"name": item["name"], "emoji": item["emoji"], "rarity": item["rarity"], "value": item["value"]},
        "balance": wallet.coins
    }

def spin_roulette(db, user_id, bet, color):
    if color not in ["red", "black", "green"]:
        return {"success": False, "message": "Invalid color"}

    wallet = get_wallet(db, user_id)
    if not wallet or wallet.coins < bet:
        return {"success": False, "message": "Not enough coins"}

    wallet.coins -= bet

    roll = random.random() * 100
    if roll < 2.8:
        result = "green"
    elif roll < 51.4:
        result = "red"
    else:
        result = "black"

    multipliers = {"red": 2, "black": 2, "green": 14}
    won = int(bet * multipliers[result]) if result == color else 0

    if won > 0:
        wallet.coins += won
        tx = Transaction(user_id=user_id, type="win", amount=won, description=f"Roulette win ({result})")
        db.add(tx)
    else:
        tx = Transaction(user_id=user_id, type="bet", amount=-bet, description=f"Roulette bet ({color})")
        db.add(tx)

    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.roulette_spins += 1

    db.commit()
    return {"success": True, "result": result, "won": won, "balance": wallet.coins}

def spin_slots(db, user_id, bet):
    symbols = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "🎰"]
    result = [random.choice(symbols) for _ in range(3)]

    payouts = {
        "🍒🍒🍒": 5, "🍋🍋🍋": 8, "🍊🍊🍊": 10, "🍇🍇🍇": 15,
        "💎💎💎": 25, "7️⃣7️⃣7️⃣": 50, "🎰🎰🎰": 100,
        "🍒🍒": 2, "💎💎": 4, "7️⃣7️⃣": 8,
    }

    result_str = "".join(result)
    multiplier = payouts.get(result_str, 0)
    if multiplier == 0 and result[0] == result[1]:
        multiplier = payouts.get(result[0] * 2, 0)

    wallet = get_wallet(db, user_id)
    if not wallet or wallet.coins < bet:
        return {"success": False, "message": "Not enough coins"}

    wallet.coins -= bet
    won = int(bet * multiplier)

    if won > 0:
        wallet.coins += won
        tx = Transaction(user_id=user_id, type="win", amount=won, description=f"Slots win ({result_str})")
        db.add(tx)
    else:
        tx = Transaction(user_id=user_id, type="bet", amount=-bet, description=f"Slots spin ({result_str})")
        db.add(tx)

    user = db.query(User).filter(User.telegram_id == user_id).first()
    if user:
        user.roulette_spins += 1

    db.commit()
    return {"success": True, "symbols": result, "multiplier": multiplier, "won": won, "balance": wallet.coins}

# ============================================================
# FASTAPI APP
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Casino Bot", lifespan=lifespan)

# ============================================================
# MINI APP
# ============================================================

@app.get("/")
async def root():
    with open("miniapp/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ============================================================
# WEBHOOK
# ============================================================

async def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            return await resp.json()

def main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎰 Play Casino", "web_app": {"url": WEBAPP_URL}}],
            [{"text": "🎁 Daily", "callback_data": "daily"}, {"text": "📦 Inventory", "callback_data": "inventory"}],
            [{"text": "📊 Stats", "callback_data": "stats"}, {"text": "👥 Referral", "callback_data": "referral"}],
        ]
    }

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = data.get("message") or data.get("callback_query", {}).get("message", {})
    callback_data = data.get("callback_query", {}).get("data")
    from_user = message.get("from", {})
    chat_id = message.get("chat", {}).get("id", from_user.get("id", 0))
    user_id = from_user.get("id", 0)
    text = message.get("text", "")

    if not user_id:
        return {"ok": True}

    db = SessionLocal()
    try:
        if text.startswith("/start"):
            args = text.split()
            ref_code = args[1][4:] if len(args) > 1 and args[1].startswith("ref_") else None
            user, is_new = get_or_create_user(db, user_id, from_user.get("username"), from_user.get("first_name"), ref_code)
            wallet = get_wallet(db, user.id)

            if is_new:
                msg = (
                    f"🎰 *Welcome to Casino Bot!* 🎰/n/n"
                    f"Hey {from_user.get('first_name', 'Player')}! 👋/n/n"
                    f"🎁 You received *{INITIAL_COINS} coins* to start!/n/n"
                    f"*🎮 Games:*/n"
                    f"📦 Case Opening/n"
                    f"🎡 Roulette/n"
                    f"🎰 Slots/n/n"
                    f"Tap *Play Casino* to begin! 🚀"
                )
            else:
                msg = (
                    f"👋 Welcome back, *{from_user.get('first_name', 'Player')}*!/n/n"
                    f"💰 Balance: *{wallet.coins if wallet else 0} coins*/n/n"
                    f"Tap *Play Casino* to continue!"
                )
            await send_message(chat_id, msg, main_keyboard())

        elif text.startswith("/daily") or callback_data == "daily":
            success, coins, streak, next_claim = claim_daily(db, user_id)
            if success:
                wallet = get_wallet(db, user_id)
                await send_message(chat_id, f"🎁 *Daily Claimed!*/n/nYou received *{coins} coins*!/n🔥 Streak: *{streak} days*/n💰 Balance: *{wallet.coins} coins*")
            else:
                await send_message(chat_id, f"⏰ *Already Claimed!*/n/nNext daily in: *{next_claim}*")

        elif text.startswith("/stats") or callback_data == "stats":
            user = db.query(User).filter(User.telegram_id == user_id).first()
            wallet = get_wallet(db, user.id) if user else None
            items = db.query(InventoryItem).filter(InventoryItem.user_id == user.id).count() if user else 0
            if user:
                await send_message(chat_id,
                    f"📊 *Your Stats*/n/n"
                    f"💰 Coins: *{wallet.coins if wallet else 0}*/n"
                    f"📊 Level: *{user.level}*/n"
                    f"📦 Items: *{items}*/n"
                    f"📦 Cases: *{user.cases_opened}*/n"
                    f"🎡 Spins: *{user.roulette_spins}*"
                )

        elif text.startswith("/inventory") or callback_data == "inventory":
            await send_message(chat_id, "📦 *Open inventory in mini app!*",
                {"inline_keyboard": [[{"text": "📦 Open Inventory", "web_app": {"url": WEBAPP_URL}}]]})

        elif text.startswith("/referral") or callback_data == "referral":
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.referral_code}"
                await send_message(chat_id, f"👥 *Your Referral Link:*/n/n`{link}`/n/nShare and earn *{REFERRAL_BONUS} coins* per friend!")

        elif text.startswith("/help"):
            await send_message(chat_id,
                "❓ *Help*/n/n/start - Start/n/daily - Claim reward/n/inventory - Items/n/stats - Stats/n/referral - Referral link/n/help - This message"
            )

    finally:
        db.close()

    if callback_query_id := data.get("callback_query", {}).get("id"):
        async with aiohttp.ClientSession() as session:
            await session.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_query_id})

    return {"ok": True}

# ============================================================
# GAME API
# ============================================================

@app.post("/api/user")
async def api_user(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    if not user_id:
        return {"error": "Missing user_id"}
    db = SessionLocal()
    try:
        user, is_new = get_or_create_user(db, user_id)
        wallet = get_wallet(db, user.id)
        return {"id": user.telegram_id, "username": user.username, "first_name": user.first_name, "coins": wallet.coins if wallet else 0, "level": user.level, "referral_code": user.referral_code}
    finally:
        db.close()

@app.post("/api/daily")
async def api_daily(request: Request):
    data = await request.json()
    db = SessionLocal()
    try:
        success, coins, streak, next_claim = claim_daily(db, data.get("user_id"))
        if success:
            wallet = get_wallet(db, data.get("user_id"))
            return {"success": True, "coins": coins, "streak": streak, "balance": wallet.coins}
        return {"success": False, "next_claim": next_claim}
    finally:
        db.close()

@app.post("/api/case/open")
async def api_case_open(request: Request):
    data = await request.json()
    db = SessionLocal()
    try:
        return open_case(db, data.get("user_id"), data.get("case_id"))
    finally:
        db.close()

@app.post("/api/roulette/spin")
async def api_roulette_spin(request: Request):
    data = await request.json()
    db = SessionLocal()
    try:
        return spin_roulette(db, data.get("user_id"), data.get("bet", 50), data.get("color", "red"))
    finally:
        db.close()

@app.post("/api/slots/spin")
async def api_slots_spin(request: Request):
    data = await request.json()
    db = SessionLocal()
    try:
        return spin_slots(db, data.get("user_id"), data.get("bet", 25))
    finally:
        db.close()

@app.post("/api/inventory")
async def api_inventory(request: Request):
    data = await request.json()
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).filter(InventoryItem.user_id == data.get("user_id")).order_by(InventoryItem.acquired_at.desc()).all()
        return {"items": [{"id": i.id, "name": i.item_name, "emoji": i.item_emoji, "rarity": i.rarity, "value": i.value} for i in items]}
    finally:
        db.close()

@app.post("/api/stats")
async def api_stats(request: Request):
    data = await request.json()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == data.get("user_id")).first()
        wallet = get_wallet(db, user.id) if user else None
        items = db.query(InventoryItem).filter(InventoryItem.user_id == user.id).count() if user else 0
        return {"coins": wallet.coins if wallet else 0, "level": user.level if user else 1, "items": items, "cases": user.cases_opened if user else 0, "spins": user.roulette_spins if user else 0}
    finally:
        db.close()

@app.get("/api/cases")
async def api_cases():
    return {"cases": [{"id": k, "name": v["name"], "price": v["price"], "emoji": v["emoji"]} for k, v in CASES.items()]}

# Vercel handler
from mangum import Mangum
handler = Mangum(app)
