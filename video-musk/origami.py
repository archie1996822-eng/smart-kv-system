"""2D origami / folded-paper drawing kit.

Every shape is a sheet of paper folded along creases: a `pyramid` splits a polygon
into facets around a peak (each facet lit by its own direction), a `fold` splits a
sheet along one crease into a lit and a shaded half. Sheets sit on each other
with soft cast shadows and a thin bright cut edge.
"""
import math

import cairo
import numpy as np

from gfx import clamp, hexc, mix, shade

LIGHT = np.array([-0.62, -0.78])  # light comes from upper-left (screen coords, y down)
LIGHT /= np.linalg.norm(LIGHT)


def _path(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def fill(ctx, pts, rgb, a=1.0):
    _path(ctx, pts)
    ctx.set_source_rgba(*rgb, a)
    ctx.fill()


def shadow(ctx, pts, off=(10, 14), a=0.28, spread=6, steps=4, rgb=(0.04, 0.05, 0.10)):
    """Soft cast shadow: a few stacked, growing translucent copies."""
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    for i in range(steps):
        k = (i + 1) / steps
        grow = spread * k
        q = []
        for x, y in pts:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy) + 1e-6
            q.append((x + off[0] * (0.6 + 0.4 * k) + dx / d * grow, y + off[1] * (0.6 + 0.4 * k) + dy / d * grow))
        fill(ctx, q, rgb, a / steps * 1.2)


def edge(ctx, pts, rgb, a=0.55, lw=1.3):
    _path(ctx, pts)
    ctx.set_source_rgba(*rgb, a)
    ctx.set_line_width(lw)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()


def crease(ctx, a, b, rgb=(1, 1, 1), alpha=0.35, lw=1.1):
    ctx.move_to(*a)
    ctx.line_to(*b)
    ctx.set_source_rgba(*rgb, alpha)
    ctx.set_line_width(lw)
    ctx.stroke()


def tone_for(direction, lo=0.78, hi=1.12):
    d = np.asarray(direction, float)
    n = np.linalg.norm(d)
    if n < 1e-9:
        return (lo + hi) / 2
    d = d / n
    lit = float(np.dot(d, -LIGHT))  # facing the light -> brighter
    return lo + (hi - lo) * (lit + 1) / 2


def pyramid(ctx, pts, peak, rgb, lo=0.78, hi=1.12, creases=True, cut_edge=True, a=1.0, crease_a=0.28):
    """Fold a sheet up to a peak: one facet per polygon edge, each shaded by its outward direction."""
    n = len(pts)
    px, py = peak
    for i in range(n):
        p0, p1 = pts[i], pts[(i + 1) % n]
        mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        k = tone_for((mx - px, my - py), lo, hi)
        fill(ctx, [peak, p0, p1], shade(rgb, k), a)
        # seal hairline seams
        _path(ctx, [peak, p0, p1])
        ctx.set_source_rgba(*shade(rgb, k), a)
        ctx.set_line_width(0.8)
        ctx.stroke()
    if creases:
        for p in pts:
            crease(ctx, peak, p, mix(rgb, (1, 1, 1), 0.55), crease_a * a, 1.0)
    if cut_edge:
        edge(ctx, pts, mix(rgb, (1, 1, 1), 0.5), 0.45 * a, 1.1)


def fold(ctx, pts, a_idx, b_idx, rgb, k_a=1.1, k_b=0.82, a=1.0, cut_edge=True):
    """Split polygon along crease pts[a_idx]–pts[b_idx]; first half lit, second shaded."""
    if a_idx > b_idx:
        a_idx, b_idx = b_idx, a_idx
    half1 = pts[a_idx:b_idx + 1]
    half2 = pts[b_idx:] + pts[:a_idx + 1]
    fill(ctx, half1, shade(rgb, k_a), a)
    fill(ctx, half2, shade(rgb, k_b), a)
    crease(ctx, pts[a_idx], pts[b_idx], mix(rgb, (1, 1, 1), 0.6), 0.4 * a)
    if cut_edge:
        edge(ctx, pts, mix(rgb, (1, 1, 1), 0.5), 0.45 * a, 1.1)


def sheet(ctx, pts, rgb, a=1.0, cut_edge=True, shade_k=1.0):
    fill(ctx, pts, shade(rgb, shade_k), a)
    if cut_edge:
        edge(ctx, pts, mix(rgb, (1, 1, 1), 0.5), 0.4 * a, 1.1)


def strip_facets(ctx, outer, inner, rgb, lo=0.8, hi=1.1, a=1.0, alt=0.06):
    """Accordion-folded band between two polylines: every segment its own facet."""
    for i in range(len(outer) - 1):
        q = [outer[i], outer[i + 1], inner[i + 1], inner[i]]
        d = (outer[i + 1][1] - outer[i][1], -(outer[i + 1][0] - outer[i][0]))
        k = tone_for(d, lo, hi) + (alt if i % 2 else -alt)
        fill(ctx, q, shade(rgb, k), a)
        _path(ctx, q)
        ctx.set_source_rgba(*shade(rgb, k), a)
        ctx.set_line_width(0.8)
        ctx.stroke()
        crease(ctx, outer[i], inner[i], mix(rgb, (1, 1, 1), 0.5), 0.25 * a)


def xform(pts, ox=0.0, oy=0.0, s=1.0, rot=0.0, sx=None):
    c, si = math.cos(rot), math.sin(rot)
    sx = s if sx is None else sx
    return [(ox + (x * sx) * c - (y * s) * si, oy + (x * sx) * si + (y * s) * c) for x, y in pts]


def regular(cx, cy, r, n, rot=0.0, jitter=None):
    pts = []
    for i in range(n):
        a = rot + 2 * math.pi * i / n
        rr = r * (jitter[i] if jitter else 1.0)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts
