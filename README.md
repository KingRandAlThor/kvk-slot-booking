# KVK Slot Booking

Application web Flask pour organiser la réservation de créneaux lors des événements KVK du jeu Kingshot : les joueurs se pré-inscrivent, les meilleurs sont sélectionnés automatiquement, puis réservent leur créneau.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)

## Fonctionnement

1. **Pré-inscription** : chaque joueur indique son nom et son nombre de jours de speedup.
2. **Sélection automatique** : après le délai configuré (1 jour par défaut), les 20 premiers sont retenus, classés par speedup décroissant puis par ordre d'inscription. Les autres passent en liste d'attente avec leur position visible.
3. **Réservation** : seuls les joueurs sélectionnés peuvent choisir un créneau.
4. **Administration** : une page protégée par mot de passe permet de configurer la semaine d'événement, déplacer ou supprimer des réservations et consulter le journal des suppressions.

La sélection se déclenche toute seule au chargement de la page, sans tâche planifiée. Le détail de cette évolution est dans [CHANGEMENTS.md](CHANGEMENTS.md).

## Installation

```bash
git clone https://github.com/KingRandAlThor/kvk-slot-booking.git
cd kvk-slot-booking
python -m venv .venv
.venv\Scripts\activate          # Windows ; sous Linux : source .venv/bin/activate
pip install -r requirements.txt
python init_db.py               # crée la base SQLite kvk.db
python app.py                   # http://127.0.0.1:5000
```

## Configuration

Deux variables d'environnement, à définir avant de lancer l'application :

| Variable | Rôle |
|---|---|
| `ADMIN_PASSWORD` | Mot de passe des actions d'administration. Sans valeur, ces actions sont refusées. |
| `SECRET_KEY` | Clé de signature des sessions Flask. À définir en production. |

Les réglages de l'événement (nombre de sélectionnés, speedup minimum, types d'événement par jour) sont en haut de `app.py` : `SELECTION_TOP_N`, `SLOT_MIN_SPEEDUP_DAYS`, `EVENT_TYPES`.

## Structure

| Fichier | Rôle |
|---|---|
| `app.py` | Routes Flask, logique de sélection et de réservation |
| `init_db.py` | Création et mise à jour du schéma SQLite |
| `view_deletion_log.py` | Affiche le journal des réservations supprimées |
| `wsgi.py` | Point d'entrée WSGI pour l'hébergement |
| `templates/`, `static/` | Pages HTML et feuilles de style (thème de fin d'année inclus) |

## Déploiement

Le déploiement sur PythonAnywhere est décrit dans [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md).
