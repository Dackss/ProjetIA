
# SCRIPT AUTONOME DE PRÉDICTION D'IMPLANTATION (LIVRABLE PROJET)


import sys
import pandas as pd
import joblib

def predire_implantation(puissance, nb_pdc, gratuit, prise_ccs, prise_type2):
    
    try:
        # CHARGEMENT DES MODELES PREALABLEMENT ENREGISTRES (Modèle à 5 variables)
        scaler = joblib.load('scaler_pretraitement_b3.pkl')
        modele = joblib.load('modele_classification_b3.pkl')
        
        # Encodage propre de l'entrée utilisateur (comme lors de l'entraînement)
        g_num = 1 if str(gratuit).upper() in ['TRUE', '1', 'OUI'] else 0
        ccs_num = 1 if str(prise_ccs).upper() in ['TRUE', '1', 'OUI'] else 0
        t2_num = 1 if str(prise_type2).upper() in ['TRUE', '1', 'OUI'] else 0
        
        # Organisation des données au format DataFrame exact attendu par le scaler
        colonnes = ['puissance', 'nb_pdc', 'gratuit', 'prise_ccs', 'prise_type2']
        donnee_borne = pd.DataFrame([[float(puissance), int(nb_pdc), g_num, ccs_num, t2_num]], columns=colonnes)
        
        # Application du prétraitement (Normalisation)
        donnee_borne_scaled = scaler.transform(donnee_borne)
        
        # Calcul de la prédiction finale
        prediction = modele.predict(donnee_borne_scaled)
        
        return prediction[0]

    except FileNotFoundError as e:
        print(f"Erreur : Les fichiers de sauvegarde (.pkl) sont introuvables dans le dossier actuel.")
        print("Veuillez vérifier que 'scaler_pretraitement_b3.pkl' et 'modele_classification_b3.pkl' existent.")
        sys.exit(1)

# Zone de test du script 
if __name__ == "__main__":
    print("--- SCRIPT DE TEST DE PREDICTION (BESOIN 3) ---")
    
    # Simulation d'une borne type "Autoroute" (Forte puissance, payante, combo CCS)
    resultat = predire_implantation(
        puissance=150.0, 
        nb_pdc=4, 
        gratuit="False", 
        prise_ccs="True", 
        prise_type2="False"
    )
    
    print("\n[Caractéristiques entrées] : 150kW, 4 PDC, Payante, Avec prise CCS")
    print(f"[Résultat de l'IA]        : Implantation prédite -> **{resultat}**\n")

    
    
    print("\n[Test A.")
    resultat_A = predire_implantation(
        puissance=7.0,       # Très faible puissance (recharge lente)
        nb_pdc=2,            # Seulement 2 points de charge
        gratuit="True",      # Gratuite !
        prise_ccs="False",   # Pas de charge rapide
        prise_type2="True"   # Prise de ville standard
    )
    print("\n[Caractéristiques entrées] : 7kW, 2 PDC, gratuite, Avec prise type2")
    print(f"[Résultat de l'IA]        : Implantation prédite -> **{resultat_A}**\n")
    
    # PROFIL B 
    print("\n[Test B]")
    resultat_B = predire_implantation(
        puissance=350.0,     # Puissance maximale du marché (Ultra-Fast)
        nb_pdc=12,           # Très grand nombre de bornes alignées
        gratuit="False",     # Très payant
        prise_ccs="True",      # Combo CCS obligatoire pour l'autoroute
        prise_type2="False"
    )
    print("\n[Caractéristiques entrées] : 350kW, 12 PDC, payante, Avec prise type2")
    print(f"[Résultat de l'IA]        : Implantation prédite -> **{resultat_B}**\n")