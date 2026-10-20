"""Cartoon Musk for the collage look (direction B).

Built as stacked cut-paper layers (body, neck, head, ears, hair) with small
drop shadows between them, halftone dots for shade/blush, and an ink pass for
the features. Head-centred coordinates, face ~400 units wide.

age 0 = 2008, age 1 = 2026.  expr: grin | smile | low | resolve
"""
import math

import cairo
import numpy as np
from scipy import ndimage

from geo import path

INK = (0.16, 0.10, 0.08)
FW, FH = 1000, 1150          # figure canvas (at scale 1)
HC = (500, 470)              # head centre on that canvas


def _mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _mirror(pts):
    return [(-x, y) for x, y in pts]


def _fill(ctx, pts, col, smooth=True):
    path(ctx, pts, True, smooth)
    ctx.set_source_rgba(*col) if len(col) == 4 else ctx.set_source_rgb(*col)
    ctx.fill()


def _ink(ctx, pts, w, col=INK, smooth=True, closed=False):
    path(ctx, pts, closed, smooth)
    ctx.set_source_rgba(*col) if len(col) == 4 else ctx.set_source_rgb(*col)
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def _surf(s):
    w, h = int(FW * s), int(FH * s)
    sf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    c = cairo.Context(sf)
    c.translate(HC[0] * s, HC[1] * s)
    c.scale(s, s)
    return sf, c


def _arr(sf):
    sf.flush()
    return np.ndarray((sf.get_height(), sf.get_width(), 4), np.uint8, buffer=sf.get_data())


