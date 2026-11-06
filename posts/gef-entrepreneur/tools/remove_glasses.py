# Remove the sunglasses resting on the hair from the cutout.
# Everything above a smooth crown arc becomes transparent; glasses pixels left over the hair
# (lighter than the near-black hair) plus a thin band under the arc are inpainted with hair.
import sys, numpy as np, cv2
from PIL import Image
im = np.array(Image.open(sys.argv[1]).convert('RGBA'))
H, W = im.shape[:2]
X0, X1, Y0, Y1 = 925, 1112, 585, 675                     # glasses box (source pixels)
xs = np.array([938, 960, 1020, 1080, 1100]); ys = np.array([668, 640, 624, 640, 668])
arc = np.polyval(np.polyfit(xs, ys, 2), np.arange(W))     # crown line
yy, xx = np.mgrid[0:H, 0:W]
inbox = (xx >= X0) & (xx < X1) & (yy >= Y0) & (yy < Y1)
above = inbox & (yy < arc[xx])
lum = im[..., :3].astype(int).mean(-1)
im[above, :3] = (25, 20, 20); im[above, 3] = 0
glass = inbox & ~above & (((lum >= 50) & (yy < 660)) | (yy < arc[xx] + 10)) & (im[..., 3] > 0)
glass = cv2.dilate(glass.astype(np.uint8), np.ones((3, 3), np.uint8)) & inbox
bgr = cv2.cvtColor(np.ascontiguousarray(im[..., :3]), cv2.COLOR_RGB2BGR)
fill = cv2.inpaint(bgr, glass.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
# add a little hair grain so the fill is not flat
noise = np.random.default_rng(1).normal(0, 7, fill.shape[:2])[..., None]
fill = np.where(glass[..., None] > 0, (fill + noise).clip(0, 255), fill).astype(np.uint8)
im[..., :3] = cv2.cvtColor(fill, cv2.COLOR_BGR2RGB)
# feathered crown edge
edge = np.clip((yy - arc[xx]) / 3.0, 0, 1)
im[..., 3] = np.where(inbox, im[..., 3] * edge, im[..., 3]).astype(np.uint8)
Image.fromarray(im).save(sys.argv[2])
