"""Migration v1 vers v2 sur un dépôt factice : les valeurs v2 viennent toujours de charger()."""
import json

import audit
import migrer
from jetons import charger

J = charger()
V1 = audit.charger_v1()


def depot(tmp_path, fichiers: dict[str, str]):
    for nom, contenu in fichiers.items():
        p = tmp_path / nom
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenu, encoding="utf-8")
    return tmp_path


def lancer(d, *args):
    return migrer.main([str(d), *args])


def plan(d, proposer=False, corr=None):
    return migrer.planifier(d, [], migrer.Contexte(corr, proposer))["entrees"]


def lire(d, nom):
    return (d / nom).read_text(encoding="utf-8")


def v2(theme, role):
    return J[theme][role]


def variables(css):
    return {k.split(":")[0].strip(): k.split(":")[1].strip(" ;") for k in css.splitlines() if k.startswith("  --")}


def test_css_v1_clair_et_sombre_migre_vers_charger(tmp_path):
    p = V1["roles"]["primaire"]
    css = (f":root {{ --color-primary: {p['clair']}; }}\n"
           "@media (prefers-color-scheme: dark) {\n"
           f"  :root {{ --color-primary: {p['sombre']}; }}\n}}\n")
    d = depot(tmp_path / "depot", {"a.css": css})
    assert lancer(d, "--appliquer", "--plan", str(tmp_path / "plan.md")) == 0
    assert lire(d, "a.css") == css.replace(p["clair"], v2("clair", "primaire")).replace(p["sombre"], v2("sombre", "primaire"))
    assert "| auto |" in (tmp_path / "plan.md").read_text(encoding="utf-8")


def test_deuxieme_passe_ne_change_rien(tmp_path, capsys):
    d = depot(tmp_path, {"a.css": f":root {{ --color-primary: {V1['roles']['primaire']['clair']}; --x: #123456; }}\n"})
    lancer(d, "--appliquer")
    apres = lire(d, "a.css")
    capsys.readouterr()
    lancer(d, "--appliquer")
    assert lire(d, "a.css") == apres
    assert "Fichiers modifiés : 0" in capsys.readouterr().out


def test_plan_seul_n_ecrit_rien(tmp_path):
    css = f"a {{ color: {V1['roles']['primaire']['clair']}; }}\n"
    d = depot(tmp_path, {"a.css": css})
    lancer(d)
    assert lire(d, "a.css") == css


def test_relief_donne_revoir_et_reste_inchange(tmp_path):
    val = V1["roles"]["relief"]["clair"]
    d = depot(tmp_path, {"a.css": f"a {{ box-shadow: 0 2px 0 {val}; }}\n"})
    (e,) = plan(d)
    assert (e["statut"], e["role"], e["ancien"]) == ("revoir", "relief", val)
    assert "n'existe plus" in e["note"]
    lancer(d, "--appliquer")
    assert val in lire(d, "a.css")


def test_primaire_fonce_revoir(tmp_path):
    d = depot(tmp_path, {"a.css": f"a {{ color: {V1['roles']['primaire-fonce']['clair']}; }}\n"})
    (e,) = plan(d)
    assert e["statut"] == "revoir" and e["nouveau"] == v2("clair", "primaire-vif") and "sens change" in e["note"]


AMBIGUE = "#123456"  # valeur arbitraire, déclarée ci-dessous comme partagée par deux rôles v1


def ctx_ambigu():
    ctx = migrer.Contexte()
    ctx.v1val = {**ctx.v1val, AMBIGUE: [("primaire", "clair"), ("fond", "clair")]}
    return ctx


def test_valeur_ambigue_sans_nom_reste_inchangee(tmp_path):
    css = f"a {{ border-color: {AMBIGUE}; }}\n"
    d = depot(tmp_path, {"a.css": css})
    res = migrer.planifier(d, [], ctx_ambigu())
    (e,) = res["entrees"]
    assert e["statut"] == "revoir" and "ne tranche pas" in e["note"]
    migrer.appliquer(d, res, False)
    assert lire(d, "a.css") == css


def test_valeur_ambigue_tranchee_par_le_nom(tmp_path):
    d = depot(tmp_path, {"a.css": f":root {{ --color-primary: {AMBIGUE}; --page: {AMBIGUE}; }}\n"})
    migrer.appliquer(d, migrer.planifier(d, [], ctx_ambigu()), False)
    assert lire(d, "a.css") == f":root {{ --color-primary: {v2('clair', 'primaire')}; --page: {v2('clair', 'fond')}; }}\n"


