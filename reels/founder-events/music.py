"""Original, royalty-free backing tracks for the founder-events reels (synthesised here, no samples).

Each style returns (stereo float32 array at SR, beat length in seconds). The arrangement follows a list of
section marks in beats so drops and risers land on the edit's cuts.
"""
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(5)


def _filt(x, kind, f, order=2):
    wn = [x / (SR / 2) for x in f] if isinstance(f, (list, tuple)) else f / (SR / 2)
    sos = butter(order, wn, btype=kind, output="sos")
    return sosfilt(sos, x)


def lp(x, f, o=2): return _filt(x, "lowpass", min(f, SR / 2 - 100), o)
def hp(x, f, o=2): return _filt(x, "highpass", f, o)
def bp(x, lo, hi, o=2): return _filt(x, "bandpass", [lo, hi], o)


def hz(m): return 440.0 * 2 ** ((m - 69) / 12)


def env(n, a=.005, d=.2, s=0.0, r=.05, hold=None):
    t = np.arange(n) / SR
    hold = t[-1] - r if hold is None else hold
    e = np.where(t < a, t / a, s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip(1 - (t - hold) / r, 0, 1)
    return e * np.where(t > hold, rel, 1)


def saw(f, n, ph=0.0):
    t = np.arange(n) / SR
    return 2 * ((f * t + ph) % 1) - 1


def sq(f, n):
    t = np.arange(n) / SR
    return np.sign(np.sin(2 * np.pi * f * t))


def sine(f, n, ph=0.0):
    return np.sin(2 * np.pi * f * np.arange(n) / SR + ph)


# ---------------- drums
def kick(dur=.45, f0=160, f1=46, punch=1.0, dist=0.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    x += punch * .5 * hp(rng.standard_normal(n), 2000) * np.exp(-t * 300)
    if dist:
        x = np.tanh(x * (1 + dist)) / np.tanh(1 + dist)
    return x


def clap(dur=.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    e = sum(np.exp(-np.maximum(t - o, 0) * 90) * (t >= o) for o in (0, .011, .022)) * .6 + np.exp(-t * 18) * .5
    return bp(rng.standard_normal(n), 900, 4200) * e


def snare(dur=.28, tone=190):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return .7 * bp(rng.standard_normal(n), 1500, 8000) * np.exp(-t * 22) + .5 * sine(tone, n) * np.exp(-t * 30)


def hat(dur=.06, open_=False):
    n = int((.32 if open_ else dur) * SR)
    t = np.arange(n) / SR
    return hp(rng.standard_normal(n), 7500) * np.exp(-t * (10 if open_ else 70))


def snap(dur=.12):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return bp(rng.standard_normal(n), 1800, 5000) * np.exp(-t * 60)


def cowbell(f=560, dur=.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = sq(f, n) + sq(f * 1.48, n)
    return bp(x, 400, 3500) * np.exp(-t * 9)


def b808(f, dur, glide_from=None, dist=.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ff = np.full(n, f) if glide_from is None else f + (glide_from - f) * np.exp(-t * 18)
    x = np.sin(2 * np.pi * np.cumsum(ff) / SR)
    x = np.tanh(x * (1 + 3 * dist)) / np.tanh(1 + 3 * dist)
    return x * env(n, .003, dur * .9, .6, .04)


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    x = rng.standard_normal(n)
    out = np.zeros(n)
    for k in range(8):  # sweep a band upward in chunks
        a, b = k * n // 8, (k + 1) * n // 8
        lo = 300 + 6000 * (k / 8) ** 2
        out[a:b] = bp(x[a:b], lo, lo * 2.2)
    return out * u ** 2 * .5


def impact(dur=1.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 3) + 30) / SR) * np.exp(-t * 2.5)
    return boom + .3 * lp(rng.standard_normal(n), 1200) * np.exp(-t * 6)


def whoosh(dur=.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    return bp(rng.standard_normal(n), 500, 5000) * np.sin(np.pi * u) ** 2 * .6


# ---------------- tonal
def supersaw(f, n, voices=5, det=.012):
    return sum(saw(f * (1 + det * (k - voices // 2) / (voices // 2)), n, ph=rng.random()) for k in range(voices)) / voices


def pad(notes, dur, cutoff=1800):
    n = int(dur * SR)
    x = sum(supersaw(hz(m), n) for m in notes) / len(notes)
    return lp(x, cutoff) * env(n, .25, 10, 1, .3)


def stab(notes, dur=.22, cutoff=3200):
    n = int(dur * SR)
    x = sum(supersaw(hz(m), n, 3, .008) for m in notes) / len(notes)
    return lp(x, cutoff) * env(n, .003, .09, .25, .05)


def pluck(m, dur=.35, bright=4000):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = saw(hz(m), n) * .6 + sine(hz(m) * 2, n) * .2
    # decaying filter: blend bright/dark versions
    x = lp(x, bright) * np.exp(-t * 14) + lp(x, 900) * np.exp(-t * 6) * .5
    return x * env(n, .002, dur, 0, .02)


def marimba(m, dur=.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    return (sine(f, n) + .35 * sine(f * 3.99, n) * np.exp(-t * 25)) * np.exp(-t * 9)


def piano(m, dur=1.6, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    x = sum(a * sine(f * k * (1 + .0004 * k * k), n) * np.exp(-t * (1.4 + k * .9)) for k, a in ((1, 1), (2, .45), (3, .22), (4, .12), (5, .06)))
    x += .05 * hp(rng.standard_normal(n), 2000) * np.exp(-t * 80)
    return vel * x * env(n, .002, 10, 1, .08)


def bass(m, dur, cutoff=700):
    n = int(dur * SR)
    x = .7 * saw(hz(m), n) + .5 * sine(hz(m) / 2, n)
    return lp(x, cutoff) * env(n, .004, dur * .7, .5, .03)


def reverb(x, mix=.25, tail=1.6):
    n = int(tail * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t * 6.9 / tail)
    ir = lp(ir, 6000)
    wet = np.fft.irfft(np.fft.rfft(x, len(x) + n) * np.fft.rfft(ir, len(x) + n))[:len(x)]
    wet *= np.std(x) / (np.std(wet) + 1e-9)
    return (1 - mix) * x + mix * wet


class Track:
    def __init__(self, seconds, bpm):
        self.b = 60.0 / bpm
        self.n = int(seconds * SR)
        self.bus = {k: np.zeros(self.n) for k in ("drums", "bass", "music", "fx")}
        self.kicks = []

    def put(self, bus, sig, beat, g=1.0):
        i = int(beat * self.b * SR)
        if i >= self.n or i < 0:
            return
        k = min(len(sig), self.n - i)
        self.bus[bus][i:i + k] += g * sig[:k]

    def mix(self, duck=.6, stereo_music=True):
        # sidechain: pump music and bass on every kick
        sc = np.ones(self.n)
        for kb in self.kicks:
            i = int(kb * self.b * SR)
            n = min(int(self.b * .9 * SR), self.n - i)
            if n > 0:
                t = np.arange(n) / SR
                sc[i:i + n] = np.minimum(sc[i:i + n], 1 - duck * np.exp(-t / (self.b * .28)))
        d = self.bus["drums"]
        bs = self.bus["bass"] * sc
        mu = reverb(self.bus["music"], .22) * sc
        fx = reverb(self.bus["fx"], .35)
        L = d + bs + mu * (1.0 if not stereo_music else .9) + fx
        R = d + bs + (np.roll(mu, 220) if stereo_music else mu) + np.roll(fx, 400)
        out = np.stack([L, R], 1)
        out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.6) * .9  # glue / soft clip
        return out.astype(np.float32)


# ---------------- styles. marks: dict of beat numbers (drop, end, ...) so the edit and music agree
def house(total_beats, drop=2, bpm=122):
    T = Track(total_beats * 60 / bpm + 2.5, bpm)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    roots = [45, 41, 36, 43]
    T.put("fx", riser(drop * T.b), 0, .9)
    T.put("fx", impact(), drop, .9)
    for b in range(drop, total_beats):
        bar, beat = divmod(b - drop, 4)
        ch = (b - drop) // 4 % 4
        T.put("drums", kick(), b, 1.0); T.kicks.append(b)
        if beat in (1, 3): T.put("drums", clap(), b, .55)
        T.put("drums", hat(open_=True), b + .5, .22)
        T.put("drums", hat(), b + .25, .1); T.put("drums", hat(), b + .75, .1)
        T.put("bass", bass(roots[ch], T.b * .45), b + .5, .8)
        if beat in (0, 2):
            pass
        for o in (.0, .75, 1.5) if beat in (0, 2) else ():
            T.put("music", stab(prog[ch]), b + o, .5)
        if beat == 0:
            T.put("music", pad([m + 12 for m in prog[ch]], 4 * T.b, 1400), b, .25)
    # tail: let the last chord ring
    T.put("music", pad([57 + 12, 60 + 12, 64 + 12], 3.0, 1200), total_beats, .35)
    T.put("drums", kick(), total_beats, 1.0)
    return T.mix(.55), T.b


def pop(total_beats, drop=2, bpm=108):
    T = Track(total_beats * 60 / bpm + 2.5, bpm)
    prog = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # C G Am F
    roots = [36, 43, 45, 41]
    melody = [72, 76, 79, 76, 74, 79, 74, 71, 72, 76, 81, 76, 77, 76, 74, 72]  # a playful hook, 2 per beat
    for b in range(0, drop):
        T.put("music", marimba(melody[(b * 2) % 16] - 12, .5), b, .6)
        T.put("drums", snap(), b + .5, .4)
    T.put("fx", impact(1.0), drop, .5)
    for b in range(drop, total_beats):
        k = b - drop
        beat = k % 4
        ch = k // 4 % 4
        if beat in (0, 2) or (beat == 3 and k % 8 == 7):
            T.put("drums", kick(.35, 140, 50, .6), b, .9); T.kicks.append(b)
        if beat == 2 and k % 8 == 6:
            T.put("drums", kick(.35, 140, 50, .6), b + .75, .6)
        if beat in (1, 3): T.put("drums", snap(), b, .7); T.put("drums", clap(), b, .3)
        T.put("drums", hat(.04), b + .5, .14)
        T.put("bass", bass(roots[ch], T.b * .9, 500), b, .7)
        for h in (0, .5):
            m = melody[(k * 2 + int(h * 2)) % 16]
            T.put("music", pluck(m, .3), b + h, .38)
            T.put("music", marimba(m - 12, .35), b + h, .18)
        if beat == 0:
            T.put("music", pad(prog[ch], 4 * T.b, 1000), b, .18)
    T.put("music", marimba(84, 1.2), total_beats, .5)
    T.put("music", pad(prog[0], 2.5, 900), total_beats, .3)
    return T.mix(.35), T.b


def cinematic(total_beats, drop=4, bpm=88):
    T = Track(total_beats * 60 / bpm + 3.5, bpm)
    prog = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 55, 60, 64], [55, 59, 62, 67]]  # Am F C G, open voicings
    roots = [33, 29, 36, 31]
    for b in range(0, total_beats, 2):  # piano throughout, two chords per bar
        ch = b // 4 % 4
        for i, m in enumerate(prog[ch]):
            T.put("music", piano(m, 3.0, .5 if b < drop else .38), b + i * .06, 1)
        T.put("music", piano(prog[ch][-1] + 12, 1.4, .25), b + 1, 1)
    T.put("fx", riser(drop * T.b * .8), drop * .2, .5)
    T.put("fx", impact(2.4), drop, 1.0)
    for b in range(drop, total_beats):
        k = b - drop
        beat = k % 4
        ch = b // 4 % 4
        if beat == 0 or (beat == 2 and k % 8 == 6):
            T.put("drums", kick(.5, 120, 42, .4), b, .9); T.kicks.append(b)
        if beat == 2: T.put("drums", snare(.35), b, .55); T.put("drums", clap(), b, .25)
        for h in (0, .5):
            T.put("drums", hat(.03), b + h, .12)
        if k % 8 == 7:
            for r in range(4): T.put("drums", hat(.02), b + .5 + r * .125, .09)  # roll
        if beat == 0:
            T.put("bass", b808(hz(roots[ch]), T.b * 3.6, hz(roots[ch]) * 1.5 if k % 8 == 4 else None, .3), b, .9)
    T.put("fx", impact(2.4), total_beats, .4)
    T.put("music", piano(57, 3.5, .5), total_beats, 1); T.put("music", piano(64, 3.5, .35), total_beats, 1)
    return T.mix(.3), T.b


def phonk(total_beats, drop=4, bpm=140):
    T = Track(total_beats * 60 / bpm + 2.2, bpm)
    bell = [69, 69, 72, 69, 67, 69, 64, 64, 69, 69, 72, 74, 72, 69, 67, 64]  # memphis cowbell line, 8ths
    roots = [45, 45, 41, 43]
    for b in range(0, drop):  # intro: filtered cowbell
        for h in (0, .5):
            T.put("music", lp(cowbell(hz(bell[int(b * 2 + h * 2) % 16])), 1200), b + h, .5)
    T.put("fx", riser(drop * T.b), 0, .6)
    T.put("fx", impact(1.4), drop, .9)
    for b in range(drop, total_beats):
        k = b - drop
        beat = k % 4
        bar = k // 4
        if beat == 0 or (beat == 2 and k % 8 != 6) or (beat == 3 and k % 4 == 3 and bar % 2):
            T.put("drums", kick(.4, 180, 48, 1.0, 1.5), b, .9); T.kicks.append(b)
        if beat in (1, 3): T.put("drums", snare(.3, 210), b, .7); T.put("drums", clap(), b, .4)
        for h in (0, .5):
            T.put("drums", hat(.03), b + h, .16)
        if k % 8 == 7:
            for r in range(6): T.put("drums", hat(.02), b + r / 6, .12)
        for h in (0, .5):
            T.put("music", cowbell(hz(bell[int(k * 2 + h * 2) % 16])), b + h, .55)
        if beat == 0:
            r = roots[bar % 4]
            T.put("bass", b808(hz(r - 12), T.b * 1.8, None, .9), b, .9)
            T.put("bass", b808(hz(r - 12), T.b * 1.5, hz(r - 5), .9), b + 2.5, .8)
    T.put("fx", impact(1.8), total_beats, .7)
    T.put("music", cowbell(hz(69), 1.0), total_beats, .5)
    return T.mix(.45), T.b


STYLES = dict(house=house, pop=pop, cinematic=cinematic, phonk=phonk)
