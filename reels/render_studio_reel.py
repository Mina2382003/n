"""Studio Q&A reels: cold-open verbal hook, visual hook, content-matched effects, English CTA.

usage: render_studio_reel.py NAME SRC OUT WORKDIR
NAME is a key of CONFIG. WORKDIR holds masks.npy (540x960 person masks per source frame, for the face track).
Segments are source-second ranges played in order; "kind" is hook / q (the quiet off-camera question,
boosted) / a (his answer). Overlay times are (segment index, source second) so a line that is used twice
(hook and answer) can be addressed unambiguously.
"""
import subprocess, numpy as np, wave, math, os, sys
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = os.path.dirname(os.path.abspath(__file__))
NAME, SRC, OUT, WORK = sys.argv[1:5]
FONT = S + "/font/package/900Black/Cairo_900Black.ttf"
FONT_B = S + "/font/package/800ExtraBold/Cairo_800ExtraBold.ttf"
EMO = S + "/emoji/package/img/apple/64/"
W, H, FPS, SR = 1080, 1920, 30, 48000
GRADE = "eq=contrast=1.08:saturation=1.2,colorbalance=rm=0.03:bm=-0.03,unsharp=5:5:0.6,vignette=PI/5"
YEL, RED, WHITE, BLACK, GREEN = (255, 214, 0), (235, 30, 45), (255, 255, 255), (0, 0, 0), (37, 211, 102)
Q_GAIN = 14                                       # dB; the question mic is ~15 dB quieter than his

CONFIG = {
    "IMG_6298": dict(   # pre-ordering -> table turnover -> more customers
        segs=[("hook", 19.10, 22.50),
              ("a", 2.45, 2.98), ("a", 3.28, 6.62), ("a", 6.88, 13.72), ("a", 14.08, 18.58), ("a", 19.10, 22.50)],
        title=("This ONE rule fills", "your restaurant", "1f4c8"),
        quote=("“…and you take WAY", "more customers.”"),
        chart=dict(start=(2, 4.6), end=(3, 13.72), label="Table turnover",
                   tags=[((3, 7.2), "Holidays"), ((3, 8.6), "Rush hours"), ((3, 10.4), "Waiting lists")]),
        phone=dict(start=(4, 15.2), end=(4, 18.58), title="Pre-order", sub="Required for tonight",
                   rows=[("1f35d", "Pasta  ×2"), ("1f957", "Salad  ×1"), ("1f964", "Drinks ×2")], button="Order confirmed ✓"),
        stamps=[((5, 19.2), (5, 22.5), "WAY more customers", "1f680")],
        punches=[(4, 15.27), (5, 19.17)],
        cta=("Run a restaurant?", "Follow for more restaurant growth hacks", "1f680", "Send this to a restaurant owner"),
    ),
    "IMG_6297": dict(   # teaser: reason #1, cliffhanger to the next video
        segs=[("hook", 2.72, 5.32), ("a", 5.78, 9.02)],
        title=("Why EVERY restaurant", "needs PRE-ORDERING", "1f37d-fe0f"),
        quote=("“Pre-ordering matters for", "more than ONE reason.”"),
        checklist=dict(title="Why pre-ordering wins", emo="2705",
                       items=[((1, 5.8), "#1  Higher table turnover", "2714-fe0f"), ((1, 7.3), "#2  Next video…", "1f512")]),
        punches=[(1, 5.8)],
        cta=("Reason #2 drops next", "Follow so you don't miss it", "1f514", "Save this for later"),
    ),
    "IMG_6299": dict(   # the customer side: no waiting for the check
        segs=[("hook", 12.95, 14.90),
              ("a", 5.80, 8.02), ("a", 8.10, 8.78), ("a", 9.05, 10.38), ("a", 10.85, 12.72), ("a", 12.95, 15.05),
              ("a", 15.70, 21.78), ("a", 22.45, 25.38)],
        title=("The WORST part of", "eating out?", "1f9fe"),
        quote=("“After I eat, I already", "got what I came for.”"),
        checklist=dict(title="What customers hate", emo="1f624",
                       items=[((6, 15.8), "Waiting for the check", "23f3"), ((6, 18.0), "Asking for the card machine", "1f4b3"),
                              ((6, 20.2), "Wasting time after eating", "1f629")], until=(6, 21.78)),
        phone=dict(start=(7, 22.45), end=(7, 25.38), title="Your table", sub="Pre-ordered online",
                   rows=[("2705", "Food ordered"), ("2705", "Bill paid"), ("1f6aa", "Leave anytime")], button="All paid ✓"),
        punches=[(5, 12.97), (7, 22.47)],
        cta=("Hate waiting for the check?", "Follow for more hospitality insights", "1f9fe", "Tag a friend who always waits for the bill"),
    ),
    "IMG_6303": dict(   # first money: 30 EGP
        segs=[("hook", 5.45, 6.65), ("q", 0.05, 3.25), ("a", 5.45, 6.65)],
        title=("My FIRST reservation", "made me…", "1f914"),
        quote=("“Thirty pounds.”", ""),
        money=dict(at=(0, 5.5), text="30 EGP"),
        question=dict(seg=1, text="How much did your FIRST reservation make you?"),
        counter=dict(start=(2, 5.45), end=(2, 6.4), to=30, unit="EGP"),
        cta=("From 30 EGP to…", "Follow the Reservya journey", "1f680", "Comment your first sale"),
    ),
    "IMG_6301": dict(   # first check: spent more celebrating than earned
        segs=[("hook", 8.30, 11.10), ("hook", 11.52, 12.36), ("hook", 12.74, 13.42), ("q", 0.25, 3.45),
              ("a", 5.15, 7.72), ("a", 8.30, 11.10), ("a", 11.52, 12.36), ("a", 12.74, 13.42), ("a", 14.18, 14.80)],
        title=("I got my first check…", "and did THIS", "1f602"),
        quote=("“I spent WAY more celebrating", "than I made.”"),
        question=dict(seg=3, text="Your first check — what did you do with it?"),
        bars=dict(start=(5, 8.3), end=(8, 14.8), left=("Earned", "1f4b5", 0.22), right=("Spent celebrating", "1f389", 0.95)),
        punches=[(5, 9.4)],
        cta=("Worth it?", "Follow the founder journey", "1f680", "How did you celebrate your first win?"),
    ),
    "IMG_6302": dict(   # the first reservation feeling
        segs=[("hook", 5.25, 8.85), ("q", 0.25, 3.50), ("a", 5.25, 8.85), ("a", 9.38, 10.20), ("a", 10.88, 13.15)],
        title=("The day our FIRST", "reservation came in", "1f514"),
        quote=("“I was happy in a way", "that's NOT normal.”"),
        notify=[((0, 5.4), (0, 8.85)), ((2, 5.3), (2, 7.2))],
        question=dict(seg=1, text="How did the first reservation feel?"),
        punches=[(2, 7.3)],
        cta=("Remember your first sale?", "Follow the Reservya journey", "1f680", "Tell me yours in the comments"),
    ),
}
# selfie footage: his face fills the middle-low frame, the sunroof above is the free space for overlays
SELFIE = dict(hook_z=1.4, framings=[(1.0, 0), (1.18, 40), (1.08, 20)], busy=(1.0, 0),
              quote_y=590, money_y=770, counter_y=1730, card=(60, 170, 1020, 720), receipt=(W / 2 + 300, 1620, 0.5))
