"""python3 paper_still.py style|board OUT"""
import sys
import cairo
from gfx import new_frame, apply_paper, W, H, hexc
import paper_open as po
from origami import fill
from scene_char import label

mode, out = sys.argv[1], sys.argv[2]
if mode == "style":
    s, c = new_frame()
    po.render_frame(c, 2.1, zoom=1.45, focus=(1060, 470))
    apply_paper(c, 1.3)
    s.write_to_png(out)
else:
    keys = [(0.0, "第 1 帧：车已在 U 形跑道底部高速冲刺"), (0.85, "沿弧面爬上近乎垂直的右壁"),
            (1.35, "冲出顶部，车头朝天"), (1.7, "顶点停一瞬，四个喷口打开"),
            (2.2, "四道冷气托住，悬停"), (2.9, "翻转：车头/车尾喷口交替点喷校准姿态"),
            (3.2, "翻转后段，姿态回正"), (3.9, "冷气减速，缓缓下落"), (4.3, "落回地面 → 接字卡钩子")]
    cw, ch = 640, 360
    board = cairo.ImageSurface(cairo.FORMAT_ARGB32, 3 * cw + 4 * 24, 3 * (ch + 70) + 24 + 70)
    bc = cairo.Context(board)
    bc.set_source_rgb(*hexc("#141c2c")); bc.paint()
    label(bc, 24, 52, "开场动作分解（半圆 U 形跑道）", 34)
    for i, (t, cap) in enumerate(keys):
        s, c = new_frame()
        po.render_frame(c, t, zoom=1.1, focus=(1000, 560))
        apply_paper(c, 1.3)
        x = 24 + (i % 3) * (cw + 24)
        y = 94 + (i // 3) * (ch + 70)
        bc.save(); bc.translate(x, y); bc.scale(cw / W, ch / H); bc.set_source_surface(s, 0, 0); bc.paint(); bc.restore()
        label(bc, x, y + ch + 44, f"{i + 1}. {t:.2f}s  {cap}", 22, (0.85, 0.88, 0.93))
    board.write_to_png(out)
