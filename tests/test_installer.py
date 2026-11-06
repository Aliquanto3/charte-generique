"""Installation de la charte dans un dépôt cible."""
import installer
import pytest


def test_copie_les_fichiers_du_support(tmp_path):
    assert installer.main(["--cible", str(tmp_path), "--supports", "web,readme"]) == 0
    base = tmp_path / "static" / "charte"
    assert (base / "charte.css").read_bytes() == (installer.DIST / "charte.css").read_bytes()
    assert (base / "mermaid-clair.json").is_file()
    assert (base / "polices" / "sora-latin-600-normal.woff2").is_file()
    assert (base / "polices" / "OFL-sora.txt").is_file()
    assert not (base / "charte.py").exists()  # support python non demandé


def test_dossier_personnalise_et_extrait(tmp_path, capsys):
    assert installer.main(["--cible", str(tmp_path), "--supports", "readme", "--dossier", "docs/charte"]) == 0
    assert (tmp_path / "docs" / "charte" / "pictogramme.svg").is_file()
    assert not (tmp_path / "docs" / "charte" / "polices").exists()  # readme sans police
    sortie = capsys.readouterr().out
    assert "`docs/charte/`" in sortie and "CLAUDE.md" in sortie


def test_refuse_d_ecraser_sans_forcer(tmp_path, capsys):
    args = ["--cible", str(tmp_path), "--supports", "web"]
    assert installer.main(args) == 0
    cible = tmp_path / "static" / "charte" / "charte.css"
    cible.write_text("local", encoding="utf-8")
    assert installer.main(args) == 1
    assert "refus d'écraser" in capsys.readouterr().err
    assert cible.read_text(encoding="utf-8") == "local"
    assert installer.main([*args, "--forcer"]) == 0
    assert cible.read_bytes() == (installer.DIST / "charte.css").read_bytes()


def test_support_inconnu(tmp_path, capsys):
    assert installer.main(["--cible", str(tmp_path), "--supports", "web,fax"]) == 1
    assert "support inconnu : fax" in capsys.readouterr().err
    assert not (tmp_path / "static").exists()


def test_sources_existent():
    for dest, src in installer.plan(list(installer.SUPPORTS)).items():
        assert src.is_file(), dest


def test_plan_rejette_support_inconnu():
    with pytest.raises(ValueError):
        installer.plan(["x"])


def test_seulement_polices_favicon_pictogramme(tmp_path):
    args = ["--cible", str(tmp_path), "--supports", "web", "--seulement", "polices,favicon,pictogramme"]
    assert installer.main(args) == 0
    base = tmp_path / "static" / "charte"
    assert sorted(p.relative_to(base).as_posix() for p in base.rglob("*") if p.is_file()) == sorted(
        [f"polices/{n}" for n in [*installer.WOFF2, *installer.LICENCES]] + ["favicon.svg", "pictogramme.svg"])
    assert not (base / "charte.css").exists()


def test_seulement_inconnu_ou_vide_refuse(tmp_path, capsys):
    assert installer.main(["--cible", str(tmp_path), "--supports", "readme", "--seulement", "polices"]) == 1
    assert "aucun fichier correspondant" in capsys.readouterr().err
    assert installer.main(["--cible", str(tmp_path), "--supports", "web", "--seulement", "css"]) == 0
    assert sorted(p.name for p in (tmp_path / "static" / "charte").iterdir()) == ["charte-base.css", "charte.css"]
    for vide in [",", "", " , "]:
        assert installer.main(["--cible", str(tmp_path / "v"), "--supports", "web", "--seulement", vide]) == 1
        assert "--seulement vide" in capsys.readouterr().err
    assert not (tmp_path / "v").exists()


def test_licences_nommees_selon_la_convention():
    """polices/OFL-<famille en minuscules, sans espace ni tiret>.txt, pour chaque famille de la charte."""
    from jetons import charger
    attendu = {"OFL-" + r["familles"][0].lower().replace(" ", "").replace("-", "") + ".txt" for r in charger()["police"].values()}
    assert attendu == set(installer.LICENCES)
    assert all((installer.POLICES / n).is_file() for n in attendu)
