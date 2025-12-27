import sqlite3
from datetime import datetime, timezone
from app import app, optimize_slot_assignments

# Créer un contexte Flask
with app.app_context():
    db = sqlite3.connect('kvk.db')
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Vérifier l'état actuel
    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday";')
    total = cur.fetchone()[0]
    print(f'Total pré-inscriptions jeudi: {total}')

    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday" AND list_type = "main";')
    main = cur.fetchone()[0]
    print(f'Liste principale: {main}')

    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday" AND list_type = "secondary";')
    secondary = cur.fetchone()[0]
    print(f'Liste secondaire: {secondary}')

    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday" AND assigned_slot IS NOT NULL AND assigned_slot != "";')
    assigned = cur.fetchone()[0]
    print(f'Créneaux attribués: {assigned}')

    # Réinitialiser les assignations et list_type pour le test
    print('\n🔄 Réinitialisation...')
    cur.execute('UPDATE preregistrations SET assigned_slot = NULL, list_type = "main" WHERE event_day = "thursday";')
    cur.execute('DELETE FROM reservations WHERE event_day = "thursday";')
    db.commit()
    db.close()

    # Lancer l'optimisation manuellement
    print('\n🚀 Lancement de l\'optimisation pour jeudi...')
    optimize_slot_assignments('2025-01-16T12:00:00+00:00', 'thursday')

    # Vérifier après
    db = sqlite3.connect('kvk.db')
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    
    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday" AND list_type = "main" AND assigned_slot IS NOT NULL AND assigned_slot != "";')
    main_assigned = cur.fetchone()[0]
    print(f'\n✅ Main list - créneaux attribués: {main_assigned}')

    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday" AND list_type = "secondary" AND assigned_slot IS NOT NULL AND assigned_slot != "";')
    secondary_assigned = cur.fetchone()[0]
    print(f'✅ Secondary list - créneaux attribués: {secondary_assigned}')

    cur.execute('SELECT COUNT(*) FROM preregistrations WHERE event_day = "thursday" AND assigned_slot IS NOT NULL AND assigned_slot != "";')
    total_assigned = cur.fetchone()[0]
    print(f'✅ Total créneaux attribués: {total_assigned}')

    # Calculer les speedups totaux
    cur.execute('SELECT SUM(speedup_days) FROM preregistrations WHERE event_day = "thursday" AND assigned_slot IS NOT NULL AND assigned_slot != "";')
    total_speedups = cur.fetchone()[0]
    print(f'📊 Total speedups: {total_speedups} jours')

    # Vérifier les réservations dans la table reservations
    cur.execute('SELECT COUNT(*) FROM reservations WHERE event_day = "thursday" AND list_type = "main";')
    main_res = cur.fetchone()[0]
    print(f'\n📋 Reservations table:')
    print(f'   Main list: {main_res}')

    cur.execute('SELECT COUNT(*) FROM reservations WHERE event_day = "thursday" AND list_type = "secondary";')
    secondary_res = cur.fetchone()[0]
    print(f'   Secondary list: {secondary_res}')

    db.close()
    print('\n✅ Test terminé !')
