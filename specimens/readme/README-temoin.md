<picture>
  <source media="(prefers-color-scheme: dark)" srcset="banniere-sombre.svg">
  <source media="(prefers-color-scheme: light)" srcset="banniere-clair.svg">
  <img alt="Projet témoin" src="banniere-sombre.svg">
</picture>

![succès](https://img.shields.io/badge/succès-succes-1B7043?labelColor=121821) ![alerte](https://img.shields.io/badge/alerte-alerte--texte-9A4A00?labelColor=121821) ![erreur](https://img.shields.io/badge/erreur-erreur-B3261E?labelColor=121821) ![info](https://img.shields.io/badge/info-primaire-1D5BC2?labelColor=121821) ![neutre](https://img.shields.io/badge/neutre-texte--attenue-4F5A68?labelColor=121821)

Dépôt témoin : un README type pour un projet qui applique la charte générique.

## Architecture

```mermaid
%%{init: {"theme": "base", "themeVariables": {"background": "#0F1318", "primaryColor": "#1E242C", "primaryTextColor": "#E8ECF2", "primaryBorderColor": "#8DB0F7", "lineColor": "#A3ADBA", "secondaryColor": "#161B22", "tertiaryColor": "#1A2742", "fontFamily": "'Atkinson Hyperlegible', system-ui, 'Segoe UI', Roboto, sans-serif", "noteBkgColor": "#3A3112", "noteTextColor": "#E8ECF2", "cScale0": "#8DB0F7", "cScale1": "#E3C26B", "cScale2": "#8CC7A0", "cScale3": "#F2A07B", "cScale4": "#E58FB8", "cScale5": "#6CCAD8", "cScale6": "#A9B4C6", "cScale7": "#9FAE4F"}}}%%
flowchart LR
    A[Jetons DTCG] --> B[generer.py]
    B --> C[dist/]
    C --> D[Spécimens]
    D --> E[Critique]
```

> Note : GitHub applique une partie seulement des thèmes mermaid (`themeVariables`) et ignore
> `%%{init}%%` dans certains contextes de rendu. `rendus/mermaid.png` montre l'intention.

## Fonctionnalités

| Fonction | Statut | Remarque |
|---|---|---|
| Jetons DTCG | stable | source unique |
| Génération de `dist/` | stable | `generer.py --verifier` en CI |
| Spécimens | en cours | web, Office, graphiques, README |
| Critique | à venir | entrée : constats des spécimens |

## Captures

| Sombre | Clair |
|---|---|
| ![Capture sombre](rendus/readme-sombre.png) | ![Capture claire](rendus/readme-clair.png) |
