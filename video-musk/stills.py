import sys
from gfx import new_frame, apply_paper
from scene_open import render_open
ts = [float(x) for x in sys.argv[2:]]
for t in ts:
    surf, ctx = new_frame()
    render_open(ctx, t)
    apply_paper(ctx)
    surf.write_to_png(f"{sys.argv[1]}_{t:.2f}.png")
