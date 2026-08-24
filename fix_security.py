#!/usr/bin/env python3
"""
SECURITY AUDIT PATCHER - GIFT RUSH
Fixes critical exploits found in recon:
  X1 negative-bet free gems (roulette/slots)
  X2 marketplace negative-price self-pay
  X3 fusion infinite-money-print (ingredients not consumed)
  X4 withdrawal item deletion by-name collision -> by stored id
  X5 public withdrawal queue -> admin gated
  X6 rate limiting on money endpoints
  X7 optional Telegram initData strict auth (STRICT_AUTH=1)
"""

import pathlib

ROOT = pathlib.Path(__file__).parent
NL = chr(10)
DQ = chr(34)


def rd(p):
    return (ROOT / p).read_text(encoding="utf-8")


def wr(p, s):
    (ROOT / p).write_text(s, encoding="utf-8")


def rep(p, old, new, label, required=True):
    s = rd(p)
    if new in s and old not in s:
        print(f"[skip] {p}: {label}")
        return False
    if old not in s:
        msg = f"[warn] {p}: {label} - anchor missing"
        print(msg)
        if required:
            raise SystemExit(msg)
        return False
    wr(p, s.replace(old, new, 1))
    print(f"[ok]   {p}: {label}")
    return True


# ============================================================
# X1 ROULETTE + SLOTS negative / non-int bets
# ============================================================

F = "api/__init__.py"

rep(F,
    '    if bet < config.ROULETTE[' + DQ + 'min_bet' + DQ + '] or bet > config.ROULETTE[' + DQ + 'max_bet' + DQ + ']:',
    NL.join([
        '    try:',
        '        bet = int(bet)',
        '    except Exception:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Invalid bet' + DQ + '}',
        '    if bet <= 0:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Invalid bet' + DQ + '}',
        '    if bet < config.ROULETTE[' + DQ + 'min_bet' + DQ + '] or bet > config.ROULETTE[' + DQ + 'max_bet' + DQ + ']:',
    ]),
    "X1 roulette bet hardening")

rep(F,
    '    if bet < config.SLOTS[' + DQ + 'min_bet' + DQ + '] or bet > config.SLOTS[' + DQ + 'max_bet' + DQ + ']:',
    NL.join([
        '    try:',
        '        bet = int(bet)',
        '    except Exception:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Invalid bet' + DQ + '}',
        '    if bet <= 0:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Invalid bet' + DQ + '}',
        '    if bet < config.SLOTS[' + DQ + 'min_bet' + DQ + '] or bet > config.SLOTS[' + DQ + 'max_bet' + DQ + ']:',
    ]),
    "X1 slots bet hardening")

# ============================================================
# X3 FUSION consumes ingredients (kills infinite gem printer)
# ============================================================

OLD_BREED = NL.join([
    "        session.add(new_item)",
    "",
    "        # Update breed counts",
    "        item1.breed_count += 1",
    "        item2.breed_count += 1",
    "        item1.last_breed = now",
    "        item2.last_breed = now",
])

NEW_BREED = NL.join([
    "        session.add(new_item)",
    "",
    "        # SECURITY: consume ingredients (prevents infinite gem printing)",
    "        await session.delete(item1)",
    "        await session.delete(item2)",
])

rep(F, OLD_BREED, NEW_BREED, "X3 fusion consumes ingredients")

# ============================================================
# X2 MARKETPLACE negative-price self-pay
# ============================================================

rep(F,
    '    if item.is_locked:' + NL +
    '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Item is locked' + DQ + '}' + NL +
    '',
    NL.join([
        '    if item.is_locked:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Item is locked' + DQ + '}',
        '',
        '    try:',
        '        price = int(price)',
        '    except Exception:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Invalid price' + DQ + '}',
        '    if price <= 0 or price > 10000000:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Price must be 1-10,000,000' + DQ + '}',
        '',
    ]),
    "X2 list price validation")

rep(F,
    '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Cannot buy your own item' + DQ + '}',
    NL.join([
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Cannot buy your own item' + DQ + '}',
        '',
        '    if listing.price <= 0:',
        '        return {' + DQ + 'success' + DQ + ': False, ' + DQ + 'message' + DQ + ': ' + DQ + 'Invalid listing' + DQ + '}',
    ]),
    "X2 buy-side price guard")

# ============================================================
# X4 withdrawals reference exact item id
# ============================================================

D = "api/deposits.py"
rep(D,
    '    item_value = Column(Integer, default=0)',
    '    item_value = Column(Integer, default=0)' + NL +
    '    item_id = Column(Integer, nullable=True)',
    "X4 WithdrawRequest.item_id column")

DP = "api/deposits.py"
rep(DP,
    '        item_value=item.value,',
    '        item_value=item.value,' + NL +
    '        item_id=item.id,',
    "X4 store item_id on request")

OLD_DEL = NL.join([
    "    it = await session.execute(",
    "        select(InventoryItem).where(",
    "            InventoryItem.item_name == wr.item_name,",
    "            InventoryItem.is_locked == True,",
    "        )",
    "    )",
    "    inv_item = it.scalars().first()",
    "    if inv_item:",
    "        await session.delete(inv_item)",
])
NEW_DEL = NL.join([
    "    if wr.item_id:",
    "        it = await session.execute(",
    "            select(InventoryItem).where(InventoryItem.id == wr.item_id)",
    "        )",
    "        inv_item = it.scalar_one_or_none()",
    "        if inv_item:",
    "            await session.delete(inv_item)",
])
rep(DP, OLD_DEL, NEW_DEL, "X4 delete by exact item id")

