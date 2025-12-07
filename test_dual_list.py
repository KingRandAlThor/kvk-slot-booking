import sqlite3
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def test_dual_list():
    """Test le système de double liste pour le jeudi"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Définir la date d'événement sur un jeudi
    # 2025-12-04 est un jeudi
    event_date = '2025-12-04'
    
    # Mettre à jour la config
    cur.execute("UPDATE config SET value = ? WHERE key = 'event_date';", (event_date,))
    conn.commit()
    
    print("=== TEST SYSTÈME DOUBLE LISTE (JEUDI) ===\n")
    print(f"Date d'événement: {event_date} (jeudi)\n")
    
    # Nettoyer les données existantes pour cet événement
    cur.execute("DELETE FROM preregistrations WHERE event_date = ?;", (event_date,))
    cur.execute("DELETE FROM selection_state WHERE event_date = ?;", (event_date,))
    conn.commit()
    
    now = datetime.now(timezone.utc)
    
    # Liste principale - 15 joueurs
    print("LISTE PRINCIPALE (Main List):")
    main_list = [
        ('Alice', 100), ('Bob', 95), ('Charlie', 90), ('David', 85), ('Eve', 80),
        ('Frank', 75), ('Grace', 70), ('Henry', 65), ('Ivy', 60), ('Jack', 55),
        ('Kate', 50), ('Leo', 45), ('Mia', 40), ('Noah', 35), ('Olivia', 30)
    ]
    
    for i, (name, days) in enumerate(main_list):
        created_at = (now - timedelta(minutes=len(main_list)-i)).isoformat()
        cur.execute(
            "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status, list_type) VALUES (?, ?, ?, ?, ?, ?);",
            (event_date, name, days, created_at, 'pending', 'main')
        )
        print(f"  ✓ {name}: {days} jours")
    
    print(f"\nTotal: {len(main_list)} joueurs\n")
    
    # Liste secondaire - 8 joueurs
    print("LISTE SECONDAIRE (Secondary List):")
    secondary_list = ['Paul', 'Quinn', 'Rose', 'Sam', 'Tina', 'Uma', 'Victor', 'Wendy']
    
    for i, name in enumerate(secondary_list):
        created_at = (now - timedelta(minutes=len(secondary_list)-i)).isoformat()
        cur.execute(
            "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status, list_type) VALUES (?, ?, ?, ?, ?, ?);",
            (event_date, name, 0, created_at, 'pending', 'secondary')
        )
        print(f"  ✓ {name}")
    
    print(f"\nTotal: {len(secondary_list)} joueurs\n")
    
    # Définir le temps de sélection dans le passé
    ready_at = (now - timedelta(minutes=1)).isoformat()
    cur.execute(
        "INSERT INTO selection_state (event_date, ready_at, completed) VALUES (?, ?, 0);",
        (event_date, ready_at)
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ Données de test créées!")
    print(f"   → {len(main_list)} joueurs dans la liste principale")
    print(f"   → {len(secondary_list)} joueurs dans la liste secondaire")
    print(f"   → Temps de sélection: {ready_at}")
    print(f"\n🔄 Rechargez http://127.0.0.1:5000 pour voir le résultat!")
    print(f"   Les Top 20 de la liste principale seront sélectionnés.")
    print(f"   Tous les joueurs de la liste secondaire pourront réserver.")

if __name__ == '__main__':
    test_dual_list()
