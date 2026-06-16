
  BESOIN CLIENT 3 - Prediction du type d'implantation


DESCRIPTION
-----------
  Ce script predit le type d'implantation d'une borne de recharge
  a partir de ses caracteristiques techniques.

  Il utilise un modele de Regression Logistique,
  charge depuis les fichiers .pkl generes par le notebook.


UTILISATION
-----------
  1. Verifier que ces fichiers sont bien dans le meme dossier :
       - scaler_pretraitement_b3.pkl
       - modele_classification_b3.pkl

  2. Appeler la fonction avec les caracteristiques de la borne :

       resultat = predire_implantation(
           puissance   = 150.0,    # Puissance en kW
           nb_pdc      = 4,        # Nombre de points de charge
           gratuit     = "False",  # "True" ou "False"
           prise_ccs   = "True",   # "True" ou "False"
           prise_type2 = "False"   # "True" ou "False"
       )
       print(resultat)

SCRIPT D'EXEMPLE
----------------

  from predict_implantation import predire_implantation

  # Exemple 1 : Borne rapide type autoroute
  resultat = predire_implantation(
      puissance   = 150.0,
      nb_pdc      = 4,
      gratuit     = "False",
      prise_ccs   = "True",
      prise_type2 = "False"
  )
  print("Exemple 1 :", resultat)
  # => Station dediee a la recharge rapide

  # Exemple 2 : Borne lente en ville
  resultat = predire_implantation(
      puissance   = 7.0,
      nb_pdc      = 2,
      gratuit     = "True",
      prise_ccs   = "False",
      prise_type2 = "True"
  )
  print("Exemple 2 :", resultat)
  # => Voirie

  # Exemple 3 : Borne ultra-rapide
  resultat = predire_implantation(
      puissance   = 350.0,
      nb_pdc      = 12,
      gratuit     = "False",
      prise_ccs   = "True",
      prise_type2 = "False"
  )
  print("Exemple 3 :", resultat)
  # => Station dediee a la recharge rapide

CLASSES PREDITES POSSIBLES
--------------------------
  - Voirie
  - Parking public
  - Parking prive a usage public
  - Parking prive reserve a la clientele
  - Station dediee a la recharge rapide