# Thierry (Assister par L'IA)
import joblib
import pandas as pd
import folium

def generer_carte_complete(lat_saisie, lon_saisie):
    # 1. Charger le modèle et les données
    model = joblib.load("kmeans_irve_model.pkl")
    df_irve = pd.read_csv("../data/export_IA.csv")
    
    # 2. Prédire le cluster de TOUTES les bornes
    df_irve['cluster'] = model.predict(df_irve[['latitude', 'longitude']])
    
    # Créer la carte
    carte = folium.Map(location=[lat_saisie, lon_saisie], zoom_start=10, tiles="CartoDB positron", prefer_canvas=True)
    
    # Boucle : Ajouter TOUTES les bornes
    couleurs = ['red', 'blue', 'green', 'purple', 'orange']
    for _, row in df_irve.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=1,
            color=couleurs[int(row['cluster']) % len(couleurs)],
            fill=True
        ).add_to(carte)
        
    # Ajouter le marqueur spécial pour le point saisi par l'utilisateur
    folium.Marker(
        [lat_saisie, lon_saisie],
        popup="Point saisi",
        icon=folium.Icon(color='black', icon='star')
    ).add_to(carte)
    
    carte.save("carte_finale.html")

if __name__ == "__main__":
    print("--- Saisie des coordonnées de la borne ---")
    try:
        user_lat = float(input("Entrez la latitude (ex: 48.8566) : "))
        user_lon = float(input("Entrez la longitude (ex: 2.3522) : "))
        
        generer_carte_complete(user_lat, user_lon)
    except ValueError:
        print("Erreur : Veuillez entrer des nombres valides.")