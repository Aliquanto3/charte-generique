"""Génère `dist/` (fichiers prêts à l'emploi pour chaque support) depuis les jetons.

Bibliothèque standard seulement. Les jetons ne sont lus que par `jetons.charger()`.
Sortie déterministe, octet pour octet : LF, ordre stable, zip aux dates fixes.

    uv run --no-project python -I skills/charte/generer.py              # régénère dist/
    uv run --no-project python -I skills/charte/generer.py --sortie X   # écrit dans X
    uv run --no-project python -I skills/charte/generer.py --verifier   # rend 1 si dist/ est périmé
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "outils"))  # `-I` ne met pas le dossier du script dans sys.path

from jetons import GENERIQUES, THEMES, charger  # noqa: E402

DIST = Path(__file__).resolve().parent / "dist"
ENTETE = "Généré par generer.py depuis charte.tokens.json — ne pas modifier"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"


# --- aides -------------------------------------------------------------------------------------

def couleurs(j: dict, theme: str) -> dict[str, str]:
    """Rôles de couleur d'un thème, sans la liste `cat` (les `cat-N` y restent)."""
    return {k: v for k, v in j[theme].items() if k != "cat"}


def jsn(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def sans_diese(c: str) -> str:
    return c.lstrip("#")


def familles_mpl(j: dict, role: str) -> str:
    return ", ".join(f for f in j["police"][role]["familles"] if f in ("serif", "sans-serif", "monospace") or f not in GENERIQUES)


# --- CSS ---------------------------------------------------------------------------------------

def _decl(j: dict, theme: str, indent: str) -> str:
    return "".join(f"{indent}--{k}: {v};\n" for k, v in couleurs(j, theme).items())


def css(j: dict) -> str:
    p = j["police"]
    fixes = [f"--police-titres: {p['titres']['pile']};", f"--police-texte: {p['texte']['pile']};", f"--police-code: {p['code']['pile']};",
             f"--graisse-titres: {p['titres']['graisse']};"]
    fixes += [f"--taille-{k}: {v}px;" for k, v in j["taille"].items()]
    fixes += [f"--espacement-{k}: {v}px;" for k, v in j["espacement"].items()]
    fixes += [f"--rayon-{k}: {v}px;" for k, v in j["rayon"].items()]
    fixes += [f"--trait-largeur: {j['trait']}px;", f"--focus-largeur: {j['focus']['largeur']}px;", f"--focus-decalage: {j['focus']['decalage']}px;"]
    return (
        f"/* {ENTETE} (version {j['version']}). */\n\n"
        ":root {\n  color-scheme: dark;\n" + _decl(j, "sombre", "  ") + "\n" + "".join(f"  {x}\n" for x in fixes) + "}\n\n"
        "@media (prefers-color-scheme: light) {\n"
        '  :root:not([data-theme="sombre"]):not([data-theme="dark"]) {\n    color-scheme: light;\n' + _decl(j, "clair", "    ") + "  }\n}\n\n"
        '[data-theme="clair"],\n[data-theme="light"] {\n  color-scheme: light;\n' + _decl(j, "clair", "  ") + "}\n\n"
        '[data-theme="sombre"],\n[data-theme="dark"] {\n  color-scheme: dark;\n' + _decl(j, "sombre", "  ") + "}\n"
    )


def css_base(j: dict) -> str:
    titres = "".join(f"h{n} {{\n  font-size: var(--taille-titre-{n});\n}}\n\n" for n in range(1, 5))
    return (
        f"/* {ENTETE} (version {j['version']}). Styles minimaux d'éléments ; charger après charte.css. */\n\n"
        "body {\n  margin: 0;\n  background: var(--fond);\n  color: var(--texte);\n  font-family: var(--police-texte);\n  font-size: var(--taille-base);\n"
        "  line-height: 1.5;\n}\n\n"
        "h1, h2, h3, h4 {\n  font-family: var(--police-titres);\n  font-weight: var(--graisse-titres);\n  line-height: 1.2;\n}\n\n"
        + titres +
        "a {\n  color: var(--primaire);\n  text-decoration: underline;\n}\n\n"
        "a:hover {\n  color: var(--primaire-vif);\n}\n\n"
        ":focus-visible {\n  outline: var(--focus-largeur) solid var(--focus);\n  outline-offset: var(--focus-decalage);\n}\n\n"
        "code, pre {\n  font-family: var(--police-code);\n  background: var(--surface-alt);\n}\n\n"
        "::selection {\n  background: var(--primaire-doux);\n}\n"
    )


# --- Python ------------------------------------------------------------------------------------

def _dict_py(nom: str, d: dict) -> str:
    return f"{nom} = {{\n" + "".join(f"    {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n" for k, v in d.items()) + "}\n"


def module_py(j: dict) -> str:
    polices = {r: {"pile": p["pile"], "familles": p["familles"], "graisse": p["graisse"]} for r, p in j["police"].items()}
    return (
        f'"""{ENTETE}.\n\nCharte générique : jetons prêts à l\'emploi, sans dépendance."""\n\n'
        f'VERSION = "{j["version"]}"\n\n'
        + _dict_py("SOMBRE", j["sombre"]) + "\n" + _dict_py("CLAIR", j["clair"]) + "\n"
        + _dict_py("POLICES", polices) + "\n" + _dict_py("TAILLES", j["taille"]) + "\n"
        + _dict_py("ESPACEMENTS", j["espacement"]) + "\n" + _dict_py("RAYONS", j["rayon"]) + "\n"
        + "\ndef theme(nom=\"sombre\"):\n"
        '    """Copie du thème `sombre` ou `clair` (alias `dark`, `light`)."""\n'
        '    themes = {"sombre": SOMBRE, "dark": SOMBRE, "clair": CLAIR, "light": CLAIR}\n'
        "    if nom not in themes:\n"
        '        raise ValueError(f"thème inconnu : {nom!r} (sombre ou clair)")\n'
        "    t = dict(themes[nom])\n"
        '    t["cat"] = list(t["cat"])\n'
        "    return t\n"
    )


# --- matplotlib, plotly, streamlit, mermaid ----------------------------------------------------

def mplstyle(j: dict, theme: str) -> str:
    c = couleurs(j, theme)
    cycle = ", ".join(f"'{sans_diese(c[f'cat-{i}'])}'" for i in range(1, len(j[theme]["cat"]) + 1))
    lignes = [
        f"# {ENTETE} (version {j['version']}).",
        f"axes.prop_cycle: cycler('color', [{cycle}])",
        f"figure.facecolor: {sans_diese(c['fond'])}",
        f"figure.edgecolor: {sans_diese(c['fond'])}",
        f"savefig.facecolor: {sans_diese(c['fond'])}",
        f"axes.facecolor: {sans_diese(c['surface'])}",
        f"axes.edgecolor: {sans_diese(c['trait'])}",
        f"axes.labelcolor: {sans_diese(c['texte'])}",
        f"axes.titlecolor: {sans_diese(c['texte'])}",
        "axes.spines.top: False",
        "axes.spines.right: False",
        "axes.grid: True",
        f"grid.color: {sans_diese(c['trait'])}",
        f"grid.linewidth: {j['trait']}",
        "axes.axisbelow: True",
        f"text.color: {sans_diese(c['texte'])}",
        f"xtick.color: {sans_diese(c['texte-attenue'])}",
        f"ytick.color: {sans_diese(c['texte-attenue'])}",
        f"font.family: {familles_mpl(j, 'texte')}",
        f"font.size: {j['taille']['petit']}",
        f"axes.titlesize: {j['taille']['grand']}",
        f"legend.facecolor: {sans_diese(c['surface'])}",
        f"legend.edgecolor: {sans_diese(c['trait'])}",
        f"legend.labelcolor: {sans_diese(c['texte'])}",
    ]
    return "\n".join(lignes) + "\n"


def plotly(j: dict, theme: str) -> str:
    c = couleurs(j, theme)
    p = j["police"]
    axe = {"gridcolor": c["trait"], "linecolor": c["trait"], "zerolinecolor": c["trait"], "tickfont": {"color": c["texte-attenue"]},
           "title": {"font": {"color": c["texte"]}}}
    return jsn({"layout": {
        "colorway": j[theme]["cat"],
        "paper_bgcolor": c["fond"],
        "plot_bgcolor": c["surface"],
        "font": {"family": p["texte"]["pile"], "color": c["texte"], "size": j["taille"]["petit"]},
        "title": {"font": {"family": p["titres"]["pile"], "color": c["texte"], "size": j["taille"]["titre-4"]}},
        "xaxis": axe,
        "yaxis": axe,
        "legend": {"font": {"color": c["texte"]}},
        "hoverlabel": {"bgcolor": c["surface-alt"], "bordercolor": c["trait"], "font": {"family": p["texte"]["pile"], "color": c["texte"]}},
    }})


def _toml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def streamlit(j: dict, theme: str) -> str:
    c = couleurs(j, theme)
    p = j["police"]
    cles = [
        ("base", theme_base(theme)), ("primaryColor", c["primaire"]), ("backgroundColor", c["fond"]),
        ("secondaryBackgroundColor", c["surface-alt"]), ("textColor", c["texte"]), ("linkColor", c["primaire"]),
        ("borderColor", c["trait"]), ("font", p["texte"]["pile"]), ("headingFont", p["titres"]["pile"]),
        ("codeFont", p["code"]["pile"]), ("baseRadius", f"{j['rayon']['moyen']}px"),
    ]
    corps = "".join(f"{k} = {_toml_str(v)}\n" for k, v in cles)
    corps += "chartCategoricalColors = [" + ", ".join(_toml_str(x) for x in j[theme]["cat"]) + "]\n"
    return (
        f"# {ENTETE} (version {j['version']}).\n"
        "# Exception connue à la règle « le bleu n'est jamais un aplat de bouton » : Streamlit remplit le bouton\n"
        "# principal en primaryColor, avec un texte qu'il choisit lui-même. On y met donc `primaire`.\n"
        "[theme]\n" + corps
    )


def theme_base(theme: str) -> str:
    return "dark" if theme == "sombre" else "light"


def mermaid(j: dict, theme: str) -> str:
    c = couleurs(j, theme)
    tv = {
        "background": c["fond"], "primaryColor": c["surface-alt"], "primaryTextColor": c["texte"], "primaryBorderColor": c["primaire"],
        "lineColor": c["texte-attenue"], "secondaryColor": c["surface"], "tertiaryColor": c["primaire-doux"],
        "fontFamily": j["police"]["texte"]["pile"], "noteBkgColor": c["accent-doux"], "noteTextColor": c["texte"],
    }
    tv.update({f"cScale{i}": x for i, x in enumerate(j[theme]["cat"])})
    return jsn({"theme": "base", "themeVariables": tv})


# --- Office ------------------------------------------------------------------------------------

def theme_office(j: dict) -> str:
    c = couleurs(j, "clair")
    schema = [("dk1", c["texte"]), ("lt1", c["surface"]), ("dk2", c["encre-pleine"]), ("lt2", c["fond"])]
    schema += [(f"accent{i}", c[f"cat-{i}"]) for i in range(1, 7)]
    schema += [("hlink", c["primaire"]), ("folHlink", c["primaire-vif"])]
    coul = "".join(f'      <a:{k}><a:srgbClr val="{sans_diese(v)}"/></a:{k}>\n' for k, v in schema)
    p = j["police"]
    remplissage = '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    ligne = '<a:ln w="{w}" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f"<!-- {ENTETE} (version {j['version']}). -->\n"
        f'<a:theme xmlns:a="{NS_A}" name="Charte générique">\n'
        "  <a:themeElements>\n"
        '    <a:clrScheme name="Charte générique">\n' + coul + "    </a:clrScheme>\n"
        '    <a:fontScheme name="Charte générique">\n'
        f'      <a:majorFont><a:latin typeface="{p["titres"]["familles"][0]}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>\n'
        f'      <a:minorFont><a:latin typeface="{p["texte"]["familles"][0]}"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>\n'
        "    </a:fontScheme>\n"
        '    <a:fmtScheme name="Charte générique">\n'
        f"      <a:fillStyleLst>{remplissage}{remplissage}{remplissage}</a:fillStyleLst>\n"
        f"      <a:lnStyleLst>{ligne.format(w=6350)}{ligne.format(w=12700)}{ligne.format(w=19050)}</a:lnStyleLst>\n"
        "      <a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>"
        "<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>\n"
        f"      <a:bgFillStyleLst>{remplissage}{remplissage}{remplissage}</a:bgFillStyleLst>\n"
        "    </a:fmtScheme>\n"
        "  </a:themeElements>\n"
        "</a:theme>\n"
    )


