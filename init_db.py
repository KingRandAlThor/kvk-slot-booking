#!/usr/bin/env python3
"""
Initialize the database schema for KVK Slot Booking
Creates all necessary tables and adds event_day column if needed
"""
import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def init_db():
    """Initialize database with all required tables"""
    print("🔧 Initializing database...")
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Create preregistrations table
    print("📋 Creating preregistrations table...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS preregistrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_day TEXT DEFAULT 'monday',
            player_name TEXT NOT NULL,
            speedup_days INTEGER NOT NULL,
            preferred_slots TEXT NOT NULL,
            created_at TEXT NOT NULL,
            assigned_slot TEXT,
            list_type TEXT DEFAULT 'main'
        );
    ''')
    
    # Create selection_state table
    print("📋 Creating selection_state table...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS selection_state (
            event_date TEXT PRIMARY KEY,
            ready_at TEXT,
            completed INTEGER DEFAULT 0,
            completed_at TEXT
        );
    ''')
    
    # Create reservations table
    print("📋 Creating reservations table...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_day TEXT DEFAULT 'monday',
            player_name TEXT NOT NULL,
            slot_index INTEGER NOT NULL,
            speedup_days INTEGER NOT NULL,
            reserved_at TEXT NOT NULL,
            list_type TEXT DEFAULT 'main'
        );
    ''')
    
    # Create config table
    print("📋 Creating config table...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    ''')
    
    # Create training_players table for KVK Training
    print("📋 Creating training_players table...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS training_players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            power REAL NOT NULL,
            alliance TEXT NOT NULL,
            infantry_tg INTEGER DEFAULT 0,
            archery_tg INTEGER DEFAULT 0,
            cavalry_tg INTEGER DEFAULT 0,
            team INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # Create slot_conflicts table
    print("📋 Creating slot_conflicts table...")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS slot_conflicts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_day TEXT NOT NULL,
            slot_iso TEXT NOT NULL,
            player_names TEXT NOT NULL,
            speedup_days INTEGER NOT NULL,
            resolved INTEGER DEFAULT 0,
            winner TEXT
        );
    ''')
    
    # Add missing columns to existing tables
    print("🔄 Checking for missing columns...")
    
    # Add list_type to preregistrations if missing
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN list_type TEXT DEFAULT 'main';")
        print("  ✓ Added list_type to preregistrations")
    except sqlite3.OperationalError:
        print("  ✓ list_type already exists in preregistrations")
    
    # Add event_day to preregistrations if missing
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN event_day TEXT DEFAULT 'monday';")
        print("  ✓ Added event_day to preregistrations")
    except sqlite3.OperationalError:
        print("  ✓ event_day already exists in preregistrations")
    
    # Add event_day to reservations if missing
    try:
        cur.execute("ALTER TABLE reservations ADD COLUMN event_day TEXT DEFAULT 'monday';")
        print("  ✓ Added event_day to reservations")
    except sqlite3.OperationalError:
        print("  ✓ event_day already exists in reservations")
    
    # Add list_type to reservations if missing
    try:
        cur.execute("ALTER TABLE reservations ADD COLUMN list_type TEXT DEFAULT 'main';")
        print("  ✓ Added list_type to reservations")
    except sqlite3.OperationalError:
        print("  ✓ list_type already exists in reservations")
    
    # Add preferred_slots to preregistrations if missing
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN preferred_slots TEXT;")
        print("  ✓ Added preferred_slots to preregistrations")
    except sqlite3.OperationalError:
        print("  ✓ preferred_slots already exists in preregistrations")
    
    # Add assigned_slot to preregistrations if missing
    try:
        cur.execute("ALTER TABLE preregistrations ADD COLUMN assigned_slot TEXT;")
        print("  ✓ Added assigned_slot to preregistrations")
    except sqlite3.OperationalError:
        print("  ✓ assigned_slot already exists in preregistrations")
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialization complete!")
    print(f"📁 Database file: {os.path.abspath(DB_PATH)}")

if __name__ == '__main__':
    init_db()
