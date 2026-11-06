from couleurs import MACHADO, de00, ecart_minimal, simule
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
    # égalités de ΔE00 départagées par indices, quel que soit l'ordre d'entrée des couleurs égales
    assert [(i, j) for _, i, j in paires(["#336699"] * 4)] == [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    a, _ = analyser(charger())
    for r in a:
        sim = None if r["vision"] == "normale" else r["vision"]
        assert r["pire8"] == r["paires"][0]
        assert r["pire4"] == next(x for x in r["paires"] if x[2] <= 4)
        cats = [charger()[r["theme"]][f"cat-{n}"] for n in range(1, 9)]
        assert r["pire4"] == ecart_minimal(cats[:4], sim)
    deut = next(r for r in a if r["theme"] == "clair" and r["vision"] == "deuteranopie")
    assert deut["pire4"][1:] == (3, 4)
    assert round(deut["pire4"][0], 1) == 9.9
    assert len(a) == 2 * len(VISIONS)


def test_permutation_a1_ordres_de_grandeur():
    """A1 (cat-4 et cat-5 permutées) : pire paire 1 à 4 en deutéranopie ≥ 9 en clair, ≥ 13 en sombre."""
    a, _ = analyser(charger())
    pire = {r["theme"]: r["pire4"][0] for r in a if r["vision"] == "deuteranopie"}
    assert pire["clair"] >= 9 and pire["sombre"] >= 13, pire
    assert round(pire["clair"], 1) == 9.9 and round(pire["sombre"], 1) == 13.7
    j = charger()
    assert (j["clair"]["cat-4"], j["clair"]["cat-5"]) == ("#B83A75", "#C24D1B")  # framboise puis corail
    assert (j["sombre"]["cat-4"], j["sombre"]["cat-5"]) == ("#E58FB8", "#F2A07B")


def test_cli_zero_sur_charte_actuelle(capsys):
    assert main([]) == 0
    assert "Échecs (séries 1 à 4 sous 4) : 0" in capsys.readouterr().out


def test_seuil_reglable_fait_echouer(capsys):
    assert main(["--seuil", "10"]) == 1
    sortie = capsys.readouterr().out
    assert "clair / deuteranopie : cat-3 / cat-4 ΔE00 9.9 < 10" in sortie
    assert main(["--seuil", "8"]) == 0  # pire paire 1 à 4, toutes visions : sombre tritanopie 8,2


def test_markdown(capsys):
    assert main(["--markdown"]) == 0
    lignes = capsys.readouterr().out.splitlines()
    assert lignes[0] == "| Thème | Vision | Pire paire 1 à 4 | Pire paire 1 à 8 |"
    resume = [x for x in lignes[2:] if x.startswith("| ") and x.count("|") == 5]
    assert len(resume) == 2 * len(VISIONS)
    assert any(x.startswith("| clair | deuteranopie | cat-3/cat-4 9.9 |") for x in resume)
    assert sum(x.startswith("| cat-") for x in lignes) == 28 * 2 * len(VISIONS)
