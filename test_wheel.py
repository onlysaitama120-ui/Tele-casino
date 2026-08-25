#!/usr/bin/env python3
"""Live test: wheel config + spin after deploy."""
import json
import time
import urllib.request

BASE = "https://tele-casino.onrender.com"


def req(path, body=None, timeout=90):
    url = BASE + path
    if body is None:
        r = urllib.request.urlopen(url, timeout=timeout)
        return json.loads(r.read())
    data = json.dumps(body).encode()
    req_obj = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        r = urllib.request.urlopen(req_obj, timeout=timeout)
        return json.loads(r.read())
    except Exception as e:
        try:
            return {"http_error": str(e), "body": e.read().decode()[:300]}
        except Exception:
            return {"http_error": str(e)}


print("waiting 170s for deploy...")
time.sleep(170)

print("=== WHEEL CONFIG ===")
cfg = req("/api/wheel/config")
if "segments" in cfg:
    print(f"segments: {len(cfg['segments'])} | cost: {cfg['spin_cost']} gems")
    for s in cfg["segments"]:
        print(f"  [{s['index']}] {s['emoji']} {s['label']} ({s['type']})")
else:
    print("config:", str(cfg)[:200])

print()
print("=== CREATE TEST USER ===")
u = req("/api/user", {"user_id": 555999, "username": "wheeltest"})
print("gems:", u.get("coins"))

print()
print("=== SPIN 1 (should be free daily) ===")
s1 = req("/api/wheel/spin", {"user_id": 555999})
if s1.get("success"):
    p = s1["prize"]
    print(f"landed seg {s1['segment']} | used={s1['used']} | prize={p['emoji']} {p['label']} ({p['type']}) | bal={s1['balance']}")
else:
    print("spin:", json.dumps(s1)[:300])

print()
print("=== SPIN 2 (gems, no bonus left) ===")
s2 = req("/api/wheel/spin", {"user_id": 555999})
if s2.get("success"):
    p = s2["prize"]
    print(f"landed seg {s2['segment']} | used={s2['used']} | prize={p['emoji']} {p['label']} | bal={s2['balance']}")
else:
    print("spin:", json.dumps(s2)[:300])

print()
print("=== STATUS ===")
st = req("/api/wheel/status", {"user_id": 555999})
print(json.dumps(st))
