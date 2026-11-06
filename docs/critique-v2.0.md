# Critique de la charte v2.0 sur pièces

Story 1.6, 2026-11-05. Regard de directeur artistique et d'expert en accessibilité, sur les rendus de `specimens/` (base `main` à 5645481).

Méthode : rendus jugés d'abord sans lire les `LISEZMOI.md`. Toutes les mesures viennent de `contrastes.py`, `daltonisme.py --markdown`, `couleurs.contraste` / `couleurs.de00` / `couleurs.lab`, et de pixels lus avec Pillow. Les PDF ont été rastérisés à part (pypdfium2, environnement jetable, hors dépôt). Le ΔE00 est noté ΔE.

## 1. Verdict

La charte tient sur le web et sur le README : calme, lisible, `Échecs : 0`, et une identité nette (pictogramme, point or, Sora). Elle ne tient pas encore hors du navigateur. Ses trois défauts majeurs :
1. **Office perd l'identité** : polices de repli non maîtrisées (empattements dans Word), et couverture sombre faite avec les jetons clairs (tuile du pictogramme à 2,82:1).
2. **Les séries de graphique ne tiennent ni en daltonisme ni en gris** : `cat-2`/`cat-4` clair à ΔE 4,4 en deutéranopie, ΔL* 0,3 entre `cat-3` et `cat-4` en gris, et aucun gabarit n'applique la règle « au-delà de quatre séries ».
3. **Le bouton principal Streamlit échoue** : libellé blanc sur `#8DB0F7`, 2,17:1.

## 2. Constats

Gravité : 3 bloquants, 8 importants, 10 mineurs.

### Bloquants

**B1. Bouton principal Streamlit illisible.**
- Support : Streamlit, `specimens/graphiques/rendus/streamlit-sombre.png`, `dist/streamlit-sombre.toml`.
- Ce qu'on voit : « Action principale » en blanc fin sur un bleu pâle, qui se lit mal.
- Mesure : pixels `#FFFFFF` sur `#8DB0F7`, soit 2,17:1 (seuil 4,5:1).
- Règle : principe 1 (texte 4,5:1) et règle « le bleu n'est jamais un aplat de bouton », déjà dérogée par l'exception Streamlit.
- Correction : décision d'identité, voir (B4).

**B2. Office : polices de repli non maîtrisées, l'identité disparaît.**
- Support : Office, `deck-1.png` à `deck-6.png`, `rapport-1.png`, `rapport.pdf`, `dist/theme-office.xml`.
- Ce qu'on voit :
  - PowerPoint rend tout dans une sans-serif de substitution, d'aspect Calibri. Les titres sont en graisse normale, pas en 600.
  - Word rend le rapport en **police à empattements**, d'aspect Cambria. Cela contredit la charte, qui est toute en sans-serif.
  - Le deck et le rapport ne se ressemblent plus, et aucun des deux ne ressemble à la page web.
- Mesure : le thème Office déclare seulement `Sora` (majeure) et `Atkinson Hyperlegible` (mineure), sans aucune police de repli. Chaque application choisit donc sa propre substitution.
- Règle : typographie (« un projet qui ne les embarque pas utilise la pile sans sa première police »). Cette règle est inapplicable en Office, où un thème ne prend qu'une police par rôle.
- Correction : (A3) dans un premier temps, et la décision (B3).

**B3. Séries 1 à 4 confondues en deutéranopie (clair), sans étiquette directe dans les gabarits.**
- Support : graphiques, `mpl-barres-clair-simulation.png`, `plotly-barres-*-simulation.png`, `deck-3.png`.
- Ce qu'on voit : en deutéranopie, l'or (`cat-2`) et le corail (`cat-4`) deviennent deux olives presque identiques. Les barres n'ont qu'une légende, sans étiquette directe.
- Mesure (`daltonisme.py`) :
  - clair, séries 1 à 4 : deutéranopie `cat-2`/`cat-4` ΔE 4,4 ;
  - sombre, séries 1 à 4 : deutéranopie `cat-2`/`cat-4` ΔE 5,9, protanopie `cat-3`/`cat-4` ΔE 7,6.
