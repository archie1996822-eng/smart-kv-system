"""Procedural score and sound design for the Lei Jun short.

Every sound is synthesised here from oscillators and seeded noise; no samples, no
external audio, no borrowed melodies.  All chord progressions are simple diatonic
movements in A minor / C major laid on the 96 BPM grid from timeline.py, and the
hit points are derived from the same scene-relative timings used by the visuals.

    python3 audio.py              -> build/audio.wav  (48 kHz, 16-bit, stereo)
"""
import math
import os
import sys
import time
import wave
from functools import lru_cache

import numpy as np
from scipy import signal
from scipy.ndimage import minimum_filter1d, uniform_filter1d

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timeline import ITEMS, BPM, BEAT, TOTAL  # noqa: E402

SR = 48000
N = int(round(TOTAL * SR))
E8 = BEAT / 2
E16 = BEAT / 4
TAU = 2 * math.pi
TARGET_LUFS = -16.0
CEIL_DB = -1.0

_seed = [0]
BUS = {}


# ============================================================ basics
def rng():
    _seed[0] += 1
    return np.random.default_rng(7919 * _seed[0] + 13)


def ns(dur):
    return max(1, int(round(dur * SR)))


def tt(n):
    return np.arange(n) / SR


def noise(n):
    return rng().standard_normal(n)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lerp(a, b, x):
    return a + (b - a) * x


@lru_cache(maxsize=None)
def _sos(kind, f1, f2=0.0, order=2):
    ny = SR / 2
    if kind == "lp":
        return signal.butter(order, min(f1, ny * 0.98) / ny, "lowpass", output="sos")
    if kind == "hp":
        return signal.butter(order, max(f1, 5.0) / ny, "highpass", output="sos")
    return signal.butter(order, [max(f1, 10.0) / ny, min(f2, ny * 0.98) / ny], "bandpass", output="sos")


def lp(x, f, order=2):
    return signal.sosfilt(_sos("lp", float(f), 0.0, order), x, axis=-1)


def hp(x, f, order=2):
    return signal.sosfilt(_sos("hp", float(f), 0.0, order), x, axis=-1)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bp", float(lo), float(hi), order), x, axis=-1)


def edges(x, a=0.002, r=0.01):
    n = x.shape[-1]
    na, nr = min(n // 2, ns(a)), min(n // 2, ns(r))
    if na > 1:
        x[..., :na] *= np.sin(np.linspace(0, math.pi / 2, na)) ** 2
    if nr > 1:
        x[..., -nr:] *= np.cos(np.linspace(0, math.pi / 2, nr)) ** 2
    return x


def asr(n, att, hold, rel):
    """Smooth attack (sin^2), sustain until `hold` seconds, cos^2 release over `rel`."""
    t = tt(n)
    e = np.ones(n)
    if att > 0:
        m = t < att
        e[m] = np.sin(0.5 * math.pi * t[m] / att) ** 2
    x = np.clip((t - hold) / max(rel, 1e-3), 0, 1)
    return e * np.cos(0.5 * math.pi * x) ** 2


def put(bus, t, sig, gain=1.0, pan=0.0, send=0.0):
    """Mix a mono or stereo signal into a bus at time t (equal-power pan)."""
    if gain == 0:
        return
    i0 = int(round(t * SR))
    if sig.ndim == 1:
        th = (np.clip(pan, -1, 1) + 1) * math.pi / 4
        sig = np.stack([sig * math.cos(th), sig * math.sin(th)])
    elif pan:
        sig = sig * np.array([[min(1.0, 1 - pan)], [min(1.0, 1 + pan)]])
    if i0 < 0:
        sig = sig[:, -i0:]
        i0 = 0
    i1 = min(N, i0 + sig.shape[1])
    if i1 <= i0:
        return
    seg = sig[:, : i1 - i0] * gain
    BUS[bus][:, i0:i1] += seg
    if send:
        BUS["rev"][:, i0:i1] += seg * send


# ============================================================ oscillators
def saw(freq, n, phase0=0.0):
    """PolyBLEP band-limited sawtooth; freq may be scalar or per-sample array."""
    dt = np.broadcast_to(np.asarray(freq, dtype=float) / SR, (n,))
    ph = (phase0 + np.cumsum(dt)) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    x = ph[m] / dt[m]
    y[m] -= x + x - x * x - 1
    m = ph > 1 - dt
    x = (ph[m] - 1) / dt[m]
    y[m] -= x * x + x + x + 1
    return y


def sweep_sine(f, phase0=0.0):
    return np.sin(phase0 + TAU * np.cumsum(f) / SR)


def swept_noise(n, fc, bw_oct=0.7):
    """Noise through a band-pass whose centre follows fc (array), by crossfading a
    bank of fixed band-passes (smooth, no zipper)."""
    nz = noise(n)
    fc = np.clip(fc, 40, 16000)
    lo, hi = float(fc.min()), float(fc.max())
    nb = max(3, int(math.log2(hi / lo) * 3) + 2)
    bands = np.geomspace(lo, hi, nb)
    sp = math.log2(hi / lo) / (nb - 1) if nb > 1 else 1.0
    lf = np.log2(fc)
    out = np.zeros(n)
    wsum = np.zeros(n) + 1e-9
    for fb in bands:
        b = bp(nz, fb * 2 ** (-bw_oct / 2), fb * 2 ** (bw_oct / 2)) / math.sqrt(fb / 1000)
        w = np.exp(-(((lf - math.log2(fb)) / (sp * 0.9 + 1e-6)) ** 2))
        out += w * b
        wsum += w
    return out / wsum


# ============================================================ harmony helpers
NOTE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUAL = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10),
        "sus2": (0, 2, 7), "sus4": (0, 5, 7), "add9": (0, 4, 7, 14), "madd9": (0, 3, 7, 14),
        "maj9": (0, 4, 7, 11, 14), "6": (0, 4, 7, 9), "dim": (0, 3, 6), "m9": (0, 3, 7, 10, 14)}


def _pc(s):
    pc = NOTE[s[0]]
    if len(s) > 1 and s[1] in "#b":
        pc += 1 if s[1] == "#" else -1
        return pc % 12, s[2:]
    return pc % 12, s[1:]


def parse(sym):
    main, _, sl = sym.partition("/")
    pc, q = _pc(main)
    bpc = _pc(sl)[0] if sl else pc
    return pc, QUAL[q], bpc


def voicing(sym, base=50):
    pc, ints, _ = parse(sym)
    r = base + ((pc - base) % 12)
    return [r + i for i in ints]


def bass_note(sym, base=28):
    bpc = parse(sym)[2]
    return base + ((bpc - base) % 12)


def arp_tones(sym, base=60, octaves=2):
    v = voicing(sym, base)
    tones = sorted({x + 12 * o for o in range(octaves) for x in v})
    return tones


def chords(t0, spec, fn):
    t = t0
    for sym, nb in spec:
        fn(sym, t, nb * BEAT)
        t += nb * BEAT
    return t


# ============================================================ instruments
def pad(midis, dur, cutoff=1500.0, att=0.6, rel=0.9, cents=9.0, vib=0.0, fmul=None, order=4):
    n = ns(dur + rel)
    t = tt(n)
    r = rng()
    L = np.zeros(n)
    R = np.zeros(n)
    for m in midis:
        f = mtof(m)
        for dc, wl, wr in ((-cents, 1.0, 0.3), (0.0, 0.65, 0.65), (cents, 0.3, 1.0)):
            fr = f * 2 ** (dc / 1200)
            if vib:
                fr = fr * (1 + vib * np.sin(TAU * r.uniform(4.6, 5.6) * t + r.uniform(0, TAU)))
            if fmul is not None:
                fr = fr * fmul
            v = saw(fr, n, r.random())
            L += wl * v
            R += wr * v
    x = np.stack([L, R]) / (1.2 * len(midis))
    x = lp(x, cutoff, order)
    return x * asr(n, att, dur, rel)


def strings(midis, dur, cutoff=2800.0, att=0.45, rel=0.8, vib=0.0035):
    return pad(midis, dur, cutoff, att, rel, cents=6.0, vib=vib)


