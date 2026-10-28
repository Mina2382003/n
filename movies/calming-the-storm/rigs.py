"""Character acting for render.py: eye blinks, talking jaws and arm/hand gestures, done as local
puppet warps on the still (coordinates are in 1280x720 still space).

face  : eyes [(x, y, rx, ry)], optional mouth (x, lip_y, half_width, jaw_depth), talk [(t0, t1, amount_px)]
limb  : pivot (x, y), direction phi (deg, 0 = right, -90 = up), reach r0..r1, half-angle hw (deg),
        motion: list of ("osc", amp_deg, hz, phase) | ("ramp", deg_from, deg_to, t0, t1)
"""
import math
import numpy as np

# fmt: off
RIGS = {
    0: [  # kids on the beach
        dict(kind="limb", pivot=(185, 380), phi=-136, r0=40, r1=210, hw=25, fa=14, motion=[('osc', 6, 1.6, 0)]),
        dict(kind="limb", pivot=(385, 385), phi=-36, r0=40, r1=170, hw=25, fa=14, motion=[('osc', 6, 1.6, 1.0)]),
        dict(kind="limb", pivot=(625, 545), phi=-50, r0=30, r1=160, hw=25, fa=14, motion=[('osc', 5, 1.2, 0.5)]),
        dict(kind="face", eyes=[(272, 263, 29, 23), (358, 258, 20, 23)], mouth=(322, 325, 30, 36), talk=[(0.3, 3.6, 6)], seed=11),
        dict(kind="face", eyes=[(530, 472, 24, 21), (589, 455, 16, 18)], mouth=(575, 505, 20, 18), talk=[(1.0, 2.6, 4)], seed=12),
        dict(kind="face", eyes=[(753, 508, 23, 20), (820, 501, 16, 19)], mouth=(800, 548, 20, 16), talk=[(1.8, 3.7, 4)], seed=13),
    ],
    1: [  # teaching the crowd
        dict(kind="limb", gate=21, pivot=(585, 300), phi=-31, r0=15, r1=130, hw=30, fa=14, motion=[('osc', 6, 0.7, 0)]),
        dict(kind="limb", gate=21, pivot=(350, 350), phi=0, r0=20, r1=100, hw=30, fa=14, motion=[('osc', 5, 0.6, 1.5)]),
        dict(kind="face", eyes=[(478, 160, 8, 8), (505, 158, 7, 8)], mouth=(488, 190, 14, 20), talk=[(0.3, 3.7, 4)], seed=21),
        dict(kind="face", eyes=[(660, 375, 9, 10), (690, 368, 8, 9)], mouth=(670, 402, 10, 8), talk=[], seed=22),
        dict(kind="face", eyes=[(735, 425, 10, 11), (758, 420, 7, 10)], mouth=(748, 453, 9, 10), talk=[], seed=23),
        dict(kind="face", eyes=[(265, 370, 8, 9), (290, 368, 7, 8)], mouth=(285, 396, 8, 8), talk=[], seed=24),
        dict(kind="face", eyes=[(840, 318, 7, 7), (868, 316, 7, 7)], mouth=(852, 352, 11, 12), talk=[], seed=25),
        dict(kind="face", eyes=[(178, 238, 6, 7), (200, 236, 5, 6)], mouth=(190, 265, 8, 7), talk=[], seed=26),
    ],
    2: [  # pointing to the boat
        dict(kind="limb", gate=31, pivot=(560, 275), phi=5, r0=40, r1=230, hw=18, fa=12, motion=[('osc', 2.5, 0.5, 0)]),
        dict(kind="limb", gate=31, pivot=(330, 390), phi=-5, r0=20, r1=110, hw=30, fa=14, motion=[('osc', 6, 0.8, 1)]),
        dict(kind="face", eyes=[(497, 157, 10, 11), (526, 157, 7, 9)], mouth=(500, 195, 16, 18), talk=[(0.2, 2.6, 4.5)], seed=31),
        dict(kind="face", eyes=[(950, 255, 9, 10), (982, 255, 8, 9)], mouth=(960, 290, 14, 10), talk=[(2.4, 3.6, 3)], seed=32),
        dict(kind="face", eyes=[(808, 258, 6, 6), (830, 255, 5, 6)], mouth=None, talk=[], seed=33),
        dict(kind="face", eyes=[(213, 265, 7, 7), (240, 262, 6, 6)], mouth=None, talk=[], seed=34),
    ],
    3: [  # setting sail
        dict(kind="limb", pivot=(175, 560), phi=-60, r0=0, r1=160, hw=20, fa=14, motion=[('osc', 7, 0.5, 0)]),
        dict(kind="limb", pivot=(175, 560), phi=120, r0=0, r1=200, hw=20, fa=14, motion=[('osc', 7, 0.5, 0)]),
        dict(kind="limb", pivot=(1160, 420), phi=40, r0=20, r1=200, hw=20, fa=14, motion=[('osc', 7, 0.5, 1.2)]),
        dict(kind="limb", pivot=(1160, 420), phi=-140, r0=0, r1=90, hw=25, fa=14, motion=[('osc', 7, 0.5, 1.2)]),
        dict(kind="face", eyes=[(650, 205, 6, 7), (675, 205, 5, 6)], mouth=(655, 232, 10, 8), talk=[(0.8, 2.6, 3)], seed=41),
        dict(kind="face", eyes=[(425, 335, 8, 9), (455, 333, 7, 8)], mouth=(440, 368, 11, 10), talk=[], seed=42),
        dict(kind="face", eyes=[(213, 298, 6, 7)], mouth=None, talk=[], seed=43),
        dict(kind="face", eyes=[(1012, 298, 8, 8), (1033, 293, 6, 7)], mouth=(1015, 326, 11, 10), talk=[], seed=44),
        dict(kind="face", eyes=[(745, 255, 6, 6), (765, 253, 5, 5)], mouth=None, talk=[], seed=45),
        dict(kind="face", eyes=[(465, 228, 6, 6), (490, 228, 5, 5)], mouth=None, talk=[], seed=46),
    ],
    4: [  # Jesus asleep, calm sea
        dict(kind="limb", pivot=(720, 420), phi=34, r0=60, r1=330, hw=22, fa=14, motion=[('osc', 4, 0.45, 0)]),
        dict(kind="face", eyes=[(765, 262, 10, 12), (805, 270, 9, 11)], mouth=(765, 320, 18, 12), talk=[(1.2, 2.4, 3)], seed=51),
        dict(kind="face", eyes=[(705, 150, 7, 8), (735, 148, 6, 7)], mouth=None, talk=[], seed=52),
        dict(kind="face", eyes=[(905, 140, 8, 8), (935, 140, 7, 8)], mouth=None, talk=[], seed=53),
        dict(kind="face", eyes=[(1100, 170, 8, 8), (1135, 165, 7, 8)], mouth=None, talk=[], seed=54),
        dict(kind="face", eyes=[(1190, 310, 8, 9), (1220, 315, 7, 8)], mouth=None, talk=[], seed=55),
    ],
    5: [  # the storm hits
        dict(kind="limb", pivot=(760, 450), phi=25, r0=60, r1=330, hw=20, fa=14, motion=[('osc', 4, 0.6, 0)]),
        dict(kind="limb", pivot=(1040, 450), phi=30, r0=40, r1=220, hw=20, fa=14, motion=[('osc', 4, 0.6, 2)]),
        dict(kind="limb", pivot=(480, 260), phi=-30, r0=20, r1=110, hw=25, fa=14, motion=[('osc', 5, 0.8, 0)]),
        dict(kind="face", eyes=[(845, 370, 10, 12), (882, 375, 9, 11)], mouth=(845, 410, 16, 16), talk=[(0.8, 2.4, 5), (3.6, 5.0, 5)], seed=61),
        dict(kind="face", eyes=[(1085, 368, 8, 9), (1115, 365, 7, 8)], mouth=(1090, 390, 14, 10), talk=[(2.0, 3.4, 4), (5.2, 6.6, 4)], seed=62),
        dict(kind="face", eyes=[(448, 165, 8, 9), (480, 162, 7, 8)], mouth=(465, 210, 14, 12), talk=[(1.4, 2.8, 4), (4.6, 5.8, 4)], seed=63),
        dict(kind="face", eyes=[(262, 175, 8, 9), (292, 170, 7, 8)], mouth=(262, 215, 12, 10), talk=[(3.0, 4.2, 3)], seed=64),
        dict(kind="face", eyes=[(780, 243, 7, 8), (805, 242, 6, 7)], mouth=(790, 268, 10, 8), talk=[(4.0, 5.4, 3)], seed=65),
    ],
    6: [  # Master, wake up!
        dict(kind="limb", pivot=(560, 320), phi=146, r0=30, r1=160, hw=25, fa=14, motion=[('osc', 3, 3.0, 0)]),
        dict(kind="limb", pivot=(200, 250), phi=165, r0=20, r1=120, hw=25, fa=14, motion=[('osc', 4, 1.2, 0)]),
        dict(kind="face", eyes=[(615, 275, 9, 12), (650, 283, 9, 11)], mouth=(617, 325, 16, 18), talk=[(0.3, 1.7, 6), (2.2, 3.5, 6)], seed=71),
        dict(kind="face", eyes=[(240, 160, 8, 10), (275, 165, 8, 9)], mouth=(245, 212, 14, 14), talk=[(1.0, 2.4, 5)], seed=72),
        dict(kind="face", eyes=[(468, 168, 10, 11), (500, 170, 9, 10)], mouth=(470, 222, 14, 12), talk=[(1.8, 3.3, 4)], seed=73),
        dict(kind="face", eyes=[(1055, 290, 10, 11), (1092, 300, 8, 10)], mouth=(1050, 340, 14, 14), talk=[(0.6, 2.0, 5), (2.6, 3.5, 4)], seed=74),
    ],
    7: [  # "Peace, be still"
        dict(kind="limb", pivot=(770, 320), phi=-12, r0=40, r1=430, hw=30, fa=16,
             motion=[("ramp", 7, 0, 0.0, 1.4), ("osc", 1.2, .55, 0)]),                 # raises his arm
        dict(kind="limb", pivot=(995, 235), phi=-55, r0=10, r1=150, hw=45, fa=20,
             motion=[("ramp", 12, 0, 0.2, 1.5), ("osc", 4, .9, 1.0)]),                   # open hand calms the sea
        dict(kind="limb", pivot=(450, 430), phi=165, r0=30, r1=200, hw=28, fa=14,
             motion=[("osc", 3, .45, 2.0)]),                                              # other hand
        dict(kind="face", eyes=[(676, 165, 13, 10), (705, 170, 6, 8)], mouth=(688, 211, 22, 30),
             talk=[(1.2, 2.6, 6)], seed=81),                                               # Jesus speaks
        dict(kind="face", eyes=[(142, 360, 10, 9), (170, 353, 6, 7)], mouth=(172, 393, 16, 24), talk=[], seed=82),
        dict(kind="face", eyes=[(313, 387, 10, 9), (347, 383, 7, 7)], mouth=(337, 420, 18, 26), talk=[], seed=83),
        dict(kind="face", eyes=[(182, 497, 11, 11), (208, 485, 6, 7)], mouth=(220, 533, 16, 22), talk=[], seed=84),
        dict(kind="face", eyes=[(825, 452, 8, 7), (855, 462, 6, 6)], mouth=(830, 485, 12, 18), talk=[], seed=85),
        dict(kind="face", eyes=[(1027, 525, 9, 8), (1062, 542, 7, 7)], mouth=(1020, 570, 14, 20), talk=[], seed=86),
    ],
    8: [  # calm at sunset
        dict(kind="limb", gate=91, pivot=(420, 240), phi=-140, r0=30, r1=160, hw=25, fa=14, motion=[("osc", 4, .5, 0)]),
        dict(kind="limb", gate=91, pivot=(720, 260), phi=-6, r0=50, r1=210, hw=20, fa=14, motion=[("osc", 3, .5, 1)]),
        dict(kind="face", eyes=[(600, 125, 7, 9), (628, 128, 6, 8)], mouth=(612, 158, 12, 10), talk=[(1.5, 3.0, 4)], seed=91),
        dict(kind="face", eyes=[(152, 272, 8, 9), (180, 268, 6, 7)], mouth=(175, 300, 12, 10), talk=[], seed=92),
        dict(kind="face", eyes=[(297, 280, 8, 9), (322, 278, 6, 7)], mouth=None, talk=[], seed=93),
        dict(kind="face", eyes=[(225, 398, 9, 10), (258, 402, 7, 8)], mouth=(255, 428, 12, 10), talk=[(3.2, 4.4, 3)], seed=94),
        dict(kind="face", eyes=[(762, 372, 7, 8), (790, 372, 6, 7)], mouth=None, talk=[], seed=95),
        dict(kind="face", eyes=[(945, 425, 8, 9), (975, 422, 6, 8)], mouth=None, talk=[], seed=96),
        dict(kind="face", eyes=[(1088, 390, 8, 9), (1112, 390, 7, 8)], mouth=(1080, 420, 11, 10), talk=[], seed=97),
    ],
}
# fmt: on


