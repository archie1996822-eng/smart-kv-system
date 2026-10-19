"""Small drawing helpers shared by every module: easing, colour, paper texture."""
import math

import cairo
import numpy as np

W, H, FPS = 1920, 1080, 30


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, a, b):
    """0..1 progress of t inside [a, b]."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_in(t, p=2.0):
    return clamp(t) ** p


def ease_out(t, p=2.0):
    return 1 - (1 - clamp(t)) ** p


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def back_out(t, s=1.7):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def mix(c1, c2, t):
    return tuple(a + (b - a) * t for a, b in zip(c1, c2))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def hash01(*xs):
    """Deterministic pseudo random in [0,1)."""
    h = 0
    for x in xs:
        h = (h * 1000003) ^ int(x * 7919 + 17)
        h &= 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 0x5BD1E995) & 0xFFFFFFFF
    h ^= h >> 15
    return (h & 0xFFFFFF) / float(0x1000000)


def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def fill_poly(ctx, pts, rgb, a=1.0, edge=None, edge_a=0.0, lw=1.0):
    poly(ctx, pts)
    ctx.set_source_rgba(*rgb, a)
    if edge is None:
        ctx.fill()
        return
    ctx.fill_preserve()
    ctx.set_source_rgba(*edge, edge_a)
    ctx.set_line_width(lw)
    ctx.stroke()


def slab(ctx, pts, rgb, depth=(0, 10), side=None, a=1.0, shadow=(14, 18, 0.22)):
    """A paper slab: drop shadow, visible thickness band, then the face.

    `depth` is the screen offset of the slab's back face, so the band between
    back and front reads as the cut edge of a thick sheet.
    """
    dx, dy = depth
    if shadow:
        sx, sy, sa = shadow
        fill_poly(ctx, [(x + sx, y + sy) for x, y in pts], (0.02, 0.03, 0.06), sa * a)
    if side is None:
        side = shade(rgb, 0.62)
    back = [(x + dx, y + dy) for x, y in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        quad = [pts[i], pts[j], back[j], back[i]]
        fill_poly(ctx, quad, side, a)
    fill_poly(ctx, back, side, a)
    fill_poly(ctx, pts, rgb, a, edge=shade(rgb, 1.25), edge_a=0.35 * a, lw=1.2)


_paper_cache = {}


def paper_texture(w=W, h=H, seed=3):
    """Fibre + grain multiply layer (cached)."""
    key = (w, h, seed)
    if key in _paper_cache:
        return _paper_cache[key]
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 1, (h // 2, w // 2)).astype(np.float32)
    from scipy.ndimage import gaussian_filter, zoom
    fine = gaussian_filter(g, 0.7)
    fibre = gaussian_filter(rng.normal(0, 1, (h // 2, w // 2)).astype(np.float32), (0.6, 5.0))
    blot = gaussian_filter(rng.normal(0, 1, (h // 8, w // 8)).astype(np.float32), 6)
    blot = zoom(blot, ((h // 2) / blot.shape[0], (w // 2) / blot.shape[1]), order=1)
    v = 0.035 * fine / fine.std() + 0.03 * fibre / fibre.std() + 0.03 * blot / (blot.std() + 1e-6)
    v = zoom(v, (h / v.shape[0], w / v.shape[1]), order=1)
    lum = np.clip(1.0 + v, 0.85, 1.08)
    # multiply layer -> values <= 1, so remap so mean ~0.97
    lum = np.clip(lum * 0.97, 0, 1)
    a = np.full((h, w), 255, np.uint8)
    l8 = (lum * 255).astype(np.uint8)
    arr = np.dstack([l8, l8, l8, a]).copy()
    surf = cairo.ImageSurface.create_for_data(arr, cairo.FORMAT_ARGB32, w, h)
    _paper_cache[key] = (surf, arr)
    return _paper_cache[key]


def apply_paper(ctx, strength=1.0, size=(W, H)):
    surf, _ = paper_texture(*size)
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_MULTIPLY)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(strength)
    ctx.restore()


def vignette(ctx, k=0.35):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 0.95)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0.02, k)
    ctx.set_source(g)
    ctx.paint()


def new_frame():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_GOOD)
    return surf, ctx
