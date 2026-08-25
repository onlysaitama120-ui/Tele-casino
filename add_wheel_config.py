#!/usr/bin/env python3
"""Appends WHEEL config + User columns for free spins."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)

# ---------- config.py ----------
cfg = ROOT / "config.py"
s = cfg.read_text(encoding="utf-8")
if "WHEEL_SEGMENTS" not in s:
    block = NL.join([
        "",
        "# ============================================================",
        "# GIFT WHEEL (hero feature - virus_play_bot style)",
        "# ============================================================",
        "",
        "WHEEL_SPIN_COST = 100          # gems when no free spin available",
        "FREE_SPIN_PER_DAY = 1",
        "REFERRAL_BONUS_SPINS = 2       # bonus spins per invite",
        "",
        "WHEEL_SEGMENTS = [",
        "    # chance must total ~100",
        '    {"label": "15",    "emoji": "💎",  "type": "gems", "value": 15,     "chance": 40.0,   "color": "#3d4470"},',
        '    {"label": "50",    "emoji": "💎",  "type": "gems", "value": 50,     "chance": 28.0,   "color": "#2a3055"},',
        '    {"label": "120",   "emoji": "💎",  "type": "gems", "value": 120,    "chance": 14.0,   "color": "#3d4470"},',
        '    {"label": "NEXT!", "emoji": "💨",  "type": "none",  "value": 0,      "chance": 12.481, "color": "#222742"},',
        '    {"label": "300",   "emoji": "💎",  "type": "gems", "value": 300,    "chance": 4.5,    "color": "#7c5cff"},',
        '    {"label": "SIGNET","emoji": "💍",  "type": "gift",  "value": 800,    "chance": 0.8,    "color": "#38bdf8",',
        '     "item": {"name": "Neon Signet", "rarity": "rare",      "emoji": "💍"}},',
        '    {"label": "ROSE",  "emoji": "🌹",  "type": "gift",  "value": 5000,   "chance": 0.15,   "color": "#f472b6",',
        '     "item": {"name": "Eternal Rose", "rarity": "epic",     "emoji": "🌹"}},',
        '    {"label": "CAP",   "emoji": "🧢",  "type": "gift",  "value": 80000,  "chance": 0.03,   "color": "#ffd54a",',
        '     "item": {"name": "Durov Cap (NFT)", "rarity": "mythic",  "emoji": "🧢"}},',
        '    {"label": "PEPE",  "emoji": "🐸",  "type": "gift",  "value": 1000000,"chance": 0.001,  "color": "#39d353",',
        '     "item": {"name": "Plush Pepe (NFT)", "rarity": "divine",  "emoji": "🐸"}},',
        "]",
    ])
    cfg.write_text(s + NL + block + NL, encoding="utf-8")
    print("[ok] WHEEL config appended")
else:
    print("[skip] wheel config exists")

# ---------- db/__init__.py : User columns ----------
dbp = ROOT / "db" / "__init__.py"
d = dbp.read_text(encoding="utf-8")
anchor = "    daily_streak = Column(Integer, default=0)"
add_cols = NL.join([
    anchor,
    "    last_free_spin = Column(DateTime, nullable=True)",
    "    bonus_spins = Column(Integer, default=0)",
])
if "last_free_spin" not in d:
    if anchor not in d:
        raise SystemExit("[fail] user column anchor missing")
    d = d.replace(anchor, add_cols, 1)
    dbp.write_text(d, encoding="utf-8")
    print("[ok] User free-spin columns added")
else:
    print("[skip] user columns exist")

print("done")