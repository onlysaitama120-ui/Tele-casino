#!/usr/bin/env python3
"""
GIFT RUSH - Telegram Bot Handlers.
NFT collectible game: mystery boxes, fusion, trading, TON deposits.
"""

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, CallbackQuery,
)

import config


# ============================================================
# KEYBOARDS
# ============================================================

def main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Open GIFT RUSH",
                              web_app=WebAppInfo(url=config.WEBAPP_URL))],
        [
            InlineKeyboardButton(text="🎁 Daily Drop", callback_data="daily"),
            InlineKeyboardButton(text="📦 Collection", callback_data="inventory"),
        ],
        [
            InlineKeyboardButton(text="💸 Deposit", callback_data="deposit"),
            InlineKeyboardButton(text="👥 Invite", callback_data="referral"),
        ],
        [
            InlineKeyboardButton(text="🏆 Top Collectors", callback_data="leaderboard"),
            InlineKeyboardButton(text="📊 Profile", callback_data="stats"),
        ],
    ])


def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="← Menu", callback_data="menu")]
    ])


def deposit_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Open Deposit Panel",
                              web_app=WebAppInfo(url=config.WEBAPP_URL + "#deposit"))],
        [InlineKeyboardButton(text="← Menu", callback_data="menu")],
    ])


# ============================================================
# COMMANDS
# ============================================================

async def cmd_start(message: types.Message, bot: Bot):
    args = message.text.split()
    ref_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]

    from db.engine import async_session
    from api import get_or_create_user, get_wallet

    async with async_session() as session:
        user, is_new = await get_or_create_user(
            session,
            message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            referral_code=ref_code,
        )
        wallet = await get_wallet(session, user.telegram_id)

    if is_new:
        text = (
            f"💎 **Welcome to GIFT RUSH!** 💎\n\n"
            f"Yo {message.from_user.first_name}! 👋\n\n"
            f"🎉 Starter pack: **{config.INITIAL_GEMS} gems**\n\n"
            f"**🎮 How it works:**\n"
            f"📦 Open Mystery Boxes → collect rare items\n"
            f"🧬 Fuse duplicates → upgrade rarity\n"
            f"🛒 Trade with other collectors\n"
            f"🏆 Climb the collector leaderboard\n\n"
            f"💸 Deposit TON → pull legendary NFT gifts!\n\n"
            f"_Collect. Fuse. Flex._ ✨"
        )
    else:
        text = (
            f"👋 Welcome back, **{message.from_user.first_name}**!\n\n"
            f"💎 Gems: **{wallet.coins if wallet else 0}**\n"
            f"🔥 Streak: **{user.daily_streak} days**\n\n"
            f"The boxes are waiting... ✨"
        )

    # banner + caption (falls back to text if photo fails)
    photo_url = config.WEBAPP_URL + "/static/banner.png?v=1"
    try:
        await message.answer_photo(
            photo=photo_url,
            caption=text,
            parse_mode="Markdown",
            reply_markup=main_kb(),
        )
    except Exception:
        await message.answer(text, reply_markup=main_kb(), 
parse_mode="Markdown")


async def cmd_play(message: types.Message, bot: Bot):
    await message.answer(
        "💎 **GIFT RUSH loading...**\n\nTap below to enter!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💎 Enter Game",
                web_app=WebAppInfo(url=config.WEBAPP_URL),
            )]
        ]),
        parse_mode="Markdown",
    )


async def cmd_daily(message: types.Message, bot: Bot):
    from db.engine import async_session
    from api import claim_daily, get_wallet

    async with async_session() as session:
        success, coins, streak, next_claim = await claim_daily(
            session, message.from_user.id
        )
        if success:
            wallet = await get_wallet(session, message.from_user.id)
            await message.answer(
                f"🎁 **Daily Drop claimed!**\n\n"
                f"💎 +{coins} gems\n"
                f"🔥 Streak: {streak} days\n"
                f"💰 Balance: {wallet.coins} gems\n\n"
                f"Back tomorrow for more ✨",
                parse_mode="Markdown",
            )
        else:
            await message.answer(
                f"⏰ Already claimed!\n\nNext drop in: **{next_claim}**",
                parse_mode="Markdown",
            )


async def cmd_deposit(message: types.Message, bot: Bot):
    """Show personal deposit address + memo."""
    from db.engine import async_session
    from api.deposits import get_deposit_info

    async with async_session() as session:
        info = await get_deposit_info(session, message.from_user.id)

    await message.answer(
        f"💸 **Deposit TON → Gems**\n\n"
        f"**1.** Send TON to this address:\n"
        f"`{info['address']}`\n\n"
        f"**2.** Attach this memo (IMPORTANT!):\n"
        f"`{info['memo']}`\n\n"
        f"💱 Rate: **1 TON = {info['gems_per_ton']} gems**\n"
        f"🔽 Minimum: **{info['min_ton']} TON**\n\n"
        f"Gems land automatically after the network confirms.\n"
        f"Use the panel below to check your deposit:",
        parse_mode="Markdown",
        reply_markup=deposit_kb(),
    )


