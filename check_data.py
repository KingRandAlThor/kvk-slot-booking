import sqlite3

db = sqlite3.connect('kvk.db')
cur = db.cursor()

for day in ['monday', 'tuesday', 'thursday']:
    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = ?;', (day,))
    count = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = ? AND assigned_slot IS NOT NULL AND assigned_slot != "";', (day,))
    assigned = cur.fetchone()[0]
    
    print(f'{day.capitalize()}: {count} pré-inscriptions, {assigned} créneaux attribués')

db.close()