CONFIG["IMG_7486_10days"] = dict(SELFIE,   # "100% sure: in 10 days every price will have gone up"
    segs=[("hook", 12.22, 17.15),
          ("a", 1.45, 4.55), ("a", 4.62, 7.0), ("a", 7.95, 11.6), ("a", 12.22, 17.15), ("a", 18.05, 21.15)],
    title=("Restaurant prices are", "about to JUMP", "1f4c8"),
    quote=("“100% sure: in 10 days, ALL", "prices will have gone up.”"),
    money=dict(at=(0, 13.4), text="10 DAYS", emo="23f3"),
    headlines=[((1, 1.6), (3, 11.6), "PARLIAMENT DECISION", "BREAKING", 330, 300, 6),
               ((2, 4.7), (3, 11.6), "PRESIDENTIAL MANDATE", "NEWS", 720, 500, -5),
               ((3, 10.4), (3, 11.6), "RESTAURANTS NEXT?", "MARKETS", 420, 700, 4)],
    stamps=[((4, 13.4), (4, 17.15), "10 days", "23f3", 1740)],
    punches=[(4, 12.27)],
    cta=("Prices in 10 days?", "Follow for the price update", "1f514", "Send this to a restaurant owner"),
    nfa=True,
)
CONFIG["IMG_7486_chain"] = dict(SELFIE,   # politics -> dollar -> market -> restaurant cost
    segs=[("hook", 42.64, 44.78), ("hook", 45.88, 46.52),
          ("a", 33.05, 34.95), ("a", 36.15, 37.15), ("a", 38.5, 41.4), ("a", 42.64, 44.78), ("a", 45.88, 46.55), ("a", 47.3, 54.05)],
    title=("How politics hits", "YOUR menu", "1f37d-fe0f"),
    quote=("“The prices of EVERYTHING", "are going up.”"),
    chips=dict(items=[((2, 33.1), "1f3db-fe0f", "Politics"), ((4, 38.6), "1f4b5", "Dollar"), ((4, 39.9), "1f6d2", "Market"),
                      ((7, 47.4), "1f37d-fe0f", "Your menu")], until=(7, 54.05)),
    stamps=[((7, 49.2), (7, 54.05), "COST ▲", "1f4c8", 620)],
    punches=[(5, 42.7), (7, 47.4)],
    cta=("Restaurant owner?", "Follow before prices move", "1f4c8", "Share this with your business partner"),
)
CONFIG["IMG_7486_bill"] = dict(SELFIE,   # who pays the bill? the customer: +5-10%
    segs=[("hook", 55.36, 57.18), ("hook", 57.84, 58.58),
          ("a", 47.3, 54.05), ("a", 55.36, 57.18), ("a", 57.84, 58.58), ("a", 63.6, 65.14), ("a", 66.22, 67.3), ("a", 67.82, 69.3)],
    title=("Who pays the bill", "when costs go up?", "1f9fe"),
    quote=("“So who pays the bill?", "The CUSTOMER.”"),
    receipt_on=True,
    counter=dict(start=(7, 67.85), end=(7, 69.2), frm=5, to=10, fmt="+{}%"),
    punches=[(3, 55.4), (4, 57.86)],
    cta=("Would you still eat out at +10%?", "Follow for more restaurant economics", "1f37d-fe0f", "Comment yes or no"),
)
CONFIG["IMG_7486_dollar60"] = dict(SELFIE,   # if the dollar crosses 60, prices become a different story
    segs=[("hook", 73.22, 75.02), ("hook", 75.72, 78.12),
          ("a", 63.6, 65.14), ("a", 66.22, 67.3), ("a", 67.82, 69.3), ("a", 71.32, 75.02), ("a", 75.72, 78.12)],
    title=("The dollar's", "DANGER LINE", "26a0-fe0f"),
    quote=("“If the dollar crosses 60, prices", "become a whole different story.”"),
    chart=dict(start=(3, 71.3), end=(4, 78.12), label="EGP per USD", threshold="60", tags=[]),
    counter=dict(start=(2, 67.85), end=(2, 69.2), frm=5, to=10, fmt="+{}%"),
    punches=[(4, 75.76)],
    cta=("I'll update you if it crosses 60", "Follow for the market update", "1f514", "Save this & watch the dollar"),
    nfa=True,
)
C = CONFIG[NAME]

