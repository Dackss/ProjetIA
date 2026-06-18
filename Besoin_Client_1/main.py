import argparse
import subprocess
import sys

REQUIREMENTS = ["pandas", "numpy", "matplotlib", "seaborn", "folium", "scikit-learn", "joblib"]

def installer_dependances():
    subprocess.check_call([sys.executable, "-m", "pip", "install", *REQUIREMENTS])


def charger_donnees(chemin_csv):
    import pandas as pd
    df = pd.read_csv(chemin_csv)
    print(f"Jeu de données chargé : {df.shape[0]} lignes et {df.shape[1]} colonnes.")
    return df


def nettoyer_donnees(df):
    colonnes_interet = ['latitude', 'longitude', 'implantation', 'puissance']
    df_b1 = df[colonnes_interet].dropna().copy()
    print(f"Nombre de lignes exploitables pour les cartes : {df_b1.shape[0]}")
    return df_b1


def encoder_implantation(df_b1, chemin_encoder):
    import joblib
    from sklearn.preprocessing import LabelEncoder

    le_implantation = LabelEncoder()
    df_b1['implantation_encoded'] = le_implantation.fit_transform(df_b1['implantation'])

    print("Correspondance des classes encodées :")
    for index, classe in enumerate(le_implantation.classes_):
        print(f"  {classe} -> {index}")

    joblib.dump(le_implantation, chemin_encoder)
    print("Encodeur sauvegardé avec succès !")
    return df_b1


def generer_carte_implantation(df_source, chemin_sortie, message_succes, plafond_par_groupe=8000):
    import folium
    from folium.plugins import MarkerCluster

    carte = folium.Map(location=[46.2276, 2.2137], zoom_start=6)

    for type_impl, sous_df in df_source.groupby('implantation'):
        calque = folium.FeatureGroup(name=f"Implantation : {type_impl}")
        cluster = MarkerCluster(options={'maxClusterRadius': 50}).add_to(calque)

        # Au-dela de `plafond_par_groupe` marqueurs, on echantillonne : le fichier HTML
        # genere etait sinon trop lourd (~30 Mo, un marqueur par borne) pour un chargement
        # fluide dans le navigateur. Echantillon aleatoire (seed fixe) pour rester reproductible.
        if len(sous_df) > plafond_par_groupe:
            sous_df = sous_df.sample(plafond_par_groupe, random_state=42)

        for lat, lon, puissance in sous_df[['latitude', 'longitude', 'puissance']].values:
            folium.Marker(
                location=[lat, lon],
                popup=f"{type_impl}<br>Puissance : {puissance:.1f} kW",
            ).add_to(cluster)

        calque.add_to(carte)

    folium.LayerControl(collapsed=False).add_to(carte)
    carte.save(chemin_sortie)
    print(message_succes)
    return carte


def generer_carte_chaleur(df_b1, chemin_sortie):
    import folium
    from folium.plugins import HeatMap

    carte_chaleur = folium.Map(location=[46.2276, 2.2137], zoom_start=6)
    coordonnees = df_b1[['latitude', 'longitude']].values.tolist()
    HeatMap(coordonnees, radius=10, blur=15, min_opacity=0.5).add_to(carte_chaleur)
    carte_chaleur.save(chemin_sortie)
    print("Carte de chaleur enregistrée avec succès !")


def generer_distribution_implantation(df_b1, chemin_sortie):
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(10, 5))
    sns.countplot(
        y='implantation',
        data=df_b1,
        order=df_b1['implantation'].value_counts().index,
        hue='implantation',
        legend=False,
        palette='viridis'
    )
    plt.title("Distribution des points de recharge par type d'implantation")
    plt.xlabel("Nombre de bornes")
    plt.ylabel("Type d'implantation")
    plt.tight_layout()
    plt.savefig(chemin_sortie)
    plt.close()


def generer_distribution_puissance(df_b1, chemin_sortie):
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(10, 5))
    sns.histplot(data=df_b1[df_b1['puissance'] <= 150], x='puissance', bins=30, kde=True, palette='magma')
    plt.title("Distribution de la puissance nominale des bornes (≤ 150 kW)")
    plt.xlabel("Puissance (kW)")
    plt.ylabel("Nombre de bornes")
    plt.tight_layout()
    plt.savefig(chemin_sortie)
    plt.close()


def parse_args():
    parser = argparse.ArgumentParser(description="Pipeline Besoin Client 1 : cartes et graphiques IRVE.")
    parser.add_argument("--csv", default="export_IA.csv", help="Chemin du fichier CSV source.")
    parser.add_argument("--output", default="output", help="Dossier de sortie pour cartes et graphiques.")
    parser.add_argument("--encoder", default="encoder_implantation.pkl", help="Chemin de sauvegarde de l'encodeur.")
    parser.add_argument("--skip-install", action="store_true", help="Ne pas installer les dépendances avant exécution.")
    return parser.parse_args()


def main():
    import os

    args = parse_args()

    if not args.skip_install:
        installer_dependances()

    os.makedirs(args.output, exist_ok=True)

    df = charger_donnees(args.csv)
    df_b1 = nettoyer_donnees(df)
    df_b1 = encoder_implantation(df_b1, args.encoder)

    generer_carte_implantation(
        df_b1,
        os.path.join(args.output, "carte_implantation_filtrable.html"),
        "Carte filtrable enregistrée avec succès !",
    )
    generer_carte_chaleur(df_b1, os.path.join(args.output, "carte_chaleur.html"))
    generer_distribution_implantation(df_b1, os.path.join(args.output, "distribution_implantation.png"))
    generer_distribution_puissance(df_b1, os.path.join(args.output, "distribution_puissance.png"))


if __name__ == "__main__":
    main()
