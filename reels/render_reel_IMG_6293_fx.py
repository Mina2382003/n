import subprocess, numpy as np, wave, math, os, sys
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

S = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(S, "reel_fx.mp4")
WORK = os.environ.get("FX_WORK", os.path.join(S, "work"))   # cached masks + clean plate
FONT = S + "/font/package/900Black/Cairo_900Black.ttf"
FONT_B = S + "/font/package/800ExtraBold/Cairo_800ExtraBold.ttf"
EMO = S + "/emoji/package/img/apple/64/"
SEG_MODEL = S + "/selfie_multiclass_256x256.tflite"
W, H, FPS, SR = 1080, 1920, 30, 48000
GRADE = "eq=contrast=1.08:saturation=1.22,colorbalance=rm=0.03:bm=-0.03,unsharp=5:5:0.6,vignette=PI/5"
os.makedirs(WORK, exist_ok=True)

# source frames: cold open = "ده يأثر عليك" lifted from the answer, Q = off-camera question (sped up),
# A = the answer; frames 351-389 are silent and run under the cover
COLD = (268, 295)
Q = (22, 102); Q_SPEED = 80 / 70                   # 80 source frames played as 70
A = (134, 351)
VSEGS = [COLD, Q, A]                               # what we hear
SEG_GAIN = [0, 12, 0]                              # dB; the question mic is ~14 dB quieter than the answer
SEG_TEMPO = [1, Q_SPEED, 1]
SIDX = (list(range(*COLD)) + [Q[0] + round(i * Q_SPEED) for i in range(70)] + list(range(A[0], 389)))
NV = (COLD[1] - COLD[0]) + 70 + (A[1] - A[0])
TAIL = 99
NF = NV + TAIL
DUR = NF / FPS
bQ = (COLD[1] - COLD[0]) / FPS                     # 0.9   cold open ends -> question
bA = bQ + 70 / FPS                                 # 3.233 question ends -> answer
bC = bA + (A[1] - A[0]) / FPS                      # 10.467 answer ends -> magazine cover
at = lambda src_s: bA + src_s - A[0] / FPS         # answer source time -> output time
# word beats, from the answer's energy envelope (pauses at 4.80, 5.92, 6.48, 7.48, 8.56-8.94, 9.84, 10.34 s)
T_DATA, T_YOU, T_HAVE, T_MUCH = at(4.88), at(5.92), at(6.50), at(6.94)
T_USELESS, T_AFFECT, T_KEEPS, T_BETTER = at(7.48), at(8.94), at(9.84), at(10.36)
FX_, FY_ = 560, 525                                # face centre in the (rotated) source frame
print("cut points", bQ, bA, bC, "total", DUR)

YEL, RED, WHITE, BLACK = (255, 214, 0), (235, 30, 45), (255, 255, 255), (0, 0, 0)
HUD = (80, 255, 200)

# ---------- prep: person masks + clean background plate (cached) ----------
def prepare():
    if not os.path.exists(WORK + "/masks.npy"):
        import mediapipe as mp
        from mediapipe.tasks.python import vision, BaseOptions
        seg = vision.ImageSegmenter.create_from_options(vision.ImageSegmenterOptions(
            base_options=BaseOptions(model_asset_path=SEG_MODEL), output_confidence_masks=True))
        dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", "scale=540:960", "-f", "rawvideo",
                                "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        ms = []
        while len(b := dec.stdout.read(540 * 960 * 3)) == 540 * 960 * 3:
            img = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.frombuffer(b, np.uint8).reshape(960, 540, 3).copy())
            ms.append((np.clip(1 - seg.segment(img).confidence_masks[0].numpy_view(), 0, 1) * 255).astype(np.uint8).reshape(960, 540))
        np.save(WORK + "/masks.npy", np.stack(ms))
    masks = np.load(WORK + "/masks.npy")
    if not os.path.exists(WORK + "/plate.png"):
        f = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", "0.2", "-i", SRC, "-frames:v", "1", "-f", "rawvideo",
                                          "-pix_fmt", "bgr24", "-"], capture_output=True).stdout, np.uint8).reshape(H, W, 3)
        pm = cv2.resize(masks.max(0), (W, H))
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); L = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        green = (hsv[..., 0] > 25) & (hsv[..., 0] < 95) & (hsv[..., 1] > 35)        # keep the plant in the background
        dark = (((L.astype(int) < cv2.GaussianBlur(L, (0, 0), 25).astype(int) - 28) | (L < 150)) & ~green).astype(np.uint8) * 255
        dark[:560] = 0
        dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        fg = cv2.morphologyEx(np.maximum(dark, (pm > 90).astype(np.uint8) * 255), cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
        keep = np.zeros_like(fg)
        for i in range(1, n):
            if st[i, 4] > 20000: keep[lab == i] = 255
        cnt, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        keep = np.zeros_like(keep); cv2.drawContours(keep, cnt, -1, 255, -1)
        cv2.imwrite(WORK + "/fg_static.png", keep)
        # fill the subject hole with a multi-scale normalized convolution (the backdrop is a smooth seamless)
        hole = cv2.dilate(keep, np.ones((45, 45), np.uint8)) > 0
        img = f.astype(np.float32); valid = (~hole).astype(np.float32)
        small = lambda a: cv2.resize(a, (270, 480), interpolation=cv2.INTER_AREA)
        fill = None
        for s, th in ((60, 0), (25, 0.15), (8, 0.3)):
            num = cv2.GaussianBlur(small(img * valid[..., None]), (0, 0), s); den = cv2.GaussianBlur(small(valid), (0, 0), s)[..., None]
            est = num / np.maximum(den, 1e-6)
            fill = est if fill is None else np.where(den > th, est, fill)
        fill = cv2.resize(cv2.GaussianBlur(fill, (0, 0), 3), (W, H), interpolation=cv2.INTER_CUBIC)
        soft = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 10)[..., None]
        plate = img * (1 - soft) + fill * soft + np.random.default_rng(1).normal(0, 1.6, img.shape) * soft
        cv2.imwrite(WORK + "/plate.png", np.clip(plate, 0, 255).astype(np.uint8))
    return masks

