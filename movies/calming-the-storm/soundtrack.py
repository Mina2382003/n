"""Soundtrack for render.py: the dialogue (voices/dialogue.wav from voices.py) over sea, wind, rain, thunder on
every lightning flash, and a soft score that follows the story (warm major on the shore, a dark drone in the storm,
resolving when the sea is calmed). Everything under the voices ducks while someone is speaking. Writes soundtrack.wav."""
import os, math, wave
from itertools import accumulate
import numpy as np
import render as R

SR = 44100
N = int(R.TOTAL * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
HERE = os.path.dirname(os.path.abspath(__file__))


def onepole(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    return np.array(list(accumulate(x * (1 - a), lambda p, v: p * a + v)))


def lp(x, fc, order=2):
    for _ in range(order):
        x = onepole(x, fc)
    return x


def hp(x, fc):
    return x - onepole(x, fc)


def noise():
    return rng.standard_normal(N)


def shot_curve(level):
    """gain curve from a per-shot level function, crossfading with the picture dissolves"""
    g = np.zeros(N)
    for k, sh in enumerate(R.SHOTS):
        s, d = sh["start"], sh["d"]
        i0, i1 = int(s * SR), min(N, int((s + d) * SR))
        tt = t[i0:i1] - s
        e = np.clip(tt / sh["xf"], 0, 1) if k else np.ones(i1 - i0)
        nxt = R.SHOTS[k + 1] if k + 1 < len(R.SHOTS) else None
        if nxt:
            e = e * np.clip((s + d - t[i0:i1]) / nxt["xf"], 0, 1)
        g[i0:i1] += level(sh, tt) * e
    return lp(g, 3, 1)


def is_storm(sh):
    return sh["look"]["sea"] == "storm"


calm = shot_curve(lambda sh, tt: np.full(len(tt), 0.0 if is_storm(sh) else 1.0))
storm = shot_curve(lambda sh, tt: np.full(len(tt), 1.0 if is_storm(sh) else (.15 if sh["image"] == 4 else 0.0)))
rain = shot_curve(lambda sh, tt: np.array([R.rain_level(sh, x) for x in tt[::441]]).repeat(441)[:len(tt)])

# --- dialogue and ducking
with wave.open(f"{HERE}/voices/dialogue.wav") as w:
    dlg = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
dlg = np.pad(dlg, (0, max(0, N - len(dlg))))[:N]
active = lp(np.abs(dlg) > .02, 4, 2)
duck = 1 - .6 * np.clip(active * 3, 0, 1)

# --- sea, wind, rain
swell = .55 + .45 * np.sin(2 * np.pi * t / 5.5) ** 2
seaL, seaR = lp(noise(), 500) * swell, lp(noise(), 500) * np.roll(swell, SR // 3)
roar = lp(noise(), 260, 3) * (.7 + .3 * np.sin(2 * np.pi * t / 2.4))
wind = lp(noise(), 900) * (.6 + .4 * np.sin(2 * np.pi * t / 3.7 + 1))
rainL, rainR = hp(noise(), 2500) * .5, hp(noise(), 2500) * .5
L = 2.2 * calm * seaL + 3.0 * storm * (roar + .6 * wind) + rain * rainL
Rr = 2.2 * calm * seaR + 3.0 * storm * (.9 * roar + .6 * np.roll(wind, 900)) + rain * rainR

# --- thunder on each flash
for sh in R.SHOTS:
    for ft in sh["flashes"]:
        i0 = int((sh["start"] + ft + .12) * SR)
        n = min(int(3.2 * SR), N - i0)
        if n <= 0:
            continue
        tt = np.arange(n) / SR
        th = hp(rng.standard_normal(n), 1500) * np.exp(-tt * 18) * .8 \
            + lp(rng.standard_normal(n), 120, 3) * (1 - np.exp(-tt * 12)) * np.exp(-tt * 1.3) * 9
        L[i0:i0 + n] += th
        Rr[i0:i0 + n] += np.roll(th, 400)


# --- score
def note(f, a, b, amp, attack=1.5, release=2.0):
    i0, i1 = int(a * SR), min(int(b * SR), N)
    if i1 <= i0:
        return np.zeros(N)
    tt = np.arange(i1 - i0) / SR
    ph = 2 * np.pi * f * np.cumsum(1 + .003 * np.sin(2 * np.pi * 5 * tt)) / SR
    w = np.sin(ph) + .35 * np.sin(2 * ph) + .15 * np.sin(3 * ph) + .5 * np.sin(ph * 1.003)
    e = np.clip(np.minimum(tt / attack, (tt[-1] - tt) / release + 1e-9), 0, 1)
    out = np.zeros(N)
    out[i0:i1] = amp * w * e
    return out


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


CALM_CHORDS = [[50, 57, 62, 66], [47, 54, 59, 62], [43, 55, 59, 62], [45, 57, 61, 64]]  # D Bm G A
MOOD = {4: [43, 55, 58, 62], 5: [38, 45, 50, 53], 6: [38, 45, 50, 53], 7: [46, 53, 58, 62, 65]}  # Gm, Dm, Dm, Bb
music = np.zeros(N)
for sh in R.SHOTS:
    a, b = sh["start"], sh["start"] + sh["d"] + .8
    if sh["image"] in MOOD:
        music += sum(note(hz(m), a, b, .06 if m > 48 else .09) for m in MOOD[sh["image"]])
    else:  # calm: walk through D Bm G A every ~4.5 s
        k, x = 0, a
        while x < b:
            y = min(b, x + 4.5 + .8)
            music += sum(note(hz(m), x, y, .05 if m > 48 else .075) for m in CALM_CHORDS[k % 4])
            x += 4.5
            k += 1
    if is_storm(sh):  # low heartbeat
        for k in np.arange(a, a + sh["d"], .8):
            i0, n = int(k * SR), int(.5 * SR)
            if i0 + n < N:
                tt = np.arange(n) / SR
                music[i0:i0 + n] += .5 * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 9)
music = lp(music, 2200, 1)
rev = music.copy()
for d, g in ((.031, .5), (.047, .45), (.071, .4), (.113, .35)):
    k = int(d * SR)
    rev[k:] += g * rev[:-k] * .5
music = music + .25 * rev / (np.abs(rev).max() + 1e-9) * np.abs(music).max()

bgL = (L + 1.4 * music) * duck
bgR = (Rr + 1.4 * np.roll(music, 300)) * duck
bg_peak = np.abs(np.stack([bgL, bgR])).max()
bgL, bgR = bgL / bg_peak * .32, bgR / bg_peak * .32  # the bed sits well under the voices
out = np.stack([bgL + .95 * dlg, bgR + .95 * dlg], 1)
fade = np.clip(np.minimum(t / .8, (R.TOTAL - t) / 1.6), 0, 1)[:, None]
out *= fade
out *= .95 / np.abs(out).max()
with wave.open(f"{HERE}/soundtrack.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("soundtrack.wav", R.TOTAL)
