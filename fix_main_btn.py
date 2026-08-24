#!/usr/bin/env python3
"""Fix main Play Casino button -> native mini app."""
import pathlib

P = pathlib.Path(__file__).parent / "bot" / "__init__.py"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

OLD = NL.join([
    "        [InlineKeyboardButton(",
    "            text=" + DQ + "🎰 Play Casino" + DQ + ",",
    "            url=config.WEBAPP_URL",
    "        )],",
])

NEW = NL.join([
    "        [InlineKeyboardButton(",
    "            text=" + DQ + "🎰 Play Casino" + DQ + ",",
    "            web_app=WebAppInfo(url=config.WEBAPP_URL)",
    "        )],",
])

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] main button -> native mini app")
elif "url=config.WEBAPP_URL" not in s:
    print("[skip] already native")
else:
    # fallback: simple line-level fix
    lines = s.split(NL)
    for i, l in enumerate(lines):
        if "url=config.WEBAPP_URL" in l and "Play Casino" in (lines[i-1] or ""):
            indent = l[:len(l) - len(l.lstrip())]
            lines[i] = indent.replace("text=", "text=") if False else l.replace("url=config.WEBAPP_URL", "web_app=WebAppInfo(url=config.WEBAPP_URL))")
            # remove one closing paren imbalance by wrapping
            lines[i] = lines[i].replace(
                "url=config.WEBAPP_URL)",
                "web_app=WebAppInfo(url=config.WEBAPP_URL)))"
            ).replace(
                "web_app=WebAppInfo(url=config.WEBAPP_URL))))",
                "web_app=WebAppInfo(url=config.WEBAPP_URL)))"
            )
            removed = True
    P.write_text(NL.join(lines), encoding="utf-8")
    print("[ok] fallback line-fix applied")