- Règle : la charte le sait (« en clair, les séries 1 à 4 restent proches en deutéranopie : libeller directement »), mais aucun gabarit (`mplstyle`, `plotly-*.json`, thème Office) ni aucun spécimen de barres ne le fait.
- Correction : (A1) permuter `cat-4` et `cat-5`, et (A2) rendre l'étiquette directe obligatoire. Mesures de la permutation, pire paire parmi les séries 1 à 4 :

  | Thème | Normale | Protanopie | Deutéranopie | Tritanopie |
  |---|---|---|---|---|
  | clair, actuel | 23,9 | 10,7 | **4,4** | 12,7 |
  | clair, `cat-4` ⇄ `cat-5` | 33,7 | 12,9 | **9,9** | 12,7 |
  | sombre, actuel | 21,7 | 7,6 | **5,9** | 8,2 |
  | sombre, `cat-4` ⇄ `cat-5` | 25,7 | 12,4 | **13,7** | 8,2 |

  La nouvelle `cat-4` (framboise) fait 5,38:1 sur `surface` en clair et 7,37:1 en sombre.

### Importants

**I1. Couverture sombre Office faite avec les jetons clairs.**
- Support : Office, `deck-1.png`, `deck-6.png`.
- Ce qu'on voit : une tuile bleu soutenu sur fond nuit, un point or devenu brun et invisible, et un filet or terne sous le titre.
- Mesure (pixels) : fond `#121821`, tuile `#1D5BC2`, point et filet `#8F6300`.
  - tuile sur fond : 2,82:1, sous le seuil de 3:1 d'une marque non textuelle ;
  - point sur tuile : 1,19:1 ;
  - filet sur fond : 3,35:1.
- Règle : pictogramme (« tuile `primaire`, point `accent` ») ; aucune règle ne dit quels jetons prendre sur un fond sombre dans un document clair.
- Correction (A4) : sur tout fond sombre, prendre les valeurs sombres (tuile `#8DB0F7` à 8,22:1 sur `#121821`, point et filet `#E3C26B` à 10,35:1), comme le font déjà le README sombre et l'aperçu social.

**I2. L'or clair en grand aplat ne se lit pas comme de l'or.**
- Support : Office, `deck-5.png` (moitié gauche de la diapositive).
- Ce qu'on voit : un brun kaki terne, couleur « boue ». Le texte blanc y est lisible, mais le signal « accent » est perdu.
- Mesure : pixel `#8F6300`, soit L* 45, C* 54, h 79°. Blanc dessus : 5,31:1.
- Règle : `accent` clair = « marque d'accent, non textuelle » ; aucune règle sur l'aplat.
- Correction : décision d'identité (B2).

**I3. La bordure des boutons secondaires contredit le principe 1.**
- Support : web, `specimen-clair.png`, `specimen-sombre.png` (boutons « Secondaire », « Annuler », « Ouvrir »).
- Ce qu'on voit : en clair, le contour du bouton se devine à peine.
- Mesure : `trait` sur `surface` donne 1,53:1 en sombre et 1,48:1 en clair ; sur `fond`, 1,65:1 et 1,39:1. Le seuil est de 3:1.
- Règle : le principe 1 exige 3:1 pour une « bordure de bouton », alors que la règle des boutons prescrit `trait`.
- Correction (A5) : un nouveau jeton `trait-fort` pour les contours interactifs, `trait` restant réservé aux séparateurs :

  | Thème | `trait-fort` | sur `fond` | sur `surface` | sur `surface-alt` |
  |---|---|---|---|---|
  | sombre | `#67717E` | 3,76:1 | 3,49:1 | 3,15:1 |
  | clair | `#808A97` | 3,29:1 | 3,50:1 | 3,06:1 |

  Autre option : réutiliser `neutre` (5,48:1 en sombre et 4,47:1 en clair sur `surface`), plus dur à l'œil.

