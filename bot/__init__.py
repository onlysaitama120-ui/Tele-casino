#!/usr/bin/env python3
"""
Professional Telegram Bot Handlers.
Full command set with inline keyboards and game integration.
"""

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, CallbackQuery
)
import config


def get_main_keyboard():
    """Main game keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🎰 Play Casino",
            web_app=WebAppInfo(url=config.WEBAPP_URL)
        )],
        [
            InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
            InlineKeyboardButton(text="📦 Inventory", callback_data="inventory"),
        ],
        [
            InlineKeyboardButton(text="🎡 Roulette", callback_data="roulette"),
            InlineKeyboardButton(text="🎰 Slots", callback_data="slots"),
        ],
        [
            InlineKeyboardButton(text="🧬 Breed", callback_data="breed"),
            InlineKeyboardButton(text="🛒 Market", callback_data="market"),
        ],
        [
            InlineKeyboardButton(text="👥 Referral", callback_data="referral"),
            InlineKeyboardButton(text="🏆 Leaderboard", callback_data="leaderboard"),
        ],
        [
            InlineKeyboardButton(text="📊 Stats", callback_data="stats"),
            InlineKeyboardButton(text="🏅 Achievements", callback_data="achievements"),
        ],
    ])


def get_back_keyboard():
    """Back button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Back to Menu", callback_data="menu")]
    ])


# ============================================================
# COMMANDS
# ============================================================

async def cmd_start(message: types.Message, bot: Bot):
    """Handle /start command."""
    args = message.text.split()
    referral_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        referral_code = args[1][4:]

    from db.engine import async_session
    from api import get_or_create_user, get_wallet

    async with async_session() as session:
        user, is_new = await get_or_create_user(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            referral_code=referral_code
        )
        wallet = await get_wallet(session, user.id)

    if is_new:
        text = (
            f"🎰 **Welcome to Casino Bot!** 🎰\n\n"
            f"Hey {message.from_user.first_name}! 👋\n\n"
            f"🎁 You received **{config.INITIAL_COINS} coins** to start!\n\n"
            f"**🎮 Games Available:**\n"
            f"📦 Case Opening - Win rare NFT items\n"
            f"🎡 Roulette - Multiply your coins\n"
            f"🎰 Slots - Jackpot wins\n"
            f"🧬 Breeding - Create new items\n"
            f"🛒 Marketplace - Trade with others\n\n"
            f"**💰 Earn More:**\n"
            f"🎁 Claim daily rewards\n"
            f"👥 Invite friends for bonuses\n"
            f"🏆 Climb the leaderboards\n\n"
            f"Tap **Play Casino** to begin! 🚀"
        )
    else:
        text = (
            f"👋 Welcome back, **{message.from_user.first_name}**!\n\n"
            f"💰 Balance: **{wallet.coins if wallet else 0} coins**\n"
            f"📊 Level: **{user.level}**\n"
            f"🔥 Daily Streak: **{user.daily_streak}**\n\n"
            f"Tap **Play Casino** to continue playing!"
        )

    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="Markdown")


async def cmd_play(message: types.Message, bot: Bot):
    """Handle /play command."""
    await message.answer(
        "🎮 **Opening Casino...**\n\nTap the button below!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Open Casino", web_app=WebAppInfo(url=config.WEBAPP_URL))]
        ]),
        parse_mode="Markdown"
    )


async def cmd_daily(message: types.Message, bot: Bot):
    """Handle /daily command."""
    from db.engine import async_session
    from api import claim_daily, get_wallet

    async with async_session() as session:
        success, coins, streak, next_claim = await claim_daily(session, message.from_user.id)

        if success:
            wallet = await get_wallet(session, message.from_user.id)
            await message.answer(
                f"🎁 **Daily Claimed!**\n\n"
                f"You received **{coins} coins**!\n"
                f"🔥 Streak: **{streak} days**\n"
                f"💰 Balance: **{wallet.coins} coins**\n\n"
                f"Come back tomorrow for more!",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"⏰ **Already Claimed!**\n\n"
                f"Next daily reward in: **{next_claim}**\n\n"
                f"See you tomorrow! 🎰",
                parse_mode="Markdown"
            )


