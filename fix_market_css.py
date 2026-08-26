#!/usr/bin/env python3
"""Adds marketplace promo card CSS."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "static" / "style.css"
NL = chr(10)

CSS = NL.join([
    "",
    "/* ============ MARKET PROMO ============ */",
    ".market-promo {",
    "  display: flex; align-items: center; justify-content: space-between;",
    "  background: linear-gradient(135deg, rgba(56,189,248,.15), rgba(124,92,255,.1));",
    "  border: 1px solid rgba(56,189,248,.4); border-radius: 18px;",
    "  padding: 16px; cursor: pointer; margin-bottom: 10px; transition: transform .12s;",
    "}",
    ".market-promo:active { transform: scale(.985); }",
    ".mp-left { display: flex; gap: 12px; align-items: center; }",
    ".mp-icon { font-size: 32px; }",
    ".mp-left small { display: block; color: var(--dim); font-size: 11px; margin-top: 2px; }",
])

s = P.read_text(encoding="utf-8")
if "MARKET PROMO" not in s:
    P.write_text(s + NL + CSS, encoding="utf-8")
    print("[ok] market promo CSS added")
else:
    print("[skip] already present")
