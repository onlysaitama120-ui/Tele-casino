#!/usr/bin/env python3
"""Removes the dangling 'try {' after initUser (handles CRLF)."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "static" / "game.js"

s = P.read_text(encoding="utf-8")
lines = s.split(chr(10))

out = []
removed = False
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped == "try {" and not removed:
        # check previous non-empty out line is initUser def
        prev = out[-1].strip() if out else ""
        if "async function initUser" in prev:
            removed = True
            print(f"[ok] removed stray try at source line {i+1}")
            continue
    out.append(line)

if removed:
    P.write_text(chr(10).join(out), encoding="utf-8")
else:
    print("[skip] no stray try found")
