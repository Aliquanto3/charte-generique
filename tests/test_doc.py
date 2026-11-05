"""docs/CHARTE.md ne doit pas diverger des jetons."""
import re
from pathlib import Path

from jetons import charger

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
    attendus = {k for k in j["sombre"] if k != "cat"}
    assert attendus == roles_doc, attendus ^ roles_doc


def test_version_du_titre():
    assert DOC.read_text(encoding="utf-8").startswith(f"# Charte générique v{charger()['version'].rsplit('.', 1)[0]}")
