import re
from pathlib import Path

from jetons import charger

DOSSIER = Path(__file__).resolve().parent.parent / "specimens" / "graphiques"


def test_aucune_couleur_en_dur_hors_jetons():
    j = charger()
    autorisees = {v.upper() for t in ("sombre", "clair") for v in j[t].values() if isinstance(v, str) and re.fullmatch(r"#[0-9A-F]{6}", v)}
    for f in DOSSIER.glob("*.py"):
        trouvees = set(re.findall(r"#[0-9A-Fa-f]{6}\b", f.read_text(encoding="utf-8")))
        assert {c.upper() for c in trouvees} <= autorisees, f.name


def test_aucune_couleur_en_dur_autre_forme():
    # #RGB, #RRGGBBAA, rgb()/rgba()/hsl() et noms de couleurs passés en argument `color`/`fill`
    motifs = (r"[\"']#[0-9A-Fa-f]{3,4}[\"']", r"#[0-9A-Fa-f]{8}\b", r"\b(?:rgba?|hsla?)\(",
              r"\b(?:color|fill|facecolor|edgecolors?)\s*=\s*[\"'][a-z]+[\"']")
    for f in DOSSIER.glob("*.py"):
        src = f.read_text(encoding="utf-8")
        for m in motifs:
            assert not re.search(m, src), (f.name, m)


def test_scripts_et_rendus_presents():
    assert (DOSSIER / "rendre.py").exists() and (DOSSIER / "streamlit_demo.py").exists()
    assert (DOSSIER / "LISEZMOI.md").exists()
    assert len(list((DOSSIER / "rendus").glob("*-simulation.png"))) == 14


def test_rendre_utilise_les_fichiers_dist():
    src = (DOSSIER / "rendre.py").read_text(encoding="utf-8")
    for motif in ("charte-{theme}.mplstyle", "plotly-{theme}.json", "streamlit-{theme}.toml", "addfont", "MACHADO"):
        assert motif in src
