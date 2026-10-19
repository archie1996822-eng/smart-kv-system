"""Opening stunt: ramp climb -> apex hold -> cold-gas hover -> backflip -> drop -> landing.

Everything is a pure function of t so frames can be rendered in any order.
The thrusters only ever emit cold gas (white / pale blue). There is no warm
colour anywhere in the effect.
"""
import math
from functools import lru_cache

import numpy as np

from car import car_mesh, thruster_world, WHEEL_X
from gfx import (W, H, clamp, ease_in, ease_io, ease_out, hash01, hexc, lerp, mix,
                 poly, seg, shade, smooth, fill_poly)
from mesh import Camera, Mesh, box, cylinder, draw, euler, rot_z, KEY

# ----------------------------------------------------------------- timing
T_LAUNCH = 1.00     # leaves the ramp lip
T_APEX = 1.58       # top of the climb, momentary stop
T_JET = 1.50        # thrusters open
T_FLIP0 = 2.50
T_FLIP1 = 3.32
T_DROP1 = 3.88      # touchdown
T_END = 4.40        # hook card follows

RAMP_R = 6.0
RAMP_TH0 = math.radians(20)
RAMP_TH1 = math.radians(80)
RAMP_W = 1.45
LIP = np.array([RAMP_R * math.sin(RAMP_TH1), RAMP_R * (1 - math.cos(RAMP_TH1)), 0.0])
APEX = np.array([6.55, 7.55, 0.0])
LAND = np.array([9.7, 0.0, 0.0])
G_STYLE = 2 * (APEX[1] + 0.35) / (T_DROP1 - T_FLIP1 + 0.3) ** 2

SKY = [hexc(c) for c in ("#162238", "#1d2d48", "#263a5a", "#33496b", "#44607f", "#5b7894", "#7893aa")]
JET_CORE = hexc("#f4f9ff")
JET_MID = hexc("#d6ebff")
JET_OUT = hexc("#a9d2f5")


def _ramp_pose(th):
    p = np.array([RAMP_R * math.sin(th), RAMP_R * (1 - math.cos(th)), 0.0])
    return p, th


def car_state(t):
    """Returns (R, T, pitch, jet_level, phase)."""
    if t < T_LAUNCH:
        u = t / T_LAUNCH
        f = u * (0.62 + 0.38 * u)
        th = lerp(RAMP_TH0, RAMP_TH1, f)
        p, pitch = _ramp_pose(th)
        jet = 0.0
        phase = "climb"
    elif t < T_APEX:
        u = seg(t, T_LAUNCH, T_APEX)
        p = LIP + (APEX - LIP) * ease_out(u, 2.0)
        pitch = lerp(RAMP_TH1, math.radians(6), ease_io(seg(t, T_LAUNCH + 0.12, T_APEX + 0.06)))
        jet = ease_out(seg(t, T_JET, T_JET + 0.08)) * 1.25
        phase = "rise"
    elif t < T_FLIP0:
        u = seg(t, T_APEX, T_FLIP0)
        bob = 0.07 * math.sin((t - T_APEX) * 9.0) * (1 - u * 0.5) - 0.05 * smooth(u)
        p = APEX + np.array([0.15 * u, bob, 0])
        pitch = math.radians(6) * (1 - smooth(seg(t, T_APEX, T_APEX + 0.25))) + 0.03 * math.sin((t - T_APEX) * 7)
        jet = 1.25 - 0.25 * seg(t, T_APEX, T_APEX + 0.2)
        phase = "hover"
    elif t < T_FLIP1:
        u = seg(t, T_FLIP0, T_FLIP1)
        base = APEX + np.array([0.15, -0.05, 0])
        p = base + np.array([lerp(0, 1.25, u), 0.55 * math.sin(math.pi * u), 0])
        pitch = 2 * math.pi * ease_io(u)
        jet = 1.0 * (1 - smooth(seg(t, T_FLIP0 + 0.1, T_FLIP1)))
        phase = "flip"
    elif t < T_DROP1:
        u = seg(t, T_FLIP1, T_DROP1)
        start = APEX + np.array([1.4, -0.05, 0])
        p = start + (LAND - start) * np.array([ease_out(u, 1.3), ease_in(u, 1.75), 0])
        pitch = math.radians(-4) * math.sin(math.pi * u)
        jet = 0.0
        phase = "drop"
    else:
        u = seg(t, T_DROP1, T_DROP1 + 0.45)
        squash = 0.16 * math.exp(-u * 4) * math.sin(u * math.pi * 2.2 + 0.0)
        p = LAND + np.array([0.25 * ease_out(u), -squash, 0])
        pitch = -0.035 * math.exp(-u * 3) * math.sin(u * 9)
        jet = 0.0
        phase = "land"
    R = rot_z(pitch)
    return R, p, pitch, jet, phase


