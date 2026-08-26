#!/usr/bin/env python3
"""
Professional Game Engine.
Cases, roulette, slots, breeding, marketplace, achievements.
"""

import random
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession
from db import (
    User, Wallet, InventoryItem, Transaction, SpinResult,
    BreedingLog, MarketplaceListing, Achievement, DailyClaim
)
import config


# ============================================================
# USER MANAGEMENT
# ============================================================

def generate_referral_code():
    """Generate unique 8-char referral code."""
    return hashlib.md5(str(random.random()).encode()).hexdigest()[:8].upper()


async def get_or_create_user(session: AsyncSession, telegram_id: int, **kwargs):
    """Get or create user with wallet."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        user.last_active = datetime.utcnow()
        if kwargs.get("username"):
            user.username = kwargs["username"]
        if kwargs.get("first_name"):
            user.first_name = kwargs["first_name"]
        await session.commit()
        return user, False

    # Create user
    referral_code = generate_referral_code()
    referred_by = None

    if kwargs.get("referral_code"):
        ref_result = await session.execute(
            select(User).where(User.referral_code == kwargs["referral_code"])
        )
        ref_user = ref_result.scalar_one_or_none()
        if ref_user:
            referred_by = ref_user.telegram_id
            ref_user.total_referrals += 1

    user = User(
        telegram_id=telegram_id,
        username=kwargs.get("username"),
        first_name=kwargs.get("first_name"),
        last_name=kwargs.get("last_name"),
        language_code=kwargs.get("language_code", "en"),
        referral_code=referral_code,
        referred_by=referred_by
    )
    session.add(user)
    await session.flush()

    # Create wallet
    wallet = Wallet(user_id=user.telegram_id, coins=config.INITIAL_COINS)
    session.add(wallet)

    # Log initial coins
    tx = Transaction(
        user_id=user.telegram_id,
        type="bonus",
        amount=config.INITIAL_COINS,
        balance_after=config.INITIAL_COINS,
        description="Welcome bonus"
    )
    session.add(tx)

    # Referral bonus
    if referred_by:
        ref_wallet = await get_wallet(session, ref_user.telegram_id)
        if ref_wallet:
            ref_wallet.coins += config.REFERRAL_BONUS
            ref_tx = Transaction(
                user_id=ref_user.id,
                type="referral",
                amount=config.REFERRAL_BONUS,
                description=f"Referral bonus: @{kwargs.get('username', 'user')}"
            )
            session.add(ref_tx)

    await session.commit()
    return user, True


async def get_wallet(session: AsyncSession, user_id: int):
    """Get user's wallet."""
    result = await session.execute(select(Wallet).where(Wallet.user_id == user_id))
    return result.scalar_one_or_none()


async def update_wallet(session: AsyncSession, user_id: int, amount: int, tx_type: str, description: str = ""):
    """Update wallet balance and log transaction."""
    wallet = await get_wallet(session, user_id)
    if not wallet:
        return None

    wallet.coins += amount
    tx = Transaction(
        user_id=user_id,
        type=tx_type,
        amount=amount,
        balance_after=wallet.coins,
        description=description
    )
    session.add(tx)
    await session.commit()
    return wallet


# ============================================================
# DAILY REWARDS
# ============================================================

