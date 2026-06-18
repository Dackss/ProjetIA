# Besoin Client 4 – Prédiction de la puissance nominale

## Description

Ce script prédit la **catégorie de puissance nominale** d'une borne de recharge électrique (IRVE) à partir de ses caractéristiques (implantation, nombre de points de charge, types de prises, réservation, condition d'accès, type de tarification, raccordement, opérateur).

Le problème est traité comme une **classification multi-classes** basée sur les standards industriels :

- **Lente** (≤ 7.4 kW)
- **Normale** (7.4 - 22 kW)
- **Accélérée** (22 - 50 kW)
- **Rapide** (50 - 150 kW)
- **Ultra-rapide** (> 150 kW)

Le notebook compare 4 algorithmes (Régression Logistique, Random Forest, Gradient Boosting, KNN) via GridSearchCV (cv=5, scoring `f1_macro`) et retient automatiquement le meilleur sur le score de validation croisée : **Random Forest**.

`class_weight: [None, 'balanced']` a été ajouté à la grille pour Régression Logistique et Random Forest (les seuls à le supporter nativement). La grille retient `class_weight=None` — le bagging de Random Forest absorbe déjà l'essentiel du déséquilibre des classes, la pondération n'apporte pas de gain ici.

Le modèle final est chargé depuis les fichiers `.pkl` situés à la racine du dossier.

### Score à retenir : split par station (section 8 du notebook)

**accuracy 0.8520 / F1-macro 0.8222** — calculé sur un split qui regroupe les lignes par `id_station` (`GroupShuffleSplit`), pour qu'aucune station ne se retrouve à la fois en train et en test. C'est le chiffre honnête, celui qui simule une borne réellement nouvelle.

Le notebook calcule aussi un split aléatoire classique (section 4.1/7), qui donne CV F1-macro 0.8409 et accuracy test 0.8745 — **mais ce chiffre est optimiste, à ne pas citer comme résultat du modèle.** Une même station a souvent plusieurs PDC quasi identiques, et le split aléatoire en met une partie en train et l'autre en test : le modèle reconnaît alors une station déjà vue plutôt que de généraliser. La vérification ci-dessous le confirme.

**Vérification concrète du mélange train/test :**

| Vérification | Split aléatoire (4.1) | Split par station (8) |
|---|---|---|
| Index communs train/test | 0 | 0 |
| Stations présentes dans train ET test | 14 768 / 17 706 stations test (83.4%) | 0 |
| Lignes test dont la station est déjà vue en train | 24 025 / 27 787 (86.5%) | 0 |
| Lignes test avec un doublon exact (mêmes features) en train | 27 565 / 27 787 (**99.2%**) | — |

Le split aléatoire n'est donc pas un vrai test out-of-sample : 99.2% des lignes test ont un jumeau quasi parfait en train (même station, mêmes prises/implantation/tarif — seul `id_pdc` change). Le score 0.8745 mesure surtout de la mémorisation. Le split par station (0 chevauchement vérifié) donne le seul score qui simule honnêtement une borne jamais vue.

### Lecture des matrices

**Corrélation** (features numériques/booléennes vs `puissance`, valeur continue) :

```
prise_ccs        0.75   ← forte, charge rapide DC
prise_chademo    0.02   ← quasi nulle en linéaire (mais utile au modèle via interaction, cf. feature_importance)
nb_pdc          -0.08   ← faible en linéaire (le modèle capte une relation non-linéaire que la corrélation rate)
reservation     -0.12   ← faible, cohérent avec le signal "modéré" observé en section 3
prise_ef        -0.35   ← modérée, prise domestique = puissance basse
prise_type2     -0.64   ← forte (inverse), charge AC lente/moyenne
```

**Matrice de confusion** (split aléatoire, 27 787 lignes test) :

```
                    Prédit →  Lente  Normale  Accélérée  Rapide  Ultra-rapide
Réel  Lente            4501      756         60       50            4
      Normale           545    11654         96       46           17
      Accélérée          37      338       3010      188          164
      Rapide              8       19        155     2075          471
      Ultra-rapide       12        7         68      446         3060
```

**FP/FN par classe (one-vs-rest)** :

| Classe | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|
| Lente | 4501 | 602 | 870 | 0.88 | 0.84 | 0.86 |
| Normale | 11654 | 1120 | 704 | 0.91 | 0.94 | 0.93 |
| Accélérée | 3010 | 379 | 727 | 0.89 | 0.81 | 0.84 |
| Rapide | 2075 | 730 | 653 | 0.74 | 0.76 | 0.75 |
| Ultra-rapide | 3060 | 656 | 533 | 0.82 | 0.85 | 0.84 |

