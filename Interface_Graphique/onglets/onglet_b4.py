# Interface_Graphique/onglets/onglet_b4.py
import os
import sys

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QSpinBox, QCheckBox, QComboBox, QLineEdit,
    QPushButton, QLabel, QMessageBox, QVBoxLayout,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from Interface_Graphique.chdir_utils import chdir

BESOIN_4_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "Besoin_Client_4",
)

IMPLANTATIONS = [
    "Parking privé réservé à la clientèle",
    "Parking privé à usage public",
    "Parking public",
    "Station dédiée à la recharge rapide",
    "Voirie",
]
CONDITIONS_ACCES = ["Accès libre", "Accès réservé"]
TYPES_TARIF = ["composite", "gratuit", "inconnu", "kwh", "temps"]
RACCORDEMENTS = ["Direct", "Indirect", "inconnu"]


class OngletB4(QWidget):
    def __init__(self):
        super().__init__()

        self.implantation = QComboBox()
        self.implantation.addItems(IMPLANTATIONS)

        self.nb_pdc = QSpinBox()
        self.nb_pdc.setRange(0, 100)
        self.nb_pdc.setValue(2)

        self.prise_ccs = QCheckBox("Prise CCS")
        self.prise_chademo = QCheckBox("Prise CHAdeMO")
        self.prise_type2 = QCheckBox("Prise Type 2")
        self.prise_ef = QCheckBox("Prise EF (domestique)")
        self.reservation = QCheckBox("Réservable")

        self.condition_acces = QComboBox()
        self.condition_acces.addItems(CONDITIONS_ACCES)

        self.type_tarif = QComboBox()
        self.type_tarif.addItems(TYPES_TARIF)

        self.raccordement = QComboBox()
        self.raccordement.addItems(RACCORDEMENTS)

        self.operateur = QLineEdit()
        self.operateur.setPlaceholderText("ex: Tesla, IZIVIA, inconnu")

        bouton_predire = QPushButton("Prédire la puissance")
        bouton_predire.clicked.connect(self._predire)

        self.resultat = QLabel("—")
        self.resultat.setStyleSheet("font-size: 18px; font-weight: bold;")

        formulaire = QFormLayout()
        formulaire.addRow("Implantation :", self.implantation)
        formulaire.addRow("Nombre de PDC :", self.nb_pdc)
        formulaire.addRow(self.prise_ccs)
        formulaire.addRow(self.prise_chademo)
        formulaire.addRow(self.prise_type2)
        formulaire.addRow(self.prise_ef)
        formulaire.addRow(self.reservation)
        formulaire.addRow("Condition d'accès :", self.condition_acces)
        formulaire.addRow("Type de tarification :", self.type_tarif)
        formulaire.addRow("Raccordement :", self.raccordement)
        formulaire.addRow("Opérateur :", self.operateur)

        layout = QVBoxLayout(self)
        layout.addLayout(formulaire)
        layout.addWidget(bouton_predire)
        layout.addWidget(QLabel("Puissance prédite :"))
        layout.addWidget(self.resultat)
        layout.addStretch()

    def _predire(self):
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from Besoin_Client_4.main import predire_puissance

        try:
            with chdir(BESOIN_4_DIR):
                resultat = predire_puissance(
                    implantation=self.implantation.currentText(),
                    nb_pdc=self.nb_pdc.value(),
                    prise_ccs=self.prise_ccs.isChecked(),
                    prise_chademo=self.prise_chademo.isChecked(),
                    prise_type2=self.prise_type2.isChecked(),
                    prise_ef=self.prise_ef.isChecked(),
                    reservation=self.reservation.isChecked(),
                    condition_acces=self.condition_acces.currentText(),
                    type_tarif=self.type_tarif.currentText(),
                    raccordement=self.raccordement.currentText(),
                    operateur=self.operateur.text() or "inconnu",
                )
        except SystemExit:
            QMessageBox.warning(
                self, "Modèles introuvables",
                "Les fichiers .pkl de Besoin_Client_4 sont introuvables.\n"
                "Exécutez d'abord Besoin_Client_4/main.ipynb en entier.",
            )
            return

        self.resultat.setText(str(resultat))