async def claim_daily(session: AsyncSession, user_id: int):
    """Claim daily reward with streak system."""
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False, 0, 0, None

    now = datetime.utcnow()

    # Check cooldown
    if user.last_daily:
        time_since = now - user.last_daily
        if time_since < timedelta(hours=23, minutes=50):
            remaining = timedelta(hours=24) - time_since
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            return False, 0, 0, f"{hours}h {minutes}m"

    # Check streak
    if user.last_daily and (now - user.last_daily) < timedelta(hours=48):
        user.daily_streak = min(user.daily_streak + 1, config.MAX_STREAK)
    else:
        user.daily_streak = 1

    # Calculate reward
    streak_bonus = min(user.daily_streak * config.DAILY_STREAK_BONUS, config.MAX_STREAK * config.DAILY_STREAK_BONUS)
    total_reward = config.DAILY_REWARD + streak_bonus

    # Update
    user.last_daily = now
    wallet = await get_wallet(session, user_id)
    if wallet:
        wallet.coins += total_reward

        # Log transaction
        tx = Transaction(
            user_id=user_id,
            type="daily",
            amount=total_reward,
            balance_after=wallet.coins,
            description=f"Daily reward (streak: {user.daily_streak})"
        )
        session.add(tx)

        # Log daily claim
        daily_log = DailyClaim(
            user_id=user_id,
            streak_day=user.daily_streak,
            coins_claimed=total_reward
        )
        session.add(daily_log)

        # Update user stats
        user.total_earned += total_reward

    await session.commit()
    return True, total_reward, user.daily_streak, None


# ============================================================
# CASE SYSTEM
# ============================================================

async def open_case(session: AsyncSession, user_id: int, case_id: str):
    """Open a case with animated results."""
    case = config.CASES.get(case_id)
    if not case:
        return {"success": False, "message": "Invalid case"}

    wallet = await get_wallet(session, user_id)
    if not wallet or wallet.coins < case["price"]:
        return {"success": False, "message": "Not enough coins", "balance": wallet.coins if wallet else 0}

    # Deduct coins
    wallet.coins -= case["price"]
    tx = Transaction(
        user_id=user_id,
        type="case_open",
        amount=-case["price"],
        balance_after=wallet.coins,
        description=f"Opened {case['name']}"
    )
    session.add(tx)

    # Roll item
    item = roll_case_item(case)

    # Create inventory item
    inv_item = InventoryItem(
        user_id=user_id,
        item_name=item["name"],
        item_emoji=item["emoji"],
        rarity=item["rarity"],
        value=item["value"],
        case_id=case_id
    )
    session.add(inv_item)

    # Update user stats
    result_user = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result_user.scalar_one_or_none()
    if user:
        user.cases_opened += 1
        user.total_spent += case["price"]
        user.xp += case["price"] // 100
        check_level_up(user)

    # Check achievements
    await check_achievements(session, user_id, "case_opened", user.cases_opened if user else 0)

    await session.commit()

    return {
        "success": True,
        "item": {
            "name": item["name"],
            "emoji": item["emoji"],
            "rarity": item["rarity"],
            "value": item["value"]
        },
        "balance": wallet.coins
    }


def roll_case_item(case):
    """Roll for item with weighted probabilities."""
    roll = random.randint(1, 10000) / 100  # 0.01 precision
    cumulative = 0
    for item in case["items"]:
        cumulative += item["chance"]
        if roll <= cumulative:
            return item
    return case["items"][0]


# ============================================================
# ROULETTE
# ============================================================

# ============================================================
# BREEDING SYSTEM
# ============================================================

