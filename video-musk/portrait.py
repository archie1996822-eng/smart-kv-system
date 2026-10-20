"""Hand-designed paper-sculpture portrait of Elon Musk (3/4 view, facing left).

Each structural plane of the face (forehead, brow ridge, eye sockets, nose bridge,
cheekbones, jaw, chin) is its own folded sheet, so the face keeps its real volume
while speaking the same paper language as the folded body.

age 0 = 2008, age 1 = 2026 (more creases: eye bags, nasolabial and forehead folds,
greying temples, heavier lids and jaw).
"""
import math

from gfx import hexc, mix, shade, lerp
from origami import fill, shadow, edge, crease, fold, pyramid, _path

SKIN = hexc("#e9bc98")
SKIN_26 = hexc("#dfb08f")
HAIR_08 = hexc("#3a2a20")
HAIR_26 = hexc("#463a32")
GREY = hexc("#a39b93")
BROW = hexc("#2c1f18")
IRIS = hexc("#3a2a1f")
LIP = hexc("#c58472")


def T(pts, ox, oy, s):
    return [(ox + x * s, oy + y * s) for x, y in pts]


def portrait(ctx, ox, oy, s=1.0, age=0.0, outfit=None):
    skin = mix(SKIN, SKIN_26, age)
    hair = mix(HAIR_08, HAIR_26, age)
    L = lambda k: shade(skin, k)  # skin tones

    def P(pts):
        return T(pts, ox, oy, s)

    def F(pts, col, a=1.0):
        fill(ctx, P(pts), col, a)

    def C(a, b, col=(1, 1, 1), al=0.3, lw=1.2):
        crease(ctx, P([a])[0], P([b])[0], col, al, lw * s)

    jaw = 8 * age  # heavier lower face with age

    # ------------------------------------------------ body (origami suit)
    outfit = outfit or ("suit" if age < 0.5 else "tee")
    _body(ctx, P, F, C, age, outfit, front=False)

    # ------------------------------------------------ neck (tucked into the collar)
    neck = [(-78, 236), (104, 200), (122, 350), (-70, 372)]
    F(neck, L(0.9))
    F([(-78, 236), (104, 200), (112, 268), (-52, 300)], L(0.72))       # shadow under the jaw
    F([(40, 290), (122, 350), (112, 268)], L(0.8))
    C((-52, 300), (112, 268), (1, 1, 1), 0.18)
    _body(ctx, P, F, C, age, outfit, front=True)

    # ------------------------------------------------ ears (near side)
    ear = [(176, -58), (204, -74), (222, -36), (216, 28), (198, 72), (176, 80)]
    shadow(ctx, P(ear), off=(6 * s, 6 * s), a=0.25, spread=2 * s)
    F(ear, L(0.88))
    F([(186, -44), (208, -52), (210, 20), (194, 56), (184, 40)], L(0.7))
    edge(ctx, P(ear), mix(skin, (1, 1, 1), 0.5), 0.4)

    # ------------------------------------------------ face silhouette
    face = [(-168, -166), (-180, -82), (-178, -10), (-168, 62), (-150, 142), (-120, 205 + jaw), (-82, 252 + jaw),
            (-48, 276 + jaw * 0.5), (2, 284), (52, 272 + jaw * 0.5), (98, 236 + jaw), (152, 178 + jaw),
            (180, 96), (192, 10), (194, -72), (186, -152), (164, -204), (-40, -204)]
    shadow(ctx, P(face), off=(12 * s, 16 * s), a=0.3, spread=4 * s)
    F(face, L(0.97))

    # forehead: folded down the middle
    fh = [(-168, -166), (-40, -200), (164, -200), (186, -152), (182, -100), (-30, -110), (-172, -100)]
    F([fh[0], fh[1], fh[5], fh[6]], L(1.1))
    F([fh[1], fh[2], fh[3], fh[4], fh[5]], L(1.0))
    C(fh[1], fh[5], (1, 1, 1), 0.25)
    if age > 0.01:
        for k, y in enumerate((-178, -158, -138)):
            C((-120 + 15 * k, y + 4), (-30, y), (0.45, 0.3, 0.25), 0.35 * age, 1.6)
            C((-30, y), (120 - 15 * k, y + 6), (0.45, 0.3, 0.25), 0.35 * age, 1.6)

    # brow ridge – high, pronounced: lit top plane, shadow beneath
    F([(-172, -100), (-30, -110), (182, -100), (178, -74), (60, -64), (-30, -72), (-120, -64), (-174, -74)], L(1.14))
    C((-174, -74), (-30, -72), (1, 1, 1), 0.35)
    C((-30, -72), (178, -74), (1, 1, 1), 0.35)

    # eye sockets: deep planes under the brow
    sock_f = [(-160, -66), (-60, -70), (-46, -32), (-78, -6), (-136, -10), (-164, -36)]
    sock_n = [(2, -68), (134, -70), (156, -38), (126, -4), (40, -6), (8, -30)]
    F(sock_f, L(0.8))
    F(sock_n, L(0.74))

    # far cheek (lit) and cheekbone planes
    F([(-178, -10), (-136, -10), (-78, -6), (-64, 82), (-92, 124), (-168, 62)], L(1.08))
    F([(-168, 62), (-92, 124), (-110, 196 + jaw), (-150, 142)], L(0.98))
    F([(40, -6), (126, -4), (172, 14), (146, 64), (64, 42)], L(1.04))               # near cheekbone highlight
    F([(64, 42), (146, 64), (192, 10), (180, 96), (152, 178 + jaw), (96, 150), (32, 122), (20, 80)], L(0.86))
    F([(96, 92), (176, 84), (152, 172 + jaw), (102, 150)], L(0.76))                 # hollow under the cheekbone
    C((64, 42), (146, 64), (1, 1, 1), 0.3)
    C((146, 64), (192, 10), (1, 1, 1), 0.25)

    # jaw (near side, in shade) and chin
    F([(96, 150), (152, 178 + jaw), (98, 236 + jaw), (44, 272 + jaw * 0.5), (30, 252), (22, 214), (32, 172)], L(0.78))
    F([(-98, 214), (-40, 222), (22, 214), (30, 252), (2, 282), (-60, 272 + jaw * 0.5), (-102, 244)], L(1.06))
    F([(-86, 200), (-40, 206), (12, 198), (8, 216), (-40, 224), (-92, 214)], L(0.84))  # under-lip shadow
    C((-40, 246), (-40, 266), (0.5, 0.35, 0.3), 0.3, 1.4)                              # chin cleft

    # nose: lit bridge, shaded side, tip, wing, nostril
    F([(-42, -64), (-22, -64), (-36, 80), (-68, 82)], L(1.16))
    F([(-22, -64), (6, -22), (16, 78), (-36, 80)], L(0.86))
    F([(-72, 80), (-36, 74), (-12, 92), (-40, 114), (-74, 106)], L(1.12))
    F([(-10, 84), (18, 80), (28, 102), (2, 114), (-28, 114)], L(0.8))
    F([(-74, 106), (-40, 114), (2, 114), (20, 120), (-40, 128), (-82, 120)], L(0.7))
    F([(-34, 110), (-14, 106), (-6, 114), (-28, 117)], hexc("#5b372b"))
    C((-22, -64), (-36, 80), (1, 1, 1), 0.4)

    # nasolabial folds (stronger with age)
    F([(-4, 114), (22, 120), (38, 186), (14, 178)], L(0.84 - 0.08 * age), 0.4 + 0.6 * age)
    F([(-86, 118), (-74, 112), (-98, 182), (-110, 176)], L(0.9 - 0.08 * age), 0.3 + 0.6 * age)
    C((-4, 114), (14, 180), (0.4, 0.25, 0.2), 0.3 + 0.35 * age, 1.6)
    C((-84, 118), (-104, 178), (0.4, 0.25, 0.2), 0.2 + 0.3 * age, 1.4)
    if age > 0.01:  # marionette folds
        C((-104, 196), (-110, 236), (0.4, 0.25, 0.2), 0.35 * age, 1.4)
        C((30, 196), (40, 236), (0.4, 0.25, 0.2), 0.35 * age, 1.4)

    # mouth: thin upper lip, fuller lower lip, slight closed smirk (2008) / flat (2026)
    smirk = 6 * (1 - age)
    upper = [(-104, 172), (-72, 160), (-52, 164), (-38, 158), (4, 164), (30, 170 - smirk), (-40, 177)]
    lower = [(-100, 174), (-40, 179), (28, 172 - smirk), (6, 192), (-40, 200), (-86, 193)]
    F(upper, mix(L(0.8), LIP, 0.55))
    F(lower, mix(L(0.98), LIP, 0.45))
    F([(-86, 186), (-40, 192), (2, 186), (-40, 199)], mix(L(1.08), LIP, 0.35))
    line = P([(-108, 172), (-70, 176), (-40, 178), (0, 175), (32, 170 - smirk)])
    ctx.move_to(*line[0])
    for p in line[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgba(0.35, 0.17, 0.14, 0.9)
    ctx.set_line_width(3.0 * s)
    ctx.stroke()

    # eyes
    _eye(ctx, P, F, C, (-104, -36), 64, age, far=True)
    _eye(ctx, P, F, C, (76, -36), 78, age, far=False)

    # brows: straight, thick, low over the eyes
    F([(-166, -78), (-120, -92), (-62, -96), (-50, -86), (-110, -80), (-164, -68)], BROW if age < 0.5 else mix(BROW, GREY, 0.2))
    F([(-6, -88), (2, -98), (70, -98), (140, -90), (156, -78), (80, -84), (4, -78)], BROW if age < 0.5 else mix(BROW, GREY, 0.2))
    C((2, -96), (140, -88), (1, 1, 1), 0.15)

    # outline crease of the face sheet
    edge(ctx, P(face), mix(skin, (1, 1, 1), 0.45), 0.5, 1.4 * s)

    # ------------------------------------------------ hair (folded locks, swept up and back)
    _hair(ctx, P, F, C, hair, age)


def _eye(ctx, P, F, C, c, w, age, far):
    cx, cy = c
    hw = w / 2
    lid = 1.0 + 0.35 * age          # heavier upper lid when older
    up = [(cx - hw, cy + 4), (cx - hw * 0.5, cy - 13 + 2 * lid), (cx + hw * 0.15, cy - 15 + 3 * lid),
          (cx + hw * 0.7, cy - 9 + 2 * lid), (cx + hw, cy + 3)]
    lo = [(cx + hw, cy + 3), (cx + hw * 0.5, cy + 10), (cx - hw * 0.3, cy + 11), (cx - hw, cy + 4)]
    almond = up + lo[1:-1]
    F(almond, hexc("#e2d7ca"))
    # iris + pupil, top tucked under the lid
    ix = cx - hw * (0.12 if far else 0.05)
    iris = [(ix + 13 * math.cos(a), cy + 1 + 13 * math.sin(a)) for a in [i * math.pi / 5 for i in range(10)]]
    ctx.save()
    from origami import _path as pth
    pth(ctx, P(almond))
    ctx.clip()
    F(iris, IRIS)
    F([(ix + 6 * math.cos(a), cy + 1 + 6 * math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]], hexc("#120b08"))
    F([(ix - 7, cy - 5), (ix - 2, cy - 6), (ix - 4, cy - 1)], hexc("#f3eee6"))
    F(up + [(cx + hw, cy - 20), (cx - hw, cy - 20)], shade(SKIN, 0.75), 0.0)
    ctx.restore()
    # upper lid line (lash) and hooded fold above
    lash = P(up)
    ctx.move_to(*lash[0])
    for p in lash[1:]:
        ctx.line_to(*p)
    ctx.set_source_rgba(0.12, 0.08, 0.06, 1)
    ctx.set_line_width(4.2)
    ctx.stroke()
    fold_pts = [(x, y - 9 - 2 * age) for x, y in up[1:]]
    C(fold_pts[0], fold_pts[-1], (0.4, 0.26, 0.2), 0.45, 1.6)
    C((cx - hw * 0.8, cy + 9), (cx + hw * 0.6, cy + 12), (0.45, 0.3, 0.25), 0.35, 1.2)
    if age > 0.01:  # eye bags and crow's feet
        bag = [(cx - hw * 0.8, cy + 14), (cx + hw * 0.1, cy + 24), (cx + hw * 0.8, cy + 15), (cx + hw * 0.1, cy + 30)]
        F(bag, shade(SKIN_26, 0.8), 0.6 * age)
        C((cx - hw * 0.7, cy + 22), (cx + hw * 0.6, cy + 24), (0.4, 0.25, 0.2), 0.4 * age, 1.3)
        if not far:
            for k in range(3):
                C((cx + hw + 6, cy - 4 + k * 8), (cx + hw + 22, cy - 8 + k * 11), (0.45, 0.3, 0.25), 0.4 * age, 1.2)


def _hair(ctx, P, F, C, hair, age):
    rise = 16 * age  # receding hairline
    mass = [(-168, -160 + rise * 0.4), (-184, -232), (-150, -294), (-70, -330), (40, -338), (150, -312), (212, -252),
            (224, -170), (198, -112), (176, -146), (150, -186 + rise), (60, -196 + rise), (-40, -202 + rise),
            (-120, -188 + rise), (-164, -170 + rise * 0.4)]
    shadow(ctx, P(mass), off=(10, 14), a=0.35, spread=4)
    F(mass, shade(hair, 0.82))
    # swept-back locks, drawn back to front; crease runs root -> tip (index 3)
    locks = [
        [(120, -192), (170, -212), (206, -190), (224, -158), (184, -150), (150, -172)],
        [(60, -198), (112, -240), (190, -246), (224, -184), (182, -212), (120, -204)],
        [(0, -202), (40, -264), (140, -294), (214, -254), (150, -264), (70, -224)],
        [(-60, -202), (-30, -272), (60, -318), (152, -314), (80, -294), (10, -232)],
        [(-120, -190), (-112, -272), (-20, -328), (62, -336), (0, -304), (-60, -242)],
        [(-166, -170), (-180, -242), (-122, -302), (-56, -322), (-92, -282), (-132, -222)],
    ]
    for i, lk in enumerate(locks):
        lk = [(x, y + rise * (1.0 if y > -240 else 0.35)) for x, y in lk]
        col = hair
        if age > 0.01 and i <= 1:
            col = mix(hair, GREY, 0.18 * age)
        shadow(ctx, P(lk), off=(5, 7), a=0.28, spread=1.5)
        fill(ctx, P(lk[:4]), shade(col, 1.2 - 0.03 * i))
        fill(ctx, P(lk[3:] + [lk[0]]), shade(col, 0.92))
        C(lk[0], lk[3], (1, 1, 1), 0.22)
        edge(ctx, P(lk), mix(col, (1, 1, 1), 0.3), 0.3)
    # sideburns / temples (grey with age)
    side_col = mix(hair, GREY, 0.75 * age)
    sb = [(150, -186 + rise), (176, -150), (188, -100), (182, -36), (170, -56), (160, -120)]
    shadow(ctx, P(sb), off=(4, 5), a=0.25, spread=1)
    F(sb, shade(side_col, 0.95))
    sbf = [(-164, -170 + rise * 0.4), (-182, -120), (-178, -60), (-168, -80), (-158, -140)]
    F(sbf, shade(side_col, 1.05))


def _body(ctx, P, F, C, age, outfit, front):
    if outfit == "suit":
        jacket = hexc("#3b414d")
        shirt = hexc("#eeebe4")
    else:
        jacket = hexc("#454952")
        shirt = hexc("#202227")
    if front:
        _collar(ctx, P, F, C, outfit, jacket, shirt)
        return
    # shoulders / torso panels
    torso = [(-120, 330), (150, 300), (380, 410), (430, 900), (-420, 900), (-360, 430)]
    shadow(ctx, P(torso), off=(14, 18), a=0.35, spread=6)
    F(torso, shade(jacket, 0.95))
    # left (far) shoulder panel, lit
    F([(-120, 330), (-360, 430), (-420, 900), (-160, 900), (-60, 520)], shade(jacket, 1.12))
    # right (near) shoulder panel, shaded, with a fold at the sleeve seam
    F([(150, 300), (380, 410), (430, 900), (240, 900), (190, 520)], shade(jacket, 0.82))
    C((300, 380), (330, 900), (1, 1, 1), 0.18, 1.4)
    C((-300, 410), (-340, 900), (1, 1, 1), 0.2, 1.4)
    if outfit == "suit":
        F([(-92, 330), (124, 300), (60, 520), (10, 640)], shirt)
    else:
        F([(-110, 340), (140, 310), (190, 900), (-190, 900)], shirt)
        F([(-110, 340), (-190, 900), (-40, 900), (-20, 520)], shade(shirt, 1.25))


def _collar(ctx, P, F, C, outfit, jacket, shirt):
    if outfit == "suit":
        F([(-70, 360), (122, 340), (60, 520), (10, 640)], shirt)
        F([(10, 640), (60, 520), (122, 340), (90, 360)], shade(shirt, 0.86))
        # collar points
        for pts, k in (([(-92, 318), (-30, 330), (-10, 420), (-70, 380)], 1.05), ([(124, 290), (96, 330), (40, 420), (90, 360)], 0.9)):
            shadow(ctx, P(pts), off=(4, 6), a=0.3, spread=1)
            F(pts, shade(shirt, k))
        # lapels: folded triangles with notch
        lapL = [(-100, 336), (-150, 380), (-120, 470), (-160, 500), (-60, 700), (10, 650), (-40, 420)]
        lapR = [(130, 306), (190, 350), (172, 440), (212, 470), (100, 680), (14, 652), (70, 420)]
        for lap, k in ((lapL, 1.2), (lapR, 0.95)):
            shadow(ctx, P(lap), off=(8, 10), a=0.35, spread=2)
            n = len(lap)
            F(lap, shade(jacket, k))
            C(lap[2], lap[5], (1, 1, 1), 0.3)
            edge(ctx, P(lap), mix(jacket, (1, 1, 1), 0.4), 0.4)
        for y in (760, 850):
            pts = [(10 + 10 * math.cos(a), y + 10 * math.sin(a)) for a in [i * math.pi / 3 for i in range(6)]]
            F(pts, shade(jacket, 0.6))
    else:
        rib = [(-92, 344), (-60, 372), (30, 372), (124, 330), (132, 348), (40, 394), (-64, 394), (-104, 360)]
        shadow(ctx, P(rib), off=(4, 6), a=0.3, spread=1)
        F(rib, shade(shirt, 1.55))
        # open jacket fronts folded back
        for pts, k in (([(-110, 340), (-170, 380), (-230, 900), (-170, 900), (-120, 520)], 1.25),
                       ([(140, 310), (200, 350), (250, 900), (190, 900), (150, 520)], 0.92)):
            shadow(ctx, P(pts), off=(8, 10), a=0.35, spread=2)
            F(pts, shade(jacket, k))
            edge(ctx, P(pts), mix(jacket, (1, 1, 1), 0.4), 0.4)
