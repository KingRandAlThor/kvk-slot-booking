#!/usr/bin/env python3
"""Migration script to add list_type column to reservations table."""

import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DATABASE = os.path.join(BASE_DIR, 'kvk.db')

def migrate():
    db = sqlite3.connect(DATABASE)
    cur = db.cursor()
    
    # Check if list_type column exists
    cur.execute("PRAGMA table_info(reservations);")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'list_type' not in columns:
        print("Adding list_type column to reservations table...")
        cur.execute("ALTER TABLE reservations ADD COLUMN list_type TEXT DEFAULT 'main';")
        db.commit()
        print("✓ Migration completed successfully!")
    else:
        print("✓ Column list_type already exists in reservations table.")
    
    db.close()

if __name__ == '__main__':
    migrate()
