"""Talking-head reel with effects, no subtitles.

usage: render_clip_fx.py SRC OUT PLAN [WORKDIR]
WORKDIR holds masks.npy (540x960 person masks, one per source frame) and plate.png (clean backdrop).
Dead air is cut from the audio, every phrase gets its own framing, and the PLAN's signature effects
are placed on the phrases that suit them (frame break on the biggest arm gesture).
"""
import subprocess, numpy as np, wave, math, os, sys
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))
SRC, OUT, PLAN = sys.argv[1:4]
WORK = sys.argv[4] if len(sys.argv) > 4 else os.path.join(S, "work")
FONT = S + "/font/package/900Black/Cairo_900Black.ttf"
FONT_B = S + "/font/package/800ExtraBold/Cairo_800ExtraBold.ttf"
EMO = S + "/emoji/package/img/apple/64/"
W, H, FPS, SR = 1080, 1920, 30, 48000
GRADE = ("eq=contrast=1.1:saturation=1.18:gamma=0.98,colorbalance=rm=0.03:bm=-0.02,"
         "unsharp=7:7:0.9:5:5:0.0,vignette=PI/5")
YEL, RED, WHITE, BLACK, HUD = (255, 214, 0), (235, 30, 45), (255, 255, 255), (0, 0, 0), (80, 255, 200)
PLANS = {   # signature effects per reel, on top of the snap-zoom opening and emphasis punch-ins
    "clip_00": ["framebreak", "dolly", "paper"],
    "clip_01": ["digital", "orbit", "zoomthrough"],
    "clip_02": ["paper", "zoomthrough", "dolly"],
    "clip_03": ["orbit", "framebreak", "digital"],
}
FX_LEN = {"framebreak": 1.3, "dolly": 1.2, "paper": 1.4, "digital": 1.6, "orbit": 1.5}

# ---------- audio analysis: his speech vs dead air ----------
def pcm(path, sr):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                                        capture_output=True, check=True).stdout, np.int16).astype(np.float32) / 32768
a16 = pcm(SRC, 16000)
HOP = 800                                             # 50 ms
db = np.array([20 * np.log10(np.sqrt((a16[i:i + HOP] ** 2).mean()) + 1e-6) for i in range(0, len(a16) - HOP, HOP)])
speech = db > np.percentile(db, 10) + 12               # the quiet stretches between phrases are faint room voices, not him
runs, i = [], 0
while i < len(speech):
    if speech[i]:
        j = i
        while j < len(speech) and (speech[j] or (j + 6 < len(speech) and speech[j:j + 6].any())): j += 1   # bridge gaps < 0.3 s
        runs.append((i * 0.05, j * 0.05)); i = j
    else: i += 1
runs = [(max(0, s - 0.10), e + 0.12) for s, e in runs if e - s >= 0.25]
SEGS = []
for s, e in runs:                                      # merge overlaps after padding
    if SEGS and s <= SEGS[-1][1]: SEGS[-1] = (SEGS[-1][0], e)
    else: SEGS.append((s, e))
NSRC_FRAMES = len(np.load(WORK + "/masks.npy", mmap_mode="r"))
SEGS = [(round(s * FPS), min(round(e * FPS), NSRC_FRAMES)) for s, e in SEGS]
OSTART = np.cumsum([0] + [b - a for a, b in SEGS])     # output frame where each segment starts
NV = int(OSTART[-1])
TAIL = 45                                              # follow end card
NF = NV + TAIL
DUR = NF / FPS
SIDX = [f for a, b in SEGS for f in range(a, b)]
SEG_OF = np.concatenate([np.full(b - a, k) for k, (a, b) in enumerate(SEGS)])
print("segments", [(round(a / FPS, 2), round(b / FPS, 2)) for a, b in SEGS], "->", round(NV / FPS, 2), "s")

# emphasis peaks (output seconds): loudest moments, at least 2 s apart
src_db = {f: db[min(len(db) - 1, int(f / FPS / 0.05))] for f in SIDX}
order = sorted(range(NV), key=lambda n: -src_db[SIDX[n]])
PEAKS = []
for n in order:
    t = n / FPS
    if t > 0.8 and all(abs(t - p) > 2.0 for p in PEAKS): PEAKS.append(t)
    if len(PEAKS) >= max(2, int(NV / FPS / 4)): break

