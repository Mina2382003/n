"""EIP event reels: verbal hook (his own line as a cold open), visual hook, content-matched effects, English CTA.

usage: render_event_reel.py CLIP SRC OUT WORKDIR
CLIP is a key of CONFIG; WORKDIR holds masks.npy (540x960 person masks per source frame) for the frame break.
All times in CONFIG are source seconds, taken from the transcript and the speech envelope.
"""
import subprocess, numpy as np, wave, math, os, sys
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = os.path.dirname(os.path.abspath(__file__))
CLIP, SRC, OUT, WORK = sys.argv[1:5]
FONT = S + "/font/package/900Black/Cairo_900Black.ttf"
FONT_B = S + "/font/package/800ExtraBold/Cairo_800ExtraBold.ttf"
EMO = S + "/emoji/package/img/apple/64/"
W, H, FPS, SR = 1080, 1920, 30, 48000
GRADE = "eq=contrast=1.1:saturation=1.18:gamma=0.98,colorbalance=rm=0.03:bm=-0.02,unsharp=7:7:0.9:5:5:0.0,vignette=PI/5"
YEL, RED, WHITE, BLACK, GREEN = (255, 214, 0), (235, 30, 45), (255, 255, 255), (0, 0, 0), (37, 211, 102)

CONFIG = {
    "clip_00": dict(   # founder intro: Reservya
        cold=(12.30, 16.25),
        body=[(4.5, 7.52), (8.15, 9.97), (10.1, 11.57), (12.05, 16.27), (20.5, 22.37), (22.5, 25.77), (28.15, 29.82)],
        hook_quote=("“We own the whole journey —", "from the moment you think of booking.”"),
        visual="phone", hook_title=("From “where should we eat?”", "to your table."),
        lower_third=(4.5, 7.5, "Mina Mounir", "Founder, Reservya"),
        chips=(12.05, 16.27, [("1f4ad", "Think"), ("1f4f1", "Book"), ("1f697", "Arrive"), ("1f37d-fe0f", "Enjoy")]),
        callouts=[(20.5, 25.77, "EIP: where founders meet investors", "1f91d"), (28.15, 29.82, "…and the people building startups", "1f680")],
        punches=[12.05, 20.5],
        cta=("Building something big?", "Follow the Reservya journey", "1f680", "Tag a founder in F&B"),
    ),
    "clip_01": dict(   # why EIP
        cold=(22.42, 24.62),
        body=[(0.55, 2.17), (2.6, 4.32), (11.85, 14.62), (15.1, 17.27), (19.15, 24.67), (26.8, 29.02)],
        hook_quote=("“…it helps you", "land an INVESTOR.”"),
        visual="title", hook_title=("How do founders land", "their first INVESTOR?"), hook_emo="1f4b0",
        checklist=("5 reasons founders join EIP", [(0.55, "Meet people — international, not just local"),
                                                (11.85, "Get real direction"),
                                                (19.15, "Know which investment fits you"),
                                                (22.45, "Get connected to investors"),
                                                (26.8, "Discover the programs")]),
        punches=[22.45],
        cta=("Want in on EIP 2026?", "Follow for the founder journey", "1f680", "Tag a founder who needs an investor"),
    ),
    "clip_02": dict(   # founder advice: don't quit
        cold=(20.36, 23.55),
        body=[(0.05, 2.62), (11.6, 12.82), (13.05, 14.12), (18.0, 20.02), (20.3, 23.52)],
        hook_quote=("“Don't drop it. One problem", "should NOT stop you.”"),
        visual="title", hook_title=("3 rules before you", "QUIT your startup"), hook_emo="1f6d1",
        checklist=("3 rules every founder needs", [(0.05, "Study your competitors"),
                                                (11.6, "Great idea + great team"),
                                                (18.0, "Keep going — don't quit")]),
        framebreak=(18.0, 19.95),
        punches=[20.3],
        cta=("Save this for the day", "you want to quit", "1f4aa", "Follow for more founder lessons"),
    ),
    "clip_03": dict(   # sign-off
        cold=(12.70, 15.55),
        body=[],
        hook_quote=("“See you at", "EIP 2026.”"),
        visual="ticket",
        punches=[],
        cta=("Are you coming?", "Comment “EIP” below", "1f39f-fe0f", "Follow for the EIP 2026 journey"),
    ),
}
CONFIG["IMG_6260"] = dict(   # Q&A: where guest experience starts (question dropped, the answer stands alone)
    cold=(10.58, 13.25),
    body=[(4.58, 8.3), (8.86, 10.22), (10.58, 13.25)],
    hook_quote=("“Hospitality doesn't start", "at arrival. At all.”"),
    visual="title", hook_title=("Where does hospitality", "REALLY start?"), hook_emo="1f914",
    chips=(4.58, 13.25, [("1f4ad", "Think"), ("1f4f1", "Book"), ("1f697", "Arrive")]),
    chip_times=[6.2, 9.7, 11.2],
    strike=(11.9, 2, 0),             # cross out "Arrive" on "مش بتبدأ من الـ arrival"; tag "Think" as the real start
    phone_at=(8.86, 10.22),
    punches=[11.9],
    cta=("Hospitality starts before the door", "Follow for more hospitality secrets", "1f6aa", "Tag a restaurant owner"),
)
C = CONFIG[CLIP]

