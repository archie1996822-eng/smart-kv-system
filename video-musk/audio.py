"""Procedural score + sound design (no samples, no third-party music: original and
free for commercial use). Writes build/audio_<name>.wav, 48 kHz stereo.

Opening cue, following the action:
  climb   – engine growl rising in pitch, riser underneath
  apex    – everything pulls away to one suspended high note ("the stop")
  jets    – cold-gas hiss (high-passed noise), no rumble/roar
  flip    – whoosh sweep
  drop    – falling whistle, tension
  landing – sub boom + body clank, then the beat comes in under the hook card
"""
import math
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 48000
BPM = 100
BEAT = 60 / BPM


def t_axis(n):
    return np.arange(n) / SR


def env_adsr(n, a, d, s, r, total=None):
    total = total or n / SR
    t = t_axis(n)
    e = np.where(t < a, t / max(a, 1e-4), 1.0)
    e = np.where((t >= a) & (t < a + d), 1 - (1 - s) * (t - a) / max(d, 1e-4), e)
    e = np.where(t >= a + d, s, e)
    rel0 = total - r
    e = np.where(t >= rel0, e * np.clip((total - t) / max(r, 1e-4), 0, 1), e)
    return e


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo / (SR / 2), hi / (SR / 2)], btype="band", output="sos")
    return sosfilt(sos, x)


def lp(x, f, order=2):
    sos = butter(order, f / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x)


def hp(x, f, order=2):
    sos = butter(order, f / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x)


def noise(n, seed=0):
    return np.random.default_rng(seed).normal(0, 1, n)


def osc(freq, n, kind="sine", phase=0.0):
    """freq may be array (glide)."""
    f = np.broadcast_to(np.asarray(freq, float), (n,))
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if kind == "sine":
        return np.sin(ph)
    if kind == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    if kind == "square":
        return np.sign(np.sin(ph))
    if kind == "tri":
        return 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1.0) - 1) - 1
    raise ValueError(kind)


class Mix:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.L = np.zeros(self.n)
        self.R = np.zeros(self.n)

    def add(self, sig, at, gain=1.0, pan=0.0):
        i0 = int(at * SR)
        if i0 >= self.n:
            return
        sig = sig[: self.n - i0]
        gl = gain * math.cos((pan + 1) * math.pi / 4)
        gr = gain * math.sin((pan + 1) * math.pi / 4)
        self.L[i0:i0 + len(sig)] += sig * gl
        self.R[i0:i0 + len(sig)] += sig * gr

    def out(self):
        st = np.stack([self.L, self.R], 1)
        peak = np.abs(st).max() + 1e-9
        st = st / peak * 0.89
        return st


# ------------------------------------------------------------ instruments

def kick(dur=0.45):
    n = int(dur * SR)
    t = t_axis(n)
    f = 45 + 110 * np.exp(-t * 32)
    s = osc(f, n) * np.exp(-t * 7.5)
    s += 0.25 * lp(noise(n, 3), 2500) * np.exp(-t * 60)
    return s


def snare(dur=0.3, seed=5):
    n = int(dur * SR)
    t = t_axis(n)
    s = 0.6 * bp(noise(n, seed), 1200, 7000) * np.exp(-t * 18)
    s += 0.4 * osc(190, n) * np.exp(-t * 25)
    return s


def hat(dur=0.08, seed=9):
    n = int(dur * SR)
    t = t_axis(n)
    return hp(noise(n, seed), 7000) * np.exp(-t * 60)


def bass_note(freq, dur):
    n = int(dur * SR)
    s = 0.7 * osc(freq, n, "saw") + 0.5 * osc(freq / 2, n, "sine")
    s = lp(s, 380)
    return s * env_adsr(n, 0.01, 0.12, 0.7, 0.08)


def pad(freqs, dur, bright=1800, seed=0):
    n = int(dur * SR)
    s = np.zeros(n)
    for k, f in enumerate(freqs):
        for det in (-0.004, 0.0, 0.005):
            s += osc(f * (1 + det), n, "saw", phase=k + det * 100)
    s = lp(s, bright) / (len(freqs) * 3)
    return s * env_adsr(n, 0.25, 0.3, 0.8, 0.5)


