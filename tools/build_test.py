#!/usr/bin/env python3
"""Génère la version de test : photos redressées (depuis les originaux pleine
résolution) en 1600 px et 800 px, plus une copie de la page."""
import os, shutil, sys
from pathlib import Path
from PIL import Image, ImageOps
sys.path.insert(0, str(Path(__file__).parent))
from deskew import redresse

SRC = Path.home() / Path("pCloudDrive/Atelier Partagé/1-AP-Généralités/"
                         "B-Nos Photos et Video/Maquette La Traverse")
RACINE = Path(__file__).resolve().parent.parent
PUB, TEST = RACINE / "public", RACINE / "test"
IMG = TEST / "img"
IMG.mkdir(parents=True, exist_ok=True)

def enregistre(im, dest, largeur):
    if im.width > largeur:
        im = im.resize((largeur, round(im.height * largeur / im.width)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=86, optimize=True, progressive=True)

angles = {}
for src in sorted(PUB.glob("img/IMG_*.jpg")):
    if "@small" in src.name:
        continue
    orig = SRC / src.name
    im, ang = redresse(orig if orig.exists() else src)
    angles[src.stem] = ang
    enregistre(im.copy(), IMG / src.name, 1600)
    enregistre(im, IMG / f"{src.stem}@small.jpg", 800)
    print(f"{src.stem}  {ang:+.2f}°", flush=True)

# hero : redressé depuis l'original, recadré comme la version publiée (2000x700)
hero_src = SRC / "IMG_20260821_172843.jpg"
im, ang = redresse(hero_src)
angles["maquette-hero"] = ang
ref = Image.open(PUB / "img/maquette-hero.jpg")
ratio = ref.width / ref.height
h = int(im.width / ratio)
if h <= im.height:
    haut = int((im.height - h) * 0.42)
    im = im.crop((0, haut, im.width, haut + h))
enregistre(im, IMG / "maquette-hero.jpg", ref.width)
print(f"maquette-hero  {ang:+.2f}°", flush=True)

for logo in PUB.glob("img/logo-*.png"):
    shutil.copy2(logo, IMG / logo.name)

import json
(TEST / "angles.json").write_text(json.dumps(angles, indent=1))
shutil.copy2(PUB / "index.html", TEST / "index.html")
shutil.copy2(PUB / "favicon.png", TEST / "favicon.png")
print("OK")
