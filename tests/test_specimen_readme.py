"""Spécimen README : SVG bien formés, couleurs issues des jetons, tailles."""
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "skills" / "charte" / "outils"))
import jetons  # noqa: E402

DOSSIER = RACINE / "specimens" / "readme"
SVGS = ["banniere-sombre.svg", "banniere-clair.svg", "apercu-social.svg"]


def _couleurs_jetons() -> set[str]:
    j = jetons.charger()
    res = set()
    for theme in jetons.THEMES:
        for v in j[theme].values():
            for x in v if isinstance(v, list) else [v]:
                if re.fullmatch(r"#[0-9A-F]{6}", x):
                    res.add(x)
    return res


@pytest.mark.parametrize("nom", SVGS)
def test_svg_bien_forme(nom):
    racine = ET.parse(DOSSIER / nom).getroot()
    assert racine.tag.endswith("svg")


@pytest.mark.parametrize("nom", SVGS)
def test_aucune_couleur_hors_jetons(nom):
    texte = (DOSSIER / nom).read_text(encoding="utf-8")
    texte = re.sub(r"base64,[A-Za-z0-9+/=]+", "", texte)  # police embarquée
    trouvees = {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}\b", texte)}
    assert trouvees
    assert trouvees <= _couleurs_jetons(), trouvees - _couleurs_jetons()


@pytest.mark.parametrize("nom", SVGS[:2])
def test_bannieres_poids_et_police(nom):
    chemin = DOSSIER / nom
    assert chemin.stat().st_size <= 60 * 1024
    assert "@font-face" in chemin.read_text(encoding="utf-8")
    assert 'width="1280"' in chemin.read_text(encoding="utf-8")


def test_apercu_social_1280x640():
    en_tete = (DOSSIER / "apercu-social.png").read_bytes()[:24]
    assert en_tete[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", en_tete[16:24]) == (1280, 640)


def test_badges_couleurs_jetons():
    texte = (DOSSIER / "badges.md").read_text(encoding="utf-8")
    urls = re.findall(r"img\.shields\.io/badge/[^)]+", texte)
    assert len(urls) == 5
    clair = {h[1:] for h in _couleurs_jetons()}
    for u in urls:
        assert re.search(r"-([0-9A-F]{6})\?labelColor=([0-9A-F]{6})", u)
        for code in re.search(r"-([0-9A-F]{6})\?labelColor=([0-9A-F]{6})", u).groups():
            assert code in clair


def test_readme_temoin_structure():
    texte = (DOSSIER / "README-temoin.md").read_text(encoding="utf-8")
    assert "prefers-color-scheme: dark" in texte
    assert "%%{init:" in texte
    assert "```mermaid" in texte
    assert "| Fonction |" in texte
    assert "## Captures" in texte


def test_readme_temoin_init_mermaid_et_picture():
    import json

    texte = (DOSSIER / "README-temoin.md").read_text(encoding="utf-8")
    assert 'media="(prefers-color-scheme: light)" srcset="banniere-clair.svg"' in texte
    assert 'media="(prefers-color-scheme: dark)" srcset="banniere-sombre.svg"' in texte
    init = re.search(r"%%\{init: (.*)\}%%", texte).group(1)
    assert json.loads(init) == {"theme": "neutral"}  # A8 : thème neutre, lisible sur les deux pages de GitHub
    for lien in re.findall(r"\]\((rendus/[^)]+)\)", texte):
        assert (DOSSIER / lien).is_file(), lien


def test_badges_lisibles_et_url_ascii():
    import couleurs

    texte = (DOSSIER / "badges.md").read_text(encoding="utf-8")
    urls = re.findall(r"https://img\.shields\.io/badge/[^)]+", texte)
    assert urls and all(u.isascii() for u in urls)
    for fond, etiquette in re.findall(r"-([0-9A-F]{6})\?labelColor=([0-9A-F]{6})", texte):
        # texte choisi par shields.io (badge-maker) : #333 si luminosité > 0,69, sinon blanc
        r, g, b = (int(fond[i:i + 2], 16) for i in (0, 2, 4))
        texte_badge = "#333333" if (r * 299 + g * 587 + b * 114) / 255000 > 0.69 else "#FFFFFF"
        assert couleurs.contraste(texte_badge, "#" + fond) >= 4.5, fond
        assert couleurs.contraste("#FFFFFF", "#" + etiquette) >= 4.5, etiquette


def test_readme_a8_mermaid_et_replis_clairs():
    """A8 : bloc mermaid `neutral`, deux rendus sous `<picture>` avec repli clair ; bannière en repli clair."""
    texte = (DOSSIER / "README-temoin.md").read_text(encoding="utf-8")
    assert '<img alt="Projet témoin" src="banniere-clair.svg">' in texte
    assert 'srcset="rendus/mermaid-sombre.png"' in texte and 'srcset="rendus/mermaid-clair.png"' in texte
    assert re.search(r'<img alt="[^"]+" src="rendus/mermaid-clair.png">', texte)
    assert "themeVariables" not in texte
    doc = (RACINE / "docs" / "CHARTE.md").read_text(encoding="utf-8")
    assert "`neutral`" in doc and "<picture>" in doc


def test_badges_etiquette_a8():
    """A8 : étiquette `badge-etiquette` (#646E7B dans les deux thèmes), blanc 5,17:1."""
    import couleurs

    j = jetons.charger()
    etiquette = j["clair"]["badge-etiquette"]
    assert etiquette == j["sombre"]["badge-etiquette"]
    texte = (DOSSIER / "badges.md").read_text(encoding="utf-8")
    assert set(re.findall(r"labelColor=([0-9A-F]{6})", texte)) == {etiquette[1:]}
    assert round(couleurs.contraste("#FFFFFF", etiquette), 2) == 5.17


def _textes(nom):
    racine = ET.parse(DOSSIER / nom).getroot()
    return [e for e in racine.iter() if e.tag.endswith("text")], racine


def test_apercu_social_a11():
    """A11 : titre ≥ 64 px, aucun texte sous 28 px, tout dans les marges sûres de 80 px, zone centrée, filet or."""
    textes, racine = _textes("apercu-social.svg")
    assert (racine.get("width"), racine.get("height")) == ("1280", "640")
    tailles = [float(t.get("font-size")) for t in textes]
    assert max(tailles) >= 64 and min(tailles) >= 28
    for t in textes:
        x, y, taille = float(t.get("x")), float(t.get("y")), float(t.get("font-size"))
        assert t.get("text-anchor") == "middle" and x == 640  # zone utile centrée
        demi = len(t.text) * 0.62 * taille / 2  # largeur estimée (Sora 600 : ~0,6 em par signe)
        assert 80 <= x - demi and x + demi <= 1200, t.text
        assert 80 <= y - taille and y <= 560, t.text
    g = next(e for e in racine.iter() if e.tag.endswith("}g"))
    assert re.search(r"translate\((\d+) (\d+)\)", g.get("transform")).groups() == ("576", "144")


@pytest.mark.parametrize("nom", SVGS)
def test_filet_or_b5(nom):
    """B5 : filet or (`accent` du thème) sous le titre de chaque bannière et de l'aperçu social."""
    j = jetons.charger()
    theme = "clair" if "clair" in nom else "sombre"
    _, racine = _textes(nom)
    filets = [e for e in racine.iter() if e.tag.endswith("rect") and e.get("class") == "filet"]
    assert len(filets) == 1 and filets[0].get("fill") == j[theme]["accent"]
    titre = max(_textes(nom)[0], key=lambda t: float(t.get("font-size")))
    assert float(filets[0].get("y")) > float(titre.get("y"))
