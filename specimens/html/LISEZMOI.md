# Spécimen HTML

Page autonome qui met la charte à l'épreuve : typographie, boutons, champs, pastilles, bandeaux, carte, tableau, modale, graphiques SVG et nuancier. Toutes les valeurs viennent de `skills/charte/dist/charte.css`.

## Régénérer les rendus

```sh
uv run --group specimens python specimens/html/rendre.py
```

Edge headless (Windows) ; la page prend `?theme=clair|sombre`, `&gris=1` (filtre `grayscale(1)`) et `&nofocus=1`.

Sans `nofocus`, le bouton « Focus visible » est focalisé au chargement : les PNG sombre et clair montrent donc l'anneau de focus, à dessein. Les PDF et le PNG gris sont rendus avec `nofocus=1`, sans anneau.

## Fichiers

- `specimen.html` : la page ;
- `composants.css` : composants, sur les seules variables, et feuille `@media print` ;
- `rendre.py` : script de rendu ;
- `rendus/specimen-sombre.png`, `specimen-clair.png` : pleine page, 1200 px ;
- `rendus/specimen-clair.pdf` : A4 clair ;
- `rendus/specimen-gris.pdf` et `specimen-gris-page1.png` : variante en niveaux de gris.

## Règles appliquées (v2.1)

- **Filet or (B5)** : la page s'ouvre sur un titre suivi du filet `accent` (96 × 4 px).
- **Contours interactifs (A5)** : bouton secondaire, champs, sélecteur de thème et modale en `trait-fort` (3,06 à 3,76:1) ; cartes et tableau gardent `trait`.
- **Pictogramme (A4)** : `--picto-tuile`, `--picto-barres`, `--picto-point` de `charte.css`, choisis par mesure dans chaque thème.
- **Aplat d'or (B2)** : bloc chiffre clé en `accent-aplat`, texte `texte-sur-vif`.
- **Impression et gris (A7)** : fonds pleins en contour (pastilles, bandeaux, aplat d'or, bouton principal), intitulés en gras, un tiret par série dans le graphique à huit lignes (même cycle que matplotlib).
- **Nuancier** : nouveaux jetons `trait-fort`, `accent-aplat`, `badge-etiquette`, `seq-1` à `seq-5`, `div-1` à `div-5`.
- Poids : PNG en 256 couleurs ; dossier `rendus/` à 1,9 Mo.

## Constats pour la critique

- Les pastilles de statut portent icône et libellé : le sens ne passe pas par la couleur seule.
- Les bandeaux `*-doux` restent peu distincts en niveaux de gris : l'intitulé en gras porte le sens, comme la règle A7 l'exige.
- Le PDF en gris est rasterisé par le filtre `grayscale(1)` (~1,4 Mo contre ~0,25 Mo pour le PDF clair).
- Polices : `@font-face` sur les `woff2` locales, rendu avec les vraies polices.
- Le thème sombre en pleine page est long (~4400 px) : le nuancier, enrichi des palettes, occupe le tiers inférieur.
- Impression : les sauts de section laissent encore des pages remplies aux deux tiers (m8 de la critique, hors liste A).
