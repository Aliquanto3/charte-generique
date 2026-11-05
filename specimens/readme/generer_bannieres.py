"""Génère les bannières SVG (sombre, clair) et la source SVG de l'aperçu social.

Toutes les valeurs viennent de `jetons.charger()`. Police Sora embarquée en base64.
Usage : uv run --no-project python -I specimens/readme/generer_bannieres.py
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "skills" / "charte" / "outils"))
import jetons  # noqa: E402

ICI = Path(__file__).resolve().parent
POLICE = RACINE / "skills" / "charte" / "polices" / "sora-latin-600-normal.woff2"
NOM = "Projet témoin"
SOUS_TITRE = "Dépôt type à la charte générique"


def _police(j: dict) -> str:
    b64 = base64.b64encode(POLICE.read_bytes()).decode()
    return (f"@font-face {{ font-family: 'Sora'; font-weight: 600; "
            f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}")


def svg(theme: str, largeur: int, hauteur: int, marge: int = 0) -> str:
    j = jetons.charger()
    c = j[theme]
    pile = j["police"]["titres"]["pile"]
    gr = j["police"]["titres"]["graisse"]
    r = j["rayon"]["grand"]
    # pictogramme (géométrie de dist/pictogramme.svg, viewBox 32) agrandi
    ech = 6
    taille = 32 * ech
    px_ = max(marge, 64)
    py = (hauteur - taille) // 2
    tx = px_ + taille + 48
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}" role="img" aria-label="{NOM}">
  <style>{_police(j)}
  .t {{ font-family: {pile}; font-weight: {gr}; }}</style>
  <rect width="{largeur}" height="{hauteur}" fill="{c['fond']}"/>
  <rect x="1" y="1" width="{largeur - 2}" height="{hauteur - 2}" rx="{r}" fill="{c['surface']}" stroke="{c['trait']}" stroke-width="{j['trait']}"/>
  <g transform="translate({px_} {py}) scale({ech})">
    <rect width="32" height="32" rx="8" fill="{c['primaire']}"/>
    <path d="M9 10h14M9 16h9M9 22h14" fill="none" stroke="{c['sur-primaire']}" stroke-width="3" stroke-linecap="round"/>
    <circle cx="23" cy="16" r="2.5" fill="{c['accent']}"/>
  </g>
  <text class="t" x="{tx}" y="{hauteur // 2 - 4}" font-size="{j['taille']['titre-1'] + 8}" fill="{c['texte']}">{NOM}</text>
  <text class="t" x="{tx}" y="{hauteur // 2 + 44}" font-size="{j['taille']['grand'] + 6}" fill="{c['texte-attenue']}">{SOUS_TITRE}</text>
  <rect x="{tx}" y="{hauteur // 2 + 72}" width="96" height="4" rx="2" fill="{c['accent']}"/>
</svg>
"""


def main() -> None:
    for theme in ("sombre", "clair"):
        (ICI / f"banniere-{theme}.svg").write_text(svg(theme, 1280, 320), encoding="utf-8")
    # source de l'aperçu social : 1280x640, texte dans la zone sûre (40 px)
    (ICI / "apercu-social.svg").write_text(svg("sombre", 1280, 640, marge=120), encoding="utf-8")
    print("bannières générées")


if __name__ == "__main__":
    main()
