"""Model sheet (形象稿) and opening action breakdown (动作分解稿) as PNGs.

python3 sheets.py   -> output/形象稿-马斯克.png, output/动作分解稿-开场.png
"""
import math
import os

import cairo
import numpy as np

from character import character_items
from gfx import apply_paper, hexc, shade, slab, fill_poly, W, H
from head import head_mesh, SKIN, SKIN_26, HAIR_08, HAIR_26, GREY, IRIS, LIP
from mesh import Camera, draw, euler
from scene_char import FONT, label

SW, SH = 2560, 1620


def text(ctx, x, y, s, size=26, rgb=(0.9, 0.92, 0.95), bold=False):
    ctx.select_font_face(FONT, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(size)
    ctx.set_source_rgb(*rgb)
    ctx.move_to(x, y)
    ctx.show_text(s)


def panel(ctx, x, y, w, h, col="#2b3d55"):
    slab(ctx, [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], hexc(col), depth=(0, 10), shadow=(12, 16, 0.3))


def head_view(ctx, cx, cy, size, age, yaw, expr=None, pitch=-0.04):
    cam = Camera((0, 0, 10), (0, 0.05, 0), fov_deg=20, cx=cx, cy=cy, h=size * 1.0)
    m = head_mesh(age, expr or {})
    draw(ctx, cam, [(m, euler(yaw, pitch, 0), np.zeros(3))])


def bust_view(ctx, cx, cy, size, age, outfit, yaw, expr, pose=None):
    cam = Camera((0, -2.6, 26), (0, -2.6, 0), fov_deg=26, cx=cx, cy=cy, h=size)
    draw(ctx, cam, character_items(age, outfit, pose=pose or {}, expr=expr, root_yaw=yaw))


def model_sheet(path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*hexc("#1c283a"))
    ctx.paint()
    text(ctx, 70, 92, "马斯克 · 折纸低多边形 形象稿", 52, bold=True)
    text(ctx, 72, 138, "脸部保留真人五官与体积：长脸、眉骨偏高、深眼窝里的深色眼睛、直鼻梁、宽方下颌。", 26, (0.75, 0.8, 0.88))
    text(ctx, 72, 176, "身体是折纸分面，脖子从下颌内侧放样进衣领，头身一体。", 26, (0.75, 0.8, 0.88))
    rows = [
        (0.0, "2008 · 三十七岁", "头发更密、发际线更低、额头和眼周几乎没有纹路，神情自信",
         dict(smile=0.25, brow=0.1), "suit08"),
        (1.0, "2026 · 五十五岁", "鬓角发灰、额纹/眼袋/法令纹/木偶纹加深，上眼皮更沉，明显疲惫",
         dict(smile=0.0, frown=0.25, squint=0.15, gaze=(0, -0.2)), "tee26"),
    ]
    for r, (age, title, note, expr, outfit) in enumerate(rows):
        y0 = 215 + r * 690
        panel(ctx, 60, y0, 1660, 640)
        text(ctx, 100, y0 + 60, title, 40, bold=True)
        text(ctx, 100, y0 + 105, note, 26, (0.78, 0.83, 0.9))
        for k, (yaw, cap) in enumerate(((0.0, "正面"), (-0.55, "四分之三侧"), (-1.45, "侧面"))):
            cx = 330 + k * 520
            head_view(ctx, cx, y0 + 370, 520, age, yaw, expr)
            text(ctx, cx - 50, y0 + 610, cap, 26, (0.7, 0.76, 0.85))
        # bust
        panel(ctx, 1760, y0, 740, 640, "#30455f")
        bust_view(ctx, 2130, y0 + 330, 880, age, outfit, -0.35, expr,
                  pose=dict(head=(0.15, -0.03, 0)))
        text(ctx, 1790, y0 + 610, "2008：深灰西装 + 白衬衫敞领" if age == 0 else "2026：黑 T 恤 + 敞开的深灰外套",
             24, (0.75, 0.8, 0.88))
    # palette
    sw = [("肤色 08", SKIN), ("肤色 26", SKIN_26), ("发色 08", HAIR_08), ("发色 26", HAIR_26), ("鬓灰", GREY),
          ("虹膜", IRIS), ("唇", LIP)]
    for i, (n, c) in enumerate(sw):
        x = 1640 + i * 125
        slab(ctx, [(x, 50), (x + 100, 50), (x + 100, 110), (x, 110)], c, depth=(0, 6), shadow=(5, 7, 0.3))
        text(ctx, x + 4, 145, n, 20, (0.75, 0.8, 0.88))
    apply_paper(ctx, 0.9, size=(SW, SH))
    surf.write_to_png(path)


def expression_sheet(path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, 900)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*hexc("#1c283a"))
    ctx.paint()
    text(ctx, 70, 80, "表情与口型（脸部是同一套网格，靠眼睑/眉/嘴的折片变化）", 40, bold=True)
    exprs = [
        (0.0, "08 自信微笑", dict(smile=0.35, brow=0.1)),
        (0.0, "08 专注", dict(frown=0.3, squint=0.2, gaze=(0.3, 0))),
        (0.0, "08 说话", dict(open=0.55, brow=0.2)),
        (1.0, "26 疲惫", dict(frown=0.2, squint=0.25, gaze=(0, -0.35), blink=0.35)),
        (1.0, "26 沉默", dict(frown=0.4, gaze=(-0.3, -0.1))),
        (1.0, "26 苦笑", dict(smile=0.3, squint=0.2)),
    ]
    for i, (age, cap, e) in enumerate(exprs):
        cx = 230 + i * 420
        panel(ctx, cx - 190, 120, 380, 720)
        head_view(ctx, cx, 470, 560, age, -0.3, e)
        text(ctx, cx - 90, 810, cap, 28, (0.8, 0.85, 0.92))
    apply_paper(ctx, 0.9, size=(SW, 900))
    surf.write_to_png(path)


