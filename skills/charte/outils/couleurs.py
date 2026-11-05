"""Calculs de couleur partagés : contraste WCAG 2.1, mélange sRGB, CIELAB, CIEDE2000, simulation des dyschromatopsies.

Bibliothèque standard seulement. Toutes les fonctions prennent des couleurs `#RRGGBB`.
"""
from __future__ import annotations

import math


def _rvb(h: str) -> list[int]:
    h = h.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def lineaire(h: str) -> list[float]:
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in (c / 255 for c in _rvb(h))]


def luminance(h: str) -> float:
    r, g, b = lineaire(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    x, y = sorted((luminance(a), luminance(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def melange(premier: str, fond: str, p: float) -> str:
    """Comme `color-mix(in srgb, premier p, fond)` en CSS."""
    a, b = _rvb(premier), _rvb(fond)
    return "#" + "".join(f"{round(p * x + (1 - p) * y):02X}" for x, y in zip(a, b, strict=True))


def lab(h: str) -> tuple[float, float, float]:
    r, g, b = lineaire(h)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    return 116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))


def de00(c1: str, c2: str) -> float:
    """Écart CIEDE2000 entre deux couleurs."""
    L1, a1, b1 = lab(c1)
    L2, a2, b2 = lab(c2)
    Cb = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1, C2 = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1 = math.degrees(math.atan2(b1, a1p)) % 360
    h2 = math.degrees(math.atan2(b2, a2p)) % 360
    if C1 * C2 == 0:
        dh = 0.0
    elif abs(h2 - h1) <= 180:
        dh = h2 - h1
    else:
        dh = h2 - h1 - 360 if h2 > h1 else h2 - h1 + 360
    dH = 2 * math.sqrt(C1 * C2) * math.sin(math.radians(dh / 2))
    Lb, Cbp = (L1 + L2) / 2, (C1 + C2) / 2
    if C1 * C2 == 0:
        hb = h1 + h2
    elif abs(h1 - h2) <= 180:
        hb = (h1 + h2) / 2
    else:
        hb = (h1 + h2 + 360) / 2 if h1 + h2 < 360 else (h1 + h2 - 360) / 2
    T = (1 - 0.17 * math.cos(math.radians(hb - 30)) + 0.24 * math.cos(math.radians(2 * hb))
         + 0.32 * math.cos(math.radians(3 * hb + 6)) - 0.20 * math.cos(math.radians(4 * hb - 63)))
    SL = 1 + 0.015 * (Lb - 50) ** 2 / math.sqrt(20 + (Lb - 50) ** 2)
    SC, SH = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    RT = -2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-((hb - 275) / 25) ** 2)))
    return math.sqrt(((L2 - L1) / SL) ** 2 + ((C2 - C1) / SC) ** 2 + (dH / SH) ** 2
                     + RT * ((C2 - C1) / SC) * (dH / SH))


# Simulation de Machado, Oliveira et Fernandes (2009), sévérité 1.0, en RVB linéaire.
MACHADO = {
    "protanopie": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    "deuteranopie": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
    "tritanopie": [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
}


def simule(h: str, vision: str) -> str:
    """Couleur perçue en `vision` (clé de MACHADO)."""
    m = MACHADO[vision]
    c = lineaire(h)
    v = [max(0.0, min(1.0, sum(m[i][j] * c[j] for j in range(3)))) for i in range(3)]
    s = [12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055 for x in v]
    return "#" + "".join(f"{round(x * 255):02X}" for x in s)


def ecart_minimal(couleurs: list[str], vision: str | None = None) -> tuple[float, int, int]:
    """Plus petit ΔE00 entre deux couleurs de la liste (indices 1-based), en vision normale ou simulée."""
    vues = couleurs if vision is None else [simule(c, vision) for c in couleurs]
    return min((de00(vues[i], vues[j]), i + 1, j + 1)
               for i in range(len(vues)) for j in range(i + 1, len(vues)))
