import copy

from contrastes import GITHUB_CLAIR, GITHUB_SOMBRE, main, paires_pictogramme, pas_voisins, verifier
from couleurs import contraste, de00, melange, simule
from jetons import charger


def test_charte_zero_echec():
    _, echecs = verifier(charger())
    assert echecs == []


def test_cli_rend_zero(tmp_path, capsys):
    assert main(["--eviter", str(tmp_path / "absent.json")]) == 0
    assert "Échecs : 0" in capsys.readouterr().out


def test_echec_detecte():
    j = copy.deepcopy(charger())
    j["clair"]["texte-attenue"] = "#AAAAAA"
    _, echecs = verifier(j)
    assert any("texte-attenue" in e for e in echecs)


def test_couleur_a_eviter_detectee():
    j = charger()
    _, echecs = verifier(j, {"témoin": j["sombre"]["primaire"]})
    assert any("témoin" in e for e in echecs)


def test_reperes_wcag():
    assert round(contraste("#000000", "#FFFFFF"), 2) == 21.0
    assert round(contraste("#777777", "#FFFFFF"), 2) == 4.48


def test_reperes_couleur():
    assert de00("#123456", "#123456") == 0
    assert melange("#FFFFFF", "#000000", 0.5) == "#808080"
    assert 0 < de00("#FF0000", "#FE0000") < 1
    # Le gris est invariant en dyschromatopsie
    assert simule("#808080", "deuteranopie") == "#808080"


def _paire(j, theme, debut):
    return next(p for p in paires_pictogramme(j) if p[0] == theme and p[1].startswith(debut))


def test_paires_pictogramme_a4():
    """Point ≥ 3:1 sur la tuile, tuile ≥ 3:1 sur `fond` et `encre-pleine`, valeurs sombres sur aplat sombre (A4)."""
    j = charger()
    point_clair = _paire(j, "clair", "point")
    assert point_clair[2:5] == ("#E0B54A", "tuile primaire", "#1D5BC2")  # accent-aplat sur primaire
    assert round(contraste(point_clair[2], point_clair[4]), 2) == 3.27
    point_sombre = _paire(j, "sombre", "point")
    assert contraste(point_sombre[2], point_sombre[4]) >= 3
    # l'or sombre sur la tuile sombre ne passe pas : c'est pourquoi le point sombre n'est pas `accent`
    assert contraste(j["sombre"]["accent"], j["sombre"]["primaire"]) < 1.3
    sur_aplat = [p for p in paires_pictogramme(j) if p[0] == "sombre sur aplat clair"]
    assert [round(contraste(p[2], p[4]), 2) for p in sur_aplat] == [8.22, 10.35]
    assert all(contraste(p[2], p[4]) >= p[5] for p in paires_pictogramme(j))


def test_paire_pictogramme_en_echec_detectee():
    j = copy.deepcopy(charger())
    j["clair"]["accent-aplat"] = j["clair"]["primaire"]
    _, echecs = verifier(j)
    assert any("point accent-aplat/tuile primaire" in e for e in echecs)


def test_badge_sur_pages_github():
    j = charger()
    assert (GITHUB_SOMBRE, GITHUB_CLAIR) == ("#0D1117", "#FFFFFF")
    b = j["clair"]["badge-etiquette"]
    assert round(contraste("#FFFFFF", b), 2) == 5.17
    assert round(contraste(b, j["sombre"]["fond"]), 2) == 3.60 and round(contraste(b, j["clair"]["fond"]), 2) == 4.86
    assert contraste(b, GITHUB_SOMBRE) >= 3 and contraste(b, GITHUB_CLAIR) >= 3


def test_palettes_pas_voisins():
    j = charger()
    for t in ("sombre", "clair"):
        for palette in ("seq", "div"):
            for vision in ("normale", "deuteranopie"):
                assert pas_voisins(j[t][palette], vision)[0] >= 9.4, (t, palette, vision)
    assert pas_voisins(["#000000", "#000000", "#FFFFFF"]) == (0.0, 1)


def test_palette_trop_serree_detectee():
    j = copy.deepcopy(charger())
    j["clair"]["seq"] = [melange(j["clair"]["primaire"], j["clair"]["surface"], p) for p in (0.2, 0.3, 0.4, 0.5, 0.6)]
    _, echecs = verifier(j)
    assert any(e.startswith("clair seq-") and "normale" in e for e in echecs)


def test_couleur_a_eviter_nouveaux_jetons():
    j = charger()
    _, echecs = verifier(j, {"témoin": j["clair"]["div-4"]})
    assert any("div-4" in e and "témoin" in e for e in echecs)
