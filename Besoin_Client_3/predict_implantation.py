
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
        
        #  Si une colonne manque , on l'ajoute à 0
        for col in scaler.feature_names_in_:
            if col not in donnee_borne.columns:
                donnee_borne[col] = 0
                
        #  Alignement dynamique et STRICT selon l'ordre du fit de ton modèle
        donnee_borne = donnee_borne[scaler.feature_names_in_]
        
        # 5.  Normalisation
        donnee_borne_scaled = scaler.transform(donnee_borne)
        
        # 6. Calcul de la prédiction finale
        prediction = modele.predict(donnee_borne_scaled)
        
        return prediction[0]

    except FileNotFoundError:
        print(f"Erreur : Les fichiers .pkl sont introuvables dans le dossier 'fichier_pkl/'.")
        sys.exit(1)


# test de code 

if __name__ == "__main__":
    print("--- SCRIPT DE TEST DE PREDICTION GLOBAL (BESOIN 3 & 4) ---")
    
    # Test 1 : Borne de transit ultra-rapide (CCS)
    print("\n[Test 1 : Hub Autoroute Ultra-Rapide]")
    res_1 = predire_implantation(puissance=350.0, nb_pdc=8, gratuit=False, prise_ccs=True, prise_type2=False, prise_chademo=False)
    print(f"-> Implantation prédite : **{res_1}**")
    
    # Test 2 : Borne accélérée de ville (Type 2)
    print("\n[Test 2 : Borne standard de Centre-Ville]")
    res_2 = predire_implantation(puissance=22.0, nb_pdc=2, gratuit=True, prise_ccs=False, prise_type2=True, prise_chademo=False)
    print(f"-> Implantation prédite : **{res_2}**")
    
    # Test 3 : Borne mixte ancienne génération (CHAdeMO + CCS + T2)
    print("\n[Test 3 : Borne Tri-Standard DC/AC]")
    res_3 = predire_implantation(puissance=50.0, nb_pdc=3, gratuit=False, prise_ccs=True, prise_type2=True, prise_chademo=True)
    print(f"-> Implantation prédite : **{res_3}**")

    