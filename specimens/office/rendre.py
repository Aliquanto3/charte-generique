"""Rendus par COM (PowerPoint et Word) dans `rendus/` : PDF du deck et du rapport, PNG de chaque diapositive et de la page 1 du rapport.

PNG du deck : `SaveAs` au format PNG (1280 px), qui emploie les polices incorporées (`Slide.Export` les ignore).
PNG du rapport : métafichier de la page 1 mis en page par Word. Word y nomme les polices incorporées
`___WRD_EMBED_SUB_NN` ; on rend leur nom de famille d'après le PDF (nom PostScript du programme incorporé, puis nom
ID 1 du `ttf` de la charte), et Python trace le métafichier avec GDI après avoir chargé ces `ttf` en privé
(`AddFontResourceEx`, `FR_PRIVATE` : ce processus seulement, rien n'est installé). La preuve d'incorporation reste
le PDF (`polices_pdf.py`).

    uv run --group specimens python specimens/office/rendre.py

Vérifie d'abord que les polices de la charte ne sont pas installées, puis, après le rendu, qu'elles figurent dans
les deux PDF (`polices_pdf.py`). Word est lancé en instance propre (`DispatchEx`) et toujours fermé. PowerPoint n'a qu'une instance par session :
si l'utilisateur l'a déjà ouvert, on ne ferme que notre présentation, jamais son application.
"""
from __future__ import annotations

import io
import re
import shutil
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
POLICES = ICI.parents[1] / "skills" / "charte" / "polices"
SORTIE = ICI / "sortie"
RENDUS = ICI / "rendus"
LARGEUR = 1600


def _en_cours(image: str) -> bool:
    """Vrai si le processus tourne. En cas de doute (tasklist absent, erreur), vrai : on ne ferme alors rien."""
    import subprocess

    try:
        r = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {image}", "/NH"], capture_output=True, text=True, errors="replace", timeout=30)
    except (OSError, subprocess.SubprocessError):
        return True
    if r.returncode != 0:
        return True
    return image.lower() in r.stdout.lower()


def _fermer(objet, *args) -> None:
    """Ferme sans laisser une erreur empêcher la fermeture suivante."""
    try:
        objet(*args)
    except Exception as e:  # noqa: BLE001
        print("Fermeture COM en échec :", e)


def _vide(app) -> bool:
    try:
        return app.Presentations.Count == 0
    except Exception:  # noqa: BLE001
        return False


def polices_privees() -> int:
    """Charge les ttf de la charte pour ce processus seulement (FR_PRIVATE) ; rend le nombre de polices chargées."""
    import ctypes

    fr_private = 0x10
    return sum(ctypes.windll.gdi32.AddFontResourceExW(str(f), fr_private, 0) for f in sorted(POLICES.glob("*.ttf")))


def renommer_polices_emf(emf: bytes, pdf: bytes) -> bytes:
    """Remplace dans le métafichier (champ `lfFaceName`, 32 WCHAR) les noms internes de Word par les familles de la charte."""
    import polices_pdf

    familles = {polices_pdf.nom_ttf(f.read_bytes(), 6): polices_pdf.nom_ttf(f.read_bytes(), 1) for f in POLICES.glob("*.ttf")}
    for nom_pdf, ps in polices_pdf.programmes(pdf).items():
        interne, famille = nom_pdf.split(",")[0], familles.get(ps)
        if not interne.startswith("___WRD_EMBED") or not famille or len(famille) > 31:
            continue
        a = interne.encode("utf-16-le") + b"\x00\x00" * (max(0, len(famille) - len(interne)) + 1)
        emf = emf.replace(a, famille.encode("utf-16-le").ljust(len(a), b"\x00"))
    return emf


def deck() -> None:
    import pythoncom
    import win32com.client as wc

    pythoncom.CoInitialize()
    deja_ouvert = _en_cours("POWERPNT.EXE")
    app = wc.DispatchEx("PowerPoint.Application")
    pres = None
    try:
        app.DisplayAlerts = 1  # ppAlertsNone
        pres = app.Presentations.Open(str(SORTIE / "deck.pptx"), True, False, False)
        pres.SaveAs(str(RENDUS / "deck.pdf"), 32)  # ppSaveAsPDF
        with tempfile.TemporaryDirectory() as tmp:
            pres.SaveAs(str(Path(tmp) / "diapos"), 18)  # ppSaveAsPNG : un fichier par diapositive, nom localisé (Slide1, Diapositive1…)
            pngs = sorted(Path(tmp).rglob("*.png", case_sensitive=False), key=lambda p: int(re.search(r"(\d+)$", p.stem).group(1)))
            for i, png in enumerate(pngs, 1):
                shutil.move(png, RENDUS / f"deck-{i}.png")
    finally:
        if pres is not None:
            _fermer(pres.Close)
        # l'utilisateur a pu ouvrir une présentation pendant le rendu : on ne ferme que si l'application est vide
        if not deja_ouvert and _vide(app):
            _fermer(app.Quit)


def rapport() -> None:
    import pythoncom
    import win32com.client as wc
    from PIL import Image

    pythoncom.CoInitialize()
    app = wc.DispatchEx("Word.Application")
    doc = None
    try:
        app.Visible = False
        app.DisplayAlerts = 0
        doc = app.Documents.Open(str(SORTIE / "rapport.docx"), ReadOnly=True, AddToRecentFiles=False)
        doc.SaveAs2(str(RENDUS / "rapport.pdf"), 17)  # wdFormatPDF
        pages = doc.ComputeStatistics(2)
        print("Pages du rapport :", pages)
        emf = bytes(doc.Windows(1).Panes(1).Pages(1).EnhMetaFileBits)
        emf = renommer_polices_emf(emf, (RENDUS / "rapport.pdf").read_bytes())
        print("Polices chargées en privé pour tracer le métafichier :", polices_privees())
        img = Image.open(io.BytesIO(emf))
        img.load()
        h = round(img.height * LARGEUR / img.width)
        img.convert("RGB").resize((LARGEUR, h), Image.LANCZOS).save(RENDUS / "rapport-1.png")
    finally:
        if doc is not None:
            _fermer(doc.Close, False)
        _fermer(app.Quit)


if __name__ == "__main__":
    import sys

    import polices_pdf

    RENDUS.mkdir(exist_ok=True)
    if polices_pdf.installees():  # la preuve ne vaut que si Office ne peut prendre les polices que dans le document
        sys.exit("Polices de la charte installées sur le poste : rendu refusé, la preuve d'incorporation serait faussée.")
    deck()
    rapport()
    sys.exit(polices_pdf.main([str(RENDUS / "deck.pdf"), str(RENDUS / "rapport.pdf")]))
