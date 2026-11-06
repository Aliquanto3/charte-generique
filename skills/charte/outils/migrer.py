"""Migration des couleurs et polices d'un dépôt vers la charte v2.

Usage : uv run --no-project python -I migrer.py <dépôt> [--plan FICHIER] [--appliquer]
        [--proposer] [--correspondances FICHIER.json] [--ajouter-sombre] [--clair-d-abord] [--ignorer GLOB]...

Par défaut, n'écrit rien dans le dépôt : il produit un plan markdown (fichier, ligne, ancien, nouveau, rôle, statut).
- Source v1 : `migrations/v1-vers-v2.json`. Les valeurs v2 se lisent par `jetons.charger()`, jamais en dur.
- Statut `auto` : remplacé par `--appliquer`. Statut `revoir` : jamais appliqué, à relire à la main
  (rôle qui change de sens, valeur partagée par deux rôles v1 sans nom de variable qui tranche, proposition approchée).
- `--proposer` : pour les variables, clés ou constantes de couleur hors table v1, propose un rôle v2 d'après le nom
  (`migrations/synonymes.json`, statut `auto`), sinon d'après le jeton le plus proche en ΔE00 (statut `revoir`).
- `--correspondances` : table {"--nom": "role-v2"} prioritaire ; `null` supprime la variable si elle n'est plus utilisée.
- `--ajouter-sombre` : dépôt en clair seulement, ajoute (avec `--appliquer`) le bloc sombre généré depuis les jetons.
  Par défaut « sombre d'abord » : sombre dans `:root`, clair sous `prefers-color-scheme: light` et `[data-theme="light"]`.
- `--clair-d-abord` : avec `--ajouter-sombre`, garde le clair dans `:root` et met le sombre sous `prefers-color-scheme: dark`.
Idempotent. Bibliothèque standard seulement.
"""
from __future__ import annotations

import argparse
import bisect
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # `-I` ne met pas le dossier du script dans sys.path

import audit  # noqa: E402
from couleurs import de00  # noqa: E402
from jetons import THEMES, charger  # noqa: E402

# Mot entier : `.dark-header` ou `.light-box` ne désignent pas un thème.
DARK = re.compile(r"prefers-color-scheme\s*:\s*dark|data-(?:theme|mode|bs-theme)\s*=\s*[\"']?(?:dark|sombre)(?![\w-])"
                  r"|\.(?:dark|sombre|theme-dark)(?![\w-])", re.IGNORECASE)
LIGHT = re.compile(r"prefers-color-scheme\s*:\s*light|data-(?:theme|mode|bs-theme)\s*=\s*[\"']?(?:light|clair)(?![\w-])"
                   r"|\.(?:light|clair|theme-light)(?![\w-])", re.IGNORECASE)
SECTION = re.compile(r"^\s*\[([^\]]+)\]", re.MULTILINE)
STYLES = {".css", ".scss", ".html", ".htm", ".svg"}
DECLARATIONS = {".toml", ".json", ".yaml", ".yml", ".py"}
NOM_AVANT = re.compile(r"(--[\w-]+|\$[\w-]+|[\w.-]+)[\"']?\s*[:=]\s*[^:=]*$")
FOND_VAR = re.compile(r"background(?:-color)?\s*:\s*var\(\s*(--[\w-]+)")
FACE = re.compile(r"@font-face\s*\{[^}]*\}", re.IGNORECASE)
URL_SRC = re.compile(r"url\(\s*([\"']?)([^)\"']+)\1\s*\)", re.IGNORECASE)
PILE_VAR = re.compile(r"(--[\w-]*(?:police|font)[\w-]*)\s*:\s*([^;{}\n]*)", re.IGNORECASE)
PAS_PILE = re.compile(r"size|weight|taille|graisse|style|line|hauteur|variant|stretch", re.IGNORECASE)
RACINE = re.compile(r":root|(?<![\w-])html(?![\w-])|(?<![\w-])body(?![\w-])|\[data-", re.IGNORECASE)
PROP_VALEUR = re.compile(r"([\w-]+)\s*:\s*([^;{}]*)")
PROPS_TEXTE = {"color", "-webkit-text-fill-color", "caret-color", "text-decoration-color"}
COMMANDE_POLICES = ('uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/installer.py" '
                    "--cible <dépôt> --supports web --seulement polices")
