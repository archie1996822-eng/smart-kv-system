"""Render the film.

  python3 render.py                 # full render -> output/雷军-科普号单集-动画演绎.mp4
  python3 render.py --still 33.5    # single frame -> build/still_33.50.png
  python3 render.py --sheet         # contact sheet of every shot -> build/sheet_*.png
  python3 render.py --cover         # thumbnail -> output/封面-错过时代的人.png
  python3 render.py --jobs 4        # parallel workers (default: CPU count)
"""
import argparse
import math
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import cairo

import gfx
from gfx import W, H, SERIF, SANS, clamp, prog, ease_out, ease_io, hexc, setc, rrect, fill_rect, font, advances
from timeline import ITEMS, FPS, TOTAL, item_at
import scenes_a  # noqa: F401  (registers scenes)
import scenes_b  # noqa: F401
from scenes_a import REG

ROOT = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(ROOT, "build")
OUT = os.path.join(ROOT, "output")
OUT_NAME = "雷军-科普号单集-动画演绎.mp4"

BADGE = "AI生成·动画演绎"
HL_COLOR = "#FFC65C"
INK = "#2A2433"
INK_HL = "#C8402E"
TRANS_DUR = {"fade": 0.6, "flash": 0.55, "wipe": 0.6, "push": 0.6, "iris": 0.75, "dip": 0.8}
BIG_POS = {
    "hook": (1225, 470),
    "rewind": (960, 575),
    "ledger": (960, 865),
    "river": (960, 230),
    "forty": (960, 150),
    "sunrise": (960, 300),
}


class State:
    pass


def scene_state(it, t, frame):
    S = State()
    S.t = t - it["scene_start"]
    S.T = it["scene_end"] - it["scene_start"]
    S.k = it["scene_k"]
    S.items = it["scene_items"]
    S.tk = t - it["start"]
    S.dk = it["end"] - it["start"]
    S.frame = frame
    S.gt = t
    return S


def draw_scene(ctx, it, t, frame):
    ctx.save()
    REG[it["scene"]](ctx, scene_state(it, t, frame))
    ctx.restore()


def scene_group(ctx, it, t, frame):
    ctx.push_group()
    draw_scene(ctx, it, t, frame)
    return ctx.pop_group()


def draw_transition(ctx, prev, cur, t, frame):
    kind = cur["trans"]
    d = TRANS_DUR.get(kind, 0)
    p = (t - cur["start"]) / d if d else 1.0
    if prev is None or kind in ("none", "cut") or p >= 1:
        draw_scene(ctx, cur, t, frame)
        return
    p = clamp(p)
    if kind == "dip":
        if p < 0.5:
            draw_scene(ctx, prev, t, frame)
            fill_rect(ctx, "#000000", alpha=ease_io(p * 2))
        else:
            draw_scene(ctx, cur, t, frame)
            fill_rect(ctx, "#000000", alpha=1 - ease_io((p - 0.5) * 2))
    elif kind == "flash":
        if p < 0.35:
            draw_scene(ctx, prev, t, frame)
            fill_rect(ctx, "#FFF6E6", alpha=p / 0.35)
        else:
            draw_scene(ctx, cur, t, frame)
            fill_rect(ctx, "#FFF6E6", alpha=(1 - (p - 0.35) / 0.65) ** 2)
    elif kind == "fade":
        draw_scene(ctx, prev, t, frame)
        b = scene_group(ctx, cur, t, frame)
        ctx.set_source(b)
        ctx.paint_with_alpha(ease_io(p))
    elif kind == "push":
        e = ease_io(p)
        a = scene_group(ctx, prev, t, frame)
        b = scene_group(ctx, cur, t, frame)
        ctx.save()
        ctx.translate(-e * W, 0)
        ctx.set_source(a)
        ctx.paint()
        ctx.restore()
        ctx.save()
        ctx.translate((1 - e) * W, 0)
        ctx.set_source(b)
        ctx.paint()
        ctx.restore()
        fill_rect(ctx, "#FFFFFF", (1 - e) * W - 6, 0, 12, H, alpha=0.5 * math.sin(p * math.pi))
    elif kind == "wipe":
        e = ease_io(p)
        draw_scene(ctx, prev, t, frame)
        b = scene_group(ctx, cur, t, frame)
        x = e * (W + 400) - 200
        ctx.save()
        ctx.move_to(-10, -10)
        ctx.line_to(x + 200, -10)
        ctx.line_to(x - 200, H + 10)
        ctx.line_to(-10, H + 10)
        ctx.close_path()
        ctx.clip()
        ctx.set_source(b)
        ctx.paint()
        ctx.restore()
        setc(ctx, "#FFE3A3", 0.8 * math.sin(p * math.pi))
        ctx.set_line_width(10)
        ctx.move_to(x + 200, -10)
        ctx.line_to(x - 200, H + 10)
        ctx.stroke()
    elif kind == "iris":
        e = ease_io(p)
        draw_scene(ctx, prev, t, frame)
        b = scene_group(ctx, cur, t, frame)
        ctx.save()
        gfx.circle(ctx, W / 2, H / 2, e * 1150)
        ctx.clip()
        ctx.set_source(b)
        ctx.paint()
        ctx.restore()
        setc(ctx, "#FFE3A3", 0.7 * math.sin(p * math.pi))
        ctx.set_line_width(8)
        gfx.circle(ctx, W / 2, H / 2, e * 1150)
        ctx.stroke()
    else:
        draw_scene(ctx, cur, t, frame)


