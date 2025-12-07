import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def update_event_date():
    """Met à jour la date d'événement pour correspondre aux données de test"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("UPDATE config SET value = '2025-12-02' WHERE key = 'event_date';")
    conn.commit()
    
    print("✓ Date d'événement mise à jour: 2025-12-02")
    
    # Vérifier
    cur.execute("SELECT value FROM config WHERE key = 'event_date';")
    result = cur.fetchone()
    print(f"  Confirmation: {result[0]}")
    
    conn.close()

if __name__ == '__main__':
    update_event_date()
