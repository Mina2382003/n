"""Market-news selfie reel: cold-open verbal hook, breaking-news visual hook, English CTA.

usage: render_reel_IMG_7394.py SRC [OUT] [WORKDIR]
Effects (only what fits the story): Snap Zoom, Headline Storm, Growth Curve (falling), Checklist Pop,
Liquid Glass cards for the English callouts.
"""
import subprocess, numpy as np, wave, math, os, sys
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(S, "reel_7394.mp4")
WORK = sys.argv[3] if len(sys.argv) > 3 else os.path.join(S, "work")
os.makedirs(WORK, exist_ok=True)
FONT = S + "/font/package/900Black/Cairo_900Black.ttf"
FONT_B = S + "/font/package/800ExtraBold/Cairo_800ExtraBold.ttf"
EMO = S + "/emoji/package/img/apple/64/"
W, H, FPS, SR = 1080, 1920, 30, 48000
# night selfie in a car: lift the shadows, tame the noise, then sharpen the upscale
GRADE = ("hqdn3d=2:2:6:6,eq=brightness=0.03:contrast=1.08:saturation=1.12:gamma=1.18,"
         "colorbalance=rs=0.02:bs=-0.03,unsharp=7:7:0.8:5:5:0.0,vignette=PI/5")
YEL, RED, WHITE, BLACK = (255, 214, 0), (235, 30, 45), (255, 255, 255), (0, 0, 0)
GREEN = (40, 210, 120)
FX_, FY_ = 600, 1000                                    # face centre in the upscaled frame

# ---------- timeline (source seconds) ----------
# his phrases; the "و..." (12.25) and "أه" (19.15) fillers are left out, pauses are shortened
PHRASES = [(1.15, 2.05), (2.35, 4.05), (4.95, 6.2), (6.85, 9.8), (10.05, 11.95), (13.65, 14.65), (15.35, 18.25),
           (20.7, 22.2), (22.45, 24.05), (24.65, 27.5), (28.2, 30.7), (31.65, 33.3), (34.1, 38.1), (39.25, 41.15),
           (42.0, 47.25), (47.9, 50.55), (51.05, 52.85), (53.45, 55.0), (55.6, 57.65), (58.0, 58.85), (59.7, 60.8), (61.3, 63.0)]
COLD = (20.62, 24.17)                                   # verbal hook: "نصيحتي محدش ياخد أي قرار"
body = []
for s, e in PHRASES:
    s, e = s - 0.08, e + 0.12
    if body and s - body[-1][1] < 0.25: body[-1] = (body[-1][0], e)
    else: body.append((s, e))
SEGS = [COLD] + body
fr_ = lambda x: int(round(x * FPS))
SEGF = [(fr_(s), fr_(e)) for s, e in SEGS]
OSTART = np.cumsum([0] + [b - a for a, b in SEGF])
NV = int(OSTART[-1])
TAIL = 105
NF = NV + TAIL
DUR = NF / FPS
SIDX = [f for a, b in SEGF for f in range(a, b)]
bH = OSTART[1] / FPS                                    # cold open ends
bC = NV / FPS                                           # speech ends -> CTA

def out_t(src_s):
    """source time inside the body -> output time"""
    f = src_s * FPS
    for k in range(1, len(SEGF)):
        a, b = SEGF[k]
        if f < b: return (OSTART[k] + max(0, f - a)) / FPS
    return bC
print("cold open", round(bH, 2), "body ->", round(bC, 2), "total", round(DUR, 2))

# ---------- camera ----------
def affine(z, cx, cy, sx=0.0, sy=0.0):
    cw, ch = W / z, H / z
    cx = min(max(cx - sx / z, cw / 2), W - cw / 2); cy = min(max(cy - sy / z, ch / 2), H - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2
    return np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])

def warp(a, M):
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

def shake(t, t0, amp, d=0.3):
    k = max(0.0, 1 - (t - t0) / d)
    return amp * k * math.sin(t * 95), amp * 0.8 * k * math.cos(t * 81)

ease_out = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
clamp01 = lambda u: min(max(u, 0.0), 1.0)

