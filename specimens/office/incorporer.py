"""Incorporation des polices de la charte (Sora, Atkinson Hyperlegible, JetBrains Mono) dans les paquets Office.

Bibliothèque standard seulement. Licence : les trois polices sont sous SIL Open Font License 1.1, qui permet
de les incorporer (« can be bundled, embedded, redistributed and/or sold with any software », préambule des
`skills/charte/polices/OFL-*.txt`) ; leur `fsType` OS/2 vaut 0 (incorporation installable).

- DOCX (ECMA-376 partie 1, §17.8.1) : `word/fonts/fontN.odttf`, police obfusquée par un XOR des 32 premiers
  octets avec la clé GUID `w:fontKey` lue octets inversés ; `w:embedRegular`/`w:embedBold` dans `fontTable.xml`,
  relations `word/_rels/fontTable.xml.rels`, type `odttf`, `w:embedTrueTypeFonts` dans `settings.xml`.
- PPTX : `ppt/fonts/fontN.fntdata`, `p:embeddedFontLst` après `p:notesSz`, attributs `embedTrueTypeFonts` et
  `saveSubsetFonts` sur `p:presentation`. `format="eot"` (défaut) enveloppe le TTF dans un en-tête Embedded
  OpenType (version 0x00020001, sans compression MTX ni XOR) ; `format="ttf"` écrit le TTF tel quel. Essai du
  2026-11-05 (PowerPoint 365, rendu PDF) : le TTF brut est ignoré (rendu en Calibri), l'EOT est employé.

Les clés GUID sont dérivées du nom de la police (uuid5) : la construction reste reproductible.
"""
from __future__ import annotations

import re
import struct
import sys
import uuid
import zipfile
from collections.abc import Callable
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CHARTE = RACINE / "skills" / "charte"
sys.path.insert(0, str(CHARTE / "outils"))

from jetons import charger  # noqa: E402

POLICES = CHARTE / "polices"
J = charger()
# (rôle de la charte, style Office, fichier ttf) ; le nom de famille vu par Office vient de `police.<rôle>.office`.
FICHIERS = [
    ("titres", "regular", "sora-latin-600-normal.ttf"),
    ("texte", "regular", "atkinson-hyperlegible-latin-400-normal.ttf"),
    ("texte", "bold", "atkinson-hyperlegible-latin-700-normal.ttf"),
    ("code", "regular", "jetbrains-mono-latin-400-normal.ttf"),
]
FAMILLE_WORD = {"titres": "swiss", "texte": "swiss", "code": "modern"}
PITCH = {"titres": "variable", "texte": "variable", "code": "fixed"}
PITCH_FAMILY = {"titres": "34", "texte": "34", "code": "49"}  # FF_SWISS|VARIABLE_PITCH, FF_MODERN|FIXED_PITCH
NS_ESPACE = uuid.UUID("6f1c2a52-9f0e-4c3b-8a7d-2b1d5e0c9a41")
REL_FONT = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def polices() -> list[tuple[str, str, str, Path]]:
    """(rôle, style, nom de famille Office, chemin du ttf)."""
    return [(r, st, J["police"][r]["office"], POLICES / f) for r, st, f in FICHIERS]


def cle(nom: str, style: str) -> str:
    return "{" + str(uuid.uuid5(NS_ESPACE, f"{nom}/{style}")).upper() + "}"


def obfusquer(donnees: bytes, cle_guid: str) -> bytes:
    """§17.8.1 : XOR des 32 premiers octets avec les 16 octets de la clé GUID, pris dans l'ordre inverse.

    L'opération est son propre inverse (obfusquer deux fois rend la police d'origine).
    """
    k = bytes.fromhex(cle_guid.strip("{}").replace("-", ""))[::-1]
    return bytes(b ^ k[i % 16] for i, b in enumerate(donnees[:32])) + donnees[32:]


# ---------------------------------------------------------------- lecture TTF (en-têtes nécessaires à l'EOT)

