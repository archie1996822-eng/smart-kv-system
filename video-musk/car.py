"""Generic low-poly roadster (no badge, no brand marks) with four cold-gas
thrusters under the floor. Local frame: +x forward, +y up, +z = right side.
Origin = ground contact point midway between the axles.
"""
import math
from functools import lru_cache

import numpy as np

from gfx import hexc, shade
from mesh import Mesh, cylinder, euler, rot_x

PAINT = hexc("#b3242f")
GLASS = hexc("#1f2b3a")
TRIM = hexc("#1a1c21")
TYRE = hexc("#141518")
RIM = hexc("#b9c0c8")
LAMP = hexc("#eef6ff")
NOZZLE = hexc("#6d7680")

WHEEL_X = 1.38
WHEEL_Z = 0.80
WHEEL_R = 0.36
THRUSTERS = [(1.02, 0.50), (1.02, -0.50), (-1.05, 0.50), (-1.05, -0.50)]

# x, bottom, belt, top, side half-width, top half-width
SECTIONS = [
    (-2.22, 0.34, 0.74, 0.80, 0.78, 0.60),
    (-2.05, 0.24, 0.82, 0.90, 0.90, 0.70),
    (-1.45, 0.21, 0.86, 0.95, 0.95, 0.74),
    (-0.85, 0.21, 0.86, 0.98, 0.94, 0.70),
    (-0.45, 0.21, 0.84, 1.20, 0.92, 0.55),
    (0.20, 0.21, 0.82, 1.22, 0.92, 0.53),
    (0.65, 0.21, 0.80, 1.02, 0.92, 0.66),
    (1.25, 0.21, 0.74, 0.84, 0.94, 0.76),
    (1.85, 0.23, 0.62, 0.68, 0.90, 0.72),
    (2.22, 0.32, 0.46, 0.50, 0.74, 0.56),
]


def _ring(sec):
    x, yb, ym, yt, zw, zt = sec
    pts = [
        (x, yb, zw * 0.84), (x, yb + 0.2, zw), (x, ym, zw * 0.97), (x, yt, zt),
        (x, yt, -zt), (x, ym, -zw * 0.97), (x, yb + 0.2, -zw), (x, yb, -zw * 0.84),
    ]
    return pts