async def cmd_inventory(message: types.Message, bot: Bot):
    """Handle /inventory command."""
    from db.engine import async_session
    from api import get_inventory, get_user_stats

    async with async_session() as session:
        stats = await get_user_stats(session, message.from_user.id)
        items = await get_inventory(session, message.from_user.id)

        if not items:
            await message.answer(
                "📦 **Your Inventory**\n\n"
                "Empty! Open some cases to get items.",
                parse_mode="Markdown"
            )
            return

        text = f"📦 **Your Inventory** ({len(items)} items)\n\n"

        # Show rarity breakdown
        if stats:
            for rarity, count in stats["rarity_counts"].items():
                if count > 0:
                    emoji = {"common": "🪙", "uncommon": "💍", "rare": "💎", "epic": "🔮", "legendary": "👑", "mythic": "🌋", "divine": "✨"}.get(rarity, "🎁")
                    text += f"{emoji} {rarity.title()}: {count}\n"

        text += "\n**Recent Items:**\n"
        for item in items[:5]:
            text += f"{item.item_emoji} **{item.item_name}** ({item.rarity}) - {item.value} coins\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def cmd_referral(message: types.Message, bot: Bot):
    """Handle /referral command."""
    from db.engine import async_session
    from sqlalchemy import select
    from db import User

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()

        if not user:
            await message.answer("Please /start the bot first!")
            return

        ref_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"

        await message.answer(
            f"👥 **Referral Program**\n\n"
            f"Share your link and earn bonuses!\n\n"
            f"**Your Link:**\n`{ref_link}`\n\n"
            f"**Rewards:**\n"
            f"👥 Each referral: **{config.REFERRAL_BONUS} coins**\n"
            f"💎 If they deposit: **{config.REFERRAL_PREMIUM} coins**\n"
            f"📊 Total referrals: **{user.total_referrals}**\n"
            f"💰 Referral earnings: **{user.referral_earnings} coins**\n\n"
            f"**How it works:**\n"
            f"1. Share the link\n"
            f"2. Friends join using your link\n"
            f"3. You both get bonuses! 🎉",
            parse_mode="Markdown",
            reply_markup=get_back_keyboard()
        )


