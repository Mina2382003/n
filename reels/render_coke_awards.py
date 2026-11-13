"""F&B Awards road-trip vlog (480x360 landscape): three competing reels in a framed 9:16 layout (sharpened video in
the middle over a blurred copy, hooks in the top band, captions over his lap so his face stays clear).
Each reel: cold open on his own line with an English card, a topic visual hook, matched effects, English CTA.

usage: render_coke_awards.py SRC OUT_DIR [r1 r2 r3]
All times are source seconds, from the Whisper transcript (Egyptian Arabic) and the speech envelope.
"""
import os, sys, math, subprocess, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/founder-events")
import music

SRC, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:] or ["r1", "r2", "r3"]
W, H, FPS, SR = 1080, 1920, 30, 48000
WHITE, BLACK, YEL, RED, GREEN, GOLD = (255, 255, 255), (0, 0, 0), (255, 214, 0), (232, 36, 52), (40, 200, 110), (212, 168, 70)
FD = S + "/founder-events/fonts/"
VY0, VH = 520, 1240           # video panel: y 520..1760
FACE_X = .62                  # his face, as a fraction of source width


def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        f.set_variation_by_axes([wght])
    return f


MONT = lambda s, w=800: font("Montserrat[wght].ttf", s, w)
ANTON = lambda s: font("Anton-Regular.ttf", s)

CAP = {
    "going":   (0.00, 4.94, "Guys, I'm heading to the *F&B Awards* today in *Cairo*"),
    "late":    (4.94, 8.68, "and I'm *late* for the event"),
    "alex":    (8.68, 13.47, "I was in *Alexandria*… needed something to *wake me up*"),
    "found":   (13.47, 18.67, "the only Coke they had was *this one* — so I got it"),
    "read":    (25.32, 31.32, "Then I read it… *ZERO CAFFEINE*. It won't even *wake me up*!"),
    "highl":   (38.27, 43.20, "Zero caffeine — they literally *highlighted* it"),
    "notice":  (43.20, 45.75, "and I *didn't even notice*"),
    "taste":   (45.75, 51.66, "Tastes like *normal Coke* though — no difference"),
    "good":    (51.66, 53.67, "but it's *good*"),
    "match1":  (107.75, 111.02, "This Coke was *matching* me… so I bought it"),
    "match2":  (113.35, 118.36, "Guys, we're *matching* — me and it"),
    "why":     (118.36, 120.37, "that's literally *why* I bought it"),
    "today":   (92.29, 96.27, "Today we're heading to the *F&B Awards*"),
    "route":   (120.37, 123.52, "driving from *Alexandria* to *Cairo*"),
    "night":   (126.44, 130.81, "at night — just for the *F&B Awards*"),
    "see":     (102.55, 107.75, "Let's see who *wins*"),
    "vote":    (136.90, 140.04, "You guys were supposed to *vote* recently"),
    "brands":  (142.05, 145.67, "So which *brands* will win this year?"),
    "orgs":    (73.04, 78.80, "Hoping for a great event — and great *organizers*"),
}

REELS = {
    "r1": dict(name="zero caffeine", cold="read", body=["going", "late", "alex", "found", "highl", "notice", "taste", "good"],
               card=[("“", WHITE), ("ZERO", RED), (" caffeine… it won't even ", WHITE), ("WAKE ME UP", YEL), ("!”", WHITE)],
               cta=("Do you read the can first?", "Be honest ↓", "Follow for my F&B Awards vlog")),
    "r2": dict(name="we're matching", cold="match2", body=["going", "found", "match1", "why"],
               card=[("“We're ", WHITE), ("MATCHING", YEL), (" — me and it”", WHITE)],
               cta=("Rate the fit /10", "Me or the can? ↓", "Follow for my F&B Awards vlog")),
    "r3": dict(name="who wins the F&B Awards", cold="brands", body=["today", "route", "night", "see", "orgs", "vote", "brands"],
               card=[("“Which ", WHITE), ("brands", YEL), (" will win this year?”", WHITE)],
               cta=("Who wins the F&B Awards?", "Drop your pick ↓", "Follow for the awards night")),
}


