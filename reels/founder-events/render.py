"""Founder "event syndrome" reels: one set of clips + photos, four competing edits (different hook, format,
music and effects) for A/B testing. Original audio is muted; each version gets its own synthesised track
(music.py) and every cut lands on its beat.

usage: python3 render.py <uploads dir> <out dir> [v1 v2 v3 v4]
"""
import os, sys, math, subprocess, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import music

UP, OUT = sys.argv[1], sys.argv[2]
ONLY = sys.argv[3:] or ["v1", "v2", "v3", "v4"]
W, H, FPS = 1080, 1920, 30
WHITE, BLACK, YEL, RED, GREEN = (255, 255, 255), (0, 0, 0), (255, 214, 0), (232, 36, 52), (40, 200, 110)

# ---------------------------------------------------------------- sources (muted)
CLIP = {
    "coffee": "472902d0-IMG_7473.mov",
    "gym": "d0548637-IMG_7460.mov",
    "egp": "bd890208-IMG_6303_-_first_30_EGP_reel_v1.mp4",
    "eip": "901955b0-f9661d6673684aa6b045048994281533.mov",   # past 7.6 s is an old Arabic CTA: never used
    "car": "683f6e0a-IMG_7306.mov",
    "sonesta": "d85dd214-IMG_7384.mov",
    "spa": "6ae5d429-IMG_7465.mov",
}
PHOTO = {
    "kabab": "1a4afd15-image.jpg",
    "thanks": "e9b7f42c-image.jpg",
    "parking": "52f38962-image.jpg",
    "patisserie": "042f1edd-image.jpg",
    "stage": "d020fab8-image.png",   # a story screenshot: only the stage is kept, the app UI and handle are cropped
}


def font(name, size, wght=None):
    f = ImageFont.truetype(f"{HERE}/fonts/{name}", size)
    if wght:
        f.set_variation_by_axes([wght])
    return f


ANTON = lambda s: font("Anton-Regular.ttf", s)
MONT = lambda s, w=800: font("Montserrat[wght].ttf", s, w)
PLAY = lambda s, w=700: font("PlayfairDisplay[wght].ttf", s, w)
PLAYI = lambda s, w=500: font("PlayfairDisplay-Italic[wght].ttf", s, w)


def cover(im, fx=.5, fy=.5):
    """crop/scale a PIL image to fill 9:16, keeping the focus point (fx, fy) in frame"""
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((int(w * s + .5), int(h * s + .5)), Image.LANCZOS)
    x = int(min(max(fx * im.width - W / 2, 0), im.width - W))
    y = int(min(max(fy * im.height - H / 2, 0), im.height - H))
    return np.asarray(im.crop((x, y, x + W, y + H)).convert("RGB"))


