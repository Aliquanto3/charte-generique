# Charte générique v2.1

Charte graphique commune à des applications web, des rapports, des présentations et des dépôts de code.

- **Sombre d'abord** : le thème sombre est le thème par défaut, et un thème clair le complète.
- **Source unique des valeurs** : [`skills/charte/jetons/charte.tokens.json`](../skills/charte/jetons/charte.tokens.json), au format DTCG 2025.10. Ce document décrit les rôles et les règles. Les tables ci-dessous sont comparées aux jetons par `tests/test_doc.py`.
- **Contrôles** : les deux commandes ci-dessous vérifient les contrastes WCAG 2.1, les pastilles de statut, le pictogramme et le filet, l'étiquette de badge, l'écart entre les pas des palettes séquentielle et divergente, et la distinction des séries de graphique en vision normale puis en dyschromatopsie. La première doit afficher `Échecs : 0`, la seconde rendre le code 0.

  ```sh
  uv run --no-project python -I skills/charte/outils/contrastes.py
  uv run --no-project python -I skills/charte/outils/daltonisme.py
  ```

## Principes

1. **Lisible avant tout.** Tout texte atteint 4,5:1 sur son fond, et toute marque non textuelle (contour de bouton ou de champ, anneau de focus, série de graphique, pictogramme) 3:1.
2. **Le sens ne passe jamais par la seule couleur.** Un statut porte toujours une icône ou un libellé. Une série de graphique porte un motif (tiret, marqueur ou hachure) et, selon les seuils de la section « Graphiques », une étiquette directe.
3. **Calme.** Fonds neutres et froids, sans motif ; formes arrondies ; halo doux plutôt qu'ombre dure.
4. **Un seul geste fort par écran** : le bouton principal, neutre et très contrasté. Le bleu sert à naviguer et à sélectionner, l'or à signaler.
5. **Une signature** : le pictogramme à point or, le filet or sous le titre et Sora, sur tous les supports.
6. **Libre** : polices sous licence OFL, servies localement ou incorporées, sans CDN.

## Palette par rôle

Valeurs en sombre, puis en clair. Les noms de rôle sont ceux des jetons.

