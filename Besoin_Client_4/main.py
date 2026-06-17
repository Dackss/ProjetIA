"""
BESOIN 4 — PRÉDICTION DE LA PUISSANCE NOMINALE
Script de prédiction utilisant les modèles pré-entraînés.

Usage :
    python main.py

Ou via import :
    from main import predire_puissance
    resultat = predire_puissance("Voirie", 2, False, False, True, True, True, "Accès libre")
"""

import sys
import pandas as pd
import joblib
import os


# ─────────────────────────────────────────────────────────
#  Chemin vers les fichiers pkl (modifiable si besoin)
# ─────────────────────────────────────────────────────────
PKL_DIR = 'fichier_pkl'


def charger_modeles():
    """
    Charge tous les modèles et encodeurs nécessaires depuis les fichiers .pkl.
    Lève une erreur claire si un fichier est manquant.
    """
    fichiers = {
        'scaler':           os.path.join(PKL_DIR, 'scaler_pretraitement_b4.pkl'),
        'modele':           os.path.join(PKL_DIR, 'modele_classification_b4.pkl'),
        'le_implantation':  os.path.join(PKL_DIR, 'le_implantation_b4.pkl'),
        'le_acces':         os.path.join(PKL_DIR, 'le_acces_b4.pkl'),
        'features':         os.path.join(PKL_DIR, 'features_b4.pkl'),
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
                      prise_type2, prise_ef, gratuit, condition_acces):
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
    gratuit         : bool  — Borne gratuite ou non
    condition_acces : str   — Condition d'accès (ex: "Accès libre", "Accès réservé")

    Retour
    ------
    str — Catégorie prédite parmi :
          "Lente (<= 7.4 kW)"
          "Normale (7.4 - 22 kW)"
          "Acceleree (22 - 50 kW)"
          "Rapide (50 - 150 kW)"
          "Ultra-rapide (> 150 kW)"
    """

    # Chargement des modèles (pas de réentraînement)
    m = charger_modeles()
    scaler          = m['scaler']
    modele          = m['modele']
    le_implantation = m['le_implantation']
    le_acces        = m['le_acces']
    features        = m['features']

    # --- Encodage des booléens ---
    ccs_num     = to_bool(prise_ccs)
    chademo_num = to_bool(prise_chademo)
    t2_num      = to_bool(prise_type2)
    ef_num      = to_bool(prise_ef)
    g_num       = to_bool(gratuit)

    # --- Encodage implantation ---
    impl_str = str(implantation).strip()
    if impl_str in le_implantation.classes_:
        impl_num = int(le_implantation.transform([impl_str])[0])
    else:
        # Valeur inconnue : on utilise 0 (catégorie par défaut)
        impl_num = 0
        print(f"  [Avertissement] Implantation inconnue : '{impl_str}' → valeur par défaut utilisée.")

    # --- Encodage condition_acces ---
    acces_str = str(condition_acces).strip()
    if acces_str in le_acces.classes_:
        acces_num = int(le_acces.transform([acces_str])[0])
    else:
        acces_num = 0
        print(f"  [Avertissement] Condition d'accès inconnue : '{acces_str}' → valeur par défaut utilisée.")

    # --- Construction du DataFrame dans le même ordre que l'entraînement ---
    donnee_borne = pd.DataFrame(
        [[impl_num, int(nb_pdc), ccs_num, chademo_num, t2_num, ef_num, g_num, acces_num]],
        columns=features
    )

    # --- Normalisation et prédiction ---
    donnee_scaled = scaler.transform(donnee_borne)
    prediction    = modele.predict(donnee_scaled)

    return prediction[0]


# ─────────────────────────────────────────────────────────
#  Tests de démonstration
# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 60)
    print('  SCRIPT DE PRÉDICTION — BESOIN 4 (Puissance Nominale)')
    print('=' * 60)

    tests = [
        {
            'label': 'Station rapide dédiée avec CCS + CHAdeMO',
            'params': {
                'implantation':    'Station dédiée à la recharge rapide',
                'nb_pdc':          6,
                'prise_ccs':       True,
                'prise_chademo':   True,
                'prise_type2':     False,
                'prise_ef':        False,
                'gratuit':         False,
                'condition_acces': 'Accès réservé'
            },
            'attendu': 'Ultra-rapide ou Rapide'
        },
        {
            'label': 'Borne lente en voirie (gratuite)',
            'params': {
                'implantation':    'Voirie',
                'nb_pdc':          2,
                'prise_ccs':       False,
                'prise_chademo':   False,
                'prise_type2':     True,
                'prise_ef':        True,
                'gratuit':         True,
                'condition_acces': 'Accès libre'
            },
            'attendu': 'Lente ou Normale'
        },
        {
            'label': 'Parking privé — Type 2 uniquement',
            'params': {
                'implantation':    'Parking privé à usage public',
                'nb_pdc':          4,
                'prise_ccs':       False,
                'prise_chademo':   False,
                'prise_type2':     True,
                'prise_ef':        False,
                'gratuit':         False,
                'condition_acces': 'Accès réservé'
            },
            'attendu': 'Normale ou Accélérée'
        },
        {
            'label': 'Borne domestique — Prise EF seulement',
            'params': {
                'implantation':    'Voirie',
                'nb_pdc':          1,
                'prise_ccs':       False,
                'prise_chademo':   False,
                'prise_type2':     False,
                'prise_ef':        True,
                'gratuit':         True,
                'condition_acces': 'Accès libre'
            },
            'attendu': 'Lente (<= 7.4 kW)'
        },
    ]

    for i, test in enumerate(tests, 1):
        print(f'\n[Test {i}] {test["label"]}')
        print(f'  Attendu    : {test["attendu"]}')
        try:
            resultat = predire_puissance(**test['params'])
            print(f'  Prédiction : {resultat}')
        except SystemExit:
            print('  → Modèles non trouvés. Exécutez le notebook d\'abord.')
            break

    print('\n' + '=' * 60)
    print('  Fin du script de prédiction.')
    print('=' * 60)