"""Paquets Office livrés (`specimens/office/sortie/`) : règles de la charte lues en zip et en XML.

Bibliothèque standard seulement : ces tests tournent en CI, sans python-pptx ni python-docx.
"""
import importlib.util
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from jetons import charger

RACINE = Path(__file__).resolve().parent.parent
OFFICE = RACINE / "specimens" / "office"
DECK, RAPPORT = OFFICE / "sortie" / "deck.pptx", OFFICE / "sortie" / "rapport.docx"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
COULEUR = r'(?:srgbClr val|w:color|w:fill)="([0-9A-Fa-f]{6})"'


def _xml(paquet, partie):
    with zipfile.ZipFile(paquet) as z:
        return ET.fromstring(z.read(partie))


def _texte(paquet, partie):
    with zipfile.ZipFile(paquet) as z:
        return z.read(partie).decode("utf-8")


def _construire():
    spec = importlib.util.spec_from_file_location("construire_office_xml", OFFICE / "construire.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # importable sans python-pptx : ses imports lourds sont dans les fonctions
    return m


def _autorisees():
    j = charger()
    return {v.lstrip("#").upper() for t in ("clair", "sombre") for v in j[t].values() if isinstance(v, str) and v.startswith("#")}


def test_six_diapositives_16_9():
    with zipfile.ZipFile(DECK) as z:
        diapos = [n for n in z.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    assert len(diapos) == 6
    taille = _xml(DECK, "ppt/presentation.xml").find(f"{P}sldSz")
    assert abs(int(taille.get("cx")) / int(taille.get("cy")) - 16 / 9) < 0.001


@pytest.mark.parametrize("paquet,partie", [(DECK, "ppt/theme/theme1.xml"), (RAPPORT, "word/theme/theme1.xml")])
def test_theme_egal_a_dist(paquet, partie):
    with zipfile.ZipFile(paquet) as z:
        assert z.read(partie) == (RACINE / "skills" / "charte" / "dist" / "theme-office.xml").read_bytes()
    polices = _xml(paquet, partie).find(f"{A}themeElements/{A}fontScheme")
    assert polices.find(f"{A}majorFont/{A}latin").get("typeface") == "Sora SemiBold"
    assert polices.find(f"{A}minorFont/{A}latin").get("typeface") == "Atkinson Hyperlegible"


@pytest.mark.parametrize("paquet,parties", [
    (DECK, r"ppt/(slides/slide\d+|slideMasters/slideMaster\d+|slideLayouts/slideLayout\d+|charts/chart\d+)\.xml"),
    (RAPPORT, r"word/(document|footer\d+|header\d+)\.xml"),
])
def test_aucune_couleur_hors_jetons(paquet, parties):
    with zipfile.ZipFile(paquet) as z:
        noms = [n for n in z.namelist() if re.fullmatch(parties, n)]
        trouvees = {m.upper() for n in noms for m in re.findall(COULEUR, z.read(n).decode("utf-8"))}
    assert trouvees, "aucune couleur trouvée : le test ne lit rien"
    assert trouvees <= _autorisees(), sorted(trouvees - _autorisees())


def test_a12_titres_et_series():
    """A12 : titres de diapositive ≥ 28 pt sans gras ; au plus six séries ; étiquette de données (nom de série)."""
    m = _construire()
    titres = 0
    for i in range(1, 7):
        for sp in _xml(DECK, f"ppt/slides/slide{i}.xml").iter(f"{P}sp"):
            ph = sp.find(f"{P}nvSpPr/{P}nvPr/{P}ph")
            if ph is not None and ph.get("type") == "title":
                for rpr in sp.iter(f"{A}rPr"):
                    assert int(rpr.get("sz")) >= m.TITRE_DIAPO_PT * 100 and rpr.get("b") == "0"
                    titres += 1
    assert titres == 3
    series = []
    for n in (1, 2):
        graphique = _xml(DECK, f"ppt/charts/chart{n}.xml")
        series.append(len(list(graphique.iter(f"{C}ser"))))
        etiquettes = graphique.find(f".//{C}barChart/{C}dLbls")
        assert etiquettes.find(f"{C}showSerName").get("val") == "1"
    assert series == [4, m.SERIES_DIAPO] and m.SERIES_DIAPO == 6


def test_a4_b5_couverture_et_b2_aplat():
    """A4 : couverture sur aplat sombre avec pictogramme et filet sombres ; B2 : aplat d'or en `accent-aplat`."""
    j = charger()
    c, s = j["clair"], j["sombre"]
    couverture = _texte(DECK, "ppt/slides/slide1.xml")
    for jeton in ("pictogramme-tuile", "pictogramme-point", "sur-primaire", "accent"):
        assert f'val="{s[jeton][1:]}"' in couverture, jeton
    assert f'val="{c["pictogramme-tuile"][1:]}"' not in couverture
    aplat = _texte(DECK, "ppt/slides/slide5.xml")
    assert f'val="{c["accent-aplat"][1:]}"' in aplat and f'val="{c["accent"][1:]}"' not in aplat


def _style(racine, ident):
    return next(e for e in racine.iter(f"{W}style") if e.get(f"{W}styleId") == ident)


def test_b5_filet_or_sous_le_titre_du_rapport():
    styles = _xml(RAPPORT, "word/styles.xml")
    bas = _style(styles, "Title").find(f"{W}pPr/{W}pBdr/{W}bottom")
    assert bas.get(f"{W}color") == charger()["clair"]["accent"][1:]
    assert int(bas.get(f"{W}sz")) >= 12
    for ident in ("Title", "Heading1", "Heading2", "Heading3"):
        style = _style(styles, ident)
        assert style.find(f"{W}rPr/{W}rFonts").get(f"{W}ascii") == "Sora SemiBold", ident
        assert style.find(f"{W}rPr/{W}b").get(f"{W}val") in ("0", "false"), ident


def test_ordre_tcpr_conforme_au_schema():
    """CT_TcPr impose tcBorders avant shd : sinon Word peut demander une réparation."""
    xml = _texte(RAPPORT, "word/document.xml")
    vus = 0
    for tcpr in re.findall(r"<w:tcPr>.*?</w:tcPr>", xml):
        if "<w:tcBorders" in tcpr and "<w:shd" in tcpr:
            assert tcpr.index("<w:tcBorders") < tcpr.index("<w:shd"), tcpr
            vus += 1
    assert vus > 0


def test_rendre_en_cours_sur_du_doute_ne_ferme_rien(monkeypatch):
    """Si tasklist est absent ou échoue, l'application est réputée ouverte (donc jamais fermée)."""
    sys.path.insert(0, str(OFFICE))
    import rendre

    def absent(*a, **k):
        raise FileNotFoundError("tasklist")

    monkeypatch.setattr(subprocess, "run", absent)
    assert rendre._en_cours("POWERPNT.EXE") is True
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="INFO: aucune tâche", stderr=""))
    assert rendre._en_cours("POWERPNT.EXE") is False
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="POWERPNT.EXE  1234", stderr=""))
    assert rendre._en_cours("POWERPNT.EXE") is True
