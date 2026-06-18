# Interface_Graphique/onglets/onglet_b1.py
import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QVBoxLayout, QProgressBar, QMessageBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Interface_Graphique.workers import FonctionWorker

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BESOIN_1_DIR = os.path.join(REPO_ROOT, "Besoin_Client_1")


class OngletB1(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self._chemins_cartes = {}

        self.bouton_generer = QPushButton("Générer les cartes")
        self.bouton_generer.clicked.connect(self._lancer_generation)

        self.selecteur_carte = QComboBox()
        self.selecteur_carte.addItems(["Carte filtrable (implantation)", "Carte de chaleur"])
        self.selecteur_carte.currentIndexChanged.connect(self._changer_carte_affichee)
        self.selecteur_carte.setEnabled(False)

        self.barre_progression = QProgressBar()
        self.barre_progression.setRange(0, 0)
        self.barre_progression.hide()

        self.vue_carte = QWebEngineView()
        # Folium charge leaflet.js/leaflet.css depuis un CDN ; par defaut QtWebEngine
        # interdit a une page locale (file://) d'acceder a des ressources distantes,
        # ce qui laisse "L" (Leaflet) indefini et la carte vide. On l'autorise ici.
        self.vue_carte.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self.bouton_generer)
        layout.addWidget(self.selecteur_carte)
        layout.addWidget(self.barre_progression)
        layout.addWidget(self.vue_carte)

    def _lancer_generation(self):
        self.bouton_generer.setEnabled(False)
        self.selecteur_carte.setEnabled(False)
        self.barre_progression.show()

        self._worker = FonctionWorker(self._generer_cartes_en_arriere_plan)
        self._worker.termine.connect(self._sur_succes)
        self._worker.erreur.connect(self._sur_erreur)
        self._worker.start()

    def _generer_cartes_en_arriere_plan(self):
        sys.path.insert(0, REPO_ROOT)
        from Besoin_Client_1.main import (
            charger_donnees, nettoyer_donnees, encoder_implantation,
            generer_carte_implantation, generer_carte_chaleur,
        )

        dossier_output = os.path.join(BESOIN_1_DIR, "output")
        os.makedirs(dossier_output, exist_ok=True)

        chemin_csv = os.path.join(BESOIN_1_DIR, "export_IA.csv")
        if not os.path.exists(chemin_csv):
            raise FileNotFoundError(f"Fichier source introuvable : {chemin_csv}")

        df = charger_donnees(chemin_csv)
        df_b1 = nettoyer_donnees(df)
        df_b1 = encoder_implantation(df_b1, os.path.join(BESOIN_1_DIR, "encoder_implantation.pkl"))

        chemin_filtrable = os.path.join(dossier_output, "carte_implantation_filtrable.html")
        chemin_chaleur = os.path.join(dossier_output, "carte_chaleur.html")

        generer_carte_implantation(df_b1, chemin_filtrable, "Carte filtrable enregistrée avec succès !")
        generer_carte_chaleur(df_b1, chemin_chaleur)

        return {"filtrable": chemin_filtrable, "chaleur": chemin_chaleur}

    def _sur_succes(self, chemins):
        self.barre_progression.hide()
        self.bouton_generer.setEnabled(True)
        self.selecteur_carte.setEnabled(True)
        self._chemins_cartes = chemins
        self._changer_carte_affichee(self.selecteur_carte.currentIndex())

    def _changer_carte_affichee(self, index):
        if not self._chemins_cartes:
            return
        cle = "filtrable" if index == 0 else "chaleur"
        self.vue_carte.setUrl(QUrl.fromLocalFile(os.path.abspath(self._chemins_cartes[cle])))

    def _sur_erreur(self, message):
        self.barre_progression.hide()
        self.bouton_generer.setEnabled(True)
        QMessageBox.warning(self, "Erreur de génération", message)
