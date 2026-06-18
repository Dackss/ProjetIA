# Interface graphique unifiée (PySide6) — design

## Objectif

Réunir les 4 besoins (`Besoin_Client_1` à `4`) dans une seule application desktop, simple, pour la démo/rendu du projet. Pas de déploiement, pas de robustesse production — juste un point d'entrée unique qui montre les 4 résultats sans naviguer entre scripts/notebooks.

## Stack et emplacement

- **PySide6** (+ `PySide6-WebEngine` pour l'affichage des cartes Folium).
- Nouveau dossier `Interface_Graphique/` à la racine du repo.
- L'appli **importe** les fonctions existantes de chaque `Besoin_Client_X/main.py` (`predire_implantation`, `predire_puissance`, `generer_carte_implantation`, `generer_carte_complete`, etc.) — aucune duplication de logique métier/ML.
- Les fonctions `installer_dependances()` de chaque besoin ne sont jamais appelées par l'appli ; `Interface_Graphique/requirements.txt` consolide toutes les dépendances (pandas, numpy, joblib, scikit-learn, folium, geopy, PySide6, PySide6-WebEngine).

## Structure du code

```
Interface_Graphique/
├── main.py                    # Point d'entree, QApplication + MainWindow
├── main_window.py             # QMainWindow avec QTabWidget (4 onglets)
├── chdir_utils.py             # Context manager `with chdir(dossier):` pour les chemins relatifs des .pkl
├── onglets/
│   ├── onglet_b1.py            # Cartes implantation/chaleur
│   ├── onglet_b2.py            # Clustering geographique
│   ├── onglet_b3.py            # Prediction implantation
│   └── onglet_b4.py            # Prediction puissance
├── requirements.txt
└── README.md
```

`main.py` ajoute la racine du repo à `sys.path` pour pouvoir faire `from Besoin_Client_3.main import predire_implantation` (namespace packages implicites Python 3, pas besoin de `__init__.py`).

## Problème d'intégration : chemins relatifs des `.pkl`

B3/B4 chargent leurs modèles avec des chemins relatifs au répertoire courant (`joblib.load('scaler_pretraitement_b3.pkl')`). Sans précaution, un appel depuis `Interface_Graphique/` échoue (`FileNotFoundError` → le code existant fait `sys.exit(1)`, ce qui tuerait l'appli GUI).

**Solution** : `chdir_utils.py` fournit un context manager qui change le cwd vers le dossier du besoin concerné juste pour la durée de l'appel, puis restaure le cwd précédent (try/finally). Pas de modification du code existant des besoins.

```python
from chdir_utils import chdir
with chdir("Besoin_Client_3"):
    resultat = predire_implantation(...)
```

Contrainte : ce changement de cwd n'est pas thread-safe si deux besoins s'exécutent en parallèle dans des threads différents au même moment (cwd est un état process global). Dans cette appli, un seul calcul lourd (B1 ou B2) tourne à la fois dans un `QThread` ; les prédictions B3/B4 sont synchrones et rapides. Donc pas de vrai risque de concurrence dans ce périmètre — à documenter en commentaire dans `chdir_utils.py` pour éviter une régression future si quelqu'un paralléllise.

## Fenêtre principale

`QMainWindow` + `QTabWidget` central, 4 onglets : "B1 — Cartes", "B2 — Clustering", "B3 — Implantation", "B4 — Puissance". Chaque onglet est une classe `QWidget` indépendante, instanciée une fois au démarrage (pas de lazy-loading des onglets eux-mêmes — seuls les calculs lourds, déclenchés par bouton, sont différés).

## Onglet B1 — Cartes implantation

- Bouton "Générer les cartes".
- `QComboBox` pour choisir entre "Carte filtrable" et "Carte de chaleur" une fois générées.
- `QWebEngineView` affiche le HTML correspondant (`setUrl(QUrl.fromLocalFile(...))`).
- Génération (`charger_donnees` → `nettoyer_donnees` → `encoder_implantation` → `generer_carte_implantation` + `generer_carte_chaleur`) dans un `QThread` avec `QProgressBar` indéterminé (barre "occupé", pas de pourcentage réel car la durée n'est pas prévisible précisément).
- Réutilise l'échantillonnage déjà en place (8000 marqueurs/groupe max) — pas de changement de comportement, juste l'intégration GUI.

## Onglet B2 — Clustering géographique

- `QLineEdit` adresse (texte libre) **ou** deux `QDoubleSpinBox` lat/lon (l'un des deux groupes suffit ; adresse prioritaire si remplie, même logique que `main.py --adresse`).
- `QComboBox` K ∈ {5, 6, 7} (défaut : modèle `kmeans_irve_model.pkl`).
- Bouton "Générer la carte" → `QThread` (géocodage réseau + génération carte, durée variable) + `QProgressBar` indéterminé + message d'erreur clair si géocodage échoue (adresse introuvable / pas d'internet) sans crasher l'appli.
- Résultat dans un `QWebEngineView`.

**Correction par rapport à la première version de ce spec** : `generer_carte_complete` de B2 n'a **pas** d'échantillonnage existant (contrairement à B1) — elle itère les ~139 000 lignes à chaque appel (~1-2 min observé). Avant de l'utiliser dans la GUI, on ajoute un paramètre `plafond_par_groupe=8000` à `Besoin_Client_2/main.py::generer_carte_complete`, même logique que B1 (échantillon aléatoire par cluster, seed fixe, au-delà du plafond). C'est une amélioration du script B2 lui-même, pas un hack GUI-only — bénéficie aussi à qui lance `main.py` en CLI.

## Onglet B3 — Prédiction implantation

Formulaire mappé 1:1 sur les paramètres de `predire_implantation` :

| Champ | Widget |
|---|---|
| Puissance (kW) | `QDoubleSpinBox` |
| Nb points de charge | `QSpinBox` |
| Latitude / Longitude | `QDoubleSpinBox` ×2 |
| Gratuit, deux_roues, prise_ccs, prise_type2, prise_chademo, prise_ef, paiement_acte, paiement_cb, paiement_autre | `QCheckBox` ×9 |
| Type de tarification | `QComboBox` (composite/gratuit/inconnu/kwh/temps) |

Bouton "Prédire" → appel synchrone (rapide, pas de thread) dans `chdir("Besoin_Client_3")` → résultat affiché dans un `QLabel` en gros caractères.

## Onglet B4 — Prédiction puissance

Formulaire mappé 1:1 sur `predire_puissance` :

| Champ | Widget |
|---|---|
| Implantation | `QComboBox` (5 valeurs connues) |
| Nb points de charge | `QSpinBox` |
| prise_ccs, prise_chademo, prise_type2, prise_ef, reservation | `QCheckBox` ×5 |
| Condition d'accès | `QComboBox` (Accès libre / Accès réservé) |
| Type de tarification | `QComboBox` (composite/gratuit/inconnu/kwh/temps) |
| Raccordement | `QComboBox` (Direct/Indirect/inconnu) |
| Opérateur | `QLineEdit` texte libre (le modèle gère le fallback si inconnu) |

Bouton "Prédire" → appel synchrone dans `chdir("Besoin_Client_4")` → résultat dans un `QLabel`.

## Gestion des erreurs

- Si un fichier `.pkl` manque (besoin pas encore "généré" via son notebook) : message `QMessageBox.warning` clair ("Modèles introuvables pour ce besoin — exécutez d'abord `Besoin_Client_X/main.ipynb`"), pas de crash.
- Géocodage B2 sans réseau : message d'erreur dans l'UI, pas d'exception non gérée.

## Hors scope (explicitement exclu)

- Pas de packaging/exécutable (`.exe`/`.app`) — lancement via `python Interface_Graphique/main.py`.
- Pas de tests automatisés pour cette GUI (cohérent avec le reste du projet, qui n'en a pas non plus).
- Pas de persistance des résultats/historique des prédictions.
- Pas de retraining depuis l'interface — chaque onglet charge uniquement des modèles pré-entraînés, jamais de ré-entraînement (cohérent avec la contrainte déjà appliquée à tous les `main.py`).
