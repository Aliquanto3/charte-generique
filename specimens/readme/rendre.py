"""Génère badges.md et README-temoin.md, puis les rendus PNG (Edge headless, mmdc si dispo).

Règle README (A8) : diagramme mermaid en thème `neutral` dans le bloc de code, rendus de référence clair et sombre
sous `<picture>` avec repli clair ; bannière en `<picture>`, repli clair ; étiquette de badge `badge-etiquette`.

Usage : uv run --no-project python -I specimens/readme/rendre.py
Prérequis : generer_bannieres.py déjà lancé.
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "skills" / "charte" / "outils"))
import couleurs  # noqa: E402
import jetons  # noqa: E402

ICI = Path(__file__).resolve().parent
RENDUS = ICI / "rendus"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
DIST = RACINE / "skills" / "charte" / "dist"
INIT_MERMAID = {"theme": "neutral"}  # GitHub : thème neutre, lisible sur les deux pages
# Couleurs imposées par shields.io (badge-maker), hors charte : servent seulement à mesurer
# le contraste du texte que shields.io choisira (#fff, ou #333 si luminosité > 0,69).
BLANC, SOMBRE = "#FFFFFF", "#333333"


def texte_shields(h: str) -> str:
    r, g, b = couleurs._rvb(h)
    return SOMBRE if (r * 299 + g * 587 + b * 114) / 255000 > 0.69 else BLANC


def badges() -> list[dict]:
    """Un badge par statut, couleur du thème clair ; repli sur une variante lisible (>= 4,5)."""
    c = jetons.charger()["clair"]
    candidats = {
        "succès": ["succes"], "alerte": ["alerte", "alerte-texte"], "erreur": ["erreur"],
        "info": ["primaire"], "neutre": ["neutre", "texte-attenue"],
    }
    label = c["badge-etiquette"]  # même valeur dans les deux thèmes : 5,17:1 avec le blanc, se détache des deux pages
    res = []
    for nom, cles in candidats.items():
        for cle in cles:
            col = c[cle]
            t = texte_shields(col)
            ratio = couleurs.contraste(t, col)
            if ratio >= 4.5:
                break
        else:
            raise ValueError(f"badge {nom} : aucune variante lisible parmi {cles}")
        res.append({"nom": nom, "jeton": cle, "hex": col, "texte": t, "ratio": ratio,
                    "label": label, "ratio_label": couleurs.contraste(BLANC, label),
                    "essaye": cles[: cles.index(cle) + 1]})
    return res


def url_badge(b: dict) -> str:
    return (f"https://img.shields.io/badge/{quote(b['nom'])}-{b['jeton'].replace('-', '--')}-{b['hex'][1:]}"
            f"?labelColor={b['label'][1:]}")


def ecrire_badges(bs: list[dict]) -> None:
    lignes = ["# Badges", "",
              "Badges shields.io aux couleurs des statuts (thème clair). shields.io choisit lui-même "
              "le texte blanc ou sombre selon la luminosité du fond ; le contraste est mesuré par "
              "`couleurs.contraste`.", "",
              "| Statut | Badge | Jeton | Couleur | Texte | Contraste |", "|---|---|---|---|---|---|"]
    for b in bs:
        lignes.append(f"| {b['nom']} | ![{b['nom']}]({url_badge(b)}) | `{b['jeton']}` | `{b['hex']}` | "
                      f"`{b['texte']}` | {b['ratio']:.2f} |")
    lignes += ["", f"Étiquette (`labelColor`) : jeton `badge-etiquette` `{bs[0]['label']}` (même valeur dans les deux thèmes), "
               f"texte blanc, contraste {bs[0]['ratio_label']:.2f} ; elle se détache de la page sombre comme de la claire.", ""]
    for b in bs:
        if len(b["essaye"]) > 1:
            lignes.append(f"- {b['nom']} : le jeton `{b['essaye'][0]}` ne passe pas 4,5:1 avec le texte de "
                          f"shields.io ; variante retenue `{b['jeton']}`.")
    (ICI / "badges.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def mermaid_init() -> str:
    return "%%{init: " + json.dumps(INIT_MERMAID) + "}%%"


DIAGRAMME = """flowchart LR
    A[Jetons DTCG] --> B[generer.py]
    B --> C[dist/]
    C --> D[Spécimens]
    D --> E[Critique]"""


def readme(bs: list[dict], mermaid_png: bool) -> str:
    rendu = ("""Rendu de référence aux couleurs de la charte, clair par défaut :

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="rendus/mermaid-sombre.png">
  <source media="(prefers-color-scheme: light)" srcset="rendus/mermaid-clair.png">
  <img alt="Diagramme d'architecture" src="rendus/mermaid-clair.png">
</picture>""" if mermaid_png else "Rendus `mermaid-*.png` indisponibles (voir `LISEZMOI.md`).")
    badges_md = " ".join(f"![{b['nom']}]({url_badge(b)})" for b in bs)
    return f"""<picture>
  <source media="(prefers-color-scheme: dark)" srcset="banniere-sombre.svg">
  <source media="(prefers-color-scheme: light)" srcset="banniere-clair.svg">
  <img alt="Projet témoin" src="banniere-clair.svg">
</picture>

{badges_md}

Dépôt témoin : un README type pour un projet qui applique la charte générique.

## Architecture

```mermaid
{mermaid_init()}
{DIAGRAMME}
```

> Le bloc mermaid prend le thème `neutral` : sans fond propre, il reste lisible sur la page claire comme sur la
> sombre de GitHub.

{rendu}

## Fonctionnalités

| Fonction | Statut | Remarque |
|---|---|---|
| Jetons DTCG | stable | source unique |
| Génération de `dist/` | stable | `generer.py --verifier` en CI |
| Spécimens | en cours | web, Office, graphiques, README |
| Critique | à venir | entrée : constats des spécimens |

