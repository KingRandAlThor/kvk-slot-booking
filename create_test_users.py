#!/usr/bin/env python3
"""Script to create realistic test data for Thursday dual-list event."""

import sqlite3
import os
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, 'kvk.db')

def create_test_data():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    
    # Set event date to next Thursday (2025-12-11)
    event_date = '2025-12-11'
    
    print(f"📅 Setting event date to {event_date} (Thursday - Dual List)")
    cur.execute("INSERT OR REPLACE INTO config (key, value) VALUES ('event_date', ?);", (event_date,))
    
    # Clear existing data for this event
    print("🧹 Clearing existing data...")
    cur.execute("DELETE FROM preregistrations WHERE event_date = ?;", (event_date,))
    cur.execute("DELETE FROM reservations WHERE slot_start LIKE ?;", (f"{event_date}%",))
    cur.execute("DELETE FROM selection_state WHERE event_date = ?;", (event_date,))
    db.commit()
    
    # Create 30 realistic players
    print("👥 Creating 30 test players...")
    now = datetime.now(timezone.utc).isoformat()
    
    players = [
        ("DragonKing", 150),
        ("WarLord99", 145),
        ("ShadowBlade", 140),
        ("IronFist", 135),
        ("ThunderStrike", 130),
        ("PhoenixRising", 125),
        ("NightWolf", 120),
        ("SteelHammer", 115),
        ("FireStorm", 110),
        ("IceQueen", 105),
        ("DarkKnight", 100),
        ("GoldenEagle", 95),
        ("CrimsonTide", 90),
        ("SilverArrow", 85),
        ("BlazeRunner", 80),
        ("StormBreaker", 75),
        ("MoonShadow", 70),
        ("StarGazer", 65),
        ("OceanWave", 60),
        ("MountainPeak", 55),
        ("DesertFox", 50),
        ("JungleLord", 45),
        ("ArcticWolf", 40),
        ("TropicThunder", 35),
        ("VolcanoKing", 30),
        ("GlacierQueen", 28),
        ("EarthShaker", 26),
        ("WindRunner", 24),
        ("TidalWave", 22),
        ("LavaFlow", 20),
    ]
    
    for player_name, speedup_days in players:
        cur.execute(
            "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status, list_type) VALUES (?, ?, ?, ?, 'pending', 'main');",
            (event_date, player_name, speedup_days, now)
        )
    
    db.commit()
    print(f"✓ Created {len(players)} players")
    
    # Run selection
    print("\n🎯 Running selection...")
    SELECTION_TOP_N = 20
    
    # Select top 20
    cur.execute(
        """SELECT id FROM preregistrations 
        WHERE event_date = ? AND list_type = 'main' 
        ORDER BY speedup_days DESC, datetime(created_at) ASC 
        LIMIT ?;""",
        (event_date, SELECTION_TOP_N)
    )
    selected = cur.fetchall()
    
    for row in selected:
        cur.execute("UPDATE preregistrations SET status = 'selected' WHERE id = ?;", (row['id'],))
    
    # Set waitlist
    cur.execute(
        """SELECT id FROM preregistrations 
        WHERE event_date = ? AND list_type = 'main' AND status = 'pending' 
        ORDER BY speedup_days DESC, datetime(created_at) ASC;""",
        (event_date,)
    )
    waitlist = cur.fetchall()
    
    for pos, row in enumerate(waitlist, start=1):
        cur.execute(
            "UPDATE preregistrations SET status = 'waitlist', waitlist_position = ? WHERE id = ?;",
            (pos, row['id'])
        )
    
    # Set selection ready time (in the past so it's already done)
    ready_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    cur.execute(
        "INSERT OR REPLACE INTO selection_state (event_date, ready_at, completed, completed_at) VALUES (?, ?, 1, ?);",
        (event_date, ready_at, now)
    )
    
    db.commit()
    print(f"✓ Selected Top {SELECTION_TOP_N}")
    
    # Display results
    print("\n📊 Test Data Summary:")
    print("=" * 60)
    
    print("\n🏆 SELECTED (Top 20):")
    cur.execute(
        "SELECT player_name, speedup_days FROM preregistrations WHERE event_date = ? AND list_type = 'main' AND status = 'selected' ORDER BY speedup_days DESC;",
        (event_date,)
    )
    selected_list = cur.fetchall()
    for i, p in enumerate(selected_list, 1):
        print(f"  {i:2d}. {p['player_name']:20s} - {p['speedup_days']:3d} days")
    
    print("\n⏳ WAITLIST (10 players):")
    cur.execute(
        "SELECT player_name, speedup_days, waitlist_position FROM preregistrations WHERE event_date = ? AND list_type = 'main' AND status = 'waitlist' ORDER BY waitlist_position ASC;",
        (event_date,)
    )
    waitlist_list = cur.fetchall()
    for p in waitlist_list:
        print(f"  Pos {p['waitlist_position']:2d}. {p['player_name']:20s} - {p['speedup_days']:3d} days")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("✅ Test data created successfully!")
    print("\n🎮 What you can test:")
    print("  1. Go to http://localhost:5000")
    print("  2. See the Top 20 selected players")
    print("  3. Click 'Switch to Secondary List' on any selected player")
    print("     → First waitlist player should be promoted automatically")
    print("  4. Reserve slots on Main List (for selected players)")
    print("  5. Reserve slots on Secondary List (for switched players)")
    print("  6. Both schedules work independently!")
    print("\n💡 Test scenarios:")
    print("  - Switch DragonKing → DesertFox promoted to Top 20")
    print("  - Switch WarLord99 → JungleLord promoted to Top 20")
    print("  - Reserve same time slot on both lists (no conflict!)")

if __name__ == '__main__':
    create_test_data()