# ----------------------------------------------------------------- camera
CAM_KEYS = [
    # t, pos, target, fov
    (0.00, (0.6, 1.5, 13.0), (3.0, 1.6, 0), 38),
    (0.55, (2.2, 2.3, 14.0), (4.6, 3.3, 0), 38),
    (1.00, (4.6, 3.0, 15.0), (5.9, 5.2, 0), 38),
    (1.50, (10.0, 3.4, 12.0), (6.7, 7.6, 0), 33),
    (2.45, (13.4, 3.8, 9.6), (6.9, 7.8, 0), 31),
    (3.30, (14.6, 3.4, 10.8), (7.8, 7.0, 0), 34),
    (3.85, (12.6, 1.6, 11.4), (9.6, 1.4, 0), 36),
    (4.40, (12.2, 1.45, 10.6), (9.9, 1.2, 0), 36),
]


def _catmull(keys, t, idx):
    ts = [k[0] for k in keys]
    if t <= ts[0]:
        return np.asarray(keys[0][idx], float)
    if t >= ts[-1]:
        return np.asarray(keys[-1][idx], float)
    i = max(j for j in range(len(ts) - 1) if ts[j] <= t)
    p0 = np.asarray(keys[max(i - 1, 0)][idx], float)
    p1 = np.asarray(keys[i][idx], float)
    p2 = np.asarray(keys[i + 1][idx], float)
    p3 = np.asarray(keys[min(i + 2, len(keys) - 1)][idx], float)
    u = (t - ts[i]) / (ts[i + 1] - ts[i])
    u2, u3 = u * u, u * u * u
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3)


def camera_at(t):
    pos = _catmull(CAM_KEYS, t, 1)
    tgt = _catmull(CAM_KEYS, t, 2)
    fov = float(_catmull(CAM_KEYS, t, 3))
    # landing shake
    k = seg(t, T_DROP1, T_DROP1 + 0.35)
    if 0 < k < 1:
        amp = 0.16 * (1 - k) ** 2
        pos = pos + amp * np.array([math.sin(t * 91), math.sin(t * 77 + 1.3), 0])
        tgt = tgt + amp * np.array([math.sin(t * 83 + 2), math.sin(t * 97), 0])
    return Camera(pos, tgt, fov_deg=fov)


# ----------------------------------------------------------------- set pieces