@lru_cache(maxsize=None)
def _piano(m, dur_q, vel_q):
    dur, vel = dur_q / 4, vel_q / 10
    f = mtof(m)
    n = ns(dur + 0.4)
    t = tt(n)
    r = np.random.default_rng(1000 + m * 31 + vel_q)
    B = 0.0004
    tau = float(np.clip(2.8 * (261.6 / f) ** 0.6, 0.45, 7.0))
    bright = 0.35 + 0.45 * vel
    y = np.zeros(n)
    for k in range(1, 10):
        fk = k * f * math.sqrt(1 + B * k * k)
        if fk > 14000:
            break
        amp = bright ** (k - 1) / k ** 0.7
        tk = tau / (1 + 0.6 * (k - 1))
        e = 0.55 * np.exp(-t / (tk * 0.16)) + 0.45 * np.exp(-t / tk)
        y += amp * e * np.sin(TAU * fk * t + r.uniform(0, TAU))
        if k == 1:
            y += 0.4 * e * np.sin(TAU * fk * 1.0011 * t + r.uniform(0, TAU))
    nh = ns(0.015)
    y[:nh] += lp(r.standard_normal(nh), 1500 + 2500 * vel) * np.exp(-tt(nh) / 0.003) * 0.12
    y /= np.abs(y).max() + 1e-9
    y *= np.cos(0.5 * math.pi * np.clip((t - dur) / 0.4, 0, 1)) ** 2
    return edges(y, 0.0012, 0.005).astype(np.float32) * vel


def piano(m, dur=1.5, vel=0.7):
    return _piano(int(m), max(1, int(round(dur * 4))), max(1, int(round(vel * 10))))


@lru_cache(maxsize=None)
def _marimba(m, vel_q):
    vel = vel_q / 10
    f = mtof(m)
    n = ns(1.1)
    t = tt(n)
    tau = float(np.clip(0.5 * (261.6 / f) ** 0.4, 0.18, 0.8))
    y = np.sin(TAU * f * t) * np.exp(-t / tau)
    y += 0.22 * vel * np.sin(TAU * 3.93 * f * t + 0.4) * np.exp(-t / (tau * 0.18))
    if 10.7 * f < 18000:
        y += 0.06 * vel * np.sin(TAU * 10.7 * f * t + 1.1) * np.exp(-t / 0.015)
    nh = ns(0.006)
    y[:nh] += lp(np.random.default_rng(m).standard_normal(nh), 2500) * 0.08 * np.exp(-tt(nh) / 0.0015)
    return edges(y, 0.0008, 0.02).astype(np.float32) * vel


def marimba(m, vel=0.7):
    return _marimba(int(m), max(1, int(round(vel * 10))))


def celesta(m, vel=0.6):
    f = mtof(m)
    n = ns(1.6)
    t = tt(n)
    y = np.sin(TAU * f * t) * np.exp(-t / 0.7) + 0.25 * np.sin(TAU * 4.0 * f * t) * np.exp(-t / 0.12)
    y += 0.08 * np.sin(TAU * 2.0 * f * t) * np.exp(-t / 0.3)
    return edges(y, 0.001, 0.05) * vel


def bass(m, dur, vel=1.0, att=0.012, rel=0.12, drive=1.3):
    f = mtof(m)
    n = ns(dur + rel)
    t = tt(n)
    y = np.sin(TAU * f * t) + 0.28 * np.sin(TAU * 2 * f * t + 0.3) + 0.12 * lp(saw(f, n), 500)
    y = np.tanh(drive * y) / math.tanh(drive)
    return y * asr(n, att, dur, rel) * vel


def bell(f, dur=3.0, vel=1.0):
    """Inharmonic additive bell (Risset-style partial table)."""
    n = ns(dur)
    t = tt(n)
    ratios = (0.56, 0.56, 0.92, 0.92, 1.19, 1.7, 2.0, 2.74, 3.0, 3.76, 4.07)
    offs = (0, 1.0, 0, 1.7, 0, 0, 0, 0, 0, 0, 0)
    amps = (1, 0.67, 1, 1.8, 2.67, 1.67, 1.46, 1.33, 1.33, 1, 1.33)
    durs = (1, 0.9, 0.65, 0.55, 0.325, 0.35, 0.25, 0.2, 0.15, 0.1, 0.075)
    y = np.zeros(n)
    for ra, of, am, du in zip(ratios, offs, amps, durs):
        fk = f * ra + of
        if fk > 16000:
            continue
        y += am * np.exp(-t / (du * dur * 0.35)) * np.sin(TAU * fk * t)
    y /= np.abs(y).max() + 1e-9
    return edges(y, 0.0015, 0.05) * vel


def ping(f, tau=0.12, vel=1.0):
    n = ns(tau * 5)
    t = tt(n)
    y = np.sin(TAU * f * t) + 0.25 * np.sin(TAU * 2.01 * f * t)
    return edges(y * np.exp(-t / tau), 0.001, 0.01) * vel


# ============================================================ drums / percussion
def kick(vel=1.0):
    n = ns(0.5)
    t = tt(n)
    body = sweep_sine(46 + 120 * np.exp(-t / 0.032)) * np.exp(-t / 0.26)
    body = np.tanh(1.6 * body) / math.tanh(1.6)
    click = hp(noise(n), 2500) * np.exp(-t / 0.003) * 0.12
    return edges(body + click, 0.0008, 0.02) * vel


def snare(vel=1.0):
    n = ns(0.4)
    t = tt(n)
    nz = bp(noise(n), 1200, 7500) * np.exp(-t / 0.11) * 0.9
    tone = np.sin(TAU * 188 * t) * np.exp(-t / 0.05) * 0.55 + np.sin(TAU * 330 * t) * np.exp(-t / 0.03) * 0.25
    return edges(nz + tone, 0.0008, 0.02) * vel


def clap(vel=1.0):
    n = ns(0.35)
    t = tt(n)
    nz = bp(noise(n), 900, 3200)
    e = 0.7 * np.exp(-t / 0.09)
    for d in (0.0, 0.011, 0.023):
        e += np.where(t >= d, np.exp(-(t - d) / 0.005), 0)
    return edges(nz * e * 0.6, 0.0005, 0.02) * vel


def hat(vel=1.0, open_=False):
    tau = 0.11 if open_ else 0.028
    n = ns(tau * 6)
    t = tt(n)
    return edges(hp(noise(n), 7000, 4) * np.exp(-t / tau), 0.0005, 0.01) * vel


def shaker(vel=1.0):
    n = ns(0.12)
    t = tt(n)
    e = np.sin(math.pi * np.clip(t / 0.09, 0, 1)) ** 2
    return edges(bp(noise(n), 4500, 11000) * e, 0.001, 0.01) * vel * 0.6


def tom(f, vel=1.0):
    n = ns(0.6)
    t = tt(n)
    y = sweep_sine(f * (1 + 0.7 * np.exp(-t / 0.04))) * np.exp(-t / 0.22)
    y += bp(noise(n), 200, 2000) * np.exp(-t / 0.03) * 0.2
    return edges(y, 0.0008, 0.02) * vel


def cymbal(dur=2.6, vel=1.0):
    n = ns(dur)
    t = tt(n)
    nz = noise(n)
    y = hp(nz, 3500, 2) * 0.7 + bp(nz, 6000, 12000) * 0.5
    r = rng()
    for f in r.uniform(3000, 9000, 14):
        y += 0.06 * np.sin(TAU * f * t + r.uniform(0, TAU))
    y = lp(y, 13000) * np.exp(-t / (dur * 0.3))
    return edges(y, 0.002, 0.1) * vel


def rev_cymbal(dur=2.0, vel=1.0):
    """Reverse cymbal: swell that ends abruptly (with a short click-free release)."""
    n = ns(dur)
    x = np.linspace(0, 1, n)
    t = tt(n)
    nz = noise(n)
    y = hp(nz, 3000, 2) * 0.6 + bp(nz, 5000, 11000) * 0.5
    r = rng()
    for f in r.uniform(2500, 8000, 12):
        y += 0.05 * np.sin(TAU * f * t + r.uniform(0, TAU))
    y *= (np.exp(4 * x) - 1) / (math.e ** 4 - 1)
    return edges(lp(y, 12000), 0.01, 0.03) * vel


def impact(size=1.0, crack=0.4, vel=1.0):
    dur = 3.2
    n = ns(dur)
    t = tt(n)
    sub = sweep_sine(30 + 50 * np.exp(-t / 0.22)) * np.exp(-t / (0.9 * size))
    body = lp(noise(n), 260, 4) * np.exp(-t / (0.35 * size)) * 1.4
    cr = bp(noise(n), 700, 5000) * np.exp(-t / 0.05) * crack
    y = np.tanh(1.3 * (sub + body + cr))
    return edges(y, 0.0015, 0.2) * vel


def thud(vel=1.0, f0=62):
    n = ns(0.4)
    t = tt(n)
    y = sweep_sine(f0 + 60 * np.exp(-t / 0.03)) * np.exp(-t / 0.11)
    y += lp(noise(n), 450) * np.exp(-t / 0.035) * 0.5
    return edges(y, 0.001, 0.03) * vel


