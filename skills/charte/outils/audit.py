"""Audit de charte : relève les couleurs et polices d'un dépôt et les classe par rapport à la charte.

Usage : uv run --no-project python -I audit.py <dépôt> [--ignorer GLOB]... [--markdown | --json] [--strict]

Classes de couleur :
- `charte` : égale à un jeton v2 d'un des deux thèmes ;
- `proche` : ΔE00 < 3 d'un jeton (le jeton est donné) ;
- `v1` : égale à une valeur de la charte v1 (rôle v1 et rôle v2 cible donnés) ;
- `hors-charte` : tout le reste (jeton le plus proche et ΔE00 donnés).

Avertissements « revoir » (sans effet sur `--strict`) : favicon ou pictogramme absent d'un dépôt qui a des pages HTML,
lien dont le soulignement est retiré (`text-decoration: none`) sans soulignement de remplacement.

Polices : `v1` pour Fredoka, `hors-charte` pour toute famille hors des piles de la charte.
Code de sortie 0, ou 1 avec `--strict` s'il reste du `hors-charte` ou du `v1`.
Bibliothèque standard seulement.
"""
from __future__ import annotations

import argparse
import colorsys
import fnmatch
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # `-I` ne met pas le dossier du script dans sys.path

from couleurs import de00  # noqa: E402
from jetons import THEMES, charger  # noqa: E402

MIGRATIONS = Path(__file__).resolve().parent.parent / "migrations"
EXTENSIONS = {".css", ".scss", ".html", ".htm", ".svg", ".js", ".mjs", ".jsx", ".ts", ".tsx", ".py", ".toml", ".json", ".md", ".yaml", ".yml"}
STYLE = {".css", ".scss"}
IGNORES_DEFAUT = ["dist/", "node_modules/", ".venv/", ".claude/", "_bmad-output/", "/archive/", "/archives/", "*.min.*"]
TAILLE_MAX = 1_000_000
SEUIL_PROCHE = 3.0

HEX = re.compile(r"(?<![\w&/#-])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})(?![\w-])")
FONCTION = re.compile(r"(?<![\w.-])(rgba?|hsla?)\(([^()]*)\)", re.IGNORECASE)
PROPRIETE = re.compile(
    r"(?:[\w-]*color|fill|stroke|background|border[\w-]*|outline[\w-]*|box-shadow|text-shadow|bgcolor)\s*[=:]\s*[\"']?[^\"';{}#]*$",
    re.IGNORECASE)
NON_COULEUR = re.compile(r"(?:href|src|id|for|aria-[\w-]+|data-[\w-]+|url\()\s*[=:]?\s*[\"']?$"
                         r"|(?:querySelector(?:All)?|getElementById|closest|matches|\$)\(\s*[\"'`]$", re.IGNORECASE)
POLICE = re.compile(r"(?<![\w.-])(?:font-family[\"']?\s*:|fontfamily\s*[=:]|font\.family\s*[=:]|font\s*=)\s*([^;{}\n]*)", re.IGNORECASE)
# Raccourci CSS `font: [style] [graisse] <taille>[/<interligne>] <familles>` : les familles suivent la taille.
POLICE_RACCOURCI = re.compile(
    r"(?<![\w.-])font\s*:\s*(?:[^;{}\n]*?\s)?(?:\d*\.?\d+(?:px|r?em|pt|pc|%|vh|vw|vmin|vmax|ex|ch|lh)|(?:xx?-)?(?:small|large)|medium|smaller|larger)"
    r"(?:\s*/\s*[\w.%-]+)?\s+([^;{}\n]*)", re.IGNORECASE)
PAS_UNE_POLICE = {"inherit", "initial", "unset", "sans serif", "sans-serif", "serif", "monospace"}


def charger_v1() -> dict:
    return json.loads((MIGRATIONS / "v1-vers-v2.json").read_text(encoding="utf-8"))


def palette(jetons: dict) -> dict[str, list[tuple[str, str]]]:
    """`#RRGGBB` → [(thème, rôle)] pour toutes les couleurs opaques des jetons."""
    out: dict[str, list[tuple[str, str]]] = {}
    for t in THEMES:
        for role, v in jetons[t].items():
            if isinstance(v, str) and re.fullmatch(r"#[0-9A-F]{6}", v):
                out.setdefault(v, []).append((t, role))
    return out


def valeurs_v1(v1: dict) -> dict[str, list[tuple[str, str]]]:
    """`#RRGGBB` → [(rôle v1, thème)]."""
    out: dict[str, list[tuple[str, str]]] = {}
    for role, d in v1["roles"].items():
        for t in THEMES:
            out.setdefault(d[t].upper(), []).append((role, t))
    return out


# --- Fichiers ---------------------------------------------------------------