# ---------- timeline ----------
SEGS = [C["cold"]] + C["body"]
fr_ = lambda x: int(round(x * FPS))
SEGF = [(fr_(s), fr_(e)) for s, e in SEGS]
NSRC = int(float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC],
                                capture_output=True, text=True).stdout) * FPS) - 1
SEGF = [(a, min(b, NSRC)) for a, b in SEGF]
OSTART = np.cumsum([0] + [b - a for a, b in SEGF])
NV = int(OSTART[-1])
TAIL = 100
NF = NV + TAIL
DUR = NF / FPS
SIDX = [f for a, b in SEGF for f in range(a, b)]
bH = OSTART[1] / FPS
bC = NV / FPS

def out_t(src_s):
    """source time inside the body -> output time (first body segment containing it)"""
    f = src_s * FPS
    for k in range(1, len(SEGF)):
        a, b = SEGF[k]
        if a - 2 <= f <= b + 2: return (OSTART[k] + min(b - a, max(0, f - a))) / FPS
    return None
print(CLIP, "hook", round(bH, 2), "body ->", round(bC, 2), "total", round(DUR, 2))

# ---------- face track (from the person masks) ----------
MASKS = np.load(WORK + "/masks.npy")
face = np.zeros((len(MASKS), 2), np.float32)
for k, m in enumerate(MASKS):
    b = m > 128; rows = np.nonzero(b.any(1))[0]; top = rows[0] if len(rows) else 200
    cols = np.nonzero(b[top + 10:top + 70].any(0))[0]
    face[k] = ((cols.mean() if len(cols) else 270) * 2, (top + 55) * 2)
kern = np.ones(15) / 15
face = np.stack([np.convolve(np.pad(face[:, i], 7, mode="edge"), kern, "valid") for i in range(2)], 1)

