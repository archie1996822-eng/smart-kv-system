"""Procedural score + sound design for the full film (no samples, no third-party music).

Follows the card timeline in b_full.py. Writes ../build/audio_full.wav (48 kHz stereo);
loudness is normalised later with ffmpeg loudnorm.
"""
import math
import os
import re
import subprocess
import sys

import numpy as np
from scipy import ndimage, signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import audio as A  # noqa: E402
from audio import (SR, BEAT, Mix, kick, snare, hat, bass_note, pad, riser, engine, hiss, whoosh, impact, tick, bell,  # noqa: E402
                   noise, lp, hp, bp, osc, t_axis)

import b_full as B  # noqa: E402

S = B.START
E = B.END


def at(i, frac=0.0):
    return S[i] + frac * (E[i] - S[i])


def tear(dur=0.5, seed=0):
    n = int(dur * SR)
    t = t_axis(n)
    nz = noise(n, seed)
    crackle = (np.random.default_rng(seed).random(n) < 0.004) * np.random.default_rng(seed + 1).normal(0, 3, n)
    s = bp(nz, 1500, 7000) * 0.6 + bp(crackle, 800, 6000)
    env = np.minimum(1, t / 0.02) * np.clip((dur - t) / (dur * 0.6), 0, 1)
    return s * env * (0.7 + 0.3 * np.sin(2 * np.pi * 31 * t))


def thud(dur=0.5, seed=3, f=70):
    n = int(dur * SR)
    t = t_axis(n)
    return osc(f + 40 * np.exp(-t * 30), n) * np.exp(-t * 9) + 0.3 * lp(noise(n, seed), 600) * np.exp(-t * 20)


def crunch(seed=0):
    a = 0.6 * impact(0.9, seed)
    b = 0.5 * tear(0.35, seed + 5)
    a[: len(b)] += b
    return a


def flutter(dur=0.6, seed=0):
    n = int(dur * SR)
    t = t_axis(n)
    return bp(noise(n, seed), 2000, 8000) * (0.5 + 0.5 * np.sin(2 * np.pi * 18 * t)) * np.sin(np.pi * t / dur)


def murmur(dur, seed=0):
    n = int(dur * SR)
    t = t_axis(n)
    s = bp(noise(n, seed), 300, 1800)
    s *= 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 3.1 * t)) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * t))
    return s * np.minimum(1, t / 0.4) * np.clip((dur - t) / 0.4, 0, 1)


def rumble(dur, seed=0):
    n = int(dur * SR)
    t = t_axis(n)
    return lp(noise(n, seed), 160, 4) * 3 * np.minimum(1, t / 0.3) * np.clip((dur - t) / 0.6, 0, 1)


