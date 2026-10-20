"""Shared geometry for the v3 style exploration.

Face/bust shapes are traced from the proportions of the reference portrait
(576x1024 reference pixels, head turned slightly to camera-left), then rendered
by each style with its own palette / treatment. Track + car follow the real demo:
a half-loop ramp whose top end curls back over, car hanging inverted at the lip.
"""
import math

import cairo


# ---------------------------------------------------------------- path helpers
def path(ctx, pts, closed=True, smooth=True):
    n = len(pts)
    if n < 2:
        return
    if not smooth or n < 3:
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        if closed:
            ctx.close_path()
        return
    ctx.move_to(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[i - 1] if (closed or i > 0) else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        ctx.curve_to(c1[0], c1[1], c2[0], c2[1], p2[0], p2[1])
    if closed:
        ctx.close_path()


def ellipse_pts(cx, cy, rx, ry, n=16):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


# ---------------------------------------------------------------- head ops
# op = (key, kind, pts, extra) ; kind in poly | spoly (smooth) | line | sline
def head_ops(age=0.0, smile=0.6, outfit=None):
    a = age
    outfit = outfit or ("suit" if a < 0.5 else "tee")

    def W(pts):
        out = []
        for x, y in pts:
            if y > 540:
                k = min(1.0, (y - 540) / 220)
                x = 310 + (x - 310) * (1 + 0.12 * a * k)
                y = y + 18 * a * k
            out.append((x, y))
        return out

    ops = []

    def add(key, kind, pts, extra=None, warp=True):
        ops.append((key, kind, W(pts) if warp else pts, extra))

    # neck (drawn first so the outfit sits on top)
    add("s1", "spoly", [(176, 640), (456, 630), (466, 820), (420, 880), (330, 910), (230, 880), (166, 820)])
    add("s0", "spoly", [(150, 660), (200, 720), (260, 756), (330, 770), (404, 756), (462, 712), (470, 770),
                        (420, 810), (330, 830), (230, 812), (160, 770)])
    # -- body
    if outfit == "suit":
        add("shirt", "poly", [(110, 800), (238, 786), (330, 904), (420, 782), (530, 792), (610, 1130), (30, 1130)], warp=False)
        add("shirt_sh", "poly", [(150, 772), (214, 780), (318, 914), (262, 968)], warp=False)
        add("shirt", "poly", [(476, 768), (520, 780), (410, 966), (344, 914)], warp=False)
        add("shirt_sh", "poly", [(330, 904), (344, 914), (330, 1130), (318, 914)], warp=False)
        add("jacket", "spoly", [(-260, 1130), (-180, 930), (-20, 850), (120, 800), (190, 930), (300, 1130)], warp=False)
        add("jacket", "spoly", [(880, 1130), (800, 930), (640, 840), (520, 790), (450, 930), (360, 1130)], warp=False)
        add("jacket_hi", "spoly", [(-200, 1130), (-140, 960), (-20, 880), (60, 860), (0, 1000), (-60, 1130)], warp=False)
    else:
        add("tee", "spoly", [(-260, 1130), (-170, 920), (40, 846), (180, 820), (250, 862), (330, 878), (410, 860),
                             (470, 816), (620, 846), (810, 920), (890, 1130)], warp=False)
        add("tee_hi", "spoly", [(-200, 1130), (-130, 950), (40, 876), (120, 860), (60, 1000), (0, 1130)], warp=False)
        add("tee_hi", "sline", [(180, 822), (250, 864), (330, 880), (410, 862), (470, 818)], 14, warp=False)

    # -- ears
    add("s2", "spoly", [(66, 392), (38, 372), (18, 402), (16, 456), (30, 514), (52, 558), (80, 570)])
    add("s1", "spoly", [(50, 410), (34, 424), (36, 480), (52, 524), (64, 500), (58, 450)])
    add("s1", "spoly", [(510, 440), (538, 424), (556, 452), (556, 520), (540, 570), (508, 596)])
    add("s0", "spoly", [(526, 456), (540, 472), (538, 530), (524, 560), (520, 500)])

    # -- face base
    face = [(62, 300), (52, 380), (58, 460), (72, 545), (98, 620), (132, 682), (180, 728), (250, 764), (322, 778),
            (398, 764), (452, 726), (488, 672), (510, 604), (522, 528), (530, 448), (526, 360), (510, 280),
            (470, 200), (400, 150), (300, 135), (200, 150), (120, 205)]
    add("s2", "spoly", face)
    add("_face", "spoly", face)  # silhouette marker for effects (not drawn)

    # -- planes of light and shade (key light camera-left, slightly above)
    add("s3", "spoly", [(120, 236), (190, 178), (290, 150), (380, 162), (440, 206), (430, 300), (392, 336),
                        (300, 340), (200, 338), (130, 330), (104, 290)])
    add("s4", "spoly", [(186, 206), (236, 182), (300, 176), (346, 196), (330, 226), (282, 250), (232, 262), (196, 244)])
    add("s1", "spoly", [(452, 214), (496, 262), (522, 340), (530, 450), (500, 420), (482, 340), (462, 280)])
    add("s1", "spoly", [(500, 420), (530, 450), (522, 528), (510, 604), (488, 672), (452, 726), (398, 764),
                        (420, 720), (452, 660), (474, 590), (484, 510)])
    add("s0", "spoly", [(510, 520), (522, 528), (510, 604), (488, 672), (460, 714), (476, 650), (496, 590)])
    add("s1", "spoly", [(56, 470), (72, 545), (98, 620), (132, 682), (142, 660), (108, 590), (90, 516), (84, 452)], 0)
    # brow ridge catches light, sockets fall into shade
    add("s3", "spoly", [(140, 352), (210, 330), (290, 340), (300, 360), (220, 352), (150, 366)])
    add("fold", "spoly", [(146, 376), (200, 362), (276, 366), (304, 394), (292, 426), (240, 434), (188, 430), (150, 410)])
    add("s1", "spoly", [(338, 378), (398, 360), (474, 356), (502, 384), (490, 418), (430, 430), (376, 426), (344, 404)])
    add("s1", "spoly", [(150, 380), (200, 366), (272, 370), (282, 386), (230, 380), (180, 388)])
    add("s0", "spoly", [(268, 370), (300, 376), (312, 398), (296, 404), (280, 386)])
    add("s0", "spoly", [(340, 380), (358, 372), (372, 384), (350, 400)])
    add("s0", "spoly", [(440, 362), (486, 366), (502, 386), (480, 384)])
    # cheeks: broad lit plane on the near side, gentle fall-off
    add("s3", "spoly", [(92, 436), (176, 432), (250, 452), (258, 488), (226, 520), (178, 540), (124, 528), (94, 490)])
    add("s3", "spoly", [(392, 456), (444, 448), (464, 470), (446, 500), (404, 504)])
    # nose
    add("s1", "spoly", [(334, 392), (352, 436), (376, 486), (366, 508), (340, 490)])
    add("s3", "spoly", [(290, 400), (304, 396), (302, 470), (284, 494), (274, 486)])
    add("s4", "spoly", [(306, 392), (324, 392), (330, 462), (318, 486), (300, 462)])
    add("s1", "spoly", [(268, 514), (300, 532), (326, 538), (356, 532), (392, 516), (376, 548), (322, 556), (278, 546)])
    add("s0", "spoly", [(286, 534), (322, 544), (360, 536), (340, 552), (304, 552)])
    add("s3", "spoly", [(258, 494), (280, 484), (298, 512), (280, 528), (260, 518)])
    add("s2", "spoly", [(362, 484), (386, 492), (394, 516), (374, 528), (356, 512)])
    add("s3", "spoly", ellipse_pts(318, 500, 22, 16, 12))
    add("s4", "spoly", ellipse_pts(312, 494, 10, 7, 8))
    add("nostril", "spoly", ellipse_pts(292, 524, 12, 5.5, 8))
    add("nostril", "spoly", ellipse_pts(350, 524, 12, 5.5, 8))
    add("s1", "sline", [(260, 498), (254, 516), (274, 532), (294, 530)], 2.6)
    add("s1", "sline", [(390, 496), (396, 516), (374, 532), (352, 530)], 2.6)
    # nasolabial folds: tapered wedges (deeper with age)
    fk = "s1" if a > 0.5 else "fold"
    add(fk, "spoly", [(256, 512), (268, 516), (246, 560), (238, 608), (226, 604), (230, 556)])
    add(fk, "spoly", [(392, 508), (404, 510), (428, 550), (444, 596), (432, 600), (414, 554)])
    add("s3", "spoly", [(268, 520), (300, 552), (250, 590), (244, 560)])
    add("s1" if a < 0.5 else "s0", "sline", [(258, 516), (238, 560), (230, 604)], 2.0 + 3 * a)
    add("s1" if a < 0.5 else "s0", "sline", [(396, 512), (420, 552), (436, 596)], 2.0 + 3 * a)
    # under lower lip, chin
    add("s1", "spoly", [(268, 640), (330, 650), (392, 636), (384, 662), (330, 674), (278, 662)])
    add("s3", "spoly", [(268, 686), (330, 676), (390, 686), (380, 730), (330, 748), (282, 728)])
    add("s4", "spoly", [(300, 694), (334, 690), (356, 700), (346, 718), (310, 718)])

    # -- mouth
    sm = 10 * smile
    lc, rc = (228, 606 - sm), (434, 596 - sm)
    if smile > 0.5:  # parted-lip grin, upper teeth showing
        add("lipU", "spoly", [lc, (262, 588), (298, 581), (322, 586), (346, 580), (390, 582), rc, (394, 594), (330, 597), (266, 599)])
        add("mouth", "spoly", [(lc[0] + 6, lc[1] + 1), (266, 599), (330, 597), (394, 594), (rc[0] - 6, rc[1] + 1), (402, 610), (330, 624), (262, 616)])
        add("teeth", "spoly", [(252, 600), (330, 598), (410, 594), (398, 607), (330, 611), (262, 609)])
        add("lipL", "spoly", [(246, 614), (330, 626), (418, 604), (408, 630), (332, 648), (262, 638)])
        add("s3", "spoly", [(290, 630), (334, 634), (378, 628), (352, 640), (310, 640)])
        add("mline", "sline", [lc, (266, 600), (330, 598), (394, 595), rc], 3.0)
    else:
        add("lipU", "spoly", [lc, (262, 592), (298, 586), (322, 591), (346, 585), (388, 587), rc, (392, 602), (330, 606), (270, 606)])
        add("lipL", "spoly", [(240, 608), (330, 610), (422, 600), (404, 624), (332, 640), (262, 630)])
        add("s3", "spoly", [(290, 616), (334, 618), (372, 614), (350, 628), (310, 628)])
        add("mline", "sline", [lc, (274, 607), (330, 609), (386, 604), rc], 4.2)
    add("s1", "sline", [(lc[0] - 6, lc[1] - 6), (lc[0] - 2, lc[1] + 6)], 3)
    add("s1", "sline", [(rc[0] + 6, rc[1] - 6), (rc[0] + 2, rc[1] + 6)], 3)

    # -- eyes (narrow, deep-set; lower lids lift when smiling)
    lift = 7 * smile + 2
    for (ox, ix_, up, lo, crease, lcrease, iris) in (
        ((178, 401), (276, 399), [(202, 386), (232, 379), (260, 384)], [(252, 409 - lift), (222, 412 - lift), (194, 407 - lift)],
         [(186, 380), (230, 365), (272, 378)], [(190, 420), (230, 426), (268, 416)], (229, 397)),
        ((468, 393), (364, 399), [(444, 381), (415, 377), (386, 383)], [(388, 406 - lift), (414, 409 - lift), (444, 403 - lift)],
         [(464, 371), (414, 361), (370, 379)], [(462, 412), (416, 424), (376, 416)], (415, 394)),
    ):
        up = [(x, y + 4 * smile) for x, y in up]
        almond = [ox] + up + [ix_] + lo
        add("white", "spoly", almond)
        add("_clip", "spoly", almond)
        add("iris", "spoly", ellipse_pts(iris[0], iris[1] + 2, 18.5, 18.5, 12))
        add("pupil", "spoly", ellipse_pts(iris[0], iris[1] + 2, 7.5, 7.5, 8))
        add("catch", "spoly", ellipse_pts(iris[0] - 6, iris[1] - 3, 3.4, 3.4, 6))
        add("lidsh", "spoly", [ox] + up + [ix_] + [(ix_[0], ix_[1] - 30), (ox[0], ox[1] - 30)])
        add("lidsh", "spoly", [ox] + [(p[0], p[1] + 6) for p in up] + [ix_] + [(ix_[0], ix_[1] - 30), (ox[0], ox[1] - 30)])
        add("_unclip", "none", [])
        add("line", "sline", [ox] + up + [ix_], 4.6)
        add("line", "sline", [ox, lo[-1], lo[-2]], 2.0)
        add("s0", "sline", crease, 3.0 + 1.5 * a)
        add("s1", "sline", lcrease, 2.6 + 2.4 * a)
        if a > 0.01:
            bag = [(p[0], p[1] + 14) for p in lcrease]
            add("s1", "sline", bag, 4.0 * a)
            sgn = 1 if ox[0] > 300 else -1
            for k in range(3):
                add("s1", "sline", [(ox[0] + sgn * 8, ox[1] - 6 + 10 * k), (ox[0] + sgn * 30, ox[1] - 14 + 16 * k)], 2.2 * a)

    # forehead lines with age
    if a > 0.01:
        for k, y in enumerate((214, 238, 262)):
            add("s1", "sline", [(196 + 10 * k, y + 6), (300, y), (404 - 10 * k, y + 4)], 2.6 * a)
        add("s1", "sline", [(250, 772), (320, 790), (392, 772)], 5 * a)   # double chin
        add("s1", "sline", [(196, 690), (208, 730)], 4 * a)                # jowl folds
        add("s1", "sline", [(444, 680), (432, 720)], 4 * a)

    # -- brows
    add("brow", "spoly", [(145, 366), (170, 350), (205, 342), (245, 342), (284, 352), (282, 363), (245, 356), (205, 356), (170, 362), (150, 374)])
    add("brow", "spoly", [(352, 362), (354, 350), (392, 339), (435, 333), (470, 336), (496, 348), (490, 356), (465, 348), (432, 346), (394, 352)])

    # -- hair (short, textured, swept up and back; hairline recedes at the temples)
    import random
    rnd = random.Random(7)
    top = []
    for i in range(41):
        t = i / 40
        ang = math.pi * (1.05 - 1.10 * t)
        r = 1.0 + 0.035 * abs(math.sin(i * 1.7)) + 0.02 * math.sin(i * 0.9)
        top.append((300 + 262 * r * math.cos(ang), 262 - 246 * r * math.sin(ang)))
    inner = [(546, 428), (528, 442), (518, 362), (506, 292), (476, 234), (436, 194), (390, 166), (330, 154),
             (262, 156), (196, 172), (140, 212), (96, 274), (72, 340), (60, 398)]
    rec = 10 * a
    inner = [(x, y + (rec if (x < 200 or x > 420) and y < 320 else 0)) for x, y in inner]
    hair = [(56, 400)] + top[1:-1] + inner[:-1]
    add("hair", "spoly", hair, warp=False)
    add("_hair", "spoly", hair, warp=False)
    add("hair_sh", "spoly", [(500, 220), (536, 220), (552, 290), (552, 380), (540, 430), (528, 440), (518, 362),
                             (508, 292)], warp=False)
    add("_clip", "spoly", hair, warp=False)
    # clumps: lit upper planes of the tufts
    for cx, cy, w, h, rot in ((170, 120, 70, 30, -0.7), (240, 76, 80, 28, -0.4), (318, 62, 84, 26, -0.1),
                              (392, 84, 76, 26, 0.3), (452, 126, 64, 24, 0.6), (118, 190, 52, 24, -1.1),
                              (210, 140, 60, 22, -0.5), (290, 120, 70, 22, -0.2), (370, 130, 66, 22, 0.2)):
        pts = []
        for k in range(10):
            th = 2 * math.pi * k / 10
            x, y = w * math.cos(th), h * math.sin(th) * (0.6 if math.sin(th) > 0 else 1.0)
            pts.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
        add("hair_mid", "spoly", pts, warp=False)
    add("hair_mid", "spoly", [(226, 162), (250, 118), (292, 86), (346, 88), (384, 120), (370, 156), (300, 146)], warp=False)
    for _ in range(70):
        x0 = rnd.uniform(110, 500)
        y0 = rnd.uniform(110, 230) - 0.0025 * (x0 - 300) ** 2 * 0.0 + abs(x0 - 300) * 0.25
        ang = -math.pi / 2 + (x0 - 300) / 420 + rnd.uniform(-0.25, 0.25)
        ln = rnd.uniform(26, 60)
        x1, y1 = x0 + ln * math.cos(ang), y0 + ln * math.sin(ang)
        key = "hair_hi" if rnd.random() < 0.55 and x0 < 420 else "hair_sh"
        add(key, "sline", [(x0, y0), ((x0 + x1) / 2 + rnd.uniform(-5, 5), (y0 + y1) / 2), (x1, y1)], rnd.uniform(3, 6), warp=False)
    if a > 0.01:
        for k in range(14):
            x0 = 60 + 4 * (k % 3) if k < 7 else 536 - 4 * (k % 3)
            y0 = 300 + 14 * (k % 7)
            add("grey", "sline", [(x0, y0), (x0 + (6 if k < 7 else -6), y0 - 34)], 3.0, warp=False)
    add("_unclip", "none", [], warp=False)
    return ops


def draw_ops(ctx, ops, ox, oy, s, pal, alpha=1.0, skip=()):
    """Draw head ops at offset/scale with a palette dict key -> rgb(a)."""
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(s, s)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for key, kind, pts, extra in ops:
        if key == "_clip":
            ctx.save()
            path(ctx, pts)
            ctx.clip()
            continue
        if key == "_unclip":
            ctx.restore()
            continue
        if key == "fold" and key not in pal and "s1" in pal and "s2" in pal and pal["s1"] and pal["s2"]:
            col = tuple(x + (y - x) * 0.45 for x, y in zip(pal["s1"][:3], pal["s2"][:3]))
        elif key.startswith("_") or key in skip or key not in pal or pal[key] is None:
            continue
        else:
            col = pal[key]
        if len(col) == 3:
            col = (*col, 1.0)
        ctx.set_source_rgba(col[0], col[1], col[2], col[3] * alpha)
        if kind in ("poly", "spoly"):
            path(ctx, pts, True, kind == "spoly")
            ctx.fill()
        else:
            path(ctx, pts, False, kind == "sline")
            ctx.set_line_width(extra)
            ctx.stroke()
    ctx.restore()


def silhouette(ctx, ops, ox, oy, s, keys=("_face", "_hair")):
    ctx.save()
    ctx.translate(ox, oy)
    ctx.scale(s, s)
    for key, kind, pts, extra in ops:
        if key in keys:
            path(ctx, pts)
            ctx.fill()
    ctx.restore()


# ---------------------------------------------------------------- track
class Track:
    """Half-loop ramp: ground lead-in, then an elongated arc that rises on the
    right, goes vertical, and curls back over the top (alpha up to ~1.06*pi)."""

    def __init__(self, cx=1120, ground=930, rx=250, ry=400, lead=700, a_end=1.06 * math.pi):
        self.cx, self.ground, self.rx, self.ry = cx, ground, rx, ry
        self.cy = ground - ry
        self.lead = lead
        self.a_end = a_end

    def at(self, alpha):
        x = self.cx + self.rx * math.sin(alpha)
        y = self.cy + self.ry * math.cos(alpha)
        dx, dy = self.rx * math.cos(alpha), -self.ry * math.sin(alpha)
        d = math.hypot(dx, dy)
        return (x, y), (dx / d, dy / d)

    def centerline(self, n=160):
        pts = [(self.cx - self.lead, self.ground)]
        for i in range(n + 1):
            pts.append(self.at(self.a_end * i / n)[0])
        return pts

    def normal_in(self, alpha):
        (x, y), (tx, ty) = self.at(alpha)
        n = (-ty, tx)
        if (self.cx - x) * n[0] + (self.cy - y) * n[1] < 0:
            n = (ty, -tx)
        return n


# ---------------------------------------------------------------- car (side profile, facing +x, wheels on y=0, length 2)
def _arch(cx, r, a0, a1, n=8):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), -0.15 + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


