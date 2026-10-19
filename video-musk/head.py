"""Low-poly 3D head modelled on Elon Musk's proportions.

Long face, high brow ridge over deep-set dark eyes, straight nose, broad jaw and a
firm chin. The skull is lofted from horizontal cross-sections, features are added
as displacements, then everything is flat shaded so the planes read as folds.

`age` 0.0 = 2008 (younger, denser hair, faint lines), 1.0 = 2026 (older, tired).
"""
import math
from functools import lru_cache

import numpy as np

from gfx import hexc, mix, shade, smooth, clamp, lerp
from mesh import Mesh

SKIN = hexc("#e2b293")
SKIN_26 = hexc("#d9a98c")
LIP = hexc("#b9786a")
HAIR_08 = hexc("#3f2c22")
HAIR_26 = hexc("#45372e")
GREY = hexc("#9a9189")
BROW = hexc("#2f211a")
IRIS = hexc("#3b2a20")
SCLERA = hexc("#d6cabb")
LASH = hexc("#20160f")

# y -> half width, front depth, back depth
PROFILE = np.array([
    # y      W     Df    Db
    [1.30, 0.00, 0.00, 0.00],
    [1.24, 0.34, 0.30, 0.42],
    [1.12, 0.54, 0.52, 0.72],
    [0.94, 0.66, 0.68, 0.90],
    [0.70, 0.725, 0.78, 0.98],
    [0.45, 0.735, 0.83, 1.00],
    [0.25, 0.735, 0.86, 0.96],
    [0.05, 0.75, 0.85, 0.86],
    [-0.15, 0.75, 0.83, 0.74],
    [-0.40, 0.72, 0.79, 0.58],
    [-0.62, 0.675, 0.75, 0.46],
    [-0.80, 0.64, 0.70, 0.38],
    [-0.94, 0.56, 0.64, 0.30],
    [-1.06, 0.42, 0.57, 0.20],
    [-1.15, 0.26, 0.46, 0.12],
    [-1.20, 0.00, 0.30, 0.00],
])


def _prof(y, age):
    W = np.interp(-y, -PROFILE[:, 0], PROFILE[:, 1]) * 0.96
    Df = np.interp(-y, -PROFILE[:, 0], PROFILE[:, 2])
    Db = np.interp(-y, -PROFILE[:, 0], PROFILE[:, 3]) * 0.9
    # age: slightly heavier lower face / jowls
    if y < -0.4:
        W *= 1.0 + 0.035 * age * smooth((-0.4 - y) / 0.5)
    return W, Df, Db


def G(d, s):
    return math.exp(-(d / s) ** 2)


def G2(dx, dy, sx, sy):
    return math.exp(-(dx / sx) ** 2 - (dy / sy) ** 2)


def _nose_h(y):
    ys = [0.30, 0.20, 0.08, -0.08, -0.22, -0.31, -0.36, -0.41, -0.46]
    hs = [0.00, 0.035, 0.085, 0.15, 0.24, 0.30, 0.27, 0.12, 0.00]
    return float(np.interp(-y, [-v for v in ys], hs))


def _nose_w(y):
    return 0.068 + 0.05 * smooth((0.05 - y) / 0.38)


def feature_dz(x, y, age):
    ax = abs(x)
    dz = 0.0
    # brow ridge – high and pronounced
    dz += 0.095 * G(y - 0.29, 0.075) * (1 - smooth((ax - 0.48) / 0.2))
    dz += 0.03 * G2(x, y - 0.26, 0.08, 0.06)
    # forehead gently rounded
    dz += 0.02 * G(y - 0.62, 0.2) * (1 - smooth(ax / 0.6))
    # deep eye sockets
    dz -= (0.165 + 0.02 * age) * G2(ax - 0.285, y - 0.125, 0.15, 0.085)
    # eyeball sitting in the socket
    dz += 0.06 * G2(ax - 0.285, y - 0.118, 0.11, 0.05)
    # nose
    dz += _nose_h(y) * math.exp(-(x / _nose_w(y)) ** 2)
    dz += 0.085 * G2(ax - 0.125, y + 0.375, 0.055, 0.05)
    dz -= 0.03 * G2(x, y + 0.465, 0.09, 0.03)
    # mouth
    dz += 0.075 * G2(x, y + 0.55, 0.21, 0.055)
    dz -= 0.035 * G2(x, y + 0.615, 0.21, 0.02)
    dz += 0.06 * G2(x, y + 0.675, 0.17, 0.04)
    dz -= 0.045 * G2(x, y + 0.775, 0.17, 0.04)
    # chin – firm, slightly squared
    dz += 0.125 * G2(x, y + 0.95, 0.25, 0.08)
    # cheekbones
    dz += 0.065 * G2(ax - 0.47, y + 0.03, 0.14, 0.09)
    # hollow below cheekbone (deeper with age)
    dz -= (0.025 + 0.03 * age) * G2(ax - 0.47, y + 0.40, 0.12, 0.12)
    # nasolabial fold groove (age)
    dz -= 0.02 * age * G2(ax - (0.20 + 0.1 * clamp((-0.38 - y) / 0.3)), y + 0.52, 0.03, 0.12)
    return dz