| Rôle | Sombre | Clair | Usage |
|---|---|---|---|
| `fond` | #0F1318 | #F6F8FB | fond de page |
| `surface` | #161B22 | #FFFFFF | carte, panneau, diapositive |
| `surface-alt` | #1E242C | #ECF0F5 | barre latérale, zone secondaire, ligne paire de tableau, centre de la palette divergente |
| `trait` | #333B46 | #CED5DF | séparateur, bordure de carte ou de tableau (jamais un contour interactif) |
| `trait-fort` | #67717E | #808A97 | contour interactif : bouton secondaire, champ, sélecteur, modale, menu ; cellule isolée d'une carte de chaleur |
| `texte` | #E8ECF2 | #121821 | texte courant, titres |
| `texte-attenue` | #A3ADBA | #4F5A68 | texte secondaire, légende |
| `neutre` | #8792A0 | #6E7886 | indicateur neutre, état indisponible (non textuel) |
| `primaire` | #8DB0F7 | #1D5BC2 | lien, sélection, série 1 ; jamais un aplat de bouton |
| `primaire-vif` | #B3CBFA | #164A9E | lien survolé, titre fort |
| `primaire-doux` | #1A2742 | #E1EAFA | fond de sélection, pastille d'information |
| `sur-primaire` | #0A1733 | #FFFFFF | texte ou trait sur `primaire` (barres du pictogramme) |
| `bouton` | #E8ECF2 | #121821 | aplat du bouton principal |
| `bouton-survol` | #FFFFFF | #2A3442 | bouton principal survolé |
| `sur-bouton` | #0F1318 | #FFFFFF | libellé du bouton principal |
| `accent` | #E3C26B | #8F6300 | marque fine d'accent (or), non textuelle : filet sous le titre, liseré |
| `accent-texte` | #E3C26B | #8A5F00 | texte d'accent |
| `accent-doux` | #3A3112 | #FBF1D6 | bandeau d'accent |
| `accent-aplat` | #E3C26B | #E0B54A | grand aplat d'or (chiffre clé, moitié de diapositive), avec `texte-sur-vif` (et `texte` en clair) ; point du pictogramme en clair ; jamais une marque fine en clair (1,93:1 sur blanc) |
| `succes` | #8CC7A0 | #1B7043 | succès, état valide (texte et pastille) |
| `succes-doux` | #15291D | #E2F1E8 | bandeau de succès |
| `alerte` | #F0A35E | #E8892A | aplat d'alerte, toujours avec `texte-sur-vif` |
| `alerte-texte` | #F0A35E | #9A4A00 | texte d'alerte |
| `alerte-doux` | #3A2614 | #FDEBDA | bandeau d'alerte |
| `erreur` | #EE8C84 | #B3261E | erreur, blocage (texte et pastille) |
| `erreur-doux` | #3B1C1A | #FCE4E1 | bandeau d'erreur |
| `focus` | #9EC0FF | #1F5FD1 | anneau de focus |
| `texte-sur-vif` | #141A1F | #141A1F | texte sur `alerte` ou sur `accent-aplat` |
| `sur-statut` | #0F1318 | #FFFFFF | texte sur un aplat `erreur`, `succes` ou `accent` |
| `encre-pleine` | #1A2742 | #121821 | aplat foncé (terminal, bulle, bandeau de titre, couverture) |
| `sur-encre` | #FFFFFF | #FFFFFF | texte sur `encre-pleine` ou sur `badge-etiquette` |
| `sur-encre-attenue` | #C3CEDD | #C3CEDD | texte secondaire sur `encre-pleine` |
| `badge-etiquette` | #646E7B | #646E7B | moitié gauche (étiquette) des badges de README, même valeur dans les deux thèmes |
| `pictogramme-tuile` | #3B6FD0 | #1D5BC2 | tuile du pictogramme ; en clair, alias de `primaire` |
| `pictogramme-point` | #F0D27A | #E0B54A | point d'or du pictogramme ; en clair, alias d'`accent-aplat` |
| `voile` | rgba(5, 8, 12, 0.6) | rgba(18, 24, 33, 0.32) | voile de modale |
| `halo` | 0 8px 24px rgba(232, 236, 242, 0.07) | 0 8px 24px rgba(18, 24, 33, 0.08) | ombre portée douce (carte, menu, modale) |

Mesures clés (`contrastes.py`) :
- `trait-fort` sur `fond`, `surface`, `surface-alt` : 3,76, 3,49 et 3,15:1 en sombre ; 3,29, 3,50 et 3,06:1 en clair.
- `accent-aplat` : `texte` dessus à 9,23:1 en clair, `texte-sur-vif` à 9,09:1 en clair et 10,19:1 en sombre. En sombre, il vaut l'`accent` : l'or sombre se lit déjà comme de l'or en aplat, et un jeton distinct n'apporterait rien.
- `badge-etiquette` : blanc dessus à 5,17:1 ; 3,60:1 sur `fond` sombre et 4,86:1 sur `fond` clair ; 3,66:1 sur la page sombre de GitHub (`#0D1117`) et 5,17:1 sur la claire (`#FFFFFF`). Ces deux fonds de GitHub sont des constantes de `contrastes.py`, pas des jetons.

### Séries de graphique

Marques non textuelles, au moins 3:1 sur `surface`. Chaque série a aussi un motif, dans le même ordre (`MOTIFS` de `dist/charte.py`) : tiret, marqueur et hachure.

| Série | Sombre | Clair | Teinte |
|---|---|---|---|
| `cat-1` | #8DB0F7 | #1D5BC2 | bleu |
| `cat-2` | #E3C26B | #A87A00 | or |
| `cat-3` | #8CC7A0 | #1F8155 | sauge |
| `cat-4` | #E58FB8 | #B83A75 | framboise |
| `cat-5` | #F2A07B | #C24D1B | corail |
| `cat-6` | #6CCAD8 | #0E7C8C | cyan |
| `cat-7` | #A9B4C6 | #6F7378 | ardoise |
| `cat-8` | #9FAE4F | #8A5A2B | olive / brun |

