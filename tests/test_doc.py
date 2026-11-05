"""docs/CHARTE.md ne doit pas diverger des jetons."""
import re
from pathlib import Path

from jetons import SERIES, charger

DOC = Path(__file__).resolve().parent.parent / "docs" / "CHARTE.md"
VALEUR = r"#[0-9A-F]{6}|rgba\([^)]*\)|0 [^|]+?"  # hexadécimal, rgba() ou box-shadow
LIGNE = re.compile(rf"^\| `([a-z0-9-]+)` \| ({VALEUR}) \| ({VALEUR}) \|", re.MULTILINE)


def test_tables_egales_aux_jetons():
    j = charger()
    lignes = LIGNE.findall(DOC.read_text(encoding="utf-8"))
    roles_doc = {role for role, _, _ in lignes}
    assert len(lignes) >= 40
    for role, sombre, clair in lignes:
        assert (sombre, clair) == (j["sombre"][role], j["clair"][role]), role
    attendus = {k for k in j["sombre"] if k not in SERIES}
    assert attendus == roles_doc, attendus ^ roles_doc


def test_version_du_titre():
    assert DOC.read_text(encoding="utf-8").startswith(f"# Charte générique v{charger()['version'].rsplit('.', 1)[0]}")


def test_regles_v2_1_presentes():
    """La v2.1 décrit chaque support et renvoie aux corrections de la critique."""
    doc = DOC.read_text(encoding="utf-8")
    for titre in ("### Web", "### Impression et niveaux de gris", "### Diapositives", "### Rapport", "### README et badges",
                  "### Aperçu social", "### Streamlit", "### Graphiques", "### Office", "## Changements depuis la v2.0"):
        assert titre in doc, titre
    changements = doc.split("## Changements depuis la v2.0", 1)[1]
    for n in ("A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A10", "A11", "A12", "B1", "B2", "B3", "B4", "B5"):
        assert f"**{n}" in changements or f", {n}**" in changements, n
    for seuil in ("au moins 28 pt", "six séries", "dès cinq séries", "dès deux séries en clair", "au-delà de quatre séries",
                  "au moins 64 px", "sous 28 px", "80 px", 'jamais `type="primary"`', "Segoe UI Semibold"):
        assert seuil.lower() in doc.lower(), seuil
