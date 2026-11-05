# Spécimen Office : deck PPTX et rapport DOCX

Thème clair de la charte (`dist/theme-office.xml` remplace la partie de thème des deux paquets), couverture et fin sur aplat `encre-pleine`.

## Régénérer

```
uv run --group specimens python specimens/office/construire.py   # écrit sortie/deck.pptx, rapport.docx, graphique.png
uv run --group specimens python specimens/office/rendre.py       # COM : écrit rendus/ (Word en instance propre ; PowerPoint fermé seulement s'il n'était pas déjà ouvert)
```

## Fichiers

- `construire.py` : python-pptx et python-docx ; couleurs lues par `jetons.charger()`, séries du graphique en couleurs de thème `accent1` à `accent6`.
- `rendre.py` : PDF et PNG par COM.
- `sortie/` (commité comme livrable témoin, régénéré par `construire.py`) : `deck.pptx` (6 diapositives 16:9), `rapport.docx` (2 pages), `graphique.png` (matplotlib, `charte-clair.mplstyle`).
- `rendus/` : `deck.pdf`, `deck-1.png` à `deck-6.png` (1600 px), `rapport.pdf`, `rapport-1.png`.
- Test : `tests/test_specimen_office.py`.

Les chiffres affichés (diapositive 5, tableau du rapport) sont calculés à la construction depuis les jetons (`contrastes.PAIRES`, pastilles, `couleurs.ecart_minimal`), jamais écrits à la main. Tailles du rapport : celles des jetons converties en pt, puis une seule échelle papier (`base` à 11 pt).

## Polices de rendu

Sora et Atkinson Hyperlegible ne sont pas installées. Le deck est rendu par PowerPoint avec Calibri (apparemment, pour titres et texte) ; Word rend tout le rapport dans une police à empattements (type Cambria), pas dans une famille sans empattement.

## Constats pour la critique

- **Or clair en grand aplat (diapositive 5)** : `accent` `#8F6300` paraît brun, voire boue, en aplat de la moitié de l'écran ; on ne lit plus « or ». Texte blanc (`sur-statut`) dessus lisible. Le point ouvert de la charte reste ouvert : en grand aplat, ce brun ne signale rien.
- **Point d'accent du logotype sur la couverture** : le point `accent` clair (`#8F6300`) sur la tuile `primaire` est presque invisible (brun sur bleu). Le logotype n'a pas de variante pour fond sombre ; la couverture sombre emploie les jetons clairs.
- **Thème fondé sur le clair seulement** : la couverture sombre est un aplat `encre-pleine` clair (`#121821`), le reste du deck est clair. Pas de thème sombre complet pour Office.
- **Deux séries catégorielles voisines** (`cat-1` bleu, `cat-6` teal ; `cat-4` orange, `cat-5` rose) : distinctes à l'écran, mais la couleur seule les sépare (pas de motif ni d'étiquette de données).
- **Thème Office limité à six accents** : les séries 7 et 8 (`cat-7`, `cat-8`) n'ont pas de place dans `clrScheme`.
- **Graphique du rapport** : la légende (cadre blanc) recouvre la série « Revue » à Février ; le titre est centré alors que le reste du rapport est aligné à gauche. Les ticks de l'axe y portent un `0` chevauché (« 10 ») dans la police de repli.
- **Rapport** : le tableau des mesures tient sur la page 2. Une cellule d'alerte portant seulement une bordure gauche `alerte` (orange) et un fond `alerte-doux` : lisible, sans icône.
- **Polices de repli** : sans Sora ni Atkinson, la hiérarchie typographique de la charte n'est pas jugeable sur ces rendus. Le rapport s'affiche en empattements, ce qui contredit la charte (sans empattement) ; à embarquer les polices ou à documenter le repli.
