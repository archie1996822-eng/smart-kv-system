"""Opening in folded-paper style (2D, side view, layered sheets).

Half-pipe track (a 180° U). The car races along the bottom, climbs the right
wall to the vertical lip, rises off it, stops at the top and hovers on four
cold-gas jets, flips with short attitude-control puffs, then lets itself down
on the jets and lands back on the ground beside the pipe.
"""
import math

import numpy as np

from gfx import W, H, hexc, mix, shade, hash01, lerp
from origami import (fill, shadow, edge, crease, pyramid, fold, sheet, strip_facets, regular, tone_for, _path)

# ---------------------------------------------------------------- palette
SKY = [hexc(c) for c in ("#18213b", "#1f2b4b", "#27375c", "#30446c", "#3a527c")]
MOON = hexc("#efe6d2")
MTN_FAR = hexc("#35597a")
MTN_MID = hexc("#2a4a68")
SNOW = hexc("#e8edf2")
HILL = hexc("#25425a")
TREE = hexc("#1c3a4a")
GROUND = hexc("#3d5a6b")
GROUND2 = hexc("#2c4656")
PIPE_IN = hexc("#d8dde4")
PIPE_SIDE = hexc("#8e9db0")
PIPE_RIB = hexc("#5c6c82")
CAR = hexc("#c8323c")
CAR_DARK = hexc("#8f1f2a")
GLASS = hexc("#1d2a44")
TYRE = hexc("#22252b")
HUB = hexc("#c4ccd6")
JET = [hexc("#f4f9ff"), hexc("#d9ecfc"), hexc("#b3d6f4")]

# ---------------------------------------------------------------- track geometry
PIPE_C = (800.0, 610.0)   # centre of the semicircle
PIPE_R = 330.0
PIPE_T = 44.0             # paper band thickness
GROUND_Y = 960.0


def pipe_point(th, r=PIPE_R):
    """th = 0 bottom, +pi/2 right lip, -pi/2 left lip."""
    return (PIPE_C[0] + r * math.sin(th), PIPE_C[1] + r * math.cos(th))


# ---------------------------------------------------------------- background
def draw_sky(ctx, cam=(0, 0)):
    fill(ctx, [(0, 0), (W, 0), (W, H), (0, H)], SKY[0])
    for i, c in enumerate(SKY[1:]):
        y0 = 120 + i * 120 - cam[1] * 0.05
        pts = [(-20, H + 20)]
        for k in range(14):
            x = k * W / 13
            pts.append((x, y0 + (24 if k % 2 else 0) + 8 * math.sin(i * 2 + k)))
        pts.append((W + 20, H + 20))
        shadow(ctx, pts, off=(0, -8), a=0.25, spread=0, steps=3)
        fill(ctx, pts, c)
        # crease each zigzag tooth
        for k in range(1, 13):
            crease(ctx, pts[k + 1], (pts[k + 1][0], pts[k + 1][1] + 60), mix(c, (1, 1, 1), 0.3), 0.12)
    mx, my = 1540 - cam[0] * 0.04, 190
    shadow(ctx, regular(mx, my, 58, 10, 0.3), off=(10, 12), a=0.35)
    pyramid(ctx, regular(mx, my, 58, 10, 0.3), (mx - 8, my - 10), MOON, lo=0.84, hi=1.06)
    for i in range(26):
        sx = (hash01(i, 1) * W * 1.1 - cam[0] * 0.03) % W
        sy = 40 + hash01(i, 2) * 380
        s = 5 + 7 * hash01(i, 3)
        star = [(sx, sy - s), (sx + s * 0.28, sy - s * 0.28), (sx + s, sy), (sx + s * 0.28, sy + s * 0.28),
                (sx, sy + s), (sx - s * 0.28, sy + s * 0.28), (sx - s, sy), (sx - s * 0.28, sy - s * 0.28)]
        pyramid(ctx, star, (sx, sy), MOON, lo=0.75, hi=1.05, creases=False, cut_edge=False, a=0.85)


