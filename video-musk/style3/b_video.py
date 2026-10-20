"""Direction B, sections 1-2 (to 「他没有。」): frame(t) for the whole cut, plus storyboard export.

Every on-screen line is copied verbatim from script_v0.4.1.md, in order, one line per card.
"""
import math
import os
import random
import sys

import cairo

import frames as F
from frames import (W, H, new, comp, blurred, grain, paper_bg, torn, drop_shadow, halftone, tape_label, b_toon,
                    poly, line, text, hexc, mix, INK, RED, PAPER, TR, track_strips, track_rails, underside,
                    truss_lines, plume_pts, off, CAR_L)
from geo import path, CAR_BODY, CAR_GLASS, WHEELS

NIGHT = hexc("#1f2b45")
SEPIA = hexc("#e9dcc3")
COLD = hexc("#c9d3d8")

# (start, end, text) — verbatim, in script order
CARDS = [
    (0.2, 3.0, "十月，一辆跑车离开地面。"),
    (3.0, 6.6, "短暂悬停。翻转。再落下。"),
    (6.6, 9.6, "推进器装进车里——不是科幻片，是刚发布的演示。"),
    (9.6, 12.0, "口约：二〇二八年才可能量产。"),
    (12.0, 14.0, "全场在看热闹。"),
    (14.0, 16.6, "可要看懂这一飞，得先看另一个画面。"),
    (16.6, 18.2, "二零零八年。"),
    (18.2, 20.2, "两家公司，都快死了。"),
    (20.2, 23.2, "连他自己都觉得：活下来的概率，不到百分之十。"),
    (23.2, 25.4, "火箭，连续三次失败。"),
    (25.4, 27.4, "电动车，在烧钱。"),
    (27.4, 29.6, "同一年，婚姻也走到头。"),
    (29.6, 32.2, "他说：那是他人生最糟的一年之一。"),
    (32.2, 34.2, "按常理，该收手了。"),
    (34.2, 36.6, "他没有。"),
]
DURATION = 36.6


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= b)


