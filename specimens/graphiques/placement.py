"""Placement des étiquettes directes en bout de ligne, sans chevauchement (règle A2 de la charte).

Fonction pure, bibliothèque standard : `rendre.py` (matplotlib en points, plotly en pixels) et le rapport Office
l'emploient ; `tests/test_graphiques.py` la vérifie.
"""
from __future__ import annotations


def placer(cibles: list[float], ecart: float) -> list[float]:
    """Positions verticales des étiquettes, au plus près des `cibles`, deux voisines séparées d'au moins `ecart`.

    Même unité pour les cibles et l'écart (points ou pixels). Les étiquettes trop proches forment un groupe,
    espacé de `ecart` exactement et centré sur la moyenne de ses cibles (écart quadratique minimal) ; on fusionne
    les groupes tant qu'ils se chevauchent. L'ordre vertical des étiquettes reste celui des cibles, et le
    résultat suit l'ordre d'entrée.
    """
    if ecart < 0:
        raise ValueError("écart négatif")
    ordre = sorted(range(len(cibles)), key=lambda i: (cibles[i], i))
    groupes: list[list[int]] = []  # indices (dans `ordre`) de chaque groupe, du bas vers le haut

    def centre(g: list[int]) -> float:
        return sum(cibles[ordre[k]] for k in g) / len(g)

    def bas(g: list[int]) -> float:
        return centre(g) - (len(g) - 1) / 2 * ecart

    def haut(g: list[int]) -> float:
        return centre(g) + (len(g) - 1) / 2 * ecart

    for k in range(len(ordre)):
        groupes.append([k])
        while len(groupes) > 1 and bas(groupes[-1]) - haut(groupes[-2]) < ecart - 1e-9:
            dernier = groupes.pop()
            groupes[-1] += dernier
    out = [0.0] * len(cibles)
    for g in groupes:
        b = bas(g)
        for j, k in enumerate(g):
            out[ordre[k]] = b + j * ecart
    return out
