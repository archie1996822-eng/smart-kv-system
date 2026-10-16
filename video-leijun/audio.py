"""Procedural score and sound design for the Lei Jun short (v6 timeline, 180 s).

Every sound is synthesised here from oscillators and seeded noise; no samples, no
external audio, no borrowed melodies.  The score is an original theme in A minor /
C major laid on the 96 BPM grid from timeline.py; every hit point is looked up by
scene name from SHOTS so the music follows the picture when the timeline moves.

Arc:  hook -> youth -> lows pressing (seg 2-3, ledger, joyo, night) -> the turn
(think / river -> shunshi) -> rebuilding -> IPO gong -> music stops at the crash ->
near silence (doubt) -> black -> car climax -> resolution / sunrise.

    python3 audio.py              -> build/audio.wav  (48 kHz, 16-bit, stereo)

Master: -14 LUFS integrated (BS.1770 K-weighting + gating), true peak about -1.5 dBTP
(4x oversampled peak limiter).
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
from timeline import SHOTS, CARDS, BPM, BEAT, TOTAL  # noqa: E402,F401

SR = 48000
N = int(round(TOTAL * SR))
E8 = BEAT / 2
E16 = BEAT / 4
TAU = 2 * math.pi
TARGET_LUFS = -14.0
CEIL_DBTP = -1.6

_seed = [0]
BUS = {}
BUSES = ("mus", "sfx", "quiet")


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
    """Mix a mono or stereo signal into a bus at time t (equal-power pan); `send`
    feeds the bus's own reverb return."""
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
        BUS["rev_" + bus][:, i0:i1] += seg * send


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
    return sorted({x + 12 * o for o in range(octaves) for x in v})


def seq(t0, t1, spec, fn):
    """Lay chords (sym, beats) from t0, cycling the spec and truncating at t1."""
    t, i = t0, 0
    while t < t1 - 1e-6:
        sym, nb = spec[i % len(spec)]
        d = min(nb * BEAT, t1 - t)
        fn(sym, t, d)
        t += d
        i += 1


# Original 8-beat theme (scale degrees 1-3-5-4-3-2-7-1); minor and major forms.
THEME_MIN = ((0, 69, 1), (1, 72, 0.5), (1.5, 76, 1.5), (3, 74, 0.5), (3.5, 72, 0.5), (4, 71, 1.5),
             (5.5, 67, 0.5), (6, 69, 2))
THEME_MAJ = ((0, 72, 1), (1, 76, 0.5), (1.5, 79, 1.5), (3, 77, 0.5), (3.5, 76, 0.5), (4, 74, 1.5),
             (5.5, 71, 0.5), (6, 72, 2))
COUNTER = ((0, 81, 1.5), (1.5, 79, 0.5), (2, 79, 1.5), (3.5, 81, 0.5), (4, 83, 2), (6, 84, 1), (7, 86, 1))


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


def lead(m, dur, vel=1.0, cutoff=3600.0, att=0.08, rel=0.45):
    """Solo string-ensemble line voice (single note, vibrato)."""
    return pad([m], dur, cutoff, att, rel, cents=7.0, vib=0.0045) * vel


def brass(midis, dur, vel=1.0, att=0.04, rel=0.3, bright=2600.0):
    """Synth brass section: detuned saws with a filter that opens on the attack."""
    n = ns(dur + rel)
    t = tt(n)
    r = rng()
    y = np.zeros(n)
    for m in midis:
        f = mtof(m)
        for dc in (-7.0, 0.0, 7.0):
            y += saw(f * 2 ** (dc / 1200), n, r.random())
    y /= 3 * len(midis)
    dark = lp(y, 800, 2)
    e = np.exp(-t / 0.16)
    y = dark + (lp(y, bright, 2) - dark) * (0.35 + 0.65 * e)
    y = np.tanh(1.4 * y) / math.tanh(1.4)
    return y * asr(n, att, dur, rel) * vel


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


def gong(f0=96.0, dur=7.0, vel=1.0):
    """Large hand gong: mallet thump, inharmonic modes whose upper partials bloom in
    after the strike, a slight downward pitch glide and a noisy shimmer."""
    n = ns(dur)
    t = tt(n)
    r = rng()
    glide = 1 - 0.012 * (1 - np.exp(-t / 0.9))
    modes = ((1.00, 1.00, 0.000, 1.00), (1.004, 0.55, 0.000, 0.95), (1.52, 0.50, 0.020, 0.80),
             (2.03, 0.55, 0.050, 0.70), (2.44, 0.42, 0.120, 0.60), (2.97, 0.38, 0.200, 0.50),
             (3.55, 0.32, 0.280, 0.42), (4.18, 0.28, 0.350, 0.36), (4.83, 0.24, 0.420, 0.30),
             (5.61, 0.20, 0.460, 0.25), (6.92, 0.14, 0.500, 0.20), (8.31, 0.10, 0.520, 0.15))
    y = np.zeros(n)
    for ra, am, bloom, dec in modes:
        f = f0 * ra * glide
        if f0 * ra > 15000:
            continue
        env = (1 - np.exp(-t / (0.004 + bloom))) * np.exp(-t / (dec * dur * 0.42))
        y += am * env * np.sin(TAU * np.cumsum(f) / SR + r.uniform(0, TAU))
    y /= np.abs(y).max() + 1e-9
    shimmer = bp(noise(n), 1800, 6500) * (1 - np.exp(-t / 0.4)) * np.exp(-t / (dur * 0.16))
    shimmer /= np.abs(shimmer).max() + 1e-9
    thump = lp(noise(n), 280, 4) * np.exp(-t / 0.035)
    thump = thump / (np.abs(thump).max() + 1e-9) * 0.6
    thump += sweep_sine(f0 * 0.5 * (1 + 0.6 * np.exp(-t / 0.03))) * np.exp(-t / 0.3) * 0.5
    y = y + 0.18 * shimmer + thump
    return edges(y / (np.abs(y).max() + 1e-9), 0.0008, 0.3) * vel


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


def tom(f, vel=1.0, decay=0.22):
    n = ns(max(0.6, decay * 4))
    t = tt(n)
    y = sweep_sine(f * (1 + 0.7 * np.exp(-t / 0.04))) * np.exp(-t / decay)
    y += bp(noise(n), 200, 2000) * np.exp(-t / 0.03) * 0.2
    return edges(y, 0.0008, 0.02) * vel


def taiko(vel=1.0):
    n = ns(1.4)
    t = tt(n)
    y = sweep_sine(58 * (1 + 0.5 * np.exp(-t / 0.05))) * np.exp(-t / 0.42)
    y += lp(noise(n), 900) * np.exp(-t / 0.025) * 0.7
    y += bp(noise(n), 120, 400) * np.exp(-t / 0.18) * 0.5
    return edges(np.tanh(1.3 * y), 0.0008, 0.05) * vel


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


def wave_rush(dur=3.6, muffle=None, vel=1.0):
    """A data wave rushing past left-to-right: Doppler-ish band sweep, low rumble and
    a faint digital tone, peaking a little after the middle."""
    n = ns(dur)
    x = np.linspace(0, 1, n)
    bump = np.exp(-(((x - 0.55) / 0.24) ** 2))
    y = swept_noise(n, 260 * (14 ** bump), 1.0)
    y /= np.abs(y).max() + 1e-9
    rumble = lp(noise(n), 160, 2)
    rumble /= np.abs(rumble).max() + 1e-9
    tone = sweep_sine(520 * (2.6 ** bump)) * (0.6 + 0.4 * np.sin(TAU * 11 * tt(n)))
    m = (y * 0.9 + rumble * 0.5 + tone * 0.12) * bump ** 0.9
    if muffle:
        m = lp(m, muffle, 2)
    th = x * math.pi / 2
    return edges(np.stack([m * np.cos(th), m * np.sin(th)]), 0.02, 0.05) * vel


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


def key_click(vel=1.0):
    n = ns(0.05)
    t = tt(n)
    y = bp(noise(n), 1500, 5000) * np.exp(-t / 0.004) + lp(noise(n), 500) * np.exp(-t / 0.008) * 0.6
    return edges(y, 0.0003, 0.008) * vel


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


def page_flip(vel=1.0):
    """Paper page turn: falling air swish then the soft flap of the page landing."""
    n = ns(0.24)
    t = tt(n)
    x = np.linspace(0, 1, n)
    sw = swept_noise(n, 6500 * (0.25 ** x), 1.1)
    sw = sw / (np.abs(sw).max() + 1e-9) * np.sin(math.pi * np.clip(x / 0.7, 0, 1)) ** 2
    d = ns(0.15)
    flap = np.zeros(n)
    flap[d:] = bp(noise(n - d), 300, 2500) * np.exp(-tt(n - d) / 0.012)
    flap /= np.abs(flap).max() + 1e-9
    return edges(sw * 0.7 + flap * 0.8, 0.003, 0.02) * vel


def footstep(vel=1.0, f0=85):
    n = ns(0.22)
    t = tt(n)
    y = sweep_sine(f0 * (1 + 0.5 * np.exp(-t / 0.01))) * np.exp(-t / 0.035)
    y += lp(noise(n), 700) * np.exp(-t / 0.02) * 0.8
    y += bp(noise(n), 2000, 6000) * np.exp(-t / 0.006) * 0.15
    return edges(y, 0.0005, 0.02) * vel


