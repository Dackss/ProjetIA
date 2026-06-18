# Interface Graphique PySide6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single PySide6 desktop app (`Interface_Graphique/`) with 4 tabs that wraps the existing `Besoin_Client_1..4` prediction/mapping functions — no ML logic duplicated, no retraining triggered from the GUI.

**Architecture:** `QMainWindow` + `QTabWidget`, one `QWidget` subclass per tab. Each tab imports functions directly from `Besoin_Client_X/main.py` via `sys.path` injection (namespace packages, no `__init__.py` needed). Heavy/blocking calls (map generation, geocoding) run in a generic `QThread` worker; predictions (B3/B4) run synchronously since they're fast.

**Tech Stack:** Python 3.13, PySide6, PySide6-WebEngine (folium HTML display), pandas, scikit-learn, joblib, geopy (already used by Besoin_Client_2).

## Global Constraints

- Never trigger retraining — only call functions that load pre-trained `.pkl` files (matches the constraint already enforced in every `Besoin_Client_X/main.py`).
- Never call `installer_dependances()` from any besoin module — the GUI's own `requirements.txt` covers all dependencies.
- B3/B4 prediction functions (`predire_implantation`, `predire_puissance`) load `.pkl` files via filenames relative to the current working directory — calls to them MUST happen inside `with chdir("Besoin_Client_3"):` / `with chdir("Besoin_Client_4"):`.
- B1/B2 functions take all file paths as explicit arguments — pass absolute paths built from each besoin's folder; do NOT use `chdir` for these (unnecessary, and would conflict with relative `--csv`/`--model` defaults used elsewhere).
- No automated tests for this GUI (consistent with the rest of the project) — each task ends with a manual run-and-observe verification step instead.
- No packaging/executable — app is launched with `python Interface_Graphique/main.py`.

---

## File Structure

```
Interface_Graphique/
├── main.py                    # Entry point: QApplication + MainWindow.show()
├── main_window.py             # QMainWindow with QTabWidget (4 tabs)
├── chdir_utils.py             # `chdir` context manager (used by B3/B4 tabs only)
├── workers.py                 # Generic QThread worker for blocking calls
├── onglets/
│   ├── onglet_b1.py            # Cartes implantation/chaleur
│   ├── onglet_b2.py            # Clustering geographique
│   ├── onglet_b3.py            # Prediction implantation
│   └── onglet_b4.py            # Prediction puissance
├── requirements.txt
└── README.md

Besoin_Client_2/main.py         # MODIFIED: add plafond_par_groupe param to generer_carte_complete
```

---

### Task 1: Scaffold project, `chdir_utils.py`, `workers.py`, `requirements.txt`

**Files:**
- Create: `Interface_Graphique/requirements.txt`
- Create: `Interface_Graphique/chdir_utils.py`
- Create: `Interface_Graphique/workers.py`
- Create: `Interface_Graphique/__init__.py` (empty, makes the folder importable if ever needed)

