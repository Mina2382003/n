"""F&B Awards 2026 at the Citadel, Part 2: countdown + entering the event. Music-driven (no speech in the clips):
the hook and story are on-screen text, every cut lands on the beat, a 3-2-1 countdown builds to the drop as he
walks into the venue, and it ends on a cliffhanger for Part 3.

usage: render_fnb_countdown.py UPLOAD_DIR OUT_DIR
"""
import os, sys, math, glob, subprocess, wave
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

S = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/founder-events")
import music

UP, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, SR = 1080, 1920, 30, music.SR
WHITE, BLACK, YEL, RED, PURPLE = (255, 255, 255), (0, 0, 0), (255, 214, 0), (232, 36, 52), (150, 70, 255)
FD = S + "/founder-events/fonts/"
BPM, DROP = 124, 8
B = 60 / BPM


def font(name, size, wght=None):
    f = ImageFont.truetype(FD + name, size)
    if wght:
        f.set_variation_by_axes([wght])
    return f


MONT = lambda s, w=800: font("Montserrat[wght].ttf", s, w)
ANTON = lambda s: font("Anton-Regular.ttf", s)


def clip(n):
    return glob.glob(f"{UP}/*IMG_{n}.mov")[0]


# shots: (beats, kind, source, a, b)  — clip seconds a..b are time-fitted to the beats
SHOTS = [
    (4, "clip", "8230", 2.4, 6.6, "hook"),        # driving up: the Citadel mosque appears
    (4, "clip", "8231", 0.0, 2.06, "count"),      # the gates: 3 · 2 · 1
    (2, "clip", "8232", 1.95, 2.76, "drop"),      # DROP: through the purple arch
    (4, "clip", "8239", 0.55, 3.90, "carpet"),    # red carpet -> F&B AWARDS & CEREMONY 2026 wall
    (4, "photo", "c9c53b2e-image.jpg", 0, 0, "fit"),  # him on the red carpet
    (2, "clip", "8240", 0.0, 0.80, "trophy"),
    (2, "clip", "8241", 0.0, 0.93, "crowd"),
    (8, "clip", "8242", 0.0, 4.20, "stage"),      # stage + lasers -> AND THE WINNER IS…
]
TAIL = 2.4  # CTA hold after the last beat


# ---------------------------------------------------------------- media
def clip_frames(n, a, b, nfr):
    vf = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setpts={(nfr / FPS) / (b - a):.5f}*PTS,fps={FPS}"
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a + .05}", "-i", clip(n), "-an", "-vf", vf,
                        "-frames:v", str(nfr), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
    fr = np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)
    if len(fr) < nfr:
        fr = np.concatenate([fr, np.repeat(fr[-1:], nfr - len(fr), 0)])
    return fr[:nfr]


def photo(name):
    im = Image.open(f"{UP}/{name}").convert("RGB")
    w, h = im.size
    s = max(W / w, H / h)
    im = im.resize((int(w * s + .5), int(h * s + .5)), Image.LANCZOS)
    x = (im.width - W) // 2
    y = int(min(max(.52 * im.height - H / 2, 0), im.height - H))
    return np.asarray(im.crop((x, y, x + W, y + H)))


def clip_audio(n, a, b):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a}", "-t", f"{b - a}", "-i", clip(n), "-vn", "-ac", "1", "-ar", str(SR),
                        "-af", "highpass=f=120", "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


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


def lines_img(lines, f, stroke=0, gap=6, maxw=1000):
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


def pill(txt, f, fg=BLACK, bg=YEL, pad=(30, 12), r=None):
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


