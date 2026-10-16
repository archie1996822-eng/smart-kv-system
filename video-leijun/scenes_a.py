"""Scenes for segments 1–6 (hook → 再输一次)."""
import math
import random

import cairo

from gfx import (W, H, TAU, PAL, clamp, lerp, prog, smooth, ease_out, ease_in, ease_io, ease_back,
                 spring, pulse, noise1, hexc, mix, shade, setc, rrect, circle, ellipse, fill_rect,
                 lin_grad, vgrad, glow, line, poly, star_shape, stars, skyline, particles, hills,
                 light_rays, spotlight, confetti, font, text_width, SANS,
                 drop_shadow, paper, papered, fold_poly, facet_mountain)
from character import person, silhouette, blend_pose, blend_expr

REG = {}


def scene(name):
    def deco(f):
        REG[name] = f
        return f
    return deco


def cam(ctx, zoom=1.0, cx=W / 2, cy=H / 2, dx=0.0, dy=0.0, rot=0.0):
    ctx.translate(W / 2 + dx, H / 2 + dy)
    ctx.rotate(rot)
    ctx.scale(zoom, zoom)
    ctx.translate(-cx, -cy)


def shake(t, amp, seed=0):
    return noise1(t * 22, seed) * amp, noise1(t * 22 + 50, seed + 1) * amp


def item_t(S, k):
    """(start, end) of k-th text item inside the current scene."""
    k = min(k, len(S.items) - 1)
    return S.items[k]