def groove(m, t0, t1, g=1.0, roots=(55, 55, 49, 43.65), hats=True, snr=True):
    nb = int((t1 - t0) / (BEAT / 2))
    for b in range(nb):
        tt = t0 + b * BEAT / 2
        root = roots[(b // 8) % len(roots)]
        if b % 2 == 0:
            m.add(kick(), tt, 0.75 * g)
        if snr and b % 4 == 2:
            m.add(snare(seed=b), tt, 0.3 * g)
        if hats:
            m.add(hat(seed=b), tt + BEAT / 4, 0.09 * g, pan=0.25)
        m.add(bass_note(root, BEAT / 2 * 0.92), tt, 0.32 * g)


def bed(m, t0, t1, chord, g=0.2, bright=1200):
    m.add(pad(chord, t1 - t0 + 0.4, bright=bright), t0, g)


def melody(m, t0, t1, notes, step=BEAT, g=0.09, pan=-0.15):
    k = 0
    tt = t0
    while tt < t1 - 0.2:
        f = notes[k % len(notes)]
        if f:
            m.add(bell(f, 1.6), tt, g, pan=pan)
        k += 1
        tt += step


def heartbeat(m, t0, t1, g=0.5):
    tt = t0
    while tt < t1:
        m.add(kick(0.3), tt, 0.5 * g)
        m.add(kick(0.3), tt + 0.22, 0.32 * g)
        tt += 1.1


def build():
    dur = B.DURATION
    m = Mix(dur + 0.5)

    # ---- 1 飞车刺: the opening cue follows the stunt (car_pose timings in b_video)
    A.cue_open(m, t_launch=1.0, t_jet=2.25, t_apex=2.3, t_flip0=3.9, t_flip1=5.1, t_land=5.5, tail=at(4, 1.0) - 5.5 - 0.1)
    m.add(murmur(at(4, 1.0) - at(4) + 0.3, 7), at(4) - 0.2, 0.25)
    bed(m, 6.6, at(4, 1.0), [220, 261.6, 329.6], 0.08, 1600)

    # ---- 2 砸回谷底: groove stops on the tear, sparse minor bed
    m.add(tear(0.9, 1), at(5, 0.1), 0.6)
    t2, t2e = at(5, 0.3), at(13, 1.0)
    bed(m, t2, t2e, [110, 130.8, 164.8], 0.22, 900)
    melody(m, at(6), at(12, 1.0), [440, 0, 392, 0, 329.6, 0, 349.2, 0], step=BEAT, g=0.07)
    m.add(thud(), at(6, 0.05), 0.6)
    heartbeat(m, at(7), at(8, 1.0), 0.6)
    for k, tb in enumerate((0.12, 0.39, 0.66)):
        m.add(crunch(10 + k), at(9, tb), 0.45, pan=(k - 1) * 0.4)
    for k in range(6):
        m.add(flutter(0.5, 20 + k), at(10, 0.1 + 0.13 * k), 0.25, pan=-0.3)
    m.add(tear(0.7, 3), at(11, 0.25), 0.55)
    m.add(lp(noise(int((E[12] - S[12]) * SR), 30), 3000) * 0.25, at(12), 0.4)   # paper rain
    m.add(pad([55, 82.4], E[13] - S[13] + 0.3, bright=400), at(13), 0.25)       # hold breath
    hit = at(14, 0.12 + 0.28 * 0.3)
    m.add(impact(1.8, 44), hit, 1.0)
    bed(m, hit, at(14, 1.0) + 0.6, [110, 164.8, 220, 277.2], 0.28, 2200)

    # ---- 3 九月留命
    groove(m, at(15), at(16), 0.6, roots=(55,), hats=False, snr=False)
    m.add(rumble(E[16] - S[16] + 0.3, 31), at(16, 0.05), 0.6)
    m.add(riser(E[16] - S[16], 120, 2600, 32), at(16), 0.35)
    m.add(impact(1.4, 33), at(16, 0.25), 0.6)
    bed(m, at(17), at(18, 1.0), [261.6, 329.6, 392, 523.3], 0.22, 2600)
    melody(m, at(17), at(18, 1.0), [523.3, 659.3, 784, 659.3], step=BEAT / 2, g=0.06)
    m.add(thud(0.4, 8, 90), at(19), 0.5)
    bed(m, at(19), at(19, 1.0), [98, 146.8], 0.25, 500)
    for k in range(int((E[19] - S[19]) / BEAT)):
        m.add(tick(), at(19) + k * BEAT, 0.25)

    # ---- 4 两家都救: ticking clock + low pulse
    t4, t4e = at(20), at(23, 1.0)
    for k in range(int((t4e - t4) / BEAT)):
        m.add(tick(), t4 + k * BEAT, 0.3)
    groove(m, t4, t4e, 0.45, roots=(55, 49), hats=False, snr=False)
    bed(m, t4, t4e, [110, 130.8, 164.8], 0.14, 700)
    m.add(whoosh(0.6, 41), at(22, 0.05), 0.45)
    m.add(thud(0.6, 42, 55), at(22, 0.75), 0.6)
    m.add(tear(0.6, 43), at(23, 0.08), 0.7)
    m.add(whoosh(0.5, 44), at(23, 0.2), 0.35, pan=-0.4)
    m.add(whoosh(0.5, 45), at(23, 0.2), 0.35, pan=0.4)
    m.add(impact(1.6, 46), at(24, 0.05), 0.85)
    bed(m, at(24), at(24, 1.0), [130.8, 196, 261.6], 0.25, 1800)
    bed(m, at(25), at(25, 1.0), [261.6, 329.6, 392], 0.15, 1500)
    melody(m, at(25), at(25, 1.0), [784, 659.3, 523.3, 659.3, 587.3, 523.3], step=BEAT / 2, g=0.06)

    # ---- 5 还要挨
    m.add(thud(0.7, 51, 60), at(26, 0.35), 0.8)
    m.add(impact(0.8, 52), at(26, 0.45), 0.4)
    bed(m, at(26), at(26, 1.0), [261.6, 329.6, 392, 523.3], 0.2, 2400)
    m.add(impact(1.6, 53), at(27, 0.62), 0.9)
    bed(m, at(27, 0.62), at(27, 1.0), [55, 82.4], 0.3, 400)
    melody(m, at(28), at(28, 1.0), [659.3, 0, 587.3, 523.3, 493.9, 0, 440, 0], step=BEAT / 2, g=0.06, pan=0.2)
    bed(m, at(28), at(28, 1.0), [110, 130.8, 164.8], 0.16, 800)
    for k in range(int((E[28] - S[28]) / BEAT)):
        m.add(tick(), at(28) + k * BEAT, 0.22)
    for k in range(8):
        m.add(flutter(0.45, 60 + k), at(29, 0.05 + 0.08 * k), 0.22, pan=0.3)
    groove(m, at(29), at(29, 1.0), 0.5, roots=(55,), hats=False)
    bed(m, at(30), at(30, 1.0), [55, 82.4, 110], 0.22, 500)

    # ---- 6 回扣飞车: the opening groove comes back
    m.add(tear(0.9, 71), at(31, 0.05), 0.6)
    m.add(riser(E[31] - S[31], 200, 3000, 72), at(31), 0.3)
    groove(m, at(32), at(34, 1.0), 1.0)
    m.add(murmur(E[32] - S[32] + 0.3, 73), at(32), 0.22)
    m.add(hiss(E[33] - S[33], 74) * 0.7, at(33), 0.35, pan=-0.15)
    m.add(hiss(E[33] - S[33], 75, 9.0) * 0.7, at(33), 0.35, pan=0.15)
    m.add(bell(1318.5, 2.2), at(33), 0.14)
    bed(m, at(34), at(34, 1.0), [220, 277.2, 329.6, 440], 0.18, 2200)

    # ---- 7 收尾
    bed(m, at(35), at(35, 1.0), [130.8, 196, 261.6, 329.6], 0.24, 1800)
    melody(m, at(35), at(35, 1.0), [523.3, 0, 587.3, 0, 659.3, 0, 784, 0], step=BEAT / 2, g=0.07)
    bed(m, at(36), at(36, 1.0), [110, 164.8, 220], 0.2, 900)
    m.add(impact(1.8, 81), at(37), 0.8)
    m.add(engine(2.6, 80, 190, 82) * np.linspace(1, 0, int(2.6 * SR)), at(37, 0.05), 0.35)
    m.add(whoosh(1.2, 83), at(37, 0.35), 0.4)
    bed(m, at(37), dur, [130.8, 196, 261.6, 392], 0.26, 2000)

    st = m.out()[: int(dur * SR)]
    f = int(0.02 * SR)
    st[:f] *= np.linspace(0, 1, f)[:, None]
    fo = int(1.2 * SR)
    st[-fo:] *= np.linspace(1, 0, fo)[:, None]
    out = os.path.join(HERE, "..", "build", "audio_full.wav")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for _ in range(10):
        wavfile.write(out, SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
        lu = measure(out)
        if abs(lu - TARGET_LUFS) < 0.3:
            break
        st = limit(st * 10 ** ((TARGET_LUFS - lu) / 20))
    return out, lu


TARGET_LUFS = -16.0


def measure(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", err)[-1])


def limit(x, ceiling=0.66, hold=0.05, smooth=0.02):
    """Look-ahead peak limiter (ceiling ≈ -3.6 dBFS leaves room for true-peak / AAC overshoot).

    The min-filter window must be wider than the smoothing window so the smoothed gain never exceeds
    the instantaneous gain needed at any peak.
    """
    g = np.minimum(1.0, ceiling / np.maximum(np.abs(x).max(axis=1), 1e-9))
    g = ndimage.minimum_filter1d(g, int(hold * SR))
    g = ndimage.uniform_filter1d(g, int(smooth * SR))
    return x * g[:, None]


if __name__ == "__main__":
    print(build())
