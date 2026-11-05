# ruff: noqa: E501
"""Construit le deck PPTX et le rapport DOCX du spécimen Office, depuis les jetons clairs.

    uv run --group specimens python specimens/office/construire.py [--fntdata eot|ttf]

Le thème `dist/theme-office.xml` remplace `ppt/theme/theme1.xml` (deck) et `word/theme/theme1.xml` (rapport).
Les polices de la charte sont incorporées aux deux paquets (`incorporer.py`). Sur les aplats sombres (couverture,
fin), pictogramme et filet prennent les valeurs du thème sombre (règle A4).
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
CHARTE = RACINE / "skills" / "charte"
sys.path.insert(0, str(CHARTE / "outils"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RACINE / "specimens" / "graphiques"))

from contrastes import PAIRES, PASTILLES, SEUIL_SERIES, TAUX_PASTILLE  # noqa: E402
from couleurs import contraste, ecart_minimal, melange  # noqa: E402
from incorporer import incorporer_docx, incorporer_pptx  # noqa: E402
from jetons import PICTOGRAMME, charger  # noqa: E402
from placement import placer  # noqa: E402

SORTIE = Path(__file__).resolve().parent / "sortie"
THEME = (CHARTE / "dist" / "theme-office.xml").read_bytes()
J = charger()
C, S = J["clair"], J["sombre"]
NOM = "Charte générique"
TITRES, TEXTE = "+mj-lt", "+mn-lt"  # polices du thème : Sora SemiBold et Atkinson Hyperlegible
POLICE_TITRES, POLICE_TEXTE, POLICE_CODE = (J["police"][r]["office"] for r in ("titres", "texte", "code"))  # noms vus par Office
TITRE_DIAPO_PT = 28  # règle A12 : titres de diapositive d'au moins 28 pt
SERIES_DIAPO = 6  # règle A12 : au plus six séries par graphique de diapositive (thème Office : accent1 à accent6)


def rgb(hexa: str):
    from pptx.dml.color import RGBColor

    return RGBColor.from_string(hexa.lstrip("#"))


def pt(px: float) -> float:
    return px * 0.75


def mesures(theme: str) -> dict[str, float]:
    """Mesures réelles de la charte, recalculées depuis les jetons (aucun chiffre écrit à la main)."""
    t = J[theme]
    return {
        "texte": min([contraste(t[a], t[b]) for a, b, seuil, _ in PAIRES if seuil == 4.5]
                     + [contraste(t[k], melange(t[k], t["surface"], TAUX_PASTILLE)) for k in PASTILLES]),
        "non-texte": min(contraste(t[a], t[b]) for a, b, seuil, _ in PAIRES if seuil == 3.0),
        "series": ecart_minimal(t["cat"])[0],
    }


def virgule(x: float, n: int = 2) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def picto(theme: str) -> dict[str, str]:
    """Couleurs de la tuile, des barres et du point (`jetons.PICTOGRAMME`)."""
    return {k: J[theme][r] for k, r in PICTOGRAMME[theme].items()}


def remplacer_theme(chemin: Path, partie: str) -> None:
    """Réécrit le paquet en remplaçant la partie de thème par celle de la charte."""
    tmp = chemin.with_suffix(chemin.suffix + ".tmp")
    with zipfile.ZipFile(chemin) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            dst.writestr(info, THEME if info.filename == partie else src.read(info.filename))
    tmp.replace(chemin)


# ---------------------------------------------------------------- deck

def deck(chemin: Path, fntdata: str = "eot") -> None:
    from pptx import Presentation
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
    from pptx.enum.dml import MSO_THEME_COLOR
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
    from pptx.util import Emu, Inches, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    L, H = prs.slide_width, prs.slide_height
    marge = Inches(0.8)

    def fond(slide, couleur):
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb(couleur)

    def texte(slide, x, y, w, h, contenu, taille, couleur, police=TEXTE, gras=False, align=PP_ALIGN.LEFT, ancre=MSO_ANCHOR.TOP):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = ancre
        for i, ligne in enumerate(contenu if isinstance(contenu, list) else [contenu]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = ligne
            r.font.size, r.font.name, r.font.bold = Pt(taille), police, gras
            r.font.color.rgb = rgb(couleur)
        return tb

    def titre(slide, contenu, couleur=C["texte"]):
        t = slide.shapes.title
        t.left, t.top, t.width, t.height = marge, Inches(0.5), L - 2 * marge, Inches(1.1)
        t.text_frame.text = contenu
        t.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = t.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        f = p.runs[0].font
        f.size, f.name, f.bold = Pt(max(pt(J["taille"]["titre-2"]), TITRE_DIAPO_PT)), TITRES, False
        f.color.rgb = rgb(couleur)

    def aplat(slide, forme, x, y, w, h, couleur):
        s = slide.shapes.add_shape(forme, x, y, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(couleur)
        s.line.fill.background()
        return s

    def logotype(slide, x, y, cote, couleur_nom, theme):
        """Pictogramme (tuile, trois barres, point d'accent) aux couleurs du thème, puis nom en Sora."""
        u = cote / 32
        p = picto(theme)
        aplat(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, cote, cote, p["tuile"]).adjustments[0] = 8 / 32
        for x1, x2, yy in ((9, 23, 10), (9, 18, 16), (9, 23, 22)):
            b = aplat(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x + int(u * x1), y + int(u * (yy - 1.5)), int(u * (x2 - x1)), int(u * 3), p["barres"])
            b.adjustments[0] = 0.5
        aplat(slide, MSO_SHAPE.OVAL, x + int(u * 20.5), y + int(u * 13.5), int(u * 5), int(u * 5), p["point"])
        texte(slide, x + cote + Emu(76200), y, Inches(5), cote, NOM, 24, couleur_nom, TITRES, ancre=MSO_ANCHOR.MIDDLE)

    vide, titre_seul = prs.slide_layouts[6], prs.slide_layouts[5]

    # 1. couverture : aplat sombre, donc pictogramme et filet or en valeurs sombres (A4) ; filet sous le titre (B5)
    s = prs.slides.add_slide(vide)
    fond(s, C["encre-pleine"])
    logotype(s, marge, Inches(0.7), Inches(0.6), C["sur-encre"], "sombre")
    texte(s, marge, Inches(1.9), Inches(11.5), Inches(2.2), "Une charte lisible, d'abord sombre", pt(J["taille"]["titre-1"]) * 1.25, C["sur-encre"], TITRES,
          ancre=MSO_ANCHOR.BOTTOM)
    aplat(s, MSO_SHAPE.RECTANGLE, marge, Inches(4.25), Inches(1.6), Inches(0.08), S["accent"])  # filet épais : or sombre, 10,35:1 sur l'aplat
    texte(s, marge, Inches(4.5), Inches(10), Inches(1), "Spécimen Office : deck et rapport construits depuis les jetons", pt(J["taille"]["titre-4"]), C["sur-encre-attenue"])

    # 2. titre et puces
    s = prs.slides.add_slide(titre_seul)
    fond(s, C["fond"])
    titre(s, "Trois règles pour tenir la charte")
    puces = ["Un seul geste fort par écran : le bouton principal, neutre et très contrasté", "Le bleu navigue et sélectionne ; l'or signale",
             "Jamais la couleur seule : toujours un libellé ou une icône", "Texte courant en Atkinson Hyperlegible, titres en Sora 600, incorporées"]
    tb = texte(s, marge, Inches(1.9), L - 2 * marge, Inches(3.6), puces, pt(J["taille"]["titre-4"]), C["texte"])
    for p in tb.text_frame.paragraphs:
        p.space_after = Pt(14)
        p.runs[0].text = "•  " + p.runs[0].text
    texte(s, marge, Inches(5.7), L - 2 * marge, Inches(0.6), "uv run --no-project python -I skills/charte/generer.py", pt(J["taille"]["base"]), C["texte"], POLICE_CODE)

    # 3. graphiques natifs (4 séries, puis 6) : étiquette directe dès deux séries en clair (A2), au plus six séries (A12)
    s = prs.slides.add_slide(titre_seul)
    fond(s, C["fond"])
    titre(s, "Séries catégorielles, étiquetées : quatre puis six")
    couleurs_theme = [MSO_THEME_COLOR.ACCENT_1, MSO_THEME_COLOR.ACCENT_2, MSO_THEME_COLOR.ACCENT_3,
                      MSO_THEME_COLOR.ACCENT_4, MSO_THEME_COLOR.ACCENT_5, MSO_THEME_COLOR.ACCENT_6]
    for nb, x in ((4, marge), (SERIES_DIAPO, Inches(6.9))):
        cd = CategoryChartData()
        cd.categories = ["T1", "T2", "T3"]
        for i in range(nb):
            cd.add_series(f"S{i + 1}", [3 + (i * 2 + j * 3) % 7 for j in range(3)])
        ch = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, Inches(1.8), Inches(5.65), Inches(4.9), cd).chart
        ch.has_legend = True
        ch.legend.position, ch.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
        ch.font.size, ch.font.name = Pt(pt(J["taille"]["petit"])), POLICE_TEXTE  # nom explicite : un graphique ne résout pas +mn-lt
        ch.font.color.rgb = rgb(C["texte"])
        for i, serie in enumerate(ch.plots[0].series):
            serie.format.fill.solid()
            serie.format.fill.fore_color.theme_color = couleurs_theme[i]
        ch.plots[0].has_data_labels = True
        etiquettes = ch.plots[0].data_labels  # étiquette de données : nom de la série au bout de chaque barre
        etiquettes.show_series_name, etiquettes.show_value = True, False
        etiquettes.position = XL_LABEL_POSITION.OUTSIDE_END
        etiquettes.font.size, etiquettes.font.name = Pt(pt(J["taille"]["legende"])), POLICE_TEXTE
        etiquettes.font.color.rgb = rgb(C["texte"])
        ch.value_axis.major_gridlines.format.line.color.rgb = rgb(C["trait"])
        ch.value_axis.format.line.fill.background()
        ch.category_axis.format.line.color.rgb = rgb(C["trait"])

    # 4. tableau
    s = prs.slides.add_slide(titre_seul)
    fond(s, C["fond"])
    titre(s, "Statuts : couleur et libellé")
    lignes = [("Statut", "Couleur", "Usage"), ("Succès", "succes", "Opération terminée"), ("Alerte", "alerte-texte", "Attention requise"),
              ("Erreur", "erreur", "Action impossible"), ("Information", "primaire", "Navigation, sélection"), ("Accent", "accent-texte", "Signal, jamais seul")]
    tbl = s.shapes.add_table(len(lignes), 3, marge, Inches(1.9), L - 2 * marge, Inches(0.7) * len(lignes)).table
    for ci, w in enumerate((3.5, 3.5, 4.733)):
        tbl.columns[ci].width = Inches(w)
    for ri, ligne in enumerate(lignes):
        for ci, val in enumerate(ligne):
            cell = tbl.cell(ri, ci)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(C["encre-pleine"] if ri == 0 else (C["surface"] if ri % 2 else C["surface-alt"]))
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            r = cell.text_frame.paragraphs[0].add_run()
            r.text = val
            r.font.size, r.font.name = Pt(pt(J["taille"]["grand"])), TEXTE
            r.font.bold = ri == 0 or ci == 0
            r.font.color.rgb = rgb(C["sur-encre"] if ri == 0 else (C[ligne[1]] if ci == 1 else C["texte"]))

    # 5. chiffre clé, or en grand aplat : `accent-aplat` et texte `texte` (B2)
    s = prs.slides.add_slide(vide)
    fond(s, C["fond"])
    aplat(s, MSO_SHAPE.RECTANGLE, 0, 0, Inches(6.2), H, C["accent-aplat"])
    texte(s, Inches(0.6), Inches(1.5), Inches(5.2), Inches(2.6), virgule(mesures("clair")["texte"]) + ":1", 80, C["texte"], TITRES, ancre=MSO_ANCHOR.MIDDLE)
    texte(s, Inches(0.6), Inches(4.2), Inches(5.2), Inches(1.4), "contraste minimal du texte en thème clair, calculé sur les paires de la charte (seuil 4,5:1)", pt(J["taille"]["titre-4"]), C["texte"])
    texte(s, Inches(6.9), Inches(2.0), Inches(5.7), Inches(3.4), "« Un seul geste fort par écran. »", pt(J["taille"]["titre-3"]) * 1.2, C["texte"], TITRES, ancre=MSO_ANCHOR.MIDDLE)
    texte(s, Inches(6.9), Inches(5.4), Inches(5.7), Inches(0.6), "Principe n° 4 de la charte", pt(J["taille"]["base"]), C["texte-attenue"])

    # 6. fin
    s = prs.slides.add_slide(vide)
    fond(s, C["encre-pleine"])
    logotype(s, marge, Inches(0.7), Inches(0.6), C["sur-encre"], "sombre")
    texte(s, marge, Inches(2.9), Inches(11), Inches(1.2), "Merci", pt(J["taille"]["titre-1"]) * 1.5, C["sur-encre"], TITRES)
    texte(s, marge, Inches(4.4), Inches(10), Inches(0.8), "Charte générique, version " + J["version"], pt(J["taille"]["titre-4"]), C["sur-encre-attenue"])

    chemin.parent.mkdir(parents=True, exist_ok=True)
    prs.save(chemin)
    remplacer_theme(chemin, "ppt/theme/theme1.xml")
    incorporer_pptx(chemin, fntdata)


