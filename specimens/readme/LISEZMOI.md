# Spécimen README et aperçu social

## Régénérer

```
uv run --no-project python -I specimens/readme/generer_bannieres.py
uv run --no-project python -I specimens/readme/rendre.py
```

Le premier écrit les SVG (valeurs lues par `jetons.charger()`, Sora en base64). Le second écrit `badges.md`, `README-temoin.md`, puis les PNG par Edge headless (Windows) ; il lance `npx -y @mermaid-js/mermaid-cli` pour `rendus/mermaid-sombre.png` et `mermaid-clair.png`, avec Edge comme navigateur de puppeteer (option `-p`), car le `chrome-headless-shell` de puppeteer n'est pas téléchargé.

## Fichiers

- `banniere-sombre.svg`, `banniere-clair.svg` (1280×320, environ 21 Ko chacune) ;
- `apercu-social.svg` (source) et `apercu-social.png` (1280×640, sombre, bloc centré dans les marges de 80 px) ;
- `badges.md`, `README-temoin.md` ;
- `rendus/` : `banniere-*.png`, `mermaid-sombre.png`, `mermaid-clair.png`, `readme-sombre.png`, `readme-clair.png`.

Licence : les SVG embarquent Sora 600 (sous-ensemble latin, base64), sous SIL Open Font License 1.1 ; texte de la licence dans `skills/charte/polices/OFL-sora.txt` (voir `skills/charte/polices/LISEZMOI.md`). Un dépôt qui reprend ces bannières doit joindre ce fichier de licence.

## Règles appliquées (v2.1)

- **Mermaid (A8)** : le bloc de `README-temoin.md` prend le thème `neutral` (`%%{init: {"theme": "neutral"}}%%`) ; deux rendus de référence, `rendus/mermaid-sombre.png` et `rendus/mermaid-clair.png` (avec `dist/mermaid-<thème>.json`), sous `<picture>` avec `<img>` de repli clair. Le rendu local de chaque thème prend l'image de son thème : plus de bandeau sombre sur la page claire.
- **Bannière (A8)** : `<img>` de repli clair, le thème par défaut de GitHub.
- **Badges (A8)** : étiquette `labelColor` en `badge-etiquette` `#646E7B`, la même dans les deux thèmes (blanc 5,17:1 ; 3,60:1 sur le fond sombre, 4,86:1 sur le clair).
- **Aperçu social (A11)** : bloc centré (pictogramme, titre, filet, sous-titre) entre 144 et 486 px de haut, dans les marges de 80 px ; titre de 72 px, sous-titre de 32 px.
- **Pictogramme (A4)** : couleurs de `jetons.PICTOGRAMME` (point `accent-aplat` en clair, `accent-doux` en sombre) ; filet or (`accent`) sous le titre de chaque SVG (B5).

## Constats pour la critique

- Badges : shields.io impose texte blanc ou `#333333`. `alerte` (#E8892A) échoue avec les deux ; remplacé par `alerte-texte` (#9A4A00). `neutre` échoue ; remplacé par `texte-attenue` (#4F5A68).
- Badges : le rendu local imite shields.io en HTML (Verdana) ; les vrais badges demandent le réseau.
- Le sous-titre des bannières est composé en Sora 600 (seule police embarquée), un peu lourd pour un texte secondaire.
- Point du pictogramme en sombre (`accent-doux`) : or bruni, peu lisible comme « or » ; voir `specimens/office/LISEZMOI.md`.
- Le rendu du README est un HTML de style GitHub simplifié, non le rendu réel de GitHub ; à vérifier sur GitHub après fusion, en particulier le thème `neutral` du bloc mermaid.

## Revue

### Passe 1 (2026-11-05, SHA revu e0e6ae7)

- Important, medium, reviewer : `mermaid.png` absent ; cause réelle, puppeteer sans `chrome-headless-shell` et `-w` refusé par `npx`. Corrigé : Edge par `-p`, option `--size`.
- Nit, low, second avis 2 : lien mort vers `rendus/mermaid.png`. Corrigé : PNG produit, note conditionnelle, test des liens `rendus/`.
- Nit, low, second avis 4 : tests de structure faibles. Corrigé : JSON `%%{init}%%` comparé à `dist/mermaid-sombre.json`, deux `<source>`, contraste des badges.
- Nit, low, second avis 6 : `succès` non ASCII dans l'URL. Corrigé : `urllib.parse.quote`.
- Nit, low, second avis 3 : licence OFL de Sora embarquée. Corrigé : mention dans « Fichiers ».
- Nit, low, reviewer : badge sans variante lisible gardé en silence. Corrigé : `ValueError`.
- Nit, low, second avis 1 : `#333333` dans `rendre.py`. Rejeté : couleur imposée par shields.io, sert au calcul de contraste, jamais rendue (commentaire précisé).
- Nit, low, second avis 5 : aperçu social non centré. Reporté à la critique (1.6), déjà dans les constats.
- Complexité : 0 constat.