def ease(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def ease_out(u, p=2):
    return 1 - (1 - clamp(u)) ** p


def back_out(u, s=1.6):
    u = clamp(u) - 1
    return u * u * ((s + 1) * u + s) + 1


# ------------------------------------------------------------------ car (generic pose)
def car_f(pos, th, L):
    hx, hy = math.cos(th), math.sin(th)
    ux, uy = math.sin(th), -math.cos(th)

    def f(p):
        x, y = p
        return (pos[0] + x * L * hx - y * L * ux, pos[1] + x * L * hy - y * L * uy)
    return f, (ux, uy), (hx, hy)


def draw_car(ctx, pos, th, L=CAR_L, col=RED, shadow=True):
    f, up, hd = car_f(pos, th, L)
    body = [f(p) for p in CAR_BODY]
    if shadow:
        drop_shadow(ctx, lambda c, cc: poly(c, body, cc), off=(8, 10), sigma=5, alpha=0.4)
    for (cx, cy) in WHEELS:
        c = f((cx, cy))
        ctx.arc(c[0], c[1], 0.15 * L, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
        ctx.arc(c[0], c[1], 0.07 * L, 0, 2 * math.pi)
        ctx.set_source_rgb(0.75, 0.73, 0.7)
        ctx.fill()
    poly(ctx, body, col)
    poly(ctx, [f(p) for p in CAR_GLASS], INK, True)
    line(ctx, [f((-0.9, -0.24)), f((0.0, -0.3)), f((0.9, -0.2))], (1, 1, 1, 0.35), 2.0, smooth=True)
    line(ctx, body + [body[0]], (0.45, 0.08, 0.06, 0.7), 1.6)
    return f, up, hd


ROOF_N = [(-0.62, -0.36), (0.55, -0.34)]
FLOOR_N = [(-0.62, -0.05), (0.55, -0.05)]


def tissue_jet(ctx, base, d, length, k, seed=0, far=False):
    """Cold-gas jet as layered torn tissue (white / pale blue). k = intensity 0..1."""
    if k <= 0.02:
        return
    fk = (0.6 if far else 1.0) * k
    for j, (ln, w0, w1, col, al) in enumerate(((1.0, 8, 50, (0.78, 0.88, 1.0), 0.45), (0.72, 6, 32, (0.92, 0.96, 1.0), 0.7),
                                                 (0.4, 3, 14, (1, 1, 1), 0.95))):
        pl = torn(plume_pts(base, d, length * ln * (0.5 + 0.5 * k), w0, w1 * (0.6 + 0.4 * k), 10, seed=seed + j),
                  seed=seed * 7 + j, amp=5, step=11)
        poly(ctx, pl, (*col, al * fk))


def jets_from(ctx, f, nozzles, d, intens, length=360, seed=0):
    for i, (nz, k) in enumerate(zip(nozzles, intens)):
        b = f(nz)
        tissue_jet(ctx, off(b, 0.7), d, length * 0.85, k, seed=seed + 10 + i, far=True)
    for i, (nz, k) in enumerate(zip(nozzles, intens)):
        tissue_jet(ctx, f(nz), d, length, k, seed=seed + i)


def dust(ctx, x, y, amt, seed=0):
    if amt <= 0.02:
        return
    rnd = random.Random(seed)
    for i in range(14):
        dx = rnd.uniform(-1, 1)
        r = (20 + 40 * rnd.random()) * (0.5 + amt)
        cx, cy = x + dx * 180 * (0.4 + amt), y - rnd.uniform(0, 40) * amt
        poly(ctx, torn([(cx + r * math.cos(a), cy + 0.6 * r * math.sin(a)) for a in [k * math.pi / 5 for k in range(10)]],
                       seed=seed + i, amp=4, step=8), (0.86, 0.85, 0.83, 0.55 * amt))


# ------------------------------------------------------------------ stunt kinematics
A_TOP = 0.96 * math.pi
LAND_X = 960


def car_pose(t):
    """Returns pos (wheel-contact point), heading th, jets dict."""
    jets = {"roof": (0, 0), "floor": (0, 0)}
    if t < 1.0:
        x = 260 + 820 * t
        return (x, TR.ground), 0.0, jets, 0.0
    if t < 2.3:
        a = A_TOP * ease_out(seg(t, 1.0, 2.3), 2)
        (px, py), (tx, ty) = TR.at(a)
        return (px, py), math.atan2(ty, tx), jets, 0.0
    (px, py), (tx, ty) = TR.at(A_TOP)
    nx, ny = TR.normal_in(A_TOP)
    th0 = math.atan2(ty, tx)
    if th0 < 0:
        th0 += 2 * math.pi
    if t < 3.9:
        u = seg(t, 2.3, 3.9)
        gap = 16 * ease(seg(t, 2.3, 2.7)) + 3 * math.sin(u * 2 * math.pi * 2)
        k = ease(seg(t, 2.25, 2.5))
        jets["roof"] = (k, k)
        return (px + nx * gap, py + ny * gap), th0, jets, 0.0
    up0 = (math.sin(th0), -math.cos(th0))
    c0 = (px + nx * 16 - up0[0] * 0.22 * CAR_L, py + ny * 16 - up0[1] * 0.22 * CAR_L)
    c1 = (LAND_X, TR.ground - 0.22 * CAR_L)
    if t < 5.5:
        u = seg(t, 3.9, 5.5)
        th = th0 + (0 - th0) * ease(seg(t, 3.9, 5.1))
        x = c0[0] + (c1[0] - c0[0]) * ease(u)
        fall = u ** 1.6 if u < 0.85 else 0.85 ** 1.6 + (1 - 0.85 ** 1.6) * ease((u - 0.85) / 0.15)
        y = c0[1] + (c1[1] - c0[1]) * fall
        up = (math.sin(th), -math.cos(th))
        pos = (x + up[0] * 0.22 * CAR_L, y + up[1] * 0.22 * CAR_L)
        # attitude-correction pulses during the flip, then floor jets cushion the landing
        p1 = max(0.0, math.sin((t - 3.9) * 2 * math.pi * 2.2)) * (1 - seg(t, 4.9, 5.1))
        p2 = max(0.0, math.sin((t - 3.9) * 2 * math.pi * 2.2 + math.pi)) * (1 - seg(t, 4.9, 5.1))
        jets["roof"] = (p1, p2)
        cush = seg(t, 4.95, 5.15) * (1 - seg(t, 5.45, 5.7))
        jets["floor"] = (cush, cush)
        return pos, th, jets, 0.0
    bounce = 6 * math.exp(-(t - 5.5) * 6) * abs(math.sin((t - 5.5) * 18))
    cush = 1 - seg(t, 5.45, 5.75)
    jets["floor"] = (cush, cush)
    return (LAND_X, TR.ground - bounce), 0.0, jets, ease(seg(t, 5.45, 5.6)) * (1 - seg(t, 5.8, 6.6))


# ------------------------------------------------------------------ backgrounds (cached)
_cache = {}


def bg_night():
    if "night" not in _cache:
        s, ctx = new()
        paper_bg(ctx, seed=1)
        sky = torn([(70, 50), (1850, 30), (1880, 1000), (40, 1030)], seed=4, amp=9, step=14)
        drop_shadow(ctx, lambda c, col: poly(c, sky, col), off=(10, 12), sigma=8, alpha=0.35)
        poly(ctx, sky, NIGHT)
        gs, gc = new()
        gc.set_source_rgb(1, 1, 1)
        gc.paint()
        rg = cairo.RadialGradient(1050, 300, 20, 1050, 300, 520)
        rg.add_color_stop_rgba(0, 0, 0, 0, 0.55)
        rg.add_color_stop_rgba(1, 0, 0, 0, 0)
        gc.set_source(rg)
        gc.paint()
        clip, cc = new()
        poly(cc, sky, (1, 1, 1))
        halftone(ctx, gs, clip, (0.55, 0.7, 0.9, 0.55), spacing=14, angle=0.3, maxr=0.6)
        gnd = torn([(40, TR.ground + 4), (1880, TR.ground - 6), (1880, 1030), (40, 1030)], seed=8, amp=5)
        poly(ctx, gnd, hexc("#2c2f36"))
        rnd = random.Random(5)
        for (a, b) in truss_lines():
            mid = ((a[0] + b[0]) / 2 + rnd.uniform(-2, 2), (a[1] + b[1]) / 2 + rnd.uniform(-2, 2))
            line(ctx, [a, mid, b], (0.92, 0.9, 0.85, 0.85), 2.4, smooth=True)
        cl, strips = track_strips()
        near, farr = track_rails(cl, -1), track_rails(cl, 1)
        shape = near + farr[::-1]
        drop_shadow(ctx, lambda c, col: poly(c, shape, col), off=(12, 14), sigma=6, alpha=0.45)
        poly(ctx, shape, hexc("#d9d5cc"))
        us = underside(cl, strips, 16)
        poly(ctx, near + track_rails(us, -1)[::-1], hexc("#9c978e"))
        sd, sdc = new()
        sdc.set_source_rgb(1, 1, 1)
        sdc.paint()
        for q, nrm, a in strips:
            k = 0.45 + 0.55 * max(0.0, nrm[0] * -0.72 + nrm[1] * 0.36)
            path(sdc, q, True, False)
            sdc.set_source_rgb(k, k, k)
            sdc.fill_preserve()
            sdc.set_line_width(1)
            sdc.stroke()
        tc_, tcc = new()
        poly(tcc, shape, (1, 1, 1))
        halftone(ctx, sd, tc_, (*INK, 0.55), spacing=7, angle=0.78, maxr=0.55)
        rnd = random.Random(9)
        jit = lambda pts: [(x + rnd.uniform(-1.2, 1.2), y + rnd.uniform(-1.2, 1.2)) for x, y in pts[::3]]
        line(ctx, jit(near), RED, 4.2, smooth=True)
        line(ctx, jit(farr), RED, 3.4, smooth=True)
        line(ctx, track_rails(cl, 0.08), (0.15, 0.15, 0.17, 0.7), 2.2, dash=[22, 20])
        _cache["night"] = s
    return _cache["night"]


def bg_paper(key, col, scraps=(), seed=0):
    if key not in _cache:
        s, ctx = new()
        paper_bg(ctx, col=col, seed=seed, lines=True)
        for i, (pts, c) in enumerate(scraps):
            pp = torn(pts, seed=seed + i, amp=8)
            drop_shadow(ctx, lambda cc, col_: poly(cc, pp, col_), off=(6, 8), sigma=5, alpha=0.25)
            poly(ctx, pp, c)
        _cache[key] = s
    return _cache[key]


# ------------------------------------------------------------------ props
def cutout(ctx, draw, sh=(8, 10, 5, 0.35)):
    drop_shadow(ctx, lambda c, col: draw(c, col), off=sh[:2], sigma=sh[2], alpha=sh[3])
    draw(ctx, None)


def rocket(ctx, cx, cy, h, rot=0.0, col=(0.97, 0.96, 0.93), broken=0.0, seed=0):
    w = h * 0.2
    parts = {
        "nose": [(0, -h / 2), (w * 0.55, -h / 2 + h * 0.18), (-w * 0.55, -h / 2 + h * 0.18)],
        "upper": [(-w / 2, -h / 2 + h * 0.18), (w / 2, -h / 2 + h * 0.18), (w / 2, 0), (-w / 2, 0)],
        "lower": [(-w / 2, 0), (w / 2, 0), (w / 2, h * 0.42), (-w / 2, h * 0.42)],
        "finl": [(-w / 2, h * 0.2), (-w * 1.1, h * 0.5), (-w / 2, h * 0.42)],
        "finr": [(w / 2, h * 0.2), (w * 1.1, h * 0.5), (w / 2, h * 0.42)],
    }
    rnd = random.Random(seed)
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    for i, (k, pts) in enumerate(parts.items()):
        dx = dy = r = 0.0
        if broken > 0:
            dx = rnd.uniform(-1, 1) * h * 0.5 * broken
            dy = (rnd.uniform(-0.6, 0.4) * h * 0.4 + h * 0.25 * broken ** 2) * broken
            r = rnd.uniform(-1.5, 1.5) * broken
        ctx.save()
        ctx.translate(dx, dy)
        ctx.rotate(r)
        c = RED if k in ("finl", "finr", "nose") else col
        pp = torn(pts, seed=seed + i, amp=1.5, step=8) if broken > 0 else pts
        poly(ctx, pp, c)
        line(ctx, pp + [pp[0]], (*INK, 0.8), 2.5)
        if k == "upper":
            ctx.arc(0, -h * 0.16, w * 0.22, 0, 2 * math.pi)
            ctx.set_source_rgb(*INK)
            ctx.fill()
        ctx.restore()
    ctx.restore()


def smoke(ctx, cx, cy, amt, seed=0, col=(0.55, 0.55, 0.57)):
    if amt <= 0.02:
        return
    rnd = random.Random(seed)
    for i in range(12):
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(0, 90) * amt
        r = (30 + rnd.uniform(0, 50)) * (0.4 + amt)
        x, y = cx + d * math.cos(a), cy + d * math.sin(a) - 30 * amt
        poly(ctx, torn([(x + r * math.cos(b), y + r * math.sin(b)) for b in [k * math.pi / 5 for k in range(10)]],
                       seed=seed * 3 + i, amp=5, step=9), (*col, 0.75 * min(1, 2 * (1 - amt) + 0.3)))


def bill(ctx, cx, cy, s, rot, ash=0.0):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(rot)
    w, h = 120 * s, 58 * s
    col = mix(hexc("#a9c3a2"), (0.55, 0.55, 0.55), ash)
    pts = torn([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)], seed=int(cx), amp=1.5 + 4 * ash, step=7)
    poly(ctx, pts, (*col, 1 - 0.7 * ash))
    ctx.rectangle(-w / 2 + 6 * s, -h / 2 + 6 * s, w - 12 * s, h - 12 * s)
    ctx.set_source_rgba(0.2, 0.35, 0.22, 0.5 * (1 - ash))
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.arc(0, 0, h * 0.28, 0, 2 * math.pi)
    ctx.stroke()
    ctx.restore()


def person(ctx, cx, cy, s, col=INK, hair=False):
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(s, s)
    poly(ctx, [(-70, 110), (-60, 40), (-26, 22), (26, 22), (60, 40), (70, 110)], col, True)
    ctx.arc(0, -10, 34, 0, 2 * math.pi)
    ctx.set_source_rgb(*col)
    ctx.fill()
    if hair:
        poly(ctx, [(-34, -14), (-30, -40), (0, -52), (30, -40), (36, -10), (24, -30), (-20, -30)], col, True)
    ctx.restore()


def flag(ctx, x, y, h, wave, grey=0.0, crumple=0.0):
    col = mix((0.98, 0.97, 0.94), (0.75, 0.75, 0.75), grey)
    line(ctx, [(x, y), (x, y - h)], hexc("#6b4f3a"), 8)
    pts = []
    for i in range(9):
        u = i / 8
        pts.append((x + 6 + u * h * 0.55, y - h + 6 + 10 * math.sin(u * 5 + wave)))
    for i in range(9):
        u = 1 - i / 8
        pts.append((x + 6 + u * h * 0.55, y - h + h * 0.34 + 10 * math.sin(u * 5 + wave)))
    if crumple > 0:
        cxm = sum(p[0] for p in pts) / len(pts)
        cym = sum(p[1] for p in pts) / len(pts)
        pts = [(cxm + (px - cxm) * (1 - 0.8 * crumple), cym + (py - cym) * (1 - 0.8 * crumple)) for px, py in pts]
        pts = torn(pts, seed=3, amp=6 * crumple, step=8)
    drop_shadow(ctx, lambda c, cc: poly(c, pts, cc), off=(6, 8), sigma=4, alpha=0.3)
    poly(ctx, pts, col, crumple == 0)


# ------------------------------------------------------------------ caption
def caption(ctx, t):
    for (a, b, s) in CARDS:
        if a <= t < b:
            u = seg(t, a, a + 0.25)
            out = seg(t, b - 0.18, b)
            last = s == "他没有。"
            size = 74 if last else 50
            y = 1000 + 30 * (1 - back_out(u)) + 40 * ease(out)
            if u <= 0 or out >= 1:
                return
            ctx.push_group()
            tape_label(ctx, s, W / 2, y, size, rot=-0.012 if not last else 0.02, bg=RED if last else INK)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(min(1, u * 3) * (1 - out))
            return


# ------------------------------------------------------------------ scenes
def sc_stunt(ctx, t):
    comp(ctx, bg_night())
    pos, th, jets, dust_amt = car_pose(t)
    f, up, hd = car_f(pos, th, CAR_L)
    d_roof = up
    d_floor = (-up[0], -up[1])
    if t < 1.0:  # speed lines
        for k in range(5):
            y = pos[1] - 20 - 18 * k
            line(ctx, [(pos[0] - CAR_L - 40 - 60 * k, y), (pos[0] - CAR_L - 220 - 60 * k, y)], (0.95, 0.93, 0.88, 0.6), 3)
    ctx.save()
    ctx.rectangle(0, 0, W, TR.ground + 2)
    ctx.clip()
    jets_from(ctx, f, ROOF_N, d_roof, jets["roof"], 380, seed=1)
    jets_from(ctx, f, FLOOR_N, d_floor, jets["floor"], 220, seed=5)
    ctx.restore()
    dust(ctx, pos[0], TR.ground, dust_amt, seed=2)
    draw_car(ctx, pos, th)


def sc_inside(ctx, t, u):
    """推进器装进车里: big cut-away of the car, tanks + 4 nozzles, little test puffs."""
    comp(ctx, bg_paper("inside", PAPER, [([(160, 140), (1760, 120), (1780, 860), (140, 880)], hexc("#d7e0e6"))], seed=11))
    zoom = 1.0 + 0.06 * u
    L = 450 * zoom
    pos = (W / 2 + 20, 600)
    f, up, hd = draw_car(ctx, pos, 0.0, L)
    # torn x-ray window
    win = torn([f((-0.36, -0.07)), f((0.36, -0.07)), f((0.33, -0.27)), f((-0.33, -0.27))], seed=13, amp=5, step=12)
    poly(ctx, win, hexc("#20304f"))
    gs, gc = new()
    gc.set_source_rgb(0.6, 0.6, 0.6)
    gc.paint()
    cl, cc = new()
    poly(cc, win, (1, 1, 1))
    halftone(ctx, gs, cl, (0.55, 0.7, 0.95, 0.45), spacing=10, angle=0.3, maxr=0.5)
    for cx in (-0.17, 0.17):  # gas tanks
        a, b = f((cx - 0.14, -0.23)), f((cx + 0.14, -0.12))
        x0, y0, x1, y1 = a[0], a[1], b[0], b[1]
        r = (y1 - y0) / 2
        ctx.new_sub_path()
        ctx.arc(x0 + r, y0 + r, r, math.pi / 2, 3 * math.pi / 2)
        ctx.arc(x1 - r, y0 + r, r, -math.pi / 2, math.pi / 2)
        ctx.close_path()
        ctx.set_source_rgb(0.92, 0.94, 0.97)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
    noz = [(-0.62, -0.06), (-0.5, -0.06), (0.5, -0.06), (0.62, -0.06)]
    for i, n in enumerate(noz):
        p = f(n)
        tank = f((-0.17 if n[0] < 0 else 0.17, -0.12))
        line(ctx, [tank, (p[0], tank[1]), p], (0.85, 0.88, 0.95), 4)
        ctx.arc(p[0], p[1], 12, 0, 2 * math.pi)
        ctx.set_source_rgb(0.85, 0.92, 1.0)
        ctx.fill_preserve()
        ctx.set_source_rgb(*INK)
        ctx.set_line_width(3)
        ctx.stroke()
        k = 0.35 + 0.65 * max(0.0, math.sin((t * 2.4 + i * 0.25) * math.pi)) ** 2
        tissue_jet(ctx, p, (0, 1), 230, k, seed=30 + i)


def sc_mass(ctx, t, u):
    """口约：二〇二八年才可能量产 — a row of car outlines still only drawn as dashed cut lines."""
    comp(ctx, bg_paper("mass", PAPER, [([(100, 200), (1820, 180), (1830, 820), (90, 840)], hexc("#e2d6c2"))], seed=12))
    line(ctx, [(60, 700), (1860, 700)], (*INK, 0.7), 6)
    for k in range(40):
        x = (k * 60 - (t * 80) % 60)
        line(ctx, [(x, 714), (x + 24, 714)], (*INK, 0.5), 3)
    LM = 210
    for i in range(4):
        cx = 330 + i * 470 - 60 * u
        f, up, hd = car_f((cx, 690), 0.0, LM)
        body = [f(p) for p in CAR_BODY]
        if i == 0:
            draw_car(ctx, (cx, 690), 0.0, LM)
        else:
            line(ctx, body + [body[0]], (*INK, 0.75 - 0.1 * i), 3, dash=[14, 10])
            for (wx, wy) in WHEELS:
                c = f((wx, wy))
                ctx.arc(c[0], c[1], 0.15 * LM, 0, 2 * math.pi)
                ctx.set_source_rgba(*INK, 0.6 - 0.08 * i)
                ctx.set_line_width(3)
                ctx.set_dash([10, 8])
                ctx.stroke()
                ctx.set_dash([])
    # scissors nibbling along the second outline
    p = 0.15 + 0.7 * u
    f, up, hd = car_f((800 - 60 * u, 690), 0.0, LM)
    idx = int(p * (len(CAR_BODY) - 1))
    sx, sy = f(CAR_BODY[idx])
    open_ = 0.25 + 0.2 * abs(math.sin(t * 9))
    ctx.save()
    ctx.translate(sx, sy)
    for sgn in (1, -1):
        ctx.save()
        ctx.rotate(-0.6 + sgn * open_)
        poly(ctx, [(0, -9), (170, -3), (170, 5), (0, 9)], (0.75, 0.77, 0.8))
        line(ctx, [(0, -9), (170, -3), (170, 5), (0, 9), (0, -9)], (*INK, 0.7), 2)
        ctx.arc(-56, 0, 32, 0, 2 * math.pi)
        ctx.set_source_rgb(*RED)
        ctx.set_line_width(9)
        ctx.stroke()
        ctx.restore()
    ctx.restore()


def sc_crowd(ctx, t, u):
    comp(ctx, bg_night())
    # the car, small, still in the air above the crowd
    draw_car(ctx, (1080, 300 - 20 * math.sin(t * 2)), 0.0, 80)
    tissue_jet(ctx, (1080 - 40, 300), (0, 1), 180, 0.7, seed=3)
    tissue_jet(ctx, (1080 + 36, 300), (0, 1), 180, 0.7, seed=4)
    rnd = random.Random(21)
    rows = ((760, 0.95, hexc("#3a3f4a")), (840, 1.15, hexc("#24272e")), (930, 1.35, INK))
    for r, (y, s, col) in enumerate(rows):
        for i in range(12):
            x = -60 + i * 175 + (r % 2) * 85 + rnd.uniform(-20, 20)
            bob = 6 * math.sin(t * 6 + i + r)
            person(ctx, x, y + bob, s, col)
            if rnd.random() < 0.45:  # phone held up, screen lit
                px, py = x + rnd.uniform(-30, 30) * s, y - 70 * s + bob
                ctx.rectangle(px - 12 * s, py - 20 * s, 24 * s, 40 * s)
                ctx.set_source_rgb(0.85, 0.93, 1.0)
                ctx.fill()


def sc_tear(ctx, t, u):
    """Night sheet is torn away, revealing the 2008 page underneath."""
    comp(ctx, bg_paper("y2008", SEPIA, [([(200, 120), (1720, 140), (1700, 860), (220, 840)], COLD)], seed=14))
    e = ease(u)
    x = W * (1.15 - 1.5 * e)
    pts = [(-50, -50), (x + 200, -50), (x, H / 2), (x + 160, H + 50), (-50, H + 50)]
    edge = torn(pts, seed=17, amp=14, step=18)
    ctx.save()
    path(ctx, edge, True, False)
    ctx.clip()
    sc_stunt(ctx, 6.0 + u)
    ctx.restore()
    line(ctx, edge[1:-2], (0.97, 0.95, 0.9), 10)


def sc_2008(ctx, t, u):
    comp(ctx, bg_paper("y2008", SEPIA, [([(200, 120), (1720, 140), (1700, 860), (220, 840)], COLD)], seed=14))
    rise = 60 * (1 - back_out(seg(u, 0, 0.5)))
    b_toon(ctx, 0.0, "smile", W / 2, 70 + rise, 0.82, rot=-0.015)
    poly(ctx, torn([(0, 860), (W, 850), (W, H + 40), (0, H + 40)], seed=33, amp=7), SEPIA)


def sc_two(ctx, t, u):
    comp(ctx, bg_paper("two", SEPIA, [([(140, 160), (900, 140), (920, 820), (160, 840)], COLD),
                                      ([(1020, 150), (1780, 170), (1760, 830), (1000, 820)], COLD)], seed=15))
    droop = ease(seg(u, 0.2, 0.9))
    rocket(ctx, 530, 470 + 40 * droop, 520, rot=-0.35 * droop)
    draw_car(ctx, (1390, 620 + 30 * droop), -0.18 * droop, 260)
    gs, gc = new()
    gc.set_source_rgb(1, 1, 1)
    gc.paint()
    g = cairo.LinearGradient(0, 100, 0, 860)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, 0.6 * droop)
    gc.set_source(g)
    gc.paint()
    m, mc = new()
    mc.rectangle(140, 140, 1640, 700)
    mc.set_source_rgb(1, 1, 1)
    mc.fill()
    halftone(ctx, gs, m, (*INK, 0.45), spacing=11, angle=0.78, maxr=0.55)


