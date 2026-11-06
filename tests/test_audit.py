"""Audit de charte sur un dépôt factice."""
import json

import audit
from jetons import charger

J = charger()


def depot(tmp_path, fichiers: dict[str, str]):
    for nom, contenu in fichiers.items():
        p = tmp_path / nom
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(contenu, encoding="utf-8")
    return tmp_path


def classes(res, type_="couleur"):
    return [(k["valeur"], k["classe"]) for k in res["constats"] if k["type"] == type_]


def test_css_v2_sans_hors_charte(tmp_path):
    css = f":root {{ --fond: {J['sombre']['fond']}; --texte: {J['clair']['texte']}; }}\n"
    res = audit.auditer(depot(tmp_path, {"a.css": css}))
    assert res["resume"]["couleurs"] == {"charte": 2, "proche": 0, "v1": 0, "hors-charte": 0}


def test_valeur_v1_classee_v1(tmp_path):
    v1 = audit.charger_v1()["roles"]["relief"]["clair"]
    res = audit.auditer(depot(tmp_path, {"a.css": f"a {{ color: {v1}; }}\n"}))
    (k,) = [k for k in res["constats"] if k["type"] == "couleur"]
    assert k["classe"] == "v1" and k["roles_v1"] == ["relief"] and k["roles_v2"] == ["(supprimé)"]


def test_couleur_etrangere_hors_charte_avec_jeton_proche(tmp_path):
    res = audit.auditer(depot(tmp_path, {"a.css": "a { color: #00FF00; }\n"}))
    (k,) = res["constats"]
    assert k["classe"] == "hors-charte" and k["delta_e"] >= audit.SEUIL_PROCHE and ":" in k["jeton"]


def test_proche_sous_le_seuil(tmp_path):
    h = J["clair"]["fond"]
    presque = "#" + format(int(h[1:3], 16) - 1, "02X") + h[3:]
    (k,) = audit.auditer(depot(tmp_path, {"a.css": f"a {{ color: {presque}; }}\n"}))["constats"]
    assert k["classe"] == "proche" and k["delta_e"] < 3 and "fond" in k["jeton"]


def test_ancres_et_identifiants_ignores(tmp_path):
    md = "Voir [le point](#123) et l'issue #123, #abc et #fff dans le texte.\n<a href=\"#add\">x</a>\n"
    html = '<div id="#bad">x</div>\n'
    res = audit.auditer(depot(tmp_path, {"a.md": md, "b.html": html}))
    assert res["constats"] == []


def test_contextes_de_couleur_reconnus(tmp_path):
    res = audit.auditer(depot(tmp_path, {
        "a.svg": '<rect fill="#112233"/>\n',
        "b.py": 'COULEUR = "#445566"\n',
        "c.json": '{"c": "#778899"}\n',
        "d.js": "el.style.color = 'rgb(10, 20, 30)'; x = hsl(120, 100%, 50%);\n",
        "e.css": ".a { background: rgba(1, 2, 3, 0.5); }\n",
    }))
    valeurs = {k["valeur"] for k in res["constats"]}
    assert valeurs == {"#112233", "#445566", "#778899", "rgb(10, 20, 30)", "hsl(120, 100%, 50%)", "rgba(1, 2, 3, 0.5)"}


def test_selecteur_css_et_binaires_ignores(tmp_path):
    d = depot(tmp_path, {"a.css": "#abc { margin: 0; }\n", "dist/b.css": "a { color: #123456; }\n", "c.min.css": "a{color:#123456}\n"})
    (d / "d.css").write_bytes(b"a { color: #123456; }\0")
    assert audit.auditer(d)["constats"] == []
    avec = audit.auditer(depot(tmp_path, {"x.css": "a { color: #123456; }\n", "y/z.css": "a { color: #654321; }\n"}), ["y/"])
    assert [k["valeur"] for k in avec["constats"]] == ["#123456"]


def test_polices(tmp_path):
    ok = J["police"]["texte"]["pile"]
    css = f"h1 {{ font-family: Fredoka, sans-serif; }}\np {{ font-family: {ok}; }}\nq {{ font-family: 'Comic Neue', serif; }}\n"
    res = audit.auditer(depot(tmp_path, {"a.css": css}))
    assert classes(res, "police") == [("Fredoka", "v1"), ("Comic Neue", "hors-charte")]


def test_strict(tmp_path, capsys):
    propre = depot(tmp_path / "p", {"a.css": f"a {{ color: {J['clair']['texte']}; }}\n"})
    sale = depot(tmp_path / "s", {"a.css": "a { color: #00FF00; }\n"})
    assert audit.main([str(sale)]) == 0
    assert audit.main([str(sale), "--strict"]) == 1
    assert audit.main([str(propre), "--strict"]) == 0
    assert "Couleurs : 0 charte, 0 proche, 0 v1, 1 hors-charte. Polices : 0 v1, 0 hors-charte." in capsys.readouterr().out