# ---------------------------------------------------------------- media
def frames(a, b):
    """source frames a..b as (panel, background) pairs"""
    n = int(round((b - a) * FPS))
    ph = VH
    pw = int(480 * ph / 360 + .5)  # 1653
    x0 = int(min(max(FACE_X * pw - W / 2, 0), pw - W))
    vf = (f"fps={FPS},scale={pw}:{ph}:flags=lanczos,unsharp=5:5:1.1:5:5:0.0,"
          f"eq=contrast=1.06:saturation=1.12,crop={W}:{ph}:{x0}:0")
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a + .1}", "-i", SRC, "-an", "-vf", vf,
                        "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, ph, W, 3)
    if len(fr) < n:
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr[:n]


def background(panel):
    small = cv2.resize(panel, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 6)
    return cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * .45


def voice(a, b):
    af = "highpass=f=110,afftdn=nf=-25,equalizer=f=3000:t=q:w=1.2:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=80"
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a}", "-i", SRC, "-vn", "-af", af,
                        "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True)
    x = np.frombuffer(p.stdout, np.float32).copy()
    n = int(round((b - a) * FPS)) * SR // FPS
    x = np.pad(x, (0, max(0, n - len(x))))[:n]
    f = int(.012 * SR)
    x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
    return x


# ---------------------------------------------------------------- graphics
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


def stamp(word, col=RED, size=120):
    f = ANTON(size)
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = d.textbbox((0, 0), word, font=f)
    w, h = r - l + 70, b - t + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((5, 5, w - 6, h - 6), 18, outline=col + (245,), width=11)
    dd.text((35 - l, 25 - t), word, font=f, fill=col + (245,))
    return im


def slam(fr, im, cx, cy, t, t0, rot=-8):
    if t < t0:
        return
    u = min(1, (t - t0) / .16)
    paste(fr, im, cx, cy, 2.0 - ease(u), min(1, u * 2), rot=rot)


def caption_pages(text):
    words, hl = [], False
    for wd in text.split():
        st = wd.startswith("*")
        en = wd.rstrip(".,?!…—").endswith("*")
        words.append((wd.replace("*", ""), hl or st))
        hl = (hl or st) and not en
    pages, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= 3 and (len(cur) == 4 or w_[0][-1] in ",.?!—…"):
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