# ---------- timeline ----------
SEGS = C["segs"]
NSRC = len(np.load(WORK + "/masks.npy", mmap_mode="r"))
SEGF = [(k, int(round(s * FPS)), min(NSRC - 1, int(round(e * FPS)))) for k, s, e in SEGS]
OSTART = np.cumsum([0] + [b - a for _, a, b in SEGF])
NV = int(OSTART[-1])
TAIL = 100
NF = NV + TAIL
DUR = NF / FPS
SIDX = [f for _, a, b in SEGF for f in range(a, b)]
bH = OSTART[sum(1 for k, *_ in SEGS if k == "hook")] / FPS          # hook ends
bC = NV / FPS

def T(ref):
    """(segment index, source second) -> output second"""
    k, src = ref
    _, a, b = SEGF[k]
    return (OSTART[k] + min(b - a, max(0, src * FPS - a))) / FPS
print(NAME, "hook", round(bH, 2), "speech ->", round(bC, 2), "total", round(DUR, 2))

# ---------- face track ----------
MASKS = np.load(WORK + "/masks.npy")
face = np.zeros((len(MASKS), 2), np.float32)
for k, m in enumerate(MASKS):
    b = m > 128; rows = np.nonzero(b.any(1))[0]; top = rows[0] if len(rows) else 200
    cols = np.nonzero(b[top + 10:top + 60].any(0))[0]
    face[k] = ((cols.mean() if len(cols) else 270) * 2, (top + 40) * 2)
kern = np.ones(15) / 15
face = np.stack([np.convolve(np.pad(face[:, i], 7, mode="edge"), kern, "valid") for i in range(2)], 1)

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
    l, t, r, b = d.textbbox((0, 0), txt or " ", font=f, stroke_width=stroke)
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

def glass(fr, box, r=40, tint=(18, 18, 26), ta=0.58, blur=22, border=120):
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

def flash(fr, col, a):
    if a > 0: fr.alpha_composite(Image.new("RGBA", (W, H), col + (int(255 * min(1, a)),)))

def two_line_card(fr, l1, l2, cy, s, size=56):
    if s <= 0: return
    a = text_img(l1, size, fill=WHITE); b = text_img(l2, size, fill=YEL) if l2 else None
    w_ = max(a.width, b.width if b else 0) + 60; h_ = a.height + (b.height - 6 if b else 0) + 24
    glass(fr, (W / 2 - w_ * s / 2, cy - h_ * s / 2, W / 2 + w_ * s / 2, cy + h_ * s / 2), r=40, ta=0.6)
    if b:
        paste_center(fr, a, W / 2, cy - b.height / 2 + 2, s); paste_center(fr, b, W / 2, cy + a.height / 2 - 6, s)
    else:
        paste_center(fr, a, W / 2, cy, s)

# ---------- hook pieces ----------
HT1 = text_img(C["title"][0], 68, fill=WHITE, stroke=8)
HT2 = text_img(C["title"][1], 92, fill=YEL, stroke=10, emo=C["title"][2])
def title(fr, t):
    hw = max(HT1.width, HT2.width) + 50
    glass(fr, (W / 2 - hw / 2, 140, W / 2 + hw / 2, 410), r=36, ta=0.55)
    paste_center(fr, HT1, W / 2, 220, ease_pop(t)); paste_center(fr, HT2, W / 2, 335, ease_pop(t - 0.12), -2)