def person(si):
    a, b = max(0, si - 1), min(len(MASKS), si + 2)
    m = cv2.resize(MASKS[a:b].mean(0).astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(np.clip((m - 0.35) / 0.3, 0, 1), (0, 0), 1.5)

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

# ---------- hook pieces ----------
Q1 = text_img(C["hook_quote"][0], 56, fill=WHITE)
Q2 = text_img(C["hook_quote"][1], 56, fill=YEL)
def quote_card(fr, t):
    s = ease_pop(t - 0.1)
    if s <= 0: return
    w_ = max(Q1.width, Q2.width) + 60; h_ = Q1.height + Q2.height + 20
    cy = 1560
    glass(fr, (W / 2 - w_ * s / 2, cy - h_ * s / 2, W / 2 + w_ * s / 2, cy + h_ * s / 2), r=40, ta=0.6)
    paste_center(fr, Q1, W / 2, cy - Q2.height / 2, s); paste_center(fr, Q2, W / 2, cy + Q1.height / 2 - 4, s)

if "hook_title" in C:
    HT1 = text_img(C["hook_title"][0], 68, fill=WHITE, stroke=8)
    HT2 = text_img(C["hook_title"][1], 92, fill=YEL, stroke=10, emo=C.get("hook_emo"))

def build_phone():
    PW, PH = 420, 860
    ph = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle((0, 0, PW - 1, PH - 1), 64, fill=(22, 22, 26)); d.rounded_rectangle((2, 2, PW - 3, PH - 3), 62, outline=(130, 130, 140), width=4)
    d.rounded_rectangle((14, 14, PW - 15, PH - 15), 52, fill=(250, 248, 244))
    d.rounded_rectangle((PW / 2 - 60, 26, PW / 2 + 60, 56), 15, fill=BLACK)
    d.text((40, 90), "Reservya", font=font(44), fill=(20, 20, 20))
    d.text((40, 150), "Your night, sorted.", font=font(24, FONT_B), fill=(120, 120, 120))
    d.rounded_rectangle((34, 210, PW - 34, 470), 28, fill=WHITE, outline=(230, 230, 230), width=2)
    ph.alpha_composite(emoji("1f37d-fe0f", 70), (60, 236))
    d.text((150, 236), "Table for 2", font=font(34), fill=(20, 20, 20))
    d.text((150, 284), "Tonight · 8:30 PM", font=font(26, FONT_B), fill=(110, 110, 110))
    d.text((60, 330), "Arrival time sent", font=font(24, FONT_B), fill=(110, 110, 110))
    d.text((60, 365), "Menu & table ready", font=font(24, FONT_B), fill=(110, 110, 110))
    d.rounded_rectangle((34, 500, PW - 34, 580), 40, fill=GREEN)
    d.text((PW / 2, 540), "Confirmed ✓", font=font(36), fill=WHITE, anchor="mm")
    for i in range(3): d.rounded_rectangle((34, 620 + i * 66, PW - 34, 672 + i * 66), 18, fill=(238, 236, 232))
    return ph
PHONE = build_phone() if C["visual"] == "phone" or "phone_at" in C else None

def build_ticket():
    TW, TH = 820, 380
    im = Image.new("RGBA", (TW + 40, TH + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((26, 30, TW + 26, TH + 30), 34, fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, TW + 20, TH + 20), 34, fill=YEL)
    d.rectangle((600, 20, 604, TH + 20), fill=(20, 20, 20))
    for y in range(40, TH, 28): d.ellipse((594, y, 610, y + 16), fill=(255, 240, 160))
    d.text((60, 52), "ADMIT ONE", font=font(30, FONT_B), fill=(40, 40, 40))
    d.text((56, 92), "EIP 2026", font=font(118), fill=BLACK)
    d.text((60, 250), "Entrepreneurs Investment Program", font=font(28, FONT_B), fill=(40, 40, 40))
    d.text((60, 296), "FOUNDER PASS", font=font(30), fill=RED)
    im.alpha_composite(emoji("1f39f-fe0f", 130), (650, 140))
    return im
TICKET = build_ticket() if C["visual"] == "ticket" else None

# ---------- body pieces ----------
def lower_third(fr, t, t0, name, role):
    u = t - t0
    e = ease_out(u / 0.25)
    n_im = text_img(name, 56, fill=WHITE); r_im = text_img(role, 40, fill=YEL, fnt=FONT_B)
    w_ = max(n_im.width, r_im.width) + 70
    x = -w_ + (w_ + 50) * e
    glass(fr, (x, 1380, x + w_, 1380 + n_im.height + r_im.height + 20), r=24, ta=0.6)
    ImageDraw.Draw(fr).rectangle((x, 1380, x + 10, 1380 + n_im.height + r_im.height + 20), fill=YEL)
    fr.alpha_composite(n_im, (int(x + 30), 1386)); fr.alpha_composite(r_im, (int(x + 30), 1386 + n_im.height - 6))

def build_x(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for col, wd in ((WHITE, 26), (RED, 16)):
        d.line((14, 14, w - 14, h - 14), fill=col, width=wd); d.line((14, h - 14, w - 14, 14), fill=col, width=wd)
    return im
def chip_row(fr, t, times, items, strike=None):
    ims = [text_img(lbl, 56, fill=BLACK, box=WHITE, fnt=FONT, emo=e, pad=(22, 4), radius=34) for e, lbl in items]
    total = sum(im.width for im in ims) + 30 * (len(ims) - 1)
    if total > W - 40:
        k = (W - 40) / total; ims = [im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS) for im in ims]; total = W - 40
    x = (W - total) / 2
    arrow = text_img("›", 70, fill=YEL, fnt=FONT, stroke=6)
    for i, (ts, im) in enumerate(zip(times, ims)):
        if t >= ts:
            paste_center(fr, im, x + im.width / 2, 1580, ease_pop(t - ts))
            if i: paste_center(fr, arrow, x - 15, 1580, ease_pop(t - ts))
            if strike and t >= strike[0]:
                if i == strike[1]:
                    paste_center(fr, build_x(im.width - 10, im.height + 30), x + im.width / 2, 1580, 2.0 - ease_out((t - strike[0]) / 0.1))
                if i == strike[2]:
                    paste_center(fr, text_img("It starts HERE", 40, fill=BLACK, box=YEL, fnt=FONT, emo="1f447", pad=(16, 0), radius=16),
                                 x + im.width / 2 + 60, 1470, ease_pop(t - strike[0] - 0.15), -3)
        x += im.width + 30

def checklist(fr, t, t0, title, items_t):
    if t < t0: return
    s = ease_pop(t - t0)
    ti = text_img(title, 46, fill=YEL, emo="2705")
    rows = [(ts, text_img(txt, 42, fill=WHITE, fnt=FONT_B)) for ts, txt in items_t]
    shown = [r for r in rows if t >= r[0]]
    h_ = 110 + 78 * len(rows)                     # full height from the start, anchored above the bottom edge
    y0 = H - 140 - h_
    glass(fr, (50, y0 + h_ * (1 - s), 1030, y0 + h_), r=40, ta=0.62)
    paste_center(fr, ti, W / 2, y0 + 55, s)
    for i, (ts, im) in enumerate(shown):
        cy = y0 + 140 + i * 78
        sc = ease_pop(t - ts)
        paste_center(fr, emoji("2714-fe0f", 46), 110, cy, sc)
        fr.alpha_composite(im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR) if sc != 1 else im,
                           (150, int(cy - im.height * sc / 2)))

# ---------- frame break (on "keep going, don't stop") ----------
_yy, _xx = np.mgrid[0:H, 0:W]
def build_navy():
    g = np.linspace(0, 1, H)[:, None, None]
    bg = ((1 - g) * np.array([12, 16, 38]) + g * np.array([42, 18, 58])) * np.ones((1, W, 1))
    glow = np.exp(-(((_xx - 540) / 520.0) ** 2 + ((_yy - 760) / 600.0) ** 2))[..., None] * np.array([255, 190, 0]) * 0.35
    return np.clip(bg + glow + np.random.default_rng(3).normal(0, 4, (H, W, 1)), 0, 255).astype(np.uint8)
NAVY = build_navy() if "framebreak" in C else None

def fx_framebreak(src, si, u_t):
    u = ease_out(u_t / 0.2)
    k = 1.0 - 0.15 * u + 0.04 * math.sin(clamp01(u_t / 0.35) * math.pi) * (1 - u * 0.3)
    rot = -3.0 * u
    fx_, fy_ = face[si]
    M = affine(1.2, fx_, fy_ + 420)
    Cc = warp(src, M); A = warp(person(si), M, cv2.BORDER_CONSTANT)
    hy = M[1, 1] * fy_ + M[1, 2]; hx = M[0, 0] * fx_ + M[0, 2]
    x0, y0, x1, y1 = int(max(30, hx - 430)), int(hy + 110), int(min(W - 30, hx + 430)), H - 60
    win = np.zeros((H, W), np.float32); win[y0:y1, x0:x1] = 1
    brd = np.zeros((H, W), np.float32); brd[y0 - 18:y1 + 18, x0 - 18:x1 + 18] = 1
    ap = A * (1 - win)
    alpha = np.maximum(win, ap + brd * (1 - ap))
    out_rgb = (Cc * ap[..., None] + 255.0 * (brd * (1 - ap))[..., None]) / np.maximum(alpha, 1e-4)[..., None]
    rgb = np.where(win[..., None] > 0, Cc, out_rgb).astype(np.float32)
    R = cv2.getRotationMatrix2D((540, 960), rot, k); R[1, 2] += 120 * u
    rgb_s = cv2.warpAffine(rgb, R, (W, H)); a_s = cv2.warpAffine(alpha, R, (W, H))[..., None]
    shadow = np.roll(cv2.GaussianBlur(cv2.warpAffine(brd, R, (W, H)), (0, 0), 24)[..., None], 26, 0) * 0.65
    out = NAVY.astype(np.float32) * (1 - shadow)
    return np.clip(out * (1 - a_s) + rgb_s * a_s, 0, 255).astype(np.uint8)

# ---------- CTA ----------
CTA1 = text_img(C["cta"][0], 80, fill=WHITE, stroke=9)
CTA2 = text_img(C["cta"][1], 66, fill=WHITE, box=RED, emo=C["cta"][2], pad=(40, 10), radius=60)
CTA3 = text_img(C["cta"][3], 44, fill=BLACK, box=WHITE, fnt=FONT_B, emo="1f447", pad=(24, 4), radius=24)

# ---------- schedule (output seconds) ----------
P_OUT = [p for p in (out_t(x) for x in C["punches"]) if p is not None]
CHIPS = None
if "chips" in C:
    s0, e0, items = C["chips"]
    a, b = out_t(s0), out_t(e0)
    times = [out_t(x) for x in C["chip_times"]] if "chip_times" in C else [a + (b - a) * i / len(items) for i in range(len(items))]
    CHIPS = (times, items, a, b + 0.6)
STRIKE = (out_t(C["strike"][0]),) + tuple(C["strike"][1:]) if "strike" in C else None
PH_AT = (out_t(C["phone_at"][0]), out_t(C["phone_at"][1])) if "phone_at" in C else None
CHECK = None
if "checklist" in C:
    title, items = C["checklist"]
    CHECK = (title, [(out_t(ts), txt) for ts, txt in items])
CALL = [(out_t(s), out_t(s) + (e - s), txt, emo) for s, e, txt, emo in C.get("callouts", [])]
LT = None
if "lower_third" in C:
    s, e, nm, rl = C["lower_third"]; LT = (out_t(s), out_t(s) + (e - s), nm, rl)
FB = None
if "framebreak" in C:
    s, e = C["framebreak"]; FB = (out_t(s), out_t(s) + (e - s))

# ---------- render ----------
class Frames:
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=lanczos," + GRADE + ",format=rgb24",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.cache, self.next = {}, 0
    def __getitem__(self, i):
        if i in self.cache: return self.cache[i]
        if i < self.next:                       # the cold open is lifted from later in the clip: restart for the body
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
FRAMINGS = [(1.3, 330), (1.6, 200), (1.2, 420)]
end_bg = None
for n in range(NF):
    t = n / FPS
    si = SIDX[min(n, NV - 1)]
    src = FRAMES[si]
    if n < NV:
        k = int(np.searchsorted(OSTART, n, side="right") - 1)
        u = (n - OSTART[k]) / FPS
        fx_, fy_ = face[si]
        if k == 0:                                     # hook: hard snap onto his face
            z, off = 1.75 + 0.6 * (1 - ease_out(u / 0.15)) + 0.05 * u, 70
            sx, sy = shake(t, 0, 20, 0.35)
        else:
            z, off = FRAMINGS[(k - 1) % len(FRAMINGS)]
            z *= (1 + 0.08 * (1 - ease_out(u / 0.12))) * (1 + 0.015 * u)
            sx = sy = 0.0
        for p in P_OUT:
            if p <= t < p + 0.7:
                z *= 1 + 0.22 * ease_out((t - p) / 0.07) * (1 - clamp01((t - p - 0.5) / 0.2)); sx, sy = shake(t, p, 14)
        if PH_AT and PH_AT[0] <= t < PH_AT[1] + 0.25:          # slide him left so the phone sits beside his face
            fx_ += 200 * ease_out((t - PH_AT[0]) / 0.3) * (1 - ease_out((t - PH_AT[1]) / 0.25))
        if FB and FB[0] <= t < FB[1]:
            arr = fx_framebreak(src, si, t - FB[0])
        else:
            arr = warp(src, affine(z, fx_, fy_ + off, sx, sy))
        fr = Image.fromarray(arr).convert("RGBA")

        if t < bH:
            # visual hook
            if C["visual"] == "phone":
                e = ease_out((t - 0.1) / 0.35)
                paste_center(fr, PHONE, 790 + 400 * (1 - e), 900, 1.0, -8 + 8 * (1 - e))
                glass(fr, (90, 130, 990, 360), r=36, ta=0.55)
                paste_center(fr, text_img(C["hook_title"][0], 60, fill=WHITE, stroke=8), W / 2, 200, ease_pop(t))
                paste_center(fr, text_img(C["hook_title"][1], 88, fill=YEL, stroke=10), W / 2, 300, ease_pop(t - 0.12), -2)
            elif C["visual"] == "ticket":
                e = ease_out((t - 0.05) / 0.35)
                paste_center(fr, TICKET, W / 2, 420 - 600 * (1 - e), 1.0, -6 + 2 * math.sin(t * 3))
            else:
                hw = max(HT1.width, HT2.width) + 50
                glass(fr, (W / 2 - hw / 2, 150, W / 2 + hw / 2, 420), r=36, ta=0.55)
                paste_center(fr, HT1, W / 2, 230, ease_pop(t))
                paste_center(fr, HT2, W / 2, 350, ease_pop(t - 0.12), -2)
            quote_card(fr, t)
            flash(fr, WHITE, 0.85 * (1 - t / 0.12))
        else:
            if LT and LT[0] <= t < LT[1]: lower_third(fr, t, LT[0], LT[2], LT[3])
            if CHIPS and CHIPS[2] <= t < CHIPS[3]: chip_row(fr, t, CHIPS[0], CHIPS[1], STRIKE)
            if PH_AT and PH_AT[0] <= t < PH_AT[1] + 0.25:
                e = ease_out((t - PH_AT[0]) / 0.3) * (1 - ease_out((t - PH_AT[1]) / 0.25))
                paste_center(fr, PHONE, 800 + 500 * (1 - e), 900, 1.0, -8 + 8 * (1 - e))
            if CHECK and not (FB and FB[0] <= t < FB[1]): checklist(fr, t, CHECK[1][0][0], CHECK[0], CHECK[1])
            for cs, ce, txt, emo in CALL:
                if cs <= t < ce: glass_text(fr, text_img(txt, 54, fill=WHITE, emo=emo), W / 2, 1580, ease_pop(t - cs))
            if any(p <= t < p + 0.08 for p in P_OUT): flash(fr, WHITE, 0.3)
            if u < 0.08 and k == 1: flash(fr, WHITE, 0.6)
    else:
        u = t - bC
        if end_bg is None:
            end_bg = (cv2.GaussianBlur(warp(src, affine(1.3, face[si][0], face[si][1] + 300)), (0, 0), 20) * 0.45).astype(np.uint8)
        fr = Image.fromarray(warp(end_bg, affine(1 + 0.04 * u / (TAIL / FPS), 540, 960))).convert("RGBA")
        paste_center(fr, CTA1, W / 2, 720, ease_pop(u - 0.02))
        if u >= 0.4:
            paste_center(fr, CTA2, W / 2, 900, ease_pop(u - 0.4) * (1 + 0.04 * math.sin((u - 0.4) * 12)))
            paste_center(fr, emoji("1f446", 110), W / 2 + 340, 1040 + 14 * math.sin(t * 10), ease_pop(u - 0.55))
        if u >= 0.9: paste_center(fr, CTA3, W / 2, 1160, ease_pop(u - 0.9))
        flash(fr, WHITE, 0.8 * (1 - u / 0.15))
    if t >= bH:
        dr = ImageDraw.Draw(fr)
        dr.rectangle((0, 0, W, 12), fill=(0, 0, 0, 110)); dr.rectangle((0, 0, int(W * (n + 1) / NF), 12), fill=YEL + (255,))
    out = fr.convert("RGB")
    if any(abs(t - p) < 0.5 / FPS for p in PREVIEW): out.save(f"{WORK}/prev_{t:05.2f}.jpg", quality=85)
    enc.stdin.write(out.tobytes())
enc.stdin.close(); enc.wait(); FRAMES.p.kill()

# ---------- audio ----------
at = ";".join(f"[0:a:0]atrim={a/FPS}:{b/FPS},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={(b-a)/FPS-0.015}:d=0.015[a{i}]"
              for i, (a, b) in enumerate(SEGF))
afc = (f"{at};{''.join(f'[a{i}]' for i in range(len(SEGF)))}concat=n={len(SEGF)}:v=0:a=1,aformat=channel_layouts=mono,"
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

def slap():
    t = tt(0.14); n = rng.standard_normal(len(t))
    return (n - lp(n, 0.3)) * np.exp(-t * 45) * 0.6 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30) * 0.6

def ding(f0=1318.5, d=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f0 * t) + 0.5 * np.sin(2 * np.pi * f0 * 1.5 * t) + 0.25 * np.sin(2 * np.pi * f0 * 2.01 * t)) * np.exp(-t * 5) * 0.3

