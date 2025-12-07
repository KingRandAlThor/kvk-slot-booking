import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def check_selection_results():
    """Vérifie les résultats de la sélection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("╔════════════════════════════════════════════════════════╗")
    print("║        RÉSULTATS DE LA SÉLECTION                      ║")
    print("╚════════════════════════════════════════════════════════╝\n")
    
    # Vérifier l'état de la sélection
    cur.execute("SELECT * FROM selection_state WHERE event_date = '2025-12-02';")
    state = cur.fetchone()
    
    if state:
        print(f"📅 Event: {state['event_date']}")
        print(f"⏰ Sélection prévue: {state['ready_at']}")
        print(f"✅ Complétée: {'OUI' if state['completed'] else 'NON'}")
        if state['completed']:
            print(f"🕐 Complétée le: {state['completed_at']}")
    else:
        print("⚠️ Aucun état de sélection trouvé")
    
    print("\n" + "="*60)
    print("🏆 JOUEURS SÉLECTIONNÉS (TOP 20)")
    print("="*60 + "\n")
    
    cur.execute("""
        SELECT player_name, speedup_days 
        FROM preregistrations 
        WHERE event_date = '2025-12-02' AND status = 'selected'
        ORDER BY speedup_days DESC, datetime(created_at) ASC;
    """)
    selected = cur.fetchall()
    
    if selected:
        for i, row in enumerate(selected, 1):
            print(f"{i:2d}. {row['player_name']:15s} - {row['speedup_days']:3d} jours de speedup")
        print(f"\nTotal: {len(selected)} joueurs sélectionnés")
    else:
        print("❌ Aucun joueur sélectionné (la sélection n'a pas encore eu lieu)")
    
    print("\n" + "="*60)
    print("⏳ LISTE D'ATTENTE")
    print("="*60 + "\n")
    
    cur.execute("""
        SELECT player_name, speedup_days, waitlist_position 
        FROM preregistrations 
        WHERE event_date = '2025-12-02' AND status = 'waitlist'
        ORDER BY waitlist_position ASC;
    """)
    waitlist = cur.fetchall()
    
    if waitlist:
        for row in waitlist:
            pos = row['waitlist_position']
            print(f"Position {pos}: {row['player_name']:15s} - {row['speedup_days']:3d} jours de speedup")
        print(f"\nTotal: {len(waitlist)} joueurs en attente")
    else:
        print("✅ Aucun joueur en attente")
    
    print("\n" + "="*60)
    print("📊 STATISTIQUES")
    print("="*60 + "\n")
    
    cur.execute("SELECT COUNT(*) as total FROM preregistrations WHERE event_date = '2025-12-02';")
    total = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as pending FROM preregistrations WHERE event_date = '2025-12-02' AND status = 'pending';")
    pending = cur.fetchone()['pending']
    
    print(f"Total des pré-inscriptions: {total}")
    print(f"Sélectionnés: {len(selected)}")
    print(f"En attente: {len(waitlist)}")
    print(f"En attente de sélection: {pending}")
    
    conn.close()

if __name__ == '__main__':
    check_selection_results()
