"""Frame renderer + encoder.

python3 render.py open            # opening stunt preview -> output/开场特技样片.mp4
python3 render.py turn            # animated character turnaround -> output/形象转面.mp4
python3 render.py open --jobs 4
"""
import argparse
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np

from gfx import FPS, H, W, apply_paper, new_frame, seg

SEQ = {}


def sequence(name, dur, out, audio_kw=None):
    def deco(fn):
        SEQ[name] = dict(fn=fn, dur=dur, out=out, audio_kw=audio_kw)
        return fn
    return deco


def _fade(ctx, k):
    if k > 0:
        ctx.set_source_rgba(0.03, 0.04, 0.07, min(1, k))
        ctx.paint()


import scene_open as so  # noqa: E402

OPEN_DUR = so.T_END + 0.8


@sequence("open", OPEN_DUR, "output/开场特技样片.mp4",
          audio_kw=dict(t_launch=so.T_LAUNCH, t_jet=so.T_JET, t_apex=so.T_APEX, t_flip0=so.T_FLIP0,
                        t_flip1=so.T_FLIP1, t_land=so.T_DROP1, tail=OPEN_DUR - so.T_DROP1))
def frame_open(t):
    surf, ctx = new_frame()
    so.render_open(ctx, min(t, so.T_END + 0.8))
    apply_paper(ctx)
    _fade(ctx, seg(t, OPEN_DUR - 0.35, OPEN_DUR))
    return surf


import scene_char as sc  # noqa: E402


@sequence("turn", sc.TURN_DUR, "output/形象转面.mp4", audio_kw={})
def frame_turn(t):
    surf, ctx = new_frame()
    sc.render_turn(ctx, t)
    apply_paper(ctx)
    return surf


def _render_index(args):
    name, i = args
    t = i / FPS
    surf = SEQ[name]["fn"](t)
    surf.flush()
    return bytes(surf.get_data())


def encode(name, jobs):
    spec = SEQ[name]
    n = int(round(spec["dur"] * FPS))
    os.makedirs("build", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    silent = f"build/{name}_video.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", silent]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(jobs) as pool:
        for k, buf in enumerate(pool.imap(_render_index, [(name, i) for i in range(n)], chunksize=2)):
            p.stdin.write(buf)
            if k % 30 == 0:
                print(f"\r{name}: frame {k}/{n}", end="", flush=True)
    p.stdin.close()
    p.wait()
    print()
    import audio
    wav = audio.build(name, spec["dur"], **spec["audio_kw"])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", wav,
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", spec["out"]], check=True)
    print(spec["out"])


def still(name, t, path):
    surf = SEQ[name]["fn"](t)
    surf.write_to_png(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--still", type=float)
    a = ap.parse_args()
    if a.still is not None:
        still(a.name, a.still, f"build/still_{a.name}_{a.still:.2f}.png")
    else:
        encode(a.name, a.jobs)