MONEY = None
if "money" in C:
    MONEY = text_img(C["money"]["text"], 170, fill=BLACK, box=YEL, emo=C["money"].get("emo", "1f4b8"), pad=(40, 10), radius=40)

NOTIF = None
if "notify" in C:
    NOTIF = Image.new("RGBA", (940, 190), (0, 0, 0, 0)); d = ImageDraw.Draw(NOTIF)
    d.rounded_rectangle((0, 0, 939, 189), 44, fill=(245, 245, 247, 245))
    d.rounded_rectangle((28, 40, 128, 140), 26, fill=YEL); NOTIF.alpha_composite(emoji("1f37d-fe0f", 70), (43, 55))
    d.text((154, 34), "RESERVYA", font=font(28, FONT_B), fill=(120, 120, 128)); d.text((780, 34), "now", font=font(28, FONT_B), fill=(120, 120, 128))
    d.text((154, 72), "New reservation!", font=font(44), fill=(20, 20, 20))
    d.text((154, 128), "Table for 2 · Tonight 8:30 PM", font=font(30, FONT_B), fill=(70, 70, 76))

# ---------- body pieces ----------
def build_phone(p):
    PW, PH = 420, 860
    ph = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(ph)
    d.rounded_rectangle((0, 0, PW - 1, PH - 1), 64, fill=(22, 22, 26)); d.rounded_rectangle((2, 2, PW - 3, PH - 3), 62, outline=(130, 130, 140), width=4)
    d.rounded_rectangle((14, 14, PW - 15, PH - 15), 52, fill=(250, 248, 244))
    d.rounded_rectangle((PW / 2 - 60, 26, PW / 2 + 60, 56), 15, fill=BLACK)
    d.text((40, 90), p["title"], font=font(46), fill=(20, 20, 20))
    d.text((40, 152), p["sub"], font=font(26, FONT_B), fill=(120, 120, 120))
    for i, (e, txt) in enumerate(p["rows"]):
        y = 220 + i * 110
        d.rounded_rectangle((34, y, PW - 34, y + 90), 24, fill=WHITE, outline=(230, 230, 230), width=2)
        ph.alpha_composite(emoji(e, 54), (56, y + 18)); d.text((128, y + 22), txt, font=font(32, FONT_B), fill=(30, 30, 30))
    d.rounded_rectangle((34, 600, PW - 34, 684), 42, fill=GREEN)
    d.text((PW / 2, 642), p["button"], font=font(34), fill=WHITE, anchor="mm")
    return ph
PHONE = build_phone(C["phone"]) if "phone" in C else None

def checklist(fr, t, cl, times):
    if t < times[0]: return
    s = ease_pop(t - times[0])
    ti = text_img(cl["title"], 48, fill=YEL, emo=cl["emo"])
    rows = [text_img(txt, 44, fill=WHITE, fnt=FONT_B, emo=e) for _, txt, e in cl["items"]]
    h_ = 112 + 86 * len(rows)
    y0 = H - 150 - h_
    glass(fr, (50, y0 + h_ * (1 - s), 1030, y0 + h_), r=40, ta=0.62)
    paste_center(fr, ti, W / 2, y0 + 58, s)
    for i, (ts, im) in enumerate(zip(times, rows)):
        if t >= ts:
            sc = ease_pop(t - ts)
            paste_center(fr, im, 90 + im.width / 2, y0 + 150 + i * 86, sc)

