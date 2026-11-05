"""Lecture de la source unique des jetons (`jetons/charte.tokens.json`, format DTCG 2025.10).

Bibliothèque standard seulement : le module tourne sans installation
(`uv run --no-project python -I`).

`charger()` rend un dictionnaire plat, le contrat commun de tous les outils et générateurs :

    {
      "version": "2.1.0",
      "theme_par_defaut": "sombre",
      "sombre": {"fond": "#0F1318", ..., "voile": "rgba(5, 8, 12, 0.6)",
                 "halo": "0 8px 24px rgba(232, 236, 242, 0.07)",
                 "cat": ["#8DB0F7", ...], "cat-1": "#8DB0F7", ..., "cat-8": "#9FAE4F",
                 "seq": [...], "seq-1": ..., "seq-5": ...,     # séquentielle, aplats contigus
                 "div": [...], "div-1": ..., "div-5": ...},    # divergente, centre `surface-alt`
      "clair": {... mêmes clés ...},
      "police": {"titres": {"familles": ["Sora", "system-ui", ...],
                            "pile": "Sora, system-ui, 'Segoe UI', Roboto, sans-serif",
                            "graisse": 600, "office": "Sora SemiBold"}, "texte": {...}, "code": {...}},
      "taille": {"legende": 12, "petit": 14, "base": 16, ..., "titre-1": 48},   # px
      "espacement": {"1": 4, "2": 8, ..., "8": 64},                            # px
      "rayon": {"petit": 6, "moyen": 10, "grand": 14, "pilule": 999},           # px
      "trait": 1,                                                               # px
      "focus": {"largeur": 2, "decalage": 2},                                   # px
    }

Les listes (`cat`, `seq`, `div`) sont les groupes de jetons numérotés ; leurs éléments existent aussi en
clés plates (`cat-1`…). `office` : nom de famille sous lequel Office voit la police incorporée (nom ID 1
du fichier `ttf` fourni), à employer dans le thème Office et dans les documents.

`PICTOGRAMME` : rôles de la tuile, des barres et du point du pictogramme, par thème (choisis par mesure,
contrôlés par `contrastes.py`). Sur un aplat sombre, on prend toujours ceux du thème sombre.

Un jeton peut être un alias DTCG (`"$value": "{theme.clair.couleur.primaire}"`) : `charger()` le résout.

Couleurs opaques en `#RRGGBB` majuscules. Couleurs translucides (`voile`) en `rgba(...)` CSS.
Ombres (`halo`) en valeur CSS `box-shadow`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CHEMIN = Path(__file__).resolve().parent.parent / "jetons" / "charte.tokens.json"
THEMES = ("sombre", "clair")
SERIES = ("cat", "seq", "div")  # groupes numérotés de couleurs
# Décision d'Anaël du 2026-11-05 : tuile et point sont des jetons (`pictogramme-tuile`, `pictogramme-point`) ;
# en clair, ils référencent `primaire` et `accent-aplat`.
PICTOGRAMME = {
    "sombre": {"tuile": "pictogramme-tuile", "barres": "sur-primaire", "point": "pictogramme-point"},
    "clair": {"tuile": "pictogramme-tuile", "barres": "sur-primaire", "point": "pictogramme-point"},
}
ALIAS = re.compile(r"^\{([^{}]+)\}$")
GENERIQUES = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-monospace",
              "ui-sans-serif", "ui-serif", "ui-rounded", "emoji", "math"}


def couleur_css(v: dict) -> str:
    """Valeur DTCG `color` → `#RRGGBB`, ou `rgba(r, g, b, a)` si alpha < 1."""
    if v.get("colorSpace") != "srgb":
        raise ValueError(f"espace de couleur non pris en charge : {v.get('colorSpace')}")
    alpha = v.get("alpha", 1)
    rvb = [round(c * 255) for c in v["components"]]
    if alpha < 1:
        return f"rgba({rvb[0]}, {rvb[1]}, {rvb[2]}, {alpha:g})"
    hexa = v.get("hex") or "#" + "".join(f"{c:02X}" for c in rvb)
    return hexa.upper()


def px(v: dict) -> int | float:
    if v.get("unit") != "px":
        raise ValueError(f"unité non prise en charge : {v.get('unit')}")
    return v["value"]


def _longueur(v: dict) -> str:
    n = px(v)
    return f"{n}px" if n else "0"


def ombre_css(v: dict) -> str:
    parties = [_longueur(v[k]) for k in ("offsetX", "offsetY", "blur")]
    if px(v["spread"]):
        parties.append(_longueur(v["spread"]))
    return " ".join(parties + [couleur_css(v["color"])])


def pile_css(familles: list[str]) -> str:
    return ", ".join(f if f in GENERIQUES or " " not in f else f"'{f}'" for f in familles)


def _valeurs(groupe: dict) -> dict:
    """Jetons directs d'un groupe (clés sans `$`), avec leur `$value`."""
    return {k: v["$value"] for k, v in groupe.items() if not k.startswith("$") and "$value" in v}


def resoudre(brut: dict, valeur, profondeur: int = 0):
    """Résout un alias DTCG (`"{theme.clair.couleur.primaire}"`) vers la `$value` visée, récursivement."""
    m = ALIAS.match(valeur) if isinstance(valeur, str) else None
    if not m:
        return valeur
    if profondeur > 8:
        raise ValueError(f"alias en boucle : {valeur}")
    noeud = brut
    for cle in m.group(1).split("."):
        if not isinstance(noeud, dict) or cle not in noeud:
            raise ValueError(f"alias introuvable : {valeur}")
        noeud = noeud[cle]
    if "$value" not in noeud:
        raise ValueError(f"alias sans valeur : {valeur}")
    return resoudre(brut, noeud["$value"], profondeur + 1)


def charger(chemin: str | Path | None = None) -> dict:
    brut = json.loads(Path(chemin or CHEMIN).read_text(encoding="utf-8"))
    meta = brut.get("$extensions", {}).get("charte", {})
    out: dict = {"version": meta.get("version"), "theme_par_defaut": meta.get("theme_par_defaut", "sombre")}
    for t in THEMES:
        groupe = brut["theme"][t]
        couleurs: dict = {k: couleur_css(resoudre(brut, v)) for k, v in _valeurs(groupe["couleur"]).items()}
        for nom in SERIES:
            g = groupe["couleur"][nom]
            serie = [couleur_css(g[str(i)]["$value"]) for i in range(1, len(_valeurs(g)) + 1)]
            couleurs[nom] = serie
            couleurs.update({f"{nom}-{i}": c for i, c in enumerate(serie, 1)})
        couleurs.update({k: ombre_css(v) for k, v in _valeurs(groupe["ombre"]).items()})
        out[t] = couleurs
    graisses = _valeurs(brut["graisse"])
    office = {r: v.get("$extensions", {}).get("charte", {}).get("office") for r, v in brut["police"].items() if not r.startswith("$")}
    out["police"] = {r: {"familles": f, "pile": pile_css(f), "graisse": graisses[r], "office": office[r] or f[0]}
                     for r, f in _valeurs(brut["police"]).items()}
    for groupe in ("taille", "espacement", "rayon", "focus"):
        out[groupe] = {k: px(v) for k, v in _valeurs(brut[groupe]).items()}
    out["trait"] = px(brut["trait"]["$value"])
    return out


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    print(json.dumps(charger(sys.argv[1] if len(sys.argv) > 1 else None), ensure_ascii=False, indent=2))
