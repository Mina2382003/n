"""Calming the Storm - turns the 9 still scenes into one continuous animated short.

No titles, zooms-for-show or slide transitions: every shot is the still brought to life
(depth-based 3D camera, moving water, rocking boat, breathing characters, rain, lightning)
and each shot dissolves into the next while both are still moving.

usage: python3 render.py [preview]   ->  calming_the_storm.mp4 (or preview.mp4 at half res)
"""
import os, sys, subprocess, math
import numpy as np
from PIL import Image, ImageFilter
from multiprocessing import Pool
import rigs

HERE = os.path.dirname(os.path.abspath(__file__))
PREVIEW = len(sys.argv) > 1 and sys.argv[1] == "preview"
W, H = (640, 360) if PREVIEW else (1280, 720)
FPS = 24
XF = 0.9  # dissolve length (s)

# per scene: duration, camera and life settings
#  z0/z1  zoom at start/end        c0/c1  view centre (fraction of frame) at start/end
#  par    parallax travel (px @1280, near-vs-far)  dz  extra zoom on near layers (dolly feel)
#  sea    water treatment: None | "calm" | "storm"      horizon  water starts below this (fraction)
#  boat   rocking amplitude (deg)  rain  0..1 (start, end)   flashes  lightning times (s, local)
SCENES = [
    dict(d=3.8, z0=1.10, z1=1.17, c0=(.50, .50), c1=(.53, .47), par=(-26, -4), dz=.06,  # kids on the beach
         sea="calm", horizon=.30, dmax=.42, boat=0, rain=(0, 0), flashes=[]),
    dict(d=3.8, z0=1.12, z1=1.20, c0=(.47, .50), c1=(.43, .44), par=(-22, -6), dz=.07,  # teaching the crowd
         sea="calm", horizon=.28, dmax=.35, boat=0, rain=(0, 0), flashes=[]),
    dict(d=3.8, z0=1.13, z1=1.13, c0=(.44, .48), c1=(.55, .48), par=(-40, 0), dz=.03,   # pointing to the boat
         sea="calm", horizon=.35, dmax=.40, boat=0, rain=(0, 0), flashes=[]),
    dict(d=3.8, z0=1.18, z1=1.12, c0=(.52, .52), c1=(.48, .50), par=(30, 0), dz=-.04,  # setting sail
         sea="calm", horizon=.36, dmax=.50, boat=.7, rain=(0, 0), flashes=[]),
    dict(d=3.8, z0=1.11, z1=1.20, c0=(.50, .50), c1=(.40, .53), par=(-20, -4), dz=.07,  # Jesus asleep, calm sea
         sea="calm", horizon=.10, dmax=.32, boat=.6, rain=(0, .15), flashes=[]),
    dict(d=7.0, z0=1.16, z1=1.24, c0=(.50, .50), c1=(.46, .50), par=(-24, -8), dz=.06,  # the storm hits
         sea="storm", horizon=0, dmax=.55, boat=2.4, rain=(.6, 1), flashes=[.15, 2.4, 4.6, 6.2]),
    dict(d=3.8, z0=1.14, z1=1.22, c0=(.47, .50), c1=(.36, .55), par=(-18, -6), dz=.07,  # "Master, wake up!"
         sea="storm", horizon=0, dmax=.40, boat=1.8, rain=(1, 1), flashes=[1.9]),
    dict(d=3.6, z0=1.12, z1=1.20, c0=(.50, .55), c1=(.52, .46), par=(-14, 16), dz=.08,  # "Peace, be still"
         sea="storm", horizon=0, dmax=.40, boat=1.4, rain=(1, 0), flashes=[.25]),
    dict(d=5.6, z0=1.22, z1=1.10, c0=(.50, .46), c1=(.50, .50), par=(16, 8), dz=-.06,  # calm at sunset
         sea="calm", horizon=.40, dmax=.42, boat=.5, rain=(0, 0), flashes=[]),
]
STARTS = np.concatenate([[0], np.cumsum([s["d"] - XF for s in SCENES])[:-1]])
TOTAL = STARTS[-1] + SCENES[-1]["d"]
NFRAMES = int(round(TOTAL * FPS))

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
U, V = xx / W, yy / H
K = W / 1280.0  # pixel scale vs 1280 design


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def load_scene(i):
    sc = SCENES[i]
    im = Image.open(f"{HERE}/stills/raw{i+1}.png").convert("RGB")
    im = im.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 40, 2))
    img = np.asarray(im).astype(np.float32) / 255
    d = Image.open(f"{HERE}/stills/depth{i+1}.png").convert("L").resize((W, H), Image.BICUBIC)
    D = np.asarray(d.filter(ImageFilter.GaussianBlur(3 * K))).astype(np.float32) / 255
    # water mask: blue/teal hues (and storm foam) below the horizon, away from the near layers
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    mx, mn = img.max(2), img.min(2)
    sat = (mx - mn) / (mx + 1e-4)
    blue = (b >= r + .06) & (b >= g - .12) & (sat > .18)
    if sc["sea"] == "storm":
        blue |= (mn > .7) & (b >= r)  # foam / spray
    m = blue & (V > sc["horizon"]) & (D < sc["dmax"]) if sc["sea"] else np.zeros_like(blue)
    M = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4 * K))).astype(np.float32) / 255
    near = smoothstep(.42, .70, D) * (1 - M)  # people / boat
    boatw = smoothstep(.28, .55, D)
    glint = smoothstep(.72, .95, mx) * M  # bright crests that sparkle
    rigs.prepare(i, img, K)
    return dict(img=img, D=D, M=M, near=near, boatw=boatw, glint=glint)


