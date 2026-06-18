"""
BESOIN 4 — PRÉDICTION DE LA PUISSANCE NOMINALE
Script de prédiction utilisant les modèles pré-entraînés.

Encodage des variables catégorielles :
  - OneHotEncoder pour `implantation` (onehot_implantation_b4.pkl)
  - OneHotEncoder pour `condition_acces` (onehot_acces_b4.pkl)
  - OneHotEncoder pour `type_tarif` (onehot_tarif_b4.pkl)
  - OneHotEncoder pour `raccordement` (onehot_raccordement_b4.pkl)
  Cohérent avec B3 — évite d'imposer un ordre arbitraire sur du nominal.

`operateur` (240 valeurs distinctes dans les données) est trop large pour un OneHot :
encodé par sa probabilité historique par catégorie de puissance, lissée vers la moyenne
globale (`encodage_operateur_b4.pkl`). Un opérateur jamais vu retombe sur cette moyenne.

`gratuit` a été retiré (importance quasi nulle dans le modèle entraîné) au profit de
`type_tarif`, `reservation`, `raccordement` et `operateur`, qui apportent un signal plus fort.

Sélection du modèle :
  Le modèle final a été sélectionné sur CV F1-macro (GridSearchCV cv=5, train only).
  Le score test sert uniquement à l'évaluation finale.

Usage :
    python main.py

Ou via import :
    from main import predire_puissance
    resultat = predire_puissance("Voirie", 2, False, False, True, True, True, "Accès libre", "kwh", "Direct", "izivia")
"""

import sys
import warnings
warnings.filterwarnings('ignore', category=UserWarning)
try:
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings('ignore', category=InconsistentVersionWarning)
except ImportError:
    pass

import numpy as np
import pandas as pd
import joblib
import os


# ─────────────────────────────────────────────────────────
#  Chemin vers les fichiers pkl (modifiable si besoin)
# ─────────────────────────────────────────────────────────
PKL_DIR = '.'


def charger_modeles():
    """
    Charge tous les modèles et encodeurs nécessaires depuis les fichiers .pkl.
    Lève une erreur claire si un fichier est manquant.
    """
    fichiers = {
        'scaler':              os.path.join(PKL_DIR, 'scaler_pretraitement_b4.pkl'),
        'modele':              os.path.join(PKL_DIR, 'modele_classification_b4.pkl'),
        'ohe_implantation':    os.path.join(PKL_DIR, 'onehot_implantation_b4.pkl'),
        'ohe_acces':           os.path.join(PKL_DIR, 'onehot_acces_b4.pkl'),
        'ohe_tarif':           os.path.join(PKL_DIR, 'onehot_tarif_b4.pkl'),
        'ohe_raccordement':    os.path.join(PKL_DIR, 'onehot_raccordement_b4.pkl'),
        'encodage_operateur':  os.path.join(PKL_DIR, 'encodage_operateur_b4.pkl'),
        'features':            os.path.join(PKL_DIR, 'features_b4.pkl'),
    }

    modeles = {}
    for nom, chemin in fichiers.items():
        if not os.path.exists(chemin):
            print(f"Erreur : fichier introuvable → {chemin}")
            print("Assurez-vous d'avoir exécuté le notebook principal avant d'utiliser ce script.")
            sys.exit(1)
        modeles[nom] = joblib.load(chemin)

    return modeles


def to_bool(val):
    """Convertit une valeur booléenne sous diverses formes en 0 ou 1."""
    return 1 if str(val).strip().upper() in ['TRUE', '1', 'OUI', 'YES'] else 0


