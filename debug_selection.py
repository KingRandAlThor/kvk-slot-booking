import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def debug_selection():
    """Debug du système de sélection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("=" * 60)
    print("DEBUG - Système de sélection")
    print("=" * 60 + "\n")
    
    event_date = '2025-12-02'
    
    # Récupérer l'état
    cur.execute("SELECT * FROM selection_state WHERE event_date = ?;", (event_date,))
    state = cur.fetchone()
    
    if not state:
        print("❌ Aucun état de sélection trouvé")
        return
    
    print(f"État actuel:")
    print(f"  event_date: {state['event_date']}")
    print(f"  ready_at: {state['ready_at']}")
    print(f"  completed: {state['completed']}")
    print(f"  completed_at: {state['completed_at']}")
    
    print(f"\nMaintenant (UTC): {datetime.now(timezone.utc).isoformat()}")
    
    # Parser ready_at
    ready_at_str = state['ready_at']
    print(f"\nTentative de parsing: '{ready_at_str}'")
    
    try:
        # Essayer le parsing comme dans le code
        ready_at_dt = datetime.fromisoformat(ready_at_str).replace(tzinfo=timezone.utc)
        print(f"✓ Parsing réussi: {ready_at_dt}")
        
        now = datetime.now(timezone.utc)
        print(f"\nComparaison:")
        print(f"  now: {now}")
        print(f"  ready_at: {ready_at_dt}")
        print(f"  now < ready_at: {now < ready_at_dt}")
        print(f"  now >= ready_at: {now >= ready_at_dt}")
        
        if now >= ready_at_dt:
            print(f"\n✅ Le moment de sélection est atteint!")
            if state['completed']:
                print(f"⚠️ Mais la sélection est déjà complétée")
            else:
                print(f"🎯 La sélection devrait se déclencher!")
        else:
            diff = (ready_at_dt - now).total_seconds()
            print(f"\n⏰ Il reste {diff:.0f} secondes avant la sélection")
    except Exception as e:
        print(f"❌ Erreur de parsing: {e}")
    
    # Vérifier les pré-inscriptions
    cur.execute("SELECT COUNT(*) as cnt FROM preregistrations WHERE event_date = ?;", (event_date,))
    count = cur.fetchone()['cnt']
    print(f"\nPré-inscriptions pour cet événement: {count}")
    
    conn.close()

if __name__ == '__main__':
    debug_selection()