MASKS = prepare()
FG_STATIC = cv2.imread(WORK + "/fg_static.png", 0)
_pu = cv2.dilate(cv2.resize(MASKS.max(0), (W, H)), np.ones((25, 25), np.uint8))
CHAIR = cv2.GaussianBlur(((FG_STATIC > 0) & (_pu < 90)).astype(np.float32), (0, 0), 3)
PLATE = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", WORK + "/plate.png", "-vf", GRADE + ",format=rgb24",
                                      "-f", "rawvideo", "-"], capture_output=True).stdout, np.uint8).reshape(H, W, 3)

def person(si):
    a, b = max(0, si - 1), min(len(MASKS), si + 2)
    m = cv2.resize(MASKS[a:b].mean(0).astype(np.float32) / 255, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(np.clip((m - 0.35) / 0.3, 0, 1), (0, 0), 1.5)

STATIC_OCC = cv2.GaussianBlur(cv2.dilate(FG_STATIC, np.ones((21, 21), np.uint8)).astype(np.float32) / 255, (0, 0), 4)

def occluder(si, solid=False):
    # solid: the whole static subject+chair silhouette, for when the background behind it is swapped (dolly zoom)
    return np.maximum(person(si), STATIC_OCC if solid else CHAIR)

# ---------- camera ----------
def affine(z, cx, cy, sx=0.0, sy=0.0):
    cw, ch = W / z, H / z
    cx = min(max(cx - sx / z, cw / 2), W - cw / 2); cy = min(max(cy - sy / z, ch / 2), H - ch / 2)
    x0, y0 = cx - cw / 2, cy - ch / 2
    return np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])

def warp(a, M, border=cv2.BORDER_REPLICATE):
    return cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=border)

def zoom_blur(src, zs, cx, cy, sx=0.0, sy=0.0):
    """average a few zoom levels -> motion blur along the zoom"""
    acc = np.zeros((H, W, 3), np.float32)
    for z in zs: acc += warp(src, affine(z, cx, cy, sx, sy))
    return (acc / len(zs)).astype(np.uint8)

def apply_pt(M, x, y):
    return M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]

def shake(t, t0, amp, d=0.32):
    k = max(0.0, 1 - (t - t0) / d)
    return amp * k * math.sin(t * 95), amp * 0.8 * k * math.cos(t * 81)

ease_out = lambda u: 1 - (1 - min(max(u, 0), 1)) ** 3
ease_io = lambda u: (lambda v: 3 * v * v - 2 * v * v * v)(min(max(u, 0), 1))
clamp01 = lambda u: min(max(u, 0.0), 1.0)

# ---------- graphics helpers ----------
_emo, _font = {}, {}
def emoji(code, size):
    k = (code, size)
    if k not in _emo:
        _emo[k] = Image.open(EMO + code + ".png").convert("RGBA").resize((size, size), Image.LANCZOS)
    return _emo[k]

def font(size, f=FONT):
    if (f, size) not in _font: _font[(f, size)] = ImageFont.truetype(f, size)
    return _font[(f, size)]

def rtl(txt):
    return "rtl" if any("؀" <= c <= "ۿ" for c in txt) else None

_txt = {}
def text_img(txt, size, fill=WHITE, stroke=10, box=None, pad=(34, 6), fnt=FONT, emo=None, emo_left=True, radius=26, maxw=960):
    key = (txt, size, fill, stroke, box, pad, fnt, emo, emo_left, radius, maxw)
    if key in _txt: return _txt[key]
    f = font(size, fnt)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, stroke_width=stroke, direction=rtl(txt))
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
    dr.text((tx - l, ty - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=BLACK, direction=rtl(txt))
    if emo:
        ex = x0 if emo_left else tx + tw + gap
        im.alpha_composite(emoji(emo, es), (ex, oy + (ch - es) // 2))
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    _txt[key] = im
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

def vgrad(w, h, a0, a1, stop=1.0):
    g = np.clip(np.linspace(0, 1, h) / stop, 0, 1)
    return Image.fromarray(np.repeat((a0 + (a1 - a0) * g)[:, None], w, 1).astype(np.uint8), "L")

def glass(fr, box, r=40, tint=(18, 18, 26), ta=0.5, blur=22, border=120):
    """liquid glass panel: frosted copy of what's behind + tint + rim light + top sheen"""
    x0, y0, x1, y1 = (int(v) for v in box)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    w, h = x1 - x0, y1 - y0
    if w < 8 or h < 8: return
    r = min(r, h // 2, w // 2)
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 54, 40 + w, 54 + h), r, fill=(0, 0, 0, 90))
    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)), (x0 - 40, y0 - 40))
    reg = fr.crop((x0, y0, x1, y1)).convert("RGB").filter(ImageFilter.GaussianBlur(blur))
    reg = Image.blend(reg, Image.new("RGB", (w, h), tint), ta)
    m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    fr.paste(reg, (x0, y0), m)
    sheen = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    sheen.putalpha(ImageChops.multiply(vgrad(w, h, 60, 0, 0.5), m))
    fr.alpha_composite(sheen, (x0, y0))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle((0, 0, w - 1, h - 1), r, outline=(255, 255, 255, border), width=3)
    fr.alpha_composite(ov, (x0, y0))

