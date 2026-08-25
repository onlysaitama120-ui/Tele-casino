#!/usr/bin/env python3
"""Welcome message now sends the GIFT RUSH banner photo."""
import pathlib

P = pathlib.Path(__file__).parent / "bot" / "__init__.py"
NL = chr(10)
DQ = chr(34)

s = P.read_text(encoding="utf-8")

OLD = (
    "    await message.answer(text, reply_markup=main_kb(), "
    'parse_mode="Markdown")'
)

NEW = NL.join([
    "    # banner + caption (falls back to text if photo fails)",
    "    photo_url = config.WEBAPP_URL + " + DQ + "/static/banner.png?v=1" + DQ,
    "    try:",
    "        await message.answer_photo(",
    "            photo=photo_url,",
    "            caption=text,",
    '            parse_mode="Markdown",',
    "            reply_markup=main_kb(),",
    "        )",
    "    except Exception:",
    "        await message.answer(text, reply_markup=main_kb(), ",
    'parse_mode="Markdown")',
])

if OLD in s:
    s = s.replace(OLD, NEW, 1)
    P.write_text(s, encoding="utf-8")
    print("[ok] /start now sends banner photo")
else:
    print("[warn] anchor drifted:")
    i = s.find("reply_markup=main_kb()")
    print(s[max(0,i-200):i+60])
