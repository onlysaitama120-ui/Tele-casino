#!/usr/bin/env python3
"""Fixes all MarketplaceListing imports (db, not api.deposits) + restores wallets endpoint."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
s = P.read_text(encoding="utf-8")
NL = chr(10)

# 1. Fix imports in debug endpoint
s = s.replace("from api.deposits import InventoryItem, MarketplaceListing",
              "from db import InventoryItem, MarketplaceListing")

# 2. Fix imports in startup (if seed_marketplace imports wrong)
# seed_marketplace is in api/__init__.py — let me check if it has the same bug

# 3. Restore wallets endpoint decorator + remove its duplicate on seed
OLD_550_551 = NL.join([
    '@app.get("/api/debug/wallets")',
    "@app.get('/api/debug/seed')",
])
NEW_551 = "@app.get('/api/debug/seed')"
if OLD_550_551 in s:
    s = s.replace(OLD_550_551, NEW_551, 1)
    print("[ok] removed stray wallets decorator from seed endpoint")

# 4. Add wallets decorator before wallets function
WALLETS_FUNC = "async def api_debug_wallets():"
WALLETS_DECORATOR = "@app.get('/api/debug/wallets')" + NL + "async def api_debug_wallets():"
if WALLETS_FUNC in s and "@app.get('/api/debug/wallets')" not in s:
    s = s.replace(WALLETS_FUNC, WALLETS_DECORATOR, 1)
    print("[ok] wallets decorator restored")

P.write_text(s, encoding="utf-8")
print("[done]")

# Verify
print("--- verify imports ---")
import subprocess
r = subprocess.run(["python", "-c", "import sys; sys.path.insert(0,'.'); from api import seed_marketplace; print('seed import OK')"], capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