def hl_mask(text, hls):
    mask = [False] * len(text)
    for h in hls:
        i = text.find(h)
        while i >= 0:
            for j in range(i, i + len(h)):
                mask[j] = True
            i = text.find(h, i + 1)
    return mask


def draw_caption(ctx, it, t, is_last):
    if it["kind"] != "text":
        return
    lt = t - it["start"]
    dur = it["end"] - it["start"]
    out = 1.0 if is_last else 1 - prog(lt, dur - 0.35, dur)
    if out <= 0:
        return
    text = it["text"]
    big = it["style"] == "big"
    size = 92 if big else 60
    font(ctx, size, SERIF, True)
    adv = advances(ctx, text)
    tw = sum(adv)
    if big:
        cx, cy = BIG_POS.get(it["scene"], (960, 560))
        base = cy + size * 0.36
        stagger, t0 = 0.075, 0.25
    else:
        cx, base = 960, 990
        stagger, t0 = 0.032, 0.18
    mask = hl_mask(text, it["hl"])
    if not big:
        paper_ribbon(ctx, cx, base, tw, size, lt, out)
    x = cx - tw / 2
    for i, ch in enumerate(text):
        a = ease_out(prog(lt, t0 + i * stagger, t0 + i * stagger + 0.28)) * out
        if a > 0 and ch != " ":
            dy = (1 - a) * (22 if big else 10)
            sc = 1.0 + (1 - a) * (0.25 if big else 0.0)
            ctx.save()
            ctx.translate(x + adv[i] / 2, base + dy - size * 0.35)
            ctx.scale(sc, sc)
            ctx.translate(-adv[i] / 2, size * 0.35)
            if big:
                # layered cut-paper letters: shadow, coloured backing sheet, white face
                ctx.move_to(9, 13)
                ctx.text_path(ch)
                ctx.set_source_rgba(0.05, 0.03, 0.08, 0.35 * a)
                ctx.fill()
                ctx.move_to(5, 6)
                ctx.text_path(ch)
                setc(ctx, "#B8322E" if mask[i] else "#2C3A66", a)
                ctx.fill()
                ctx.move_to(0, 0)
                ctx.text_path(ch)
                setc(ctx, HL_COLOR if mask[i] else "#FFFDF6", a)
                ctx.fill()
            else:
                ctx.move_to(0, 0)
                ctx.text_path(ch)
                setc(ctx, INK_HL if mask[i] else INK, a)
                ctx.fill()
            ctx.restore()
        x += adv[i]