def _shadow_of(sf, sigma, dx, dy, alpha):
    a = _arr(sf)[..., 3].astype(np.float32)
    a = ndimage.gaussian_filter(a, sigma)
    a = ndimage.shift(a, (dy, dx), order=0, mode="constant", cval=0.0) * alpha
    out = cairo.ImageSurface(cairo.FORMAT_ARGB32, sf.get_width(), sf.get_height())
    o = _arr(out)
    o[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    out.mark_dirty()
    return out


# ------------------------------------------------------------------ shapes
def face_shape(age):
    j = 14 * age          # heavier, wider jaw with age
    return [(0, -256), (112, -240), (172, -176), (194, -70), (192, 20), (182 + j, 110), (150 + j, 190 + j * 0.4),
            (92 + j * 0.5, 240 + j * 0.5), (0, 254 + j * 0.6), (-92 - j * 0.5, 240 + j * 0.5), (-150 - j, 190 + j * 0.4),
            (-182 - j, 110), (-192, 20), (-194, -70), (-172, -176), (-112, -240)]


EAR = [(186, -64), (222, -84), (244, -44), (238, 18), (216, 58), (188, 48)]
EAR_IN = [(200, -50), (224, -60), (230, -24), (222, 18), (206, 34), (210, 0)]


def hair_shapes(age):
    rec = 10 * age
    outer = [(-198, -40), (-208, -150), (-186, -236), (-140, -290), (-80, -326), (-20, -344), (30, -372),
             (70, -356), (120, -362), (150, -334), (192, -290), (214, -200), (204, -40), (190, -36),
             (182, -128), (160, -168 + rec), (122, -150 + rec), (84, -172), (40, -186), (0, -176),
             (-40, -190), (-84, -176), (-124, -154 + rec), (-162, -170 + rec), (-186, -128), (-188, -36)]
    tuft = [(-60, -190), (-50, -270), (0, -330), (40, -366), (66, -340), (110, -356), (98, -310), (60, -260), (20, -200)]
    side_hi = [(-196, -150), (-180, -232), (-130, -284), (-150, -224), (-172, -168)]
    return outer, tuft, side_hi


# ------------------------------------------------------------------ figure
def figure(age=0.0, expr="grin", outfit=None, s=1.0, seed=0):
    outfit = outfit or ("suit" if age < 0.5 else "tee")
    skin = _mix(_hex("#f3c7a6"), _hex("#eabd9e"), age)
    skin_sh = _mix(_hex("#dc9a7c"), _hex("#d19378"), age)
    hair_c = _mix(_hex("#5a3b2a"), _hex("#5c4638"), age)
    hair_hi = _mix(_hex("#7a5440"), _hex("#7c6656"), age)
    hair_dk = _mix(_hex("#3c261b"), _hex("#3f3029"), age)

    out, oc = _surf(s)
    shade, sc = _surf(s)          # white bg, grey = halftone darkness
    sc.save()
    sc.identity_matrix()
    sc.set_source_rgb(1, 1, 1)
    sc.paint()
    sc.restore()
    blush, bc = _surf(s)
    bc.save()
    bc.identity_matrix()
    bc.set_source_rgb(1, 1, 1)
    bc.paint()
    bc.restore()

    def layer(fn, sh=(6, 7, 5, 0.32)):
        sf, c = _surf(s)
        fn(c)
        if sh:
            oc.save()
            oc.identity_matrix()
            oc.set_source_surface(_shadow_of(sf, sh[2] * s, sh[0] * s, sh[1] * s, sh[3]), 0, 0)
            oc.paint()
            oc.restore()
        oc.save()
        oc.identity_matrix()
        oc.set_source_surface(sf, 0, 0)
        oc.paint()
        oc.restore()

    # ---- body
    def body(c):
        if outfit == "suit":
            _fill(c, [(-130, 250), (130, 250), (150, 690), (-150, 690)], _hex("#f5f1e8"), False)
            _fill(c, [(-420, 690), (-380, 420), (-250, 330), (-110, 280), (-30, 470), (-70, 690)], _hex("#30333b"))
            _fill(c, [(420, 690), (380, 420), (250, 330), (110, 280), (30, 470), (70, 690)], _hex("#2a2d34"))
        else:
            _fill(c, [(-420, 690), (-380, 420), (-250, 320), (-110, 286), (0, 300), (110, 286), (250, 320),
                      (380, 420), (420, 690)], _hex("#24262b"))
    layer(body)

    def neck(c):
        _fill(c, [(-96, 150), (96, 150), (104, 330), (0, 350), (-104, 330)], skin, False)
        _fill(c, [(-96, 190), (96, 190), (100, 280), (0, 300), (-100, 278)], skin_sh)
    layer(neck, None)

    def collar(c):
        if outfit == "suit":
            _fill(c, [(-112, 262), (-40, 300), (0, 392), (-70, 410)], _hex("#ffffff"), False)
            _fill(c, [(112, 262), (40, 300), (0, 392), (70, 410)], _hex("#ebe6dc"), False)
            # lapels
            _fill(c, [(-118, 290), (-180, 340), (-150, 430), (-190, 460), (-60, 690), (-20, 600), (-60, 420)], _hex("#3c4049"), False)
            _fill(c, [(118, 290), (180, 340), (150, 430), (190, 460), (60, 690), (20, 600), (60, 420)], _hex("#353841"), False)
        else:
            _fill(c, [(-112, 292), (-60, 330), (0, 340), (60, 330), (112, 292), (122, 312), (60, 354), (0, 362),
                      (-60, 354), (-122, 312)], _hex("#33363d"))
    layer(collar, (4, 5, 3, 0.35))

    # ---- head
    fshape = face_shape(age)

    def head(c):
        for sx in (1, -1):
            e = [(sx * x, y) for x, y in EAR]
            _fill(c, e, skin)
            _fill(c, [(sx * x, y) for x, y in EAR_IN], skin_sh)
        _fill(c, fshape, skin)
        # shadow plane: camera-right side of the face, under the cheekbone
        _fill(c, [(120, -200), (170, -172), (196, -64), (196, 16), (180 + 14 * age, 100), (136 + 14 * age, 170),
                  (90, 196), (130, 120), (150, 20), (146, -80)], skin_sh)
    layer(head, (8, 10, 6, 0.3))

    # halftone: under-hair band, shade side, under nose, under lower lip, neck
    g = lambda v: (v, v, v)
    _fill(sc, [(-96, 180), (96, 180), (100, 300), (-100, 300)], g(0.6))
    _fill(sc, fshape, g(1.0))
    _fill(sc, [(140, -150), (190, -70), (190, 20), (180, 110), (150, 190), (110, 228), (146, 120), (162, 20), (160, -80)], g(0.5))
    _fill(sc, [(-28, 74), (28, 74), (18, 86), (-18, 86)], g(0.55))
    # rosy cheeks
    for cx in (-120, 120):
        rg = cairo.RadialGradient(cx, 66, 0, cx, 66, 50)
        rg.add_color_stop_rgba(0, 0, 0, 0, 0.55)
        rg.add_color_stop_rgba(1, 0, 0, 0, 0)
        bc.arc(cx, 66, 50, 0, 2 * math.pi)
        bc.set_source(rg)
        bc.fill()

    # ---- hair
    outer, tuft, side_hi = hair_shapes(age)

    def hair(c):
        _fill(c, outer, hair_c)
        _fill(c, tuft, hair_hi)
        _fill(c, side_hi, hair_hi)
        _fill(c, [(x * -1, y) for x, y in side_hi], hair_dk)
        if age > 0.5:   # greying temples
            for sx in (1, -1):
                _fill(c, [(sx * 188, -36), (sx * 204, -40), (sx * 210, -150), (sx * 190, -190), (sx * 182, -128)], _hex("#b9b0a8"))
    layer(hair, (6, 9, 5, 0.38))

    # ---- ink pass (separate layer so halftone sits underneath)
    ink_s, ic = _surf(s)
    fw = 5.0
    _ink(ic, fshape, fw, closed=True)
    for sx in (1, -1):
        _ink(ic, [(sx * x, y) for x, y in EAR], 4.0, closed=False)
        _ink(ic, [(sx * 206, -40), (sx * 224, -30), (sx * 214, 10)], 3.0)
    ic.save()
    path(ic, outer)
    ic.set_operator(cairo.OPERATOR_CLEAR)
    ic.fill()
    ic.restore()
    _ink(ic, outer, 4.5, closed=True)
    for (x0, y0, x1, y1) in ((-150, -200, -120, -268), (-100, -196, -70, -290), (-30, -200, 10, -320), (40, -200, 70, -330),
                             (100, -176, 130, -300), (150, -170, 170, -260)):  # strands swept up and back
        _ink(ic, [(x0, y0), ((x0 + x1) / 2 - 4, (y0 + y1) / 2), (x1, y1)], 2.6, (*INK, 0.55))

    # brows (thick, low, slightly tilted)
    br_in, br_out = {"grin": (0, 0), "smile": (0, 0), "low": (-22, 10), "resolve": (16, -8)}.get(expr, (0, 0))
    for sx in (1, -1):
        brow = [(sx * 46, -100 + br_in), (sx * 96, -110), (sx * 150, -104 + br_out), (sx * 152, -90 + br_out),
                (sx * 96, -94), (sx * 48, -86 + br_in)]
        _fill(ic, brow, _mix(hair_dk, INK, 0.5))

    # eyes
    lid_drop = 4 * age + {"grin": 0, "smile": 2, "low": 8, "resolve": 6}[expr]
    lo_lift = {"grin": 12, "smile": 8, "low": 0, "resolve": 4}[expr]
    for sx in (1, -1):
        cx, cy = sx * 96, -52
        up = [(cx - 40, cy + 2), (cx - 18, cy - 16 + lid_drop), (cx + 14, cy - 17 + lid_drop), (cx + 40, cy)]
        lo = [(cx + 38, cy + 4), (cx + 12, cy + 16 - lo_lift), (cx - 16, cy + 16 - lo_lift), (cx - 38, cy + 6)]
        eye = up + lo
        _fill(ic, eye, (1, 1, 1))
        ic.save()
        path(ic, eye)
        ic.clip()
        ic.arc(cx + sx * -2, cy + 1, 15, 0, 2 * math.pi)
        ic.set_source_rgb(*_hex("#4a3022"))
        ic.fill()
        ic.arc(cx + sx * -2, cy + 1, 8, 0, 2 * math.pi)
        ic.set_source_rgb(*INK)
        ic.fill()
        ic.arc(cx + sx * -2 - 5, cy - 4, 3.6, 0, 2 * math.pi)
        ic.set_source_rgb(1, 1, 1)
        ic.fill()
        ic.restore()
        _ink(ic, up, 6.0)
        _ink(ic, lo[1:3], 2.4)
        if lo_lift > 6:  # smiling cheeks push up the lower lid
            _ink(ic, [(cx - 30, cy + 28), (cx, cy + 34), (cx + 30, cy + 28)], 2.4, (*INK, 0.55))
        if age > 0.5:
            _ink(ic, [(cx - 30, cy + 34), (cx, cy + 42), (cx + 28, cy + 34)], 2.6, (*INK, 0.6))
            for k in range(2):
                ox = cx + sx * 46
                _ink(ic, [(ox, cy - 4 + 12 * k), (ox + sx * 18, cy - 10 + 18 * k)], 2.4, (*INK, 0.6))
        if expr == "low":
            _ink(ic, [(cx - 28, cy + 26), (cx, cy + 32), (cx + 26, cy + 26)], 2.4, (*INK, 0.6))

    # nose
    _fill(ic, [(14, -60), (30, 28), (46, 62), (18, 76), (8, 36)], skin_sh)
    _ink(ic, [(-12, -50), (-20, 26), (-36, 56), (-30, 72), (-12, 76)], 3.4)
    _ink(ic, [(12, 76), (32, 72), (40, 58)], 3.4)
    _fill(ic, [(-12, 70), (-2, 68), (-4, 76), (-14, 76)], INK)
    _fill(ic, [(12, 70), (2, 68), (4, 76), (14, 76)], INK)

    # mouth
    if expr == "grin":
        top = [(-106, 118), (-50, 128), (0, 131), (50, 128), (106, 114)]
        bot = [(98, 126), (54, 170), (0, 180), (-54, 170), (-100, 130)]
        m = top + bot
        _fill(ic, m, _hex("#7a2a24"))
        ic.save()
        path(ic, m)
        ic.clip()
        _fill(ic, [(-110, 108), (110, 104), (110, 146), (0, 152), (-110, 148)], (1, 1, 1))
        _fill(ic, [(-60, 178), (0, 160), (60, 178), (0, 190)], _hex("#d9736a"))
        ic.restore()
        _ink(ic, m, 4.5, closed=True)
        _ink(ic, [(-30, 198), (0, 204), (30, 198)], 3.0, (*INK, 0.6))
        _ink(ic, [(-122, 100), (-114, 122), (-116, 144)], 3.0)
        _ink(ic, [(122, 96), (116, 118), (118, 140)], 3.0)
    elif expr == "smile":
        _ink(ic, [(-90, 130), (-40, 140), (10, 142), (60, 136), (92, 122)], 5.0)
        _ink(ic, [(-30, 164), (0, 168), (30, 164)], 3.0, (*INK, 0.6))
        _ink(ic, [(96, 114), (102, 130)], 3.0)
    elif expr == "low":
        _ink(ic, [(-70, 146), (-30, 138), (20, 138), (68, 148)], 5.0)
        _ink(ic, [(-26, 168), (0, 170), (26, 168)], 3.0, (*INK, 0.6))
    else:  # resolve: tight, one corner pulled
        _ink(ic, [(-76, 138), (-20, 136), (40, 134), (82, 126)], 5.5)
        _ink(ic, [(-24, 160), (0, 163), (24, 160)], 3.0, (*INK, 0.6))
        _ink(ic, [(86, 118), (92, 134)], 3.0)
    if age > 0.5:  # forehead lines, nasolabial folds, double chin
        for k in range(3):
            y = -160 + 20 * k
            _ink(ic, [(-80 + 8 * k, y + 4), (0, y), (80 - 8 * k, y + 4)], 2.4, (*INK, 0.5))
        _ink(ic, [(-46, 80), (-86, 116), (-100, 166)], 2.6, (*INK, 0.55))
        _ink(ic, [(46, 80), (86, 112), (102, 162)], 2.6, (*INK, 0.55))
        _ink(ic, [(-76, 272), (0, 290), (76, 272)], 3.0, (*INK, 0.55))
    if age < 0.5:
        _ink(ic, [(-6, 230), (6, 230)], 2.4, (*INK, 0.5))   # chin dimple

    # body ink
    if outfit == "suit":
        _ink(ic, [(-112, 262), (-40, 300), (0, 392), (40, 300), (112, 262)], 3.0, (*INK, 0.6))
        _ink(ic, [(-118, 290), (-180, 340), (-150, 430), (-190, 460), (-60, 690)], 3.0, (*INK, 0.6))
        _ink(ic, [(118, 290), (180, 340), (150, 430), (190, 460), (60, 690)], 3.0, (*INK, 0.6))
    else:
        _ink(ic, [(-122, 312), (-60, 354), (0, 362), (60, 354), (122, 312)], 3.0, (*INK, 0.6))
    return out, shade, blush, ink_s