def zoom(img, z, cx=.5, cy=.5, rot=0.0, dx=0, dy=0):
    M = cv2.getRotationMatrix2D((cx * W, cy * H), rot, z)
    M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def count_digit(n, size=520):
    """big countdown digit inside a glowing ring"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, size - 10, size - 10), outline=(255, 255, 255, 230), width=14)
    d.ellipse((40, 40, size - 40, size - 40), fill=(20, 0, 40, 120))
    d.text((size / 2, size / 2 + 10), str(n), font=ANTON(int(size * .62)), fill=WHITE, anchor="mm",
           stroke_width=8, stroke_fill=PURPLE)
    return im


def part_badge(n):
    return pill(f"F&B AWARDS · PART {n}", ANTON(52), fg=WHITE, bg=(200, 30, 40, 235), pad=(34, 8), r=14)


# ---------------------------------------------------------------- render
def render():
    total_beats = sum(s[0] for s in SHOTS)
    audio, b = music.house(total_beats, drop=DROP, bpm=BPM)
    T = total_beats * B + TAIL
    nfr = int(round(T * FPS))
    mix = audio[:int(T * SR)].astype(np.float64)
    if len(mix) < int(T * SR):
        mix = np.pad(mix, ((0, int(T * SR) - len(mix)), (0, 0)))

    def put(sig, at, g=1.0):
        i = int(at * SR); k = min(len(sig), len(mix) - i)
        if k > 0 and i >= 0:
            mix[i:i + k] += g * sig[:k, None] if sig.ndim == 1 else g * sig[:k]
    # countdown ticks on beats 4, 5, 6 and a riser whoosh into the drop
    for k, bb in enumerate((4, 5, 6)):
        n = int(.12 * SR); t = np.arange(n) / SR
        tick = np.sin(2 * np.pi * (1500 + 300 * k) * t) * np.exp(-t * 40) * .5
        put(tick, bb * B, .9)
    put(music.whoosh(.6), (DROP - 1.2) * B, .8)
    # the real crowd/stage sound fades in under the stage shot
    st = sum(s[0] for s in SHOTS[:-1]) * B
    amb = clip_audio("8242", 0.0, 4.2 + TAIL)
    amb = amb[:int((T - st) * SR)]
    fade = np.minimum(1, np.arange(len(amb)) / (.6 * SR))
    put(amb * fade / (np.abs(amb).max() + 1e-9), st, .35)
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.3) * .92
    os.makedirs(OUT, exist_ok=True)
    wav = f"{OUT}/.fnb.wav"
    with wave.open(wav, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype(np.int16).tobytes())
    out = f"{OUT}/F&B Awards Part 2 - countdown and entering the Citadel.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                            "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-14:TP=-1", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                           stdin=subprocess.PIPE)
    starts = np.cumsum([0] + [s[0] for s in SHOTS])
    badge = part_badge(2)
    digits = {n: count_digit(n) for n in (3, 2, 1)}
    last = None
    for si, (beats, kind, src, a, b_, role) in enumerate(SHOTS):
        t0 = starts[si] * B
        is_last = si == len(SHOTS) - 1
        d = beats * B + (TAIL if is_last else 0)
        n = int(round((t0 + d) * FPS)) - int(round(t0 * FPS))
        if kind == "clip":
            fit_n = int(round(beats * B * FPS))
            frs = clip_frames(src, a, b_, fit_n)
            if n > fit_n:
                frs = np.concatenate([frs, np.repeat(frs[-1:], n - fit_n, 0)])
        else:
            still = photo(src)
            frs = None
        for k in range(n):
            t = k / FPS
            T_ = t0 + t
            base = frs[k] if frs is not None else still
            z, rot, dx, dy = 1.0, 0.0, 0, 0
            if role == "hook":
                z = 1.0 + .10 * t / d
            if role == "count":
                z = 1.0 + .22 * (t / d) ** 2  # slow creep in as the count builds
            if role == "drop":
                z = 1.25 - .25 * ease(t / .25)  # zoom-out punch on the drop
                if t < .3:
                    dx, dy, rot = 22 * math.sin(t * 80) * (1 - t / .3), 16 * math.cos(t * 65) * (1 - t / .3), 1.2 * math.sin(t * 50) * (1 - t / .3)
            if role in ("carpet", "trophy", "crowd") and t < .15:
                z = 1.12 - .12 * t / .15  # snap zoom on each cut
            if role == "fit":
                z = 1.12 - .10 * ease(t / d)
            if role == "stage":
                z = 1.0 + .08 * t / d
            if not is_last and d - t < .1 and role not in ("hook",):  # zoom-through into the next shot
                z *= 1 + 1.4 * ((.1 - (d - t)) / .1) ** 2
            fr = zoom(base, z, .5, .5, rot, dx, dy).astype(np.float32) if (z != 1 or rot or dx) else base.astype(np.float32)
            g = fr.mean(2, keepdims=True); fr = np.clip(g + (fr - g) * 1.2, 0, 255)
            fr = np.clip((fr - 128) * 1.06 + 128, 0, 255)
            # ---- overlays
            if role == "hook":
                paste(fr, badge, W / 2, 150, pop(min(1, t / .25)))
                l1 = lines_img([[("POV: ", YEL), ("you're invited to the", WHITE)]], MONT(62, 900), stroke=7)
                l2 = lines_img([[("F&B AWARDS 2026", YEL)]], ANTON(150), stroke=8)
                l3 = lines_img([[("…at the ", WHITE), ("CITADEL", YEL)]], MONT(72, 900), stroke=7)
                paste(fr, l1, W / 2, 1180, pop(min(1, (t - .05) / .25)))
                paste(fr, l2, W / 2, 1300, pop(min(1, (t - .3) / .25)))
                paste(fr, l3, W / 2, 1430, pop(min(1, (t - .9) / .25)))
            if role == "count":
                cb = int(t / B)  # 0..3 within the shot
                lab = lines_img(["ENTERING IN…"], ANTON(90), stroke=7)
                paste(fr, lab, W / 2, 470, 1, ease(t / .2))
                if cb < 3:
                    u = (t - cb * B) / B
                    paste(fr, digits[3 - cb], W / 2, H / 2 + 60, 1.35 - .35 * ease(u / .35), min(1, u / .12))
                else:
                    u = (t - 3 * B) / B
                    go = lines_img([[("LET'S ", WHITE), ("GO", YEL)]], ANTON(230), stroke=10)
                    paste(fr, go, W / 2, H / 2 + 60, pop(min(1, u / .3)))
            if role == "drop" and t < .18:  # white flash on the drop
                fr = fr + (255 - fr) * (1 - t / .18)
            if role == "carpet":
                paste(fr, pill("RED CARPET ✓".replace(" ✓", ""), ANTON(70), fg=WHITE, bg=(200, 30, 40, 235), pad=(34, 8), r=14), W / 2, 230, pop(min(1, t / .25)))
            if role == "fit":
                paste(fr, lines_img([[("RED CARPET ", WHITE), ("CHECK", YEL)]], ANTON(110), stroke=7), W / 2, 220, pop(min(1, t / .25)))
                paste(fr, pill("FOUNDER · RESERVYA", MONT(44, 800), fg=BLACK, bg=YEL), W / 2, 1640, pop(min(1, (t - .4) / .3)))
            if role == "trophy":
                paste(fr, lines_img([[("WHO TAKES ", WHITE), ("THIS", YEL), (" HOME?", WHITE)]], ANTON(110), stroke=7), W / 2, 330, pop(min(1, t / .2)))
            if role == "crowd":
                paste(fr, lines_img([[("THE WHOLE ", WHITE), ("F&B", YEL), (" INDUSTRY", WHITE)]], ANTON(100), stroke=7), W / 2, 330, pop(min(1, t / .2)))
            if role == "stage":
                if t < 4 * B:
                    paste(fr, lines_img([[("LIVE", RED), (" FROM THE CITADEL", WHITE)]], ANTON(90), stroke=7), W / 2, 300, pop(min(1, t / .25)))
                elif t < 8 * B:
                    u = t - 4 * B
                    paste(fr, lines_img(["AND THE", [("WINNER", YEL), (" IS…", WHITE)]], ANTON(170), stroke=9), W / 2, 820, pop(min(1, u / .3)))
                else:  # CTA / cliffhanger
                    u = t - 8 * B
                    fr *= .5
                    paste(fr, lines_img(["AND THE", [("WINNER", YEL), (" IS…", WHITE)]], ANTON(170), stroke=9), W / 2, 700)
                    paste(fr, pill("Find out in PART 3", MONT(64, 900), fg=BLACK, bg=YEL), W / 2, 1000, pop(min(1, u / .3)))
                    paste(fr, pill("Follow so you don't miss it  →", MONT(48, 800), fg=WHITE, bg=(200, 30, 40)), W / 2, 1140, pop(min(1, (u - .4) / .3)))
            # global fade
            gg = min(1, T_ / .1, (T - T_) / .3)
            if gg < 1:
                fr *= max(gg, 0)
            enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print(out, f"{T:.1f}s")


if __name__ == "__main__":
    render()
