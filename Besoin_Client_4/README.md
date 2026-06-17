# Modèle de Prédiction de la Puissance Nominale (IRVE)

## Objectif

Ce projet vise à développer un modèle d'intelligence artificielle permettant de prédire la **catégorie de puissance nominale** d'une borne de recharge électrique (IRVE) en fonction de ses caractéristiques techniques (types de prises, lieu d'implantation, etc.).

Le problème est traité comme une **classification multi-classes** basée sur les standards industriels :

- **Lente** (≤ 7.4 kW)
- **Normale** (7.4 - 22 kW)
- **Accélérée** (22 - 50 kW)
- **Rapide** (50 - 150 kW)
- **Ultra-rapide** (> 150 kW)

---

## Architecture du Projet

Le projet est composé de deux éléments principaux :

1. `main.ipynb` : Notebook Jupyter contenant toute la chaîne de traitement (Data Cleaning, Feature Engineering, Entraînement, Évaluation, Export).
2. `main.py` : Script Python autonome pour effectuer des prédictions en production en utilisant les modèles exportés.

### Structure des dossiers

- `/data` : Dossier contenant le fichier source `export_IA.csv`.
- `/fichier_pkl` : Contient les modèles entraînés (`.pkl`), les encodeurs (`LabelEncoder`), le `StandardScaler` et la liste des features.
- `/figures` : Graphiques générés lors de l'analyse exploratoire (EDA) et de l'évaluation du modèle.

---

## Installation et Utilisation

### 1. Prérequis

Assurez-vous d'avoir installé les bibliothèques nécessaires :

```bash
pip install pandas numpy scikit-learn joblib matplotlib seaborn
```
