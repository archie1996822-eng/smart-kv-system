"""v3 style exploration: three candidate looks, each as two 1920x1080 frames
(opening apex hover + 2008/2026 portrait pair) and one comparison board.

A  cinematic dark illustration (hard light/shade cuts, rim light, haze, grain)
B  newsprint collage (cut paper, halftone, tape, paper grain)
C  flat vector motion graphics (clean shapes, soft gradients)
"""
import math
import os
import random

import cairo
import numpy as np
from scipy import ndimage

from geo import (path, head_ops, draw_ops, silhouette, Track, CAR_BODY, CAR_GLASS, CAR_SIDE_HI, WHEELS, NOZZLES,
                 car_xform, ellipse_pts)

W, H = 1920, 1080
OUT = os.path.join(os.path.dirname(__file__), "..", "release", "v3")
os.makedirs(OUT, exist_ok=True)

LINE_A = "短暂悬停。翻转。再落下。"
Y08, Y26 = "二零零八年。", "十八年后。"


def hexc(h, a=None):
    h = h.lstrip("#")
    c = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return c if a is None else (*c, a)


def mix(c1, c2, t):
    return tuple(x + (y - x) * t for x, y in zip(c1, c2))


def new(w=W, h=H):
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    return s, cairo.Context(s)


def arr(s):
    s.flush()
    return np.ndarray((s.get_height(), s.get_width(), 4), np.uint8, buffer=s.get_data())


def blurred(s, sigma):
    a = arr(s).astype(np.float32)
    out, _ = new(s.get_width(), s.get_height())
    b = arr(out)
    for c in range(4):
        b[..., c] = np.clip(ndimage.gaussian_filter(a[..., c], sigma), 0, 255).astype(np.uint8)
    out.mark_dirty()
    return out


def comp(ctx, src, op=cairo.OPERATOR_OVER, alpha=1.0, x=0, y=0):
    ctx.save()
    ctx.set_operator(op)
    ctx.set_source_surface(src, x, y)
    ctx.paint_with_alpha(alpha)
    ctx.restore()


_GRAIN = {}


def grain(s, amt=10, seed=1, mono=True):
    a = arr(s)
    key = (amt, seed, a.shape[:2])
    if key not in _GRAIN:
        _GRAIN[key] = np.random.default_rng(seed).normal(0, amt, a.shape[:2]).astype(np.float32)
    n = _GRAIN[key]
    for c in range(3):
        a[..., c] = np.clip(a[..., c].astype(np.float32) + n * (a[..., 3] / 255.0), 0, 255).astype(np.uint8)
    s.mark_dirty()


def vignette(ctx, strength=0.6, col=(0, 0, 0)):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05)
    g.add_color_stop_rgba(0, *col, 0)
    g.add_color_stop_rgba(1, *col, strength)
    ctx.set_source(g)
    ctx.paint()


