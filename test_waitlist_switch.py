import sqlite3
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def test_waitlist_switch():
    """Test le basculement de la liste d'attente vers la liste secondaire"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    event_date = '2025-12-04'
    
    # Mettre à jour la config
    cur.execute("UPDATE config SET value = ? WHERE key = 'event_date';", (event_date,))
    conn.commit()
    
    print("=== TEST BASCULEMENT LISTE D'ATTENTE → SECONDAIRE ===\n")
    print(f"Date d'événement: {event_date} (jeudi)\n")
    
    # Nettoyer
    cur.execute("DELETE FROM preregistrations WHERE event_date = ?;", (event_date,))
    cur.execute("DELETE FROM selection_state WHERE event_date = ?;", (event_date,))
    conn.commit()
    
    now = datetime.now(timezone.utc)
    
    # 25 joueurs dans la liste principale (Top 20 + 5 en attente)
    print("CRÉATION DE 25 JOUEURS:")
    players = [
        ('Alice', 100), ('Bob', 95), ('Charlie', 90), ('David', 85), ('Eve', 80),
        ('Frank', 75), ('Grace', 70), ('Henry', 65), ('Ivy', 60), ('Jack', 55),
        ('Kate', 50), ('Leo', 45), ('Mia', 40), ('Noah', 35), ('Olivia', 30),
        ('Paul', 29), ('Quinn', 28), ('Rose', 27), ('Sam', 26), ('Tina', 25),
        # 5 en attente
        ('Uma', 24), ('Victor', 23), ('Wendy', 22), ('Xavier', 21), ('Yuki', 20)
    ]
    
    for i, (name, days) in enumerate(players):
        created_at = (now - timedelta(minutes=len(players)-i)).isoformat()
        cur.execute(
            "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status, list_type) VALUES (?, ?, ?, ?, ?, ?);",
            (event_date, name, days, created_at, 'pending', 'main')
        )
    
    print(f"  ✓ {len(players)} joueurs ajoutés à la liste principale\n")
    
    # Définir et déclencher la sélection
    ready_at = (now - timedelta(minutes=1)).isoformat()
    cur.execute(
        "INSERT INTO selection_state (event_date, ready_at, completed) VALUES (?, ?, 0);",
        (event_date, ready_at)
    )
    conn.commit()
    
    print("SIMULATION DE LA SÉLECTION:")
    print("  (Normalement déclenchée par le rechargement de la page)\n")
    
    # Simuler la sélection
    cur.execute(
        """
        SELECT id FROM preregistrations
        WHERE event_date = ? AND list_type = 'main'
        ORDER BY speedup_days DESC, datetime(created_at) ASC;
        """,
        (event_date,)
    )
    rows = cur.fetchall()
    selected_ids = [r[0] for r in rows[:20]]
    waitlist_ids = [r[0] for r in rows[20:]]
    
    if selected_ids:
        placeholders = ','.join('?' * len(selected_ids))
        cur.execute(
            f"UPDATE preregistrations SET status = 'selected', waitlist_position = NULL WHERE id IN ({placeholders});",
            selected_ids
        )
    
    if waitlist_ids:
        for pos, pid in enumerate(waitlist_ids, start=1):
            cur.execute("UPDATE preregistrations SET status = 'waitlist', waitlist_position = ? WHERE id = ?;", (pos, pid))
    
    cur.execute("UPDATE selection_state SET completed = 1, completed_at = ? WHERE event_date = ?;", (now.isoformat(), event_date))
    conn.commit()
    
    print("RÉSULTAT:")
    cur.execute("SELECT player_name FROM preregistrations WHERE event_date = ? AND status = 'selected' AND list_type = 'main' ORDER BY speedup_days DESC;", (event_date,))
    selected = cur.fetchall()
    print(f"  ✓ {len(selected)} sélectionnés: {', '.join([s[0] for s in selected[:3]])}... à {selected[-1][0]}")
    
    cur.execute("SELECT player_name, waitlist_position FROM preregistrations WHERE event_date = ? AND status = 'waitlist' ORDER BY waitlist_position ASC;", (event_date,))
    waitlist = cur.fetchall()
    print(f"  ✓ {len(waitlist)} en attente: {', '.join([f'{w[0]} (pos.{w[1]})' for w in waitlist])}")
    
    print(f"\n📋 Après sélection, les joueurs en attente verront un bouton")
    print(f"   '🔄 Switch to Secondary List' pour garantir une réservation!\n")
    
    conn.close()
    
    print("✅ Données prêtes!")
    print("🔄 Rechargez http://127.0.0.1:5000 pour tester le basculement!")

if __name__ == '__main__':
    test_waitlist_switch()
