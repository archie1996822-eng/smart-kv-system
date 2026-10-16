"""逐帧渲染 9:16 画面（PIL），多进程分段编码，再与混音合成成片。

用法：python3 render.py [--preview 秒,秒,...] [--workers N]
"""
import argparse
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from character import sprite
from script import DURATION, FPS, H, LINES, SCENES, W, YEAR_CARDS

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
OUT = ROOT / "out"

NAVY0 = (6, 16, 36)
NAVY1 = (14, 36, 72)
ORANGE = (255, 138, 61)
AMBER = (255, 196, 107)
WHITE = (244, 246, 250)
GREY = (150, 162, 186)
CYAN = (120, 200, 255)
RED = (232, 72, 56)

FONT_DIR = "/usr/share/fonts/opentype/noto"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


# ---------------------------------------------------------------- 基础工具
@lru_cache(maxsize=None)
def font(size, weight="Bold"):
    return ImageFont.truetype(f"{FONT_DIR}/NotoSansCJK-{weight}.ttc", size, index=2)


@lru_cache(maxsize=None)
def mono(size):
    return ImageFont.truetype(MONO, size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 3 * x * x - 2 * x * x * x


def back_out(x):
    x = clamp(x)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def window(t, a, b, fade_in=0.4, fade_out=0.4):
    """在 [a, b] 内为 1，两端淡入淡出。"""
    return min(prog(t, a, a + fade_in), 1 - prog(t, b - fade_out, b))


def lerp(a, b, x):
    return a + (b - a) * x


def rgba(c, a):
    return (c[0], c[1], c[2], int(clamp(a) * 255))


@lru_cache(maxsize=2048)
def text_img(text, size, weight="Bold", fill=WHITE, stroke=0, stroke_fill=(0, 0, 0),
             glow=0, glow_fill=ORANGE, mono_font=False, spacing=0):
    f = mono(size) if mono_font else font(size, weight)
    if spacing:
        widths = [f.getbbox(ch)[2] for ch in text]
        tw = sum(widths) + spacing * (len(text) - 1)
    else:
        tw = int(f.getlength(text))
    asc, desc = f.getmetrics()
    pad = stroke + glow * 3 + 4
    img = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def draw_on(dr, color, sw, sf):
        if spacing:
            x = pad
            for ch, wch in zip(text, widths):
                dr.text((x, pad), ch, font=f, fill=color, stroke_width=sw, stroke_fill=sf)
                x += wch + spacing
        else:
            dr.text((pad, pad), text, font=f, fill=color, stroke_width=sw, stroke_fill=sf)

    if glow:
        g = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw_on(ImageDraw.Draw(g), glow_fill + (255,), stroke + 2, glow_fill + (255,))
        g = g.filter(ImageFilter.GaussianBlur(glow))
        img.alpha_composite(g)
        img.alpha_composite(g)
    draw_on(d, fill + (255,) if len(fill) == 3 else fill, stroke, stroke_fill)
    return img


def blit(canvas, img, cx, cy, alpha=1.0, scale=1.0, anchor="mm"):
    if alpha <= 0.003:
        return
    if abs(scale - 1) > 1e-3:
        nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
        img = img.resize((nw, nh), Image.BILINEAR)
    if alpha < 0.997:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    x = cx - img.width / 2 if anchor[0] == "m" else (cx if anchor[0] == "l" else cx - img.width)
    y = cy - img.height / 2 if anchor[1] == "m" else (cy if anchor[1] == "t" else cy - img.height)
    canvas.paste(img, (int(round(x)), int(round(y))), img)


def text(canvas, s, cx, cy, size, weight="Bold", fill=WHITE, alpha=1.0, scale=1.0,
         anchor="mm", **kw):
    blit(canvas, text_img(s, size, weight, fill, **kw), cx, cy, alpha, scale, anchor)


def chip(canvas, d, s, cx, cy, size=40, fg=WHITE, bg=(20, 34, 64), border=ORANGE, alpha=1.0,
         weight="Bold"):
    if alpha <= 0.003:
        return
    im = text_img(s, size, weight, fg)
    w, h = im.width + 36, size + 34
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=h / 2,
                        fill=rgba(bg, 0.85 * alpha), outline=rgba(border, alpha), width=3)
    blit(canvas, im, cx, cy - 2, alpha)


@lru_cache(maxsize=1)
def background():
    y = np.linspace(0, 1, H)[:, None, None]
    x = np.linspace(-1, 1, W)[None, :, None]
    c0, c1 = np.array(NAVY0, float), np.array(NAVY1, float)
    grad = c0 * (1 - y) + c1 * y
    grad = grad + 0 * x
    r = np.sqrt((x * 0.9) ** 2 + ((y - 0.45) * 1.6) ** 2)
    vig = np.clip(1.15 - 0.55 * r, 0.35, 1.1)
    img = np.clip(grad * vig, 0, 255).astype(np.uint8)
    return Image.fromarray(img, "RGB")


@lru_cache(maxsize=8)
def radial(radius, color, strength=1.0):
    s = radius * 2
    yy, xx = np.mgrid[0:s, 0:s]
    r = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1 - r, 0, 1) ** 2 * 255 * strength
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = a.astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def glow(canvas, cx, cy, radius, color, alpha):
    blit(canvas, radial(radius, color), cx, cy, alpha)


PARTICLES = np.random.default_rng(3).uniform(0, 1, (70, 4))


def particles(d, t, alpha=1.0, color=AMBER):
    for px, py, sp, sz in PARTICLES:
        x = (px * W + math.sin(t * 0.3 + py * 9) * 30) % W
        y = (py * H - t * (12 + sp * 30)) % H
        r = 1.5 + sz * 3
        d.ellipse([x - r, y - r, x + r, y + r], fill=rgba(color, (0.12 + 0.25 * sz) * alpha))


def dim(d, a, color=(0, 0, 0)):
    if a > 0.003:
        d.rectangle([0, 0, W, H], fill=rgba(color, a))


# ---------------------------------------------------------------- 数据
def load_lines():
    out = {}
    for line_id, kind, start, txt in LINES:
        meta = json.loads((BUILD / "tts" / f"{line_id}.json").read_text())
        out[line_id] = dict(kind=kind, start=start, text=txt, words=meta["words"],
                            dur=meta["duration"])
    return out


LINE_DATA = None
CHAR_ENV = None


def init_data():
    global LINE_DATA, CHAR_ENV
    LINE_DATA = load_lines()
    CHAR_ENV = np.load(BUILD / "char_env.npy")


def word_time(line_id, needle):
    ln = LINE_DATA[line_id]
    for w in ln["words"]:
        if needle in w["text"] or w["text"] in needle and len(w["text"]) > 1:
            return ln["start"] + w["t"]
    acc = ""
    for w in ln["words"]:
        acc += w["text"]
        if needle in acc:
            return ln["start"] + w["t"]
    return ln["start"]


