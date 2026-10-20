"""Full film re-timed to the song 若如初见 (wenever): music/ruoruchujian.mp3, 112.3 BPM, 4/4.

The animation is unchanged: frame(t) renders b_full.frame(warp(t)), where warp is piecewise linear between
knots. Key cards sit on the song's section starts, the other cards on the nearest beat, and the opening
stunt's launch / hover / flip / landing on beats as well.

  python3 b_music.py --analyze   # beat tracking (librosa) -> ../music/beats.json
  python3 b_music.py             # print the re-timed card table
  python3 b_music.py --audio     # song (cut + fade) + sound effects -> ../build/audio_music.wav
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b_full as B  # noqa: E402

SONG = os.path.join(HERE, "..", "music", "ruoruchujian.mp3")
BEATS_JSON = os.path.join(HERE, "..", "music", "beats.json")


def analyze():
    import librosa
    y, sr = librosa.load(SONG, sr=22050, mono=True)
    _, bf = librosa.beat.beat_track(y=y, sr=sr, hop_length=256)
    beats = librosa.frames_to_time(bf, sr=sr, hop_length=256)
    with open(BEATS_JSON, "w") as f:
        json.dump({"bpm": round(60 / float(np.median(np.diff(beats))), 2), "downbeat_phase": 0,
                   "beats": [round(float(b), 4) for b in beats]}, f)


def load_beats():
    with open(BEATS_JSON) as f:
        return np.array(json.load(f)["beats"])


if __name__ == "__main__" and "--analyze" in sys.argv:
    analyze()
BEATS = load_beats()


def bar(k):
    return float(BEATS[4 * k])


# old time -> new time, fixed by the song's structure
FIXED = {
    0.0: 0.0,
    1.0: float(BEATS[1]),                       # launch onto the ramp
    2.3: float(BEATS[3] + BEATS[4]) / 2,        # hover starts on the off-beat
    3.9: float(BEATS[7]),                       # flip
    5.5: float(BEATS[10]),                      # landing
    B.START[0]: 0.2,
    B.START[6]: bar(8),                         # 二零零八年。 – the band comes in
    B.START[14]: bar(16),                       # 他没有。 – next 8-bar phrase
    B.START[20]: bar(24),                       # section 4
    B.START[26]: bar(32),                       # section 5
    B.START[31]: bar(40),                       # 十八年后。 – quiet interlude
    B.START[37]: bar(48),                       # 是继续往前押。 – the song lifts again
}
FIXED[B.DURATION] = float(BEATS[4 * 48 + 9])   # tail, ~2 bars after the last card


def build_knots():
    old = sorted(set(FIXED) | set(B.START))
    fo = sorted(FIXED)
    fn = [FIXED[k] for k in fo]
    new = []
    for t in old:
        if t in FIXED:
            new.append(FIXED[t])
            continue
        v = float(np.interp(t, fo, fn))
        new.append(float(BEATS[np.argmin(np.abs(BEATS - v))]))
    return np.array(old), np.array(new)


OLD_K, NEW_K = build_knots()
assert np.all(np.diff(NEW_K) > 0.1), list(zip(OLD_K.round(2), NEW_K.round(2)))
DURATION = float(NEW_K[-1])


def warp(t):
    """new (song) time -> old (animation) time"""
    return float(np.interp(t, NEW_K, OLD_K))


def unwarp(t):
    """old (animation) time -> new (song) time"""
    return float(np.interp(t, OLD_K, NEW_K))


START = [unwarp(t) for t in B.START]
END = [unwarp(t) for t in B.END]
assert min(e - s for s, e in zip(START, END)) > 1.4, "a card became too short to read"


def frame(t):
    return B.frame(min(warp(t), B.DURATION - 1e-3))


# ------------------------------------------------------------------ audio
def sfx():
    """Sound effects only (the song is the score), placed at re-timed moments."""
    sys.path.insert(0, os.path.join(HERE, ".."))
    import audio as A
    import audio_full as AF
    SR = A.SR
    m = A.Mix(DURATION + 1.0)
    u = unwarp
    S, E = B.START, B.END

    def at(i, frac=0.0):
        return u(S[i] + frac * (E[i] - S[i]))

    # opening stunt
    t_launch, t_jet, t_flip0, t_flip1, t_land = u(1.0), u(2.25), u(3.9), u(5.1), u(5.5)
    m.add(A.engine(t_launch + 0.3, 70, 210) * np.linspace(1, 0.3, int((t_launch + 0.3) * SR)), 0.0, 0.3)
    m.add(A.whoosh(0.5, 21), t_launch - 0.15, 0.35, pan=0.2)
    jd = t_flip1 - t_jet + 0.25
    n = int(jd * SR)
    tt = A.t_axis(n)
    e = np.minimum(1, tt / 0.03) * np.where(tt < 0.15, 1.5 - tt / 0.15 * 0.5, 1.0) * np.clip((jd - tt) / 0.5, 0, 1)
    m.add(A.hiss(jd, 4) * e, t_jet, 0.2, pan=-0.15)
    m.add(A.hiss(jd, 14, 9.0) * e, t_jet, 0.2, pan=0.15)
    m.add(A.whoosh(t_flip1 - t_flip0 + 0.1, 31), t_flip0, 0.45)
    m.add(A.impact(1.2, 8), t_land, 0.55)
    m.add(AF.murmur(at(4, 1.0) - at(4) + 0.3, 7), at(4) - 0.2, 0.18)
    # section 2
    m.add(AF.tear(0.9, 1), at(5, 0.1), 0.45)
    for k, tb in enumerate((0.12, 0.39, 0.66)):
        m.add(AF.crunch(10 + k), at(9, tb), 0.3, pan=(k - 1) * 0.4)
    m.add(AF.tear(0.7, 3), at(11, 0.25), 0.4)
    m.add(A.impact(1.4, 44), at(14, 0.12 + 0.28 * 0.3), 0.5)
    # section 3
    m.add(AF.rumble(E[16] - S[16] + 0.3, 31), at(16, 0.05), 0.4)
    # section 4
    m.add(AF.tear(0.6, 43), at(23, 0.08), 0.45)
    # section 5
    m.add(AF.thud(0.7, 51, 60), at(26, 0.35), 0.45)
    m.add(A.impact(1.2, 53), at(27, 0.62), 0.4)
    for k in range(6):
        m.add(AF.flutter(0.45, 60 + k), at(29, 0.05 + 0.1 * k), 0.15, pan=0.3)
    # section 6-7
    m.add(AF.tear(0.9, 71), at(31, 0.05), 0.4)
    m.add(A.hiss(at(33, 1.0) - at(33), 74) * 0.7, at(33), 0.2, pan=-0.15)
    m.add(A.hiss(at(33, 1.0) - at(33), 75, 9.0) * 0.7, at(33), 0.2, pan=0.15)
    m.add(A.whoosh(1.2, 83), at(37, 0.35), 0.3)
    return m.out()[: int(DURATION * SR)]


def build_audio():
    import subprocess
    from scipy.io import wavfile
    import audio as A
    import audio_full as AF
    SR = A.SR
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SONG, "-t", f"{DURATION:.3f}", "-ar", str(SR), "-ac", "2",
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    song = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    n = int(DURATION * SR)
    song = np.pad(song, ((0, max(0, n - len(song))), (0, 0)))[:n]
    fo = int((DURATION - bar(48) - 2.0) * SR)     # hold the lift for ~2 s, then fade out
    song[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    fx = sfx()
    mix = song * 0.8 + fx[:n] * 0.8
    out = os.path.join(HERE, "..", "build", "audio_music.wav")
    st = mix
    for _ in range(10):
        wavfile.write(out, SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
        lu = AF.measure(out)
        if abs(lu - AF.TARGET_LUFS) < 0.3:
            break
        st = AF.limit(st * 10 ** ((AF.TARGET_LUFS - lu) / 20))
    return out, lu


if __name__ == "__main__":
    if "--audio" in sys.argv:
        sys.path.insert(0, os.path.join(HERE, ".."))
        print(build_audio())
    else:
        print(f"duration {DURATION:.2f}s (old {B.DURATION:.2f}s)")
        for i, s in enumerate(B.LINES):
            d0 = B.END[i] - B.START[i]
            print(f"{i:2d} {START[i]:6.2f}-{END[i]:6.2f} ({END[i] - START[i]:4.2f}s, x{(END[i] - START[i]) / d0:4.2f})  {s}")
