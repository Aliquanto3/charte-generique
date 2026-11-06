# Skill `charte`

Le skill met un dépôt à la charte (`init`), vérifie qu'il la respecte (`audit`) et le migre de la v1 vers la v2 (`migrer`). Les outils n'utilisent que la bibliothèque standard de Python (3.11 ou plus récent).

## Installation

Avec le plugin, depuis la place de marché `charte-generique` :

```sh
claude plugin marketplace add Aliquanto3/charte-generique
claude plugin install charte@charte-generique
```

Sans le plugin, `installer.py` copie les fichiers de la charte dans un dépôt (voir `init` plus bas).

Dans les commandes ci-dessous, `${CLAUDE_PLUGIN_ROOT}` est la racine du plugin. Sans plugin, c'est la racine de ce dépôt.

## Mode `init`

Dépôt neuf ou sans charte. Le skill demande les supports, puis lance :

```sh
uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/installer.py" --cible <dépôt> --supports web,readme [--dossier static/charte] [--forcer] [--seulement polices,favicon,pictogramme]
```

- `--supports` : liste séparée par des virgules parmi `web`, `streamlit`, `python`, `office`, `readme`.
- `--dossier` : dossier de destination dans le dépôt cible.
- `--forcer` : écrase les fichiers qui existent déjà. Sans lui, l'outil refuse d'écraser.
- `--seulement` : ne pose que certains groupes parmi ceux des supports demandés : `polices` (polices et licences), `favicon`, `pictogramme`, `css`, ou un nom de fichier exact. Utile pour ajouter les polices manquantes à un dépôt déjà migré : `--supports web --seulement polices`. Un groupe sans fichier correspondant est refusé.

Il copie les fichiers utiles de `dist/` et les polices, avec leurs licences OFL. Les licences se nomment `polices/OFL-<famille en minuscules, sans espace ni tiret>.txt` (`OFL-sora.txt`, `OFL-atkinsonhyperlegible.txt`, `OFL-jetbrainsmono.txt`) : même nom dans la charte et dans le dépôt cible. Il affiche les fichiers posés et l'extrait à ajouter au `CLAUDE.md` du dépôt cible.

## Mode `audit`

Il ne modifie rien.

```sh
uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/audit.py" <dépôt> [--ignorer GLOB] [--markdown | --json] [--strict]
```

- `--ignorer` : motif glob à ignorer, répétable. Par défaut : `dist/`, `node_modules/`, `.venv/`, `.claude/`, `_bmad-output/`, `archive/`, `archives/` et `*.min.*`. Entre guillemets : `--ignorer "docs/*"` (sinon le shell développe le motif ; sous Git Bash, `set -f` coupe cette expansion).
- Sortie : tableau texte, ou `--markdown`, ou `--json`. Un résumé chiffré par classe finit le rapport.
- `--strict` : code de sortie 1 s'il reste des couleurs ou des polices `hors-charte` ou `v1`. Sans lui, le code est 0.

### Classes

| Classe | Sens |
|---|---|
| `charte` | La couleur est celle d'un jeton v2, dans l'un des deux thèmes. |
| `proche` | ΔE00 inférieur à 3 d'un jeton. Le jeton est donné. |
| `v1` | Valeur de la charte v1. Le rôle v1 et le rôle v2 cible sont donnés. |
| `hors-charte` | Tout le reste. Le jeton le plus proche et son ΔE00 sont donnés. |

Des avertissements `revoir` s'ajoutent au rapport (sans effet sur `--strict`) : favicon ou pictogramme absent d'un dépôt qui a des pages HTML (avec la commande `installer.py` à lancer (voir `init`)), et lien dont le soulignement est retiré (`text-decoration: none`) sans soulignement de remplacement.

