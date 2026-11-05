"""Contrôle de la charte : contrastes WCAG 2.1, pastilles, pictogramme, séries et palettes de graphique, couleurs à éviter.

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

from couleurs import contraste, de00, ecart_minimal, melange, simule  # noqa: E402
from jetons import PICTOGRAMME, THEMES, charger  # noqa: E402

EVITER_DEFAUT = Path.home() / ".claude" / "charte" / "eviter.json"
SEUIL_EVITER = 15.0
SEUIL_SERIES = 10.0  # ΔE00 minimal entre deux séries de graphique, en vision normale
SEUIL_PAS = 9.4  # ΔE00 minimal entre deux pas voisins des palettes `seq` et `div`, en normale et en deutéranopie
VISIONS_PAS = ("normale", "deuteranopie")
# Fonds de page de GitHub (thème par défaut, Primer « canvas.default »). Ce ne sont pas des jetons : ils servent
# seulement à vérifier que l'étiquette de badge (`badge-etiquette`) se détache de la page dans les deux thèmes.
GITHUB_SOMBRE = "#0D1117"
GITHUB_CLAIR = "#FFFFFF"

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
    ("trait-fort", "fond", 3.0, "contour interactif (non textuel)"), ("trait-fort", "surface", 3.0, "contour interactif (non textuel)"),
    ("trait-fort", "surface-alt", 3.0, "contour interactif (non textuel)"),
    ("texte-sur-vif", "accent-aplat", 4.5, "texte sur aplat d'or"),
    ("sur-encre", "badge-etiquette", 4.5, "texte de l'étiquette de badge"),
    ("badge-etiquette", "fond", 3.0, "étiquette de badge sur la page (non textuel)"),
]
# Paires propres à un thème.
PAIRES_THEME = {
    "clair": [("texte", "accent-aplat", 4.5, "texte sur aplat d'or")],
    "sombre": [],
}
# Pastille : texte coloré sur un mélange à 13 % de sa couleur avec `surface`.
PASTILLES = ("succes", "alerte-texte", "erreur", "accent-texte", "primaire")
TAUX_PASTILLE = 0.13
# Jetons comparés aux couleurs à éviter.
IDENTITE = ("primaire", "accent", "bouton", *[f"cat-{i}" for i in range(1, 9)], "trait-fort", "accent-aplat", "badge-etiquette",
            *[f"seq-{i}" for i in range(1, 6)], *[f"div-{i}" for i in range(1, 6)])


def paires_pictogramme(j: dict) -> list[tuple[str, str, str, str, str, float, str]]:
    """(thème, nom 1, couleur 1, nom 2, couleur 2, seuil, usage) des marques non textuelles du pictogramme et du filet.

    Règle « fond sombre » (A4) : sur un aplat sombre d'un document clair (`encre-pleine` clair), le pictogramme et le
    filet prennent les valeurs du thème sombre.
    """
    out = []
    for theme in THEMES:
        t, r = j[theme], PICTOGRAMME[theme]
        tuile = (f"{r['tuile']}", t[r["tuile"]])
        out.append((theme, f"point {r['point']}", t[r["point"]], f"tuile {r['tuile']}", tuile[1], 3.0, "point du pictogramme"))
        for fond in ("fond", "surface", "encre-pleine") if theme == "sombre" else ("fond", "surface"):
            out.append((theme, f"tuile {r['tuile']}", tuile[1], fond, t[fond], 3.0, "tuile du pictogramme"))
        out.append((theme, "filet accent", t["accent"], "fond", t["fond"], 3.0, "filet or sous le titre"))
    s, r = j["sombre"], PICTOGRAMME["sombre"]
    aplat = j["clair"]["encre-pleine"]
    out.append(("sombre sur aplat clair", f"tuile {r['tuile']}", s[r["tuile"]], "encre-pleine (clair)", aplat, 3.0, "pictogramme sur aplat sombre"))
    out.append(("sombre sur aplat clair", "filet accent", s["accent"], "encre-pleine (clair)", aplat, 3.0, "filet sur aplat sombre"))
    for theme in THEMES:
        for nom, page in (("page sombre de GitHub", GITHUB_SOMBRE), ("page claire de GitHub", GITHUB_CLAIR)):
            out.append((theme, "badge-etiquette", j[theme]["badge-etiquette"], nom, page, 3.0, "étiquette de badge sur GitHub"))
    return out


def pas_voisins(couleurs: list[str], vision: str = "normale") -> tuple[float, int]:
    """Plus petit ΔE00 entre deux pas voisins d'une palette ordonnée, et l'indice (1-based) du premier des deux."""
    vues = couleurs if vision == "normale" else [simule(c, vision) for c in couleurs]
    return min((de00(vues[i], vues[i + 1]), i + 1) for i in range(len(vues) - 1))


def verifier(j: dict, eviter: dict[str, str] | None = None) -> tuple[list[str], list[str]]:
    """Rend (lignes du rapport en Markdown, échecs). `j` est le résultat de `jetons.charger()`."""
    eviter = eviter or {}
    lignes = ["| Thème | Premier plan | Arrière-plan | Contraste | Seuil | Usage | État |", "|---|---|---|---|---|---|---|"]
    echecs: list[str] = []
    notes: list[str] = []
    for theme in THEMES:
        t = j[theme]
        for a, b, seuil, usage in PAIRES + PAIRES_THEME[theme]:
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
        for palette in ("seq", "div"):
            for vision in VISIONS_PAS:
                d, i = pas_voisins(t[palette], vision)
                notes.append(f"- {theme} : palette {palette}, pas voisins les plus proches en {vision} {palette}-{i}/{palette}-{i + 1}, "
                             f"ΔE00 = {d:.1f} (seuil {SEUIL_PAS:g})")
                if d < SEUIL_PAS:
                    echecs.append(f"{theme} {palette}-{i}/{palette}-{i + 1} trop proches en {vision} ({d:.1f} < {SEUIL_PAS:g})")
        d, i, k = ecart_minimal(t["cat"])
        notes.append(f"- {theme} : séries les plus proches en vision normale cat-{i}/cat-{k}, ΔE00 = {d:.1f} (seuil {SEUIL_SERIES:g})")
        if d < SEUIL_SERIES:
            echecs.append(f"{theme} cat-{i}/cat-{k} trop proches en vision normale ({d:.1f})")
        for nom, ref in eviter.items():
            for k in IDENTITE:
                d = de00(t[k], ref)
                if d < SEUIL_EVITER:
                    echecs.append(f"{theme} {k} {t[k]} trop proche de « {nom} » {ref} (ΔE00 {d:.1f})")
    for theme, a, ca, b, cb, seuil, usage in paires_pictogramme(j):
        r = contraste(ca, cb)
        ok = r >= seuil
        lignes.append(f"| {theme} | `{a}` {ca} | `{b}` {cb} | {r:.2f}:1 | {seuil}:1 | {usage} | {'OK' if ok else 'ÉCHEC'} |")
        if not ok:
            echecs.append(f"{theme} {a}/{b} {r:.2f} < {seuil}")
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