def photo(key):
    im = Image.open(f"{UP}/{PHOTO[key]}").convert("RGB")
    if key == "stage":
        im = im.crop((380, 520, 1080, 2280)).rotate(90, expand=True)  # stage + screen, turned upright
        bg = Image.fromarray(cover(im)).filter(ImageFilter.GaussianBlur(40))
        bg = Image.fromarray((np.asarray(bg) * .55).astype(np.uint8))
        fw = int(W * 1.4)  # the screen is the middle ~70%: let the side lights run off the frame
        fg = im.resize((fw, int(im.height * fw / im.width)), Image.LANCZOS)
        bg.paste(fg, ((W - fw) // 2, (H - fg.height) // 2 - 60))
        return np.asarray(bg)
    return cover(im, .5, {"kabab": .55, "parking": .5, "thanks": .55, "patisserie": .55}.get(key, .5))


def clip_frames(key, a, b, n):
    """n frames covering source seconds a..b of a clip (sped up / slowed down to fit), muted, 9:16"""
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts={(n / FPS) / (b - a):.5f}*PTS,fps={FPS}"
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a + .05}", "-i", f"{UP}/{CLIP[key]}",
                        "-an", "-vf", vf, "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n:
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr[:n]


# ---------------------------------------------------------------- text / graphics
def text_block(lines, f, fill=WHITE, stroke=0, stroke_fill=BLACK, spacing=8, align="center", shadow=0, maxw=960):
    """multi-line text as an RGBA image; a line may be [(text, colour), ...] for highlighted words"""
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    rows = []
    for ln in lines:
        segs = ln if isinstance(ln, list) else [(ln, fill)]
        ws = [d.textbbox((0, 0), s, font=f, stroke_width=stroke) for s, _ in segs]
        rows.append((segs, ws, sum(b[2] - b[0] for b in ws)))
    asc, desc = f.getmetrics()
    lh = asc + desc + spacing
    tw = max(r[2] for r in rows) + 2 * stroke + 2 * shadow
    im = Image.new("RGBA", (tw + 20, lh * len(rows) + 2 * stroke + 20 + shadow), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for i, (segs, ws, rw) in enumerate(rows):
        x = 10 + stroke + ((tw - rw) // 2 if align == "center" else 0)
        y = 10 + stroke + i * lh
        for (s, col), bb in zip(segs, ws):
            if shadow:
                ImageDraw.Draw(sh).text((x - bb[0] + shadow, y + shadow), s, font=f, fill=(0, 0, 0, 170))
            ImageDraw.Draw(im).text((x - bb[0], y), s, font=f, fill=col, stroke_width=stroke, stroke_fill=stroke_fill)
            x += bb[2] - bb[0]
    if shadow:
        sh = sh.filter(ImageFilter.GaussianBlur(shadow))
        sh.alpha_composite(im)
        im = sh
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return im


def pill(txt, f, fg=BLACK, bg=YEL, pad=(30, 14), r=None, icon=None):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, rr, b = d.textbbox((0, 0), txt, font=f)
    iw = (b - t) + 14 if icon else 0
    w, h = rr - l + 2 * pad[0] + iw, b - t + 2 * pad[1]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.rounded_rectangle((0, 0, w - 1, h - 1), r if r is not None else h // 2, fill=bg)
    if icon == "check":
        s = b - t
        x0, y0 = pad[0], pad[1]
        dr.ellipse((x0, y0, x0 + s, y0 + s), fill=GREEN)
        dr.line([(x0 + s * .25, y0 + s * .52), (x0 + s * .43, y0 + s * .7), (x0 + s * .76, y0 + s * .3)], fill=WHITE, width=max(3, s // 8))
    dr.text((pad[0] + iw - l, pad[1] - t), txt, font=f, fill=fg)
    return im


def paste(fr, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    if scale != 1.0 or rot:
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


def pop_in(u):  # 0..1 -> overshoot scale
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    return 1 + 1.7 * (u - 1) ** 3 + .7 * (u - 1) ** 2 * 0 + .25 * math.sin(u * math.pi) * (1 - u)


def ease(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)


def zoom(img, z, cx=.5, cy=.5, dx=0.0, dy=0.0, rot=0.0):
    M = cv2.getRotationMatrix2D((cx * W, cy * H), rot, z)
    M[0, 2] += dx + (W / 2 - cx * W)
    M[1, 2] += dy + (H / 2 - cy * H)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def grade(fr, sat=1.15, con=1.08, warm=0.0, teal=0.0):
    f = fr.astype(np.float32)
    g = f.mean(2, keepdims=True)
    f = g + (f - g) * sat
    f = (f - 128) * con + 128
    if warm: f[..., 0] += 10 * warm; f[..., 2] -= 8 * warm
    if teal:  # teal shadows, warm highlights
        lum = f.mean(2, keepdims=True) / 255
        f += teal * np.concatenate([(lum - .5) * 30, lum * 0, (.5 - lum) * 30], 2)
    return np.clip(f, 0, 255)


def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * .75)) ** 2 + ((y - H / 2) / (H * .7)) ** 2)
    return (1 - .35 * np.clip(r - .45, 0, 1) ** 1.5)[..., None]


VIG = vignette()


# ---------------------------------------------------------------- the four edits
# shot: (beats, kind, key, a, b) kind "clip" (seconds a..b of the clip) or "photo"; plus per-shot text/fx
def V(beats, kind, key, a=0.0, b=0.0, **kw):
    return dict(beats=beats, kind=kind, key=key, a=a, b=b, **kw)


VERSIONS = {
    "v1": dict(  # POV: day-in-the-life with timestamps (house)
        name="POV founder day", style="house", drop=4,
        shots=[
            V(4, "clip", "eip", .75, 1.45, hook=True),
            V(4, "clip", "gym", 1.6, 4.5, ts="06:30", cap="Gym. (networking warm-up)"),
            V(2, "clip", "coffee", 0, 2.8, ts="08:15", cap="Coffee #1"),
            V(2, "photo", "parking", ts="09:00", cap="Same parking spot. Every event."),
            V(4, "clip", "eip", 2.0, 5.5, ts="10:00", cap="Entrepreneurs Investment Program", capy=.80),
            V(2, "photo", "patisserie", ts="12:30", cap="Coffee meeting #2"),
            V(4, "clip", "car", .4, 4.4, ts="14:00", cap="On the way to event #3", capy=.80),
            V(4, "photo", "stage", ts="16:00", cap="Naguib Sawiris on stage", capy=.80),
            V(2, "clip", "sonesta", 0, 1.06, ts="18:30", cap="Next venue", capy=.82),
            V(2, "photo", "thanks", ts="19:30", cap="Event #4 done"),
            V(2, "photo", "kabab", ts="21:00", cap="Dinner = another meeting"),
            V(4, "clip", "spa", 0, 3.2, ts="23:00", cap="“Recovery”"),
            V(4, "clip", "gym", 14.4, 16.8, cta=True),
        ],
        hook=["POV:", "you're a founder with", [("EVENT SYNDROME", YEL)]],
        cta=("Tomorrow? Same thing.", "Follow for the founder diaries", "Tag a founder who never skips an event"),
    ),
    "v2": dict(  # medical "diagnosis" meme + checklist (bouncy pop)
        name="Event Syndrome diagnosis", style="pop", drop=4,
        shots=[
            V(4, "clip", "gym", 14.4, 16.8, hook=True),
            V(3, "clip", "gym", 1.6, 4.5, sym="Gym at 6AM… to “network better”"),
            V(3, "photo", "parking", sym="Knows every hotel parking by heart"),
            V(3, "clip", "coffee", 0, 2.8, sym="4th coffee before noon"),
            V(3, "photo", "stage", sym="“Just ONE more event”"),
            V(3, "photo", "kabab", sym="Lunch = meeting. Dinner = meeting."),
            V(3, "photo", "thanks", sym="Photographs every “Thank You” slide"),
            V(3, "clip", "spa", 0, 3.2, sym="Calls the spa “recovery”"),
            V(6, "clip", "eip", .75, 1.45, cta=True),
        ],
        cta=("PROGNOSIS: incurable", "Follow if you have it too", "Tag a founder who's got it"),
    ),
    "v3": dict(  # cinematic "from 30 EGP to the front row" + magazine cover (cinematic hip-hop)
        name="30 EGP to the front row", style="cinematic", drop=4,
        shots=[
            V(4, "clip", "egp", 0.0, 1.1, hook=True),
            V(4, "photo", "stage", line="Now I sit in rooms like this."),
            V(2, "photo", "thanks", line="Everyone sees the events."),
            V(4, "clip", "gym", 1.6, 4.5, line="Nobody sees the 6AM."),
            V(2, "clip", "coffee", 0, 2.8, line="The 4th coffee."),
            V(2, "photo", "parking", line="The parking at midnight."),
            V(2, "clip", "car", .4, 2.2, line="The drive between rooms.", liney=.84),
            V(4, "clip", "eip", 2.0, 5.5, line="But every room gets me closer.", liney=.84),
            V(6, "clip", "eip", .75, 1.45, cta=True),
        ],
        cta=("Follow the Reservya journey",),
    ),
    "v4": dict(  # speedrun counter, 7 events in 7 days (phonk)
        name="7 events speedrun", style="phonk", drop=4,
        shots=[
            V(4, "clip", "car", 0.0, 1.9, hook=True),
            V(2, "clip", "eip", 1.45, 2.05, n=1, lab="EIP", laby=.70),
            V(2, "photo", "stage", n=2, lab="ORASCOM SUMMIT"),
            V(1, "clip", "gym", 2.6, 3.4, lab="NO REST"),
            V(2, "photo", "thanks", n=3, lab="ANOTHER PANEL"),
            V(2, "photo", "patisserie", n=4, lab="COFFEE MEETING"),
            V(1, "clip", "coffee", 0, 1.0, lab="REFUEL"),
            V(2, "clip", "sonesta", 0, 1.06, n=5, lab="SONESTA", laby=.70),
            V(2, "photo", "kabab", n=6, lab="DINNER MEETING"),
            V(1, "photo", "parking", lab="PARKING 04-A. AGAIN."),
            V(2, "clip", "spa", 0, 3.2, n=7, lab="“RECOVERY”"),
            V(6, "clip", "gym", 14.4, 16.8, cta=True),
        ],
        cta=("WEEK 2 STARTS MONDAY", "Follow to see if I survive", "Tag a founder who needs a nap"),
    ),
}


# ---------------------------------------------------------------- per-version overlay painters
def hook_v1(fr, t, sh):
    u = t / .35
    s = pop_in(min(1, u))
    for i, ln in enumerate(VERSIONS["v1"]["hook"]):
        im = text_block([ln], MONT(84 if i == 2 else 64, 900 if i == 2 else 800), stroke=7)
        paste(fr, im, W / 2, H * .60 + i * 96, s if i == 0 else pop_in(min(1, (t - .12 * i) / .35)))


def timestamp(fr, t, sh, beat):
    chip = pill(sh["ts"], MONT(64, 900), fg=BLACK, bg=YEL, pad=(34, 16))
    k = pop_in(min(1, t / .25))
    paste(fr, chip, W / 2, 230, k)
    cap = text_block([sh["cap"]], MONT(58, 800), stroke=6)
    u = ease(t / .3)
    paste(fr, cap, W / 2, H * sh.get("capy", .74) + 40 * (1 - u), 1, u)


def cta_card(fr, t, lines, style):
    if style == "v1":
        im = text_block([lines[0]], MONT(70, 900), stroke=7)
        paste(fr, im, W / 2, H * .30, pop_in(min(1, t / .3)))
        b = pill(lines[1], MONT(50, 800), fg=BLACK, bg=YEL)
        paste(fr, b, W / 2, H * .62, pop_in(min(1, (t - .45) / .3)))
        s = text_block([lines[2]], MONT(40, 700), stroke=4)
        paste(fr, s, W / 2, H * .69, 1, ease((t - .8) / .3))


def snap_punch(t, k=.14, d=.18):  # snap zoom on the cut
    return 1 + k * math.exp(-t / d * 3) if t < d * 3 else 1.0


MED = None


def med_card():
    """the 'DIAGNOSIS' card for v2"""
    w, h = 900, 520
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 34, fill=(250, 250, 248, 255))
    d.rounded_rectangle((0, 0, w - 1, 120), 34, fill=(220, 40, 52, 255))
    d.rectangle((0, 80, w - 1, 120), fill=(220, 40, 52, 255))
    cx, cy, s = 70, 60, 26  # medical cross
    d.rectangle((cx - s / 3, cy - s, cx + s / 3, cy + s), fill=WHITE); d.rectangle((cx - s, cy - s / 3, cx + s, cy + s / 3), fill=WHITE)
    d.text((120, 60), "MEDICAL REPORT", font=MONT(46, 900), fill=WHITE, anchor="lm")
    d.text((50, 170), "PATIENT: Founder", font=MONT(38, 600), fill=(90, 90, 90))
    d.text((50, 235), "DIAGNOSIS:", font=MONT(42, 800), fill=(30, 30, 30))
    d.text((50, 300), "Founder", font=ANTON(92), fill=(220, 40, 52))
    d.text((50, 400), "Event Syndrome", font=ANTON(92), fill=(220, 40, 52))
    return im


def stamp():
    im = Image.new("RGBA", (420, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, 414, 144), 18, outline=(220, 40, 52, 235), width=10)
    d.text((210, 76), "CONFIRMED", font=ANTON(84), fill=(220, 40, 52, 235), anchor="mm")
    return im


def symptom(fr, t, sh, idx, total):
    hdr = pill(f"SYMPTOM {idx}/{total}", MONT(36, 800), fg=WHITE, bg=(220, 40, 52))
    paste(fr, hdr, W / 2, 230, pop_in(min(1, t / .25)))
    words = sh["sym"].split()
    half = (len(words) + 1) // 2
    lines = [" ".join(words[:half]), " ".join(words[half:])] if len(sh["sym"]) > 22 else [sh["sym"]]
    txt = text_block(lines, MONT(66, 900), fill=(25, 25, 25), spacing=4)
    card = Image.new("RGBA", (txt.width + 130, txt.height + 40), (0, 0, 0, 0))
    dc = ImageDraw.Draw(card)
    dc.rounded_rectangle((0, 0, card.width - 1, card.height - 1), 30, fill=(250, 250, 248, 245))
    s_ = 56; x0, y0 = 34, (card.height - s_) // 2
    dc.ellipse((x0, y0, x0 + s_, y0 + s_), fill=GREEN)
    dc.line([(x0 + s_ * .25, y0 + s_ * .52), (x0 + s_ * .43, y0 + s_ * .7), (x0 + s_ * .76, y0 + s_ * .3)], fill=WHITE, width=7)
    card.alpha_composite(txt, (110, 20))
    if card.width > 1000:
        card = card.resize((1000, int(card.height * 1000 / card.width)), Image.LANCZOS)
    paste(fr, card, W / 2, 330 + card.height / 2, pop_in(min(1, (t - .12) / .3)))


def letterbox(fr, h=150):
    fr[:h] = 0; fr[-h:] = 0


def subtitle(fr, t, txt, y=.80):
    im = text_block([txt], PLAYI(66, 500), shadow=6)
    u = ease(t / .45)
    paste(fr, im, W / 2, H * y + 18 * (1 - u), 1, u)


def magazine(fr, t):
    """'THE FOUNDER ISSUE' cover over the frame"""
    a = ease(t / .4)
    mast = text_block(["FOUNDERS"], PLAY(190, 900), fill=WHITE, shadow=8)
    paste(fr, mast, W / 2, 250, 1, a)
    bar = pill("THE EVENT ISSUE", MONT(34, 800), fg=WHITE, bg=(200, 30, 40), r=4)
    paste(fr, bar, W / 2, 380, 1, ease((t - .3) / .3))
    l1 = text_block([[("From ", WHITE), ("30 EGP", YEL)], "to the front row"], PLAY(64, 800), shadow=6)
    paste(fr, l1, 250, 1180, 1, ease((t - .6) / .4))
    l2 = text_block(["Mina Mounir", "Founder, Reservya"], MONT(38, 700), shadow=5)
    paste(fr, l2, 820, 1220, 1, ease((t - .9) / .4))
    c = pill("Follow the Reservya journey  →", MONT(44, 800), fg=BLACK, bg=YEL)
    paste(fr, c, W / 2, 1470, pop_in(min(1, (t - 1.4) / .35)))


def counter(fr, t, n, lab, y=.20):
    s = pop_in(min(1, t / .18))
    big = text_block([[(f"{n:02d}", RED), ("/07", WHITE)]], ANTON(230), stroke=8)
    paste(fr, big, W / 2, H * y, s)
    if lab:
        l = text_block([lab], ANTON(78), stroke=6)
        paste(fr, l, W / 2, H * y + 170, pop_in(min(1, (t - .08) / .2)))


def label(fr, t, lab, y=.22):
    l = text_block([lab], ANTON(96), stroke=7)
    paste(fr, l, W / 2, H * y, pop_in(min(1, t / .18)))


def rgb_split(fr, k):
    o = int(k)
    if o <= 0: return fr
    out = fr.copy()
    out[:, o:, 0] = fr[:, :-o, 0]
    out[:, :-o, 2] = fr[:, o:, 2]
    return out


# ---------------------------------------------------------------- render
def render(vk):
    cfg = VERSIONS[vk]
    style = cfg["style"]
    total_beats = sum(s["beats"] for s in cfg["shots"])
    audio, beat = music.STYLES[style](total_beats, cfg["drop"])
    tail = {"house": 1.2, "pop": 1.0, "cinematic": 1.6, "phonk": .9}[style]  # last shot holds a bit past the bar
    T = total_beats * beat + tail
    nfr = int(T * FPS)
    os.makedirs(OUT, exist_ok=True)
    wav = f"{OUT}/.{vk}.wav"
    a16 = (np.clip(audio[:int(T * music.SR)], -1, 1) * 32767).astype(np.int16)
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(music.SR); w.writeframes(a16.tobytes())
    out = f"{OUT}/Founder events - {cfg['name']} ({vk}).mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-14:TP=-1", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    med, stp = med_card(), stamp()
    starts = np.cumsum([0] + [s["beats"] for s in cfg["shots"]])
    sym_total = sum(1 for s in cfg["shots"] if "sym" in s)
    sym_i = 0
    for si, sh in enumerate(cfg["shots"]):
        t0 = starts[si] * beat
        last = si == len(cfg["shots"]) - 1
        d = sh["beats"] * beat + (tail if last else 0)
        n = int(round((t0 + d) * FPS)) - int(round(t0 * FPS))
        if sh["kind"] == "clip":
            frames = clip_frames(sh["key"], sh["a"], sh["b"], n)
        else:
            still = photo(sh["key"])
            frames = None
        if "sym" in sh:
            sym_i += 1
        for k in range(n):
            t = k / FPS
            u = t / d
            src = frames[k] if frames is not None else still
            # camera: slow push on stills (digital zoom), snap punch on the cut, zoom-through into the next shot
            z, rot, dx, dy = 1.0, 0.0, 0.0, 0.0
            if frames is None:
                z = 1.04 + .10 * u if style != "cinematic" else 1.02 + .07 * u
            if style in ("house", "pop", "phonk") and si > 0:
                z *= snap_punch(t, .16 if style == "phonk" else .12)
            if style in ("house", "cinematic") and not last and d - t < .12:  # zoom-through cut
                z *= 1 + 1.8 * ((.12 - (d - t)) / .12) ** 2
            if style == "phonk" and (sh.get("n") or sh.get("hook")) and t < .25:  # frame-break shake on impacts
                dx, dy, rot = 26 * math.sin(t * 90) * (1 - t / .25), 18 * math.cos(t * 70) * (1 - t / .25), 1.2 * math.sin(t * 60) * (1 - t / .25)
            fr = zoom(src, z, .5, .5, dx, dy, rot) if (z != 1 or rot or dx) else src.copy()
            if style == "cinematic":
                fr = grade(fr, 1.05, 1.1, teal=1.0)
            elif style == "phonk":
                fr = grade(fr, 1.25, 1.15)
            else:
                fr = grade(fr, 1.18, 1.06, warm=.4)
            fr *= VIG
            if style == "phonk" and t < .1 and si > 0:
                fr = rgb_split(fr, 18 * (1 - t / .1))
            # ---- overlays
            if style == "house":
                if sh.get("hook"):
                    hook_v1(fr, t, sh)
                elif sh.get("cta"):
                    cta_card(fr, t, cfg["cta"], "v1")
                else:
                    timestamp(fr, t, sh, beat)
            elif style == "pop":
                if sh.get("hook"):
                    cs = pop_in(min(1, (t - .15) / .35))
                    paste(fr, med, W / 2, H * .30, cs, rot=-2)
                    if t > 1.1:
                        paste(fr, stp, W / 2 + 200, H * .30 + 330, max(.01, 1.6 - 3 * min(1, (t - 1.1) / .2)) if t < 1.3 else 1, rot=12)
                elif sh.get("cta"):
                    p = text_block([[("PROGNOSIS: ", WHITE), ("incurable", YEL)]], MONT(70, 900), stroke=7)
                    paste(fr, p, W / 2, H * .62, pop_in(min(1, t / .3)))
                    paste(fr, pill(cfg["cta"][1], MONT(50, 800), fg=BLACK, bg=YEL), W / 2, H * .70, pop_in(min(1, (t - .5) / .3)))
                    paste(fr, text_block([cfg["cta"][2]], MONT(40, 700), stroke=4), W / 2, H * .765, 1, ease((t - .8) / .3))
                else:
                    symptom(fr, t, sh, sym_i, sym_total)
            elif style == "cinematic":
                if not sh.get("hook"):
                    letterbox(fr)
                if sh.get("line"):
                    subtitle(fr, t, sh["line"], sh.get("liney", .78))
                if sh.get("cta"):
                    magazine(fr, t)
            elif style == "phonk":
                if sh.get("hook"):
                    q = text_block(["“Okay guys, right now I'm…”"], MONT(56, 800), stroke=6)
                    paste(fr, q, W / 2, H * .80, 1, ease(t / .2))
                    if t > beat * 2:
                        paste(fr, text_block([[("EVENT ", WHITE), ("#7", RED)], "THIS WEEK"], ANTON(150), stroke=8),
                              W / 2, H * .22, pop_in(min(1, (t - beat * 2) / .15)))
                elif sh.get("cta"):
                    paste(fr, text_block(["WEEK 2", [("STARTS ", WHITE), ("MONDAY", RED)]], ANTON(150), stroke=8), W / 2, H * .25,
                          pop_in(min(1, t / .18)))
                    paste(fr, pill(cfg["cta"][1], MONT(50, 800), fg=BLACK, bg=YEL), W / 2, H * .70, pop_in(min(1, (t - .5) / .25)))
                    paste(fr, text_block([cfg["cta"][2]], MONT(40, 700), stroke=4), W / 2, H * .765, 1, ease((t - .8) / .3))
                elif sh.get("n"):
                    counter(fr, t, sh["n"], sh["lab"], sh.get("laby", .20))
                else:
                    label(fr, t, sh["lab"])
            # global fade in/out
            g = min(1, (t0 + t) / .15, (T - (t0 + t)) / .35)
            if g < 1:
                fr *= max(g, 0)
            enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print(out, f"{T:.1f}s")
    return out


if __name__ == "__main__":
    for vk in ONLY:
        render(vk)
