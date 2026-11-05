# Spécimen README et aperçu social

## Régénérer

```
uv run --no-project python -I specimens/readme/generer_bannieres.py
uv run --no-project python -I specimens/readme/rendre.py
```

Le premier écrit les SVG (valeurs lues par `jetons.charger()`, Sora en base64). Le second écrit `badges.md`, `README-temoin.md`, puis les PNG par Edge headless (Windows) ; il tente `npx -y @mermaid-js/mermaid-cli` pour `rendus/mermaid.png`.

## Fichiers

- `banniere-sombre.svg`, `banniere-clair.svg` (1280×320, environ 21 Ko chacune) ;
- `apercu-social.svg` (source) et `apercu-social.png` (1280×640, sombre, marge de 120 px autour du bloc) ;
- `badges.md`, `README-temoin.md` ;
- `rendus/` : `banniere-*.png`, `readme-sombre.png`, `readme-clair.png`.

## Constats pour la critique

- Mermaid : `rendus/mermaid.png` absent. `npx -y @mermaid-js/mermaid-cli` a échoué (erreur de sortie non nulle après ~60 s, probablement le téléchargement de Chromium par puppeteer). Le rendu README montre donc le code du diagramme. GitHub ignore en partie `%%{init}%%` et les `themeVariables` : le thème sombre n'est pas garanti.
- Badges : shields.io impose texte blanc ou `#333333`. Jetons clairs retenus. `alerte` (#E8892A) échoue avec le blanc et le gris sombre ; remplacé par `alerte-texte` (#9A4A00). `neutre` échoue ; remplacé par `texte-attenue` (#4F5A68). Les badges ont un fond sombre fixe d'étiquette, quel que soit le thème de la page.
- Badges : le rendu local imite shields.io en HTML (Verdana) ; les vrais badges demandent le réseau.
- La bannière sombre sur GitHub clair (ou inversement) est évitée par `<picture>`, mais l'`<img>` de repli est la sombre.
- Le sous-titre est composé en Sora 600 (seule police embarquée), un peu lourd pour un texte secondaire ; Atkinson alourdirait la bannière de ~15 Ko.
- Aperçu social : bloc centré à gauche avec beaucoup de vide à droite ; peu d'information.
- Le rendu du README est un HTML de style GitHub simplifié, non le rendu réel de GitHub ; la section Captures n'y figure pas (elle référence ces captures).
