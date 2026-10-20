"""Direction B, full film: all 7 sections. frame(t) + timeline.

Card text is read straight from script_v0.4.1.md (「上屏文字」 section), so every line
is verbatim and in order; one line per card, never wrapped.
"""
import math
import os
import random
import re

import cairo

import b_video as V
from b_video import (seg, ease, ease_out, back_out, clamp, car_f, draw_car, tissue_jet, rocket, smoke, bill, person,
                     flag, bg_night, bg_paper, sc_stunt, sc_crowd, NIGHT, SEPIA, COLD)
from frames import (W, H, new, comp, grain, torn, drop_shadow, halftone, tape_label, b_toon, poly, line, text, hexc,
                    mix, INK, RED, PAPER, TR, CAR_L)
from geo import path

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "script_v0.4.1.md")


def script_lines():
    src = open(SCRIPT, encoding="utf-8").read()
    body = src.split("## 上屏文字", 1)[1].split("\n---", 1)[0]
    out = []
    for ln in body.splitlines():
        ln = re.sub(r"^\s*\d+\|", "", ln).strip()
        if not ln or ln.startswith("#"):
            continue
        out.append(ln)
    return out


LINES = script_lines()
assert len(LINES) == 38, len(LINES)
assert [c[2] for c in V.CARDS] == LINES[:15]


def auto_dur(s):
    return max(2.0, min(4.0, 1.3 + 0.09 * len(s)))


DUR = [b - a for (a, b, _) in V.CARDS] + [auto_dur(s) for s in LINES[15:]]
DUR[16] = 2.8                 # launch needs room
DUR[31] = 2.2                 # 十八年后。
DUR[37] = 3.2                 # last card, then a tail
TAIL = 1.6
START = [a for (a, b, _) in V.CARDS]
END = [b for (a, b, _) in V.CARDS]
for d in DUR[15:]:
    START.append(END[-1])
    END.append(END[-1] + d)
DURATION = END[-1] + TAIL
SECTION_STARTS = {1: 0.0, 2: START[5], 3: START[15], 4: START[20], 5: START[26], 6: START[31], 7: START[35]}


def span(i, j=None):
    j = i if j is None else j
    return (START[i] if i else 0.0), END[j]


# ------------------------------------------------------------------ props
def card(ctx, cx, cy, w, h, kind, rot=0.0, grey=0.0, s=1.0, alpha=1.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.scale(s, s)
    pts = torn([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], seed=int(w + h) + len(kind), amp=4, step=12)
    drop_shadow(ctx, lambda c, col: poly(c, pts, col), off=(8, 10), sigma=6, alpha=0.35 * alpha)
    poly(ctx, pts, (0.98, 0.97, 0.94, alpha))
    poly(ctx, [(x * 0.9, y * 0.9) for x, y in pts], (*COLD, alpha))
    if kind == "rocket":
        rocket(ctx, 0, 10, h * 0.72, rot=0.0)
    else:
        draw_car(ctx, (0, h * 0.18), 0.0, w * 0.36, shadow=False)
    if grey > 0:
        poly(ctx, pts, (0.35, 0.35, 0.38, 0.55 * grey))
    ctx.restore()


def tape(ctx, x, y, rot=0.0, w=110):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    poly(ctx, torn([(-w / 2, -15), (w / 2, -15), (w / 2, 15), (-w / 2, 15)], seed=int(x + y), amp=2, step=6), (0.96, 0.93, 0.8, 0.8))
    ctx.restore()


def half_bill(ctx, cx, cy, s, rot, side):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    ctx.rectangle(-200 if side < 0 else 0, -200, 200, 400)
    ctx.clip()
    bill(ctx, 0, 0, s, 0.0)
    ctx.restore()


def burst(ctx, cx, cy, col, n=18, r0=120, r1=1400, rot=0.0):
    for k in range(n):
        a0 = rot + 2 * math.pi * k / n
        a1 = a0 + math.pi / n
        poly(ctx, [(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)), (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)),
                   (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)), (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1))], col)


def bottom_strip(ctx, col):
    poly(ctx, torn([(0, 880), (W, 870), (W, H + 40), (0, H + 40)], seed=33, amp=7), col)