def paper_ribbon(ctx, cx, base, tw, size, lt, out):
    """Folded paper strip behind lower-third captions."""
    u = ease_out(prog(lt, 0.0, 0.32), 3)
    if u <= 0:
        return
    w = (tw + 90) * u
    h = size * 1.55
    y0 = base - size * 1.03
    x0 = cx - w / 2
    ctx.save()
    ctx.translate(cx, y0 + h / 2)
    ctx.rotate(-0.006)
    ctx.translate(-cx, -(y0 + h / 2))
    ctx.push_group()
    tail = 46
    for sx in (-1, 1):
        ex = x0 if sx < 0 else x0 + w
        setc(ctx, "#B9A98C", out)
        gfx.poly(ctx, [(ex - sx * 10, y0 + 14), (ex + sx * (tail + 20), y0 + 14), (ex + sx * tail, y0 + h / 2 + 10),
                       (ex + sx * (tail + 20), y0 + h + 6), (ex - sx * 10, y0 + h + 6)])
        ctx.fill()
        setc(ctx, "#8E7E62", out)
        gfx.poly(ctx, [(ex, y0 + h), (ex, y0 + h + 6), (ex - sx * 10, y0 + h + 6)])
        ctx.fill()
    setc(ctx, "#F7F0E1", out)
    ctx.rectangle(x0, y0, w, h)
    ctx.fill()
    setc(ctx, "#ECE2CE", out)
    ctx.rectangle(x0, y0 + h * 0.55, w, h * 0.45)
    ctx.fill()
    setc(ctx, "#FFFFFF", 0.5 * out)
    ctx.rectangle(x0, y0 + h * 0.55 - 1, w, 2)
    ctx.fill()
    pat = ctx.pop_group()
    gfx.drop_shadow(ctx, pat, 0.9, 0.4)
    ctx.set_source(pat)
    ctx.paint()
    ctx.restore()


def draw_badge(ctx):
    font(ctx, 28, SANS, True)
    tw = sum(advances(ctx, BADGE))
    pad = 22
    w, h = tw + pad * 2, 54
    x, y = W - 40 - w, 34
    rrect(ctx, x, y, w, h, h / 2)
    ctx.set_source_rgba(0, 0, 0, 0.5)
    ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, 0.65)
    ctx.set_line_width(2)
    ctx.stroke()
    ctx.move_to(x + pad, y + h / 2 + 10)
    ctx.set_source_rgba(1, 1, 1, 0.96)
    ctx.show_text(BADGE)


def render_frame(frame, scale=1.0):
    t = frame / FPS
    w, h = int(W * scale), int(H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
    ctx = cairo.Context(surf)
    ctx.scale(scale, scale)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    i, it = item_at(t)
    prev = ITEMS[i - 1] if i > 0 else None
    draw_transition(ctx, prev, it, t, frame)
    gfx.apply_paper(ctx, facet_seed=it["seg_index"] + 1)
    gfx.vignette(ctx, 0.4)
    if prev is not None and t - it["start"] < 0.4:
        draw_caption(ctx, prev, t, False)
    draw_caption(ctx, it, t, i == len(ITEMS) - 1)
    draw_badge(ctx)
    surf.flush()
    return surf


def render_chunk(args):
    idx, f0, f1, crf = args
    path = os.path.join(BUILD, f"part_{idx:02d}.mp4")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr0", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-g", "60", "-bf", "2", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        surf = render_frame(f)
        p.stdin.write(bytes(surf.get_data()))
        if (f - f0) % 300 == 0:
            print(f"  worker {idx}: frame {f - f0}/{f1 - f0}  ({time.time() - t0:.0f}s)", flush=True)
    p.stdin.close()
    p.wait()
    return path


def full_render(jobs, crf, skip_audio=False, video_only=False, mux_only=False):
    os.makedirs(BUILD, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    silent = os.path.join(BUILD, "video_silent.mp4")
    if not mux_only:
        render_silent(jobs, crf, silent)
    if video_only:
        return
    mux(silent, skip_audio)


def render_silent(jobs, crf, silent):
    n = int(round(TOTAL * FPS))
    chunk = math.ceil(n / jobs)
    tasks = [(i, i * chunk, min(n, (i + 1) * chunk), crf) for i in range(jobs) if i * chunk < n]
    t0 = time.time()
    print(f"rendering {n} frames with {len(tasks)} workers …", flush=True)
    with Pool(len(tasks)) as pool:
        parts = pool.map(render_chunk, tasks)
    print(f"frames done in {time.time() - t0:.0f}s", flush=True)
    lst = os.path.join(BUILD, "parts.txt")
    with open(lst, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", silent],
                   check=True)


def mux(silent, skip_audio):
    wav = os.path.join(BUILD, "audio.wav")
    if not skip_audio or not os.path.exists(wav):
        import audio
        audio.build(wav)
    out = os.path.join(OUT, OUT_NAME)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                    "-movflags", "+faststart",
                    "-metadata", "title=账上只剩十几万的那年，雷军做了一个决定",
                    "-metadata", "comment=AI生成·动画演绎；音乐与音效均为程序合成原创",
                    out], check=True)
    print("wrote", out)


