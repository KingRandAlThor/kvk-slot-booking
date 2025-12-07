import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def check_config():
    """Vérifie la configuration de la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    print("Configuration actuelle:\n")
    
    cur.execute("SELECT * FROM config;")
    configs = cur.fetchall()
    
    for config in configs:
        print(f"  {config['key']}: {config['value']}")
    
    if not configs:
        print("  (aucune configuration trouvée)")
    
    conn.close()

if __name__ == '__main__':
    check_config()