Pire paire parmi les séries 1 à 4 en deutéranopie (`daltonisme.py`) : 9,9 en clair (`cat-3`/`cat-4`) et 13,7 en sombre.

### Palette séquentielle

Mélanges sRGB de `primaire` avec `surface` à 20, 40, 60, 80 et 100 %. Écart entre pas voisins : ΔE00 ≥ 9,4 en vision normale et en deutéranopie (contrôlé par `contrastes.py`).

| Pas | Sombre | Clair | Usage |
|---|---|---|---|
| `seq-1` | #2E394D | #D2DEF3 | valeur la plus basse |
| `seq-2` | #465777 | #A5BDE7 | |
| `seq-3` | #5D74A2 | #779DDA | |
| `seq-4` | #7592CC | #4A7CCE | |
| `seq-5` | #8DB0F7 | #1D5BC2 | valeur la plus haute (`primaire`) |

### Palette divergente

Deux ancres, `primaire` et le corail (`cat-5`), autour d'un centre neutre `surface-alt` ; les pas 2 et 4 mélangent chaque ancre à 50 % avec `surface-alt`. Écart entre pas voisins : ΔE00 ≥ 20 en vision normale et en deutéranopie.

| Pas | Sombre | Clair | Usage |
|---|---|---|---|
| `div-1` | #8DB0F7 | #1D5BC2 | extrême bas (`primaire`) |
| `div-2` | #566A92 | #84A6DC | |
| `div-3` | #1E242C | #ECF0F5 | centre neutre (`surface-alt`) |
| `div-4` | #886254 | #D79E88 | |
| `div-5` | #F2A07B | #C24D1B | extrême haut (corail, `cat-5`) |

Les pas bas et le centre restent sous 3:1 sur `surface` : ces deux palettes servent aux **aplats contigus** (carte de chaleur, choroplèthe), jamais à des séries isolées, qui gardent `cat-*`. Toujours une légende graduée ou la valeur écrite dans chaque cellule, et une bordure `trait-fort` autour d'une cellule isolée dans un pas bas.

## Règles d'usage

- **Bouton principal** :
  - un seul par écran, en `bouton` et `sur-bouton` ;
  - les boutons secondaires sont des contours : fond `surface`, contour `trait-fort`, texte `texte` ;
  - le bleu n'est jamais un aplat de bouton.
- **Champs et contours interactifs** : contour `trait-fort` (3:1 au moins) ; `trait` reste aux séparateurs. Un composant désactivé peut garder `trait` (WCAG exempte les composants inactifs).
- **Liens** : en `primaire`, toujours soulignés dans le texte courant, et en `primaire-vif` au survol.
- **Statuts** :
  - en pastille : texte coloré (`succes`, `alerte-texte`, `erreur`, `accent-texte` ou `primaire`) sur un fond qui mélange 13 % de sa couleur avec `surface`, soit `color-mix(in srgb, <couleur> 13%, <surface>)` ;
  - en aplat : `sur-statut` sur `erreur`, `succes` ou `accent`, et `texte-sur-vif` sur `alerte` ou `accent-aplat` ;
  - toujours avec une icône ou un libellé.
- **Or** : `accent` pour les marques fines (filet, liseré), `accent-texte` pour le texte, `accent-aplat` pour les grands aplats.
- **Fond sombre** : sur tout aplat sombre, même dans un document clair (couverture, bandeau, terminal), le pictogramme, le filet et les accents prennent les valeurs du thème sombre. Tuile `#3B6FD0` à 3,71:1 et filet or `#E3C26B` à 10,35:1 sur `encre-pleine` clair.
- **Focus** : anneau de 2 px en `focus`, décalé de 2 px, visible sur tout élément interactif.
- **Modale et menus** : `voile` derrière, `surface`, contour `trait-fort` et `halo` pour la boîte, rayon `grand`.

## Typographie

