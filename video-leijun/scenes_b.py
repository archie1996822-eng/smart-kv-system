"""Scenes for segments 7–12 (转折 → 收尾)."""
import math
import random

import cairo

from gfx import (W, H, TAU, clamp, lerp, prog, smooth, ease_out, ease_in, ease_io, ease_back,
                 spring, pulse, noise1, hexc, mix, shade, setc, rrect, circle, ellipse, fill_rect,
                 lin_grad, vgrad, glow, line, poly, star_shape, stars, skyline, particles, hills,
                 light_rays, spotlight, confetti,
                 drop_shadow, paper, papered, fold_poly, facet_mountain)
from character import person, silhouette, blend_pose, blend_expr
from scenes_a import REG, scene, cam, shake, item_t, speech_bubble, comic_bg, ground, bulb


# ======================================================== 7 think (2006)
@scene("think")
def think(ctx, S):
    t, T = S.t, S.T
    idea = T * 0.68
    ip = prog(t, idea, idea + 0.5)
    vgrad(ctx, [(0, mix("#10142A", "#2A2340", ip)), (1, mix("#191C33", "#3A2A3A", ip))])
    # window with moon
    setc(ctx, "#0A0D1E")
    rrect(ctx, 1320, 140, 420, 340, 12)
    ctx.fill()
    ctx.save()
    rrect(ctx, 1320, 140, 420, 340, 12)
    ctx.clip()
    stars(ctx, 61, 40, t, 0.8)
    setc(ctx, "#F1F4FF")
    circle(ctx, 1640, 230, 40)
    ctx.fill()
    ctx.restore()
    setc(ctx, "#2B2A44")
    ctx.set_line_width(14)
    rrect(ctx, 1320, 140, 420, 340, 12)
    ctx.stroke()
    line(ctx, 1530, 140, 1530, 480, "#2B2A44", 10)
    # lamp cone
    spotlight(ctx, 620, 430, 760, 720, 20, 260, "#FFD99A", 0.22)
    setc(ctx, "#3C3A52")
    line(ctx, 560, 720, 590, 460, "#3C3A52", 8)
    poly(ctx, [(560, 470), (680, 420), (690, 450), (580, 500)])
    ctx.fill()
    # him seated, thinking
    pose = "think" if t < idea else blend_pose("think", "wave", ease_back(ip))
    expr = "calm" if t < idea * 0.5 else ("worried" if t < idea else "happy")
    info = person(ctx, 960, 880, 0.9, outfit="jacket", pose=pose, expr=expr, t=t, sit=True,
                  look=(0.5, -0.8) if t < idea else (0.0, -0.2), tilt=0.06 if t < idea else 0.0, hair_grey=0.05)
    # desk
    setc(ctx, "#5A3D2E")
    rrect(ctx, 420, 720, 1080, 30, 8)
    ctx.fill()
    setc(ctx, "#43302A")
    ctx.rectangle(450, 750, 1020, 200)
    ctx.fill()
    hx, hy = ctx.device_to_user(*info["head"])
    bx, by = hx, hy - 230
    # thought particles converge into a bulb
    rnd = random.Random(7)
    conv = ease_in(prog(t, 0.6, idea), 2)
    pts = []
    for i in range(26):
        a0 = rnd.uniform(0, TAU)
        r0 = rnd.uniform(160, 420)
        a = a0 + t * rnd.uniform(0.3, 0.8)
        r = r0 * (1 - conv)
        pts.append((bx + math.cos(a) * r, by + math.sin(a) * r * 0.6))
    if ip < 1:
        for i in range(len(pts) - 1):
            if i % 3 != 2:
                line(ctx, *pts[i], *pts[i + 1], "#9FB4FF", 1.5, 0.35 * (1 - ip) * prog(t, 0.3, 1.0))
        for p in pts:
            setc(ctx, "#C9D6FF", 0.8 * (1 - ip) * prog(t, 0.3, 1.0))
            circle(ctx, p[0], p[1], 4)
            ctx.fill()
    if t > idea:
        s = ease_back(prog(t, idea, idea + 0.4))
        glow(ctx, bx, by, 420 * s, "#FFD27A", 0.6)
        light_rays(ctx, bx, by, 14, 380 * s, "#FFE7A8", 0.22, t, rot=t * 0.3)
        setc(ctx, "#FFE9A8")
        circle(ctx, bx, by, 46 * s)
        ctx.fill()
        setc(ctx, "#B0B0BA")
        rrect(ctx, bx - 20 * s, by + 38 * s, 40 * s, 26 * s, 5)
        ctx.fill()


