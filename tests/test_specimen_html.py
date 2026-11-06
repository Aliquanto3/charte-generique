"""Le spécimen HTML n'utilise que des variables existantes et aucune couleur en dur."""
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
HTML = RACINE / "specimens" / "html"
CSS_CHARTE = RACINE / "skills" / "charte" / "dist" / "charte.css"
RENDUS = ["specimen-sombre.png", "specimen-clair.png", "specimen-clair.pdf",
          "specimen-gris.pdf", "specimen-gris-page1.png"]
COULEURS_NOMMEES = {"white", "black", "red", "green", "blue", "gray", "grey", "silver",
                    "yellow", "orange", "purple", "navy", "teal", "maroon", "olive", "lime",
                    "aqua", "fuchsia", "pink", "brown", "gold"}


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
        # Couleurs nommées dans une propriété CSS ou un attribut SVG de couleur.
        nommees = re.findall(r"(?:color|background|fill|stroke|border[a-z-]*)\s*[:=]\s*\"?([^;\"}]*)", texte)
        for valeur in nommees:
            mots = set(re.sub(r"var\([^)]*\)", "", valeur).split())
            assert not mots & COULEURS_NOMMEES, f"{nom} : {valeur}"


def test_liens_et_polices():
    page = _texte("specimen.html")
    assert "../../skills/charte/dist/charte.css" in page
    assert "../../skills/charte/dist/charte-base.css" in page
    for police in re.findall(r'url\("([^"]+\.woff2)"\)', _texte("composants.css")):
        assert (HTML / police).resolve().exists(), police


def test_contenu_attendu():
    page = _texte("specimen.html")
    classes = {c for attr in re.findall(r'class="([^"]+)"', page) for c in attr.split()}
    for classe in ("titre-1", "titre-2", "titre-3", "titre-4", "bouton-principal",
                   "bouton-secondaire", "champ-erreur", "pastille-succes", "pastille-alerte",
                   "pastille-erreur", "pastille-accent", "pastille-info", "bandeau-succes",
                   "carte", "scene-modale", "c8", "nuancier"):
        assert classe in classes, classe
    assert re.search(r"<button[^>]*\bdisabled\b", page)
    assert "documentElement.dataset.theme" in page
    assert len(re.findall(r'<svg class="graphique"', page)) == 2
    for svg in re.findall(r'<svg class="graphique"[^>]*>', page):
        assert 'role="img"' in svg and "aria-label=" in svg
    assert len(re.findall(r'<polyline class="ligne c[1-8]"', page)) == 8
    assert len(re.findall(r'<rect class="c[1-4]"', page)) == 4
    assert "@media print" in _texte("composants.css")


def test_rendus_presents():
    for nom in RENDUS:
        assert (HTML / "rendus" / nom).stat().st_size > 1000, nom


def test_filet_or_sous_le_titre():
    """B5 : la première page porte le filet or (`accent`) sous son titre."""
    page = _texte("specimen.html")
    ouverture = page.split('id="ouverture"', 1)[1].split("</section>", 1)[0]
    assert 'class="titre-1"' in ouverture and 'class="filet"' in ouverture
    assert ouverture.index("titre-1") < ouverture.index("filet")
    assert re.search(r"\.filet \{[^}]*background: var\(--accent\)", _texte("composants.css"))


def test_contours_interactifs_trait_fort():
    """A5 : bouton secondaire, champs, sélecteur et modale en `trait-fort`."""
    css = _texte("composants.css")
    for regle in (".bouton-secondaire", ".champ input", ".selecteur select", ".modale {"):
        bloc = css.split(regle, 1)[1].split("}", 1)[0]
        assert "var(--trait-fort)" in bloc, regle


def test_feuille_impression_a7():
    """A7 : à l'impression, fonds pleins en contour, intitulés en gras ; un tiret par série dès l'écran."""
    css = _texte("composants.css")
    impression = css.split("@media print", 1)[1]
    assert re.search(r"\.bandeau, \.pastille, \.aplat-or \{ background: none; \}", impression)
    assert re.search(r"\.bandeau strong[^{]*\{ font-weight: 700; \}", impression)
    assert "border: var(--trait-largeur) solid var(--couleur)" in impression  # pastille en contour
    assert len(re.findall(r"stroke-dasharray", css)) >= 3


def test_pictogramme_et_nouveaux_jetons():
    page = _texte("specimen.html")
    for var in ("--picto-tuile", "--picto-barres", "--picto-point"):
        assert f"var({var})" in page
    for jeton in ("trait-fort", "accent-aplat", "badge-etiquette", "seq-1", "seq-5", "div-1", "div-5"):
        assert f"var(--{jeton})" in page, jeton
    assert 'class="aplat-or"' in page
