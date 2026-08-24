#!/usr/bin/env python3
"""Removes roulette + slots completely (game engine + API routes)."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)
BAR = "# ============================================================"


def splice(s, start_marker, end_marker, label):
    i = s.find(start_marker)
    j = s.find(end_marker, i + 1) if i >= 0 else -1
    if i < 0 or j < 0:
        print(f"[warn] {label}: markers missing")
        return s, False
    print(f"[ok] {label}: removed {j - i} chars")
    return s[:i] + s[j:], True


# ---------- api/__init__.py : kill game functions ----------
P = ROOT / "api" / "__init__.py"
s = P.read_text(encoding="utf-8")

start = "async def spin_roulette"
end = BAR + NL + "# BREEDING SYSTEM"
s, ok1 = splice(s, start, end, "engine: roulette+slots functions")
P.write_text(s, encoding="utf-8")

# ---------- server.py : kill routes ----------
P2 = ROOT / "api" / "server.py"
s2 = P2.read_text(encoding="utf-8")

r_start = "@app.post(" + chr(34) + "/api/roulette/spin" + chr(34) + ")"
r_end = BAR + NL + "# BREEDING"
s2, ok2 = splice(s2, r_start, r_end, "routes: roulette+slots+configs")

P2.write_text(s2, encoding="utf-8")

if ok1 and ok2:
    print("[done] roulette & slots fully excised")
