# Spécimen : graphiques et daltonisme

Graphiques témoins (matplotlib, plotly), planches de simulation des trois dyschromatopsies, appli Streamlit thémée. Toutes les couleurs viennent de `dist/` ou des jetons.

## Régénérer

```
uv run --group specimens python -I specimens/graphiques/rendre.py [--sans-plotly] [--sans-streamlit]
uv run --no-project python -I skills/charte/outils/daltonisme.py [--markdown] [--seuil 4.0]
```

Prérequis du rendu : Chrome (kaleido 1.x, via `BROWSER_PATH`) et Edge ou Chrome (capture Streamlit par DevTools).

29 PNG, 1,65 Mo (originaux et planches en 256 couleurs, sans tramage).

## Fichiers

- `rendre.py` : rendu complet ; `placement.py` : placement des étiquettes directes sans chevauchement (fonction pure) ; `streamlit_demo.py` : appli témoin (deux boutons en contour, graphique en barres, champ, case, message).
- `rendus/mpl-{barres,lignes,nuage,chaleur}-{sombre,clair}.png` et `rendus/plotly-{barres,lignes,nuage}-{sombre,clair}.png`.
- `rendus/*-simulation.png` : planche 2 × 2 (normale, protanopie, deutéranopie, tritanopie), Machado 2009 pixel par pixel.
- `rendus/streamlit-sombre.png` : capture de l'appli avec `dist/streamlit-sombre.toml`, copié en `.streamlit/config.toml` temporaire.
- `skills/charte/outils/daltonisme.py` et `tests/test_daltonisme.py`, `tests/test_graphiques.py`.

## Règles appliquées (v2.1)

- **Motifs (A2, A7)** : le cycle des `mplstyle` combine couleur, tiret et marqueur ; plotly reçoit `line.dash`, `marker.symbol` et `marker.pattern.shape` trace par trace depuis `MOTIFS` (`dist/charte.py`) ; barres hachurées.
- **Étiquettes directes (A2)** : lignes à 8 séries étiquetées en bout de courbe, écart vertical minimal d'une hauteur de ligne (1,25 × 11 pt en matplotlib, 17 px en plotly), calculé par `placement.placer` ; barres (dès deux séries en clair) et nuages étiquetés. Plus aucun chevauchement dans `mpl-lignes-*` ni `plotly-lignes-*`.
- **Légende entière (A10)** : `savefig.bbox: tight` dans les `mplstyle`.
- **Palettes (A6)** : carte de chaleur en `seq-1` à `seq-5` et en `div-1` à `div-5`, palettes discrètes, valeur écrite dans chaque cellule (encre `texte` claire ou sombre, la plus contrastée).
- **Streamlit (B4)** : aucun `type="primary"` ; boutons en contour (`borderColor` = `trait-fort`) ; la case cochée montre `primaryColor`, resté `primaire`.

## Distinction des séries (ΔE00, Machado 2009)

Seuil de la CLI : 4,0 sur les séries 1 à 4 (`--seuil`), code de sortie 1 en dessous. Charte v2.1 (après A1, `cat-4` et `cat-5` permutées) : code 0.

| Thème | Vision | Pire paire 1 à 4 | Pire paire 1 à 8 |
|---|---|---|---|
| sombre | normale | cat-2/cat-3 25,7 | cat-1/cat-7 12,1 |
| sombre | protanopie | cat-1/cat-4 12,4 | cat-6/cat-7 4,1 |
| sombre | deutéranopie | cat-3/cat-4 13,7 | cat-6/cat-7 4,5 |
| sombre | tritanopie | cat-1/cat-3 8,2 | cat-4/cat-5 4,6 |
| clair | normale | cat-1/cat-4 33,7 | cat-5/cat-8 14,7 |
| clair | protanopie | cat-2/cat-3 12,9 | cat-5/cat-8 4,1 |
| clair | deutéranopie | cat-3/cat-4 9,9 | cat-4/cat-7 4,0 |
| clair | tritanopie | cat-1/cat-3 12,7 | cat-3/cat-6 4,0 |

Les séries 5 à 8 restent proches en dyschromatopsie (4,0 à 4,6) : c'est pourquoi la charte impose motif et étiquette directe au-delà de quatre séries.

## Constats pour la critique

- **Couleurs Streamlit hors jetons** : `st.success` (texte `#5CE488` sur `#183A29`) et le code en ligne gardent les couleurs propres de Streamlit ; le thème 1.66 n'a pas de clé pour elles. Les champs n'ont pas de contour visible (option `showWidgetBorder` non posée).
- **Polices** : matplotlib charge Atkinson et Sora par `addfont` (avertissement `findfont` pour `Roboto`, absente) ; plotly et Streamlit rendent en repli (Segoe UI), faute de polices installées.
- **Streamlit** : l'en-tête (`Deploy`, menu) n'est pas thémé ; `st.bar_chart` ne prend ni hachures ni étiquettes directes.
- **Étiquettes de nuage** : placées au-dessus de chaque groupe, elles peuvent toucher un point d'un autre groupe quand les nuages se recouvrent.
