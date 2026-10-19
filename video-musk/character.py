"""Folded-paper body joined to the low-poly head.

The neck is lofted from inside the jaw down into the collar, so head, neck and
torso are one continuous faceted surface. Clothes are cut as separate paper
layers (lapels, collar) sitting slightly proud of the torso with a visible edge.

Units: head ~2.5 tall, head centre at y=0. Character faces +z.
"""
import math
from functools import lru_cache

import numpy as np

from gfx import hexc, mix, shade, lerp, smooth, clamp
from head import head_mesh, SKIN, SKIN_26
from mesh import Mesh, loft, euler, rot_x, rot_y, rot_z

OUTFITS = {
    # 2008: charcoal suit jacket, white open-collar shirt
    "suit08": dict(jacket=hexc("#3a3f49"), shirt=hexc("#e9e6df"), trousers=hexc("#2a2d33"), tee=False),
    # 2026: black tee under a dark grey work jacket
    "tee26": dict(jacket=hexc("#3b3d44"), shirt=hexc("#1c1d22"), trousers=hexc("#25272c"), tee=True),
    # factory / launch site
    "work": dict(jacket=hexc("#1d2026"), shirt=hexc("#1a1b1f"), trousers=hexc("#2a2d33"), tee=True),
}


def _ring(y, w, df, db, n=14, zc=0.0, flat=0.35):
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n
        s, c = math.sin(a), math.cos(a)
        # squarish cross-section, flatter front
        sx = math.copysign(abs(s) ** (1 - flat), s)
        cz = math.copysign(abs(c) ** (1 - flat * 0.6), c)
        z = (df if c > 0 else db) * cz
        pts.append((w * sx, y, zc + z))
    return pts


