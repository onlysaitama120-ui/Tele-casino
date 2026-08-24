#!/usr/bin/env python3
"""Adds missing .deposit-banner styles + bumps css cache."""
import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)

# 1) CSS fix
css_p = ROOT / "miniapp" / "static" / "style.css"
s = css_p.read_text(encoding="utf-8")

if ".deposit-banner" not in s:
    block = NL.join([
        "",
        "/* ---------- deposit banner ---------- */",
        ".deposit-banner {",
        "  display:flex; align-items:center; justify-content:space-between;",
        "  background:linear-gradient(135deg,rgba(124,92,255,.18),rgba(56,189,248,.09));",
        "  border:1px solid rgba(124,92,255,.45); border-radius:18px;",
        "  padding:14px 16px; cursor:pointer; margin-bottom:12px;",
        "  transition:transform .15s;",
        "}",
        ".deposit-banner:active { transform:scale(.98); }",
        ".claim-btn.dep {",
        "  background:linear-gradient(135deg,#7c5cff,#38bdf8);",
        "  color:#fff; flex:none;",
        "}",
    ])
    css_p.write_text(s + NL + block + NL, encoding="utf-8")
    print("[ok] deposit-banner styles added")
else:
    print("[skip] banner css exists")

# 2) bump cache versions v=5 -> v=6
html_p = ROOT / "miniapp" / "index.html"
h = html_p.read_text(encoding="utf-8")
h = h.replace("style.css?v=5", "style.css?v=6")
html_p.write_text(h, encoding="utf-8")
print("[ok] cache bumped to v6")
