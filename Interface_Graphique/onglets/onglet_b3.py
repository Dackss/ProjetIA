# Interface_Graphique/onglets/onglet_b3.py
import os
import sys

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QDoubleSpinBox, QSpinBox, QCheckBox, QComboBox,
    QPushButton, QLabel, QMessageBox, QVBoxLayout,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Interface_Graphique.chdir_utils import chdir

BESOIN_3_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Besoin_Client_3",
)

TYPES_TARIF = ["composite", "gratuit", "inconnu", "kwh", "temps"]


class OngletB3(QWidget):
    def __init__(self):
        super().__init__()

        self.puissance = QDoubleSpinBox()
        self.puissance.setRange(0.0, 1000.0)
        self.puissance.setValue(22.0)
        self.puissance.setSuffix(" kW")

        self.nb_pdc = QSpinBox()
        self.nb_pdc.setRange(0, 100)
        self.nb_pdc.setValue(2)

        self.latitude = QDoubleSpinBox()
        self.latitude.setRange(-90.0, 90.0)
        self.latitude.setDecimals(6)
        self.latitude.setValue(48.8566)

        self.longitude = QDoubleSpinBox()
        self.longitude.setRange(-180.0, 180.0)
        self.longitude.setDecimals(6)
        self.longitude.setValue(2.3522)

        self.gratuit = QCheckBox("Gratuit")
        self.deux_roues = QCheckBox("Accessible deux-roues")
        self.prise_ccs = QCheckBox("Prise CCS")
        self.prise_type2 = QCheckBox("Prise Type 2")
        self.prise_chademo = QCheckBox("Prise CHAdeMO")
        self.prise_ef = QCheckBox("Prise EF (domestique)")
        self.paiement_acte = QCheckBox("Paiement à l'acte")
        self.paiement_cb = QCheckBox("Paiement carte bancaire")
        self.paiement_autre = QCheckBox("Autre moyen de paiement")

        self.type_tarif = QComboBox()
        self.type_tarif.addItems(TYPES_TARIF)

        bouton_predire = QPushButton("Prédire l'implantation")
        bouton_predire.clicked.connect(self._predire)

        self.resultat = QLabel("—")
        self.resultat.setStyleSheet("font-size: 18px; font-weight: bold;")

        formulaire = QFormLayout()
        formulaire.addRow("Puissance :", self.puissance)
        formulaire.addRow("Nombre de PDC :", self.nb_pdc)
        formulaire.addRow("Latitude :", self.latitude)
        formulaire.addRow("Longitude :", self.longitude)
        formulaire.addRow(self.gratuit)
        formulaire.addRow(self.deux_roues)
        formulaire.addRow(self.prise_ccs)
        formulaire.addRow(self.prise_type2)
        formulaire.addRow(self.prise_chademo)
        formulaire.addRow(self.prise_ef)
        formulaire.addRow(self.paiement_acte)
        formulaire.addRow(self.paiement_cb)
        formulaire.addRow(self.paiement_autre)
        formulaire.addRow("Type de tarification :", self.type_tarif)

        layout = QVBoxLayout(self)
        layout.addLayout(formulaire)
        layout.addWidget(bouton_predire)
        layout.addWidget(QLabel("Implantation prédite :"))
        layout.addWidget(self.resultat)
        layout.addStretch()

    def _predire(self):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from Besoin_Client_3.main import predire_implantation

        try:
            with chdir(BESOIN_3_DIR):
                resultat = predire_implantation(
                    puissance=self.puissance.value(),
                    nb_pdc=self.nb_pdc.value(),
                    latitude=self.latitude.value(),
                    longitude=self.longitude.value(),
                    gratuit=self.gratuit.isChecked(),
                    deux_roues=self.deux_roues.isChecked(),
                    prise_ccs=self.prise_ccs.isChecked(),
                    prise_type2=self.prise_type2.isChecked(),
                    prise_chademo=self.prise_chademo.isChecked(),
                    prise_ef=self.prise_ef.isChecked(),
                    paiement_acte=self.paiement_acte.isChecked(),
                    paiement_cb=self.paiement_cb.isChecked(),
                    paiement_autre=self.paiement_autre.isChecked(),
                    type_tarif=self.type_tarif.currentText(),
                )
        except SystemExit:
            QMessageBox.warning(
                self, "Modèles introuvables",
                "Les fichiers .pkl de Besoin_Client_3 sont introuvables.\n"
                "Exécutez d'abord Besoin_Client_3/main.ipynb en entier.",
            )
            return

        self.resultat.setText(str(resultat))
