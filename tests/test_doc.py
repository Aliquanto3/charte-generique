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


def _module(chemin, nom):
    import importlib.util

    spec = importlib.util.spec_from_file_location(nom, chemin)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_seuils_de_la_doc_egaux_aux_constantes():
    """Les seuils chiffrés de la doc sont ceux qu'appliquent les spécimens (constantes du code)."""
    racine = DOC.parent.parent
    office = _module(racine / "specimens" / "office" / "construire.py", "construire_doc")
    apercu = _module(racine / "specimens" / "readme" / "generer_bannieres.py", "bannieres_doc")
    doc = DOC.read_text(encoding="utf-8").lower()
    nombres = {2: "deux", 5: "cinq", 6: "six"}
    assert f"titres d'au moins {office.TITRE_DIAPO_PT} pt" in doc
    assert f"au plus {nombres[office.SERIES_DIAPO]} séries" in doc
    assert f"étiquette de données dès {nombres[office.ETIQUETTE_DONNEES_DES]} séries" in doc
    assert f"dès {nombres[office.ETIQUETTE_CLAIR_DES]} séries en clair" in doc
    assert f"titre d'au moins {apercu.TITRE_APERCU_MIN} px" in doc
    assert f"aucun texte sous {apercu.TEXTE_APERCU_MIN} px" in doc
    assert f"marges sûres de {apercu.MARGE_APERCU} px" in doc
    assert f"{apercu.APERCU[0]} × {apercu.APERCU[1]}" in doc
