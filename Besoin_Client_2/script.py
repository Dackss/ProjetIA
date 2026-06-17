# Thierry (Assister par L'IA)
"""Script de production : prédit le cluster d'une borne saisie et génère la carte complète."""
import argparse
import subprocess
import sys

REQUIREMENTS = ["pandas", "numpy", "matplotlib", "seaborn", "folium", "scikit-learn", "joblib"]


def installer_dependances():
    subprocess.check_call([sys.executable, "-m", "pip", "install", *REQUIREMENTS])


def generer_carte_complete(lat_saisie, lon_saisie, chemin_csv, chemin_model, chemin_sortie, k=None):
    import joblib
    import pandas as pd
    import folium

    df_irve = pd.read_csv(chemin_csv)
    df_irve = df_irve.dropna(subset=["latitude", "longitude"]).reset_index(drop=True)

    if k is not None:
        # Nombre de clusters choisi par l'utilisateur : on réentraîne à la
        # demande plutôt que de réutiliser le modèle pré-entraîné figé.
        from sklearn.cluster import KMeans
        print(f"Entraînement d'un modèle KMeans avec K={k}...")
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        model.fit(df_irve[['latitude', 'longitude']])
    else:
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
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=2,
            color=couleurs[cluster_id % len(couleurs)],
            fill=True,
            fill_color=couleurs[cluster_id % len(couleurs)],
            fill_opacity=0.8,
        ).add_to(cluster_groups[cluster_id])

    folium.LayerControl(collapsed=False).add_to(carte)

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
    parser.add_argument("--lat", type=float, help="Latitude de la borne (ex: 48.8566). Demandée si absente.")
    parser.add_argument("--lon", type=float, help="Longitude de la borne (ex: 2.3522). Demandée si absente.")
    parser.add_argument("--csv", default="export_IA.csv", help="Chemin du fichier CSV source.")
    parser.add_argument("--model", default="kmeans_irve_model.pkl", help="Chemin du modèle KMeans entraîné.")
    parser.add_argument("--k", type=int, choices=[5, 6, 7], help="Nombre de clusters à utiliser (5, 6 ou 7). Si absent, réutilise le modèle pré-entraîné (--model).")
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
    if lat is None or lon is None:
        print("--- Saisie des coordonnées de la borne ---")
        try:
            lat = lat if lat is not None else float(input("Entrez la latitude (ex: 48.8566) : "))
            lon = lon if lon is not None else float(input("Entrez la longitude (ex: 2.3522) : "))
        except ValueError:
            print("Erreur : Veuillez entrer des nombres valides.")
            return

    os.makedirs(args.output, exist_ok=True)
    chemin_sortie = os.path.join(args.output, "carte_finale.html")

    generer_carte_complete(lat, lon, args.csv, args.model, chemin_sortie, k=args.k)


if __name__ == "__main__":
    main()