def surf(phi, y, age):
    W, Df, Db = _prof(y, age)
    s, c = math.sin(phi), math.cos(phi)
    x = W * s
    z = (Df if c > 0 else Db) * c
    fr = max(c, 0.0) ** 1.4
    if fr > 0:
        z += feature_dz(x, y, age) * fr
        # cheekbone width and temple hollow
        ax = abs(x)
        push = 0.03 * G2(ax - 0.62, y + 0.03, 0.15, 0.12) - 0.025 * G2(ax - 0.7, y - 0.42, 0.1, 0.15)
        x += math.copysign(push, x) if x else 0
    return np.array([x, y, z])


def surface_at(x, y, age, out=0.012):
    """Point on the front surface with front-projected coordinate x."""
    W, _, _ = _prof(y, age)
    phi = math.asin(clamp(x / max(W, 1e-3), -0.999, 0.999))
    p = surf(phi, y, age)
    # rough normal by finite differences
    e = 0.01
    px = surf(phi + e, y, age) - surf(phi - e, y, age)
    py = surf(phi, y + e, age) - surf(phi, y - e, age)
    n = np.cross(px, py)
    n /= np.linalg.norm(n) + 1e-9
    if n[2] < 0:
        n = -n
    return p + n * out


def _phis():
    front = np.radians(np.arange(-72, 72.1, 4.0))
    side_r = np.radians(np.linspace(84, 180, 7))
    side_l = -side_r[::-1][:-1]
    phis = np.concatenate([side_l, front, side_r])
    return phis[:-1] if abs(phis[-1] - math.pi) < 1e-6 and abs(phis[0] + math.pi) < 1e-6 else phis


def _ys():
    top = np.linspace(1.30, 0.62, 7)
    face = np.arange(0.565, -1.17, -0.055)
    return np.concatenate([top, face, [-1.20]])


def hairline(phi, age):
    d = abs(math.degrees(phi))
    # front hairline height by angle (2008 vs 2026: higher temples, slight recession)
    pts08 = [(0, 0.80), (22, 0.82), (40, 0.80), (58, 0.52), (70, 0.34), (78, -0.06), (88, 0.14),
             (104, 0.16), (135, -0.30), (180, -0.52)]
    pts26 = [(0, 0.84), (22, 0.90), (40, 0.93), (58, 0.60), (70, 0.38), (78, 0.02), (88, 0.16),
             (104, 0.18), (135, -0.28), (180, -0.50)]
    a = np.array(pts08)
    b = np.array(pts26)
    h0 = np.interp(d, a[:, 0], a[:, 1])
    h1 = np.interp(d, b[:, 0], b[:, 1])
    return lerp(h0, h1, age)


