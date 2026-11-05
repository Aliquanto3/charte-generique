from couleurs import MACHADO, de00, simule
from daltonisme import VISIONS, analyser, main, paires
from jetons import charger


def test_gris_invariant():
    for vision in MACHADO:
        for gris in ("#808080", "#000000", "#FFFFFF"):
            sim = simule(gris, vision)
            assert de00(gris, sim) < 0.6, (vision, gris, sim)


def test_paires_exhaustives_et_triees():
    p = paires(["#FF0000", "#00FF00", "#0000FF", "#808080"])
    assert len(p) == 6
    assert [x[0] for x in p] == sorted(x[0] for x in p)
    assert {(i, j) for _, i, j in p} == {(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)}


def test_paire_identique_ecart_nul_en_tete():
    d, i, j = paires(["#123456", "#ABCDEF", "#123456"])[0]
    assert (d, i, j) == (0.0, 1, 3)


def test_ordre_pires_paires_stable():
    j = charger()
    a, _ = analyser(j)
    b, _ = analyser(j)
    assert [r["paires"] for r in a] == [r["paires"] for r in b]
    deut = next(r for r in a if r["theme"] == "clair" and r["vision"] == "deuteranopie")
    assert deut["pire4"][1:] == (2, 4)
    assert round(deut["pire4"][0], 1) == 4.4
    assert len(a) == 2 * len(VISIONS)


def test_cli_zero_sur_charte_actuelle(capsys):
    assert main([]) == 0
    assert "Échecs (séries 1 à 4 sous 4) : 0" in capsys.readouterr().out


def test_seuil_reglable_fait_echouer(capsys):
    assert main(["--seuil", "5"]) == 1
    sortie = capsys.readouterr().out
    assert "clair / deuteranopie : cat-2 / cat-4 ΔE00 4.4 < 5" in sortie


def test_markdown(capsys):
    assert main(["--markdown"]) == 0
    assert "| Thème | Vision |" in capsys.readouterr().out
