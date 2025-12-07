import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'kvk.db')

def migrate_database():
    """Ajoute la colonne list_type à la table preregistrations"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    print("=== MIGRATION BASE DE DONNÉES ===\n")
    
    # Vérifier si la colonne existe déjà
    cur.execute("PRAGMA table_info(preregistrations);")
    columns = [col[1] for col in cur.fetchall()]
    
    if 'list_type' in columns:
        print("✓ La colonne 'list_type' existe déjà.")
    else:
        print("Ajout de la colonne 'list_type'...")
        try:
            cur.execute("ALTER TABLE preregistrations ADD COLUMN list_type TEXT DEFAULT 'main';")
            conn.commit()
            print("✓ Colonne 'list_type' ajoutée avec succès!")
        except Exception as e:
            print(f"✗ Erreur: {e}")
            return False
    
    # Mettre à jour les enregistrements existants
    cur.execute("UPDATE preregistrations SET list_type = 'main' WHERE list_type IS NULL;")
    conn.commit()
    
    print("\n✅ Migration terminée!")
    
    # Afficher le nouveau schéma
    print("\nNouveau schéma de 'preregistrations':")
    cur.execute("PRAGMA table_info(preregistrations);")
    for col in cur.fetchall():
        print(f"  {col[1]} ({col[2]})")
    
    conn.close()
    return True

if __name__ == '__main__':
    migrate_database()
