# Thierry (Assister par L'IA)
"""Script de production : prédit le cluster d'une borne saisie et génère la carte complète."""
import argparse
import subprocess
import sys

REQUIREMENTS = ["pandas", "numpy", "matplotlib", "seaborn", "folium", "scikit-learn", "joblib", "geopy"]


def installer_dependances():
    subprocess.check_call([sys.executable, "-m", "pip", "install", *REQUIREMENTS])


def geocoder_adresse(adresse):
    """Convertit une adresse/ville en (latitude, longitude) via Nominatim (OpenStreetMap).
    Necessite une connexion internet. Retourne None si l'adresse n'est pas trouvee."""
    from geopy.geocoders import Nominatim

    geolocaliseur = Nominatim(user_agent="projet_ia_besoin_client_2")
    resultat = geolocaliseur.geocode(adresse, timeout=10)
    if resultat is None:
        return None
    return resultat.latitude, resultat.longitude


def construire_legende(df_irve, couleurs):
    """Boite HTML fixe (coin bas-gauche) resumant chaque cluster : couleur, effectif,
    part du total et position moyenne. Plus parlant qu'un simple "Cluster 0/1/2..."
    dans le LayerControl, qui ne dit rien du contenu reel du cluster."""
    import folium

    total = len(df_irve)
    lignes = ""
    for cluster_id, sous_df in df_irve.groupby('cluster'):
        couleur = couleurs[int(cluster_id) % len(couleurs)]
        effectif = len(sous_df)
        part = effectif / total * 100
        lat_moy = sous_df['latitude'].mean()
        lon_moy = sous_df['longitude'].mean()
        lignes += (
            f'<div style="margin-bottom:4px;">'
            f'<span style="display:inline-block;width:12px;height:12px;background:{couleur};'
            f'border-radius:50%;margin-right:6px;"></span>'
            f'Cluster {int(cluster_id)} — {effectif:,} bornes ({part:.1f}%)<br>'
            f'<span style="margin-left:18px;color:#555;">zone moyenne : {lat_moy:.2f}, {lon_moy:.2f}</span>'
            f'</div>'
        )

    return folium.Element(f"""
    <div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
                background: white; padding: 10px 14px; border: 1px solid #999;
                border-radius: 6px; font-size: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.3);
                max-width: 260px;">
        <b>Légende des clusters</b><br><br>
        {lignes}
    </div>
    """)


def generer_carte_complete(lat_saisie, lon_saisie, chemin_csv, chemin_model, chemin_sortie):
    import joblib
    import pandas as pd
    import folium

    df_irve = pd.read_csv(chemin_csv, low_memory=False)
    colonnes_popup = [c for c in ['commune', 'implantation', 'puissance'] if c in df_irve.columns]
    df_irve = df_irve.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

    # Le modèle est toujours chargé depuis un fichier pré-entraîné (jamais de
    # réentraînement ici) : main.ipynb sauvegarde un modèle par valeur de K
    # (kmeans_irve_model_k5.pkl, _k6.pkl, _k7.pkl) ainsi qu'un modèle par
    # défaut (kmeans_irve_model.pkl).
    model = joblib.load(chemin_model)

    # Prédire le cluster de TOUTES les bornes
    df_irve['cluster'] = model.predict(df_irve[['latitude', 'longitude']])

    # Créer la carte
    carte = folium.Map(location=[lat_saisie, lon_saisie], zoom_start=10, tiles="CartoDB positron", prefer_canvas=True)

    # Un FeatureGroup par cluster (sans MarkerCluster) : chaque borne garde sa
    # couleur de cluster visible individuellement, sans regroupement par
    # proximité géographique qui mélangerait les couleurs entre clusters.
    couleurs = ['red', 'blue', 'green', 'purple', 'orange']
    cluster_groups = {}
    for cluster_id in sorted(df_irve['cluster'].unique()):
        cluster_groups[cluster_id] = folium.FeatureGroup(name=f"Cluster {cluster_id}").add_to(carte)

    for _, row in df_irve.iterrows():
        cluster_id = int(row['cluster'])
        texte_popup = "<br>".join(str(row[c]) for c in colonnes_popup) if colonnes_popup else f"Cluster {cluster_id}"
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=2,
            color=couleurs[cluster_id % len(couleurs)],
            fill=True,
            fill_color=couleurs[cluster_id % len(couleurs)],
            fill_opacity=0.8,
            popup=texte_popup,
        ).add_to(cluster_groups[cluster_id])

    folium.LayerControl(collapsed=False).add_to(carte)
    carte.get_root().html.add_child(construire_legende(df_irve, couleurs))

    # Ajouter le marqueur spécial pour le point saisi par l'utilisateur
    folium.Marker(
        [lat_saisie, lon_saisie],
        popup="Point saisi",
        icon=folium.Icon(color='black', icon='star')
    ).add_to(carte)

    carte.save(chemin_sortie)
    print(f"Carte générée avec succès : '{chemin_sortie}'")


