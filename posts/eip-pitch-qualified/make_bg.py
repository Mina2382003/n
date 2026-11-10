# Erase the partner's text from the reference flyer, keeping paper, frame, X tape, GEF logo and date line.
# Fill = smooth shading interpolated from the clean rows above/below + fine paper grain from a clean strip.
import sys, numpy as np
from PIL import Image, ImageFilter
src = Image.open(sys.argv[1]).convert('RGB'); a = np.asarray(src).astype(float)
H, W, _ = a.shape
X0, X1, y0, y1 = 50, 1152, 118, 776
blur = lambda arr, r: np.asarray(Image.fromarray(arr.clip(0, 255).astype('uint8')).filter(ImageFilter.GaussianBlur(r))).astype(float)
top = blur(a[y0 - 12:y0, X0:X1], 6).mean(0); bot = blur(a[y1:y1 + 12, X0:X1], 6).mean(0)
t = np.linspace(0, 1, y1 - y0)[:, None, None]
shade = top[None] * (1 - t) + bot[None] * t
band = a[1325:1420, X0:X1]; grain = band - blur(band, 8)
rows, h, n = [], band.shape[0], y1 - y0
reps = grain
fill = shade + np.concatenate([reps] * (n // reps.shape[0] + 1))[:n]
out = a.copy(); patch = a.copy(); patch[y0:y1, X0:X1] = fill
mask = np.zeros((H, W)); mask[y0 + 8:y1 - 8, X0 + 14:X1 - 14] = 1
mask = blur(mask * 255, 6) / 255.0
out = out * (1 - mask[..., None]) + patch * mask[..., None]
Image.fromarray(out.clip(0, 255).astype('uint8')).save(sys.argv[2], quality=95)