def heart(vel=1.0):
    n = ns(0.35)
    t = tt(n)
    y = sweep_sine(38 + 40 * np.exp(-t / 0.035)) * np.exp(-t / 0.085)
    y += lp(noise(n), 160) * np.exp(-t / 0.03) * 0.6
    return edges(lp(y, 260), 0.002, 0.03) * vel


# ============================================================ sound effects
def riser(dur, f0=280, f1=7000, tone=(160, 900), vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    y = swept_noise(n, f0 * (f1 / f0) ** (x ** 1.6))
    y = y / (np.abs(y).max() + 1e-9)
    if tone:
        y += 0.35 * sweep_sine(tone[0] * (tone[1] / tone[0]) ** (x ** 1.4))
    return edges(y * x ** 2.2, 0.01, 0.025) * vel


def whoosh(dur=0.5, f0=450, f1=3800, vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    y = swept_noise(n, f0 * (f1 / f0) ** x)
    y = y / (np.abs(y).max() + 1e-9)
    e = np.sin(math.pi * x ** 0.8) ** 2
    out = np.stack([y * e * (1.1 - 0.6 * x), y * e * (0.5 + 0.6 * x)])
    return edges(out, 0.005, 0.02) * vel


def sparkle(dur, count, base=84, vel=1.0, scale=(0, 2, 4, 7, 9)):
    """Cluster of tiny high pings on a major pentatonic."""
    n = ns(dur + 0.8)
    out = np.zeros((2, n))
    r = rng()
    for _ in range(count):
        ti = r.uniform(0, dur)
        m = base + r.choice(scale) + 12 * r.integers(0, 2)
        p = ping(mtof(m), r.uniform(0.06, 0.18), r.uniform(0.4, 1.0))
        i0 = ns(ti)
        pan = r.uniform(-0.8, 0.8)
        th = (pan + 1) * math.pi / 4
        k = min(len(p), n - i0)
        out[0, i0:i0 + k] += p[:k] * math.cos(th)
        out[1, i0:i0 + k] += p[:k] * math.sin(th)
    return out * vel


def flash_shimmer(vel=1.0):
    s = sparkle(0.35, 9, 88, 0.6)
    n = s.shape[1]
    x = np.linspace(0, 1, n)
    air = hp(noise(n), 6000) * np.exp(-tt(n) / 0.18) * 0.25
    out = s + np.stack([air, air])
    out[:, : ns(0.02)] *= np.linspace(0, 1, ns(0.02))
    return edges(out * (1 - x) ** 0.5, 0.002, 0.05) * vel


def pop(vel=1.0):
    n = ns(0.22)
    t = tt(n)
    y = sweep_sine(260 + 900 * (1 - np.exp(-t / 0.025))) * np.exp(-t / 0.055)
    y += bp(noise(n), 1800, 6000) * np.exp(-t / 0.004) * 0.35
    return edges(y, 0.0008, 0.02) * vel


def tick(hi=True, vel=1.0):
    n = ns(0.04)
    t = tt(n)
    y = bp(noise(n), 2500, 7000) * np.exp(-t / 0.0025)
    y += np.sin(TAU * (2600 if hi else 1900) * t) * np.exp(-t / 0.006) * 0.4
    return edges(y, 0.0003, 0.005) * vel


def coin(vel=1.0, f=None):
    r = rng()
    f = f or r.uniform(2300, 3500)
    n = ns(0.45)
    t = tt(n)
    y = np.zeros(n)
    for ra, am, ta in ((1, 1, 0.22), (2.76, 0.55, 0.1), (5.40, 0.3, 0.05), (8.93, 0.15, 0.025)):
        if f * ra < 19000:
            y += am * np.sin(TAU * f * ra * t + r.uniform(0, TAU)) * np.exp(-t / ta)
    return edges(y / 2.0, 0.0005, 0.02) * vel


def light_click(vel=1.0):
    n = ns(0.06)
    t = tt(n)
    y = bp(noise(n), 1500, 6000) * np.exp(-t / 0.0022)
    y += np.sin(TAU * 950 * t) * np.exp(-t / 0.006) * 0.3
    d = ns(0.022)
    y[d:] += 0.45 * y[: n - d]
    return edges(y, 0.0003, 0.01) * vel


def paper_slide(dur=0.8, vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    rough = 0.55 + 0.45 * np.abs(lp(noise(n), 35)) / 0.1
    y = swept_noise(n, 5200 * (0.55 ** x), 1.2) * np.clip(rough, 0, 3)
    y /= np.abs(y).max() + 1e-9
    return edges(y * np.sin(math.pi * x) ** 1.5, 0.01, 0.03) * vel


def string_snap(f=659.3, vel=1.0):
    n = ns(1.2)
    t = tt(n)
    fr = f * (1 - 0.03 * (1 - np.exp(-t / 0.03)))
    ph = TAU * np.cumsum(fr) / SR
    y = np.zeros(n)
    for k in range(1, 9):
        y += np.sin(k * ph) / k * np.exp(-t / (0.35 / k ** 0.6))
    y += bp(noise(n), 2000, 7000) * np.exp(-t / 0.006) * 0.6
    y += np.sin(TAU * 110 * t) * np.exp(-t / 0.07) * 0.4
    return edges(y / 2.2, 0.0005, 0.05) * vel


def water(dur, vel=1.0):
    n = ns(dur)
    nz = noise(n)
    low = lp(nz, 700, 2) * 2.0
    mod = 0.6 + 0.4 * np.sin(TAU * 0.42 * tt(n)) * np.sin(TAU * 0.23 * tt(n) + 1)
    mid = bp(nz, 300, 1400) * (0.5 + 2.5 * np.abs(lp(noise(n), 3)))
    y = (low * 0.6 + mid * 0.6) * mod
    r = rng()
    t = tt(n)
    for ti in r.uniform(0, dur, int(dur * 6)):
        k = ns(0.03)
        i0 = ns(ti)
        if i0 + k >= n:
            continue
        f = r.uniform(350, 900)
        y[i0:i0 + k] += 0.15 * np.sin(TAU * np.cumsum(f * (1 + 2 * tt(k) / 0.03)) / SR) * np.hanning(k)
    del t
    a = np.stack([y, np.roll(y, 911)])
    return edges(a / (np.abs(a).max() + 1e-9), 0.4, 0.6) * vel


def splash(vel=1.0):
    n = ns(0.6)
    t = tt(n)
    y = bp(noise(n), 700, 5000) * (1 - np.exp(-t / 0.015)) * np.exp(-t / 0.15)
    y += lp(noise(n), 400) * np.exp(-t / 0.08) * 0.8
    return edges(y, 0.003, 0.05) * vel


def wind(dur=1.8, vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    fc = 260 * (1 + 4.5 * np.sin(math.pi * x ** 0.7) ** 2)
    y = swept_noise(n, fc, 1.0)
    y /= np.abs(y).max() + 1e-9
    e = np.sin(math.pi * x ** 0.6) ** 2
    return np.stack([y * e * (1.2 - x), y * e * (0.3 + x)]) * vel


def rain(dur, vel=1.0):
    n = ns(dur)
    nz = noise(n)
    bed = lp(hp(nz, 1800), 9000) * 0.25 + bp(nz, 400, 1500) * 0.15
    out = np.stack([bed, np.roll(bed, 3313)])
    r = rng()
    for ti in r.uniform(0, dur, int(dur * 40)):
        i0 = ns(ti)
        k = ns(0.012)
        if i0 + k >= n:
            continue
        d = bp(r.standard_normal(k), r.uniform(2500, 4500), 9000) * np.exp(-tt(k) / 0.002)
        out[r.integers(0, 2), i0:i0 + k] += d * r.uniform(0.2, 0.6)
    return edges(out / (np.abs(out).max() + 1e-9), 0.6, 0.6) * vel


def crowd(dur, vel=1.0):
    n = ns(dur)
    out = np.zeros((2, n))
    for ch in range(2):
        for lo, hi in ((250, 700), (500, 1300), (900, 2400), (1600, 3600)):
            am = np.clip(0.5 + 1.6 * lp(noise(n), 6), 0, None)
            out[ch] += bp(noise(n), lo, hi) * am
    return out / (np.abs(out).max() + 1e-9) * vel


def blip(m, vel=1.0):
    f = mtof(m)
    n = ns(0.12)
    t = tt(n)
    y = (np.sin(TAU * f * t) + 0.3 * np.sin(TAU * 3 * f * t)) * np.exp(-t / 0.035)
    return edges(y, 0.001, 0.01) * vel


def pitch_drop(dur=1.4, vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    f = 880 * (50 / 880) ** (x ** 0.65)
    y = 0.6 * sweep_sine(f) + 0.35 * lp(saw(f, n), 2200)
    return edges(y * (1 - x) ** 0.8, 0.003, 0.05) * vel


def tape_warble(dur, vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    t = tt(n)
    f = (300 + 1700 * x ** 2) * (1 + 0.08 * np.sin(TAU * (7 + 10 * x) * t))
    y = sweep_sine(f) * 0.6 + hp(noise(n), 5000) * 0.2 * (0.4 + x)
    return edges(lp(y, 5000) * (0.3 + 0.7 * x), 0.15, 0.03) * vel


# ============================================================ score
def item(scene, k=0):
    return [it for it in ITEMS if it["scene"] == scene][k]


def scene_span(scene):
    it = item(scene)
    return it["scene_start"], it["scene_end"] - it["scene_start"]


def compose():
    M, S = "mus", "sfx"

    def lpad(sym, t, d, g, cut=1400, att=0.5, rel=0.9, base=50, extra_low=True, send=0.35):
        v = voicing(sym, base)
        if extra_low:
            v = [v[0] - 12] + v
        put(M, t, pad(v, d, cut, att, rel), g, send=send)

    def lstr(sym, t, d, g, cut=2800, att=0.45, rel=0.8, base=55, top=True, send=0.4):
        v = voicing(sym, base)
        if top:
            v = v + [v[1] + 12]
        put(M, t, strings(v, d, cut, att, rel), g, send=send)

    def lbass(sym, t, d, g, base=28, att=0.02, rel=0.25):
        put(M, t, bass(bass_note(sym, base), d - 0.02, 1.0, att, rel), g)

    def larp(sym, t, d, g, inst="piano", step=E8, pat=(0, 1, 2, 3, 4, 3, 2, 1), base=60, vel=0.6,
             nd=1.0, fade=(1.0, 1.0), send=0.3, octaves=2):
        tones = arp_tones(sym, base, octaves)
        k = int(round(d / step))
        for j in range(k):
            m = tones[pat[j % len(pat)] % len(tones)]
            acc = 1.0 if j % 2 == 0 else 0.78
            gg = g * acc * lerp(fade[0], fade[1], j / max(1, k - 1))
            pan = (m - 72) / 30
            if inst == "piano":
                put(M, t + j * step, piano(m, nd, vel), gg, pan, send)
            else:
                put(M, t + j * step, marimba(m, vel), gg, pan, send)

    def pn(t, m, g, dur=2.0, vel=0.6, send=0.45):
        put(M, t, piano(m, dur, vel), g, (m - 66) / 36, send)

    def drums(t0, nb, k=0.0, sn=0.0, ht=0.0, cl=0.0, sh=0.0, half=False, ramp=(1.0, 1.0), open_hat=0.0):
        for b in range(nb):
            tb = t0 + b * BEAT
            r = lerp(ramp[0], ramp[1], b / max(1, nb - 1))
            if k and (not half or b % 2 == 0):
                put(M, tb, kick(), k * r, send=0.05)
            if sn and b % 2 == 1:
                put(M, tb, snare(), sn * r, 0.05, send=0.2)
            if cl and b % 2 == 1:
                put(M, tb, clap(), cl * r, -0.05, send=0.25)
            if ht:
                put(M, tb, hat(), ht * r * 0.6, 0.3, send=0.05)
                put(M, tb + E8, hat(open_=bool(open_hat)), ht * r, 0.3, send=0.08)
            if sh:
                put(M, tb + E8, shaker(), sh * r, -0.35, send=0.1)
                put(M, tb + E8 + E16, shaker(), sh * r * 0.6, -0.35, send=0.1)

    # ---------------------------------------------------------- 0 hook
    t0 = item("hook", 0)["start"]
    t1 = item("hook", 1)["start"]
    chords(t0, [("Am", 4), ("Fmaj7", 2), ("Dm", 3)],
           lambda s, t, d: (lpad(s, t, d, 0.17, 750, att=1.6 if t < 0.1 else 0.5, rel=1.0),
                            lbass(s, t, d, 0.12, att=0.8 if t < 0.1 else 0.1, rel=0.4)))
    chords(t1, [("Am", 3), ("F", 2), ("E", 2)],
           lambda s, t, d: (lpad(s, t, d, 0.2, 1100, att=0.3, rel=1.0),
                            lbass(s, t, d, 0.16, att=0.05, rel=0.3),
                            lstr(s, t, d, 0.05 + 0.03 * (t - t1), 1800, att=0.6, base=64, top=False)))
    nb8 = int(round((10.0 - t0) / E8))
    for j in range(nb8):
        tj = t0 + j * E8
        g = lerp(0.08, 0.16, tj / 10.0) * (1.0 if j % 2 == 0 else 0.6)
        m = 33 if tj < 8.75 else 28
        put(M, tj, bass(m + 12, 0.11, 1.0, 0.004, 0.06, 1.8), g, send=0.1)
    for b in range(0, 16, 2):
        put(M, t0 + b * BEAT, heart(), 0.22 + 0.01 * b, send=0.1)
    put(S, t1, impact(1.4, 0.15), 0.55, send=0.6)
    put(S, t1, cymbal(3.0), 0.07, send=0.5)
    put(S, t1 + 0.4, riser(10.0 - t1 - 0.4, 200, 6000, (110, 700)), 0.17, send=0.3)

    # ---------------------------------------------------------- 1 rewind
    r0, rT = scene_span("rewind")
    x = np.linspace(0, 1, ns((rT - 0.05) + 0.05))
    put(M, r0, pad(voicing("Am", 57) + [45], rT - 0.05, 1600, 0.12, 0.05, fmul=1 + x ** 2), 0.11, send=0.3)
    put(M, r0, tape_warble(rT - 0.02), 0.035, 0.25, send=0.2)
    tl, k = 0.0, 0
    while tl < rT - 0.05:
        speed = 0.4 + 2.6 * (tl / rT) ** 2
        put(S, r0 + tl, tick(k % 2 == 0), 0.11, 0.35 if k % 2 else -0.35, send=0.15)
        tl += 1.0 / (3.0 * speed)
        k += 1
    put(S, r0 + rT - 2.6, lp(rev_cymbal(2.6), 8000), 0.11, send=0.3)
    nn = ns(rT)
    xw = np.linspace(0, 1, nn)
    w = swept_noise(nn, 250 * (24 ** xw ** 2))
    w = w / np.abs(w).max() * xw ** 3
    put(S, r0, edges(w, 0.01, 0.02), 0.09, send=0.25)

    # ---------------------------------------------------------- 2 campus / startup
    c0 = item("campus")["start"]
    chords(c0, [("C", 2), ("G/B", 2), ("Am", 2), ("F", 2)],
           lambda s, t, d: (larp(s, t, d, 0.16, "marimba", pat=(0, 2, 4, 2, 1, 3, 5, 3), base=60, vel=0.7),
                            lpad(s, t, d, 0.06, 2400, att=0.3, base=55, extra_low=False),
                            lbass(s, t, d, 0.13, base=36, rel=0.3)))
    drums(c0, 8, sh=0.05)
    s0 = item("startup", 0)["start"]
    chords(s0, [("F", 2), ("G", 2), ("C", 2)],
           lambda s, t, d: (larp(s, t, d, 0.17, "piano", pat=(0, 2, 4, 5, 4, 2, 3, 1), vel=0.6, nd=0.75),
                            larp(s, t, d, 0.06, "marimba", step=BEAT, pat=(5, 4), vel=0.6),
                            lpad(s, t, d, 0.07, 2600, att=0.25, base=55, extra_low=False),
                            lbass(s, t, d, 0.15, base=36, rel=0.3)))
    drums(s0, 6, k=0.16, sh=0.06, half=True)
    f0 = item("startup", 1)["start"]
    put(S, f0, thud(1.0, 55), 0.45, send=0.35)
    chords(f0, [("Am", 4), ("Fmaj7", 3)],
           lambda s, t, d: (lpad(s, t, d, 0.075, 650, att=0.8, rel=1.2), lbass(s, t, d, 0.06, att=0.4, rel=0.6)))
    for b, m, v in ((0.5, 57, 0.5), (2.0, 64, 0.4), (3.5, 60, 0.4), (5.0, 59, 0.35), (6.0, 52, 0.3)):
        pn(f0 + b * BEAT, m, 0.24, 2.5, v)

    # ---------------------------------------------------------- 3 kingsoft / pangu / ledger / lights
    k0 = item("kingsoft")["start"]
    chords(k0, [("C", 2), ("Em", 2), ("F", 2), ("G", 1)],
           lambda s, t, d: (larp(s, t, d, 0.15, "piano", pat=(0, 2, 3, 4, 3, 2), vel=0.55, nd=1.0),
                            lpad(s, t, d, 0.08, 2000, att=0.4, base=55, extra_low=False),
                            lstr(s, t, d, 0.05, 2400, att=0.6, base=60, top=False),
                            lbass(s, t, d, 0.15, base=36)))
    drums(k0, 7, sh=0.045)
    p0, pT = scene_span("pangu")
    hit = p0 + pT * 0.55
    chords(p0, [("F", 2), ("G", 3)],
           lambda s, t, d: (larp(s, t, min(d, hit - t), 0.15, "piano", pat=(0, 2, 4, 5), vel=0.6, nd=0.75),
                            lpad(s, t, min(d, hit - t), 0.09, 2200, att=0.3, rel=0.15, base=55, extra_low=False),
                            lstr(s, t, min(d, hit - t), 0.07, 2600, att=0.5, rel=0.2, base=60),
                            lbass(s, t, min(d, hit - t), 0.16, base=36, rel=0.1)))
    drums(p0, 5, k=0.14, ht=0.03, half=True)
    put(S, hit - 1.0, riser(1.0, 600, 5000, None), 0.06)
    put(S, hit, impact(1.2, 0.55), 0.5, send=0.55)
    put(S, hit, cymbal(2.4), 0.06, send=0.4)
    dd = p0 + pT - hit
    put(M, hit + 0.05, pad([38, 45, 50, 53, 57], dd + 0.3, 600, 0.5, 1.2), 0.17, send=0.4)
    put(M, hit + 0.05, bass(26, dd, 1.0, 0.2, 0.8), 0.14)
    pn(hit + 0.1, 38, 0.35, 3.0, 0.7)
    pn(hit + 0.1, 45, 0.25, 3.0, 0.6)

    l0, lT = scene_span("ledger")
    put(M, l0, pad([33, 45, 52, 57, 60], lT - 0.2, 520, 0.5, 1.0), 0.15, send=0.35)
    put(M, l0, strings([76], lT - 0.3, 3000, 1.0, 0.8, 0.004), 0.03, send=0.5)
    kk = 0
    while kk / 1.5 < lT - 0.1:
        put(S, l0 + kk / 1.5, heart(), 0.75, send=0.12)
        put(S, l0 + kk / 1.5 + 0.12, heart(), 0.45, send=0.12)
        kk += 1
    r = rng()
    tl = 0.2
    while tl < lT - 0.15:
        flow = 1 - np.clip((tl - lT * 0.8) / (lT * 0.2), 0, 1)
        put(S, l0 + tl, coin(r.uniform(0.6, 1.0)), 0.075 * (0.4 + 0.6 * flow), r.uniform(-0.4, 0.4), send=0.3)
        tl += r.uniform(0.12, 0.32) / max(0.25, flow)

    g0, gT = scene_span("lights")
    put(M, g0, pad([45, 52, 57, 60, 64], 2.5, 900, 1.0, 1.2), 0.07, send=0.5)
    put(M, g0 + 2.5, pad([41, 53, 57, 60, 64], gT - 2.5, 800, 0.8, 1.2), 0.065, send=0.5)
    for b, m, v in ((0, 57, 0.45), (0, 64, 0.35), (2, 72, 0.35), (3.5, 71, 0.3), (5, 69, 0.3), (6.5, 64, 0.28)):
        pn(g0 + b * BEAT, m, 0.24, 2.8, v, send=0.55)
    for off in (0.08, 0.2, 0.33, 0.45, 0.57, 0.68, 0.78, 0.87, 0.95):
        tl = 0.4 + (gT - 0.9) * off ** (1 / 1.4)
        put(S, g0 + tl, light_click(), 0.06, (off - 0.5) * 1.2, send=0.25)

    # ---------------------------------------------------------- 4 resign / return
    z0, zT = scene_span("resign")
    put(S, z0 + 0.05, paper_slide(0.85), 0.07, 0.2, send=0.25)
    chords(z0, [("Am", 3), ("Fmaj7", 3)],
           lambda s, t, d: lpad(s, t, d, 0.06, 900, att=0.8, rel=1.2))
    for b, m, v in ((0.5, 76, 0.4), (1.5, 74, 0.35), (2.5, 72, 0.35), (3.0, 53, 0.3), (4.0, 69, 0.35), (5.0, 67, 0.3)):
        pn(z0 + b * BEAT, m, 0.24, 2.4, v, send=0.55)
    pn(z0, 45, 0.18, 3.0, 0.4)

    u0, uT = scene_span("return")
    chords(u0, [("F", 2), ("G", 2), ("C", 1)],
           lambda s, t, d: (lstr(s, t, d, lerp(0.05, 0.14, (t - u0) / uT), 2600, att=0.8, rel=1.0, base=55),
                            lpad(s, t, d, 0.07, 1800, att=0.6),
                            larp(s, t, d, 0.11, "piano", step=E8, pat=(0, 1, 2, 3), vel=0.5, nd=1.5),
                            lbass(s, t, d, 0.12, base=36, att=0.2)))

    # ---------------------------------------------------------- 5 squeeze / feed / bubble / mountain
    q0, qT = scene_span("squeeze")
    put(M, q0, pad([38, 50, 53, 57], qT, 700, 0.15, 0.3), 0.12, send=0.3)
    ost = (26, 26, 29, 26, 28, 26, 33, 26)
    for j in range(int(round(qT / E8))):
        m = ost[j % len(ost)]
        put(M, q0 + j * E8, bass(m + 12, 0.16, 1.0, 0.004, 0.08, 2.0), 0.2 if j % 2 == 0 else 0.15, send=0.1)
        put(M, q0 + j * E8, pad([m + 24, m + 36], 0.12, 1800, 0.008, 0.08, cents=5), 0.06, send=0.15)
    drums(q0, 6, k=0.2, ht=0.025)
    put(S, q0 + 1.0, impact(0.8, 0.5), 0.36, -0.5, send=0.45)
    put(S, q0 + 1.45, impact(0.9, 0.5), 0.4, 0.5, send=0.45)

    e0, eT = scene_span("feed")
    chords(e0, [("Am", 2), ("F", 2), ("G", 2)],
           lambda s, t, d: (larp(s, t, d, 0.14, "piano", pat=(0, 2, 4, 2), vel=0.6, nd=0.75),
                            lpad(s, t, d, 0.09, 2200, att=0.2),
                            lstr(s, t, d, 0.07, 2600, att=0.3, base=60)))
    for j in range(int(round((eT - BEAT) / E8))):
        sym = ("Am", "F", "G")[min(2, int(j * E8 / (2 * BEAT)))]
        put(M, e0 + j * E8, bass(bass_note(sym, 33), 0.2, 1.0, 0.004, 0.08, 1.6), 0.16, send=0.05)
    drums(e0, 5, k=0.3, ht=0.045, cl=0.12, ramp=(0.6, 1.0))
    for i in range(6):
        put(S, e0 + 0.3 + i * 0.12, coin(0.8, 2600 + 180 * i), 0.05, -0.6 + 0.24 * i, send=0.35)
    put(S, e0 + 1.5, sparkle(eT - 2.0, 10, 91, 0.5), 0.07, send=0.4)
    fill = e0 + eT - BEAT
    for j, f in enumerate((220, 185, 150, 120)):
        put(M, fill + j * E16, tom(f), 0.32 + 0.05 * j, -0.3 + 0.2 * j, send=0.2)
    put(M, fill + 3 * E16, snare(), 0.18, send=0.2)

    w0, wT = scene_span("bubble_wps")
    put(M, w0, kick(), 0.45)
    put(M, w0, cymbal(2.6), 0.13, send=0.35)
    chords(w0, [("C", 2), ("G/B", 2), ("F", 1), ("G", 1)],
           lambda s, t, d: (lstr(s, t, d, 0.12, 3200, att=0.05, rel=0.6, base=55),
                            lpad(s, t, d, 0.09, 2600, att=0.03, rel=0.6),
                            lbass(s, t, d, 0.17, base=28, att=0.005, rel=0.2),
                            larp(s, t, d, 0.13, "piano", step=E8, pat=(0, 2, 4, 3), vel=0.75, nd=0.75)))
    for m in (48, 55, 60, 64, 67):
        pn(w0, m, 0.18, 2.0, 0.8, send=0.3)
    drums(w0, 6, k=0.3, sn=0.22, ht=0.04)

    m0, mT = scene_span("mountain")
    chords(m0, [("F", 2), ("C/E", 2), ("Dm7", 2), ("Gsus4", 2), ("G", 1)],
           lambda s, t, d: (lstr(s, t, d, 0.16, 2600, att=0.7, rel=1.0, base=55),
                            lstr(s, t, d, 0.08, 1500, att=0.9, rel=1.0, base=40, top=False),
                            lpad(s, t, d, 0.06, 1400, att=0.6),
                            lbass(s, t, d, 0.17, base=28, att=0.3, rel=0.5)))
    for b, m in ((0, 69), (2, 67), (4, 65), (5, 69), (6, 67), (7.5, 62)):
        pn(m0 + b * BEAT, m, 0.22, 2.6, 0.55)
        pn(m0 + b * BEAT, m - 12, 0.14, 2.6, 0.45)
    for b in (0, 4, 8):
        put(M, m0 + b * BEAT, tom(70, 0.8), 0.18, send=0.5)

    # ---------------------------------------------------------- 6 joyo / doors / balloon
    j0, jT = scene_span("joyo")
    for ci, (sym, nb) in enumerate((("C", 2), ("F", 2), ("G", 2))):
        tc = j0 + ci * 2 * BEAT
        tones = arp_tones(sym, 60)
        for q in range(int(nb * 2)):
            if q % 2 == 1:
                for m in tones[:3]:
                    put(M, tc + q * E8, marimba(m, 0.6), 0.09, (m - 66) / 20, send=0.25)
            else:
                put(M, tc + q * E8, marimba(tones[3 + (q // 2) % 2], 0.7), 0.11, 0.3, send=0.25)
            if q % 2 == 0:
                put(M, tc + q * E8, bass(bass_note(sym, 36) + (7 if q % 4 == 2 else 0), 0.12, 1.0, 0.004, 0.1), 0.18)
        lpad(sym, tc, nb * BEAT, 0.05, 2600, att=0.2, base=55, extra_low=False)
    drums(j0, 6, k=0.2, cl=0.12, sh=0.07, half=True)

    d0, dT = scene_span("doors")
    spec = [("Am", 2), ("F", 2), ("Dm", 2), ("E", 2)]
    for ci, (sym, nb) in enumerate(spec):
        tc = d0 + ci * 2 * BEAT
        x = ci / 3
        lpad(sym, tc, nb * BEAT, lerp(0.10, 0.07, x), lerp(1800, 600, x), att=0.3, rel=0.9)
        lbass(sym, tc, nb * BEAT, lerp(0.13, 0.09, x), att=0.05)
        larp(sym, tc, nb * BEAT, lerp(0.10, 0.03, x), "marimba", pat=(0, 2, 1, 3), vel=0.6, base=57)
    r = rng()
    for i in range(30):
        ti = lerp(0.25, dT - 0.6, (i / 30) ** 0.85) + 0.2
        q = i % 6
        put(S, d0 + ti, thud(1.0, r.uniform(55, 75)), 0.16 * r.uniform(0.8, 1.1), (q - 2.5) / 5, send=0.2)
        put(S, d0 + ti, tick(False), 0.025, (q - 2.5) / 5)

    b0, bT = scene_span("balloon")
    rel_t = b0 + bT * 0.28
    chords(b0, [("Am", 2), ("Fmaj7", 2), ("C/G", 2), ("E", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.08, 1900, att=0.8, rel=1.0, base=55),
                            lpad(s, t, d, 0.06, 1000, att=0.6, rel=1.0),
                            lbass(s, t, d, 0.09, att=0.3, rel=0.5)))
    put(S, rel_t, string_snap(659.3), 0.2, 0.25, send=0.45)
    for k_, m in enumerate((76, 74, 72, 71, 69, 67, 68)):
        pn(rel_t + 0.35 + k_ * BEAT * 0.75 * (1 + 0.08 * k_), m, 0.22, 2.4, 0.45, send=0.55)
    pn(b0, 57, 0.18, 1.5, 0.45)
    pn(b0 + BEAT, 64, 0.15, 1.5, 0.4)

    # ---------------------------------------------------------- 7 think / river
    h0, hT = scene_span("think")
    idea = h0 + hT * 0.68
    put(M, h0, pad([45, 52, 59, 60, 64], idea - h0, 700, 1.0, 0.3), 0.14, send=0.5)
    put(M, h0, strings([81, 83], idea - h0, 3500, 1.5, 0.3, 0.006), 0.025, send=0.6)
    put(M, h0, bass(33, idea - h0, 1.0, 0.8, 0.3), 0.1)
    r = rng()
    pent = (69, 72, 74, 76, 79, 81, 84)
    for j in range(int((idea - h0) / E8)):
        if r.random() < 0.38:
            put(M, h0 + j * E8, celesta(int(r.choice(pent)), r.uniform(0.3, 0.6)), 0.1, r.uniform(-0.6, 0.6), send=0.6)
    put(S, idea, bell(mtof(84), 3.0), 0.14, 0.15, send=0.6)
    put(S, idea + 0.02, bell(mtof(91), 2.0), 0.06, -0.2, send=0.6)
    put(S, idea, sparkle(0.6, 14, 91, 0.6), 0.1, send=0.5)
    put(M, idea, pad([48, 55, 62, 64, 67, 71], h0 + hT - idea, 2600, 0.25, 1.0), 0.12, send=0.5)
    put(M, idea, strings([67, 72, 76], h0 + hT - idea, 3200, 0.4, 1.0), 0.08, send=0.5)
    put(M, idea, bass(36, h0 + hT - idea, 1.0, 0.1, 0.6), 0.1)

    v0, vT = scene_span("river")
    vt1 = item("river", 1)["start"]
    put(S, v0, water(vT + 0.4), 0.09, send=0.15)
    chords(v0, [("Dm", 2), ("Am", 2), ("E", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.07, 1500, att=0.5, rel=0.4, base=50, top=False),
                            lpad(s, t, d, 0.06, 900, att=0.4, rel=0.4)))
    for j in range(int(round((vt1 - v0) / E8))):
        m = (38, 38, 41, 38, 40, 40, 33, 40)[j % 8]
        put(M, v0 + j * E8, bass(m + 12, 0.18, 1.0, 0.01, 0.1, 1.4), 0.14 if j % 3 == 0 else 0.09, send=0.1)
    for b in range(0, int(round((vt1 - v0) / BEAT)), 2):
        put(M, v0 + b * BEAT + 0.04 * (b % 4), tom(78, 0.9), 0.22, -0.15, send=0.3)
        put(S, v0 + b * BEAT + 0.1, splash(), 0.07, 0.2, send=0.3)
        put(M, v0 + (b + 1.25) * BEAT, tom(95, 0.5), 0.1, 0.15, send=0.3)
    put(S, vt1 - 0.15, wind(2.0), 0.16, send=0.3)
    put(S, vt1, cymbal(2.2), 0.06, send=0.4)
    chords(vt1, [("C", 2), ("G", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.15, 3600, att=0.15, rel=0.7, base=55),
                            lpad(s, t, d, 0.1, 2600, att=0.1, rel=0.7),
                            lbass(s, t, d, 0.17, att=0.03),
                            larp(s, t, d, 0.11, "piano", pat=(0, 2, 4, 5, 6, 5, 4, 2), vel=0.6, nd=1.0)))
    put(S, vt1 + 0.1, sparkle(0.8, 8, 88, 0.6), 0.06, send=0.4)

    # ---------------------------------------------------------- 8 leave / rings
    a0, aT = scene_span("leave")
    put(S, a0 + 0.05, bell(mtof(72), 3.5), 0.16, -0.2, send=0.5)
    put(S, a0 + 0.05 + BEAT, bell(mtof(76), 3.0), 0.12, 0.2, send=0.5)
    put(S, a0 + 0.05 + 2 * BEAT, bell(mtof(79), 3.0), 0.12, 0.0, send=0.5)
    put(S, a0 + 0.2, sparkle(1.6, 24, 88, 0.7), 0.09, send=0.4)
    nconf = ns(1.5)
    conf = hp(noise(nconf), 6000) * np.exp(-tt(nconf) / 0.4) * 0.15
    put(S, a0 + 0.15, edges(np.stack([conf, np.roll(conf, 517)]), 0.02, 0.05), 0.25, send=0.3)
    chords(a0, [("C", 2), ("F", 2)],
           lambda s, t, d: (larp(s, t, d, 0.13, "marimba", pat=(0, 2, 4, 5, 4, 2), vel=0.7),
                            lpad(s, t, d, 0.08, 2600, att=0.1, base=55, extra_low=False),
                            lstr(s, t, d, 0.09, 3000, att=0.2, base=60),
                            lbass(s, t, d, 0.16, base=36)))
    drums(a0, 4, k=0.22, ht=0.04, cl=0.1)
    tb = a0 + 4 * BEAT
    chords(tb, [("Am", 2), ("Fmaj7", 2), ("Gsus4", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.09, 2000, att=0.6, rel=1.0, base=55),
                            lpad(s, t, d, 0.06, 1200, att=0.5),
                            lbass(s, t, d, 0.1, att=0.2)))
    for b, m in ((0, 76), (1.5, 74), (2, 72), (4, 72), (5, 71), (6, 67)):
        pn(tb + b * BEAT, m, 0.2, 2.2, 0.45)
    put(S, a0 + aT * 0.4 + 0.25, thud(0.6, 90), 0.12, -0.2, send=0.2)

    i0_, iT = scene_span("rings")
    chords(i0_, [("Fmaj7", 3), ("C/E", 2)],
           lambda s, t, d: (lpad(s, t, d, 0.07, 1300, att=0.5, rel=1.0),
                            lbass(s, t, d, 0.08, att=0.3)))
    ring_notes = (60, 62, 64, 67, 69, 67, 69, 72, 74, 72, 74, 76, 79, 76, 79, 81)
    for i in range(16):
        ti = 0.1 + i / 16 * (iT - 0.6)
        m = ring_notes[i]
        put(M, i0_ + ti, marimba(m, 0.55 + 0.02 * i), 0.15, (i - 7.5) / 12, send=0.45)

    # ---------------------------------------------------------- 9 forty / summit / blueprint
    o0, oT = scene_span("forty")
    put(M, o0, pad([48, 55, 62, 64, 67], 4 * BEAT, 1500, 1.4, 1.2), 0.11, send=0.55)
    put(M, o0 + 4 * BEAT, pad([41, 53, 57, 60, 64], 3 * BEAT, 1500, 1.0, 1.2), 0.11, send=0.55)
    put(M, o0, strings([79, 84], oT, 4000, 2.0, 1.0, 0.003), 0.03, send=0.6)
    put(M, o0, bass(36, 4 * BEAT, 1.0, 1.0, 0.8), 0.07)
    for b, m in ((0.5, 67), (2, 76), (4, 74), (5.5, 72)):
        pn(o0 + b * BEAT, m, 0.2, 2.8, 0.4, send=0.6)

    s0_, sT = scene_span("summit")
    chords(s0_, [("Am", 2), ("F", 2), ("C", 2), ("G", 3)],
           lambda s, t, d: (lstr(s, t, d, lerp(0.07, 0.14, (t - s0_) / sT), 2600, att=0.5, rel=0.8, base=55),
                            lpad(s, t, d, 0.07, 1800, att=0.3),
                            lbass(s, t, d, 0.15, base=28, att=0.05),
                            larp(s, t, d, lerp(0.08, 0.13, (t - s0_) / sT), "piano", pat=(0, 2, 4, 2),
                                 vel=0.55, nd=0.75)))
    drums(s0_, 9, k=0.3, ht=0.03, ramp=(0.35, 1.0))

    p0_, pT_ = scene_span("blueprint")
    chords(p0_, [("F", 2), ("G", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.14, 3000, att=0.2, base=55),
                            lpad(s, t, d, 0.09, 2400, att=0.2),
                            lbass(s, t, d, 0.17, base=28)))
    drums(p0_, 4, k=0.34, ht=0.05, cl=0.1)
    r = rng()
    pent2 = (84, 86, 88, 91, 93, 96)
    for j in range(int(round(pT_ / E16))):
        if j % 2 == 0 or r.random() < 0.5:
            m = pent2[min(5, int(r.integers(0, 3) + j * 4 / (pT_ / E16)))]
            put(S, p0_ + 0.05 + j * E16, blip(m), 0.045, r.uniform(-0.6, 0.6), send=0.3)
    put(S, p0_ + 0.5, riser(pT_ - 0.5, 400, 8000, (300, 1500)), 0.12, send=0.25)

    # ---------------------------------------------------------- 10 crash / doubt
    x0, xT = scene_span("crash")
    drop = x0 + xT * 0.28
    put(S, x0 + 0.05, bell(mtof(76), 3.0), 0.2, 0.0, send=0.5)
    put(S, x0 + 0.05, bell(mtof(83), 2.0), 0.08, 0.2, send=0.5)
    put(M, x0, pad(voicing("C", 55) + [48], drop - x0, 2600, 0.05, 0.15), 0.1, send=0.4)
    put(M, x0, strings(voicing("C", 60), drop - x0, 3000, 0.1, 0.15), 0.08, send=0.4)
    for j in range(int((drop - x0) / E8)):
        put(M, x0 + j * E8, marimba(arp_tones("C", 72)[j % 4], 0.6), 0.08, send=0.3)
    put(S, drop, pitch_drop(1.5), 0.12, send=0.4)
    put(S, drop, impact(1.6, 0.25), 0.55, send=0.5)
    after = x0 + xT - drop
    put(M, drop + 0.3, pad([33, 45, 52, 57, 60], after - 0.3, 600, 1.0, 1.0), 0.11, send=0.45)
    put(M, drop + 0.3, bass(33, after - 0.3, 1.0, 0.8, 0.6), 0.1)
    for tl, m, v in ((1.2, 57, 0.4), (2.2, 60, 0.35), (3.1, 64, 0.3), (3.6, 63, 0.25)):
        pn(drop + tl, m, 0.17, 2.4, v, send=0.55)

    y0, yT = scene_span("doubt")
    put(S, y0 - 0.3, rain(yT + 0.6), 0.07, send=0.15)
    put(M, y0, pad([33, 45, 52, 60], yT, 500, 0.8, 0.6), 0.075, send=0.45)
    for b, m, v in ((0.5, 57, 0.3), (2.0, 60, 0.28), (3.5, 64, 0.25)):
        pn(y0 + b * BEAT, m, 0.15, 2.4, v, send=0.6)
    pn(y0 + yT - 1.4, 71, 0.13, 2.0, 0.35, send=0.6)

    # ---------------------------------------------------------- 11 car / bubble / launch
    k0_, kT = scene_span("car")
    on = k0_ + kT * 0.62
    put(M, k0_, pad([33, 45, 52, 57, 60], on - k0_, 700, 0.6, 0.12), 0.1, send=0.35)
    tr = strings([57, 64, 69, 72], on - k0_, 1500, 0.8, 0.15, 0.006)
    xk = np.linspace(0, 1, tr.shape[1])
    put(M, k0_, tr * (0.4 + 0.6 * xk ** 2), 0.12, send=0.4)
    for j in range(int((on - k0_) / E8)):
        put(M, k0_ + j * E8, bass(45, 0.12, 1.0, 0.004, 0.06, 1.8), lerp(0.1, 0.2, j * E8 / (on - k0_)), send=0.1)
    for b in range(int((on - k0_) / BEAT)):
        put(M, k0_ + b * BEAT, kick(), lerp(0.12, 0.35, b * BEAT / (on - k0_)))
    put(S, k0_ + 0.4, riser(on - k0_ - 0.4, 250, 9000, (120, 1200)), 0.2, send=0.3)
    put(S, on, impact(1.3, 0.45), 0.75, send=0.5)
    put(M, on, cymbal(2.8), 0.14, send=0.4)
    put(M, on, kick(), 0.6)
    aft = k0_ + kT - on
    put(M, on, strings([48, 55, 60, 64, 67, 72, 76], aft, 3800, 0.03, 0.5), 0.18, send=0.4)
    put(M, on, pad([36, 48, 55, 60, 64, 67], aft, 3000, 0.02, 0.5), 0.15, send=0.35)
    for m in (48, 60, 64, 67, 72):
        pn(on, m, 0.16, 2.0, 0.85, send=0.3)
    put(M, on, bass(36, aft, 1.0, 0.005, 0.2), 0.22)
    put(S, on + 0.05, sparkle(0.7, 12, 91, 0.7), 0.08, send=0.4)
    tg = k0_ + math.ceil((on - k0_) / BEAT) * BEAT
    drums(tg, int(round((k0_ + kT - tg) / BEAT)), k=0.42, ht=0.05, sn=0.25)

    a0_, aT_ = scene_span("bubble_allin")
    put(M, a0_, cymbal(2.6), 0.15, send=0.4)
    chords(a0_, [("F", 2), ("G", 2), ("G", 1)],
           lambda s, t, d: (lstr(s, t, d, 0.25, 4200, att=0.05, rel=0.4, base=55),
                            lstr(s, t, d, 0.12, 2200, att=0.05, rel=0.4, base=40, top=False),
                            lpad(s, t, d, 0.13, 3000, att=0.02, rel=0.4),
                            lbass(s, t, d, 0.25, base=28, att=0.005),
                            larp(s, t, d, 0.14, "piano", pat=(0, 2, 4, 5, 6, 5, 4, 2), vel=0.8, nd=0.75)))
    drums(a0_, 4, k=0.58, sn=0.44, ht=0.08, cl=0.17)
    roll0 = a0_ + 4 * BEAT
    for j in range(8):
        put(M, roll0 + j * BEAT / 8, snare(), lerp(0.12, 0.38, j / 7), send=0.2)
    put(M, roll0, tom(150), 0.25, -0.3, send=0.2)
    put(M, roll0 + E8, tom(110), 0.3, 0.3, send=0.2)

    n0, nT = scene_span("launch")
    rev = n0 + nT * 0.12
    put(S, n0 - 1.5, rev_cymbal(1.5), 0.22, send=0.4)
    put(S, n0, impact(1.5, 0.5), 0.75, send=0.55)
    put(M, n0, cymbal(3.5), 0.2, send=0.45)
    put(M, rev, cymbal(3.0), 0.1, 0.4, send=0.45)
    chords(n0, [("C", 2), ("F", 2), ("G", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.27, 4500, att=0.03, rel=0.6, base=55),
                            lstr(s, t, d, 0.12, 2400, att=0.03, rel=0.6, base=40, top=False),
                            lpad(s, t, d, 0.14, 3400, att=0.02, rel=0.6),
                            lbass(s, t, d, 0.26, base=28, att=0.005),
                            larp(s, t, d, 0.15, "piano", pat=(0, 2, 4, 6, 5, 4, 2, 1), vel=0.85, nd=0.75)))
    for m in (48, 55, 60, 64, 67, 72):
        pn(n0, m, 0.16, 2.5, 0.9, send=0.35)
    drums(n0, 6, k=0.62, sn=0.46, ht=0.09, cl=0.18, open_hat=1)
    put(S, rev, sparkle(2.4, 40, 88, 0.8), 0.12, send=0.45)
    nc = ns(n0 + nT - rev + 0.6)
    cx = np.linspace(0, 1, nc)
    cenv = np.clip(cx / 0.25, 0, 1) ** 1.5 * (1 - 0.5 * cx) * np.cos(0.5 * math.pi * np.clip((cx - 0.8) / 0.2, 0, 1))
    put(S, rev, crowd(nc / SR) * cenv, 0.13, send=0.35)

    # ---------------------------------------------------------- 12 path / sunrise
    t0_, tT = scene_span("path")
    chords(t0_, [("F", 2), ("G", 2), ("Em7", 1), ("Am", 2)],
           lambda s, t, d: (lstr(s, t, d, 0.11, 2600, att=0.5, rel=1.0, base=55),
                            lpad(s, t, d, 0.07, 1600, att=0.4, rel=1.0),
                            lbass(s, t, d, 0.13, base=28, att=0.2, rel=0.6),
                            larp(s, t, d, 0.12, "piano", step=E8, pat=(0, 1, 2, 3, 4, 3, 2, 1), vel=0.5, nd=1.5)))
    for b, m in ((0, 72), (2, 74), (4, 71), (5, 72)):
        pn(t0_ + b * BEAT, m + 12, 0.12, 2.5, 0.45)

    u0_, uT_ = scene_span("sunrise")
    chords(u0_, [("Fmaj7", 2), ("Gsus4", 1), ("G", 1)],
           lambda s, t, d: (lstr(s, t, d, 0.11, 2600, att=0.3, rel=0.8, base=55),
                            lpad(s, t, d, 0.07, 1600, att=0.3, rel=0.8),
                            lbass(s, t, d, 0.13, base=28, att=0.1),
                            larp(s, t, d, 0.11, "piano", step=E8, pat=(0, 1, 2, 3), vel=0.5, nd=1.5)))
    fin = u0_ + 4 * BEAT
    hold = TOTAL - fin - 1.2
    put(M, fin, strings([48, 55, 60, 64, 67, 72, 76], hold, 2600, 0.5, 2.0, 0.003), 0.15, send=0.55)
    put(M, fin, pad([36, 48, 55, 62, 64, 67], hold, 1600, 0.5, 2.0), 0.09, send=0.55)
    put(M, fin, bass(36, hold, 1.0, 0.3, 2.0), 0.12)
    for k_, m in enumerate((48, 55, 60, 64, 67, 72)):
        pn(fin + k_ * 0.06, m, 0.16, 4.0, 0.55, send=0.65)
    pn(fin + 2 * BEAT, 76, 0.13, 4.0, 0.4, send=0.7)
    pn(fin + 4 * BEAT, 79, 0.1, 3.0, 0.35, send=0.75)
    put(S, fin, bell(mtof(84), 4.0), 0.05, 0.2, send=0.7)

    # ---------------------------------------------------------- transitions / bubbles
    for it in ITEMS:
        st = it["start"]
        if st > 0.2 and it["trans"] in ("wipe", "push", "iris", "fade", "dip"):
            dur = 0.5 if it["trans"] != "dip" else 0.6
            put(S, st - dur * 0.55, whoosh(dur), 0.07, send=0.3)
        elif it["trans"] == "flash":
            put(S, st, flash_shimmer(), 0.12, send=0.45)
        if it["kind"] == "bubble":
            put(S, st + 0.35, pop(), 0.28, 0.1, send=0.25)


# ============================================================ mixing / master
def make_ir(dur=2.6):
    n = ns(dur)
    t = tt(n)
    out = np.zeros((2, n))
    for ch in range(2):
        nz = noise(n)
        early = lp(nz, 9000) * np.exp(-t / 0.12) * 0.5
        late = lp(nz, 3800) * np.exp(-6.9 * t / dur) + lp(nz, 1500) * np.exp(-6.9 * t / (dur * 1.2)) * 0.6
        ir = (early + late) * (1 - np.exp(-t / 0.008))
        ir = np.concatenate([np.zeros(ns(0.018 + 0.004 * ch)), ir])[:n]
        out[ch] = ir / math.sqrt(np.sum(ir ** 2))
    return out


_KW = (np.array([[1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585],
                 [1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621]]))


def lufs(x):
    """Approximate BS.1770 integrated loudness (48 kHz K-weighting, gated)."""
    y = signal.sosfilt(_KW, x, axis=-1)
    blk, hop = ns(0.4), ns(0.1)
    p = np.sum(y ** 2, axis=0)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, x.shape[1] - blk, hop)
    z = (cs[starts + blk] - cs[starts]) / blk
    lk = -0.691 + 10 * np.log10(z + 1e-12)
    g = z[lk > -70]
    if not len(g):
        return -70.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = z[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def compress(x, thr_db=-18.0, ratio=2.0):
    env = np.sqrt(lp(np.mean(x ** 2, axis=0), 6.0, 1).clip(1e-12))
    lvl = 20 * np.log10(env)
    over = np.clip(lvl - thr_db, 0, None)
    gain = 10 ** (-over * (1 - 1 / ratio) / 20)
    return x * gain


def limit(x, ceil):
    pk = np.max(np.abs(x), axis=0)
    g = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    R = ns(0.012)
    g = minimum_filter1d(g, 2 * R + 1)
    g = uniform_filter1d(g, R)
    return x * g


def master(mix):
    mix = hp(mix, 28, 2)
    mix = compress(mix / (np.sqrt(np.mean(mix ** 2)) + 1e-9) * 10 ** (-20 / 20), -22.0, 2.0)
    n = mix.shape[1]
    fo = ns(1.5)
    tail = np.ones(n)
    tail[n - fo:] = np.cos(0.5 * math.pi * np.linspace(0, 1, fo)) ** 2
    tail[: ns(0.005)] = np.linspace(0, 1, ns(0.005))
    mix *= tail
    ceil = 10 ** (CEIL_DB / 20)
    g = 10 ** ((TARGET_LUFS - lufs(mix)) / 20)
    for _ in range(4):
        out = limit(mix * g, ceil * 0.985)
        diff = TARGET_LUFS - lufs(out)
        if abs(diff) < 0.3:
            break
        g *= 10 ** (diff / 20)
    out = np.tanh(out / ceil * 1.0) * ceil if np.abs(out).max() > ceil else out
    out *= ceil / max(np.abs(out).max(), ceil)
    out[:, -1] = 0.0
    return out


def write_wav(path, x):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    pcm = np.clip(np.round(x.T * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def build(path: str) -> None:
    t_start = time.time()
    _seed[0] = 0
    BUS.clear()
    for k in ("mus", "sfx", "rev"):
        BUS[k] = np.zeros((2, N))
    compose()
    ir = make_ir(2.6)
    wet = np.stack([signal.fftconvolve(BUS["rev"][c], ir[c])[:N] for c in range(2)])
    mix = BUS["mus"] + BUS["sfx"] * 0.9 + wet * 0.55
    if not np.all(np.isfinite(mix)):
        raise RuntimeError("non-finite samples in mix")
    out = master(mix)
    write_wav(path, out)
    BUS.clear()
    _piano.cache_clear()
    _marimba.cache_clear()
    print(f"audio: wrote {path} ({out.shape[1] / SR:.3f}s, {lufs(out):.1f} LUFS approx) "
          f"in {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    build("build/audio.wav")
