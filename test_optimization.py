#!/usr/bin/env python3
"""
Test script for optimization algorithm with 205 registrations
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta, timezone

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def generate_test_data():
    """Generate 205 test registrations with varying speedups and slot preferences"""
    print("🔧 Generating 205 test registrations...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Clear existing preregistrations for test
    event_date = "2025-12-02"
    event_day = "monday"
    cur.execute("DELETE FROM preregistrations WHERE event_date = ? AND event_day = ?;", (event_date, event_day))
    cur.execute("DELETE FROM slot_conflicts WHERE event_date = ? AND event_day = ?;", (event_date, event_day))
    
    # Generate time slots (48 slots from 00:00 to 23:30)
    slots = []
    for hour in range(24):
        for minute in [0, 30]:
            slot_time = f"2025-12-02T{hour:02d}:{minute:02d}:00+00:00"
            slots.append(slot_time)
    
    # Generate 205 players with varying speedups
    import random
    players = []
    
    # Distribution de speedups pour rendre le test réaliste
    # 20 joueurs avec 100+ speedups (top tier)
    for i in range(20):
        speedups = random.randint(100, 200)
        players.append({'name': f'TopPlayer{i+1}', 'speedups': speedups})
    
    # 50 joueurs avec 50-99 speedups (high tier)
    for i in range(50):
        speedups = random.randint(50, 99)
        players.append({'name': f'HighPlayer{i+1}', 'speedups': speedups})
    
    # 85 joueurs avec 25-49 speedups (mid tier)
    for i in range(85):
        speedups = random.randint(25, 49)
        players.append({'name': f'MidPlayer{i+1}', 'speedups': speedups})
    
    # 50 joueurs avec 20-24 speedups (low tier)
    for i in range(50):
        speedups = random.randint(20, 24)
        players.append({'name': f'LowPlayer{i+1}', 'speedups': speedups})
    
    # Insert into database
    now = datetime.now(timezone.utc)
    
    for idx, player in enumerate(players):
        # Chaque joueur sélectionne 3-10 créneaux aléatoires
        num_slots = random.randint(3, 10)
        preferred_slots = random.sample(slots, num_slots)
        preferred_slots_json = json.dumps(preferred_slots)
        
        created_at = (now - timedelta(minutes=205-idx)).isoformat()  # Stagger creation times
        
        cur.execute(
            'INSERT INTO preregistrations (event_date, event_day, player_name, speedup_days, preferred_slots, created_at, list_type) VALUES (?, ?, ?, ?, ?, ?, ?);',
            (event_date, event_day, player['name'], player['speedups'], preferred_slots_json, created_at, 'main')
        )
    
    conn.commit()
    
    # Set selection ready time to now + 2 minutes
    ready_at = (now + timedelta(minutes=2)).isoformat()
    cur.execute("INSERT OR REPLACE INTO selection_state (event_date, ready_at, completed) VALUES (?, ?, 0);", (event_date, ready_at))
    conn.commit()
    
    print(f"✅ Generated {len(players)} test registrations")
    print(f"⏰ Optimization will run at: {ready_at}")
    print(f"📊 Speedup distribution:")
    print(f"   - 100-200 days: 20 players")
    print(f"   - 50-99 days: 50 players")
    print(f"   - 25-49 days: 85 players")
    print(f"   - 20-24 days: 50 players")
    print(f"   Total slots available: {len(slots)}")
    
    conn.close()
    return event_date, event_day


def simulate_optimization(event_date, event_day):
    """Simulate the optimization algorithm and show expected results"""
    print("\n🔮 Simulating optimization algorithm...")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    # Get all preregistrations
    cur.execute(
        "SELECT id, player_name, speedup_days, preferred_slots, list_type FROM preregistrations WHERE event_date = ? AND event_day = ?;",
        (event_date, event_day)
    )
    preregistrations = cur.fetchall()
    
    # Build candidates list
    candidates = []
    for prereg in preregistrations:
        player_id = prereg['id']
        player_name = prereg['player_name']
        speedup_days = prereg['speedup_days']
        list_type = prereg['list_type']
        try:
            preferred_slots = json.loads(prereg['preferred_slots'])
        except:
            preferred_slots = []
        
        for slot_iso in preferred_slots:
            candidates.append({
                'player_id': player_id,
                'player_name': player_name,
                'slot_iso': slot_iso,
                'speedup_days': speedup_days,
                'list_type': list_type
            })
    
    # Sort by speedups (descending)
    candidates.sort(key=lambda x: x['speedup_days'], reverse=True)
    
    # Greedy assignment
    assigned_players = set()
    assigned_slots = {}
    conflicts = []
    
    for candidate in candidates:
        player_id = candidate['player_id']
        player_name = candidate['player_name']
        slot_iso = candidate['slot_iso']
        speedup_days = candidate['speedup_days']
        list_type = candidate['list_type']
        
        # If player already has a slot, skip
        if player_id in assigned_players:
            continue
        
        slot_key = f"{slot_iso}_{list_type}"
        
        # If slot already taken
        if slot_key in assigned_slots:
            existing = assigned_slots[slot_key]
            # Check for conflict (same speedups)
            if existing['speedup_days'] == speedup_days:
                # Find existing conflict or create new
                conflict_exists = False
                for c in conflicts:
                    if c['slot_iso'] == slot_iso and c['speedup_days'] == speedup_days:
                        if player_name not in c['player_names']:
                            c['player_names'].append(player_name)
                        conflict_exists = True
                        break
                
                if not conflict_exists:
                    conflicts.append({
                        'slot_iso': slot_iso,
                        'player_names': [existing['player_name'], player_name],
                        'speedup_days': speedup_days
                    })
            continue
        
        # Assign slot
        assigned_slots[slot_key] = {
            'player_id': player_id,
            'player_name': player_name,
            'speedup_days': speedup_days
        }
        assigned_players.add(player_id)
    
    # Show results
    print(f"\n📊 EXPECTED RESULTS:")
    print(f"=" * 80)
    print(f"Total registrations: {len(preregistrations)}")
    print(f"Total slot requests: {len(candidates)}")
    print(f"Players assigned slots: {len(assigned_players)}")
    print(f"Players without slots: {len(preregistrations) - len(assigned_players)}")
    print(f"Conflicts detected: {len(conflicts)}")
    print(f"Total speedup-days assigned: {sum(a['speedup_days'] for a in assigned_slots.values())}")
    
    # Show top 20 assignments
    print(f"\n🏆 TOP 20 SLOT ASSIGNMENTS (by speedups):")
    print(f"-" * 80)
    sorted_assignments = sorted(assigned_slots.values(), key=lambda x: x['speedup_days'], reverse=True)[:20]
    for idx, assignment in enumerate(sorted_assignments, 1):
        print(f"{idx:2d}. {assignment['player_name']:20s} - {assignment['speedup_days']:3d} days")
    
    # Show conflicts if any
    if conflicts:
        print(f"\n⚠️  CONFLICTS (require manual resolution):")
        print(f"-" * 80)
        for idx, conflict in enumerate(conflicts, 1):
            print(f"{idx}. Slot {conflict['slot_iso']} - {conflict['speedup_days']} days")
            print(f"   Players: {', '.join(conflict['player_names'])}")
    
    # Show players who didn't get slots
    unassigned = [p for p in preregistrations if p['id'] not in assigned_players]
    if unassigned:
        print(f"\n❌ PLAYERS WITHOUT SLOTS ({len(unassigned)}):")
        print(f"-" * 80)
        # Show first 10
        for idx, p in enumerate(sorted(unassigned, key=lambda x: x['speedup_days'], reverse=True)[:10], 1):
            slots_requested = len(json.loads(p['preferred_slots'])) if p['preferred_slots'] else 0
            print(f"{idx:2d}. {p['player_name']:20s} - {p['speedup_days']:3d} days - {slots_requested} slots requested")
        if len(unassigned) > 10:
            print(f"... and {len(unassigned) - 10} more players")
    
    conn.close()
    return len(assigned_players), len(conflicts)


if __name__ == '__main__':
    print("=" * 80)
    print("🧪 OPTIMIZATION ALGORITHM TEST - 205 REGISTRATIONS")
    print("=" * 80)
    
    event_date, event_day = generate_test_data()
    assigned_count, conflict_count = simulate_optimization(event_date, event_day)
    
    print(f"\n" + "=" * 80)
    print(f"✅ Test data generated successfully!")
    print(f"⏰ Algorithm will run automatically in 2 minutes")
    print(f"📊 Expected: {assigned_count} players get slots, {conflict_count} conflicts")
    print(f"🌐 Visit http://127.0.0.1:5000/event/monday to see the page")
    print(f"🔮 IMPORTANT: Avec l'algorithme optimal (hongrois), le résultat réel")
    print(f"   sera MEILLEUR que la simulation gloutonne ci-dessus!")
    print("=" * 80)