async def cmd_inventory(message: types.Message, bot: Bot):
    await message.answer(
        "📦 **Your Collection** lives in the game app!",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📦 Open Collection",
                web_app=WebAppInfo(url=config.WEBAPP_URL + "#inventory"),
            )],
            [InlineKeyboardButton(text="← Menu", callback_data="menu")],
        ]),
    )


async def cmd_referral(message: types.Message, bot: Bot):
    from db.engine import async_session
    from sqlalchemy import select
    from db import User

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Send /start first!")
            return

        link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"
        await message.answer(
            f"👥 **Invite & Earn**\n\n"
            f"Your link:`\n`{link}`\n\n"
            f"💎 +{config.REFERRAL_BONUS} gems per friend\n"
            f"📊 Total invites: **{user.total_referrals}**",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )


async def cmd_stats(message: types.Message, bot: Bot):
    from db.engine import async_session
    from api import get_user_stats

    async with async_session() as session:
        s = await get_user_stats(session, message.from_user.id)
        if not s:
            await message.answer("Send /start first!")
            return

        await message.answer(
            f"📊 **Collector Profile**\n\n"
            f"💎 Gems: **{s['coins']}**\n"
            f"⭐ Level: **{s['level']}**\n"
            f"📦 Items: **{s['total_items']}**\n"
            f"🎁 Boxes opened: **{s['cases_opened']}**\n"
            f"🧬 Fusions: **{s['items_bred']}**\n"
            f"🔥 Streak: **{s['daily_streak']} days**\n"
            f"👥 Invites: **{s['total_referrals']}**",
            parse_mode="Markdown",
            reply_markup=back_kb(),
        )


async def cmd_leaderboard(message: types.Message, bot: Bot):
    from db.engine import async_session
    from api import get_leaderboard

    async with async_session() as session:
        board = await get_leaderboard(session, "coins")
        medals = ["🥇", "🥈", "🥉"]
        text = "🏆 **Top Collectors**\n\n"
        for i, e in enumerate(board[:10]):
            m = medals[i] if i < 3 else f"{i+1}."
            text += f"{m} **{e['username'] or 'Player'}** — 💎{e['value']}\n"
        await message.answer(text, parse_mode="Markdown", reply_markup=back_kb())


async def cmd_achievements(message: types.Message, bot: Bot):
    await message.answer(
        "🏅 **Achievements live in the game app!**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🏅 View Achievements",
                web_app=WebAppInfo(url=config.WEBAPP_URL),
            )],
            [InlineKeyboardButton(text="← Menu", callback_data="menu")],
        ]),
    )


async def cmd_help(message: types.Message, bot: Bot):
    await message.answer(
        "💎 **GIFT RUSH — Help**\n\n"
        "/start — begin collecting\n"
        "/play — open the game\n"
        "/daily — free daily drop\n"
        "/deposit — buy gems with TON\n"
        "/inventory — your collection\n"
        "/referral — invite & earn\n"
        "/stats — profile stats\n"
        "/leaderboard — top collectors\n"
        "/help — this menu",
        parse_mode="Markdown",
        reply_markup=back_kb(),
    )


async def cmd_admin(message: types.Message, bot: Bot):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ No access")
        return

    from db.engine import async_session
    from api.deposits import list_withdrawals

    async with async_session() as session:
        queue = await list_withdrawals(session)

    text = "🔧 **Admin**\n\n**Pending gift payouts:**\n"
    if queue:
        for r in queue:
            text += f"#{r['id']} — @{r['user']} wants **{r['item']}** (💎{r['value']})\n"
        text += "\nDeliver the gift in Telegram, then:\n"
        text += "`/admin_done <request_id>`"
    else:
        text += "Queue empty ✅"

    await message.answer(text, parse_mode="Markdown")


async def cmd_admin_done(message: types.Message, bot: Bot):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ No access")
        return

    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("Usage: /admin_done <request_id>")
        return

    from db.engine import async_session
    from api.deposits import complete_withdrawal

    async with async_session() as session:
        result = await complete_withdrawal(session, int(parts[1]))
        await message.answer("✅ Marked fulfilled" if result.get("success")
                             else result.get("message"))


# ============================================================
# CALLBACKS - always use cb.from_user.id (NOT message.from_user!
# that is the BOT's id on callback messages)
# ============================================================

N = chr(10)

async def cb_menu(cb: CallbackQuery, bot: Bot):
    await cb.message.edit_text(
        "💎 **GIFT RUSH**" + N + N + "Pick an action:",
        parse_mode="Markdown", reply_markup=main_kb(),
    )
    await cb.answer()

