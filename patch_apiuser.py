#!/usr/bin/env python3
"""Fix /api/user to accept plain user_id (browser + telegram)."""
import pathlib

P = pathlib.Path(__file__).parent / "api" / "server.py"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

OLD = NL.join([
    "    data = await request.json()",
    "    init_data = data.get(" + DQ + "init_data" + DQ + ", " + DQ + DQ + ")",
    "    user_data = extract_user(init_data)",
    "",
    "    user_id = user_data.get(" + DQ + "id" + DQ + ")",
    "    if not user_id:",
    '        raise HTTPException(status_code=400, detail="Invalid user")',
])

NEW = NL.join([
    "    data = await request.json()",
    "    user_id = data.get(" + DQ + "user_id" + DQ + ")",
    "    user_data = data",
    "",
    "    if not user_id:",
    "        # fallback: try telegram init_data",
    "        init_data = data.get(" + DQ + "init_data" + DQ + ", " + DQ + DQ + ")",
    "        user_data = extract_user(init_data)",
    "        user_id = user_data.get(" + DQ + "id" + DQ + ")",
    "    if not user_id:",
    '        raise HTTPException(status_code=400, detail="No user identified")',
])

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] api_user patched - accepts user_id now")
elif "fallback: try telegram init_data" in s:
    print("[skip] already patched")
else:
    print("[fail] pattern drifted - showing current:")
    i = s.find("async def api_user")
    print(s[i:i+500])