def glass_caption(fr, txt, size, cx, cy, s=1.0, emo=None, tint=(18, 18, 26), ta=0.5):
    if s <= 0.01: return
    ti = text_img(txt, size, fill=WHITE, stroke=0, emo=emo)
    bw, bh = (ti.width + 60) * s, (ti.height + 22) * s
    glass(fr, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), r=int(bh / 2), tint=tint, ta=ta)
    paste_center(fr, ti, cx, cy, s)

def flash(fr, col, a):
    if a > 0: fr.alpha_composite(Image.new("RGBA", (W, H), col + (int(255 * min(1, a)),)))

def with_occlusion(fr_np, overlay, occ):
    """composite an RGBA overlay *behind* the subject"""
    ov = np.asarray(overlay).copy()
    ov[..., 3] = (ov[..., 3].astype(np.float32) * (1 - occ)).astype(np.uint8)
    out = Image.fromarray(fr_np).convert("RGBA"); out.alpha_composite(Image.fromarray(ov, "RGBA"))
    return out

# ---------- headline storm ----------
def headline(txt, tag):
    f = font(58); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), txt, font=f, direction=rtl(txt))
    w, h = r - l + 70, b - t + 110
    im = Image.new("RGBA", (w + 30, h + 30), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((18, 22, w + 18, h + 22), fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)))
    dr.rectangle((10, 10, w + 10, h + 10), fill=(246, 241, 228))
    dr.rectangle((10, 10, w + 10, 52), fill=RED)
    tg = font(26, FONT_B); dr.text((28, 13), tag, font=tg, fill=WHITE, direction=rtl(tag))
    dr.line((28, h - 4, w - 8, h - 4), fill=(60, 60, 60), width=2)
    dr.text((10 + 35 - l, 62 - t + 8), txt, font=f, fill=(15, 15, 15), direction=rtl(txt))
    return im
HEADLINES = [  # appear-time, image, x, y, rotation
    (T_DATA + 0.22, headline("DATA IS THE NEW OIL", "BREAKING"), 290, 250, 7),
    (T_DATA + 0.34, headline("اجمع كل حاجة!", "عاجل"), 800, 380, -6),
    (T_DATA + 0.46, headline("BIG DATA = BIG MONEY?", "TRENDING"), 330, 640, -4),
    (T_DATA + 0.58, headline("كل كليك ليه تمن", "عاجل"), 790, 760, 5),
    (T_DATA + 0.70, headline("TRACK EVERYTHING", "BREAKING"), 520, 960, -8),
]
SWEEP = np.zeros((H, W), np.float32)
_yy, _xx = np.mgrid[0:H, 0:W]
SWEEP_D = (_xx + 0.45 * _yy).astype(np.float32)

# ---------- growth curve card ----------
CARD = (70, 1000, 1010, 1510)
def draw_chart(fr, t):
    x0, y0, x1, y1 = CARD
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    cx0, cy0, cx1, cy1 = 60, 120, x1 - x0 - 60, y1 - y0 - 60
    for i in range(5):
        yy = cy0 + (cy1 - cy0) * i / 4; d.line((cx0, yy, cx1, yy), fill=(255, 255, 255, 30), width=2)
    d.line((cx0, cy1, cx1, cy1), fill=(255, 255, 255, 110), width=3)
    p = clamp01((t - T_MUCH - 0.07) / (T_USELESS - T_MUCH - 0.07))
    k = 3.4
    xs = np.linspace(0, 1, 90)
    pts = [(cx0 + (cx1 - cx0) * x, cy1 - (cy1 - cy0) * (math.exp(k * x) - 1) / (math.exp(k) - 1)) for x in xs if x <= p]
    title = text_img("حجم الـ Data", 38, stroke=0, fnt=FONT_B, emo="1f4ca", emo_left=False)
    lay.alpha_composite(title, (cx1 - title.width + 12, 18))
    rows = int(10 ** (3 + 3.3 * p)) if p > 0 else 0
    d.text((cx0, 30), f"{rows:,} rows", font=font(40, FONT_B), fill=YEL)
    glow = Image.new("RGBA", lay.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    if len(pts) > 1:
        d.polygon(pts + [(pts[-1][0], cy1), (cx0, cy1)], fill=YEL + (45,))
        gd.line(pts, fill=YEL + (255,), width=22, joint="curve")
        d.line(pts, fill=YEL + (255,), width=9, joint="curve")
        ex, ey = pts[-1]
        gd.ellipse((ex - 22, ey - 22, ex + 22, ey + 22), fill=YEL + (255,))
        d.ellipse((ex - 11, ey - 11, ex + 11, ey + 11), fill=WHITE)
        if p > 0.6:
            lb = text_img("Data", 34, fill=BLACK, stroke=0, box=YEL, fnt=FONT_B, pad=(16, 0), radius=14)
            lay.alpha_composite(lb, (int(min(ex - lb.width + 10, cx1 - lb.width)), int(ey + 6)))
    q = clamp01((t - T_USELESS) / 0.35)
    if q > 0:
        vp = [(cx0 + (cx1 - cx0) * x, cy1 - 26 - 6 * math.sin(x * 19)) for x in np.linspace(0, q, 60)]
        gd.line(vp, fill=(255, 59, 48, 255), width=22, joint="curve")
        d.line(vp, fill=(255, 59, 48, 255), width=9, joint="curve")
        lb = text_img("الفايدة", 32, fill=WHITE, stroke=0, box=(255, 59, 48), fnt=FONT_B, pad=(16, 0), radius=14, emo="1f4c9", emo_left=False)
        lay.alpha_composite(lb, (int(vp[-1][0] - lb.width / 2 if q < 1 else cx1 - lb.width), int(cy1 - 26 - lb.height - 16)))
    lay = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)).point(lambda v: v), lay)
    fr.alpha_composite(lay, (x0, y0))