def scrap_bg(key, col, scrap, seed):
    return bg_paper(key, col, [([(120, 150), (1800, 130), (1810, 860), (110, 850)], scrap)], seed=seed)


# ------------------------------------------------------------------ section 3
def sc_last(ctx, t, u):
    comp(ctx, scrap_bg("last", SEPIA, COLD, 31))
    for i in range(3):
        cx = 330 + i * 230
        ctx.push_group()
        rocket(ctx, cx, 520, 300, rot=0.05 * (i - 1), broken=0.25, seed=40 + i)
        line(ctx, [(cx - 80, 560), (cx + 80, 600)], RED, 8)
        line(ctx, [(cx + 80, 560), (cx - 80, 600)], RED, 8)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(0.45)
    z = 1.0 + 0.05 * u
    rocket(ctx, 1320, 470, 560 * z, rot=0.0, seed=7)
    line(ctx, [(1080, 790), (1560, 790)], (*INK, 0.6), 6)


def sc_launch(ctx, t, u):
    comp(ctx, scrap_bg("launch", SEPIA, COLD, 32))
    lift = 720 * seg(u, 0.25, 1.0) ** 2.2
    shake = 5 * math.sin(t * 70) * (1 - seg(u, 0.85, 1.0))
    cx, cy = W / 2 + shake, 470 - lift
    line(ctx, [(560, 790), (1360, 790)], (*INK, 0.6), 6)
    ign = ease(seg(u, 0.05, 0.25))
    smoke(ctx, W / 2 - 160, 780, ign * 0.9, seed=81, col=(0.82, 0.81, 0.79))
    smoke(ctx, W / 2 + 160, 780, ign * 0.9, seed=82, col=(0.82, 0.81, 0.79))
    base = (cx, cy + 560 * 0.42 + 10)
    rnd = random.Random(int(t * 30))
    for j, (ln, w0, col) in enumerate(((260, 70, (*RED, 0.9)), (190, 46, (0.98, 0.95, 0.88, 0.95)), (110, 24, (1, 1, 1, 1)))):
        L_ = ln * ign * (0.9 + 0.2 * rnd.random())
        pts = [(base[0] - w0 / 2, base[1]), (base[0] + w0 / 2, base[1]), (base[0] + w0 * 0.2, base[1] + L_ * 0.7),
               (base[0], base[1] + L_), (base[0] - w0 * 0.2, base[1] + L_ * 0.7)]
        poly(ctx, torn(pts, seed=j + int(t * 15), amp=6, step=10), col)
    rocket(ctx, cx, cy, 560, seed=7)


def sc_orbit(ctx, t, u):
    if "orbit" not in V._cache:
        s, c = new()
        V.paper_bg(c, seed=41)
        sky = torn([(70, 50), (1850, 30), (1880, 1000), (40, 1030)], seed=42, amp=9, step=14)
        poly(c, sky, NIGHT)
        rnd = random.Random(43)
        for _ in range(80):
            c.arc(rnd.uniform(90, 1830), rnd.uniform(70, 700), rnd.uniform(1.5, 3.5), 0, 2 * math.pi)
            c.set_source_rgba(0.95, 0.93, 0.85, rnd.uniform(0.4, 0.9))
            c.fill()
        earth = [(W / 2 + 1500 * math.cos(a), 2350 + 1500 * math.sin(a)) for a in [k * math.pi / 90 for k in range(180)]]
        drop_shadow(c, lambda cc, col: poly(cc, earth, col), off=(0, -6), sigma=14, alpha=0.5)
        poly(c, earth, hexc("#3f6f9a"))
        gs, gc = new()
        gc.set_source_rgb(0.5, 0.5, 0.5)
        gc.paint()
        m, mc = new()
        poly(mc, earth, (1, 1, 1))
        halftone(c, gs, m, (0.75, 0.88, 0.95, 0.45), spacing=12, angle=0.4, maxr=0.5)
        V._cache["orbit"] = s
    comp(ctx, V._cache["orbit"])
    ctx.save()
    ctx.translate(W / 2, 1180)
    ctx.scale(1.0, 0.55)
    ctx.arc(0, 0, 1080, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.95, 0.93, 0.85, 0.7)
    ctx.set_line_width(3)
    ctx.set_dash([18, 14])
    ctx.stroke()
    ctx.set_dash([])
    a = -math.pi * (0.85 - 0.5 * ease(u))
    x, y = W / 2 + 1080 * math.cos(a), 1180 + 1080 * 0.55 * math.sin(a)
    rocket(ctx, x, y, 170, rot=a + math.pi, seed=9)


