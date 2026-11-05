"""Génère les bannières SVG (sombre, clair) et la source SVG de l'aperçu social.

Toutes les valeurs viennent de `jetons.charger()`. Police Sora embarquée en base64. Pictogramme aux couleurs de
`jetons.PICTOGRAMME` ; filet or (`accent`) sous le titre (B5). Aperçu social selon la règle A11 : 1280 × 640,
zone utile centrée dans des marges sûres de 80 px, titre d'au moins 64 px, aucun texte sous 28 px.
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
# Règle A11 de l'aperçu social
APERCU = (1280, 640)
MARGE_APERCU = 80
TITRE_APERCU = 72  # px, au moins 64
TEXTE_APERCU = 32  # px, aucun texte sous 28


def _police(j: dict) -> str:
    b64 = base64.b64encode(POLICE.read_bytes()).decode()
    return (f"@font-face {{ font-family: 'Sora'; font-weight: 600; "
            f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}")


def picto(theme: str) -> str:
    """Pictogramme (géométrie de dist/pictogramme.svg, viewBox 32) aux couleurs de `jetons.PICTOGRAMME`."""
    j = jetons.charger()
    r = {k: j[theme][v] for k, v in jetons.PICTOGRAMME[theme].items()}
    return (f'    <rect width="32" height="32" rx="8" fill="{r["tuile"]}"/>\n'
            f'    <path d="M9 10h14M9 16h9M9 22h14" fill="none" stroke="{r["barres"]}" stroke-width="3" stroke-linecap="round"/>\n'
            f'    <circle cx="23" cy="16" r="2.5" fill="{r["point"]}"/>')


def apercu(theme: str = "sombre") -> str:
    """Aperçu social (A11) : bloc centré, pictogramme, titre, filet or, sous-titre, dans les marges sûres."""
    j = jetons.charger()
    c = j[theme]
    largeur, hauteur = APERCU
    pile, gr = j["police"]["titres"]["pile"], j["police"]["titres"]["graisse"]
    cote = 128
    x0, y0 = (largeur - cote) // 2, 144  # bloc de 144 à 486 px : centré verticalement, dans les marges de 80 px
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}" role="img" aria-label="{NOM}">
  <style>{_police(j)}
  .t {{ font-family: {pile}; font-weight: {gr}; }}</style>
  <rect width="{largeur}" height="{hauteur}" fill="{c['fond']}"/>
  <rect x="1" y="1" width="{largeur - 2}" height="{hauteur - 2}" rx="{j['rayon']['grand']}" fill="{c['surface']}"
        stroke="{c['trait']}" stroke-width="{j['trait']}"/>
  <g transform="translate({x0} {y0}) scale({cote // 32})">
{picto(theme)}
  </g>
  <text class="t" x="{largeur // 2}" y="{y0 + cote + 104}" font-size="{TITRE_APERCU}" text-anchor="middle" fill="{c['texte']}">{NOM}</text>
  <rect class="filet" x="{largeur // 2 - 64}" y="{y0 + cote + 132}" width="128" height="6" rx="3" fill="{c['accent']}"/>
  <text class="t" x="{largeur // 2}" y="{y0 + cote + 204}" font-size="{TEXTE_APERCU}" text-anchor="middle" fill="{c['texte-attenue']}">{SOUS_TITRE}</text>
</svg>
"""


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
{picto(theme)}
  </g>
  <text class="t" x="{tx}" y="{hauteur // 2 - 4}" font-size="{j['taille']['titre-1'] + 8}" fill="{c['texte']}">{NOM}</text>
  <text class="t" x="{tx}" y="{hauteur // 2 + 44}" font-size="{j['taille']['grand'] + 6}" fill="{c['texte-attenue']}">{SOUS_TITRE}</text>
  <rect class="filet" x="{tx}" y="{hauteur // 2 + 72}" width="96" height="4" rx="2" fill="{c['accent']}"/>
</svg>
"""


def main() -> None:
    for theme in ("sombre", "clair"):
        (ICI / f"banniere-{theme}.svg").write_text(svg(theme, 1280, 320), encoding="utf-8")
    (ICI / "apercu-social.svg").write_text(apercu("sombre"), encoding="utf-8")
    print("bannières générées")


if __name__ == "__main__":
    main()
