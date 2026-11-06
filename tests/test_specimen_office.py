"""Spécimen Office reconstruit (python-pptx, python-docx) : mêmes règles que les paquets livrés.

Les paquets commités de `sortie/` sont contrôlés sans ces bibliothèques par `tests/test_office_paquets.py`.
"""
import importlib.util
import re
import zipfile
from pathlib import Path

import pytest
from jetons import charger

pytest.importorskip("pptx")
pytest.importorskip("docx")

RACINE = Path(__file__).resolve().parent.parent
OFFICE = RACINE / "specimens" / "office"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


@pytest.fixture(scope="module")
def construire():
    spec = importlib.util.spec_from_file_location("construire_office", OFFICE / "construire.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def paquets(construire, tmp_path_factory):
    d = tmp_path_factory.mktemp("office")
    pptx, docx = d / "deck.pptx", d / "rapport.docx"
    construire.deck(pptx)
    pytest.importorskip("matplotlib")
    construire.graphique_png(d / "g.png")
    construire.rapport(docx, d / "g.png")
    return pptx, docx


def test_six_diapositives_16_9(paquets):
    from pptx import Presentation

    prs = Presentation(paquets[0])
    assert len(prs.slides) == 6
    assert prs.slide_width * 9 == prs.slide_height * 16 or abs(prs.slide_width / prs.slide_height - 16 / 9) < 0.001


@pytest.mark.parametrize("indice,partie", [(0, "ppt/theme/theme1.xml"), (1, "word/theme/theme1.xml")])
def test_theme_porte_les_jetons_clairs(paquets, indice, partie):
    import xml.etree.ElementTree as ET

    c = charger()["clair"]
    with zipfile.ZipFile(paquets[indice]) as z:
        racine = ET.fromstring(z.read(partie))
        assert z.read(partie) == (RACINE / "skills" / "charte" / "dist" / "theme-office.xml").read_bytes()
    schema = racine.find(f"{A}themeElements/{A}clrScheme")

    def val(nom):
        return "#" + schema.find(f"{A}{nom}/{A}srgbClr").get("val")

    assert val("dk1") == c["texte"]
    assert val("lt1") == c["surface"]
    assert val("dk2") == c["encre-pleine"]
    assert val("lt2") == c["fond"]
    for i in range(1, 7):
        assert val(f"accent{i}") == c[f"cat-{i}"]
    polices = racine.find(f"{A}themeElements/{A}fontScheme")
    assert polices.find(f"{A}majorFont/{A}latin").get("typeface") == "Sora SemiBold"
    assert polices.find(f"{A}minorFont/{A}latin").get("typeface") == "Atkinson Hyperlegible"


def _autorisees():
    j = charger()
    return {v.lstrip("#").upper() for t in ("clair", "sombre") for v in j[t].values() if isinstance(v, str) and v.startswith("#")}


COULEUR = r'(?:srgbClr val|w:color|w:fill)="([0-9A-Fa-f]{6})"'


@pytest.mark.parametrize("indice,parties", [
    (0, r"ppt/(slides/slide\d+|slideMasters/slideMaster\d+|slideLayouts/slideLayout\d+|charts/chart\d+)\.xml"),
    (1, r"word/(document|footer\d+|header\d+)\.xml"),
])
def test_aucune_couleur_hors_jetons(paquets, indice, parties):
    trouvees = set()
    with zipfile.ZipFile(paquets[indice]) as z:
        for nom in z.namelist():
            if re.fullmatch(parties, nom):
                trouvees |= {m.upper() for m in re.findall(COULEUR, z.read(nom).decode("utf-8"))}
    assert trouvees, "aucune couleur trouvée : le test ne lit rien"
    assert trouvees <= _autorisees(), f"couleurs hors jetons : {sorted(trouvees - _autorisees())}"


def test_styles_utilises_du_rapport_en_jetons(paquets):
    """Les styles du modèle python-docx non employés gardent leurs couleurs ; ceux du rapport doivent être en jetons."""
    from docx import Document

    d = Document(paquets[1])
    for nom in ("Normal", "Title", "Heading 1", "Heading 2", "Heading 3"):
        assert str(d.styles[nom].font.color.rgb) in _autorisees(), nom
    tailles = [d.styles[n].font.size.pt for n in ("Title", "Heading 1", "Heading 2", "Heading 3", "Normal")]
    assert tailles == sorted(tailles, reverse=True) and len(set(tailles)) == 5, tailles
    assert tailles[3] >= tailles[4] * 1.3, "Titre 3 trop proche du corps"


def test_ordre_tcpr_conforme_au_schema(paquets):
    """CT_TcPr impose tcBorders avant shd : sinon Word peut demander une réparation."""
    with zipfile.ZipFile(paquets[1]) as z:
        xml = z.read("word/document.xml").decode("utf-8")
    for tcpr in re.findall(r"<w:tcPr>.*?</w:tcPr>", xml):
        if "<w:tcBorders" in tcpr and "<w:shd" in tcpr:
            assert tcpr.index("<w:tcBorders") < tcpr.index("<w:shd"), tcpr


def test_rapport_styles_et_pied(paquets):
    from docx import Document

    d = Document(paquets[1])
    styles = {p.style.name for p in d.paragraphs}
    assert {"Title", "Heading 1", "Heading 2", "Heading 3"} <= styles
    assert len(d.tables) == 2  # tableau de données et encadré d'alerte
    assert "version" in d.sections[0].footer.paragraphs[0].text
    assert len(d.inline_shapes) == 1


def test_regles_diapositive_a12_a4_b2(paquets):
    """A12 : titres ≥ 28 pt, au plus six séries, étiquettes de données ; A4 : pictogramme sombre sur la couverture ;
    B2 : aplat d'or en `accent-aplat` ; B5 : filet or (valeur sombre) sous le titre de couverture."""
    from pptx import Presentation

    j = charger()
    c, s = j["clair"], j["sombre"]
    prs = Presentation(paquets[0])
    for diapo in prs.slides:
        if diapo.shapes.title is not None:
            assert diapo.shapes.title.text_frame.paragraphs[0].runs[0].font.size.pt >= 28
    graphiques = [sh.chart for sh in prs.slides[2].shapes if sh.has_chart]
    assert [len(list(g.plots[0].series)) for g in graphiques] == [4, 6]
    assert all(g.plots[0].has_data_labels and g.plots[0].data_labels.show_series_name for g in graphiques)
    with zipfile.ZipFile(paquets[0]) as z:
        couverture = z.read("ppt/slides/slide1.xml").decode("utf-8")
        aplat = z.read("ppt/slides/slide5.xml").decode("utf-8")
    for jeton in ("pictogramme-tuile", "pictogramme-point", "sur-primaire", "accent"):
        assert f'val="{s[jeton][1:]}"' in couverture, jeton
    assert f'val="{c["pictogramme-tuile"][1:]}"' not in couverture
    assert f'val="{c["accent-aplat"][1:]}"' in aplat and f'val="{c["accent"][1:]}"' not in aplat


def test_rapport_filet_or_sous_le_titre(paquets):
    from docx import Document
    from docx.oxml.ns import qn

    d = Document(paquets[1])
    bas = d.styles["Title"].element.pPr.find(qn("w:pBdr")).find(qn("w:bottom"))
    assert bas.get(qn("w:color")) == charger()["clair"]["accent"][1:]
    assert int(bas.get(qn("w:sz"))) >= 12
    assert all(d.styles[n].font.bold is False for n in ("Title", "Heading 1", "Heading 2", "Heading 3"))