def cover():
    """Thumbnail per the script: 封面「错过时代的人」."""
    os.makedirs(OUT, exist_ok=True)
    surf = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    ctx = cairo.Context(surf)
    draw_scene(ctx, ITEMS[0], 3.6, int(3.6 * FPS))
    gfx.apply_paper(ctx, facet_seed=1)
    gfx.vignette(ctx, 0.4)
    title = "错过时代的人"
    size = 150
    font(ctx, size, SERIF, True)
    adv = advances(ctx, title)
    x = 1260 - sum(adv) / 2
    for i, ch in enumerate(title):
        for (dx, dy), col in (((12, 16), (0.05, 0.03, 0.08, 0.4)), ((6, 8), hexc("#B8322E")), ((0, 0), hexc("#FFFDF6"))):
            ctx.move_to(x + dx, 560 + dy)
            ctx.text_path(ch)
            ctx.set_source_rgba(*col)
            ctx.fill()
        x += adv[i]
    draw_badge(ctx)
    path = os.path.join(OUT, "封面-错过时代的人.png")
    surf.write_to_png(path)
    print(path)


def sheet():
    os.makedirs(BUILD, exist_ok=True)
    times = []
    for it in ITEMS:
        a, b = it["start"], it["end"]
        times += [a + 0.25 * (b - a), a + 0.8 * (b - a)]
    sc = 0.3333
    tw, th = int(W * sc), int(H * sc)
    per = 12
    for si in range(0, len(times), per):
        grid = cairo.ImageSurface(cairo.FORMAT_RGB24, tw * 3, th * 4)
        g = cairo.Context(grid)
        for j, t in enumerate(times[si:si + per]):
            s = render_frame(int(t * FPS), sc)
            g.set_source_surface(s, (j % 3) * tw, (j // 3) * th)
            g.paint()
            g.set_source_rgb(1, 1, 0)
            g.select_font_face(SANS)
            g.set_font_size(18)
            g.move_to((j % 3) * tw + 8, (j // 3) * th + 22)
            g.show_text(f"{t:.1f}s")
        path = os.path.join(BUILD, f"sheet_{si // per:02d}.png")
        grid.write_to_png(path)
        print(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float)
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--cover", action="store_true")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 4)
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--reuse-audio", action="store_true")
    ap.add_argument("--video-only", action="store_true")
    ap.add_argument("--mux-only", action="store_true")
    a = ap.parse_args()
    if a.still is not None:
        os.makedirs(BUILD, exist_ok=True)
        t0 = time.time()
        s = render_frame(int(a.still * FPS))
        p = os.path.join(BUILD, f"still_{a.still:.2f}.png")
        s.write_to_png(p)
        print(p, f"{(time.time() - t0) * 1000:.0f} ms")
    elif a.sheet:
        sheet()
    elif a.cover:
        cover()
    else:
        full_render(a.jobs, a.crf, a.reuse_audio, a.video_only, a.mux_only)
