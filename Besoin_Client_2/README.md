# Projet IRVE — Visualisation et Sectorisation Géographique

> **Besoin Client 2** : Sectorisation intelligente des bornes de recharge (IRVE) et visualisation sur carte interactive.

---

## 📁 Structure des fichiers

| Fichier                 | Rôle                                                                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `main.ipynb`            | Notebook d'analyse : entraînement du modèle K-Means, calcul des métriques (Silhouette, Calinski-Harabasz, Davies-Bouldin) et validation du nombre optimal de clusters. |
| `script.py`             | Script de production : charge le modèle pré-entraîné pour prédire le cluster d'une nouvelle borne saisie par l'utilisateur et génère la carte interactive complète.    |
| `kmeans_irve_model.pkl` | Modèle de clustering entraîné et sérialisé (chargé à l'exécution, jamais réentraîné).                                                                                  |

---

## 🛠️ Guide d'utilisation

### Prérequis

Installez les dépendances nécessaires :

```bash
pip install pandas scikit-learn folium joblib
```

### Lancer le script de production

1. Placez votre fichier de données `export_IA.csv` dans le répertoire `../data/`  
   _(ou ajustez le chemin dans `script.py`)._

2. Exécutez le script depuis votre terminal :

```bash
python script.py
```

3. Un fichier `carte_finale.html` est généré. Ouvrez-le dans n'importe quel navigateur pour visualiser :
   - toutes les bornes colorées par cluster,
   - le point saisi par l'utilisateur (marqué d'une **étoile noire**).

---

## 📋 Justifications techniques

### Apprentissage non supervisé

**Algorithme choisi : K-Means**  
K-Means regroupe les points géographiques (latitude/longitude) en zones compactes, ce qui est idéal pour une sectorisation opérationnelle. Le nombre de clusters _K_ est déterminé dans `main.ipynb` à l'aide des métriques Silhouette et Calinski-Harabasz, afin de garantir la meilleure qualité de regroupement possible.

### Visualisation sur carte

**Bibliothèque : Folium**  
Les tuiles **CartoDB Positron** sont utilisées à la place d'OpenStreetMap afin d'éviter les erreurs réseau (403 Forbidden). Elles offrent également une meilleure lisibilité pour la lecture des clusters.

### Script de production (conformité cahier des charges)

Le script `script.py` charge le modèle via `joblib.load()` — aucun entraînement (`fit`) n'est réalisé à l'exécution, ce qui garantit une prédiction instantanée et conforme aux exigences.

---

_Projet réalisé dans le cadre de la formation **ISEN — Big Data / IA / Web 2026**._
