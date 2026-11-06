"""Preuve de l'incorporation : polices absentes du poste, puis polices présentes dans les PDF rendus par Office.

    uv run --no-project python -I specimens/office/polices_pdf.py [rendus/deck.pdf rendus/rapport.pdf]

Bibliothèque standard seulement. Lit les `/BaseFont` et `/FontName` du PDF après décompression zlib de tous les
flux (`FlateDecode`), y compris les flux d'objets (`/ObjStm`). Word et PowerPoint renomment les polices incorporées
au document (`___WRD_EMBED_SUB_46`, `1`, `2`…) : on lit donc aussi le nom PostScript (nom ID 6) de chaque programme
de police TrueType incorporé au PDF (`/FontFile2`). Code de sortie 1 si une police de la charte est installée sur
le poste, ou si Sora ou Atkinson Hyperlegible manque à un PDF.
"""
from __future__ import annotations

import os
import re
import struct
import sys
import zlib
from pathlib import Path

ICI = Path(__file__).resolve().parent
MOTS = ("sora", "atkinson", "jetbrains")  # familles de la charte, en minuscules
REQUISES = ("Sora", "Atkinson")  # préfixes des noms PostScript attendus
FLUX = re.compile(rb"stream\r?\n(.*?)\r?\nendstream", re.DOTALL)
NOM = re.compile(rb"/(?:BaseFont|FontName)\s*/([^\s/\[\]<>()]+)")


def nom_pdf(brut: bytes) -> str:
    """Décode un nom PDF (`#20` → espace) et retire le préfixe de sous-ensemble (`ABCDEF+`)."""
    s = re.sub(rb"#([0-9A-Fa-f]{2})", lambda m: bytes([int(m.group(1), 16)]), brut).decode("latin-1")
    return re.sub(r"^[A-Z]{6}\+", "", s)


def flux(donnees: bytes) -> list[bytes]:
    """Contenu décompressé de chaque flux zlib du PDF (les flux non compressés ou d'un autre filtre sont ignorés)."""
    out = []
    for m in FLUX.finditer(donnees):
        try:
            out.append(zlib.decompressobj().decompress(m.group(1)))  # tolère des octets superflus après le flux
        except zlib.error:
            continue
    return out


def nom_postscript(ttf: bytes) -> str | None:
    """Nom PostScript (ID 6) d'un programme TrueType, ou None si ce n'en est pas un."""
    return nom_ttf(ttf, 6)


def nom_ttf(ttf: bytes, identifiant: int) -> str | None:
    """Nom d'identifiant donné d'un programme TrueType (plateformes Unicode et Windows en UTF-16), ou None."""
    if ttf[:4] not in (b"\x00\x01\x00\x00", b"true"):
        return None
    try:
        n = struct.unpack(">H", ttf[4:6])[0]
        repertoire = {ttf[12 + 16 * i: 16 + 16 * i]: struct.unpack(">II", ttf[20 + 16 * i: 28 + 16 * i]) for i in range(n)}
        off, _ = repertoire[b"name"]
        nb, base = struct.unpack(">HH", ttf[off + 2: off + 6])
        for i in range(nb):
            pf, _, _, nid, lg, o = struct.unpack(">6H", ttf[off + 6 + 12 * i: off + 18 + 12 * i])
            if nid == identifiant:
                brut = ttf[off + base + o: off + base + o + lg]
                return brut.decode("utf-16-be" if pf in (0, 3) else "latin-1")
    except (KeyError, struct.error, UnicodeDecodeError):
        return None
    return None


def polices_pdf(donnees: bytes) -> set[str]:
    """Noms des polices du PDF : `/BaseFont` et `/FontName` (texte brut et flux), et noms PostScript des programmes incorporés."""
    blocs = flux(donnees)
    noms = {nom_pdf(n) for bloc in [donnees, *blocs] for n in NOM.findall(bloc)}
    return noms | {p for p in map(nom_postscript, blocs) if p}


def programmes(donnees: bytes) -> dict[str, str]:
    """Nom de police du PDF (sans préfixe de sous-ensemble) → nom PostScript du programme `/FontFile2` incorporé."""
    blocs = [donnees, *flux(donnees)]
    out = {}
    for bloc in blocs:
        for m in re.finditer(rb"/FontName\s*/([^\s/\[\]<>()]+)[^>]*?/FontFile2\s+(\d+)\s+0\s+R", bloc):
            obj = re.search(rb"(?<![0-9])%d 0 obj.*?stream\r?\n(.*?)\r?\nendstream" % int(m.group(2)), donnees, re.DOTALL)
            if obj:
                try:
                    ps = nom_postscript(zlib.decompressobj().decompress(obj.group(1)))
                except zlib.error:
                    ps = None
                if ps:
                    out[nom_pdf(m.group(1))] = ps
    return out


def manquantes(pdfs: list[Path]) -> list[str]:
    """« <pdf> : manquent Sora, … » pour chaque PDF auquel manque une police requise ; liste vide si tout y est."""
    out = []
    for pdf in pdfs:
        noms = polices_pdf(pdf.read_bytes())
        absentes = [r for r in REQUISES if not any(n.startswith(r) for n in noms)]
        if absentes:
            out.append(f"{pdf.name} : manquent {', '.join(absentes)}")
    return out


def installees() -> list[str]:
    """Fichiers ou entrées de registre des polices de la charte sur le poste (système, utilisateur, HKCU, HKLM)."""
    trouve = []
    dossiers = [Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"]
    if os.environ.get("LOCALAPPDATA"):
        dossiers.append(Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "Windows" / "Fonts")
    for d in dossiers:
        if d.is_dir():
            trouve += [str(p) for p in d.iterdir() if any(m in p.name.lower() for m in MOTS)]
    try:
        import winreg
    except ImportError:  # hors Windows : seuls les dossiers comptent
        return trouve
    cle = r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    for racine, nom in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
        try:
            with winreg.OpenKey(racine, cle) as k:
                i = 0
                while True:
                    try:
                        v, d, _ = winreg.EnumValue(k, i)
                    except OSError:
                        break
                    if any(m in f"{v} {d}".lower() for m in MOTS):
                        trouve.append(f"{nom}\\{cle}\\{v}")
                    i += 1
        except OSError:
            continue
    return trouve


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    pdfs = [Path(a) for a in (argv if argv is not None else sys.argv[1:])] or [ICI / "rendus" / "deck.pdf", ICI / "rendus" / "rapport.pdf"]
    code = 0
    poste = installees()
    print("Polices de la charte installées sur le poste :", ", ".join(poste) if poste else "aucune")
    if poste:
        code = 1
    for pdf in pdfs:
        print(f"{pdf.name} : {', '.join(sorted(polices_pdf(pdf.read_bytes())))}")
    manques = manquantes(pdfs)
    for m in manques:
        print(m)
    return 1 if manques else code


if __name__ == "__main__":
    sys.exit(main())