| Rôle | Police | Graisse | Pile web | Nom dans Office |
|---|---|---|---|---|
| Titres, libellés forts, chiffres clés | Sora | 600 | `Sora, system-ui, 'Segoe UI', Roboto, sans-serif` | `Sora SemiBold` |
| Texte courant, interface | Atkinson Hyperlegible | 400 et 700 | `'Atkinson Hyperlegible', system-ui, 'Segoe UI', Roboto, sans-serif` | `Atkinson Hyperlegible` |
| Code, chasse fixe | JetBrains Mono | 400 | `'JetBrains Mono', 'Cascadia Mono', Consolas, ui-monospace, monospace` | `JetBrains Mono` |

- Les trois polices sont sous licence SIL Open Font License 1.1, qui permet de les servir, de les incorporer et de les redistribuer (« can be bundled, embedded, redistributed and/or sold with any software », préambule des `skills/charte/polices/OFL-*.txt`). Leur `fsType` vaut 0 : incorporation permise. Un projet les sert lui-même, sans CDN.
- Le seul `ttf` de Sora fourni est la graisse 600, nommé « Sora SemiBold » (nom ID 1). Office le voit sous ce nom : c'est celui du thème Office et des documents. Les titres y sont en graisse normale, jamais en gras synthétique.
- **Repli** : un projet qui ne les embarque pas utilise la pile sans sa première police. En Office, si les polices ne sont ni incorporées ni installées : Segoe UI Semibold pour les titres et Segoe UI pour le texte. Le thème Office ne peut pas porter ce repli (`a:latin` prend une seule police) : il se choisit à la main.

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

Le pictogramme se compose de trois barres. Celle du milieu est plus courte et se termine par un point d'accent. Une tuile bleue, un point or : tuile et point ont leurs propres jetons, `pictogramme-tuile` et `pictogramme-point` (décision d'Anaël du 2026-11-05), lus par `jetons.PICTOGRAMME` ; les paires sont contrôlées par `contrastes.py`.

| Thème | Tuile | Barres | Point | Point sur tuile | Barres sur tuile | Tuile sur `fond`, `surface`, `encre-pleine` |
|---|---|---|---|---|---|---|
| sombre | `pictogramme-tuile` #3B6FD0 | `sur-primaire` | `pictogramme-point` #F0D27A | 3,25:1 | 3,69:1 | 3,88, 3,60 et 3,09:1 (3,71:1 sur `encre-pleine` clair) |
| clair | `pictogramme-tuile` = `primaire` | `sur-primaire` | `pictogramme-point` = `accent-aplat` | 3,27:1 | 6,31:1 | 5,93 et 6,31:1 |

Pourquoi une tuile propre au sombre : l'or `#E3C26B` sur `primaire` sombre `#8DB0F7` ne fait que 1,26:1. Avec la tuile bleu moyen `#3B6FD0` et l'or clair `#F0D27A`, le point garde 3:1 et la tuile tient 3:1 sur tous les fonds sombres. Le pictogramme clair ne se pose que sur un fond clair ; sur un aplat sombre, on prend le sombre (règle « fond sombre »).

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="28" height="28" aria-hidden="true" focusable="false">
  <rect width="32" height="32" rx="8" style="fill: var(--picto-tuile)"/>
  <path d="M9 10h14M9 16h9M9 22h14" fill="none" style="stroke: var(--picto-barres)" stroke-width="3" stroke-linecap="round"/>
  <circle cx="23" cy="16" r="2.5" style="fill: var(--picto-point)"/>
</svg>
```

- **Logotype** : le pictogramme, puis le nom du projet en texte réel, en Sora 600 et en couleur `texte`. Les deux sont séparés de 8 px et centrés verticalement.
- **SVG** : il est décoratif (`aria-hidden`). `charte.css` définit `--picto-tuile`, `--picto-barres` et `--picto-point` pour chaque thème.
- **Favicon autonome** : il est produit par `generer.py` dans `dist/`.
- **Filet or** : sous le titre principal de chaque support (couverture de deck, titre de rapport, bannière, aperçu social, première page web). Trait court et arrondi en `accent` (96 × 4 px à l'écran) ; en sombre, or `#E3C26B` ; en clair, `#8F6300` (5,31:1 sur `surface`). Un filet épais posé sur un aplat sombre prend l'or sombre (10,35:1 sur `encre-pleine` clair).

