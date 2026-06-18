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