def sample(img, sx, sy):
    sx = np.clip(sx, 0, W - 1.001)
    sy = np.clip(sy, 0, H - 1.001)
    x0, y0 = sx.astype(np.int32), sy.astype(np.int32)
    fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def ease(u):
    return .8 * u + .2 * (u * u * (3 - 2 * u))


def flash_level(sc, t):
    e = 0.0
    for ft in sc["flashes"]:
        dt = t - ft
        if 0 <= dt < .7:
            e = max(e, math.exp(-dt * 9) + .6 * math.exp(-max(dt - .16, 0) * 12) * (dt > .16))
    return min(e, 1.3)


RAIN = None
GLIT = None


def glitter_layers():
    rng = np.random.default_rng(3)
    out = []
    for k in range(2):
        n = rng.random((H // 3, W // 10)).astype(np.float32)
        out.append(np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)).astype(np.float32) / 255)
    return out


def rain_layers():
    rng = np.random.default_rng(7)
    layers = []
    for n, ln, alpha, wid in ((900, 34, .30, 1), (260, 70, .45, 2)):
        im = Image.new("L", (W, H * 2), 0)
        from PIL import ImageDraw
        dr = ImageDraw.Draw(im)
        for _ in range(n):
            x, y = rng.uniform(-60, W), rng.uniform(0, H * 2)
            L = ln * K * rng.uniform(.6, 1.2)
            dr.line([(x, y), (x + L * .25, y + L)], fill=int(255 * alpha * rng.uniform(.5, 1)), width=max(1, int(wid * K)))
        layers.append(np.asarray(im.filter(ImageFilter.GaussianBlur(.6 * K))).astype(np.float32) / 255)
    return layers


def render_scene(i, S, t):
    sc = SCENES[i]
    u = ease(np.clip(t / sc["d"], 0, 1))
    z = sc["z0"] + (sc["z1"] - sc["z0"]) * u
    cx = sc["c0"][0] + (sc["c1"][0] - sc["c0"][0]) * u
    cy = sc["c0"][1] + (sc["c1"][1] - sc["c0"][1]) * u
    D = S["D"]
    dd = D - .5
    zeff = z * (1 + sc["dz"] * u * dd)
    sx = (cx + (U - .5) / zeff) * W - sc["par"][0] * K * (u - .5) * dd
    sy = (cy + (V - .5) / zeff) * H - sc["par"][1] * K * (u - .5) * dd

    storm = sc["sea"] == "storm"
    # handheld feel; stronger in the storm
    hs = (3.5 if storm else .8) * K
    sx += hs * (math.sin(t * 1.3 + i) + .5 * math.sin(t * 3.1 + 2 * i))
    sy += hs * (math.sin(t * 1.1 + 3 * i) + .5 * math.sin(t * 2.7 + i))

    # boat rocking: near layers rotate/bob against the sea
    if sc["boat"]:
        per = 2.4 if storm else 4.2
        th = math.radians(sc["boat"]) * math.sin(2 * math.pi * t / per + i)
        bob = (7 if storm else 2.2) * K * math.sin(2 * math.pi * t / per + i + 1.2)
        px, py = W * .5, H * .95
        rx = (sx - px) * math.cos(th) - (sy - py) * math.sin(th) + px
        ry = (sx - px) * math.sin(th) + (sy - py) * math.cos(th) + py + bob
        bw = S["boatw"]
        sx, sy = sx + bw * (rx - sx), sy + bw * (ry - sy)

    # breathing / idle sway of the characters, each body on its own phase
    nr = S["near"]
    ph = xx * .011
    br = 1.3 * K * (2.2 if storm else 1)
    sy += nr * br * np.sin(2 * math.pi * t / 3.3 + ph) * (1 - V)
    sx += nr * .9 * K * np.sin(2 * math.pi * t / 4.7 + ph * 1.3)

    # water: travelling swells, shrinking toward the horizon
    M = S["M"]
    if sc["sea"]:
        hz = sc["horizon"]
        persp = .25 + .75 * np.clip((V - hz) / (1 - hz + 1e-3), 0, 1)
        if storm:
            A, sp, f = 8.0 * K, 2.6, .55
        else:
            A, sp, f = 2.6 * K, 1.6, 1.0
        x1, y1 = xx / K, yy / K
        wy = (np.sin(.030 * f * x1 + .19 * f * y1 / persp - sp * t)
              + .55 * np.sin(-.051 * f * x1 + .11 * f * y1 / persp - 1.4 * sp * t + 1.7))
        wx = .6 * np.sin(.14 * f * y1 / persp + .012 * x1 - 1.2 * sp * t)
        if storm:  # big rolling waves
            wy += 1.6 * np.sin(.009 * x1 - .012 * y1 - 1.1 * t)
            wx += 1.8 * np.sin(.007 * x1 + .010 * y1 - 0.9 * t + 1)
        sx += M * A * persp * wx
        sy += M * A * persp * wy

    sx, sy, shade, ovr = rigs.apply(i, sx, sy, t, sc["d"], K, S["img"])
    out = sample(S["img"], sx, sy)
    if shade is not None:
        a = ovr[0][..., None]
        out = (out * (1 - a) + ovr[1]) * shade[..., None]
    gl = sample(S["glint"][..., None], sx, sy)[..., 0]

    # sparkle on crests
    if sc["sea"]:
        a = np.roll(GLIT[0], (int(t * 9 * K), int(t * 40 * K)), axis=(0, 1))[:H, :W]
        b = np.roll(GLIT[1], (int(-t * 6 * K), int(-t * 55 * K)), axis=(0, 1))[:H, :W]
        tw = np.clip((a + b - 1.25) * 4, 0, 1)
        out += (gl * tw * (.45 if not storm else .25))[..., None]

    # rain
    r0, r1 = sc["rain"]
    rain = r0 + (r1 - r0) * u
    if rain > .01:
        for k, lay in enumerate(RAIN):
            spd = (900 if k else 600) * K
            off = int(t * spd) % H
            drift = int(t * spd * .25) % W
            r = np.roll(lay[H - off:2 * H - off], drift, axis=1)
            out += (rain * r * (.55 if k else .4))[..., None] * np.array([.85, .9, 1.0])
        out *= 1 - .10 * rain  # darker under the clouds

    # lightning
    fl = flash_level(sc, t)
    if fl > 0:
        out = out * (1 + .9 * fl) + fl * .18 * np.array([.75, .85, 1.0])
    return out