CARD = C.get("card", (60, 1110, 1020, 1660))
def chart(fr, t, t0, t1, label, tags):
    e = ease_pop((t - t0) * 0.8)
    x0, y0, x1, y1 = CARD; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    glass(fr, (cx - (cx - x0) * e, cy - (cy - y0) * e, cx + (x1 - cx) * e, cy + (y1 - cy) * e), r=44, ta=0.6)
    if t < t0 + 0.08: return
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    gx0, gy0, gx1, gy1 = 60, 120, x1 - x0 - 60, y1 - y0 - 50
    for i in range(5):
        yy = gy0 + (gy1 - gy0) * i / 4; d.line((gx0, yy, gx1, yy), fill=(255, 255, 255, 30), width=2)
    d.text((gx0, 26), label, font=font(44), fill=WHITE)
    thr = C["chart"].get("threshold")
    p = clamp01((t - t0 - 0.1) / max(0.5, t1 - t0 - 0.8))
    k = 3.2
    pts = [(gx0 + (gx1 - gx0) * x, gy1 - (gy1 - gy0) * (math.exp(k * x) - 1) / (math.exp(k) - 1)) for x in np.linspace(0, 1, 90) if x <= p]
    ty = gy0 + (gy1 - gy0) * 0.35
    crossed = thr and len(pts) > 1 and pts[-1][1] < ty
    col = RED if crossed else GREEN
    if thr:
        for xx in range(gx0, gx1, 34): d.line((xx, ty, xx + 18, ty), fill=RED + (255,), width=5)
        tl = text_img(thr, 40, fill=WHITE, box=RED, fnt=FONT, emo="26a0-fe0f", pad=(14, 0), radius=12)
        lay.alpha_composite(tl, (gx1 - tl.width + 12, int(ty - tl.height - 4)))
        if crossed:
            lay.alpha_composite(text_img("PRICES: A DIFFERENT STORY", 34, fill=WHITE, box=RED, fnt=FONT_B, pad=(14, 0), radius=12), (gx0, gy0 - 6))
    else:
        up = text_img("▲ UP", 34, fill=BLACK, box=GREEN, fnt=FONT_B, pad=(16, 0), radius=12)
        lay.alpha_composite(up, (gx1 - up.width + 12, 22))
    glow = Image.new("RGBA", lay.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    if len(pts) > 1:
        d.polygon(pts + [(pts[-1][0], gy1), (gx0, gy1)], fill=col + (45,))
        gd.line(pts, fill=col + (255,), width=22, joint="curve"); d.line(pts, fill=col + (255,), width=9, joint="curve")
        ex, ey = pts[-1]; d.ellipse((ex - 11, ey - 11, ex + 11, ey + 11), fill=WHITE)
    for i, (ts, txt) in enumerate(tags):
        if t >= ts:
            tg = text_img(txt, 32, fill=BLACK, box=WHITE, fnt=FONT_B, pad=(14, 0), radius=12)
            sc = ease_pop(t - ts)
            tg = tg.resize((max(1, int(tg.width * sc)), max(1, int(tg.height * sc))))
            lay.alpha_composite(tg, (gx0 + 10 + i * 270, gy0 + 6))
    fr.alpha_composite(Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)), lay), (x0, y0))

def bars(fr, t, t0, cfg):
    e = ease_pop((t - t0) * 0.8)
    x0, y0, x1, y1 = CARD; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    glass(fr, (cx - (cx - x0) * e, cy - (cy - y0) * e, cx + (x1 - cx) * e, cy + (y1 - cy) * e), r=44, ta=0.6)
    if t < t0 + 0.1: return
    for i, (lbl, em, val) in enumerate((cfg["left"], cfg["right"])):
        p = ease_out((t - t0 - 0.2 - 0.6 * i) / 0.9)
        if p <= 0: continue
        by = y0 + 120 + i * 200
        fr.alpha_composite(text_img(lbl, 46, fill=WHITE, emo=em), (x0 + 50, by - 70))
        bw = (x1 - x0 - 100) * val * p
        col = GREEN if i == 0 else RED
        ImageDraw.Draw(fr).rounded_rectangle((x0 + 50, by + 10, x0 + 50 + max(20, bw), by + 80), 20, fill=col + (255,))

def qcard(fr, t, t0, t1, text):
    """chat takeover: the off-camera question lands as a DM bubble, typing dots first"""
    u = t - t0
    s = ease_out(u / 0.25)
    y = 210 - 260 * (1 - s)
    w_ = 940
    glass(fr, (70, y, 70 + w_, y + 240), r=40, ta=0.62)
    d = ImageDraw.Draw(fr)
    d.ellipse((100, y + 30, 170, y + 100), fill=YEL)
    fr.alpha_composite(emoji("1f399-fe0f", 46), (112, int(y + 42)))
    fr.alpha_composite(text_img("Question", 36, fill=YEL, fnt=FONT_B), (180, int(y + 28)))
    if u < 0.45:
        for i in range(3):
            bb = 10 * max(0, math.sin(u * 14 - i * 0.9))
            d.ellipse((190 + i * 34, y + 140 - bb, 212 + i * 34, y + 162 - bb), fill=WHITE)
    else:
        f = font(46)
        words, lines, cur = text.split(), [], ""
        for w in words:
            nxt = (cur + " " + w).strip()
            if d.textlength(nxt, font=f) > w_ - 150: lines.append(cur); cur = w
            else: cur = nxt
        lines.append(cur)
        for i, ln in enumerate(lines[:2]): d.text((110, y + 110 + i * 60), ln, font=f, fill=WHITE)

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

def chip_row(fr, t, times, items, y=1600):
    ims = [text_img(lbl, 50, fill=BLACK, box=WHITE, fnt=FONT, emo=e, pad=(18, 4), radius=30) for e, lbl in items]
    total = sum(im.width for im in ims) + 40 * (len(ims) - 1)
    k = min(1.0, (W - 40) / total)
    ims = [im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS) for im in ims] if k < 1 else ims
    total = sum(im.width for im in ims) + 40 * (len(ims) - 1)
    x = (W - total) / 2
    arrow = text_img("›", 70, fill=YEL, fnt=FONT, stroke=6)
    for i, (ts, im) in enumerate(zip(times, ims)):
        if t >= ts:
            paste_center(fr, im, x + im.width / 2, y, ease_pop(t - ts))
            if i: paste_center(fr, arrow, x - 20, y, ease_pop(t - ts))
        x += im.width + 40

