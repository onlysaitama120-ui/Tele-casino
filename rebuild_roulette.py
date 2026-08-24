#!/usr/bin/env python3
"""Rebuilds spin_roulette as one clean hardened function."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "__init__.py"
NL = chr(10)
DQ = chr(34)

CLEAN = NL.join([
    "async def spin_roulette(session: AsyncSession, user_id: int, bet, color: str):",
    '    """Spin roulette - hardened."""',
    "    if color not in config.ROULETTE[" + DQ + "colors" + DQ + "]:",
    "        return {" + DQ + "success" + DQ + ": False, " + DQ + "message" + DQ + ": " + DQ + "Invalid color" + DQ + "}",
    "",
    "    try:",
    "        bet = int(bet)",
    "    except Exception:",
    "        bet = -1",
    "    if bet <= 0:",
    "        return {" + DQ + "success" + DQ + ": False, " + DQ + "message" + DQ + ": " + DQ + "Invalid bet" + DQ + "}",
    "    if bet < config.ROULETTE[" + DQ + "min_bet" + DQ + "] or bet > config.ROULETTE[" + DQ + "max_bet" + DQ + "]:",
    "        return {" + DQ + "success" + DQ + ": False, " + DQ + "message" + DQ + ": " + DQ + "Bet out of range" + DQ + "}",
    "",
    "    wallet = await get_wallet(session, user_id)",
    "    if not wallet or wallet.coins < bet:",
    "        return {" + DQ + "success" + DQ + ": False, " + DQ + "message" + DQ + ": " + DQ + "Not enough coins" + DQ + ",",
    "                " + DQ + "balance" + DQ + ": wallet.coins if wallet else 0}",
    "",
    "    # Deduct bet",
    "    wallet.coins -= bet",
    "    session.add(Transaction(",
    "        user_id=user_id,",
    "        type=" + DQ + "roulette_bet" + DQ + ",",
    "        amount=-bet,",
    "        balance_after=wallet.coins,",
    "        description=f" + DQ + "Roulette bet ({color})" + DQ + ",",
    "    ))",
    "",
    "    # Provably fair roll",
    "    result_color = generate_roulette_result()",
    "    color_data = config.ROULETTE[" + DQ + "colors" + DQ + "][color]",
    "",
    "    won = 0",
    "    if result_color == color:",
    "        won = int(bet * color_data[" + DQ + "multiplier" + DQ + "])",
    "        wallet.coins += won",
    "        session.add(Transaction(",
    "            user_id=user_id,",
    "            type=" + DQ + "roulette_win" + DQ + ",",
    "            amount=won,",
    "            balance_after=wallet.coins,",
    "            description=f" + DQ + "Roulette win ({result_color})" + DQ + ",",
    "        ))",
    "",
    "    session.add(SpinResult(",
    "        user_id=user_id,",
    "        game_type=" + DQ + "roulette" + DQ + ",",
    "        bet=bet,",
    "        result={" + DQ + "color" + DQ + ": result_color},",
    "        multiplier=color_data[" + DQ + "multiplier" + DQ + "] if result_color == color else 0,",
    "        won=won,",
    "    ))",
    "",
    "    u = await session.execute(select(User).where(User.telegram_id == user_id))",
    "    user_row = u.scalar_one_or_none()",
    "    if user_row:",
    "        user_row.roulette_spins += 1",
    "        if won > 0:",
    "            user_row.total_earned += won",
    "        else:",
    "            user_row.total_spent += bet",
    "",
    "    await session.commit()",
    "",
    "    return {",
    "        " + DQ + "success" + DQ + ": True,",
    "        " + DQ + "result" + DQ + ": result_color,",
    "        " + DQ + "color_emoji" + DQ + ": config.ROULETTE[" + DQ + "colors" + DQ + "][result_color][" + DQ + "emoji" + DQ + "],",
    "        " + DQ + "multiplier" + DQ + ": color_data[" + DQ + "multiplier" + DQ + "] if result_color == color else 0,",
    "        " + DQ + "won" + DQ + ": won,",
    "        " + DQ + "balance" + DQ + ": wallet.coins,",
    "    }",
    "",
    "",
])

s = P.read_text(encoding="utf-8")

start = s.find("async def spin_roulette")
end = s.find("def generate_roulette_result")

if start < 0 or end < 0 or end <= start:
    raise SystemExit("[fail] section markers not found")

s = s[:start] + CLEAN + s[end:]
P.write_text(s, encoding="utf-8")
print("[ok] spin_roulette rebuilt clean")