STAMP = text_img("مالهاش لازمة", 84, fill=WHITE, stroke=0, box=RED, emo="274c", radius=20)

# ---------- frame break ----------
def build_navy():
    g = np.linspace(0, 1, H)[:, None, None]
    bg = ((1 - g) * np.array([12, 16, 38]) + g * np.array([42, 18, 58])) * np.ones((1, W, 1))
    glow = np.exp(-(((_xx - 540) / 520.0) ** 2 + ((_yy - 760) / 600.0) ** 2))[..., None] * np.array([255, 190, 0]) * 0.35
    bg = bg + glow + np.random.default_rng(3).normal(0, 4, (H, W, 1))
    return np.clip(bg, 0, 255).astype(np.uint8)
NAVY = build_navy()
FB_Z, FB_CX, FB_CY = 1.3, 560, 860
FB_WIN = (60, 730, 1020, 1860)          # window in content coords: top edge cuts across the shoulders
def frame_break(src, occ, t):
    u = ease_out((t - T_KEEPS) / 0.2)
    k = 1.0 - 0.30 * u
    k += 0.04 * math.sin(clamp01((t - T_KEEPS) / 0.35) * math.pi) * (1 - u * 0.3)   # small overshoot wobble
    rot = -3.0 * u
    M = affine(FB_Z, FB_CX, FB_CY)
    C = warp(src, M); A = warp(occ, M, cv2.BORDER_CONSTANT)
    win = np.zeros((H, W), np.float32); x0, y0, x1, y1 = FB_WIN; win[y0:y1, x0:x1] = 1
    brd = np.zeros((H, W), np.float32); brd[y0 - 18:y1 + 18, x0 - 18:x1 + 18] = 1
    ap = A * (1 - win)                                   # the person outside the window sits over the border
    alpha = np.maximum(win, ap + brd * (1 - ap))
    out_rgb = (C * ap[..., None] + 255.0 * (brd * (1 - ap))[..., None]) / np.maximum(alpha, 1e-4)[..., None]
    rgb = np.where(win[..., None] > 0, C, out_rgb).astype(np.float32)
    R = cv2.getRotationMatrix2D((540, 960), rot, k); R[1, 2] += 110 * u
    rgb_s = cv2.warpAffine(rgb, R, (W, H), flags=cv2.INTER_LINEAR)
    a_s = cv2.warpAffine(alpha, R, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    shadow = cv2.GaussianBlur(cv2.warpAffine(brd, R, (W, H)), (0, 0), 24)[..., None]
    shadow = np.roll(shadow, 26, 0) * 0.65
    out = NAVY.astype(np.float32) * (1 - shadow)
    out = out * (1 - a_s) + rgb_s * a_s
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------- digital zoom HUD ----------
SCAN = Image.new("RGBA", (W, H), (0, 0, 0, 0))
_sd = ImageDraw.Draw(SCAN)
for yy in range(0, H, 4): _sd.line((0, yy, W, yy), fill=(0, 0, 0, 26))
DZ_STEPS = [(T_YOU, 1.45), (T_YOU + 0.3, 1.95), (T_HAVE, 2.5)]
def hud(fr, M, z, t, ts):
    d = ImageDraw.Draw(fr)
    fx, fy = apply_pt(M, FX_, FY_)
    hw, hh = 120 * z, 150 * z
    lock = clamp01((t - ts) / 0.15)
    pad = 60 * (1 - ease_out(lock))
    bx0, by0, bx1, by1 = fx - hw - pad, fy - hh - pad, fx + hw + pad, fy + hh + pad
    L_ = 56
    for (cx, cy, sx, sy) in [(bx0, by0, 1, 1), (bx1, by0, -1, 1), (bx0, by1, 1, -1), (bx1, by1, -1, -1)]:
        d.line((cx, cy, cx + sx * L_, cy), fill=HUD + (255,), width=7); d.line((cx, cy, cx, cy + sy * L_), fill=HUD + (255,), width=7)
    d.line((fx - 22, fy, fx + 22, fy), fill=HUD + (170,), width=3); d.line((fx, fy - 22, fx, fy + 22), fill=HUD + (170,), width=3)
    tl = text_img("TARGET LOCKED", 30, fill=HUD, stroke=4, fnt=FONT_B)
    fr.alpha_composite(tl, (int(max(20, bx0)), int(max(30, by0 - tl.height - 4))))
    if int(t * 4) % 2 == 0: d.ellipse((50, 62, 76, 88), fill=(255, 40, 40))
    d.text((88, 50), "REC", font=font(34, FONT_B), fill=WHITE, stroke_width=3, stroke_fill=BLACK)
    zt = f"ZOOM ×{z:.1f}"
    d.text((W - 60 - d.textlength(zt, font=font(34, FONT_B)), 50), zt, font=font(34, FONT_B), fill=HUD, stroke_width=3, stroke_fill=BLACK)
    fr.alpha_composite(SCAN)

# ---------- magazine cover ----------
def masthead():
    f = font(420); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), "DATA", font=f)
    im = Image.new("RGBA", (r - l, b - t), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-l, -t), "DATA", font=f, fill=(225, 29, 42))
    if im.width > 1000: im = im.resize((1000, int(im.height * 1000 / im.width)), Image.LANCZOS)
    return im
