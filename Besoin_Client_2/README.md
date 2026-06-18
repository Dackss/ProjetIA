# Besoin Client 2

Sectorisation intelligente des bornes de recharge (IRVE) et visualisation sur carte interactive.

## Structure des fichiers

| Fichier | Role |
|---|---|
| `main.ipynb` | Notebook d'analyse : justification des variables et de l'algorithme, calcul des metriques (Silhouette, Calinski-Harabasz, Davies-Bouldin, inertie/elbow), discussion des resultats, entrainement et sauvegarde des modeles K-Means (K=5, 6 et 7). |
| `main.py` | Script de production : charge un modele pre-entraine (jamais de reentrainement) pour predire le cluster d'une nouvelle borne saisie et genere la carte interactive complete. |
| `export_IA.csv` | Donnees source IRVE utilisees par le notebook et le script. |
| `kmeans_irve_model.pkl` | Modele par defaut (K choisi via `k_choisi` dans le notebook), charge a l'execution sans reentrainement. |
| `kmeans_irve_model_k5.pkl` / `_k6.pkl` / `_k7.pkl` | Un modele K-Means pre-entraine par valeur de K, generes par `main.ipynb`. `main.py --k` charge directement le fichier correspondant. |

## Prerequis

- Python 3.x installe
- Le fichier `export_IA.csv` present dans ce meme dossier (`Besoin_Client_2/`)
- Les modeles `.pkl` deja entraines (generes par `main.ipynb`) : `kmeans_irve_model.pkl`
  pour l'usage par defaut, et `kmeans_irve_model_k5/6/7.pkl` pour l'option `--k`

## Execution

1. Se placer dans ce dossier avant de lancer le script :

   ```
   cd Besoin_Client_2
   python main.py
   ```

2. Au premier lancement, le script installe automatiquement les dependances
   (pandas, numpy, matplotlib, seaborn, folium, scikit-learn, joblib, geopy) via pip.
   Pour sauter cette etape sur les lancements suivants :

   ```
   python main.py --skip-install
   ```

3. Si ni `--adresse` ni `--lat`/`--lon` ne sont fournis, le script demande de
   maniere interactive une adresse/ville (geocodee automatiquement via
   Nominatim/OpenStreetMap, necessite internet) ou, si laissee vide, des
   coordonnees lat/lon brutes (ex : `48.8566` / `2.3522`).

## Options disponibles

| Option | Description |
|---|---|
| `--adresse <texte>` | Adresse ou ville de la borne (ex: `"10 rue de Rivoli, Paris"`), geocodee automatiquement. Prioritaire sur `--lat`/`--lon` si fournie. |
| `--lat <valeur>` | Latitude de la borne saisie (demandee si absente et `--adresse` non fourni) |
| `--lon <valeur>` | Longitude de la borne saisie (demandee si absente et `--adresse` non fourni) |
| `--csv <chemin>` | Chemin du fichier CSV source (defaut : `export_IA.csv`) |
| `--model <chemin>` | Chemin du modele KMeans pre-entraine a charger (ignore si `--k` est fourni, defaut : `kmeans_irve_model.pkl`) |
| `--k {5,6,7}` | Charge le modele pre-entraine pour ce K (`kmeans_irve_model_k<K>.pkl`). Ne reentraine jamais. |
| `--output <dossier>` | Dossier de sortie pour la carte generee (defaut : `output`) |
| `--skip-install` | Ne pas reinstaller les dependances |

Exemple (modele par defaut) :

```
python main.py --lat 48.8566 --lon 2.3522 --output output --skip-install
```

Exemple (choix du nombre de clusters parmi les modeles pre-entraines) :

```
python main.py --lat 48.8566 --lon 2.3522 --k 7 --skip-install
```

## Resultats generes (dans le dossier `output/`)

- `carte_clusters_borne_recherchee.html` — Carte interactive : toutes les bornes colorees par cluster (un calque par cluster, sans regroupement visuel), plus le point saisi par l'utilisateur (marqueur etoile noire). Chaque borne a un popup (commune/implantation/puissance au clic) et une legende fixe (coin bas-gauche) resume chaque cluster : effectif, part du total, position moyenne.