def riser(dur, f0=200, f1=2400, seed=1):
    n = int(dur * SR)
    t = t_axis(n)
    u = t / dur
    nz = noise(n, seed)
    out = np.zeros(n)
    # sweep a band through the noise in blocks
    blocks = 24
    for b in range(blocks):
        a0, a1 = int(n * b / blocks), int(n * (b + 1) / blocks)
        fc = f0 * (f1 / f0) ** ((b + 0.5) / blocks)
        seg_ = bp(nz[max(0, a0 - 2000):a1], fc * 0.7, min(fc * 1.4, SR / 2 - 100))[-(a1 - a0):]
        out[a0:a1] = seg_
    tone = osc(f0 * 0.5 * (f1 / f0) ** (u * 0.6), n, "saw")
    return (out * 0.8 + 0.15 * lp(tone, 1500)) * u ** 1.5


def engine(dur, f0, f1, seed=2):
    n = int(dur * SR)
    t = t_axis(n)
    u = t / dur
    f = f0 * (f1 / f0) ** (u ** 0.8)
    s = osc(f, n, "saw") + 0.5 * osc(f * 2.01, n, "saw") + 0.3 * osc(f * 0.5, n, "square")
    blocks = 16
    outb = np.zeros(n)
    for b in range(blocks):
        a0, a1 = int(n * b / blocks), int(n * (b + 1) / blocks)
        outb[a0:a1] = lp(s[max(0, a0 - 2000):a1], 900 + 1400 * (b + 0.5) / blocks)[-(a1 - a0):]
    s = outb
    grit = bp(noise(n, seed), 150, 900) * 0.35
    am = 1 + 0.25 * np.sin(2 * np.pi * np.cumsum(f * 0.25) / SR)
    return (s * 0.6 + grit) * am


def hiss(dur, seed=4, flutter=7.0):
    """Cold-gas jet: bright, airy, no low end."""
    n = int(dur * SR)
    t = t_axis(n)
    s = hp(noise(n, seed), 1800, 4) * 0.8 + bp(noise(n, seed + 1), 4000, 11000) * 0.5
    s *= 1 + 0.18 * np.sin(2 * np.pi * flutter * t) + 0.1 * np.sin(2 * np.pi * 23 * t)
    return s


def whoosh(dur, seed=6, up=True):
    n = int(dur * SR)
    t = t_axis(n)
    u = t / dur
    nz = noise(n, seed)
    out = np.zeros(n)
    blocks = 20
    for b in range(blocks):
        a0, a1 = int(n * b / blocks), int(n * (b + 1) / blocks)
        x = (b + 0.5) / blocks
        fc = 300 + 2600 * (math.sin(math.pi * x) if up else 1 - x)
        out[a0:a1] = bp(nz[max(0, a0 - 2000):a1], fc * 0.6, fc * 1.6)[-(a1 - a0):]
    return out * np.sin(np.pi * u) ** 1.5


def impact(dur=1.6, seed=8):
    n = int(dur * SR)
    t = t_axis(n)
    boom = osc(32 + 60 * np.exp(-t * 9), n) * np.exp(-t * 3.2)
    crack = bp(noise(n, seed), 500, 6000) * np.exp(-t * 28)
    clank = sum(osc(f, n) * np.exp(-t * d) for f, d in ((310, 14), (523, 18), (787, 22), (1290, 30))) * 0.25
    body = lp(noise(n, seed + 1), 400) * np.exp(-t * 6) * 0.6
    return boom * 1.2 + crack * 0.7 + clank + body


def tick(dur=0.05):
    n = int(dur * SR)
    t = t_axis(n)
    return osc(2400, n) * np.exp(-t * 120)


def bell(freq, dur):
    n = int(dur * SR)
    t = t_axis(n)
    s = sum(a * osc(freq * r, n) * np.exp(-t * dcy) for r, a, dcy in ((1, 1, 1.6), (2.76, 0.4, 3), (5.4, 0.2, 5)))
    return s * np.minimum(1, t / 0.004)


# ------------------------------------------------------------ cues