def stamp(vel=1.0):
    """Rubber stamp on paper: dull thump + papery slap."""
    n = ns(0.3)
    t = tt(n)
    y = sweep_sine(70 + 50 * np.exp(-t / 0.01)) * np.exp(-t / 0.06)
    y += lp(noise(n), 1600) * np.exp(-t / 0.012) * 0.9
    y += bp(noise(n), 2500, 7000) * np.exp(-t / 0.004) * 0.2
    return edges(y, 0.0005, 0.02) * vel


def pencil(dur=0.6, vel=1.0):
    n = ns(dur)
    x = np.linspace(0, 1, n)
    grit = np.abs(lp(noise(n), 90)) * 8
    y = bp(noise(n), 2500, 8000) * np.clip(grit, 0, 2.5)
    return edges(y / (np.abs(y).max() + 1e-9) * np.sin(math.pi * x) ** 0.7, 0.01, 0.02) * vel


def door(vel=1.0):
    """Office door pushed open: latch click, stick-slip hinge creak, soft stop bump."""
    n = ns(1.5)
    t = tt(n)
    y = np.zeros(n)
    for d, a in ((0.0, 1.0), (0.055, 0.6)):
        i = ns(d)
        k = ns(0.05)
        y[i:i + k] += a * (bp(noise(k), 1500, 6000) * np.exp(-tt(k) / 0.003)
                           + np.sin(TAU * 1250 * tt(k)) * np.exp(-tt(k) / 0.01) * 0.5)
    c0, c1 = ns(0.14), ns(1.05)
    m = c1 - c0
    x = np.linspace(0, 1, m)
    rate = 55 + 70 * np.sin(math.pi * x) + 12 * lp(noise(m), 6) * 6
    ph = np.cumsum(np.clip(rate, 20, 200) / SR)
    imp = np.diff(np.floor(ph), prepend=0.0) * (0.6 + 0.4 * np.abs(noise(m)))
    cr = bp(imp, 500, 900) * 2.0 + bp(imp, 1300, 2000) * 1.4 + bp(imp, 2600, 3400) * 0.6
    cr /= np.abs(cr).max() + 1e-9
    y[c0:c1] += cr * np.sin(math.pi * x) ** 0.6 * 0.55
    i = ns(1.12)
    k = n - i
    y[i:] += (sweep_sine(75 * (1 + 0.4 * np.exp(-tt(k) / 0.01))) * np.exp(-tt(k) / 0.07)
              + lp(noise(k), 600) * np.exp(-tt(k) / 0.03) * 0.6) * 0.8
    return edges(y, 0.0005, 0.05) * vel


def shutter(dur=1.3, vel=1.0):
    """Rolling metal shop shutter coming down: ratchet rattle, rumble, final slam."""
    n = ns(dur + 0.9)
    t = tt(n)
    y = np.zeros(n)
    r = rng()
    m = ns(dur)
    x = np.linspace(0, 1, m)
    rate = 16 + 18 * x
    ph = np.cumsum(rate / SR)
    imp = np.diff(np.floor(ph), prepend=0.0) * r.uniform(0.6, 1.0, m)
    rat = bp(imp, 1800, 3200) * 3 + bp(imp, 3800, 6000) * 1.5
    tm = tt(m)
    for f in (1210.0, 1873.0, 2950.0):
        rat += signal.lfilter([1.0], [1, -2 * math.exp(-TAU * 40 / SR) * math.cos(TAU * f / SR),
                                      math.exp(-2 * TAU * 40 / SR)], imp) * 0.02
    rat /= np.abs(rat).max() + 1e-9
    rum = bp(noise(m), 120, 700) * (0.5 + 0.5 * np.abs(lp(noise(m), 8)) * 4)
    rum /= np.abs(rum).max() + 1e-9
    y[:m] += (rat * 0.6 + rum * 0.45) * np.sin(0.5 * math.pi * np.clip(tm / 0.15, 0, 1)) ** 2
    i = m
    k = n - i
    tk = tt(k)
    slam = sweep_sine(52 * (1 + 0.6 * np.exp(-tk / 0.015))) * np.exp(-tk / 0.12)
    slam += lp(noise(k), 900) * np.exp(-tk / 0.03) * 0.8
    for f, a, d in ((312.0, 0.3, 0.35), (517.0, 0.25, 0.28), (861.0, 0.2, 0.2), (1294.0, 0.15, 0.15)):
        slam += a * np.sin(TAU * f * tk) * np.exp(-tk / d)
    y[i:] += slam
    return edges(y / (np.abs(y).max() + 1e-9), 0.003, 0.1) * vel


def water(dur, vel=1.0):
    n = ns(dur)
    nz = noise(n)
    low = lp(nz, 700, 2) * 2.0
    mod = 0.6 + 0.4 * np.sin(TAU * 0.42 * tt(n)) * np.sin(TAU * 0.23 * tt(n) + 1)
    mid = bp(nz, 300, 1400) * (0.5 + 2.5 * np.abs(lp(noise(n), 3)))
    y = (low * 0.6 + mid * 0.6) * mod
    r = rng()
    for ti in r.uniform(0, dur, int(dur * 6)):
        k = ns(0.03)
        i0 = ns(ti)
        if i0 + k >= n:
            continue
        f = r.uniform(350, 900)
        y[i0:i0 + k] += 0.15 * np.sin(TAU * np.cumsum(f * (1 + 2 * tt(k) / 0.03)) / SR) * np.hanning(k)
    a = np.stack([y, np.roll(y, 911)])
    return edges(a / (np.abs(a).max() + 1e-9), 0.4, 0.6) * vel


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


def headlights(vel=1.0):
    """Relay thunk + rising electric shimmer when the car's lights switch on."""
    n = ns(1.4)
    t = tt(n)
    x = np.linspace(0, 1, n)
    y = (sweep_sine(110 * (1 + 0.5 * np.exp(-t / 0.01))) * np.exp(-t / 0.06)
         + bp(noise(n), 1000, 4000) * np.exp(-t / 0.006) * 0.4)
    hum = sweep_sine(220 * 2 ** (1.5 * x ** 0.5)) * 0.18 + sweep_sine(330 * 2 ** (1.5 * x ** 0.5)) * 0.08
    y += hum * np.sin(math.pi * x) ** 1.2
    return edges(y, 0.0008, 0.1) * vel


# ============================================================ timeline lookups
def shot(scene):
    for s in SHOTS:
        if s["scene"] == scene:
            return s
    raise KeyError(scene)


def span(scene):
    s = shot(scene)
    return s["start"], s["end"]


def card_start(scene, k):
    return CARDS[shot(scene)["cards"][k]]["start"]


def snap(t0, dt):
    return t0 + round(dt / BEAT) * BEAT


def crash_drop():
    """Moment the price breaks below issue (visual drop at 0.28 of the crash shot),
    snapped to the beat grid."""
    x0, x1 = span("crash")
    return snap(x0, 0.28 * (x1 - x0))