CAR_BODY = ([(-1.0, -0.12), (-0.98, -0.22), (-0.82, -0.27), (-0.45, -0.29), (-0.26, -0.31), (-0.08, -0.42),
             (0.12, -0.43), (0.40, -0.31), (0.75, -0.25), (0.96, -0.17), (1.0, -0.09), (0.97, -0.05), (0.84, -0.05)]
            + _arch(0.62, 0.19, 0.0, -math.pi)[::1] + [(0.4, -0.05), (-0.4, -0.05)]
            + _arch(-0.62, 0.19, 0.0, -math.pi) + [(-0.84, -0.05), (-0.98, -0.06)])
CAR_BODY = [(x, y * 1.18 if y < -0.06 else y) for x, y in CAR_BODY]
CAR_GLASS = [(-0.24, -0.36), (-0.06, -0.48), (0.12, -0.49), (0.38, -0.36)]
CAR_SIDE_HI = [(-0.9, -0.2), (0.9, -0.15), (0.9, -0.12), (-0.92, -0.16)]
WHEELS = [(-0.62, -0.15), (0.62, -0.15)]
NOZZLES = [(-0.62, -0.32), (0.55, -0.3)]


def car_xform(track, alpha, L, gap=0.0, reverse_dir=False):
    """Returns f(local)->screen with car on the inner side of the track."""
    (px, py), (tx, ty) = track.at(alpha)
    nx, ny = track.normal_in(alpha)
    if reverse_dir:
        tx, ty = -tx, -ty
    px += nx * gap
    py += ny * gap

    def f(p):
        x, y = p
        return (px + x * L * tx - y * L * nx, py + x * L * ty - y * L * ny)

    return f, (nx, ny)