PUNCT = "，。？！；：、——「」"


def subtitle_chunks(line_id):
    """把一句按标点切成字幕块，用逐词时间戳定时。"""
    ln = LINE_DATA[line_id]
    txt = ln["text"]
    chunks, cur = [], ""
    for ch in txt:
        if ch in "，。？！；：":
            if cur.strip():
                chunks.append(cur.strip())
            cur = ""
        elif ch == "—":
            if cur.strip():
                chunks.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        chunks.append(cur.strip())
    plain = lambda s: "".join(c for c in s if c not in PUNCT + " ")
    words = ln["words"]
    pos = []
    acc = 0
    for w in words:
        pos.append(acc)
        acc += len(plain(w["text"]))
    res = []
    ci = 0
    for c in chunks:
        target = ci
        st = ln["start"]
        for w, p in zip(words, pos):
            if p >= target:
                st = ln["start"] + w["t"]
                break
        res.append([c, st])
        ci += len(plain(c))
    end = ln["start"] + ln["dur"]
    for i in range(len(res)):
        res[i].append(res[i + 1][1] if i + 1 < len(res) else end + 0.25)
    return res


# ---------------------------------------------------------------- 人物
def char_frame(t):
    i = int(t * FPS)
    return CHAR_ENV[i] if 0 <= i < len(CHAR_ENV) else 0.0


def draw_char(canvas, stage, cx, cy, scale, t, alpha=1.0, speaking=False, eyes=None, mouth=None):
    if alpha <= 0.003:
        return
    if mouth is None:
        mouth = 0
        if speaking:
            e = math.sqrt(char_frame(t))
            mouth = 0 if e < 0.22 else (1 if e < 0.5 else 2)
    if eyes is None:
        ph = (t + stage * 0.7) % 3.6
        eyes = "blink" if ph < 0.12 else "open"
    sp = sprite(stage, mouth, eyes)
    bob = math.sin(t * 1.8 + stage) * 4 * scale
    # 精灵图头部中心在 (300, 340)，此处以头部中心定位
    ox = (sp.width / 2 - 300) * scale
    oy = (sp.height / 2 - 340) * scale
    blit(canvas, sp, cx + ox, cy + oy + bob, alpha, scale)


# ---------------------------------------------------------------- 通用元件
TL_X0, TL_X1, TL_Y = 130, 950, 238


def timeline(canvas, d, t):
    a = 1 - prog(t, 98.0, 98.8)
    if a <= 0:
        return
    xs = np.linspace(TL_X0, TL_X1, len(YEAR_CARDS))
    d.line([TL_X0, TL_Y, TL_X1, TL_Y], fill=rgba(GREY, 0.35 * a), width=3)
    active = [i for i, (ct, *_) in enumerate(YEAR_CARDS) if t >= ct]
    if active:
        last = active[-1]
        d.line([TL_X0, TL_Y, xs[last], TL_Y], fill=rgba(ORANGE, 0.9 * a), width=4)
    for i, (ct, yr, _) in enumerate(YEAR_CARDS):
        on = t >= ct
        r = 9 if on else 6
        if on and i == (active[-1] if active else -1):
            pr = (t - ct) % 1.6 / 1.6
            d.ellipse([xs[i] - 10 - 18 * pr, TL_Y - 10 - 18 * pr, xs[i] + 10 + 18 * pr,
                       TL_Y + 10 + 18 * pr], outline=rgba(ORANGE, (1 - pr) * 0.7 * a), width=3)
        d.ellipse([xs[i] - r, TL_Y - r, xs[i] + r, TL_Y + r],
                  fill=rgba(ORANGE if on else (60, 74, 104), a))
        text(canvas, yr, xs[i], TL_Y + 36, 26, "Bold", ORANGE if on else GREY, alpha=a)
    text(canvas, "人物科普", 70, 150, 30, "Bold", AMBER, alpha=a * 0.9, anchor="lm")
    text(canvas, "从仙桃机房到千万台手机", 1010, 150, 26, "Medium", GREY, alpha=a * 0.8, anchor="rm")


def year_card(canvas, d, t):
    for ct, yr, sub in YEAR_CARDS:
        lt = t - ct
        if not (0 <= lt <= 2.6):
            continue
        a = min(prog(lt, 0, 0.3), 1 - prog(lt, 2.1, 2.6))
        sc = lerp(1.35, 1.0, ease_out(prog(lt, 0, 0.45)))
        y = 470 - 30 * ease_in_out(prog(lt, 2.1, 2.6))
        glow(canvas, 540, y, 330, ORANGE, 0.22 * a)
        text(canvas, yr, 540, y, 190, "Black", ORANGE, alpha=a, scale=sc, glow=10,
             glow_fill=(255, 110, 40), spacing=8)
        wline = 360 * ease_out(prog(lt, 0.2, 0.7))
        d.line([540 - wline, y + 112, 540 + wline, y + 112], fill=rgba(AMBER, 0.8 * a), width=3)
        text(canvas, sub, 540, y + 165, 50, "Bold", WHITE, alpha=a * prog(lt, 0.25, 0.6))


SUB_Y = 1405


def subtitles(canvas, d, t):
    for line_id, ln in LINE_DATA.items():
        if not (ln["start"] - 0.1 <= t <= ln["start"] + ln["dur"] + 0.4):
            continue
        if line_id == "n11" and t > 98.6:
            continue
        for chunk, st, en in subtitle_chunks(line_id):
            if not (st - 0.05 <= t < en):
                continue
            a = min(prog(t, st - 0.05, st + 0.1), 1 - prog(t, en - 0.08, en))
            if ln["kind"] == "c":
                s = f"「{chunk}」"
                im = text_img(s, 66, "Black", AMBER, stroke=3, stroke_fill=(40, 20, 0))
                w, h = im.width + 50, 120
                d.rounded_rectangle([540 - w / 2, SUB_Y - h / 2, 540 + w / 2, SUB_Y + h / 2],
                                    radius=24, fill=rgba((24, 16, 8), 0.72 * a),
                                    outline=rgba(ORANGE, 0.9 * a), width=3)
                blit(canvas, im, 540, SUB_Y - 4, a)
            else:
                im = text_img(chunk, 56, "Bold", WHITE, stroke=3, stroke_fill=(6, 12, 28))
                w, h = im.width + 44, 96
                d.rounded_rectangle([540 - w / 2, SUB_Y - h / 2, 540 + w / 2, SUB_Y + h / 2],
                                    radius=20, fill=rgba((4, 10, 24), 0.55 * a))
                blit(canvas, im, 540, SUB_Y - 4, a)


