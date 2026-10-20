"""Flat-shaded low-poly mesh renderer (painter's algorithm on a cairo context).

Every face is filled with one colour lit by a fixed key/fill light, so neighbouring
facets meet at a hard crease – the folded-paper look. Meshes are combined into one
draw list and sorted back to front.
"""
import math

import numpy as np

from gfx import clamp, hash01


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], float)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], float)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], float)


def euler(yaw=0.0, pitch=0.0, roll=0.0):
    return rot_y(yaw) @ rot_x(pitch) @ rot_z(roll)


class Mesh:
    """verts: list of xyz; faces: list of (index tuple, rgb, opts dict)."""

    def __init__(self):
        self.v = []
        self.f = []

    def add_v(self, p):
        self.v.append(tuple(float(c) for c in p))
        return len(self.v) - 1

    def add_f(self, idx, rgb, **opt):
        self.f.append((tuple(idx), tuple(rgb), opt))

    def extend(self, other, R=None, T=(0, 0, 0)):
        base = len(self.v)
        vs = np.asarray(other.v, float)
        if R is not None:
            vs = vs @ np.asarray(R).T
        vs = vs + np.asarray(T, float)
        self.v.extend(map(tuple, vs))
        for idx, rgb, opt in other.f:
            self.f.append((tuple(i + base for i in idx), rgb, opt))
        return self


class Camera:
    def __init__(self, pos, target, fov_deg=35.0, cx=960, cy=540, h=1080, roll=0.0):
        self.pos = np.asarray(pos, float)
        self.target = np.asarray(target, float)
        fwd = self.target - self.pos
        fwd /= np.linalg.norm(fwd)
        up = np.array([0, 1, 0.0])
        right = np.cross(fwd, up)
        right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        if roll:
            c, s = math.cos(roll), math.sin(roll)
            right, up = right * c + up * s, -right * s + up * c
        self.R = np.stack([right, up, -fwd])  # world -> camera
        self.f = (h / 2) / math.tan(math.radians(fov_deg) / 2)
        self.cx, self.cy = cx, cy

    def to_cam(self, p):
        return (np.asarray(p, float) - self.pos) @ self.R.T

    def project(self, p):
        """World points (N,3) -> screen (N,2), camera depth (N,) (positive = in front)."""
        pc = self.to_cam(p)
        z = -pc[..., 2]
        zz = np.maximum(z, 1e-3)
        x = self.cx + self.f * pc[..., 0] / zz
        y = self.cy - self.f * pc[..., 1] / zz
        return np.stack([x, y], -1), z


KEY = np.array([-0.55, 0.62, 0.56])
KEY /= np.linalg.norm(KEY)
FILL = np.array([0.7, -0.15, 0.45])
FILL /= np.linalg.norm(FILL)