**I4. Pas de palette séquentielle.**
- Support : graphiques, `mpl-chaleur-clair.png`.
- Ce qu'on voit : un dégradé bleu fabriqué dans le spécimen. Sa valeur basse se fond dans le fond de la figure.
- Mesure : bas de l'échelle `#E7ECF4`, soit 1,12:1 sur `fond` et 1,19:1 sur `surface`.
- Règle : il n'en existe pas ; c'est un point ouvert de la charte.
- Correction (A6) : cinq jetons `seq-1` à `seq-5`, mélanges sRGB de `primaire` avec `surface` (20, 40, 60, 80 et 100 %) :

  | Thème | Pas | Contraste sur `surface` | ΔE entre pas (normale) | ΔE entre pas (deutéranopie) |
  |---|---|---|---|---|
  | clair | `#D2DEF3` `#A5BDE7` `#779DDA` `#4A7CCE` `#1D5BC2` | 1,36 / 1,90 / 2,76 / 4,15 / 6,31 | 10,2 à 11,7 | 10,7 à 12,1 |
  | sombre | `#2E394D` `#465777` `#5D74A2` `#7592CC` `#8DB0F7` | 1,49 / 2,38 / 3,69 / 5,55 / 7,98 | 9,4 à 11,4 | 9,6 à 11,4 |

  Les pas bas sont sous 3:1 sur `surface` : en clair `seq-1` à `seq-3`, en sombre `seq-1` et `seq-2`. Cette palette sert donc aux **aplats contigus** (carte de chaleur, choroplèthe), jamais à des séries isolées, qui gardent `cat-*`. Règles d'accompagnement :
  - une légende graduée, ou la valeur écrite dans chaque cellule ;
  - une cellule isolée dans un pas bas porte une bordure `trait-fort` (A5).

  Une 6ᵉ étape plus foncée en clair a été écartée : `primaire-vif` `#164A9E` n'est qu'à ΔE 6,9 de `seq-5`. Une palette divergente reste à faire, sur le même principe : `primaire` d'un côté, le corail (`cat-5` après A1) de l'autre.

**I5. La règle « au-delà de quatre séries » n'est appliquée par aucun gabarit.**
- Supports :
  - `plotly-lignes-clair.png` : 8 séries avec légende seule ;
  - `deck-3.png` : 6 séries avec légende seule ;
  - `mpl-lignes-sombre.png` : étiquettes directes superposées en bout de courbe (séries 3, 4 et 5, puis 6 et 7).
- Mesure : pire paire parmi les 8 séries, de ΔE 4,0 à 4,6 selon le thème et la dyschromatopsie (`daltonisme.py`). Exemples : clair `cat-4`/`cat-8` 4,1 en protanopie, sombre `cat-6`/`cat-7` 4,1 en protanopie.
- Règle : « au-delà de quatre séries, légende directe ou motif ».
- Correction (A2) : étiquettes directes avec anti-chevauchement (décalage vertical minimal égal à la hauteur de ligne), ou motifs : tirets et marqueurs dans le cycle mpl et plotly (`axes.prop_cycle` avec `linestyle` et `marker`), hachures pour les barres.

**I6. Impression en gris : les séries se confondent, et la charte n'a aucune règle d'impression.**
- Support : `specimen-gris.pdf`, page 4.
- Ce qu'on voit : les barres et les lignes prennent toutes le même gris moyen. Seules les étiquettes les distinguent.
- Mesure (L* des séries) :
  - clair, de 40,6 à 54,3 ; `cat-3`/`cat-4` ΔL* 0,3 ; `cat-4`/`cat-7` ΔL* 0,2 ;
  - sombre, de 68,2 à 79,6 ; `cat-1`/`cat-4` ΔL* 1,4.
  - Bandeaux `*-doux` clairs : L* de 92,4 à 95,3.
- Règle : aucune (« règles par support… en v2.1 »).
- Correction (A7), règle d'impression :
  - en sortie papier ou en gris, chaque série porte un motif (tirets, marqueurs, hachures), et la couleur n'est qu'un appoint ;
  - les fonds pleins passent en contour, ce que fait déjà le CSS d'impression du spécimen web ;
  - les bandeaux gardent leur intitulé en gras.

**I7. Mermaid sombre sur un README clair.**
- Support : README, `readme-clair.png`, `mermaid.png`.
- Ce qu'on voit : un bandeau noir posé au milieu d'une page claire.
- Mesure : pixels `#1E242C` sur `#F6F8FB`, soit un écart de 14,69:1. C'est une rupture franche.
- Règle : aucune règle README.
- Correction (A8), règle README :
  - diagramme mermaid en thème `neutral`, sans fond, ou deux images SVG sous `<picture>` comme la bannière ;
  - `<img>` de repli en clair, le thème par défaut de GitHub.