def caption(canvas, d, s, t, a0, a1, y=SUB_Y, size=48):
    """画面字（无旁白段的说明字）。"""
    a = window(t, a0, a1, 0.3, 0.3)
    if a <= 0:
        return
    im = text_img(s, size, "Bold", AMBER)
    w, h = im.width + 60, size + 44
    yy = y + 16 * (1 - ease_out(prog(t, a0, a0 + 0.4)))
    d.rounded_rectangle([540 - w / 2, yy - h / 2, 540 + w / 2, yy + h / 2], radius=12,
                        fill=rgba((4, 10, 24), 0.6 * a), outline=rgba(AMBER, 0.6 * a), width=2)
    d.rectangle([540 - w / 2, yy - h / 2, 540 - w / 2 + 8, yy + h / 2], fill=rgba(ORANGE, a))
    blit(canvas, im, 540 + 4, yy - 3, a)


# ---------------------------------------------------------------- 场景元件
def keyboard_hands(canvas, d, cx, cy, s, t, a, sleeve=(236, 238, 242)):
    if a <= 0:
        return
    kw, kh = 860 * s, 330 * s
    d.rounded_rectangle([cx - kw / 2, cy - kh / 2, cx + kw / 2, cy + kh / 2], radius=28 * s,
                        fill=rgba((18, 28, 50), a), outline=rgba((70, 96, 140), a), width=max(1, int(3 * s)))
    cols, rows = 13, 4
    kx0, ky0 = cx - kw / 2 + 30 * s, cy - kh / 2 + 30 * s
    kws, khs = (kw - 60 * s) / cols, (kh - 60 * s) / rows
    tick = int(t * 9)
    for r in range(rows):
        for c in range(cols):
            lit = ((c * 7 + r * 13 + tick * 5) % 23) == 0
            col = ORANGE if lit else (42, 58, 92)
            x, y = kx0 + c * kws, ky0 + r * khs
            d.rounded_rectangle([x + 4 * s, y + 4 * s, x + kws - 4 * s, y + khs - 4 * s],
                                radius=8 * s, fill=rgba(col, a))
            if lit:
                glow(canvas, x + kws / 2, y + khs / 2, int(40 * s) + 1, ORANGE, 0.6 * a)
    skin, shade = (240, 203, 168), (214, 170, 136)
    for side in (-1, 1):
        hx, hy = cx + side * 190 * s, cy + 120 * s
        for k in range(12):
            y0 = hy + 60 * s + k * 22 * s
            d.rectangle([hx - 80 * s, y0, hx + 80 * s, y0 + 22 * s], fill=rgba(sleeve, a * (1 - k / 12)))
        d.rectangle([hx - 80 * s, hy + 60 * s, hx + 80 * s, hy + 80 * s], fill=rgba((205, 208, 216), a))
        d.ellipse([hx - 95 * s, hy - 70 * s, hx + 95 * s, hy + 90 * s], fill=rgba(skin, a))
        for k in range(4):
            fx = hx + (-66 + k * 44) * s * (1 if side < 0 else -1) * -1
            press = 14 * s * max(0.0, math.sin(t * 11 + k * 1.7 + side))
            top = hy - (150 - abs(k - 1.5) * 18) * s + press
            d.rounded_rectangle([fx - 19 * s, top, fx + 19 * s, hy - 20 * s], radius=19 * s,
                                fill=rgba(skin, a), outline=rgba(shade, a), width=max(1, int(2 * s)))
        tx = hx - side * 95 * s
        d.ellipse([tx - 26 * s, hy - 60 * s, tx + 26 * s, hy + 30 * s], fill=rgba(skin, a),
                  outline=rgba(shade, a), width=max(1, int(2 * s)))


CODE = ["mov ax, 0013h", "int 21h", "jmp short @@loop", "push bp", "cmp cx, 0FFh",
        "call print_str", "xor bx, bx", "lea dx, msg", "for (i = 0; i < n; i++)", "ret",
        "db 'WPS', 0", "out dx, al", "loop @@next", "mov [si], al", "if (key == ESC)"]


def code_rain(canvas, t, a, x0=60, y0=300, cols=2, color=(80, 200, 140)):
    if a <= 0:
        return
    for c in range(cols):
        for k in range(16):
            idx = (k + c * 5 + int(t * 2)) % len(CODE)
            y = y0 + ((k * 64 - t * 40 + c * 30) % 1000)
            text(canvas, CODE[idx], x0 + c * 520, y, 30, fill=color, alpha=a * 0.35,
                 anchor="lm", mono_font=True)


def pin(d, canvas, x, y, s, a):
    glow(canvas, x, y - 40 * s, int(160 * s), ORANGE, 0.5 * a)
    d.polygon([(x - 36 * s, y - 70 * s), (x + 36 * s, y - 70 * s), (x, y)], fill=rgba(ORANGE, a))
    d.ellipse([x - 48 * s, y - 130 * s, x + 48 * s, y - 34 * s], fill=rgba(ORANGE, a))
    d.ellipse([x - 18 * s, y - 100 * s, x + 18 * s, y - 64 * s], fill=rgba((255, 236, 210), a))


DOTS = None


def dot_map(d, t, a, cx, cy):
    global DOTS
    if DOTS is None:
        rng = np.random.default_rng(11)
        pts = []
        for gx in range(-9, 10):
            for gy in range(-8, 9):
                x, y = gx * 46, gy * 46
                r = math.hypot(x / 1.1, y)
                ang = math.atan2(y, x)
                edge = 360 + 50 * math.sin(ang * 3 + 1) + 30 * math.sin(ang * 5)
                if r < edge:
                    pts.append((x, y, rng.uniform(0, 1)))
        DOTS = pts
    for x, y, rr in DOTS:
        dist = math.hypot(x - 60, y - 40)
        wave = max(0.0, 1 - abs((t * 260) % 700 - dist) / 60)
        col = ORANGE if wave > 0.3 else (70, 100, 150)
        rad = 5 + 3 * wave
        d.ellipse([cx + x - rad, cy + y - rad, cx + x + rad, cy + y + rad],
                  fill=rgba(col, a * (0.55 + 0.4 * wave)))


def crt(d, canvas, x, y, s, t, a, seed):
    w, h = 220 * s, 180 * s
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], radius=16 * s,
                        fill=rgba((196, 186, 160), a))
    d.rounded_rectangle([x - w / 2 + 16 * s, y - h / 2 + 14 * s, x + w / 2 - 16 * s, y + h / 2 - 30 * s],
                        radius=10 * s, fill=rgba((10, 40, 28), a))
    for k in range(5):
        ln = (math.sin(seed * 3 + k * 1.3 + int(t * 3)) * 0.5 + 0.5) * (w - 60 * s)
        yy = y - h / 2 + 30 * s + k * 20 * s
        d.line([x - w / 2 + 28 * s, yy, x - w / 2 + 28 * s + ln, yy], fill=rgba((80, 220, 140), a * 0.9),
               width=max(1, int(5 * s)))
    d.rectangle([x - 30 * s, y + h / 2, x + 30 * s, y + h / 2 + 20 * s], fill=rgba((170, 160, 136), a))


