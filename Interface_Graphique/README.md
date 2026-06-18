# Interface Graphique — Projet IA Bornes IRVE

Application desktop PySide6 qui regroupe les 4 besoins dans une seule fenêtre à onglets.
N'entraîne jamais de modèle : charge uniquement les `.pkl` déjà générés par chaque
`Besoin_Client_X/main.ipynb`.

## Prérequis

- Python 3.x
- Les 4 dossiers `Besoin_Client_1` à `4` doivent déjà contenir leurs fichiers `.pkl`
  (générés en exécutant chaque `main.ipynb` une fois).
- `Besoin_Client_1/export_IA.csv` et `Besoin_Client_2/export_IA.csv` présents (utilisés
  par les onglets B1/B2 pour générer les cartes).

## Installation

```bash
pip install -r Interface_Graphique/requirements.txt
```

## Lancement

Depuis la racine du repo :

```bash
python3 Interface_Graphique/main.py
```

## Onglets

- **B1 — Cartes** : génère la carte filtrable par implantation et la carte de chaleur
  (échantillonnées à 8000 marqueurs/groupe pour rester fluides).
- **B2 — Clustering** : saisie d'une adresse (géocodée via Nominatim, nécessite internet)
  ou de coordonnées lat/lon brutes, choix de K (5/6/7), génère la carte de clustering
  avec légende et popups.
- **B3 — Implantation** : formulaire de caractéristiques de borne → prédit le type
  d'implantation.
- **B4 — Puissance** : formulaire de caractéristiques de borne → prédit la catégorie
  de puissance nominale.

## Si un onglet affiche une erreur "Modèles introuvables"

Le `.pkl` correspondant n'a pas encore été généré — ouvrir le notebook du besoin
concerné (`Besoin_Client_X/main.ipynb`) et l'exécuter entièrement une fois.