# ---------------------------------------------------------------- hooks (top band, y < VY0)
def hook_r1(fr, t):
    a = lines_img([[("I NEEDED ", WHITE), ("CAFFEINE", YEL), ("…", WHITE)]], ANTON(110), stroke=7)
    paste(fr, a, W / 2, 170, pop(min(1, t / .25)))
    # energy bar drains to zero
    u = ease((t - .35) / 1.1)
    bar = Image.new("RGBA", (760, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(bar)
    d.rounded_rectangle((0, 0, 759, 89), 24, fill=(255, 255, 255, 235))
    fill = int(740 * (1 - u))
    if fill > 20:
        d.rounded_rectangle((10, 10, 10 + fill, 79), 18, fill=(GREEN if u < .5 else (240, 160, 0) if u < .8 else RED) + (255,))
    d.text((380, 45), f"ENERGY {int(round(100 * (1 - u)))}%", font=ANTON(52), fill=(20, 20, 20), anchor="mm")
    paste(fr, bar, W / 2, 315, pop(min(1, (t - .2) / .25)))
    slam(fr, stamp("0 CAFFEINE", size=90), W / 2 + 140, 455, t, 1.5, rot=-6)


def hook_r2(fr, t):
    a = pill("FIT CHECK", ANTON(96), fg=BLACK, bg=YEL, pad=(44, 12))
    paste(fr, a, W / 2, 140, pop(min(1, t / .25)), rot=-3)
    for i, (lab, cols) in enumerate((("ME", [(25, 22, 22), (120, 90, 60)]), ("THE CAN", [(20, 20, 20), GOLD]))):
        c = Image.new("RGBA", (380, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        d.rounded_rectangle((0, 0, 379, 149), 26, fill=(255, 255, 255, 240))
        for k, col in enumerate(cols):
            d.ellipse((24 + k * 70, 30, 24 + k * 70 + 90, 120), fill=col + (255,), outline=(255, 255, 255, 255), width=4)
        d.text((260, 75), lab, font=ANTON(54), fill=(20, 20, 20), anchor="mm")
        paste(fr, c, 280 + i * 520, 320, pop(min(1, (t - .25 - i * .25) / .25)))
    u = ease((t - .8) / .9)
    pct = lines_img([[(f"{int(round(100 * u))}% ", YEL), ("MATCH", WHITE)]], ANTON(84), stroke=6)
    if t > .8:
        paste(fr, pct, W / 2, 460, pop(min(1, (t - .8) / .2)))


def hook_r3(fr, t):
    tk = pill("F&B AWARDS · TONIGHT", ANTON(70), fg=WHITE, bg=(200, 30, 40), pad=(40, 12), r=18)
    paste(fr, tk, W / 2, 110, pop(min(1, t / .25)))
    # route card: Alexandria -> Cairo with a moving car dot
    c = Image.new("RGBA", (900, 250), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 899, 249), 30, fill=(18, 20, 28, 238))
    x0, x1, y = 110, 790, 120
    d.line((x0, y, x1, y), fill=(90, 95, 110), width=10)
    u = ease((t - .3) / 1.6)
    xc = x0 + (x1 - x0) * u
    d.line((x0, y, xc, y), fill=YEL, width=10)
    for x, name in ((x0, "ALEXANDRIA"), (x1, "CAIRO")):
        d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=WHITE)
        d.text((x, y + 65), name, font=MONT(38, 900), fill=WHITE, anchor="mm")
    d.ellipse((xc - 26, y - 26, xc + 26, y + 26), fill=RED, outline=WHITE, width=5)
    d.text((450, 40), f"{int(round(220 * u))} km", font=MONT(36, 800), fill=YEL, anchor="mm")
    paste(fr, c, W / 2, 340, pop(min(1, (t - .15) / .3)))


HOOKS = dict(r1=hook_r1, r2=hook_r2, r3=hook_r3)


def poll(fr, t):
    """r3 effect: poll sticker during 'which brands will win'"""
    c = Image.new("RGBA", (760, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 759, 299), 30, fill=(255, 255, 255, 245))
    d.text((380, 52), "WHO WINS THIS YEAR?", font=ANTON(58), fill=(20, 20, 20), anchor="mm")
    for k, (lab, v) in enumerate((("Your favourite brand", .62), ("The underdog", .38))):
        y = 120 + k * 85
        u = ease((t - .3) / .8) * v
        d.rounded_rectangle((40, y, 720, y + 66), 33, fill=(235, 235, 240))
        if u > .05:
            d.rounded_rectangle((40, y, 40 + 680 * u, y + 66), 33, fill=((255, 190, 0) if k == 0 else (120, 90, 220)))
        d.text((70, y + 33), lab, font=MONT(34, 800), fill=(20, 20, 20), anchor="lm")
    paste(fr, c, W / 2, 330, pop(min(1, t / .3)))


def cta(fr, t, lines):
    a = lines_img([lines[0]], MONT(76, 900), stroke=8)
    paste(fr, a, W / 2, 260, pop(min(1, t / .3)))
    b = pill(lines[1], MONT(58, 800), fg=BLACK, bg=YEL)
    paste(fr, b, W / 2, 400, pop(min(1, (t - .25) / .3)))
    c = pill(lines[2] + "  →", MONT(48, 800), fg=WHITE, bg=(220, 30, 40))
    paste(fr, c, W / 2, 1520, pop(min(1, (t - .7) / .3)))


def quote_card(fr, t, segs):
    im = lines_img([segs], MONT(62, 900), stroke=6, maxw=940)
    c = Image.new("RGBA", (im.width + 60, im.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, c.width - 1, c.height - 1), 28, fill=(0, 0, 0, 160))
    c.alpha_composite(im, (30, 20))
    paste(fr, c, W / 2, 1520, pop(min(1, t / .25)))


# ---------------------------------------------------------------- sound
def sfx_whoosh(d=.35):
    n = int(d * SR); t = np.arange(n) / SR
    return music.bp(np.random.default_rng(1).standard_normal(n), 600, 6000) * np.sin(np.pi * t / d) ** 2 * .5


def sfx_pop():
    n = int(.08 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 60) * .6


def sfx_stamp():
    return music.kick(.4, 120, 40, 1.2, 1.0) * .9


def sfx_down(d=1.1):  # power-down for the energy bar
    n = int(d * SR); t = np.arange(n) / SR
    f = 700 * np.exp(-t * 2.2) + 60
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.5) * .35


def bed(seconds, bpm):
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


# ---------------------------------------------------------------- render
def render(rk):
    cfg = REELS[rk]
    parts = [cfg["cold"]] + cfg["body"]
    tl, t = [], 0.0
    for i, key in enumerate(parts):
        a, b, _ = CAP[key]
        tl.append((t, a, b, key, i == 0)); t += round((b - a) * FPS) / FPS
    body_end = t
    T = body_end + 2.6
    nfr = int(round(T * FPS))
    cold_end = tl[1][0]
    hook_len = max(cold_end, 2.4)

    vo = np.zeros(int(T * SR) + SR)
    for t0, a, b, key, cold in tl:
        x = voice(a, b); i = int(t0 * SR); vo[i:i + len(x)] += x
    vo = vo / (np.abs(vo).max() + 1e-9) * .9
    mus = bed(T + 1, {"r1": 100, "r2": 108, "r3": 96}[rk])[:len(vo)]
    mus = np.pad(mus, (0, len(vo) - len(mus)))
    env = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same")
    duck = 1 - .75 * np.clip(env / (np.percentile(env, 80) + 1e-9), 0, 1)
    fx = np.zeros_like(vo)

    def put(sig, at, g=1.0):
        i = int(at * SR); k = min(len(sig), len(fx) - i)
        if k > 0 and i >= 0: fx[i:i + k] += g * sig[:k]
    for t0, a, b, key, cold in tl[1:]:
        put(sfx_whoosh(), t0 - .12, .35)
    if rk == "r1": put(sfx_down(), .35, .8); put(sfx_stamp(), 1.5, .7)
    if rk == "r2": put(sfx_pop(), 0, .6); put(sfx_pop(), .25, .6); put(sfx_pop(), .5, .6); put(sfx_stamp(), 1.7, .5)
    if rk == "r3": put(sfx_whoosh(1.6), .3, .5)
    start = {key: t0 for t0, a, b, key, cold in tl if not cold}
    if rk == "r1": put(sfx_stamp(), start["highl"] + 1.0, .6)
    if rk == "r3": put(sfx_pop(), start["brands"], .6)
    put(sfx_whoosh(.5), body_end - .1, .6)
    mix = np.clip(vo + .15 * mus / (np.abs(mus).max() + 1e-9) * duck + fx * .5, -1, 1)
    os.makedirs(OUT, exist_ok=True)
    wav = f"{OUT}/.{rk}.wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix[:int(T * SR)] * 32767).astype(np.int16).tobytes())
    out = f"{OUT}/F&B Awards trip - {cfg['name']} ({rk}).mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-14:TP=-1", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    caps = []
    for t0, a, b, key, cold in tl:
        if cold:
            continue
        pages = caption_pages(CAP[key][2])
        nw = sum(len(p) for p in pages)
        acc = 0
        for p in pages:
            ps = t0 + (b - a) * acc / nw; acc += len(p)
            caps.append((ps, t0 + (b - a) * acc / nw, caption_img(p)))
    seg_i, src, last = 0, None, None
    for fi in range(nfr):
        T_ = fi / FPS
        if T_ < body_end:
            while seg_i + 1 < len(tl) and T_ >= tl[seg_i + 1][0]:
                seg_i += 1; src = None
            t0, a, b, key, cold = tl[seg_i]
            if src is None:
                src = frames(a, b)
            panel = src[min(int(round((T_ - t0) * FPS)), len(src) - 1)]; last = panel
            lt = T_ - t0
        else:
            panel, lt, key = last, T_ - body_end, None
        # camera on the panel: slow push in the hook, alternating punch-ins per caption, snap on cuts,
        # and a digital zoom onto the can label when he says it's highlighted (r1)
        z, cx, cy = 1.0, .5, .32
        page_i = sum(1 for c in caps if c[0] <= T_)
        if T_ < hook_len:
            z = 1.0 + .08 * T_ / hook_len
        elif T_ < body_end:
            z = 1.0 if page_i % 2 == 0 else 1.15
            if lt < .18:
                z *= 1 + .08 * (1 - lt / .18) ** 2
        if rk == "r1" and key == "highl" and T_ < body_end:
            z, cx, cy = 1.0 + .5 * ease((lt - .6) / .35), .32, .55
        if rk == "r2" and key == "match1" and T_ < body_end:
            z = 1.0 + .25 * ease(lt / .3)
        if z != 1.0:
            M = cv2.getRotationMatrix2D((cx * W, cy * VH), 0, z)
            pv = cv2.warpAffine(panel, M, (W, VH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        else:
            pv = panel
        fr = background(panel)
        fr[VY0:VY0 + VH] = pv
        # thin frame around the panel
        fr[VY0 - 6:VY0] = 255 * .9; fr[VY0 + VH:VY0 + VH + 6] = 255 * .9
        if T_ >= body_end:
            fr *= .55
            cta(fr, lt, cfg["cta"])
        else:
            if T_ < hook_len:
                HOOKS[rk](fr, T_)
            if T_ < cold_end:
                quote_card(fr, T_, cfg["card"])
            else:
                for cs, ce, im in caps:
                    if cs <= T_ < ce:
                        paste(fr, im, W / 2, 1520, pop(min(1, (T_ - cs) / .12)))
                if T_ >= hook_len:
                    if rk == "r1" and key == "highl":
                        slam(fr, stamp("0 CAFFEINE", size=100), W / 2, 330, lt, 1.0, rot=-6)
                    if rk == "r1" and key == "notice":
                        paste(fr, lines_img([[("READ THE CAN", YEL), (" 🫠".replace(" 🫠", ""), WHITE)]], ANTON(100), stroke=7), W / 2, 330, pop(min(1, lt / .2)))
                    if rk == "r2" and key in ("match1", "why"):
                        paste(fr, pill("100% MATCH", ANTON(90), fg=BLACK, bg=YEL, pad=(40, 10)), W / 2, 330, pop(min(1, lt / .2)), rot=-3)
                    if rk == "r3" and key in ("vote", "brands"):
                        poll(fr, T_ - start["vote"])
                    if rk == "r3" and key in ("route", "night"):
                        paste(fr, pill("ALEXANDRIA → CAIRO", ANTON(80), fg=WHITE, bg=(200, 30, 40), pad=(40, 10), r=18), W / 2, 330, pop(min(1, (T_ - start["route"]) / .2)))
        g2 = min(1, T_ / .12, (T - T_) / .3)
        if g2 < 1: fr *= max(g2, 0)
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print(out, f"{T:.1f}s", flush=True)


if __name__ == "__main__":
    for rk in ONLY:
        render(rk)