def sc_odds(ctx, t, u):
    comp(ctx, bg_paper("odds", SEPIA, [([(120, 150), (1800, 130), (1810, 860), (110, 850)], COLD)], seed=16))
    b_toon(ctx, 0.0, "low", 560, 120, 0.72, rot=-0.02)
    cx, cy, r = 1330, 470, 270
    disc = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in [k * math.pi / 32 for k in range(64)]]
    drop_shadow(ctx, lambda c, col: poly(c, disc, col), off=(8, 10), sigma=5, alpha=0.35)
    poly(ctx, disc, (0.97, 0.95, 0.9))
    ang = 2 * math.pi * 0.09 * ease(seg(u, 0.1, 0.6))
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + ang)
    ctx.close_path()
    ctx.set_source_rgb(*RED)
    ctx.fill()
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.set_source_rgb(*INK)
    ctx.set_line_width(4)
    ctx.stroke()
    gs, gc = new()
    gc.set_source_rgb(0.72, 0.72, 0.72)
    gc.paint()
    m, mc = new()
    mc.move_to(cx, cy)
    mc.arc(cx, cy, r, -math.pi / 2 + ang, 1.5 * math.pi)
    mc.close_path()
    mc.set_source_rgb(1, 1, 1)
    mc.fill()
    halftone(ctx, gs, m, (*INK, 0.5), spacing=10, angle=0.78, maxr=0.5)
    poly(ctx, torn([(0, 860), (W, 850), (W, H + 40), (0, H + 40)], seed=33, amp=7), SEPIA)


