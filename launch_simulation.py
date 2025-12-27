import sqlite3
import os
import time
from datetime import datetime, timezone, timedelta
import urllib.request

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def clear_test_data():
    """Nettoie les données de test existantes"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Supprimer les anciennes pré-inscriptions de test
    cur.execute("DELETE FROM preregistrations WHERE event_date >= ?", (datetime.now().strftime('%Y-%m-%d'),))
    cur.execute("DELETE FROM selection_state WHERE event_date >= ?", (datetime.now().strftime('%Y-%m-%d'),))
    
    conn.commit()
    conn.close()
    print("✓ Données de test nettoyées")

def create_test_preregistrations():
    """Crée des pré-inscriptions de test"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Date de l'événement dans 45 secondes
    event_time = datetime.now(timezone.utc) + timedelta(seconds=45)
    event_date = event_time.strftime('%Y-%m-%d')
    ready_at = event_time.isoformat()
    
    print(f"\n📅 Événement programmé pour: {event_time.strftime('%H:%M:%S')}")
    print(f"   (dans 45 secondes)\n")
    
    # Créer l'état de sélection
    cur.execute(
        "INSERT INTO selection_state (event_date, ready_at, completed) VALUES (?, ?, 0);",
        (event_date, ready_at)
    )
    
    # Liste de joueurs de test avec leurs speedup
    test_players = [
        ('Alice', 50, '18:00,19:00,20:00'),
        ('Bob', 45, '18:00,19:00'),
        ('Charlie', 40, '19:00,20:00,21:00'),
        ('David', 35, '18:00,20:00'),
        ('Eve', 30, '19:00,21:00'),
        ('Frank', 25, '20:00,21:00'),
        ('Grace', 20, '18:00,19:00,20:00'),
        ('Henry', 15, '19:00,20:00'),
        ('Ivy', 10, '18:00,21:00'),
        ('Jack', 5, '19:00,20:00,21:00'),
        ('Kate', 50, '18:00,19:00'),
        ('Leo', 45, '19:00,20:00,21:00'),
        ('Mia', 40, '18:00,20:00'),
        ('Noah', 35, '19:00,21:00'),
        ('Olivia', 30, '18:00,19:00,20:00'),
        ('Paul', 25, '19:00,20:00'),
        ('Quinn', 20, '18:00,20:00,21:00'),
        ('Rachel', 15, '19:00,21:00'),
        ('Sam', 10, '18:00,19:00,20:00'),
        ('Tina', 5, '19:00,20:00,21:00'),
        ('Uma', 50, '18:00,20:00'),
        ('Victor', 45, '19:00,21:00'),
        ('Wendy', 40, '18:00,19:00,20:00'),
        ('Xavier', 35, '19:00,20:00'),
        ('Yara', 30, '18:00,20:00,21:00'),
    ]
    
    now = datetime.now(timezone.utc).isoformat()
    
    print("Création des pré-inscriptions:")
    for name, days, slots in test_players:
        cur.execute(
            """INSERT INTO preregistrations 
               (event_date, event_day, player_name, speedup_days, preferred_slots, created_at, status, list_type) 
               VALUES (?, 'monday', ?, ?, ?, ?, 'pending', 'main');""",
            (event_date, name, days, slots, now)
        )
        print(f"  ✓ {name}: {days} jours, slots={slots}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ {len(test_players)} pré-inscriptions créées!")
    print(f"✓ Sélection programmée pour: {ready_at}")
    
    return ready_at

def countdown(seconds):
    """Affiche un compte à rebours"""
    print(f"\n⏱️  DÉMARRAGE DE LA SIMULATION DANS:")
    for i in range(seconds, 0, -1):
        if i <= 10 or i % 5 == 0:
            print(f"    {i} secondes...")
        time.sleep(1)
    print("\n🚀 LANCEMENT!")

def trigger_selection():
    """Déclenche la sélection en faisant une requête à l'app"""
    print("\n📡 Déclenchement de la sélection automatique...")
    try:
        with urllib.request.urlopen('http://127.0.0.1:5000') as response:
            print(f"✓ Requête envoyée (HTTP {response.status})")
            print("✓ La sélection devrait être en cours!")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == '__main__':
    print("╔════════════════════════════════════════════╗")
    print("║   SIMULATION DE SÉLECTION AUTOMATIQUE     ║")
    print("╚════════════════════════════════════════════╝\n")
    
    # Nettoyer et créer les données
    clear_test_data()
    ready_at = create_test_preregistrations()
    
    # Compte à rebours
    countdown(45)
    
    # Déclencher la sélection
    trigger_selection()
    
    # Attendre un peu pour que la sélection se termine
    print("\n⏳ Attente de la fin de la sélection (5 secondes)...\n")
    time.sleep(5)
    
    # Afficher les résultats
    print("╔════════════════════════════════════════════╗")
    print("║         RÉSULTATS DE LA SÉLECTION         ║")
    print("╚════════════════════════════════════════════╝\n")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("SELECT event_date FROM selection_state WHERE ready_at = ?", (ready_at,))
    result = cur.fetchone()
    if result:
        event_date = result[0]
        
        # Afficher les sélectionnés
        cur.execute("""
            SELECT player_name, speedup_days, assigned_slot 
            FROM preregistrations 
            WHERE event_date = ? AND status = 'selected' AND list_type = 'main'
            ORDER BY speedup_days DESC
        """, (event_date,))
        selected = cur.fetchall()
        
        print(f"✅ LISTE PRINCIPALE - Sélectionnés ({len(selected)}):")
        for name, days, slot in selected:
            print(f"   {name}: {days} jours → {slot if slot else 'N/A'}")
        
        # Afficher la liste d'attente
        cur.execute("""
            SELECT player_name, speedup_days, waitlist_position 
            FROM preregistrations 
            WHERE event_date = ? AND status = 'waitlist' AND list_type = 'main'
            ORDER BY waitlist_position
        """, (event_date,))
        waitlist = cur.fetchall()
        
        print(f"\n⏳ LISTE D'ATTENTE ({len(waitlist)}):")
        for name, days, pos in waitlist:
            print(f"   #{pos}: {name} ({days} jours)")
    
    conn.close()
    
    print("\n✨ Simulation terminée!")
