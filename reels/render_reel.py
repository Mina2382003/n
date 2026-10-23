import subprocess, numpy as np, wave, math, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))
SRC = "/root/.claude/uploads/774937ae-ec8b-5983-80fd-05069d741008/e8c961d6-IMG_7053.mov"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(S, "reel.mp4")
FONT = S + "/font/package/900Black/Cairo_900Black.ttf"
FONT_B = S + "/font/package/800ExtraBold/Cairo_800ExtraBold.ttf"
EMO = S + "/emoji/package/img/apple/64/"
W, H, FPS, SR = 1080, 1920, 30, 48000
GRADE = ("curves=all='0/0 0.25/0.19 0.5/0.46 0.75/0.73 1/0.94',eq=contrast=1.12:saturation=1.38:gamma=0.97,"
         "colorbalance=rs=0.04:bs=-0.04:rm=0.07:gm=0.01:bm=-0.05,unsharp=5:5:0.7,vignette=PI/4.5")

# source segments in frames (jump cuts remove dead air + the "faaa" filler)
SEGS = [(18, 116), (159, 278), (402, 498)]
TAIL = 66
NSEG = sum(b - a for a, b in SEGS)
NF = NSEG + TAIL
DUR = NF / FPS
bA = (SEGS[0][1] - SEGS[0][0]) / FPS              # 3.267
bB = bA + (SEGS[1][1] - SEGS[1][0]) / FPS         # 7.233
bC = bB + (SEGS[2][1] - SEGS[2][0]) / FPS         # 10.433
print("cut points", bA, bB, bC, "total", DUR)

YEL, RED, WHITE, BLACK = (255, 230, 0), (235, 30, 45), (255, 255, 255), (0, 0, 0)

