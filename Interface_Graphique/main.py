# Interface_Graphique/main.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication
from Interface_Graphique.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    fenetre = MainWindow()
    fenetre.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