def sc_rockets(ctx, t, u):
    comp(ctx, bg_paper("rk", SEPIA, [([(120, 150), (1800, 130), (1810, 860), (110, 850)], COLD)], seed=17))
    line(ctx, [(150, 800), (1770, 800)], (*INK, 0.5), 4)
    for i in range(3):
        cx = 520 + i * 440
        tb = 0.12 + i * 0.27
        b = ease(seg(u, tb, tb + 0.2))
        lift = 160 * ease(seg(u, tb - 0.1, tb))
        rocket(ctx, cx, 520 - lift, 440, rot=0.05 * (i - 1), broken=b, seed=40 + i)
        smoke(ctx, cx, 420 - lift, b * (1 - 0.5 * seg(u, tb + 0.2, 1.0)), seed=50 + i)
        if b > 0.5:
            # cross-out mark in red pencil
            line(ctx, [(cx - 120, 700), (cx + 120, 760)], (*RED, 0.85), 10)
            line(ctx, [(cx + 120, 700), (cx - 120, 760)], (*RED, 0.85), 10)


def sc_burn(ctx, t, u):
    comp(ctx, bg_paper("burn", SEPIA, [([(120, 150), (1800, 130), (1810, 860), (110, 850)], COLD)], seed=18))
    draw_car(ctx, (1150, 720), 0.0, 300)
    rnd = random.Random(61)
    for i in range(22):
        st = rnd.uniform(0, 0.8)
        v = seg(u, st, st + 0.6)
        if v <= 0:
            continue
        x = 820 - 900 * v + rnd.uniform(-40, 40)
        y = 620 - 260 * v * rnd.uniform(0.5, 1.2) + 40 * math.sin(v * 6 + i)
        bill(ctx, x, y, 0.9 + 0.4 * rnd.random(), rnd.uniform(-1, 1) + v * 3, ash=clamp(v * 1.4 - 0.3))


