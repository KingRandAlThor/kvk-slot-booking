#!/usr/bin/env python3
"""Script to clean and reset the database completely."""

import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, 'kvk.db')

def reset_database():
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    
    print("🧹 Cleaning database...")
    
    # Clear all tables
    print("  - Clearing preregistrations...")
    cur.execute("DELETE FROM preregistrations;")
    
    print("  - Clearing reservations...")
    cur.execute("DELETE FROM reservations;")
    
    print("  - Clearing selection_state...")
    cur.execute("DELETE FROM selection_state;")
    
    print("  - Clearing config (keeping event_date)...")
    cur.execute("DELETE FROM config WHERE key != 'event_date';")
    
    db.commit()
    
    # Verify column exists in reservations
    cur.execute("PRAGMA table_info(reservations);")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'list_type' in columns:
        print("✓ Column list_type exists in reservations table")
    else:
        print("⚠️  Column list_type is missing! Running migration...")
        cur.execute("ALTER TABLE reservations ADD COLUMN list_type TEXT DEFAULT 'main';")
        db.commit()
        print("✓ Migration completed")
    
    # Verify column exists in preregistrations
    cur.execute("PRAGMA table_info(preregistrations);")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'list_type' in columns:
        print("✓ Column list_type exists in preregistrations table")
    else:
        print("⚠️  Column list_type is missing in preregistrations! Running migration...")
        cur.execute("ALTER TABLE preregistrations ADD COLUMN list_type TEXT DEFAULT 'main';")
        db.commit()
        print("✓ Migration completed")
    
    db.close()
    
    print("\n✅ Database reset completed!")
    print("\nYou can now:")
    print("  1. Go to /admin to set a new event date")
    print("  2. Start fresh with pre-registrations")
    print("  3. Test the dual-list system for Thursday events")

if __name__ == '__main__':
    response = input("⚠️  This will DELETE ALL data from the database. Continue? (yes/no): ")
    if response.lower() in ('yes', 'y'):
        reset_database()
    else:
        print("❌ Operation cancelled")