Les polices sont classées `v1` (l'ancienne police de titres) ou `hors-charte` (famille absente des piles de la charte).

## Mode `migrer`

```sh
uv run --no-project python -I "${CLAUDE_PLUGIN_ROOT}/skills/charte/outils/migrer.py" <dépôt> [--proposer] [--plan plan.md] [--correspondances corr.json] [--appliquer] [--ajouter-sombre] [--ignorer GLOB]
```

Sans `--appliquer`, rien n'est écrit dans le dépôt : l'outil produit un plan. Avec `--appliquer`, il écrit les remplacements et affiche le nombre de fichiers modifiés. Une deuxième passe ne change rien.

Options : `--plan` (fichier du plan, sinon sortie standard ; l'outil dit où il l'a écrit, et si c'est dans le dépôt), `--proposer`, `--correspondances`, `--appliquer`, `--ajouter-sombre`, `--clair-d-abord`, `--ignorer` (comme pour `audit`).

Écrire le plan et `corr.json` hors du dépôt cible, pour ne pas les commiter.

Déroulé conseillé :

1. `audit` pour mesurer l'écart.
2. `migrer --proposer --plan <hors-du-dépôt>/plan.md`, puis relire le plan.
3. Décider des cas `revoir` dans `corr.json`, puis relancer avec `--correspondances corr.json --appliquer`.
4. `audit --strict`, puis les tests du dépôt cible.

### Format du plan

Un tableau markdown, une ligne par remplacement :

| Fichier | Ligne | Ancien | Nouveau | Rôle | Statut | Note |
|---|---|---|---|---|---|---|

Il contient ensuite un résumé (« N remplacement(s) automatique(s), M à revoir à la main »), s'il y en a une section d'avertissements (fichier lu en cp1252, encodage illisible), et finit par une section « Thème sombre » (bloc proposé, ou absence de thème sombre détecté).

Deux statuts :

- `auto` : remplacement sûr, écrit par `--appliquer`. La valeur v1 est sans ambiguïté, ou le nom de la variable correspond au rôle.
- `revoir` : jamais appliqué, à décider à la main. Cas : rôle qui change de sens, valeur partagée par deux rôles v1 sans nom de variable qui tranche, proposition au jeton le plus proche.

Autres relevés du plan :

- `@font-face` d'une police v1 : la famille, le `src` (nom du fichier de la charte, même dossier) et la graisse (`font-weight`) suivent la charte ; si le fichier est absent du dépôt, le plan donne en `revoir` la commande `installer.py` qui pose les polices (voir `init`).
- Piles de polices des variables dont le nom contient `police` ou `font` : remplacées par la pile de la charte si elles citent une police v1, sinon `revoir` avec la pile proposée.
- Variable de couleur utilisée en texte (`color`) et en aplat (`background`) : `revoir` « variable à éclater », avec les usages.
- Tout aplat `primaire` (nav, puce, badge, bouton) est listé en `revoir`.

Les cas `revoir` qui changent le sens :

- `primaire-fonce` devient `primaire-vif` ;
- `relief`, `relief-actif` et `point` n'existent plus en v2 ;
- le bouton principal n'est plus un aplat `primaire` mais un aplat neutre `bouton` / `sur-bouton` : chercher les règles CSS de bouton qui utilisent la variable primaire.

### Fichier de correspondances (`--correspondances`)

Un objet JSON `{"--nom-de-variable": "role-v2"}`. Il est prioritaire sur le reste.

```json
{
  "--brand": "primaire",
  "--vieux-gris": null
}
```

- Une valeur de type chaîne est un rôle v2 de la charte. Le remplacement est `auto`.
- Une valeur `null` demande de supprimer la variable. Si elle n'est plus utilisée dans le dépôt, la ligne est supprimée (`auto`) dans les fichiers de style ; dans les autres fichiers, le plan émet `revoir` (« variable à supprimer à la main »). Si elle l'est encore, elle est conservée et signalée en `revoir`, avec le nombre d'usages.
- La clé s'écrit avec ou sans les tirets initiaux.

### `--proposer`

Pour les variables, clés ou constantes de couleur que la table v1 ne connaît pas :

1. d'après le nom, avec `migrations/synonymes.json` : le rôle proposé est `auto` ;
2. sinon, d'après le jeton le plus proche en ΔE00 : statut `revoir`, avec l'écart en note.

### `--ajouter-sombre`

Pour un dépôt qui n'a qu'un thème clair. Avec `--appliquer`, l'outil ajoute aux fichiers de style un bloc généré depuis les jetons, pour toutes les variables de couleur des blocs `:root` (migrées, ou déjà égales à un jeton clair ; une valeur partagée par plusieurs jetons clairs de contreparties sombres différentes est signalée `revoir`). Sans `--appliquer`, le plan montre le bloc proposé. Si le dépôt a déjà un thème sombre, rien n'est ajouté.

Par défaut le bloc suit la règle « sombre d'abord » : le sombre est dans `:root` (et forcé par `[data-theme="dark"]`), le clair sous `@media (prefers-color-scheme: light)` et `[data-theme="light"]`.

### `--clair-d-abord`

Avec `--ajouter-sombre`, garde l'ancienne structure : le clair reste dans `:root`, le sombre va sous `prefers-color-scheme: dark` et `[data-theme="dark"]`. À réserver aux dépôts dont les pages supposent un défaut clair.

## Dossier `migrations/`

`skills/charte/migrations/` contient :

- `v1-vers-v2.json` : la table de migration de la v1 vers la v2. Les valeurs v1 sont figées dans le fichier. Les valeurs v2 ne le sont jamais : elles sont lues dans les jetons à chaque passage.
- `synonymes.json` : noms de variables (français et anglais) rangés par rôle v2, pour `--proposer`.

Chaque entrée de `roles` dans `v1-vers-v2.json` porte les valeurs `clair` et `sombre`, le rôle v2 `cible` et un `statut` (`auto` ou `revoir`, avec une `note` dans ce cas). Les séries se suivent par rang (`cat-n` vers `cat-n`). Le fichier donne aussi `polices` (famille v1 et son usage) et `synonymes` (noms de variables v1 par rôle).

Pour ajouter une migration :

1. écrire le fichier `migrations/<de>-vers-<vers>.json` sur le modèle de `v1-vers-v2.json`, sans valeur v2 en dur ;
2. compléter `synonymes.json` si de nouveaux noms de variables sont à reconnaître ;
3. ajouter les tests dans `tests/test_migrer.py` (chaque rôle cible doit exister dans les jetons).

Attention : `audit.py` et `migrer.py` ne lisent aujourd'hui que le fichier nommé `v1-vers-v2.json`. Une autre migration demande donc aussi de choisir le fichier dans `audit.charger_v1`.