def mountain(ctx, x0, x1, peak, base_y, col, snow=True):
    px, py = peak
    pts = [(x0, base_y), (px, py), (x1, base_y)]
    shadow(ctx, pts, off=(14, 6), a=0.3)
    mid = (px + (x1 - px) * 0.18, base_y)
    fill(ctx, [(x0, base_y), (px, py), mid], shade(col, 1.1))
    fill(ctx, [mid, (px, py), (x1, base_y)], shade(col, 0.8))
    crease(ctx, (px, py), mid, mix(col, (1, 1, 1), 0.5), 0.3)
    if snow:
        h = (base_y - py) * 0.26
        lx = px - (px - x0) * h / (base_y - py)
        rx = px + (x1 - px) * h / (base_y - py)
        cy = py + h
        cap = [(px, py), (rx, cy), (rx - (rx - px) * 0.35, cy - h * 0.18), (px + (mid[0] - px) * h / (base_y - py), cy + 6),
               (px - (px - lx) * 0.45, cy - h * 0.12), (lx, cy)]
        fill(ctx, [cap[0], cap[3], cap[4], cap[5]], shade(SNOW, 1.03))
        fill(ctx, [cap[0], cap[1], cap[2], cap[3]], shade(SNOW, 0.82))
    edge(ctx, pts, mix(col, (1, 1, 1), 0.4), 0.35)


def tree(ctx, x, y, h, col=TREE):
    for k in range(3):
        w = h * (0.42 - k * 0.09)
        ty = y - h * (0.25 + 0.27 * k)
        pts = [(x - w, ty + h * 0.32), (x, ty - h * 0.28), (x + w, ty + h * 0.32)]
        shadow(ctx, pts, off=(6, 5), a=0.3, spread=2)
        fold(ctx, [pts[0], pts[1], (x, ty + h * 0.32), pts[2]], 1, 2, col, 1.15, 0.8)


def draw_landscape(ctx, cam=(0, 0)):
    ox = -cam[0] * 0.15
    for x0, x1, px, py in ((-200, 520, 170, 330), (300, 1100, 720, 260), (900, 1700, 1300, 300), (1450, 2200, 1850, 340)):
        mountain(ctx, x0 + ox, x1 + ox, (px + ox, py), 760, MTN_FAR)
    ox = -cam[0] * 0.3
    for x0, x1, px, py in ((-120, 460, 160, 520), (1180, 1800, 1500, 500), (1650, 2200, 1950, 560)):
        mountain(ctx, x0 + ox, x1 + ox, (px + ox, py), 820, MTN_MID, snow=False)
    ox = -cam[0] * 0.5
    hill = [(-40, 1000), (-40, 820)]
    for k in range(11):
        hill.append((k * 200 + ox, 830 - 34 * math.sin(k * 1.3) - 20))
    hill += [(2000, 820), (2000, 1000)]
    shadow(ctx, hill, off=(0, -10), a=0.3, spread=0)
    fill(ctx, hill, HILL)
    for k in range(2, len(hill) - 3):
        fill(ctx, [hill[k], hill[k + 1], ((hill[k][0] + hill[k + 1][0]) / 2, 900)],
             shade(HILL, 1.08 if k % 2 else 0.9))
    for i in range(14):
        x = (hash01(i, 40) * 2300 - 150 + ox) % 2100 - 90
        if 420 < x < 1260:
            continue
        tree(ctx, x, 850 + hash01(i, 41) * 30, 70 + 50 * hash01(i, 42))


def draw_ground(ctx, cam=(0, 0)):
    ox = -cam[0] * 1.0
    g = [(-20, GROUND_Y), (W + 20, GROUND_Y), (W + 20, H + 20), (-20, H + 20)]
    shadow(ctx, g, off=(0, -12), a=0.35, spread=0)
    fill(ctx, g, GROUND)
    # accordion folds of the ground strip
    for k in range(-1, 22):
        x = k * 96 + (ox % 96)
        fill(ctx, [(x, GROUND_Y), (x + 48, GROUND_Y), (x + 30, H), (x - 18, H)], shade(GROUND, 1.07))
    front = [(-20, 1030), (W + 20, 1015), (W + 20, H + 20), (-20, H + 20)]
    shadow(ctx, front, off=(0, -10), a=0.35, spread=0)
    fill(ctx, front, GROUND2)


