"""generer.py : dist/ est à jour, déterministe, et ses valeurs égalent les jetons."""
import importlib.util
import json
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from jetons import CHEMIN, charger

RACINE = Path(__file__).resolve().parent.parent
GENERER = RACINE / "skills" / "charte" / "generer.py"
DIST = RACINE / "skills" / "charte" / "dist"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def lancer(*args):
    return subprocess.run([sys.executable, "-I", str(GENERER), *args], capture_output=True, text=True, encoding="utf-8")


@pytest.fixture(scope="module")
def j():
    return charger()


def test_verifier_vert():
    r = lancer("--verifier")
    assert r.returncode == 0, r.stdout
    assert "à jour" in r.stdout


def test_generation_identique_a_dist(tmp_path):
    assert lancer("--sortie", str(tmp_path)).returncode == 0
    noms = sorted(p.name for p in tmp_path.iterdir())
    assert noms == sorted(p.name for p in DIST.iterdir() if p.is_file())
    for n in noms:
        octets = (tmp_path / n).read_bytes()
        assert octets == (DIST / n).read_bytes(), n
        if not n.endswith(".thmx"):
            assert b"\r" not in octets, n


def test_jetons_modifies_changent_la_sortie(tmp_path):
    copie = tmp_path / "jetons.json"
    texte = CHEMIN.read_text(encoding="utf-8")
    h = charger()["sombre"]["primaire"].lstrip("#")
    assert h.upper() in texte.upper()
    copie.write_text(re.sub(h, "010203", texte, flags=re.IGNORECASE), encoding="utf-8")
    sortie = tmp_path / "out"
    assert lancer("--jetons", str(copie), "--sortie", str(sortie)).returncode == 0
    assert "#010203" in (sortie / "charte.css").read_text(encoding="utf-8")
    assert (sortie / "charte.css").read_bytes() != (DIST / "charte.css").read_bytes()
    r = lancer("--jetons", str(copie), "--verifier")
    assert r.returncode == 1
    assert "charte.css" in r.stdout


def _bloc_css(css, entete):
    m = re.search(re.escape(entete) + r" \{(.*?)\n\s*\}", css, re.DOTALL)
    assert m, entete
    return dict(re.findall(r"--([a-z0-9-]+): ([^;]+);", m.group(1)))


@pytest.mark.parametrize("theme", ["sombre", "clair"])
def test_css(j, theme):
    css = (DIST / "charte.css").read_text(encoding="utf-8")
    attendu = {k: v for k, v in j[theme].items() if k != "cat"}
    assert "Généré par generer.py depuis charte.tokens.json — ne pas modifier" in css
    assert j["version"] in css.splitlines()[0]
    forces = {"sombre": '[data-theme="sombre"],\n[data-theme="dark"]', "clair": '[data-theme="clair"],\n[data-theme="light"]'}[theme]
    bloc = _bloc_css(css, forces)
    assert {k: bloc[k] for k in attendu} == attendu
    if theme == "clair":
        media = css.split("@media (prefers-color-scheme: light)")[1].split("\n}\n")[0]
        assert ':root:not([data-theme="sombre"]):not([data-theme="dark"])' in media
        assert {k: v for k, v in re.findall(r"--([a-z0-9-]+): ([^;]+);", media) if k in attendu} == attendu
    else:
        racine = css.split(":root {")[1].split("\n}\n")[0]
        assert "color-scheme: dark;" in racine
        assert {k: v for k, v in re.findall(r"--([a-z0-9-]+): ([^;]+);", racine) if k in attendu} == attendu
    fixes = _bloc_css(css, ":root")
    assert fixes["police-titres"] == j["police"]["titres"]["pile"]
    assert fixes["graisse-titres"] == "600"
    assert fixes["taille-titre-1"] == "48px"
    assert fixes["espacement-8"] == "64px"
    assert fixes["rayon-pilule"] == "999px"
    assert (fixes["trait-largeur"], fixes["focus-largeur"], fixes["focus-decalage"]) == ("1px", "2px", "2px")


def test_css_base():
    base = (DIST / "charte-base.css").read_text(encoding="utf-8")
    for var in ("--fond", "--texte", "--police-texte", "--primaire-vif", "--focus", "--surface-alt", "--primaire-doux", "--taille-titre-4"):
        assert f"var({var})" in base
    assert not re.search(r"#[0-9A-Fa-f]{6}", base)


