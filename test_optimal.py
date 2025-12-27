#!/usr/bin/env python3
"""
Test pour vérifier que l'algorithme trouve vraiment la solution optimale
"""
import sqlite3
import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def test_scenario():
    """
    Scénario:
    - Joueur 1 : 80 speedups → veut slot 1 et 2
    - Joueur 2 : 79 speedups → veut slot 1
    - Joueur 3 : 45 speedups → veut slot 2
    
    Solution optimale attendue:
    - Joueur 1 → Slot 2 (80)
    - Joueur 2 → Slot 1 (79)
    Total: 159 speedups
    """
    print("🧪 Test de l'algorithme optimal")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Clear test data
    event_date = "2025-12-03"
    event_day = "tuesday"
    cur.execute("DELETE FROM preregistrations WHERE event_date = ? AND event_day = ?;", (event_date, event_day))
    
    now = datetime.now(timezone.utc)
    
    # Créer les slots
    slot1 = "2025-12-03T08:00:00+00:00"
    slot2 = "2025-12-03T10:00:00+00:00"
    
    # Joueur 1 : 80 speedups, veut slot 1 et 2
    cur.execute(
        'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, preferred_slots, created_at, list_type) VALUES (?, ?, ?, ?, ?, ?, ?);',
        (event_date, event_day, "Joueur1", 80, json.dumps([slot1, slot2]), now.isoformat(), 'main')
    )
    
    # Joueur 2 : 79 speedups, veut slot 1
    cur.execute(
        'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, preferred_slots, created_at, list_type) VALUES (?, ?, ?, ?, ?, ?, ?);',
        (event_date, event_day, "Joueur2", 79, json.dumps([slot1]), now.isoformat(), 'main')
    )
    
    # Joueur 3 : 45 speedups, veut slot 2
    cur.execute(
        'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, preferred_slots, created_at, list_type) VALUES (?, ?, ?, ?, ?, ?, ?);',
        (event_date, event_day, "Joueur3", 45, json.dumps([slot2]), now.isoformat(), 'main')
    )
    
    conn.commit()
    
    print("📋 Configuration:")
    print("  - Joueur1: 80 speedups → veut slots [08:00, 10:00]")
    print("  - Joueur2: 79 speedups → veut slots [08:00]")
    print("  - Joueur3: 45 speedups → veut slots [10:00]")
    print()
    
    # Importer la fonction d'optimisation
    import sys
    sys.path.insert(0, BASE_DIR)
    from app import app, optimize_slot_assignments
    
    # Exécuter l'optimisation dans le contexte Flask
    print("⚙️  Exécution de l'algorithme optimal...")
    with app.app_context():
        optimize_slot_assignments(event_date, event_day)
    
    # Vérifier les résultats
    cur.execute(
        "SELECT player_name, speedup_days, assigned_slot FROM preregistrations WHERE event_date = ? AND event_day = ? ORDER BY speedup_days DESC;",
        (event_date, event_day)
    )
    results = cur.fetchall()
    
    print("\n📊 RÉSULTATS:")
    print("=" * 80)
    total_speedups = 0
    for r in results:
        if r['assigned_slot']:
            slot_time = r['assigned_slot'].split('T')[1][:5]
            print(f"✅ {r['player_name']}: {r['speedup_days']} speedups → Slot {slot_time}")
            total_speedups += r['speedup_days']
        else:
            print(f"❌ {r['player_name']}: {r['speedup_days']} speedups → Pas de slot")
    
    print(f"\n🎯 Total speedups optimisé: {total_speedups} jours")
    
    if total_speedups == 159:
        print("✅ SUCCÈS! L'algorithme a trouvé la solution optimale (159)")
    elif total_speedups == 125:
        print("❌ ÉCHEC! L'algorithme a utilisé l'approche gloutonne (125)")
    else:
        print(f"⚠️  Résultat inattendu: {total_speedups}")
    
    conn.close()

if __name__ == '__main__':
    test_scenario()