def draw_pipe(ctx):
    n = 28
    ths = np.linspace(-math.pi / 2, math.pi / 2, n + 1)
    inner = [pipe_point(t, PIPE_R) for t in ths]
    outer = [pipe_point(t, PIPE_R + PIPE_T) for t in ths]
    back_in = [(x + 22, y - 18) for x, y in inner]
    # supports: folded triangle trusses
    for t in np.linspace(-1.35, 1.35, 9):
        x, y = pipe_point(t, PIPE_R + PIPE_T)
        if y > GROUND_Y - 10:
            continue
        leg = [(x - 16, y), (x + 16, y), (x + 26 + 12 * math.sin(t), GROUND_Y), (x - 26 + 12 * math.sin(t), GROUND_Y)]
        shadow(ctx, leg, off=(10, 6), a=0.3, spread=2)
        fold(ctx, leg, 1, 3, PIPE_RIB, 1.08, 0.82)
    band = outer + inner[::-1]
    shadow(ctx, band, off=(16, 16), a=0.35, spread=6)
    # far rim (paper wall behind the riding surface)
    strip_facets(ctx, inner, back_in, shade(PIPE_IN, 0.78), lo=0.85, hi=1.05, alt=0.03)
    # riding surface seen edge-on: accordion facets
    strip_facets(ctx, outer, inner, PIPE_SIDE, lo=0.82, hi=1.12, alt=0.07)
    # bright lip strip on the inner edge
    for i in range(len(inner) - 1):
        a, b = inner[i], inner[i + 1]
        crease(ctx, a, b, PIPE_IN, 0.9, 3.0)
    for th in (-math.pi / 2, math.pi / 2):
        p0 = pipe_point(th, PIPE_R - 4)
        p1 = pipe_point(th, PIPE_R + PIPE_T + 4)
        cap = [(p0[0] - 6 * math.copysign(1, th), p0[1] - 10), (p1[0], p1[1] - 10), (p1[0], p1[1] + 6), (p0[0], p0[1] + 6)]
        fill(ctx, cap, shade(PIPE_IN, 1.05))
    base = [(PIPE_C[0] - PIPE_R - 120, GROUND_Y - 22), (PIPE_C[0] + PIPE_R + 120, GROUND_Y - 22),
            (PIPE_C[0] + PIPE_R + 140, GROUND_Y + 8), (PIPE_C[0] - PIPE_R - 140, GROUND_Y + 8)]
    shadow(ctx, base, off=(8, 8), a=0.3)
    fold(ctx, base, 0, 1, PIPE_RIB, 1.15, 0.85)


# ---------------------------------------------------------------- car (2.5D oblique paper model)
DEPTH = np.array([46.0, -26.0])   # screen offset of the far side

# local coords: x forward, y up; origin = ground contact midway between wheels
PROFILE = [(-150, 22), (-153, 58), (-122, 70), (-62, 75), (-28, 101), (26, 103), (78, 77), (132, 63),
           (153, 48), (150, 22)]
UPPER = [(-153, 58), (-122, 70), (-62, 75), (78, 77), (132, 63), (153, 48), (151, 44), (-152, 50)]
WINDOW = [(-52, 77), (-24, 97), (22, 99), (68, 78)]
WHEELS = [(-95, 30), (97, 30)]
NOZZLES = [(-84, 18), (66, 18)]


def _tf(pts, pose, z=0.0, scale=1.0):
    # local (x, y-up) -> screen (x, y-down), rotated by ang (counter-clockwise on screen)
    x0, y0, ang = pose
    c, s = math.cos(ang), math.sin(ang)
    out = []
    for x, y in pts:
        x *= scale
        y *= scale
        X = x * c - y * s
        Y = x * s + y * c
        out.append((x0 + X + DEPTH[0] * z, y0 - Y + DEPTH[1] * z))
    return out


def car_down(pose):
    """Screen-space unit vector of the car's local 'down'."""
    ang = pose[2]
    return np.array([math.sin(ang), math.cos(ang)])


def jet(ctx, base, down, length, w0=12, w1=46, a=1.0, flick=0.0):
    d = np.asarray(down, float)
    nrm = np.array([-d[1], d[0]])
    b = np.asarray(base, float)
    tip = b + d * length
    p = [tuple(b - nrm * w0), tuple(b + nrm * w0), tuple(tip + nrm * w1), tuple(tip - nrm * w1)]
    for k, (col, sc, al) in enumerate(((JET[2], 1.0, 0.45), (JET[1], 0.7, 0.6), (JET[0], 0.36, 0.85))):
        q = [tuple(b - nrm * w0 * sc), tuple(b + nrm * w0 * sc), tuple(b + d * length * (1 - 0.12 * k) + nrm * w1 * sc),
             tuple(b + d * length * (1 - 0.12 * k) - nrm * w1 * sc)]
        mid0 = tuple(b)
        mid1 = tuple(b + d * length * (1 - 0.12 * k))
        fill(ctx, [q[0], mid0, mid1, q[3]], shade(col, 1.04), al * a)
        fill(ctx, [mid0, q[1], q[2], mid1], shade(col, 0.9), al * a)
    return tip