def sc_saved(ctx, t, u, worried=False):
    comp(ctx, scrap_bg("saved", PAPER, hexc("#f1d9c6") if not worried else COLD, 34 if not worried else 35))
    if not worried:
        burst(ctx, 1330, 470, (1, 1, 1, 0.35), rot=t * 0.15)
    card(ctx, 1330, 470, 420, 560, "rocket", rot=0.04, grey=0.6 * ease(seg(u, 0.1, 0.6)) if worried else 0.0)
    tape(ctx, 1330, 200, -0.1)
    b_toon(ctx, 0.0, "low" if worried else "grin", 600, 60, 0.82, rot=-0.02)
    if worried:
        cr = ease(seg(u, 0.05, 0.7))
        pts = [(1100, 180), (1200, 320), (1160, 450), (1280, 600), (1240, 760)]
        n = max(2, int(len(pts) * cr) + 1)
        line(ctx, pts[:n], (*INK, 0.8), 5)
    bottom_strip(ctx, PAPER)


def sc_notsafe(ctx, t, u):
    sc_saved(ctx, t, u, worried=True)


# ------------------------------------------------------------------ section 4
def sc_money(ctx, t, u):
    comp(ctx, scrap_bg("money", SEPIA, COLD, 36))
    jx, jy, jw, jh = W / 2, 520, 420, 520
    n = int(round(14 * (1 - 0.82 * ease(seg(u, 0.05, 0.8)))))
    for k in range(n):
        bill(ctx, jx + 12 * math.sin(k * 1.7), jy + jh / 2 - 30 - k * 26, 2.6, 0.05 * math.sin(k * 2.3))
    jar = [(jx - jw / 2, jy - jh / 2 + 60), (jx - jw / 2 + 20, jy + jh / 2), (jx + jw / 2 - 20, jy + jh / 2), (jx + jw / 2, jy - jh / 2 + 60)]
    line(ctx, jar, (*INK, 0.85), 6)
    poly(ctx, jar + [(jx + jw / 2, jy - jh / 2 + 60)], (0.85, 0.92, 0.98, 0.18), False)
    line(ctx, [(jx - jw / 2 - 20, jy - jh / 2 + 50), (jx + jw / 2 + 20, jy - jh / 2 + 50)], (*INK, 0.85), 8)


def sc_lastbill(ctx, t, u):
    comp(ctx, scrap_bg("lastbill", hexc("#d9d6cf"), hexc("#a9b4bc"), 37))
    gs, gc = new()
    gc.set_source_rgb(1, 1, 1)
    gc.paint()
    rg = cairo.RadialGradient(W / 2, 470, 60, W / 2, 470, 620)
    rg.add_color_stop_rgba(0, 0, 0, 0, 0)
    rg.add_color_stop_rgba(1, 0, 0, 0, 0.7)
    gc.set_source(rg)
    gc.paint()
    m, mc = new()
    mc.rectangle(110, 130, 1700, 730)
    mc.set_source_rgb(1, 1, 1)
    mc.fill()
    halftone(ctx, gs, m, (*INK, 0.5), spacing=12, angle=0.78, maxr=0.55)
    bill(ctx, W / 2, 470 + 14 * math.sin(t * 2.2), 4.2, 0.08 * math.sin(t * 1.3))


def two_cards(ctx, t, gl=0.0, gr=0.0, rl=0.04, rr=-0.04, dl=0.0, dr=0.0):
    card(ctx, 560, 470 + dl, 440, 560, "rocket", rot=rl, grey=gl)
    card(ctx, 1360, 470 + dr, 560, 440, "car", rot=rr, grey=gr)


def sc_allin(ctx, t, u):
    comp(ctx, scrap_bg("allin", SEPIA, COLD, 38))
    fall = ease(seg(u, 0.45, 0.95))
    two_cards(ctx, t, gr=fall, rr=-0.04 - 0.5 * fall, dr=260 * fall ** 2)
    v = ease(seg(u, 0.05, 0.45))
    bill(ctx, W / 2 + (560 - W / 2) * v, 230 + 200 * v - 120 * math.sin(math.pi * v), 2.2, 0.3 * v)