# ---------- graphics ----------
_emo, _txt = {}, {}
def emoji(code, size):
    if (code, size) not in _emo:
        _emo[(code, size)] = Image.open(EMO + code + ".png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return _emo[(code, size)]

def font(size, f=FONT): return ImageFont.truetype(f, size)

def text_img(txt, size, fill=WHITE, stroke=0, box=None, fnt=FONT, emo=None, pad=(34, 6), radius=26, maxw=980):
    key = (txt, size, fill, stroke, box, fnt, emo, pad, radius, maxw)
    if key in _txt: return _txt[key]
    f = font(size, fnt)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, stroke_width=stroke)
    tw, th = r - l, b - t
    es = int(size * 1.05) if emo else 0; gap = int(size * 0.2) if emo else 0
    cw = tw + es + gap + (2 * pad[0] if box else 0); ch = max(th, es) + (2 * pad[1] + 16 if box else 0)
    im = Image.new("RGBA", (cw + 24, ch + 24), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    if box:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((18, 21, 18 + cw, 21 + ch), radius, fill=(0, 0, 0, 150))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(4)))
        dr.rounded_rectangle((12, 12, 12 + cw, 12 + ch), radius, fill=box)
    x0 = 12 + (pad[0] if box else 0)
    if emo: im.alpha_composite(emoji(emo, es), (x0, 12 + (ch - es) // 2))
    dr.text((x0 + es + gap - l, 12 + (ch - th) // 2 - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=BLACK)
    if im.width > maxw: im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    _txt[key] = im
    return im

def ease_pop(u):
    if u < 0: return 0
    if u < 0.09: return 0.45 + 0.7 * (u / 0.09)
    if u < 0.18: return 1.15 - 0.15 * ((u - 0.09) / 0.09)
    return 1.0

def paste_center(frame, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def vgrad(w, h, a0, a1, stop=1.0):
    g = np.clip(np.linspace(0, 1, h) / stop, 0, 1)
    return Image.fromarray(np.repeat((a0 + (a1 - a0) * g)[:, None], w, 1).astype(np.uint8), "L")

def glass(fr, box, r=40, tint=(18, 18, 26), ta=0.55, blur=22, border=120):
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    w, h = x1 - x0, y1 - y0
    if w < 8 or h < 8: return
    r = min(r, h // 2, w // 2)
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 54, 40 + w, 54 + h), r, fill=(0, 0, 0, 90))
    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (x0 - 40, y0 - 40))
    reg = Image.blend(fr.crop((x0, y0, x1, y1)).convert("RGB").filter(ImageFilter.GaussianBlur(blur)), Image.new("RGB", (w, h), tint), ta)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    fr.paste(reg, (x0, y0), m)
    sheen = Image.new("RGBA", (w, h), (255, 255, 255, 0)); sheen.putalpha(ImageChops.multiply(vgrad(w, h, 55, 0, 0.5), m))
    fr.alpha_composite(sheen, (x0, y0))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((0, 0, w - 1, h - 1), r, outline=(255, 255, 255, border), width=3)
    fr.alpha_composite(ov, (x0, y0))

def glass_text(fr, im, cx, cy, s=1.0, tint=(18, 18, 26), ta=0.55):
    if s <= 0.01: return
    bw, bh = (im.width + 50) * s, (im.height + 18) * s
    glass(fr, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), r=int(min(bh / 2, 44)), tint=tint, ta=ta)
    paste_center(fr, im, cx, cy, s)

def flash(fr, col, a):
    if a > 0: fr.alpha_composite(Image.new("RGBA", (W, H), col + (int(255 * min(1, a)),)))

# ---------- visual hook: breaking banner + market ticker ----------
BANNER = text_img("BREAKING", 54, fill=WHITE, box=RED, emo="1f6a8", pad=(26, 2), radius=12)
HOOK_TOP = text_img("Egypt's stock market", 76, fill=WHITE, stroke=8)
HOOK_TOP2 = text_img("just HALTED trading", 92, fill=YEL, stroke=9)
TICK_TXT = "   EGX  ▼  TRADING HALTED 30 MIN   •   GOLD ?   •   FED RATE DECISION THURSDAY   •   EGX  ▼  "
_tf = font(40, FONT_B)
_tw = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(TICK_TXT, font=_tf))
TICKER = Image.new("RGBA", (_tw * 2, 70), (0, 0, 0, 0))
_d = ImageDraw.Draw(TICKER)
for k in range(2): _d.text((k * _tw, 6), TICK_TXT, font=_tf, fill=WHITE)
def ticker(fr, t, y):
    bar = Image.new("RGBA", (W, 70), (12, 12, 16, 230)); ImageDraw.Draw(bar).rectangle((0, 0, 190, 70), fill=RED)
    ImageDraw.Draw(bar).text((22, 6), "LIVE", font=_tf, fill=WHITE)
    off = int(t * 260) % _tw
    bar.alpha_composite(TICKER.crop((off, 0, off + W - 190, 70)), (190, 0))
    fr.alpha_composite(bar, (0, y))
VERBAL = text_img("“My advice: make NO decision right now.”", 58, fill=WHITE, emo="270b")

# ---------- headline storm ----------
def headline(txt, tag):
    f = font(54); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    w, h = r - l + 70, b - t + 104
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((18, 22, w + 18, h + 22), fill=(0, 0, 0, 130))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    dr.rectangle((10, 10, w + 10, h + 10), fill=(246, 241, 228)); dr.rectangle((10, 10, w + 10, 50), fill=RED)
    dr.text((28, 12), tag, font=font(26, FONT_B), fill=WHITE)
    dr.text((10 + 35 - l, 60 - t + 8), txt, font=f, fill=(15, 15, 15))
    return im
HEADLINES = [   # source time, card, x, y, rotation
    (4.95, headline("EGX HALTS TRADING", "BREAKING"), 360, 330, 6),
    (6.85, headline("30-MINUTE SUSPENSION", "MARKETS"), 700, 520, -5),
    (10.05, headline("INVESTORS ON EDGE", "TODAY"), 420, 700, 4),
]

# ---------- falling curve ----------
CARD = (70, 230, 1010, 760)
def draw_fall(fr, t, t0, t1):
    x0, y0, x1, y1 = CARD
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx0, cy0, cx1, cy1 = 60, 120, x1 - x0 - 60, y1 - y0 - 50
    for i in range(5):
        yy = cy0 + (cy1 - cy0) * i / 4; d.line((cx0, yy, cx1, yy), fill=(255, 255, 255, 30), width=2)
    d.text((cx0, 22), "EGX", font=font(46, FONT_B), fill=WHITE)
    p = clamp01((t - t0) / (t1 - t0))
    tag = text_img("▼ FALLING", 34, fill=WHITE, box=RED, fnt=FONT_B, pad=(16, 0), radius=12)
    lay.alpha_composite(tag, (cx1 - tag.width + 12, 18))
    rng = np.random.default_rng(4)
    xs = np.linspace(0, 1, 120)
    ys = 0.15 + 0.75 * xs ** 1.6 + 0.05 * np.sin(xs * 23) * (1 - xs) + 0.02 * rng.standard_normal(len(xs))
    pts = [(cx0 + (cx1 - cx0) * x, cy0 + (cy1 - cy0) * min(1, y)) for x, y in zip(xs, ys) if x <= p]
    glow = Image.new("RGBA", lay.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    if len(pts) > 1:
        d.polygon(pts + [(pts[-1][0], cy1), (cx0, cy1)], fill=(255, 59, 48, 45))
        gd.line(pts, fill=(255, 59, 48, 255), width=22, joint="curve"); d.line(pts, fill=(255, 59, 48, 255), width=9, joint="curve")
        ex, ey = pts[-1]; d.ellipse((ex - 11, ey - 11, ex + 11, ey + 11), fill=WHITE)
    fr.alpha_composite(Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)), lay), (x0, y0))