@lru_cache(maxsize=1)
def ramp_mesh():
    m = Mesh()
    deck = hexc("#c9d2dc")
    deck2 = hexc("#b5c0cc")
    rail = hexc("#e6ecf2")
    rail_side = hexc("#8b98a8")
    stripe = hexc("#2fb7c4")
    n = 16
    ths = np.linspace(0, RAMP_TH1, n + 1)
    prev = None
    for i, th in enumerate(ths):
        x, y = RAMP_R * math.sin(th), RAMP_R * (1 - math.cos(th))
        nx, ny = -math.sin(th), math.cos(th)  # inward normal (deck up)
        ring = []
        for z in (-RAMP_W, RAMP_W):
            ring.append(m.add_v((x, y, z)))
        # rails: thick lip on both sides
        rails = []
        for z, zz in ((RAMP_W, RAMP_W + 0.28), (-RAMP_W, -RAMP_W - 0.28)):
            rails.append([m.add_v((x, y, z)), m.add_v((x + nx * 0.45, y + ny * 0.45, z)),
                          m.add_v((x + nx * 0.45, y + ny * 0.45, zz)), m.add_v((x - nx * 0.3, y - ny * 0.3, zz))])
        if prev is not None:
            pr, prails = prev
            col = deck if i % 2 else deck2
            m.add_f((pr[0], pr[1], ring[1], ring[0]), col, edge=0.15, double=True)
            for rr, pp in zip(rails, prails):
                for k in range(4):
                    kk = (k + 1) % 4
                    c = rail if k == 1 else rail_side
                    if k == 2 and i % 3 == 0:
                        c = stripe
                    m.add_f((pp[k], pp[kk], rr[kk], rr[k]), c, edge=0.12, double=True)
        prev = (ring, rails)
    # under-structure: folded trusses
    for i in range(1, n + 1, 2):
        th = ths[i]
        x, y = RAMP_R * math.sin(th), RAMP_R * (1 - math.cos(th))
        if y < 0.4:
            continue
        for z in (-RAMP_W - 0.1, RAMP_W + 0.1):
            b = box(0.22, y, 0.22, hexc("#56657a"), center=(x + 0.25, y / 2, z), opt={"edge": 0.1})
            m.extend(b)
    # base slab
    m.extend(box(7.4, 0.12, 2 * RAMP_W + 1.0, hexc("#5f6d80"), center=(3.2, 0.06, 0), opt={"edge": 0.1}))
    return m


def _ridge(z, x0, x1, base, hmin, hmax, col, seed, step=9.0, thick=2.0):
    rng = np.random.default_rng(seed)
    m = Mesh()
    xs = np.arange(x0, x1 + step, step)
    tops = [(x + rng.uniform(-step * 0.3, step * 0.3), rng.uniform(hmin, hmax)) for x in xs]
    for i in range(len(tops) - 1):
        (xa, ya), (xb, yb) = tops[i], tops[i + 1]
        xm = (xa + xb) / 2 + rng.uniform(-2, 2)
        ym = (ya + yb) / 2 * rng.uniform(0.55, 0.8)
        dz = rng.uniform(-3, 3)
        A = m.add_v((xa, ya, z))
        B = m.add_v((xb, yb, z))
        Mv = m.add_v((xm, ym, z + dz + 2.5))
        Ba = m.add_v((xa, base, z + 1.0))
        Bb = m.add_v((xb, base, z + 1.0))
        cA = shade(col, 1.0 + rng.uniform(-0.05, 0.07))
        m.add_f((A, Mv, Ba), cA, double=True, edge=0.05)
        m.add_f((A, B, Mv), shade(col, 1.12), double=True, edge=0.05)
        m.add_f((Mv, B, Bb), shade(col, 0.9), double=True, edge=0.05)
        m.add_f((Ba, Mv, Bb), shade(col, 0.82), double=True, edge=0.05)
        # cut-paper thickness behind the ridge
        A2 = m.add_v((xa, ya - 0.3, z - thick))
        B2 = m.add_v((xb, yb - 0.3, z - thick))
        m.add_f((A2, B2, B, A), shade(col, 0.6), double=True, edge=0.0)
    return m


@lru_cache(maxsize=1)
def backdrop():
    far = _ridge(-150, -160, 200, -2, 16, 34, hexc("#3a5574"), 4, step=22, thick=4)
    mid = _ridge(-95, -110, 150, -2, 8, 19, hexc("#2c4462"), 9, step=15, thick=3)
    near = _ridge(-60, -80, 110, -1, 3, 8, hexc("#24384f"), 13, step=10, thick=2)
    return [far, mid, near]


