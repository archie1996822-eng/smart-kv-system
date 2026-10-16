"""Low-level drawing helpers (Cairo) shared by every scene."""
import math
import random

import cairo
import numpy as np

W, H = 1920, 1080
TAU = math.tau

SERIF = "Noto Serif CJK SC"
SANS = "Noto Sans CJK SC"

PAL = {
    "night": "#0B1226",
    "navy": "#14203F",
    "deep": "#070B18",
    "amber": "#F6B64A",
    "gold": "#FFD27A",
    "warm": "#FF8D4D",
    "teal": "#43C6C3",
    "red": "#E2504C",
    "cream": "#F7EEDC",
    "ink": "#1A1D29",
    "white": "#FFFFFF",
    "grey": "#8A93A8",
}


# ----------------------------------------------------------------- math
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, t):
    return a + (b - a) * t


def prog(t, a, b):
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t, p=3):
    t = clamp(t)
    return 1 - (1 - t) ** p


def ease_in(t, p=3):
    t = clamp(t)
    return t ** p


def ease_io(t):
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_back(t, s=1.9):
    t = clamp(t)
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def spring(t, freq=2.6, damp=5.0):
    if t <= 0:
        return 0.0
    return 1 - math.exp(-damp * t) * math.cos(freq * TAU * t)


def pulse(t, a, b):
    """0 -> 1 -> 0 bump inside [a, b]."""
    p = prog(t, a, b)
    return math.sin(p * math.pi)


def noise1(x, seed=0):
    """Cheap smooth 1D value noise in [-1, 1]."""
    i = math.floor(x)
    f = x - i

    def h(n):
        r = random.Random((n * 7919 + seed * 104729) & 0xFFFFFFFF)
        return r.uniform(-1, 1)

    return lerp(h(i), h(i + 1), smooth(f))


# ----------------------------------------------------------------- colour
def hexc(h, a=1.0):
    if isinstance(h, tuple):
        return h if len(h) == 4 else (*h, a)
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, a)


def mix(c1, c2, t):
    a, b = hexc(c1), hexc(c2)
    return tuple(lerp(a[i], b[i], clamp(t)) for i in range(4))


def shade(c, k):
    """k<0 darken, k>0 lighten."""
    c = hexc(c)
    tgt = (0, 0, 0, c[3]) if k < 0 else (1, 1, 1, c[3])
    return mix(c, tgt, abs(k))


def setc(ctx, c, alpha=None):
    c = hexc(c)
    ctx.set_source_rgba(c[0], c[1], c[2], c[3] if alpha is None else c[3] * alpha)