def sc_tearbill(ctx, t, u):
    comp(ctx, scrap_bg("allin", SEPIA, COLD, 38))
    wob = 0.06 * math.sin(t * 7) * ease(seg(u, 0.5, 1.0))
    g = 0.5 * ease(seg(u, 0.5, 1.0))
    two_cards(ctx, t, gl=g, gr=g, rl=0.04 + wob, rr=-0.04 - wob)
    v = ease(seg(u, 0.15, 0.6))
    for side, tx in ((-1, 560), (1, 1360)):
        x = W / 2 + side * 20 * ease(seg(u, 0.05, 0.15)) + (tx - W / 2) * v
        half_bill(ctx, x, 230 + 180 * v, 2.2, side * 0.3 * v, side)


def sc_chose(ctx, t, u):
    comp(ctx, scrap_bg("chose", PAPER, hexc("#f1c9b8"), 39))
    card(ctx, 330, 430, 330, 420, "rocket", rot=0.06)
    card(ctx, 1590, 430, 420, 330, "car", rot=-0.06)
    half_bill(ctx, 330, 560, 1.6, -0.2, -1)
    half_bill(ctx, 1590, 520, 1.6, 0.2, 1)
    tape(ctx, 330, 560, 0.5, 80)
    tape(ctx, 1590, 520, -0.5, 80)
    sl = back_out(seg(u, 0.0, 0.3), 2.0)
    b_toon(ctx, 0.0, "resolve", W / 2, 50 + 120 * (1 - sl), 0.85, rot=0.01)
    bottom_strip(ctx, PAPER)


def sc_kids(ctx, t, u):
    comp(ctx, scrap_bg("kids", PAPER, hexc("#e6d3c2"), 40))
    for side, kind, x in ((-1, "rocket", 400), (1, "car", 1520)):
        sw = 0.08 * math.sin(t * 1.6 + side)
        ax, ay = x, 0
        L_ = 300
        bx, by = ax + L_ * math.sin(sw), ay + L_ * math.cos(sw)
        line(ctx, [(ax, ay), (bx, by)], (*INK, 0.7), 3)
        card(ctx, bx, by + 170, 300 if kind == "rocket" else 360, 360 if kind == "rocket" else 290, kind, rot=sw)
    b_toon(ctx, 0.0, "smile", W / 2, 60, 0.85, rot=-0.01)
    bottom_strip(ctx, PAPER)


# ------------------------------------------------------------------ section 5
def sc_contract(ctx, t, u):
    comp(ctx, scrap_bg("contract", PAPER, hexc("#d7e0e6"), 41))
    card(ctx, 1260, 480, 440, 560, "rocket", rot=0.04)
    drop = ease_out(seg(u, 0.0, 0.35), 3)
    x, y = 640, -500 + 960 * drop
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(-0.08 + 0.1 * (1 - drop))
    pts = torn([(-260, -340), (260, -340), (260, 340), (-260, 340)], seed=5, amp=3, step=10)
    drop_shadow(ctx, lambda c, col: poly(c, pts, col), off=(12, 16), sigma=8, alpha=0.4)
    poly(ctx, pts, (0.99, 0.98, 0.95))
    for k in range(13):
        yy = -280 + k * 40
        line(ctx, [(-200, yy), (200 - (60 if k % 4 == 3 else 0), yy)], (0.3, 0.3, 0.35, 0.35), 6)
    st = back_out(seg(u, 0.4, 0.6), 2.5)
    if st > 0:
        ctx.save()
        ctx.translate(120, 220)
        ctx.scale(st, st)
        ctx.arc(0, 0, 80, 0, 2 * math.pi)
        ctx.set_source_rgba(*RED, 0.85)
        ctx.set_line_width(10)
        ctx.stroke()
        ctx.arc(0, 0, 58, 0, 2 * math.pi)
        ctx.set_line_width(4)
        ctx.stroke()
        pts_s = [(56 * math.cos(-math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45),
                  56 * math.sin(-math.pi / 2 + k * math.pi / 5) * (1 if k % 2 == 0 else 0.45)) for k in range(10)]
        poly(ctx, pts_s, (*RED, 0.85))
        ctx.restore()
    ctx.restore()


