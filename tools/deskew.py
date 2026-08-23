#!/usr/bin/env python3
"""Redresse une photo : détecte l'inclinaison des lignes droites (horizontales et
verticales, modulo 90°) et fait tourner l'image de l'angle opposé, puis recadre
le plus grand rectangle inscrit de même proportion."""
import math, sys
import numpy as np
from PIL import Image, ImageOps

LIMITE = 8.0   # degrés : au-delà, on considère que c'est un cadrage voulu

def angle_dominant(im, limite=LIMITE):
    g = np.asarray(ImageOps.grayscale(im.copy()).resize(
        (900, max(1, round(900 * im.height / im.width))), Image.LANCZOS), float)
    gx = np.zeros_like(g); gy = np.zeros_like(g)
    gx[:, 1:-1] = g[:, 2:] - g[:, :-2]
    gy[1:-1, :] = g[2:, :] - g[:-2, :]
    mag = np.hypot(gx, gy)
    seuil = np.percentile(mag, 92)
    m = mag > seuil
    if m.sum() < 500:
        return 0.0
    # direction du contour = gradient tourné de 90°, repliée modulo 90°
    theta = np.degrees(np.arctan2(gy[m], gx[m])) - 90.0
    theta = (theta + 45.0) % 90.0 - 45.0
    poids = mag[m]
    garde = np.abs(theta) <= limite
    if garde.sum() < 200:
        return 0.0
    hist, bords = np.histogram(theta[garde], bins=int(limite * 20),
                               range=(-limite, limite), weights=poids[garde])
    # lissage gaussien (sigma ~ 0.25°)
    k = np.exp(-((np.arange(-10, 11) / 5.0) ** 2) / 2); k /= k.sum()
    hist = np.convolve(hist, k, mode="same")
    i = int(hist.argmax())
    # affinage par barycentre local
    a, b = max(0, i - 4), min(len(hist), i + 5)
    centres = (bords[:-1] + bords[1:]) / 2
    return float((hist[a:b] * centres[a:b]).sum() / hist[a:b].sum())

def rect_inscrit(w, h, angle):
    """Plus grand rectangle de proportion w/h inscrit dans le rectangle tourné."""
    a = abs(math.radians(angle))
    if a < 1e-9:
        return w, h
    c, s = math.cos(a), math.sin(a)
    # rectangle de même ratio : facteur d'échelle limitant
    f = min(w, h) / (min(w, h) * c + max(w, h) * s) if False else None
    # résolution directe : on cherche k tel que (k*w, k*h) tourné de -angle tienne
    k = 1.0 / (c + s * max(w / h, h / w)) if False else None
    # formule standard (rectangle inscrit homothétique)
    k = (w * h) / (w * w * s * s + h * h * c * c) ** 0.5 / max(w, h) if False else None
    k = 1.0 / (c + s * (h / w)) if w >= h else 1.0 / (c + s * (w / h))
    k = min(1.0 / (c + s * h / w), 1.0 / (c + s * w / h))
    return int(w * k), int(h * k)

def redresse(chemin, limite=LIMITE):
    im = ImageOps.exif_transpose(Image.open(chemin)).convert("RGB")
    ang = angle_dominant(im, limite)
    if abs(ang) < 0.15:
        return im, 0.0
    tourne = im.rotate(ang, resample=Image.BICUBIC, expand=False)
    nw, nh = rect_inscrit(im.width, im.height, ang)
    x, y = (im.width - nw) // 2, (im.height - nh) // 2
    return tourne.crop((x, y, x + nw, y + nh)), ang

if __name__ == "__main__":
    for c in sys.argv[1:]:
        im, a = redresse(c)
        print(f"{c}: {a:+.2f}°")
