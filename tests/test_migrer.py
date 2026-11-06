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
    assert "Aucun thème sombre détecté" in p and '[data-theme="dark"]' in p and "prefers-color-scheme: light" in p
    assert lire(d, "a.css") == MAISON
    lancer(d, "--proposer", "--appliquer", "--ajouter-sombre")
    css = lire(d, "a.css")
    bloc = css[css.index("/* Sombre d'abord"):]
    assert "prefers-color-scheme: light" in bloc and '[data-theme="dark"]' in bloc
    valeurs = {ligne.split(":")[1].strip(" ;") for ligne in bloc[:bloc.index("@media")].splitlines() if ligne.strip().startswith("--")}
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


def test_classe_dark_header_ni_fichier_darkroom_ne_basculent_le_theme(tmp_path):
    p = V1["roles"]["primaire"]
    d = depot(tmp_path, {"a.css": f".dark-header {{ --color-primary: {p['clair']}; }}\n.light-x {{ --color-primary: {p['sombre']}; }}\n",
                         "darkroom.css": f":root {{ --color-primary: {p['clair']}; }}\n",
                         "highlight.css": f":root {{ --color-primary: {p['sombre']}; }}\n"})
    par = {(e["fichier"], e["ancien"]): e["nouveau"] for e in plan(d)}
    assert par[("a.css", p["clair"])] == v2("clair", "primaire")
    assert par[("a.css", p["sombre"])] == v2("sombre", "primaire")
    assert par[("darkroom.css", p["clair"])] == v2("clair", "primaire")
    assert par[("highlight.css", p["sombre"])] == v2("sombre", "primaire")
    assert migrer.theme_nom("theme-dark.css") == "sombre" and migrer.theme_nom("darkTheme.ts") == "sombre"
    assert migrer.theme_nom("highlight.toml") is None


def test_plan_dans_le_depot_n_est_pas_un_theme_sombre(tmp_path):
    d = depot(tmp_path, {"a.css": MAISON})
    lancer(d, "--proposer", "--plan", str(d / "plan.md"))
    assert "prefers-color-scheme: light" in lire(d, "plan.md")
    res = migrer.planifier(d, [], migrer.Contexte(None, True))
    assert not res["sombre_present"] and res["blocs"]
    lancer(d, "--proposer", "--plan", str(d / "plan.md"))
    assert "Aucun thème sombre détecté" in lire(d, "plan.md")


def test_encodage_cp1252_conserve_a_l_ecriture(tmp_path):
    p = V1["roles"]["primaire"]["clair"]
    (tmp_path / "a.css").write_bytes(f"/* thème */ :root {{ --color-primary: {p}; }}\n".encode("cp1252"))
    lancer(tmp_path, "--appliquer")
    assert (tmp_path / "a.css").read_bytes().decode("cp1252") == f"/* thème */ :root {{ --color-primary: {v2('clair', 'primaire')}; }}\n"


# --- Recette 2.9 -------------------------------------------------------------

def bloc_apres(css, debut):
    return css[css.index(debut):]


def test_sombre_d_abord_par_defaut(tmp_path):
    d = depot(tmp_path, {"a.css": ":root { --encre: #202020; --primaire: #345678; }\n"})
    lancer(d, "--proposer", "--appliquer", "--ajouter-sombre")
    css = lire(d, "a.css")
    _, _, bas = css.partition("/* Sombre d'abord")
    assert "prefers-color-scheme: dark" not in css
    racine, _, media = bas.partition("@media (prefers-color-scheme: light)")
    assert ':root,\n[data-theme="dark"] {' in racine
    assert f"--encre: {v2('sombre', 'texte')};" in racine
    assert f"--primaire: {v2('sombre', 'primaire')};" in racine
    clair, _, light = media.partition('[data-theme="light"] {')
    assert ':root:not([data-theme="dark"])' in clair
    assert f"--primaire: {v2('clair', 'primaire')};" in clair
    assert f"--primaire: {v2('clair', 'primaire')};" in light


def test_clair_d_abord_garde_l_ancienne_structure(tmp_path):
    d = depot(tmp_path, {"a.css": ":root { --encre: #202020; }\n"})
    lancer(d, "--proposer", "--appliquer", "--ajouter-sombre", "--clair-d-abord")
    bloc = bloc_apres(lire(d, "a.css"), "/* Thème sombre")
    assert "@media (prefers-color-scheme: dark)" in bloc and '[data-theme="dark"] {' in bloc
    assert "prefers-color-scheme: light" not in bloc


def test_variable_deja_egale_a_un_jeton_clair_recoit_son_sombre(tmp_path):
    d = depot(tmp_path, {"a.css": f":root {{ --carte: {v2('clair', 'surface')}; --encre: #202020; }}\n"})
    lancer(d, "--proposer", "--appliquer", "--ajouter-sombre")
    bloc = bloc_apres(lire(d, "a.css"), "/* Sombre d'abord")
    assert f"  --carte: {v2('sombre', 'surface')};" in bloc.split("@media")[0]
    assert f"    --carte: {v2('clair', 'surface')};" in bloc


