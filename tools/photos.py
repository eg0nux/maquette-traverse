#!/usr/bin/env python3
"""Prépare les photos de maquette pour `public/img/`.

Chaîne : redressement (deskew), recadrage, traitement esthétique, puis deux
tailles (1600 px et 800 px). Les cadrages sont exprimés en fractions de l'image
redressée — gauche, haut, droite, bas — pour rester lisibles et rejouables.

    python tools/photos.py            # tout régénérer
    python tools/photos.py 165328     # une seule photo
"""
import io
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
    "IMG_20260903_165454": ("IMG_20260903_165454", (0.00, 0.105, 0.97, 1.00)),
    "IMG_20260903_165430": ("IMG_20260903_165430", (0.00, 0.00, 1.00, 0.84)),
    "IMG_20260903_165517": ("IMG_20260903_165517", (0.12, 0.00, 0.96, 0.95)),
    "IMG_20260903_165544": ("IMG_20260903_165544", (0.03, 0.00, 1.00, 0.88)),
    "IMG_20260903_165408": ("IMG_20260903_165408", (0.00, 0.12, 1.00, 1.00)),
    "IMG_20260903_165347": ("IMG_20260903_165347", (0.05, 0.00, 0.56, 1.00)),
    "IMG_20260903_165354": ("IMG_20260903_165354", (0.02, 0.10, 0.98, 0.97)),
    # Bandeau d'ouverture : la bande, puis la photo entière qu'un clic ouvre.
    # Elle prend le pied du château d'eau et descend jusque dans la cour, devant
    # le pavillon : la pelouse, la maison et ses arbres y tiennent d'un bout à
    # l'autre.
    "maquette-hero": ("IMG_20260903_165328", (0.00, 0.30, 1.00, 0.90)),
    "IMG_20260903_165328": ("IMG_20260903_165328", (0.03, 0.02, 0.95, 1.00)),
}

# Le bandeau n'a pas de vignette ; la photo qu'il ouvre non plus.
LARGEURS = {"maquette-hero": (2000,), "IMG_20260903_165328": (1600,)}
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


# Seuil calibré sur ces photos-là, mesuré par la fonction ci-dessous : au-delà,
# passer à la qualité supérieure ne gagne plus rien que l'œil retrouve, et
# l'image enfle. Les valeurs ne sont pas comparables à celles d'une autre
# implémentation de SSIM.
SSIM_MINIMAL = 0.950
QUALITES = (70, 72, 74, 76, 78, 80, 82, 84, 86)


def ssim(a, b, fenetre=8):
    """Similarité structurelle, en niveaux de gris, sur des fenêtres carrées.
    Une image très détaillée — feuillage, gravier — perd sa matière avant qu'un
    aplat ne bouge : la mesure le voit là où l'écart moyen ne dit rien."""
    x = np.asarray(a.convert("L"), float)
    y = np.asarray(b.convert("L"), float)
    h, w = (s - s % fenetre for s in x.shape)
    x, y = x[:h, :w], y[:h, :w]
    forme = (h // fenetre, fenetre, w // fenetre, fenetre)
    bloc = lambda m: m.reshape(forme).mean(axis=(1, 3))
    mx, my = bloc(x), bloc(y)
    vx, vy = bloc(x * x) - mx * mx, bloc(y * y) - my * my
    vxy = bloc(x * y) - mx * my
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    carte = ((2 * mx * my + c1) * (2 * vxy + c2)) / ((mx * mx + my * my + c1) * (vx + vy + c2))
    return float(carte.mean())


def qualite_juste(im):
    """La plus basse qualité JPEG que cette image-là supporte sans qu'on le voie.
    Un ciel uni descend bas, une pelouse d'arbres découpés beaucoup moins ; un
    réglage unique aurait donc surpayé les unes et abîmé les autres."""
    for q in QUALITES:
        tampon = io.BytesIO()
        im.save(tampon, "JPEG", quality=q, optimize=True, progressive=True)
        tampon.seek(0)
        if ssim(im, Image.open(tampon)) >= SSIM_MINIMAL:
            return q, tampon.getvalue()
    return QUALITES[-1], None


def enregistre(im, dest, largeur):
    if im.width > largeur:
        im = im.resize((largeur, round(im.height * largeur / im.width)), Image.LANCZOS)
    q, octets = qualite_juste(im)
    if octets is None:
        im.save(dest, "JPEG", quality=q, optimize=True, progressive=True)
    else:
        dest.write_bytes(octets)
    return q


def prepare(nom, source, cadre):
    im, angle = redresse(SRC / f"{source}.jpg")
    w, h = im.size
    l, t, r, b = cadre
    im = im.crop((round(l * w), round(t * h), round(r * w), round(b * h)))
    im = sublime(im)
    qualites = []
    for largeur in LARGEURS.get(nom, DEFAUT):
        suffixe = "" if largeur == max(LARGEURS.get(nom, DEFAUT)) else "@small"
        qualites.append(enregistre(im.copy(), IMG / f"{nom}{suffixe}.jpg", largeur))
    print(f"{nom}  {angle:+.2f}°  {im.width}×{im.height}  q{'/'.join(map(str, qualites))}",
          flush=True)


if __name__ == "__main__":
    choix = sys.argv[1:]
    for nom, (source, cadre) in PHOTOS.items():
        if choix and not any(c in nom for c in choix):
            continue
        prepare(nom, source, cadre)
