"""Génère badges.md et README-temoin.md, puis les rendus PNG (Edge headless, mmdc si dispo).

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

RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE / "skills" / "charte" / "outils"))
import couleurs  # noqa: E402
import jetons  # noqa: E402

ICI = Path(__file__).resolve().parent
RENDUS = ICI / "rendus"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
MERMAID = RACINE / "skills" / "charte" / "dist" / "mermaid-sombre.json"
# shields.io : texte #fff, ou #333 sur fond clair (luminosité > 0,69)
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
    label = c["encre-pleine"]
    res = []
    for nom, cles in candidats.items():
        for cle in cles:
            col = c[cle]
            t = texte_shields(col)
            ratio = couleurs.contraste(t, col)
            if ratio >= 4.5:
                break
        res.append({"nom": nom, "jeton": cle, "hex": col, "texte": t, "ratio": ratio,
                    "label": label, "ratio_label": couleurs.contraste(BLANC, label),
                    "essaye": cles[: cles.index(cle) + 1]})
    return res


def url_badge(b: dict) -> str:
    return (f"https://img.shields.io/badge/{b['nom']}-{b['jeton'].replace('-', '--')}-{b['hex'][1:]}"
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
    lignes += ["", f"Étiquette (`labelColor`) : jeton `encre-pleine` clair `{bs[0]['label']}`, "
               f"texte blanc, contraste {bs[0]['ratio_label']:.2f}.", ""]
    for b in bs:
        if len(b["essaye"]) > 1:
            lignes.append(f"- {b['nom']} : le jeton `{b['essaye'][0]}` ne passe pas 4,5:1 avec le texte de "
                          f"shields.io ; variante retenue `{b['jeton']}`.")
    (ICI / "badges.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def mermaid_init() -> str:
    data = json.loads(MERMAID.read_text("utf-8"))
    return "%%{init: " + json.dumps(data, ensure_ascii=False) + "}%%"


DIAGRAMME = """flowchart LR
    A[Jetons DTCG] --> B[generer.py]
    B --> C[dist/]
    C --> D[Spécimens]
    D --> E[Critique]"""


def readme(bs: list[dict]) -> str:
    badges_md = " ".join(f"![{b['nom']}]({url_badge(b)})" for b in bs)
    return f"""<picture>
  <source media="(prefers-color-scheme: dark)" srcset="banniere-sombre.svg">
  <source media="(prefers-color-scheme: light)" srcset="banniere-clair.svg">
  <img alt="Projet témoin" src="banniere-sombre.svg">
</picture>

{badges_md}

Dépôt témoin : un README type pour un projet qui applique la charte générique.

## Architecture

```mermaid
{mermaid_init()}
{DIAGRAMME}
```

> Note : GitHub applique une partie seulement des thèmes mermaid (`themeVariables`) et ignore
> `%%{{init}}%%` dans certains contextes de rendu. `rendus/mermaid.png` montre l'intention.

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
    diag = ('<img src="rendus/mermaid.png" alt="diagramme" style="max-width:100%">' if mermaid_png
            else f"<pre>{html.escape(DIAGRAMME)}</pre>")
    return f"""<!doctype html><html lang="fr"><meta charset="utf-8"><style>
body {{ background:{c['fond']}; color:{c['texte']}; font:16px/1.5 {pile}; margin:0; padding:32px; }}
.c {{ max-width:880px; margin:auto; border:1px solid {c['trait']}; border-radius:6px; padding:32px; }}
h2 {{ border-bottom:1px solid {c['trait']}; padding-bottom:8px; }}
table {{ border-collapse:collapse; }} td,th {{ border:1px solid {c['trait']}; padding:6px 12px; }}
th {{ background:{c['surface']}; }}
blockquote {{ border-left:4px solid {c['trait']}; margin:0; padding:0 16px; color:{c['texte-attenue']}; }}
.b {{ display:inline-flex; font:12px Verdana,sans-serif; border-radius:3px; overflow:hidden; margin-right:4px; }}
.l {{ background:{j['clair']['encre-pleine']}; color:{BLANC}; padding:3px 8px; }} .v {{ padding:3px 8px; }}
pre {{ background:{c['surface']}; padding:12px; border-radius:6px; }}
</style><div class="c">
<img src="banniere-{theme}.svg" style="width:100%">
<p>{badges_h}</p>
<p>Dépôt témoin : un README type pour un projet qui applique la charte générique.</p>
<h2>Architecture</h2>{diag}
<blockquote>GitHub applique une partie seulement des thèmes mermaid.</blockquote>
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
    cfg = RENDUS / "_mermaid-config.json"
    mmd = RENDUS / "_diagramme.mmd"
    data = json.loads(MERMAID.read_text("utf-8"))
    cfg.write_text(json.dumps(data), encoding="utf-8")
    mmd.write_text(DIAGRAMME + "\n", encoding="utf-8")
    try:
        subprocess.run(["npx.cmd", "-y", "@mermaid-js/mermaid-cli", "-i", str(mmd), "-o",
                        str(RENDUS / "mermaid.png"), "-c", str(cfg),
                        "-b", data["themeVariables"]["background"], "-w", "900"],
                       check=True, timeout=120, capture_output=True)
        return True
    except (subprocess.SubprocessError, OSError) as e:
        print("mmdc indisponible :", type(e).__name__)
        return False
    finally:
        cfg.unlink(missing_ok=True)
        mmd.unlink(missing_ok=True)


def main() -> None:
    RENDUS.mkdir(exist_ok=True)
    bs = badges()
    ecrire_badges(bs)
    (ICI / "README-temoin.md").write_text(readme(bs), encoding="utf-8")
    ok = mmdc()
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