# ======================================================== 7 river: 勤奋远远不够 → 顺势而为
@scene("river")
def river(ctx, S):
    t, T = S.t, S.T
    t1 = S.items[1][0] if len(S.items) > 1 else 1e9
    turn = smooth(prog(t, t1 - 0.2, t1 + 0.8))
    sail = ease_back(prog(t, t1 + 0.1, t1 + 0.7))
    ctx.save()
    cam(ctx, 1.0 + 0.04 * turn, 960, 540)
    vgrad(ctx, [(0, mix("#5B6B86", "#F7B65A", turn)), (0.7, mix("#9AA8BC", "#FFE0A6", turn)), (1, mix("#B7C2CF", "#FFF0CF", turn))])
    if turn > 0:
        glow(ctx, 1500, 260, 600, "#FFF4D0", 0.7 * turn)
    hills(ctx, 560, 70, 0.0025, 1.4, mix("#6D7A92", "#C98A5A", turn))
    hills(ctx, 610, 50, 0.004, 0.2, mix("#55637C", "#A86B48", turn))
    # water
    ctx.set_source(lin_grad(0, 600, 0, H, [(0, mix("#3D5C7A", "#3F8FB0", turn)), (1, mix("#24384E", "#22607E", turn))]))
    ctx.rectangle(0, 600, W, H)
    ctx.fill()
    # current: strongly left before, rightwards after
    dir_ = lerp(-1.0, 1.4, turn)
    rnd = random.Random(5)
    phase_shift = -t * 520 if t < t1 else -t1 * 520 + (t - t1) * 700 * turn
    for i in range(46):
        y = rnd.uniform(620, 1060)
        x0 = rnd.uniform(0, W + 300)
        ln = rnd.uniform(60, 180)
        x = (x0 + phase_shift * (0.6 + (y - 600) / 900)) % (W + 300) - 150
        line(ctx, x, y, x + ln, y, "#D6EEFF", 3, 0.35)
    # wind lines after the turn
    if turn > 0:
        for i in range(10):
            ph = (t * 0.9 + i / 10) % 1.0
            y = 200 + i * 38
            x = lerp(-300, W + 300, ph)
            setc(ctx, "#FFFFFF", 0.5 * turn * math.sin(ph * math.pi))
            ctx.set_line_width(4)
            ctx.move_to(x, y)
            ctx.curve_to(x + 120, y - 30, x + 240, y + 30, x + 380, y)
            ctx.stroke()
    # boat
    struggle = 1 - turn
    bx = 820 + math.sin(t * 2.6) * 12 * struggle - 30 * prog(t, 0, t1) + ease_in(prog(t, t1 + 0.3, T + 0.5), 2) * 900
    by = 800 + math.sin(t * 2.2) * 6
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(math.sin(t * 2.2) * 0.03 - 0.04 * turn)
    if sail > 0:
        line(ctx, 0, -40, 0, -40 - 330 * sail, "#5A3D2E", 10)
        setc(ctx, "#FFF3DE")
        ctx.move_to(8, -60)
        ctx.curve_to(130 * sail + 40, -160 * sail, 140 * sail + 40, -250 * sail, 8, -350 * sail)
        ctx.close_path()
        ctx.fill()
        setc(ctx, "#F6B64A")
        ctx.move_to(-8, -80)
        ctx.curve_to(-50 * sail, -160 * sail, -60 * sail, -240 * sail, -8, -320 * sail)
        ctx.close_path()
        ctx.fill()
    ctx.restore()
    row = math.sin(t * 7) if turn < 0.5 else 0.0
    pose = (0.5 + 0.5 * row, -1.4 + 0.5 * row, 0.5 + 0.5 * row, -1.4 + 0.5 * row) if turn < 0.5 else blend_pose("type", "open", turn)
    person(ctx, bx - 40, by + 10, 0.62, outfit="jacket", pose=pose, expr="worried" if turn < 0.5 else "happy",
           t=t, sit=True, sweat=0.9 * struggle, look=(0.8, 0) if turn < 0.5 else (0.6, -0.5))
    if turn < 0.5 and row > 0:
        line(ctx, bx - 120, by - 120, bx - 260 - row * 60, by + 40, "#6B4A36", 9)
    ctx.save()
    ctx.translate(bx, by)
    ctx.rotate(math.sin(t * 2.2) * 0.03 - 0.04 * turn)
    setc(ctx, "#8B5A3C")
    ctx.move_to(-220, -10)
    ctx.line_to(220, -10)
    ctx.curve_to(200, 50, 140, 70, 100, 70)
    ctx.line_to(-120, 70)
    ctx.curve_to(-170, 70, -210, 40, -220, -10)
    ctx.close_path()
    ctx.fill()
    setc(ctx, "#6B4430")
    ctx.rectangle(-220, -12, 440, 14)
    ctx.fill()
    ctx.restore()
    # spray behind boat after turn
    if turn > 0.3:
        for i in range(12):
            ph = (t * 2 + i / 12) % 1.0
            setc(ctx, "#FFFFFF", 0.6 * (1 - ph) * turn)
            circle(ctx, bx - 240 - ph * 200, by + 50 - math.sin(ph * math.pi) * 40, 6 * (1 - ph) + 2)
            ctx.fill()
        for i in range(4):
            xx = (t * 160 + i * 400) % (W + 200) - 100
            yy = 260 + i * 50 + math.sin(t * 2 + i) * 15
            w_ = math.sin(t * 9 + i) * 8
            setc(ctx, "#4A3A2A", turn)
            ctx.set_line_width(4)
            ctx.move_to(xx - 18, yy - w_)
            ctx.line_to(xx, yy)
            ctx.line_to(xx + 18, yy - w_)
            ctx.stroke()
    ctx.restore()


