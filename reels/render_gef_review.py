"""GEF honest-review reels (Nov 10 car vlog): three competing cuts, each with a cold open on his own line
(English card), a visual hook in the first second, content-matched effects, English captions and an English CTA.

usage: render_gef_review.py SRC OUT_DIR [r1 r2 r3]
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
WHITE, BLACK, YEL, RED, GREEN = (255, 255, 255), (0, 0, 0), (255, 214, 0), (232, 36, 52), (40, 200, 110)
FD = S + "/founder-events/fonts/"


def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        f.set_variation_by_axes([wght])
    return f


MONT = lambda s, w=800: font("Montserrat[wght].ttf", s, w)
ANTON = lambda s: font("Anton-Regular.ttf", s)

# captions: (src start, src end, English text). *word* = highlighted
CAP = {
    "good":   [(3.50, 9.08, "For me, the event was *really* good"), (9.08, 13.46, "I talked to *investors* — great connections for me *and the app*")],
    "paid":   [(14.67, 20.48, "But some people paid *a lot* of money"), (20.48, 25.14, "paid a *fortune* to be speakers")],
    "5m":     [(29.44, 32.05, "Some people paid over *5 MILLION* EGP")],
    "bad":    [(32.05, 38.04, "and didn't get what they paid for — for them it was *really bad*"),
               (38.04, 42.89, "Many of them are *complaining* about their money now"), (42.89, 44.36, "and honestly? *They're right.*")],
    "org":    [(55.20, 58.99, "But the *problem* was the organizer"), (58.99, 61.77, "First: way too many *volunteers*"),
               (61.77, 67.09, "and way too many *media tickets*"), (67.09, 72.02, "way more than the people who *actually paid*")],
    "70":     [(73.44, 77.47, "*70%* of the organization *FAILED*")],
    "comms":  [(99.80, 103.11, "Up to the last day I couldn't reach the *organizer*"), (103.11, 105.79, "*Nobody* knew *anything*")],
    "vol":    [(108.44, 110.68, "And the volunteers? A *disaster*")],
    "help":   [(118.37, 122.88, "They were supposed to *HELP* organize…"), (122.88, 124.47, "*No.* They were the *first* to rush in")],
    "swarm":  [(128.77, 131.52, "to take *photos* with the speakers"), (131.52, 134.25, "they *swarmed* them — not normal")],
    "media":  [(137.44, 143.69, "Biggest problem: volunteers + *too many media tickets*")],
    "crowd":  [(149.59, 152.76, "It was *SO* crowded"), (152.76, 156.13, "we couldn't see past the *media*")],
}


def seg(key):
    c = CAP[key]
    return (c[0][0], c[-1][1], key)


REELS = {
    "r1": dict(name="5 MILLION", cold=("5m",),
               body=["good", "paid", "5m", "bad"],
               cta=("Would YOU pay 5M EGP", "to speak at an event?", "Follow for honest founder takes")),
    "r2": dict(name="70 percent failed", cold=("70",),
               body=["good", "org", "70", "comms", "crowd"],
               cta=("Were you at GEF?", "Rate it /10 in the comments", "Follow for honest event reviews")),
    "r3": dict(name="the volunteers", cold=("help",),
               body=["vol", "help", "swarm", "media", "crowd"],
               cta=("Ever volunteered at an event?", "Be honest in the comments", "Follow for more founder stories")),
}


# ---------------------------------------------------------------- media
def frames(a, b):
    n = int(round((b - a) * FPS))
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}"
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a + .1}", "-i", SRC, "-an", "-vf", vf,
                        "-frames:v", str(n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < n:
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr[:n]


def voice(a, b):
    """cleaned-up voice for a segment: rumble cut, light denoise, presence, short fades"""
    af = "highpass=f=90,afftdn=nf=-25,equalizer=f=3000:t=q:w=1.2:g=3,acompressor=threshold=-20dB:ratio=3:attack=5:release=80"
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


def zoom(img, z, cx=.5, cy=.42, dx=0, dy=0, rot=0.0):
    M = cv2.getRotationMatrix2D((cx * W, cy * H), rot, z)
    M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def caption_pages(text):
    """split a caption into 2-4 word pages; *x* words highlighted"""
    words, hl = [], False
    for wd in text.split():
        st = wd.startswith("*")
        en = wd.endswith("*") or wd.endswith("*.") or wd.endswith("*,") or wd.endswith("*?")
        clean = wd.replace("*", "")
        words.append((clean, hl or st))
        hl = (hl or st) and not en
    pages, cur = [], []
    for w_ in words:
        cur.append(w_)
        if len(cur) >= 3 and (len(cur) == 4 or w_[0][-1] in ",.?—…"):
            pages.append(cur); cur = []
    if cur:
        if len(cur) == 1 and pages:
            pages[-1] += cur
        else:
            pages.append(cur)
    return pages


def caption_img(page):
    segs = []
    for i, (w_, hl) in enumerate(page):
        segs.append((w_.upper() + (" " if i < len(page) - 1 else ""), YEL if hl else WHITE))
    return lines_img([segs], MONT(68, 900), stroke=7)


# ---------------------------------------------------------------- reel-specific hook graphics
def breaking(fr, t):
    """r1: BREAKING banner + money counter"""
    k = ease(t / .25)
    bar = Image.new("RGBA", (W, 110), (220, 30, 40, 255))
    d = ImageDraw.Draw(bar)
    d.rectangle((0, 0, 250, 110), fill=(255, 255, 255, 255))
    d.text((125, 55), "BREAKING", font=ANTON(58), fill=(220, 30, 40), anchor="mm")
    d.text((280, 55), "GEF 2026 · FOUNDER'S HONEST TAKE", font=MONT(40, 800), fill=WHITE, anchor="lm")
    paste(fr, bar, W / 2 - W * (1 - k), 250)
    v = int(5_000_000 * ease(min(1, (t - .15) / .9)))
    num = lines_img([[(f"{v:,}", YEL), (" EGP", WHITE)]], ANTON(150), stroke=8)
    paste(fr, num, W / 2, 470, pop(min(1, (t - .1) / .25)))


def stamp70(fr, t):
    """r2: review ticket + giant 70% stamp"""
    tk = Image.new("RGBA", (820, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(tk)
    d.rounded_rectangle((0, 0, 819, 139), 26, fill=(255, 255, 255, 245))
    for x in range(40, 800, 40):
        d.ellipse((x - 6, -6, x + 6, 6), fill=(0, 0, 0, 0))
    d.text((410, 72), "GEF · HONEST REVIEW", font=ANTON(76), fill=(20, 20, 20), anchor="mm")
    paste(fr, tk, W / 2, 250, pop(min(1, t / .3)))
    if t > .25:
        u = min(1, (t - .25) / .18)
        big = lines_img([[("70%", RED)]], ANTON(300), stroke=10)
        paste(fr, big, W / 2, 520, 2.2 - 1.2 * ease(u), min(1, u * 2), rot=-8)


def chat(fr, t, msgs):
    """r3: group-chat takeover bubbles"""
    y = 240
    for i, (t0, who, txt, mine) in enumerate(msgs):
        if t < t0:
            break
        f = MONT(42, 700)
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        l, tp, r, b = d.textbbox((0, 0), txt, font=f)
        bw, bh = min(800, r - l + 60), b - tp + 70
        im = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        dd = ImageDraw.Draw(im)
        dd.rounded_rectangle((0, 0, bw - 1, bh - 1), 34, fill=(37, 211, 102, 250) if mine else (255, 255, 255, 250))
        dd.text((30, 12), who, font=MONT(26, 800), fill=(10, 90, 50) if mine else (120, 60, 200))
        dd.text((30 - l, 48 - tp), txt, font=f, fill=(15, 15, 15))
        x = W - 60 - bw / 2 if mine else 60 + bw / 2
        paste(fr, im, x, y + bh / 2, pop(min(1, (t - t0) / .22)))
        y += bh + 16


def icon_pill(txt, ok, f):
    """scorecard row: drawn check / cross in a circle + text on a coloured pill"""
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, tp, r, b = d.textbbox((0, 0), txt, font=f)
    th = b - tp
    s_ = th + 18
    w, h = r - l + s_ + 70, th + 34
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=((30, 170, 90) if ok else (215, 35, 50)) + (240,))
    x0, y0 = 16, (h - s_) // 2
    dd.ellipse((x0, y0, x0 + s_, y0 + s_), fill=WHITE)
    c = (30, 170, 90) if ok else (215, 35, 50)
    if ok:
        dd.line([(x0 + s_ * .25, y0 + s_ * .52), (x0 + s_ * .43, y0 + s_ * .7), (x0 + s_ * .76, y0 + s_ * .3)], fill=c, width=7)
    else:
        dd.line([(x0 + s_ * .3, y0 + s_ * .3), (x0 + s_ * .7, y0 + s_ * .7)], fill=c, width=7)
        dd.line([(x0 + s_ * .7, y0 + s_ * .3), (x0 + s_ * .3, y0 + s_ * .7)], fill=c, width=7)
    dd.text((x0 + s_ + 18 - l, (h - th) // 2 - tp), txt, font=f, fill=WHITE)
    return im


def checklist(fr, t, items):
    """r2: review scorecard that builds up across the reel"""
    y = 200
    for t0, ok, txt in items:
        if t < t0:
            break
        im = icon_pill(txt, ok, MONT(50, 800))
        paste(fr, im, W / 2, y + im.height / 2, pop(min(1, (t - t0) / .25)))
        y += im.height + 16


def cta(fr, t, lines):
    a = lines_img([lines[0]], MONT(80, 900), stroke=8)
    paste(fr, a, W / 2, 330, pop(min(1, t / .3)))
    b = pill(lines[1], MONT(60, 800), fg=BLACK, bg=YEL)
    paste(fr, b, W / 2, 470, pop(min(1, (t - .25) / .3)))
    c = pill(lines[2] + "  →", MONT(52, 800), fg=WHITE, bg=(220, 30, 40))
    paste(fr, c, W / 2, 1480, pop(min(1, (t - .7) / .3)))


def quote_card(fr, t, txt):
    """the cold open's English card"""
    im = lines_img([txt], MONT(64, 900), stroke=6, maxw=940)
    card = Image.new("RGBA", (im.width + 60, im.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle((0, 0, card.width - 1, card.height - 1), 28, fill=(0, 0, 0, 150))
    card.alpha_composite(im, (30, 20))
    paste(fr, card, W / 2, 1430, pop(min(1, t / .25)))


# ---------------------------------------------------------------- sound
def sfx_whoosh(d=.35):
    n = int(d * SR); t = np.arange(n) / SR
    return music.bp(np.random.default_rng(1).standard_normal(n), 600, 6000) * np.sin(np.pi * t / d) ** 2 * .5


def sfx_pop():
    n = int(.08 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (900 - 4000 * t) * t) * np.exp(-t * 60) * .6


def sfx_cash():
    n = int(.9 * SR); t = np.arange(n) / SR
    bell = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * 6) for f in (2093, 2637, 3136)) * .25
    clk = music.hp(np.random.default_rng(2).standard_normal(n), 3000) * np.exp(-t * 80) * .4
    return bell + clk