DECL_VAR = re.compile(r"(--[\w-]+)\s*:[^;}\n]*;?")


def normaliser(nom: str) -> str:
    n = nom.strip().lower().lstrip("-$@").replace("_", "-")
    return re.sub(r"^(?:color|couleur|colour|c)-", "", n)


class Suivi:
    """Pile des blocs CSS ouverts, pour connaître le thème et le sélecteur courants."""

    def __init__(self) -> None:
        self.pile: list[str] = []
        self.buf = ""

    def avancer(self, s: str) -> None:
        for ch in s:
            if ch == "{":
                self.pile.append(self.buf.strip())
                self.buf = ""
            elif ch == "}":
                if self.pile:
                    self.pile.pop()
                self.buf = ""
            elif ch == ";":
                self.buf = ""
            else:
                self.buf += ch

    def theme(self) -> str | None:
        for h in reversed(self.pile):
            if DARK.search(h):
                return "sombre"
            if LIGHT.search(h):
                return "clair"
        return None

    def selecteur(self) -> str:
        return self.pile[-1] if self.pile else ""


def theme_nom(texte: str) -> str | None:
    """Thème d'un nom de fichier ou de section, par mot entier (`theme-dark.css`, `darkTheme`, `[theme.sombre]`).

    Une sous-chaîne ne suffit pas : `darkroom.css` ou `highlight.toml` ne désignent aucun thème.
    """
    mots = {m.lower() for m in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", texte)}
    if mots & {"dark", "sombre"}:
        return "sombre"
    if mots & {"light", "clair"}:
        return "clair"
    return None


def a_sombre(rel: Path, texte: str) -> bool:
    if rel.suffix.lower() == ".md":  # un plan ou une doc qui cite `prefers-color-scheme: dark` n'est pas un thème
        return False
    return (theme_nom(rel.name) == "sombre" or bool(DARK.search(texte))
            or any(theme_nom(s) == "sombre" for s in SECTION.findall(texte)))


class Contexte:
    def __init__(self, correspondances: dict | None = None, proposer: bool = False, clair_d_abord: bool = False) -> None:
        self.clair_d_abord = clair_d_abord
        self.jetons = charger()
        self.v1 = audit.charger_v1()
        self.pal = audit.palette(self.jetons)
        self.v1val = audit.valeurs_v1(self.v1)
        self.syn_v1 = {r: {normaliser(n) for n in noms} for r, noms in self.v1["synonymes"].items()}
        brut = json.loads((audit.MIGRATIONS / "synonymes.json").read_text(encoding="utf-8"))["roles"]
        self.syn_v2 = {normaliser(n): r for r, noms in brut.items() for n in noms}
        self.corr = correspondances or {}
        self.proposer = proposer

    def valeur(self, role: str, theme: str) -> str | None:
        v = self.jetons[theme].get(role)
        return v if isinstance(v, str) else None

    def meilleur_theme(self, role: str, h: str) -> str | None:
        """Thème où le rôle est le plus proche de la couleur d'origine."""
        cand = [(de00(h, v), t) for t in THEMES if (v := self.valeur(role, t)) and v.startswith("#") and len(v) == 7]
        return min(cand)[1] if cand else next((t for t in THEMES if self.valeur(role, t)), None)

    def corr_pour(self, nom: str | None) -> tuple[bool, str | None]:
        if not nom:
            return False, None
        nu = nom.lstrip("-")
        for k in (nom, "--" + nu, nu):
            if k in self.corr:
                return True, self.corr[k]
        return False, None


def _entree(fichier, n, ancien, nouveau, role, statut, note="", **extra) -> dict:
    return {"fichier": fichier, "ligne": n, "ancien": ancien, "nouveau": nouveau, "role": role, "statut": statut, "note": note, **extra}


def _valeur_ecrite(brut: str, val: str, alpha: str) -> str:
    if val.startswith("#") and len(val) == 7:
        val += alpha
        return val.lower() if brut[1:] != brut[1:].upper() else val
    return val


def resoudre_v1(ctx: Contexte, cands: list, theme: str | None, nom: str | None, selecteur: str) -> tuple[str, str, str | None, str | None, str]:
    """→ (statut, rôle affiché, rôle v2 cible, thème de la valeur, note)."""
    sub = [c for c in cands if c[1] == theme] if theme and any(c[1] == theme for c in cands) else list(cands)
    roles = sorted({r for r, _ in sub})
    defs = ctx.v1["roles"]

    def trancher(s: list) -> bool:
        if any(defs[r]["statut"] != "auto" for r, _ in s):
            return False
        vals = set()
        for r, t in s:
            v = ctx.valeur(defs[r]["cible"], t)
            if v is None:
                return False
            vals.add(v)
        return len(vals) == 1

    choix = None
    if trancher(sub):
        choix = sub
    else:
        nn = normaliser(nom) if nom else None
        par_nom = [c for c in sub if nn and nn in ctx.syn_v1.get(c[0], ())]
        if par_nom and trancher(par_nom):
            choix = par_nom
    if choix:
        r, t = choix[0]
        cible = defs[r]["cible"]
        b = ctx.v1["bouton"]
        if re.search(b["motif_selecteur"], selecteur, re.IGNORECASE) and cible in b["cibles"]:
            return "revoir", cible, b["cibles"][cible], t, b["note"]
        return "auto", cible, cible, t, ""
    if len(roles) == 1:
        d = defs[roles[0]]
        return "revoir", roles[0], d["cible"], sub[0][1], d.get("note", "rôle v2 absent des jetons")
    return "revoir", "/".join(roles), None, None, f"valeur partagée par plusieurs rôles v1 ({', '.join(roles)}) : le nom de la variable ne tranche pas"


def plus_proche(ctx: Contexte, h: str, theme: str | None) -> tuple[float, str, str]:
    cand = []
    for t in ([theme] if theme else THEMES):
        for role, v in ctx.jetons[t].items():
            if isinstance(v, str) and re.fullmatch(r"#[0-9A-F]{6}", v) and not role.startswith("cat-"):
                cand.append((de00(h, v), t, role))
    return min(cand, key=lambda x: x[0])


def role_clair(ctx: Contexte, h: str, nom: str | None) -> tuple[str | None, str]:
    """Rôle clair d'une valeur déjà égale à un jeton : (rôle, note d'échec)."""
    roles = sorted({r for t, r in ctx.pal[h] if t == "clair"})
    if not roles:
        return None, "couleur d'un jeton sombre dans un thème clair : contrepartie sombre à choisir"
    if len(roles) == 1:
        return roles[0], ""
    par_nom = ctx.syn_v2.get(normaliser(nom or ""))
    if par_nom in roles:
        return par_nom, ""
    if len({ctx.valeur(r, "sombre") for r in roles}) == 1:
        return roles[0], ""
    return None, f"valeur égale à plusieurs jetons clairs ({', '.join(roles)}) : contrepartie sombre à choisir"


def pile_police(nom_var: str) -> str:
    n = nom_var.lower()
    return "code" if re.search(r"code|mono", n) else "titres" if re.search(r"titre|head|display|title", n) else "texte"


def migrer_faces(ctx: Contexte, rel: Path, texte: str, noms_depot: set[str], entrees: list[dict], edits: dict) -> None:
    """`@font-face` d'une police v1 : graisse et fichier `src` suivent la charte (la famille l'est ailleurs)."""
    starts = [0]
    for ln in texte.splitlines(keepends=True):
        starts.append(starts[-1] + len(ln))
    f = rel.as_posix()

    def pos(off: int) -> tuple[int, int]:
        i = bisect.bisect_right(starts, off) - 1
        return i, off - starts[i]

    premieres: dict[tuple[str, str], int] = {}  # (rôle, font-style) → ligne de la première face migrée
    for m in FACE.finditer(texte):
        bloc, base = m.group(), m.start()
        fam = re.search(r"font-family\s*:\s*([^;}]+)", bloc, re.IGNORECASE)
        role = ctx.v1["polices"].get(fam.group(1).strip().strip("'\" ")) if fam else None
        if not role or role not in ctx.jetons["police"]:
            continue
        p = ctx.jetons["police"][role]
        stem = re.sub(r"\s+", "-", p["familles"][0].lower()) + f"-latin-{p['graisse']}-normal"
        poids = re.search(r"(font-weight\s*:\s*)([^;}\n]*[^;}\s])", bloc, re.IGNORECASE)
        style_f = re.search(r"font-style\s*:\s*([\w-]+)", bloc, re.IGNORECASE)
        cle = (role, style_f.group(1).lower() if style_f else "normal")
        if cle in premieres:
            origine = poids.group(2) if poids else "absente"
            entrees.append(_entree(f, pos(base)[0] + 1, "@font-face", "(à supprimer)", f"police:{role}", "revoir",
                                   f"face en double après migration (graisse d'origine {origine}) : la charte n'a que la graisse "
                                   f"{p['graisse']} pour `{role}`, déjà déclarée ligne {premieres[cle]} ; supprimer ce bloc"))
        else:
            premieres[cle] = pos(base)[0] + 1
        if not poids:
            entrees.append(_entree(f, pos(base)[0] + 1, "@font-face", f"font-weight: {p['graisse']}", f"police:{role}", "revoir",
                                   "font-weight absent : à ajouter"))
        elif poids.group(2) != str(p["graisse"]):
            i, c = pos(base + poids.start(2))
            entrees.append(_entree(f, i + 1, f"font-weight: {poids.group(2)}", f"font-weight: {p['graisse']}", f"police:{role}", "auto"))
            edits.setdefault(rel, []).append((i, c, c + len(poids.group(2)), str(p["graisse"]), False))
        for u in URL_SRC.finditer(bloc):
            chemin = u.group(2)
            if chemin.startswith("data:"):
                continue
            dossier, _, nom = chemin.rpartition("/")
            ext = nom.rpartition(".")[2].lower()
            i, c = pos(base + u.start(2))
            if ext not in ("woff2", "ttf"):
                entrees.append(_entree(f, i + 1, chemin, "-", f"police:{role}", "revoir", f"format {ext} non fourni par la charte (woff2 ou ttf)"))
                continue
            nouveau = (dossier + "/" if dossier else "") + f"{stem}.{ext}"
            if nouveau != chemin:
                entrees.append(_entree(f, i + 1, chemin, nouveau, f"police:{role}", "auto", "fichier de police de la charte"))
                edits.setdefault(rel, []).append((i, c, c + len(chemin), nouveau, False))
            if f"{stem}.{ext}" not in noms_depot:
                entrees.append(_entree(f, i + 1, f"{stem}.{ext}", "-", f"police:{role}", "revoir",
                                       f"fichier de police absent du dépôt : `{COMMANDE_POLICES}` (le dossier doit correspondre à l'url)"))


def planifier(depot: Path, ignorer: list[str], ctx: Contexte) -> dict:
    encodages: dict[Path, str] = {}
    avertissements: list[str] = []
    fichiers = audit.lire_fichiers(depot, ignorer, encodages, avertissements)
    textes = {rel: t for rel, t in fichiers}
    entrees: list[dict] = []
    edits: dict[Path, list[tuple[int, int, int, str, bool]]] = {}
    sombre_present = any(a_sombre(rel, t) for rel, t in fichiers)
    nulles = {k.lstrip("-") for k, v in ctx.corr.items() if v is None}
    jetons = ctx.jetons
    noms_depot = {p.name for p in audit.lister(depot)}
    conformes: list[dict] = []  # variables déjà égales à un jeton : elles aussi ont besoin d'une contrepartie sombre
    decls: dict[str, tuple[str, int]] = {}

    for rel, texte in fichiers:
        ext, f = rel.suffix.lower(), rel.as_posix()
        style = ext in STYLES
        theme_f = theme_nom(rel.name)
        suivi, section = Suivi(), None
        if style:
            migrer_faces(ctx, rel, texte, noms_depot, entrees, edits)
        for idx, ligne_brute in enumerate(texte.splitlines(keepends=True)):
            ligne = ligne_brute.rstrip("\r\n")
            n = idx + 1
            m = SECTION.match(ligne) if ext == ".toml" else None
            if m:
                section = theme_nom(m.group(1))
            pts = [(c["debut"], "c", c) for c in audit.couleurs_ligne(ligne, ext) if c["kind"] == "hex"]
            if style:
                pts += [(m.start(), "v", m) for m in FOND_VAR.finditer(ligne)]
                pts += [(m.start(), "s", m) for m in DECL_VAR.finditer(ligne) if nulles and m.group(1).lstrip("-") in nulles]
            pts.sort(key=lambda p: p[0])
            pos = 0
            for debut, genre, c in pts:
                if style:
                    suivi.avancer(ligne[pos:debut])
                    pos = debut
                theme = (suivi.theme() if style else section) or theme_f
                sel = suivi.selecteur() if style else ""
                if genre == "v":
                    nu = normaliser(c.group(1))
                    b = ctx.v1["bouton"]
                    if nu in ctx.syn_v1["primaire"]:
                        if re.search(b["motif_selecteur"], sel, re.IGNORECASE):
                            entrees.append(_entree(f, n, f"var({c.group(1)})", "bouton", "primaire", "revoir", b["note"]))
                        else:
                            entrees.append(_entree(f, n, f"var({c.group(1)})", "(à décider)", "primaire", "revoir",
                                                   f"aplat primaire hors bouton (`{sel or '?'}`) : nav, puce ou badge ? à relire"))
                    continue
                if genre == "s":
                    nom = c.group(1)
                    usages = sum(len(re.findall(rf"var\(\s*{re.escape(nom)}\b", t)) for t in textes.values())
                    if usages:
                        entrees.append(_entree(f, n, nom, "(conservée)", "-", "revoir", f"variable à supprimer encore utilisée ({usages} usages)"))
                    else:
                        entrees.append(_entree(f, n, nom, "(supprimée)", "-", "auto", "supprimée sur demande (correspondance null)"))
                        edits.setdefault(rel, []).append((idx, c.start(), c.end(), "", True))
                    continue
                h, brut = c["hex"], c["brut"]
                nom = None
                mn = NOM_AVANT.search(ligne[:c["debut"]])
                if mn:
                    nom = mn.group(1)
                declaration = bool(nom) and ((style and nom.startswith(("--", "$"))) or ext in DECLARATIONS)
                variable_css = declaration and style and nom.startswith("--")
                if variable_css:
                    decls.setdefault(nom, (f, n))
                a_corr, role_corr = ctx.corr_pour(nom)
                role = statut = note = aff = None
                th_val = None
                if a_corr:
                    if role_corr is None:
                        if not style:
                            entrees.append(_entree(f, n, brut, "-", "-", "revoir", "variable à supprimer à la main"))
                        continue
                    role, statut, note = role_corr, "auto", "correspondance fournie"
                else:
                    if h in ctx.pal:
                        if variable_css and theme != "sombre" and not sombre_present and RACINE.search(sel):
                            r_cl, motif = role_clair(ctx, h, nom)
                            if r_cl:
                                conformes.append({"fichier": f, "variable": nom, "cible": r_cl})
                            else:
                                entrees.append(_entree(f, n, brut, "-", "-", "revoir", motif))
                        continue
                    cands = ctx.v1val.get(h)
                    if cands:
                        statut, aff, role, th_val, note = resoudre_v1(ctx, cands, theme, nom, sel)
                        if role is None and statut == "revoir":
                            entrees.append(_entree(f, n, brut, "-", aff, "revoir", note))
                            continue
                    elif ctx.proposer and declaration:
                        r = ctx.syn_v2.get(normaliser(nom))
                        if r and any(ctx.valeur(r, t) for t in THEMES):
                            role, statut, note = r, "auto", "proposé d'après le nom"
                        else:
                            ecart, t, role = plus_proche(ctx, h, theme)
                            statut, th_val, note = "revoir", t, f"jeton le plus proche (dE00 {ecart:.1f}) : à confirmer"
                    else:
                        continue
                if role is None or not any(ctx.valeur(role, t) for t in THEMES):
                    entrees.append(_entree(f, n, brut, "-", role or "-", "revoir", "rôle v2 absent des jetons"))
                    continue
                th_val = theme or th_val or ctx.meilleur_theme(role, h)
                if not ctx.valeur(role, th_val):
                    th_val = next(t for t in THEMES if ctx.valeur(role, t))
                nouveau = _valeur_ecrite(brut, ctx.valeur(role, th_val), c["alpha"])
                if nouveau.upper() == brut.upper():
                    if variable_css and th_val != "sombre" and not sombre_present and RACINE.search(sel):
                        conformes.append({"fichier": f, "variable": nom, "cible": role})
                    continue
                e = _entree(f, n, brut, nouveau, aff or role, statut, note or "",
                            variable=nom if declaration and style and nom.startswith("--") else None,
                            cible=role, theme=theme)
                entrees.append(e)
                if statut == "auto":
                    edits.setdefault(rel, []).append((idx, c["debut"], c["fin"], nouveau, False))
            if style:
                suivi.avancer(ligne[pos:] + "\n")
            if style:
                for mp in PILE_VAR.finditer(ligne):
                    if PAS_PILE.search(mp.group(1)):
                        continue
                    valeur = re.sub(r"\s*!\s*important\s*$", "", mp.group(2).rstrip(), flags=re.IGNORECASE)  # !important conservé
                    if not valeur or "var(" in valeur:
                        continue
                    noms = [x.replace("!important", "").strip().strip("'\"") for x in valeur.split(",")]
                    role_v1 = next((ctx.v1["polices"][x] for x in noms if x in ctx.v1["polices"]), None)
                    role_n = pile_police(mp.group(1))
                    if role_v1 and role_v1 in jetons["police"]:
                        pile = jetons["police"][role_v1]["pile"]
                        if valeur != pile:
                            entrees.append(_entree(f, n, valeur, pile, f"police:{role_v1}", "auto", f"pile de {mp.group(1)}"))
                            edits.setdefault(rel, []).append((idx, mp.start(2), mp.start(2) + len(valeur), pile, False))
                    elif noms[0] not in {fam for r in jetons["police"].values() for fam in r["familles"]}:
                        entrees.append(_entree(f, n, valeur, jetons["police"][role_n]["pile"], f"police:{role_n}", "revoir",
                                               f"pile {mp.group(1)} hors charte : pile du rôle `{role_n}` proposée"))
            # polices
            for nom_p, d, fin in audit.polices_ligne(ligne):
                role_p = ctx.v1["polices"].get(nom_p)
                if role_p and role_p in jetons["police"]:
                    cible = jetons["police"][role_p]["familles"][0]
                    entrees.append(_entree(f, n, nom_p, cible, f"police:{role_p}", "auto"))
                    edits.setdefault(rel, []).append((idx, d, fin, cible, False))
    entrees += eclater(textes, decls)
    bloc = {}
    if not sombre_present:
        bloc = blocs_sombres(ctx, entrees, conformes)
    return {"entrees": entrees, "edits": edits, "textes": textes, "sombre_present": sombre_present, "blocs": bloc,
            "encodages": encodages, "avertissements": avertissements}


def eclater(textes: dict[Path, str], decls: dict[str, tuple[str, int]]) -> list[dict]:
    """Variables de couleur utilisées en texte et en aplat : un seul rôle ne convient pas aux deux."""
    usages: dict[str, dict[str, list[str]]] = {}
    for rel, texte in textes.items():
        if rel.suffix.lower() not in STYLES:
            continue
        for n, ligne in enumerate(texte.splitlines(), 1):
            for mp in PROP_VALEUR.finditer(ligne):
                prop = mp.group(1).lower()
                genre = "texte" if prop in PROPS_TEXTE else "aplat" if prop.startswith("background") else None
                if not genre:
                    continue
                for v in re.finditer(r"var\(\s*(--[\w-]+)", mp.group(2)):
                    usages.setdefault(v.group(1), {}).setdefault(genre, []).append(f"{rel.as_posix()}:{n} ({prop})")
    out = []
    for nom, (f, n) in decls.items():
        u = usages.get(nom, {})
        if "texte" in u and "aplat" in u:
            detail = " ; ".join(f"{g} : {', '.join(u[g][:4])}" for g in ("texte", "aplat"))
            out.append(_entree(f, n, nom, "(à éclater)", "-", "revoir", f"variable à éclater en deux rôles (texte / aplat) : {detail}"))
    return out


def blocs_sombres(ctx: Contexte, entrees: list[dict], conformes: list[dict] | None = None) -> dict[str, str]:
    """Par fichier de style : variables migrées ou déjà conformes, avec leur contrepartie sombre lue par charger()."""
    par_fichier: dict[str, dict[str, str]] = {}
    for e in entrees:
        if e["statut"] != "auto" or not e.get("variable") or e.get("theme") == "sombre":
            continue
        par_fichier.setdefault(e["fichier"], {})[e["variable"]] = e["cible"]
    for c in conformes or []:
        par_fichier.setdefault(c["fichier"], {}).setdefault(c["variable"], c["cible"])

    def corps(d: dict[str, str], pas: str) -> str:
        return "".join(f"{pas}{k}: {v};\n" for k, v in d.items())

    out = {}
    for f, roles in par_fichier.items():
        sombre = {k: v for k, r in roles.items() if (v := ctx.valeur(r, "sombre"))}
        clair = {k: v for k, r in roles.items() if k in sombre and (v := ctx.valeur(r, "clair"))}
        if not sombre:
            continue
        if ctx.clair_d_abord:
            out[f] = ("\n/* Thème sombre : généré depuis les jetons de la charte */\n"
                      "@media (prefers-color-scheme: dark) {\n  :root:not([data-theme=\"light\"]) {\n" + corps(sombre, "    ") + "  }\n}\n"
                      "[data-theme=\"dark\"] {\n" + corps(sombre, "  ") + "}\n")
        else:
            out[f] = ("\n/* Sombre d'abord : thème sombre par défaut, clair sur demande (généré depuis les jetons de la charte) */\n"
                      ":root,\n[data-theme=\"dark\"] {\n" + corps(sombre, "  ") + "}\n"
                      "@media (prefers-color-scheme: light) {\n  :root:not([data-theme=\"dark\"]) {\n" + corps(clair, "    ") + "  }\n}\n"
                      "[data-theme=\"light\"] {\n" + corps(clair, "  ") + "}\n")
    return out


def rendre_plan(res: dict, ctx: Contexte) -> str:
    e = res["entrees"]
    auto = sum(1 for x in e if x["statut"] == "auto")
    revoir = len(e) - auto
    out = [f"# Plan de migration vers la charte v{ctx.jetons['version']}", "",
           "| Fichier | Ligne | Ancien | Nouveau | Rôle | Statut | Note |", "|---|---|---|---|---|---|---|"]
    for x in e:
        out.append(f"| `{x['fichier']}` | {x['ligne']} | `{x['ancien']}` | `{x['nouveau']}` | {x['role']} | {x['statut']} | {x['note']} |")
    out += ["", f"Résumé : {auto} remplacement(s) automatique(s), {revoir} à revoir à la main."]
    if res.get("avertissements"):
        out += ["", "## Avertissements", ""] + [f"- {a}" for a in res["avertissements"]]
    if res["blocs"]:
        out += ["", "## Thème sombre", "",
                "Aucun thème sombre détecté dans le dépôt. Bloc proposé (écrit seulement avec `--appliquer --ajouter-sombre`) :"]
        for f, b in res["blocs"].items():
            out += ["", f"Dans `{f}` :", "", "```css", b.strip("\n"), "```"]
    elif not res["sombre_present"]:
        out += ["", "## Thème sombre", "", "Aucun thème sombre détecté dans le dépôt, et aucune variable migrée pour en générer un."]
    return "\n".join(out) + "\n"


def appliquer(depot: Path, res: dict, ajouter_sombre: bool) -> int:
    modifies = 0
    fichiers = set(res["edits"]) | {Path(f) for f in (res["blocs"] if ajouter_sombre else {})}
    for rel in sorted(fichiers):
        lignes = res["textes"][rel].splitlines(keepends=True)
        suppr: set[int] = set()
        for idx, d, fin, nouveau, retrait in sorted(res["edits"].get(rel, []), key=lambda x: (x[0], -x[1])):
            lignes[idx] = lignes[idx][:d] + nouveau + lignes[idx][fin:]
            if retrait:
                suppr.add(idx)
        lignes = [ln for i, ln in enumerate(lignes) if not (i in suppr and not ln.strip())]
        texte = "".join(lignes)
        if ajouter_sombre and rel.as_posix() in res["blocs"]:
            texte += ("" if texte.endswith("\n") else "\n") + res["blocs"][rel.as_posix()]
        if texte != res["textes"][rel]:
            (depot / rel).write_bytes(texte.encode(res.get("encodages", {}).get(rel, "utf-8")))
            modifies += 1
    return modifies


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("depot", type=Path)
    ap.add_argument("--plan", type=Path)
    ap.add_argument("--appliquer", action="store_true")
    ap.add_argument("--proposer", action="store_true")
    ap.add_argument("--correspondances", type=Path)
    ap.add_argument("--ajouter-sombre", action="store_true")
    ap.add_argument("--clair-d-abord", action="store_true")
    ap.add_argument("--ignorer", action="append", default=[], metavar="GLOB")
    a = ap.parse_args(argv)
    corr = json.loads(a.correspondances.read_text(encoding="utf-8")) if a.correspondances else None
    ctx = Contexte(corr, a.proposer, a.clair_d_abord)
    depot = a.depot.resolve()
    ignorer = list(a.ignorer)
    if a.plan:
        a.plan = a.plan.resolve()
        if a.plan.is_relative_to(depot):  # le plan d'une passe précédente ne fait pas partie du dépôt à migrer
            ignorer.append(a.plan.relative_to(depot).as_posix())
    res = planifier(depot, ignorer, ctx)
    plan = rendre_plan(res, ctx)
    if a.plan:
        a.plan.write_text(plan, encoding="utf-8")
        lieu = "dans le dépôt : ne le commitez pas" if a.plan.is_relative_to(depot) else "hors du dépôt : rien à commiter"
        print(f"Plan écrit dans {a.plan} ({lieu})")
    else:
        print(plan)
    if a.appliquer:
        print(f"Fichiers modifiés : {appliquer(depot, res, a.ajouter_sombre)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
