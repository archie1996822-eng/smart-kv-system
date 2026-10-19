"""Character turnaround (animated model sheet) and shared studio backdrop."""
import math

import cairo
import numpy as np

from character import character_items
from gfx import H, W, ease_io, fill_poly, hexc, seg, shade, slab, smooth
from mesh import Camera, draw

TURN_DUR = 9.0
FONT = "Noto Sans CJK SC"


def studio(ctx, base="#25364d", accent="#3b5576"):
    ctx.set_source_rgb(*hexc(base))
    ctx.paint()
    b = hexc(base)
    a = hexc(accent)
    # stacked folded-paper panels behind the subject
    slab(ctx, [(-40, 120), (760, 60), (900, 1120), (-40, 1120)], shade(b, 1.18), depth=(0, 14), shadow=(18, 22, 0.3))
    slab(ctx, [(1180, 40), (1960, 110), (1960, 1120), (1040, 1120)], shade(b, 1.1), depth=(0, 14), shadow=(-18, 22, 0.3))
    slab(ctx, [(560, 300), (1380, 260), (1460, 1120), (480, 1120)], shade(a, 1.0), depth=(0, 16), shadow=(0, 26, 0.3))
    slab(ctx, [(-40, 860), (1960, 820), (1960, 1120), (-40, 1120)], shade(b, 0.82), depth=(0, -16), shadow=(0, -14, 0.25))


def label(ctx, x, y, text, size=34, rgb=(0.95, 0.96, 0.98), bg=None):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(size)
    ext = ctx.text_extents(text)
    if bg:
        pad = size * 0.4
        slab(ctx, [(x - pad, y - size - pad * 0.5), (x + ext.x_advance + pad, y - size - pad * 0.5),
                   (x + ext.x_advance + pad, y + pad * 0.9), (x - pad, y + pad * 0.9)], hexc(bg), depth=(0, 6),
             shadow=(6, 8, 0.3))
    ctx.set_source_rgb(*rgb)
    ctx.move_to(x, y)
    ctx.show_text(text)
    return ext.x_advance


def blink_at(t, times, d=0.16):
    for b in times:
        u = seg(t, b, b + d)
        if 0 < u < 1:
            return math.sin(math.pi * u)
    return 0.0


def render_turn(ctx, t):
    studio(ctx)
    cam = Camera((0, -0.8, 19), (0, -1.0, 0), fov_deg=24)
    # yaw sweep: three-quarter -> front -> profile -> back to three-quarter
    keys = [(0, -0.5), (1.6, 0.0), (3.2, 0.0), (4.6, 1.25), (6.0, 1.25), (7.6, -0.45), (9.0, -0.5)]
    yaw = keys[-1][1]
    for (t0, y0), (t1, y1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            yaw = y0 + (y1 - y0) * ease_io((t - t0) / (t1 - t0))
            break
    looks = 0.12 * math.sin(t * 0.9)
    young = character_items(0.0, "suit08",
                            pose=dict(head=(looks, -0.04, 0.02), armL=(0.06, 0.1, 0, -0.3, 0), armR=(0.06, 0.1, 0, -0.3, 0)),
                            expr=dict(smile=0.25, blink=blink_at(t, [1.0, 3.9, 7.1]), brow=0.1, gaze=(-looks * 2, 0)),
                            root=(-4.2, 0.6, 0), root_yaw=yaw)
    old = character_items(1.0, "tee26",
                          pose=dict(head=(looks * 0.6, 0.06, -0.02), body=(0, 0.04, 0), armL=(0.05, 0.08, 0, -0.25, 0),
                                    armR=(0.05, 0.08, 0, -0.25, 0)),
                          expr=dict(smile=0.0, frown=0.25, squint=0.15, blink=blink_at(t, [0.6, 2.7, 5.4, 8.2], 0.22),
                                    gaze=(-looks, -0.25)),
                          root=(4.2, 0.6, 0), root_yaw=yaw)
    draw(ctx, cam, young)
    draw(ctx, cam, old)
    label(ctx, 520, 1020, "2008", 40, bg="#1b2638")
    label(ctx, 1300, 1020, "2026", 40, bg="#1b2638")
