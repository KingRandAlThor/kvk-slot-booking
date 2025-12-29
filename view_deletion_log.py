#!/usr/bin/env python3
"""
Affiche l'historique des suppressions depuis la table deletion_log
"""
import sqlite3
from datetime import datetime

DATABASE = 'kvk.db'

def view_deletion_log():
    """Affiche toutes les suppressions enregistrées"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    
    # Vérifier si la table existe
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='deletion_log';")
    if not cur.fetchone():
        print("❌ La table deletion_log n'existe pas encore.")
        print("   Lancez l'application une fois pour créer la table.")
        return
    
    # Récupérer toutes les suppressions
    cur.execute("""
        SELECT id, table_name, record_id, player_name, deleted_by, deleted_at, data_backup
        FROM deletion_log
        ORDER BY deleted_at DESC;
    """)
    
    deletions = cur.fetchall()
    
    if not deletions:
        print("✅ Aucune suppression enregistrée.")
        return
    
    print("\n" + "="*80)
    print(f"📜 HISTORIQUE DES SUPPRESSIONS ({len(deletions)} entrées)")
    print("="*80 + "\n")
    
    for deletion in deletions:
        # Formatter la date
        try:
            deleted_at = datetime.fromisoformat(deletion['deleted_at'])
            date_str = deleted_at.strftime('%d/%m/%Y %H:%M:%S')
        except:
            date_str = deletion['deleted_at']
        
        print(f"🗑️  ID: {deletion['id']}")
        print(f"   Table: {deletion['table_name']}")
        print(f"   Record ID: {deletion['record_id']}")
        print(f"   Joueur: {deletion['player_name'] or 'N/A'}")
        print(f"   Supprimé par: {deletion['deleted_by']}")
        print(f"   Date: {date_str}")
        if deletion['data_backup']:
            print(f"   Backup: {deletion['data_backup'][:50]}...")
        print("-" * 80)
    
    db.close()
    
    print(f"\n✅ Total: {len(deletions)} suppressions enregistrées\n")

if __name__ == '__main__':
    view_deletion_log()