# ============================================================ score
def compose():
    M, S, Q = "mus", "sfx", "quiet"

    def lpad(sym, t, d, g, cut=1400, att=0.5, rel=0.9, base=50, low=True, send=0.35, bus=M):
        v = voicing(sym, base)
        if low:
            v = [v[0] - 12] + v
        put(bus, t, pad(v, d, cut, att, rel), g, send=send)

    def lstr(sym, t, d, g, cut=2800, att=0.45, rel=0.8, base=55, top=True, send=0.4, bus=M):
        v = voicing(sym, base)
        if top:
            v = v + [v[1] + 12]
        put(bus, t, strings(v, d, cut, att, rel), g, send=send)

    def lbrass(sym, t, d, g, base=52, att=0.04, rel=0.3, send=0.3):
        put(M, t, brass(voicing(sym, base), d, 1.0, att, rel), g, send=send)

    def lbass(sym, t, d, g, base=28, att=0.02, rel=0.25):
        put(M, t, bass(bass_note(sym, base), d - 0.02, 1.0, att, rel), g)

    def bass8(sym, t, d, g, base=33, accent=1.0, octave=False):
        k = int(round(d / E8))
        for j in range(k):
            m = bass_note(sym, base) + (12 if octave and j % 2 == 1 else 0)
            put(M, t + j * E8, bass(m, E8 * 0.8, 1.0, 0.004, 0.06, 1.7), g * (accent if j % 2 == 0 else 0.8),
                send=0.05)

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

    def pn(t, m, g, dur=2.0, vel=0.6, send=0.45, bus=M):
        put(bus, t, piano(m, dur, vel), g, (m - 66) / 36, send)

    def melody(t0, notes, g, inst="piano", tr=0, vel=0.6, send=0.45, until=None, legato=1.0):
        for b, m, nb in notes:
            t = t0 + b * BEAT
            if until is not None and t >= until - 0.05:
                break
            d = nb * BEAT * legato
            if until is not None:
                d = min(d, until - t + 0.3)
            mm = m + tr
            pan = (mm - 72) / 48
            if inst == "piano":
                put(M, t, piano(mm, d + 0.5, vel), g, pan, send)
            elif inst == "lead":
                put(M, t, lead(mm, d, vel), g, pan, send)
            elif inst == "brass":
                put(M, t, brass([mm], d, vel), g, pan, send)
            elif inst == "celesta":
                put(M, t, celesta(mm, vel), g, pan, send)
            else:
                put(M, t, marimba(mm, vel), g, pan, send)

    def drums(t0, t1, k=0.0, sn=0.0, ht=0.0, cl=0.0, sh=0.0, half=False, ramp=(1.0, 1.0), open_hat=0.0):
        nb = int(round((t1 - t0) / BEAT))
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
                put(M, tb + E8, hat(open_=bool(open_hat) and b % 2 == 1), ht * r, 0.3, send=0.08)
            if sh:
                put(M, tb + E8, shaker(), sh * r, -0.35, send=0.1)
                put(M, tb + E8 + E16, shaker(), sh * r * 0.6, -0.35, send=0.1)

    def roll(t0, t1, g0, g1, div=8):
        k = int(round((t1 - t0) / (BEAT / div)))
        for j in range(k):
            put(M, t0 + j * BEAT / div, snare(), lerp(g0, g1, j / max(1, k - 1)), 0.05, send=0.2)

    def tomfill(t0, g=0.32, fs=(220, 185, 150, 120)):
        for j, f in enumerate(fs):
            put(M, t0 + j * E16, tom(f), g + 0.05 * j, -0.3 + 0.2 * j, send=0.2)

    # ========================================================== 1 hook
    h0, h1 = span("hook")
    c2 = card_start("hook", 1)
    # card 1: night, low drone in A minor, the theme quietly in the piano's low-middle register
    put(M, h0, pad([33, 45, 52, 59, 60], c2 - h0 + 0.2, 650, 1.8, 0.7), 0.17, send=0.4)
    put(M, h0, bass(33, c2 - h0, 1.0, 1.4, 0.4), 0.11)
    put(M, h0, strings([76, 83], c2 - h0, 3200, 2.5, 0.6, 0.004), 0.025, send=0.6)
    melody(h0 + BEAT, THEME_MIN, 0.3, "piano", tr=-12, vel=0.45, send=0.5)
    for b in range(0, int(round((c2 - h0) / BEAT)), 2):
        put(Q, h0 + b * BEAT, heart(), 0.2 + 0.012 * b, send=0.1)
    put(S, h0 + 0.9, wave_rush(3.7), 0.24, send=0.3)
    r = rng()
    for j in range(int((c2 - 0.5 - (h0 + 1.3)) / E16)):
        tj = h0 + 1.3 + j * E16
        x = j * E16 / (c2 - 0.5 - h0 - 1.3)
        if r.random() < 0.65:
            put(S, tj, blip(int(r.choice((84, 86, 88, 91, 93, 96))), 0.8),
                0.035 * math.sin(math.pi * x) ** 0.7, lerp(-0.8, 0.8, x) + r.uniform(-0.15, 0.15), send=0.3)
    # card 2: he raises a fist, warm light bursts
    put(S, c2 - 1.3, rev_cymbal(1.3), 0.08, send=0.3)
    put(S, c2 + 0.05, impact(1.3, 0.1), 0.45, send=0.55)
    put(S, c2 + 0.1, bell(mtof(81), 3.5), 0.07, 0.2, send=0.6)
    put(S, c2 + 0.1, sparkle(0.9, 16, 88, 0.6), 0.08, send=0.45)
    seq(c2, h1, [("Fmaj7", 2), ("G", 2), ("C/E", 3)],
        lambda s, t, d: (lpad(s, t, d, 0.17, 1300, att=0.25, rel=0.9),
                         lbass(s, t, d, 0.15, att=0.05, rel=0.3),
                         lstr(s, t, d, 0.06 + 0.012 * (t - c2), 2400, att=0.5, base=60, top=False)))
    melody(c2, ((0.5, 72, 1.5), (2, 74, 2), (4, 76, 3)), 0.11, "lead", send=0.45, until=h1)
    for j in range(int(round((h1 - c2) / E8))):
        tj = c2 + j * E8
        put(M, tj, bass(45 if tj < c2 + 4 * BEAT else 40, 0.11, 1.0, 0.004, 0.06, 1.8),
            lerp(0.08, 0.15, j * E8 / (h1 - c2)) * (1.0 if j % 2 == 0 else 0.6), send=0.1)
    for b in range(int(round((h1 - c2) / BEAT))):
        put(M, c2 + b * BEAT, kick(), lerp(0.12, 0.22, b / 6), send=0.05)
    put(S, c2 + 0.6, riser(h1 - c2 - 0.6, 200, 6000, (110, 700)), 0.14, send=0.3)

    # ========================================================== 2 rewind -> campus -> failure
    r0, r1 = span("rewind_young")
    rT = r1 - r0
    x = np.linspace(0, 1, ns(rT))
    put(M, r0, pad(voicing("C", 57) + [48], rT - 0.05, 1600, 0.12, 0.05, fmul=1 + x ** 2), 0.1, send=0.3)
    put(M, r0, tape_warble(rT - 0.02), 0.035, 0.25, send=0.2)
    tl, k = 0.0, 0
    while tl < rT - 0.05:
        speed = 0.4 + 2.6 * (tl / rT) ** 2
        put(S, r0 + tl, tick(k % 2 == 0)[::-1].copy(), 0.12, 0.35 if k % 2 else -0.35, send=0.15)
        tl += 1.0 / (3.0 * speed)
        k += 1
    put(S, r1 - 2.6, lp(rev_cymbal(2.6), 8000), 0.11, send=0.3)
    nn = ns(rT)
    xw = np.linspace(0, 1, nn)
    w = swept_noise(nn, 250 * (24 ** xw ** 2))
    put(S, r0, edges(w / np.abs(w).max() * xw ** 3, 0.01, 0.02), 0.09, send=0.25)

    c0, c1 = span("campus")
    seq(c0, c1, [("C", 2), ("G/B", 2), ("Am", 2), ("F", 2), ("G", 1)],
        lambda s, t, d: (larp(s, t, d, 0.16, "marimba", pat=(0, 2, 4, 2, 1, 3, 5, 3), base=60, vel=0.7),
                         lpad(s, t, d, 0.06, 2400, att=0.3, base=55, low=False),
                         lbass(s, t, d, 0.13, base=36, rel=0.3)))
    drums(c0, c1, k=0.12, sh=0.055, half=True)
    r = rng()
    for j in range(int((c1 - c0) / E8)):
        if r.random() < 0.25:
            put(M, c0 + j * E8, celesta(int(r.choice((84, 86, 88, 91, 93))), 0.4), 0.07, r.uniform(-0.6, 0.6),
                send=0.5)

    s0, s1 = span("closed_shop")
    put(S, s0 + 0.25, shutter(1.25), 0.2, 0.15, send=0.3)
    seq(s0, s1, [("Am", 4), ("Fmaj7", 4)],
        lambda s, t, d: (lpad(s, t, d, 0.085, 700, att=0.7, rel=1.1, base=45),
                         lbass(s, t, d, 0.07, att=0.4, rel=0.6)))
    for b, m, v in ((1.0, 76, 0.42), (2.0, 74, 0.38), (3.0, 72, 0.36), (4.5, 71, 0.34), (5.5, 69, 0.32),
                    (6.5, 64, 0.3)):
        pn(s0 + b * BEAT, m, 0.22, 2.4, v, send=0.55)

    a0, a1 = span("alone_sit")
    put(S, a0 + 0.05, thud(0.9, 46), 0.3, send=0.5)
    pn(a0 + 0.05, 33, 0.3, 4.0, 0.6, send=0.5)
    pn(a0 + 0.05, 45, 0.18, 4.0, 0.5, send=0.5)
    seq(a0, a1, [("Dm", 4), ("Am", 5)],
        lambda s, t, d: lpad(s, t, d, 0.085, 520, att=1.0, rel=1.2, base=45))
    for b, m, v in ((1.5, 65, 0.34), (3.0, 64, 0.3), (4.5, 62, 0.3), (6.0, 60, 0.28), (7.5, 57, 0.26)):
        pn(a0 + b * BEAT, m, 0.2, 2.6, v, send=0.6)
    for b in range(1, int(round((a1 - a0) / BEAT)) - 1, 2):
        put(Q, a0 + b * BEAT, heart(), 0.3, send=0.1)
        put(Q, a0 + b * BEAT + 0.13, heart(), 0.18, send=0.1)

    # ========================================================== 3 kingsoft / pangu / ledger / lights / resign / return
    k0, k1 = span("kingsoft")
    seq(k0, k1, [("C", 2), ("Em", 2), ("F", 2), ("G", 2), ("C", 2)],
        lambda s, t, d: (larp(s, t, d, 0.15, "piano", pat=(0, 2, 3, 4, 3, 2), vel=0.55, nd=1.0),
                         lpad(s, t, d, 0.075, 2000, att=0.4, base=55, low=False),
                         lstr(s, t, d, 0.05, 2400, att=0.6, base=60, top=False),
                         lbass(s, t, d, 0.14, base=36)))
    drums(k0, k1, k=0.1, sh=0.045, half=True)
    r = rng()
    tl = 0.6
    while tl < (k1 - k0) * 0.55:
        put(S, k0 + tl, key_click(r.uniform(0.6, 1.0)), 0.05, r.uniform(-0.3, 0.1), send=0.1)
        tl += r.uniform(0.07, 0.2) + (0.35 if r.random() < 0.12 else 0)

    p0, p1 = span("pangu")
    hit = p0 + 0.55 * (p1 - p0)
    seq(p0, hit, [("F", 2), ("G", 2), ("Am", 2)],
        lambda s, t, d: (larp(s, t, d, 0.15, "piano", pat=(0, 2, 4, 5), vel=0.6, nd=0.75),
                         lpad(s, t, d, 0.085, 2200, att=0.3, rel=0.15, base=55, low=False),
                         lstr(s, t, d, 0.065, 2600, att=0.5, rel=0.2, base=60),
                         lbass(s, t, d, 0.15, base=36, rel=0.1)))
    drums(p0, snap(p0, hit - p0 - 0.3), k=0.13, ht=0.025, half=True)
    put(S, hit - 1.0, riser(1.0, 600, 5000, None), 0.06)
    put(S, hit, impact(1.2, 0.55), 0.5, send=0.55)
    put(S, hit, cymbal(2.4), 0.05, send=0.4)
    put(S, hit + 0.15, pitch_drop(1.6), 0.05, send=0.4)
    dd = p1 - hit
    put(M, hit + 0.05, pad([38, 45, 50, 53, 57], dd + 0.3, 600, 0.5, 1.2), 0.16, send=0.4)
    put(M, hit + 0.05, bass(26, dd, 1.0, 0.2, 0.8), 0.13)
    pn(hit + 0.1, 38, 0.33, 3.0, 0.7)
    pn(hit + 0.1, 45, 0.24, 3.0, 0.6)

    l0, l1 = span("ledger")
    lT = l1 - l0
    put(M, l0, pad([33, 45, 52, 57, 60], lT - 0.2, 520, 0.5, 1.0), 0.15, send=0.35)
    put(M, l0, strings([76], lT - 0.3, 3000, 1.0, 0.8, 0.004), 0.03, send=0.5)
    pn(l0 + 0.05, 33, 0.25, 3.5, 0.55, send=0.5)
    kk = 0
    while kk / 1.4 < lT - 0.3:
        put(Q, l0 + 0.2 + kk / 1.4, heart(), 0.6, send=0.12)
        put(Q, l0 + 0.2 + kk / 1.4 + 0.13, heart(), 0.36, send=0.12)
        kk += 1
    for i, (tl, f) in enumerate(((0.35, 3100), (0.95, 2900), (1.75, 2700), (2.9, 2450))):
        put(S, l0 + tl, coin(0.9 - 0.12 * i, f), 0.07, -0.2 + 0.15 * i, send=0.4)

    g0, g1 = span("lights")
    gT = g1 - g0
    put(M, g0, pad([45, 52, 57, 60, 64], gT * 0.55, 900, 1.0, 1.2), 0.07, send=0.5)
    put(M, g0 + gT * 0.55, pad([41, 53, 57, 60, 64], gT * 0.45, 800, 0.8, 1.2), 0.065, send=0.5)
    for b, m, v in ((0, 57, 0.45), (0, 64, 0.35), (2, 72, 0.35), (3.5, 71, 0.3), (5, 69, 0.3), (6.5, 64, 0.28)):
        if b * BEAT < gT:
            pn(g0 + b * BEAT, m, 0.24, 2.8, v, send=0.55)
    nl = 12
    light_times = []
    for i in range(nl):
        off = (i + 0.5) / nl
        tl = 0.4 + (gT - 0.9) * off ** (1 / 1.4)
        light_times.append(g0 + tl)
        put(S, g0 + tl, light_click(), 0.065, (off - 0.5) * 1.2, send=0.25)

    z0, z1 = span("resign")
    put(S, z0 + 0.1, paper_slide(0.8), 0.08, 0.2, send=0.25)
    put(S, z0 + 0.92, thud(0.5, 130), 0.1, 0.2, send=0.25)
    seq(z0, z1, [("Am", 3), ("Fmaj7", 3)], lambda s, t, d: lpad(s, t, d, 0.06, 900, att=0.8, rel=1.2))
    for b, m, v in ((0.5, 76, 0.4), (1.5, 74, 0.35), (2.5, 72, 0.35), (3.0, 53, 0.3), (4.0, 69, 0.35),
                    (5.0, 67, 0.3)):
        pn(z0 + b * BEAT, m, 0.22, 2.4, v, send=0.55)
    pn(z0, 45, 0.18, 3.0, 0.4)

    u0, u1 = span("return_kingsoft")
    uT = u1 - u0
    put(S, u0 + 0.3, door(), 0.3, -0.25, send=0.3)
    for i in range(3):
        put(S, u0 + 1.55 + i * 0.42, footstep(0.8, 80 + 6 * (i % 2)), 0.12, -0.2 + 0.12 * i, send=0.2)
    seq(u0, u1, [("F", 2), ("G", 2), ("C", 2), ("Am", 2), ("G", 1)],
        lambda s, t, d: (lstr(s, t, d, lerp(0.05, 0.13, (t - u0) / uT), 2600, att=0.8, rel=1.0, base=55),
                         lpad(s, t, d, 0.065, 1800, att=0.6),
                         larp(s, t, d, 0.1, "piano", step=E8, pat=(0, 1, 2, 3), vel=0.5, nd=1.5),
                         lbass(s, t, d, 0.12, base=36, att=0.2)))
    mid = u0 + uT * 0.5
    nf = 11
    flips = []
    for i in range(nf):
        tf = mid + (u1 - 0.3 - mid) * (1 - (1 - i / nf) ** 1.6)
        flips.append(tf)
        put(S, tf, page_flip(), 0.08 * lerp(0.8, 1.0, i / nf), lerp(-0.2, 0.3, i / nf), send=0.15)

    # ========================================================== 4 squeeze / feed / bubble / window / mountain
    q0, q1 = span("squeeze")
    qT = q1 - q0
    put(M, q0, pad([38, 50, 53, 57], qT, 700, 0.15, 0.3), 0.12, send=0.3)
    put(M, q0, strings([74, 75], qT, 2600, 0.6, 0.3, 0.006), 0.035, send=0.4)
    ost = (26, 26, 29, 26, 28, 26, 33, 26)
    for j in range(int(round(qT / E8))):
        m = ost[j % len(ost)]
        put(M, q0 + j * E8, bass(m + 12, 0.16, 1.0, 0.004, 0.08, 2.0), 0.2 if j % 2 == 0 else 0.15, send=0.1)
        put(M, q0 + j * E8, pad([m + 24, m + 36], 0.12, 1800, 0.008, 0.08, cents=5), 0.06, send=0.15)
    drums(q0, q1, k=0.2, ht=0.025)
    put(S, q0 + 2 * BEAT, impact(0.8, 0.5), 0.34, -0.5, send=0.45)
    put(S, q0 + 4 * BEAT, impact(0.9, 0.5), 0.38, 0.5, send=0.45)

    e0, e1 = span("feed")
    eT = e1 - e0
    seq(e0, e1, [("Am", 2), ("F", 2), ("G", 2), ("E", 2)],
        lambda s, t, d: (larp(s, t, d, 0.14, "piano", pat=(0, 2, 4, 2), vel=0.6, nd=0.75),
                         lpad(s, t, d, 0.085, 2200, att=0.2),
                         lstr(s, t, d, 0.065, 2600, att=0.3, base=60)))
    seq(e0, e1 - BEAT, [("Am", 2), ("F", 2), ("G", 2), ("E", 2)], lambda s, t, d: bass8(s, t, d, 0.15))
    drums(e0, e1 - BEAT, k=0.3, ht=0.045, cl=0.12, ramp=(0.6, 1.0))
    for i in range(6):
        put(S, e0 + 0.3 + i * 0.12, coin(0.8, 2600 + 180 * i), 0.05, -0.6 + 0.24 * i, send=0.35)
    put(S, e0 + 1.5, sparkle(eT - 2.0, 10, 91, 0.5), 0.06, send=0.4)
    tomfill(e1 - BEAT)
    put(M, e1 - BEAT + 3 * E16, snare(), 0.18, send=0.2)

    w0, w1 = span("bubble_wps")
    put(M, w0, kick(), 0.45)
    put(M, w0, cymbal(2.6), 0.13, send=0.35)
    put(M, w0, brass(voicing("C", 52) + [48], 0.55, 1.0, 0.01, 0.35), 0.12, send=0.3)
    seq(w0, w1, [("C", 2), ("G/B", 2), ("F", 1), ("G", 1)],
        lambda s, t, d: (lstr(s, t, d, 0.12, 3200, att=0.05, rel=0.6, base=55),
                         lpad(s, t, d, 0.085, 2600, att=0.03, rel=0.6),
                         lbass(s, t, d, 0.17, base=28, att=0.005, rel=0.2),
                         larp(s, t, d, 0.13, "piano", step=E8, pat=(0, 2, 4, 3), vel=0.75, nd=0.75)))
    for m in (48, 55, 60, 64, 67):
        pn(w0, m, 0.17, 2.0, 0.8, send=0.3)
    drums(w0, w1, k=0.3, sn=0.22, ht=0.04)

    v0, v1 = span("window_wave")
    seq(v0, v1, [("Am", 2), ("Fmaj7", 2), ("C", 2), ("G", 2)],
        lambda s, t, d: (lpad(s, t, d, 0.08, 1100, att=0.6, rel=1.0),
                         lstr(s, t, d, 0.05, 1800, att=0.7, rel=1.0, base=55, top=False),
                         lbass(s, t, d, 0.09, att=0.3, rel=0.5),
                         larp(s, t, d, 0.075, "piano", step=BEAT, pat=(4, 3, 2, 1), vel=0.45, nd=1.5)))
    put(S, v0 + 0.7, wave_rush(3.0, muffle=2600), 0.24, send=0.35)

    m0, m1 = span("mountain")
    mb = card_start("mountain", 1)
    seq(m0, mb, [("Am", 2), ("Fmaj7", 2), ("G", 2), ("Am", 2), ("F", 2)],
        lambda s, t, d: (lstr(s, t, d, 0.11, 2200, att=0.7, rel=1.0, base=55, top=False),
                         lpad(s, t, d, 0.055, 1300, att=0.6),
                         lbass(s, t, d, 0.15, base=28, att=0.3, rel=0.5)))
    melody(m0, THEME_MIN, 0.15, "lead", send=0.5, until=mb)
    melody(m0, THEME_MIN, 0.13, "piano", tr=-12, vel=0.45, send=0.5, until=mb)
    seq(mb, m1, [("F", 2), ("C/E", 2), ("Dm7", 2), ("Gsus4", 2), ("G", 1)],
        lambda s, t, d: (lstr(s, t, d, 0.15, 2600, att=0.7, rel=1.0, base=55),
                         lstr(s, t, d, 0.075, 1500, att=0.9, rel=1.0, base=40, top=False),
                         lpad(s, t, d, 0.055, 1400, att=0.6),
                         lbass(s, t, d, 0.16, base=28, att=0.3, rel=0.5)))
    for b, m in ((0, 69), (2, 67), (4, 65), (5, 69), (6, 67), (7.5, 62)):
        pn(mb + b * BEAT, m, 0.2, 2.6, 0.55)
        pn(mb + b * BEAT, m - 12, 0.13, 2.6, 0.45)
    for b in range(0, int(round((m1 - m0) / BEAT)), 4):
        put(M, m0 + b * BEAT, tom(70, 0.8, 0.4), 0.17, send=0.5)

    # ========================================================== 5 joyo
    j0, j1 = span("joyo_story")
    jb, jc = card_start("joyo_story", 1), card_start("joyo_story", 2)
    for ci, (sym, nb) in enumerate((("C", 2), ("F", 2), ("G", 2), ("C", 2))):
        tc = j0 + ci * 2 * BEAT
        if tc >= jb - 1e-6:
            break
        tones = arp_tones(sym, 60)
        for q in range(int(nb * 2)):
            if q % 2 == 1:
                for m in tones[:3]:
                    put(M, tc + q * E8, marimba(m, 0.6), 0.085, (m - 66) / 20, send=0.25)
            else:
                put(M, tc + q * E8, marimba(tones[3 + (q // 2) % 2], 0.7), 0.1, 0.3, send=0.25)
                put(M, tc + q * E8, bass(bass_note(sym, 36) + (7 if q % 4 == 2 else 0), 0.12, 1.0, 0.004, 0.1),
                    0.17)
        lpad(sym, tc, nb * BEAT, 0.05, 2600, att=0.2, base=55, low=False)
    drums(j0, jb, k=0.18, cl=0.1, sh=0.06, half=True)
    # 30 investors say no: groove drains away, rejection stamps on a low dissonant dyad
    seq(jb, jc, [("Am", 2), ("Dm", 2), ("Am", 2), ("E", 2)],
        lambda s, t, d: (lpad(s, t, d, lerp(0.09, 0.075, (t - jb) / (jc - jb)),
                              lerp(1500, 700, (t - jb) / (jc - jb)), att=0.3, rel=0.9),
                         lbass(s, t, d, 0.1, att=0.05),
                         larp(s, t, d, lerp(0.07, 0.03, (t - jb) / (jc - jb)), "marimba", step=BEAT,
                              pat=(0, 2, 1, 3), vel=0.55, base=57)))
    r = rng()
    for i, b in enumerate((0.5, 1.5, 2.5, 3.5, 4.75, 6.0, 7.0)):
        ts = jb + b * BEAT
        put(S, ts, stamp(1.0), 0.16, r.uniform(-0.5, 0.5), send=0.2)
        put(M, ts, piano(40 - (i % 3), 1.2, 0.5), 0.1, -0.2, send=0.3)
        put(M, ts, piano(41 - (i % 3), 1.2, 0.5), 0.08, -0.1, send=0.3)
    # has to sell it, "like losing a child": low pads under a slowing music-box lullaby
    seq(jc, j1, [("Am", 2), ("F", 2), ("Dm", 2), ("E", 3)],
        lambda s, t, d: (lpad(s, t, d, 0.085, 650, att=0.8, rel=1.2, base=45),
                         lbass(s, t, d, 0.07, att=0.4, rel=0.7)))
    lull = (76, 72, 74, 71, 72, 69, 71, 68, 69)
    tl = 0.25
    for i, m in enumerate(lull):
        if jc + tl > j1 - 0.4:
            break
        put(M, jc + tl, celesta(m, 0.5 - 0.025 * i), 0.13, 0.15, send=0.6)
        tl += E8 * 1.6 * (1 + 0.09 * i)
    pn(jc + 0.05, 45, 0.2, 3.0, 0.45)
    pn(jc + 4 * BEAT, 38, 0.18, 3.0, 0.4)

    # ========================================================== 6 night -> the turn -> leave / rings
    n0, n1 = span("night_ponder")
    nT = n1 - n0
    put(M, n0, pad([33, 40, 45, 48], nT + 0.3, 380, 1.6, 1.0), 0.11, send=0.4)
    put(M, n0, bass(33, nT, 1.0, 1.5, 1.0), 0.07)
    for b in range(int(round(nT / BEAT))):
        put(S, n0 + b * BEAT + 0.05, tick(b % 2 == 0), 0.022, 0.4, send=0.35)
    for b, m, v in ((1.5, 72, 0.3), (4.0, 71, 0.28), (6.5, 69, 0.26), (8.5, 64, 0.24)):
        pn(n0 + b * BEAT, m, 0.13, 2.6, v, send=0.7)

    t0_, t1_ = span("think")
    rv0, rv1 = span("river")
    put(M, t0_, pad([41, 53, 57, 60, 64, 67], t1_ - t0_ + 0.4, 1000, 1.0, 0.6), 0.1, send=0.5)
    put(M, t0_, bass(41, t1_ - t0_, 1.0, 0.6, 0.4), 0.08)
    put(M, t0_, strings([81, 84], t1_ - t0_ + 0.3, 3500, 1.2, 0.5, 0.005), 0.025, send=0.6)
    r = rng()
    pent = (72, 74, 76, 79, 81, 84)
    for j in range(int((t1_ - t0_) / E8)):
        if r.random() < 0.45:
            put(M, t0_ + j * E8, celesta(int(r.choice(pent)), r.uniform(0.3, 0.55)), 0.09, r.uniform(-0.6, 0.6),
                send=0.6)
    idea = t0_ + 2 * BEAT
    put(S, idea, bell(mtof(84), 3.0), 0.12, 0.15, send=0.6)
    put(S, idea + 0.02, bell(mtof(91), 2.0), 0.05, -0.2, send=0.6)
    put(S, idea, sparkle(0.6, 12, 91, 0.6), 0.08, send=0.5)
    # river: flowing water, ascending sixteenth arpeggios and a crescendo into 顺势而为
    put(S, rv0 - 0.2, water(rv1 - rv0 + 0.6), 0.08, send=0.15)
    rT = rv1 - rv0
    seq(rv0, rv1, [("F", 2), ("G", 2), ("Am", 1), ("G/B", 1)],
        lambda s, t, d: (larp(s, t, d, lerp(0.07, 0.12, (t - rv0) / rT), "piano", step=E16,
                              pat=(0, 1, 2, 3, 4, 5, 4, 3), vel=0.55, nd=0.5, send=0.35),
                         lstr(s, t, d, lerp(0.07, 0.14, (t - rv0) / rT), 3000, att=0.5, rel=0.4, base=55),
                         lpad(s, t, d, 0.07, 1800, att=0.4, rel=0.4),
                         lbass(s, t, d, 0.14, base=29, att=0.05)))
    for b in range(int(round(rT / BEAT))):
        put(M, rv0 + b * BEAT, kick(), lerp(0.08, 0.2, b / 5), send=0.05)
    for j in range(8):
        put(M, rv1 - BEAT + j * E16 / 2, tom(90, 0.7, 0.3), lerp(0.06, 0.2, j / 7), send=0.3)
    put(S, rv1 - 2.0, rev_cymbal(2.0), 0.14, send=0.35)
    put(S, rv0 + 0.4, riser(rT - 0.4, 300, 7000, (200, 1000)), 0.09, send=0.3)

    sh0, sh1 = span("shunshi")
    put(S, sh0, impact(1.0, 0.15), 0.42, send=0.5)
    put(M, sh0, cymbal(3.0), 0.15, send=0.45)
    put(S, sh0 + 0.02, bell(mtof(84), 3.5), 0.08, 0.1, send=0.6)
    seq(sh0, sh1, [("C", 2), ("G/B", 2), ("Fmaj7", 2), ("C", 1)],
        lambda s, t, d: (lstr(s, t, d, 0.17, 3800, att=0.05, rel=0.9, base=55),
                         lstr(s, t, d, 0.08, 2000, att=0.1, rel=0.9, base=43, top=False),
                         lpad(s, t, d, 0.1, 3000, att=0.05, rel=0.9),
                         lbrass(s, t, d, 0.055, base=52, att=0.08, rel=0.5),
                         lbass(s, t, d, 0.18, base=28, att=0.01, rel=0.4)))
    melody(sh0, THEME_MAJ, 0.16, "lead", send=0.45, until=sh1)
    melody(sh0, THEME_MAJ, 0.12, "piano", vel=0.65, send=0.4, until=sh1)
    for m in (48, 55, 60, 64, 67, 72):
        pn(sh0, m, 0.13, 2.5, 0.75, send=0.35)
    for b in range(0, int(round((sh1 - sh0) / BEAT)), 2):
        put(M, sh0 + b * BEAT, kick(), 0.32, send=0.05)
        put(M, sh0 + b * BEAT, taiko(), 0.16, send=0.3)
    put(S, sh0 + 0.05, sparkle(1.2, 18, 88, 0.6), 0.07, send=0.45)

    lv0, lv1 = span("leave")
    seq(lv0, lv1, [("Am", 2), ("F", 2), ("C", 2), ("G", 3)],
        lambda s, t, d: (lstr(s, t, d, 0.1, 2000, att=0.7, rel=1.0, base=55),
                         lpad(s, t, d, 0.06, 1200, att=0.6, rel=1.0),
                         lbass(s, t, d, 0.1, att=0.3, rel=0.6)))
    melody(lv0 + BEAT, THEME_MIN, 0.17, "piano", vel=0.45, send=0.55, until=lv1)
    for i in range(6):
        put(S, lv0 + 0.4 + i * 0.52, footstep(0.7, 82 + 5 * (i % 2)), 0.1 * (1 - 0.1 * i),
            lerp(-0.1, 0.5, i / 5), send=0.25)
    put(S, lv0 + 0.3, wind(lv1 - lv0), 0.035, send=0.2)

    ri0, ri1 = span("rings")
    seq(ri0, ri1, [("Fmaj7", 3), ("C/E", 3)],
        lambda s, t, d: (lpad(s, t, d, 0.07, 1300, att=0.5, rel=1.0), lbass(s, t, d, 0.08, att=0.3)))
    ring_notes = (60, 62, 64, 67, 69, 67, 69, 72, 74, 72, 74, 76, 79, 76, 79, 81)
    for i in range(16):
        ti = 0.1 + i / 16 * (ri1 - ri0 - 0.6)
        put(M, ri0 + ti, marimba(ring_notes[i], 0.55 + 0.02 * i), 0.14, (i - 7.5) / 12, send=0.45)

    # ========================================================== 7 forty / blueprint / summit / IPO
    f0_, f1_ = span("forty")
    put(M, f0_, pad([45, 52, 57, 59, 64], f1_ - f0_ + 0.2, 1200, 0.8, 0.5), 0.11, send=0.5)
    pn(f0_ + 0.05, 69, 0.2, 3.0, 0.5, send=0.6)
    pn(f0_ + 0.05, 57, 0.14, 3.0, 0.45, send=0.6)
    for j in range(int(round((f1_ - f0_) / E8))):
        put(M, f0_ + j * E8, bass(33, 0.12, 1.0, 0.004, 0.06, 1.6), lerp(0.05, 0.13, j / 7), send=0.05)

    b0, b1 = span("blueprint")
    seq(b0, b1, [("F", 2), ("G", 2), ("Am", 2)],
        lambda s, t, d: (larp(s, t, d, 0.11, "marimba", pat=(0, 2, 4, 3, 1, 3, 5, 3), base=60, vel=0.65),
                         lpad(s, t, d, 0.08, 2000, att=0.2),
                         lstr(s, t, d, 0.07, 2600, att=0.3, base=60, top=False),
                         bass8(s, t, d, 0.13)))
    drums(b0, b1, k=0.26, ht=0.035, ramp=(0.7, 1.0))
    for i, tl in enumerate((0.3, 1.25, 2.3)):
        put(S, b0 + tl, pencil(0.55 + 0.1 * i), 0.05, -0.3 + 0.3 * i, send=0.1)
    r = rng()
    pent2 = (84, 86, 88, 91, 93, 96)
    bT = b1 - b0
    for j in range(int(round(bT / E16))):
        if j % 2 == 0 or r.random() < 0.4:
            m = pent2[min(5, int(r.integers(0, 3) + j * 4 / (bT / E16)))]
            put(S, b0 + 0.05 + j * E16, blip(m), 0.03, r.uniform(-0.6, 0.6), send=0.3)

    sm0, sm1 = span("summit")
    smT = sm1 - sm0
    seq(sm0, sm1, [("Am", 2), ("F", 2), ("C", 2), ("G", 3)],
        lambda s, t, d: (lstr(s, t, d, lerp(0.08, 0.15, (t - sm0) / smT), 2800, att=0.4, rel=0.8, base=55),
                         lpad(s, t, d, 0.075, 2000, att=0.3),
                         bass8(s, t, d, 0.15, octave=True),
                         larp(s, t, d, lerp(0.09, 0.13, (t - sm0) / smT), "piano", pat=(0, 2, 4, 2),
                              vel=0.6, nd=0.75)))
    drums(sm0, sm1 - BEAT, k=0.36, sn=0.18, ht=0.04, ramp=(0.6, 1.0))
    roll(sm1 - BEAT, sm1, 0.08, 0.3)
    put(S, sm0 + 1.0, riser(smT - 1.0, 350, 8000, (200, 1200)), 0.1, send=0.3)

    i0, i1 = span("ipo_gong")
    gong_t = i0 + 0.8
    put(M, i0, kick(), 0.45)
    put(M, i0, cymbal(2.6), 0.12, send=0.4)
    put(S, gong_t - 0.8, rev_cymbal(0.8), 0.08, send=0.3)
    put(S, gong_t, gong(96.0, 7.0), 0.55, 0.05, send=0.55)
    seq(i0, i1, [("C", 2), ("F", 2), ("G", 2), ("C", 2)],
        lambda s, t, d: (lstr(s, t, d, 0.15, 3600, att=0.15, rel=0.8, base=55),
                         lpad(s, t, d, 0.085, 2800, att=0.1, rel=0.8),
                         bass8(s, t, d, 0.16, octave=True),
                         larp(s, t, d, 0.11, "piano", pat=(0, 2, 4, 5, 4, 2), vel=0.7, nd=0.75)))
    for b, ch in ((0, "C"), (1.5, "C"), (2, "F"), (4, "G"), (5.5, "G"), (6, "C")):
        v = voicing(ch, 55)
        put(M, i0 + b * BEAT, brass(v + [v[0] + 12], BEAT * (0.4 if b % 1 else 0.9), 1.0, 0.012, 0.25), 0.1,
            send=0.3)
    drums(i0 + 2 * BEAT, i1, k=0.4, cl=0.15, ht=0.05, ramp=(0.7, 1.0))
    nc = ns(crash_drop() - gong_t)
    cx = np.linspace(0, 1, nc)
    cenv = np.clip(cx / 0.3, 0, 1) ** 1.5
    put(S, gong_t + 0.2, crowd(nc / SR) * cenv, 0.07, send=0.3)
    put(S, gong_t + 0.1, sparkle(2.0, 26, 88, 0.7), 0.07, send=0.45)

    # ========================================================== crash: the music stops at the break
    x0, x1 = span("crash")
    drop = crash_drop()
    put(M, x0, strings([72, 76, 79, 83, 84], drop - x0 + 0.2, 3600, 0.05, 0.2, 0.006), 0.09, send=0.4)
    put(M, x0, pad([48, 60, 67], drop - x0 + 0.2, 1500, 0.05, 0.2), 0.08, send=0.3)
    for j in range(int(round((drop - x0) / E8))):
        put(S, x0 + j * E8, tick(j % 2 == 0), 0.05, 0.3, send=0.15)
        put(M, x0 + j * E8, bass(36, 0.1, 1.0, 0.004, 0.05, 1.5), 0.1, send=0.05)
    put(S, drop, impact(1.7, 0.4), 0.62, send=0.55)
    put(S, drop, pitch_drop(1.9), 0.13, send=0.45)
    put(S, drop, thud(1.0, 40), 0.3, send=0.3)

    # ========================================================== doubt: near silence (quiet bus)
    d0, d1 = span("doubt")
    dT = d1 - d0
    put(Q, d0, pad([33, 45], dT - 0.5, 320, 1.4, 0.45, cents=4.0), 0.09, send=0.4)
    put(Q, d0 - 0.2, rain(dT), 0.018, send=0.1)
    for b in range(1, int(round(dT / BEAT)) - 1, 2):
        put(Q, d0 + b * BEAT, heart(), 0.32, send=0.15)
        put(Q, d0 + b * BEAT + 0.14, heart(), 0.2, send=0.15)
    pn(d1 - 1.4, 76, 0.1, 1.0, 0.3, send=0.6, bus=Q)

    # ========================================================== car -> all in -> launch: climax
    k0_, k1_ = span("car")
    on = k0_ + 0.62 * (k1_ - k0_)
    put(S, k0_, impact(1.6, 0.5), 0.7, send=0.5)
    put(M, k0_, kick(), 0.6)
    put(M, k0_, taiko(), 0.4, send=0.3)
    put(M, k0_, cymbal(3.0), 0.15, send=0.4)
    put(M, k0_, brass(voicing("Am", 52) + [45], BEAT * 1.5, 1.0, 0.008, 0.5), 0.14, send=0.35)
    seq(k0_, k1_, [("Am", 2), ("F", 2), ("G", 2)],
        lambda s, t, d: (lstr(s, t, d, lerp(0.12, 0.18, (t - k0_) / (k1_ - k0_)), 3400, att=0.05, rel=0.5),
                         lpad(s, t, d, 0.09, 2600, att=0.05, rel=0.5),
                         bass8(s, t, d, 0.18, octave=True)))
    for j in range(int(round((k1_ - k0_) / E16))):
        x = j / ((k1_ - k0_) / E16)
        m = (57, 64, 69, 64)[j % 4] if x < 2 / 6 else ((53, 60, 65, 60) if x < 4 / 6 else (55, 62, 67, 62))[j % 4]
        put(M, k0_ + j * E16, strings([m], 0.09, 3000, 0.004, 0.06, 0.0), lerp(0.05, 0.1, x), 0.1, send=0.15)
    drums(k0_ + BEAT, k1_ - 2 * BEAT, k=0.45, ht=0.05)
    for b in (2, 3):
        put(M, k0_ + b * BEAT, taiko(), 0.28, send=0.3)
    roll(k1_ - 2 * BEAT, k1_, 0.1, 0.38, div=4)
    for j in range(4):
        put(M, k1_ - 2 * BEAT + j * BEAT / 2, taiko(), lerp(0.22, 0.4, j / 3), send=0.3)
    put(S, on, headlights(), 0.16, 0.25, send=0.4)
    put(S, on, flash_shimmer(), 0.08, send=0.4)
    put(S, k1_ - 1.6, rev_cymbal(1.6), 0.14, send=0.35)

    ba0, ba1 = span("bubble_allin")
    put(M, ba0, cymbal(2.8), 0.17, send=0.4)
    put(M, ba0, taiko(), 0.35, send=0.3)
    seq(ba0, ba1, [("F", 2), ("G", 2), ("Em7", 2), ("Am", 1), ("G", 1)],
        lambda s, t, d: (lstr(s, t, d, 0.2, 4200, att=0.04, rel=0.4, base=55),
                         lstr(s, t, d, 0.1, 2200, att=0.05, rel=0.4, base=40, top=False),
                         lpad(s, t, d, 0.1, 3000, att=0.02, rel=0.4),
                         lbrass(s, t, d, 0.075, base=52, att=0.03, rel=0.3),
                         bass8(s, t, d, 0.2, base=28, octave=True),
                         larp(s, t, d, 0.12, "piano", pat=(0, 2, 4, 5, 6, 5, 4, 2), vel=0.8, nd=0.75)))
    melody(ba0, COUNTER, 0.17, "lead", send=0.4, until=ba1)
    drums(ba0, ba1 - BEAT, k=0.55, sn=0.4, ht=0.07, cl=0.15)
    roll(ba1 - BEAT, ba1, 0.12, 0.4)
    tomfill(ba1 - BEAT, 0.28, (150, 120, 100, 80))
    put(S, ba1 - 1.5, rev_cymbal(1.5), 0.18, send=0.4)

    la0, la1 = span("launch")
    rev = la0 + 0.12 * (la1 - la0)
    put(S, la0, impact(1.5, 0.5), 0.7, send=0.55)
    put(M, la0, cymbal(3.5), 0.19, send=0.45)
    put(M, la0, taiko(), 0.4, send=0.3)
    put(M, rev, cymbal(3.0), 0.09, 0.4, send=0.45)
    put(S, rev - 0.3, whoosh(1.1, 200, 2400), 0.09, send=0.3)
    seq(la0, la1, [("C", 2), ("Fmaj7", 2), ("G", 2), ("C", 1)],
        lambda s, t, d: (lstr(s, t, d, 0.21, 4500, att=0.03, rel=0.9, base=55),
                         lstr(s, t, d, 0.1, 2400, att=0.03, rel=0.9, base=40, top=False),
                         lpad(s, t, d, 0.11, 3400, att=0.02, rel=0.9),
                         lbrass(s, t, d, 0.08, base=52, att=0.03, rel=0.5),
                         bass8(s, t, d, 0.21, base=28, octave=True),
                         larp(s, t, d, 0.12, "piano", pat=(0, 2, 4, 6, 5, 4, 2, 1), vel=0.85, nd=0.75)))
    melody(la0, THEME_MAJ, 0.19, "lead", tr=12, send=0.45, until=la1 + BEAT)
    melody(la0, THEME_MAJ, 0.13, "brass", vel=1.0, send=0.35, until=la1)
    melody(la0, THEME_MAJ, 0.11, "piano", vel=0.8, send=0.4, until=la1)
    for m in (48, 55, 60, 64, 67, 72):
        pn(la0, m, 0.13, 2.5, 0.9, send=0.35)
    drums(la0, la1 - BEAT, k=0.58, sn=0.42, ht=0.08, cl=0.16, open_hat=1)
    put(M, la1 - BEAT, kick(), 0.5)
    put(M, la1 - BEAT, taiko(), 0.35, send=0.35)
    put(M, la1 - BEAT, cymbal(3.2), 0.13, send=0.5)
    put(S, rev, sparkle(2.4, 40, 88, 0.8), 0.1, send=0.45)
    nc = ns(la1 - rev + 0.8)
    cx = np.linspace(0, 1, nc)
    cenv = np.clip(cx / 0.25, 0, 1) ** 1.5 * (1 - 0.5 * cx) * np.cos(0.5 * math.pi * np.clip((cx - 0.75) / 0.25, 0, 1))
    put(S, rev, crowd(nc / SR) * cenv, 0.1, send=0.35)

    # ========================================================== 8 path / sunrise: resolve and close
    pa0, pa1 = span("path")
    seq(pa0, pa1, [("F", 2), ("G", 2), ("Em7", 2), ("Am", 2)],
        lambda s, t, d: (lstr(s, t, d, 0.1, 2600, att=0.6, rel=1.0, base=55),
                         lpad(s, t, d, 0.06, 1600, att=0.5, rel=1.0),
                         lbass(s, t, d, 0.12, base=28, att=0.2, rel=0.6),
                         larp(s, t, d, 0.11, "piano", step=E8, pat=(0, 1, 2, 3, 4, 3, 2, 1), vel=0.5, nd=1.5)))
    for b, m in ((0.5, 81), (2.5, 79), (4.5, 79), (6.0, 76)):
        pn(pa0 + b * BEAT, m, 0.12, 2.5, 0.45, send=0.6)

    su0, su1 = span("sunrise")
    fin = su0 + 4 * BEAT
    seq(su0, fin, [("Fmaj7", 2), ("G", 2)],
        lambda s, t, d: (lstr(s, t, d, 0.1, 2600, att=0.4, rel=0.8, base=55),
                         lpad(s, t, d, 0.065, 1600, att=0.4, rel=0.8),
                         lbass(s, t, d, 0.12, base=28, att=0.1),
                         larp(s, t, d, 0.1, "piano", step=E8, pat=(0, 1, 2, 3), vel=0.5, nd=1.5)))
    melody(su0, ((2, 74, 1.5), (3.5, 71, 0.5), (4, 72, 4)), 0.17, "piano", vel=0.5, send=0.6)
    hold = su1 - fin - 1.6
    put(M, fin, strings([48, 55, 60, 64, 67, 72, 76], hold, 2600, 0.5, 1.6, 0.003), 0.13, send=0.55)
    put(M, fin, pad([36, 48, 55, 62, 64, 67], hold, 1500, 0.5, 1.6), 0.08, send=0.55)
    put(M, fin, bass(36, hold, 1.0, 0.3, 1.6), 0.11)
    for k_, m in enumerate((48, 55, 60, 64, 67)):
        pn(fin + k_ * 0.06, m, 0.14, 4.0, 0.5, send=0.65)
    pn(fin + 2 * BEAT, 79, 0.1, 3.0, 0.35, send=0.75)
    put(S, fin, bell(mtof(84), 4.0), 0.04, 0.2, send=0.7)

    # ========================================================== transitions / bubbles
    silent = {"doubt", "black", "car"}
    for it in SHOTS:
        st = it["start"]
        if st < 0.2 or it["scene"] in silent:
            continue
        tr = it["trans"]
        if tr in ("wipe", "push", "iris"):
            put(S, st - 0.5 * 0.55, whoosh(0.5), 0.07, send=0.3)
            put(S, st - 0.04, page_flip(), 0.045, 0.3, send=0.15)
        elif tr in ("fade", "dip"):
            put(S, st - 0.6 * 0.55, whoosh(0.6, 350, 2400), 0.04, send=0.3)
        elif tr == "flash":
            put(S, st, flash_shimmer(), 0.11, send=0.45)
        if it["kind"] == "bubble":
            put(S, st + 0.3, pop(), 0.28, 0.1, send=0.25)

    return dict(light_times=light_times, flips=flips, gong=gong_t, drop=drop, hit=hit, on=on)


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


def ramp_env(points):
    """Piecewise gain envelope from (time, gain) points with cos^2-shaped segments."""
    e = np.ones(N)
    for (ta, ga), (tb, gb) in zip(points[:-1], points[1:]):
        ia, ib = int(round(ta * SR)), int(round(tb * SR))
        if ib <= ia:
            continue
        x = np.linspace(0, 1, ib - ia, endpoint=False)
        e[ia:ib] = ga + (gb - ga) * np.sin(0.5 * math.pi * x) ** 2
    ia = int(round(points[-1][0] * SR))
    e[ia:] = points[-1][1]
    ia = int(round(points[0][0] * SR))
    e[:ia] = points[0][1]
    return e


def envelopes():
    """Music bus: hard stop at the crash, back at the car.  Everything: fade to silence
    into the black gap, silent through it, final fade to zero at TOTAL."""
    drop = crash_drop()
    d1 = span("doubt")[1]
    b0, b1 = span("black")
    car0 = span("car")[0]
    env_m = ramp_env([(0.0, 1.0), (drop, 1.0), (drop + 0.03, 0.0), (car0, 0.0), (car0 + 0.003, 1.0)])
    env_g = ramp_env([(0.0, 0.0), (0.005, 1.0), (d1 - 0.6, 1.0), (b0, 0.0), (b1, 0.0), (b1 + 0.003, 1.0),
                      (TOTAL - 2.4, 1.0), (TOTAL - 1.0 / SR, 0.0)])
    return env_m, env_g


_KW = (np.array([[1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585],
                 [1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621]]))


def _kblocks(x):
    y = signal.sosfilt(_KW, x, axis=-1)
    blk, hop = ns(0.4), ns(0.1)
    p = np.sum(y ** 2, axis=0)
    cs = np.concatenate([[0.0], np.cumsum(p)])
    starts = np.arange(0, x.shape[1] - blk + 1, hop)
    return (cs[starts + blk] - cs[starts]) / blk


def lufs(x):
    """BS.1770-4 integrated loudness at 48 kHz (K-weighting, 400 ms blocks, 75 %
    overlap, -70 LUFS absolute and -10 LU relative gates)."""
    z = _kblocks(x)
    lk = -0.691 + 10 * np.log10(z + 1e-12)
    g = z[lk > -70]
    if not len(g):
        return -70.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g2 = z[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(g2.mean()))


def os_peak(x, k=4):
    """Per-sample true-peak envelope: max |x| over a k-times oversampled signal."""
    n = x.shape[1]
    out = np.empty(n)
    C, P = 1 << 19, 64
    for a0 in range(0, n, C):
        a1 = min(n, a0 + C)
        lo, hi = max(0, a0 - P), min(n, a1 + P)
        up = signal.resample_poly(x[:, lo:hi], k, 1, axis=1)
        pk = np.abs(up).max(axis=0).reshape(-1, k).max(axis=1)
        out[a0:a1] = pk[a0 - lo: a1 - lo]
    return np.maximum(out, np.abs(x).max(axis=0))


def compress(x, thr_db=-24.0, ratio=2.0, att=0.015, rel=0.3, knee=6.0):
    """Feed-forward RMS compressor with soft knee; gain computed at a 1 kHz control
    rate with separate attack/release smoothing."""
    hop = SR // 1000
    p = uniform_filter1d(np.mean(x ** 2, axis=0), ns(0.03))
    lvl = 10 * np.log10(p[::hop] + 1e-12)
    over = lvl - thr_db
    s = 1 - 1 / ratio
    gr = np.where(over <= -knee / 2, 0.0,
                  np.where(over >= knee / 2, over * s, s * (over + knee / 2) ** 2 / (2 * knee)))
    aa, ar = math.exp(-1 / (att * 1000)), math.exp(-1 / (rel * 1000))
    sm = np.empty_like(gr)
    v = 0.0
    for i, g in enumerate(gr.tolist()):
        v = aa * v + (1 - aa) * g if g > v else ar * v + (1 - ar) * g
        sm[i] = v
    gain = 10 ** (-sm / 20)
    return x * np.interp(np.arange(x.shape[1]), np.arange(len(gain)) * hop, gain)


def limiter_gain(pk, ceil, hold=0.012):
    """Look-ahead brickwall gain: the moving average of a min-hold never exceeds the
    gain needed at any sample inside the hold window."""
    g = np.minimum(1.0, ceil / np.maximum(pk, 1e-12))
    H = ns(hold)
    g = minimum_filter1d(g, 2 * H + 1)
    return uniform_filter1d(g, H)


def master(mix, env):
    mix = hp(mix, 30, 2) * env
    mix = mix * 10 ** ((-20.0 - lufs(mix)) / 20)
    mix = compress(mix, -25.0, 2.2, 0.012, 0.32) * env
    ceil = 10 ** (CEIL_DBTP / 20)
    pk = os_peak(mix)
    g = 10 ** ((TARGET_LUFS - lufs(mix)) / 20)
    for _ in range(8):
        G = g * limiter_gain(pk * g, ceil)
        out = mix * G
        diff = TARGET_LUFS - lufs(out)
        if abs(diff) < 0.03:
            break
        g *= 10 ** (diff / 20)
    for _ in range(3):
        tp = os_peak(out)
        if tp.max() <= ceil:
            break
        out = out * limiter_gain(tp, ceil * 0.995)
    out *= env
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


def report(out, marks=None):
    """Per-shot loudness (K-weighted, ungated) plus the black-gap RMS."""
    y = signal.sosfilt(_KW, out, axis=-1)
    p = np.sum(y ** 2, axis=0)
    for s in SHOTS:
        a, b = int(s["start"] * SR), int(s["end"] * SR)
        l = -0.691 + 10 * np.log10(p[a:b].mean() + 1e-20)
        print(f"  {s['start']:7.2f} {s['end']:7.2f}  {s['scene']:16s} {l:7.1f} LUFS")
    b0, b1 = span("black")
    seg = out[:, int(b0 * SR):int(b1 * SR)]
    rms = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-12)
    print(f"  black gap {b0:.2f}-{b1:.2f}: RMS {rms:.1f} dBFS, peak {20 * np.log10(np.abs(seg).max() + 1e-12):.1f} dBFS")
    tp = 20 * np.log10(os_peak(out).max())
    print(f"  integrated {lufs(out):.2f} LUFS, true peak {tp:.2f} dBTP")
    if marks:
        print("  marks:", {k: (round(v, 3) if isinstance(v, float) else [round(q, 2) for q in v])
                           for k, v in marks.items()})


def build(path: str, verbose: bool = False) -> None:
    t_start = time.time()
    _seed[0] = 0
    BUS.clear()
    for k in BUSES:
        BUS[k] = np.zeros((2, N), dtype=np.float32)
        BUS["rev_" + k] = np.zeros((2, N), dtype=np.float32)
    marks = compose()
    ir = make_ir(2.6)
    env_m, env_g = envelopes()
    mix = np.zeros((2, N))
    for k, g in (("mus", 1.0), ("sfx", 0.9), ("quiet", 1.0)):
        wet = np.stack([signal.oaconvolve(BUS["rev_" + k][c], ir[c])[:N] for c in range(2)])
        stem = (BUS[k] + wet * 0.55) * g
        if k == "mus":
            stem *= env_m
        mix += stem
        del wet, stem
        BUS[k] = BUS["rev_" + k] = None
    if not np.all(np.isfinite(mix)):
        raise RuntimeError("non-finite samples in mix")
    out = master(mix, env_g)
    del mix
    write_wav(path, out)
    BUS.clear()
    _piano.cache_clear()
    _marimba.cache_clear()
    print(f"audio: wrote {path} ({out.shape[1] / SR:.3f}s, {lufs(out):.2f} LUFS) in {time.time() - t_start:.1f}s")
    if verbose:
        report(out, marks)


if __name__ == "__main__":
    build("build/audio.wav", verbose=True)
