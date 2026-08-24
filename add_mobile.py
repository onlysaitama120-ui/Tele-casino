#!/usr/bin/env python3
"""Appends mobile optimization block to style.css."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "static" / "style.css"
NL = chr(10)

BLOCK = NL.join([
    "",
    "/* ============ MOBILE OPTIMIZATIONS ============ */",
    "html { -webkit-text-size-adjust: 100%; }",
    "body { -webkit-font-smoothing: antialiased; overscroll-behavior-y: contain; }",
    "",
    "#app { padding-left: max(16px, env(safe-area-inset-left)); padding-right: max(16px, env(safe-area-inset-right)); padding-bottom: calc(96px + env(safe-area-inset-bottom)); }",
    ".header { padding-top: max(8px, env(safe-area-inset-top)); }",
    ".bottom-nav { padding-bottom: max(8px, env(safe-area-inset-bottom)); }",
    ".modal { padding: max(24px, env(safe-area-inset-top)) 24px max(24px, env(safe-area-inset-bottom)); }",
    "",
    "button, .case-card, .game-tile, .inv-item, .daily-strip, .pill-btn, .lb-row {",
    "  user-select: none; -webkit-user-select: none; touch-action: manipulation;",
    "}",
    ".nav-btn, .cb, .bet-chips button, .f-btn { min-height: 44px; }",
    "",
    "@media (max-width: 380px) {",
    "  #app { padding-left:12px; padding-right:12px; }",
    "  .cases-grid, .games-grid { gap:9px; }",
    "  .case-card { padding:14px 10px; }",
    "  .case-emoji { font-size:36px; }",
    "  .gt-icon { font-size:26px; }",
    "  .title { font-size:22px; }",
    "  .coin-pill { padding:7px 12px; font-size:13px; }",
    "  .reel { width:70px; height:70px; font-size:38px; }",
    "  .wheel-wrap { width:160px; height:160px; }",
    "  .cb { font-size:13px; padding:14px 4px; }",
    "}",
    "",
    "@media (min-width: 460px) {",
    "  .cases-grid { grid-template-columns: repeat(4, 1fr); }",
    "  .games-grid { grid-template-columns: repeat(4, 1fr); }",
    "  .game-tile { text-align:center; }",
    "}",
    "",
    "@media (max-height: 480px) and (orientation: landscape) {",
    "  .wheel-wrap { width:130px; height:130px; margin:10px auto; }",
    "  .title { margin:4px 0 10px; font-size:20px; }",
    "  .slot-cabinet { padding:12px; }",
    "  .reel { width:64px; height:64px; font-size:34px; }",
    "}",
])

s = P.read_text(encoding="utf-8")
if "MOBILE OPTIMIZATIONS" in s:
    print("[skip] already present")
else:
    P.write_text(s + BLOCK + NL, encoding="utf-8")
    print("[ok] mobile block appended")
