# Besoin Client 3 – Prédiction du type d'implantation

## Description

Ce script prédit le type d'implantation d'une borne de recharge electrique a partir de ses caracteristiques techniques (puissance, nombre de points de charge, types de prises, gratuite ou non).

Il utilise un modele de Regression Logistique pre-entraine, charge depuis les fichiers `.pkl` situes a la racine du dossier.

---

## Contenu du dossier

```
Besoin_Client_3/
├── main.ipynb                        # Notebook experimental
├── main.py                           # Script de prediction interactif
├── README.md                         # Ce fichier
├── export_IA.csv                     # Base de donnees IRVE
├── scaler_pretraitement_b3.pkl       # StandardScaler sauvegarde
├── modele_classification_b3.pkl      # Modele de classification sauvegarde
└── output/
    ├── justification_puissance.png   # Graphique de justification
    ├── proportion_prise_ccs.png      # Graphique de justification
    └── matrice_confusion.png         # Matrice de confusion du modele
```



## Utilisation

### 1. Générer les modèles

Exécuter le notebook `main.ipynb` en entier.
Cela génère les fichiers `scaler_pretraitement_b3.pkl` et `modele_classification_b3.pkl` à la racine du dossier.

> Le script `main.py` **charge** ces fichiers, il ne relance pas d'entraînement.

### 2. Lancer le script

```bash
python main.py
```

Le script demande à l'utilisateur de saisir les caractéristiques de la borne directement dans le terminal :

```
============================================================
   PRÉDICTION DU TYPE D'IMPLANTATION D'UNE BORNE
============================================================
Veuillez entrer les caractéristiques de la borne :

Puissance nominale (en kW) : 150
Nombre de points de charge : 4
Borne gratuite ? (True/False) : False
Présence d'une prise CCS ? (True/False) : True
Présence d'une prise Type 2 ? (True/False) : False
Présence d'une prise CHAdeMO ? (True/False) : False

============================================================
  Implantation prédite : Station dédiée à la recharge rapide
============================================================
```

---

## Paramètres demandés

| Paramètre | Type | Description |
|---|---|---|
| Puissance nominale | `float` | Puissance de la borne en kW |
| Nombre de points de charge | `int` | Nombre de PDC sur la borne |
| Borne gratuite | `True` / `False` | Accès gratuit ou payant |
| Prise CCS | `True` / `False` | Présence d'une prise combo CCS |
| Prise Type 2 | `True` / `False` | Présence d'une prise Type 2 |
| Prise CHAdeMO | `True` / `False` | Présence d'une prise CHAdeMO |

---

## Importer la fonction dans un autre fichier

```python
from main import predire_implantation

resultat = predire_implantation(
    puissance=150.0,
    nb_pdc=4,
    gratuit=False,
    prise_ccs=True,
    prise_type2=False,
    prise_chademo=False
)
print(resultat)
```

---

## Classes prédites possibles

- `Voirie`
- `Parking public`
- `Parking privé à usage public`
- `Parking privé réservé à la clientèle`
- `Station dédiée à la recharge rapide`