def puff(ctx, x, y, r, seed=0, a=1.0, col=None):
    col = col or JET[1]
    jit = [0.85 + 0.3 * hash01(seed, k) for k in range(7)]
    pts = regular(x, y, r, 7, hash01(seed, 9) * 6.28, jit)
    shadow(ctx, pts, off=(r * 0.12, r * 0.16), a=0.22 * a, spread=r * 0.05, steps=3)
    pyramid(ctx, pts, (x - r * 0.15, y - r * 0.2), col, lo=0.82, hi=1.06, a=a, crease_a=0.18)


def draw_car(ctx, pose, jets=(0, 0, 0, 0), t=0.0, scale=1.0, puffs=True):
    """pose = (screen x, screen y, angle). jets = level of the four nozzles (near-rear, near-front, far-rear, far-front)."""
    down = car_down(pose)
    far = _tf(PROFILE, pose, 1.0, scale)
    near = _tf(PROFILE, pose, 0.0, scale)
    # far-side jets + wheels sit behind the body
    for k, (nx, ny) in enumerate(NOZZLES):
        lvl = jets[2 + k]
        if lvl > 0.01:
            b = _tf([(nx, ny)], pose, 0.85, scale)[0]
            jet(ctx, b, down, (150 + 25 * math.sin(t * 17 + k)) * lvl * scale, 9 * scale, 24 * scale * lvl, a=0.8)
    for wx, wy in WHEELS:
        c = _tf([(wx, wy)], pose, 0.92, scale)[0]
        pyramid(ctx, regular(c[0], c[1], 30 * scale, 8, pose[2] + t * 0), c, shade(TYRE, 0.8), lo=0.8, hi=1.1)
    shadow(ctx, near, off=(14, 18), a=0.3, spread=4)
    fill(ctx, far, CAR_DARK)
    # connecting planes between near and far outline (only the ones facing the viewer)
    n = len(PROFILE)
    dvec = DEPTH / np.linalg.norm(DEPTH)
    for i in range(n):
        j = (i + 1) % n
        e = np.array(near[j]) - np.array(near[i])
        out = np.array([e[1], -e[0]])  # outward normal for CCW-on-screen... check sign below
        cen = np.mean(near, 0)
        mid = (np.array(near[i]) + np.array(near[j])) / 2
        if np.dot(out, mid - cen) < 0:
            out = -out
        if np.dot(out, dvec) <= 0:
            continue
        q = [near[i], near[j], far[j], far[i]]
        col = GLASS if (3 <= i <= 5) else CAR
        fill(ctx, q, shade(col, tone_for(out, 0.8, 1.15)))
        crease(ctx, near[i], far[i], mix(col, (1, 1, 1), 0.5), 0.3)
    # near side panels
    fill(ctx, near, shade(CAR, 0.86))
    up = _tf(UPPER, pose, 0.0, scale)
    fill(ctx, up, shade(CAR, 1.1))
    crease(ctx, up[-1], up[-2], mix(CAR, (1, 1, 1), 0.6), 0.5)
    win = _tf(WINDOW, pose, 0.0, scale)
    fold(ctx, win, 1, 3, GLASS, 1.25, 0.95)
    # side intake fold
    fold(ctx, _tf([(-40, 32), (20, 32), (0, 50), (-30, 50)], pose, 0.0, scale), 0, 2, CAR_DARK, 1.0, 0.75, cut_edge=False)
    edge(ctx, near, mix(CAR, (1, 1, 1), 0.55), 0.5, 1.4)
    # lamps
    fill(ctx, _tf([(140, 50), (152, 47), (150, 38), (136, 41)], pose, 0.0, scale), hexc("#f2f6fb"))
    fill(ctx, _tf([(-152, 52), (-140, 55), (-141, 46), (-152, 44)], pose, 0.0, scale), hexc("#6d1622"))
    # nozzles (near)
    for k, (nx, ny) in enumerate(NOZZLES):
        c = _tf([(nx - 14, ny + 2), (nx + 14, ny + 2), (nx + 10, ny - 10), (nx - 10, ny - 10)], pose, 0.15, scale)
        fold(ctx, c, 0, 2, hexc("#7f8b99"), 1.15, 0.85, cut_edge=False)
    for wx, wy in WHEELS:
        c = _tf([(wx, wy)], pose, 0.0, scale)[0]
        tyre = regular(c[0], c[1], 31 * scale, 8, pose[2])
        shadow(ctx, tyre, off=(5, 6), a=0.3, spread=1)
        pyramid(ctx, tyre, (c[0] - 4, c[1] - 4), TYRE, lo=0.8, hi=1.25)
        hub = regular(c[0], c[1], 15 * scale, 5, pose[2] * 1.0 + 0.3)
        pyramid(ctx, hub, c, HUB, lo=0.8, hi=1.1)
    for k, (nx, ny) in enumerate(NOZZLES):
        lvl = jets[k]
        if lvl > 0.01:
            b = _tf([(nx, ny - 8)], pose, 0.15, scale)[0]
            jet(ctx, b, down, (160 + 25 * math.sin(t * 19 + k)) * lvl * scale, 10 * scale, 26 * scale * lvl)
    return down