def window_panel(d, canvas, cx, cy, w, h, title, a, title_col=(206, 64, 52)):
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=18,
                        fill=rgba((236, 238, 244), a))
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy - h / 2 + 64], radius=18,
                        fill=rgba(title_col, a))
    d.rectangle([cx - w / 2, cy - h / 2 + 40, cx + w / 2, cy - h / 2 + 64], fill=rgba(title_col, a))
    text(canvas, title, cx - w / 2 + 28, cy - h / 2 + 30, 34, "Black", WHITE, alpha=a, anchor="lm")


def bubble(d, canvas, s, x, y, a, size=40, col=(230, 234, 242)):
    if a <= 0:
        return
    im = text_img(s, size, "Bold", (30, 36, 52))
    w, h = im.width + 50, size + 46
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], radius=h / 2, fill=rgba(col, 0.92 * a))
    d.polygon([(x - 20, y + h / 2 - 4), (x + 6, y + h / 2 - 4), (x - 26, y + h / 2 + 22)], fill=rgba(col, 0.92 * a))
    blit(canvas, im, x, y - 3, a)


def phone(d, canvas, cx, cy, s, a, screen_t=0.0):
    w, h = 300 * s, 600 * s
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=44 * s,
                        fill=rgba((24, 26, 32), a), outline=rgba((120, 130, 150), a), width=max(1, int(4 * s)))
    sx0, sy0, sx1, sy1 = cx - w / 2 + 16 * s, cy - h / 2 + 50 * s, cx + w / 2 - 16 * s, cy + h / 2 - 60 * s
    d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=16 * s, fill=rgba((26, 52, 96), a))
    if screen_t > 0:
        for i in range(4):
            for j in range(3):
                ix = sx0 + 30 * s + j * (sx1 - sx0 - 60 * s) / 2
                iy = sy0 + 50 * s + i * 90 * s
                ap = a * clamp(screen_t * 4 - (i * 3 + j) * 0.25)
                d.rounded_rectangle([ix - 26 * s, iy - 26 * s, ix + 26 * s, iy + 26 * s], radius=12 * s,
                                    fill=rgba([ORANGE, CYAN, AMBER, (130, 220, 150)][(i + j) % 4], ap))
    d.ellipse([cx - 18 * s, cy + h / 2 - 46 * s, cx + 18 * s, cy + h / 2 - 10 * s],
              outline=rgba((120, 130, 150), a), width=max(1, int(3 * s)))


def mi_mark(d, canvas, cx, cy, s, a):
    glow(canvas, cx, cy, int(260 * s), ORANGE, 0.45 * a)
    d.rounded_rectangle([cx - 120 * s, cy - 120 * s, cx + 120 * s, cy + 120 * s], radius=60 * s,
                        fill=rgba(ORANGE, a))
    text(canvas, "小米", cx, cy - 6 * s, int(92 * s) + 1, "Black", WHITE, alpha=a)


def chips_stack(d, canvas, cx, cy, n, a, col=ORANGE):
    for k in range(n):
        y = cy - k * 16
        d.ellipse([cx - 70, y - 22, cx + 70, y + 22], fill=rgba(tuple(int(c * 0.7) for c in col), a))
        d.ellipse([cx - 70, y - 30, cx + 70, y + 14], fill=rgba(col, a), outline=rgba(WHITE, a * 0.6), width=3)


CAR = [(-430, 70), (-420, 10), (-380, -20), (-250, -40), (-150, -110), (40, -125), (190, -100),
       (300, -40), (410, -20), (440, 20), (440, 70)]


def car(d, canvas, cx, cy, s, reveal, a, lights=0.0):
    pts = [(cx + x * s, cy + y * s) for x, y in CAR]
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    lim = total * clamp(reveal)
    acc = 0
    for i in range(len(pts) - 1):
        seg = math.dist(pts[i], pts[i + 1])
        if acc >= lim:
            break
        f = min(1.0, (lim - acc) / seg)
        p0, p1 = pts[i], pts[i + 1]
        pe = (lerp(p0[0], p1[0], f), lerp(p0[1], p1[1], f))
        d.line([p0, pe], fill=rgba(AMBER, a), width=max(2, int(7 * s)))
        acc += seg
    if reveal > 0.5:
        ra = a * prog(reveal, 0.5, 0.9)
        d.line([(cx - 120 * s, cy - 100 * s), (cx + 170 * s, cy - 95 * s)], fill=rgba(AMBER, ra * 0.6), width=max(1, int(3 * s)))
        d.line([(cx - 440 * s, cy + 70 * s), (cx + 440 * s, cy + 70 * s)], fill=rgba(AMBER, ra), width=max(2, int(6 * s)))
        for wx in (-250, 260):
            r = 70 * s
            d.ellipse([cx + wx * s - r, cy + 70 * s - r, cx + wx * s + r, cy + 70 * s + r],
                      fill=rgba((10, 18, 34), ra), outline=rgba(AMBER, ra), width=max(2, int(7 * s)))
            d.ellipse([cx + wx * s - r * 0.4, cy + 70 * s - r * 0.4, cx + wx * s + r * 0.4, cy + 70 * s + r * 0.4],
                      outline=rgba(AMBER, ra * 0.7), width=max(1, int(4 * s)))
    if lights > 0:
        glow(canvas, cx + 430 * s, cy + 10 * s, int(200 * s), (255, 236, 200), lights * a)
        d.polygon([(cx + 440 * s, cy), (cx + 1000 * s, cy - 120 * s), (cx + 1000 * s, cy + 140 * s)],
                  fill=rgba((255, 230, 180), 0.12 * lights * a))


PRICE = None


def price_path():
    """上市首日走势示意：仅发行价 17.00 与收盘 16.80 为确切数字，曲线形态为示意。"""
    global PRICE
    if PRICE is None:
        rng = np.random.default_rng(718)
        keys_x = [0, 0.18, 0.55, 0.8, 1.0]
        keys_y = [16.6, 16.1, 17.15, 16.7, 16.8]
        xs = np.linspace(0, 1, 120)
        p = np.interp(xs, keys_x, keys_y) + rng.normal(0, 0.035, 120)
        p[0], p[-1] = 16.6, 16.8
        PRICE = p
    return PRICE


def stamp(canvas, s, cx, cy, t0, t, color=RED, size=170, angle=-12):
    lt = t - t0
    if lt < 0:
        return
    a = prog(lt, 0, 0.08)
    sc = lerp(2.2, 1.0, ease_out(prog(lt, 0, 0.18)))
    im = stamp_img(s, size, color, angle)
    blit(canvas, im, cx, cy, a, sc)


@lru_cache(maxsize=16)
def stamp_img(s, size, color, angle):
    im = text_img(s, size, "Black", color, spacing=10)
    w, h = im.width + 40, im.height + 20
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(box)
    d.rounded_rectangle([6, 6, w - 6, h - 6], radius=18, outline=color + (255,), width=10)
    box.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2 - 6))
    return box.rotate(-angle, expand=True, resample=Image.BICUBIC)


