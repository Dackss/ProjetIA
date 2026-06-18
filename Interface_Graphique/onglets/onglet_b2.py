# Interface_Graphique/onglets/onglet_b2.py
import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel, QMessageBox, QVBoxLayout, QProgressBar,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Interface_Graphique.workers import FonctionWorker

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BESOIN_2_DIR = os.path.join(REPO_ROOT, "Besoin_Client_2")


class OngletB2(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None

        self.adresse = QLineEdit()
        self.adresse.setPlaceholderText("ex: 10 rue de Rivoli, Paris (laisser vide pour saisir lat/lon)")

        self.latitude = QDoubleSpinBox()
        self.latitude.setRange(-90.0, 90.0)
        self.latitude.setDecimals(6)
        self.latitude.setValue(48.8566)

        self.longitude = QDoubleSpinBox()
        self.longitude.setRange(-180.0, 180.0)
        self.longitude.setDecimals(6)
        self.longitude.setValue(2.3522)

        self.k_choisi = QComboBox()
        self.k_choisi.addItems(["5", "6", "7"])

        self.bouton_generer = QPushButton("Générer la carte")
        self.bouton_generer.clicked.connect(self._lancer_generation)

        self.barre_progression = QProgressBar()
        self.barre_progression.setRange(0, 0)  # indeterminee
        self.barre_progression.hide()

        self.vue_carte = QWebEngineView()
        # Folium charge leaflet.js/leaflet.css depuis un CDN ; par defaut QtWebEngine
        # interdit a une page locale (file://) d'acceder a des ressources distantes,
        # ce qui laisse "L" (Leaflet) indefini et la carte vide. On l'autorise ici.
        self.vue_carte.settings().setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )

        formulaire = QFormLayout()
        formulaire.addRow("Adresse/ville :", self.adresse)
        formulaire.addRow("Latitude (si pas d'adresse) :", self.latitude)
        formulaire.addRow("Longitude (si pas d'adresse) :", self.longitude)
        formulaire.addRow("Nombre de clusters (K) :", self.k_choisi)

        layout = QVBoxLayout(self)
        layout.addLayout(formulaire)
        layout.addWidget(self.bouton_generer)
        layout.addWidget(self.barre_progression)
        layout.addWidget(self.vue_carte)

    def _lancer_generation(self):
        self.bouton_generer.setEnabled(False)
        self.barre_progression.show()

        lat = self.latitude.value()
        lon = self.longitude.value()
        texte_adresse = self.adresse.text().strip()
        k = int(self.k_choisi.currentText())

        self._worker = FonctionWorker(self._generer_carte_en_arriere_plan, lat, lon, texte_adresse, k)
        self._worker.termine.connect(self._sur_succes)
        self._worker.erreur.connect(self._sur_erreur)
        self._worker.start()

    def _generer_carte_en_arriere_plan(self, lat, lon, texte_adresse, k):
        sys.path.insert(0, REPO_ROOT)
        from Besoin_Client_2.main import geocoder_adresse, generer_carte_complete

        if texte_adresse:
            resultat = geocoder_adresse(texte_adresse)
            if resultat is None:
                raise ValueError(f"Adresse introuvable : '{texte_adresse}'")
            lat, lon = resultat

        chemin_csv = os.path.join(BESOIN_2_DIR, "export_IA.csv")
        chemin_model = os.path.join(BESOIN_2_DIR, f"kmeans_irve_model_k{k}.pkl")
        chemin_sortie = os.path.join(BESOIN_2_DIR, "output", "carte_clusters_borne_recherchee.html")

        if not os.path.exists(chemin_model):
            raise FileNotFoundError(
                f"Modèle introuvable : {chemin_model}. Exécutez Besoin_Client_2/main.ipynb d'abord."
            )

        os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)
        generer_carte_complete(lat, lon, chemin_csv, chemin_model, chemin_sortie)
        return chemin_sortie

    def _sur_succes(self, chemin_carte):
        self.barre_progression.hide()
        self.bouton_generer.setEnabled(True)
        self.vue_carte.setUrl(QUrl.fromLocalFile(os.path.abspath(chemin_carte)))

    def _sur_erreur(self, message):
        self.barre_progression.hide()
        self.bouton_generer.setEnabled(True)
        QMessageBox.warning(self, "Erreur de génération", message)