def test_json_valide(tmp_path, capsys):
    d = depot(tmp_path, {"a.css": "a { color: #00FF00; }\n"})
    assert audit.main([str(d), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["resume"]["couleurs"]["hors-charte"] == 1
    assert data["constats"][0]["fichier"] == "a.css" and data["constats"][0]["ligne"] == 1


def test_markdown(tmp_path, capsys):
    d = depot(tmp_path, {"a.css": "a { color: #00FF00; }\n"})
    audit.main([str(d), "--markdown"])
    sortie = capsys.readouterr().out
    assert "| Classe | Fichier |" in sortie and "| hors-charte | `a.css` | 1 | `#00FF00` |" in sortie


def test_raccourci_font_reconnu():
    assert [n for n, _, _ in audit.polices_ligne("h1 { font: italic 700 2rem/1.2 Fredoka, sans-serif; }")] == ["Fredoka"]
    assert audit.polices_ligne("p { font: inherit; }") == []


def test_fichiers_non_suivis_lus_dans_un_depot_git(tmp_path):
    import subprocess
    d = depot(tmp_path, {"suivi.css": "a { color: #123456; }\n"})
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    subprocess.run(["git", "-C", str(d), "add", "suivi.css"], check=True)
    (d / "neuf.css").write_text("a { color: #654321; }\n", encoding="utf-8")
    (d / ".gitignore").write_text("ignore.css\n", encoding="utf-8")
    (d / "ignore.css").write_text("a { color: #222222; }\n", encoding="utf-8")
    fichiers = {r.as_posix() for r, _ in audit.lire_fichiers(d)}
    assert {"suivi.css", "neuf.css"} <= fichiers and "ignore.css" not in fichiers


def test_cp1252_lu_et_signale_bom_retire(tmp_path):
    (tmp_path / "a.css").write_bytes("/* thème */ a { color: #123456; }\n".encode("cp1252"))
    (tmp_path / "t.toml").write_bytes(b"\xef\xbb\xbf[theme]\nprimaryColor = \"#123456\"\n")
    enc, avert = {}, []
    textes = dict(audit.lire_fichiers(tmp_path, None, enc, avert))
    assert enc == {audit.Path("a.css"): "cp1252", audit.Path("t.toml"): "utf-8-sig"}
    assert textes[audit.Path("t.toml")].startswith("[theme]")
    res = audit.auditer(tmp_path)
    assert res["avertissements"] == ["a.css : pas en UTF-8, lu en cp1252"]
    assert "Avertissement : a.css" in audit.texte(res, False)


def test_selecteurs_js_ignores():
    assert audit.couleurs_ligne('document.querySelector("#add").hidden = true;', ".js") == []
    assert audit.couleurs_ligne("$('#bed').show();", ".js") == []
    assert [c["hex"] for c in audit.couleurs_ligne('const c = "#add";', ".js")] == ["#AADDDD"]


def test_hsl_negatif_ne_plante_pas():
    assert audit._fonction("hsl", "-10 -20% 150%") == ("#FFFFFF", "")
    assert audit._fonction("hsl", "200 -50% 50%") == ("#808080", "")


# --- Recette 2.9 -------------------------------------------------------------

def test_dossiers_d_outils_ignores_par_defaut(tmp_path):
    css = "a { color: #00FF00; }\n"
    d = depot(tmp_path, {"app/a.css": css, ".claude/b.css": css, "_bmad-output/c.css": css, "node_modules/x/d.css": css,
                         ".venv/e.css": css, "archive/f.css": css})
    res = audit.auditer(d)
    assert {k["fichier"] for k in res["constats"]} == {"app/a.css"}


def test_archive_ignore_a_la_racine_seulement(tmp_path):
    css = "a { color: #00FF00; }\n"
    d = depot(tmp_path, {"archive/a.css": css, "archives/b.css": css, "templates/archive/c.css": css, "archive.css": css})
    assert {k["fichier"] for k in audit.auditer(d)["constats"]} == {"templates/archive/c.css", "archive.css"}


def test_liens_de_bouton_ou_de_navigation_non_signales(tmp_path):
    css = ("nav a { text-decoration: none; }\na.btn { text-decoration: none; }\n.menu > a { text-decoration: none; }\n"
           ".tabs a { text-decoration: none; }\ntable a { text-decoration: none; }\n")
    avert = audit.auditer(depot(tmp_path, {"style.css": css}))["avertissements"]
    assert [a for a in avert if "lien" in a] == ["revoir : style.css:5 lien (`table a`) sans soulignement de remplacement (la charte souligne les liens)"]


def test_selecteur_groupe_garde_le_lien_du_texte(tmp_path):
    avert = audit.auditer(depot(tmp_path, {"s.css": "nav a, .article a { text-decoration: none; }\n"}))["avertissements"]
    assert any("lien" in a and ".article a" in a for a in avert)


def test_favicon_et_pictogramme_absents_signales(tmp_path):
    res = audit.auditer(depot(tmp_path, {"index.html": "<html></html>\n"}))
    avert = res["avertissements"]
    assert any(a.startswith("revoir : aucun favicon") and "--seulement favicon" in a for a in avert)
    assert any(a.startswith("revoir : aucun pictogramme") and "--seulement pictogramme" in a for a in avert)
    res = audit.auditer(depot(tmp_path / "b", {"index.html": "<html></html>\n", "static/favicon.svg": "<svg/>", "pictogramme.svg": "<svg/>"}))
    assert res["avertissements"] == []
    assert audit.auditer(depot(tmp_path / "c", {"a.css": "a { }\n"}))["avertissements"] == []  # pas de page HTML


def test_lien_sans_soulignement_de_remplacement_signale(tmp_path):
    res = audit.auditer(depot(tmp_path, {"a.css": ".article a {\n  text-decoration: none;\n}\n"}))
    (a,) = res["avertissements"]
    assert a == "revoir : a.css:1 lien (`.article a`) sans soulignement de remplacement (la charte souligne les liens)"
    ok = audit.auditer(depot(tmp_path / "b", {"a.css": "a { text-decoration: none; }\na:hover { text-decoration: underline; }\n"}))
    assert ok["avertissements"] == []
    ok2 = audit.auditer(depot(tmp_path / "c", {"a.css": ".btn { text-decoration: none; }\n"}))
    assert ok2["avertissements"] == []