def shake(t, t0, dur=0.4, amp=18):
    lt = t - t0
    if not (0 <= lt <= dur):
        return 0, 0
    k = (1 - lt / dur) * amp
    return math.sin(lt * 90) * k, math.cos(lt * 77) * k


# ---------------------------------------------------------------- 场景
def s01(c, d, t):
    lt = t
    a_kb = 1 - prog(t, 4.0, 5.2)
    zoom = lerp(1.15, 0.85, ease_in_out(prog(t, 0, 5.2)))
    code_rain(c, t, a_kb * 0.8)
    keyboard_hands(c, d, 540, 980, zoom, t, a_kb)
    # 开场大字（兼封面）
    ta = 1 - prog(t, 2.2, 2.7)
    text(c, "千万台手机", 540, 470, 132, "Black", WHITE, alpha=ta, glow=8, glow_fill=(20, 60, 140), spacing=6)
    text(c, "· 那双手 ·", 540, 640, 88, "Black", ORANGE, alpha=ta, glow=8, glow_fill=(120, 40, 0))
    # 地图 + 仙桃
    ma = prog(t, 4.0, 5.0)
    if ma > 0:
        dot_map(d, t - 4.0, ma, 540, 930)
        py = 970 - 60 * (1 - back_out(prog(t, 4.6, 5.2)))
        pin(d, c, 600, py, 1.0, prog(t, 4.6, 4.9))
        text(c, "湖北 · 仙桃", 540, 1170, 72, "Black", WHITE, alpha=prog(t, 5.0, 5.4), glow=6,
             glow_fill=(20, 60, 140))
        text(c, "N 30.36°  E 113.45°", 540, 1250, 34, "Medium", GREY, alpha=prog(t, 5.3, 5.7),
             mono_font=True)
    del lt


def s02(c, d, t):
    lt = t - 8.0
    a1 = 1 - prog(t, 12.4, 12.9)
    if a1 > 0:
        glow(c, 540, 800, 520, (60, 180, 120), 0.25 * a1)
        for i, (x, y) in enumerate([(200, 760), (540, 700), (880, 760), (110, 990), (970, 990)]):
            crt(d, c, x, y, 1.0, t, a1 * prog(lt, 0.1 * i, 0.1 * i + 0.5), i)
        draw_char(c, 1, 540, 1030, 0.92, t, a1 * prog(lt, 0.2, 0.8))
        chip(c, d, "武汉大学 · 机房", 540, 560, 44, alpha=a1 * prog(lt, 0.4, 0.9))
    a2 = prog(t, 12.6, 13.0)
    if a2 > 0:
        lt2 = t - 12.6
        squeeze = ease_in_out(prog(t, 14.2, 16.6))
        sx, sy = shake(t, 16.4, 1.2, 6 * squeeze + 1)
        ww = lerp(620, 470, squeeze)
        window_panel(d, c, 540 + sx, 880 + sy, ww, 340, "WPS", a2)
        for k in range(6):
            ln = (ww - 90) * (0.55 + 0.45 * math.sin(k * 2.1 + 1)) * clamp(lt2 * 1.5 - k * 0.2)
            yy = 880 - 90 + k * 38
            d.line([540 - ww / 2 + 40 + sx, yy + sy, 540 - ww / 2 + 40 + ln + sx, yy + sy], fill=rgba((90, 100, 120), a2),
                   width=10)
        lx = lerp(-260, 540 - ww / 2 - 130, ease_out(prog(t, 14.0, 14.8)))
        d.rounded_rectangle([lx - 130, 760, lx + 130, 1000], radius=18, fill=rgba((40, 92, 170), a2))
        text(c, "微软", lx, 850, 52, "Black", WHITE, alpha=a2)
        text(c, "Office", lx, 916, 38, "Bold", (200, 220, 255), alpha=a2)
        rx = lerp(1340, 540 + ww / 2 + 130, ease_out(prog(t, 14.6, 15.4)))
        d.rounded_rectangle([rx - 130, 760, rx + 130, 1000], radius=18, fill=rgba((70, 70, 80), a2))
        text(c, "盗版", rx, 880, 60, "Black", (255, 210, 200), alpha=a2)
        for k in range(3):
            stamp(c, "盗版", 540 - 120 + k * 120 + sx, 830 + (k % 2) * 100, 15.4 + k * 0.35, t,
                  color=(200, 60, 50), size=60, angle=-14 + k * 10)
        draw_char(c, 2, 540, 1170, 0.62, t, a2)
        if t > 15.6:
            meter = ease_in_out(prog(t, 15.6, 17.4))
            d.rounded_rectangle([200, 1265, 880, 1290], radius=12, fill=rgba((30, 44, 70), a2))
            d.rounded_rectangle([200, 1265, 200 + 680 * meter, 1290], radius=12, fill=rgba(RED, a2))
            text(c, "压力", 170, 1278, 30, "Bold", GREY, alpha=a2, anchor="rm")
    caption(c, d, "九十年代 · WPS 被夹击", t, 13.6, 15.9)
    caption(c, d, "团队几乎熬不住", t, 15.9, 17.9)
    glow(c, 540, 470, 400, (255, 255, 255), 0.6 * window(t, 12.45, 12.9, 0.1, 0.3))


def road(d, pts, col, a):
    d.polygon(pts, fill=rgba(col, a))