def sc_split(ctx, t, u):
    comp(ctx, bg_paper("split", SEPIA, [([(120, 150), (1800, 130), (1810, 860), (110, 850)], COLD)], seed=19))
    sep = 140 * ease(seg(u, 0.25, 0.9))
    for side in (-1, 1):
        ctx.save()
        ctx.translate(W / 2 + side * sep, 470)
        ctx.rotate(side * 0.06 * ease(seg(u, 0.25, 0.9)))
        tear = [(0, -320), (14, -220), (-10, -120), (12, 0), (-12, 120), (10, 230), (0, 330)]
        if side < 0:
            shp = [(-300, -330), (0, -320)] + tear[1:-1] + [(0, 330), (-300, 340)]
        else:
            shp = [(300, -330), (0, -320)] + tear[1:-1] + [(0, 330), (300, 340)]
        drop_shadow(ctx, lambda c, col: poly(c, shp, col), off=(8, 10), sigma=6, alpha=0.35)
        poly(ctx, shp, (0.98, 0.97, 0.94))
        inner = [(side * 270, -300), (side * 6, -296)] + [(x * 0.9 + side * 12, y * 0.88) for x, y in tear[1:-1]] + \
                [(side * 6, 220), (side * 270, 230)]
        poly(ctx, inner, hexc("#b9c4cc"))
        ctx.save()
        path(ctx, inner, True, False)
        ctx.clip()
        person(ctx, side * 130, 60, 1.6, hexc("#3a3f4a"), hair=side < 0)
        ctx.restore()
        ctx.restore()


