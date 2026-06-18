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