**I8. Identité : propre mais générique en sombre.**
- Supports : tous.
- Ce qu'on voit : la page sombre ressemble à GitHub sombre. Le bleu pervenche est un bleu d'interface standard. Ce qui signe la charte tient en trois choses : le pictogramme à point or, le filet or et Sora. Or Sora disparaît en Office, en Plotly et dans Streamlit (Segoe UI de repli).
- Mesure : `surface` sombre `#161B22` est aussi la surface du thème sombre de GitHub. `primaire` : L* 72, C* 40, h 279° en sombre ; L* 41, C* 62, h 289° en clair.
- Règle : aucune règle d'identité (signature, usages du filet or).
- Correction :
  - (B5) faire du **filet or sous le titre** une règle de tous les supports : couverture de deck, titre de rapport, bannière, aperçu social, première page web. C'est l'élément le plus reconnaissable des rendus, mais il change la signature : décision d'Anaël.
  - (B1) et (B3) pour la teinte et les polices.

### Mineurs

**m1. Streamlit : couleurs hors jetons.**
- Support : `streamlit-sombre.png`.
- Mesure : `st.success` donne un texte `#5CE488` sur `#183A29` (7,70:1), et le code en ligne `#5CE488` sur `#161C22`. Le jeton `succes` sombre vaut `#8CC7A0`, à 7,90:1 sur `succes-doux`.
- Effet : un vert néon étranger à la charte.
- Correction : poser les clés de couleur de Streamlit, si la version en offre ; sinon documenter la limite.

**m2. Légende coupée sous les barres matplotlib.**
- Support : `mpl-barres-clair.png`, `mpl-barres-sombre.png`.
- Ce qu'on voit : les libellés « Série 1 » à « Série 4 » sont tronqués au bas de l'image.
- Correction (A10) : `savefig.bbox: tight` dans les deux `mplstyle`.

**m3. Graphique du rapport.**
- Support : `rapport-1.png`.
- Ce qu'on voit :
  - la légende masque le point « Revue » de février ;
  - le graphique garde le fond `fond` de la figure, ce qui fait un cadre gris sur la page blanche (pixels `#F8F8F8` et `#F6F8F8` contre `#FFFFFF`) ;
  - l'image est floue à l'agrandissement.
- Correction : un style « document » (`figure.facecolor` = `surface`, légende hors du tracé, export en SVG ou à 200 dpi).

**m4. Badges du README sombre : l'étiquette disparaît.**
- Support : `readme-sombre.png`.
- Mesure : la moitié gauche du badge, `#121821`, sur la page `#0F1318` : 1,05:1. Le badge perd sa forme.
- Correction : une seule étiquette `#646E7B`, valable dans les deux thèmes. Elle porte le blanc à 5,17:1 et se détache à 3,60:1 de la page sombre et à 4,86:1 de la page claire. Pas besoin de `<picture>`. `#4F5A68` (`texte-attenue` clair) ne suffit pas : 2,66:1 sur la page sombre. `neutre` clair `#6E7886` non plus : 4,47:1 avec le blanc.

**m5. Aperçu social vide à droite.**
- Support : `apercu-social.png`.
- Ce qu'on voit : le bloc occupe la moitié gauche, et l'autre moitié est vide. Réduite à 400 px de large, le sous-titre devient très petit.
- Correction (A11), règle de l'aperçu social :
  - titre d'au moins 64 px à 1280 × 640 ;
  - zone utile centrée, marges sûres de 80 px ;
  - filet or ;
  - pas de texte sous 28 px.

**m6. Surfaces sombres peu étagées, voile sombre invisible.**
- Support : `specimen-sombre.png`.
- Mesure :
  - `surface` sur `fond` : 1,08:1 (ΔE 2,8) ;
  - dans la zone du voile de la modale, le pixel vaut `#0F1318`, soit le fond exact : le voile ne se voit pas.
- Effet : la modale ne tient que par son contour `trait`, à 1,65:1.
- Correction : garder les valeurs, mais ajouter le contour `trait-fort` (I3) à la modale et aux menus.

**m7. Le thème Office n'a que six accents.**
- Support : `theme-office.xml`.
- Mesure : `accent1` à `accent6` valent `cat-1` à `cat-6` ; `cat-7` et `cat-8` sont absents.
- Effet : un 7ᵉ graphique Office reprend des teintes Office.
- Correction : documenter la limite à six séries en Office, avec le motif obligatoire au-delà de quatre.