# ======================================================== shared props
@papered(0.9)
def doc_icon(ctx, x, y, s, glow_a=0.0, t=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    if glow_a > 0:
        glow(ctx, 0, 0, 260, "#7FB8FF", glow_a)
    setc(ctx, "#000000", 0.25)
    rrect(ctx, -86, -106, 180, 230, 16)
    ctx.fill()
    setc(ctx, "#FFFFFF")
    ctx.move_to(-90, -120)
    ctx.line_to(40, -120)
    ctx.line_to(90, -70)
    ctx.line_to(90, 110)
    ctx.curve_to(90, 118, 84, 120, 80, 120)
    ctx.line_to(-80, 120)
    ctx.curve_to(-88, 120, -90, 116, -90, 110)
    ctx.close_path()
    ctx.fill()
    setc(ctx, "#D5DCE8")
    poly(ctx, [(40, -120), (90, -70), (40, -70)])
    ctx.fill()
    setc(ctx, "#2E6BE6")
    rrect(ctx, -62, -82, 90, 16, 6)
    ctx.fill()
    for i, w in enumerate((124, 110, 124, 92, 118, 70)):
        setc(ctx, "#B9C3D6" if i % 3 else "#E35B4F")
        rrect(ctx, -62, -46 + i * 24, w, 10, 5)
        ctx.fill()
    ctx.restore()


@papered(0.9)
def software_box(ctx, x, y, s, tilt=0.0, dim=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(tilt)
    ctx.scale(s, s)
    w, h, d = 260, 340, 70
    setc(ctx, mix("#6E1F1B", "#2A1A1A", dim))
    poly(ctx, [(w / 2, -h), (w / 2 + d, -h - d * 0.5), (w / 2 + d, -d * 0.5), (w / 2, 0)])
    ctx.fill()
    setc(ctx, mix("#E07A5A", "#4A3030", dim))
    poly(ctx, [(-w / 2, -h), (-w / 2 + d, -h - d * 0.5), (w / 2 + d, -h - d * 0.5), (w / 2, -h)])
    ctx.fill()
    ctx.set_source(lin_grad(0, -h, 0, 0, [(0, mix("#D2493A", "#3A2626", dim)), (1, mix("#8F2420", "#2A1C1C", dim))]))
    ctx.rectangle(-w / 2, -h, w, h)
    ctx.fill()
    # abstract emblem: a split sphere ("开天辟地") – no lettering
    setc(ctx, mix("#FFD27A", "#7A6A50", dim))
    circle(ctx, 0, -h * 0.58, 70)
    ctx.fill()
    setc(ctx, mix("#B8322E", "#3A2626", dim))
    ctx.set_line_width(12)
    ctx.move_to(-60, -h * 0.58 + 50)
    ctx.curve_to(-10, -h * 0.58 + 10, 10, -h * 0.58 - 10, 60, -h * 0.58 - 50)
    ctx.stroke()
    setc(ctx, mix("#FFD27A", "#7A6A50", dim), 0.85)
    for i in range(3):
        rrect(ctx, -90, -110 + i * 26, 180 - i * 40, 10, 5)
        ctx.fill()
    setc(ctx, "#FFFFFF", 0.18 * (1 - dim))
    poly(ctx, [(-w / 2, -h), (-w / 2 + 50, -h), (-w / 2 + 160, 0), (-w / 2 + 110, 0)])
    ctx.fill()
    ctx.restore()


def window_grid(ctx, x, y, cols, rows, cw, ch, gx, gy, c, alpha_fn):
    for r in range(rows):
        for q in range(cols):
            a = alpha_fn(r, q)
            if a > 0.01:
                setc(ctx, c, a)
                ctx.rectangle(x + q * (cw + gx), y + r * (ch + gy), cw, ch)
                ctx.fill()


def petals(ctx, seed, n, t, c="#F8C3D2", alpha=0.85):
    rnd = random.Random(seed)
    for _ in range(n):
        x0, y0 = rnd.uniform(-100, W), rnd.uniform(-200, H)
        sp = rnd.uniform(0.6, 1.4)
        x = (x0 + t * 70 * sp) % (W + 200) - 100
        y = (y0 + t * 90 * sp) % (H + 200) - 100
        a = t * 2 * sp + x0
        ctx.save()
        ctx.translate(x + math.sin(t * 1.5 + x0) * 25, y)
        ctx.rotate(a)
        ctx.scale(1, 0.55 + 0.45 * math.sin(a * 1.7))
        setc(ctx, c, alpha)
        ellipse(ctx, 0, 0, 9, 6)
        ctx.fill()
        ctx.restore()


# ======================================================== 1 hook
def _internet_stream(ctx, t, alpha, shift):
    if alpha <= 0.01:
        return
    rnd = random.Random(11)
    nodes = []
    for _ in range(150):
        x0 = rnd.uniform(0, W + 600)
        lane = rnd.uniform(150, 470)
        sp = rnd.uniform(380, 720)
        ph = rnd.uniform(0, TAU)
        col = rnd.choice(["#53E0FF", "#7FB8FF", "#FFFFFF", "#43C6C3", "#B28CFF"])
        x = (x0 + sp * t) % (W + 600) - 300 + shift
        y = lane + math.sin(x * 0.004 + ph) * 46
        nodes.append((x, y, col, rnd.uniform(2.5, 6), sp))
    nodes.sort(key=lambda n: n[0])
    ctx.set_line_width(1.4)
    for i, (x, y, c, r, sp) in enumerate(nodes):
        for j in range(i + 1, min(i + 4, len(nodes))):
            x2, y2 = nodes[j][0], nodes[j][1]
            d = math.hypot(x2 - x, y2 - y)
            if d < 170:
                setc(ctx, "#7FD6FF", alpha * 0.35 * (1 - d / 170))
                ctx.move_to(x, y)
                ctx.line_to(x2, y2)
                ctx.stroke()
    for x, y, c, r, sp in nodes:
        glow(ctx, x, y, r * 5, c, alpha * 0.35)
        line(ctx, x - sp * 0.09, y, x, y, c, r * 0.8, alpha * 0.5)
        setc(ctx, c, alpha)
        circle(ctx, x, y, r)
        ctx.fill()


def _paper_wave(ctx, front, length, base, t):
    """A long folded-paper wave (the internet tide) whose crest sits at x=front."""
    layers = (("#1E4C8A", 0.0, 1.0), ("#2F78B8", 160, 0.82), ("#5FB6E6", 300, 0.62))
    for col, lag, hk in layers:
        f0 = front - lag
        def draw(f0=f0, col=col, hk=hk):
            step = 70
            xs = list(range(int(f0 - length), int(f0) + 1, step)) + [f0]
            ys = []
            for x in xs:
                u = clamp((x - (f0 - length)) / length)
                h = (380 * hk * (0.22 + 0.78 * u ** 2.2) + 18 * math.sin(x * 0.02 + t * 6)) * smooth(u / 0.18)
                ys.append(base - h)
            for i in range(len(xs) - 1):
                up = ys[i + 1] < ys[i]
                setc(ctx, shade(col, 0.08 if up else -0.1))
                poly(ctx, [(xs[i], ys[i]), (xs[i + 1], ys[i + 1]), (xs[i + 1], base + 4), (xs[i], base + 4)])
                ctx.fill()
            # curling crest folded forward
            cx, cy = f0, ys[-1]
            setc(ctx, shade(col, 0.2))
            poly(ctx, [(cx - 140, cy + 30), (cx, cy), (cx + 120, cy + 70), (cx + 40, cy + 60)])
            ctx.fill()
            setc(ctx, shade(col, -0.15))
            poly(ctx, [(cx + 40, cy + 60), (cx + 120, cy + 70), (cx + 60, cy + 150)])
            ctx.fill()
            setc(ctx, "#FFFFFF", 0.55)
            ctx.set_line_width(3)
            ctx.move_to(cx - 140, cy + 30)
            ctx.line_to(cx, cy)
            ctx.line_to(cx + 120, cy + 70)
            ctx.stroke()
        paper(ctx, draw, 1.1, 0.35)
    # data nodes riding the wave
    rnd = random.Random(23)
    for _ in range(60):
        u = rnd.random()
        x = front - u * length * 0.9
        y = base - 380 * (0.22 + 0.78 * (1 - u) ** 2.2) * smooth((1 - u) / 0.18) * rnd.uniform(0.25, 0.9)
        c = rnd.choice(["#FFFFFF", "#9EE7FF", "#53E0FF"])
        glow(ctx, x, y, 22, c, 0.35)
        line(ctx, x - 90, y, x, y, c, 2.5, 0.45)
        setc(ctx, c, 0.9)
        circle(ctx, x, y, 4)
        ctx.fill()


def _wave_spray(ctx, front, length, t):
    """Wind streaks and flecks in front of him while the wave passes."""
    rnd = random.Random(31)
    for _ in range(26):
        u = rnd.random()
        x = front - u * length * 0.8 + rnd.uniform(-40, 40)
        y = rnd.uniform(560, 960)
        ln = rnd.uniform(80, 220)
        line(ctx, x - ln, y, x, y, "#CFF2FF", 3, 0.35 * (1 - u))


@scene("hook")
def hook(ctx, S):
    t = S.t
    t1 = item_t(S, 1)[0]
    q = prog(t, t1 + 0.1, t1 + 0.9)
    push = ease_io(prog(t, t1, S.T))
    z = lerp(1.0, 1.05, prog(t, 0, t1)) + 0.22 * push
    ctx.save()
    cam(ctx, z, lerp(960, 985, push), lerp(540, 560, push))
    vgrad(ctx, [(0, "#04060F"), (0.55, "#101A3A"), (1, "#2C2B57")])
    stars(ctx, 4, 140, t, 0.8)
    glow(ctx, 1500, 260, 520, "#3A64C8", 0.25)
    _internet_stream(ctx, t, 1 - 0.8 * smooth(prog(t, 2.6, t1 + 0.4)), ease_in(prog(t, 1.2, t1 + 1.5)) * 1100)
    skyline(ctx, 21, 820, "#0E1630", "#F6B64A", lit=0.22, t=t, win_alpha=0.45, hmin=160, hmax=430)
    skyline(ctx, 22, 870, "#080C1C", "#FFCF7A", lit=0.12, t=t, win_alpha=0.5, hmin=60, hmax=240, wmin=120, wmax=260)
    fill_rect(ctx, "#070A15", 0, 880, W, 400)
    line(ctx, -50, 882, W + 50, 882, "#2A3560", 3)
    for i in range(0, W + 60, 60):
        line(ctx, i, 830, i, 882, "#1A2344", 4)
    line(ctx, -50, 830, W + 50, 830, "#1F2A50", 5)
    # the internet wave rushes past while he stands still
    wp = ease_in(prog(t, 0.45, t1 - 0.15), 1.4)
    front = lerp(-300, W + 2900, wp)
    if 0 < wp < 1:
        _paper_wave(ctx, front, 2600, 882, t)
    if q > 0:
        light_rays(ctx, 560, 470, 16, 1100, "#FFB347", 0.16 * q, t, rot=t * 0.15)
        glow(ctx, 560, 520, 620, "#FF8D4D", 0.32 * q)
    pose = blend_pose("idle", "fist_up", ease_back(q))
    expr = "calm" if t < 1.0 else ("worried" if t < t1 else "fierce")
    if t < t1 - 0.3:
        look = (clamp((front - 2600 * 0.5 - 560) / 900, -1, 1) * 0.9, -0.2) if 0 < wp < 1 else (0.7, -0.4)
    else:
        look = (0.1, 0.0)
    info = person(ctx, 560, 900, 0.95, outfit="sweater", pose=pose, expr=expr, t=t, look=look, hair_grey=0.08)
    if 0 < wp < 1:
        _wave_spray(ctx, front, 2600, t)
    ctx.restore()
    if q > 0:
        hx, hy = ctx.device_to_user(*info["handR"])
        glow(ctx, hx, hy, 230 * q, "#FFD27A", 0.9 * q)
        rnd = random.Random(5)
        for _ in range(28):
            a = rnd.uniform(0, TAU)
            sp = rnd.uniform(60, 260)
            tt = (t - t1 - 0.2 + rnd.uniform(0, 1.2)) % 1.2
            r = sp * tt
            setc(ctx, "#FFE3A3", q * (1 - tt / 1.2))
            circle(ctx, hx + math.cos(a) * r, hy + math.sin(a) * r - tt * 40, 3)
            ctx.fill()


# ======================================================== 过渡 rewind
@scene("rewind")
def rewind(ctx, S):
    t, T = S.t, S.T
    g = cairo.RadialGradient(960, 540, 50, 960, 540, 1150)
    g.add_color_stop_rgba(0, *hexc("#4A3522"))
    g.add_color_stop_rgba(1, *hexc("#0E0905"))
    ctx.set_source(g)
    ctx.paint()
    speed = 0.4 + 2.6 * ease_in(prog(t, 0, T), 2)
    rnd = random.Random(3)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for _ in range(120):
        a = rnd.uniform(0, TAU)
        ph = rnd.random()
        r = ((ph - t * 0.35 * speed) % 1.0) ** 1.6 * 1250
        ln = 40 + speed * 70
        setc(ctx, "#F2D7A6", 0.25 * clamp(r / 300))
        ctx.set_line_width(2 + r / 400)
        ctx.move_to(960 + math.cos(a) * r, 540 + math.sin(a) * r)
        ctx.line_to(960 + math.cos(a) * (r + ln), 540 + math.sin(a) * (r + ln))
        ctx.stroke()
    for i in range(5):
        rr = ((i / 5 - t * 0.5) % 1.0) * 900
        setc(ctx, "#F2D7A6", 0.12 * (1 - rr / 900))
        ctx.set_line_width(3)
        circle(ctx, 960, 540, rr)
        ctx.stroke()
    R = 360
    setc(ctx, "#F2D7A6", 0.12)
    circle(ctx, 960, 540, R)
    ctx.fill()
    setc(ctx, "#F2D7A6", 0.55)
    ctx.set_line_width(6)
    circle(ctx, 960, 540, R)
    ctx.stroke()
    for i in range(60):
        a = i / 60 * TAU
        r1 = R - (34 if i % 5 == 0 else 16)
        line(ctx, 960 + math.cos(a) * r1, 540 + math.sin(a) * r1, 960 + math.cos(a) * (R - 6),
             540 + math.sin(a) * (R - 6), "#F2D7A6", 5 if i % 5 == 0 else 2, 0.6)
    ang = -(t * 1.2 + t * t * 1.8) * TAU
    line(ctx, 960, 540, 960 + math.cos(ang - math.pi / 2) * 290, 540 + math.sin(ang - math.pi / 2) * 290, "#FFF1D2", 8, 0.4)
    ang_h = ang / 12
    line(ctx, 960, 540, 960 + math.cos(ang_h - math.pi / 2) * 190, 540 + math.sin(ang_h - math.pi / 2) * 190, "#FFF1D2", 12, 0.4)
    setc(ctx, "#FFF1D2", 0.5)
    circle(ctx, 960, 540, 12)
    ctx.fill()
    g2 = cairo.RadialGradient(960, 560, 0, 960, 560, 520)
    g2.add_color_stop_rgba(0, 0.05, 0.03, 0.02, 0.55)
    g2.add_color_stop_rgba(1, 0.05, 0.03, 0.02, 0.0)
    ctx.set_source(g2)
    ellipse(ctx, 960, 560, 520, 130)
    ctx.fill()
    for y in range(0, H, 6):
        fill_rect(ctx, "#000000", 0, y, W, 2, 0.12)
    by = (t * 700) % (H + 300) - 150
    fill_rect(ctx, "#FFFFFF", 0, by, W, 60, 0.05)
    fill_rect(ctx, "#FFFFFF", 0, 0, W, H, 0.85 * ease_in(prog(t, T - 0.55, T)))


# ======================================================== 2 campus
@papered(0.9)
def campus_building(ctx, cx, base, s):
    ctx.save()
    ctx.translate(cx, base)
    ctx.scale(s, s)
    roof = "#3F8C6C"
    roof_d = "#2C6A50"
    wall = "#C46E52"
    # side wings
    for sx in (-1, 1):
        setc(ctx, shade(wall, -0.05))
        ctx.rectangle(sx * 230 - 170 * (sx < 0) - (0 if sx < 0 else 0), -210, 170, 210)
        ctx.fill()
    setc(ctx, wall)
    ctx.rectangle(-400, -200, 800, 200)
    ctx.fill()
    for r in range(2):
        for i in range(12):
            x = -360 + i * 62
            setc(ctx, "#F4E3C8")
            rrect(ctx, x, -175 + r * 90, 30, 52, 14)
            ctx.fill()
            setc(ctx, "#5A86A6", 0.6)
            rrect(ctx, x + 5, -165 + r * 90, 20, 38, 9)
            ctx.fill()

    def roof_shape(w, y, h, col, colD):
        setc(ctx, col)
        ctx.move_to(-w / 2 - 50, y - 12)
        ctx.curve_to(-w / 2 - 20, y - 4, -w / 2 + 10, y - h * 0.4, -w / 2 + 60, y - h)
        ctx.line_to(w / 2 - 60, y - h)
        ctx.curve_to(w / 2 - 10, y - h * 0.4, w / 2 + 20, y - 4, w / 2 + 50, y - 12)
        ctx.line_to(w / 2 + 10, y + 4)
        ctx.line_to(-w / 2 - 10, y + 4)
        ctx.close_path()
        ctx.fill()
        setc(ctx, colD)
        ctx.set_line_width(3)
        for i in range(int(w / 26)):
            x = -w / 2 + 20 + i * 26
            ctx.move_to(x, y - h + 6)
            ctx.line_to(x * 1.06, y)
            ctx.stroke()
        rrect(ctx, -w / 2 + 50, y - h - 8, w - 100, 12, 6)
        ctx.fill()

    roof_shape(840, -198, 70, roof, roof_d)
    # central tower
    setc(ctx, shade(wall, 0.05))
    ctx.rectangle(-130, -380, 260, 180)
    ctx.fill()
    for i in range(4):
        setc(ctx, "#F4E3C8")
        rrect(ctx, -100 + i * 56, -350, 30, 60, 14)
        ctx.fill()
    roof_shape(320, -378, 60, roof, roof_d)
    setc(ctx, shade(wall, 0.1))
    ctx.rectangle(-60, -500, 120, 70)
    ctx.fill()
    setc(ctx, roof)
    poly(ctx, [(-100, -496), (0, -590), (100, -496)])
    ctx.fill()
    setc(ctx, "#E9C46A")
    circle(ctx, 0, -598, 10)
    ctx.fill()
    # steps
    for i in range(4):
        setc(ctx, mix("#D9CBB0", "#BFAF92", i / 4))
        ctx.rectangle(-140 - i * 16, -16 + i * 6, 280 + i * 32, 8)
        ctx.fill()
    ctx.restore()


@papered(0.9)
def cherry_tree(ctx, x, y, s, seed):
    rnd = random.Random(seed)
    setc(ctx, "#6B4632")
    ctx.move_to(x - 10 * s, y)
    ctx.line_to(x - 4 * s, y - 140 * s)
    ctx.line_to(x + 8 * s, y - 140 * s)
    ctx.line_to(x + 12 * s, y)
    ctx.close_path()
    ctx.fill()
    for _ in range(9):
        ox, oy = rnd.uniform(-90, 90) * s, rnd.uniform(-230, -130) * s
        setc(ctx, rnd.choice(["#F7B9CB", "#F29CB5", "#FBD3DE"]))
        circle(ctx, x + ox, y + oy, rnd.uniform(50, 80) * s)
        ctx.fill()


@papered(0.9)
def hourglass(ctx, x, y, s, rot, fill):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    setc(ctx, "#7A4E2E")
    rrect(ctx, -46, -66, 92, 12, 5)
    ctx.fill()
    rrect(ctx, -46, 54, 92, 12, 5)
    ctx.fill()
    setc(ctx, "#FFFFFF", 0.55)
    ctx.move_to(-36, -54)
    ctx.line_to(36, -54)
    ctx.line_to(4, 0)
    ctx.line_to(36, 54)
    ctx.line_to(-36, 54)
    ctx.line_to(-4, 0)
    ctx.close_path()
    ctx.fill()
    setc(ctx, "#F6B64A")
    top = 1 - fill
    if top > 0.02:
        hh = 46 * top
        poly(ctx, [(-30 * top, -hh - 4), (30 * top, -hh - 4), (2, -4), (-2, -4)])
        ctx.fill()
    if fill > 0.02:
        hh = 46 * fill
        poly(ctx, [(-34, 52), (34, 52), (34 * (1 - fill * 0.6), 52 - hh), (-34 * (1 - fill * 0.6), 52 - hh)])
        ctx.fill()
    ctx.restore()


@scene("campus")
def campus(ctx, S):
    t, T = S.t, S.T
    ctx.save()
    cam(ctx, 1.0 + 0.04 * t / T, 960, 560)
    vgrad(ctx, [(0, "#7CB8E3"), (0.65, "#CFE4EE"), (1, "#F8E2BF")])
    glow(ctx, 1560, 200, 360, "#FFF4D0", 0.8)
    hills(ctx, 700, 40, 0.004, 1.0, "#9CC3B4")
    hills(ctx, 760, 30, 0.006, 2.0, "#7FB09A")
    campus_building(ctx, 1320, 800, 0.95)
    ground(ctx, 790, "#8FC07E", "#6C9E5E")
    setc(ctx, "#E3D2B0")
    poly(ctx, [(1180, 800), (1460, 800), (1700, H), (900, H)])
    ctx.fill()
    for i, (tx, ts) in enumerate(((180, 1.1), (330, 0.8), (1760, 1.0), (1880, 0.75))):
        cherry_tree(ctx, tx, 820, ts, i + 3)
    walk_p = prog(t, 0, 1.4)
    x = lerp(-120, 470, ease_out(walk_p, 2))
    walking = walk_p < 1
    # book columns (4 years' credits) filling at double speed
    fill_p = prog(t, 1.2, T - 0.6)
    n_total = 24
    shown = fill_p * n_total
    cols = ["#E76F51", "#2A9D8F", "#E9C46A", "#457B9D", "#F4A261", "#8AB17D"]
    for i in range(n_total):
        c, r = i // 6, i % 6
        a = clamp(shown - i)
        if a <= 0:
            continue
        bx = 700 + c * 92
        by = 880 - r * 26 - 26
        pop = ease_back(a)
        ctx.save()
        ctx.translate(bx + 36, by + 13 - (1 - pop) * 60)
        ctx.rotate((noise1(i * 3.1) * 0.06))
        setc(ctx, cols[(i * 5 + c) % 6], a)
        rrect(ctx, -38, -12, 76, 24, 4)
        ctx.fill()
        setc(ctx, "#FFFFFF", 0.6 * a)
        ctx.rectangle(-30, -3, 52, 4)
        ctx.fill()
        ctx.restore()
    # hourglass flips twice (= two years)
    flips = [1.4 + (T - 2.0) * 0.5, T - 0.6]
    rot, fl = 0.0, prog(t, 1.2, flips[0])
    if t > flips[0]:
        rot = math.pi * ease_io(prog(t, flips[0], flips[0] + 0.35))
        fl = prog(t, flips[0] + 0.35, flips[1])
    if t > flips[1]:
        rot = math.pi + math.pi * ease_io(prog(t, flips[1], flips[1] + 0.35))
        fl = 0.0
    hourglass(ctx, 838, 560, 1.0, rot, fl)
    expr = "smile" if fill_p < 0.85 else "happy"
    person(ctx, x, 880, 0.82, outfit="student", pose="hold", expr=expr, t=t,
           walk=(t * 9 if walking else None), look=(0.6, 0.2), hair_grey=0)
    if True:
        # books in arms
        bx, by = x, 880 - 0.82 * 250
        for j, c in enumerate(("#E76F51", "#457B9D")):
            setc(ctx, c)
            rrect(ctx, bx - 50, by - 16 - j * 18, 100, 18, 3)
            ctx.fill()
    petals(ctx, 8, 40, t)
    ctx.restore()


def ground(ctx, y, c1, c2):
    vgrad(ctx, [(0, c1), (1, c2)], 0, y, W, H - y + 200)


# ======================================================== 2 startup / fail
@papered(0.9)
def crt(ctx, x, y, on, t, static=0.0):
    setc(ctx, "#D8CFB8")
    rrect(ctx, x - 170, y - 260, 340, 250, 22)
    ctx.fill()
    setc(ctx, "#BDB298")
    poly(ctx, [(x - 110, y - 10), (x + 110, y - 10), (x + 80, y + 10), (x - 80, y + 10)])
    ctx.fill()
    setc(ctx, "#1A1E1E")
    rrect(ctx, x - 140, y - 236, 280, 196, 18)
    ctx.fill()
    if on > 0:
        setc(ctx, "#0F4A44", on)
        rrect(ctx, x - 132, y - 228, 264, 180, 14)
        ctx.fill()
        rnd = random.Random(int(t * 8))
        for i in range(8):
            w = rnd.uniform(40, 200)
            setc(ctx, "#6CF5C8", 0.8 * on)
            ctx.rectangle(x - 116, y - 212 + i * 20, w, 7)
            ctx.fill()
        glow(ctx, x, y - 140, 300, "#6CF5C8", 0.25 * on)
    if static > 0:
        rnd = random.Random(int(t * 30))
        for i in range(40):
            setc(ctx, "#FFFFFF", rnd.uniform(0.1, 0.6) * static)
            ctx.rectangle(x - 132, y - 228 + rnd.uniform(0, 176), 264, rnd.uniform(1, 4))
            ctx.fill()


def bulb(ctx, x, y, on, broken=0.0, s=1.0):
    line(ctx, x, 0, x, y - 50 * s, "#2B2B33", 3)
    if on > 0:
        glow(ctx, x, y, 380 * s, "#FFD27A", 0.55 * on)
        light_rays(ctx, x, y, 12, 260 * s, "#FFE7A8", 0.18 * on, rot=0.1)
    setc(ctx, mix("#6E6E78", "#FFE9A8", on))
    circle(ctx, x, y, 34 * s)
    ctx.fill()
    setc(ctx, "#8A8A92")
    rrect(ctx, x - 16 * s, y - 52 * s, 32 * s, 22 * s, 4)
    ctx.fill()
    if broken > 0:
        setc(ctx, "#1A1A22", broken)
        ctx.set_line_width(3)
        ctx.move_to(x - 18 * s, y - 14 * s)
        ctx.line_to(x - 2 * s, y)
        ctx.line_to(x - 12 * s, y + 10 * s)
        ctx.line_to(x + 8 * s, y + 24 * s)
        ctx.stroke()


@papered(0.9)
def meal_ticket(ctx, x, y, rot, a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    setc(ctx, "#F4D58D", a)
    rrect(ctx, -46, -26, 92, 52, 6)
    ctx.fill()
    setc(ctx, "#C9A24A", a)
    ctx.set_line_width(2)
    ctx.set_dash([5, 5])
    ctx.move_to(-22, -24)
    ctx.line_to(-22, 24)
    ctx.stroke()
    ctx.set_dash([])
    # tiny bowl icon
    ctx.arc(14, -2, 15, 0, math.pi)
    ctx.close_path()
    ctx.fill()
    line(ctx, 4, -12, 12, -26, "#C9A24A", 2, a)
    line(ctx, 14, -12, 22, -26, "#C9A24A", 2, a)
    ctx.restore()


@papered(0.9)
def card(ctx, x, y, rot, face, suit_col="#E2504C", a=1.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(abs(math.cos(face * math.pi)) + 0.02, 1)
    up = face > 0.5
    setc(ctx, "#FFFFFF" if up else "#2E5AAC", a)
    rrect(ctx, -32, -46, 64, 92, 7)
    ctx.fill()
    if up:
        setc(ctx, suit_col, a)
        ctx.move_to(0, 18)
        ctx.curve_to(-30, -6, -14, -30, 0, -14)
        ctx.curve_to(14, -30, 30, -6, 0, 18)
        ctx.fill()
    else:
        setc(ctx, "#FFFFFF", 0.4 * a)
        ctx.set_line_width(2)
        rrect(ctx, -24, -38, 48, 76, 5)
        ctx.stroke()
    ctx.restore()


@scene("startup")
def startup(ctx, S):
    t, T = S.t, S.T
    f0 = item_t(S, 1)[0] if len(S.items) > 1 else 99
    tf = t - f0
    fail = tf >= 0
    dim = 0.5 * smooth(prog(tf, 0.1, 0.9)) if fail else 0.0
    ctx.save()
    sx, sy = shake(t, 9 * pulse(tf, 0.0, 0.5) if fail else 0, 3)
    cam(ctx, 1.02 + 0.03 * prog(t, 0, T), 960, 540, sx, sy)
    vgrad(ctx, [(0, "#4B3F63"), (1, "#3A2F4F")])
    # window
    setc(ctx, "#1B2140")
    rrect(ctx, 150, 160, 360, 300, 10)
    ctx.fill()
    stars(ctx, 9, 30, t, 0.7, y_max=440)
    ctx.save()
    rrect(ctx, 150, 160, 360, 300, 10)
    ctx.clip()
    stars(ctx, 9, 0, t)
    skyline(ctx, 3, 470, "#2A2F55", "#F6B64A", lit=0.3, x0=140, x1=520, hmin=40, hmax=150, wmin=40, wmax=80)
    if fail:
        rnd = random.Random(1)
        for _ in range(50):
            x0, y0 = rnd.uniform(150, 510), rnd.uniform(0, 300)
            y = 160 + (y0 + tf * 600) % 300
            line(ctx, x0, y, x0 - 6, y + 22, "#9FB4E0", 2, 0.5 * prog(tf, 0.3, 1.0))
    ctx.restore()
    setc(ctx, "#2C2440")
    ctx.set_line_width(14)
    rrect(ctx, 150, 160, 360, 300, 10)
    ctx.stroke()
    line(ctx, 330, 160, 330, 460, "#2C2440", 10)
    # shelf poster shapes (no text)
    setc(ctx, "#5D5080")
    rrect(ctx, 1500, 200, 230, 150, 8)
    ctx.fill()
    setc(ctx, "#E9C46A", 0.7)
    star_shape(ctx, 1615, 275, 46)
    ctx.fill()
    ground(ctx, 860, "#2C2338", "#221B2C")
    # light bulb
    on = smooth(prog(t, 0.6, 1.0))
    if fail:
        flick = 1.0 if tf < 0.08 else (0.4 if tf < 0.16 else (0.8 if tf < 0.22 else 0.0))
        on = flick
    bulb(ctx, 960, 210, on, broken=1.0 if fail and tf > 0.22 else 0.0, s=1.0 * (0.6 + 0.4 * ease_back(prog(t, 0.6, 1.0))))
    # characters behind desk
    senior_a = 1.0 - smooth(prog(tf, 0.7, 1.6)) if fail else 1.0
    exp_me = "happy" if not fail else ("sad" if tf < 1.6 else ("tired" if tf < 2.8 else "smile"))
    exp_sr = "grin" if not fail else "sad"
    person(ctx, 700, 900, 0.95, outfit="student", pose="type" if not fail else ("sad" if tf < 1.6 else "hold"),
           expr=exp_me, t=t, look=(0.4, 0.3))
    if senior_a > 0.01:
        person(ctx, 1230, 900, 1.0, outfit="senior", pose="point" if not fail else "sad", expr=exp_sr, t=t,
               hair_style="flat", glasses=True, look=(-0.5, 0.3), alpha=senior_a, flip=True, seed=3)
    # desk
    setc(ctx, "#8A5A3C")
    rrect(ctx, 480, 690, 960, 34, 8)
    ctx.fill()
    setc(ctx, "#6E4430")
    ctx.rectangle(510, 724, 900, 200)
    ctx.fill()
    setc(ctx, "#5A3726")
    ctx.rectangle(540, 760, 400, 6)
    ctx.fill()
    crt_on = 1.0 if not fail else (0.0 if tf > 0.5 else 0.6)
    crt(ctx, 1000, 694, crt_on * smooth(prog(t, 0.2, 0.6)), t, static=(1.0 - prog(tf, 0.0, 0.55)) if fail else 0.0)
    if fail:
        ca = smooth(prog(tf, 1.5, 1.9))
        for i in range(3):
            fl = prog(tf, 1.8 + i * 0.2, 2.1 + i * 0.2)
            card(ctx, 640 + i * 76, 690 - 50, (i - 1) * 0.12, fl, a=ca)
        for i in range(4):
            st = 2.2 + i * 0.42
            pp = ease_out(prog(tf, st, st + 0.45))
            if pp > 0:
                tx = lerp(1500, 860 + i * 14, pp)
                ty = lerp(560, 676 - i * 8, pp)
                meal_ticket(ctx, tx, ty, lerp(0.8, -0.08 + i * 0.05, pp))
                if pp > 0.95:
                    glow(ctx, tx, ty, 70, "#FFE7A8", 0.5 * (1 - prog(tf, st + 0.45, st + 0.9)))
    ctx.restore()
    if dim > 0:
        fill_rect(ctx, "#0A0614", alpha=dim)


# ======================================================== 3 kingsoft 1992
@papered(0.9)
def bicycle(ctx, x, y, s, t, c="#2B2B35"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    ctx.set_line_width(5)
    setc(ctx, c)
    for wx in (-60, 60):
        circle(ctx, wx, 0, 38)
        ctx.stroke()
        a = -t * 6
        line(ctx, wx + math.cos(a) * 36, math.sin(a) * 36, wx - math.cos(a) * 36, -math.sin(a) * 36, c, 2)
    ctx.set_line_width(6)
    setc(ctx, c)
    ctx.move_to(-60, 0)
    ctx.line_to(-10, -50)
    ctx.line_to(45, -50)
    ctx.line_to(60, 0)
    ctx.move_to(-10, -50)
    ctx.line_to(5, 0)
    ctx.line_to(60, 0)
    ctx.move_to(45, -50)
    ctx.line_to(40, -78)
    ctx.move_to(-10, -50)
    ctx.line_to(-18, -70)
    ctx.stroke()
    # rider
    setc(ctx, "#3C5A80")
    rrect(ctx, -30, -150, 50, 90, 18)
    ctx.fill()
    setc(ctx, "#F3CBA2")
    circle(ctx, -4, -178, 26)
    ctx.fill()
    setc(ctx, "#191A22")
    ctx.arc(-4, -184, 27, math.pi, TAU)
    ctx.fill()
    ctx.restore()


@scene("kingsoft")
def kingsoft(ctx, S):
    t, T = S.t, S.T
    ctx.save()
    cam(ctx, 1.0 + 0.08 * ease_io(t / T), lerp(960, 1080, ease_io(t / T)), 540)
    vgrad(ctx, [(0, "#86B4C4"), (0.7, "#D9E0D0"), (1, "#EBD7AE")])
    glow(ctx, 380, 180, 300, "#FFF6DA", 0.7)
    skyline(ctx, 40, 780, "#A9BDC3", None, hmin=80, hmax=260, wmin=90, wmax=200)
    # office tower
    bx, bw, btop = 1000, 480, 150
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
    # entrance
    dx = bx + bw / 2
    setc(ctx, "#5D4A36")
    ctx.rectangle(dx - 110, 620, 220, 190)
    ctx.fill()
    op = smooth(prog(t, T * 0.62, T * 0.85))
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
    for tx in (160, 640, 1700):
        setc(ctx, "#5E4636")
        ctx.rectangle(tx - 8, 640, 16, 170)
        ctx.fill()
        setc(ctx, "#5E9466")
        circle(ctx, tx, 610, 80)
        ctx.fill()
        setc(ctx, "#4E8456")
        circle(ctx, tx + 40, 640, 56)
        ctx.fill()
    bicycle(ctx, lerp(2100, -300, t / T), 860, 0.9, t)
    wp = prog(t, 0.2, T * 0.82)
    x = lerp(160, dx, ease_io(wp))
    a = 1 - smooth(prog(t, T * 0.8, T * 0.98))
    s = lerp(0.85, 0.62, ease_io(wp))
    y = lerp(900, 812, ease_io(wp))
    if a > 0.01:
        person(ctx, x, y, s, outfit="shirt", pose="idle", expr="smile", t=t,
               walk=(t * 9 if wp < 1 else None), facing="front" if wp < 0.55 else "back", alpha=a)
    ctx.restore()


# ======================================================== 3 pangu 1995
@scene("pangu")
def pangu(ctx, S):
    t, T = S.t, S.T
    hit = T * 0.55
    ctx.save()
    sx, sy = shake(t, 12 * pulse(t, hit, hit + 0.45), 7)
    cam(ctx, 1.0, 960, 540, sx, sy)
    vgrad(ctx, [(0, "#18213F"), (1, "#0B1022")])
    spotlight(ctx, 470, -50, 470, 800, 60, 300, "#FFE6B0", 0.18 * (1 - 0.6 * prog(t, hit, hit + 1)))
    ground(ctx, 800, "#121832", "#090D1C")
    # pedestal + box
    setc(ctx, "#2B355E")
    rrect(ctx, 300, 760, 340, 60, 8)
    ctx.fill()
    tilt = -0.08 * ease_out(prog(t, hit + 0.2, hit + 0.8))
    software_box(ctx, 460, 762, 1.05 * ease_back(prog(t, 0.0, 0.5)), tilt, dim=0.55 * prog(t, hit, hit + 1.2))
    # chart: dashed "expected" bar divided into 10, actual fills one
    base = 800
    bx, bw, bh = 1010, 230, 560
    gp = ease_out(prog(t, 0.35, 1.4))
    setc(ctx, "#8EA2D8", 0.8)
    ctx.set_line_width(4)
    ctx.set_dash([16, 10])
    rrect(ctx, bx, base - bh * gp, bw, bh * gp, 10)
    ctx.stroke()
    ctx.set_dash([])
    for i in range(1, 10):
        yy = base - bh * i / 10
        if yy > base - bh * gp:
            line(ctx, bx + 14, yy, bx + bw - 14, yy, "#8EA2D8", 2, 0.35)
    setc(ctx, "#8EA2D8", 0.12)
    rrect(ctx, bx, base - bh * gp, bw, bh * gp, 10)
    ctx.fill()
    ap = prog(t, 1.6, hit)
    # actual bar tries to climb and stalls at one tenth
    level = 0.1 * ease_out(ap, 2) + 0.05 * math.sin(ap * math.pi) ** 2
    if ap > 0:
        ah = bh * level
        col = mix("#F6B64A", "#E2504C", prog(t, hit - 0.2, hit + 0.3))
        glow(ctx, bx + bw + 330, base - ah / 2, 180, col, 0.3 * prog(t, hit, hit + 0.4))
        setc(ctx, col)
        rrect(ctx, bx + bw + 230, base - ah, bw, ah, 10)
        ctx.fill()
    line(ctx, 960, base, 1760, base, "#C8D2F0", 4, 0.8)
    # down arrow
    if t > hit:
        ap2 = ease_back(prog(t, hit, hit + 0.4))
        ctx.save()
        ctx.translate(bx + bw * 1.5 + 230, base - bh * 0.1 - 150)
        ctx.scale(ap2, ap2)
        setc(ctx, "#E2504C")
        poly(ctx, [(-22, -70), (22, -70), (22, 0), (52, 0), (0, 56), (-52, 0), (-22, 0)])
        ctx.fill()
        ctx.restore()
    expr = "smile" if t < hit else "shock"
    person(ctx, 1760, 820, 0.62, outfit="shirt", pose="idle" if t < hit else "shrug", expr=expr, t=t,
           look=(-0.8, -0.2), flip=False)
    ctx.restore()


# ======================================================== 3 ledger
def jar_path(ctx, cx, top, w, h):
    ctx.move_to(cx - w * 0.28, top)
    ctx.line_to(cx + w * 0.28, top)
    ctx.line_to(cx + w * 0.28, top + 40)
    ctx.curve_to(cx + w * 0.5, top + 60, cx + w * 0.5, top + 90, cx + w * 0.5, top + 130)
    ctx.line_to(cx + w * 0.5, top + h - 40)
    ctx.curve_to(cx + w * 0.5, top + h, cx + w * 0.4, top + h, cx + w * 0.3, top + h)
    ctx.line_to(cx - w * 0.3, top + h)
    ctx.curve_to(cx - w * 0.4, top + h, cx - w * 0.5, top + h, cx - w * 0.5, top + h - 40)
    ctx.line_to(cx - w * 0.5, top + 130)
    ctx.curve_to(cx - w * 0.5, top + 90, cx - w * 0.5, top + 60, cx - w * 0.28, top + 40)
    ctx.close_path()


@scene("ledger")
def ledger(ctx, S):
    t, T = S.t, S.T
    hb = (t * 1.5) % 1.0
    beat = math.exp(-hb * 9) + 0.6 * math.exp(-max(0, hb - 0.18) * 9) * (hb > 0.18)
    vgrad(ctx, [(0, "#230F13"), (1, "#0D0608")])
    glow(ctx, 960, 420, 700, "#E2504C", 0.12 + 0.12 * beat)
    cx, top, w, h = 960, 110, 440, 560
    level = lerp(0.92, 0.07, ease_io(prog(t, 0.15, T * 0.85)))
    # coins inside
    ctx.save()
    jar_path(ctx, cx, top, w, h)
    ctx.clip()
    setc(ctx, "#FFFFFF", 0.05)
    ctx.paint()
    surf_y = top + h - (h - 40) * level
    rnd = random.Random(2)
    rows = int(h / 22) + 2
    for r in range(rows):
        yy = top + h - 18 - r * 22
        if yy < surf_y - 6:
            break
        for q in range(9):
            xx = cx - w * 0.45 + q * (w * 0.9 / 8) + (r % 2) * 18 + rnd.uniform(-6, 6)
            setc(ctx, "#B8862E")
            ellipse(ctx, xx, yy + 5, 30, 12)
            ctx.fill()
            setc(ctx, rnd.choice(["#F6C453", "#E9B03E", "#FFD67A"]))
            ellipse(ctx, xx, yy, 30, 12)
            ctx.fill()
    ctx.restore()
    setc(ctx, "#DDE6F5", 0.75)
    ctx.set_line_width(7)
    jar_path(ctx, cx, top, w, h)
    ctx.stroke()
    setc(ctx, "#FFFFFF", 0.25)
    rrect(ctx, cx - w * 0.42, top + 150, 18, h - 230, 9)
    ctx.fill()
    # coins leaking out of a crack at the bottom
    flow = 1 - prog(t, T * 0.8, T)
    rnd = random.Random(8)
    for i in range(36):
        ph = rnd.random()
        tt = (t * 1.2 + ph) % 1.0
        if t < 0.2 or (flow < 0.5 and ph > flow * 2):
            continue
        x = cx + rnd.uniform(-40, 40) + tt * rnd.uniform(-80, 80)
        y = top + h + 10 + tt * tt * 600
        wspin = abs(math.cos(t * 9 + ph * 20))
        setc(ctx, "#F6C453", 1 - tt * 0.5)
        ellipse(ctx, x, y, 24 * wspin + 3, 24)
        ctx.fill()
    setc(ctx, "#0D0608")
    poly(ctx, [(cx - 30, top + h - 4), (cx - 6, top + h - 20), (cx + 10, top + h - 6), (cx + 34, top + h - 18), (cx + 30, top + h + 6), (cx - 30, top + h + 6)])
    ctx.fill()
    g = cairo.RadialGradient(960, 540, 300, 960, 540, 1100)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0.4, 0.02, 0.04, 0.35 + 0.25 * beat)
    ctx.set_source(g)
    ctx.paint()


# ======================================================== 3 lights out
@scene("lights")
def lights(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#0A1430"), (1, "#18264E")])
    stars(ctx, 30, 40, t, 0.7, y_max=200)
    glow(ctx, 380, 130, 120, "#E8EEFF", 0.5)
    setc(ctx, "#F2F4FF")
    circle(ctx, 380, 130, 34)
    ctx.fill()
    # opposite building
    setc(ctx, "#1C2442")
    ctx.rectangle(120, 200, 1680, 700)
    ctx.fill()
    cols, rows = 20, 10
    rnd = random.Random(12)
    order = list(range(cols * rows))
    rnd.shuffle(order)
    rank = {idx: i for i, idx in enumerate(order)}
    lit0 = {idx: rnd.random() < 0.82 for idx in range(cols * rows)}
    progress = ease_in(prog(t, 0.4, T - 0.5), 1.4)
    dark = 0.0
    total_lit = 0
    for r in range(rows):
        for q in range(cols):
            idx = r * cols + q
            if not lit0[idx]:
                continue
            off_at = rank[idx] / (cols * rows)
            a = 1.0 if progress < off_at else max(0.0, 1 - (progress - off_at) * 60)
            x, y = 170 + q * 80, 240 + r * 62
            setc(ctx, "#2A3458")
            ctx.rectangle(x, y, 54, 38)
            ctx.fill()
            if a > 0:
                total_lit += a
                setc(ctx, mix("#FFC86B", "#FFE6A8", (idx * 37 % 10) / 10), a)
                ctx.rectangle(x, y, 54, 38)
                ctx.fill()
                glow(ctx, x + 27, y + 19, 60, "#FFC86B", 0.15 * a)
    lit_frac = total_lit / max(1, sum(lit0.values()))
    # office window frame (foreground)
    setc(ctx, "#05070E")
    ctx.rectangle(0, 0, W, 70)
    ctx.rectangle(0, 0, 110, H)
    ctx.rectangle(W - 110, 0, 110, H)
    ctx.rectangle(0, 780, W, 400)
    ctx.rectangle(650, 0, 26, 780)
    ctx.rectangle(1244, 0, 26, 780)
    ctx.fill()
    setc(ctx, "#FFFFFF", 0.04)
    poly(ctx, [(200, 70), (520, 70), (300, 780), (110, 780)])
    ctx.fill()
    # him, from behind, lit by the windows across
    person(ctx, 940, 1150, 1.25, outfit="shirt", pose="sad", expr="sad", t=t, facing="back", sit=True, breathe=True)
    fill_rect(ctx, "#05070E", alpha=0.55 - 0.35 * lit_frac)
    glow(ctx, 940, 760, 500, "#FFC86B", 0.12 * lit_frac)


# ======================================================== 4 resign
@papered(0.9)
def envelope(ctx, x, y, s, rot=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    setc(ctx, "#000000", 0.25)
    rrect(ctx, -150, -86, 310, 190, 10)
    ctx.fill()
    setc(ctx, "#FBF6EC")
    rrect(ctx, -160, -100, 320, 200, 10)
    ctx.fill()
    setc(ctx, "#E5DCCB")
    ctx.set_line_width(4)
    ctx.move_to(-156, -96)
    ctx.line_to(0, 14)
    ctx.line_to(156, -96)
    ctx.stroke()
    setc(ctx, "#C0392B")
    circle(ctx, 0, 14, 22)
    ctx.fill()
    ctx.restore()


@papered(0.9)
def resign_letter(ctx, x, y, s, rot=0.0, sign=1.0):
    """Resignation letter: ruled sheet, a heading bar and a red signature scribble (no lettering)."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    setc(ctx, "#FFFDF6")
    poly(ctx, [(-150, -200), (110, -200), (150, -160), (150, 200), (-150, 200)])
    ctx.fill()
    setc(ctx, "#E6DCC8")
    poly(ctx, [(110, -200), (150, -160), (110, -160)])
    ctx.fill()
    setc(ctx, "#F1E9D8")
    ctx.rectangle(-150, 10, 300, 190)
    ctx.fill()
    setc(ctx, "#3A3F55")
    rrect(ctx, -70, -168, 140, 16, 8)
    ctx.fill()
    for i in range(8):
        w_ = 230 if i % 4 != 3 else 150
        setc(ctx, "#B9C0CF")
        rrect(ctx, -115, -124 + i * 30, w_, 7, 3.5)
        ctx.fill()
    if sign > 0:
        setc(ctx, "#C0392B")
        ctx.set_line_width(4)
        ctx.move_to(30, 160)
        n = int(14 * sign) + 1
        for j in range(1, n):
            ctx.line_to(30 + j * 7, 160 + (-12 if j % 2 else 8) * (1 - j / 18))
        ctx.stroke()
    ctx.restore()


@scene("resign")
def resign(ctx, S):
    t, T = S.t, S.T
    split = T * 0.5
    a2 = smooth(prog(t, split - 0.15, split + 0.3))
    if a2 < 1:
        # close-up of desk: the resignation letter is laid down beside its envelope
        vgrad(ctx, [(0, "#2D2A3A"), (1, "#1B1824")])
        glow(ctx, 960, 300, 700, "#FFD9A0", 0.2)
        setc(ctx, "#7A4F35")
        ctx.rectangle(0, 560, W, 600)
        ctx.fill()
        setc(ctx, "#8C5E40")
        ctx.rectangle(0, 560, W, 14)
        ctx.fill()
        for i in range(6):
            line(ctx, 0, 640 + i * 70, W, 630 + i * 74, "#6A4430", 3, 0.6)
        envelope(ctx, 560, 720, 0.95, 0.1)
        ep = ease_out(prog(t, 0.05, 0.85))
        ex = lerp(1560, 1060, ep)
        ey = lerp(560, 690, ep)
        resign_letter(ctx, ex, ey, 1.0, lerp(0.3, -0.05, ep), sign=prog(t, 0.2, 0.8))
        hand_back = ease_in(prog(t, 0.95, 1.35))
        hx = ex + 170 + hand_back * 700
        setc(ctx, "#E9ECEF")
        rrect(ctx, hx + 20, ey - 50, 900, 90, 40)
        ctx.fill()
        setc(ctx, "#F3CBA2")
        ellipse(ctx, hx, ey, 64, 44)
        ctx.fill()
        if a2 > 0:
            fill_rect(ctx, "#000000", alpha=a2)
    if a2 > 0:
        ctx.push_group()
        tt = prog(t, split, T)
        # sky cycling through ~6 day/night turns while seasons change
        cyc = tt * 6
        day = 0.5 + 0.5 * math.cos(cyc * TAU)
        season = tt
        sky_top = mix("#0E1838", "#6FA8DC", day)
        sky_bot = mix("#24305A", mix("#FCE1B4", "#DCE3EA", season), day)
        vgrad(ctx, [(0, sky_top), (1, sky_bot)])
        ang = cyc * TAU
        sxp, syp = 960 + math.sin(ang) * 760, 760 - math.cos(ang) * 600
        glow(ctx, sxp, syp, 140, "#FFF2C2", 0.9 * day)
        setc(ctx, "#FFF2C2", day)
        circle(ctx, sxp, syp, 40)
        ctx.fill()
        mx, my = 960 - math.sin(ang) * 760, 760 + math.cos(ang) * 600
        setc(ctx, "#EEF2FF", 1 - day)
        circle(ctx, mx, my, 30)
        ctx.fill()
        stars(ctx, 41, 60, t, (1 - day) * 0.9)
        hills(ctx, 780, 30, 0.003, 0.6, mix("#7FA77C", "#C9D2D8", season))
        ground(ctx, 800, mix("#6E9A5A", "#E8EDF2", smooth(prog(season, 0.6, 1.0))), mix("#5A8048", "#C9D3DC", smooth(prog(season, 0.6, 1.0))))
        # tree changing seasons
        tx, ty = 1240, 820
        setc(ctx, "#5B3F2E")
        poly(ctx, [(tx - 22, ty), (tx - 10, ty - 300), (tx + 10, ty - 300), (tx + 22, ty)])
        ctx.fill()
        line(ctx, tx, ty - 220, tx - 120, ty - 330, "#5B3F2E", 14)
        line(ctx, tx, ty - 260, tx + 130, ty - 360, "#5B3F2E", 12)
        leaf_c = mix(mix("#5FA35A", "#E9B44C", smooth(prog(season, 0.15, 0.45))), "#C8642E", smooth(prog(season, 0.45, 0.7)))
        leaf_a = 1 - smooth(prog(season, 0.7, 0.9))
        rnd = random.Random(4)
        for _ in range(12):
            ox, oy = rnd.uniform(-190, 190), rnd.uniform(-480, -270)
            setc(ctx, shade(leaf_c, rnd.uniform(-0.12, 0.08)), leaf_a)
            circle(ctx, tx + ox, ty + oy, rnd.uniform(70, 110))
            ctx.fill()
        if season > 0.35:
            rnd = random.Random(9)
            for _ in range(40):
                x0, y0 = rnd.uniform(900, 1600), rnd.uniform(0, 600)
                y = 340 + (y0 + t * 140) % 520
                setc(ctx, leaf_c if season < 0.75 else "#FFFFFF", 0.85 * (season < 0.75 or 1))
                ellipse(ctx, x0 + math.sin(t * 2 + x0) * 30, y, 8, 5)
                ctx.fill()
        # bench + him
        setc(ctx, "#6B4A36")
        rrect(ctx, 700, 760, 420, 22, 6)
        ctx.fill()
        rrect(ctx, 700, 690, 420, 18, 6)
        ctx.fill()
        for bx in (730, 1070):
            ctx.rectangle(bx, 780, 16, 60)
        ctx.fill()
        person(ctx, 900, 840, 0.75, outfit="shirt", pose="hold", expr="tired" if tt < 0.7 else "calm", t=t, sit=True,
               look=(0.3, -0.3))
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a2)


# ======================================================== 4 return
@scene("return")
def return_(ctx, S):
    t, T = S.t, S.T
    op = ease_io(prog(t, 0.1, 1.2))
    vgrad(ctx, [(0, "#0D0F1A"), (1, "#171A2B")])
    dx, dy, dw, dh = 960, 860, 300, 560
    # light pouring through the doorway
    col = hexc("#FFD99A")
    g = cairo.LinearGradient(0, dy - dh, 0, H)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.0)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0.5 * op)
    ctx.set_source(g)
    poly(ctx, [(dx - dw / 2, dy), (dx + dw / 2, dy), (dx + 700, H), (dx - 700, H)])
    ctx.fill()
    glow(ctx, dx, dy - dh / 2, 900, "#FFD99A", 0.35 * op)
    setc(ctx, "#2A2420")
    ctx.rectangle(dx - dw / 2 - 24, dy - dh - 24, dw + 48, dh + 24)
    ctx.fill()
    setc(ctx, mix("#3A3028", "#FFF1CF", op))
    ctx.rectangle(dx - dw / 2, dy - dh, dw, dh)
    ctx.fill()
    # door leaf swinging
    leaf_w = dw * (1 - op * 0.82)
    setc(ctx, "#6B4A36")
    poly(ctx, [(dx - dw / 2, dy - dh), (dx - dw / 2 + leaf_w, dy - dh - op * 40), (dx - dw / 2 + leaf_w, dy + op * 40), (dx - dw / 2, dy)])
    ctx.fill()
    setc(ctx, "#E9C46A")
    circle(ctx, dx - dw / 2 + leaf_w - 24 * (1 - op), dy - dh / 2, 9)
    ctx.fill()
    particles(ctx, 6, 60, t, "#FFF1CF", 0.5 * op, area=(dx - 400, dy - dh, 800, dh + 200), vy=-15, vx=4)
    wp = prog(t, 0.7, T)
    s = lerp(0.55, 0.95, ease_out(wp, 2))
    y = lerp(dy, 1000, ease_out(wp, 2))
    a = smooth(prog(t, 0.55, 0.9))
    if a > 0:
        person(ctx, dx, y, s, outfit="jacket", pose=blend_pose("idle", "open", smooth(prog(t, T - 1.2, T - 0.4))),
               expr="smile" if t < T - 1.0 else "happy", t=t, walk=(t * 8 if wp < 0.95 else None), alpha=a)
        fill_rect(ctx, "#000000", alpha=0.4 * (1 - wp))


# ======================================================== 5 squeeze
@scene("squeeze")
def squeeze(ctx, S):
    t, T = S.t, S.T
    close = ease_out(prog(t, 0.0, 1.2), 2)
    hit = pulse(t, 1.0, 1.5) + 0.5 * pulse(t, 2.2, 2.6)
    ctx.save()
    sx, sy = shake(t, 14 * hit, 9)
    cam(ctx, 1.0, 960, 540, sx, sy)
    vgrad(ctx, [(0, "#1A1F2E"), (1, "#0E1220")])
    breathe = 18 * math.sin(t * 5) * prog(t, 1.2, 1.6)
    gap = lerp(1400, 560, close) + breathe
    lx = 960 - gap / 2
    rx = 960 + gap / 2
    # left: cool glossy monolith
    ctx.set_source(lin_grad(0, 0, lx, 0, [(0, "#14326E"), (1, "#2F6FD6")]))
    ctx.rectangle(-200, 60, lx + 200, 820)
    ctx.fill()
    for r in range(6):
        for q in range(5):
            x = lx - 120 - q * 130
            setc(ctx, "#6FA6FF", 0.25 - q * 0.03)
            rrect(ctx, x, 100 + r * 130, 100, 100, 10)
            ctx.fill()
    line(ctx, lx, 60, lx, 880, "#A9C8FF", 6, 0.8)
    # right: stacked copied discs
    ctx.set_source(lin_grad(rx, 0, W, 0, [(0, "#5A1620"), (1, "#24080C")]))
    ctx.rectangle(rx, 60, W - rx + 200, 820)
    ctx.fill()
    rnd = random.Random(3)
    for r in range(6):
        for q in range(5):
            x = rx + 80 + q * 130 + (r % 2) * 40
            y = 130 + r * 130
            spin = t * 3 + rnd.random() * 6
            setc(ctx, "#B8BCC8", 0.8)
            circle(ctx, x, y, 52)
            ctx.fill()
            ctx.set_source(lin_grad(x - 52, y - 52, x + 52, y + 52,
                                    [(0, "#FF9AA2"), (0.5 + 0.3 * math.sin(spin), "#9AD7FF"), (1, "#C6FFB0")]))
            circle(ctx, x, y, 48)
            ctx.fill()
            setc(ctx, "#24080C")
            circle(ctx, x, y, 12)
            ctx.fill()
    line(ctx, rx, 60, rx, 880, "#FF8A8A", 6, 0.8)
    # pressure chevrons
    for side in (-1, 1):
        for i in range(3):
            ph = (t * 1.6 + i / 3) % 1.0
            xx = (lx + 40 + ph * 80) if side < 0 else (rx - 40 - ph * 80)
            setc(ctx, "#FFFFFF", 0.5 * (1 - ph) * close)
            ctx.set_line_width(8)
            ctx.move_to(xx - side * 20, 440)
            ctx.line_to(xx, 470)
            ctx.line_to(xx - side * 20, 500)
            ctx.stroke()
    ground(ctx, 880, "#141828", "#0B0E18")
    doc_icon(ctx, 960, 650, 0.85, glow_a=0.25)
    person(ctx, 960, 900, 0.78, outfit="jacket", pose=blend_pose("idle", "push", ease_out(prog(t, 0.6, 1.1))),
           expr="determined" if t < 1.0 else "fierce", t=t, sweat=prog(t, 1.2, 1.8))
    ctx.restore()


# ======================================================== 5 feed
@papered(0.9)
def app_icon(ctx, x, y, s, kind, col):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    setc(ctx, "#000000", 0.25)
    rrect(ctx, -62, -54, 128, 128, 30)
    ctx.fill()
    setc(ctx, col)
    rrect(ctx, -64, -64, 128, 128, 30)
    ctx.fill()
    setc(ctx, "#FFFFFF")
    if kind == "book":
        rrect(ctx, -36, -34, 34, 68, 5)
        rrect(ctx, 2, -34, 34, 68, 5)
        ctx.fill()
    elif kind == "shield":
        ctx.move_to(0, -40)
        ctx.line_to(34, -26)
        ctx.curve_to(34, 10, 18, 30, 0, 42)
        ctx.curve_to(-18, 30, -34, 10, -34, -26)
        ctx.close_path()
        ctx.fill()
    elif kind == "game":
        rrect(ctx, -44, -22, 88, 46, 22)
        ctx.fill()
        setc(ctx, col)
        ctx.rectangle(-30, -4, 22, 8)
        ctx.rectangle(-23, -11, 8, 22)
        ctx.fill()
        circle(ctx, 22, -4, 6)
        circle(ctx, 32, 6, 6)
        ctx.fill()
    elif kind == "chat":
        rrect(ctx, -40, -34, 56, 40, 12)
        ctx.fill()
        setc(ctx, "#FFFFFF", 0.7)
        rrect(ctx, -12, -6, 54, 40, 12)
        ctx.fill()
    ctx.restore()


@scene("feed")
def feed(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#1B2346"), (1, "#0F1430")])
    glow(ctx, 1100, 480, 700, "#3A64C8", 0.25)
    cx, cy = 1120, 470
    icons = [("book", "#E76F51"), ("shield", "#2A9D8F"), ("game", "#8A5CF6"), ("chat", "#E9A23B")]
    fed = prog(t, 0.6, T)
    for i, (kind, col) in enumerate(icons):
        a = -math.pi * 0.95 + i * (math.pi * 0.9 / 3) + 0.05 * math.sin(t + i)
        ix, iy = cx + math.cos(a) * 400, cy + 40 + math.sin(a) * 300 + 260
        ix, iy = cx + (i - 1.5) * 260, 800 + math.sin(t * 2 + i) * 10
        pop = ease_back(prog(t, 0.1 + i * 0.12, 0.5 + i * 0.12))
        if pop <= 0:
            continue
        # coin stream along curve into the document
        rnd = random.Random(i)
        for j in range(10):
            ph = (t * 0.9 + j / 10 + rnd.random() * 0.05) % 1.0
            if t < 0.6:
                break
            bx = (1 - ph) ** 2 * ix + 2 * (1 - ph) * ph * (ix + (cx - ix) * 0.2) + ph * ph * cx
            by = (1 - ph) ** 2 * (iy - 60) + 2 * (1 - ph) * ph * (iy - 300) + ph * ph * (cy + 40)
            glow(ctx, bx, by, 26, "#FFD27A", 0.5)
            setc(ctx, "#FFD27A")
            ellipse(ctx, bx, by, 12 * abs(math.cos(t * 6 + j)) + 3, 12)
            ctx.fill()
        app_icon(ctx, ix, iy, 0.85 * pop, kind, col)
    doc_icon(ctx, cx, cy, 1.0 + 0.18 * ease_out(fed) + 0.03 * math.sin(t * 6), glow_a=0.3 + 0.5 * fed)
    person(ctx, 380, 900, 0.85, outfit="jacket", pose="pointL" if False else "point", expr="smile", t=t, look=(0.8, -0.2))


# ======================================================== 5 bubble: 把 WPS 进行到底
def speech_bubble(ctx, text, x, y, tail_to, t_in, size=74, max_w=None):
    """Folded paper speech card with a cut-paper tail."""
    p = spring(t_in, 1.6, 6.0)
    if t_in <= 0:
        return
    font(ctx, size, SANS, True)
    tw = text_width(ctx, text)
    bw, bh = tw + size * 1.3, size * 1.9
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(p, 0.01), max(p, 0.01))
    ctx.rotate(-0.03 + 0.015 * math.sin(t_in * 2))
    tx, ty = tail_to[0] - x, tail_to[1] - y
    ang = math.atan2(ty, tx)
    px, py = -math.sin(ang) * 40, math.cos(ang) * 40
    ctx.push_group()
    setc(ctx, "#E6DCC8")
    poly(ctx, [(px * 0.2, py * 0.2), (tx * 0.6, ty * 0.6), (-px, -py)])
    ctx.fill()
    setc(ctx, "#FFFDF6")
    poly(ctx, [(px, py), (tx * 0.6, ty * 0.6), (px * 0.2, py * 0.2)])
    ctx.fill()
    # card: folded horizontally, top half lit, bottom half slightly shaded
    c = 26
    pts = [(-bw / 2 + c, -bh / 2), (bw / 2 - c, -bh / 2), (bw / 2, -bh / 2 + c), (bw / 2, bh / 2 - c),
           (bw / 2 - c, bh / 2), (-bw / 2 + c, bh / 2), (-bw / 2, bh / 2 - c), (-bw / 2, -bh / 2 + c)]
    setc(ctx, "#FFFDF6")
    poly(ctx, pts)
    ctx.fill()
    setc(ctx, "#EFE6D4")
    poly(ctx, [(-bw / 2, 4), (bw / 2, 4), (bw / 2, bh / 2 - c), (bw / 2 - c, bh / 2), (-bw / 2 + c, bh / 2),
               (-bw / 2, bh / 2 - c)])
    ctx.fill()
    setc(ctx, "#D9CDB5")
    poly(ctx, [(bw / 2 - c, -bh / 2), (bw / 2, -bh / 2 + c), (bw / 2 - c, -bh / 2 + c)])
    ctx.fill()
    pat = ctx.pop_group()
    drop_shadow(ctx, pat, 1.3, 0.45)
    ctx.set_source(pat)
    ctx.paint()
    setc(ctx, "#C8402E", 0.55)
    ctx.move_to(-tw / 2 + 3, size * 0.36 + 3)
    ctx.show_text(text)
    setc(ctx, "#1A1D29")
    ctx.move_to(-tw / 2, size * 0.36)
    ctx.show_text(text)
    ctx.restore()


def comic_bg(ctx, t, c1, c2, ray_c, cx=760, cy=420):
    vgrad(ctx, [(0, c1), (1, c2)])
    light_rays(ctx, cx, cy, 18, 1600, ray_c, 0.16, t, rot=t * 0.2, width=0.09)
    rnd = random.Random(1)
    for i in range(46):
        a = rnd.uniform(0, TAU)
        r0 = rnd.uniform(500, 800)
        ph = (t * 1.5 + rnd.random()) % 1.0
        r = r0 + ph * 500
        line(ctx, cx + math.cos(a) * r, cy + math.sin(a) * r, cx + math.cos(a) * (r + 120), cy + math.sin(a) * (r + 120),
             "#FFFFFF", 4, 0.25 * (1 - ph))


@scene("bubble_wps")
def bubble_wps(ctx, S):
    t, T = S.t, S.T
    ctx.save()
    cam(ctx, 1.0 + 0.04 * t / T, 960, 540)
    comic_bg(ctx, t, "#F08A3C", "#C2452F", "#FFE3A3")
    doc_icon(ctx, 1480, 760, 1.2, glow_a=0.4, t=t)
    q = ease_back(prog(t, 0.15, 0.6))
    info = person(ctx, 720, 1170, 1.7, outfit="jacket", pose=blend_pose("idle", "fist_up", q),
                  expr="fierce" if t < 0.4 else "shout", t=t, look=(0.4, -0.2))
    ctx.restore()
    hx, hy = ctx.device_to_user(*info["head"])
    fade = 1 - prog(t, T - 0.4, T - 0.08)
    if fade > 0:
        ctx.push_group()
        speech_bubble(ctx, "把 WPS 进行到底", 1250, 250, (hx + 120, hy - 60), t - 0.35)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade)


# ======================================================== 5 mountain (quote)
@scene("mountain")
def mountain(ctx, S):
    t, T = S.t, S.T
    ctx.save()
    cam(ctx, 1.0 + 0.05 * t / T, 900, 560)
    vgrad(ctx, [(0, "#1B1F4A"), (0.6, "#7C5A8C"), (1, "#F2A27A")])
    stars(ctx, 51, 60, t, 0.6, y_max=380)
    # the high peak (志存高远)
    def peaks():
        facet_mountain(ctx, (780, 900), (980, 380), (1300, 900), "#34336A")
        facet_mountain(ctx, (-100, 900), (520, 150), (1000, 900), "#2B2C55")
        setc(ctx, "#F4F1FA")
        poly(ctx, [(520, 150), (450, 240), (500, 228), (520, 262)])
        ctx.fill()
        setc(ctx, "#C9C4DE")
        poly(ctx, [(520, 150), (520, 262), (560, 232), (604, 252)])
        ctx.fill()
    paper(ctx, peaks, 1.2, 0.35)
    sg = 0.6 + 0.4 * math.sin(t * 3)
    glow(ctx, 520, 90, 160, "#FFE6A0", 0.6 * sg)
    setc(ctx, "#FFE6A0")
    star_shape(ctx, 520, 90, 26 + 4 * sg)
    ctx.fill()
    # the easy river (顺势而为) going downhill to the right
    hills(ctx, 760, 40, 0.004, 3.0, "#3E3A66")
    setc(ctx, "#2F6E8E")
    ctx.move_to(980, 900)
    ctx.curve_to(1200, 800, 1500, 760, W + 50, 720)
    ctx.line_to(W + 50, 860)
    ctx.curve_to(1600, 880, 1300, 930, 1100, 1000)
    ctx.close_path()
    ctx.fill()
    for i in range(14):
        ph = (t * 0.5 + i / 14) % 1.0
        x = lerp(1050, 1900, ph)
        y = lerp(930, 770, ph) + math.sin(i) * 20
        line(ctx, x, y, x + 60, y - 10, "#9ED8FF", 4, 0.6 * math.sin(ph * math.pi))
    ground(ctx, 900, "#1E1C3A", "#141228")
    # paths from the fork
    fork = (960, 930)
    climb = [fork, (820, 860), (900, 780), (760, 700), (840, 620), (700, 520), (640, 400), (560, 260)]
    setc(ctx, "#5C5689")
    ctx.set_line_width(14)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*climb[0])
    for p in climb[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    setc(ctx, "#5C5689", 0.7)
    ctx.move_to(*fork)
    ctx.curve_to(1050, 920, 1100, 900, 1160, 880)
    ctx.stroke()
    # light travels up the chosen path
    lp = ease_io(prog(t, 1.2, T - 0.3))
    seglens = [math.dist(climb[i], climb[i + 1]) for i in range(len(climb) - 1)]
    total = sum(seglens)
    target = total * lp
    acc = 0
    pos = climb[0]
    ctx.set_line_width(8)
    setc(ctx, "#FFD27A")
    ctx.move_to(*climb[0])
    for i, L in enumerate(seglens):
        if acc + L >= target:
            f = (target - acc) / L if L else 0
            pos = (lerp(climb[i][0], climb[i + 1][0], f), lerp(climb[i][1], climb[i + 1][1], f))
            ctx.line_to(*pos)
            break
        ctx.line_to(*climb[i + 1])
        acc += L
        pos = climb[i + 1]
    ctx.stroke()
    glow(ctx, pos[0], pos[1], 60, "#FFD27A", 0.8)
    cp = prog(t, 1.2, T - 0.3)
    s = lerp(0.42, 0.22, ease_io(cp))
    ppos = pos if lp > 0 else fork
    person(ctx, ppos[0], ppos[1] + 6, s, outfit="jacket", pose="idle", expr="determined", t=t,
           facing="back" if t > 1.0 else "front", walk=(t * 9 if 0 < cp < 1 else None))
    ctx.restore()


# ======================================================== 6 joyo
@scene("joyo")
def joyo(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#FFF1DC"), (1, "#F6D7B0")])
    for i in range(6):
        setc(ctx, "#FFFFFF", 0.35)
        circle(ctx, 200 + i * 330, 160 + (i % 2) * 90, 90 + i * 10)
        ctx.fill()
    pop = ease_back(prog(t, 0.0, 0.5))
    bx, by, bw, bh = 760, 130, 1000, 640
    ctx.save()
    ctx.translate(bx + bw / 2, by + bh / 2)
    ctx.scale(pop, pop)
    ctx.translate(-(bx + bw / 2), -(by + bh / 2))
    setc(ctx, "#000000", 0.12)
    rrect(ctx, bx + 16, by + 22, bw, bh, 26)
    ctx.fill()
    setc(ctx, "#FFFFFF")
    rrect(ctx, bx, by, bw, bh, 26)
    ctx.fill()
    setc(ctx, "#2E4057")
    rrect(ctx, bx, by, bw, 70, 26)
    ctx.rectangle(bx, by + 40, bw, 30)
    ctx.fill()
    for i, c in enumerate(("#FF6B6B", "#FFD93D", "#6BCB77")):
        setc(ctx, c)
        circle(ctx, bx + 40 + i * 34, by + 35, 11)
        ctx.fill()
    setc(ctx, "#4E6380")
    rrect(ctx, bx + 160, by + 18, 600, 34, 17)
    ctx.fill()
    # cart icon
    setc(ctx, "#F6B64A")
    ctx.set_line_width(6)
    ctx.move_to(bx + bw - 110, by + 22)
    ctx.line_to(bx + bw - 96, by + 22)
    ctx.line_to(bx + bw - 86, by + 48)
    ctx.line_to(bx + bw - 54, by + 48)
    ctx.line_to(bx + bw - 48, by + 30)
    ctx.stroke()
    circle(ctx, bx + bw - 84, by + 56, 4)
    circle(ctx, bx + bw - 58, by + 56, 4)
    ctx.fill()
    cols = ["#E76F51", "#2A9D8F", "#457B9D", "#E9C46A", "#8A5CF6", "#F4A261", "#6BCB77", "#EF476F"]
    for i in range(8):
        r, q = i // 4, i % 4
        a = ease_back(prog(t, 0.35 + i * 0.12, 0.65 + i * 0.12))
        if a <= 0:
            continue
        cx = bx + 70 + q * 230 + 90
        cy = by + 130 + r * 250 + 90
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(a, a)
        setc(ctx, "#F3F5F9")
        rrect(ctx, -95, -95, 190, 210, 16)
        ctx.fill()
        if i % 3 == 2:
            setc(ctx, "#C8CDD8")
            circle(ctx, 0, -10, 56)
            ctx.fill()
            ctx.set_source(lin_grad(-56, -66, 56, 46, [(0, "#FF9AA2"), (0.5, "#9AD7FF"), (1, "#C6FFB0")]))
            circle(ctx, 0, -10, 50)
            ctx.fill()
            setc(ctx, "#F3F5F9")
            circle(ctx, 0, -10, 12)
            ctx.fill()
        else:
            setc(ctx, cols[i])
            rrect(ctx, -46, -74, 92, 128, 6)
            ctx.fill()
            setc(ctx, "#FFFFFF", 0.7)
            ctx.rectangle(-30, -50, 60, 8)
            ctx.rectangle(-30, -34, 40, 6)
            ctx.fill()
        setc(ctx, "#D7DCE6")
        rrect(ctx, -70, 76, 100, 12, 6)
        ctx.fill()
        setc(ctx, "#F6B64A")
        rrect(ctx, 40, 72, 40, 20, 10)
        ctx.fill()
        ctx.restore()
    ctx.restore()
    # parcels flying out
    rnd = random.Random(4)
    for i in range(6):
        ph = (t * 0.6 + i / 6) % 1.0
        if t < 1.0:
            break
        x = lerp(bx + bw - 60, W + 120, ph)
        y = lerp(by + 300 + rnd.uniform(-100, 200), by + 100 + rnd.uniform(-60, 120), ph) - math.sin(ph * math.pi) * 120
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
    ground(ctx, 880, "#E8C49A", "#D9AE7E")
    person(ctx, 420, 900, 0.88, outfit="jacket", pose=blend_pose("idle", "point", ease_out(prog(t, 0.3, 0.8))),
           expr="happy", t=t, look=(0.8, -0.3))


# ======================================================== 6 thirty doors
@scene("doors")
def doors(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#232A3E"), (1, "#141826")])
    glow(ctx, 650, 420, 800, "#4A5A8C", 0.2)
    cols, rows = 6, 5
    dw, dh, gx, gy = 112, 132, 32, 22
    x0, y0 = 220, 70
    seq_start, seq_end = 0.25, T - 0.6
    n = cols * rows
    for i in range(n):
        r, q = i // cols, i % cols
        x, y = x0 + q * (dw + gx), y0 + r * (dh + gy)
        ti = lerp(seq_start, seq_end, (i / n) ** 0.85)
        p = (t - ti) / 0.22
        setc(ctx, "#3A4362")
        rrect(ctx, x - 8, y - 8, dw + 16, dh + 12, 6)
        ctx.fill()
        if p < 0:
            setc(ctx, "#6A5242")
            rrect(ctx, x, y, dw, dh, 4)
            ctx.fill()
            setc(ctx, "#E9C46A")
            circle(ctx, x + dw - 18, y + dh / 2, 6)
            ctx.fill()
        else:
            open_ = pulse(p, 0, 1.0)
            if open_ > 0:
                glow(ctx, x + dw / 2, y + dh / 2, 120, "#FFD99A", 0.5 * open_)
                setc(ctx, "#FFE8B8", open_)
                ctx.rectangle(x, y, dw, dh)
                ctx.fill()
            setc(ctx, mix("#6A5242", "#3E3330", clamp(p - 0.8)))
            lw = dw * (1 - 0.7 * open_)
            ctx.rectangle(x, y, lw, dh)
            ctx.fill()
            if p > 0.9:
                xa = ease_back(clamp((p - 0.9) * 3))
                setc(ctx, "#E2504C", 0.9)
                ctx.set_line_width(9)
                cx, cy = x + dw / 2, y + dh / 2
                d = 34 * xa
                ctx.move_to(cx - d, cy - d)
                ctx.line_to(cx + d, cy + d)
                ctx.move_to(cx + d, cy - d)
                ctx.line_to(cx - d, cy + d)
                ctx.stroke()
    ground(ctx, 880, "#141826", "#0C0F18")
    pr = prog(t, seq_start, seq_end)
    person(ctx, 1450, 900, 0.88, outfit="jacket",
           pose=blend_pose("hold", "sad", smooth(prog(pr, 0.5, 1.0))),
           expr=blend_expr("determined", "sad", smooth(prog(pr, 0.3, 0.95))), t=t,
           look=(-0.9, lerp(-0.2, 0.4, pr)), tilt=-0.08 * pr)
    fill_rect(ctx, "#000000", alpha=0.25 * pr)


# ======================================================== 6 balloon (selling it)
@papered(0.9)
def mini_site(ctx, x, y, s, rot):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.scale(s, s)
    setc(ctx, "#FFFFFF")
    rrect(ctx, -90, -64, 180, 128, 16)
    ctx.fill()
    setc(ctx, "#2E4057")
    rrect(ctx, -90, -64, 180, 30, 16)
    ctx.rectangle(-90, -48, 180, 14)
    ctx.fill()
    for i, c in enumerate(("#E76F51", "#2A9D8F", "#E9C46A")):
        setc(ctx, c)
        rrect(ctx, -70 + i * 50, -20, 40, 66, 5)
        ctx.fill()
    ctx.restore()


@scene("balloon")
def balloon(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#3B2C5E"), (0.55, "#B0627A"), (1, "#F4A66A")])
    glow(ctx, 1400, 760, 420, "#FFC27A", 0.7)
    setc(ctx, "#FFD7A0")
    circle(ctx, 1400, 780, 90)
    ctx.fill()
    for i in range(4):
        cx = (300 + i * 520 + t * 20) % (W + 400) - 200
        setc(ctx, "#FFFFFF", 0.18)
        ellipse(ctx, cx, 220 + i * 50, 160, 34)
        ctx.fill()
    hills(ctx, 840, 50, 0.003, 2.0, "#4A2E50")
    ground(ctx, 870, "#3A2340", "#24152A")
    release = T * 0.28
    rp = ease_in(prog(t, release, T), 1.6)
    hx0, hy0 = 1080, 590
    bx = hx0 + lerp(-20, -620, rp) + math.sin(t * 1.4) * 20
    by = hy0 - 160 - rp * 900
    for j, (ox, c) in enumerate(((-50, "#EF476F"), (0, "#FFD166"), (50, "#06D6A0"))):
        ex, ey = bx + ox * 1.2, by - 230 - abs(ox) * 0.4
        line(ctx, bx, by - 60, ex, ey + 60, "#FFFFFF", 2, 0.8)
        setc(ctx, c)
        ellipse(ctx, ex, ey, 52, 64)
        ctx.fill()
        setc(ctx, "#FFFFFF", 0.35)
        ellipse(ctx, ex - 16, ey - 22, 12, 18)
        ctx.fill()
    mini_site(ctx, bx, by, 0.9, math.sin(t * 1.2) * 0.08)
    if rp <= 0:
        line(ctx, bx, by + 58, hx0, hy0, "#FFFFFF", 2, 0.8)
    else:
        sway = math.sin(t * 3) * 30
        ctx.set_line_width(2)
        setc(ctx, "#FFFFFF", 0.8)
        ctx.move_to(bx, by + 58)
        ctx.curve_to(bx + sway, by + 140, bx - sway, by + 200, bx + sway * 0.5, by + 260)
        ctx.stroke()
    pose = "reach" if t < release else blend_pose("reach", "reach2", ease_out(prog(t, release, release + 0.5)))
    if t > release + 1.8:
        pose = blend_pose("reach2", "sad", smooth(prog(t, release + 1.8, release + 2.6)))
    expr = "calm" if t < release else ("shock" if t < release + 0.6 else "sad")
    person(ctx, 1080, 900, 0.85, outfit="jacket", pose=pose, expr=expr, t=t, look=(-0.6, -1.0))
    for i in range(3):
        bxp = (t * 120 + i * 300) % (W + 200) - 100
        byp = 330 + i * 40 + math.sin(t * 2 + i) * 10
        setc(ctx, "#2A1A30")
        ctx.set_line_width(4)
        w_ = math.sin(t * 9 + i) * 8
        ctx.move_to(bxp - 18, byp - w_)
        ctx.line_to(bxp, byp)
        ctx.line_to(bxp + 18, byp - w_)
        ctx.stroke()