Les erreurs se concentrent sur les paliers adjacents, jamais sur des paliers opposés : **Rapide ↔ Ultra-rapide** est la confusion la plus fréquente (471 + 446 = 917 lignes), suivie de **Lente ↔ Normale** (756 + 545 = 1301 lignes). Logique : une borne à la frontière entre deux paliers de puissance a souvent un profil de features ambigu (ex : 6 PDC avec CCS peut être Rapide ou Ultra-rapide selon le modèle exact de borne, une info qu'on n'a pas). `Rapide` reste la classe la plus difficile (F1 0.75, la plus faible) — c'est aussi la 3ᵉ plus petite classe (2728 lignes test sur 27787).

### Historique des améliorations

Score de départ : F1-macro 0.7163 / accuracy 0.7728 (split aléatoire, pas encore vérifié pour la fuite par station). Quatre pistes testées dans l'ordre :

1. **Nettoyage de `condition_acces`** : le CSV source contenait des variantes mal encodées (mojibake) de "Accès libre" / "Accès réservé" (`Accs libre`, `Acc¸s libre`, `AccĂ¨s libre`, ...), qui généraient des colonnes OneHot parasites. La fonction `normaliser_acces` (section 2.1) réconcilie ces variantes sur un mot-clé stable (`libre` / `serv`) avant l'encodage — la feature passe de 5 colonnes bruitées à 2 colonnes propres.
2. **`class_weight='balanced'`** : testé en grille, non retenu (pas de gain mesuré).
3. **`type_tarif` + `reservation` ajoutées, `gratuit` retirée** : `gratuit` avait une importance quasi nulle dans le modèle (0.0024, la plus faible de toutes) — retiré. `type_tarif` (tarif "temps" → 88% Normale, "kwh" → 22.5% Rapide) et `reservation` (sépare les bornes Rapide/Ultra-rapide du reste) ont pris sa place.
4. **`raccordement` + `operateur` ajoutées** : `raccordement` (Direct/Indirect) en OneHot classique, NaN (64% des lignes) gardé comme sa propre catégorie "inconnu" plutôt que supprimé. `operateur` (240 réseaux distincts dans les données, ex : Tesla, IZIVIA, Bouygues Energies & Services) est trop large pour un OneHot — encodé par sa **probabilité historique par catégorie de puissance**, calculée sur le train uniquement et lissée vers la moyenne globale (`m_lissage=50` lignes virtuelles) pour ne pas laisser un opérateur vu une seule fois imposer 100%/0%. C'est cette étape qui explique l'essentiel du gain : certains réseaux (Tesla, Ionity) standardisent presque exclusivement sur de l'ultra-rapide, d'autres sur du lent — un signal que les autres features ne capturaient pas.

### Limite à connaître

Le F1-macro honnête (0.82) reste légèrement inférieur à l'accuracy honnête (0.85) : les classes minoritaires (Accélérée, Rapide) restent un peu moins bien reconnues que les classes majoritaires, mais l'écart s'est nettement resserré par rapport à la version précédente (0.72 vs 0.77). `operateur` et `nb_pdc`/`prise_ccs` sont désormais les features les plus discriminantes (voir `feature_importance_b4.png`).

Un opérateur jamais vu au train (nouveau réseau) retombe sur la moyenne globale — comme une catégorie inconnue pour les OneHotEncoder. Le score peut légèrement baisser en production si beaucoup de nouveaux opérateurs apparaissent après l'entraînement.

---

## Contenu du dossier

```
Besoin_Client_4/
├── main.ipynb                            # Notebook expérimental
├── main.py                               # Script de prédiction interactif
├── README.md                             # Ce fichier
├── export_IA.csv                         # Base de données IRVE
├── scaler_pretraitement_b4.pkl           # StandardScaler sauvegardé
├── onehot_implantation_b4.pkl            # OneHotEncoder sauvegardé (implantation)
├── onehot_acces_b4.pkl                   # OneHotEncoder sauvegardé (condition_acces)
├── onehot_tarif_b4.pkl                   # OneHotEncoder sauvegardé (type_tarif)
├── onehot_raccordement_b4.pkl            # OneHotEncoder sauvegardé (raccordement)
├── encodage_operateur_b4.pkl             # Table de probabilités lissées par opérateur + moyenne globale
├── features_b4.pkl                       # Ordre des colonnes du modèle
├── modele_classification_b4.pkl          # Modèle de classification sauvegardé
└── output/
    ├── distribution_puissance.png        # Distribution des catégories de puissance
    ├── justification_features_prises_b4.png  # Lien types de prises ↔ puissance
    ├── correlation_features_b4.png       # Matrice de corrélation des variables numériques/booléennes
    ├── boxplot_nbpdc_b4.png               # Nombre de points de charge par catégorie de puissance
    ├── comparaison_algorithmes_b4.png    # Comparaison des 4 algorithmes (CV F1-macro / accuracy / F1)
    ├── rapport_classification_b4.png     # Précision/rappel/f1 par classe (modèle retenu)
    ├── matrice_confusion_b4.png          # Matrice de confusion du modèle
    ├── feature_importance_b4.png         # Importance des variables (modèle retenu)
    └── f1_par_classe_b4.png              # F1-score par classe (modèle retenu)
```

