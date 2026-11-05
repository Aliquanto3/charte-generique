import json
import re

import pytest
from jetons import CHEMIN, THEMES, charger, couleur_css, pile_css

HEX = re.compile(r"^#[0-9A-F]{6}$")


@pytest.fixture(scope="module")
def j():
    return charger()


def test_version(j):
    assert re.fullmatch(r"\d+\.\d+\.\d+", j["version"])
    assert j["theme_par_defaut"] == "sombre"


def test_themes_memes_roles(j):
    assert set(j["sombre"]) == set(j["clair"])


@pytest.mark.parametrize("theme", THEMES)
def test_couleurs_bien_formees(j, theme):
    for role, v in j[theme].items():
        if role in ("cat", "seq", "div"):
            assert len(v) == (8 if role == "cat" else 5) and all(HEX.match(c) for c in v)
            assert v == [j[theme][f"{role}-{i}"] for i in range(1, len(v) + 1)]
        elif role == "voile":
            assert v.startswith("rgba(")
        elif role == "halo":
            assert v.endswith(")") and "rgba(" in v
        else:
            assert HEX.match(v), (theme, role, v)


@pytest.mark.parametrize("theme", THEMES)
def test_hex_egal_composantes(theme):
    """Le champ `hex` des couleurs DTCG doit correspondre à `components`."""
    brut = json.loads(CHEMIN.read_text(encoding="utf-8"))
    couleurs = brut["theme"][theme]["couleur"]
    groupes = ("cat", "seq", "div")
    a_voir = [v for k, v in couleurs.items() if not k.startswith("$") and k not in groupes]
    for g in groupes:
        a_voir += [v for k, v in couleurs[g].items() if not k.startswith("$")]
    assert len(a_voir) > 50
    for jeton in a_voir:
        v = jeton["$value"]
        rvb = "#" + "".join(f"{round(c * 255):02X}" for c in v["components"])
        assert rvb == v["hex"].upper()


def test_roles_attendus(j):
    attendus = {"fond", "surface", "surface-alt", "trait", "texte", "texte-attenue", "neutre", "primaire",
                "primaire-vif", "primaire-doux", "sur-primaire", "bouton", "bouton-survol", "sur-bouton", "accent",
                "accent-texte", "accent-doux", "succes", "succes-doux", "alerte", "alerte-texte", "alerte-doux",
                "erreur", "erreur-doux", "focus", "texte-sur-vif", "sur-statut", "encre-pleine", "sur-encre",
                "sur-encre-attenue", "voile", "halo", "trait-fort", "accent-aplat", "badge-etiquette"}
    assert attendus <= set(j["sombre"])


def test_jetons_v2_1(j):
    """Valeurs fixées par la critique v2.0 (A5, A6, A8, B2) et version 2.1."""
    from couleurs import melange

    assert j["version"] == "2.1.0"
    assert (j["sombre"]["trait-fort"], j["clair"]["trait-fort"]) == ("#67717E", "#808A97")
    assert (j["sombre"]["accent-aplat"], j["clair"]["accent-aplat"]) == ("#E3C26B", "#E0B54A")
    assert j["sombre"]["badge-etiquette"] == j["clair"]["badge-etiquette"] == "#646E7B"
    assert j["clair"]["seq"] == ["#D2DEF3", "#A5BDE7", "#779DDA", "#4A7CCE", "#1D5BC2"]
    assert j["sombre"]["seq"] == ["#2E394D", "#465777", "#5D74A2", "#7592CC", "#8DB0F7"]
    for t in THEMES:
        c = j[t]
        assert c["seq"] == [melange(c["primaire"], c["surface"], p) for p in (0.2, 0.4, 0.6, 0.8, 1.0)]
        assert c["div"] == [c["primaire"], melange(c["primaire"], c["surface-alt"], 0.5), c["surface-alt"],
                            melange(c["cat-5"], c["surface-alt"], 0.5), c["cat-5"]]


def test_noms_office(j):
    """Noms de famille vus par Office une fois la police incorporée (nom ID 1 des ttf fournis)."""
    assert [j["police"][r]["office"] for r in ("titres", "texte", "code")] == ["Sora SemiBold", "Atkinson Hyperlegible", "JetBrains Mono"]


def test_typo_et_formes(j):
    assert j["police"]["titres"]["familles"][0] == "Sora"
    assert j["police"]["titres"]["graisse"] == 600
    assert j["police"]["texte"]["pile"].startswith("'Atkinson Hyperlegible', system-ui")
    assert list(j["taille"].values()) == sorted(j["taille"].values())
    assert j["rayon"] == {"petit": 6, "moyen": 10, "grand": 14, "pilule": 999}
    assert j["focus"] == {"largeur": 2, "decalage": 2}


def test_pile_css():
    assert pile_css(["JetBrains Mono", "Consolas", "ui-monospace"]) == "'JetBrains Mono', Consolas, ui-monospace"


def test_couleur_alpha():
    assert couleur_css({"colorSpace": "srgb", "components": [0, 0, 1], "alpha": 0.5}) == "rgba(0, 0, 255, 0.5)"
    with pytest.raises(ValueError):
        couleur_css({"colorSpace": "display-p3", "components": [0, 0, 0]})