@lru_cache(maxsize=8)
def build_head(age_key):
    age = age_key / 100.0
    phis = _phis()
    ys = _ys()
    skin = mix(SKIN, SKIN_26, age)
    hair = mix(HAIR_08, HAIR_26, age)
    m = Mesh()
    grid = [[m.add_v(surf(p, y, age)) for p in phis] for y in ys]
    n = len(phis)
    for i in range(len(ys) - 1):
        for j in range(n):
            k = (j + 1) % n
            a, b, c, d = grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]
            ctr = np.mean([m.v[q] for q in (a, b, c, d)], 0)
            cx, cy, cz = ctr
            phi_c = math.atan2(cx, cz)
            col = skin
            opt = {"jit": 0.035, "edge": 0.05}
            if cy > hairline(phi_c, age) - 0.02:
                col = hair
                opt = {"jit": 0.1, "edge": 0.0}
            elif cz > 0 and abs(cx) < 0.17 - 0.35 * abs(cy + 0.612) and -0.69 < cy < -0.545:
                col = mix(skin, LIP, 0.62 if cy > -0.612 else 0.45)
            elif cz > 0:
                warm = 0.35 * G2(abs(cx) - 0.42, cy + 0.2, 0.15, 0.15) + 0.3 * G2(cx, cy + 0.32, 0.08, 0.06)
                col = mix(skin, hexc("#d98f7f"), warm * (0.6 + 0.3 * age))
            if (i + j) % 2:
                tris = ((a, b, c), (a, c, d))
            else:
                tris = ((a, b, d), (b, c, d))
            for t in tris:
                m.add_f(tuple(reversed(t)), col, **opt)
    # orient every face outward from the skull axis
    _orient(m, lambda c: np.array([0.0, c[1], -0.05]))
    _add_hair(m, phis, ys, age, hair)
    _add_ears(m, age, skin)
    return m


def _orient(m, inner):
    v = np.asarray(m.v)
    out = []
    for idx, rgb, opt in m.f:
        p = v[list(idx)]
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        if np.dot(nrm, p.mean(0) - inner(p.mean(0))) < 0:
            idx = tuple(reversed(idx))
        out.append((idx, rgb, opt))
    m.f = out


def _hair_thick(phi, y, age):
    d = abs(math.degrees(phi))
    front = G(d, 38)
    # short, tapered sides and back; volume concentrated on top-front, swept back
    t = 0.035 + 0.01 * (1 - age)
    t += (0.10 - 0.03 * age) * smooth((y - 0.55) / 0.5) * (0.55 + 0.45 * front)
    t += (0.08 - 0.03 * age) * front * G(y - 0.95, 0.22)
    if 40 < d < 110:
        t *= 1 - 0.6 * smooth((0.75 - y) / 0.45) * smooth((d - 40) / 15)
    if d > 100:
        t *= 1 - 0.6 * smooth((0.5 - y) / 0.6)
    return t


def _add_hair(m, phis, ys, age, hair):
    """Hair shell lofted from the crown down to the exact hairline curve, so the
    edge is a clean cut line, plus a thickness band from the shell edge to the scalp."""
    rng = np.random.default_rng(int(age * 100) + 7)
    hphis = np.radians(np.concatenate([np.arange(-180, -70, 15), np.arange(-70, 70, 7), np.arange(70, 180, 15)]))
    nv = 9
    n = len(hphis)
    top = 1.30
    shell = []
    scalp = []
    for j, p in enumerate(hphis):
        hl = hairline(p, age)
        col_s, col_c = [], []
        for v in range(nv):
            u = v / (nv - 1)
            y = lerp(top, hl, u ** 0.85)
            s = surf(p, y, age)
            axis = np.array([0.0, s[1] * 0.35 - 0.1, -0.05])
            d = s - axis
            d /= np.linalg.norm(d)
            t = _hair_thick(p, y, age)
            # tapered at the very edge, clumpy elsewhere
            t *= (0.55 + 0.45 * smooth((1 - u) / 0.22)) * (0.88 + 0.24 * rng.random())
            # hair sweeps up and back from the forehead
            sweep = np.array([0, 0.03, -0.05]) * G(math.degrees(p), 45) * (1 - u) * (1 - 0.4 * age)
            col_s.append(m.add_v(s + d * t + sweep))
            col_c.append(m.add_v(s - d * 0.004))
        shell.append(col_s)
        scalp.append(col_c)
    grey = GREY
    for j in range(n):
        k = (j + 1) % n
        for v in range(nv - 1):
            quad = (shell[j][v], shell[k][v], shell[k][v + 1], shell[j][v + 1])
            ctr = np.mean([m.v[q] for q in quad], 0)
            dphi = abs(math.degrees(math.atan2(ctr[0], ctr[2])))
            g = age * (0.5 * smooth((dphi - 62) / 16) * (1 - smooth((dphi - 96) / 14)) * smooth((0.55 - ctr[1]) / 0.35) + 0.04)
            col = mix(hair, grey, clamp(g))
            col = shade(col, 0.88 + 0.26 * rng.random())
            tris = ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])) if (j + v) % 2 else \
                ((quad[0], quad[1], quad[3]), (quad[1], quad[2], quad[3]))
            for t in tris:
                m.add_f(t, col, jit=0.08, edge=0.05, bias=0.02, hair=True)
        # cut edge of the hair sheet
        rim = (shell[j][-1], shell[k][-1], scalp[k][-1], scalp[j][-1])
        m.add_f(rim, shade(hair, 0.8), double=True, edge=0.0, bias=0.015, hair=True)
    v = np.asarray(m.v)
    out = []
    for idx, rgb, opt in m.f:
        if opt.get("hair") and not opt.get("double"):
            p = v[list(idx)]
            c = p.mean(0)
            nrm = np.cross(p[1] - p[0], p[2] - p[0])
            if np.dot(nrm, c - np.array([0.0, c[1] * 0.35 - 0.1, -0.05])) < 0:
                idx = tuple(reversed(idx))
        out.append((idx, rgb, opt))
    m.f = out


