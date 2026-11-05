# Spécimen HTML

Page autonome qui met la charte à l'épreuve : typographie, boutons, champs, pastilles, bandeaux, carte, tableau, modale, graphiques SVG et nuancier. Toutes les valeurs viennent de `skills/charte/dist/charte.css`.

## Régénérer les rendus

```sh
uv run --group specimens python specimens/html/rendre.py
```

Edge headless (Windows) ; la page prend `?theme=clair|sombre`, `&gris=1` (filtre `grayscale(1)`) et `&nofocus=1`.

## Fichiers

- `specimen.html` : la page ;
- `composants.css` : composants, sur les seules variables, et feuille `@media print` ;
- `rendre.py` : script de rendu ;
- `rendus/specimen-sombre.png`, `specimen-clair.png` : pleine page, 1200 px ;
- `rendus/specimen-clair.pdf` : A4 clair ;
- `rendus/specimen-gris.pdf` et `specimen-gris-page1.png` : variante en niveaux de gris.

## Constats pour la critique

- Les pastilles de statut portent icône et libellé : le sens ne passe pas par la couleur seule.
- Dans le graphique à huit lignes, les séries 5 à 8 restent proches en gris ; seule la légende directe les distingue (pas de motif).
- Les bandeaux `*-doux` se distinguent peu les uns des autres en niveaux de gris : seul le texte en gras (« Succès. », « Alerte. »…) porte le sens.
- Impression : les fonds pleins sont retirés (pastilles et bandeaux passent en contour, bouton principal en contour épais) ; le PDF en gris est rasterisé par le filtre (~1 Mo contre ~0,15 Mo).
- Polices : `@font-face` sur les `woff2` locales, rendu avec les vraies polices.
- Le thème sombre en pleine page est long (~3500 px) : le nuancier occupe le tiers inférieur.
