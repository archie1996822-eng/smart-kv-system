"""Stylised (non-photoreal) cartoon rig for the protagonist and side characters.

Local coordinates: origin at the feet, y grows downward, head is at about y=-415.
At scale 1.0 the figure is ~520 px tall.
"""
import math
import random

import cairo

from gfx import hexc, mix, setc, shade, ellipse, circle, rrect, lerp, clamp, poly, fold_poly

SKIN = "#F3CBA2"
SKIN_SHADE = "#E2AC80"
HAIR = "#191A22"

OUTFITS = {
    # young, campus years
    "student": dict(top="#3A8F99", sleeve="short", pants="#2D3753", shoes="#20222C", neck="round"),
    # early Kingsoft years
    "shirt": dict(top="#EEF0F2", sleeve="long", pants="#2E3B5E", shoes="#20222C", neck="collar",
                  trim="#C9CED6"),
    # middle years, jacket over shirt
    "jacket": dict(top="#24304D", sleeve="long", pants="#272C39", shoes="#16171D", neck="jacket",
                   inner="#E9ECEF"),
    # 40+, the familiar dark crew-neck + jeans look
    "sweater": dict(top="#1E2433", sleeve="long", pants="#3B4F78", shoes="#15161B", neck="crew"),
    # side character (senior schoolmate)
    "senior": dict(top="#C5763F", sleeve="short", pants="#3A3A48", shoes="#20222C", neck="round"),
}

POSES = {
    #          aL     bL     aR     bR   (upper-arm angle from straight down, outward +;
    #                                     b = forearm bend relative to upper arm)
    "idle":   (0.14, 0.05, 0.14, 0.05),
    "wave":   (0.14, 0.05, 2.35, 0.55),
    "fist_up": (0.14, 0.05, 2.75, 0.45),
    "chest":  (0.14, 0.05, 0.42, -2.35),
    "think":  (0.14, 0.05, 0.62, -2.55),
    "push":   (1.45, 0.20, 1.45, 0.20),
    "reach":  (0.14, 0.05, 2.45, 0.15),
    "reach2": (2.30, 0.10, 2.30, 0.10),
    "open":   (0.95, 0.25, 0.95, 0.25),
    "hold":   (0.30, -1.25, 0.30, -1.25),
    "fists":  (0.40, -1.95, 0.40, -1.95),
    "point":  (0.14, 0.05, 1.45, 0.05),
    "pointL": (1.45, 0.05, 0.14, 0.05),
    "pocket": (0.06, 0.0, 0.06, 0.0),
    "sad":    (0.08, 0.0, 0.08, 0.0),
    "type":   (0.25, -1.45, 0.25, -1.45),
    "shrug":  (0.75, -1.35, 0.75, -1.35),
    "roll":   (0.35, -2.25, 0.35, -2.25),
}

EXPRS = {
    #              smile  brow   eye       mouth_open
    "neutral":    (0.25, 0.0, "open", 0.0),
    "smile":      (0.65, 0.0, "open", 0.0),
    "happy":      (1.0, -0.1, "happy", 0.55),
    "grin":       (1.0, 0.0, "happy", 0.35),
    "sad":        (-0.6, 0.85, "open", 0.0),
    "tired":      (-0.2, 0.5, "half", 0.0),
    "worried":    (-0.25, 0.75, "open", 0.0),
    "determined": (0.15, -0.65, "open", 0.0),
    "fierce":     (0.45, -0.7, "open", 0.25),
    "shock":      (-0.1, 0.6, "wide", 0.65),
    "calm":       (0.35, 0.1, "half", 0.0),
    "closed":     (0.3, 0.2, "closed", 0.0),
    "shout":      (0.6, -0.55, "happy", 0.8),
}


def blend_pose(a, b, t):
    pa = POSES[a] if isinstance(a, str) else a
    pb = POSES[b] if isinstance(b, str) else b
    return tuple(lerp(pa[i], pb[i], t) for i in range(4))


def blend_expr(a, b, t):
    ea = EXPRS[a] if isinstance(a, str) else a
    eb = EXPRS[b] if isinstance(b, str) else b
    return (lerp(ea[0], eb[0], t), lerp(ea[1], eb[1], t), ea[2] if t < 0.5 else eb[2], lerp(ea[3], eb[3], t))


