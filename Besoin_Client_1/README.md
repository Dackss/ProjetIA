# Besoin Client 1

## Prerequis

- Python 3.x installe
- Le fichier `export_IA.csv` present dans ce meme dossier (`Besoin_Client_1/`)

## Execution

1. Se placer dans ce dossier avant de lancer le script :

   ```
   cd Besoin_Client_1
   python main.py
   ```

2. Au premier lancement, le script installe automatiquement les dependances
   (pandas, numpy, matplotlib, seaborn, folium, scikit-learn, joblib) via pip.
   Pour sauter cette etape sur les lancements suivants :

   ```
   python main.py --skip-install
   ```

## Options disponibles

| Option | Description |
|---|---|
| `--csv <chemin>` | Chemin du fichier CSV source (defaut : `export_IA.csv`) |
| `--output <dossier>` | Dossier de sortie pour cartes/graphiques (defaut : `output`) |
| `--encoder <chemin>` | Chemin de sauvegarde de l'encodeur `.pkl` (defaut : `encoder_implantation.pkl`) |
| `--skip-install` | Ne pas reinstaller les dependances |

Exemple :

```
python main.py --csv export_IA.csv --output output --skip-install
```

## Resultats generes (dans le dossier `output/`)

- `carte_implantation_filtrable.html` — Carte interactive filtrable par type d'implantation. Chaque marqueur a un popup (implantation + puissance au clic). Au-dela de 8000 bornes par type, un echantillon aleatoire est affiche (seed fixe) pour garder un fichier exploitable dans le navigateur.
- `carte_chaleur.html` — Carte de densite (heatmap) des bornes
- `distribution_implantation.png` — Graphique de distribution par type d'implantation
- `distribution_puissance.png` — Graphique de distribution de la puissance (≤ 150 kW)

L'encodeur LabelEncoder (`encoder_implantation.pkl`) est sauvegarde a la racine
de `Besoin_Client_1/`.
