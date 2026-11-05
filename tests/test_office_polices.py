"""B3 : polices de la charte incorporées aux paquets Office livrés (`specimens/office/sortie/`), lus en zip et en XML.

Bibliothèque standard seulement : ces tests tournent en CI, sans python-pptx ni python-docx.
"""
import importlib.util
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
OFFICE = RACINE / "specimens" / "office"
POLICES = RACINE / "skills" / "charte" / "polices"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
FAMILLES = {"Sora SemiBold", "Atkinson Hyperlegible", "JetBrains Mono"}


def _module(nom):
    sys.path.insert(0, str(OFFICE))
    spec = importlib.util.spec_from_file_location(nom, OFFICE / f"{nom}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def inc():
    return _module("incorporer")


@pytest.fixture(scope="module")
def pdf():
    return _module("polices_pdf")


def _rels(z, partie):
    return {e.get("Id"): e for e in ET.fromstring(z.read(partie))}


def test_obfuscation_17_8_1(inc):
    """XOR des 32 premiers octets avec la clé GUID lue octets inversés ; l'opération est involutive."""
    cle = "{00112233-4455-6677-8899-AABBCCDDEEFF}"
    donnees = bytes(range(40))
    o = inc.obfusquer(donnees, cle)
    inverse = bytes.fromhex("FFEEDDCCBBAA99887766554433221100")
    assert o[:16] == bytes(a ^ b for a, b in zip(donnees[:16], inverse, strict=True))
    assert o[16:32] == bytes(a ^ b for a, b in zip(donnees[16:32], inverse, strict=True))
    assert o[32:] == donnees[32:]
    assert inc.obfusquer(o, cle) == donnees


def test_eot_entete(inc):
    """En-tête EOT 0x00020001 : tailles, nombre magique, poids, fsType, puis le TTF intact en fin de fichier."""
    ttf = (POLICES / "sora-latin-600-normal.ttf").read_bytes()
    e = inc.eot(ttf)
    taille, donnees, version, drapeaux = struct.unpack("<4I", e[:16])
    assert (taille, donnees, version, drapeaux) == (len(e), len(ttf), 0x00020001, 0)
    poids, fs_type, magique = struct.unpack("<IHH", e[28:36])
    assert (poids, fs_type, magique) == (600, 0, 0x504C)
    assert e.endswith(ttf)
    assert "Sora SemiBold".encode("utf-16-le") in e[: len(e) - len(ttf)]


def test_noms_office_egaux_aux_ttf(inc):
    """Précision 3 : la famille déclarée est le nom ID 1 du ttf incorporé."""
    for _, _, nom, ttf in inc.polices():
        assert inc.noms(ttf.read_bytes())[1] == nom
        assert struct.unpack(">H", inc.tables(ttf.read_bytes())["OS/2"][8:10])[0] == 0  # fsType : incorporation permise


def test_docx_polices_incorporees(inc):
    with zipfile.ZipFile(OFFICE / "sortie" / "rapport.docx") as z:
        types = z.read("[Content_Types].xml").decode("utf-8")
        assert '<Default Extension="odttf" ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont"/>' in types
        assert ET.fromstring(z.read("word/settings.xml")).find(f"{W}embedTrueTypeFonts") is not None
        reglages = [e.tag for e in ET.fromstring(z.read("word/settings.xml"))]
        assert reglages.index(f"{W}embedTrueTypeFonts") == reglages.index(f"{W}zoom") + 1  # ordre de CT_Settings
        rels = _rels(z, "word/_rels/fontTable.xml.rels")
        polices = {f.get(f"{W}name"): f for f in ET.fromstring(z.read("word/fontTable.xml"))}
        assert FAMILLES <= set(polices)
        vues = 0
        for _, style, nom, ttf in inc.polices():
            balise = f"{W}embedRegular" if style == "regular" else f"{W}embedBold"
            e = polices[nom].find(balise)
            assert e is not None, (nom, style)
            assert list(polices[nom])[-1].tag.startswith(f"{W}embed")  # embed* en fin de CT_Font
            rel = rels[e.get(f"{R}id")]
            assert rel.get("Type").endswith("/relationships/font")
            cle = e.get(f"{W}fontKey")
            assert re.fullmatch(r"\{[0-9A-F]{8}(-[0-9A-F]{4}){3}-[0-9A-F]{12}\}", cle)
            assert inc.obfusquer(z.read("word/" + rel.get("Target")), cle) == ttf.read_bytes()
            vues += 1
        assert vues == 4


def test_pptx_polices_incorporees():
    with zipfile.ZipFile(OFFICE / "sortie" / "deck.pptx") as z:
        assert '<Default Extension="fntdata" ContentType="application/x-fontdata"/>' in z.read("[Content_Types].xml").decode("utf-8")
        racine = ET.fromstring(z.read("ppt/presentation.xml"))
        assert racine.get("embedTrueTypeFonts") == "1" and racine.get("saveSubsetFonts") == "1"
        enfants = [e.tag[len(P):] for e in racine]
        assert enfants.index("embeddedFontLst") == enfants.index("notesSz") + 1  # ordre de CT_Presentation
        rels = _rels(z, "ppt/_rels/presentation.xml.rels")
        lst = racine.find(f"{P}embeddedFontLst")
        noms = {}
        for ef in lst:
            styles = [e.tag[len(P):] for e in ef]
            assert styles[0] == "font" and styles[1] == "regular"
            noms[ef.find(f"{P}font").get("typeface")] = styles[1:]
            for e in ef[1:]:
                rel = rels[e.get(f"{R}id")]
                assert rel.get("Type").endswith("/relationships/font")
                donnees = z.read("ppt/" + rel.get("Target"))
                assert struct.unpack("<I", donnees[8:12])[0] == 0x00020001  # EOT : seul format employé par PowerPoint
                assert struct.unpack("<I", donnees[:4])[0] == len(donnees)
        assert noms == {"Sora SemiBold": ["regular"], "Atkinson Hyperlegible": ["regular", "bold"], "JetBrains Mono": ["regular"]}


def test_preuve_pdf_lecture(pdf):
    """Noms PDF décodés, préfixe de sous-ensemble retiré, flux zlib lus, programme TrueType reconnu."""
    import zlib

    assert pdf.nom_pdf(b"ABCDEF+Atkinson#20Hyperlegible") == "Atkinson Hyperlegible"
    ttf = (POLICES / "sora-latin-600-normal.ttf").read_bytes()
    corps = zlib.compress(b"<</Type/FontDescriptor/FontName/ABCDEF+1/FontFile2 7 0 R>>")
    faux = (b"%PDF-1.7\n3 0 obj\n<</Length 9>>stream\n" + corps + b"\nendstream\nendobj\n"
            b"7 0 obj\n<</Filter/FlateDecode>>stream\n" + zlib.compress(ttf) + b"\nendstream\nendobj\n")
    assert pdf.polices_pdf(faux) >= {"1", "Sora-SemiBold"}
    assert pdf.programmes(faux) == {"1": "Sora-SemiBold"}
    assert pdf.nom_postscript(b"pas une police") is None
    assert pdf.manquantes([OFFICE / "rendus" / "deck.pdf", OFFICE / "rendus" / "rapport.pdf"]) == []


@pytest.mark.parametrize("nom", ["deck.pdf", "rapport.pdf"])
def test_pdf_rendus_portent_les_polices(pdf, nom):
    """Preuve commitée : Sora et Atkinson figurent dans les PDF rendus par Office (sans les polices installées)."""
    noms = pdf.polices_pdf((OFFICE / "rendus" / nom).read_bytes())
    for attendu in ("Sora-SemiBold", "AtkinsonHyperlegible-Regular", "JetBrainsMono-Regular"):
        assert attendu in noms, (nom, sorted(noms))


def test_preuve_echoue_sans_les_polices(pdf, tmp_path):
    vide = tmp_path / "vide.pdf"
    vide.write_bytes(b"%PDF-1.7\n1 0 obj\n<</Type/Font/BaseFont/Calibri>>\nendobj\n")
    assert pdf.manquantes([vide]) == ["vide.pdf : manquent Sora, Atkinson"]


@pytest.mark.skipif(os.environ.get("CHARTE_VERIFIER_POSTE") != "1", reason="contrôle du poste de rendu, facultatif (CHARTE_VERIFIER_POSTE=1)")
def test_polices_absentes_du_poste(pdf):
    """Sur le poste qui rend les spécimens : aucune police de la charte installée (sinon la preuve ne vaut rien)."""
    assert pdf.installees() == []


def test_type_de_contenu_jamais_silencieux(inc):
    f = inc._type_defaut("odttf", "application/x-test")
    sortie = f(b'<Types xmlns="x"><Override PartName="/a" ContentType="b"/></Types>').decode("utf-8")
    assert sortie.startswith('<Types xmlns="x"><Default Extension="odttf" ContentType="application/x-test"/><Override')
    assert f(sortie.encode("utf-8")).decode("utf-8") == sortie  # idempotent
    with pytest.raises(ValueError, match="sans élément"):
        f(b"<Autre/>")
    with pytest.raises(ValueError, match="inattendu"):
        f(b'<Types><Default Extension="odttf" ContentType="autre"/></Types>')