## Captures

| Sombre | Clair |
|---|---|
| ![Capture sombre](rendus/readme-sombre.png) | ![Capture claire](rendus/readme-clair.png) |
"""


def html_page(theme: str, bs: list[dict], mermaid_png: bool) -> str:
    j = jetons.charger()
    c = j[theme]
    pile = j["police"]["texte"]["pile"]
    badges_h = " ".join(
        f'<span class="b"><span class="l">{b["nom"]}</span><span class="v" '
        f'style="background:{b["hex"]};color:{b["texte"]}">{b["jeton"]}</span></span>' for b in bs)
    diag = (f'<img src="rendus/mermaid-{theme}.png" alt="diagramme" style="max-width:100%">' if mermaid_png
            else f"<pre>{html.escape(DIAGRAMME)}</pre>")
    return f"""<!doctype html><html lang="fr"><meta charset="utf-8"><style>
body {{ background:{c['fond']}; color:{c['texte']}; font:16px/1.5 {pile}; margin:0; padding:32px; }}
.c {{ max-width:880px; margin:auto; border:1px solid {c['trait']}; border-radius:6px; padding:32px; }}
h2 {{ border-bottom:1px solid {c['trait']}; padding-bottom:8px; }}
table {{ border-collapse:collapse; }} td,th {{ border:1px solid {c['trait']}; padding:6px 12px; }}
th {{ background:{c['surface']}; }}
blockquote {{ border-left:4px solid {c['trait']}; margin:0; padding:0 16px; color:{c['texte-attenue']}; }}
.b {{ display:inline-flex; font:12px Verdana,sans-serif; border-radius:3px; overflow:hidden; margin-right:4px; }}
.l {{ background:{bs[0]['label']}; color:{BLANC}; padding:3px 8px; }} .v {{ padding:3px 8px; }}
pre {{ background:{c['surface']}; padding:12px; border-radius:6px; }}
</style><div class="c">
<img src="banniere-{theme}.svg" style="width:100%">
<p>{badges_h}</p>
<p>Dépôt témoin : un README type pour un projet qui applique la charte générique.</p>
<h2>Architecture</h2>{diag}
<blockquote>Bloc mermaid en thème neutral ; rendu de référence aux couleurs du thème.</blockquote>
<h2>Fonctionnalités</h2>
<table><tr><th>Fonction</th><th>Statut</th><th>Remarque</th></tr>
<tr><td>Jetons DTCG</td><td>stable</td><td>source unique</td></tr>
<tr><td>Génération de <code>dist/</code></td><td>stable</td><td><code>generer.py --verifier</code> en CI</td></tr>
<tr><td>Spécimens</td><td>en cours</td><td>web, Office, graphiques, README</td></tr>
<tr><td>Critique</td><td>à venir</td><td>constats des spécimens</td></tr></table>
</div></html>"""


def edge(args: list[str]) -> None:
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", f"--user-data-dir={prof}",
                        "--hide-scrollbars", *args], check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def capture(src: Path, dest: Path, w: int, h: int) -> None:
    edge([f"--window-size={w},{h}", f"--screenshot={dest}", src.as_uri()])


def mmdc() -> bool:
    """Rendus de référence `mermaid-sombre.png` et `mermaid-clair.png`, avec `dist/mermaid-<thème>.json`."""
    cfg = RENDUS / "_mermaid-config.json"
    mmd = RENDUS / "_diagramme.mmd"
    pup = RENDUS / "_puppeteer.json"
    # Edge du poste plutôt que le chrome-headless-shell que puppeteer ne télécharge pas
    pup.write_text(json.dumps({"executablePath": EDGE, "headless": "shell"}), encoding="utf-8")
    mmd.write_text(DIAGRAMME + "\n", encoding="utf-8")
    try:
        for theme in ("sombre", "clair"):
            data = json.loads((DIST / f"mermaid-{theme}.json").read_text("utf-8"))
            cfg.write_text(json.dumps(data), encoding="utf-8")
            subprocess.run(["npx.cmd", "-y", "@mermaid-js/mermaid-cli", "-i", str(mmd), "-o",
                            str(RENDUS / f"mermaid-{theme}.png"), "-c", str(cfg), "-p", str(pup),
                            "-b", data["themeVariables"]["background"], "--size", "900"],
                           check=True, timeout=120, capture_output=True)
        (RENDUS / "mermaid.png").unlink(missing_ok=True)  # rendu unique de la v2.0, remplacé par les deux thèmes
        return True
    except (subprocess.SubprocessError, OSError) as e:
        print("mmdc indisponible :", type(e).__name__, getattr(e, "stderr", b"")[-600:])
        return False
    finally:
        cfg.unlink(missing_ok=True)
        mmd.unlink(missing_ok=True)
        pup.unlink(missing_ok=True)


def main() -> None:
    RENDUS.mkdir(exist_ok=True)
    bs = badges()
    ecrire_badges(bs)
    ok = mmdc()
    (ICI / "README-temoin.md").write_text(readme(bs, ok), encoding="utf-8")
    for theme in ("sombre", "clair"):
        page = ICI / f"_rendu-{theme}.html"
        page.write_text(html_page(theme, bs, ok), encoding="utf-8")
        capture(page, RENDUS / f"readme-{theme}.png", 1000, 1100)
        page.unlink()
        capture(ICI / f"banniere-{theme}.svg", RENDUS / f"banniere-{theme}.png", 1280, 320)
    capture(ICI / "apercu-social.svg", ICI / "apercu-social.png", 1280, 640)
    print("rendus faits, mermaid :", ok)


if __name__ == "__main__":
    main()
