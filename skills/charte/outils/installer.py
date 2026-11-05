"""Installe la charte dans un dépôt cible : fichiers de `dist/` et polices utiles, avec les licences OFL.

Usage : uv run --no-project python -I installer.py --cible <dépôt> --supports web,streamlit,python,office,readme
        [--dossier static/charte] [--forcer]

N'écrase rien sans `--forcer`. Affiche les fichiers posés et l'extrait à coller dans le `CLAUDE.md` du dépôt cible.
Bibliothèque standard seulement.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
DIST, POLICES = RACINE / "dist", RACINE / "polices"

WOFF2 = ["sora-latin-600-normal.woff2", "atkinson-hyperlegible-latin-400-normal.woff2", "atkinson-hyperlegible-latin-700-normal.woff2",
         "jetbrains-mono-latin-400-normal.woff2"]
TTF = [n.replace(".woff2", ".ttf") for n in WOFF2]
SUPPORTS: dict[str, dict[str, list[str]]] = {
    "web": {"dist": ["charte.css", "charte-base.css", "favicon.svg", "pictogramme.svg"], "polices": WOFF2},
    "streamlit": {"dist": ["streamlit-clair.toml", "streamlit-sombre.toml"], "polices": WOFF2},
    "python": {"dist": ["charte.py", "charte-clair.mplstyle", "charte-sombre.mplstyle", "plotly-clair.json", "plotly-sombre.json"], "polices": TTF},
    "office": {"dist": ["charte.thmx", "theme-office.xml"], "polices": TTF},
    "readme": {"dist": ["pictogramme.svg", "mermaid-clair.json", "mermaid-sombre.json"], "polices": []},
}
LICENCES = ["OFL-sora.txt", "OFL-atkinsonhyperlegible.txt", "OFL-jetbrainsmono.txt"]


def plan(supports: list[str]) -> dict[str, Path]:
    """Destination relative → source, pour les supports demandés."""
    inconnus = [s for s in supports if s not in SUPPORTS]
    if inconnus:
        raise ValueError(f"support inconnu : {', '.join(inconnus)} (choix : {', '.join(SUPPORTS)})")
    out: dict[str, Path] = {}
    for s in supports:
        for n in SUPPORTS[s]["dist"]:
            out[n] = DIST / n
        for n in SUPPORTS[s]["polices"]:
            out[f"polices/{n}"] = POLICES / n
    if any(k.startswith("polices/") for k in out):
        for n in LICENCES:
            out[f"polices/{n}"] = POLICES / n
    return out


def installer(cible: Path, supports: list[str], dossier: str, forcer: bool) -> list[str]:
    fichiers = plan(supports)
    base = cible / dossier
    existants = [k for k in fichiers if (base / k).exists()]
    if existants and not forcer:
        raise FileExistsError(f"refus d'écraser sans --forcer : {', '.join(sorted(existants))}")
    for k, src in fichiers.items():
        (base / k).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, base / k)
    return sorted(fichiers)


def extrait_claude_md(dossier: str, supports: list[str]) -> str:
    return (f"- **Charte graphique** : ce dépôt suit la charte générique (supports : {', '.join(supports)}). "
            f"Les fichiers prêts à l'emploi sont dans `{dossier}/` ; aucune couleur en dur, on les prend dans ces fichiers. "
            "Contrôle : `/charte audit`. Source : https://github.com/Aliquanto3/charte-generique")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cible", type=Path, required=True)
    ap.add_argument("--supports", required=True, help="liste séparée par des virgules : " + ",".join(SUPPORTS))
    ap.add_argument("--dossier", default="static/charte")
    ap.add_argument("--forcer", action="store_true")
    a = ap.parse_args(argv)
    supports = [s.strip() for s in a.supports.split(",") if s.strip()]
    try:
        poses = installer(a.cible, supports, a.dossier, a.forcer)
    except (ValueError, FileExistsError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    print(f"Fichiers posés dans {a.cible / a.dossier} :")
    print("\n".join(f"  {p}" for p in poses))
    print("\nÀ coller dans le CLAUDE.md du dépôt cible :\n")
    print(extrait_claude_md(a.dossier, supports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