def test_bouton_primaire_revoir(tmp_path):
    val = V1["roles"]["primaire"]["clair"]
    css = f".btn-principal {{ background: {val}; }}\n.btn {{ background: var(--color-primary); }}\n.lien {{ color: {val}; }}\n"
    d = depot(tmp_path, {"a.css": css})
    e = plan(d)
    assert [x["statut"] for x in e] == ["revoir", "revoir", "auto"]
    assert e[1]["ancien"] == "var(--color-primary)"
    lancer(d, "--appliquer")
    lignes = lire(d, "a.css").splitlines()
    assert lignes[0] == f".btn-principal {{ background: {val}; }}"
    assert v2("clair", "primaire") in lignes[2]


def test_police_fredoka_vers_titres(tmp_path):
    d = depot(tmp_path, {"a.css": "h1 { font-family: Fredoka, sans-serif; }\n"})
    lancer(d, "--appliquer")
    assert lire(d, "a.css") == f"h1 {{ font-family: {J['police']['titres']['familles'][0]}, sans-serif; }}\n"


def test_casse_et_alpha_conserves(tmp_path):
    val = V1["roles"]["primaire"]["clair"]
    d = depot(tmp_path, {"a.css": f"a {{ color: {val.lower()}; fill: {val}80; }}\n"})
    lancer(d, "--appliquer")
    assert lire(d, "a.css") == f"a {{ color: {v2('clair', 'primaire').lower()}; fill: {v2('clair', 'primaire')}80; }}\n"


def test_roles_cibles_existent_dans_charger():
    for role, d in V1["roles"].items():
        if d["cible"] is None:
            assert d["statut"] == "revoir", role
            continue
        for t in ("clair", "sombre"):
            assert d["cible"] in J[t], (role, t)
    for role in V1["polices"].values():
        assert role in J["police"]
    # Les cibles du bouton (bouton, sur-bouton) sont tolérées absentes si 2.7 ne les a pas encore apportées.
    assert set(V1["bouton"]["cibles"]) <= set(V1["roles"])


# --- --proposer, --correspondances, --ajouter-sombre ---

MAISON = """:root {
  --fond: #F2F2F2;
  --carte: #FDFDFD;
  --bordure: #D0D0D0;
  --encre: #202020;
  --encre-secondaire: #606060;
  --primaire: #345678;
  --lavande: #A090D0;
  --succes-fond: #E0F0E0;
  --succes-texte: #206030;
  --erreur-fond: #F8E0E0;
  --erreur-texte: #A02020;
  --logo: #12DD55;
}
.carte { background: var(--carte); border: 1px solid var(--bordure); }
"""


def test_proposer_par_synonymes(tmp_path):
    d = depot(tmp_path, {"a.css": MAISON})
    par_valeur = {e["ancien"]: (e["role"], e["statut"]) for e in plan(d, proposer=True)}
    attendu = {"#F2F2F2": "fond", "#FDFDFD": "surface", "#D0D0D0": "trait", "#202020": "texte", "#606060": "texte-attenue",
               "#345678": "primaire", "#E0F0E0": "succes-doux", "#206030": "succes", "#F8E0E0": "erreur-doux", "#A02020": "erreur"}
    for ancien, role in attendu.items():
        assert par_valeur[ancien] == (role, "auto"), ancien
    for ancien in ("#A090D0", "#12DD55"):  # sans synonyme : jeton le plus proche, à revoir
        assert par_valeur[ancien][1] == "revoir"


def test_sans_proposer_rien_hors_table_v1(tmp_path):
    assert plan(depot(tmp_path, {"a.css": MAISON})) == []


def test_proposer_applique_seulement_les_exacts(tmp_path):
    d = depot(tmp_path, {"a.css": MAISON})
    migrer.appliquer(d, migrer.planifier(d, [], migrer.Contexte(None, True)), False)
    css = lire(d, "a.css")
    assert "#A090D0" in css and "#12DD55" in css  # revoir : inchangés
    v = variables(css)
    assert v["--fond"] in (v2("clair", "fond"), v2("sombre", "fond"))
    assert v["--carte"] in (v2("clair", "surface"), v2("sombre", "surface"))