def cue_open(m, t_launch, t_jet, t_apex, t_flip0, t_flip1, t_land, tail=1.4):
    # climb: engine already roaring on frame 1
    m.add(engine(t_launch + 0.2, 70, 210), 0.0, 0.55)
    m.add(riser(t_apex + 0.05, 180, 3200), 0.0, 0.35)
    m.add(lp(noise(int((t_launch + 0.1) * SR), 12), 500) * np.linspace(0.6, 1.0, int((t_launch + 0.1) * SR)), 0, 0.35)
    # driving pulse under the climb (16ths), cut at the apex
    for k in range(int(t_apex / (BEAT / 4))):
        tt = k * BEAT / 4
        m.add(bass_note(55 * (1.0 if k % 8 < 6 else 1.335), BEAT / 4 * 0.9), tt, 0.32)
        if k % 4 == 0:
            m.add(kick(), tt, 0.7)
        m.add(hat(), tt, 0.12, pan=0.3)
    m.add(whoosh(0.5, 21), t_launch - 0.15, 0.45, pan=0.2)
    # apex: the stop – one suspended high note + tick
    m.add(tick(), t_apex, 0.4)
    m.add(bell(1318.5, 2.2), t_apex, 0.18, pan=-0.2)
    m.add(pad([659.3, 987.8, 1318.5], t_flip1 - t_apex + 0.4, bright=2600), t_apex, 0.12)
    # cold-gas jets: burst then steady hiss, cut on the flip
    jet_dur = t_flip1 - t_jet + 0.25
    n = int(jet_dur * SR)
    e = np.ones(n)
    tt = t_axis(n)
    e *= np.minimum(1, tt / 0.03)
    e *= np.where(tt < 0.15, 1.5 - tt / 0.15 * 0.5, 1.0)
    e *= np.clip((jet_dur - tt) / 0.5, 0, 1)
    e *= np.where(tt > t_flip0 - t_jet, 0.75, 1.0)
    m.add(hiss(jet_dur, 4) * e, t_jet, 0.42, pan=-0.15)
    m.add(hiss(jet_dur, 14, 9.0) * e, t_jet, 0.42, pan=0.15)
    # flip
    m.add(whoosh(t_flip1 - t_flip0 + 0.1, 31), t_flip0, 0.6)
    # drop: falling whistle
    nd = int((t_land - t_flip1) * SR)
    f = np.linspace(1500, 380, nd)
    m.add(osc(f, nd) * np.linspace(0.0, 1.0, nd) ** 2 * 0.5, t_flip1, 0.18)
    m.add(riser(t_land - t_flip1, 300, 2500, 41), t_flip1, 0.22)
    # landing
    m.add(impact(), t_land, 0.95)
    m.add(pad([55, 110, 164.8, 220], 2.0, bright=900), t_land, 0.35)
    # the hook beat comes in under the first card
    t0 = t_land
    for b in range(int(tail / BEAT * 2) + 1):
        tt = t0 + b * BEAT / 2
        if b % 2 == 0:
            m.add(kick(), tt, 0.8)
        if b % 4 == 2:
            m.add(snare(), tt, 0.35)
        m.add(hat(seed=b), tt + BEAT / 4, 0.1, pan=0.25)
        m.add(bass_note(55 if b < 4 else 49, BEAT / 2 * 0.95), tt, 0.35)


def build(name, dur, **kw):
    m = Mix(dur)
    if name == "open":
        cue_open(m, **kw)
    elif name == "turn":
        m.add(pad([220, 277.2, 329.6], dur, bright=1200), 0, 0.3)
        for b in range(int(dur / BEAT)):
            m.add(bell([440, 554.4, 659.3, 554.4][b % 4], 1.5), b * BEAT, 0.08)
    st = m.out()
    # short fades at the edges
    f = int(0.02 * SR)
    st[:f] *= np.linspace(0, 1, f)[:, None]
    st[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))[:, None]
    path = f"build/audio_{name}.wav"
    wavfile.write(path, SR, (st * 32767).astype(np.int16))
    return path


if __name__ == "__main__":
    print(build(sys.argv[1], float(sys.argv[2])))
