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
        if role == "cat":
            assert len(v) == 8 and all(HEX.match(c) for c in v)
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
    a_voir = [v for k, v in couleurs.items() if not k.startswith("$") and k != "cat"]
    a_voir += list(couleurs["cat"].values())
    for jeton in a_voir:
        v = jeton["$value"]
        rvb = "#" + "".join(f"{round(c * 255):02X}" for c in v["components"])
        assert rvb == v["hex"].upper()


def test_roles_attendus(j):
    attendus = {"fond", "surface", "surface-alt", "trait", "texte", "texte-attenue", "neutre", "primaire",
                "primaire-vif", "primaire-doux", "sur-primaire", "bouton", "bouton-survol", "sur-bouton", "accent",
                "accent-texte", "accent-doux", "succes", "succes-doux", "alerte", "alerte-texte", "alerte-doux",
                "erreur", "erreur-doux", "focus", "texte-sur-vif", "sur-statut", "encre-pleine", "sur-encre",
                "sur-encre-attenue", "voile", "halo"}
    assert attendus <= set(j["sombre"])


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
