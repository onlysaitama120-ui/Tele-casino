#!/usr/bin/env python3
"""Fixes literal '/n' -> backslash-n escape sequences (correct way)."""
import pathlib

ROOT = pathlib.Path(__file__).parent
BS = chr(92)          # backslash
TARGET = "/n"          # broken literal in source
FIXED = BS + "n"       # proper /n escape

for rel in ["bot/__init__.py", "api/index.py", "api/server.py"]:
    p = ROOT / rel
    if not p.exists():
        continue
    s = p.read_text(encoding="utf-8")
    count = s.count(TARGET)
    if count:
        s = s.replace(TARGET, FIXED)
        p.write_text(s, encoding="utf-8")
    print(f"[ok] {rel}: {count} fixed")

# cache-bust
p = ROOT / "miniapp" / "index.html"
s = p.read_text(encoding="utf-8")
s = s.replace('href="/static/style.css"', 'href="/static/style.css?v=2"')
s = s.replace('src="/static/game.js"', 'src="/static/game.js?v=2"')
p.write_text(s, encoding="utf-8")
print("[ok] index.html cache-busted")

import subprocess
for rel in ["bot/__init__.py", "api/index.py", "api/server.py"]:
    r = subprocess.run(["python", "-m", "py_compile", rel], capture_output=True)
    print(f"[{'ok' if r.returncode == 0 else 'FAIL'}] compile {rel}")