# ---------------------------------------------------------------- choreography (for keyframes / animation)
def car_pose_at(t):
    """Returns pose (x, y, angle), jet levels and a label. Angle: CCW positive (nose up when moving right)."""
    lip = pipe_point(math.pi / 2, PIPE_R - 2)
    if t < 1.1:
        # racing along the inside of the U: from left of bottom, around to the right lip
        th = lerp(-0.25, math.pi / 2, (t / 1.1) ** 1.25)
        x, y = pipe_point(th, PIPE_R - 2)
        return (x, y, th), (0, 0, 0, 0), "爬升"
    if t < 1.5:
        u = (t - 1.1) / 0.4
        e = 1 - (1 - u) ** 2
        return (lip[0] - 6 * e, lip[1] - 230 * e, math.pi / 2 - 0.25 * u), (0, 0, 0, 0), "冲出顶部"
    if t < 1.8:
        u = (t - 1.5) / 0.3
        ang = (math.pi / 2 - 0.25) * (1 - (u * u * (3 - 2 * u)))
        lv = min(1, u * 2)
        return (lip[0] - 6 + 40 * u, lip[1] - 230 - 8 * u, ang), (lv,) * 4, "顶点停住"
    if t < 2.6:
        u = (t - 1.8) / 0.8
        bob = 6 * math.sin(u * 6.28)
        return (lip[0] + 34 + 30 * u, lip[1] - 238 + bob, 0.0), (1, 1, 1, 1), "冷气托住悬停"
    if t < 3.5:
        u = (t - 2.6) / 0.9
        e = u * u * (3 - 2 * u)
        ang = 2 * math.pi * e
        # attitude-control puffs alternate between nose and tail nozzles
        pulse = 0.5 + 0.5 * math.sin(u * math.pi * 6)
        jets = (0.45 * pulse, 0.45 * (1 - pulse), 0.45 * pulse, 0.45 * (1 - pulse))
        return (lip[0] + 64 + 120 * u, lip[1] - 238 - 40 * math.sin(math.pi * u), ang), jets, "翻转 · 喷气校准姿态"
    u = min(1.0, (t - 3.5) / 0.8)
    e = u * u * (3 - 2 * u)
    gy = GROUND_Y - 6
    y = lerp(lip[1] - 238, gy, e)
    lv = 0.9 * (1 - u) + 0.2
    return (lip[0] + 184 + 60 * e, y, 0.0), (lv,) * 4, "喷气减速落地"


def render_frame(ctx, t, cam=(0, 0), zoom=1.0, focus=(960, 540)):
    draw_sky(ctx, cam)
    ctx.save()
    ctx.translate(W / 2, H / 2)
    ctx.scale(zoom, zoom)
    ctx.translate(-focus[0], -focus[1])
    draw_landscape(ctx, cam)
    draw_ground(ctx, cam)
    draw_pipe(ctx)
    pose, jets, _ = car_pose_at(t)
    down = draw_car(ctx, pose, jets, t)
    # cold-gas mist gathering under the jets
    if max(jets) > 0.05:
        x, y = pose[0], pose[1]
        for i in range(9):
            r = 22 + 26 * hash01(i, 5)
            px = x + (hash01(i, 6) - 0.5) * 260
            py = y + 150 + 50 * hash01(i, 7)
            puff(ctx, px, min(py, GROUND_Y - r * 0.6), r, seed=i, a=0.55 * max(jets), col=JET[1 + i % 2])
    ctx.restore()
