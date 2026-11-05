# charte-generique

Charte graphique générique, en plugin Claude Code. Sa source unique est `skills/charte/jetons/charte.tokens.json`, au format DTCG 2025.10. On la lit toujours par `skills/charte/outils/jetons.py` (`charger()`), jamais en relisant le JSON à la main.

- **Lint** : `uv run --group dev ruff check .`
- **Tests** : `uv run --group dev pytest` (ciblés : `uv run --group dev pytest tests/test_x.py`)
- **Contrôle de la charte** : `uv run --no-project python -I skills/charte/outils/contrastes.py` doit afficher `Échecs : 0`.
- **Génération** : `uv run --no-project python -I skills/charte/generer.py` régénère `skills/charte/dist/` (commité) ; `--verifier` rend 1 si `dist/` est périmé. À relancer après toute modification des jetons.
- **Dépendances** :
  - `skills/charte/` : bibliothèque standard seulement, car le plugin tourne sans installation ;
  - spécimens : groupe `specimens` du `pyproject.toml`.
- **Charte** :
  - toute valeur de couleur vient des jetons ; pas de couleur en dur ailleurs, sauf dans les fichiers générés de `dist/` ;
  - `docs/CHARTE.md` est comparé aux jetons par `tests/test_doc.py`.
- **Interdits** : aucun nom ni aucune couleur d'une ancienne marque. La liste des couleurs à éviter reste locale (`~/.claude/charte/eviter.json`) et n'est jamais versionnée.
- **Commandes** : `uv run`, jamais `python` nu.
