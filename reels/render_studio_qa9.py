"""Studio Q&A reels, batch IMG_6281-6291 (armchair set): one reel per clip. Each gets a verbal hook (his own line,
lifted as a cold open where the strongest line isn't already first), a topic-matched visual hook in the first
second, 2-4 effects tied to what he says, English captions, cleaned voice under a quiet bed, and an English CTA.

usage: render_studio_qa9.py UPLOAD_DIR OUT_DIR [6281 6282 ...]
All times are source seconds, from the Whisper transcript (Egyptian Arabic) and the speech envelope.
"""
import os, sys, math, glob, subprocess, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/founder-events")
import music

UP, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, SR = 1080, 1920, 30, 48000
WHITE, BLACK, YEL, RED, GREEN = (255, 255, 255), (0, 0, 0), (255, 214, 0), (232, 36, 52), (40, 200, 110)
FD = S + "/founder-events/fonts/"
CX, CY = .5, .30  # zoom centre: upper body; his face sits at ~y .24 in the wide shot


def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        f.set_variation_by_axes([wght])
    return f


MONT = lambda s, w=800: font("Montserrat[wght].ttf", s, w)
ANTON = lambda s: font("Anton-Regular.ttf", s)

# segs: (src start, src end, English caption)   cold: (src start, src end, card text segments)   *x* = highlight
CLIPS = {
    "6281": dict(name="looked amazing online", hook="evr", cold=None, segs=[
        (0.00, 4.21, "Ever been somewhere that looked *AMAZING* online… and got *SHOCKED* when you got there?"),
        (4.21, 8.68, "Oh yeah. *A lot.*"),
        (8.68, 10.69, "Unfortunately — a lot in *Egypt*"),
        (10.69, 14.49, "And honestly… *why* do they even do that?")],
        cta=("Name a place that did this to you", "Drop it in the comments ↓", "Follow for honest restaurant talk")),
    "6282": dict(name="5PM vs 8PM", hook="vs", cold=(9.14, 14.76, [("“The ", WHITE), ("5PM", YEL), (" customer is NOT the ", WHITE), ("8PM", YEL), (" one”", WHITE)]), segs=[
        (6.08, 9.14, "Every time slot needs its *own kind of service*"),
        (9.14, 11.83, "The customer who comes at *5PM*…"),
        (11.83, 14.76, "is *not* the one who comes at *8PM*"),
        (14.76, 17.46, "Everyone wants something *different*")],
        cta=("Do you serve 5PM like 8PM?", "Tell me in the comments ↓", "Follow for restaurant growth tips")),
    "6283": dict(name="every reservation a no-show", hook="noshow", cold=None, segs=[
        (0.00, 2.24, "Is every reservation a potential *NO-SHOW*?"),
        (2.24, 7.76, "No — *data* can help you analyze that"),
        (7.76, 11.38, "But you also have another *option*"),
        (11.38, 13.39, "to *kill* no-shows completely"),
        (13.39, 16.78, "so why take that *risk*?")],
        cta=("How many no-shows this week?", "Be honest ↓", "Follow for restaurant growth tips")),
    "6284": dict(name="your data knows", hook="curve", cold=(9.24, 12.38, [("“New ", WHITE), ("chef", YEL), ("? New ", WHITE), ("dish", YEL), ("?”", WHITE)]), segs=[
        (4.14, 9.24, "so you know exactly what *problems* you have"),
        (9.24, 12.38, "like a *new chef*, or a *new dish*"),
        (12.38, 16.63, "something went wrong — operations *dropped* that day"),
        (16.63, 20.62, "all of it helps you improve the *offer* and the *experience*")],
        cta=("Do you track your restaurant's data?", "Yes or no ↓", "Follow for restaurant growth tips")),
    "6285": dict(name="overbooking system", hook="xover", cold=(7.67, 12.38, [("“It's ", WHITE), ("WRONG", RED), (" if you already use a ", WHITE), ("system", YEL), ("”", WHITE)]), segs=[
        (2.32, 7.67, "Overbooking? Some people think it's *right* — to cover no-shows"),
        (7.67, 12.38, "but in my opinion it's *wrong* if you already use a *system*"),
        (12.38, 16.70, "that cuts *no-shows* a lot and manages"),
        (16.70, 18.84, "no-shows, *dine-in*"),
        (18.84, 24.78, "*walk-ins* and the *waiting list* — then you don't need overbooking *at all*")],
        cta=("Do you overbook?", "Be honest in the comments ↓", "Follow for restaurant growth tips")),
    "6286": dict(name="overbooking hot take", hook="hot", cold=(13.31, 17.33, [("“You'd lose those customers… ", WHITE), ("FOREVER", RED), ("”", WHITE)]), segs=[
        (0.00, 2.74, "Is overbooking *ALWAYS* wrong?"),
        (2.74, 6.56, "For me? *Completely* wrong."),
        (6.56, 8.77, "Imagine I've got a booking…"),
        (8.77, 10.78, "and *everyone* who booked *shows up*"),
        (10.78, 13.31, "It rarely happens — but say it *does*"),
        (13.31, 17.33, "you'd lose *how many customers* — forever?"),
        (17.33, 20.58, "If you use the *right system* from day one"),
        (20.58, 25.58, "*deposits* + *online confirmation* based on your availability"),
        (25.58, 28.85, "it can *never* happen — and you *win*")],
        cta=("Agree or disagree?", "Overbooking: yes or no ↓", "Follow for restaurant growth tips")),
    "6289": dict(name="busy is not productive", hook="meetings", cold=(14.17, 18.97, [("“No sales. ", WHITE), ("Zero", RED), (" progress. It's all ", WHITE), ("talk", YEL), (".”", WHITE)]), segs=[
        (0.00, 4.02, "What makes you *FEEL* productive… when you're *not*?"),
        (4.02, 10.49, "Tons of *meetings* — your day feels *full*, like you really worked"),
        (10.49, 14.17, "but when you look at it *on paper*…"),
        (14.17, 16.96, "no sales. *ZERO* progress."),
        (16.96, 18.97, "It's all *talk*.")],
        cta=("How many meetings this week?", "And how many sales? ↓", "Follow for founder truths")),
    "6290": dict(name="how many NOs", hook="nos", cold=None, segs=[
        (0.00, 2.01, "How many *NOs* before you *STOP*?"),
        (2.01, 8.78, "Not every no means the same — “*it doesn't fit me*”"),
        (8.78, 11.53, "“*Too expensive*” — no this, no that"),
        (11.53, 15.62, "The right move: *analyze* everything they say"),
        (15.62, 18.31, "see what you can *change* and build on"),
        (18.31, 22.52, "and who just doesn't want to *change* or make the *effort*"),
        (22.52, 27.03, "Analyze it: is this NO *right* or *wrong*?")],
        cta=("What's the worst NO you've heard?", "Drop it below ↓", "Follow for founder truths")),
    "6291": dict(name="founders dont sleep", hook="clock", cold=(2.62, 8.85, [("“Who told you founders even ", WHITE), ("SLEEP", YEL), ("?”", WHITE)]), segs=[
        (0.00, 2.62, "Does *16 hours* a day make you a great founder?"),
        (2.62, 8.85, "Who told you founders even *SLEEP*?"),
        (8.85, 15.48, "Sometimes I close my eyes… but my *brain* keeps working"),
        (15.48, 18.75, "A lot of nights I *can't sleep*"),
        (18.75, 23.56, "Unfortunately — as a founder, especially with a *startup*"),
        (23.56, 28.21, "you work *24 hours* out of 24")],
        cta=("Founders: how many hours", "did you sleep last night? ↓", "Follow for founder truths")),
}
ONLY = sys.argv[3:] or list(CLIPS)