# ======================================================== 8 rings (16 years)
@scene("rings")
def rings(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#3A2A22"), (1, "#1E1612")])
    glow(ctx, 860, 500, 700, "#FFC27A", 0.15)
    cx, cy = 860, 470
    R = 400
    setc(ctx, "#6B4630")
    ellipse(ctx, cx, cy + 22, R + 26, R + 18)
    ctx.fill()
    setc(ctx, "#E8C291")
    ellipse(ctx, cx, cy, R, R)
    ctx.fill()
    n = 16
    rp = prog(t, 0.1, T - 0.5) * n
    for i in range(n):
        a = clamp(rp - i)
        if a <= 0:
            continue
        r = (i + 1) / n * (R - 18)
        setc(ctx, "#B9875A", a)
        ctx.set_line_width(5 if i % 4 != 3 else 8)
        ctx.new_path()
        for j in range(73):
            ang = j / 72 * TAU
            wob = 1 + 0.015 * math.sin(ang * 3 + i) + 0.01 * math.sin(ang * 7 + i * 2)
            px, py = cx + math.cos(ang) * r * wob, cy + math.sin(ang) * r * wob
            if j == 0:
                ctx.move_to(px, py)
            else:
                ctx.line_to(px, py)
        ctx.close_path()
        ctx.stroke()
        if 0 < rp - i < 1:
            glow(ctx, cx + r, cy, 40, "#FFE6B0", 0.6 * (1 - a))
    setc(ctx, "#9A6A44")
    circle(ctx, cx, cy, 12)
    ctx.fill()
    rnd = random.Random(2)
    for _ in range(18):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        y = (y0 + t * 80) % (H + 100) - 50
        ctx.save()
        ctx.translate(x0 + math.sin(t + x0) * 30, y)
        ctx.rotate(t + x0)
        setc(ctx, rnd.choice(["#E9A23B", "#C8642E", "#E76F51"]), 0.8)
        ellipse(ctx, 0, 0, 12, 6)
        ctx.fill()
        ctx.restore()
    person(ctx, 1520, 900, 0.78, outfit="jacket", pose="pocket", expr="calm", t=t, hair_grey=0.12, look=(-0.8, -0.1))


# ======================================================== 9 forty (2010)
@scene("forty")
def forty(ctx, S):
    t, T = S.t, S.T
    dawn = smooth(prog(t, 0.0, T))
    vgrad(ctx, [(0, mix("#2B2A44", "#4B3B4F", dawn)), (1, mix("#1E1D30", "#2F2533", dawn))])
    wx, wy, ww, wh = 1180, 260, 520, 400
    ctx.save()
    rrect(ctx, wx, wy, ww, wh, 10)
    ctx.clip()
    vgrad(ctx, [(0, mix("#203060", "#F08A5D", dawn)), (1, mix("#5A4A6A", "#FFD99A", dawn))], wx, wy, ww, wh)
    glow(ctx, wx + ww / 2, wy + wh - 40 * dawn, 260, "#FFE6B0", 0.9 * dawn)
    skyline(ctx, 5, wy + wh, "#2A2238", None, hmin=40, hmax=160, x0=wx, x1=wx + ww, wmin=50, wmax=110)
    ctx.restore()
    setc(ctx, "#1A1726")
    ctx.set_line_width(16)
    rrect(ctx, wx, wy, ww, wh, 10)
    ctx.stroke()
    line(ctx, wx + ww / 2, wy, wx + ww / 2, wy + wh, "#1A1726", 10)
    # light beam into the room
    col = hexc("#FFD99A")
    g = cairo.LinearGradient(wx, wy, 700, H)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], 0.28 * dawn)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0.0)
    ctx.set_source(g)
    poly(ctx, [(wx, wy), (wx + ww, wy + wh), (900, H), (200, H)])
    ctx.fill()
    ground(ctx, 870, "#2A2232", "#1A1520")
    # small desk with a steaming bowl
    setc(ctx, "#5A3D2E")
    rrect(ctx, 880, 700, 300, 22, 6)
    ctx.fill()
    ctx.rectangle(900, 722, 16, 160)
    ctx.rectangle(1144, 722, 16, 160)
    ctx.fill()
    setc(ctx, "#F2EDE4")
    ctx.arc(1030, 680, 46, 0, math.pi)
    ctx.close_path()
    ctx.fill()
    setc(ctx, "#E9C46A")
    ellipse(ctx, 1030, 682, 44, 8)
    ctx.fill()
    for i in range(3):
        ph = (t * 0.5 + i / 3) % 1.0
        setc(ctx, "#FFFFFF", 0.35 * math.sin(ph * math.pi))
        ctx.set_line_width(5)
        ctx.move_to(1010 + i * 20, 660 - ph * 120)
        ctx.curve_to(1000 + i * 20, 640 - ph * 120, 1030 + i * 20, 620 - ph * 120, 1015 + i * 20, 600 - ph * 120)
        ctx.stroke()
    person(ctx, 520, 900, 0.95, outfit="sweater", pose="pocket", expr="calm" if t < T * 0.5 else "smile", t=t,
           hair_grey=0.15, look=(0.8, -0.3))


