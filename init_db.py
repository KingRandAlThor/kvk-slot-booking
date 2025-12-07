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
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            waitlist_position INTEGER,
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
            slot_start TEXT NOT NULL,
            event_day TEXT DEFAULT 'monday',
            player_name TEXT NOT NULL,
            speedup_days INTEGER DEFAULT 0,
            created_at TEXT,
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
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialization complete!")
    print(f"📁 Database file: {os.path.abspath(DB_PATH)}")

if __name__ == '__main__':
    init_db()