# ----------------------------------------------------------------- shapes
def rrect(ctx, x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def circle(ctx, x, y, r):
    ctx.new_sub_path()
    ctx.arc(x, y, max(r, 0.01), 0, TAU)


def ellipse(ctx, x, y, rx, ry):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(max(rx, 0.01), max(ry, 0.01))
    ctx.new_sub_path()
    ctx.arc(0, 0, 1, 0, TAU)
    ctx.restore()


def fill_rect(ctx, c, x=0, y=0, w=W, h=H, alpha=None):
    setc(ctx, c, alpha)
    ctx.rectangle(x, y, w, h)
    ctx.fill()


def lin_grad(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for off, c in stops:
        g.add_color_stop_rgba(off, *hexc(c))
    return g


def vgrad(ctx, stops, x=0, y=0, w=W, h=H):
    ctx.set_source(lin_grad(0, y, 0, y + h, stops))
    ctx.rectangle(x, y, w, h)
    ctx.fill()


def glow(ctx, x, y, r, c, alpha=1.0, core=0.0):
    col = hexc(c)
    g = cairo.RadialGradient(x, y, r * core, x, y, max(r, 1))
    g.add_color_stop_rgba(0, col[0], col[1], col[2], col[3] * alpha)
    g.add_color_stop_rgba(0.35, col[0], col[1], col[2], col[3] * alpha * 0.45)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
    ctx.set_source(g)
    circle(ctx, x, y, r)
    ctx.fill()


def line(ctx, x0, y0, x1, y1, c, w=4, alpha=None, cap=cairo.LINE_CAP_ROUND):
    setc(ctx, c, alpha)
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()


def poly(ctx, pts):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.close_path()


def star_shape(ctx, x, y, r, n=5, inner=0.45, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        rr = r if i % 2 == 0 else r * inner
        a = rot + i * math.pi / n
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
    poly(ctx, pts)


# ----------------------------------------------------------------- scenery
def stars(ctx, seed, n, t, alpha=1.0, y_max=H * 0.7, color="#FFFFFF"):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, y_max)
        r = rnd.uniform(0.8, 2.4)
        ph = rnd.uniform(0, TAU)
        tw = 0.55 + 0.45 * math.sin(t * rnd.uniform(1.0, 3.0) + ph)
        setc(ctx, color, alpha * tw * rnd.uniform(0.4, 1.0))
        circle(ctx, x, y, r)
        ctx.fill()


def skyline(ctx, *a, **k):
    """Silhouette city as a cut-paper layer."""
    return paper(ctx, lambda: _skyline(ctx, *a, **k), 0.8, 0.28)


def _skyline(ctx, seed, base_y, color, win_color=None, lit=0.5, t=0.0,
             hmin=120, hmax=420, wmin=70, wmax=170, x0=-40, x1=W + 40,
             win_alpha=1.0, lit_fn=None):
    rnd = random.Random(seed)
    x = x0
    bi = 0
    while x < x1:
        w = rnd.uniform(wmin, wmax)
        h = rnd.uniform(hmin, hmax)
        setc(ctx, shade(color, 0.07))
        ctx.rectangle(x, base_y - h, w * 0.62 + 1, h + 400)
        ctx.fill()
        setc(ctx, shade(color, -0.1))
        ctx.rectangle(x + w * 0.62, base_y - h, w * 0.38 + 1, h + 400)
        ctx.fill()
        if rnd.random() < 0.3:
            ctx.rectangle(x + w * 0.4, base_y - h - rnd.uniform(20, 60), 4, 60)
            ctx.fill()
        if win_color:
            cols = max(1, int((w - 16) // 22))
            rows = int((h - 24) // 30)
            for i in range(rows):
                for j in range(cols):
                    r0 = rnd.random()
                    a = lit_fn(i, j, bi) if lit_fn else (1.0 if r0 < lit else 0.0)
                    if a > 0.01:
                        flick = 0.85 + 0.15 * math.sin(t * 2 + r0 * 40)
                        setc(ctx, win_color, a * win_alpha * flick)
                        ctx.rectangle(x + 10 + j * 22, base_y - h + 16 + i * 30, 11, 15)
                        ctx.fill()
        x += w + rnd.uniform(-10, 14)
        bi += 1


def particles(ctx, seed, n, t, color="#FFFFFF", alpha=0.5, area=(0, 0, W, H),
              vy=-20, vx=6, rmin=1.5, rmax=4, glow_r=0):
    rnd = random.Random(seed)
    ax, ay, aw, ah = area
    for _ in range(n):
        x0, y0 = rnd.uniform(0, aw), rnd.uniform(0, ah)
        sp = rnd.uniform(0.5, 1.5)
        r = rnd.uniform(rmin, rmax)
        ph = rnd.uniform(0, TAU)
        x = ax + (x0 + vx * sp * t + math.sin(t * 0.7 + ph) * 12) % aw
        y = ay + (y0 + vy * sp * t) % ah
        a = alpha * (0.5 + 0.5 * math.sin(t * 1.3 + ph))
        if glow_r:
            glow(ctx, x, y, r * glow_r, color, a * 0.5)
        setc(ctx, color, a)
        circle(ctx, x, y, r)
        ctx.fill()


def ground(ctx, y, c1, c2):
    vgrad(ctx, [(0, c1), (1, c2)], 0, y, W, H - y)


def hills(ctx, base_y, amp, freq, phase, color, seed=0):
    """Folded-paper ridge: straight facets, alternating light/dark panels."""
    def draw():
        step = 120
        xs = list(range(-step, W + step * 2, step))
        ys = [base_y - amp * (0.6 * math.sin(x * freq + phase) + 0.4 * math.sin(x * freq * 2.3 + phase * 1.7 + seed))
              for x in xs]
        for i in range(len(xs) - 1):
            up = ys[i + 1] < ys[i]
            setc(ctx, shade(color, 0.07 if up else -0.08))
            poly(ctx, [(xs[i], ys[i]), (xs[i + 1], ys[i + 1]), (xs[i + 1], H + 10), (xs[i], H + 10)])
            ctx.fill()
    paper(ctx, draw, 0.9, 0.3)


def light_rays(ctx, x, y, n, length, c, alpha, t=0.0, spread=TAU, rot=0.0, width=0.06):
    col = hexc(c)
    for i in range(n):
        a = rot + i * spread / n + 0.08 * math.sin(t * 0.6 + i)
        g = cairo.RadialGradient(x, y, 0, x, y, length)
        g.add_color_stop_rgba(0, col[0], col[1], col[2], alpha)
        g.add_color_stop_rgba(1, col[0], col[1], col[2], 0)
        ctx.set_source(g)
        ctx.move_to(x, y)
        ctx.arc(x, y, length, a - width, a + width)
        ctx.close_path()
        ctx.fill()


def spotlight(ctx, x_top, y_top, x_bot, y_bot, w_top, w_bot, c, alpha):
    col = hexc(c)
    g = cairo.LinearGradient(0, y_top, 0, y_bot)
    g.add_color_stop_rgba(0, col[0], col[1], col[2], alpha)
    g.add_color_stop_rgba(1, col[0], col[1], col[2], alpha * 0.15)
    ctx.set_source(g)
    poly(ctx, [(x_top - w_top, y_top), (x_top + w_top, y_top), (x_bot + w_bot, y_bot), (x_bot - w_bot, y_bot)])
    ctx.fill()
    ctx.save()
    ctx.translate(x_bot, y_bot)
    ctx.scale(1, 0.18)
    glow(ctx, 0, 0, w_bot * 1.3, c, alpha * 1.2)
    ctx.restore()


def confetti(ctx, seed, n, t, t0, colors, area=(0, -100, W, H + 200), fall=260):
    rnd = random.Random(seed)
    tt = t - t0
    if tt < 0:
        return
    for _ in range(n):
        x = rnd.uniform(area[0], area[2])
        y0 = rnd.uniform(-600, 0)
        sp = rnd.uniform(0.6, 1.4)
        y = y0 + tt * fall * sp
        if y > H + 40:
            continue
        x += math.sin(tt * 2 * sp + x) * 30
        ang = tt * 4 * sp + x
        c = colors[rnd.randrange(len(colors))]
        ctx.save()
        ctx.translate(x, y)
        ctx.rotate(ang)
        ctx.scale(1, abs(math.sin(ang * 1.3)) + 0.2)
        setc(ctx, c)
        ctx.rectangle(-7, -4, 14, 8)
        ctx.fill()
        ctx.restore()


# ----------------------------------------------------------------- text
def font(ctx, size, family=SERIF, bold=True):
    ctx.select_font_face(family, cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    fo = cairo.FontOptions()
    fo.set_antialias(cairo.ANTIALIAS_GRAY)
    fo.set_hint_style(cairo.HINT_STYLE_NONE)
    fo.set_hint_metrics(cairo.HINT_METRICS_OFF)
    ctx.set_font_options(fo)


def advances(ctx, s):
    return [ctx.text_extents(ch).x_advance for ch in s]


def text_width(ctx, s):
    return sum(advances(ctx, s))


def text_center(ctx, s, x, y, c="#FFFFFF", alpha=1.0, stroke=None, stroke_w=0):
    w = text_width(ctx, s)
    ctx.move_to(x - w / 2, y)
    ctx.text_path(s)
    if stroke:
        setc(ctx, stroke, alpha)
        ctx.set_line_width(stroke_w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke_preserve()
    setc(ctx, c, alpha)
    ctx.fill()


# ----------------------------------------------------------------- origami / paper craft
def drop_shadow(ctx, pattern, depth=1.0, alpha=0.32):
    """Soft-ish paper shadow from a group's alpha (a few offset mask taps)."""
    taps = ((1.0, 0.5), (0.7, 0.3), (1.35, 0.2))
    for k, a in taps:
        ctx.save()
        ctx.translate(7 * depth * k, 10 * depth * k)
        ctx.set_source_rgba(0.05, 0.03, 0.08, alpha * a)
        ctx.mask(pattern)
        ctx.restore()


def paper(ctx, fn, depth=1.0, alpha=0.32):
    """Draw fn() as a cut-paper layer with a drop shadow underneath."""
    ctx.push_group()
    res = fn()
    pat = ctx.pop_group()
    drop_shadow(ctx, pat, depth, alpha)
    ctx.set_source(pat)
    ctx.paint()
    return res


def fold_poly(ctx, pts, c, split, k_dark=-0.16, k_light=0.06, alpha=None):
    """Polygon folded along the line pts[split[0]] -> pts[split[1]]: two tones."""
    i, j = split
    a = pts[i:j + 1]
    b = pts[j:] + pts[:i + 1]
    setc(ctx, shade(c, k_light), alpha)
    poly(ctx, a)
    ctx.fill()
    setc(ctx, shade(c, k_dark), alpha)
    poly(ctx, b)
    ctx.fill()
    setc(ctx, "#FFFFFF", 0.18 if alpha is None else 0.18 * alpha)
    ctx.set_line_width(1.5)
    ctx.move_to(*pts[i])
    ctx.line_to(*pts[j])
    ctx.stroke()


def facet_mountain(ctx, base_l, peak, base_r, c, alpha=None):
    """Origami mountain: lit left facet, shaded right facet."""
    mid = (peak[0] + (base_r[0] - peak[0]) * 0.18, base_l[1])
    setc(ctx, shade(c, 0.08), alpha)
    poly(ctx, [base_l, peak, mid])
    ctx.fill()
    setc(ctx, shade(c, -0.18), alpha)
    poly(ctx, [peak, base_r, mid])
    ctx.fill()


def papered(depth=1.0, alpha=0.32):
    """Decorator: render a prop function as a paper cut-out with drop shadow."""
    def deco(fn):
        def wrapped(ctx, *a, **k):
            return paper(ctx, lambda: fn(ctx, *a, **k), depth, alpha)
        wrapped.__name__ = fn.__name__
        return wrapped
    return deco


_FACETS = {}


def facet_surface(seed=1):
    """Low-poly 'folded paper' light pattern, used with SOFT_LIGHT over the frame."""
    if seed in _FACETS:
        return _FACETS[seed]
    sw, sh = W // 2, H // 2
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
    c = cairo.Context(surf)
    rnd = random.Random(seed)
    cols, rows = 9, 6
    pts = [[(q * sw / cols + (rnd.uniform(-0.3, 0.3) * sw / cols if 0 < q < cols else 0),
             r * sh / rows + (rnd.uniform(-0.3, 0.3) * sh / rows if 0 < r < rows else 0))
            for q in range(cols + 1)] for r in range(rows + 1)]
    for r in range(rows):
        for q in range(cols):
            a, b, cc, d = pts[r][q], pts[r][q + 1], pts[r + 1][q + 1], pts[r + 1][q]
            tris = [(a, b, cc), (a, cc, d)] if rnd.random() < 0.5 else [(a, b, d), (b, cc, d)]
            for tri in tris:
                v = rnd.uniform(0.38, 0.62)
                c.set_source_rgba(v, v, v, 1)
                poly(c, tri)
                c.fill()
    _FACETS[seed] = surf
    return surf


_PAPER_TEX = None


def paper_texture():
    global _PAPER_TEX
    if _PAPER_TEX is None:
        rng = np.random.default_rng(3)
        sw, sh = W // 2, H // 2
        base = rng.normal(0.5, 0.05, size=(sh, sw))
        # fibres: short random strokes
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, sw, sh)
        c = cairo.Context(surf)
        v = np.clip(base * 255, 0, 255).astype(np.uint8)
        arr = np.dstack([v, v, v, np.full_like(v, 255)]).copy()
        tmp = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, sw, sh)
        c.set_source_surface(tmp)
        c.paint()
        rnd = random.Random(5)
        c.set_line_width(0.8)
        for _ in range(2600):
            x, y = rnd.uniform(0, sw), rnd.uniform(0, sh)
            a = rnd.uniform(0, TAU)
            l = rnd.uniform(4, 14)
            g = rnd.choice((0.35, 0.65))
            c.set_source_rgba(g, g, g, 0.5)
            c.move_to(x, y)
            c.curve_to(x + math.cos(a) * l * 0.4, y + math.sin(a + 0.4) * l * 0.4,
                       x + math.cos(a) * l * 0.7, y + math.sin(a - 0.3) * l * 0.7,
                       x + math.cos(a) * l, y + math.sin(a) * l)
            c.stroke()
        _PAPER_TEX = (surf, arr)
    return _PAPER_TEX[0]


def apply_paper(ctx, facet_seed=1, facet_strength=0.55, tex_strength=0.6):
    ctx.save()
    ctx.scale(2, 2)
    ctx.set_operator(cairo.OPERATOR_SOFT_LIGHT)
    ctx.set_source_surface(facet_surface(facet_seed), 0, 0)
    ctx.paint_with_alpha(facet_strength)
    ctx.set_source_surface(paper_texture(), 0, 0)
    ctx.paint_with_alpha(tex_strength)
    ctx.restore()


# ----------------------------------------------------------------- overlays
_GRAIN = None
_VIGNETTE = None


def grain_surfaces():
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(7)
        _GRAIN = []
        for _ in range(4):
            v = rng.integers(0, 255, size=(H // 2, W // 2), dtype=np.uint8)
            a = np.full_like(v, 16)
            # premultiplied BGRA
            pv = (v.astype(np.uint16) * a // 255).astype(np.uint8)
            arr = np.dstack([pv, pv, pv, a]).copy()
            surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, W // 2, H // 2)
            _GRAIN.append((surf, arr))
    return _GRAIN


def vignette(ctx, strength=0.55):
    g = cairo.RadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, H * 1.05)
    g.add_color_stop_rgba(0, 0, 0, 0, 0)
    g.add_color_stop_rgba(1, 0, 0, 0, strength)
    ctx.set_source(g)
    ctx.paint()


def apply_grain(ctx, frame):
    surf, _ = grain_surfaces()[frame % 4]
    ctx.save()
    ctx.scale(2, 2)
    ctx.set_source_surface(surf, 0, 0)
    ctx.get_source().set_filter(cairo.FILTER_FAST)
    ctx.paint()
    ctx.restore()