# ======================================================== 9 summit (try once more)
@scene("summit")
def summit(ctx, S):
    t, T = S.t, S.T
    ctx.save()
    cam(ctx, 1.0 + 0.05 * t / T, 960, 560)
    vgrad(ctx, [(0, "#2E3F7A"), (0.6, "#E28B6A"), (1, "#FFD3A0")])
    stars(ctx, 81, 40, t, 0.5 * (1 - t / T), y_max=300)
    for i in range(4):
        cx = (200 + i * 560 + t * 25) % (W + 400) - 200
        setc(ctx, "#FFFFFF", 0.25)
        ellipse(ctx, cx, 300 + (i % 2) * 70, 200, 36)
        ctx.fill()
    def peaks():
        facet_mountain(ctx, (1300, 900), (1700, 260), (2200, 900), "#6A5888")
        facet_mountain(ctx, (700, 900), (1450, 230), (1950, 900), "#5B4A78")
        setc(ctx, "#F4EEF8")
        poly(ctx, [(1450, 230), (1395, 300), (1430, 292), (1452, 318)])
        ctx.fill()
        setc(ctx, "#CFC5DE")
        poly(ctx, [(1450, 230), (1452, 318), (1480, 296), (1515, 312)])
        ctx.fill()
    paper(ctx, peaks, 1.2, 0.35)
    # flag
    fx, fy = 1450, 230
    line(ctx, fx, fy, fx, fy - 110, "#3A2E44", 5)
    setc(ctx, "#F6B64A")
    ctx.move_to(fx, fy - 110)
    for i in range(11):
        xx = fx + i * 8
        ctx.line_to(xx, fy - 110 + math.sin(t * 6 - i * 0.6) * 5)
    for i in range(10, -1, -1):
        xx = fx + i * 8
        ctx.line_to(xx, fy - 70 + math.sin(t * 6 - i * 0.6) * 5)
    ctx.close_path()
    ctx.fill()
    glow(ctx, fx + 40, fy - 90, 160, "#FFD27A", 0.5 + 0.2 * math.sin(t * 3))
    hills(ctx, 820, 60, 0.003, 1.0, "#3E3058")
    ground(ctx, 880, "#2E2444", "#1E182E")
    path = [(420, 900), (700, 860), (880, 800), (1050, 740), (1180, 640), (1300, 520), (1400, 360), (1450, 240)]
    lp = ease_io(prog(t, 1.4, T))
    setc(ctx, "#7C6A9A", 0.6)
    ctx.set_line_width(10)
    ctx.set_dash([2, 24])
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(*path[0])
    for p in path[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    ctx.set_dash([])
    nseg = len(path) - 1
    k = lp * nseg
    setc(ctx, "#FFD27A")
    ctx.set_line_width(8)
    ctx.move_to(*path[0])
    tip = path[0]
    for i in range(1, len(path)):
        if i <= k:
            ctx.line_to(*path[i])
            tip = path[i]
        else:
            f = k - (i - 1)
            if f > 0:
                tip = (lerp(path[i - 1][0], path[i][0], f), lerp(path[i - 1][1], path[i][1], f))
                ctx.line_to(*tip)
            break
    ctx.stroke()
    if lp > 0:
        glow(ctx, tip[0], tip[1], 60, "#FFD27A", 0.8)
    roll = smooth(prog(t, 0.3, 1.0))
    pose = blend_pose("idle", "roll", roll) if t < 1.6 else blend_pose("roll", "fists", smooth(prog(t, 1.6, 2.1)))
    wp = prog(t, 2.4, T + 1)
    person(ctx, lerp(420, 640, wp), lerp(900, 870, wp), lerp(0.95, 0.8, wp), outfit="sweater", pose=pose,
           expr="determined" if t < 2.0 else "fierce", t=t, hair_grey=0.15,
           walk=(t * 8 if wp > 0 else None), look=(0.8, -0.6))
    ctx.restore()


# ======================================================== 9 blueprint phone
def phone_outline(ctx, cx, cy, w, h, p):
    """Stroke a rounded phone outline progressively (p in 0..1)."""
    r = 46
    pts = []
    n = 160
    for i in range(n + 1):
        f = i / n
        per = 2 * (w + h)
        d = f * per
        if d < w:
            pts.append((cx - w / 2 + d, cy - h / 2))
        elif d < w + h:
            pts.append((cx + w / 2, cy - h / 2 + d - w))
        elif d < 2 * w + h:
            pts.append((cx + w / 2 - (d - w - h), cy + h / 2))
        else:
            pts.append((cx - w / 2, cy + h / 2 - (d - 2 * w - h)))
    return pts


@scene("blueprint")
def blueprint(ctx, S):
    t, T = S.t, S.T
    fill_rect(ctx, "#0D2A52")
    for x in range(0, W, 40):
        line(ctx, x, 0, x, H, "#3D6FB0", 1 if x % 200 else 2, 0.35, cap=cairo.LINE_CAP_BUTT)
    for y in range(0, H, 40):
        line(ctx, 0, y, W, y, "#3D6FB0", 1 if y % 200 else 2, 0.35, cap=cairo.LINE_CAP_BUTT)
    cx, cy, w, h = 1120, 470, 330, 660
    dot = ease_out(prog(t, 0.0, 0.25))
    p = ease_io(prog(t, 0.2, 1.2))
    if p <= 0:
        glow(ctx, cx, cy, 60 * dot + 10, "#BFE3FF", 0.9)
        setc(ctx, "#FFFFFF")
        circle(ctx, cx, cy, 8 * dot + 2)
        ctx.fill()
    ww, hh = lerp(4, w, p), lerp(4, h, p)
    setc(ctx, "#DDF0FF")
    ctx.set_line_width(5)
    rrect(ctx, cx - ww / 2, cy - hh / 2, ww, hh, min(46, ww / 2))
    ctx.stroke()
    q = ease_out(prog(t, 1.0, 1.7))
    if q > 0:
        setc(ctx, "#DDF0FF", q)
        ctx.set_line_width(3)
        rrect(ctx, cx - w / 2 + 18, cy - h / 2 + 18, w - 36, h - 36, 30)
        ctx.stroke()
        circle(ctx, cx, cy - h / 2 + 40, 8)
        ctx.stroke()
        # dimension lines (no numbers)
        line(ctx, cx - w / 2, cy + h / 2 + 50, cx + w / 2, cy + h / 2 + 50, "#9CCBFF", 2, q)
        line(ctx, cx + w / 2 + 50, cy - h / 2, cx + w / 2 + 50, cy + h / 2, "#9CCBFF", 2, q)
        for (ax, ay) in ((cx - w / 2, cy + h / 2 + 50), (cx + w / 2, cy + h / 2 + 50)):
            line(ctx, ax, ay - 14, ax, ay + 14, "#9CCBFF", 2, q)
        for (ax, ay) in ((cx + w / 2 + 50, cy - h / 2), (cx + w / 2 + 50, cy + h / 2)):
            line(ctx, ax - 14, ay, ax + 14, ay, "#9CCBFF", 2, q)
        # components
        comps = [(cx - 70, cy - 150, 110, 80), (cx + 40, cy - 30, 90, 90), (cx - 100, cy + 60, 200, 170)]
        for i, (x, y, cw, ch) in enumerate(comps):
            a = ease_back(prog(t, 1.2 + i * 0.12, 1.5 + i * 0.12))
            if a > 0:
                setc(ctx, "#9CCBFF", 0.8 * clamp(a))
                ctx.set_line_width(3)
                rrect(ctx, x, y, cw * a, ch * a, 10)
                ctx.stroke()
    lit = smooth(prog(t, 1.8, T))
    if lit > 0:
        ctx.set_source(lin_grad(cx, cy - h / 2, cx, cy + h / 2, [(0, hexc("#5BC0FF", 0.85 * lit)), (1, hexc("#B28CFF", 0.85 * lit))]))
        rrect(ctx, cx - w / 2 + 18, cy - h / 2 + 18, w - 36, h - 36, 30)
        ctx.fill()
        glow(ctx, cx, cy, 500, "#8FD0FF", 0.3 * lit)
    person(ctx, 520, 900, 0.9, outfit="sweater", pose="point", expr="smile", t=t, hair_grey=0.15, look=(0.9, -0.3))


# ======================================================== 10 crash (2018)
@scene("crash")
def crash(ctx, S):
    t, T = S.t, S.T
    drop = T * 0.28
    ctx.save()
    sx, sy = shake(t, 10 * pulse(t, drop, drop + 0.6), 4)
    cam(ctx, 1.0 + 0.04 * t / T, 960, 520, sx, sy)
    vgrad(ctx, [(0, "#0C1222"), (1, "#070A14")])
    sx0, sy0, sw, sh = 260, 90, 1400, 640
    setc(ctx, "#1A2236")
    rrect(ctx, sx0 - 20, sy0 - 20, sw + 40, sh + 40, 24)
    ctx.fill()
    setc(ctx, "#0E1528")
    rrect(ctx, sx0, sy0, sw, sh, 14)
    ctx.fill()
    for i in range(1, 8):
        line(ctx, sx0, sy0 + i * sh / 8, sx0 + sw, sy0 + i * sh / 8, "#24304C", 2)
    for i in range(1, 14):
        line(ctx, sx0 + i * sw / 14, sy0, sx0 + i * sw / 14, sy0 + sh, "#1C2640", 2)
    issue_y = sy0 + 230
    ctx.set_dash([18, 12])
    line(ctx, sx0 + 20, issue_y, sx0 + sw - 20, issue_y, "#E8ECF5", 3, 0.9, cap=cairo.LINE_CAP_BUTT)
    ctx.set_dash([])
    # candles: open near issue price then slide below it
    n = 26
    p = prog(t, 0.3, T - 0.4)
    rnd = random.Random(10)
    level = issue_y
    red = hexc("#E2504C")
    for i in range(n):
        if i / n > p:
            break
        f = i / n
        target = issue_y - 30 + (f ** 0.7) * 300 if f > 0.12 else issue_y - 30 + f * 120
        o = level
        c = target + rnd.uniform(-30, 30)
        hi, lo = min(o, c) - rnd.uniform(5, 30), max(o, c) + rnd.uniform(5, 30)
        x = sx0 + 60 + i * (sw - 120) / n
        col = "#E2504C" if c > o else "#3CCB7F"
        line(ctx, x, hi, x, lo, col, 3)
        setc(ctx, col)
        ctx.rectangle(x - 12, min(o, c), 24, max(4, abs(c - o)))
        ctx.fill()
        level = c
    if t > drop:
        glow(ctx, sx0 + sw / 2, sy0 + sh * 0.7, 700, "#E2504C", 0.25 * smooth(prog(t, drop, drop + 0.5)))
        a = ease_back(prog(t, drop, drop + 0.5))
        ctx.save()
        ctx.translate(sx0 + sw - 170, sy0 + 420)
        ctx.scale(a, a)
        setc(ctx, "#E2504C")
        poly(ctx, [(-30, -120), (30, -120), (30, 0), (72, 0), (0, 80), (-72, 0), (-30, 0)])
        ctx.fill()
        ctx.restore()
    ground(ctx, 870, "#0C1020", "#070A14")
    person(ctx, 1640, 900, 0.8, outfit="sweater", pose="idle" if t < drop else "pocket",
           expr="calm" if t < drop else "worried", t=t, hair_grey=0.25, look=(-0.7, -0.8))
    ctx.restore()
    if t > drop:
        fill_rect(ctx, "#3A0508", alpha=0.18 * pulse(t, drop, drop + 0.8))


# ======================================================== 10 doubt
@scene("doubt")
def doubt(ctx, S):
    t, T = S.t, S.T
    vgrad(ctx, [(0, "#0D111D"), (1, "#151A2A")])
    spotlight(ctx, 960, -60, 960, 820, 40, 230, "#DDE6FF", 0.22)
    lift = smooth(prog(t, T - 1.4, T - 0.6))
    person(ctx, 960, 820, 0.74, outfit="sweater", pose="pocket", expr=blend_expr("sad", "determined", lift), t=t,
           hair_grey=0.25, look=(0, lerp(0.8, -0.2, lift)), tilt=lerp(0.06, 0.0, lift))
    rnd = random.Random(3)
    for _ in range(90):
        x0, y0 = rnd.uniform(0, W), rnd.uniform(0, H)
        y = (y0 + t * 1400) % (H + 100) - 50
        x = x0 - (y / H) * 60
        line(ctx, x, y, x - 8, y + 34, "#9FB4E0", 2, 0.35)
    # crowd in the foreground, shaking heads; gossip bubbles of scribbles
    for i in range(9):
        x = 60 + i * 230 + (i % 2) * 40
        silhouette(ctx, x, 1080 - (i % 2) * 30, 1.25 + (i % 3) * 0.12, "#05070D", seed=i, t=t, nod=0.12)
    for i, (bx, by) in enumerate(((330, 600), (1540, 560), (760, 640), (1240, 650))):
        a = ease_back(prog(t, 0.3 + i * 0.35, 0.7 + i * 0.35)) * (1 - 0.6 * lift)
        if a <= 0:
            continue
        ctx.save()
        ctx.translate(bx, by + math.sin(t * 2 + i) * 6)
        ctx.scale(a, a)
        setc(ctx, "#2A3148", 0.92)
        rrect(ctx, -90, -44, 180, 88, 40)
        ctx.fill()
        poly(ctx, [(-20, 40), (10, 40), (-30, 80)])
        ctx.fill()
        setc(ctx, "#8A93A8")
        ctx.set_line_width(4)
        ctx.move_to(-60, 0)
        for j in range(12):
            ctx.line_to(-60 + j * 10, -12 if j % 2 else 12)
        ctx.stroke()
        ctx.restore()


# ======================================================== 11 car
def car_points():
    """Side profile of a generic sleek fastback sedan (local coords, wheels at y=0)."""
    return [(-520, -40), (-520, -95), (-480, -130), (-330, -165), (-170, -255), (60, -270), (220, -240),
            (420, -170), (520, -140), (548, -95), (540, -40)]


@papered(0.9)
def draw_car(ctx, x, y, s, reveal=1.0, body=0.0, lights=0.0, color="#2E7FA8", t=0.0, outline_c="#BFE3FF"):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    pts = car_points()
    if body > 0:
        ctx.set_source(lin_grad(0, -270, 0, 0, [(0, hexc(shade(color, 0.25), body)), (0.55, hexc(color, body)),
                                                (1, hexc(shade(color, -0.45), body))]))
        ctx.move_to(*pts[0])
        for i in range(1, len(pts) - 1):
            mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
            ctx.curve_to(pts[i][0], pts[i][1], pts[i][0], pts[i][1], mx, my)
        ctx.line_to(*pts[-1])
        ctx.close_path()
        ctx.fill()
        setc(ctx, "#0E1A2A", body * 0.9)
        poly(ctx, [(-300, -170), (-160, -240), (60, -252), (200, -228), (300, -170)])
        ctx.fill()
        setc(ctx, "#FFFFFF", 0.25 * body)
        poly(ctx, [(-120, -236), (-40, -244), (-140, -176), (-220, -176)])
        ctx.fill()
        line(ctx, -40, -170, -40, -60, shade(color, -0.4), 3, body)
        line(ctx, -460, -110, 500, -112, shade(color, 0.35), 3, body * 0.7)
        sweep = (t * 0.6) % 2.0
        if sweep < 1:
            setc(ctx, "#FFFFFF", 0.18 * body)
            xx = lerp(-600, 600, sweep)
            poly(ctx, [(xx, -270), (xx + 60, -270), (xx - 40, -40), (xx - 100, -40)])
            ctx.fill()
    for wx in (-330, 330):
        if body > 0:
            setc(ctx, "#0B0D12", body)
            circle(ctx, wx, -10, 78)
            ctx.fill()
            setc(ctx, "#8A93A8", body)
            circle(ctx, wx, -10, 44)
            ctx.fill()
            for k in range(5):
                a = k / 5 * TAU + t * 0.5
                line(ctx, wx, -10, wx + math.cos(a) * 40, -10 + math.sin(a) * 40, "#3A3F4C", 6, body)
    if reveal > 0:
        seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        total = sum(seg) + 2 * 78 * math.pi
        L = total * reveal
        ctx.set_line_width(5)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        setc(ctx, outline_c)
        ctx.move_to(*pts[0])
        acc = 0
        tip = pts[0]
        for i, l in enumerate(seg):
            if acc + l >= L:
                f = (L - acc) / l
                tip = (lerp(pts[i][0], pts[i + 1][0], f), lerp(pts[i][1], pts[i + 1][1], f))
                ctx.line_to(*tip)
                break
            ctx.line_to(*pts[i + 1])
            tip = pts[i + 1]
            acc += l
        ctx.stroke()
        rest = L - sum(seg)
        if rest > 0:
            for j, wx in enumerate((330, -330)):
                frac = clamp((rest - j * 78 * math.pi) / (78 * math.pi))
                if frac > 0:
                    ctx.new_sub_path()
                    ctx.arc(wx, -10, 78, 0, TAU * frac)
                    ctx.stroke()
        if reveal < 1:
            glow(ctx, tip[0], tip[1], 90, outline_c, 0.9)
    if lights > 0:
        glow(ctx, 530, -110, 160, "#E8F6FF", lights)
        setc(ctx, "#FFFFFF", lights)
        rrect(ctx, 470, -128, 70, 12, 6)
        ctx.fill()
        light_rays(ctx, 540, -110, 1, 900, "#E8F6FF", 0.25 * lights, rot=0.04, width=0.12)
        setc(ctx, "#FF4D5A", lights)
        rrect(ctx, -524, -118, 30, 12, 6)
        ctx.fill()
    ctx.restore()


@scene("car")
def car(ctx, S):
    t, T = S.t, S.T
    on = T * 0.62
    vgrad(ctx, [(0, "#05070D"), (1, "#0B0F1C")])
    fl = cairo.LinearGradient(0, 770, 0, H)
    fl.add_color_stop_rgba(0, 0.12, 0.16, 0.26, 1)
    fl.add_color_stop_rgba(1, 0.02, 0.03, 0.06, 1)
    ctx.set_source(fl)
    ctx.rectangle(0, 770, W, H)
    ctx.fill()
    rp = ease_io(prog(t, 0.3, on))
    bp = smooth(prog(t, on, on + 1.0))
    lp = ease_out(prog(t, on - 0.1, on + 0.25))
    if bp > 0:
        spotlight(ctx, 1200, -60, 1200, 790, 50, 620, "#CFE6FF", 0.16 * bp)
    draw_car(ctx, 1200, 790, 0.95, rp, bp, lp, t=t)
    # floor reflection
    ctx.save()
    ctx.translate(0, 790 * 2 + 4)
    ctx.scale(1, -1)
    ctx.push_group()
    draw_car(ctx, 1200, 790, 0.95, rp, bp, lp * 0.4, t=t)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(0.16)
    ctx.restore()
    spotlight(ctx, 380, -60, 380, 880, 30, 200, "#FFE6B0", 0.2)
    q = smooth(prog(t, on - 0.3, on + 0.3))
    person(ctx, 380, 880, 0.82, outfit="sweater", pose=blend_pose("pocket", "fists", q),
           expr="calm" if t < on - 0.3 else "determined", t=t, hair_grey=0.28, look=(0.9, -0.2))


# ======================================================== 11 bubble: 愿意押上全部声誉
@scene("bubble_allin")
def bubble_allin(ctx, S):
    t, T = S.t, S.T
    ctx.save()
    cam(ctx, 1.0 + 0.05 * t / T, 960, 540)
    vgrad(ctx, [(0, "#1A1030"), (1, "#3B1626")])
    light_rays(ctx, 720, 400, 20, 1700, "#FFB347", 0.12, t, rot=-t * 0.15, width=0.07)
    glow(ctx, 720, 520, 760, "#FF8D4D", 0.35)
    particles(ctx, 12, 70, t, "#FFD27A", 0.8, vy=-90, vx=10, rmin=2, rmax=5, glow_r=4)
    q = ease_out(prog(t, 0.1, 0.6))
    info = person(ctx, 720, 1170, 1.7, outfit="sweater", pose=blend_pose("idle", "chest", q),
                  expr="determined" if t < 0.9 else "fierce", t=t, hair_grey=0.28, look=(0.3, -0.1))
    ctx.restore()
    hx, hy = ctx.device_to_user(*info["head"])
    fade = 1 - prog(t, T - 0.4, T - 0.08)
    if fade > 0:
        ctx.push_group()
        speech_bubble(ctx, "愿意押上全部声誉", 1290, 250, (hx + 120, hy - 60), t - 0.45)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade)