async def cmd_stats(message: types.Message, bot: Bot):
    """Handle /stats command."""
    from db.engine import async_session
    from api import get_user_stats

    async with async_session() as session:
        stats = await get_user_stats(session, message.from_user.id)

        if not stats:
            await message.answer("Please /start the bot first!")
            return

        text = (
            f"📊 **Your Stats**\n\n"
            f"💰 **Coins:** {stats['coins']}\n"
            f"📊 **Level:** {stats['level']} (XP: {stats['xp']}/{stats['xp_to_next']})\n"
            f"📦 **Items:** {stats['total_items']}\n"
            f"🔥 **Daily Streak:** {stats['daily_streak']}\n\n"
            f"**🎮 Games:**\n"
            f"📦 Cases Opened: {stats['cases_opened']}\n"
            f"🎡 Roulette Spins: {stats['roulette_spins']}\n"
            f"🎰 Slots Spins: {stats['slots_spins']}\n"
            f"🧬 Items Bred: {stats['items_bred']}\n\n"
            f"**👥 Social:**\n"
            f"👥 Referrals: {stats['total_referrals']}\n"
            f"🛒 Active Listings: {stats['active_listings']}\n"
            f"⭐ VIP: {'Yes' if stats['is_vip'] else 'No'}"
        )

        await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def cmd_leaderboard(message: types.Message, bot: Bot):
    """Handle /leaderboard command."""
    from db.engine import async_session
    from api import get_leaderboard

    async with async_session() as session:
        coins_board = await get_leaderboard(session, "coins")
        items_board = await get_leaderboard(session, "items")

        text = "🏆 **Leaderboard**\n\n"

        text += "**💰 Top by Coins:**\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, entry in enumerate(coins_board[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} **{entry['username']}** - {entry['value']} coins\n"

        text += "\n**📦 Top by Items:**\n"
        for i, entry in enumerate(items_board[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} **{entry['username']}** - {entry['value']} items\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def cmd_achievements(message: types.Message, bot: Bot):
    """Handle /achievements command."""
    from db.engine import async_session
    from api import get_achievements, ACHIEVEMENTS

    async with async_session() as session:
        achievements = await get_achievements(session, message.from_user.id)

        text = "🏅 **Achievements**\n\n"

        if achievements:
            text += f"Unlocked: {len(achievements)}/{len(ACHIEVEMENTS)}\n\n"
            for a in achievements:
                text += f"{a['emoji']} **{a['name']}** - {a['description']}\n"
        else:
            text += "No achievements yet. Keep playing to unlock them!\n\n"
            text += "**Available Achievements:**\n"
            for aid, adata in list(ACHIEVEMENTS.items())[:5]:
                text += f"{adata['emoji']} {adata['name']} - {adata['description']}\n"

        await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


async def cmd_help(message: types.Message, bot: Bot):
    """Handle /help command."""
    text = (
        "❓ **Help**\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/play - Open casino\n"
        "/daily - Claim daily reward\n"
        "/inventory - View items\n"
        "/referral - Get referral link\n"
        "/stats - Your statistics\n"
        "/leaderboard - Top players\n"
        "/achievements - Your achievements\n"
        "/help - This message\n\n"
        "**Games:**\n"
        "📦 **Cases** - Open cases for random items\n"
        "🎡 **Roulette** - Bet on colors\n"
        "🎰 **Slots** - Spin the slot machine\n"
        "🧬 **Breed** - Combine items\n"
        "🛒 **Market** - Buy/sell items\n\n"
        "**Support:**\n"
        "Message @your_support_username"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=get_back_keyboard())


# ============================================================
# CALLBACK HANDLERS
# ============================================================

async def callback_daily(callback: CallbackQuery, bot: Bot):
    """Handle daily callback."""
    from db.engine import async_session
    from api import claim_daily, get_wallet

    async with async_session() as session:
        success, coins, streak, next_claim = await claim_daily(session, callback.from_user.id)

        if success:
            wallet = await get_wallet(session, callback.from_user.id)
            await callback.message.edit_text(
                f"🎁 **Daily Claimed!**\n\n"
                f"You received **{coins} coins**!\n"
                f"🔥 Streak: **{streak} days**\n"
                f"💰 Balance: **{wallet.coins} coins**",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
        else:
            await callback.message.edit_text(
                f"⏰ **Already Claimed!**\n\n"
                f"Next daily in: **{next_claim}**",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
    await callback.answer()


async def callback_inventory(callback: CallbackQuery, bot: Bot):
    """Handle inventory callback."""
    await callback.message.edit_text(
        "📦 **Opening Inventory...**\n\nTap the button below!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 Open Inventory", web_app=WebAppInfo(url=config.WEBAPP_URL + "#inventory"))],
            [InlineKeyboardButton(text="← Back", callback_data="menu")]
        ])
    )
    await callback.answer()


async def callback_roulette(callback: CallbackQuery, bot: Bot):
    """Handle roulette callback."""
    await callback.message.edit_text(
        "🎡 **Roulette**\n\nTap to play!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎡 Open Roulette", web_app=WebAppInfo(url=config.WEBAPP_URL + "#roulette"))],
            [InlineKeyboardButton(text="← Back", callback_data="menu")]
        ])
    )
    await callback.answer()


async def callback_slots(callback: CallbackQuery, bot: Bot):
    """Handle slots callback."""
    await callback.message.edit_text(
        "🎰 **Slots Machine**\n\nTap to play!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎰 Open Slots", web_app=WebAppInfo(url=config.WEBAPP_URL + "#slots"))],
            [InlineKeyboardButton(text="← Back", callback_data="menu")]
        ])
    )
    await callback.answer()