@lru_cache(maxsize=1)
def buildings():
    m = Mesh()
    wall = hexc("#3d4f66")
    roof = hexc("#5a6f88")
    # hangar with folded gable roof
    hx, hz = 22.0, -34.0
    m.extend(box(18, 7, 12, wall, center=(hx, 3.5, hz), opt={"edge": 0.1}))
    for s in (-1, 1):
        a = m.add_v((hx - 9.4, 7, hz + s * 6.4))
        b = m.add_v((hx + 9.4, 7, hz + s * 6.4))
        c = m.add_v((hx + 9.4, 10, hz))
        d = m.add_v((hx - 9.4, 10, hz))
        m.add_f((a, b, c, d), shade(roof, 1.0 + 0.12 * s), double=True, edge=0.12)
    # big door panels
    for k in range(4):
        x0 = hx - 7.5 + k * 3.8
        p = [m.add_v(q) for q in ((x0, 0.2, hz + 6.05), (x0 + 3.5, 0.2, hz + 6.05), (x0 + 3.5, 5.6, hz + 6.05), (x0, 5.6, hz + 6.05))]
        m.add_f(tuple(p), shade(wall, 1.15 if k % 2 else 1.05), double=True, bias=0.2, edge=0.15)
    # control tower
    m.extend(box(3, 12, 3, hexc("#344459"), center=(-14, 6, -40), opt={"edge": 0.1}))
    m.extend(box(5.2, 2.4, 5.2, hexc("#4b6280"), center=(-14, 13.2, -40), opt={"edge": 0.12}))
    m.extend(box(5.6, 0.8, 5.6, hexc("#9fb6cc"), center=(-14, 13.0, -40), opt={"edge": 0.0, "flat": True}))
    # light masts
    for x, z in ((-4, -22), (14, -20), (34, -24)):
        m.extend(box(0.4, 9, 0.4, hexc("#3a4a5e"), center=(x, 4.5, z)))
        m.extend(box(1.8, 0.9, 0.5, hexc("#e6f2ff"), center=(x, 9.2, z), opt={"flat": True}))
    # low sheds
    for x, w in ((-28, 10), (44, 12)):
        m.extend(box(w, 3.2, 6, hexc("#33465c"), center=(x, 1.6, -26), opt={"edge": 0.1}))
    return m