def parse_args():
    parser = argparse.ArgumentParser(description="Génère la carte de clustering IRVE pour une borne saisie.")
    parser.add_argument("--adresse", help="Adresse ou ville de la borne (ex: '10 rue de Rivoli, Paris'). Géocodée automatiquement, nécessite internet.")
    parser.add_argument("--lat", type=float, help="Latitude de la borne (ex: 48.8566). Demandée si absente et --adresse non fourni.")
    parser.add_argument("--lon", type=float, help="Longitude de la borne (ex: 2.3522). Demandée si absente et --adresse non fourni.")
    parser.add_argument("--csv", default="export_IA.csv", help="Chemin du fichier CSV source.")
    parser.add_argument("--model", default="kmeans_irve_model.pkl", help="Chemin du modèle KMeans pré-entraîné à charger (ignoré si --k est fourni).")
    parser.add_argument("--k", type=int, choices=[5, 6, 7], help="Charge le modèle pré-entraîné pour ce K (kmeans_irve_model_k<K>.pkl), généré par main.ipynb. Ne réentraîne jamais.")
    parser.add_argument("--output", default="output", help="Dossier de sortie pour la carte générée.")
    parser.add_argument("--skip-install", action="store_true", help="Ne pas installer les dépendances avant exécution.")
    return parser.parse_args()


def main():
    import os

    args = parse_args()

    if not args.skip_install:
        installer_dependances()

    lat = args.lat
    lon = args.lon
    adresse = args.adresse

    if lat is None or lon is None:
        if adresse is None:
            print("--- Saisie de la position de la borne ---")
            adresse = input("Adresse/ville (laisser vide pour saisir lat/lon directement) : ").strip() or None

        if adresse:
            print(f"Géocodage de '{adresse}'...")
            try:
                resultat = geocoder_adresse(adresse)
            except Exception as exc:
                print(f"Erreur de géocodage ({exc}). Vérifiez votre connexion internet.")
                resultat = None
            if resultat is None:
                print("Adresse introuvable. Saisie manuelle des coordonnées :")
            else:
                lat, lon = resultat
                print(f"  -> latitude={lat:.4f}, longitude={lon:.4f}")

        if lat is None or lon is None:
            try:
                lat = lat if lat is not None else float(input("Entrez la latitude (ex: 48.8566) : "))
                lon = lon if lon is not None else float(input("Entrez la longitude (ex: 2.3522) : "))
            except ValueError:
                print("Erreur : Veuillez entrer des nombres valides.")
                return

    os.makedirs(args.output, exist_ok=True)
    chemin_sortie = os.path.join(args.output, "carte_clusters_borne_recherchee.html")

    chemin_model = f"kmeans_irve_model_k{args.k}.pkl" if args.k is not None else args.model

    generer_carte_complete(lat, lon, args.csv, chemin_model, chemin_sortie)


if __name__ == "__main__":
    main()