# ---------- masks, face track, plate ----------
MASKS = np.load(WORK + "/masks.npy")
NSRC = len(MASKS)
face = np.zeros((NSRC, 2), np.float32)
reach = np.zeros(NSRC, np.float32)
for k, m in enumerate(MASKS):
    b = m > 128
    rows = np.nonzero(b.any(1))[0]
    top = rows[0] if len(rows) else 200
    cols = np.nonzero(b[top + 10:top + 70].any(0))[0]
    face[k] = ((cols.mean() if len(cols) else 270) * 2, (top + 55) * 2)
    band = b[int(top + 180):int(top + 420)]            # elbows/hands band
    cs = np.nonzero(band.any(0))[0]
    reach[k] = (cs[-1] - cs[0]) if len(cs) else 0
kern = np.ones(15) / 15
face = np.stack([np.convolve(np.pad(face[:, i], 7, mode="edge"), kern, "valid") for i in range(2)], 1)
PLATE = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", WORK + "/plate.png", "-vf", f"scale={W}:{H}:flags=lanczos," + GRADE + ",format=rgb24",
                                      "-f", "rawvideo", "-"], capture_output=True, check=True).stdout, np.uint8).reshape(H, W, 3)

def person(si):
    a, b = max(0, si - 1), min(NSRC, si + 2)
    m = cv2.resize(MASKS[a:b].mean(0).astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(np.clip((m - 0.35) / 0.3, 0, 1), (0, 0), 1.5)

# ---------- effect placement ----------
fx = PLAN and PLANS[PLAN] or []
seg_t = [(OSTART[k] / FPS, OSTART[k + 1] / FPS) for k in range(len(SEGS))]
used = {0}
EFFECTS = []   # (start, end, kind, segment)
def spaced(k):   # keep signature effects at least 2.5 s apart
    return all(abs(seg_t[k][0] - s) >= 2.5 for s, *_ in EFFECTS)
def take(kind, k):
    s, e = seg_t[k]
    EFFECTS.append((s, min(e, s + FX_LEN[kind]), kind, k)); used.add(k)
if "framebreak" in fx:
    cand = [k for k in range(len(SEGS)) if k not in used and seg_t[k][1] - seg_t[k][0] >= 1.0]
    k = max(cand, key=lambda k: reach[SEGS[k][0]:SEGS[k][0] + int(1.3 * FPS)].max())
    take("framebreak", k)
rest = [f for f in fx if f not in ("framebreak", "zoomthrough")]
for j, kind in enumerate(rest):
    goal = DUR * (0.35 + 0.5 * j / max(1, len(rest) - 1)) if len(rest) > 1 else DUR * 0.5
    cand = [k for k in range(len(SEGS)) if k not in used and seg_t[k][1] - seg_t[k][0] >= 0.9 and spaced(k)]
    if cand: take(kind, min(cand, key=lambda k: abs(seg_t[k][0] - goal)))
ZT_CUTS = []
if "zoomthrough" in fx:   # zoom-through transitions on two cuts that don't touch another effect
    cuts = [seg_t[k][0] for k in range(1, len(SEGS)) if k not in used and k - 1 not in used]
    for g in (0.3, 0.7):
        if cuts:
            c = min(cuts, key=lambda c: abs(c - DUR * g)); ZT_CUTS.append(c); cuts.remove(c)
EFFECTS.sort()
PEAKS = [p for p in PEAKS if not any(s - 0.3 <= p < e + 0.3 for s, e, *_ in EFFECTS) and all(abs(p - c) > 0.5 for c in ZT_CUTS)]
print("effects", [(round(s, 2), round(e, 2), kd) for s, e, kd, _ in EFFECTS], "zoom-through", [round(c, 2) for c in ZT_CUTS],
      "punches", [round(p, 2) for p in PEAKS])

# ---------- camera ----------
def affine(z, cx, cy, sx=0.0, sy=0.0):
    cw, ch = W / z, H / z
    cx = min(max(cx - sx / z, cw / 2), W - cw / 2); cy = min(max(cy - sy / z, ch / 2), H - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2
    return np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])

