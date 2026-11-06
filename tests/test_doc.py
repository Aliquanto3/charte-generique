"""docs/CHARTE.md ne doit pas diverger des jetons."""
import json
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


SKILL_DOC = DOC.with_name("SKILL-CHARTE.md")
OUTILS = DOC.parent.parent / "skills" / "charte" / "outils"
OPTIONS_UV = {"--no-project", "--group"}  # options d'uv, pas des outils
SECTIONS = {"init": "installer", "audit": "audit", "migrer": "migrer"}  # titre « ## Mode `x` » -> outil


def _options(outil):
    return set(re.findall(r"add_argument\(\s*[\"'](--[a-z-]+)", (OUTILS / f"{outil}.py").read_text(encoding="utf-8")))


def _sections():
    """Texte de chaque « ## Mode `x` » du skill, par outil. Les renvois `audit --strict` du déroulé de migrer sont retirés."""
    doc = SKILL_DOC.read_text(encoding="utf-8")
    morceaux = re.split(r"^## ", doc, flags=re.MULTILINE)
    out = {}
    for m in morceaux:
        titre = re.match(r"Mode `(\w+)`", m)
        if titre:
            out[SECTIONS[titre.group(1)]] = re.sub(r"`audit --strict`", "", m)
    return out


def _citees(texte):
    return set(re.findall(r"(?<![\w\"-])--[a-z]+(?:-[a-z]+)*", texte)) - OPTIONS_UV


def test_options_du_skill_existent_dans_les_outils():
    """Chaque option citée dans la section d'un outil existe dans l'argparse de cet outil."""
    sections = _sections()
    assert set(sections) == set(SECTIONS.values())
    for outil, texte in sections.items():
        citees = _citees(texte)
        assert citees, outil
        assert citees <= _options(outil) | {"--help"}, (outil, citees - _options(outil))


def test_chaque_option_des_outils_est_documentee():
    for outil, texte in _sections().items():
        for option in _options(outil):
            assert option in _citees(texte), (outil, option)


def test_supports_et_classes_documentes():
    installer = _module(OUTILS / "installer.py", "installer_doc")
    sections = _sections()
    ligne = next(x for x in sections["installer"].splitlines() if x.startswith("- `--supports`"))
    assert set(re.findall(r"`(\w+)`", ligne.split(":", 1)[1])) == set(installer.SUPPORTS)
    for classe in ("charte", "proche", "v1", "hors-charte"):
        assert f"| `{classe}` |" in sections["audit"], classe
    for statut in ("auto", "revoir"):
        assert f"- `{statut}` :" in sections["migrer"], statut


def test_strict_documente_couleurs_et_polices(tmp_path):
    """--strict rend 1 sur une couleur hors-charte, et sur une police seule ; sans lui, 0."""
    audit = _module(OUTILS / "audit.py", "audit_doc")
    sections = _sections()["audit"]
    assert "couleurs ou des polices" in sections
    (tmp_path / "a.css").write_text("p { font-family: Comic Sans MS; }\n", encoding="utf-8")
    assert audit.main([str(tmp_path), "--strict"]) == 1
    assert audit.main([str(tmp_path)]) == 0


def test_commandes_et_fichiers_du_skill_existent():
    doc = SKILL_DOC.read_text(encoding="utf-8")
    racine = DOC.parent.parent
    chemins = re.findall(r'\$\{CLAUDE_PLUGIN_ROOT\}/(skills/charte/[\w/.-]+)', doc)
    assert chemins
    for chemin in chemins:
        assert (racine / chemin).is_file(), chemin
    for nom in ("v1-vers-v2.json", "synonymes.json"):
        assert (racine / "skills" / "charte" / "migrations" / nom).is_file() and f"`{nom}`" in doc, nom
    marche = (racine / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    nom_marche = json.loads(marche)["name"]
    assert f"claude plugin marketplace add Aliquanto3/{nom_marche}" in doc
    assert f"claude plugin install charte@{nom_marche}" in doc
    assert "docs/SKILL-CHARTE.md" in (racine / "README.md").read_text(encoding="utf-8")