async def breed_items(session: AsyncSession, user_id: int, item1_id: int, item2_id: int):
    """Breed two items to create a new one."""
    if not config.BREEDING["enabled"]:
        return {"success": False, "message": "Breeding disabled"}

    # Get items
    result1 = await session.execute(
        select(InventoryItem).where(InventoryItem.id == item1_id, InventoryItem.user_id == user_id)
    )
    item1 = result1.scalar_one_or_none()

    result2 = await session.execute(
        select(InventoryItem).where(InventoryItem.id == item2_id, InventoryItem.user_id == user_id)
    )
    item2 = result2.scalar_one_or_none()

    if not item1 or not item2:
        return {"success": False, "message": "Items not found"}

    if item1.id == item2.id:
        return {"success": False, "message": "Cannot breed same item"}

    if item1.is_locked or item2.is_locked:
        return {"success": False, "message": "Cannot breed locked items"}

    # Check cooldown
    now = datetime.utcnow()
    if item1.last_breed and (now - item1.last_breed) < timedelta(hours=config.BREEDING["cooldown_hours"]):
        remaining = timedelta(hours=config.BREEDING["cooldown_hours"]) - (now - item1.last_breed)
        hours = int(remaining.total_seconds() // 3600)
        return {"success": False, "message": f"Item on cooldown ({hours}h left)"}

    # Check cost
    wallet = await get_wallet(session, user_id)
    if not wallet or wallet.coins < config.BREEDING["cost"]:
        return {"success": False, "message": "Not enough coins"}

    # Deduct cost
    wallet.coins -= config.BREEDING["cost"]

    # Get breeding combo
    combo_key = tuple(sorted([item1.rarity, item2.rarity]))
    combo = config.BREEDING["combos"].get(combo_key)

    if not combo:
        # Fallback: 50% chance to upgrade, 50% same rarity
        combo = {"result": item1.rarity, "chance": 50}

    # Roll for success
    success = random.randint(1, 100) <= combo["chance"]

    if success:
        # Create new item
        new_rarity = combo["result"]
        new_value = int((item1.value + item2.value) * 1.5)

        new_item = InventoryItem(
            user_id=user_id,
            item_name=f"Bred {new_rarity.title()}",
            item_emoji=get_rarity_emoji(new_rarity),
            rarity=new_rarity,
            value=new_value,
            is_tradeable=True,
            breed_count=0
        )
        session.add(new_item)

        # SECURITY: consume ingredients (prevents infinite gem printing)
        await session.delete(item1)
        await session.delete(item2)

        # Log breeding
        breed_log = BreedingLog(
            user_id=user_id,
            item1_id=item1.id,
            item2_id=item2.id,
            result_item_id=new_item.id,
            success=True,
            cost=config.BREEDING["cost"]
        )
        session.add(breed_log)

        # Update stats
        result_user = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result_user.scalar_one_or_none()
        if user:
            user.items_bred += 1

        await session.commit()

        return {
            "success": True,
            "bred": True,
            "item": {
                "name": new_item.item_name,
                "emoji": new_item.item_emoji,
                "rarity": new_rarity,
                "value": new_value
            },
            "balance": wallet.coins
        }
    else:
        # Failed - items survive but cost is lost
        item1.last_breed = now
        item2.last_breed = now

        breed_log = BreedingLog(
            user_id=user_id,
            item1_id=item1.id,
            item2_id=item2.id,
            result_item_id=None,
            success=False,
            cost=config.BREEDING["cost"]
        )
        session.add(breed_log)

        await session.commit()

        return {
            "success": True,
            "bred": False,
            "message": "Breeding failed! Items survived but coins were lost.",
            "balance": wallet.coins
        }


def get_rarity_emoji(rarity):
    """Get emoji for rarity."""
    emojis = {
        "common": "🪙", "uncommon": "💍", "rare": "💎",
        "epic": "🔮", "legendary": "👑", "mythic": "🌋", "divine": "✨"
    }
    return emojis.get(rarity, "🎁")


# ============================================================

async def seed_marketplace(session):
    """Auto-populate marketplace with 25 demo listings on fresh DB."""
    import random
    from sqlalchemy import func
    try:
        count = await session.execute(select(func.count()).select_from(MarketplaceListing))
        if count.scalar() and count.scalar() > 0:
            return
    except Exception:
        pass  # table might not exist yet

    pool = []
    for case in config.BOXES.values():
        for item in case.get('items', []):
            pool.append(item)
    if not pool:
        return

    rarity_mult = {
        "common": 1.2, "uncommon": 2.5, "rare": 5, "epic": 15,
        "legendary": 50, "mythic": 200, "divine": 1000
    }

    for _ in range(25):
        pick = random.choice(pool)
        val = pick.get('value', 100)
        m = rarity_mult.get(pick.get('rarity', 'common'), 1)
        price = max(int(val * m * random.uniform(0.7, 1.3)), 10)
        inv = InventoryItem(
            user_id=0,
            item_name=pick['name'],
            item_emoji=pick.get('emoji', '🎁'),
            rarity=pick.get('rarity', 'common'),
            value=val,
        )
        session.add(inv)
        await session.flush()
        session.add(MarketplaceListing(
            item_id=inv.id, seller_id=0,
            price=price, is_active=True,
        ))
    await session.commit()
    print("[+] Marketplace seeded with 25 demo listings")

# MARKETPLACE
# ============================================================

async def list_item(session: AsyncSession, user_id: int, item_id: int, price: int):
    """List item on marketplace."""
    result = await session.execute(
        select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.user_id == user_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        return {"success": False, "message": "Item not found"}

    if not item.is_tradeable:
        return {"success": False, "message": "Item is not tradeable"}

    if item.is_locked:
        return {"success": False, "message": "Item is locked"}

    try:
        price = int(price)
    except Exception:
        return {"success": False, "message": "Invalid price"}
    if price <= 0 or price > 10000000:
        return {"success": False, "message": "Price must be 1-10,000,000"}

    try:
        price = int(price)
    except Exception:
        return {"success": False, "message": "Invalid price"}
    if price <= 0 or price > 10000000:
        return {"success": False, "message": "Price must be 1-10,000,000"}

    # Check if already listed
    existing = await session.execute(
        select(MarketplaceListing).where(MarketplaceListing.item_id == item_id)
    )
    if existing.scalar_one_or_none():
        return {"success": False, "message": "Item already listed"}

    listing = MarketplaceListing(
        item_id=item_id,
        seller_id=user_id,
        price=price
    )
    session.add(listing)
    await session.commit()

    return {"success": True, "message": f"Listed for {price} coins"}


async def buy_item(session: AsyncSession, user_id: int, listing_id: int):
    """Buy item from marketplace."""
    result = await session.execute(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id, MarketplaceListing.is_active == True)
    )
    listing = result.scalar_one_or_none()

    if not listing:
        return {"success": False, "message": "Listing not found"}

    if listing.seller_id == user_id:
        return {"success": False, "message": "Cannot buy your own item"}

    if listing.price <= 0:
        return {"success": False, "message": "Invalid listing"}

    if listing.price <= 0:
        return {"success": False, "message": "Invalid listing"}

    # Check buyer wallet
    buyer_wallet = await get_wallet(session, user_id)
    if not buyer_wallet or buyer_wallet.coins < listing.price:
        return {"success": False, "message": "Not enough coins"}

    # Get seller wallet
    seller_wallet = await get_wallet(session, listing.seller_id)
    if not seller_wallet:
        return {"success": False, "message": "Seller not found"}

    # Transfer item
    item_result = await session.execute(
        select(InventoryItem).where(InventoryItem.id == listing.item_id)
    )
    item = item_result.scalar_one_or_none()

    if not item:
        return {"success": False, "message": "Item not found"}

    # Transfer coins
    buyer_wallet.coins -= listing.price
    seller_wallet.coins += listing.price

    # Transfer item ownership
    item.user_id = user_id

    # Update listing
    listing.is_active = False
    listing.sold_at = datetime.utcnow()
    listing.buyer_id = user_id

    # Log transactions
    buyer_tx = Transaction(
        user_id=user_id,
        type="marketplace_buy",
        amount=-listing.price,
        balance_after=buyer_wallet.coins,
        description=f"Bought {item.item_name} from marketplace"
    )
    session.add(buyer_tx)

    seller_tx = Transaction(
        user_id=listing.seller_id,
        type="marketplace_sell",
        amount=listing.price,
        balance_after=seller_wallet.coins,
        description=f"Sold {item.item_name} on marketplace"
    )
    session.add(seller_tx)

    await session.commit()

    return {"success": True, "balance": buyer_wallet.coins}


# ============================================================
# INVENTORY & STATS
# ============================================================

async def get_inventory(session: AsyncSession, user_id: int, rarity_filter: str = None):
    """Get user's inventory with optional rarity filter."""
    query = select(InventoryItem).where(InventoryItem.user_id == user_id)

    if rarity_filter:
        query = query.where(InventoryItem.rarity == rarity_filter)

    query = query.order_by(InventoryItem.acquired_at.desc())
    result = await session.execute(query)
    return result.scalars().all()


async def get_user_stats(session: AsyncSession, user_id: int):
    """Get comprehensive user stats."""
    from sqlalchemy import func

    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None

    wallet = await get_wallet(session, user_id)

    # Item counts by rarity
    rarity_counts = {}
    for rarity in config.RARITY_ORDER:
        count_result = await session.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.user_id == user.id,
                InventoryItem.rarity == rarity
            )
        )
        rarity_counts[rarity] = count_result.scalar() or 0

    total_items = sum(rarity_counts.values())

    # Marketplace stats
    active_listings = await session.execute(
        select(func.count(MarketplaceListing.id)).where(
            MarketplaceListing.seller_id == user.id,
            MarketplaceListing.is_active == True
        )
    )

    return {
        "user_id": user.telegram_id,
        "username": user.username,
        "coins": wallet.coins if wallet else 0,
        "level": user.level,
        "xp": user.xp,
        "xp_to_next": get_xp_to_next_level(user.level),
        "total_items": total_items,
        "rarity_counts": rarity_counts,
        "cases_opened": user.cases_opened,
        "roulette_spins": user.roulette_spins,
        "slots_spins": user.slots_spins,
        "items_bred": user.items_bred,
        "total_referrals": user.total_referrals,
        "daily_streak": user.daily_streak,
        "active_listings": active_listings.scalar() or 0,
        "is_vip": user.is_vip,
    }