# ---------- graphics helpers ----------
_emo = {}
def emoji(code, size):
    k = (code, size)
    if k not in _emo:
        _emo[k] = Image.open(EMO + code + ".png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return _emo[k]

def text_img(txt, size, fill=WHITE, stroke=10, box=None, pad=(34, 6), font=FONT, emo=None, emo_left=True, radius=26):
    f = ImageFont.truetype(font, size)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    tw, th = r - l, b - t
    es = int(size * 1.05) if emo else 0
    gap = int(size * 0.18) if emo else 0
    cw = tw + es + gap + (2 * pad[0] if box else 0)
    ch = max(th, es) + (2 * pad[1] + 16 if box else 0)
    im = Image.new("RGBA", (cw + 24, ch + 24), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    ox, oy = 12, 12
    if box:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((ox + 6, oy + 9, ox + cw + 6, oy + ch + 9), radius, fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
        dr.rounded_rectangle((ox, oy, ox + cw, oy + ch), radius, fill=box)
    x0 = ox + (pad[0] if box else 0)
    tx = x0 + (es + gap if (emo and emo_left) else 0)
    ty = oy + (ch - th) // 2
    dr.text((tx - l, ty - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=BLACK)
    if emo:
        ex = x0 if emo_left else tx + tw + gap
        im.alpha_composite(emoji(emo, es), (ex, oy + (ch - es) // 2))
    if im.width > 960:  # keep inside the reel safe width
        im = im.resize((960, int(im.height * 960 / im.width)), Image.LANCZOS)
    return im

def ease_pop(u):
    # 0 -> overshoot 1.15 -> settle 1.0
    if u < 0: return 0
    if u < 0.09: return 0.45 + (1.15 - 0.45) * (u / 0.09)
    if u < 0.18: return 1.15 - 0.15 * ((u - 0.09) / 0.09)
    return 1.0

def paste_center(frame, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------- overlay timeline (output seconds) ----------
CAP_Y = 1545
caps = [  # start, end, image, rotation
    (0.10, 0.80, text_img("ده اسمه", 120), 0),
    (0.80, 1.75, text_img("OVERBOOKING", 128, fill=BLACK, stroke=0, box=YEL, emo="1f92f", emo_left=False), -4),
    (1.75, 2.50, text_img("وفي الـ Stage", 120), 0),
    (2.50, bA, text_img("اللي احنا فيها", 120), 0),
    (bA + 0.05, 4.45, text_img("في الماركت", 120, fill=YEL), 0),
    (4.45, 4.97, text_img("يعني", 120), 0),
    (4.97, 5.57, text_img("للأسف", 130, fill=WHITE, stroke=0, box=RED, emo="1f62c"), 3),
    (5.57, 6.17, text_img("الـ Restaurants", 120, fill=YEL, emo="1f37d-fe0f"), 0),
    (6.17, 6.57, text_img("مضطرة", 125), 0),
    (6.57, bB, text_img("تعمل كده!", 125, fill=YEL), 0),
    (bB + 0.05, 8.13, text_img("ودي مش", 120), 0),
    (8.13, 8.93, text_img("مشكلتهم", 130, fill=WHITE, stroke=0, box=RED, emo="274c"), -3),
    (8.93, 9.78, text_img("دي مشكلة", 120), 0),
    (9.78, bC, text_img("الـ CUSTOMER", 135, fill=BLACK, stroke=0, box=YEL, emo="1f440", emo_left=False), 4),
]
hook1 = text_img("حجزت في مطعم..", 92, fill=BLACK, stroke=0, box=WHITE)
hook2 = text_img("ومالقتش ترابيزة؟!", 100, fill=WHITE, stroke=0, box=RED, emo="1f631")
mid = text_img("طب الغلطة غلطة مين؟", 92, fill=BLACK, stroke=0, box=YEL, emo="1f914")
cta1 = text_img("إنت مع مين؟", 150, fill=YEL, stroke=12, emo="1f914")
cta2 = text_img("المطعم ولا الـ Customer؟", 96, fill=WHITE, stroke=9)
cta3 = text_img("اكتب رأيك في الكومنتات", 82, fill=BLACK, stroke=0, box=WHITE, emo="1f447")
cta4 = text_img("تابعني لأسرار البيزنس", 88, fill=WHITE, stroke=0, box=RED, emo="1f525", radius=60, pad=(46, 10))

# ---------- camera moves ----------
def cam(t):
    """returns zoom, crop-center x, crop-center y, shake x, shake y"""
    sx = sy = 0.0
    if t < bA:
        z = 1.35 - 0.23 * min(1, t / 0.25) if t < 0.25 else 1.12 + 0.06 * (t - 0.25) / (bA - 0.25)
        cy = 1050
        if 0.80 <= t < 1.12:
            k = 1 - (t - 0.80) / 0.32; sx, sy = 26 * k * math.sin(t * 95), 20 * k * math.cos(t * 81)
    elif t < 4.97:
        u = (t - bA) / (4.97 - bA); z = 1.0 + 0.06 * u; cy = 980
    elif t < bB:
        u = (t - 4.97) / (bB - 4.97); z = 1.22 + 0.06 * u; cy = 1100
    elif t < 9.78:
        u = (t - bB) / (9.78 - bB); z = 1.10 + 0.06 * u; cy = 1050
    else:
        z = 1.62 - 0.17 * min(1, (t - 9.78) / 0.12); cy = 1040
        k = max(0, 1 - (t - 9.78) / 0.4); sx, sy = 30 * k * math.sin(t * 90), 24 * k * math.cos(t * 77)
    return z, 520, cy, sx, sy

def transform(img, z, cx, cy, sx, sy):
    cw, ch = W / z, H / z
    cx = min(max(cx - sx / z, cw / 2), W - cw / 2); cy = min(max(cy - sy / z, ch / 2), H - ch / 2)
    return img.resize((W, H), Image.BILINEAR, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))

# ---------- decode graded segments ----------
trims = ";".join(f"[0:v]trim=start_frame={a}:end_frame={b},setpts=PTS-STARTPTS[v{i}]" for i, (a, b) in enumerate(SEGS))
fc = f"{trims};{''.join(f'[v{i}]' for i in range(len(SEGS)))}concat=n={len(SEGS)}:v=1:a=0,{GRADE},format=rgb24[o]"
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-filter_complex", fc, "-map", "[o]", "-f", "rawvideo", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                        S + "/video_only.mp4"], stdin=subprocess.PIPE)

last = None
for n in range(NF):
    t = n / FPS
    if n < NSEG:
        raw = dec.stdout.read(W * H * 3)
        src = Image.frombytes("RGB", (W, H), raw)
        last = src
        fr = transform(src, *cam(t)).convert("RGBA")
    else:
        # CTA end card: frozen last frame, blurred & darkened, slow push
        u = (t - bC) / (DUR - bC)
        if n == NSEG:
            bg = transform(last, 1.2, 520, 1040, 0, 0).filter(ImageFilter.GaussianBlur(22))
            bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.5)
        fr = transform(bg, 1.0 + 0.05 * u, 540, 960, 0, 0).convert("RGBA")

    # flashes
    for ft, col, dur, a0 in [(0.0, WHITE, 0.18, 0.85), (9.78, (255, 40, 40), 0.22, 0.55), (bC, WHITE, 0.15, 0.8)]:
        if ft <= t < ft + dur:
            fr.alpha_composite(Image.new("RGBA", (W, H), col + (int(255 * a0 * (1 - (t - ft) / dur)),)))

    # captions
    for st, en, im, rot in caps:
        if st <= t < en:
            paste_center(fr, im, W / 2, CAP_Y, ease_pop(t - st), rot)

    # opening hook (top)
    if t < bA:
        paste_center(fr, hook1, W / 2, 300, ease_pop(t))
        wob = 2.5 * math.sin(t * 9)
        paste_center(fr, hook2, W / 2, 440, ease_pop(t - 0.12), wob)
    # mid-video re-hook
    if bB <= t < 9.78:
        paste_center(fr, mid, W / 2, 330, ease_pop(t - bB), 2 * math.sin(t * 8))

    # CTA
    if t >= bC:
        paste_center(fr, cta1, W / 2, 560, ease_pop(t - bC - 0.02))
        paste_center(fr, cta2, W / 2, 760, ease_pop(t - bC - 0.30))
        paste_center(fr, cta3, W / 2, 1010, ease_pop(t - bC - 0.65))
        if t >= bC + 1.0:
            pulse = ease_pop(t - bC - 1.0) * (1 + 0.05 * math.sin((t - bC - 1.0) * 12))
            paste_center(fr, cta4, W / 2, 1240, pulse)
            hand = emoji("1f446", 120)  # pointing up at the follow button
            paste_center(fr, hand, W / 2 + 230, 1385 + 18 * math.sin(t * 10), ease_pop(t - bC - 1.15))

    # retention progress bar
    dr = ImageDraw.Draw(fr)
    dr.rectangle((0, 0, W, 14), fill=(0, 0, 0, 110))
    dr.rectangle((0, 0, int(W * (n + 1) / NF), 14), fill=YEL + (255,))

    enc.stdin.write(fr.convert("RGB").tobytes())
    if n % 60 == 0: print("frame", n, "/", NF, flush=True)
enc.stdin.close(); enc.wait(); dec.wait()

# ---------- audio ----------
# voice: same cuts, 12ms micro-fades at each cut, light cleanup (no gate: it clips word endings)
at = ";".join(f"[0:a]atrim={a/FPS}:{b/FPS},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={(b-a)/FPS-0.015}:d=0.015[a{i}]"
              for i, (a, b) in enumerate(SEGS))
afc = (f"{at};{''.join(f'[a{i}]' for i in range(len(SEGS)))}concat=n={len(SEGS)}:v=0:a=1,pan=mono|c0=0.5*c0+0.5*c1,"
       "highpass=f=80,afftdn=nr=8:nf=-42,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1:g=3.5,"
       "highshelf=f=8000:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", afc, "-map", "[o]", "-ar", str(SR), S + "/voice.wav"], check=True)
w = wave.open(S + "/voice.wav"); voice = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
N = int(DUR * SR)
V = np.zeros(N, np.float32); V[:min(N, len(voice))] = voice[:N]
rng = np.random.default_rng(7)
tt = lambda d: np.arange(int(d * SR)) / SR

def lp(x, a):  # one-pole low-pass
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y

def boom(d=1.1):
    t = tt(d); f = 32 + 90 * np.exp(-t * 9)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    s += 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 60)
    return np.tanh(s * 2.2) * 0.9

def whoosh(d=0.45, up=True):
    t = tt(d); n = rng.standard_normal(len(t))
    env = np.sin(np.pi * t / d) ** 2
    out = np.zeros_like(n); ph = 0
    # sweep a resonant band through the noise with a time-varying 2-pole filter
    y1 = y2 = 0.0
    for i in range(len(n)):
        fc = (300 + 4200 * (t[i] / d)) if up else (4500 - 4200 * (t[i] / d))
        r = 0.97; th = 2 * np.pi * fc / SR
        y = n[i] * (1 - r) + 2 * r * np.cos(th) * y1 - r * r * y2
        y2, y1 = y1, y; out[i] = y
    return out / (np.abs(out).max() + 1e-9) * env * 0.7

def pop(d=0.08):
    t = tt(d); f = 900 * np.exp(-t * 40) + 250
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 55) * 0.5

def ding(f0=1318.5, d=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * t) + 0.25 * np.sin(2 * np.pi * f0 * 2.01 * t)) * np.exp(-t * 5) * 0.3

def buzzer(d=0.42):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * 140 * t)) + 0.6 * np.sign(np.sin(2 * np.pi * 147 * t))
    return lp(s.astype(np.float32), 0.25) * np.minimum(1, (d - t) * 25) * 0.28

