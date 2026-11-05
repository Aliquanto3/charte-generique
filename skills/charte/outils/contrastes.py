"""Contrôle de la charte : contrastes WCAG 2.1, pastilles, séries de graphique, couleurs à éviter.

Usage : uv run --no-project python -I skills/charte/outils/contrastes.py [jetons.json] [--eviter eviter.json]

- `jetons.json` : par défaut `skills/charte/jetons/charte.tokens.json`.
- `--eviter` : liste locale facultative de couleurs dont la charte doit rester loin
  (ΔE00 ≥ 15), au format {"nom": "#RRGGBB", ...}. Par défaut `~/.claude/charte/eviter.json`,
  lu seulement s'il existe ; ce fichier n'est jamais versionné.

Rend le tableau des contrastes, puis `Échecs : N`. Code de sortie 1 s'il y a au moins un échec.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # `-I` ne met pas le dossier du script dans sys.path

from couleurs import contraste, de00, ecart_minimal, melange  # noqa: E402
from jetons import THEMES, charger  # noqa: E402

EVITER_DEFAUT = Path.home() / ".claude" / "charte" / "eviter.json"
SEUIL_EVITER = 15.0
SEUIL_SERIES = 10.0  # ΔE00 minimal entre deux séries de graphique, en vision normale

# (premier plan, arrière-plan, seuil, usage)
PAIRES = [
    ("texte", "fond", 4.5, "texte courant"), ("texte", "surface", 4.5, "texte courant"),
    ("texte", "surface-alt", 4.5, "texte courant"),
    ("texte-attenue", "fond", 4.5, "texte secondaire"), ("texte-attenue", "surface", 4.5, "texte secondaire"),
    ("texte-attenue", "surface-alt", 4.5, "texte secondaire"),
    ("primaire", "fond", 4.5, "lien"), ("primaire", "surface", 4.5, "lien"),
    ("primaire", "primaire-doux", 4.5, "texte sur sélection"),
    ("primaire-vif", "surface", 4.5, "lien survolé"), ("sur-primaire", "primaire", 4.5, "texte sur pastille primaire"),
    ("sur-bouton", "bouton", 4.5, "libellé du bouton principal"), ("sur-bouton", "bouton-survol", 4.5, "bouton survolé"),
    ("bouton", "surface", 3.0, "limite du bouton (non textuel)"), ("bouton", "fond", 3.0, "limite du bouton (non textuel)"),
    ("accent", "surface", 3.0, "marque d'accent"), ("accent-texte", "surface", 4.5, "texte d'accent"),
    ("accent-texte", "accent-doux", 4.5, "bandeau d'accent"),
    ("succes", "surface", 4.5, "texte de succès"), ("succes", "succes-doux", 4.5, "bandeau de succès"),
    ("alerte-texte", "surface", 4.5, "texte d'alerte"), ("alerte-texte", "alerte-doux", 4.5, "bandeau d'alerte"),
    ("texte-sur-vif", "alerte", 4.5, "texte sur aplat d'alerte"),
    ("erreur", "surface", 4.5, "texte d'erreur"), ("erreur", "erreur-doux", 4.5, "bandeau d'erreur"),
    ("sur-statut", "erreur", 4.5, "texte sur pastille d'erreur"), ("sur-statut", "succes", 4.5, "texte sur pastille de succès"),
    ("sur-statut", "accent", 4.5, "texte sur aplat d'accent"),
    ("focus", "fond", 3.0, "anneau de focus"), ("focus", "surface", 3.0, "anneau de focus"),
    ("neutre", "surface", 3.0, "indicateur neutre (non textuel)"),
    ("sur-encre", "encre-pleine", 4.5, "texte sur aplat d'encre"),
    ("sur-encre-attenue", "encre-pleine", 4.5, "texte secondaire sur encre"),
]
# Pastille : texte coloré sur un mélange à 13 % de sa couleur avec `surface`.
PASTILLES = ("succes", "alerte-texte", "erreur", "accent-texte", "primaire")
TAUX_PASTILLE = 0.13
# Jetons comparés aux couleurs à éviter.
IDENTITE = ("primaire", "accent", "bouton", *[f"cat-{i}" for i in range(1, 9)])


def verifier(j: dict, eviter: dict[str, str] | None = None) -> tuple[list[str], list[str]]:
    """Rend (lignes du rapport en Markdown, échecs). `j` est le résultat de `jetons.charger()`."""
    eviter = eviter or {}
    lignes = ["| Thème | Premier plan | Arrière-plan | Contraste | Seuil | Usage | État |", "|---|---|---|---|---|---|---|"]
    echecs: list[str] = []
    notes: list[str] = []
    for theme in THEMES:
        t = j[theme]
        for a, b, seuil, usage in PAIRES:
            r = contraste(t[a], t[b])
            ok = r >= seuil
            lignes.append(f"| {theme} | `{a}` {t[a]} | `{b}` {t[b]} | {r:.2f}:1 | {seuil}:1 | {usage} | {'OK' if ok else 'ÉCHEC'} |")
            if not ok:
                echecs.append(f"{theme} {a}/{b} {r:.2f} < {seuil}")
        for k in PASTILLES:
            fond = melange(t[k], t["surface"], TAUX_PASTILLE)
            r = contraste(t[k], fond)
            ok = r >= 4.5
            lignes.append(f"| {theme} | `{k}` {t[k]} | pastille {fond} | {r:.2f}:1 | 4.5:1 | pastille de statut | {'OK' if ok else 'ÉCHEC'} |")
            if not ok:
                echecs.append(f"{theme} pastille {k} {r:.2f} < 4.5")
        for i, c in enumerate(t["cat"], 1):
            r = contraste(c, t["surface"])
            ok = r >= 3
            lignes.append(f"| {theme} | `cat-{i}` {c} | `surface` {t['surface']} | {r:.2f}:1 | 3.0:1 | série de graphique | {'OK' if ok else 'ÉCHEC'} |")
            if not ok:
                echecs.append(f"{theme} cat-{i} {r:.2f} < 3")
        d, i, k = ecart_minimal(t["cat"])
        notes.append(f"- {theme} : séries les plus proches en vision normale cat-{i}/cat-{k}, ΔE00 = {d:.1f} (seuil {SEUIL_SERIES:g})")
        if d < SEUIL_SERIES:
            echecs.append(f"{theme} cat-{i}/cat-{k} trop proches en vision normale ({d:.1f})")
        for nom, ref in eviter.items():
            for k in IDENTITE:
                d = de00(t[k], ref)
                if d < SEUIL_EVITER:
                    echecs.append(f"{theme} {k} {t[k]} trop proche de « {nom} » {ref} (ΔE00 {d:.1f})")
    return lignes + [""] + notes, echecs


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    p = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("jetons", nargs="?", help="fichier de jetons DTCG")
    p.add_argument("--eviter", type=Path, default=EVITER_DEFAUT, help="couleurs à éviter (fichier local)")
    args = p.parse_args(argv)
    eviter = json.loads(args.eviter.read_text(encoding="utf-8-sig")) if args.eviter.exists() else {}
    lignes, echecs = verifier(charger(args.jetons), eviter)
    print("\n".join(lignes))
    print(f"\nCouleurs à éviter vérifiées : {len(eviter)}")
    if echecs:
        print("\n".join(echecs))
    print(f"Échecs : {len(echecs)}")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
