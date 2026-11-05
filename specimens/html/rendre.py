"""Rend le spécimen HTML (Edge headless) : PNG sombre et clair, PDF A4 clair, PDF et PNG en gris.

Usage : uv run --group specimens python specimens/html/rendre.py
Pillow sert à réduire les PNG à 1600 px de large au plus et à recadrer la première page grise.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ICI = Path(__file__).resolve().parent
RENDUS = ICI / "rendus"
EDGE = Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PAGE = (ICI / "specimen.html").as_uri()
LARGEUR = 1200
HAUTEUR_MAX = 6000


def edge(profil: str, *args: str) -> None:
    cmd = [str(EDGE), "--headless=new", "--disable-gpu", "--hide-scrollbars",
           f"--user-data-dir={profil}", "--allow-file-access-from-files",
           "--virtual-time-budget=4000", *args]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def png(profil: str, theme: str) -> None:
    sortie = RENDUS / f"specimen-{theme}.png"
    edge(profil, f"--screenshot={sortie}", f"--window-size={LARGEUR},{HAUTEUR_MAX}",
         f"{PAGE}?theme={theme}")
    img = Image.open(sortie).convert("RGB")
    # Recadre le bas uni : cherche la dernière ligne différente du fond.
    fond = img.getpixel((2, img.height - 1))
    bas = img.height
    while bas > 1 and all(img.getpixel((x, bas - 1)) == fond for x in range(0, img.width, 40)):
        bas -= 1
    img.crop((0, 0, img.width, min(img.height, bas + 48))).save(sortie, optimize=True)


def pdf(profil: str, nom: str, requete: str) -> Path:
    sortie = RENDUS / nom
    edge(profil, f"--print-to-pdf={sortie}", "--no-pdf-header-footer", f"{PAGE}?{requete}")
    return sortie


def main() -> int:
    if not EDGE.exists():
        print(f"Edge introuvable : {EDGE}", file=sys.stderr)
        return 1
    RENDUS.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as profil:
        png(profil, "sombre")
        png(profil, "clair")
        pdf(profil, "specimen-clair.pdf", "theme=clair&nofocus=1")
        pdf(profil, "specimen-gris.pdf", "theme=clair&nofocus=1&gris=1")
        # PNG de la première page en gris : capture à la largeur A4 (794 px) de la même variante.
        sortie = RENDUS / "specimen-gris-page1.png"
        edge(profil, f"--screenshot={sortie}", "--window-size=794,1123",
             f"{PAGE}?theme=clair&nofocus=1&gris=1")
    print("Rendus écrits dans", RENDUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
