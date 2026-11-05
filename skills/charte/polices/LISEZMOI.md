# Polices de la charte

Sous-ensemble latin (français compris), téléchargé depuis Fontsource 5.2.6 le 2026-11-05. Chaque police est sous SIL Open Font License 1.1 : voir le fichier `OFL-*.txt` correspondant.

| Fichier | Police | Graisse | Rôle |
|---|---|---|---|
| `sora-latin-600-normal.*` | Sora | 600 | titres |
| `atkinson-hyperlegible-latin-400-normal.*` | Atkinson Hyperlegible | 400 | texte |
| `atkinson-hyperlegible-latin-700-normal.*` | Atkinson Hyperlegible | 700 | texte en gras |
| `jetbrains-mono-latin-400-normal.*` | JetBrains Mono | 400 | code |

- **Pages web** : `woff2`, déclarés par `@font-face` et servis par le projet lui-même, sans CDN.
- **Graphiques et documents générés** (matplotlib, PDF) : `ttf`, chargés par chemin. On ne les installe pas sur le poste.
