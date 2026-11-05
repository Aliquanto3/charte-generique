# Charte générique v2.0

Charte graphique commune à des applications web, des rapports, des présentations et des dépôts de code.

- **Sombre d'abord** : le thème sombre est le thème par défaut, et un thème clair le complète.
- **Source unique des valeurs** : [`skills/charte/jetons/charte.tokens.json`](../skills/charte/jetons/charte.tokens.json), au format DTCG 2025.10. Ce document décrit les rôles et les règles. Les tables ci-dessous sont comparées aux jetons par `tests/test_doc.py`.
- **Contrôle** : la commande ci-dessous vérifie les contrastes WCAG 2.1, les pastilles de statut et la distinction des séries de graphique. Elle doit afficher `Échecs : 0`.

  ```sh
  uv run --no-project python -I skills/charte/outils/contrastes.py
  ```

## Principes

1. **Lisible avant tout.** Tout texte atteint 4,5:1 sur son fond, et toute marque non textuelle (bordure de bouton, anneau de focus, série de graphique) 3:1.
2. **Le sens ne passe jamais par la seule couleur.** Un statut porte toujours une icône ou un libellé, et une série de graphique une légende directe ou un motif au-delà de quatre séries.
3. **Calme.** Fonds neutres et froids, sans motif ; formes arrondies ; halo doux plutôt qu'ombre dure.
4. **Un seul geste fort par écran** : le bouton principal, neutre et très contrasté. Le bleu sert à naviguer et à sélectionner, l'or à signaler.
5. **Libre** : polices sous licence OFL, servies localement, sans CDN.

## Palette par rôle

Valeurs en sombre, puis en clair. Les noms de rôle sont ceux des jetons.

| Rôle | Sombre | Clair | Usage |
|---|---|---|---|
| `fond` | #0F1318 | #F6F8FB | fond de page |
| `surface` | #161B22 | #FFFFFF | carte, panneau, diapositive |
| `surface-alt` | #1E242C | #ECF0F5 | barre latérale, zone secondaire, ligne paire de tableau |
| `trait` | #333B46 | #CED5DF | séparateur, bordure, contour de bouton secondaire |
| `texte` | #E8ECF2 | #121821 | texte courant, titres |
| `texte-attenue` | #A3ADBA | #4F5A68 | texte secondaire, légende |
| `neutre` | #8792A0 | #6E7886 | indicateur neutre, état indisponible (non textuel) |
| `primaire` | #8DB0F7 | #1D5BC2 | lien, sélection, pictogramme, série 1 ; jamais un aplat de bouton |
| `primaire-vif` | #B3CBFA | #164A9E | lien survolé, titre fort |
| `primaire-doux` | #1A2742 | #E1EAFA | fond de sélection, pastille d'information |
| `sur-primaire` | #0A1733 | #FFFFFF | texte ou trait sur `primaire` |
| `bouton` | #E8ECF2 | #121821 | aplat du bouton principal |
| `bouton-survol` | #FFFFFF | #2A3442 | bouton principal survolé |
| `sur-bouton` | #0F1318 | #FFFFFF | libellé du bouton principal |
| `accent` | #E3C26B | #8F6300 | marque d'accent (or), non textuelle |
| `accent-texte` | #E3C26B | #8A5F00 | texte d'accent |
| `accent-doux` | #3A3112 | #FBF1D6 | bandeau d'accent |
| `succes` | #8CC7A0 | #1B7043 | succès, état valide (texte et pastille) |
| `succes-doux` | #15291D | #E2F1E8 | bandeau de succès |
| `alerte` | #F0A35E | #E8892A | aplat d'alerte, toujours avec `texte-sur-vif` |
| `alerte-texte` | #F0A35E | #9A4A00 | texte d'alerte |
| `alerte-doux` | #3A2614 | #FDEBDA | bandeau d'alerte |
| `erreur` | #EE8C84 | #B3261E | erreur, blocage (texte et pastille) |
| `erreur-doux` | #3B1C1A | #FCE4E1 | bandeau d'erreur |
| `focus` | #9EC0FF | #1F5FD1 | anneau de focus |
| `texte-sur-vif` | #141A1F | #141A1F | texte sur `alerte` seulement |
| `sur-statut` | #0F1318 | #FFFFFF | texte sur un aplat `erreur`, `succes` ou `accent` |
| `encre-pleine` | #1A2742 | #121821 | aplat foncé (terminal, bulle, bandeau de titre) |
| `sur-encre` | #FFFFFF | #FFFFFF | texte sur `encre-pleine` |
| `sur-encre-attenue` | #C3CEDD | #C3CEDD | texte secondaire sur `encre-pleine` |
| `voile` | rgba(5, 8, 12, 0.6) | rgba(18, 24, 33, 0.32) | voile de modale |
| `halo` | 0 8px 24px rgba(232, 236, 242, 0.07) | 0 8px 24px rgba(18, 24, 33, 0.08) | ombre portée douce (carte, menu, modale) |

### Séries de graphique