def sc_worst(ctx, t, u):
    comp(ctx, bg_paper("worst", hexc("#d9d6cf"), [([(120, 120), (1800, 110), (1810, 880), (110, 870)], hexc("#a9b4bc"))], seed=20))
    rnd = random.Random(70)
    for i in range(60):  # rain of paper strips
        x = rnd.uniform(120, 1800)
        y = (rnd.uniform(0, 1100) + t * 420) % 900 + 60
        line(ctx, [(x, y), (x - 8, y + 40)], (0.95, 0.96, 0.98, 0.55), 3)
    b_toon(ctx, 0.0, "low", W / 2, 40 + 10 * u, 0.9, rot=0.01)
    poly(ctx, torn([(0, 880), (W, 870), (W, H + 40), (0, H + 40)], seed=33, amp=7), hexc("#d9d6cf"))


def sc_quit(ctx, t, u):
    comp(ctx, bg_paper("quit", SEPIA, [([(120, 150), (1800, 130), (1810, 860), (110, 850)], COLD)], seed=21))
    h = 560 * ease(seg(u, 0.0, 0.6))
    flag(ctx, 900, 860, max(10, h), t * 4, grey=0.2)


def sc_no(ctx, t, u):
    comp(ctx, bg_paper("no", PAPER, [([(140, 120), (1780, 100), (1800, 880), (120, 900)], hexc("#f1c9b8"))], seed=22))
    gone = ease(seg(u, 0.0, 0.25))
    if gone < 1:
        ctx.save()
        ctx.translate(-700 * gone, 300 * gone)
        flag(ctx, 900, 860, 560, t * 4, grey=0.2, crumple=gone)
        ctx.restore()
    slam = back_out(seg(u, 0.12, 0.4), 2.2)
    s = 0.95 * (0.6 + 0.4 * slam)
    if slam > 0:
        b_toon(ctx, 0.0, "resolve", W / 2, 40 + 200 * (1 - slam), s, rot=0.015)
    poly(ctx, torn([(0, 880), (W, 870), (W, H + 40), (0, H + 40)], seed=33, amp=7), PAPER)