def src_path(n):
    return glob.glob(f"{UP}/*IMG_{n}.mov")[0]


# ---------------------------------------------------------------- media
def frames(src, a, b):
    n = int(round((b - a) * FPS))
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a + .1}", "-i", src, "-an", "-vf", vf,
                        "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n:
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr[:n]


def voice(src, a, b):
    af = "highpass=f=90,afftdn=nf=-25,equalizer=f=3000:t=q:w=1.2:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=80"
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a}", "-i", src, "-vn", "-af", af,
                        "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, np.float32).copy()
    n = int(round((b - a) * FPS)) * SR // FPS
    x = np.pad(x, (0, max(0, n - len(x))))[:n]
    f = int(.012 * SR)
    x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    return x


# ---------------------------------------------------------------- graphics helpers
def text_img(segs, f, stroke=0, pad=10):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    bbs = [d.textbbox((0, 0), s, font=f, stroke_width=stroke) for s, _ in segs]
    asc, desc = f.getmetrics()
    w = sum(b[2] - b[0] for b in bbs) + 2 * pad
    im = Image.new("RGBA", (w, asc + desc + 2 * pad + 2 * stroke), (0, 0, 0, 0))
    x = pad
    for (s, col), bb in zip(segs, bbs):
        ImageDraw.Draw(im).text((x - bb[0], pad + stroke), s, font=f, fill=col, stroke_width=stroke, stroke_fill=BLACK)
        x += bb[2] - bb[0]
    return im