def _ignore(rel: Path, motifs: list[str]) -> bool:
    for p in motifs:
        if p.startswith("/") and p.endswith("/"):  # dossier à la racine du dépôt seulement
            if len(rel.parts) > 1 and rel.parts[0] == p[1:-1]:
                return True
        elif p.endswith("/"):
            if p[:-1] in rel.parts[:-1]:
                return True
        elif fnmatch.fnmatch(rel.as_posix(), p) or fnmatch.fnmatch(rel.name, p):
            return True
    return False


def lister(depot: Path) -> list[Path]:
    try:
        r = subprocess.run(["git", "-C", str(depot), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           capture_output=True, check=True)
        noms = {n for n in r.stdout.decode("utf-8", "replace").split("\0") if n}
        if noms:
            return [Path(n) for n in noms]
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p.relative_to(depot) for p in depot.rglob("*") if p.is_file() and ".git" not in p.relative_to(depot).parts]


def lire_fichiers(depot: Path, ignorer: list[str] | None = None, encodages: dict | None = None,
                  avertissements: list[str] | None = None) -> list[tuple[Path, str]]:
    """(chemin relatif, texte) des fichiers texte utiles : ni binaire, ni > 1 Mo, ni ignoré.

    Décodage UTF-8 (BOM retiré), sinon cp1252. L'encodage retenu va dans `encodages`, pour réécrire à l'identique.
    Un fichier lu en repli, ou illisible, est signalé dans `avertissements`, jamais ignoré en silence.
    """
    motifs = IGNORES_DEFAUT + list(ignorer or [])
    out = []
    for rel in sorted(lister(depot)):
        p = depot / rel
        if rel.suffix.lower() not in EXTENSIONS or _ignore(rel, motifs) or not p.is_file():
            continue
        if p.stat().st_size > TAILLE_MAX:
            continue
        brut = p.read_bytes()
        if b"\0" in brut[:8192]:
            continue
        enc = "utf-8-sig" if brut.startswith(b"\xef\xbb\xbf") else "utf-8"
        try:
            texte = brut.decode(enc)
        except UnicodeDecodeError:
            enc = "cp1252"
            try:
                texte = brut.decode(enc)
            except UnicodeDecodeError:
                if avertissements is not None:
                    avertissements.append(f"{rel.as_posix()} : encodage illisible, fichier ignoré")
                continue
            if avertissements is not None:
                avertissements.append(f"{rel.as_posix()} : pas en UTF-8, lu en cp1252")
        if encodages is not None:
            encodages[rel] = enc
        out.append((rel, texte))
    return out


# --- Détection --------------------------------------------------------------

def _hex_complet(h: str) -> tuple[str, str]:
    """`#RGB`, `#RGBA`, `#RRGGBB`, `#RRGGBBAA` → (`#RRGGBB`, suffixe alpha éventuel)."""
    c = h[1:].upper()
    if len(c) in (3, 4):
        c = "".join(x * 2 for x in c)
    return "#" + c[:6], c[6:]


def _nombre(s: str, pct: float = 1.0) -> float | None:
    m = re.fullmatch(r"(-?\d*\.?\d+)(%|deg)?", s)
    if not m:
        return None
    v = float(m.group(1))
    return v * pct if m.group(2) == "%" else v


def _fonction(nom: str, args: str) -> tuple[str, str] | None:
    """rgb()/hsl() → (`#RRGGBB`, `rgba(...)` ou ''), None si les arguments ne sont pas numériques."""
    jetons = [t for t in re.split(r"[\s,/]+", args.strip()) if t]
    if len(jetons) not in (3, 4):
        return None
    alpha = 1.0
    if len(jetons) == 4:
        a = _nombre(jetons[3], 0.01)
        if a is None:
            return None
        alpha = min(a, 1.0)
    if nom.lower().startswith("rgb"):
        vals = [_nombre(t, 2.55) for t in jetons[:3]]
        if None in vals:
            return None
        r, g, b = (max(0, min(255, round(v))) for v in vals)  # type: ignore[arg-type]
    else:
        h, s, ln = _nombre(jetons[0]), _nombre(jetons[1], 0.01), _nombre(jetons[2], 0.01)
        if h is None or s is None or ln is None:
            return None
        rgb = colorsys.hls_to_rgb((h % 360) / 360, max(0.0, min(ln, 1.0)), max(0.0, min(s, 1.0)))
        r, g, b = (max(0, min(255, round(x * 255))) for x in rgb)
    hexa = f"#{r:02X}{g:02X}{b:02X}"
    return hexa, (f"rgba({r}, {g}, {b}, {alpha:g})" if alpha < 1 else "")