def tables(ttf: bytes) -> dict[str, bytes]:
    n = struct.unpack(">H", ttf[4:6])[0]
    out = {}
    for i in range(n):
        tag, _, off, lg = struct.unpack(">4sIII", ttf[12 + 16 * i: 28 + 16 * i])
        out[tag.decode("latin-1")] = ttf[off: off + lg]
    return out


def noms(ttf: bytes) -> dict[int, str]:
    """Noms Windows (plateforme 3, encodage 1, anglais US) par identifiant."""
    t = tables(ttf)["name"]
    nb, base = struct.unpack(">HH", t[2:6])
    out = {}
    for i in range(nb):
        pf, enc, lang, nid, lg, off = struct.unpack(">6H", t[6 + 12 * i: 18 + 12 * i])
        if (pf, enc, lang) == (3, 1, 0x409):
            out[nid] = t[base + off: base + off + lg].decode("utf-16-be")
    return out


def eot(ttf: bytes) -> bytes:
    """Enveloppe Embedded OpenType 0x00020001, sans compression ni XOR (W3C, « Embedded OpenType File Format »)."""
    t = tables(ttf)
    os2, head = t["OS/2"], t["head"]
    poids, fs_type = struct.unpack(">H", os2[4:6])[0], struct.unpack(">H", os2[8:10])[0]
    panose, unicode_r = os2[32:42], struct.unpack(">4I", os2[42:58])
    fs_selection = struct.unpack(">H", os2[62:64])[0]
    pages = struct.unpack(">2I", os2[78:86]) if len(os2) >= 86 else (0, 0)
    ajust = struct.unpack(">I", head[8:12])[0]
    n = noms(ttf)

    def chaine(s: str) -> bytes:
        b = s.encode("utf-16-le")
        return struct.pack("<HH", 0, len(b)) + b

    corps = (struct.pack("<I", 0x00020001) + struct.pack("<I", 0) + panose + struct.pack("<BB", 1, fs_selection & 1)
             + struct.pack("<IHH", poids, fs_type, 0x504C) + struct.pack("<4I", *unicode_r) + struct.pack("<2I", *pages)
             + struct.pack("<I", ajust) + struct.pack("<4I", 0, 0, 0, 0)
             + chaine(n.get(1, "")) + chaine(n.get(2, "")) + chaine(n.get(5, "")) + chaine(n.get(4, "")) + chaine(""))
    taille = 8 + len(corps) + len(ttf)
    return struct.pack("<II", taille, len(ttf)) + corps + ttf


# ---------------------------------------------------------------- paquets

def reecrire(chemin: Path, modifier: dict[str, Callable[[bytes], bytes]], ajouter: dict[str, bytes]) -> None:
    """Réécrit le paquet : parties modifiées sur place, parties nouvelles ajoutées à la fin."""
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    with zipfile.ZipFile(chemin) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        presentes = set(src.namelist())
        for info in src.infolist():
            data = src.read(info.filename)
            dst.writestr(info, modifier[info.filename](data) if info.filename in modifier else data)
        for nom, data in ajouter.items():
            assert nom not in presentes, f"partie déjà présente : {nom}"
            dst.writestr(nom, data)
    tmp.replace(chemin)


def _type_defaut(ext: str, type_contenu: str) -> Callable[[bytes], bytes]:
    def f(xml: bytes) -> bytes:
        s = xml.decode("utf-8")
        if f'Extension="{ext}"' not in s:
            s = s.replace("<Default ", f'<Default Extension="{ext}" ContentType="{type_contenu}"/><Default ', 1)
        return s.encode("utf-8")
    return f