@lru_cache(maxsize=2)
def car_mesh():
    m = Mesh()
    rings = [[m.add_v(p) for p in _ring(s)] for s in SECTIONS]
    n = 8
    for i in range(len(rings) - 1):
        x0, x1 = SECTIONS[i][0], SECTIONS[i + 1][0]
        xm = (x0 + x1) / 2
        cabin = -0.85 <= xm <= 0.65
        for j in range(n):
            k = (j + 1) % n
            quad = (rings[i][j], rings[i + 1][j], rings[i + 1][k], rings[i][k])
            col = PAINT
            opt = {"jit": 0.04, "edge": 0.12}
            if j == 3:  # roof / bonnet / deck
                if cabin:
                    col = GLASS if (xm > 0.3 or xm < -0.6) else TRIM
                    opt = {"jit": 0.02, "edge": 0.2, "bright": 1.15 if col is GLASS else 1.0}
            elif j in (2, 4) and cabin:
                col = GLASS
                opt = {"jit": 0.02, "edge": 0.2, "bright": 1.2}
            elif j == 7:
                col = TRIM
            elif j in (0, 6):
                col = shade(PAINT, 0.8)
            m.add_f(quad, col, **opt)
    # nose and tail caps
    m.add_f(tuple(reversed(rings[0])), shade(PAINT, 0.85), edge=0.12)
    m.add_f(tuple(rings[-1]), shade(PAINT, 0.9), edge=0.12)
    _orient(m)
    # lamps (flat inset quads)
    for s in (1, -1):
        m.add_f(_quad(m, [(2.05, 0.60, s * 0.40), (2.12, 0.55, s * 0.70), (1.92, 0.66, s * 0.80), (1.86, 0.70, s * 0.46)]),
                LAMP, flat=True, bias=0.03, double=True)
        m.add_f(_quad(m, [(-2.2, 0.76, s * 0.25), (-2.2, 0.76, s * 0.58), (-2.12, 0.84, s * 0.64), (-2.12, 0.84, s * 0.28)]),
                hexc("#7d1420"), flat=True, bias=0.03, double=True)
        # side intake fold
        m.add_f(_quad(m, [(-0.9, 0.42, s * 0.955), (-0.3, 0.40, s * 0.95), (-0.45, 0.62, s * 0.955), (-0.95, 0.60, s * 0.958)]),
                shade(PAINT, 0.55), bias=0.02, double=True, edge=0.0)
    # wheels
    for wx in (WHEEL_X, -WHEEL_X):
        for s in (1, -1):
            w = cylinder(WHEEL_R, WHEEL_R, 0.28, 10, TYRE, axis="z", rgb_cap=TYRE)
            m.extend(w, T=(wx, WHEEL_R, s * WHEEL_Z - (0.28 if s > 0 else 0)))
            rim = cylinder(0.22, 0.22, 0.02, 5, RIM, axis="z")
            m.extend(rim, T=(wx, WHEEL_R, s * (WHEEL_Z + 0.29) - (0.02 if s > 0 else 0)))
    # thruster nozzles under the floor
    for tx, tz in THRUSTERS:
        noz = cylinder(0.13, 0.17, 0.16, 8, NOZZLE, axis="y", rgb_cap=hexc("#cfe9ff"))
        m.extend(noz, T=(tx, 0.22, tz))
    _orient_parts(m)
    return m


def _quad(m, pts):
    return tuple(m.add_v(p) for p in pts)


def _orient(m):
    v = np.asarray(m.v)
    out = []
    for idx, rgb, opt in m.f:
        p = v[list(idx)]
        n = np.cross(p[1] - p[0], p[2] - p[0])
        c = p.mean(0)
        if np.dot(n, c - np.array([c[0] * 0.6, 0.6, 0.0])) < 0:
            idx = tuple(reversed(idx))
        out.append((idx, rgb, opt))
    m.f = out


def _orient_parts(m):
    """Make wheel / nozzle faces point away from their own axis."""
    v = np.asarray(m.v)
    out = []
    for idx, rgb, opt in m.f:
        p = v[list(idx)]
        c = p.mean(0)
        n = np.cross(p[1] - p[0], p[2] - p[0])
        if rgb in (TYRE, RIM):
            wx = WHEEL_X if c[0] > 0 else -WHEEL_X
            axis_pt = np.array([wx, WHEEL_R, 0.0])
            ref = c - axis_pt
            if abs(n[2]) / (np.linalg.norm(n) + 1e-9) > 0.9:
                ref = np.array([0, 0, c[2]])
            else:
                ref[2] = 0
            if np.dot(n, ref) < 0:
                idx = tuple(reversed(idx))
        elif rgb == NOZZLE or rgb == hexc("#cfe9ff"):
            tx = min(THRUSTERS, key=lambda t: (t[0] - c[0]) ** 2 + (t[1] - c[2]) ** 2)
            ref = c - np.array([tx[0], c[1], tx[1]])
            if abs(n[1]) / (np.linalg.norm(n) + 1e-9) > 0.9:
                ref = np.array([0, -1.0, 0])
            if np.dot(n, ref) < 0:
                idx = tuple(reversed(idx))
        out.append((idx, rgb, opt))
    m.f = out


def thruster_world(R, T):
    """World positions of the 4 nozzle exits and the car's down vector."""
    R = np.asarray(R)
    down = R @ np.array([0, -1.0, 0])
    return [R @ np.array([tx, 0.05, tz]) + T for tx, tz in THRUSTERS], down