**Interfaces:**
- Produces: `chdir_utils.chdir(dossier: str)` — context manager, changes cwd to `dossier` (relative to repo root) for the `with` block, restores previous cwd on exit (even on exception).
- Produces: `workers.FonctionWorker(QThread)` — constructor `FonctionWorker(fonction, *args, **kwargs)`; signals `termine = Signal(object)` (emits the function's return value) and `erreur = Signal(str)` (emits `str(exception)` on failure). Call `.start()` to run `fonction(*args, **kwargs)` on a background thread.

- [ ] **Step 1: Create the requirements file**

```
# Interface_Graphique/requirements.txt
PySide6
PySide6-Addons
pandas
numpy
scikit-learn
joblib
folium
geopy
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r Interface_Graphique/requirements.txt`
Expected: no errors, `PySide6` importable afterward.

Verify: `python3 -c "import PySide6; from PySide6.QtWebEngineWidgets import QWebEngineView; print('ok')"`
Expected output: `ok`

- [ ] **Step 3: Create the empty package marker**

```python
# Interface_Graphique/__init__.py
```
(empty file)

- [ ] **Step 4: Write `chdir_utils.py`**

```python
# Interface_Graphique/chdir_utils.py
"""Context manager pour les fonctions de Besoin_Client_3/4 qui chargent
leurs .pkl avec des chemins relatifs au repertoire courant. N'est PAS
thread-safe (le cwd est un etat global du process) : dans cette appli,
un seul appel a une fonction necessitant `chdir` est en vol a la fois
(les predictions B3/B4 sont synchrones, jamais lancees en parallele dans
deux threads). Si une future evolution paralleliserait ces appels, ce
contrat ne tiendrait plus et il faudrait refactorer les fonctions de
Besoin_Client_3/4 pour accepter un parametre de dossier explicite."""
import os
from contextlib import contextmanager


@contextmanager
def chdir(dossier):
    cwd_precedent = os.getcwd()
    os.chdir(dossier)
    try:
        yield
    finally:
        os.chdir(cwd_precedent)
```

- [ ] **Step 5: Manually verify `chdir`**

Run:
```bash
cd /mnt/c/Users/dacks/Documents/Cours/A3/IA/ProjetIA
python3 -c "
from Interface_Graphique.chdir_utils import chdir
import os
avant = os.getcwd()
with chdir('Besoin_Client_3'):
    print('dans le bloc :', os.getcwd())
print('apres :', os.getcwd())
assert os.getcwd() == avant
print('ok')
"
```
Expected output:
```
dans le bloc : /mnt/c/Users/dacks/Documents/Cours/A3/IA/ProjetIA/Besoin_Client_3
apres : /mnt/c/Users/dacks/Documents/Cours/A3/IA/ProjetIA
ok
```

- [ ] **Step 6: Write `workers.py`**

```python
# Interface_Graphique/workers.py
"""Worker generique pour executer une fonction bloquante (generation de
carte, geocodage reseau) sur un thread separe, pour ne jamais geler l'UI
Qt. Usage :

    worker = FonctionWorker(ma_fonction, arg1, arg2, kwarg=valeur)
    worker.termine.connect(lambda resultat: ...)
    worker.erreur.connect(lambda message: ...)
    worker.start()
"""
from PySide6.QtCore import QThread, Signal


class FonctionWorker(QThread):
    termine = Signal(object)
    erreur = Signal(str)

    def __init__(self, fonction, *args, **kwargs):
        super().__init__()
        self.fonction = fonction
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            resultat = self.fonction(*self.args, **self.kwargs)
        except Exception as exc:
            self.erreur.emit(str(exc))
            return
        self.termine.emit(resultat)
```

- [ ] **Step 7: Manually verify `FonctionWorker`**

Run:
```bash
python3 -c "
import sys
from PySide6.QtCore import QCoreApplication
sys.path.insert(0, '.')
from Interface_Graphique.workers import FonctionWorker

app = QCoreApplication([])

def addition_lente(a, b):
    import time
    time.sleep(0.2)
    return a + b

worker = FonctionWorker(addition_lente, 2, 3)
worker.termine.connect(lambda r: (print('resultat:', r), app.quit()))
worker.erreur.connect(lambda m: (print('erreur:', m), app.quit()))
worker.start()
app.exec()
"
```
Expected output: `resultat: 5`

- [ ] **Step 8: Commit**

```bash
git add Interface_Graphique/requirements.txt Interface_Graphique/chdir_utils.py Interface_Graphique/workers.py Interface_Graphique/__init__.py
git commit -m "Scaffold Interface_Graphique: chdir utility and generic QThread worker"
```

---

### Task 2: Main window with 4 empty tabs

**Files:**
- Create: `Interface_Graphique/main_window.py`
- Create: `Interface_Graphique/main.py`

**Interfaces:**
- Consumes: nothing yet (tabs are placeholders in this task; replaced with real tabs in Tasks 3-6).
- Produces: `main_window.MainWindow(QMainWindow)` — has a `self.tabs` (`QTabWidget`) attribute with 4 tabs added in order B1, B2, B3, B4. Later tasks call `self.tabs.addTab(widget, titre)` is already done here with placeholder widgets; later tasks replace the placeholder widget instances, not the tab structure.

- [ ] **Step 1: Write `main_window.py` with placeholder tabs**

```python
# Interface_Graphique/main_window.py
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QLabel, QVBoxLayout


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
        self.tabs.addTab(_onglet_placeholder("B2 — a venir"), "B2 — Clustering")
        self.tabs.addTab(_onglet_placeholder("B3 — a venir"), "B3 — Implantation")
        self.tabs.addTab(_onglet_placeholder("B4 — Puissance"), "B4 — Puissance")
```

- [ ] **Step 2: Write `main.py` entry point**

```python
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
```

- [ ] **Step 3: Manually verify the app launches with 4 tabs**

Run: `python3 Interface_Graphique/main.py`
Expected: a window titled "Projet IA — Bornes de recharge IRVE" opens, with 4 tabs labeled "B1 — Cartes", "B2 — Clustering", "B3 — Implantation", "B4 — Puissance", each showing its placeholder text. Close the window to end the process cleanly (no traceback in terminal).

- [ ] **Step 4: Commit**

```bash
git add Interface_Graphique/main_window.py Interface_Graphique/main.py
git commit -m "Add Interface_Graphique main window with 4 placeholder tabs"
```

---

### Task 3: Onglet B3 — Prédiction implantation

**Files:**
- Create: `Interface_Graphique/onglets/__init__.py` (empty)
- Create: `Interface_Graphique/onglets/onglet_b3.py`
- Modify: `Interface_Graphique/main_window.py:21` (replace B3 placeholder with `OngletB3()`)

**Interfaces:**
- Consumes: `Besoin_Client_3.main.predire_implantation(puissance, nb_pdc, latitude, longitude, gratuit, deux_roues, prise_ccs, prise_type2, prise_chademo, prise_ef, paiement_acte, paiement_cb, paiement_autre, type_tarif)` → returns a `str` (predicted implantation class) or calls `sys.exit(1)` if `.pkl` files are missing (this is existing behavior — Step 1 of the test plan in this task covers catching that case via `chdir_utils.chdir` + try/except `SystemExit`).
- Consumes: `Interface_Graphique.chdir_utils.chdir(dossier: str)`.
- Produces: `onglet_b3.OngletB3(QWidget)` — no public methods consumed by other tasks (self-contained).

- [ ] **Step 1: Create the empty `onglets` package marker**

```python
# Interface_Graphique/onglets/__init__.py
```
(empty file)

- [ ] **Step 2: Write `onglet_b3.py`**

```python
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
```

- [ ] **Step 3: Wire the tab into `main_window.py`**

Modify `Interface_Graphique/main_window.py`: replace the import section and the B3 tab line.

```python
# Interface_Graphique/main_window.py
from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QLabel, QVBoxLayout
from Interface_Graphique.onglets.onglet_b3 import OngletB3


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
        self.tabs.addTab(_onglet_placeholder("B2 — a venir"), "B2 — Clustering")
        self.tabs.addTab(OngletB3(), "B3 — Implantation")
        self.tabs.addTab(_onglet_placeholder("B4 — a venir"), "B4 — Puissance")
```

- [ ] **Step 4: Manually verify the prediction works end-to-end**

Run: `python3 Interface_Graphique/main.py`
In the app: click the "B3 — Implantation" tab, leave default values, click "Prédire l'implantation".
Expected: the `QLabel` below "Implantation prédite :" shows a non-empty string (one of: `Voirie`, `Parking public`, `Parking privé à usage public`, `Parking privé réservé à la clientèle`, `Station dédiée à la recharge rapide`). No traceback in terminal.

- [ ] **Step 5: Commit**

```bash
git add Interface_Graphique/onglets/__init__.py Interface_Graphique/onglets/onglet_b3.py Interface_Graphique/main_window.py
git commit -m "Add Onglet B3: implantation prediction form"
```

---

### Task 4: Onglet B4 — Prédiction puissance

**Files:**
- Create: `Interface_Graphique/onglets/onglet_b4.py`
- Modify: `Interface_Graphique/main_window.py` (replace B4 placeholder with `OngletB4()`)

**Interfaces:**
- Consumes: `Besoin_Client_4.main.predire_puissance(implantation, nb_pdc, prise_ccs, prise_chademo, prise_type2, prise_ef, reservation, condition_acces, type_tarif, raccordement, operateur)` → returns a `str` (e.g. `"Rapide (50 - 150 kW)"`) or raises `SystemExit` if `.pkl` files are missing.
- Consumes: `Interface_Graphique.chdir_utils.chdir`.
- Produces: `onglet_b4.OngletB4(QWidget)` — self-contained.

- [ ] **Step 1: Write `onglet_b4.py`**

```python
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
```

- [ ] **Step 2: Wire the tab into `main_window.py`**

Modify `Interface_Graphique/main_window.py`: add the import and replace the B4 placeholder line.

```python
from Interface_Graphique.onglets.onglet_b4 import OngletB4
```
(added next to the `onglet_b3` import)

```python
self.tabs.addTab(OngletB4(), "B4 — Puissance")
```
(replaces `self.tabs.addTab(_onglet_placeholder("B4 — a venir"), "B4 — Puissance")`)

- [ ] **Step 3: Manually verify**

Run: `python3 Interface_Graphique/main.py`
In the app: click "B4 — Puissance" tab, set Implantation = "Station dédiée à la recharge rapide", check Prise CCS and Prise CHAdeMO, set Opérateur = "Tesla", click "Prédire la puissance".
Expected: result label shows a string like `Ultra-rapide (> 150 kW)`. No traceback.

- [ ] **Step 4: Commit**

```bash
git add Interface_Graphique/onglets/onglet_b4.py Interface_Graphique/main_window.py
git commit -m "Add Onglet B4: puissance prediction form"
```

---

### Task 5: Add sampling to `Besoin_Client_2/main.py::generer_carte_complete`

**Files:**
- Modify: `Besoin_Client_2/main.py` (function `generer_carte_complete`, and its `main()` caller)

**Interfaces:**
- Produces: `generer_carte_complete(lat_saisie, lon_saisie, chemin_csv, chemin_model, chemin_sortie, plafond_par_groupe=8000)` — new optional 6th parameter, default preserves a fast, capped map; existing callers (the CLI `main()`) keep working unchanged since the parameter has a default.

- [ ] **Step 1: Read the current function before editing**

Run: `sed -n '14,64p' Besoin_Client_2/main.py`
Confirm the function body matches what Task 5's Step 2 below modifies (the `for idx, row in df_irve.iterrows():` loop is the one being capped).

- [ ] **Step 2: Add the sampling parameter and logic**

Modify `Besoin_Client_2/main.py`. Replace:

```python
def generer_carte_complete(lat_saisie, lon_saisie, chemin_csv, chemin_model, chemin_sortie):
```

with:

```python
def generer_carte_complete(lat_saisie, lon_saisie, chemin_csv, chemin_model, chemin_sortie, plafond_par_groupe=8000):
```

Then, inside the function, after the line `cluster_groups[cluster_id] = folium.FeatureGroup(name=f"Cluster {cluster_id}").add_to(carte)` loop and before `for _, row in df_irve.iterrows():`, insert the sampling step. Replace:

```python
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
```

with:

```python
    # Au-dela de `plafond_par_groupe` marqueurs par cluster, on echantillonne : le
    # fichier HTML genere etait sinon trop lent a produire/charger (~139 000 marqueurs
    # avec popup, 1-2 min). Meme logique que Besoin_Client_1 (echantillon aleatoire,
    # seed fixe, par groupe plutot que global pour garder chaque cluster represente).
    df_a_afficher = (
        df_irve.groupby('cluster', group_keys=False)
        .apply(lambda g: g.sample(plafond_par_groupe, random_state=42) if len(g) > plafond_par_groupe else g)
    )

    for _, row in df_a_afficher.iterrows():
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
```

Note: the legend (`construire_legende`) and `LayerControl` still use the full `df_irve` (not `df_a_afficher`) — the legend's effectif/% counts must reflect the true cluster sizes, not the sampled subset shown on the map. No change needed there; just confirm `construire_legende(df_irve, couleurs)` (not `df_a_afficher`) stays as the call argument a few lines below.

- [ ] **Step 3: Manually verify the CLI still works and is faster**

Run (from `Besoin_Client_2/`):
```bash
cd Besoin_Client_2
time python3 main.py --skip-install --lat 48.8566 --lon 2.3522
```
Expected: completes in well under 30 seconds (vs. 1-2 min before), prints `Carte générée avec succès : 'output/carte_clusters_borne_recherchee.html'`, no traceback.

Verify the output file still has the legend with correct (unsampled) counts:
```bash
grep -o "Cluster [0-9] —[^<]*" output/carte_clusters_borne_recherchee.html | head -5
```
Expected: counts roughly matching the earlier full-population numbers (e.g. `Cluster 2 — 47,354 bornes (34.1%)`), not capped-at-8000 numbers.

- [ ] **Step 4: Commit**

```bash
git add Besoin_Client_2/main.py
git commit -m "Cap markers per cluster in generer_carte_complete for faster map generation"
```

---

### Task 6: Onglet B2 — Clustering géographique

**Files:**
- Create: `Interface_Graphique/onglets/onglet_b2.py`
- Modify: `Interface_Graphique/main_window.py` (replace B2 placeholder with `OngletB2()`)

**Interfaces:**
- Consumes: `Besoin_Client_2.main.geocoder_adresse(adresse: str) -> tuple[float, float] | None`.
- Consumes: `Besoin_Client_2.main.generer_carte_complete(lat_saisie, lon_saisie, chemin_csv, chemin_model, chemin_sortie, plafond_par_groupe=8000)` (signature from Task 5).
- Consumes: `Interface_Graphique.workers.FonctionWorker`.
- Produces: `onglet_b2.OngletB2(QWidget)` — self-contained.

- [ ] **Step 1: Write `onglet_b2.py`**

```python
# Interface_Graphique/onglets/onglet_b2.py
import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QDoubleSpinBox, QComboBox,
    QPushButton, QLabel, QMessageBox, QVBoxLayout, QProgressBar,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

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

        self._worker = FonctionWorker(self._generer_carte_en_arriere_plan)
        self._worker.termine.connect(self._sur_succes)
        self._worker.erreur.connect(self._sur_erreur)
        self._worker.start()

    def _generer_carte_en_arriere_plan(self):
        sys.path.insert(0, REPO_ROOT)
        from Besoin_Client_2.main import geocoder_adresse, generer_carte_complete

        lat, lon = self.latitude.value(), self.longitude.value()
        texte_adresse = self.adresse.text().strip()
        if texte_adresse:
            resultat = geocoder_adresse(texte_adresse)
            if resultat is None:
                raise ValueError(f"Adresse introuvable : '{texte_adresse}'")
            lat, lon = resultat

        k = int(self.k_choisi.currentText())
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
```

- [ ] **Step 2: Wire the tab into `main_window.py`**

Modify `Interface_Graphique/main_window.py`: add the import and replace the B2 placeholder line.

```python
from Interface_Graphique.onglets.onglet_b2 import OngletB2
```

```python
self.tabs.addTab(OngletB2(), "B2 — Clustering")
```
(replaces `self.tabs.addTab(_onglet_placeholder("B2 — a venir"), "B2 — Clustering")`)

- [ ] **Step 3: Manually verify with raw lat/lon (no network dependency)**

Run: `python3 Interface_Graphique/main.py`
In the app: click "B2 — Clustering" tab, leave Adresse empty, keep default lat/lon, K=5, click "Générer la carte".
Expected: progress bar appears, button disables; after a few seconds the progress bar hides, button re-enables, and the map (colored clusters + black star marker + legend box bottom-left) renders inside the tab. No traceback in terminal.

- [ ] **Step 4: Manually verify the address path (requires internet)**

In the app: type `10 rue de Rivoli, Paris` in Adresse, click "Générer la carte".
Expected: same as Step 3, map centers near Paris (48.85, 2.36).

- [ ] **Step 5: Manually verify the error path**

In the app: type `zzzznotarealplace1234` in Adresse, click "Générer la carte".
Expected: a `QMessageBox` warning appears saying the address wasn't found; app does not crash; button re-enables.

- [ ] **Step 6: Commit**

```bash
git add Interface_Graphique/onglets/onglet_b2.py Interface_Graphique/main_window.py
git commit -m "Add Onglet B2: geocoded clustering map with background worker"
```

---

### Task 7: Onglet B1 — Cartes implantation/chaleur

**Files:**
- Create: `Interface_Graphique/onglets/onglet_b1.py`
- Modify: `Interface_Graphique/main_window.py` (replace B1 placeholder with `OngletB1()`)

**Interfaces:**
- Consumes: `Besoin_Client_1.main.charger_donnees(chemin_csv) -> pd.DataFrame`.
- Consumes: `Besoin_Client_1.main.nettoyer_donnees(df) -> pd.DataFrame`.
- Consumes: `Besoin_Client_1.main.encoder_implantation(df_b1, chemin_encoder) -> pd.DataFrame`.
- Consumes: `Besoin_Client_1.main.generer_carte_implantation(df_source, chemin_sortie, message_succes, plafond_par_groupe=8000) -> folium.Map` (saves HTML as a side effect).
- Consumes: `Besoin_Client_1.main.generer_carte_chaleur(df_b1, chemin_sortie) -> None` (saves HTML as a side effect).
- Consumes: `Interface_Graphique.workers.FonctionWorker`.
- Produces: `onglet_b1.OngletB1(QWidget)` — self-contained.

- [ ] **Step 1: Write `onglet_b1.py`**

```python
# Interface_Graphique/onglets/onglet_b1.py
import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QWidget, QPushButton, QComboBox, QVBoxLayout, QProgressBar, QMessageBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView

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
```

- [ ] **Step 2: Wire the tab into `main_window.py`**

Modify `Interface_Graphique/main_window.py`: add the import and replace the B1 placeholder line. After this task, `_onglet_placeholder` is unused and its definition (plus the now-unneeded `QWidget`/`QLabel`/`QVBoxLayout` imports if nothing else uses them) can be removed — check first whether any tab still references it before deleting.

```python
from Interface_Graphique.onglets.onglet_b1 import OngletB1
```

```python
self.tabs.addTab(OngletB1(), "B1 — Cartes")
```

Final `main_window.py` (all 4 tabs wired, placeholder removed since B1-B4 all use real widgets now):

```python
# Interface_Graphique/main_window.py
from PySide6.QtWidgets import QMainWindow, QTabWidget
from Interface_Graphique.onglets.onglet_b1 import OngletB1
from Interface_Graphique.onglets.onglet_b2 import OngletB2
from Interface_Graphique.onglets.onglet_b3 import OngletB3
from Interface_Graphique.onglets.onglet_b4 import OngletB4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Projet IA — Bornes de recharge IRVE")
        self.resize(1100, 750)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(OngletB1(), "B1 — Cartes")
        self.tabs.addTab(OngletB2(), "B2 — Clustering")
        self.tabs.addTab(OngletB3(), "B3 — Implantation")
        self.tabs.addTab(OngletB4(), "B4 — Puissance")
```

- [ ] **Step 3: Manually verify**

Run: `python3 Interface_Graphique/main.py`
In the app: click "B1 — Cartes" tab, click "Générer les cartes".
Expected: progress bar shows briefly, then the filtrable map (colored markers, layer control top-right) renders. Switch the combo box to "Carte de chaleur" — the heatmap renders without re-running generation. No traceback.

- [ ] **Step 4: Commit**

```bash
git add Interface_Graphique/onglets/onglet_b1.py Interface_Graphique/main_window.py
git commit -m "Add Onglet B1: implantation/heatmap maps, wire all 4 tabs"
```

---

### Task 8: README for the GUI

**Files:**
- Create: `Interface_Graphique/README.md`

- [ ] **Step 1: Write the README**

```markdown
# Interface Graphique — Projet IA Bornes IRVE

Application desktop PySide6 qui regroupe les 4 besoins dans une seule fenêtre à onglets.
N'entraîne jamais de modèle : charge uniquement les `.pkl` déjà générés par chaque
`Besoin_Client_X/main.ipynb`.

## Prérequis

- Python 3.x
- Les 4 dossiers `Besoin_Client_1` à `4` doivent déjà contenir leurs fichiers `.pkl`
  (générés en exécutant chaque `main.ipynb` une fois).
- `Besoin_Client_1/export_IA.csv` et `Besoin_Client_2/export_IA.csv` présents (utilisés
  par les onglets B1/B2 pour générer les cartes).

## Installation

```bash
pip install -r Interface_Graphique/requirements.txt
```

## Lancement

Depuis la racine du repo :

```bash
python3 Interface_Graphique/main.py
```

## Onglets

- **B1 — Cartes** : génère la carte filtrable par implantation et la carte de chaleur
  (échantillonnées à 8000 marqueurs/groupe pour rester fluides).
- **B2 — Clustering** : saisie d'une adresse (géocodée via Nominatim, nécessite internet)
  ou de coordonnées lat/lon brutes, choix de K (5/6/7), génère la carte de clustering
  avec légende et popups.
- **B3 — Implantation** : formulaire de caractéristiques de borne → prédit le type
  d'implantation.
- **B4 — Puissance** : formulaire de caractéristiques de borne → prédit la catégorie
  de puissance nominale.

## Si un onglet affiche une erreur "Modèles introuvables"

Le `.pkl` correspondant n'a pas encore été généré — ouvrir le notebook du besoin
concerné (`Besoin_Client_X/main.ipynb`) et l'exécuter entièrement une fois.
```

- [ ] **Step 2: Manually verify the README accuracy**

Read through `Interface_Graphique/README.md` and confirm every command listed (`pip install -r ...`, `python3 Interface_Graphique/main.py`) matches the actual files created in Tasks 1-7.

- [ ] **Step 3: Commit**

```bash
git add Interface_Graphique/README.md
git commit -m "Add README for Interface_Graphique"
```

---

## Self-Review Notes

- **Spec coverage:** all 4 tabs (B1-B4), `chdir` usage scoped correctly to B3/B4 only, `QThread` usage for B1/B2, error handling (missing `.pkl`, geocoding failure), sampling fix for B2 (caught during planning — spec originally assumed it existed) all have a task.
- **Placeholder scan:** no TBD/TODO; every step has complete code.
- **Type consistency:** `FonctionWorker.termine` always emits the wrapped function's return value (a `dict` for B1, a `str` path for B2, unused for B3/B4 since those run synchronously) — verified each consumer (`_sur_succes` in B1 and B2 tabs) expects the matching type.