# ======================================================== 11 launch (2024)
@scene("launch")
def launch(ctx, S):
    t, T = S.t, S.T
    rev = T * 0.12
    ctx.save()
    cam(ctx, 1.0 + 0.06 * ease_io(t / T), 960, 520)
    vgrad(ctx, [(0, "#060818"), (1, "#0D1230")])
    # LED wall: abstract flowing waves
    setc(ctx, "#0A1236")
    ctx.rectangle(120, 60, 1680, 560)
    ctx.fill()
    ctx.save()
    ctx.rectangle(120, 60, 1680, 560)
    ctx.clip()
    for i in range(7):
        ctx.set_source(lin_grad(120, 0, 1800, 0, [(0, hexc("#2E7FA8", 0.0)), (0.5, hexc(["#2E7FA8", "#5BC0FF", "#B28CFF"][i % 3], 0.35)), (1, hexc("#2E7FA8", 0.0))]))
        ctx.set_line_width(26 - i * 2)
        ctx.move_to(120, 340)
        for x in range(120, 1801, 40):
            ctx.line_to(x, 340 + math.sin(x * 0.004 + t * 1.6 + i * 0.7) * (70 + i * 18))
        ctx.stroke()
    ctx.restore()
    # stage
    setc(ctx, "#121A3A")
    ellipse(ctx, 960, 800, 760, 90)
    ctx.fill()
    setc(ctx, "#5BC0FF", 0.5)
    ctx.set_line_width(4)
    ellipse(ctx, 960, 800, 760, 90)
    ctx.stroke()
    for i in range(6):
        a = math.sin(t * 1.2 + i * 1.3) * 0.35
        x_top = 160 + i * 320
        spotlight(ctx, x_top, -40, x_top + math.sin(a) * 900, 820, 20, 160, ["#CFE6FF", "#FFE6B0", "#B28CFF"][i % 3], 0.1)
    cp = ease_io(prog(t, rev, rev + 1.0))
    draw_car(ctx, 1020, 800, 0.9, 1.0 if cp > 0 else 0.0, cp, cp, t=t, outline_c="#DDF0FF")
    # cover cloth lifting off
    if cp < 1:
        ctx.save()
        ctx.translate(1020, 800 - cp * 700)
        ctx.rotate(-cp * 0.3)
        setc(ctx, "#8E1B2A", 1 - cp * 0.6)
        ctx.move_to(-560, 0)
        ctx.curve_to(-480, -150, -250, -280, 0, -290 - cp * 100)
        ctx.curve_to(250, -280, 500, -170, 580, 0)
        for k in range(8):
            ctx.line_to(580 - k * 140, math.sin(k * 1.7 + t * 4) * 18 * cp)
        ctx.close_path()
        ctx.fill()
        ctx.restore()
    if t > rev + 0.5:
        rnd = random.Random(2)
        for _ in range(80):
            tt = (t - rev - 0.5 + rnd.random() * 1.5) % 1.5
            a = rnd.uniform(-math.pi * 0.95, -math.pi * 0.05)
            sp = rnd.uniform(300, 800)
            x = 1020 + math.cos(a) * sp * tt
            y = 520 + math.sin(a) * sp * tt + 380 * tt * tt
            setc(ctx, rnd.choice(["#FFD27A", "#FFFFFF", "#9AD7FF"]), 1 - tt / 1.5)
            circle(ctx, x, y, 3)
            ctx.fill()
    confetti(ctx, 9, 120, t, rev + 0.6, ["#FFD27A", "#5BC0FF", "#FFFFFF", "#EF476F"])
    person(ctx, 380, 820, 0.6, outfit="sweater", pose=blend_pose("idle", "open", smooth(prog(t, rev + 0.6, rev + 1.2))),
           expr="happy", t=t, hair_grey=0.3, look=(0.8, -0.2))
    for i in range(12):
        x = 40 + i * 170
        silhouette(ctx, x, 1100, 1.0 + (i % 3) * 0.1, "#03040A", seed=i + 20, t=t)
        if i % 2 == 0:
            yy = 1100 - 1.0 * 200 - 10
            setc(ctx, "#DDF0FF", 0.85)
            rrect(ctx, x + 40, yy - 40 + math.sin(t + i) * 4, 34, 56, 6)
            ctx.fill()
            glow(ctx, x + 57, yy - 12, 50, "#DDF0FF", 0.3)
    ctx.restore()