def get_xp_to_next_level(current_level):
    """Calculate XP needed for next level."""
    return current_level * 100 + 500


def check_level_up(user):
    """Check and apply level ups."""
    xp_needed = get_xp_to_next_level(user.level)
    while user.xp >= xp_needed:
        user.xp -= xp_needed
        user.level += 1
        xp_needed = get_xp_to_next_level(user.level)


# ============================================================
# ACHIEVEMENTS
# ============================================================

ACHIEVEMENTS = {
    "first_case": {"name": "First Case", "description": "Open your first case", "emoji": "📦"},
    "case_10": {"name": "Collector", "description": "Open 10 cases", "emoji": "🎯"},
    "case_100": {"name": "Veteran", "description": "Open 100 cases", "emoji": "🏆"},
    "case_1000": {"name": "Legend", "description": "Open 1000 cases", "emoji": "👑"},
    "win_1000": {"name": "Big Winner", "description": "Win 1000+ coins in one spin", "emoji": "🎰"},
    "win_10000": {"name": "Jackpot", "description": "Win 10,000+ coins in one spin", "emoji": "💎"},
    "referral_5": {"name": "Influencer", "description": "Refer 5 friends", "emoji": "👥"},
    "referral_25": {"name": "Networker", "description": "Refer 25 friends", "emoji": "🌐"},
    "streak_7": {"name": "Dedicated", "description": "7-day daily streak", "emoji": "🔥"},
    "streak_30": {"name": "Devoted", "description": "30-day daily streak", "emoji": "💪"},
    "level_10": {"name": "Rising Star", "description": "Reach level 10", "emoji": "⭐"},
    "level_25": {"name": "Pro", "description": "Reach level 25", "emoji": "🌟"},
    "level_50": {"name": "Master", "description": "Reach level 50", "emoji": "💫"},
    "breeeder_10": {"name": "Breeder", "description": "Breed 10 items", "emoji": "🧬"},
    "trader_10": {"name": "Trader", "description": "Complete 10 marketplace trades", "emoji": "💰"},
}


