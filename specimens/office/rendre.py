"""Rendus par COM (PowerPoint et Word) dans `rendus/` : PDF du deck et du rapport, PNG de chaque diapositive et de la page 1 du rapport.

    uv run --group specimens python specimens/office/rendre.py

Les applications sont lancées en instance propre, sans alerte, et toujours fermées (`Quit`) dans un `finally`.
"""
from __future__ import annotations

import io
from pathlib import Path

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "sortie"
RENDUS = ICI / "rendus"
LARGEUR = 1600


def deck() -> None:
    import pythoncom
    import win32com.client as wc

    pythoncom.CoInitialize()
    app = wc.DispatchEx("PowerPoint.Application")
    pres = None
    try:
        app.DisplayAlerts = 1  # ppAlertsNone
        pres = app.Presentations.Open(str(SORTIE / "deck.pptx"), True, False, False)
        pres.SaveAs(str(RENDUS / "deck.pdf"), 32)  # ppSaveAsPDF
        for i in range(1, pres.Slides.Count + 1):
            pres.Slides(i).Export(str(RENDUS / f"deck-{i}.png"), "PNG", LARGEUR, LARGEUR * 9 // 16)
    finally:
        if pres is not None:
            pres.Close()
        app.Quit()


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
        img = Image.open(io.BytesIO(emf))
        img.load()
        h = round(img.height * LARGEUR / img.width)
        img.convert("RGB").resize((LARGEUR, h), Image.LANCZOS).save(RENDUS / "rapport-1.png")
    finally:
        if doc is not None:
            doc.Close(False)
        app.Quit()


if __name__ == "__main__":
    RENDUS.mkdir(exist_ok=True)
    deck()
    rapport()