FXA = np.zeros(N, np.float32)
def put(sig, at_, g=1.0):
    i = int(at_ * SR); j = min(N, i + len(sig))
    if i < N: FXA[i:j] += sig[:j - i] * g

put(boom(1.2), 0.0, 1.0); put(whoosh(0.3, False), 0.0, 0.5)
if C["visual"] in ("phone", "ticket"): put(whoosh(0.35), 0.1, 0.6); put(ding(1568, 0.5), 0.45, 0.5)
put(whoosh(0.3, False), bH - 0.15, 0.5)
if LT: put(whoosh(0.25), LT[0], 0.4)
if CHIPS:
    for ts in CHIPS[0]: put(pop(), ts, 0.5)
if STRIKE: put(boom(0.7), STRIKE[0], 0.8); put(slap(), STRIKE[0], 0.7)
if PH_AT: put(whoosh(0.3), PH_AT[0] - 0.05, 0.6); put(ding(1568, 0.4), PH_AT[0] + 0.3, 0.4)
if CHECK:
    for ts, _ in CHECK[1]: put(pop(), ts, 0.6); put(ding(1568, 0.35), ts + 0.02, 0.35)
for cs, *_ in CALL: put(pop(), cs, 0.4)
for p in P_OUT: put(boom(0.6), p, 0.6); put(whoosh(0.2), p - 0.1, 0.4)
if FB: put(whoosh(0.3), FB[0] - 0.2, 0.6); put(boom(0.8), FB[0], 0.8)
put(whoosh(0.4), bC - 0.15, 0.6); put(ding(1318.5), bC + 0.4, 0.8); put(ding(1760, 0.8), bC + 0.52, 0.6)