async def check_achievements(session: AsyncSession, user_id: int, achievement_type: str, value: int):
    """Check and unlock achievements."""
    achievement_checks = {
        "case_opened": [
            (1, "first_case"), (10, "case_10"), (100, "case_100"), (1000, "case_1000")
        ],
        "win_amount": [
            (1000, "win_1000"), (10000, "win_10000")
        ],
        "referrals": [
            (5, "referral_5"), (25, "referral_25")
        ],
        "streak": [
            (7, "streak_7"), (30, "streak_30")
        ],
        "level": [
            (10, "level_10"), (25, "level_25"), (50, "level_50")
        ],
    }

    checks = achievement_checks.get(achievement_type, [])
    for threshold, achievement_id in checks:
        if value >= threshold:
            # Check if already unlocked
            existing = await session.execute(
                select(Achievement).where(
                    Achievement.user_id == user_id,
                    Achievement.achievement_id == achievement_id
                )
            )
            if not existing.scalar_one_or_none():
                achievement = Achievement(
                    user_id=user_id,
                    achievement_id=achievement_id
                )
                session.add(achievement)
                await session.commit()


async def get_achievements(session: AsyncSession, user_id: int):
    """Get user's unlocked achievements."""
    result = await session.execute(
        select(Achievement).where(Achievement.user_id == user_id)
    )
    achievements = result.scalars().all()
    return [
        {
            "id": a.achievement_id,
            "name": ACHIEVEMENTS.get(a.achievement_id, {}).get("name", "Unknown"),
            "description": ACHIEVEMENTS.get(a.achievement_id, {}).get("description", ""),
            "emoji": ACHIEVEMENTS.get(a.achievement_id, {}).get("emoji", "🏅"),
            "unlocked_at": a.unlocked_at.isoformat()
        }
        for a in achievements
    ]


