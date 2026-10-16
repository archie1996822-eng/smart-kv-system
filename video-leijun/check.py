"""Self-check for the v6 cut.

  python3 check.py              # script / timeline / caption checks + pixel checks at every card boundary
  python3 check.py --video      # also probe output mp4 (spec + EBU R128 loudness)

Checks:
  1. on-screen cards equal 「定稿剧本 v5」 character for character (parsed from docs/…v6….md)
  2. segment time ranges follow the v5 table, total ≈ 180 s
  3. at most one card visible per frame, and the previous card is fully gone before the next appears
     (verified analytically per frame and by pixel diff at every card boundary)
  4. bubbles and 「顺势而为。」 on screen ≥ 3 s, half-beat black gap after 「所有人都以为，这次他该收手了。」
  5. subtitle strip keeps ≥ 54 px from the bottom edge (pixel diff below y = 1026)
  6. (--video) 1920×1080, 30 fps, H.264, ≈180 s, integrated loudness ≈ -14 LUFS, true peak < -1 dBTP
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys

import numpy as np

import render
from render import caption_alpha
from timeline import CARDS, SHOTS, FPS, TOTAL, BEAT, SEGMENTS

ROOT = os.path.dirname(os.path.abspath(__file__))
DOC = glob.glob(os.path.join(ROOT, "docs", "*v6*.md"))[0]
fails = []


def ok(cond, msg):
    print(("  OK   " if cond else "  FAIL ") + msg)
    if not cond:
        fails.append(msg)


def parse_v5():
    src = open(DOC, encoding="utf-8").read()
    body = src[src.index("定稿剧本 v5"):]
    rows = []
    for ln in body.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*(\d+)–(\d+)″\s*\|\s*(.+?)\s*\|\s*$", ln)
        if m:
            seg, a, b, txt = m.groups()
            cards = []
            for s in txt.split(" / "):
                s = s.strip()
                if s.startswith("【气泡】"):
                    cards.append(("bubble", s[len("【气泡】"):]))
                else:
                    cards.append(("text", s))
            rows.append((seg, int(a), int(b), cards))
    return rows


def check_script():
    print("[1] cards vs 定稿剧本 v5")
    rows = parse_v5()
    want = [c for r in rows for c in r[3]]
    have = [(c["kind"], c["text"]) for c in CARDS if c["kind"] != "gap"]
    ok(len(want) == len(have), f"card count {len(have)} == v5 {len(want)}")
    for i, (w, h) in enumerate(zip(want, have)):
        if w != h:
            ok(False, f"card {i}: have {h!r} want {w!r}")
    ok(want == have, "every card identical to v5 (text + bubble markers)")
    print("[2] segments / total length")
    for (seg, a, b, _), (name, s0, s1, _) in zip(rows, SEGMENTS):
        cs = [c for c in CARDS if c["segment"] == name]
        st, en = cs[0]["start"], cs[-1]["end"]
        ok(seg == name and abs(st - a) <= BEAT and abs(en - b) <= BEAT,
           f"{name}: {st:.2f}–{en:.2f}s  (v5 {a}–{b}″)")
    ok(abs(CARDS[-1]["end"] - 180) < 0.01 and abs(SHOTS[-1]["end"] - 180) < 0.01, f"total {TOTAL:.2f}s")


def check_timing():
    print("[3] one card at a time, no leftovers")
    n = int(round(TOTAL * FPS))
    last = len(CARDS) - 1
    multi, partial_start = 0, 0
    for f in range(n):
        t = f / FPS
        vis = [i for i, c in enumerate(CARDS) if caption_alpha(c, t, i == last) > 0.002]
        if len(vis) > 1:
            multi += 1
    ok(multi == 0, f"frames with >1 visible card: {multi}")
    for i in range(1, len(CARDS)):
        prev, cur = CARDS[i - 1], CARDS[i]
        t_last = (math.ceil(cur["start"] * FPS - 1e-9) - 1) / FPS
        a_prev = caption_alpha(prev, t_last, False)
        a_cur0 = caption_alpha(cur, cur["start"], i == last)
        if a_prev > 0.002 or a_cur0 > 0.002:
            partial_start += 1
            ok(False, f"boundary {cur['start']:.2f}s: prev alpha {a_prev:.3f}, next alpha {a_cur0:.3f}")
    ok(partial_start == 0, "every card fully faded out before the next one starts")
    print("[4] holds")
    for c in CARDS:
        d = c["end"] - c["start"]
        if c["kind"] == "bubble":
            ok(d >= 3.0, f"bubble 「{c['text']}」 {d:.2f}s ≥ 3s")
        if c["text"] == "顺势而为。":
            vis = sum(1 for f in range(int(c["start"] * FPS), int(c["end"] * FPS))
                      if caption_alpha(c, f / FPS, False) > 0.95) / FPS
            ok(c["style"] == "big" and vis >= 3.0, f"「顺势而为。」 big, fully visible {vis:.2f}s ≥ 3s")
    i = next(i for i, c in enumerate(CARDS) if c["text"] == "所有人都以为，这次他该收手了。")
    g = CARDS[i + 1]
    ok(g["kind"] == "gap" and g["shot"] == "black" and 0.3 <= g["end"] - g["start"] <= 1.0,
       f"black gap {g['start']:.2f}–{g['end']:.2f}s after 「所有人都以为…」")


def check_pixels():
    print("[5] pixel checks (caption on vs off)")
    sc = 0.5
    bottom = int((1080 - 54) * sc)
    worst_bottom, leftovers = 0.0, []
    for i, c in enumerate(CARDS):
        if c["kind"] != "text":
            continue
        mid = int(((c["start"] + c["end"]) / 2) * FPS)
        a = np.frombuffer(render.render_frame(mid, sc).get_data(), np.uint8).astype(int)
        b = np.frombuffer(render.render_frame(mid, sc, captions=False).get_data(), np.uint8).astype(int)
        w = int(1920 * sc)
        a, b = a.reshape(-1, w, 4), b.reshape(-1, w, 4)
        worst_bottom = max(worst_bottom, np.abs(a[bottom:] - b[bottom:]).max())
        if not np.abs(a - b).max() > 30:
            ok(False, f"card {i} not visible at mid-point")
    ok(worst_bottom == 0, f"no caption pixels within 54 px of the bottom edge (max diff {worst_bottom})")
    for i in range(1, len(CARDS)):
        f = math.ceil(CARDS[i]["start"] * FPS - 1e-9)
        for ff in (f - 2, f - 1):
            a = np.frombuffer(render.render_frame(ff, sc).get_data(), np.uint8).astype(int)
            b = np.frombuffer(render.render_frame(ff, sc, captions=False).get_data(), np.uint8).astype(int)
            d = np.abs(a - b).max()
            if d > 0:
                leftovers.append((ff / FPS, d))
    ok(not leftovers, f"the 2 frames before every card change carry no caption pixels at all {leftovers[:5]}")


def probe(path):
    print("[6] video", os.path.basename(path))
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                                  capture_output=True, text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next(s for s in j["streams"] if s["codec_type"] == "audio")
    dur = float(j["format"]["duration"])
    ok(v["codec_name"] == "h264" and v["width"] == 1920 and v["height"] == 1080, f"{v['codec_name']} {v['width']}x{v['height']}")
    ok(v["r_frame_rate"] == "30/1", f"fps {v['r_frame_rate']}")
    ok(abs(dur - 180) < 0.5, f"duration {dur:.2f}s")
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-map", "0:a", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = r[r.rindex("Summary:"):]
    I = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summ).group(1))
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ).group(1))
    ok(abs(I + 14) <= 0.5, f"integrated loudness {I} LUFS (target -14)")
    ok(tp < -1.0, f"true peak {tp} dBTP (< -1)")
    ok(a["codec_name"] == "aac", f"audio {a['codec_name']} {a.get('sample_rate')} Hz")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", nargs="?", const=os.path.join(ROOT, "output", render.OUT_NAME))
    ap.add_argument("--no-pixels", action="store_true")
    a = ap.parse_args()
    check_script()
    check_timing()
    if not a.no_pixels:
        check_pixels()
    if a.video:
        probe(a.video)
    print("\nALL CHECKS PASSED" if not fails else f"\n{len(fails)} CHECK(S) FAILED")
    sys.exit(1 if fails else 0)
