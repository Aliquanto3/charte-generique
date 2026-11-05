import copy

from contrastes import main, verifier
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