def couleurs_ligne(ligne: str, ext: str) -> list[dict]:
    """Couleurs d'une ligne : dicts {debut, fin, brut, kind, hex, rgba, alpha}."""
    out = []
    for m in HEX.finditer(ligne):
        avant, apres = ligne[:m.start()], ligne[m.end():]
        brut = m.group()
        if NON_COULEUR.search(avant):
            continue
        ok = False
        if ext in STYLE:
            ok = not avant.rstrip().endswith(("url(", "url('", 'url("')) and not re.match(r"[^;(){}]*\{", apres)
        if not ok and avant[-1:] in "\"'`" and avant and apres[:1] == avant[-1]:
            ok = not (len(brut) in (4, 5) and brut[1:].isdigit())
        if not ok and PROPRIETE.search(avant):
            ok = True
        if not ok and ext == ".md" and re.search(r"\|\s*$", avant):
            ok = True
        if ok:
            h, alpha = _hex_complet(brut)
            out.append({"debut": m.start(), "fin": m.end(), "brut": brut, "kind": "hex", "hex": h, "rgba": "", "alpha": alpha})
    for m in FONCTION.finditer(ligne):
        r = _fonction(m.group(1), m.group(2))
        if r:
            out.append({"debut": m.start(), "fin": m.end(), "brut": m.group(), "kind": "fonction", "hex": r[0], "rgba": r[1], "alpha": ""})
    return sorted(out, key=lambda c: c["debut"])


def polices_ligne(ligne: str) -> list[tuple[str, int, int]]:
    """Familles déclarées sur une ligne : (nom, début, fin)."""
    out = []
    for m in [*POLICE.finditer(ligne), *POLICE_RACCOURCI.finditer(ligne)]:
        base, valeur = m.start(1), m.group(1)
        pos = 0
        for item in valeur.split(","):
            nom = item.replace("!important", "").strip().strip("'\"[]() ").strip()
            if nom and "(" not in nom and not nom.startswith("var") and nom.lower() not in PAS_UNE_POLICE:
                i = item.find(nom)
                if i >= 0:
                    out.append((nom, base + pos + i, base + pos + i + len(nom)))
            pos += len(item) + 1
    return out


# --- Classement -------------------------------------------------------------

@lru_cache(maxsize=4096)
def _plus_proche(h: str, hexes: tuple[str, ...]) -> tuple[str, float]:
    return min(((c, de00(h, c)) for c in hexes), key=lambda t: t[1])


def _nom_jeton(pal: dict, h: str) -> str:
    return "/".join(sorted({f"{t}:{r}" for t, r in pal[h]}))


def classer(c: dict, jetons: dict, pal: dict, v1: dict, v1val: dict) -> dict:
    h = c["hex"]
    if c["rgba"]:
        for t in THEMES:
            for role, v in jetons[t].items():
                if v == c["rgba"]:
                    return {"classe": "charte", "jeton": f"{t}:{role}"}
    if h in pal:
        return {"classe": "charte", "jeton": _nom_jeton(pal, h)}
    if h in v1val:
        roles = sorted({r for r, _ in v1val[h]})
        cibles = sorted({v1["roles"][r]["cible"] or "(supprimé)" for r in roles})
        return {"classe": "v1", "roles_v1": roles, "roles_v2": cibles}
    proche, ecart = _plus_proche(h, tuple(pal))
    return {"classe": "proche" if ecart < SEUIL_PROCHE else "hors-charte", "jeton": _nom_jeton(pal, proche), "delta_e": round(ecart, 1)}


def classer_police(nom: str, familles: set[str]) -> str | None:
    if nom in familles:
        return None
    return "v1" if nom in charger_v1()["polices"] else "hors-charte"


REGLE_CSS = re.compile(r"([^{}]+)\{([^{}]*)\}")
SELECTEUR_LIEN = re.compile(r"(?:^|[\s,>+~])a(?![\w-])", re.IGNORECASE)
HORS_TEXTE = re.compile(r"btn|button|bouton|nav|menu|\btabs?\b|onglet|breadcrumb|ariane|pagination", re.IGNORECASE)  # hors texte courant
COMMANDE_INSTALLER = ('uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/installer.py" '
                      "--cible <dépôt> --supports web --seulement ")