def _quad(ax, ay, bx, by, w0, w1):
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    return [(ax + nx * w0 / 2, ay + ny * w0 / 2), (bx + nx * w1 / 2, by + ny * w1 / 2),
            (bx - nx * w1 / 2, by - ny * w1 / 2), (ax - nx * w0 / 2, ay - ny * w0 / 2)]


def _strip(ctx, ax, ay, bx, by, w0, w1, c):
    """A folded paper strip: two tones split along its length."""
    q = _quad(ax, ay, bx, by, w0, w1)
    m0 = ((q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2)
    m1 = ((q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2)
    setc(ctx, shade(c, 0.06))
    poly(ctx, [q[0], q[1], m1, m0])
    ctx.fill()
    setc(ctx, shade(c, -0.12))
    poly(ctx, [m0, m1, q[2], q[3]])
    ctx.fill()


def _hand(ctx, x, y, r):
    pts = [(x + math.cos(a) * r, y + math.sin(a) * r) for a in [i * math.tau / 6 + 0.3 for i in range(6)]]
    setc(ctx, shade(SKIN, 0.04))
    poly(ctx, pts[:4])
    ctx.fill()
    setc(ctx, shade(SKIN, -0.1))
    poly(ctx, pts[3:] + pts[:1])
    ctx.fill()


def _limb(ctx, x0, y0, a, b, l1, l2, w, side, sleeve_col, skin_col, short_sleeve, fist=False):
    sx = -1 if side == "L" else 1
    ex = x0 + sx * math.sin(a) * l1
    ey = y0 + math.cos(a) * l1
    a2 = a + b
    hx = ex + sx * math.sin(a2) * l2
    hy = ey + math.cos(a2) * l2
    if short_sleeve:
        _strip(ctx, x0, y0, ex, ey, w * 0.8, w * 0.72, skin_col)
        _strip(ctx, ex, ey, hx, hy, w * 0.72, w * 0.62, skin_col)
        _strip(ctx, x0, y0, lerp(x0, ex, 0.55), lerp(y0, ey, 0.55), w * 1.15, w * 1.05, sleeve_col)
    else:
        _strip(ctx, x0, y0, ex, ey, w * 1.02, w * 0.92, sleeve_col)
        _strip(ctx, ex, ey, lerp(ex, hx, 0.86), lerp(ey, hy, 0.86), w * 0.92, w * 0.82, shade(sleeve_col, -0.04))
        setc(ctx, shade(sleeve_col, -0.02))
        circle(ctx, ex, ey, w * 0.46)
        ctx.fill()
    _hand(ctx, hx, hy, w * 0.6)
    return hx, hy


def person(ctx, x, y, s=1.0, **kw):
    """Origami-style character with a paper drop shadow. Returns anchor points in device space."""
    alpha = kw.pop("alpha", 1.0)
    ctx.push_group()
    info = _person(ctx, x, y, s, **kw)
    pat = ctx.pop_group()
    ctx.save()
    for k, a in ((1.0, 0.5), (0.65, 0.3), (1.4, 0.2)):
        ctx.save()
        ctx.translate(9 * s * k, 12 * s * k)
        ctx.set_source_rgba(0.05, 0.03, 0.08, 0.3 * a * alpha)
        ctx.mask(pat)
        ctx.restore()
    ctx.set_source(pat)
    ctx.paint_with_alpha(alpha)
    ctx.restore()
    return info


def _person(ctx, x, y, s=1.0, outfit="sweater", pose="idle", expr="neutral", t=0.0,
            walk=None, facing="front", look=(0.0, 0.0), tilt=0.0, hair_grey=0.0,
            glasses=False, hair_style="lei", seed=0, breathe=True,
            sit=False, blush=0.25, sweat=0.0, flip=False):
    o = OUTFITS[outfit] if isinstance(outfit, str) else outfit
    arms = POSES[pose] if isinstance(pose, str) else pose
    ex_ = EXPRS[expr] if isinstance(expr, str) else expr
    smile, brow, eye, mouth_open = ex_

    ctx.save()
    ctx.translate(x, y)
    ctx.scale(-s if flip else s, s)

    bob = 0.0
    lift = [0.0, 0.0]
    swing = 0.0
    if walk is not None:
        bob = abs(math.sin(walk)) * 7
        lift = [max(0.0, math.sin(walk)) * 20, max(0.0, -math.sin(walk)) * 20]
        swing = math.sin(walk) * 0.22
    br = math.sin(t * 2.2 + seed) * 2.2 if breathe else 0.0

    hip_y = -165 + (70 if sit else 0)
    leg_len = 160 - (70 if sit else 0)
    body_dy = -bob + (70 if sit else 0)

    # legs: tapered paper strips + folded shoes
    for i, lx in enumerate((-28, 28)):
        ly = -lift[i]
        _strip(ctx, lx, hip_y - 10, lx + (2 if lx > 0 else -2), -16 + ly, 50, 42, o["pants"])
        so = -8 if lx < 0 else 8
        setc(ctx, shade(o["shoes"], 0.12))
        poly(ctx, [(lx - 26 + so, -2 + ly), (lx + so * 0.2, -26 + ly), (lx + 26 + so, -2 + ly)])
        ctx.fill()
        setc(ctx, o["shoes"])
        poly(ctx, [(lx - 26 + so, -2 + ly), (lx + 26 + so, -2 + ly), (lx + 22 + so, 6 + ly), (lx - 22 + so, 6 + ly)])
        ctx.fill()
    if sit:
        setc(ctx, shade(o["pants"], -0.12))
        poly(ctx, [(-58, hip_y - 26), (58, hip_y - 26), (52, hip_y + 12), (-52, hip_y + 12)])
        ctx.fill()

    ctx.translate(0, body_dy + br * 0.3)

    # torso: folded down the middle (left lit, right in shade)
    top = o["top"]
    torso = [(0, -165), (-62, -168), (-80, -316), (-52, -344), (0, -348), (52, -344), (80, -316), (62, -168)]
    if facing == "front":
        fold_poly(ctx, torso, top, (0, 4), k_dark=-0.13, k_light=0.05)
    else:
        fold_poly(ctx, torso, top, (0, 4), k_dark=-0.05, k_light=-0.16)
    setc(ctx, shade(top, -0.22))
    poly(ctx, [(-62, -168), (62, -168), (60, -182), (-60, -182)])
    ctx.fill()

    if facing == "front":
        neck = o.get("neck")
        if neck == "jacket":
            setc(ctx, o["inner"])
            poly(ctx, [(-26, -346), (26, -346), (0, -250)])
            ctx.fill()
            setc(ctx, shade(top, 0.16))
            poly(ctx, [(-32, -346), (-6, -262), (-30, -282)])
            ctx.fill()
            setc(ctx, shade(top, -0.02))
            poly(ctx, [(32, -346), (6, -262), (30, -282)])
            ctx.fill()
            setc(ctx, shade(top, -0.3))
            ctx.set_line_width(3)
            ctx.move_to(0, -250)
            ctx.line_to(0, -170)
            ctx.stroke()
        elif neck == "collar":
            setc(ctx, o.get("trim", "#ccc"))
            for by in (-292, -258, -224, -190):
                poly(ctx, [(0, by - 4), (4, by), (0, by + 4), (-4, by)])
                ctx.fill()
            setc(ctx, "#FFFFFF")
            poly(ctx, [(-30, -350), (-2, -318), (-34, -312)])
            ctx.fill()
            setc(ctx, "#E3E6EA")
            poly(ctx, [(30, -350), (2, -318), (34, -312)])
            ctx.fill()
        elif neck in ("round", "crew"):
            setc(ctx, shade(top, -0.25 if neck == "round" else 0.14))
            poly(ctx, [(-26, -347), (26, -347), (14, -328), (-14, -328)])
            ctx.fill()

    # arms
    aL, bL, aR, bR = arms
    if walk is not None:
        aL += swing
        aR -= swing
    short = o.get("sleeve") == "short"
    hands = {}
    for side, a, b, sx in (("L", aL, bL, -70), ("R", aR, bR, 70)):
        hands[side] = _limb(ctx, sx, -318, a, b, 84, 80, 34, side, shade(top, -0.03), SKIN, short)

    # neck
    setc(ctx, SKIN_SHADE)
    poly(ctx, [(-16, -364), (16, -364), (14, -336), (-14, -336)])
    ctx.fill()

    # head
    ctx.save()
    ctx.translate(0, -415)
    ctx.rotate(tilt)
    hair = mix(HAIR, "#9A9CA6", hair_grey)
    lx, ly = look
    face = [(-88 * math.sin(a) * (0.97 if math.cos(a) < 0 else 1.0), -86 * math.cos(a))
            for a in (k * math.tau / 14 for k in range(14))]
    for sxe in (-1, 1):
        setc(ctx, SKIN_SHADE if sxe < 0 else shade(SKIN_SHADE, -0.08))
        poly(ctx, [(sxe * 76, -18), (sxe * 98, -2), (sxe * 90, 26), (sxe * 74, 30)])
        ctx.fill()
    if facing == "front":
        fold_poly(ctx, face, SKIN, (0, 7), k_dark=-0.07, k_light=0.03)
        setc(ctx, hair)
        if hair_style == "lei":
            cap = [(-86, 8), (-92, -40), (-68, -94), (-18, -112), (40, -108), (78, -84), (92, -40), (87, 8),
                   (78, -28), (58, -58), (24, -66), (-30, -56), (-62, -48), (-78, -14)]
            setc(ctx, hair)
            poly(ctx, cap)
            ctx.fill()
            setc(ctx, shade(hair, -0.25))
            poly(ctx, [(40, -108), (78, -84), (92, -40), (87, 8), (78, -28), (58, -58), (24, -66)])
            ctx.fill()
            # folded fringe flap sweeping from the side part
            setc(ctx, shade(hair, 0.22))
            poly(ctx, [(34, -104), (-64, -50), (-30, -56), (22, -66)])
            ctx.fill()
            setc(ctx, shade(hair, 0.4))
            ctx.set_line_width(2)
            ctx.move_to(34, -104)
            ctx.line_to(-64, -50)
            ctx.stroke()
        elif hair_style == "flat":
            cap = [(-86, 4), (-88, -56), (-50, -102), (50, -102), (88, -56), (86, 4), (74, -40), (48, -56),
                   (-48, -56), (-74, -40)]
            fold_poly(ctx, cap, hair, (2, 4), k_dark=-0.15, k_light=0.12)
        elif hair_style == "bun":
            poly(ctx, [(-30, -100), (0, -136), (30, -100)])
            ctx.fill()
            cap = [(-86, 10), (-86, -60), (-40, -98), (40, -98), (86, -60), (86, 10), (60, -44), (0, -62), (-60, -44)]
            poly(ctx, cap)
            ctx.fill()

        # brows: little paper strips
        setc(ctx, shade(hair, 0.05))
        for sxe in (-1, 1):
            inner_y = -36 - brow * 8
            outer_y = -36 + brow * 4
            poly(ctx, [(sxe * 16, inner_y - 4), (sxe * 50, outer_y - 4), (sxe * 48, outer_y + 4), (sxe * 16, inner_y + 4)])
            ctx.fill()

        bl = (t + seed * 1.37) % 3.9
        blink = 1.0 - (math.sin(clamp(bl / 0.16) * math.pi) if bl < 0.16 else 0.0)
        setc(ctx, "#1C1C24")
        for sxe in (-1, 1):
            exx, eyy = sxe * 32 + lx * 6, -8 + ly * 5
            if eye == "happy":
                ctx.set_line_width(6)
                ctx.move_to(exx - 10, eyy + 2)
                ctx.line_to(exx, eyy - 7)
                ctx.line_to(exx + 10, eyy + 2)
                ctx.stroke()
            elif eye == "closed" or blink < 0.25:
                ctx.set_line_width(5)
                ctx.move_to(exx - 10, eyy - 2)
                ctx.line_to(exx, eyy + 4)
                ctx.line_to(exx + 10, eyy - 2)
                ctx.stroke()
            else:
                ry = {"open": 10, "wide": 13, "half": 6}[eye] * blink
                rx = 7.5 if eye != "wide" else 9
                poly(ctx, [(exx, eyy - ry), (exx + rx, eyy), (exx, eyy + ry), (exx - rx, eyy)])
                ctx.fill()
                setc(ctx, "#FFFFFF", 0.9)
                poly(ctx, [(exx + 2, eyy - 5), (exx + 4.5, eyy - 3), (exx + 2, eyy - 1), (exx - 0.5, eyy - 3)])
                ctx.fill()
                setc(ctx, "#1C1C24")

        # nose: a tiny folded triangle
        setc(ctx, SKIN_SHADE)
        poly(ctx, [(lx * 3, 2), (lx * 3 + 8, 20), (lx * 3 - 6, 20)])
        ctx.fill()

        if blush > 0:
            setc(ctx, "#F2918A", blush)
            for sxe in (-1, 1):
                poly(ctx, [(sxe * 52 - 15, 26), (sxe * 52, 18), (sxe * 52 + 15, 26), (sxe * 52, 33)])
                ctx.fill()

        my = 42
        mw = 26 + smile * 10
        if mouth_open > 0.05:
            h = 6 + mouth_open * 22
            setc(ctx, "#7A2E2E")
            poly(ctx, [(-mw, my - 2), (mw, my - 2), (mw * 0.45, my + h), (-mw * 0.45, my + h)])
            ctx.fill()
            if smile > 0.3:
                setc(ctx, "#FFFFFF")
                poly(ctx, [(-mw * 0.85, my), (mw * 0.85, my), (mw * 0.65, my + 7), (-mw * 0.65, my + 7)])
                ctx.fill()
        else:
            setc(ctx, "#8A3A34")
            ctx.set_line_width(5.5)
            ctx.set_line_join(cairo.LINE_JOIN_MITER)
            ctx.move_to(-mw * 0.8, my - smile * 2)
            ctx.line_to(0, my + smile * 10)
            ctx.line_to(mw * 0.8, my - smile * 2)
            ctx.stroke()

        if hair_style == "lei":
            # round black frames
            for sxe in (-1, 1):
                gx = sxe * 32 + lx * 4
                circle(ctx, gx, -8, 22)
                setc(ctx, "#FFFFFF", 0.12)
                ctx.fill_preserve()
                setc(ctx, "#15151B")
                ctx.set_line_width(5.5)
                ctx.stroke()
                ctx.move_to(sxe * 54 + lx * 4, -12)
                ctx.line_to(sxe * 80, -16)
                ctx.set_line_width(4.5)
                ctx.stroke()
            ctx.move_to(-10 + lx * 4, -12)
            ctx.curve_to(-4 + lx * 4, -17, 4 + lx * 4, -17, 10 + lx * 4, -12)
            ctx.set_line_width(4.5)
            ctx.stroke()
        elif glasses:
            setc(ctx, "#2A2A33")
            ctx.set_line_width(4)
            for sxe in (-1, 1):
                ctx.rectangle(sxe * 32 - 20, -24, 40, 30)
                ctx.stroke()
            ctx.move_to(-12, -12)
            ctx.line_to(12, -12)
            ctx.stroke()

        if sweat > 0:
            setc(ctx, "#9ED8FF", sweat)
            poly(ctx, [(70, -40), (80, -14), (70, -6), (60, -14)])
            ctx.fill()
    else:
        fold_poly(ctx, face, SKIN, (0, 7), k_dark=-0.12, k_light=-0.02)
        cap = [(0, -106), (-58, -96), (-92, -40), (-86, 20), (-56, 54), (0, 62), (56, 54), (86, 20), (92, -40), (58, -96)]
        fold_poly(ctx, cap, hair, (0, 5), k_dark=-0.2, k_light=0.1)
    ctx.restore()

    head = ctx.user_to_device(0, -415)
    hl = ctx.user_to_device(*hands["L"])
    hr = ctx.user_to_device(*hands["R"])
    ctx.restore()
    return {"head": head, "handL": hl, "handR": hr, "top": (x, y - 525 * s)}


def silhouette(ctx, x, y, s, c, seed=0, t=0.0, nod=0.0):
    """Simple crowd figure (head + shoulders), cut-paper style."""
    rnd = random.Random(seed)
    hw = rnd.uniform(0.9, 1.15)
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(s * hw, s)
    fold_poly(ctx, [(0, 40), (-95, 40), (-92, -50), (-60, -92), (0, -98), (60, -92), (92, -50), (95, 40)], c, (0, 4),
              k_dark=-0.3, k_light=0.12)
    ctx.rotate(math.sin(t * 5 + seed) * nod)
    head = [(0, -210), (-40, -196), (-52, -150), (-40, -104), (0, -92), (40, -104), (52, -150), (40, -196)]
    fold_poly(ctx, head, c, (0, 4), k_dark=-0.3, k_light=0.12)
    ctx.restore()
