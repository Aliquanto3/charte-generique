# Spécimen README et aperçu social

## Régénérer

```
uv run --no-project python -I specimens/readme/generer_bannieres.py
uv run --no-project python -I specimens/readme/rendre.py
```

Le premier écrit les SVG (valeurs lues par `jetons.charger()`, Sora en base64). Le second écrit `badges.md`, `README-temoin.md`, puis les PNG par Edge headless (Windows) ; il lance `npx -y @mermaid-js/mermaid-cli` pour `rendus/mermaid.png`, avec Edge comme navigateur de puppeteer (option `-p`), car le `chrome-headless-shell` de puppeteer n'est pas téléchargé.

## Fichiers

- `banniere-sombre.svg`, `banniere-clair.svg` (1280×320, environ 21 Ko chacune) ;
- `apercu-social.svg` (source) et `apercu-social.png` (1280×640, sombre, marge de 120 px autour du bloc) ;
- `badges.md`, `README-temoin.md` ;
- `rendus/` : `banniere-*.png`, `mermaid.png`, `readme-sombre.png`, `readme-clair.png`.

Licence : les SVG embarquent Sora 600 (sous-ensemble latin, base64), sous SIL Open Font License 1.1 ; texte de la licence dans `skills/charte/polices/OFL-sora.txt` (voir `skills/charte/polices/LISEZMOI.md`). Un dépôt qui reprend ces bannières doit joindre ce fichier de licence.

## Constats pour la critique

- Mermaid : `rendus/mermaid.png` rendu avec `dist/mermaid-sombre.json` ; il garde son fond sombre dans le rendu clair du README (bandeau sombre sur page claire). GitHub ignore en partie `%%{init}%%` et les `themeVariables` : le thème sombre n'est pas garanti.
- Badges : shields.io impose texte blanc ou `#333333`. Jetons clairs retenus. `alerte` (#E8892A) échoue avec le blanc et le gris sombre ; remplacé par `alerte-texte` (#9A4A00). `neutre` échoue ; remplacé par `texte-attenue` (#4F5A68). Les badges ont un fond sombre fixe d'étiquette, quel que soit le thème de la page.
- Badges : le rendu local imite shields.io en HTML (Verdana) ; les vrais badges demandent le réseau.
- La bannière sombre sur GitHub clair (ou inversement) est évitée par `<picture>`, mais l'`<img>` de repli est la sombre.
- Le sous-titre est composé en Sora 600 (seule police embarquée), un peu lourd pour un texte secondaire ; Atkinson alourdirait la bannière de ~15 Ko.
- Aperçu social : bloc centré à gauche avec beaucoup de vide à droite ; peu d'information.
- Le rendu du README est un HTML de style GitHub simplifié, non le rendu réel de GitHub ; la section Captures n'y figure pas (elle référence ces captures).

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