async def callback_breed(callback: CallbackQuery, bot: Bot):
    """Handle breed callback."""
    await callback.message.edit_text(
        "🧬 **Breeding System**\n\nCombine items to create new ones!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧬 Open Breeding", web_app=WebAppInfo(url=config.WEBAPP_URL + "#breed"))],
            [InlineKeyboardButton(text="← Back", callback_data="menu")]
        ])
    )
    await callback.answer()


async def callback_market(callback: CallbackQuery, bot: Bot):
    """Handle market callback."""
    await callback.message.edit_text(
        "🛒 **Marketplace**\n\nBuy and sell items!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Open Market", web_app=WebAppInfo(url=config.WEBAPP_URL + "#market"))],
            [InlineKeyboardButton(text="← Back", callback_data="menu")]
        ])
    )
    await callback.answer()


async def callback_referral(callback: CallbackQuery, bot: Bot):
    """Handle referral callback."""
    from db.engine import async_session
    from sqlalchemy import select
    from db import User

    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        if user:
            ref_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"
            await callback.message.edit_text(
                f"👥 **Your Referral Link:**\n\n`{ref_link}`\n\n"
                f"Share it and earn **{config.REFERRAL_BONUS} coins** per friend!",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
    await callback.answer()


async def callback_leaderboard(callback: CallbackQuery, bot: Bot):
    """Handle leaderboard callback."""
    from db.engine import async_session
    from api import get_leaderboard

    async with async_session() as session:
        board = await get_leaderboard(session, "coins")

        text = "🏆 **Top Players**\n\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, entry in enumerate(board[:10]):
            medal = medals[i] if i < 3 else f"{i+1}."
            text += f"{medal} **{entry['username']}** - {entry['value']} coins\n"

        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_back_keyboard())
    await callback.answer()


async def callback_stats(callback: CallbackQuery, bot: Bot):
    """Handle stats callback."""
    from db.engine import async_session
    from api import get_user_stats

    async with async_session() as session:
        stats = await get_user_stats(session, callback.from_user.id)

        if stats:
            await callback.message.edit_text(
                f"📊 **Your Stats**\n\n"
                f"💰 Coins: {stats['coins']}\n"
                f"📊 Level: {stats['level']}\n"
                f"📦 Items: {stats['total_items']}\n"
                f"📦 Cases: {stats['cases_opened']}\n"
                f"🎡 Roulette: {stats['roulette_spins']}\n"
                f"🎰 Slots: {stats['slots_spins']}",
                parse_mode="Markdown",
                reply_markup=get_back_keyboard()
            )
    await callback.answer()


async def callback_achievements(callback: CallbackQuery, bot: Bot):
    """Handle achievements callback."""
    await cmd_achievements(callback.message, bot)
    await callback.answer()


async def callback_menu(callback: CallbackQuery, bot: Bot):
    """Handle menu callback."""
    await callback.message.edit_text(
        "🎰 **Casino Menu**\n\nChoose a game:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


# ============================================================
# REGISTER HANDLERS
# ============================================================

def register_handlers(dp: Dispatcher):
    """Register all handlers."""
    # Commands
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_play, Command("play"))
    dp.message.register(cmd_daily, Command("daily"))
    dp.message.register(cmd_inventory, Command("inventory"))
    dp.message.register(cmd_referral, Command("referral"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_leaderboard, Command("leaderboard"))
    dp.message.register(cmd_achievements, Command("achievements"))
    dp.message.register(cmd_help, Command("help"))

    # Callbacks
    dp.callback_query.register(callback_daily, F.data == "daily")
    dp.callback_query.register(callback_inventory, F.data == "inventory")
    dp.callback_query.register(callback_roulette, F.data == "roulette")
    dp.callback_query.register(callback_slots, F.data == "slots")
    dp.callback_query.register(callback_breed, F.data == "breed")
    dp.callback_query.register(callback_market, F.data == "market")
    dp.callback_query.register(callback_referral, F.data == "referral")
    dp.callback_query.register(callback_leaderboard, F.data == "leaderboard")
    dp.callback_query.register(callback_stats, F.data == "stats")
    dp.callback_query.register(callback_achievements, F.data == "achievements")
    dp.callback_query.register(callback_menu, F.data == "menu")
