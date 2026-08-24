#!/usr/bin/env python3
"""Hardens game.js: fetch timeout + visible errors instead of silent hang."""
import pathlib

P = pathlib.Path(__file__).parent / "miniapp" / "static" / "game.js"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

# 1) fetch with 10s timeout
old_fetch = (
    "        const response = await fetch(endpoint, {"
)
new_fetch = NL.join([
    "        const controller = new AbortController();",
    "        const timer = setTimeout(() => controller.abort(), 10000);",
    "        const response = await fetch(endpoint, { signal: controller.signal,"
])
if old_fetch in s and "AbortController" not in s:
    s = s.replace(old_fetch, new_fetch, 1)
    # close: add clearTimeout after the fetch block's closing
    s = s.replace(
        "                body: JSON.stringify(data)" + NL + "        });",
        "                body: JSON.stringify(data)" + NL +
        "        });" + NL + "        clearTimeout(timer);", 1)
    print("[ok] fetch timeout added")
elif "AbortController" in s:
    print("[skip] timeout already present")

# 2) show real API errors on screen
old_err = (
    "    if (result.error) {" + NL +
    "        document.getElementById('loading').innerHTML = '<p>Error loading user data</p>';"
)
new_err = (
    "    if (result.error || !result.id) {" + NL +
    "        document.getElementById('loading').innerHTML = '<p style=" +
    DQ + "color:#ff5555;padding:20px" + DQ + ">API said: ' + JSON.stringify(result) + '</p>';"
)
if old_err in s:
    s = s.replace(old_err, new_err, 1)
    print("[ok] error display patched")
elif "API said:" in s:
    print("[skip] error display already present")
else:
    print("[warn] error pattern not found")

P.write_text(s, encoding="utf-8")
print("[done] game.js saved")
