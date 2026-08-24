#!/usr/bin/env python3
"""Wraps spin_roulette with debug traceback exposure (temporary)."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "__init__.py"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

if "_spin_roulette_inner" in s:
    print("[skip] wrapper already present")
    raise SystemExit

OLD_DEF = "async def spin_roulette(session: AsyncSession, user_id: int, bet: int, color: str):"
NEW_DEF = NL.join([
    "async def spin_roulette(session: AsyncSession, user_id: int, bet: int, color: str):",
    "    try:",
    "        return await _spin_roulette_inner(session, user_id, bet, color)",
    "    except Exception as e:",
    "        import traceback",
    "        return {" + DQ + "success" + DQ + ": False,",
    "                " + DQ + "debug" + DQ + ": traceback.format_exc()[-700:]}",
    "",
    "",
    "async def _spin_roulette_inner(session: AsyncSession, user_id: int, bet: int, color: str):",
])

if OLD_DEF in s:
    s = s.replace(OLD_DEF, NEW_DEF, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] debug wrapper installed")
else:
    print("[fail] def not found")
