"""Scenes added in the v6 revision (定稿剧本 v5)."""
import math
import random

import cairo

from gfx import (W, H, TAU, clamp, lerp, prog, smooth, ease_out, ease_in, ease_io, ease_back,
                 pulse, noise1, hexc, mix, shade, setc, rrect, circle, ellipse, fill_rect,
                 lin_grad, vgrad, glow, line, poly, star_shape, stars, skyline, particles, hills,
                 light_rays, spotlight, confetti, paper, papered, fold_poly)
from character import person, silhouette, blend_pose, blend_expr
from scenes_a import (REG, scene, cam, shake, item_t, ground, petals, cherry_tree, window_grid, mini_site,
                      _internet_stream, _paper_wave, rewind)


def _k(S):
    """Index of the current card inside the shot and the time since it started."""
    k = 0
    for i, (a, b) in enumerate(S.items):
        if S.t >= a:
            k = i
    return k, S.t - S.items[k][0], S.items[k][1] - S.items[k][0]


# ======================================================== 1 rewind → young
@scene("rewind_young")
def rewind_young(ctx, S):
    t, T = S.t, S.T
    rewind(ctx, S)
    # the figure flips like a paper card through the years, getting younger each turn
    stages = [("sweater", 0.14, 1.0), ("jacket", 0.06, 0.97), ("shirt", 0.0, 0.94), ("student", 0.0, 0.9)]
    flips = [0.55, 1.2, 1.85]
    idx = sum(1 for f in flips if t >= f)
    sx = 1.0
    for f in flips:
        d = t - f
        if -0.17 < d < 0.17:
            sx = abs(d) / 0.17
    outfit, grey, sc = stages[idx]
    a = 1 - smooth(prog(t, T - 0.5, T - 0.15))
    glow(ctx, 960, 680, 380, "#FFE7B8", 0.25 + 0.25 * (1 - sx))
    ctx.save()
    ctx.translate(960, 0)
    ctx.scale(max(sx, 0.03), 1)
    ctx.translate(-960, 0)
    person(ctx, 960, 895, 0.82 * sc, outfit=outfit, pose="idle", expr="calm" if idx < 3 else "smile", t=t,
           hair_grey=grey, look=(0, -0.2), alpha=a)
    ctx.restore()
    rnd = random.Random(12)
    for i in range(18):
        ph = (t * 0.9 + rnd.random()) % 1.0
        ang = rnd.uniform(0, TAU) - t * 2.2
        r = 120 + ph * 260
        x, y = 960 + math.cos(ang) * r, 660 + math.sin(ang) * r * 0.7
        setc(ctx, rnd.choice(["#F2D7A6", "#FFFFFF", "#E9C46A"]), 0.6 * (1 - ph))
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ang * 2)
        poly(ctx, [(-10, -6), (10, -6), (6, 6), (-6, 6)])
        ctx.fill()
        ctx.restore()