# ---------------------------------------------------------------- rapport

def graphique_png(chemin: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    for ttf in (CHARTE / "polices").glob("*.ttf"):
        font_manager.fontManager.addfont(str(ttf))
    with plt.style.context(str(CHARTE / "dist" / "charte-document.mplstyle")):
        fig, ax = plt.subplots(figsize=(6.5, 3.2))
        mois = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin"]
        series = {nom: [4 + i + (k * (i + 2)) % 5 for k in range(6)] for i, nom in enumerate(("Lecture", "Écriture", "Revue"))}
        lignes = [ax.plot(range(6), v)[0] for v in series.values()]
        ax.set_xticks(range(6), mois)
        ax.set_xlim(-0.3, 5.9)
        ax.set_title("Activité par mois")
        # étiquette directe dès deux séries en clair (A2), sans chevauchement : écart d'une hauteur de ligne, en points
        ax.get_ylim()  # fige l'échelle avant de convertir en points
        taille = plt.rcParams["font.size"]
        fin = [ax.transData.transform((5, v[-1]))[1] * 72 / fig.dpi for v in series.values()]
        for nom, ligne, y0, y in zip(series, lignes, fin, placer(fin, taille * 1.25), strict=True):
            ax.annotate(nom, (5, series[nom][-1]), xytext=(8, y - y0), textcoords="offset points", va="center",
                        color=ligne.get_color(), fontweight="bold")
        fig.savefig(chemin)
        plt.close(fig)


def rapport(chemin: Path, png: Path) -> None:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    def rvb(h):
        return RGBColor.from_string(h.lstrip("#"))

    def fonte(style, police, taille, couleur):
        style.font.name, style.font.size = police, Pt(taille)
        style.font.color.rgb = rvb(couleur)
        rpr = style.element.get_or_add_rPr()
        rf = rpr.find(qn("w:rFonts"))
        if rf is None:
            rf = OxmlElement("w:rFonts")
            rpr.insert(0, rf)
        for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            rf.attrib.pop(qn(a), None)
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            rf.set(qn(a), police)

    def ombrer(cell, fond_hex):
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), fond_hex.lstrip("#"))
        tcpr = cell._tc.get_or_add_tcPr()
        bords = tcpr.find(qn("w:tcBorders"))
        if bords is not None:  # ordre du schéma CT_TcPr : tcW, …, tcBorders, shd, …
            bords.addnext(shd)
        else:
            tcpr.append(shd)

    def bordure(cell, cotes):
        b = OxmlElement("w:tcBorders")
        for cote, (couleur, taille) in cotes.items():
            e = OxmlElement(f"w:{cote}")
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(taille))
            e.set(qn("w:color"), couleur.lstrip("#"))
            b.append(e)
        tcpr = cell._tc.get_or_add_tcPr()
        shd = tcpr.find(qn("w:shd"))
        if shd is not None:
            shd.addprevious(b)
        else:
            tcpr.append(b)

    d = Document()
    sec = d.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2.3)
    sec.top_margin = sec.bottom_margin = Cm(2.2)
    st = d.styles
    papier = 11 / pt(J["taille"]["base"])  # une seule échelle papier : `base` à 11 pt, rapports des jetons conservés
    fonte(st["Normal"], POLICE_TEXTE, pt(J["taille"]["base"]) * papier, C["texte"])
    st["Normal"].paragraph_format.space_after = Pt(8)
    st["Normal"].paragraph_format.line_spacing = 1.35
    for nom, taille in (("Title", J["taille"]["titre-1"]), ("Heading 1", J["taille"]["titre-2"]), ("Heading 2", J["taille"]["titre-3"]), ("Heading 3", J["taille"]["titre-4"])):
        fonte(st[nom], POLICE_TITRES, round(pt(taille) * papier * 2) / 2, C["texte"] if nom != "Heading 3" else C["primaire-vif"])
        st[nom].font.bold = False  # « Sora SemiBold » porte déjà la graisse 600 : pas de gras synthétique
        st[nom].paragraph_format.space_before = Pt(14)
        st[nom].paragraph_format.space_after = Pt(6)
    ppr = st["Title"].element.get_or_add_pPr()
    if ppr.find(qn("w:pBdr")) is not None:
        ppr.remove(ppr.find(qn("w:pBdr")))
    # filet or sous le titre (B5) : trait `accent` de 3 pt, 5,31:1 sur `surface`
    bdr, bas = OxmlElement("w:pBdr"), OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "24"), ("w:space", "6"), ("w:color", C["accent"].lstrip("#"))):
        bas.set(qn(k), v)
    bdr.append(bas)
    suivants = [qn(f"w:{t}") for t in ("shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap", "overflowPunct", "topLinePunct", "autoSpaceDE",
                                       "autoSpaceDN", "bidi", "adjustRightInd", "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents",
                                       "suppressOverlap", "jc", "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId",
                                       "cnfStyle", "rPr", "sectPr", "pPrChange")]
    suivant = next((e for e in ppr if e.tag in suivants), None)  # CT_PPrBase : pBdr avant shd, spacing, jc…
    if suivant is not None:
        suivant.addprevious(bdr)
    else:
        ppr.append(bdr)

    d.add_heading("Rapport d'activité", 0)
    d.add_paragraph("Spécimen Office : un rapport construit depuis les jetons de la charte générique, en thème clair.")
    d.add_heading("1. Contexte", 1)
    for _ in range(2):
        d.add_paragraph("La charte repose sur une source unique de jetons. Chaque sortie, page web, graphique ou document Office, en est dérivée par un générateur, "
                        "ce qui évite toute valeur écrite à la main et garde les contrastes vérifiés par construction.")
    d.add_heading("1.1 Principes", 2)
    d.add_paragraph("Le bleu sert à naviguer et à sélectionner, l'or à signaler. La couleur n'est jamais seule : un libellé ou une icône l'accompagne toujours.")
    d.add_heading("1.1.1 Typographie", 3)
    d.add_paragraph("Les titres sont en Sora 600, le texte courant en Atkinson Hyperlegible, le code en JetBrains Mono. Les trois polices sont incorporées au document.")
    code = d.add_paragraph().add_run("uv run --no-project python -I skills/charte/generer.py --verifier")
    code.font.name, code.font.size = POLICE_CODE, Pt(9.5)

    d.add_heading("2. Résultats", 1)
    d.add_picture(str(png), width=Cm(15.5))
    d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    leg = d.add_paragraph("Figure 1. Activité par mois (matplotlib, style charte-document, étiquettes directes).")
    leg.runs[0].font.size, leg.runs[0].font.color.rgb = Pt(10), rvb(C["texte-attenue"])
    leg.alignment = WD_ALIGN_PARAGRAPH.CENTER

    mc, ms = mesures("clair"), mesures("sombre")
    lignes = [("Mesure (calculée depuis les jetons)", "Clair", "Sombre", "Seuil"),
              ("Contraste minimal du texte", virgule(mc["texte"]) + ":1", virgule(ms["texte"]) + ":1", "4,5:1"),
              ("Contraste minimal non textuel", virgule(mc["non-texte"]) + ":1", virgule(ms["non-texte"]) + ":1", "3:1"),
              ("Écart minimal entre séries (ΔE00)", virgule(mc["series"], 1), virgule(ms["series"], 1), f"{SEUIL_SERIES:g}")]
    t = d.add_table(rows=len(lignes), cols=4)
    for ri, ligne in enumerate(lignes):
        for ci, val in enumerate(ligne):
            cell = t.cell(ri, ci)
            r = cell.paragraphs[0].add_run(val)
            r.bold = ri == 0
            r.font.color.rgb = rvb(C["sur-encre"] if ri == 0 else C["texte"])
            cell.paragraphs[0].paragraph_format.space_after = Pt(2)
            ombrer(cell, C["encre-pleine"] if ri == 0 else (C["surface"] if ri % 2 else C["surface-alt"]))
            bordure(cell, {k: (C["trait"], 4) for k in ("top", "left", "bottom", "right")})
    d.add_paragraph()

    d.add_heading("3. Points d'attention", 1)
    cell = d.add_table(rows=1, cols=1).cell(0, 0)
    ombrer(cell, C["alerte-doux"])
    bordure(cell, {"left": (C["alerte"], 36)})
    p = cell.paragraphs[0]
    r = p.add_run("▲ Attention. ")
    r.bold, r.font.color.rgb = True, rvb(C["alerte-texte"])
    r2 = p.add_run("Les polices de la charte sont incorporées au document. Si un lecteur les refuse, le repli est Segoe UI Semibold pour les titres et Segoe UI pour le texte.")
    r2.font.color.rgb = rvb(C["texte"])
    d.add_paragraph()
    d.add_paragraph("L'or sert d'accent : accent-aplat pour les grands aplats, accent pour les marques fines et le filet, accent-texte pour le texte.")
    for _ in range(3):
        d.add_paragraph("Un point de suivi reste ouvert : vérifier le rendu de chaque sortie dans les lecteurs qui ignorent les polices incorporées.")

    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fp.add_run(f"{NOM} · version {J['version']} · page ")
    r.font.size, r.font.color.rgb = Pt(9), rvb(C["texte-attenue"])
    r = fp.add_run()
    r.font.size, r.font.color.rgb = Pt(9), rvb(C["texte-attenue"])
    for typ, txt in (("begin", None), (None, " PAGE "), ("end", None)):
        if typ:
            e = OxmlElement("w:fldChar")
            e.set(qn("w:fldCharType"), typ)
        else:
            e = OxmlElement("w:instrText")
            e.set(qn("xml:space"), "preserve")
            e.text = txt
        r._r.append(e)

    d.core_properties.title = "Rapport d'activité"
    d.save(chemin)
    remplacer_theme(chemin, "word/theme/theme1.xml")
    incorporer_docx(chemin)


def main(argv: list[str] | None = None) -> None:
    import argparse

    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--fntdata", choices=("ttf", "eot"), default="eot", help="format des polices incorporées au PPTX (ttf brut : ignoré par PowerPoint)")
    a = ap.parse_args(argv)
    SORTIE.mkdir(exist_ok=True)
    graphique_png(SORTIE / "graphique.png")
    deck(SORTIE / "deck.pptx", a.fntdata)
    rapport(SORTIE / "rapport.docx", SORTIE / "graphique.png")
    print("Construit :", *sorted(p.name for p in SORTIE.iterdir()))


if __name__ == "__main__":
    main()