def sc_door(ctx, t, u):
    comp(ctx, scrap_bg("door", SEPIA, COLD, 42))
    card(ctx, W / 2, 470, 640, 500, "car", rot=0.0)
    c = ease(seg(u, 0.1, 0.65))
    gap = 520 * (1 - c)
    for side in (-1, 1):
        x_in = W / 2 + side * gap
        x_out = W / 2 + side * 1100
        pts = [(x_in, 150), (x_out, 150), (x_out, 860), (x_in, 860)]
        drop_shadow(ctx, lambda cc, col: poly(cc, pts, col), off=(side * -10, 8), sigma=6, alpha=0.4)
        poly(ctx, pts, hexc("#5d6470"))
        for k in range(5):
            xx = x_in + side * (60 + k * 120)
            line(ctx, [(xx, 170), (xx, 840)], (0.25, 0.27, 0.3, 0.5), 4)
    bottom_strip(ctx, SEPIA)


def sc_xmas(ctx, t, u):
    if "xmas" not in V._cache:
        s, c = new()
        V.paper_bg(c, seed=51)
        poly(c, torn([(70, 50), (1850, 30), (1880, 1000), (40, 1030)], seed=52, amp=9, step=14), hexc("#24304a"))
        V._cache["xmas"] = s
    comp(ctx, V._cache["xmas"])
    rnd = random.Random(53)
    for i in range(90):
        x = (rnd.uniform(0, W) + 30 * math.sin(t + i)) % W
        y = (rnd.uniform(0, H) + t * rnd.uniform(40, 90)) % 980 + 40
        r = rnd.uniform(4, 10)
        poly(ctx, torn([(x + r * math.cos(a), y + r * math.sin(a)) for a in [k * math.pi / 3 for k in range(6)]], seed=i, amp=1.5, step=4),
             (0.97, 0.97, 0.95, 0.9))
    cx, cy, r = 700, 460, 260
    disc = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [k * math.pi / 32 for k in range(64)]]
    drop_shadow(ctx, lambda c, col: poly(c, disc, col), off=(10, 12), sigma=6, alpha=0.4)
    poly(ctx, disc, (0.97, 0.95, 0.9))
    for k in range(12):
        a = k * math.pi / 6
        line(ctx, [(cx + 0.82 * r * math.cos(a), cy + 0.82 * r * math.sin(a)), (cx + 0.94 * r * math.cos(a), cy + 0.94 * r * math.sin(a))], INK, 8 if k % 3 == 0 else 4)
    m_ang = -math.pi / 2 - 0.5 + 0.48 * ease(u)
    line(ctx, [(cx, cy), (cx + 0.75 * r * math.cos(m_ang), cy + 0.75 * r * math.sin(m_ang))], INK, 10)
    line(ctx, [(cx, cy), (cx + 0.5 * r * math.cos(-math.pi / 2 - 0.04), cy + 0.5 * r * math.sin(-math.pi / 2 - 0.04))], INK, 14)
    ctx.arc(cx, cy, 14, 0, 2 * math.pi)
    ctx.set_source_rgb(*RED)
    ctx.fill()
    # empty pay envelopes
    for i in range(3):
        ex, ey = 1240 + i * 170, 560 + 30 * math.sin(i)
        ctx.save()
        ctx.translate(ex, ey)
        ctx.rotate(0.1 * (i - 1))
        pts = [(-80, -55), (80, -55), (80, 55), (-80, 55)]
        drop_shadow(ctx, lambda c, col: poly(c, pts, col), off=(6, 8), sigma=4, alpha=0.35)
        poly(ctx, pts, (0.93, 0.88, 0.78))
        line(ctx, [(-80, -55), (0, 5), (80, -55)], (*INK, 0.5), 3)
        ctx.restore()


def sc_allcash(ctx, t, u):
    comp(ctx, scrap_bg("allcash", PAPER, hexc("#f1c9b8"), 43))
    card(ctx, 1440, 470, 560, 440, "car", rot=-0.04)
    b_toon(ctx, 0.0, "resolve", 520, 60, 0.82, rot=0.01)
    rnd = random.Random(91)
    for i in range(14):
        st = rnd.uniform(0, 0.6)
        v = ease(seg(u, st, st + 0.35))
        if v <= 0 or v >= 1:
            continue
        x = 760 + (1440 - 760) * v
        y = 520 - 200 * math.sin(math.pi * v) + rnd.uniform(-40, 40)
        bill(ctx, x, y, 1.1 * (1 - 0.5 * v), rnd.uniform(-1, 1) + 3 * v)
    bottom_strip(ctx, PAPER)