def draw(ctx, cam, items, key=KEY, fill=FILL, amb=0.44, kd=0.56, kf=0.12,
         edge_a=0.10, tint_shadow=(0.93, 0.96, 1.06), light_rgb=(1.0, 1.0, 1.0)):
    """items: list of (Mesh, R (3x3), T (3,)). Lights are in world space."""
    polys = []
    for mesh, R, T in items:
        if not mesh.f:
            continue
        vs = np.asarray(mesh.v, float) @ np.asarray(R).T + np.asarray(T, float)
        scr, dep = cam.project(vs)
        campos = cam.pos
        for fi, (idx, rgb, opt) in enumerate(mesh.f):
            pts = vs[list(idx)]
            if len(idx) >= 3:
                n = np.cross(pts[1] - pts[0], pts[2] - pts[0])
                if len(idx) > 3:
                    n = n + np.cross(pts[2] - pts[0], pts[3 % len(idx)] - pts[0])
                ln = np.linalg.norm(n)
                if ln < 1e-12:
                    continue
                n = n / ln
            c = pts.mean(0)
            view = campos - c
            facing = float(np.dot(n, view))
            if facing <= 0:
                if not opt.get("double"):
                    continue
                n = -n
            d = dep[list(idx)]
            if d.min() <= 0.05:
                continue
            if opt.get("flat"):
                col = rgb
            else:
                dk = max(0.0, float(np.dot(n, key)))
                df = max(0.0, float(np.dot(n, fill)))
                jit = 1.0 + (hash01(fi, len(mesh.f)) - 0.5) * opt.get("jit", 0.05)
                k = (amb + kd * dk + kf * df) * jit * opt.get("bright", 1.0)
                lit = clamp((k - amb) / kd)
                col = tuple(clamp(ch * k * (t + (1 - t) * lit) * lc)
                            for ch, t, lc in zip(rgb, tint_shadow, light_rgb))
            zkey = float(d.mean()) - opt.get("bias", 0.0)
            polys.append((zkey, scr[list(idx)], col, opt))
    polys.sort(key=lambda p: -p[0])
    for _, pts, col, opt in polys:
        a = opt.get("alpha", 1.0)
        ctx.move_to(*pts[0])
        for p in pts[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.set_source_rgba(*col, a)
        if a >= 0.999:
            ctx.fill_preserve()
            ctx.set_line_width(0.9)
            ctx.stroke_preserve()  # seal hairline seams between facets
            ea = opt.get("edge", edge_a)
            if ea > 0:
                ctx.set_source_rgba(*(min(1, ch * 1.18 + 0.03) for ch in col), ea)
                ctx.set_line_width(0.8)
                ctx.stroke()
            else:
                ctx.new_path()
        else:
            ctx.fill()
    return polys


# ---------------------------------------------------------------- primitives

def loft(sections, rgb_fn, closed=True, cap0=True, cap1=True, tri=True):
    """Join a list of equal-length rings (each a list of xyz) into a skin.

    rgb_fn(i, j, centre) -> (rgb, opts) for quad between ring i/i+1 and point j/j+1.
    """
    m = Mesh()
    rings = []
    for ring in sections:
        rings.append([m.add_v(p) for p in ring])
    n = len(rings[0])
    for i in range(len(rings) - 1):
        a, b = rings[i], rings[i + 1]
        for j in range(n if closed else n - 1):
            k = (j + 1) % n
            quad = (a[j], a[k], b[k], b[j])
            ctr = np.mean([m.v[q] for q in quad], 0)
            rgb, opt = rgb_fn(i, j, ctr)
            if rgb is None:
                continue
            if tri:
                if (i + j) % 2:
                    m.add_f((a[j], a[k], b[k]), rgb, **opt)
                    m.add_f((a[j], b[k], b[j]), rgb, **opt)
                else:
                    m.add_f((a[j], a[k], b[j]), rgb, **opt)
                    m.add_f((a[k], b[k], b[j]), rgb, **opt)
            else:
                m.add_f(quad, rgb, **opt)
    if cap0:
        ctr = np.mean([m.v[q] for q in rings[0]], 0)
        rgb, opt = rgb_fn(-1, 0, ctr)
        if rgb is not None:
            m.add_f(tuple(reversed(rings[0])), rgb, **opt)
    if cap1:
        ctr = np.mean([m.v[q] for q in rings[-1]], 0)
        rgb, opt = rgb_fn(len(rings), 0, ctr)
        if rgb is not None:
            m.add_f(tuple(rings[-1]), rgb, **opt)
    return m


def cylinder(r0, r1, length, sides, rgb, axis="y", cap=True, rgb_cap=None, opt=None):
    opt = opt or {}
    secs = []
    for t, r in ((0.0, r0), (1.0, r1)):
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides
            u, v = r * math.cos(a), r * math.sin(a)
            h = t * length
            if axis == "y":
                ring.append((u, -h, v))
            elif axis == "x":
                ring.append((h, u, v))
            else:
                ring.append((u, v, h))
        secs.append(ring)
    capc = rgb_cap or rgb

    def fn(i, j, c):
        if i < 0 or i >= 2:
            return (capc, opt) if cap else (None, {})
        return rgb, opt

    m = loft(secs, fn, cap0=cap, cap1=cap, tri=False)
    if axis == "y":
        # loft winding for -y growth is inverted; flip faces
        m.f = [(tuple(reversed(i)), c, o) for i, c, o in m.f]
    return m


def box(sx, sy, sz, rgb, opt=None, center=(0, 0, 0)):
    opt = opt or {}
    m = Mesh()
    cx, cy, cz = center
    for x in (-1, 1):
        for y in (-1, 1):
            for z in (-1, 1):
                m.add_v((cx + x * sx / 2, cy + y * sy / 2, cz + z * sz / 2))
    # index = (x>0)*4 + (y>0)*2 + (z>0)
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in faces:
        m.add_f(f, rgb, **opt)
    return m
