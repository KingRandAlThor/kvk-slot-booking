#!/usr/bin/env python3
"""Test script to verify automatic promotion when Top 20 switches to secondary list."""

import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, 'kvk.db')

def test_promotion():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    
    event_date = '2025-12-05'  # Thursday
    
    # Clear existing data for this event
    print("Clearing existing test data...")
    cur.execute("DELETE FROM preregistrations WHERE event_date = ?;", (event_date,))
    cur.execute("DELETE FROM reservations WHERE slot_start LIKE ?;", (f"{event_date}%",))
    cur.execute("DELETE FROM selection_state WHERE event_date = ?;", (event_date,))
    db.commit()
    
    # Create 25 players (20 selected + 5 waitlist)
    print("Creating 25 test players...")
    now = datetime.now(timezone.utc).isoformat()
    
    for i in range(1, 26):
        player_name = f"Player{i}"
        speedup_days = 100 - i  # Higher speedups for earlier players
        cur.execute(
            "INSERT INTO preregistrations (event_date, player_name, speedup_days, created_at, status, list_type) VALUES (?, ?, ?, ?, 'pending', 'main');",
            (event_date, player_name, speedup_days, now)
        )
    
    db.commit()
    
    # Run selection manually
    print("Running selection...")
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
    
    # Mark selection as completed
    cur.execute(
        "INSERT OR REPLACE INTO selection_state (event_date, ready_at, completed, completed_at) VALUES (?, ?, 1, ?);",
        (event_date, now, now)
    )
    
    db.commit()
    
    print("\n✓ Initial state created:")
    print("  - 20 players selected (Player1 to Player20)")
    print("  - 5 players on waitlist (Player21 to Player25)")
    
    # Display initial state
    cur.execute("SELECT player_name, speedup_days, status, waitlist_position FROM preregistrations WHERE event_date = ? AND list_type = 'main' ORDER BY speedup_days DESC;", (event_date,))
    players = cur.fetchall()
    
    print("\nInitial Main List:")
    for p in players:
        pos = f"(pos {p['waitlist_position']})" if p['waitlist_position'] else ""
        print(f"  {p['player_name']}: {p['speedup_days']} days - {p['status']} {pos}")
    
    # Now simulate Player1 (top selected) switching to secondary
    print("\n\nSimulating Player1 switching to secondary list...")
    
    cur.execute(
        "SELECT id, status FROM preregistrations WHERE event_date = ? AND player_name = ? AND list_type = 'main' LIMIT 1;",
        (event_date, "Player1")
    )
    row = cur.fetchone()
    
    if row:
        was_selected = row['status'] == 'selected'
        print(f"  Player1 status: {row['status']}")
        print(f"  Was selected: {was_selected}")
        
        # Switch to secondary list
        cur.execute(
            "UPDATE preregistrations SET list_type = 'secondary', status = 'selected', waitlist_position = NULL WHERE id = ?;",
            (row['id'],)
        )
        
        # If was selected, promote first waitlist
        if was_selected:
            cur.execute(
                """SELECT id, player_name FROM preregistrations 
                WHERE event_date = ? AND list_type = 'main' AND status = 'waitlist' 
                ORDER BY waitlist_position ASC LIMIT 1;""",
                (event_date,)
            )
            first_waitlist = cur.fetchone()
            
            if first_waitlist:
                print(f"  Promoting: {first_waitlist['player_name']}")
                
                # Promote to selected
                cur.execute(
                    "UPDATE preregistrations SET status = 'selected', waitlist_position = NULL WHERE id = ?;",
                    (first_waitlist['id'],)
                )
                
                # Recalculate waitlist positions
                cur.execute(
                    """SELECT id FROM preregistrations 
                    WHERE event_date = ? AND list_type = 'main' AND status = 'waitlist' 
                    ORDER BY speedup_days DESC, datetime(created_at) ASC;""",
                    (event_date,)
                )
                remaining_waitlist = cur.fetchall()
                for pos, wl_row in enumerate(remaining_waitlist, start=1):
                    cur.execute(
                        "UPDATE preregistrations SET waitlist_position = ? WHERE id = ?;",
                        (pos, wl_row['id'])
                    )
                
                db.commit()
                print(f"  ✓ {first_waitlist['player_name']} promoted to Top 20!")
            else:
                print("  No waitlist players to promote")
        else:
            print("  Player was not selected, no promotion needed")
    
    # Display final state
    print("\n\nFinal state:")
    
    print("\nMain List (should have 20 selected):")
    cur.execute("SELECT player_name, speedup_days, status FROM preregistrations WHERE event_date = ? AND list_type = 'main' AND status = 'selected' ORDER BY speedup_days DESC;", (event_date,))
    selected_players = cur.fetchall()
    print(f"  Selected count: {len(selected_players)}")
    for p in selected_players:
        print(f"    {p['player_name']}: {p['speedup_days']} days")
    
    print("\nWaitlist (should have 4 players):")
    cur.execute("SELECT player_name, speedup_days, waitlist_position FROM preregistrations WHERE event_date = ? AND list_type = 'main' AND status = 'waitlist' ORDER BY waitlist_position ASC;", (event_date,))
    waitlist_players = cur.fetchall()
    print(f"  Waitlist count: {len(waitlist_players)}")
    for p in waitlist_players:
        print(f"    Position {p['waitlist_position']}: {p['player_name']} ({p['speedup_days']} days)")
    
    print("\nSecondary List (should have 1 player):")
    cur.execute("SELECT player_name, speedup_days FROM preregistrations WHERE event_date = ? AND list_type = 'secondary' ORDER BY datetime(created_at);", (event_date,))
    secondary_players = cur.fetchall()
    print(f"  Secondary count: {len(secondary_players)}")
    for p in secondary_players:
        print(f"    {p['player_name']}: {p['speedup_days']} days")
    
    db.close()
    
    print("\n✓ Test completed!")
    print("\nExpected results:")
    print("  - Main List: 20 selected (Player2-Player20, Player21)")
    print("  - Waitlist: 4 players (Player22-Player25)")
    print("  - Secondary: 1 player (Player1)")

if __name__ == '__main__':
    test_promotion()
