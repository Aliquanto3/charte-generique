import re
from pathlib import Path

import pytest
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


def _placement():
    import importlib.util

    spec = importlib.util.spec_from_file_location("placement", DOSSIER / "placement.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.placer


def test_placement_sans_chevauchement():
    """A2 : écart minimal entre étiquettes voisines, au plus près des cibles, ordre conservé."""
    placer = _placement()
    assert placer([0, 100, 200], 13.75) == [0, 100, 200]  # rien à déplacer
    assert placer([0, 1, 2], 10) == [-9, 1, 11]  # groupe centré sur la moyenne de ses cibles
    assert placer([5, 0], 10) == [7.5, -2.5]  # résultat dans l'ordre d'entrée
    assert placer([], 10) == []
    cibles = [3.0, 3.5, 4.0, 40.0, 41.0, 90.0, 12.0, 12.2]
    pos = placer(cibles, 13.75)
    tri = sorted(pos)
    assert all(b - a >= 13.75 - 1e-9 for a, b in zip(tri, tri[1:], strict=False))
    assert [cibles[i] for i in sorted(range(8), key=lambda i: pos[i])] == sorted(cibles)  # ordre vertical gardé
    assert abs(sum(pos) - sum(cibles)) < 1e-9  # chaque groupe reste centré : somme des déplacements nulle
    with pytest.raises(ValueError):
        placer([0], -1)


def test_streamlit_sans_bouton_principal():
    """B4 : aucun `type="primary"` dans l'appli témoin."""
    src = (DOSSIER / "streamlit_demo.py").read_text(encoding="utf-8")
    assert "st.button" in src or ".button(" in src
    assert not re.search(r"type\s*=\s*[\"']primary[\"']", src)


def test_rendre_applique_motifs_et_palettes():
    src = (DOSSIER / "rendre.py").read_text(encoding="utf-8")
    for motif in ('MOTIFS["plotly_dash"]', 'MOTIFS["plotly_symbol"]', 'MOTIFS["mpl_hatch"]', "placer(", '"seq"', '"div"'):
        assert motif in src, motif