# ======================================================== 12 path (every fall counts)
@papered(0.9)
def mini_icon(ctx, kind, x, y, s, a):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s, s)
    setc(ctx, "#3A2A1A", a)
    ctx.set_line_width(4)
    if kind == "ticket":
        rrect(ctx, -20, -12, 40, 24, 4)
        ctx.fill()
    elif kind == "box":
        ctx.rectangle(-16, -22, 32, 40)
        ctx.fill()
    elif kind == "jar":
        rrect(ctx, -16, -20, 32, 40, 8)
        ctx.stroke()
        ctx.rectangle(-10, 4, 20, 10)
        ctx.fill()
    elif kind == "letter":
        ctx.rectangle(-22, -14, 44, 28)
        ctx.stroke()
        ctx.move_to(-22, -14)
        ctx.line_to(0, 2)
        ctx.line_to(22, -14)
        ctx.stroke()
    elif kind == "door":
        ctx.rectangle(-14, -22, 28, 44)
        ctx.stroke()
        circle(ctx, 8, 0, 3)
        ctx.fill()
    elif kind == "balloon":
        ellipse(ctx, 0, -8, 14, 17)
        ctx.fill()
        ctx.move_to(0, 9)
        ctx.line_to(0, 24)
        ctx.stroke()
    elif kind == "chart":
        ctx.move_to(-22, -16)
        ctx.line_to(-6, -4)
        ctx.line_to(6, -10)
        ctx.line_to(22, 16)
        ctx.stroke()
    ctx.restore()


