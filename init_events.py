"""
Script d'initialisation pour les événements de la semaine.
Configure les dates d'événements et les dates d'ouverture des inscriptions.

Logique:
- Lundi (Construction): Événement le lundi, inscriptions ouvertes le dimanche, optimisation terminée le dimanche soir
- Mardi (Research): Événement le mardi, inscriptions ouvertes le lundi, optimisation terminée le lundi soir
- Jeudi (Troop Training): Événement le jeudi, inscriptions ouvertes le mercredi, optimisation terminée le mercredi soir
"""

import sqlite3
from datetime import datetime, timedelta, timezone

db = sqlite3.connect('kvk.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Fonction pour obtenir le prochain jour de la semaine
def get_next_weekday(target_weekday, from_date=None):
    """
    Retourne le prochain jour de la semaine spécifié.
    target_weekday: 0=Lundi, 1=Mardi, 3=Jeudi
    """
    if from_date is None:
        from_date = datetime.now(timezone.utc)
    
    days_ahead = target_weekday - from_date.weekday()
    if days_ahead <= 0:  # Le jour est passé cette semaine
        days_ahead += 7
    
    return from_date + timedelta(days=days_ahead)

# Date de référence: aujourd'hui
now = datetime.now(timezone.utc)
print(f"Date actuelle: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"Jour de la semaine: {now.strftime('%A')} (weekday={now.weekday()})")

# Configuration pour chaque jour
events_config = [
    {
        'day': 'monday',
        'weekday': 0,  # Lundi
        'name': 'Construction',
    },
    {
        'day': 'tuesday',
        'weekday': 1,  # Mardi
        'name': 'Research',
    },
    {
        'day': 'thursday',
        'weekday': 3,  # Jeudi
        'name': 'Troop Training',
    }
]

print("\n" + "="*60)
print("INITIALISATION DES ÉVÉNEMENTS")
print("="*60)

for event in events_config:
    day = event['day']
    weekday = event['weekday']
    name = event['name']
    
    # Calculer le prochain jour d'événement
    event_date = get_next_weekday(weekday, now)
    event_date_str = event_date.strftime('%Y-%m-%d')
    
    # L'inscription ouvre la veille à 12:00 UTC
    registration_open = event_date - timedelta(days=1)
    registration_open = registration_open.replace(hour=12, minute=0, second=0, microsecond=0)
    registration_open_str = registration_open.isoformat()
    
    print(f"\n{name.upper()} ({day.capitalize()}):")
    print(f"  Event date: {event_date_str} ({event_date.strftime('%A')})")
    print(f"  Registration opens: {registration_open.strftime('%Y-%m-%d %H:%M UTC')} ({registration_open.strftime('%A')})")
    
    # Sauvegarder dans la base de données
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?);",
                (f'event_date_{day}', event_date_str))
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?);",
                (f'registration_open_{day}', registration_open_str))

db.commit()

print("\n" + "="*60)
print("✅ Configuration sauvegardée dans la base de données!")
print("="*60)

# Vérifier la configuration
print("\nVérification de la configuration:")
for event in events_config:
    day = event['day']
    cur.execute("SELECT value FROM config WHERE key = ?;", (f'event_date_{day}',))
    event_date = cur.fetchone()['value']
    cur.execute("SELECT value FROM config WHERE key = ?;", (f'registration_open_{day}',))
    reg_open = cur.fetchone()['value']
    print(f"  {day}: event_date={event_date}, registration_open={reg_open}")

db.close()
print("\n✅ Initialisation terminée!")