def lines_img(lines, f, stroke=0, gap=6, maxw=980):
    ims = [text_img(l if isinstance(l, list) else [(l, WHITE)], f, stroke) for l in lines]
    w = max(i.width for i in ims)
    h = sum(i.height for i in ims) + gap * (len(ims) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in ims:
        out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + gap
    if out.width > maxw:
        out = out.resize((maxw, int(out.height * maxw / out.width)), Image.LANCZOS)
    return out


def pill(txt, f, fg=BLACK, bg=YEL, pad=(30, 14), r=None):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, rr, b = d.textbbox((0, 0), txt, font=f)
    w, h = rr - l + 2 * pad[0], b - t + 2 * pad[1]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), h // 2 if r is None else r, fill=bg)
    ImageDraw.Draw(im).text((pad[0] - l, pad[1] - t), txt, font=f, fill=fg)
    return im


def paste(fr, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= .01 or scale <= .01:
        return
    if scale != 1 or rot:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
        if rot:
            im = im.rotate(rot, Image.BICUBIC, expand=True)
    a = np.asarray(im).astype(np.float32) / 255
    x0, y0 = int(cx - im.width / 2), int(cy - im.height / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + im.width), min(H, y0 + im.height)
    if xb <= xa or yb <= ya:
        return
    s = a[ya - y0:yb - y0, xa - x0:xb - x0]
    al = s[..., 3:] * alpha
    fr[ya:yb, xa:xb] = fr[ya:yb, xa:xb] * (1 - al) + s[..., :3] * 255 * al


def pop(u):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 1 + 1.7 * (u - 1) ** 3 + .25 * math.sin(u * math.pi) * (1 - u)


def ease(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)


def zoom(img, z, dx=0, dy=0, rot=0.0):
    M = cv2.getRotationMatrix2D((CX * W, CY * H), rot, z)
    M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def caption_pages(text):
    words, hl = [], False
    for wd in text.split():
        st = wd.startswith("*") or wd.startswith("“*")
        clean = wd.replace("*", "")
        en = wd.rstrip(".,?!…”—").endswith("*")
        words.append((clean, hl or st))
        hl = (hl or st) and not en
    pages, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= 3 and (len(cur) == 4 or w_[0][-1] in ",.?—…”"):
            pages.append(cur); cur = []
    if cur:
        if len(cur) == 1 and pages:
            pages[-1] += cur
        else:
            pages.append(cur)
    return pages


def caption_img(page):
    segs = [(w_.upper() + (" " if i < len(page) - 1 else ""), YEL if hl else WHITE) for i, (w_, hl) in enumerate(page)]
    return lines_img([segs], MONT(70, 900), stroke=7)


def stamp(word, col=RED, size=120):
    f = ANTON(size)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), word, font=f)
    w, h = r - l + 70, b - t + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((5, 5, w - 6, h - 6), 18, outline=col + (240,), width=11)
    dd.text((35 - l, 25 - t), word, font=f, fill=col + (240,))
    return im


