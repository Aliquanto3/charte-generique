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