def text(ctx, s, x, y, size, col, font="Noto Serif CJK SC", bold=True, spacing=0.08, anchor="center", alpha=1.0):
    ctx.save()
    ctx.select_font_face(font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    widths = [ctx.text_extents(ch).x_advance for ch in s]
    total = sum(widths) + spacing * size * (len(s) - 1)
    cx = x - total / 2 if anchor == "center" else x if anchor == "left" else x - total
    ctx.set_source_rgba(*col[:3], (col[3] if len(col) > 3 else 1.0) * alpha)
    for ch, w_ in zip(s, widths):
        ctx.move_to(cx, y)
        ctx.show_text(ch)
        cx += w_ + spacing * size
    ctx.restore()
    return total


def poly(ctx, pts, col, smooth=False):
    path(ctx, pts, True, smooth)
    ctx.set_source_rgba(*col) if len(col) == 4 else ctx.set_source_rgb(*col)
    ctx.fill()


def line(ctx, pts, col, w, smooth=False, dash=None):
    path(ctx, pts, False, smooth)
    ctx.set_source_rgba(*col) if len(col) == 4 else ctx.set_source_rgb(*col)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    if dash:
        ctx.set_dash(dash)
    ctx.stroke()
    ctx.set_dash([])


# ====================================================================== shared scene layout
TR = Track(cx=1080, ground=950, rx=250, ry=392, lead=1150, a_end=1.09 * math.pi)
HALF = 66                    # track half-width along depth
CAR_A = 0.96 * math.pi      # apex position (car hanging inverted under the lip)
CAR_L = 132                  # half car length in px


def dvec(y):
    """Oblique depth axis; camera sits low, so the far edge drops as the track rises
    (we see the deck near the ground and the underside of the lip at the top)."""
    t = min(1.0, max(0.0, (TR.ground - y) / (2 * TR.ry)))
    return (-0.6, -0.2 + 0.5 * t)


def off(p, k):
    d = dvec(p[1])
    return (p[0] + d[0] * HALF * k, p[1] + d[1] * HALF * k)


def track_strips(n=220):
    """Quad strips across the ribbon with the inner-normal for shading."""
    cl = [(TR.cx - TR.lead + TR.lead * i / 30, TR.ground) for i in range(30)]
    al = [0.0] * 30
    for i in range(n + 1):
        a = TR.a_end * i / n
        cl.append(TR.at(a)[0])
        al.append(a)
    strips = []
    for i in range(len(cl) - 1):
        p0, p1 = cl[i], cl[i + 1]
        nrm = TR.normal_in(al[i]) if al[i] > 0 else (0, -1)
        q = [off(p0, -1), off(p1, -1), off(p1, 1), off(p0, 1)]
        strips.append((q, nrm, al[i]))
    return cl, strips


def track_rails(cl, k):
    return [off(p, k) for p in cl]


def underside(cl, strips, th=14):
    pts_out = []
    for (q, nrm, a), p in zip(strips, cl):
        pts_out.append((p[0] - nrm[0] * th, p[1] - nrm[1] * th))
    return pts_out


def truss_lines(depth_k=1.9):
    """Lattice tower behind the vertical section + gantry over the top lip."""
    bx = TR.cx + TR.rx + 60
    top = TR.cy - TR.ry - 26
    segs = []
    O = lambda x, y, dk: off((x, y), dk)
    for dk in (depth_k, 0.9):
        for xx in (bx, bx + 70):
            segs.append((O(xx, TR.ground, dk), O(xx, top, dk)))
        y = TR.ground
        step = 62
        while y - step > top:
            segs.append((O(bx, y, dk), O(bx + 70, y - step, dk)))
            segs.append((O(bx + 70, y, dk), O(bx, y - step, dk)))
            segs.append((O(bx, y, dk), O(bx + 70, y, dk)))
            y -= step
        lip = TR.at(TR.a_end)[0]
        segs.append((O(bx + 70, top, dk), O(lip[0] - 20, top, dk)))
        segs.append((O(bx, top + 34, dk), O(lip[0] - 20, top + 34, dk)))
        xx = bx
        while xx > lip[0]:
            segs.append((O(xx, top, dk), O(xx - 34, top + 34, dk)))
            xx -= 34
    return segs


def car_geom(gap=10):
    f, n = car_xform(TR, CAR_A, CAR_L, gap=gap)
    body = [f(p) for p in CAR_BODY]
    glass = [f(p) for p in CAR_GLASS]
    hi = [f(p) for p in CAR_SIDE_HI]
    wheels = [(f(c), 0.15 * CAR_L) for c in WHEELS]
    nozz = [f(p) for p in NOZZLES]
    return f, n, body, glass, hi, wheels, nozz


def plume_pts(base, direction, length, w0, w1, wobble=0.0, seed=0):
    rnd = random.Random(seed)
    dx, dy = direction
    px, py = -dy, dx
    left, right = [], []
    for i in range(13):
        t = i / 12
        w = w0 + (w1 - w0) * t ** 0.8
        j = wobble * (rnd.random() - 0.5) * t
        cx, cy = base[0] + dx * length * t, base[1] + dy * length * t
        left.append((cx + px * (w + j), cy + py * (w + j)))
        right.append((cx - px * (w - j), cy - py * (w - j)))
    return left + right[::-1]


def gas(ctx, base, d, length, w0, w1, col, a0, seed=0, wobble=8.0, fade=1.0):
    """Cold-gas plume: tapered body whose opacity falls off along the axis."""
    pts = plume_pts(base, d, length, w0, w1, wobble, seed)
    g = cairo.LinearGradient(base[0], base[1], base[0] + d[0] * length, base[1] + d[1] * length)
    g.add_color_stop_rgba(0, *col, a0)
    g.add_color_stop_rgba(0.35, *col, a0 * 0.75)
    g.add_color_stop_rgba(fade, *col, 0)
    path(ctx, pts, True, True)
    ctx.set_source(g)
    ctx.fill()


def puffs(ctx, base, d, length, col, a0, seed=0, n=10, r0=8, r1=46):
    rnd = random.Random(seed)
    px, py = -d[1], d[0]
    for i in range(n):
        t = 0.25 + 0.75 * rnd.random()
        r = r0 + (r1 - r0) * t
        sx = rnd.uniform(-0.6, 0.6) * r
        cx, cy = base[0] + d[0] * length * t + px * sx, base[1] + d[1] * length * t + py * sx
        g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
        g.add_color_stop_rgba(0, *col, a0 * (1 - t) ** 0.7)
        g.add_color_stop_rgba(1, *col, 0)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.set_source(g)
        ctx.fill()


def jets(ctx, nozz, n, scale=1.0, seed=0, style="A"):
    """Four cold-gas jets: two near nozzles + two on the far side (offset along depth)."""
    bases = [off(nz, 0.75) for nz in nozz] + [off(nz, -0.1) for nz in nozz]
    out = []
    for k, b in enumerate(bases):
        out.append((b, k >= 2))
    return out


# ====================================================================== A: cinematic dark illustration
A_SKIN = {"s0": hexc("#2a1814"), "s1": hexc("#6a4436"), "s2": hexc("#a8775f"), "s3": hexc("#cf9f83"), "s4": hexc("#ecc6aa")}


def a_pal(age):
    p = dict(A_SKIN)
    if age > 0.5:  # 2026: duller, a touch paler skin under harsher light
        p = {k: mix(v, (0.62, 0.58, 0.56), 0.18) for k, v in p.items()}
    hair = hexc("#4a3427") if age < 0.5 else hexc("#55483f")
    p.update({
        "nostril": hexc("#1d0f0c"), "line": hexc("#160c09"), "white": hexc("#a9998c"), "iris": hexc("#3b2a20"),
        "pupil": hexc("#0b0605"), "catch": hexc("#f4f1ec"), "lidsh": (0.1, 0.05, 0.03, 0.35),
        "lipU": mix(p["s1"], hexc("#8a3f36"), 0.35), "lipL": mix(p["s2"], hexc("#a5574c"), 0.3), "mline": hexc("#2a1210"), "mouth": hexc("#2a1210"), "teeth": hexc("#cdbfb2"),
        "brow": hexc("#24170f"), "hair": hair, "hair_mid": mix(hair, (0.75, 0.62, 0.52), 0.18),
        "hair_hi": mix(hair, (0.85, 0.75, 0.66), 0.32 if age < 0.5 else 0.42), "hair_sh": hexc("#20160f"),
        "grey": (0.7, 0.68, 0.66, 0.7),
        "jacket": hexc("#0d0f13"), "jacket_hi": hexc("#1c2029"), "shirt": hexc("#d8d6d0"), "shirt_sh": hexc("#8f8d88"),
        "tee": hexc("#0f1013"), "tee_hi": hexc("#1d1f25"),
    })
    return p


def a_head(ctx, ops, ox, oy, s, pal, rim=(0.55, 0.75, 1.0)):
    layer, lc = new()
    draw_ops(lc, ops, ox, oy, s, pal)
    # rim light: silhouette minus itself shifted toward the light -> thin edge on the shadow side
    a = arr(layer)[..., 3].astype(np.float32) / 255
    sh = np.roll(np.roll(a, -9, axis=1), 5, axis=0)
    edge = np.clip(a - sh, 0, 1)
    edge = ndimage.gaussian_filter(edge, 1.2)
    rl, _ = new()
    r = arr(rl)
    for c, v in zip((2, 1, 0), rim):
        r[..., c] = (np.clip(edge, 0, 1) * 255 * v).astype(np.uint8)
    r[..., 3] = (np.clip(edge, 0, 1) * 255).astype(np.uint8)
    rl.mark_dirty()
    comp(ctx, layer)
    comp(ctx, rl, cairo.OPERATOR_SCREEN, 0.95)
    comp(ctx, blurred(rl, 10), cairo.OPERATOR_SCREEN, 0.8)


def a_car():
    surf, ctx = new()
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *hexc("#04060a"))
    g.add_color_stop_rgb(0.75, *hexc("#0a101b"))
    g.add_color_stop_rgb(1, *hexc("#06080c"))
    ctx.set_source(g)
    ctx.paint()
    # horizon haze + distant lights
    hz, hc = new()
    g = cairo.LinearGradient(0, TR.ground - 140, 0, TR.ground + 40)
    g.add_color_stop_rgba(0, 0.25, 0.36, 0.55, 0)
    g.add_color_stop_rgba(0.8, 0.25, 0.36, 0.55, 0.22)
    g.add_color_stop_rgba(1, 0.25, 0.36, 0.55, 0)
    hc.set_source(g)
    hc.paint()
    comp(ctx, hz)
    rnd = random.Random(3)
    lights, lc = new()
    for _ in range(26):
        x = rnd.uniform(0, W)
        y = TR.ground - rnd.uniform(4, 30)
        lc.arc(x, y, rnd.uniform(1.2, 3.0), 0, 2 * math.pi)
        lc.set_source_rgba(0.7, 0.82, 1.0, rnd.uniform(0.3, 0.8))
        lc.fill()
    comp(ctx, lights)
    comp(ctx, blurred(lights, 6), cairo.OPERATOR_SCREEN, 1.0)
    # ground
    g = cairo.LinearGradient(0, TR.ground, 0, H)
    g.add_color_stop_rgb(0, *hexc("#0c1119"))
    g.add_color_stop_rgb(1, *hexc("#030406"))
    ctx.rectangle(0, TR.ground, W, H - TR.ground)
    ctx.set_source(g)
    ctx.fill()
    # floodlight beams from the ground, lower left
    beams, bc = new()
    for (x0, ang, spread, a_) in ((560, -1.05, 0.11, 0.22), (760, -1.2, 0.09, 0.18), (1700, -2.05, 0.1, 0.16)):
        L_ = 1500
        bc.move_to(x0, TR.ground)
        bc.line_to(x0 + L_ * math.cos(ang - spread), TR.ground + L_ * math.sin(ang - spread))
        bc.line_to(x0 + L_ * math.cos(ang + spread), TR.ground + L_ * math.sin(ang + spread))
        bc.close_path()
        gg = cairo.RadialGradient(x0, TR.ground, 10, x0, TR.ground, L_)
        gg.add_color_stop_rgba(0, 0.75, 0.85, 1.0, a_)
        gg.add_color_stop_rgba(1, 0.75, 0.85, 1.0, 0)
        bc.set_source(gg)
        bc.fill()
    comp(ctx, blurred(beams, 14), cairo.OPERATOR_SCREEN)

    # truss (behind)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for (a, b) in truss_lines():
        ctx.move_to(*a)
        ctx.line_to(*b)
    ctx.set_source_rgba(0.34, 0.38, 0.45, 0.9)
    ctx.set_line_width(3.2)
    ctx.stroke()
    for (a, b) in truss_lines(1.9)[:4]:
        line(ctx, [a, b], (0.62, 0.7, 0.82, 0.55), 1.4)

    # track
    cl, strips = track_strips()
    us = underside(cl, strips, 16)
    poly(ctx, track_rails(cl, -1) + track_rails(us, -1)[::-1], hexc("#1b1f26"))
    L = (-0.72, 0.36)
    for q, nrm, a in strips:
        k = 0.42 + 0.58 * max(0.0, nrm[0] * L[0] + nrm[1] * L[1])
        if a == 0:
            k = 0.5
        c = mix(hexc("#2a2f37"), hexc("#d9dde2"), k)
        path(ctx, q, True, False)
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_line_width(1)
        ctx.stroke()
    # red edges + centre line
    edges, ec = new()
    line(ec, track_rails(cl, -1), hexc("#ff3b4a"), 3.2)
    line(ec, track_rails(cl, 1), hexc("#ff3b4a"), 2.6)
    comp(ctx, edges)
    comp(ctx, blurred(edges, 5), cairo.OPERATOR_SCREEN, 0.9)
    line(ctx, track_rails(cl, 0.08), (0.96, 0.97, 1.0, 0.85), 2.4, dash=[26, 22])

    # car hanging inverted under the lip + jets
    f, n, body, glass, hi, wheels, nozz = car_geom(gap=12)
    plumes, pc = new()
    for k, (b, far) in enumerate(jets(ctx, nozz, n)):
        fk = 0.55 if far else 1.0
        gas(pc, b, n, 400, 6, 48, (0.72, 0.84, 1.0), 0.32 * fk, seed=k, wobble=12)
        gas(pc, b, n, 240, 3.5, 18, (0.9, 0.96, 1.0), 0.7 * fk, seed=k + 9, wobble=4)
        puffs(pc, b, n, 400, (0.85, 0.92, 1.0), 0.28 * fk, seed=k, n=12, r0=8, r1=42)
    comp(ctx, blurred(plumes, 14), cairo.OPERATOR_SCREEN, 0.9)
    comp(ctx, blurred(plumes, 2), cairo.OPERATOR_SCREEN, 0.7)
    cores, cc_ = new()
    for k, (b, far) in enumerate(jets(ctx, nozz, n)):
        gas(cc_, b, n, 110, 2.5, 6, (1, 1, 1), 0.6 if far else 1.0, seed=k + 3, wobble=0)
    comp(ctx, cores, cairo.OPERATOR_SCREEN)
    comp(ctx, blurred(cores, 6), cairo.OPERATOR_SCREEN)
    # car body
    for (c, r) in wheels:
        ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#0b0c0f"))
        ctx.fill()
        ctx.arc(c[0], c[1], r * 0.55, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#5c6470"))
        ctx.fill()
    poly(ctx, body, hexc("#c9ced6"))
    g = cairo.LinearGradient(*f((0, -0.42)), *f((0, -0.02)))
    g.add_color_stop_rgba(0, 1, 1, 1, 0.0)
    g.add_color_stop_rgba(1, 0.95, 0.98, 1.0, 0.55)
    path(ctx, body, True, False)
    ctx.set_source(g)
    ctx.fill()
    poly(ctx, glass, hexc("#0b0f16"), True)
    line(ctx, [f((-0.9, -0.24)), f((0.0, -0.3)), f((0.9, -0.2))], (1, 1, 1, 0.5), 2.0, smooth=True)
    line(ctx, [f((-0.98, -0.2)), f((-0.9, -0.2))], hexc("#ff3b4a"), 4)
    line(ctx, [f((0.97, -0.13)), f((0.9, -0.15))], (0.9, 0.95, 1.0), 4)
    for nz in nozz:
        ctx.arc(nz[0], nz[1], 5, 0, 2 * math.pi)
        ctx.set_source_rgb(0.85, 0.92, 1.0)
        ctx.fill()

    # text
    tl, tc = new()
    text(tc, LINE_A, W / 2, 1010, 54, (0.96, 0.97, 1.0), spacing=0.12)
    comp(ctx, blurred(tl, 8), cairo.OPERATOR_SCREEN, 0.5)
    comp(ctx, tl)
    vignette(ctx, 0.65)
    grain(surf, 9, seed=11)
    return surf


def a_portrait():
    surf, ctx = new()
    ctx.set_source_rgb(*hexc("#05070a"))
    ctx.paint()
    for cx, age, smile, key in ((480, 0.0, 0.7, (0.78, 0.86, 1.0)), (1440, 1.0, 0.1, (1.0, 0.94, 0.88))):
        # soft key-light glow behind each head
        gl = cairo.RadialGradient(cx - 120, 360, 40, cx - 120, 360, 640)
        gl.add_color_stop_rgba(0, *key, 0.13)
        gl.add_color_stop_rgba(1, *key, 0)
        ctx.rectangle(cx - 480, 0, 960, H)
        ctx.set_source(gl)
        ctx.fill()
        ctx.save()
        ctx.rectangle(cx - 480, 0, 960, H)
        ctx.clip()
        s = 0.92
        a_head(ctx, head_ops(age, smile), cx - 305 * s, 58 - 18 * s, s, a_pal(age))
        ctx.restore()
        g = cairo.LinearGradient(0, 820, 0, H)
        g.add_color_stop_rgba(0, 0, 0, 0, 0)
        g.add_color_stop_rgba(1, 0, 0, 0, 0.85)
        ctx.rectangle(cx - 480, 820, 960, H - 820)
        ctx.set_source(g)
        ctx.fill()
    line(ctx, [(960, 120), (960, 960)], (1, 1, 1, 0.12), 1.5)
    text(ctx, Y08, 480, 1018, 50, (0.95, 0.96, 1.0), spacing=0.14)
    text(ctx, Y26, 1440, 1018, 50, (0.95, 0.96, 1.0), spacing=0.14)
    vignette(ctx, 0.5)
    grain(surf, 9, seed=12)
    return surf


# ====================================================================== B: newsprint collage
PAPER = hexc("#efe7d6")
INK = hexc("#17171a")
RED = hexc("#d8382e")


def paper_bg(ctx, col=PAPER, seed=0, lines=False):
    ctx.set_source_rgb(*col)
    ctx.paint()
    rnd = random.Random(seed)
    for _ in range(900):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        ang = rnd.uniform(0, math.pi)
        ln = rnd.uniform(4, 18)
        ctx.move_to(x, y)
        ctx.line_to(x + ln * math.cos(ang), y + ln * math.sin(ang))
        ctx.set_source_rgba(0.4, 0.33, 0.25, rnd.uniform(0.03, 0.09))
        ctx.set_line_width(0.8)
        ctx.stroke()
    if lines:
        for y in range(0, H, 36):
            line(ctx, [(0, y), (W, y)], (0.3, 0.45, 0.6, 0.08), 1)


def torn(pts, seed=0, amp=6, step=10):
    rnd = random.Random(seed)
    out = []
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        d = math.hypot(x1 - x0, y1 - y0)
        k = max(1, int(d / step))
        nx, ny = -(y1 - y0) / (d + 1e-9), (x1 - x0) / (d + 1e-9)
        for j in range(k):
            t = j / k
            j_ = rnd.uniform(-amp, amp)
            out.append((x0 + (x1 - x0) * t + nx * j_, y0 + (y1 - y0) * t + ny * j_))
    return out


def drop_shadow(ctx, draw_fn, off=(8, 10), sigma=6, alpha=0.35):
    sh, sc = new()
    sc.translate(*off)
    draw_fn(sc, (0, 0, 0, 1))
    comp(ctx, blurred(sh, sigma), alpha=alpha)


def halftone(ctx, dark_surf, clip_surf, ink, spacing=9.0, angle=0.6, maxr=0.62, region=None):
    d = arr(dark_surf).astype(np.float32)
    lum = (0.11 * d[..., 0] + 0.59 * d[..., 1] + 0.3 * d[..., 2]) / 255
    alpha = arr(clip_surf)[..., 3].astype(np.float32) / 255
    dark = (1 - lum) * alpha
    x0, y0, x1, y1 = region or (0, 0, W, H)
    ca, sa = math.cos(angle), math.sin(angle)
    diag = math.hypot(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ctx.set_source_rgba(*ink)
    n = int(diag / spacing) + 2
    for i in range(-n // 2, n // 2 + 1):
        for j in range(-n // 2, n // 2 + 1):
            u, v = i * spacing, j * spacing
            x, y = cx + u * ca - v * sa, cy + u * sa + v * ca
            if not (x0 <= x < x1 and y0 <= y < y1):
                continue
            dv = dark[int(y), int(x)]
            if dv < 0.04:
                continue
            ctx.arc(x, y, spacing * maxr * math.sqrt(dv), 0, 2 * math.pi)
            ctx.new_sub_path()
    ctx.fill()


def b_flat_pal(age):
    skin = hexc("#f0c3a4") if age < 0.5 else hexc("#e9bea3")
    hair = hexc("#5a4030") if age < 0.5 else hexc("#6b5a50")
    p = {k: skin for k in ("s2", "s3", "s4")}
    p["s1"] = mix(skin, hexc("#c98466"), 0.45)
    p["s0"] = mix(skin, hexc("#a8634c"), 0.6)
    p.update({"nostril": INK, "line": INK, "white": hexc("#f7f2e8"), "iris": hexc("#4a3426"), "pupil": INK,
              "catch": hexc("#ffffff"), "lipU": hexc("#c96f60"), "lipL": hexc("#d98676"), "mline": INK, "mouth": hexc("#3a1a16"), "teeth": hexc("#fbf6ec"), "brow": hexc("#3b2a20"),
              "hair": hair, "hair_mid": hair, "hair_hi": hair, "hair_sh": hair, "grey": hexc("#b8b0aa"),
              "jacket": hexc("#26282e"), "jacket_hi": hexc("#26282e"), "shirt": hexc("#f7f4ec"), "shirt_sh": hexc("#f7f4ec"),
              "tee": hexc("#26282e"), "tee_hi": hexc("#26282e")})
    return p


def b_dark_pal(age):
    g = lambda v: (v, v, v)
    p = {"s0": g(0.3), "s1": g(0.62), "s2": g(0.93), "s3": g(1.0), "s4": g(1.0), "nostril": g(0.0), "line": g(0.0),
         "white": g(1.0), "iris": g(1.0), "pupil": g(1.0), "catch": g(1), "lidsh": (0, 0, 0, 0.0), "lipU": g(0.55), "lipL": g(0.8), "mouth": g(0.1), "teeth": g(1.0),
         "mline": g(0), "brow": g(0.25), "hair": g(0.55), "hair_mid": g(0.75), "hair_hi": g(0.85), "hair_sh": g(0.15),
         "grey": g(0.9), "jacket": g(0.45), "jacket_hi": g(0.7), "shirt": g(1.0), "shirt_sh": g(0.7), "tee": g(0.45), "tee_hi": g(0.7)}
    return p


def b_head(ctx, ops, ox, oy, s, age, rot=0.0, pivot=(0, 0), border=14, region=None):
    flat, fc = new()
    draw_ops(fc, ops, ox, oy, s, b_flat_pal(age))
    dk, dc = new()
    dc.set_source_rgb(1, 1, 1)
    dc.paint()
    draw_ops(dc, ops, ox, oy, s, b_dark_pal(age))
    fctx = cairo.Context(flat)
    halftone(fctx, dk, flat, (*INK, 0.8), spacing=9.5, angle=0.78, maxr=0.58, region=region)
    # re-draw the crisp key lines on top of the dots
    draw_ops(fctx, [o for o in ops if o[0] in ("line", "mline", "brow", "pupil", "catch", "white", "iris", "nostril", "teeth", "_clip", "_unclip")],
             ox, oy, s, {"line": INK, "mline": INK, "brow": hexc("#2a1d16"), "pupil": INK, "catch": (1, 1, 1),
                         "white": hexc("#f7f2e8"), "iris": hexc("#4a3426"), "nostril": INK, "teeth": hexc("#fbf6ec")})
    # white paper border (cut-out sticker) + shadow
    a = arr(flat)[..., 3] > 10
    big = ndimage.binary_dilation(a, iterations=border)
    big = ndimage.gaussian_filter(big.astype(np.float32), 1.0)
    cut, _ = new()
    c = arr(cut)
    c[..., 0] = (big * 0.93 * 255).astype(np.uint8)
    c[..., 1] = (big * 0.96 * 255).astype(np.uint8)
    c[..., 2] = (big * 0.98 * 255).astype(np.uint8)
    c[..., 3] = (big * 255).astype(np.uint8)
    cut.mark_dirty()
    comb, cc = new()
    comp(cc, cut)
    comp(cc, flat)
    ctx.save()
    ctx.translate(*pivot)
    ctx.rotate(rot)
    ctx.translate(-pivot[0], -pivot[1])
    sh = blurred(cut, 8)
    comp(ctx, sh, alpha=0.4, x=10, y=12)
    comp(ctx, comb)
    ctx.restore()


_TOON = {}


def b_toon(ctx, age, expr, cx, top, s, rot=0.0, border=12, zoom=1.0):
    """Cartoon cut-out: flat paper layers -> halftone shade + blush -> ink -> white border + shadow."""
    key = (age, expr, round(s, 3), border)
    if key not in _TOON:
        _TOON[key] = _toon_build(age, expr, s, border)
    cut, flat, sh = _TOON[key]
    fw, fh = flat.get_width(), flat.get_height()
    x0, y0 = cx - 500 * s, top
    ctx.save()
    hcx, hcy = cx, top + 470 * s
    ctx.translate(hcx, hcy)
    ctx.rotate(rot)
    ctx.scale(zoom, zoom)
    ctx.translate(-hcx, -hcy)
    comp(ctx, sh, alpha=0.4, x=x0 - 30 + 10, y=y0 - 30 + 12)
    comp(ctx, cut, x=x0, y=y0)
    comp(ctx, flat, x=x0, y=y0)
    ctx.restore()


def _toon_build(age, expr, s, border):
    import toon
    flat, shade, blush, ink = toon.figure(age, expr, s=s)
    fw, fh = flat.get_width(), flat.get_height()
    fctx = cairo.Context(flat)
    reg = (0, 0, fw, fh)
    halftone(fctx, shade, flat, (*INK, 0.7), spacing=9 * s / 0.9, angle=0.78, maxr=0.55, region=reg)
    halftone(fctx, blush, flat, (0.86, 0.3, 0.3, 0.75), spacing=8 * s / 0.9, angle=0.3, maxr=0.6, region=reg)
    fctx.set_source_surface(ink, 0, 0)
    fctx.paint()
    a = arr(flat)[..., 3] > 10
    big = ndimage.binary_dilation(a, iterations=max(2, int(border * s)))
    big = ndimage.gaussian_filter(big.astype(np.float32), 1.0)
    cut = cairo.ImageSurface(cairo.FORMAT_ARGB32, fw, fh)
    c = arr(cut)
    c[..., 0] = (big * 0.93 * 255).astype(np.uint8)
    c[..., 1] = (big * 0.96 * 255).astype(np.uint8)
    c[..., 2] = (big * 0.98 * 255).astype(np.uint8)
    c[..., 3] = (big * 255).astype(np.uint8)
    cut.mark_dirty()
    sh = cairo.ImageSurface(cairo.FORMAT_ARGB32, fw + 60, fh + 60)
    shc = cairo.Context(sh)
    shc.set_source_surface(cut, 30, 30)
    shc.paint()
    return cut, flat, blurred(sh, 7)


def tape_label(ctx, s, x, y, size, rot=-0.02, bg=INK, fg=(1, 1, 1)):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    ctx.select_font_face("Noto Sans CJK SC", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    wid = sum(ctx.text_extents(ch).x_advance for ch in s) + 0.06 * size * (len(s) - 1)
    pad = size * 0.55
    rect = [(-wid / 2 - pad, -size * 0.95), (wid / 2 + pad, -size * 0.95), (wid / 2 + pad, size * 0.42), (-wid / 2 - pad, size * 0.42)]
    rt = torn(rect, seed=int(x), amp=2.5, step=7)
    drop_shadow(ctx, lambda c, col: poly(c, rt, col), off=(5, 6), sigma=4, alpha=0.3)
    poly(ctx, rt, bg)
    ctx.restore()
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(rot)
    text(ctx, s, 0, 0, size, fg, font="Noto Sans CJK SC", spacing=0.06)
    ctx.restore()


def b_car():
    surf, ctx = new()
    paper_bg(ctx, seed=1)
    # torn navy "night" sheet
    sky = torn([(70, 50), (1850, 30), (1880, 1000), (40, 1030)], seed=4, amp=9, step=14)
    drop_shadow(ctx, lambda c, col: poly(c, sky, col), off=(10, 12), sigma=8, alpha=0.35)
    poly(ctx, sky, hexc("#1f2b45"))
    # halftone glow behind the apex
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
    # ground strip of torn grey paper
    gnd = torn([(40, TR.ground + 4), (1880, TR.ground - 6), (1880, 1030), (40, 1030)], seed=8, amp=5)
    poly(ctx, gnd, hexc("#2c2f36"))
    # ink truss, hand-drawn wobble
    rnd = random.Random(5)
    for (a, b) in truss_lines():
        mid = ((a[0] + b[0]) / 2 + rnd.uniform(-2, 2), (a[1] + b[1]) / 2 + rnd.uniform(-2, 2))
        line(ctx, [a, mid, b], (0.92, 0.9, 0.85, 0.85), 2.4, smooth=True)
    # track: grey card cut-out
    cl, strips = track_strips()
    near = track_rails(cl, -1)
    farr = track_rails(cl, 1)
    shape = near + farr[::-1]
    drop_shadow(ctx, lambda c, col: poly(c, shape, col), off=(12, 14), sigma=6, alpha=0.45)
    poly(ctx, shape, hexc("#d9d5cc"))
    us = underside(cl, strips, 16)
    poly(ctx, near + track_rails(us, -1)[::-1], hexc("#9c978e"))
    # halftone shading on the inner surface (dark where it turns away)
    sd, sdc = new()
    sdc.set_source_rgb(1, 1, 1)
    sdc.paint()
    L = (-0.72, 0.36)
    for q, nrm, a in strips:
        k = 0.45 + 0.55 * max(0.0, nrm[0] * L[0] + nrm[1] * L[1])
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
    # jets: layered torn tissue paper (white / pale blue)
    f, n, body, glass, hi, wheels, nozz = car_geom(gap=12)
    for k, (b, far) in enumerate(jets(ctx, nozz, n)):
        fk = 0.6 if far else 1.0
        for j, (ln, w0, w1, col, al) in enumerate(((380, 8, 50, (0.78, 0.88, 1.0), 0.45), (280, 6, 32, (0.92, 0.96, 1.0), 0.7),
                                                     (150, 3, 14, (1, 1, 1), 0.95))):
            pl = torn(plume_pts(b, n, ln, w0, w1, 10, seed=k + j), seed=20 + 7 * k + j, amp=5, step=11)
            poly(ctx, pl, (*col, al * fk))
    # car: red paper cut-out
    drop_shadow(ctx, lambda c, col: poly(c, body, col), off=(8, 10), sigma=5, alpha=0.45)
    for (c, r) in wheels:
        ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
        ctx.set_source_rgb(*INK)
        ctx.fill()
    poly(ctx, body, RED)
    poly(ctx, hi, (1, 1, 1, 0.35))
    poly(ctx, glass, INK, True)
    line(ctx, body + [body[0]], (0.5, 0.1, 0.08, 0.6), 1.5)
    # caption tape
    tape_label(ctx, LINE_A, W / 2, 1000, 50, rot=-0.012)
    grain(surf, 6, seed=21)
    return surf


def b_portrait():
    surf, ctx = new()
    paper_bg(ctx, seed=2, lines=True)
    # background scraps
    poly(ctx, torn([(80, 120), (900, 90), (930, 900), (110, 940)], seed=31, amp=8), hexc("#cfd9df"))
    poly(ctx, torn([(1010, 140), (1840, 110), (1860, 930), (1000, 960)], seed=32, amp=8), hexc("#e6d3c2"))
    # big halftone year numerals as texture (no extra words)
    for (cx, age, expr, rot) in ((480, 0.0, "grin", -0.025), (1440, 1.0, "smile", 0.02)):
        b_toon(ctx, age, expr, cx, 30, 0.95, rot=rot)
    # torn bottom edge where the busts are cut
    poly(ctx, torn([(0, 880), (W, 870), (W, H + 40), (0, H + 40)], seed=33, amp=7), PAPER)
    line(ctx, torn([(0, 880), (W, 870)], seed=33, amp=7)[:-1], (0.4, 0.35, 0.3, 0.25), 1.2)
    # tape at corners
    for (x, y, r) in ((170, 110, -0.6), (800, 92, 0.5), (1100, 120, -0.4), (1760, 112, 0.6)):
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(r)
        poly(ctx, torn([(-60, -16), (60, -16), (60, 16), (-60, 16)], seed=int(x), amp=2, step=6), (0.96, 0.93, 0.8, 0.75))
        ctx.restore()
    tape_label(ctx, Y08, 480, 990, 52, rot=-0.02)
    tape_label(ctx, Y26, 1440, 990, 52, rot=0.015, bg=RED)
    grain(surf, 6, seed=22)
    return surf


def b_sheet():
    """Design sheet (not a video frame): expressions needed for sections 1-2 and the 2026 callback."""
    surf, ctx = new()
    paper_bg(ctx, seed=3, lines=True)
    items = ((260, 0.0, "grin", "2008 · 笑"), (740, 0.0, "low", "2008 · 低谷"), (1200, 0.0, "resolve", "2008 · 不收手"),
             (1660, 1.0, "smile", "2026 · 平静"))
    for i, (cx, age, expr, lab) in enumerate(items):
        b_toon(ctx, age, expr, cx, 100, 0.58, rot=(-0.02, 0.015, -0.01, 0.02)[i])
    poly(ctx, torn([(0, 760), (W, 752), (W, H + 40), (0, H + 40)], seed=35, amp=6), PAPER)
    for (cx, age, expr, lab) in items:
        text(ctx, lab, cx, 850, 40, (0.25, 0.22, 0.2), font="Noto Sans CJK SC", spacing=0.04)
    grain(surf, 6, seed=23)
    return surf


# ====================================================================== C: flat vector motion graphics
C_BG0, C_BG1 = hexc("#141a3c"), hexc("#2b2f6b")


def c_pal(age):
    base = hexc("#f2c4a2") if age < 0.5 else hexc("#ebbb9c")
    sh = hexc("#d9967a") if age < 0.5 else hexc("#cf8f76")
    hi = hexc("#fbd9bf")
    hair = hexc("#4a3226") if age < 0.5 else hexc("#5e5048")
    p = {"s0": mix(sh, (0.4, 0.2, 0.2), 0.25), "s1": sh, "s2": base, "s3": base, "s4": hi, "nostril": hexc("#7a4136"),
         "line": hexc("#2a1a16"), "white": hexc("#ffffff"), "iris": hexc("#4b3022"), "pupil": hexc("#1a0f0b"),
         "catch": hexc("#ffffff"), "lipU": hexc("#c4705f"), "lipL": hexc("#d98a77"), "mline": hexc("#6a2e26"), "mouth": hexc("#5a2420"), "teeth": hexc("#ffffff"),
         "brow": hexc("#3a281e"), "hair": hair, "hair_mid": mix(hair, (1, 1, 1), 0.12), "hair_hi": None, "hair_sh": None,
         "grey": hexc("#c9c1bb"), "jacket": hexc("#232744"), "jacket_hi": hexc("#2e3358"), "shirt": hexc("#ffffff"),
         "shirt_sh": hexc("#dfe3f0"), "tee": hexc("#232744"), "tee_hi": hexc("#2e3358")}
    return p


def c_car():
    surf, ctx = new()
    g = cairo.LinearGradient(0, 0, 0, H)
    g.add_color_stop_rgb(0, *C_BG0)
    g.add_color_stop_rgb(1, *C_BG1)
    ctx.set_source(g)
    ctx.paint()
    rnd = random.Random(2)
    for _ in range(90):
        x, y, r = rnd.uniform(0, W), rnd.uniform(0, 760), rnd.uniform(1, 2.6)
        ctx.arc(x, y, r, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, rnd.uniform(0.3, 0.9))
        ctx.fill()
    ctx.arc(330, 210, 74, 0, 2 * math.pi)
    ctx.set_source_rgb(*hexc("#f4f1ff"))
    ctx.fill()
    ctx.arc(356, 196, 70, 0, 2 * math.pi)
    ctx.set_source_rgb(*C_BG0)
    ctx.fill()
    # layered hills
    for k, (col, base, amp) in enumerate(((hexc("#363b7e"), 860, 40), (hexc("#2a2e63"), 900, 28))):
        pts = [(0, H)]
        for i in range(25):
            x = i * W / 24
            pts.append((x, base - amp * math.sin(i * 0.9 + k)))
        pts.append((W, H))
        poly(ctx, pts, col, True)
    ctx.rectangle(0, TR.ground, W, H - TR.ground)
    ctx.set_source_rgb(*hexc("#1c2048"))
    ctx.fill()
    # truss: clean flat lines
    for (a, b) in truss_lines():
        line(ctx, [a, b], hexc("#5a60a8"), 4)
    cl, strips = track_strips()
    us = underside(cl, strips, 18)
    near = track_rails(cl, -1)
    farr = track_rails(cl, 1)
    # long flat shadow on the ground
    poly(ctx, [(TR.cx - TR.lead, TR.ground + 4), (TR.cx + TR.rx + 40, TR.ground + 4), (TR.cx + TR.rx + 340, TR.ground + 70),
               (TR.cx - TR.lead + 200, TR.ground + 70)], (0.05, 0.06, 0.18, 0.35))
    poly(ctx, near + track_rails(us, -1)[::-1], hexc("#8d93c9"))
    L = (-0.72, 0.36)
    for q, nrm, a in strips:
        k = max(0.0, nrm[0] * L[0] + nrm[1] * L[1])
        c = hexc("#e9ebfa") if k > 0.35 else hexc("#c7cbee")
        path(ctx, q, True, False)
        ctx.set_source_rgb(*c)
        ctx.fill_preserve()
        ctx.set_line_width(1)
        ctx.stroke()
    line(ctx, near, hexc("#ff5468"), 5)
    line(ctx, farr, hexc("#ff5468"), 4)
    line(ctx, track_rails(cl, 0.08), (1, 1, 1, 0.9), 3, dash=[24, 20])
    # jets: rounded puffs
    f, n, body, glass, hi, wheels, nozz = car_geom(gap=12)
    gl, glc = new()
    for k, (b, far) in enumerate(jets(ctx, nozz, n)):
        poly(glc, plume_pts(b, n, 300, 8, 54, 0, seed=k), (0.75, 0.88, 1.0, 0.5))
    comp(ctx, blurred(gl, 18), cairo.OPERATOR_SCREEN)
    for k, (b, far) in enumerate(jets(ctx, nozz, n)):
        poly(ctx, plume_pts(b, n, 260 * (0.85 if far else 1), 7, 40, 0, seed=k), hexc("#bfe0ff") if far else hexc("#d9eeff"), True)
        poly(ctx, plume_pts(b, n, 150, 4, 18, 0, seed=k), (1, 1, 1), True)
        for j in range(4):
            t = 0.55 + 0.15 * j
            cx, cy = b[0] + n[0] * 300 * t, b[1] + n[1] * 300 * t
            ctx.arc(cx + (-1) ** j * 18, cy, 22 + 8 * j, 0, 2 * math.pi)
            ctx.set_source_rgba(0.88, 0.94, 1.0, 0.5 if far else 0.85)
            ctx.fill()
    for (c, r) in wheels:
        ctx.arc(c[0], c[1], r, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#1a1c33"))
        ctx.fill()
        ctx.arc(c[0], c[1], r * 0.5, 0, 2 * math.pi)
        ctx.set_source_rgb(*hexc("#9aa0d6"))
        ctx.fill()
    poly(ctx, body, hexc("#ffffff"))
    lower = [f((-1.0, -0.12)), f((1.0, -0.09)), f((0.97, -0.05)), f((-0.98, -0.06))]
    poly(ctx, lower, hexc("#d4d8f2"))
    poly(ctx, glass, hexc("#3a4fd6"), True)
    poly(ctx, [f((-0.1, -0.39)), f((0.06, -0.4)), f((-0.02, -0.33)), f((-0.16, -0.33))], (1, 1, 1, 0.5))
    # caption pill
    ctx.select_font_face("Noto Sans CJK SC", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(50)
    wid = sum(ctx.text_extents(ch).x_advance for ch in LINE_A) + 0.08 * 50 * (len(LINE_A) - 1)
    x0, y0, w_, h_ = W / 2 - wid / 2 - 40, 952, wid + 80, 82
    r = 41
    ctx.new_sub_path()
    ctx.arc(x0 + w_ - r, y0 + r, r, -math.pi / 2, math.pi / 2)
    ctx.arc(x0 + r, y0 + r, r, math.pi / 2, 3 * math.pi / 2)
    ctx.close_path()
    ctx.set_source_rgba(1, 1, 1, 0.96)
    ctx.fill()
    text(ctx, LINE_A, W / 2, 1010, 50, hexc("#1b1f4a"), font="Noto Sans CJK SC", spacing=0.08)
    return surf


def c_portrait():
    surf, ctx = new()
    ctx.set_source_rgb(*hexc("#f4f2fb"))
    ctx.paint()
    for cx, age, smile, col in ((480, 0.0, 0.7, hexc("#5b6cff")), (1440, 1.0, 0.1, hexc("#ff5d73"))):
        ctx.arc(cx, 470, 360, 0, 2 * math.pi)
        ctx.set_source_rgb(*col)
        ctx.fill()
        ctx.arc(cx, 470, 360, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.12)
        ctx.set_line_width(26)
        ctx.stroke()
        ctx.save()
        ctx.rectangle(cx - 480, 0, 960, 880)
        ctx.clip()
        s = 0.8
        ops = [o for o in head_ops(age, smile) if not (o[0] in ("lidsh",))]
        draw_ops(ctx, ops, cx - 305 * s, 90 - 18 * s, s, c_pal(age))
        ctx.restore()
    ctx.rectangle(0, 880, W, H - 880)
    ctx.set_source_rgb(*hexc("#f4f2fb"))
    ctx.fill()
    text(ctx, Y08, 480, 990, 56, hexc("#1b1f4a"), font="Noto Sans CJK SC", spacing=0.08)
    text(ctx, Y26, 1440, 990, 56, hexc("#1b1f4a"), font="Noto Sans CJK SC", spacing=0.08)
    return surf


# ====================================================================== boards
def board(frames, title, sub, accent, name):
    sc = 0.85
    fw, fh = int(W * sc), int(H * sc)
    BW, BH = 1920, 190 + len(frames) * (fh + 40) + 50
    s, ctx = new(BW, BH)
    ctx.set_source_rgb(*hexc("#101114"))
    ctx.paint()
    text(ctx, title, 144, 92, 54, (1, 1, 1), font="Noto Sans CJK SC", anchor="left", spacing=0.04)
    text(ctx, sub, 144, 150, 28, (0.72, 0.74, 0.8), font="Noto Sans CJK SC", bold=False, anchor="left", spacing=0.02)
    ctx.rectangle(144, 112, 90, 6)
    ctx.set_source_rgb(*accent)
    ctx.fill()
    for i, f in enumerate(frames):
        x, y = (BW - fw) / 2, 190 + i * (fh + 40)
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(sc, sc)
        ctx.set_source_surface(f, 0, 0)
        ctx.paint()
        ctx.restore()
    tmp = os.path.join(OUT, "_tmp.png")
    s.write_to_png(tmp)
    from PIL import Image
    Image.open(tmp).convert("RGB").save(os.path.join(OUT, name), quality=88)
    os.remove(tmp)


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["A", "B", "C"]
    if "A" in which:
        a1, a2 = a_car(), a_portrait()
        a1.write_to_png(os.path.join(OUT, "A_cinematic_apex.png"))
        a2.write_to_png(os.path.join(OUT, "A_cinematic_portrait.png"))
        board([a1, a2], "方向 A · 电影感暗调插画", "夜景硬光 · 明暗色块塑形 · 冷色轮廓光 · 胶片颗粒", hexc("#ff3b4a"), "board_A.jpg")
    if "B" in which:
        b1, b2, b3 = b_car(), b_portrait(), b_sheet()
        b1.write_to_png(os.path.join(OUT, "B_collage_apex.png"))
        b2.write_to_png(os.path.join(OUT, "B_collage_portrait.png"))
        b3.write_to_png(os.path.join(OUT, "B_collage_expressions.png"))
        board([b2, b3], "方向 B · 卡通人物优化稿", "剪纸分层 · 墨线五官 · 网点阴影与腮红 · 白边贴纸", RED, "board_B_toon.jpg")
        board([b1, b2], "方向 B · 新闻剪报拼贴", "剪纸 · 网点印刷 · 胶带字卡 · 纸张纹理", RED, "board_B.jpg")
    if "C" in which:
        c1, c2 = c_car(), c_portrait()
        c1.write_to_png(os.path.join(OUT, "C_flat_apex.png"))
        c2.write_to_png(os.path.join(OUT, "C_flat_portrait.png"))
        board([c1, c2], "方向 C · 扁平矢量动画", "干净色块 · 柔和渐变 · 圆润造型 · 信息图友好", hexc("#5b6cff"), "board_C.jpg")