MAST = masthead()
MAST_Y = 300
STRAP = text_img("THE BUSINESS ISSUE  •  ISSUE 01  •  2026", 30, fill=BLACK, stroke=0, fnt=FONT_B)
COVER_LINES = [
    (bC + 0.40, text_img("اجمع الـ Data اللي هتستخدمها", 48, stroke=0, fnt=FONT_B, emo="2705", emo_left=False)),
    (bC + 0.70, text_img("Data كتير مالهاش لازمة", 48, stroke=0, fnt=FONT_B, emo="274c", emo_left=False)),
    (bC + 1.00, text_img("ركّز على اللي بيفرّق", 48, stroke=0, fnt=FONT_B, emo="2705", emo_left=False)),
]
COVER_HEAD = text_img("مش كل Data مفيدة!", 96, fill=YEL, stroke=11)
CTA = text_img("Follow for more business secrets", 64, fill=WHITE, stroke=0, box=RED, emo="1f525", radius=60, pad=(46, 10))
MAG_Z, MAG_CX, MAG_CY = 1.12, 560, 860

# ---------- captions (bottom) ----------
CAP_Y = 1590
caps = [  # start, end, kind, text, emoji, rotation
    (0.0, bQ, "glassred", "ده يأثر عليك", "1f62c", 0),
    (bQ + 0.06, bQ + 0.96, "glass", "هل الهدف", None, 0),
    (bQ + 0.96, bQ + 1.77, "glass", "أي Platform", None, 0),
    (bQ + 1.77, bA, "glass", "تجمع Data أكتر؟", "1f914", 0),
    (bA + 0.03, T_DATA, "red", "لأ!", "1f6ab", -5),
    (T_DATA, T_YOU, "glass", "الداتا مهمة", "2705", 0),
    (T_YOU, T_HAVE, "glass", "بس إنك إنت", "1f448", 0),
    (T_HAVE, T_MUCH, "glass", "يبقى عندك", None, 0),
    (T_MUCH, T_USELESS, "yel", "داتا كتير", "1f4c8", 3),
    (T_USELESS, T_AFFECT, "red", "مالهاش لازمة", "274c", -3),
    (T_AFFECT, T_KEEPS, "glassred", "ده يأثر عليك", "1f62c", 0),
    (T_KEEPS, T_BETTER, "glass", "ما يخلّيكش", None, 0),
    (T_BETTER, bC, "yel", "تبقى أحسن خالص", "1f4a5", 4),
]
def draw_caption(fr, t):
    for st, en, kind, txt, emo, rot in caps:
        if not st <= t < en: continue
        s = ease_pop(t - st); cy = CAP_Y if not (T_KEEPS <= t < T_BETTER) else 1800
        if kind == "red": paste_center(fr, text_img(txt, 190 if txt == "لأ!" else 120, fill=WHITE, stroke=0, box=RED, emo=emo), W / 2, cy, s, rot)
        elif kind == "yel": paste_center(fr, text_img(txt, 120, fill=BLACK, stroke=0, box=YEL, emo=emo), W / 2, cy, s, rot)
        elif kind == "glassred": glass_caption(fr, txt, 104, W / 2, cy, s, emo, tint=(120, 10, 20), ta=0.55)
        else: glass_caption(fr, txt, 104, W / 2, cy, s, emo)

HOOK = text_img("Data أكتر ≠ نجاح أكتر", 92, fill=WHITE, stroke=0, box=RED, emo="274c")
Q_TAG = text_img("السؤال", 44, fill=BLACK, stroke=0, box=YEL, fnt=FONT_B, emo="1f399-fe0f", pad=(22, 0), radius=18)

# ---------- decode graded frames ----------
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-vf", GRADE + ",format=rgb24", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
FRAMES = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                        WORK + "/video_only.mp4"], stdin=subprocess.PIPE)
PREVIEW = [float(x) for x in os.environ.get("FX_PREVIEW", "").split(",") if x]