def warp(a, M, border=cv2.BORDER_REPLICATE):
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)

def shake(t, t0, amp, d=0.3):
    k = max(0.0, 1 - (t - t0) / d)
    return amp * k * math.sin(t * 95), amp * 0.8 * k * math.cos(t * 81)

ease_out = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
ease_io = lambda u: (lambda v: 3 * v * v - 2 * v * v * v)(min(max(u, 0), 1))
clamp01 = lambda u: min(max(u, 0.0), 1.0)

FRAMINGS = [(1.35, 330), (1.0, 0), (1.75, 180), (1.25, 420), (1.6, 230)]   # zoom, centre offset below the face
def framing(k):
    return FRAMINGS[0] if k == 0 else FRAMINGS[1 + (k - 1) % (len(FRAMINGS) - 1)]

def base_cam(n, si):
    """phrase framing + snap into each new phrase + emphasis punch-ins"""
    t = n / FPS; k = SEG_OF[min(n, NV - 1)]
    z, off = framing(k)
    fx_, fy_ = face[si]
    u = (n - OSTART[k]) / FPS
    if k == 0: z *= 1 + 0.9 * (1 - ease_out(u / 0.18))          # opening snap zoom
    else: z *= 1 + 0.12 * (1 - ease_out(u / 0.12))
    z *= 1 + 0.02 * u                                         # slow push within the phrase
    sx = sy = 0.0
    for p in PEAKS:
        if p <= t < p + 0.55:
            z *= 1 + 0.18 * ease_out((t - p) / 0.06) * (1 - clamp01((t - p - 0.4) / 0.15)); sx, sy = shake(t, p, 12, 0.3)
    if k == 0: sx, sy = shake(t, 0, 20, 0.35)
    return z, fx_, fy_ + off * (z > 1.01), sx, sy