## Règles par support

Chaque support a ses fichiers dans `skills/charte/dist/`, générés par `generer.py` depuis les jetons (`uv run --no-project python -I skills/charte/generer.py`, `--verifier` pour contrôler qu'ils sont à jour).

### Web

- Fichiers : `charte.css` (variables des deux thèmes : sombre par défaut, clair par `prefers-color-scheme` ou `data-theme="clair"`/`"light"`, sombre forcé par `data-theme="sombre"`/`"dark"` ; polices, tailles, espacements, rayons, pictogramme) et `charte-base.css` (styles minimaux d'éléments : corps, titres, liens, focus, code, sélection).
- Première page : titre, puis filet or, puis le contenu.
- Contours interactifs en `trait-fort` ; cartes et tableaux en `trait`.

### Impression et niveaux de gris

- Chaque série de graphique porte un motif (tirets, marqueurs, hachures) ; la couleur n'est qu'un appoint.
- Les fonds pleins passent en contour : pastilles, bandeaux, aplats d'or, bouton principal (contour épais).
- Les bandeaux et pastilles gardent leur intitulé en gras.
- Les blocs évitent la coupure (`break-inside: avoid`).

### Diapositives

- Titres d'au moins 28 pt, en Sora 600 (`Sora SemiBold` incorporée), à défaut en Segoe UI Semibold.
- Au plus six séries par graphique (le thème Office n'a que six accents, `cat-1` à `cat-6`) ; étiquette de données dès cinq séries, et dès deux séries en clair (règle des graphiques) ; motif au-delà de quatre.
- Couverture et fin sur `encre-pleine` : pictogramme et filet en valeurs sombres.
- Grand aplat d'or : `accent-aplat`, texte `texte`.

### Rapport

- Titre suivi du filet or (bordure basse `accent` de 3 pt dans Word).
- Figures matplotlib avec `charte-document.mplstyle` : fond `surface` (pas de cadre gris sur la page blanche), tailles des jetons en pt, titre à gauche, légende sans cadre, 200 dpi, `savefig.bbox: tight` ; étiquettes directes plutôt que légende.
- Polices incorporées au document (voir « Office »).

### README et badges

- Bannière en `<picture>` (une source par thème), `<img>` de repli **clair**, le thème par défaut de GitHub.
- Diagramme mermaid : bloc de code en thème `neutral` (`%%{init: {"theme": "neutral"}}%%`), sans fond propre, lisible sur les deux pages ; ou deux images rendues avec `mermaid-sombre.json` et `mermaid-clair.json` sous `<picture>`, repli clair.
- Badges shields.io : valeur dans la couleur du statut (variante lisible avec le texte imposé par shields.io : `alerte-texte`, `texte-attenue`), étiquette `labelColor` en `badge-etiquette`, la même dans les deux thèmes.

### Aperçu social

- Image de 1280 × 640, en sombre.
- Zone utile centrée, dans des marges sûres de 80 px.
- Titre d'au moins 64 px, aucun texte sous 28 px (l'image est souvent réduite à 400 px de large).
- Pictogramme et filet or.

### Streamlit

- Fichiers : `streamlit-sombre.toml`, `streamlit-clair.toml`.
- **Jamais `type="primary"`** : Streamlit remplit ce bouton en `primaryColor` avec un libellé blanc imposé (2,17:1 sur le primaire sombre), ce qui contredit aussi la règle « le bleu n'est jamais un aplat de bouton ». Tous les boutons sont en contour (libellé `texte`).
- `primaryColor` reste `primaire` : Streamlit s'en sert aussi pour les cases, curseurs, onglets et le focus, qui doivent rester bleus.
- `borderColor` vaut `trait-fort` (contours ≥ 3:1).
- Limite connue : `st.success` et le code en ligne gardent les couleurs propres de Streamlit.

### Graphiques

- Fichiers : matplotlib `charte-sombre.mplstyle`, `charte-clair.mplstyle`, `charte-document.mplstyle` ; plotly `plotly-sombre.json`, `plotly-clair.json` (gabarit `layout.template`) ; motifs `MOTIFS` de `charte.py`.
- Utiliser d'abord `cat-1` à `cat-4`.
- **Motif** : le cycle matplotlib combine couleur, tiret et marqueur ; en plotly, les tirets (`line.dash`), marqueurs (`marker.symbol`) et hachures (`marker.pattern.shape`) ne passent pas par le gabarit : les appliquer trace par trace depuis `MOTIFS`. Hachures pour les barres.
- **Étiquette directe** : au-delà de quatre séries, et dès deux séries en clair (les séries restent proches en deutéranopie). En bout de ligne, sans chevauchement : écart vertical minimal d'une hauteur de ligne entre deux étiquettes.
- Palettes `seq` et `div` pour les aplats contigus seulement (voir plus haut).

### Office

- Fichiers : `theme-office.xml` et `charte.thmx` (thème clair, qui imprime bien ; six accents `cat-1` à `cat-6`), polices `Sora SemiBold` (titres) et `Atkinson Hyperlegible` (texte).
- **Polices incorporées** au .pptx et au .docx :
  - Word : `word/fonts/*.odttf`, obfusqués selon ECMA-376 partie 1, §17.8.1 (XOR des 32 premiers octets avec la clé GUID `w:fontKey`, lue octets inversés), `w:embedRegular`/`w:embedBold` dans `fontTable.xml`, `w:embedTrueTypeFonts` dans `settings.xml` ;
  - PowerPoint : `ppt/fonts/*.fntdata` au format Embedded OpenType (le TTF brut est ignoré), `p:embeddedFontLst` après `p:notesSz`.
  - Recette : `specimens/office/incorporer.py` ; preuve par le PDF rendu : `specimens/office/polices_pdf.py`.
- Repli si un lecteur ignore les polices incorporées : Segoe UI Semibold pour les titres, Segoe UI pour le texte, à choisir à la main.

### Mermaid

- `mermaid-sombre.json`, `mermaid-clair.json` : thème `base` et variables de la charte, pour un rendu où l'on maîtrise le fond (site, image de référence). Sur GitHub, préférer `neutral` (voir « README »).

## Changements depuis la v2.0

D'après la critique sur pièces (`docs/critique-v2.0.md`), sections 3A et 3B :

- **A1** : valeurs de `cat-4` et `cat-5` permutées dans les deux thèmes (framboise en 4, corail en 5). Pire paire 1 à 4 en deutéranopie : 4,4 → 9,9 en clair, 5,9 → 13,7 en sombre.
- **A2** : motifs (tirets, marqueurs, hachures) dans les gabarits matplotlib et dans `MOTIFS` pour plotly ; étiquettes directes sans chevauchement dans les spécimens.
- **A3, A12** : repli Segoe UI documenté ; règles de diapositive (titres ≥ 28 pt, six séries au plus, étiquettes de données).
- **A4** : règle « fond sombre » ; pictogramme choisi par mesure dans chaque thème ; jetons `pictogramme-tuile` et `pictogramme-point` (décision d'Anaël du 2026-11-05).
- **A5** : nouveau jeton `trait-fort` pour les contours interactifs.
- **A6** : palettes `seq-1` à `seq-5` et `div-1` à `div-5`.
- **A7** : règle d'impression et de gris.
- **A8** : règle README (mermaid `neutral` ou `<picture>`, replis clairs) et jeton `badge-etiquette`.
- **A10** : `savefig.bbox: tight` et style `charte-document.mplstyle`.
- **A11** : règle de l'aperçu social.
- **B1 a** : teinte primaire inchangée.
- **B2 b** : nouveau jeton `accent-aplat` pour les grands aplats d'or.
- **B3 a** : Sora, Atkinson Hyperlegible et JetBrains Mono incorporées aux documents Office ; noms Office dans les jetons (`$extensions.charte.office`).
- **B4 b** : Streamlit sans `type="primary"`, boutons en contour.
- **B5 a** : filet or sous le titre sur tous les supports.