def _orient_out(m, inner):
    v = np.asarray(m.v)
    out = []
    for idx, rgb, opt in m.f:
        p = v[list(idx)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if np.dot(n, p.mean(0) - inner(p.mean(0))) < 0:
            idx = tuple(reversed(idx))
        out.append((idx, rgb, opt))
    m.f = out
    return m


def neck_mesh(age):
    skin = mix(SKIN, SKIN_26, age)
    secs = []
    for y, r in ((-0.55, 0.47), (-1.05, 0.48), (-1.5, 0.5), (-1.95, 0.54), (-2.2, 0.6)):
        secs.append(_ring(y, r, r * 0.98, r * 0.95, n=10, zc=-0.17, flat=0.1))

    def fn(i, j, c):
        if i < 0 or i >= len(secs):
            return None, {}
        # throat shadow under the jaw
        col = skin if c[2] < -0.05 or c[1] < -1.2 else shade(skin, 0.86)
        return col, {"jit": 0.04, "edge": 0.04}

    m = loft(secs, fn, cap0=False, cap1=False)
    return _orient_out(m, lambda c: np.array([0, c[1], -0.17]))


@lru_cache(maxsize=8)
def torso_mesh(outfit, age_key):
    age = age_key / 100.0
    o = OUTFITS[outfit]
    jk, sh = o["jacket"], o["shirt"]
    rows = [
        (-1.98, 0.62, 0.48, 0.50, 0.15),
        (-2.22, 1.25, 0.62, 0.62, 0.30),
        (-2.55, 1.64, 0.72, 0.70, 0.45),
        (-3.05, 1.63, 0.80, 0.74, 0.40),
        (-3.9, 1.60, 0.82, 0.74, 0.35),
        (-4.9, 1.46, 0.76, 0.70, 0.35),
        (-5.9, 1.42, 0.72, 0.68, 0.35),
        (-6.3, 1.40, 0.70, 0.66, 0.35),
    ]
    secs = [_ring(y, w * (1 + 0.04 * age * (y < -3)), df * (1 + 0.06 * age * (y < -3.5)), db, n=16,
                  zc=-0.2, flat=fl) for y, w, df, db, fl in rows]

    def fn(i, j, c):
        if i < 0:
            return None, {}
        if i >= len(secs):
            return shade(o["trousers"], 0.8), {}
        x, y, z = c
        col = jk
        if z > 0 and o["tee"]:
            if outfit != "tee26" or abs(x) < 0.66 + 0.06 * (y < -3.0):
                col = sh
        return col, {"jit": 0.06, "edge": 0.09}

    m = loft(secs, fn, cap0=False, cap1=True)
    _orient_out(m, lambda c: np.array([0, c[1], -0.2]))
    # lapels / collar as raised paper flaps
    if not o["tee"]:
        vee = [(-0.5, -1.96), (0.5, -1.96), (0.36, -2.6), (0.0, -3.75), (-0.36, -2.6)]
        _flap(m, vee, sh, shade(sh, 0.75), rows, lift=0.025)
        for s in (-1, 1):
            lap = [(s * 0.40, -2.0), (s * 0.66, -2.12), (s * 0.84, -2.55), (s * 0.70, -2.66),
                   (s * 0.92, -2.84), (s * 0.62, -3.55), (s * 0.04, -3.98), (s * 0.30, -2.75)]
            _flap(m, lap, shade(jk, 1.12), shade(jk, 0.55), rows, lift=0.06)
            col = [(s * 0.12, -1.96), (s * 0.48, -1.9), (s * 0.5, -2.3), (s * 0.26, -2.5)]
            _flap(m, col, shade(sh, 1.0), shade(sh, 0.7), rows, lift=0.09)
        # buttons
        for by in (-4.25, -4.95):
            _flap(m, [(-0.06 + 0.06 * math.cos(a), by + 0.06 * math.sin(a)) for a in np.linspace(0, 6.2, 6)],
                  shade(jk, 0.6), shade(jk, 0.4), rows, lift=0.05)
    else:
        # crew neck rib
        ring_in, ring_out = [], []
        for a in np.linspace(-math.pi, math.pi, 13):
            x = 0.56 * math.sin(a)
            z = -0.2 + 0.55 * math.cos(a)
            ring_in.append((x, -1.97, z))
            ring_out.append((x * 1.12, -2.05, -0.2 + (z + 0.2) * 1.1))
        ii = [m.add_v(p) for p in ring_in]
        oo = [m.add_v(p) for p in ring_out]
        for k in range(len(ii) - 1):
            m.add_f((ii[k], ii[k + 1], oo[k + 1], oo[k]), shade(sh, 1.25), double=True, edge=0.1)
        if False:
            for s in (-1, 1):
                lap = [(s * 0.58, -2.0), (s * 1.05, -2.25), (s * 1.2, -3.4), (s * 1.15, -5.9), (s * 0.78, -5.9),
                       (s * 0.72, -3.0)]
                _flap(m, lap, shade(jk, 1.15), shade(jk, 0.55), rows, lift=0.05)
    return m


def _front_z(rows, x, y):
    ys = [r[0] for r in rows]
    w = np.interp(-y, [-v for v in ys], [r[1] for r in rows])
    df = np.interp(-y, [-v for v in ys], [r[2] for r in rows])
    fl = np.interp(-y, [-v for v in ys], [r[4] for r in rows])
    s = clamp(abs(x) / w, 0, 0.999)
    # invert sx = s^(1-fl) -> sin(a)
    sa = s ** (1 / (1 - fl))
    c = math.sqrt(max(0.0, 1 - sa * sa))
    return -0.2 + df * c ** (1 - fl * 0.6)


def _flap(m, pts2, rgb, side, rows, lift=0.05):
    top = [m.add_v((x, y, _front_z(rows, x, y) + lift)) for x, y in pts2]
    bot = [m.add_v((x, y, _front_z(rows, x, y) - 0.01)) for x, y in pts2]
    m.add_f(tuple(top), rgb, double=True, bias=0.04, edge=0.15)
    n = len(top)
    for i in range(n):
        j = (i + 1) % n
        m.add_f((top[i], top[j], bot[j], bot[i]), side, double=True, bias=0.035, edge=0.0)


@lru_cache(maxsize=16)
def limb(r0, r1, length, sides, rgb, cuff=None):
    secs = []
    for t, r in ((0, r0), (0.5, (r0 + r1) / 2 * 1.04), (1, r1)):
        secs.append([(r * math.cos(2 * math.pi * j / sides), -t * length, r * 0.92 * math.sin(2 * math.pi * j / sides))
                     for j in range(sides)])

    def fn(i, j, c):
        if i < 0:
            return rgb, {"edge": 0.08}
        if i >= len(secs):
            return (cuff or shade(rgb, 0.8)), {"edge": 0.08}
        return rgb, {"jit": 0.07, "edge": 0.1}

    m = loft(secs, fn, tri=False)
    return _orient_out(m, lambda c: np.array([0, c[1], 0]))


@lru_cache(maxsize=4)
def hand_mesh(age_key):
    age = age_key / 100.0
    skin = shade(mix(SKIN, SKIN_26, age), 0.96)
    m = Mesh()
    # palm + fingers block (low poly mitten) and thumb, along -y
    prof = [(0.0, 0.26, 0.11), (-0.35, 0.30, 0.12), (-0.62, 0.28, 0.10), (-0.85, 0.22, 0.08)]
    secs = []
    for y, w, d in prof:
        secs.append([(w * math.copysign(abs(math.cos(a)) ** 0.6, math.cos(a)), y,
                      d * math.copysign(abs(math.sin(a)) ** 0.6, math.sin(a))) for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
    hm = loft(secs, lambda i, j, c: (skin, {"edge": 0.12}), tri=False)
    _orient_out(hm, lambda c: np.array([0, c[1], 0]))
    m.extend(hm)
    th = limb(0.08, 0.06, 0.38, 5, skin)
    m.extend(th, R=rot_z(0.7) @ rot_y(0.3), T=(0.22, -0.18, 0.05))
    return m


def arm_items(side, age, outfit, pose, R0, T0):
    """Shoulder → elbow → wrist chain. pose: (sh_pitch, sh_roll, sh_yaw, elbow, wrist_pitch)."""
    o = OUTFITS[outfit]
    sleeve = o["jacket"] if not (o["tee"] and outfit == "work") else o["jacket"]
    p_sh, r_sh, y_sh, elb, wr = pose
    s = side
    shoulder = np.array([s * 1.5, -2.62, -0.2])
    Ru = euler(y_sh * s, p_sh, s * r_sh)
    up = limb(0.42, 0.34, 2.75, 8, shade(sleeve, 1.04))
    fo = limb(0.34, 0.27, 2.45, 8, sleeve, cuff=OUTFITS[outfit]["shirt"])
    Rf = Ru @ rot_x(elb)
    elbow = shoulder + Ru @ np.array([0, -2.75, 0])
    wrist = elbow + Rf @ np.array([0, -2.45, 0])
    Rh = Rf @ rot_x(wr)
    hand = hand_mesh(int(round(age * 100)))
    items = [
        (up, R0 @ Ru, R0 @ shoulder + T0),
        (fo, R0 @ Rf, R0 @ elbow + T0),
        (hand, R0 @ Rh @ rot_y(-s * 0.2), R0 @ (wrist + Rh @ np.array([0, -0.02, 0])) + T0),
    ]
    return items, R0 @ wrist + T0


DEFAULT_POSE = dict(
    head=(0.0, 0.0, 0.0),            # yaw, pitch, roll of head relative to torso
    body=(0.0, 0.0, 0.0),            # yaw, pitch(lean), roll of torso
    armL=(0.08, 0.12, 0.0, -0.25, 0.0),
    armR=(0.08, 0.12, 0.0, -0.25, 0.0),
)


BODY_DY = 0.62


def character_items(age, outfit="suit08", pose=None, expr=None, root=(0, 0, 0), root_yaw=0.0, scale=1.0):
    pose = dict(DEFAULT_POSE, **(pose or {}))
    R_root = rot_y(root_yaw) * scale
    T_root = np.asarray(root, float)
    by, bp, br = pose["body"]
    Rb = R_root @ euler(by, bp, br)
    pivot_waist = np.array([0, -6.0, -0.2])
    Tb = T_root + R_root @ pivot_waist - Rb @ pivot_waist + R_root @ np.array([0, BODY_DY, 0])
    items = [(torso_mesh(outfit, int(round(age * 100))), Rb, Tb),
             (neck_mesh(age), Rb, Tb)]
    hy, hp, hr = pose["head"]
    neck_pivot = np.array([0, -1.05, -0.17])
    Rh = Rb @ euler(hy, hp, hr)
    Th = Tb + Rb @ neck_pivot - Rh @ (neck_pivot + np.array([0, BODY_DY, 0]))
    items.append((head_mesh(age, expr or {}), Rh, Th))
    for side, key in ((1, "armL"), (-1, "armR")):
        ai, _ = arm_items(side, age, outfit, pose[key], Rb, Tb)
        items.extend(ai)
    return items