# ============================================================
# X5 admin-gate the withdrawal queue + X6 rate limiter + X7 strict auth
# ============================================================

S = "api/server.py"

# rate limiter helper after CORS block
rep(S,
    '    allow_headers=["*"],' + NL + ')',
    NL.join([
        '    allow_headers=["*"],',
        ')',
        '',
        '# ---- naive per-user rate limiter (money endpoints) ----',
        '_RL = {}',
        'import time as _time',
        'def _rl(uid, ep, min_gap=1.2):',
        '    key = (uid, ep)',
        '    now = _time.time()',
        '    if now - _RL.get(key, 0) < min_gap:',
        '        raise HTTPException(status_code=429, detail=' + DQ + 'Slow down' + DQ + ')',
        '    _RL[key] = now',
    ]),
    "X6 rate limiter helper")

# inject rl calls per endpoint
rep(S,
    '    case_id = data.get(' + DQ + 'case_id' + DQ + ')',
    '    case_id = data.get(' + DQ + 'case_id' + DQ + ')',
    "noop-case-anchor", required=False)
s = rd(S)
anchor = '    user_id = data.get(' + DQ + 'user_id' + DQ + ')' + NL + '    case_id = data.get(' + DQ + 'case_id' + DQ + ')'
if '_rl(user_id, "case")' not in s:
    s = s.replace(anchor,
        anchor + NL + '    _rl(user_id, ' + DQ + 'case' + DQ + ')', 1)
    print("[ok]   rl: case")
anchor2 = '    color = data.get(' + DQ + 'color' + DQ + ', ' + DQ + 'red' + DQ + ')'
if '_rl(user_id, "roul")' not in s:
    s = s.replace(anchor2, anchor2 + NL + '    _rl(user_id, ' + DQ + 'roul' + DQ + ')', 1)
    print("[ok]   rl: roulette")
anchor3 = '    bet = data.get(' + DQ + 'bet' + DQ + ', 25)'
if '_rl(user_id, "slots")' not in s:
    s = s.replace(anchor3, anchor3 + NL + '    _rl(user_id, ' + DQ + 'slots' + DQ + ')', 1)
    print("[ok]   rl: slots")
anchor4 = '    listing_id = data.get(' + DQ + 'listing_id' + DQ + ')'
if '_rl(user_id, "buy")' not in s:
    s = s.replace(anchor4, anchor4 + NL + '    _rl(user_id, ' + DQ + 'buy' + DQ + ')', 1)
    print("[ok]   rl: buy")
wr_anchor = '    item_id = data.get(' + DQ + 'item_id' + DQ + ')' + NL + '    if not user_id or not item_id:'
if '_rl(user_id, "wd")' not in s:
    s = s.replace(wr_anchor,
        '    item_id = data.get(' + DQ + 'item_id' + DQ + ')' + NL +
        '    _rl(user_id, ' + DQ + 'wd' + DQ + ', 3.0)' + NL +
        '    if not user_id or not item_id:', 1)
    print("[ok]   rl: withdraw")
wr(S, s)

# X5 admin gate on queue listing
rep(S,
    '@app.get(' + DQ + '/api/withdrawals' + DQ + ')' + NL +
    'async def api_withdrawals():' + NL +
    '    async with async_session() as session:' + NL +
    '        return {' + DQ + 'requests' + DQ + ': await list_withdrawals(session)}',
    NL.join([
        '@app.get(' + DQ + '/api/withdrawals' + DQ + ')',
        'async def api_withdrawals(request: Request):',
        '    try:',
        '        admin_id = int(request.query_params.get(' + DQ + 'admin_id' + DQ + ', ' + DQ + '0' + DQ + '))',
        '    except Exception:',
        '        admin_id = 0',
        '    if admin_id not in config.ADMIN_IDS:',
        '        raise HTTPException(status_code=403, detail=' + DQ + 'Unauthorized' + DQ + ')',
        '    async with async_session() as session:',
        '        return {' + DQ + 'requests' + DQ + ': await list_withdrawals(session)}',
    ]),
    "X5 admin gate on withdrawals")

# X7 strict auth option on identity endpoint
rep(S,
    '    data = await request.json()' + NL +
    '    user_id = data.get(' + DQ + 'user_id' + DQ + ')' + NL +
    '    user_data = data',
    NL.join([
        '    data = await request.json()',
        '    if os.environ.get(' + DQ + 'STRICT_AUTH' + DQ + ') == ' + DQ + '1' + DQ + ':',
        '        init_data = data.get(' + DQ + 'init_data' + DQ + ', ' + DQ + DQ + ')',
        '        if not init_data or not verify_init_data(init_data):',
        '            raise HTTPException(status_code=401, detail=' + DQ + 'Telegram auth required' + DQ + ')',
        '    user_id = data.get(' + DQ + 'user_id' + DQ + ')',
        '    user_data = data',
    ]),
    "X7 strict auth hook")

print()
print("SECURITY PATCH COMPLETE")
