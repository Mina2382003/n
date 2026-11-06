# Replace the top of the phone with the shirt/lapel continued from the rows just above it,
# then crop chest-up so the poster fades out before the hands.
import sys, numpy as np
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('RGBA')).astype(float)
X0, X1, Y0, Y1, REF = 955, 1056, 962, 1075, 958
src = im[REF - 6:REF + 1, :, :].mean(0)                  # averaged reference row
rng = np.random.default_rng(2)
for y in range(Y0, Y1):
    dx = (y - REF) * 0.22                                # V of the shirt narrows going down
    xs = np.clip(np.arange(X0, X1) - dx, 0, im.shape[1] - 1)
    row = np.array([np.interp(xs, np.arange(im.shape[1]), src[:, c]) for c in range(4)]).T
    row[:, :3] += rng.normal(0, 3, (len(xs), 1))
    w = np.clip(np.minimum(np.arange(X0, X1) - X0, X1 - 1 - np.arange(X0, X1)) / 4, 0, 1)[:, None]
    im[y, X0:X1] = row * w + im[y, X0:X1] * (1 - w)
Image.fromarray(im.clip(0, 255).astype(np.uint8)).crop((590, 560, 1390, 1080)).save(sys.argv[2])