for n in range(NF):
    t = n / FPS
    si = SIDX[min(n, len(SIDX) - 1)]
    src = FRAMES[si]

    if t < bQ:
        # ---- Cold open: Snap Zoom straight onto his strongest line ----
        u = t / 0.12
        sx, sy = shake(t, 0.0, 22, 0.35)
        if u < 1:
            z1 = 3.0 - 0.8 * ease_out(u)
            arr = zoom_blur(src, [z1 + 0.2 * j for j in range(4)], FX_, FY_ + 70, sx, sy)
        else:
            arr = warp(src, affine(2.2 + 0.1 * t / bQ, FX_, FY_ + 70, sx, sy))
        fr = Image.fromarray(arr).convert("RGBA")
        paste_center(fr, HOOK, W / 2, 300, ease_pop(t - 0.05), -3)
        flash(fr, WHITE, 0.8 * (1 - t / 0.12))
    elif t < bA:
        # ---- the question, with him on camera ----
        u = (t - bQ) / (bA - bQ)
        fr = Image.fromarray(warp(src, affine(1.3 + 0.18 * u, FX_, FY_ + 250))).convert("RGBA")
        paste_center(fr, HOOK, W / 2, 260, 0.8, -3)
        paste_center(fr, Q_TAG, W / 2, CAP_Y - 125, ease_pop(t - bQ - 0.02))
        flash(fr, WHITE, 0.5 * (1 - (t - bQ) / 0.1))
    elif t < T_DATA:
        # ---- Snap Zoom on "No!" ----
        u = (t - bA) / 0.12
        sx, sy = shake(t, bA, 24)
        if u < 1:
            z1 = 3.4 - 1.0 * ease_out(u); zs = [z1 + 0.25 * j for j in range(4)]
            arr = zoom_blur(src, zs, FX_, FY_ + 60, sx, sy)
        else:
            arr = warp(src, affine(2.4, FX_, FY_ + 60, sx, sy))
        fr = Image.fromarray(arr).convert("RGBA")
        flash(fr, WHITE, 0.9 * (1 - (t - bA) / 0.14)); flash(fr, (255, 40, 40), 0.35 * (1 - (t - bA) / 0.25))
    elif t < T_YOU:
        # ---- Studio Reveal pull-back + Headline Storm behind him ----
        u = ease_out((t - T_DATA) / 0.5)
        z = 2.4 - 1.4 * u
        M = affine(z, FX_, FY_ + 60 + (960 - FY_ - 60) * u)
        arr = warp(src, M) if u > 0.9 else zoom_blur(src, [z, z + 0.035, z + 0.07], FX_, FY_ + 60 + (960 - FY_ - 60) * u)
        sw = clamp01((t - T_DATA) / 0.55)
        if sw < 1:   # light sweep across the studio
            band = np.exp(-((SWEEP_D - (-500 + 2600 * sw)) / 160.0) ** 2)[..., None] * 0.45
            arr = np.clip(arr + band * 255, 0, 255).astype(np.uint8)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        out_k = clamp01((t - T_YOU + 0.13) / 0.13)
        for ht, im, hx, hy, hr in HEADLINES:
            if t >= ht:
                s = 2.2 - 1.2 * ease_out((t - ht) / 0.1)
                paste_center(ov, im, hx, hy, s * (1 - 0.25 * out_k), hr, 1 - out_k)
        fr = with_occlusion(arr, ov, warp(occluder(si), M, cv2.BORDER_CONSTANT))
    elif t < T_MUCH:
        # ---- Digital Zoom locking onto "you" ----
        ts, z = [s for s in DZ_STEPS if t >= s[0]][-1]
        M = affine(z, FX_, FY_ + 40)
        arr = warp(src, M)
        u = t - ts
        if u < 0.16:
            blk = int(34 * (1 - u / 0.16))
            if blk >= 2:
                arr = cv2.resize(cv2.resize(arr, (W // blk, H // blk), interpolation=cv2.INTER_AREA), (W, H), interpolation=cv2.INTER_NEAREST)
        if u < 0.2:
            arr = arr.copy(); arr[..., 0] = np.roll(arr[..., 0], 8, 1); arr[..., 2] = np.roll(arr[..., 2], -8, 1)
        arr = np.clip(arr.astype(np.float32) * np.array([0.95, 1.02, 1.03]), 0, 255).astype(np.uint8)
        fr = Image.fromarray(arr).convert("RGBA")
        hud(fr, M, z, t, ts)
        flash(fr, WHITE, 0.4 * (1 - u / 0.08))
    elif t < T_AFFECT:
        # ---- Growth Curve on a liquid-glass card ----
        sx, sy = shake(t, T_USELESS, 14, 0.25)
        u = (t - T_MUCH) / 0.15
        M = affine(1.15, FX_, 860, sx, sy)
        arr = warp(src, M) if u >= 1 else zoom_blur(src, [1.15 + (2.5 - 1.15) * (1 - ease_out(u)) * f for f in (1, 0.8, 0.6, 0.4)], FX_, 860)
        fr = Image.fromarray(arr).convert("RGBA")
        e = ease_pop((t - T_MUCH - 0.03) * 0.8)
        if e > 0:
            x0, y0, x1, y1 = CARD; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            glass(fr, (cx - (cx - x0) * e, cy - (cy - y0) * e, cx + (x1 - cx) * e, cy + (y1 - cy) * e), r=44, ta=0.55)
            if t > T_MUCH + 0.09: draw_chart(fr, t)
        if t >= T_USELESS + 0.05:
            paste_center(fr, STAMP, W / 2, (CARD[1] + CARD[3]) / 2 - 20, 2.0 - 1.0 * ease_out((t - T_USELESS - 0.05) / 0.1), 8)
        flash(fr, (255, 40, 40), 0.35 * (1 - (t - T_USELESS) / 0.2) if t >= T_USELESS else 0)
    elif t < T_KEEPS:
        # ---- Dolly Zoom: subject locked, background stretches away ----
        u = ease_io((t - T_AFFECT) / (T_KEEPS - T_AFFECT))
        Ms = affine(1.35, FX_, 800)
        zb = 1.35 - 0.35 * u
        bg = np.zeros((H, W, 3), np.float32)
        for j in range(3): bg += warp(PLATE, affine(zb + 0.015 * j * (u > 0.02), FX_, 800))
        bg /= 3
        gray = bg.mean(2, keepdims=True)
        bg = bg * (1 - 0.5 * u) + gray * 0.5 * u
        bg = bg * (1 - 0.22 * u) + np.array([60, 0, 10]) * 0.22 * u
        a = warp(occluder(si, True), Ms, cv2.BORDER_CONSTANT)[..., None]
        subj = warp(src, Ms).astype(np.float32)
        arr = subj * a + bg * (1 - a)
        vig = 1 - 0.45 * u * np.clip(((_xx - 540) / 700.0) ** 2 + ((_yy - 900) / 1100.0) ** 2, 0, 1)[..., None]
        fr = Image.fromarray(np.clip(arr * vig, 0, 255).astype(np.uint8)).convert("RGBA")
    elif t < T_BETTER:
        # ---- Frame Break: he pops out of the photo ----
        fr = Image.fromarray(frame_break(src, person(si), t)).convert("RGBA")
        flash(fr, WHITE, 0.5 * (1 - (t - T_KEEPS) / 0.1))
    elif t < bC:
        # ---- Snap Zoom punch ----
        sx, sy = shake(t, T_BETTER, 26, 0.4)
        z = 2.6 - 0.3 * min(1, (t - T_BETTER) / 0.12) - 0.15 * (t - T_BETTER)
        fr = Image.fromarray(warp(src, affine(z, FX_, FY_ + 70, sx, sy))).convert("RGBA")
        flash(fr, WHITE, 0.6 * (1 - (t - T_BETTER) / 0.15))
    else:
        # ---- Magazine Cover + Checklist Pop + CTA ----
        u = (t - bC) / (DUR - bC)
        M = affine(MAG_Z + 0.05 * u, MAG_CX, MAG_CY)
        arr = warp(src, M)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        mi = ease_out((t - bC - 0.05) / 0.18)
        paste_center(ov, MAST, W / 2, MAST_Y + MAST.height / 2, 1.25 - 0.25 * mi, 0, mi)
        fr = with_occlusion(arr, ov, warp(person(si), M, cv2.BORDER_CONSTANT))
        paste_center(fr, STRAP, W / 2, MAST_Y - 40, 1.0, 0, clamp01((t - bC - 0.2) / 0.2))
        for i, (ct, im) in enumerate(COVER_LINES):
            if t >= ct:
                s = ease_pop(t - ct); cy = 1110 + i * 118
                bw, bh = (im.width + 50) * s, (im.height + 16) * s
                glass(fr, (1030 - bw, cy - bh / 2, 1030, cy + bh / 2), r=int(bh / 2), ta=0.55)
                paste_center(fr, im, 1030 - bw / 2, cy, s)
        if t >= bC + 1.4: paste_center(fr, COVER_HEAD, W / 2, 1500, ease_pop(t - bC - 1.4), -2)
        if t >= bC + 1.9:
            pulse = ease_pop(t - bC - 1.9) * (1 + 0.04 * math.sin((t - bC - 1.9) * 12))
            paste_center(fr, CTA, W / 2, 1715, pulse)
            paste_center(fr, emoji("1f446", 110), W / 2 + 300, 1840 + 14 * math.sin(t * 10), ease_pop(t - bC - 2.05))
        flash(fr, WHITE, 0.9 * (1 - (t - bC) / 0.18))

    draw_caption(fr, t)

    # retention progress bar
    dr = ImageDraw.Draw(fr)
    dr.rectangle((0, 0, W, 12), fill=(0, 0, 0, 110))
    dr.rectangle((0, 0, int(W * (n + 1) / NF), 12), fill=YEL + (255,))

    out = fr.convert("RGB")
    if any(abs(t - p) < 0.5 / FPS for p in PREVIEW): out.save(f"{WORK}/prev_{t:05.2f}.jpg", quality=85)
    enc.stdin.write(out.tobytes())
    if n % 60 == 0: print("frame", n, "/", NF, flush=True)
enc.stdin.close(); enc.wait()

# ---------- audio ----------
# voice: same cuts, 12ms micro-fades at each cut, light cleanup (no gate: it clips word endings)
ats = ";".join(f"[0:a:0]atrim={a/FPS}:{b/FPS},asetpts=PTS-STARTPTS,volume={SEG_GAIN[i]}dB,afade=t=in:d=0.012,afade=t=out:st={(b-a)/FPS-0.015}:d=0.015,atempo={SEG_TEMPO[i]}[a{i}]"
               for i, (a, b) in enumerate(VSEGS))
afc = (f"{ats};{''.join(f'[a{i}]' for i in range(len(VSEGS)))}concat=n={len(VSEGS)}:v=0:a=1,pan=mono|c0=0.5*c0+0.5*c1,"
       "highpass=f=80,afftdn=nr=8:nf=-42,equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1:g=3.5,"
       "highshelf=f=8000:g=2,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=150:makeup=2[o]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", SRC, "-filter_complex", afc, "-map", "[o]", "-ar", str(SR), WORK + "/voice.wav"], check=True)
w = wave.open(WORK + "/voice.wav"); voice = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
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
    out = np.zeros_like(n)
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

def digi(f0=1200):
    t = tt(0.09); s = np.sign(np.sin(2 * np.pi * f0 * t)) * 0.25 + 0.2 * rng.standard_normal(len(t)) * np.exp(-t * 60)
    return (np.round(s * 6) / 6) * np.exp(-t * 18)

def slap():
    t = tt(0.14); n = rng.standard_normal(len(t))
    return (n - lp(n, 0.3)) * np.exp(-t * 45) * 0.6 + np.sin(2 * np.pi * 90 * t) * np.exp(-t * 30) * 0.6

def buzzer(d=0.42):
    t = tt(d); s = np.sign(np.sin(2 * np.pi * 140 * t)) + 0.6 * np.sign(np.sin(2 * np.pi * 147 * t))
    return lp(s.astype(np.float32), 0.25) * np.minimum(1, (d - t) * 25) * 0.28

def riser(d):
    t = tt(d); f = 200 * (2 ** (t / d * 3))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 + 0.25 * rng.standard_normal(len(t)) * (t / d)
    return s * (t / d) ** 2 * 0.6

def vertigo(d):
    t = tt(d); f = 70 - 30 * t / d
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t)) + 0.3 * np.sin(2 * np.pi * np.cumsum(f * 3.01) / SR)
    return s * np.minimum(1, t * 6) * np.minimum(1, (d - t) * 8) * 0.5