def build_receipt():
    RW, RH = 560, 640
    im = Image.new("RGBA", (RW + 40, RH + 40), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((26, 30, RW + 26, RH + 30), fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    pts = [(20, 20), (RW + 20, 20), (RW + 20, RH)] + [(RW + 20 - i * 28 - (14 if j else 0), RH + (14 if j else 0)) for i in range(RW // 28 + 1) for j in (0, 1)] + [(20, RH)]
    d.polygon(pts, fill=(252, 250, 244))
    d.text((RW / 2 + 20, 80), "RESTAURANT BILL", font=font(42), fill=(20, 20, 20), anchor="mm")
    d.line((50, 120, RW - 10, 120), fill=(180, 180, 180), width=3)
    for i, item in enumerate(["Main course", "Drinks", "Dessert", "Service"]):
        y = 150 + i * 70
        d.text((50, y), item, font=font(34, FONT_B), fill=(60, 60, 60))
        d.text((RW - 10, y), "· · ·", font=font(34, FONT_B), fill=(120, 120, 120), anchor="ra")
    d.line((50, 440, RW - 10, 440), fill=(20, 20, 20), width=4)
    d.text((50, 470), "TOTAL", font=font(52), fill=(20, 20, 20))
    return im
RECEIPT = build_receipt() if C.get("receipt_on") else None
RX, RY, RS = C.get("receipt", (W / 2 + 190, 1060, 0.78))
RECEIPT_UP = text_img("▲ UP", 90, fill=WHITE, box=RED, pad=(26, 6), radius=20)
NFA = text_img("Opinion, not financial advice", 32, fill=(220, 220, 220), fnt=FONT_B)

CTA1 = text_img(C["cta"][0], 80, fill=WHITE, stroke=9)
CTA2 = text_img(C["cta"][1], 60, fill=WHITE, box=RED, emo=C["cta"][2], pad=(40, 10), radius=60)
CTA3 = text_img(C["cta"][3], 44, fill=BLACK, box=WHITE, fnt=FONT_B, emo="1f447", pad=(24, 4), radius=24)

# ---------- schedule (output seconds) ----------
P_OUT = [T(r) for r in C.get("punches", [])]
CHART = (T(C["chart"]["start"]), T(C["chart"]["end"]), C["chart"]["label"], [(T(r), x) for r, x in C["chart"]["tags"]]) if "chart" in C else None
PH = (T(C["phone"]["start"]), T(C["phone"]["end"])) if "phone" in C else None
CL = None
if "checklist" in C:
    cl = C["checklist"]
    CL = (cl, [T(r) for r, *_ in cl["items"]], T(cl["until"]) if "until" in cl else bC)
STAMPS = [(T(st[0]), T(st[1]), text_img(st[2], 70, fill=BLACK, box=YEL, emo=st[3], pad=(30, 6), radius=24), st[4] if len(st) > 4 else 1580)
          for st in C.get("stamps", [])]
HL = [(T(a), T(b), headline(txt, tag), x, y, r) for a, b, txt, tag, x, y, r in C.get("headlines", [])]
CHIPS = ([T(r) for r, *_ in C["chips"]["items"]], [(e, l) for _, e, l in C["chips"]["items"]], T(C["chips"]["until"])) if "chips" in C else None
QC = None
if "question" in C:
    k = C["question"]["seg"]; QC = (OSTART[k] / FPS, OSTART[k + 1] / FPS, C["question"]["text"])
CNT = None
if "counter" in C:
    c = C["counter"]
    CNT = (T(c["start"]), T(c["end"]), c.get("frm", 0), c["to"], c.get("fmt", "{} " + c.get("unit", "")))
BARS = (T(C["bars"]["start"]), T(C["bars"]["end"]), C["bars"]) if "bars" in C else None
NOT = [(T(a), T(b)) for a, b in C.get("notify", [])]
MONEY_T = T(C["money"]["at"]) if MONEY else None

# ---------- render ----------
class Frames:
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"scale={W}:{H}:flags=lanczos," + GRADE + ",format=rgb24",
                                   "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
        self.cache, self.next = {}, 0
    def __getitem__(self, i):
        if i in self.cache: return self.cache[i]
        if i < self.next:                      # segments jump back in the clip: restart the decoder
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
FRAMINGS = [(1.45, 300), (1.9, 160), (1.25, 420)]
end_bg = None
na = 0
for n in range(NF):
    t = n / FPS
    si = SIDX[min(n, NV - 1)]
    src = FRAMES[si]
    if n < NV:
        k = int(np.searchsorted(OSTART, n, side="right") - 1)
        kind = SEGS[k][0]
        u = (n - OSTART[k]) / FPS
        fx_, fy_ = face[si]
        sx = sy = 0.0
        if kind == "hook":
            z, off = C.get("hook_z", 2.15) + 0.6 * (1 - ease_out(t / 0.15)) + 0.05 * t, 120 if "hook_z" not in C else 60
            if t < 0.35: sx, sy = shake(t, 0, 20, 0.35)
        elif kind == "q":
            z, off = 1.3 + 0.15 * u / 3, 40           # face mid-frame, under the question card
        else:
            na_k = sum(1 for kk in SEGS[:k] if kk[0] == "a")
            fr_list = C.get("framings", FRAMINGS)
            z, off = fr_list[na_k % len(fr_list)]
            z *= (1 + 0.08 * (1 - ease_out(u / 0.12))) * (1 + 0.015 * u)
        bottom_busy = (CL and t >= CL[1][0] - 0.05 and t < CL[2]) or (CHART and CHART[0] <= t < CHART[1]) or (BARS and BARS[0] <= t < BARS[1])
        if bottom_busy and kind == "a": z, off = C.get("busy", (1.5, 200))      # face high, the lower half holds the card
        for p in P_OUT:
            if p <= t < p + 0.7:
                z *= 1 + 0.22 * ease_out((t - p) / 0.07) * (1 - clamp01((t - p - 0.5) / 0.2)); sx, sy = shake(t, p, 14)
        if PH and PH[0] <= t < PH[1] + 0.25:                    # slide him left so the phone sits beside his face
            fx_ += 220 * ease_out((t - PH[0]) / 0.3) * (1 - ease_out((t - PH[1]) / 0.25))
        fr = Image.fromarray(warp(src, affine(z, fx_, fy_ + off, sx, sy))).convert("RGBA")

        if t < bH:
            title(fr, t)
            if MONEY and t >= MONEY_T: paste_center(fr, MONEY, W / 2, C.get("money_y", 1180), 2.2 - 1.2 * ease_out((t - MONEY_T) / 0.12), -4)
            if RECEIPT is not None:
                e = ease_out((t - 0.1) / 0.35)
                paste_center(fr, RECEIPT, RX, RY + 500 * (1 - e), RS, -6)
                if t >= 0.9: paste_center(fr, RECEIPT_UP, RX + 60 * RS / 0.78, RY + 250 * RS / 0.78, (2.0 - ease_out((t - 0.9) / 0.1)) * RS / 0.78, 8)
            for a, b in NOT[:1]:
                if a <= t < b: paste_center(fr, NOTIF, W / 2, 1250 + 300 * (1 - ease_out((t - a) / 0.3)))
            two_line_card(fr, C["quote"][0], C["quote"][1], C.get("quote_y", 1580), ease_pop(t - 0.1))
            flash(fr, WHITE, 0.85 * (1 - t / 0.12))
        else:
            if QC and QC[0] <= t < QC[1]: qcard(fr, t, QC[0], QC[1], QC[2])
            if CHART and CHART[0] <= t < CHART[1]: chart(fr, t, CHART[0], CHART[1], CHART[2], CHART[3])
            if BARS and BARS[0] <= t < BARS[1]: bars(fr, t, BARS[0], BARS[2])
            if CL and CL[1][0] <= t < CL[2]: checklist(fr, t, CL[0], CL[1])
            if PH and PH[0] <= t < PH[1] + 0.25:
                e = ease_out((t - PH[0]) / 0.3) * (1 - ease_out((t - PH[1]) / 0.25))
                paste_center(fr, PHONE, 820 + 500 * (1 - e), 900, 1.0, -8 + 8 * (1 - e))
            for a, b, im, sy_ in STAMPS:
                if a <= t < b: paste_center(fr, im, W / 2, sy_, 2.0 - ease_out((t - a) / 0.1), -3)
            for a, b, im, x, y, r in HL:
                if a <= t < b: paste_center(fr, im, x, y, 2.0 - ease_out((t - a) / 0.1), r)
            if CHIPS and CHIPS[0][0] <= t < CHIPS[2]: chip_row(fr, t, CHIPS[0], CHIPS[1])
            for a, b in NOT[1:]:
                if a <= t < b: paste_center(fr, NOTIF, W / 2, 300 - 260 * (1 - ease_out((t - a) / 0.3)), 1.0)
            if CNT and CNT[0] <= t < CNT[1] + 1.5:
                v = int(round(CNT[2] + (CNT[3] - CNT[2]) * ease_out((t - CNT[0]) / max(0.2, CNT[1] - CNT[0]))))
                paste_center(fr, text_img(CNT[4].format(v).strip(), 170, fill=BLACK, box=YEL, emo="1f4b8", pad=(40, 10), radius=40), W / 2, C.get("counter_y", 1300),
                             ease_pop(t - CNT[0]), -3)
            if any(p <= t < p + 0.08 for p in P_OUT): flash(fr, WHITE, 0.3)
            if u < 0.08 and OSTART[k] / FPS == bH: flash(fr, WHITE, 0.6)
    else:
        u = t - bC
        if end_bg is None:
            end_bg = (cv2.GaussianBlur(warp(src, affine(1.4, face[si][0], face[si][1] + 300)), (0, 0), 20) * 0.45).astype(np.uint8)
        fr = Image.fromarray(warp(end_bg, affine(1 + 0.04 * u / (TAIL / FPS), 540, 960))).convert("RGBA")
        paste_center(fr, CTA1, W / 2, 720, ease_pop(u - 0.02))
        if u >= 0.4:
            paste_center(fr, CTA2, W / 2, 900, ease_pop(u - 0.4) * (1 + 0.04 * math.sin((u - 0.4) * 12)))
            paste_center(fr, emoji("1f446", 110), W / 2 + 340, 1040 + 14 * math.sin(t * 10), ease_pop(u - 0.55))
        if u >= 0.9: paste_center(fr, CTA3, W / 2, 1160, ease_pop(u - 0.9))
        if C.get("nfa"): paste_center(fr, NFA, W / 2, 1800, 1.0, 0, clamp01((u - 0.3) / 0.3))
        flash(fr, WHITE, 0.8 * (1 - u / 0.15))
    if t >= bH:
        dr = ImageDraw.Draw(fr)
        dr.rectangle((0, 0, W, 12), fill=(0, 0, 0, 110)); dr.rectangle((0, 0, int(W * (n + 1) / NF), 12), fill=YEL + (255,))
    out = fr.convert("RGB")
    if any(abs(t - p) < 0.5 / FPS for p in PREVIEW): out.save(f"{WORK}/prev_{t:05.2f}.jpg", quality=85)
    enc.stdin.write(out.tobytes())
enc.stdin.close(); enc.wait(); FRAMES.p.kill()

# ---------- audio ----------
at = ";".join(f"[0:a:0]atrim={a/FPS}:{b/FPS},asetpts=PTS-STARTPTS,volume={Q_GAIN if k == 'q' else 0}dB,"
              f"afade=t=in:d=0.012,afade=t=out:st={(b-a)/FPS-0.015}:d=0.015[a{i}]" for i, (k, a, b) in enumerate(SEGF))
afc = (f"{at};{''.join(f'[a{i}]' for i in range(len(SEGF)))}concat=n={len(SEGF)}:v=0:a=1,aformat=channel_layouts=mono,"
       "highpass=f=80,afftdn=nr=8:nf=-42,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1:g=3.5,"
       "highshelf=f=8000:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2[o]")
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

def slap():
    t = tt(0.14); n = rng.standard_normal(len(t))
    return (n - lp(n, 0.3)) * np.exp(-t * 45) * 0.6 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30) * 0.6

def coin():
    t = tt(0.35); f = np.where(t < 0.08, 988, 1319)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.35

def riser(d):
    t = tt(d); f = 200 * (2 ** (t / d * 3))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + 0.25 * rng.standard_normal(len(t)) * (t / d)
    return s * (t / d) ** 2 * 0.6

FXA = np.zeros(N, np.float32)
def put(sig, at_, g=1.0):
    i = int(max(0, at_) * SR); j = min(N, i + len(sig))
    if i < N: FXA[i:j] += sig[:j - i] * g

put(boom(1.2), 0.0, 1.0); put(whoosh(0.3, False), 0.0, 0.5)
if MONEY: put(coin(), MONEY_T, 0.9); put(boom(0.6), MONEY_T, 0.6)
if NOT: put(ding(1568, 0.5), NOT[0][0] + 0.1, 0.6); put(ding(2093, 0.5), NOT[0][0] + 0.22, 0.4)
put(whoosh(0.3, False), bH - 0.15, 0.5)
if QC: put(pop(), QC[0], 0.5); put(ding(1760, 0.3), QC[0] + 0.45, 0.4)
if CHART: put(whoosh(0.3), CHART[0] - 0.1, 0.5); put(riser(min(2.5, CHART[1] - CHART[0])), CHART[0] + 0.1, 0.5); [put(pop(), a, 0.4) for a, _ in CHART[3]]
if BARS: put(whoosh(0.3), BARS[0] - 0.1, 0.5); put(pop(), BARS[0] + 0.2, 0.5); put(boom(0.6), BARS[0] + 0.8, 0.6)
if CL:
    for ts in CL[1]: put(pop(), ts, 0.6); put(ding(1568, 0.35), ts + 0.02, 0.35)
if PH: put(whoosh(0.3), PH[0] - 0.05, 0.6); put(ding(1568, 0.4), PH[0] + 0.3, 0.4)
for a, *_ in STAMPS: put(slap(), a, 0.7)
for a, *_ in HL: put(slap(), a, 0.8)
if CHIPS: [put(pop(), a, 0.5) for a in CHIPS[0]]
if RECEIPT is not None: put(whoosh(0.35), 0.1, 0.6); put(boom(0.6), 0.9, 0.7)
if CNT: [put(coin(), CNT[0] + i * 0.12, 0.35) for i in range(int((CNT[1] - CNT[0]) / 0.12) + 1)]
for a, _ in NOT[1:]: put(ding(1568, 0.5), a + 0.1, 0.5)
for p in P_OUT: put(boom(0.6), p, 0.6); put(whoosh(0.2), p - 0.1, 0.4)
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