@scene("path")
def path_scene(ctx, S):
    t, T = S.t, S.T
    pan = ease_io(prog(t, 0.0, T))
    ctx.save()
    cam(ctx, 1.0, 960, lerp(640, 470, pan))
    vgrad(ctx, [(0, "#2C3C78"), (0.5, "#C77D7A"), (1, "#FFD7A0")], 0, -200, W, H + 400)
    glow(ctx, 1560, 160, 400, "#FFE6B0", 0.7)
    hills(ctx, 700, 80, 0.002, 0.5, "#6A4E7A")
    setc(ctx, "#4A3A62")
    ctx.move_to(-50, H + 200)
    ctx.curve_to(500, 900, 1100, 500, 1700, 150)
    ctx.line_to(W + 100, 150)
    ctx.line_to(W + 100, H + 200)
    ctx.close_path()
    ctx.fill()
    pts = [(140, 1060), (420, 960), (640, 900), (820, 800), (1010, 720), (1170, 610), (1330, 500), (1480, 380),
           (1640, 250)]
    setc(ctx, "#6E5A8A")
    ctx.set_line_width(16)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()
    kinds = ["ticket", "box", "jar", "letter", "door", "balloon", "chart"]
    lp = prog(t, 0.2, T - 0.6) * (len(pts) - 1)
    for i, p in enumerate(pts[1:-1]):
        a = clamp(lp - i)
        # a dusty fall-mark that turns into a glowing step
        setc(ctx, "#8A7A9A", 0.8 * (1 - a))
        ellipse(ctx, p[0], p[1] + 6, 46, 16)
        ctx.fill()
        if a > 0:
            s = ease_back(a)
            glow(ctx, p[0], p[1], 120 * s, "#FFD27A", 0.6 * a)
            setc(ctx, "#FFD27A")
            ellipse(ctx, p[0], p[1] + 4, 56 * s, 22 * s)
            ctx.fill()
            setc(ctx, "#FFE9B8")
            ellipse(ctx, p[0], p[1], 56 * s, 20 * s)
            ctx.fill()
            mini_icon(ctx, kinds[i % len(kinds)], p[0], p[1] - 60 * s, 1.0 * s, a)
    k = clamp(lp, 0, len(pts) - 1.001)
    i = int(k)
    f = k - i
    px = lerp(pts[i][0], pts[i + 1][0], f)
    py = lerp(pts[i][1], pts[i + 1][1], f)
    person(ctx, px, py, lerp(0.5, 0.3, k / (len(pts) - 1)), outfit="sweater", pose="idle", expr="smile", t=t,
           walk=t * 9, facing="back", hair_grey=0.3)
    ctx.restore()