# ---------- checklist ----------
CHK_TITLE = text_img("2 things to watch this week", 50, fill=YEL, fnt=FONT, emo="1f440")
CHK = [
    (34.1, "1", "Tomorrow", "Parliament: military involvement?"),
    (42.0, "2", "Thursday", "US Fed: hold, hike or cut rates?"),
]
def chk_item(num, when, what):
    im = Image.new("RGBA", (900, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 25, 100, 125), fill=YEL); d.text((50, 75), num, font=font(60), fill=BLACK, anchor="mm")
    d.text((128, 12), when.upper(), font=font(40, FONT_B), fill=YEL)
    d.text((128, 62), what, font=font(46, FONT_B), fill=WHITE)
    bb = im.getbbox(); return im.crop((0, 0, bb[2] + 10, 150))
CHK_IMG = [chk_item(*c[1:]) for c in CHK]
FED_BET = text_img("His bet: the Fed holds rates", 40, fill=BLACK, box=YEL, fnt=FONT_B, emo="1f914", pad=(20, 2), radius=16)

# ---------- English callouts (glass cards) ----------
CALLOUTS = [   # source start, end, image
    (1.07, 4.17, text_img("The world is upside down today", 56, emo="1f30d")),
    (20.62, 24.17, text_img("My advice: make NO decision", 60, emo="270b")),
    (24.57, 27.62, text_img("Don't invest. Don't sell. Not even gold.", 50, emo="1f6ab")),
    (28.12, 33.42, text_img("Wait until the end of the week", 56, emo="23f3")),
    (55.52, 58.97, text_img("All of this will hit your money", 56, emo="1f4b8")),
    (59.62, 60.92, text_img("So don't decide yet.", 64, fill=YEL, emo="1f6d1")),
    (61.22, 63.12, text_img("Wait and see where it goes.", 60, emo="1f440")),
]
PUNCHES = [20.7, 24.65, 59.7]                            # snap punch-ins (source time)

