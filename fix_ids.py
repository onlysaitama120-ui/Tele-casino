#!/usr/bin/env python3
"""Standardizes ALL wallet/tx keys on TELEGRAM id (fixes split-brain)."""
import pathlib

ROOT = pathlib.Path(__file__).parent

FIXES = {
    "api/__init__.py": [
        ("Wallet(user_id=user.id,", "Wallet(user_id=user.telegram_id,"),
        ("user_id=user.id,", "user_id=user.telegram_id,"),
        ("await get_wallet(session, user.id)", "await get_wallet(session, user.telegram_id)"),
        ("await get_wallet(session, ref_user.id)", "await get_wallet(session, ref_user.telegram_id)"),
        ("wallet = await get_wallet(session, user.id)", "wallet = await get_wallet(session, user.telegram_id)"),
    ],
    "api/server.py": [
        ("await update_wallet(session, user.id,", "await update_wallet(session, user.telegram_id,"),
        ("wallet = await get_wallet(session, user.id)", "wallet = await get_wallet(session, user.telegram_id)"),
    ],
    "bot/__init__.py": [
        ("wallet = await get_wallet(session, user.id)", "wallet = await get_wallet(session, user.telegram_id)"),
        ("wallet = await get_wallet(session, user.id) if user else None", "wallet = await get_wallet(session, user.telegram_id) if user else None"),
    ],
}

for rel, pairs in FIXES.items():
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    changed = 0
    for old, new in pairs:
        n = s.count(old)
        if n:
            s = s.replace(old, new)
            changed += n
    p.write_text(s, encoding="utf-8")
    print(f"[ok] {rel}: {changed} id-references standardized")

import subprocess
ok = True
for rel in FIXES:
    r = subprocess.run(["python", "-m", "py_compile", rel], capture_output=True)
    if r.returncode != 0:
        ok = False
        print(f"[FAIL] compile {rel}")
print("ALL COMPILE OK" if ok else "COMPILE ERRORS")
