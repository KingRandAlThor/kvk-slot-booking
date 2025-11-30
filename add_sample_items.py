import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

items = [
    ('Item A',),
    ('Item B',),
    ('Item C',),
]

def add_items():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executemany('INSERT INTO items (name) VALUES (?);', items)
    conn.commit()
    cur.execute('SELECT COUNT(*) FROM items;')
    count = cur.fetchone()[0]
    conn.close()
    return count

if __name__ == '__main__':
    new_count = add_items()
    print('Inserted', len(items), 'items. New count =', new_count)