def test_correspondances_prioritaires_et_idempotentes(tmp_path):
    d = depot(tmp_path, {"a.css": MAISON})
    corr = tmp_path / "corr.json"
    corr.write_text(json.dumps({"--lavande": "primaire-doux", "--logo": "accent", "--carte": "surface-alt"}), encoding="utf-8")
    lancer(d, "--appliquer", "--correspondances", str(corr))
    css = lire(d, "a.css")
    lig = variables(css)
    th = migrer.Contexte().meilleur_theme
    assert lig["--lavande"] == v2(th("primaire-doux", "#A090D0"), "primaire-doux")
    assert lig["--logo"] == v2(th("accent", "#12DD55"), "accent")
    assert lig["--carte"] == v2(th("surface-alt", "#FDFDFD"), "surface-alt")  # prioritaire sur le synonyme surface
    assert lig["--bordure"] == "#D0D0D0"  # pas de --proposer : inchangé
    lancer(d, "--appliquer", "--correspondances", str(corr))
    assert lire(d, "a.css") == css


def test_correspondance_null_supprime_si_inutilisee_sinon_signale(tmp_path):
    d = depot(tmp_path, {"a.css": MAISON})
    assert plan(d) == []  # sans correspondances chargées
    res = migrer.planifier(d, [], migrer.Contexte({"--lavande": None, "--carte": None}))
    par = {x["ancien"]: x for x in res["entrees"]}
    assert (par["--lavande"]["statut"], par["--lavande"]["nouveau"]) == ("auto", "(supprimée)")
    assert par["--carte"]["statut"] == "revoir" and "encore utilisée (1 usages)" in par["--carte"]["note"]
    migrer.appliquer(d, res, False)
    css = lire(d, "a.css")
    assert "--lavande" not in css and "--carte: #FDFDFD;" in css
    assert "\n\n" not in css


def test_clair_seul_propose_puis_ajoute_le_bloc_sombre(tmp_path, capsys):
    d = depot(tmp_path / "depot", {"a.css": MAISON})
    lancer(d, "--proposer", "--plan", str(tmp_path / "plan.md"))
    p = (tmp_path / "plan.md").read_text(encoding="utf-8")
    assert "Aucun thème sombre détecté" in p and '[data-theme="dark"]' in p and "prefers-color-scheme: dark" in p
    assert lire(d, "a.css") == MAISON
    lancer(d, "--proposer", "--appliquer", "--ajouter-sombre")
    css = lire(d, "a.css")
    bloc = css[css.index("/* Thème sombre"):]
    assert "prefers-color-scheme: dark" in bloc and '[data-theme="dark"]' in bloc
    valeurs = {ligne.split(":")[1].strip(" ;") for ligne in bloc.splitlines() if ligne.strip().startswith("--")}
    assert valeurs <= {v for v in J["sombre"].values() if isinstance(v, str)}
    assert J["sombre"]["surface"] in valeurs and J["sombre"]["texte"] in valeurs
    capsys.readouterr()
    lancer(d, "--proposer", "--appliquer", "--ajouter-sombre")  # idempotent : le thème sombre existe désormais
    assert lire(d, "a.css") == css
    assert "Fichiers modifiés : 0" in capsys.readouterr().out


def test_pas_de_bloc_sans_flag_ni_si_sombre_present(tmp_path):
    d = depot(tmp_path, {"a.css": MAISON})
    lancer(d, "--proposer", "--appliquer")
    assert "Thème sombre" not in lire(d, "a.css")
    d2 = depot(tmp_path / "b", {"a.css": MAISON + "@media (prefers-color-scheme: dark) { :root { --fond: #101010; } }\n"})
    assert migrer.planifier(d2, [], migrer.Contexte(None, True))["blocs"] == {}


def test_cles_toml_et_constantes_python(tmp_path):
    d = depot(tmp_path, {"t.toml": '[theme]\nprimaryColor = "#345678"\nbackground = "#F2F2F2"\n', "c.py": 'CARTE = "#FDFDFD"\nAUTRE = "#A090D0"\n'})
    e = {x["ancien"]: x for x in plan(d, proposer=True)}
    assert e["#F2F2F2"]["role"] == "fond" and e["#FDFDFD"]["role"] == "surface"
    assert e["#A090D0"]["statut"] == "revoir"