# ---------- CTA ----------
CTA1 = text_img("Don't miss Thursday's", 84, fill=WHITE, stroke=9)
CTA2 = text_img("Fed decision", 104, fill=YEL, stroke=10)
CTA3 = text_img("Follow for the market update", 66, fill=WHITE, box=RED, emo="1f514", pad=(40, 10), radius=60)
CTA4 = text_img("Save this & send it to someone about to invest", 40, fill=BLACK, box=WHITE, fnt=FONT_B, emo="1f4cc", pad=(24, 4), radius=24)
NFA = text_img("Not financial advice", 30, fill=(220, 220, 220), fnt=FONT_B)

# ---------- render ----------
class Frames:
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=lanczos," + GRADE + ",format=rgb24",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.cache, self.next = {}, 0
    def __getitem__(self, i):
        if i in self.cache: return self.cache[i]
        if i < self.next:                                # the cold open looks ahead: restart for the body
            self.p.kill(); self.__init__()
        while self.next <= i:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: return self.cache[max(self.cache)]
            self.cache[self.next] = np.frombuffer(b, np.uint8).reshape(H, W, 3); self.next += 1
            for k in [k for k in self.cache if k < self.next - 10]: del self.cache[k]
        return self.cache[i]
FRAMES = Frames()
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        WORK + "/video_only.mp4"], stdin=subprocess.PIPE)
PREVIEW = [float(x) for x in os.environ.get("FX_PREVIEW", "").split(",") if x]
P_OUT = [out_t(p) for p in PUNCHES[1:]] + [0.0]
HL = [(out_t(s), im, x, y, r) for s, im, x, y, r in HEADLINES]
FALL = (out_t(13.57), out_t(18.37))
CHK_T = [out_t(c[0]) for c in CHK]
CHK_END = out_t(53.4); BET_T = out_t(53.45)
CO = [(0.0, bH, VERBAL)] + [(out_t(s), out_t(e), im) for s, e, im in CALLOUTS if s != 20.62]
end_bg = None
for n in range(NF):
    t = n / FPS
    si = SIDX[min(n, NV - 1)]
    src = FRAMES[si]
    if n < NV:
        z, cy = 1.12, FY_
        k = int(np.searchsorted(OSTART, n, side="right") - 1)
        u = (n - OSTART[k]) / FPS
        z *= 1 + 0.08 * (1 - ease_out(u / 0.12)) if k else 1
        z *= 1 + 0.015 * u
        sx = sy = 0.0
        for p in P_OUT:
            if p <= t < p + 0.7:
                z *= 1 + 0.22 * ease_out((t - p) / 0.07) * (1 - clamp01((t - p - 0.5) / 0.2)); sx, sy = shake(t, p, 14)
        if t < bH:                                       # cold open: hard snap onto his face
            z = 1.55 + 0.5 * (1 - ease_out(t / 0.15)) + 0.04 * t; cy = FY_ - 60; sx, sy = shake(t, 0, 20, 0.35)
        if CHK_T[0] <= t < CHK_END: z, cy = 1.05, FY_ + 160    # wider so the checklist has room above him
        arr = warp(src, affine(z, FX_, cy, sx, sy))
        fr = Image.fromarray(arr).convert("RGBA")

        if t < bH:
            # visual hook: red alert wash, BREAKING banner, headline, live ticker
            flash(fr, (255, 0, 0), 0.18 * (0.5 + 0.5 * math.sin(t * 9)))
            paste_center(fr, BANNER, W / 2, 210, ease_pop(t), -2)
            paste_center(fr, HOOK_TOP, W / 2, 330, ease_pop(t - 0.08))
            paste_center(fr, HOOK_TOP2, W / 2, 440, ease_pop(t - 0.16), 2)
            ticker(fr, t, 12)
            flash(fr, WHITE, 0.85 * (1 - t / 0.12))
        for hs, im, x, y, r in HL:
            if hs <= t < FALL[0] - 0.1:
                paste_center(fr, im, x, y, 2.0 - ease_out((t - hs) / 0.1), r)
        if FALL[0] <= t < FALL[1]:
            e = ease_pop((t - FALL[0]) * 0.8)
            x0, y0, x1, y1 = CARD; cx, ccy = (x0 + x1) / 2, (y0 + y1) / 2
            glass(fr, (cx - (cx - x0) * e, ccy - (ccy - y0) * e, cx + (x1 - cx) * e, ccy + (y1 - ccy) * e), r=44, ta=0.6)
            if t > FALL[0] + 0.08: draw_fall(fr, t, FALL[0] + 0.1, FALL[1] - 0.6)
        if CHK_T[0] <= t < CHK_END:
            glass(fr, (50, 150, 1030, 700), r=44, ta=0.62)
            paste_center(fr, CHK_TITLE, W / 2, 230, ease_pop(t - CHK_T[0]))
            for i, (ct, im) in enumerate(zip(CHK_T, CHK_IMG)):
                if t >= ct: paste_center(fr, im, 90 + im.width / 2, 390 + i * 170, ease_pop(t - ct))
        if BET_T <= t < out_t(55.5):
            paste_center(fr, FED_BET, W / 2, 470, ease_pop(t - BET_T), -2)
        for cs, ce, im in CO:
            if cs <= t < ce:
                glass_text(fr, im, W / 2, 1580 if t >= bH else 1600, ease_pop(t - cs))
        if any(p <= t < p + 0.1 for p in P_OUT[:-1]): flash(fr, WHITE, 0.35)
    else:
        u = t - bC
        if end_bg is None:
            end_bg = (cv2.GaussianBlur(warp(src, affine(1.3, FX_, FY_)), (0, 0), 20) * 0.45).astype(np.uint8)
        fr = Image.fromarray(warp(end_bg, affine(1 + 0.04 * u / (TAIL / FPS), 540, 960))).convert("RGBA")
        paste_center(fr, CTA1, W / 2, 620, ease_pop(u - 0.02))
        paste_center(fr, CTA2, W / 2, 760, ease_pop(u - 0.2), -2)
        if u >= 0.6:
            paste_center(fr, CTA3, W / 2, 1020, ease_pop(u - 0.6) * (1 + 0.04 * math.sin((u - 0.6) * 12)))
            paste_center(fr, emoji("1f446", 110), W / 2 + 330, 1160 + 14 * math.sin(t * 10), ease_pop(u - 0.75))
        if u >= 1.1: paste_center(fr, CTA4, W / 2, 1290, ease_pop(u - 1.1))
        paste_center(fr, NFA, W / 2, 1800, 1.0, 0, clamp01((u - 0.3) / 0.3))
        flash(fr, WHITE, 0.8 * (1 - u / 0.15))
    dr = ImageDraw.Draw(fr)
    if t >= bH or n >= NV:
        dr.rectangle((0, 0, W, 12), fill=(0, 0, 0, 110)); dr.rectangle((0, 0, int(W * (n + 1) / NF), 12), fill=YEL + (255,))
    out = fr.convert("RGB")
    if any(abs(t - p) < 0.5 / FPS for p in PREVIEW): out.save(f"{WORK}/prev_{t:05.2f}.jpg", quality=85)
    enc.stdin.write(out.tobytes())
    if n % 300 == 0: print("frame", n, "/", NF, flush=True)
