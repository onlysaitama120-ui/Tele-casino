#!/usr/bin/env python3
"""Replaces all callback handlers with versions using cb.from_user.id."""
import pathlib

P = pathlib.Path(__file__).parent / "bot" / "__init__.py"
NL = chr(10)
DQ = chr(34)

NEW = NL.join([
    "# ============================================================",
    "# CALLBACKS - always use cb.from_user.id (NOT message.from_user!",
    "# that is the BOT's id on callback messages)",
    "# ============================================================",
    "",
    "N = chr(10)",
    "",
    "async def cb_menu(cb: CallbackQuery, bot: Bot):",
    "    await cb.message.edit_text(",
    '        "💎 **GIFT RUSH**" + N + N + "Pick an action:",',
    '        parse_mode="Markdown", reply_markup=main_kb(),',
    "    )",
    "    await cb.answer()",
    "",
    "async def cb_daily(cb: CallbackQuery, bot: Bot):",
    "    from db.engine import async_session",
    "    from api import claim_daily, get_wallet",
    "    from sqlalchemy import select",
    "    from db import User",
    "    uid = cb.from_user.id",
    "    async with async_session() as session:",
    "        success, coins, streak, next_claim = await claim_daily(session, uid)",
    "        if success:",
    "            u = await session.execute(",
    "                select(User).where(User.telegram_id == uid))",
    "            user = u.scalar_one_or_none()",
    "            wallet = await get_wallet(session, user.id) if user else None",
    "            bal = wallet.coins if wallet else 0",
    "            await cb.message.answer(",
    '                f"🎁 **Daily Drop claimed!**{N}{N}"',
    '                + f"💎 +{coins} gems{N}"',
    '                + f"🔥 Streak: {streak} days{N}"',
    '                + f"💰 Balance: {bal} gems",',
    '                parse_mode="Markdown", reply_markup=back_kb())',
    "        else:",
    "            await cb.message.answer(",
    '                f"⏰ Already claimed! Next drop in **{next_claim}**",',
    '                parse_mode="Markdown", reply_markup=back_kb())',
    "    await cb.answer()",
    "",
    "async def cb_deposit(cb: CallbackQuery, bot: Bot):",
    "    from db.engine import async_session",
    "    from api.deposits import get_deposit_info",
    "    uid = cb.from_user.id",
    "    async with async_session() as session:",
    "        info = await get_deposit_info(session, uid)",
    "    await cb.message.answer(",
    '        f"💸 **Deposit TON → Gems**{N}{N}"',
    '        + f"**1.** Send TON to:{N}`{info[' + DQ + "address" + DQ + ']}`{N}{N}"',
    '        + f"**2.** Memo (IMPORTANT!):{N}`{info[' + DQ + "memo" + DQ + ']}`{N}{N}"',
    '        + f"💱 1 TON = **{info[' + DQ + "gems_per_ton" + DQ + ']} gems**",',
    '        parse_mode="Markdown", reply_markup=deposit_kb())',
    "    await cb.answer()",
    "",
    "async def cb_referral(cb: CallbackQuery, bot: Bot):",
    "    from db.engine import async_session",
    "    from sqlalchemy import select",
    "    from db import User",
    "    uid = cb.from_user.id",
    "    async with async_session() as session:",
    "        result = await session.execute(",
    "            select(User).where(User.telegram_id == uid))",
    "        user = result.scalar_one_or_none()",
    "        if not user:",
    "            await cb.message.answer(" + DQ + "Send /start first!" + DQ + ")",
    "        else:",
    "            link = f" + DQ + "https://t.me/{config.BOT_USERNAME}?start=ref_{user.referral_code}" + DQ,
    "            await cb.message.answer(",
    '                f"👥 **Invite & Earn**{N}{N}"',
    '                + f"`{link}`{N}{N}"',
    '                + f"💎 +{config.REFERRAL_BONUS} gems per friend{N}"',
    '                + f"📊 Total invites: **{user.total_referrals}**",',
    '                parse_mode="Markdown", reply_markup=back_kb())',
    "    await cb.answer()",
    "",
    "async def cb_leaderboard(cb: CallbackQuery, bot: Bot):",
    "    from db.engine import async_session",
    "    from api import get_leaderboard",
    "    async with async_session() as session:",
    "        board = await get_leaderboard(session, " + DQ + "coins" + DQ + ")",
    "        medals = [" + DQ + "🥇" + DQ + ", " + DQ + "🥈" + DQ + ", " + DQ + "🥉" + DQ + "]",
    "        text = " + DQ + "🏆 **Top Collectors**" + DQ + " + N + N",
    "        for i, e in enumerate(board[:10]):",
    "            m = medals[i] if i < 3 else f" + DQ + "{i+1}." + DQ,
    "            text += f" + DQ + "{m} **{e[" + "'username'" + "] or "
    + "'Player'" + "}** — 💎{e[" + "'value'" + "]}{N}" + DQ,
    "        await cb.message.edit_text(text, parse_mode=" + DQ + "Markdown" + DQ +
    ", reply_markup=back_kb())",
    "    await cb.answer()",
    "",
    "async def cb_stats(cb: CallbackQuery, bot: Bot):",
    "    from db.engine import async_session",
    "    from api import get_user_stats",
    "    uid = cb.from_user.id",
    "    async with async_session() as session:",
    "        s = await get_user_stats(session, uid)",
    "        if not s:",
    "            await cb.message.answer(" + DQ + "Send /start first!" + DQ + ")",
    "        else:",
    "            await cb.message.answer(",
    '                f"📊 **Collector Profile**{N}{N}"',
    '                + f"💎 Gems: **{s[' + "'coins'" + ']}**{N}"',
    '                + f"⭐ Level: **{s[' + "'level'" + ']}**{N}"',
    '                + f"📦 Items: **{s[' + "'total_items'" + ']}**{N}"',
    '                + f"🎁 Boxes: **{s[' + "'cases_opened'" + ']}**{N}"',
    '                + f"🧬 Fusions: **{s[' + "'items_bred'" + ']}**{N}"',
    '                + f"🔥 Streak: **{s[' + "'daily_streak'" + ']} days**{N}"',
    '                + f"👥 Invites: **{s[' + "'total_referrals'" + ']}**",',
    '                parse_mode="Markdown", reply_markup=back_kb())',
    "    await cb.answer()",
    "",
    "async def cb_inventory(cb: CallbackQuery, bot: Bot):",
    "    await cb.message.answer(",
    '        "📦 **Your Vault lives in the game!**",',
    '        parse_mode="Markdown",',
    "        reply_markup=InlineKeyboardMarkup(inline_keyboard=[",
    "            [InlineKeyboardButton(",
    '                text="📦 Open Vault",',
    "                web_app=WebAppInfo(url=config.WEBAPP_URL + " + DQ + "#inventory" + DQ + ")),",
    "            ],",
    "            [InlineKeyboardButton(text=" + DQ + "← Menu" + DQ + ", callback_data=" + DQ + "menu" + DQ + ")],",
    "        ]))",
    "    await cb.answer()",
    "",
    "",
])

s = P.read_text(encoding="utf-8")
start_marker = "# ============================================================"
# locate old callback section start (the one followed by CALLBACKS comment)
i = s.find(NL + start_marker + NL + "# CALLBACKS")
if i < 0:
    # maybe already replaced
    if "always use cb.from_user.id" in s:
        print("[skip] already patched")
        raise SystemExit
    raise SystemExit("[fail] callback section not found")

end_marker = NL + "def register_handlers"
j = s.find(end_marker, i)
if j < 0:
    raise SystemExit("[fail] register_handlers not found")

s = s[:i] + NL + NEW + s[j:]
P.write_text(s, encoding="utf-8")
print("[ok] callback handlers rewritten with correct user ids")
