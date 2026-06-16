
#  PREDICTION DE LA PUISSANCE NOMINALE


import sys
import pandas as pd
import joblib


def predire_puissance(implantation, nb_pdc, prise_ccs, prise_chademo,
                      prise_type2, prise_ef, gratuit, condition_acces):

    try:
        # CHARGEMENT DES MODELES  ENREGISTRES
        scaler          = joblib.load('fichier_pkl/scaler_pretraitement_b4.pkl')
        modele          = joblib.load('fichier_pkl/modele_classification_b4.pkl')
        le_implantation = joblib.load('fichier_pkl/le_implantation_b4.pkl')
        le_acces        = joblib.load('fichier_pkl/le_acces_b4.pkl')
        features        = joblib.load('fichier_pkl/features_b4.pkl')

    except FileNotFoundError:
        print("Erreur : fichiers .pkl introuvables.")
        sys.exit(1)

    # Encodage des booleens
    def to_bool(val):
        return 1 if str(val).upper() in ['TRUE', '1', 'OUI'] else 0

    ccs_num     = to_bool(prise_ccs)
    chademo_num = to_bool(prise_chademo)
    t2_num      = to_bool(prise_type2)
    ef_num      = to_bool(prise_ef)
    g_num       = to_bool(gratuit)

    # Encodage implantation
    impl_str = str(implantation).strip()
    if impl_str in le_implantation.classes_:
        impl_num = le_implantation.transform([impl_str])[0]
    else:
        impl_num = 0

    # Encodage condition_acces
    acces_str = str(condition_acces).strip()
    if acces_str in le_acces.classes_:
        acces_num = le_acces.transform([acces_str])[0]
    else:
        acces_num = 0

    # Construction du DataFrame dans le meme ordre que l'entrainement
    donnee_borne = pd.DataFrame([[impl_num, int(nb_pdc), ccs_num, chademo_num,
                                   t2_num, ef_num, g_num, acces_num]],
                                 columns=features)

    # Normalisation et prediction
    donnee_scaled = scaler.transform(donnee_borne)
    prediction    = modele.predict(donnee_scaled)

    return prediction[0]



if __name__ == "__main__":
    print(" SCRIPT DE TEST DE PREDICTION (BESOIN 4) \n")

    # Exemple 1 : 
    resultat = predire_puissance(
        implantation    = "Station dédiée à la recharge rapide",
        nb_pdc          = 6,
        prise_ccs       = "True",
        prise_chademo   = "True",
        prise_type2     = "False",
        prise_ef        = "False",
        gratuit         = "False",
        condition_acces = "Accès réservé"
    )
    print("[Caracteristiques] : Station dediee, 6 PDC, CCS + CHAdeMO, payante")
    print(f"[Prediction IA]    : Puissance predite -> **{resultat}**\n")

    # Exemple 2 : Borne lente en voirie
    resultat_A = predire_puissance(
        implantation    = "Voirie",
        nb_pdc          = 2,
        prise_ccs       = "False",
        prise_chademo   = "False",
        prise_type2     = "True",
        prise_ef        = "True",
        gratuit         = "True",
        condition_acces = "Accès libre"
    )
    print("[Caracteristiques] : Voirie, 2 PDC, Type2 + EF, gratuite")
    print(f"[Prediction IA]    : Puissance predite -> **{resultat_A}**\n")

    # Exemple 3 : Borne en parking prive
    resultat_B = predire_puissance(
        implantation    = "Parking privé à usage public",
        nb_pdc          = 4,
        prise_ccs       = "False",
        prise_chademo   = "False",
        prise_type2     = "True",
        prise_ef        = "False",
        gratuit         = "False",
        condition_acces = "Accès réservé"
    )
    print("[Caracteristiques] : Parking prive, 4 PDC, Type2, payante")
    print(f"[Prediction IA]    : Puissance predite -> **{resultat_B}**\n")