Marques non textuelles, au moins 3:1 sur `surface`.

| Série | Sombre | Clair | Teinte |
|---|---|---|---|
| `cat-1` | #8DB0F7 | #1D5BC2 | bleu |
| `cat-2` | #E3C26B | #A87A00 | or |
| `cat-3` | #8CC7A0 | #1F8155 | sauge |
| `cat-4` | #F2A07B | #C24D1B | corail |
| `cat-5` | #E58FB8 | #B83A75 | framboise |
| `cat-6` | #6CCAD8 | #0E7C8C | cyan |
| `cat-7` | #A9B4C6 | #6F7378 | ardoise |
| `cat-8` | #9FAE4F | #8A5A2B | olive / brun |

## Règles d'usage

- **Bouton principal** :
  - un seul par écran, en `bouton` et `sur-bouton` ;
  - les boutons secondaires sont des contours : fond `surface`, bordure `trait`, texte `texte` ;
  - le bleu n'est jamais un aplat de bouton.
- **Liens** : en `primaire`, toujours soulignés dans le texte courant, et en `primaire-vif` au survol.
- **Statuts** :
  - en pastille : texte coloré (`succes`, `alerte-texte`, `erreur`, `accent-texte` ou `primaire`) sur un fond qui mélange 13 % de sa couleur avec `surface`, soit `color-mix(in srgb, <couleur> 13%, <surface>)` ;
  - en aplat : `sur-statut` sur `erreur`, `succes` ou `accent`, et `texte-sur-vif` sur `alerte` ;
  - toujours avec une icône ou un libellé.
- **Graphiques** :
  - utiliser d'abord `cat-1` à `cat-4` ;
  - au-delà de quatre séries, ajouter une légende directe ou un motif, car certaines paires se confondent pour les personnes daltoniennes (protanopie, deutéranopie, tritanopie) ;
  - en clair, les séries 1 à 4 restent proches en deutéranopie : libeller directement.
- **Focus** : anneau de 2 px en `focus`, décalé de 2 px, visible sur tout élément interactif.
- **Modale** : `voile` derrière, `surface` et `halo` pour la boîte, rayon `grand`.

## Typographie

| Rôle | Police | Graisse | Pile |
|---|---|---|---|
| Titres, libellés forts, chiffres clés | Sora | 600 | `Sora, system-ui, 'Segoe UI', Roboto, sans-serif` |
| Texte courant, interface | Atkinson Hyperlegible | 400 | `'Atkinson Hyperlegible', system-ui, 'Segoe UI', Roboto, sans-serif` |
| Code, chasse fixe | JetBrains Mono | 400 | `'JetBrains Mono', 'Cascadia Mono', Consolas, ui-monospace, monospace` |

- Les trois polices sont sous licence SIL Open Font License. Un projet les sert lui-même, sans CDN.
- Un projet qui ne les embarque pas utilise la pile sans sa première police.

**Échelle des tailles (px)**

| `legende` | `petit` | `base` | `grand` | `titre-4` | `titre-3` | `titre-2` | `titre-1` |
|---|---|---|---|---|---|---|---|
| 12 | 14 | 16 | 18 | 22 | 28 | 36 | 48 |

## Formes

- **Rayons** : `petit` 6 px (champ, pastille), `moyen` 10 px (bouton, carte), `grand` 14 px (panneau, modale), `pilule` 999 px (badge).
- **Espacements** : 4, 8, 12, 16, 24, 32, 48 et 64 px (jetons `espacement.1` à `espacement.8`).
- **Trait** : 1 px.
- **Fond** : uni, sans motif ni grille.

## Pictogramme

Le pictogramme se compose de trois barres. Celle du milieu est plus courte et se termine par un point d'accent. La tuile est en `primaire`, les barres en `sur-primaire`, le point en `accent`.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" focusable="false">
  <rect width="32" height="32" rx="8" fill="var(--primaire)"/>
  <path d="M9 10h14M9 16h9M9 22h14" stroke="var(--sur-primaire)" stroke-width="3" stroke-linecap="round"/>
  <circle cx="23" cy="16" r="2.5" fill="var(--accent)"/>
</svg>
```

- **Logotype** : le pictogramme, puis le nom du projet en texte réel, en Sora 600 et en couleur `texte`. Les deux sont séparés de 8 px et centrés verticalement.
- **SVG** : il est décoratif (`aria-hidden`).
- **Favicon autonome** : il est produit par `generer.py` dans `dist/`.

## Supports

Chaque support a son fichier dans `skills/charte/dist/`, généré depuis les jetons :
- web : CSS, avec les thèmes clair et sombre et l'attribut `data-theme` ;
- graphiques : Python, matplotlib et plotly ;
- Streamlit ;
- Office : thème `.thmx` ;
- mermaid ;
- favicon.

Les règles propres à chaque support (impression et niveaux de gris, diapositives, README, image d'aperçu des réseaux sociaux) seront complétées en v2.1, après la mise à l'épreuve par les spécimens.
