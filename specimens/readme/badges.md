# Badges

Badges shields.io aux couleurs des statuts (thème clair). shields.io choisit lui-même le texte blanc ou sombre selon la luminosité du fond ; le contraste est mesuré par `couleurs.contraste`.

| Statut | Badge | Jeton | Couleur | Texte | Contraste |
|---|---|---|---|---|---|
| succès | ![succès](https://img.shields.io/badge/succ%C3%A8s-succes-1B7043?labelColor=646E7B) | `succes` | `#1B7043` | `#FFFFFF` | 6.10 |
| alerte | ![alerte](https://img.shields.io/badge/alerte-alerte--texte-9A4A00?labelColor=646E7B) | `alerte-texte` | `#9A4A00` | `#FFFFFF` | 6.26 |
| erreur | ![erreur](https://img.shields.io/badge/erreur-erreur-B3261E?labelColor=646E7B) | `erreur` | `#B3261E` | `#FFFFFF` | 6.54 |
| info | ![info](https://img.shields.io/badge/info-primaire-1D5BC2?labelColor=646E7B) | `primaire` | `#1D5BC2` | `#FFFFFF` | 6.31 |
| neutre | ![neutre](https://img.shields.io/badge/neutre-texte--attenue-4F5A68?labelColor=646E7B) | `texte-attenue` | `#4F5A68` | `#FFFFFF` | 7.01 |

Étiquette (`labelColor`) : jeton `badge-etiquette` `#646E7B` (même valeur dans les deux thèmes), texte blanc, contraste 5.17 ; elle se détache de la page sombre comme de la claire.

- alerte : le jeton `alerte` ne passe pas 4,5:1 avec le texte de shields.io ; variante retenue `alerte-texte`.
- neutre : le jeton `neutre` ne passe pas 4,5:1 avec le texte de shields.io ; variante retenue `texte-attenue`.