def a_revoir(depot: Path, fichiers: list[tuple[Path, str]], ignorer: list[str] | None) -> list[str]:
    """Avertissements `revoir` : favicon et pictogramme absents, liens sans soulignement."""
    out = []
    motifs = IGNORES_DEFAUT + list(ignorer or [])
    noms = {p.name.lower() for p in lister(depot) if not _ignore(p, motifs)}
    if any(r.suffix.lower() in (".html", ".htm") for r, _ in fichiers):
        if not any(n.startswith("favicon.") for n in noms):
            out.append(f"revoir : aucun favicon dans le dépôt (`{COMMANDE_INSTALLER}favicon`)")
        if not any(n.startswith("pictogramme.") for n in noms):
            out.append(f"revoir : aucun pictogramme dans le dépôt (`{COMMANDE_INSTALLER}pictogramme`)")
    for rel, texte in fichiers:
        if rel.suffix.lower() not in STYLE | {".html", ".htm"}:
            continue
        regles = [(m.group(1).strip(), m.group(2), texte.count("\n", 0, m.start(2)) + 1) for m in REGLE_CSS.finditer(texte)]
        souligne = any(SELECTEUR_LIEN.search(s) and re.search(r"underline|border-bottom", c) for s, c, _ in regles)
        for sel, corps, n in regles:
            if SELECTEUR_LIEN.search(sel) and not HORS_TEXTE.search(sel) and not souligne \
                    and re.search(r"text-decoration(?:-line)?\s*:\s*none", corps) and not re.search(r"border-bottom", corps):
                out.append(f"revoir : {rel.as_posix()}:{n} lien (`{sel}`) sans soulignement de remplacement (la charte souligne les liens)")
    return out


def auditer(depot: Path, ignorer: list[str] | None = None) -> dict:
    jetons, v1 = charger(), charger_v1()
    pal, v1val = palette(jetons), valeurs_v1(v1)
    familles = {f for r in jetons["police"].values() for f in r["familles"]}
    constats: list[dict] = []
    avertissements: list[str] = []
    fichiers = lire_fichiers(depot, ignorer, avertissements=avertissements)
    avertissements += a_revoir(depot, fichiers, ignorer)
    for rel, texte in fichiers:
        ext = rel.suffix.lower()
        for n, ligne in enumerate(texte.splitlines(), 1):
            for c in couleurs_ligne(ligne, ext):
                constats.append({"fichier": rel.as_posix(), "ligne": n, "type": "couleur", "valeur": c["brut"], **classer(c, jetons, pal, v1, v1val)})
            for nom, _, _ in polices_ligne(ligne):
                cl = classer_police(nom, familles)
                if cl:
                    constats.append({"fichier": rel.as_posix(), "ligne": n, "type": "police", "valeur": nom, "classe": cl})
    resume = {"couleurs": {k: 0 for k in ("charte", "proche", "v1", "hors-charte")}, "polices": {"v1": 0, "hors-charte": 0}}
    for k in constats:
        resume["couleurs" if k["type"] == "couleur" else "polices"][k["classe"]] += 1
    return {"depot": str(depot), "constats": constats, "resume": resume, "avertissements": avertissements}


def _detail(k: dict) -> str:
    if k["classe"] == "v1":
        return f"v1 {'/'.join(k['roles_v1'])} -> {'/'.join(k['roles_v2'])}" if "roles_v1" in k else "Fredoka -> Sora"
    if "jeton" in k:
        return f"{k['jeton']}" + (f" (dE00 {k['delta_e']})" if k["classe"] != "charte" else "")
    return ""


def texte(res: dict, markdown: bool) -> str:
    gravite = {"hors-charte": 0, "v1": 1, "proche": 2, "charte": 3}
    lignes = sorted(res["constats"], key=lambda k: (gravite[k["classe"]], k["fichier"], k["ligne"]))
    lignes = [k for k in lignes if k["classe"] != "charte"]
    sortie = []
    if markdown:
        sortie += ["| Classe | Fichier | Ligne | Valeur | Détail |", "|---|---|---|---|---|"]
        sortie += [f"| {k['classe']} | `{k['fichier']}` | {k['ligne']} | `{k['valeur']}` | {_detail(k)} |" for k in lignes]
    else:
        sortie += [f"{k['classe']:<12} {k['fichier']}:{k['ligne']:<5} {k['valeur']:<22} {_detail(k)}" for k in lignes]
    r = res["resume"]
    c, p = r["couleurs"], r["polices"]
    resume = (f"Couleurs : {c['charte']} charte, {c['proche']} proche, {c['v1']} v1, {c['hors-charte']} hors-charte. "
              f"Polices : {p['v1']} v1, {p['hors-charte']} hors-charte.")
    avert = [("- " if markdown else "Avertissement : ") + a for a in res.get("avertissements", [])]
    return "\n".join(sortie + ["", ("**" + resume + "**") if markdown else resume] + ([""] + avert if avert else []))


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("depot", type=Path)
    ap.add_argument("--ignorer", action="append", default=[], metavar="GLOB")
    fmt = ap.add_mutually_exclusive_group()
    fmt.add_argument("--markdown", action="store_true")
    fmt.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    res = auditer(a.depot.resolve(), a.ignorer)
    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else texte(res, a.markdown))
    r = res["resume"]
    reste = r["couleurs"]["hors-charte"] + r["couleurs"]["v1"] + r["polices"]["hors-charte"] + r["polices"]["v1"]
    return 1 if a.strict and reste else 0


if __name__ == "__main__":
    sys.exit(main())