# upbeat bed: 120 bpm, Am-F-C-G
beat = 0.5
MUS = np.zeros(N, np.float32)
def kick():
    t = tt(0.3); f = 45 + 110 * np.exp(-t * 30); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)
def hat():
    t = tt(0.05); n = rng.standard_normal(len(t)); n = n - lp(n, 0.5); return n * np.exp(-t * 90) * 0.25
roots = [55.0, 43.65, 65.41, 49.0]
chords = [[220, 261.6, 329.6], [174.6, 220, 261.6], [261.6, 329.6, 392], [196, 246.9, 293.7]]
for b in range(int(DUR / beat) + 1):
    s0 = b * beat
    def mput(sig, at_, g):
        i = int(at_ * SR); j = min(N, i + len(sig))
        if i < N: MUS[i:j] += sig[:j - i] * g
    mput(kick(), s0, 0.8); mput(hat(), s0 + beat / 2, 1.0)
    bar = (b // 4) % 4; t = tt(beat); r = roots[bar]
    mput((np.sin(2 * np.pi * r * t) + 0.4 * np.sin(2 * np.pi * 2 * r * t)) * np.exp(-t * 3), s0, 0.35)
    if b % 4 == 0:
        t = tt(4 * beat)
        pad = sum(np.sin(2 * np.pi * f * t) for f in chords[bar]) * np.minimum(1, t * 4) * np.minimum(1, (4 * beat - t) * 4)
        mput(pad.astype(np.float32), s0, 0.05)
env = np.convolve(np.abs(V), np.ones(int(0.03 * SR)) / int(0.03 * SR), mode="same"); env /= env.max() + 1e-9
MUS = MUS * (1 - 0.6 * np.clip(env * 4, 0, 1)) * 0.22 * np.where(np.arange(N) / SR >= bC, 1.8, 1.0)
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