# ======================================================== 12 sunrise
@scene("sunrise")
def sunrise(ctx, S):
    t, T = S.t, S.T
    rise = ease_out(prog(t, 0.0, T - 1.5), 2)
    vgrad(ctx, [(0, mix("#1E2A5A", "#F08A5D", rise * 0.7)), (0.62, mix("#C77D7A", "#FFD27A", rise)),
                (1, mix("#F2A27A", "#FFF0CF", rise))])
    sy = lerp(820, 600, rise)
    glow(ctx, 960, sy, 900, "#FFE6B0", 0.6 + 0.3 * rise)
    light_rays(ctx, 960, sy, 22, 1500, "#FFF3D2", 0.08 + 0.08 * rise, t, rot=t * 0.05)
    setc(ctx, "#FFF6DD")
    circle(ctx, 960, sy, 120)
    ctx.fill()
    ctx.set_source(lin_grad(0, 700, 0, H, [(0, "#4A2E4A"), (1, "#24152A")]))
    ctx.rectangle(0, 700, W, H)
    ctx.fill()
    setc(ctx, "#FFE6B0", 0.25)
    poly(ctx, [(900, 700), (1020, 700), (1400, H), (520, H)])
    ctx.fill()
    for i in range(5):
        xx = (t * 90 + i * 360) % (W + 200) - 100
        yy = 300 + i * 30 + math.sin(t * 2 + i) * 10
        w_ = math.sin(t * 9 + i) * 8
        setc(ctx, "#3A2A3A", 0.8)
        ctx.set_line_width(4)
        ctx.move_to(xx - 18, yy - w_)
        ctx.line_to(xx, yy)
        ctx.line_to(xx + 18, yy - w_)
        ctx.stroke()
    wp = prog(t, 0.3, T)
    y = lerp(1040, 900, ease_out(wp, 1.5))
    s = lerp(0.62, 0.4, ease_out(wp, 1.5))
    # long shadow toward camera
    setc(ctx, "#140A18", 0.5)
    poly(ctx, [(960 - 30 * s, y), (960 + 30 * s, y), (960 + 140 * s, H + 40), (960 - 140 * s, H + 40)])
    ctx.fill()
    person(ctx, 960, y, s, outfit="sweater", pose="idle", expr="smile", t=t, walk=t * 7, facing="back", hair_grey=0.3)
    fill_rect(ctx, "#000000", alpha=ease_in(prog(t, T - 1.4, T), 2))
