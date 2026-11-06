<picture>
  <source media="(prefers-color-scheme: dark)" srcset="banniere-sombre.svg">
  <source media="(prefers-color-scheme: light)" srcset="banniere-clair.svg">
  <img alt="Projet témoin" src="banniere-clair.svg">
</picture>

![succès](https://img.shields.io/badge/succ%C3%A8s-succes-1B7043?labelColor=646E7B) ![alerte](https://img.shields.io/badge/alerte-alerte--texte-9A4A00?labelColor=646E7B) ![erreur](https://img.shields.io/badge/erreur-erreur-B3261E?labelColor=646E7B) ![info](https://img.shields.io/badge/info-primaire-1D5BC2?labelColor=646E7B) ![neutre](https://img.shields.io/badge/neutre-texte--attenue-4F5A68?labelColor=646E7B)

Dépôt témoin : un README type pour un projet qui applique la charte générique.

## Architecture

```mermaid
%%{init: {"theme": "neutral"}}%%
flowchart LR
    A[Jetons DTCG] --> B[generer.py]
    B --> C[dist/]
    C --> D[Spécimens]
    D --> E[Critique]
```

> Le bloc mermaid prend le thème `neutral` : sans fond propre, il reste lisible sur la page claire comme sur la
> sombre de GitHub.

Rendu de référence aux couleurs de la charte, clair par défaut :

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="rendus/mermaid-sombre.png">
  <source media="(prefers-color-scheme: light)" srcset="rendus/mermaid-clair.png">
  <img alt="Diagramme d'architecture" src="rendus/mermaid-clair.png">
</picture>

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
