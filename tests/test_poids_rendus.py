"""Poids des rendus commités : au plus ~2 Mo par dossier de spécimens (règle du brief, comme en V2)."""
from pathlib import Path

import pytest

SPECIMENS = Path(__file__).resolve().parent.parent / "specimens"
PLAFOND = 2_000_000  # octets


@pytest.mark.parametrize("dossier", ["html", "office", "graphiques", "readme"])
def test_rendus_sous_le_plafond(dossier):
    rendus = SPECIMENS / dossier / "rendus"
    fichiers = [f for f in rendus.rglob("*") if f.is_file()]
    assert fichiers, f"{rendus} vide"
    total = sum(f.stat().st_size for f in fichiers)
    assert total <= PLAFOND, f"{dossier} : {total} octets > {PLAFOND}"