def sfx_stamp():
    return music.kick(.4, 120, 40, 1.2, 1.0) * .9


def bed(seconds, style):
    """quiet backing beat for under the voice"""
    bpm = {"r1": 100, "r2": 96, "r3": 104}[style]
    T = music.Track(seconds + 1, bpm)
    beats = int(seconds / T.b) + 1
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for b in range(beats):
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
    parts = [seg(k) for k in cfg["cold"]] + [seg(k) for k in cfg["body"]]
    # timeline: source segments one after another (cold open first), then a 2.4 s CTA hold on the last frame
    tl, t = [], 0.0
    for a, b, key in parts:
        d = round((b - a) * FPS) / FPS
        tl.append((t, a, b, key)); t += d
    body_end = t
    cta_d = 2.6
    T = body_end + cta_d
    nfr = int(round(T * FPS))
    # audio: voice + bed (ducked) + sfx
    vo = np.zeros(int(T * SR) + SR)
    for t0, a, b, key in tl:
        x = voice(a, b); i = int(t0 * SR); vo[i:i + len(x)] += x
    vo = vo / (np.abs(vo).max() + 1e-9) * .9
    mus = bed(T + 1, rk)[:len(vo)]
    mus = np.pad(mus, (0, len(vo) - len(mus)))
    env = np.convolve(np.abs(vo), np.ones(2400) / 2400, "same")
    duck = 1 - .75 * np.clip(env / (np.percentile(env, 80) + 1e-9), 0, 1)
    fx = np.zeros_like(vo)

    def put(sig, at, g=1.0):
        i = int(at * SR); k = min(len(sig), len(fx) - i)
        if k > 0: fx[i:i + k] += g * sig[:k]

    for t0, a, b, key in tl[1:]:
        put(sfx_whoosh(), t0 - .12, .5)
    if rk == "r1": put(sfx_cash(), .2, .7)
    if rk == "r2": put(sfx_stamp(), .3, .8)
    if rk == "r3":
        for k in range(4): put(sfx_pop(), .15 + k * .45, .7)
    put(sfx_whoosh(.5), body_end - .1, .6)
    mix = vo + .16 * mus / (np.abs(mus).max() + 1e-9) * duck + fx * .5
    mix = np.clip(mix, -1, 1)
    os.makedirs(OUT, exist_ok=True)
    wav = f"{OUT}/.{rk}.wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix[:int(T * SR)] * 32767).astype(np.int16).tobytes())
    out = f"{OUT}/GEF review - {cfg['name']} ({rk}).mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-14:TP=-1", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    # caption pages on the output timeline
    caps = []
    for t0, a, b, key in tl:
        for ca, cb, txt in CAP[key]:
            if cb <= a or ca >= b:
                continue
            pages = caption_pages(txt)
            nw = sum(len(p) for p in pages)
            s0, s1 = t0 + max(ca, a) - a, t0 + min(cb, b) - a
            acc = 0
            for p in pages:
                ps = s0 + (s1 - s0) * acc / nw; acc += len(p)
                caps.append((ps, s0 + (s1 - s0) * acc / nw, caption_img(p)))
    # r2 scorecard items and r3 chat, on the output timeline
    start = {key: t0 for t0, a, b, key in tl[1:]}
    score = [(start["good"], True, "Networking  9/10"), (start["org"] + 3.5, False, "Volunteers & media tickets"),
             (start["comms"] + .3, False, "Communication  1/10"), (start["crowd"] + .3, False, "Crowd & chairs")] if rk == "r2" else []
    msgs = [(.15, "Organizer", "Where are the volunteers??", False), (.6, "Volunteer", "busy 🤳", True),
            (1.05, "Organizer", "doing WHAT", False), (1.5, "Volunteer", "selfies with the speakers", True)] if rk == "r3" else []
    msgs = [(a, b, c.replace(" 🤳", ""), d) for a, b, c, d in msgs]
    src = None
    seg_i = 0
    last_frame = None
    cold_end = tl[1][0]
    for n in range(nfr):
        T_ = n / FPS
        if T_ < body_end:
            while seg_i + 1 < len(tl) and T_ >= tl[seg_i + 1][0]:
                seg_i += 1; src = None
            t0, a, b, key = tl[seg_i]
            if src is None:
                src = frames(a, b)
            k = min(int(round((T_ - t0) * FPS)), len(src) - 1)
            base = src[k]; last_frame = base
            lt = T_ - t0
        else:
            base = last_frame
            lt = T_ - body_end
        # camera: punch-in jump zooms alternate per caption page; snap zoom on every cut; slow push in the cold open
        page_i = sum(1 for c in caps if c[0] <= T_)
        z = 1.0 + (.12 if page_i % 2 else 0)
        if T_ < cold_end:
            z = 1.0 + .06 * T_ / cold_end  # slow push; keeps his face clear of the hook text
        if T_ < body_end and lt < .2:
            z *= 1 + .1 * (1 - lt / .2) ** 2
        dx = dy = rot = 0
        if rk == "r3" and tl[seg_i][3] == "swarm" and T_ < body_end and lt < .45:  # the swarm: camera shake
            dx, dy, rot = 14 * math.sin(lt * 70) * (1 - lt / .45), 10 * math.cos(lt * 55) * (1 - lt / .45), .8 * math.sin(lt * 40)
        if T_ >= body_end:
            z = 1.05 + .04 * lt
        fr = zoom(base, z, .5, .42, dx, dy, rot).astype(np.float32)
        g = fr.mean(2, keepdims=True); fr = np.clip(g + (fr - g) * 1.12, 0, 255)
        if T_ >= body_end:
            fr *= .55
            cta(fr, lt, cfg["cta"])
        else:
            # visual hook + cold-open card
            if T_ < cold_end:
                quote_card(fr, T_, {"r1": [("“Some people paid over ", WHITE), ("5 MILLION", YEL), (" EGP…”", WHITE)],
                                    "r2": [("“70% ", YEL), ("of the organization FAILED.”", WHITE)],
                                    "r3": [("“They were supposed to ", WHITE), ("HELP", YEL), ("…”", WHITE)]}[rk])
                if rk == "r1": breaking(fr, T_)
                if rk == "r2": stamp70(fr, T_)
                if rk == "r3":
                    pov = lines_img([[("POV: ", YEL), ("volunteers when the speakers walk in", WHITE)]], MONT(46, 900), stroke=6)
                    paste(fr, pov, W / 2, 150, pop(min(1, T_ / .25)))
                    chat(fr, T_, msgs)
            else:
                for cs, ce, im in caps:
                    if cs <= T_ < ce:
                        paste(fr, im, W / 2, 1390, pop(min(1, (T_ - cs) / .12)))
                if score:
                    checklist(fr, T_, score)
                if rk == "r1" and tl[seg_i][3] == "5m":
                    paste(fr, lines_img([[("5,000,000", YEL), (" EGP", WHITE)]], ANTON(130), stroke=8), W / 2, 300, pop(min(1, lt / .2)))
            g2 = min(1, T_ / .12, (T - T_) / .3)
            if g2 < 1: fr *= max(g2, 0)
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print(out, f"{T:.1f}s")


if __name__ == "__main__":
    for rk in ONLY:
        render(rk)
