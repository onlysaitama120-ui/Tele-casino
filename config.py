#!/usr/bin/env python3
"""
Casino Bot - Professional Configuration.
All game settings, payments, and admin config.
"""

# ============================================================
# BOT CONFIGURATION
# ============================================================

BOT_TOKEN = "8944289947:AAEDO9RcrZWr-KdOFy5ypC7E3H43CUtuRMY"  # Get from @BotFather
BOT_USERNAME = "MyCasinoBotx_bot"
WEBAPP_URL = "https://yourdomain.com"  # Deployed mini app URL
ADMIN_IDS = [123456789]  # Your Telegram user ID(s)

# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = "sqlite+aiosqlite:///db/casino.db"

# ============================================================
# PAYMENT CONFIGURATION
# ============================================================

# Telegram Stars (built-in Telegram payments)
STARS_ENABLED = True

# Crypto payments (NOWPayments)
NOWPAYMENTS_API_KEY = "YOUR_KEY"
NOWPAYMENTS_IPN_SECRET = "YOUR_SECRET"

# ============================================================
# GAME ECONOMY
# ============================================================

INITIAL_COINS = 1000          # New user bonus
DAILY_REWARD = 100            # Daily login reward
DAILY_STREAK_BONUS = 50       # Extra per consecutive day (max 500)
MAX_STREAK = 10               # Days for max streak bonus
REFERRAL_BONUS = 200          # Coins per referral
REFERRAL_PREMIUM = 500        # Coins if referral deposits

# ============================================================
# CASE SYSTEM
# ============================================================

CASES = {
    "bronze": {
        "name": "Bronze Case",
        "price": 100,
        "emoji": "📦",
        "color": "#CD7F32",
        "items": [
            {"name": "Bronze Coin", "rarity": "common", "chance": 50, "value": 15, "emoji": "🪙"},
            {"name": "Copper Ring", "rarity": "common", "chance": 25, "value": 30, "emoji": "💍"},
            {"name": "Iron Dagger", "rarity": "uncommon", "chance": 15, "value": 75, "emoji": "🗡️"},
            {"name": "Silver Pendant", "rarity": "rare", "chance": 8, "value": 200, "emoji": "📿"},
            {"name": "Golden Token", "rarity": "epic", "chance": 2, "value": 500, "emoji": "🏅"},
        ]
    },
    "silver": {
        "name": "Silver Case",
        "price": 500,
        "emoji": "🎁",
        "color": "#C0C0C0",
        "items": [
            {"name": "Silver Bar", "rarity": "common", "chance": 30, "value": 60, "emoji": "🪙"},
            {"name": "Crystal Shard", "rarity": "uncommon", "chance": 30, "value": 150, "emoji": "💠"},
            {"name": "Ruby Gem", "rarity": "rare", "chance": 25, "value": 500, "emoji": "💎"},
            {"name": "Emerald Crown", "rarity": "epic", "chance": 12, "value": 1500, "emoji": "👑"},
            {"name": "Dragon Scale", "rarity": "legendary", "chance": 3, "value": 5000, "emoji": "🐉"},
        ]
    },
    "gold": {
        "name": "Gold Case",
        "price": 2000,
        "emoji": "🏆",
        "color": "#FFD700",
        "items": [
            {"name": "Gold Ingot", "rarity": "uncommon", "chance": 30, "value": 250, "emoji": "🪙"},
            {"name": "Sapphire Ring", "rarity": "rare", "chance": 30, "value": 800, "emoji": "💍"},
            {"name": "Phoenix Feather", "rarity": "epic", "chance": 25, "value": 3000, "emoji": "🔥"},
            {"name": "Unicorn Horn", "rarity": "legendary", "chance": 12, "value": 10000, "emoji": "🦄"},
            {"name": "Cosmic Artifact", "rarity": "mythic", "chance": 3, "value": 50000, "emoji": "🌌"},
        ]
    },
    "diamond": {
        "name": "Diamond Case",
        "price": 10000,
        "emoji": "💎",
        "color": "#B9F2FF",
        "items": [
            {"name": "Diamond Shard", "rarity": "rare", "chance": 35, "value": 1000, "emoji": "💎"},
            {"name": "Obsidian Blade", "rarity": "epic", "chance": 30, "value": 4000, "emoji": "⚔️"},
            {"name": "Leviathan Eye", "rarity": "legendary", "chance": 25, "value": 15000, "emoji": "👁️"},
            {"name": "Void Walker", "rarity": "mythic", "chance": 8, "value": 75000, "emoji": "🌀"},
            {"name": "Eternal Core", "rarity": "divine", "chance": 2, "value": 200000, "emoji": "✨"},
        ]
    },
}

# ============================================================
# ROULETTE
# ============================================================

ROULETTE = {
    "min_bet": 50,
    "max_bet": 50000,
    "colors": {
        "red": {"multiplier": 2, "chance": 48.6, "emoji": "🔴"},
        "black": {"multiplier": 2, "chance": 48.6, "emoji": "⚫"},
        "green": {"multiplier": 14, "chance": 2.8, "emoji": "🟢"},
    }
}

# ============================================================
# SLOTS MACHINE
# ============================================================

SLOTS = {
    "min_bet": 25,
    "max_bet": 10000,
    "symbols": ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "🎰"],
    "payouts": {
        "🍒🍒🍒": 5,
        "🍋🍋🍋": 8,
        "🍊🍊🍊": 10,
        "🍇🍇🍇": 15,
        "💎💎💎": 25,
        "7️⃣7️⃣7️⃣": 50,
        "🎰🎰🎰": 100,
        "🍒🍒": 2,
        "💎💎": 4,
        "7️⃣7️⃣": 8,
    }
}

# ============================================================
# BREEDING SYSTEM
# ============================================================

BREEDING = {
    "enabled": True,
    "cost": 500,
    "cooldown_hours": 24,
    "combos": {
        ("common", "common"): {"result": "uncommon", "chance": 70},
        ("uncommon", "uncommon"): {"result": "rare", "chance": 50},
        ("rare", "rare"): {"result": "epic", "chance": 35},
        ("epic", "epic"): {"result": "legendary", "chance": 20},
        ("legendary", "legendary"): {"result": "mythic", "chance": 10},
        ("mythic", "mythic"): {"result": "divine", "chance": 5},
    }
}

# ============================================================
# LEADERBOARD
# ============================================================

LEADERBOARD = {
    "update_interval": 300,  # seconds
    "top_n": 10,
}

# ============================================================
# RARITY COLORS (for UI)
# ============================================================

RARITY_COLORS = {
    "common": "#888888",
    "uncommon": "#44ff44",
    "rare": "#4488ff",
    "epic": "#aa44ff",
    "legendary": "#ffaa00",
    "mythic": "#ff4444",
    "divine": "#ffd700",
}

RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "divine"]