enc.stdin.close(); enc.wait(); FRAMES.p.kill()

# ---------- audio ----------
at = ";".join(f"[0:a:0]atrim={a/FPS}:{b/FPS},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={(b-a)/FPS-0.015}:d=0.015[a{i}]"
              for i, (a, b) in enumerate(SEGF))
afc = (f"{at};{''.join(f'[a{i}]' for i in range(len(SEGF)))}concat=n={len(SEGF)}:v=0:a=1,aformat=channel_layouts=mono,"
       "highpass=f=90,afftdn=nr=12:nf=-45:tn=1,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1:g=3,"
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

def alarm(d=0.9):
    t = tt(d); f = np.where((t * 4).astype(int) % 2 == 0, 880, 660)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.22 * np.minimum(1, (d - t) * 10)

def slap():
    t = tt(0.14); n = rng.standard_normal(len(t))
    return (n - lp(n, 0.3)) * np.exp(-t * 45) * 0.6 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30) * 0.6

def fall_tone(d):
    t = tt(d); f = 900 * 2 ** (-2.5 * t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.18 * np.minimum(1, t * 10) * np.minimum(1, (d - t) * 10)

FXA = np.zeros(N, np.float32)
def put(sig, at_, g=1.0):
    i = int(at_ * SR); j = min(N, i + len(sig))
    if i < N: FXA[i:j] += sig[:j - i] * g

put(boom(1.2), 0.0, 1.0); put(alarm(), 0.0, 0.5); put(whoosh(0.3, False), bH - 0.15, 0.6)
for hs, *_ in HL: put(slap(), hs, 0.8)
put(whoosh(0.3), FALL[0] - 0.1, 0.5); put(fall_tone(FALL[1] - FALL[0] - 0.7), FALL[0] + 0.1, 0.8)
for ct in CHK_T: put(pop(), ct, 0.6); put(ding(1568, 0.4), ct + 0.02, 0.4)
put(pop(), BET_T, 0.4)
for cs, ce, im in CO[1:]: put(pop(), cs, 0.35)
for p in P_OUT[:-1]: put(boom(0.6), p, 0.6); put(whoosh(0.2), p - 0.1, 0.4)
put(whoosh(0.4), bC - 0.15, 0.6); put(ding(1318.5), bC + 0.6, 0.8); put(ding(1760, 0.8), bC + 0.72, 0.6)

# tense news bed: 100 bpm, minor pulse
beat = 0.6
MUS = np.zeros(N, np.float32)
def kick():
    t = tt(0.3); f = 45 + 110 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
def tick():
    t = tt(0.04); n = rng.standard_normal(len(t)); n = n - lp(n, 0.5); return n * np.exp(-t * 120) * 0.2
roots = [55.0, 55.0, 43.65, 49.0]
for b in range(int(DUR / beat) + 1):
    s0 = b * beat
    def mput(sig, at_, g):
        i = int(at_ * SR); j = min(N, i + len(sig))
        if i < N: MUS[i:j] += sig[:j - i] * g
    mput(kick(), s0, 0.6 if b % 2 == 0 else 0.3)
    for q in (0.25, 0.5, 0.75): mput(tick(), s0 + beat * q, 1.0)
    t = tt(beat); r = roots[(b // 4) % 4]
    mput((np.sin(2 * np.pi * r * t) + 0.3 * np.sin(2 * np.pi * 2 * r * t)) * np.exp(-t * 2.5), s0, 0.35)
    if b % 8 == 0:
        t = tt(8 * beat)
        pad = sum(np.sin(2 * np.pi * f * t) for f in (220, 261.6, 329.6)) * np.minimum(1, t) * np.minimum(1, (8 * beat - t) * 2)
        mput(pad.astype(np.float32), s0, 0.035)
env = np.convolve(np.abs(V), np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same"); env /= env.max() + 1e-9
MUS = MUS * (1 - 0.6 * np.clip(env * 4, 0, 1)) * 0.2 * np.where(np.arange(N) / SR >= bC, 1.8, 1.0)
MUS *= np.minimum(1, (N - np.arange(N)) / (0.5 * SR))

mix = V + FXA * 0.55 + MUS
mix = mix / max(1.0, np.abs(mix).max() / 0.95)
with wave.open(WORK + "/mix.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", WORK + "/video_only.mp4", "-i", WORK + "/mix.wav",
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11,aresample=48000", "-ac", "2",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", OUT)