def _ss(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def refine_eye(img, e, K):
    """snap a rough eye (x, y, rx, ry) to the white of the eye nearby; also pick the lid skin colour"""
    x, y, rx, ry = (v * K for v in e[:4])
    H, W = img.shape[:2]
    x0, x1 = int(max(0, x - 2 * rx)), int(min(W, x + 2 * rx + 1))
    y0, y1 = int(max(0, y - 2 * ry)), int(min(H, y + 2 * ry + 1))
    win = img[y0:y1, x0:x1]
    mn, mx = win.min(2), win.max(2)
    white = (mn > .62) & ((mx - mn) / (mx + 1e-4) < .3)
    # connected white blob closest to the rough centre (simple flood fill)
    seeds = np.argwhere(white)
    out = (x / K, y / K, rx / K, ry / K)
    if len(seeds) and min(e[2], e[3]) < 14:  # big eyes are measured by hand
        cy, cx = y - y0, x - x0
        s0 = tuple(seeds[np.argmin((seeds[:, 0] - cy) ** 2 + (seeds[:, 1] - cx) ** 2)])
        seen = np.zeros_like(white); stack = [s0]; seen[s0] = True; pts = []
        while stack:
            a, b = stack.pop(); pts.append((a, b))
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                na, nb = a + da, b + db
                if 0 <= na < white.shape[0] and 0 <= nb < white.shape[1] and white[na, nb] and not seen[na, nb]:
                    seen[na, nb] = True; stack.append((na, nb))
        p = np.array(pts)
        if len(p) >= 6 * K * K:
            ya, xa = p[:, 0].min() + y0, p[:, 1].min() + x0
            yb, xb = p[:, 0].max() + y0, p[:, 1].max() + x0
            ex, ey = (xa + xb) / 2, (ya + yb) / 2
            erx, ery = max((xb - xa) / 2 + 1.5 * K, 3 * K), max((yb - ya) / 2 + 1.5 * K, 3 * K)
            if abs(ex - x) < 1.6 * rx and abs(ey - y) < 1.6 * ry and .45 < (erx * ery) / (rx * ry) < 2.2:
                out = (ex / K, ey / K, erx / K, ery / K)
    ex, ey, erx, ery = (v * K for v in out)
    # skin: median of mid-tone, saturated pixels on a ring around the eye
    ang = np.radians(np.linspace(35, 145, 24))  # the cheek just under the eye
    rr = np.concatenate([np.full(24, 1.7), np.full(24, 2.1)])
    ang = np.concatenate([ang, ang])
    px = np.clip((ex + rr * erx * np.cos(ang)).astype(int), 0, W - 1)
    py = np.clip((ey + rr * ery * np.sin(ang)).astype(int), 0, H - 1)
    ring = img[py, px]
    lum = ring.mean(1)
    sat = (ring.max(1) - ring.min(1)) / (ring.max(1) + 1e-4)
    good = ring[(lum > .3) & (lum < .85) & (sat > .25) & (ring[:, 0] > ring[:, 2])]
    pool = good if len(good) >= 4 else ring
    pool = pool[np.argsort(pool.mean(1))[len(pool) // 3:]]  # skip shadows
    skin = np.median(pool, 0)
    return out, skin.astype(np.float32)


def prepare(scene, img, K):
    """refine all eyes of a scene once (called when the scene is loaded)"""
    for r in RIGS.get(scene, []):
        if r["kind"] == "face" and "_eyes" not in r:
            r["_eyes"] = [refine_eye(img, e, K) for e in r["eyes"]]


def blink_amount(seed, t, dur):
    """0 open .. 1 closed; a blink every ~2.5-4 s, each lasting ~0.2 s"""
    rng = np.random.default_rng(seed * 31 + 7)
    tb = rng.uniform(.3, 1.6)
    c = 0.0
    while tb < dur + 1:
        dt = t - tb
        if -0.08 < dt < 0.0:
            c = max(c, 1 + dt / 0.08)
        elif 0 <= dt < 0.06:
            c = 1.0
        elif 0.06 <= dt < 0.2:
            c = max(c, 1 - (dt - .06) / .14)
        tb += rng.uniform(2.3, 4.0)
    return c


def talk_amount(spans, t):
    o = 0.0
    for t0, t1, amp in spans:
        gate = min(1.0, max(0.0, (t - t0) / .12), max(0.0, (t1 - t) / .12))
        if gate > 0:
            syl = abs(math.sin(math.pi * 3.6 * (t - t0) + .7 * math.sin(2 * math.pi * .8 * t)))
            o = max(o, amp * gate * (.25 + .75 * syl))
    return o


def limb_angle(motion, t):
    a = 0.0
    for m in motion:
        if m[0] == "osc":
            a += m[1] * math.sin(2 * math.pi * m[2] * t + m[3])
        else:
            _, a0, a1, t0, t1 = m
            u = min(1, max(0, (t - t0) / (t1 - t0)))
            a += a0 + (a1 - a0) * (u * u * (3 - 2 * u))
    return math.radians(a)


def speaking(spans, t, pad=.35):
    """0..1: is this face talking around time t (for gestures that go with speech)"""
    a = 0.0
    for t0, env in spans:
        t1 = t0 + len(env) / 100
        a = max(a, min(1.0, max(0.0, (t - t0 + pad) / pad), max(0.0, (t1 + pad - t) / pad)))
    return a


def voice_amount(spans, t):
    for t0, env in spans:
        k = int((t - t0) * 100)
        if 0 <= k < len(env):
            return float(env[k])
    return 0.0


def apply(scene, sx, sy, t, dur, K, img, talk=None, limb_t0=0.0):
    """remap source coords (in place copies) and return (sx, sy, shade multiplier or None)"""
    rigs = RIGS.get(scene)
    if not rigs:
        return sx, sy, None, None
    sx, sy = sx.copy(), sy.copy()
    shade = np.ones_like(sx)
    ovr_a = np.zeros_like(sx)
    ovr_c = np.zeros(sx.shape + (3,), np.float32)
    for r in rigs:
        if r["kind"] == "limb":
            th = limb_angle(r["motion"], t - limb_t0)
            if "gate" in r:  # gestures while speaking
                th *= .2 + .8 * speaking((talk or {}).get(r["gate"], []), t)
            if abs(th) < 1e-4:
                continue
            px, py = r["pivot"][0] * K, r["pivot"][1] * K
            R1 = (r["r1"] + 60) * K
            box = (sx > px - R1) & (sx < px + R1) & (sy > py - R1) & (sy < py + R1)
            x, y = sx[box] - px, sy[box] - py
            rad = np.hypot(x, y)
            ang = np.degrees(np.arctan2(y, x))
            da = np.abs((ang - r["phi"] + 180) % 360 - 180)
            w = _ss(r["r0"] * K, (r["r0"] + 60) * K, rad) * (1 - _ss(r["hw"], r["hw"] + r["fa"], da)) \
                * (1 - _ss(r["r1"] * K, (r["r1"] + 60) * K, rad))
            a = -th * w
            c, s = np.cos(a), np.sin(a)
            sx[box] = px + x * c - y * s
            sy[box] = py + x * s + y * c
        else:
            c = blink_amount(r["seed"], t, dur)
            for e, skin in r["_eyes"]:
                if c <= 0.01:
                    break
                ex, ey, rx, ry = (v * K for v in e)
                skin = skin * .97
                ax, ay = rx * 1.08, ry * 1.12
                box = (np.abs(sx - ex) < ax * 1.3) & (np.abs(sy - ey) < ay * 1.3)
                if not box.any():
                    continue
                x, y = sx[box], sy[box]
                ell = 1 - _ss(.8, 1.1, np.hypot((x - ex) / ax, (y - ey) / ay))
                # local skin straight below the eye (keeps the face's own shading), mixed with the cheek tone
                bx = np.clip(x, 0, img.shape[1] - 1).astype(int)
                by = int(min(ey + 1.45 * ay, img.shape[0] - 1))
                local = img[by, bx] * .7 + skin[None, :] * .3
                top = ey - ay
                lid = top + c * 2 * ay + c * .45 * ay * (1 - ((x - ex) / ax) ** 2)  # curved lid edge
                cover = ell * _ss(lid + 1.0 * K, lid - 1.0 * K, y)
                arc = .45 * ay * (1 - ((x - ex) / ax) ** 2)
                lid_line = np.minimum(lid, ey + .25 * ay + arc)  # closed eye: a curved lash line low in the eye
                ell_w = 1 - _ss(.75, 1.0, np.hypot((x - ex) / ax, (y - ey) / ay))
                lash = ell_w * c * np.exp(-((y - lid_line) / (max(1.4, .09 * ay) + .1)) ** 2)
                tone = .78 + .27 * np.clip((y - top) / np.maximum(lid - top, 1), 0, 1)  # crease shadow
                a = ovr_a[box]; col = ovr_c[box]
                a_new = np.maximum(a, cover)
                col = col * (1 - cover[:, None]) + local * (tone * cover)[:, None]
                ovr_a[box] = a_new; ovr_c[box] = col
                sh = shade[box]
                sh *= 1 - .8 * lash
                shade[box] = sh
            if talk is None:
                o = talk_amount(r["talk"], t) * K
            elif r["mouth"]:
                o = voice_amount(talk.get(r["seed"], []), t) * max(2.5, min(7.0, r["mouth"][3] * .26)) * K
            else:
                o = 0.0
            if r["mouth"] and o > .2:
                mx, my, mw, md = (v * K for v in r["mouth"])
                box = (np.abs(sx - mx) < mw * 1.3) & (sy > my - 4 * K) & (sy < my + md + o)
                x, y = sx[box], sy[box]
                wx = 1 - _ss(.55, 1.25, np.abs(x - mx) / mw)
                g = _ss(my - 2 * K, my + 2 * K, y) * (1 - _ss(my + .55 * md, my + md, y))
                sy[box] = y - o * wx * g
                inner = (1 - _ss(.3, .85, np.abs(x - mx) / mw)) * _ss(my - 1 * K, my + 1.5 * K, y) * (1 - _ss(my + o * .8, my + o * 1.05, y))
                sh = shade[box]
                sh *= 1 - .55 * inner
                shade[box] = sh
    return sx, sy, shade, (ovr_a, ovr_c)
