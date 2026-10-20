"""python3 portrait_sheet.py OUT.png  -> 2008 / 2026 character design side by side."""
import sys

import cairo

from gfx import apply_paper, hexc, shade
from origami import fill, shadow, pyramid, regular
from portrait import portrait
from scene_char import label

SW, SH = 2200, 1300
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, SW, SH)
ctx = cairo.Context(surf)
ctx.set_source_rgb(*hexc("#1a2338"))
ctx.paint()
for i, (x0, col) in enumerate(((60, "#2a3a5c"), (1120, "#2d3f5e"))):
    card = [(x0, 140), (x0 + 1020, 120), (x0 + 1030, 1240), (x0 - 10, 1250)]
    shadow(ctx, card, off=(16, 20), a=0.4, spread=6)
    fill(ctx, card, hexc(col))
    fill(ctx, [(x0, 140), (x0 + 1020, 120), (x0 + 500, 700)], shade(hexc(col), 1.08))
label(ctx, 60, 80, "马斯克 · 折纸人物形象稿", 46)
portrait(ctx, 560, 560, 0.95, age=0.0)
portrait(ctx, 1620, 560, 0.95, age=1.0)
label(ctx, 100, 1215, "2008 · 37 岁：发量密、发际线低，脸上折痕少，神情自信", 28, bg="#16202e")
label(ctx, 1160, 1215, "2026 · 55 岁：鬓角发灰，眼袋/法令纹/额纹折痕加深，眼皮更沉", 28, bg="#16202e")
apply_paper(ctx, 1.3, size=(SW, SH))
surf.write_to_png(sys.argv[1])
