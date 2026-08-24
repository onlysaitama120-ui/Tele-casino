#!/usr/bin/env python3
"""Removes dead roulette/slots imports from server.py."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
NL = chr(10)

s = P.read_text(encoding="utf-8")

OLD = NL.join([
    "from api import (",
    "    get_or_create_user, get_wallet, update_wallet,",
    "    claim_daily, open_case, spin_roulette, spin_slots,",
    "    breed_items, list_item, buy_item,",
    "    get_inventory, get_user_stats, get_achievements,",
    "    get_leaderboard, send_gift",
    ")",
])

NEW = NL.join([
    "from api import (",
    "    get_or_create_user, get_wallet, update_wallet,",
    "    claim_daily, open_case,",
    "    breed_items, list_item, buy_item,",
    "    get_inventory, get_user_stats, get_achievements,",
    "    get_leaderboard, send_gift",
    ")",
])

if OLD in s:
    P.write_text(s.replace(OLD, NEW, 1), encoding="utf-8")
    print("[ok] imports cleaned")
else:
    print("[warn] pattern drifted")
