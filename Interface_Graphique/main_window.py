# Interface_Graphique/main_window.py
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QLabel, QVBoxLayout
from Interface_Graphique.onglets.onglet_b2 import OngletB2
from Interface_Graphique.onglets.onglet_b3 import OngletB3
from Interface_Graphique.onglets.onglet_b4 import OngletB4


def _onglet_placeholder(texte):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.addWidget(QLabel(texte))
    return widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projet IA — Bornes de recharge IRVE")
        self.resize(1100, 750)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(_onglet_placeholder("B1 — a venir"), "B1 — Cartes")
        self.tabs.addTab(OngletB2(), "B2 — Clustering")
        self.tabs.addTab(OngletB3(), "B3 — Implantation")
        self.tabs.addTab(OngletB4(), "B4 — Puissance")