---

## Utilisation

### 1. Générer les modèles

Exécuter le notebook `main.ipynb` en entier.
Cela génère les fichiers `scaler_pretraitement_b4.pkl`, `onehot_implantation_b4.pkl`, `onehot_acces_b4.pkl`, `onehot_tarif_b4.pkl`, `onehot_raccordement_b4.pkl`, `encodage_operateur_b4.pkl`, `features_b4.pkl` et `modele_classification_b4.pkl` à la racine du dossier.

> Le script `main.py` **charge** ces fichiers, il ne relance pas d'entraînement.

### 2. Lancer le script

```bash
pip install pandas numpy scikit-learn joblib matplotlib seaborn
python main.py
```

Le script demande à l'utilisateur de saisir les caractéristiques de la borne directement dans le terminal :

```
============================================================
  SCRIPT DE PRÉDICTION — BESOIN 4 (Puissance Nominale)
============================================================
Veuillez entrer les caractéristiques de la borne :

Type d'implantation : Station dédiée à la recharge rapide
Nombre de points de charge : 6
Présence d'une prise CCS ? (True/False) : True
Présence d'une prise CHAdeMO ? (True/False) : True
Présence d'une prise Type 2 ? (True/False) : False
Présence d'une prise domestique EF ? (True/False) : False
Borne réservable ? (True/False) : False
Condition d'accès : Accès réservé
Type de tarification (composite/gratuit/inconnu/kwh/temps) : kwh
Type de raccordement (Direct/Indirect/inconnu) : Direct
Opérateur/réseau (ex: Tesla, IZIVIA, inconnu) : Tesla

  Puissance nominale prédite : Ultra-rapide (> 150 kW)

============================================================
  Fin du script de prédiction.
============================================================
```

---

## Paramètres demandés

| Paramètre | Type | Description |
|---|---|---|
| Type d'implantation | `str` | Lieu d'implantation (ex : Voirie, Parking public, Station dédiée à la recharge rapide) |
| Nombre de points de charge | `int` | Nombre de PDC sur la borne |
| Prise CCS | `True` / `False` | Présence d'une prise combo CCS |
| Prise CHAdeMO | `True` / `False` | Présence d'une prise CHAdeMO |
| Prise Type 2 | `True` / `False` | Présence d'une prise Type 2 |
| Prise EF | `True` / `False` | Présence d'une prise domestique (EF) |
| Borne réservable | `True` / `False` | Borne réservable à l'avance ou non |
| Condition d'accès | `str` | Condition d'accès (ex : Accès libre, Accès réservé) |
| Type de tarification | `composite`/`gratuit`/`inconnu`/`kwh`/`temps` | Catégorie de tarif appliquée |
| Type de raccordement | `str` | Raccordement électrique (ex : Direct, Indirect, inconnu) |
| Opérateur/réseau | `str` | Nom de l'opérateur (ex : Tesla, IZIVIA) — inconnu accepté, retombe sur la moyenne globale |

---

## Importer la fonction dans un autre fichier

```python
from main import predire_puissance

resultat = predire_puissance(
    implantation="Station dédiée à la recharge rapide",
    nb_pdc=6,
    prise_ccs=True,
    prise_chademo=True,
    prise_type2=False,
    prise_ef=False,
    reservation=False,
    condition_acces="Accès réservé",
    type_tarif="kwh",
    raccordement="Direct",
    operateur="Tesla"
)
print(resultat)
```

---

## Classes prédites possibles

- `Lente (<= 7.4 kW)`
- `Normale (7.4 - 22 kW)`
- `Acceleree (22 - 50 kW)`
- `Rapide (50 - 150 kW)`
- `Ultra-rapide (> 150 kW)`