Le notebook `main.ipynb` genere en plus, dans le meme dossier `output/` :

- `carte_clusters_irve.html` — Carte de clustering sur l'ensemble du jeu de donnees, une couleur distincte par cluster.
- `metriques_clustering.png` — Graphique comparatif des scores Silhouette, Calinski-Harabasz et Davies-Bouldin selon K.
- `elbow_inertie.png` — Courbe d'inertie (methode du coude), complement pour situer le nombre de clusters optimal.
- `repartition_clusters.png` — Repartition du nombre de bornes par cluster pour le K choisi.

Les modeles entraines (`kmeans_irve_model.pkl`, `kmeans_irve_model_k5/6/7.pkl`)
sont sauvegardes a la racine de `Besoin_Client_2/`, pas dans `output/`.

## Justifications techniques

### Choix des variables

Seules `latitude` / `longitude` sont utilisees : le besoin est une sectorisation
purement geographique des bornes, independante de leurs autres caracteristiques
(puissance, operateur, type d'implantation...). `dropna` est applique sur ces
deux colonnes uniquement, une borne sans coordonnees etant inutilisable pour
le clustering comme pour la carte.

### Choix de l'algorithme : K-Means

K-Means place K centroides, assigne chaque borne au plus proche, recalcule les
centroides comme moyenne des bornes assignees, et repete jusqu'a convergence
(minimisation de l'inertie). Choisi face aux alternatives
([scikit-learn clustering](https://scikit-learn.org/stable/modules/clustering.html))
car rapide sur ~139 000 points et produit des zones compactes de taille
comparable, adaptees a une sectorisation operationnelle. DBSCAN est ecarte
(les bornes IRVE sont denses en ville et tres clairsemees en zone rurale, ce
qui produirait un unique cluster urbain geant) ; le clustering hierarchique
est ecarte pour sa complexite quadratique, inutilisable sur ce volume.

### Choix des metriques et discussion des resultats

Silhouette, Calinski-Harabasz et Davies-Bouldin sont calcules pour K dans
{2, 3, 4, 5, 6, 7, 12}, complementes par la courbe d'inertie (elbow). Sur les
donnees IRVE : le Silhouette progresse jusqu'a K=7 (creux a K=6), Calinski-Harabasz
augmente avec K sans etre decisif seul (il favorise structurellement plus de
clusters), Davies-Bouldin est minimal a K=5, et le coude de l'inertie se situe
autour de K=5. L'ensemble converge vers la plage 5-7 comme meilleur compromis,
d'ou la restriction du choix final a ces trois valeurs (detail dans
`main.ipynb`, section "Discussion des resultats").

### Visualisation sur carte

Bibliotheque : Folium. Les tuiles CartoDB Positron sont utilisees a la place
d'OpenStreetMap pour eviter les erreurs reseau (403 Forbidden) et offrir une
meilleure lisibilite des clusters. Chaque cluster est rendu dans son propre
`FeatureGroup`, sans `MarkerCluster` : volontairement, les points ne sont pas
regroupes par proximite geographique afin de garder une couleur distincte et
lisible pour chaque cluster (contrairement a la carte du Besoin Client 1, qui
regroupe les marqueurs par zone).

**Ajouts pour l'experience utilisateur :** popup (commune/implantation/puissance)
sur chaque borne au lieu d'un point muet ; legende HTML fixe resumant chaque
cluster (effectif, % du total, position moyenne) — plus parlant qu'un simple
"Cluster 0/1/2..." dans le `LayerControl` ; saisie par adresse/ville (geocodee
via `geopy`/Nominatim) en plus de la saisie lat/lon brute, pour un usage non
technique.

### Script de production

Le script `main.py` charge toujours un modele via `joblib.load()` — il ne
reentraine jamais de modele a l'execution, conformement au cahier des charges.
`--k` ne fait que selectionner quel fichier `.pkl` pre-entraine charger parmi
ceux generes par `main.ipynb`.