def slam(fr, im, cx, cy, t, t0, rot=-8):
    if t < t0:
        return
    u = min(1, (t - t0) / .16)
    paste(fr, im, cx, cy, 2.0 - 1.0 * ease(u), min(1, u * 2), rot=rot)


def card(w, h, fill=(255, 255, 255, 245), r=30):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill)
    return im


def stars(n_on, size=46, col=(255, 190, 0)):
    im = Image.new("RGBA", (size * 5 + 40, size + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k in range(5):
        cx, cy, R = k * (size + 10) + size / 2, size / 2 + 2, size / 2
        pts = [(cx + (R if j % 2 == 0 else R * .45) * math.sin(j * math.pi / 5), cy - (R if j % 2 == 0 else R * .45) * math.cos(j * math.pi / 5)) for j in range(10)]
        d.polygon(pts, fill=col if k < n_on else (210, 210, 210))
    return im


# ---------------------------------------------------------------- hooks (t = output time; they run over the opening seconds)
def hook_evr(fr, t, ctx):
    for i, (lab, n_on, col) in enumerate((("ONLINE", 5, GREEN), ("REALITY", 1, RED))):
        c = card(440, 270)
        d = ImageDraw.Draw(c)
        d.rounded_rectangle((0, 0, 439, 70), 30, fill=col + (255,)); d.rectangle((0, 40, 439, 70), fill=col + (255,))
        d.text((220, 36), lab, font=ANTON(52), fill=WHITE, anchor="mm")
        c.alpha_composite(stars(n_on), (220 - 145, 110))
        d.text((220, 205), "looks amazing" if i == 0 else "…not even close", font=MONT(34, 800), fill=(40, 40, 40), anchor="mm")
        paste(fr, c, 290 + i * 500, 1000, pop(min(1, (t - .1 - i * .45) / .25)), rot=4 if i == 0 else -4)
    if t > .4:
        paste(fr, lines_img([[("VS", YEL)]], ANTON(110), stroke=7), W / 2, 1000, pop(min(1, (t - .4) / .2)))


def hook_vs(fr, t, ctx):
    for i, (lab, sub) in enumerate((("5:00 PM", "quick & casual?"), ("8:00 PM", "the full night out?"))):
        im = lines_img([[(lab, YEL)], sub], ANTON(110), stroke=7) if False else None
        c = card(440, 230, (20, 20, 28, 235))
        d = ImageDraw.Draw(c)
        d.text((220, 95), lab, font=ANTON(108), fill=YEL, anchor="mm")
        d.text((220, 185), "customer", font=MONT(38, 800), fill=WHITE, anchor="mm")
        x0 = -300 if i == 0 else W + 300
        k = ease((t - .05) / .3)
        paste(fr, c, x0 + (290 + i * 500 - x0) * k, 1000)
    if t > .35:
        paste(fr, lines_img([[("≠", RED)]], ANTON(170), stroke=8), W / 2, 1000, pop(min(1, (t - .35) / .2)))


def hook_noshow(fr, t, ctx):
    c = card(620, 300)
    d = ImageDraw.Draw(c)
    d.text((310, 70), "RESERVED", font=ANTON(96), fill=(25, 25, 25), anchor="mm")
    d.line((60, 135, 560, 135), fill=(200, 200, 200), width=3)
    d.text((310, 190), "Table for 4 · 8:30 PM", font=MONT(42, 800), fill=(60, 60, 60), anchor="mm")
    d.text((310, 250), "Status: confirmed ✓".replace(" ✓", ""), font=MONT(32, 600), fill=(30, 160, 80), anchor="mm")
    paste(fr, c, W / 2, 1000, pop(min(1, t / .3)))
    slam(fr, stamp("NO-SHOW"), W / 2 + 60, 1040, t, .9)


def hook_curve(fr, t, ctx):
    c = card(860, 470, (18, 20, 28, 238))
    d = ImageDraw.Draw(c)
    d.text((40, 36), "COVERS · THIS WEEK", font=MONT(36, 800), fill=(200, 200, 210))
    days = ["SAT", "SUN", "MON", "TUE", "WED", "THU", "FRI"]
    vals = [.62, .68, .7, .3, .55, .72, .86]
    x0, x1, y0, y1 = 60, 800, 380, 110
    pts = [(x0 + (x1 - x0) * i / 6, y0 - (y0 - y1) * v) for i, v in enumerate(vals)]
    for i, dname in enumerate(days):
        d.text((pts[i][0], 420), dname, font=MONT(26, 700), fill=(150, 150, 165), anchor="mm")
    u = min(1, max(0, (t - .2) / 1.6))
    nseg = u * 6
    for i in range(6):
        if nseg <= i: break
        a, b = pts[i], pts[i + 1]
        f = min(1, nseg - i)
        e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
        d.line([a, e], fill=(255, 214, 0) if i not in (2, 3) else (232, 36, 52), width=9)
    if nseg > 3:
        p = pts[3]
        d.ellipse((p[0] - 14, p[1] - 14, p[0] + 14, p[1] + 14), fill=(232, 36, 52))
        d.text((p[0], p[1] + 50), "new chef day", font=MONT(30, 800), fill=(255, 120, 120), anchor="mm")
    paste(fr, c, W / 2, 1010, pop(min(1, t / .3)))


def hook_xover(fr, t, ctx):
    im = lines_img([[("OVERBOOKING", WHITE)]], ANTON(150), stroke=8)
    paste(fr, im, W / 2, 1000, pop(min(1, t / .25)))
    if t > .55:
        u = min(1, (t - .55) / .25)
        x = Image.new("RGBA", (im.width, im.height), (0, 0, 0, 0))
        ImageDraw.Draw(x).line((10, im.height * .55, 10 + (im.width - 20) * u, im.height * .45), fill=RED + (255,), width=22)
        paste(fr, x, W / 2, 1000)


def hook_hot(fr, t, ctx):
    bar = pill("🔥 HOT TAKE".replace("🔥 ", ""), ANTON(80), fg=WHITE, bg=(230, 60, 20), pad=(46, 16))
    paste(fr, bar, W / 2, 900, pop(min(1, t / .25)), rot=-3)
    for k in range(4):
        t0 = .35 + k * .28
        if t < t0: break
        c = card(760, 110, (255, 255, 255, 240), 26)
        d = ImageDraw.Draw(c)
        d.ellipse((24, 25, 84, 85), fill=GREEN)
        d.text((104, 22), "New booking", font=MONT(28, 700), fill=(110, 110, 110))
        d.text((104, 56), f"Table for {[4, 2, 6, 3][k]} · 8:30 PM", font=MONT(36, 800), fill=(25, 25, 25))
        paste(fr, c, W / 2, 1030 + k * 125, pop(min(1, (t - t0) / .2)))
    slam(fr, stamp("FULL", size=140), W / 2 + 40, 1180, t, 1.6, rot=8)


def hook_meetings(fr, t, ctx):
    times = ["9:00", "10:30", "12:00", "1:30", "3:00", "4:30"]
    for k, tm in enumerate(times):
        t0 = .1 + k * .2
        if t < t0: break
        c = card(420, 92, (66, 133, 244, 235), 18)
        d = ImageDraw.Draw(c)
        d.text((24, 46), f"{tm}  Meeting", font=MONT(40, 800), fill=WHITE, anchor="lm")
        paste(fr, c, 290 + (k % 2) * 500, 860 + (k // 2) * 115, pop(min(1, (t - t0) / .2)))
    slam(fr, stamp("SALES: 0", size=120), W / 2, 980, t, 1.5)


def hook_nos(fr, t, ctx):
    items = [("NO", 300, 900, -12, 120), ("too expensive", 760, 830, 8, 70), ("NO", 780, 1110, 10, 120),
             ("not for us", 320, 1160, -6, 70), ("NOT NOW", 540, 1010, -3, 90)]
    for k, (w_, x, y, r, s) in enumerate(items):
        slam(fr, stamp(w_.upper(), size=s), x, y, t, .1 + k * .22, rot=r)


def hook_clock(fr, t, ctx):
    u = ease(min(1, max(0, (t - .2) / 1.4)))
    h = int(round(16 + 8 * u))
    big = lines_img([[(f"{h}H", YEL if h < 24 else RED)]], ANTON(260), stroke=10)
    paste(fr, big, W / 2, 950, pop(min(1, t / .25)))
    lab = lines_img(["WORK / DAY"], MONT(48, 900), stroke=6)
    paste(fr, lab, W / 2, 1110, 1, ease(t / .3))
    if t > 1.7:
        slam(fr, stamp("SLEEP: 0", size=100), W / 2 + 160, 1230, t, 1.7, rot=6)


HOOKS = dict(evr=hook_evr, vs=hook_vs, noshow=hook_noshow, curve=hook_curve, xover=hook_xover, hot=hook_hot,
             meetings=hook_meetings, nos=hook_nos, clock=hook_clock)


# mid-reel effects tied to what he says (src times)
def fx_checklist(fr, T_, ctx):
    items = [(12.38, "No-shows ↓"), (16.70, "Dine-in"), (18.84, "Walk-ins"), (20.5, "Waiting list")]
    y = 820
    for src_t, txt in items:
        t0 = ctx["out"](src_t)
        if t0 is None or T_ < t0: break
        c = card(560, 96, (40, 190, 105, 238), 22)
        d = ImageDraw.Draw(c)
        d.ellipse((22, 20, 78, 76), fill=WHITE)
        d.line([(34, 50), (46, 62), (68, 36)], fill=(40, 190, 105), width=7)
        d.text((100, 48), txt.replace(" ↓", " cut"), font=MONT(44, 800), fill=WHITE, anchor="lm")
        paste(fr, c, W / 2, y, pop(min(1, (T_ - t0) / .25)))
        y += 110


def fx_stamp_at(src_t, word, rot=-8):
    def f(fr, T_, ctx):
        t0 = ctx["out"](src_t)
        if t0 is not None and t0 <= T_ < t0 + 2.2:
            slam(fr, stamp(word, size=120), W / 2, 1000, T_, t0, rot)
    return f


FX = {"6285": [fx_checklist], "6289": [fx_stamp_at(14.17, "SALES: 0")], "6283": [fx_stamp_at(11.38, "NO-SHOW = 0", 6)],
      "6286": [fx_stamp_at(25.58, "YOU WIN", 6)], "6291": [fx_stamp_at(23.56, "24/24", -6)],
      "6290": [fx_stamp_at(22.52, "RIGHT OR WRONG?", 4)]}


def cta(fr, t, lines):
    a = lines_img([lines[0]], MONT(76, 900), stroke=8)
    paste(fr, a, W / 2, 900, pop(min(1, t / .3)))
    b = pill(lines[1], MONT(56, 800), fg=BLACK, bg=YEL)
    paste(fr, b, W / 2, 900 + a.height / 2 + 70, pop(min(1, (t - .25) / .3)))
    c = pill(lines[2] + "  →", MONT(48, 800), fg=WHITE, bg=(220, 30, 40))
    paste(fr, c, W / 2, 1460, pop(min(1, (t - .7) / .3)))


def quote_card(fr, t, segs):
    im = lines_img([segs], MONT(62, 900), stroke=6, maxw=940)
    c = Image.new("RGBA", (im.width + 60, im.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, c.width - 1, c.height - 1), 28, fill=(0, 0, 0, 150))
    c.alpha_composite(im, (30, 20))
    paste(fr, c, W / 2, 1460, pop(min(1, t / .25)))


# ---------------------------------------------------------------- sound
def sfx_whoosh(d=.35):
    n = int(d * SR); t = np.arange(n) / SR
    return music.bp(np.random.default_rng(1).standard_normal(n), 600, 6000) * np.sin(np.pi * t / d) ** 2 * .5


def sfx_pop():
    n = int(.08 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 60) * .6


def sfx_stamp():
    return music.kick(.4, 120, 40, 1.2, 1.0) * .9


def bed(seconds, seed):
    bpm = [96, 100, 104][seed % 3]
    T = music.Track(seconds + 1, bpm)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for b in range(int(seconds / T.b) + 1):
        beat, ch = b % 4, b // 4 % 4
        if beat in (0, 2): T.put("drums", music.kick(.35, 110, 45, .3), b, .6); T.kicks.append(b)
        if beat in (1, 3): T.put("drums", music.snap(), b, .35)
        T.put("drums", music.hat(.03), b + .5, .1)
        if beat == 0:
            T.put("music", music.pad(prog[ch], 4 * T.b, 900), b, .35)
            T.put("bass", music.bass(prog[ch][0] - 24, 3.5 * T.b, 300), b, .5)
    return T.mix(.3)[:, 0]


SFX_HOOK = {"evr": [(.1, "pop"), (.55, "pop"), (.4, "stamp")], "vs": [(.05, "whoosh"), (.35, "stamp")], "noshow": [(.9, "stamp")],
            "curve": [(.2, "whoosh")], "xover": [(.55, "whoosh")], "hot": [(.35, "pop"), (.63, "pop"), (.91, "pop"), (1.19, "pop"), (1.6, "stamp")],
            "meetings": [(.1 + k * .2, "pop") for k in range(6)] + [(1.5, "stamp")],
            "nos": [(.1 + k * .22, "stamp") for k in range(5)], "clock": [(.2, "whoosh"), (1.7, "stamp")]}


# ---------------------------------------------------------------- render
def render(n):
    cfg = CLIPS[n]
    src = src_path(n)
    parts = []
    if cfg["cold"]:
        parts.append((cfg["cold"][0], cfg["cold"][1], "cold"))
    parts += [(a, b, i) for i, (a, b, _) in enumerate(cfg["segs"])]
    tl, t = [], 0.0
    for a, b, k in parts:
        tl.append((t, a, b, k)); t += round((b - a) * FPS) / FPS
    body_end = t
    T = body_end + 2.6
    nfr = int(round(T * FPS))
    cold_end = tl[1][0] if cfg["cold"] else 0.0
    hook_len = max(cold_end, 2.4)

    def out_t(s):  # first body occurrence of source time s on the output timeline
        for t0, a, b, k in tl:
            if k != "cold" and a <= s < b:
                return t0 + s - a
        return None
    ctx = dict(out=out_t)
    # audio
    vo = np.zeros(int(T * SR) + SR)
    for t0, a, b, k in tl:
        x = voice(src, a, b); i = int(t0 * SR); vo[i:i + len(x)] += x
    vo = vo / (np.abs(vo).max() + 1e-9) * .9
    mus = bed(T + 1, int(n))[:len(vo)]
    mus = np.pad(mus, (0, len(vo) - len(mus)))
    env = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same")
    duck = 1 - .75 * np.clip(env / (np.percentile(env, 80) + 1e-9), 0, 1)
    fx = np.zeros_like(vo)

    def put(sig, at, g=1.0):
        i = int(at * SR); k = min(len(sig), len(fx) - i)
        if k > 0 and i >= 0: fx[i:i + k] += g * sig[:k]
    snd = dict(pop=sfx_pop(), stamp=sfx_stamp(), whoosh=sfx_whoosh())
    for at, kind in SFX_HOOK[cfg["hook"]]:
        put(snd[kind], at, .6)
    if cfg["cold"]:
        put(snd["whoosh"], cold_end - .12, .5)
    for f_ in FX.get(n, []):
        pass
    for s_, word in {"6289": [(14.17, "")], "6283": [(11.38, "")], "6286": [(25.58, "")], "6291": [(23.56, "")], "6290": [(22.52, "")]}.get(n, []):
        o = out_t(s_)
        if o is not None: put(snd["stamp"], o, .6)
    if n == "6285":
        for s_ in (12.38, 16.70, 18.84, 20.5):
            o = out_t(s_)
            if o is not None: put(snd["pop"], o, .6)
    put(sfx_whoosh(.5), body_end - .1, .6)
    mix = np.clip(vo + .16 * mus / (np.abs(mus).max() + 1e-9) * duck + fx * .5, -1, 1)
    os.makedirs(OUT, exist_ok=True)
    wav = f"{OUT}/.{n}.wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix[:int(T * SR)] * 32767).astype(np.int16).tobytes())
    out = f"{OUT}/IMG_{n} - {cfg['name']} reel v1.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-14:TP=-1", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    # captions (body only; the cold open shows its English card instead)
    caps = []
    for t0, a, b, k in tl:
        if k == "cold":
            continue
        txt = cfg["segs"][k][2]
        pages = caption_pages(txt)
        nw = sum(len(p) for p in pages)
        acc = 0
        for p in pages:
            ps = t0 + (b - a) * acc / nw; acc += len(p)
            caps.append((ps, t0 + (b - a) * acc / nw, caption_img(p)))
    seg_i, srcf, last = 0, None, None
    zooms = [1.0, 1.35, 1.6]
    for fi in range(nfr):
        T_ = fi / FPS
        if T_ < body_end:
            while seg_i + 1 < len(tl) and T_ >= tl[seg_i + 1][0]:
                seg_i += 1; srcf = None
            t0, a, b, k = tl[seg_i]
            if srcf is None:
                srcf = frames(src, a, b)
            base = srcf[min(int(round((T_ - t0) * FPS)), len(srcf) - 1)]; last = base
            lt = T_ - t0
            # jump zooms: each segment gets its own framing; the hook runs wide->medium push; snap on every cut
            if T_ < hook_len and (k == "cold" or seg_i == 0):
                z = 1.0 + .25 * ease(T_ / hook_len)
            else:
                z = zooms[(seg_i + 1) % 3]
            if lt < .18 and seg_i > 0:
                z *= 1 + .08 * (1 - lt / .18) ** 2
        else:
            base, lt = last, T_ - body_end
            z = 1.1 + .03 * lt
        fr = zoom(base, z).astype(np.float32)
        g = fr.mean(2, keepdims=True); fr = np.clip(g + (fr - g) * 1.12, 0, 255)
        if T_ >= body_end:
            fr *= .55
            cta(fr, lt, cfg["cta"])
        else:
            if T_ < hook_len:
                HOOKS[cfg["hook"]](fr, T_, ctx)
            if cfg["cold"] and T_ < cold_end:
                quote_card(fr, T_, cfg["cold"][2])
            else:
                for cs, ce, im in caps:
                    if cs <= T_ < ce:
                        paste(fr, im, W / 2, 1460, pop(min(1, (T_ - cs) / .12)))
            if T_ >= hook_len:
                for f_ in FX.get(n, []):
                    f_(fr, T_, ctx)
        g2 = min(1, T_ / .12, (T - T_) / .3)
        if g2 < 1: fr *= max(g2, 0)
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print(out, f"{T:.1f}s", flush=True)


if __name__ == "__main__":
    for n in ONLY:
        render(n)
