#!/usr/bin/env python3
"""Appends wheel styles to style.css."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "static" / "style.css"
NL = chr(10)

BLOCK = NL.join([
    "",
    "/* ============ GIFT WHEEL ============ */",
    ".wheel-hero {",
    "  display:flex; align-items:center; justify-content:space-between;",
    "  background:linear-gradient(135deg, rgba(124,92,255,.22), rgba(255,213,74,.12));",
    "  border:1px solid rgba(124,92,255,.5); border-radius:18px;",
    "  padding:16px; margin-bottom:14px; cursor:pointer;",
    "  box-shadow:0 6px 24px rgba(124,92,255,.25);",
    "}",
    ".wheel-hero:active { transform:scale(.98); }",
    ".wh-left { display:flex; gap:12px; align-items:center; }",
    ".wh-icon { font-size:34px; }",
    ".wh-left small { display:block; color:var(--dim); font-size:12px; }",
    ".wh-btn { background:linear-gradient(135deg,#7c5cff,#38bdf8); color:#fff; }",
    "",
    ".wheel-stage { position:relative; width:280px; height:340px; margin:10px auto 6px; }",
    "",
    ".big-wheel {",
    "  position:absolute; top:20px; left:50%; margin-left:-140px;",
    "  width:280px; height:280px; border-radius:50%;",
    "  border:8px solid var(--gold);",
    "  box-shadow:0 0 44px rgba(255,183,0,.35), inset 0 0 30px rgba(0,0,0,.65);",
    "  transition:transform 4.2s cubic-bezier(.15,.82,.16,1);",
    "  overflow:hidden;",
    "}",
    ".seg-label {",
    "  position:absolute; left:50%; top:50%; transform-origin:0 0;",
    "  font-size:13px; font-weight:900; white-space:nowrap;",
    "  text-shadow:0 1px 3px #000;",
    "}",
    "",
    ".wheel-pointer {",
    "  position:absolute; top:-2px; left:50%; transform:translateX(-50%);",
    "  font-size:30px; color:var(--gold); z-index:5;",
    "  filter:drop-shadow(0 3px 6px rgba(0,0,0,.7));",
    "}",
    "",
    ".wheel-hub {",
    "  position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);",
    "  width:86px; height:86px; border-radius:50%; z-index:4;",
    "  background:linear-gradient(135deg,var(--gold),var(--gold2));",
    "  display:flex; align-items:center; justify-content:center;",
    "  font-weight:900; font-size:15px; letter-spacing:1px; color:#231a00;",
    "  cursor:pointer; border:5px solid #fff3;",
    "  box-shadow:0 6px 22px rgba(0,0,0,.55);",
    "  transition:transform .12s;",
    "}",
    ".wheel-hub:active { transform:translate(-50%,-50%) scale(.93); }",
    ".wheel-hub.spinning { pointer-events:none; opacity:.75; }",
    "",
    ".wheel-status { text-align:center; color:var(--dim); font-size:13px; margin-top:12px; }",
])

s = P.read_text(encoding="utf-8")
if "GIFT WHEEL" in s:
    print("[skip] wheel css exists")
else:
    P.write_text(s + BLOCK + NL, encoding="utf-8")
    print("[ok] wheel styles appended")
