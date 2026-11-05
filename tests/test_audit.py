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
