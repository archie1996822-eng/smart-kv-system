"""混音：旁白 / 人物短句就位 + 代码生成的纪录片配乐与音效 + 人声闪避。

输出：build/mix.wav（立体声 44.1kHz），build/char_env.npy（人物短句逐帧响度，驱动口型）。
"""
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

from script import DURATION, FPS, LINES, YEAR_CARDS

SR = 44100
ROOT = Path(__file__).parent
BUILD = ROOT / "build"
rng = np.random.default_rng(7)


def decode(path):
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"])
    return np.frombuffer(raw, dtype=np.float32).copy()


def tt(t):
    return int(round(t * SR))


def smooth(x, win):
    win = max(1, int(win))
    c = np.cumsum(np.concatenate([np.zeros(win // 2 + 1), x, np.zeros(win)]))
    return (c[win:win + len(x)] - c[:len(x)]) / win


def lowpass_noise(n, win):
    return smooth(rng.standard_normal(n), win)


def env_adsr(n, a, r):
    e = np.ones(n)
    na, nr = min(n, tt(a)), min(n, tt(r))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr)
    return e


def add(buf, sig, t):
    i = tt(t)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def boom(dur=1.6, f0=58):
    n = tt(dur)
    t = np.arange(n) / SR
    f = f0 * (1 + 1.2 * np.exp(-t * 18))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
    noise = lowpass_noise(n, 18) * np.exp(-t * 9) * 0.9
    return (body + noise) * 0.9


def kick():
    n = tt(0.35)
    t = np.arange(n) / SR
    f = 45 + 90 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)


def whoosh(dur=0.7):
    n = tt(dur)
    t = np.linspace(0, 1, n)
    return lowpass_noise(n, 6) * np.sin(np.pi * t) ** 2 * 1.4


def riser(dur=2.2):
    n = tt(dur)
    t = np.arange(n) / SR
    f = 180 * (4 ** (t / dur))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    noise = lowpass_noise(n, 4) * 0.8
    return (tone + noise) * (t / dur) ** 2.2


def click():
    n = tt(0.03)
    t = np.arange(n) / SR
    return rng.standard_normal(n) * np.exp(-t * 260) * 0.35


def heartbeat():
    out = np.zeros(tt(0.7))
    k = kick() * 0.9
    out[: len(k)] += k
    k2 = kick() * 0.6
    s = tt(0.22)
    out[s: s + len(k2)] += k2[: len(out) - s]
    return out


NOTE = {"D2": 73.42, "F2": 87.31, "A2": 110.0, "Bb1": 58.27, "C2": 65.41, "G2": 98.0,
        "D3": 146.83, "F3": 174.61, "A3": 220.0, "Bb2": 116.54, "C3": 130.81, "E3": 164.81,
        "G3": 196.0, "D4": 293.66, "F4": 349.23, "A4": 440.0, "C4": 261.63, "E4": 329.63,
        "Bb3": 233.08, "G4": 392.0}
CHORDS = [  # Dm - Bb - F - C
    ["D2", "A2", "D3", "F3", "A3"],
    ["Bb1", "F2", "Bb2", "D3", "F3"],
    ["F2", "C3", "F3", "A3", "C4"],
    ["C2", "G2", "C3", "E3", "G3"],
]


def intensity(t):
    pts = [(0, 0.55), (8, 0.5), (12.6, 0.6), (18, 0.55), (27.8, 0.45), (34, 0.5), (42, 0.75),
           (50.4, 0.9), (57.3, 1.0), (60, 0.6), (67.2, 0.45), (70.4, 0.2), (72.4, 0.35),
           (76.3, 0.8), (85, 1.0), (94, 0.75), (101, 0.6), (DURATION, 0.0)]
    xs, ys = zip(*pts)
    return np.interp(t, xs, ys)


def pad(n):
    t = np.arange(n) / SR
    chord_len = 8.0
    out_l = np.zeros(n)
    out_r = np.zeros(n)
    idx = (t // chord_len).astype(int)
    for ci in range(int(DURATION // chord_len) + 2):
        notes = CHORDS[ci % 4]
        start = ci * chord_len - 1.0
        end = start + chord_len + 2.0
        a, b = max(0, tt(start)), min(n, tt(end))
        if a >= b:
            continue
        seg_t = t[a:b] - start
        w = np.clip(np.minimum(seg_t / 1.5, (chord_len + 2.0 - seg_t) / 1.5), 0, 1)
        w = np.sin(w * np.pi / 2) ** 2
        for k, nm in enumerate(notes):
            f = NOTE[nm]
            amp = 0.16 if k == 0 else 0.07
            ph = rng.uniform(0, 6.28)
            sl = np.sin(2 * np.pi * f * 0.998 * seg_t + ph) + 0.25 * np.sin(4 * np.pi * f * seg_t)
            sr_ = np.sin(2 * np.pi * f * 1.002 * seg_t + ph + 0.5) + 0.25 * np.sin(4 * np.pi * f * seg_t + 0.3)
            out_l[a:b] += amp * w * sl
            out_r[a:b] += amp * w * sr_
    del idx
    return out_l, out_r


def bass_pulse(n):
    out = np.zeros(n)
    t = np.arange(n) / SR
    roots = [73.42, 58.27, 87.31, 65.41]
    step = 60 / 84 / 2
    k = 0
    while k * step < DURATION:
        st = k * step
        lvl = float(np.interp(st, [0, 18, 20, 34, 42, 50, 60, 70, 76, 77, 94, 98, DURATION],
                                  [0, 0, .35, .35, .3, .6, .5, 0, 0, .7, .85, .4, 0]))
        if lvl > 0:
            f = roots[int(st // 8.0) % 4]
            m = tt(0.32)
            tt_ = np.arange(m) / SR
            note = np.sin(2 * np.pi * f * tt_) * np.exp(-tt_ * 9) * lvl * 0.5
            add(out, note, st)
        k += 1
    return out


def build():
    BUILD.mkdir(exist_ok=True)
    n = tt(DURATION)
    t = np.arange(n) / SR
    voice = np.zeros(n)
    char = np.zeros(n)
    for line_id, kind, start, _ in LINES:
        s = decode(BUILD / "tts" / f"{line_id}.mp3")
        s = s / (np.abs(s).max() + 1e-9) * 0.9
        if kind == "c":
            wet = s.copy()
            for dly, g in ((0.055, 0.16), (0.11, 0.08), (0.19, 0.04)):
                d = tt(dly)
                wet[d:] += s[:-d] * g
            add(char, wet * 0.92, start)
        else:
            add(voice, s, start)

    pl, pr = pad(n)
    inten = intensity(t)
    music_l = pl * inten
    music_r = pr * inten
    b = bass_pulse(n)
    music_l += b
    music_r += b

    fx = np.zeros(n)
    for ct, *_ in YEAR_CARDS:
        add(fx, boom(1.4, 62) * 0.55, ct)
    beats = 60 / 84
    for k in range(int((57.3 - 50.4) / beats)):
        add(fx, kick() * 0.5, 50.4 + k * beats)
    for k in range(int((94 - 77) / beats)):
        add(fx, kick() * (0.45 + 0.25 * k / 23), 77 + k * beats)
    for st in (8.0, 18.0, 34.0, 42.0, 47.4, 60.0, 76.0, 94.0, 98.4):
        add(fx, whoosh() * 0.35, st - 0.35)
    add(fx, riser(2.4) * 0.5, 57.3 - 2.4)
    add(fx, riser(2.0) * 0.45, 76.3 - 2.0)
    add(fx, riser(1.6) * 0.4, 85.0 - 1.6)
    add(fx, boom(2.2, 50) * 0.9, 57.3)
    meta8 = json.loads((BUILD / "tts" / "n08.json").read_text())
    pofa = next(w["t"] for w in meta8["words"] if "破" in w["text"]) + 60.6
    add(fx, boom(2.0, 48) * 1.0, pofa)
    for k in range(5):
        add(fx, heartbeat() * 0.6, 72.6 + k * 0.85)
    add(fx, boom(2.4, 46) * 0.9, 87.6)
    for st in np.concatenate([np.cumsum(rng.uniform(0.08, 0.2, 30)), 94 + np.cumsum(rng.uniform(0.08, 0.2, 18))]):
        if st < 3.6 or 94 < st < 97:
            add(fx, click(), float(st))

    # 人声闪避
    vpres = smooth(np.abs(voice) + np.abs(char), tt(0.25))
    vpres = np.clip(vpres / 0.08, 0, 1)
    duck = 1 - 0.62 * smooth(vpres, tt(0.3))
    mus_gain = 0.55
    L = voice * 1.0 + char * 1.0 + (music_l * mus_gain + fx * 0.6) * duck
    R = voice * 1.0 + char * 1.0 + (music_r * mus_gain + fx * 0.6) * duck
    fade = np.ones(n)
    fade[-tt(1.5):] = np.linspace(1, 0, tt(1.5))
    L *= fade
    R *= fade
    peak = max(np.abs(L).max(), np.abs(R).max())
    L, R = L / peak * 0.95, R / peak * 0.95
    st = np.stack([L, R], axis=1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(str(BUILD / "mix.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())

    nf = int(DURATION * FPS)
    spf = SR / FPS
    env = np.array([np.sqrt(np.mean(char[int(i * spf): int((i + 1) * spf)] ** 2) + 1e-12)
                    for i in range(nf)])
    env = env / (env.max() + 1e-9)
    np.save(BUILD / "char_env.npy", env)
    print("mix.wav", DURATION, "s; char_env frames", nf)


if __name__ == "__main__":
    build()
