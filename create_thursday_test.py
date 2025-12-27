import sqlite3
from datetime import datetime, timezone, timedelta
import json
import random

db = sqlite3.connect('kvk.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

# Supprimer les anciennes données de test
cur.execute('DELETE FROM preregistrations WHERE event_day = "thursday";')
cur.execute('DELETE FROM reservations WHERE event_day = "thursday";')
db.commit()

# Date de l'événement jeudi
event_date = '2025-01-16T12:00:00+00:00'

# Générer 205 joueurs avec des speedups variés
print('Génération de 205 pré-inscriptions pour jeudi...')

# Distribution réaliste
# - TopPlayer (100-200 days): 10 joueurs
# - HighPlayer (50-99 days): 30 joueurs
# - MidPlayer (25-49 days): 80 joueurs
# - LowPlayer (20-24 days): 85 joueurs

players = []

# TopPlayer
for i in range(1, 11):
    speedup = random.randint(100, 200)
    players.append({'name': f'TopPlayer{i}', 'speedup': speedup})

# HighPlayer
for i in range(1, 31):
    speedup = random.randint(50, 99)
    players.append({'name': f'HighPlayer{i}', 'speedup': speedup})

# MidPlayer
for i in range(1, 81):
    speedup = random.randint(25, 49)
    players.append({'name': f'MidPlayer{i}', 'speedup': speedup})

# LowPlayer
for i in range(1, 86):
    speedup = random.randint(20, 24)
    players.append({'name': f'LowPlayer{i}', 'speedup': speedup})

# Générer les créneaux (48 créneaux de 30 minutes entre 12:00 et 12:00 le lendemain)
start_time = datetime.fromisoformat('2025-01-16T12:00:00+00:00')
slots = []
for i in range(48):
    slot_time = start_time + timedelta(minutes=30 * i)
    slots.append(slot_time.isoformat())

# Insérer les pré-inscriptions
for player in players:
    # Chaque joueur choisit entre 5 et 15 créneaux au hasard
    num_slots = random.randint(5, 15)
    preferred_slots = random.sample(slots, num_slots)
    
    now = datetime.now(timezone.utc)
    cur.execute(
        'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, preferred_slots, list_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?);',
        (event_date, 'thursday', player['name'], player['speedup'], json.dumps(preferred_slots), 'main', now.isoformat())
    )

db.commit()

# Vérifier
cur.execute('SELECT COUNT(*) as total FROM preregistrations WHERE event_day = "thursday";')
total = cur.fetchone()['total']
print(f'✅ {total} pré-inscriptions créées pour jeudi')

# Afficher la distribution des speedups
cur.execute('SELECT COUNT(*) as count FROM preregistrations WHERE event_day = "thursday" AND speedup_days >= 100;')
top = cur.fetchone()['count']
cur.execute('SELECT COUNT(*) as count FROM preregistrations WHERE event_day = "thursday" AND speedup_days >= 50 AND speedup_days < 100;')
high = cur.fetchone()['count']
cur.execute('SELECT COUNT(*) as count FROM preregistrations WHERE event_day = "thursday" AND speedup_days >= 25 AND speedup_days < 50;')
mid = cur.fetchone()['count']
cur.execute('SELECT COUNT(*) as count FROM preregistrations WHERE event_day = "thursday" AND speedup_days >= 20 AND speedup_days < 25;')
low = cur.fetchone()['count']

print(f'\nDistribution des speedups:')
print(f'  TopPlayer (100-200 days): {top}')
print(f'  HighPlayer (50-99 days): {high}')
print(f'  MidPlayer (25-49 days): {mid}')
print(f'  LowPlayer (20-24 days): {low}')

db.close()
print('\n✅ Données de test créées avec succès !')