**m8. L'impression web gaspille des pages.**
- Support : `specimen-clair.pdf`.
- Mesure : 5 pages A4. Les pages 2, 3 et 4 sont remplies aux deux tiers environ, à cause des sauts de section.
- Correction : `break-inside: avoid` sur les blocs plutôt que des sauts de page par section.

**m9. Le rapport affiche un chiffre rassurant mais partiel.**
- Support : `rapport.pdf`, page 2.
- Ce qu'on voit : « Écart minimal entre séries (ΔE00) : 14,7 / 12,1 ». Ce chiffre vaut en vision normale seulement, alors que la pire paire descend à ΔE 4,0 en dyschromatopsie.
- Correction : afficher aussi la pire valeur en dyschromatopsie.

**m10. Bandeaux `*-doux` indistincts en gris.**
- Support : `specimen-gris-page1.png`.
- Mesure : L* de 92,4 à 95,3 en clair, de 14,6 à 20,6 en sombre.
- Effet : sans conséquence tant que l'intitulé en gras reste. C'est déjà le cas, et la règle A7 le rend obligatoire.

## 3. Listes de corrections

### (A) Corrections sans effet sur l'identité, applicables en v2.1

| # | Correction | Mesure attendue |
|---|---|---|
| A1 | Permuter `cat-4` (corail) et `cat-5` (framboise) dans les deux thèmes | séries 1 à 4, pire paire en deutéranopie : 4,4 → 9,9 en clair, 5,9 → 13,7 en sombre |
| A2 | Appliquer dans les gabarits les règles existantes : étiquette directe au-delà de quatre séries, et dès deux séries en clair (la charte le prescrit déjà : « en clair, les séries 1 à 4 restent proches en deutéranopie : libeller directement ») ; anti-chevauchement ; cycle de tirets et de marqueurs dans mpl et plotly. Aucune règle nouvelle. Après A1, l'assouplissement de la consigne en clair serait une décision à part | pas de chevauchement dans `mpl-lignes-*` |
| A3 | Thème Office : documenter le repli explicite (Segoe UI Semibold pour les titres, Segoe UI pour le texte) tant que les polices ne sont pas incorporées (B3) | plus d'empattements dans Word |
| A4 | Règle « fond sombre » : sur tout aplat sombre (couverture, bandeau, terminal), pictogramme, filet et accents en valeurs sombres | tuile 8,22:1, or 10,35:1 sur `#121821` |
| A5 | Jeton `trait-fort` (sombre `#67717E`, clair `#808A97`) pour les contours interactifs | ≥ 3,06:1 sur `fond`, `surface` et `surface-alt` |
| A6 | Jetons `seq-1` à `seq-5` (table I4), réservés aux aplats contigus, avec légende ou valeurs et bordure `trait-fort` pour une cellule isolée en pas bas ; palette divergente sur le même principe | ΔE ≥ 9,4 entre pas, en normale et en deutéranopie |
| A7 | Règle d'impression et de gris : motif par série, fonds en contour, intitulés en gras | ne dépend plus de ΔL* |
| A8 | Règle README : mermaid `neutral` ou `<picture>`, repli clair ; étiquette de badge `#646E7B` dans les deux thèmes | blanc 5,17:1 ; 3,60:1 sur la page sombre, 4,86:1 sur la page claire |
| A10 | `savefig.bbox: tight` dans les `mplstyle` ; style « document » pour les figures insérées dans un rapport | légende entière |
| A11 | Règle de l'aperçu social (taille de titre, zone sûre) | — |
| A12 | Règle de diapositive : titres en Segoe UI Semibold tant que Sora n'est pas incorporée (A3), en Sora 600 ensuite (B3 a) ; au moins 28 pt ; au plus six séries ; étiquette de données dès cinq séries | — |

A9 (filet or) est passé en liste B (B5) : il change la signature visuelle.

Toute nouvelle valeur de cette critique a été contrôlée contre la liste locale des couleurs à éviter (ΔE ≥ 15).

### (B) Décisions d'identité, réservées à Anaël

**B1. Teinte primaire**

