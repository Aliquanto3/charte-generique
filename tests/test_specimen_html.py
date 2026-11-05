"""Le spécimen HTML n'utilise que des variables existantes et aucune couleur en dur."""
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
HTML = RACINE / "specimens" / "html"
CSS_CHARTE = RACINE / "skills" / "charte" / "dist" / "charte.css"
RENDUS = ["specimen-sombre.png", "specimen-clair.png", "specimen-clair.pdf",
          "specimen-gris.pdf", "specimen-gris-page1.png"]


def _texte(nom):
    return (HTML / nom).read_text(encoding="utf-8")


def test_variables_utilisees_existent():
    definies = set(re.findall(r"(--[a-z0-9-]+)\s*:", CSS_CHARTE.read_text(encoding="utf-8")))
    assert "--trait-largeur" in definies
    locales = set()  # variables locales aux composants, ex. --couleur, --c
    for nom in ("composants.css", "specimen.html"):
        locales |= set(re.findall(r"(--[a-z0-9-]+)\s*:", _texte(nom)))
    for nom in ("composants.css", "specimen.html"):
        texte = _texte(nom)
        for var in set(re.findall(r"var\((--[a-z0-9-]+)", texte)):
            assert var in definies or var in locales, f"{nom} : {var} inconnue"


def test_aucune_couleur_en_dur():
    motif = re.compile(r"#[0-9A-Fa-f]{3,8}\b|rgba?\(|hsla?\(")
    for nom in ("composants.css", "specimen.html"):
        texte = re.sub(r"&#\d+;", "", _texte(nom))
        assert not motif.findall(texte), nom


def test_liens_et_polices():
    page = _texte("specimen.html")
    assert "../../skills/charte/dist/charte.css" in page
    assert "../../skills/charte/dist/charte-base.css" in page
    for police in re.findall(r'url\("([^"]+\.woff2)"\)', _texte("composants.css")):
        assert (HTML / police).resolve().exists(), police


def test_contenu_attendu():
    page = _texte("specimen.html")
    for classe in ("titre-1", "titre-2", "titre-3", "titre-4", "bouton-principal",
                   "bouton-secondaire", "champ-erreur", "pastille-succes", "pastille-alerte",
                   "pastille-erreur", "pastille-accent", "pastille-info", "bandeau-succes",
                   "carte", "scene-modale", "c8", "nuancier"):
        assert f'"{classe}' in page or f" {classe}" in page, classe
    assert "disabled" in page and 'data-theme' in page.replace("dataset.theme", "data-theme")
    assert "@media print" in _texte("composants.css")


def test_rendus_presents():
    for nom in RENDUS:
        assert (HTML / "rendus" / nom).stat().st_size > 1000, nom
