#!/usr/bin/env python3
"""Prépare les photos de maquette pour `public/img/`.

Chaîne : redressement (deskew), recadrage, traitement esthétique, puis deux
tailles (1600 px et 800 px). Les cadrages sont exprimés en fractions de l'image
redressée — gauche, haut, droite, bas — pour rester lisibles et rejouables.

    python tools/photos.py            # tout régénérer
    python tools/photos.py 165328     # une seule photo
"""
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from deskew import redresse

DOSSIER = ("Atelier Partagé/1-AP-Généralités/B-Nos Photos et Video/"
           "Maquette La Traverse/Dernières photos maquette")
# pCloud se monte tantôt sur P:, tantôt dans le dossier personnel.
SRC = next((r / DOSSIER for r in (Path("P:/"), Path.home() / "pCloudDrive")
            if (r / DOSSIER).is_dir()), Path("P:/") / DOSSIER)
IMG = Path(__file__).resolve().parent.parent / "public" / "img"

# nom publié -> (fichier source, cadrage en fractions de l'image redressée)
PHOTOS = {
    # Vues d'ensemble
    "IMG_20260903_165418": ("IMG_20260903_165418", (0.02, 0.175, 0.955, 0.96)),
    "IMG_20260903_165253": ("IMG_20260903_165253", (0.185, 0.245, 0.855, 0.558)),
    "IMG_20260903_165240": ("IMG_20260903_165240", (0.145, 0.00, 0.825, 0.94)),
    "IMG_20260903_165308": ("IMG_20260903_165308", (0.00, 0.02, 0.97, 0.93)),
    "IMG_20260903_165627": ("IMG_20260903_165627", (0.02, 0.00, 0.98, 0.47)),
    # Détails
    "IMG_20260903_165328": ("IMG_20260903_165328", (0.03, 0.02, 0.95, 1.00)),
    "IMG_20260903_165430": ("IMG_20260903_165430", (0.00, 0.00, 1.00, 0.84)),
    "IMG_20260903_165517": ("IMG_20260903_165517", (0.12, 0.00, 0.96, 0.95)),
    "IMG_20260903_165544": ("IMG_20260903_165544", (0.03, 0.00, 1.00, 0.88)),
    "IMG_20260903_165408": ("IMG_20260903_165408", (0.00, 0.12, 1.00, 1.00)),
    "IMG_20260903_165347": ("IMG_20260903_165347", (0.05, 0.00, 0.56, 1.00)),
    "IMG_20260903_165354": ("IMG_20260903_165354", (0.02, 0.10, 0.98, 0.97)),
    # Bandeau d'ouverture
    "maquette-hero": ("IMG_20260903_165454", (0.00, 0.10, 1.00, 0.567)),
}

LARGEURS = {"maquette-hero": (2000,)}   # le bandeau n'a pas de version @small
DEFAUT = (1600, 800)


def niveaux(im, coupe=0.25, force=0.7):
    """Étire les niveaux par canal : noir et blanc ne se déplacent que d'une
    fraction (force) de l'écart mesuré, pour ne pas boucher les ombres."""
    a = np.asarray(im, float)
    out = np.empty_like(a)
    for c in range(3):
        ch = a[..., c]
        lo, hi = np.percentile(ch, coupe), np.percentile(ch, 100 - coupe)
        lo, hi = lo * force, 255 - (255 - hi) * force
        out[..., c] = ch if hi - lo < 1 else np.clip((ch - lo) * 255.0 / (hi - lo), 0, 255)
    return Image.fromarray(out.astype("uint8"))


def courbe_s(im, k=0.09):
    """Contraste doux : courbe en S centrée sur le gris moyen."""
    x = np.arange(256) / 255.0
    table = np.clip((x - k * np.sin(2 * np.pi * x) / (2 * np.pi)) * 255, 0, 255)
    return im.point(list(table.astype("uint8")) * 3)


def saturation_manquante(im, cible=30.0, gain=0.16):
    """Ravive d'autant plus que la photo est terne ; laisse tranquilles les
    verts de la pelouse, déjà vifs."""
    a = np.asarray(im.resize((200, 150)), float)
    manque = max(0.0, min(1.0, (cible - (a.max(2) - a.min(2)).mean()) / cible))
    return 1.0 + gain * manque


def sublime(im):
    """Les prises de vue en atelier sont plates : néons, blancs voilés."""
    im = courbe_s(niveaux(im))
    im = ImageEnhance.Color(im).enhance(saturation_manquante(im))
    return im.filter(ImageFilter.UnsharpMask(radius=1.1, percent=50, threshold=3))


def qualite(largeur):
    """Les vignettes s'affichent sous 400 px de côté : 80 y est indiscernable
    de 86. Le bandeau, lui, se charge d'emblée — il descend à 82 pour ne pas
    peser sur le premier affichage."""
    if largeur <= 800:
        return 80
    return 82 if largeur >= 2000 else 86


def enregistre(im, dest, largeur):
    if im.width > largeur:
        im = im.resize((largeur, round(im.height * largeur / im.width)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=qualite(largeur), optimize=True, progressive=True)


def prepare(nom, source, cadre):
    im, angle = redresse(SRC / f"{source}.jpg")
    w, h = im.size
    l, t, r, b = cadre
    im = im.crop((round(l * w), round(t * h), round(r * w), round(b * h)))
    im = sublime(im)
    for largeur in LARGEURS.get(nom, DEFAUT):
        suffixe = "" if largeur == max(LARGEURS.get(nom, DEFAUT)) else "@small"
        enregistre(im.copy(), IMG / f"{nom}{suffixe}.jpg", largeur)
    print(f"{nom}  {angle:+.2f}°  {im.width}×{im.height}", flush=True)


if __name__ == "__main__":
    choix = sys.argv[1:]
    for nom, (source, cadre) in PHOTOS.items():
        if choix and not any(c in nom for c in choix):
            continue
        prepare(nom, source, cadre)