SCENES = [
    (0.0, 6.6, lambda c, t, u: sc_stunt(c, t)),
    (6.6, 9.6, sc_inside),
    (9.6, 12.0, sc_mass),
    (12.0, 14.0, sc_crowd),
    (14.0, 16.6, sc_tear),
    (16.6, 18.2, sc_2008),
    (18.2, 20.2, sc_two),
    (20.2, 23.2, sc_odds),
    (23.2, 25.4, sc_rockets),
    (25.4, 27.4, sc_burn),
    (27.4, 29.6, sc_split),
    (29.6, 32.2, sc_worst),
    (32.2, 34.2, sc_quit),
    (34.2, 36.6, sc_no),
]


def frame(t):
    surf, ctx = new()
    for (a, b, fn) in SCENES:
        if a <= t < b or (b == DURATION and t >= a):
            fn(ctx, t, seg(t, a, b))
            break
    caption(ctx, t)
    grain(surf, 5, seed=int(t * 30) % 97)
    return surf


# ------------------------------------------------------------------ storyboard
KEYS = [0.45, 1.7, 3.2, 4.4, 5.0, 5.9, 8.0, 11.0, 13.0, 15.4, 17.4, 19.6, 22.0, 24.6, 26.6, 28.9, 31.0, 33.4, 35.6]