def s03(c, d, t):
    lt = t - 18.0
    a = prog(lt, 0, 0.6)
    t_stay = word_time("n03", "留下") if LINE_DATA else 28.0
    choose = ease_in_out(prog(t, t_stay, t_stay + 1.4))
    left_lit = window(t, 18.8, t_stay + 0.3, 0.6, 0.6)
    fx, fy = 540, 1010
    road(d, [(330, 1330), (750, 1330), (fx + 70, fy), (fx - 70, fy)], (36, 52, 84), a)
    road(d, [(fx - 70, fy), (fx + 10, fy), (300, 640), (190, 640)], lerp_col((36, 52, 84), (90, 170, 230), left_lit * (1 - choose)), a)
    road(d, [(fx - 10, fy), (fx + 70, fy), (890, 640), (780, 640)], lerp_col((36, 52, 84), (200, 110, 40), choose), a)
    for k in range(8):
        yy = 1320 - k * 42
        d.line([540, yy, 540, yy - 18], fill=rgba(AMBER, a * 0.5), width=4)
    glow(c, 245, 600, 260, CYAN, 0.55 * left_lit * (1 - choose) * a)
    glow(c, 835, 600, 260, ORANGE, 0.6 * choose * a)
    text(c, "互联网", 245, 570, 62, "Black", CYAN if choose < 0.5 else (90, 110, 140),
         alpha=a * prog(t, 19.2, 19.7))
    chip(c, d, "那条路更顺", 245, 670, 34, fg=CYAN, border=CYAN,
         alpha=a * window(t, word_time("n02", "更顺") - 0.3, t_stay + 0.6, 0.3, 0.5))
    text(c, "WPS", 835, 570, 70, "Black", ORANGE if choose > 0.3 else (130, 140, 160),
         alpha=a * prog(t, 19.4, 19.9))
    q = window(t, word_time("n02", "互联网") - 0.1, t_stay, 0.2, 0.5)
    text(c, "？", 540, 760, 160, "Black", WHITE, alpha=q * a, scale=1 + 0.05 * math.sin(t * 6))
    cx = lerp(540, 690, choose)
    cy = lerp(1070, 900, choose)
    sc = lerp(0.62, 0.5, choose)
    draw_char(c, 2, cx, cy, sc, t, a, speaking=24.3 < t < 27.6)
    # 十年暗调
    dk = prog(t, word_time("n03", "十年") - 0.3, word_time("n03", "十年") + 1.5)
    dim(d, 0.45 * dk, (2, 6, 16))
    if dk > 0:
        for k in range(10):
            on = prog(t, word_time("n03", "十年") + k * 0.12, word_time("n03", "十年") + k * 0.12 + 0.1)
            x = 200 + k * 70
            d.rounded_rectangle([x, 1250, x + 50, 1290], radius=8, fill=rgba(lerp_col((40, 50, 70), ORANGE, on * 0.6), dk))
        text(c, "十年", 540, 1215, 34, "Bold", AMBER, alpha=dk)


def lerp_col(a, b, x):
    return tuple(int(lerp(a[i], b[i], clamp(x))) for i in range(3))


def s04(c, d, t):
    lt = t - 34.0
    a = prog(lt, 0, 0.5)
    t40 = word_time("n04", "四十")
    age = int(lerp(30, 40, ease_out(prog(t, t40 - 0.9, t40 + 0.4))))
    sc = 1 + 0.12 * max(0.0, 1 - abs(t - t40 - 0.4) * 3)
    text(c, str(age), 500, 540, 230, "Black", WHITE, alpha=a, scale=sc, glow=10, glow_fill=(20, 60, 140))
    text(c, "岁", 690, 590, 80, "Black", ORANGE, alpha=a * prog(t, t40, t40 + 0.3))
    draw_char(c, 3, 540, 1010, 0.92, t, a, eyes="open")
    t_cuo = word_time("n04", "错过")
    items = [("晚了吧", 220, 770), ("错过移动互联网", 790, 760), ("40 岁还创业？", 230, 1230), ("风口早过了", 840, 1210)]
    for i, (s, x, y) in enumerate(items):
        st = t_cuo - 1.2 + i * 0.55
        ba = prog(t, st, st + 0.25) * (1 - prog(t, 41.4, 42.0))
        wob = math.sin(t * 3 + i) * 6
        inward = 30 * ease_in_out(prog(t, st, 41.5))
        bubble(d, c, s, x + (540 - x) / abs(540 - x) * inward, y + wob, ba, 40)


def s05(c, d, t):
    lt = t - 42.0
    a_found = window(t, 42.0, 47.4, 0.4, 0.5)
    if a_found > 0:
        mi_mark(d, c, 540, 830, back_out(prog(t, 42.6, 43.3)), a_found)
        chip(c, d, "2010.04 · 北京", 540, 1010, 38, alpha=a_found * prog(t, 43.2, 43.6))
        draw_char(c, 3, 540, 1210, 0.6, t, a_found, eyes="smile" if t > 43.4 else None)
    # 2011 手机亮相（留白）
    a_ph = window(t, 46.9, 51.6, 0.5, 0.6)
    if a_ph > 0:
        dim(d, 0.4 * a_ph)
        glow(c, 540, 860, 520, (200, 220, 255), 0.35 * a_ph)
        rise = ease_out(prog(t, 46.9, 48.2))
        phone(d, c, 540, lerp(1400, 960, rise), 0.9, a_ph, screen_t=prog(t, 48.2, 49.5))
        sweep = prog(t, 48.4, 49.4)
        if 0 < sweep < 1:
            x = lerp(200, 880, sweep)
            d.polygon([(x - 40, 560), (x + 40, 560), (x - 60, 1200), (x - 140, 1200)], fill=rgba(WHITE, 0.25 * a_ph))
    # 三线合流
    a_tr = window(t, 51.4, 57.6, 0.4, 0.5)
    if a_tr > 0:
        labels = [("硬件", 190, 1240, word_time("n06", "硬件")), ("软件", 540, 1300, word_time("n06", "软件")),
                  ("互联网", 890, 1240, word_time("n06", "互联网"))]
        tm = word_time("n06", "赛道")
        merge = ease_in_out(prog(t, tm - 0.9, tm + 0.3))
        for i, (s, x, y, st) in enumerate(labels):
            la = prog(t, st - 0.1, st + 0.2) * a_tr
            grow = ease_out(prog(t, st, st + 0.9))
            pts = []
            for k in range(30):
                u = k / 29 * grow
                bx = lerp(x, 540, u ** 0.7)
                by = lerp(y - 50, 760, u)
                pts.append((bx, by))
            if len(pts) > 1 and la > 0:
                d.line(pts, fill=rgba([CYAN, (130, 220, 150), AMBER][i], la * 0.35), width=30, joint="curve")
                d.line(pts, fill=rgba([CYAN, (130, 220, 150), AMBER][i], la), width=14, joint="curve")
            chip(c, d, s, x, y, 44, border=[CYAN, (130, 220, 150), AMBER][i], alpha=la)
        if merge > 0:
            d.line([(540, 760), (540, lerp(760, 470, merge))], fill=rgba(ORANGE, a_tr), width=28)
            glow(c, 540, lerp(760, 470, merge), 200, ORANGE, 0.8 * merge * a_tr)
            text(c, "一条赛道", 540, 380, 84, "Black", ORANGE, alpha=a_tr * prog(t, tm, tm + 0.3), glow=8,
                 glow_fill=(120, 40, 0))
        mi_mark(d, c, 540, 760, 0.55, a_tr * 0.95)
    # 点名
    t_name = 57.3 + LINE_DATA["n07"]["words"][-1]["t"] - 0.05 if LINE_DATA else 58.5
    a_nm = window(t, 57.2, 60.3, 0.4, 0.4)
    if a_nm > 0:
        glow(c, 540, 900, 560, ORANGE, 0.3 * a_nm)
        draw_char(c, 3, 540, 1010, lerp(0.92, 1.02, prog(t, 57.2, 60.3)), t, a_nm, eyes="smile")
        na = prog(t, t_name - 0.05, t_name + 0.15)
        sc = lerp(1.6, 1.0, ease_out(prog(t, t_name - 0.05, t_name + 0.3)))
        text(c, "雷 军", 540, 450, 200, "Black", WHITE, alpha=na * a_nm, scale=sc, glow=12, glow_fill=ORANGE)
        text(c, "小米集团创始人", 540, 590, 44, "Bold", AMBER, alpha=prog(t, t_name + 0.3, t_name + 0.6) * a_nm)
        glow(c, 540, 470, 500, WHITE, 0.6 * window(t, t_name - 0.05, t_name + 0.4, 0.05, 0.3))
    del lt