def riser(d):
    t = tt(d); f = 200 * (2 ** (t / d * 3))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + 0.25 * rng.standard_normal(len(t)) * (t / d)
    return s * (t / d) ** 2 * 0.6

def shutter():
    t = tt(0.12); return rng.standard_normal(len(t)) * (np.exp(-t * 80) + 0.6 * np.exp(-np.abs(t - 0.06) * 150)) * 0.35

FX = np.zeros(N, np.float32)
def put(sig, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(sig)); FX[i:j] += sig[:j - i] * g

put(whoosh(0.35), 0.0, 0.8); put(boom(), 0.0, 0.9)
put(boom(), 0.80, 0.85); put(whoosh(0.3, False), 0.78, 0.4)
for c in [1.75, 2.50, bA + 0.05, 4.45, 5.57, 6.17, 6.57, bB + 0.05, 8.93]:
    put(pop(), c, 0.45)
put(whoosh(0.35), bA - 0.12, 0.6)
put(boom(0.6), 4.97, 0.45); put(pop(), 4.97, 0.5)
put(whoosh(0.35), bB - 0.12, 0.6); put(ding(988, 0.6), bB + 0.02, 0.6)
put(buzzer(), 8.13, 0.8)
put(riser(9.78 - 8.95), 8.95, 0.7)
put(boom(1.3), 9.78, 1.0); put(whoosh(0.3, False), 9.74, 0.5)
put(whoosh(0.4), bC - 0.15, 0.6); put(shutter(), bC, 0.9)
for c in [bC + 0.30, bC + 0.65]: put(pop(), c, 0.5)
put(ding(1318.5), bC + 1.0, 0.8); put(ding(1760, 0.8), bC + 1.12, 0.6)