def predire_puissance(implantation, nb_pdc, prise_ccs, prise_chademo,
                      prise_type2, prise_ef, reservation, condition_acces, type_tarif,
                      raccordement, operateur):
    """
    Prédit la catégorie de puissance nominale d'une borne de recharge.

    Paramètres
    ----------
    implantation    : str   — Type d'implantation (ex: "Voirie", "Parking privé à usage public")
    nb_pdc          : int   — Nombre de points de charge
    prise_ccs       : bool  — Présence d'une prise CCS
    prise_chademo   : bool  — Présence d'une prise CHAdeMO
    prise_type2     : bool  — Présence d'une prise Type 2
    prise_ef        : bool  — Présence d'une prise EF (domestique)
    reservation     : bool  — Borne réservable ou non
    condition_acces : str   — Condition d'accès (ex: "Accès libre", "Accès réservé")
    type_tarif      : str   — Type de tarification (ex: "kwh", "temps", "gratuit", "composite", "inconnu")
    raccordement    : str   — Type de raccordement électrique (ex: "Direct", "Indirect", "inconnu")
    operateur       : str   — Nom de l'opérateur/réseau (ex: "Tesla", "IZIVIA") — inconnu accepté

    Retour
    ------
    str — Catégorie prédite parmi :
          "Lente (<= 7.4 kW)"
          "Normale (7.4 - 22 kW)"
          "Acceleree (22 - 50 kW)"
          "Rapide (50 - 150 kW)"
          "Ultra-rapide (> 150 kW)"
    """

    m = charger_modeles()
    scaler           = m['scaler']
    modele           = m['modele']
    ohe_implantation = m['ohe_implantation']
    ohe_acces        = m['ohe_acces']
    ohe_tarif        = m['ohe_tarif']
    ohe_raccordement = m['ohe_raccordement']
    enc_operateur    = m['encodage_operateur']   # {'table': proba par classe, 'prior': moyenne globale, 'ordre': classes}
    features         = m['features']   # liste ordonnée des colonnes attendues par le modèle

    # ── Encodage des booléens ──
    ccs_num     = to_bool(prise_ccs)
    chademo_num = to_bool(prise_chademo)
    t2_num      = to_bool(prise_type2)
    ef_num      = to_bool(prise_ef)
    resa_num    = to_bool(reservation)

    # ── OHE implantation ──
    impl_str = str(implantation).strip()
    impl_df  = pd.DataFrame([[impl_str]], columns=['implantation'])
    impl_encoded = ohe_implantation.transform(impl_df)   # handle_unknown='ignore' → zeros si inconnu
    impl_cols = [f'implantation_{c}' for c in ohe_implantation.categories_[0]]
    if impl_str not in ohe_implantation.categories_[0]:
        print(f"  [Avertissement] Implantation inconnue : '{impl_str}' → vecteur zéro utilisé.")

    # ── OHE condition_acces ──
    acces_str = str(condition_acces).strip()
    acces_df  = pd.DataFrame([[acces_str]], columns=['condition_acces'])
    acces_encoded = ohe_acces.transform(acces_df)
    acces_cols = [f'acces_{c}' for c in ohe_acces.categories_[0]]
    if acces_str not in ohe_acces.categories_[0]:
        print(f"  [Avertissement] Condition d'accès inconnue : '{acces_str}' → vecteur zéro utilisé.")

    # ── OHE type_tarif ──
    tarif_str = str(type_tarif).strip().lower()
    tarif_df  = pd.DataFrame([[tarif_str]], columns=['type_tarif'])
    tarif_encoded = ohe_tarif.transform(tarif_df)
    tarif_cols = [f'tarif_{c}' for c in ohe_tarif.categories_[0]]
    if tarif_str not in ohe_tarif.categories_[0]:
        print(f"  [Avertissement] Type de tarif inconnu : '{tarif_str}' → vecteur zéro utilisé.")

    # ── OHE raccordement ──
    raccordement_str = str(raccordement).strip()
    raccordement_df  = pd.DataFrame([[raccordement_str]], columns=['raccordement'])
    raccordement_encoded = ohe_raccordement.transform(raccordement_df)
    raccordement_cols = [f'raccordement_{c}' for c in ohe_raccordement.categories_[0]]
    if raccordement_str not in ohe_raccordement.categories_[0]:
        print(f"  [Avertissement] Raccordement inconnu : '{raccordement_str}' → vecteur zéro utilisé.")

    # ── Encodage cible operateur (proba par classe, lissee, sauvegardee a l'entrainement) ──
    operateur_str = str(operateur).strip().lower()
    table_operateur = enc_operateur['table']
    prior_global    = enc_operateur['prior']
    ordre_classes   = enc_operateur['ordre']
    if operateur_str in table_operateur.index:
        proba_operateur = table_operateur.loc[operateur_str, ordre_classes].values
    else:
        proba_operateur = prior_global[ordre_classes].values
        print(f"  [Avertissement] Opérateur inconnu : '{operateur_str}' → moyenne globale utilisée.")
    operateur_cols = [f'operateur_proba_{c}' for c in ordre_classes]

    # ── Colonnes booléennes/numériques ──
    bool_num = pd.DataFrame(
        [[int(nb_pdc), ccs_num, chademo_num, t2_num, ef_num, resa_num]],
        columns=['nb_pdc', 'prise_ccs', 'prise_chademo', 'prise_type2', 'prise_ef', 'reservation']
    )

    # ── Assemblage dans l'ordre exact de l'entraînement ──
    df_impl         = pd.DataFrame(impl_encoded,  columns=impl_cols)
    df_acces        = pd.DataFrame(acces_encoded, columns=acces_cols)
    df_tarif        = pd.DataFrame(tarif_encoded, columns=tarif_cols)
    df_raccordement = pd.DataFrame(raccordement_encoded, columns=raccordement_cols)
    df_operateur    = pd.DataFrame([proba_operateur], columns=operateur_cols)
    donnee_borne = pd.concat([bool_num, df_impl, df_acces, df_tarif, df_raccordement, df_operateur], axis=1)

    # Réordonner selon features sauvegardées (robustesse)
    donnee_borne = donnee_borne.reindex(columns=features, fill_value=0)

    # ── Normalisation et prédiction ──
    donnee_scaled = scaler.transform(donnee_borne.astype(float))
    prediction    = modele.predict(donnee_scaled)

    return prediction[0]


