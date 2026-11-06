---
name: charte
description: Applique, audite et migre la charte graphique générique d'un dépôt (couleurs, polices, thèmes clair et sombre). À invoquer avec « appliquer la charte », « mettre ce dépôt à la charte », « audit de charte », « couleurs hors charte », « migrer vers la charte v2 », « nouveau projet à la charte ».
---

Tu mets un dépôt à la charte générique, ou tu vérifies qu'il la respecte. Trois modes : `init`, `audit`, `migrer`. Choisis-le d'après la demande ; demande-le si elle ne le dit pas. Les outils sont en bibliothèque standard.

Règles de la charte (le détail et les valeurs sont dans `${CLAUDE_PLUGIN_ROOT}/docs/CHARTE.md`, ne les recopie pas) :
- sombre d'abord, deux thèmes (clair et sombre) ;
- toute couleur vient d'un jeton ; aucune couleur en dur dans le code du dépôt cible ;
- les polices sont celles de la charte (titres, texte, code), servies par le dépôt, sans CDN.

## Mode `init` : dépôt neuf ou sans charte

1. Demande les supports : `web`, `streamlit`, `python` (graphiques), `office`, `readme`. Un ou plusieurs.
2. Pose les fichiers (rien n'est écrasé sans `--forcer`) :

   ```
   uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/installer.py" --cible <dépôt> --supports web,readme [--dossier static/charte] [--seulement polices,favicon,pictogramme]
   ```

   `--seulement` ne pose que ces groupes (par exemple les polices manquantes d'un dépôt migré).

3. Ajoute au `CLAUDE.md` du dépôt cible l'extrait que le script affiche (une ligne qui pointe vers la charte). S'il existe un `DESIGN.md`, ajoute la même ligne.
4. Branche les fichiers posés dans le projet (lien du CSS, thème Streamlit, style matplotlib), puis lance `audit`.

## Mode `audit` : constats sans rien modifier

```
uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/audit.py" <dépôt> [--ignorer GLOB] [--markdown | --json] [--strict]
```

Ignorés par défaut : `dist/`, `node_modules/`, `.venv/`, `.claude/`, `_bmad-output/`, `archive/` et `archives/` à la racine du dépôt seulement (motif `/archive/`), `*.min.*`. Les motifs de `--ignorer` se mettent entre guillemets (`--ignorer "docs/*"`) ; sous Git Bash, `set -f` coupe l'expansion des motifs par le shell.

Au-delà des couleurs et des polices, vérifie aussi le reste de la charte : logotype, favicon (l'audit signale son absence), filet or, pictogramme (sur fond sombre, version du thème sombre), et liens soulignés (l'audit signale un `text-decoration: none` sans soulignement de remplacement). Ces avertissements sont des `revoir`.

Classes : `charte` (égale à un jeton), `proche` (ΔE00 < 3, jeton donné), `v1` (valeur de l'ancienne charte, rôle cible donné), `hors-charte` (jeton le plus proche donné). Polices : `v1` (ancienne police de titres) ou `hors-charte`.

Présente les constats par gravité : `hors-charte`, puis `v1`, puis `proche`. Propose les corrections (jeton à utiliser, variable à créer), et n'en applique aucune sans l'accord de l'utilisateur.

## Mode `migrer` : vers la charte v2

```
uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/migrer.py" <dépôt> [--proposer] [--plan plan.md] [--correspondances corr.json] [--appliquer] [--ajouter-sombre] [--clair-d-abord]
```

Déroulé en quatre temps :

1. **Constater.** Lance `audit` (ci-dessus) pour mesurer l'écart.
2. **Proposer et relire.** Lance `migrer --proposer --plan <hors-du-dépôt>/plan.md` (sans `--appliquer` : le plan seul n'écrit rien dans le dépôt). Écris le plan et `corr.json` hors du dépôt cible, pour ne pas les commiter. Relis le plan avec l'utilisateur, avertissements compris (fichier lu en cp1252, encodage illisible) :
   - `auto` : remplacement sûr (valeur v1 sans ambiguïté, ou nom de variable qui correspond exactement à un rôle) ;
   - `revoir` : à décider à la main (rôle qui change de sens, valeur partagée par deux rôles, proposition au jeton le plus proche).
3. **Décider puis appliquer.** Écris `corr.json`, une table `{"--nom-de-variable": "role-v2"}` (`null` supprime une variable ; si elle est encore utilisée, elle est signalée et conservée). Lance `migrer --proposer --correspondances corr.json --appliquer`. Ajoute `--ajouter-sombre` si le plan signale qu'il n'y a pas de thème sombre : le bloc est généré depuis les jetons, sombre d'abord (sombre dans `:root` et `[data-theme="dark"]`, clair sous `prefers-color-scheme: light` et `[data-theme="light"]`). `--clair-d-abord` garde l'ancienne structure (clair par défaut). Toute variable de couleur de `:root` reçoit sa contrepartie ; une variable utilisée en texte et en aplat est signalée « à éclater ».
4. **Vérifier.** Relance `audit --strict`, puis les tests du dépôt cible et le contrôle de la charte (`contrastes.py`) si le dépôt en est un.

Règles de migration :
- Les couleurs de marque sans rôle (un vert vif de logo, par exemple) se remplacent par le rôle le plus proche par usage (`accent`, `primaire`, `succes`), jamais par une couleur nouvelle.
- Relis à la main les cas `revoir` qui changent le sens : `primaire-fonce` (devient `primaire-vif`), `relief`, `relief-actif` et `point` (n'existent plus), et le bouton principal (en v2, un aplat neutre `bouton` / `sur-bouton`, plus un aplat `primaire` : cherche les règles CSS de bouton qui utilisent la variable primaire).
- Une valeur v1 partagée par deux rôles n'est remplacée que si le nom de la variable tranche ; sinon elle reste en `revoir`.
- Au-delà des couleurs : `@font-face` (famille, fichier `src`, graisse) et piles de polices des variables migrent aussi ; si le fichier de police manque, lance la commande `installer.py` qui pose les polices (voir `init`) du plan. Relis le logotype, le favicon, le filet or, le pictogramme (fond sombre) et les liens soulignés.
- Tous les aplats `primaire` (nav, puces, badges, bouton) sont listés en `revoir` : en v2, un aplat plat n'est plus `primaire`.
- Le plan se lit hors du dépôt : l'outil dit où il l'a écrit.
- La migration est idempotente : une deuxième passe ne change rien.

## Contrôles

- Charte elle-même : `uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/contrastes.py"` doit afficher `Échecs : 0`.
- Dépôt cible : ses propres tests, plus un `audit --strict` final.