| Option | Clair | Sombre | Mesures |
|---|---|---|---|
| a. garder | `#1D5BC2` (L* 41, C* 62, h 289°) | `#8DB0F7` (h 279°) | 6,31:1 et 7,98:1 sur `surface` ; ΔE au plus proche (`cat-7` sombre) 12,1 |
| b. bleu acier, désaturé | `#1565A8` (L* 42, C* 42, h 273°) | `#8DB8E8` (L* 73, C* 29, h 265°) | 6,07:1 et 8,36:1 sur `surface` ; `sur-primaire` sur le sombre 8,58:1 ; `cat-7` sombre à ΔE 10,2, à la limite |
| c. bleu pétrole | `#0F5F8C` (h 260°) | `#7CC3E8` (h 244°) | 6,92:1 et 8,92:1, mais ΔE 9,5 avec `cat-6` sombre : il faudrait refaire `cat-6` |

Recommandation : **a**. Le caractère doit venir de l'or, de Sora et du filet (B5), pas d'un changement de bleu qui coûterait une palette.

**B2. Accent or en clair, en aplat**

| Option | Valeur | Texte dessus | Lecture |
|---|---|---|---|
| a. garder `#8F6300` | L* 45, C* 54, h 79° | blanc 5,31:1 | brun boue en grand aplat |
| b. nouveau jeton `accent-aplat` | `#E0B54A` (L* 76, C* 59, h 86°) | `texte` 9,23:1 | or franc ; à 17,1 ΔE de `alerte` ; jamais en marque fine (1,93:1 sur blanc) |
| c. or moyen | `#D4A537` (L* 70, C* 61, h 84°) | `texte` 7,84:1 | plus chaud, plus proche de `alerte` (ΔE 14,4) |

Recommandation : **b**, réservé aux aplats et au point du pictogramme en clair. Sur la tuile `#1D5BC2`, le point passerait de 1,19:1 (`#8F6300`) à 3,27:1 avec `#E0B54A`. `accent` `#8F6300` reste pour les marques fines.

**B3. Polices**

| Option | Effet |
|---|---|
| a. garder Sora, Atkinson et JetBrains Mono ; les incorporer dans les .pptx et .docx (licence OFL, incorporation permise) ; repli Segoe UI documenté (A3) | identité tenue partout, au prix de fichiers plus lourds |
| b. Sora pour le web et le README seulement ; Office et Streamlit assumés en Segoe UI | simple, mais deux visages de la charte |
| c. remplacer Sora par une police système | la charte perd son principal trait de caractère |

Recommandation : **a**. Sans Sora, la charte devient anonyme.

**B4. Bouton principal Streamlit**

La règle de la charte est « le bleu n'est jamais un aplat de bouton » : le bouton principal est neutre, et c'est un de ses points forts (section 5). Toute option en bleu plein est donc une **exception propre à Streamlit**, qui vient de son libellé blanc imposé.

| Option | Respect de la règle | Mesures |
|---|---|---|
| b. ne pas utiliser `type="primary"` ; boutons en contour seulement | oui | libellé `texte` sur `surface` sombre ; perd le « geste fort » |
| a. exception Streamlit : `primaryColor` `#3B6FD0` | non, exception documentée | blanc 4,80:1 ; sur `fond` 3,88:1 |
| a′. exception Streamlit, variante `#2F6FE0` | non, exception documentée | blanc 4,70:1 ; sur `fond` 3,97:1 |
| c. garder `#8DB0F7` | non, et non conforme WCAG 1.4.3 | 2,17:1 |

Recommandation : **b** par défaut, puisqu'il respecte la règle. Choisir **a** seulement si Anaël veut garder un geste fort dans Streamlit. Dans ce cas, l'exception est à documenter dans la charte, avec ses effets : `primaryColor` colore aussi les cases et les curseurs.

**B5. Filet or sous le titre, en signature**

| Option | Effet |
|---|---|
| a. règle de tous les supports : couverture de deck, titre de rapport, bannière, aperçu social, première page web | signature reconnaissable partout ; or sombre `#E3C26B` sur fond sombre, `accent` `#8F6300` (5,31:1 sur blanc) en clair |
| b. le garder seulement sur la bannière et l'aperçu social, comme aujourd'hui | statu quo ; identité faible hors README |

Recommandation : **a**. C'est le geste le plus distinctif des rendus, et il ne coûte aucune couleur nouvelle.

## 4. Recoupement avec les constats des `LISEZMOI`