def demander_valeur(message, type_attendu=str, valeurs_possibles=None):
    """Saisie interactive d'une valeur, avec validation de type/choix."""
    while True:
        saisie = input(message).strip()
        if valeurs_possibles and saisie.upper() not in [v.upper() for v in valeurs_possibles]:
            print(f"  Valeur invalide. Choix possibles : {valeurs_possibles}")
            continue
        try:
            return type_attendu(saisie)
        except ValueError:
            print(f"  Veuillez entrer une valeur de type {type_attendu.__name__}.")


# ─────────────────────────────────────────────────────────
#  Saisie interactive des spécificités d'une borne
# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  SCRIPT DE PRÉDICTION — BESOIN 4 (Puissance Nominale)')
    print('=' * 60)
    print("Veuillez entrer les caractéristiques de la borne :\n")

    implantation = demander_valeur("Type d'implantation : ", str)
    nb_pdc = demander_valeur("Nombre de points de charge : ", int)
    prise_ccs = demander_valeur("Présence d'une prise CCS ? (True/False) : ", str, ["True", "False"])
    prise_chademo = demander_valeur("Présence d'une prise CHAdeMO ? (True/False) : ", str, ["True", "False"])
    prise_type2 = demander_valeur("Présence d'une prise Type 2 ? (True/False) : ", str, ["True", "False"])
    prise_ef = demander_valeur("Présence d'une prise domestique EF ? (True/False) : ", str, ["True", "False"])
    reservation = demander_valeur("Borne réservable ? (True/False) : ", str, ["True", "False"])
    condition_acces = demander_valeur("Condition d'accès : ", str)
    type_tarif = demander_valeur(
        "Type de tarification (composite/gratuit/inconnu/kwh/temps) : ", str,
        ["composite", "gratuit", "inconnu", "kwh", "temps"]
    )
    raccordement = demander_valeur("Type de raccordement (Direct/Indirect/inconnu) : ", str)
    operateur = demander_valeur("Opérateur/réseau (ex: Tesla, IZIVIA, inconnu) : ", str)

    try:
        resultat = predire_puissance(
            implantation=implantation,
            nb_pdc=nb_pdc,
            prise_ccs=prise_ccs,
            prise_chademo=prise_chademo,
            prise_type2=prise_type2,
            prise_ef=prise_ef,
            reservation=reservation,
            condition_acces=condition_acces,
            type_tarif=type_tarif,
            raccordement=raccordement,
            operateur=operateur
        )
        print(f'\n  Puissance nominale prédite : {resultat}')
    except SystemExit:
        print('  → Modèles non trouvés. Exécutez le notebook d\'abord.')

    print('\n' + '=' * 60)
    print('  Fin du script de prédiction.')
    print('=' * 60)