def test_valeur_egale_a_plusieurs_jetons_clairs_est_signalee_revoir(tmp_path):
    d = depot(tmp_path, {"a.css": ":root { --zzz: #FFFFFF; }\n"})
    e = [x for x in plan(d) if x["ancien"] == "#FFFFFF"]
    assert len(e) == 1 and e[0]["statut"] == "revoir" and "contrepartie sombre à choisir" in e[0]["note"]
    res = migrer.planifier(d, [], migrer.Contexte(None, False))
    assert res["blocs"] == {}


def test_variable_a_eclater_texte_et_aplat(tmp_path):
    css = (":root { --accent-x: #345678; --seul: #345678; }\n"
           "a { color: var(--accent-x); }\n.puce { background: var(--accent-x); }\n.t { color: var(--seul); }\n")
    e = [x for x in plan(depot(tmp_path, {"a.css": css})) if x["nouveau"] == "(à éclater)"]
    assert [x["ancien"] for x in e] == ["--accent-x"] and e[0]["statut"] == "revoir" and e[0]["ligne"] == 1
    assert "texte : a.css:2 (color)" in e[0]["note"] and "aplat : a.css:3 (background)" in e[0]["note"]


FACE_V1 = """@font-face {
  font-family: "Fredoka";
  src: url("fonts/fredoka-regular.woff2") format("woff2");
  font-weight: 400;
}
:root { --police-titres: 'Fredoka', cursive; --police-texte: Arial, sans-serif; --taille-police: 16px; }
"""


def test_font_face_renomme_famille_src_et_graisse(tmp_path):
    d = depot(tmp_path, {"a.css": FACE_V1})
    lancer(d, "--appliquer")
    css = lire(d, "a.css")
    assert 'font-family: "Sora";' in css and 'url("fonts/sora-latin-600-normal.woff2")' in css and "font-weight: 600;" in css
    assert f"--police-titres: {J['police']['titres']['pile']};" in css
    assert "--police-texte: Arial, sans-serif;" in css and "--taille-police: 16px;" in css  # revoir, jamais appliqué
    apres = css
    lancer(d, "--appliquer")
    assert lire(d, "a.css") == apres


def test_font_face_police_absente_donne_la_commande_installer(tmp_path):
    d = depot(tmp_path, {"a.css": FACE_V1})
    e = plan(d, proposer=True)
    absent = [x for x in e if "absent du dépôt" in x["note"]]
    assert len(absent) == 1 and "installer.py" in absent[0]["note"] and "--seulement polices" in absent[0]["note"]
    d2 = depot(tmp_path / "b", {"a.css": FACE_V1, "fonts/sora-latin-600-normal.woff2": "x"})
    assert not [x for x in plan(d2) if "absent du dépôt" in x["note"]]


def test_pile_hors_charte_proposee_en_revoir(tmp_path):
    e = [x for x in plan(depot(tmp_path, {"a.css": FACE_V1})) if x["ancien"] == "Arial, sans-serif"]
    assert e[0]["statut"] == "revoir" and e[0]["nouveau"] == J["police"]["texte"]["pile"]


def test_aplat_primaire_hors_bouton_est_liste(tmp_path):
    css = ":root { --primaire: #345678; }\nnav { background: var(--primaire); }\n.badge { background-color: var(--primaire); }\n"
    e = [x for x in plan(depot(tmp_path, {"a.css": css})) if x["nouveau"] == "(à décider)"]
    assert [x["ligne"] for x in e] == [2, 3] and all(x["statut"] == "revoir" for x in e)
    assert "`nav`" in e[0]["note"] and "`.badge`" in e[1]["note"]


def test_message_du_plan_dit_ou_il_est_ecrit(tmp_path, capsys):
    d = depot(tmp_path / "depot", {"a.css": MAISON})
    dehors = tmp_path / "plan.md"
    lancer(d, "--plan", str(dehors))
    assert f"Plan écrit dans {dehors} (hors du dépôt : rien à commiter)" in capsys.readouterr().out
    lancer(d, "--plan", str(d / "plan.md"))
    assert "(dans le dépôt : ne le commitez pas)" in capsys.readouterr().out


def test_font_face_plusieurs_graisses_double_signale(tmp_path):
    css = ('@font-face {\n  font-family: Fredoka;\n  font-weight: 400;\n  src: url(f/fredoka-400.woff2);\n}\n'
           '@font-face {\n  font-family: Fredoka;\n  font-weight: 700;\n  src: url(f/fredoka-700.woff2);\n}\n'
           '@font-face {\n  font-family: Fredoka;\n  font-style: italic;\n  font-weight: 400;\n  src: url(f/fredoka-i.woff2);\n}\n')
    doubles = [x for x in plan(depot(tmp_path, {"a.css": css})) if x["nouveau"] == "(à supprimer)"]
    assert [x["ligne"] for x in doubles] == [6] and doubles[0]["statut"] == "revoir"
    assert "graisse d'origine 700" in doubles[0]["note"] and "ligne 1" in doubles[0]["note"]


def test_pile_de_police_garde_important(tmp_path):
    d = depot(tmp_path, {"a.css": ":root { --police-titres: 'Fredoka', cursive !important; }\n"})
    lancer(d, "--appliquer")
    assert lire(d, "a.css") == f":root {{ --police-titres: {J['police']['titres']['pile']} !important; }}\n"
