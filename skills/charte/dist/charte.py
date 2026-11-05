"""Généré par generer.py depuis charte.tokens.json — ne pas modifier.

Charte générique : jetons prêts à l'emploi, sans dépendance."""

VERSION = "2.0.0"

SOMBRE = {
    "fond": "#0F1318",
    "surface": "#161B22",
    "surface-alt": "#1E242C",
    "trait": "#333B46",
    "texte": "#E8ECF2",
    "texte-attenue": "#A3ADBA",
    "neutre": "#8792A0",
    "primaire": "#8DB0F7",
    "primaire-vif": "#B3CBFA",
    "primaire-doux": "#1A2742",
    "sur-primaire": "#0A1733",
    "bouton": "#E8ECF2",
    "bouton-survol": "#FFFFFF",
    "sur-bouton": "#0F1318",
    "accent": "#E3C26B",
    "accent-texte": "#E3C26B",
    "accent-doux": "#3A3112",
    "succes": "#8CC7A0",
    "succes-doux": "#15291D",
    "alerte": "#F0A35E",
    "alerte-texte": "#F0A35E",
    "alerte-doux": "#3A2614",
    "erreur": "#EE8C84",
    "erreur-doux": "#3B1C1A",
    "focus": "#9EC0FF",
    "texte-sur-vif": "#141A1F",
    "sur-statut": "#0F1318",
    "encre-pleine": "#1A2742",
    "sur-encre": "#FFFFFF",
    "sur-encre-attenue": "#C3CEDD",
    "voile": "rgba(5, 8, 12, 0.6)",
    "cat": ["#8DB0F7", "#E3C26B", "#8CC7A0", "#F2A07B", "#E58FB8", "#6CCAD8", "#A9B4C6", "#9FAE4F"],
    "cat-1": "#8DB0F7",
    "cat-2": "#E3C26B",
    "cat-3": "#8CC7A0",
    "cat-4": "#F2A07B",
    "cat-5": "#E58FB8",
    "cat-6": "#6CCAD8",
    "cat-7": "#A9B4C6",
    "cat-8": "#9FAE4F",
    "halo": "0 8px 24px rgba(232, 236, 242, 0.07)",
}

CLAIR = {
    "fond": "#F6F8FB",
    "surface": "#FFFFFF",
    "surface-alt": "#ECF0F5",
    "trait": "#CED5DF",
    "texte": "#121821",
    "texte-attenue": "#4F5A68",
    "neutre": "#6E7886",
    "primaire": "#1D5BC2",
    "primaire-vif": "#164A9E",
    "primaire-doux": "#E1EAFA",
    "sur-primaire": "#FFFFFF",
    "bouton": "#121821",
    "bouton-survol": "#2A3442",
    "sur-bouton": "#FFFFFF",
    "accent": "#8F6300",
    "accent-texte": "#8A5F00",
    "accent-doux": "#FBF1D6",
    "succes": "#1B7043",
    "succes-doux": "#E2F1E8",
    "alerte": "#E8892A",
    "alerte-texte": "#9A4A00",
    "alerte-doux": "#FDEBDA",
    "erreur": "#B3261E",
    "erreur-doux": "#FCE4E1",
    "focus": "#1F5FD1",
    "texte-sur-vif": "#141A1F",
    "sur-statut": "#FFFFFF",
    "encre-pleine": "#121821",
    "sur-encre": "#FFFFFF",
    "sur-encre-attenue": "#C3CEDD",
    "voile": "rgba(18, 24, 33, 0.32)",
    "cat": ["#1D5BC2", "#A87A00", "#1F8155", "#C24D1B", "#B83A75", "#0E7C8C", "#6F7378", "#8A5A2B"],
    "cat-1": "#1D5BC2",
    "cat-2": "#A87A00",
    "cat-3": "#1F8155",
    "cat-4": "#C24D1B",
    "cat-5": "#B83A75",
    "cat-6": "#0E7C8C",
    "cat-7": "#6F7378",
    "cat-8": "#8A5A2B",
    "halo": "0 8px 24px rgba(18, 24, 33, 0.08)",
}

POLICES = {
    "titres": {"pile": "Sora, system-ui, 'Segoe UI', Roboto, sans-serif", "familles": ["Sora", "system-ui", "Segoe UI", "Roboto", "sans-serif"], "graisse": 600},
    "texte": {"pile": "'Atkinson Hyperlegible', system-ui, 'Segoe UI', Roboto, sans-serif", "familles": ["Atkinson Hyperlegible", "system-ui", "Segoe UI", "Roboto", "sans-serif"], "graisse": 400},
    "code": {"pile": "'JetBrains Mono', 'Cascadia Mono', Consolas, ui-monospace, monospace", "familles": ["JetBrains Mono", "Cascadia Mono", "Consolas", "ui-monospace", "monospace"], "graisse": 400},
}

TAILLES = {
    "legende": 12,
    "petit": 14,
    "base": 16,
    "grand": 18,
    "titre-4": 22,
    "titre-3": 28,
    "titre-2": 36,
    "titre-1": 48,
}

ESPACEMENTS = {
    "1": 4,
    "2": 8,
    "3": 12,
    "4": 16,
    "5": 24,
    "6": 32,
    "7": 48,
    "8": 64,
}

RAYONS = {
    "petit": 6,
    "moyen": 10,
    "grand": 14,
    "pilule": 999,
}


def theme(nom="sombre"):
    """Copie du thème `sombre` ou `clair` (alias `dark`, `light`)."""
    themes = {"sombre": SOMBRE, "dark": SOMBRE, "clair": CLAIR, "light": CLAIR}
    if nom not in themes:
        raise ValueError(f"thème inconnu : {nom!r} (sombre ou clair)")
    t = dict(themes[nom])
    t["cat"] = list(t["cat"])
    return t