BREAKDOWN = [
    (0.00, "第 1 帧", "车已在坡上高速爬升，带速度线，没有静止画面"),
    (0.55, "爬升", "沿四分之一圆弧坡继续加速，坡度越来越陡"),
    (0.97, "冲出坡顶", "坡顶接近垂直（80°），车头朝天"),
    (1.58, "顶点·停一瞬", "速度降到零；四个喷口同时打开（1.50 s）"),
    (2.10, "冷气托举悬停", "车底四道淡蓝白冷气把车托住，轻微上下浮动"),
    (2.78, "翻转 ①", "后空翻起步，冷气减弱，雾气散开"),
    (2.92, "翻转 ②", "翻过倒置位置，喷口朝天，只剩白雾"),
    (3.62, "下落", "喷口关闭，加速下落，镜头跟着下摇"),
    (3.92, "落地", "悬挂压缩回弹、灰白扬尘、镜头震动，随即接字卡钩子"),
]


def breakdown_sheet(path):
    import scene_open as so
    from gfx import new_frame
    cols, cw, ch = 3, 800, 450
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 70 * 2 + cols * cw + (cols - 1) * 30, 2080)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(*hexc("#1c283a"))
    ctx.paint()
    text(ctx, 70, 90, "开场动作分解稿 · 飞行汽车演示（0 – 4.4 秒，之后立即接字卡）", 48, bold=True)
    text(ctx, 72, 140, "推进器只喷冷气：白 / 淡蓝，没有任何橙黄色火焰或尾焰。画面全部由代码逐帧绘制。", 26, (0.75, 0.8, 0.88))
    for i, (t, title, note) in enumerate(BREAKDOWN):
        fs, fc = new_frame()
        so.render_open(fc, t)
        apply_paper(fc)
        x = 70 + (i % cols) * (cw + 30)
        y = 190 + (i // cols) * (ch + 150)
        slab(ctx, [(x, y), (x + cw, y), (x + cw, y + ch), (x, y + ch)], hexc("#0f1520"), depth=(0, 8), shadow=(10, 14, 0.35))
        ctx.save()
        ctx.rectangle(x, y, cw, ch)
        ctx.clip()
        ctx.translate(x, y)
        ctx.scale(cw / W, ch / H)
        ctx.set_source_surface(fs, 0, 0)
        ctx.paint()
        ctx.restore()
        label(ctx, x + 16, y + 44, f"{t:0.2f}s", 28, bg="#16202e")
        text(ctx, x, y + ch + 50, f"{i + 1}. {title}", 32, bold=True)
        text(ctx, x, y + ch + 92, note, 24, (0.78, 0.83, 0.9))
    # phase bar
    y = 1975
    total = so.T_END
    phases = [(0, so.T_LAUNCH, "爬坡", "#4d6a8c"), (so.T_LAUNCH, so.T_APEX, "冲顶", "#5b7ea6"),
              (so.T_APEX, so.T_FLIP0, "悬停", "#8fbbe0"), (so.T_FLIP0, so.T_FLIP1, "翻转", "#6f97c2"),
              (so.T_FLIP1, so.T_DROP1, "下落", "#4d6a8c"), (so.T_DROP1, so.T_END, "落地→字卡", "#c9d6e3")]
    x0, x1 = 70, surf.get_width() - 70
    for a, b, name, col in phases:
        xa = x0 + (x1 - x0) * a / total
        xb = x0 + (x1 - x0) * b / total
        slab(ctx, [(xa, y), (xb - 4, y), (xb - 4, y + 56), (xa, y + 56)], hexc(col), depth=(0, 6), shadow=(4, 6, 0.3))
        text(ctx, xa + 12, y + 38, f"{name} {a:.2f}–{b:.2f}s", 24, (0.06, 0.08, 0.12), bold=True)
    apply_paper(ctx, 0.9, size=(surf.get_width(), surf.get_height()))
    surf.write_to_png(path)


if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    model_sheet("output/形象稿-马斯克.png")
    expression_sheet("output/形象稿-表情.png")
    breakdown_sheet("output/动作分解稿-开场.png")
    print("ok")