def sc_nohouse(ctx, t, u):
    comp(ctx, scrap_bg("nohouse", hexc("#d9d6cf"), hexc("#a9b4bc"), 44))
    hx, hy = 1250, 560
    house = [(hx - 280, hy + 220), (hx - 280, hy - 60), (hx, hy - 300), (hx + 280, hy - 60), (hx + 280, hy + 220)]
    line(ctx, house + [house[0]], (*INK, 0.7), 5, dash=[22, 16])
    line(ctx, [(hx - 70, hy + 220), (hx - 70, hy + 60), (hx + 70, hy + 60), (hx + 70, hy + 220)], (*INK, 0.5), 4, dash=[16, 12])
    # blank sign on a post
    sx, sy = hx + 420, hy + 220
    line(ctx, [(sx, sy), (sx, sy - 280)], hexc("#6b4f3a"), 10)
    pts = [(sx - 110, sy - 360), (sx + 110, sy - 360), (sx + 110, sy - 230), (sx - 110, sy - 230)]
    drop_shadow(ctx, lambda c, col: poly(c, pts, col), off=(6, 8), sigma=4, alpha=0.35)
    poly(ctx, pts, (0.98, 0.97, 0.94))
    b_toon(ctx, 0.0, "low", 520, 120, 0.66, rot=-0.02)
    bottom_strip(ctx, hexc("#d9d6cf"))


# ------------------------------------------------------------------ section 6
def sc_18(ctx, t, u):
    comp(ctx, bg_night())
    e = ease(seg(u, 0.0, 0.45))
    x = W * (-0.15 + 1.5 * e)
    pts = [(W + 50, -50), (x - 200, -50), (x, H / 2), (x - 160, H + 50), (W + 50, H + 50)]
    edge = torn(pts, seed=19, amp=14, step=18)
    pop = back_out(seg(u, 0.35, 0.7), 1.8)
    if pop > 0:
        poly(ctx, torn([(560, 120), (1360, 110), (1370, 880), (550, 890)], seed=61, amp=8), hexc("#2c3a5a"))
        b_toon(ctx, 1.0, "smile", W / 2, 60 + 160 * (1 - pop), 0.82, rot=0.015)
    ctx.save()
    path(ctx, edge, True, False)
    ctx.clip()
    comp(ctx, scrap_bg("nohouse", hexc("#d9d6cf"), hexc("#a9b4bc"), 44))
    ctx.restore()
    line(ctx, edge[1:-2], (0.97, 0.95, 0.9), 10)


def sc_apex(ctx, t, u):
    sc_stunt(ctx, 2.6 + 1.1 * u)


def sc_bet(ctx, t, u):
    comp(ctx, bg_night())
    hov = 8 * math.sin(t * 2)
    draw_car(ctx, (W / 2, 250 + hov), 0.0, 90)
    tissue_jet(ctx, (W / 2 - 50, 250 + hov), (0, 1), 160, 0.8, seed=3)
    tissue_jet(ctx, (W / 2 + 46, 250 + hov), (0, 1), 160, 0.8, seed=4)
    b_toon(ctx, 0.0, "resolve", 470, 260, 0.6, rot=-0.03)
    half_bill(ctx, 300, 760, 1.3, -0.2, -1)
    half_bill(ctx, 640, 760, 1.3, 0.2, 1)
    sl = back_out(seg(u, 0.1, 0.45), 1.6)
    if sl > 0:
        b_toon(ctx, 1.0, "resolve", 1430, 150 + 140 * (1 - sl), 0.75, rot=0.02)
    poly(ctx, torn([(0, 880), (W, 870), (W, H + 40), (0, H + 40)], seed=33, amp=7), hexc("#2c2f36"))