@lru_cache(maxsize=1)
def ground_mesh():
    rng = np.random.default_rng(21)
    m = Mesh()
    base = hexc("#6c7a8c")
    zs = [16, 10, 6, 3, 0, -3, -7, -12, -18, -26, -36, -50, -70, -100, -150]
    xs = np.arange(-40, 70, 4.0)
    grid = {}
    for zi, z in enumerate(zs):
        for xi, x in enumerate(xs):
            jx = rng.uniform(-0.8, 0.8)
            grid[(zi, xi)] = m.add_v((x + jx, rng.uniform(-0.03, 0.03) if abs(z) < 30 else 0.0, z))
    for zi in range(len(zs) - 1):
        for xi in range(len(xs) - 1):
            a, b, c, d = grid[(zi, xi)], grid[(zi, xi + 1)], grid[(zi + 1, xi + 1)], grid[(zi + 1, xi)]
            col = shade(base, 0.92 + 0.16 * rng.random())
            far = smooth((-zs[zi] - 20) / 80)
            col = mix(col, hexc("#56677d"), far * 0.6)
            m.add_f((a, b, c), col, edge=0.06, double=True, jit=0.0)
            m.add_f((a, c, d), shade(col, 0.97), edge=0.06, double=True, jit=0.0)
    # landing strip markings
    for k in range(10):
        x = -6 + k * 4.2
        p = [m.add_v(q) for q in ((x, 0.03, 3.4), (x + 2.4, 0.03, 3.4), (x + 2.4, 0.03, 3.0), (x, 0.03, 3.0))]
        m.add_f(tuple(p), hexc("#dfe6ee"), double=True, flat=False, edge=0.0, bias=0.5)
    pad = [m.add_v((LAND[0] + 3.2 * math.cos(a), 0.025, 3.2 * math.sin(a))) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    m.add_f(tuple(pad), hexc("#7f8ea1"), double=True, bias=0.4, edge=0.2)
    return m


@lru_cache(maxsize=1)
def foreground():
    rng = np.random.default_rng(5)
    m = Mesh()
    for k in range(9):
        x = -2 + k * 2.6 + rng.uniform(-0.6, 0.6)
        z = rng.uniform(6.5, 9.0)
        r = rng.uniform(0.35, 0.8)
        top = m.add_v((x, r * 1.3, z))
        ring = [m.add_v((x + r * math.cos(a) * rng.uniform(0.8, 1.2), 0.0, z + r * math.sin(a) * rng.uniform(0.8, 1.2)))
                for a in np.linspace(0, 2 * math.pi, 6, endpoint=False)]
        col = hexc("#4a586a")
        for i in range(6):
            m.add_f((top, ring[i], ring[(i + 1) % 6]), shade(col, 0.95 + 0.1 * rng.random()), double=True, edge=0.08)
    # marker cones: white with teal band (no warm colours on set)
    for x in (3.0, 8.2, 12.6, 15.5):
        c = cylinder(0.32, 0.04, 0.85, 6, hexc("#e9eef3"), axis="y", rgb_cap=hexc("#e9eef3"), opt={"double": True})
        m.extend(c, R=np.diag([1, -1, 1]), T=(x, 0.0, 4.6))
        band = cylinder(0.22, 0.16, 0.2, 6, hexc("#2fb7c4"), axis="y", cap=False, opt={"double": True, "bias": 0.05})
        m.extend(band, R=np.diag([1, -1, 1]), T=(x, 0.3, 4.6))
    return m


# ----------------------------------------------------------------- effects

def _jet_cones(t, R, T, level):
    m = Mesh()
    if level <= 0.01:
        return m
    exits, down = thruster_world(R, T)
    # build an orthonormal frame around `down`
    a = np.array([1.0, 0, 0]) if abs(down[0]) < 0.9 else np.array([0, 0, 1.0])
    u = np.cross(down, a)
    u /= np.linalg.norm(u)
    v = np.cross(down, u)
    for ni, e in enumerate(exits):
        flick = 0.92 + 0.08 * math.sin(t * 53 + ni * 1.7)
        L = (2.4 + 0.6 * math.sin(t * 13 + ni)) * level * flick
        for layer, (r0, r1, Lk, col, al) in enumerate((
                (0.2, 0.7, 1.0, JET_OUT, 0.2), (0.15, 0.45, 0.9, JET_MID, 0.3), (0.09, 0.2, 0.7, JET_CORE, 0.6))):
            sides = 7
            rot = t * 2.0 + ni + layer
            ring0 = [m.add_v(e + r0 * (math.cos(rot + 2 * math.pi * k / sides) * u + math.sin(rot + 2 * math.pi * k / sides) * v))
                     for k in range(sides)]
            tip = e + down * L * Lk
            ring1 = [m.add_v(tip + r1 * level * (math.cos(rot + 0.4 + 2 * math.pi * k / sides) * u +
                                                 math.sin(rot + 0.4 + 2 * math.pi * k / sides) * v))
                     for k in range(sides)]
            for k in range(sides):
                kk = (k + 1) % sides
                m.add_f((ring0[k], ring0[kk], ring1[kk], ring1[k]), col, alpha=al * min(1.0, level), double=True,
                        flat=True, bias=-0.05 * layer)
    return m


def _mist_particles(t):
    """Deterministic particle field for the cold-gas mist. -> list of (pos, radius, alpha, colour)."""
    out = []
    dt = 1 / 60
    t0 = T_JET
    t1 = min(t, T_FLIP0 + 0.12)
    if t1 <= t0:
        return out
    n_emit = int((t1 - t0) / dt)
    for ei in range(0, n_emit + 1, 2):
        te = t0 + ei * dt
        if te > t1:
            break
        R, T, _, level, _ = car_state(te)
        if level <= 0.02:
            continue
        exits, down = thruster_world(R, T)
        age = t - te
        life = 1.0
        if age > life or age < 0:
            continue
        for ni, e in enumerate(exits):
            h = hash01(ei, ni)
            h2 = hash01(ni, ei, 3)
            h3 = hash01(ei * 7, ni * 13, 5)
            spd = (5.5 + 3 * h) * level
            side = np.array([h2 - 0.5, 0, h3 - 0.5]) * 1.4
            # gas slows quickly (drag) and drifts down / outward
            k = 1 - math.exp(-age * 2.6)
            pos = e + down * spd * k / 2.6 + side * k * 0.9 + np.array([0, -0.4 * age * age, 0])
            if pos[1] < 0.15:
                pos[1] = 0.15 + 0.1 * h
            r = 0.14 + 0.75 * k * (0.7 + 0.6 * h)
            a = (1 - age / life) ** 2.2 * 0.16 * min(1, level)
            col = mix(JET_MID, JET_CORE, h2)
            out.append((pos, r, a, col, ei * 4 + ni))
    return out


def _dust_particles(t):
    out = []
    age = t - T_DROP1
    if age <= 0:
        return out
    for i in range(70):
        h = hash01(i, 11)
        h2 = hash01(i, 23)
        ang = 2 * math.pi * hash01(i, 37)
        spd = 2.5 + 5.5 * h
        k = 1 - math.exp(-age * 3.2)
        wheel = (WHEEL_X if i % 2 else -WHEEL_X)
        pos = LAND + np.array([wheel + math.cos(ang) * spd * k / 3.2 * 1.3, 0.08 + 0.45 * h2 * k,
                               (1.1 if i % 4 < 2 else -1.1) + math.sin(ang) * spd * k / 3.2])
        r = 0.18 + 0.6 * k * (0.6 + h)
        a = max(0.0, 1 - age / 0.9) ** 1.6 * 0.3
        col = mix(hexc("#c9d3de"), hexc("#e8eef4"), h2)
        out.append((pos, r, a, col, i))
    return out


def _draw_puffs(ctx, cam, parts):
    if not parts:
        return
    pts = np.array([p[0] for p in parts])
    scr, dep = cam.project(pts)
    order = np.argsort(-dep)
    for i in order:
        pos, r, a, col, seed = parts[i]
        if dep[i] < 0.2 or a < 0.01:
            continue
        rr = cam.f * r / dep[i]
        cx, cy = scr[i]
        n = 7
        rot = hash01(seed, 9) * 6.28
        ring = [(cx + rr * (0.82 + 0.25 * hash01(seed, k)) * math.cos(rot + 2 * math.pi * k / n),
                 cy + rr * (0.82 + 0.25 * hash01(seed, k)) * math.sin(rot + 2 * math.pi * k / n) * 0.86) for k in range(n)]
        # faceted puff: lit upper-left facet, shaded lower-right facet
        poly(ctx, ring)
        ctx.set_source_rgba(*shade(col, 0.86), a)
        ctx.fill()
        hi = ring[3:7] + [(cx, cy)]
        poly(ctx, hi)
        ctx.set_source_rgba(*col, a * 0.9)
        ctx.fill()


def _sky(ctx, cam):
    # horizon line from a far point straight ahead
    far = cam.pos + np.array([0, 0, -1]) * 1000
    far[1] = 0
    hy = float(cam.project(far[None, :])[0][0][1])
    ctx.set_source_rgb(*SKY[0])
    ctx.paint()
    bands = len(SKY)
    for i in range(1, bands):
        y = hy - (bands - i) * 105 + 30
        pts = [(-20, H + 20)]
        for k in range(0, 13):
            x = k * W / 12
            pts.append((x, y + 9 * math.sin(k * 1.7 + i * 2.3)))
        pts.append((W + 20, H + 20))
        fill_poly(ctx, [(x, yy + 6) for x, yy in pts], (0.05, 0.07, 0.12), 0.25)
        fill_poly(ctx, pts, SKY[i])
    # moon: faceted disc, cold
    mx, my = 1520 - (cam.pos[0] * 6), hy - 380 + cam.pos[1] * 4
    ring = [(mx + 46 * math.cos(a), my + 46 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 9)[:-1]]
    fill_poly(ctx, ring, hexc("#dfe8f2"))
    fill_poly(ctx, [ring[0], ring[1], ring[2], ring[3], (mx, my)], hexc("#c3d0de"))
    for i in range(28):
        sx = (hash01(i, 1) * W * 1.4 - cam.pos[0] * 4) % W
        sy = hash01(i, 2) * (hy - 300)
        if sy < 20:
            continue
        s = 2 + 3 * hash01(i, 3)
        fill_poly(ctx, [(sx, sy - s), (sx + s * 0.4, sy), (sx, sy + s), (sx - s * 0.4, sy)], hexc("#dfe8f5"), 0.7)


def _speed_lines(ctx, cam, t):
    k = 1 - seg(t, 0.75, 1.15)
    if k <= 0:
        return
    R, T, pitch, _, _ = car_state(t)
    d = np.array([math.cos(pitch), math.sin(pitch), 0])
    for i in range(9):
        h = hash01(i, 77)
        off = np.array([0, 0, (h - 0.5) * 2.2]) + (hash01(i, 5) - 0.5) * 1.3 * np.array([-d[1], d[0], 0])
        back = 1.6 + 3.0 * hash01(i, int(t * 30) % 5)
        p0 = T + off + d * 0.4 - d * 2.0
        p1 = p0 - d * back
        (s0, s1), _ = cam.project(np.array([p0, p1]))
        nrm = np.array([-(s1[1] - s0[1]), s1[0] - s0[0]])
        nrm /= np.linalg.norm(nrm) + 1e-9
        w = 2.5 + 3 * h
        fill_poly(ctx, [tuple(s0 + nrm * w), tuple(s1), tuple(s0 - nrm * w)], hexc("#e7eef7"), 0.55 * k)


def _car_shadow(R, T):
    m = Mesh()
    h = max(T[1], 0.0)
    a = 0.38 * math.exp(-h / 3.0)
    if a < 0.02:
        return m
    fw = np.array([R[0, 0], 0, R[2, 0]])
    if np.linalg.norm(fw) < 0.2:
        fw = np.array([1.0, 0, 0])
    fw /= np.linalg.norm(fw)
    side = np.array([0, 0, 1.0])
    s = 1 + h * 0.08
    c = np.array([T[0], 0.035, T[2]])
    pts = [c + fw * 2.3 * s * math.cos(a_) + side * 1.0 * s * math.sin(a_) for a_ in np.linspace(0, 2 * math.pi, 9)[:-1]]
    idx = [m.add_v(p) for p in pts]
    m.add_f(tuple(idx), hexc("#1c2533"), alpha=a, double=True, flat=True, bias=0.6)
    return m


def render_open(ctx, t):
    cam = camera_at(t)
    _sky(ctx, cam)
    I = np.eye(3)
    Z = np.zeros(3)
    for layer in backdrop():
        draw(ctx, cam, [(layer, I, Z)], amb=0.6, kd=0.4, edge_a=0.05)
    draw(ctx, cam, [(ground_mesh(), I, Z)], amb=0.62, kd=0.38)
    R, T, pitch, jet, phase = car_state(t)
    draw(ctx, cam, [(_car_shadow(R, T), I, Z)])
    draw(ctx, cam, [(buildings(), I, Z)], amb=0.55, kd=0.45)
    mist = _mist_particles(t) + _dust_particles(t)
    car_depth = float(cam.project(T[None, :])[1][0])
    if mist:
        md = cam.project(np.array([p[0] for p in mist]))[1]
        behind = [p for p, d in zip(mist, md) if d > car_depth + 0.6]
        front = [p for p, d in zip(mist, md) if d <= car_depth + 0.6]
    else:
        behind, front = [], []
    _draw_puffs(ctx, cam, behind)
    _speed_lines(ctx, cam, t)
    items = [(ramp_mesh(), I, Z), (car_mesh(), R, T), (_jet_cones(t, R, T, jet), I, Z)]
    draw(ctx, cam, items, amb=0.5, kd=0.6)
    _draw_puffs(ctx, cam, front)
    draw(ctx, cam, [(foreground(), I, Z)], amb=0.5, kd=0.5)
    return cam
