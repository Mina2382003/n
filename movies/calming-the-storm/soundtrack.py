"""Synthesised soundtrack for render.py: sea, wind, rain, thunder on every lightning flash, and a soft score
that goes from warm major (shore) to a dark drone (storm) and resolves at sunset. Writes soundtrack.wav."""
import os, math, wave
import numpy as np
import render as R

SR = 44100
N = int(R.TOTAL * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(11)
HERE = os.path.dirname(os.path.abspath(__file__))


def onepole(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    y = np.empty_like(x)
    from itertools import accumulate
    y[:] = list(accumulate(x * (1 - a), lambda p, v: p * a + v))
    return y


def lp(x, fc, order=2):
    for _ in range(order):
        x = onepole(x, fc)
    return x


def hp(x, fc):
    return x - onepole(x, fc)


def noise():
    return rng.standard_normal(N).astype(np.float64)


def env_scenes(levels, xf=R.XF):
    """per-scene gain curve, crossfading exactly with the picture dissolves"""
    g = np.zeros(N)
    for i, lv in enumerate(levels):
        s, d = R.STARTS[i], R.SCENES[i]["d"]
        e = np.clip((t - s) / xf, 0, 1) if i else np.ones(N)
        e = e * np.clip((s + d - t) / xf, 0, 1) if i < len(levels) - 1 else e * (t >= s)
        g += lv * e * ((t >= s) & (t < s + d))
    return lp(g, 3, 1)


# --- sea: low swells
swell = .55 + .45 * np.sin(2 * np.pi * t / 5.5) ** 2
seaL, seaR = lp(noise(), 500) * swell, lp(noise(), 500) * np.roll(swell, SR // 3)
# --- storm sea / wind / rain
roar = lp(noise(), 260, 3) * (.7 + .3 * np.sin(2 * np.pi * t / 2.4))
wind_c = lp(noise(), 900) * (.6 + .4 * np.sin(2 * np.pi * t / 3.7 + 1))
rainL, rainR = hp(noise(), 2500) * .5, hp(noise(), 2500) * .5

calm = env_scenes([1, .9, 1, 1, 1, 0, 0, 0, .8])
storm = env_scenes([0, 0, 0, 0, .15, 1, 1, .7, 0])
rain = env_scenes([0, 0, 0, 0, .05, .8, 1, .6, 0])

L = 2.2 * calm * seaL + 3.0 * storm * (roar + .6 * wind_c) + 1.0 * rain * rainL
Rr = 2.2 * calm * seaR + 3.0 * storm * (roar * .9 + .6 * np.roll(wind_c, 900)) + 1.0 * rain * rainR

# --- thunder on each flash
for i, sc in enumerate(R.SCENES):
    for ft in sc["flashes"]:
        T0 = R.STARTS[i] + ft
        i0 = int(T0 * SR)
        n = int(3.2 * SR)
        if i0 >= N:
            continue
        n = min(n, N - i0)
        tt = np.arange(n) / SR
        crack = hp(rng.standard_normal(n), 1500) * np.exp(-tt * 18) * .8
        rumble = lp(rng.standard_normal(n), 120, 3) * (1 - np.exp(-tt * 12)) * np.exp(-tt * 1.3) * 9
        th = crack + rumble
        L[i0:i0 + n] += th
        Rr[i0:i0 + n] += np.roll(th, 400)

# --- score
def note(f, a, b, amp, attack=1.2, release=1.5):
    i0, i1 = int(a * SR), min(int(b * SR), N)
    tt = np.arange(i1 - i0) / SR
    vib = 1 + .003 * np.sin(2 * np.pi * 5 * tt)
    ph = 2 * np.pi * f * np.cumsum(vib) / SR
    w = np.sin(ph) + .35 * np.sin(2 * ph) + .15 * np.sin(3 * ph) + .5 * np.sin(ph * 1.003)
    e = np.minimum(1, tt / attack) * np.minimum(1, (tt[-1] - tt) / release + 1e-9)
    out = np.zeros(N)
    out[i0:i1] = amp * w * np.clip(e, 0, 1)
    return out


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


music = np.zeros(N)
S = R.STARTS
chords = [  # (start, end, midi notes)
    (0, S[1] + .6, [50, 57, 62, 66]),             # D
    (S[1], S[2] + .6, [47, 54, 59, 62]),          # Bm
    (S[2], S[3] + .6, [43, 55, 59, 62]),          # G
    (S[3], S[4] + .6, [45, 57, 61, 64]),          # A
    (S[4], S[5] + .4, [43, 55, 58, 62]),          # Gm - something is coming
    (S[5], S[7] + .5, [38, 45, 50, 53]),          # Dm drone through the storm
    (S[7], S[8] + .6, [46, 53, 58, 62, 65]),      # Bb - he stands
    (S[8], R.TOTAL, [38, 50, 57, 62, 66, 69]),    # D - calm
]
for a, b, ns in chords:
    for m in ns:
        music += note(hz(m), a, b, .06 if m > 48 else .09)
# low heartbeat pulse in the storm
for k in np.arange(S[5], S[7] + 1, .8):
    i0 = int(k * SR); n = int(.5 * SR)
    if i0 + n < N:
        tt = np.arange(n) / SR
        music[i0:i0 + n] += .5 * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 9)
music = lp(music, 2200, 1)
# simple room: a few feedback delays
rev = music.copy()
for d, g in ((.031, .5), (.047, .45), (.071, .4), (.113, .35)):
    k = int(d * SR)
    for _ in range(3):
        rev[k:] += g * rev[:-k] * .5
music = music + .25 * rev / np.abs(rev).max() * np.abs(music).max()

L += 1.4 * music
Rr += 1.4 * np.roll(music, 300)

out = np.stack([L, Rr], 1)
fade = np.clip(np.minimum(t / .8, (R.TOTAL - t) / 1.6), 0, 1)[:, None]
out *= fade
out *= .89 / np.abs(out).max()
with wave.open(f"{HERE}/soundtrack.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((out * 32767).astype(np.int16).tobytes())
print("soundtrack.wav", R.TOTAL)
