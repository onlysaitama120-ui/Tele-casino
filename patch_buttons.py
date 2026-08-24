#!/usr/bin/env python3
"""Swap web_app buttons -> url buttons (opens in external browser)."""
import pathlib

P = pathlib.Path(__file__).parent / "bot" / "__init__.py"
s = P.read_text(encoding="utf-8")

old = "web_app=WebAppInfo(url=config.WEBAPP_URL)"
new = "url=config.WEBAPP_URL"

count = s.count(old)
if count:
    s = s.replace(old, new)
    P.write_text(s, encoding="utf-8")
print(f"[ok] swapped {count} buttons to url mode")
