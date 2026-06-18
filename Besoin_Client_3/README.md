# Besoin Client 3 – Prédiction du type d'implantation

## Description

Ce script prédit le type d'implantation d'une borne de recharge electrique a partir de ses caracteristiques (puissance, nombre de points de charge, localisation, types de prises, types de paiement, tarification).

Le notebook compare 4 algorithmes (Régression Logistique, Random Forest, Gradient Boosting, K-Nearest Neighbors) via GridSearchCV et retient automatiquement le meilleur sur le score de validation croisée : Random Forest (cv_score 0.9615, accuracy test 0.97).

Le modèle final est chargé depuis les fichiers `.pkl` situés à la racine du dossier.

### Limite à connaître

Le score de 0.97 est optimiste : il vient d'un split train/test aléatoire, et une même station (3.3 points de charge en moyenne) peut se retrouver à la fois en train et en test. Le modèle reconnaît alors parfois une station déjà vue plutôt que de vraiment généraliser. En refaisant le split en regroupant les lignes par station (section 6.2 du notebook), l'accuracy retombe à 0.81 — c'est le chiffre le plus honnête pour une borne réellement nouvelle. Les variables `paiement_*` ajoutent aussi un peu de raisonnement circulaire (elles reflètent plus le contexte du lieu que des causes indépendantes).

---

## Contenu du dossier

```
Besoin_Client_3/
├── main.ipynb                        # Notebook experimental
├── main.py                           # Script de prediction interactif
├── README.md                         # Ce fichier
├── export_IA.csv                     # Base de donnees IRVE
├── scaler_pretraitement_b3.pkl       # StandardScaler sauvegarde
├── onehot_type_tarif_b3.pkl          # OneHotEncoder sauvegarde (type_tarif)
├── feature_order_b3.pkl              # Ordre des colonnes du modele
├── modele_classification_b3.pkl      # Modele de classification sauvegarde
└── output/
    ├── justification_puissance.png   # Boxplot puissance par implantation
    ├── proportion_prise_ccs.png      # Proportion de prise CCS par implantation
    ├── matrice_correlation.png       # Matrice de correlation des variables
    ├── feature_importance.png        # Importance des variables (modele retenu)
    ├── matrice_confusion.png         # Matrice de confusion du modele
    ├── rapport_classification.png    # Precision/rappel/f1 par classe
    ├── tp_fn_fp_par_classe.png       # Vrais/faux positifs et negatifs par classe
    └── comparaison_splits.png        # Accuracy split aleatoire vs split par station
```

---

## Utilisation

### 1. Générer les modèles

Exécuter le notebook `main.ipynb` en entier.
Cela génère les fichiers `scaler_pretraitement_b3.pkl`, `onehot_type_tarif_b3.pkl`, `feature_order_b3.pkl` et `modele_classification_b3.pkl` à la racine du dossier.

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
Latitude : 48.8566
Longitude : 2.3522
Borne gratuite ? (True/False) : False
Borne accessible aux deux-roues ? (True/False) : False
Présence d'une prise CCS ? (True/False) : True
Présence d'une prise Type 2 ? (True/False) : False
Présence d'une prise CHAdeMO ? (True/False) : False
Présence d'une prise domestique EF ? (True/False) : False
Paiement à l'acte possible ? (True/False) : True
Paiement par carte bancaire possible ? (True/False) : False
Autre moyen de paiement possible ? (True/False) : False
Type de tarification (composite/gratuit/inconnu/kwh/temps) : kwh

============================================================
  Implantation prédite : Parking privé à usage public
============================================================
```

---

## Paramètres demandés

| Paramètre | Type | Description |
|---|---|---|
| Puissance nominale | `float` | Puissance de la borne en kW |
| Nombre de points de charge | `int` | Nombre de PDC sur la borne |
| Latitude | `float` | Latitude GPS de la borne |
| Longitude | `float` | Longitude GPS de la borne |
| Borne gratuite | `True` / `False` | Accès gratuit ou payant |
| Deux-roues | `True` / `False` | Borne accessible aux deux-roues |
| Prise CCS | `True` / `False` | Présence d'une prise combo CCS |
| Prise Type 2 | `True` / `False` | Présence d'une prise Type 2 |
| Prise CHAdeMO | `True` / `False` | Présence d'une prise CHAdeMO |
| Prise EF | `True` / `False` | Présence d'une prise domestique (EF) |
| Paiement à l'acte | `True` / `False` | Paiement à l'acte disponible |
| Paiement CB | `True` / `False` | Paiement par carte bancaire disponible |
| Paiement autre | `True` / `False` | Autre moyen de paiement disponible |
| Type de tarification | `composite`/`gratuit`/`inconnu`/`kwh`/`temps` | Catégorie de tarif appliquée |

---

## Importer la fonction dans un autre fichier

```python
from main import predire_implantation

resultat = predire_implantation(
    puissance=150.0,
    nb_pdc=4,
    latitude=48.8566,
    longitude=2.3522,
    gratuit=False,
    deux_roues=False,
    prise_ccs=True,
    prise_type2=False,
    prise_chademo=False,
    prise_ef=False,
    paiement_acte=True,
    paiement_cb=False,
    paiement_autre=False,
    type_tarif='kwh'
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
