#!/usr/bin/env python3
"""Generates the GIFT RUSH welcome banner with PIL."""
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
GOLD = (255, 213, 74)
GOLD_DEEP = (255, 143, 0)
BG_TOP = (11, 14, 26)
BG_BOT = (19, 26, 46)

img = Image.new("RGB", (W, H), BG_TOP)
d = ImageDraw.Draw(img)

# ---- vertical gradient ----
for y in range(H):
    t = y / H
    r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t)
    g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t)
    b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t)
    d.line([(0, y), (W, y)], fill=(r, g, b))

# ---- radial gold glow behind title ----
glow = Image.new("L", (W, H), 0)
gd = ImageDraw.Draw(glow)
cx, cy, rad = W // 2, int(H * 0.38), 420
for i in range(rad, 0, -4):
    a = int(90 * (1 - i / rad))
    gd.ellipse([cx - i * 1.4, cy - i * 0.8, cx + i * 1.4, cy + i * 0.8], fill=a)
glow = glow.filter(ImageFilter.GaussianBlur(60))
gold_layer = Image.new("RGB", (W, H), GOLD)
img.paste(gold_layer, (0, 0), glow)

d = ImageDraw.Draw(img)

# ---- purple side glows ----
glow2 = Image.new("L", (W, H), 0)
g2 = ImageDraw.Draw(glow2)
g2.ellipse([-200, H - 260, 320, H + 160], fill=70)
g2.ellipse([W - 320, -180, W + 200, 220], fill=55)
glow2 = glow2.filter(ImageFilter.GaussianBlur(80))
purple = Image.new("RGB", (W, H), (124, 92, 255))
img.paste(purple, (0, 0), glow2)

d = ImageDraw.Draw(img)

# ---- decorative diamonds (confetti-ish) ----
random.seed(42)
colors = [GOLD, (124, 92, 255), (56, 189, 248), (57, 211, 83), (255, 82, 82)]
for _ in range(46):
    x = random.randint(30, W - 30)
    y = random.randint(30, H - 30)
    s = random.randint(5, 13)
    col = random.choice(colors)
    op = random.randint(60, 150)
    poly = [(x, y - s), (x + s, y), (x, y + s), (x - s, y)]
    d.polygon(poly, outline=col, width=2)

# thin gold frame
m = 22
d.rounded_rectangle([m, m, W - m, H - m], radius=28, outline=(212, 175, 55), width=3)
d.rounded_rectangle([m + 8, m + 8, W - m - 8, H - m - 8], radius=22, outline=(212, 175, 55, 90), width=1)

# ---- fonts ----
def load_font(size, bold=True):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/ArialBD.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

f_title = load_font(150)
f_sub = load_font(44)
f_tag = load_font(30)
f_small = load_font(24)

def center_text(y, text, font, fill):
    bbox = d.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    d.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]

# ---- title with layered shadow + glow ----
title = "GIFT RUSH"
tb = d.textbbox((0, 0), title, font=f_title)
tw = tb[2] - tb[0]
tx = (W - tw) // 2
ty = int(H * 0.30)

# soft outer glow
glow_txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gt = ImageDraw.Draw(glow_txt)
gt.text((tx, ty), title, font=f_title, fill=(255, 213, 74, 200))
glow_txt = glow_txt.filter(ImageFilter.GaussianBlur(18))
img.paste(Image.new("RGB", (W, H), GOLD), (0, 0), glow_txt.split()[3].point(lambda a: min(a, 130)))
d = ImageDraw.Draw(img)

# dark drop shadow
d.text((tx + 6, ty + 8), title, font=f_title, fill=(0, 0, 0))

# gold gradient effect: draw twice slightly offset
d.text((tx, ty), title, font=f_title, fill=GOLD_DEEP)
d.text((tx, ty - 3), title, font=f_title, fill=GOLD)

# ---- divider lines ----
ly = ty + 190
d.line([(W // 2 - 330, ly), (W // 2 - 40, ly)], fill=GOLD, width=3)
d.line([(W // 2 + 40, ly), (W // 2 + 330, ly)], fill=GOLD, width=3)
dd = 10
d.polygon([(W//2, ly-dd), (W//2+dd, ly), (W//2, ly+dd), (W//2-dd, ly)], outline=GOLD, width=2)

# ---- subtitle ----
center_text(ly + 34, "COLLECT  ·  FUSE  ·  FLEX", f_sub, (238, 241, 255))

# ---- tagline ----
center_text(int(H * 0.72), "MYSTERY BOXES   •   RARE NFT GIFTS   •   TON REWARDS", f_tag, (139, 147, 181))

# ---- bottom badge ----
badge = "PLAY INSIDE TELEGRAM"
bb = d.textbbox((0, 0), badge, font=f_small)
bw = bb[2] - bb[0]
bx, by = (W - bw) // 2, int(H * 0.84)
d.rounded_rectangle([bx - 26, by - 14, bx + bw + 26, by + bb[3] + 18],
                    radius=24, fill=(124, 92, 255))
d.text((bx, by), badge, font=f_small, fill=(255, 255, 255))

img.save("miniapp/static/banner.png", optimize=True)
print("[ok] banner saved:", img.size)