# ------------------------------------------------------------------ section 7
def sc_quote(ctx, t, u):
    comp(ctx, scrap_bg("quote", PAPER, hexc("#f1d9c6"), 45))
    burst(ctx, W / 2, 470, (1, 1, 1, 0.45), n=22, rot=t * 0.08)
    b_toon(ctx, 1.0, "resolve", W / 2, 40, 0.9, rot=0.0, zoom=1.0 + 0.04 * u)
    bottom_strip(ctx, PAPER)


def sc_quiet(ctx, t, u):
    sc_crowd(ctx, t, u)
    fade = ease(seg(u, 0.1, 0.9))
    ctx.rectangle(0, 0, W, H)
    ctx.set_source_rgba(*PAPER, 0.75 * fade)
    ctx.fill()


def sc_end(ctx, t, u):
    comp(ctx, bg_night())
    v = ease(seg(u, 0.05, 0.75))
    x = 700 + 1500 * v ** 1.4
    draw_car(ctx, (x, TR.ground), 0.0, CAR_L)
    for k in range(4):
        y = TR.ground - 20 - 18 * k
        line(ctx, [(x - CAR_L - 40 - 60 * k, y), (x - CAR_L - 200 - 60 * k, y)], (0.95, 0.93, 0.88, 0.5 * v), 3)
    fade = ease(seg(t, DURATION - 1.0, DURATION))
    if fade > 0:
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(*PAPER, fade)
        ctx.fill()


# ------------------------------------------------------------------ timeline
def first(fn):
    return lambda c, t, u: fn(c, t, u)


SCENES = [(0.0, V.SCENES[-1][1], None)]  # sections 1-2 delegated to b_video
SCENES += [
    (*span(15), sc_last), (*span(16), sc_launch), (*span(17), sc_orbit), (*span(18), sc_saved), (*span(19), sc_notsafe),
    (*span(20), sc_money), (*span(21), sc_lastbill), (*span(22), sc_allin), (*span(23), sc_tearbill), (*span(24), sc_chose),
    (*span(25), sc_kids),
    (*span(26), sc_contract), (*span(27), sc_door), (*span(28), sc_xmas), (*span(29), sc_allcash), (*span(30), sc_nohouse),
    (*span(31), sc_18), (*span(32), lambda c, t, u: sc_crowd(c, t, u)), (*span(33), sc_apex), (*span(34), sc_bet),
    (*span(35), sc_quote), (*span(36), sc_quiet), (START[37], DURATION, sc_end),
]


def caption(ctx, t):
    for i, s in enumerate(LINES):
        a, b = START[i], END[i]
        if a <= t < b:
            u = seg(t, a, a + 0.25)
            out = seg(t, b - 0.18, b) if i < len(LINES) - 1 else seg(t, DURATION - 1.0, DURATION - 0.6)
            if u <= 0 or out >= 1:
                return
            last = s in ("他没有。", "是继续往前押。")
            size = 74 if s == "他没有。" else 50
            ctx.save()
            ctx.select_font_face("Noto Sans CJK SC", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(size)
            wid = sum(ctx.text_extents(ch).x_advance for ch in s) * (1 + 0.06)
            ctx.restore()
            if wid > 1680:
                size *= 1680 / wid
            y = 1000 + 30 * (1 - back_out(u)) + 40 * ease(out)
            ctx.push_group()
            tape_label(ctx, s, W / 2, y, size, rot=-0.012 if not last else 0.02, bg=RED if last else INK)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(min(1, u * 3) * (1 - out))
            return
    # the final card holds through the tail until the fade
    if t >= END[-1] - 0.01 and t < DURATION - 0.6:
        tape_label(ctx, LINES[-1], W / 2, 1000, 50, rot=0.02, bg=RED)


def frame(t):
    surf, ctx = new()
    if t < V.SCENES[-1][1]:
        for (a, b, fn) in V.SCENES:
            if a <= t < b:
                fn(ctx, t, seg(t, a, b))
                break
    else:
        for (a, b, fn) in SCENES[1:]:
            if a <= t < b or (b == DURATION and t >= a):
                fn(ctx, t, seg(t, a, b))
                break
    caption(ctx, t)
    grain(surf, 4, seed=int(round(t * 30)) // 4 % 12)
    return surf


if __name__ == "__main__":
    for i, s in enumerate(LINES):
        a = START[i]
        print(f"{a:6.2f}-{END[i]:6.2f}  {s}")
    print("duration", DURATION)
