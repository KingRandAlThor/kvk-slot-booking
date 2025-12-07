import sqlite3
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def add_test_data():
    """Ajoute des données de test pour pré-inscriptions"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    event_date = '2025-12-02'
    now = datetime.now(timezone.utc)
    
    print("Ajout de pré-inscriptions de test...\n")
    
    # Ajout de 25 joueurs pour tester le système (20 sélectionnés + 5 en attente)
    test_players = [
        ('Alice', 100),
        ('Bob', 95),
        ('Charlie', 90),
        ('David', 85),
        ('Eve', 80),
        ('Frank', 75),
        ('Grace', 70),
        ('Henry', 65),
        ('Ivy', 60),
        ('Jack', 55),
        ('Kate', 50),
        ('Leo', 45),
        ('Mia', 40),
        ('Noah', 35),
        ('Olivia', 30),
        ('Paul', 29),
        ('Quinn', 28),
        ('Rose', 27),
        ('Sam', 26),
        ('Tina', 25),
        # 5 suivants en attente
        ('Uma', 24),
        ('Victor', 23),
        ('Wendy', 22),
        ('Xavier', 21),
        ('Yuki', 20),
    ]
    
    for i, (name, days) in enumerate(test_players):
        created_at = (now - timedelta(minutes=len(test_players)-i)).isoformat()
        try:
            cur.execute(
                "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status) VALUES (?, ?, ?, ?, ?);",
                (event_date, name, days, created_at, 'pending')
            )
            print(f"✓ {name}: {days} jours de speedup")
        except Exception as e:
            print(f"✗ Erreur pour {name}: {e}")
    
    # Définir le moment de sélection (dans le passé pour déclencher la sélection immédiatement)
    ready_at = (now - timedelta(minutes=1)).isoformat()
    cur.execute(
        "INSERT OR REPLACE INTO selection_state (event_date, ready_at, completed) VALUES (?, ?, 0);",
        (event_date, ready_at)
    )
    print(f"\n✓ Temps de sélection défini: {ready_at}")
    print(f"  (dans le passé pour déclencher la sélection immédiatement)")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ {len(test_players)} pré-inscriptions ajoutées!")
    print(f"   → Les 20 premiers seront sélectionnés")
    print(f"   → Les 5 derniers seront en liste d'attente")
    print("\n🔄 Rechargez la page web pour voir le résultat de la sélection!")

if __name__ == '__main__':
    add_test_data()
