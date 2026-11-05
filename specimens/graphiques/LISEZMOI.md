# Spécimen : graphiques et daltonisme

Graphiques témoins (matplotlib, plotly), planches de simulation des trois dyschromatopsies, appli Streamlit thémée. Toutes les couleurs viennent de `dist/` ou des jetons.

## Régénérer

```
uv run --group specimens python -I specimens/graphiques/rendre.py [--sans-plotly] [--sans-streamlit]
uv run --no-project python -I skills/charte/outils/daltonisme.py [--markdown] [--seuil 4.0]
```

Prérequis du rendu : Chrome (kaleido 1.x, via `BROWSER_PATH`) et Edge ou Chrome (capture Streamlit par DevTools). Le script de capture utilise `websockets`, présent via Streamlit mais non déclaré dans `pyproject.toml`. 29 PNG, 1,45 Mo.

## Fichiers

- `rendre.py` : rendu complet ; `streamlit_demo.py` : appli témoin (bouton principal, bouton secondaire, graphique en barres, champ, message).
- `rendus/mpl-{barres,lignes,nuage,chaleur}-{sombre,clair}.png` et `rendus/plotly-{barres,lignes,nuage}-{sombre,clair}.png`.
- `rendus/*-simulation.png` : planche 2 × 2 (normale, protanopie, deutéranopie, tritanopie), Machado 2009 pixel par pixel.
- `rendus/streamlit-sombre.png` : capture de l'appli avec `dist/streamlit-sombre.toml`, copié en `.streamlit/config.toml` temporaire (serveur prêt en ~1 s).
- `skills/charte/outils/daltonisme.py` et `tests/test_daltonisme.py`, `tests/test_graphiques.py`.

## Distinction des séries (ΔE00, Machado 2009)

Seuil de la CLI : 4,0 sur les séries 1 à 4 (`--seuil`), code de sortie 1 en dessous ; les séries 5 à 8 sont rapportées sans faire échouer. Charte actuelle : code 0.

| Thème | Vision | Pire paire 1 à 4 | Pire paire 1 à 8 |
|---|---|---|---|
| sombre | normale | cat-2/cat-4 21,7 | cat-1/cat-7 12,1 |
| sombre | protanopie | cat-3/cat-4 7,6 | cat-6/cat-7 4,1 |
| sombre | deutéranopie | cat-2/cat-4 5,9 | cat-6/cat-7 4,5 |
| sombre | tritanopie | cat-1/cat-3 8,2 | cat-4/cat-5 4,6 |
| clair | normale | cat-2/cat-4 23,9 | cat-4/cat-8 14,7 |
| clair | protanopie | cat-2/cat-4 10,7 | cat-4/cat-8 4,1 |
| clair | deutéranopie | cat-2/cat-4 4,4 | cat-5/cat-7 4,0 |
| clair | tritanopie | cat-2/cat-4 12,7 | cat-3/cat-6 4,0 |

## Pistes de correction (non appliquées)

Thème clair, série 1 à 4 en deutéranopie : `cat-2` `#A87A00` et `cat-4` `#C24D1B` ne sont distinctes qu'à ΔE00 4,4. Candidats mesurés (contraste avec `surface` `#FFFFFF`, minimum ΔE00 des séries 1 à 4 en vision normale / protanopie / deutéranopie / tritanopie ; séries 1 à 8 inchangées en protanopie, deutéranopie et tritanopie : 4,1 / 4,0 / 4,0) :

| Candidat | Contraste sur `surface` | Min. 1 à 4 (N / P / D / T) | Remarque |
|---|---|---|---|
| `cat-2` = `#B58900` (garde la teinte jaune-ocre) | 3,21:1 | 27,8 / 12,0 / 9,1 / 12,7 | recommandé : ne dégrade rien en 1 à 8 |
| `cat-2` = `#E87430` (orange) | 3,01:1 (limite) | 13,4 / 12,0 / 12,2 / 12,7 | proche de `cat-4` en vision normale |
| `cat-4` = `#B42424` (rouge) | 6,52:1 | 35,1 / 12,9 / 12,9 / 12,7 | à écarter : ΔE00 1,8 avec `erreur` `#B3261E` ; deutéranopie 1 à 8 tombe à 2,5 |

Thème sombre : séries 1 à 4 au minimum 5,9 ; la faiblesse est dans les séries 5 à 8 (cat-6/cat-7 4,1 en protanopie). Aucune correction proposée avant d'avoir décidé si les séries 5 à 8 doivent être distinguables seules par la couleur (en pratique : légende directe, motifs, marqueurs).

## Constats pour la critique

- **Bouton principal Streamlit (mesure sur `streamlit-sombre.png`, zone du bouton)** : fond `#8DB0F7` (= `primaire`), libellé `#FFFFFF` imposé par Streamlit 1.66, contraste mesuré **2,17:1**, sous 4,5:1 (texte de 14 px, non gras). Le fond du bouton sur `fond` fait 8,60:1. Aucune clé de thème ne change le libellé. Options pour la décision d'Anaël (aucune appliquée) :
  1. Un bleu soutenu propre à Streamlit comme `primaryColor`, libellé blanc : `#3B6FD0` donne 4,80:1 avec le blanc et 3,88:1 sur `fond` ; `#3366CC` donne 5,37:1 et 3,47:1 sur `fond` (3,22:1 sur `surface`). Exception à documenter : ce bleu n'est pas dans les jetons, et `primaryColor` sert aussi aux focus, curseurs et cases à cocher. Le `primaire` clair `#1D5BC2` ne convient pas (6,31:1 avec le blanc, mais 2,95:1 sur `fond` sombre).
  2. Ne pas utiliser `type="primary"` : le bouton secondaire (texte `texte` sur fond `surface`) reste lisible et cohérent avec la règle « le bleu n'est jamais un aplat de bouton ».
  3. Garder `#8DB0F7` et accepter 2,17:1 en le documentant comme limite connue (statu quo, non conforme WCAG 1.4.3).
- **Pas de palette séquentielle** dans les jetons ni dans `dist/` : la carte de chaleur utilise un dégradé `surface-alt` vers `primaire` fabriqué dans `rendre.py`. Manque à combler (séquentielle, divergente).
- **Lignes à 8 séries** : les étiquettes directes de fin de courbe se chevauchent (vérifié en clair : séries 4, 5 et 6, 7 ; mêmes données en sombre) ; la légende directe ne suffit pas sans anti-chevauchement.
- **Thème clair, 8 séries** : en simulation, `cat-4`/`cat-8` (protanopie 4,1) sont proches (bruns) ; `cat-1` devient vert-bleu en tritanopie.
- **Polices** : Atkinson, Sora et JetBrains Mono ne sont pas installées sur le poste. Matplotlib les charge par `addfont` ; le `mplstyle` cite aussi `Segoe UI` et `Roboto` en repli, d'où des avertissements `findfont` pour `Roboto` (absente). Plotly et Streamlit rendent en repli (`system-ui`/Segoe UI) : les captures ne montrent donc pas Atkinson ni Sora.
- **Streamlit** : l'en-tête (`Deploy`, menu) n'est pas thémé par la charte ; la capture est prise en 1100 × 900. `st.bar_chart` utilise `chartCategoricalColors` et empile les barres.
