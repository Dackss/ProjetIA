# Besoin Client 2

Sectorisation intelligente des bornes de recharge (IRVE) et visualisation sur carte interactive.

## Structure des fichiers

| Fichier | Role |
|---|---|
| `main.ipynb` | Notebook d'analyse : entrainement du modele K-Means, calcul des metriques (Silhouette, Calinski-Harabasz, Davies-Bouldin) et choix du nombre de clusters (5, 6 ou 7). |
| `script.py` | Script de production : charge le modele pre-entraine pour predire le cluster d'une nouvelle borne saisie et genere la carte interactive complete. |
| `export_IA.csv` | Donnees source IRVE utilisees par le notebook et le script. |
| `kmeans_irve_model.pkl` | Modele de clustering entraine et serialise (charge a l'execution, jamais reentraine). |

## Prerequis

- Python 3.x installe
- Le fichier `export_IA.csv` present dans ce meme dossier (`Besoin_Client_2/`)
- Le modele `kmeans_irve_model.pkl` deja entraine (genere par `main.ipynb`),
  sauf si vous lancez `script.py` avec `--k` (qui entraine un modele a la
  volee sans avoir besoin du `.pkl`)

## Execution

1. Se placer dans ce dossier avant de lancer le script :

   ```
   cd Besoin_Client_2
   python script.py
   ```

2. Au premier lancement, le script installe automatiquement les dependances
   (pandas, numpy, matplotlib, seaborn, folium, scikit-learn, joblib) via pip.
   Pour sauter cette etape sur les lancements suivants :

   ```
   python script.py --skip-install
   ```

3. Si `--lat`/`--lon` ne sont pas fournis, le script les demande de maniere
   interactive (ex : `48.8566` / `2.3522`).

## Options disponibles

| Option | Description |
|---|---|
| `--lat <valeur>` | Latitude de la borne saisie (demandee si absente) |
| `--lon <valeur>` | Longitude de la borne saisie (demandee si absente) |
| `--csv <chemin>` | Chemin du fichier CSV source (defaut : `export_IA.csv`) |
| `--model <chemin>` | Chemin du modele KMeans entraine (defaut : `kmeans_irve_model.pkl`) |
| `--k {5,6,7}` | Nombre de clusters a utiliser. Si fourni, reentraine un modele a la volee avec cette valeur au lieu de charger `--model`. |
| `--output <dossier>` | Dossier de sortie pour la carte generee (defaut : `output`) |
| `--skip-install` | Ne pas reinstaller les dependances |

Exemple (modele pre-entraine) :

```
python script.py --lat 48.8566 --lon 2.3522 --output output --skip-install
```

Exemple (choix du nombre de clusters) :

```
python script.py --lat 48.8566 --lon 2.3522 --k 7 --skip-install
```

## Resultats generes (dans le dossier `output/`)

- `carte_finale.html` — Carte interactive : toutes les bornes colorees par cluster (un calque par cluster, sans regroupement visuel), plus le point saisi par l'utilisateur (marqueur etoile noire).

Le notebook `main.ipynb` genere en plus, dans le meme dossier `output/` :

- `carte_clusters_irve.html` — Carte de clustering sur l'ensemble du jeu de donnees, une couleur distincte par cluster.
- `metriques_clustering.png` — Graphique comparatif des scores Silhouette, Calinski-Harabasz et Davies-Bouldin selon K.

Le modele entraine (`kmeans_irve_model.pkl`) est sauvegarde a la racine de
`Besoin_Client_2/`, pas dans `output/`.

## Justifications techniques

### Apprentissage non supervise

Algorithme choisi : K-Means. Il regroupe les points geographiques
(latitude/longitude) en zones compactes, ce qui convient a une sectorisation
operationnelle. Le tableau de metriques (Silhouette, Calinski-Harabasz,
Davies-Bouldin) est calcule pour K dans {2, 3, 4, 5, 6, 7, 12} afin de guider
le choix, mais le nombre de clusters final est fixe par l'utilisateur parmi
5, 6 ou 7 — la variable `k_choisi` dans `main.ipynb`, ou l'option `--k` de
`script.py`.

### Visualisation sur carte

Bibliotheque : Folium. Les tuiles CartoDB Positron sont utilisees a la place
d'OpenStreetMap pour eviter les erreurs reseau (403 Forbidden) et offrir une
meilleure lisibilite des clusters. Chaque cluster est rendu dans son propre
`FeatureGroup`, sans `MarkerCluster` : volontairement, les points ne sont pas
regroupes par proximite geographique afin de garder une couleur distincte et
lisible pour chaque cluster (contrairement a la carte du Besoin Client 1, qui
regroupe les marqueurs par zone).

### Script de production

Par defaut, le script `script.py` charge le modele via `joblib.load()` — aucun
entrainement (`fit`) n'est realise a l'execution, ce qui garantit une
prediction instantanee. Si `--k` est fourni (5, 6 ou 7), un nouveau modele
KMeans est entraine a la volee avec ce nombre de clusters, sans toucher au
fichier `kmeans_irve_model.pkl`.
