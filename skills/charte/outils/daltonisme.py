"""Distinction des séries `cat-1` à `cat-8` en vision normale et en dyschromatopsie (Machado 2009, ΔE00).

Usage : uv run --no-project python -I skills/charte/outils/daltonisme.py [jetons.json] [--markdown] [--seuil 4.0]

Pour chaque thème et chaque vision (normale, protanopie, deutéranopie, tritanopie), rend le tableau des ΔE00
entre toutes les paires de séries, la pire paire, et deux repères : séries 1 à 4 seules, séries 1 à 8.

Code de sortie 1 seulement si une paire de `cat-1` à `cat-4` a un ΔE00 inférieur à `--seuil` (défaut 4.0,
en vision normale ou simulée). Les paires qui font intervenir `cat-5` à `cat-8` sont rapportées sans faire échouer.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # `-I` ne met pas le dossier du script dans sys.path

from couleurs import MACHADO, de00, simule  # noqa: E402
from jetons import THEMES, charger  # noqa: E402

VISIONS = ("normale", *MACHADO)
SEUIL_DEFAUT = 4.0


def paires(couleurs: list[str], vision: str = "normale") -> list[tuple[float, int, int]]:
    """Tous les ΔE00 entre paires (indices 1-based), du plus petit au plus grand ; égalités départagées par indices."""
    vues = couleurs if vision == "normale" else [simule(c, vision) for c in couleurs]
    return sorted((de00(vues[i], vues[j]), i + 1, j + 1) for i in range(len(vues)) for j in range(i + 1, len(vues)))


def analyser(jetons: dict, seuil: float = SEUIL_DEFAUT) -> tuple[list[dict], list[str]]:
    """Rend (résultats par thème et vision, échecs). Un échec = paire 1 à 4 sous le seuil."""
    res, echecs = [], []
    for theme in THEMES:
        cats = [jetons[theme][f"cat-{n}"] for n in range(1, 9)]
        for vision in VISIONS:
            p = paires(cats, vision)
            pire8, pire4 = p[0], next(x for x in p if x[2] <= 4)
            res.append({"theme": theme, "vision": vision, "paires": p, "pire8": pire8, "pire4": pire4})
            for d, i, j in p:
                if j <= 4 and d < seuil:
                    echecs.append(f"{theme} / {vision} : cat-{i} / cat-{j} ΔE00 {d:.1f} < {seuil:g}")
    return res, echecs


def _fmt(r: dict, md: bool) -> list[str]:
    cle = lambda x: f"cat-{x[1]}/cat-{x[2]} {x[0]:.1f}"  # noqa: E731
    if md:
        return [f"| {r['theme']} | {r['vision']} | {cle(r['pire4'])} | {cle(r['pire8'])} |"]
    return [f"{r['theme']:7} {r['vision']:13} séries 1-4 : {cle(r['pire4']):18} séries 1-8 : {cle(r['pire8'])}"]


def rendre(res: list[dict], md: bool = False) -> list[str]:
    sortie = []
    if md:
        sortie += ["| Thème | Vision | Pire paire 1 à 4 | Pire paire 1 à 8 |", "|---|---|---|---|"]
    for r in res:
        sortie += _fmt(r, md)
    sortie.append("")
    for r in res:
        titre = f"{r['theme']} / {r['vision']}"
        sortie.append(f"**{titre}**" if md else titre)
        if md:
            sortie += ["", "| Paire | ΔE00 |", "|---|---|"]
            sortie += [f"| cat-{i} / cat-{j} | {d:.1f} |" for d, i, j in r["paires"]]
            sortie.append("")
        else:
            sortie += [f"  cat-{i}/cat-{j} {d:5.1f}" for d, i, j in r["paires"]]
    return sortie


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    p = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("jetons", nargs="?", help="fichier de jetons DTCG")
    p.add_argument("--markdown", action="store_true", help="sortie en tableaux Markdown")
    p.add_argument("--seuil", type=float, default=SEUIL_DEFAUT, help=f"ΔE00 minimal des séries 1 à 4 (défaut {SEUIL_DEFAUT:g})")
    args = p.parse_args(argv)
    res, echecs = analyser(charger(args.jetons), args.seuil)
    print("\n".join(rendre(res, args.markdown)))
    if echecs:
        print("\n".join(echecs))
    print(f"Échecs (séries 1 à 4 sous {args.seuil:g}) : {len(echecs)}")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