def test_module_python(j):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("charte_dist", DIST / "charte.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert m.VERSION == j["version"]
    assert m.SOMBRE == j["sombre"]
    assert m.CLAIR == j["clair"]
    assert m.TAILLES == j["taille"] and m.ESPACEMENTS == j["espacement"] and m.RAYONS == j["rayon"]
    assert m.POLICES["titres"]["pile"] == j["police"]["titres"]["pile"]
    assert m.theme() == j["sombre"]
    assert m.theme("clair") == j["clair"]
    m.theme("clair")["cat"].append("x")
    assert len(m.CLAIR["cat"]) == 8
    with pytest.raises(ValueError, match="thème inconnu"):
        m.theme("rose")


def _mpl(chemin):
    d = {}
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if ligne and not ligne.startswith("#"):
            k, v = ligne.split(": ", 1)
            d[k] = v
    return d


@pytest.mark.parametrize("theme", ["sombre", "clair"])
def test_mplstyle(j, theme):
    d = _mpl(DIST / f"charte-{theme}.mplstyle")
    c = j[theme]
    assert d["axes.prop_cycle"] == "cycler('color', [" + ", ".join(f"'{x[1:]}'" for x in c["cat"]) + "])"
    assert d["figure.facecolor"] == c["fond"][1:]
    assert d["axes.facecolor"] == c["surface"][1:]
    assert d["text.color"] == c["texte"][1:]
    assert d["grid.color"] == c["trait"][1:]
    assert d["axes.spines.top"] == d["axes.spines.right"] == "False"
    assert d["font.family"] == "Atkinson Hyperlegible, Segoe UI, Roboto, sans-serif"


@pytest.mark.parametrize("theme", ["sombre", "clair"])
def test_mplstyle_charge_par_matplotlib(j, theme):
    """Hors CI (groupe `specimens`) : matplotlib accepte chaque clé et chaque valeur."""
    mpl = pytest.importorskip("matplotlib")
    rc = mpl.rc_params_from_file(DIST / f"charte-{theme}.mplstyle", use_default_template=False)
    assert len(rc) == len(_mpl(DIST / f"charte-{theme}.mplstyle"))  # matplotlib écarte (et journalise) clé ou valeur invalide
    assert rc["axes.prop_cycle"].by_key()["color"] == j[theme]["cat"]
    assert rc["axes.facecolor"] == j[theme]["surface"]
    assert rc["font.family"] == ["Atkinson Hyperlegible", "Segoe UI", "Roboto", "sans-serif"]


@pytest.mark.parametrize("theme", ["sombre", "clair"])
def test_plotly(j, theme):
    lay = json.loads((DIST / f"plotly-{theme}.json").read_text(encoding="utf-8"))["layout"]
    c = j[theme]
    assert lay["colorway"] == c["cat"]
    assert (lay["paper_bgcolor"], lay["plot_bgcolor"]) == (c["fond"], c["surface"])
    assert lay["font"]["color"] == c["texte"]
    assert lay["xaxis"]["gridcolor"] == lay["yaxis"]["gridcolor"] == c["trait"]
    assert lay["hoverlabel"]["bgcolor"] == c["surface-alt"]


@pytest.mark.parametrize("theme", ["sombre", "clair"])
def test_streamlit(j, theme):
    brut = (DIST / f"streamlit-{theme}.toml").read_text(encoding="utf-8")
    assert "Exception connue" in brut
    t = tomllib.loads(brut)["theme"]
    c = j[theme]
    assert t["base"] == ("dark" if theme == "sombre" else "light")
    assert t["primaryColor"] == t["linkColor"] == c["primaire"]
    assert t["backgroundColor"] == c["fond"]
    assert t["secondaryBackgroundColor"] == c["surface-alt"]
    assert t["textColor"] == c["texte"] and t["borderColor"] == c["trait"]
    assert t["font"] == j["police"]["texte"]["pile"] and t["headingFont"] == j["police"]["titres"]["pile"]
    assert t["codeFont"] == j["police"]["code"]["pile"]
    assert t["baseRadius"] == "10px"
    assert t["chartCategoricalColors"] == c["cat"]
    assert len(t) == 12


@pytest.mark.parametrize("theme", ["sombre", "clair"])
def test_mermaid(j, theme):
    m = json.loads((DIST / f"mermaid-{theme}.json").read_text(encoding="utf-8"))
    v, c = m["themeVariables"], j[theme]
    assert m["theme"] == "base"
    assert (v["background"], v["primaryColor"], v["primaryBorderColor"]) == (c["fond"], c["surface-alt"], c["primaire"])
    assert v["primaryTextColor"] == v["noteTextColor"] == c["texte"]
    assert v["fontFamily"] == j["police"]["texte"]["pile"]
    assert v["cScale0"] == c["cat-1"] and v["cScale7"] == c["cat-8"]


def test_office(j):
    c = j["clair"]
    racine = ET.parse(DIST / "theme-office.xml").getroot()
    assert racine.tag == f"{A}theme" and racine.get("name") == "Charte générique"
    schema = {e.tag[len(A):]: e[0].get("val") for e in racine.find(f"{A}themeElements/{A}clrScheme")}
    attendu = {"dk1": c["texte"], "lt1": c["surface"], "dk2": c["encre-pleine"], "lt2": c["fond"], "hlink": c["primaire"], "folHlink": c["primaire-vif"]}
    attendu.update({f"accent{i}": c[f"cat-{i}"] for i in range(1, 7)})
    assert len(schema) == 12
    assert schema == {k: v[1:] for k, v in attendu.items()}
    # Ordre imposé par le schéma OOXML (CT_ColorScheme, CT_StyleMatrix) : PowerPoint rejette un autre ordre.
    ordre = ["dk1", "lt1", "dk2", "lt2", *(f"accent{i}" for i in range(1, 7)), "hlink", "folHlink"]
    assert list(schema) == ordre
    fmt = racine.find(f"{A}themeElements/{A}fmtScheme")
    assert [e.tag[len(A):] for e in fmt] == ["fillStyleLst", "lnStyleLst", "effectStyleLst", "bgFillStyleLst"]
    assert all(len(e) == 3 for e in fmt)
    assert [e.tag[len(A):] for e in racine.find(f"{A}themeElements")] == ["clrScheme", "fontScheme", "fmtScheme"]
    fonts = racine.find(f"{A}themeElements/{A}fontScheme")
    assert fonts.find(f"{A}majorFont/{A}latin").get("typeface") == "Sora"
    assert fonts.find(f"{A}minorFont/{A}latin").get("typeface") == "Atkinson Hyperlegible"
    assert racine.find(f"{A}themeElements/{A}fmtScheme") is not None


def test_thmx():
    with zipfile.ZipFile(DIST / "charte.thmx") as z:
        assert z.namelist() == ["[Content_Types].xml", "_rels/.rels", "theme/theme/themeManager.xml",
                                "theme/theme/_rels/themeManager.xml.rels", "theme/theme/theme1.xml"]
        assert all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in z.infolist())
        assert z.read("theme/theme/theme1.xml") == (DIST / "theme-office.xml").read_bytes()
        ET.fromstring(z.read("[Content_Types].xml"))
        assert b"theme/theme/themeManager.xml" in z.read("_rels/.rels")
        assert b'Target="theme1.xml"' in z.read("theme/theme/_rels/themeManager.xml.rels")


def test_svg(j):
    s, c = j["sombre"], j["clair"]
    pic = (DIST / "pictogramme.svg").read_text(encoding="utf-8")
    ET.fromstring(pic)
    assert 'aria-hidden="true"' in pic
    # var() dans une propriété `style`, pas dans un attribut de présentation (repli non garanti partout).
    assert f'style="fill: var(--primaire, {s["primaire"]})"' in pic
    assert f'style="stroke: var(--sur-primaire, {s["sur-primaire"]})"' in pic
    assert f'style="fill: var(--accent, {s["accent"]})"' in pic
    assert not re.search(r'(fill|stroke)="var\(', pic)
    fav = (DIST / "favicon.svg").read_text(encoding="utf-8")
    ET.fromstring(fav)
    assert "var(" not in fav
    avant, apres = fav.split("@media (prefers-color-scheme: light)")
    assert s["primaire"] in avant and c["primaire"] in apres and c["accent"] in apres