# ============================================================
# LEADERBOARD
# ============================================================

async def get_leaderboard(session: AsyncSession, category: str = "coins"):
    """Get leaderboard for specified category."""
    if category == "coins":
        query = (
            select(User.telegram_id, User.username, User.first_name, Wallet.coins)
            .join(Wallet, User.id == Wallet.user_id)
            .order_by(desc(Wallet.coins))
            .limit(config.LEADERBOARD["top_n"])
        )
        result = await session.execute(query)
        return [
            {"rank": i+1, "user_id": row[0], "username": row[1] or row[2], "value": row[3]}
            for i, row in enumerate(result.all())
        ]
    elif category == "items":
        from sqlalchemy import func
        query = (
            select(User.telegram_id, User.username, User.first_name, func.count(InventoryItem.id))
            .join(InventoryItem, User.id == InventoryItem.user_id)
            .group_by(User.id)
            .order_by(desc(func.count(InventoryItem.id)))
            .limit(config.LEADERBOARD["top_n"])
        )
        result = await session.execute(query)
        return [
            {"rank": i+1, "user_id": row[0], "username": row[1] or row[2], "value": row[3]}
            for i, row in enumerate(result.all())
        ]
    return []


# ============================================================
# GIFT SYSTEM
# ============================================================

async def send_gift(session: AsyncSession, sender_id: int, receiver_id: int, item_id: int, message: str = ""):
    """Send item as gift to another user."""
    # Get sender's item
    result = await session.execute(
        select(InventoryItem).where(InventoryItem.id == item_id, InventoryItem.user_id == sender_id)
    )
    item = result.scalar_one_or_none()

    if not item:
        return {"success": False, "message": "Item not found"}

    if not item.is_tradeable:
        return {"success": False, "message": "Item is not tradeable"}

    # Transfer item
    item.user_id = receiver_id

    # Log gift
    from db import Gift
    gift = Gift(
        sender_id=sender_id,
        receiver_id=receiver_id,
        item_id=item.id,
        message=message
    )
    session.add(gift)
    await session.commit()

    return {"success": True, "message": "Gift sent!"}
