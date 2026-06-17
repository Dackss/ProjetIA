import sys
import pandas as pd
import joblib


def predire_implantation(puissance, nb_pdc, gratuit, prise_ccs, prise_type2, prise_chademo):

    try:
        # CHARGEMENT DES MODELES PREALABLEMENT ENREGISTRES
        scaler = joblib.load('fichier_pkl/scaler_pretraitement_b3.pkl')
        modele = joblib.load('fichier_pkl/modele_classification_b3.pkl')

        # Encodage
        mapping = {'TRUE': 1, 'FALSE': 0, '1': 1, '0': 0, True: 1, False: 0}

        g_num = mapping.get(str(gratuit).upper(), 0)
        ccs_num = mapping.get(str(prise_ccs).upper(), 0)
        t2_num = mapping.get(str(prise_type2).upper(), 0)
        chademo_num = mapping.get(str(prise_chademo).upper(), 0)

        # intégralité des connecteurs du marché
        donnees_brutes = {
            'puissance': float(puissance),
            'nb_pdc': int(nb_pdc),
            'gratuit': g_num,
            'prise_ccs': ccs_num,
            'prise_type2': t2_num,
            'prise_chademo': chademo_num,
        }

        # Conversion en DataFrame
        donnee_borne = pd.DataFrame([donnees_brutes])

        # Si une colonne manque, on l'ajoute à 0
        for col in scaler.feature_names_in_:
            if col not in donnee_borne.columns:
                donnee_borne[col] = 0

        # Alignement dynamique et STRICT selon l'ordre du fit de ton modèle
        donnee_borne = donnee_borne[scaler.feature_names_in_]

        # Normalisation
        donnee_borne_scaled = scaler.transform(donnee_borne)

        # Calcul de la prédiction finale
        prediction = modele.predict(donnee_borne_scaled)

        return prediction[0]

    except FileNotFoundError:
        print("Erreur : Les fichiers .pkl sont introuvables dans le dossier 'fichier_pkl/'.")
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
    gratuit = demander_valeur("Borne gratuite ? (True/False) : ", str, ["True", "False"])
    prise_ccs = demander_valeur("Présence d'une prise CCS ? (True/False) : ", str, ["True", "False"])
    prise_type2 = demander_valeur("Présence d'une prise Type 2 ? (True/False) : ", str, ["True", "False"])
    prise_chademo = demander_valeur("Présence d'une prise CHAdeMO ? (True/False) : ", str, ["True", "False"])

    resultat = predire_implantation(
        puissance=puissance,
        nb_pdc=nb_pdc,
        gratuit=gratuit,
        prise_ccs=prise_ccs,
        prise_type2=prise_type2,
        prise_chademo=prise_chademo
    )

    print(f"  Implantation prédite : {resultat}")
    print("=" * 60)