# background beat: 120 bpm, Am-F-C-G bass, kick + offbeat hats + soft pad
bpm = 120; beat = 60 / bpm
M = np.zeros(N, np.float32)
def kick():
    t = tt(0.3); f = 45 + 110 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
def hat():
    t = tt(0.05); n = rng.standard_normal(len(t)); n = n - lp(n, 0.5); return n * np.exp(-t * 90) * 0.25
roots = [55.0, 43.65, 65.41, 49.0]           # A1 F1 C2 G1
chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
nb = int(DUR / beat) + 1
for b in range(nb):
    s0 = b * beat
    def mput(sig, at, g):
        i = int(at * SR); j = min(N, i + len(sig))
        if i < N: M[i:j] += sig[:j - i] * g
    mput(kick(), s0, 0.8)
    mput(hat(), s0 + beat / 2, 1.0)
    bar = (b // 4) % 4
    t = tt(beat); r = roots[bar]
    bass = (np.sin(2 * np.pi * r * t) + 0.4 * np.sin(2 * np.pi * 2 * r * t)) * np.exp(-t * 3)
    mput(bass, s0, 0.35)
    if b % 4 == 0:
        t = tt(4 * beat)
        pad = sum(np.sin(2 * np.pi * f * t) for f in chords[bar]) * np.minimum(1, t * 4) * np.minimum(1, (4 * beat - t) * 4)
        mput(pad.astype(np.float32), s0, 0.05)
# duck music under the voice
env = np.abs(V); k = int(0.03 * SR)
env = np.convolve(env, np.ones(k) / k, mode="same"); env = env / (env.max() + 1e-9)
duck = 1 - 0.6 * np.clip(env * 4, 0, 1)
tail_boost = np.where(np.arange(N) / SR >= bC, 1.8, 1.0)
M = M * duck * 0.22 * tail_boost
fade = np.minimum(1, (N - np.arange(N)) / (0.4 * SR)); M *= fade

mix = V + FX * 0.55 + M
mix = mix / max(1.0, np.abs(mix).max() / 0.95)
with wave.open(S + "/mix.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", S + "/video_only.mp4", "-i", S + "/mix.wav",
                "-af", "loudnorm=I=-12.6:TP=-1.0:LRA=11,aresample=48000", "-ac", "2",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", OUT)
