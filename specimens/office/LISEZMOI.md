# Spécimen Office : deck PPTX et rapport DOCX

Thème clair de la charte (`dist/theme-office.xml` remplace la partie de thème des deux paquets), couverture et fin sur aplat `encre-pleine` avec pictogramme et filet en valeurs sombres (règle « fond sombre »). Polices de la charte incorporées aux deux paquets.

## Régénérer

```
uv run --group specimens python specimens/office/construire.py   # écrit sortie/deck.pptx, rapport.docx, graphique.png
uv run --group specimens python specimens/office/rendre.py       # COM : écrit rendus/, puis vérifie les polices des PDF
uv run --no-project python -I specimens/office/polices_pdf.py    # preuve seule, sur les PDF déjà rendus
```

`rendre.py` refuse de rendre si une police de la charte est installée sur le poste (sinon la preuve ne vaudrait rien). Word est lancé en instance propre ; PowerPoint n'est fermé que s'il n'était pas déjà ouvert.

## Fichiers

- `construire.py` : python-pptx et python-docx ; couleurs lues par `jetons.charger()`, séries du graphique en couleurs de thème `accent1` à `accent6`.
- `incorporer.py` : incorporation des polices (bibliothèque standard), appelée par `construire.py`.
- `polices_pdf.py` : vérifie que les polices ne sont pas installées et lit les polices des PDF.
- `rendre.py` : PDF et PNG par COM.
- `sortie/` (commité comme livrable témoin) : `deck.pptx` (6 diapositives 16:9), `rapport.docx` (3 pages), `graphique.png` (matplotlib, `charte-document.mplstyle`, étiquettes directes).
- `rendus/` : `deck.pdf`, `deck-1.png` à `deck-6.png` (1280 px, export PNG de PowerPoint), `rapport.pdf`, `rapport-1.png` (1600 px).
- Tests : `tests/test_specimen_office.py` (construction, groupe `specimens`) et `tests/test_office_polices.py` (paquets livrés et PDF, bibliothèque standard).

Les chiffres affichés (diapositive 5, tableau du rapport) sont calculés à la construction depuis les jetons, jamais écrits à la main.

## Polices incorporées (B3)

Licence : SIL Open Font License 1.1, qui permet l'incorporation (« can be bundled, embedded, redistributed and/or sold with any software », préambule des `skills/charte/polices/OFL-*.txt`) ; `fsType` 0 dans les trois `ttf`.

Noms vus par Office (nom ID 1 des `ttf` fournis) : `Sora SemiBold` (le seul `ttf` de Sora est la graisse 600), `Atkinson Hyperlegible` (normal et gras), `JetBrains Mono`.

| Format | Recette | Résultat (rendu PDF par COM, 2026-11-05) |
|---|---|---|
| DOCX | `word/fonts/font1..4.odttf` obfusqués (§17.8.1, clé `w:fontKey` lue octets inversés), `w:embedRegular`/`w:embedBold`, `fontTable.xml.rels`, type `odttf`, `w:embedTrueTypeFonts` | **réussi** : Word emploie les quatre polices ; ouverture par COM sans erreur (alertes coupées : l'absence de demande de réparation n'est pas vérifiée à l'écran) |
| PPTX, TTF brut | `ppt/fonts/*.fntdata` = `ttf` tel quel, `p:embeddedFontLst` après `p:notesSz` | **échec** : PowerPoint ignore la police, rendu en Calibri |
| PPTX, EOT | même recette, `fntdata` en Embedded OpenType 0x00020001 sans compression (défaut de `construire.py`) | **réussi** : PowerPoint emploie les quatre polices |

Preuve (`polices_pdf.py`) : aucune police de la charte dans `C:\Windows\Fonts`, `%LOCALAPPDATA%\Microsoft\Windows\Fonts` ni dans le registre (HKCU et HKLM). Word et PowerPoint renomment les polices incorporées dans le PDF (`___WRD_EMBED_SUB_46`, `1`, `2`…) ; le script lit donc aussi le nom PostScript des programmes de police incorporés au PDF, après décompression des flux.

- `deck.pdf` : `Sora-SemiBold`, `AtkinsonHyperlegible-Regular`, `AtkinsonHyperlegible-Bold`, `JetBrainsMono-Regular` (et `Arial`, voir constats).
- `rapport.pdf` : `Sora-SemiBold`, `AtkinsonHyperlegible-Regular`, `AtkinsonHyperlegible-Bold`, `JetBrainsMono-Regular` (et `Cambria`, `Calibri`, `Times New Roman` gras, voir constats).

PNG : l'export par diapositive de PowerPoint (`Slide.Export`) ignore les polices incorporées ; `rendre.py` prend donc l'export PNG de la présentation (`SaveAs`, 1280 px). Pour le rapport, le métafichier de la page 1 nomme les polices `___WRD_EMBED_SUB_NN` : `rendre.py` leur rend leur nom d'après le PDF, puis les trace avec les `ttf` chargés en privé pour ce seul processus (rien n'est installé).

Repli si un lecteur ignore les polices incorporées : Segoe UI Semibold pour les titres, Segoe UI pour le texte (voir `docs/CHARTE.md`). Le thème Office ne peut pas le déclarer.

## Règles appliquées (v2.1)

- Couverture et fin : pictogramme sombre (`pictogramme-tuile` #3B6FD0, point `pictogramme-point` #F0D27A, décision d'Anaël du 2026-11-05), filet or sombre `#E3C26B` sous le titre (filet épais : 10,35:1 sur l'aplat).
- Titres de diapositive à 28 pt, en `Sora SemiBold` sans gras synthétique.
- Graphiques : 4 puis 6 séries au plus, étiquette de données (nom de la série) sur chaque barre.
- Diapositive 5 : aplat d'or en `accent-aplat`, texte `texte`.
- Rapport : filet or (`accent`, 3 pt) sous le titre ; figure en style « document », étiquettes directes sans légende ; code en JetBrains Mono ; encadré d'alerte avec icône.

## Constats pour la critique

- **Graphiques natifs PowerPoint** : leur texte (axes, étiquettes, légende) sort en Arial dans le PDF, même avec la police nommée explicitement : le moteur de graphiques ne prend pas les polices incorporées.
- **Glyphes hors du sous-ensemble latin** : `Δ` (tableau du rapport) et `▲` (encadré d'alerte) ne sont pas dans les `ttf` fournis ; Word les prend dans une police de repli (Cambria, Calibri, Times New Roman gras dans le PDF).
- **Thème Office limité à six accents** : documenté (au plus six séries en diapositive).
- **Rapport** : trois pages au lieu de deux (Sora et Atkinson sont plus larges que les polices de repli).
