# charte-generique

*A generic, dark-first design system: DTCG design tokens, ready-to-use theme files and accessibility checks, packaged as a Claude Code plugin.*

Charte graphique générique, sombre d'abord, pour des applications web, des rapports, des présentations et des dépôts de code.

- **Jetons** : [`skills/charte/jetons/charte.tokens.json`](skills/charte/jetons/charte.tokens.json), au format DTCG 2025.10, source unique de toutes les valeurs.
- **Charte lisible** : [`docs/CHARTE.md`](docs/CHARTE.md), v2.1 (rôles, palettes séquentielle et divergente, règles d'usage et par support, typographie et polices incorporées dans Office, formes, pictogramme).
- **Fichiers prêts à l'emploi** : [`skills/charte/dist/`](skills/charte/dist/) (CSS, Python, matplotlib, plotly, Streamlit, mermaid, Office, SVG), généré par `uv run --no-project python -I skills/charte/generer.py` (`--verifier` en CI).
- **Contrôles** : contrastes WCAG 2.1 (pictogramme et étiquette de badge compris), écart entre les pas des palettes et distinction des séries de graphique, en vision normale et en dyschromatopsie.

  ```sh
  uv run --no-project python -I skills/charte/outils/contrastes.py
  uv run --no-project python -I skills/charte/outils/daltonisme.py
  ```

  Pour vérifier en plus que la charte reste loin d'une liste locale de couleurs (au format `{"nom": "#RRGGBB"}`), passer `--eviter chemin.json`.

## Développement

```sh
uv run --group dev ruff check .
uv run --group dev pytest
```

Les outils de `skills/charte/` n'utilisent que la bibliothèque standard de Python (3.11 ou plus récent).

## Licences

- **Code et jetons** : MIT.
- **Polices recommandées** : Sora, Atkinson Hyperlegible et JetBrains Mono, sous SIL Open Font License 1.1.