def _add_ears(m, age, skin):
    for sgn in (-1, 1):
        phi = sgn * math.radians(93)
        outline = [(0.16, 0.00), (0.13, 0.06), (0.06, 0.09), (-0.03, 0.07), (-0.08, 0.0),
                   (-0.06, -0.12), (-0.02, -0.22), (0.04, -0.30), (0.09, -0.28), (0.12, -0.16)]
        base_y = 0.02
        idx = []
        idx_in = []
        for (u, v) in outline:
            y = base_y + v + 0.04
            p = surf(phi, y, age)
            # ear sticks out sideways and slightly back
            p = p + np.array([sgn * (0.07 + 0.1 * (u + 0.1)), 0, -u * 0.9 - 0.02])
            idx.append(m.add_v(p))
            pin = surf(phi, y * 0.8 + base_y * 0.2, age) + np.array([sgn * 0.06, 0, -u * 0.6])
            idx_in.append(m.add_v(pin))
        m.add_f(tuple(idx), shade(skin, 0.9), double=True, edge=0.25)
        m.add_f(tuple(idx_in), shade(skin, 0.66), double=True, bias=0.01, edge=0.0)


# ------------------------------------------------------------------ overlays

def _clip(subject, clip):
    """Sutherland–Hodgman: clip polygon `subject` by convex polygon `clip` (2D)."""
    def inside(p, a, b):
        return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) >= 0

    def inter(p, q, a, b):
        x1, y1 = p
        x2, y2 = q
        x3, y3 = a
        x4, y4 = b
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return q
        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))

    out = list(subject)
    # make clip CCW
    area = sum(clip[i][0] * clip[(i + 1) % len(clip)][1] - clip[(i + 1) % len(clip)][0] * clip[i][1]
               for i in range(len(clip)))
    if area < 0:
        clip = clip[::-1]
    for i in range(len(clip)):
        a, b = clip[i], clip[(i + 1) % len(clip)]
        inp = out
        out = []
        if not inp:
            break
        s = inp[-1]
        for e in inp:
            if inside(e, a, b):
                if not inside(s, a, b):
                    out.append(inter(s, e, a, b))
                out.append(e)
            elif inside(s, a, b):
                out.append(inter(s, e, a, b))
            s = e
    return out


def _strip(path, w0, w1):
    """Ribbon polygon along a 2D path with width tapering w0 -> w1."""
    path = np.asarray(path, float)
    left, right = [], []
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, len(path) - 1)]
        t = b - a
        t /= np.linalg.norm(t) + 1e-9
        nrm = np.array([-t[1], t[0]])
        w = lerp(w0, w1, i / (len(path) - 1)) / 2
        left.append(p + nrm * w)
        right.append(p - nrm * w)
    return [tuple(p) for p in left + right[::-1]]