# ======================================================== 2 closed stall
@papered(0.9)
def _stall(ctx, x, y, shut, t):
    """A tiny shopfront/office; the roller shutter comes down by `shut` (0..1)."""
    w, h = 620, 430
    setc(ctx, "#B79C7E")
    ctx.rectangle(x - w / 2 - 40, y - h - 120, w + 80, h + 120)
    ctx.fill()
    setc(ctx, "#9C8268")
    ctx.rectangle(x + w / 2, y - h - 120, 40, h + 120)
    ctx.fill()
    # awning
    for i in range(8):
        setc(ctx, "#C8503A" if i % 2 == 0 else "#F2E6D0")
        poly(ctx, [(x - w / 2 - 40 + i * (w + 80) / 8, y - h - 40), (x - w / 2 - 40 + (i + 1) * (w + 80) / 8, y - h - 40),
                   (x - w / 2 - 40 + (i + 1) * (w + 80) / 8, y - h + 20), (x - w / 2 - 40 + (i + 0.5) * (w + 80) / 8, y - h + 44),
                   (x - w / 2 - 40 + i * (w + 80) / 8, y - h + 20)])
        ctx.fill()
    # empty interior: a bare desk and a dark screen
    setc(ctx, "#3A3044")
    ctx.rectangle(x - w / 2, y - h + 50, w, h - 50)
    ctx.fill()
    setc(ctx, "#5A4A3C")
    ctx.rectangle(x - 200, y - 150, 400, 20)
    ctx.fill()
    ctx.rectangle(x - 180, y - 130, 16, 130)
    ctx.rectangle(x + 164, y - 130, 16, 130)
    ctx.fill()
    setc(ctx, "#2A2430")
    rrect(ctx, x - 70, y - 260, 140, 100, 8)
    ctx.fill()
    # shutter
    sh = (h - 50) * shut
    if sh > 0:
        for i in range(int(sh // 22) + 1):
            yy = y - h + 50 + i * 22
            hh = min(22, y - h + 50 + sh - yy)
            if hh <= 0:
                break
            setc(ctx, "#9AA3B0" if i % 2 == 0 else "#8A93A0")
            ctx.rectangle(x - w / 2, yy, w, hh)
            ctx.fill()
        setc(ctx, "#6E7684")
        ctx.rectangle(x - w / 2, y - h + 50 + sh - 8, w, 8)
        ctx.fill()
    # padlock tag once shut
    lk = ease_back(prog(shut, 0.95, 1.0))
    if shut >= 0.95 and lk > 0.001:
        ctx.save()
        ctx.translate(x, y - 40)
        ctx.scale(lk, lk)
        setc(ctx, "#5B5F6A")
        ctx.set_line_width(7)
        ctx.arc(0, -28, 20, math.pi, TAU)
        ctx.stroke()
        setc(ctx, "#C9A24A")
        rrect(ctx, -28, -28, 56, 46, 6)
        ctx.fill()
        setc(ctx, "#5B4520")
        circle(ctx, 0, -8, 6)
        ctx.fill()
        ctx.restore()


@scene("closed_shop")
def closed_shop(ctx, S):
    t, T = S.t, S.T
    shut = ease_io(prog(t, 0.3, 1.7))
    ctx.save()
    cam(ctx, 1.0 + 0.03 * t / T, 960, 540)
    vgrad(ctx, [(0, "#5E6577"), (0.7, "#8C8C94"), (1, "#A69C92")])
    skyline(ctx, 61, 700, "#6E7486", None, hmin=120, hmax=300, wmin=100, wmax=220)
    ground(ctx, 820, "#5C5560", "#433C48")
    setc(ctx, "#6C6470")
    ctx.rectangle(0, 820, W, 14)
    ctx.fill()
    _stall(ctx, 1220, 822, shut, t)
    # boxes left out front
    for i, (bx, by, bw, bh) in enumerate(((820, 822, 120, 90), (870, 732, 90, 70), (1610, 822, 110, 80))):
        fold_poly(ctx, [(bx - bw / 2, by), (bx - bw / 2, by - bh), (bx + bw / 2, by - bh), (bx + bw / 2, by)],
                  "#B98A5A", (1, 3), k_dark=-0.15, k_light=0.05)
        line(ctx, bx, by - bh, bx, by, "#E4C79A", 5, 0.8)
    sad = smooth(prog(t, 1.4, 2.4))
    person(ctx, 430, 900, 0.86, outfit="student", pose=blend_pose("idle", "sad", sad),
           expr=blend_expr("worried", "sad", sad), t=t, look=(0.8, -0.2), tilt=0.05 * sad)
    person(ctx, 650, 900, 0.9, outfit="senior", pose=blend_pose("idle", "shrug", pulse(t, 1.6, 3.4)),
           expr="sad", t=t, hair_style="flat", glasses=True, look=(0.7, -0.1), seed=3)
    # wind-blown paper scraps
    rnd = random.Random(8)
    for _ in range(10):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(500, 880)
        x = (x0 - t * 160) % (W + 200) - 100
        y = y0 + math.sin(t * 2 + x0) * 20
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(t * 2 + x0)
        setc(ctx, "#E8E2D6", 0.8)
        poly(ctx, [(-14, -10), (14, -8), (10, 10), (-12, 8)])
        ctx.fill()
        ctx.restore()
    ctx.restore()
    fill_rect(ctx, "#1A1424", alpha=0.25 * sad)


# ======================================================== 2 alone: 光聪明，不够
@scene("alone_sit")
def alone_sit(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#0E1222"), (1, "#1B1E30")])
    spotlight(ctx, 960, -40, 960, 900, 30, 260, "#E6ECFF", 0.18)
    setc(ctx, "#232740")
    ellipse(ctx, 960, 905, 360, 34)
    ctx.fill()
    # a lone stool
    setc(ctx, "#4A3B34")
    rrect(ctx, 905, 812, 110, 16, 5)
    ctx.fill()
    line(ctx, 918, 828, 908, 902, "#3A2E28", 7)
    line(ctx, 1002, 828, 1012, 902, "#3A2E28", 7)
    person(ctx, 960, 905, 0.62, outfit="student", pose="hold", expr="tired", t=t, sit=True,
           look=(0, 0.7), tilt=0.04)
    particles(ctx, 14, 30, t, "#C9D6FF", 0.25, area=(700, 120, 520, 760), vy=-10, vx=2)


# ======================================================== 3 back to Kingsoft
def kingsoft_facade(ctx, op, t):
    """Kingsoft office tower (same design as the 1992 shot); returns the door centre x."""
    vgrad(ctx, [(0, "#86B4C4"), (0.7, "#D9E0D0"), (1, "#EBD7AE")])
    glow(ctx, 380, 180, 300, "#FFF6DA", 0.7)
    skyline(ctx, 40, 780, "#A9BDC3", None, hmin=80, hmax=260, wmin=90, wmax=200)
    bx, bw, btop = 720, 480, 150
    setc(ctx, "#E2D3B6")
    ctx.rectangle(bx, btop, bw, 650)
    ctx.fill()
    setc(ctx, "#C9B795")
    ctx.rectangle(bx + bw, btop + 20, 60, 630)
    ctx.fill()
    window_grid(ctx, bx + 30, btop + 40, 7, 10, 42, 34, 22, 20, "#4F7FA3",
                lambda r, q: 0.9 if (r * 7 + q) % 5 else 0.6)
    setc(ctx, "#B9A47E")
    ctx.rectangle(bx - 20, btop - 24, bw + 100, 28)
    ctx.fill()
    dx = bx + bw / 2
    setc(ctx, "#5D4A36")
    ctx.rectangle(dx - 110, 620, 220, 190)
    ctx.fill()
    glow(ctx, dx, 720, 300 * (0.3 + op), "#FFE2A0", 0.6 * op)
    setc(ctx, mix("#8FB3C9", "#FFF0C8", op))
    ctx.rectangle(dx - 96, 636, 192, 174)
    ctx.fill()
    setc(ctx, "#6E8FA6")
    ctx.rectangle(dx - 96, 636, 96 * (1 - op), 174)
    ctx.rectangle(dx + 96 * op, 636, 96 * (1 - op), 174)
    ctx.fill()
    ground(ctx, 800, "#B9AE98", "#8E8470")
    setc(ctx, "#A39A84")
    ctx.rectangle(0, 800, W, 18)
    ctx.fill()
    for tx in (220, 1500, 1780):
        setc(ctx, "#5E4636")
        ctx.rectangle(tx - 8, 640, 16, 170)
        ctx.fill()
        setc(ctx, "#5E9466")
        circle(ctx, tx, 610, 80)
        ctx.fill()
        setc(ctx, "#4E8456")
        circle(ctx, tx + 40, 640, 56)
        ctx.fill()
    return dx


@papered(0.9)
def wall_calendar(ctx, x, y, s, flip, t):
    """Tear-off calendar without numerals: coloured month band + day grid. `flip` counts pages."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    cols = ["#E76F51", "#2A9D8F", "#E9C46A", "#457B9D", "#F4A261", "#8AB17D", "#EF476F", "#6C8EBF"]
    n = int(flip)
    f = flip - n

    def page(c, k):
        setc(ctx, "#FFFDF6")
        rrect(ctx, -170, -200, 340, 400, 10)
        ctx.fill()
        setc(ctx, c)
        rrect(ctx, -170, -200, 340, 96, 10)
        ctx.rectangle(-170, -140, 340, 36)
        ctx.fill()
        for r in range(5):
            for q in range(7):
                setc(ctx, "#C9CED6" if (r * 7 + q + k) % 9 else c)
                rrect(ctx, -146 + q * 42, -84 + r * 54, 30, 30, 6)
                ctx.fill()
    setc(ctx, "#5A4A3C")
    ctx.rectangle(-180, -214, 360, 22)
    ctx.fill()
    page(cols[(n + 1) % len(cols)], n + 1)
    # the current page lifts and flies up
    ctx.save()
    ctx.translate(0, -200)
    ctx.scale(1, max(0.02, math.cos(f * math.pi * 0.5)))
    ctx.translate(f * 40, -f * 60)
    ctx.rotate(-f * 0.3)
    ctx.translate(0, 200)
    page(cols[n % len(cols)], n)
    ctx.restore()
    for i in range(3):
        circle(ctx, -100 + i * 100, -204, 9)
        setc(ctx, "#2A2430")
        ctx.fill()
    ctx.restore()


@scene("return_kingsoft")
def return_kingsoft(ctx, S):
    t, T = S.t, S.T
    k, tk, dk = _k(S)
    split = T * 0.5
    b = smooth(prog(t, split - 0.25, split + 0.25))
    if b < 1:
        ctx.save()
        cam(ctx, 1.0 + 0.12 * ease_io(prog(t, 0, split)), lerp(960, 960, t / T), 600)
        op = smooth(prog(t, 1.2, 1.8))
        dx = kingsoft_facade(ctx, op, t)
        wp = prog(t, 0.1, 2.3)
        x = lerp(1620, dx, ease_io(wp))
        s = lerp(0.9, 0.62, ease_io(wp))
        y = lerp(960, 812, ease_io(wp))
        a = 1 - smooth(prog(t, 2.25, 2.6))
        if a > 0.01:
            pose = blend_pose("idle", "push", smooth(prog(t, 1.1, 1.5)))
            person(ctx, x, y, s, outfit="jacket", pose=pose, expr="determined", t=t,
                   walk=(t * 8 if wp < 1 else None), facing="back", alpha=a)
        ctx.restore()
        if b > 0:
            fill_rect(ctx, "#FFF6E6", alpha=b)
    if b > 0:
        ctx.push_group()
        u = prog(t, split, T)
        vgrad(ctx, [(0, "#E9DCC4"), (1, "#CDBA98")])
        setc(ctx, "#BFAA86")
        ctx.rectangle(0, 760, W, 400)
        ctx.fill()
        window_grid(ctx, 1240, 150, 2, 2, 230, 160, 18, 18, "#9CC3D9", lambda r, q: 0.85)
        flip = ease_in(u, 1.3) * 22
        wall_calendar(ctx, 640, 420, 1.05, flip, t)
        # pages already torn off, drifting down
        rnd = random.Random(5)
        for i in range(int(flip)):
            ph = clamp((flip - i) / 4)
            if ph >= 1:
                continue
            px = 640 + rnd.uniform(-80, 260) + ph * 300
            py = 300 - ph * 120 + ph * ph * 700
            ctx.save()
            ctx.translate(px, py)
            ctx.rotate(ph * 3 + i)
            ctx.scale(0.35, 0.35 * abs(math.cos(ph * 5)) + 0.05)
            setc(ctx, "#FFFDF6", 1 - ph)
            rrect(ctx, -170, -200, 340, 400, 10)
            ctx.fill()
            ctx.restore()
        setc(ctx, "#6E4A35")
        rrect(ctx, 1080, 700, 700, 26, 6)
        ctx.fill()
        ctx.rectangle(1110, 726, 640, 180)
        ctx.fill()
        person(ctx, 1560, 905, 0.8, outfit="jacket", pose="type", expr=blend_expr("determined", "tired", u),
               t=t, sit=True, hair_grey=lerp(0.0, 0.12, u), look=(-0.6, 0.3))
        setc(ctx, "#2A2D3A")
        rrect(ctx, 1150, 550, 250, 150, 10)
        ctx.fill()
        setc(ctx, "#4F7FA3")
        rrect(ctx, 1162, 562, 226, 120, 6)
        ctx.fill()
        setc(ctx, "#2A2D3A")
        ctx.rectangle(1262, 700, 26, 10)
        ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(b)


# ======================================================== 4 window: the internet passes by
@scene("window_wave")
def window_wave(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#2C2A40"), (1, "#1E1C2E")])
    wx, wy, ww, wh = 260, 130, 1400, 520
    setc(ctx, "#0B1430")
    ctx.rectangle(wx, wy, ww, wh)
    ctx.fill()
    ctx.save()
    ctx.rectangle(wx, wy, ww, wh)
    ctx.clip()
    vgrad(ctx, [(0, "#0A1230"), (1, "#1C2A5A")], wx, wy, ww, wh)
    stars(ctx, 33, 50, t, 0.7, y_max=wy + 300)
    skyline(ctx, 18, wy + wh, "#121A3A", "#F6B64A", lit=0.25, t=t, win_alpha=0.5, hmin=60, hmax=220,
            wmin=80, wmax=160, x0=wx - 20, x1=wx + ww + 20)
    ctx.translate(0, -120)
    _internet_stream(ctx, t, 0.95, t * 600)
    ctx.translate(0, 120)
    wp = prog(t, 0.6, T - 0.4)
    _paper_wave(ctx, lerp(wx - 200, wx + ww + 2400, wp), 2200, wy + wh + 10, t)
    ctx.restore()
    setc(ctx, "#3E3A56")
    ctx.set_line_width(22)
    ctx.rectangle(wx, wy, ww, wh)
    ctx.stroke()
    line(ctx, wx + ww / 2, wy, wx + ww / 2, wy + wh, "#3E3A56", 14)
    setc(ctx, "#4A4462")
    ctx.rectangle(wx - 40, wy + wh + 8, ww + 80, 26)
    ctx.fill()
    glance = pulse(t, 1.4, 3.6)
    person(ctx, 820, 880, 0.86, outfit="jacket", pose="type", expr=blend_expr("determined", "worried", glance),
           t=t, sit=True, look=(lerp(0.8, -0.3, glance), lerp(0.3, -0.8, glance)), hair_grey=0.04)
    # office desk with the WPS document he keeps working on
    setc(ctx, "#5A3D2E")
    rrect(ctx, 520, 720, 900, 28, 8)
    ctx.fill()
    setc(ctx, "#43302A")
    ctx.rectangle(550, 748, 840, 200)
    ctx.fill()
    setc(ctx, "#2A2D3A")
    rrect(ctx, 1020, 540, 300, 180, 12)
    ctx.fill()
    setc(ctx, "#F5F7FB")
    rrect(ctx, 1036, 556, 268, 148, 6)
    ctx.fill()
    setc(ctx, "#2E6BE6")
    rrect(ctx, 1056, 572, 100, 14, 5)
    ctx.fill()
    for i in range(5):
        setc(ctx, "#B9C3D6")
        rrect(ctx, 1056, 600 + i * 18, 220 - (i % 2) * 60, 8, 4)
        ctx.fill()


# ======================================================== 5 Joyo: built, refused, sold
@scene("joyo_story")
def joyo_story(ctx, S):
    t, T = S.t, S.T
    k, tk, dk = _k(S)
    t1 = S.items[1][0] if len(S.items) > 1 else 1e9
    t2 = S.items[2][0] if len(S.items) > 2 else 1e9
    dusk = smooth(prog(t, t2 - 0.5, t2 + 1.5))
    gloom = smooth(prog(t, t1 - 0.3, t1 + 0.6)) * (1 - dusk)
    top = mix(mix("#FFE9C9", "#3B3F5C", gloom), "#3B2C5E", dusk)
    mid = mix(mix("#FBD9A8", "#2C3048", gloom), "#B0627A", dusk)
    bot = mix(mix("#F6C58E", "#22263A", gloom), "#F4A66A", dusk)
    vgrad(ctx, [(0, top), (0.6, mid), (1, bot)])
    if dusk > 0:
        glow(ctx, 1500, 760, 420, "#FFC27A", 0.7 * dusk)
        setc(ctx, "#FFD7A0", dusk)
        circle(ctx, 1500, 780, 90)
        ctx.fill()
    hills(ctx, 840, 50, 0.003, 2.0, mix(mix("#E1B07A", "#2E3048", gloom), "#4A2E50", dusk))
    ground(ctx, 870, mix(mix("#E8C49A", "#1C1F30", gloom), "#3A2340", dusk),
           mix(mix("#D9AE7E", "#141726", gloom), "#24152A", dusk))
    # the store (browser card) on its paper easel
    pop = ease_back(prog(t, 0.1, 0.7))
    rel = ease_in(prog(t, t2 + 1.2, T + 0.6), 1.6)
    sx_ = 760 + lerp(0, -500, rel) + math.sin(t * 1.4) * 14 * (rel > 0)
    sy_ = 470 - rel * 900
    if rel <= 0:
        setc(ctx, "#6B4A36")
        line(ctx, 760, 600, 700, 872, "#6B4A36", 10)
        line(ctx, 760, 600, 820, 872, "#6B4A36", 10)
    if rel > 0 or t > t2:
        ba = smooth(prog(t, t2 + 0.2, t2 + 0.8))
        for j, (ox, c) in enumerate(((-120, "#EF476F"), (0, "#FFD166"), (120, "#06D6A0"))):
            if ba <= 0.001:
                break
            ex, ey = sx_ + ox * 1.3, sy_ - 330 - abs(ox) * 0.3 + (1 - ba) * 120
            line(ctx, sx_ + ox * 0.4, sy_ - 150, ex, ey + 70, "#FFFFFF", 2, 0.8 * ba)
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(ba, ba)
            setc(ctx, c)
            ellipse(ctx, 0, 0, 62, 76)
            ctx.fill()
            setc(ctx, "#FFFFFF", 0.35)
            ellipse(ctx, -18, -26, 14, 20)
            ctx.fill()
            ctx.restore()
    if pop > 0:
        mini_site(ctx, sx_, sy_, 2.6 * pop, math.sin(t * 1.2) * 0.05 * (rel > 0))
    # parcels while the business runs
    if t < t1:
        rnd = random.Random(4)
        for i in range(6):
            ph = (t * 0.6 + i / 6) % 1.0
            if t < 1.0:
                break
            x = lerp(1000, W + 120, ph)
            y = lerp(420 + rnd.uniform(-60, 120), 300 + rnd.uniform(-60, 80), ph) - math.sin(ph * math.pi) * 120
            ctx.save()
            ctx.translate(x, y)
            ctx.rotate(ph * 2)
            setc(ctx, "#C98B52")
            rrect(ctx, -30, -24, 60, 48, 5)
            ctx.fill()
            setc(ctx, "#E9C46A")
            ctx.rectangle(-4, -24, 8, 48)
            ctx.fill()
            ctx.restore()
    # thirty investors' doors: each opens, then a red cross
    da = smooth(prog(t, t1 - 0.2, t1 + 0.3)) * (1 - smooth(prog(t, t2 - 0.3, t2 + 0.3)))
    if da > 0:
        cols, rows = 6, 5
        dw, dh, gx, gy = 92, 108, 26, 16
        x0, y0 = 1130, 90
        for i in range(cols * rows):
            r, q = i // cols, i % cols
            x, y = x0 + q * (dw + gx), y0 + r * (dh + gy)
            ti = lerp(t1 + 0.2, t2 - 0.6, (i / 30) ** 0.85)
            p = (t - ti) / 0.2
            setc(ctx, "#3A4362", da)
            rrect(ctx, x - 6, y - 6, dw + 12, dh + 10, 5)
            ctx.fill()
            if p < 0:
                setc(ctx, "#6A5242", da)
                rrect(ctx, x, y, dw, dh, 4)
                ctx.fill()
                setc(ctx, "#E9C46A", da)
                circle(ctx, x + dw - 15, y + dh / 2, 5)
                ctx.fill()
            else:
                open_ = pulse(p, 0, 1.0)
                if open_ > 0:
                    setc(ctx, "#FFE8B8", open_ * da)
                    ctx.rectangle(x, y, dw, dh)
                    ctx.fill()
                setc(ctx, mix("#6A5242", "#3E3330", clamp(p - 0.8)), da)
                ctx.rectangle(x, y, dw * (1 - 0.7 * open_), dh)
                ctx.fill()
                if p > 0.9:
                    xa = ease_back(clamp((p - 0.9) * 3))
                    setc(ctx, "#E2504C", 0.9 * da)
                    ctx.set_line_width(8)
                    cx, cy = x + dw / 2, y + dh / 2
                    d = 28 * xa
                    ctx.move_to(cx - d, cy - d)
                    ctx.line_to(cx + d, cy + d)
                    ctx.move_to(cx + d, cy - d)
                    ctx.line_to(cx - d, cy + d)
                    ctx.stroke()
    # him
    if t < t1:
        pose = blend_pose("idle", "point", ease_out(prog(t, 0.4, 0.9)))
        expr, look = "happy", (-0.8, -0.3)
    elif t < t2:
        pr = prog(t, t1, t2)
        pose = blend_pose("hold", "sad", smooth(prog(pr, 0.5, 1.0)))
        expr = blend_expr("determined", "sad", smooth(prog(pr, 0.3, 0.95)))
        look = (0.9, lerp(-0.4, 0.3, pr))
    else:
        release = t2 + 1.2
        pose = "reach" if t < release else blend_pose("reach", "reach2", ease_out(prog(t, release, release + 0.5)))
        if t > release + 1.8:
            pose = blend_pose("reach2", "sad", smooth(prog(t, release + 1.8, release + 2.6)))
        expr = "calm" if t < release else ("shock" if t < release + 0.6 else "sad")
        look = (-0.6, -1.0)
    person(ctx, 1080 if t < t2 else 1000, 905, 0.86, outfit="jacket", pose=pose, expr=expr, t=t, look=look,
           hair_grey=0.06)
    if t > t2:
        for i in range(3):
            bxp = (t * 120 + i * 300) % (W + 200) - 100
            byp = 300 + i * 40 + math.sin(t * 2 + i) * 10
            setc(ctx, "#2A1A30", dusk)
            ctx.set_line_width(4)
            w_ = math.sin(t * 9 + i) * 8
            ctx.move_to(bxp - 18, byp - w_)
            ctx.line_to(bxp, byp)
            ctx.line_to(bxp + 18, byp - w_)
            ctx.stroke()
    if gloom > 0:
        fill_rect(ctx, "#000000", alpha=0.15 * gloom)


# ======================================================== 6 night: why so hard and still missed it
@scene("night_ponder")
def night_ponder(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#0A0D1C"), (1, "#141729")])
    # large window over the night city with rain on the glass
    wx, wy, ww, wh = 360, 110, 1200, 640
    ctx.save()
    rrect(ctx, wx, wy, ww, wh, 10)
    ctx.clip()
    vgrad(ctx, [(0, "#0B1028"), (1, "#1D2346")], wx, wy, ww, wh)
    stars(ctx, 71, 40, t, 0.6, y_max=wy + 260)
    setc(ctx, "#E9EEFF")
    circle(ctx, 1380, 240, 44)
    ctx.fill()
    glow(ctx, 1380, 240, 160, "#C9D6FF", 0.35)
    skyline(ctx, 72, wy + wh, "#151B38", "#F6B64A", lit=0.08, t=t, win_alpha=0.45, hmin=100, hmax=330,
            wmin=80, wmax=170, x0=wx - 20, x1=wx + ww + 20)
    rnd = random.Random(6)
    for _ in range(70):
        x0, y0 = rnd.uniform(wx, wx + ww), rnd.uniform(0, wh)
        y = wy + (y0 + t * 260 * rnd.uniform(0.6, 1.2)) % wh
        line(ctx, x0, y, x0 - 2, y + 18, "#AFC4F0", 2, 0.35)
    ctx.restore()
    setc(ctx, "#2B2A44")
    ctx.set_line_width(18)
    rrect(ctx, wx, wy, ww, wh, 10)
    ctx.stroke()
    line(ctx, wx + ww / 2, wy, wx + ww / 2, wy + wh, "#2B2A44", 12)
    line(ctx, wx, wy + wh / 2, wx + ww, wy + wh / 2, "#2B2A44", 8)
    # wall clock without numerals, hands crawling past midnight
    cx, cy = 1760, 230
    setc(ctx, "#E8E2D2")
    circle(ctx, cx, cy, 70)
    ctx.fill()
    setc(ctx, "#3A3448")
    ctx.set_line_width(6)
    circle(ctx, cx, cy, 70)
    ctx.stroke()
    for i in range(12):
        a = i / 12 * TAU
        line(ctx, cx + math.cos(a) * 56, cy + math.sin(a) * 56, cx + math.cos(a) * 64, cy + math.sin(a) * 64,
             "#3A3448", 3)
    am = -math.pi / 2 + t * 0.9
    line(ctx, cx, cy, cx + math.cos(am) * 52, cy + math.sin(am) * 52, "#2A2433", 4)
    ah = -math.pi / 2 + 0.2 + t * 0.08
    line(ctx, cx, cy, cx + math.cos(ah) * 34, cy + math.sin(ah) * 34, "#2A2433", 6)
    setc(ctx, "#4A4462")
    ctx.rectangle(wx - 40, wy + wh + 6, ww + 80, 26)
    ctx.fill()
    # desk lamp pool
    spotlight(ctx, 470, 560, 520, 900, 18, 220, "#FFD99A", 0.18)
    setc(ctx, "#3C3A52")
    line(ctx, 430, 900, 450, 600, "#3C3A52", 8)
    poly(ctx, [(420, 600), (530, 560), (540, 590), (440, 630)])
    ctx.fill()
    info = person(ctx, 960, 905, 0.92, outfit="jacket", pose="think", expr="worried", t=t, facing="front",
                  look=(0.3, -0.6), tilt=0.05, hair_grey=0.08)
    hx, hy = ctx.device_to_user(*info["head"])
    # tangled thought scribble that keeps knotting
    rnd = random.Random(17)
    grow = ease_out(prog(t, 0.4, T - 0.6))
    n = int(80 * grow) + 2
    ctx.set_line_width(3)
    setc(ctx, "#9FB4FF", 0.6)
    bx, by = hx + 40, hy - 250
    ctx.move_to(bx, by)
    for i in range(n):
        a = i * 0.9 + t * 0.6
        r = 40 + 70 * abs(math.sin(i * 0.37 + rnd.random()))
        ctx.line_to(bx + math.cos(a) * r * 1.5, by + math.sin(a) * r * 0.8)
    ctx.stroke()
    q = ease_back(prog(t, 1.2, 1.7))
    if q > 0:
        ctx.save()
        ctx.translate(bx + 190, by - 90)
        ctx.scale(q, q)
        setc(ctx, "#C9D6FF", 0.9)
        ctx.set_line_width(12)
        ctx.arc(0, -18, 26, math.pi * 1.05, math.pi * 2.4)
        ctx.line_to(0, 26)
        ctx.stroke()
        circle(ctx, 0, 54, 8)
        ctx.fill()
        ctx.restore()


# ======================================================== 6 顺势而为 (big text)
@scene("shunshi")
def shunshi(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#F7B65A"), (0.55, "#FFE0A6"), (1, "#FFF0CF")])
    glow(ctx, 1600, 220, 600, "#FFF4D0", 0.8)
    light_rays(ctx, 1600, 220, 14, 1500, "#FFF4D0", 0.12, t, rot=t * 0.1)
    hills(ctx, 640, 60, 0.0025, 1.4, "#E3A46C")
    hills(ctx, 690, 40, 0.004, 0.2, "#C98A5A")
    ctx.set_source(lin_grad(0, 690, 0, H, [(0, "#4FA3C8"), (1, "#22607E")]))
    ctx.rectangle(0, 690, W, H)
    ctx.fill()
    rnd = random.Random(9)
    for i in range(46):
        y = rnd.uniform(700, 1070)
        x0 = rnd.uniform(0, W + 300)
        ln = rnd.uniform(80, 220)
        x = (x0 + t * 700 * (0.6 + (y - 690) / 800)) % (W + 300) - 150
        line(ctx, x, y, x + ln, y, "#D6EEFF", 3, 0.45)
    # wind
    for i in range(9):
        ph = (t * 0.9 + i / 9) % 1.0
        y = 470 + i * 26
        x = lerp(-300, W + 300, ph)
        setc(ctx, "#FFFFFF", 0.55 * math.sin(ph * math.pi))
        ctx.set_line_width(4)
        ctx.move_to(x, y)
        ctx.curve_to(x + 120, y - 30, x + 240, y + 30, x + 380, y)
        ctx.stroke()
    # origami paper boat riding the current under full sail
    bx = lerp(520, 1350, ease_io(prog(t, 0, T))) + math.sin(t * 2) * 6
    by = 800 + math.sin(t * 2.4) * 8
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(math.sin(t * 2.4) * 0.03)

    def boat():
        fold_poly(ctx, [(-230, -20), (230, -20), (150, 70), (-150, 70)], "#FFFDF6", (0, 2), k_dark=-0.12, k_light=0.0)
        fold_poly(ctx, [(0, -20), (0, -300), (190, -40)], "#FFFDF6", (0, 1), k_dark=-0.18, k_light=0.03)
        fold_poly(ctx, [(-10, -20), (-10, -250), (-160, -40)], "#F6B64A", (0, 1), k_dark=-0.14, k_light=0.05)
    paper(ctx, boat, 1.2, 0.35)
    ctx.restore()
    person(ctx, bx - 70, by - 4, 0.42, outfit="jacket", pose="open", expr="happy", t=t, sit=True,
           look=(0.7, -0.4), hair_grey=0.05)
    for i in range(12):
        ph = (t * 2 + i / 12) % 1.0
        setc(ctx, "#FFFFFF", 0.6 * (1 - ph))
        circle(ctx, bx - 250 - ph * 220, by + 50 - math.sin(ph * math.pi) * 40, 6 * (1 - ph) + 2)
        ctx.fill()


# ======================================================== 6 leave (2007): he walks out alone
@scene("leave")
def leave(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#3B2C5E"), (0.55, "#B86A6A"), (1, "#F0A868")])
    glow(ctx, 300, 760, 420, "#FFC27A", 0.6)
    setc(ctx, "#FFD7A0")
    circle(ctx, 300, 790, 80)
    ctx.fill()
    skyline(ctx, 44, 800, "#5A3F5E", None, hmin=80, hmax=240, wmin=90, wmax=200)
    # the office tower, door lit from inside
    bx, bw, btop = 1100, 560, 110
    setc(ctx, "#7C6A78")
    ctx.rectangle(bx, btop, bw, 700)
    ctx.fill()
    setc(ctx, "#5E4E5E")
    ctx.rectangle(bx + bw, btop + 20, 70, 680)
    ctx.fill()
    window_grid(ctx, bx + 34, btop + 40, 8, 10, 40, 34, 24, 20, "#FFD58A",
                lambda r, q: 0.85 if (r * 8 + q) % 3 else 0.25)
    setc(ctx, "#6A5868")
    ctx.rectangle(bx - 20, btop - 24, bw + 110, 28)
    ctx.fill()
    dx = bx + bw / 2
    setc(ctx, "#3E3040")
    ctx.rectangle(dx - 120, 620, 240, 190)
    ctx.fill()
    glow(ctx, dx, 720, 300, "#FFE2A0", 0.5)
    setc(ctx, "#FFF0C8")
    ctx.rectangle(dx - 104, 636, 208, 174)
    ctx.fill()
    # a quiet red ribbon over the entrance for the listing day
    setc(ctx, "#B8322E")
    ctx.move_to(dx - 170, 600)
    ctx.curve_to(dx - 80, 650, dx + 80, 650, dx + 170, 600)
    ctx.line_to(dx + 170, 616)
    ctx.curve_to(dx + 80, 666, dx - 80, 666, dx - 170, 616)
    ctx.close_path()
    ctx.fill()
    setc(ctx, "#D9483E")
    circle(ctx, dx, 650, 22)
    ctx.fill()
    ground(ctx, 810, "#6A4A58", "#3A2838")
    setc(ctx, "#7A5868")
    ctx.rectangle(0, 810, W, 14)
    ctx.fill()
    wp = prog(t, 0.3, T + 0.4)
    e = ease_in(wp, 1.3)
    x = lerp(dx, 360, e)
    y = lerp(812, 930, e)
    s = lerp(0.6, 0.92, e)
    a = smooth(prog(t, 0.2, 0.6))
    # long evening shadow stretching back toward the building
    ctx.save()
    ctx.translate(x, y)
    ctx.transform(cairo.Matrix(1, 0, -1.6, 0.18, 0, 0))
    ctx.translate(-x, -y)
    setc(ctx, "#1E1424", 0.35 * a)
    ellipse(ctx, x + 0, y - 260 * s, 46 * s, 260 * s)
    ctx.fill()
    ctx.restore()
    person(ctx, x, y, s, outfit="jacket", pose="pocket", expr="calm", t=t, walk=t * 7, facing="front",
           hair_grey=0.12, look=(-0.6, 0.1), alpha=a)
    rnd = random.Random(2)
    for _ in range(10):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        yy = (y0 + t * 70) % (H + 100) - 50
        ctx.save()
        ctx.translate(x0 + math.sin(t + x0) * 30, yy)
        ctx.rotate(t + x0)
        setc(ctx, rnd.choice(["#E9A23B", "#C8642E"]), 0.7)
        ellipse(ctx, 0, 0, 12, 6)
        ctx.fill()
        ctx.restore()


# ======================================================== 7 listing day: the gong
@papered(1.0)
def _gong(ctx, x, y, r, swing, shine):
    ctx.save()
    ctx.translate(x, y)
    setc(ctx, "#6B4A36")
    ctx.rectangle(-r - 70, -r - 120, 30, 2 * r + 260)
    ctx.rectangle(r + 40, -r - 120, 30, 2 * r + 260)
    ctx.rectangle(-r - 100, -r - 140, 2 * r + 200, 34)
    ctx.fill()
    setc(ctx, "#B8322E")
    ctx.rectangle(-r - 110, -r - 150, 2 * r + 220, 14)
    ctx.fill()
    line(ctx, -r * 0.5, -r - 106, -r * 0.3, -r * 0.9, "#3A2A20", 4)
    line(ctx, r * 0.5, -r - 106, r * 0.3, -r * 0.9, "#3A2A20", 4)
    ctx.rotate(swing)
    n = 16
    for i in range(n):
        a0, a1 = i / n * TAU, (i + 1) / n * TAU
        c = shade("#D9A441", 0.12 if (i % 2 == 0) else -0.08)
        setc(ctx, mix(c, "#FFF2C2", shine * 0.5))
        poly(ctx, [(0, 0), (math.cos(a0) * r, math.sin(a0) * r), (math.cos(a1) * r, math.sin(a1) * r)])
        ctx.fill()
    setc(ctx, "#A87A2A")
    ctx.set_line_width(6)
    circle(ctx, 0, 0, r * 0.62)
    ctx.stroke()
    setc(ctx, mix("#E9C46A", "#FFF6D8", shine))
    circle(ctx, 0, 0, r * 0.28)
    ctx.fill()
    ctx.restore()


@scene("ipo_gong")
def ipo_gong(ctx, S):
    t, T = S.t, S.T
    hit = 0.85
    ht = t - hit
    shine = pulse(ht, 0, 1.2) if ht > 0 else 0.0
    ctx.save()
    sx, sy = shake(t, 6 * pulse(ht, 0, 0.35) if ht > 0 else 0, 2)
    cam(ctx, 1.0 + 0.05 * t / T, 960, 520, sx, sy)
    vgrad(ctx, [(0, "#3A1420"), (1, "#1E0A12")])
    for i in range(5):
        spotlight(ctx, 300 + i * 330, -40, 300 + i * 330 + math.sin(t + i) * 80, 880, 30, 170, "#FFE6B0", 0.07)
    spotlight(ctx, 1080, -60, 1080, 860, 60, 360, "#FFE6B0", 0.2)
    # stage
    setc(ctx, "#5A1E28")
    ctx.rectangle(0, 820, W, 300)
    ctx.fill()
    setc(ctx, "#7A2A34")
    ctx.rectangle(0, 820, W, 16)
    ctx.fill()
    gx, gy, gr = 1180, 450, 210
    if ht > 0:
        for i in range(4):
            rp = ((ht * 0.9 + i * 0.25) % 1.0) if ht < 3.5 else 1.0
            setc(ctx, "#FFE6A0", 0.45 * (1 - rp))
            ctx.set_line_width(6)
            circle(ctx, gx, gy, gr + rp * 600)
            ctx.stroke()
        glow(ctx, gx, gy, 520, "#FFD27A", 0.5 * shine + 0.15)
        light_rays(ctx, gx, gy, 16, 900, "#FFE7A8", 0.1 + 0.12 * shine, t, rot=t * 0.15)
    _gong(ctx, gx, gy, gr, 0.06 * math.sin(ht * 9) * math.exp(-ht * 1.2) if ht > 0 else 0.0, shine)
    # he swings the mallet
    sw = ease_in(prog(t, 0.2, hit), 2) - ease_out(prog(t, hit, hit + 0.6)) * 0.4
    info = person(ctx, 720, 905, 0.92, outfit="sweater", pose=blend_pose("idle", "point", clamp(0.3 + sw)),
                  expr="determined" if t < hit else "grin", t=t, hair_grey=0.2, look=(0.9, -0.4))
    hx, hy = ctx.device_to_user(*info["handR"])
    ang = lerp(-1.4, 0.15, clamp(sw))
    mx, my = hx + math.cos(ang) * 230, hy + math.sin(ang) * 230
    line(ctx, hx, hy, mx, my, "#6B4A36", 12)
    setc(ctx, "#B8322E")
    ellipse(ctx, mx, my, 34, 30)
    ctx.fill()
    ctx.restore()
    for i in range(10):
        x = 60 + i * 200 + (i % 2) * 40
        silhouette(ctx, x, 1080 - (i % 2) * 24, 1.15 + (i % 3) * 0.1, "#12060A", seed=i + 20, t=t, nod=0.05)
    if ht > 0:
        confetti(ctx, 7, 90, t, hit + 0.1, ["#F6B64A", "#EF476F", "#FFFFFF", "#FFD27A"], fall=200)


@scene("black")
def black(ctx, S):
    fill_rect(ctx, "#000000")
