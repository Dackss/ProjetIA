import sys
import pandas as pd
import joblib


def predire_implantation(puissance, nb_pdc, latitude, longitude, gratuit, deux_roues,
                          prise_ccs, prise_type2, prise_chademo, prise_ef,
                          paiement_acte, paiement_cb, paiement_autre, type_tarif):

    try:
        # CHARGEMENT DES MODELES PREALABLEMENT ENREGISTRES
        scaler = joblib.load('scaler_pretraitement_b3.pkl')
        ohe = joblib.load('onehot_type_tarif_b3.pkl')
        colonnes_features_modele = joblib.load('feature_order_b3.pkl')
        modele = joblib.load('modele_classification_b3.pkl')

        # Encodage des booléens
        mapping = {'TRUE': 1, 'FALSE': 0, '1': 1, '0': 0, 'OUI': 1, 'NON': 0, True: 1, False: 0}

        colonnes_numeriques = ['puissance', 'nb_pdc', 'latitude', 'longitude']
        colonnes_booleennes = ['gratuit', 'deux_roues', 'prise_ccs', 'prise_type2', 'prise_chademo', 'prise_ef',
                                'paiement_acte', 'paiement_cb', 'paiement_autre']

        donnees_brutes = {
            'puissance': float(puissance),
            'nb_pdc': int(nb_pdc),
            'latitude': float(latitude),
            'longitude': float(longitude),
            'gratuit': mapping.get(str(gratuit).upper(), 0),
            'deux_roues': mapping.get(str(deux_roues).upper(), 0),
            'prise_ccs': mapping.get(str(prise_ccs).upper(), 0),
            'prise_type2': mapping.get(str(prise_type2).upper(), 0),
            'prise_chademo': mapping.get(str(prise_chademo).upper(), 0),
            'prise_ef': mapping.get(str(prise_ef).upper(), 0),
            'paiement_acte': mapping.get(str(paiement_acte).upper(), 0),
            'paiement_cb': mapping.get(str(paiement_cb).upper(), 0),
            'paiement_autre': mapping.get(str(paiement_autre).upper(), 0),
        }

        donnee_borne = pd.DataFrame([donnees_brutes])

        # Normalisation des colonnes numeriques/booleennes
        donnee_borne_scaled = scaler.transform(donnee_borne[colonnes_numeriques + colonnes_booleennes])

        # Encodage OneHot du type de tarif
        donnee_tarif = pd.DataFrame([{'type_tarif': type_tarif}])
        donnee_tarif_ohe = ohe.transform(donnee_tarif)

        # Concatenation dans le meme ordre que lors de l'entrainement
        import numpy as np
        donnee_finale = np.hstack([donnee_borne_scaled, donnee_tarif_ohe])

        prediction = modele.predict(donnee_finale)

        return prediction[0]

    except FileNotFoundError:
        print("Erreur : Les fichiers .pkl sont introuvables dans ce dossier.")
        sys.exit(1)


def demander_valeur(message, type_attendu=str, valeurs_possibles=None):
    while True:
        saisie = input(message).strip()
        if valeurs_possibles and saisie.upper() not in [v.upper() for v in valeurs_possibles]:
            print(f"  Valeur invalide. Choix possibles : {valeurs_possibles}")
            continue
        try:
            return type_attendu(saisie)
        except ValueError:
            print(f"  Veuillez entrer une valeur de type {type_attendu.__name__}.")


#  SAISIE INTERACTIVE DES VALEURS PAR L'UTILISATEUR

if __name__ == "__main__":

    print("   PRÉDICTION DU TYPE D'IMPLANTATION D'UNE BORNE")

    print("Veuillez entrer les caractéristiques de la borne :\n")

    puissance = demander_valeur("Puissance nominale (en kW) : ", float)
    nb_pdc = demander_valeur("Nombre de points de charge : ", int)
    latitude = demander_valeur("Latitude : ", float)
    longitude = demander_valeur("Longitude : ", float)
    gratuit = demander_valeur("Borne gratuite ? (True/False) : ", str, ["True", "False"])
    deux_roues = demander_valeur("Borne accessible aux deux-roues ? (True/False) : ", str, ["True", "False"])
    prise_ccs = demander_valeur("Présence d'une prise CCS ? (True/False) : ", str, ["True", "False"])
    prise_type2 = demander_valeur("Présence d'une prise Type 2 ? (True/False) : ", str, ["True", "False"])
    prise_chademo = demander_valeur("Présence d'une prise CHAdeMO ? (True/False) : ", str, ["True", "False"])
    prise_ef = demander_valeur("Présence d'une prise domestique EF ? (True/False) : ", str, ["True", "False"])
    paiement_acte = demander_valeur("Paiement à l'acte possible ? (True/False) : ", str, ["True", "False"])
    paiement_cb = demander_valeur("Paiement par carte bancaire possible ? (True/False) : ", str, ["True", "False"])
    paiement_autre = demander_valeur("Autre moyen de paiement possible ? (True/False) : ", str, ["True", "False"])
    type_tarif = demander_valeur(
        "Type de tarification (composite/gratuit/inconnu/kwh/temps) : ", str,
        ["composite", "gratuit", "inconnu", "kwh", "temps"]
    )

    resultat = predire_implantation(
        puissance=puissance,
        nb_pdc=nb_pdc,
        latitude=latitude,
        longitude=longitude,
        gratuit=gratuit,
        deux_roues=deux_roues,
        prise_ccs=prise_ccs,
        prise_type2=prise_type2,
        prise_chademo=prise_chademo,
        prise_ef=prise_ef,
        paiement_acte=paiement_acte,
        paiement_cb=paiement_cb,
        paiement_autre=paiement_autre,
        type_tarif=type_tarif
    )

    print(f"  Implantation prédite : {resultat}")
    print("=" * 60)