async def cb_daily(cb: CallbackQuery, bot: Bot):
    from db.engine import async_session
    from api import claim_daily, get_wallet
    from sqlalchemy import select
    from db import User
    uid = cb.from_user.id
    async with async_session() as session:
        success, coins, streak, next_claim = await claim_daily(session, uid)
        if success:
            u = await session.execute(
                select(User).where(User.telegram_id == uid))
            user = u.scalar_one_or_none()
            wallet = await get_wallet(session, user.telegram_id) if user else None
            bal = wallet.coins if wallet else 0
            await cb.message.answer(
                f"🎁 **Daily Drop claimed!**{N}{N}"
                + f"💎 +{coins} gems{N}"
                + f"🔥 Streak: {streak} days{N}"
                + f"💰 Balance: {bal} gems",
                parse_mode="Markdown", reply_markup=back_kb())
        else:
            await cb.message.answer(
                f"⏰ Already claimed! Next drop in **{next_claim}**",
                parse_mode="Markdown", reply_markup=back_kb())
    await cb.answer()

async def cb_deposit(cb: CallbackQuery, bot: Bot):
    from db.engine import async_session
    from api.deposits import get_deposit_info
    uid = cb.from_user.id
    async with async_session() as session:
        info = await get_deposit_info(session, uid)
    await cb.message.answer(
        f"💸 **Deposit TON → Gems**{N}{N}"
        + f"**1.** Send TON to:{N}`{info["address"]}`{N}{N}"
        + f"**2.** Memo (IMPORTANT!):{N}`{info["memo"]}`{N}{N}"
        + f"💱 1 TON = **{info["gems_per_ton"]} gems**",
        parse_mode="Markdown", reply_markup=deposit_kb())
    await cb.answer()

async def cb_referral(cb: CallbackQuery, bot: Bot):
    from db.engine import async_session
    from sqlalchemy import select
    from db import User
    uid = cb.from_user.id
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == uid))
        user = result.scalar_one_or_none()
        if not user:
            await cb.message.answer("Send /start first!")
        else:
            link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}"
            await cb.message.answer(
                f"👥 **Invite & Earn**{N}{N}"
                + f"`{link}`{N}{N}"
                + f"💎 +{config.REFERRAL_BONUS} gems per friend{N}"
                + f"📊 Total invites: **{user.total_referrals}**",
                parse_mode="Markdown", reply_markup=back_kb())
    await cb.answer()

async def cb_leaderboard(cb: CallbackQuery, bot: Bot):
    from db.engine import async_session
    from api import get_leaderboard
    async with async_session() as session:
        board = await get_leaderboard(session, "coins")
        medals = ["🥇", "🥈", "🥉"]
        text = "🏆 **Top Collectors**" + N + N
        for i, e in enumerate(board[:10]):
            m = medals[i] if i < 3 else f"{i+1}."
            text += f"{m} **{e['username'] or 'Player'}** — 💎{e['value']}{N}"
        await cb.message.edit_text(text, parse_mode="Markdown", reply_markup=back_kb())
    await cb.answer()

async def cb_stats(cb: CallbackQuery, bot: Bot):
    from db.engine import async_session
    from api import get_user_stats
    uid = cb.from_user.id
    async with async_session() as session:
        s = await get_user_stats(session, uid)
        if not s:
            await cb.message.answer("Send /start first!")
        else:
            await cb.message.answer(
                f"📊 **Collector Profile**{N}{N}"
                + f"💎 Gems: **{s['coins']}**{N}"
                + f"⭐ Level: **{s['level']}**{N}"
                + f"📦 Items: **{s['total_items']}**{N}"
                + f"🎁 Boxes: **{s['cases_opened']}**{N}"
                + f"🧬 Fusions: **{s['items_bred']}**{N}"
                + f"🔥 Streak: **{s['daily_streak']} days**{N}"
                + f"👥 Invites: **{s['total_referrals']}**",
                parse_mode="Markdown", reply_markup=back_kb())
    await cb.answer()

async def cb_inventory(cb: CallbackQuery, bot: Bot):
    await cb.message.answer(
        "📦 **Your Vault lives in the game!**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📦 Open Vault",
                web_app=WebAppInfo(url=config.WEBAPP_URL + "#inventory")),
            ],
            [InlineKeyboardButton(text="← Menu", callback_data="menu")],
        ]))
    await cb.answer()


def register_handlers(dp: Dispatcher):
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_play, Command("play"))
    dp.message.register(cmd_daily, Command("daily"))
    dp.message.register(cmd_deposit, Command("deposit"))
    dp.message.register(cmd_inventory, Command("inventory"))
    dp.message.register(cmd_referral, Command("referral"))
    dp.message.register(cmd_stats, Command("stats"))
    dp.message.register(cmd_leaderboard, Command("leaderboard"))
    dp.message.register(cmd_achievements, Command("achievements"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_admin_done, Command("admin_done"))
    dp.message.register(cmd_admin, Command("admin"))

    dp.callback_query.register(cb_menu, F.data == "menu")
    dp.callback_query.register(cb_daily, F.data == "daily")
    dp.callback_query.register(cb_deposit, F.data == "deposit")
    dp.callback_query.register(cb_referral, F.data == "referral")
    dp.callback_query.register(cb_leaderboard, F.data == "leaderboard")
    dp.callback_query.register(cb_stats, F.data == "stats")
    dp.callback_query.register(cb_inventory, F.data == "inventory")
