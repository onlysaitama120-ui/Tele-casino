#!/usr/bin/env python3
"""Switch buttons back to native Telegram mini app mode."""
import pathlib

P = pathlib.Path(__file__).parent / "bot" / "__init__.py"
s = P.read_text(encoding="utf-8")

old = "url=config.WEBAPP_URL)"
new = "web_app=WebAppInfo(url=config.WEBAPP_URL))"

count = s.count(old)
if count:
    s = s.replace(old, new)
    P.write_text(s, encoding="utf-8")
print(f"[ok] {count} buttons -> native mini app")