def incorporer_docx(chemin: Path) -> list[str]:
    """Incorpore les polices dans un DOCX ; rend les noms de famille incorporés."""
    fichiers: dict[str, bytes] = {}
    rels, entrees = [], {}
    for i, (role, style, nom, ttf) in enumerate(polices(), 1):
        k = cle(nom, style)
        fichiers[f"word/fonts/font{i}.odttf"] = obfusquer(ttf.read_bytes(), k)
        rels.append(f'<Relationship Id="rIdPolice{i}" Type="{REL_FONT}" Target="fonts/font{i}.odttf"/>')
        balise = "w:embedRegular" if style == "regular" else "w:embedBold"
        entrees.setdefault(nom, (role, []))[1].append(f'<{balise} r:id="rIdPolice{i}" w:fontKey="{k}"/>')

    def table(xml: bytes) -> bytes:
        s = xml.decode("utf-8")
        if "xmlns:r=" not in s.split(">", 2)[1]:
            s = re.sub(r"<w:fonts ", f'<w:fonts xmlns:r="{NS_R}" ', s, count=1)
        bloc = "".join(f'<w:font w:name="{nom}"><w:charset w:val="00"/><w:family w:val="{FAMILLE_WORD[role]}"/>'
                       f'<w:pitch w:val="{PITCH[role]}"/>{"".join(e)}</w:font>' for nom, (role, e) in entrees.items())
        return s.replace("</w:fonts>", bloc + "</w:fonts>").encode("utf-8")

    def reglages(xml: bytes) -> bytes:
        s = xml.decode("utf-8")
        if "<w:embedTrueTypeFonts" not in s:  # CT_Settings : après w:zoom (et ses prédécesseurs), avant w:proofState
            s = re.sub(r"(<w:zoom[^>]*/>)", r"\1<w:embedTrueTypeFonts/>", s, count=1)
        assert "<w:embedTrueTypeFonts/>" in s, "settings.xml sans w:zoom"
        return s.encode("utf-8")

    relations = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="{NS_REL}">'
                 + "".join(rels) + "</Relationships>").encode("utf-8")
    fichiers["word/_rels/fontTable.xml.rels"] = relations
    reecrire(chemin, {"word/fontTable.xml": table, "word/settings.xml": reglages,
                      "[Content_Types].xml": _type_defaut("odttf", "application/vnd.openxmlformats-officedocument.obfuscatedFont")},
             fichiers)
    return list(entrees)


def incorporer_pptx(chemin: Path, format: str = "eot") -> list[str]:
    """Incorpore les polices dans un PPTX (`format` : « ttf » brut ou « eot ») ; rend les noms incorporés."""
    fichiers: dict[str, bytes] = {}
    rels, entrees = [], {}
    for i, (role, style, nom, ttf) in enumerate(polices(), 1):
        data = ttf.read_bytes()
        fichiers[f"ppt/fonts/font{i}.fntdata"] = eot(data) if format == "eot" else data
        rels.append(f'<Relationship Id="rIdPolice{i}" Type="{REL_FONT}" Target="fonts/font{i}.fntdata"/>')
        entrees.setdefault(nom, (role, {}))[1][style] = f"rIdPolice{i}"

    def presentation(xml: bytes) -> bytes:
        s = xml.decode("utf-8")
        lst = "<p:embeddedFontLst>" + "".join(
            f'<p:embeddedFont><p:font typeface="{nom}" pitchFamily="{PITCH_FAMILY[role]}" charset="0"/>'
            + "".join(f'<p:{st} r:id="{rid}"/>' for st, rid in sorted(styles.items(), key=lambda x: ("regular", "bold").index(x[0])))
            + "</p:embeddedFont>" for nom, (role, styles) in entrees.items()) + "</p:embeddedFontLst>"
        s, n = re.subn(r"(<p:notesSz[^>]*/>)", lambda m: m.group(1) + lst, s, count=1)
        assert n == 1, "presentation.xml sans p:notesSz"
        racine = re.search(r"<p:presentation\b[^>]*>", s).group(0)
        nouvelle = racine
        for attr in ("embedTrueTypeFonts", "saveSubsetFonts"):
            if f"{attr}=" not in nouvelle:
                nouvelle = nouvelle[:-1] + f' {attr}="1">'
        return s.replace(racine, nouvelle, 1).encode("utf-8")

    def relations(xml: bytes) -> bytes:
        return xml.decode("utf-8").replace("</Relationships>", "".join(rels) + "</Relationships>").encode("utf-8")

    reecrire(chemin, {"ppt/presentation.xml": presentation, "ppt/_rels/presentation.xml.rels": relations,
                      "[Content_Types].xml": _type_defaut("fntdata", "application/x-fontdata")}, fichiers)
    return list(entrees)