def bloom(img, amt):
    hi = np.clip(img - .62, 0, 1)
    small = Image.fromarray((np.clip(hi, 0, 1) * 255).astype(np.uint8)).resize((W // 8, H // 8), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BILINEAR)
    return img + amt * np.asarray(small).astype(np.float32) / 255


VIG = None


def frame(n, cache):
    T = n / FPS
    acc, wsum = None, 0
    active = [i for i in range(len(SCENES)) if STARTS[i] - 1e-6 <= T < STARTS[i] + SCENES[i]["d"]]
    layers = []
    for i in active:
        t = T - STARTS[i]
        a = 1.0
        if i > 0 and t < XF:
            a = smoothstep(0, 1, t / XF)
        layers.append((i, t, a))
    img = None
    for i, t, a in layers:
        if i not in cache:
            cache[i] = load_scene(i)
        f = render_scene(i, cache[i], t)
        img = f if img is None else img * (1 - a) + f * a

    # the storm breaking: warm light washes in over the last dissolve
    s9 = STARTS[8]
    if s9 <= T < s9 + XF:
        k = math.sin(math.pi * (T - s9) / XF)
        img = img + .22 * k * np.array([1.0, .82, .55])

    img = bloom(img, .35)
    # grade: gentle contrast, warm highlights, vignette, fine grain
    img = np.clip(img, 0, 1)
    img = img + .06 * (img - .5) * (1 - np.abs(img - .5) * 2)
    img *= VIG[..., None]
    rng = np.random.default_rng(n)
    img += rng.normal(0, .012, (H, W, 1)).astype(np.float32)
    fade = min(1, T / .8, (TOTAL - T) / 1.2)
    img *= max(fade, 0)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


def init():
    global RAIN, VIG, GLIT
    RAIN = rain_layers()
    GLIT = glitter_layers()
    r = np.sqrt(((U - .5) * 1.1) ** 2 + (V - .5) ** 2)
    VIG = 1 - .32 * smoothstep(.35, .85, r)


def chunk(args):
    k, a, b, path = args
    init()
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    cache = {}
    for n in range(a, b):
        p.stdin.write(frame(n, cache).tobytes())
    p.stdin.close()
    p.wait()
    return path


if __name__ == "__main__":
    tmp = os.environ.get("TMPDIR_RENDER", f"{HERE}/.render")
    os.makedirs(tmp, exist_ok=True)
    nproc = os.cpu_count() or 4
    bounds = np.linspace(0, NFRAMES, nproc * 2 + 1).astype(int)
    jobs = [(k, bounds[k], bounds[k + 1], f"{tmp}/part{k:02d}.mp4") for k in range(len(bounds) - 1)]
    with Pool(nproc) as pool:
        parts = pool.map(chunk, jobs)
    with open(f"{tmp}/list.txt", "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    video = f"{tmp}/video.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy", video], check=True)
    out = f"{HERE}/{'preview' if PREVIEW else 'calming_the_storm'}.mp4"
    audio = f"{HERE}/soundtrack.wav"
    if os.path.exists(audio):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5", "-ar", "44100", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", out], check=True)
    else:
        os.replace(video, out)
    print(out, f"{TOTAL:.1f}s", NFRAMES, "frames")
