"""Self-check for rendered previews.

python3 check.py output/开场特技样片.mp4
  * spec: 1920x1080, 30 fps, h264 + aac
  * flame check: per-frame share of saturated orange/yellow pixels (hue 18–55°)
    – the jets must stay white / pale blue, so this has to be ~0 on every frame of the jet shots
    – `--jets 0-14,79.3-88` limits the strict test to those time ranges (seconds); elsewhere the
      character's brown hair and skin shade sit on the edge of that hue band, so it is only reported
  * first-frame motion: frame 0 and frame 1 must differ (no static poster)
  * loudness (EBU R128 integrated) and true peak
"""
import json
import re
import subprocess
import sys

import numpy as np

W, H = 1920, 1080


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def frames(path, scale=4):
    w, h = W // scale, H // scale
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    while True:
        buf = p.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, w, 3).astype(np.float32) / 255


def orange_share(img):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    mx = img.max(-1)
    mn = img.min(-1)
    sat = (mx - mn) / (mx + 1e-6)
    hue = np.zeros_like(mx)
    m = (mx == r) & (mx > mn)
    hue[m] = (60 * ((g - b)[m] / (mx - mn)[m])) % 360
    m2 = (mx == g) & (mx > mn) & ~m
    hue[m2] = 60 * ((b - r)[m2] / (mx - mn)[m2]) + 120
    flame = (hue > 18) & (hue < 55) & (sat > 0.45) & (mx > 0.45)
    return float(flame.mean())


def loudness(path):
    out = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    i = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    return (float(i[-1]) if i else None), (float(tp[-1]) if tp else None)


def main(path, jets=None):
    info = probe(path)
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    a = [s for s in info["streams"] if s["codec_type"] == "audio"]
    ok = True
    spec = (v["width"], v["height"], v["r_frame_rate"], v["codec_name"])
    print("spec:", spec, "audio:", a[0]["codec_name"] if a else None, "dur:", info["format"]["duration"])
    ok &= spec == (1920, 1080, "30/1", "h264") and bool(a)
    shares = []
    prev = None
    first_diff = None
    for k, f in enumerate(frames(path)):
        shares.append(orange_share(f))
        if k == 1:
            first_diff = float(np.abs(f - prev).mean())
        prev = f
    worst = int(np.argmax(shares))
    print(f"flame-colour pixels, whole film: max {max(shares) * 100:.3f}% (frame {worst}), mean {np.mean(shares) * 100:.4f}%")
    if jets:
        fps = 30
        sel = [k for k in range(len(shares)) if any(a <= k / fps < b for a, b in jets)]
        js = [shares[k] for k in sel]
        w = sel[int(np.argmax(js))]
        print(f"flame-colour pixels, jet shots {jets}: max {max(js) * 100:.3f}% (frame {w}), {len(sel)} frames")
        ok &= max(js) < 0.001
    else:
        ok &= max(shares) < 0.001
    print(f"frame0->1 mean abs diff: {first_diff:.4f} (must be > 0.004: first frame already moving)")
    ok &= first_diff > 0.004
    lu, tp = loudness(path)
    print(f"loudness: {lu} LUFS, true peak {tp} dBFS")
    print("PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    args = sys.argv[1:]
    jets = None
    if "--jets" in args:
        i = args.index("--jets")
        jets = [tuple(float(v) for v in r.split("-")) for r in args[i + 1].split(",")]
        del args[i:i + 2]
    sys.exit(0 if main(args[0], jets) else 1)
