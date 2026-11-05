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
    attendu = RACINE / "skills" / "charte" / "dist" / "mermaid-sombre.json"
    assert json.loads(init) == json.loads(attendu.read_text(encoding="utf-8"))
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