def s06(c, d, t):
    lt = t - 60.0
    a = prog(lt, 0, 0.5) * (1 - prog(t, 75.5, 76.0))
    px0, px1, py0, py1 = 90, 990, 700, 1200
    chart_a = a * prog(t, 60.6, 61.2) * (1 - 0.75 * prog(t, 70.0, 70.8))
    if chart_a <= 0:
        return
    t_po = word_time("n08", "破发")
    sx, sy = shake(t, t_po, 0.5, 20)
    d.rounded_rectangle([px0 + sx, py0 - 90 + sy, px1 + sx, py1 + 40 + sy], radius=24,
                        fill=rgba((8, 18, 38), 0.9 * chart_a), outline=rgba((50, 70, 110), chart_a), width=2)
    text(c, "2018.07.09 · 港股上市首日", px0 + 30 + sx, py0 - 48 + sy, 34, "Bold", GREY, alpha=chart_a, anchor="lm")
    lo, hi = 15.8, 17.5
    ymap = lambda v: py1 - (v - lo) / (hi - lo) * (py1 - py0)
    for v in (16.0, 16.5, 17.0, 17.5):
        d.line([px0 + 30 + sx, ymap(v) + sy, px1 - 30 + sx, ymap(v) + sy], fill=rgba((40, 56, 90), chart_a), width=1)
    y17 = ymap(17.0) + sy
    for k in range(0, px1 - px0 - 60, 30):
        d.line([px0 + 30 + k + sx, y17, px0 + 30 + k + 16 + sx, y17], fill=rgba(AMBER, chart_a), width=4)
    text(c, "发行价 17.00", px1 - 40 + sx, y17 - 30, 32, "Bold", AMBER, alpha=chart_a, anchor="rm")
    p = price_path()
    t_close = word_time("n08", "十六") + 0.6
    pr = ease_in_out(prog(t, 61.4, t_close))
    n = max(2, int(len(p) * pr))
    pts = [(lerp(px0 + 40, px1 - 40, i / (len(p) - 1)) + sx, ymap(p[i]) + sy) for i in range(n)]
    cur = p[n - 1]
    col = WHITE if cur >= 17.0 else ORANGE
    if len(pts) > 1:
        d.line(pts, fill=rgba(col, chart_a), width=7, joint="curve")
        ex, ey = pts[-1]
        d.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], fill=rgba(col, chart_a))
    text(c, "走势示意", px0 + 40 + sx, py1 + 10 + sy, 26, "Medium", GREY, alpha=chart_a * 0.8, anchor="lm")
    if pr < 1:
        text(c, "发行价 HK$ 17.00", 540 + sx, 1295 + sy, 66, "Black", WHITE, alpha=chart_a)
    else:
        ca = prog(t, t_close, t_close + 0.3)
        text(c, "首日收盘 HK$ 16.80", 540 + sx, 1295 + sy, 66, "Black", ORANGE, alpha=chart_a * ca)
        text(c, "较发行价 -1.2%", px1 - 30 + sx, py0 - 48 + sy, 34, "Bold", ORANGE, alpha=chart_a * ca, anchor="rm")
    stamp(c, "破发", 470 + sx, 1000 + sy, t_po, t)
    # 多数人会收手
    t_sh = LINE_DATA["n09"]["start"]
    if t > t_sh - 0.2:
        ka = a * window(t, t_sh - 0.2, 76.0, 0.3, 0.5)
        dim(d, 0.45 * ka)
        for i in range(5):
            x = 180 + i * 90
            off = 260 * ease_in_out(prog(t, t_sh + 0.6 + i * 0.1, t_sh + 1.8 + i * 0.1))
            chips_stack(d, c, x - off, 1180, 4, ka * (1 - off / 300), col=(120, 130, 150))
        text(c, "收手", 330 - 120 * ease_in_out(prog(t, t_sh + 0.6, t_sh + 1.8)), 1060, 56, "Black", GREY,
             alpha=ka * (1 - prog(t, t_sh + 1.4, t_sh + 2.2)))
        lit = prog(t, 72.6, 74.0)
        glow(c, 820, 1040, 300, ORANGE, 0.4 * lit * ka)
        draw_char(c, 4, 820, 1050, 0.55, t, ka)
        text(c, "他呢？", 820, 1290, 56, "Black", ORANGE, alpha=ka * prog(t, 73.4, 73.9))


def s07(c, d, t):
    lt = t - 76.0
    a = prog(lt, 0, 0.5)
    t_jz = word_time("n10", "加注")
    t_yb = word_time("n10", "一把手")
    car_a = a * (1 - 0.55 * prog(t, 84.4, 85.0))
    car_y = lerp(880, 690, ease_in_out(prog(t, 84.2, 85.2)))
    car_s = lerp(1.0, 0.8, ease_in_out(prog(t, 84.2, 85.2)))
    chip(c, d, "2021.03.30", 540, 620, 40, alpha=a * prog(t, 77.4, 77.8) * (1 - prog(t, 84.0, 84.5)))
    car(d, c, 540, car_y, car_s, prog(t, 78.0, 82.0), car_a, lights=prog(t, 82.0, 82.6) * (0.6 + 0.4 * prog(t, 88, 89)))
    if t > t_jz - 0.2:
        stack = int(clamp((t - t_jz) / 0.1, 0, 9))
        ca = a * (1 - prog(t, 84.0, 84.6))
        push = ease_out(prog(t, t_jz, t_jz + 0.8))
        chips_stack(d, c, lerp(200, 540, push), 1240, stack, ca)
        text(c, "加注", lerp(200, 540, push), 1100 - stack * 16, 60, "Black", ORANGE, alpha=ca * prog(t, t_jz, t_jz + 0.3))
    chip(c, d, "智能电动汽车业务 · 兼任一把手", 540, 1300, 40, alpha=a * window(t, t_yb - 0.2, 84.4, 0.3, 0.4))
    # 发布会：愿意押上全部声誉
    pa = prog(t, 84.2, 85.0)
    if pa > 0:
        d.polygon([(470, 300), (610, 300), (900, 1400), (180, 1400)], fill=rgba((255, 230, 190), 0.07 * pa))
        glow(c, 540, 980, 420, AMBER, 0.3 * pa)
        draw_char(c, 4, 540, 980, 0.86, t, pa, speaking=84.9 < t < 87.8)
        d.polygon([(380, 1225), (700, 1225), (660, 1350), (420, 1350)], fill=rgba((44, 52, 72), pa))
        d.line([(390, 1232), (690, 1232)], fill=rgba(ORANGE, pa), width=6)
        chip(c, d, "2021.3.30 · 小米发布会", 540, 1290, 30, fg=GREY, border=(80, 96, 130),
             alpha=pa * prog(t, 85.0, 85.4), weight="Medium")
    if t > 87.8:
        stamp(c, "加注", 820, 560, 88.2, t, color=ORANGE, size=120, angle=10)
    dim(d, 0.0)