def _bez(p0, p1, p2, n=8):
    p0, p1, p2 = map(np.asarray, (p0, p1, p2))
    return [tuple((1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t * t * p2) for t in np.linspace(0, 1, n)]


def overlays(age, expr):
    """Feature polygons in head space. expr keys: blink, brow, smile, open, gaze(x,y), squint, frown."""
    blink = expr.get("blink", 0.0)
    brow = expr.get("brow", 0.0)
    smile = expr.get("smile", 0.0)
    mopen = expr.get("open", 0.0)
    gx, gy = expr.get("gaze", (0.0, 0.0))
    squint = expr.get("squint", 0.0) + 0.25 * age
    frown = expr.get("frown", 0.0)
    m = Mesh()
    skin = mix(SKIN, SKIN_26, age)
    hair = mix(HAIR_08, HAIR_26, age)
    browc = mix(BROW, mix(BROW, GREY, 0.35), age)

    def add2d(pts2, rgb, bias, out=0.014, **opt):
        idx = [m.add_v(surface_at(x, y, age, out)) for x, y in pts2]
        opt.setdefault("double", True)
        m.add_f(tuple(idx), rgb, bias=bias, **opt)

    for s in (-1, 1):
        ex, ey = 0.285 * s, 0.118
        hw = 0.136
        top_h = (0.058 - 0.012 * squint) * (1 - blink)
        bot_h = 0.03 - 0.006 * squint
        outer_drop = -0.012 - 0.008 * age
        xs = np.linspace(-1, 1, 9)
        upper, lower = [], []
        for u in xs:
            x = ex + s * u * hw
            lift = outer_drop * max(u, 0)
            upper.append((x, ey + lift + top_h * (1 - u * u) ** 0.8 + 0.006 * (1 - abs(u))))
            lower.append((x, ey + lift - bot_h * (1 - u * u) ** 1.2))
        almond = upper + lower[::-1][1:-1]
        if blink < 0.9:
            add2d(almond, SCLERA, 0.06, flat=False, jit=0.0, bright=0.82, edge=0.0)
            ic = (ex + gx * 0.05 + 0.004 * s, ey + 0.004 + gy * 0.02)
            iris = [(ic[0] + 0.053 * math.cos(a), ic[1] + 0.056 * math.sin(a))
                    for a in np.linspace(0, 2 * math.pi, 12, endpoint=False)]
            ip = _clip(iris, almond)
            if len(ip) >= 3:
                add2d(ip, IRIS, 0.11, jit=0.0, edge=0.0)
            pup = [(ic[0] + 0.021 * math.cos(a), ic[1] + 0.022 * math.sin(a))
                   for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)]
            pp = _clip(pup, almond)
            if len(pp) >= 3:
                add2d(pp, hexc("#110b08"), 0.13, flat=True)
            hl = [(ic[0] - 0.018, ic[1] + 0.016), (ic[0] - 0.006, ic[1] + 0.02), (ic[0] - 0.012, ic[1] + 0.006)]
            if all(_inside_poly(p, almond) for p in hl):
                add2d(hl, hexc("#f4efe8"), 0.15, flat=True)
        # upper lid line + lashes
        add2d(_strip(upper, 0.014, 0.014), LASH, 0.16, flat=True)
        # heavy, hooded upper lid fold
        crease = [(x, y + 0.035 + 0.01 * (1 - age)) for x, y in upper]
        add2d(_strip(crease, 0.01, 0.014), shade(skin, 0.72), 0.05, alpha=0.75, flat=False, edge=0.0)
        # lower lid
        add2d(_strip(lower[1:-1], 0.006, 0.006), shade(skin, 0.7), 0.05, alpha=0.8, edge=0.0)
        # brows: fairly straight, dark, high over the ridge
        by = 0.262 + 0.035 * brow - 0.02 * frown
        bpath = [(s * 0.075, by - 0.012 - 0.02 * frown), (s * 0.20, by + 0.018), (s * 0.33, by + 0.028),
                 (s * 0.43, by + 0.012), (s * 0.49, by - 0.012)]
        add2d(_strip(bpath, 0.052 - 0.01 * age, 0.024), browc, 0.05, out=0.02, jit=0.06, edge=0.0)
        # age lines
        if age > 0.01:
            a = age
            bag = _bez((ex - s * 0.08, ey - 0.055), (ex + s * 0.01, ey - 0.095), (ex + s * 0.10, ey - 0.05), 7)
            add2d(_strip(bag, 0.008, 0.012), shade(skin, 0.68), 0.04, alpha=0.75 * a, edge=0.0)
            bag2 = _bez((ex - s * 0.07, ey - 0.075), (ex + s * 0.01, ey - 0.12), (ex + s * 0.10, ey - 0.07), 7)
            add2d(_strip(bag2, 0.006, 0.006), shade(skin, 0.80), 0.04, alpha=0.5 * a, edge=0.0)
            for k in range(2):
                yy = ey + 0.015 - k * 0.03
                cf = [(ex + s * 0.13, yy), (ex + s * 0.17, yy + 0.008 - k * 0.012)]
                add2d(_strip(cf, 0.006, 0.003), shade(skin, 0.72), 0.04, alpha=0.6 * a, edge=0.0)
        # nasolabial fold
        nl = _bez((s * 0.155, -0.36), (s * 0.255, -0.47), (s * 0.255, -0.67 - 0.02 * age), 8)
        add2d(_strip(nl, 0.010 + 0.01 * age, 0.004), shade(skin, 0.75), 0.03, alpha=0.35 + 0.45 * age, edge=0.0)
        if age > 0.01:
            mar = _bez((s * 0.20, -0.72), (s * 0.22, -0.80), (s * 0.19, -0.88), 5)
            add2d(_strip(mar, 0.008, 0.002), shade(skin, 0.78), 0.03, alpha=0.5 * age, edge=0.0)
        # nostril
        nost = [(s * 0.075, -0.435), (s * 0.115, -0.425), (s * 0.135, -0.445), (s * 0.095, -0.455)]
        add2d(nost, hexc("#5a372c"), 0.05, out=0.02, flat=True)
    if age > 0.01:
        for k, yy in enumerate((0.52, 0.60, 0.68)):
            fl = _bez((-0.24 + 0.03 * k, yy), (0, yy + 0.02), (0.24 - 0.03 * k, yy), 7)
            add2d(_strip(fl, 0.006, 0.006), shade(skin, 0.8), 0.03, alpha=0.45 * age, edge=0.0)
        # frown line between brows
        add2d(_strip([(-0.035, 0.22), (-0.03, 0.29)], 0.006, 0.004), shade(skin, 0.76), 0.03, alpha=0.6 * age)
        add2d(_strip([(0.035, 0.22), (0.03, 0.29)], 0.006, 0.004), shade(skin, 0.76), 0.03, alpha=0.6 * age)
    # mouth line
    cy = -0.612
    corner = cy + 0.025 * smile - 0.012 * frown - 0.008 * age
    half = 0.185 + 0.02 * smile
    if mopen > 0.05:
        up = [(x, cy + 0.008 + 0.012 * (1 - (x / half) ** 2)) for x in np.linspace(-half, half, 9)]
        lo = [(x, cy - mopen * 0.075 * (1 - (x / half) ** 2) ** 0.7) for x in np.linspace(half, -half, 9)]
        up[0] = (up[0][0], corner)
        up[-1] = (up[-1][0], corner)
        add2d(up + lo[1:-1], hexc("#3b1d18"), 0.06, flat=True)
        teeth = [(x, cy + 0.004 - 0.016 * (1 - (x / half) ** 2)) for x in np.linspace(-half * 0.7, half * 0.7, 7)]
        teeth = [(x, cy + 0.008) for x, _ in teeth[::-1]] + teeth
        add2d(teeth, hexc("#e9e2d6"), 0.065, flat=True)
    else:
        line = []
        for x in np.linspace(-half, half, 11):
            u = abs(x) / half
            line.append((x, lerp(cy, corner, u ** 2) + 0.004 * (1 - u)))
        add2d(_strip(line, 0.014, 0.014), hexc("#7a4038"), 0.06, flat=True)
    return m


def _inside_poly(p, poly):
    x, y = p
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
    return inside


def head_mesh(age, expr=None):
    base = build_head(int(round(age * 100)))
    ov = overlays(age, expr or {})
    m = Mesh()
    m.v = list(base.v)
    m.f = list(base.f)
    m.extend(ov)
    return m
