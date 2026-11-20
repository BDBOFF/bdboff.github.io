#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Petit serveur du tableau de bord mural (iPad mini, iOS 9).

- Python 3 standard uniquement : rien à installer (pas de pip).
- Sert la page (dossier public/) et un seul point de données : /api/donnees
- C'est ce serveur qui ira chercher la météo, l'agenda et l'état des volets.
  La tablette ne fait qu'afficher.
- Cohabitation avec Home Assistant : ce serveur tourne sur son propre port
  (8765 par défaut), ne modifie rien dans Home Assistant et, quand on
  branchera les volets, se contentera de LIRE leur état via l'API de HA.

Étape actuelle : toutes les sources sont en mode "exemple" (données fictives).
On branchera les vraies sources une par une ensuite.

Lancement :  python3 serveur.py     puis ouvrir http://<ip-de-l-ordinateur>:8765
"""

import datetime
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

DOSSIER = os.path.dirname(os.path.abspath(__file__))
DOSSIER_PUBLIC = os.path.join(DOSSIER, "public")


# --------------------------------------------------------------------------
# Lecture du fichier .env (sans dépendance externe)
# --------------------------------------------------------------------------
def lire_env(chemin):
    valeurs = {}
    if not os.path.exists(chemin):
        return valeurs
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, val = ligne.split("=", 1)
            valeurs[cle.strip()] = val.strip().strip('"').strip("'")
    return valeurs


CONFIG = lire_env(os.path.join(DOSSIER, ".env"))
PORT = int(CONFIG.get("PORT", "8765"))

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# --------------------------------------------------------------------------
# Sources de données — VERSION EXEMPLE (fictive)
# Chaque fonction sera remplacée par la vraie source, une par une.
# --------------------------------------------------------------------------
def meteo_exemple():
    # Vraie source prévue : Open-Meteo (gratuit, sans clé),
    # La Roquette-sur-Siagne : latitude 43.599, longitude 6.955
    aujourd_hui = datetime.date.today()
    previsions = []
    exemples = [("☀️", 19, 9), ("⛅", 17, 10), ("🌧", 14, 9)]
    for i, (icone, tmax, tmin) in enumerate(exemples):
        jour = aujourd_hui + datetime.timedelta(days=i + 1)
        previsions.append({
            "jour": JOURS[jour.weekday()][:3].capitalize() + ".",
            "icone": icone, "max": tmax, "min": tmin,
        })
    return {
        "exemple": True,
        "lieu": "La Roquette-sur-Siagne",
        "temperature": 16,
        "icone": "⛅",
        "description": "Éclaircies",
        "max": 18, "min": 8,
        "pluie": 10,          # probabilité de pluie (%)
        "vent": 12,           # km/h
        "previsions": previsions,
    }


def agenda_exemple():
    # Vraie source prévue : lien d'abonnement iCal de FamilyWall (.env)
    return {
        "exemple": True,
        "evenements": [
            {"heure": "08:15", "titre": "École", "qui": "Papa"},
            {"heure": "12:30", "titre": "Déjeuner Mamie", "qui": "Famille"},
            {"heure": "17:00", "titre": "Judo", "qui": "Léo"},
            {"heure": "19:30", "titre": "Dentiste", "qui": "Maman"},
        ],
    }


def volets_exemple():
    # Vraie source prévue : API de Home Assistant (lecture seule),
    # entités cover.* créées par l'intégration Somfy (TaHoma / Overkiz)
    return {
        "exemple": True,
        "volets": [
            {"nom": "Salon", "position": 100},
            {"nom": "Cuisine", "position": 100},
            {"nom": "Chambre", "position": 0},
            {"nom": "Bureau", "position": 50},
        ],
    }


def soleil_exemple():
    # Tuile proposée en plus : lever / coucher du soleil + fête du jour.
    # Vraie source prévue : calcul local (aucune clé) + liste des saints.
    return {
        "exemple": True,
        "lever": "07:31",
        "coucher": "17:03",
        "fete": "Edmond",
    }


def collecter_donnees():
    return {
        "maj": datetime.datetime.now().strftime("%H:%M"),
        "meteo": meteo_exemple(),
        "agenda": agenda_exemple(),
        "volets": volets_exemple(),
        "soleil": soleil_exemple(),
    }


# --------------------------------------------------------------------------
# Serveur HTTP
# --------------------------------------------------------------------------
class Gestionnaire(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOSSIER_PUBLIC, **kwargs)

    def end_headers(self):
        # Jamais de cache : la tablette récupère toujours la dernière version
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def do_GET(self):
        chemin = self.path.split("?", 1)[0]
        if chemin == "/api/donnees":
            corps = json.dumps(collecter_donnees(), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corps)))
            self.end_headers()
            self.wfile.write(corps)
            return
        if chemin == "/api/ping":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return
        return super().do_GET()

    def log_message(self, fmt, *args):
        # Journal discret : seulement les erreurs
        if len(args) > 1 and str(args[1]).startswith(("4", "5")):
            sys.stderr.write("[tableau-de-bord] " + (fmt % args) + "\n")


if __name__ == "__main__":
    serveur = ThreadingHTTPServer(("0.0.0.0", PORT), Gestionnaire)
    print("Tableau de bord servi sur http://localhost:%d  (Ctrl+C pour arrêter)" % PORT)
    try:
        serveur.serve_forever()
    except KeyboardInterrupt:
        pass
