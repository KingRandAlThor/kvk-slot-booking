import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def check_db_schema():
    """Vérifie le schéma de la base de données"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("=== SCHÉMA DE LA BASE DE DONNÉES ===\n")
    
    # Liste des tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables présentes:")
    for table in tables:
        print(f"  - {table[0]}")
    
    print("\n=== DÉTAILS DES NOUVELLES TABLES ===\n")
    
    # Schéma de preregistrations
    if any('preregistrations' in t for t in tables):
        cur.execute("PRAGMA table_info(preregistrations);")
        columns = cur.fetchall()
        print("Table 'preregistrations':")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("⚠️ Table 'preregistrations' NON TROUVÉE")
    
    print()
    
    # Schéma de selection_state
    if any('selection_state' in t for t in tables):
        cur.execute("PRAGMA table_info(selection_state);")
        columns = cur.fetchall()
        print("Table 'selection_state':")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    else:
        print("⚠️ Table 'selection_state' NON TROUVÉE")
    
    print("\n=== DONNÉES ACTUELLES ===\n")
    
    # Vérifier les pré-inscriptions
    try:
        cur.execute("SELECT COUNT(*) FROM preregistrations;")
        count = cur.fetchone()[0]
        print(f"Pré-inscriptions: {count}")
        
        if count > 0:
            cur.execute("SELECT player_name, speedup_days, status, waitlist_position FROM preregistrations ORDER BY speedup_days DESC;")
            print("\nListe des pré-inscrits:")
            for row in cur.fetchall():
                pos = f" (position {row[3]})" if row[3] else ""
                print(f"  - {row[0]}: {row[1]} jours, status={row[2]}{pos}")
    except Exception as e:
        print(f"Erreur lors de la lecture des pré-inscriptions: {e}")
    
    print()
    
    # Vérifier l'état de sélection
    try:
        cur.execute("SELECT * FROM selection_state;")
        states = cur.fetchall()
        print(f"États de sélection: {len(states)}")
        for state in states:
            print(f"  Event: {state[0]}, Ready at: {state[1]}, Completed: {state[2]}")
    except Exception as e:
        print(f"Erreur lors de la lecture de selection_state: {e}")
    
    conn.close()

def simulate_preregistration():
    """Simule quelques pré-inscriptions pour tester"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    event_date = '2025-12-02'
    now = datetime.now(timezone.utc).isoformat()
    
    print("\n=== SIMULATION DE PRÉ-INSCRIPTIONS ===\n")
    
    test_players = [
        ('Player1', 50),
        ('Player2', 45),
        ('Player3', 40),
        ('Player4', 35),
        ('Player5', 30),
        ('Player6', 25),
        ('Player7', 20),
        ('Player8', 15),
    ]
    
    for name, days in test_players:
        try:
            cur.execute(
                "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status) VALUES (?, ?, ?, ?, ?);",
                (event_date, name, days, now, 'pending')
            )
            print(f"✓ {name} inscrit avec {days} jours")
        except Exception as e:
            print(f"✗ Erreur pour {name}: {e}")
    
    conn.commit()
    conn.close()
    print("\nPré-inscriptions simulées avec succès!")

if __name__ == '__main__':
    print("╔════════════════════════════════════════╗")
    print("║  TEST DU SYSTÈME DE PRÉ-INSCRIPTION   ║")
    print("╚════════════════════════════════════════╝\n")
    
    check_db_schema()
    
    response = input("\nVoulez-vous ajouter des pré-inscriptions de test ? (o/n): ")
    if response.lower() in ['o', 'oui', 'y', 'yes']:
        simulate_preregistration()
        print("\n" + "="*50)
        check_db_schema()
