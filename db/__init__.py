#!/usr/bin/env python3
"""
Professional Database Models.
Full schema for casino bot with NFT items, breeding, marketplace.
"""

from datetime import datetime, timedelta
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User account with profile and stats."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    language_code = Column(String(10), default="en")

    # Referral system
    referral_code = Column(String(10), unique=True, nullable=False)
    referred_by = Column(Integer, nullable=True)
    total_referrals = Column(Integer, default=0)
    referral_earnings = Column(Integer, default=0)

    # Stats
    total_spent = Column(Integer, default=0)
    total_earned = Column(Integer, default=0)
    cases_opened = Column(Integer, default=0)
    roulette_spins = Column(Integer, default=0)
    slots_spins = Column(Integer, default=0)
    items_bred = Column(Integer, default=0)

    # Daily rewards
    last_daily = Column(DateTime, nullable=True)
    daily_streak = Column(Integer, default=0)
    last_free_spin = Column(DateTime, nullable=True)
    bonus_spins = Column(Integer, default=0)

    # VIP / Level
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    is_vip = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    inventory = relationship("InventoryItem", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    breeding_history = relationship("BreedingLog", back_populates="user")
    marketplace_listings = relationship("MarketplaceListing", back_populates="seller")


class Wallet(Base):
    """User wallet with coin balance."""
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    coins = Column(Integer, default=0)
    total_deposited = Column(Float, default=0.0)
    total_withdrawn = Column(Float, default=0.0)

    user = relationship("User", back_populates="wallet")


class InventoryItem(Base):
    """NFT-style item in user's inventory."""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_name = Column(String(100), nullable=False)
    item_emoji = Column(String(10), nullable=True)
    rarity = Column(String(20), nullable=False, index=True)
    value = Column(Integer, default=0)
    case_id = Column(String(50), nullable=True)
    is_tradeable = Column(Boolean, default=True)
    is_locked = Column(Boolean, default=False)
    extra_data = Column(JSON, nullable=True)  # Custom properties

    # Breeding
    breed_count = Column(Integer, default=0)
    last_breed = Column(DateTime, nullable=True)

    # Timestamps
    acquired_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="inventory")
    marketplace_listing = relationship("MarketplaceListing", back_populates="item", uselist=False)

    __table_args__ = (
        Index("idx_inventory_user_rarity", "user_id", "rarity"),
    )


class Transaction(Base):
    """All financial transactions."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)  # deposit, withdraw, purchase, win, daily, referral, breed, trade
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")

    __table_args__ = (
        Index("idx_transactions_user_type", "user_id", "type"),
    )


class SpinResult(Base):
    """Roulette and slots history."""
    __tablename__ = "spins"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    game_type = Column(String(20), nullable=False)  # roulette, slots
    bet = Column(Integer, nullable=False)
    result = Column(JSON, nullable=False)  # {"color": "red"} or {"symbols": ["🍒","🍒","🍒"]}
    multiplier = Column(Float, nullable=False)
    won = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class BreedingLog(Base):
    """Breeding history."""
    __tablename__ = "breeding_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item1_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    item2_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    result_item_id = Column(Integer, ForeignKey("inventory.id"), nullable=True)
    success = Column(Boolean, default=False)
    cost = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="breeding_history")


class MarketplaceListing(Base):
    """Marketplace listings for trading items."""
    __tablename__ = "marketplace"

    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("inventory.id"), unique=True, nullable=False)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    price = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    sold_at = Column(DateTime, nullable=True)
    buyer_id = Column(Integer, nullable=True)

    item = relationship("InventoryItem", back_populates="marketplace_listing")
    seller = relationship("User", back_populates="marketplace_listings")


class Achievement(Base):
    """User achievements."""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(String(50), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),
    )


class Leaderboard(Base):
    """Cached leaderboard data."""
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True)
    category = Column(String(30), nullable=False)  # coins, items, referrals
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value = Column(Integer, nullable=False)
    rank = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Gift(Base):
    """Gifts sent between users."""
    __tablename__ = "gifts"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory.id"), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DailyClaim(Base):
    """Track daily claims for streak management."""
    __tablename__ = "daily_claims"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    claimed_at = Column(DateTime, default=datetime.utcnow)
    streak_day = Column(Integer, nullable=False)
    coins_claimed = Column(Integer, nullable=False)

    __table_args__ = (
        Index("idx_daily_user_date", "user_id", "claimed_at"),
    )
