#!/usr/bin/env python3
"""
GIFT RUSH - NFT Collectible Game Configuration.
Set secrets via environment variables (never hardcode).
"""

import os

# ============================================================
# BOT
# ============================================================

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "MyCasinoBotx_bot")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://tele-casino.onrender.com")
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "0").split(",") if x.strip()]

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///db/casino.db")

# ============================================================
# TON DEPOSITS  (real money entry point)
# ============================================================

TON_WALLET = os.environ.get("TON_WALLET", "UQYourMerchantTonWalletAddressHere")
TONCENTER_API = "https://toncenter.com/api/v2"
GEMS_PER_TON = 1000          # 1 TON = 1,000 gems
DEPOSIT_MIN = 0.1            # minimum TON credited

# ============================================================
# ECONOMY
# ============================================================

INITIAL_GEMS = 300
DAILY_REWARD = 50
DAILY_STREAK_BONUS = 25
MAX_STREAK = 10
REFERRAL_BONUS = 150
MARKET_FEE_PCT = 5           # platform cut on trades

# ============================================================
# MYSTERY BOXES  (chance = %, total 100 per box)
# ============================================================

BOXES = {
    "starter": {
        "name": "Starter Box", "price": 250, "emoji": "🎁", "color": "#7c5cff",
        "items": [
            {"name": "Sticker Pack",      "rarity": "common",    "chance": 55, "value": 80,    "emoji": "🩷"},
            {"name": "Mini Plush",        "rarity": "common",    "chance": 25, "value": 160,   "emoji": "🧸"},
            {"name": "Neon Signet",       "rarity": "rare",      "chance": 14, "value": 450,   "emoji": "💍"},
            {"name": "Astral Shard",      "rarity": "epic",      "chance": 5,  "value": 1400,  "emoji": "🔮"},
            {"name": "Golden Heart",      "rarity": "legendary", "chance": 1,  "value": 6000,  "emoji": "💛"},
        ]
    },
    "pro": {
        "name": "Pro Box", "price": 1200, "emoji": "🎀", "color": "#38bdf8",
        "items": [
            {"name": "Candy Cane",        "rarity": "common",    "chance": 40, "value": 350,   "emoji": "🍬"},
            {"name": "Snow Globe",        "rarity": "uncommon",  "chance": 30, "value": 700,   "emoji": "🌐"},
            {"name": "Signet Ring",       "rarity": "rare",      "chance": 20, "value": 2000,  "emoji": "💎"},
            {"name": "Eternal Rose",      "rarity": "epic",      "chance": 8,  "value": 6500,  "emoji": "🌹"},
            {"name": "Durov Cap",         "rarity": "legendary", "chance": 2,  "value": 30000, "emoji": "🧢"},
        ]
    },
    "elite": {
        "name": "Elite Box", "price": 6000, "emoji": "🗃️", "color": "#f472b6",
        "items": [
            {"name": "Crystal Ball",      "rarity": "uncommon",  "chance": 35, "value": 1800,  "emoji": "🔮"},
            {"name": "Eternal Rose",      "rarity": "rare",      "chance": 30, "value": 4000,  "emoji": "🌹"},
            {"name": "Plush Pepe Mini",   "rarity": "epic",      "chance": 22, "value": 12000, "emoji": "🐸"},
            {"name": "Swiss Watch",       "rarity": "legendary", "chance": 10, "value": 45000, "emoji": "⌚"},
            {"name": "Plush Pepe (NFT)",  "rarity": "mythic",    "chance": 3,  "value": 250000,"emoji": "🐸👑"},
        ]
    },
    "legend": {
        "name": "Legend Box", "price": 25000, "emoji": "🏆", "color": "#ffd54a",
        "items": [
            {"name": "Swiss Watch",       "rarity": "epic",      "chance": 40, "value": 20000, "emoji": "⌚"},
            {"name": "Plush Pepe (NFT)",  "rarity": "legendary", "chance": 40, "value": 90000, "emoji": "🐸"},
            {"name": "Durov Cap (NFT)",   "rarity": "mythic",    "chance": 15, "value": 350000,"emoji": "🧢"},
            {"name": "Precious Peach",    "rarity": "divine",    "chance": 5,  "value": 1000000,"emoji": "🍑"},
        ]
    },
}

# Rarity order + colors
RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "divine"]
RARITY_COLORS = {
    "common": "#8b93b5", "uncommon": "#44dd77", "rare": "#4488ff",
    "epic": "#aa44ff", "legendary": "#ffaa00", "mythic": "#ff4444",
    "divine": "#ffd700",
}

# ============================================================
# FUSION (breeding)
# ============================================================

FUSION = {
    "enabled": True, "cost": 300, "cooldown_hours": 24,
    "combos": {
        ("common", "common"):       {"result": "uncommon",  "chance": 70},
        ("uncommon", "uncommon"):   {"result": "rare",      "chance": 50},
        ("rare", "rare"):           {"result": "epic",      "chance": 35},
        ("epic", "epic"):           {"result": "legendary", "chance": 20},
        ("legendary", "legendary"): {"result": "mythic",    "chance": 10},
        ("mythic", "mythic"):       {"result": "divine",    "chance": 5},
    }
}

LEADERBOARD = {"top_n": 10}

# compat alias for case engine
CASES = BOXES