def thmx(xml_theme: str) -> bytes:
    import io

    entete = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    ns_rel = "http://schemas.openxmlformats.org/package/2006/relationships"
    # PowerPoint n'ouvre le paquet que si la racine pointe (officeDocument) vers un themeManager qui référence le thème.
    parties = [
        ("[Content_Types].xml",
         entete + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
         '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
         '<Default Extension="xml" ContentType="application/xml"/>'
         '<Override PartName="/theme/theme/themeManager.xml" ContentType="application/vnd.openxmlformats-officedocument.themeManager+xml"/>'
         '<Override PartName="/theme/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
         "</Types>"),
        ("_rels/.rels",
         entete + f'<Relationships xmlns="{ns_rel}"><Relationship Id="rId1" Type="{rel}officeDocument" Target="theme/theme/themeManager.xml"/>'
         '</Relationships>'),
        ("theme/theme/themeManager.xml", entete + f'<a:themeManager xmlns:a="{NS_A}"/>'),
        ("theme/theme/_rels/themeManager.xml.rels",
         entete + f'<Relationships xmlns="{ns_rel}"><Relationship Id="rId1" Type="{rel}theme" Target="theme1.xml"/></Relationships>'),
        ("theme/theme/theme1.xml", xml_theme),
    ]
    tampon = io.BytesIO()
    with zipfile.ZipFile(tampon, "w") as z:
        for nom, contenu in parties:
            info = zipfile.ZipInfo(nom, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED  # pas de dépendance à la version de zlib
            info.create_system = 3
            info.external_attr = 0o644 << 16
            z.writestr(info, contenu.encode("utf-8"))
    return tampon.getvalue()


# --- SVG ---------------------------------------------------------------------------------------

def pictogramme(j: dict) -> str:
    s = j["sombre"]
    return (
        f"<!-- {ENTETE} (version {j['version']}). -->\n"
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" focusable="false">\n'
        f'  <rect width="32" height="32" rx="8" fill="var(--primaire, {s["primaire"]})"/>\n'
        f'  <path d="M9 10h14M9 16h9M9 22h14" stroke="var(--sur-primaire, {s["sur-primaire"]})" stroke-width="3" stroke-linecap="round"/>\n'
        f'  <circle cx="23" cy="16" r="2.5" fill="var(--accent, {s["accent"]})"/>\n'
        "</svg>\n"
    )


def favicon(j: dict) -> str:
    s, c = j["sombre"], j["clair"]

    def regles(t: dict, indent: str) -> str:
        return (f"{indent}.t {{ fill: {t['primaire']}; }}\n{indent}.b {{ stroke: {t['sur-primaire']}; }}\n"
                f"{indent}.p {{ fill: {t['accent']}; }}\n")

    return (
        f"<!-- {ENTETE} (version {j['version']}). -->\n"
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">\n'
        "  <style>\n" + regles(s, "    ") + "    @media (prefers-color-scheme: light) {\n" + regles(c, "      ") + "    }\n  </style>\n"
        '  <rect class="t" width="32" height="32" rx="8"/>\n'
        '  <path class="b" d="M9 10h14M9 16h9M9 22h14" fill="none" stroke-width="3" stroke-linecap="round"/>\n'
        '  <circle class="p" cx="23" cy="16" r="2.5"/>\n'
        "</svg>\n"
    )


# --- orchestration -----------------------------------------------------------------------------

def fichiers(j: dict) -> dict[str, bytes]:
    """Nom → contenu, dans un ordre stable."""
    xml = theme_office(j)
    texte = {
        "charte.css": css(j),
        "charte-base.css": css_base(j),
        "charte.py": module_py(j),
    }
    for t in THEMES:
        texte[f"charte-{t}.mplstyle"] = mplstyle(j, t)
        texte[f"plotly-{t}.json"] = plotly(j, t)
        texte[f"streamlit-{t}.toml"] = streamlit(j, t)
        texte[f"mermaid-{t}.json"] = mermaid(j, t)
    texte["theme-office.xml"] = xml
    texte["pictogramme.svg"] = pictogramme(j)
    texte["favicon.svg"] = favicon(j)
    out = {k: v.encode("utf-8") for k, v in texte.items()}
    out["charte.thmx"] = thmx(xml)
    return dict(sorted(out.items()))


def ecrire(j: dict, dossier: Path) -> list[str]:
    dossier.mkdir(parents=True, exist_ok=True)
    f = fichiers(j)
    for nom, contenu in f.items():
        (dossier / nom).write_bytes(contenu)
    return list(f)


def differences(j: dict, dossier: Path) -> list[str]:
    attendu = fichiers(j)
    reel = {p.name for p in dossier.iterdir() if p.is_file()} if dossier.is_dir() else set()
    diff = [n for n, c in attendu.items() if not (dossier / n).is_file() or (dossier / n).read_bytes() != c]
    return sorted(set(diff) | (reel - set(attendu)))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sortie", type=Path, help="dossier de sortie (défaut : skills/charte/dist)")
    ap.add_argument("--jetons", type=Path, help="fichier de jetons (défaut : celui du dépôt)")
    ap.add_argument("--verifier", action="store_true", help="compare dist/ à une régénération ; rend 1 s'il y a un écart")
    a = ap.parse_args(argv)
    j = charger(a.jetons)
    if a.verifier:
        with tempfile.TemporaryDirectory() as tmp:
            ecrire(j, Path(tmp))
            diff = differences(j, a.sortie or DIST)
        if diff:
            print("dist/ n'est pas à jour, fichiers différents :")
            for n in diff:
                print(f"  {n}")
            return 1
        print("dist/ est à jour.")
        return 0
    cible = a.sortie or DIST
    noms = ecrire(j, cible)
    print(f"{len(noms)} fichiers écrits dans {cible}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
