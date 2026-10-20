"""Render the full film: frames in parallel, piped to ffmpeg with the procedural audio.

audio_full.py already normalises to -16 LUFS; the 6 Mbit/s cap keeps the file under GitHub's 100 MB limit.

Usage: python3 render_full.py [out.mp4]
"""
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b_full as B  # noqa: E402

FPS = 30
W, H = 1920, 1080
N = int(round(B.DURATION * FPS))


def render(i):
    s = B.frame(i / FPS)
    s.flush()
    a = np.ndarray((H, s.get_stride() // 4, 4), np.uint8, s.get_data())[:, :W]
    return a[:, :, 2::-1].tobytes()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "release", "musk_full_B.mp4")
    wav = os.path.join(HERE, "..", "build", "audio_full.wav")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "6M", "-bufsize", "12M",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
           "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
           "-shortest", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with Pool(4, maxtasksperchild=400) as pool:
        for k, buf in enumerate(pool.imap(render, range(N), chunksize=4)):
            ff.stdin.write(buf)
            if k % 150 == 0:
                el = time.time() - t0
                print(f"{k}/{N}  {el:.0f}s  eta {el / (k + 1) * (N - k - 1):.0f}s", flush=True)
    ff.stdin.close()
    ff.wait()
    print("done", out, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