def shutter():
    t = tt(0.12); return rng.standard_normal(len(t)) * (np.exp(-t * 80) + 0.6 * np.exp(-np.abs(t - 0.06) * 150)) * 0.35

FX = np.zeros(N, np.float32)
def put(sig, at, g=1.0):
    i = int(at * SR); j = min(N, i + len(sig)); FX[i:j] += sig[:j - i] * g

put(boom(1.2), 0.0, 1.0); put(pop(), 0.05, 0.5)
put(whoosh(0.3, False), bQ - 0.1, 0.5)
for st, _, kind, *_ in caps[1:4]: put(pop(), st, 0.4)
put(whoosh(0.3), bA - 0.3, 0.8); put(boom(1.2), bA, 1.0)
put(whoosh(0.45, False), T_DATA, 0.6)
for ht, *_ in HEADLINES: put(slap(), ht, 0.7)
for ts, _ in DZ_STEPS: put(digi(), ts, 0.8); put(digi(1800), ts + 0.06, 0.5)
put(whoosh(0.2, False), T_MUCH - 0.05, 0.5); put(riser(T_USELESS - T_MUCH - 0.07), T_MUCH + 0.07, 0.6)
put(buzzer(), T_USELESS, 0.8); put(boom(0.6), T_USELESS + 0.05, 0.6)
put(vertigo(T_KEEPS - T_AFFECT), T_AFFECT, 0.9); put(whoosh(T_KEEPS - T_AFFECT - 0.05, False), T_AFFECT + 0.02, 0.35)
put(boom(0.8), T_KEEPS, 0.8); put(whoosh(0.25), T_KEEPS - 0.05, 0.5)
put(boom(1.3), T_BETTER, 1.0); put(whoosh(0.3, False), T_BETTER - 0.04, 0.5)
put(whoosh(0.4), bC - 0.15, 0.6); put(shutter(), bC, 0.9); put(boom(0.6), bC + 0.07, 0.5)
for ct, _ in COVER_LINES: put(pop(), ct, 0.5); put(ding(1568, 0.3), ct + 0.02, 0.35)
put(slap(), bC + 1.4, 0.6)
put(ding(1318.5), bC + 1.9, 0.8); put(ding(1760, 0.8), bC + 2.02, 0.6)

# background beat: 120 bpm, Am-F-C-G bass, kick + offbeat hats + soft pad
bpm = 120; beat = 60 / bpm
MUS = np.zeros(N, np.float32)
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
        if i < N: MUS[i:j] += sig[:j - i] * g
    if not T_AFFECT <= s0 < T_KEEPS:                  # drop the drums under the dolly zoom
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
MUS = MUS * duck * 0.22 * tail_boost
fade = np.minimum(1, (N - np.arange(N)) / (0.5 * SR)); MUS *= fade

mix = V + FX * 0.55 + MUS
mix = mix / max(1.0, np.abs(mix).max() / 0.95)
with wave.open(WORK + "/mix.wav", "wb") as o:
    o.setnchannels(1); o.setsampwidth(2); o.setframerate(SR)
    o.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", WORK + "/video_only.mp4", "-i", WORK + "/mix.wav",
                "-af", "loudnorm=I=-11.6:TP=-1.0:LRA=11,aresample=48000", "-ac", "2",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("done", OUT)