def storyboard(path_out, keys=KEYS, cols=3):
    from PIL import Image
    tw, th = 600, 338
    rows = (len(keys) + cols - 1) // cols
    BW = cols * tw + (cols + 1) * 30
    BH = 170 + rows * (th + 64)
    s, ctx = new(BW, BH)
    ctx.set_source_rgb(*hexc("#101114"))
    ctx.paint()
    text(ctx, "方向 B · 前三十秒分镜（第一、二节，到「他没有。」）", 30, 80, 46, (1, 1, 1), font="Noto Sans CJK SC", anchor="left", spacing=0.03)
    text(ctx, "全长 %.1f 秒 · 每格为成片中的真实一帧 · 时间码在左下" % DURATION, 30, 130, 26, (0.72, 0.74, 0.8),
         font="Noto Sans CJK SC", bold=False, anchor="left", spacing=0.02)
    for i, t in enumerate(keys):
        fr = frame(t)
        x = 30 + (i % cols) * (tw + 30)
        y = 170 + (i // cols) * (th + 64)
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(tw / W, th / H)
        ctx.set_source_surface(fr, 0, 0)
        ctx.paint()
        ctx.restore()
        text(ctx, "%05.2f s" % t, x, y + th + 36, 24, (0.8, 0.82, 0.86), font="Noto Sans Mono CJK SC", bold=False, anchor="left", spacing=0)
    tmp = path_out + ".tmp.png"
    s.write_to_png(tmp)
    Image.open(tmp).convert("RGB").save(path_out, quality=88)
    os.remove(tmp)


if __name__ == "__main__":
    out = os.path.join(F.OUT, "B_storyboard_30s.jpg")
    storyboard(out)
    print(out)