# ---------- graphics ----------
_emo, _txt = {}, {}
def emoji(code, size):
    if (code, size) not in _emo:
        _emo[(code, size)] = Image.open(EMO + code + ".png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return _emo[(code, size)]

def text_img(txt, size, fill=WHITE, box=None, fnt=FONT, emo=None, pad=(46, 10), radius=60):
    key = (txt, size, fill, box, fnt, emo)
    if key in _txt: return _txt[key]
    f = ImageFont.truetype(fnt, size)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, direction="rtl")
    tw, th = r - l, b - t
    es = int(size * 1.05) if emo else 0; gap = int(size * 0.18) if emo else 0
    cw, ch = tw + es + gap + 2 * pad[0], max(th, es) + 2 * pad[1] + 16
    im = Image.new("RGBA", (cw + 24, ch + 24), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((18, 21, 18 + cw, 21 + ch), radius, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
    dr.rounded_rectangle((12, 12, 12 + cw, 12 + ch), radius, fill=box)
    dr.text((12 + pad[0] + es + gap - l, 12 + (ch - th) // 2 - t), txt, font=f, fill=fill, direction="rtl")
    if emo: im.alpha_composite(emoji(emo, es), (12 + pad[0], 12 + (ch - es) // 2))
    _txt[key] = im
    return im

def ease_pop(u):
    if u < 0: return 0
    if u < 0.09: return 0.45 + 0.7 * (u / 0.09)
    if u < 0.18: return 1.15 - 0.15 * ((u - 0.09) / 0.09)
    return 1.0

def paste_center(frame, im, cx, cy, scale=1.0, rot=0.0):
    if scale <= 0.01: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def flash(arr, a, col=(255, 255, 255)):
    if a <= 0: return arr
    return (arr.astype(np.float32) * (1 - a) + np.array(col, np.float32) * a).astype(np.uint8)

_yy, _xx = np.mgrid[0:H, 0:W]

# ---------- signature effects ----------
def build_navy():
    g = np.linspace(0, 1, H)[:, None, None]
    bg = ((1 - g) * np.array([12, 16, 38]) + g * np.array([42, 18, 58])) * np.ones((1, W, 1))
    glow = np.exp(-(((_xx - 540) / 520.0) ** 2 + ((_yy - 760) / 600.0) ** 2))[..., None] * np.array([255, 190, 0]) * 0.35
    return np.clip(bg + glow + np.random.default_rng(3).normal(0, 4, (H, W, 1)), 0, 255).astype(np.uint8)
NAVY = build_navy()

def fx_framebreak(src, si, u_t):
    """photo frame narrower than his reach: head and hands break out of it"""
    u = ease_out(u_t / 0.2)
    k = 1.0 - 0.15 * u + 0.04 * math.sin(clamp01(u_t / 0.35) * math.pi) * (1 - u * 0.3)
    rot = -3.0 * u
    fx_, fy_ = face[si]
    M = affine(1.2, fx_, fy_ + 420)
    C = warp(src, M); A = warp(person(si), M, cv2.BORDER_CONSTANT)
    hy = M[1, 1] * fy_ + M[1, 2]
    hx = M[0, 0] * fx_ + M[0, 2]
    x0, y0, x1, y1 = int(max(30, hx - 430)), int(hy + 110), int(min(W - 30, hx + 430)), H - 60
    win = np.zeros((H, W), np.float32); win[y0:y1, x0:x1] = 1
    brd = np.zeros((H, W), np.float32); brd[y0 - 18:y1 + 18, x0 - 18:x1 + 18] = 1
    ap = A * (1 - win)
    alpha = np.maximum(win, ap + brd * (1 - ap))
    out_rgb = (C * ap[..., None] + 255.0 * (brd * (1 - ap))[..., None]) / np.maximum(alpha, 1e-4)[..., None]
    rgb = np.where(win[..., None] > 0, C, out_rgb).astype(np.float32)
    R = cv2.getRotationMatrix2D((540, 960), rot, k); R[1, 2] += 120 * u
    rgb_s = cv2.warpAffine(rgb, R, (W, H)); a_s = cv2.warpAffine(alpha, R, (W, H))[..., None]
    shadow = np.roll(cv2.GaussianBlur(cv2.warpAffine(brd, R, (W, H)), (0, 0), 24)[..., None], 26, 0) * 0.65
    out = NAVY.astype(np.float32) * (1 - shadow)
    return np.clip(out * (1 - a_s) + rgb_s * a_s, 0, 255).astype(np.uint8)

def fx_dolly(src, si, u_t, d):
    u = ease_io(u_t / d)
    fx_, fy_ = face[si]
    Ms = affine(1.4, fx_, fy_ + 300)
    bg = np.zeros((H, W, 3), np.float32)
    for j in range(3): bg += warp(PLATE, affine(1.4 - 0.4 * u + 0.012 * j * (u > 0.02), fx_, fy_ + 300))
    bg /= 3
    bg = bg * (1 - 0.45 * u) + bg.mean(2, keepdims=True) * 0.45 * u
    bg = bg * (1 - 0.2 * u) + np.array([60, 0, 10]) * 0.2 * u
    a = warp(person(si), Ms, cv2.BORDER_CONSTANT)[..., None]
    arr = warp(src, Ms).astype(np.float32) * a + bg * (1 - a)
    vig = 1 - 0.45 * u * np.clip(((_xx - 540) / 700.0) ** 2 + ((_yy - 900) / 1100.0) ** 2, 0, 1)[..., None]
    return np.clip(arr * vig, 0, 255).astype(np.uint8)

PAPER = None
def build_paper():
    rng = np.random.default_rng(5)
    base = np.array([255, 205, 40], np.float32) * np.ones((H, W, 3))
    fib = cv2.GaussianBlur(rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32), (0, 0), 1.2)
    base *= (1 + 0.05 * cv2.resize(fib, (W, H)))[..., None]
    dots = ((((_xx // 36) + (_yy // 36)) % 2 == 0) & (((_xx % 36) - 18) ** 2 + ((_yy % 36) - 18) ** 2 < 25))
    base[dots] *= 0.9
    return np.clip(base, 0, 255).astype(np.uint8)

def fx_paper(src, si, u_t):
    """stop-motion paper cutout on a craft-paper card"""
    global PAPER
    if PAPER is None: PAPER = build_paper()
    step = int(u_t * 10)                                # 10 fps stop-motion
    rng = np.random.default_rng(step + 11)
    hold = SIDX[max(0, cur_n - int(round((u_t - step / 10) * FPS)))]   # pose held for the whole step
    fx_, fy_ = face[hold]
    pop = ease_pop(u_t * 0.9 + 0.02)
    M = affine(1.25, fx_, fy_ + 380)
    sub = warp(FRAMES[hold], M); m = warp(person(hold), M, cv2.BORDER_CONSTANT)
    rot = rng.uniform(-2.0, 2.0); dx, dy = rng.uniform(-8, 8), rng.uniform(-6, 6)
    R = cv2.getRotationMatrix2D((540, 1100), rot, 0.92 * pop); R[0, 2] += dx; R[1, 2] += dy + 60
    sub = cv2.warpAffine(sub, R, (W, H)); m = cv2.warpAffine(m, R, (W, H))
    outline = cv2.GaussianBlur(cv2.dilate((m > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (29, 29))).astype(np.float32), (0, 0), 1.2)
    shadow = np.roll(np.roll(cv2.GaussianBlur(outline, (0, 0), 10), 18, 0), 12, 1)[..., None] * 0.45
    out = PAPER.astype(np.float32) * (1 - shadow)
    out = out * (1 - outline[..., None]) + 250 * outline[..., None]
    out = out * (1 - m[..., None]) + sub * m[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

def fx_orbit(src, si, u_t, d):
    """camera arcs around him: subject yaws, backdrop slides the other way (parallax)"""
    u = ease_io(u_t / d)
    th = math.radians(-18 + 36 * u)
    fx_, fy_ = face[si]
    M = affine(1.3, fx_, fy_ + 330)
    sub = warp(src, M); m = warp(person(si), M, cv2.BORDER_CONSTANT)
    bg = warp(PLATE, affine(1.5, fx_ - 420 * math.sin(th), fy_ + 330))
    cx = M[0, 0] * fx_ + M[0, 2]
    f = 1800.0
    def proj(x, y):
        X = (x - cx) * math.cos(th); Z = (x - cx) * math.sin(th)
        return cx + X * f / (f + Z), 960 + (y - 960) * f / (f + Z)
    srcq = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
    dstq = np.float32([proj(0, 0), proj(W, 0), proj(W, H), proj(0, H)])
    P = cv2.getPerspectiveTransform(srcq, dstq)
    sub = cv2.warpPerspective(sub, P, (W, H), borderMode=cv2.BORDER_REPLICATE)
    m = cv2.warpPerspective(m, P, (W, H))[..., None]
    arr = sub.astype(np.float32) * m + bg.astype(np.float32) * (1 - m)
    return np.clip(arr, 0, 255).astype(np.uint8)

SCAN = np.ones((H, 1, 1), np.float32); SCAN[::4] = 0.9
def fx_digital(src, si, u_t, fr_holder):
    steps = [(0.0, 1.45), (0.4, 1.95), (0.8, 2.5)]
    ts, z = [s for s in steps if u_t >= s[0]][-1]
    fx_, fy_ = face[si]
    M = affine(z, fx_, fy_ + 40)
    arr = warp(src, M)
    v = u_t - ts
    if v < 0.16:
        blk = int(34 * (1 - v / 0.16))
        if blk >= 2: arr = cv2.resize(cv2.resize(arr, (W // blk, H // blk), interpolation=cv2.INTER_AREA), (W, H), interpolation=cv2.INTER_NEAREST)
    if v < 0.2:
        arr = arr.copy(); arr[..., 0] = np.roll(arr[..., 0], 8, 1); arr[..., 2] = np.roll(arr[..., 2], -8, 1)
    arr = np.clip(arr.astype(np.float32) * np.array([0.95, 1.02, 1.03]) * SCAN, 0, 255).astype(np.uint8)
    arr = flash(arr, 0.4 * (1 - v / 0.08))
    fr_holder.append((M, z, u_t, ts))
    return arr

def draw_hud(fr, M, z, u_t, ts):
    d = ImageDraw.Draw(fr)
    fx_, fy_ = face[cur_si]
    hx, hy = M[0, 0] * fx_ + M[0, 2], M[1, 1] * fy_ + M[1, 2]
    hw, hh = 95 * z, 120 * z
    pad = 60 * (1 - ease_out((u_t - ts) / 0.15))
    bx0, by0, bx1, by1 = hx - hw - pad, hy - hh - pad, hx + hw + pad, hy + hh + pad
    for (cx, cy, sx, sy) in [(bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)]:
        d.line((cx, cy, cx + sx * 56, cy), fill=HUD + (255,), width=7); d.line((cx, cy, cx, cy + sy * 56), fill=HUD + (255,), width=7)
    d.line((hx - 22, hy, hx + 22, hy), fill=HUD + (170,), width=3); d.line((hx, hy - 22, hx, hy + 22), fill=HUD + (170,), width=3)
    if int(u_t * 4) % 2 == 0: d.ellipse((50, 62, 76, 88), fill=(255, 40, 40))
    fb = ImageFont.truetype(FONT_B, 34)
    d.text((88, 50), "REC", font=fb, fill=WHITE, stroke_width=3, stroke_fill=BLACK)
    zt = f"ZOOM ×{z:.1f}"
    d.text((W - 60 - d.textlength(zt, font=fb), 50), zt, font=fb, fill=HUD, stroke_width=3, stroke_fill=BLACK)

CTA = text_img("تابعني لأسرار البيزنس", 72, fill=WHITE, box=RED, emo="1f525")

# ---------- render ----------
class Frames:
    """sequential decode with a short cache: output frames only ever look back a few frames"""
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=lanczos," + GRADE + ",format=rgb24",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.cache, self.next = {}, 0
    def __getitem__(self, i):
        while self.next <= i:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: return self.cache[max(self.cache)]
            self.cache[self.next] = np.frombuffer(b, np.uint8).reshape(H, W, 3); self.next += 1
            for k in [k for k in self.cache if k < self.next - 40]: del self.cache[k]
        return self.cache[i]
FRAMES = Frames()
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        WORK + "/video_only.mp4"], stdin=subprocess.PIPE)
PREVIEW = [float(x) for x in os.environ.get("FX_PREVIEW", "").split(",") if x]
end_bg = None
for n in range(NF):
    t = n / FPS
    cur_n = n
    si = cur_si = SIDX[min(n, NV - 1)]
    src = FRAMES[si]
    hud = []
    if n < NV:
        act = next(((s, e, kd) for s, e, kd, _ in EFFECTS if s <= t < e), None)
        if act:
            s, e, kd = act; u = t - s
            if kd == "framebreak": arr = fx_framebreak(src, si, u)
            elif kd == "dolly": arr = fx_dolly(src, si, u, e - s)
            elif kd == "paper": arr = fx_paper(src, si, u)
            elif kd == "orbit": arr = fx_orbit(src, si, u, e - s)
            else: arr = fx_digital(src, si, u, hud)
            if u < 0.1 and kd != "digital": arr = flash(arr, 0.5 * (1 - u / 0.1))
        else:
            z, cx, cy, sx, sy = base_cam(n, si)
            zt = next((c for c in ZT_CUTS if c - 0.17 <= t < c + 0.17), None)
            if zt is not None:   # zoom through the cut: dive in on the out-going phrase, burst out on the new one
                v = (t - zt) / 0.17
                z *= 1 + 2.4 * (1 - abs(v)) ** 2.2
                acc = np.zeros((H, W, 3), np.float32)
                for j in range(4): acc += warp(src, affine(z * (1 - 0.05 * j), face[si][0], face[si][1] + 60))
                arr = flash((acc / 4).astype(np.uint8), 0.5 * max(0, 1 - abs(v) / 0.35))
            else:
                k = SEG_OF[n]; u = (n - OSTART[k]) / FPS
                if u < 0.12 or (k == 0 and u < 0.18):   # motion blur on the snap
                    acc = np.zeros((H, W, 3), np.float32)
                    for j in range(3): acc += warp(src, affine(z * (1 + 0.04 * j), cx, cy, sx, sy))
                    arr = (acc / 3).astype(np.uint8)
                else:
                    arr = warp(src, affine(z, cx, cy, sx, sy))
                if k == 0: arr = flash(arr, 0.8 * (1 - u / 0.12))
        fr = Image.fromarray(arr).convert("RGBA")
        if hud: draw_hud(fr, *hud[0])
    else:
        # end card: last frame blurred and darkened, follow CTA
        u = (t - NV / FPS)
        if end_bg is None:
            end_bg = cv2.GaussianBlur(warp(src, affine(1.3, face[si][0], face[si][1] + 300)), (0, 0), 18)
            end_bg = (end_bg * 0.5).astype(np.uint8)
        fr = Image.fromarray(warp(end_bg, affine(1 + 0.04 * u / (TAIL / FPS), 540, 960))).convert("RGBA")
        pulse = ease_pop(u - 0.05) * (1 + 0.04 * math.sin(u * 12))
        paste_center(fr, CTA, W / 2, 900, pulse)
        paste_center(fr, emoji("1f446", 120), W / 2 + 260, 1060 + 16 * math.sin(t * 10), ease_pop(u - 0.2))
        if u < 0.12: fr = Image.fromarray(flash(np.asarray(fr.convert("RGB")), 0.8 * (1 - u / 0.12))).convert("RGBA")
    dr = ImageDraw.Draw(fr)
    dr.rectangle((0, 0, W, 12), fill=(0, 0, 0, 110)); dr.rectangle((0, 0, int(W * (n + 1) / NF), 12), fill=YEL + (255,))
    out = fr.convert("RGB")
    if any(abs(t - p) < 0.5 / FPS for p in PREVIEW): out.save(f"{WORK}/prev_{t:05.2f}.jpg", quality=85)
    enc.stdin.write(out.tobytes())
    if n % 90 == 0: print("frame", n, "/", NF, flush=True)
enc.stdin.close(); enc.wait(); FRAMES.p.kill()

# ---------- audio ----------
at = ";".join(f"[0:a:0]atrim={a/FPS}:{b/FPS},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={(b-a)/FPS-0.015}:d=0.015[a{i}]"
              for i, (a, b) in enumerate(SEGS))
afc = (f"{at};{''.join(f'[a{i}]' for i in range(len(SEGS)))}concat=n={len(SEGS)}:v=0:a=1,aformat=channel_layouts=mono,"
       "highpass=f=90,afftdn=nr=14:nf=-40:tn=1,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1:g=3.5,"
       "highshelf=f=8000:g=1.5,acompressor=threshold=-20dB:ratio=3:attack=8:release=150:makeup=2[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", afc, "-map", "[o]", "-ar", str(SR), WORK + "/voice.wav"], check=True)
w = wave.open(WORK + "/voice.wav"); voice = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
N = int(DUR * SR)
V = np.zeros(N, np.float32); V[:min(N, len(voice))] = voice[:N]
rng = np.random.default_rng(7)
tt = lambda d: np.arange(int(d * SR)) / SR

def lp(x, a):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y

def boom(d=1.1):
    t = tt(d); f = 32 + 90 * np.exp(-t * 9)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2) + 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 60)
    return np.tanh(s * 2.2) * 0.9

def whoosh(d=0.45, up=True):
    t = tt(d); n = rng.standard_normal(len(t)); env = np.sin(np.pi * t / d) ** 2
    out = np.zeros_like(n); y1 = y2 = 0.0
    for i in range(len(n)):
        fc = (300 + 4200 * (t[i] / d)) if up else (4500 - 4200 * (t[i] / d))
        r = 0.97; th = 2 * np.pi * fc / SR
        y = n[i] * (1 - r) + 2 * r * np.cos(th) * y1 - r * r * y2; y2, y1 = y1, y; out[i] = y
    return out / (np.abs(out).max() + 1e-9) * env * 0.7

def pop(d=0.08):
    t = tt(d); f = 900 * np.exp(-t * 40) + 250
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 55) * 0.5

def ding(f0=1318.5, d=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * t) + 0.25 * np.sin(2 * np.pi * f0 * 2.01 * t)) * np.exp(-t * 5) * 0.3

def digi(f0=1200):
    t = tt(0.09); s = np.sign(np.sin(2 * np.pi * f0 * t)) * 0.25 + 0.2 * rng.standard_normal(len(t)) * np.exp(-t * 60)
    return (np.round(s * 6) / 6) * np.exp(-t * 18)

def slap():
    t = tt(0.14); n = rng.standard_normal(len(t))
    return (n - lp(n, 0.3)) * np.exp(-t * 45) * 0.6 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30) * 0.6

def vertigo(d):
    t = tt(d); f = 70 - 30 * t / d
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 3.01) / SR)
    return s * np.minimum(1, t * 6) * np.minimum(1, (d - t) * 8) * 0.5

FXA = np.zeros(N, np.float32)
def put(sig, at_, g=1.0):
    i = int(at_ * SR); j = min(N, i + len(sig))
    if i < N: FXA[i:j] += sig[:j - i] * g

put(boom(1.2), 0.0, 1.0); put(whoosh(0.25, False), 0.0, 0.5)
for p in PEAKS: put(pop(), p, 0.45); put(boom(0.4), p, 0.35)
for s, e, kd, _ in EFFECTS:
    put(whoosh(0.3), s - 0.2, 0.6)
    if kd == "framebreak": put(boom(0.8), s, 0.8)
    elif kd == "dolly": put(vertigo(e - s), s, 0.9)
    elif kd == "paper":
        for j in range(int((e - s) * 10)): put(slap(), s + j * 0.1, 0.12 if j else 0.7)
    elif kd == "orbit": put(whoosh(e - s, False), s, 0.45)
    elif kd == "digital":
        for o in (0, 0.4, 0.8): put(digi(), s + o, 0.8); put(digi(1800), s + o + 0.06, 0.5)
for c in ZT_CUTS: put(whoosh(0.34), c - 0.17, 0.8); put(boom(0.6), c, 0.5)
put(whoosh(0.4), NV / FPS - 0.15, 0.6); put(ding(1318.5), NV / FPS + 0.05, 0.8); put(ding(1760, 0.8), NV / FPS + 0.17, 0.6)

# background beat: 120 bpm, Am-F-C-G, drums drop out under the dolly zoom
beat = 0.5
MUS = np.zeros(N, np.float32)
def kick():
    t = tt(0.3); f = 45 + 110 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
def hat():
    t = tt(0.05); n = rng.standard_normal(len(t)); n = n - lp(n, 0.5); return n * np.exp(-t * 90) * 0.25
roots = [55.0, 43.65, 65.41, 49.0]
chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
quiet = [(s, e) for s, e, kd, _ in EFFECTS if kd == "dolly"]
for b in range(int(DUR / beat) + 1):
    s0 = b * beat
    def mput(sig, at_, g):
        i = int(at_ * SR); j = min(N, i + len(sig))
        if i < N: MUS[i:j] += sig[:j - i] * g
    if not any(s <= s0 < e for s, e in quiet):
        mput(kick(), s0, 0.8); mput(hat(), s0 + beat / 2, 1.0)
    bar = (b // 4) % 4; t = tt(beat); r = roots[bar]
    mput((np.sin(2 * np.pi * r * t) + 0.4 * np.sin(2 * np.pi * 2 * r * t)) * np.exp(-t * 3), s0, 0.35)
    if b % 4 == 0:
        t = tt(4 * beat)
        pad = sum(np.sin(2 * np.pi * f * t) for f in chords[bar]) * np.minimum(1, t * 4) * np.minimum(1, (4 * beat - t) * 4)
        mput(pad.astype(np.float32), s0, 0.05)
env = np.convolve(np.abs(V), np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same"); env /= env.max() + 1e-9
MUS = MUS * (1 - 0.6 * np.clip(env * 4, 0, 1)) * 0.22 * np.where(np.arange(N) / SR >= NV / FPS, 1.8, 1.0)
MUS *= np.minimum(1, (N - np.arange(N)) / (0.4 * SR))

mix = V + FXA * 0.55 + MUS
mix = mix / max(1.0, np.abs(mix).max() / 0.95)
with wave.open(WORK + "/mix.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", WORK + "/video_only.mp4", "-i", WORK + "/mix.wav",
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000", "-ac", "2",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", OUT)