def s08(c, d, t):
    a = prog(t, 94.0, 94.6)
    t_q = 98.6
    grid_p = prog(t, word_time("n11", "千万"), word_time("n11", "千万") + 1.8)
    ka = a * (1 - prog(t, t_q - 0.4, t_q))
    if ka > 0:
        if grid_p > 0:
            for i in range(-6, 7):
                for j in range(-9, 10):
                    dist = math.hypot(i, j * 0.7)
                    ap = clamp(grid_p * 9 - dist) * ka * 0.8
                    if ap <= 0:
                        continue
                    x, y = 540 + i * 84, 900 + j * 120
                    d.rounded_rectangle([x - 26, y - 46, x + 26, y + 46], radius=10, fill=rgba((40, 60, 96), ap),
                                        outline=rgba(ORANGE if (i + j) % 5 == 0 else (90, 120, 170), ap), width=3)
        s = lerp(0.9, 0.45, ease_in_out(grid_p))
        dim(d, 0.0)
        keyboard_hands(c, d, 540, 960, s, t, ka)
    qa = prog(t, t_q, t_q + 0.6)
    if qa > 0:
        dim(d, 0.5 * qa, (2, 6, 18))
        glow(c, 540, 900, 600, ORANGE, 0.18 * qa)
        draw_char(c, 1, 330, 600, 0.42, t, qa)
        draw_char(c, 4, 750, 600, 0.42, t, qa)
        d.line([(440, 640), (630, 640)], fill=rgba(AMBER, qa), width=5)
        d.polygon([(630, 626), (660, 640), (630, 654)], fill=rgba(AMBER, qa))
        text(c, "仙桃机房", 330, 830, 34, "Bold", GREY, alpha=qa)
        text(c, "千万台手机", 750, 830, 34, "Bold", GREY, alpha=qa)
        q1 = prog(t, t_q + 0.2, t_q + 0.6)
        text(c, "他每一次", 540, 960, 64, "Bold", WHITE, alpha=q1)
        q2 = prog(t, word_time("n11", "留下") - 0.1, word_time("n11", "留下") + 0.2)
        text(c, "「留下」", 300, 1080, 80, "Black", CYAN, alpha=q2, scale=lerp(1.3, 1, ease_out(q2)))
        text(c, "还是", 540, 1086, 56, "Bold", WHITE, alpha=q2)
        q3 = prog(t, word_time("n11", "加注") - 0.1, word_time("n11", "加注") + 0.2)
        text(c, "「加注」", 780, 1080, 80, "Black", ORANGE, alpha=q3, scale=lerp(1.3, 1, ease_out(q3)))
        q4 = prog(t, word_time("n11", "到底") - 0.4, word_time("n11", "到底"))
        text(c, "赌的到底是什么？", 540, 1215, 76, "Black", WHITE, alpha=q4, glow=6, glow_fill=(20, 60, 140))
        t_pl = word_time("n11", "评论")
        q5 = prog(t, t_pl - 0.1, t_pl + 0.2)
        if q5 > 0:
            pulse = 1 + 0.06 * math.sin((t - t_pl) * 7)
            im = text_img("评论区说", 60, "Black", (20, 12, 4))
            w, h = im.width + 90, 110
            ww, hh = w * pulse, h * pulse
            d.rounded_rectangle([540 - ww / 2, 1400 - hh / 2, 540 + ww / 2, 1400 + hh / 2], radius=hh / 2,
                                fill=rgba(ORANGE, q5))
            blit(c, im, 540, 1396, q5, pulse)
            bob = 10 * math.sin((t - t_pl) * 6)
            d.polygon([(520, 1480 + bob), (560, 1480 + bob), (540, 1510 + bob)], fill=rgba(ORANGE, q5))


SCENE_FUNCS = {"S01": s01, "S02": s02, "S03": s03, "S04": s04, "S05": s05, "S06": s06, "S07": s07, "S08": s08}


def frame(t):
    c = background().copy()
    d = ImageDraw.Draw(c, "RGBA")
    particles(d, t, 0.8)
    for name, a, b in SCENES:
        if a - 0.6 <= t < b + 0.6:
            SCENE_FUNCS[name](c, d, t)
    # 转场：场景边界短暂压暗
    for name, a, b in SCENES[1:]:
        k = 1 - min(1.0, abs(t - a) / 0.3)
        if k > 0:
            dim(d, 0.85 * k, NAVY0)
    timeline(c, d, t)
    year_card(c, d, t)
    subtitles(c, d, t)
    dim(d, 1 - prog(t, 0, 0.25), NAVY0)
    dim(d, prog(t, DURATION - 0.6, DURATION), NAVY0)
    return c


# ---------------------------------------------------------------- 编码
def render_segment(args):
    idx, f0, f1 = args
    init_data()
    path = BUILD / "segments" / f"seg_{idx:02d}.mp4"
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-x264-params", "keyint=60", str(path)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", help="只导出若干秒的静帧，例如 1,10,25")
    ap.add_argument("--workers", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--out", default=str(OUT / "leijun_kepu_9x16.mp4"))
    args = ap.parse_args()
    init_data()
    if args.preview:
        pv = BUILD / "preview"
        pv.mkdir(parents=True, exist_ok=True)
        for s in args.preview.split(","):
            frame(float(s)).save(pv / f"t{float(s):06.2f}.jpg", quality=88)
        print("preview ->", pv)
        return
    (BUILD / "segments").mkdir(parents=True, exist_ok=True)
    total = int(round(DURATION * FPS))
    n = args.workers * 2
    bounds = [round(total * i / n) for i in range(n + 1)]
    jobs = [(i, bounds[i], bounds[i + 1]) for i in range(n)]
    with Pool(args.workers) as pool:
        segs = []
        for k, path in enumerate(pool.imap(render_segment, jobs)):
            segs.append(path)
            print(f"segment {k + 1}/{n} done", flush=True)
    lst = BUILD / "segments" / "list.txt"
    lst.write_text("".join(f"file '{p.name}'\n" for p in segs))
    OUT.mkdir(exist_ok=True)
    frame(1.2).save(OUT / "cover.jpg", quality=92)
    subprocess.check_call([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
        "-i", str(BUILD / "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart", "-shortest", args.out])
    print("done ->", args.out)


if __name__ == "__main__":
    sys.exit(main())