| Constat (`LISEZMOI`) | Statut | Commentaire |
|---|---|---|
| Graphiques : bouton Streamlit 2,17:1 | trouvé seul, confirmé | mêmes pixels (`#FFFFFF` sur `#8DB0F7`) ; je recommande l'option b (pas de `type="primary"`), qui respecte la règle, et l'option a seulement en exception documentée |
| Graphiques : pas de palette séquentielle | trouvé seul, confirmé | valeur basse à 1,12:1 sur le fond ; jetons proposés (A6) |
| Graphiques : étiquettes des 8 lignes qui se chevauchent | trouvé seul, confirmé | j'ai vu aussi les séries 3, 4 et 5 superposées en sombre |
| Graphiques : `cat-4`/`cat-8` clair proches (protanopie 4,1), `cat-1` vert-bleu en tritanopie | confirmé | mais le défaut le plus grave est `cat-2`/`cat-4` à 4,4 parmi les quatre **premières** séries (B3) |
| Graphiques : Plotly et Streamlit en polices de repli | trouvé seul, confirmé | — |
| Graphiques : couleurs Streamlit hors jetons | trouvé seul, confirmé | m1 |
| Graphiques : en-tête Streamlit non thémé | confirmé | sans gravité |
| Web : bordure `trait` du bouton secondaire, 1,53 et 1,48:1 | non trouvé seul, confirmé par la mesure | I3 ; je préfère un jeton `trait-fort` à `neutre` |
| Web : pastilles avec icône et libellé | confirmé | à garder |
| Web : séries 5 à 8 proches en gris | contesté en partie | le problème touche aussi les séries 1 à 4 : `cat-3`/`cat-4` ΔL* 0,3 |
| Web : bandeaux `*-doux` peu distincts en gris | confirmé | L* de 92,4 à 95,3 ; sans conséquence grâce à l'intitulé |
| Web : impression, fonds retirés et contours | confirmé | bon choix ; j'ajoute le gaspillage de pages (m8) |
| Web : polices locales en `@font-face` | confirmé | le web est le seul support fidèle |
| Web : page sombre longue | confirmé | sans gravité |
| Office : or clair en aplat, « boue » | trouvé seul, confirmé | B2 |
| Office : point d'accent invisible sur la couverture | trouvé seul, confirmé | 1,19:1 ; tuile à 2,82:1 sur le fond, que le `LISEZMOI` ne relève pas |
| Office : thème fondé sur le clair seulement | trouvé seul, confirmé | A4 suffit, sans thème sombre complet |
| Office : `cat-1`/`cat-6` et `cat-4`/`cat-5` voisines sans étiquette | confirmé | je l'étends : six séries en légende seule violent la règle des quatre séries |
| Office : six accents seulement | non trouvé seul, confirmé | m7 |
| Office : légende du rapport sur « Revue », titre centré, « 10 » chevauché | confirmé en partie | légende confirmée ; le zéro barré est le dessin d'Atkinson Hyperlegible, pas un chevauchement |
| Office : bandeau d'alerte sans icône | confirmé | contraire au principe 2 ; à corriger dans le gabarit |
| Office : empattements dans Word | trouvé seul, confirmé | B2, jugé bloquant |
| README : mermaid sombre sur la page claire | trouvé seul, confirmé | I7 |
| README : choix des badges (`alerte-texte`, `texte-attenue`) | confirmé | bons choix ; j'ajoute l'étiquette à 1,05:1 en sombre (m4) |
| README : badges imités en local | confirmé | limite de méthode |
| README : `<img>` de repli sombre | confirmé | je recommande le repli clair (A8) |
| README : sous-titre en Sora 600 un peu lourd | confirmé | Sora 400 ou Atkinson, si le poids du fichier le permet |
| README : aperçu social vide à droite | trouvé seul, confirmé | m5 |
| README : rendu HTML imité, pas GitHub réel | confirmé | à vérifier sur GitHub après fusion |

## 5. Ce qui marche, à garder

- La palette de rôles : `Échecs : 0`, tous les textes au-dessus de 4,5:1, les marques non textuelles à 3:1 (seule exception : `trait`, I3).
- Le bouton principal neutre (`bouton`, 17,82:1 en clair, 15,72:1 en sombre). C'est un vrai parti pris, et il tient à l'impression (contour épais).
- Les pastilles avec icône, libellé et contour à l'impression.
- Le pictogramme, le point or et le filet or sur le web, le README et l'aperçu social. C'est la signature à étendre.
- La structure en jetons et générateur : chaque défaut ci-dessus se corrige à un seul endroit.
